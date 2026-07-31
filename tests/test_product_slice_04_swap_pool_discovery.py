from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_DISCOVERY_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_swap_pool_discovery.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_swap_pool_discovery', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def address_topic(address: str) -> str:
    return '0x' + '0' * 24 + address[2:]


def uint_word(value: int) -> str:
    return value.to_bytes(32, 'big').hex()


def int_word(value: int) -> str:
    if value < 0:
        value = (1 << 256) + value
    return value.to_bytes(32, 'big').hex()



import importlib.util as _archive_importlib_util
from pathlib import Path as _ArchivePath

_archive_contract_path = (
    _ArchivePath(__file__).resolve().parents[1]
    / "tools"
    / "tokenoskobi_product_slice_04_swap_pool_discovery_archive_contract.py"
)
_archive_contract_spec = _archive_importlib_util.spec_from_file_location(
    "product_slice_04_swap_pool_discovery_archive_contract",
    _archive_contract_path,
)
if (
    _archive_contract_spec is None
    or _archive_contract_spec.loader is None
):
    raise RuntimeError("ARCHIVE_CONTRACT_MODULE_LOAD_FAILED")

archive_module = _archive_importlib_util.module_from_spec(
    _archive_contract_spec
)
_archive_contract_spec.loader.exec_module(archive_module)

def valid_enrichment_payload() -> dict:
    transactions = [
        {'tx_hash': '0x' + f'{index:064x}'}
        for index in range(1, 15)
    ]
    metadata = [
        {
            'token_address': '0x' + f'{index:040x}',
            'metadata_temporal_mode': 'LATEST_STATE_FALLBACK_ARCHIVE_UNAVAILABLE',
            'historical_state_verified': False,
            'archive_fallback_used': True,
            'effective_block_tag': 'latest',
        }
        for index in range(1, 4)
    ]
    return {
        'schema': 'tokenoskobi.product_slice_04.candidate_enrichment.v1',
        'status': archive_module.EXPECTED_ENRICHMENT_STATUS,
        'result_hash': archive_module.EXPECTED_ENRICHMENT_RESULT_HASH,
        'metadata_temporal_policy': {
            'historical_block_attempt_required': True,
            'fallback_allowed_only_for_archive_state_unavailable_errors': True,
            'fallback_target': 'latest',
            'historical_metadata_verified_count': 0,
            'latest_metadata_fallback_count': 3,
            'historical_transaction_and_receipt_identity_preserved': True,
            'token_amount_normalization_ready': True,
            'metadata_temporal_limit_explicit': True,
        },
        'transactions': transactions,
        'token_metadata': metadata,
    }


class ProductSlice04SwapPoolDiscoveryTests(unittest.TestCase):
    def test_v2_swap_decode(self):
        sender = '0x' + '1' * 40
        recipient = '0x' + '2' * 40
        log = {
            'topics': [module.V2_SWAP_TOPIC, address_topic(sender), address_topic(recipient)],
            'data': '0x' + ''.join([uint_word(100), uint_word(0), uint_word(0), uint_word(50)]),
        }
        result = module.decode_v2_swap(log)
        self.assertEqual(result['sender'], sender)
        self.assertEqual(result['recipient'], recipient)
        self.assertEqual(result['input_side'], 0)
        self.assertEqual(result['output_side'], 1)
        self.assertTrue(result['direction_unambiguous'])

    def test_v3_standard_swap_decode(self):
        sender = '0x' + '3' * 40
        recipient = '0x' + '4' * 40
        log = {
            'topics': [module.V3_SWAP_TOPIC, address_topic(sender), address_topic(recipient)],
            'data': '0x' + ''.join([
                int_word(100), int_word(-50), uint_word(2**96), uint_word(12345), int_word(-120),
            ]),
        }
        result = module.decode_v3_swap(log, extended=False)
        self.assertEqual(result['event_type'], 'V3_SWAP')
        self.assertEqual(result['input_side'], 0)
        self.assertEqual(result['output_side'], 1)
        self.assertEqual(result['tick'], -120)

    def test_pancake_v3_extended_swap_decode(self):
        sender = '0x' + '5' * 40
        recipient = '0x' + '6' * 40
        log = {
            'topics': [
                module.PANCAKE_V3_EXTENDED_SWAP_TOPIC,
                address_topic(sender),
                address_topic(recipient),
            ],
            'data': '0x' + ''.join([
                int_word(-75), int_word(150), uint_word(2**96), uint_word(999),
                int_word(42), uint_word(3), uint_word(4),
            ]),
        }
        result = module.decode_v3_swap(log, extended=True)
        self.assertEqual(result['event_type'], 'PANCAKE_V3_EXTENDED_SWAP')
        self.assertEqual(result['input_side'], 1)
        self.assertEqual(result['output_side'], 0)
        self.assertEqual(result['protocol_fees_token0_raw'], '3')
        self.assertEqual(result['protocol_fees_token1_raw'], '4')

    def test_signed_word_decode(self):
        self.assertEqual(module.decode_int_word(int_word(-1)), -1)
        self.assertEqual(module.decode_signed_nbit_word(int_word(-120), 24), -120)
        self.assertEqual(module.decode_signed_nbit_word(int_word(120), 24), 120)

    def test_address_result_decode(self):
        address = '0x' + 'a' * 40
        encoded = '0x' + '0' * 24 + address[2:]
        self.assertEqual(module.decode_address_result(encoded, 'address'), address)

    def test_actor_flow_pair_match(self):
        token0 = '0x' + '7' * 40
        token1 = '0x' + '8' * 40
        tx = {'actor_flow': {'token_flows': [{'token_address': token0}, {'token_address': token1}]}}
        result = module.actor_flow_pair_match(tx, token0, token1)
        self.assertTrue(result['matched'])
        self.assertEqual(result['status'], 'EXACT_PAIR')

    def test_actor_flow_subset_is_rejected(self):
        token0 = '0x' + '7' * 40
        token1 = '0x' + '8' * 40
        tx = {'actor_flow': {'token_flows': [{'token_address': token0}]}}
        result = module.actor_flow_pair_match(tx, token0, token1)
        self.assertFalse(result['matched'])
        self.assertEqual(result['status'], 'PARTIAL_OR_NON_PAIR')

    def test_actor_flow_superset_is_rejected(self):
        token0 = '0x' + '7' * 40
        token1 = '0x' + '8' * 40
        token2 = '0x' + '9' * 40
        tx = {
            'actor_flow': {
                'token_flows': [
                    {'token_address': token0},
                    {'token_address': token1},
                    {'token_address': token2},
                ]
            }
        }
        result = module.actor_flow_pair_match(tx, token0, token1)
        self.assertFalse(result['matched'])
        self.assertEqual(result['status'], 'PARTIAL_OR_NON_PAIR')

    def test_actor_flow_duplicate_token_rows_are_rejected(self):
        token0 = '0x' + '7' * 40
        token1 = '0x' + '8' * 40
        tx = {
            'actor_flow': {
                'token_flows': [
                    {'token_address': token0},
                    {'token_address': token0},
                ]
            }
        }
        result = module.actor_flow_pair_match(tx, token0, token1)
        self.assertFalse(result['matched'])
        self.assertEqual(result['status'], 'PARTIAL_OR_NON_PAIR')

    def test_authority_boundary(self):
        self.assertTrue(module.AUTHORITY['network_access'])
        self.assertTrue(module.AUTHORITY['staging_file_write'])
        for key in (
            'source_database_write', 'production_database_write', 'repository_write',
            'panel_mutation', 'service_mutation', 'timer_mutation', 'paper_trade',
            'live_trade', 'wallet', 'signing', 'order_create', 'broadcast',
        ):
            self.assertFalse(module.AUTHORITY[key], key)

    def test_archive_fallback_enrichment_contract_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'enrichment.json'
            path.write_text(json.dumps(valid_enrichment_payload()), encoding='utf-8')
            result = archive_module.load_enrichment(path)
        self.assertEqual(len(result['tx_map']), 14)
        self.assertEqual(len(result['metadata_map']), 3)
        self.assertEqual(result['result_hash'], archive_module.EXPECTED_ENRICHMENT_RESULT_HASH)

    def test_archive_fallback_enrichment_rejects_wrong_counts(self):
        payload = valid_enrichment_payload()
        payload['metadata_temporal_policy']['latest_metadata_fallback_count'] = 2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'enrichment.json'
            path.write_text(json.dumps(payload), encoding='utf-8')
            with self.assertRaises(archive_module.Slice04SwapDiscoveryError):
                archive_module.load_enrichment(path)

    def test_archive_fallback_enrichment_rejects_wrong_result_hash(self):
        payload = valid_enrichment_payload()
        payload['result_hash'] = '0' * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'enrichment.json'
            path.write_text(json.dumps(payload), encoding='utf-8')
            with self.assertRaises(archive_module.Slice04SwapDiscoveryError):
                archive_module.load_enrichment(path)


if __name__ == '__main__':
    unittest.main()
