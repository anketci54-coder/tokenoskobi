
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
REGISTRY = ROOT / "config/news_source_registry_v1.json"
PLAN = ROOT / "config/news_ingress_adapter_readonly_scaffold_plan_v1.json"
GATE = ROOT / "config/news_gate_logic_contract_v1.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def uid(parts):
    raw = "|".join(str(x) for x in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

def contains_any(text, items):
    t = text.lower()
    return any(str(x).lower() in t for x in items)

def normalize(raw):
    observed = raw.get("observed_at_utc") or now()
    source_id = raw["source_id"].strip()
    title = raw["title"].strip()
    topic = raw.get("topic", "").strip()
    token = raw.get("token", "").strip()
    chain = raw.get("chain", "").strip()
    event_uid = uid([source_id, title, topic, token, chain, observed[:16]])
    return {
        "event_uid": event_uid,
        "source_id": source_id,
        "observed_at_utc": observed,
        "topic": topic,
        "title": title,
        "body": raw.get("body", "").strip(),
        "token": token,
        "chain": chain,
        "raw_ref": raw.get("raw_ref", "NOAPI_ADAPTER_SYNTHETIC_FIXTURE"),
        "ingress_mode": "NOAPI_ADAPTER_DRYRUN",
        "normalized": True
    }

def gate_event(event, source, contract):
    text = " ".join([
        event.get("topic", ""),
        event.get("title", ""),
        event.get("body", ""),
        event.get("token", ""),
        event.get("chain", "")
    ]).lower()

    blocked = source.get("blocked_topics", {}).get("disallowed_patterns", [])
    if contains_any(text, blocked):
        return {
            "decision": "DROP_NOISE",
            "severity": "DROP",
            "route": [],
            "reasons": ["blocked_pattern_matched", "NOISE_DROP_GATE"],
            "trade_authority": False
        }

    if source.get("incubation_period") is True:
        return {
            "decision": "WATCH_INCUBATION_ONLY",
            "severity": "WATCH",
            "route": ["Evidence Engine Watch Only"],
            "reasons": ["INCUBATION_GATE", "no_direct_prosecutor"],
            "trade_authority": False
        }

    if source.get("priority") == "QUARANTINE" or source.get("manual_review_required") is True:
        allowed = contains_any(text, source.get("allowed_topics", []))
        return {
            "decision": "QUARANTINE_MANUAL_REVIEW" if allowed else "DROP_QUARANTINE_NO_RELEVANCE",
            "severity": "QUARANTINE" if allowed else "DROP",
            "route": ["Manual Review Queue"] if allowed else [],
            "reasons": ["GENERAL_NEWS_QUARANTINE_GATE", "no_auto_prosecutor"],
            "trade_authority": False
        }

    if source["source_class"] == "security_exploit":
        allowed = contains_any(text, source.get("allowed_topics", []))
        return {
            "decision": "ACCEPT_SECURITY_EARLY_WARNING" if allowed else "DROP_SECURITY_NO_RELEVANCE",
            "severity": source["priority"] if allowed else "DROP",
            "route": contract["routing_policy"]["security_exploit"] if allowed else [],
            "reasons": ["SOURCE_TRUST_GATE", "SECURITY_RELEVANCE_GATE", "EVIDENCE_LINK_GATE"] if allowed else ["security_topic_not_allowed"],
            "trade_authority": False
        }

    if source["source_class"] == "cex_listing_market":
        if event.get("topic") == "new_pair_seen_before_announcement":
            return {
                "decision": "ACCEPT_CRITICAL_CEX_PRE_ANNOUNCEMENT_MARKET_INTEL",
                "severity": "CRITICAL",
                "route": ["Evidence Engine", "Opportunity Memory", "Market Impact Review"],
                "reasons": ["CEX_PAIR_PRE_ANNOUNCEMENT_GATE", "not_confirmed_news", "no_auto_trade"],
                "trade_authority": False
            }
        allowed = contains_any(text, source.get("allowed_topics", []))
        return {
            "decision": "ACCEPT_CEX_MARKET_IMPACT" if allowed else "DROP_CEX_NO_RELEVANCE",
            "severity": source["priority"] if allowed else "DROP",
            "route": contract["routing_policy"]["cex_listing_market"] if allowed else [],
            "reasons": ["SOURCE_TRUST_GATE", "CEX_MARKET_IMPACT_GATE", "TOKEN_MATCH_GATE"] if allowed else ["cex_topic_not_allowed"],
            "trade_authority": False
        }

    if source["source_class"] == "dex_liquidity_market":
        allowed = contains_any(text, source.get("allowed_topics", []))
        return {
            "decision": "ACCEPT_DEX_MARKET_BEHAVIOR" if allowed else "DROP_DEX_NO_RELEVANCE",
            "severity": source["priority"] if allowed else "DROP",
            "route": contract["routing_policy"]["dex_liquidity_market"] if allowed else [],
            "reasons": ["DEX_MARKET_BEHAVIOR_GATE", "LIQUIDITY_RISK_GATE", "TOKEN_MATCH_GATE"] if allowed else ["dex_topic_not_allowed"],
            "trade_authority": False
        }

    if source["source_class"] == "chain_infra":
        allowed = contains_any(text, source.get("allowed_topics", []))
        return {
            "decision": "ACCEPT_CHAIN_INFRA_RISK" if allowed else "DROP_CHAIN_INFRA_NO_RELEVANCE",
            "severity": source["priority"] if allowed else "DROP",
            "route": contract["routing_policy"]["chain_infra"] if allowed else [],
            "reasons": ["SOURCE_TRUST_GATE", "CHAIN_INFRA_RELEVANCE_GATE", "MARKET_IMPACT_GATE"] if allowed else ["chain_topic_not_allowed"],
            "trade_authority": False
        }

    return {
        "decision": "DROP_UNHANDLED_SOURCE_CLASS",
        "severity": "DROP",
        "route": [],
        "reasons": ["unhandled_source_class"],
        "trade_authority": False
    }

def build_envelope(raw, source, adapter_family, contract):
    normalized = normalize(raw)
    gate = gate_event(normalized, source, contract)
    return {
        "schema": "NEWS_INGRESS_ADAPTER_READONLY_ENVELOPE_V1",
        "generated_at_utc": now(),
        "adapter_family": adapter_family,
        "source_id": normalized["source_id"],
        "source_class": source["source_class"],
        "event_uid": normalized["event_uid"],
        "ingress_mode": "NOAPI_ADAPTER_DRYRUN",
        "normalized_event": normalized,
        "gate_decision": gate,
        "routing": {
            "route": gate["route"],
            "severity": gate["severity"],
            "trade_authority": False,
            "paper_trade": False,
            "live_trade": False,
            "db_write": False
        },
        "adapter_authority": {
            "network_call": False,
            "api_call": False,
            "db_write": False,
            "service_change": False,
            "timer_change": False,
            "execution_authority": False
        }
    }

def run_dryrun():
    registry = load(REGISTRY)
    plan = load(PLAN)
    contract = load(GATE)

    source_by_id = {s["source_id"]: s for s in registry["sources"]}
    mapping = {m["source_id"]: m for m in plan["source_adapter_mapping"]}

    fixtures = [
        {
            "case_id": "A01_SECURITY_ACCEPT",
            "source_id": "peckshield_alert",
            "topic": "exploit",
            "title": "Exploit detected on tracked token liquidity pool",
            "body": "wallet drain and liquidity attack evidence",
            "token": "TRACKED_TOKEN_FIXTURE",
            "chain": "BSC",
            "expected": "ACCEPT_SECURITY_EARLY_WARNING"
        },
        {
            "case_id": "A02_CEX_LISTING_ACCEPT",
            "source_id": "binance_announcements",
            "topic": "listing",
            "title": "New listing for tracked token",
            "body": "deposit withdraw enabled network upgrade",
            "token": "TRACKED_TOKEN_FIXTURE",
            "chain": "BSC",
            "expected": "ACCEPT_CEX_MARKET_IMPACT"
        },
        {
            "case_id": "A03_CEX_PAIR_PRE_ANNOUNCEMENT",
            "source_id": "binance_pair_update_stream_watch",
            "topic": "new_pair_seen_before_announcement",
            "title": "New pair seen before official announcement",
            "body": "market symbol enable",
            "token": "TRACKED_TOKEN_FIXTURE",
            "chain": "BSC",
            "expected": "ACCEPT_CRITICAL_CEX_PRE_ANNOUNCEMENT_MARKET_INTEL"
        },
        {
            "case_id": "A04_DEX_BEHAVIOR_ACCEPT",
            "source_id": "dexscreener_market_anomaly",
            "topic": "liquidity_spike",
            "title": "Pair creation and liquidity spike",
            "body": "volume anomaly and price dislocation",
            "token": "TRACKED_TOKEN_FIXTURE",
            "chain": "BSC",
            "expected": "ACCEPT_DEX_MARKET_BEHAVIOR"
        },
        {
            "case_id": "A05_CHAIN_INFRA_ACCEPT",
            "source_id": "bnb_chain_infra",
            "topic": "chain_outage",
            "title": "RPC issue and validator issue",
            "body": "network upgrade and fee spike",
            "token": "",
            "chain": "BSC",
            "expected": "ACCEPT_CHAIN_INFRA_RISK"
        },
        {
            "case_id": "A06_GENERAL_QUARANTINE",
            "source_id": "general_crypto_quarantine_pool",
            "topic": "exchange_collapse",
            "title": "Major exchange collapse",
            "body": "systemic market impact and legal issue",
            "token": "",
            "chain": "",
            "expected": "QUARANTINE_MANUAL_REVIEW"
        },
        {
            "case_id": "A07_INCUBATION_WATCH",
            "source_id": "new_investigator_incubation_pool",
            "topic": "exploit_claim",
            "title": "New investigator wallet cluster claim",
            "body": "unverified exploit claim",
            "token": "TRACKED_TOKEN_FIXTURE",
            "chain": "BSC",
            "expected": "WATCH_INCUBATION_ONLY"
        }
    ]

    envelopes = []
    failures = []
    skipped_live_inputs = []

    for fx in fixtures:
        src = source_by_id[fx["source_id"]]
        mp = mapping[fx["source_id"]]
        if src.get("api_required") or src.get("websocket_supported"):
            skipped_live_inputs.append({
                "source_id": fx["source_id"],
                "api_required": src.get("api_required"),
                "websocket_supported": src.get("websocket_supported"),
                "reason": "live_input_disabled_noapi_dryrun_uses_synthetic_fixture_only"
            })

        envelope = build_envelope(fx, src, mp["adapter_family"], contract)
        envelope["case_id"] = fx["case_id"]
        envelope["expected"] = fx["expected"]
        envelope["ok"] = envelope["gate_decision"]["decision"] == fx["expected"]
        if not envelope["ok"]:
            failures.append({
                "case_id": fx["case_id"],
                "expected": fx["expected"],
                "got": envelope["gate_decision"]["decision"]
            })
        envelopes.append(envelope)

    hard_checks = {
        "all_cases_ok": all(e["ok"] for e in envelopes),
        "all_no_network": all(e["adapter_authority"]["network_call"] is False for e in envelopes),
        "all_no_api": all(e["adapter_authority"]["api_call"] is False for e in envelopes),
        "all_no_db_write": all(e["adapter_authority"]["db_write"] is False and e["routing"]["db_write"] is False for e in envelopes),
        "all_no_trade": all(e["routing"]["trade_authority"] is False and e["routing"]["paper_trade"] is False and e["routing"]["live_trade"] is False for e in envelopes),
        "quarantine_no_prosecutor": all("Prosecutor Engine" not in e["routing"]["route"] for e in envelopes if e["source_class"] == "general_crypto_quarantine"),
        "incubation_no_prosecutor": all("Prosecutor Engine" not in e["routing"]["route"] for e in envelopes if e["gate_decision"]["decision"] == "WATCH_INCUBATION_ONLY"),
        "api_sources_not_live_enabled": all(m["adapter_runtime_enabled_now"] is False for m in mapping.values() if m["api_required"] is True),
        "websocket_sources_not_live_enabled": all(m["adapter_runtime_enabled_now"] is False for m in mapping.values() if m["websocket_supported"] is True)
    }

    for k, v in hard_checks.items():
        if v is not True:
            failures.append({"hard_check_failed": k})

    return {
        "stage": "NEWS_INGRESS_ADAPTER_READONLY_SCAFFOLD_DRYRUN_NOAPI",
        "generated_at_utc": now(),
        "case_count": len(fixtures),
        "ok_count": sum(1 for e in envelopes if e["ok"]),
        "fail_count": len(failures),
        "skipped_live_inputs": skipped_live_inputs,
        "hard_checks": hard_checks,
        "envelopes": envelopes,
        "failures": failures,
        "decision": "OK_INGRESS_ADAPTER_READONLY_SCAFFOLD_DRYRUN" if not failures else "FAIL_INGRESS_ADAPTER_READONLY_SCAFFOLD_DRYRUN"
    }

if __name__ == "__main__":
    print(json.dumps(run_dryrun(), ensure_ascii=False, indent=2, sort_keys=True))
