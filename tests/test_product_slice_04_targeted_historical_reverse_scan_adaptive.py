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
    unique = block * 1000 + index
    return {
        'address': address('1'),
        'blockNumber': hex(block),
        'transactionHash': '0x' + f'{unique:064x}',
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

    def test_group_filter_uses_scalar_for_one_actor_and_or_list_for_multiple(self) -> None:
        out_source = {
            'address': address('1'),
            'fromBlock': '0x1',
            'toBlock': '0x2',
            'topics': [module.base.TRANSFER_TOPIC, topic('a')],
        }
        in_source = {
            'address': address('1'),
            'fromBlock': '0x1',
            'toBlock': '0x2',
            'topics': [module.base.TRANSFER_TOPIC, None, topic('a')],
        }
        self.assertEqual(module.group_filter_for_actors(out_source, 'OUT', [topic('b')])['topics'][1], topic('b'))
        self.assertEqual(
            module.group_filter_for_actors(out_source, 'OUT', [topic('b'), topic('a')])['topics'][1],
            [topic('a'), topic('b')],
        )
        self.assertEqual(module.group_filter_for_actors(in_source, 'IN', [topic('b')])['topics'][2], topic('b'))

    def test_actor_topic_split_precedes_block_split(self) -> None:
        calls: list[object] = []

        def call_once(value: dict[str, object]) -> list[dict[str, object]]:
            actor_filter = value['topics'][1]  # type: ignore[index]
            calls.append(actor_filter)
            if isinstance(actor_filter, list):
                raise module.base.Slice04HistoricalReverseScanError(
                    "RPC_RESPONSE_INVALID:{'code': -32005, 'message': 'limit exceeded'}"
                )
            actor_char = str(actor_filter)[-40]
            return [log(1, 0 if actor_char == 'a' else 1, actor_char)]

        value = {
            'address': address('1'),
            'fromBlock': '0x1',
            'toBlock': '0x1',
            'topics': [module.base.TRANSFER_TOPIC, topic('a')],
        }
        result, block_splits, actor_splits, learned_span, learned_group_size = module.adaptive_fetch_grouped(
            call_once,
            value,
            'OUT',
            [topic('a'), topic('c')],
        )
        self.assertEqual(block_splits, 0)
        self.assertEqual(actor_splits, 1)
        self.assertEqual(learned_span, 1)
        self.assertEqual(learned_group_size, 1)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(calls[0], list)

    def test_single_actor_range_splits_by_block(self) -> None:
        calls: list[tuple[int, int]] = []

        def call_once(value: dict[str, object]) -> list[dict[str, object]]:
            start, end = module.parse_filter_range(value)
            calls.append((start, end))
            if end - start + 1 > 4:
                raise module.base.Slice04HistoricalReverseScanError(
                    "RPC_RESPONSE_INVALID:{'code': -32005, 'message': 'limit exceeded'}"
                )
            return [log(start, 0)]

        value = {
            'address': address('1'),
            'fromBlock': '0x0',
            'toBlock': '0x7',
            'topics': [module.base.TRANSFER_TOPIC, topic('a')],
        }
        result, block_splits, actor_splits, learned_span, learned_group_size = module.adaptive_fetch_grouped(
            call_once,
            value,
            'OUT',
            [topic('a')],
        )
        self.assertEqual(block_splits, 1)
        self.assertEqual(actor_splits, 0)
        self.assertEqual(learned_span, 4)
        self.assertEqual(learned_group_size, 1)
        self.assertEqual(len(result), 2)
        self.assertEqual(calls, [(0, 7), (0, 3), (4, 7)])

    def test_preferred_actor_group_size_avoids_or_topic_query(self) -> None:
        calls: list[object] = []

        def call_once(value: dict[str, object]) -> list[dict[str, object]]:
            calls.append(value['topics'][1])  # type: ignore[index]
            return []

        value = {
            'address': address('1'),
            'fromBlock': '0x0',
            'toBlock': '0x1',
            'topics': [module.base.TRANSFER_TOPIC, topic('a')],
        }
        module.adaptive_fetch_grouped(
            call_once,
            value,
            'OUT',
            [topic('a'), topic('c')],
            preferred_actor_group_size=1,
        )
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(isinstance(item, str) for item in calls))

    def test_single_actor_single_block_limit_fails_closed(self) -> None:
        def call_once(_: dict[str, object]) -> list[dict[str, object]]:
            raise module.base.Slice04HistoricalReverseScanError(
                "RPC_RESPONSE_INVALID:{'code': -32005, 'message': 'limit exceeded'}"
            )

        value = {
            'address': address('1'),
            'fromBlock': '0x5',
            'toBlock': '0x5',
            'topics': [module.base.TRANSFER_TOPIC, topic('a')],
        }
        with self.assertRaisesRegex(
            module.base.Slice04HistoricalReverseScanError,
            'ETH_GET_LOGS_LIMIT_AT_SINGLE_ACTOR_SINGLE_BLOCK',
        ):
            module.adaptive_fetch_grouped(call_once, value, 'OUT', [topic('a')])

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
