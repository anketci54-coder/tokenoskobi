import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
CONFIG=ROOT/'config/era64i_bounded_historical_wallet_event_backfill_v1.json'
CONTROL=ROOT/'data/control/era64i_bounded_historical_wallet_event_backfill_v1.json'
DETAIL=ROOT/'data/replay/era64i_bounded_historical_wallet_event_backfill_v1.json'
DB=ROOT/'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
TOOL=ROOT/'tools/era64i_bounded_historical_wallet_event_backfill_v1.py'
SPEC=importlib.util.spec_from_file_location('era64i',TOOL)
MODULE=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

class Era64ITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.control=json.loads(CONTROL.read_text(encoding='utf-8'))
        cls.detail=json.loads(DETAIL.read_text(encoding='utf-8'))

    def test_01_status_and_real_data(self):
        self.assertEqual(self.control['status'],'BOUNDED_HISTORICAL_WALLET_TRANSFER_BACKFILL_VERIFIED')
        self.assertTrue(self.control['real_data'])
        self.assertFalse(self.control['synthetic_data'])

    def test_02_network_and_staging_write_are_explicitly_bounded(self):
        authority=self.control['authority']
        self.assertTrue(authority['network_access'])
        self.assertEqual(authority['network_mode'],'READ_ONLY_ALLOWLISTED_BSC_RPC')
        self.assertTrue(authority['staging_database_write'])
        self.assertFalse(authority['production_database_write'])
        for key in ('runtime_service_mutation','panel_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
            self.assertFalse(authority[key])

    def test_03_chain_and_historical_bounds(self):
        self.assertEqual(self.control['chain_id'],56)
        limits=self.config['limits']
        self.assertLessEqual(self.control['historical_block_span'],4096)
        self.assertLessEqual(self.control['selected_event_count'],limits['maximum_events'])
        self.assertLessEqual(self.control['sampled_block_count'],limits['maximum_distinct_blocks'])
        self.assertLessEqual(self.control['rpc_request_count'],limits['maximum_rpc_requests'])

    def test_04_acceptance_minimums_are_met(self):
        acceptance=self.config['acceptance']
        self.assertGreaterEqual(self.control['scanned_chunk_count'],acceptance['minimum_scanned_chunks'])
        self.assertGreaterEqual(self.control['sampled_block_count'],acceptance['minimum_sampled_blocks'])
        self.assertGreaterEqual(self.control['selected_event_count'],acceptance['minimum_real_transfer_events'])
        self.assertGreaterEqual(self.control['distinct_wallet_count'],acceptance['minimum_distinct_wallets'])

    def test_05_database_integrity_and_unique_key(self):
        self.assertEqual(self.control['database_integrity_check'],'ok')
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            conn.execute('PRAGMA query_only=ON')
            total=conn.execute('SELECT COUNT(*) FROM era64i_historical_wallet_transfer_staging_v1').fetchone()[0]
            unique=conn.execute('SELECT COUNT(*) FROM (SELECT chain_id,tx_hash,log_index FROM era64i_historical_wallet_transfer_staging_v1 GROUP BY chain_id,tx_hash,log_index)').fetchone()[0]
            self.assertEqual(total,unique)
            self.assertEqual(total,self.control['staging_event_count'])
        finally:
            conn.close()

    def test_06_event_provenance_and_timestamps_are_complete(self):
        self.assertEqual(self.detail['scan']['missing_timestamp_event_count'],0)
        self.assertEqual(self.detail['scan']['missing_provenance_event_count'],0)
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            missing=conn.execute("SELECT COUNT(*) FROM era64i_historical_wallet_transfer_staging_v1 WHERE block_time_utc='' OR source_provider_host='' OR evidence_hash=''").fetchone()[0]
            self.assertEqual(missing,0)
        finally:
            conn.close()

    def test_07_scope_tokens_are_canonical_base_quote_assets(self):
        expected={
          '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',
          '0x55d398326f99059ff775485246999027b3197955',
          '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d',
          '0xe9e7cea3dedca5984780bafc599bd69add087d56',
        }
        self.assertEqual(set(self.config['scope_tokens']),expected)
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            observed={row[0] for row in conn.execute('SELECT DISTINCT token_address FROM era64i_historical_wallet_transfer_staging_v1')}
            self.assertTrue(observed.issubset(expected))
        finally:
            conn.close()

    def test_08_zero_address_is_not_counted_as_wallet(self):
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            wallets={row[0] for row in conn.execute('SELECT from_address FROM era64i_historical_wallet_transfer_staging_v1 UNION SELECT to_address FROM era64i_historical_wallet_transfer_staging_v1')}
            expected=len(wallets-{MODULE.ZERO_ADDRESS})
            self.assertEqual(self.control['distinct_wallet_count'],expected)
        finally:
            conn.close()

    def test_09_cost_and_successful_wallet_classification_remain_blocked(self):
        self.assertFalse(self.control['cost_enrichment_complete'])
        self.assertEqual(self.control['cost_enriched_event_count'],0)
        self.assertEqual(self.control['receipt_enriched_event_count'],0)
        self.assertEqual(self.control['closed_cycle_count'],0)
        self.assertFalse(self.control['successful_wallet_classification_ready'])

    def test_10_cluster_inference_is_not_claimed(self):
        self.assertFalse(self.control['cluster_inference_performed'])
        self.assertEqual(self.control['identity_cluster_count'],0)

    def test_11_production_database_path_is_rejected(self):
        with self.assertRaises(MODULE.Era64IError):
            MODULE.ensure_staging_path(ROOT/'data/tokenoskobi.db')

    def test_12_source_has_no_wallet_signing_order_or_dynamic_execution(self):
        source=TOOL.read_text(encoding='utf-8')
        for token in ('subprocess','os.system','shell=True','eval(','exec('):
            self.assertNotIn(token,source)
        self.assertNotIn('eth_sendRawTransaction',source)
        self.assertNotIn('eth_sendTransaction',source)
        self.assertNotIn('personal_sign',source)

if __name__=='__main__':
    unittest.main()
