from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_BSCSCAN_PROVIDER_PROBE_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_bscscan_indexed_provider_probe.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_bscscan_probe', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def address(char: str) -> str:
    return '0x' + char * 40


def tx_hash(char: str) -> str:
    return '0x' + char * 64


class BscScanIndexedProviderProbeTests(unittest.TestCase):
    def test_normalize_address(self) -> None:
        self.assertEqual(module.normalize_address(address('A')), address('a'))

    def test_invalid_address_fails_closed(self) -> None:
        with self.assertRaisesRegex(module.Slice04BscScanProbeError, 'INVALID_EVM_ADDRESS'):
            module.normalize_address('0x1234')

    def test_build_query_is_allowlisted_and_bounded(self) -> None:
        url = module.build_query(
            address=address('a'),
            token=address('1'),
            start_block=10,
            end_block=20,
            api_key='',
        )
        self.assertTrue(url.startswith('https://api.bscscan.com/api?'))
        self.assertIn('action=tokentx', url)
        self.assertIn('startblock=10', url)
        self.assertNotIn('apikey=', url)

    def test_build_query_includes_key_without_exposing_elsewhere(self) -> None:
        url = module.build_query(
            address=address('a'),
            token=address('1'),
            start_block=10,
            end_block=10,
            api_key='secret-key',
        )
        self.assertIn('apikey=secret-key', url)

    def test_parse_success_response(self) -> None:
        ok, rows, error = module.parse_tokentx_response(
            {'status': '1', 'message': 'OK', 'result': [{'hash': tx_hash('1')}]}
        )
        self.assertTrue(ok)
        self.assertEqual(len(rows), 1)
        self.assertEqual(error, '')

    def test_parse_no_transactions_is_success(self) -> None:
        ok, rows, error = module.parse_tokentx_response(
            {'status': '0', 'message': 'No transactions found', 'result': []}
        )
        self.assertTrue(ok)
        self.assertEqual(rows, [])
        self.assertEqual(error, '')

    def test_credential_required_detection(self) -> None:
        payload = {'status': '0', 'message': 'NOTOK', 'result': 'Missing/Invalid API Key'}
        self.assertTrue(module.credential_required(payload))

    def test_exact_event_found(self) -> None:
        event = {
            'tx_hash': tx_hash('1'),
            'block_number': 100,
            'token_address': address('2'),
            'from_address': address('a'),
            'to_address': address('b'),
            'amount_raw': '123',
        }
        rows = [{
            'hash': tx_hash('1'),
            'blockNumber': '100',
            'contractAddress': address('2'),
            'from': address('a'),
            'to': address('b'),
            'value': '123',
        }]
        self.assertTrue(module.exact_event_found(rows, event))

    def test_classify_usable(self) -> None:
        classification, next_step = module.classify_probe(
            known_ok=True,
            known_exact=True,
            historical_ok=True,
            known_payload={'status': '1', 'result': []},
            historical_payload={'status': '1', 'result': []},
        )
        self.assertEqual(classification, 'BSCSCAN_INDEXED_PROVIDER_USABLE')
        self.assertIn('IMPLEMENT_BSCSCAN', next_step)

    def test_classify_key_required(self) -> None:
        payload = {'status': '0', 'message': 'NOTOK', 'result': 'Max rate limit reached, please use API Key'}
        classification, next_step = module.classify_probe(
            known_ok=False,
            known_exact=False,
            historical_ok=False,
            known_payload=payload,
            historical_payload=payload,
        )
        self.assertEqual(classification, 'BSCSCAN_FREE_API_KEY_REQUIRED')
        self.assertIn('LOCAL_SECRET_FILE', next_step)


if __name__ == '__main__':
    unittest.main()
