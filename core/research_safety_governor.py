
from datetime import datetime, timezone
from typing import Any
import hashlib
import re

INJECTION_PATTERNS = (
    r"ignore\s+(all\s+)?previous",
    r"system\s+(message|prompt)",
    r"reveal\s+(the\s+)?secret",
    r"execute\s+(this|the following)",
    r"disable\s+(security|policy)",
    r"override\s+(policy|instructions)",
)

DEFAULT_POLICY = {
    "max_iterations": 20,
    "max_total_tokens": 100000,
    "max_total_cost_units": 1000,
    "max_wall_seconds": 900,
    "max_sources": 100,
    "max_duplicate_fingerprint": 2,
    "max_no_gain_streak": 3,
    "minimum_gain_delta": 0.01,
    "paid_api_authorized": False,
}

def deny(reasons):
    return {
        "ok": False,
        "decision": "FAIL_CLOSED",
        "reason_codes": sorted(set(reasons)),
        "fail_closed": True,
    }

def parse_utc(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("TIMESTAMP_REQUIRED")

    text = value.strip()

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    parsed = datetime.fromisoformat(text)

    if parsed.tzinfo is None:
        raise ValueError("TIMEZONE_REQUIRED")

    return parsed.astimezone(timezone.utc)

def validate_adversarial_context(
    envelope: Any,
    source_observed_at: str,
    now_utc: str,
    declared_as_of: str | None = None,
    max_age_seconds: int = 86400,
    max_future_skew_seconds: int = 300,
    max_context_drift_seconds: int = 300,
):
    if not isinstance(envelope, dict):
        return deny(["ENVELOPE_OBJECT_REQUIRED"])

    reasons = []

    if envelope.get("schema") != \
            "era57_network_disabled_synthesis_v1":
        reasons.append("SYNTHESIS_SCHEMA_MISMATCH")

    if envelope.get("logical_policy_only") is not True:
        reasons.append("LOGICAL_POLICY_LOCK_MISSING")

    if envelope.get("runtime_bound") is not False:
        reasons.append("RUNTIME_BOUND_NOT_FALSE")

    if envelope.get("tools_available") is not False:
        reasons.append("TOOLS_AVAILABLE_NOT_FALSE")

    if envelope.get("content_role") != \
            "EXTERNAL_DATA_NOT_INSTRUCTION":
        reasons.append("CONTENT_ROLE_INVALID")

    content = envelope.get("quarantined_content")

    if not isinstance(content, dict):
        reasons.append("QUARANTINED_CONTENT_REQUIRED")
        content = {}

    if content.get("tainted_external_content") is not True:
        reasons.append("TAINT_LABEL_REQUIRED")

    if content.get("active_content_executed") is not False:
        reasons.append("ACTIVE_CONTENT_EXECUTION_NOT_FALSE")

    if content.get("content_role") != \
            "EXTERNAL_DATA_NOT_INSTRUCTION":
        reasons.append("QUARANTINED_CONTENT_ROLE_INVALID")

    try:
        source_time = parse_utc(source_observed_at)
        now_time = parse_utc(now_utc)

        future_seconds = (source_time - now_time).total_seconds()
        age_seconds = (now_time - source_time).total_seconds()

        if future_seconds > max_future_skew_seconds:
            reasons.append("FUTURE_TIME_CONTEXT_POISONING")

        if age_seconds > max_age_seconds:
            reasons.append("STALE_TIME_CONTEXT")

        if declared_as_of is not None:
            declared_time = parse_utc(declared_as_of)
            drift = abs(
                (declared_time - source_time).total_seconds()
            )

            if drift > max_context_drift_seconds:
                reasons.append("DECLARED_TIME_CONTEXT_MISMATCH")

    except ValueError as exc:
        reasons.append(str(exc))

    text = str(content.get("normalized_text") or "")
    indicators = []

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            indicators.append(pattern)

    fingerprint = hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()

    if reasons:
        result = deny(reasons)
        result["adversarial_indicators"] = indicators
        result["content_fingerprint"] = fingerprint
        return result

    return {
        "ok": True,
        "decision": "ALLOW_CONTAINED_DATA_ONLY",
        "reason_codes": [],
        "adversarial_indicators": indicators,
        "content_fingerprint": fingerprint,
        "instruction_authority": False,
        "actionable": False,
        "execution_eligible": False,
        "human_review_required": True,
        "fail_closed": True,
    }

def evaluate_iteration(
    state: Any,
    request: Any,
    policy: Any = None,
):
    if not isinstance(state,dict):
        return deny(["STATE_OBJECT_REQUIRED"])

    if not isinstance(request,dict):
        return deny(["REQUEST_OBJECT_REQUIRED"])

    rules=dict(DEFAULT_POLICY)

    if policy is not None:
        if not isinstance(policy,dict):
            return deny(["POLICY_OBJECT_REQUIRED"])
        rules.update(policy)

    reasons=[]

    state_keys=(
        "iterations",
        "total_tokens",
        "total_cost_units",
        "wall_seconds",
        "source_count",
        "no_gain_streak"
    )

    request_keys=(
        "estimated_tokens",
        "estimated_cost_units",
        "wall_seconds_delta",
        "new_sources"
    )

    for key in state_keys:
        value=state.get(key,0)
        if (
            isinstance(value,bool)
            or not isinstance(value,(int,float))
        ):
            reasons.append(
                "STATE_NUMERIC_VALUE_REQUIRED:"+key
            )
        elif value<0:
            reasons.append(
                "NEGATIVE_STATE_VALUE:"+key
            )

    for key in request_keys:
        value=request.get(key,0)
        if (
            isinstance(value,bool)
            or not isinstance(value,(int,float))
        ):
            reasons.append(
                "REQUEST_NUMERIC_VALUE_REQUIRED:"+key
            )
        elif value<0:
            reasons.append(
                "NEGATIVE_REQUEST_VALUE:"+key
            )

    counts=state.get("fingerprint_counts",{})

    if not isinstance(counts,dict):
        reasons.append(
            "FINGERPRINT_COUNTS_OBJECT_REQUIRED"
        )

    if (
        request.get("paid_api_requested") is True
        and rules.get("paid_api_authorized") is not True
    ):
        reasons.append("PAID_API_NOT_AUTHORIZED")

    if reasons:
        value=deny(reasons)
        value["updated_state"]=None
        value["partial_output_actionable"]=False
        return value

    projected={
        "iterations":
            int(state.get("iterations",0))+1,
        "total_tokens":
            int(state.get("total_tokens",0))
            +int(request.get("estimated_tokens",0)),
        "total_cost_units":
            float(state.get("total_cost_units",0))
            +float(request.get("estimated_cost_units",0)),
        "wall_seconds":
            float(state.get("wall_seconds",0))
            +float(request.get("wall_seconds_delta",0)),
        "source_count":
            int(state.get("source_count",0))
            +int(request.get("new_sources",0))
    }

    limits={
        "iterations":"max_iterations",
        "total_tokens":"max_total_tokens",
        "total_cost_units":"max_total_cost_units",
        "wall_seconds":"max_wall_seconds",
        "source_count":"max_sources"
    }

    for key,limit_key in limits.items():
        if projected[key]>rules[limit_key]:
            reasons.append(
                "RESOURCE_LIMIT_EXCEEDED:"+key
            )

    fingerprint=str(
        request.get("fingerprint") or ""
    ).strip()

    updated_counts=dict(counts)

    if not fingerprint:
        reasons.append("FINGERPRINT_REQUIRED")
    else:
        updated_counts[fingerprint]=(
            updated_counts.get(fingerprint,0)+1
        )

        if (
            updated_counts[fingerprint]
            >rules["max_duplicate_fingerprint"]
        ):
            reasons.append(
                "DUPLICATE_LOOP_DETECTED"
            )

    gain=float(
        request.get("expected_gain_delta",0)
    )

    if gain<rules["minimum_gain_delta"]:
        no_gain=int(
            state.get("no_gain_streak",0)
        )+1
    else:
        no_gain=0

    if no_gain>=rules["max_no_gain_streak"]:
        reasons.append("NO_GAIN_LOOP_DETECTED")

    if reasons:
        value=deny(reasons)
        value["updated_state"]=None
        value["partial_output_actionable"]=False
        return value

    projected.update({
        "fingerprint_counts":updated_counts,
        "no_gain_streak":no_gain
    })

    return {
        "ok":True,
        "decision":"ALLOW_BOUNDED_ITERATION",
        "reason_codes":[],
        "updated_state":projected,
        "partial_output_actionable":False,
        "paid_api_authorized":
            rules["paid_api_authorized"],
        "fail_closed":True
    }

