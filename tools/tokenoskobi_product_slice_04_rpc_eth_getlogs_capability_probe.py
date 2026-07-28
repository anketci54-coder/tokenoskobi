#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
DEFAULT_DB = ROOT / 'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
DEFAULT_PROVIDER = ROOT / 'config/era63e_always_on_market_runtime_v1.json'
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/rpc_eth_getlogs_capability_probe_v1.json')
BASE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_HISTORICAL_REVERSE_SCAN_BASE_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_targeted_historical_reverse_scan.py',
    )
)

SOURCE_TABLE = 'era64i_historical_wallet_transfer_staging_v1'
EXPECTED_DB_HASH = '99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_ENDPOINTS = (
    'https://bsc-dataseed.bnbchain.org',
    'https://bsc-dataseed-public.bnbchain.org',
    'https://bsc-dataseed.nariox.org',
    'https://bsc-dataseed.defibit.io',
)
FAILED_HISTORICAL_BLOCK = 111790635
MAX_TOTAL_REQUESTS = 24

AUTHORITY = {
    'network_access': True,
    'network_mode': 'READ_ONLY_ALLOWLISTED_BSC_RPC_CAPABILITY_PROBE',
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


class Slice04RpcCapabilityProbeError(RuntimeError):
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
    if len(text) != 42 or not text.startswith('0x'):
        raise Slice04RpcCapabilityProbeError('INVALID_EVM_ADDRESS')
    try:
        int(text[2:], 16)
    except ValueError as exc:
        raise Slice04RpcCapabilityProbeError('INVALID_EVM_ADDRESS') from exc
    return text


def normalize_hash(value: Any) -> str:
    text = str(value or '').strip().lower()
    if len(text) != 66 or not text.startswith('0x'):
        raise Slice04RpcCapabilityProbeError('INVALID_HASH')
    try:
        int(text[2:], 16)
    except ValueError as exc:
        raise Slice04RpcCapabilityProbeError('INVALID_HASH') from exc
    return text


def topic_address(value: Any) -> str:
    address = normalize_address(value)
    return '0x' + ('0' * 24) + address[2:]


def parse_hex_int(value: Any, field: str) -> int:
    text = str(value or '').strip().lower()
    if not text.startswith('0x'):
        raise Slice04RpcCapabilityProbeError(f'{field}:INVALID_HEX')
    try:
        number = int(text, 16)
    except ValueError as exc:
        raise Slice04RpcCapabilityProbeError(f'{field}:INVALID_HEX') from exc
    if number < 0:
        raise Slice04RpcCapabilityProbeError(f'{field}:NEGATIVE')
    return number


def load_base_module() -> Any:
    if not BASE_PATH.is_file():
        raise Slice04RpcCapabilityProbeError('BASE_MODULE_MISSING')
    spec = importlib.util.spec_from_file_location('product_slice_04_historical_reverse_scan_probe_base', BASE_PATH)
    if spec is None or spec.loader is None:
        raise Slice04RpcCapabilityProbeError('BASE_MODULE_IMPORT_FAILED')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_provider(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if payload.get('schema') != 'tokenoskobi.era63e.always_on_market_runtime_config.v1':
        raise Slice04RpcCapabilityProbeError('PROVIDER_SCHEMA_INVALID')
    rpc = payload.get('rpc')
    if not isinstance(rpc, dict) or int(rpc.get('chain_id', 0)) != 56:
        raise Slice04RpcCapabilityProbeError('PROVIDER_CHAIN_INVALID')
    endpoints = tuple(str(item).rstrip('/') for item in rpc.get('endpoints') or [])
    if endpoints != EXPECTED_ENDPOINTS:
        raise Slice04RpcCapabilityProbeError('PROVIDER_ENDPOINT_SET_CHANGED')
    allowed_hosts = set(str(item).lower() for item in rpc.get('allowed_hosts') or [])
    for endpoint in endpoints:
        parsed = urllib.parse.urlparse(endpoint)
        if parsed.scheme != 'https' or str(parsed.hostname or '').lower() not in allowed_hosts:
            raise Slice04RpcCapabilityProbeError('PROVIDER_ENDPOINT_NOT_ALLOWLISTED_HTTPS')
    timeout = min(max(float(rpc.get('request_timeout_sec', 8)), 2.0), 20.0)
    return {'endpoints': list(endpoints), 'allowed_hosts': sorted(allowed_hosts), 'timeout': timeout}


def load_known_event(database_path: Path) -> dict[str, Any]:
    resolved = database_path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file() or file_sha256(resolved) != EXPECTED_DB_HASH:
        raise Slice04RpcCapabilityProbeError('SOURCE_DATABASE_INVALID')
    conn = sqlite3.connect(f'file:{resolved}?mode=ro&immutable=1', uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04RpcCapabilityProbeError('SOURCE_DATABASE_INTEGRITY_FAILED')
        row = conn.execute(
            f'''SELECT token_address,from_address,to_address,amount_raw,tx_hash,log_index,block_number,block_hash
                FROM {SOURCE_TABLE}
                ORDER BY block_number,tx_hash,log_index
                LIMIT 1'''
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise Slice04RpcCapabilityProbeError('KNOWN_EVENT_MISSING')
    result = dict(row)
    result['token_address'] = normalize_address(result['token_address'])
    result['from_address'] = normalize_address(result['from_address'])
    result['to_address'] = normalize_address(result['to_address'])
    result['tx_hash'] = normalize_hash(result['tx_hash'])
    result['block_hash'] = normalize_hash(result['block_hash'])
    result['amount_raw'] = str(int(str(result['amount_raw'])))
    result['log_index'] = int(result['log_index'])
    result['block_number'] = int(result['block_number'])
    return result


def load_failed_anchor(base: Any) -> dict[str, Any]:
    source_rows, receipt_rows, _ = base.load_database(base.DEFAULT_DB)
    anchors = base.select_anchors(base.build_eligible_records(source_rows, receipt_rows))
    if not anchors:
        raise Slice04RpcCapabilityProbeError('ANCHOR_SCOPE_EMPTY')
    anchor = dict(anchors[0])
    anchor['actor'] = normalize_address(anchor['actor'])
    anchor['token'] = normalize_address(anchor['token'])
    if anchor.get('missing_direction') not in {'IN', 'OUT'}:
        raise Slice04RpcCapabilityProbeError('ANCHOR_DIRECTION_INVALID')
    return anchor


def known_event_filter(base: Any, event: dict[str, Any]) -> dict[str, Any]:
    block = int(event['block_number'])
    return {
        'address': event['token_address'],
        'fromBlock': hex(block),
        'toBlock': hex(block),
        'topics': [
            base.TRANSFER_TOPIC,
            topic_address(event['from_address']),
            topic_address(event['to_address']),
        ],
    }


def historical_anchor_filter(base: Any, anchor: dict[str, Any]) -> dict[str, Any]:
    return base.build_log_filter(anchor, FAILED_HISTORICAL_BLOCK, FAILED_HISTORICAL_BLOCK)


def sanitize_error(value: Any) -> str:
    text = str(value or '').strip().replace('\n', ' ')
    return text[:500]


def rpc_call(endpoint: str, method: str, params: list[Any], timeout: float, request_id: int) -> dict[str, Any]:
    body = json.dumps(
        {'jsonrpc': '2.0', 'id': request_id, 'method': method, 'params': params},
        separators=(',', ':'),
    ).encode('utf-8')
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Tokenoskobi-Product-Slice-04/1.0 rpc-capability-probe',
        },
        method='POST',
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode('utf-8'))
        elapsed_ms = round((time.monotonic() - started) * 1000, 3)
        if not isinstance(payload, dict):
            return {'ok': False, 'elapsed_ms': elapsed_ms, 'error': 'RPC_RESPONSE_NOT_OBJECT'}
        if payload.get('error') is not None:
            return {'ok': False, 'elapsed_ms': elapsed_ms, 'error': sanitize_error(payload.get('error'))}
        if 'result' not in payload:
            return {'ok': False, 'elapsed_ms': elapsed_ms, 'error': 'RPC_RESULT_MISSING'}
        return {'ok': True, 'elapsed_ms': elapsed_ms, 'result': payload['result']}
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        elapsed_ms = round((time.monotonic() - started) * 1000, 3)
        return {'ok': False, 'elapsed_ms': elapsed_ms, 'error': sanitize_error(f'{type(exc).__name__}:{exc}')}


def summarize_log_result(probe: dict[str, Any], expected_event: dict[str, Any] | None = None) -> dict[str, Any]:
    if not probe.get('ok'):
        return {'ok': False, 'count': None, 'exact_known_event_found': False, 'error': probe.get('error')}
    result = probe.get('result')
    if not isinstance(result, list):
        return {'ok': False, 'count': None, 'exact_known_event_found': False, 'error': 'ETH_GET_LOGS_RESULT_NOT_LIST'}
    exact = False
    if expected_event is not None:
        for item in result:
            if not isinstance(item, dict):
                continue
            try:
                tx_hash = normalize_hash(item.get('transactionHash'))
                log_index = parse_hex_int(item.get('logIndex'), 'logIndex')
            except Slice04RpcCapabilityProbeError:
                continue
            if tx_hash == expected_event['tx_hash'] and log_index == expected_event['log_index']:
                exact = True
                break
    return {'ok': True, 'count': len(result), 'exact_known_event_found': exact, 'error': None}


def classify_endpoint(result: dict[str, Any]) -> str:
    if not result['chain_id']['ok'] or result['chain_id'].get('value') != 56:
        return 'CHAIN_UNAVAILABLE_OR_MISMATCH'
    if not result['known_block']['ok']:
        return 'KNOWN_BLOCK_UNAVAILABLE'
    known = result['known_exact_log']
    historical = result['historical_single_actor_single_block']
    if not known['ok']:
        return 'ETH_GETLOGS_UNUSABLE_ON_KNOWN_EXACT_EVENT'
    if not known['exact_known_event_found']:
        return 'ETH_GETLOGS_KNOWN_EVENT_NOT_RETURNED'
    if not historical['ok']:
        return 'ETH_GETLOGS_KNOWN_EVENT_OK_HISTORICAL_FILTER_REJECTED'
    return 'ETH_GETLOGS_AVAILABLE_FOR_EXACT_HISTORICAL_FILTER'


def classify_overall(endpoint_results: list[dict[str, Any]]) -> str:
    classes = {item['classification'] for item in endpoint_results}
    if 'ETH_GETLOGS_AVAILABLE_FOR_EXACT_HISTORICAL_FILTER' in classes:
        return 'AT_LEAST_ONE_CURRENT_ENDPOINT_SUPPORTS_REQUIRED_ETH_GETLOGS'
    if 'ETH_GETLOGS_KNOWN_EVENT_OK_HISTORICAL_FILTER_REJECTED' in classes:
        return 'CURRENT_ENDPOINT_SET_HAS_HISTORICAL_FILTER_OR_DEPTH_RESTRICTION'
    if 'ETH_GETLOGS_KNOWN_EVENT_NOT_RETURNED' in classes:
        return 'CURRENT_ENDPOINT_SET_RETURNS_INCOMPLETE_KNOWN_LOG_EVIDENCE'
    return 'CURRENT_ENDPOINT_SET_ETH_GETLOGS_UNUSABLE'


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
    base = load_base_module()
    provider = load_provider(provider_path)
    known_event = load_known_event(database_path)
    anchor = load_failed_anchor(base)
    known_filter = known_event_filter(base, known_event)
    historical_filter = historical_anchor_filter(base, anchor)

    request_id = 0
    endpoint_results: list[dict[str, Any]] = []
    for endpoint in provider['endpoints']:
        parsed = urllib.parse.urlparse(endpoint)
        host = str(parsed.hostname or '').lower()
        request_id += 1
        chain_probe = rpc_call(endpoint, 'eth_chainId', [], provider['timeout'], request_id)
        chain_result = {
            'ok': bool(chain_probe.get('ok')),
            'value': parse_hex_int(chain_probe['result'], 'chainId') if chain_probe.get('ok') else None,
            'error': None if chain_probe.get('ok') else chain_probe.get('error'),
            'elapsed_ms': chain_probe.get('elapsed_ms'),
        }

        request_id += 1
        block_probe = rpc_call(endpoint, 'eth_getBlockByNumber', [hex(known_event['block_number']), False], provider['timeout'], request_id)
        block_ok = bool(block_probe.get('ok') and isinstance(block_probe.get('result'), dict))
        block_result = {
            'ok': block_ok,
            'number': parse_hex_int(block_probe['result'].get('number'), 'knownBlock.number') if block_ok else None,
            'hash': normalize_hash(block_probe['result'].get('hash')) if block_ok else None,
            'error': None if block_ok else block_probe.get('error') or 'KNOWN_BLOCK_RESULT_INVALID',
            'elapsed_ms': block_probe.get('elapsed_ms'),
        }

        request_id += 1
        known_probe_raw = rpc_call(endpoint, 'eth_getLogs', [known_filter], provider['timeout'], request_id)
        known_probe = summarize_log_result(known_probe_raw, known_event)
        known_probe['elapsed_ms'] = known_probe_raw.get('elapsed_ms')

        request_id += 1
        historical_probe_raw = rpc_call(endpoint, 'eth_getLogs', [historical_filter], provider['timeout'], request_id)
        historical_probe = summarize_log_result(historical_probe_raw)
        historical_probe['elapsed_ms'] = historical_probe_raw.get('elapsed_ms')

        endpoint_result = {
            'endpoint': endpoint,
            'host': host,
            'chain_id': chain_result,
            'known_block': block_result,
            'known_exact_log': known_probe,
            'historical_single_actor_single_block': historical_probe,
        }
        endpoint_result['classification'] = classify_endpoint(endpoint_result)
        endpoint_results.append(endpoint_result)

    if request_id > MAX_TOTAL_REQUESTS:
        raise Slice04RpcCapabilityProbeError('PROBE_REQUEST_BUDGET_EXCEEDED')

    overall = classify_overall(endpoint_results)
    if overall == 'AT_LEAST_ONE_CURRENT_ENDPOINT_SUPPORTS_REQUIRED_ETH_GETLOGS':
        next_step = 'USE_ONLY_PROVEN_ETH_GETLOGS_ENDPOINT_AND_RETRY_BOUNDED_SCAN'
    elif overall == 'CURRENT_ENDPOINT_SET_HAS_HISTORICAL_FILTER_OR_DEPTH_RESTRICTION':
        next_step = 'DO_NOT_RETRY_CURRENT_ENDPOINTS_SELECT_EVIDENCE_BACKED_ARCHIVE_INDEXER_OR_REDUCE_HISTORY_REQUIREMENT'
    else:
        next_step = 'DO_NOT_RETRY_CURRENT_ENDPOINTS_SELECT_EVIDENCE_BACKED_INDEXED_DATA_PROVIDER'

    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.rpc_eth_getlogs_capability_probe.v1',
        'generated_at_utc': iso_now(),
        'status': 'RPC_ETH_GETLOGS_CAPABILITY_PROBE_COMPLETED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {
            'database_path': str(database_path.resolve()),
            'database_sha256': file_sha256(database_path),
            'provider_path': str(provider_path.resolve()),
            'base_module_path': str(BASE_PATH.resolve()),
        },
        'policy': {
            'current_allowlisted_endpoints_only': True,
            'endpoint_isolation_required': True,
            'known_exact_transfer_log_required': True,
            'failed_historical_single_actor_single_block_reproduced': True,
            'maximum_total_requests': MAX_TOTAL_REQUESTS,
            'probe_only_no_historical_scan': True,
        },
        'known_event': known_event,
        'known_exact_filter': known_filter,
        'historical_anchor': anchor,
        'historical_probe_block': FAILED_HISTORICAL_BLOCK,
        'historical_exact_filter': historical_filter,
        'endpoint_results': endpoint_results,
        'summary': {
            'endpoint_count': len(endpoint_results),
            'chain_56_endpoint_count': sum(int(item['chain_id']['ok'] and item['chain_id']['value'] == 56) for item in endpoint_results),
            'known_block_available_endpoint_count': sum(int(item['known_block']['ok']) for item in endpoint_results),
            'known_exact_log_success_endpoint_count': sum(int(item['known_exact_log']['ok'] and item['known_exact_log']['exact_known_event_found']) for item in endpoint_results),
            'historical_exact_filter_success_endpoint_count': sum(int(item['historical_single_actor_single_block']['ok']) for item in endpoint_results),
            'request_count': request_id,
            'overall_classification': overall,
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
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.database, args.provider, args.output)
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'KNOWN_EVENT_TX={result["known_event"]["tx_hash"]}')
    print(f'KNOWN_EVENT_BLOCK={result["known_event"]["block_number"]}')
    print(f'HISTORICAL_PROBE_BLOCK={result["historical_probe_block"]}')
    for index, endpoint in enumerate(result['endpoint_results'], start=1):
        print(
            f'ENDPOINT_{index}=host:{endpoint["host"]},classification:{endpoint["classification"]},'
            f'chain_ok:{str(endpoint["chain_id"]["ok"]).lower()},'
            f'block_ok:{str(endpoint["known_block"]["ok"]).lower()},'
            f'known_log_ok:{str(endpoint["known_exact_log"]["ok"]).lower()},'
            f'known_exact_found:{str(endpoint["known_exact_log"]["exact_known_event_found"]).lower()},'
            f'historical_log_ok:{str(endpoint["historical_single_actor_single_block"]["ok"]).lower()},'
            f'historical_count:{endpoint["historical_single_actor_single_block"]["count"]},'
            f'known_error:{endpoint["known_exact_log"]["error"]},'
            f'historical_error:{endpoint["historical_single_actor_single_block"]["error"]}'
        )
    for key in (
        'endpoint_count',
        'chain_56_endpoint_count',
        'known_block_available_endpoint_count',
        'known_exact_log_success_endpoint_count',
        'historical_exact_filter_success_endpoint_count',
        'request_count',
    ):
        print(f'{key.upper()}={summary[key]}')
    print(f'OVERALL_CLASSIFICATION={summary["overall_classification"]}')
    print(f'RESULT_HASH={result["result_hash"]}')
    print('CLOSED_LOOP_CONFIRMED=false')
    print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
