#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_ROUTE = Path('/var/lib/tokenoskobi-product-slice-04/targeted_route_reselection_v1.json')
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/executor_route_classification_v1.json')
EXPECTED_ROUTE_HASH = 'abfc88e83fd87159baa0a2bbd41ee2ceaabd96d95e9377b44fce3e1a165955ad'
EXPECTED_ACTOR = '0x9999b0cdd35d7f3b281ba02efc0d228486940515'
ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')
MAX_TRANSACTIONS = 6
MAX_EVENTS = 18

AUTHORITY = {
    'network_access': False,
    'staging_file_write': True,
    'source_database_write': False,
    'production_database_write': False,
    'repository_write': False,
    'panel_mutation': False,
    'service_mutation': False,
    'timer_mutation': False,
    'paper_trade': False,
    'live_trade': False,
    'wallet': False,
    'signing': False,
    'order_create': False,
    'broadcast': False,
}


class Slice04ExecutorClassificationError(RuntimeError):
    pass


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def normalize_address(value: Any) -> str:
    text = str(value or '').strip().lower()
    if ADDRESS_RE.fullmatch(text) is None:
        raise Slice04ExecutorClassificationError('INVALID_ADDRESS')
    return text


def normalize_hash(value: Any) -> str:
    text = str(value or '').strip().lower()
    if HASH_RE.fullmatch(text) is None:
        raise Slice04ExecutorClassificationError('INVALID_HASH')
    return text


def read_json(path: Path, code: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise Slice04ExecutorClassificationError(f'{code}_MISSING')
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise Slice04ExecutorClassificationError(f'{code}_INVALID_JSON') from exc
    if not isinstance(payload, dict):
        raise Slice04ExecutorClassificationError(f'{code}_NOT_OBJECT')
    return payload


def validate_route_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get('schema') != 'tokenoskobi.product_slice_04.targeted_route_reselection.v1':
        raise Slice04ExecutorClassificationError('ROUTE_SCHEMA_INVALID')
    if payload.get('status') != 'TARGETED_MULTI_HOP_ROUTE_RESELECTION_COMPLETED':
        raise Slice04ExecutorClassificationError('ROUTE_STATUS_INVALID')
    if payload.get('result_hash') != EXPECTED_ROUTE_HASH:
        raise Slice04ExecutorClassificationError('ROUTE_HASH_INVALID')
    if payload.get('chain') != 'BSC' or payload.get('chain_id') != 56:
        raise Slice04ExecutorClassificationError('ROUTE_CHAIN_INVALID')
    summary = payload.get('summary')
    if not isinstance(summary, dict):
        raise Slice04ExecutorClassificationError('ROUTE_SUMMARY_INVALID')
    expected_summary = {
        'target_transaction_count': 6,
        'recognized_swap_event_count': 18,
        'protocol_verified_swap_event_count': 18,
        'route_verified_transaction_count': 0,
        'reversed_route_candidate_count': 0,
        'full_position_closed_loop_count': 0,
        'self_call_transaction_count': 6,
        'closed_loop_confirmed': False,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise Slice04ExecutorClassificationError(f'ROUTE_SUMMARY_DRIFT:{key}')
    transactions = payload.get('transactions')
    if not isinstance(transactions, list) or len(transactions) != MAX_TRANSACTIONS:
        raise Slice04ExecutorClassificationError('ROUTE_TRANSACTION_SCOPE_INVALID')
    total_events = 0
    seen_hashes: set[str] = set()
    for tx in transactions:
        if not isinstance(tx, dict):
            raise Slice04ExecutorClassificationError('ROUTE_TRANSACTION_INVALID')
        tx_hash = normalize_hash(tx.get('tx_hash'))
        if tx_hash in seen_hashes:
            raise Slice04ExecutorClassificationError('ROUTE_TRANSACTION_DUPLICATE')
        seen_hashes.add(tx_hash)
        actor = normalize_address(tx.get('actor'))
        target = normalize_address(tx.get('transaction_target'))
        if actor != EXPECTED_ACTOR or target != actor or tx.get('self_call') is not True:
            raise Slice04ExecutorClassificationError('SELF_CALL_SCOPE_DRIFT')
        events = tx.get('events')
        if not isinstance(events, list):
            raise Slice04ExecutorClassificationError('ROUTE_EVENTS_INVALID')
        if len(events) != int(tx.get('recognized_swap_event_count', -1)):
            raise Slice04ExecutorClassificationError('ROUTE_EVENT_COUNT_MISMATCH')
        if int(tx.get('protocol_verified_swap_event_count', -1)) != len(events):
            raise Slice04ExecutorClassificationError('ROUTE_VERIFIED_EVENT_COUNT_MISMATCH')
        for event in events:
            if not isinstance(event, dict) or event.get('protocol_verified') is not True:
                raise Slice04ExecutorClassificationError('UNVERIFIED_EVENT_IN_SCOPE')
        total_events += len(events)
    if total_events != MAX_EVENTS:
        raise Slice04ExecutorClassificationError('ROUTE_TOTAL_EVENT_SCOPE_INVALID')
    return transactions


def event_edge(event: dict[str, Any]) -> dict[str, Any]:
    source = normalize_address(event.get('input_token'))
    target = normalize_address(event.get('output_token'))
    input_raw = int(str(event.get('input_raw')))
    output_raw = int(str(event.get('output_raw')))
    if source == target or input_raw <= 0 or output_raw <= 0:
        raise Slice04ExecutorClassificationError('EVENT_EDGE_INVALID')
    return {
        'source_token': source,
        'target_token': target,
        'input_raw': str(input_raw),
        'output_raw': str(output_raw),
        'protocol_id': str(event.get('protocol_id') or ''),
        'pool_address': normalize_address(event.get('pool_address')),
        'receipt_log_index': int(event.get('receipt_log_index')),
    }


def weak_component_count(edges: list[dict[str, Any]]) -> int:
    undirected: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        source = edge['source_token']
        target = edge['target_token']
        undirected[source].add(target)
        undirected[target].add(source)
    seen: set[str] = set()
    count = 0
    for node in sorted(undirected):
        if node in seen:
            continue
        count += 1
        stack = [node]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(sorted(undirected[current] - seen))
    return count


def has_directed_cycle(edges: list[dict[str, Any]]) -> bool:
    adjacency: dict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    for edge in edges:
        source = edge['source_token']
        target = edge['target_token']
        adjacency[source].add(target)
        nodes.update((source, target))
    state: dict[str, int] = {node: 0 for node in nodes}

    def visit(node: str) -> bool:
        state[node] = 1
        for child in adjacency.get(node, set()):
            if state[child] == 1:
                return True
            if state[child] == 0 and visit(child):
                return True
        state[node] = 2
        return False

    return any(state[node] == 0 and visit(node) for node in sorted(nodes))


def classify_transaction(tx: dict[str, Any]) -> dict[str, Any]:
    route = tx.get('route')
    if not isinstance(route, dict):
        raise Slice04ExecutorClassificationError('TRANSACTION_ROUTE_INVALID')
    events = sorted((event_edge(item) for item in tx['events']), key=lambda row: row['receipt_log_index'])
    actor_net = {normalize_address(token): int(str(amount)) for token, amount in (route.get('actor_net_by_token') or {}).items()}
    swap_net = {normalize_address(token): int(str(amount)) for token, amount in (route.get('swap_net_by_token') or {}).items()}
    actor_out = sorted(token for token, amount in actor_net.items() if amount < 0)
    actor_in = sorted(token for token, amount in actor_net.items() if amount > 0)
    exact_token_set = bool(actor_net) and set(actor_net) == set(swap_net)
    exact_raw_amounts = exact_token_set and all(actor_net[token] == swap_net[token] for token in actor_net)
    single_endpoint_pair = len(actor_out) == 1 and len(actor_in) == 1
    cycle_present = has_directed_cycle(events)
    component_count = weak_component_count(edges)
    if single_endpoint_pair and exact_raw_amounts:
        classification = 'SELF_CALL_SIMPLE_TWO_TOKEN_ROUTE_VERIFIED'
    elif exact_raw_amounts and cycle_present:
        classification = 'SELF_CALL_MULTI_ASSET_CYCLIC_EXECUTION_VERIFIED'
    elif exact_raw_amounts:
        classification = 'SELF_CALL_MULTI_ASSET_EXECUTION_VERIFIED'
    else:
        classification = 'SELF_CALL_EXECUTION_WITH_UNEXPLAINED_TRANSFER_RESIDUALS'
    simple_wallet_position_admissible = bool(single_endpoint_pair and exact_raw_amounts)
    return {
        'tx_hash': normalize_hash(tx.get('tx_hash')),
        'block_number': int(tx.get('block_number')),
        'transaction_index': int(tx.get('transaction_index')),
        'actor': normalize_address(tx.get('actor')),
        'transaction_target': normalize_address(tx.get('transaction_target')),
        'selector': str(tx.get('selector') or ''),
        'self_call': bool(tx.get('self_call')),
        'event_count': len(events),
        'protocol_ids': sorted({edge['protocol_id'] for edge in events}),
        'pool_addresses': sorted({edge['pool_address'] for edge in events}),
        'token_nodes': sorted({edge['source_token'] for edge in events} | {edge['target_token'] for edge in events}),
        'edges': events,
        'weak_component_count': component_count,
        'directed_cycle_present': cycle_present,
        'actor_net_by_token': {token: str(amount) for token, amount in sorted(actor_net.items())},
        'swap_net_by_token': {token: str(amount) for token, amount in sorted(swap_net.items())},
        'actor_out_tokens': actor_out,
        'actor_in_tokens': actor_in,
        'single_endpoint_pair': single_endpoint_pair,
        'exact_token_set': exact_token_set,
        'exact_raw_amounts': exact_raw_amounts,
        'classification': classification,
        'simple_wallet_position_admissible': simple_wallet_position_admissible,
        'closed_loop_admissible': False,
        'classification_hash': canonical_hash({
            'tx_hash': tx.get('tx_hash'),
            'actor_net': actor_net,
            'swap_net': swap_net,
            'edges': events,
            'classification': classification,
        }),
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    os.chmod(temp, 0o600)
    json.loads(temp.read_text(encoding='utf-8'))
    temp.replace(path)
    os.chmod(path, 0o600)


def run(route_path: Path, output_path: Path) -> dict[str, Any]:
    source = read_json(route_path, 'TARGETED_ROUTE')
    transactions = validate_route_payload(source)
    classified = [classify_transaction(tx) for tx in transactions]
    classified.sort(key=lambda row: (row['block_number'], row['transaction_index'], row['tx_hash']))
    simple_count = sum(int(row['simple_wallet_position_admissible']) for row in classified)
    exact_multi_count = sum(int(row['exact_raw_amounts'] and not row['single_endpoint_pair']) for row in classified)
    cyclic_exact_count = sum(int(row['classification'] == 'SELF_CALL_MULTI_ASSET_CYCLIC_EXECUTION_VERIFIED') for row in classified)
    residual_count = sum(int(row['classification'] == 'SELF_CALL_EXECUTION_WITH_UNEXPLAINED_TRANSFER_RESIDUALS') for row in classified)
    next_step = (
        'BUILD_SIMPLE_WALLET_CLOSED_LOOP_FROM_ADMISSIBLE_ROUTES'
        if simple_count
        else 'SELECT_NON_SELF_CALL_SINGLE_ENDPOINT_PAIR_CANDIDATES_FROM_FULL_DATASET'
    )
    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.executor_route_classification.v1',
        'generated_at_utc': iso_now(),
        'status': 'SELF_CALL_EXECUTOR_ROUTE_BLOCKERS_CLASSIFIED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {
            'targeted_route_path': str(route_path),
            'targeted_route_result_hash': EXPECTED_ROUTE_HASH,
        },
        'policy': {
            'classification_is_transaction_evidence_only': True,
            'protocol_intent_is_not_inferred': True,
            'ownership_or_control_is_not_inferred': True,
            'multi_asset_execution_is_not_treated_as_simple_wallet_position': True,
            'unexplained_transfer_residuals_fail_closed': True,
            'closed_loop_requires_separate_admissible_open_and_close_routes': True,
        },
        'transactions': classified,
        'summary': {
            'transaction_count': len(classified),
            'self_call_transaction_count': sum(int(row['self_call']) for row in classified),
            'simple_wallet_position_route_count': simple_count,
            'exact_multi_asset_execution_count': exact_multi_count,
            'exact_cyclic_execution_count': cyclic_exact_count,
            'unexplained_residual_transaction_count': residual_count,
            'closed_loop_confirmed': False,
            'dataset_admissible_for_simple_wallet_position_model': bool(simple_count),
            'dataset_classification': (
                'MIXED_WITH_SIMPLE_WALLET_POSITION_ROUTE'
                if simple_count
                else 'SELF_CALL_EXECUTOR_SCOPE_NOT_ADMISSIBLE_AS_SIMPLE_WALLET_POSITION_SAMPLE'
            ),
            'next_safe_step': next_step,
        },
    }
    payload['result_hash'] = canonical_hash(payload)
    atomic_write_json(output_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--route', type=Path, default=DEFAULT_ROUTE)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.route, args.output)
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'TRANSACTION_COUNT={summary["transaction_count"]}')
    print(f'SELF_CALL_TRANSACTION_COUNT={summary["self_call_transaction_count"]}')
    print(f'SIMPLE_WALLET_POSITION_ROUTE_COUNT={summary["simple_wallet_position_route_count"]}')
    print(f'EXACT_MULTI_ASSET_EXECUTION_COUNT={summary["exact_multi_asset_execution_count"]}')
    print(f'EXACT_CYCLIC_EXECUTION_COUNT={summary["exact_cyclic_execution_count"]}')
    print(f'UNEXPLAINED_RESIDUAL_TRANSACTION_COUNT={summary["unexplained_residual_transaction_count"]}')
    for index, tx in enumerate(result['transactions'], start=1):
        print(
            f'EXECUTOR_TX_{index}=tx:{tx["tx_hash"]},block:{tx["block_number"]},events:{tx["event_count"]},'
            f'nodes:{len(tx["token_nodes"])},components:{tx["weak_component_count"]},cycle:{str(tx["directed_cycle_present"]).lower()},'
            f'out_count:{len(tx["actor_out_tokens"])},in_count:{len(tx["actor_in_tokens"])},'
            f'exact_tokens:{str(tx["exact_token_set"]).lower()},exact_amounts:{str(tx["exact_raw_amounts"]).lower()},'
            f'class:{tx["classification"]}'
        )
        print('ACTOR_NET_' + str(index) + '=' + json.dumps(tx['actor_net_by_token'], sort_keys=True, separators=(',', ':')))
        print('SWAP_NET_' + str(index) + '=' + json.dumps(tx['swap_net_by_token'], sort_keys=True, separators=(',', ':')))
    print(f'DATASET_CLASSIFICATION={summary["dataset_classification"]}')
    print(f'RESULT_HASH={result["result_hash"]}')
    print('CLOSED_LOOP_CONFIRMED=false')
    print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
