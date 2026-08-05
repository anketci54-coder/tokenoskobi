
from pathlib import Path
import json, sqlite3

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PLAN = ROOT / "config/news_historical_access_layer_plan_v1.json"
PRIOR = ROOT / "data/control/news_runtime_freshness_monitor_dryrun_noapi_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def q(name):
    return '"' + str(name).replace('"', '""') + '"'

def validate():
    plan = load(PLAN)
    prior = load(PRIOR)
    failures = []
    warnings = []

    if prior.get("decision") != "OK_NEWS_RUNTIME_FRESHNESS_MONITOR_DRYRUN_NOAPI":
        failures.append("prior_freshness_dryrun_not_ok")

    boundary = plan.get("authority_boundary", {})
    for k in ["api_call","network_call","db_write","db_schema_change","index_creation","service_change","timer_change","paper_trade","live_trade","execution_authority"]:
        if boundary.get(k) is not False:
            failures.append("authority_boundary_not_false:" + k)

    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    try:
        for t in TABLES:
            try:
                con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()
            except Exception:
                failures.append("table_unreadable:" + t)
    finally:
        con.close()

    dims = set(plan.get("query_contract", {}).get("required_query_dimensions", []))
    required = {
        "date_range", "source_uid", "news_uid", "symbol", "chain",
        "risk_label", "decision_from_artifacts", "route_from_artifacts",
        "url_hash", "raw_hash"
    }
    missing = sorted(required - dims)
    if missing:
        failures.append("missing_query_dimensions:" + ",".join(missing))

    idx = plan.get("index_strategy_plan_only", {})
    if idx.get("required") is not True:
        failures.append("index_strategy_not_required")
    if idx.get("create_now") is not False:
        failures.append("index_creation_not_blocked")
    if len(idx.get("candidate_indexes", [])) < 8:
        failures.append("too_few_index_candidates")

    dedup = plan.get("deduplication_policy_plan_only", {})
    if dedup.get("required") is not True:
        failures.append("dedup_not_required")
    if dedup.get("backfill_now") is not False:
        failures.append("backfill_not_blocked")
    if dedup.get("no_duplicate_raw_feed_events") is not True:
        failures.append("no_duplicate_rule_missing")

    legacy = plan.get("query_contract", {}).get("legacy_id_policy", {})
    if legacy.get("legacy_db_primary_news_id") != "news_uid":
        failures.append("legacy_news_uid_not_locked")
    if legacy.get("new_ingress_primary_event_id") != "event_uid":
        failures.append("event_uid_not_locked")

    return {
        "decision": "OK_NEWS_HISTORICAL_ACCESS_LAYER_PLAN_VALIDATED" if not failures else "FAIL_NEWS_HISTORICAL_ACCESS_LAYER_PLAN_VALIDATED",
        "failures": failures,
        "warnings": warnings,
        "table_count": len(TABLES),
        "query_dimension_count": len(dims),
        "index_candidate_count": len(idx.get("candidate_indexes", [])),
        "dedup_required": dedup.get("required"),
        "backfill_now": dedup.get("backfill_now"),
        "index_creation_now": idx.get("create_now")
    }

if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2, sort_keys=True))
