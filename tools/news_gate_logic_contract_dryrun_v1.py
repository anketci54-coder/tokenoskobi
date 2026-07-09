
from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path("/root/tokenoskobi_clean_v1")
REGISTRY = ROOT / "config/news_source_registry_v1.json"
CONTRACT = ROOT / "config/news_gate_logic_contract_v1.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def contains_any(text, items):
    t = text.lower()
    return any(str(x).lower() in t for x in items)

def source_map(registry):
    return {s["source_id"]: s for s in registry["sources"]}

def evaluate_event(event, registry, contract):
    sources = source_map(registry)
    src = sources.get(event["source_id"])
    if not src:
        return {
            "event_id": event["event_id"],
            "decision": "DROP_UNKNOWN_SOURCE",
            "severity": "DROP",
            "route": [],
            "reasons": ["source_not_in_registry"],
            "trade_authority": False
        }

    text = " ".join([
        event.get("topic", ""),
        event.get("title", ""),
        event.get("body", ""),
        event.get("token", ""),
        event.get("chain", "")
    ]).lower()

    reasons = []
    route = []
    trade_authority = False

    blocked = src.get("blocked_topics", {}).get("disallowed_patterns", [])
    if contains_any(text, blocked):
        return {
            "event_id": event["event_id"],
            "source_id": src["source_id"],
            "source_class": src["source_class"],
            "decision": "DROP_NOISE",
            "severity": "DROP",
            "route": [],
            "reasons": ["blocked_pattern_matched", "NOISE_DROP_GATE"],
            "trade_authority": trade_authority
        }

    if src.get("incubation_period") is True:
        return {
            "event_id": event["event_id"],
            "source_id": src["source_id"],
            "source_class": src["source_class"],
            "decision": "WATCH_INCUBATION_ONLY",
            "severity": "WATCH",
            "route": ["Evidence Engine Watch Only"],
            "reasons": ["INCUBATION_GATE", "no_direct_prosecutor"],
            "trade_authority": trade_authority
        }

    if src.get("priority") == "QUARANTINE" or src.get("manual_review_required") is True:
        allowed = contains_any(text, src.get("allowed_topics", []))
        return {
            "event_id": event["event_id"],
            "source_id": src["source_id"],
            "source_class": src["source_class"],
            "decision": "QUARANTINE_MANUAL_REVIEW" if allowed else "DROP_QUARANTINE_NO_RELEVANCE",
            "severity": "QUARANTINE" if allowed else "DROP",
            "route": ["Manual Review Queue"] if allowed else [],
            "reasons": ["GENERAL_NEWS_QUARANTINE_GATE", "no_auto_prosecutor"],
            "trade_authority": trade_authority
        }

    if src["source_class"] == "security_exploit":
        allowed = contains_any(text, src.get("allowed_topics", []))
        return {
            "event_id": event["event_id"],
            "source_id": src["source_id"],
            "source_class": src["source_class"],
            "decision": "ACCEPT_SECURITY_EARLY_WARNING" if allowed else "DROP_SECURITY_NO_RELEVANCE",
            "severity": src["priority"] if allowed else "DROP",
            "route": contract["routing_policy"]["security_exploit"] if allowed else [],
            "reasons": ["SOURCE_TRUST_GATE", "SECURITY_RELEVANCE_GATE", "EVIDENCE_LINK_GATE"] if allowed else ["security_topic_not_allowed"],
            "trade_authority": trade_authority
        }

    if src["source_class"] == "cex_listing_market":
        if event.get("topic") == "new_pair_seen_before_announcement":
            return {
                "event_id": event["event_id"],
                "source_id": src["source_id"],
                "source_class": src["source_class"],
                "decision": "ACCEPT_CRITICAL_CEX_PRE_ANNOUNCEMENT_MARKET_INTEL",
                "severity": "CRITICAL",
                "route": ["Evidence Engine", "Opportunity Memory", "Market Impact Review"],
                "reasons": ["CEX_PAIR_PRE_ANNOUNCEMENT_GATE", "not_confirmed_news", "no_auto_trade"],
                "trade_authority": trade_authority
            }
        allowed = contains_any(text, src.get("allowed_topics", []))
        return {
            "event_id": event["event_id"],
            "source_id": src["source_id"],
            "source_class": src["source_class"],
            "decision": "ACCEPT_CEX_MARKET_IMPACT" if allowed else "DROP_CEX_NO_RELEVANCE",
            "severity": src["priority"] if allowed else "DROP",
            "route": contract["routing_policy"]["cex_listing_market"] if allowed else [],
            "reasons": ["SOURCE_TRUST_GATE", "CEX_MARKET_IMPACT_GATE", "TOKEN_MATCH_GATE"] if allowed else ["cex_topic_not_allowed"],
            "trade_authority": trade_authority
        }

    if src["source_class"] == "dex_liquidity_market":
        allowed = contains_any(text, src.get("allowed_topics", []))
        return {
            "event_id": event["event_id"],
            "source_id": src["source_id"],
            "source_class": src["source_class"],
            "decision": "ACCEPT_DEX_MARKET_BEHAVIOR" if allowed else "DROP_DEX_NO_RELEVANCE",
            "severity": src["priority"] if allowed else "DROP",
            "route": contract["routing_policy"]["dex_liquidity_market"] if allowed else [],
            "reasons": ["DEX_MARKET_BEHAVIOR_GATE", "LIQUIDITY_RISK_GATE", "TOKEN_MATCH_GATE"] if allowed else ["dex_topic_not_allowed"],
            "trade_authority": trade_authority
        }

    if src["source_class"] == "chain_infra":
        allowed = contains_any(text, src.get("allowed_topics", []))
        return {
            "event_id": event["event_id"],
            "source_id": src["source_id"],
            "source_class": src["source_class"],
            "decision": "ACCEPT_CHAIN_INFRA_RISK" if allowed else "DROP_CHAIN_INFRA_NO_RELEVANCE",
            "severity": src["priority"] if allowed else "DROP",
            "route": contract["routing_policy"]["chain_infra"] if allowed else [],
            "reasons": ["SOURCE_TRUST_GATE", "CHAIN_INFRA_RELEVANCE_GATE", "MARKET_IMPACT_GATE"] if allowed else ["chain_topic_not_allowed"],
            "trade_authority": trade_authority
        }

    return {
        "event_id": event["event_id"],
        "source_id": src["source_id"],
        "source_class": src["source_class"],
        "decision": "DROP_UNHANDLED_CLASS",
        "severity": "DROP",
        "route": [],
        "reasons": ["unhandled_source_class"],
        "trade_authority": trade_authority
    }

def run_dryrun():
    registry = load_json(REGISTRY)
    contract = load_json(CONTRACT)

    cases = [
        {
            "event_id": "T01_SECURITY_EXPLOIT_ACCEPT",
            "source_id": "peckshield_alert",
            "topic": "exploit",
            "title": "Exploit detected on tracked token liquidity pool",
            "body": "wallet drain and liquidity attack evidence",
            "expected": "ACCEPT_SECURITY_EARLY_WARNING"
        },
        {
            "event_id": "T02_SECURITY_NOISE_DROP",
            "source_id": "blocksec_alert",
            "topic": "price_prediction",
            "title": "price prediction sponsored giveaway",
            "body": "giveaway",
            "expected": "DROP_NOISE"
        },
        {
            "event_id": "T03_INCUBATION_WATCH",
            "source_id": "new_investigator_incubation_pool",
            "topic": "exploit_claim",
            "title": "new wallet cluster claim",
            "body": "unverified exploit claim",
            "expected": "WATCH_INCUBATION_ONLY"
        },
        {
            "event_id": "T04_GENERAL_QUARANTINE_ACCEPT",
            "source_id": "general_crypto_quarantine_pool",
            "topic": "exchange_collapse",
            "title": "major exchange collapse systemic risk",
            "body": "market impact and legal issue",
            "expected": "QUARANTINE_MANUAL_REVIEW"
        },
        {
            "event_id": "T05_GENERAL_NOISE_DROP",
            "source_id": "general_crypto_quarantine_pool",
            "topic": "minor_partnership",
            "title": "minor partnership sponsored content",
            "body": "airdrop shill",
            "expected": "DROP_NOISE"
        },
        {
            "event_id": "T06_CEX_PAIR_PRE_ANNOUNCEMENT",
            "source_id": "binance_pair_update_stream_watch",
            "topic": "new_pair_seen_before_announcement",
            "title": "new trading pair appears before announcement",
            "body": "market symbol enable",
            "expected": "ACCEPT_CRITICAL_CEX_PRE_ANNOUNCEMENT_MARKET_INTEL"
        },
        {
            "event_id": "T07_CEX_LISTING_ACCEPT",
            "source_id": "binance_announcements",
            "topic": "listing",
            "title": "new listing for tracked token",
            "body": "deposit withdraw enabled",
            "expected": "ACCEPT_CEX_MARKET_IMPACT"
        },
        {
            "event_id": "T08_DEX_ANOMALY_ACCEPT",
            "source_id": "dexscreener_market_anomaly",
            "topic": "liquidity_spike",
            "title": "liquidity spike and pair creation",
            "body": "volume anomaly",
            "expected": "ACCEPT_DEX_MARKET_BEHAVIOR"
        },
        {
            "event_id": "T09_CHAIN_INFRA_ACCEPT",
            "source_id": "bnb_chain_infra",
            "topic": "chain_outage",
            "title": "rpc issue and validator issue",
            "body": "network upgrade fee spike",
            "expected": "ACCEPT_CHAIN_INFRA_RISK"
        },
        {
            "event_id": "T10_UNKNOWN_SOURCE_DROP",
            "source_id": "unknown_blog",
            "topic": "exploit",
            "title": "unknown source claim",
            "body": "wallet drain",
            "expected": "DROP_UNKNOWN_SOURCE"
        }
    ]

    results = []
    failures = []
    for case in cases:
        got = evaluate_event(case, registry, contract)
        got["expected"] = case["expected"]
        got["ok"] = got["decision"] == case["expected"] and got["trade_authority"] is False
        if not got["ok"]:
            failures.append({"event_id": case["event_id"], "expected": case["expected"], "got": got["decision"]})
        results.append(got)

    return {
        "stage": "NEWS_GATE_LOGIC_CONTRACT_DRYRUN_NOAPI",
        "generated_at_utc": now(),
        "registry": str(REGISTRY),
        "contract": str(CONTRACT),
        "case_count": len(cases),
        "ok_count": sum(1 for r in results if r["ok"]),
        "fail_count": len(failures),
        "results": results,
        "failures": failures,
        "hard_assertions": {
            "no_trade_authority_in_all_cases": all(r["trade_authority"] is False for r in results),
            "quarantine_not_routed_to_prosecutor": all("Prosecutor Engine" not in r["route"] for r in results if r.get("source_class") == "general_crypto_quarantine"),
            "incubation_not_routed_to_prosecutor": all("Prosecutor Engine" not in r["route"] for r in results if r.get("source_class") == "security_exploit" and r["decision"] == "WATCH_INCUBATION_ONLY"),
            "critical_cex_pair_is_not_trade": all(r["trade_authority"] is False for r in results if r["decision"] == "ACCEPT_CRITICAL_CEX_PRE_ANNOUNCEMENT_MARKET_INTEL")
        }
    }

if __name__ == "__main__":
    print(json.dumps(run_dryrun(), ensure_ascii=False, indent=2, sort_keys=True))
