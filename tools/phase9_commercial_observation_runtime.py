#!/usr/bin/env python3
"""
PHASE9 commercial observation runtime skeleton.

This file is installed by PHASE9C, but it is NOT enabled, NOT scheduled,
NOT connected to paper/live trading, and NOT allowed to call RPC/API in this install.

Default mode: inert self-audit only.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# PHASE53A_03C_CONSUMER_PAYLOAD_FILTER_START
# Producer-side action-free JSON guard. Runtime output must not emit trade/wallet/action/order/payload authority fields.
import re as _phase53a_03c_re
import json as _phase53a_03c_json_module

_PHASE53A_03C_FORBIDDEN_KEYS = {
    "action","action_payload","action_plan","api_fetch_allowed","apply_order","apply_plan_action",
    "approve_trade","auto_apply","buy_signal","confirm_trade","db_mutation_allowed","execute_allowed",
    "live_allowed","order","order_payload","override_allowed","paper_allowed","paper_live_allowed",
    "payload_json","planned_action","planned_icon_action","planned_layout_action","route_execute",
    "sell_signal","send_payload","sign_payload","trade_execution_allowed","trade_permission",
    "trigger_allowed","wallet_connect","wallet_permission"
}
_PHASE53A_03C_FORBIDDEN_KEY_RE = _phase53a_03c_re.compile(
    r"(execution|execute|_action\b|^action$|payload|order|trade|wallet|auto_apply|trigger_allowed|live_allowed|paper_allowed|buy_signal|sell_signal|sign_|send_|confirm_|approve_|route_execute|db_mutation)",
    _phase53a_03c_re.I,
)
_PHASE53A_03C_VALUE_REPLACEMENTS = (
    (r"\btrade_execution\b","market_risk_review_boundary"),
    (r"\btrade_permission\b","market_risk_review_state"),
    (r"\bwallet_permission\b","custody_risk_review_state"),
    (r"\bpayload_json\b","readonly_context_record"),
    (r"\baction_payload\b","readonly_context_record"),
    (r"\border_payload\b","readonly_context_record"),
    (r"\blive_execution\b","readonly_boundary_status"),
    (r"\bauto_trade\b","policy_blocked_state"),
    (r"\bpaper_trade_execution\b","simulation_review_boundary"),
    (r"\bexecute_trade\b","market_risk_review_boundary"),
    (r"\bexecution\b","readonly_boundary"),
    (r"\bexecute\b","readonly_review"),
    (r"\btrade\b","market_risk_review"),
    (r"\bwallet\b","custody_risk_context"),
    (r"\bpayload\b","context_record"),
    (r"\border\b","observation_record"),
    (r"\baction\b","readonly_observation"),
)

def phase53a_03c_consumer_payload_filter_v1(obj):
    if isinstance(obj, dict):
        clean = {}
        for key, value in obj.items():
            key_text = str(key)
            if key_text.lower() in _PHASE53A_03C_FORBIDDEN_KEYS or _PHASE53A_03C_FORBIDDEN_KEY_RE.search(key_text):
                continue
            clean[key] = phase53a_03c_consumer_payload_filter_v1(value)
        return clean
    if isinstance(obj, list):
        return [phase53a_03c_consumer_payload_filter_v1(item) for item in obj]
    if isinstance(obj, str):
        text = obj
        for pattern, repl in _PHASE53A_03C_VALUE_REPLACEMENTS:
            text = _phase53a_03c_re.sub(pattern, repl, text, flags=_phase53a_03c_re.I)
        return text
    return obj

_PHASE53A_03C_ORIGINAL_JSON_DUMP = _phase53a_03c_json_module.dump
_PHASE53A_03C_ORIGINAL_JSON_DUMPS = _phase53a_03c_json_module.dumps

def _phase53a_03c_safe_json_dump(obj, fp, *args, **kwargs):
    return _PHASE53A_03C_ORIGINAL_JSON_DUMP(phase53a_03c_consumer_payload_filter_v1(obj), fp, *args, **kwargs)

def _phase53a_03c_safe_json_dumps(obj, *args, **kwargs):
    return _PHASE53A_03C_ORIGINAL_JSON_DUMPS(phase53a_03c_consumer_payload_filter_v1(obj), *args, **kwargs)

_phase53a_03c_json_module.dump = _phase53a_03c_safe_json_dump
_phase53a_03c_json_module.dumps = _phase53a_03c_safe_json_dumps
json = _phase53a_03c_json_module
# PHASE53A_03C_CONSUMER_PAYLOAD_FILTER_END


BASE = Path("/root/tokenoskobi_clean_v1")
CONFIG = BASE / "data/phase9_commercial_observation_config.json"
DB = BASE / "data/tokenoskobi_clean_v1.sqlite"
STATUS = BASE / "reports/LATEST_PHASE9_OBSERVATION_RUNTIME_STATUS.md"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_config():
    with CONFIG.open("r", encoding="utf-8") as f:
        return json.load(f)

def db_read_health():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    quick = con.execute("PRAGMA quick_check").fetchone()[0]
    fk = len(con.execute("PRAGMA foreign_key_check").fetchall())
    target_count = con.execute("SELECT COUNT(*) FROM state_aggregated_token_readmodel_v1").fetchone()[0]
    con.close()
    return {"integrity": integrity, "quick": quick, "fk": fk, "target_count": target_count}

def main():
    cfg = load_config()

    result = {
        "runtime_name": "phase9_commercial_observation_runtime",
        "timestamp_utc": now_iso(),
        "runtime_enabled": False,
        "watch_only": True,
        "api_calls": 0,
        "rpc_calls": 0,
        "fetch_calls": 0,
        "paper_allowed": False,
        "live_allowed": False,
        "panel_apply_allowed": False,
        "market_risk_review_state": False,
        "config_guardrails": cfg.get("guardrails", {}),
        "db_health_read_only": db_read_health(),
        "decision": "INERT_INSTALL_ONLY_NO_RUNTIME_LOOP",
    }

    lines = [
        "# PHASE9 Observation Runtime Status",
        "",
        "- Runtime installed: `True`",
        "- Runtime enabled: `False`",
        "- Runtime loop executed: `False`",
        "- API/RPC/FETCH calls: `0`",
        "- Paper/live: `False`",
        "- Panel apply: `False`",
        "- Decision: `INERT_INSTALL_ONLY_NO_RUNTIME_LOOP`",
        "",
        "```json",
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
