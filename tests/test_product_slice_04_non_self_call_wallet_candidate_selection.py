from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_NON_SELF_CALL_SELECTION_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_non_self_call_wallet_candidate_selection.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_non_self_call_selection', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def address(char: str) -> str:
    return '0x' + char * 40


def tx_hash(char: str) -> str:
    return '0x' + char * 64


def source(tx: str, token: str, src: str, dst: str, amount: int) -> dict:
    return {
        'tx_hash': tx,
        'token_address': token,
        'from_address': src,
        'to_address': dst,
        'amount_raw': str(amount),
    }


def receipt(tx: str, actor: str, target: str, block: int, *, status: int = 1, raw: bool = True) -> dict:
    return {
        'tx_hash': tx,
        'block_number': block,
        'transaction_index': 0,
        'receipt_status': status,
        'gas_cost_wei': '1',
        'tx_from_address': actor,
        'tx_to_address': target,
        'evidence_hash': 'e',
        'raw_transaction_json': '{"hash":"x"}' if raw else '',
    }


class ProductSlice04NonSelfCallSelectionTests(unittest.TestCase):
    def test_compute_actor_net(self):
        actor, peer = address('a'), address('b')
        token = address('1')
        net = module.compute_actor_net([source(tx_hash('1'), token, actor, peer, 5)], actor)
        self.assertEqual(net, {token: -5})

    def test_self_call_is_excluded(self):
        actor, token = address('a'), address('1')
        tx1, tx2 = tx_hash('1'), tx_hash('2')
        rows = [source(tx1, token, actor, address('b'), 5), source(tx2, token, address('b'), actor, 5)]
        receipts = [receipt(tx1, actor, actor, 1), receipt(tx2, actor, actor, 2)]
        result = module.select_non_self_call_candidates(rows, receipts, excluded_actor=address('f'))
        self.assertEqual(result['all_pair_count'], 0)
        self.assertEqual(result['excluded_self_call_count'], 2)

    def test_executor_actor_is_excluded(self):
        actor, target, token = address('a'), address('b'), address('1')
        tx1, tx2 = tx_hash('1'), tx_hash('2')
        rows = [source(tx1, token, actor, target, 5), source(tx2, token, target, actor, 5)]
        receipts = [receipt(tx1, actor, target, 1), receipt(tx2, actor, target, 2)]
        result = module.select_non_self_call_candidates(rows, receipts, excluded_actor=actor)
        self.assertEqual(result['all_pair_count'], 0)
        self.assertEqual(result['excluded_executor_transaction_count'], 2)

    def test_opposite_direction_pair_is_selected(self):
        actor, target, token = address('a'), address('b'), address('1')
        tx1, tx2 = tx_hash('1'), tx_hash('2')
        rows = [source(tx1, token, actor, target, 5), source(tx2, token, target, actor, 5)]
        receipts = [receipt(tx1, actor, target, 1), receipt(tx2, actor, target, 2)]
        result = module.select_non_self_call_candidates(rows, receipts, excluded_actor=address('f'))
        self.assertEqual(result['all_pair_count'], 1)
        self.assertEqual(result['selected_pairs'][0]['first_direction'], 'OUT')
        self.assertEqual(result['selected_pairs'][0]['second_direction'], 'IN')

    def test_exact_reversed_endpoint_pair_is_ranked_strong(self):
        actor, target = address('a'), address('b')
        base, position = address('1'), address('2')
        tx1, tx2 = tx_hash('1'), tx_hash('2')
        rows = [
            source(tx1, base, actor, target, 100),
            source(tx1, position, target, actor, 50),
            source(tx2, position, actor, target, 50),
            source(tx2, base, target, actor, 110),
        ]
        receipts = [receipt(tx1, actor, target, 1), receipt(tx2, actor, target, 2)]
        result = module.select_non_self_call_candidates(rows, receipts, excluded_actor=address('f'))
        strong = [item for item in result['selected_pairs'] if item['endpoint_reverse_exact']]
        self.assertTrue(strong)
        self.assertTrue(any(item['selected_token_amount_exact'] for item in strong))
        self.assertEqual(result['next_safe_step'], 'BOUNDED_NON_SELF_CALL_TRANSACTION_ENRICHMENT_AND_ROUTE_DECODE')

    def test_amount_mismatch_is_not_exact(self):
        actor, target = address('a'), address('b')
        token = address('1')
        tx1, tx2 = tx_hash('1'), tx_hash('2')
        rows = [source(tx1, token, actor, target, 5), source(tx2, token, target, actor, 4)]
        receipts = [receipt(tx1, actor, target, 1), receipt(tx2, actor, target, 2)]
        result = module.select_non_self_call_candidates(rows, receipts, excluded_actor=address('f'))
        self.assertFalse(result['selected_pairs'][0]['selected_token_amount_exact'])

    def test_failed_receipt_is_excluded(self):
        actor, target, token = address('a'), address('b'), address('1')
        tx1, tx2 = tx_hash('1'), tx_hash('2')
        rows = [source(tx1, token, actor, target, 5), source(tx2, token, target, actor, 5)]
        receipts = [receipt(tx1, actor, target, 1, status=0), receipt(tx2, actor, target, 2)]
        result = module.select_non_self_call_candidates(rows, receipts, excluded_actor=address('f'))
        self.assertEqual(result['all_pair_count'], 0)
        self.assertEqual(result['excluded_failed_receipt_count'], 1)

    def test_no_candidate_returns_scan_extension(self):
        actor, target, token = address('a'), address('b'), address('1')
        tx1 = tx_hash('1')
        result = module.select_non_self_call_candidates(
            [source(tx1, token, actor, target, 5)],
            [receipt(tx1, actor, target, 1)],
            excluded_actor=address('f'),
        )
        self.assertEqual(result['next_safe_step'], 'CURRENT_DATASET_HAS_NO_NON_SELF_CALL_ROUND_TRIP_CANDIDATE_EXTEND_HISTORICAL_SCAN')

    def test_raw_transaction_coverage_is_reported(self):
        actor, target, token = address('a'), address('b'), address('1')
        tx1, tx2 = tx_hash('1'), tx_hash('2')
        rows = [source(tx1, token, actor, target, 5), source(tx2, token, target, actor, 5)]
        receipts = [receipt(tx1, actor, target, 1, raw=True), receipt(tx2, actor, target, 2, raw=False)]
        result = module.select_non_self_call_candidates(rows, receipts, excluded_actor=address('f'))
        self.assertFalse(result['selected_pairs'][0]['raw_transaction_coverage_complete'])

    def test_authority_boundary(self):
        self.assertFalse(module.AUTHORITY['network_access'])
        self.assertTrue(module.AUTHORITY['staging_file_write'])
        for key in (
            'source_database_write', 'production_database_write', 'repository_write',
            'panel_mutation', 'service_mutation', 'timer_mutation', 'paper_trade',
            'live_trade', 'wallet', 'signing', 'order_create', 'broadcast',
        ):
            self.assertFalse(module.AUTHORITY[key], key)


if __name__ == '__main__':
    unittest.main()
