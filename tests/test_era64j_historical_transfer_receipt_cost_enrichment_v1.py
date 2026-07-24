import importlib.util
import json
import sqlite3
import unittest
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
CONFIG=ROOT/'config/era64j_historical_transfer_receipt_cost_enrichment_v1.json'
CONTROL=ROOT/'data/control/era64j_historical_transfer_receipt_cost_enrichment_v1.json'
DETAIL=ROOT/'data/replay/era64j_historical_transfer_receipt_cost_enrichment_v1.json'
DB=ROOT/'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
TOOL=ROOT/'tools/era64j_historical_transfer_receipt_cost_enrichment_v1.py'
SPEC=importlib.util.spec_from_file_location('era64j',TOOL)
MODULE=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

class Era64JTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.control=json.loads(CONTROL.read_text(encoding='utf-8'))
        cls.detail=json.loads(DETAIL.read_text(encoding='utf-8'))

    def test_01_status_and_real_data(self):
        self.assertEqual(self.control['status'],'HISTORICAL_TRANSFER_RECEIPT_GAS_COST_ENRICHMENT_VERIFIED')
        self.assertTrue(self.control['real_data'])
        self.assertFalse(self.control['synthetic_data'])

    def test_02_authority_is_bounded(self):
        authority=self.control['authority']
        self.assertTrue(authority['network_access'])
        self.assertEqual(authority['network_mode'],'READ_ONLY_ALLOWLISTED_BSC_RPC')
        self.assertTrue(authority['staging_database_write'])
        self.assertFalse(authority['production_database_write'])
        for key in ('runtime_service_mutation','panel_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
            self.assertFalse(authority[key])

    def test_03_source_event_count_is_preserved(self):
        self.assertEqual(self.control['source_event_count'],367)
        self.assertEqual(self.control['receipt_enriched_event_count'],367)
        self.assertEqual(self.control['gas_cost_enriched_event_count'],367)
        self.assertEqual(self.control['event_gas_cost_coverage_ratio'],1.0)

    def test_04_transaction_receipt_coverage_is_complete(self):
        self.assertGreater(self.control['source_transaction_count'],0)
        self.assertEqual(self.control['receipt_enriched_transaction_count'],self.control['source_transaction_count'])
        self.assertEqual(self.control['staging_receipt_count'],self.control['source_transaction_count'])
        self.assertEqual(self.control['receipt_coverage_ratio'],1.0)
        self.assertEqual(self.control['missing_receipt_count'],0)

    def test_05_database_integrity_and_unique_receipts(self):
        self.assertEqual(self.control['database_integrity_check'],'ok')
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            conn.execute('PRAGMA query_only=ON')
            total=conn.execute('SELECT COUNT(*) FROM era64j_historical_receipt_cost_enrichment_v1').fetchone()[0]
            unique=conn.execute('SELECT COUNT(DISTINCT tx_hash) FROM era64j_historical_receipt_cost_enrichment_v1').fetchone()[0]
            self.assertEqual(total,unique)
            self.assertEqual(total,self.control['staging_receipt_count'])
        finally:
            conn.close()

    def test_06_gas_cost_invariant(self):
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            rows=conn.execute('SELECT gas_used,effective_gas_price_wei,gas_cost_wei FROM era64j_historical_receipt_cost_enrichment_v1').fetchall()
            self.assertTrue(rows)
            for gas_used,gas_price,gas_cost in rows:
                self.assertEqual(int(gas_cost),int(gas_used)*int(gas_price))
                self.assertGreaterEqual(int(gas_cost),0)
        finally:
            conn.close()

    def test_07_receipt_linkage_matches_source(self):
        self.assertEqual(self.control['block_mismatch_count'],0)
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            mismatch=conn.execute('''
              SELECT COUNT(*)
              FROM era64i_historical_wallet_transfer_staging_v1 s
              JOIN era64j_historical_receipt_cost_enrichment_v1 e ON e.tx_hash=s.tx_hash
              WHERE e.block_number!=s.block_number OR e.block_hash!=s.block_hash
            ''').fetchone()[0]
            self.assertEqual(mismatch,0)
        finally:
            conn.close()

    def test_08_receipt_provenance_is_complete(self):
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            missing=conn.execute("SELECT COUNT(*) FROM era64j_historical_receipt_cost_enrichment_v1 WHERE source_provider_host='' OR evidence_hash='' OR raw_receipt_json=''").fetchone()[0]
            self.assertEqual(missing,0)
        finally:
            conn.close()

    def test_09_receipt_status_partition_is_complete(self):
        self.assertEqual(self.control['successful_receipt_count']+self.control['failed_receipt_count'],self.control['source_transaction_count'])
        self.assertEqual(self.control['invalid_cost_record_count'],0)

    def test_10_source_flags_remain_immutable_zero(self):
        self.assertTrue(self.control['source_flags_immutable_zero'])
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            changed=conn.execute('SELECT COUNT(*) FROM era64i_historical_wallet_transfer_staging_v1 WHERE cost_enriched!=0 OR receipt_enriched!=0').fetchone()[0]
            self.assertEqual(changed,0)
        finally:
            conn.close()

    def test_11_successful_wallet_classification_remains_blocked(self):
        self.assertTrue(self.control['receipt_gas_cost_enrichment_complete'])
        self.assertFalse(self.control['performance_cost_enrichment_complete'])
        self.assertFalse(self.control['swap_direction_classification_ready'])
        self.assertEqual(self.control['closed_cycle_count'],0)
        self.assertFalse(self.control['successful_wallet_classification_ready'])
        self.assertFalse(self.control['cluster_inference_performed'])

    def test_12_no_wallet_signing_order_or_dynamic_execution(self):
        source=TOOL.read_text(encoding='utf-8')
        for token in ('subprocess','os.system','shell=True','eval(','exec(','eth_sendRawTransaction','eth_sendTransaction','personal_sign'):
            self.assertNotIn(token,source)
        with self.assertRaises(MODULE.Era64JError):
            MODULE.ensure_staging_path(ROOT/'data/tokenoskobi.db')

if __name__=='__main__':
    unittest.main()
