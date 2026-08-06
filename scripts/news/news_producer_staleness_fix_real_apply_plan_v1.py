
from pathlib import Path
import json, sqlite3

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PLAN = ROOT / "config/news_producer_staleness_fix_real_apply_plan_v1.json"
PRIOR = ROOT / "data/control/news_producer_staleness_fix_tempdb_post_audit_noapi_v1.json"

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
    try:
        return {t: con.execute("SELECT COUNT(*) FROM " + q(t)).fetchone()[0] for t in TABLES}
    finally:
        con.close()

def validate():
    plan = load(PLAN)
    prior = load(PRIOR)
    failures = []
    warnings = []

    if prior.get("decision") != "OK_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_POST_AUDIT_NOAPI":
        failures.append("prior_not_ok")

    if plan.get("real_apply_scope", {}).get("real_db_apply_now") is not False:
        failures.append("real_db_apply_now_not_false")

    if plan.get("real_apply_scope", {}).get("real_db_apply_next") is not True:
        failures.append("real_db_apply_next_not_true")

    if plan.get("real_apply_scope", {}).get("requires_commander_approval_before_next") is not True:
        failures.append("commander_approval_not_required")

    boundary = plan.get("authority_boundary_this_step", {})
    for key in [
        "api_call", "network_call", "db_write", "db_schema_change",
        "index_creation", "service_change", "timer_change", "nginx_change",
        "paper_trade", "live_trade", "execution_authority"
    ]:
        if boundary.get(key) is not False:
            failures.append("authority_not_false:" + key)

    preview = plan.get("current_real_db_preview", {})
    expected = plan.get("expected_real_apply_delta", {})
    candidate_count = int(preview.get("current_candidate_count") or 0)

    if candidate_count <= 0:
        failures.append("candidate_count_not_positive")

    if candidate_count > plan.get("apply_algorithm_locked", {}).get("batch_limit", 0):
        failures.append("candidate_count_exceeds_batch_limit")

    if expected.get("news_raw_feed_events") != 0:
        failures.append("expected_raw_delta_not_zero")

    for t in ["news_token_match_events", "news_signal_events", "news_score_events_v1"]:
        if expected.get(t) != candidate_count:
            failures.append("expected_delta_mismatch:" + t)

    before = counts()
    after = counts()
    db_delta = {k: after[k] - before[k] for k in before}

    derived_delta = {
        "news_token_match_events": db_delta.get("news_token_match_events", 0),
        "news_signal_events": db_delta.get("news_signal_events", 0),
        "news_score_events_v1": db_delta.get("news_score_events_v1", 0)
    }

    if any(v != 0 for v in derived_delta.values()):
        failures.append("derived_db_delta_not_zero")

    if db_delta.get("news_raw_feed_events", 0) != 0:
        warnings.append("raw_timer_delta_observed_during_plan_validation")

    next_step = plan.get("safety_gates_for_next", {}).get("next_step")
    if next_step != "NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_WITH_BACKUP":
        failures.append("wrong_next_step")

    return {
        "decision": "OK_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_PLAN_VALIDATED" if not failures else "FAIL_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_PLAN_VALIDATED",
        "failures": failures,
        "warnings": warnings,
        "db_delta": db_delta,
        "candidate_count": candidate_count,
        "expected_real_apply_delta": expected,
        "next": next_step
    }

if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2, sort_keys=True))
