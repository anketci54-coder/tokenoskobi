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
        reason = module.refresh_reason(event, state, self.config, 500.0)
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
        tree = ast.parse(ENGINE_PATH.read_text(encoding='utf-8'))
        methods = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != 'call' or not node.args:
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                methods.add(first.value)
        self.assertEqual(methods, {'eth_chainId', 'eth_blockNumber', 'eth_getBlockByNumber'})

    def test_14_systemd_is_service_not_timer(self):
        unit = (ROOT / 'systemd_drafts' / 'tokenoskobi-era63e-always-on-market.service').read_text(encoding='utf-8')
        self.assertIn('Restart=always', unit)
        self.assertNotIn('[Timer]', unit)
        self.assertNotIn('OnUnitActiveSec', unit)


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



if __name__ == '__main__':
    unittest.main(verbosity=2)
