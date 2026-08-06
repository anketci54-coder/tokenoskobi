
from pathlib import Path
import json

ROOT = Path("/root/tokenoskobi_clean_v1")
PLAN = ROOT / "config/news_runtime_freshness_monitor_plan_v1.json"
FINAL_SEAL = ROOT / "data/control/news_ingress_chain_final_review_and_seal_noapi_v1.json"

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def validate():
    plan = load(PLAN)
    seal = load(FINAL_SEAL)
    failures = []
    warnings = []

    if seal.get("decision") != "OK_NEWS_INGRESS_CHAIN_FINAL_REVIEW_AND_SEAL_NOAPI":
        failures.append("prior_ingress_final_seal_not_ok")

    boundary = plan.get("authority_boundary", {})
    for k in ["api_call", "network_call", "db_write", "db_schema_change", "index_creation", "service_change", "timer_change", "paper_trade", "live_trade", "execution_authority"]:
        if boundary.get(k) is not False:
            failures.append("authority_boundary_not_false:" + k)

    if len(plan.get("monitored_tables", [])) != 4:
        failures.append("monitored_table_count_not_four")

    history = plan.get("history_alignment", {})
    if history.get("index_strategy_required") is not True:
        failures.append("index_strategy_not_required")
    if history.get("deduplication_policy_required") is not True:
        failures.append("dedup_policy_not_required")
    if history.get("index_strategy_plan_only_now", {}).get("no_index_creation_in_this_step") is not True:
        failures.append("index_creation_not_blocked")
    if history.get("deduplication_policy_plan_only_now", {}).get("backfill_must_not_duplicate_raw_feed_events") is not True:
        failures.append("backfill_dedup_not_locked")

    required_query_dims = {"date_range", "source_id", "token", "chain", "severity", "decision", "route", "event_uid"}
    dims = set(history.get("query_dimensions", []))
    missing = sorted(required_query_dims - dims)
    if missing:
        failures.append("missing_history_query_dimensions:" + ",".join(missing))

    thresholds = plan.get("threshold_policy_noapi_plan", {})
    if thresholds.get("raw_feed_warn_after_minutes", 0) <= 0:
        failures.append("bad_raw_warn_threshold")
    if thresholds.get("raw_feed_fail_after_minutes", 0) <= thresholds.get("raw_feed_warn_after_minutes", 0):
        failures.append("bad_raw_fail_threshold")
    if thresholds.get("no_auto_restart") is not True:
        failures.append("auto_restart_not_blocked")

    return {
        "decision": "OK_NEWS_RUNTIME_FRESHNESS_MONITOR_PLAN_VALIDATED" if not failures else "FAIL_NEWS_RUNTIME_FRESHNESS_MONITOR_PLAN_VALIDATED",
        "failures": failures,
        "warnings": warnings,
        "plan": str(PLAN),
        "prior_final_seal": str(FINAL_SEAL),
        "monitored_table_count": len(plan.get("monitored_tables", [])),
        "history_query_dimension_count": len(history.get("query_dimensions", [])),
        "index_strategy_required": history.get("index_strategy_required"),
        "deduplication_policy_required": history.get("deduplication_policy_required")
    }

if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2, sort_keys=True))
