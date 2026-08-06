from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.legacy.era64_wallet_event_coverage_bridge_v1 import (
    AUTHORITY,
    classify_schema,
    inspect_database,
    run,
)

A = '0x' + '1' * 40
B = '0x' + '2' * 40


class Era64DWalletCoverageBridgeTests(unittest.TestCase):
    def test_01_uid_registry_classification(self):
        result = classify_schema('wallet_registry', ['wallet_uid', 'wallet_address'])
        self.assertIn('UID_ADDRESS_REGISTRY', result['capabilities'])

    def test_02_known_wallet_label_classification(self):
        result = classify_schema('known_wallet_registry', ['wallet_address', 'known_name', 'label_confidence'])
        self.assertIn('DIRECT_LABEL_REGISTRY', result['capabilities'])

    def test_03_uid_transfer_missing_block_number_is_explicit(self):
        result = classify_schema(
            'wallet_transfer_events',
            ['from_wallet_uid', 'to_wallet_uid', 'tx_hash', 'block_time_utc', 'amount'],
        )
        self.assertIn('UID_RELATION_CANDIDATE', result['capabilities'])
        self.assertIn('MISSING_BLOCK_NUMBER', result['blockers'])
        self.assertNotIn('REPLAYABLE_UID_RELATION_AFTER_REGISTRY_JOIN', result['capabilities'])

    def test_04_whale_flow_schema_is_replayable(self):
        result = classify_schema(
            'whale_entity_flow_events',
            ['from_address', 'to_address', 'tx_hash', 'block_number', 'event_time_utc', 'amount_raw'],
        )
        self.assertIn('REPLAYABLE_DIRECT_RELATION', result['capabilities'])

    def test_05_cluster_link_is_evidence_not_fake_transaction(self):
        result = classify_schema(
            'wallet_cluster_links',
            ['root_wallet_address', 'linked_wallet_address', 'link_confidence', 'first_seen_at_utc'],
        )
        self.assertIn('DIRECT_CLUSTER_EVIDENCE', result['capabilities'])
        self.assertNotIn('REPLAYABLE_DIRECT_RELATION', result['capabilities'])

    def test_06_paper_lifecycle_is_excluded(self):
        result = classify_schema(
            'paper_position_lifecycle',
            ['paper_position_id', 'token_address', 'paper_entry_price', 'paper_exit_price', 'paper_engine_trade_authority'],
        )
        self.assertIn('PAPER_SIMULATION_ONLY_EXCLUDED', result['capabilities'])

    def test_07_real_readonly_replay_with_uid_join(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / 'x.sqlite'
            conn = sqlite3.connect(db)
            conn.execute('CREATE TABLE wallet_registry(wallet_uid TEXT, wallet_address TEXT)')
            conn.execute('CREATE TABLE wallet_transfer_events(from_wallet_uid TEXT, to_wallet_uid TEXT, tx_hash TEXT, block_number INTEGER, block_time_utc TEXT, amount REAL, asset_symbol TEXT)')
            conn.executemany('INSERT INTO wallet_registry VALUES(?,?)', [('a', A), ('b', B)])
            conn.execute("INSERT INTO wallet_transfer_events VALUES('a','b','0xabc',123,'2026-01-01T00:00:00Z',5,'T')")
            conn.commit(); conn.close()
            result = inspect_database(db, 20, 100)
            self.assertEqual(len(result['relations']), 1)
            self.assertEqual(result['relations'][0]['block_number'], 123)

    def test_08_missing_block_number_never_uses_rowid_as_fake_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / 'x.sqlite'
            conn = sqlite3.connect(db)
            conn.execute('CREATE TABLE wallet_registry(wallet_uid TEXT, wallet_address TEXT)')
            conn.execute('CREATE TABLE wallet_transfer_events(from_wallet_uid TEXT, to_wallet_uid TEXT, tx_hash TEXT, block_time_utc TEXT, amount REAL)')
            conn.executemany('INSERT INTO wallet_registry VALUES(?,?)', [('a', A), ('b', B)])
            conn.execute("INSERT INTO wallet_transfer_events VALUES('a','b','0xabc','2026-01-01T00:00:00Z',5)")
            conn.commit(); conn.close()
            result = inspect_database(db, 20, 100)
            self.assertEqual(result['relations'], [])
            self.assertEqual(result['blocker_counts'].get('MISSING_BLOCK_NUMBER'), 1)

    def test_09_runtime_status_contract_ready_without_events(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'data').mkdir()
            db = root / 'data' / 'x.sqlite'
            conn = sqlite3.connect(db)
            conn.execute('CREATE TABLE wallet_transfer_events(from_wallet_uid TEXT, to_wallet_uid TEXT, tx_hash TEXT, block_time_utc TEXT, amount REAL)')
            conn.commit(); conn.close()
            config = {
                'database_candidates': ['data/x.sqlite'],
                'maximum_tables_per_database': 20,
                'maximum_rows_per_table': 100,
                'maximum_graph_nodes': 16,
                'maximum_graph_edges': 16,
                'maximum_trade_groups': 16,
            }
            cfg = root / 'config.json'; cfg.write_text(json.dumps(config), encoding='utf-8')
            summary, _ = run(root, cfg)
            self.assertEqual(summary['status'], 'REAL_WALLET_EVENT_COVERAGE_REPAIRED_SOURCE_CONTRACT_READY')
            self.assertTrue(summary['source_contract_ready'])

    def test_10_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'data').mkdir()
            db = root / 'data' / 'x.sqlite'
            conn = sqlite3.connect(db)
            conn.execute('CREATE TABLE wallet_registry(wallet_uid TEXT, wallet_address TEXT)')
            conn.commit(); conn.close()
            config = {
                'database_candidates': ['data/x.sqlite'],
                'maximum_tables_per_database': 20,
                'maximum_rows_per_table': 100,
                'maximum_graph_nodes': 16,
                'maximum_graph_edges': 16,
                'maximum_trade_groups': 16,
            }
            cfg = root / 'config.json'; cfg.write_text(json.dumps(config), encoding='utf-8')
            first, detail1 = run(root, cfg)
            second, detail2 = run(root, cfg)
            self.assertEqual(first['result_hash'], second['result_hash'])
            self.assertEqual(detail1['detail_hash'], detail2['detail_hash'])

    def test_11_authority_is_zero(self):
        self.assertFalse(any(AUTHORITY.values()))

    def test_12_source_has_no_network_db_write_or_dynamic_execution(self):
        source = Path('tools/era64_wallet_event_coverage_bridge_v1.py').read_text(encoding='utf-8')
        for forbidden in ('requests.', 'urllib.', 'subprocess', 'os.system', 'shell=True', 'eval(', 'exec(', 'INSERT INTO', 'UPDATE ', 'DELETE FROM'):
            self.assertNotIn(forbidden, source)
        self.assertIn('?mode=ro', source)
        self.assertIn('PRAGMA query_only=ON', source)


if __name__ == '__main__':
    unittest.main()
