from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(os.environ.get('PRODUCT_SLICE_04_MODULE_PATH', 'tools/tokenoskobi_product_slice_04_candidate_enrichment.py'))
spec = importlib.util.spec_from_file_location('product_slice_04_candidate_enrichment', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProductSlice04CandidateEnrichmentTests(unittest.TestCase):
    def test_candidate_set_is_exact_and_unique(self):
        self.assertEqual(len(module.CANDIDATE_TX_HASHES), 14)
        self.assertEqual(len(set(module.CANDIDATE_TX_HASHES)), 14)
        for item in module.CANDIDATE_TX_HASHES:
            self.assertEqual(module.normalize_hash(item), item)

    def test_token_set_is_exact_and_unique(self):
        self.assertEqual(len(module.TRACKED_TOKENS), 3)
        self.assertEqual(len(set(module.TRACKED_TOKENS)), 3)
        for item in module.TRACKED_TOKENS:
            self.assertEqual(module.normalize_address(item), item)

    def test_decode_uint256(self):
        self.assertEqual(module.decode_uint256('0x' + '0' * 63 + '6'), 6)
        self.assertEqual(module.decode_uint256('0x' + '0' * 62 + '12'), 18)

    def test_decode_dynamic_abi_string(self):
        text = b'USDT'
        payload = (32).to_bytes(32, 'big') + len(text).to_bytes(32, 'big') + text.ljust(32, b'\x00')
        self.assertEqual(module.decode_abi_string('0x' + payload.hex()), 'USDT')

    def test_decode_bytes32_abi_string(self):
        self.assertEqual(module.decode_abi_string('0x' + b'WBNB'.ljust(32, b'\x00').hex()), 'WBNB')

    def test_normalized_decimal(self):
        self.assertEqual(module.normalized_decimal(1_000_000, 6), '1')
        self.assertEqual(module.normalized_decimal(123_450_000, 6), '123.45')
        self.assertEqual(module.normalized_decimal(10**18, 18), '1')

    def test_actor_flow_is_normalized(self):
        actor = '0x' + '1' * 40
        pool = '0x' + '2' * 40
        token_a, token_b = module.TRACKED_TOKENS[:2]
        metadata = {
            token_a: {'symbol': 'USDT', 'decimals': 18},
            token_b: {'symbol': 'WBNB', 'decimals': 18},
        }
        result = module.build_actor_flow(
            {'actor': actor},
            [
                {'token_address': token_a, 'amount_raw': str(2 * 10**18), 'from_address': actor, 'to_address': pool},
                {'token_address': token_b, 'amount_raw': str(10**18), 'from_address': pool, 'to_address': actor},
            ],
            metadata,
        )
        self.assertTrue(result['two_sided_actor_flow'])
        self.assertEqual([row['direction'] for row in result['token_flows']], ['OUT', 'IN'])

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
