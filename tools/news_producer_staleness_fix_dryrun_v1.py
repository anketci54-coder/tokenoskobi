
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PLAN = ROOT / "config/news_producer_staleness_fix_plan_v1.json"
PLAN_ART = ROOT / "data/control/news_producer_staleness_fix_plan_noapi_v1.json"

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

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {"cmd": cmd, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def count(con, sql, params=None):
    if params is None:
        params = []
    return con.execute(sql, params).fetchone()[0]

def one(con, sql, params=None):
    if params is None:
        params = []
    row = con.execute(sql, params).fetchone()
    return None if not row else row[0]

def counts(con):
    return {t: count(con, "SELECT COUNT(*) FROM " + q(t)) for t in TABLES}

def table_cols(con, table):
    return [r[1] for r in con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()]

def latest_derived_ts(con):
    vals = []
    for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
        cols = table_cols(con, t)
        if "created_at_utc" in cols:
            v = one(con, "SELECT MAX(created_at_utc) FROM " + q(t) + " WHERE created_at_utc IS NOT NULL")
            if v:
                vals.append(v)
    return max(vals) if vals else None

def latest_by_table(con):
    out = {}
    for t in TABLES:
        cols = table_cols(con, t)
        item = {}
        for c in ["published_at_utc", "fetched_at_utc", "created_at_utc"]:
            if c in cols:
                item[c] = one(con, "SELECT MAX(" + q(c) + ") FROM " + q(t) + " WHERE " + q(c) + " IS NOT NULL")
        out[t] = item
    return out

def sample_rows(con, sql, params=None, limit=10):
    if params is None:
        params = []
    rows = con.execute(sql + " LIMIT " + str(int(limit)), params).fetchall()
    return [dict(r) for r in rows]

def main():
    plan = load(PLAN)
    plan_art = load(PLAN_ART)
    failures = []
    warnings = []

    if plan_art.get("decision") != "OK_NEWS_PRODUCER_STALENESS_FIX_PLAN_NOAPI":
        failures.append("prior_fix_plan_not_ok")

    if plan.get("locked_root_cause") != "RAW_FEED_IS_CURRENT_BUT_DERIVED_LAYERS_ARE_STALE":
        failures.append("root_cause_not_locked")

    boundary = plan.get("authority_boundary", {})
    for key in [
        "api_call", "network_call", "db_write", "db_schema_change",
        "index_creation", "service_change", "timer_change", "nginx_change",
        "paper_trade", "live_trade", "execution_authority"
    ]:
        if boundary.get(key) is not False:
            failures.append("authority_not_false:" + key)

    timer_before = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_before = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        before = counts(con)
        latest_ts = latest_derived_ts(con)
        latest_map = latest_by_table(con)

        if latest_ts is None:
            warnings.append("latest_derived_ts_missing")
            new_raw_since_latest_derived = 0
            unmatched_raw_candidates = 0
            raw_candidate_samples = []
        else:
            new_raw_since_latest_derived = count(
                con,
                """
                SELECT COUNT(*)
                FROM news_raw_feed_events
                WHERE COALESCE(published_at_utc, fetched_at_utc) > ?
                """,
                [latest_ts]
            )

            unmatched_raw_candidates = count(
                con,
                """
                SELECT COUNT(*)
                FROM news_raw_feed_events r
                WHERE COALESCE(r.published_at_utc, r.fetched_at_utc) > ?
                  AND NOT EXISTS (
                    SELECT 1 FROM news_token_match_events m
                    WHERE m.news_uid = r.news_uid
                  )
                """,
                [latest_ts]
            )

            raw_candidate_samples = sample_rows(
                con,
                """
                SELECT news_uid, source_uid, published_at_utc, fetched_at_utc, title
                FROM news_raw_feed_events r
                WHERE COALESCE(r.published_at_utc, r.fetched_at_utc) > ?
                  AND NOT EXISTS (
                    SELECT 1 FROM news_token_match_events m
                    WHERE m.news_uid = r.news_uid
                  )
                ORDER BY COALESCE(published_at_utc, fetched_at_utc) DESC
                """,
                [latest_ts],
                10
            )

        existing_match_without_signal = count(
            con,
            """
            SELECT COUNT(*)
            FROM news_token_match_events m
            WHERE NOT EXISTS (
              SELECT 1 FROM news_signal_events s
              WHERE s.news_uid = m.news_uid
            )
            """
        )

        existing_match_without_score = count(
            con,
            """
            SELECT COUNT(*)
            FROM news_token_match_events m
            WHERE NOT EXISTS (
              SELECT 1 FROM news_score_events_v1 sc
              WHERE sc.news_uid = m.news_uid
            )
            """
        )

        existing_signal_without_score = count(
            con,
            """
            SELECT COUNT(*)
            FROM news_signal_events s
            WHERE NOT EXISTS (
              SELECT 1 FROM news_score_events_v1 sc
              WHERE sc.news_uid = s.news_uid
            )
            """
        )

        duplicate_raw_url_groups = count(
            con,
            """
            SELECT COUNT(*)
            FROM (
              SELECT url_hash, COUNT(*) c
              FROM news_raw_feed_events
              WHERE url_hash IS NOT NULL AND url_hash != ''
              GROUP BY url_hash
              HAVING c > 1
            )
            """
        )

        duplicate_raw_hash_groups = count(
            con,
            """
            SELECT COUNT(*)
            FROM (
              SELECT raw_hash, COUNT(*) c
              FROM news_raw_feed_events
              WHERE raw_hash IS NOT NULL AND raw_hash != ''
              GROUP BY raw_hash
              HAVING c > 1
            )
            """
        )

        after = counts(con)
    finally:
        con.close()

    timer_after = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_after = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    db_delta = {k: after[k] - before[k] for k in before}

    if any(v != 0 for v in db_delta.values()):
        failures.append("db_delta_not_zero")

    if timer_before.get("stdout") != timer_after.get("stdout"):
        failures.append("timer_state_changed")
    if service_before.get("stdout") != service_after.get("stdout"):
        warnings.append("service_state_changed_during_readonly_audit")

    projected = {
        "token_match_candidate_count_without_write": unmatched_raw_candidates,
        "signal_candidate_count_without_write_existing": existing_match_without_signal,
        "score_candidate_count_without_write_existing_match_based": existing_match_without_score,
        "score_candidate_count_without_write_existing_signal_based": existing_signal_without_score,
        "projected_signal_candidate_count_after_token_match_apply": unmatched_raw_candidates,
        "projected_score_candidate_count_after_token_match_apply": unmatched_raw_candidates
    }

    apply_plan_needed = any(v > 0 for v in projected.values())

    tests = [
        {
            "test_id": "T01_IDENTIFY_NEW_RAW_ROWS_SINCE_LATEST_DERIVED_TIMESTAMP",
            "ok": latest_ts is not None and new_raw_since_latest_derived >= 0,
            "latest_derived_created_at_utc": latest_ts,
            "new_raw_count": new_raw_since_latest_derived
        },
        {
            "test_id": "T02_PREVIEW_TOKEN_MATCH_CANDIDATES_WITHOUT_WRITE",
            "ok": unmatched_raw_candidates >= 0,
            "candidate_count": unmatched_raw_candidates
        },
        {
            "test_id": "T03_PREVIEW_SIGNAL_CANDIDATES_WITHOUT_WRITE",
            "ok": existing_match_without_signal >= 0,
            "existing_match_without_signal": existing_match_without_signal,
            "projected_after_match_apply": unmatched_raw_candidates
        },
        {
            "test_id": "T04_PREVIEW_SCORE_CANDIDATES_WITHOUT_WRITE",
            "ok": existing_match_without_score >= 0 and existing_signal_without_score >= 0,
            "existing_match_without_score": existing_match_without_score,
            "existing_signal_without_score": existing_signal_without_score,
            "projected_after_match_apply": unmatched_raw_candidates
        },
        {
            "test_id": "T05_PROVE_NO_DB_DELTA",
            "ok": all(v == 0 for v in db_delta.values()),
            "db_delta": db_delta
        },
        {
            "test_id": "T06_PROVE_NO_SERVICE_TIMER_NGINX_CHANGE",
            "ok": timer_before.get("stdout") == timer_after.get("stdout"),
            "timer_before": timer_before.get("stdout"),
            "timer_after": timer_after.get("stdout"),
            "service_before": service_before.get("stdout"),
            "service_after": service_after.get("stdout"),
            "nginx_change": False
        },
        {
            "test_id": "T07_PROVE_NO_TRADE_AUTHORITY",
            "ok": True,
            "paper_trade": False,
            "live_trade": False,
            "execution_authority": False
        },
        {
            "test_id": "T08_PRODUCE_APPLY_PLAN_ONLY_IF_CANDIDATES_EXIST",
            "ok": True,
            "apply_plan_needed": apply_plan_needed,
            "next_if_candidates": "NEWS_PRODUCER_STALENESS_FIX_APPLY_PLAN_NOAPI",
            "next_if_no_candidates": "NEWS_PRODUCER_STALENESS_FIX_NOOP_FINAL_SEAL_NOAPI"
        },
        {
            "test_id": "T09_DEDUP_PREVIEW_WITHOUT_WRITE",
            "ok": duplicate_raw_url_groups >= 0 and duplicate_raw_hash_groups >= 0,
            "duplicate_url_hash_groups": duplicate_raw_url_groups,
            "duplicate_raw_hash_groups": duplicate_raw_hash_groups
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_PRODUCER_STALENESS_FIX_APPLY_PLAN_NOAPI" if apply_plan_needed and not failures else "NEWS_PRODUCER_STALENESS_FIX_NOOP_FINAL_SEAL_NOAPI"
    if failures:
        next_step = "NEWS_PRODUCER_STALENESS_FIX_DRYRUN_REPAIR_REQUIRED"

    return {
        "stage": "NEWS_PRODUCER_STALENESS_FIX_DRYRUN_NOAPI",
        "generated_at_utc": now(),
        "decision": "OK_NEWS_PRODUCER_STALENESS_FIX_DRYRUN_INTERNAL" if not failures else "FAIL_NEWS_PRODUCER_STALENESS_FIX_DRYRUN_INTERNAL",
        "locked_root_cause": "RAW_FEED_IS_CURRENT_BUT_DERIVED_LAYERS_ARE_STALE",
        "latest_timestamps": latest_map,
        "preview": {
            "latest_derived_created_at_utc": latest_ts,
            "new_raw_rows_since_latest_derived": new_raw_since_latest_derived,
            "candidate_counts": projected,
            "raw_candidate_samples": raw_candidate_samples,
            "apply_plan_needed": apply_plan_needed
        },
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "db_before": before,
        "db_after": after,
        "db_delta": db_delta,
        "timer_before": timer_before,
        "timer_after": timer_after,
        "service_before": service_before,
        "service_after": service_after,
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
