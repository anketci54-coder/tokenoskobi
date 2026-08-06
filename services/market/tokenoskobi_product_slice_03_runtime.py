#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import importlib.util
import os
import re
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

ROOT = Path(os.getenv("TOKENOSKOBI_ROOT", "/root/tokenoskobi_clean_v1"))
CORE_PATH = Path(
    os.getenv(
        "TOKENOSKOBI_SLICE03_CORE_PATH",
        ROOT / "tools/tokenoskobi_product_slice_03_server.py",
    )
)
SPEC = importlib.util.spec_from_file_location(
    "tokenoskobi_product_slice_03_core",
    CORE_PATH,
)
if not SPEC or not SPEC.loader:
    raise RuntimeError("PRODUCT_SLICE_03_CORE_IMPORT_FAILED")
CORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CORE)

ACTOR_ID = re.compile(r"^[A-Za-z0-9_.@-]{1,128}$")
VERIFY_UNLOCKED = getattr(
    CORE,
    "_verify_event_chain_unlocked",
    CORE.verify_event_chain,
)
PayloadFactory = Callable[[list[dict[str, Any]]], dict[str, Any]]


def normalize_actor(value: Any) -> str:
    actor = str(value or "LOCAL_LOOPBACK_USER").strip()
    if not ACTOR_ID.fullmatch(actor):
        raise CORE.ValidationError("INVALID_AUTHENTICATED_USER")
    return actor


def verify_event_chain_locked() -> list[dict[str, Any]]:
    CORE.ensure_state()
    with CORE.LOCK_FILE.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_SH)
        try:
            return VERIFY_UNLOCKED()
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def append_event_from_factory(
    event_type: str,
    packet_id: str,
    payload_factory: PayloadFactory,
) -> dict[str, Any]:
    if event_type not in CORE.EVENT_TYPES:
        raise CORE.ValidationError("INVALID_EVENT_TYPE")
    packet_id = CORE.validate_packet_id(packet_id)
    if not callable(payload_factory):
        raise CORE.ValidationError("EVENT_PAYLOAD_FACTORY_REQUIRED")

    CORE.ensure_state()
    with CORE.STATE_THREAD_LOCK:
        with CORE.LOCK_FILE.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                events = VERIFY_UNLOCKED()
                payload = payload_factory(events)
                if not isinstance(payload, dict):
                    raise CORE.ValidationError("EVENT_PAYLOAD_NOT_OBJECT")
                event = {
                    "schema": "tokenoskobi.product_slice_03.history_event.v1",
                    "seq": len(events) + 1,
                    "event_id": CORE.secrets.token_hex(16),
                    "event_type": event_type,
                    "occurred_at_utc": CORE.utc_now(),
                    "packet_id": packet_id,
                    "payload": payload,
                    "prev_hash": (
                        events[-1]["event_hash"]
                        if events
                        else CORE.ZERO_HASH
                    ),
                }
                event["event_hash"] = CORE.digest(event)
                descriptor = os.open(
                    CORE.EVENTS_FILE,
                    os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                    0o600,
                )
                with os.fdopen(descriptor, "ab", closefd=True) as handle:
                    handle.write(CORE.canonical_bytes(event) + b"\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                return event
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def append_event_locked(
    event_type: str,
    packet_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CORE.ValidationError("EVENT_PAYLOAD_NOT_OBJECT")
    return append_event_from_factory(
        event_type,
        packet_id,
        lambda _events: payload,
    )


def record_human_decision(
    packet_id: str,
    action: Any,
    note: Any = None,
    actor: Any = None,
) -> dict[str, Any]:
    packet_id = CORE.validate_packet_id(packet_id)
    action_value = str(action or "").upper()
    if action_value not in CORE.HUMAN_ACTIONS:
        raise CORE.ValidationError("INVALID_HUMAN_ACTION")
    envelope = CORE.load_packet(packet_id)
    actor_value = normalize_actor(actor)
    note_value = CORE.normalize_note(note)
    system_decision = (
        (envelope["analysis"].get("decision") or {}).get("decision")
    )

    def build(events: list[dict[str, Any]]) -> dict[str, Any]:
        if not CORE.latest_event_for(
            events,
            packet_id,
            "ANALYSIS_CREATED",
        ):
            raise CORE.HistoryCorruption("ANALYSIS_EVENT_MISSING")
        previous = CORE.latest_event_for(
            events,
            packet_id,
            "HUMAN_DECISION_RECORDED",
        )
        return {
            "action": action_value,
            "actor": actor_value,
            "note": note_value,
            "previous_decision_event_hash": (
                previous["event_hash"] if previous else None
            ),
            "system_decision": system_decision,
            "authority": "HUMAN_RECORD_ONLY_NO_EXECUTION",
        }

    event = append_event_from_factory(
        "HUMAN_DECISION_RECORDED",
        packet_id,
        build,
    )
    return {
        "ok": True,
        "packet_id": packet_id,
        "event": event,
        "authority": "NO_TRADE_EXECUTION",
    }


def observe_outcome(packet_id: str, actor: Any = None) -> dict[str, Any]:
    packet_id = CORE.validate_packet_id(packet_id)
    envelope = CORE.load_packet(packet_id)
    analysis = envelope["analysis"]
    token = str(analysis.get("token_address") or "").lower()
    if not CORE.ADDR.fullmatch(token):
        raise CORE.HistoryCorruption("PACKET_TOKEN_INVALID")

    baseline = CORE.finite_number(
        ((analysis.get("market") or {}).get("token") or {}).get(
            "price_usd"
        )
    )
    if baseline is None or baseline <= 0:
        raise CORE.ValidationError("BASELINE_PRICE_UNAVAILABLE")

    current_market = CORE.SLICE02.market(token)
    selected = current_market.get("selected_pool") or {}
    current = CORE.finite_number(
        (current_market.get("token") or {}).get("price_usd")
    )
    pool_current = CORE.finite_number(selected.get("price_usd"))
    orientation = bool(
        current_market.get("target_orientation_verified")
        and selected.get("orientation_verified")
        and selected.get("target_token_address") == token
    )
    if (
        current is None
        or current <= 0
        or pool_current is None
        or not orientation
    ):
        raise CORE.ValidationError("CURRENT_TARGET_PRICE_UNAVAILABLE")
    ratio = current / pool_current
    if not 0.75 <= ratio <= 1.25:
        raise CORE.ValidationError("CURRENT_TARGET_PRICE_MISMATCH")

    generated = CORE.parse_utc(str(analysis.get("generated_at_utc")))
    observed_at = CORE.datetime.now(CORE.timezone.utc)
    change_pct = (current / baseline - 1) * 100
    actor_value = normalize_actor(actor)

    def build(events: list[dict[str, Any]]) -> dict[str, Any]:
        human_decision = CORE.latest_event_for(
            events,
            packet_id,
            "HUMAN_DECISION_RECORDED",
        )
        if not human_decision:
            raise CORE.ValidationError(
                "HUMAN_DECISION_REQUIRED_BEFORE_OUTCOME"
            )
        return {
            "token_address": token,
            "actor": actor_value,
            "human_decision_event_hash": human_decision["event_hash"],
            "baseline_generated_at_utc": generated.isoformat(),
            "observed_at_utc": observed_at.isoformat(),
            "age_sec": max(
                0,
                round((observed_at - generated).total_seconds(), 3),
            ),
            "baseline_price_usd": baseline,
            "current_price_usd": current,
            "current_pool_price_usd": pool_current,
            "change_pct": round(change_pct, 8),
            "price_source": (
                current_market.get("token") or {}
            ).get("price_source"),
            "target_orientation_verified": True,
            "classification": (
                "UP"
                if change_pct > 0
                else "DOWN"
                if change_pct < 0
                else "FLAT"
            ),
        }

    event = append_event_from_factory(
        "OUTCOME_OBSERVED",
        packet_id,
        build,
    )
    return {
        "ok": True,
        "packet_id": packet_id,
        "event": event,
        "authority": "OBSERVATION_ONLY_NO_EXECUTION",
    }


CORE.verify_event_chain = verify_event_chain_locked
CORE.append_event = append_event_locked
CORE.record_human_decision = record_human_decision
CORE.observe_outcome = observe_outcome


class Handler(CORE.Handler):
    def do_POST(self) -> None:
        path = CORE.urllib.parse.urlsplit(self.path).path
        try:
            payload = self.read_json()
            actor = self.headers.get("X-Authenticated-User")
            if path == "/api/v1/analyze":
                return self.send_json(
                    200,
                    CORE.create_analysis(
                        str(payload.get("token_address") or "")
                    ),
                )
            if path == "/api/v1/decisions":
                return self.send_json(
                    201,
                    record_human_decision(
                        str(payload.get("packet_id") or ""),
                        payload.get("action"),
                        payload.get("note"),
                        actor,
                    ),
                )
            if path == "/api/v1/outcomes/observe":
                return self.send_json(
                    201,
                    observe_outcome(
                        str(payload.get("packet_id") or ""),
                        actor,
                    ),
                )
            return self.send_json(404, {"error": "NOT_FOUND"})
        except Exception as exc:
            self.handle_error(exc)


AUTHORITY = CORE.AUTHORITY
if __name__ == "__main__":
    assert CORE.CFG["host"] == "127.0.0.1"
    assert all(
        AUTHORITY[key] is False
        for key in (
            "paper",
            "live",
            "wallet",
            "signing",
            "order",
            "broadcast",
        )
    )
    CORE.ensure_state()
    verify_event_chain_locked()
    ThreadingHTTPServer(
        (CORE.CFG["host"], CORE.CFG["port"]),
        Handler,
    ).serve_forever()
