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
