
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, re, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_runtime_freshness_state_cleanup_apply_with_backup_noapi_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
DERIVED_HELPER = ROOT / "tools/news_derived_layer_refresher_v1.py"

def now():
    return datetime.now(timezone.utc).isoformat()

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "rc": p.returncode,
        "stdout": p.stdout.strip(),
        "stderr": p.stderr.strip()
    }

def table_exists(con, table):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        [table]
    ).fetchone() is not None

def table_cols(con, table):
    return [r[1] for r in con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()]

def counts(con):
    return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}

def duplicate_news_uid(con, table, limit=50):
    return [
        {"news_uid": r[0], "row_count": r[1]}
        for r in con.execute("""
            SELECT news_uid, COUNT(*) AS c
            FROM """ + q(table) + """
            GROUP BY news_uid
            HAVING COUNT(*) > 1
            ORDER BY c DESC, news_uid ASC
            LIMIT ?
        """, [limit]).fetchall()
    ]

def orphan_rows(con, table, limit=50):
    return [
        {"news_uid": r[0], "row_count": r[1]}
        for r in con.execute("""
            SELECT d.news_uid, COUNT(*) AS c
            FROM """ + q(table) + """ d
            LEFT JOIN news_raw_feed_events r ON r.news_uid = d.news_uid
            WHERE r.news_uid IS NULL
            GROUP BY d.news_uid
            ORDER BY c DESC, d.news_uid ASC
            LIMIT ?
        """, [limit]).fetchall()
    ]

def namespace_stats(con):
    rows = con.execute("""
        SELECT
          CASE
            WHEN news_uid LIKE 'hist_news_%' THEN 'historical_hist_news'
            WHEN news_uid LIKE 'news_%' THEN 'live_or_runtime_news'
            WHEN news_uid LIKE 'rss_%' THEN 'rss_news'
            ELSE 'other'
          END AS namespace,
          COUNT(*) AS c
        FROM news_raw_feed_events
        GROUP BY namespace
        ORDER BY namespace
    """).fetchall()
    return [{"namespace": r[0], "count": r[1]} for r in rows]

def hist_live_collision_check(con):
    raw_cols = table_cols(con, "news_raw_feed_events")
    result = {
        "raw_news_uid_duplicates": duplicate_news_uid(con, "news_raw_feed_events"),
        "match_news_uid_duplicates": duplicate_news_uid(con, "news_token_match_events"),
        "signal_news_uid_duplicates": duplicate_news_uid(con, "news_signal_events"),
        "score_news_uid_duplicates": duplicate_news_uid(con, "news_score_events_v1"),
        "hist_prefix_count": 0,
        "non_hist_count": 0,
        "namespace_stats": namespace_stats(con),
        "sample_hist": [],
        "sample_non_hist": [],
        "collision_risk": "LOW_IF_PREFIX_DISCIPLINE_MAINTAINED",
        "notes": []
    }

    result["hist_prefix_count"] = con.execute("SELECT COUNT(*) FROM news_raw_feed_events WHERE news_uid LIKE 'hist_news_%'").fetchone()[0]
    result["non_hist_count"] = con.execute("SELECT COUNT(*) FROM news_raw_feed_events WHERE news_uid NOT LIKE 'hist_news_%'").fetchone()[0]

    result["sample_hist"] = [
        dict(r) for r in con.execute("""
            SELECT news_uid, title, published_at_utc, fetched_at_utc
            FROM news_raw_feed_events
            WHERE news_uid LIKE 'hist_news_%'
            ORDER BY COALESCE(fetched_at_utc, published_at_utc) DESC
            LIMIT 10
        """).fetchall()
    ]

    result["sample_non_hist"] = [
        dict(r) for r in con.execute("""
            SELECT news_uid, title, published_at_utc, fetched_at_utc
            FROM news_raw_feed_events
            WHERE news_uid NOT LIKE 'hist_news_%'
            ORDER BY COALESCE(fetched_at_utc, published_at_utc) DESC
            LIMIT 10
        """).fetchall()
    ]

    if result["raw_news_uid_duplicates"]:
        result["collision_risk"] = "HIGH_DUPLICATE_RAW_NEWS_UID_PRESENT"
    elif result["match_news_uid_duplicates"]:
        result["collision_risk"] = "HIGH_DUPLICATE_MATCH_NEWS_UID_PRESENT"
    elif result["hist_prefix_count"] > 0 and result["non_hist_count"] > 0:
        result["collision_risk"] = "LOW_HIST_AND_NON_HIST_NAMESPACES_SEPARATED"
    elif result["hist_prefix_count"] > 0:
        result["collision_risk"] = "LOW_ONLY_HIST_PREFIX_PRESENT"
    else:
        result["collision_risk"] = "UNKNOWN_NO_HIST_PREFIX_PRESENT"

    if "event_hash" not in raw_cols:
        result["notes"].append("raw_event_hash_column_absent_schema_hardening_backlog")

    return result

def systemd_review():
    service_show = run(["systemctl", "show", SERVICE, "--no-pager"])
    timer_show = run(["systemctl", "show", TIMER, "--no-pager"])
    service_status = run(["systemctl", "is-active", SERVICE])
    timer_status = run(["systemctl", "is-active", TIMER])
    timer_enabled = run(["systemctl", "is-enabled", TIMER])

    service_unit = Path("/etc/systemd/system/" + SERVICE)
    timer_unit = Path("/etc/systemd/system/" + TIMER)

    service_text = service_unit.read_text(encoding="utf-8", errors="replace") if service_unit.exists() else ""
    timer_text = timer_unit.read_text(encoding="utf-8", errors="replace") if timer_unit.exists() else ""

    exec_lines = [line for line in service_text.splitlines() if line.strip().startswith("ExecStart=")]
    timer_lines = [line for line in timer_text.splitlines() if line.strip().startswith(("OnCalendar=", "OnBootSec=", "OnUnitActiveSec=", "OnActiveSec=", "Unit="))]

    return {
        "service_show_rc": service_show["rc"],
        "timer_show_rc": timer_show["rc"],
        "service_active": service_status["stdout"],
        "service_active_rc": service_status["rc"],
        "timer_active": timer_status["stdout"],
        "timer_active_rc": timer_status["rc"],
        "timer_enabled": timer_enabled["stdout"],
        "timer_enabled_rc": timer_enabled["rc"],
        "service_unit_exists": service_unit.exists(),
        "timer_unit_exists": timer_unit.exists(),
        "service_execstart_lines": exec_lines,
        "timer_schedule_lines": timer_lines,
        "service_text_sha256": hashlib.sha256(service_text.encode("utf-8")).hexdigest() if service_text else None,
        "timer_text_sha256": hashlib.sha256(timer_text.encode("utf-8")).hexdigest() if timer_text else None
    }

def runner_review():
    runner_text = RUNNER.read_text(encoding="utf-8", errors="replace") if RUNNER.exists() else ""
    helper_text = DERIVED_HELPER.read_text(encoding="utf-8", errors="replace") if DERIVED_HELPER.exists() else ""

    return {
        "runner_exists": RUNNER.exists(),
        "derived_helper_exists": DERIVED_HELPER.exists(),
        "runner_sha256": hashlib.sha256(runner_text.encode("utf-8")).hexdigest() if runner_text else None,
        "derived_helper_sha256": hashlib.sha256(helper_text.encode("utf-8")).hexdigest() if helper_text else None,
        "runner_mentions_original_backup": "ORIGINAL_RUNNER" in runner_text or "PRE_DERIVED_BINDING" in runner_text,
        "runner_mentions_derived_helper": "news_derived_layer_refresher_v1.py" in runner_text or "NEWS_DERIVED_REFRESH" in runner_text,
        "runner_mentions_write": "--write" in runner_text,
        "runner_mentions_stage": "--stage" in runner_text,
        "runner_mentions_db_path": "--db-path" in runner_text,
        "runner_line_count": len(runner_text.splitlines()) if runner_text else 0,
        "helper_line_count": len(helper_text.splitlines()) if helper_text else 0
    }

def freshness_review(con):
    info = {
        "exists": table_exists(con, "news_runtime_freshness_v1"),
        "target_historical_access": [],
        "latest": {},
        "ok_historical_access_synced": False
    }
    if not info["exists"]:
        return info

    cols = table_cols(con, "news_runtime_freshness_v1")
    info["columns"] = cols

    if "component" in cols:
        rows = con.execute("""
            SELECT *
            FROM news_runtime_freshness_v1
            WHERE component = 'NEWS_HISTORICAL_ACCESS_LAYER'
        """).fetchall()
        info["target_historical_access"] = [dict(r) for r in rows]

    for c in ["created_at_utc", "last_observed_at_utc"]:
        if c in cols:
            info["latest"][c] = con.execute("SELECT MAX(" + q(c) + ") FROM news_runtime_freshness_v1").fetchone()[0]

    if info["target_historical_access"]:
        r = info["target_historical_access"][0]
        info["ok_historical_access_synced"] = (
            r.get("heartbeat_status") == "OK_HISTORICAL_ACCESS_SYNCED"
            and int(r.get("raw_count", -1)) >= 353
            and int(r.get("match_count", -1)) >= 166
            and int(r.get("signal_count", -1)) >= 166
            and int(r.get("score_count", -1)) >= 166
        )

    return info

def main():
    generated_at = now()
    failures = []
    warnings = []

    prior = load_json(PRIOR)
    if prior.get("decision") != "OK_NEWS_RUNTIME_FRESHNESS_STATE_CLEANUP_APPLY_WITH_BACKUP_NOAPI":
        failures.append("prior_freshness_cleanup_not_ok")

    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        missing_tables = [t for t in TABLES if not table_exists(con, t)]
        db_counts = counts(con) if not missing_tables else {}
        orphan_checks = {
            "news_token_match_events": orphan_rows(con, "news_token_match_events") if table_exists(con, "news_token_match_events") else ["missing"],
            "news_signal_events": orphan_rows(con, "news_signal_events") if table_exists(con, "news_signal_events") else ["missing"],
            "news_score_events_v1": orphan_rows(con, "news_score_events_v1") if table_exists(con, "news_score_events_v1") else ["missing"]
        }
        collision = hist_live_collision_check(con) if not missing_tables else {}
        freshness = freshness_review(con)
        bad_trade_flags = con.execute("""
            SELECT COUNT(*)
            FROM news_token_match_events
            WHERE write_allowed != 0 OR trade_signal != 0 OR paper_signal != 0
        """).fetchone()[0] if table_exists(con, "news_token_match_events") else -1
    finally:
        con.close()

    sysd = systemd_review()
    runner = runner_review()

    if integrity != "ok":
        failures.append("sqlite_integrity_not_ok")
    if missing_tables:
        failures.append("missing_news_tables:" + ",".join(missing_tables))
    if any(orphan_checks.get(t) for t in orphan_checks):
        failures.append("orphan_derived_rows_present")
    if collision.get("raw_news_uid_duplicates"):
        failures.append("raw_news_uid_duplicates_present")
    if collision.get("match_news_uid_duplicates"):
        failures.append("match_news_uid_duplicates_present")
    if bad_trade_flags != 0:
        failures.append("bad_trade_flags_nonzero")
    if not freshness.get("ok_historical_access_synced"):
        failures.append("freshness_historical_access_not_synced")
    if not runner.get("runner_exists"):
        failures.append("news_runner_missing")
    if not runner.get("derived_helper_exists"):
        failures.append("derived_helper_missing")
    if not runner.get("runner_mentions_derived_helper"):
        failures.append("runner_derived_helper_binding_not_detected")
    if not sysd.get("timer_unit_exists"):
        failures.append("news_timer_unit_missing")
    if not sysd.get("service_unit_exists"):
        failures.append("news_service_unit_missing")

    if sysd.get("timer_active") != "active":
        warnings.append("news_timer_not_active")
    if sysd.get("timer_enabled") not in ["enabled", "static"]:
        warnings.append("news_timer_not_enabled_or_static")
    if collision.get("notes"):
        warnings.extend(collision.get("notes"))

    tests = [
        {
            "test_id": "T01_PRIOR_FRESHNESS_CLEANUP_OK",
            "ok": prior.get("decision") == "OK_NEWS_RUNTIME_FRESHNESS_STATE_CLEANUP_APPLY_WITH_BACKUP_NOAPI"
        },
        {
            "test_id": "T02_DB_INTEGRITY_AND_COUNTS_OK",
            "ok": integrity == "ok" and not missing_tables and db_counts.get("news_raw_feed_events", 0) >= 353 and db_counts.get("news_token_match_events", 0) >= 166,
            "integrity": integrity,
            "db_counts": db_counts,
            "missing_tables": missing_tables
        },
        {
            "test_id": "T03_NO_ORPHANS_AND_NO_BAD_TRADE_FLAGS",
            "ok": all(len(orphan_checks[t]) == 0 for t in orphan_checks) and bad_trade_flags == 0,
            "orphan_checks": orphan_checks,
            "bad_trade_flags": bad_trade_flags
        },
        {
            "test_id": "T04_UID_NAMESPACE_COLLISION_REVIEW_OK",
            "ok": not collision.get("raw_news_uid_duplicates") and not collision.get("match_news_uid_duplicates"),
            "collision": collision
        },
        {
            "test_id": "T05_FRESHNESS_STATE_SYNCED",
            "ok": freshness.get("ok_historical_access_synced") is True,
            "freshness": freshness
        },
        {
            "test_id": "T06_SYSTEMD_PRODUCER_UNITS_DISCOVERED_READONLY",
            "ok": sysd.get("service_unit_exists") is True and sysd.get("timer_unit_exists") is True,
            "systemd": sysd
        },
        {
            "test_id": "T07_RUNNER_AND_DERIVED_BINDING_PRESENT",
            "ok": runner.get("runner_exists") and runner.get("derived_helper_exists") and runner.get("runner_mentions_derived_helper"),
            "runner": runner
        },
        {
            "test_id": "T08_REVIEW_BOUNDARY_NOAPI_READONLY",
            "ok": True,
            "network_call": False,
            "api_call": False,
            "db_write": False,
            "service_change": False,
            "timer_change": False,
            "runner_executed": False,
            "paper_trade": False,
            "live_trade": False,
            "trade_authority": False
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI" if not failures else "NEWS_RUNTIME_STABILIZATION_REVIEW_HOLD"

    return {
        "stage": "NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW",
        "generated_at_utc": generated_at,
        "decision": "OK_NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW" if not failures else "FAIL_NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW",
        "prior": "data/control/news_runtime_freshness_state_cleanup_apply_with_backup_noapi_v1.json",
        "db_counts": db_counts,
        "integrity": integrity,
        "bad_trade_flags": bad_trade_flags,
        "orphan_checks": orphan_checks,
        "uid_collision_review": collision,
        "freshness_review": freshness,
        "systemd_review": sysd,
        "runner_review": runner,
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
            "runner_executed": False,
            "nginx_change": False,
            "paper_trade": False,
            "live_trade": False,
            "execution_authority": False
        },
        "remaining_after_this_if_ok": [
            "NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI",
            "NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN_AND_POST_AUDIT_SEAL"
        ],
        "failures": failures,
        "warnings": warnings,
        "next": next_step
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
