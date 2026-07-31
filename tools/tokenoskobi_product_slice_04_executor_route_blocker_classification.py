#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
DEFAULT_DB = ROOT / 'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
DEFAULT_ROUTE = Path('/var/lib/tokenoskobi-product-slice-04/targeted_route_reselection_v1.json')
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/executor_route_blocker_classification_v1.json')
RECEIPT_TABLE = 'era64j_historical_receipt_cost_enrichment_v1'
EXPECTED_DB_HASH = '99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_ROUTE_HASH = 'abfc88e83fd87159baa0a2bbd41ee2ceaabd96d95e9377b44fce3e1a165955ad'
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')
MAX_TRANSACTIONS = 6
MAX_TRANSFER_EDGES = 500

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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


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


def read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise Slice04ExecutorClassificationError(f'{label}_MISSING')
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError) as exc:
        raise Slice04ExecutorClassificationError(f'{label}_INVALID_JSON') from exc
    if not isinstance(payload, dict):
        raise Slice04ExecutorClassificationError(f'{label}_NOT_OBJECT')
    return payload


def validate_route(path: Path) -> dict[str, Any]:
    payload = read_json(path, 'TARGETED_ROUTE')
    if payload.get('schema') != 'tokenoskobi.product_slice_04.targeted_route_reselection.v1':
        raise Slice04ExecutorClassificationError('TARGETED_ROUTE_SCHEMA_INVALID')
    if payload.get('status') != 'TARGETED_MULTI_HOP_ROUTE_RESELECTION_COMPLETED':
        raise Slice04ExecutorClassificationError('TARGETED_ROUTE_STATUS_INVALID')
    if payload.get('result_hash') != EXPECTED_ROUTE_HASH:
        raise Slice04ExecutorClassificationError('TARGETED_ROUTE_HASH_INVALID')
    summary = payload.get('summary')
    transactions = payload.get('transactions')
    if not isinstance(summary, dict) or not isinstance(transactions, list):
        raise Slice04ExecutorClassificationError('TARGETED_ROUTE_SHAPE_INVALID')
    if len(transactions) != MAX_TRANSACTIONS:
        raise Slice04ExecutorClassificationError('TARGETED_ROUTE_TRANSACTION_SCOPE_INVALID')
    if int(summary.get('recognized_swap_event_count', -1)) != 18:
        raise Slice04ExecutorClassificationError('TARGETED_ROUTE_SWAP_COUNT_INVALID')
    if int(summary.get('protocol_verified_swap_event_count', -1)) != 18:
        raise Slice04ExecutorClassificationError('TARGETED_ROUTE_VERIFIED_SWAP_COUNT_INVALID')
    if int(summary.get('self_call_transaction_count', -1)) != MAX_TRANSACTIONS:
        raise Slice04ExecutorClassificationError('TARGETED_ROUTE_SELF_CALL_SCOPE_INVALID')
    if bool(summary.get('closed_loop_confirmed')):
        raise Slice04ExecutorClassificationError('TARGETED_ROUTE_ALREADY_CLOSED')
    actors = {normalize_address(item.get('actor')) for item in transactions}
    selectors = {str(item.get('selector') or '') for item in transactions}
    if actors != {'0x9999b0cdd35d7f3b281ba02efc0d228486940515'}:
        raise Slice04ExecutorClassificationError('TARGET_ACTOR_DRIFT')
    if selectors != {'0xd4d6ab16'}:
        raise Slice04ExecutorClassificationError('TARGET_SELECTOR_DRIFT')
    return payload


def load_receipt_logs(database_path: Path, tx_hashes: list[str]) -> dict[str, list[dict[str, Any]]]:
    resolved = database_path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file() or file_sha256(resolved) != EXPECTED_DB_HASH:
        raise Slice04ExecutorClassificationError('SOURCE_DATABASE_INVALID')
    if len(tx_hashes) != MAX_TRANSACTIONS or len(set(tx_hashes)) != MAX_TRANSACTIONS:
        raise Slice04ExecutorClassificationError('TARGET_HASH_SCOPE_INVALID')
    uri = f'file:{resolved}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04ExecutorClassificationError('SOURCE_DATABASE_INTEGRITY_FAILED')
        placeholders = ','.join('?' for _ in tx_hashes)
        rows = [dict(row) for row in conn.execute(
            f'''SELECT tx_hash,raw_receipt_json FROM {RECEIPT_TABLE}
                WHERE tx_hash IN ({placeholders})''',
            tx_hashes,
        )]
    finally:
        conn.close()
    result: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        tx_hash = normalize_hash(row.get('tx_hash'))
        try:
            receipt = json.loads(str(row.get('raw_receipt_json') or ''))
        except json.JSONDecodeError as exc:
            raise Slice04ExecutorClassificationError('RECEIPT_JSON_INVALID') from exc
        logs = receipt.get('logs') if isinstance(receipt, dict) else None
        if not isinstance(logs, list):
            raise Slice04ExecutorClassificationError('RECEIPT_LOGS_INVALID')
        result[tx_hash] = [item for item in logs if isinstance(item, dict)]
    if set(result) != set(tx_hashes):
        raise Slice04ExecutorClassificationError('RECEIPT_COVERAGE_INVALID')
    return result


def decode_transfer(log: dict[str, Any]) -> dict[str, Any] | None:
    topics = log.get('topics')
    if not isinstance(topics, list) or not topics:
        return None
    if normalize_hash(topics[0]) != TRANSFER_TOPIC:
        return None
    if len(topics) == 4:
        return None
    if len(topics) != 3:
        raise Slice04ExecutorClassificationError('TRANSFER_TOPIC_COUNT_INVALID')
    data = str(log.get('data') or '').strip().lower()
    if not re.fullmatch(r'0x[0-9a-f]{64}', data):
        raise Slice04ExecutorClassificationError('TRANSFER_DATA_INVALID')
    return {
        'token_address': normalize_address(log.get('address')),
        'from_address': normalize_address('0x' + normalize_hash(topics[1])[-40:]),
        'to_address': normalize_address('0x' + normalize_hash(topics[2])[-40:]),
        'amount_raw': int(data[2:], 16),
    }


def actor_transfer_edges(logs: list[dict[str, Any]], actor: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for position, log in enumerate(logs):
        transfer = decode_transfer(log)
        if transfer is None:
            continue
        src = transfer['from_address']
        dst = transfer['to_address']
        if src != actor and dst != actor:
            continue
        direction = 'OUT' if src == actor and dst != actor else 'IN' if dst == actor and src != actor else 'SELF'
        counterparty = dst if direction == 'OUT' else src if direction == 'IN' else actor
        rows.append({
            'receipt_log_position': position,
            'token_address': transfer['token_address'],
            'direction': direction,
            'counterparty': counterparty,
            'amount_raw': str(transfer['amount_raw']),
        })
        if len(rows) > MAX_TRANSFER_EDGES:
            raise Slice04ExecutorClassificationError('TRANSFER_EDGE_SCOPE_EXCEEDED')
    return rows


def connected_components(events: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for event in events:
        a = normalize_address(event.get('input_token'))
        b = normalize_address(event.get('output_token'))
        adjacency[a].add(b)
        adjacency[b].add(a)
    visited: set[str] = set()
    token_components: list[set[str]] = []
    for token in sorted(adjacency):
        if token in visited:
            continue
        stack = [token]
        component: set[str] = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.add(current)
            stack.extend(sorted(adjacency[current] - visited))
        token_components.append(component)
    rows: list[list[dict[str, Any]]] = []
    for tokens in token_components:
        rows.append([event for event in events if normalize_address(event.get('input_token')) in tokens])
    return rows


def component_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    net: dict[str, int] = defaultdict(int)
    pools: set[str] = set()
    protocols: set[str] = set()
    for event in events:
        input_token = normalize_address(event.get('input_token'))
        output_token = normalize_address(event.get('output_token'))
        input_raw = int(str(event.get('input_raw')))
        output_raw = int(str(event.get('output_raw')))
        if input_raw <= 0 or output_raw <= 0:
            raise Slice04ExecutorClassificationError('SWAP_AMOUNT_INVALID')
        net[input_token] -= input_raw
        net[output_token] += output_raw
        pools.add(normalize_address(event.get('pool_address')))
        protocols.add(str(event.get('protocol_id') or 'UNVERIFIED'))
    net = {token: amount for token, amount in net.items() if amount != 0}
    out_tokens = sorted(token for token, amount in net.items() if amount < 0)
    in_tokens = sorted(token for token, amount in net.items() if amount > 0)
    if not net:
        classification = 'ZERO_NET_SWAP_CYCLE_COMPONENT'
    elif len(out_tokens) == 1 and len(in_tokens) == 1:
        classification = 'TWO_ENDPOINT_ROUTE_COMPONENT'
    else:
        classification = 'MULTI_ENDPOINT_ROUTE_COMPONENT'
    return {
        'classification': classification,
        'event_count': len(events),
        'protocol_ids': sorted(protocols),
        'pool_addresses': sorted(pools),
        'net_by_token': {token: str(amount) for token, amount in sorted(net.items())},
        'out_tokens': out_tokens,
        'in_tokens': in_tokens,
        'input_token': out_tokens[0] if len(out_tokens) == 1 and len(in_tokens) == 1 else '',
        'output_token': in_tokens[0] if len(out_tokens) == 1 and len(in_tokens) == 1 else '',
        'input_raw': str(abs(net[out_tokens[0]])) if len(out_tokens) == 1 and len(in_tokens) == 1 else '',
        'output_raw': str(net[in_tokens[0]]) if len(out_tokens) == 1 and len(in_tokens) == 1 else '',
    }


def transaction_classification(record: dict[str, Any], logs: list[dict[str, Any]]) -> dict[str, Any]:
    route = record.get('route')
    events = record.get('events')
    if not isinstance(route, dict) or not isinstance(events, list):
        raise Slice04ExecutorClassificationError('TRANSACTION_ROUTE_SHAPE_INVALID')
    verified_events = [item for item in events if isinstance(item, dict) and bool(item.get('protocol_verified'))]
    components = [component_summary(rows) for rows in connected_components(verified_events)]
    actor = normalize_address(record.get('actor'))
    edges = actor_transfer_edges(logs, actor)
    actor_net = {normalize_address(token): int(str(amount)) for token, amount in (route.get('actor_net_by_token') or {}).items()}
    out_count = sum(1 for amount in actor_net.values() if amount < 0)
    in_count = sum(1 for amount in actor_net.values() if amount > 0)
    exact = bool(route.get('exact_token_set')) and bool(route.get('exact_raw_amounts'))
    if bool(record.get('self_call')) and exact and (out_count > 1 or in_count > 1):
        behavior = 'SELF_CALL_MULTI_ASSET_EXECUTOR_EXACT_SETTLEMENT'
    elif bool(record.get('self_call')) and not exact:
        behavior = 'SELF_CALL_EXECUTOR_WITH_UNEXPLAINED_SETTLEMENT'
    elif out_count == 1 and in_count == 1 and exact:
        behavior = 'SINGLE_POSITION_ROUTE'
    else:
        behavior = 'UNCLASSIFIED_ROUTE_BEHAVIOR'
    return {
        'tx_hash': normalize_hash(record.get('tx_hash')),
        'block_number': int(record.get('block_number')),
        'transaction_index': int(record.get('transaction_index')),
        'actor': actor,
        'selector': str(record.get('selector')),
        'self_call': bool(record.get('self_call')),
        'behavior_class': behavior,
        'actor_out_token_count': out_count,
        'actor_in_token_count': in_count,
        'actor_net_by_token': {token: str(amount) for token, amount in sorted(actor_net.items())},
        'swap_net_by_token': dict(route.get('swap_net_by_token') or {}),
        'exact_token_set': bool(route.get('exact_token_set')),
        'exact_raw_amounts': bool(route.get('exact_raw_amounts')),
        'route_blockers': list(route.get('blockers') or []),
        'actor_transfer_edge_count': len(edges),
        'actor_counterparties': sorted({item['counterparty'] for item in edges}),
        'actor_transfer_edges': edges,
        'component_count': len(components),
        'two_endpoint_component_count': sum(int(item['classification'] == 'TWO_ENDPOINT_ROUTE_COMPONENT') for item in components),
        'zero_net_cycle_component_count': sum(int(item['classification'] == 'ZERO_NET_SWAP_CYCLE_COMPONENT') for item in components),
        'multi_endpoint_component_count': sum(int(item['classification'] == 'MULTI_ENDPOINT_ROUTE_COMPONENT') for item in components),
        'components': components,
    }


def build_component_reverse_candidates(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []
    for tx in transactions:
        actor_net = {token: int(amount) for token, amount in tx['actor_net_by_token'].items()}
        for index, component in enumerate(tx['components'], start=1):
            if component['classification'] != 'TWO_ENDPOINT_ROUTE_COMPONENT':
                continue
            input_token = component['input_token']
            output_token = component['output_token']
            input_raw = component['input_raw']
            output_raw = component['output_raw']
            actor_attribution = (
                set(actor_net) == {input_token, output_token}
                and actor_net[input_token] == -int(input_raw)
                and actor_net[output_token] == int(output_raw)
            )
            endpoints.append({
                'tx_hash': tx['tx_hash'],
                'block_number': tx['block_number'],
                'transaction_index': tx['transaction_index'],
                'component_index': index,
                'input_token': input_token,
                'output_token': output_token,
                'input_raw': input_raw,
                'output_raw': output_raw,
                'actor_attribution_verified': actor_attribution,
            })
    endpoints.sort(key=lambda row: (row['block_number'], row['transaction_index'], row['tx_hash'], row['component_index']))
    candidates: list[dict[str, Any]] = []
    for index, opening in enumerate(endpoints):
        for closing in endpoints[index + 1:]:
            if opening['tx_hash'] == closing['tx_hash']:
                continue
            if opening['input_token'] != closing['output_token'] or opening['output_token'] != closing['input_token']:
                continue
            position_exact = opening['output_raw'] == closing['input_raw']
            attributed = bool(opening['actor_attribution_verified'] and closing['actor_attribution_verified'])
            candidates.append({
                'opening_tx_hash': opening['tx_hash'],
                'closing_tx_hash': closing['tx_hash'],
                'opening_component_index': opening['component_index'],
                'closing_component_index': closing['component_index'],
                'base_token': opening['input_token'],
                'position_token': opening['output_token'],
                'position_acquired_raw': opening['output_raw'],
                'position_sold_raw': closing['input_raw'],
                'position_amount_exact': position_exact,
                'actor_settlement_attribution_verified': attributed,
                'closed_loop_confirmed': bool(position_exact and attributed),
                'blockers': ([] if position_exact else ['POSITION_AMOUNT_NOT_EXACT']) + ([] if attributed else ['ACTOR_SETTLEMENT_ATTRIBUTION_UNVERIFIED']),
            })
    return candidates


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    os.chmod(temp, 0o600)
    json.loads(temp.read_text(encoding='utf-8'))
    temp.replace(path)
    os.chmod(path, 0o600)


def run(database_path: Path, route_path: Path, output_path: Path) -> dict[str, Any]:
    route_payload = validate_route(route_path)
    records = route_payload['transactions']
    tx_hashes = [normalize_hash(item.get('tx_hash')) for item in records]
    receipt_logs = load_receipt_logs(database_path, tx_hashes)
    transactions = [transaction_classification(item, receipt_logs[normalize_hash(item.get('tx_hash'))]) for item in records]
    transactions.sort(key=lambda row: (row['block_number'], row['transaction_index'], row['tx_hash']))
    candidates = build_component_reverse_candidates(transactions)
    confirmed = [item for item in candidates if item['closed_loop_confirmed']]
    exact_multi_asset = sum(int(item['behavior_class'] == 'SELF_CALL_MULTI_ASSET_EXECUTOR_EXACT_SETTLEMENT') for item in transactions)
    unexplained = sum(int(item['behavior_class'] == 'SELF_CALL_EXECUTOR_WITH_UNEXPLAINED_SETTLEMENT') for item in transactions)
    component_candidates = len(candidates)
    attributed_candidates = sum(int(item['actor_settlement_attribution_verified']) for item in candidates)
    if confirmed:
        next_step = 'EXECUTION_PRICE_GAS_FEE_AND_PERFORMANCE_RECONSTRUCTION'
    elif component_candidates:
        next_step = 'COMPONENT_TO_ACTOR_SETTLEMENT_ATTRIBUTION_OR_EXECUTOR_EXCLUSION'
    else:
        next_step = 'EXCLUDE_SELF_CALL_EXECUTOR_AND_SELECT_NON_SELF_CALL_WALLET_CANDIDATES'
    actor_behavior = (
        'SELF_CALL_MULTI_ROUTE_EXECUTION_ACCOUNT_BEHAVIOR'
        if all(item['self_call'] for item in transactions)
        else 'MIXED_ACCOUNT_BEHAVIOR'
    )
    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.executor_route_blocker_classification.v1',
        'generated_at_utc': iso_now(),
        'status': 'EXECUTOR_ROUTE_BLOCKERS_CLASSIFIED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {
            'database_path': str(database_path.resolve()),
            'database_sha256': file_sha256(database_path),
            'targeted_route_path': str(route_path),
            'targeted_route_result_hash': route_payload['result_hash'],
        },
        'policy': {
            'identity_or_ownership_inference_allowed': False,
            'self_call_behavior_is_not_wallet_ownership_proof': True,
            'component_closed_loop_requires_actor_settlement_attribution': True,
            'position_raw_amount_must_reverse_exactly': True,
            'unexplained_settlement_fails_closed': True,
        },
        'actor': transactions[0]['actor'],
        'actor_behavior_class': actor_behavior,
        'transactions': transactions,
        'component_reverse_candidates': candidates,
        'summary': {
            'target_transaction_count': len(transactions),
            'self_call_transaction_count': sum(int(item['self_call']) for item in transactions),
            'exact_multi_asset_executor_transaction_count': exact_multi_asset,
            'unexplained_settlement_transaction_count': unexplained,
            'total_component_count': sum(item['component_count'] for item in transactions),
            'two_endpoint_component_count': sum(item['two_endpoint_component_count'] for item in transactions),
            'zero_net_cycle_component_count': sum(item['zero_net_cycle_component_count'] for item in transactions),
            'multi_endpoint_component_count': sum(item['multi_endpoint_component_count'] for item in transactions),
            'component_reverse_candidate_count': component_candidates,
            'actor_attributed_component_reverse_candidate_count': attributed_candidates,
            'confirmed_component_closed_loop_count': len(confirmed),
            'closed_loop_confirmed': bool(confirmed),
            'next_safe_step': next_step,
        },
    }
    payload['result_hash'] = canonical_hash(payload)
    atomic_write_json(output_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=DEFAULT_DB)
    parser.add_argument('--route', type=Path, default=DEFAULT_ROUTE)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.database, args.route, args.output)
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'ACTOR={result["actor"]}')
    print(f'ACTOR_BEHAVIOR_CLASS={result["actor_behavior_class"]}')
    for key in (
        'target_transaction_count', 'self_call_transaction_count',
        'exact_multi_asset_executor_transaction_count', 'unexplained_settlement_transaction_count',
        'total_component_count', 'two_endpoint_component_count', 'zero_net_cycle_component_count',
        'multi_endpoint_component_count', 'component_reverse_candidate_count',
        'actor_attributed_component_reverse_candidate_count', 'confirmed_component_closed_loop_count',
    ):
        print(f'{key.upper()}={summary[key]}')
    for index, tx in enumerate(result['transactions'], start=1):
        print(
            f'EXECUTOR_TX_{index}=tx:{tx["tx_hash"]},behavior:{tx["behavior_class"]},'
            f'actor_out:{tx["actor_out_token_count"]},actor_in:{tx["actor_in_token_count"]},'
            f'components:{tx["component_count"]},two_endpoint:{tx["two_endpoint_component_count"]},'
            f'zero_cycle:{tx["zero_net_cycle_component_count"]},multi_endpoint:{tx["multi_endpoint_component_count"]},'
            f'counterparties:{len(tx["actor_counterparties"])}'
        )
        for component_index, component in enumerate(tx['components'], start=1):
            print(
                f'COMPONENT_{index}_{component_index}=class:{component["classification"]},events:{component["event_count"]},'
                f'input:{component["input_token"] or "NONE"},output:{component["output_token"] or "NONE"},'
                f'input_raw:{component["input_raw"] or "NONE"},output_raw:{component["output_raw"] or "NONE"}'
            )
    for index, candidate in enumerate(result['component_reverse_candidates'], start=1):
        print(
            f'COMPONENT_REVERSE_{index}=open:{candidate["opening_tx_hash"]},close:{candidate["closing_tx_hash"]},'
            f'base:{candidate["base_token"]},position:{candidate["position_token"]},'
            f'position_exact:{str(candidate["position_amount_exact"]).lower()},'
            f'actor_attributed:{str(candidate["actor_settlement_attribution_verified"]).lower()},'
            f'confirmed:{str(candidate["closed_loop_confirmed"]).lower()}'
        )
    print(f'RESULT_HASH={result["result_hash"]}')
    print(f'CLOSED_LOOP_CONFIRMED={str(summary["closed_loop_confirmed"]).lower()}')
    print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
