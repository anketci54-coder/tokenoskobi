
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_runtime_stabilization_and_continuous_producer_review_v1.json"

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

def table_cols(con, table):
    return [r[1] for r in con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()]

def counts(con):
    return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}

def group_count(con, cols, expr, limit=100):
    sql = """
        SELECT """ + expr + """ AS bucket, COUNT(*) AS c
        FROM news_token_match_events
        WHERE COALESCE(write_allowed,0) != 0
           OR COALESCE(trade_signal,0) != 0
           OR COALESCE(paper_signal,0) != 0
        GROUP BY bucket
        ORDER BY c DESC, bucket ASC
        LIMIT ?
    """
    return [{"bucket": r[0], "count": r[1]} for r in con.execute(sql, [limit]).fetchall()]

def safe_col_expr(cols, col, fallback):
    return q(col) if col in cols else fallback

def sample_bad_rows(con, cols, limit=80):
    wanted = [
        "match_uid", "news_uid", "source_uid", "token_uid", "pair_uid",
        "symbol", "chain", "match_type", "match_confidence", "match_score",
        "write_allowed", "trade_signal", "paper_signal", "created_at_utc",
        "evidence_text", "match_reasons_json"
    ]
    selected = [c for c in wanted if c in cols]
    sql = """
        SELECT """ + ",".join(q(c) for c in selected) + """
        FROM news_token_match_events
        WHERE COALESCE(write_allowed,0) != 0
           OR COALESCE(trade_signal,0) != 0
           OR COALESCE(paper_signal,0) != 0
        ORDER BY COALESCE(created_at_utc,''), news_uid
        LIMIT ?
    """
    rows = []
    for r in con.execute(sql, [limit]).fetchall():
        d = dict(r)
        if "evidence_text" in d and d["evidence_text"]:
            d["evidence_text"] = str(d["evidence_text"])[:500]
        if "match_reasons_json" in d and d["match_reasons_json"]:
            d["match_reasons_json"] = str(d["match_reasons_json"])[:1000]
        rows.append(d)
    return rows

def bad_uid_chain_status(con, bad_uids):
    out = []
    for uid in bad_uids:
        raw_c = con.execute("SELECT COUNT(*) FROM news_raw_feed_events WHERE news_uid=?", [uid]).fetchone()[0]
        match_c = con.execute("SELECT COUNT(*) FROM news_token_match_events WHERE news_uid=?", [uid]).fetchone()[0]
        signal_c = con.execute("SELECT COUNT(*) FROM news_signal_events WHERE news_uid=?", [uid]).fetchone()[0]
        score_c = con.execute("SELECT COUNT(*) FROM news_score_events_v1 WHERE news_uid=?", [uid]).fetchone()[0]
        out.append({
            "news_uid": uid,
            "raw_count": raw_c,
            "match_count": match_c,
            "signal_count": signal_c,
            "score_count": score_c
        })
    return out

def namespace_from_uid_expr():
    return """
        CASE
          WHEN news_uid LIKE 'hist_news_%' THEN 'historical_hist_news'
          WHEN news_uid LIKE 'timer_news_%' THEN 'timer_news'
          WHEN news_uid LIKE 'news_%' THEN 'runtime_news'
          WHEN news_uid LIKE 'rss_%' THEN 'rss_news'
          ELSE 'other'
        END
    """

def audit_main():
    generated_at = now()
    failures = []
    warnings = []

    prior = load_json(PRIOR)
    prior_decision = prior.get("decision")
    prior_result = prior.get("result", {})

    if prior_decision != "FAIL_NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW":
        warnings.append("prior_review_not_failed_or_missing_expected_hold_state")

    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        missing_tables = [t for t in TABLES if not table_exists(con, t)]
        if missing_tables:
            failures.append("missing_news_tables:" + ",".join(missing_tables))

        db_counts = counts(con) if not missing_tables else {}

        cols = table_cols(con, TARGET) if table_exists(con, TARGET) else []
        required = ["news_uid", "write_allowed", "trade_signal", "paper_signal"]
        missing_required = [c for c in required if c not in cols]
        if missing_required:
            failures.append("missing_required_columns:" + ",".join(missing_required))

        if failures:
            bad_count = None
            bad_samples = []
            groupings = {}
            bad_uids = []
            chain_status = []
            cleanup_scope = {}
            derived_impact = {}
        else:
            bad_count = con.execute("""
                SELECT COUNT(*)
                FROM news_token_match_events
                WHERE COALESCE(write_allowed,0) != 0
                   OR COALESCE(trade_signal,0) != 0
                   OR COALESCE(paper_signal,0) != 0
            """).fetchone()[0]

            bad_uids = [
                r[0] for r in con.execute("""
                    SELECT DISTINCT news_uid
                    FROM news_token_match_events
                    WHERE COALESCE(write_allowed,0) != 0
                       OR COALESCE(trade_signal,0) != 0
                       OR COALESCE(paper_signal,0) != 0
                    ORDER BY news_uid
                    LIMIT 200
                """).fetchall()
            ]

            groupings = {
                "by_write_allowed": group_count(con, cols, "COALESCE(write_allowed,0)"),
                "by_trade_signal": group_count(con, cols, "COALESCE(trade_signal,0)"),
                "by_paper_signal": group_count(con, cols, "COALESCE(paper_signal,0)"),
                "by_flag_tuple": group_count(con, cols, "COALESCE(write_allowed,0) || '/' || COALESCE(trade_signal,0) || '/' || COALESCE(paper_signal,0)"),
                "by_namespace": group_count(con, cols, namespace_from_uid_expr()),
                "by_match_type": group_count(con, cols, safe_col_expr(cols, "match_type", "'NO_MATCH_TYPE'")),
                "by_chain": group_count(con, cols, safe_col_expr(cols, "chain", "'NO_CHAIN'")),
                "by_symbol": group_count(con, cols, safe_col_expr(cols, "symbol", "'NO_SYMBOL'")),
                "by_created_at_day": group_count(con, cols, "substr(COALESCE(created_at_utc,''),1,10)" if "created_at_utc" in cols else "'NO_CREATED_AT'")
            }

            bad_samples = sample_bad_rows(con, cols)
            chain_status = bad_uid_chain_status(con, bad_uids)

            hist_bad_count = con.execute("""
                SELECT COUNT(*)
                FROM news_token_match_events
                WHERE news_uid LIKE 'hist_news_%'
                  AND (
                    COALESCE(write_allowed,0) != 0
                    OR COALESCE(trade_signal,0) != 0
                    OR COALESCE(paper_signal,0) != 0
                  )
            """).fetchone()[0]

            cleanup_scope = {
                "bad_total_rows": bad_count,
                "bad_distinct_news_uid_count": len(bad_uids),
                "historical_bad_rows": hist_bad_count,
                "historical_layer_impacted": hist_bad_count != 0,
                "candidate_cleanup_action": "SET write_allowed=0, trade_signal=0, paper_signal=0 for rows where any flag is nonzero",
                "requires_backup": True,
                "schema_change_required": False,
                "network_required": False,
                "service_timer_required": False
            }

            derived_impact = {
                "all_bad_uids_have_raw": all(x["raw_count"] >= 1 for x in chain_status),
                "all_bad_uids_have_match": all(x["match_count"] >= 1 for x in chain_status),
                "signal_rows_for_bad_uids": sum(x["signal_count"] for x in chain_status),
                "score_rows_for_bad_uids": sum(x["score_count"] for x in chain_status),
                "chain_status_sample": chain_status[:80]
            }

            if bad_count == 0:
                warnings.append("no_bad_trade_flags_found_now")
            if hist_bad_count != 0:
                failures.append("historical_bad_flags_present")
            if not all(x["raw_count"] >= 1 for x in chain_status):
                failures.append("bad_flag_uid_without_raw_present")

        if integrity != "ok":
            failures.append("sqlite_integrity_not_ok")

    finally:
        con.close()

    tests = [
        {
            "test_id": "T01_PRIOR_HOLD_REASON_AVAILABLE",
            "ok": prior_decision == "FAIL_NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW",
            "prior_decision": prior_decision,
            "prior_bad_trade_flags": prior_result.get("bad_trade_flags")
        },
        {
            "test_id": "T02_DB_READONLY_INTEGRITY_OK",
            "ok": integrity == "ok" and not missing_tables,
            "integrity": integrity,
            "missing_tables": missing_tables
        },
        {
            "test_id": "T03_BAD_FLAGS_LOCATED_AND_GROUPED",
            "ok": bad_count is not None and bad_count >= 0 and bool(groupings),
            "bad_count": bad_count,
            "groupings": groupings
        },
        {
            "test_id": "T04_HISTORICAL_LAYER_NOT_IMPACTED",
            "ok": cleanup_scope.get("historical_layer_impacted") is False,
            "cleanup_scope": cleanup_scope
        },
        {
            "test_id": "T05_CLEANUP_SCOPE_DEFINED",
            "ok": cleanup_scope.get("bad_total_rows", -1) >= 0
                  and cleanup_scope.get("candidate_cleanup_action") is not None
                  and cleanup_scope.get("requires_backup") is True,
            "cleanup_scope": cleanup_scope
        },
        {
            "test_id": "T06_NOAPI_READONLY_BOUNDARY_LOCKED",
            "ok": True,
            "network_call": False,
            "api_call": False,
            "db_write": False,
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

    next_step = "BAD_TRADE_FLAGS_CLEANUP_APPLY_WITH_BACKUP_NOAPI" if not failures else "BAD_TRADE_FLAGS_ROOT_CAUSE_AUDIT_HOLD"

    return {
        "stage": "BAD_TRADE_FLAGS_ROOT_CAUSE_AUDIT_NOAPI",
        "generated_at_utc": generated_at,
        "decision": "OK_BAD_TRADE_FLAGS_ROOT_CAUSE_AUDIT_NOAPI" if not failures else "FAIL_BAD_TRADE_FLAGS_ROOT_CAUSE_AUDIT_NOAPI",
        "prior": "data/control/news_runtime_stabilization_and_continuous_producer_review_v1.json",
        "db_counts": db_counts,
        "integrity": integrity,
        "bad_trade_flags": {
            "count": bad_count,
            "distinct_news_uid_count": len(bad_uids) if isinstance(bad_uids, list) else None,
            "groupings": groupings,
            "samples": bad_samples
        },
        "derived_impact": derived_impact,
        "cleanup_scope": cleanup_scope,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "network_call": False,
            "api_call": False,
            "db_write": False,
            "db_schema_change": False,
            "index_creation": False,
            "service_change": False,
            "timer_change": False,
            "nginx_change": False,
            "paper_trade": False,
            "live_trade": False,
            "execution_authority": False
        },
        "remaining_after_this_if_ok": [
            "BAD_TRADE_FLAGS_CLEANUP_APPLY_WITH_BACKUP_NOAPI",
            "NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI",
            "NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI",
            "NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN_AND_POST_AUDIT_SEAL"
        ],
        "failures": failures,
        "warnings": warnings,
        "next": next_step
    }

if __name__ == "__main__":
    print(json.dumps(audit_main(), ensure_ascii=False, indent=2, sort_keys=True))
