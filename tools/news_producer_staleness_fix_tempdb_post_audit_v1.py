
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
REAL_DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_producer_staleness_fix_tempdb_apply_dryrun_noapi_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def counts_ro(db):
    con = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True)
    out = {}
    try:
        for t in TABLES:
            out[t] = con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0]
    finally:
        con.close()
    return out

def scalar_ro(db, sql, params=None):
    if params is None:
        params = []
    con = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True)
    try:
        return con.execute(sql, params).fetchone()[0]
    finally:
        con.close()

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "rc": p.returncode,
        "stdout": p.stdout.strip(),
        "stderr": p.stderr.strip()
    }

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def main():
    prior = load(PRIOR)
    dryrun = prior.get("dryrun", {})
    temp_result = dryrun.get("tempdb_apply_result", {})
    tempdb_path = Path(str(dryrun.get("tempdb_path", "")))

    failures = []
    warnings = []

    real_before = counts_ro(REAL_DB)
    timer_before = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_before = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    if prior.get("decision") != "OK_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_APPLY_DRYRUN_NOAPI":
        failures.append("prior_tempdb_apply_dryrun_not_ok")

    if dryrun.get("decision") != "OK_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_APPLY_DRYRUN_INTERNAL":
        failures.append("prior_internal_not_ok")

    if dryrun.get("failures") not in ([], None):
        failures.append("prior_internal_failures_not_empty")

    if prior.get("failures") not in ([], None):
        failures.append("prior_outer_failures_not_empty")

    if dryrun.get("test_count") != 8:
        failures.append("prior_test_count_not_8")

    if dryrun.get("ok_count") != 8:
        failures.append("prior_ok_count_not_8")

    if dryrun.get("fail_count") != 0:
        failures.append("prior_fail_count_not_zero")

    if not tempdb_path.exists():
        failures.append("tempdb_path_missing")

    tempdb_counts = {}
    tempdb_integrity = None
    tempdb_latest = {}
    tempdb_unique_checks = {}

    if tempdb_path.exists():
        tempdb_counts = counts_ro(tempdb_path)
        tempdb_integrity = scalar_ro(tempdb_path, "PRAGMA integrity_check")

        for table in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
            tempdb_latest[table] = scalar_ro(
                tempdb_path,
                "SELECT MAX(created_at_utc) FROM " + q(table) + " WHERE created_at_utc IS NOT NULL"
            )

        tempdb_unique_checks["match_uid_duplicates"] = scalar_ro(
            tempdb_path,
            """
            SELECT COUNT(*) FROM (
              SELECT match_uid, COUNT(*) c
              FROM news_token_match_events
              GROUP BY match_uid
              HAVING c > 1
            )
            """
        )
        tempdb_unique_checks["signal_uid_duplicates"] = scalar_ro(
            tempdb_path,
            """
            SELECT COUNT(*) FROM (
              SELECT signal_uid, COUNT(*) c
              FROM news_signal_events
              GROUP BY signal_uid
              HAVING c > 1
            )
            """
        )
        tempdb_unique_checks["score_uid_duplicates"] = scalar_ro(
            tempdb_path,
            """
            SELECT COUNT(*) FROM (
              SELECT score_uid, COUNT(*) c
              FROM news_score_events_v1
              GROUP BY score_uid
              HAVING c > 1
            )
            """
        )

        expected_after = temp_result.get("tempdb_after", {})
        for t in TABLES:
            if tempdb_counts.get(t) != expected_after.get(t):
                failures.append("tempdb_count_mismatch:" + t)

        if tempdb_integrity != "ok":
            failures.append("tempdb_integrity_not_ok")

        for k, v in tempdb_unique_checks.items():
            if v != 0:
                failures.append("tempdb_duplicate_uid:" + k)

    temp_delta = temp_result.get("tempdb_delta", {})
    if temp_delta.get("news_raw_feed_events") != 0:
        failures.append("tempdb_raw_delta_not_zero")

    for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
        if int(temp_delta.get(t) or 0) <= 0:
            failures.append("tempdb_delta_not_positive:" + t)

    second_pass_delta = temp_result.get("idempotency_second_pass_delta", {})
    if any(v != 0 for v in second_pass_delta.values()):
        failures.append("idempotency_second_pass_delta_not_zero")

    if temp_result.get("idempotency_second_pass_remaining_candidates") != 0:
        failures.append("idempotency_remaining_candidates_not_zero")

    real_after = counts_ro(REAL_DB)
    real_delta = {k: real_after[k] - real_before[k] for k in real_before}

    timer_after = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_after = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    if any(v != 0 for v in real_delta.values()):
        failures.append("real_db_delta_not_zero")

    if timer_before.get("stdout") != timer_after.get("stdout"):
        failures.append("timer_state_changed")

    if service_before.get("stdout") != service_after.get("stdout"):
        warnings.append("service_state_changed_during_post_audit")

    carried_warnings = prior.get("warnings", []) + dryrun.get("warnings", [])
    warnings.extend(carried_warnings)

    tests = [
        {
            "test_id": "T01_PRIOR_TEMPDB_DRYRUN_OK",
            "ok": prior.get("decision") == "OK_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_APPLY_DRYRUN_NOAPI"
                  and dryrun.get("decision") == "OK_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_APPLY_DRYRUN_INTERNAL"
                  and dryrun.get("fail_count") == 0
        },
        {
            "test_id": "T02_TEMPDB_FILE_EXISTS_AND_INTEGRITY_OK",
            "ok": tempdb_path.exists() and tempdb_integrity == "ok",
            "tempdb_path": str(tempdb_path),
            "integrity_check": tempdb_integrity,
            "sha256": sha256(tempdb_path)
        },
        {
            "test_id": "T03_TEMPDB_COUNTS_MATCH_ARTIFACT",
            "ok": tempdb_path.exists() and tempdb_counts == temp_result.get("tempdb_after", {}),
            "tempdb_counts": tempdb_counts,
            "artifact_tempdb_after": temp_result.get("tempdb_after", {})
        },
        {
            "test_id": "T04_TEMPDB_UID_DEDUP_OK",
            "ok": all(v == 0 for v in tempdb_unique_checks.values()) if tempdb_unique_checks else False,
            "unique_checks": tempdb_unique_checks
        },
        {
            "test_id": "T05_IDEMPOTENCY_CONFIRMED",
            "ok": all(v == 0 for v in second_pass_delta.values()) and temp_result.get("idempotency_second_pass_remaining_candidates") == 0,
            "second_pass_delta": second_pass_delta,
            "remaining_candidates": temp_result.get("idempotency_second_pass_remaining_candidates")
        },
        {
            "test_id": "T06_REAL_DB_UNTOUCHED",
            "ok": all(v == 0 for v in real_delta.values()),
            "real_db_delta": real_delta
        },
        {
            "test_id": "T07_RUNTIME_BOUNDARY_UNCHANGED",
            "ok": timer_before.get("stdout") == timer_after.get("stdout"),
            "timer_before": timer_before.get("stdout"),
            "timer_after": timer_after.get("stdout"),
            "service_before": service_before.get("stdout"),
            "service_after": service_after.get("stdout")
        },
        {
            "test_id": "T08_READY_FOR_REAL_APPLY_PLAN",
            "ok": len(failures) == 0,
            "next_if_ok": "NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_PLAN_NOAPI"
        }
    ]

    for t in tests:
        if t.get("ok") is not True and not str(t["test_id"]).endswith("T08_READY_FOR_REAL_APPLY_PLAN"):
            failures.append("test_failed:" + t["test_id"])

    decision = "OK_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_POST_AUDIT_INTERNAL" if not failures else "FAIL_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_POST_AUDIT_INTERNAL"
    next_step = "NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_PLAN_NOAPI" if not failures else "NEWS_PRODUCER_STALENESS_FIX_TEMPDB_POST_AUDIT_REPAIR_REQUIRED"

    return {
        "stage": "NEWS_PRODUCER_STALENESS_FIX_TEMPDB_POST_AUDIT_NOAPI",
        "generated_at_utc": now(),
        "decision": decision,
        "prior_tempdb_apply_dryrun": "data/control/news_producer_staleness_fix_tempdb_apply_dryrun_noapi_v1.json",
        "tempdb_path": str(tempdb_path),
        "tempdb_integrity_check": tempdb_integrity,
        "tempdb_counts": tempdb_counts,
        "tempdb_delta": temp_delta,
        "tempdb_latest": tempdb_latest,
        "tempdb_uid_duplicate_checks": tempdb_unique_checks,
        "real_db_before": real_before,
        "real_db_after": real_after,
        "real_db_delta": real_delta,
        "timer_before": timer_before,
        "timer_after": timer_after,
        "service_before": service_before,
        "service_after": service_after,
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
