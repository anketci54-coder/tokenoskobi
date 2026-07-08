#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import os

ROOT = Path("/root/tokenoskobi_clean_v1")
STAGE = "HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI"

OUT_JSON = ROOT / "data/control/hot_intelligence_ingress_gateway_plan_noapi_v1.json"
OUT_MD = ROOT / "docs/HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI.md"
OUT_REPORT = ROOT / "reports/LATEST_HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI.md"

NEWS_F = ROOT / "data/control/news_f_final_operational_seal_with_known_warnings_v1.json"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, type(e).__name__ + ":" + str(e)[:300]

def safe_write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    os.replace(tmp, path)

def safe_write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def md(result):
    lines = []
    lines.append("# HOT Intelligence Ingress Gateway Plan NOAPI")
    lines.append("")
    lines.append(f"- stage: `{STAGE}`")
    lines.append(f"- generated_at_utc: `{result['generated_at_utc']}`")
    lines.append(f"- decision: `{result['decision']}`")
    lines.append(f"- next_step: `{result['next_step']}`")
    lines.append("")
    lines.append("## Red Team Locked Rules")
    for x in result["red_team_locked_rules"]:
        lines.append(f"- `{x['code']}`: {x['rule']}")
    lines.append("")
    lines.append("## Cold / Hot Boundary")
    for k, v in result["cold_hot_boundary"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Atomic Ingress Event Contract")
    lines.append("```json")
    lines.append(json.dumps(result["contracts"]["intelligence_ingress_event_v1"], ensure_ascii=False, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("## Filter / Routing Policy")
    for item in result["filter_routing_policy"]:
        lines.append(f"- `{item['route']}`: {item['condition']}")
    lines.append("")
    lines.append("## Conflict Resolver Policy")
    for item in result["conflict_resolver_policy"]:
        lines.append(f"- `{item['code']}`: {item['rule']}")
    lines.append("")
    lines.append("## Safety Boundary")
    for k, v in result["authority"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    return "\n".join(lines)

def main():
    news_f_obj, news_f_err = read_json(NEWS_F)

    result = {
        "stage": STAGE,
        "generated_at_utc": now_iso(),
        "decision": "OK_HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI_DOCUMENTED",
        "next_step": "HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_NOAPI",
        "news_f_reference": {
            "path": str(NEWS_F),
            "read_error": news_f_err,
            "decision": news_f_obj.get("decision") if isinstance(news_f_obj, dict) else None,
            "next_step": news_f_obj.get("next_step") if isinstance(news_f_obj, dict) else None
        },
        "authority": {
            "plan_only": True,
            "noapi": True,
            "real_db_write": False,
            "db_schema_write": False,
            "runtime_change": False,
            "systemd_change": False,
            "telegram_token_use": False,
            "discord_bot_use": False,
            "x_api_use": False,
            "wallet": False,
            "signing": False,
            "live_trade": False,
            "paper_trade": False,
            "ai_trade_authority": False,
            "repo_artifact_write": True
        },
        "cold_hot_boundary": {
            "cold_news_refresh": "20min timer, fallback/backfill only",
            "hot_gateway": "primary war intelligence ingress plan",
            "forbidden_claim": "20min timer is real-time intelligence",
            "current_stage": "plan and contract only"
        },
        "red_team_decision": "OK_HOT_GATEWAY_PLAN_CAN_PROCEED_NOAPI",
        "red_team_locked_rules": [
            {"code": "ONCHAIN_SOURCE_OF_TRUTH", "rule": "Onchain evidence outranks social/news claims when conflict exists."},
            {"code": "CONFLICT_RESOLVER_BLOCKER", "rule": "HOT Gateway cannot go live without conflict resolver policy."},
            {"code": "CRITICAL_REQUIRES_EVIDENCE", "rule": "CRITICAL event cannot become outbound alarm without Evidence/Prosecutor confirmation."},
            {"code": "UNKNOWN_MONITOR", "rule": "Unknown anomaly is not automatically dangerous; classify as UNKNOWN_MONITOR unless severity evidence exists."},
            {"code": "FUZZY_DUPLICATE_REQUIRED", "rule": "Exact hash is not enough; content similarity/fuzzy duplicate threshold must be planned."},
            {"code": "DYNAMIC_TRUST_SCORE", "rule": "Source trust score must decay dynamically; recent major false signal has strong negative impact."},
            {"code": "RATE_LIMIT_INGRESS", "rule": "Source-level rate limiting is mandatory against spam wave attacks."},
            {"code": "ATOMIC_DATA_ONLY", "rule": "Do not copy every API parameter; keep only minimum decision-relevant fields."},
            {"code": "SOURCE_REGISTRY_DEFER_DETAIL", "rule": "Deep source registry details are deferred; only minimum source identity/trust fields now."},
            {"code": "NO_TOKENS_NO_KEYS", "rule": "No Telegram token, Discord bot, X API, live API key, wallet, signing, trade, or paper trade in this stage."}
        ],
        "contracts": {
            "intelligence_ingress_event_v1": {
                "event_uid": "deterministic string",
                "source_uid": "string",
                "source_type": "telegram|discord|x|news|rss|onchain|dex|mempool|manual_synthetic",
                "received_at_utc": "ISO-8601",
                "raw_text_hash": "sha256",
                "canonical_content_hash": "sha256 normalized text",
                "fuzzy_duplicate_key": "planned similarity bucket",
                "raw_url_hash": "optional sha256",
                "chain": "optional string",
                "token_symbol": "optional string",
                "token_address": "optional string",
                "wallet_address": "optional string",
                "contract_address": "optional string",
                "event_type": "exploit|lp_pull|deployer_move|whale_move|bridge_risk|social_rumor|spam|unknown_monitor",
                "source_trust_score": "0-100 planned",
                "severity_guess": "INFO|WATCH|CRITICAL_CANDIDATE|QUARANTINE",
                "conflict_state": "NONE|SOCIAL_ONLY|ONCHAIN_CONFLICT|MULTI_SOURCE_CONFIRMED|QUARANTINE",
                "routing_status": "DROP|INFO|WATCH|CRITICAL_CANDIDATE|QUARANTINE"
            }
        },
        "filter_routing_policy": [
            {"route": "DROP", "condition": "price-only comment, generic shill, no token/chain/wallet/contract/actionable entity"},
            {"route": "INFO", "condition": "relevant but low severity, no immediate risk"},
            {"route": "WATCH", "condition": "single-source suspicious event or unknown_monitor without evidence"},
            {"route": "QUARANTINE", "condition": "conflicting evidence, spam wave, low-trust source, possible manipulation"},
            {"route": "CRITICAL_CANDIDATE", "condition": "high-severity event with entity extraction and at least preliminary evidence"},
            {"route": "CRITICAL_ALARM", "condition": "not produced by Gateway alone; requires Evidence/Prosecutor confirmation"}
        ],
        "conflict_resolver_policy": [
            {"code": "SOCIAL_VS_ONCHAIN", "rule": "If social says exploit but onchain has no anomaly, route WATCH or QUARANTINE, not CRITICAL_ALARM."},
            {"code": "ONCHAIN_CONFIRMED", "rule": "If onchain confirms abnormal LP/deployer/bridge/wallet behavior, raise severity."},
            {"code": "MULTI_SOCIAL_DUPLICATE", "rule": "Many social posts with same content are not multi-source confirmation unless independent source trust differs."},
            {"code": "FAST_BUT_FAKE_GUARD", "rule": "Speed cannot bypass source trust, duplicate filtering, and evidence requirement."}
        ],
        "dynamic_trust_score_plan": {
            "model": "exponential_decay_planned",
            "positive_history_weight": "decays over time",
            "recent_false_signal_penalty": "high impact",
            "major_manipulation_penalty": "can force quarantine",
            "source_compromise_mode": "manual or rule-based quarantine"
        },
        "fuzzy_duplicate_plan": {
            "exact_hash": "raw hash and canonical hash",
            "near_duplicate": "normalized title/text similarity planned",
            "threshold_policy": "same entity + similar content + close time window = duplicate cluster",
            "critical_spam_guard": "duplicate cluster cannot multiply CRITICAL alarms"
        },
        "rate_limit_plan": {
            "source_level": "max events per window planned",
            "route_level": "max critical candidates per source/window planned",
            "spam_wave_response": "QUARANTINE source or downgrade route"
        },
        "adversarial_taxonomy": [
            "HONEYPOT",
            "HIDDEN_TAX",
            "FAKE_RENOUNCE",
            "PROXY_TRAP",
            "UPGRADEABLE_RUG",
            "LP_PULL",
            "LIQUIDITY_MIRAGE",
            "FAKE_VOLUME",
            "COORDINATED_SHILL",
            "COORDINATED_FUD",
            "SANDWICH_BAIT",
            "MEV_TRAP",
            "ORACLE_MANIPULATION",
            "BRIDGE_EXPLOIT",
            "WALLET_DRAIN_CAMPAIGN",
            "FAKE_AIRDROP",
            "FAKE_PARTNERSHIP",
            "SOCIAL_ENGINEERING",
            "UNKNOWN_MONITOR"
        ],
        "next_safe_step_contract_dryrun": {
            "name": "HOT_INTELLIGENCE_INGRESS_GATEWAY_CONTRACT_DRYRUN_NOAPI",
            "scope": "synthetic JSON events only; no API, no DB real apply, no runtime change",
            "tests": [
                "synthetic fake exploit rumor",
                "synthetic LP pull with onchain confirmation",
                "synthetic social/onchain conflict",
                "synthetic duplicate wave",
                "synthetic spam wave",
                "synthetic unknown_monitor event"
            ]
        }
    }

    safe_write_json(OUT_JSON, result)
    text = md(result)
    safe_write_text(OUT_MD, text)
    safe_write_text(OUT_REPORT, text)

    print("OK_HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI_WRITTEN")
    print("DECISION=" + result["decision"])
    print("JSON=data/control/hot_intelligence_ingress_gateway_plan_noapi_v1.json")
    print("DOC=docs/HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI.md")
    print("REPORT=reports/LATEST_HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI.md")
    print("NEXT_STEP=" + result["next_step"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
