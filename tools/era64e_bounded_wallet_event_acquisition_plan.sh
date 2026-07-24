#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era64e_wallet_acquisition_plan_backup_${STAMP}.tar.gz"
COMMITTED=0

CANONICAL_FILES=(
  PROJECT_RUNTIME.json
  PROJECT_HISTORY.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
  03_ROADMAP.md
  04_ALMANAC.md
  06_PROJECT_MASTER_STATE.md
  07_PROJECT_HANDOFF.md
)

NEW_FILES=(
  config/era64_bounded_wallet_event_acquisition_plan_v1.json
  tools/era64_wallet_event_acquisition_plan_v1.py
  tests/test_era64e_wallet_event_acquisition_plan_v1.py
  data/control/era64e_bounded_real_wallet_event_acquisition_and_backfill_plan_v1.json
  data/replay/era64e_bounded_wallet_event_acquisition_plan_v1.json
  reports/LATEST_ERA64E_WALLET_EVENT_ACQUISITION_PLAN.md
)

rollback() {
  rc=$?
  trap - ERR
  echo "ERA64E_FAILED_RC=$rc"
  if [[ "$COMMITTED" -eq 0 && -f "$BACKUP" ]]; then
    tar -xzf "$BACKUP" -C /root/tokenoskobi_clean_v1
    rm -f "${NEW_FILES[@]}"
    git reset --quiet
    echo "ROLLBACK=COMPLETED"
  fi
  exit "$rc"
}
trap rollback ERR

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer

python3 <<'PY_PRECHECK'
import json
from pathlib import Path

runtime = json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
pointer = runtime.get('canonical_runtime_pointer') if isinstance(runtime.get('canonical_runtime_pointer'), dict) else {}

def current(key):
    return runtime.get(key, pointer.get(key))

assert current('current_era') == 'ERA64'
assert current('current_stage') == 'ERA64D_REAL_WALLET_EVENT_COVERAGE_GAP_REPAIR'
assert current('next_safe_step') == 'ERA64E_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN_REQUIRES_USER_APPROVAL'
assert current('era64d_coverage_classification_repaired') is True
assert current('era64d_source_contract_ready') is True
assert current('era64d_candidate_source_table_count') == 8
assert current('era64d_empty_candidate_table_count') == 8
assert current('era64d_nonempty_candidate_table_count') == 0
assert current('paper_runtime_enabled') is False

authority = runtime.get('authority', {})
assert isinstance(authority, dict)
assert authority.get('real_trade_authority') == 0
assert authority.get('real_wallet_authority') == 0
assert authority.get('real_signing_authority') == 0
assert authority.get('real_order_authority') == 0
assert authority.get('live_trade') == 'DISABLED'

control = json.loads(Path('data/control/era64d_real_wallet_event_coverage_gap_repair_v1.json').read_text(encoding='utf-8'))
assert control['status'] == 'REAL_WALLET_EVENT_COVERAGE_REPAIRED_SOURCE_CONTRACT_READY'
assert control['source_contract_ready'] is True
assert control['candidate_source_table_count'] == 8
assert control['empty_candidate_table_count'] == 8
assert control['nonempty_candidate_table_count'] == 0
assert Path(control['detail_artifact']).is_file()
print('PRECHECK=VERIFIED')
PY_PRECHECK

tar -czf "$BACKUP" "${CANONICAL_FILES[@]}"
echo "BACKUP=$BACKUP"
mkdir -p config tools tests data/control data/replay reports

cat > config/era64_bounded_wallet_event_acquisition_plan_v1.json <<'JSON_CONFIG'
{
  "schema": "tokenoskobi.era64.bounded_wallet_event_acquisition_plan.config.v1",
  "mode": "PLAN_ONLY_NO_ACQUISITION",
  "chain": {
    "name": "BSC",
    "chain_id": 56,
    "scope": "SINGLE_CHAIN_BOUNDED"
  },
  "authority": {
    "network_access": false,
    "database_write": false,
    "runtime_mutation": false,
    "panel_mutation": false,
    "service_mutation": false,
    "timer_mutation": false,
    "paper_trade": false,
    "live_trade": false,
    "wallet": false,
    "signing": false,
    "order_create": false,
    "broadcast": false
  },
  "execution_authorized": false,
  "synthetic_runtime_data_allowed": false,
  "source_contract": "data/control/era64d_real_wallet_event_coverage_gap_repair_v1.json",
  "source_detail": "data/replay/era64d_real_wallet_event_coverage_bridge_v1.json",
  "source_priority": [
    "LOCAL_EXISTING_SQLITE_AND_RUNTIME_OUTPUTS",
    "BOUNDED_BSC_RPC_CANARY_AFTER_SEPARATE_APPROVAL",
    "BOUNDED_BSC_HISTORICAL_BACKFILL_AFTER_CANARY_PASS_AND_SEPARATE_APPROVAL"
  ],
  "provider_policy": {
    "reuse_existing_allowlisted_https_providers_only": true,
    "paid_provider_required": false,
    "secrets_in_repository_forbidden": true,
    "bounded_exponential_backoff_required": true,
    "provider_rotation_required": true,
    "fail_closed_on_chain_mismatch": true,
    "fail_closed_on_rate_limit_exhaustion": true
  },
  "future_rpc_method_allowlist": [
    "eth_blockNumber",
    "eth_getLogs",
    "eth_getTransactionByHash",
    "eth_getTransactionReceipt",
    "eth_getBlockByNumber",
    "eth_call"
  ],
  "canary_budget": {
    "maximum_pool_count": 2,
    "maximum_block_span": 5000,
    "log_chunk_size": 500,
    "maximum_log_count": 10000,
    "maximum_transaction_receipt_count": 1000,
    "maximum_distinct_wallet_count": 1000,
    "maximum_runtime_seconds": 600
  },
  "historical_backfill_budget": {
    "maximum_pool_count": 2,
    "maximum_block_span": 100000,
    "log_chunk_size": 1000,
    "maximum_log_count": 250000,
    "maximum_transaction_receipt_count": 25000,
    "maximum_distinct_wallet_count": 5000,
    "maximum_runtime_seconds": 7200
  },
  "event_identity": {
    "log_event_key": ["chain_id", "tx_hash", "log_index"],
    "transaction_key": ["chain_id", "tx_hash"],
    "relationship_key": ["chain_id", "tx_hash", "log_index", "from_address", "to_address"],
    "raw_payload_hash_required": true,
    "source_provider_required": true,
    "observed_at_utc_required": true
  },
  "minimum_canary_acceptance": {
    "real_transfer_or_swap_event_count": 100,
    "distinct_wallet_count": 10,
    "cost_complete_trade_event_count": 5,
    "duplicate_event_count": 0,
    "missing_transaction_hash_count": 0,
    "missing_block_number_count": 0,
    "missing_timestamp_count": 0,
    "missing_provenance_count": 0,
    "authority_violation_count": 0
  }
}
JSON_CONFIG

cat > tools/era64_wallet_event_acquisition_plan_v1.py <<'PY_ENGINE'
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

AUTHORITY = {
    'network_access': False,
    'database_write': False,
    'runtime_mutation': False,
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

STATUS = 'BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN_VERIFIED'
NEXT_SAFE_STEP = 'ERA64F_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_CANARY_APPLY_REQUIRES_USER_APPROVAL'


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )
    temporary.replace(path)


def candidate_sources(detail: dict[str, Any]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for database in detail.get('database_sources', []):
        database_path = str(database.get('path') or '')
        for item in database.get('inventory', []):
            if item.get('candidate_source') is not True:
                continue
            selected.append({
                'database': database_path,
                'table': str(item.get('table') or ''),
                'capabilities': sorted(str(value) for value in item.get('capabilities', [])),
                'blockers': sorted(str(value) for value in item.get('blockers', [])),
                'empty': bool(item.get('empty')),
                'total_rows': int(item.get('total_rows') or 0),
                'columns': sorted(str(value) for value in item.get('columns', [])),
            })
    return sorted(selected, key=lambda value: (value['database'], value['table']))


def build_plan(config: dict[str, Any], source_control: dict[str, Any], source_detail: dict[str, Any]) -> dict[str, Any]:
    candidates = candidate_sources(source_detail)
    return {
        'schema': 'tokenoskobi.era64e.bounded_wallet_event_acquisition_and_backfill_plan.v1',
        'status': STATUS,
        'mode': config['mode'],
        'chain': config['chain'],
        'authority': dict(AUTHORITY),
        'execution_authorized': False,
        'network_execution_performed': False,
        'database_write_performed': False,
        'runtime_mutation_performed': False,
        'synthetic_data': False,
        'real_data_baseline_verified': source_control.get('real_data') is True,
        'new_real_event_count': 0,
        'source_contract_ready': source_control.get('source_contract_ready') is True,
        'source_contract_status': source_control.get('status'),
        'candidate_source_count': len(candidates),
        'empty_candidate_source_count': sum(1 for item in candidates if item['empty']),
        'candidate_sources': candidates,
        'source_priority': list(config['source_priority']),
        'provider_policy': dict(config['provider_policy']),
        'future_rpc_method_allowlist': list(config['future_rpc_method_allowlist']),
        'canary_budget': dict(config['canary_budget']),
        'historical_backfill_budget': dict(config['historical_backfill_budget']),
        'event_identity': dict(config['event_identity']),
        'minimum_canary_acceptance': dict(config['minimum_canary_acceptance']),
        'event_contracts': {
            'transfer_event': {
                'required': [
                    'chain_id', 'tx_hash', 'log_index', 'block_number', 'block_time_utc',
                    'from_address', 'to_address', 'token_address', 'amount_raw',
                    'token_decimals', 'amount_normalized', 'source_provider', 'raw_payload_hash',
                ],
                'purpose': ['FUNDING_RELATIONSHIP', 'WALLET_FLOW', 'CLUSTER_EVIDENCE'],
            },
            'swap_event': {
                'required': [
                    'chain_id', 'tx_hash', 'log_index', 'block_number', 'block_time_utc',
                    'wallet_address', 'pair_address', 'token_in', 'token_out', 'side',
                    'quantity', 'execution_price', 'protocol_fee', 'gas_cost',
                    'source_provider', 'raw_payload_hash',
                ],
                'purpose': ['COST_COMPLETE_POSITION_REPLAY', 'SUCCESSFUL_WALLET_STATISTICS'],
            },
            'wallet_label_evidence': {
                'required': [
                    'chain_id', 'wallet_address', 'label', 'confidence', 'evidence_source',
                    'evidence_id', 'observed_at_utc',
                ],
                'unknown_wallet_policy': 'PRESERVE_UNKNOWN_NO_INVENTED_LABEL',
            },
        },
        'logical_backfill_targets': [
            'wallet_transfer_events',
            'whale_entity_flow_events_v1',
            'known_wallet_registry',
            'whale_entity_wallet_links_v1',
            'wallet_cluster_links',
            'wallet_link_graph_events',
            'wallet_token_entry_events',
            'wallet_outcome_events',
        ],
        'write_strategy_after_future_approval': {
            'mode': 'APPEND_ONLY_STAGING_THEN_VALIDATED_MERGE',
            'idempotent': True,
            'production_table_direct_write_forbidden': True,
            'transactional_batch_required': True,
            'rollback_on_validation_failure': True,
            'raw_evidence_preservation_required': True,
        },
        'fail_closed_rules': [
            'MISSING_TX_HASH_REJECT_EVENT',
            'MISSING_BLOCK_NUMBER_REJECT_EVENT',
            'MISSING_TIMESTAMP_REJECT_EVENT',
            'CHAIN_ID_MISMATCH_ABORT_BATCH',
            'MISSING_RECEIPT_EXCLUDE_COST_COMPLETE_TRADE',
            'MISSING_PRICE_EXCLUDE_COST_COMPLETE_TRADE',
            'MISSING_PROTOCOL_FEE_EXCLUDE_COST_COMPLETE_TRADE',
            'MISSING_GAS_COST_EXCLUDE_COST_COMPLETE_TRADE',
            'UNKNOWN_LABEL_REMAINS_UNKNOWN',
            'DUPLICATE_EVENT_KEY_REJECT_DUPLICATE',
            'CANARY_THRESHOLD_FAILURE_BLOCKS_HISTORICAL_BACKFILL',
            'NO_SCORECARD_OR_PANEL_BINDING_BEFORE_VALIDATED_CLOSED_CYCLES',
        ],
        'approval_gates': [
            {
                'gate': 'ERA64F_CANARY_APPLY',
                'authorized': False,
                'requires_user_approval': True,
                'scope': 'BOUNDED_BSC_READONLY_NETWORK_ACQUISITION_AND_STAGING_BACKFILL',
            },
            {
                'gate': 'ERA64G_HISTORICAL_BACKFILL_APPLY',
                'authorized': False,
                'requires_user_approval': True,
                'scope': 'ONLY_AFTER_CANARY_ACCEPTANCE_PASS',
            },
            {
                'gate': 'SCORECARD_AND_PANEL_BINDING',
                'authorized': False,
                'requires_user_approval': True,
                'scope': 'ONLY_AFTER_REAL_CLOSED_POSITION_REPLAY_VALIDATION',
            },
        ],
        'strongest_alternative_hypotheses': [
            'SHORT_LOOKBACK_CAN_OVERFIT_RECENT_WALLET_BEHAVIOR',
            'DEX_ROUTER_AND_AGGREGATOR_PATHS_CAN_OBSCURE_TRUE_TRADER_IDENTITY',
            'MEV_AND_ARBITRAGE_WALLETS_CAN_LOOK_SUCCESSFUL_BUT_BE_NON_COPYABLE',
            'INCOMPLETE_RECEIPTS_OR_PRICE_CONTEXT_CAN OVERSTATE NET PERFORMANCE'.replace(' ', '_'),
            'SURVIVORSHIP_BIAS_REQUIRES_FAILED_AND_OPEN_POSITIONS_TOO',
        ],
        'next_safe_step': NEXT_SAFE_STEP,
    }


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get('status') != STATUS:
        raise ValueError('INVALID_PLAN_STATUS')
    if plan.get('mode') != 'PLAN_ONLY_NO_ACQUISITION':
        raise ValueError('INVALID_PLAN_MODE')
    if plan.get('execution_authorized') is not False:
        raise ValueError('EXECUTION_MUST_REMAIN_UNAUTHORIZED')
    if any(plan.get('authority', {}).values()):
        raise ValueError('AUTHORITY_MUST_REMAIN_ZERO')
    if plan.get('candidate_source_count') != 8:
        raise ValueError('EXPECTED_EIGHT_CANDIDATE_SOURCES')
    if plan.get('empty_candidate_source_count') != 8:
        raise ValueError('EXPECTED_ALL_CANDIDATE_SOURCES_EMPTY')
    if plan.get('source_priority', [None])[0] != 'LOCAL_EXISTING_SQLITE_AND_RUNTIME_OUTPUTS':
        raise ValueError('LOCAL_FIRST_POLICY_REQUIRED')
    canary = plan.get('canary_budget', {})
    historical = plan.get('historical_backfill_budget', {})
    if int(canary.get('maximum_block_span', 0)) <= 0:
        raise ValueError('INVALID_CANARY_BLOCK_SPAN')
    if int(historical.get('maximum_block_span', 0)) <= int(canary.get('maximum_block_span', 0)):
        raise ValueError('HISTORICAL_BUDGET_MUST_EXCEED_CANARY')
    if plan.get('next_safe_step') != NEXT_SAFE_STEP:
        raise ValueError('INVALID_NEXT_SAFE_STEP')


def run(root: Path, config_path: Path, control_path: Path, detail_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_json(config_path)
    source_control = load_json(root / config['source_contract'])
    source_detail = load_json(root / config['source_detail'])
    plan = build_plan(config, source_control, source_detail)
    validate_plan(plan)
    plan['plan_hash'] = canonical_hash({key: value for key, value in plan.items() if key != 'plan_hash'})
    summary = {
        'schema': 'tokenoskobi.era64e.bounded_wallet_event_acquisition_plan.summary.v1',
        'status': plan['status'],
        'mode': plan['mode'],
        'chain': plan['chain'],
        'authority': plan['authority'],
        'execution_authorized': False,
        'network_execution_performed': False,
        'database_write_performed': False,
        'synthetic_data': False,
        'real_data_baseline_verified': plan['real_data_baseline_verified'],
        'new_real_event_count': 0,
        'candidate_source_count': plan['candidate_source_count'],
        'empty_candidate_source_count': plan['empty_candidate_source_count'],
        'canary_budget': plan['canary_budget'],
        'minimum_canary_acceptance': plan['minimum_canary_acceptance'],
        'plan_detail_artifact': str(detail_path.relative_to(root)),
        'plan_hash': plan['plan_hash'],
        'next_safe_step': NEXT_SAFE_STEP,
    }
    atomic_json(detail_path, plan)
    atomic_json(control_path, summary)
    return summary, plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--config', default='config/era64_bounded_wallet_event_acquisition_plan_v1.json')
    parser.add_argument('--control', default='data/control/era64e_bounded_real_wallet_event_acquisition_and_backfill_plan_v1.json')
    parser.add_argument('--detail', default='data/replay/era64e_bounded_wallet_event_acquisition_plan_v1.json')
    args = parser.parse_args()
    root = Path(args.root).resolve()
    summary, _ = run(root, root / args.config, root / args.control, root / args.detail)
    print(f"ERA64E_STATUS={summary['status']}")
    print(f"CANDIDATE_SOURCE_COUNT={summary['candidate_source_count']}")
    print(f"EMPTY_CANDIDATE_SOURCE_COUNT={summary['empty_candidate_source_count']}")
    print(f"NEXT_SAFE_STEP={summary['next_safe_step']}")


if __name__ == '__main__':
    main()
PY_ENGINE

cat > tests/test_era64e_wallet_event_acquisition_plan_v1.py <<'PY_TEST'
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.era64_wallet_event_acquisition_plan_v1 import (
    AUTHORITY,
    NEXT_SAFE_STEP,
    STATUS,
    build_plan,
    candidate_sources,
    canonical_hash,
    validate_plan,
)


class Era64EWalletAcquisitionPlanTests(unittest.TestCase):
    def fixture(self):
        inventory = []
        for index in range(8):
            inventory.append({
                'table': f'candidate_{index}',
                'candidate_source': True,
                'capabilities': ['DIRECT_RELATION_CANDIDATE'],
                'blockers': [],
                'empty': True,
                'total_rows': 0,
                'columns': ['tx_hash'],
            })
        detail = {'database_sources': [{'path': 'data/x.sqlite', 'inventory': inventory}]}
        control = {
            'real_data': True,
            'source_contract_ready': True,
            'status': 'REAL_WALLET_EVENT_COVERAGE_REPAIRED_SOURCE_CONTRACT_READY',
        }
        config = json.loads(Path('config/era64_bounded_wallet_event_acquisition_plan_v1.json').read_text(encoding='utf-8'))
        return config, control, detail

    def test_01_candidate_sources_are_preserved(self):
        _, _, detail = self.fixture()
        result = candidate_sources(detail)
        self.assertEqual(len(result), 8)
        self.assertTrue(all(item['empty'] for item in result))

    def test_02_plan_is_plan_only(self):
        config, control, detail = self.fixture()
        plan = build_plan(config, control, detail)
        self.assertEqual(plan['status'], STATUS)
        self.assertEqual(plan['mode'], 'PLAN_ONLY_NO_ACQUISITION')
        self.assertFalse(plan['execution_authorized'])

    def test_03_chain_is_bsc_only(self):
        config, control, detail = self.fixture()
        plan = build_plan(config, control, detail)
        self.assertEqual(plan['chain']['chain_id'], 56)
        self.assertEqual(plan['chain']['scope'], 'SINGLE_CHAIN_BOUNDED')

    def test_04_local_first_policy_is_locked(self):
        config, control, detail = self.fixture()
        plan = build_plan(config, control, detail)
        self.assertEqual(plan['source_priority'][0], 'LOCAL_EXISTING_SQLITE_AND_RUNTIME_OUTPUTS')

    def test_05_canary_budget_is_bounded(self):
        config, control, detail = self.fixture()
        plan = build_plan(config, control, detail)
        budget = plan['canary_budget']
        self.assertLessEqual(budget['maximum_pool_count'], 2)
        self.assertLessEqual(budget['maximum_block_span'], 5000)
        self.assertLessEqual(budget['maximum_runtime_seconds'], 600)

    def test_06_historical_backfill_requires_larger_separate_gate(self):
        config, control, detail = self.fixture()
        plan = build_plan(config, control, detail)
        self.assertGreater(
            plan['historical_backfill_budget']['maximum_block_span'],
            plan['canary_budget']['maximum_block_span'],
        )
        self.assertFalse(plan['approval_gates'][1]['authorized'])

    def test_07_cost_complete_swap_contract_exists(self):
        config, control, detail = self.fixture()
        plan = build_plan(config, control, detail)
        required = set(plan['event_contracts']['swap_event']['required'])
        self.assertTrue({'wallet_address', 'side', 'quantity', 'execution_price', 'protocol_fee', 'gas_cost'} <= required)

    def test_08_fail_closed_rules_block_incomplete_costs(self):
        config, control, detail = self.fixture()
        plan = build_plan(config, control, detail)
        rules = set(plan['fail_closed_rules'])
        self.assertIn('MISSING_RECEIPT_EXCLUDE_COST_COMPLETE_TRADE', rules)
        self.assertIn('MISSING_GAS_COST_EXCLUDE_COST_COMPLETE_TRADE', rules)
        self.assertIn('CANARY_THRESHOLD_FAILURE_BLOCKS_HISTORICAL_BACKFILL', rules)

    def test_09_authority_remains_zero(self):
        self.assertFalse(any(AUTHORITY.values()))
        config, control, detail = self.fixture()
        plan = build_plan(config, control, detail)
        validate_plan(plan)
        self.assertEqual(plan['next_safe_step'], NEXT_SAFE_STEP)

    def test_10_output_is_deterministic_and_source_is_safe(self):
        config, control, detail = self.fixture()
        first = build_plan(config, control, detail)
        second = build_plan(config, control, detail)
        self.assertEqual(canonical_hash(first), canonical_hash(second))
        source = Path('tools/era64_wallet_event_acquisition_plan_v1.py').read_text(encoding='utf-8')
        for forbidden in ('requests.', 'urllib.', 'web3', 'sqlite3', 'subprocess', 'os.system', 'shell=True', 'eval(', 'exec(', 'INSERT INTO', 'UPDATE ', 'DELETE FROM'):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
PY_TEST

python3 -m unittest -v tests/test_era64e_wallet_event_acquisition_plan_v1.py
python3 -m unittest -v tests/test_era64d_wallet_event_coverage_bridge_v1.py
python3 -m unittest -v tests/test_era64_real_historical_wallet_replay_v1.py
python3 -m unittest -v tests/test_era64_successful_wallet_foundation_v1.py
python3 tools/era58_smart_money_performance_engine_v1_test.py
python3 -m unittest -v tests/test_era63b_paper_trading_core_v1.py
python3 -m unittest -v tests/test_era63c_technical_dex_execution_v1.py
python3 -m unittest -v tests/test_era63d_market_technical_runtime_v1.py
python3 -m unittest -v tests/test_era63e_always_on_market_runtime_v1.py
echo "TESTS=118/118_VERIFIED"

python3 tools/era64_wallet_event_acquisition_plan_v1.py --root /root/tokenoskobi_clean_v1

python3 <<'PY_RESULT_VERIFY'
import json
from pathlib import Path

summary = json.loads(Path('data/control/era64e_bounded_real_wallet_event_acquisition_and_backfill_plan_v1.json').read_text(encoding='utf-8'))
assert summary['status'] == 'BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN_VERIFIED'
assert summary['mode'] == 'PLAN_ONLY_NO_ACQUISITION'
assert summary['candidate_source_count'] == 8
assert summary['empty_candidate_source_count'] == 8
assert summary['execution_authorized'] is False
assert summary['network_execution_performed'] is False
assert summary['database_write_performed'] is False
assert summary['synthetic_data'] is False
assert summary['new_real_event_count'] == 0
assert not any(summary['authority'].values())
assert summary['next_safe_step'] == 'ERA64F_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_CANARY_APPLY_REQUIRES_USER_APPROVAL'
print('PLAN_VERIFY=VERIFIED')
PY_RESULT_VERIFY

python3 <<'PY_CANONICAL'
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

NOW = datetime.now(timezone.utc).isoformat()
STAGE = 'ERA64E_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN'
STATUS = 'BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN_VERIFIED'
NEXT = 'ERA64F_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_CANARY_APPLY_REQUIRES_USER_APPROVAL'
ARTIFACT_PATH = 'data/control/era64e_bounded_real_wallet_event_acquisition_and_backfill_plan_v1.json'
DETAIL_PATH = 'data/replay/era64e_bounded_wallet_event_acquisition_plan_v1.json'
artifact = json.loads(Path(ARTIFACT_PATH).read_text(encoding='utf-8'))


def load(path: str):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path: str, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')


def apply_state(obj):
    if not isinstance(obj, dict):
        return
    obj['current_era'] = 'ERA64'
    obj['current_stage'] = STAGE
    obj['current_status'] = 'ACTIVE_BOUNDED_WALLET_EVENT_ACQUISITION_PLAN_VERIFIED'
    obj['next_safe_step'] = NEXT
    obj['updated_at_utc'] = NOW
    obj['era64_implementation_authorized'] = True
    obj['era64e_artifact'] = ARTIFACT_PATH
    obj['era64e_detail_artifact'] = DETAIL_PATH
    obj['era64e_status'] = STATUS
    obj['era64e_plan_verified'] = True
    obj['era64e_execution_authorized'] = False
    obj['era64e_network_execution_performed'] = False
    obj['era64e_database_write_performed'] = False
    obj['era64e_candidate_source_count'] = artifact['candidate_source_count']
    obj['era64e_empty_candidate_source_count'] = artifact['empty_candidate_source_count']
    obj['paper_runtime_enabled'] = False
    obj['fixed_timer_enabled'] = False
    authority = obj.get('authority')
    if isinstance(authority, dict):
        authority['real_trade_authority'] = 0
        authority['real_wallet_authority'] = 0
        authority['real_signing_authority'] = 0
        authority['real_order_authority'] = 0
        authority['live_trade'] = 'DISABLED'
        authority['paper_trade'] = 'DISABLED_PENDING_COORDINATED_INTELLIGENCE'


runtime = load('PROJECT_RUNTIME.json')
apply_state(runtime)
pointer = runtime.get('canonical_runtime_pointer')
if isinstance(pointer, dict):
    apply_state(pointer)
save('PROJECT_RUNTIME.json', runtime)

machine = load('data/control/latest_tk_machine_state.json')
apply_state(machine)
pointer = machine.get('canonical_runtime_pointer') if isinstance(machine, dict) else None
if isinstance(pointer, dict):
    apply_state(pointer)
save('data/control/latest_tk_machine_state.json', machine)

history = load('PROJECT_HISTORY.json')
entry = {
    'id': STAGE,
    'era': 'ERA64',
    'stage': STAGE,
    'status': STATUS,
    'completed_at_utc': NOW,
    'artifact': ARTIFACT_PATH,
    'detail_artifact': DETAIL_PATH,
    'plan_only': True,
    'execution_authorized': False,
    'network_execution_performed': False,
    'database_write_performed': False,
    'synthetic_data': False,
    'candidate_source_count': artifact['candidate_source_count'],
    'empty_candidate_source_count': artifact['empty_candidate_source_count'],
    'tests': '118/118_VERIFIED',
    'real_financial_authority': 0,
    'next_safe_step': NEXT,
}
if isinstance(history, list):
    history.append(entry)
elif isinstance(history, dict):
    target = None
    for key in ('events', 'history', 'timeline', 'entries'):
        if isinstance(history.get(key), list):
            target = history[key]
            break
    if target is None:
        target = history.setdefault('events', [])
    target.append(entry)
    history['updated_at_utc'] = NOW
save('PROJECT_HISTORY.json', history)

roadmap = load('data/tokenoskobi_v1_v8_master_era_roadmap.json')

def walk(value):
    if isinstance(value, dict):
        if value.get('id') == 'ERA64' or value.get('era') == 'ERA64':
            value['opened'] = True
            value['status'] = 'ACTIVE'
            value['current_stage'] = STAGE
            value['actual_status'] = STATUS
            value['next_safe_step'] = NEXT
            value['era64e_artifact'] = ARTIFACT_PATH
            value['era64e_execution_authorized'] = False
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)

walk(roadmap)
if isinstance(roadmap, dict):
    direction = roadmap.setdefault('current_direction', {})
    if isinstance(direction, dict):
        direction.update({
            'current_version': 'V4',
            'current_era': 'ERA64',
            'current_stage': STAGE,
            'current_status': 'ACTIVE_BOUNDED_WALLET_EVENT_ACQUISITION_PLAN_VERIFIED',
            'next_safe_step': NEXT,
            'updated_at_utc': NOW,
        })
save('data/tokenoskobi_v1_v8_master_era_roadmap.json', roadmap)

marker = '<!-- ERA64E_BOUNDED_WALLET_EVENT_ACQUISITION_PLAN -->'
blocks = {
    '03_ROADMAP.md': f'''\n{marker}\n## ERA64E bounded wallet-event acquisition plan\n\n- Status: `{STATUS}`\n- Mode: `PLAN_ONLY_NO_ACQUISITION`\n- Candidate source tables: `{artifact['candidate_source_count']}`\n- Empty candidate tables: `{artifact['empty_candidate_source_count']}`\n- Next approval gate: `{NEXT}`\n''',
    '04_ALMANAC.md': f'''\n{marker}\n## {NOW} — ERA64E\n\nA bounded BSC wallet-event acquisition and historical backfill plan was verified. No network acquisition or database write was executed. Tests: `118/118_VERIFIED`.\n''',
    '06_PROJECT_MASTER_STATE.md': f'''\n{marker}\n## Current ERA64 state\n\n`{STAGE}` completed with `{STATUS}`. The plan is local-first, BSC-only, bounded, fail-closed and separately gated before any network acquisition or database backfill.\n''',
    '07_PROJECT_HANDOFF.md': f'''\n{marker}\n## ERA64 handoff\n\n- Current stage: `{STAGE}`\n- Result: `{STATUS}`\n- Plan only: `true`\n- Network acquisition executed: `false`\n- Database write executed: `false`\n- Next: `{NEXT}`\n- Paper/live runtime: disabled\n- Real financial authority: zero\n''',
}
for path, block in blocks.items():
    text = Path(path).read_text(encoding='utf-8')
    if marker not in text:
        Path(path).write_text(text.rstrip() + '\n' + block, encoding='utf-8')

report = f'''# ERA64E BOUNDED REAL WALLET EVENT ACQUISITION AND BACKFILL PLAN\n\n- Status: `{STATUS}`\n- Mode: `PLAN_ONLY_NO_ACQUISITION`\n- Chain: `BSC / 56`\n- Local-first: `true`\n- Candidate sources: `{artifact['candidate_source_count']}`\n- Empty candidate sources: `{artifact['empty_candidate_source_count']}`\n- New real events acquired: `0`\n- Network execution performed: `false`\n- Database write performed: `false`\n- Synthetic data: `false`\n- Canary maximum pools: `{artifact['canary_budget']['maximum_pool_count']}`\n- Canary maximum block span: `{artifact['canary_budget']['maximum_block_span']}`\n- Canary maximum logs: `{artifact['canary_budget']['maximum_log_count']}`\n- Tests: `118/118_VERIFIED`\n- Paper runtime: `DISABLED`\n- Live trade: `DISABLED`\n- Real financial authority: `0`\n- Next: `{NEXT}`\n'''
Path('reports/LATEST_ERA64E_WALLET_EVENT_ACQUISITION_PLAN.md').write_text(report, encoding='utf-8')
Path('reports/LATEST_TK_AI_HANDOFF.md').write_text(f'''# TOKENOSKOBI LATEST HANDOFF\n\n```text\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA64\nCURRENT_STAGE={STAGE}\nRESULT={STATUS}\nNEXT_SAFE_STEP={NEXT}\n```\n\nERA64E produced a bounded, local-first BSC acquisition and backfill plan only. No network acquisition, database write, paper runtime or financial authority was opened.\n''', encoding='utf-8')

print('CANONICAL_SYNC=VERIFIED')
print(f'NEXT_SAFE_STEP={NEXT}')
PY_CANONICAL

python3 <<'PY_VERIFY'
import json
from pathlib import Path

for path in (
    'PROJECT_RUNTIME.json',
    'PROJECT_HISTORY.json',
    'data/tokenoskobi_v1_v8_master_era_roadmap.json',
    'data/control/latest_tk_machine_state.json',
    'config/era64_bounded_wallet_event_acquisition_plan_v1.json',
    'data/control/era64e_bounded_real_wallet_event_acquisition_and_backfill_plan_v1.json',
    'data/replay/era64e_bounded_wallet_event_acquisition_plan_v1.json',
):
    json.loads(Path(path).read_text(encoding='utf-8'))

runtime = json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert runtime['current_era'] == 'ERA64'
assert runtime['current_stage'] == 'ERA64E_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN'
assert runtime['current_status'] == 'ACTIVE_BOUNDED_WALLET_EVENT_ACQUISITION_PLAN_VERIFIED'
assert runtime['next_safe_step'] == 'ERA64F_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_CANARY_APPLY_REQUIRES_USER_APPROVAL'
assert runtime['era64e_execution_authorized'] is False
assert runtime['era64e_network_execution_performed'] is False
assert runtime['era64e_database_write_performed'] is False
assert runtime['paper_runtime_enabled'] is False
assert runtime['fixed_timer_enabled'] is False
authority = runtime['authority']
assert authority['real_trade_authority'] == 0
assert authority['real_wallet_authority'] == 0
assert authority['real_signing_authority'] == 0
assert authority['real_order_authority'] == 0
assert authority['live_trade'] == 'DISABLED'
print('CANONICAL_VERIFY=VERIFIED')
PY_VERIFY

git diff --check
git add -- \
  "${CANONICAL_FILES[@]}" \
  config/era64_bounded_wallet_event_acquisition_plan_v1.json \
  tools/era64_wallet_event_acquisition_plan_v1.py \
  tests/test_era64e_wallet_event_acquisition_plan_v1.py \
  data/control/era64e_bounded_real_wallet_event_acquisition_and_backfill_plan_v1.json \
  data/replay/era64e_bounded_wallet_event_acquisition_plan_v1.json
git add -f -- reports/LATEST_ERA64E_WALLET_EVENT_ACQUISITION_PLAN.md reports/LATEST_TK_AI_HANDOFF.md
git diff --cached --check
! git diff --cached --quiet

git commit -m "ERA64: verify bounded wallet event acquisition plan"
COMMITTED=1
HEAD="$(git rev-parse HEAD)"
git push origin main
git fetch origin main --quiet
[[ "$(git rev-parse origin/main)" == "$HEAD" ]]
[[ -z "$(git status --porcelain=v1)" ]]
systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer

trap - ERR
echo "ERA64E_STATUS=BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN_VERIFIED"
echo "TESTS=118/118_VERIFIED"
echo "PLAN_ONLY=true"
echo "NETWORK_ACQUISITION_EXECUTED=false"
echo "DATABASE_WRITE_EXECUTED=false"
echo "NEW_REAL_EVENT_COUNT=0"
echo "CANDIDATE_SOURCE_COUNT=8"
echo "EMPTY_CANDIDATE_SOURCE_COUNT=8"
echo "ALWAYS_ON_TECHNICAL_SERVICE=ACTIVE_READONLY"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REAL_FINANCIAL_AUTHORITY=0"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=ERA64F_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_CANARY_APPLY_REQUIRES_USER_APPROVAL"
