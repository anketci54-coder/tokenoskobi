
import sys,unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from core.research_evidence_ledger import (
    ZERO_HASH,append_evidence,build_entry,
    capacity_decision,verify_chain
)

class Tests(unittest.TestCase):
    def test_genesis(self):
        x=build_entry({"id":"a"},1)
        self.assertEqual(x["previous_entry_hash"],ZERO_HASH)

    def test_valid_chain(self):
        a=build_entry({"id":"a"},1)
        b=build_entry({"id":"b"},2,a["entry_hash"])
        self.assertTrue(verify_chain([a,b])["ok"])

    def test_payload_tamper(self):
        a=build_entry({"id":"a"},1)
        a["evidence"]["id"]="x"
        self.assertFalse(verify_chain([a])["ok"])

    def test_sequence_tamper(self):
        a=build_entry({"id":"a"},1)
        a["sequence_number"]=2
        self.assertFalse(verify_chain([a])["ok"])

    def test_previous_hash_tamper(self):
        a=build_entry({"id":"a"},1)
        b=build_entry({"id":"b"},2,a["entry_hash"])
        b["previous_entry_hash"]=ZERO_HASH
        self.assertFalse(verify_chain([a,b])["ok"])

    def test_normal_capacity(self):
        x=capacity_decision(0,100,0,1000,10)
        self.assertEqual(x["decision"],"ALLOW")

    def test_warning_backpressure(self):
        x=capacity_decision(790,20,0,1000,10)
        self.assertEqual(x["decision"],"ALLOW_WITH_BACKPRESSURE")

    def test_critical_fail_closed(self):
        x=capacity_decision(940,20,0,1000,10)
        self.assertEqual(x["decision"],"FAIL_CLOSED")

    def test_entry_quota(self):
        x=capacity_decision(0,1,10,1000,10)
        self.assertEqual(x["decision"],"FAIL_CLOSED")

    def test_append_no_delete(self):
        x=append_evidence([],{"id":"a"},0,10000,10)
        self.assertTrue(x["ok"])
        self.assertFalse(x["auto_delete"])

    def test_rejected_partial_not_actionable(self):
        x=append_evidence([],{"id":"a"},950,1000,10)
        self.assertFalse(x["partial_output_actionable"])

if __name__=="__main__":
    unittest.main(verbosity=2)
