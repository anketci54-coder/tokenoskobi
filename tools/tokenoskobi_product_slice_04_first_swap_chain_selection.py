#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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
DEFAULT_ENRICHMENT = Path('/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json')
DEFAULT_DISCOVERY = Path('/var/lib/tokenoskobi-product-slice-04/swap_pool_discovery_v1.json')
DEFAULT_ALLOWLIST = ROOT / 'config/product_slice_04_factory_allowlist_v1.json'
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/first_swap_chain_selection_v1.json')

SOURCE_TABLE = 'era64i_historical_wallet_transfer_staging_v1'
EXPECTED_DB_HASH = '99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_ENRICHMENT_HASH = '34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
EXPECTED_DISCOVERY_HASH = '94ab3493b18a064aae90a25bd2cf54ebdba1b5463c997cf2a04bc09c78a933f2'
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')
ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')

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


class Slice04ChainSelectionError(RuntimeError):
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
        raise Slice04ChainSelectionError('INVALID_TRANSACTION_HASH')
    return text


def normalize_address(value: Any) -> str:
    text = str(value or '').strip().lower()
    if ADDRESS_RE.fullmatch(text) is None:
        raise Slice04ChainSelectionError('INVALID_EVM_ADDRESS')
    return text


def read_json(path: Path, code: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise Slice04ChainSelectionError(f'{code}_MISSING')
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise Slice04ChainSelectionError(f'{code}_INVALID_JSON') from exc
    if not isinstance(payload, dict):
        raise Slice04ChainSelectionError(f'{code}_NOT_OBJECT')
    return payload


def validate_allowlist(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if payload.get('schema') != 'tokenoskobi.product_slice_04.factory_allowlist.v1':
        raise Slice04ChainSelectionError('ALLOWLIST_SCHEMA_INVALID')
    if payload.get('chain') != 'BSC' or payload.get('chain_id') != 56:
        raise Slice04ChainSelectionError('ALLOWLIST_CHAIN_INVALID')
    policy = payload.get('policy')
    if not isinstance(policy, dict):
        raise Slice04ChainSelectionError('ALLOWLIST_POLICY_MISSING')
    required_policy = {
        'official_protocol_source_required': True,
        'unlisted_factory_protocol_identity': 'UNVERIFIED',
        'router_identity_inferred_from_factory': False,
        'closed_loop_requires_strict_pair_direction_and_amount_match': True,
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            raise Slice04ChainSelectionError(f'ALLOWLIST_POLICY_INVALID:{key}')
    factories = payload.get('factories')
    if not isinstance(factories, dict) or len(factories) != 4:
        raise Slice04ChainSelectionError('ALLOWLIST_FACTORY_COUNT_INVALID')
    result: dict[str, dict[str, Any]] = {}
    for address, item in factories.items():
        normalized = normalize_address(address)
        if normalized != address or not isinstance(item, dict):
            raise Slice04ChainSelectionError('ALLOWLIST_FACTORY_ENTRY_INVALID')
        if item.get('official_source_kind') != 'PROTOCOL_DEVELOPER_DOCS':
            raise Slice04ChainSelectionError('ALLOWLIST_SOURCE_KIND_INVALID')
        if not str(item.get('official_source_url') or '').startswith('https://'):
            raise Slice04ChainSelectionError('ALLOWLIST_SOURCE_URL_INVALID')
        event_types = item.get('allowed_event_types')
        if not isinstance(event_types, list) or not event_types:
            raise Slice04ChainSelectionError('ALLOWLIST_EVENT_TYPES_INVALID')
        result[normalized] = dict(item)
    return result


def load_inputs(
    enrichment_path: Path,
    discovery_path: Path,
    allowlist_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    enrichment = read_json(enrichment_path, 'ENRICHMENT')
    if enrichment.get('schema') != 'tokenoskobi.product_slice_04.candidate_enrichment.v1':
        raise Slice04ChainSelectionError('ENRICHMENT_SCHEMA_INVALID')
    if enrichment.get('status') != 'CANDIDATE_INPUT_AND_TOKEN_METADATA_ENRICHMENT_VERIFIED_WITH_ARCHIVE_FALLBACK_POLICY':
        raise Slice04ChainSelectionError('ENRICHMENT_STATUS_INVALID')
    if enrichment.get('result_hash') != EXPECTED_ENRICHMENT_HASH:
        raise Slice04ChainSelectionError('ENRICHMENT_RESULT_HASH_INVALID')
    if len(enrichment.get('transactions') or []) != 14 or len(enrichment.get('token_metadata') or []) != 3:
        raise Slice04ChainSelectionError('ENRICHMENT_SCOPE_INVALID')

    discovery = read_json(discovery_path, 'DISCOVERY')
    if discovery.get('schema') != 'tokenoskobi.product_slice_04.swap_pool_discovery.v1':
        raise Slice04ChainSelectionError('DISCOVERY_SCHEMA_INVALID')
    if discovery.get('status') != 'SWAP_POOL_DISCOVERY_COMPLETED':
        raise Slice04ChainSelectionError('DISCOVERY_STATUS_INVALID')
    if discovery.get('result_hash') != EXPECTED_DISCOVERY_HASH:
        raise Slice04ChainSelectionError('DISCOVERY_RESULT_HASH_INVALID')
    if len(discovery.get('events') or []) != 36:
        raise Slice04ChainSelectionError('DISCOVERY_EVENT_COUNT_INVALID')
    source = discovery.get('source')
    if not isinstance(source, dict) or source.get('database_sha256') != EXPECTED_DB_HASH:
        raise Slice04ChainSelectionError('DISCOVERY_DATABASE_HASH_INVALID')
    if source.get('candidate_enrichment_result_hash') != EXPECTED_ENRICHMENT_HASH:
        raise Slice04ChainSelectionError('DISCOVERY_ENRICHMENT_HASH_INVALID')

    allowlist_payload = read_json(allowlist_path, 'ALLOWLIST')
    allowlist = validate_allowlist(allowlist_payload)
    return enrichment, discovery, allowlist, allowlist_payload


def load_block_times(database_path: Path, tx_hashes: set[str]) -> dict[str, str]:
    resolved = database_path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file():
        raise Slice04ChainSelectionError('SOURCE_DATABASE_PATH_INVALID')
    if file_sha256(resolved) != EXPECTED_DB_HASH:
        raise Slice04ChainSelectionError('SOURCE_DATABASE_HASH_INVALID')
    uri = f'file:{resolved}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04ChainSelectionError('SOURCE_DATABASE_INTEGRITY_FAILED')
        placeholders = ','.join('?' for _ in tx_hashes)
        query = (
            f'SELECT tx_hash, MIN(block_time_utc) AS block_time_utc '
            f'FROM {SOURCE_TABLE} WHERE tx_hash IN ({placeholders}) GROUP BY tx_hash'
        )
        rows = conn.execute(query, sorted(tx_hashes)).fetchall()
    finally:
        conn.close()
    result = {normalize_hash(row['tx_hash']): str(row['block_time_utc']) for row in rows}
    if set(result) != tx_hashes:
        raise Slice04ChainSelectionError('SOURCE_BLOCK_TIME_COVERAGE_INVALID')
    return result


def event_raw_amounts(event: dict[str, Any]) -> tuple[int, int]:
    swap = event.get('swap')
    if not isinstance(swap, dict) or swap.get('direction_unambiguous') is not True:
        raise Slice04ChainSelectionError('SWAP_DIRECTION_NOT_UNAMBIGUOUS')
    input_side = swap.get('input_side')
    output_side = swap.get('output_side')
    if input_side not in {0, 1} or output_side not in {0, 1} or input_side == output_side:
        raise Slice04ChainSelectionError('SWAP_SIDE_INVALID')
    event_type = swap.get('event_type')
    if event_type == 'V2_SWAP':
        input_raw = int(str(swap[f'amount{input_side}_in_raw']))
        output_raw = int(str(swap[f'amount{output_side}_out_raw']))
    elif event_type in {'V3_SWAP', 'PANCAKE_V3_EXTENDED_SWAP'}:
        input_delta = int(str(swap[f'amount{input_side}_delta_raw']))
        output_delta = int(str(swap[f'amount{output_side}_delta_raw']))
        if input_delta <= 0 or output_delta >= 0:
            raise Slice04ChainSelectionError('V3_SWAP_DELTA_SIGN_INVALID')
        input_raw, output_raw = input_delta, -output_delta
    else:
        raise Slice04ChainSelectionError('SWAP_EVENT_TYPE_UNSUPPORTED')
    if input_raw <= 0 or output_raw <= 0:
        raise Slice04ChainSelectionError('SWAP_AMOUNT_INVALID')
    return input_raw, output_raw


def strict_actor_event_match(event: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]:
    swap = event.get('swap')
    if not isinstance(swap, dict):
        raise Slice04ChainSelectionError('EVENT_SWAP_MISSING')
    input_token = normalize_address(swap.get('input_token'))
    output_token = normalize_address(swap.get('output_token'))
    if input_token == output_token:
        raise Slice04ChainSelectionError('EVENT_TOKEN_DIRECTION_INVALID')

    actor_flow = transaction.get('actor_flow')
    rows = actor_flow.get('token_flows') if isinstance(actor_flow, dict) else None
    if not isinstance(rows, list):
        rows = []
    row_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        token = normalize_address(row.get('token_address'))
        if token in row_map:
            raise Slice04ChainSelectionError('ACTOR_FLOW_DUPLICATE_TOKEN')
        row_map[token] = row
    expected_pair = {input_token, output_token}
    full_pair_equality = set(row_map) == expected_pair
    input_row = row_map.get(input_token)
    output_row = row_map.get(output_token)
    direction_match = (
        full_pair_equality
        and input_row is not None
        and output_row is not None
        and input_row.get('direction') == 'OUT'
        and output_row.get('direction') == 'IN'
        and actor_flow.get('has_inflow') is True
        and actor_flow.get('has_outflow') is True
        and actor_flow.get('two_sided_actor_flow') is True
    )
    pool_input_raw, pool_output_raw = event_raw_amounts(event)
    actor_input_raw = abs(int(str(input_row.get('net_raw')))) if input_row else 0
    actor_output_raw = int(str(output_row.get('net_raw'))) if output_row else 0
    input_amount_exact = direction_match and actor_input_raw == pool_input_raw
    output_amount_exact = direction_match and actor_output_raw == pool_output_raw
    amount_exact = bool(input_amount_exact and output_amount_exact)
    return {
        'full_pair_equality': full_pair_equality,
        'direction_match': bool(direction_match),
        'input_amount_exact': bool(input_amount_exact),
        'output_amount_exact': bool(output_amount_exact),
        'strict_event_match': amount_exact,
        'actor_flow_tokens': sorted(row_map),
        'pool_input_raw': str(pool_input_raw),
        'pool_output_raw': str(pool_output_raw),
        'actor_input_raw': str(actor_input_raw),
        'actor_output_raw': str(actor_output_raw),
    }


def normalize_amount(raw: int, decimals: int) -> str:
    if raw < 0 or decimals < 0 or decimals > 36:
        raise Slice04ChainSelectionError('NORMALIZE_AMOUNT_INPUT_INVALID')
    if decimals == 0:
        return str(raw)
    text = str(raw).rjust(decimals + 1, '0')
    whole, fraction = text[:-decimals], text[-decimals:].rstrip('0')
    return whole if not fraction else f'{whole}.{fraction}'


def build_event_records(
    enrichment: dict[str, Any],
    discovery: dict[str, Any],
    allowlist: dict[str, dict[str, Any]],
    block_times: dict[str, str],
) -> list[dict[str, Any]]:
    tx_map = {normalize_hash(item['tx_hash']): item for item in enrichment['transactions']}
    metadata = {normalize_address(item['token_address']): item for item in enrichment['token_metadata']}
    tx_event_counts = Counter(normalize_hash(item['tx_hash']) for item in discovery['events'])
    records: list[dict[str, Any]] = []
    for item in discovery['events']:
        tx_hash = normalize_hash(item['tx_hash'])
        identity = item.get('pool_identity')
        swap = item.get('swap')
        if not isinstance(identity, dict) or not isinstance(swap, dict):
            raise Slice04ChainSelectionError('DISCOVERY_EVENT_SHAPE_INVALID')
        factory = normalize_address(identity.get('factory'))
        event_type = str(swap.get('event_type') or '')
        protocol = allowlist.get(factory)
        protocol_verified = bool(protocol and event_type in protocol.get('allowed_event_types', []))
        match = strict_actor_event_match(item, tx_map[tx_hash])
        input_token = normalize_address(swap.get('input_token'))
        output_token = normalize_address(swap.get('output_token'))
        input_raw, output_raw = event_raw_amounts(item)
        input_meta, output_meta = metadata.get(input_token), metadata.get(output_token)
        tracked_pair_complete = input_meta is not None and output_meta is not None
        records.append({
            'tx_hash': tx_hash,
            'block_number': int(item['block_number']),
            'block_time_utc': block_times[tx_hash],
            'receipt_log_index': int(item['receipt_log_index']),
            'actor': normalize_address(item['actor']),
            'transaction_target': normalize_address(item['transaction_target']),
            'transaction_swap_event_count': tx_event_counts[tx_hash],
            'pool_address': normalize_address(identity['pool_address']),
            'factory': factory,
            'event_type': event_type,
            'protocol_verified': protocol_verified,
            'protocol_id': protocol.get('protocol_id') if protocol_verified else 'UNVERIFIED',
            'protocol_name': protocol.get('protocol_name') if protocol_verified else 'UNVERIFIED',
            'protocol_version': protocol.get('version') if protocol_verified else 'UNVERIFIED',
            'input_token': input_token,
            'output_token': output_token,
            'input_symbol': str(input_meta.get('symbol')) if input_meta else 'UNKNOWN',
            'output_symbol': str(output_meta.get('symbol')) if output_meta else 'UNKNOWN',
            'input_raw': str(input_raw),
            'output_raw': str(output_raw),
            'input_normalized': normalize_amount(input_raw, int(input_meta['decimals'])) if input_meta else None,
            'output_normalized': normalize_amount(output_raw, int(output_meta['decimals'])) if output_meta else None,
            'tracked_pair_complete': tracked_pair_complete,
            'strict_actor_event_match': match,
            'strict_verified_event': bool(protocol_verified and tracked_pair_complete and match['strict_event_match']),
            'gas_cost_wei': str(tx_map[tx_hash].get('gas_cost_wei') or ''),
            'receipt_evidence_hash': str(item.get('receipt_evidence_hash') or ''),
            'log_evidence_hash': str(item.get('log_evidence_hash') or ''),
        })
    return records


def build_chain_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    strict = [item for item in records if item['strict_verified_event']]
    by_key: dict[tuple[str, tuple[str, str]], list[dict[str, Any]]] = defaultdict(list)
    for item in strict:
        pair = tuple(sorted((item['input_token'], item['output_token'])))
        by_key[(item['actor'], pair)].append(item)
    candidates: list[dict[str, Any]] = []
    for (actor, pair), items in by_key.items():
        ordered = sorted(
            items,
            key=lambda row: (
                row['block_number'],
                row.get('transaction_index', -1),
                row['receipt_log_index'],
                row['tx_hash'],
            ),
        )
        for index, opening in enumerate(ordered):
            for closing in ordered[index + 1:]:
                if opening['tx_hash'] == closing['tx_hash']:
                    continue
                opposite = (
                    opening['input_token'] == closing['output_token']
                    and opening['output_token'] == closing['input_token']
                )
                if not opposite:
                    continue
                same_pool = opening['pool_address'] == closing['pool_address']
                same_protocol = opening['protocol_id'] == closing['protocol_id']
                clean_single_swap_transactions = (
                    opening['transaction_swap_event_count'] == 1
                    and closing['transaction_swap_event_count'] == 1
                )
                opening_position = (
                    opening['block_number'],
                    opening.get('transaction_index', -1),
                )
                closing_position = (
                    closing['block_number'],
                    closing.get('transaction_index', -1),
                )
                chronology_strict = (
                    opening['block_number'] < closing['block_number']
                    or (
                        opening['block_number'] == closing['block_number']
                        and isinstance(opening.get('transaction_index'), int)
                        and isinstance(closing.get('transaction_index'), int)
                        and opening['transaction_index'] < closing['transaction_index']
                    )
                )
                blockers: list[str] = []
                if not chronology_strict:
                    blockers.append('CHRONOLOGY_NOT_STRICT')
                if not same_pool:
                    blockers.append('POOL_CHANGED')
                if not same_protocol:
                    blockers.append('PROTOCOL_CHANGED')
                if not clean_single_swap_transactions:
                    blockers.append('MULTI_SWAP_TRANSACTION_PRESENT')
                confirmed = not blockers
                score = (
                    100 * int(same_pool)
                    + 50 * int(same_protocol)
                    + 100 * int(clean_single_swap_transactions)
                    - (closing['block_number'] - opening['block_number']) / 1_000_000
                )
                candidates.append({
                    'actor': actor,
                    'token_pair': list(pair),
                    'opening_event': opening,
                    'closing_event': closing,
                    'same_pool': same_pool,
                    'same_protocol': same_protocol,
                    'clean_single_swap_transactions': clean_single_swap_transactions,
                    'block_distance': closing['block_number'] - opening['block_number'],
                    'closed_loop_confirmed': confirmed,
                    'blockers': blockers,
                    'selection_score': round(score, 9),
                })
    return sorted(
        candidates,
        key=lambda row: (
            not row['closed_loop_confirmed'],
            -row['selection_score'],
            row['block_distance'],
            row['opening_event']['tx_hash'],
            row['closing_event']['tx_hash'],
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
    enrichment_path: Path,
    discovery_path: Path,
    allowlist_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    enrichment, discovery, allowlist, allowlist_payload = load_inputs(
        enrichment_path, discovery_path, allowlist_path
    )
    tx_hashes = {normalize_hash(item['tx_hash']) for item in enrichment['transactions']}
    block_times = load_block_times(database_path, tx_hashes)
    records = build_event_records(enrichment, discovery, allowlist, block_times)
    candidates = build_chain_candidates(records)
    confirmed = [item for item in candidates if item['closed_loop_confirmed']]
    strict_records = [item for item in records if item['strict_verified_event']]
    protocol_counts = Counter(item['protocol_id'] for item in records if item['protocol_verified'])
    unknown_factories = sorted({item['factory'] for item in records if not item['protocol_verified']})
    top_candidate = candidates[0] if candidates else None
    next_step = (
        'EXECUTION_PRICE_GAS_FEE_AND_PERFORMANCE_RECONSTRUCTION'
        if confirmed
        else 'TARGETED_SAME_ACTOR_HISTORY_ENRICHMENT_FOR_CLOSED_LOOP'
    )
    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.first_swap_chain_selection.v1',
        'generated_at_utc': iso_now(),
        'status': 'STRICT_FACTORY_AND_SWAP_CHAIN_SELECTION_COMPLETED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {
            'database_path': str(database_path.resolve()),
            'database_sha256': file_sha256(database_path),
            'candidate_enrichment_result_hash': enrichment['result_hash'],
            'swap_pool_discovery_result_hash': discovery['result_hash'],
            'factory_allowlist_path': str(allowlist_path),
            'factory_allowlist_sha256': file_sha256(allowlist_path),
            'factory_allowlist_hash': canonical_hash(allowlist_payload),
        },
        'factory_allowlist': allowlist_payload,
        'event_records': records,
        'chain_candidates': candidates,
        'top_candidate': top_candidate,
        'summary': {
            'recognized_swap_event_count': len(records),
            'officially_allowlisted_factory_count': len(allowlist),
            'protocol_verified_event_count': sum(int(item['protocol_verified']) for item in records),
            'strict_pair_direction_amount_event_count': len(strict_records),
            'opposite_direction_chain_candidate_count': len(candidates),
            'clean_single_swap_closed_loop_count': len(confirmed),
            'protocol_event_counts': dict(sorted(protocol_counts.items())),
            'unverified_factory_count': len(unknown_factories),
            'unverified_factories': unknown_factories,
            'router_identity_verified': False,
            'closed_loop_confirmed': bool(confirmed),
            'first_chain_selected': top_candidate is not None,
            'next_safe_step': next_step,
        },
    }
    payload['result_hash'] = canonical_hash(payload)
    atomic_write_json(output_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=DEFAULT_DB)
    parser.add_argument('--enrichment', type=Path, default=DEFAULT_ENRICHMENT)
    parser.add_argument('--discovery', type=Path, default=DEFAULT_DISCOVERY)
    parser.add_argument('--allowlist', type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.database, args.enrichment, args.discovery, args.allowlist, args.output)
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'PROTOCOL_VERIFIED_EVENT_COUNT={summary["protocol_verified_event_count"]}')
    print(f'STRICT_PAIR_DIRECTION_AMOUNT_EVENT_COUNT={summary["strict_pair_direction_amount_event_count"]}')
    print(f'OPPOSITE_DIRECTION_CHAIN_CANDIDATE_COUNT={summary["opposite_direction_chain_candidate_count"]}')
    print(f'CLEAN_SINGLE_SWAP_CLOSED_LOOP_COUNT={summary["clean_single_swap_closed_loop_count"]}')
    print('PROTOCOL_EVENT_COUNTS=' + json.dumps(summary['protocol_event_counts'], sort_keys=True, separators=(',', ':')))
    print('UNVERIFIED_FACTORIES=' + json.dumps(summary['unverified_factories'], separators=(',', ':')))
    top = result.get('top_candidate')
    if top:
        opening, closing = top['opening_event'], top['closing_event']
        print(
            'TOP_CHAIN_CANDIDATE='
            f'actor:{top["actor"]},'
            f'open_tx:{opening["tx_hash"]},open:{opening["input_symbol"]}->{opening["output_symbol"]},'
            f'close_tx:{closing["tx_hash"]},close:{closing["input_symbol"]}->{closing["output_symbol"]},'
            f'pool:{opening["pool_address"]},same_pool:{str(top["same_pool"]).lower()},'
            f'same_protocol:{str(top["same_protocol"]).lower()},'
            f'clean_single_swap:{str(top["clean_single_swap_transactions"]).lower()},'
            f'confirmed:{str(top["closed_loop_confirmed"]).lower()},'
            f'blockers:{"|".join(top["blockers"]) or "NONE"}'
        )
    else:
        print('TOP_CHAIN_CANDIDATE=NONE')
    print(f'RESULT_HASH={result["result_hash"]}')
    print(f'CLOSED_LOOP_CONFIRMED={str(summary["closed_loop_confirmed"]).lower()}')
    print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
