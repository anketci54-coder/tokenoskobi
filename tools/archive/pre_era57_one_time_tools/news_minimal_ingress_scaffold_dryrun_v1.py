
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib

ROOT = Path("/root/tokenoskobi_clean_v1")
REGISTRY = ROOT / "config/news_source_registry_v1.json"
GATE_CONTRACT = ROOT / "config/news_gate_logic_contract_v1.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def stable_uid(parts):
    raw = "|".join(str(x) for x in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

def contains_any(text, items):
    t = text.lower()
    return any(str(x).lower() in t for x in items)

def normalize_raw_event(raw):
    source_id = raw["source_id"].strip()
    title = raw["title"].strip()
    body = raw.get("body", "").strip()
    topic = raw.get("topic", "").strip()
    token = raw.get("token", "").strip()
    chain = raw.get("chain", "").strip()
    observed_at = raw.get("observed_at_utc") or now()
    uid = stable_uid([source_id, title, topic, token, chain, observed_at[:16]])
    return {
        "event_uid": uid,
        "source_id": source_id,
        "observed_at_utc": observed_at,
        "topic": topic,
        "title": title,
        "body": body,
        "token": token,
        "chain": chain,
        "raw_ref": raw.get("raw_ref", "NOAPI_SYNTHETIC_FIXTURE"),
        "ingress_mode": "NOAPI_DRYRUN",
        "normalized": True
    }

def evaluate_event(event, registry, contract):
    source_by_id = {s["source_id"]: s for s in registry["sources"]}
    src = source_by_id.get(event["source_id"])
    if not src:
        return {
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

    blocked = src.get("blocked_topics", {}).get("disallowed_patterns", [])
    if contains_any(text, blocked):
        return {
            "decision": "DROP_NOISE",
            "severity": "DROP",
            "route": [],
            "reasons": ["blocked_pattern_matched", "NOISE_DROP_GATE"],
            "source_class": src["source_class"],
            "priority": src["priority"],
            "trust_score": src["trust_score"],
            "trade_authority": False
        }

    if src.get("incubation_period") is True:
        return {
            "decision": "WATCH_INCUBATION_ONLY",
            "severity": "WATCH",
            "route": ["Evidence Engine Watch Only"],
            "reasons": ["INCUBATION_GATE", "no_direct_prosecutor"],
            "source_class": src["source_class"],
            "priority": src["priority"],
            "trust_score": src["trust_score"],
            "trade_authority": False
        }

    if src.get("priority") == "QUARANTINE" or src.get("manual_review_required") is True:
        allowed = contains_any(text, src.get("allowed_topics", []))
        return {
            "decision": "QUARANTINE_MANUAL_REVIEW" if allowed else "DROP_QUARANTINE_NO_RELEVANCE",
            "severity": "QUARANTINE" if allowed else "DROP",
            "route": ["Manual Review Queue"] if allowed else [],
            "reasons": ["GENERAL_NEWS_QUARANTINE_GATE", "no_auto_prosecutor"],
            "source_class": src["source_class"],
            "priority": src["priority"],
            "trust_score": src["trust_score"],
            "trade_authority": False
        }

    if src["source_class"] == "security_exploit":
        allowed = contains_any(text, src.get("allowed_topics", []))
        return {
            "decision": "ACCEPT_SECURITY_EARLY_WARNING" if allowed else "DROP_SECURITY_NO_RELEVANCE",
            "severity": src["priority"] if allowed else "DROP",
            "route": contract["routing_policy"]["security_exploit"] if allowed else [],
            "reasons": ["SOURCE_TRUST_GATE", "SECURITY_RELEVANCE_GATE", "EVIDENCE_LINK_GATE"] if allowed else ["security_topic_not_allowed"],
            "source_class": src["source_class"],
            "priority": src["priority"],
            "trust_score": src["trust_score"],
            "trade_authority": False
        }

    if src["source_class"] == "cex_listing_market":
        if event.get("topic") == "new_pair_seen_before_announcement":
            return {
                "decision": "ACCEPT_CRITICAL_CEX_PRE_ANNOUNCEMENT_MARKET_INTEL",
                "severity": "CRITICAL",
                "route": ["Evidence Engine", "Opportunity Memory", "Market Impact Review"],
                "reasons": ["CEX_PAIR_PRE_ANNOUNCEMENT_GATE", "not_confirmed_news", "no_auto_trade"],
                "source_class": src["source_class"],
                "priority": src["priority"],
                "trust_score": src["trust_score"],
                "trade_authority": False
            }

    return {
        "decision": "DROP_UNHANDLED_MINIMAL_SCAFFOLD_CLASS",
        "severity": "DROP",
        "route": [],
        "reasons": ["minimal_scaffold_class_not_enabled"],
        "source_class": src["source_class"],
        "priority": src["priority"],
        "trust_score": src["trust_score"],
        "trade_authority": False
    }

def build_envelope(raw_event):
    registry = load_json(REGISTRY)
    contract = load_json(GATE_CONTRACT)

    normalized = normalize_raw_event(raw_event)
    gate = evaluate_event(normalized, registry, contract)

    return {
        "schema": "NEWS_MINIMAL_INGRESS_ENVELOPE_V1",
        "generated_at_utc": now(),
        "event_uid": normalized["event_uid"],
        "source_id": normalized["source_id"],
        "ingress_mode": "NOAPI_DRYRUN",
        "normalized_event": normalized,
        "gate_decision": gate,
        "routing": {
            "route": gate.get("route", []),
            "severity": gate.get("severity", "DROP"),
            "trade_authority": False,
            "paper_trade": False,
            "live_trade": False,
            "db_write": False
        }
    }

def run_dryrun():
    raw_event = {
        "source_id": "peckshield_alert",
        "topic": "exploit",
        "title": "Exploit detected on tracked token liquidity pool",
        "body": "wallet drain, liquidity attack and suspicious contract interaction evidence",
        "token": "TRACKED_TOKEN_FIXTURE",
        "chain": "BSC",
        "raw_ref": "NOAPI_SYNTHETIC_SINGLE_EVENT",
        "observed_at_utc": "2026-07-09T13:30:00+00:00"
    }

    envelope = build_envelope(raw_event)
    checks = {
        "normalized": envelope["normalized_event"]["normalized"] is True,
        "event_uid_present": bool(envelope["event_uid"]),
        "decision_accept_security": envelope["gate_decision"]["decision"] == "ACCEPT_SECURITY_EARLY_WARNING",
        "route_evidence": "Evidence Engine" in envelope["routing"]["route"],
        "route_unknown_anomaly": "Unknown Anomaly Engine" in envelope["routing"]["route"],
        "route_prosecutor": "Prosecutor Engine" in envelope["routing"]["route"],
        "no_trade_authority": envelope["routing"]["trade_authority"] is False,
        "no_db_write": envelope["routing"]["db_write"] is False,
        "no_live_trade": envelope["routing"]["live_trade"] is False,
        "no_paper_trade": envelope["routing"]["paper_trade"] is False
    }
    failures = [k for k, v in checks.items() if v is not True]

    return {
        "stage": "NEWS_MINIMAL_INGRESS_SCAFFOLD_DRYRUN_NOAPI",
        "generated_at_utc": now(),
        "event_count": 1,
        "envelope": envelope,
        "checks": checks,
        "failures": failures,
        "decision": "OK_MINIMAL_INGRESS_ENVELOPE" if not failures else "FAIL_MINIMAL_INGRESS_ENVELOPE"
    }

if __name__ == "__main__":
    print(json.dumps(run_dryrun(), ensure_ascii=False, indent=2, sort_keys=True))
