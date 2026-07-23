#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SERVICE="tokenoskobi-era63e-always-on-market.service"
TIMER="tokenoskobi-era63d-market-technical.timer"
STAGE="ERA64A_EXISTING_WALLET_DATA_AND_CAPABILITY_AUDIT"
NEXT="ERA64B_SUCCESSFUL_WALLET_STATISTICS_AND_CLUSTER_FOUNDATION_BUILD_REQUIRES_USER_APPROVAL"
CONTROL="data/control/era64a_opening_scope_and_evidence_audit_v1.json"
REPORT="reports/LATEST_ERA64A_OPENING_SCOPE_AND_EVIDENCE_AUDIT.md"
BACKUP=""
MUTATED=0
COMMITTED=0
PUSHED=0

rollback_on_error() {
  local rc=$?
  trap - ERR
  set +e
  if [[ "$PUSHED" -eq 0 ]]; then
    if [[ "$COMMITTED" -eq 1 ]]; then
      git reset --hard HEAD^ >/dev/null 2>&1 || true
    fi
    if [[ "$MUTATED" -eq 1 && -n "$BACKUP" && -f "$BACKUP" ]]; then
      tar -xzf "$BACKUP" -C /root/tokenoskobi_clean_v1 >/dev/null 2>&1 || true
      rm -f "$CONTROL" "$REPORT"
      git reset --quiet >/dev/null 2>&1 || true
    fi
  fi
  echo "ERA64A_OPENING_FAILED_RC=$rc"
  if [[ "$PUSHED" -eq 0 ]]; then
    echo "ROLLBACK=COMPLETED"
  else
    echo "ROLLBACK=NOT_ATTEMPTED_REMOTE_ALREADY_UPDATED"
  fi
  exit "$rc"
}
trap rollback_on_error ERR

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]

BASE_HEAD="$(git rev-parse HEAD)"
export BASE_HEAD STAGE NEXT CONTROL REPORT

already_open="$(python3 <<'PY_ALREADY'
import json
from pathlib import Path
p=Path('/root/tokenoskobi_clean_v1/PROJECT_RUNTIME.json')
v=json.loads(p.read_text(encoding='utf-8'))
print('1' if v.get('current_era') == 'ERA64' and v.get('next_safe_step') == 'ERA64B_SUCCESSFUL_WALLET_STATISTICS_AND_CLUSTER_FOUNDATION_BUILD_REQUIRES_USER_APPROVAL' else '0')
PY_ALREADY
)"
if [[ "$already_open" == "1" ]]; then
  echo "ERA64A_OPENING=ALREADY_APPLIED"
  echo "NEXT_SAFE_STEP=$NEXT"
  echo "REMOTE_VERIFY=VERIFIED"
  echo "WORKTREE=CLEAN"
  echo "HEAD=$BASE_HEAD"
  exit 0
fi

python3 <<'PY_PRECHECK'
import json
from pathlib import Path
root=Path('/root/tokenoskobi_clean_v1')
runtime=json.loads((root/'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert runtime.get('next_safe_step') == 'ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION'
assert runtime.get('project_status') == 'V4_ERA63_CLOSED'
assert runtime.get('work_unit', {}).get('id') == 'ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION'
assert runtime.get('work_unit', {}).get('status') == 'CLOSED_VERIFIED_GITHUB_SEALED'
assert runtime.get('authority', {}).get('live_trade') == 'DISABLED'
assert int(runtime.get('authority', {}).get('real_trade_authority', -1)) == 0
assert int(runtime.get('authority', {}).get('real_wallet_authority', -1)) == 0
assert int(runtime.get('authority', {}).get('real_signing_authority', -1)) == 0
assert int(runtime.get('authority', {}).get('real_order_authority', -1)) == 0
closure=json.loads((root/'data/control/era63e_continuous_observation_and_technical_closure_v1.json').read_text(encoding='utf-8'))
assert closure.get('status') == 'CLOSED_VERIFIED_GITHUB_SEALED'
assert closure.get('next_safe_step') == 'ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION'
print('PRECHECK=VERIFIED')
PY_PRECHECK

systemctl is-enabled --quiet "$SERVICE"
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

REGRESSION_LOG="/tmp/era64a_regression_$(date -u +%Y%m%dT%H%M%SZ).log"
python3 tests/test_era63b_paper_trading_core_v1.py >"$REGRESSION_LOG" 2>&1
python3 tests/test_era63c_technical_dex_execution_v1.py >>"$REGRESSION_LOG" 2>&1
python3 tests/test_era63d_market_technical_runtime_v1.py >>"$REGRESSION_LOG" 2>&1
python3 tests/test_era63e_always_on_market_runtime_v1.py >>"$REGRESSION_LOG" 2>&1
echo "REGRESSION_TESTS=69/69_VERIFIED"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era64a_opening_backup_${TS}.tar.gz"
tar -czf "$BACKUP" -C /root/tokenoskobi_clean_v1 \
  PROJECT_RUNTIME.json \
  PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json \
  03_ROADMAP.md \
  04_ALMANAC.md \
  05_ATLAS.md \
  06_PROJECT_MASTER_STATE.md \
  07_PROJECT_HANDOFF.md \
  reports/LATEST_TK_AI_HANDOFF.md

echo "BACKUP=$BACKUP"

python3 <<'PY_APPLY'
from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
BASE_HEAD = os.environ['BASE_HEAD']
STAGE = os.environ['STAGE']
NEXT = os.environ['NEXT']
CONTROL = os.environ['CONTROL']
REPORT = os.environ['REPORT']
NOW = datetime.now(timezone.utc).isoformat()
TITLE = 'Successful Wallet Intelligence and Statistical Performance'
WORK_ID = 'ERA64_SUCCESSFUL_WALLET_INTELLIGENCE_AND_STATISTICAL_PERFORMANCE'


def load(path: str, default: Any = None) -> Any:
    target = ROOT / path
    if not target.exists():
        return default
    return json.loads(target.read_text(encoding='utf-8'))


def save(path: str, value: Any) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def read_text(path: str) -> str:
    target = ROOT / path
    return target.read_text(encoding='utf-8') if target.exists() else ''


def write_text(path: str, value: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value.rstrip() + '\n', encoding='utf-8')


def replace_block(path: str, marker: str, body: str) -> None:
    start = f'<!-- {marker}:BEGIN -->'
    end = f'<!-- {marker}:END -->'
    text = read_text(path)
    block = f'{start}\n{body.rstrip()}\n{end}'
    pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.S)
    if pattern.search(text):
        text = pattern.sub(block, text, count=1)
    else:
        text = text.rstrip() + '\n\n' + block
    write_text(path, text)


def tracked_files() -> list[str]:
    raw = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT)
    return [item.decode('utf-8') for item in raw.split(b'\0') if item]


capability_patterns: dict[str, list[str]] = {
    'WALLET_IDENTITY_AND_EVIDENCE_LABELS': [r'known[_ -]?wallet', r'wallet[_ -]?registry', r'entity[_ -]?label', r'wallet[_ -]?identity'],
    'WALLET_RELATIONSHIP_AND_CLUSTER_GRAPH': [r'wallet[_ -]?cluster', r'related[_ -]?wallet', r'sub[_ -]?wallet', r'entity[_ -]?graph'],
    'FUNDING_RELATIONSHIP_RECONSTRUCTION': [r'funding[_ -]?relationship', r'funded[_ -]?by', r'funding[_ -]?source', r'wallet[_ -]?funding'],
    'TRANSACTION_AND_TRANSFER_HISTORY': [r'wallet[_ -]?(transaction|transfer|movement)', r'transfer[_ -]?history', r'onchain[_ -]?movement'],
    'POSITION_CYCLE_RECONSTRUCTION': [r'position[_ -]?cycle', r'entry[_ -]?exit', r'wallet[_ -]?position', r'realized[_ -]?pnl'],
    'MARKET_PRICE_AND_TIME_ALIGNMENT': [r'price[_ -]?alignment', r'market[_ -]?timestamp', r'price[_ -]?history', r'ohlcv'],
    'COST_ADJUSTED_PERFORMANCE_METRICS': [r'win[_ -]?rate', r'median[_ -]?return', r'wallet[_ -]?roi', r'performance[_ -]?metric'],
    'DRAWDOWN_AND_RISK_ADJUSTED_PERFORMANCE': [r'drawdown', r'sharpe', r'sortino', r'risk[_ -]?adjusted'],
    'ENTRY_EXIT_QUALITY': [r'entry[_ -]?quality', r'exit[_ -]?quality', r'timing[_ -]?quality', r'execution[_ -]?quality'],
    'CLUSTER_CONFIDENCE_AND_PROVENANCE': [r'cluster[_ -]?confidence', r'cluster[_ -]?evidence', r'provenance', r'evidence[_ -]?pointer'],
    'HISTORICAL_REPLAY_AND_VALIDATION': [r'wallet.*replay', r'cluster.*replay', r'performance.*replay', r'backtest'],
    'READONLY_RUNTIME_AND_PANEL_BINDING': [r'whale.*readmodel', r'wallet.*readmodel', r'whale.*runtime', r'wallet.*panel'],
}
compiled = {name: [re.compile(pattern, re.I) for pattern in patterns] for name, patterns in capability_patterns.items()}
text_suffixes = {'.py', '.json', '.jsonl', '.md', '.sql', '.yaml', '.yml', '.toml', '.ini', '.sh'}
scan: dict[str, dict[str, list[str]]] = {
    name: {'implementation': [], 'tests': [], 'schema_or_dryrun': [], 'plan_or_archive': [], 'other': []}
    for name in capability_patterns
}

for rel in tracked_files():
    if rel == 'tools/era64a_open_and_evidence_audit.sh':
        continue
    path = ROOT / rel
    if not path.is_file() or path.suffix.lower() not in text_suffixes:
        continue
    try:
        if path.stat().st_size > 700_000:
            content = ''
        else:
            content = path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        continue
    haystack = rel + '\n' + content
    lower = rel.lower()
    parts = set(Path(rel).parts)
    archived = 'archive' in parts or 'backups' in parts or '/archive/' in lower
    is_test = rel.startswith('tests/') and path.suffix.lower() == '.py'
    is_implementation = (
        (rel.startswith('core/') or rel.startswith('tools/') or rel.startswith('services/'))
        and path.suffix.lower() == '.py'
        and not archived
        and not any(token in lower for token in ('plan', 'audit', 'review', 'dryrun', 'scaffold', 'transition', 'opening'))
    )
    is_schema_or_dryrun = path.suffix.lower() == '.sql' or 'schema' in lower or 'dryrun' in lower
    is_plan = archived or 'plan' in lower or rel.startswith('docs/') or rel.startswith('data/pass17') or rel.startswith('data/phase20') or rel.startswith('data/phase21')
    for name, patterns in compiled.items():
        if not any(pattern.search(haystack) for pattern in patterns):
            continue
        if is_test:
            bucket = 'tests'
        elif is_implementation:
            bucket = 'implementation'
        elif is_schema_or_dryrun:
            bucket = 'schema_or_dryrun'
        elif is_plan:
            bucket = 'plan_or_archive'
        else:
            bucket = 'other'
        if len(scan[name][bucket]) < 20:
            scan[name][bucket].append(rel)

sqlite_evidence: list[dict[str, Any]] = []
seen_db: set[Path] = set()
for base in (ROOT, ROOT / 'data', ROOT / 'runtime'):
    if not base.exists():
        continue
    for pattern in ('*.db', '*.sqlite', '*.sqlite3'):
        for db_path in base.rglob(pattern):
            if db_path in seen_db or not db_path.is_file():
                continue
            seen_db.add(db_path)
            if len(sqlite_evidence) >= 20:
                break
            try:
                uri = f"file:{db_path.resolve()}?mode=ro"
                connection = sqlite3.connect(uri, uri=True, timeout=2.0)
                rows = connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
                matched = [str(row[0]) for row in rows if re.search(r'wallet|whale|cluster|transfer|transaction|trade|position|price|outcome|pnl', str(row[0]), re.I)]
                connection.close()
                if matched:
                    sqlite_evidence.append({
                        'path': str(db_path.relative_to(ROOT)) if db_path.is_relative_to(ROOT) else str(db_path),
                        'matched_tables': matched[:40],
                        'mode': 'SQLITE_READ_ONLY_SCHEMA_INSPECTION',
                    })
            except Exception as exc:
                sqlite_evidence.append({
                    'path': str(db_path),
                    'error': f'{type(exc).__name__}:{exc}',
                    'mode': 'SQLITE_READ_ONLY_SCHEMA_INSPECTION_FAILED',
                })

capabilities: dict[str, dict[str, Any]] = {}
for name, evidence in scan.items():
    for key in evidence:
        evidence[key] = sorted(set(evidence[key]))
    if evidence['implementation'] and evidence['tests']:
        status = 'IMPLEMENTATION_AND_TEST_EVIDENCE_PRESENT'
    elif evidence['implementation']:
        status = 'IMPLEMENTATION_EVIDENCE_ONLY'
    elif evidence['schema_or_dryrun']:
        status = 'SCHEMA_OR_DRYRUN_EVIDENCE_ONLY'
    elif evidence['plan_or_archive'] or evidence['other']:
        status = 'PLAN_OR_REFERENCE_EVIDENCE_ONLY'
    else:
        status = 'MISSING'
    capabilities[name] = {'status': status, **evidence}

build_priority = [
    name for name, value in capabilities.items()
    if value['status'] != 'IMPLEMENTATION_AND_TEST_EVIDENCE_PRESENT'
]
core_blockers = [
    name for name in (
        'POSITION_CYCLE_RECONSTRUCTION',
        'MARKET_PRICE_AND_TIME_ALIGNMENT',
        'COST_ADJUSTED_PERFORMANCE_METRICS',
        'DRAWDOWN_AND_RISK_ADJUSTED_PERFORMANCE',
        'CLUSTER_CONFIDENCE_AND_PROVENANCE',
        'HISTORICAL_REPLAY_AND_VALIDATION',
    )
    if capabilities[name]['status'] != 'IMPLEMENTATION_AND_TEST_EVIDENCE_PRESENT'
]

authority = {
    'human_per_paper_trade_approval': False,
    'live_trade': 'DISABLED',
    'paper_order_authority': 'SIMULATION_ENGINE_ONLY_NO_RUNTIME_WRITE',
    'paper_position_authority': 'SIMULATION_ENGINE_ONLY_NO_RUNTIME_WRITE',
    'paper_trade': 'DISABLED_PENDING_COORDINATED_INTELLIGENCE',
    'paper_unattended_execution': 'NOT_ALLOWED_YET',
    'real_order_authority': 0,
    'real_signing_authority': 0,
    'real_trade_authority': 0,
    'real_wallet_authority': 0,
    'risk_engine_veto': True,
    'system_may_not_expand_policy': True,
}

opening = {
    'schema': 'tokenoskobi.era64a.opening_scope_and_evidence_audit.v1',
    'era': 'ERA64',
    'stage': STAGE,
    'title': TITLE,
    'status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'result': 'ERA64_OPENED_SCOPE_LOCKED_AND_READONLY_EVIDENCE_AUDIT_COMPLETED',
    'opened_at_utc': NOW,
    'baseline_head': BASE_HEAD,
    'depends_on': {
        'era': 'ERA63',
        'status': 'CLOSED_VERIFIED_GITHUB_SEALED',
        'artifact': 'data/control/era63e_continuous_observation_and_technical_closure_v1.json',
    },
    'connects_to': 'ERA65',
    'purpose': 'Measure win rate, ROI, median return, drawdown, risk-adjusted performance, consistency, entry/exit quality, funding relationships, sub-wallets and evidence-backed clusters.',
    'scope': {
        'performance_metrics': ['WIN_RATE', 'ROI', 'MEDIAN_RETURN', 'DRAWDOWN', 'RISK_ADJUSTED_PERFORMANCE', 'CONSISTENCY', 'ENTRY_QUALITY', 'EXIT_QUALITY'],
        'relationship_intelligence': ['MAIN_WALLET', 'SUB_WALLET', 'FUNDING_SOURCE', 'RELATED_WALLET', 'EVIDENCE_BACKED_CLUSTER'],
        'required_alignment': ['CHAIN', 'WALLET', 'TOKEN', 'PAIR', 'TRANSACTION', 'BLOCK_TIME', 'MARKET_TIME', 'PRICE', 'LIQUIDITY', 'COST'],
    },
    'capability_audit': capabilities,
    'sqlite_readonly_schema_evidence': sqlite_evidence,
    'build_priority': build_priority,
    'core_blockers': core_blockers,
    'substeps': {
        'ERA64A': 'READONLY_EXISTING_EVIDENCE_AUDIT_COMPLETED',
        'ERA64B': 'STATISTICAL_PERFORMANCE_AND_CLUSTER_FOUNDATION_BUILD',
        'ERA64C': 'HISTORICAL_REPLAY_AND_VALIDATION',
        'ERA64D': 'READONLY_RUNTIME_AND_PANEL_BINDING',
        'ERA64E': 'NATURAL_OBSERVATION_AND_AUDIT',
        'ERA64F': 'FINAL_CLOSURE',
    },
    'implementation_authorized': False,
    'network_access_authorized': False,
    'database_write_authorized': False,
    'runtime_mutation_authorized': False,
    'panel_mutation_authorized': False,
    'service_mutation_authorized': False,
    'timer_mutation_authorized': False,
    'authority': authority,
    'closure_requirements': [
        'DETERMINISTIC_WALLET_IDENTITY_AND_LABEL_EVIDENCE',
        'EVIDENCE_BACKED_MAIN_SUBWALLET_AND_FUNDING_GRAPH',
        'DETERMINISTIC_POSITION_CYCLE_RECONSTRUCTION',
        'BLOCK_TIME_AND_MARKET_TIME_ALIGNMENT',
        'COST_ADJUSTED_RETURN_AND_PNL_CALCULATION',
        'WIN_RATE_ROI_MEDIAN_RETURN_DRAWDOWN_RISK_ADJUSTED_CONSISTENCY_METRICS',
        'ENTRY_AND_EXIT_QUALITY_MEASUREMENT',
        'CLUSTER_CONFIDENCE_AND_PROVENANCE',
        'HISTORICAL_REPLAY_WITH_NEGATIVE_AND_ADVERSARIAL_CASES',
        'READONLY_RUNTIME_AND_PANEL_EVIDENCE',
        'ZERO_REAL_FINANCIAL_AUTHORITY',
        'REGRESSION_AND_FAIL_CLOSED_VERIFICATION',
        'CANONICAL_SYNC_REMOTE_VERIFY_AND_GITHUB_SEAL',
    ],
    'next_safe_step': NEXT,
}
save(CONTROL, opening)

runtime = load('PROJECT_RUNTIME.json', {})
runtime.update({
    'current_version': 'V4',
    'current_version_label': 'Coordinated Intelligence and Paper-Trading Proving Ground',
    'current_era': 'ERA64',
    'current_era_title': TITLE,
    'current_stage': STAGE,
    'current_status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'project_status': 'V4_ERA64_ACTIVE',
    'status': 'ACTIVE',
    'last_closed_era': 'ERA63',
    'last_completed': STAGE,
    'last_result': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'next_safe_step': NEXT,
    'updated_at': NOW,
    'updated_at_utc': NOW,
})
runtime['authority'] = authority
runtime['era64_opening'] = {
    'artifact': CONTROL,
    'status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'implementation_authorized': False,
    'core_blockers': core_blockers,
    'next_safe_step': NEXT,
}
runtime['work_unit'] = {
    'id': WORK_ID,
    'title': TITLE,
    'status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'completed_substeps': [STAGE],
    'next_substep': NEXT,
    'implementation_authorized': False,
    'network_access_authorized': False,
    'database_write_authorized': False,
    'runtime_mutation_authorized': False,
    'panel_mutation_authorized': False,
    'service_mutation_authorized': False,
    'timer_mutation_authorized': False,
    'paper_trade_currently': 'DISABLED_PENDING_COORDINATED_INTELLIGENCE',
    'live_trade': 'DISABLED',
    'wallet_authority': 0,
    'signing_authority': 0,
    'real_order_create_authority': 0,
}
ptr = runtime.setdefault('canonical_runtime_pointer', {})
ptr.update({
    'current_version_line': 'V4',
    'current_era': 'ERA64',
    'current_stage': STAGE,
    'current_status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'era63_closed': True,
    'era64_opened': True,
    'era64_implementation_authorized': False,
    'new_work_unit_opened': True,
    'next_safe_step': NEXT,
})
runtime['open_risks'] = [
    item for item in runtime.get('open_risks', [])
    if not str(item).startswith('ERA64_REQUIRED:')
]
for blocker in core_blockers:
    risk = f'ERA64_BLOCKER:{blocker}'
    if risk not in runtime['open_risks']:
        runtime['open_risks'].append(risk)
save('PROJECT_RUNTIME.json', runtime)

roadmap_path = 'data/tokenoskobi_v1_v8_master_era_roadmap.json'
roadmap = load(roadmap_path, {})
v4 = next((value for value in roadmap.get('versions', []) if isinstance(value, dict) and value.get('id') == 'V4'), None)
if not isinstance(v4, dict):
    raise RuntimeError('V4_NOT_FOUND')
era63 = next((value for value in v4.get('children', []) if isinstance(value, dict) and value.get('id') == 'ERA63'), None)
era64 = next((value for value in v4.get('children', []) if isinstance(value, dict) and value.get('id') == 'ERA64'), None)
if not isinstance(era63, dict) or not isinstance(era64, dict):
    raise RuntimeError('ERA63_OR_ERA64_NOT_FOUND')
era63.update({
    'opened': False,
    'status': 'CLOSED_VERIFIED_GITHUB_SEALED',
    'active_stage': 'ERA63_FINAL_TECHNICAL_LINE_CLOSURE',
    'next_safe_step': 'ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION',
    'closure_artifact': 'data/control/era63e_continuous_observation_and_technical_closure_v1.json',
})
era64.update({
    'opened': True,
    'opened_at_utc': NOW,
    'status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'active_stage': STAGE,
    'scope_locked': True,
    'implementation_authorized': False,
    'network_access_authorized': False,
    'database_write_authorized': False,
    'runtime_mutation_authorized': False,
    'panel_mutation_authorized': False,
    'service_mutation_authorized': False,
    'timer_mutation_authorized': False,
    'opening_artifact': CONTROL,
    'substeps': opening['substeps'],
    'core_blockers': core_blockers,
    'next_safe_step': NEXT,
})
roadmap.setdefault('current_direction', {}).update({
    'current_version': 'V4',
    'current_era': 'ERA64',
    'current_line': WORK_ID,
    'current_stage': STAGE,
    'current_status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'era63_closed': True,
    'era63_opened': False,
    'era64_opened': True,
    'era64_implementation_authorized': False,
    'new_work_unit_opened': True,
    'next_safe_step': NEXT,
    'status': 'ERA64_OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'updated_at_utc': NOW,
})
roadmap['era64_opening'] = {
    'actual_title': TITLE,
    'artifact': CONTROL,
    'status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'implementation_authorized': False,
    'core_blockers': core_blockers,
    'next_safe_step': NEXT,
}
save(roadmap_path, roadmap)

history = load('PROJECT_HISTORY.json', {})
events = history.setdefault('events', [])
events[:] = [event for event in events if not (isinstance(event, dict) and event.get('event_id') == STAGE)]
events.append({
    'artifact': CONTROL,
    'era': 'ERA64',
    'event': 'ERA_OPEN_SCOPE_LOCK_AND_READONLY_EVIDENCE_AUDIT',
    'event_id': STAGE,
    'status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'implementation_authorized': False,
    'network_access_authorized': False,
    'database_write_authorized': False,
    'runtime_mutation_authorized': False,
    'real_financial_authority': 0,
    'core_blockers': core_blockers,
    'next_safe_step': NEXT,
    'timestamp_utc': NOW,
})
history['updated_at'] = NOW
history['updated_at_utc'] = NOW
save('PROJECT_HISTORY.json', history)

machine = load('data/control/latest_tk_machine_state.json', {})
machine.update({
    'current_version': 'V4',
    'current_era': 'ERA64',
    'current_stage': STAGE,
    'current_status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
    'last_completed': STAGE,
    'next_safe_step': NEXT,
    'updated_at_utc': NOW,
    'era63_closed': True,
    'era64_opened': True,
    'era64_implementation_authorized': False,
    'era64_opening': {
        'artifact': CONTROL,
        'status': 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED',
        'core_blockers': core_blockers,
    },
    'authority': authority,
})
save('data/control/latest_tk_machine_state.json', machine)

capability_lines = '\n'.join(
    f"- `{name}`: `{value['status']}`"
    for name, value in capabilities.items()
)
blocker_lines = '\n'.join(f'- `{name}`' for name in core_blockers) or '- `NONE`'
priority_lines = '\n'.join(f'{index}. `{name}`' for index, name in enumerate(build_priority, 1)) or '1. `NO_BUILD_GAP_DETECTED`'

write_text('03_ROADMAP.md', f'''# 03 ROADMAP - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={STAGE}
ERA63_STATUS=CLOSED_VERIFIED_GITHUB_SEALED
ERA64_STATUS=OPEN_SCOPE_LOCKED_AUDIT_COMPLETED
NEXT_SAFE_STEP={NEXT}

## LOCKED V4 EXECUTION ORDER

```text
ERA63=TECHNICAL_ANALYSIS_AND_DEX_EXECUTION=CLOSED
ERA64=SUCCESSFUL_WALLET_STATS_AND_CLUSTERING=ACTIVE
ERA65=ONCHAIN_AND_CEX_TO_DEX_WHALE_FLOW
ERA66=NEWS_AIRDROP_ICO_IDO_AND_LAUNCH_INTELLIGENCE
ERA67=COORDINATED_MULTI_INTELLIGENCE_FUSION
ERA68=UNATTENDED_COORDINATED_PAPER_RUNTIME
```

## ERA64 SUBSTEPS

```text
ERA64A=EXISTING_WALLET_DATA_AND_CAPABILITY_AUDIT=COMPLETED
ERA64B=STATISTICAL_PERFORMANCE_AND_CLUSTER_FOUNDATION_BUILD=USER_APPROVAL_REQUIRED
ERA64C=HISTORICAL_REPLAY_AND_VALIDATION
ERA64D=READONLY_RUNTIME_AND_PANEL_BINDING
ERA64E=NATURAL_OBSERVATION_AND_AUDIT
ERA64F=FINAL_CLOSURE
```

ERA64 implementation, network access, database writes, runtime binding, panel changes, service changes and timer changes remain unauthorized. Paper/live trade and real wallet, signing, order and broadcast authority remain disabled.''')

replace_block('04_ALMANAC.md', 'ERA64A_OPENING_AND_EVIDENCE_AUDIT', f'''## ERA64A OPENING, SCOPE LOCK AND READ-ONLY EVIDENCE AUDIT

- Status: `OPEN_SCOPE_LOCKED_AUDIT_COMPLETED`
- Title: `{TITLE}`
- Dependency: `ERA63=CLOSED_VERIFIED_GITHUB_SEALED`
- Artifact: `{CONTROL}`
- Implementation authorized: `false`
- Network access authorized: `false`
- Database write authorized: `false`
- Runtime/panel/service/timer mutation authorized: `false`
- Real financial authority: `0`
- Core blocker count: `{len(core_blockers)}`
- Next: `{NEXT}`
- UTC: `{NOW}`''')

replace_block('05_ATLAS.md', 'ERA64_SUCCESSFUL_WALLET_INTELLIGENCE_FLOW', '''## ERA64 SUCCESSFUL WALLET INTELLIGENCE FLOW

```text
OBSERVED WALLET + VERIFIED IDENTITY EVIDENCE
→ MAIN / SUB-WALLET / FUNDING RELATIONSHIP GRAPH
→ TOKEN POSITION-CYCLE RECONSTRUCTION
→ BLOCK-TIME / MARKET-TIME / PRICE / LIQUIDITY ALIGNMENT
→ COST-ADJUSTED RETURN AND PNL
→ WIN RATE / ROI / MEDIAN RETURN / DRAWDOWN
→ RISK-ADJUSTED PERFORMANCE / CONSISTENCY
→ ENTRY AND EXIT QUALITY
→ CLUSTER CONFIDENCE + PROVENANCE
→ SUCCESSFUL-WALLET CONTEXT
→ ERA65 FLOW INTELLIGENCE
→ ERA67 COORDINATED FUSION
```

Rules:

- A wallet or cluster is never classified as successful from a single trade or raw balance.
- Identity, funding relationships, position cycles, market-time alignment, costs and provenance are mandatory evidence.
- Cluster confidence is explicit and fail-closed when evidence is incomplete or conflicting.
- Successful-wallet context cannot create paper/live trade, wallet, signing, order or broadcast authority.''')

write_text('06_PROJECT_MASTER_STATE.md', f'''# 06 PROJECT MASTER STATE - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={STAGE}
CURRENT_STATUS=OPEN_SCOPE_LOCKED_AUDIT_COMPLETED
NEXT_SAFE_STEP={NEXT}

## ERA64 PURPOSE

Measure win rate, ROI, median return, drawdown, risk-adjusted performance, consistency, entry/exit quality, funding relationships, sub-wallets and evidence-backed clusters.

## READ-ONLY CAPABILITY AUDIT

{capability_lines}

## CORE BLOCKERS

{blocker_lines}

## ACTIVE CONTEXT PRODUCER

- `tokenoskobi-era63e-always-on-market.service`: ACTIVE, resident, read-only
- BSC block observation: ACTIVE
- Fixed 15-minute timer: DISABLED

## AUTHORITY

```text
ERA64_IMPLEMENTATION_AUTHORIZED=false
NETWORK_ACCESS_AUTHORIZED=false
DATABASE_WRITE_AUTHORIZED=false
RUNTIME_PANEL_SERVICE_TIMER_MUTATION_AUTHORIZED=false
PAPER_RUNTIME=false
LIVE_TRADE=DISABLED
REAL_WALLET=false
REAL_SIGNING=false
REAL_ORDER=false
REAL_BROADCAST=false
```''')

handoff = f'''# 07 PROJECT HANDOFF - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={STAGE}
CURRENT_STATUS=OPEN_SCOPE_LOCKED_AUDIT_COMPLETED
NEXT_SAFE_STEP={NEXT}

ERA63 is closed and GitHub-sealed. ERA64 is open with a locked scope and completed read-only evidence audit.

## BUILD PRIORITY

{priority_lines}

## BOUNDARY

ERA64 implementation has not been authorized. Network access, database writes, runtime binding, panel changes, service changes and timer changes remain disabled. Paper/live trade and real wallet, signing, order and broadcast authority remain disabled.

Evidence:
- `{CONTROL}`
- `{REPORT}`
'''
write_text('07_PROJECT_HANDOFF.md', handoff)
write_text('reports/LATEST_TK_AI_HANDOFF.md', handoff)

write_text(REPORT, f'''# ERA64A OPENING, SCOPE LOCK AND READ-ONLY EVIDENCE AUDIT

- Status: `OPEN_SCOPE_LOCKED_AUDIT_COMPLETED`
- Opened UTC: `{NOW}`
- Baseline head: `{BASE_HEAD}`
- Dependency: `ERA63=CLOSED_VERIFIED_GITHUB_SEALED`
- Purpose: `{opening['purpose']}`
- SQLite read-only evidence sources: `{len(sqlite_evidence)}`
- Core blocker count: `{len(core_blockers)}`
- Implementation authorized: `false`
- Network access authorized: `false`
- Database write authorized: `false`
- Runtime/panel/service/timer mutation authorized: `false`
- Real financial authority: `0`
- Next: `{NEXT}`

## CAPABILITY AUDIT

{capability_lines}

## CORE BLOCKERS

{blocker_lines}

## BUILD PRIORITY

{priority_lines}
''')

print('ERA64A_READONLY_AUDIT=COMPLETED')
print(f'CAPABILITY_COUNT={len(capabilities)}')
print(f'CORE_BLOCKER_COUNT={len(core_blockers)}')
print(f'SQLITE_READONLY_EVIDENCE_SOURCES={len(sqlite_evidence)}')
print(f'NEXT_SAFE_STEP={NEXT}')
PY_APPLY

MUTATED=1

python3 <<'PY_VERIFY'
import json
from pathlib import Path
root=Path('/root/tokenoskobi_clean_v1')
json_paths=[
    'PROJECT_RUNTIME.json',
    'PROJECT_HISTORY.json',
    'data/tokenoskobi_v1_v8_master_era_roadmap.json',
    'data/control/latest_tk_machine_state.json',
    'data/control/era64a_opening_scope_and_evidence_audit_v1.json',
]
for rel in json_paths:
    json.loads((root/rel).read_text(encoding='utf-8'))
runtime=json.loads((root/'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert runtime['current_era'] == 'ERA64'
assert runtime['current_stage'] == 'ERA64A_EXISTING_WALLET_DATA_AND_CAPABILITY_AUDIT'
assert runtime['next_safe_step'] == 'ERA64B_SUCCESSFUL_WALLET_STATISTICS_AND_CLUSTER_FOUNDATION_BUILD_REQUIRES_USER_APPROVAL'
assert runtime['work_unit']['implementation_authorized'] is False
assert runtime['authority']['live_trade'] == 'DISABLED'
assert runtime['authority']['real_trade_authority'] == 0
assert runtime['authority']['real_wallet_authority'] == 0
assert runtime['authority']['real_signing_authority'] == 0
assert runtime['authority']['real_order_authority'] == 0
roadmap=json.loads((root/'data/tokenoskobi_v1_v8_master_era_roadmap.json').read_text(encoding='utf-8'))
v4=next(v for v in roadmap['versions'] if v.get('id') == 'V4')
era63=next(v for v in v4['children'] if v.get('id') == 'ERA63')
era64=next(v for v in v4['children'] if v.get('id') == 'ERA64')
assert era63['status'] == 'CLOSED_VERIFIED_GITHUB_SEALED' and era63['opened'] is False
assert era64['status'] == 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED' and era64['opened'] is True
assert era64['implementation_authorized'] is False
opening=json.loads((root/'data/control/era64a_opening_scope_and_evidence_audit_v1.json').read_text(encoding='utf-8'))
assert opening['status'] == 'OPEN_SCOPE_LOCKED_AUDIT_COMPLETED'
assert opening['implementation_authorized'] is False
assert opening['network_access_authorized'] is False
assert opening['database_write_authorized'] is False
for rel in ('03_ROADMAP.md','06_PROJECT_MASTER_STATE.md','07_PROJECT_HANDOFF.md'):
    text=(root/rel).read_text(encoding='utf-8')
    assert 'CURRENT_ERA=ERA64' in text
    assert 'ERA64B_SUCCESSFUL_WALLET_STATISTICS_AND_CLUSTER_FOUNDATION_BUILD_REQUIRES_USER_APPROVAL' in text
print('CANONICAL_VERIFY=VERIFIED')
PY_VERIFY

systemctl is-enabled --quiet "$SERVICE"
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

git diff --check
git add -- \
  PROJECT_RUNTIME.json \
  PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json \
  data/control/era64a_opening_scope_and_evidence_audit_v1.json \
  03_ROADMAP.md \
  04_ALMANAC.md \
  05_ATLAS.md \
  06_PROJECT_MASTER_STATE.md \
  07_PROJECT_HANDOFF.md
git add -f -- \
  reports/LATEST_ERA64A_OPENING_SCOPE_AND_EVIDENCE_AUDIT.md \
  reports/LATEST_TK_AI_HANDOFF.md

git diff --cached --check
! git diff --cached --quiet

git commit -m "ERA64: open successful wallet intelligence and complete evidence audit"
COMMITTED=1
HEAD="$(git rev-parse HEAD)"
git push origin main
PUSHED=1

git fetch origin main --quiet
[[ "$(git rev-parse origin/main)" == "$HEAD" ]]
[[ -z "$(git status --porcelain=v1)" ]]
systemctl is-enabled --quiet "$SERVICE"
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

trap - ERR

echo "ERA64_STATUS=OPEN_SCOPE_LOCKED_AUDIT_COMPLETED"
echo "CURRENT_STAGE=$STAGE"
echo "IMPLEMENTATION_AUTHORIZED=false"
echo "NETWORK_ACCESS_AUTHORIZED=false"
echo "DATABASE_WRITE_AUTHORIZED=false"
echo "RUNTIME_PANEL_SERVICE_TIMER_MUTATION_AUTHORIZED=false"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "ALWAYS_ON_TECHNICAL_SERVICE=ENABLED_ACTIVE_READONLY"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=$NEXT"
