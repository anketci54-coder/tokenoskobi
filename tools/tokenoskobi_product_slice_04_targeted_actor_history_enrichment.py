#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
DEFAULT_DB = ROOT / 'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
DEFAULT_PROVIDER = ROOT / 'config/era63e_always_on_market_runtime_v1.json'
DEFAULT_ENRICHMENT = Path('/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json')
DEFAULT_SELECTION = Path('/var/lib/tokenoskobi-product-slice-04/first_swap_chain_selection_v1.json')
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/targeted_actor_history_enrichment_v1.json')
SOURCE_TABLE = 'era64i_historical_wallet_transfer_staging_v1'
RECEIPT_TABLE = 'era64j_historical_receipt_cost_enrichment_v1'
EXPECTED_DB_HASH = '99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_ENRICHMENT_HASH = '34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
EXPECTED_SELECTION_HASH = 'e19adf42373e643a27c4c8f23815672ab42598af012d887a9a17398e92f19c61'
MAX_TARGET_ACTORS = 10
MAX_TARGET_TRANSACTIONS = 80
MAX_ROUND_TRIP_PAIRS = 100
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')
ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')
HEX_RE = re.compile(r'^0x(?:[0-9a-f]{2})*$')
ZERO = '0x0000000000000000000000000000000000000000'

AUTHORITY = {
    'network_access': True,
    'network_mode': 'READ_ONLY_ALLOWLISTED_BSC_RPC_ETH_GET_TRANSACTION_BY_HASH_ONLY',
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


class Slice04TargetedHistoryError(RuntimeError):
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
        raise Slice04TargetedHistoryError('INVALID_TRANSACTION_HASH')
    return text


def normalize_address(value: Any, *, allow_empty: bool = False) -> str:
    text = str(value or '').strip().lower()
    if allow_empty and text == '':
        return ''
    if ADDRESS_RE.fullmatch(text) is None:
        raise Slice04TargetedHistoryError('INVALID_EVM_ADDRESS')
    return text


def validate_hex_data(value: Any, field: str) -> str:
    text = str(value or '').strip().lower()
    if HEX_RE.fullmatch(text) is None:
        raise Slice04TargetedHistoryError(f'{field}:INVALID_HEX_DATA')
    return text


def parse_hex_int(value: Any, field: str) -> int:
    text = str(value or '').strip().lower()
    if not text.startswith('0x'):
        raise Slice04TargetedHistoryError(f'{field}:NOT_HEX')
    try:
        number = int(text, 16)
    except ValueError as exc:
        raise Slice04TargetedHistoryError(f'{field}:INVALID_HEX') from exc
    if number < 0:
        raise Slice04TargetedHistoryError(f'{field}:NEGATIVE')
    return number


def read_json(path: Path, code: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise Slice04TargetedHistoryError(f'{code}_MISSING')
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise Slice04TargetedHistoryError(f'{code}_INVALID_JSON') from exc
    if not isinstance(payload, dict):
        raise Slice04TargetedHistoryError(f'{code}_NOT_OBJECT')
    return payload


def validate_inputs(enrichment_path: Path, selection_path: Path) -> dict[str, dict[str, Any]]:
    enrichment = read_json(enrichment_path, 'ENRICHMENT')
    if enrichment.get('schema') != 'tokenoskobi.product_slice_04.candidate_enrichment.v1':
        raise Slice04TargetedHistoryError('ENRICHMENT_SCHEMA_INVALID')
    if enrichment.get('status') != 'CANDIDATE_INPUT_AND_TOKEN_METADATA_ENRICHMENT_VERIFIED_WITH_ARCHIVE_FALLBACK_POLICY':
        raise Slice04TargetedHistoryError('ENRICHMENT_STATUS_INVALID')
    if enrichment.get('result_hash') != EXPECTED_ENRICHMENT_HASH:
        raise Slice04TargetedHistoryError('ENRICHMENT_RESULT_HASH_INVALID')
    metadata = enrichment.get('token_metadata')
    if not isinstance(metadata, list) or len(metadata) != 3:
        raise Slice04TargetedHistoryError('ENRICHMENT_METADATA_SCOPE_INVALID')
    metadata_map: dict[str, dict[str, Any]] = {}
    for item in metadata:
        if not isinstance(item, dict):
            raise Slice04TargetedHistoryError('ENRICHMENT_METADATA_NOT_OBJECT')
        token = normalize_address(item.get('token_address'))
        decimals = int(item.get('decimals'))
        if decimals < 0 or decimals > 36 or token in metadata_map:
            raise Slice04TargetedHistoryError('ENRICHMENT_METADATA_INVALID')
        metadata_map[token] = dict(item)

    selection = read_json(selection_path, 'SELECTION')
    if selection.get('schema') != 'tokenoskobi.product_slice_04.first_swap_chain_selection.v1':
        raise Slice04TargetedHistoryError('SELECTION_SCHEMA_INVALID')
    if selection.get('status') != 'STRICT_FACTORY_AND_SWAP_CHAIN_SELECTION_COMPLETED':
        raise Slice04TargetedHistoryError('SELECTION_STATUS_INVALID')
    if selection.get('result_hash') != EXPECTED_SELECTION_HASH:
        raise Slice04TargetedHistoryError('SELECTION_RESULT_HASH_INVALID')
    summary = selection.get('summary')
    if not isinstance(summary, dict):
        raise Slice04TargetedHistoryError('SELECTION_SUMMARY_MISSING')
    if summary.get('closed_loop_confirmed') is not False:
        raise Slice04TargetedHistoryError('SELECTION_ALREADY_CLOSED_LOOP')
    if summary.get('next_safe_step') != 'TARGETED_SAME_ACTOR_HISTORY_ENRICHMENT_FOR_CLOSED_LOOP':
        raise Slice04TargetedHistoryError('SELECTION_NEXT_STEP_INVALID')
    return metadata_map


def validate_provider_config(config: dict[str, Any]) -> tuple[list[str], set[str], float, int]:
    if config.get('schema') != 'tokenoskobi.era63e.always_on_market_runtime_config.v1':
        raise Slice04TargetedHistoryError('PROVIDER_SCHEMA_INVALID')
    rpc = config.get('rpc')
    if not isinstance(rpc, dict) or int(rpc.get('chain_id', 0)) != 56:
        raise Slice04TargetedHistoryError('PROVIDER_CHAIN_INVALID')
    endpoints = [str(item).rstrip('/') for item in rpc.get('endpoints') or []]
    allowed_hosts = {str(item).lower() for item in rpc.get('allowed_hosts') or []}
    if len(endpoints) < 2 or len(allowed_hosts) < 2:
        raise Slice04TargetedHistoryError('PROVIDER_REDUNDANCY_INSUFFICIENT')
    for endpoint in endpoints:
        parsed = urllib.parse.urlparse(endpoint)
        if parsed.scheme != 'https' or str(parsed.hostname or '').lower() not in allowed_hosts:
            raise Slice04TargetedHistoryError('PROVIDER_ENDPOINT_NOT_ALLOWLISTED_HTTPS')
    timeout = float(rpc.get('request_timeout_sec', 8))
    retries = int(rpc.get('retries_per_endpoint', 1))
    if timeout < 2 or timeout > 30 or retries < 0 or retries > 2:
        raise Slice04TargetedHistoryError('PROVIDER_LIMITS_INVALID')
    return endpoints, allowed_hosts, timeout, retries


class RpcClient:
    ALLOWED_METHODS = {'eth_chainId', 'eth_getTransactionByHash'}

    def __init__(self, config: dict[str, Any], *, maximum_requests: int = 200, maximum_seconds: float = 300.0):
        self.endpoints, self.allowed_hosts, self.timeout, self.retries = validate_provider_config(config)
        self.maximum_requests = maximum_requests
        self.maximum_seconds = maximum_seconds
        self.started = time.monotonic()
        self.request_count = 0
        self.endpoint_index = 0
        self.last_endpoint_host = ''
        self.errors: list[str] = []

    def call(self, method: str, params: list[Any]) -> Any:
        if method not in self.ALLOWED_METHODS:
            raise Slice04TargetedHistoryError(f'RPC_METHOD_NOT_ALLOWLISTED:{method}')
        if self.request_count >= self.maximum_requests:
            raise Slice04TargetedHistoryError('RPC_REQUEST_BUDGET_EXCEEDED')
        if time.monotonic() - self.started > self.maximum_seconds:
            raise Slice04TargetedHistoryError('RPC_RUNTIME_BUDGET_EXCEEDED')
        last_error = ''
        count = len(self.endpoints)
        for offset in range(count):
            endpoint = self.endpoints[(self.endpoint_index + offset) % count]
            host = str(urllib.parse.urlparse(endpoint).hostname or '').lower()
            if host not in self.allowed_hosts:
                continue
            for attempt in range(self.retries + 1):
                if self.request_count >= self.maximum_requests:
                    raise Slice04TargetedHistoryError('RPC_REQUEST_BUDGET_EXCEEDED')
                self.request_count += 1
                body = json.dumps({'jsonrpc': '2.0', 'id': self.request_count, 'method': method, 'params': params}, separators=(',', ':')).encode('utf-8')
                request = urllib.request.Request(endpoint, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Tokenoskobi-Product-Slice-04/1.0 targeted-actor-history'}, method='POST')
                try:
                    with urllib.request.urlopen(request, timeout=self.timeout) as response:
                        payload = json.loads(response.read().decode('utf-8'))
                    if not isinstance(payload, dict) or payload.get('error') is not None or 'result' not in payload:
                        raise Slice04TargetedHistoryError(f'RPC_RESPONSE_INVALID:{payload.get("error") if isinstance(payload, dict) else "NOT_OBJECT"}')
                    self.endpoint_index = (self.endpoint_index + offset + 1) % count
                    self.last_endpoint_host = host
                    return payload['result']
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError, Slice04TargetedHistoryError) as exc:
                    last_error = f'{type(exc).__name__}:{exc}'
                    self.errors.append(f'{host}:{method}:{last_error}')
                    if attempt < self.retries:
                        time.sleep(min(0.25 * (2 ** attempt), 1.0))
        raise Slice04TargetedHistoryError(f'ALL_RPC_ENDPOINTS_FAILED:{method}:{last_error}')


def load_database(database_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    resolved = database_path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file() or file_sha256(resolved) != EXPECTED_DB_HASH:
        raise Slice04TargetedHistoryError('SOURCE_DATABASE_INVALID')
    uri = f'file:{resolved}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04TargetedHistoryError('SOURCE_DATABASE_INTEGRITY_FAILED')
        tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if SOURCE_TABLE not in tables or RECEIPT_TABLE not in tables:
            raise Slice04TargetedHistoryError('SOURCE_TABLES_MISSING')
        source_rows = [dict(row) for row in conn.execute(f'''SELECT event_uid,token_address,from_address,to_address,amount_raw,tx_hash,log_index,block_number,block_time_utc,evidence_hash FROM {SOURCE_TABLE} ORDER BY block_number,tx_hash,log_index''')]
        receipt_rows = [dict(row) for row in conn.execute(f'''SELECT tx_hash,block_number,transaction_index,receipt_status,gas_used,effective_gas_price_wei,gas_cost_wei,tx_from_address,tx_to_address,evidence_hash,raw_receipt_json,raw_transaction_json FROM {RECEIPT_TABLE} ORDER BY block_number,transaction_index,tx_hash''')]
    finally:
        conn.close()
    if len(source_rows) != 367 or len(receipt_rows) != 277:
        raise Slice04TargetedHistoryError('SOURCE_COUNTS_CHANGED')
    return source_rows, receipt_rows


def compute_actor_net(events: list[dict[str, Any]], actor: str) -> dict[str, int]:
    net: dict[str, int] = defaultdict(int)
    for event in events:
        token = normalize_address(event.get('token_address'))
        amount = int(str(event.get('amount_raw')))
        if amount <= 0:
            raise Slice04TargetedHistoryError('SOURCE_AMOUNT_INVALID')
        if normalize_address(event.get('from_address')) == actor:
            net[token] -= amount
        if normalize_address(event.get('to_address')) == actor:
            net[token] += amount
    return {token: amount for token, amount in net.items() if amount != 0}


def select_target_scope(source_rows: list[dict[str, Any]], receipt_rows: list[dict[str, Any]]) -> dict[str, Any]:
    events_by_tx: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        events_by_tx[normalize_hash(row.get('tx_hash'))].append(row)
    receipts_by_tx = {normalize_hash(row.get('tx_hash')): row for row in receipt_rows}
    if len(receipts_by_tx) != len(receipt_rows):
        raise Slice04TargetedHistoryError('RECEIPT_DUPLICATE_TRANSACTION')

    tx_records: list[dict[str, Any]] = []
    actor_token_series: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for tx_hash, events in events_by_tx.items():
        receipt = receipts_by_tx.get(tx_hash)
        if not receipt:
            raise Slice04TargetedHistoryError('SOURCE_RECEIPT_JOIN_INCOMPLETE')
        actor = normalize_address(receipt.get('tx_from_address'))
        if actor == ZERO:
            continue
        net = compute_actor_net(events, actor)
        record = {
            'tx_hash': tx_hash,
            'actor': actor,
            'tx_to': normalize_address(receipt.get('tx_to_address'), allow_empty=True),
            'block_number': int(receipt.get('block_number')),
            'transaction_index': int(receipt.get('transaction_index')),
            'block_time_utc': str(events[0].get('block_time_utc')),
            'net_by_token': {token: str(amount) for token, amount in sorted(net.items())},
        }
        tx_records.append(record)
        for token, amount in net.items():
            actor_token_series[(actor, token)].append({**record, 'net_raw': amount})

    pairs: list[dict[str, Any]] = []
    for (actor, token), rows in sorted(actor_token_series.items()):
        ordered = sorted(rows, key=lambda item: (item['block_number'], item['transaction_index'], item['tx_hash']))
        for index, first in enumerate(ordered):
            for second in ordered[index + 1:]:
                if (first['net_raw'] > 0 > second['net_raw']) or (first['net_raw'] < 0 < second['net_raw']):
                    pairs.append({
                        'actor': actor,
                        'token_address': token,
                        'first_tx_hash': first['tx_hash'],
                        'first_block_number': first['block_number'],
                        'first_direction': 'IN' if first['net_raw'] > 0 else 'OUT',
                        'first_net_raw': str(first['net_raw']),
                        'second_tx_hash': second['tx_hash'],
                        'second_block_number': second['block_number'],
                        'second_direction': 'IN' if second['net_raw'] > 0 else 'OUT',
                        'second_net_raw': str(second['net_raw']),
                        'block_distance': second['block_number'] - first['block_number'],
                    })
                    if len(pairs) > MAX_ROUND_TRIP_PAIRS:
                        raise Slice04TargetedHistoryError('ROUND_TRIP_PAIR_SCOPE_EXCEEDED')

    actors = sorted({item['actor'] for item in pairs})
    if not actors:
        raise Slice04TargetedHistoryError('NO_TARGET_ACTOR_FOUND')
    if len(actors) > MAX_TARGET_ACTORS:
        raise Slice04TargetedHistoryError('TARGET_ACTOR_SCOPE_EXCEEDED')
    actor_set = set(actors)
    transactions = sorted(
        [item for item in tx_records if item['actor'] in actor_set],
        key=lambda item: (item['block_number'], item['transaction_index'], item['tx_hash']),
    )
    if not transactions or len(transactions) > MAX_TARGET_TRANSACTIONS:
        raise Slice04TargetedHistoryError('TARGET_TRANSACTION_SCOPE_INVALID')
    return {
        'target_actors': actors,
        'round_trip_pairs': pairs,
        'transactions': transactions,
        'events_by_tx': events_by_tx,
        'receipts_by_tx': receipts_by_tx,
    }


def raw_transaction_from_database(value: Any) -> dict[str, Any] | None:
    text = str(value or '').strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) and payload else None


def validate_transaction(raw: dict[str, Any], tx_hash: str, receipt: dict[str, Any]) -> dict[str, Any]:
    if normalize_hash(raw.get('hash')) != tx_hash:
        raise Slice04TargetedHistoryError(f'TRANSACTION_IDENTITY_INVALID:{tx_hash}')
    block_number = parse_hex_int(raw.get('blockNumber'), 'transaction.blockNumber')
    if block_number != int(receipt.get('block_number')):
        raise Slice04TargetedHistoryError(f'TRANSACTION_BLOCK_MISMATCH:{tx_hash}')
    actor = normalize_address(raw.get('from'))
    tx_to = normalize_address(raw.get('to'), allow_empty=True)
    if actor != normalize_address(receipt.get('tx_from_address')):
        raise Slice04TargetedHistoryError(f'TRANSACTION_ACTOR_MISMATCH:{tx_hash}')
    if tx_to != normalize_address(receipt.get('tx_to_address'), allow_empty=True):
        raise Slice04TargetedHistoryError(f'TRANSACTION_TARGET_MISMATCH:{tx_hash}')
    input_data = validate_hex_data(raw.get('input') or '0x', 'transaction.input')
    if input_data != '0x' and len(input_data) < 10:
        raise Slice04TargetedHistoryError(f'TRANSACTION_INPUT_TOO_SHORT:{tx_hash}')
    return {
        'tx_hash': tx_hash,
        'block_number': block_number,
        'transaction_index': parse_hex_int(raw.get('transactionIndex'), 'transaction.transactionIndex'),
        'actor': actor,
        'tx_to': tx_to,
        'value_wei': str(parse_hex_int(raw.get('value') or '0x0', 'transaction.value')),
        'gas_limit': str(parse_hex_int(raw.get('gas') or '0x0', 'transaction.gas')),
        'gas_price_wei': str(parse_hex_int(raw.get('gasPrice') or '0x0', 'transaction.gasPrice')),
        'nonce': parse_hex_int(raw.get('nonce') or '0x0', 'transaction.nonce'),
        'input': input_data,
        'selector': input_data[:10] if len(input_data) >= 10 else '0x',
        'input_bytes': max(0, (len(input_data) - 2) // 2),
        'transaction_evidence_hash': canonical_hash(raw),
    }


def normalize_amount(raw: int, decimals: int) -> str:
    sign = '-' if raw < 0 else ''
    value = str(abs(raw)).rjust(decimals + 1, '0') if decimals else str(abs(raw))
    if decimals:
        whole, fraction = value[:-decimals], value[-decimals:].rstrip('0')
        value = whole if not fraction else f'{whole}.{fraction}'
    return sign + value


def build_actor_flow(actor: str, events: list[dict[str, Any]], metadata_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    net = compute_actor_net(events, actor)
    rows: list[dict[str, Any]] = []
    for token, amount in sorted(net.items()):
        metadata = metadata_map.get(token)
        if not metadata:
            raise Slice04TargetedHistoryError(f'TOKEN_METADATA_MISSING:{token}')
        decimals = int(metadata['decimals'])
        rows.append({
            'token_address': token,
            'symbol': str(metadata.get('symbol') or 'UNKNOWN'),
            'decimals': decimals,
            'net_raw': str(amount),
            'net_normalized': normalize_amount(amount, decimals),
            'direction': 'IN' if amount > 0 else 'OUT',
        })
    directions = {item['direction'] for item in rows}
    return {
        'actor': actor,
        'token_flows': rows,
        'has_inflow': 'IN' in directions,
        'has_outflow': 'OUT' in directions,
        'two_sided_actor_flow': directions == {'IN', 'OUT'},
        'flow_hash': canonical_hash(rows),
    }


def summarize_receipt_logs(value: Any) -> dict[str, Any]:
    try:
        receipt = json.loads(str(value or ''))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Slice04TargetedHistoryError('RECEIPT_JSON_INVALID') from exc
    logs = receipt.get('logs') if isinstance(receipt, dict) else None
    if not isinstance(logs, list):
        raise Slice04TargetedHistoryError('RECEIPT_LOGS_INVALID')
    topic0_counts: Counter[str] = Counter()
    address_counts: Counter[str] = Counter()
    for log in logs:
        if not isinstance(log, dict):
            continue
        address_counts[normalize_address(log.get('address'))] += 1
        topics = log.get('topics')
        if isinstance(topics, list) and topics:
            topic0_counts[normalize_hash(topics[0])] += 1
    core = {'log_address_counts': dict(sorted(address_counts.items())), 'topic0_counts': dict(sorted(topic0_counts.items()))}
    return {'log_count': sum(address_counts.values()), **core, 'log_summary_hash': canonical_hash(core)}


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    os.chmod(temp, 0o600)
    json.loads(temp.read_text(encoding='utf-8'))
    temp.replace(path)
    os.chmod(path, 0o600)


def run(database_path: Path, provider_path: Path, enrichment_path: Path, selection_path: Path, output_path: Path) -> dict[str, Any]:
    started = time.monotonic()
    metadata_map = validate_inputs(enrichment_path, selection_path)
    source_rows, receipt_rows = load_database(database_path)
    scope = select_target_scope(source_rows, receipt_rows)
    provider = read_json(provider_path, 'PROVIDER')
    client = RpcClient(provider)
    if parse_hex_int(client.call('eth_chainId', []), 'eth_chainId') != 56:
        raise Slice04TargetedHistoryError('RPC_CHAIN_ID_MISMATCH')

    transactions: list[dict[str, Any]] = []
    db_raw_count = 0
    rpc_raw_count = 0
    selector_counts: Counter[str] = Counter()
    tx_to_counts: Counter[str] = Counter()
    for item in scope['transactions']:
        tx_hash = item['tx_hash']
        receipt = scope['receipts_by_tx'][tx_hash]
        raw = raw_transaction_from_database(receipt.get('raw_transaction_json'))
        source_mode = 'DATABASE_RAW_TRANSACTION_JSON'
        provider_host = ''
        if raw is None:
            raw = client.call('eth_getTransactionByHash', [tx_hash])
            if not isinstance(raw, dict):
                raise Slice04TargetedHistoryError(f'RPC_TRANSACTION_NOT_OBJECT:{tx_hash}')
            source_mode = 'ALLOWLISTED_RPC_ETH_GET_TRANSACTION_BY_HASH'
            provider_host = client.last_endpoint_host
            rpc_raw_count += 1
        else:
            db_raw_count += 1
        tx = validate_transaction(raw, tx_hash, receipt)
        if tx['actor'] != item['actor']:
            raise Slice04TargetedHistoryError('TARGET_SCOPE_ACTOR_DRIFT')
        flow = build_actor_flow(tx['actor'], scope['events_by_tx'][tx_hash], metadata_map)
        selector_counts[tx['selector']] += 1
        tx_to_counts[tx['tx_to'] or 'CONTRACT_CREATION'] += 1
        transactions.append({
            **tx,
            'raw_transaction_source': source_mode,
            'rpc_provider_host': provider_host,
            'block_time_utc': item['block_time_utc'],
            'receipt_status': int(receipt['receipt_status']),
            'gas_used': str(receipt['gas_used']),
            'effective_gas_price_wei': str(receipt['effective_gas_price_wei']),
            'gas_cost_wei': str(receipt['gas_cost_wei']),
            'receipt_evidence_hash': str(receipt['evidence_hash']),
            'source_event_count': len(scope['events_by_tx'][tx_hash]),
            'source_event_hashes': sorted(str(row['evidence_hash']) for row in scope['events_by_tx'][tx_hash]),
            'actor_flow': flow,
            'receipt_log_summary': summarize_receipt_logs(receipt['raw_receipt_json']),
        })

    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.targeted_actor_history_enrichment.v1',
        'generated_at_utc': iso_now(),
        'status': 'TARGETED_SAME_ACTOR_HISTORY_ENRICHMENT_COMPLETED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {
            'database_path': str(database_path.resolve()),
            'database_sha256': file_sha256(database_path),
            'candidate_enrichment_result_hash': EXPECTED_ENRICHMENT_HASH,
            'first_swap_chain_selection_result_hash': EXPECTED_SELECTION_HASH,
            'source_event_count': len(source_rows),
            'source_transaction_count': len(receipt_rows),
        },
        'scope_policy': {
            'selection_rule': 'SAME_ACTOR_SAME_TRACKED_TOKEN_OPPOSITE_NET_DIRECTIONS_ACROSS_DISTINCT_TRANSACTIONS',
            'maximum_target_actors': MAX_TARGET_ACTORS,
            'maximum_target_transactions': MAX_TARGET_TRANSACTIONS,
            'maximum_round_trip_pairs': MAX_ROUND_TRIP_PAIRS,
            'all_target_transactions_must_be_in_immutable_source_database': True,
            'network_fetch_only_when_database_raw_transaction_missing': True,
        },
        'target_actors': scope['target_actors'],
        'round_trip_pairs': scope['round_trip_pairs'],
        'transactions': transactions,
        'rpc': {
            'request_count': client.request_count,
            'error_count': len(client.errors),
            'errors': client.errors[-30:],
            'database_raw_transaction_count': db_raw_count,
            'rpc_raw_transaction_count': rpc_raw_count,
        },
        'summary': {
            'target_actor_count': len(scope['target_actors']),
            'round_trip_pair_count': len(scope['round_trip_pairs']),
            'target_transaction_count': len(transactions),
            'transaction_input_coverage': len(transactions),
            'two_sided_actor_flow_transaction_count': sum(int(item['actor_flow']['two_sided_actor_flow']) for item in transactions),
            'selector_counts': dict(sorted(selector_counts.items())),
            'tx_to_counts': dict(sorted(tx_to_counts.items())),
            'swap_direction_classified': False,
            'protocol_identity_verified': False,
            'closed_loop_confirmed': False,
            'next_safe_step': 'TARGETED_SWAP_POOL_DECODE_AND_STRICT_CLOSED_LOOP_RESELECTION',
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
    parser.add_argument('--selection', type=Path, default=DEFAULT_SELECTION)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.database, args.provider, args.enrichment, args.selection, args.output)
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'TARGET_ACTOR_COUNT={summary["target_actor_count"]}')
    print(f'ROUND_TRIP_PAIR_COUNT={summary["round_trip_pair_count"]}')
    print(f'TARGET_TRANSACTION_COUNT={summary["target_transaction_count"]}')
    print(f'TRANSACTION_INPUT_COVERAGE={summary["transaction_input_coverage"]}_OF_{summary["target_transaction_count"]}')
    print(f'DATABASE_RAW_TRANSACTION_COUNT={result["rpc"]["database_raw_transaction_count"]}')
    print(f'RPC_RAW_TRANSACTION_COUNT={result["rpc"]["rpc_raw_transaction_count"]}')
    print(f'RPC_REQUEST_COUNT={result["rpc"]["request_count"]}')
    print(f'RPC_ERROR_COUNT={result["rpc"]["error_count"]}')
    print('TARGET_ACTORS=' + json.dumps(result['target_actors'], separators=(',', ':')))
    for index, pair in enumerate(result['round_trip_pairs'], start=1):
        print(f'ROUND_TRIP_PAIR_{index}=actor:{pair["actor"]},token:{pair["token_address"]},first_tx:{pair["first_tx_hash"]},first:{pair["first_direction"]},second_tx:{pair["second_tx_hash"]},second:{pair["second_direction"]},block_distance:{pair["block_distance"]}')
    print('SELECTOR_COUNTS=' + json.dumps(summary['selector_counts'], sort_keys=True, separators=(',', ':')))
    print(f'RESULT_HASH={result["result_hash"]}')
    print('CLOSED_LOOP_CONFIRMED=false')
    print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
