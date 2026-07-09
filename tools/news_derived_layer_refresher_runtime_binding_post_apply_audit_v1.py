
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, hashlib, sys

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_derived_layer_refresher_runtime_binding_apply_with_backup_v1.json"
TARGET = ROOT / "tools/news_radar_refresh_runner_v1.py"
HELPER = ROOT / "tools/news_derived_layer_refresher_v1.py"

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

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path and path.exists() else None

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {"cmd": cmd, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def counts_ro():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    try:
        return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}
    finally:
        con.close()

def db_preview():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    try:
        counts = {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}
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

        tail_candidates = 0
        if latest_derived:
            tail_candidates = con.execute("""
                SELECT COUNT(*)
                FROM news_raw_feed_events r
                WHERE COALESCE(r.published_at_utc, r.fetched_at_utc) > ?
                  AND NOT EXISTS (
                    SELECT 1 FROM news_token_match_events m WHERE m.news_uid = r.news_uid
                  )
            """, [latest_derived]).fetchone()[0]

        latest_bad_trade_flags = 0
        if latest_derived:
            latest_bad_trade_flags = con.execute("""
                SELECT COUNT(*)
                FROM news_token_match_events
                WHERE created_at_utc = ?
                  AND (write_allowed != 0 OR trade_signal != 0 OR paper_signal != 0)
            """, [latest_derived]).fetchone()[0]

        return {
            "counts": counts,
            "integrity": integrity,
            "latest_raw": latest_raw,
            "latest_derived": latest_derived,
            "latest_by_table": latest_by_table,
            "tail_candidates": tail_candidates,
            "latest_bad_trade_flags": latest_bad_trade_flags,
            "derived_counts_balanced": counts["news_token_match_events"] == counts["news_signal_events"] == counts["news_score_events_v1"]
        }
    finally:
        con.close()

def wrapper_contract(target_text, backup_rel):
    raw_call_pos = target_text.find("raw = subprocess.run")
    derived_call_pos = target_text.find("derived = subprocess.run")
    return {
        "contains_original_var": "ORIGINAL =" in target_text,
        "contains_helper_var": "HELPER =" in target_text and "news_derived_layer_refresher_v1.py" in target_text,
        "contains_db_var": "DB =" in target_text and "tokenoskobi_clean_v1.sqlite" in target_text,
        "contains_backup_reference": bool(backup_rel and backup_rel.split("/")[-1] in target_text),
        "contains_raw_call": raw_call_pos >= 0,
        "contains_raw_failure_gate": "if raw.returncode != 0:" in target_text,
        "contains_derived_call": derived_call_pos >= 0,
        "contains_stage_reference": "NEWS_SYSTEMD_TIMER_DERIVED_REFRESH" in target_text,
        "raw_call_before_derived_call": raw_call_pos >= 0 and derived_call_pos >= 0 and raw_call_pos < derived_call_pos,
        "contains_main_exit": "raise SystemExit(main())" in target_text
    }

def main():
    prior = load(PRIOR)
    apply = prior.get("apply", {})
    prior_sha = apply.get("sha256", {})
    backup_rel = apply.get("backup_runner")
    backup_path = ROOT / backup_rel if backup_rel else None

    failures = []
    warnings = []

    before = counts_ro()

    target_text = TARGET.read_text(encoding="utf-8", errors="ignore") if TARGET.exists() else ""
    target_sha = sha256(TARGET)
    helper_sha = sha256(HELPER)
    backup_sha = sha256(backup_path)

    contract = wrapper_contract(target_text, backup_rel)

    target_compile = run([sys.executable, "-m", "py_compile", str(TARGET)])
    helper_compile = run([sys.executable, "-m", "py_compile", str(HELPER)])
    backup_compile = run([sys.executable, "-m", "py_compile", str(backup_path)]) if backup_path and backup_path.exists() else {"rc": 99, "stdout": "", "stderr": "backup_missing"}

    service_cat = run(["systemctl", "cat", "tokenoskobi-news-radar-refresh.service"])
    timer_state = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    timer_enabled = run(["systemctl", "is-enabled", "tokenoskobi-news-radar-refresh.timer"])
    service_state = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    preview = db_preview()
    after = counts_ro()
    db_delta = {k: after[k] - before[k] for k in before}

    apply_db_after = apply.get("db_after", {})
    runtime_effect_observed = (
        preview["counts"].get("news_token_match_events", 0) >= int(apply_db_after.get("news_token_match_events", 0) or 0)
        and preview["counts"].get("news_signal_events", 0) >= int(apply_db_after.get("news_signal_events", 0) or 0)
        and preview["counts"].get("news_score_events_v1", 0) >= int(apply_db_after.get("news_score_events_v1", 0) or 0)
        and preview.get("derived_counts_balanced") is True
    )

    if prior.get("decision") != "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_WITH_BACKUP":
        failures.append("prior_apply_not_ok")
    if apply.get("decision") != "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_WITH_BACKUP_INTERNAL":
        failures.append("prior_internal_apply_not_ok")
    if not TARGET.exists():
        failures.append("target_runner_missing")
    if not HELPER.exists():
        failures.append("helper_missing")
    if not backup_path or not backup_path.exists():
        failures.append("backup_runner_missing")
    if target_sha != prior_sha.get("target_after"):
        failures.append("target_sha_mismatch_vs_apply")
    if helper_sha != prior_sha.get("helper"):
        failures.append("helper_sha_mismatch_vs_apply")
    if backup_sha != prior_sha.get("backup_runner"):
        failures.append("backup_sha_mismatch_vs_apply")
    for k, v in contract.items():
        if v is not True:
            failures.append("wrapper_contract_false:" + k)
    if target_compile.get("rc") != 0:
        failures.append("target_runner_compile_failed")
    if helper_compile.get("rc") != 0:
        failures.append("helper_compile_failed")
    if backup_compile.get("rc") != 0:
        failures.append("backup_runner_compile_failed")
    if "ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py" not in service_cat.get("stdout", ""):
        failures.append("systemd_execstart_not_target_runner")
    if timer_state.get("stdout") != "active":
        failures.append("timer_not_active")
    if preview.get("integrity") != "ok":
        failures.append("sqlite_integrity_not_ok")
    if preview.get("latest_bad_trade_flags", 0) != 0:
        failures.append("latest_bad_trade_flags_nonzero")
    if preview.get("derived_counts_balanced") is not True:
        failures.append("derived_counts_not_balanced")
    if not runtime_effect_observed:
        failures.append("runtime_effect_not_observed")

    if preview.get("tail_candidates", 0) != 0:
        warnings.append("tail_candidates_nonzero_after_runtime_binding")
    if any(v != 0 for v in db_delta.values()):
        warnings.append("db_changed_during_readonly_audit_external_runtime_possible")
    if timer_enabled.get("stdout") != "enabled":
        warnings.append("timer_not_enabled")

    tests = [
        {
            "test_id": "T01_PRIOR_APPLY_OK",
            "ok": prior.get("decision") == "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_WITH_BACKUP"
                  and apply.get("decision") == "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_WITH_BACKUP_INTERNAL"
                  and apply.get("fail_count") == 0
        },
        {
            "test_id": "T02_FILES_AND_SHA_LOCK_OK",
            "ok": TARGET.exists() and HELPER.exists() and backup_path and backup_path.exists()
                  and target_sha == prior_sha.get("target_after")
                  and helper_sha == prior_sha.get("helper")
                  and backup_sha == prior_sha.get("backup_runner"),
            "target_sha": target_sha,
            "helper_sha": helper_sha,
            "backup_sha": backup_sha
        },
        {
            "test_id": "T03_WRAPPER_CONTRACT_OK",
            "ok": all(contract.values()),
            "contract": contract
        },
        {
            "test_id": "T04_PY_COMPILE_OK",
            "ok": target_compile.get("rc") == 0 and helper_compile.get("rc") == 0 and backup_compile.get("rc") == 0
        },
        {
            "test_id": "T05_SYSTEMD_BOUNDARY_OK",
            "ok": "ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py" in service_cat.get("stdout", "")
                  and timer_state.get("stdout") == "active",
            "timer_state": timer_state.get("stdout"),
            "timer_enabled": timer_enabled.get("stdout"),
            "service_state": service_state.get("stdout")
        },
        {
            "test_id": "T06_DB_HEALTH_OK",
            "ok": preview.get("integrity") == "ok"
                  and preview.get("latest_bad_trade_flags", 0) == 0
                  and preview.get("derived_counts_balanced") is True,
            "preview": preview
        },
        {
            "test_id": "T07_RUNTIME_BINDING_EFFECT_OBSERVED",
            "ok": runtime_effect_observed,
            "apply_db_after": apply_db_after,
            "current_counts": preview.get("counts")
        },
        {
            "test_id": "T08_AUTHORITY_BOUNDARY_LOCKED",
            "ok": True,
            "api_call": False,
            "network_call": False,
            "db_write_by_audit": False,
            "service_change": False,
            "timer_change": False,
            "trade_authority": False
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_HISTORICAL_ACCESS_REAL_FETCH_PLAN_NOAPI" if not failures and preview.get("tail_candidates", 0) == 0 else "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_SMOKE_ONCE_WITH_BACKUP"

    return {
        "stage": "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_POST_APPLY_AUDIT_NOAPI",
        "repair_reason": "previous audit had brittle/missing outer helper; repaired audit validates wrapper, sha lock, systemd boundary, db health, and runtime effect",
        "generated_at_utc": now(),
        "decision": "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_POST_APPLY_AUDIT_NOAPI_INTERNAL" if not failures else "FAIL_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_POST_APPLY_AUDIT_NOAPI_INTERNAL",
        "target_runner": "tools/news_radar_refresh_runner_v1.py",
        "helper": "tools/news_derived_layer_refresher_v1.py",
        "backup_runner": backup_rel,
        "sha256": {
            "target": target_sha,
            "helper": helper_sha,
            "backup_runner": backup_sha,
            "prior": prior_sha
        },
        "wrapper_contract": contract,
        "systemd": {
            "timer_state": timer_state,
            "timer_enabled": timer_enabled,
            "service_state": service_state,
            "execstart_target_present": "ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py" in service_cat.get("stdout", "")
        },
        "db_preview": preview,
        "runtime_effect_observed": runtime_effect_observed,
        "db_before": before,
        "db_after": after,
        "db_delta_observed": db_delta,
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
