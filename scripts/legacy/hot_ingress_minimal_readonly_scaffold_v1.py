from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
OUT = ROOT / "data/control/era54c_hot_ingress_minimal_readonly_scaffold_dryrun_noapi_v1.json"

FORBIDDEN_IMPORT_PREFIXES = (
    "runtime",
    "lab",
    "app.runtime",
    "tokenoskobi_runtime",
)

TRUST_MINIMUM = 0.50
EVIDENCE_MAX_SKEW_SECONDS = 3600


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_dt(value: str) -> datetime:
    value = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def event_time_bucket(event_time: datetime) -> str:
    return event_time.replace(minute=0, second=0, microsecond=0).isoformat()


def static_import_block_check() -> dict[str, Any]:
    text = SELF.read_text(encoding="utf-8")
    tree = ast.parse(text)
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                name = item.name
                if any(name == p or name.startswith(p + ".") for p in FORBIDDEN_IMPORT_PREFIXES):
                    violations.append(name)
        elif isinstance(node, ast.ImportFrom):
            name = node.module or ""
            if any(name == p or name.startswith(p + ".") for p in FORBIDDEN_IMPORT_PREFIXES):
                violations.append(name)

    return {
        "ok": len(violations) == 0,
        "violations": violations,
        "checked_file": str(SELF.relative_to(ROOT)),
        "forbidden_import_prefixes": list(FORBIDDEN_IMPORT_PREFIXES),
    }


def build_synthetic_events() -> list[dict[str, Any]]:
    now = utc_now()
    base_time = now - timedelta(seconds=90)
    evidence_time = base_time + timedelta(seconds=10)
    future_time = now + timedelta(days=3650)

    title = "BSC bridge exploit detected"
    body = "Exploit report says suspicious bridge drain activity was observed."

    return [
        {
            "name": "happy_path_exploit_news",
            "source_uid": "hot_source_alpha",
            "trust_score": 0.91,
            "topic": "exploit",
            "title": title,
            "body": body,
            "event_time": base_time.isoformat(),
            "evidence_timestamp": evidence_time.isoformat(),
            "expected_route": "ADMIT",
        },
        {
            "name": "duplicate_same_source_hash",
            "source_uid": "hot_source_alpha",
            "trust_score": 0.91,
            "topic": "exploit",
            "title": title,
            "body": body,
            "event_time": base_time.isoformat(),
            "evidence_timestamp": evidence_time.isoformat(),
            "expected_route": "DUPLICATE_DROP",
        },
        {
            "name": "poison_pill_impossible_timestamp",
            "source_uid": "hot_source_alpha",
            "trust_score": 0.99,
            "topic": "exploit",
            "title": "Impossible future exploit event",
            "body": "This event is intentionally impossible and toxic.",
            "event_time": future_time.isoformat(),
            "evidence_timestamp": future_time.isoformat(),
            "expected_route": "QUARANTINE",
        },
        {
            "name": "noisy_low_trust_source",
            "source_uid": "hot_source_noise",
            "trust_score": 0.20,
            "topic": "rumor",
            "title": "Unverified token panic rumor",
            "body": "Low trust source claims vague market panic without evidence.",
            "event_time": base_time.isoformat(),
            "evidence_timestamp": evidence_time.isoformat(),
            "expected_route": "DROP",
        },
        {
            "name": "conflicting_topic_same_hash",
            "source_uid": "hot_source_beta",
            "trust_score": 0.88,
            "topic": "whale_transfer",
            "title": title,
            "body": body,
            "event_time": base_time.isoformat(),
            "evidence_timestamp": evidence_time.isoformat(),
            "expected_route": "QUARANTINE",
        },
    ]


def compute_identity(event: dict[str, Any]) -> dict[str, str]:
    et = parse_dt(event["event_time"])
    normalized_title = normalize_text(event["title"])
    normalized_body = normalize_text(event["body"])
    bucket = event_time_bucket(et)

    event_hash = sha256_text("|".join([normalized_title, normalized_body, bucket]))
    event_uid = sha256_text("|".join([event["source_uid"], event_hash]))
    dedupe_key = "|".join([event["source_uid"], event_hash])

    return {
        "event_hash": event_hash,
        "event_uid": event_uid,
        "dedupe_key": dedupe_key,
        "event_time_bucket": bucket,
    }


def evidence_freshness_stub(event: dict[str, Any]) -> dict[str, Any]:
    event_dt = parse_dt(event["event_time"])
    evidence_dt = parse_dt(event["evidence_timestamp"])
    skew = abs((evidence_dt - event_dt).total_seconds())
    return {
        "ok": skew <= EVIDENCE_MAX_SKEW_SECONDS,
        "skew_seconds": int(skew),
        "max_allowed_seconds": EVIDENCE_MAX_SKEW_SECONDS,
    }


def route_event(
    event: dict[str, Any],
    seen_dedupe: set[str],
    seen_hash_topic: dict[str, str],
    now: datetime,
) -> dict[str, Any]:
    identity = compute_identity(event)
    event_dt = parse_dt(event["event_time"])
    freshness = evidence_freshness_stub(event)

    route = "ADMIT"
    reasons: list[str] = []

    if event_dt > now + timedelta(minutes=5):
        route = "QUARANTINE"
        reasons.append("IMPOSSIBLE_FUTURE_TIMESTAMP")
    elif event["trust_score"] < TRUST_MINIMUM:
        route = "DROP"
        reasons.append("LOW_TRUST_SOURCE")
    elif not freshness["ok"]:
        route = "QUARANTINE"
        reasons.append("EVIDENCE_STALE_OR_SKEWED")
    elif identity["dedupe_key"] in seen_dedupe:
        route = "DUPLICATE_DROP"
        reasons.append("DUPLICATE_SOURCE_HASH")
    elif identity["event_hash"] in seen_hash_topic and seen_hash_topic[identity["event_hash"]] != event["topic"]:
        route = "QUARANTINE"
        reasons.append("CONFLICTING_TOPIC_FOR_SAME_HASH")

    if route == "ADMIT":
        reasons.append("ADMISSION_GATE_ACCEPTED")

    if route == "ADMIT":
        seen_dedupe.add(identity["dedupe_key"])
        seen_hash_topic[identity["event_hash"]] = event["topic"]
    elif route == "DUPLICATE_DROP":
        pass
    elif route == "QUARANTINE":
        seen_dedupe.add(identity["dedupe_key"])
        seen_hash_topic.setdefault(identity["event_hash"], event["topic"])

    return {
        "name": event["name"],
        "expected_route": event["expected_route"],
        "actual_route": route,
        "route_ok": route == event["expected_route"],
        "reasons": reasons,
        "event_uid": identity["event_uid"],
        "event_hash": identity["event_hash"],
        "dedupe_key": identity["dedupe_key"],
        "event_time_bucket": identity["event_time_bucket"],
        "evidence_freshness_stub": freshness,
        "prosecutor_candidate_gate_stub": {
            "enabled": False,
            "runtime_handoff": False,
            "alarm": False,
            "note": "Admission is gatekeeper. Prosecutor is judge stub only in ERA54C.",
        },
    }


def main() -> int:
    now = utc_now()
    import_check = static_import_block_check()
    events = build_synthetic_events()
    seen_dedupe: set[str] = set()
    seen_hash_topic: dict[str, str] = {}

    results = [
        route_event(event, seen_dedupe, seen_hash_topic, now)
        for event in events
    ]

    fail_count = 0
    warn_count = 0

    if not import_check["ok"]:
        fail_count += 1

    route_failures = [r for r in results if not r["route_ok"]]
    fail_count += len(route_failures)

    obj = {
        "stage": "ERA54C_STANDALONE_SCAFFOLD_DRYRUN_NOAPI",
        "generated_at_utc": now.isoformat(),
        "decision": "OK_ERA54C_DRYRUN_PASSED" if fail_count == 0 else "FAIL_ERA54C_DRYRUN",
        "tool": str(SELF.relative_to(ROOT)),
        "boundary": {
            "noapi": True,
            "db_change": False,
            "runtime_change": False,
            "runtime_import": False,
            "service_change": False,
            "panel_change": False,
            "wallet_or_trade": False,
            "new_top_level_directory": False,
            "external_source_adapter": False,
        },
        "static_import_block_check": import_check,
        "motto_opportunity_cost_gate": {
            "speed": "manual stdout dryrun only",
            "power": "happy duplicate poison noisy conflicting cases covered",
            "security": "runtime import static block and noapi boundary",
            "economy": "one tool one control json no docs bloat",
            "formula_source": "ERA24F_EDE_OPPORTUNITY_COST_BASELINE",
        },
        "uid_contract": {
            "event_uid": "sha256(source_uid + event_hash)",
            "event_hash": "sha256(normalized_title + normalized_body + event_time_bucket)",
            "dedupe_key": "source_uid + event_hash",
        },
        "results": results,
        "summary": {
            "event_count": len(events),
            "route_failures": len(route_failures),
            "fail_count": fail_count,
            "warn_count": warn_count,
        },
        "next_step": "ERA54D_STATIC_AND_BOUNDARY_AUDIT_NOAPI",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("ERA54C_DECISION=" + obj["decision"])
    print("ERA54C_OUT=" + str(OUT.relative_to(ROOT)))
    print("ERA54C_FAIL_COUNT=" + str(fail_count))
    print("ERA54C_WARN_COUNT=" + str(warn_count))
    for item in results:
        print(item["name"] + "=" + item["actual_route"] + "/" + item["expected_route"])

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
