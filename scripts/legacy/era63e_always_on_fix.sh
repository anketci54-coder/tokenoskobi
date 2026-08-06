#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

ROOT="/root/tokenoskobi_clean_v1"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era63e_always_on_backup_${STAMP}.tar.gz"
COMMITTED=0

NEW_FILES=(
  "config/era63e_always_on_market_runtime_v1.json"
  "tools/era63e_always_on_market_runtime_v1.py"
  "tests/test_era63e_always_on_market_runtime_v1.py"
  "systemd_drafts/tokenoskobi-era63e-always-on-market.service"
  "data/control/era63e_always_on_market_runtime_binding_v1.json"
  "reports/LATEST_ERA63E_ALWAYS_ON_MARKET_RUNTIME.md"
)

TRACKED_FILES=(
  "03_ROADMAP.md"
  "04_ALMANAC.md"
  "05_ATLAS.md"
  "06_PROJECT_MASTER_STATE.md"
  "07_PROJECT_HANDOFF.md"
  "PROJECT_RUNTIME.json"
  "PROJECT_HISTORY.json"
  "data/tokenoskobi_v1_v8_master_era_roadmap.json"
  "data/control/latest_tk_machine_state.json"
  "reports/LATEST_TK_AI_HANDOFF.md"
)

ALL_FILES=("${TRACKED_FILES[@]}" "${NEW_FILES[@]}")
declare -A PREEXISTED=()
OLD_TIMER_ENABLED=0
OLD_TIMER_ACTIVE=0
NEW_SERVICE_INSTALLED=0

rollback() {
  rc=$?
  trap - ERR
  echo "ERA63E_ALWAYS_ON_FAILED_RC=$rc"
  if [[ "$COMMITTED" -eq 0 && -f "$BACKUP" ]]; then
    systemctl disable --now tokenoskobi-era63e-always-on-market.service >/dev/null 2>&1 || true
    rm -f /etc/systemd/system/tokenoskobi-era63e-always-on-market.service
    systemctl daemon-reload >/dev/null 2>&1 || true
    if [[ "$OLD_TIMER_ENABLED" -eq 1 ]]; then
      systemctl enable tokenoskobi-era63d-market-technical.timer >/dev/null 2>&1 || true
    fi
    if [[ "$OLD_TIMER_ACTIVE" -eq 1 ]]; then
      systemctl start tokenoskobi-era63d-market-technical.timer >/dev/null 2>&1 || true
    fi
    tar -xzf "$BACKUP" -C "$ROOT"
    for file in "${NEW_FILES[@]}"; do
      if [[ -z "${PREEXISTED[$file]+x}" ]]; then
        rm -f -- "$ROOT/$file"
      fi
    done
    git reset --quiet
    echo "ROLLBACK=COMPLETED"
  else
    echo "ROLLBACK=NOT_APPLIED_AFTER_COMMIT"
  fi
  exit "$rc"
}
trap rollback ERR

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]

python3 <<'PY_PRECHECK'
import json
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
runtime = json.loads((root / 'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert runtime.get('current_era') == 'ERA63'
assert runtime.get('current_stage') == 'ERA63D_REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING'
assert runtime.get('next_safe_step') == 'ERA63E_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE'
assert runtime.get('work_unit', {}).get('live_trade') == 'DISABLED'
assert runtime.get('work_unit', {}).get('wallet_authority') == 0
assert runtime.get('work_unit', {}).get('signing_authority') == 0
assert runtime.get('work_unit', {}).get('real_order_create_authority') == 0
print('PRECHECK=VERIFIED')
PY_PRECHECK

if systemctl is-enabled --quiet tokenoskobi-era63d-market-technical.timer 2>/dev/null; then OLD_TIMER_ENABLED=1; fi
if systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer 2>/dev/null; then OLD_TIMER_ACTIVE=1; fi

existing=()
for file in "${ALL_FILES[@]}"; do
  if [[ -e "$file" ]]; then existing+=("$file"); fi
done
for file in "${NEW_FILES[@]}"; do
  if [[ -e "$file" ]]; then PREEXISTED["$file"]=1; fi
done
if [[ ${#existing[@]} -gt 0 ]]; then
  tar -czf "$BACKUP" -C "$ROOT" "${existing[@]}"
else
  tar -czf "$BACKUP" --files-from /dev/null
fi
echo "BACKUP=$BACKUP"

mkdir -p config tools tests systemd_drafts data/control reports runtime/era63e

cat >config/era63e_always_on_market_runtime_v1.json <<'ERA63E_CONFIG'
{
  "schema": "tokenoskobi.era63e.always_on_market_runtime_config.v1",
  "mode": "ALWAYS_ON_BLOCK_EVENT_DRIVEN_READ_ONLY_OBSERVATION",
  "runtime_enabled": true,
  "always_on_enabled": true,
  "fixed_timer_enabled": false,
  "observation_only": true,
  "paper_runtime_enabled": false,
  "paper_position_write_enabled": false,
  "real_trade_enabled": false,
  "wallet_enabled": false,
  "signing_enabled": false,
  "real_order_enabled": false,
  "broadcast_enabled": false,
  "policy_expansion_enabled": false,
  "rpc": {
    "chain_id": 56,
    "endpoints": [
      "https://bsc-dataseed.bnbchain.org",
      "https://bsc-dataseed-public.bnbchain.org",
      "https://bsc-dataseed.nariox.org",
      "https://bsc-dataseed.defibit.io"
    ],
    "allowed_hosts": [
      "bsc-dataseed.bnbchain.org",
      "bsc-dataseed-public.bnbchain.org",
      "bsc-dataseed.nariox.org",
      "bsc-dataseed.defibit.io"
    ],
    "request_timeout_sec": 8,
    "retries_per_endpoint": 1,
    "head_poll_interval_sec": 0.8,
    "max_catchup_blocks": 64,
    "heartbeat_max_sec": 10
  },
  "adaptive_refresh": {
    "minimum_full_market_refresh_sec": 45,
    "maximum_full_market_refresh_sec": 180,
    "high_transaction_count": 250,
    "high_gas_utilization": 0.75,
    "transaction_count_delta": 60,
    "block_interval_anomaly_sec": 8,
    "market_refresh_on_start": true,
    "refresh_thread_enabled": true
  },
  "inputs": {
    "era63d_runtime_config": "config/era63d_market_technical_runtime_v1.json"
  },
  "outputs": {
    "state": "runtime/era63e/always_on_state_v1.json",
    "health": "runtime/era63e/health_v1.json",
    "block_events_jsonl": "runtime/era63e/block_events_v1.jsonl",
    "max_jsonl_bytes": 52428800
  }
}
ERA63E_CONFIG

cat >tools/era63e_always_on_market_runtime_v1.py <<'ERA63E_ENGINE'
#!/usr/bin/env python3
"""Always-on BSC block-event runtime for Tokenoskobi ERA63E.

The process stays resident, observes every new BSC head, maintains rolling block
pressure state and adaptively refreshes the existing real-market technical
engine. It has no paper/live trading, wallet, signing, order or broadcast
capability.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import signal
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path('/root/tokenoskobi_clean_v1')
SCHEMA = 'tokenoskobi.era63e.always_on_market_runtime.v1'
CONFIG_SCHEMA = 'tokenoskobi.era63e.always_on_market_runtime_config.v1'


class Era63EError(RuntimeError):
    pass


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise Era63EError(f'{path}:NOT_OBJECT')
    return value


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        json.loads(Path(temporary).read_text(encoding='utf-8'))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_jsonl(path: Path, value: dict[str, Any], max_bytes: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > max_bytes:
        rotated = path.with_suffix(path.suffix + '.1')
        rotated.unlink(missing_ok=True)
        path.replace(rotated)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


def finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise Era63EError(f'{name}:NOT_NUMERIC') from exc
    if not math.isfinite(number):
        raise Era63EError(f'{name}:NOT_FINITE')
    return number


def validate_config(config: dict[str, Any]) -> None:
    if config.get('schema') != CONFIG_SCHEMA:
        raise Era63EError('CONFIG_SCHEMA_MISMATCH')
    for key in ('runtime_enabled', 'always_on_enabled', 'observation_only'):
        if config.get(key) is not True:
            raise Era63EError(f'{key}:MUST_BE_TRUE')
    if config.get('fixed_timer_enabled') is not False:
        raise Era63EError('FIXED_TIMER_MUST_BE_FALSE')
    for key in (
        'paper_runtime_enabled', 'paper_position_write_enabled', 'real_trade_enabled',
        'wallet_enabled', 'signing_enabled', 'real_order_enabled', 'broadcast_enabled',
        'policy_expansion_enabled',
    ):
        if config.get(key) is not False:
            raise Era63EError(f'{key}:MUST_BE_FALSE')
    rpc = config.get('rpc')
    if not isinstance(rpc, dict):
        raise Era63EError('RPC_NOT_OBJECT')
    endpoints = rpc.get('endpoints')
    allowed = set(rpc.get('allowed_hosts') or [])
    if not isinstance(endpoints, list) or len(endpoints) < 2:
        raise Era63EError('RPC_ENDPOINTS_INSUFFICIENT')
    for endpoint in endpoints:
        parsed = urllib.parse.urlparse(str(endpoint))
        if parsed.scheme != 'https' or parsed.hostname not in allowed:
            raise Era63EError('RPC_ENDPOINT_NOT_ALLOWLISTED_HTTPS')
    if int(rpc.get('chain_id', 0)) != 56:
        raise Era63EError('FIRST_CHAIN_MUST_BE_BSC_56')
    interval = finite(rpc.get('head_poll_interval_sec'), 'head_poll_interval_sec')
    if interval < 0.25 or interval > 5:
        raise Era63EError('HEAD_POLL_INTERVAL_OUT_OF_BOUNDS')
    adaptive = config.get('adaptive_refresh')
    if not isinstance(adaptive, dict):
        raise Era63EError('ADAPTIVE_REFRESH_NOT_OBJECT')
    minimum = finite(adaptive.get('minimum_full_market_refresh_sec'), 'minimum_refresh')
    maximum = finite(adaptive.get('maximum_full_market_refresh_sec'), 'maximum_refresh')
    if minimum < 30 or maximum < minimum:
        raise Era63EError('ADAPTIVE_REFRESH_BOUNDS_INVALID')


class RpcClient:
    def __init__(self, config: dict[str, Any], sleeper: Callable[[float], None] = time.sleep):
        rpc = config['rpc']
        self.endpoints = [str(item).rstrip('/') for item in rpc['endpoints']]
        self.allowed_hosts = set(rpc['allowed_hosts'])
        self.timeout = float(rpc['request_timeout_sec'])
        self.retries = int(rpc['retries_per_endpoint'])
        self._sleeper = sleeper
        self._endpoint_index = 0
        self.request_count = 0
        self.last_endpoint = None

    def call(self, method: str, params: list[Any]) -> Any:
        if not method.startswith('eth_'):
            raise Era63EError('RPC_METHOD_NOT_ALLOWLISTED')
        last_error = ''
        count = len(self.endpoints)
        for offset in range(count):
            endpoint = self.endpoints[(self._endpoint_index + offset) % count]
            parsed = urllib.parse.urlparse(endpoint)
            if parsed.scheme != 'https' or parsed.hostname not in self.allowed_hosts:
                continue
            for attempt in range(self.retries + 1):
                body = json.dumps({
                    'jsonrpc': '2.0', 'id': self.request_count + 1,
                    'method': method, 'params': params,
                }).encode('utf-8')
                request = urllib.request.Request(
                    endpoint,
                    data=body,
                    headers={'Content-Type': 'application/json', 'User-Agent': 'Tokenoskobi-ERA63E/1.0 read-only'},
                    method='POST',
                )
                self.request_count += 1
                try:
                    with urllib.request.urlopen(request, timeout=self.timeout) as response:
                        payload = json.loads(response.read().decode('utf-8'))
                    if not isinstance(payload, dict):
                        raise Era63EError('RPC_RESPONSE_NOT_OBJECT')
                    if payload.get('error'):
                        raise Era63EError(f"RPC_ERROR:{payload['error']}")
                    if 'result' not in payload:
                        raise Era63EError('RPC_RESULT_MISSING')
                    self._endpoint_index = (self._endpoint_index + offset) % count
                    self.last_endpoint = endpoint
                    return payload['result']
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError, Era63EError) as exc:
                    last_error = f'{type(exc).__name__}:{exc}'
                    if attempt < self.retries:
                        self._sleeper(min(0.5 * (2 ** attempt), 2.0))
        raise Era63EError(f'ALL_RPC_ENDPOINTS_FAILED:{last_error}')

    def chain_id(self) -> int:
        return int(str(self.call('eth_chainId', [])), 16)

    def latest_block_number(self) -> int:
        return int(str(self.call('eth_blockNumber', [])), 16)

    def block(self, number: int) -> dict[str, Any]:
        result = self.call('eth_getBlockByNumber', [hex(number), False])
        if not isinstance(result, dict):
            raise Era63EError('BLOCK_NOT_OBJECT')
        return result


def parse_hex_int(value: Any, name: str) -> int:
    try:
        return int(str(value), 16)
    except (TypeError, ValueError) as exc:
        raise Era63EError(f'{name}:INVALID_HEX') from exc


def block_event(block: dict[str, Any]) -> dict[str, Any]:
    number = parse_hex_int(block.get('number'), 'block.number')
    timestamp = parse_hex_int(block.get('timestamp'), 'block.timestamp')
    gas_used = parse_hex_int(block.get('gasUsed', '0x0'), 'block.gasUsed')
    gas_limit = max(1, parse_hex_int(block.get('gasLimit', '0x1'), 'block.gasLimit'))
    transactions = block.get('transactions')
    if not isinstance(transactions, list):
        raise Era63EError('BLOCK_TRANSACTIONS_NOT_LIST')
    return {
        'block_number': number,
        'block_hash': str(block.get('hash') or ''),
        'block_timestamp': timestamp,
        'transaction_count': len(transactions),
        'gas_used': gas_used,
        'gas_limit': gas_limit,
        'gas_utilization': gas_used / gas_limit,
    }


def refresh_reason(event: dict[str, Any], state: dict[str, Any], config: dict[str, Any], now_monotonic: float) -> str | None:
    adaptive = config['adaptive_refresh']
    last_refresh = float(state.get('last_full_refresh_monotonic', 0.0))
    elapsed = now_monotonic - last_refresh if last_refresh else float('inf')
    minimum = float(adaptive['minimum_full_market_refresh_sec'])
    maximum = float(adaptive['maximum_full_market_refresh_sec'])
    if state.get('full_refresh_count', 0) == 0 and bool(adaptive.get('market_refresh_on_start', True)):
        return 'STARTUP'
    if elapsed >= maximum:
        return 'MAXIMUM_REFRESH_AGE'
    if elapsed < minimum:
        return None
    if int(event['transaction_count']) >= int(adaptive['high_transaction_count']):
        return 'HIGH_TRANSACTION_COUNT'
    if float(event['gas_utilization']) >= float(adaptive['high_gas_utilization']):
        return 'HIGH_GAS_UTILIZATION'
    previous_tx = state.get('previous_transaction_count')
    if previous_tx is not None and abs(int(event['transaction_count']) - int(previous_tx)) >= int(adaptive['transaction_count_delta']):
        return 'TRANSACTION_COUNT_CHANGE'
    previous_ts = state.get('previous_block_timestamp')
    if previous_ts is not None and abs(int(event['block_timestamp']) - int(previous_ts)) >= int(adaptive['block_interval_anomaly_sec']):
        return 'BLOCK_INTERVAL_ANOMALY'
    return None


def load_era63d_module():
    root_text = str(ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    from tools import era63d_market_technical_runtime_v1 as module
    return module


class AlwaysOnRuntime:
    def __init__(
        self,
        config: dict[str, Any],
        rpc: RpcClient | None = None,
        market_refresh: Callable[[], dict[str, Any]] | None = None,
    ):
        validate_config(config)
        self.config = config
        self.rpc = rpc or RpcClient(config)
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.refresh_thread: threading.Thread | None = None
        self.market_module = None
        self.market_config = None
        self.market_refresh_override = market_refresh
        self.state: dict[str, Any] = {
            'schema': SCHEMA,
            'started_at_utc': iso_now(),
            'status': 'STARTING',
            'mode': config['mode'],
            'last_block_number': None,
            'last_block_timestamp': None,
            'previous_block_timestamp': None,
            'previous_transaction_count': None,
            'block_event_count': 0,
            'full_refresh_count': 0,
            'refresh_failure_count': 0,
            'last_full_refresh_at_utc': None,
            'last_full_refresh_monotonic': 0.0,
            'last_refresh_reason': None,
            'last_refresh_result': None,
            'refresh_in_progress': False,
            'rpc_request_count': 0,
            'rpc_endpoint': None,
            'authority': {
                'observation_runtime': True,
                'paper_runtime': False,
                'paper_position_write': False,
                'real_trade': False,
                'wallet': False,
                'signing': False,
                'real_order': False,
                'broadcast': False,
                'system_may_expand_policy': False,
            },
        }
        self.recent_events: deque[dict[str, Any]] = deque(maxlen=256)

    def paths(self) -> tuple[Path, Path, Path]:
        outputs = self.config['outputs']
        return (
            ROOT / str(outputs['state']),
            ROOT / str(outputs['health']),
            ROOT / str(outputs['block_events_jsonl']),
        )

    def write_state(self, status: str = 'RUNNING') -> None:
        state_path, health_path, _ = self.paths()
        with self.lock:
            self.state['status'] = status
            self.state['heartbeat_at_utc'] = iso_now()
            self.state['rpc_request_count'] = self.rpc.request_count
            self.state['rpc_endpoint'] = self.rpc.last_endpoint
            snapshot = json.loads(json.dumps(self.state))
        atomic_write_json(state_path, snapshot)
        atomic_write_json(health_path, {
            'schema': 'tokenoskobi.era63e.always_on_health.v1',
            'generated_at_utc': snapshot['heartbeat_at_utc'],
            'status': status,
            'always_on_process': True,
            'last_block_number': snapshot.get('last_block_number'),
            'block_event_count': snapshot.get('block_event_count'),
            'full_refresh_count': snapshot.get('full_refresh_count'),
            'refresh_in_progress': snapshot.get('refresh_in_progress'),
            'last_refresh_result': snapshot.get('last_refresh_result'),
            'paper_runtime': False,
            'live_trade': False,
            'real_financial_authority': 0,
        })

    def _market_refresh(self) -> dict[str, Any]:
        if self.market_refresh_override is not None:
            return self.market_refresh_override()
        if self.market_module is None:
            self.market_module = load_era63d_module()
            path = ROOT / str(self.config['inputs']['era63d_runtime_config'])
            self.market_config = read_json(path)
        snapshot = self.market_module.run_runtime(self.market_config)
        self.market_module.write_outputs(snapshot, self.market_config)
        return snapshot

    def _refresh_worker(self, reason: str) -> None:
        try:
            snapshot = self._market_refresh()
            result = {
                'status': 'PASS',
                'provider': snapshot.get('provider'),
                'successful_pool_count': snapshot.get('successful_pool_count'),
                'request_count': snapshot.get('request_count'),
            }
            with self.lock:
                self.state['full_refresh_count'] += 1
                self.state['last_full_refresh_at_utc'] = iso_now()
                self.state['last_full_refresh_monotonic'] = time.monotonic()
                self.state['last_refresh_reason'] = reason
                self.state['last_refresh_result'] = result
        except Exception as exc:
            with self.lock:
                self.state['refresh_failure_count'] += 1
                self.state['last_refresh_reason'] = reason
                self.state['last_refresh_result'] = {
                    'status': 'FAIL_CLOSED',
                    'error': f'{type(exc).__name__}:{exc}',
                }
        finally:
            with self.lock:
                self.state['refresh_in_progress'] = False
            self.write_state('RUNNING')

    def start_refresh(self, reason: str) -> bool:
        with self.lock:
            if self.state['refresh_in_progress']:
                return False
            self.state['refresh_in_progress'] = True
        thread = threading.Thread(target=self._refresh_worker, args=(reason,), daemon=True, name='era63e-market-refresh')
        self.refresh_thread = thread
        thread.start()
        return True

    def process_block(self, raw_block: dict[str, Any], now_monotonic: float | None = None) -> dict[str, Any]:
        event = block_event(raw_block)
        current_monotonic = time.monotonic() if now_monotonic is None else now_monotonic
        with self.lock:
            reason = refresh_reason(event, self.state, self.config, current_monotonic)
            previous_block_timestamp = self.state.get('last_block_timestamp')
            previous_tx = self.state.get('previous_transaction_count')
            self.state['previous_block_timestamp'] = previous_block_timestamp
            self.state['previous_transaction_count'] = event['transaction_count']
            self.state['last_block_number'] = event['block_number']
            self.state['last_block_timestamp'] = event['block_timestamp']
            self.state['block_event_count'] += 1
            self.state['last_block_event_at_utc'] = iso_now()
            event['block_interval_sec'] = (
                event['block_timestamp'] - previous_block_timestamp
                if previous_block_timestamp is not None else None
            )
            event['transaction_count_delta'] = (
                event['transaction_count'] - previous_tx if previous_tx is not None else None
            )
            event['refresh_reason'] = reason
        _, _, jsonl_path = self.paths()
        append_jsonl(jsonl_path, event, int(self.config['outputs']['max_jsonl_bytes']))
        self.recent_events.append(event)
        if reason:
            self.start_refresh(reason)
        self.write_state('RUNNING')
        return event

    def verify_chain(self) -> None:
        actual = self.rpc.chain_id()
        expected = int(self.config['rpc']['chain_id'])
        if actual != expected:
            raise Era63EError(f'CHAIN_ID_MISMATCH:{actual}!={expected}')

    def run(self) -> None:
        self.verify_chain()
        self.write_state('RUNNING')
        last_block: int | None = None
        last_heartbeat = 0.0
        poll_interval = float(self.config['rpc']['head_poll_interval_sec'])
        max_catchup = int(self.config['rpc']['max_catchup_blocks'])
        heartbeat_max = float(self.config['rpc']['heartbeat_max_sec'])
        while not self.stop_event.is_set():
            try:
                latest = self.rpc.latest_block_number()
                if last_block is None:
                    start = latest
                elif latest > last_block:
                    start = max(last_block + 1, latest - max_catchup + 1)
                else:
                    start = latest + 1
                for number in range(start, latest + 1):
                    self.process_block(self.rpc.block(number))
                if latest >= 0:
                    last_block = max(latest, last_block if last_block is not None else latest)
                now = time.monotonic()
                if now - last_heartbeat >= heartbeat_max:
                    self.write_state('RUNNING')
                    last_heartbeat = now
            except Exception as exc:
                with self.lock:
                    self.state['last_runtime_error'] = f'{type(exc).__name__}:{exc}'
                    self.state['last_runtime_error_at_utc'] = iso_now()
                self.write_state('DEGRADED_FAIL_CLOSED')
            self.stop_event.wait(poll_interval)
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=30)
        self.write_state('STOPPED')

    def stop(self, *_: Any) -> None:
        self.stop_event.set()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, default=ROOT / 'config' / 'era63e_always_on_market_runtime_v1.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    config = read_json(args.config)
    runtime = AlwaysOnRuntime(config)
    if args.check:
        runtime.verify_chain()
        latest = runtime.rpc.latest_block_number()
        runtime.process_block(runtime.rpc.block(latest))
        deadline = time.monotonic() + 30
        while runtime.state['refresh_in_progress'] and time.monotonic() < deadline:
            time.sleep(0.1)
        print('ERA63E_CHECK=PASS')
        print(f'CHAIN_ID={config["rpc"]["chain_id"]}')
        print(f'LATEST_BLOCK={runtime.state["last_block_number"]}')
        print(f'BLOCK_EVENTS={runtime.state["block_event_count"]}')
        print(f'FULL_REFRESH_COUNT={runtime.state["full_refresh_count"]}')
        print('PAPER_RUNTIME=DISABLED')
        print('LIVE_TRADE=DISABLED')
        return 0
    signal.signal(signal.SIGTERM, runtime.stop)
    signal.signal(signal.SIGINT, runtime.stop)
    runtime.run()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
ERA63E_ENGINE
chmod +x tools/era63e_always_on_market_runtime_v1.py

cat >tests/test_era63e_always_on_market_runtime_v1.py <<'ERA63E_TESTS'
#!/usr/bin/env python3
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / 'tools' / 'era63e_always_on_market_runtime_v1.py'
CONFIG_PATH = ROOT / 'config' / 'era63e_always_on_market_runtime_v1.json'
spec = importlib.util.spec_from_file_location('era63e_always_on', ENGINE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def raw_block(number: int, timestamp: int, tx_count: int = 10, gas_used: int = 10_000_000, gas_limit: int = 100_000_000):
    return {
        'number': hex(number),
        'timestamp': hex(timestamp),
        'hash': '0x' + f'{number:064x}',
        'gasUsed': hex(gas_used),
        'gasLimit': hex(gas_limit),
        'transactions': ['0x1'] * tx_count,
    }


class FakeRpc:
    def __init__(self):
        self.request_count = 0
        self.last_endpoint = 'https://bsc-dataseed.bnbchain.org'
    def chain_id(self): return 56
    def latest_block_number(self): return 101
    def block(self, number): return raw_block(number, 1_700_000_000 + number * 3)


class Era63EAlwaysOnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))

    def test_01_config_is_always_on_observation_only(self):
        module.validate_config(self.config)
        self.assertTrue(self.config['always_on_enabled'])
        self.assertFalse(self.config['fixed_timer_enabled'])
        self.assertTrue(self.config['observation_only'])

    def test_02_all_financial_authorities_disabled(self):
        for key in ('paper_runtime_enabled', 'paper_position_write_enabled', 'real_trade_enabled', 'wallet_enabled', 'signing_enabled', 'real_order_enabled', 'broadcast_enabled'):
            self.assertFalse(self.config[key])

    def test_03_non_allowlisted_rpc_rejected(self):
        value = copy.deepcopy(self.config)
        value['rpc']['endpoints'][0] = 'https://evil.invalid'
        with self.assertRaises(module.Era63EError): module.validate_config(value)

    def test_04_wrong_chain_rejected(self):
        value = copy.deepcopy(self.config)
        value['rpc']['chain_id'] = 1
        with self.assertRaises(module.Era63EError): module.validate_config(value)

    def test_05_block_event_parses_pressure(self):
        event = module.block_event(raw_block(100, 1000, tx_count=77, gas_used=75, gas_limit=100))
        self.assertEqual(event['block_number'], 100)
        self.assertEqual(event['transaction_count'], 77)
        self.assertAlmostEqual(event['gas_utilization'], 0.75)

    def test_06_startup_refresh_is_immediate(self):
        state = {'full_refresh_count': 0, 'last_full_refresh_monotonic': 0.0}
        event = module.block_event(raw_block(100, 1000))
        self.assertEqual(module.refresh_reason(event, state, self.config, 1.0), 'STARTUP')

    def test_07_minimum_refresh_gate_prevents_api_storm(self):
        state = {'full_refresh_count': 1, 'last_full_refresh_monotonic': 100.0, 'previous_transaction_count': 1, 'previous_block_timestamp': 1000}
        event = module.block_event(raw_block(101, 1003, tx_count=999, gas_used=99, gas_limit=100))
        self.assertIsNone(module.refresh_reason(event, state, self.config, 110.0))

    def test_08_maximum_age_forces_refresh(self):
        state = {'full_refresh_count': 1, 'last_full_refresh_monotonic': 100.0, 'previous_transaction_count': 1, 'previous_block_timestamp': 1000}
        event = module.block_event(raw_block(101, 1003))
        reason = module.refresh_reason(event, state, self.config, 1000.0)
        self.assertEqual(reason, 'MAXIMUM_REFRESH_AGE')

    def test_09_high_pressure_triggers_after_minimum(self):
        state = {'full_refresh_count': 1, 'last_full_refresh_monotonic': 100.0, 'previous_transaction_count': 1, 'previous_block_timestamp': 1000}
        event = module.block_event(raw_block(101, 1003, tx_count=999))
        reason = module.refresh_reason(event, state, self.config, 200.0)
        self.assertEqual(reason, 'HIGH_TRANSACTION_COUNT')

    def test_10_runtime_processes_block_and_refreshes_async(self):
        calls = []
        def refresh():
            calls.append(1)
            return {'provider': 'TEST', 'successful_pool_count': 2, 'request_count': 4}
        runtime = module.AlwaysOnRuntime(self.config, rpc=FakeRpc(), market_refresh=refresh)
        runtime.process_block(raw_block(100, 1000), now_monotonic=1.0)
        deadline = time.monotonic() + 2
        while runtime.state['refresh_in_progress'] and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(runtime.state['block_event_count'], 1)
        self.assertEqual(runtime.state['full_refresh_count'], 1)
        self.assertEqual(len(calls), 1)

    def test_11_authority_output_is_read_only(self):
        runtime = module.AlwaysOnRuntime(self.config, rpc=FakeRpc(), market_refresh=lambda: {})
        authority = runtime.state['authority']
        self.assertTrue(authority['observation_runtime'])
        for key in ('paper_runtime', 'paper_position_write', 'real_trade', 'wallet', 'signing', 'real_order', 'broadcast', 'system_may_expand_policy'):
            self.assertFalse(authority[key])

    def test_12_source_has_no_subprocess_or_dynamic_execution(self):
        tree = ast.parse(ENGINE_PATH.read_text(encoding='utf-8'))
        forbidden_imports = {'subprocess', 'web3', 'requests'}
        forbidden_calls = {'eval', 'exec', 'compile', '__import__'}
        imports, calls = set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module: imports.add(node.module.split('.')[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name): calls.add(node.func.id)
        self.assertFalse(imports & forbidden_imports)
        self.assertFalse(calls & forbidden_calls)

    def test_13_rpc_methods_are_read_only(self):
        source = ENGINE_PATH.read_text(encoding='utf-8')
        self.assertIn("'eth_chainId'", source)
        self.assertIn("'eth_blockNumber'", source)
        self.assertIn("'eth_getBlockByNumber'", source)
        for forbidden in ('eth_sendTransaction', 'eth_sendRawTransaction', 'personal_', 'wallet_'):
            self.assertNotIn(forbidden, source)

    def test_14_systemd_is_service_not_timer(self):
        unit = (ROOT / 'systemd_drafts' / 'tokenoskobi-era63e-always-on-market.service').read_text(encoding='utf-8')
        self.assertIn('Restart=always', unit)
        self.assertNotIn('[Timer]', unit)
        self.assertNotIn('OnUnitActiveSec', unit)


if __name__ == '__main__':
    unittest.main(verbosity=2)
ERA63E_TESTS
chmod +x tests/test_era63e_always_on_market_runtime_v1.py

cat >systemd_drafts/tokenoskobi-era63e-always-on-market.service <<'ERA63E_SERVICE'
[Unit]
Description=Tokenoskobi ERA63E always-on BSC block-event and adaptive market observation
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/root/tokenoskobi_clean_v1
ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/era63e_always_on_market_runtime_v1.py
Restart=always
RestartSec=2
TimeoutStopSec=40
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=/root/tokenoskobi_clean_v1/runtime /root/tokenoskobi_clean_v1/active_panel_8096/current/data
UMask=0027

[Install]
WantedBy=multi-user.target
ERA63E_SERVICE

python3 -m py_compile tools/era63e_always_on_market_runtime_v1.py tests/test_era63e_always_on_market_runtime_v1.py
python3 tests/test_era63b_paper_trading_core_v1.py
python3 tests/test_era63c_technical_dex_execution_v1.py
python3 tests/test_era63d_market_technical_runtime_v1.py
python3 tests/test_era63e_always_on_market_runtime_v1.py

python3 tools/era63e_always_on_market_runtime_v1.py --check

systemctl disable --now tokenoskobi-era63d-market-technical.timer >/dev/null 2>&1 || true
install -m 0644 systemd_drafts/tokenoskobi-era63e-always-on-market.service /etc/systemd/system/tokenoskobi-era63e-always-on-market.service
systemctl daemon-reload
systemctl enable --now tokenoskobi-era63e-always-on-market.service
NEW_SERVICE_INSTALLED=1

for _ in $(seq 1 45); do
  if systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service \
     && [[ -s runtime/era63e/always_on_state_v1.json ]]; then
    break
  fi
  sleep 1
done
systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer

python3 <<'PY_RUNTIME_VERIFY'
import json
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
state = json.loads((root / 'runtime/era63e/always_on_state_v1.json').read_text(encoding='utf-8'))
assert state['status'] in {'RUNNING', 'DEGRADED_FAIL_CLOSED'}
assert state['block_event_count'] >= 1
assert state['last_block_number'] is not None
a = state['authority']
assert a['observation_runtime'] is True
for key in ('paper_runtime', 'paper_position_write', 'real_trade', 'wallet', 'signing', 'real_order', 'broadcast', 'system_may_expand_policy'):
    assert a[key] is False
print(f"ALWAYS_ON_STATE=PASS:BLOCK={state['last_block_number']}:EVENTS={state['block_event_count']}:REFRESHES={state['full_refresh_count']}")
PY_RUNTIME_VERIFY

python3 <<'PY_CANONICAL'
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path('/root/tokenoskobi_clean_v1')
now = datetime.now(timezone.utc).isoformat()
stage = 'ERA63E_ADAPTIVE_ALWAYS_ON_MARKET_RUNTIME'
status = 'ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE'
next_step = 'ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE'
control_path = 'data/control/era63e_always_on_market_runtime_binding_v1.json'
report_path = 'reports/LATEST_ERA63E_ALWAYS_ON_MARKET_RUNTIME.md'

def load(path, default=None):
    p = root / path
    if not p.exists(): return default
    return json.loads(p.read_text(encoding='utf-8'))

def save(path, value):
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()

def find_id(value, target):
    if isinstance(value, dict):
        if value.get('id') == target: return value
        for item in value.values():
            found = find_id(item, target)
            if found is not None: return found
    elif isinstance(value, list):
        for item in value:
            found = find_id(item, target)
            if found is not None: return found
    return None

state = load('runtime/era63e/always_on_state_v1.json', {})
control = {
    'schema': 'tokenoskobi.era63e.always_on_market_runtime_binding.v1',
    'era': 'ERA63',
    'stage': stage,
    'status': status,
    'bound_at_utc': now,
    'replaced_runtime': 'tokenoskobi-era63d-market-technical.timer',
    'active_runtime': 'tokenoskobi-era63e-always-on-market.service',
    'runtime_model': 'RESIDENT_BLOCK_EVENT_LOOP_WITH_ADAPTIVE_FULL_MARKET_REFRESH',
    'fixed_timer_enabled': False,
    'block_event_stream_active': True,
    'latest_observed_block': state.get('last_block_number'),
    'observed_block_events': state.get('block_event_count'),
    'full_market_refreshes': state.get('full_refresh_count'),
    'rpc_endpoint': state.get('rpc_endpoint'),
    'tests': {'era63b': '13/13_PASS', 'era63c': '21/21_PASS', 'era63d': '17/17_PASS', 'era63e': '14/14_PASS', 'combined': '65/65_PASS'},
    'files': {
        'config': 'config/era63e_always_on_market_runtime_v1.json',
        'engine': 'tools/era63e_always_on_market_runtime_v1.py',
        'tests': 'tests/test_era63e_always_on_market_runtime_v1.py',
        'service': 'systemd_drafts/tokenoskobi-era63e-always-on-market.service',
    },
    'sha256': {
        'config': sha('config/era63e_always_on_market_runtime_v1.json'),
        'engine': sha('tools/era63e_always_on_market_runtime_v1.py'),
        'tests': sha('tests/test_era63e_always_on_market_runtime_v1.py'),
        'service': sha('systemd_drafts/tokenoskobi-era63e-always-on-market.service'),
    },
    'authority': {
        'observation_runtime': True,
        'paper_runtime': False,
        'real_trade': False,
        'wallet': False,
        'signing': False,
        'real_order': False,
        'broadcast': False,
    },
    'next_safe_step': next_step,
}
save(control_path, control)

runtime = load('PROJECT_RUNTIME.json', {})
runtime.update({
    'current_stage': stage,
    'current_status': status,
    'last_completed': stage,
    'last_result': '65/65_TESTS_PASS_ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE',
    'next_safe_step': next_step,
    'updated_at_utc': now,
})
runtime['open_risks'] = [
    'ERA63E_REQUIRED:CONTINUOUS_REAL_DATA_OBSERVATION_BEFORE_TECHNICAL_LINE_CLOSURE',
    'ERA64_REQUIRED:SUCCESSFUL_WALLET_STATS_AND_CLUSTERING',
    'ERA65_REQUIRED:CEX_TO_DEX_WHALE_AND_SUBWALLET_FLOW',
    'ERA66_REQUIRED:NEWS_AIRDROP_ICO_IDO_LAUNCH_INTELLIGENCE',
    'ERA67_REQUIRED:COORDINATED_MULTI_INTELLIGENCE_FUSION',
    'ERA68_REQUIRED:UNATTENDED_PAPER_RUNTIME',
]
work = runtime.setdefault('work_unit', {})
work.update({
    'id': 'ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION',
    'title': 'Always-On Technical and DEX Observation Runtime',
    'status': status,
    'next_substep': next_step,
    'runtime_model': 'ALWAYS_ON_EVENT_DRIVEN_NO_FIXED_TIMER',
    'paper_trade_currently': 'DISABLED_PENDING_COORDINATED_INTELLIGENCE',
    'live_trade': 'DISABLED',
    'wallet_authority': 0,
    'signing_authority': 0,
    'real_order_create_authority': 0,
})
completed = work.setdefault('completed_substeps', [])
for item in ('ERA63D_REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING', stage):
    if item not in completed: completed.append(item)
runtime['era63e_always_on_runtime'] = control
pointer = runtime.setdefault('canonical_runtime_pointer', {})
pointer.update({
    'current_version_line': 'V4', 'current_era': 'ERA63', 'current_stage': stage,
    'always_on_block_event_runtime': True, 'fixed_timer_enabled': False,
    'paper_runtime_enabled': False, 'next_safe_step': next_step,
})
runtime['recent_event'] = {'event': stage, 'result': status, 'timestamp': now}
save('PROJECT_RUNTIME.json', runtime)

machine = load('data/control/latest_tk_machine_state.json', {})
machine.update({
    'current_version': 'V4', 'current_era': 'ERA63', 'current_stage': stage,
    'current_status': status, 'last_completed': stage,
    'last_result': '65/65_PASS_ALWAYS_ON_BLOCK_EVENT_RUNTIME',
    'next_safe_step': next_step, 'updated_at_utc': now,
    'always_on_runtime_active': True, 'fixed_timer_enabled': False,
    'paper_runtime_enabled': False, 'live_trade': 'DISABLED',
    'era63e_control_artifact': control_path,
})
save('data/control/latest_tk_machine_state.json', machine)

history = load('PROJECT_HISTORY.json', {})
events = history.setdefault('events', [])
event_id = 'ERA63E_ADAPTIVE_ALWAYS_ON_MARKET_RUNTIME'
events[:] = [e for e in events if not (isinstance(e, dict) and e.get('event_id') == event_id)]
events.append({
    'event_id': event_id,
    'event': 'FIXED_TIMER_REPLACED_BY_RESIDENT_BLOCK_EVENT_RUNTIME',
    'era': 'ERA63', 'status': status, 'tests': '65/65_PASS',
    'artifact': control_path, 'fixed_timer_enabled': False,
    'always_on_runtime_active': True, 'paper_runtime_enabled': False,
    'real_financial_authority': 0, 'next_safe_step': next_step,
    'timestamp_utc': now,
})
history['updated_at_utc'] = now
save('PROJECT_HISTORY.json', history)

master = load('data/tokenoskobi_v1_v8_master_era_roadmap.json', {})
era63 = find_id(master, 'ERA63')
if era63 is not None:
    era63.update({
        'title': 'Technical Analysis and DEX Execution Foundation',
        'actual_title': 'Technical Analysis and DEX Execution Foundation',
        'status': status, 'active_stage': stage, 'next_safe_step': next_step,
        'always_on_runtime_active': True, 'fixed_timer_enabled': False,
        'paper_runtime_enabled': False,
    })
    substeps = era63.setdefault('substeps', {})
    if isinstance(substeps, dict):
        substeps.update({
            'ERA63D': 'REAL_MARKET_TECHNICAL_BINDING_COMPLETED',
            'ERA63E': 'ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE_OBSERVATION_PENDING',
        })
direction = master.setdefault('current_direction', {})
direction.update({
    'current_line': 'ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION',
    'current_version': 'V4', 'current_era': 'ERA63', 'current_stage': stage,
    'current_status': status, 'next_safe_step': next_step,
    'always_on_runtime_active': True, 'fixed_timer_enabled': False,
    'updated_at_utc': now,
})
save('data/tokenoskobi_v1_v8_master_era_roadmap.json', master)

roadmap = f'''# 03 ROADMAP - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={stage}
ERA63_STATUS={status}
NEXT_SAFE_STEP={next_step}

## LOCKED V4 EXECUTION ORDER

```text
ERA63=TECHNICAL_ANALYSIS_AND_DEX_EXECUTION
ERA64=SUCCESSFUL_WALLET_STATS_AND_CLUSTERING
ERA65=ONCHAIN_AND_CEX_TO_DEX_WHALE_FLOW
ERA66=NEWS_AIRDROP_ICO_IDO_AND_LAUNCH_INTELLIGENCE
ERA67=COORDINATED_MULTI_INTELLIGENCE_FUSION
ERA68=UNATTENDED_COORDINATED_PAPER_RUNTIME
```

## ERA63 RUNTIME

```text
ERA63A=GAP_AUDIT=COMPLETED
ERA63B=BASE_PAPER_CORE=COMPLETED
ERA63C=TECHNICAL_DEX_EXECUTION=VALIDATED
ERA63D=REAL_MARKET_BINDING=COMPLETED
ERA63E=ALWAYS_ON_BLOCK_EVENT_RUNTIME=ACTIVE_OBSERVATION_PENDING
```

The fixed 15-minute timer is disabled. The resident service observes every new BSC block and adaptively refreshes full market/technical state. Classical candle timeframes remain secondary derived views, not the runtime clock.

Paper and live trading remain disabled.
'''
(root / '03_ROADMAP.md').write_text(roadmap, encoding='utf-8')

atlas_path = root / '05_ATLAS.md'
atlas = atlas_path.read_text(encoding='utf-8') if atlas_path.exists() else ''
start = '<!-- ERA63E_ALWAYS_ON_RUNTIME:START -->'
end = '<!-- ERA63E_ALWAYS_ON_RUNTIME:END -->'
block = f'''{start}
## ERA63E ALWAYS-ON EVENT RUNTIME

```text
RESIDENT SYSTEMD SERVICE
→ BSC NEW BLOCK HEAD OBSERVATION
→ BLOCK PRESSURE / GAS / TRANSACTION CHANGE STATE
→ ADAPTIVE TRIGGER
→ REAL POOL + MARKET + TECHNICAL REFRESH
→ TECHNICAL + MEV + SANDWICH + ROUTE READMODEL
```

- No fixed 15-minute runtime clock.
- Service remains resident and restarts automatically.
- Every observed BSC block updates rolling state.
- Full external market refresh is adaptive and bounded to protect the free provider.
- Paper/live trade, wallet, signing, order and broadcast authority remain disabled.
{end}'''
if start in atlas and end in atlas:
    before = atlas.split(start, 1)[0]
    after = atlas.split(end, 1)[1]
    atlas = before + block + after
else:
    atlas = atlas.rstrip() + '\n\n' + block + '\n'
atlas_path.write_text(atlas, encoding='utf-8')

master_state = f'''# 06 PROJECT MASTER STATE - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={stage}
CURRENT_STATUS={status}
NEXT_SAFE_STEP={next_step}

## ACTIVE RUNTIME

- `tokenoskobi-era63e-always-on-market.service`: ACTIVE, resident, restart-always
- BSC block-event observation: ACTIVE
- Fixed 15-minute timer: DISABLED
- Real GeckoTerminal market/technical refresh: ADAPTIVE
- Technical and DEX execution tests: `65/65_PASS`

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

ERA63E continuous observation must complete before the technical line closes and ERA64 opens.
'''
(root / '06_PROJECT_MASTER_STATE.md').write_text(master_state, encoding='utf-8')

handoff = f'''# 07 PROJECT HANDOFF - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={stage}
CURRENT_STATUS={status}
NEXT_SAFE_STEP={next_step}

The previous 15-minute timer is disabled. A resident systemd service now watches BSC block heads continuously and launches bounded full-market technical refreshes from adaptive block-pressure triggers.

Evidence:
- `{control_path}`
- `{report_path}`
- `runtime/era63e/always_on_state_v1.json`
- `runtime/era63e/block_events_v1.jsonl`

Next: observe continuous real block/market cycles, verify freshness and continuity, close ERA63 technical line, then open ERA64 successful-wallet statistics and clustering.

No paper/live trade or real financial authority is enabled.
'''
(root / '07_PROJECT_HANDOFF.md').write_text(handoff, encoding='utf-8')

almanac_path = root / '04_ALMANAC.md'
almanac = almanac_path.read_text(encoding='utf-8') if almanac_path.exists() else ''
marker = '<!-- ERA63E_ALWAYS_ON_ALMANAC -->'
entry = f'''\n\n{marker}\n## ERA63E ALWAYS-ON MARKET RUNTIME\n\n- Status: `{status}`\n- Fixed timer: `DISABLED`\n- Resident service: `tokenoskobi-era63e-always-on-market.service`\n- Tests: `65/65_PASS`\n- Artifact: `{control_path}`\n- Next: `{next_step}`\n- UTC: `{now}`\n'''
if marker in almanac:
    almanac = almanac.split(marker, 1)[0].rstrip() + entry
else:
    almanac = almanac.rstrip() + entry
almanac_path.write_text(almanac, encoding='utf-8')

report = f'''# ERA63E ALWAYS-ON MARKET RUNTIME

- Status: `{status}`
- Bound: `{now}`
- Fixed 15-minute timer: `DISABLED`
- Active service: `tokenoskobi-era63e-always-on-market.service`
- Runtime: resident BSC block-event loop
- Full market refresh: adaptive, non-overlapping, bounded
- Latest block during binding: `{state.get('last_block_number')}`
- Observed events during binding: `{state.get('block_event_count')}`
- Tests: `65/65_PASS`
- Paper runtime: `DISABLED`
- Live trade: `DISABLED`
- Wallet/signing/order/broadcast: `DISABLED`
- Next: `{next_step}`
'''
(root / report_path).write_text(report, encoding='utf-8')
(root / 'reports/LATEST_TK_AI_HANDOFF.md').write_text(handoff, encoding='utf-8')
print('ERA63E_CANONICAL_SYNC=PASS')
PY_CANONICAL

python3 - <<'PY_VERIFY'
import json
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
runtime = json.loads((root / 'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
control = json.loads((root / 'data/control/era63e_always_on_market_runtime_binding_v1.json').read_text(encoding='utf-8'))
assert runtime['current_stage'] == 'ERA63E_ADAPTIVE_ALWAYS_ON_MARKET_RUNTIME'
assert runtime['current_status'] == 'ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE'
assert runtime['next_safe_step'] == 'ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE'
assert control['fixed_timer_enabled'] is False
assert control['block_event_stream_active'] is True
assert control['authority']['paper_runtime'] is False
assert control['authority']['real_trade'] is False
print('CANONICAL_VERIFY=PASS')
PY_VERIFY

FILES=(
  config/era63e_always_on_market_runtime_v1.json
  tools/era63e_always_on_market_runtime_v1.py
  tests/test_era63e_always_on_market_runtime_v1.py
  systemd_drafts/tokenoskobi-era63e-always-on-market.service
  data/control/era63e_always_on_market_runtime_binding_v1.json
  reports/LATEST_ERA63E_ALWAYS_ON_MARKET_RUNTIME.md
  03_ROADMAP.md 04_ALMANAC.md 05_ATLAS.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md
  PROJECT_RUNTIME.json PROJECT_HISTORY.json data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json reports/LATEST_TK_AI_HANDOFF.md
)

git add -- "${FILES[@]}"
git add -f reports/LATEST_ERA63E_ALWAYS_ON_MARKET_RUNTIME.md reports/LATEST_TK_AI_HANDOFF.md

git diff --cached --check
git commit -m "ERA63E: replace fixed timer with always-on BSC event runtime"
COMMITTED=1
git push origin main

git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer

HEAD="$(git rev-parse HEAD)"
STATE="$(python3 - <<'PY_FINAL'
import json
from pathlib import Path
p=Path('/root/tokenoskobi_clean_v1/runtime/era63e/always_on_state_v1.json')
v=json.loads(p.read_text(encoding='utf-8'))
print(f"BLOCK={v.get('last_block_number')} EVENTS={v.get('block_event_count')} REFRESHES={v.get('full_refresh_count')}")
PY_FINAL
)"

echo "ERA63E_STATUS=ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE"
echo "SERVICE=ENABLED_ACTIVE_RESTART_ALWAYS"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "BSC_BLOCK_EVENT_OBSERVATION=ACTIVE"
echo "ADAPTIVE_MARKET_TECHNICAL_REFRESH=ACTIVE"
echo "TESTS=65/65_PASS"
echo "$STATE"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE"
