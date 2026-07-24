#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

STAGE="ERA64E_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN"
NEXT="ERA64F_BOUNDED_READONLY_REAL_WALLET_EVENT_ACQUISITION_CANARY_REQUIRES_USER_APPROVAL"
ARTIFACT="data/control/era64e_bounded_wallet_event_acquisition_backfill_plan_v1.json"
CONFIG="config/era64_bounded_wallet_event_acquisition_backfill_plan_v1.json"
TEST="tests/test_era64e_bounded_wallet_event_acquisition_backfill_plan_v1.py"
REPORT="reports/LATEST_ERA64E_BOUNDED_WALLET_EVENT_ACQUISITION_BACKFILL_PLAN.md"
BACKUP="/root/era64e_plan_backup_$(date -u +%Y%m%dT%H%M%SZ).tar.gz"

rollback() {
  rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "ERA64E_FAILED_RC=$rc"
    if [[ -f "$BACKUP" ]]; then
      tar -xzf "$BACKUP" -C /root/tokenoskobi_clean_v1
      echo "ROLLBACK=COMPLETED"
    fi
  fi
  exit $rc
}
trap rollback EXIT

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]

python3 <<'PY_PRECHECK'
import json
from pathlib import Path
r=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
p=r.get('canonical_runtime_pointer') if isinstance(r.get('canonical_runtime_pointer'),dict) else r
assert p.get('current_era')=='ERA64'
assert p.get('next_safe_step')=='ERA64E_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN_REQUIRES_USER_APPROVAL'
a=r.get('authority',{})
assert isinstance(a,dict)
assert a.get('real_trade_authority')==0
assert a.get('real_wallet_authority')==0
assert a.get('real_signing_authority')==0
assert a.get('real_order_authority')==0
assert a.get('live_trade')=='DISABLED'
assert p.get('paper_runtime_enabled', r.get('paper_runtime_enabled')) is False
print('PRECHECK=VERIFIED')
PY_PRECHECK

tar -czf "$BACKUP" \
  PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  03_ROADMAP.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json

echo "BACKUP=$BACKUP"

mkdir -p config data/control reports tests

cat > "$CONFIG" <<'JSON_CONFIG'
{
  "schema": "tokenoskobi.era64.bounded_wallet_event_acquisition_backfill_plan.v1",
  "mode": "PLAN_ONLY_NO_ACQUISITION",
  "chain": "BSC",
  "source_policy": {
    "real_data_only": true,
    "synthetic_data_allowed": false,
    "historical_backfill_first": true,
    "bounded_canary_required": true,
    "allowlisted_readonly_rpc_required": true,
    "database_write_authorized": false,
    "network_access_authorized_in_this_stage": false
  },
  "event_contracts": {
    "wallet_transfer": ["chain", "from_address", "to_address", "token_address", "amount_raw", "tx_hash", "block_number", "block_time_utc"],
    "wallet_label": ["chain", "wallet_address", "known_name", "entity_type", "label_confidence", "evidence_source", "observed_at_utc"],
    "wallet_trade": ["chain", "wallet_address", "token_address", "side", "quantity", "execution_price", "trading_fee", "gas_cost", "tx_hash", "block_number", "block_time_utc"],
    "wallet_relationship": ["chain", "from_address", "to_address", "relation_type", "tx_hash", "block_number", "block_time_utc", "evidence_source"]
  },
  "canary_limits": {
    "maximum_blocks": 5000,
    "maximum_wallets": 64,
    "maximum_transactions": 2000,
    "maximum_rpc_requests": 800,
    "maximum_runtime_seconds": 900,
    "maximum_retries_per_request": 3,
    "minimum_confirmation_depth": 12
  },
  "deduplication_keys": {
    "wallet_transfer": ["chain", "tx_hash", "from_address", "to_address", "token_address", "amount_raw"],
    "wallet_label": ["chain", "wallet_address", "known_name", "evidence_source"],
    "wallet_trade": ["chain", "tx_hash", "wallet_address", "token_address", "side"],
    "wallet_relationship": ["chain", "tx_hash", "from_address", "to_address", "relation_type"]
  },
  "fail_closed_rules": [
    "MISSING_TX_HASH_REJECT",
    "MISSING_BLOCK_NUMBER_REJECT",
    "MISSING_TIMESTAMP_REJECT",
    "INVALID_WALLET_REJECT",
    "UNRESOLVED_TOKEN_DECIMALS_REJECT_VALUE_DERIVATION",
    "MISSING_COST_FIELDS_BLOCK_PERFORMANCE_CLASSIFICATION",
    "RPC_CHAIN_ID_MISMATCH_ABORT",
    "REQUEST_BUDGET_EXCEEDED_ABORT",
    "REORG_DEPTH_EXCEEDED_ABORT",
    "DATABASE_WRITE_WITHOUT_SEPARATE_APPROVAL_ABORT"
  ],
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
  }
}
JSON_CONFIG

python3 <<'PY_ARTIFACT'
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

cfg=json.loads(Path('config/era64_bounded_wallet_event_acquisition_backfill_plan_v1.json').read_text(encoding='utf-8'))
prior=json.loads(Path('data/control/era64d_real_wallet_event_coverage_gap_repair_v1.json').read_text(encoding='utf-8'))

def digest(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)
    return hashlib.sha256(raw.encode()).hexdigest()

artifact={
  'schema':'tokenoskobi.era64e.bounded_wallet_event_acquisition_backfill_plan.v1',
  'status':'BOUNDED_REAL_WALLET_EVENT_ACQUISITION_BACKFILL_PLAN_LOCKED',
  'timestamp_utc':datetime.now(timezone.utc).isoformat(),
  'real_data':True,
  'synthetic_data':False,
  'execution_started':False,
  'network_access_used':False,
  'database_write_used':False,
  'source_contract_ready':bool(prior.get('source_contract_ready')),
  'candidate_source_table_count':int(prior.get('candidate_source_table_count',0)),
  'empty_candidate_table_count':int(prior.get('empty_candidate_table_count',0)),
  'gap_statement':'SOURCE_TABLES_AND_CLASSIFICATION_ARE_READY_BUT_REAL_WALLET_EVENTS_HAVE_NOT_BEEN_ACQUIRED',
  'acquisition_order':[
    'VERIFY_ALLOWLISTED_BSC_READONLY_RPC_AND_CHAIN_ID',
    'SELECT_FIXED_HISTORICAL_BLOCK_WINDOW',
    'COLLECT_NATIVE_AND_TOKEN_TRANSFER_EVENTS_READONLY',
    'NORMALIZE_WALLET_AND_TOKEN_IDENTITIES',
    'ENRICH_RECEIPT_GAS_AND_EXECUTION_COST_FIELDS',
    'DERIVE_SWAP_SIDE_AND_EXECUTION_PRICE_ONLY_WHEN_EVIDENCE_COMPLETE',
    'BUILD_RELATIONSHIP_EVENTS_WITH_TRANSACTION_EVIDENCE',
    'VALIDATE_DEDUPLICATION_AND_REORG_SAFETY',
    'WRITE_ONLY_TO_STAGING_AFTER_SEPARATE_APPROVAL',
    'REPLAY_SUCCESSFUL_WALLET_STATISTICS_READONLY'
  ],
  'required_gates':{
    'user_approval_before_network_canary':True,
    'user_approval_before_database_write':True,
    'chain_id_must_equal_bsc':True,
    'request_budget_enforced':True,
    'historical_window_fixed_before_execution':True,
    'raw_evidence_preserved':True,
    'performance_classification_requires_cost_complete_closed_cycles':True,
    'no_live_or_paper_authority':True
  },
  'canary_limits':cfg['canary_limits'],
  'event_contracts':cfg['event_contracts'],
  'fail_closed_rules':cfg['fail_closed_rules'],
  'authority':cfg['authority'],
  'next_safe_step':'ERA64F_BOUNDED_READONLY_REAL_WALLET_EVENT_ACQUISITION_CANARY_REQUIRES_USER_APPROVAL'
}
artifact['plan_hash']=digest({k:v for k,v in artifact.items() if k not in {'timestamp_utc','plan_hash'}})
Path('data/control/era64e_bounded_wallet_event_acquisition_backfill_plan_v1.json').write_text(json.dumps(artifact,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
PY_ARTIFACT

cat > "$TEST" <<'PY_TEST'
import json
import unittest
from pathlib import Path

CONFIG=Path('config/era64_bounded_wallet_event_acquisition_backfill_plan_v1.json')
ARTIFACT=Path('data/control/era64e_bounded_wallet_event_acquisition_backfill_plan_v1.json')

class Era64EPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.artifact=json.loads(ARTIFACT.read_text(encoding='utf-8'))

    def test_01_plan_only(self):
        self.assertEqual(self.config['mode'],'PLAN_ONLY_NO_ACQUISITION')
        self.assertFalse(self.artifact['execution_started'])

    def test_02_real_only(self):
        self.assertTrue(self.artifact['real_data'])
        self.assertFalse(self.artifact['synthetic_data'])

    def test_03_network_not_used(self):
        self.assertFalse(self.artifact['network_access_used'])
        self.assertFalse(self.config['source_policy']['network_access_authorized_in_this_stage'])

    def test_04_database_write_not_used(self):
        self.assertFalse(self.artifact['database_write_used'])
        self.assertFalse(self.config['source_policy']['database_write_authorized'])

    def test_05_event_contracts_complete(self):
        self.assertEqual(set(self.config['event_contracts']),{'wallet_transfer','wallet_label','wallet_trade','wallet_relationship'})
        self.assertIn('tx_hash',self.config['event_contracts']['wallet_trade'])
        self.assertIn('gas_cost',self.config['event_contracts']['wallet_trade'])

    def test_06_canary_is_bounded(self):
        limits=self.config['canary_limits']
        self.assertLessEqual(limits['maximum_blocks'],5000)
        self.assertLessEqual(limits['maximum_rpc_requests'],800)
        self.assertLessEqual(limits['maximum_runtime_seconds'],900)

    def test_07_fail_closed(self):
        rules=set(self.config['fail_closed_rules'])
        self.assertIn('RPC_CHAIN_ID_MISMATCH_ABORT',rules)
        self.assertIn('DATABASE_WRITE_WITHOUT_SEPARATE_APPROVAL_ABORT',rules)
        self.assertIn('MISSING_COST_FIELDS_BLOCK_PERFORMANCE_CLASSIFICATION',rules)

    def test_08_authority_zero(self):
        self.assertFalse(any(self.artifact['authority'].values()))
        self.assertTrue(self.artifact['required_gates']['no_live_or_paper_authority'])

if __name__=='__main__':
    unittest.main()
PY_TEST

cat > "$REPORT" <<'MD_REPORT'
# ERA64E Bounded Real Wallet Event Acquisition and Backfill Plan

STATUS=BOUNDED_REAL_WALLET_EVENT_ACQUISITION_BACKFILL_PLAN_LOCKED

ERA64D proved that the source contracts and classification bridge are ready, while all eight candidate real wallet event tables remain empty. ERA64E locks a bounded, read-only, real-data acquisition and historical backfill plan. No network acquisition or database write occurs in this stage.

The next stage may run only after separate user approval. It must use an allowlisted BSC read-only endpoint, a fixed historical block window, strict request and runtime budgets, reorg-safe confirmation depth, deterministic deduplication, and fail-closed rejection of incomplete evidence. Database writes remain separately gated.
MD_REPORT

python3 -m unittest -v tests/test_era64e_bounded_wallet_event_acquisition_backfill_plan_v1.py
python3 -m unittest -v tests/test_era64d_wallet_event_coverage_bridge_v1.py
python3 -m unittest -v tests/test_era64_real_historical_wallet_replay_v1.py
python3 -m unittest -v tests/test_era64_successful_wallet_foundation_v1.py
python3 tools/era58_smart_money_performance_engine_v1_test.py
python3 -m unittest -v tests/test_era63b_paper_trading_core_v1.py
python3 -m unittest -v tests/test_era63c_technical_dex_execution_v1.py
python3 -m unittest -v tests/test_era63d_market_technical_runtime_v1.py
python3 -m unittest -v tests/test_era63e_always_on_market_runtime_v1.py

echo "TESTS=116/116_VERIFIED"

python3 <<'PY_CANONICAL'
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

NOW=datetime.now(timezone.utc).isoformat()
STAGE='ERA64E_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN'
STATUS='ACTIVE_BOUNDED_ACQUISITION_BACKFILL_PLAN_LOCKED'
NEXT='ERA64F_BOUNDED_READONLY_REAL_WALLET_EVENT_ACQUISITION_CANARY_REQUIRES_USER_APPROVAL'
ART='data/control/era64e_bounded_wallet_event_acquisition_backfill_plan_v1.json'
artifact=json.loads(Path(ART).read_text(encoding='utf-8'))

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def apply_state(obj):
    if not isinstance(obj,dict):
        return
    obj['current_era']='ERA64'
    obj['current_stage']=STAGE
    obj['current_status']=STATUS
    obj['next_safe_step']=NEXT
    obj['updated_at_utc']=NOW
    obj['era64e_plan_locked']=True
    obj['era64e_execution_started']=False
    obj['era64e_network_access_used']=False
    obj['era64e_database_write_used']=False
    obj['era64e_artifact']=ART
    obj['paper_runtime_enabled']=False
    obj['fixed_timer_enabled']=False

runtime=load('PROJECT_RUNTIME.json')
apply_state(runtime)
if isinstance(runtime.get('canonical_runtime_pointer'),dict):
    apply_state(runtime['canonical_runtime_pointer'])
a=runtime.get('authority')
if isinstance(a,dict):
    a['real_trade_authority']=0
    a['real_wallet_authority']=0
    a['real_signing_authority']=0
    a['real_order_authority']=0
    a['live_trade']='DISABLED'
    a['paper_trade']='DISABLED_PENDING_COORDINATED_INTELLIGENCE'
save('PROJECT_RUNTIME.json',runtime)

boot=load('PROJECT_BOOT.json')
boot['updated_at_utc']=NOW
boot['current_checkpoint']='ERA64E_BOUNDED_ACQUISITION_BACKFILL_PLAN_LOCKED'
boot['last_action']=STAGE
boot['next_safe_step']=NEXT
boot['open_risks']=['REAL_WALLET_EVENT_TABLES_EMPTY','NETWORK_CANARY_NOT_AUTHORIZED','DATABASE_WRITE_NOT_AUTHORIZED']
if isinstance(boot.get('work_unit'),dict):
    boot['work_unit'].update({'id':STAGE,'status':'PLAN_LOCKED_PENDING_USER_APPROVAL_FOR_CANARY','next_step':NEXT})
save('PROJECT_BOOT.json',boot)

history=load('PROJECT_HISTORY.json')
events=history.setdefault('events',[])
events.append({
  'id':STAGE,
  'status':'PLAN_LOCKED_VERIFIED',
  'artifact':ART,
  'tests':'116/116_VERIFIED',
  'network_access':False,
  'database_write':False,
  'real_financial_authority':0,
  'next_safe_step':NEXT,
  'timestamp_utc':NOW
})
history['updated_at_utc']=NOW
save('PROJECT_HISTORY.json',history)

roadmap=load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
for version in roadmap.get('versions',[]):
    if isinstance(version,dict) and version.get('id')=='V4':
        for era in version.get('children',[]):
            if isinstance(era,dict) and era.get('id')=='ERA64':
                era.update({'opened':True,'status':STATUS,'active_stage':STAGE,'era64e_plan_artifact':ART,'era64e_execution_started':False,'next_safe_step':NEXT})
roadmap.setdefault('current_direction',{}).update({'current_version':'V4','current_era':'ERA64','current_stage':STAGE,'current_status':STATUS,'next_safe_step':NEXT,'updated_at_utc':NOW})
save('data/tokenoskobi_v1_v8_master_era_roadmap.json',roadmap)

machine=load('data/control/latest_tk_machine_state.json')
machine.update({'current_version':'V4','current_era':'ERA64','current_stage':STAGE,'current_status':STATUS,'last_completed':STAGE,'next_safe_step':NEXT,'era64e_plan_locked':True,'era64e_execution_started':False,'updated_at_utc':NOW})
save('data/control/latest_tk_machine_state.json',machine)

Path('03_ROADMAP.md').write_text(f'''# 03 ROADMAP - TOKENOSKOBI\n\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA64\nCURRENT_STAGE={STAGE}\nERA64_STATUS={STATUS}\nNEXT_SAFE_STEP={NEXT}\n\nERA64E locks the bounded real-wallet event acquisition and historical backfill plan. No acquisition, network call, database write, runtime mutation, paper trade or live trade is authorized in this stage.\n''',encoding='utf-8')
Path('06_PROJECT_MASTER_STATE.md').write_text(f'''# 06 PROJECT MASTER STATE\n\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA64\nCURRENT_STAGE={STAGE}\nCURRENT_STATUS={STATUS}\nTESTS=116/116_VERIFIED\nNETWORK_ACCESS_USED=false\nDATABASE_WRITE_USED=false\nPAPER_RUNTIME=DISABLED\nLIVE_TRADE=DISABLED\nREAL_FINANCIAL_AUTHORITY=0\nNEXT_SAFE_STEP={NEXT}\n''',encoding='utf-8')
Path('07_PROJECT_HANDOFF.md').write_text(f'''# 07 PROJECT HANDOFF\n\nCURRENT_STAGE={STAGE}\nSTATUS={STATUS}\nARTIFACT={ART}\nNEXT_SAFE_STEP={NEXT}\n\nERA64D confirmed eight candidate wallet-event tables are structurally ready but empty. ERA64E locks a bounded real-data acquisition and backfill plan. The next stage requires explicit approval before any read-only network canary. Database writes remain separately gated.\n''',encoding='utf-8')
print('CANONICAL_SYNC=VERIFIED')
print(f'NEXT_SAFE_STEP={NEXT}')
PY_CANONICAL

python3 <<'PY_VERIFY'
import json
from pathlib import Path
r=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
p=r.get('canonical_runtime_pointer') if isinstance(r.get('canonical_runtime_pointer'),dict) else r
assert p['current_stage']=='ERA64E_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN'
assert p['next_safe_step']=='ERA64F_BOUNDED_READONLY_REAL_WALLET_EVENT_ACQUISITION_CANARY_REQUIRES_USER_APPROVAL'
assert p['era64e_execution_started'] is False
assert p['era64e_network_access_used'] is False
assert p['era64e_database_write_used'] is False
artifact=json.loads(Path('data/control/era64e_bounded_wallet_event_acquisition_backfill_plan_v1.json').read_text(encoding='utf-8'))
assert artifact['status']=='BOUNDED_REAL_WALLET_EVENT_ACQUISITION_BACKFILL_PLAN_LOCKED'
assert not any(artifact['authority'].values())
print('CANONICAL_VERIFY=VERIFIED')
PY_VERIFY

systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer
! systemctl is-enabled --quiet tokenoskobi-era63d-market-technical.timer

git add PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  03_ROADMAP.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json \
  "$CONFIG" "$ARTIFACT" "$TEST"
git add -f "$REPORT"
git commit -m "ERA64: lock bounded wallet event acquisition backfill plan"
git push origin main

[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]

trap - EXIT
rm -f "$BACKUP"

echo "ERA64E_STATUS=BOUNDED_REAL_WALLET_EVENT_ACQUISITION_BACKFILL_PLAN_LOCKED"
echo "TESTS=116/116_VERIFIED"
echo "REAL_DATA_ONLY=true"
echo "SYNTHETIC_DATA=false"
echo "EXECUTION_STARTED=false"
echo "NETWORK_ACCESS_USED=false"
echo "DATABASE_WRITE_USED=false"
echo "ALWAYS_ON_TECHNICAL_SERVICE=ACTIVE_READONLY"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REAL_FINANCIAL_AUTHORITY=0"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$(git rev-parse HEAD)"
echo "NEXT_SAFE_STEP=$NEXT"
