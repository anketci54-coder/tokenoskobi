#!/usr/bin/env python3
"""Design-safe secret governance helpers for Phase41.

This module is intentionally inert until imported by a future approved
migration. It performs no writes, no DB access, no network calls, no PAYG
calls, no provider tests, no environment reads, and no filesystem secret reads.
"""

from datetime import datetime, timezone
import re


SCHEMA_VERSION = "secret_registry_v1"

SECRET_REGISTRY = {
    "schema_version": SCHEMA_VERSION,
    "scaffold_status": "INERT_BUILTIN_REGISTRY_NO_RUNTIME_EFFECT",
    "storage": {
        "path_key": "secrets_dir",
        "tracked_in_git": False,
        "directory_mode": "0700",
        "file_mode": "0600",
    },
    "secrets": {
        "github_username": {
            "type": "username",
            "required": False,
            "storage": "local_file_or_env",
            "env_names": ["GITHUB_USERNAME"],
            "masking": "username",
            "never_log": True,
        },
        "github_pat": {
            "type": "personal_access_token",
            "required": False,
            "storage": "local_file_or_env",
            "env_names": ["GITHUB_PAT", "GH_TOKEN"],
            "masking": "github_pat",
            "never_log": True,
        },
        "telegram_bot_token": {
            "type": "telegram_bot_token",
            "required": False,
            "storage": "local_file_or_env",
            "env_names": ["TELEGRAM_BOT_TOKEN"],
            "masking": "telegram_bot_token",
            "never_log": True,
        },
        "telegram_chat_id": {
            "type": "telegram_chat_id",
            "required": False,
            "storage": "local_file_or_env",
            "env_names": ["TELEGRAM_CHAT_ID"],
            "masking": "chat_id",
            "never_log": True,
        },
        "future_api_keys": {
            "type": "api_key",
            "required": False,
            "storage": "local_file_or_env",
            "env_names": [],
            "masking": "token",
            "never_log": True,
        },
        "future_rpc_keys": {
            "type": "rpc_key",
            "required": False,
            "storage": "local_file_or_env",
            "env_names": [],
            "masking": "provider_url_or_token",
            "never_log": True,
        },
    },
}


PROTECTED_OPERATIONS = {
    "secret_update",
    "secret_rotation",
    "secret_delete",
    "provider_test",
    "raw_secret_read",
}


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _decision(
    ok,
    secret_key="",
    operation="",
    reason_codes=None,
    required_controls=None,
    matched_secret=None,
    audit=None,
):
    return {
        "ok": bool(ok),
        "decision": "ALLOW" if ok else "DENY",
        "engine": SCHEMA_VERSION,
        "secret_key": str(secret_key or ""),
        "operation": str(operation or ""),
        "reason_codes": list(reason_codes or []),
        "required_controls": list(required_controls or []),
        "matched_secret": dict(matched_secret or {}),
        "audit": dict(audit or {}),
    }


def load_secret_registry(registry=None):
    """Return the inert built-in secret registry.

    This function intentionally performs no filesystem or environment access.
    Passing a registry is supported for tests and future callers.
    """
    if registry is None:
        registry = SECRET_REGISTRY

    validation = validate_secret_registry(registry)
    if not validation.get("ok"):
        return {
            "ok": False,
            "registry": None,
            "error": "SECRET_REGISTRY_INVALID",
            "errors": validation.get("errors", []),
        }

    return {
        "ok": True,
        "registry": registry,
        "error": "",
    }


def validate_secret_registry(registry):
    """Validate the minimal secret registry contract."""
    errors = []
    warnings = []

    if not isinstance(registry, dict):
        return {
            "ok": False,
            "errors": ["SECRET_REGISTRY_NOT_OBJECT"],
            "warnings": warnings,
        }

    if registry.get("schema_version") != SCHEMA_VERSION:
        errors.append("SECRET_REGISTRY_SCHEMA_VERSION_MISMATCH")

    if not isinstance(registry.get("storage"), dict):
        errors.append("SECRET_REGISTRY_STORAGE_MISSING")

    secrets = registry.get("secrets")
    if not isinstance(secrets, dict):
        errors.append("SECRET_REGISTRY_SECRETS_MISSING")
        secrets = {}

    for key in (
        "github_username",
        "github_pat",
        "telegram_bot_token",
        "telegram_chat_id",
        "future_api_keys",
        "future_rpc_keys",
    ):
        entry = secrets.get(key)
        if not isinstance(entry, dict):
            errors.append(f"SECRET_REGISTRY_KEY_MISSING:{key}")
            continue
        for field in ("type", "storage", "masking"):
            if not str(entry.get(field) or "").strip():
                errors.append(f"SECRET_REGISTRY_FIELD_MISSING:{key}:{field}")
        if entry.get("never_log") is not True:
            warnings.append(f"SECRET_REGISTRY_NEVER_LOG_NOT_TRUE:{key}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def classify_secret(secret_key, registry=None):
    """Classify a known secret without reading its value."""
    loaded = load_secret_registry(registry)
    if not loaded.get("ok"):
        return _decision(
            False,
            secret_key=secret_key,
            operation="classify",
            reason_codes=["SECRET_REGISTRY_INVALID"],
            required_controls=["valid_secret_registry"],
            audit={"errors": loaded.get("errors", [])},
        )

    registry = loaded.get("registry")
    key = str(secret_key or "").strip()
    if not key:
        return _decision(
            False,
            secret_key=key,
            operation="classify",
            reason_codes=["SECRET_KEY_EMPTY"],
            required_controls=["known_secret_key"],
        )

    entry = _as_dict(_as_dict(registry).get("secrets")).get(key)
    if not isinstance(entry, dict):
        return _decision(
            False,
            secret_key=key,
            operation="classify",
            reason_codes=[f"SECRET_UNKNOWN:{key}"],
            required_controls=["known_secret_key"],
        )

    matched = {
        "secret_type": entry.get("type"),
        "storage": entry.get("storage"),
        "env_names": list(entry.get("env_names") or []),
        "masking": entry.get("masking"),
        "required": bool(entry.get("required")),
        "never_log": bool(entry.get("never_log")),
        "requires_authority": True,
        "requires_policy": True,
        "requires_approval_for_update": True,
    }
    return _decision(
        True,
        secret_key=key,
        operation="classify",
        matched_secret=matched,
        audit={"secret_value_returned": False},
    )


def _authority_allows(authority_decision):
    if not isinstance(authority_decision, dict):
        return False
    return authority_decision.get("ok") is True and authority_decision.get("decision") == "ALLOW"


def _policy_allows(policy_decision):
    if not isinstance(policy_decision, dict):
        return False
    return policy_decision.get("ok") is True and policy_decision.get("decision") == "ALLOW"


def _approval_allows(approval_decision):
    if not isinstance(approval_decision, dict):
        return False
    return approval_decision.get("ok") is True and approval_decision.get("decision") == "ALLOW"


def _gate(operation, authority_decision=None, policy_decision=None, approval_decision=None):
    reasons = []
    required = []

    if operation in {"status", "read_redacted", "validate_value", "classify"}:
        return reasons, required

    if not _authority_allows(authority_decision):
        reasons.append("AUTHORITY_DECISION_DENIED_OR_MISSING")
        required.append("authority_allow")

    if not _policy_allows(policy_decision):
        reasons.append("POLICY_DECISION_DENIED_OR_MISSING")
        required.append("policy_allow")

    if operation in PROTECTED_OPERATIONS and not _approval_allows(approval_decision):
        reasons.append("APPROVAL_DECISION_DENIED_OR_MISSING")
        required.append("approval_allow")

    return reasons, required


def secret_status(secret_key, context=None, registry=None):
    """Return redacted metadata only. Does not read env or filesystem."""
    classified = classify_secret(secret_key, registry)
    if not classified.get("ok"):
        return classified

    matched = _as_dict(classified.get("matched_secret"))
    status = {
        "secret_type": matched.get("secret_type"),
        "storage": matched.get("storage"),
        "configured": False,
        "source": "not_checked_in_inert_loader",
        "redacted": None,
        "secret_value_returned": False,
        "can_update": False,
        "can_test": False,
    }
    return _decision(
        True,
        secret_key=secret_key,
        operation="status",
        matched_secret=status,
        audit={"context_present": isinstance(context, dict), "secret_value_returned": False},
    )


def read_secret_redacted(secret_key, context=None, registry=None):
    """Return redacted metadata only. Does not read raw secret values."""
    status = secret_status(secret_key, context=context, registry=registry)
    if not status.get("ok"):
        return status

    matched = _as_dict(status.get("matched_secret"))
    return _decision(
        True,
        secret_key=secret_key,
        operation="read_redacted",
        matched_secret={
            "secret_type": matched.get("secret_type"),
            "configured": matched.get("configured"),
            "redacted": matched.get("redacted"),
            "secret_value_returned": False,
        },
        audit={"secret_value_returned": False},
    )


def read_secret_raw(
    secret_key,
    context=None,
    authority_decision=None,
    policy_decision=None,
    approval_decision=None,
    registry=None,
):
    """Raw secret reads are denied by default."""
    classified = classify_secret(secret_key, registry)
    if not classified.get("ok"):
        return classified

    reasons, required = _gate(
        "raw_secret_read",
        authority_decision=authority_decision,
        policy_decision=policy_decision,
        approval_decision=approval_decision,
    )
    reasons.append("SECRET_RAW_READ_DENIED_BY_DEFAULT")
    return _decision(
        False,
        secret_key=secret_key,
        operation="raw_secret_read",
        reason_codes=sorted(set(reasons)),
        required_controls=sorted(set(required)),
        matched_secret=classified.get("matched_secret"),
        audit={"context_present": isinstance(context, dict), "secret_value_returned": False},
    )


def _has_control_chars(value):
    return any(ord(ch) < 32 for ch in str(value or ""))


def validate_secret_value(secret_key, value, registry=None):
    """Validate a secret value offline without storing or testing it."""
    classified = classify_secret(secret_key, registry)
    if not classified.get("ok"):
        return classified

    text = str(value or "")
    matched = _as_dict(classified.get("matched_secret"))
    secret_type = str(matched.get("secret_type") or "")
    reasons = []

    if not text:
        reasons.append("SECRET_VALUE_EMPTY")
    if _has_control_chars(text):
        reasons.append("SECRET_VALUE_HAS_CONTROL_CHARACTERS")

    if secret_type == "username":
        if any(ch.isspace() for ch in text):
            reasons.append("USERNAME_CONTAINS_WHITESPACE")
        if len(text) > 80:
            reasons.append("USERNAME_TOO_LONG")
    elif secret_type == "personal_access_token":
        if not (text.startswith("github_pat_") or text.startswith("ghp_")):
            reasons.append("GITHUB_PAT_SHAPE_INVALID")
        if len(text) < 20:
            reasons.append("GITHUB_PAT_TOO_SHORT")
    elif secret_type == "telegram_bot_token":
        if not re.match(r"^[0-9]{5,}:[A-Za-z0-9_-]{20,}$", text):
            reasons.append("TELEGRAM_BOT_TOKEN_SHAPE_INVALID")
    elif secret_type == "telegram_chat_id":
        if not re.match(r"^-?[0-9]{3,}$", text):
            reasons.append("TELEGRAM_CHAT_ID_SHAPE_INVALID")
    elif secret_type in {"api_key", "rpc_key"}:
        if any(ch.isspace() for ch in text):
            reasons.append("SECRET_TOKEN_CONTAINS_WHITESPACE")
        if len(text) < 8:
            reasons.append("SECRET_TOKEN_TOO_SHORT")

    if reasons:
        return _decision(
            False,
            secret_key=secret_key,
            operation="validate_value",
            reason_codes=sorted(set(reasons)),
            required_controls=["well_formed_secret_value"],
            matched_secret=matched,
            audit={"offline_validation_only": True, "secret_value_returned": False},
        )

    return _decision(
        True,
        secret_key=secret_key,
        operation="validate_value",
        matched_secret=matched,
        audit={"offline_validation_only": True, "secret_value_returned": False},
    )


def prepare_secret_update(
    secret_key,
    value,
    context=None,
    authority_decision=None,
    policy_decision=None,
    approval_decision=None,
    registry=None,
):
    """Prepare a secret update decision without writing anything."""
    validation = validate_secret_value(secret_key, value, registry)
    if not validation.get("ok"):
        return validation

    reasons, required = _gate(
        "secret_update",
        authority_decision=authority_decision,
        policy_decision=policy_decision,
        approval_decision=approval_decision,
    )
    if reasons:
        return _decision(
            False,
            secret_key=secret_key,
            operation="secret_update",
            reason_codes=sorted(set(reasons)),
            required_controls=sorted(set(required)),
            matched_secret=validation.get("matched_secret"),
            audit={"context_present": isinstance(context, dict), "secret_value_returned": False},
        )

    return _decision(
        True,
        secret_key=secret_key,
        operation="secret_update",
        matched_secret={
            "secret_type": _as_dict(validation.get("matched_secret")).get("secret_type"),
            "redacted_preview": mask_secret(value, _as_dict(validation.get("matched_secret")).get("masking")),
            "secret_value_returned": False,
        },
        audit={"prepared_only": True, "no_write_performed": True, "secret_value_returned": False},
    )


def mask_secret(value, secret_type=None):
    """Mask a secret-like value without returning it in clear text."""
    if value is None:
        return None

    text = str(value)
    if not text:
        return None

    kind = str(secret_type or "").strip()

    if kind in {"github_pat", "personal_access_token"}:
        if text.startswith("github_pat_"):
            return "github_pat_<REDACTED>"
        if text.startswith("ghp_"):
            return "ghp_<REDACTED>"

    if kind == "telegram_bot_token":
        if ":" in text:
            prefix = text.split(":", 1)[0]
            return prefix + ":<REDACTED>"
        return "<REDACTED_TELEGRAM_TOKEN>"

    if kind == "chat_id" or kind == "telegram_chat_id":
        return "<REDACTED_CHAT_ID>"

    if kind == "provider_url_or_token":
        redacted = re.sub(r"(/v2/)[A-Za-z0-9_-]+", r"\1<REDACTED>", text)
        if redacted != text:
            return redacted

    if len(text) <= 8:
        return "<REDACTED>"

    return text[:4] + "..." + text[-4:]


def redact_mapping(values, registry=None):
    """Return a redacted copy of a mapping."""
    if not isinstance(values, dict):
        return {}

    loaded = load_secret_registry(registry)
    reg = loaded.get("registry") if loaded.get("ok") else SECRET_REGISTRY
    secrets = _as_dict(reg.get("secrets"))

    out = {}
    for key, value in values.items():
        key_text = str(key)
        entry = _as_dict(secrets.get(key_text))
        if entry:
            out[key_text] = mask_secret(value, entry.get("masking"))
        elif any(marker in key_text.lower() for marker in ("secret", "token", "pat", "api_key", "password", "provider_url")):
            out[key_text] = mask_secret(value, "token")
        else:
            out[key_text] = value
    return out


def build_secret_audit_event(event_type, secret_key, decision, context=None):
    """Build a redacted audit event. Never includes raw secret values."""
    dec = _as_dict(decision)
    ctx = _as_dict(context)
    return {
        "event_type": str(event_type or ""),
        "secret_key": str(secret_key or ""),
        "decision": str(dec.get("decision") or "DENY"),
        "reason_codes": list(dec.get("reason_codes") or []),
        "required_controls": list(dec.get("required_controls") or []),
        "caller": str(ctx.get("caller") or ""),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "secret_value_returned": False,
        "redacted": True,
    }


def explain_secret_decision(decision):
    """Return a short human-readable explanation for a secret decision."""
    if not isinstance(decision, dict):
        return "DENY: malformed secret decision"

    status = str(decision.get("decision") or "DENY")
    secret_key = str(decision.get("secret_key") or "unknown_secret")
    operation = str(decision.get("operation") or "unknown_operation")
    reasons = decision.get("reason_codes") or []

    if status == "ALLOW":
        return f"ALLOW: secret policy permits {operation} for {secret_key}"
    if reasons:
        return f"DENY: {operation} for {secret_key} blocked by " + ", ".join(str(r) for r in reasons)
    return f"DENY: {operation} for {secret_key} blocked by fail-closed secret policy"
