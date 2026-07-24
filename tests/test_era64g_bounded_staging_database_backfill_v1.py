import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
SPEC=importlib.util.spec_from_file_location('era64g',ROOT/'tools/era64g_bounded_staging_database_backfill_v1.py')
MODULE=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONFIG=ROOT/'config/era64g_bounded_staging_database_backfill_v1.json'
SOURCE=ROOT/'data/replay/era64f_bounded_readonly_wallet_event_canary_v1.json'
CONTROL=ROOT/'data/control/era64g_bounded_staging_database_backfill_v1.json'
DB=ROOT/'runtime/era64g/wallet_events_staging_v1.sqlite3'

class Era64GTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.control=json.loads(CONTROL.read_text(encoding='utf-8'))
        cls.source=json.loads(SOURCE.read_text(encoding='utf-8'))

    def test_01_status_and_real_data(self):
        self.assertEqual(self.control['status'],'BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED')
        self.assertTrue(self.control['real_data'])
        self.assertFalse(self.control['synthetic_data'])

    def test_02_only_staging_database_write_authorized(self):
        authority=self.control['authority']
        self.assertTrue(authority['staging_database_write'])
        self.assertFalse(authority['production_database_write'])
        for key in ('blockchain_network_access','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
            self.assertFalse(authority[key])

    def test_03_source_count_preserved(self):
        self.assertEqual(self.control['source_event_count'],len(self.source['events']))
        self.assertEqual(self.control['staging_event_count'],191)
        self.assertEqual(self.control['distinct_wallet_count'],self.source['distinct_wallet_count'])

    def test_04_transfer_counts_preserved(self):
        self.assertEqual(self.control['native_transfer_event_count'],17)
        self.assertEqual(self.control['token_transfer_event_count'],174)

    def test_05_database_integrity_and_unique_key(self):
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            total=conn.execute('SELECT COUNT(*) FROM era64g_wallet_event_staging_v1').fetchone()[0]
            unique=conn.execute('SELECT COUNT(*) FROM (SELECT chain_id,tx_hash,log_index FROM era64g_wallet_event_staging_v1 GROUP BY chain_id,tx_hash,log_index)').fetchone()[0]
            self.assertEqual(total,unique)
        finally:
            conn.close()

    def test_06_idempotent_import(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'runtime/era64g') as tmp:
            path=Path(tmp)/'test.sqlite3'
            first=MODULE.import_events(CONFIG,SOURCE,path)
            second=MODULE.import_events(CONFIG,SOURCE,path)
            self.assertEqual(first['inserted_event_count'],191)
            self.assertEqual(second['inserted_event_count'],0)
            self.assertEqual(second['deduplicated_event_count'],191)
            self.assertEqual(second['staging_event_count'],191)

    def test_07_production_path_rejected(self):
        with self.assertRaises(MODULE.Era64GError):
            MODULE.ensure_staging_path(ROOT/'data/tokenoskobi.db')

    def test_08_invalid_wallet_rejected(self):
        event=dict(self.source['events'][0])
        event['from_address']='0x1234'
        with self.assertRaises(MODULE.Era64GError):
            MODULE.normalize_event(event)

    def test_09_native_log_index_contract(self):
        event=next(dict(item) for item in self.source['events'] if item['event_type']=='NATIVE_TRANSFER')
        event['log_index']=0
        with self.assertRaises(MODULE.Era64GError):
            MODULE.normalize_event(event)

    def test_10_raw_evidence_and_hash_preserved(self):
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            row=conn.execute('SELECT raw_event_json,evidence_hash,source_artifact_sha256 FROM era64g_wallet_event_staging_v1 LIMIT 1').fetchone()
            self.assertTrue(json.loads(row[0])['event_uid'])
            self.assertEqual(len(row[1]),64)
            self.assertEqual(len(row[2]),64)
        finally:
            conn.close()

if __name__=='__main__':
    unittest.main()
