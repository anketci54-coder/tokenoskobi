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
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any

getcontext().prec = 80

ROOT = Path('/root/tokenoskobi_clean_v1')
DEFAULT_DB = ROOT / 'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
DEFAULT_CONFIG = ROOT / 'config/era63e_always_on_market_runtime_v1.json'
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json')

SOURCE_TABLE = 'era64i_historical_wallet_transfer_staging_v1'
RECEIPT_TABLE = 'era64j_historical_receipt_cost_enrichment_v1'
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')
ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')
HEX_RE = re.compile(r'^0x(?:[0-9a-f]{2})*$')

CANDIDATE_TX_HASHES = (
    '0xfcdc5f52f01dd5405a8a06888366f891c3154dce20e2b78371fbdce610e3b7d7',
    '0xc5e7abdad1aede7ce17343af296343fb2a773ef617fb2cf332fbb4eeb5602cc6',
    '0xcdd7990f09c1319f314b838526e97cb3ad53cb1e7d66c21eb401dd18b8ce6bed',
    '0xd62825974fffe07294520dae7f03c7fb76484022a36cdb176faa8bab5251c384',
    '0x1ed2373882aeca4cb99572b354c5e6447a422cf24b05c85893617f71bc2741a5',
    '0x8b9843892e9894dc6e6df59b6664754465aad35faf9c1ba95056977c49e080b5',
    '0xc511ddafcef6e338ea705571506cefd68827f5807a5facb1025545ef41eb415a',
    '0xe4dd460ca0e8b1bed6a77ba61c0b7651c846f7f023a7556d2f800682296e9d88',
    '0x8ca83effa5c92e60abf65558a5c4ec97ae2bda7312d5b43a898823e1c92fe1ad',
    '0x7f3ead8ca6261d132df64230976c10bacdc6dc99a70e3c9bf29870443de3c840',
    '0xfe716dbf1005220397bc5dd988ab35e9e923f826c91bcddcb187e25034b67682',
    '0x15da86852bfac2cc57e241e524518e8b7ffa4a3fa7f6f4c868f427d00d58f28b',
    '0xa9840f2eb2c57d2ce302e624463550540f8acd058fc6768f4820d2a54bb4edf0',
    '0xc09c48ae33398a6753f8efa93d573f11fe8dd73b47a7e3989b2cf864f68611c5',
)

TRACKED_TOKENS = (
    '0x55d398326f99059ff775485246999027b3197955',
    '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',
    '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d',
)

TOKEN_CALLS = {
    'decimals': '0x313ce567',
    'symbol': '0x95d89b41',
    'name': '0x06fdde03',
}

AUTHORITY = {
    'network_access': True,
    'network_mode': 'READ_ONLY_ALLOWLISTED_BSC_RPC',
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


class Slice04EnrichmentError(RuntimeError):
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
        raise Slice04EnrichmentError('INVALID_TRANSACTION_HASH')
    return text


def normalize_address(value: Any, *, allow_empty: bool = False) -> str:
    text = str(value or '').strip().lower()
    if allow_empty and text == '':
        return ''
    if ADDRESS_RE.fullmatch(text) is None:
        raise Slice04EnrichmentError('INVALID_EVM_ADDRESS')
    return text


def parse_hex_int(value: Any, field: str) -> int:
    text = str(value or '').strip().lower()
    if not text.startswith('0x'):
        raise Slice04EnrichmentError(f'{field}:NOT_HEX')
    try:
        number = int(text, 16)
    except ValueError as exc:
        raise Slice04EnrichmentError(f'{field}:INVALID_HEX') from exc
    if number < 0:
        raise Slice04EnrichmentError(f'{field}:NEGATIVE')
    return number


def validate_hex_data(value: Any, field: str) -> str:
    text = str(value or '').strip().lower()
    if HEX_RE.fullmatch(text) is None:
        raise Slice04EnrichmentError(f'{field}:INVALID_HEX_DATA')
    return text


def decode_uint256(value: str) -> int:
    data = validate_hex_data(value, 'uint256')
    payload = data[2:]
    if len(payload) < 64:
        raise Slice04EnrichmentError('UINT256_RESPONSE_TOO_SHORT')
    return int(payload[:64], 16)


def _decode_bytes_text(raw: bytes) -> str:
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise Slice04EnrichmentError('ABI_STRING_NOT_UTF8') from exc
    text = text.rstrip('\x00').strip()
    if not text or len(text) > 128 or any(ord(char) < 32 for char in text):
        raise Slice04EnrichmentError('ABI_STRING_INVALID_TEXT')
    return text


def decode_abi_string(value: str) -> str:
    data = validate_hex_data(value, 'abi_string')
    payload = bytes.fromhex(data[2:])
    if len(payload) == 32:
        return _decode_bytes_text(payload)
    if len(payload) < 64 or len(payload) % 32 != 0:
        raise Slice04EnrichmentError('ABI_STRING_RESPONSE_SHAPE_INVALID')
    offset = int.from_bytes(payload[0:32], 'big')
    if offset % 32 != 0 or offset + 32 > len(payload):
        raise Slice04EnrichmentError('ABI_STRING_OFFSET_INVALID')
    length = int.from_bytes(payload[offset:offset + 32], 'big')
    start = offset + 32
    end = start + length
    if length < 1 or length > 128 or end > len(payload):
        raise Slice04EnrichmentError('ABI_STRING_LENGTH_INVALID')
    return _decode_bytes_text(payload[start:end])


def normalized_decimal(raw_amount: int, decimals: int) -> str:
    if raw_amount < 0 or decimals < 0 or decimals > 36:
        raise Slice04EnrichmentError('NORMALIZED_AMOUNT_INPUT_INVALID')
    value = Decimal(raw_amount) / (Decimal(10) ** decimals)
    text = format(value, 'f')
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return text or '0'


def validate_provider_config(config: dict[str, Any]) -> tuple[list[str], set[str], float, int]:
    if config.get('schema') != 'tokenoskobi.era63e.always_on_market_runtime_config.v1':
        raise Slice04EnrichmentError('PROVIDER_SCHEMA_INVALID')
    rpc = config.get('rpc')
    if not isinstance(rpc, dict) or int(rpc.get('chain_id', 0)) != 56:
        raise Slice04EnrichmentError('PROVIDER_CHAIN_INVALID')
    endpoints = [str(item).rstrip('/') for item in rpc.get('endpoints') or []]
    allowed_hosts = {str(item).lower() for item in rpc.get('allowed_hosts') or []}
    if len(endpoints) < 2 or len(allowed_hosts) < 2:
        raise Slice04EnrichmentError('PROVIDER_REDUNDANCY_INSUFFICIENT')
    for endpoint in endpoints:
        parsed = urllib.parse.urlparse(endpoint)
        if parsed.scheme != 'https' or str(parsed.hostname or '').lower() not in allowed_hosts:
            raise Slice04EnrichmentError('PROVIDER_ENDPOINT_NOT_ALLOWLISTED_HTTPS')
    timeout = float(rpc.get('request_timeout_sec', 8))
    retries = int(rpc.get('retries_per_endpoint', 1))
    if timeout < 2 or timeout > 30 or retries < 0 or retries > 2:
        raise Slice04EnrichmentError('PROVIDER_LIMITS_INVALID')
    return endpoints, allowed_hosts, timeout, retries


class RpcClient:
    ALLOWED_METHODS = {'eth_chainId', 'eth_getTransactionByHash', 'eth_call'}

    def __init__(self, config: dict[str, Any], *, maximum_requests: int = 120, maximum_seconds: float = 300.0):
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
            raise Slice04EnrichmentError(f'RPC_METHOD_NOT_ALLOWLISTED:{method}')
        if self.request_count >= self.maximum_requests:
            raise Slice04EnrichmentError('RPC_REQUEST_BUDGET_EXCEEDED')
        if time.monotonic() - self.started > self.maximum_seconds:
            raise Slice04EnrichmentError('RPC_RUNTIME_BUDGET_EXCEEDED')
        last_error = ''
        endpoint_count = len(self.endpoints)
        for offset in range(endpoint_count):
            endpoint = self.endpoints[(self.endpoint_index + offset) % endpoint_count]
            parsed = urllib.parse.urlparse(endpoint)
            host = str(parsed.hostname or '').lower()
            if parsed.scheme != 'https' or host not in self.allowed_hosts:
                continue
            for attempt in range(self.retries + 1):
                self.request_count += 1
                payload = json.dumps({'jsonrpc': '2.0', 'id': self.request_count, 'method': method, 'params': params}, separators=(',', ':')).encode('utf-8')
                request = urllib.request.Request(endpoint, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'Tokenoskobi-Product-Slice-04/1.0 bounded-readonly-enrichment'}, method='POST')
                try:
                    with urllib.request.urlopen(request, timeout=self.timeout) as response:
                        body = json.loads(response.read().decode('utf-8'))
                    if not isinstance(body, dict) or body.get('error') is not None or 'result' not in body:
                        raise Slice04EnrichmentError(f'RPC_RESPONSE_INVALID:{body.get("error") if isinstance(body, dict) else "NOT_OBJECT"}')
                    self.endpoint_index = (self.endpoint_index + offset + 1) % endpoint_count
                    self.last_endpoint_host = host
                    return body['result']
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError, Slice04EnrichmentError) as exc:
                    last_error = f'{type(exc).__name__}:{exc}'
                    self.errors.append(f'{host}:{method}:{last_error}')
                    if attempt < self.retries:
                        time.sleep(min(0.25 * (2 ** attempt), 1.0))
                if self.request_count >= self.maximum_requests:
                    raise Slice04EnrichmentError('RPC_REQUEST_BUDGET_EXCEEDED')
        raise Slice04EnrichmentError(f'ALL_RPC_ENDPOINTS_FAILED:{method}:{last_error}')


def load_source_evidence(database_path: Path) -> dict[str, Any]:
    resolved = database_path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file() or resolved.stat().st_size <= 0:
        raise Slice04EnrichmentError('SOURCE_DATABASE_PATH_OR_FILE_INVALID')
    uri = f'file:{resolved}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04EnrichmentError('SOURCE_DATABASE_INTEGRITY_FAILED')
        tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if SOURCE_TABLE not in tables or RECEIPT_TABLE not in tables:
            raise Slice04EnrichmentError('SOURCE_TABLES_MISSING')
        placeholders = ','.join('?' for _ in CANDIDATE_TX_HASHES)
        source_rows = [dict(row) for row in conn.execute(f'''SELECT event_uid,token_address,from_address,to_address,amount_raw,tx_hash,log_index,block_number,block_time_utc,evidence_hash FROM {SOURCE_TABLE} WHERE tx_hash IN ({placeholders}) ORDER BY block_number,tx_hash,log_index''', CANDIDATE_TX_HASHES)]
        receipt_rows = [dict(row) for row in conn.execute(f'''SELECT tx_hash,block_number,receipt_status,gas_used,effective_gas_price_wei,gas_cost_wei,tx_from_address,tx_to_address,evidence_hash,raw_receipt_json FROM {RECEIPT_TABLE} WHERE tx_hash IN ({placeholders}) ORDER BY block_number,transaction_index,tx_hash''', CANDIDATE_TX_HASHES)]
    finally:
        conn.close()
    source_hashes = {normalize_hash(row['tx_hash']) for row in source_rows}
    receipt_hashes = {normalize_hash(row['tx_hash']) for row in receipt_rows}
    expected = set(CANDIDATE_TX_HASHES)
    if source_hashes != expected or receipt_hashes != expected:
        raise Slice04EnrichmentError(f'CANDIDATE_SOURCE_COVERAGE_FAILED:source={sorted(expected-source_hashes)}:receipt={sorted(expected-receipt_hashes)}')
    if len(receipt_rows) != len(CANDIDATE_TX_HASHES):
        raise Slice04EnrichmentError('CANDIDATE_RECEIPT_UNIQUENESS_FAILED')
    blocks = [int(row['block_number']) for row in receipt_rows]
    return {'database_path': str(resolved), 'database_sha256': file_sha256(resolved), 'source_rows': source_rows, 'receipt_rows': receipt_rows, 'minimum_block': min(blocks), 'maximum_block': max(blocks)}


def fetch_transaction(client: RpcClient, tx_hash: str, receipt: dict[str, Any]) -> dict[str, Any]:
    raw = client.call('eth_getTransactionByHash', [tx_hash])
    if not isinstance(raw, dict) or normalize_hash(raw.get('hash')) != tx_hash:
        raise Slice04EnrichmentError(f'TRANSACTION_IDENTITY_INVALID:{tx_hash}')
    block_number = parse_hex_int(raw.get('blockNumber'), 'transaction.blockNumber')
    if block_number != int(receipt['block_number']):
        raise Slice04EnrichmentError(f'TRANSACTION_BLOCK_MISMATCH:{tx_hash}')
    actor = normalize_address(raw.get('from'))
    tx_to = normalize_address(raw.get('to'), allow_empty=True)
    if actor != normalize_address(receipt.get('tx_from_address')) or tx_to != normalize_address(receipt.get('tx_to_address'), allow_empty=True):
        raise Slice04EnrichmentError(f'TRANSACTION_ENDPOINT_MISMATCH:{tx_hash}')
    input_data = validate_hex_data(raw.get('input') or '0x', 'transaction.input')
    if len(input_data) < 10 and input_data != '0x':
        raise Slice04EnrichmentError(f'TRANSACTION_INPUT_TOO_SHORT:{tx_hash}')
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
        'rpc_provider_host': client.last_endpoint_host,
        'transaction_evidence_hash': canonical_hash(raw),
    }


def fetch_token_metadata(client: RpcClient, token: str, block_number: int) -> dict[str, Any]:
    block_tag = hex(block_number)
    responses: dict[str, str] = {}
    provider_hosts: set[str] = set()
    for field, selector in TOKEN_CALLS.items():
        responses[field] = validate_hex_data(client.call('eth_call', [{'to': token, 'data': selector}, block_tag]), f'token.{field}')
        provider_hosts.add(client.last_endpoint_host)
    decimals = decode_uint256(responses['decimals'])
    if decimals > 36:
        raise Slice04EnrichmentError(f'TOKEN_DECIMALS_OUT_OF_BOUNDS:{token}')
    return {'token_address': token, 'block_number': block_number, 'block_tag': block_tag, 'decimals': decimals, 'symbol': decode_abi_string(responses['symbol']), 'name': decode_abi_string(responses['name']), 'provider_hosts': sorted(provider_hosts), 'call_response_hash': canonical_hash(responses)}


def summarize_receipt_logs(receipt_json: Any) -> dict[str, Any]:
    try:
        receipt = json.loads(str(receipt_json or ''))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Slice04EnrichmentError('RECEIPT_JSON_INVALID') from exc
    logs = receipt.get('logs') if isinstance(receipt, dict) else None
    if not isinstance(logs, list):
        raise Slice04EnrichmentError('RECEIPT_LOGS_NOT_LIST')
    address_counts: Counter[str] = Counter()
    topic0_counts: Counter[str] = Counter()
    for log in logs:
        if not isinstance(log, dict):
            continue
        address_counts[normalize_address(log.get('address'))] += 1
        topics = log.get('topics')
        if isinstance(topics, list) and topics:
            topic0_counts[normalize_hash(topics[0])] += 1
    core = {'log_address_counts': dict(sorted(address_counts.items())), 'topic0_counts': dict(sorted(topic0_counts.items()))}
    return {'log_count': sum(address_counts.values()), **core, 'log_summary_hash': canonical_hash(core)}


def build_actor_flow(transaction: dict[str, Any], events: list[dict[str, Any]], metadata_by_token: dict[str, dict[str, Any]]) -> dict[str, Any]:
    actor = transaction['actor']
    net_raw: dict[str, int] = defaultdict(int)
    for event in events:
        token = normalize_address(event['token_address'])
        amount = int(str(event['amount_raw']))
        if amount <= 0:
            raise Slice04EnrichmentError('SOURCE_AMOUNT_INVALID')
        if normalize_address(event['from_address']) == actor:
            net_raw[token] -= amount
        if normalize_address(event['to_address']) == actor:
            net_raw[token] += amount
    rows = []
    for token in sorted(net_raw):
        amount = net_raw[token]
        if amount == 0:
            continue
        metadata = metadata_by_token.get(token)
        if not metadata:
            raise Slice04EnrichmentError(f'METADATA_MISSING_FOR_FLOW_TOKEN:{token}')
        rows.append({'token_address': token, 'symbol': metadata['symbol'], 'decimals': metadata['decimals'], 'net_raw': str(amount), 'net_normalized': ('-' if amount < 0 else '') + normalized_decimal(abs(amount), int(metadata['decimals'])), 'direction': 'IN' if amount > 0 else 'OUT'})
    directions = {row['direction'] for row in rows}
    return {'actor': actor, 'token_flows': rows, 'has_inflow': 'IN' in directions, 'has_outflow': 'OUT' in directions, 'two_sided_actor_flow': directions == {'IN', 'OUT'}, 'flow_hash': canonical_hash(rows)}


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    os.chmod(temp, 0o600)
    json.loads(temp.read_text(encoding='utf-8'))
    temp.replace(path)
    os.chmod(path, 0o600)


def run(database_path: Path, provider_path: Path, output_path: Path) -> dict[str, Any]:
    started = time.monotonic()
    if len(CANDIDATE_TX_HASHES) != 14 or len(set(CANDIDATE_TX_HASHES)) != 14:
        raise Slice04EnrichmentError('CANDIDATE_SET_MUST_BE_14_UNIQUE_HASHES')
    if len(TRACKED_TOKENS) != 3 or len(set(TRACKED_TOKENS)) != 3:
        raise Slice04EnrichmentError('TOKEN_SET_MUST_BE_3_UNIQUE_ADDRESSES')
    evidence = load_source_evidence(database_path)
    provider = json.loads(provider_path.read_text(encoding='utf-8'))
    client = RpcClient(provider)
    if parse_hex_int(client.call('eth_chainId', []), 'eth_chainId') != 56:
        raise Slice04EnrichmentError('RPC_CHAIN_ID_MISMATCH')
    metadata = [fetch_token_metadata(client, normalize_address(token), evidence['maximum_block']) for token in TRACKED_TOKENS]
    metadata_by_token = {row['token_address']: row for row in metadata}
    receipt_by_tx = {normalize_hash(row['tx_hash']): row for row in evidence['receipt_rows']}
    events_by_tx: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence['source_rows']:
        events_by_tx[normalize_hash(row['tx_hash'])].append(row)
    transactions = []
    selector_counts: Counter[str] = Counter()
    tx_to_counts: Counter[str] = Counter()
    two_sided_count = 0
    for tx_hash in CANDIDATE_TX_HASHES:
        receipt = receipt_by_tx[tx_hash]
        tx = fetch_transaction(client, tx_hash, receipt)
        selector_counts[tx['selector']] += 1
        tx_to_counts[tx['tx_to'] or 'CONTRACT_CREATION'] += 1
        flow = build_actor_flow(tx, events_by_tx[tx_hash], metadata_by_token)
        two_sided_count += int(flow['two_sided_actor_flow'])
        transactions.append({**tx, 'receipt_status': int(receipt['receipt_status']), 'gas_used': str(receipt['gas_used']), 'effective_gas_price_wei': str(receipt['effective_gas_price_wei']), 'gas_cost_wei': str(receipt['gas_cost_wei']), 'receipt_evidence_hash': str(receipt['evidence_hash']), 'source_event_count': len(events_by_tx[tx_hash]), 'source_event_hashes': sorted(str(row['evidence_hash']) for row in events_by_tx[tx_hash]), 'actor_flow': flow, 'receipt_log_summary': summarize_receipt_logs(receipt['raw_receipt_json'])})
    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.candidate_enrichment.v1',
        'generated_at_utc': iso_now(),
        'status': 'CANDIDATE_INPUT_AND_TOKEN_METADATA_ENRICHMENT_VERIFIED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {'database_path': evidence['database_path'], 'database_sha256': evidence['database_sha256'], 'minimum_block': evidence['minimum_block'], 'maximum_block': evidence['maximum_block'], 'candidate_transaction_count': len(CANDIDATE_TX_HASHES), 'candidate_source_event_count': len(evidence['source_rows']), 'tracked_token_count': len(TRACKED_TOKENS)},
        'rpc': {'request_count': client.request_count, 'error_count': len(client.errors), 'errors': client.errors[-20:]},
        'token_metadata': metadata,
        'transactions': transactions,
        'summary': {'transaction_input_coverage': len(transactions), 'token_metadata_coverage': len(metadata), 'two_sided_actor_flow_count': two_sided_count, 'selector_counts': dict(sorted(selector_counts.items())), 'tx_to_counts': dict(sorted(tx_to_counts.items())), 'swap_direction_classified': False, 'router_pool_identity_verified': False, 'execution_price_complete': False, 'dex_fee_slippage_tax_complete': False, 'closed_loop_confirmed': False, 'cex_evidence_status': 'UNVERIFIED_OR_UNAVAILABLE', 'next_safe_step': 'ALLOWLISTED_DEX_ROUTER_POOL_AND_SWAP_EVENT_DECODE'},
        'runtime_seconds': round(time.monotonic() - started, 6),
    }
    payload['result_hash'] = canonical_hash(payload)
    atomic_write_json(output_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=DEFAULT_DB)
    parser.add_argument('--provider', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.database, args.provider, args.output)
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'CANDIDATE_TRANSACTION_INPUT_COVERAGE={summary["transaction_input_coverage"]}_OF_14')
    print(f'TOKEN_METADATA_COVERAGE={summary["token_metadata_coverage"]}_OF_3')
    print(f'TWO_SIDED_ACTOR_FLOW_COUNT={summary["two_sided_actor_flow_count"]}')
    print(f'RPC_REQUEST_COUNT={result["rpc"]["request_count"]}')
    print(f'RPC_ERROR_COUNT={result["rpc"]["error_count"]}')
    print(f'RESULT_HASH={result["result_hash"]}')
    print('SWAP_DIRECTION_CLASSIFIED=false')
    print('ROUTER_POOL_IDENTITY_VERIFIED=false')
    print('CLOSED_LOOP_CONFIRMED=false')
    print('NEXT_SAFE_STEP=ALLOWLISTED_DEX_ROUTER_POOL_AND_SWAP_EVENT_DECODE')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
