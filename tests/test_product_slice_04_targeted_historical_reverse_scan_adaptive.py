from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_HISTORICAL_REVERSE_SCAN_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_targeted_historical_reverse_scan_adaptive.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_historical_reverse_scan_adaptive', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def address(char: str) -> str:
    return '0x' + char * 40


def topic(char: str) -> str:
    return '0x' + '0' * 24 + char * 40


def log(block: int, index: int, actor_char: str = 'a') -> dict[str, object]:
    return {
        'address': address('1'),
        'blockNumber': hex(block),
        'transactionHash': '0x' + f'{block:064x}',
        'logIndex': hex(index),
        'blockHash': '0x' + f'{block + 1:064x}',
        'topics': [module.base.TRANSFER_TOPIC, topic(actor_char), topic('b')],
        'data': '0x1',
        'removed': False,
    }


class AdaptiveHistoricalReverseScanTests(unittest.TestCase):
    def test_limit_error_detection_code(self) -> None:
        exc = module.base.Slice04HistoricalReverseScanError(
            "RPC_RESPONSE_INVALID:{'code': -32005, 'message': 'limit exceeded'}"
        )
        self.assertTrue(module.is_limit_exceeded_error(exc))

    def test_unrelated_error_not_limit(self) -> None:
        exc = module.base.Slice04HistoricalReverseScanError('RPC_RESPONSE_INVALID:timeout')
        self.assertFalse(module.is_limit_exceeded_error(exc))

    def test_parse_filter_range(self) -> None:
        self.assertEqual(module.parse_filter_range({'fromBlock': '0x10', 'toBlock': '0x20'}), (16, 32))

    def test_group_filter_out(self) -> None:
        source = {'address': address('1'), 'fromBlock': '0x1', 'toBlock': '0x2', 'topics': [module.base.TRANSFER_TOPIC, topic('a')]}
        grouped = module.group_filter_for_actors(source, 'OUT', [topic('b'), topic('a')])
        self.assertEqual(grouped['topics'][1], [topic('a'), topic('b')])

    def test_group_filter_in(self) -> None:
        source = {'address': address('1'), 'fromBlock': '0x1', 'toBlock': '0x2', 'topics': [module.base.TRANSFER_TOPIC, None, topic('a')]}
        grouped = module.group_filter_for_actors(source, 'IN', [topic('b'), topic('a')])
        self.assertEqual(grouped['topics'][2], [topic('a'), topic('b')])

    def test_adaptive_split_only_on_limit(self) -> None:
        calls: list[tuple[int, int]] = []

        def call_once(value: dict[str, object]) -> list[dict[str, object]]:
            start, end = module.parse_filter_range(value)
            calls.append((start, end))
            if end - start + 1 > 4:
                raise module.base.Slice04HistoricalReverseScanError(
                    "RPC_RESPONSE_INVALID:{'code': -32005, 'message': 'limit exceeded'}"
                )
            return [log(start, 0)]

        value = {'address': address('1'), 'fromBlock': '0x0', 'toBlock': '0x7', 'topics': [module.base.TRANSFER_TOPIC, topic('a')]}
        result, splits, learned = module.adaptive_fetch(call_once, value)
        self.assertEqual(splits, 1)
        self.assertEqual(learned, 4)
        self.assertEqual(len(result), 2)
        self.assertEqual(calls, [(0, 7), (0, 3), (4, 7)])

    def test_preferred_span_avoids_initial_oversized_call(self) -> None:
        calls: list[tuple[int, int]] = []

        def call_once(value: dict[str, object]) -> list[dict[str, object]]:
            current = module.parse_filter_range(value)
            calls.append(current)
            return []

        value = {'address': address('1'), 'fromBlock': '0x0', 'toBlock': '0x7', 'topics': [module.base.TRANSFER_TOPIC, topic('a')]}
        _, splits, learned = module.adaptive_fetch(call_once, value, preferred_span=4)
        self.assertEqual(splits, 0)
        self.assertEqual(learned, 4)
        self.assertEqual(calls, [(0, 3), (4, 7)])

    def test_single_block_limit_fails_closed(self) -> None:
        def call_once(_: dict[str, object]) -> list[dict[str, object]]:
            raise module.base.Slice04HistoricalReverseScanError(
                "RPC_RESPONSE_INVALID:{'code': -32005, 'message': 'limit exceeded'}"
            )

        value = {'address': address('1'), 'fromBlock': '0x5', 'toBlock': '0x5', 'topics': [module.base.TRANSFER_TOPIC, topic('a')]}
        with self.assertRaisesRegex(module.base.Slice04HistoricalReverseScanError, 'ETH_GET_LOGS_LIMIT_AT_SINGLE_BLOCK'):
            module.adaptive_fetch(call_once, value)

    def test_dedupe_and_sort_logs(self) -> None:
        first = log(2, 0)
        second = log(1, 0)
        self.assertEqual(module.dedupe_logs([first, second, first]), [second, first])

    def test_filter_logs_for_actor(self) -> None:
        selected = module.filter_logs_for_actor([log(1, 0, 'a'), log(2, 0, 'c')], 'OUT', topic('a'))
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['blockNumber'], '0x1')


if __name__ == '__main__':
    unittest.main()
