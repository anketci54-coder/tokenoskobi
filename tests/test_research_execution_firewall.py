import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from core.research_execution_firewall import *

def report():
    return {
      "schema":RESEARCH_SCHEMA,"report_id":"r1",
      "research_question":"test","scope":{},
      "status":"COMPLETED_VERIFIED","executive_summary":"research",
      "claims":[],"unknowns":[],"contradictions":[],"sources":[],
      "confidence":{"overall":1.0},"limitations":[],
      "human_review_required":True,"executable":False,
      "actionable":False,"decision_eligible":False,
      "created_at":"2026-07-18T00:00:00Z"
    }

class T(unittest.TestCase):
 def test_valid(self): self.assertTrue(validate_research_report(report())["ok"])
 def test_missing(self):
  x=report(); del x["report_id"]
  self.assertFalse(validate_research_report(x)["ok"])
 def test_extra(self):
  x=report(); x["extra"]=1
  self.assertFalse(validate_research_report(x)["ok"])
 def test_nested_forbidden(self):
  x=report(); x["claims"]=[{"transaction_payload":"0x"}]
  self.assertFalse(validate_research_report(x)["ok"])
 def test_actionable(self):
  x=report(); x["actionable"]=True
  self.assertFalse(validate_research_report(x)["ok"])
 def test_research_rejected(self):
  self.assertFalse(validate_execution_input(report())["ok"])
 def test_unknown_rejected(self):
  self.assertFalse(validate_execution_input({"schema":"unknown"})["ok"])
 def test_exception(self):
  with self.assertRaises(ResearchExecutionHardReject):
   enforce_execution_input(report())

if __name__=="__main__":
 unittest.main(verbosity=2)
