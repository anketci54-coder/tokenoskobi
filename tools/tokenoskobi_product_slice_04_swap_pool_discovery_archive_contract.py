#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

BASE_MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_DISCOVERY_BASE_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_swap_pool_discovery.py',
    )
)
EXPECTED_ENRICHMENT_STATUS = (
    'CANDIDATE_INPUT_AND_TOKEN_METADATA_ENRICHMENT_VERIFIED_WITH_ARCHIVE_FALLBACK_POLICY'
)
EXPECTED_ENRICHMENT_RESULT_HASH = (
    '34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
)


def load_base_module(path: Path):
    spec = importlib.util.spec_from_file_location(
        'tokenoskobi_product_slice_04_swap_pool_discovery_base',
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError('DISCOVERY_BASE_MODULE_IMPORT_SPEC_INVALID')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_module(BASE_MODULE_PATH)


def load_enrichment(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise base.Slice04SwapDiscoveryError('ENRICHMENT_FILE_MISSING')
    payload = json.loads(path.read_text(encoding='utf-8'))
    if payload.get('schema') != 'tokenoskobi.product_slice_04.candidate_enrichment.v1':
        raise base.Slice04SwapDiscoveryError('ENRICHMENT_SCHEMA_INVALID')
    if payload.get('status') != EXPECTED_ENRICHMENT_STATUS:
        raise base.Slice04SwapDiscoveryError('ENRICHMENT_STATUS_INVALID')
    if payload.get('result_hash') != EXPECTED_ENRICHMENT_RESULT_HASH:
        raise base.Slice04SwapDiscoveryError('ENRICHMENT_RESULT_HASH_INVALID')

    policy = payload.get('metadata_temporal_policy')
    if not isinstance(policy, dict):
        raise base.Slice04SwapDiscoveryError('ENRICHMENT_TEMPORAL_POLICY_MISSING')
    required_policy = {
        'historical_block_attempt_required': True,
        'fallback_allowed_only_for_archive_state_unavailable_errors': True,
        'fallback_target': 'latest',
        'historical_metadata_verified_count': 0,
        'latest_metadata_fallback_count': 3,
        'historical_transaction_and_receipt_identity_preserved': True,
        'token_amount_normalization_ready': True,
        'metadata_temporal_limit_explicit': True,
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            raise base.Slice04SwapDiscoveryError(
                f'ENRICHMENT_TEMPORAL_POLICY_INVALID:{key}'
            )

    transactions = payload.get('transactions')
    metadata = payload.get('token_metadata')
    if not isinstance(transactions, list) or len(transactions) != 14:
        raise base.Slice04SwapDiscoveryError('ENRICHMENT_TRANSACTION_COUNT_INVALID')
    if not isinstance(metadata, list) or len(metadata) != 3:
        raise base.Slice04SwapDiscoveryError('ENRICHMENT_METADATA_COUNT_INVALID')

    tx_map: dict[str, dict[str, Any]] = {}
    for item in transactions:
        if not isinstance(item, dict):
            raise base.Slice04SwapDiscoveryError('ENRICHMENT_TRANSACTION_NOT_OBJECT')
        tx_hash = base.normalize_hash(item.get('tx_hash'))
        if tx_hash in tx_map:
            raise base.Slice04SwapDiscoveryError('ENRICHMENT_DUPLICATE_TRANSACTION')
        tx_map[tx_hash] = item

    metadata_map: dict[str, dict[str, Any]] = {}
    for item in metadata:
        if not isinstance(item, dict):
            raise base.Slice04SwapDiscoveryError('ENRICHMENT_METADATA_NOT_OBJECT')
        token = base.normalize_address(item.get('token_address'))
        if token in metadata_map:
            raise base.Slice04SwapDiscoveryError('ENRICHMENT_DUPLICATE_TOKEN')
        if item.get('metadata_temporal_mode') != 'LATEST_STATE_FALLBACK_ARCHIVE_UNAVAILABLE':
            raise base.Slice04SwapDiscoveryError('ENRICHMENT_METADATA_TEMPORAL_MODE_INVALID')
        if item.get('historical_state_verified') is not False:
            raise base.Slice04SwapDiscoveryError('ENRICHMENT_METADATA_HISTORICAL_FLAG_INVALID')
        if item.get('archive_fallback_used') is not True:
            raise base.Slice04SwapDiscoveryError('ENRICHMENT_METADATA_FALLBACK_FLAG_INVALID')
        if item.get('effective_block_tag') != 'latest':
            raise base.Slice04SwapDiscoveryError('ENRICHMENT_METADATA_EFFECTIVE_TAG_INVALID')
        metadata_map[token] = item

    return {
        'tx_map': tx_map,
        'metadata_map': metadata_map,
        'result_hash': EXPECTED_ENRICHMENT_RESULT_HASH,
        'metadata_temporal_policy': dict(policy),
    }


base.load_enrichment = load_enrichment

# Re-export the original decoder surface after installing the corrected loader.
for name in dir(base):
    if not name.startswith('__'):
        globals()[name] = getattr(base, name)


if __name__ == '__main__':
    raise SystemExit(base.main())
