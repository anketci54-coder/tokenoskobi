
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, hashlib, os, re, sys, stat

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_derived_layer_refresher_runtime_binding_dryrun_noapi_v1.json"

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

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {"cmd": cmd, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def counts_ro():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    try:
        return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}
    finally:
        con.close()

def make_wrapper(backup_name):
    lines = [
        "#!/usr/bin/env python3",
        "from pathlib import Path",
        "import subprocess",
        "import sys",
        "",
        "ROOT = Path('/root/tokenoskobi_clean_v1')",
        "ORIGINAL = ROOT / 'tools' / '" + backup_name + "'",
        "HELPER = ROOT / 'tools' / 'news_derived_layer_refresher_v1.py'",
        "DB = ROOT / 'data' / 'tokenoskobi_clean_v1.sqlite'",
        "",
        "def main():",
        "    raw = subprocess.run([sys.executable, str(ORIGINAL)])",
        "    if raw.returncode != 0:",
        "        return raw.returncode",
        "    derived = subprocess.run([sys.executable, str(HELPER), '--db-path', str(DB), '--write', '--stage', 'NEWS_SYSTEMD_TIMER_DERIVED_REFRESH'])",
        "    return derived.returncode",
        "",
        "if __name__ == '__main__':",
        "    raise SystemExit(main())",
        ""
    ]
    return "\n".join(lines)

def main():
    prior = load(PRIOR)
    failures = []
    warnings = []
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    before = counts_ro()

    if prior.get("decision") != "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_NOAPI":
        failures.append("prior_dryrun_not_ok")

    if prior.get("dryrun", {}).get("decision") != "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_INTERNAL":
        failures.append("prior_internal_dryrun_not_ok")

    if not TARGET.exists():
        failures.append("target_runner_missing")

    if not HELPER.exists():
        failures.append("helper_missing")

    helper_compile = run([sys.executable, "-m", "py_compile", str(HELPER)])
    if helper_compile.get("rc") != 0:
        failures.append("helper_py_compile_failed")

    service_cat_before = run(["systemctl", "cat", "tokenoskobi-news-radar-refresh.service"])
    timer_before = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_before = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    if "tools/news_radar_refresh_runner_v1.py" not in service_cat_before.get("stdout", ""):
        failures.append("service_not_using_target_runner")

    if timer_before.get("stdout") != "active":
        failures.append("timer_not_active_before")

    apply_action = None
    backup_path = None
    backup_name = None
    target_sha_before = sha256(TARGET)
    helper_sha = sha256(HELPER)
    wrapper_sha = None
    target_sha_after = None
    wrapper_compile = {"rc": 1, "stdout": "", "stderr": "not_run"}

    target_text = TARGET.read_text(encoding="utf-8", errors="ignore") if TARGET.exists() else ""
    already_bound = "news_derived_layer_refresher_v1.py" in target_text and "NEWS_SYSTEMD_TIMER_DERIVED_REFRESH" in target_text

    if not failures:
        if already_bound:
            apply_action = "ALREADY_BOUND_VALIDATE_ONLY"
            m = re.search(r"news_radar_refresh_runner_v1\.PRE_DERIVED_BINDING_[0-9T]+Z\.py", target_text)
            backup_name = m.group(0) if m else None
            backup_path = ROOT / "tools" / backup_name if backup_name else None
            if not backup_path or not backup_path.exists():
                failures.append("already_bound_backup_runner_missing")
            wrapper_sha = sha256(TARGET)
            wrapper_compile = run([sys.executable, "-m", "py_compile", str(TARGET)])
        else:
            apply_action = "APPLIED_WRAPPER_WITH_BACKUP"
            backup_name = "news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_" + ts + ".py"
            backup_path = ROOT / "tools" / backup_name

            backup_path.write_text(target_text, encoding="utf-8")
            os.chmod(backup_path, TARGET.stat().st_mode)

            wrapper_text = make_wrapper(backup_name)
            wrapper_sha = sha256_bytes(wrapper_text.encode("utf-8"))

            tmp = ROOT / "tools/news_radar_refresh_runner_v1.py.tmp_derived_binding"
            tmp.write_text(wrapper_text, encoding="utf-8")
            os.chmod(tmp, TARGET.stat().st_mode)

            wrapper_compile = run([sys.executable, "-m", "py_compile", str(tmp)])
            backup_compile = run([sys.executable, "-m", "py_compile", str(backup_path)])

            if wrapper_compile.get("rc") != 0:
                failures.append("wrapper_py_compile_failed")

            if backup_compile.get("rc") != 0:
                failures.append("backup_runner_py_compile_failed")

            if not failures:
                os.replace(tmp, TARGET)
            elif tmp.exists():
                tmp.unlink()

    target_sha_after = sha256(TARGET)

    service_cat_after = run(["systemctl", "cat", "tokenoskobi-news-radar-refresh.service"])
    timer_after = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_after = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    after = counts_ro()
    db_delta = {k: after[k] - before[k] for k in before}

    derived_delta = {
        "news_token_match_events": db_delta.get("news_token_match_events", 0),
        "news_signal_events": db_delta.get("news_signal_events", 0),
        "news_score_events_v1": db_delta.get("news_score_events_v1", 0)
    }

    if any(v != 0 for v in derived_delta.values()):
        failures.append("derived_db_delta_not_zero_during_apply")

    if db_delta.get("news_raw_feed_events", 0) != 0:
        warnings.append("raw_timer_delta_observed_during_apply_window")

    target_after_text = TARGET.read_text(encoding="utf-8", errors="ignore") if TARGET.exists() else ""
    if "news_derived_layer_refresher_v1.py" not in target_after_text:
        failures.append("target_runner_missing_helper_call_after_apply")

    if backup_name and backup_name not in target_after_text:
        failures.append("target_runner_missing_backup_reference_after_apply")

    if service_cat_before.get("stdout") != service_cat_after.get("stdout"):
        failures.append("systemd_service_unit_changed")

    if timer_before.get("stdout") != timer_after.get("stdout"):
        failures.append("timer_state_changed")

    if service_before.get("stdout") != service_after.get("stdout"):
        warnings.append("service_state_changed_during_apply_window")

    if target_sha_after == target_sha_before and apply_action != "ALREADY_BOUND_VALIDATE_ONLY":
        failures.append("target_runner_sha_not_changed")

    tests = [
        {
            "test_id": "T01_PRIOR_DRYRUN_OK",
            "ok": prior.get("decision") == "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_NOAPI"
                  and prior.get("dryrun", {}).get("decision") == "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_INTERNAL"
        },
        {
            "test_id": "T02_HELPER_COMPILES",
            "ok": helper_compile.get("rc") == 0,
            "helper_sha256": helper_sha
        },
        {
            "test_id": "T03_BACKUP_RUNNER_EXISTS",
            "ok": backup_path is not None and backup_path.exists(),
            "backup_runner": str(backup_path.relative_to(ROOT)) if backup_path else None
        },
        {
            "test_id": "T04_TARGET_WRAPPER_BOUND",
            "ok": "news_derived_layer_refresher_v1.py" in target_after_text and backup_name and backup_name in target_after_text,
            "target_runner_sha256_before": target_sha_before,
            "target_runner_sha256_after": target_sha_after,
            "wrapper_sha256_expected": wrapper_sha
        },
        {
            "test_id": "T05_WRAPPER_COMPILES",
            "ok": wrapper_compile.get("rc") == 0,
            "wrapper_compile": wrapper_compile
        },
        {
            "test_id": "T06_SYSTEMD_UNIT_UNCHANGED",
            "ok": service_cat_before.get("stdout") == service_cat_after.get("stdout"),
            "timer_before": timer_before.get("stdout"),
            "timer_after": timer_after.get("stdout"),
            "service_before": service_before.get("stdout"),
            "service_after": service_after.get("stdout")
        },
        {
            "test_id": "T07_REAL_DB_UNTOUCHED_BY_BINDING_APPLY",
            "ok": all(v == 0 for v in derived_delta.values()),
            "db_delta": db_delta
        },
        {
            "test_id": "T08_READY_FOR_POST_APPLY_AUDIT",
            "ok": True,
            "next": "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_POST_APPLY_AUDIT_NOAPI"
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_POST_APPLY_AUDIT_NOAPI" if not failures else "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_REPAIR_OR_ROLLBACK_REQUIRED"

    return {
        "stage": "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_WITH_BACKUP",
        "generated_at_utc": now(),
        "decision": "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_WITH_BACKUP_INTERNAL" if not failures else "FAIL_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_WITH_BACKUP_INTERNAL",
        "apply_action": apply_action,
        "target_runner": "tools/news_radar_refresh_runner_v1.py",
        "backup_runner": str(backup_path.relative_to(ROOT)) if backup_path else None,
        "helper": "tools/news_derived_layer_refresher_v1.py",
        "sha256": {
            "target_before": target_sha_before,
            "target_after": target_sha_after,
            "helper": helper_sha,
            "wrapper_expected": wrapper_sha,
            "backup_runner": sha256(backup_path) if backup_path else None
        },
        "service_unit_changed": service_cat_before.get("stdout") != service_cat_after.get("stdout"),
        "timer_before": timer_before,
        "timer_after": timer_after,
        "service_before": service_before,
        "service_after": service_after,
        "db_before": before,
        "db_after": after,
        "db_delta": db_delta,
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
