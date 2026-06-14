#!/usr/bin/env python3
"""Design-safe approval evaluator for Phase41.

This module is intentionally inert until imported by a future approved
migration. It performs no writes, no network calls, no DB access, no secret
access, no PAYG calls, and no runtime side effects.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = "approval_policy_v1"

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "approval_policy_v1.json"
)

PROTECTED_OPERATION_TYPES = {
    "real_apply",
    "db_write",
    "rpc_payg_call",
    "rpc_call",
    "secret_update",
    "secret_provider_test",
    "dashboard_active_mutation",
    "service_enablement",
    "schema_apply",
}

UNPROTECTED_OPERATION_TYPES = {
    "read_only",
    "dryrun",
}

KNOWN_OPERATION_TYPES = PROTECTED_OPERATION_TYPES | UNPROTECTED_OPERATION_TYPES


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _decision(
    ok,
    operation_type="unknown",
    operation_id="",
    reason_codes=None,
    required_controls=None,
    matched_approval=None,
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
        "matched_approval": dict(matched_approval or {}),
        "audit": dict(audit or {}),
    }


def load_approval_policy(path=None):
    """Load approval_policy_v1.json.

    Missing, unreadable, or invalid JSON config returns a fail-closed object
    instead of raising.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    try:
        with config_path.open("r", encoding="utf-8") as f:
            policy = json.load(f)
    except FileNotFoundError:
        return {
            "ok": False,
            "policy": None,
            "error": "APPROVAL_POLICY_MISSING",
            "path": str(config_path),
        }
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "policy": None,
            "error": "APPROVAL_POLICY_INVALID_JSON",
            "detail": str(exc),
            "path": str(config_path),
        }
    except Exception as exc:
        return {
            "ok": False,
            "policy": None,
            "error": "APPROVAL_POLICY_LOAD_FAILED",
            "detail": str(exc),
            "path": str(config_path),
        }

    return {
        "ok": True,
        "policy": policy,
        "error": "",
        "path": str(config_path),
    }


def _validate_approval_policy(policy):
    errors = []
    warnings = []

    if not isinstance(policy, dict):
        return {
            "ok": False,
            "errors": ["APPROVAL_POLICY_NOT_OBJECT"],
            "warnings": warnings,
        }

    if policy.get("schema_version") != SCHEMA_VERSION:
        errors.append("APPROVAL_SCHEMA_VERSION_MISMATCH")

    for key in ("defaults", "approval_classes"):
        if not isinstance(policy.get(key), dict):
            errors.append(f"APPROVAL_POLICY_MISSING_{key.upper()}")

    defaults = policy.get("defaults") or {}
    if defaults.get("deny_without_required_approval") is not True:
        errors.append("APPROVAL_DENY_WITHOUT_REQUIRED_APPROVAL_NOT_TRUE")

    approval_classes = policy.get("approval_classes") or {}
    for op in PROTECTED_OPERATION_TYPES:
        if op == "rpc_call":
            continue
        if not isinstance(approval_classes.get(op), dict):
            warnings.append(f"APPROVAL_CLASS_MISSING:{op}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def validate_approval_request(request):
    """Validate and classify an approval request."""
    if not isinstance(request, dict):
        return {
            "ok": False,
            "operation_id": "",
            "operation_type": "unknown",
            "errors": ["APPROVAL_REQUEST_NOT_OBJECT"],
            "request": {},
        }

    operation_id = str(request.get("operation_id") or "").strip()
    operation_type = str(request.get("operation_type") or "").strip()
    caller = str(request.get("caller") or "").strip()
    target = str(request.get("target") or "").strip()
    requested_mode = str(request.get("requested_mode") or request.get("mode") or "").strip()

    errors = []
    if not operation_id:
        errors.append("APPROVAL_OPERATION_ID_EMPTY")
    if not operation_type:
        errors.append("APPROVAL_OPERATION_TYPE_EMPTY")
        operation_type = "unknown"
    elif operation_type not in KNOWN_OPERATION_TYPES:
        errors.append(f"APPROVAL_OPERATION_UNKNOWN:{operation_type}")

    if operation_type in PROTECTED_OPERATION_TYPES:
        if not caller:
            errors.append("APPROVAL_CALLER_EMPTY")
        if not target:
            errors.append("APPROVAL_TARGET_EMPTY")
        if not requested_mode:
            errors.append("APPROVAL_REQUESTED_MODE_EMPTY")

    return {
        "ok": not errors,
        "operation_id": operation_id,
        "operation_type": operation_type,
        "caller": caller,
        "target": target,
        "requested_mode": requested_mode,
        "errors": errors,
        "request": request,
    }


def validate_approval_record(record):
    """Validate approval record shape without granting approval."""
    if not isinstance(record, dict):
        return {
            "ok": False,
            "errors": ["APPROVAL_RECORD_NOT_OBJECT"],
            "record": {},
        }

    required = [
        "operation_id",
        "operation_type",
        "caller",
        "target",
        "requested_mode",
        "approved_by",
        "approved_at_utc",
        "expires_at_utc",
    ]
    errors = []
    for field in required:
        if not str(record.get(field) or "").strip():
            errors.append(f"APPROVAL_RECORD_{field.upper()}_EMPTY")

    if not (str(record.get("approval_phrase") or "").strip() or str(record.get("approval_token") or "").strip()):
        errors.append("APPROVAL_PHRASE_OR_TOKEN_MISSING")

    return {
        "ok": not errors,
        "errors": errors,
        "record": record,
    }


def approval_required(operation_type, approval_policy=None):
    """Return whether an operation type requires approval."""
    op = str(operation_type or "").strip()
    if op in UNPROTECTED_OPERATION_TYPES:
        return False
    if op in PROTECTED_OPERATION_TYPES:
        return True

    policy = approval_policy if isinstance(approval_policy, dict) else {}
    approval_classes = policy.get("approval_classes") or {}
    cls = approval_classes.get(op)
    if isinstance(cls, dict):
        return bool(cls.get("requires_explicit_approval"))

    return True


def _parse_utc(value):
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def approval_expired(record, now_utc=None):
    """Return True when an approval record is expired or has invalid expiry."""
    if not isinstance(record, dict):
        return True

    expires = _parse_utc(record.get("expires_at_utc"))
    if expires is None:
        return True

    approved_at = _parse_utc(record.get("approved_at_utc"))
    if approved_at is not None and approved_at > expires:
        return True

    now = now_utc
    if now is None:
        now = datetime.now(timezone.utc)
    elif isinstance(now, str):
        now = _parse_utc(now)
        if now is None:
            return True
    elif isinstance(now, datetime):
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        now = now.astimezone(timezone.utc)
    else:
        return True

    return now >= expires


def approval_matches_operation(request, record):
    """Validate that an approval record is scoped to exactly this request."""
    req = _as_dict(request)
    rec = _as_dict(record)
    mismatches = []

    fields = (
        ("operation_id", "APPROVAL_OPERATION_ID_MISMATCH"),
        ("operation_type", "APPROVAL_OPERATION_TYPE_MISMATCH"),
        ("caller", "APPROVAL_CALLER_MISMATCH"),
        ("target", "APPROVAL_TARGET_MISMATCH"),
    )
    for field, code in fields:
        if str(req.get(field) or "").strip() != str(rec.get(field) or "").strip():
            mismatches.append(code)

    req_mode = str(req.get("requested_mode") or req.get("mode") or "").strip()
    rec_mode = str(rec.get("requested_mode") or rec.get("mode") or "").strip()
    if req_mode != rec_mode:
        mismatches.append("APPROVAL_MODE_MISMATCH")

    return {
        "ok": not mismatches,
        "errors": mismatches,
    }


def _authority_allows(authority_decision):
    if not isinstance(authority_decision, dict):
        return False
    return authority_decision.get("ok") is True and authority_decision.get("decision") == "ALLOW"


def _policy_allows(policy_decision):
    if not isinstance(policy_decision, dict):
        return False
    return policy_decision.get("ok") is True and policy_decision.get("decision") == "ALLOW"


def _approval_class(operation_type, policy):
    approval_classes = _as_dict(_as_dict(policy).get("approval_classes"))
    op = str(operation_type or "").strip()
    if op == "rpc_call":
        op = "rpc_payg_call"
    return _as_dict(approval_classes.get(op))


def _artifacts(request, record):
    req_artifacts = _as_dict(_as_dict(request).get("artifacts"))
    return {
        "dryrun_artifact": record.get("dryrun_artifact") or req_artifacts.get("dryrun_artifact"),
        "backup_artifact": record.get("backup_artifact") or req_artifacts.get("backup_artifact"),
        "rollback_artifact": record.get("rollback_artifact") or req_artifacts.get("rollback_artifact"),
    }


def evaluate_approval(
    request,
    authority_decision=None,
    policy_decision=None,
    approval_record=None,
    approval_policy=None,
):
    """Evaluate approval for a request.

    Authority denial and policy denial always dominate approval. This evaluator
    fails closed for malformed requests, missing approval, malformed approval,
    expired approval, operation mismatch, and missing required artifacts.
    """
    loaded = None
    if approval_policy is None:
        loaded = load_approval_policy()
        if not loaded.get("ok"):
            return _decision(
                False,
                reason_codes=[loaded.get("error") or "APPROVAL_POLICY_LOAD_FAILED"],
                required_controls=["valid_approval_policy"],
                audit={"config_path": loaded.get("path", "")},
            )
        approval_policy = loaded.get("policy")

    policy_validation = _validate_approval_policy(approval_policy)
    if not policy_validation.get("ok"):
        return _decision(
            False,
            reason_codes=policy_validation.get("errors"),
            required_controls=["valid_approval_policy"],
            audit={"warnings": policy_validation.get("warnings", [])},
        )

    request_validation = validate_approval_request(request)
    operation_id = request_validation.get("operation_id", "")
    operation_type = request_validation.get("operation_type", "unknown")

    if not request_validation.get("ok"):
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=request_validation.get("errors"),
            required_controls=["well_formed_approval_request"],
            audit={"fail_closed": True},
        )

    if operation_type in UNPROTECTED_OPERATION_TYPES:
        return _decision(
            True,
            operation_type=operation_type,
            operation_id=operation_id,
            matched_approval={"approval_required": False},
            audit={
                "approval_schema_version": approval_policy.get("schema_version"),
                "authority_dominates_approval": True,
                "policy_dominates_approval": True,
                "fail_closed": True,
            },
        )

    if not _authority_allows(authority_decision):
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=["AUTHORITY_DECISION_DENIED_OR_MISSING"],
            required_controls=["authority_allow"],
            audit={
                "authority_dominates_approval": True,
                "fail_closed": True,
            },
        )

    if not _policy_allows(policy_decision):
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=["POLICY_DECISION_DENIED_OR_MISSING"],
            required_controls=["policy_allow"],
            audit={
                "policy_dominates_approval": True,
                "fail_closed": True,
            },
        )

    if approval_required(operation_type, approval_policy) and approval_record is None:
        cls = _approval_class(operation_type, approval_policy)
        controls = ["explicit_approval"]
        if cls.get("requires_dryrun") is True:
            controls.append("dryrun_artifact")
        if cls.get("requires_backup") is True:
            controls.append("backup_artifact")
        if cls.get("requires_rollback") is True:
            controls.append("rollback_artifact")
        if cls.get("requires_authentication") is True:
            controls.append("authentication")
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=["APPROVAL_RECORD_MISSING"],
            required_controls=sorted(set(controls)),
            matched_approval=cls,
            audit={"fail_closed": True},
        )

    record_validation = validate_approval_record(approval_record)
    if not record_validation.get("ok"):
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=record_validation.get("errors"),
            required_controls=["well_formed_approval_record"],
            audit={"fail_closed": True},
        )

    match = approval_matches_operation(request_validation.get("request"), approval_record)
    if not match.get("ok"):
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=match.get("errors"),
            required_controls=["matching_approval_record"],
            audit={"operation_match_checked": True, "fail_closed": True},
        )

    if approval_expired(approval_record):
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=["APPROVAL_EXPIRED"],
            required_controls=["fresh_approval"],
            audit={"expiry_checked": True, "fail_closed": True},
        )

    cls = _approval_class(operation_type, approval_policy)
    artifacts = _artifacts(request_validation.get("request"), approval_record)
    reasons = []
    required = []

    if cls.get("requires_explicit_approval") is True:
        if not (str(approval_record.get("approval_phrase") or "").strip() or str(approval_record.get("approval_token") or "").strip()):
            reasons.append("APPROVAL_PHRASE_OR_TOKEN_MISSING")
            required.append("explicit_approval")

    if cls.get("requires_dryrun") is True and not str(artifacts.get("dryrun_artifact") or "").strip():
        reasons.append("DRYRUN_ARTIFACT_REQUIRED")
        required.append("dryrun_artifact")

    if cls.get("requires_backup") is True and not str(artifacts.get("backup_artifact") or "").strip():
        reasons.append("BACKUP_ARTIFACT_REQUIRED")
        required.append("backup_artifact")

    if cls.get("requires_rollback") is True and not str(artifacts.get("rollback_artifact") or "").strip():
        reasons.append("ROLLBACK_ARTIFACT_REQUIRED")
        required.append("rollback_artifact")

    if cls.get("requires_authentication") is True:
        auth_ctx = _as_dict(approval_record.get("authentication_context"))
        if auth_ctx.get("authenticated") is not True:
            reasons.append("AUTHENTICATION_REQUIRED")
            required.append("authentication")

    if reasons:
        return _decision(
            False,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=sorted(set(reasons)),
            required_controls=sorted(set(required)),
            matched_approval=cls,
            audit={
                "approval_schema_version": approval_policy.get("schema_version"),
                "expiry_checked": True,
                "operation_match_checked": True,
                "fail_closed": True,
            },
        )

    return _decision(
        True,
        operation_type=operation_type,
        operation_id=operation_id,
        reason_codes=[],
        required_controls=[],
        matched_approval=cls,
        audit={
            "approval_schema_version": approval_policy.get("schema_version"),
            "authority_dominates_approval": True,
            "policy_dominates_approval": True,
            "expiry_checked": True,
            "operation_match_checked": True,
            "fail_closed": True,
        },
    )
