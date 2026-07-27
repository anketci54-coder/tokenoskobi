from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_EXECUTOR_CLASSIFIER_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_executor_route_blocker_classification.py',
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


def address_topic(value: str) -> str:
    return '0x' + '0' * 24 + value[2:]


def transfer_log(token: str, src: str, dst: str, amount: int) -> dict:
    return {
        'address': token,
        'topics': [module.TRANSFER_TOPIC, address_topic(src), address_topic(dst)],
        'data': '0x' + amount.to_bytes(32, 'big').hex(),
    }


def event(input_token: str, output_token: str, input_raw: int, output_raw: int, pool: str | None = None) -> dict:
    return {
        'protocol_verified': True,
        'protocol_id': 'PANCAKESWAP_V3',
        'pool_address': pool or address('9'),
        'input_token': input_token,
        'output_token': output_token,
        'input_raw': str(input_raw),
        'output_raw': str(output_raw),
    }


def record(actor_net: dict[str, int], events: list[dict], *, exact: bool = True, self_call: bool = True) -> dict:
    actor = address('a')
    return {
        'tx_hash': tx_hash('1'),
        'block_number': 10,
        'transaction_index': 1,
        'actor': actor,
        'selector': '0xd4d6ab16',
        'self_call': self_call,
        'events': events,
        'route': {
            'actor_net_by_token': {token: str(amount) for token, amount in actor_net.items()},
            'swap_net_by_token': {token: str(amount) for token, amount in actor_net.items()} if exact else {},
            'exact_token_set': exact,
            'exact_raw_amounts': exact,
            'blockers': [] if exact else ['ACTOR_SWAP_NET_TOKEN_SET_MISMATCH'],
        },
    }


class ProductSlice04ExecutorClassificationTests(unittest.TestCase):
    def test_decode_transfer(self):
        token, src, dst = address('1'), address('2'), address('3')
        decoded = module.decode_transfer(transfer_log(token, src, dst, 125))
        self.assertEqual(decoded['token_address'], token)
        self.assertEqual(decoded['from_address'], src)
        self.assertEqual(decoded['to_address'], dst)
        self.assertEqual(decoded['amount_raw'], 125)

    def test_actor_transfer_edges(self):
        actor, pool, token = address('a'), address('b'), address('1')
        rows = module.actor_transfer_edges([
            transfer_log(token, actor, pool, 100),
            transfer_log(token, pool, actor, 80),
        ], actor)
        self.assertEqual([row['direction'] for row in rows], ['OUT', 'IN'])
        self.assertEqual({row['counterparty'] for row in rows}, {pool})

    def test_connected_components_separate_routes(self):
        a, b, c, d = address('1'), address('2'), address('3'), address('4')
        components = module.connected_components([
            event(a, b, 100, 90),
            event(c, d, 50, 40),
        ])
        self.assertEqual(len(components), 2)

    def test_zero_net_cycle_component(self):
        a, b = address('1'), address('2')
        summary = module.component_summary([
            event(a, b, 100, 90),
            event(b, a, 90, 100),
        ])
        self.assertEqual(summary['classification'], 'ZERO_NET_SWAP_CYCLE_COMPONENT')

    def test_two_endpoint_component(self):
        a, b, c = address('1'), address('2'), address('3')
        summary = module.component_summary([
            event(a, b, 100, 80),
            event(b, c, 80, 60),
        ])
        self.assertEqual(summary['classification'], 'TWO_ENDPOINT_ROUTE_COMPONENT')
        self.assertEqual(summary['input_token'], a)
        self.assertEqual(summary['output_token'], c)

    def test_multi_endpoint_component(self):
        a, b, c = address('1'), address('2'), address('3')
        summary = module.component_summary([
            event(a, b, 100, 80),
            event(a, c, 50, 30),
        ])
        self.assertEqual(summary['classification'], 'MULTI_ENDPOINT_ROUTE_COMPONENT')

    def test_exact_multi_asset_self_call_behavior(self):
        a, b, c, d = address('1'), address('2'), address('3'), address('4')
        result = module.transaction_classification(
            record({a: -100, b: 80, c: -50, d: 30}, [event(a, b, 100, 80), event(c, d, 50, 30)]),
            [],
        )
        self.assertEqual(result['behavior_class'], 'SELF_CALL_MULTI_ASSET_EXECUTOR_EXACT_SETTLEMENT')
        self.assertEqual(result['component_count'], 2)

    def test_unexplained_self_call_behavior(self):
        a, b = address('1'), address('2')
        result = module.transaction_classification(
            record({a: -100, b: 80}, [event(a, b, 100, 80)], exact=False),
            [],
        )
        self.assertEqual(result['behavior_class'], 'SELF_CALL_EXECUTOR_WITH_UNEXPLAINED_SETTLEMENT')

    def test_component_reverse_without_actor_attribution_not_confirmed(self):
        actor = address('a')
        base, position, extra = address('1'), address('2'), address('3')
        transactions = [
            {
                'tx_hash': tx_hash('1'), 'block_number': 10, 'transaction_index': 1,
                'actor_net_by_token': {base: '-100', position: '50', extra: '1'},
                'components': [{'classification': 'TWO_ENDPOINT_ROUTE_COMPONENT', 'input_token': base, 'output_token': position, 'input_raw': '100', 'output_raw': '50'}],
            },
            {
                'tx_hash': tx_hash('2'), 'block_number': 20, 'transaction_index': 1,
                'actor_net_by_token': {position: '-50', base: '110', extra: '-1'},
                'components': [{'classification': 'TWO_ENDPOINT_ROUTE_COMPONENT', 'input_token': position, 'output_token': base, 'input_raw': '50', 'output_raw': '110'}],
            },
        ]
        candidate = module.build_component_reverse_candidates(transactions)[0]
        self.assertTrue(candidate['position_amount_exact'])
        self.assertFalse(candidate['actor_settlement_attribution_verified'])
        self.assertFalse(candidate['closed_loop_confirmed'])

    def test_component_reverse_with_exact_actor_attribution_confirms_and_authority_is_zero(self):
        base, position = address('1'), address('2')
        transactions = [
            {
                'tx_hash': tx_hash('1'), 'block_number': 10, 'transaction_index': 1,
                'actor_net_by_token': {base: '-100', position: '50'},
                'components': [{'classification': 'TWO_ENDPOINT_ROUTE_COMPONENT', 'input_token': base, 'output_token': position, 'input_raw': '100', 'output_raw': '50'}],
            },
            {
                'tx_hash': tx_hash('2'), 'block_number': 20, 'transaction_index': 1,
                'actor_net_by_token': {position: '-50', base: '110'},
                'components': [{'classification': 'TWO_ENDPOINT_ROUTE_COMPONENT', 'input_token': position, 'output_token': base, 'input_raw': '50', 'output_raw': '110'}],
            },
        ]
        candidate = module.build_component_reverse_candidates(transactions)[0]
        self.assertTrue(candidate['closed_loop_confirmed'])
        self.assertFalse(module.AUTHORITY['network_access'])
        for key in ('paper_trade', 'live_trade', 'wallet', 'signing', 'order_create', 'broadcast'):
            self.assertFalse(module.AUTHORITY[key], key)


if __name__ == '__main__':
    unittest.main()
