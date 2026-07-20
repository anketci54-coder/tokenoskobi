
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.research_consensus_policy import (
    assess_claim,
    assess_report,
)

def models_same():
    return [
        {
            "claim_id": "c1",
            "model_id": "m1",
            "stance": "SUPPORT",
        },
        {
            "claim_id": "c1",
            "model_id": "m2",
            "stance": "SUPPORT",
        },
    ]

def evidence_two():
    return [
        {
            "claim_id": "c1",
            "independence_key": "source-a",
            "verified": True,
            "supports": True,
        },
        {
            "claim_id": "c1",
            "independence_key": "source-b",
            "verified": True,
            "supports": True,
        },
    ]


def registry():
    return {
        "source-a": {
            "active": True,
            "verified_independent": True,
            "independence_group": "group-a",
        },
        "source-b": {
            "active": True,
            "verified_independent": True,
            "independence_group": "group-b",
        },
        "source-c": {
            "active": True,
            "verified_independent": True,
            "independence_group": "group-c",
        },
    }

class Tests(unittest.TestCase):
    def test_models_not_evidence(self):
        value = assess_claim("c1", models_same(), [])
        self.assertTrue(value["model_consensus"])
        self.assertFalse(value["evidence_consensus"])

    def test_independent_evidence_consensus(self):
        value = assess_claim("c1", [], evidence_two(), source_registry=registry())
        self.assertTrue(value["evidence_consensus"])

    def test_duplicate_source_not_independent(self):
        evidence = evidence_two()
        evidence[1]["independence_key"] = "source-a"
        value = assess_claim("c1", [], evidence, source_registry=registry())
        self.assertFalse(value["evidence_consensus"])

    def test_unverified_source_ignored(self):
        evidence = evidence_two()
        evidence[1]["verified"] = False
        value = assess_claim("c1", [], evidence, source_registry=registry())
        self.assertFalse(value["evidence_consensus"])

    def test_contradiction_blocks_consensus(self):
        evidence = evidence_two()
        evidence.append({
            "claim_id": "c1",
            "independence_key": "source-c",
            "verified": True,
            "contradicts": True,
        })
        value = assess_claim("c1", models_same(), evidence, source_registry=registry())
        self.assertFalse(value["evidence_consensus"])

    def test_incomplete_report_non_actionable(self):
        claim = assess_claim("c1", [], evidence_two(), source_registry=registry())
        report = {
            "status": "INCOMPLETE_EVIDENCE",
            "complete": False,
            "claims": ["c1"],
            "contradictions": [],
        }
        value = assess_report(report, [claim])
        self.assertFalse(value["actionable"])
        self.assertFalse(value["research_quality_gate_passed"])

    def test_unresolved_contradiction_non_actionable(self):
        claim = assess_claim("c1", [], evidence_two(), source_registry=registry())
        report = {
            "status": "UNRESOLVED_CONTRADICTION",
            "complete": True,
            "claims": ["c1"],
            "contradictions": ["conflict"],
        }
        value = assess_report(report, [claim])
        self.assertFalse(value["research_quality_gate_passed"])

    def test_verified_quality_still_non_actionable(self):
        claim = assess_claim("c1", [], evidence_two(), source_registry=registry())
        report = {
            "status": "COMPLETED_VERIFIED",
            "complete": True,
            "claims": ["c1"],
            "contradictions": [],
        }
        value = assess_report(report, [claim])
        self.assertTrue(value["research_quality_gate_passed"])
        self.assertFalse(value["actionable"])
        self.assertFalse(value["execution_eligible"])

    def test_missing_claim_assessment_blocks(self):
        report = {
            "status": "COMPLETED_VERIFIED",
            "complete": True,
            "claims": ["c1"],
            "contradictions": [],
        }
        value = assess_report(report, [])
        self.assertFalse(value["research_quality_gate_passed"])

    def test_invalid_status_fail_closed(self):
        report = {
            "status": "UNKNOWN",
            "complete": True,
            "claims": [],
            "contradictions": [],
        }
        self.assertFalse(assess_report(report, [])["ok"])

    def test_human_review_always_required(self):
        claim = assess_claim("c1", [], evidence_two(), source_registry=registry())
        self.assertTrue(claim["human_review_required"])
        self.assertFalse(claim["decision_eligible"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
