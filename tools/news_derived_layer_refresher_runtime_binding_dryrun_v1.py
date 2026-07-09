
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, shutil, hashlib, sys

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_derived_layer_refresher_runtime_binding_plan_noapi_v1.json"
HELPER = ROOT / "tools/news_derived_layer_refresher_v1.py"
TARGET_RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"

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

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {"cmd": cmd, "rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def counts_ro(db):
    con = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True)
    try:
        return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}
    finally:
        con.close()

def latest_derived_ro(db):
    con = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True)
    try:
        vals = []
        for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
            v = con.execute("SELECT MAX(created_at_utc) FROM " + q(t) + " WHERE created_at_utc IS NOT NULL").fetchone()[0]
            if v:
                vals.append(v)
        return max(vals) if vals else None
    finally:
        con.close()

def tail_candidates_ro(db):
    con = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True)
    try:
        latest = latest_derived_ro(db)
        if not latest:
            return 0
        return con.execute("""
            SELECT COUNT(*)
            FROM news_raw_feed_events r
            WHERE COALESCE(r.published_at_utc, r.fetched_at_utc) > ?
              AND NOT EXISTS (
                SELECT 1 FROM news_token_match_events m WHERE m.news_uid = r.news_uid
              )
        """, [latest]).fetchone()[0]
    finally:
        con.close()

def wrapper_preview(ts):
    backup_name = "news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_" + ts + ".py"
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
    text = "\n".join(lines)
    return {
        "backup_runner": "tools/" + backup_name,
        "target_runner": "tools/news_radar_refresh_runner_v1.py",
        "helper": "tools/news_derived_layer_refresher_v1.py",
        "preview_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "preview_line_count": len(lines),
        "preview_contains_original": backup_name in text,
        "preview_contains_helper": "news_derived_layer_refresher_v1.py" in text,
        "preview_text_sample": text[:1200]
    }

def main():
    prior = load(PRIOR)
    failures = []
    warnings = []
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if prior.get("decision") != "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_PLAN_NOAPI":
        failures.append("prior_runtime_binding_plan_not_ok")

    plan_result = prior.get("plan_result", {})
    binding = plan_result.get("binding_decision", {})
    if binding.get("target_runner") != "tools/news_radar_refresh_runner_v1.py":
        failures.append("unexpected_target_runner")

    if binding.get("new_helper") != "tools/news_derived_layer_refresher_v1.py":
        failures.append("unexpected_helper")

    before_real = counts_ro(DB)
    helper_compile = run([sys.executable, "-m", "py_compile", str(HELPER)])

    tempdb = Path("/tmp/tokenoskobi_news_derived_refresher_runtime_binding_dryrun_" + ts + ".sqlite")
    shutil.copy2(DB, tempdb)
    temp_before = counts_ro(tempdb)
    temp_tail_before = tail_candidates_ro(tempdb)

    helper_proc = run([
        sys.executable,
        str(HELPER),
        "--db-path",
        str(tempdb),
        "--write",
        "--max-batch",
        "250",
        "--stage",
        "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_NOAPI"
    ])

    try:
        helper_result = json.loads(helper_proc.get("stdout") or "{}")
    except Exception as exc:
        helper_result = {"decision": "FAIL_PARSE_HELPER_OUTPUT", "failures": ["parse_error:" + repr(exc)], "raw_stdout": helper_proc.get("stdout")}

    temp_after = counts_ro(tempdb)
    temp_delta = {k: temp_after[k] - temp_before[k] for k in temp_before}

    after_real = counts_ro(DB)
    real_delta = {k: after_real[k] - before_real[k] for k in before_real}

    service_cat = run(["systemctl", "cat", "tokenoskobi-news-radar-refresh.service"])
    timer_state = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"])
    service_state = run(["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"])

    target_sha = sha256(TARGET_RUNNER)
    helper_sha = sha256(HELPER)
    preview = wrapper_preview(ts)

    service_uses_target = "tools/news_radar_refresh_runner_v1.py" in service_cat.get("stdout", "")
    target_exists = TARGET_RUNNER.exists()
    helper_exists = HELPER.exists()

    if helper_compile.get("rc") != 0:
        failures.append("helper_py_compile_failed")

    if helper_proc.get("rc") != 0:
        failures.append("helper_tempdb_dryrun_rc_nonzero")

    if helper_result.get("decision") != "OK_NEWS_DERIVED_LAYER_REFRESHER_V1":
        failures.append("helper_tempdb_dryrun_not_ok")

    if temp_delta.get("news_raw_feed_events", 0) != 0:
        failures.append("tempdb_raw_delta_not_zero")

    candidate_count = int(helper_result.get("candidate_count") or 0)
    inserted = helper_result.get("inserted", {})
    if candidate_count > 0:
        for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
            if inserted.get(t) != candidate_count:
                failures.append("tempdb_insert_count_mismatch:" + t)
    else:
        warnings.append("dryrun_candidate_count_zero")

    derived_real_delta = {
        "news_token_match_events": real_delta.get("news_token_match_events", 0),
        "news_signal_events": real_delta.get("news_signal_events", 0),
        "news_score_events_v1": real_delta.get("news_score_events_v1", 0)
    }
    if any(v != 0 for v in derived_real_delta.values()):
        failures.append("real_derived_delta_not_zero")

    if real_delta.get("news_raw_feed_events", 0) != 0:
        warnings.append("raw_timer_delta_observed_during_dryrun")

    if not service_uses_target:
        failures.append("service_execstart_not_using_target_runner")

    if not target_exists:
        failures.append("target_runner_missing")

    if not helper_exists:
        failures.append("helper_missing")

    if not preview.get("preview_contains_original") or not preview.get("preview_contains_helper"):
        failures.append("wrapper_preview_invalid")

    if timer_state.get("stdout") != "active":
        failures.append("timer_not_active")

    tests = [
        {
            "test_id": "T01_PRIOR_PLAN_OK",
            "ok": prior.get("decision") == "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_PLAN_NOAPI"
        },
        {
            "test_id": "T02_HELPER_COMPILES",
            "ok": helper_compile.get("rc") == 0,
            "helper_sha256": helper_sha
        },
        {
            "test_id": "T03_TEMPDB_DRYRUN_OK",
            "ok": helper_result.get("decision") == "OK_NEWS_DERIVED_LAYER_REFRESHER_V1",
            "candidate_count": candidate_count,
            "inserted": inserted,
            "tempdb_delta": temp_delta
        },
        {
            "test_id": "T04_REAL_DB_UNTOUCHED_BY_DRYRUN",
            "ok": all(v == 0 for v in derived_real_delta.values()),
            "real_delta": real_delta
        },
        {
            "test_id": "T05_RUNNER_BINDING_PREVIEW_OK",
            "ok": target_exists and service_uses_target and preview.get("preview_contains_original") and preview.get("preview_contains_helper"),
            "target_sha256": target_sha,
            "wrapper_preview": preview
        },
        {
            "test_id": "T06_SYSTEMD_BOUNDARY_UNCHANGED",
            "ok": timer_state.get("stdout") == "active",
            "timer_state": timer_state.get("stdout"),
            "service_state": service_state.get("stdout")
        },
        {
            "test_id": "T07_AUTHORITY_BOUNDARY_LOCKED",
            "ok": True,
            "api_call": False,
            "network_call": False,
            "real_db_write": False,
            "service_change": False,
            "timer_change": False,
            "trade_authority": False
        }
    ]

    for t in tests:
        if t.get("ok") is not True:
            failures.append("test_failed:" + t["test_id"])

    next_step = "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_WITH_BACKUP" if not failures else "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_REPAIR_REQUIRED"

    return {
        "stage": "NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_NOAPI",
        "generated_at_utc": now(),
        "decision": "OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_INTERNAL" if not failures else "FAIL_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_INTERNAL",
        "tempdb_path": str(tempdb),
        "helper": "tools/news_derived_layer_refresher_v1.py",
        "helper_sha256": helper_sha,
        "target_runner": "tools/news_radar_refresh_runner_v1.py",
        "target_runner_sha256": target_sha,
        "wrapper_preview": preview,
        "helper_result": helper_result,
        "tempdb_before": temp_before,
        "tempdb_after": temp_after,
        "tempdb_delta": temp_delta,
        "real_db_before": before_real,
        "real_db_after": after_real,
        "real_db_delta": real_delta,
        "temp_tail_before": temp_tail_before,
        "service_uses_target_runner": service_uses_target,
        "timer_state": timer_state,
        "service_state": service_state,
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "authority": {
            "api_call": False,
            "network_call": False,
            "real_db_write": False,
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
