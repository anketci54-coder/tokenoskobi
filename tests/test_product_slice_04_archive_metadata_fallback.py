from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

WRAPPER_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_WRAPPER_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_candidate_enrichment_archive_fallback.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_archive_fallback', WRAPPER_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def abi_uint(value: int) -> str:
    return '0x' + value.to_bytes(32, 'big').hex()


def abi_string(value: str) -> str:
    raw = value.encode('utf-8')
    payload = (32).to_bytes(32, 'big') + len(raw).to_bytes(32, 'big') + raw.ljust(32, b'\x00')
    return '0x' + payload.hex()


class FakeClient:
    def __init__(self, *, historical_failure: str | None = None):
        self.historical_failure = historical_failure
        self.last_endpoint_host = 'bsc-dataseed.bnbchain.org'
        self.calls: list[tuple[str, list[object]]] = []

    def call(self, method: str, params: list[object]):
        self.calls.append((method, params))
        block_tag = str(params[1])
        if block_tag != 'latest' and self.historical_failure:
            raise module.base.Slice04EnrichmentError(self.historical_failure)
        selector = str(params[0]['data'])
        if selector == module.base.TOKEN_CALLS['decimals']:
            return abi_uint(18)
        if selector == module.base.TOKEN_CALLS['symbol']:
            return abi_string('TEST')
        if selector == module.base.TOKEN_CALLS['name']:
            return abi_string('Test Token')
        raise AssertionError(selector)


class ProductSlice04ArchiveMetadataFallbackTests(unittest.TestCase):
    def test_archive_error_classifier_accepts_missing_trie_node(self):
        exc = module.base.Slice04EnrichmentError('RPC_RESPONSE_INVALID: missing trie node')
        self.assertTrue(module.is_archive_state_unavailable_error(exc))

    def test_archive_error_classifier_rejects_unrelated_rpc_error(self):
        exc = module.base.Slice04EnrichmentError('RPC_RESPONSE_INVALID: execution reverted')
        self.assertFalse(module.is_archive_state_unavailable_error(exc))

    def test_latest_fallback_is_used_only_after_archive_failure(self):
        client = FakeClient(historical_failure='ALL_RPC_ENDPOINTS_FAILED:eth_call:missing trie node')
        result = module.fetch_token_metadata_with_archive_fallback(
            client,
            module.base.TRACKED_TOKENS[0],
            111858091,
        )
        self.assertTrue(result['archive_fallback_used'])
        self.assertFalse(result['historical_state_verified'])
        self.assertEqual(result['effective_block_tag'], 'latest')
        self.assertEqual(result['decimals'], 18)
        self.assertEqual(result['symbol'], 'TEST')
        self.assertEqual(result['name'], 'Test Token')
        self.assertEqual([str(params[1]) for _, params in client.calls[-3:]], ['latest'] * 3)

    def test_historical_success_does_not_use_fallback(self):
        client = FakeClient()
        result = module.fetch_token_metadata_with_archive_fallback(
            client,
            module.base.TRACKED_TOKENS[0],
            111858091,
        )
        self.assertFalse(result['archive_fallback_used'])
        self.assertTrue(result['historical_state_verified'])
        self.assertEqual(result['effective_block_tag'], hex(111858091))
        self.assertEqual(len(client.calls), 3)

    def test_unrelated_error_fails_closed(self):
        client = FakeClient(historical_failure='RPC_RESPONSE_INVALID: execution reverted')
        with self.assertRaises(module.base.Slice04EnrichmentError):
            module.fetch_token_metadata_with_archive_fallback(
                client,
                module.base.TRACKED_TOKENS[0],
                111858091,
            )


if __name__ == '__main__':
    unittest.main()
