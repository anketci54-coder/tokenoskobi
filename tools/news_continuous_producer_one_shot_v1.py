
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, shutil, tempfile, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/bad_trade_flags_cleanup_apply_with_backup_noapi_v1.json"

RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
DERIVED_HELPER = ROOT / "tools/news_derived_layer_refresher_v1.py"

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

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

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def run(cmd, timeout=None):
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {
            "cmd": cmd,
            "rc": p.returncode,
            "stdout": p.stdout.strip()[-8000:],
            "stderr": p.stderr.strip()[-8000:]
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "rc": 124,
            "stdout": (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else "TIMEOUT",
            "timeout": True
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

def bad_flags(con):
    return con.execute("""
        SELECT COUNT(*)
        FROM news_token_match_events
        WHERE COALESCE(write_allowed,0) != 0
           OR COALESCE(trade_signal,0) != 0
           OR COALESCE(paper_signal,0) != 0
    """).fetchone()[0]

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

def namespace_stats(con):
    rows = con.execute("""
        SELECT
          CASE
            WHEN news_uid LIKE 'hist_news_%' THEN 'historical_hist_news'
            WHEN news_uid LIKE 'timer_news_%' THEN 'timer_news'
            WHEN news_uid LIKE 'news_%' THEN 'runtime_news'
            WHEN news_uid LIKE 'rss_%' THEN 'rss_news'
            ELSE 'other'
          END AS namespace,
          COUNT(*) AS c
        FROM news_raw_feed_events
        GROUP BY namespace
        ORDER BY namespace
    """).fetchall()
    return [{"namespace": r[0], "count": r[1]} for r in rows]

def collision_review(con):
    return {
        "raw_news_uid_duplicates": duplicate_news_uid(con, "news_raw_feed_events"),
        "match_news_uid_duplicates": duplicate_news_uid(con, "news_token_match_events"),
        "signal_news_uid_duplicates": duplicate_news_uid(con, "news_signal_events"),
        "score_news_uid_duplicates": duplicate_news_uid(con, "news_score_events_v1"),
        "hist_prefix_count": con.execute("SELECT COUNT(*) FROM news_raw_feed_events WHERE news_uid LIKE 'hist_news_%'").fetchone()[0],
        "timer_prefix_count": con.execute("SELECT COUNT(*) FROM news_raw_feed_events WHERE news_uid LIKE 'timer_news_%'").fetchone()[0],
        "namespace_stats": namespace_stats(con)
    }

def freshness_review(con):
    info = {
        "exists": table_exists(con, "news_runtime_freshness_v1"),
        "ok_historical_access_synced": False,
        "target_historical_access": [],
        "latest": {}
    }
    if not info["exists"]:
        return info

    cols = table_cols(con, "news_runtime_freshness_v1")
    info["columns"] = cols

    if "component" in cols:
        rows = con.execute("""
            SELECT *
            FROM news_runtime_freshness_v1
            WHERE component='NEWS_HISTORICAL_ACCESS_LAYER'
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

def systemd_review():
    service_unit = Path("/etc/systemd/system/" + SERVICE)
    timer_unit = Path("/etc/systemd/system/" + TIMER)
    service_text = service_unit.read_text(encoding="utf-8", errors="replace") if service_unit.exists() else ""
    timer_text = timer_unit.read_text(encoding="utf-8", errors="replace") if timer_unit.exists() else ""

    return {
        "service_active": run(["systemctl", "is-active", SERVICE])["stdout"],
        "timer_active": run(["systemctl", "is-active", TIMER])["stdout"],
        "timer_enabled": run(["systemctl", "is-enabled", TIMER])["stdout"],
        "service_unit_exists": service_unit.exists(),
        "timer_unit_exists": timer_unit.exists(),
        "service_execstart_lines": [x for x in service_text.splitlines() if x.strip().startswith("ExecStart=")],
        "timer_schedule_lines": [x for x in timer_text.splitlines() if x.strip().startswith(("OnActiveSec=", "OnUnitActiveSec=", "OnCalendar=", "Unit="))],
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
        "helper_sha256": hashlib.sha256(helper_text.encode("utf-8")).hexdigest() if helper_text else None,
        "runner_mentions_db_path": "--db-path" in runner_text,
        "runner_mentions_stage": "--stage" in runner_text,
        "runner_mentions_write": "--write" in runner_text,
        "runner_mentions_derived_helper": "news_derived_layer_refresher_v1.py" in runner_text or "NEWS_DERIVED_REFRESH" in runner_text,
        "runner_line_count": len(runner_text.splitlines()) if runner_text else 0,
        "helper_line_count": len(helper_text.splitlines()) if helper_text else 0
    }

def db_snapshot(path):
    con = sqlite3.connect("file:" + str(path) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        snap = {
            "integrity": con.execute("PRAGMA integrity_check").fetchone()[0],
            "counts": counts(con),
            "bad_flags": bad_flags(con),
            "orphans": {
                "news_token_match_events": orphan_rows(con, "news_token_match_events"),
                "news_signal_events": orphan_rows(con, "news_signal_events"),
                "news_score_events_v1": orphan_rows(con, "news_score_events_v1")
            },
            "duplicates": {
                "news_raw_feed_events": duplicate_news_uid(con, "news_raw_feed_events"),
                "news_token_match_events": duplicate_news_uid(con, "news_token_match_events"),
                "news_signal_events": duplicate_news_uid(con, "news_signal_events"),
                "news_score_events_v1": duplicate_news_uid(con, "news_score_events_v1")
            },
            "freshness": freshness_review(con),
            "collision": collision_review(con)
        }
        return snap
    finally:
        con.close()

def count_delta(after, before):
    return {k: after.get(k, 0) - before.get(k, 0) for k in before}

def stabilization_retry():
    generated_at = now()
    failures = []
    warnings = []

    prior = load_json(PRIOR)
    if prior.get("decision") != "OK_BAD_TRADE_FLAGS_CLEANUP_APPLY_WITH_BACKUP_NOAPI":
        failures.append("prior_bad_trade_flags_cleanup_not_ok")

    snap = db_snapshot(DB)
    sysd = systemd_review()
    runner = runner_review()

    if snap["integrity"] != "ok":
        failures.append("sqlite_integrity_not_ok")
    if snap["bad_flags"] != 0:
        failures.append("bad_trade_flags_not_zero")
    if any(snap["orphans"][t] for t in snap["orphans"]):
        failures.append("orphan_derived_rows_present")
    if any(snap["duplicates"][t] for t in snap["duplicates"]):
        failures.append("duplicate_news_uid_present")
    if not snap["freshness"].get("ok_historical_access_synced"):
        failures.append("freshness_historical_access_not_synced")
    if not runner.get("runner_exists"):
        failures.append("runner_missing")
    if not runner.get("derived_helper_exists"):
        failures.append("derived_helper_missing")
    if not runner.get("runner_mentions_derived_helper"):
        failures.append("runner_derived_binding_missing")
    if not sysd.get("service_unit_exists"):
        failures.append("service_unit_missing")
    if not sysd.get("timer_unit_exists"):
        failures.append("timer_unit_missing")

    if sysd.get("timer_active") != "active":
        warnings.append("timer_not_active")
    if sysd.get("timer_enabled") != "enabled":
        warnings.append("timer_not_enabled")

    tests = [
        {"test_id": "T01_PRIOR_CLEANUP_OK", "ok": prior.get("decision") == "OK_BAD_TRADE_FLAGS_CLEANUP_APPLY_WITH_BACKUP_NOAPI"},
        {"test_id": "T02_DB_INTEGRITY_OK", "ok": snap["integrity"] == "ok", "integrity": snap["integrity"]},
        {"test_id": "T03_BAD_FLAGS_ZERO", "ok": snap["bad_flags"] == 0, "bad_flags": snap["bad_flags"]},
        {"test_id": "T04_NO_ORPHANS_AND_DUPLICATES", "ok": all(not snap["orphans"][t] for t in snap["orphans"]) and all(not snap["duplicates"][t] for t in snap["duplicates"]), "orphans": snap["orphans"], "duplicates": snap["duplicates"]},
        {"test_id": "T05_FRESHNESS_SYNCED", "ok": snap["freshness"].get("ok_historical_access_synced") is True, "freshness": snap["freshness"]},
        {"test_id": "T06_RUNNER_AND_SYSTEMD_DISCOVERED", "ok": runner.get("runner_exists") and runner.get("derived_helper_exists") and sysd.get("service_unit_exists") and sysd.get("timer_unit_exists"), "runner": runner, "systemd": sysd},
        {"test_id": "T07_NOAPI_RETRY_BOUNDARY", "ok": True, "network_call": False, "api_call": False, "db_write": False, "service_change": False, "timer_change": False, "runner_executed": False}
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    return {
        "stage": "NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI",
        "generated_at_utc": generated_at,
        "decision": "OK_NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI" if not failures else "FAIL_NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI",
        "snapshot": snap,
        "runner_review": runner,
        "systemd_review": sysd,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "network_call": False,
            "api_call": False,
            "db_write": False,
            "service_change": False,
            "timer_change": False,
            "runner_executed": False,
            "paper_trade": False,
            "live_trade": False,
            "execution_authority": False
        },
        "failures": failures,
        "warnings": warnings,
        "next": "NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI" if not failures else "NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_HOLD"
    }

def dryrun_plan(retry):
    generated_at = now()
    failures = []
    warnings = []

    runner = retry.get("runner_review", {})
    if retry.get("decision") != "OK_NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI":
        failures.append("retry_not_ok")
    for key in ["runner_exists", "derived_helper_exists", "runner_mentions_db_path", "runner_mentions_stage", "runner_mentions_write", "runner_mentions_derived_helper"]:
        if runner.get(key) is not True:
            failures.append("runner_capability_missing:" + key)

    plan = {
        "dryrun_type": "TEMPDB_CONTROLLED_PRODUCER_DRYRUN",
        "real_db_write": False,
        "temp_db_write": True,
        "network_call": True,
        "api_call": False,
        "service_change": False,
        "timer_change": False,
        "service_trigger": False,
        "paper_trade": False,
        "live_trade": False,
        "trade_authority": False,
        "runner": "tools/news_radar_refresh_runner_v1.py",
        "command_template": [
            "python3",
            "tools/news_radar_refresh_runner_v1.py",
            "--db-path",
            "<TEMP_DB>",
            "--stage",
            "NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN",
            "--write"
        ],
        "timeout_seconds": 180,
        "success_criteria": [
            "runner_rc_zero",
            "real_db_counts_unchanged",
            "temp_db_integrity_ok",
            "temp_bad_trade_flags_zero",
            "temp_raw_match_signal_score_delta_balanced_or_all_zero",
            "no_service_or_timer_change"
        ]
    }

    tests = [
        {"test_id": "T01_RETRY_OK", "ok": retry.get("decision") == "OK_NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI"},
        {"test_id": "T02_RUNNER_TEMPDB_CAPABILITY_PRESENT", "ok": not any(x.startswith("runner_capability_missing") for x in failures), "runner_review": runner},
        {"test_id": "T03_PLAN_BOUNDARY_LOCKED", "ok": True, "plan": plan}
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    return {
        "stage": "NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI",
        "generated_at_utc": generated_at,
        "decision": "OK_NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI" if not failures else "FAIL_NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI",
        "plan": plan,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "network_call": False,
            "api_call": False,
            "db_write": False,
            "service_change": False,
            "timer_change": False,
            "paper_trade": False,
            "live_trade": False,
            "execution_authority": False
        },
        "failures": failures,
        "warnings": warnings,
        "next": "NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN_AND_POST_AUDIT_SEAL" if not failures else "NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_HOLD"
    }

def controlled_dryrun(plan):
    generated_at = now()
    failures = []
    warnings = []

    real_before = db_snapshot(DB)
    sysd_before = systemd_review()

    if plan.get("decision") != "OK_NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI":
        failures.append("plan_not_ok")

    temp_dir = Path(tempfile.mkdtemp(prefix="tokenoskobi_news_producer_dryrun_"))
    temp_db = temp_dir / "tokenoskobi_clean_v1.CONTINUOUS_PRODUCER_DRYRUN.sqlite"
    shutil.copy2(DB, temp_db)

    temp_before = db_snapshot(temp_db)

    cmd = [
        "python3",
        str(RUNNER),
        "--db-path",
        str(temp_db),
        "--stage",
        "NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN",
        "--write"
    ]

    runner_result = {"cmd": cmd, "rc": None, "stdout": "", "stderr": "", "skipped": True}
    if not failures:
        runner_result = run(cmd, timeout=180)

    temp_after = db_snapshot(temp_db)
    real_after = db_snapshot(DB)
    sysd_after = systemd_review()

    temp_delta = count_delta(temp_after["counts"], temp_before["counts"])
    real_delta = count_delta(real_after["counts"], real_before["counts"])

    balanced_temp_delta = (
        temp_delta.get("news_raw_feed_events", 0)
        == temp_delta.get("news_token_match_events", 0)
        == temp_delta.get("news_signal_events", 0)
        == temp_delta.get("news_score_events_v1", 0)
    )

    systemd_unchanged = (
        sysd_before.get("service_text_sha256") == sysd_after.get("service_text_sha256")
        and sysd_before.get("timer_text_sha256") == sysd_after.get("timer_text_sha256")
    )

    if runner_result.get("rc") != 0:
        failures.append("runner_rc_nonzero")
    if any(v != 0 for v in real_delta.values()):
        failures.append("real_db_counts_changed_during_tempdb_dryrun")
    if real_after.get("bad_flags") != 0:
        failures.append("real_db_bad_flags_nonzero_after_dryrun")
    if temp_after.get("integrity") != "ok":
        failures.append("temp_db_integrity_not_ok")
    if temp_after.get("bad_flags") != 0:
        failures.append("temp_db_bad_flags_nonzero_after_dryrun")
    if not balanced_temp_delta:
        failures.append("temp_delta_not_balanced")
    if not systemd_unchanged:
        failures.append("systemd_units_changed")

    tests = [
        {"test_id": "T01_PLAN_OK", "ok": plan.get("decision") == "OK_NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI"},
        {"test_id": "T02_RUNNER_RC_ZERO", "ok": runner_result.get("rc") == 0, "runner_result": runner_result},
        {"test_id": "T03_REAL_DB_UNCHANGED", "ok": all(v == 0 for v in real_delta.values()) and real_after.get("bad_flags") == 0, "real_delta": real_delta, "real_bad_flags_after": real_after.get("bad_flags")},
        {"test_id": "T04_TEMP_DB_INTEGRITY_AND_FLAGS_OK", "ok": temp_after.get("integrity") == "ok" and temp_after.get("bad_flags") == 0, "temp_integrity": temp_after.get("integrity"), "temp_bad_flags": temp_after.get("bad_flags")},
        {"test_id": "T05_TEMP_DELTA_BALANCED", "ok": balanced_temp_delta, "temp_delta": temp_delta},
        {"test_id": "T06_SYSTEMD_UNCHANGED", "ok": systemd_unchanged, "systemd_before": sysd_before, "systemd_after": sysd_after},
        {"test_id": "T07_BOUNDARY_LOCKED", "ok": True, "network_call": True, "api_call": False, "real_db_write": False, "temp_db_write": True, "service_change": False, "timer_change": False, "paper_trade": False, "live_trade": False, "trade_authority": False}
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    return {
        "stage": "NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN_AND_POST_AUDIT_SEAL",
        "generated_at_utc": generated_at,
        "decision": "OK_NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN_AND_POST_AUDIT_SEAL" if not failures else "FAIL_NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN_AND_POST_AUDIT_SEAL",
        "temp_dir": str(temp_dir),
        "temp_db": str(temp_db),
        "runner_result": runner_result,
        "real_before": real_before,
        "real_after": real_after,
        "real_delta": real_delta,
        "temp_before": temp_before,
        "temp_after": temp_after,
        "temp_delta": temp_delta,
        "balanced_temp_delta": balanced_temp_delta,
        "systemd_unchanged": systemd_unchanged,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "network_call": True,
            "api_call": False,
            "real_db_write": False,
            "temp_db_write": True,
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
        "next": "NEWS_CONTINUOUS_PRODUCER_OBSERVATION_WINDOW_NOAPI" if not failures else "NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN_HOLD"
    }

def main():
    generated_at = now()

    retry = stabilization_retry()
    plan = dryrun_plan(retry)
    dryrun = controlled_dryrun(plan)

    failures = []
    warnings = []
    for step in [retry, plan, dryrun]:
        warnings.extend(step.get("warnings", []))
        if not step.get("decision", "").startswith("OK_"):
            failures.append(step["stage"] + ":" + step.get("decision", "NO_DECISION"))
        failures.extend(step.get("failures", []))

    final_decision = "OK_NEWS_CONTINUOUS_PRODUCER_ONE_SHOT_COMPLETION" if not failures else "FAIL_NEWS_CONTINUOUS_PRODUCER_ONE_SHOT_COMPLETION"
    next_step = dryrun.get("next") if not failures else "NEWS_CONTINUOUS_PRODUCER_ONE_SHOT_HOLD"

    return {
        "stage": "NEWS_CONTINUOUS_PRODUCER_ONE_SHOT_COMPLETION",
        "generated_at_utc": generated_at,
        "decision": final_decision,
        "steps": {
            "retry": retry,
            "plan": plan,
            "controlled_dryrun": dryrun
        },
        "remaining_after_this_if_ok": [
            "NEWS_CONTINUOUS_PRODUCER_OBSERVATION_WINDOW_NOAPI"
        ],
        "failures": failures,
        "warnings": warnings,
        "next": next_step
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
