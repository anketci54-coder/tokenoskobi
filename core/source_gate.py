#!/usr/bin/env python3
from .identity import normalize_chain

SOURCE_TRUST = {
    "MANUAL_PILOT": {
        "trusted": True,
        "api_allowed": False,
        "requires_identity": True,
        "max_age_seconds": None,
    },
    "LOCAL_PILOT_SEED": {
        "trusted": True,
        "api_allowed": False,
        "requires_identity": True,
        "max_age_seconds": None,
    },
    "DEXSCREENER_CAPPED_REFRESH": {
        "trusted": True,
        "api_allowed": True,
        "requires_identity": True,
        "max_age_seconds": 900,
    },
}

def validate_source(source, api_allowed=False):
    s = str(source or "").strip()
    if not s:
        return {"ok": False, "errors": [{"code": "SOURCE_EMPTY"}], "source": s}
    info = SOURCE_TRUST.get(s)
    if not info:
        return {"ok": False, "errors": [{"code": "SOURCE_UNKNOWN", "source": s}], "source": s}
    if info.get("api_allowed") and not api_allowed:
        return {"ok": False, "errors": [{"code": "API_SOURCE_USED_WHILE_API_BLOCKED", "source": s}], "source": s}
    return {"ok": True, "errors": [], "source": s, "policy": info}

def route_from_quality(hard_fail=False, medium_risk=False, high_opportunity=False):
    if hard_fail:
        return "REJECT"
    if medium_risk and high_opportunity:
        return "WATCH_ONLY"
    if high_opportunity:
        return "MICRO_OBSERVE"
    return "WATCH_ONLY"
