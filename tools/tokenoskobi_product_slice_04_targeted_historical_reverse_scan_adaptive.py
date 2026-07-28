#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any, Callable

BASE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_HISTORICAL_REVERSE_SCAN_BASE_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_targeted_historical_reverse_scan.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_historical_reverse_scan_base', BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError('BASE_MODULE_IMPORT_FAILED')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

MAX_GROUPED_LOGS_PER_CHUNK = 2000


def is_limit_exceeded_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return (
        'limit exceeded' in text
        or "'code': -32005" in text
        or '"code": -32005' in text
        or 'code=-32005' in text
    )


def parse_filter_range(log_filter: dict[str, Any]) -> tuple[int, int]:
    try:
        start = int(str(log_filter['fromBlock']), 16)
        end = int(str(log_filter['toBlock']), 16)
    except (KeyError, TypeError, ValueError) as exc:
        raise base.Slice04HistoricalReverseScanError('ADAPTIVE_FILTER_RANGE_INVALID') from exc
    if start < 0 or end < start:
        raise base.Slice04HistoricalReverseScanError('ADAPTIVE_FILTER_RANGE_INVALID')
    return start, end


def with_range(log_filter: dict[str, Any], start: int, end: int) -> dict[str, Any]:
    if start < 0 or end < start:
        raise base.Slice04HistoricalReverseScanError('ADAPTIVE_SUBRANGE_INVALID')
    value = dict(log_filter)
    value['fromBlock'] = hex(start)
    value['toBlock'] = hex(end)
    return value


def log_key(log: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(log.get('transactionHash') or '').lower(),
        str(log.get('logIndex') or '').lower(),
        str(log.get('address') or '').lower(),
        str(log.get('blockHash') or '').lower(),
    )


def log_sort_key(log: dict[str, Any]) -> tuple[int, str, int, str]:
    try:
        block = int(str(log.get('blockNumber') or '0x0'), 16)
        index = int(str(log.get('logIndex') or '0x0'), 16)
    except ValueError as exc:
        raise base.Slice04HistoricalReverseScanError('ADAPTIVE_LOG_HEX_INVALID') from exc
    return (block, str(log.get('transactionHash') or '').lower(), index, str(log.get('address') or '').lower())


def dedupe_logs(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for log in logs:
        if not isinstance(log, dict):
            raise base.Slice04HistoricalReverseScanError('ADAPTIVE_LOG_NOT_OBJECT')
        unique.setdefault(log_key(log), log)
    return sorted(unique.values(), key=log_sort_key)


def adaptive_fetch(
    call_once: Callable[[dict[str, Any]], Any],
    log_filter: dict[str, Any],
    *,
    preferred_span: int | None = None,
    maximum_grouped_logs: int = MAX_GROUPED_LOGS_PER_CHUNK,
) -> tuple[list[dict[str, Any]], int, int | None]:
    start, end = parse_filter_range(log_filter)
    pending: list[tuple[int, int]] = []
    if preferred_span is not None and preferred_span > 0 and end - start + 1 > preferred_span:
        cursor = start
        while cursor <= end:
            sub_end = min(cursor + preferred_span - 1, end)
            pending.append((cursor, sub_end))
            cursor = sub_end + 1
    else:
        pending.append((start, end))

    output: list[dict[str, Any]] = []
    split_count = 0
    learned_span = preferred_span
    while pending:
        current_start, current_end = pending.pop(0)
        current_filter = with_range(log_filter, current_start, current_end)
        try:
            result = call_once(current_filter)
        except base.Slice04HistoricalReverseScanError as exc:
            if not is_limit_exceeded_error(exc):
                raise
            if current_start == current_end:
                raise base.Slice04HistoricalReverseScanError(
                    f'ETH_GET_LOGS_LIMIT_AT_SINGLE_ACTOR_SINGLE_BLOCK:{current_start}'
                ) from exc
            midpoint = (current_start + current_end) // 2
            pending.insert(0, (midpoint + 1, current_end))
            pending.insert(0, (current_start, midpoint))
            split_count += 1
            continue

        if not isinstance(result, list):
            raise base.Slice04HistoricalReverseScanError('ADAPTIVE_ETH_GET_LOGS_RESULT_NOT_LIST')
        if len(result) > maximum_grouped_logs:
            if current_start == current_end:
                raise base.Slice04HistoricalReverseScanError('ADAPTIVE_SINGLE_BLOCK_LOG_SCOPE_EXCEEDED')
            midpoint = (current_start + current_end) // 2
            pending.insert(0, (midpoint + 1, current_end))
            pending.insert(0, (current_start, midpoint))
            split_count += 1
            continue
        successful_span = current_end - current_start + 1
        learned_span = successful_span if learned_span is None else min(learned_span, successful_span)
        output.extend(result)
        if len(output) > maximum_grouped_logs:
            raise base.Slice04HistoricalReverseScanError('ADAPTIVE_GROUPED_LOG_SCOPE_EXCEEDED')

    return dedupe_logs(output), split_count, learned_span


def group_filter_for_actors(
    original_filter: dict[str, Any],
    direction: str,
    actor_topics: list[str],
) -> dict[str, Any]:
    normalized = sorted(set(str(item).lower() for item in actor_topics if str(item).strip()))
    if not normalized:
        raise base.Slice04HistoricalReverseScanError('ADAPTIVE_GROUP_ACTORS_EMPTY')
    topic_value: str | list[str] = normalized[0] if len(normalized) == 1 else normalized
    value = dict(original_filter)
    topics = list(value.get('topics') or [])
    if direction == 'OUT' and len(topics) == 2:
        topics[1] = topic_value
    elif direction == 'IN' and len(topics) == 3 and topics[1] is None:
        topics[2] = topic_value
    else:
        raise base.Slice04HistoricalReverseScanError('ADAPTIVE_GROUP_FILTER_INVALID')
    value['topics'] = topics
    return value


def partition_actor_topics(actor_topics: list[str], maximum_group_size: int | None) -> list[list[str]]:
    normalized = sorted(set(str(item).lower() for item in actor_topics if str(item).strip()))
    if not normalized:
        raise base.Slice04HistoricalReverseScanError('ADAPTIVE_GROUP_ACTORS_EMPTY')
    if maximum_group_size is None or maximum_group_size <= 0 or len(normalized) <= maximum_group_size:
        return [normalized]
    return [normalized[index:index + maximum_group_size] for index in range(0, len(normalized), maximum_group_size)]


def adaptive_fetch_grouped(
    call_once: Callable[[dict[str, Any]], Any],
    original_filter: dict[str, Any],
    direction: str,
    actor_topics: list[str],
    *,
    preferred_span: int | None = None,
    preferred_actor_group_size: int | None = None,
    maximum_grouped_logs: int = MAX_GROUPED_LOGS_PER_CHUNK,
) -> tuple[list[dict[str, Any]], int, int, int | None, int | None]:
    start, end = parse_filter_range(original_filter)
    block_ranges: list[tuple[int, int]] = []
    if preferred_span is not None and preferred_span > 0 and end - start + 1 > preferred_span:
        cursor = start
        while cursor <= end:
            sub_end = min(cursor + preferred_span - 1, end)
            block_ranges.append((cursor, sub_end))
            cursor = sub_end + 1
    else:
        block_ranges.append((start, end))

    topic_groups = partition_actor_topics(actor_topics, preferred_actor_group_size)
    pending: list[tuple[int, int, list[str]]] = [
        (range_start, range_end, list(group))
        for range_start, range_end in block_ranges
        for group in topic_groups
    ]
    output: list[dict[str, Any]] = []
    block_split_count = 0
    actor_split_count = 0
    learned_span = preferred_span
    learned_actor_group_size = preferred_actor_group_size

    while pending:
        current_start, current_end, current_topics = pending.pop(0)
        current_filter = group_filter_for_actors(
            with_range(original_filter, current_start, current_end),
            direction,
            current_topics,
        )
        try:
            result = call_once(current_filter)
        except base.Slice04HistoricalReverseScanError as exc:
            if not is_limit_exceeded_error(exc):
                raise
            if len(current_topics) > 1:
                midpoint = len(current_topics) // 2
                pending.insert(0, (current_start, current_end, current_topics[midpoint:]))
                pending.insert(0, (current_start, current_end, current_topics[:midpoint]))
                actor_split_count += 1
                continue
            if current_start < current_end:
                midpoint = (current_start + current_end) // 2
                pending.insert(0, (midpoint + 1, current_end, current_topics))
                pending.insert(0, (current_start, midpoint, current_topics))
                block_split_count += 1
                continue
            raise base.Slice04HistoricalReverseScanError(
                f'ETH_GET_LOGS_LIMIT_AT_SINGLE_ACTOR_SINGLE_BLOCK:{current_start}'
            ) from exc

        if not isinstance(result, list):
            raise base.Slice04HistoricalReverseScanError('ADAPTIVE_ETH_GET_LOGS_RESULT_NOT_LIST')
        if len(result) > maximum_grouped_logs:
            if len(current_topics) > 1:
                midpoint = len(current_topics) // 2
                pending.insert(0, (current_start, current_end, current_topics[midpoint:]))
                pending.insert(0, (current_start, current_end, current_topics[:midpoint]))
                actor_split_count += 1
                continue
            if current_start < current_end:
                midpoint = (current_start + current_end) // 2
                pending.insert(0, (midpoint + 1, current_end, current_topics))
                pending.insert(0, (current_start, midpoint, current_topics))
                block_split_count += 1
                continue
            raise base.Slice04HistoricalReverseScanError('ADAPTIVE_SINGLE_ACTOR_SINGLE_BLOCK_LOG_SCOPE_EXCEEDED')

        successful_span = current_end - current_start + 1
        successful_group_size = len(current_topics)
        learned_span = successful_span if learned_span is None else min(learned_span, successful_span)
        learned_actor_group_size = (
            successful_group_size
            if learned_actor_group_size is None
            else min(learned_actor_group_size, successful_group_size)
        )
        output.extend(result)
        if len(output) > maximum_grouped_logs:
            raise base.Slice04HistoricalReverseScanError('ADAPTIVE_GROUPED_LOG_SCOPE_EXCEEDED')

    return (
        dedupe_logs(output),
        block_split_count,
        actor_split_count,
        learned_span,
        learned_actor_group_size,
    )


def filter_logs_for_actor(logs: list[dict[str, Any]], direction: str, actor_topic: str) -> list[dict[str, Any]]:
    topic_index = 1 if direction == 'OUT' else 2 if direction == 'IN' else -1
    if topic_index < 0:
        raise base.Slice04HistoricalReverseScanError('ADAPTIVE_DIRECTION_INVALID')
    output: list[dict[str, Any]] = []
    for log in logs:
        topics = log.get('topics')
        if not isinstance(topics, list) or len(topics) <= topic_index:
            raise base.Slice04HistoricalReverseScanError('ADAPTIVE_LOG_TOPICS_INVALID')
        if str(topics[topic_index]).lower() == actor_topic.lower():
            output.append(log)
    return dedupe_logs(output)


OriginalRpcClient = base.RpcClient


class AdaptiveGroupedRpcClient(OriginalRpcClient):
    def __init__(self, provider: dict[str, Any]):
        super().__init__(provider)
        source_rows, receipt_rows, _ = base.load_database(base.DEFAULT_DB)
        anchors = base.select_anchors(base.build_eligible_records(source_rows, receipt_rows))
        groups: dict[tuple[str, str], list[str]] = {}
        for anchor in anchors:
            key = (base.normalize_address(anchor['token']), str(anchor['missing_direction']))
            groups.setdefault(key, []).append(base.topic_address(anchor['actor']))
        self.group_topics = {key: sorted(set(values)) for key, values in groups.items()}
        self.group_cache: dict[tuple[str, str, int, int], list[dict[str, Any]]] = {}
        self.actor_cache: dict[tuple[str, str, str, int, int], list[dict[str, Any]]] = {}
        self.preferred_span: int | None = None
        self.preferred_actor_group_size: int | None = None
        self.adaptive_block_split_count = 0
        self.adaptive_actor_split_count = 0

    def _raw_get_logs(self, log_filter: dict[str, Any]) -> Any:
        return super().call('eth_getLogs', [log_filter])

    def call(self, method: str, params: list[Any]) -> Any:
        if method != 'eth_getLogs':
            return super().call(method, params)
        if len(params) != 1 or not isinstance(params[0], dict):
            raise base.Slice04HistoricalReverseScanError('ADAPTIVE_ETH_GET_LOGS_PARAMS_INVALID')
        original_filter = dict(params[0])
        start, end = parse_filter_range(original_filter)
        token = base.normalize_address(original_filter.get('address'))
        topics = list(original_filter.get('topics') or [])
        if len(topics) == 2:
            direction = 'OUT'
            actor_topic = str(topics[1]).lower()
        elif len(topics) == 3 and topics[1] is None:
            direction = 'IN'
            actor_topic = str(topics[2]).lower()
        else:
            raise base.Slice04HistoricalReverseScanError('ADAPTIVE_ORIGINAL_FILTER_INVALID')

        actor_key = (token, direction, actor_topic, start, end)
        if actor_key in self.actor_cache:
            return list(self.actor_cache[actor_key])

        group_key = (token, direction, start, end)
        if group_key not in self.group_cache:
            actor_topics = self.group_topics.get((token, direction))
            if not actor_topics or actor_topic not in actor_topics:
                raise base.Slice04HistoricalReverseScanError('ADAPTIVE_ANCHOR_GROUP_MISSING')
            logs, block_splits, actor_splits, learned_span, learned_group_size = adaptive_fetch_grouped(
                self._raw_get_logs,
                original_filter,
                direction,
                actor_topics,
                preferred_span=self.preferred_span,
                preferred_actor_group_size=self.preferred_actor_group_size,
            )
            self.adaptive_block_split_count += block_splits
            self.adaptive_actor_split_count += actor_splits
            if learned_span is not None:
                self.preferred_span = learned_span if self.preferred_span is None else min(self.preferred_span, learned_span)
            if learned_group_size is not None:
                self.preferred_actor_group_size = (
                    learned_group_size
                    if self.preferred_actor_group_size is None
                    else min(self.preferred_actor_group_size, learned_group_size)
                )
            self.group_cache[group_key] = logs

        actor_logs = filter_logs_for_actor(self.group_cache[group_key], direction, actor_topic)
        if len(actor_logs) > base.MAX_LOGS_PER_QUERY:
            logs, splits, learned = adaptive_fetch(
                self._raw_get_logs,
                original_filter,
                preferred_span=self.preferred_span,
                maximum_grouped_logs=base.MAX_LOGS_PER_QUERY,
            )
            self.adaptive_block_split_count += splits
            if learned is not None:
                self.preferred_span = learned if self.preferred_span is None else min(self.preferred_span, learned)
            actor_logs = logs
        self.actor_cache[actor_key] = actor_logs
        return list(actor_logs)


base.RpcClient = AdaptiveGroupedRpcClient


def main() -> int:
    return base.main()


if __name__ == '__main__':
    raise SystemExit(main())
