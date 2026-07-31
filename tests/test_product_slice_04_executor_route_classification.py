from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_EXECUTOR_CLASSIFIER_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_executor_route_classification.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_executor_classifier', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def address(char: str) -> str:
    return '0x' + char * 40


def tx_hash(char: str) -> str:
    return '0x' + char * 64


def event(source: str, target: str, index: int = 0, input_raw: int = 100, output_raw: int = 50) -> dict:
    return {
        'input_token': source,
        'output_token': target,
        'input_raw': str(input_raw),
        'output_raw': str(output_raw),
        'protocol_id': 'PANCAKESWAP_V3',
        'pool_address': address(str((index % 8) + 1)),
        'receipt_log_index': index,
    }


def transaction(events: list[dict], actor_net: dict[str, int], swap_net: dict[str, int]) -> dict:
    actor = module.EXPECTED_ACTOR
    return {
        'tx_hash': tx_hash('a'),
        'block_number': 100,
        'transaction_index': 1,
        'actor': actor,
        'transaction_target': actor,
        'selector': '0xd4d6ab16',
        'self_call': True,
        'recognized_swap_event_count': len(events),
        'protocol_verified_swap_event_count': len(events),
        'events': [{**item, 'protocol_verified': True} for item in events],
        'route': {
            'actor_net_by_token': {token: str(amount) for token, amount in actor_net.items()},
            'swap_net_by_token': {token: str(amount) for token, amount in swap_net.items()},
        },
    }


class ProductSlice04ExecutorRouteClassificationTests(unittest.TestCase):
    def test_directed_cycle_detected(self):
        a, b, c = address('a'), address('b'), address('c')
        edges = [event(a, b, 1), event(b, c, 2), event(c, a, 3)]
        self.assertTrue(module.has_directed_cycle(edges))

    def test_acyclic_path_not_cycle(self):
        a, b, c = address('a'), address('b'), address('c')
        edges = [event(a, b, 1), event(b, c, 2)]
        self.assertFalse(module.has_directed_cycle(edges))

    def test_weak_component_count(self):
        a, b, c, d = address('a'), address('b'), address('c'), address('d')
        self.assertEqual(module.weak_component_count([event(a, b, 1), event(c, d, 2)]), 2)

    def test_simple_two_token_route(self):
        a, b = address('1'), address('2')
        tx = transaction([event(a, b, 1, 100, 50)], {a: -100, b: 50}, {a: -100, b: 50})
        result = module.classify_transaction(tx)
        self.assertEqual(result['classification'], 'SELF_CALL_SIMPLE_TWO_TOKEN_ROUTE_VERIFIED')
        self.assertTrue(result['simple_wallet_position_admissible'])

    def test_exact_multi_asset_cycle(self):
        a, b, c = address('1'), address('2'), address('3')
        events = [event(a, b, 1, 100, 80), event(b, c, 2, 70, 60), event(c, a, 3, 50, 40)]
        net = {a: -60, b: 10, c: 10}
        tx = transaction(events, net, net)
        result = module.classify_transaction(tx)
        self.assertTrue(result['directed_cycle_present'])
        self.assertEqual(result['classification'], 'SELF_CALL_MULTI_ASSET_CYCLIC_EXECUTION_VERIFIED')
        self.assertFalse(result['simple_wallet_position_admissible'])

    def test_exact_multi_asset_acyclic_execution(self):
        a, b, c = address('1'), address('2'), address('3')
        events = [event(a, b, 1, 100, 80), event(a, c, 2, 20, 10)]
        net = {a: -120, b: 80, c: 10}
        result = module.classify_transaction(transaction(events, net, net))
        self.assertEqual(result['classification'], 'SELF_CALL_MULTI_ASSET_EXECUTION_VERIFIED')

    def test_unexplained_residual_rejected(self):
        a, b = address('1'), address('2')
        tx = transaction([event(a, b, 1, 100, 50)], {a: -99, b: 50}, {a: -100, b: 50})
        result = module.classify_transaction(tx)
        self.assertEqual(result['classification'], 'SELF_CALL_EXECUTION_WITH_UNEXPLAINED_TRANSFER_RESIDUALS')
        self.assertFalse(result['exact_raw_amounts'])

    def test_event_edge_rejects_same_token(self):
        a = address('1')
        with self.assertRaises(module.Slice04ExecutorClassificationError):
            module.event_edge(event(a, a, 1))

    def test_hash_and_address_validation(self):
        self.assertEqual(module.normalize_address(address('a')), address('a'))
        self.assertEqual(module.normalize_hash(tx_hash('b')), tx_hash('b'))
        with self.assertRaises(module.Slice04ExecutorClassificationError):
            module.normalize_address('0x1234')

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
