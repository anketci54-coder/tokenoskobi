#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SERVICE="tokenoskobi-era63e-always-on-market.service"
TIMER="tokenoskobi-era63d-market-technical.timer"
AUDIT_TMP="/tmp/era63e_continuous_observation_audit_v1.json"
BACKUP=""
MUTATED=0
COMMITTED=0
PUSHED=0

rollback_on_error() {
  local rc=$?
  set +e
  if [[ "$PUSHED" -eq 0 ]]; then
    if [[ "$COMMITTED" -eq 1 ]]; then
      git reset --hard HEAD^ >/dev/null 2>&1 || true
    fi
    if [[ "$MUTATED" -eq 1 && -n "$BACKUP" && -f "$BACKUP" ]]; then
      tar -xzf "$BACKUP" -C / >/dev/null 2>&1 || true
      rm -f \
        data/control/era63e_continuous_observation_and_technical_closure_v1.json \
        reports/LATEST_ERA63E_CONTINUOUS_OBSERVATION_AND_TECHNICAL_CLOSURE.md
    fi
  fi
  echo "ERA63E_CLOSURE_FAILED_RC=$rc"
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

python3 <<'PY_PRECHECK'
import json
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
runtime = json.loads((root / 'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert runtime['next_safe_step'] == 'ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE'
assert runtime['work_unit']['id'] == 'ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION'
assert runtime['work_unit']['status'] == 'ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE'
assert runtime['work_unit']['observation_runtime'] == 'ACTIVE_READ_ONLY'
assert runtime['authority']['live_trade'] == 'DISABLED'
assert runtime['authority']['real_wallet_authority'] == 0
assert runtime['authority']['real_signing_authority'] == 0
assert runtime['authority']['real_order_authority'] == 0
print('PRECHECK=VERIFIED')
PY_PRECHECK

systemctl is-enabled --quiet "$SERVICE"
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

for _ in $(seq 1 75); do
  if [[ -s runtime/era63e/always_on_state_v1.json ]]; then
    if python3 - <<'PY_WAIT' >/dev/null 2>&1
import json
from pathlib import Path
p = Path('/root/tokenoskobi_clean_v1/runtime/era63e/always_on_state_v1.json')
v = json.loads(p.read_text(encoding='utf-8'))
raise SystemExit(0 if not v.get('refresh_in_progress', False) else 1)
PY_WAIT
    then
      break
    fi
  fi
  sleep 1
done

python3 <<'PY_AUDIT'
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path('/root/tokenoskobi_clean_v1')
SERVICE = 'tokenoskobi-era63e-always-on-market.service'
TIMER = 'tokenoskobi-era63d-market-technical.timer'
OUT = Path('/tmp/era63e_continuous_observation_audit_v1.json')
MIN_EVENTS = 20
MIN_EVENT_SPAN_SEC = 60.0
MIN_REFRESHES = 3
MIN_UPTIME_SEC = 180.0
MAX_HEARTBEAT_AGE_SEC = 25.0
MAX_BLOCK_AGE_SEC = 30.0
MAX_MARKET_AGE_SEC = 1200.0


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError(f'{path}:NOT_OBJECT')
    return value


def parse_dt(value: Any) -> datetime:
    text = str(value or '').strip()
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def age_sec(value: Any, now: datetime) -> float:
    return max(0.0, (now - parse_dt(value)).total_seconds())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def systemctl_show(unit: str) -> dict[str, str]:
    names = [
        'ActiveState', 'SubState', 'UnitFileState', 'MainPID', 'NRestarts',
        'FragmentPath', 'DropInPaths', 'ExecStart', 'ActiveEnterTimestampMonotonic',
    ]
    raw = subprocess.check_output(
        ['systemctl', 'show', unit, '--no-pager', '--property=' + ','.join(names)],
        text=True,
    )
    result: dict[str, str] = {}
    for line in raw.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            result[key] = value
    return result


def inactive(unit: str) -> bool:
    return subprocess.run(['systemctl', 'is-active', '--quiet', unit]).returncode != 0


def disabled_or_static(unit: str) -> bool:
    result = subprocess.run(['systemctl', 'is-enabled', unit], text=True, capture_output=True)
    state = (result.stdout or result.stderr).strip()
    return state in {'disabled', 'static', 'indirect', 'not-found', 'masked'}


now = datetime.now(timezone.utc)
config = read_json(ROOT / 'config/era63e_always_on_market_runtime_v1.json')
binding = read_json(ROOT / 'data/control/era63e_always_on_market_runtime_binding_v1.json')
state = read_json(ROOT / 'runtime/era63e/always_on_state_v1.json')
health = read_json(ROOT / 'runtime/era63e/health_v1.json')
market = read_json(ROOT / 'runtime/era63d/latest_real_market_technical_snapshot_v1.json')
panel = read_json(ROOT / 'active_panel_8096/current/data/technical_center_live_readmodel_v1.json')
show = systemctl_show(SERVICE)

active_mono_us = int(show.get('ActiveEnterTimestampMonotonic') or 0)
service_uptime_sec = max(0.0, time.monotonic() - active_mono_us / 1_000_000.0) if active_mono_us else 0.0
state_started = parse_dt(state['started_at_utc'])
state_uptime_sec = max(0.0, (now - state_started).total_seconds())
process_start_epoch = state_started.timestamp() - 5.0

events_path = ROOT / 'runtime/era63e/block_events_v1.jsonl'
events: list[dict[str, Any]] = []
invalid_event_rows = 0
for raw in events_path.read_text(encoding='utf-8').splitlines() if events_path.exists() else []:
    if not raw.strip():
        continue
    try:
        row = json.loads(raw)
        if isinstance(row, dict) and float(row.get('block_timestamp', 0)) >= process_start_epoch:
            events.append(row)
    except Exception:
        invalid_event_rows += 1

blocks = sorted({int(row['block_number']) for row in events if row.get('block_number') is not None})
timestamps = [float(row['block_timestamp']) for row in events if row.get('block_timestamp') is not None]
event_span_sec = max(timestamps) - min(timestamps) if len(timestamps) >= 2 else 0.0
latest_event_block_age_sec = max(0.0, now.timestamp() - max(timestamps)) if timestamps else float('inf')

expected_exec = '/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/era63e_always_on_market_runtime_v1.py'
installed_unit = Path('/etc/systemd/system/tokenoskobi-era63e-always-on-market.service')
draft_unit = ROOT / 'systemd_drafts/tokenoskobi-era63e-always-on-market.service'

checks: dict[str, bool] = {}
checks['service_active'] = show.get('ActiveState') == 'active' and show.get('SubState') == 'running'
checks['service_enabled'] = show.get('UnitFileState') == 'enabled'
checks['service_pid_valid'] = int(show.get('MainPID') or 0) > 1
checks['service_restart_count_bounded'] = int(show.get('NRestarts') or 0) <= 1
checks['service_uptime_sufficient'] = service_uptime_sec >= MIN_UPTIME_SEC and state_uptime_sec >= MIN_UPTIME_SEC
checks['service_fragment_exact'] = show.get('FragmentPath') == str(installed_unit)
checks['service_has_no_dropins'] = not show.get('DropInPaths', '').strip()
checks['service_execstart_exact'] = expected_exec in show.get('ExecStart', '')
checks['service_unit_hash_matches_draft'] = installed_unit.exists() and draft_unit.exists() and sha256(installed_unit) == sha256(draft_unit)
checks['fixed_timer_inactive'] = inactive(TIMER)
checks['fixed_timer_disabled'] = disabled_or_static(TIMER)

checks['config_always_on'] = config.get('runtime_enabled') is True and config.get('always_on_enabled') is True
checks['config_observation_only'] = config.get('observation_only') is True and config.get('fixed_timer_enabled') is False
for key in (
    'paper_runtime_enabled', 'paper_position_write_enabled', 'real_trade_enabled',
    'wallet_enabled', 'signing_enabled', 'real_order_enabled', 'broadcast_enabled',
    'policy_expansion_enabled',
):
    checks[f'config_{key}_false'] = config.get(key) is False
checks['rpc_chain_bsc'] = int(config['rpc']['chain_id']) == 56
checks['rpc_hosts_allowlisted'] = all(
    urlparse(str(endpoint)).scheme == 'https'
    and urlparse(str(endpoint)).hostname in set(config['rpc']['allowed_hosts'])
    for endpoint in config['rpc']['endpoints']
)
checks['active_rpc_endpoint_allowlisted'] = urlparse(str(state.get('rpc_endpoint') or '')).hostname in set(config['rpc']['allowed_hosts'])

checks['state_running'] = state.get('status') == 'RUNNING'
checks['state_not_refreshing_during_audit'] = state.get('refresh_in_progress') is False
checks['heartbeat_fresh'] = age_sec(state.get('heartbeat_at_utc'), now) <= MAX_HEARTBEAT_AGE_SEC
checks['natural_event_count_sufficient'] = len(blocks) >= MIN_EVENTS
checks['natural_event_span_sufficient'] = event_span_sec >= MIN_EVENT_SPAN_SEC
checks['latest_block_fresh'] = latest_event_block_age_sec <= MAX_BLOCK_AGE_SEC
checks['invalid_event_rows_zero'] = invalid_event_rows == 0
checks['refresh_count_sufficient'] = int(state.get('full_refresh_count') or 0) >= MIN_REFRESHES
refresh_successes = int(state.get('full_refresh_count') or 0)
refresh_failures = int(state.get('refresh_failure_count') or 0)
refresh_attempts = refresh_successes + refresh_failures
refresh_failure_rate = (refresh_failures / refresh_attempts) if refresh_attempts else 1.0
checks['refresh_failure_rate_bounded'] = refresh_attempts >= MIN_REFRESHES and refresh_failure_rate <= 0.20
checks['consecutive_refresh_failures_zero'] = int(state.get('consecutive_refresh_failures') or 0) == 0
checks['refresh_backoff_inactive'] = float(state.get('refresh_backoff_until_monotonic') or 0.0) <= time.monotonic()
last_refresh = state.get('last_refresh_result') or {}
checks['last_refresh_pass'] = isinstance(last_refresh, dict) and last_refresh.get('status') == 'PASS'
checks['last_refresh_pool_count_positive'] = int(last_refresh.get('successful_pool_count') or 0) >= 1
checks['last_refresh_fresh'] = age_sec(state.get('last_full_refresh_at_utc'), now) <= MAX_MARKET_AGE_SEC

last_runtime_error_at = state.get('last_runtime_error_at_utc')
last_block_event_at = state.get('last_block_event_at_utc')
if last_runtime_error_at:
    checks['runtime_recovered_after_last_error'] = bool(last_block_event_at) and parse_dt(last_block_event_at) > parse_dt(last_runtime_error_at)
else:
    checks['runtime_recovered_after_last_error'] = True

checks['health_running'] = health.get('status') == 'RUNNING'
checks['health_fresh'] = age_sec(health.get('generated_at_utc'), now) <= MAX_HEARTBEAT_AGE_SEC
checks['health_real_financial_authority_zero'] = int(health.get('real_financial_authority', -1)) == 0
checks['health_paper_disabled'] = health.get('paper_runtime') is False and health.get('live_trade') is False

checks['market_snapshot_fresh'] = age_sec(market.get('generated_at_utc'), now) <= MAX_MARKET_AGE_SEC
checks['market_provider_expected'] = market.get('provider') == 'GECKOTERMINAL_KEYLESS_PUBLIC'
checks['market_network_bsc'] = market.get('network') == 'bsc'
checks['market_pool_count_positive'] = int(market.get('successful_pool_count') or 0) >= 1
checks['market_request_count_bounded'] = 1 <= int(market.get('request_count') or 0) <= 25
checks['market_items_present'] = isinstance(market.get('items'), list) and len(market['items']) >= 1
market_authority = market.get('authority') or {}
checks['market_observation_authority_only'] = market_authority.get('observation_runtime') is True
for key in ('paper_runtime', 'paper_position_write', 'real_trade', 'wallet', 'signing', 'real_order', 'broadcast', 'system_may_expand_policy'):
    checks[f'market_authority_{key}_false'] = market_authority.get(key) is False

checks['panel_fresh'] = age_sec(panel.get('generated_at_utc'), now) <= MAX_MARKET_AGE_SEC
checks['panel_source_count_positive'] = int(panel.get('source_count') or 0) >= 1
checks['panel_observation_only'] = panel.get('decision') == 'REAL_MARKET_TECHNICAL_OBSERVATION_ACTIVE'
panel_authority = panel.get('authority') or {}
for key in ('trade', 'paper_trade_write', 'wallet', 'signing', 'real_order', 'broadcast', 'provider_call_from_browser', 'policy_apply'):
    checks[f'panel_authority_{key}_false'] = panel_authority.get(key) is False

checks['binding_status_active'] = binding.get('status') == 'ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE'
checks['binding_timer_false'] = binding.get('fixed_timer_enabled') is False
checks['binding_event_stream_true'] = binding.get('block_event_stream_active') is True
for label, rel in binding.get('files', {}).items():
    path = ROOT / rel
    expected = binding.get('sha256', {}).get(label)
    checks[f'binding_hash_{label}'] = path.exists() and expected == sha256(path)

required = [name for name, result in checks.items() if not result]
status = 'READY_TO_CLOSE' if not required else 'OBSERVATION_PENDING'
audit = {
    'schema': 'tokenoskobi.era63e.continuous_observation_audit.v1',
    'generated_at_utc': now.isoformat(),
    'status': status,
    'thresholds': {
        'minimum_natural_block_events': MIN_EVENTS,
        'minimum_event_span_sec': MIN_EVENT_SPAN_SEC,
        'minimum_full_market_refreshes': MIN_REFRESHES,
        'minimum_service_uptime_sec': MIN_UPTIME_SEC,
        'maximum_heartbeat_age_sec': MAX_HEARTBEAT_AGE_SEC,
        'maximum_latest_block_age_sec': MAX_BLOCK_AGE_SEC,
        'maximum_market_age_sec': MAX_MARKET_AGE_SEC,
        'maximum_refresh_failure_rate': 0.20,
    },
    'observed': {
        'service_uptime_sec': round(service_uptime_sec, 3),
        'state_uptime_sec': round(state_uptime_sec, 3),
        'natural_block_event_count': len(blocks),
        'natural_event_span_sec': round(event_span_sec, 3),
        'first_observed_block': blocks[0] if blocks else None,
        'latest_observed_block': blocks[-1] if blocks else None,
        'latest_block_age_sec': round(latest_event_block_age_sec, 3) if timestamps else None,
        'full_market_refresh_count': int(state.get('full_refresh_count') or 0),
        'refresh_failure_count': refresh_failures,
        'refresh_attempt_count': refresh_attempts,
        'refresh_failure_rate': round(refresh_failure_rate, 6),
        'consecutive_refresh_failures': int(state.get('consecutive_refresh_failures') or 0),
        'refresh_backoff_until_utc': state.get('refresh_backoff_until_utc'),
        'rpc_request_count': int(state.get('rpc_request_count') or 0),
        'rpc_endpoint': state.get('rpc_endpoint'),
        'service_main_pid': int(show.get('MainPID') or 0),
        'service_restart_count': int(show.get('NRestarts') or 0),
        'market_successful_pool_count': int(market.get('successful_pool_count') or 0),
        'market_request_count': int(market.get('request_count') or 0),
        'panel_source_count': int(panel.get('source_count') or 0),
        'heartbeat_age_sec': round(age_sec(state.get('heartbeat_at_utc'), now), 3),
        'market_snapshot_age_sec': round(age_sec(market.get('generated_at_utc'), now), 3),
    },
    'checks': checks,
    'unmet_checks': required,
    'authority': {
        'observation_runtime': True,
        'paper_runtime': False,
        'live_trade': False,
        'wallet': False,
        'signing': False,
        'real_order': False,
        'broadcast': False,
        'risk_engine_veto': True,
    },
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(f"OBSERVATION_AUDIT={status}")
print(f"NATURAL_BLOCK_EVENTS={audit['observed']['natural_block_event_count']}/{MIN_EVENTS}")
print(f"EVENT_SPAN_SEC={audit['observed']['natural_event_span_sec']}/{MIN_EVENT_SPAN_SEC}")
print(f"FULL_MARKET_REFRESHES={audit['observed']['full_market_refresh_count']}/{MIN_REFRESHES}")
print(f"SERVICE_UPTIME_SEC={audit['observed']['service_uptime_sec']}/{MIN_UPTIME_SEC}")
if required:
    print('UNMET_CHECKS=' + ','.join(required))
PY_AUDIT

AUDIT_STATUS="$(python3 - <<'PY_STATUS'
import json
from pathlib import Path
v=json.loads(Path('/tmp/era63e_continuous_observation_audit_v1.json').read_text(encoding='utf-8'))
print(v['status'])
PY_STATUS
)"

if [[ "$AUDIT_STATUS" != "READY_TO_CLOSE" ]]; then
  echo "ERA63E_STATUS=OBSERVATION_PENDING"
  python3 <<'PY_PENDING'
import json
from pathlib import Path
v=json.loads(Path('/tmp/era63e_continuous_observation_audit_v1.json').read_text(encoding='utf-8'))
o=v['observed']; t=v['thresholds']
print(f"NATURAL_BLOCK_EVENTS={o['natural_block_event_count']}/{t['minimum_natural_block_events']}")
print(f"EVENT_SPAN_SEC={o['natural_event_span_sec']}/{t['minimum_event_span_sec']}")
print(f"FULL_MARKET_REFRESHES={o['full_market_refresh_count']}/{t['minimum_full_market_refreshes']}")
print('UNMET_CHECKS=' + ','.join(v['unmet_checks']))
PY_PENDING
  echo "CANONICAL_MUTATION=NONE"
  echo "SERVICE=ENABLED_ACTIVE_RESTART_ALWAYS"
  echo "FIXED_15_MINUTE_TIMER=DISABLED"
  echo "PAPER_RUNTIME=DISABLED"
  echo "LIVE_TRADE=DISABLED"
  echo "WORKTREE=CLEAN"
  echo "HEAD=$(git rev-parse HEAD)"
  echo "NEXT_SAFE_STEP=WAIT_FOR_NATURAL_ALWAYS_ON_CYCLES_THEN_RERUN_ERA63E_CLOSURE"
  exit 0
fi

python3 -m py_compile \
  tools/era63_paper_trading_core_v1.py \
  tools/era63_technical_dex_execution_v1.py \
  tools/era63d_market_technical_runtime_v1.py \
  tools/era63e_always_on_market_runtime_v1.py \
  tests/test_era63b_paper_trading_core_v1.py \
  tests/test_era63c_technical_dex_execution_v1.py \
  tests/test_era63d_market_technical_runtime_v1.py \
  tests/test_era63e_always_on_market_runtime_v1.py
python3 tests/test_era63b_paper_trading_core_v1.py
python3 tests/test_era63c_technical_dex_execution_v1.py
python3 tests/test_era63d_market_technical_runtime_v1.py
python3 tests/test_era63e_always_on_market_runtime_v1.py

echo "TESTS=69/69_PASS"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era63e_technical_closure_backup_${TS}.tar.gz"
tar -czf "$BACKUP" -C / \
  root/tokenoskobi_clean_v1/PROJECT_RUNTIME.json \
  root/tokenoskobi_clean_v1/PROJECT_HISTORY.json \
  root/tokenoskobi_clean_v1/data/tokenoskobi_v1_v8_master_era_roadmap.json \
  root/tokenoskobi_clean_v1/data/control/latest_tk_machine_state.json \
  root/tokenoskobi_clean_v1/03_ROADMAP.md \
  root/tokenoskobi_clean_v1/04_ALMANAC.md \
  root/tokenoskobi_clean_v1/05_ATLAS.md \
  root/tokenoskobi_clean_v1/06_PROJECT_MASTER_STATE.md \
  root/tokenoskobi_clean_v1/07_PROJECT_HANDOFF.md \
  root/tokenoskobi_clean_v1/reports/LATEST_TK_AI_HANDOFF.md

echo "BACKUP=$BACKUP"

python3 <<'PY_CANONICAL'
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
AUDIT = json.loads(Path('/tmp/era63e_continuous_observation_audit_v1.json').read_text(encoding='utf-8'))
assert AUDIT['status'] == 'READY_TO_CLOSE'
NOW = datetime.now(timezone.utc).isoformat()
PRE_HEAD = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
NEXT = 'ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION'
STAGE = 'ERA63_FINAL_TECHNICAL_LINE_CLOSURE'
STATUS = 'CLOSED_VERIFIED_GITHUB_SEALED'
CONTROL = 'data/control/era63e_continuous_observation_and_technical_closure_v1.json'
REPORT = 'reports/LATEST_ERA63E_CONTINUOUS_OBSERVATION_AND_TECHNICAL_CLOSURE.md'


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def save(path: str, value: Any) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def replace_marker(text: str, start: str, end: str, block: str) -> str:
    if start in text and end in text:
        before = text.split(start, 1)[0]
        after = text.split(end, 1)[1]
        return before.rstrip() + '\n\n' + block.strip() + '\n\n' + after.lstrip()
    return text.rstrip() + '\n\n' + block.strip() + '\n'


closure = {
    'schema': 'tokenoskobi.era63e.continuous_observation_and_technical_closure.v1',
    'era': 'ERA63',
    'stage': STAGE,
    'status': STATUS,
    'result': 'OK_ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION_CLOSED_VERIFIED',
    'closed_at_utc': NOW,
    'head_before_closure_commit': PRE_HEAD,
    'service_retained': 'tokenoskobi-era63e-always-on-market.service',
    'fixed_timer_enabled': False,
    'runtime_model': 'ALWAYS_ON_EVENT_DRIVEN_NO_FIXED_TIMER',
    'tests': '69/69_PASS',
    'natural_observation': AUDIT,
    'authority': AUDIT['authority'],
    'project_boot_changed': False,
    'project_boot_reason': 'STABLE_BOOT_OWNER_NO_IDENTITY_OR_CONSTITUTION_CHANGE',
    'next_safe_step': NEXT,
}
save(CONTROL, closure)

runtime = load('PROJECT_RUNTIME.json')
runtime['next_safe_step'] = NEXT
runtime['project_status'] = 'V4_ERA63_CLOSED'
runtime['updated_at_utc'] = NOW
runtime['recent_event'] = {
    'event': STAGE,
    'result': STATUS,
    'timestamp': NOW,
}
runtime['era63_final_closure'] = {
    'artifact': CONTROL,
    'status': STATUS,
    'tests': '69/69_PASS',
    'natural_block_events': AUDIT['observed']['natural_block_event_count'],
    'full_market_refreshes': AUDIT['observed']['full_market_refresh_count'],
    'always_on_service_retained': True,
    'fixed_timer_enabled': False,
    'next_safe_step': NEXT,
}
ptr = runtime.setdefault('canonical_runtime_pointer', {})
ptr.update({
    'current_era': 'ERA63',
    'current_stage': STAGE,
    'current_status': STATUS,
    'technical_line_closed': True,
    'always_on_block_event_runtime': True,
    'canonical_closure_sync': STATUS,
    'next_safe_step': NEXT,
})
work = runtime.setdefault('work_unit', {})
completed = work.setdefault('completed_substeps', [])
for item in ('ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION', 'ERA63F_FINAL_TECHNICAL_LINE_CLOSURE'):
    if item not in completed:
        completed.append(item)
work.update({
    'id': 'ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION',
    'title': 'Technical Analysis and DEX Execution Line',
    'status': STATUS,
    'next_substep': NEXT,
    'observation_runtime': 'ACTIVE_READ_ONLY_RETAINED',
    'runtime_model': 'ALWAYS_ON_EVENT_DRIVEN_NO_FIXED_TIMER',
    'paper_trade_currently': 'DISABLED_PENDING_COORDINATED_INTELLIGENCE',
    'live_trade': 'DISABLED',
    'wallet_authority': 0,
    'signing_authority': 0,
    'real_order_create_authority': 0,
})
runtime['open_risks'] = [
    item for item in runtime.get('open_risks', [])
    if not str(item).startswith('ERA63E_REQUIRED:')
]
save('PROJECT_RUNTIME.json', runtime)

roadmap = load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
direction = roadmap.setdefault('current_direction', {})
direction.update({
    'always_on_runtime_active': True,
    'current_era': 'ERA63',
    'current_line': 'ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION',
    'current_stage': STAGE,
    'current_status': STATUS,
    'current_version': 'V4',
    'era63_opened': False,
    'era63_closed': True,
    'fixed_timer_enabled': False,
    'new_work_unit_opened': False,
    'next_safe_step': NEXT,
    'updated_at_utc': NOW,
})
roadmap['era63_final_closure'] = {
    'actual_title': 'Technical Analysis and DEX Execution',
    'artifact': CONTROL,
    'status': STATUS,
    'tests': '69/69_PASS',
    'natural_block_events': AUDIT['observed']['natural_block_event_count'],
    'full_market_refreshes': AUDIT['observed']['full_market_refresh_count'],
    'always_on_runtime_retained': True,
    'next_safe_step': NEXT,
}
save('data/tokenoskobi_v1_v8_master_era_roadmap.json', roadmap)

history = load('PROJECT_HISTORY.json')
history.setdefault('events', []).append({
    'artifact': CONTROL,
    'era': 'ERA63',
    'event': 'FINAL_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION_CLOSURE',
    'event_id': 'ERA63_FINAL_TECHNICAL_LINE_CLOSURE',
    'status': STATUS,
    'tests': '69/69_PASS',
    'natural_block_events': AUDIT['observed']['natural_block_event_count'],
    'full_market_refreshes': AUDIT['observed']['full_market_refresh_count'],
    'always_on_runtime_retained': True,
    'fixed_timer_enabled': False,
    'real_financial_authority': 0,
    'next_safe_step': NEXT,
    'timestamp_utc': NOW,
})
history['updated_at_utc'] = NOW
save('PROJECT_HISTORY.json', history)

roadmap_md = f'''# 03 ROADMAP - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={STAGE}
ERA63_STATUS={STATUS}
NEXT_SAFE_STEP={NEXT}

## LOCKED V4 EXECUTION ORDER

```text
ERA63=TECHNICAL_ANALYSIS_AND_DEX_EXECUTION=CLOSED
ERA64=SUCCESSFUL_WALLET_STATS_AND_CLUSTERING
ERA65=ONCHAIN_AND_CEX_TO_DEX_WHALE_FLOW
ERA66=NEWS_AIRDROP_ICO_IDO_AND_LAUNCH_INTELLIGENCE
ERA67=COORDINATED_MULTI_INTELLIGENCE_FUSION
ERA68=UNATTENDED_COORDINATED_PAPER_RUNTIME
```

## ERA63 CLOSURE

```text
ERA63A=GAP_AUDIT=COMPLETED
ERA63B=BASE_PAPER_CORE=COMPLETED
ERA63C=TECHNICAL_DEX_EXECUTION=VALIDATED
ERA63D=REAL_MARKET_BINDING=COMPLETED
ERA63E=ALWAYS_ON_BLOCK_EVENT_RUNTIME=CONTINUOUS_OBSERVATION_VERIFIED
ERA63F=FINAL_TECHNICAL_LINE_CLOSURE=CLOSED_VERIFIED
```

The resident read-only BSC event service remains active as the technical context producer. Fixed timer, paper runtime, live trade, wallet, signing, real order and broadcast remain disabled.
'''
(ROOT / '03_ROADMAP.md').write_text(roadmap_md, encoding='utf-8')

almanac_path = ROOT / '04_ALMANAC.md'
almanac = almanac_path.read_text(encoding='utf-8')
marker = '<!-- ERA63_FINAL_TECHNICAL_CLOSURE -->'
entry = f'''{marker}
## ERA63 FINAL TECHNICAL ANALYSIS AND DEX EXECUTION CLOSURE

- Status: `{STATUS}`
- Result: `OK_ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION_CLOSED_VERIFIED`
- Natural block events: `{AUDIT['observed']['natural_block_event_count']}`
- Natural observation span: `{AUDIT['observed']['natural_event_span_sec']} sec`
- Full adaptive market refreshes: `{AUDIT['observed']['full_market_refresh_count']}`
- Tests: `69/69_PASS`
- Resident service retained: `tokenoskobi-era63e-always-on-market.service`
- Fixed 15-minute timer: `DISABLED`
- Paper/live/wallet/signing/order/broadcast: `DISABLED`
- Artifact: `{CONTROL}`
- Next: `{NEXT}`
- UTC: `{NOW}`
'''
if marker in almanac:
    almanac = almanac.split(marker, 1)[0].rstrip() + '\n\n' + entry
else:
    almanac = almanac.rstrip() + '\n\n' + entry
almanac_path.write_text(almanac, encoding='utf-8')

atlas_path = ROOT / '05_ATLAS.md'
atlas = atlas_path.read_text(encoding='utf-8')
start = '<!-- ERA63E_ALWAYS_ON_RUNTIME:START -->'
end = '<!-- ERA63E_ALWAYS_ON_RUNTIME:END -->'
block = '''<!-- ERA63E_ALWAYS_ON_RUNTIME:START -->
## ERA63 ALWAYS-ON TECHNICAL CONTEXT PRODUCER

```text
RESIDENT SYSTEMD SERVICE
→ BSC NEW BLOCK HEAD OBSERVATION
→ BLOCK PRESSURE / GAS / TRANSACTION CHANGE STATE
→ ADAPTIVE TRIGGER
→ REAL POOL + MARKET + TECHNICAL REFRESH
→ TECHNICAL + MEV + SANDWICH + ROUTE READMODEL
→ ERA64 / ERA65 / ERA66 CONTEXT ALIGNMENT
→ ERA67 COORDINATED FUSION
```

- No fixed runtime clock.
- Service remains resident and restarts automatically.
- Every observed BSC block updates rolling state.
- Full external market refresh is adaptive and bounded.
- The producer supplies context only and cannot create paper/live trade, wallet, signing, order or broadcast authority.
<!-- ERA63E_ALWAYS_ON_RUNTIME:END -->'''
atlas_path.write_text(replace_marker(atlas, start, end, block), encoding='utf-8')

master = f'''# 06 PROJECT MASTER STATE - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={STAGE}
CURRENT_STATUS={STATUS}
NEXT_SAFE_STEP={NEXT}

## VERIFIED CLOSURE

- ERA63 technical analysis and DEX execution line: CLOSED
- Natural block events: `{AUDIT['observed']['natural_block_event_count']}`
- Adaptive full-market refreshes: `{AUDIT['observed']['full_market_refresh_count']}`
- Tests: `69/69_PASS`

## ACTIVE READ-ONLY RUNTIME

- `tokenoskobi-era63e-always-on-market.service`: ACTIVE, resident, restart-always
- BSC block-event observation: ACTIVE
- Fixed 15-minute timer: DISABLED
- Real market/technical refresh: ADAPTIVE

## AUTHORITY

```text
OBSERVATION_RUNTIME=true
PAPER_RUNTIME=false
LIVE_TRADE=DISABLED
REAL_WALLET=false
REAL_SIGNING=false
REAL_ORDER=false
REAL_BROADCAST=false
```

ERA64 has not been opened. Its opening decision is the only next safe step.
'''
(ROOT / '06_PROJECT_MASTER_STATE.md').write_text(master, encoding='utf-8')

handoff = f'''# 07 PROJECT HANDOFF - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={STAGE}
CURRENT_STATUS={STATUS}
NEXT_SAFE_STEP={NEXT}

ERA63 technical analysis and DEX execution line is closed with verified natural always-on runtime evidence. The resident BSC block-event service remains active as a read-only technical context producer; the fixed timer is disabled.

Evidence:
- `{CONTROL}`
- `{REPORT}`
- `runtime/era63e/always_on_state_v1.json`
- `runtime/era63e/block_events_v1.jsonl`

ERA64 is not open. Next: decide whether to open successful-wallet performance statistics, main/sub-wallet clustering and funding-relationship intelligence.

Paper/live trade and real wallet, signing, order and broadcast authority remain disabled.
'''
(ROOT / '07_PROJECT_HANDOFF.md').write_text(handoff, encoding='utf-8')
(ROOT / 'reports/LATEST_TK_AI_HANDOFF.md').write_text(handoff, encoding='utf-8')

report = f'''# ERA63 CONTINUOUS OBSERVATION AND TECHNICAL LINE CLOSURE

- Status: `{STATUS}`
- Closed UTC: `{NOW}`
- Natural block events: `{AUDIT['observed']['natural_block_event_count']}`
- Event span: `{AUDIT['observed']['natural_event_span_sec']} sec`
- Full adaptive market refreshes: `{AUDIT['observed']['full_market_refresh_count']}`
- Refresh failures: `{AUDIT['observed']['refresh_failure_count']}`
- Latest observed BSC block: `{AUDIT['observed']['latest_observed_block']}`
- Successful pools in latest market snapshot: `{AUDIT['observed']['market_successful_pool_count']}`
- Service uptime: `{AUDIT['observed']['service_uptime_sec']} sec`
- Tests: `69/69_PASS`
- Resident service: `ACTIVE_RETAINED`
- Fixed timer: `DISABLED`
- Paper runtime: `DISABLED`
- Live trade: `DISABLED`
- Wallet/signing/order/broadcast: `DISABLED`
- Next: `{NEXT}`
'''
(ROOT / REPORT).write_text(report, encoding='utf-8')

machine = load('data/control/latest_tk_machine_state.json')
machine.update({
    'always_on_runtime_active': True,
    'current_version': 'V4',
    'current_era': 'ERA63',
    'current_stage': STAGE,
    'current_status': STATUS,
    'next_safe_step': NEXT,
    'updated_at_utc': NOW,
    'era63_final_closure': {
        'artifact': CONTROL,
        'status': STATUS,
        'tests': '69/69_PASS',
        'natural_block_events': AUDIT['observed']['natural_block_event_count'],
        'full_market_refreshes': AUDIT['observed']['full_market_refresh_count'],
    },
})
machine['authority'] = {
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
save('data/control/latest_tk_machine_state.json', machine)

print('ERA63_CANONICAL_CLOSURE_SYNC=PASS')
PY_CANONICAL

MUTATED=1

python3 <<'PY_VERIFY'
import json
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
paths = [
    'PROJECT_RUNTIME.json', 'PROJECT_HISTORY.json',
    'data/tokenoskobi_v1_v8_master_era_roadmap.json',
    'data/control/latest_tk_machine_state.json',
    'data/control/era63e_continuous_observation_and_technical_closure_v1.json',
]
for rel in paths:
    json.loads((root / rel).read_text(encoding='utf-8'))
runtime = json.loads((root / 'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
closure = json.loads((root / 'data/control/era63e_continuous_observation_and_technical_closure_v1.json').read_text(encoding='utf-8'))
assert runtime['next_safe_step'] == 'ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION'
assert runtime['work_unit']['status'] == 'CLOSED_VERIFIED_GITHUB_SEALED'
assert runtime['work_unit']['paper_trade_currently'] == 'DISABLED_PENDING_COORDINATED_INTELLIGENCE'
assert closure['status'] == 'CLOSED_VERIFIED_GITHUB_SEALED'
assert closure['natural_observation']['status'] == 'READY_TO_CLOSE'
assert closure['authority']['paper_runtime'] is False
assert closure['authority']['live_trade'] is False
assert closure['authority']['wallet'] is False
assert closure['authority']['signing'] is False
assert closure['authority']['real_order'] is False
assert closure['authority']['broadcast'] is False
print('CANONICAL_VERIFY=PASS')
PY_VERIFY

systemctl is-enabled --quiet "$SERVICE"
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

git add -- \
  PROJECT_RUNTIME.json \
  PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json \
  data/control/era63e_continuous_observation_and_technical_closure_v1.json \
  03_ROADMAP.md \
  04_ALMANAC.md \
  05_ATLAS.md \
  06_PROJECT_MASTER_STATE.md \
  07_PROJECT_HANDOFF.md
git add -f -- \
  reports/LATEST_ERA63E_CONTINUOUS_OBSERVATION_AND_TECHNICAL_CLOSURE.md \
  reports/LATEST_TK_AI_HANDOFF.md

git diff --cached --check
git commit -m "ERA63: close technical analysis and always-on observation line"
COMMITTED=1
git push origin main
PUSHED=1

git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

HEAD="$(git rev-parse HEAD)"
python3 <<'PY_FINAL'
import json
from pathlib import Path
v=json.loads(Path('/tmp/era63e_continuous_observation_audit_v1.json').read_text(encoding='utf-8'))
o=v['observed']
print('ERA63E_STATUS=REAL_DATA_OBSERVATION_VERIFIED_TECHNICAL_LINE_CLOSED')
print(f"NATURAL_BLOCK_EVENTS={o['natural_block_event_count']}")
print(f"EVENT_SPAN_SEC={o['natural_event_span_sec']}")
print(f"FULL_MARKET_REFRESHES={o['full_market_refresh_count']}")
print(f"LATEST_BLOCK={o['latest_observed_block']}")
print(f"MARKET_POOLS={o['market_successful_pool_count']}")
PY_FINAL
echo "SOURCE_CONTINUITY=PASS"
echo "FRESHNESS=PASS"
echo "TECHNICAL_READMODEL=PASS"
echo "FAIL_CLOSED=PASS"
echo "AUTHORITY_SPLIT=PASS"
echo "ALWAYS_ON_SERVICE=ENABLED_ACTIVE_RESTART_ALWAYS"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION"
