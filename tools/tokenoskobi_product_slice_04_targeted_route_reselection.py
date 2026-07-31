#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
DEFAULT_DB = ROOT / 'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
DEFAULT_PROVIDER = ROOT / 'config/era63e_always_on_market_runtime_v1.json'
DEFAULT_TARGETED = Path('/var/lib/tokenoskobi-product-slice-04/targeted_actor_history_enrichment_v1.json')
DEFAULT_ENRICHMENT = Path('/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json')
DEFAULT_ALLOWLIST = ROOT / 'config/product_slice_04_factory_allowlist_v1.json'
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/targeted_route_reselection_v1.json')
RECEIPT_TABLE = 'era64j_historical_receipt_cost_enrichment_v1'
EXPECTED_DB_HASH = '99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_TARGETED_HASH = '1929f555b30c9bf987acb1929a6c26ca7ebbfe90cfddb631d1f5a60fe378d18b'
EXPECTED_ENRICHMENT_HASH = '34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')
ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')
HEX_RE = re.compile(r'^0x(?:[0-9a-f]{2})*$')
ZERO = '0x0000000000000000000000000000000000000000'
MAX_TARGET_TRANSACTIONS = 6
MAX_RECOGNIZED_SWAP_EVENTS = 80
MAX_RPC_REQUESTS = 300

AUTHORITY = {
    'network_access': True,
    'network_mode': 'READ_ONLY_ALLOWLISTED_BSC_RPC_POOL_IDENTITY_ONLY',
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


class Slice04TargetedRouteError(RuntimeError):
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
        raise Slice04TargetedRouteError('INVALID_HASH')
    return text


def normalize_address(value: Any, *, allow_empty: bool = False) -> str:
    text = str(value or '').strip().lower()
    if allow_empty and not text:
        return ''
    if ADDRESS_RE.fullmatch(text) is None:
        raise Slice04TargetedRouteError('INVALID_ADDRESS')
    return text


def validate_hex(value: Any, field: str) -> str:
    text = str(value or '').strip().lower()
    if HEX_RE.fullmatch(text) is None:
        raise Slice04TargetedRouteError(f'{field}:INVALID_HEX')
    return text


def read_json(path: Path, code: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise Slice04TargetedRouteError(f'{code}_MISSING')
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise Slice04TargetedRouteError(f'{code}_INVALID_JSON') from exc
    if not isinstance(payload, dict):
        raise Slice04TargetedRouteError(f'{code}_NOT_OBJECT')
    return payload


def load_base_module(path: Path):
    spec = importlib.util.spec_from_file_location('tokenoskobi_slice04_discovery_base', path)
    if spec is None or spec.loader is None:
        raise Slice04TargetedRouteError('DISCOVERY_BASE_IMPORT_INVALID')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_inputs(
    targeted_path: Path,
    enrichment_path: Path,
    allowlist_path: Path,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    targeted = read_json(targeted_path, 'TARGETED_HISTORY')
    if targeted.get('schema') != 'tokenoskobi.product_slice_04.targeted_actor_history_enrichment.v1':
        raise Slice04TargetedRouteError('TARGETED_HISTORY_SCHEMA_INVALID')
    if targeted.get('status') != 'TARGETED_SAME_ACTOR_HISTORY_ENRICHMENT_COMPLETED':
        raise Slice04TargetedRouteError('TARGETED_HISTORY_STATUS_INVALID')
    if targeted.get('result_hash') != EXPECTED_TARGETED_HASH:
        raise Slice04TargetedRouteError('TARGETED_HISTORY_HASH_INVALID')
    transactions = targeted.get('transactions')
    if not isinstance(transactions, list) or len(transactions) != MAX_TARGET_TRANSACTIONS:
        raise Slice04TargetedRouteError('TARGETED_TRANSACTION_SCOPE_INVALID')
    if targeted.get('target_actors') != ['0x9999b0cdd35d7f3b281ba02efc0d228486940515']:
        raise Slice04TargetedRouteError('TARGET_ACTOR_DRIFT')
    if len(targeted.get('round_trip_pairs') or []) != 5:
        raise Slice04TargetedRouteError('ROUND_TRIP_PAIR_SCOPE_INVALID')

    enrichment = read_json(enrichment_path, 'ENRICHMENT')
    if enrichment.get('schema') != 'tokenoskobi.product_slice_04.candidate_enrichment.v1':
        raise Slice04TargetedRouteError('ENRICHMENT_SCHEMA_INVALID')
    if enrichment.get('result_hash') != EXPECTED_ENRICHMENT_HASH:
        raise Slice04TargetedRouteError('ENRICHMENT_HASH_INVALID')
    metadata_rows = enrichment.get('token_metadata')
    if not isinstance(metadata_rows, list) or len(metadata_rows) != 3:
        raise Slice04TargetedRouteError('TOKEN_METADATA_SCOPE_INVALID')
    metadata: dict[str, dict[str, Any]] = {}
    for row in metadata_rows:
        if not isinstance(row, dict):
            raise Slice04TargetedRouteError('TOKEN_METADATA_ENTRY_INVALID')
        token = normalize_address(row.get('token_address'))
        if token in metadata:
            raise Slice04TargetedRouteError('TOKEN_METADATA_DUPLICATE')
        metadata[token] = dict(row)

    allowlist_payload = read_json(allowlist_path, 'ALLOWLIST')
    if allowlist_payload.get('schema') != 'tokenoskobi.product_slice_04.factory_allowlist.v1':
        raise Slice04TargetedRouteError('ALLOWLIST_SCHEMA_INVALID')
    if allowlist_payload.get('chain') != 'BSC' or allowlist_payload.get('chain_id') != 56:
        raise Slice04TargetedRouteError('ALLOWLIST_CHAIN_INVALID')
    factories = allowlist_payload.get('factories')
    if not isinstance(factories, dict) or len(factories) != 4:
        raise Slice04TargetedRouteError('ALLOWLIST_FACTORY_SCOPE_INVALID')
    allowlist: dict[str, dict[str, Any]] = {}
    for address, item in factories.items():
        normalized = normalize_address(address)
        if normalized != address or not isinstance(item, dict):
            raise Slice04TargetedRouteError('ALLOWLIST_ENTRY_INVALID')
        event_types = item.get('allowed_event_types')
        if not isinstance(event_types, list) or not event_types:
            raise Slice04TargetedRouteError('ALLOWLIST_EVENT_TYPE_INVALID')
        allowlist[normalized] = dict(item)
    return targeted, metadata, allowlist, allowlist_payload


def load_receipts(database_path: Path, tx_hashes: list[str]) -> dict[str, dict[str, Any]]:
    resolved = database_path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file() or file_sha256(resolved) != EXPECTED_DB_HASH:
        raise Slice04TargetedRouteError('SOURCE_DATABASE_INVALID')
    if len(tx_hashes) != MAX_TARGET_TRANSACTIONS or len(set(tx_hashes)) != MAX_TARGET_TRANSACTIONS:
        raise Slice04TargetedRouteError('TARGET_HASH_SCOPE_INVALID')
    uri = f'file:{resolved}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04TargetedRouteError('SOURCE_DATABASE_INTEGRITY_FAILED')
        placeholders = ','.join('?' for _ in tx_hashes)
        rows = [dict(row) for row in conn.execute(
            f'''SELECT tx_hash,block_number,transaction_index,receipt_status,gas_cost_wei,
                       tx_from_address,tx_to_address,evidence_hash,raw_receipt_json
                FROM {RECEIPT_TABLE}
                WHERE tx_hash IN ({placeholders})
                ORDER BY block_number,transaction_index,tx_hash''',
            tx_hashes,
        )]
    finally:
        conn.close()
    result = {normalize_hash(row['tx_hash']): row for row in rows}
    if set(result) != set(tx_hashes) or len(rows) != len(tx_hashes):
        raise Slice04TargetedRouteError('RECEIPT_COVERAGE_INVALID')
    return result


def decode_transfer_log(log: dict[str, Any]) -> dict[str, Any] | None:
    topics = log.get('topics')
    if not isinstance(topics, list) or not topics:
        return None
    if normalize_hash(topics[0]) != TRANSFER_TOPIC:
        return None
    if len(topics) == 4:
        return None
    if len(topics) != 3:
        raise Slice04TargetedRouteError('TRANSFER_TOPIC_COUNT_INVALID')
    data = validate_hex(log.get('data') or '', 'transfer.data')
    payload = data[2:]
    if len(payload) != 64:
        raise Slice04TargetedRouteError('TRANSFER_DATA_LENGTH_INVALID')
    amount = int(payload, 16)
    if amount < 0:
        raise Slice04TargetedRouteError('TRANSFER_AMOUNT_INVALID')
    return {
        'token_address': normalize_address(log.get('address')),
        'from_address': normalize_address('0x' + normalize_hash(topics[1])[-40:]),
        'to_address': normalize_address('0x' + normalize_hash(topics[2])[-40:]),
        'amount_raw': amount,
    }


def actor_net_from_receipt(logs: list[dict[str, Any]], actor: str) -> dict[str, int]:
    net: dict[str, int] = defaultdict(int)
    for log in logs:
        transfer = decode_transfer_log(log)
        if transfer is None:
            continue
        token = transfer['token_address']
        amount = int(transfer['amount_raw'])
        if transfer['from_address'] == actor:
            net[token] -= amount
        if transfer['to_address'] == actor:
            net[token] += amount
    return {token: amount for token, amount in net.items() if amount != 0}


def swap_raw_amounts(decoded: dict[str, Any]) -> tuple[int, int]:
    input_side = decoded.get('input_side')
    output_side = decoded.get('output_side')
    if input_side not in {0, 1} or output_side not in {0, 1} or input_side == output_side:
        raise Slice04TargetedRouteError('SWAP_SIDE_INVALID')
    event_type = decoded.get('event_type')
    if event_type == 'V2_SWAP':
        input_raw = int(str(decoded[f'amount{input_side}_in_raw']))
        output_raw = int(str(decoded[f'amount{output_side}_out_raw']))
    elif event_type in {'V3_SWAP', 'PANCAKE_V3_EXTENDED_SWAP'}:
        input_delta = int(str(decoded[f'amount{input_side}_delta_raw']))
        output_delta = int(str(decoded[f'amount{output_side}_delta_raw']))
        if input_delta <= 0 or output_delta >= 0:
            raise Slice04TargetedRouteError('V3_DELTA_SIGN_INVALID')
        input_raw, output_raw = input_delta, -output_delta
    else:
        raise Slice04TargetedRouteError('SWAP_EVENT_UNSUPPORTED')
    if input_raw <= 0 or output_raw <= 0:
        raise Slice04TargetedRouteError('SWAP_AMOUNT_INVALID')
    return input_raw, output_raw


def aggregate_swap_net(events: list[dict[str, Any]]) -> dict[str, int]:
    net: dict[str, int] = defaultdict(int)
    for event in events:
        decoded = event['swap']
        input_token = normalize_address(decoded['input_token'])
        output_token = normalize_address(decoded['output_token'])
        input_raw, output_raw = swap_raw_amounts(decoded)
        net[input_token] -= input_raw
        net[output_token] += output_raw
    return {token: amount for token, amount in net.items() if amount != 0}


def classify_transaction_route(
    actor_net: dict[str, int],
    protocol_events: list[dict[str, Any]],
    recognized_event_count: int,
    unverified_event_count: int,
) -> dict[str, Any]:
    swap_net = aggregate_swap_net(protocol_events)
    actor_tokens = set(actor_net)
    swap_tokens = set(swap_net)
    actor_out = sorted(token for token, amount in actor_net.items() if amount < 0)
    actor_in = sorted(token for token, amount in actor_net.items() if amount > 0)
    exact_token_set = bool(actor_tokens) and actor_tokens == swap_tokens
    exact_raw_amounts = exact_token_set and all(actor_net[token] == swap_net[token] for token in actor_tokens)
    single_endpoint_pair = len(actor_out) == 1 and len(actor_in) == 1
    all_recognized_verified = recognized_event_count > 0 and unverified_event_count == 0
    route_verified = bool(all_recognized_verified and single_endpoint_pair and exact_raw_amounts)
    blockers: list[str] = []
    if recognized_event_count == 0:
        blockers.append('NO_RECOGNIZED_SWAP_EVENT')
    if unverified_event_count:
        blockers.append('UNVERIFIED_FACTORY_EVENT_PRESENT')
    if not single_endpoint_pair:
        blockers.append('ACTOR_ENDPOINT_PAIR_NOT_SINGLE')
    if not exact_token_set:
        blockers.append('ACTOR_SWAP_NET_TOKEN_SET_MISMATCH')
    if exact_token_set and not exact_raw_amounts:
        blockers.append('ACTOR_SWAP_NET_RAW_AMOUNT_MISMATCH')
    return {
        'actor_net_by_token': {token: str(amount) for token, amount in sorted(actor_net.items())},
        'swap_net_by_token': {token: str(amount) for token, amount in sorted(swap_net.items())},
        'actor_out_tokens': actor_out,
        'actor_in_tokens': actor_in,
        'single_endpoint_pair': single_endpoint_pair,
        'exact_token_set': exact_token_set,
        'exact_raw_amounts': bool(exact_raw_amounts),
        'all_recognized_events_protocol_verified': all_recognized_verified,
        'route_verified': route_verified,
        'route_input_token': actor_out[0] if single_endpoint_pair else '',
        'route_output_token': actor_in[0] if single_endpoint_pair else '',
        'route_input_raw': str(abs(actor_net[actor_out[0]])) if single_endpoint_pair else '',
        'route_output_raw': str(actor_net[actor_in[0]]) if single_endpoint_pair else '',
        'blockers': blockers,
    }


def build_closed_loop_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verified = [item for item in records if item['route']['route_verified']]
    verified.sort(key=lambda row: (row['block_number'], row['transaction_index'], row['tx_hash']))
    candidates: list[dict[str, Any]] = []
    for index, opening in enumerate(verified):
        for closing in verified[index + 1:]:
            if opening['actor'] != closing['actor'] or opening['tx_hash'] == closing['tx_hash']:
                continue
            open_route = opening['route']
            close_route = closing['route']
            reversed_pair = (
                open_route['route_input_token'] == close_route['route_output_token']
                and open_route['route_output_token'] == close_route['route_input_token']
            )
            if not reversed_pair:
                continue
            position_amount_exact = open_route['route_output_raw'] == close_route['route_input_raw']
            blockers = [] if position_amount_exact else ['POSITION_TOKEN_AMOUNT_NOT_FULLY_CLOSED']
            candidates.append({
                'actor': opening['actor'],
                'opening_tx_hash': opening['tx_hash'],
                'closing_tx_hash': closing['tx_hash'],
                'opening_block_number': opening['block_number'],
                'closing_block_number': closing['block_number'],
                'block_distance': closing['block_number'] - opening['block_number'],
                'base_token': open_route['route_input_token'],
                'position_token': open_route['route_output_token'],
                'base_spent_raw': open_route['route_input_raw'],
                'position_acquired_raw': open_route['route_output_raw'],
                'position_sold_raw': close_route['route_input_raw'],
                'base_received_raw': close_route['route_output_raw'],
                'position_amount_exact': position_amount_exact,
                'closed_loop_confirmed': position_amount_exact,
                'opening_protocols': opening['protocol_ids'],
                'closing_protocols': closing['protocol_ids'],
                'opening_pools': opening['pool_addresses'],
                'closing_pools': closing['pool_addresses'],
                'blockers': blockers,
            })
    return sorted(candidates, key=lambda row: (not row['closed_loop_confirmed'], row['block_distance'], row['opening_tx_hash'], row['closing_tx_hash']))


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
    targeted_path: Path,
    enrichment_path: Path,
    allowlist_path: Path,
    output_path: Path,
    base_module_path: Path,
) -> dict[str, Any]:
    targeted, metadata, allowlist, allowlist_payload = validate_inputs(targeted_path, enrichment_path, allowlist_path)
    tx_map = {normalize_hash(item['tx_hash']): item for item in targeted['transactions']}
    tx_hashes = sorted(tx_map)
    receipts = load_receipts(database_path, tx_hashes)
    base = load_base_module(base_module_path)
    provider = read_json(provider_path, 'PROVIDER')
    client = base.RpcClient(provider, maximum_requests=MAX_RPC_REQUESTS, maximum_seconds=300.0)
    if base.parse_hex_int(client.call('eth_chainId', []), 'eth_chainId') != 56:
        raise Slice04TargetedRouteError('RPC_CHAIN_ID_MISMATCH')

    pool_cache: dict[tuple[str, str], dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    total_recognized = 0
    total_verified = 0
    protocol_counts: Counter[str] = Counter()
    for tx_hash in tx_hashes:
        tx = tx_map[tx_hash]
        receipt_row = receipts[tx_hash]
        if normalize_address(tx['actor']) != normalize_address(receipt_row['tx_from_address']):
            raise Slice04TargetedRouteError('ACTOR_RECEIPT_MISMATCH')
        receipt = json.loads(str(receipt_row['raw_receipt_json']))
        logs = receipt.get('logs') if isinstance(receipt, dict) else None
        if not isinstance(logs, list):
            raise Slice04TargetedRouteError('RECEIPT_LOGS_INVALID')
        actor = normalize_address(tx['actor'])
        actor_net = actor_net_from_receipt(logs, actor)
        protocol_events: list[dict[str, Any]] = []
        recognized_count = 0
        unverified_count = 0
        event_rows: list[dict[str, Any]] = []
        for position, log in enumerate(logs):
            if not isinstance(log, dict):
                continue
            decoded = base.decode_swap_log(log)
            if decoded is None:
                continue
            recognized_count += 1
            total_recognized += 1
            if total_recognized > MAX_RECOGNIZED_SWAP_EVENTS:
                raise Slice04TargetedRouteError('RECOGNIZED_SWAP_EVENT_SCOPE_EXCEEDED')
            pool = normalize_address(log.get('address'))
            cache_key = (pool, decoded['event_type'])
            if cache_key not in pool_cache:
                pool_cache[cache_key] = base.introspect_pool(client, pool, decoded['event_type'])
            identity = pool_cache[cache_key]
            decoded = base.apply_pool_tokens(decoded, identity, metadata)
            factory = normalize_address(identity['factory'])
            protocol = allowlist.get(factory)
            verified = bool(protocol and decoded['event_type'] in protocol.get('allowed_event_types', []))
            if verified:
                total_verified += 1
                protocol_counts[str(protocol['protocol_id'])] += 1
            else:
                unverified_count += 1
            input_raw, output_raw = swap_raw_amounts(decoded)
            event_row = {
                'receipt_log_position': position,
                'receipt_log_index': base.parse_hex_int(log.get('logIndex') or '0x0', 'log.logIndex'),
                'pool_address': pool,
                'factory': factory,
                'protocol_verified': verified,
                'protocol_id': str(protocol.get('protocol_id')) if verified else 'UNVERIFIED',
                'event_type': decoded['event_type'],
                'input_token': decoded['input_token'],
                'output_token': decoded['output_token'],
                'input_raw': str(input_raw),
                'output_raw': str(output_raw),
                'log_evidence_hash': canonical_hash(log),
                'swap': decoded,
            }
            event_rows.append(event_row)
            if verified:
                protocol_events.append(event_row)
        route = classify_transaction_route(actor_net, protocol_events, recognized_count, unverified_count)
        tx_to = normalize_address(tx['tx_to'], allow_empty=True)
        records.append({
            'tx_hash': tx_hash,
            'block_number': int(tx['block_number']),
            'transaction_index': int(tx['transaction_index']),
            'block_time_utc': str(tx['block_time_utc']),
            'actor': actor,
            'transaction_target': tx_to,
            'selector': str(tx['selector']),
            'self_call': bool(tx_to and actor == tx_to),
            'receipt_status': int(receipt_row['receipt_status']),
            'gas_cost_wei': str(receipt_row['gas_cost_wei']),
            'receipt_evidence_hash': str(receipt_row['evidence_hash']),
            'recognized_swap_event_count': recognized_count,
            'protocol_verified_swap_event_count': len(protocol_events),
            'unverified_swap_event_count': unverified_count,
            'protocol_ids': sorted({row['protocol_id'] for row in protocol_events}),
            'pool_addresses': sorted({row['pool_address'] for row in protocol_events}),
            'events': event_rows,
            'route': route,
        })

    records.sort(key=lambda row: (row['block_number'], row['transaction_index'], row['tx_hash']))
    candidates = build_closed_loop_candidates(records)
    confirmed = [item for item in candidates if item['closed_loop_confirmed']]
    next_step = (
        'EXECUTION_PRICE_GAS_FEE_AND_PERFORMANCE_RECONSTRUCTION'
        if confirmed
        else 'CLASSIFY_EXECUTOR_ROUTE_BLOCKERS_AND_EXTEND_ONLY_IF_EVIDENCE_REQUIRES'
    )
    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.targeted_route_reselection.v1',
        'generated_at_utc': iso_now(),
        'status': 'TARGETED_MULTI_HOP_ROUTE_RESELECTION_COMPLETED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {
            'database_path': str(database_path.resolve()),
            'database_sha256': file_sha256(database_path),
            'targeted_history_path': str(targeted_path),
            'targeted_history_result_hash': targeted['result_hash'],
            'candidate_enrichment_result_hash': EXPECTED_ENRICHMENT_HASH,
            'factory_allowlist_path': str(allowlist_path),
            'factory_allowlist_sha256': file_sha256(allowlist_path),
            'factory_allowlist_hash': canonical_hash(allowlist_payload),
        },
        'policy': {
            'transaction_level_net_reconstruction': True,
            'all_receipt_erc20_transfers_included': True,
            'multi_hop_and_split_routes_supported': True,
            'all_recognized_swap_events_must_be_officially_allowlisted': True,
            'actor_and_swap_net_token_sets_must_match_exactly': True,
            'actor_and_swap_raw_amounts_must_match_exactly': True,
            'closed_loop_requires_reversed_endpoint_pair': True,
            'closed_loop_requires_full_position_raw_amount_reversal': True,
            'same_pool_required': False,
            'same_protocol_required': False,
        },
        'transactions': records,
        'closed_loop_candidates': candidates,
        'top_candidate': candidates[0] if candidates else None,
        'rpc': {
            'request_count': client.request_count,
            'error_count': len(client.errors),
            'errors': client.errors[-30:],
        },
        'summary': {
            'target_transaction_count': len(records),
            'recognized_swap_event_count': total_recognized,
            'protocol_verified_swap_event_count': total_verified,
            'route_verified_transaction_count': sum(int(item['route']['route_verified']) for item in records),
            'reversed_route_candidate_count': len(candidates),
            'full_position_closed_loop_count': len(confirmed),
            'self_call_transaction_count': sum(int(item['self_call']) for item in records),
            'protocol_event_counts': dict(sorted(protocol_counts.items())),
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
    parser.add_argument('--provider', type=Path, default=DEFAULT_PROVIDER)
    parser.add_argument('--targeted', type=Path, default=DEFAULT_TARGETED)
    parser.add_argument('--enrichment', type=Path, default=DEFAULT_ENRICHMENT)
    parser.add_argument('--allowlist', type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--base-module', type=Path, required=True)
    args = parser.parse_args()
    result = run(
        args.database,
        args.provider,
        args.targeted,
        args.enrichment,
        args.allowlist,
        args.output,
        args.base_module,
    )
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'TARGET_TRANSACTION_COUNT={summary["target_transaction_count"]}')
    print(f'RECOGNIZED_SWAP_EVENT_COUNT={summary["recognized_swap_event_count"]}')
    print(f'PROTOCOL_VERIFIED_SWAP_EVENT_COUNT={summary["protocol_verified_swap_event_count"]}')
    print(f'ROUTE_VERIFIED_TRANSACTION_COUNT={summary["route_verified_transaction_count"]}')
    print(f'REVERSED_ROUTE_CANDIDATE_COUNT={summary["reversed_route_candidate_count"]}')
    print(f'FULL_POSITION_CLOSED_LOOP_COUNT={summary["full_position_closed_loop_count"]}')
    print(f'SELF_CALL_TRANSACTION_COUNT={summary["self_call_transaction_count"]}')
    print('PROTOCOL_EVENT_COUNTS=' + json.dumps(summary['protocol_event_counts'], sort_keys=True, separators=(',', ':')))
    for index, tx in enumerate(result['transactions'], start=1):
        route = tx['route']
        print(
            f'ROUTE_TX_{index}=tx:{tx["tx_hash"]},block:{tx["block_number"]},'
            f'swaps:{tx["recognized_swap_event_count"]},verified_swaps:{tx["protocol_verified_swap_event_count"]},'
            f'input:{route["route_input_token"] or "NONE"},output:{route["route_output_token"] or "NONE"},'
            f'exact_tokens:{str(route["exact_token_set"]).lower()},exact_amounts:{str(route["exact_raw_amounts"]).lower()},'
            f'verified:{str(route["route_verified"]).lower()},blockers:{"|".join(route["blockers"]) or "NONE"}'
        )
    top = result.get('top_candidate')
    if top:
        print(
            'TOP_CLOSED_LOOP_CANDIDATE='
            f'open_tx:{top["opening_tx_hash"]},close_tx:{top["closing_tx_hash"]},'
            f'base:{top["base_token"]},position:{top["position_token"]},'
            f'position_acquired:{top["position_acquired_raw"]},position_sold:{top["position_sold_raw"]},'
            f'full_position:{str(top["position_amount_exact"]).lower()},'
            f'confirmed:{str(top["closed_loop_confirmed"]).lower()},'
            f'blockers:{"|".join(top["blockers"]) or "NONE"}'
        )
    else:
        print('TOP_CLOSED_LOOP_CANDIDATE=NONE')
    print(f'RPC_REQUEST_COUNT={result["rpc"]["request_count"]}')
    print(f'RPC_ERROR_COUNT={result["rpc"]["error_count"]}')
    print(f'RESULT_HASH={result["result_hash"]}')
    print(f'CLOSED_LOOP_CONFIRMED={str(summary["closed_loop_confirmed"]).lower()}')
    print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
