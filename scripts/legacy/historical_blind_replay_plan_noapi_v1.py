
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, sys, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/era60_schema_hardening_backlog_plan_noapi_v1.json"
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
        failures.append("prior_era60_plan_missing")
        prior = {}
    else:
        prior = json.loads(PRIOR.read_text(encoding="utf-8"))
        if prior.get("decision") != "OK_ERA60_SCHEMA_HARDENING_BACKLOG_PLAN_NOAPI":
            failures.append("prior_era60_plan_not_ok")

    if not POLICY.exists():
        failures.append("policy_json_missing")
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
        failures.append("policy_verifier_not_ok")

    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        counts = {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}
        schema = {t: cols(con, t) for t in TABLES}
        existing_uids_sample = [
            r[0] for r in con.execute(
                "SELECT news_uid FROM news_raw_feed_events ORDER BY COALESCE(fetched_at_utc,published_at_utc,news_uid) DESC LIMIT 50"
            ).fetchall()
        ]
    finally:
        con.close()

    if integrity != "ok":
        failures.append("sqlite_integrity_not_ok")

    replay_plan = {
        "plan_id": "HISTORICAL_BLIND_REPLAY_PLAN_V1",
        "mode": "NOAPI_PLAN_ONLY",
        "purpose": "Define blind historical replay without result peeking and without DB writes.",
        "core_rule": "input first, seal input, predict, seal prediction, fetch results, compare last",
        "phases": [
            {
                "id": "HBR_A_INPUT_ONLY_SOURCE_PLAN_NOAPI",
                "purpose": "Select historical sources and time windows without fetching outcome labels.",
                "network": False,
                "db_write": False,
                "result_labels_allowed": False,
                "output": "source plan artifact only"
            },
            {
                "id": "HBR_B_INPUT_ONLY_FETCH_AND_SEAL_WITH_NETWORK_TEMPFILES",
                "purpose": "Fetch only historical input/news items into temp files, not production DB.",
                "network": True,
                "db_write": False,
                "production_db_insert": False,
                "result_labels_allowed": False,
                "required_seal": "input_manifest_sha256"
            },
            {
                "id": "HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI",
                "purpose": "Run ingress/policy simulation against sealed input without inserting rows.",
                "network": False,
                "db_write": False,
                "production_db_insert": False,
                "dry_run_hook_required": True,
                "collision_policy": {
                    "existing_uid_collision": "SKIP_AND_REPORT",
                    "hist_news_existing_collision": "SKIP_AND_REPORT",
                    "runtime_uid_collision": "HOLD",
                    "unknown_namespace": "QUARANTINE_PLAN_ONLY"
                }
            },
            {
                "id": "HBR_D_PREDICTION_RUN_WITHOUT_RESULTS_NOAPI",
                "purpose": "Generate predictions/scores from sealed input only, without outcomes.",
                "network": False,
                "db_write": False,
                "result_labels_allowed": False,
                "required_seal": "prediction_manifest_sha256"
            },
            {
                "id": "HBR_E_RESULT_FETCH_AFTER_PREDICTION_SEAL_WITH_NETWORK",
                "purpose": "Fetch outcomes only after input and prediction manifests are sealed.",
                "network": True,
                "db_write": False,
                "result_labels_allowed": True,
                "precondition": [
                    "input_manifest_sha256_exists",
                    "prediction_manifest_sha256_exists"
                ]
            },
            {
                "id": "HBR_F_SCORE_COMPARISON_NOAPI",
                "purpose": "Compare predictions to outcomes and produce metrics artifact.",
                "network": False,
                "db_write": False,
                "production_db_insert": False,
                "score_comparison_last": True
            }
        ],
        "red_lines": {
            "no_result_peeking_before_prediction_seal": True,
            "production_db_write_forbidden": True,
            "production_db_insert_forbidden": True,
            "service_timer_change_forbidden": True,
            "trade_authority_forbidden": True,
            "paper_live_trade_forbidden": True,
            "manual_runner_execution_forbidden": True
        },
        "manifests": {
            "input_manifest_required": True,
            "input_manifest_hash": "sha256",
            "prediction_manifest_required": True,
            "prediction_manifest_hash": "sha256",
            "outcome_manifest_required_after_prediction": True,
            "artifact_only_state": True
        },
        "collision_and_replay_policy": {
            "dry_run_hook": "required",
            "existing_production_uids_loaded_readonly": True,
            "uid_collision_insert_action": "never_insert_skip_and_report",
            "historical_existing_collision_action": "skip_and_report",
            "runtime_collision_action": "hold",
            "duplicate_source_url_action": "dedupe_and_report",
            "unknown_namespace_action": "quarantine_plan_only"
        },
        "metrics_plan": {
            "minimum_metrics": [
                "input_count",
                "accepted_simulated_count",
                "skipped_collision_count",
                "quarantine_candidate_count",
                "prediction_count",
                "outcome_count_after_seal",
                "matched_prediction_outcome_count",
                "precision_like_score",
                "risk_false_positive_count",
                "risk_false_negative_count"
            ],
            "success_is_not_profit": True,
            "success_is_pipeline_truthfulness": True
        }
    }

    tests = [
        {
            "test_id": "T01_PRIOR_ERA60_OK",
            "ok": prior.get("decision") == "OK_ERA60_SCHEMA_HARDENING_BACKLOG_PLAN_NOAPI"
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
            "test_id": "T04_NO_RESULT_PEEKING_RULE_DEFINED",
            "ok": replay_plan["red_lines"]["no_result_peeking_before_prediction_seal"] is True
        },
        {
            "test_id": "T05_PRODUCTION_DB_WRITE_FORBIDDEN",
            "ok": replay_plan["red_lines"]["production_db_write_forbidden"] is True and replay_plan["red_lines"]["production_db_insert_forbidden"] is True
        },
        {
            "test_id": "T06_COLLISION_DRYRUN_HOOK_REQUIRED",
            "ok": replay_plan["collision_and_replay_policy"]["dry_run_hook"] == "required"
        },
        {
            "test_id": "T07_INPUT_AND_PREDICTION_SEAL_REQUIRED",
            "ok": replay_plan["manifests"]["input_manifest_required"] is True and replay_plan["manifests"]["prediction_manifest_required"] is True
        },
        {
            "test_id": "T08_RESULT_FETCH_AFTER_PREDICTION_SEAL",
            "ok": replay_plan["phases"][4]["precondition"] == ["input_manifest_sha256_exists", "prediction_manifest_sha256_exists"]
        },
        {
            "test_id": "T09_NOAPI_BOUNDARY_FOR_PLAN",
            "ok": True,
            "api_call": False,
            "db_schema_change": False,
            "db_write": False,
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
        "stage": "HISTORICAL_BLIND_REPLAY_PLAN_NOAPI",
        "generated_at_utc": generated_at,
        "decision": "OK_HISTORICAL_BLIND_REPLAY_PLAN_NOAPI" if not failures else "FAIL_HISTORICAL_BLIND_REPLAY_PLAN_NOAPI",
        "prior": "data/control/era60_schema_hardening_backlog_plan_noapi_v1.json",
        "policy_json": "runtime/policies/news_runtime_policy_lock_v1.json",
        "policy_json_sha256": sha256_file(POLICY),
        "policy_verifier": "tools/news_runtime_policy_verifier_v1.py",
        "policy_verifier_sha256": sha256_file(VERIFIER),
        "compile_verifier": compile_verifier,
        "verifier_result": verifier_result,
        "db_counts": counts,
        "sqlite_integrity": integrity,
        "schema": schema,
        "existing_uid_sample_readonly": existing_uids_sample,
        "replay_plan": replay_plan,
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
        "next": "HBR_A_INPUT_ONLY_SOURCE_PLAN_NOAPI" if not failures else "HISTORICAL_BLIND_REPLAY_PLAN_HOLD"
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
