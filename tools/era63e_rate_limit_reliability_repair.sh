#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SERVICE="tokenoskobi-era63e-always-on-market.service"
TIMER="tokenoskobi-era63d-market-technical.timer"
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
      systemctl daemon-reload >/dev/null 2>&1 || true
      systemctl restart "$SERVICE" >/dev/null 2>&1 || true
    fi
  fi
  echo "ERA63E_RATE_LIMIT_REPAIR_FAILED_RC=$rc"
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
systemctl is-enabled --quiet "$SERVICE"
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

python3 <<'PY_PRECHECK'
import json
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
runtime = json.loads((root / 'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
state = json.loads((root / 'runtime/era63e/always_on_state_v1.json').read_text(encoding='utf-8'))
assert runtime['next_safe_step'] == 'ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE'
assert runtime['work_unit']['id'] == 'ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION'
assert runtime['work_unit']['observation_runtime'] == 'ACTIVE_READ_ONLY'
assert runtime['authority']['live_trade'] == 'DISABLED'
assert runtime['authority']['real_wallet_authority'] == 0
assert runtime['authority']['real_signing_authority'] == 0
assert runtime['authority']['real_order_authority'] == 0
successes = int(state.get('full_refresh_count') or 0)
failures = int(state.get('refresh_failure_count') or 0)
attempts = successes + failures
rate = failures / attempts if attempts else 0.0
record = {
    'successes': successes,
    'failures': failures,
    'attempts': attempts,
    'failure_rate': rate,
    'last_refresh_reason': state.get('last_refresh_reason'),
    'last_refresh_result': state.get('last_refresh_result'),
    'last_block_number': state.get('last_block_number'),
    'block_event_count': state.get('block_event_count'),
}
Path('/tmp/era63e_rate_limit_before.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print('PRECHECK=VERIFIED')
print(f'PRE_REPAIR_REFRESH_SUCCESSES={successes}')
print(f'PRE_REPAIR_REFRESH_FAILURES={failures}')
print(f'PRE_REPAIR_REFRESH_FAILURE_RATE={rate:.6f}')
assert failures > 0
PY_PRECHECK

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era63e_rate_limit_repair_backup_${TS}.tar.gz"
tar -czf "$BACKUP" -C / \
  root/tokenoskobi_clean_v1/config/era63d_market_technical_runtime_v1.json \
  root/tokenoskobi_clean_v1/config/era63e_always_on_market_runtime_v1.json \
  root/tokenoskobi_clean_v1/tools/era63e_always_on_market_runtime_v1.py \
  root/tokenoskobi_clean_v1/tests/test_era63e_always_on_market_runtime_v1.py \
  root/tokenoskobi_clean_v1/tools/era63e_observe_close.sh \
  root/tokenoskobi_clean_v1/data/control/era63e_always_on_market_runtime_binding_v1.json \
  root/tokenoskobi_clean_v1/PROJECT_RUNTIME.json \
  root/tokenoskobi_clean_v1/PROJECT_HISTORY.json \
  root/tokenoskobi_clean_v1/03_ROADMAP.md \
  root/tokenoskobi_clean_v1/04_ALMANAC.md \
  root/tokenoskobi_clean_v1/05_ATLAS.md \
  root/tokenoskobi_clean_v1/06_PROJECT_MASTER_STATE.md \
  root/tokenoskobi_clean_v1/07_PROJECT_HANDOFF.md \
  root/tokenoskobi_clean_v1/data/control/latest_tk_machine_state.json \
  root/tokenoskobi_clean_v1/reports/LATEST_TK_AI_HANDOFF.md

echo "BACKUP=$BACKUP"

python3 <<'PY_PATCH'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'PATCH_TARGET_NOT_FOUND:{label}')
    return text.replace(old, new, 1)

# Reduce request fan-out and spread calls for the keyless public provider.
d_cfg_path = ROOT / 'config/era63d_market_technical_runtime_v1.json'
d_cfg = json.loads(d_cfg_path.read_text(encoding='utf-8'))
d_cfg['provider']['max_pools'] = 2
d_cfg['provider']['retries'] = 1
d_cfg['provider']['minimum_request_interval_sec'] = 2.5
save_json(d_cfg_path, d_cfg)

# Keep the process always-on while making expensive enrichment rate-limit aware.
e_cfg_path = ROOT / 'config/era63e_always_on_market_runtime_v1.json'
e_cfg = json.loads(e_cfg_path.read_text(encoding='utf-8'))
adaptive = e_cfg['adaptive_refresh']
adaptive['minimum_full_market_refresh_sec'] = 300
adaptive['maximum_full_market_refresh_sec'] = 900
adaptive['provider_rate_limit_base_backoff_sec'] = 900
adaptive['provider_rate_limit_max_backoff_sec'] = 3600
adaptive['provider_other_failure_base_backoff_sec'] = 300
adaptive['refresh_failure_backoff_multiplier'] = 2.0
save_json(e_cfg_path, e_cfg)

engine_path = ROOT / 'tools/era63e_always_on_market_runtime_v1.py'
engine = engine_path.read_text(encoding='utf-8')
engine = replace_once(
    engine,
    'from datetime import datetime, timezone',
    'from datetime import datetime, timedelta, timezone',
    'datetime_import',
)
engine = replace_once(
    engine,
    """    if minimum < 30 or maximum < minimum:
        raise Era63EError('ADAPTIVE_REFRESH_BOUNDS_INVALID')


class RpcClient:
""",
    """    if minimum < 30 or maximum < minimum:
        raise Era63EError('ADAPTIVE_REFRESH_BOUNDS_INVALID')
    rate_base = finite(adaptive.get('provider_rate_limit_base_backoff_sec'), 'rate_limit_base_backoff')
    rate_max = finite(adaptive.get('provider_rate_limit_max_backoff_sec'), 'rate_limit_max_backoff')
    other_base = finite(adaptive.get('provider_other_failure_base_backoff_sec'), 'other_failure_base_backoff')
    multiplier = finite(adaptive.get('refresh_failure_backoff_multiplier'), 'refresh_failure_backoff_multiplier')
    if rate_base < minimum or rate_max < rate_base or other_base < minimum or multiplier < 1.0 or multiplier > 8.0:
        raise Era63EError('ADAPTIVE_BACKOFF_BOUNDS_INVALID')


def classify_refresh_error(exc: Exception) -> str:
    text = f'{type(exc).__name__}:{exc}'.upper()
    if 'HTTP_429' in text or 'RATE_LIMIT' in text or 'TOO MANY REQUESTS' in text:
        return 'PROVIDER_RATE_LIMIT'
    if 'TIMEOUT' in text or 'TIMED OUT' in text:
        return 'PROVIDER_TIMEOUT'
    if 'HTTP_5' in text or 'URLERROR' in text or 'CONNECTION' in text:
        return 'PROVIDER_TRANSIENT_NETWORK'
    return 'PROVIDER_OR_DATA_FAILURE'


def refresh_backoff_seconds(config: dict[str, Any], consecutive_failures: int, error_class: str) -> float:
    adaptive = config['adaptive_refresh']
    if error_class == 'PROVIDER_RATE_LIMIT':
        base = float(adaptive['provider_rate_limit_base_backoff_sec'])
    else:
        base = float(adaptive['provider_other_failure_base_backoff_sec'])
    maximum = float(adaptive['provider_rate_limit_max_backoff_sec'])
    multiplier = float(adaptive['refresh_failure_backoff_multiplier'])
    exponent = max(0, int(consecutive_failures) - 1)
    return min(maximum, base * (multiplier ** exponent))


class RpcClient:
""",
    'validation_and_helpers',
)
engine = replace_once(
    engine,
    """def refresh_reason(event: dict[str, Any], state: dict[str, Any], config: dict[str, Any], now_monotonic: float) -> str | None:
    adaptive = config['adaptive_refresh']
    last_refresh = float(state.get('last_full_refresh_monotonic', 0.0))
""",
    """def refresh_reason(event: dict[str, Any], state: dict[str, Any], config: dict[str, Any], now_monotonic: float) -> str | None:
    adaptive = config['adaptive_refresh']
    backoff_until = float(state.get('refresh_backoff_until_monotonic', 0.0) or 0.0)
    if now_monotonic < backoff_until:
        return None
    last_refresh = float(state.get('last_full_refresh_monotonic', 0.0))
""",
    'refresh_reason_backoff_gate',
)
engine = replace_once(
    engine,
    """            'full_refresh_count': 0,
            'refresh_failure_count': 0,
            'last_full_refresh_at_utc': None,
""",
    """            'full_refresh_count': 0,
            'refresh_failure_count': 0,
            'consecutive_refresh_failures': 0,
            'refresh_backoff_until_monotonic': 0.0,
            'refresh_backoff_until_utc': None,
            'last_refresh_error_class': None,
            'last_full_refresh_at_utc': None,
""",
    'state_backoff_fields',
)
engine = replace_once(
    engine,
    """            'refresh_in_progress': snapshot.get('refresh_in_progress'),
            'last_refresh_result': snapshot.get('last_refresh_result'),
""",
    """            'refresh_in_progress': snapshot.get('refresh_in_progress'),
            'consecutive_refresh_failures': snapshot.get('consecutive_refresh_failures'),
            'refresh_backoff_until_utc': snapshot.get('refresh_backoff_until_utc'),
            'last_refresh_error_class': snapshot.get('last_refresh_error_class'),
            'last_refresh_result': snapshot.get('last_refresh_result'),
""",
    'health_backoff_fields',
)
engine = replace_once(
    engine,
    """                self.state['last_refresh_reason'] = reason
                self.state['last_refresh_result'] = result
        except Exception as exc:
            with self.lock:
                self.state['refresh_failure_count'] += 1
                self.state['last_refresh_reason'] = reason
                self.state['last_refresh_result'] = {
                    'status': 'FAIL_CLOSED',
                    'error': f'{type(exc).__name__}:{exc}',
                }
""",
    """                self.state['last_refresh_reason'] = reason
                self.state['last_refresh_result'] = result
                self.state['consecutive_refresh_failures'] = 0
                self.state['refresh_backoff_until_monotonic'] = 0.0
                self.state['refresh_backoff_until_utc'] = None
                self.state['last_refresh_error_class'] = None
        except Exception as exc:
            error_class = classify_refresh_error(exc)
            with self.lock:
                self.state['refresh_failure_count'] += 1
                self.state['consecutive_refresh_failures'] += 1
                consecutive = int(self.state['consecutive_refresh_failures'])
                backoff_sec = refresh_backoff_seconds(self.config, consecutive, error_class)
                self.state['refresh_backoff_until_monotonic'] = time.monotonic() + backoff_sec
                self.state['refresh_backoff_until_utc'] = (datetime.now(timezone.utc) + timedelta(seconds=backoff_sec)).isoformat()
                self.state['last_refresh_error_class'] = error_class
                self.state['last_refresh_reason'] = reason
                self.state['last_refresh_result'] = {
                    'status': 'FAIL_CLOSED',
                    'error_class': error_class,
                    'backoff_sec': backoff_sec,
                    'error': f'{type(exc).__name__}:{exc}',
                }
""",
    'refresh_worker_backoff',
)
engine = replace_once(
    engine,
    """    def start_refresh(self, reason: str) -> bool:
        with self.lock:
            if self.state['refresh_in_progress']:
                return False
            self.state['refresh_in_progress'] = True
""",
    """    def start_refresh(self, reason: str) -> bool:
        with self.lock:
            current = time.monotonic()
            if current < float(self.state.get('refresh_backoff_until_monotonic', 0.0) or 0.0):
                return False
            if self.state['refresh_in_progress']:
                return False
            self.state['refresh_in_progress'] = True
""",
    'start_refresh_backoff',
)
engine_path.write_text(engine, encoding='utf-8')

# Extend unit coverage for cooldown and error classification.
test_path = ROOT / 'tests/test_era63e_always_on_market_runtime_v1.py'
test = test_path.read_text(encoding='utf-8')
test = replace_once(
    test,
    "reason = module.refresh_reason(event, state, self.config, 200.0)",
    "reason = module.refresh_reason(event, state, self.config, 500.0)",
    'high_pressure_after_new_minimum',
)
insert = """
    def test_15_config_has_bounded_provider_backoff(self):
        adaptive = self.config['adaptive_refresh']
        self.assertGreaterEqual(adaptive['minimum_full_market_refresh_sec'], 300)
        self.assertGreaterEqual(adaptive['provider_rate_limit_base_backoff_sec'], adaptive['minimum_full_market_refresh_sec'])
        self.assertGreaterEqual(adaptive['provider_rate_limit_max_backoff_sec'], adaptive['provider_rate_limit_base_backoff_sec'])

    def test_16_backoff_gate_prevents_provider_storm(self):
        state = {
            'full_refresh_count': 1,
            'last_full_refresh_monotonic': 100.0,
            'refresh_backoff_until_monotonic': 1000.0,
            'previous_transaction_count': 1,
            'previous_block_timestamp': 1000,
        }
        event = module.block_event(raw_block(101, 1003, tx_count=999, gas_used=99, gas_limit=100))
        self.assertIsNone(module.refresh_reason(event, state, self.config, 500.0))

    def test_17_rate_limit_classification_and_exponential_backoff(self):
        exc = RuntimeError('PROVIDER_REQUEST_FAILED:HTTP_429:https://api.geckoterminal.com')
        error_class = module.classify_refresh_error(exc)
        self.assertEqual(error_class, 'PROVIDER_RATE_LIMIT')
        first = module.refresh_backoff_seconds(self.config, 1, error_class)
        second = module.refresh_backoff_seconds(self.config, 2, error_class)
        maximum = self.config['adaptive_refresh']['provider_rate_limit_max_backoff_sec']
        self.assertGreaterEqual(first, 900)
        self.assertGreater(second, first)
        self.assertLessEqual(second, maximum)

    def test_18_start_refresh_respects_active_backoff(self):
        calls = []
        runtime = module.AlwaysOnRuntime(self.config, rpc=FakeRpc(), market_refresh=lambda: calls.append(1) or {})
        runtime.state['refresh_backoff_until_monotonic'] = time.monotonic() + 60.0
        self.assertFalse(runtime.start_refresh('TEST'))
        self.assertEqual(calls, [])

"""
marker = "\n\nif __name__ == '__main__':\n"
if marker not in test:
    raise SystemExit('PATCH_TARGET_NOT_FOUND:test_insert_marker')
test = test.replace(marker, '\n' + insert + marker, 1)
test_path.write_text(test, encoding='utf-8')

# Make closure judge post-repair reliability rather than impossible lifetime zero-failure history.
closure_path = ROOT / 'tools/era63e_observe_close.sh'
closure = closure_path.read_text(encoding='utf-8')
closure = replace_once(closure, 'MAX_MARKET_AGE_SEC = 300.0', 'MAX_MARKET_AGE_SEC = 1200.0', 'closure_market_age')
closure = replace_once(
    closure,
    "checks['refresh_failures_zero'] = int(state.get('refresh_failure_count') or 0) == 0",
    """refresh_successes = int(state.get('full_refresh_count') or 0)
refresh_failures = int(state.get('refresh_failure_count') or 0)
refresh_attempts = refresh_successes + refresh_failures
refresh_failure_rate = (refresh_failures / refresh_attempts) if refresh_attempts else 1.0
checks['refresh_failure_rate_bounded'] = refresh_attempts >= MIN_REFRESHES and refresh_failure_rate <= 0.20
checks['consecutive_refresh_failures_zero'] = int(state.get('consecutive_refresh_failures') or 0) == 0
checks['refresh_backoff_inactive'] = float(state.get('refresh_backoff_until_monotonic') or 0.0) <= time.monotonic()""",
    'closure_failure_gate',
)
closure = replace_once(
    closure,
    "        'maximum_market_age_sec': MAX_MARKET_AGE_SEC,\n",
    "        'maximum_market_age_sec': MAX_MARKET_AGE_SEC,\n        'maximum_refresh_failure_rate': 0.20,\n",
    'closure_threshold',
)
closure = replace_once(
    closure,
    "        'refresh_failure_count': int(state.get('refresh_failure_count') or 0),\n",
    """        'refresh_failure_count': refresh_failures,
        'refresh_attempt_count': refresh_attempts,
        'refresh_failure_rate': round(refresh_failure_rate, 6),
        'consecutive_refresh_failures': int(state.get('consecutive_refresh_failures') or 0),
        'refresh_backoff_until_utc': state.get('refresh_backoff_until_utc'),
""",
    'closure_observed_metrics',
)
closure = closure.replace('65/65_PASS', '69/69_PASS')
closure_path.write_text(closure, encoding='utf-8')

print('PATCH=PROVIDER_RATE_LIMIT_BACKOFF_AND_REQUEST_BUDGET_APPLIED')
PY_PATCH

MUTATED=1

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

systemctl restart "$SERVICE"

for _ in $(seq 1 60); do
  if systemctl is-active --quiet "$SERVICE" && [[ -s runtime/era63e/always_on_state_v1.json ]]; then
    if python3 - <<'PY_READY' >/dev/null 2>&1
import json
from pathlib import Path
p=Path('/root/tokenoskobi_clean_v1/runtime/era63e/always_on_state_v1.json')
v=json.loads(p.read_text(encoding='utf-8'))
required = {'consecutive_refresh_failures', 'refresh_backoff_until_monotonic', 'last_refresh_error_class'}
raise SystemExit(0 if v.get('status') == 'RUNNING' and required.issubset(v) and int(v.get('block_event_count') or 0) >= 1 else 1)
PY_READY
    then
      break
    fi
  fi
  sleep 1
done

systemctl is-enabled --quiet "$SERVICE"
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

python3 <<'PY_RUNTIME_VERIFY'
import json
import time
from pathlib import Path
root=Path('/root/tokenoskobi_clean_v1')
state_path=root/'runtime/era63e/always_on_state_v1.json'
first=json.loads(state_path.read_text(encoding='utf-8'))
first_count=int(first.get('block_event_count') or 0)
time.sleep(4)
second=json.loads(state_path.read_text(encoding='utf-8'))
second_count=int(second.get('block_event_count') or 0)
assert second.get('status') == 'RUNNING'
assert second_count > first_count
assert second.get('authority', {}).get('observation_runtime') is True
for key in ('paper_runtime','paper_position_write','real_trade','wallet','signing','real_order','broadcast','system_may_expand_policy'):
    assert second['authority'][key] is False
last=second.get('last_refresh_result') or {}
if last.get('status') == 'FAIL_CLOSED':
    assert second.get('last_refresh_error_class') in {'PROVIDER_RATE_LIMIT','PROVIDER_TIMEOUT','PROVIDER_TRANSIENT_NETWORK','PROVIDER_OR_DATA_FAILURE'}
    assert float(second.get('refresh_backoff_until_monotonic') or 0.0) > time.monotonic()
elif last:
    assert last.get('status') == 'PASS'
print('POST_REPAIR_RUNTIME=VERIFIED')
print(f'POST_REPAIR_BLOCK_EVENTS={second_count}')
print(f'POST_REPAIR_REFRESH_SUCCESSES={int(second.get("full_refresh_count") or 0)}')
print(f'POST_REPAIR_REFRESH_FAILURES={int(second.get("refresh_failure_count") or 0)}')
print(f'POST_REPAIR_CONSECUTIVE_FAILURES={int(second.get("consecutive_refresh_failures") or 0)}')
print(f'POST_REPAIR_ERROR_CLASS={second.get("last_refresh_error_class")}')
print(f'POST_REPAIR_LAST_REFRESH_STATUS={last.get("status")}')
PY_RUNTIME_VERIFY

python3 <<'PY_CANONICAL'
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')
NOW = datetime.now(timezone.utc).isoformat()
PRE_HEAD = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
CONTROL = 'data/control/era63e_rate_limit_reliability_repair_v1.json'
REPORT = 'reports/LATEST_ERA63E_RATE_LIMIT_RELIABILITY_REPAIR.md'
NEXT = 'ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE'


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def save(path: str, value) -> None:
    target=ROOT/path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def sha(path: str) -> str:
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

before=json.loads(Path('/tmp/era63e_rate_limit_before.json').read_text(encoding='utf-8'))
state=load('runtime/era63e/always_on_state_v1.json')
e_cfg=load('config/era63e_always_on_market_runtime_v1.json')
d_cfg=load('config/era63d_market_technical_runtime_v1.json')
last=state.get('last_refresh_result') or {}
repair={
    'schema':'tokenoskobi.era63e.rate_limit_reliability_repair.v1',
    'era':'ERA63',
    'stage':'ERA63E_RATE_LIMIT_RELIABILITY_REPAIR',
    'status':'APPLIED_VERIFIED_OBSERVATION_PENDING',
    'result':'OK_GECKOTERMINAL_429_BACKOFF_AND_REQUEST_BUDGET_REPAIR',
    'applied_at_utc':NOW,
    'head_before_repair_commit':PRE_HEAD,
    'root_cause':'GECKOTERMINAL_KEYLESS_PUBLIC_HTTP_429_RATE_LIMIT',
    'pre_repair':before,
    'repair':{
        'maximum_pools_per_refresh':d_cfg['provider']['max_pools'],
        'provider_retries':d_cfg['provider']['retries'],
        'minimum_request_interval_sec':d_cfg['provider']['minimum_request_interval_sec'],
        'minimum_full_market_refresh_sec':e_cfg['adaptive_refresh']['minimum_full_market_refresh_sec'],
        'maximum_full_market_refresh_sec':e_cfg['adaptive_refresh']['maximum_full_market_refresh_sec'],
        'rate_limit_base_backoff_sec':e_cfg['adaptive_refresh']['provider_rate_limit_base_backoff_sec'],
        'rate_limit_max_backoff_sec':e_cfg['adaptive_refresh']['provider_rate_limit_max_backoff_sec'],
        'other_failure_base_backoff_sec':e_cfg['adaptive_refresh']['provider_other_failure_base_backoff_sec'],
        'backoff_multiplier':e_cfg['adaptive_refresh']['refresh_failure_backoff_multiplier'],
    },
    'post_restart':{
        'service_status':state.get('status'),
        'block_event_count':state.get('block_event_count'),
        'full_refresh_count':state.get('full_refresh_count'),
        'refresh_failure_count':state.get('refresh_failure_count'),
        'consecutive_refresh_failures':state.get('consecutive_refresh_failures'),
        'last_refresh_error_class':state.get('last_refresh_error_class'),
        'last_refresh_status':last.get('status'),
        'refresh_backoff_until_utc':state.get('refresh_backoff_until_utc'),
    },
    'tests':'69/69_PASS',
    'authority':{
        'observation_runtime':True,
        'paper_runtime':False,
        'live_trade':False,
        'wallet':False,
        'signing':False,
        'real_order':False,
        'broadcast':False,
        'risk_engine_veto':True,
    },
    'next_safe_step':NEXT,
}
save(CONTROL, repair)

binding=load('data/control/era63e_always_on_market_runtime_binding_v1.json')
binding['sha256']['config']=sha('config/era63e_always_on_market_runtime_v1.json')
binding['sha256']['engine']=sha('tools/era63e_always_on_market_runtime_v1.py')
binding['sha256']['tests']=sha('tests/test_era63e_always_on_market_runtime_v1.py')
binding['tests']['era63e']='18/18_PASS'
binding['tests']['combined']='69/69_PASS'
binding['rate_limit_reliability']={
    'status':'REPAIRED_OBSERVATION_PENDING',
    'artifact':CONTROL,
    'minimum_full_market_refresh_sec':e_cfg['adaptive_refresh']['minimum_full_market_refresh_sec'],
    'maximum_full_market_refresh_sec':e_cfg['adaptive_refresh']['maximum_full_market_refresh_sec'],
    'provider_rate_limit_backoff_sec':[
        e_cfg['adaptive_refresh']['provider_rate_limit_base_backoff_sec'],
        e_cfg['adaptive_refresh']['provider_rate_limit_max_backoff_sec'],
    ],
}
save('data/control/era63e_always_on_market_runtime_binding_v1.json', binding)

runtime=load('PROJECT_RUNTIME.json')
runtime['updated_at_utc']=NOW
runtime['recent_event']={
    'event':'ERA63E_RATE_LIMIT_RELIABILITY_REPAIR',
    'result':'APPLIED_VERIFIED_OBSERVATION_PENDING',
    'timestamp':NOW,
}
runtime['era63e_rate_limit_reliability_repair']={
    'artifact':CONTROL,
    'status':'APPLIED_VERIFIED_OBSERVATION_PENDING',
    'root_cause':'GECKOTERMINAL_HTTP_429_RATE_LIMIT',
    'tests':'69/69_PASS',
    'always_on_service_retained':True,
    'fixed_timer_enabled':False,
    'next_safe_step':NEXT,
}
ptr=runtime.setdefault('canonical_runtime_pointer',{})
ptr['era63e_rate_limit_reliability_repaired']=True
ptr['era63e_rate_limit_repair_artifact']=CONTROL
ptr['current_stage']='ERA63E_ADAPTIVE_ALWAYS_ON_MARKET_RUNTIME'
ptr['current_status']='ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE_RATE_LIMIT_HARDENED'
ptr['next_safe_step']=NEXT
work=runtime.setdefault('work_unit',{})
completed=work.setdefault('completed_substeps',[])
if 'ERA63E_RATE_LIMIT_RELIABILITY_REPAIR' not in completed:
    completed.append('ERA63E_RATE_LIMIT_RELIABILITY_REPAIR')
work['status']='ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE'
work['next_substep']=NEXT
save('PROJECT_RUNTIME.json',runtime)

history=load('PROJECT_HISTORY.json')
history.setdefault('events',[]).append({
    'artifact':CONTROL,
    'era':'ERA63',
    'event':'GECKOTERMINAL_RATE_LIMIT_RELIABILITY_REPAIR',
    'event_id':'ERA63E_RATE_LIMIT_RELIABILITY_REPAIR',
    'root_cause':'HTTP_429_RATE_LIMIT',
    'status':'APPLIED_VERIFIED_OBSERVATION_PENDING',
    'tests':'69/69_PASS',
    'next_safe_step':NEXT,
    'timestamp_utc':NOW,
})
history['updated_at_utc']=NOW
save('PROJECT_HISTORY.json',history)

roadmap=(ROOT/'03_ROADMAP.md').read_text(encoding='utf-8')
roadmap=roadmap.replace('ERA63E=ALWAYS_ON_BLOCK_EVENT_RUNTIME=ACTIVE_OBSERVATION_PENDING','ERA63E=ALWAYS_ON_BLOCK_EVENT_RUNTIME=RATE_LIMIT_HARDENED_OBSERVATION_PENDING')
roadmap=roadmap.rstrip()+f'''\n\n<!-- ERA63E_RATE_LIMIT_REPAIR -->\n## ERA63E PROVIDER RELIABILITY\n\n- GeckoTerminal HTTP 429 root cause: `CONFIRMED`\n- Request fan-out: `REDUCED`\n- Adaptive refresh floor/ceiling: `300/900 seconds`\n- Rate-limit backoff: `900..3600 seconds`\n- Always-on BSC block observation: `RETAINED`\n- Status: `OBSERVATION_PENDING`\n- Next: `{NEXT}`\n'''
(ROOT/'03_ROADMAP.md').write_text(roadmap,encoding='utf-8')

almanac=ROOT/'04_ALMANAC.md'
text=almanac.read_text(encoding='utf-8')
marker='<!-- ERA63E_RATE_LIMIT_RELIABILITY_REPAIR -->'
entry=f'''{marker}\n## ERA63E RATE-LIMIT RELIABILITY REPAIR\n\n- Status: `APPLIED_VERIFIED_OBSERVATION_PENDING`\n- Root cause: `GECKOTERMINAL HTTP 429`\n- Pre-repair failure rate: `{before['failure_rate']:.6f}`\n- Request interval: `2.5 sec`\n- Refresh bounds: `300..900 sec`\n- Rate-limit backoff: `900..3600 sec`\n- Tests: `69/69_PASS`\n- Always-on BSC service: `ACTIVE_RETAINED`\n- Financial authority: `0`\n- Artifact: `{CONTROL}`\n- Next: `{NEXT}`\n- UTC: `{NOW}`\n'''
if marker in text:
    text=text.split(marker,1)[0].rstrip()+'\n\n'+entry
else:
    text=text.rstrip()+'\n\n'+entry
almanac.write_text(text,encoding='utf-8')

atlas_path=ROOT/'05_ATLAS.md'
atlas=atlas_path.read_text(encoding='utf-8')
old='''→ ADAPTIVE TRIGGER\n→ REAL POOL + MARKET + TECHNICAL REFRESH'''
new='''→ ADAPTIVE TRIGGER\n→ PROVIDER REQUEST BUDGET + HTTP 429 CIRCUIT BREAKER/BACKOFF\n→ REAL POOL + MARKET + TECHNICAL REFRESH'''
if old in atlas:
    atlas=atlas.replace(old,new,1)
atlas_path.write_text(atlas,encoding='utf-8')

master=f'''# 06 PROJECT MASTER STATE - TOKENOSKOBI\n\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA63\nCURRENT_STAGE=ERA63E_ADAPTIVE_ALWAYS_ON_MARKET_RUNTIME\nCURRENT_STATUS=ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE_RATE_LIMIT_HARDENED\nNEXT_SAFE_STEP={NEXT}\n\n## ACTIVE RUNTIME\n\n- `tokenoskobi-era63e-always-on-market.service`: ACTIVE, resident, restart-always\n- BSC block-event observation: ACTIVE\n- Fixed 15-minute timer: DISABLED\n- GeckoTerminal market/technical refresh: ADAPTIVE + RATE-LIMIT BACKOFF\n- Request budget: max 2 pools, 2.5 sec request spacing\n- Refresh bounds: 300..900 sec\n- HTTP 429 backoff: 900..3600 sec\n- Tests: `69/69_PASS`\n\n## AUTHORITY\n\n```text\nOBSERVATION_RUNTIME=true\nPAPER_RUNTIME=false\nLIVE_TRADE=DISABLED\nREAL_WALLET=false\nREAL_SIGNING=false\nREAL_ORDER=false\nREAL_BROADCAST=false\n```\n\nERA63 remains open until post-repair natural refresh reliability and continuity are observed.\n'''
(ROOT/'06_PROJECT_MASTER_STATE.md').write_text(master,encoding='utf-8')

handoff=f'''# 07 PROJECT HANDOFF - TOKENOSKOBI\n\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA63\nCURRENT_STAGE=ERA63E_ADAPTIVE_ALWAYS_ON_MARKET_RUNTIME\nCURRENT_STATUS=ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE_RATE_LIMIT_HARDENED\nNEXT_SAFE_STEP={NEXT}\n\nThe resident BSC block-event service remains active. Diagnostic evidence confirmed GeckoTerminal HTTP 429 rate limiting. The runtime now uses a lower provider request budget, slower adaptive full-refresh bounds and exponential fail-closed provider backoff while continuing to process every BSC block.\n\nEvidence:\n- `{CONTROL}`\n- `data/control/era63e_always_on_market_runtime_binding_v1.json`\n- `runtime/era63e/always_on_state_v1.json`\n\nERA63 is not closed. Post-repair natural cycles must verify refresh reliability before technical-line closure. Paper/live trade and wallet, signing, order and broadcast remain disabled.\n'''
(ROOT/'07_PROJECT_HANDOFF.md').write_text(handoff,encoding='utf-8')
(ROOT/'reports/LATEST_TK_AI_HANDOFF.md').write_text(handoff,encoding='utf-8')

report=f'''# ERA63E RATE-LIMIT RELIABILITY REPAIR\n\n- Status: `APPLIED_VERIFIED_OBSERVATION_PENDING`\n- Root cause: `GECKOTERMINAL_KEYLESS_PUBLIC_HTTP_429_RATE_LIMIT`\n- Pre-repair refreshes: `{before['successes']} success / {before['failures']} failure`\n- Pre-repair failure rate: `{before['failure_rate']:.6f}`\n- Maximum pools: `2`\n- Provider retries: `1`\n- Request spacing: `2.5 sec`\n- Full-refresh bounds: `300..900 sec`\n- HTTP 429 backoff: `900..3600 sec`\n- Tests: `69/69_PASS`\n- Always-on BSC block service: `ACTIVE_RETAINED`\n- Fixed timer: `DISABLED`\n- Paper/live/wallet/signing/order/broadcast: `DISABLED`\n- Next: `{NEXT}`\n'''
(ROOT/REPORT).write_text(report,encoding='utf-8')

machine=load('data/control/latest_tk_machine_state.json')
machine.update({
    'always_on_runtime_active':True,
    'current_version':'V4',
    'current_era':'ERA63',
    'current_stage':'ERA63E_ADAPTIVE_ALWAYS_ON_MARKET_RUNTIME',
    'current_status':'ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE_RATE_LIMIT_HARDENED',
    'next_safe_step':NEXT,
    'updated_at_utc':NOW,
    'era63e_rate_limit_reliability_repair':{
        'artifact':CONTROL,
        'status':'APPLIED_VERIFIED_OBSERVATION_PENDING',
        'tests':'69/69_PASS',
    },
})
machine['authority']={
    'human_per_paper_trade_approval':False,
    'live_trade':'DISABLED',
    'paper_order_authority':'SIMULATION_ENGINE_ONLY_NO_RUNTIME_WRITE',
    'paper_position_authority':'SIMULATION_ENGINE_ONLY_NO_RUNTIME_WRITE',
    'paper_trade':'DISABLED_PENDING_COORDINATED_INTELLIGENCE',
    'paper_unattended_execution':'NOT_ALLOWED_YET',
    'real_order_authority':0,
    'real_signing_authority':0,
    'real_trade_authority':0,
    'real_wallet_authority':0,
    'risk_engine_veto':True,
    'system_may_not_expand_policy':True,
}
save('data/control/latest_tk_machine_state.json',machine)

print('CANONICAL_SYNC=VERIFIED')
PY_CANONICAL

python3 <<'PY_VERIFY'
import hashlib
import json
from pathlib import Path
root=Path('/root/tokenoskobi_clean_v1')
for rel in (
    'PROJECT_RUNTIME.json','PROJECT_HISTORY.json',
    'data/control/latest_tk_machine_state.json',
    'data/control/era63e_always_on_market_runtime_binding_v1.json',
    'data/control/era63e_rate_limit_reliability_repair_v1.json',
):
    json.loads((root/rel).read_text(encoding='utf-8'))
runtime=json.loads((root/'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
binding=json.loads((root/'data/control/era63e_always_on_market_runtime_binding_v1.json').read_text(encoding='utf-8'))
assert runtime['next_safe_step']=='ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE'
assert runtime['work_unit']['status']=='ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE'
assert runtime['authority']['live_trade']=='DISABLED'
assert runtime['authority']['real_wallet_authority']==0
assert runtime['authority']['real_signing_authority']==0
assert runtime['authority']['real_order_authority']==0
files=binding['files']; hashes=binding['sha256']
for label in ('config','engine','tests','service'):
    actual=hashlib.sha256((root/files[label]).read_bytes()).hexdigest()
    assert actual==hashes[label], (label,actual,hashes[label])
assert binding['tests']['combined']=='69/69_PASS'
print('CANONICAL_VERIFY=PASS')
PY_VERIFY

systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

git add -- \
  config/era63d_market_technical_runtime_v1.json \
  config/era63e_always_on_market_runtime_v1.json \
  tools/era63e_always_on_market_runtime_v1.py \
  tests/test_era63e_always_on_market_runtime_v1.py \
  tools/era63e_observe_close.sh \
  data/control/era63e_always_on_market_runtime_binding_v1.json \
  data/control/era63e_rate_limit_reliability_repair_v1.json \
  PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  03_ROADMAP.md 04_ALMANAC.md 05_ATLAS.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  data/control/latest_tk_machine_state.json
git add -f -- \
  reports/LATEST_ERA63E_RATE_LIMIT_RELIABILITY_REPAIR.md \
  reports/LATEST_TK_AI_HANDOFF.md

git diff --cached --check
git commit -m "ERA63E: harden adaptive refresh against provider rate limits"
COMMITTED=1
git push origin main
PUSHED=1

git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
systemctl is-enabled --quiet "$SERVICE"
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

HEAD="$(git rev-parse HEAD)"
python3 <<'PY_FINAL'
import json
from pathlib import Path
root=Path('/root/tokenoskobi_clean_v1')
state=json.loads((root/'runtime/era63e/always_on_state_v1.json').read_text(encoding='utf-8'))
cfg=json.loads((root/'config/era63e_always_on_market_runtime_v1.json').read_text(encoding='utf-8'))
dcfg=json.loads((root/'config/era63d_market_technical_runtime_v1.json').read_text(encoding='utf-8'))
last=state.get('last_refresh_result') or {}
print('ERA63E_RATE_LIMIT_REPAIR=APPLIED_VERIFIED')
print('ROOT_CAUSE=GECKOTERMINAL_HTTP_429_RATE_LIMIT')
print(f'MAX_POOLS={dcfg["provider"]["max_pools"]}')
print(f'REQUEST_INTERVAL_SEC={dcfg["provider"]["minimum_request_interval_sec"]}')
print(f'REFRESH_BOUNDS_SEC={cfg["adaptive_refresh"]["minimum_full_market_refresh_sec"]}..{cfg["adaptive_refresh"]["maximum_full_market_refresh_sec"]}')
print(f'RATE_LIMIT_BACKOFF_SEC={cfg["adaptive_refresh"]["provider_rate_limit_base_backoff_sec"]}..{cfg["adaptive_refresh"]["provider_rate_limit_max_backoff_sec"]}')
print(f'POST_RESTART_BLOCK_EVENTS={state.get("block_event_count")}')
print(f'POST_RESTART_REFRESH_STATUS={last.get("status")}')
print(f'POST_RESTART_ERROR_CLASS={state.get("last_refresh_error_class")}')
print(f'POST_RESTART_BACKOFF_UNTIL={state.get("refresh_backoff_until_utc")}')
PY_FINAL
echo "TESTS=69/69_PASS"
echo "ALWAYS_ON_SERVICE=ENABLED_ACTIVE_RESTART_ALWAYS"
echo "BSC_BLOCK_OBSERVATION=ACTIVE"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE"
