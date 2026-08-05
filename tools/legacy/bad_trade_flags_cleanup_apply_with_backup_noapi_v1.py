
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, shutil

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/bad_trade_flags_root_cause_audit_noapi_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

TARGET = "news_token_match_events"

def now():
    return datetime.now(timezone.utc).isoformat()

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def table_exists(con, table):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        [table]
    ).fetchone() is not None

def counts(con):
    return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}

def bad_count(con):
    return con.execute("""
        SELECT COUNT(*)
        FROM news_token_match_events
        WHERE COALESCE(write_allowed,0) != 0
           OR COALESCE(trade_signal,0) != 0
           OR COALESCE(paper_signal,0) != 0
    """).fetchone()[0]

def bad_count_historical(con):
    return con.execute("""
        SELECT COUNT(*)
        FROM news_token_match_events
        WHERE news_uid LIKE 'hist_news_%'
          AND (
            COALESCE(write_allowed,0) != 0
            OR COALESCE(trade_signal,0) != 0
            OR COALESCE(paper_signal,0) != 0
          )
    """).fetchone()[0]

def cleanup_scope_rows(con):
    rows = con.execute("""
        SELECT match_uid, news_uid, symbol, chain, write_allowed, trade_signal, paper_signal, created_at_utc
        FROM news_token_match_events
        WHERE news_uid NOT LIKE 'hist_news_%'
          AND (
            COALESCE(write_allowed,0) != 0
            OR COALESCE(trade_signal,0) != 0
            OR COALESCE(paper_signal,0) != 0
          )
        ORDER BY created_at_utc, news_uid
    """).fetchall()
    return [dict(r) for r in rows]

def group_after(con):
    rows = con.execute("""
        SELECT
          COALESCE(write_allowed,0) || '/' || COALESCE(trade_signal,0) || '/' || COALESCE(paper_signal,0) AS flag_tuple,
          COUNT(*) AS c
        FROM news_token_match_events
        GROUP BY flag_tuple
        ORDER BY c DESC, flag_tuple ASC
    """).fetchall()
    return [{"flag_tuple": r[0], "count": r[1]} for r in rows]

def main():
    generated_at = now()
    failures = []
    warnings = []

    prior = load_json(PRIOR)
    prior_result = prior.get("result", {})
    expected_bad = int(prior_result.get("bad_trade_flags", {}).get("count", 0) or 0)
    historical_impacted = prior_result.get("cleanup_scope", {}).get("historical_layer_impacted")

    if prior.get("decision") != "OK_BAD_TRADE_FLAGS_ROOT_CAUSE_AUDIT_NOAPI":
        failures.append("prior_bad_trade_flags_root_cause_not_ok")
    if expected_bad <= 0:
        failures.append("expected_bad_count_zero")
    if historical_impacted is not False:
        failures.append("historical_layer_impacted_in_prior_scope")

    backup_dir = ROOT / "data/backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / ("tokenoskobi_clean_v1.PRE_BAD_TRADE_FLAGS_CLEANUP_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".sqlite")
    shutil.copy2(DB, backup_path)

    con = sqlite3.connect(str(DB), timeout=30)
    con.row_factory = sqlite3.Row

    applied = False
    updated_rows = 0

    try:
        missing_tables = [t for t in TABLES if not table_exists(con, t)]
        if missing_tables:
            failures.append("missing_news_tables:" + ",".join(missing_tables))

        integrity_before = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity_before != "ok":
            failures.append("sqlite_integrity_before_not_ok")

        before_counts = counts(con) if not missing_tables else {}
        before_bad = bad_count(con) if not missing_tables else None
        before_bad_historical = bad_count_historical(con) if not missing_tables else None
        scope_rows_before = cleanup_scope_rows(con) if not missing_tables else []

        if before_bad != expected_bad:
            warnings.append("bad_count_changed_since_root_cause_audit")
        if before_bad_historical != 0:
            failures.append("historical_bad_flags_present_before_cleanup")
        if len(scope_rows_before) != before_bad:
            failures.append("cleanup_scope_row_count_mismatch")

        if not failures:
            con.execute("BEGIN IMMEDIATE")
            cur = con.execute("""
                UPDATE news_token_match_events
                SET write_allowed = 0,
                    trade_signal = 0,
                    paper_signal = 0
                WHERE news_uid NOT LIKE 'hist_news_%'
                  AND (
                    COALESCE(write_allowed,0) != 0
                    OR COALESCE(trade_signal,0) != 0
                    OR COALESCE(paper_signal,0) != 0
                  )
            """)
            updated_rows = cur.rowcount

            after_counts_preview = counts(con)
            after_bad_preview = bad_count(con)
            after_bad_hist_preview = bad_count_historical(con)
            integrity_after_preview = con.execute("PRAGMA integrity_check").fetchone()[0]

            news_delta_preview = {k: after_counts_preview[k] - before_counts[k] for k in before_counts}

            temp_failures = []
            if updated_rows != len(scope_rows_before):
                temp_failures.append("updated_rows_scope_mismatch")
            if after_bad_preview != 0:
                temp_failures.append("bad_flags_still_nonzero_after_cleanup")
            if after_bad_hist_preview != 0:
                temp_failures.append("historical_bad_flags_after_cleanup")
            if any(v != 0 for v in news_delta_preview.values()):
                temp_failures.append("news_table_counts_changed_during_cleanup")
            if integrity_after_preview != "ok":
                temp_failures.append("sqlite_integrity_after_not_ok")

            if temp_failures:
                con.rollback()
                failures.extend(temp_failures)
                applied = False
                after_counts = counts(con)
                after_bad = bad_count(con)
                after_bad_historical = bad_count_historical(con)
                integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]
            else:
                con.commit()
                applied = True
                after_counts = counts(con)
                after_bad = bad_count(con)
                after_bad_historical = bad_count_historical(con)
                integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]
        else:
            after_counts = counts(con) if not missing_tables else {}
            after_bad = bad_count(con) if not missing_tables else None
            after_bad_historical = bad_count_historical(con) if not missing_tables else None
            integrity_after = con.execute("PRAGMA integrity_check").fetchone()[0]

        after_grouping = group_after(con) if not missing_tables else []

    except Exception as exc:
        try:
            con.rollback()
        except Exception:
            pass
        failures.append("cleanup_exception:" + repr(exc))
        applied = False
        before_counts = {}
        after_counts = {}
        before_bad = None
        after_bad = None
        before_bad_historical = None
        after_bad_historical = None
        scope_rows_before = []
        after_grouping = []
        integrity_before = "unknown"
        integrity_after = "unknown"
    finally:
        con.close()

    news_delta = {k: after_counts[k] - before_counts[k] for k in before_counts} if before_counts and after_counts else {}

    tests = [
        {
            "test_id": "T01_PRIOR_ROOT_CAUSE_OK",
            "ok": prior.get("decision") == "OK_BAD_TRADE_FLAGS_ROOT_CAUSE_AUDIT_NOAPI",
            "expected_bad": expected_bad
        },
        {
            "test_id": "T02_BACKUP_CREATED",
            "ok": backup_path.exists(),
            "backup_path": str(backup_path)
        },
        {
            "test_id": "T03_SCOPE_CONFIRMED_BEFORE_CLEANUP",
            "ok": before_bad is not None and before_bad >= expected_bad and before_bad_historical == 0 and len(scope_rows_before) == before_bad,
            "before_bad": before_bad,
            "before_bad_historical": before_bad_historical,
            "scope_rows": len(scope_rows_before)
        },
        {
            "test_id": "T04_CLEANUP_APPLIED_AND_FLAGS_ZERO",
            "ok": applied is True and updated_rows == len(scope_rows_before) and after_bad == 0 and after_bad_historical == 0,
            "applied": applied,
            "updated_rows": updated_rows,
            "after_bad": after_bad,
            "after_bad_historical": after_bad_historical
        },
        {
            "test_id": "T05_NEWS_COUNTS_UNCHANGED",
            "ok": all(v == 0 for v in news_delta.values()),
            "news_delta": news_delta
        },
        {
            "test_id": "T06_SQLITE_INTEGRITY_OK",
            "ok": integrity_before == "ok" and integrity_after == "ok",
            "integrity_before": integrity_before,
            "integrity_after": integrity_after
        },
        {
            "test_id": "T07_NOAPI_BOUNDARY_LOCKED",
            "ok": True,
            "network_call": False,
            "api_call": False,
            "db_write": True,
            "schema_change": False,
            "service_change": False,
            "timer_change": False,
            "paper_trade": False,
            "live_trade": False,
            "trade_authority": False
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI" if not failures else "BAD_TRADE_FLAGS_CLEANUP_HOLD"

    return {
        "stage": "BAD_TRADE_FLAGS_CLEANUP_APPLY_WITH_BACKUP_NOAPI",
        "generated_at_utc": generated_at,
        "decision": "OK_BAD_TRADE_FLAGS_CLEANUP_APPLY_WITH_BACKUP_NOAPI_INTERNAL" if not failures else "FAIL_BAD_TRADE_FLAGS_CLEANUP_APPLY_WITH_BACKUP_NOAPI_INTERNAL",
        "applied": applied,
        "backup_path": str(backup_path),
        "prior": "data/control/bad_trade_flags_root_cause_audit_noapi_v1.json",
        "expected_bad_from_prior": expected_bad,
        "before_bad_flags": before_bad,
        "after_bad_flags": after_bad,
        "before_bad_historical": before_bad_historical,
        "after_bad_historical": after_bad_historical,
        "updated_rows": updated_rows,
        "scope_rows_before": scope_rows_before,
        "after_flag_grouping": after_grouping,
        "before_counts": before_counts,
        "after_counts": after_counts,
        "news_delta": news_delta,
        "integrity_before": integrity_before,
        "integrity_after": integrity_after,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "network_call": False,
            "api_call": False,
            "db_write": True,
            "db_schema_change": False,
            "index_creation": False,
            "service_change": False,
            "timer_change": False,
            "nginx_change": False,
            "paper_trade": False,
            "live_trade": False,
            "execution_authority": False
        },
        "failures": failures,
        "warnings": warnings,
        "next": next_step
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
