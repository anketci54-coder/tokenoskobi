import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
CONFIG=ROOT/'config/era64f_bounded_readonly_wallet_event_canary_v1.json'
CONTROL=ROOT/'data/control/era64f_bounded_readonly_wallet_event_canary_v1.json'
ENGINE=ROOT/'tools/era64f_bounded_readonly_wallet_event_canary_v1.py'

spec=importlib.util.spec_from_file_location('era64f_canary',ENGINE)
module=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

class Era64FCanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.control=json.loads(CONTROL.read_text(encoding='utf-8'))
        cls.source=ENGINE.read_text(encoding='utf-8')

    def test_01_network_is_readonly_and_explicit(self):
        authority=self.config['authority']
        self.assertTrue(authority['network_access'])
        self.assertEqual(authority['network_mode'],'READ_ONLY_ALLOWLISTED_BSC_RPC')

    def test_02_all_financial_and_mutation_authorities_are_zero(self):
        authority=self.control['authority']
        for key in ('database_write','runtime_mutation','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
            self.assertFalse(authority[key])

    def test_03_chain_is_bsc(self):
        self.assertEqual(self.control['chain_id'],56)

    def test_04_canary_is_bounded(self):
        limits=self.config['limits']
        self.assertLessEqual(limits['block_span'],8)
        self.assertLessEqual(limits['maximum_receipts'],128)
        self.assertLessEqual(limits['maximum_rpc_requests'],200)
        self.assertLessEqual(limits['maximum_runtime_seconds'],300)

    def test_05_rpc_methods_are_readonly_allowlisted(self):
        self.assertEqual(
            set(self.config['rpc_method_allowlist']),
            {'eth_chainId','eth_blockNumber','eth_getBlockByNumber','eth_getTransactionReceipt'},
        )

    def test_06_topic_address_decoding(self):
        topic='0x'+'00'*12+'1234567890abcdef1234567890abcdef12345678'
        self.assertEqual(module.topic_address(topic),'0x1234567890abcdef1234567890abcdef12345678')

    def test_07_output_is_real_and_not_synthetic(self):
        self.assertTrue(self.control['real_data'])
        self.assertFalse(self.control['synthetic_data'])
        self.assertTrue(self.control['network_access_used'])
        self.assertFalse(self.control['database_write_used'])

    def test_08_status_is_fail_closed_or_verified(self):
        self.assertIn(
            self.control['status'],
            {'REAL_WALLET_EVENT_CANARY_VERIFIED','REAL_WALLET_EVENT_CANARY_EMPTY_FAIL_CLOSED'},
        )

    def test_09_verified_status_requires_real_events(self):
        if self.control['status']=='REAL_WALLET_EVENT_CANARY_VERIFIED':
            self.assertGreater(self.control['scanned_block_count'],0)
            self.assertGreater(self.control['receipt_count'],0)
            self.assertGreater(self.control['real_wallet_event_count'],0)
            self.assertEqual(self.control['duplicate_event_count'],0)

    def test_10_source_has_no_database_or_execution_authority(self):
        forbidden=('sqlite3','subprocess','os.system','shell=True','eval(','exec(','eth_sendRawTransaction','personal_sign','eth_signTransaction')
        for token in forbidden:
            self.assertNotIn(token,self.source)

if __name__=='__main__':
    unittest.main()
