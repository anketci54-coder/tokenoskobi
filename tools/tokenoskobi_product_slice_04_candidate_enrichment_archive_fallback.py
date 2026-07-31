#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
from typing import Any

BASE_MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_BASE_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_candidate_enrichment.py',
    )
)


def load_base_module(path: Path):
    spec = importlib.util.spec_from_file_location('tokenoskobi_product_slice_04_candidate_enrichment_base', path)
    if spec is None or spec.loader is None:
        raise RuntimeError('BASE_MODULE_IMPORT_SPEC_INVALID')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_module(BASE_MODULE_PATH)
BASE_FETCH_TOKEN_METADATA = base.fetch_token_metadata

ARCHIVE_STATE_UNAVAILABLE_MARKERS = (
    'missing trie node',
    'historical state unavailable',
    'state is not available',
    'state unavailable',
    'header not found',
    'old state is not available',
)


def is_archive_state_unavailable_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in ARCHIVE_STATE_UNAVAILABLE_MARKERS)


def fetch_token_metadata_with_archive_fallback(
    client: Any,
    token: str,
    block_number: int,
) -> dict[str, Any]:
    historical_tag = hex(block_number)
    try:
        result = dict(BASE_FETCH_TOKEN_METADATA(client, token, block_number))
        result.update(
            {
                'requested_historical_block_number': block_number,
                'requested_historical_block_tag': historical_tag,
                'effective_block_tag': historical_tag,
                'metadata_temporal_mode': 'HISTORICAL_BLOCK_VERIFIED',
                'historical_state_verified': True,
                'archive_fallback_used': False,
                'historical_error_hash': '',
            }
        )
        return result
    except base.Slice04EnrichmentError as exc:
        if not is_archive_state_unavailable_error(exc):
            raise
        historical_error_hash = base.canonical_hash(
            {
                'token_address': token,
                'requested_historical_block_tag': historical_tag,
                'error': str(exc),
            }
        )

    responses: dict[str, str] = {}
    provider_hosts: set[str] = set()
    for field, selector in base.TOKEN_CALLS.items():
        responses[field] = base.validate_hex_data(
            client.call('eth_call', [{'to': token, 'data': selector}, 'latest']),
            f'token.{field}',
        )
        provider_hosts.add(client.last_endpoint_host)

    decimals = base.decode_uint256(responses['decimals'])
    if decimals > 36:
        raise base.Slice04EnrichmentError(f'TOKEN_DECIMALS_OUT_OF_BOUNDS:{token}')

    return {
        'token_address': token,
        'block_number': None,
        'block_tag': 'latest',
        'requested_historical_block_number': block_number,
        'requested_historical_block_tag': historical_tag,
        'effective_block_tag': 'latest',
        'metadata_temporal_mode': 'LATEST_STATE_FALLBACK_ARCHIVE_UNAVAILABLE',
        'historical_state_verified': False,
        'archive_fallback_used': True,
        'historical_error_hash': historical_error_hash,
        'decimals': decimals,
        'symbol': base.decode_abi_string(responses['symbol']),
        'name': base.decode_abi_string(responses['name']),
        'provider_hosts': sorted(provider_hosts),
        'call_response_hash': base.canonical_hash(responses),
    }


def run(database_path: Path, provider_path: Path, output_path: Path) -> dict[str, Any]:
    base.fetch_token_metadata = fetch_token_metadata_with_archive_fallback
    result = base.run(database_path, provider_path, output_path)

    metadata = result.get('token_metadata') or []
    fallback_count = sum(bool(row.get('archive_fallback_used')) for row in metadata)
    historical_count = sum(bool(row.get('historical_state_verified')) for row in metadata)
    if fallback_count + historical_count != len(base.TRACKED_TOKENS):
        raise base.Slice04EnrichmentError('TOKEN_METADATA_TEMPORAL_CLASSIFICATION_INCOMPLETE')

    result['status'] = 'CANDIDATE_INPUT_AND_TOKEN_METADATA_ENRICHMENT_VERIFIED_WITH_ARCHIVE_FALLBACK_POLICY'
    result['metadata_temporal_policy'] = {
        'historical_block_attempt_required': True,
        'fallback_allowed_only_for_archive_state_unavailable_errors': True,
        'fallback_target': 'latest',
        'historical_metadata_verified_count': historical_count,
        'latest_metadata_fallback_count': fallback_count,
        'historical_transaction_and_receipt_identity_preserved': True,
        'token_amount_normalization_ready': len(metadata) == len(base.TRACKED_TOKENS),
        'metadata_temporal_limit_explicit': fallback_count > 0,
    }
    summary = result['summary']
    summary['historical_metadata_verified_count'] = historical_count
    summary['latest_metadata_fallback_count'] = fallback_count
    summary['token_amount_normalization_ready'] = len(metadata) == len(base.TRACKED_TOKENS)
    summary['metadata_historical_state_complete'] = fallback_count == 0

    result.pop('result_hash', None)
    result['result_hash'] = base.canonical_hash(result)
    base.atomic_write_json(output_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=base.DEFAULT_DB)
    parser.add_argument('--provider', type=Path, default=base.DEFAULT_CONFIG)
    parser.add_argument('--output', type=Path, default=base.DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = run(args.database, args.provider, args.output)
    summary = result['summary']
    policy = result['metadata_temporal_policy']
    print(f'OUTPUT={args.output}')
    print(f'CANDIDATE_TRANSACTION_INPUT_COVERAGE={summary["transaction_input_coverage"]}_OF_14')
    print(f'TOKEN_METADATA_COVERAGE={summary["token_metadata_coverage"]}_OF_3')
    print(f'HISTORICAL_METADATA_VERIFIED_COUNT={policy["historical_metadata_verified_count"]}')
    print(f'LATEST_METADATA_ARCHIVE_FALLBACK_COUNT={policy["latest_metadata_fallback_count"]}')
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
