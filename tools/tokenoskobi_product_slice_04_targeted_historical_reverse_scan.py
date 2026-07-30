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
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
DEFAULT_DB = ROOT / 'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
DEFAULT_PROVIDER = ROOT / 'config/era63e_always_on_market_runtime_v1.json'
DEFAULT_SELECTION = Path('/var/lib/tokenoskobi-product-slice-04/non_self_call_wallet_candidate_selection_v1.json')
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/targeted_historical_reverse_scan_v1.json')

SOURCE_TABLE = 'era64i_historical_wallet_transfer_staging_v1'
RECEIPT_TABLE = 'era64j_historical_receipt_cost_enrichment_v1'
EXPECTED_DB_HASH = '99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_SELECTION_HASH = 'a6f4779363a0993cab9f82510eee5139a7f7fabc7996701ef2bb1bf4cf1906ba'
EXCLUDED_EXECUTOR = '0x9999b0cdd35d7f3b281ba02efc0d228486940515'
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')
HEX_RE = re.compile(r'^0x[0-9a-f]*$')

SCAN_BLOCK_SPAN = 65_536
LOG_CHUNK_SIZE = 2_048
MAX_ANCHORS = 16
MAX_ACTORS = 12
MAX_DISCOVERED_LOGS = 500
MAX_DISCOVERED_TRANSACTIONS = 40
MAX_RPC_REQUESTS = 700
MAX_RUNTIME_SECONDS = 1_500.0
MAX_LOGS_PER_QUERY = 200

AUTHORITY = {
    'network_access': True,
    'network_mode': 'READ_ONLY_ALLOWLISTED_BSC_RPC_INDEXED_TRANSFER_REVERSE_SCAN',
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


class Slice04HistoricalReverseScanError(RuntimeError):
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
        raise Slice04HistoricalReverseScanError('INVALID_TRANSACTION_HASH')
    return text


def normalize_address(value: Any, *, allow_empty: bool = False) -> str:
    text = str(value or '').strip().lower()
    if allow_empty and text == '':
        return ''
    if ADDRESS_RE.fullmatch(text) is None:
        raise Slice04HistoricalReverseScanError('INVALID_EVM_ADDRESS')
    return text


def parse_hex_int(value: Any, field: str) -> int:
    text = str(value or '').strip().lower()
    if HEX_RE.fullmatch(text) is None:
        raise Slice04HistoricalReverseScanError(f'{field}:INVALID_HEX')
    try:
        number = int(text, 16)
    except ValueError as exc:
        raise Slice04HistoricalReverseScanError(f'{field}:INVALID_HEX') from exc
    if number < 0:
        raise Slice04HistoricalReverseScanError(f'{field}:NEGATIVE')
    return number


def read_json(path: Path, code: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise Slice04HistoricalReverseScanError(f'{code}_MISSING')
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise Slice04HistoricalReverseScanError(f'{code}_INVALID_JSON') from exc
    if not isinstance(payload, dict):
        raise Slice04HistoricalReverseScanError(f'{code}_NOT_OBJECT')
    return payload


def validate_selection(path: Path) -> dict[str, Any]:
    payload = read_json(path, 'SELECTION')
    if payload.get('schema') != 'tokenoskobi.product_slice_04.non_self_call_wallet_candidate_selection.v1':
        raise Slice04HistoricalReverseScanError('SELECTION_SCHEMA_INVALID')
    if payload.get('status') != 'NON_SELF_CALL_WALLET_CANDIDATE_SELECTION_COMPLETED':
        raise Slice04HistoricalReverseScanError('SELECTION_STATUS_INVALID')
    if payload.get('result_hash') != EXPECTED_SELECTION_HASH:
        raise Slice04HistoricalReverseScanError('SELECTION_HASH_INVALID')
    summary = payload.get('summary')
    if not isinstance(summary, dict):
        raise Slice04HistoricalReverseScanError('SELECTION_SUMMARY_INVALID')
    expected = {
        'non_self_call_source_transaction_count': 101,
        'all_round_trip_pair_count': 0,
        'selected_candidate_pair_count': 0,
        'selected_actor_count': 0,
        'selected_transaction_count': 0,
        'closed_loop_confirmed': False,
        'next_safe_step': 'CURRENT_DATASET_HAS_NO_NON_SELF_CALL_ROUND_TRIP_CANDIDATE_EXTEND_HISTORICAL_SCAN',
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise Slice04HistoricalReverseScanError(f'SELECTION_SUMMARY_DRIFT:{key}')
    return payload


def validate_provider(path: Path) -> dict[str, Any]:
    payload = read_json(path, 'PROVIDER')
    if payload.get('schema') != 'tokenoskobi.era63e.always_on_market_runtime_config.v1':
        raise Slice04HistoricalReverseScanError('PROVIDER_SCHEMA_INVALID')
    rpc = payload.get('rpc')
    if not isinstance(rpc, dict) or int(rpc.get('chain_id', 0)) != 56:
        raise Slice04HistoricalReverseScanError('PROVIDER_CHAIN_INVALID')
    endpoints = rpc.get('endpoints')
    allowed_hosts = set(rpc.get('allowed_hosts') or [])
    if not isinstance(endpoints, list) or len(endpoints) < 2 or not allowed_hosts:
        raise Slice04HistoricalReverseScanError('PROVIDER_ENDPOINTS_INVALID')
    normalized_endpoints: list[str] = []
    for endpoint in endpoints:
        parsed = urllib.parse.urlparse(str(endpoint))
        host = str(parsed.hostname or '').lower()
        if parsed.scheme != 'https' or host not in allowed_hosts:
            raise Slice04HistoricalReverseScanError('PROVIDER_ENDPOINT_NOT_ALLOWLISTED_HTTPS')
        normalized_endpoints.append(str(endpoint).rstrip('/'))
    return {
        'endpoints': normalized_endpoints,
        'allowed_hosts': sorted(allowed_hosts),
        'timeout': min(max(float(rpc.get('timeout_seconds', 12)), 2.0), 30.0),
        'retries': min(max(int(rpc.get('retries_per_endpoint', 1)), 0), 2),
    }


class RpcClient:
    ALLOWED_METHODS = {
        'eth_chainId',
        'eth_getLogs',
        'eth_getTransactionByHash',
        'eth_getTransactionReceipt',
        'eth_getBlockByNumber',
    }

    def __init__(self, provider: dict[str, Any]):
        self.endpoints = list(provider['endpoints'])
        self.allowed_hosts = set(provider['allowed_hosts'])
        self.timeout = float(provider['timeout'])
        self.retries = int(provider['retries'])
        self.request_count = 0
        self.errors: list[str] = []
        self.started = time.monotonic()
        self.endpoint_index = 0
        self.last_endpoint_host = ''

    def call(self, method: str, params: list[Any]) -> Any:
        if method not in self.ALLOWED_METHODS:
            raise Slice04HistoricalReverseScanError(f'RPC_METHOD_NOT_ALLOWLISTED:{method}')
        if self.request_count >= MAX_RPC_REQUESTS:
            raise Slice04HistoricalReverseScanError('RPC_REQUEST_BUDGET_EXCEEDED')
        if time.monotonic() - self.started > MAX_RUNTIME_SECONDS:
            raise Slice04HistoricalReverseScanError('RPC_RUNTIME_BUDGET_EXCEEDED')
        last_error = ''
        endpoint_count = len(self.endpoints)
        for offset in range(endpoint_count):
            endpoint = self.endpoints[(self.endpoint_index + offset) % endpoint_count]
            parsed = urllib.parse.urlparse(endpoint)
            host = str(parsed.hostname or '').lower()
            if parsed.scheme != 'https' or host not in self.allowed_hosts:
                continue
            for attempt in range(self.retries + 1):
                if self.request_count >= MAX_RPC_REQUESTS:
                    raise Slice04HistoricalReverseScanError('RPC_REQUEST_BUDGET_EXCEEDED')
                self.request_count += 1
                body = json.dumps(
                    {'jsonrpc': '2.0', 'id': self.request_count, 'method': method, 'params': params},
                    separators=(',', ':'),
                ).encode('utf-8')
                request = urllib.request.Request(
                    endpoint,
                    data=body,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'Tokenoskobi-Product-Slice-04/1.0 targeted-historical-reverse-scan',
                    },
                    method='POST',
                )
                try:
                    with urllib.request.urlopen(request, timeout=self.timeout) as response:
                        payload = json.loads(response.read().decode('utf-8'))
                    if not isinstance(payload, dict) or payload.get('error') is not None or 'result' not in payload:
                        detail = payload.get('error') if isinstance(payload, dict) else 'NOT_OBJECT'
                        raise Slice04HistoricalReverseScanError(f'RPC_RESPONSE_INVALID:{detail}')
                    self.endpoint_index = (self.endpoint_index + offset + 1) % endpoint_count
                    self.last_endpoint_host = host
                    return payload['result']
                except (
                    urllib.error.URLError,
                    urllib.error.HTTPError,
                    TimeoutError,
                    OSError,
                    json.JSONDecodeError,
                    Slice04HistoricalReverseScanError,
                ) as exc:
                    last_error = f'{type(exc).__name__}:{exc}'
                    self.errors.append(f'{host}:{method}:{last_error}')
                    if attempt < self.retries:
                        time.sleep(min(0.25 * (2 ** attempt), 1.0))
        raise Slice04HistoricalReverseScanError(f'ALL_RPC_ENDPOINTS_FAILED:{method}:{last_error}')


def load_database(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    resolved = path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file() or file_sha256(resolved) != EXPECTED_DB_HASH:
        raise Slice04HistoricalReverseScanError('SOURCE_DATABASE_INVALID')
    uri = f'file:{resolved}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04HistoricalReverseScanError('SOURCE_DATABASE_INTEGRITY_FAILED')
        source_rows = [
            dict(row)
            for row in conn.execute(
                f'''SELECT token_address,from_address,to_address,amount_raw,tx_hash,log_index,
                           block_number,block_time_utc,evidence_hash
                    FROM {SOURCE_TABLE}
                    ORDER BY block_number,tx_hash,log_index'''
            )
        ]
        receipt_rows = [
            dict(row)
            for row in conn.execute(
                f'''SELECT tx_hash,block_number,transaction_index,receipt_status,gas_cost_wei,
                           tx_from_address,tx_to_address,evidence_hash,raw_receipt_json,raw_transaction_json
                    FROM {RECEIPT_TABLE}
                    ORDER BY block_number,transaction_index,tx_hash'''
            )
        ]
    finally:
        conn.close()
    if len(source_rows) != 367 or len(receipt_rows) != 277:
        raise Slice04HistoricalReverseScanError('SOURCE_COUNTS_CHANGED')
    tokens = sorted({normalize_address(row['token_address']) for row in source_rows})
    if len(tokens) != 3:
        raise Slice04HistoricalReverseScanError('TRACKED_TOKEN_SCOPE_CHANGED')
    return source_rows, receipt_rows, tokens


def compute_actor_net(events: list[dict[str, Any]], actor: str) -> dict[str, int]:
    net: dict[str, int] = defaultdict(int)
    for event in events:
        token = normalize_address(event.get('token_address'))
        amount = int(str(event.get('amount_raw')))
        if amount <= 0:
            raise Slice04HistoricalReverseScanError('TRANSFER_AMOUNT_INVALID')
        if normalize_address(event.get('from_address')) == actor:
            net[token] -= amount
        if normalize_address(event.get('to_address')) == actor:
            net[token] += amount
    return {token: amount for token, amount in net.items() if amount != 0}


def endpoint_tokens(net: dict[str, int]) -> tuple[list[str], list[str]]:
    outs = sorted(token for token, amount in net.items() if amount < 0)
    ins = sorted(token for token, amount in net.items() if amount > 0)
    return outs, ins


def raw_transaction_available(value: Any) -> bool:
    text = str(value or '').strip()
    if not text:
        return False
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return False
    return isinstance(payload, dict) and bool(payload)


def build_eligible_records(
    source_rows: list[dict[str, Any]],
    receipt_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    events_by_tx: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        events_by_tx[normalize_hash(row['tx_hash'])].append(row)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for receipt in receipt_rows:
        tx_hash = normalize_hash(receipt['tx_hash'])
        if tx_hash in seen:
            raise Slice04HistoricalReverseScanError('RECEIPT_DUPLICATE_TRANSACTION')
        seen.add(tx_hash)
        actor = normalize_address(receipt['tx_from_address'])
        tx_to = normalize_address(receipt.get('tx_to_address'), allow_empty=True)
        if int(receipt['receipt_status']) != 1:
            continue
        if actor == EXCLUDED_EXECUTOR or not tx_to or actor == tx_to:
            continue
        events = events_by_tx.get(tx_hash)
        if not events:
            continue
        net = compute_actor_net(events, actor)
        if not net:
            continue
        outs, ins = endpoint_tokens(net)
        records.append(
            {
                'tx_hash': tx_hash,
                'actor': actor,
                'tx_to': tx_to,
                'block_number': int(receipt['block_number']),
                'transaction_index': int(receipt['transaction_index']),
                'gas_cost_wei': str(receipt['gas_cost_wei']),
                'receipt_evidence_hash': str(receipt['evidence_hash']),
                'net_by_token': {token: str(amount) for token, amount in sorted(net.items())},
                'out_tokens': outs,
                'in_tokens': ins,
                'two_sided_actor_flow': bool(outs and ins),
                'single_endpoint_pair': len(outs) == 1 and len(ins) == 1,
                'raw_transaction_available': raw_transaction_available(receipt.get('raw_transaction_json')),
                'source_event_count': len(events),
            }
        )
    if len(records) != 101:
        raise Slice04HistoricalReverseScanError('ELIGIBLE_RECORD_COUNT_CHANGED')
    return records


def select_anchors(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for record in records:
        if not record['single_endpoint_pair'] or not record['two_sided_actor_flow']:
            continue
        input_token = record['out_tokens'][0]
        output_token = record['in_tokens'][0]
        net = {token: int(value) for token, value in record['net_by_token'].items()}
        for token, observed_direction, missing_direction in (
            (output_token, 'IN', 'OUT'),
            (input_token, 'OUT', 'IN'),
        ):
            score = 32 + 8 * int(record['raw_transaction_available']) + min(int(record['source_event_count']), 7)
            candidate = {
                'actor': record['actor'],
                'token': token,
                'observed_direction': observed_direction,
                'missing_direction': missing_direction,
                'anchor_tx_hash': record['tx_hash'],
                'anchor_tx_to': record['tx_to'],
                'anchor_block_number': record['block_number'],
                'anchor_transaction_index': record['transaction_index'],
                'anchor_input_token': input_token,
                'anchor_output_token': output_token,
                'anchor_input_raw': str(abs(net[input_token])),
                'anchor_output_raw': str(net[output_token]),
                'anchor_net_by_token': record['net_by_token'],
                'anchor_raw_transaction_available': record['raw_transaction_available'],
                'ranking_score': score,
            }
            candidate['anchor_hash'] = canonical_hash(candidate)
            candidates.append(candidate)
    candidates.sort(
        key=lambda row: (
            -int(row['ranking_score']),
            -int(row['anchor_block_number']),
            row['actor'],
            row['token'],
            row['missing_direction'],
            row['anchor_tx_hash'],
        )
    )
    selected: list[dict[str, Any]] = []
    actors: set[str] = set()
    seen_keys: set[tuple[str, str, str]] = set()
    for row in candidates:
        key = (row['actor'], row['token'], row['missing_direction'])
        if key in seen_keys:
            continue
        prospective = actors | {row['actor']}
        if len(prospective) > MAX_ACTORS:
            continue
        selected.append(row)
        actors = prospective
        seen_keys.add(key)
        if len(selected) >= MAX_ANCHORS:
            break
    if not selected:
        raise Slice04HistoricalReverseScanError('NO_ELIGIBLE_SINGLE_ENDPOINT_ANCHOR')
    return selected


def topic_address(address: str) -> str:
    return '0x' + ('0' * 24) + normalize_address(address)[2:]


def build_log_filter(anchor: dict[str, Any], start_block: int, end_block: int) -> dict[str, Any]:
    if start_block < 0 or end_block < start_block:
        raise Slice04HistoricalReverseScanError('SCAN_RANGE_INVALID')
    actor_topic = topic_address(anchor['actor'])
    direction = anchor['missing_direction']
    if direction == 'OUT':
        topics: list[Any] = [TRANSFER_TOPIC, actor_topic]
    elif direction == 'IN':
        topics = [TRANSFER_TOPIC, None, actor_topic]
    else:
        raise Slice04HistoricalReverseScanError('ANCHOR_DIRECTION_INVALID')
    return {
        'address': normalize_address(anchor['token']),
        'fromBlock': hex(start_block),
        'toBlock': hex(end_block),
        'topics': topics,
    }


def decode_transfer_log(log: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(log, dict):
        raise Slice04HistoricalReverseScanError('TRANSFER_LOG_NOT_OBJECT')
    token = normalize_address(log.get('address'))
    topics = log.get('topics')
    if not isinstance(topics, list) or len(topics) != 3:
        raise Slice04HistoricalReverseScanError('TRANSFER_LOG_TOPICS_INVALID')
    if str(topics[0]).lower() != TRANSFER_TOPIC:
        raise Slice04HistoricalReverseScanError('TRANSFER_LOG_TOPIC0_INVALID')
    from_address = normalize_address('0x' + str(topics[1]).lower()[-40:])
    to_address = normalize_address('0x' + str(topics[2]).lower()[-40:])
    amount = parse_hex_int(log.get('data') or '0x0', 'transfer.data')
    if amount <= 0:
        raise Slice04HistoricalReverseScanError('TRANSFER_LOG_AMOUNT_INVALID')
    return {
        'token_address': token,
        'from_address': from_address,
        'to_address': to_address,
        'amount_raw': amount,
        'tx_hash': normalize_hash(log.get('transactionHash')),
        'block_number': parse_hex_int(log.get('blockNumber'), 'transfer.blockNumber'),
        'log_index': parse_hex_int(log.get('logIndex'), 'transfer.logIndex'),
        'removed': bool(log.get('removed', False)),
        'evidence_hash': canonical_hash(log),
    }


def receipt_actor_net(receipt: dict[str, Any], actor: str, tracked_tokens: set[str]) -> dict[str, int]:
    logs = receipt.get('logs')
    if not isinstance(logs, list):
        raise Slice04HistoricalReverseScanError('RECEIPT_LOGS_INVALID')
    events: list[dict[str, Any]] = []
    for log in logs:
        if not isinstance(log, dict):
            continue
        topics = log.get('topics')
        token = str(log.get('address') or '').strip().lower()
        if token not in tracked_tokens:
            continue
        if not isinstance(topics, list) or len(topics) != 3 or str(topics[0]).lower() != TRANSFER_TOPIC:
            continue
        events.append(decode_transfer_log(log))
    return compute_actor_net(events, actor)


def validate_transaction_and_receipt(
    client: RpcClient,
    tx_hash: str,
    actor: str,
    tracked_tokens: set[str],
    tx_cache: dict[str, dict[str, Any]],
    receipt_cache: dict[str, dict[str, Any]],
    block_cache: dict[int, dict[str, Any]],
) -> dict[str, Any] | None:
    if tx_hash not in tx_cache:
        tx = client.call('eth_getTransactionByHash', [tx_hash])
        if tx is None:
            return None
        if not isinstance(tx, dict):
            raise Slice04HistoricalReverseScanError('DISCOVERED_TRANSACTION_NOT_OBJECT')
        tx_cache[tx_hash] = tx
    tx = tx_cache[tx_hash]
    if normalize_hash(tx.get('hash')) != tx_hash:
        raise Slice04HistoricalReverseScanError('DISCOVERED_TRANSACTION_HASH_MISMATCH')
    tx_actor = normalize_address(tx.get('from'))
    tx_to = normalize_address(tx.get('to'), allow_empty=True)
    if tx_actor != actor or not tx_to or tx_to == actor:
        return None

    if tx_hash not in receipt_cache:
        receipt = client.call('eth_getTransactionReceipt', [tx_hash])
        if receipt is None:
            return None
        if not isinstance(receipt, dict):
            raise Slice04HistoricalReverseScanError('DISCOVERED_RECEIPT_NOT_OBJECT')
        receipt_cache[tx_hash] = receipt
    receipt = receipt_cache[tx_hash]
    if normalize_hash(receipt.get('transactionHash')) != tx_hash:
        raise Slice04HistoricalReverseScanError('DISCOVERED_RECEIPT_HASH_MISMATCH')
    if parse_hex_int(receipt.get('status'), 'receipt.status') != 1:
        return None
    block_number = parse_hex_int(receipt.get('blockNumber'), 'receipt.blockNumber')
    if block_number not in block_cache:
        block = client.call('eth_getBlockByNumber', [hex(block_number), False])
        if not isinstance(block, dict):
            raise Slice04HistoricalReverseScanError('DISCOVERED_BLOCK_NOT_OBJECT')
        block_cache[block_number] = block
    block = block_cache[block_number]
    if parse_hex_int(block.get('number'), 'block.number') != block_number:
        raise Slice04HistoricalReverseScanError('DISCOVERED_BLOCK_NUMBER_MISMATCH')
    net = receipt_actor_net(receipt, actor, tracked_tokens)
    if not net:
        return None
    outs, ins = endpoint_tokens(net)
    input_data = str(tx.get('input') or '0x').lower()
    return {
        'tx_hash': tx_hash,
        'actor': actor,
        'tx_to': tx_to,
        'block_number': block_number,
        'transaction_index': parse_hex_int(receipt.get('transactionIndex'), 'receipt.transactionIndex'),
        'block_time_utc': datetime.fromtimestamp(
            parse_hex_int(block.get('timestamp'), 'block.timestamp'),
            tz=timezone.utc,
        ).isoformat(),
        'gas_used': str(parse_hex_int(receipt.get('gasUsed'), 'receipt.gasUsed')),
        'effective_gas_price_wei': str(
            parse_hex_int(receipt.get('effectiveGasPrice') or tx.get('gasPrice') or '0x0', 'receipt.effectiveGasPrice')
        ),
        'net_by_token': {token: str(value) for token, value in sorted(net.items())},
        'out_tokens': outs,
        'in_tokens': ins,
        'two_sided_actor_flow': bool(outs and ins),
        'single_endpoint_pair': len(outs) == 1 and len(ins) == 1,
        'transaction_input': input_data,
        'selector': input_data[:10] if len(input_data) >= 10 else '0x',
        'transaction_evidence_hash': canonical_hash(tx),
        'receipt_evidence_hash': canonical_hash(receipt),
        'block_evidence_hash': canonical_hash(block),
    }


def build_pair(anchor: dict[str, Any], discovered: dict[str, Any]) -> dict[str, Any]:
    discovered_net = {token: int(value) for token, value in discovered['net_by_token'].items()}
    missing_direction = anchor['missing_direction']
    selected_amount = discovered_net.get(anchor['token'], 0)
    direction_matches = (
        (missing_direction == 'IN' and selected_amount > 0)
        or (missing_direction == 'OUT' and selected_amount < 0)
    )
    endpoint_reverse_exact = (
        direction_matches
        and discovered['single_endpoint_pair']
        and discovered['out_tokens'][0] == anchor['anchor_output_token']
        and discovered['in_tokens'][0] == anchor['anchor_input_token']
    )
    position_amount_exact = (
        endpoint_reverse_exact
        and str(abs(discovered_net[anchor['anchor_output_token']])) == anchor['anchor_output_raw']
    )
    same_target = discovered['tx_to'] == anchor['anchor_tx_to']
    score = (
        32 * int(endpoint_reverse_exact)
        + 16 * int(position_amount_exact)
        + 8 * int(discovered['two_sided_actor_flow'])
        + 4 * int(discovered['single_endpoint_pair'])
        + 2 * int(same_target)
        + int(direction_matches)
    )
    pair = {
        'actor': anchor['actor'],
        'anchor_tx_hash': anchor['anchor_tx_hash'],
        'historical_tx_hash': discovered['tx_hash'],
        'anchor_block_number': anchor['anchor_block_number'],
        'historical_block_number': discovered['block_number'],
        'block_distance': anchor['anchor_block_number'] - discovered['block_number'],
        'selected_token': anchor['token'],
        'anchor_observed_direction': anchor['observed_direction'],
        'historical_direction': 'IN' if selected_amount > 0 else 'OUT' if selected_amount < 0 else 'ZERO',
        'direction_opposite_exact': direction_matches,
        'endpoint_reverse_exact': endpoint_reverse_exact,
        'position_amount_exact': position_amount_exact,
        'same_transaction_target': same_target,
        'anchor_input_token': anchor['anchor_input_token'],
        'anchor_output_token': anchor['anchor_output_token'],
        'anchor_input_raw': anchor['anchor_input_raw'],
        'anchor_output_raw': anchor['anchor_output_raw'],
        'historical_net_by_token': discovered['net_by_token'],
        'historical_tx_to': discovered['tx_to'],
        'historical_selector': discovered['selector'],
        'ranking_score': score,
        'closed_loop_confirmed': False,
        'candidate_only': True,
    }
    pair['candidate_hash'] = canonical_hash(pair)
    return pair


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
    selection_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    selection = validate_selection(selection_path)
    source_rows, receipt_rows, tracked_tokens_list = load_database(database_path)
    tracked_tokens = set(tracked_tokens_list)
    records = build_eligible_records(source_rows, receipt_rows)
    anchors = select_anchors(records)

    minimum_source_block = min(int(row['block_number']) for row in source_rows)
    scan_end = minimum_source_block - 1
    scan_start = scan_end - SCAN_BLOCK_SPAN + 1
    if scan_start < 0:
        raise Slice04HistoricalReverseScanError('HISTORICAL_SCAN_RANGE_INVALID')

    provider = validate_provider(provider_path)
    client = RpcClient(provider)
    if parse_hex_int(client.call('eth_chainId', []), 'eth_chainId') != 56:
        raise Slice04HistoricalReverseScanError('RPC_CHAIN_ID_MISMATCH')

    raw_hits: list[dict[str, Any]] = []
    seen_log_keys: set[tuple[str, int, str]] = set()
    for anchor_index, anchor in enumerate(anchors, start=1):
        for chunk_start in range(scan_start, scan_end + 1, LOG_CHUNK_SIZE):
            chunk_end = min(chunk_start + LOG_CHUNK_SIZE - 1, scan_end)
            result = client.call('eth_getLogs', [build_log_filter(anchor, chunk_start, chunk_end)])
            if not isinstance(result, list):
                raise Slice04HistoricalReverseScanError('ETH_GET_LOGS_RESULT_NOT_LIST')
            if len(result) > MAX_LOGS_PER_QUERY:
                raise Slice04HistoricalReverseScanError('ETH_GET_LOGS_QUERY_RESULT_SCOPE_EXCEEDED')
            for log in result:
                decoded = decode_transfer_log(log)
                if decoded['removed']:
                    continue
                if decoded['token_address'] != anchor['token']:
                    raise Slice04HistoricalReverseScanError('ETH_GET_LOGS_TOKEN_FILTER_MISMATCH')
                if decoded['block_number'] < scan_start or decoded['block_number'] > scan_end:
                    raise Slice04HistoricalReverseScanError('ETH_GET_LOGS_BLOCK_RANGE_MISMATCH')
                if anchor['missing_direction'] == 'OUT' and decoded['from_address'] != anchor['actor']:
                    raise Slice04HistoricalReverseScanError('ETH_GET_LOGS_FROM_TOPIC_MISMATCH')
                if anchor['missing_direction'] == 'IN' and decoded['to_address'] != anchor['actor']:
                    raise Slice04HistoricalReverseScanError('ETH_GET_LOGS_TO_TOPIC_MISMATCH')
                key = (decoded['tx_hash'], decoded['log_index'], anchor['anchor_hash'])
                if key in seen_log_keys:
                    continue
                seen_log_keys.add(key)
                raw_hits.append({'anchor_index': anchor_index, 'anchor_hash': anchor['anchor_hash'], **decoded})
                if len(raw_hits) > MAX_DISCOVERED_LOGS:
                    raise Slice04HistoricalReverseScanError('DISCOVERED_LOG_SCOPE_EXCEEDED')

    tx_hashes = sorted({item['tx_hash'] for item in raw_hits})
    if len(tx_hashes) > MAX_DISCOVERED_TRANSACTIONS:
        raise Slice04HistoricalReverseScanError('DISCOVERED_TRANSACTION_SCOPE_EXCEEDED')

    tx_cache: dict[str, dict[str, Any]] = {}
    receipt_cache: dict[str, dict[str, Any]] = {}
    block_cache: dict[int, dict[str, Any]] = {}
    validated_by_actor_tx: dict[tuple[str, str], dict[str, Any] | None] = {}
    pairs: list[dict[str, Any]] = []
    discovered_transactions: dict[str, dict[str, Any]] = {}
    anchor_by_hash = {anchor['anchor_hash']: anchor for anchor in anchors}

    for hit in sorted(raw_hits, key=lambda row: (row['block_number'], row['tx_hash'], row['log_index'], row['anchor_hash'])):
        anchor = anchor_by_hash[hit['anchor_hash']]
        cache_key = (anchor['actor'], hit['tx_hash'])
        if cache_key not in validated_by_actor_tx:
            validated_by_actor_tx[cache_key] = validate_transaction_and_receipt(
                client,
                hit['tx_hash'],
                anchor['actor'],
                tracked_tokens,
                tx_cache,
                receipt_cache,
                block_cache,
            )
        discovered = validated_by_actor_tx[cache_key]
        if discovered is None:
            continue
        discovered_transactions[discovered['tx_hash']] = discovered
        pair = build_pair(anchor, discovered)
        if pair['direction_opposite_exact']:
            pairs.append(pair)

    unique_pairs: dict[str, dict[str, Any]] = {}
    for pair in pairs:
        unique_pairs.setdefault(pair['candidate_hash'], pair)
    pairs = list(unique_pairs.values())
    pairs.sort(
        key=lambda row: (
            -int(row['ranking_score']),
            int(row['block_distance']),
            row['actor'],
            row['historical_tx_hash'],
            row['anchor_tx_hash'],
            row['selected_token'],
        )
    )
    endpoint_count = sum(int(item['endpoint_reverse_exact']) for item in pairs)
    amount_exact_count = sum(int(item['endpoint_reverse_exact'] and item['position_amount_exact']) for item in pairs)
    next_step = (
        'ENRICH_DISCOVERED_REVERSE_TRANSACTIONS_AND_ALLOWLISTED_ROUTE_DECODE'
        if endpoint_count
        else 'NO_REVERSE_ENDPOINT_CANDIDATE_IN_65536_BLOCK_WINDOW_REASSESS_SCAN_SCOPE'
    )

    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.targeted_historical_reverse_scan.v1',
        'generated_at_utc': iso_now(),
        'status': 'TARGETED_HISTORICAL_REVERSE_SCAN_COMPLETED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {
            'database_path': str(database_path.resolve()),
            'database_sha256': file_sha256(database_path),
            'selection_path': str(selection_path),
            'selection_result_hash': selection['result_hash'],
            'provider_path': str(provider_path.resolve()),
            'source_event_count': len(source_rows),
            'source_receipt_count': len(receipt_rows),
            'eligible_non_self_call_transaction_count': len(records),
            'tracked_tokens': tracked_tokens_list,
        },
        'policy': {
            'scan_direction': 'OLDER_ADJACENT_BLOCKS_ONLY',
            'scan_block_span': SCAN_BLOCK_SPAN,
            'log_chunk_size': LOG_CHUNK_SIZE,
            'maximum_anchors': MAX_ANCHORS,
            'maximum_actors': MAX_ACTORS,
            'maximum_discovered_logs': MAX_DISCOVERED_LOGS,
            'maximum_discovered_transactions': MAX_DISCOVERED_TRANSACTIONS,
            'maximum_rpc_requests': MAX_RPC_REQUESTS,
            'indexed_transfer_topic_filter_required': True,
            'missing_opposite_direction_only': True,
            'successful_receipt_required': True,
            'tx_from_must_equal_actor': True,
            'tx_to_must_not_equal_actor': True,
            'executor_actor_excluded': EXCLUDED_EXECUTOR,
            'selection_is_candidate_only_not_closed_loop_proof': True,
            'identity_or_ownership_inference_allowed': False,
        },
        'scan_range': {
            'minimum_existing_source_block': minimum_source_block,
            'start_block': scan_start,
            'end_block': scan_end,
            'block_count': SCAN_BLOCK_SPAN,
        },
        'anchors': anchors,
        'raw_indexed_transfer_hits': raw_hits,
        'discovered_transactions': sorted(
            discovered_transactions.values(),
            key=lambda row: (row['block_number'], row['transaction_index'], row['tx_hash']),
        ),
        'candidate_pairs': pairs[:40],
        'top_candidate': pairs[0] if pairs else None,
        'rpc': {
            'request_count': client.request_count,
            'error_count': len(client.errors),
            'last_endpoint_host': client.last_endpoint_host,
            'errors': client.errors[-40:],
        },
        'summary': {
            'anchor_count': len(anchors),
            'anchor_actor_count': len({item['actor'] for item in anchors}),
            'raw_indexed_transfer_hit_count': len(raw_hits),
            'distinct_discovered_transaction_hash_count': len(tx_hashes),
            'validated_discovered_transaction_count': len(discovered_transactions),
            'opposite_direction_candidate_count': len(pairs),
            'endpoint_reverse_exact_candidate_count': endpoint_count,
            'endpoint_reverse_and_position_amount_exact_candidate_count': amount_exact_count,
            'closed_loop_confirmed': False,
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
    parser.add_argument('--selection', type=Path, default=DEFAULT_SELECTION)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.database, args.provider, args.selection, args.output)
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'SCAN_START_BLOCK={result["scan_range"]["start_block"]}')
    print(f'SCAN_END_BLOCK={result["scan_range"]["end_block"]}')
    print(f'SCAN_BLOCK_COUNT={result["scan_range"]["block_count"]}')
    for key in (
        'anchor_count',
        'anchor_actor_count',
        'raw_indexed_transfer_hit_count',
        'distinct_discovered_transaction_hash_count',
        'validated_discovered_transaction_count',
        'opposite_direction_candidate_count',
        'endpoint_reverse_exact_candidate_count',
        'endpoint_reverse_and_position_amount_exact_candidate_count',
    ):
        print(f'{key.upper()}={summary[key]}')
    for index, anchor in enumerate(result['anchors'], start=1):
        print(
            f'ANCHOR_{index}=actor:{anchor["actor"]},token:{anchor["token"]},'
            f'observed:{anchor["observed_direction"]},search:{anchor["missing_direction"]},'
            f'tx:{anchor["anchor_tx_hash"]},block:{anchor["anchor_block_number"]},'
            f'input:{anchor["anchor_input_token"]},output:{anchor["anchor_output_token"]},'
            f'score:{anchor["ranking_score"]}'
        )
    for index, pair in enumerate(result['candidate_pairs'], start=1):
        print(
            f'REVERSE_CANDIDATE_{index}=actor:{pair["actor"]},historical_tx:{pair["historical_tx_hash"]},'
            f'anchor_tx:{pair["anchor_tx_hash"]},token:{pair["selected_token"]},'
            f'historical:{pair["historical_direction"]},anchor:{pair["anchor_observed_direction"]},'
            f'endpoint_reverse:{str(pair["endpoint_reverse_exact"]).lower()},'
            f'position_amount_exact:{str(pair["position_amount_exact"]).lower()},'
            f'block_distance:{pair["block_distance"]},score:{pair["ranking_score"]}'
        )
    top = result.get('top_candidate')
    if top:
        print(
            f'TOP_CANDIDATE=actor:{top["actor"]},historical_tx:{top["historical_tx_hash"]},'
            f'anchor_tx:{top["anchor_tx_hash"]},endpoint_reverse:{str(top["endpoint_reverse_exact"]).lower()},'
            f'position_amount_exact:{str(top["position_amount_exact"]).lower()},score:{top["ranking_score"]}'
        )
    else:
        print('TOP_CANDIDATE=NONE')
    print(f'RPC_REQUEST_COUNT={result["rpc"]["request_count"]}')
    print(f'RPC_ERROR_COUNT={result["rpc"]["error_count"]}')
    print(f'RESULT_HASH={result["result_hash"]}')
    print('CLOSED_LOOP_CONFIRMED=false')
    print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
