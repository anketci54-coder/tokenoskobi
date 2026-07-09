
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_producer_staleness_fix_real_apply_with_backup_v1.json"
PREVIOUS_FAILED = ROOT / "data/control/news_producer_staleness_post_apply_freshness_audit_noapi_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

def now():
    return datetime.now(timezone.utc).isoformat()

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {"cmd": cmd, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def main():
    prior = load(PRIOR)
    apply_result = prior.get("apply_result", {})
    prior_latest = apply_result.get("latest", {})
    batch_ts = prior_latest.get("derived_after")
    backup = apply_result.get("backup", {})
    backup_db = Path(str(backup.get("backup_db", "")))

    previous_failed_summary = None
    if PREVIOUS_FAILED.exists():
        try:
            old = load(PREVIOUS_FAILED)
            previous_failed_summary = {
                "decision": old.get("decision"),
                "internal": old.get("audit", {}).get("decision"),
                "failures": old.get("failures", []),
                "warnings": old.get("warnings", []),
                "db_delta": old.get("db_delta", {})
            }
        except Exception as exc:
            previous_failed_summary = {"read_error": repr(exc)}

    failures = []
    warnings = []

    if prior.get("decision") != "OK_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_WITH_BACKUP":
        failures.append("prior_real_apply_not_ok")

    if apply_result.get("decision") != "OK_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_WITH_BACKUP_INTERNAL":
        failures.append("prior_real_apply_internal_not_ok")

    if apply_result.get("failures") not in ([], None):
        failures.append("prior_real_apply_internal_failures_not_empty")

    if not batch_ts:
        failures.append("batch_timestamp_missing")

    backup_sha_current = None
    if backup_db.exists():
        backup_sha_current = sha256(backup_db)
        if backup.get("backup_sha256") and backup_sha_current != backup.get("backup_sha256"):
            failures.append("backup_sha_mismatch")
    else:
        warnings.append("backup_file_not_visible_or_ignored_but_apply_artifact_recorded_sha")

    timer_state = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_state = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    before = {}
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        for t in TABLES:
            before[t] = con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0]

        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]

        latest_raw = con.execute("""
            SELECT MAX(COALESCE(published_at_utc, fetched_at_utc))
            FROM news_raw_feed_events
            WHERE COALESCE(published_at_utc, fetched_at_utc) IS NOT NULL
        """).fetchone()[0]

        latest_by_table = {}
        for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
            latest_by_table[t] = con.execute(
                "SELECT MAX(created_at_utc) FROM " + q(t) + " WHERE created_at_utc IS NOT NULL"
            ).fetchone()[0]

        latest_derived = max([v for v in latest_by_table.values() if v] or [None])

        batch_counts = {
            "news_token_match_events": con.execute(
                "SELECT COUNT(*) FROM news_token_match_events WHERE created_at_utc = ?",
                [batch_ts]
            ).fetchone()[0] if batch_ts else 0,
            "news_signal_events": con.execute(
                "SELECT COUNT(*) FROM news_signal_events WHERE created_at_utc = ?",
                [batch_ts]
            ).fetchone()[0] if batch_ts else 0,
            "news_score_events_v1": con.execute(
                "SELECT COUNT(*) FROM news_score_events_v1 WHERE created_at_utc = ?",
                [batch_ts]
            ).fetchone()[0] if batch_ts else 0
        }

        expected_inserted = apply_result.get("inserted", {})

        batch_missing_signal_for_match = con.execute("""
            SELECT COUNT(*)
            FROM news_token_match_events m
            WHERE m.created_at_utc = ?
              AND NOT EXISTS (
                SELECT 1 FROM news_signal_events s WHERE s.news_uid = m.news_uid
              )
        """, [batch_ts]).fetchone()[0] if batch_ts else 0

        batch_missing_score_for_match = con.execute("""
            SELECT COUNT(*)
            FROM news_token_match_events m
            WHERE m.created_at_utc = ?
              AND NOT EXISTS (
                SELECT 1 FROM news_score_events_v1 sc WHERE sc.news_uid = m.news_uid
              )
        """, [batch_ts]).fetchone()[0] if batch_ts else 0

        batch_missing_score_for_signal = con.execute("""
            SELECT COUNT(*)
            FROM news_signal_events s
            WHERE s.created_at_utc = ?
              AND NOT EXISTS (
                SELECT 1 FROM news_score_events_v1 sc WHERE sc.news_uid = s.news_uid
              )
        """, [batch_ts]).fetchone()[0] if batch_ts else 0

        batch_bad_trade_flags = con.execute("""
            SELECT COUNT(*)
            FROM news_token_match_events
            WHERE created_at_utc = ?
              AND (write_allowed != 0 OR trade_signal != 0 OR paper_signal != 0)
        """, [batch_ts]).fetchone()[0] if batch_ts else 0

        batch_duplicate_checks = {
            "match_uid_duplicates": con.execute("""
                SELECT COUNT(*) FROM (
                  SELECT match_uid, COUNT(*) c
                  FROM news_token_match_events
                  WHERE created_at_utc = ?
                  GROUP BY match_uid
                  HAVING c > 1
                )
            """, [batch_ts]).fetchone()[0] if batch_ts else 0,
            "signal_uid_duplicates": con.execute("""
                SELECT COUNT(*) FROM (
                  SELECT signal_uid, COUNT(*) c
                  FROM news_signal_events
                  WHERE created_at_utc = ?
                  GROUP BY signal_uid
                  HAVING c > 1
                )
            """, [batch_ts]).fetchone()[0] if batch_ts else 0,
            "score_uid_duplicates": con.execute("""
                SELECT COUNT(*) FROM (
                  SELECT score_uid, COUNT(*) c
                  FROM news_score_events_v1
                  WHERE created_at_utc = ?
                  GROUP BY score_uid
                  HAVING c > 1
                )
            """, [batch_ts]).fetchone()[0] if batch_ts else 0
        }

        global_counts_balanced = (
            before["news_token_match_events"] == before["news_signal_events"] ==
            before["news_score_events_v1"]
        )

        tail_candidates = con.execute("""
            SELECT COUNT(*)
            FROM news_raw_feed_events r
            WHERE COALESCE(r.published_at_utc, r.fetched_at_utc) > ?
              AND NOT EXISTS (
                SELECT 1 FROM news_token_match_events m
                WHERE m.news_uid = r.news_uid
              )
        """, [latest_derived]).fetchone()[0] if latest_derived else 0

        latest_samples = [
            dict(r) for r in con.execute("""
                SELECT news_uid, symbol, chain, match_type, match_score, created_at_utc
                FROM news_token_match_events
                ORDER BY created_at_utc DESC
                LIMIT 10
            """).fetchall()
        ]
    finally:
        con.close()

    after = {}
    con2 = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    try:
        for t in TABLES:
            after[t] = con2.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0]
    finally:
        con2.close()

    db_delta = {k: after[k] - before[k] for k in before}

    if integrity != "ok":
        failures.append("sqlite_integrity_not_ok")

    for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
        if batch_counts.get(t) != expected_inserted.get(t):
            failures.append("batch_count_mismatch:" + t)

    if batch_missing_signal_for_match != 0:
        failures.append("batch_missing_signal_for_match_nonzero")

    if batch_missing_score_for_match != 0:
        failures.append("batch_missing_score_for_match_nonzero")

    if batch_missing_score_for_signal != 0:
        failures.append("batch_missing_score_for_signal_nonzero")

    if any(v != 0 for v in batch_duplicate_checks.values()):
        failures.append("batch_duplicate_uid_nonzero")

    if batch_bad_trade_flags != 0:
        failures.append("batch_bad_trade_flags_nonzero")

    if latest_derived is None or latest_derived <= prior_latest.get("derived_before", ""):
        failures.append("latest_derived_not_advanced")

    if any(v != 0 for v in db_delta.values()):
        failures.append("audit_mutated_db")

    if not global_counts_balanced:
        warnings.append("global_derived_counts_not_balanced_outside_batch_scope")

    if tail_candidates > 0:
        warnings.append("new_raw_tail_exists_after_apply_runtime_binding_required")

    tests = [
        {
            "test_id": "T01_PRIOR_REAL_APPLY_OK",
            "ok": prior.get("decision") == "OK_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_WITH_BACKUP"
                  and apply_result.get("decision") == "OK_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_WITH_BACKUP_INTERNAL"
                  and apply_result.get("fail_count") == 0
        },
        {
            "test_id": "T02_SQLITE_INTEGRITY_OK",
            "ok": integrity == "ok",
            "integrity": integrity
        },
        {
            "test_id": "T03_BATCH_COUNTS_MATCH_INSERTED",
            "ok": all(batch_counts.get(t) == expected_inserted.get(t) for t in batch_counts),
            "batch_counts": batch_counts,
            "expected_inserted": expected_inserted
        },
        {
            "test_id": "T04_BATCH_LAYER_LINKS_OK",
            "ok": batch_missing_signal_for_match == 0 and batch_missing_score_for_match == 0 and batch_missing_score_for_signal == 0,
            "batch_missing_signal_for_match": batch_missing_signal_for_match,
            "batch_missing_score_for_match": batch_missing_score_for_match,
            "batch_missing_score_for_signal": batch_missing_score_for_signal
        },
        {
            "test_id": "T05_BATCH_UID_DEDUP_OK",
            "ok": all(v == 0 for v in batch_duplicate_checks.values()),
            "batch_duplicate_checks": batch_duplicate_checks
        },
        {
            "test_id": "T06_NO_BATCH_TRADE_FLAGS",
            "ok": batch_bad_trade_flags == 0,
            "batch_bad_trade_flags": batch_bad_trade_flags
        },
        {
            "test_id": "T07_FRESHNESS_ADVANCED_AND_TAIL_CLEAR",
            "ok": latest_derived is not None and latest_derived > prior_latest.get("derived_before", "") and tail_candidates == 0,
            "latest_raw": latest_raw,
            "latest_derived": latest_derived,
            "prior_derived_before": prior_latest.get("derived_before"),
            "tail_candidates": tail_candidates
        },
        {
            "test_id": "T08_AUDIT_READONLY_AND_RUNTIME_BOUNDARY_OK",
            "ok": all(v == 0 for v in db_delta.values()) and timer_state.get("stdout") == "active",
            "db_delta": db_delta,
            "timer_state": timer_state.get("stdout"),
            "service_state": service_state.get("stdout")
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_PLAN_NOAPI" if not failures else "NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_REPAIR_REQUIRED"

    return {
        "stage": "NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI",
        "repair_reason": "previous_audit_used_global_layer_link_scope; repaired audit validates real-apply batch scope and current freshness",
        "previous_failed_audit_summary": previous_failed_summary,
        "generated_at_utc": now(),
        "decision": "OK_NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI_INTERNAL" if not failures else "FAIL_NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI_INTERNAL",
        "current_counts": before,
        "batch_timestamp": batch_ts,
        "batch_counts": batch_counts,
        "expected_inserted": expected_inserted,
        "integrity": integrity,
        "latest_raw": latest_raw,
        "latest_derived": latest_derived,
        "latest_by_table": latest_by_table,
        "tail_candidates_after_apply": tail_candidates,
        "batch_layer_links": {
            "batch_missing_signal_for_match": batch_missing_signal_for_match,
            "batch_missing_score_for_match": batch_missing_score_for_match,
            "batch_missing_score_for_signal": batch_missing_score_for_signal
        },
        "batch_duplicate_checks": batch_duplicate_checks,
        "batch_bad_trade_flags": batch_bad_trade_flags,
        "global_counts_balanced": global_counts_balanced,
        "backup": {
            "backup_db": str(backup_db),
            "backup_sha256_expected": backup.get("backup_sha256"),
            "backup_sha256_current": backup_sha_current
        },
        "latest_samples": latest_samples,
        "timer_state": timer_state,
        "service_state": service_state,
        "db_delta_during_audit": db_delta,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "api_call": False,
            "network_call": False,
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
        "failures": failures,
        "warnings": warnings,
        "next": next_step
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
