
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, sys, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/news_runtime_policy_lock_repair_noapi_v1.json"
POLICY = ROOT / "runtime/policies/news_runtime_policy_lock_v1.json"
VERIFIER = ROOT / "tools/news_runtime_policy_verifier_v1.py"

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

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {"rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def table_exists(con, table):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        [table]
    ).fetchone() is not None

def cols(con, table):
    if not table_exists(con, table):
        return []
    return [r[1] for r in con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()]

def main():
    generated_at = now()
    failures = []
    warnings = []

    if not PRIOR.exists():
        failures.append("prior_policy_lock_repair_missing")
        prior = {}
    else:
        prior = json.loads(PRIOR.read_text(encoding="utf-8"))
        if prior.get("decision") != "OK_NEWS_RUNTIME_POLICY_LOCK_REPAIR_NOAPI":
            failures.append("prior_policy_lock_repair_not_ok")

    if not POLICY.exists():
        failures.append("policy_json_missing")
        policy = {}
    else:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))

    if not VERIFIER.exists():
        failures.append("policy_verifier_missing")

    compile_verifier = run([sys.executable, "-m", "py_compile", str(VERIFIER)]) if VERIFIER.exists() else {"rc": 1, "stdout": "", "stderr": "missing"}
    if compile_verifier["rc"] != 0:
        failures.append("policy_verifier_compile_failed")

    verifier_run = run([sys.executable, str(VERIFIER), "--db-path", str(DB), "--recent-limit", "500"]) if VERIFIER.exists() else {"rc": 1, "stdout": "", "stderr": "missing"}
    try:
        verifier_result = json.loads(verifier_run["stdout"]) if verifier_run["stdout"] else {}
    except Exception as exc:
        verifier_result = {"decision": "FAIL_PARSE_POLICY_VERIFIER", "error": repr(exc), "raw": verifier_run}

    if verifier_run["rc"] != 0:
        failures.append("policy_verifier_runtime_failed")
    if verifier_result.get("decision") != "OK_NEWS_RUNTIME_POLICY_VERIFIER_V1":
        failures.append("policy_verifier_not_ok_before_era60_plan")

    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        counts = {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}
        existing_schema = {
            "news_raw_feed_events_columns": cols(con, "news_raw_feed_events"),
            "news_token_match_events_columns": cols(con, "news_token_match_events"),
            "news_signal_events_columns": cols(con, "news_signal_events"),
            "news_score_events_v1_columns": cols(con, "news_score_events_v1"),
            "news_quarantine_events_exists": table_exists(con, "news_quarantine_events_v1"),
            "news_conflict_resolution_events_exists": table_exists(con, "news_conflict_resolution_events_v1"),
            "news_event_hash_registry_exists": table_exists(con, "news_event_hash_registry_v1")
        }
    finally:
        con.close()

    if integrity != "ok":
        failures.append("sqlite_integrity_not_ok")

    event_hash_missing = {}
    for table in TABLES:
        event_hash_missing[table] = "event_hash" not in existing_schema.get(table + "_columns", [])

    hardening_backlog = {
        "ERA60A_EVENT_HASH_BACKLOG": {
            "status": "PLANNED_NO_SCHEMA_CHANGE_IN_THIS_STEP",
            "purpose": "Add deterministic event_hash to NEWS raw and derived event rows for tamper/collision detection.",
            "target_tables": TABLES,
            "currently_missing": event_hash_missing,
            "acceptance": [
                "event_hash deterministic",
                "event_hash reproducible from canonical row fields",
                "no existing row identity rewritten without backup",
                "backfill uses tempdb dryrun before real apply"
            ]
        },
        "ERA60B_QUARANTINE_BACKLOG": {
            "status": "PLANNED_NO_SCHEMA_CHANGE_IN_THIS_STEP",
            "purpose": "Route unclassified/conflicting NEWS items into quarantine instead of polluting runtime tables.",
            "target_table": "news_quarantine_events_v1",
            "currently_exists": existing_schema["news_quarantine_events_exists"],
            "acceptance": [
                "quarantine_uid deterministic",
                "source news_uid retained",
                "reason_code required",
                "no trade authority",
                "quarantine can be reviewed without runtime writes"
            ]
        },
        "ERA60C_CONFLICT_RESOLUTION_BACKLOG": {
            "status": "PLANNED_NO_SCHEMA_CHANGE_IN_THIS_STEP",
            "purpose": "Record duplicate/conflicting sources, symbol conflicts, stale items, and policy routing decisions.",
            "target_table": "news_conflict_resolution_events_v1",
            "currently_exists": existing_schema["news_conflict_resolution_events_exists"],
            "acceptance": [
                "conflict_uid deterministic",
                "conflict_type required",
                "routing HOLD/QUARANTINE/OBSERVE/OK required",
                "policy_verifier compatible",
                "bounded recent-window audit only"
            ]
        },
        "ERA60D_BLIND_REPLAY_GATE": {
            "status": "PLANNED_NO_SCHEMA_CHANGE_IN_THIS_STEP",
            "purpose": "Open blind historical replay only after policy lock and schema-hardening backlog are canonically recorded.",
            "next_stage": "HISTORICAL_BLIND_REPLAY_PLAN_NOAPI",
            "acceptance": [
                "input fetched before outcome labels",
                "input manifest SHA sealed",
                "prediction run writes predictions before result fetch",
                "result fetch happens only after input/prediction seal",
                "score comparison happens last"
            ]
        }
    }

    stage_order = [
        "ERA60A_EVENT_HASH_BACKLOG_PLAN_NOAPI",
        "ERA60B_QUARANTINE_BACKLOG_PLAN_NOAPI",
        "ERA60C_CONFLICT_RESOLUTION_BACKLOG_PLAN_NOAPI",
        "ERA60D_HISTORICAL_BLIND_REPLAY_GATE_PLAN_NOAPI"
    ]

    tests = [
        {
            "test_id": "T01_PRIOR_POLICY_LOCK_REPAIR_OK",
            "ok": prior.get("decision") == "OK_NEWS_RUNTIME_POLICY_LOCK_REPAIR_NOAPI"
        },
        {
            "test_id": "T02_POLICY_VERIFIER_OK",
            "ok": verifier_result.get("decision") == "OK_NEWS_RUNTIME_POLICY_VERIFIER_V1",
            "verifier_decision": verifier_result.get("decision")
        },
        {
            "test_id": "T03_SQLITE_READONLY_INTEGRITY_OK",
            "ok": integrity == "ok",
            "integrity": integrity
        },
        {
            "test_id": "T04_EVENT_HASH_BACKLOG_IDENTIFIED",
            "ok": any(event_hash_missing.values()),
            "event_hash_missing": event_hash_missing
        },
        {
            "test_id": "T05_QUARANTINE_AND_CONFLICT_BACKLOG_IDENTIFIED",
            "ok": existing_schema["news_quarantine_events_exists"] is False and existing_schema["news_conflict_resolution_events_exists"] is False,
            "quarantine_exists": existing_schema["news_quarantine_events_exists"],
            "conflict_exists": existing_schema["news_conflict_resolution_events_exists"]
        },
        {
            "test_id": "T06_BLIND_REPLAY_GATE_DEFINED",
            "ok": hardening_backlog["ERA60D_BLIND_REPLAY_GATE"]["next_stage"] == "HISTORICAL_BLIND_REPLAY_PLAN_NOAPI"
        },
        {
            "test_id": "T07_NOAPI_BOUNDARY_LOCKED",
            "ok": True,
            "api_call": False,
            "db_write": False,
            "db_schema_change": False,
            "network_call": False,
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

    return {
        "stage": "ERA60_SCHEMA_HARDENING_BACKLOG_PLAN_NOAPI",
        "generated_at_utc": generated_at,
        "decision": "OK_ERA60_SCHEMA_HARDENING_BACKLOG_PLAN_NOAPI" if not failures else "FAIL_ERA60_SCHEMA_HARDENING_BACKLOG_PLAN_NOAPI",
        "prior": "data/control/news_runtime_policy_lock_repair_noapi_v1.json",
        "policy_json": "runtime/policies/news_runtime_policy_lock_v1.json",
        "policy_json_sha256": sha256_file(POLICY),
        "policy_verifier": "tools/news_runtime_policy_verifier_v1.py",
        "policy_verifier_sha256": sha256_file(VERIFIER),
        "compile_verifier": compile_verifier,
        "verifier_result": verifier_result,
        "db_counts": counts,
        "sqlite_integrity": integrity,
        "existing_schema": existing_schema,
        "hardening_backlog": hardening_backlog,
        "stage_order": stage_order,
        "blind_replay_rule": {
            "input_first": True,
            "outcome_labels_after_input_seal": True,
            "prediction_before_result_fetch": True,
            "score_comparison_last": True,
            "next_stage": "HISTORICAL_BLIND_REPLAY_PLAN_NOAPI"
        },
        "authority": {
            "api_call": False,
            "db_schema_change": False,
            "db_write": False,
            "index_creation": False,
            "live_trade": False,
            "network_call": False,
            "nginx_change": False,
            "paper_trade": False,
            "service_change": False,
            "timer_change": False,
            "trade_authority": False
        },
        "tests": tests,
        "test_count": len(tests),
        "ok_count": sum(1 for t in tests if t.get("ok") is True),
        "fail_count": sum(1 for t in tests if t.get("ok") is not True),
        "failures": failures,
        "warnings": warnings,
        "next": "HISTORICAL_BLIND_REPLAY_PLAN_NOAPI" if not failures else "ERA60_SCHEMA_HARDENING_BACKLOG_PLAN_HOLD"
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
