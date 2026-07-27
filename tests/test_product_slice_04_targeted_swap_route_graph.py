from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_ROUTE_GRAPH_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_targeted_swap_route_graph.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_targeted_swap_route_graph', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def address(char: str) -> str:
    return '0x' + char * 40


def tx_hash(number: int) -> str:
    return '0x' + f'{number:064x}'


def edge(source: str, target: str, *, verified: bool = True, index: int = 0) -> dict:
    return {
        'tx_hash': tx_hash(1),
        'block_number': 100,
        'receipt_log_position': index,
        'receipt_log_index': index,
        'event_type': 'PANCAKE_V3_EXTENDED_SWAP',
        'pool_address': address(chr(ord('a') + index)),
        'factory': address('f'),
        'protocol_verified': verified,
        'protocol_id': 'PANCAKESWAP_V3' if verified else 'UNVERIFIED',
        'protocol_name': 'PancakeSwap' if verified else 'UNVERIFIED',
        'protocol_version': 'V3' if verified else 'UNVERIFIED',
        'input_token': source,
        'output_token': target,
        'input_raw': '100',
        'output_raw': '90',
        'fee': 100,
        'fee_status': 'VERIFIED',
        'pool_identity_temporal_limitation': 'TEST',
        'log_evidence_hash': 'evidence',
    }


def transaction(number: int, flows: list[dict]) -> dict:
    return {
        'tx_hash': tx_hash(number),
        'block_number': 100 + number,
        'transaction_index': number,
        'block_time_utc': '2026-01-01T00:00:00+00:00',
        'actor': module.EXPECTED_TARGET_ACTOR,
        'tx_to': module.EXPECTED_TARGET_ACTOR,
        'selector': module.EXPECTED_SELECTOR,
        'gas_cost_wei': '1',
        'receipt_evidence_hash': 'receipt',
        'actor_flow': {
            'actor': module.EXPECTED_TARGET_ACTOR,
            'token_flows': flows,
            'has_inflow': any(item['direction'] == 'IN' for item in flows),
            'has_outflow': any(item['direction'] == 'OUT' for item in flows),
            'two_sided_actor_flow': {item['direction'] for item in flows} == {'IN', 'OUT'},
        },
    }


class ProductSlice04TargetedSwapRouteGraphTests(unittest.TestCase):
    def test_undirected_connected(self):
        a, b, c = address('1'), address('2'), address('3')
        self.assertTrue(module.undirected_connected([edge(a, b), edge(b, c, index=1)]))

    def test_undirected_disconnected(self):
        a, b, c, d = address('1'), address('2'), address('3'), address('4')
        self.assertFalse(module.undirected_connected([edge(a, b), edge(c, d, index=1)]))

    def test_directed_cycle_present(self):
        a, b, c = address('1'), address('2'), address('3')
        self.assertTrue(module.directed_cycle_present([edge(a, b), edge(b, c, index=1), edge(c, a, index=2)]))

    def test_directed_cycle_absent(self):
        a, b, c = address('1'), address('2'), address('3')
        self.assertFalse(module.directed_cycle_present([edge(a, b), edge(b, c, index=1)]))

    def test_actor_flow_endpoint_checks_match(self):
        a, b = address('1'), address('2')
        flow = {
            'token_flows': [
                {'token_address': a, 'symbol': 'A', 'direction': 'OUT', 'net_raw': '-100'},
                {'token_address': b, 'symbol': 'B', 'direction': 'IN', 'net_raw': '90'},
            ]
        }
        checks = module.actor_flow_endpoint_checks(flow, [edge(a, b)])
        self.assertTrue(all(item['matched'] for item in checks))

    def test_actor_flow_endpoint_checks_reject_wrong_role(self):
        a, b = address('1'), address('2')
        flow = {'token_flows': [{'token_address': b, 'symbol': 'B', 'direction': 'OUT', 'net_raw': '-90'}]}
        checks = module.actor_flow_endpoint_checks(flow, [edge(a, b)])
        self.assertFalse(checks[0]['matched'])

    def test_build_transaction_route_usable(self):
        a, b = address('1'), address('2')
        tx = transaction(1, [
            {'token_address': a, 'symbol': 'A', 'direction': 'OUT', 'net_raw': '-100'},
            {'token_address': b, 'symbol': 'B', 'direction': 'IN', 'net_raw': '90'},
        ])
        route = module.build_transaction_route(tx, [edge(a, b)])
        self.assertTrue(route['route_evidence_usable'])
        self.assertTrue(route['self_target_call'])

    def test_build_transaction_route_rejects_unverified_protocol(self):
        a, b = address('1'), address('2')
        tx = transaction(1, [{'token_address': a, 'symbol': 'A', 'direction': 'OUT', 'net_raw': '-100'}])
        route = module.build_transaction_route(tx, [edge(a, b, verified=False)])
        self.assertFalse(route['route_evidence_usable'])

    def test_pair_candidate_route_verified_but_not_closed_loop(self):
        token, counter = address('1'), address('2')
        first_tx = transaction(1, [{'token_address': token, 'symbol': 'T', 'direction': 'OUT', 'net_raw': '-100'}])
        second_tx = transaction(2, [{'token_address': token, 'symbol': 'T', 'direction': 'IN', 'net_raw': '110'}])
        first_route = module.build_transaction_route(first_tx, [edge(token, counter)])
        second_edge = edge(counter, token)
        second_edge['tx_hash'] = tx_hash(2)
        second_route = module.build_transaction_route(second_tx, [second_edge])
        pairs = module.build_pair_candidates([{
            'actor': module.EXPECTED_TARGET_ACTOR,
            'token_address': token,
            'first_tx_hash': tx_hash(1),
            'first_direction': 'OUT',
            'second_tx_hash': tx_hash(2),
            'second_direction': 'IN',
            'block_distance': 10,
        }], {tx_hash(1): first_route, tx_hash(2): second_route})
        self.assertTrue(pairs[0]['route_pair_verified'])
        self.assertFalse(pairs[0]['closed_loop_confirmed'])
        self.assertIn('COUNTERASSET_CONTINUITY_NOT_VERIFIED', pairs[0]['blockers'])

    def test_authority_boundary(self):
        self.assertTrue(module.AUTHORITY['network_access'])
        self.assertTrue(module.AUTHORITY['staging_file_write'])
        for key in (
            'source_database_write', 'production_database_write', 'repository_write',
            'panel_mutation', 'service_mutation', 'timer_mutation', 'paper_trade',
            'live_trade', 'wallet', 'signing', 'order_create', 'broadcast',
        ):
            self.assertFalse(module.AUTHORITY[key], key)


if __name__ == '__main__':
    unittest.main()
