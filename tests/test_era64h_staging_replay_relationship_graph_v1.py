import importlib.util
import json
import sqlite3
import unittest
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
CONFIG=ROOT/'config/era64h_staging_replay_relationship_graph_v1.json'
CONTROL=ROOT/'data/control/era64h_staging_replay_relationship_graph_validation_v1.json'
DETAIL=ROOT/'data/replay/era64h_staging_replay_relationship_graph_v1.json'
DB=ROOT/'runtime/era64g/wallet_events_staging_v1.sqlite3'
TOOL=ROOT/'tools/era64h_staging_replay_relationship_graph_v1.py'
SPEC=importlib.util.spec_from_file_location('era64h',TOOL)
MODULE=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

class Era64HTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.control=json.loads(CONTROL.read_text(encoding='utf-8'))
        cls.detail=json.loads(DETAIL.read_text(encoding='utf-8'))

    def test_01_status_and_real_data(self):
        self.assertEqual(self.control['status'],'STAGING_REPLAY_RELATIONSHIP_GRAPH_VALIDATED')
        self.assertTrue(self.control['real_data'])
        self.assertFalse(self.control['synthetic_data'])

    def test_02_all_authorities_are_zero(self):
        self.assertFalse(any(self.control['authority'].values()))
        self.assertFalse(self.control['database_write_used'])
        self.assertFalse(self.control['network_access_used'])

    def test_03_database_is_readonly_and_unchanged(self):
        self.assertEqual(self.detail['database_mode'],'READ_ONLY_IMMUTABLE_SQLITE')
        self.assertEqual(self.detail['database_sha256_before'],self.detail['database_sha256_after'])
        self.assertEqual(self.detail['database_mtime_ns_before'],self.detail['database_mtime_ns_after'])
        self.assertEqual(self.control['database_integrity_check'],'ok')

    def test_04_event_counts_are_preserved(self):
        self.assertEqual(self.control['staging_event_count'],191)
        self.assertEqual(self.control['unique_event_count'],191)
        self.assertEqual(self.control['native_transfer_event_count'],17)
        self.assertEqual(self.control['token_transfer_event_count'],174)

    def test_05_zero_address_is_not_a_wallet_node(self):
        graph=self.detail['relationship_graph']
        self.assertEqual(graph['node_count'],150)
        addresses={item['address'] for item in graph['nodes']}
        self.assertNotIn(self.config['zero_address'],addresses)

    def test_06_evidence_is_complete_and_unique(self):
        self.assertEqual(self.control['evidence_complete_event_count'],191)
        self.assertEqual(self.detail['evidence_incomplete_event_count'],0)
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            total=conn.execute('SELECT COUNT(*) FROM era64g_wallet_event_staging_v1').fetchone()[0]
            unique=conn.execute('SELECT COUNT(*) FROM (SELECT chain_id,tx_hash,log_index FROM era64g_wallet_event_staging_v1 GROUP BY chain_id,tx_hash,log_index)').fetchone()[0]
            self.assertEqual(total,unique)
        finally:
            conn.close()

    def test_07_relationship_graph_is_nonempty(self):
        self.assertGreater(self.control['relationship_event_count'],0)
        self.assertGreater(self.control['relationship_edge_count'],0)
        self.assertGreater(self.control['connected_component_count'],0)

    def test_08_relationship_semantics_do_not_claim_identity(self):
        self.assertFalse(self.control['cluster_inference_performed'])
        self.assertEqual(self.control['identity_cluster_count'],0)
        for edge in self.detail['relationship_graph']['edges']:
            self.assertEqual(edge['relationship_type'],'OBSERVED_TRANSACTION_FLOW_ONLY')
            self.assertEqual(edge['evidence_count'],edge['event_count'])

    def test_09_components_partition_all_nodes(self):
        components=self.detail['relationship_graph']['components']
        members=[wallet for component in components for wallet in component['members']]
        self.assertEqual(len(members),150)
        self.assertEqual(len(set(members)),150)

    def test_10_graph_is_deterministic(self):
        first_detail,first_control=MODULE.run(CONFIG)
        second_detail,second_control=MODULE.run(CONFIG)
        self.assertEqual(first_control['graph_hash'],second_control['graph_hash'])
        self.assertEqual(first_detail['relationship_graph'],second_detail['relationship_graph'])

    def test_11_successful_wallet_classification_remains_blocked(self):
        self.assertFalse(self.control['successful_wallet_classification_ready'])
        self.assertEqual(self.control['cost_complete_trade_event_count'],0)
        self.assertEqual(self.control['closed_cycle_count'],0)

    def test_12_source_has_no_network_write_or_dynamic_execution(self):
        source=TOOL.read_text(encoding='utf-8')
        for token in ('urllib','requests','subprocess','os.system','shell=True','eval(','exec('):
            self.assertNotIn(token,source)
        lowered=source.lower()
        for sql in ('insert into','update era64g','delete from','create table','drop table','alter table'):
            self.assertNotIn(sql,lowered)

if __name__=='__main__':
    unittest.main()
