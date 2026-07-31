from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_CHAIN_SELECTION_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_first_swap_chain_selection.py',
    )
)
ALLOWLIST_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_FACTORY_ALLOWLIST_PATH',
        'config/product_slice_04_factory_allowlist_v1.json',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_chain_selection', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def address(char: str) -> str:
    return '0x' + char * 40


def tx_hash(number: int) -> str:
    return '0x' + f'{number:064x}'


def v3_event(input_token: str, output_token: str, *, input_raw: int = 100, output_raw: int = 50) -> dict:
    return {
        'swap': {
            'event_type': 'PANCAKE_V3_EXTENDED_SWAP',
            'direction_unambiguous': True,
            'input_side': 0,
            'output_side': 1,
            'input_token': input_token,
            'output_token': output_token,
            'amount0_delta_raw': str(input_raw),
            'amount1_delta_raw': str(-output_raw),
        },
        'pool_identity': {
            'factory': address('a'),
            'pool_address': address('b'),
            'token0': input_token,
            'token1': output_token,
        },
    }


def actor_transaction(input_token: str, output_token: str, *, input_raw: int = 100, output_raw: int = 50) -> dict:
    return {
        'actor_flow': {
            'has_inflow': True,
            'has_outflow': True,
            'two_sided_actor_flow': True,
            'token_flows': [
                {
                    'token_address': input_token,
                    'direction': 'OUT',
                    'net_raw': str(-input_raw),
                },
                {
                    'token_address': output_token,
                    'direction': 'IN',
                    'net_raw': str(output_raw),
                },
            ],
        }
    }


def record(
    *,
    number: int,
    block: int,
    actor: str,
    pool: str,
    input_token: str,
    output_token: str,
    count: int = 1,
) -> dict:
    return {
        'strict_verified_event': True,
        'tx_hash': tx_hash(number),
        'block_number': block,
        'receipt_log_index': 1,
        'actor': actor,
        'pool_address': pool,
        'protocol_id': 'PANCAKESWAP_V3',
        'input_token': input_token,
        'output_token': output_token,
        'transaction_swap_event_count': count,
    }


class ProductSlice04ChainSelectionTests(unittest.TestCase):
    def test_official_factory_allowlist_contract(self):
        payload = json.loads(ALLOWLIST_PATH.read_text(encoding='utf-8'))
        result = module.validate_allowlist(payload)
        self.assertEqual(len(result), 4)
        self.assertEqual(
            result['0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865']['protocol_id'],
            'PANCAKESWAP_V3',
        )
        self.assertEqual(
            result['0xca143ce32fe78f1f7019d7d551a6402fc5350c73']['protocol_id'],
            'PANCAKESWAP_V2',
        )
        self.assertEqual(
            result['0xdb1d10011ad0ff90774d0c6bb92e5c5c8b4461f7']['protocol_id'],
            'UNISWAP_V3',
        )
        self.assertEqual(
            result['0x8909dc15e40173ff4699343b6eb8132c65e18ec6']['protocol_id'],
            'UNISWAP_V2',
        )

    def test_v2_event_amount_decode(self):
        event = {
            'swap': {
                'event_type': 'V2_SWAP',
                'direction_unambiguous': True,
                'input_side': 1,
                'output_side': 0,
                'amount0_in_raw': '0',
                'amount1_in_raw': '123',
                'amount0_out_raw': '45',
                'amount1_out_raw': '0',
            }
        }
        self.assertEqual(module.event_raw_amounts(event), (123, 45))

    def test_v3_event_amount_decode(self):
        event = v3_event(address('1'), address('2'), input_raw=123, output_raw=45)
        self.assertEqual(module.event_raw_amounts(event), (123, 45))

    def test_strict_actor_event_match_accepts_full_pair_direction_and_amount(self):
        token0, token1 = address('1'), address('2')
        result = module.strict_actor_event_match(
            v3_event(token0, token1),
            actor_transaction(token0, token1),
        )
        self.assertTrue(result['full_pair_equality'])
        self.assertTrue(result['direction_match'])
        self.assertTrue(result['strict_event_match'])

    def test_subset_match_is_rejected(self):
        token0, token1 = address('1'), address('2')
        transaction = actor_transaction(token0, token1)
        transaction['actor_flow']['token_flows'] = transaction['actor_flow']['token_flows'][:1]
        transaction['actor_flow']['has_inflow'] = False
        transaction['actor_flow']['two_sided_actor_flow'] = False
        result = module.strict_actor_event_match(v3_event(token0, token1), transaction)
        self.assertFalse(result['full_pair_equality'])
        self.assertFalse(result['strict_event_match'])

    def test_wrong_direction_is_rejected(self):
        token0, token1 = address('1'), address('2')
        transaction = actor_transaction(token0, token1)
        transaction['actor_flow']['token_flows'][0]['direction'] = 'IN'
        result = module.strict_actor_event_match(v3_event(token0, token1), transaction)
        self.assertFalse(result['direction_match'])
        self.assertFalse(result['strict_event_match'])

    def test_amount_mismatch_is_rejected(self):
        token0, token1 = address('1'), address('2')
        transaction = actor_transaction(token0, token1, input_raw=101)
        result = module.strict_actor_event_match(v3_event(token0, token1), transaction)
        self.assertTrue(result['direction_match'])
        self.assertFalse(result['input_amount_exact'])
        self.assertFalse(result['strict_event_match'])

    def test_clean_opposite_direction_chain_is_confirmed(self):
        actor, pool = address('3'), address('4')
        token0, token1 = address('1'), address('2')
        candidates = module.build_chain_candidates([
            record(number=1, block=100, actor=actor, pool=pool, input_token=token0, output_token=token1),
            record(number=2, block=200, actor=actor, pool=pool, input_token=token1, output_token=token0),
        ])
        self.assertEqual(len(candidates), 1)
        self.assertTrue(candidates[0]['closed_loop_confirmed'])
        self.assertEqual(candidates[0]['blockers'], [])

    def test_different_actor_chain_is_rejected(self):
        actor1, actor2, pool = address('3'), address('5'), address('4')
        token0, token1 = address('1'), address('2')
        candidates = module.build_chain_candidates([
            record(number=1, block=100, actor=actor1, pool=pool, input_token=token0, output_token=token1),
            record(number=2, block=200, actor=actor2, pool=pool, input_token=token1, output_token=token0),
        ])
        self.assertEqual(candidates, [])

    def test_non_increasing_chronology_is_rejected(self):
        actor, pool = address('3'), address('4')
        token0, token1 = address('1'), address('2')
        candidates = module.build_chain_candidates([
            record(number=1, block=100, actor=actor, pool=pool, input_token=token0, output_token=token1),
            record(number=2, block=100, actor=actor, pool=pool, input_token=token1, output_token=token0),
        ])
        self.assertEqual(len(candidates), 1)
        self.assertFalse(candidates[0]['closed_loop_confirmed'])
        self.assertIn('CHRONOLOGY_NOT_STRICT', candidates[0]['blockers'])

    def test_multi_swap_transaction_blocks_confirmation(self):
        actor, pool = address('3'), address('4')
        token0, token1 = address('1'), address('2')
        candidates = module.build_chain_candidates([
            record(number=1, block=100, actor=actor, pool=pool, input_token=token0, output_token=token1),
            record(number=2, block=200, actor=actor, pool=pool, input_token=token1, output_token=token0, count=3),
        ])
        self.assertEqual(len(candidates), 1)
        self.assertFalse(candidates[0]['closed_loop_confirmed'])
        self.assertIn('MULTI_SWAP_TRANSACTION_PRESENT', candidates[0]['blockers'])

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
