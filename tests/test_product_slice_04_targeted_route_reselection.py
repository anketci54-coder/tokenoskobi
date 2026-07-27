from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_TARGETED_ROUTE_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_targeted_route_reselection.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_targeted_route', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def address(char: str) -> str:
    return '0x' + char * 40


def address_topic(value: str) -> str:
    return '0x' + '0' * 24 + value[2:]


def transfer_log(token: str, src: str, dst: str, amount: int) -> dict:
    return {
        'address': token,
        'topics': [module.TRANSFER_TOPIC, address_topic(src), address_topic(dst)],
        'data': '0x' + amount.to_bytes(32, 'big').hex(),
    }


def v3_event(input_token: str, output_token: str, input_raw: int, output_raw: int) -> dict:
    return {
        'swap': {
            'event_type': 'V3_SWAP',
            'input_side': 0,
            'output_side': 1,
            'input_token': input_token,
            'output_token': output_token,
            'amount0_delta_raw': str(input_raw),
            'amount1_delta_raw': str(-output_raw),
        }
    }


class ProductSlice04TargetedRouteTests(unittest.TestCase):
    def test_transfer_decode(self):
        token, src, dst = address('1'), address('2'), address('3')
        decoded = module.decode_transfer_log(transfer_log(token, src, dst, 125))
        self.assertEqual(decoded['token_address'], token)
        self.assertEqual(decoded['from_address'], src)
        self.assertEqual(decoded['to_address'], dst)
        self.assertEqual(decoded['amount_raw'], 125)

    def test_actor_net_from_all_receipt_transfers(self):
        actor, pool = address('a'), address('b')
        token0, token1 = address('1'), address('2')
        logs = [
            transfer_log(token0, actor, pool, 100),
            transfer_log(token1, pool, actor, 60),
        ]
        self.assertEqual(
            module.actor_net_from_receipt(logs, actor),
            {token0: -100, token1: 60},
        )

    def test_multi_hop_swap_net_cancels_intermediate_token(self):
        token0, mid, token1 = address('1'), address('2'), address('3')
        events = [
            v3_event(token0, mid, 100, 80),
            v3_event(mid, token1, 80, 60),
        ]
        self.assertEqual(
            module.aggregate_swap_net(events),
            {token0: -100, token1: 60},
        )

    def test_exact_multi_hop_route_is_verified(self):
        token0, mid, token1 = address('1'), address('2'), address('3')
        events = [
            v3_event(token0, mid, 100, 80),
            v3_event(mid, token1, 80, 60),
        ]
        result = module.classify_transaction_route(
            {token0: -100, token1: 60}, events, recognized_event_count=2, unverified_event_count=0
        )
        self.assertTrue(result['exact_token_set'])
        self.assertTrue(result['exact_raw_amounts'])
        self.assertTrue(result['route_verified'])
        self.assertEqual(result['route_input_token'], token0)
        self.assertEqual(result['route_output_token'], token1)

    def test_raw_amount_mismatch_is_rejected(self):
        token0, token1 = address('1'), address('2')
        result = module.classify_transaction_route(
            {token0: -99, token1: 60},
            [v3_event(token0, token1, 100, 60)],
            recognized_event_count=1,
            unverified_event_count=0,
        )
        self.assertFalse(result['route_verified'])
        self.assertIn('ACTOR_SWAP_NET_RAW_AMOUNT_MISMATCH', result['blockers'])

    def test_unverified_factory_event_blocks_route(self):
        token0, token1 = address('1'), address('2')
        result = module.classify_transaction_route(
            {token0: -100, token1: 60},
            [v3_event(token0, token1, 100, 60)],
            recognized_event_count=2,
            unverified_event_count=1,
        )
        self.assertFalse(result['route_verified'])
        self.assertIn('UNVERIFIED_FACTORY_EVENT_PRESENT', result['blockers'])

    def test_full_position_reversal_confirms_closed_loop(self):
        actor = address('a')
        base, position = address('1'), address('2')
        records = [
            {
                'tx_hash': '0x' + '1' * 64,
                'actor': actor,
                'block_number': 10,
                'transaction_index': 1,
                'protocol_ids': ['PANCAKESWAP_V3'],
                'pool_addresses': [address('3')],
                'route': {
                    'route_verified': True,
                    'route_input_token': base,
                    'route_output_token': position,
                    'route_input_raw': '100',
                    'route_output_raw': '50',
                },
            },
            {
                'tx_hash': '0x' + '2' * 64,
                'actor': actor,
                'block_number': 20,
                'transaction_index': 1,
                'protocol_ids': ['PANCAKESWAP_V3'],
                'pool_addresses': [address('4')],
                'route': {
                    'route_verified': True,
                    'route_input_token': position,
                    'route_output_token': base,
                    'route_input_raw': '50',
                    'route_output_raw': '110',
                },
            },
        ]
        candidates = module.build_closed_loop_candidates(records)
        self.assertEqual(len(candidates), 1)
        self.assertTrue(candidates[0]['closed_loop_confirmed'])
        self.assertEqual(candidates[0]['base_received_raw'], '110')

    def test_partial_position_reversal_is_not_confirmed(self):
        actor = address('a')
        base, position = address('1'), address('2')
        records = [
            {
                'tx_hash': '0x' + '1' * 64,
                'actor': actor,
                'block_number': 10,
                'transaction_index': 1,
                'protocol_ids': ['PANCAKESWAP_V3'],
                'pool_addresses': [address('3')],
                'route': {
                    'route_verified': True,
                    'route_input_token': base,
                    'route_output_token': position,
                    'route_input_raw': '100',
                    'route_output_raw': '50',
                },
            },
            {
                'tx_hash': '0x' + '2' * 64,
                'actor': actor,
                'block_number': 20,
                'transaction_index': 1,
                'protocol_ids': ['UNISWAP_V3'],
                'pool_addresses': [address('4')],
                'route': {
                    'route_verified': True,
                    'route_input_token': position,
                    'route_output_token': base,
                    'route_input_raw': '40',
                    'route_output_raw': '90',
                },
            },
        ]
        candidate = module.build_closed_loop_candidates(records)[0]
        self.assertFalse(candidate['closed_loop_confirmed'])
        self.assertIn('POSITION_TOKEN_AMOUNT_NOT_FULLY_CLOSED', candidate['blockers'])

    def test_same_pool_and_same_protocol_are_not_required(self):
        actor = address('a')
        base, position = address('1'), address('2')
        records = [
            {
                'tx_hash': '0x' + '1' * 64,
                'actor': actor,
                'block_number': 10,
                'transaction_index': 1,
                'protocol_ids': ['PANCAKESWAP_V3'],
                'pool_addresses': [address('3')],
                'route': {'route_verified': True, 'route_input_token': base, 'route_output_token': position, 'route_input_raw': '100', 'route_output_raw': '50'},
            },
            {
                'tx_hash': '0x' + '2' * 64,
                'actor': actor,
                'block_number': 20,
                'transaction_index': 1,
                'protocol_ids': ['UNISWAP_V3'],
                'pool_addresses': [address('4')],
                'route': {'route_verified': True, 'route_input_token': position, 'route_output_token': base, 'route_input_raw': '50', 'route_output_raw': '101'},
            },
        ]
        self.assertTrue(module.build_closed_loop_candidates(records)[0]['closed_loop_confirmed'])

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
