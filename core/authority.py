#!/usr/bin/env python3
"""Design-safe authority evaluator for Phase41.

This module is intentionally inert until imported by a future approved
migration. It performs no writes, no network calls, no DB access, and no
runtime side effects.
"""

import json
from pathlib import Path


SCHEMA_VERSION = "authority_state_v1"

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "authority_state_v1.json"
)

KNOWN_OPERATION_TYPES = {
    "read_only",
    "dryrun",
    "db_write",
    "file_write",
    "secret_update",
    "rpc_call",
    "dashboard_active_mutation",
    "service_enablement",
    "schema_apply",
}

EFFECT_TO_AUTHORITY = {
    "writes_db": ("write", "db_write_allowed", "DB_WRITE_AUTHORITY_DENIED"),
    "writes_file": ("write", "file_write_allowed", "FILE_WRITE_AUTHORITY_DENIED"),
    "touches_secret": ("secret", "update_allowed", "SECRET_UPDATE_AUTHORITY_DENIED"),
    "calls_rpc": ("rpc", "allowed", "RPC_AUTHORITY_DENIED"),
    "mutates_dashboard_active": (
        "dashboard",
        "active_panel_mutation_allowed",
        "DASHBOARD_ACTIVE_MUTATION_AUTHORITY_DENIED",
    ),
    "enables_service": ("service", "enable_allowed", "SERVICE_ENABLE_AUTHORITY_DENIED"),
    "applies_schema": ("schema", "apply_allowed", "SCHEMA_APPLY_AUTHORITY_DENIED"),
}

OPERATION_TO_AUTHORITY = {
    "db_write": ("write", "db_write_allowed", "DB_WRITE_AUTHORITY_DENIED"),
    "file_write": ("write", "file_write_allowed", "FILE_WRITE_AUTHORITY_DENIED"),
    "secret_update": ("secret", "update_allowed", "SECRET_UPDATE_AUTHORITY_DENIED"),
    "rpc_call": ("rpc", "allowed", "RPC_AUTHORITY_DENIED"),
    "dashboard_active_mutation": (
        "dashboard",
        "active_panel_mutation_allowed",
        "DASHBOARD_ACTIVE_MUTATION_AUTHORITY_DENIED",
    ),
    "service_enablement": ("service", "enable_allowed", "SERVICE_ENABLE_AUTHORITY_DENIED"),
    "schema_apply": ("schema", "apply_allowed", "SCHEMA_APPLY_AUTHORITY_DENIED"),
}


def _decision(
    ok,
    operation_type="unknown",
    operation_id="",
    reason_codes=None,
    required_controls=None,
    matched_authority=None,
    audit=None,
):
    return {
        "ok": bool(ok),
        "decision": "ALLOW" if ok else "DENY",
        "engine": SCHEMA_VERSION,
        "operation_id": str(operation_id or ""),
        "operation_type": str(operation_type or "unknown"),
        "reason_codes": list(reason_codes or []),
        "required_controls": list(required_controls or []),
        "matched_authority": dict(matched_authority or {}),
        "audit": dict(audit or {}),
    }


def load_authority_state(path=None):
    """Load authority_state_v1.json.

    Missing, unreadable, or invalid JSON config returns a fail-closed state
    object instead of raising.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    try:
        with config_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
    except FileNotFoundError:
        return {
            "ok": False,
            "state": None,
            "error": "AUTHORITY_CONFIG_MISSING",
            "path": str(config_path),
        }
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "state": None,
            "error": "AUTHORITY_CONFIG_INVALID_JSON",
            "detail": str(exc),
            "path": str(config_path),
        }
    except Exception as exc:
        return {
            "ok": False,
            "state": None,
            "error": "AUTHORITY_CONFIG_LOAD_FAILED",
            "detail": str(exc),
            "path": str(config_path),
        }

    return {
        "ok": True,
        "state": state,
        "error": "",
        "path": str(config_path),
    }


def validate_authority_state(state):
    """Validate the minimal authority_state_v1 contract."""
    errors = []
    warnings = []

    if not isinstance(state, dict):
        return {
            "ok": False,
            "errors": ["AUTHORITY_STATE_NOT_OBJECT"],
            "warnings": warnings,
        }

    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append("AUTHORITY_SCHEMA_VERSION_MISMATCH")

    for key in ("defaults", "authority", "operation_classes"):
        if not isinstance(state.get(key), dict):
            errors.append(f"AUTHORITY_STATE_MISSING_{key.upper()}")

    defaults = state.get("defaults") or {}
    if defaults.get("deny_by_default") is not True:
        errors.append("AUTHORITY_DENY_BY_DEFAULT_NOT_TRUE")

    operation_classes = state.get("operation_classes") or {}
    for op in KNOWN_OPERATION_TYPES:
        if not isinstance(operation_classes.get(op), dict):
            warnings.append(f"AUTHORITY_OPERATION_CLASS_MISSING:{op}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def classify_operation(request):
    """Classify an authority request without making an allow/deny decision."""
    if not isinstance(request, dict):
        return {
            "ok": False,
            "operation_type": "unknown",
            "operation_id": "",
            "effects": {},
            "target": {},
            "errors": ["AUTHORITY_REQUEST_NOT_OBJECT"],
        }

    operation_type = str(request.get("operation_type") or "").strip()
    operation_id = str(request.get("operation_id") or "").strip()
    effects = request.get("effects") or {}
    target = request.get("target") or {}

    errors = []
    if not operation_type:
        errors.append("AUTHORITY_OPERATION_TYPE_EMPTY")
        operation_type = "unknown"
    elif operation_type not in KNOWN_OPERATION_TYPES:
        errors.append(f"AUTHORITY_OPERATION_UNKNOWN:{operation_type}")

    if not isinstance(effects, dict):
        errors.append("AUTHORITY_EFFECTS_NOT_OBJECT")
        effects = {}

    if not isinstance(target, dict):
        errors.append("AUTHORITY_TARGET_NOT_OBJECT")
        target = {}

    hot_path = bool(target.get("hot_path"))
    mutating_effects = [
        name for name, value in effects.items() if name in EFFECT_TO_AUTHORITY and bool(value)
    ]

    return {
        "ok": not errors,
        "operation_type": operation_type,
        "operation_id": operation_id,
        "effects": effects,
        "target": target,
        "hot_path": hot_path,
        "mutating_effects": mutating_effects,
        "errors": errors,
    }


def _lookup_bool(state, section, key):
    authority = state.get("authority") or {}
    section_obj = authority.get(section) or {}
    return section_obj.get(key)


def evaluate_authority(request, state=None):
    """Evaluate authority for a request.

    The evaluator fails closed for missing config, invalid config, malformed
    request, unknown operation, and any false/missing required authority flag.
    """
    loaded = None
    if state is None:
        loaded = load_authority_state()
        if not loaded.get("ok"):
            return _decision(
                False,
                reason_codes=[loaded.get("error") or "AUTHORITY_CONFIG_LOAD_FAILED"],
                required_controls=["valid_authority_config"],
                audit={"config_path": loaded.get("path", "")},
            )
        state = loaded.get("state")

    validation = validate_authority_state(state)
    if not validation.get("ok"):
        return _decision(
            False,
            reason_codes=validation.get("errors"),
            required_controls=["valid_authority_config"],
            audit={"warnings": validation.get("warnings", [])},
        )

    classified = classify_operation(request)
    operation_type = classified.get("operation_type", "unknown")
    operation_id = classified.get("operation_id", "")
    if not classified.get("ok"):
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=classified.get("errors"),
            required_controls=["well_formed_authority_request"],
            audit={"classification": classified},
        )

    operation_classes = state.get("operation_classes") or {}
    operation_class = operation_classes.get(operation_type)
    if not isinstance(operation_class, dict):
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=[f"AUTHORITY_OPERATION_CLASS_MISSING:{operation_type}"],
            required_controls=["known_operation_class"],
        )

    matched = {}
    reasons = []
    required = []

    op_allowed = operation_class.get("allowed")
    matched[f"operation_classes.{operation_type}.allowed"] = op_allowed
    if op_allowed is not True:
        reasons.append(f"AUTHORITY_OPERATION_DENIED:{operation_type}")
        if operation_class.get("requires_approval") is True:
            required.append("explicit_approval")
        if operation_class.get("requires_rollback") is True:
            required.append("rollback_plan")
        if operation_class.get("requires_dryrun") is True:
            required.append("dryrun_result")
        if operation_class.get("requires_backup") is True:
            required.append("backup_plan")
        if operation_class.get("requires_budget_guard") is True:
            required.append("budget_guard")
        if operation_class.get("requires_authentication") is True:
            required.append("authentication")

    authority_check = OPERATION_TO_AUTHORITY.get(operation_type)
    if authority_check is not None:
        section, key, reason = authority_check
        value = _lookup_bool(state, section, key)
        matched[f"authority.{section}.{key}"] = value
        if value is not True:
            reasons.append(reason)

    for effect_name, (section, key, reason) in EFFECT_TO_AUTHORITY.items():
        if bool(classified["effects"].get(effect_name)):
            value = _lookup_bool(state, section, key)
            matched[f"authority.{section}.{key}"] = value
            if value is not True:
                reasons.append(reason)

    if classified.get("hot_path"):
        hot_value = _lookup_bool(state, "hot_path", "uncontrolled_write_allowed")
        matched["authority.hot_path.uncontrolled_write_allowed"] = hot_value
        if hot_value is not True and operation_type not in {"read_only", "dryrun"}:
            reasons.append("HOT_PATH_MUTATION_AUTHORITY_DENIED")
            required.append("hot_path_authority")

    if reasons:
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=sorted(set(reasons)),
            required_controls=sorted(set(required)),
            matched_authority=matched,
            audit={
                "state_schema_version": state.get("schema_version"),
                "deny_by_default": (state.get("defaults") or {}).get("deny_by_default"),
            },
        )

    return _decision(
        True,
        operation_type=operation_type,
        operation_id=operation_id,
        reason_codes=[],
        required_controls=[],
        matched_authority=matched,
        audit={
            "state_schema_version": state.get("schema_version"),
            "deny_by_default": (state.get("defaults") or {}).get("deny_by_default"),
        },
    )


def explain_authority_decision(decision):
    """Return a short human-readable explanation for a decision."""
    if not isinstance(decision, dict):
        return "DENY: malformed authority decision"

    status = str(decision.get("decision") or "DENY")
    operation_type = str(decision.get("operation_type") or "unknown")
    reasons = decision.get("reason_codes") or []
    if status == "ALLOW":
        return f"ALLOW: authority permits {operation_type}"
    if reasons:
        return f"DENY: {operation_type} blocked by " + ", ".join(str(r) for r in reasons)
    return f"DENY: {operation_type} blocked by deny-by-default authority"
