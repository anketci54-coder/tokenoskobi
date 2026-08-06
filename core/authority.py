#!/usr/bin/env python3
"""Fail-closed authority evaluator for Tokenoskobi.

This module is side-effect free. It classifies a requested operation, validates
its declared effects and checks the machine-readable authority state. Missing,
unknown or semantically incomplete requests are denied.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "authority_state_v1"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "authority_state_v1.json"

READ_ONLY_OPERATIONS = {"read_only", "dryrun", "wallet_read"}
MUTATING_OPERATIONS = {
    "db_write",
    "file_write",
    "secret_update",
    "rpc_call",
    "dashboard_active_mutation",
    "service_enablement",
    "schema_apply",
    "trade_execution",
    "paper_trade_execution",
    "wallet_connect",
    "wallet_sign",
    "transaction_broadcast",
    "order_create",
    "order_cancel",
    "order_replace",
    "swap_execution",
    "hot_path_publish",
}
KNOWN_OPERATION_TYPES = READ_ONLY_OPERATIONS | MUTATING_OPERATIONS

EFFECT_TO_AUTHORITY = {
    "writes_db": ("write", "db_write_allowed", "DB_WRITE_AUTHORITY_DENIED"),
    "writes_file": ("write", "file_write_allowed", "FILE_WRITE_AUTHORITY_DENIED"),
    "touches_secret": ("secret", "update_allowed", "SECRET_UPDATE_AUTHORITY_DENIED"),
    "calls_rpc": ("rpc", "allowed", "RPC_AUTHORITY_DENIED"),
    "mutates_dashboard_active": ("dashboard", "active_panel_mutation_allowed", "DASHBOARD_ACTIVE_MUTATION_AUTHORITY_DENIED"),
    "enables_service": ("service", "enable_allowed", "SERVICE_ENABLE_AUTHORITY_DENIED"),
    "applies_schema": ("schema", "apply_allowed", "SCHEMA_APPLY_AUTHORITY_DENIED"),
    "executes_trade": ("trade", "allowed", "TRADE_AUTHORITY_DENIED"),
    "executes_paper_trade": ("trade", "paper_allowed", "PAPER_TRADE_AUTHORITY_DENIED"),
    "connects_wallet": ("wallet", "connect_allowed", "WALLET_CONNECT_AUTHORITY_DENIED"),
    "reads_wallet": ("wallet", "read_allowed", "WALLET_READ_AUTHORITY_DENIED"),
    "signs_wallet": ("wallet", "sign_allowed", "WALLET_SIGN_AUTHORITY_DENIED"),
    "broadcasts_transaction": ("wallet", "broadcast_allowed", "TRANSACTION_BROADCAST_AUTHORITY_DENIED"),
    "creates_order": ("order", "create_allowed", "ORDER_CREATE_AUTHORITY_DENIED"),
    "cancels_order": ("order", "cancel_allowed", "ORDER_CANCEL_AUTHORITY_DENIED"),
    "replaces_order": ("order", "replace_allowed", "ORDER_REPLACE_AUTHORITY_DENIED"),
    "executes_swap": ("trade", "swap_allowed", "SWAP_EXECUTION_AUTHORITY_DENIED"),
    "publishes_hot_path": ("hot_path", "uncontrolled_write_allowed", "HOT_PATH_PUBLISH_AUTHORITY_DENIED"),
}

OPERATION_TO_AUTHORITY = {
    "db_write": ("write", "db_write_allowed", "DB_WRITE_AUTHORITY_DENIED"),
    "file_write": ("write", "file_write_allowed", "FILE_WRITE_AUTHORITY_DENIED"),
    "secret_update": ("secret", "update_allowed", "SECRET_UPDATE_AUTHORITY_DENIED"),
    "rpc_call": ("rpc", "allowed", "RPC_AUTHORITY_DENIED"),
    "dashboard_active_mutation": ("dashboard", "active_panel_mutation_allowed", "DASHBOARD_ACTIVE_MUTATION_AUTHORITY_DENIED"),
    "service_enablement": ("service", "enable_allowed", "SERVICE_ENABLE_AUTHORITY_DENIED"),
    "schema_apply": ("schema", "apply_allowed", "SCHEMA_APPLY_AUTHORITY_DENIED"),
    "trade_execution": ("trade", "live_allowed", "LIVE_TRADE_AUTHORITY_DENIED"),
    "paper_trade_execution": ("trade", "paper_allowed", "PAPER_TRADE_AUTHORITY_DENIED"),
    "wallet_connect": ("wallet", "connect_allowed", "WALLET_CONNECT_AUTHORITY_DENIED"),
    "wallet_read": ("wallet", "read_allowed", "WALLET_READ_AUTHORITY_DENIED"),
    "wallet_sign": ("wallet", "sign_allowed", "WALLET_SIGN_AUTHORITY_DENIED"),
    "transaction_broadcast": ("wallet", "broadcast_allowed", "TRANSACTION_BROADCAST_AUTHORITY_DENIED"),
    "order_create": ("order", "create_allowed", "ORDER_CREATE_AUTHORITY_DENIED"),
    "order_cancel": ("order", "cancel_allowed", "ORDER_CANCEL_AUTHORITY_DENIED"),
    "order_replace": ("order", "replace_allowed", "ORDER_REPLACE_AUTHORITY_DENIED"),
    "swap_execution": ("trade", "swap_allowed", "SWAP_EXECUTION_AUTHORITY_DENIED"),
    "hot_path_publish": ("hot_path", "uncontrolled_write_allowed", "HOT_PATH_PUBLISH_AUTHORITY_DENIED"),
}


def _decision(ok: bool, operation_type: str = "unknown", operation_id: str = "", reason_codes=None, required_controls=None, matched_authority=None, audit=None) -> dict[str, Any]:
    return {
        "ok": bool(ok),
        "decision": "ALLOW" if ok else "DENY",
        "engine": SCHEMA_VERSION,
        "operation_id": str(operation_id or ""),
        "operation_type": str(operation_type or "unknown"),
        "reason_codes": sorted(set(reason_codes or [])),
        "required_controls": sorted(set(required_controls or [])),
        "matched_authority": dict(matched_authority or {}),
        "audit": dict(audit or {}),
    }


def load_authority_state(path=None) -> dict[str, Any]:
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    try:
        state = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            raise ValueError("AUTHORITY_STATE_NOT_OBJECT")
    except FileNotFoundError:
        return {"ok": False, "state": None, "error": "AUTHORITY_CONFIG_MISSING", "path": str(config_path)}
    except json.JSONDecodeError as exc:
        return {"ok": False, "state": None, "error": "AUTHORITY_CONFIG_INVALID_JSON", "detail": str(exc), "path": str(config_path)}
    except Exception as exc:
        return {"ok": False, "state": None, "error": "AUTHORITY_CONFIG_LOAD_FAILED", "detail": str(exc), "path": str(config_path)}
    return {"ok": True, "state": state, "error": "", "path": str(config_path)}


def validate_authority_state(state: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(state, dict):
        return {"ok": False, "errors": ["AUTHORITY_STATE_NOT_OBJECT"], "warnings": []}
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append("AUTHORITY_SCHEMA_VERSION_MISMATCH")
    for key in ("defaults", "authority", "operation_classes"):
        if not isinstance(state.get(key), dict):
            errors.append(f"AUTHORITY_STATE_MISSING_{key.upper()}")
    if (state.get("defaults") or {}).get("deny_by_default") is not True:
        errors.append("AUTHORITY_DENY_BY_DEFAULT_NOT_TRUE")
    classes = state.get("operation_classes") or {}
    for op in KNOWN_OPERATION_TYPES:
        if not isinstance(classes.get(op), dict):
            errors.append(f"AUTHORITY_OPERATION_CLASS_MISSING:{op}")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def classify_operation(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        return {"ok": False, "operation_type": "unknown", "operation_id": "", "effects": {}, "target": {}, "hot_path": False, "mutating_effects": [], "errors": ["AUTHORITY_REQUEST_NOT_OBJECT"]}
    operation_type = str(request.get("operation_type") or "").strip() or "unknown"
    operation_id = str(request.get("operation_id") or "").strip()
    effects = request.get("effects")
    target = request.get("target")
    errors: list[str] = []
    if operation_type not in KNOWN_OPERATION_TYPES:
        errors.append(f"AUTHORITY_OPERATION_UNKNOWN:{operation_type}")
    if not isinstance(effects, dict):
        errors.append("AUTHORITY_EFFECTS_NOT_OBJECT")
        effects = {}
    if not isinstance(target, dict):
        errors.append("AUTHORITY_TARGET_NOT_OBJECT")
        target = {}
    unknown_effects = sorted(k for k, v in effects.items() if bool(v) and k not in EFFECT_TO_AUTHORITY)
    errors.extend(f"AUTHORITY_EFFECT_UNKNOWN:{name}" for name in unknown_effects)
    mutating_effects = sorted(k for k, v in effects.items() if bool(v) and k in EFFECT_TO_AUTHORITY)
    if operation_type in MUTATING_OPERATIONS and not mutating_effects:
        errors.append("AUTHORITY_MUTATING_OPERATION_EFFECTS_REQUIRED")
    if operation_type in READ_ONLY_OPERATIONS and mutating_effects:
        errors.append("AUTHORITY_READ_ONLY_WITH_MUTATING_EFFECTS")
    return {
        "ok": not errors,
        "operation_type": operation_type,
        "operation_id": operation_id,
        "effects": effects,
        "target": target,
        "hot_path": bool(target.get("hot_path")),
        "mutating_effects": mutating_effects,
        "errors": errors,
    }


def _lookup_bool(state: dict[str, Any], section: str, key: str) -> Any:
    return ((state.get("authority") or {}).get(section) or {}).get(key)


def evaluate_authority(request: Any, state=None) -> dict[str, Any]:
    if state is None:
        loaded = load_authority_state()
        if not loaded.get("ok"):
            return _decision(False, reason_codes=[loaded.get("error") or "AUTHORITY_CONFIG_LOAD_FAILED"], required_controls=["valid_authority_config"], audit={"config_path": loaded.get("path", "")})
        state = loaded["state"]
    validation = validate_authority_state(state)
    if not validation.get("ok"):
        return _decision(False, reason_codes=validation["errors"], required_controls=["valid_authority_config"])
    classified = classify_operation(request)
    op = classified["operation_type"]
    op_id = classified["operation_id"]
    if not classified["ok"]:
        return _decision(False, op, op_id, classified["errors"], ["well_formed_authority_request"], audit={"classification": classified})

    operation_class = state["operation_classes"][op]
    matched: dict[str, Any] = {}
    reasons: list[str] = []
    required: list[str] = []
    allowed = operation_class.get("allowed")
    matched[f"operation_classes.{op}.allowed"] = allowed
    if allowed is not True:
        reasons.append(f"AUTHORITY_OPERATION_DENIED:{op}")
    for key, control in (
        ("requires_approval", "explicit_approval"),
        ("requires_rollback", "rollback_plan"),
        ("requires_dryrun", "dryrun_result"),
        ("requires_backup", "backup_plan"),
        ("requires_budget_guard", "budget_guard"),
        ("requires_authentication", "authentication"),
    ):
        if operation_class.get(key) is True:
            required.append(control)

    check = OPERATION_TO_AUTHORITY.get(op)
    if check:
        section, key, reason = check
        value = _lookup_bool(state, section, key)
        matched[f"authority.{section}.{key}"] = value
        if value is not True:
            reasons.append(reason)
    for effect_name in classified["mutating_effects"]:
        section, key, reason = EFFECT_TO_AUTHORITY[effect_name]
        value = _lookup_bool(state, section, key)
        matched[f"authority.{section}.{key}"] = value
        if value is not True:
            reasons.append(reason)
    if classified["hot_path"] and op not in READ_ONLY_OPERATIONS:
        value = _lookup_bool(state, "hot_path", "uncontrolled_write_allowed")
        matched["authority.hot_path.uncontrolled_write_allowed"] = value
        if value is not True:
            reasons.append("HOT_PATH_MUTATION_AUTHORITY_DENIED")
            required.append("hot_path_authority")
    return _decision(not reasons, op, op_id, reasons, required, matched, {"deny_by_default": True})


def check_operation(operation_type: str, *, effects: dict[str, bool], target: dict[str, Any] | None = None, operation_id: str = "", config_path=None) -> dict[str, Any]:
    """Evaluate one explicitly described operation. Effects are mandatory."""
    loaded = load_authority_state(config_path)
    if not loaded.get("ok"):
        return _decision(False, operation_type, operation_id, [loaded.get("error") or "AUTHORITY_CONFIG_LOAD_FAILED"], ["valid_authority_config"])
    return evaluate_authority({"operation_type": operation_type, "operation_id": operation_id or operation_type, "effects": effects, "target": target or {}}, loaded["state"])


def explain_authority_decision(decision: Any) -> str:
    if not isinstance(decision, dict):
        return "DENY: malformed authority decision"
    op = str(decision.get("operation_type") or "unknown")
    if decision.get("decision") == "ALLOW":
        return f"ALLOW: authority permits {op}"
    reasons = decision.get("reason_codes") or ["deny-by-default authority"]
    return f"DENY: {op} blocked by " + ", ".join(map(str, reasons))

