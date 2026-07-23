#!/usr/bin/env python3
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "tools" / "era63_technical_dex_execution_v1.py"
CONFIG_PATH = ROOT / "config" / "era63c_technical_dex_execution_v1.json"

spec = importlib.util.spec_from_file_location("era63c_engine", ENGINE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def make_candles(
    *,
    start: float = 1.0,
    step: float = 0.003,
    count: int = 90,
    interval: int = 60,
    falling: bool = False,
) -> list[dict]:
    candles = []
    price = start
    for index in range(count):
        direction = -1.0 if falling else 1.0
        delta = direction * step * (1.0 + 0.2 * math.sin(index / 5.0))
        open_price = price
        close_price = max(0.05, price + delta)
        high = max(open_price, close_price) + abs(delta) * 0.5 + 0.001
        low = max(0.001, min(open_price, close_price) - abs(delta) * 0.5 - 0.001)
        candles.append(
            {
                "timestamp": 1_700_000_000 + index * interval,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close_price,
                "volume": 10_000.0 * (1.0 + 0.01 * index),
            }
        )
        price = close_price
    return candles


def route(route_id: str, reserve: float, fee_bps: float = 25.0, hops: int = 1) -> dict:
    return {
        "route_id": route_id,
        "hops": [
            {
                "pool_id": f"{route_id}_{index}",
                "reserve_in": reserve,
                "reserve_out": reserve,
                "fee_bps": fee_bps,
                "token_out_price_usd": 1.0,
            }
            for index in range(hops)
        ],
    }


def payload(
    *,
    reserve: float = 1_000_000.0,
    slippage: float = 60.0,
    historical: float = 0.05,
    gas_competition: float = 0.2,
    pending: float = 100.0,
    public: bool = True,
    private_relay: bool = False,
    tax_bps: float = 0.0,
    age: float = 5.0,
    routes: list[dict] | None = None,
    falling: bool = False,
) -> dict:
    return {
        "equity_usd": 10_000.0,
        "mark_price_usd": 1.10,
        "timeframes": {
            "5m": make_candles(step=0.0025, interval=300, falling=falling),
            "15m": make_candles(step=0.0030, interval=900, falling=falling),
            "1h": make_candles(step=0.0035, interval=3600, falling=falling),
        },
        "dex": {
            "market_age_sec": age,
            "slippage_tolerance_bps": slippage,
            "gas_usd": 0.15,
            "mempool": {
                "public": public,
                "private_relay": private_relay,
                "pending_tx_count": pending,
                "gas_competition_ratio": gas_competition,
                "historical_sandwich_rate": historical,
            },
            "token_tax": {
                "buy_bps": tax_bps / 2.0,
                "sell_bps": tax_bps / 2.0,
            },
            "routes": routes or [route("direct", reserve)],
        },
    }


class Era63CTechnicalDexExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    def test_01_safe_rising_market_produces_buy(self):
        result = module.run_cycle(payload(), self.config)
        self.assertEqual(result["edge"]["action"], "BUY")
        self.assertEqual(result["fill"]["status"], "SIMULATED_FILLED")

    def test_02_falling_market_waits(self):
        result = module.run_cycle(payload(falling=True), self.config)
        self.assertEqual(result["edge"]["action"], "WAIT")

    def test_03_technical_indicators_complete(self):
        result = module.run_cycle(payload(), self.config)
        frame = result["technical"]["frames"]["1h"]
        for key in (
            "ema_fast", "ema_slow", "ema_long", "rsi", "atr", "adx",
            "macd", "macd_signal", "macd_histogram",
            "bollinger_upper", "bollinger_lower", "volume_zscore",
            "obv_slope", "support", "resistance",
        ):
            self.assertIn(key, frame)
            self.assertTrue(math.isfinite(float(frame[key])))

    def test_04_multitimeframe_consensus_is_measured(self):
        result = module.run_cycle(payload(), self.config)
        self.assertGreaterEqual(result["technical"]["consensus"], 0.6)
        self.assertEqual(set(result["technical"]["frames"]), {"5m", "15m", "1h"})

    def test_05_cpmm_output_is_positive(self):
        value = module.cpmm_amount_out(100.0, 100_000.0, 100_000.0, 25.0)
        self.assertGreater(value, 0.0)
        self.assertLess(value, 100.0)

    def test_06_price_impact_increases_with_size(self):
        hops = [module.validate_hop(route("x", 100_000.0)["hops"][0], 0)]
        small = module.route_quote(100.0, hops)
        large = module.route_quote(5_000.0, hops)
        self.assertGreater(large["price_impact_bps"], small["price_impact_bps"])

    def test_07_dynamic_sandwich_risk_detected(self):
        result = module.run_cycle(
            payload(
                reserve=20_000.0,
                slippage=300.0,
                historical=0.8,
                gas_competition=0.9,
                pending=900.0,
            ),
            self.config,
        )
        selected = result["execution_probe"]["selected"]
        self.assertGreater(selected["sandwich"]["probability"], 0.5)
        self.assertGreater(selected["sandwich"]["expected_loss_bps"], 0.0)
        self.assertEqual(result["edge"]["action"], "WAIT")

    def test_08_private_relay_reduces_sandwich_probability(self):
        public_result = module.run_cycle(
            payload(
                reserve=20_000.0,
                slippage=120.0,
                historical=0.8,
                gas_competition=0.9,
                pending=900.0,
            ),
            self.config,
        )
        protected_result = module.run_cycle(
            payload(
                reserve=20_000.0,
                slippage=120.0,
                historical=0.8,
                gas_competition=0.9,
                pending=900.0,
                public=False,
                private_relay=True,
            ),
            self.config,
        )
        public_probability = public_result["execution_probe"]["selected"]["sandwich"]["probability"]
        protected_probability = protected_result["execution_probe"]["selected"]["sandwich"]["probability"]
        self.assertLess(protected_probability, public_probability)

    def test_09_high_token_tax_blocks(self):
        result = module.run_cycle(payload(tax_bps=1000.0), self.config)
        self.assertEqual(result["edge"]["action"], "WAIT")
        self.assertIn("TOKEN_TAX_TOO_HIGH", result["execution_probe"]["selected"]["blocks"])

    def test_10_stale_dex_data_blocks(self):
        result = module.run_cycle(payload(age=999.0), self.config)
        self.assertIn("DEX_MARKET_DATA_STALE", result["execution_probe"]["selected"]["blocks"])
        self.assertEqual(result["edge"]["action"], "WAIT")

    def test_11_route_selector_prefers_deeper_route(self):
        routes = [route("shallow", 10_000.0), route("deep", 1_000_000.0, 30.0)]
        result = module.run_cycle(payload(routes=routes), self.config)
        self.assertEqual(result["execution_probe"]["selected_route_id"], "deep")

    def test_12_multihop_route_reports_route_risk(self):
        result = module.run_cycle(payload(routes=[route("multi", 1_000_000.0, hops=2)]), self.config)
        selected = result["execution_probe"]["selected"]
        self.assertEqual(selected["quote"]["route_hops"], 2)
        self.assertGreater(selected["sandwich"]["probability_components"]["route_score"], 0.0)

    def test_13_adaptive_sizing_reduces_unsafe_notional(self):
        result = module.run_cycle(payload(reserve=100_000.0), self.config)
        self.assertEqual(result["edge"]["action"], "BUY")
        self.assertLess(
            result["sizing"]["notional_usd"],
            result["proposed_sizing"]["proposed_notional_usd"],
        )
        self.assertGreater(len(result["sizing"]["attempts"]), 1)

    def test_14_net_edge_includes_mev_and_sandwich(self):
        result = module.run_cycle(payload(), self.config)
        selected = result["execution_probe"]["selected"]
        self.assertIn("expected_sandwich_loss_bps", result["fill"]["costs"])
        self.assertIn("expected_other_mev_bps", result["fill"]["costs"])
        self.assertAlmostEqual(
            result["edge"]["probe_net_edge_bps"],
            result["edge"]["gross_edge_bps"] - selected["total_execution_cost_bps"],
            places=9,
        )

    def test_15_execution_protection_recommendations_exist(self):
        value = payload(reserve=100_000.0)
        execution = module.evaluate_routes(1_500.0, value["dex"], self.config)
        protections = execution["selected"]["protections"]
        self.assertIn("USE_PRIVATE_OR_PROTECTED_RELAY", protections)
        self.assertTrue(any(item.startswith("SPLIT_ORDER_INTO_") for item in protections))

    def test_16_portfolio_values_are_finite(self):
        result = module.run_cycle(payload(), self.config)
        for value in result["portfolio"].values():
            self.assertTrue(math.isfinite(float(value)))

    def test_17_deterministic_decision_fields(self):
        first = module.run_cycle(payload(), self.config)
        second = module.run_cycle(payload(), self.config)
        for key in (
            "technical", "execution_probe", "edge", "proposed_sizing",
            "sizing", "fill", "portfolio",
        ):
            self.assertEqual(first[key], second[key])

    def test_18_authority_split_is_correct(self):
        result = module.run_cycle(payload(), self.config)
        authority = result["authority"]
        self.assertTrue(authority["paper_simulation"])
        self.assertTrue(authority["paper_order_create"])
        self.assertTrue(authority["paper_position_management"])
        for key in ("real_trade", "wallet", "signing", "real_order", "broadcast"):
            self.assertFalse(authority[key])
        self.assertFalse(authority["system_may_expand_policy"])
        self.assertTrue(authority["risk_engine_veto"])

    def test_19_source_has_no_network_or_dynamic_execution(self):
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

    def test_20_runtime_and_real_authorities_remain_disabled(self):
        for key in (
            "paper_runtime_enabled",
            "unattended_runtime_enabled",
            "real_trade_enabled",
            "wallet_enabled",
            "signing_enabled",
            "real_order_broadcast_enabled",
        ):
            self.assertFalse(self.config[key])

    def test_21_invalid_config_is_rejected(self):
        bad = copy.deepcopy(self.config)
        bad["risk_fraction"] = 0.5
        with self.assertRaises(module.Era63CError):
            module.run_cycle(payload(), bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
