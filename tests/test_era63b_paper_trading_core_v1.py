#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "tools" / "era63_paper_trading_core_v1.py"
CONFIG_PATH = ROOT / "config" / "era63_paper_trading_core_v1.json"

spec = importlib.util.spec_from_file_location("era63_paper_core", ENGINE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def make_payload(
    *,
    rising: bool = True,
    spread_bps: float = 8.0,
    depth: float = 100000.0,
    age: float = 5.0,
) -> dict:
    candles = []
    price = 100.0
    for index in range(40):
        delta = 0.45 if rising else (-0.15 if index % 2 == 0 else 0.10)
        open_price = price
        close_price = max(1.0, price + delta)
        high = max(open_price, close_price) + 0.20
        low = min(open_price, close_price) - 0.20
        candles.append(
            {
                "timestamp": 1_700_000_000 + index * 60,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close_price,
                "volume": 1000 + index,
            }
        )
        price = close_price
    return {
        "equity_usd": 10000.0,
        "candles": candles,
        "market": {
            "quote_depth_usd": depth,
            "spread_bps": spread_bps,
            "market_age_sec": age,
            "source": "TEST_FIXTURE",
        },
        "mark_price": price * 1.002,
    }


class Era63PaperCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    def test_01_rising_market_produces_bounded_simulated_fill(self):
        result = module.run_cycle(make_payload(), self.config)
        self.assertEqual(result["edge"]["action"], "BUY")
        self.assertEqual(result["fill"]["status"], "SIMULATED_FILLED")
        self.assertGreater(result["sizing"]["notional_usd"], 0)
        self.assertLessEqual(
            result["sizing"]["notional_usd"],
            10000.0 * self.config["max_position_fraction"],
        )

    def test_02_authority_is_simulation_only(self):
        result = module.run_cycle(make_payload(), self.config)
        self.assertTrue(result["authority"]["paper_simulation"])
        for key in ("real_trade", "wallet", "signing", "real_order", "broadcast"):
            self.assertFalse(result["authority"][key])

    def test_03_stale_market_waits(self):
        result = module.run_cycle(make_payload(age=9999), self.config)
        self.assertEqual(result["edge"]["action"], "WAIT")
        self.assertIn("MARKET_DATA_STALE", result["edge"]["blocks"])
        self.assertEqual(result["fill"]["status"], "NO_FILL")

    def test_04_wide_spread_waits(self):
        result = module.run_cycle(make_payload(spread_bps=500), self.config)
        self.assertEqual(result["edge"]["action"], "WAIT")
        self.assertIn("SPREAD_TOO_WIDE", result["edge"]["blocks"])

    def test_05_low_liquidity_waits(self):
        result = module.run_cycle(make_payload(depth=500), self.config)
        self.assertEqual(result["edge"]["action"], "WAIT")
        self.assertIn("LIQUIDITY_RATIO_TOO_LOW", result["edge"]["blocks"])

    def test_06_invalid_candle_is_rejected(self):
        payload = make_payload()
        payload["candles"][10]["high"] = 1
        with self.assertRaises(module.PaperCoreError):
            module.run_cycle(payload, self.config)

    def test_07_risk_fraction_over_limit_rejected(self):
        config = copy.deepcopy(self.config)
        config["risk_fraction"] = 0.5
        with self.assertRaises(module.PaperCoreError):
            module.run_cycle(make_payload(), config)

    def test_08_cost_model_is_positive_and_complete(self):
        result = module.run_cycle(make_payload(), self.config)
        costs = result["fill"]["costs"]
        self.assertGreater(costs["total_bps"], 0)
        self.assertGreater(costs["total_usd"], 0)
        for key in ("fee_bps", "spread_bps", "slippage_bps", "mev_buffer_bps", "gas_bps"):
            self.assertIn(key, costs)

    def test_09_portfolio_and_drawdown_are_finite(self):
        result = module.run_cycle(make_payload(), self.config)
        portfolio = result["portfolio"]
        for value in portfolio.values():
            self.assertTrue(math.isfinite(float(value)))
        self.assertGreaterEqual(portfolio["drawdown_fraction"], 0)

    def test_10_latency_contains_all_stages(self):
        result = module.run_cycle(make_payload(), self.config)
        for key in (
            "validate_ms",
            "technical_ms",
            "edge_ms",
            "execution_ms",
            "accounting_ms",
            "total_ms",
        ):
            self.assertIn(key, result["latency_ms"])
            self.assertGreaterEqual(result["latency_ms"][key], 0)

    def test_11_deterministic_decision_fields(self):
        first = module.run_cycle(make_payload(), self.config)
        second = module.run_cycle(make_payload(), self.config)
        for key in ("technical", "liquidity", "edge", "sizing", "fill", "portfolio"):
            self.assertEqual(first[key], second[key])

    def test_12_source_has_no_network_or_dynamic_execution(self):
        import ast
        tree = ast.parse(ENGINE_PATH.read_text(encoding="utf-8"))
        forbidden_imports = {"requests", "urllib", "httpx", "web3", "socket", "subprocess"}
        forbidden_calls = {"eval", "exec", "compile", "__import__"}
        imports = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                calls.add(node.func.id)
        self.assertFalse(imports & forbidden_imports)
        self.assertFalse(calls & forbidden_calls)

    def test_13_runtime_and_real_authorities_remain_disabled(self):
        self.assertFalse(self.config["paper_runtime_enabled"])
        self.assertFalse(self.config["unattended_runtime_enabled"])
        self.assertFalse(self.config["real_trade_enabled"])
        self.assertFalse(self.config["wallet_enabled"])
        self.assertFalse(self.config["signing_enabled"])
        self.assertFalse(self.config["real_order_broadcast_enabled"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
