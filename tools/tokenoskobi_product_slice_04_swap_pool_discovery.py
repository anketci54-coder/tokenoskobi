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
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
DEFAULT_DB = ROOT / 'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
DEFAULT_PROVIDER = ROOT / 'config/era63e_always_on_market_runtime_v1.json'
DEFAULT_ENRICHMENT = Path('/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json')
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/swap_pool_discovery_v1.json')
RECEIPT_TABLE = 'era64j_historical_receipt_cost_enrichment_v1'
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')
ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')
HEX_RE = re.compile(r'^0x(?:[0-9a-f]{2})*$')
V2_SWAP_TOPIC = '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822'
V3_SWAP_TOPIC = '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'
PANCAKE_V3_EXTENDED_SWAP_TOPIC = '0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83'
TOKEN0_SELECTOR = '0x0dfe1681'
TOKEN1_SELECTOR = '0xd21220a7'
FACTORY_SELECTOR = '0xc45a0155'
FEE_SELECTOR = '0xddca3f43'
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


class Slice04SwapDiscoveryError(RuntimeError):
    pass


def iso_now() -> str:
    from datetime import datetime, timezone
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
        raise Slice04SwapDiscoveryError('INVALID_HASH')
    return text


def normalize_address(value: Any, *, allow_empty: bool = False) -> str:
    text = str(value or '').strip().lower()
    if allow_empty and text == '':
        return ''
    if ADDRESS_RE.fullmatch(text) is None:
        raise Slice04SwapDiscoveryError('INVALID_ADDRESS')
    return text


def validate_hex_data(value: Any, field: str) -> str:
    text = str(value or '').strip().lower()
    if HEX_RE.fullmatch(text) is None:
        raise Slice04SwapDiscoveryError(f'{field}:INVALID_HEX_DATA')
    return text


def parse_hex_int(value: Any, field: str) -> int:
    text = str(value or '').strip().lower()
    if not text.startswith('0x'):
        raise Slice04SwapDiscoveryError(f'{field}:NOT_HEX')
    try:
        number = int(text, 16)
    except ValueError as exc:
        raise Slice04SwapDiscoveryError(f'{field}:INVALID_HEX') from exc
    if number < 0:
        raise Slice04SwapDiscoveryError(f'{field}:NEGATIVE')
    return number


def split_words(data: str, expected_words: int, field: str) -> list[str]:
    value = validate_hex_data(data, field)
    payload = value[2:]
    if len(payload) != expected_words * 64:
        raise Slice04SwapDiscoveryError(
            f'{field}:WORD_COUNT_MISMATCH:expected={expected_words}:actual={len(payload)//64}'
        )
    return [payload[index:index + 64] for index in range(0, len(payload), 64)]


def decode_uint_word(word: str) -> int:
    if len(word) != 64:
        raise Slice04SwapDiscoveryError('UINT_WORD_LENGTH_INVALID')
    return int(word, 16)


def decode_int_word(word: str) -> int:
    value = decode_uint_word(word)
    return value - (1 << 256) if value >= (1 << 255) else value


def decode_signed_nbit_word(word: str, bits: int) -> int:
    if bits < 1 or bits > 256:
        raise Slice04SwapDiscoveryError('SIGNED_BITS_INVALID')
    value = decode_uint_word(word)
    mask = (1 << bits) - 1
    narrowed = value & mask
    sign = 1 << (bits - 1)
    return narrowed - (1 << bits) if narrowed & sign else narrowed


def topic_address(topic: Any) -> str:
    value = normalize_hash(topic)
    return normalize_address('0x' + value[-40:])


def decode_address_result(value: Any, field: str) -> str:
    data = validate_hex_data(value, field)
    payload = data[2:]
    if len(payload) < 64:
        raise Slice04SwapDiscoveryError(f'{field}:ADDRESS_RESPONSE_TOO_SHORT')
    return normalize_address('0x' + payload[-40:])


def decode_uint_result(value: Any, field: str) -> int:
    data = validate_hex_data(value, field)
    payload = data[2:]
    if len(payload) < 64:
        raise Slice04SwapDiscoveryError(f'{field}:UINT_RESPONSE_TOO_SHORT')
    return int(payload[:64], 16)


def validate_provider_config(config: dict[str, Any]) -> tuple[list[str], set[str], float, int]:
    if config.get('schema') != 'tokenoskobi.era63e.always_on_market_runtime_config.v1':
        raise Slice04SwapDiscoveryError('PROVIDER_SCHEMA_INVALID')
    rpc = config.get('rpc')
    if not isinstance(rpc, dict) or int(rpc.get('chain_id', 0)) != 56:
        raise Slice04SwapDiscoveryError('PROVIDER_CHAIN_INVALID')
    endpoints = [str(item).rstrip('/') for item in rpc.get('endpoints') or []]
    allowed_hosts = {str(item).lower() for item in rpc.get('allowed_hosts') or []}
    if len(endpoints) < 2 or len(allowed_hosts) < 2:
        raise Slice04SwapDiscoveryError('PROVIDER_REDUNDANCY_INSUFFICIENT')
    for endpoint in endpoints:
        parsed = urllib.parse.urlparse(endpoint)
        if parsed.scheme != 'https' or str(parsed.hostname or '').lower() not in allowed_hosts:
            raise Slice04SwapDiscoveryError('PROVIDER_ENDPOINT_NOT_ALLOWLISTED_HTTPS')
    timeout = float(rpc.get('request_timeout_sec', 8))
    retries = int(rpc.get('retries_per_endpoint', 1))
    if timeout < 2 or timeout > 30 or retries < 0 or retries > 2:
        raise Slice04SwapDiscoveryError('PROVIDER_LIMITS_INVALID')
    return endpoints, allowed_hosts, timeout, retries


class RpcClient:
    ALLOWED_METHODS = {'eth_chainId', 'eth_call', 'eth_getCode'}

    def __init__(self, config: dict[str, Any], *, maximum_requests: int = 300, maximum_seconds: float = 300.0):
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
            raise Slice04SwapDiscoveryError(f'RPC_METHOD_NOT_ALLOWLISTED:{method}')
        if self.request_count >= self.maximum_requests:
            raise Slice04SwapDiscoveryError('RPC_REQUEST_BUDGET_EXCEEDED')
        if time.monotonic() - self.started > self.maximum_seconds:
            raise Slice04SwapDiscoveryError('RPC_RUNTIME_BUDGET_EXCEEDED')
        last_error = ''
        count = len(self.endpoints)
        for offset in range(count):
            endpoint = self.endpoints[(self.endpoint_index + offset) % count]
            parsed = urllib.parse.urlparse(endpoint)
            host = str(parsed.hostname or '').lower()
            if parsed.scheme != 'https' or host not in self.allowed_hosts:
                continue
            for attempt in range(self.retries + 1):
                if self.request_count >= self.maximum_requests:
                    raise Slice04SwapDiscoveryError('RPC_REQUEST_BUDGET_EXCEEDED')
                self.request_count += 1
                payload = json.dumps(
                    {'jsonrpc': '2.0', 'id': self.request_count, 'method': method, 'params': params},
                    separators=(',', ':'),
                ).encode('utf-8')
                request = urllib.request.Request(
                    endpoint,
                    data=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'Tokenoskobi-Product-Slice-04/1.0 swap-pool-discovery',
                    },
                    method='POST',
                )
                try:
                    with urllib.request.urlopen(request, timeout=self.timeout) as response:
                        body = json.loads(response.read().decode('utf-8'))
                    if not isinstance(body, dict) or body.get('error') is not None or 'result' not in body:
                        error = body.get('error') if isinstance(body, dict) else 'NOT_OBJECT'
                        raise Slice04SwapDiscoveryError(f'RPC_RESPONSE_INVALID:{error}')
                    self.endpoint_index = (self.endpoint_index + offset + 1) % count
                    self.last_endpoint_host = host
                    return body['result']
                except (
                    urllib.error.URLError,
                    urllib.error.HTTPError,
                    TimeoutError,
                    OSError,
                    json.JSONDecodeError,
                    Slice04SwapDiscoveryError,
                ) as exc:
                    last_error = f'{type(exc).__name__}:{exc}'
                    self.errors.append(f'{host}:{method}:{last_error}')
                    if attempt < self.retries:
                        time.sleep(min(0.25 * (2 ** attempt), 1.0))
        raise Slice04SwapDiscoveryError(f'ALL_RPC_ENDPOINTS_FAILED:{method}:{last_error}')


def load_enrichment(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise Slice04SwapDiscoveryError('ENRICHMENT_FILE_MISSING')
    payload = json.loads(path.read_text(encoding='utf-8'))
    if payload.get('schema') != 'tokenoskobi.product_slice_04.candidate_enrichment.v1':
        raise Slice04SwapDiscoveryError('ENRICHMENT_SCHEMA_INVALID')
    if payload.get('status') != 'CANDIDATE_INPUT_AND_TOKEN_METADATA_ENRICHMENT_VERIFIED':
        raise Slice04SwapDiscoveryError('ENRICHMENT_STATUS_INVALID')
    transactions = payload.get('transactions')
    metadata = payload.get('token_metadata')
    if not isinstance(transactions, list) or len(transactions) != 14:
        raise Slice04SwapDiscoveryError('ENRICHMENT_TRANSACTION_COUNT_INVALID')
    if not isinstance(metadata, list) or len(metadata) != 3:
        raise Slice04SwapDiscoveryError('ENRICHMENT_METADATA_COUNT_INVALID')
    tx_map: dict[str, dict[str, Any]] = {}
    for item in transactions:
        tx_hash = normalize_hash(item.get('tx_hash'))
        if tx_hash in tx_map:
            raise Slice04SwapDiscoveryError('ENRICHMENT_DUPLICATE_TRANSACTION')
        tx_map[tx_hash] = item
    metadata_map: dict[str, dict[str, Any]] = {}
    for item in metadata:
        token = normalize_address(item.get('token_address'))
        if token in metadata_map:
            raise Slice04SwapDiscoveryError('ENRICHMENT_DUPLICATE_TOKEN')
        metadata_map[token] = item
    return {
        'tx_map': tx_map,
        'metadata_map': metadata_map,
        'result_hash': str(payload.get('result_hash') or ''),
    }


def load_receipts(database_path: Path, tx_hashes: list[str]) -> dict[str, dict[str, Any]]:
    resolved = database_path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file() or resolved.stat().st_size <= 0:
        raise Slice04SwapDiscoveryError('SOURCE_DATABASE_INVALID')
    uri = f'file:{resolved}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04SwapDiscoveryError('SOURCE_DATABASE_INTEGRITY_FAILED')
        tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if RECEIPT_TABLE not in tables:
            raise Slice04SwapDiscoveryError('RECEIPT_TABLE_MISSING')
        placeholders = ','.join('?' for _ in tx_hashes)
        rows = [
            dict(row)
            for row in conn.execute(
                f'''SELECT tx_hash,block_number,receipt_status,gas_cost_wei,
                           tx_from_address,tx_to_address,evidence_hash,raw_receipt_json
                    FROM {RECEIPT_TABLE}
                    WHERE tx_hash IN ({placeholders})
                    ORDER BY block_number,transaction_index,tx_hash''',
                tx_hashes,
            )
        ]
    finally:
        conn.close()
    result = {normalize_hash(row['tx_hash']): row for row in rows}
    if set(result) != set(tx_hashes) or len(rows) != len(tx_hashes):
        raise Slice04SwapDiscoveryError('RECEIPT_COVERAGE_OR_UNIQUENESS_FAILED')
    return result


def decode_v2_swap(log: dict[str, Any]) -> dict[str, Any]:
    topics = log.get('topics')
    if not isinstance(topics, list) or len(topics) != 3:
        raise Slice04SwapDiscoveryError('V2_SWAP_TOPICS_INVALID')
    words = split_words(str(log.get('data') or ''), 4, 'v2_swap.data')
    amount0_in, amount1_in, amount0_out, amount1_out = [decode_uint_word(word) for word in words]
    if amount0_in + amount1_in <= 0 or amount0_out + amount1_out <= 0:
        raise Slice04SwapDiscoveryError('V2_SWAP_AMOUNT_DIRECTION_INVALID')
    if amount0_in > 0 and amount1_out > 0 and amount1_in == 0 and amount0_out == 0:
        input_side, output_side = 0, 1
    elif amount1_in > 0 and amount0_out > 0 and amount0_in == 0 and amount1_out == 0:
        input_side, output_side = 1, 0
    else:
        input_side, output_side = None, None
    return {
        'event_type': 'V2_SWAP',
        'sender': topic_address(topics[1]),
        'recipient': topic_address(topics[2]),
        'amount0_in_raw': str(amount0_in),
        'amount1_in_raw': str(amount1_in),
        'amount0_out_raw': str(amount0_out),
        'amount1_out_raw': str(amount1_out),
        'input_side': input_side,
        'output_side': output_side,
        'direction_unambiguous': input_side is not None,
    }


def decode_v3_swap(log: dict[str, Any], *, extended: bool) -> dict[str, Any]:
    topics = log.get('topics')
    if not isinstance(topics, list) or len(topics) != 3:
        raise Slice04SwapDiscoveryError('V3_SWAP_TOPICS_INVALID')
    words = split_words(str(log.get('data') or ''), 7 if extended else 5, 'v3_swap.data')
    amount0 = decode_int_word(words[0])
    amount1 = decode_int_word(words[1])
    if amount0 == 0 or amount1 == 0 or (amount0 > 0) == (amount1 > 0):
        raise Slice04SwapDiscoveryError('V3_SWAP_AMOUNT_DIRECTION_INVALID')
    result = {
        'event_type': 'PANCAKE_V3_EXTENDED_SWAP' if extended else 'V3_SWAP',
        'sender': topic_address(topics[1]),
        'recipient': topic_address(topics[2]),
        'amount0_delta_raw': str(amount0),
        'amount1_delta_raw': str(amount1),
        'sqrt_price_x96': str(decode_uint_word(words[2])),
        'liquidity': str(decode_uint_word(words[3])),
        'tick': decode_signed_nbit_word(words[4], 24),
        'input_side': 0 if amount0 > 0 else 1,
        'output_side': 1 if amount0 > 0 else 0,
        'direction_unambiguous': True,
    }
    if extended:
        result['protocol_fees_token0_raw'] = str(decode_uint_word(words[5]))
        result['protocol_fees_token1_raw'] = str(decode_uint_word(words[6]))
    return result


def decode_swap_log(log: dict[str, Any]) -> dict[str, Any] | None:
    topics = log.get('topics')
    if not isinstance(topics, list) or not topics:
        return None
    topic0 = normalize_hash(topics[0])
    if topic0 == V2_SWAP_TOPIC:
        return decode_v2_swap(log)
    if topic0 == V3_SWAP_TOPIC:
        return decode_v3_swap(log, extended=False)
    if topic0 == PANCAKE_V3_EXTENDED_SWAP_TOPIC:
        return decode_v3_swap(log, extended=True)
    return None


def eth_call_address(client: RpcClient, contract: str, selector: str, field: str) -> str:
    result = client.call('eth_call', [{'to': contract, 'data': selector}, 'latest'])
    return decode_address_result(result, field)


def eth_call_uint(client: RpcClient, contract: str, selector: str, field: str) -> int:
    result = client.call('eth_call', [{'to': contract, 'data': selector}, 'latest'])
    return decode_uint_result(result, field)


def introspect_pool(client: RpcClient, pool: str, event_type: str) -> dict[str, Any]:
    code = validate_hex_data(client.call('eth_getCode', [pool, 'latest']), 'pool.code')
    if code in {'0x', '0x00'}:
        raise Slice04SwapDiscoveryError(f'POOL_CODE_MISSING:{pool}')
    token0 = eth_call_address(client, pool, TOKEN0_SELECTOR, 'pool.token0')
    token1 = eth_call_address(client, pool, TOKEN1_SELECTOR, 'pool.token1')
    factory = eth_call_address(client, pool, FACTORY_SELECTOR, 'pool.factory')
    if token0 == token1:
        raise Slice04SwapDiscoveryError(f'POOL_TOKEN_IDENTITY_INVALID:{pool}')
    fee = None
    fee_status = 'NOT_APPLICABLE'
    if event_type in {'V3_SWAP', 'PANCAKE_V3_EXTENDED_SWAP'}:
        try:
            fee = eth_call_uint(client, pool, FEE_SELECTOR, 'pool.fee')
            if fee < 0 or fee > 1_000_000:
                raise Slice04SwapDiscoveryError(f'POOL_FEE_OUT_OF_BOUNDS:{pool}')
            fee_status = 'VERIFIED'
        except Slice04SwapDiscoveryError:
            fee_status = 'UNAVAILABLE_FAIL_CLOSED'
    return {
        'pool_address': pool,
        'contract_code_bytes': max(0, (len(code) - 2) // 2),
        'token0': token0,
        'token1': token1,
        'factory': factory,
        'fee': fee,
        'fee_status': fee_status,
        'identity_block_tag': 'latest',
        'identity_temporal_limitation': 'POOL_IDENTITY_READ_AT_LATEST_EVENT_EVIDENCE_IS_HISTORICAL',
        'protocol_identity': 'UNVERIFIED_PENDING_FACTORY_ALLOWLIST_MATCH',
        'rpc_provider_host': client.last_endpoint_host,
    }


def apply_pool_tokens(decoded: dict[str, Any], identity: dict[str, Any], metadata_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    side_tokens = [identity['token0'], identity['token1']]
    input_side = decoded.get('input_side')
    output_side = decoded.get('output_side')
    result = dict(decoded)
    result['input_token'] = side_tokens[input_side] if input_side in {0, 1} else ''
    result['output_token'] = side_tokens[output_side] if output_side in {0, 1} else ''
    result['pool_tokens'] = [
        {
            'side': index,
            'token_address': token,
            'tracked': token in metadata_map,
            'symbol': str(metadata_map[token].get('symbol')) if token in metadata_map else 'UNKNOWN',
            'decimals': int(metadata_map[token].get('decimals')) if token in metadata_map else None,
        }
        for index, token in enumerate(side_tokens)
    ]
    return result


def actor_flow_pair_match(tx: dict[str, Any], token0: str, token1: str) -> dict[str, Any]:
    flow = tx.get('actor_flow')
    rows = flow.get('token_flows') if isinstance(flow, dict) else None
    if not isinstance(rows, list):
        return {'status': 'ACTOR_FLOW_MISSING', 'matched': False, 'actor_flow_tokens': []}
    tokens = sorted({normalize_address(row.get('token_address')) for row in rows})
    matched = bool(tokens) and set(tokens).issubset({token0, token1})
    return {
        'status': 'EXACT_PAIR' if matched else 'PARTIAL_OR_NON_PAIR',
        'matched': matched,
        'actor_flow_tokens': tokens,
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


def run(database_path: Path, provider_path: Path, enrichment_path: Path, output_path: Path) -> dict[str, Any]:
    started = time.monotonic()
    enrichment = load_enrichment(enrichment_path)
    tx_hashes = sorted(enrichment['tx_map'])
    receipts = load_receipts(database_path, tx_hashes)
    provider = json.loads(provider_path.read_text(encoding='utf-8'))
    client = RpcClient(provider)
    if parse_hex_int(client.call('eth_chainId', []), 'eth_chainId') != 56:
        raise Slice04SwapDiscoveryError('RPC_CHAIN_ID_MISMATCH')
    pool_cache: dict[tuple[str, str], dict[str, Any]] = {}
    events: list[dict[str, Any]] = []
    without_swap: list[str] = []
    event_type_counts: Counter[str] = Counter()
    factory_counts: Counter[str] = Counter()
    exact_pair_match_count = 0
    for tx_hash in tx_hashes:
        receipt_row = receipts[tx_hash]
        receipt = json.loads(str(receipt_row.get('raw_receipt_json') or ''))
        logs = receipt.get('logs') if isinstance(receipt, dict) else None
        if not isinstance(logs, list):
            raise Slice04SwapDiscoveryError(f'RECEIPT_LOGS_INVALID:{tx_hash}')
        recognized = 0
        for log_position, log in enumerate(logs):
            if not isinstance(log, dict):
                continue
            decoded = decode_swap_log(log)
            if decoded is None:
                continue
            recognized += 1
            pool = normalize_address(log.get('address'))
            cache_key = (pool, decoded['event_type'])
            if cache_key not in pool_cache:
                pool_cache[cache_key] = introspect_pool(client, pool, decoded['event_type'])
            identity = pool_cache[cache_key]
            decoded = apply_pool_tokens(decoded, identity, enrichment['metadata_map'])
            flow_match = actor_flow_pair_match(enrichment['tx_map'][tx_hash], identity['token0'], identity['token1'])
            exact_pair_match_count += int(flow_match['matched'])
            event = {
                'tx_hash': tx_hash,
                'block_number': int(receipt_row['block_number']),
                'receipt_log_position': log_position,
                'receipt_log_index': parse_hex_int(log.get('logIndex') or '0x0', 'log.logIndex'),
                'pool_identity': identity,
                'swap': decoded,
                'actor': normalize_address(enrichment['tx_map'][tx_hash].get('actor')),
                'transaction_target': normalize_address(enrichment['tx_map'][tx_hash].get('tx_to'), allow_empty=True),
                'actor_flow_pair_match': flow_match,
                'receipt_evidence_hash': str(receipt_row.get('evidence_hash') or ''),
                'log_evidence_hash': canonical_hash(log),
            }
            event_type_counts[decoded['event_type']] += 1
            factory_counts[identity['factory']] += 1
            events.append(event)
        if recognized == 0:
            without_swap.append(tx_hash)
    distinct_pools = sorted({event['pool_identity']['pool_address'] for event in events})
    transactions_with_swap = sorted({event['tx_hash'] for event in events})
    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.swap_pool_discovery.v1',
        'generated_at_utc': iso_now(),
        'status': 'SWAP_POOL_DISCOVERY_COMPLETED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {
            'database_path': str(database_path.resolve()),
            'database_sha256': file_sha256(database_path),
            'candidate_enrichment_path': str(enrichment_path),
            'candidate_enrichment_sha256': file_sha256(enrichment_path),
            'candidate_enrichment_result_hash': enrichment['result_hash'],
            'candidate_transaction_count': len(tx_hashes),
        },
        'rpc': {'request_count': client.request_count, 'error_count': len(client.errors), 'errors': client.errors[-30:]},
        'recognized_topics': {
            'v2_swap': V2_SWAP_TOPIC,
            'v3_swap': V3_SWAP_TOPIC,
            'pancake_v3_extended_swap': PANCAKE_V3_EXTENDED_SWAP_TOPIC,
        },
        'events': events,
        'summary': {
            'recognized_swap_event_count': len(events),
            'candidate_transaction_with_swap_count': len(transactions_with_swap),
            'candidate_transaction_without_recognized_swap_count': len(without_swap),
            'candidate_transactions_without_recognized_swap': without_swap,
            'distinct_pool_count': len(distinct_pools),
            'distinct_pools': distinct_pools,
            'event_type_counts': dict(sorted(event_type_counts.items())),
            'factory_counts': dict(sorted(factory_counts.items())),
            'direction_decoded_event_count': sum(int(event['swap']['direction_unambiguous']) for event in events),
            'exact_actor_flow_pair_match_count': exact_pair_match_count,
            'factory_allowlist_locked': False,
            'protocol_identity_verified': False,
            'router_identity_verified': False,
            'closed_loop_confirmed': False,
            'cex_evidence_status': 'UNVERIFIED_OR_UNAVAILABLE',
            'next_safe_step': 'VERIFY_FACTORY_ADDRESSES_AND_SELECT_FIRST_REAL_SWAP_CHAIN',
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
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.database, args.provider, args.enrichment, args.output)
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'RECOGNIZED_SWAP_EVENT_COUNT={summary["recognized_swap_event_count"]}')
    print(f'CANDIDATE_TRANSACTION_WITH_SWAP_COUNT={summary["candidate_transaction_with_swap_count"]}')
    print(f'DISTINCT_POOL_COUNT={summary["distinct_pool_count"]}')
    print(f'DIRECTION_DECODED_EVENT_COUNT={summary["direction_decoded_event_count"]}')
    print(f'EXACT_ACTOR_FLOW_PAIR_MATCH_COUNT={summary["exact_actor_flow_pair_match_count"]}')
    print('FACTORY_COUNTS=' + json.dumps(summary['factory_counts'], sort_keys=True, separators=(',', ':')))
    print('EVENT_TYPE_COUNTS=' + json.dumps(summary['event_type_counts'], sort_keys=True, separators=(',', ':')))
    print(f'RPC_REQUEST_COUNT={result["rpc"]["request_count"]}')
    print(f'RPC_ERROR_COUNT={result["rpc"]["error_count"]}')
    print(f'RESULT_HASH={result["result_hash"]}')
    print('FACTORY_ALLOWLIST_LOCKED=false')
    print('PROTOCOL_IDENTITY_VERIFIED=false')
    print('ROUTER_IDENTITY_VERIFIED=false')
    print('CLOSED_LOOP_CONFIRMED=false')
    print('NEXT_SAFE_STEP=VERIFY_FACTORY_ADDRESSES_AND_SELECT_FIRST_REAL_SWAP_CHAIN')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
