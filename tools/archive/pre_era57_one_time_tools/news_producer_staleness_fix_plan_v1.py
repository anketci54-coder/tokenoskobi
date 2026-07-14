
from pathlib import Path
import json, sqlite3

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PLAN = ROOT / "config/news_producer_staleness_fix_plan_v1.json"
AUDIT = ROOT / "data/control/news_producer_staleness_root_cause_audit_noapi_v1.json"

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1"
]

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def q(x):
    return '"' + str(x).replace('"', '""') + '"'

def counts():
    con = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True)
    out = {}
    try:
        for t in TABLES:
            out[t] = con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0]
    finally:
        con.close()
    return out

def validate():
    plan = load(PLAN)
    audit = load(AUDIT)
    failures = []
    warnings = []

    if audit.get("decision") != "OK_NEWS_PRODUCER_STALENESS_ROOT_CAUSE_AUDIT_NOAPI":
        failures.append("prior_audit_not_ok")

    if plan.get("locked_root_cause") != "RAW_FEED_IS_CURRENT_BUT_DERIVED_LAYERS_ARE_STALE":
        failures.append("locked_root_cause_wrong")

    boundary = plan.get("authority_boundary", {})
    for key in [
        "api_call",
        "network_call",
        "db_write",
        "db_schema_change",
        "index_creation",
        "service_change",
        "timer_change",
        "nginx_change",
        "paper_trade",
        "live_trade",
        "execution_authority"
    ]:
        if boundary.get(key) is not False:
            failures.append("authority_not_false:" + key)

    before = counts()
    after = counts()
    db_delta = {k: after[k] - before[k] for k in before}

    if any(v != 0 for v in db_delta.values()):
        failures.append("db_delta_not_zero")

    strategy = plan.get("fix_strategy_plan_only", {})
    if strategy.get("create_now") is not False:
        failures.append("create_now_not_false")
    if strategy.get("apply_now") is not False:
        failures.append("apply_now_not_false")

    required_props = set(strategy.get("required_properties", []))
    needed = {
        "idempotent_by_uid",
        "no_trade_authority",
        "bounded_batch_size",
        "readonly_dryrun_first",
        "raw_feed_not_modified"
    }
    missing = sorted(needed - required_props)
    if missing:
        failures.append("missing_required_properties:" + ",".join(missing))

    next_req = plan.get("dryrun_requirements_next", {})
    if next_req.get("next_step") != "NEWS_PRODUCER_STALENESS_FIX_DRYRUN_NOAPI":
        failures.append("wrong_next_step")

    if len(plan.get("current_evidence", {}).get("source_candidates", [])) == 0:
        warnings.append("no_source_candidate_detected")

    return {
        "decision": "OK_NEWS_PRODUCER_STALENESS_FIX_PLAN_VALIDATED" if not failures else "FAIL_NEWS_PRODUCER_STALENESS_FIX_PLAN_VALIDATED",
        "failures": failures,
        "warnings": warnings,
        "db_delta": db_delta,
        "source_candidate_count": len(plan.get("current_evidence", {}).get("source_candidates", [])),
        "next": next_req.get("next_step")
    }

if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2, sort_keys=True))
