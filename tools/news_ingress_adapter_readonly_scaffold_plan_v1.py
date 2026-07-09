
from pathlib import Path
import json

ROOT = Path("/root/tokenoskobi_clean_v1")
PLAN = ROOT / "config/news_ingress_adapter_readonly_scaffold_plan_v1.json"
REGISTRY = ROOT / "config/news_source_registry_v1.json"
GATE_CONTRACT = ROOT / "config/news_gate_logic_contract_v1.json"
ENVELOPE_CONTRACT = ROOT / "config/news_minimal_ingress_output_contract_v1.json"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def validate():
    plan = load(PLAN)
    registry = load(REGISTRY)
    gate = load(GATE_CONTRACT)
    envelope = load(ENVELOPE_CONTRACT)

    failures = []
    warnings = []

    registry_sources = {s["source_id"]: s for s in registry["sources"]}
    mapped = {m["source_id"]: m for m in plan["source_adapter_mapping"]}

    for sid in registry_sources:
        if sid not in mapped:
            failures.append("source_not_mapped:" + sid)

    for sid, item in mapped.items():
        if item["adapter_family"] == "UNMAPPED":
            failures.append("source_unmapped_family:" + sid)
        if item["adapter_runtime_enabled_now"] is not False:
            failures.append("adapter_enabled_in_plan:" + sid)
        if item["api_required"] is True and item["adapter_runtime_enabled_now"] is not False:
            failures.append("api_required_source_enabled:" + sid)
        if item["websocket_supported"] is True and item["adapter_runtime_enabled_now"] is not False:
            failures.append("websocket_source_enabled:" + sid)
        if item["incubation_period"] is True and item["adapter_family"] != "security_social_alert_readonly":
            failures.append("incubation_wrong_family:" + sid)

    guards = plan["hard_guards"]
    for k, v in guards.items():
        if v is not True:
            failures.append("hard_guard_false:" + k)

    iso = plan["isolation_policy"]
    forbidden_true = [
        "runtime_write_to_core_db",
        "runtime_write_to_trade",
        "runtime_service_change",
        "runtime_timer_change",
        "network_enabled_in_this_step",
        "api_enabled_in_this_step"
    ]
    for k in forbidden_true:
        if iso.get(k) is not False:
            failures.append("isolation_violation:" + k)

    required_gates = [
        "SOURCE_TRUST_GATE",
        "SECURITY_RELEVANCE_GATE",
        "GENERAL_NEWS_QUARANTINE_GATE",
        "INCUBATION_GATE",
        "CEX_PAIR_PRE_ANNOUNCEMENT_GATE",
        "DEX_MARKET_BEHAVIOR_GATE",
        "TOKEN_MATCH_GATE"
    ]
    for g in required_gates:
        if g not in gate["gates"]:
            failures.append("missing_gate:" + g)

    required_fields = set(envelope["required_fields"])
    needed = {"schema", "event_uid", "source_id", "normalized_event", "gate_decision", "routing"}
    if not needed.issubset(required_fields):
        failures.append("envelope_contract_missing_required_fields")

    return {
        "plan": str(PLAN),
        "source_count": len(registry_sources),
        "mapped_count": len(mapped),
        "adapter_family_count": len(plan["adapter_families"]),
        "api_required_sources": [sid for sid, m in mapped.items() if m["api_required"] is True],
        "websocket_sources": [sid for sid, m in mapped.items() if m["websocket_supported"] is True],
        "quarantine_sources": [sid for sid, m in mapped.items() if m["priority"] == "QUARANTINE"],
        "incubation_sources": [sid for sid, m in mapped.items() if m["incubation_period"] is True],
        "failures": failures,
        "warnings": warnings,
        "decision": "OK_ADAPTER_READONLY_SCAFFOLD_PLAN" if not failures else "FAIL_ADAPTER_READONLY_SCAFFOLD_PLAN"
    }

if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2, sort_keys=True))
