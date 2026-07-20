
import sys, unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from core.research_execution_firewall import (
    RESEARCH_SCHEMA,validate_execution_input,validate_research_report
)
from core.research_content_quarantine import (
    DISABLED_CAPABILITIES,quarantine,synthesis_envelope
)
from core.research_evidence_ledger import (
    append_evidence,build_entry,capacity_decision,verify_chain
)
from core.research_consensus_policy import assess_claim,assess_report
from core.research_safety_governor import (
    evaluate_iteration,validate_adversarial_context
)

def caps():
    return {k:False for k in DISABLED_CAPABILITIES}

def envelope(text=b"external evidence"):
    q=quarantine(text,"text/plain","https://example.com/evidence")
    return synthesis_envelope(q,caps())["content"]

def report():
    return {
      "schema":RESEARCH_SCHEMA,"report_id":"r1",
      "research_question":"test","scope":{},
      "status":"COMPLETED_VERIFIED",
      "executive_summary":"research only",
      "claims":["c1"],"unknowns":[],"contradictions":[],
      "sources":["a","b"],"confidence":{"overall":1.0},
      "limitations":[],"human_review_required":True,
      "executable":False,"actionable":False,
      "decision_eligible":False,
      "created_at":"2026-07-18T00:00:00Z"
    }

def evidence():
    return [
      {"claim_id":"c1","independence_key":"a",
       "verified":True,"supports":True},
      {"claim_id":"c1","independence_key":"b",
       "verified":True,"supports":True}
    ]


def registry():
    return {
      "a": {
        "active": True,
        "verified_independent": True,
        "independence_group": "group-a"
      },
      "b": {
        "active": True,
        "verified_independent": True,
        "independence_group": "group-b"
      }
    }

def state():
    return {
      "iterations":0,"total_tokens":0,"total_cost_units":0,
      "wall_seconds":0,"source_count":0,
      "fingerprint_counts":{},"no_gain_streak":0
    }

def request():
    return {
      "estimated_tokens":100,"estimated_cost_units":1,
      "wall_seconds_delta":1,"new_sources":1,
      "fingerprint":"fixture","expected_gain_delta":1,
      "paid_api_requested":False
    }

class Tests(unittest.TestCase):
    def test_full_chain_non_actionable(self):
        env=envelope()
        context=validate_adversarial_context(
            env,"2026-07-18T12:00:00Z","2026-07-18T12:01:00Z"
        )
        item=append_evidence([],{"id":"a"},0,100000,10)
        claim=assess_claim("c1", [], evidence(), source_registry=registry())
        quality=assess_report({
            "status":"COMPLETED_VERIFIED","complete":True,
            "claims":["c1"],"contradictions":[]
        },[claim])
        self.assertTrue(context["ok"])
        self.assertTrue(verify_chain([item["entry"]])["ok"])
        self.assertTrue(validate_research_report(report())["ok"])
        self.assertFalse(quality["actionable"])
        self.assertFalse(validate_execution_input(report())["ok"])

    def test_execution_bypass_denied(self):
        self.assertFalse(validate_execution_input(report())["ok"])

    def test_missing_taint_denied(self):
        env=envelope()
        env["quarantined_content"]["tainted_external_content"]=False
        self.assertFalse(validate_adversarial_context(
            env,"2026-07-18T12:00:00Z","2026-07-18T12:01:00Z"
        )["ok"])

    def test_future_time_denied(self):
        self.assertFalse(validate_adversarial_context(
            envelope(),
            "2026-07-18T13:00:00Z",
            "2026-07-18T12:00:00Z"
        )["ok"])

    def test_ledger_tamper_denied(self):
        item=build_entry({"id":"a"},1)
        item["evidence"]["id"]="tampered"
        self.assertFalse(verify_chain([item])["ok"])

    def test_critical_watermark_denied(self):
        self.assertEqual(
            capacity_decision(940,20,0,1000,10)["decision"],
            "FAIL_CLOSED"
        )

    def test_model_consensus_not_evidence(self):
        models=[
          {"claim_id":"c1","model_id":"m1","stance":"SUPPORT"},
          {"claim_id":"c1","model_id":"m2","stance":"SUPPORT"}
        ]
        value=assess_claim("c1",models,[])
        self.assertTrue(value["model_consensus"])
        self.assertFalse(value["evidence_consensus"])

    def test_incomplete_non_actionable(self):
        claim=assess_claim("c1", [], evidence(), source_registry=registry())
        value=assess_report({
            "status":"INCOMPLETE_EVIDENCE","complete":False,
            "claims":["c1"],"contradictions":[]
        },[claim])
        self.assertFalse(value["actionable"])

    def test_paid_api_denied(self):
        req=request()
        req["paid_api_requested"]=True
        self.assertFalse(evaluate_iteration(state(),req)["ok"])

    def test_duplicate_loop_denied(self):
        current=state()
        current["fingerprint_counts"]={"fixture":2}
        self.assertFalse(evaluate_iteration(current,request())["ok"])

    def test_partial_output_non_actionable(self):
        value=append_evidence([],{"id":"a"},950,1000,10)
        self.assertFalse(value["ok"])
        self.assertFalse(value["partial_output_actionable"])

if __name__=="__main__":
    unittest.main(verbosity=2)
