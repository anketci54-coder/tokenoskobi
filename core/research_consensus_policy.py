
from typing import Any

VALID_REPORT_STATUSES = {
    "COMPLETED_VERIFIED",
    "COMPLETED_WITH_LIMITATIONS",
    "INCOMPLETE_EVIDENCE",
    "UNRESOLVED_CONTRADICTION",
}

def deny(reasons):
    return {
        "ok": False,
        "decision": "FAIL_CLOSED",
        "reason_codes": sorted(set(reasons)),
        "fail_closed": True,
    }

def assess_claim(
    claim_id: str,
    model_outputs: Any,
    evidence_items: Any,
    minimum_independent_sources: int = 2,
    source_registry: Any = None,
):
    if not isinstance(model_outputs,list):
        return deny(["MODEL_OUTPUT_LIST_REQUIRED"])

    if not isinstance(evidence_items,list):
        return deny(["EVIDENCE_ITEM_LIST_REQUIRED"])

    if minimum_independent_sources<2:
        return deny([
            "MINIMUM_INDEPENDENT_SOURCE_POLICY_INVALID"
        ])

    model_votes={}

    for item in model_outputs:
        if not isinstance(item,dict):
            return deny(["MODEL_OUTPUT_OBJECT_REQUIRED"])

        if item.get("claim_id")!=claim_id:
            continue

        model_id=str(item.get("model_id") or "").strip()
        stance=str(item.get("stance") or "").upper()

        if model_id and stance in {
            "SUPPORT","OPPOSE","UNCERTAIN"
        }:
            model_votes[model_id]=stance

    decisive=[
        value for value in model_votes.values()
        if value!="UNCERTAIN"
    ]

    model_consensus=(
        len(decisive)>=2
        and len(set(decisive))==1
    )

    registry_valid=isinstance(source_registry,dict)
    support_groups=set()
    contradiction_groups=set()
    untrusted_sources=set()

    for item in evidence_items:
        if not isinstance(item,dict):
            return deny(["EVIDENCE_ITEM_OBJECT_REQUIRED"])

        if item.get("claim_id")!=claim_id:
            continue

        if item.get("verified") is not True:
            continue

        source_id=str(
            item.get("independence_key") or ""
        ).strip()

        if not source_id:
            continue

        metadata=(
            source_registry.get(source_id)
            if registry_valid else None
        )

        if (
            not isinstance(metadata,dict)
            or metadata.get("active") is not True
            or metadata.get(
                "verified_independent"
            ) is not True
        ):
            untrusted_sources.add(source_id)
            continue

        group=str(
            metadata.get("independence_group") or ""
        ).strip()

        if not group:
            untrusted_sources.add(source_id)
            continue

        if item.get("supports") is True:
            support_groups.add(group)

        if item.get("contradicts") is True:
            contradiction_groups.add(group)

    evidence_consensus=(
        len(support_groups)>=minimum_independent_sources
        and not contradiction_groups
    )

    reasons=[]

    if evidence_items and not registry_valid:
        reasons.append(
            "SOURCE_INDEPENDENCE_REGISTRY_REQUIRED"
        )

    if untrusted_sources:
        reasons.append(
            "UNTRUSTED_SOURCE_INDEPENDENCE_CLAIM"
        )

    if model_consensus and not evidence_consensus:
        reasons.append(
            "MODEL_CONSENSUS_NOT_EVIDENCE"
        )

    if contradiction_groups:
        reasons.append(
            "EVIDENCE_CONTRADICTION_PRESENT"
        )

    if not evidence_consensus:
        reasons.append(
            "INDEPENDENT_EVIDENCE_CONSENSUS_MISSING"
        )

    return {
        "ok":True,
        "decision":(
            "EVIDENCE_SUPPORTED"
            if evidence_consensus
            else "EVIDENCE_NOT_ESTABLISHED"
        ),
        "claim_id":claim_id,
        "model_consensus":model_consensus,
        "model_count":len(model_votes),
        "evidence_consensus":evidence_consensus,
        "independent_support_count":
            len(support_groups),
        "independent_contradiction_count":
            len(contradiction_groups),
        "source_registry_verified":
            registry_valid,
        "reason_codes":sorted(set(reasons)),
        "actionable":False,
        "decision_eligible":False,
        "execution_eligible":False,
        "human_review_required":True,
        "fail_closed":True
    }

def assess_report(report: Any, claim_assessments: Any):
    if not isinstance(report, dict):
        return deny(["REPORT_OBJECT_REQUIRED"])

    if not isinstance(claim_assessments, list):
        return deny(["CLAIM_ASSESSMENT_LIST_REQUIRED"])

    status = report.get("status")

    if status not in VALID_REPORT_STATUSES:
        return deny(["REPORT_STATUS_INVALID"])

    claims = report.get("claims")

    if not isinstance(claims, list):
        return deny(["REPORT_CLAIM_LIST_REQUIRED"])

    assessment_map = {
        item.get("claim_id"): item
        for item in claim_assessments
        if isinstance(item, dict) and item.get("claim_id")
    }

    reasons = []

    complete = (
        report.get("complete") is True
        and status in {
            "COMPLETED_VERIFIED",
            "COMPLETED_WITH_LIMITATIONS",
        }
    )

    if not complete:
        reasons.append("REPORT_INCOMPLETE")

    contradictions = report.get("contradictions", [])

    if not isinstance(contradictions, list):
        return deny(["REPORT_CONTRADICTION_LIST_REQUIRED"])

    if contradictions or status == "UNRESOLVED_CONTRADICTION":
        reasons.append("UNRESOLVED_CONTRADICTION")

    for claim_id in claims:
        assessment = assessment_map.get(claim_id)

        if not assessment:
            reasons.append(
                "CLAIM_ASSESSMENT_MISSING:" + str(claim_id)
            )
            continue

        if assessment.get("evidence_consensus") is not True:
            reasons.append(
                "EVIDENCE_CONSENSUS_MISSING:" + str(claim_id)
            )

        if assessment.get(
            "independent_contradiction_count", 0
        ) > 0:
            reasons.append(
                "CLAIM_CONTRADICTION_PRESENT:" + str(claim_id)
            )

    quality_gate_passed = not reasons

    return {
        "ok": True,
        "decision": (
            "RESEARCH_QUALITY_PASS_NON_ACTIONABLE"
            if quality_gate_passed
            else "NON_ACTIONABLE"
        ),
        "research_quality_gate_passed": quality_gate_passed,
        "reason_codes": sorted(set(reasons)),
        "actionable": False,
        "decision_eligible": False,
        "execution_eligible": False,
        "trade_eligible": False,
        "wallet_eligible": False,
        "human_review_required": True,
        "fail_closed": True,
    }
