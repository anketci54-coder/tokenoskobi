#!/usr/bin/env python3
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "tools" / "era63d_market_technical_runtime_v1.py"
CONFIG_PATH = ROOT / "config" / "era63d_market_technical_runtime_v1.json"

spec = importlib.util.spec_from_file_location("era63d_runtime", RUNTIME_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def candles(count: int = 80, start: int = 1_700_000_000, step: int = 300):
    rows = []
    price = 100.0
    for index in range(count):
        opening = price
        closing = price + 0.20 + (index % 3) * 0.01
        rows.append([
            start + index * step,
            opening,
            closing + 0.08,
            opening - 0.08,
            closing,
            1000.0 + index,
        ])
        price = closing
    return rows


def discovery():
    return {
        "data": [
            {
                "id": "bsc_0xpool1",
                "attributes": {
                    "address": "0xpool1",
                    "name": "TOKEN / USDT 0.25%",
                    "reserve_in_usd": "2000000",
                    "volume_usd": {"h24": "900000"},
                    "base_token_price_usd": "100",
                    "quote_token_price_usd": "1",
                    "transactions": {"h1": {"buys": 50, "sells": 40}},
                },
            },
            {
                "id": "bsc_0xpool2",
                "attributes": {
                    "address": "0xpool2",
                    "name": "SMALL / USDT",
                    "reserve_in_usd": "10000",
                    "volume_usd": {"h24": "1000"},
                    "base_token_price_usd": "2",
                    "quote_token_price_usd": "1",
                    "transactions": {"h1": {"buys": 1, "sells": 1}},
                },
            },
        ]
    }


def ohlcv():
    return {"data": {"attributes": {"ohlcv_list": list(reversed(candles()))}}}


class FakeClient:
    def __init__(self):
        self.request_count = 0

    def get_json(self, path, params=None):
        self.request_count += 1
        if path.endswith("trending_pools") or path.endswith("/pools"):
            return discovery()
        if "/ohlcv/" in path:
            return ohlcv()
        raise AssertionError(path)


class Era63DRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    def test_01_config_is_observation_only(self):
        module.validate_config(self.config)
        self.assertTrue(self.config["runtime_enabled"])
        self.assertTrue(self.config["observation_only"])
        for key in (
            "paper_runtime_enabled",
            "paper_position_write_enabled",
            "real_trade_enabled",
            "wallet_enabled",
            "signing_enabled",
            "real_order_enabled",
            "broadcast_enabled",
            "policy_expansion_enabled",
        ):
            self.assertFalse(self.config[key])

    def test_02_config_rejects_paper_runtime(self):
        config = copy.deepcopy(self.config)
        config["paper_runtime_enabled"] = True
        with self.assertRaises(module.Era63DRuntimeError):
            module.validate_config(config)

    def test_03_provider_is_https_allowlisted(self):
        client = module.ApiClient(self.config, sleeper=lambda _: None)
        url = client.build_url("/networks/bsc/pools", {"page": 1})
        self.assertTrue(url.startswith("https://api.geckoterminal.com/api/v2/"))

    def test_04_non_allowlisted_url_rejected(self):
        config = copy.deepcopy(self.config)
        config["provider"]["base_url"] = "http://example.com/api"
        with self.assertRaises(module.Era63DRuntimeError):
            module.validate_config(config)

    def test_05_pool_candidates_rank_real_liquidity(self):
        rows = module.parse_pool_candidates(discovery(), self.config)
        self.assertEqual(rows[0]["address"], "0xpool1")
        self.assertTrue(rows[0]["meets_primary_filter"])
        self.assertFalse(rows[1]["meets_primary_filter"])

    def test_06_pool_fee_is_parsed(self):
        fee, source = module.parse_fee_bps("TOKEN / USDT 0.25%", 30.0)
        self.assertEqual(fee, 25.0)
        self.assertEqual(source, "POOL_NAME_DISCLOSED")

    def test_07_pool_fee_falls_back_conservatively(self):
        fee, source = module.parse_fee_bps("TOKEN / USDT", 30.0)
        self.assertEqual(fee, 30.0)
        self.assertEqual(source, "CONFIG_CONSERVATIVE_DEFAULT")

    def test_08_ohlcv_is_sorted_and_validated(self):
        parsed = module.parse_ohlcv(ohlcv(), 60)
        self.assertEqual(len(parsed), 80)
        self.assertLess(parsed[0]["timestamp"], parsed[-1]["timestamp"])

    def test_09_insufficient_ohlcv_is_rejected(self):
        payload = {"data": {"attributes": {"ohlcv_list": candles(10)}}}
        with self.assertRaises(module.Era63DRuntimeError):
            module.parse_ohlcv(payload, 60)

    def test_10_engine_payload_uses_real_frames_and_estimated_reserves(self):
        pool = module.parse_pool_candidates(discovery(), self.config)[0]
        frames = {name: module.parse_ohlcv(ohlcv(), 60) for name in ("5m", "15m", "1h")}
        now = frames["1h"][-1]["timestamp"] + 30
        payload, quality = module.build_engine_payload(pool, frames, self.config, now)
        hop = payload["dex"]["routes"][0]["hops"][0]
        self.assertGreater(hop["reserve_in"], 0)
        self.assertGreater(hop["reserve_out"], 0)
        self.assertEqual(quality["pool_reserves"], "ESTIMATED_FROM_TVL_AND_BASE_PRICE")
        self.assertEqual(quality["token_tax_measurement"], "UNKNOWN_FAIL_CLOSED")

    def test_11_runtime_guard_blocks_paper_on_unknowns(self):
        fake_result = {"edge": {"action": "BUY"}}
        guard = module.runtime_guard(fake_result, {"market_age_sec": 10})
        self.assertEqual(guard["paper_action"], "DISABLED")
        self.assertEqual(guard["final_trade_action"], "NONE")
        self.assertIn("TOKEN_TAX_UNKNOWN", guard["blocks"])
        self.assertIn("COORDINATED_INTELLIGENCE_NOT_BOUND", guard["blocks"])

    def test_12_real_engine_integration_runs(self):
        client = FakeClient()
        last = candles()[-1][0]
        snapshot = module.run_runtime(
            self.config,
            client=client,
            now=datetime.fromtimestamp(last + 30, timezone.utc),
        )
        self.assertGreaterEqual(snapshot["successful_pool_count"], 1)
        self.assertTrue(snapshot["authority"]["observation_runtime"])
        self.assertFalse(snapshot["authority"]["paper_runtime"])
        self.assertFalse(snapshot["authority"]["real_trade"])

    def test_13_request_budget_is_bounded(self):
        maximum = 2 + int(self.config["provider"]["max_pools"]) * len(self.config["provider"]["timeframes"])
        self.assertLessEqual(maximum, 11)
        self.assertGreaterEqual(self.config["provider"]["minimum_request_interval_sec"], 1.0)

    def test_14_panel_has_no_financial_authority(self):
        client = FakeClient()
        last = candles()[-1][0]
        snapshot = module.run_runtime(
            self.config,
            client=client,
            now=datetime.fromtimestamp(last + 30, timezone.utc),
        )
        panel = module.build_panel(snapshot)
        self.assertEqual(panel["decision"], "REAL_MARKET_TECHNICAL_OBSERVATION_ACTIVE")
        self.assertGreaterEqual(panel["source_count"], 1)
        for value in panel["authority"].values():
            self.assertFalse(value)

    def test_15_outputs_are_atomic_and_runtime_only(self):
        client = FakeClient()
        last = candles()[-1][0]
        snapshot = module.run_runtime(
            self.config,
            client=client,
            now=datetime.fromtimestamp(last + 30, timezone.utc),
        )
        with tempfile.TemporaryDirectory() as directory:
            original_root = module.ROOT
            try:
                module.ROOT = Path(directory)
                config = copy.deepcopy(self.config)
                config["outputs"] = {
                    "latest_snapshot": "runtime/latest.json",
                    "health": "runtime/health.json",
                    "observations_jsonl": "runtime/observations.jsonl",
                    "observations_max_bytes": 1000000,
                    "panel_readmodel": "panel/technical.json",
                }
                module.write_outputs(snapshot, config)
                self.assertTrue((Path(directory) / "runtime/latest.json").exists())
                self.assertTrue((Path(directory) / "panel/technical.json").exists())
                self.assertTrue((Path(directory) / "runtime/observations.jsonl").exists())
            finally:
                module.ROOT = original_root

    def test_16_source_has_no_wallet_signing_order_or_dynamic_execution(self):
        source = RUNTIME_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_imports = {"requests", "httpx", "web3", "socket", "subprocess"}
        forbidden_calls = {"eval", "exec", "compile", "__import__", "system", "popen"}
        imports = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
        self.assertFalse(imports & forbidden_imports)
        self.assertFalse(calls & forbidden_calls)
        for forbidden in (
            "send_raw_transaction",
            "sign_transaction",
            "eth_sendTransaction",
            "eth_sendRawTransaction",
            "create_order(",
            "swapExact",
            "shell=True",
        ):
            self.assertNotIn(forbidden, source)

    def test_17_systemd_units_remain_observation_only(self):
        service = (ROOT / "systemd_drafts/tokenoskobi-era63d-market-technical.service").read_text(encoding="utf-8")
        timer = (ROOT / "systemd_drafts/tokenoskobi-era63d-market-technical.timer").read_text(encoding="utf-8")
        self.assertIn("era63d_market_technical_runtime_v1.py", service)
        self.assertNotIn("bash -c", service)
        self.assertNotIn("sh -c", service)
        self.assertIn("OnUnitActiveSec=15min", timer)
        self.assertIn("Persistent=true", timer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
