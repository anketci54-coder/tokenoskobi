#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import time
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
DEFAULT_DB = ROOT / 'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
DEFAULT_PROVIDER = ROOT / 'config/era63e_always_on_market_runtime_v1.json'
DEFAULT_ENRICHMENT = Path('/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json')
DEFAULT_TARGETED = Path('/var/lib/tokenoskobi-product-slice-04/targeted_actor_history_enrichment_v1.json')
DEFAULT_ALLOWLIST = ROOT / 'config/product_slice_04_factory_allowlist_v1.json'
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/targeted_swap_route_graph_v1.json')
RECEIPT_TABLE = 'era64j_historical_receipt_cost_enrichment_v1'
EXPECTED_DB_HASH = '99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_ENRICHMENT_HASH = '34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
EXPECTED_TARGETED_HASH = '1929f555b30c9bf987acb1929a6c26ca7ebbfe90cfddb631d1f5a60fe378d18b'
EXPECTED_TARGET_ACTOR = '0x9999b0cdd35d7f3b281ba02efc0d228486940515'
EXPECTED_SELECTOR = '0xd4d6ab16'
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')
ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')

AUTHORITY = {
    'network_access': True,
    'network_mode': 'READ_ONLY_ALLOWLISTED_BSC_RPC_POOL_INTROSPECTION_ONLY',
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


class Slice04RouteGraphError(RuntimeError):
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


def normalize_hash(value: Any) -> str:
    text = str(value or '').strip().lower()
    if HASH_RE.fullmatch(text) is None:
        raise Slice04RouteGraphError('INVALID_TRANSACTION_HASH')
    return text


def normalize_address(value: Any) -> str:
    text = str(value or '').strip().lower()
    if ADDRESS_RE.fullmatch(text) is None:
        raise Slice04RouteGraphError('INVALID_EVM_ADDRESS')
    return text


def read_json(path: Path, code: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise Slice04RouteGraphError(f'{code}_MISSING')
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise Slice04RouteGraphError(f'{code}_INVALID_JSON') from exc
    if not isinstance(value, dict):
        raise Slice04RouteGraphError(f'{code}_NOT_OBJECT')
    return value


def load_decoder(path: Path):
    if not path.is_file() or path.stat().st_size <= 0:
        raise Slice04RouteGraphError('DISCOVERY_DECODER_MISSING')
    spec = importlib.util.spec_from_file_location('tokenoskobi_slice04_route_decoder', path)
    if spec is None or spec.loader is None:
        raise Slice04RouteGraphError('DISCOVERY_DECODER_IMPORT_SPEC_INVALID')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_allowlist(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if payload.get('schema') != 'tokenoskobi.product_slice_04.factory_allowlist.v1':
        raise Slice04RouteGraphError('ALLOWLIST_SCHEMA_INVALID')
    if payload.get('chain') != 'BSC' or payload.get('chain_id') != 56:
        raise Slice04RouteGraphError('ALLOWLIST_CHAIN_INVALID')
    factories = payload.get('factories')
    if not isinstance(factories, dict) or len(factories) != 4:
        raise Slice04RouteGraphError('ALLOWLIST_FACTORY_COUNT_INVALID')
    result: dict[str, dict[str, Any]] = {}
    for address, item in factories.items():
        normalized = normalize_address(address)
        if normalized != address or not isinstance(item, dict):
            raise Slice04RouteGraphError('ALLOWLIST_FACTORY_ENTRY_INVALID')
        event_types = item.get('allowed_event_types')
        if not isinstance(event_types, list) or not event_types:
            raise Slice04RouteGraphError('ALLOWLIST_EVENT_TYPES_INVALID')
        if item.get('official_source_kind') != 'PROTOCOL_DEVELOPER_DOCS':
            raise Slice04RouteGraphError('ALLOWLIST_SOURCE_KIND_INVALID')
        result[normalized] = dict(item)
    return result


def validate_inputs(
    enrichment_path: Path,
    targeted_path: Path,
    allowlist_path: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    enrichment = read_json(enrichment_path, 'ENRICHMENT')
    if enrichment.get('schema') != 'tokenoskobi.product_slice_04.candidate_enrichment.v1':
        raise Slice04RouteGraphError('ENRICHMENT_SCHEMA_INVALID')
    if enrichment.get('result_hash') != EXPECTED_ENRICHMENT_HASH:
        raise Slice04RouteGraphError('ENRICHMENT_RESULT_HASH_INVALID')
    metadata_rows = enrichment.get('token_metadata')
    if not isinstance(metadata_rows, list) or len(metadata_rows) != 3:
        raise Slice04RouteGraphError('ENRICHMENT_METADATA_SCOPE_INVALID')
    metadata = {normalize_address(item.get('token_address')): dict(item) for item in metadata_rows}
    if len(metadata) != 3:
        raise Slice04RouteGraphError('ENRICHMENT_METADATA_DUPLICATE')

    targeted = read_json(targeted_path, 'TARGETED_HISTORY')
    if targeted.get('schema') != 'tokenoskobi.product_slice_04.targeted_actor_history_enrichment.v1':
        raise Slice04RouteGraphError('TARGETED_HISTORY_SCHEMA_INVALID')
    if targeted.get('status') != 'TARGETED_SAME_ACTOR_HISTORY_ENRICHMENT_COMPLETED':
        raise Slice04RouteGraphError('TARGETED_HISTORY_STATUS_INVALID')
    if targeted.get('result_hash') != EXPECTED_TARGETED_HASH:
        raise Slice04RouteGraphError('TARGETED_HISTORY_RESULT_HASH_INVALID')
    target_actors = targeted.get('target_actors')
    transactions = targeted.get('transactions')
    pairs = targeted.get('round_trip_pairs')
    if target_actors != [EXPECTED_TARGET_ACTOR]:
        raise Slice04RouteGraphError('TARGET_ACTOR_SCOPE_INVALID')
    if not isinstance(transactions, list) or len(transactions) != 6:
        raise Slice04RouteGraphError('TARGET_TRANSACTION_SCOPE_INVALID')
    if not isinstance(pairs, list) or len(pairs) != 5:
        raise Slice04RouteGraphError('ROUND_TRIP_PAIR_SCOPE_INVALID')
    tx_map: dict[str, dict[str, Any]] = {}
    for item in transactions:
        tx_hash = normalize_hash(item.get('tx_hash'))
        if tx_hash in tx_map:
            raise Slice04RouteGraphError('TARGET_TRANSACTION_DUPLICATE')
        if normalize_address(item.get('actor')) != EXPECTED_TARGET_ACTOR:
            raise Slice04RouteGraphError('TARGET_TRANSACTION_ACTOR_INVALID')
        if normalize_address(item.get('tx_to')) != EXPECTED_TARGET_ACTOR:
            raise Slice04RouteGraphError('TARGET_TRANSACTION_SELF_TARGET_INVALID')
        if item.get('selector') != EXPECTED_SELECTOR:
            raise Slice04RouteGraphError('TARGET_TRANSACTION_SELECTOR_INVALID')
        tx_map[tx_hash] = dict(item)

    allowlist_payload = read_json(allowlist_path, 'ALLOWLIST')
    allowlist = validate_allowlist(allowlist_payload)
    return metadata, targeted, allowlist, allowlist_payload


def load_receipts(database_path: Path, tx_hashes: set[str]) -> dict[str, dict[str, Any]]:
    resolved = database_path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file():
        raise Slice04RouteGraphError('SOURCE_DATABASE_PATH_INVALID')
    if file_sha256(resolved) != EXPECTED_DB_HASH:
        raise Slice04RouteGraphError('SOURCE_DATABASE_HASH_INVALID')
    uri = f'file:{resolved}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04RouteGraphError('SOURCE_DATABASE_INTEGRITY_FAILED')
        placeholders = ','.join('?' for _ in tx_hashes)
        rows = [dict(row) for row in conn.execute(
            f'''SELECT tx_hash,block_number,transaction_index,receipt_status,gas_cost_wei,
                       tx_from_address,tx_to_address,evidence_hash,raw_receipt_json
                FROM {RECEIPT_TABLE}
                WHERE tx_hash IN ({placeholders})
                ORDER BY block_number,transaction_index,tx_hash''',
            sorted(tx_hashes),
        )]
    finally:
        conn.close()
    result = {normalize_hash(row.get('tx_hash')): row for row in rows}
    if set(result) != tx_hashes or len(rows) != len(tx_hashes):
        raise Slice04RouteGraphError('TARGET_RECEIPT_COVERAGE_INVALID')
    return result


def decode_event_raw_amounts(swap: dict[str, Any]) -> tuple[int, int]:
    input_side = swap.get('input_side')
    output_side = swap.get('output_side')
    if input_side not in {0, 1} or output_side not in {0, 1} or input_side == output_side:
        raise Slice04RouteGraphError('SWAP_SIDE_INVALID')
    event_type = swap.get('event_type')
    if event_type == 'V2_SWAP':
        input_raw = int(str(swap.get(f'amount{input_side}_in_raw')))
        output_raw = int(str(swap.get(f'amount{output_side}_out_raw')))
    elif event_type in {'V3_SWAP', 'PANCAKE_V3_EXTENDED_SWAP'}:
        input_delta = int(str(swap.get(f'amount{input_side}_delta_raw')))
        output_delta = int(str(swap.get(f'amount{output_side}_delta_raw')))
        if input_delta <= 0 or output_delta >= 0:
            raise Slice04RouteGraphError('V3_DELTA_SIGN_INVALID')
        input_raw, output_raw = input_delta, -output_delta
    else:
        raise Slice04RouteGraphError('SWAP_EVENT_TYPE_UNSUPPORTED')
    if input_raw <= 0 or output_raw <= 0:
        raise Slice04RouteGraphError('SWAP_AMOUNT_INVALID')
    return input_raw, output_raw


def undirected_connected(edges: list[dict[str, Any]]) -> bool:
    if not edges:
        return False
    graph: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        source = edge['input_token']
        target = edge['output_token']
        graph[source].add(target)
        graph[target].add(source)
    start = next(iter(graph))
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == set(graph)


def directed_cycle_present(edges: list[dict[str, Any]]) -> bool:
    graph: dict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    for edge in edges:
        source = edge['input_token']
        target = edge['output_token']
        graph[source].add(target)
        nodes.update((source, target))
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for neighbor in graph.get(node, set()):
            if visit(neighbor):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in sorted(nodes) if node not in visited)


def actor_flow_endpoint_checks(actor_flow: dict[str, Any], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = actor_flow.get('token_flows') if isinstance(actor_flow, dict) else None
    if not isinstance(rows, list):
        raise Slice04RouteGraphError('ACTOR_FLOW_ROWS_INVALID')
    input_tokens = {edge['input_token'] for edge in edges}
    output_tokens = {edge['output_token'] for edge in edges}
    checks: list[dict[str, Any]] = []
    for row in rows:
        token = normalize_address(row.get('token_address'))
        direction = str(row.get('direction') or '')
        if direction == 'OUT':
            matched = token in input_tokens
            role = 'ROUTE_INPUT'
        elif direction == 'IN':
            matched = token in output_tokens
            role = 'ROUTE_OUTPUT'
        else:
            raise Slice04RouteGraphError('ACTOR_FLOW_DIRECTION_INVALID')
        checks.append({
            'token_address': token,
            'symbol': str(row.get('symbol') or 'UNKNOWN'),
            'direction': direction,
            'net_raw': str(row.get('net_raw') or ''),
            'expected_route_role': role,
            'matched': matched,
        })
    return checks


def build_transaction_route(
    transaction: dict[str, Any],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    ordered = sorted(edges, key=lambda item: (item['receipt_log_index'], item['pool_address']))
    endpoint_checks = actor_flow_endpoint_checks(transaction['actor_flow'], ordered)
    all_protocol_verified = bool(ordered) and all(item['protocol_verified'] for item in ordered)
    endpoint_consistent = bool(endpoint_checks) and all(item['matched'] for item in endpoint_checks)
    connected = undirected_connected(ordered)
    cycle = directed_cycle_present(ordered)
    route_tokens = sorted({token for edge in ordered for token in (edge['input_token'], edge['output_token'])})
    return {
        'tx_hash': transaction['tx_hash'],
        'block_number': int(transaction['block_number']),
        'transaction_index': int(transaction['transaction_index']),
        'block_time_utc': str(transaction['block_time_utc']),
        'actor': transaction['actor'],
        'transaction_target': transaction['tx_to'],
        'selector': transaction['selector'],
        'self_target_call': transaction['actor'] == transaction['tx_to'],
        'gas_cost_wei': str(transaction.get('gas_cost_wei') or ''),
        'actor_flow': transaction['actor_flow'],
        'actor_flow_endpoint_checks': endpoint_checks,
        'recognized_swap_event_count': len(ordered),
        'protocol_verified_swap_event_count': sum(int(item['protocol_verified']) for item in ordered),
        'all_swap_events_protocol_verified': all_protocol_verified,
        'actor_flow_route_endpoint_consistent': endpoint_consistent,
        'undirected_route_connected': connected,
        'directed_cycle_present': cycle,
        'route_evidence_usable': bool(all_protocol_verified and endpoint_consistent and connected),
        'route_tokens': route_tokens,
        'route_edges': ordered,
        'receipt_evidence_hash': str(transaction.get('receipt_evidence_hash') or ''),
    }


def pair_direction_endpoint_match(route: dict[str, Any], token: str, direction: str) -> bool:
    for item in route.get('actor_flow_endpoint_checks') or []:
        if item.get('token_address') == token and item.get('direction') == direction:
            return item.get('matched') is True
    return False


def build_pair_candidates(
    pairs: list[dict[str, Any]],
    route_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for pair in pairs:
        token = normalize_address(pair.get('token_address'))
        first_hash = normalize_hash(pair.get('first_tx_hash'))
        second_hash = normalize_hash(pair.get('second_tx_hash'))
        first = route_map.get(first_hash)
        second = route_map.get(second_hash)
        if first is None or second is None:
            raise Slice04RouteGraphError('PAIR_TRANSACTION_ROUTE_MISSING')
        first_direction = str(pair.get('first_direction') or '')
        second_direction = str(pair.get('second_direction') or '')
        opposite = {first_direction, second_direction} == {'IN', 'OUT'}
        first_endpoint = pair_direction_endpoint_match(first, token, first_direction)
        second_endpoint = pair_direction_endpoint_match(second, token, second_direction)
        same_actor = first['actor'] == second['actor'] == normalize_address(pair.get('actor'))
        same_selector = first['selector'] == second['selector'] == EXPECTED_SELECTOR
        route_pair_verified = bool(
            opposite
            and same_actor
            and same_selector
            and first['route_evidence_usable']
            and second['route_evidence_usable']
            and first_endpoint
            and second_endpoint
        )
        blockers: list[str] = []
        if not opposite:
            blockers.append('DIRECTION_NOT_OPPOSITE')
        if not same_actor:
            blockers.append('ACTOR_CHANGED')
        if not same_selector:
            blockers.append('SELECTOR_CHANGED')
        if not first['route_evidence_usable']:
            blockers.append('FIRST_ROUTE_EVIDENCE_NOT_USABLE')
        if not second['route_evidence_usable']:
            blockers.append('SECOND_ROUTE_EVIDENCE_NOT_USABLE')
        if not first_endpoint:
            blockers.append('FIRST_TOKEN_ROUTE_ENDPOINT_MISMATCH')
        if not second_endpoint:
            blockers.append('SECOND_TOKEN_ROUTE_ENDPOINT_MISMATCH')
        if route_pair_verified:
            blockers.extend([
                'COUNTERASSET_CONTINUITY_NOT_VERIFIED',
                'ROUTE_AMOUNT_CONSERVATION_NOT_VERIFIED',
                'NET_PERFORMANCE_NOT_RECONSTRUCTED',
            ])
        result.append({
            'actor': pair['actor'],
            'token_address': token,
            'first_tx_hash': first_hash,
            'first_direction': first_direction,
            'second_tx_hash': second_hash,
            'second_direction': second_direction,
            'block_distance': int(pair.get('block_distance')),
            'first_route_evidence_usable': first['route_evidence_usable'],
            'second_route_evidence_usable': second['route_evidence_usable'],
            'first_token_route_endpoint_match': first_endpoint,
            'second_token_route_endpoint_match': second_endpoint,
            'same_actor': same_actor,
            'same_selector': same_selector,
            'route_pair_verified': route_pair_verified,
            'counterasset_continuity_verified': False,
            'route_amount_conservation_verified': False,
            'net_performance_reconstructed': False,
            'closed_loop_confirmed': False,
            'blockers': blockers,
            'selection_score': (
                100 * int(route_pair_verified)
                + 20 * int(first_endpoint)
                + 20 * int(second_endpoint)
                + 10 * int(first['directed_cycle_present'])
                + 10 * int(second['directed_cycle_present'])
                - int(pair.get('block_distance')) / 1_000_000
            ),
        })
    return sorted(
        result,
        key=lambda item: (
            not item['route_pair_verified'],
            -item['selection_score'],
            item['block_distance'],
            item['first_tx_hash'],
            item['second_tx_hash'],
        ),
    )


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    os.chmod(temp, 0o600)
    json.loads(temp.read_text(encoding='utf-8'))
    temp.replace(path)
    os.chmod(path, 0o600)


def run(
    database_path: Path,
    provider_path: Path,
    enrichment_path: Path,
    targeted_path: Path,
    allowlist_path: Path,
    decoder_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    metadata, targeted, allowlist, allowlist_payload = validate_inputs(
        enrichment_path, targeted_path, allowlist_path
    )
    transactions = targeted['transactions']
    tx_map = {normalize_hash(item['tx_hash']): item for item in transactions}
    receipts = load_receipts(database_path, set(tx_map))
    decoder = load_decoder(decoder_path)
    provider = read_json(provider_path, 'PROVIDER')
    client = decoder.RpcClient(provider, maximum_requests=240, maximum_seconds=300.0)
    if decoder.parse_hex_int(client.call('eth_chainId', []), 'eth_chainId') != 56:
        raise Slice04RouteGraphError('RPC_CHAIN_ID_MISMATCH')

    pool_cache: dict[tuple[str, str], dict[str, Any]] = {}
    edges_by_tx: dict[str, list[dict[str, Any]]] = defaultdict(list)
    event_type_counts: Counter[str] = Counter()
    protocol_counts: Counter[str] = Counter()
    unverified_factories: set[str] = set()

    for tx_hash in sorted(tx_map):
        receipt_row = receipts[tx_hash]
        try:
            receipt = json.loads(str(receipt_row.get('raw_receipt_json') or ''))
        except json.JSONDecodeError as exc:
            raise Slice04RouteGraphError(f'RECEIPT_JSON_INVALID:{tx_hash}') from exc
        logs = receipt.get('logs') if isinstance(receipt, dict) else None
        if not isinstance(logs, list):
            raise Slice04RouteGraphError(f'RECEIPT_LOGS_INVALID:{tx_hash}')
        for position, log in enumerate(logs):
            if not isinstance(log, dict):
                continue
            decoded = decoder.decode_swap_log(log)
            if decoded is None:
                continue
            pool = decoder.normalize_address(log.get('address'))
            event_type = str(decoded.get('event_type') or '')
            cache_key = (pool, event_type)
            if cache_key not in pool_cache:
                pool_cache[cache_key] = decoder.introspect_pool(client, pool, event_type)
            identity = pool_cache[cache_key]
            decoded = decoder.apply_pool_tokens(decoded, identity, metadata)
            input_raw, output_raw = decode_event_raw_amounts(decoded)
            factory = normalize_address(identity.get('factory'))
            protocol = allowlist.get(factory)
            protocol_verified = bool(protocol and event_type in protocol.get('allowed_event_types', []))
            if protocol_verified:
                protocol_counts[str(protocol['protocol_id'])] += 1
            else:
                unverified_factories.add(factory)
            event_type_counts[event_type] += 1
            edges_by_tx[tx_hash].append({
                'tx_hash': tx_hash,
                'block_number': int(receipt_row['block_number']),
                'receipt_log_position': position,
                'receipt_log_index': decoder.parse_hex_int(log.get('logIndex') or '0x0', 'log.logIndex'),
                'event_type': event_type,
                'pool_address': pool,
                'factory': factory,
                'protocol_verified': protocol_verified,
                'protocol_id': protocol.get('protocol_id') if protocol_verified else 'UNVERIFIED',
                'protocol_name': protocol.get('protocol_name') if protocol_verified else 'UNVERIFIED',
                'protocol_version': protocol.get('version') if protocol_verified else 'UNVERIFIED',
                'input_token': normalize_address(decoded.get('input_token')),
                'output_token': normalize_address(decoded.get('output_token')),
                'input_raw': str(input_raw),
                'output_raw': str(output_raw),
                'fee': identity.get('fee'),
                'fee_status': identity.get('fee_status'),
                'pool_identity_temporal_limitation': identity.get('identity_temporal_limitation'),
                'log_evidence_hash': canonical_hash(log),
            })

    routes = [build_transaction_route(tx_map[tx_hash], edges_by_tx.get(tx_hash, [])) for tx_hash in sorted(tx_map)]
    route_map = {item['tx_hash']: item for item in routes}
    pairs = build_pair_candidates(targeted['round_trip_pairs'], route_map)
    verified_pairs = [item for item in pairs if item['route_pair_verified']]
    top_pair = pairs[0] if pairs else None
    next_step = (
        'TARGETED_ROUTE_AMOUNT_CONSERVATION_COUNTERASSET_AND_PERFORMANCE_RECONSTRUCTION'
        if verified_pairs
        else 'EXPAND_OR_RECLASSIFY_TARGETED_ROUTE_EVIDENCE'
    )

    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.targeted_swap_route_graph.v1',
        'generated_at_utc': iso_now(),
        'status': 'TARGETED_SWAP_ROUTE_GRAPH_COMPLETED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {
            'database_path': str(database_path.resolve()),
            'database_sha256': file_sha256(database_path),
            'candidate_enrichment_result_hash': EXPECTED_ENRICHMENT_HASH,
            'targeted_actor_history_result_hash': EXPECTED_TARGETED_HASH,
            'factory_allowlist_path': str(allowlist_path),
            'factory_allowlist_sha256': file_sha256(allowlist_path),
            'factory_allowlist_hash': canonical_hash(allowlist_payload),
            'decoder_path': str(decoder_path),
            'decoder_sha256': file_sha256(decoder_path),
        },
        'target_actor': EXPECTED_TARGET_ACTOR,
        'selector': EXPECTED_SELECTOR,
        'factory_allowlist': allowlist_payload,
        'transaction_routes': routes,
        'route_pair_candidates': pairs,
        'top_route_pair_candidate': top_pair,
        'rpc': {
            'request_count': client.request_count,
            'error_count': len(client.errors),
            'errors': client.errors[-30:],
        },
        'summary': {
            'target_transaction_count': len(routes),
            'recognized_swap_event_count': sum(len(item['route_edges']) for item in routes),
            'protocol_verified_swap_event_count': sum(item['protocol_verified_swap_event_count'] for item in routes),
            'route_evidence_usable_transaction_count': sum(int(item['route_evidence_usable']) for item in routes),
            'connected_route_transaction_count': sum(int(item['undirected_route_connected']) for item in routes),
            'directed_cycle_transaction_count': sum(int(item['directed_cycle_present']) for item in routes),
            'self_target_call_transaction_count': sum(int(item['self_target_call']) for item in routes),
            'route_pair_candidate_count': len(pairs),
            'route_pair_verified_count': len(verified_pairs),
            'event_type_counts': dict(sorted(event_type_counts.items())),
            'protocol_event_counts': dict(sorted(protocol_counts.items())),
            'unverified_factories': sorted(unverified_factories),
            'router_identity_verified': False,
            'counterasset_continuity_verified': False,
            'route_amount_conservation_verified': False,
            'net_performance_reconstructed': False,
            'closed_loop_confirmed': False,
            'next_safe_step': next_step,
        },
        'runtime_seconds': round(time.monotonic() - started, 6),
    }
    payload['result_hash'] = canonical_hash(payload)
    atomic_write_json(output_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=DEFAULT_DB)
    parser.add_argument('--provider', type=Path, default=DEFAULT_PROVIDER)
    parser.add_argument('--enrichment', type=Path, default=DEFAULT_ENRICHMENT)
    parser.add_argument('--targeted', type=Path, default=DEFAULT_TARGETED)
    parser.add_argument('--allowlist', type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument('--decoder', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(
        args.database,
        args.provider,
        args.enrichment,
        args.targeted,
        args.allowlist,
        args.decoder,
        args.output,
    )
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'TARGET_TRANSACTION_COUNT={summary["target_transaction_count"]}')
    print(f'RECOGNIZED_SWAP_EVENT_COUNT={summary["recognized_swap_event_count"]}')
    print(f'PROTOCOL_VERIFIED_SWAP_EVENT_COUNT={summary["protocol_verified_swap_event_count"]}')
    print(f'ROUTE_EVIDENCE_USABLE_TRANSACTION_COUNT={summary["route_evidence_usable_transaction_count"]}')
    print(f'CONNECTED_ROUTE_TRANSACTION_COUNT={summary["connected_route_transaction_count"]}')
    print(f'DIRECTED_CYCLE_TRANSACTION_COUNT={summary["directed_cycle_transaction_count"]}')
    print(f'SELF_TARGET_CALL_TRANSACTION_COUNT={summary["self_target_call_transaction_count"]}')
    print(f'ROUTE_PAIR_CANDIDATE_COUNT={summary["route_pair_candidate_count"]}')
    print(f'ROUTE_PAIR_VERIFIED_COUNT={summary["route_pair_verified_count"]}')
    print('EVENT_TYPE_COUNTS=' + json.dumps(summary['event_type_counts'], sort_keys=True, separators=(',', ':')))
    print('PROTOCOL_EVENT_COUNTS=' + json.dumps(summary['protocol_event_counts'], sort_keys=True, separators=(',', ':')))
    print('UNVERIFIED_FACTORIES=' + json.dumps(summary['unverified_factories'], separators=(',', ':')))
    for index, route in enumerate(result['transaction_routes'], start=1):
        flows = '|'.join(
            f'{item["symbol"]}:{item["direction"]}:{item["net_raw"]}'
            for item in route['actor_flow_endpoint_checks']
        ) or 'NONE'
        print(
            f'ROUTE_TX_{index}=tx:{route["tx_hash"]},block:{route["block_number"]},'
            f'swaps:{route["recognized_swap_event_count"]},protocol_verified:{str(route["all_swap_events_protocol_verified"]).lower()},'
            f'connected:{str(route["undirected_route_connected"]).lower()},cycle:{str(route["directed_cycle_present"]).lower()},'
            f'endpoint_consistent:{str(route["actor_flow_route_endpoint_consistent"]).lower()},'
            f'usable:{str(route["route_evidence_usable"]).lower()},flows:{flows}'
        )
    top = result.get('top_route_pair_candidate')
    if top:
        print(
            'TOP_ROUTE_PAIR_CANDIDATE='
            f'token:{top["token_address"]},first_tx:{top["first_tx_hash"]},first:{top["first_direction"]},'
            f'second_tx:{top["second_tx_hash"]},second:{top["second_direction"]},'
            f'route_pair_verified:{str(top["route_pair_verified"]).lower()},'
            f'blockers:{"|".join(top["blockers"]) or "NONE"}'
        )
    else:
        print('TOP_ROUTE_PAIR_CANDIDATE=NONE')
    print(f'RPC_REQUEST_COUNT={result["rpc"]["request_count"]}')
    print(f'RPC_ERROR_COUNT={result["rpc"]["error_count"]}')
    print(f'RESULT_HASH={result["result_hash"]}')
    print('ROUTER_IDENTITY_VERIFIED=false')
    print('CLOSED_LOOP_CONFIRMED=false')
    print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
