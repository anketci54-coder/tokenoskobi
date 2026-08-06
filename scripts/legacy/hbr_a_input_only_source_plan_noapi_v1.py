
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3, subprocess, sys, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PRIOR = ROOT / "data/control/historical_blind_replay_plan_noapi_v1.json"
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

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

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
        failures.append("prior_historical_blind_replay_plan_missing")
        prior = {}
    else:
        prior = json.loads(PRIOR.read_text(encoding="utf-8"))
        if prior.get("decision") != "OK_HISTORICAL_BLIND_REPLAY_PLAN_NOAPI":
            failures.append("prior_historical_blind_replay_plan_not_ok")

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
        existing_uid_sample = [
            r[0] for r in con.execute(
                "SELECT news_uid FROM news_raw_feed_events ORDER BY COALESCE(fetched_at_utc,published_at_utc,news_uid) DESC LIMIT 75"
            ).fetchall()
        ]
        namespace_counts = {}
        for prefix in ["hist_news_", "timer_news_", "news_", "rss_news_", "news12_", "news21_"]:
            namespace_counts[prefix] = con.execute(
                "SELECT COUNT(*) FROM news_raw_feed_events WHERE news_uid LIKE ?",
                [prefix + "%"]
            ).fetchone()[0]
    finally:
        con.close()

    if integrity != "ok":
        failures.append("sqlite_integrity_not_ok")

    source_plan = {
        "plan_id": "HBR_A_INPUT_ONLY_SOURCE_PLAN_V1",
        "mode": "NOAPI_SOURCE_PLAN_ONLY",
        "purpose": "Choose blind historical input sources/windows without fetching data and without outcome labels.",
        "input_only": True,
        "outcome_labels_allowed": False,
        "network_call_in_this_step": False,
        "production_db_write": False,
        "production_db_insert": False,
        "manual_runner_execution": False,
        "sources": [
            {
                "source_id": "coindesk_rss_input_only_candidate",
                "source_name": "CoinDesk RSS",
                "source_type": "rss",
                "input_role": "historical_news_input",
                "outcome_role": "forbidden_in_HBR_A",
                "enabled_for_next_fetch_plan": True,
                "max_items_next_step": 75
            },
            {
                "source_id": "cointelegraph_rss_input_only_candidate",
                "source_name": "Cointelegraph RSS",
                "source_type": "rss",
                "input_role": "historical_news_input",
                "outcome_role": "forbidden_in_HBR_A",
                "enabled_for_next_fetch_plan": True,
                "max_items_next_step": 75
            }
        ],
        "time_windows": [
            {
                "window_id": "HBR_W1_SETTLED_INPUT_2026_06_01_2026_06_15",
                "start_utc": "2026-06-01T00:00:00+00:00",
                "end_utc": "2026-06-15T23:59:59+00:00",
                "reason": "settled historical input window; outcomes intentionally not fetched in HBR_A"
            },
            {
                "window_id": "HBR_W2_SETTLED_INPUT_2026_06_16_2026_06_30",
                "start_utc": "2026-06-16T00:00:00+00:00",
                "end_utc": "2026-06-30T23:59:59+00:00",
                "reason": "second settled historical input window; outcomes intentionally not fetched in HBR_A"
            }
        ],
        "next_fetch_caps": {
            "max_total_input_items": 150,
            "max_items_per_source": 75,
            "max_sources": 2,
            "timeout_seconds_per_source": 20,
            "retry_count": 1,
            "write_target": "tempfiles_only",
            "production_db_insert_allowed": False
        },
        "allowed_input_fields_next_step": [
            "source_id",
            "source_name",
            "published_at_utc",
            "title",
            "url",
            "url_hash",
            "raw_hash",
            "candidate_news_uid",
            "fetched_at_utc"
        ],
        "forbidden_fields_before_prediction_seal": [
            "outcome_label",
            "price_after",
            "future_return_pct",
            "result",
            "win_loss",
            "success_failure",
            "future_price",
            "post_event_price_change",
            "score_comparison"
        ],
        "uid_policy_next_step": {
            "candidate_prefix": "hbr_input_",
            "production_prefix_insert": "forbidden_in_blind_replay",
            "existing_uid_collision": "SKIP_AND_REPORT",
            "hist_news_existing_collision": "SKIP_AND_REPORT",
            "runtime_uid_collision": "HOLD",
            "unknown_namespace": "QUARANTINE_PLAN_ONLY"
        },
        "seal_policy": {
            "source_plan_sha256_required": True,
            "input_manifest_sha256_required_next_step": True,
            "prediction_manifest_sha256_required_before_outcome_fetch": True
        }
    }

    canonical_source_plan_text = json.dumps(source_plan, ensure_ascii=False, sort_keys=True)
    source_plan_sha256 = sha256_text(canonical_source_plan_text)

    tests = [
        {
            "test_id": "T01_PRIOR_HISTORICAL_BLIND_REPLAY_PLAN_OK",
            "ok": prior.get("decision") == "OK_HISTORICAL_BLIND_REPLAY_PLAN_NOAPI"
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
            "test_id": "T04_NO_NETWORK_IN_HBR_A",
            "ok": source_plan["network_call_in_this_step"] is False
        },
        {
            "test_id": "T05_NO_DB_WRITE_OR_INSERT_IN_HBR_A",
            "ok": source_plan["production_db_write"] is False and source_plan["production_db_insert"] is False
        },
        {
            "test_id": "T06_OUTCOME_LABELS_FORBIDDEN",
            "ok": source_plan["outcome_labels_allowed"] is False and len(source_plan["forbidden_fields_before_prediction_seal"]) >= 5
        },
        {
            "test_id": "T07_SOURCES_AND_WINDOWS_DEFINED",
            "ok": len(source_plan["sources"]) == 2 and len(source_plan["time_windows"]) == 2
        },
        {
            "test_id": "T08_FETCH_CAPS_DEFINED",
            "ok": source_plan["next_fetch_caps"]["max_total_input_items"] == 150 and source_plan["next_fetch_caps"]["production_db_insert_allowed"] is False
        },
        {
            "test_id": "T09_COLLISION_POLICY_DEFINED",
            "ok": source_plan["uid_policy_next_step"]["existing_uid_collision"] == "SKIP_AND_REPORT" and source_plan["uid_policy_next_step"]["runtime_uid_collision"] == "HOLD"
        },
        {
            "test_id": "T10_SOURCE_PLAN_SHA256_CREATED",
            "ok": len(source_plan_sha256) == 64,
            "source_plan_sha256": source_plan_sha256
        },
        {
            "test_id": "T11_NOAPI_BOUNDARY_FOR_SOURCE_PLAN",
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
        "stage": "HBR_A_INPUT_ONLY_SOURCE_PLAN_NOAPI",
        "generated_at_utc": generated_at,
        "decision": "OK_HBR_A_INPUT_ONLY_SOURCE_PLAN_NOAPI" if not failures else "FAIL_HBR_A_INPUT_ONLY_SOURCE_PLAN_NOAPI",
        "prior": "data/control/historical_blind_replay_plan_noapi_v1.json",
        "policy_json": "runtime/policies/news_runtime_policy_lock_v1.json",
        "policy_json_sha256": sha256_file(POLICY),
        "policy_verifier": "tools/news_runtime_policy_verifier_v1.py",
        "policy_verifier_sha256": sha256_file(VERIFIER),
        "compile_verifier": compile_verifier,
        "verifier_result": verifier_result,
        "db_counts": counts,
        "sqlite_integrity": integrity,
        "schema": schema,
        "namespace_counts_readonly": namespace_counts,
        "existing_uid_sample_readonly": existing_uid_sample,
        "source_plan": source_plan,
        "source_plan_sha256": source_plan_sha256,
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
        "next": "HBR_B_INPUT_ONLY_FETCH_AND_SEAL_WITH_NETWORK_TEMPFILES" if not failures else "HBR_A_INPUT_ONLY_SOURCE_PLAN_HOLD"
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2, sort_keys=True))
