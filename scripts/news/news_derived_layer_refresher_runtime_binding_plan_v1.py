
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, re

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_producer_staleness_post_apply_freshness_audit_noapi_v1.json"

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
    return {
        "cmd": cmd,
        "rc": p.returncode,
        "stdout": p.stdout.strip(),
        "stderr": p.stderr.strip()
    }

def counts_ro():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    try:
        return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}
    finally:
        con.close()

def db_preview():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        counts = {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}

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

        tail_candidates = con.execute("""
            SELECT COUNT(*)
            FROM news_raw_feed_events r
            WHERE COALESCE(r.published_at_utc, r.fetched_at_utc) > ?
              AND NOT EXISTS (
                SELECT 1 FROM news_token_match_events m
                WHERE m.news_uid = r.news_uid
              )
        """, [latest_derived]).fetchone()[0] if latest_derived else 0

        recent_raw_samples = [
            dict(r) for r in con.execute("""
                SELECT news_uid, source_uid, published_at_utc, fetched_at_utc, title
                FROM news_raw_feed_events
                ORDER BY COALESCE(published_at_utc, fetched_at_utc) DESC
                LIMIT 10
            """).fetchall()
        ]

        return {
            "counts": counts,
            "latest_raw": latest_raw,
            "latest_derived": latest_derived,
            "latest_by_table": latest_by_table,
            "tail_candidates": tail_candidates,
            "recent_raw_samples": recent_raw_samples
        }
    finally:
        con.close()

def unit_info():
    service_cat = run(["systemctl", "cat", "tokenoskobi-news-radar-refresh.service"])
    timer_cat = run(["systemctl", "cat", "tokenoskobi-news-radar-refresh.timer"])
    service_active = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])
    timer_active = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    timer_enabled = run(["systemctl", "is-enabled", "tokenoskobi-news-radar-refresh.timer"])

    execstarts = []
    for line in service_cat.get("stdout", "").splitlines():
        s = line.strip()
        if s.startswith("ExecStart="):
            execstarts.append(s.split("=", 1)[1])

    return {
        "service_cat_rc": service_cat.get("rc"),
        "timer_cat_rc": timer_cat.get("rc"),
        "service_active": service_active.get("stdout"),
        "timer_active": timer_active.get("stdout"),
        "timer_enabled": timer_enabled.get("stdout"),
        "execstarts": execstarts,
        "service_unit_text_sample": service_cat.get("stdout", "")[-4000:],
        "timer_unit_text_sample": timer_cat.get("stdout", "")[-2000:]
    }

def scan_candidate_files():
    patterns = [
        "tools/*news*refresh*.py",
        "tools/*news*radar*.py",
        "tools/*news*token*match*.py",
        "tools/*news*signal*.py",
        "tools/*news*score*.py",
        "tools/*derived*.py",
        "config/*news*.json"
    ]
    paths = []
    seen = set()
    for pat in patterns:
        for p in ROOT.glob(pat):
            if p.is_file() and str(p) not in seen:
                seen.add(str(p))
                paths.append(p)

    out = []
    needle_tables = [
        "news_raw_feed_events",
        "news_token_match_events",
        "news_signal_events",
        "news_score_events_v1"
    ]

    for p in sorted(paths):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            out.append({"path": str(p.relative_to(ROOT)), "read_error": repr(exc)})
            continue

        out.append({
            "path": str(p.relative_to(ROOT)),
            "size": p.stat().st_size,
            "contains_sqlite3": "sqlite3" in txt,
            "contains_systemd": "systemctl" in txt or "ExecStart" in txt,
            "contains_tables": {t: (t in txt) for t in needle_tables},
            "contains_refresh_runner": "news_radar_refresh_runner" in txt,
            "contains_original_runner": "ORIGINAL_RUNNER" in txt,
            "contains_write_flags": ("write_allowed" in txt or "trade_signal" in txt or "paper_signal" in txt),
            "contains_derived_refresh_terms": (
                "news_token_match_events" in txt and
                "news_signal_events" in txt and
                "news_score_events_v1" in txt
            )
        })
    return out

def decide_binding_mode(units, files):
    exec_text = "\n".join(units.get("execstarts", []))
    file_paths = [f.get("path", "") for f in files]

    wrapper_exists = "tools/news_radar_refresh_runner_v1.py" in file_paths
    exec_uses_wrapper = "news_radar_refresh_runner_v1.py" in exec_text

    if exec_uses_wrapper and wrapper_exists:
        return {
            "mode": "PATCH_EXISTING_RUNNER_TO_CALL_DERIVED_REFRESHER_AFTER_RAW_REFRESH",
            "target_runner": "tools/news_radar_refresh_runner_v1.py",
            "new_helper": "tools/news_derived_layer_refresher_v1.py",
            "systemd_unit_change_required": False,
            "daemon_reload_required": False
        }

    if wrapper_exists:
        return {
            "mode": "PATCH_SERVICE_TO_USE_EXISTING_RUNNER_PLUS_DERIVED_REFRESHER",
            "target_runner": "tools/news_radar_refresh_runner_v1.py",
            "new_helper": "tools/news_derived_layer_refresher_v1.py",
            "systemd_unit_change_required": True,
            "daemon_reload_required": True
        }

    return {
        "mode": "CREATE_HELPER_AND_BIND_MANUALLY_AFTER_SERVICE_EXECSTART_REVIEW",
        "target_runner": None,
        "new_helper": "tools/news_derived_layer_refresher_v1.py",
        "systemd_unit_change_required": True,
        "daemon_reload_required": True
    }

def main():
    prior = load(PRIOR)
    failures = []
    warnings = []

    before = counts_ro()
    units = unit_info()
    preview = db_preview()
    files = scan_candidate_files()
    binding = decide_binding_mode(units, files)
    after = counts_ro()
    db_delta = {k: after[k] - before[k] for k in before}

    if prior.get("decision") != "OK_NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI":
        failures.append("prior_post_apply_freshness_audit_not_ok")

    if prior.get("audit", {}).get("decision") != "OK_NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI_INTERNAL":
        failures.append("prior_internal_post_apply_freshness_audit_not_ok")

    if units.get("timer_active") != "active":
        failures.append("news_timer_not_active")

    if units.get("timer_enabled") not in ("enabled", "static", "indirect"):
        warnings.append("news_timer_enabled_state_not_enabled_static_or_indirect")

    if units.get("service_cat_rc") != 0:
        failures.append("service_unit_not_readable")

    if units.get("timer_cat_rc") != 0:
        failures.append("timer_unit_not_readable")

    if not files:
        failures.append("no_candidate_news_files_found")

    if preview.get("counts", {}).get("news_raw_feed_events", 0) <= 0:
        failures.append("raw_feed_empty")

    if preview.get("counts", {}).get("news_token_match_events", 0) <= 0:
        failures.append("token_match_empty_after_apply")

    if preview.get("counts", {}).get("news_signal_events", 0) <= 0:
        failures.append("signal_empty_after_apply")

    if preview.get("counts", {}).get("news_score_events_v1", 0) <= 0:
        failures.append("score_empty_after_apply")

    derived_delta = {
        "news_token_match_events": db_delta.get("news_token_match_events", 0),
        "news_signal_events": db_delta.get("news_signal_events", 0),
        "news_score_events_v1": db_delta.get("news_score_events_v1", 0)
    }

    if any(v != 0 for v in derived_delta.values()):
        failures.append("derived_db_delta_not_zero_during_plan")

    if db_delta.get("news_raw_feed_events", 0) != 0:
        warnings.append("raw_timer_delta_observed_during_plan_readonly_window")

    if binding.get("mode") == "CREATE_HELPER_AND_BIND_MANUALLY_AFTER_SERVICE_EXECSTART_REVIEW":
        warnings.append("binding_mode_requires_service_execstart_review")

    proposed_plan = {
        "plan_version": "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_PLAN_V1",
        "generated_at_utc": now(),
        "purpose": "Bind NEWS raw producer runtime to derived token_match, signal, and score refresh so stale derived layers do not recur.",
        "prior_required_artifact": "data/control/news_producer_staleness_post_apply_freshness_audit_noapi_v1.json",
        "prior_required_decision": "OK_NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI",
        "current_root_cause_closed": "RAW_FEED_IS_CURRENT_BUT_DERIVED_LAYERS_WERE_STALE",
        "new_prevention_goal": "Every timer-triggered raw refresh must be followed by deterministic derived-layer refresh.",
        "runtime_binding_scope_this_step": {
            "plan_only": True,
            "real_db_write_now": False,
            "service_change_now": False,
            "timer_change_now": False,
            "nginx_change_now": False,
            "api_network_enable_now": False,
            "trade_authority_now": False
        },
        "binding_decision": binding,
        "derived_refresher_contract": {
            "new_helper": "tools/news_derived_layer_refresher_v1.py",
            "input_table": "news_raw_feed_events",
            "output_tables": [
                "news_token_match_events",
                "news_signal_events",
                "news_score_events_v1"
            ],
            "selection_rule": "raw rows newer than latest derived timestamp and not already present in news_token_match_events",
            "transaction_required": True,
            "idempotent_insert_required": True,
            "write_allowed": 0,
            "trade_signal": 0,
            "paper_signal": 0,
            "api_call": False,
            "network_call": False,
            "schema_change": False,
            "index_creation": False
        },
        "runner_binding_contract": {
            "preferred_order": [
                "run_existing_raw_refresh_exactly_as_before",
                "run_news_derived_layer_refresher_v1",
                "write local artifact/runtime event",
                "exit nonzero only if raw refresh or derived refresh hard fails"
            ],
            "preserve_existing_raw_runner": True,
            "backup_target_runner_before_patch": True,
            "dryrun_first": True,
            "post_apply_freshness_audit_required": True
        },
        "safety_gates_for_next": {
            "next_step": "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_NOAPI",
            "must_hold": [
                "do_not_patch_service_or_timer_in_dryrun",
                "helper_py_compile_ok",
                "helper_dryrun_tempdb_ok",
                "runner_binding_preview_ok",
                "real_db_delta_zero_in_dryrun",
                "api_network_trade_all_false",
                "then_request_apply"
            ]
        },
        "current_runtime_preview": {
            "db_preview": preview,
            "unit_info": units,
            "candidate_file_count": len(files)
        }
    }

    tests = [
        {
            "test_id": "T01_PRIOR_POST_APPLY_FRESHNESS_AUDIT_OK",
            "ok": prior.get("decision") == "OK_NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI"
                  and prior.get("audit", {}).get("decision") == "OK_NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI_INTERNAL"
        },
        {
            "test_id": "T02_NEWS_SYSTEMD_TIMER_DISCOVERED",
            "ok": units.get("service_cat_rc") == 0 and units.get("timer_cat_rc") == 0 and units.get("timer_active") == "active",
            "service_active": units.get("service_active"),
            "timer_active": units.get("timer_active"),
            "timer_enabled": units.get("timer_enabled"),
            "execstarts": units.get("execstarts")
        },
        {
            "test_id": "T03_CURRENT_DB_COUNTS_VALID",
            "ok": preview.get("counts", {}).get("news_raw_feed_events", 0) > 0
                  and preview.get("counts", {}).get("news_token_match_events", 0) > 0
                  and preview.get("counts", {}).get("news_signal_events", 0) > 0
                  and preview.get("counts", {}).get("news_score_events_v1", 0) > 0,
            "counts": preview.get("counts")
        },
        {
            "test_id": "T04_BINDING_MODE_SELECTED",
            "ok": binding.get("mode") in [
                "PATCH_EXISTING_RUNNER_TO_CALL_DERIVED_REFRESHER_AFTER_RAW_REFRESH",
                "PATCH_SERVICE_TO_USE_EXISTING_RUNNER_PLUS_DERIVED_REFRESHER",
                "CREATE_HELPER_AND_BIND_MANUALLY_AFTER_SERVICE_EXECSTART_REVIEW"
            ],
            "binding": binding
        },
        {
            "test_id": "T05_CANDIDATE_FILES_SCANNED",
            "ok": len(files) > 0,
            "candidate_file_count": len(files)
        },
        {
            "test_id": "T06_PLAN_STEP_READONLY",
            "ok": all(v == 0 for v in derived_delta.values()),
            "db_delta": db_delta
        },
        {
            "test_id": "T07_AUTHORITY_BOUNDARY_LOCKED",
            "ok": proposed_plan["runtime_binding_scope_this_step"]["real_db_write_now"] is False
                  and proposed_plan["runtime_binding_scope_this_step"]["service_change_now"] is False
                  and proposed_plan["runtime_binding_scope_this_step"]["timer_change_now"] is False
                  and proposed_plan["runtime_binding_scope_this_step"]["trade_authority_now"] is False
        },
        {
            "test_id": "T08_READY_FOR_DRYRUN",
            "ok": True,
            "next": "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_NOAPI"
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    return {
        "stage": "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_PLAN_NOAPI",
        "generated_at_utc": now(),
        "decision": "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_PLAN_INTERNAL" if not failures else "FAIL_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_PLAN_INTERNAL",
        "proposed_plan": proposed_plan,
        "db_before": before,
        "db_after": after,
        "db_delta": db_delta,
        "unit_info": units,
        "binding_decision": binding,
        "candidate_files": files,
        "current_db_preview": preview,
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
        "next": "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_NOAPI" if not failures else "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_PLAN_REPAIR_REQUIRED"
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
