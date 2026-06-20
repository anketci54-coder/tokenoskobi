#!/usr/bin/env python3
"""Design-safe policy evaluator for Phase41.

This module is intentionally inert until imported by a future approved
migration. It performs no writes, no network calls, no DB access, no secret
access, no PAYG calls, and no runtime side effects.
"""

import json
from pathlib import Path


SCHEMA_VERSION = "project_policy_registry_v1"

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "project_policy_registry_v1.json"
)

KNOWN_DOMAINS = {
    "source_trust",
    "payg_rpc",
    "db_write",
    "file_write",
    "dashboard",
    "service",
    "secret",
    "paper_live",
    "schema_apply",
    "logging_redaction",
    "path_governance",
    "approval",
}

KNOWN_OPERATION_TYPES = {
    "read_only",
    "dryrun",
    "source_check",
    "rpc_call",
    "db_write",
    "file_write",
    "dashboard_render",
    "dashboard_preview",
    "dashboard_active_mutation",
    "secret_status",
    "secret_raw_read",
    "secret_update",
    "secret_provider_test",
    "schema_apply",
    "logging_check",
    "service_enablement",
}


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _decision(
    ok,
    domain="unknown",
    operation_type="unknown",
    operation_id="",
    reason_codes=None,
    required_controls=None,
    matched_policy=None,
    audit=None,
):
    return {
        "ok": bool(ok),
        "decision": "ALLOW" if ok else "DENY",
        "engine": SCHEMA_VERSION,
        "operation_id": str(operation_id or ""),
        "operation_type": str(operation_type or "unknown"),
        "domain": str(domain or "unknown"),
        "reason_codes": list(reason_codes or []),
        "required_controls": list(required_controls or []),
        "matched_policy": dict(matched_policy or {}),
        "audit": dict(audit or {}),
    }


def load_policy_registry(path=None):
    """Load project_policy_registry_v1.json.

    Missing, unreadable, or invalid JSON config returns a fail-closed object
    instead of raising.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    try:
        with config_path.open("r", encoding="utf-8") as f:
            registry = json.load(f)
    except FileNotFoundError:
        return {
            "ok": False,
            "registry": None,
            "error": "POLICY_REGISTRY_MISSING",
            "path": str(config_path),
        }
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "registry": None,
            "error": "POLICY_REGISTRY_INVALID_JSON",
            "detail": str(exc),
            "path": str(config_path),
        }
    except Exception as exc:
        return {
            "ok": False,
            "registry": None,
            "error": "POLICY_REGISTRY_LOAD_FAILED",
            "detail": str(exc),
            "path": str(config_path),
        }

    return {
        "ok": True,
        "registry": registry,
        "error": "",
        "path": str(config_path),
    }


def validate_policy_registry(registry):
    """Validate the minimal project_policy_registry_v1 contract."""
    errors = []
    warnings = []

    if not isinstance(registry, dict):
        return {
            "ok": False,
            "errors": ["POLICY_REGISTRY_NOT_OBJECT"],
            "warnings": warnings,
        }

    if registry.get("schema_version") != SCHEMA_VERSION:
        errors.append("POLICY_SCHEMA_VERSION_MISMATCH")

    for key in ("defaults", "domains", "decision_defaults"):
        if not isinstance(registry.get(key), dict):
            errors.append(f"POLICY_REGISTRY_MISSING_{key.upper()}")

    defaults = registry.get("defaults") or {}
    if defaults.get("deny_by_default") is not True:
        errors.append("POLICY_DENY_BY_DEFAULT_NOT_TRUE")

    domains = registry.get("domains") or {}
    for domain in KNOWN_DOMAINS:
        if not isinstance(domains.get(domain), dict):
            warnings.append(f"POLICY_DOMAIN_MISSING:{domain}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def classify_policy_request(request):
    """Classify a policy request without making an allow/deny decision."""
    if not isinstance(request, dict):
        return {
            "ok": False,
            "operation_id": "",
            "operation_type": "unknown",
            "domain": "unknown",
            "errors": ["POLICY_REQUEST_NOT_OBJECT"],
            "request": {},
        }

    operation_id = str(request.get("operation_id") or "").strip()
    operation_type = str(request.get("operation_type") or "").strip()
    domain = str(request.get("domain") or "").strip()

    errors = []
    if not operation_type:
        errors.append("POLICY_OPERATION_TYPE_EMPTY")
        operation_type = "unknown"
    elif operation_type not in KNOWN_OPERATION_TYPES:
        errors.append(f"POLICY_OPERATION_UNKNOWN:{operation_type}")

    if not domain:
        errors.append("POLICY_DOMAIN_EMPTY")
        domain = "unknown"
    elif domain not in KNOWN_DOMAINS:
        errors.append(f"POLICY_DOMAIN_UNKNOWN:{domain}")

    return {
        "ok": not errors,
        "operation_id": operation_id,
        "operation_type": operation_type,
        "domain": domain,
        "errors": errors,
        "request": request,
    }


def _domain(registry, name):
    return _as_dict(_as_dict(registry).get("domains", {})).get(name) or {}


def _authority_allows(authority_decision):
    if authority_decision is None:
        return False
    if not isinstance(authority_decision, dict):
        return False
    return authority_decision.get("decision") == "ALLOW" and authority_decision.get("ok") is True


def _approval_allows(approval_decision):
    if approval_decision is None:
        return False
    if not isinstance(approval_decision, dict):
        return False
    return approval_decision.get("decision") == "ALLOW" and approval_decision.get("ok") is True


def _requires_authority(request):
    domain = str(request.get("domain") or "")
    operation_type = str(request.get("operation_type") or "")
    mode = str(request.get("mode") or "").lower()

    if mode in {"real", "apply", "enable", "update", "test"}:
        return True
    if domain in {"payg_rpc", "db_write", "dashboard", "secret", "schema_apply", "service"}:
        if operation_type not in {"read_only", "dryrun", "dashboard_render", "dashboard_preview", "secret_status"}:
            return True
    return False


def _requires_approval(request):
    domain = str(request.get("domain") or "")
    operation_type = str(request.get("operation_type") or "")
    mode = str(request.get("mode") or "").lower()

    if mode in {"real", "apply", "enable", "update", "test"}:
        return True
    if operation_type in {
        "db_write",
        "rpc_call",
        "secret_update",
        "secret_provider_test",
        "dashboard_active_mutation",
        "service_enablement",
        "schema_apply",
    }:
        return True
    if domain in {"db_write", "schema_apply"}:
        return True
    return False


def _gate_authority_and_approval(request, authority_decision, approval_decision):
    reasons = []
    required = []

    if _requires_authority(request) and not _authority_allows(authority_decision):
        reasons.append("AUTHORITY_DECISION_DENIED_OR_MISSING")
        required.append("authority_allow")

    if _requires_approval(request) and not _approval_allows(approval_decision):
        reasons.append("APPROVAL_DECISION_DENIED_OR_MISSING")
        required.append("approval_allow")

    return reasons, required


def evaluate_source_trust(request, registry):
    domain = _domain(registry, "source_trust")
    source = _as_dict(request.get("source"))
    source_name = str(source.get("name") or request.get("source_name") or "").strip()
    matched = {
        "domains.source_trust.default_behavior": domain.get("default_behavior"),
        "domains.source_trust.requires_identity": domain.get("requires_identity"),
    }

    if not source_name:
        return False, ["SOURCE_EMPTY"], [], matched

    sources = _as_dict(domain.get("sources"))
    info = sources.get(source_name)
    matched[f"domains.source_trust.sources.{source_name}"] = info

    if not isinstance(info, dict):
        return False, ["SOURCE_UNKNOWN"], [], matched
    if info.get("trusted") is not True:
        return False, ["SOURCE_NOT_TRUSTED"], [], matched
    if info.get("api_allowed") is True and source.get("api_allowed") is False:
        return False, ["API_SOURCE_USED_WHILE_API_BLOCKED"], ["api_allowed_context"], matched
    if info.get("requires_identity") is True and source.get("identity_present") is False:
        return False, ["SOURCE_IDENTITY_REQUIRED"], ["identity_context"], matched

    return True, [], [], matched


def evaluate_payg_rpc(request, registry):
    domain = _domain(registry, "payg_rpc")
    rpc = _as_dict(request.get("rpc"))
    matched = {
        "domains.payg_rpc.default_mode": domain.get("default_mode"),
        "domains.payg_rpc.manual_approval_required_for_any_payg_real": domain.get("manual_approval_required_for_any_payg_real"),
    }
    reasons = []
    required = []

    chain = str(rpc.get("chain") or "").strip()
    provider_key = str(rpc.get("provider_key") or "").strip()
    method = str(rpc.get("method") or "").strip()

    if chain not in list(domain.get("allowed_chains") or []):
        reasons.append("RPC_CHAIN_NOT_ALLOWED")
    if provider_key not in list(domain.get("allowed_provider_keys") or []):
        reasons.append("RPC_PROVIDER_NOT_ALLOWED")
    if method not in list(domain.get("allowed_methods") or []):
        reasons.append("RPC_METHOD_NOT_ALLOWED")

    forbidden = _as_dict(domain.get("forbidden"))
    if forbidden.get("secret_print") is True and rpc.get("prints_secret") is True:
        reasons.append("SECRET_PRINT_FORBIDDEN")
    if forbidden.get("full_url_print") is True and rpc.get("prints_full_url") is True:
        reasons.append("FULL_URL_PRINT_FORBIDDEN")
    if forbidden.get("ssl_verify_disabled") is True and rpc.get("ssl_verify_disabled") is True:
        reasons.append("SSL_VERIFY_DISABLED_FORBIDDEN")
    if forbidden.get("unplanned_rpc_method") is True and rpc.get("planned") is False:
        reasons.append("UNPLANNED_RPC_METHOD_FORBIDDEN")
    if forbidden.get("unplanned_historical_scan") is True and rpc.get("historical_scan") is True:
        reasons.append("UNPLANNED_HISTORICAL_SCAN_FORBIDDEN")
    if forbidden.get("genesis_scan_without_budget") is True and rpc.get("genesis_scan_without_budget") is True:
        reasons.append("GENESIS_SCAN_WITHOUT_BUDGET_FORBIDDEN")

    limits = _as_dict(domain.get("limits"))
    span = rpc.get("getlogs_block_span")
    soft_cap = limits.get("single_getlogs_block_span_default_soft_cap")
    if span is not None and soft_cap is not None:
        try:
            if int(span) > int(soft_cap):
                reasons.append("GETLOGS_BLOCK_SPAN_REQUIRES_SEPARATE_PLAN")
                required.append("separate_getlogs_plan")
        except Exception:
            reasons.append("GETLOGS_BLOCK_SPAN_INVALID")

    if rpc.get("is_real") is True or str(request.get("mode") or "").lower() == "real":
        if domain.get("manual_approval_required_for_any_payg_real") is True:
            required.append("approval_allow")

    matched["domains.payg_rpc.allowed_chains"] = domain.get("allowed_chains")
    matched["domains.payg_rpc.allowed_provider_keys"] = domain.get("allowed_provider_keys")
    matched["domains.payg_rpc.allowed_methods"] = domain.get("allowed_methods")
    return not reasons, reasons, required, matched


def evaluate_db_write(request, registry):
    domain = _domain(registry, "db_write")
    write = _as_dict(request.get("write"))
    matched = {
        "domains.db_write.default": domain.get("default"),
        "domains.db_write.allowed_modes": domain.get("allowed_modes"),
        "domains.db_write.live_db_write_by_default": domain.get("live_db_write_by_default"),
    }
    reasons = []
    required = []

    mode = str(write.get("mode") or request.get("mode") or "").lower()
    allowed_modes = set(domain.get("allowed_modes") or [])

    if mode in allowed_modes and write.get("target_hot_path") is not True:
        return True, [], [], matched

    if write.get("writes_db") is True or request.get("operation_type") == "db_write":
        reasons.append("DB_WRITE_DENIED_BY_POLICY")
        for control in list(domain.get("real_write_requires") or []):
            required.append(str(control))

    return not reasons, reasons, required, matched


def evaluate_dashboard(request, registry):
    domain = _domain(registry, "dashboard")
    dashboard = _as_dict(request.get("dashboard"))
    matched = {
        "domains.dashboard.render_allowed": domain.get("render_allowed"),
        "domains.dashboard.preview_allowed": domain.get("preview_allowed"),
        "domains.dashboard.active_panel_mutation_allowed": domain.get("active_panel_mutation_allowed"),
    }
    reasons = []
    required = []

    if dashboard.get("active_panel_mutation") is True or request.get("operation_type") == "dashboard_active_mutation":
        if domain.get("active_panel_mutation_allowed") is not True:
            reasons.append("DASHBOARD_ACTIVE_MUTATION_DENIED")
            if domain.get("active_panel_mutation_requires_separate_explicit_approval") is True:
                required.append("approval_allow")

    if dashboard.get("render") is True and domain.get("render_allowed") is not True:
        reasons.append("DASHBOARD_RENDER_DENIED")
    if dashboard.get("preview") is True and domain.get("preview_allowed") is not True:
        reasons.append("DASHBOARD_PREVIEW_DENIED")
    if dashboard.get("copy_assets") is True and domain.get("copy_assets_by_default") is False:
        reasons.append("DASHBOARD_COPY_ASSETS_DENIED")

    return not reasons, reasons, required, matched


def evaluate_secret(request, registry):
    domain = _domain(registry, "secret")
    secret = _as_dict(request.get("secret"))
    matched = {
        "domains.secret.status_allowed": domain.get("status_allowed"),
        "domains.secret.raw_read_allowed": domain.get("raw_read_allowed"),
        "domains.secret.update_allowed": domain.get("update_allowed"),
        "domains.secret.provider_test_allowed": domain.get("provider_test_allowed"),
        "domains.secret.forbid_secret_value_return": domain.get("forbid_secret_value_return"),
    }
    reasons = []
    required = []

    if secret.get("status") is True and domain.get("status_allowed") is not True:
        reasons.append("SECRET_STATUS_DENIED")
    if secret.get("raw_read") is True or request.get("operation_type") == "secret_raw_read":
        if domain.get("raw_read_allowed") is not True:
            reasons.append("SECRET_RAW_READ_DENIED")
    if secret.get("update") is True or request.get("operation_type") == "secret_update":
        if domain.get("update_allowed") is not True:
            reasons.append("SECRET_UPDATE_DENIED")
            required.extend(["authority_allow", "approval_allow", "authentication"])
    if secret.get("provider_test") is True or request.get("operation_type") == "secret_provider_test":
        if domain.get("provider_test_allowed") is not True:
            reasons.append("SECRET_PROVIDER_TEST_DENIED")
            required.extend(["authority_allow", "approval_allow", "budget_guard", "authentication"])

    if secret.get("returns_secret_value") is True and domain.get("forbid_secret_value_return") is True:
        reasons.append("SECRET_VALUE_RETURN_FORBIDDEN")

    return not reasons, reasons, required, matched


def evaluate_schema_apply(request, registry):
    domain = _domain(registry, "schema_apply")
    schema = _as_dict(request.get("schema"))
    matched = {
        "domains.schema_apply.default": domain.get("default"),
        "domains.schema_apply.canonical_sql_reference_only": domain.get("canonical_sql_reference_only"),
        "domains.schema_apply.live_apply_allowed": domain.get("live_apply_allowed"),
    }
    reasons = []
    required = []

    if schema.get("apply") is True or request.get("operation_type") == "schema_apply":
        reasons.append("SCHEMA_APPLY_DENIED_BY_POLICY")
        required.extend(str(v) for v in list(domain.get("requires") or []))
    if schema.get("live_apply") is True and domain.get("live_apply_allowed") is not True:
        reasons.append("SCHEMA_LIVE_APPLY_DENIED")

    return not reasons, reasons, required, matched


def evaluate_logging_redaction(request, registry):
    domain = _domain(registry, "logging_redaction")
    logging = _as_dict(request.get("logging"))
    matched = {
        "domains.logging_redaction.secret_print_forbidden": domain.get("secret_print_forbidden"),
        "domains.logging_redaction.full_url_print_forbidden": domain.get("full_url_print_forbidden"),
        "domains.logging_redaction.large_payload_dump_forbidden": domain.get("large_payload_dump_forbidden"),
    }
    reasons = []
    required = []

    if logging.get("prints_secret") is True and domain.get("secret_print_forbidden") is True:
        reasons.append("SECRET_PRINT_FORBIDDEN")
    if logging.get("prints_full_url") is True and domain.get("full_url_print_forbidden") is True:
        reasons.append("FULL_URL_PRINT_FORBIDDEN")
    if logging.get("prints_large_payload") is True and domain.get("large_payload_dump_forbidden") is True:
        reasons.append("LARGE_PAYLOAD_DUMP_FORBIDDEN")

    sensitive = set(domain.get("redaction_required_fields") or [])
    fields = set(str(f) for f in list(logging.get("fields") or []))
    if sensitive.intersection(fields):
        required.append("redaction")

    return not reasons, reasons, required, matched


def evaluate_policy(request, authority_decision=None, approval_decision=None, registry=None):
    """Evaluate project policy for a request.

    The evaluator fails closed for missing config, invalid config, malformed
    request, unknown domain, authority denial, approval absence for sensitive
    operations, and any explicit policy denial.
    """
    loaded = None
    if registry is None:
        loaded = load_policy_registry()
        if not loaded.get("ok"):
            return _decision(
                False,
                reason_codes=[loaded.get("error") or "POLICY_REGISTRY_LOAD_FAILED"],
                required_controls=["valid_policy_registry"],
                audit={"config_path": loaded.get("path", "")},
            )
        registry = loaded.get("registry")

    validation = validate_policy_registry(registry)
    if not validation.get("ok"):
        return _decision(
            False,
            reason_codes=validation.get("errors"),
            required_controls=["valid_policy_registry"],
            audit={"warnings": validation.get("warnings", [])},
        )

    classified = classify_policy_request(request)
    domain = classified.get("domain", "unknown")
    operation_type = classified.get("operation_type", "unknown")
    operation_id = classified.get("operation_id", "")

    if not classified.get("ok"):
        return _decision(
            False,
            domain=domain,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=classified.get("errors"),
            required_controls=["well_formed_policy_request"],
            audit={"classification": classified},
        )

    auth_reasons, auth_required = _gate_authority_and_approval(
        classified["request"],
        authority_decision,
        approval_decision,
    )
    if auth_reasons:
        return _decision(
            False,
            domain=domain,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=sorted(set(auth_reasons)),
            required_controls=sorted(set(auth_required)),
            audit={
                "policy_schema_version": registry.get("schema_version"),
                "authority_dominates_policy": True,
            },
        )

    evaluators = {
        "source_trust": evaluate_source_trust,
        "payg_rpc": evaluate_payg_rpc,
        "db_write": evaluate_db_write,
        "dashboard": evaluate_dashboard,
        "secret": evaluate_secret,
        "schema_apply": evaluate_schema_apply,
        "logging_redaction": evaluate_logging_redaction,
    }

    evaluator = evaluators.get(domain)
    if evaluator is None:
        return _decision(
            False,
            domain=domain,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=[f"POLICY_DOMAIN_NOT_EVALUATABLE:{domain}"],
            required_controls=["supported_policy_domain"],
            audit={"policy_schema_version": registry.get("schema_version")},
        )

    ok, reasons, required, matched = evaluator(classified["request"], registry)
    if not ok or reasons:
        return _decision(
            False,
            domain=domain,
            operation_type=operation_type,
            operation_id=operation_id,
            reason_codes=sorted(set(reasons)),
            required_controls=sorted(set(required)),
            matched_policy=matched,
            audit={
                "policy_schema_version": registry.get("schema_version"),
                "fail_closed": True,
            },
        )

    return _decision(
        True,
        domain=domain,
        operation_type=operation_type,
        operation_id=operation_id,
        reason_codes=[],
        required_controls=sorted(set(required)),
        matched_policy=matched,
        audit={
            "policy_schema_version": registry.get("schema_version"),
            "fail_closed": True,
        },
    )


def explain_policy_decision(decision):
    """Return a short human-readable explanation for a policy decision."""
    if not isinstance(decision, dict):
        return "DENY: malformed policy decision"

    status = str(decision.get("decision") or "DENY")
    domain = str(decision.get("domain") or "unknown")
    operation_type = str(decision.get("operation_type") or "unknown")
    reasons = decision.get("reason_codes") or []

    if status == "ALLOW":
        return f"ALLOW: policy permits {operation_type} in {domain}"
    if reasons:
        return f"DENY: {operation_type} in {domain} blocked by " + ", ".join(str(r) for r in reasons)
    return f"DENY: {operation_type} in {domain} blocked by fail-closed policy"
