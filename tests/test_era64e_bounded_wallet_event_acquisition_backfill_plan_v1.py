import json
import unittest
from pathlib import Path

CONFIG=Path('config/era64_bounded_wallet_event_acquisition_backfill_plan_v1.json')
ARTIFACT=Path('data/control/era64e_bounded_wallet_event_acquisition_backfill_plan_v1.json')

class Era64EPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.artifact=json.loads(ARTIFACT.read_text(encoding='utf-8'))

    def test_01_plan_only(self):
        self.assertEqual(self.config['mode'],'PLAN_ONLY_NO_ACQUISITION')
        self.assertFalse(self.artifact['execution_started'])

    def test_02_real_only(self):
        self.assertTrue(self.artifact['real_data'])
        self.assertFalse(self.artifact['synthetic_data'])

    def test_03_network_not_used(self):
        self.assertFalse(self.artifact['network_access_used'])
        self.assertFalse(self.config['source_policy']['network_access_authorized_in_this_stage'])

    def test_04_database_write_not_used(self):
        self.assertFalse(self.artifact['database_write_used'])
        self.assertFalse(self.config['source_policy']['database_write_authorized'])

    def test_05_event_contracts_complete(self):
        self.assertEqual(set(self.config['event_contracts']),{'wallet_transfer','wallet_label','wallet_trade','wallet_relationship'})
        self.assertIn('tx_hash',self.config['event_contracts']['wallet_trade'])
        self.assertIn('gas_cost',self.config['event_contracts']['wallet_trade'])

    def test_06_canary_is_bounded(self):
        limits=self.config['canary_limits']
        self.assertLessEqual(limits['maximum_blocks'],5000)
        self.assertLessEqual(limits['maximum_rpc_requests'],800)
        self.assertLessEqual(limits['maximum_runtime_seconds'],900)

    def test_07_fail_closed(self):
        rules=set(self.config['fail_closed_rules'])
        self.assertIn('RPC_CHAIN_ID_MISMATCH_ABORT',rules)
        self.assertIn('DATABASE_WRITE_WITHOUT_SEPARATE_APPROVAL_ABORT',rules)
        self.assertIn('MISSING_COST_FIELDS_BLOCK_PERFORMANCE_CLASSIFICATION',rules)

    def test_08_authority_zero(self):
        self.assertFalse(any(self.artifact['authority'].values()))
        self.assertTrue(self.artifact['required_gates']['no_live_or_paper_authority'])

if __name__=='__main__':
    unittest.main()
