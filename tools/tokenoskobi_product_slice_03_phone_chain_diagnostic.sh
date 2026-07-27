#!/usr/bin/env bash
set -Eeuo pipefail

STATE_DIR='/var/lib/tokenoskobi-product-slice-03'
EVENTS_FILE="$STATE_DIR/decision_history_v1.jsonl"
PACKETS_DIR="$STATE_DIR/packets"

[[ -f "$EVENTS_FILE" ]] || {
  printf 'BLOCKED=EVENT_LOG_MISSING\n'
  exit 1
}
[[ -d "$PACKETS_DIR" ]] || {
  printf 'BLOCKED=PACKETS_DIRECTORY_MISSING\n'
  exit 1
}

EVENTS_FILE="$EVENTS_FILE" PACKETS_DIR="$PACKETS_DIR" python3 - <<'PY'
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

EVENTS_FILE = Path(os.environ["EVENTS_FILE"])
PACKETS_DIR = Path(os.environ["PACKETS_DIR"])
ZERO_HASH = "0" * 64
TARGET_NOTE = "Telefon kabul testi"
TARGET_ACTION = "WAIT"
TARGET_TOKEN = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def short(value: Any) -> str:
    text = str(value or "")
    return text[:16] if text else "NONE"


def packet_data(packet_id: str) -> dict[str, Any]:
    path = PACKETS_DIR / f"{packet_id}.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    analysis = value["analysis"]
    assert digest(analysis) == packet_id, "PACKET_DIGEST_MISMATCH"
    return value

lines = EVENTS_FILE.read_text(encoding="utf-8").splitlines()
events: list[dict[str, Any]] = []
previous = ZERO_HASH
for expected_seq, line in enumerate(lines, start=1):
    assert line.strip(), f"BLANK_EVENT_LINE:{expected_seq}"
    event = json.loads(line)
    assert event["seq"] == expected_seq, f"BAD_SEQUENCE:{expected_seq}"
    assert event["prev_hash"] == previous, f"BAD_PREV_HASH:{expected_seq}"
    unsigned = dict(event)
    actual_hash = unsigned.pop("event_hash")
    assert digest(unsigned) == actual_hash, f"BAD_EVENT_HASH:{expected_seq}"
    previous = actual_hash
    events.append(event)

print("===== APPEND-ONLY CHAIN =====")
print(f"EVENT_COUNT={len(events)}")
print("HASH_CHAIN_INTEGRITY=VERIFIED")

candidates = []
for event in events:
    if event.get("event_type") != "HUMAN_DECISION_RECORDED":
        continue
    payload = event.get("payload") or {}
    if payload.get("note") == TARGET_NOTE and payload.get("action") == TARGET_ACTION:
        candidates.append(event)

print("\n===== PHONE DECISION CANDIDATES =====")
print(f"PHONE_DECISION_CANDIDATE_COUNT={len(candidates)}")

if not candidates:
    print("DIAGNOSIS=PHONE_DECISION_EVENT_NOT_FOUND")
else:
    for index, decision in enumerate(candidates, start=1):
        packet_id = decision["packet_id"]
        packet = packet_data(packet_id)
        analysis = packet["analysis"]
        token = str(analysis.get("token_address") or "").lower()
        market = analysis.get("market") or {}
        token_data = market.get("token") or {}
        baseline = token_data.get("price_usd")
        actor = (decision.get("payload") or {}).get("actor")

        packet_events = [e for e in events if e.get("packet_id") == packet_id]
        later_decisions = [
            e for e in packet_events
            if e.get("event_type") == "HUMAN_DECISION_RECORDED"
            and e.get("seq", 0) > decision.get("seq", 0)
        ]
        outcomes = [
            e for e in packet_events
            if e.get("event_type") == "OUTCOME_OBSERVED"
        ]
        exact_outcomes = [
            e for e in outcomes
            if (e.get("payload") or {}).get("human_decision_event_hash")
            == decision.get("event_hash")
        ]

        print(f"\nCANDIDATE_{index}_PACKET_ID={packet_id}")
        print(f"CANDIDATE_{index}_TOKEN={token}")
        print(f"CANDIDATE_{index}_BASELINE_PRICE_USD={baseline}")
        print(f"CANDIDATE_{index}_DECISION_SEQ={decision['seq']}")
        print(f"CANDIDATE_{index}_DECISION_HASH={decision['event_hash']}")
        print(f"CANDIDATE_{index}_ACTOR={actor}")
        print(f"CANDIDATE_{index}_PACKET_EVENT_COUNT={len(packet_events)}")
        print(f"CANDIDATE_{index}_LATER_DECISION_COUNT={len(later_decisions)}")
        print(f"CANDIDATE_{index}_OUTCOME_COUNT={len(outcomes)}")
        print(f"CANDIDATE_{index}_EXACT_LINKED_OUTCOME_COUNT={len(exact_outcomes)}")

        if token != TARGET_TOKEN:
            print(f"CANDIDATE_{index}_TOKEN_MATCH=false")
        else:
            print(f"CANDIDATE_{index}_TOKEN_MATCH=true")

        for number, later in enumerate(later_decisions, start=1):
            payload = later.get("payload") or {}
            print(
                f"CANDIDATE_{index}_LATER_DECISION_{number}="
                f"seq:{later.get('seq')},hash:{later.get('event_hash')},"
                f"action:{payload.get('action')},note:{payload.get('note')},"
                f"actor:{payload.get('actor')}"
            )

        for number, outcome in enumerate(outcomes, start=1):
            payload = outcome.get("payload") or {}
            print(
                f"CANDIDATE_{index}_OUTCOME_{number}="
                f"seq:{outcome.get('seq')},hash:{outcome.get('event_hash')},"
                f"linked_decision:{payload.get('human_decision_event_hash')},"
                f"baseline:{payload.get('baseline_price_usd')},"
                f"current:{payload.get('current_price_usd')},"
                f"change_pct:{payload.get('change_pct')},"
                f"classification:{payload.get('classification')},"
                f"actor:{payload.get('actor')}"
            )

        if exact_outcomes:
            print(f"CANDIDATE_{index}_DIAGNOSIS=EXACT_LINK_PRESENT")
        elif outcomes and later_decisions:
            linked_hashes = {
                (e.get("payload") or {}).get("human_decision_event_hash")
                for e in outcomes
            }
            later_hashes = {e.get("event_hash") for e in later_decisions}
            if linked_hashes.intersection(later_hashes):
                print(
                    f"CANDIDATE_{index}_DIAGNOSIS="
                    "OUTCOME_LINKED_TO_LATER_DECISION_ON_SAME_PACKET"
                )
            else:
                print(
                    f"CANDIDATE_{index}_DIAGNOSIS="
                    "OUTCOME_ON_SAME_PACKET_WITH_UNKNOWN_DECISION_LINK"
                )
        elif outcomes:
            print(
                f"CANDIDATE_{index}_DIAGNOSIS="
                "OUTCOME_ON_SAME_PACKET_NOT_LINKED_TO_PHONE_DECISION"
            )
        else:
            print(f"CANDIDATE_{index}_DIAGNOSIS=NO_OUTCOME_ON_PHONE_PACKET")

print("\n===== FINAL =====")
print("DIAGNOSTIC_MODE=READ_ONLY")
print("SERVICE_RESTARTED=false")
print("STATE_MUTATED=false")
print("COMMIT_PUSH=NONE")
print("CANONICAL_UPDATE=NONE")
print("PAPER_TRADE=DISABLED")
print("LIVE_TRADE=DISABLED")
print("REAL_FINANCIAL_AUTHORITY=0")
print("NEXT_SAFE_STEP=INTERPRET_EXACT_EVENT_LINKAGE")
PY
