from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_RPC_CAPABILITY_PROBE_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_rpc_eth_getlogs_capability_probe.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_rpc_capability_probe', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeBase:
    TRANSFER_TOPIC = '0x' + 'd' * 64

    @staticmethod
    def build_log_filter(anchor: dict[str, object], start: int, end: int) -> dict[str, object]:
        actor_topic = module.topic_address(anchor['actor'])
        if anchor['missing_direction'] == 'OUT':
            topics = [FakeBase.TRANSFER_TOPIC, actor_topic]
        else:
            topics = [FakeBase.TRANSFER_TOPIC, None, actor_topic]
        return {
            'address': anchor['token'],
            'fromBlock': hex(start),
            'toBlock': hex(end),
            'topics': topics,
        }


def address(char: str) -> str:
    return '0x' + char * 40


def tx_hash(char: str) -> str:
    return '0x' + char * 64


class RpcCapabilityProbeTests(unittest.TestCase):
    def test_normalize_address(self) -> None:
        self.assertEqual(module.normalize_address(address('a').upper().replace('0X', '0x')), address('a'))

    def test_invalid_address_fails_closed(self) -> None:
        with self.assertRaisesRegex(module.Slice04RpcCapabilityProbeError, 'INVALID_EVM_ADDRESS'):
            module.normalize_address('0x1234')

    def test_topic_address(self) -> None:
        self.assertEqual(module.topic_address(address('b')), '0x' + '0' * 24 + 'b' * 40)

    def test_known_event_filter_is_exact(self) -> None:
        event = {
            'token_address': address('1'),
            'from_address': address('2'),
            'to_address': address('3'),
            'block_number': 99,
        }
        value = module.known_event_filter(FakeBase, event)
        self.assertEqual(value['fromBlock'], hex(99))
        self.assertEqual(value['toBlock'], hex(99))
        self.assertEqual(value['topics'][1], module.topic_address(address('2')))
        self.assertEqual(value['topics'][2], module.topic_address(address('3')))

    def test_historical_anchor_filter_is_single_block(self) -> None:
        anchor = {'actor': address('a'), 'token': address('1'), 'missing_direction': 'OUT'}
        value = module.historical_anchor_filter(FakeBase, anchor)
        expected = hex(module.FAILED_HISTORICAL_BLOCK)
        self.assertEqual(value['fromBlock'], expected)
        self.assertEqual(value['toBlock'], expected)

    def test_summarize_known_exact_event(self) -> None:
        expected = {'tx_hash': tx_hash('a'), 'log_index': 7}
        probe = {
            'ok': True,
            'result': [{'transactionHash': tx_hash('a'), 'logIndex': hex(7)}],
        }
        result = module.summarize_log_result(probe, expected)
        self.assertTrue(result['ok'])
        self.assertTrue(result['exact_known_event_found'])
        self.assertEqual(result['count'], 1)

    def test_summarize_rpc_error(self) -> None:
        result = module.summarize_log_result({'ok': False, 'error': "{'code': -32005}"})
        self.assertFalse(result['ok'])
        self.assertEqual(result['error'], "{'code': -32005}")

    def test_endpoint_classification_available(self) -> None:
        result = {
            'chain_id': {'ok': True, 'value': 56},
            'known_block': {'ok': True},
            'known_exact_log': {'ok': True, 'exact_known_event_found': True},
            'historical_single_actor_single_block': {'ok': True},
        }
        self.assertEqual(
            module.classify_endpoint(result),
            'ETH_GETLOGS_AVAILABLE_FOR_EXACT_HISTORICAL_FILTER',
        )

    def test_overall_classification_historical_restriction(self) -> None:
        endpoint_results = [
            {'classification': 'ETH_GETLOGS_KNOWN_EVENT_OK_HISTORICAL_FILTER_REJECTED'},
            {'classification': 'ETH_GETLOGS_UNUSABLE_ON_KNOWN_EXACT_EVENT'},
        ]
        self.assertEqual(
            module.classify_overall(endpoint_results),
            'CURRENT_ENDPOINT_SET_HAS_HISTORICAL_FILTER_OR_DEPTH_RESTRICTION',
        )

    def test_authority_keeps_financial_paths_disabled(self) -> None:
        self.assertTrue(module.AUTHORITY['network_access'])
        for key in ('paper_trade', 'live_trade', 'wallet', 'signing', 'order_create', 'broadcast'):
            self.assertFalse(module.AUTHORITY[key], key)


if __name__ == '__main__':
    unittest.main()
