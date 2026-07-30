#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
DEFAULT_DB = ROOT / 'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/bscscan_indexed_provider_probe_v1.json')
BASE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_HISTORICAL_REVERSE_SCAN_BASE_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_targeted_historical_reverse_scan.py',
    )
)

EXPECTED_DB_HASH = '99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
SOURCE_TABLE = 'era64i_historical_wallet_transfer_staging_v1'
API_URL = 'https://api.bscscan.com/api'
API_HOST = 'api.bscscan.com'
MAX_REQUESTS = 2
REQUEST_TIMEOUT_SECONDS = 20
RESULT_OFFSET = 1000
ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')

AUTHORITY = {
    'network_access': True,
    'network_mode': 'READ_ONLY_BSCSCAN_INDEXED_BEP20_TRANSFER_CAPABILITY_PROBE',
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


class Slice04BscScanProbeError(RuntimeError):
    pass


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location('product_slice_04_historical_reverse_scan_base', BASE_PATH)
    if spec is None or spec.loader is None:
        raise Slice04BscScanProbeError('BASE_MODULE_IMPORT_FAILED')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        raise Slice04BscScanProbeError('INVALID_EVM_ADDRESS')
    return text


def normalize_hash(value: Any) -> str:
    text = str(value or '').strip().lower()
    if HASH_RE.fullmatch(text) is None:
        raise Slice04BscScanProbeError('INVALID_TRANSACTION_HASH')
    return text


def read_api_key() -> tuple[str, str]:
    direct = str(os.environ.get('BSCSCAN_API_KEY') or '').strip()
    if direct:
        return direct, 'ENVIRONMENT_KEY_PRESENT'
    file_name = str(os.environ.get('BSCSCAN_API_KEY_FILE') or '').strip()
    if file_name:
        path = Path(file_name)
        if path.is_file():
            key = path.read_text(encoding='utf-8').strip()
            if key:
                return key, 'LOCAL_SECRET_FILE_PRESENT'
    return '', 'NO_KEY'


def load_known_event(database_path: Path) -> dict[str, Any]:
    resolved = database_path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file():
        raise Slice04BscScanProbeError('SOURCE_DATABASE_INVALID')
    if file_sha256(resolved) != EXPECTED_DB_HASH:
        raise Slice04BscScanProbeError('SOURCE_DATABASE_HASH_CHANGED')
    uri = f'file:{resolved}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04BscScanProbeError('SOURCE_DATABASE_INTEGRITY_FAILED')
        count = int(conn.execute(f'SELECT COUNT(*) FROM {SOURCE_TABLE}').fetchone()[0])
        if count != 367:
            raise Slice04BscScanProbeError('SOURCE_EVENT_COUNT_CHANGED')
        row = conn.execute(
            f'''SELECT token_address,from_address,to_address,amount_raw,tx_hash,log_index,block_number
                FROM {SOURCE_TABLE}
                ORDER BY block_number,tx_hash,log_index
                LIMIT 1'''
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise Slice04BscScanProbeError('KNOWN_EVENT_MISSING')
    event = dict(row)
    event['token_address'] = normalize_address(event['token_address'])
    event['from_address'] = normalize_address(event['from_address'])
    event['to_address'] = normalize_address(event['to_address'])
    event['tx_hash'] = normalize_hash(event['tx_hash'])
    event['amount_raw'] = str(int(str(event['amount_raw'])))
    event['block_number'] = int(event['block_number'])
    event['query_address'] = event['from_address']
    return event


def build_query(
    *,
    address: str,
    token: str,
    start_block: int,
    end_block: int,
    api_key: str,
) -> str:
    parsed = urllib.parse.urlparse(API_URL)
    if parsed.scheme != 'https' or parsed.hostname != API_HOST:
        raise Slice04BscScanProbeError('BSCSCAN_API_URL_NOT_ALLOWLISTED')
    if start_block < 0 or end_block < start_block:
        raise Slice04BscScanProbeError('BSCSCAN_BLOCK_RANGE_INVALID')
    params = {
        'module': 'account',
        'action': 'tokentx',
        'contractaddress': normalize_address(token),
        'address': normalize_address(address),
        'startblock': str(start_block),
        'endblock': str(end_block),
        'page': '1',
        'offset': str(RESULT_OFFSET),
        'sort': 'asc',
    }
    if api_key:
        params['apikey'] = api_key
    return API_URL + '?' + urllib.parse.urlencode(params)


def request_json(url: str) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != API_HOST:
        raise Slice04BscScanProbeError('BSCSCAN_REQUEST_HOST_NOT_ALLOWLISTED')
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'Tokenoskobi-Product-Slice-04/1.0 bscscan-indexed-provider-probe'},
        method='GET',
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise Slice04BscScanProbeError(f'BSCSCAN_REQUEST_FAILED:{type(exc).__name__}') from exc
    if not isinstance(payload, dict):
        raise Slice04BscScanProbeError('BSCSCAN_RESPONSE_NOT_OBJECT')
    return payload


def response_error_text(payload: dict[str, Any]) -> str:
    return ' '.join(
        str(payload.get(key) or '') for key in ('status', 'message', 'result')
    ).strip().lower()


def credential_required(payload: dict[str, Any]) -> bool:
    text = response_error_text(payload)
    return any(marker in text for marker in (
        'missing/invalid api key',
        'missing or invalid api key',
        'invalid api key',
        'api key required',
        'max rate limit reached',
    ))


def parse_tokentx_response(payload: dict[str, Any]) -> tuple[bool, list[dict[str, Any]], str]:
    status = str(payload.get('status') or '')
    message = str(payload.get('message') or '')
    result = payload.get('result')
    if status == '1' and isinstance(result, list):
        rows = [item for item in result if isinstance(item, dict)]
        if len(rows) != len(result):
            raise Slice04BscScanProbeError('BSCSCAN_RESULT_ROW_NOT_OBJECT')
        return True, rows, ''
    text = response_error_text(payload)
    if status == '0' and ('no transactions found' in text or result == []):
        return True, [], ''
    error = f'{message}:{result}'[:500]
    return False, [], error


def exact_event_found(rows: list[dict[str, Any]], event: dict[str, Any]) -> bool:
    for row in rows:
        try:
            matches = (
                normalize_hash(row.get('hash')) == event['tx_hash']
                and int(str(row.get('blockNumber'))) == event['block_number']
                and normalize_address(row.get('contractAddress')) == event['token_address']
                and normalize_address(row.get('from')) == event['from_address']
                and normalize_address(row.get('to')) == event['to_address']
                and str(int(str(row.get('value')))) == event['amount_raw']
            )
        except (Slice04BscScanProbeError, TypeError, ValueError):
            matches = False
        if matches:
            return True
    return False


def classify_probe(
    *,
    known_ok: bool,
    known_exact: bool,
    historical_ok: bool,
    known_payload: dict[str, Any],
    historical_payload: dict[str, Any],
) -> tuple[str, str]:
    if known_ok and known_exact and historical_ok:
        return (
            'BSCSCAN_INDEXED_PROVIDER_USABLE',
            'IMPLEMENT_BSCSCAN_INDEXED_TARGETED_REVERSE_SCAN_WITH_PAGINATION_AND_RPC_RECEIPT_VALIDATION',
        )
    if credential_required(known_payload) or credential_required(historical_payload):
        return (
            'BSCSCAN_FREE_API_KEY_REQUIRED',
            'CREATE_FREE_BSCSCAN_API_KEY_AND_RERUN_CAPABILITY_PROBE_WITH_LOCAL_SECRET_FILE',
        )
    if known_ok and not known_exact:
        return (
            'BSCSCAN_INDEXED_DATA_INCOMPLETE_ON_KNOWN_EVENT',
            'DO_NOT_USE_PROVIDER_REASSESS_INDEXED_DATA_SOURCE',
        )
    return (
        'BSCSCAN_INDEXED_PROVIDER_UNAVAILABLE',
        'DO_NOT_USE_PROVIDER_REASSESS_INDEXED_DATA_SOURCE',
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


def run(database_path: Path, output_path: Path) -> dict[str, Any]:
    base = load_base()
    known_event = load_known_event(database_path)
    source_rows, receipt_rows, _ = base.load_database(database_path)
    anchors = base.select_anchors(base.build_eligible_records(source_rows, receipt_rows))
    anchor = anchors[0]
    minimum_source_block = min(int(row['block_number']) for row in source_rows)
    historical_end = minimum_source_block - 1
    historical_start = historical_end - base.SCAN_BLOCK_SPAN + 1
    api_key, credential_mode = read_api_key()

    request_count = 0
    known_url = build_query(
        address=known_event['query_address'],
        token=known_event['token_address'],
        start_block=known_event['block_number'],
        end_block=known_event['block_number'],
        api_key=api_key,
    )
    known_payload = request_json(known_url)
    request_count += 1
    known_ok, known_rows, known_error = parse_tokentx_response(known_payload)
    known_exact = known_ok and exact_event_found(known_rows, known_event)

    historical_url = build_query(
        address=anchor['actor'],
        token=anchor['token'],
        start_block=historical_start,
        end_block=historical_end,
        api_key=api_key,
    )
    historical_payload = request_json(historical_url)
    request_count += 1
    if request_count > MAX_REQUESTS:
        raise Slice04BscScanProbeError('BSCSCAN_REQUEST_BUDGET_EXCEEDED')
    historical_ok, historical_rows, historical_error = parse_tokentx_response(historical_payload)

    classification, next_step = classify_probe(
        known_ok=known_ok,
        known_exact=known_exact,
        historical_ok=historical_ok,
        known_payload=known_payload,
        historical_payload=historical_payload,
    )
    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.bscscan_indexed_provider_probe.v1',
        'generated_at_utc': iso_now(),
        'status': 'BSCSCAN_INDEXED_PROVIDER_CAPABILITY_PROBE_COMPLETED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'provider': {
            'name': 'BscScan Community API',
            'host': API_HOST,
            'endpoint_family': 'account.tokentx',
            'credential_mode': credential_mode,
            'api_key_exposed': False,
        },
        'source': {
            'database_path': str(database_path.resolve()),
            'database_sha256': file_sha256(database_path),
            'source_event_count': len(source_rows),
            'source_receipt_count': len(receipt_rows),
        },
        'known_event_probe': {
            'tx_hash': known_event['tx_hash'],
            'block_number': known_event['block_number'],
            'token_address': known_event['token_address'],
            'query_address': known_event['query_address'],
            'response_ok': known_ok,
            'result_count': len(known_rows),
            'exact_event_found': known_exact,
            'error': known_error,
        },
        'historical_anchor_probe': {
            'actor': anchor['actor'],
            'token': anchor['token'],
            'missing_direction': anchor['missing_direction'],
            'start_block': historical_start,
            'end_block': historical_end,
            'response_ok': historical_ok,
            'result_count': len(historical_rows),
            'result_page_may_be_capped': len(historical_rows) >= RESULT_OFFSET,
            'error': historical_error,
        },
        'summary': {
            'request_count': request_count,
            'known_exact_event_verified': known_exact,
            'historical_anchor_query_succeeded': historical_ok,
            'overall_classification': classification,
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
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.database, args.output)
    known = result['known_event_probe']
    historical = result['historical_anchor_probe']
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    print(f'CREDENTIAL_MODE={result["provider"]["credential_mode"]}')
    print(f'KNOWN_EVENT_TX={known["tx_hash"]}')
    print(f'KNOWN_EVENT_BLOCK={known["block_number"]}')
    print(f'KNOWN_RESPONSE_OK={str(known["response_ok"]).lower()}')
    print(f'KNOWN_RESULT_COUNT={known["result_count"]}')
    print(f'KNOWN_EXACT_EVENT_VERIFIED={str(known["exact_event_found"]).lower()}')
    print(f'HISTORICAL_ANCHOR_ACTOR={historical["actor"]}')
    print(f'HISTORICAL_ANCHOR_TOKEN={historical["token"]}')
    print(f'HISTORICAL_RESPONSE_OK={str(historical["response_ok"]).lower()}')
    print(f'HISTORICAL_RESULT_COUNT={historical["result_count"]}')
    print(f'REQUEST_COUNT={summary["request_count"]}')
    print(f'OVERALL_CLASSIFICATION={summary["overall_classification"]}')
    print(f'RESULT_HASH={result["result_hash"]}')
    print('CLOSED_LOOP_CONFIRMED=false')
    print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
