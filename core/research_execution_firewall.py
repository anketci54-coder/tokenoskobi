from typing import Any, Iterable

RESEARCH_SCHEMA="era57_research_report_v1"

ALLOWED=frozenset({
"schema","report_id","research_question","scope","status",
"executive_summary","claims","unknowns","contradictions","sources",
"confidence","limitations","human_review_required","executable",
"actionable","decision_eligible","created_at"
})

REQUIRED=frozenset({
"schema","report_id","research_question","status","claims","unknowns",
"contradictions","sources","confidence","limitations",
"human_review_required","executable","actionable","decision_eligible"
})

FORBIDDEN=frozenset({
"order_side","order_type","order_size","quantity","amount","entry_price",
"stop_loss","take_profit","slippage","gas_limit","nonce","signature",
"private_key","transaction_payload","execution_deadline","router_address",
"wallet_address_for_execution"
})

STATUSES=frozenset({
"COMPLETED_VERIFIED","COMPLETED_WITH_LIMITATIONS",
"INCOMPLETE_EVIDENCE","UNRESOLVED_CONTRADICTION"
})

class ResearchExecutionHardReject(RuntimeError):
    pass

def _keys(v:Any)->Iterable[str]:
    if isinstance(v,dict):
        for k,x in v.items():
            yield str(k).lower()
            yield from _keys(x)
    elif isinstance(v,list):
        for x in v:
            yield from _keys(x)

def _result(reasons):
    reasons=sorted(set(reasons))
    return {"ok":not reasons,"decision":"ALLOW" if not reasons else "DENY",
            "reason_codes":reasons,"fail_closed":True}

def validate_research_report(v:Any):
    if not isinstance(v,dict):
        return _result(["RESEARCH_OBJECT_REQUIRED"])
    reasons=[]
    reasons += ["MISSING_FIELD:"+x for x in sorted(REQUIRED-set(v))]
    reasons += ["UNEXPECTED_FIELD:"+x for x in sorted(set(v)-ALLOWED)]
    if v.get("schema")!=RESEARCH_SCHEMA:
        reasons.append("RESEARCH_SCHEMA_MISMATCH")
    if v.get("status") not in STATUSES:
        reasons.append("RESEARCH_STATUS_INVALID")
    for k in ("executable","actionable","decision_eligible"):
        if v.get(k) is not False:
            reasons.append(k.upper()+"_MUST_BE_FALSE")
    if v.get("human_review_required") is not True:
        reasons.append("HUMAN_REVIEW_REQUIRED")
    reasons += ["FORBIDDEN_EXECUTION_FIELD:"+x
                for x in sorted(set(_keys(v))&FORBIDDEN)]
    return _result(reasons)

TRUSTED_EXECUTION_SCHEMAS=frozenset()

def validate_execution_input(v:Any,allowed_schemas=()):
    if not isinstance(v,dict):
        return _result(["EXECUTION_OBJECT_REQUIRED"])

    if tuple(allowed_schemas):
        return _result([
            "CALLER_CONTROLLED_EXECUTION_ALLOWLIST_REJECTED"
        ])

    schema=str(v.get("schema") or "")

    if schema==RESEARCH_SCHEMA or schema.startswith("era57_"):
        return _result([
            "RESEARCH_SCHEMA_EXECUTION_HARD_REJECT"
        ])

    if schema not in TRUSTED_EXECUTION_SCHEMAS:
        return _result([
            "EXECUTION_SCHEMA_NOT_ALLOWLISTED"
        ])

    return _result([])

def enforce_execution_input(v:Any,allowed_schemas=()):
    result=validate_execution_input(v,allowed_schemas)
    if not result["ok"]:
        raise ResearchExecutionHardReject(",".join(result["reason_codes"]))
    return result
