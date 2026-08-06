#!/usr/bin/env python3
"""
PAYG RPC Budget Guard V1 - DRYRUN DRAFT.
No network. No secrets. No provider calls.
"""
def guard_eval(policy, state, req):
    reasons = []
    method = req.get("method")
    chain = req.get("chain")
    provider_key = req.get("provider_key")
    phase_id = req.get("phase_id")
    is_real = bool(req.get("is_real"))
    approval_matched = bool(req.get("approval_matched"))
    requested_calls = int(req.get("requested_calls", 0) or 0)
    getlogs_calls = int(req.get("getlogs_calls", 0) or 0)
    max_block_span = int(req.get("max_block_span", 0) or 0)
    target_scope = req.get("target_scope")
    raw_archive_sanitized_path = req.get("raw_archive_sanitized_path")

    if policy.get("default_mode") != "LOCKED_UNTIL_PHASE_APPROVED":
        reasons.append("POLICY_DEFAULT_MODE_NOT_LOCKED")
    if is_real and not approval_matched:
        reasons.append("REAL_REQUIRES_EXPLICIT_APPROVAL")
    if provider_key not in policy.get("allowed_provider_keys", []):
        reasons.append("UNKNOWN_PROVIDER")
    if chain not in policy.get("allowed_chains", []):
        reasons.append("UNKNOWN_CHAIN")
    if method not in policy.get("allowed_methods", []):
        reasons.append("UNKNOWN_METHOD")
    if not phase_id:
        reasons.append("PHASE_ID_REQUIRED")
    if not target_scope:
        reasons.append("TARGET_SCOPE_REQUIRED")
    if not raw_archive_sanitized_path:
        reasons.append("RAW_ARCHIVE_SANITIZED_PATH_REQUIRED")

    limits = policy.get("limits", {})
    if requested_calls > int(limits.get("single_phase_rpc_call_default_hard_cap", 0)):
        reasons.append("PHASE_RPC_CALL_HARD_CAP_EXCEEDED")
    if getlogs_calls > int(limits.get("single_phase_getlogs_call_default_hard_cap", 0)):
        reasons.append("PHASE_GETLOGS_CALL_HARD_CAP_EXCEEDED")
    if method == "eth_getLogs" and max_block_span > int(limits.get("single_getlogs_block_span_default_soft_cap", 0)):
        reasons.append("GETLOGS_BLOCK_SPAN_REQUIRES_SEPARATE_PLAN")
    if int(state.get("daily_rpc_calls_used", 0)) + requested_calls > int(limits.get("global_daily_rpc_call_hard_cap", 0)):
        reasons.append("DAILY_RPC_HARD_CAP_EXCEEDED")
    if bool(req.get("prints_secret")):
        reasons.append("SECRET_PRINT_FORBIDDEN")
    if bool(req.get("prints_full_url")):
        reasons.append("FULL_URL_PRINT_FORBIDDEN")
    if bool(req.get("ssl_verify_disabled")):
        reasons.append("SSL_VERIFY_DISABLE_FORBIDDEN")
    if bool(req.get("historical_scan")) and not bool(req.get("historical_budget_phase_approved")):
        reasons.append("HISTORICAL_SCAN_REQUIRES_SEPARATE_BUDGET_PHASE")

    return {
        "allowed": len(reasons) == 0,
        "reasons": reasons,
        "decision": "ALLOW_DRYRUN_REQUEST_SHAPE" if len(reasons) == 0 else "BLOCK_REQUEST",
    }
