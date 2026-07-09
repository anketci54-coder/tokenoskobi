
from pathlib import Path
import json, sqlite3

ROOT = Path("/root/tokenoskobi_clean_v1")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PLAN = ROOT / "config/news_producer_staleness_fix_apply_plan_v1.json"
DRYRUN_ART = ROOT / "data/control/news_producer_staleness_fix_dryrun_noapi_v1.json"

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
    dryrun_art = load(DRYRUN_ART)
    dryrun = dryrun_art.get("dryrun", {})
    preview = dryrun.get("preview", {})
    expected = plan.get("expected_tempdb_delta", {})
    failures = []
    warnings = []

    if dryrun_art.get("decision") != "OK_NEWS_PRODUCER_STALENESS_FIX_DRYRUN_NOAPI":
        failures.append("prior_dryrun_not_ok")

    if preview.get("apply_plan_needed") is not True:
        failures.append("apply_plan_needed_not_true")

    if plan.get("apply_plan_scope", {}).get("real_db_apply_now") is not False:
        failures.append("real_db_apply_now_not_false")

    if plan.get("apply_plan_scope", {}).get("tempdb_apply_next") is not True:
        failures.append("tempdb_apply_next_not_true")

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

    if expected.get("news_raw_feed_events") != 0:
        failures.append("expected_raw_delta_not_zero")

    if int(expected.get("news_token_match_events") or 0) <= 0:
        failures.append("expected_token_match_delta_not_positive")

    if int(expected.get("news_signal_events") or 0) <= 0:
        failures.append("expected_signal_delta_not_positive")

    if int(expected.get("news_score_events_v1") or 0) <= 0:
        failures.append("expected_score_delta_not_positive")

    before = counts()
    after = counts()
    db_delta = {k: after[k] - before[k] for k in before}

    if any(v != 0 for v in db_delta.values()):
        failures.append("real_db_delta_not_zero")

    gates = plan.get("safety_gates_for_next", {})
    if gates.get("next_step") != "NEWS_PRODUCER_STALENESS_FIX_TEMPDB_APPLY_DRYRUN_NOAPI":
        failures.append("wrong_next_step")

    if plan.get("apply_algorithm_plan", {}).get("batch_limit", 0) > 250:
        failures.append("batch_limit_too_high")

    return {
        "decision": "OK_NEWS_PRODUCER_STALENESS_FIX_APPLY_PLAN_VALIDATED" if not failures else "FAIL_NEWS_PRODUCER_STALENESS_FIX_APPLY_PLAN_VALIDATED",
        "failures": failures,
        "warnings": warnings,
        "db_delta": db_delta,
        "expected_tempdb_delta": expected,
        "next": gates.get("next_step")
    }

if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2, sort_keys=True))
