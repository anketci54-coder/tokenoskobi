#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

ROOT="/root/tokenoskobi_clean_v1"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era63b_paper_core_backup_${STAMP}.tar.gz"
COMMITTED=0

NEW_FILES=(
  "config/era63_paper_trading_core_v1.json"
  "tools/era63_paper_trading_core_v1.py"
  "tests/test_era63b_paper_trading_core_v1.py"
  "data/replay/era63b_paper_core_fixture_v1.json"
  "data/replay/era63b_paper_core_sample_result_v1.json"
  "data/control/era63b_accelerated_paper_trading_core_build_v1.json"
  "reports/LATEST_ERA63_PAPER_TRADING_CORE_BUILD.md"
)

TRACKED_FILES=(
  "03_ROADMAP.md"
  "04_ALMANAC.md"
  "06_PROJECT_MASTER_STATE.md"
  "07_PROJECT_HANDOFF.md"
  "PROJECT_RUNTIME.json"
  "PROJECT_HISTORY.json"
  "data/tokenoskobi_v1_v8_master_era_roadmap.json"
  "data/control/latest_tk_machine_state.json"
  "reports/LATEST_TK_AI_HANDOFF.md"
)

ALL_FILES=("${TRACKED_FILES[@]}" "${NEW_FILES[@]}")

rollback() {
  rc=$?
  trap - ERR
  echo "ERA63B_FAILED_RC=$rc"
  if [[ "$COMMITTED" -eq 0 && -f "$BACKUP" ]]; then
    tar -xzf "$BACKUP" -C "$ROOT"
    for file in "${NEW_FILES[@]}"; do
      if ! tar -tzf "$BACKUP" | grep -Fxq "$file"; then
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

python3 <<'PY'
import json
from pathlib import Path
root = Path("/root/tokenoskobi_clean_v1")
runtime = json.loads((root / "PROJECT_RUNTIME.json").read_text(encoding="utf-8"))
assert runtime.get("current_era") == "ERA63"
assert runtime.get("next_safe_step") == "ERA63B_ACCELERATED_PAPER_TRADING_CORE_BUILD"
print("PRECHECK=VERIFIED")
PY

printf '%s\n' "${ALL_FILES[@]}" |
while IFS= read -r file; do
  [[ -e "$file" ]] && printf '%s\n' "$file"
done >/tmp/era63b_existing_files.txt

tar -czf "$BACKUP" -C "$ROOT" -T /tmp/era63b_existing_files.txt
echo "BACKUP=$BACKUP"

mkdir -p config tools tests data/replay data/control reports

cat >config/era63_paper_trading_core_v1.json <<'ERA63_CONFIG'
{
  "schema": "tokenoskobi.era63.paper_core_config.v1",
  "mode": "BUILD_ONLY_ZERO_REAL_FUNDS",
  "paper_runtime_enabled": false,
  "unattended_runtime_enabled": false,
  "real_trade_enabled": false,
  "wallet_enabled": false,
  "signing_enabled": false,
  "real_order_broadcast_enabled": false,
  "fast_window": 5,
  "slow_window": 20,
  "rsi_window": 14,
  "atr_window": 14,
  "min_edge_bps": 8.0,
  "risk_fraction": 0.01,
  "max_position_fraction": 0.2,
  "atr_stop_multiple": 2.0,
  "min_stop_bps": 40.0,
  "min_notional_usd": 10.0,
  "probe_notional_usd": 100.0,
  "min_liquidity_ratio": 20.0,
  "max_spread_bps": 40.0,
  "max_market_age_sec": 120.0,
  "fee_bps": 25.0,
  "mev_buffer_bps": 5.0,
  "gas_usd": 0.1,
  "impact_factor_bps": 250.0
}
ERA63_CONFIG

cat >tools/era63_paper_trading_core_v1.py <<'ERA63_ENGINE'
#!/usr/bin/env python3
"""Deterministic, zero-real-funds paper-trading core for ERA63.

The module is pure computation. It does not call networks, wallets, signers,
exchanges, databases, services or timers.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "tokenoskobi.era63.paper_core.v1"


class PaperCoreError(ValueError):
    pass


def _finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise PaperCoreError(f"{name}:NOT_NUMERIC") from exc
    if not math.isfinite(number):
        raise PaperCoreError(f"{name}:NOT_FINITE")
    return number


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        raise PaperCoreError("MEAN_EMPTY")
    return sum(items) / len(items)


def validate_config(config: dict[str, Any]) -> None:
    if not isinstance(config, dict):
        raise PaperCoreError("CONFIG_NOT_OBJECT")
    required_positive = (
        "fast_window",
        "slow_window",
        "rsi_window",
        "atr_window",
        "min_edge_bps",
        "risk_fraction",
        "max_position_fraction",
        "atr_stop_multiple",
        "min_stop_bps",
        "min_liquidity_ratio",
        "max_spread_bps",
        "max_market_age_sec",
    )
    for key in required_positive:
        value = _finite(config.get(key), f"config.{key}")
        if value <= 0:
            raise PaperCoreError(f"config.{key}:MUST_BE_POSITIVE")
    if int(config["fast_window"]) >= int(config["slow_window"]):
        raise PaperCoreError("FAST_WINDOW_MUST_BE_LT_SLOW_WINDOW")
    for key in ("fee_bps", "mev_buffer_bps", "gas_usd", "impact_factor_bps"):
        if _finite(config.get(key), f"config.{key}") < 0:
            raise PaperCoreError(f"config.{key}:MUST_BE_NONNEGATIVE")
    if _finite(config["risk_fraction"], "risk_fraction") > 0.1:
        raise PaperCoreError("RISK_FRACTION_TOO_HIGH")
    if _finite(config["max_position_fraction"], "max_position_fraction") > 1:
        raise PaperCoreError("MAX_POSITION_FRACTION_TOO_HIGH")


def validate_candles(candles: Any, minimum: int) -> list[dict[str, float]]:
    if not isinstance(candles, list) or len(candles) < minimum:
        raise PaperCoreError(f"CANDLES_MINIMUM:{minimum}")
    normalized: list[dict[str, float]] = []
    previous_ts = -1.0
    for index, row in enumerate(candles):
        if not isinstance(row, dict):
            raise PaperCoreError(f"CANDLE_{index}:NOT_OBJECT")
        item = {
            "timestamp": _finite(row.get("timestamp"), f"candle.{index}.timestamp"),
            "open": _finite(row.get("open"), f"candle.{index}.open"),
            "high": _finite(row.get("high"), f"candle.{index}.high"),
            "low": _finite(row.get("low"), f"candle.{index}.low"),
            "close": _finite(row.get("close"), f"candle.{index}.close"),
            "volume": _finite(row.get("volume", 0), f"candle.{index}.volume"),
        }
        if min(item["open"], item["high"], item["low"], item["close"]) <= 0:
            raise PaperCoreError(f"CANDLE_{index}:NONPOSITIVE_PRICE")
        if item["high"] < max(item["open"], item["close"]):
            raise PaperCoreError(f"CANDLE_{index}:HIGH_INVALID")
        if item["low"] > min(item["open"], item["close"]):
            raise PaperCoreError(f"CANDLE_{index}:LOW_INVALID")
        if item["timestamp"] <= previous_ts:
            raise PaperCoreError(f"CANDLE_{index}:TIMESTAMP_NOT_INCREASING")
        previous_ts = item["timestamp"]
        normalized.append(item)
    return normalized


def sma(values: list[float], window: int) -> float:
    if len(values) < window:
        raise PaperCoreError("SMA_INSUFFICIENT_DATA")
    return _mean(values[-window:])


def rsi(values: list[float], window: int) -> float:
    if len(values) <= window:
        raise PaperCoreError("RSI_INSUFFICIENT_DATA")
    changes = [values[i] - values[i - 1] for i in range(len(values) - window, len(values))]
    gains = _mean(max(change, 0.0) for change in changes)
    losses = _mean(max(-change, 0.0) for change in changes)
    if losses == 0:
        return 100.0 if gains > 0 else 50.0
    relative = gains / losses
    return 100.0 - (100.0 / (1.0 + relative))


def atr(candles: list[dict[str, float]], window: int) -> float:
    if len(candles) <= window:
        raise PaperCoreError("ATR_INSUFFICIENT_DATA")
    true_ranges: list[float] = []
    for index in range(len(candles) - window, len(candles)):
        current = candles[index]
        previous_close = candles[index - 1]["close"]
        true_ranges.append(
            max(
                current["high"] - current["low"],
                abs(current["high"] - previous_close),
                abs(current["low"] - previous_close),
            )
        )
    return _mean(true_ranges)


def technical_snapshot(candles: list[dict[str, float]], config: dict[str, Any]) -> dict[str, float]:
    closes = [row["close"] for row in candles]
    fast = sma(closes, int(config["fast_window"]))
    slow = sma(closes, int(config["slow_window"]))
    current = closes[-1]
    atr_value = atr(candles, int(config["atr_window"]))
    rsi_value = rsi(closes, int(config["rsi_window"]))
    trend_bps = ((fast / slow) - 1.0) * 10000.0
    momentum_bps = (rsi_value - 50.0) * 2.0
    volatility_bps = (atr_value / current) * 10000.0
    return {
        "price": current,
        "sma_fast": fast,
        "sma_slow": slow,
        "rsi": rsi_value,
        "atr": atr_value,
        "trend_bps": trend_bps,
        "momentum_bps": momentum_bps,
        "volatility_bps": volatility_bps,
    }


def liquidity_snapshot(market: dict[str, Any], price: float, config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(market, dict):
        raise PaperCoreError("MARKET_NOT_OBJECT")
    quote_depth = _finite(market.get("quote_depth_usd"), "market.quote_depth_usd")
    spread_bps = _finite(market.get("spread_bps"), "market.spread_bps")
    market_age_sec = _finite(market.get("market_age_sec"), "market.market_age_sec")
    if quote_depth <= 0:
        raise PaperCoreError("MARKET_DEPTH_NONPOSITIVE")
    if spread_bps < 0:
        raise PaperCoreError("MARKET_SPREAD_NEGATIVE")
    stale = market_age_sec > float(config["max_market_age_sec"])
    spread_block = spread_bps > float(config["max_spread_bps"])
    return {
        "price": price,
        "quote_depth_usd": quote_depth,
        "spread_bps": spread_bps,
        "market_age_sec": market_age_sec,
        "stale": stale,
        "spread_block": spread_block,
        "source": str(market.get("source") or "LOCAL_INPUT"),
    }


def estimate_costs(notional_usd: float, liquidity: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    if notional_usd <= 0:
        return {
            "fee_bps": float(config["fee_bps"]),
            "spread_bps": liquidity["spread_bps"] / 2.0,
            "slippage_bps": 0.0,
            "mev_buffer_bps": float(config["mev_buffer_bps"]),
            "gas_bps": 0.0,
            "total_bps": 0.0,
            "total_usd": 0.0,
        }
    depth = liquidity["quote_depth_usd"]
    participation = notional_usd / depth
    slippage_bps = participation * float(config["impact_factor_bps"])
    gas_bps = (float(config["gas_usd"]) / notional_usd) * 10000.0
    total_bps = (
        float(config["fee_bps"])
        + liquidity["spread_bps"] / 2.0
        + slippage_bps
        + float(config["mev_buffer_bps"])
        + gas_bps
    )
    return {
        "fee_bps": float(config["fee_bps"]),
        "spread_bps": liquidity["spread_bps"] / 2.0,
        "slippage_bps": slippage_bps,
        "mev_buffer_bps": float(config["mev_buffer_bps"]),
        "gas_bps": gas_bps,
        "total_bps": total_bps,
        "total_usd": notional_usd * total_bps / 10000.0,
    }


def opportunity_edge(
    technical: dict[str, float],
    liquidity: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    gross_edge_bps = technical["trend_bps"] * 0.7 + technical["momentum_bps"] * 0.3
    probe_notional = float(config["probe_notional_usd"])
    probe_cost = estimate_costs(probe_notional, liquidity, config)
    net_edge_bps = gross_edge_bps - probe_cost["total_bps"]
    blocks: list[str] = []
    if liquidity["stale"]:
        blocks.append("MARKET_DATA_STALE")
    if liquidity["spread_block"]:
        blocks.append("SPREAD_TOO_WIDE")
    if liquidity["quote_depth_usd"] / probe_notional < float(config["min_liquidity_ratio"]):
        blocks.append("LIQUIDITY_RATIO_TOO_LOW")
    action = "BUY" if not blocks and net_edge_bps >= float(config["min_edge_bps"]) else "WAIT"
    return {
        "action": action,
        "gross_edge_bps": gross_edge_bps,
        "probe_cost_bps": probe_cost["total_bps"],
        "net_edge_bps": net_edge_bps,
        "blocks": blocks,
    }


def position_size(
    action: str,
    equity_usd: float,
    technical: dict[str, float],
    config: dict[str, Any],
) -> dict[str, float]:
    equity = _finite(equity_usd, "equity_usd")
    if equity <= 0:
        raise PaperCoreError("EQUITY_NONPOSITIVE")
    if action != "BUY":
        return {
            "risk_budget_usd": 0.0,
            "stop_distance_usd": 0.0,
            "notional_usd": 0.0,
            "units": 0.0,
        }
    price = technical["price"]
    stop_distance = max(
        technical["atr"] * float(config["atr_stop_multiple"]),
        price * float(config["min_stop_bps"]) / 10000.0,
    )
    risk_budget = equity * float(config["risk_fraction"])
    units_by_risk = risk_budget / stop_distance
    notional_by_risk = units_by_risk * price
    notional_cap = equity * float(config["max_position_fraction"])
    notional = min(notional_by_risk, notional_cap)
    if notional < float(config["min_notional_usd"]):
        return {
            "risk_budget_usd": risk_budget,
            "stop_distance_usd": stop_distance,
            "notional_usd": 0.0,
            "units": 0.0,
        }
    return {
        "risk_budget_usd": risk_budget,
        "stop_distance_usd": stop_distance,
        "notional_usd": notional,
        "units": notional / price,
    }


def simulate_fill(
    action: str,
    technical: dict[str, float],
    sizing: dict[str, float],
    liquidity: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    notional = sizing["notional_usd"]
    if action != "BUY" or notional <= 0:
        return {
            "status": "NO_FILL",
            "side": "NONE",
            "notional_usd": 0.0,
            "units": 0.0,
            "reference_price": technical["price"],
            "fill_price": technical["price"],
            "costs": estimate_costs(0.0, liquidity, config),
        }
    costs = estimate_costs(notional, liquidity, config)
    fill_price = technical["price"] * (1.0 + costs["total_bps"] / 10000.0)
    return {
        "status": "SIMULATED_FILLED",
        "side": "BUY",
        "notional_usd": notional,
        "units": notional / fill_price,
        "reference_price": technical["price"],
        "fill_price": fill_price,
        "costs": costs,
    }


def portfolio_outcome(
    equity_usd: float,
    fill: dict[str, Any],
    mark_price: float,
) -> dict[str, float]:
    equity = float(equity_usd)
    mark = _finite(mark_price, "mark_price")
    if fill["status"] != "SIMULATED_FILLED":
        return {
            "equity_before_usd": equity,
            "equity_after_usd": equity,
            "unrealized_pnl_usd": 0.0,
            "drawdown_fraction": 0.0,
        }
    unrealized = fill["units"] * (mark - fill["fill_price"])
    after = equity + unrealized
    drawdown = max(0.0, (equity - after) / equity)
    return {
        "equity_before_usd": equity,
        "equity_after_usd": after,
        "unrealized_pnl_usd": unrealized,
        "drawdown_fraction": drawdown,
    }


def run_cycle(payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    validate_config(config)
    if not isinstance(payload, dict):
        raise PaperCoreError("PAYLOAD_NOT_OBJECT")
    minimum = max(
        int(config["slow_window"]),
        int(config["rsi_window"]) + 1,
        int(config["atr_window"]) + 1,
    )
    timings: dict[str, float] = {}
    started = time.perf_counter()

    stage = time.perf_counter()
    candles = validate_candles(payload.get("candles"), minimum)
    timings["validate_ms"] = (time.perf_counter() - stage) * 1000.0

    stage = time.perf_counter()
    technical = technical_snapshot(candles, config)
    timings["technical_ms"] = (time.perf_counter() - stage) * 1000.0

    stage = time.perf_counter()
    liquidity = liquidity_snapshot(payload.get("market"), technical["price"], config)
    edge = opportunity_edge(technical, liquidity, config)
    timings["edge_ms"] = (time.perf_counter() - stage) * 1000.0

    stage = time.perf_counter()
    sizing = position_size(edge["action"], payload.get("equity_usd"), technical, config)
    fill = simulate_fill(edge["action"], technical, sizing, liquidity, config)
    timings["execution_ms"] = (time.perf_counter() - stage) * 1000.0

    stage = time.perf_counter()
    mark_price = payload.get("mark_price", technical["price"])
    portfolio = portfolio_outcome(float(payload["equity_usd"]), fill, mark_price)
    timings["accounting_ms"] = (time.perf_counter() - stage) * 1000.0
    timings["total_ms"] = (time.perf_counter() - started) * 1000.0

    return {
        "schema": SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "ZERO_REAL_FUNDS_PURE_SIMULATION",
        "authority": {
            "paper_simulation": True,
            "real_trade": False,
            "wallet": False,
            "signing": False,
            "real_order": False,
            "broadcast": False,
        },
        "technical": technical,
        "liquidity": liquidity,
        "edge": edge,
        "sizing": sizing,
        "fill": fill,
        "portfolio": portfolio,
        "latency_ms": timings,
    }


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PaperCoreError(f"{path}:NOT_OBJECT")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_cycle(load_json(args.input), load_json(args.config))
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temp = args.output.with_name(args.output.name + ".tmp")
        temp.write_text(text, encoding="utf-8")
        temp.replace(args.output)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
ERA63_ENGINE
chmod 0755 tools/era63_paper_trading_core_v1.py

cat >tests/test_era63b_paper_trading_core_v1.py <<'ERA63_TEST'
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
ERA63_TEST
chmod 0755 tests/test_era63b_paper_trading_core_v1.py

python3 <<'PY'
import json
from pathlib import Path

root = Path("/root/tokenoskobi_clean_v1")
candles = []
price = 100.0
for index in range(40):
    open_price = price
    close_price = price + 0.45
    candles.append(
        {
            "timestamp": 1700000000 + index * 60,
            "open": open_price,
            "high": close_price + 0.20,
            "low": open_price - 0.20,
            "close": close_price,
            "volume": 1000 + index,
        }
    )
    price = close_price

payload = {
    "equity_usd": 10000.0,
    "candles": candles,
    "market": {
        "quote_depth_usd": 100000.0,
        "spread_bps": 8.0,
        "market_age_sec": 5.0,
        "source": "ERA63B_LOCAL_FIXTURE",
    },
    "mark_price": price * 1.002,
}
path = root / "data/replay/era63b_paper_core_fixture_v1.json"
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

python3 -m py_compile tools/era63_paper_trading_core_v1.py
python3 tests/test_era63b_paper_trading_core_v1.py

python3 tools/era63_paper_trading_core_v1.py \
  --input data/replay/era63b_paper_core_fixture_v1.json \
  --config config/era63_paper_trading_core_v1.json \
  --output data/replay/era63b_paper_core_sample_result_v1.json

python3 <<'PY'
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
NOW = datetime.now(timezone.utc).isoformat()
BASE_HEAD = __import__("subprocess").check_output(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
).strip()
NEXT = "ERA63C_END_TO_END_REPLAY_AND_COST_VALIDATION"
STAGE = "ERA63B_ACCELERATED_PAPER_TRADING_CORE_BUILD"
STATUS = "LOCAL_CORE_BUILD_VERIFIED"

def load(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))

def save(relative: str, value: Any) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)

def sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()

def write(relative: str, text: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")

def upsert(relative: str, marker: str, body: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    start = f"<!-- {marker}_START -->"
    end = f"<!-- {marker}_END -->"
    block = f"{start}\n{body.rstrip()}\n{end}"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pattern.search(text):
        text = pattern.sub(block, text, count=1)
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8")

result = load("data/replay/era63b_paper_core_sample_result_v1.json")
assert result["mode"] == "ZERO_REAL_FUNDS_PURE_SIMULATION"
assert result["fill"]["status"] == "SIMULATED_FILLED"
assert result["edge"]["action"] == "BUY"
assert result["authority"] == {
    "paper_simulation": True,
    "real_trade": False,
    "wallet": False,
    "signing": False,
    "real_order": False,
    "broadcast": False,
}

files = {
    "config": "config/era63_paper_trading_core_v1.json",
    "engine": "tools/era63_paper_trading_core_v1.py",
    "tests": "tests/test_era63b_paper_trading_core_v1.py",
    "fixture": "data/replay/era63b_paper_core_fixture_v1.json",
    "sample_result": "data/replay/era63b_paper_core_sample_result_v1.json",
}
artifact = {
    "schema": "tokenoskobi.era63b.paper_core_build.v1",
    "era": "ERA63",
    "stage": STAGE,
    "status": STATUS,
    "built_at_utc": NOW,
    "baseline_head": BASE_HEAD,
    "files": files,
    "sha256": {name: sha(path) for name, path in files.items()},
    "verification": {
        "syntax": "PASS",
        "unit_tests": "13/13_PASS",
        "cli_fixture": "PASS",
        "sample_action": result["edge"]["action"],
        "sample_fill": result["fill"]["status"],
        "sample_total_latency_ms": result["latency_ms"]["total_ms"],
    },
    "capabilities_built": [
        "MARKET_DATA_VALIDATION_AND_LIQUIDITY_GATE",
        "TECHNICAL_ANALYSIS_RUNTIME",
        "OPPORTUNITY_AND_NET_EDGE_ENGINE",
        "POSITION_SIZING_AND_RISK_ENVELOPE",
        "PAPER_ORDER_AND_FILL_SIMULATION",
        "FEE_SLIPPAGE_MEV_GAS_COST_MODEL",
        "PORTFOLIO_PNL_AND_DRAWDOWN",
        "END_TO_END_STAGE_LATENCY",
    ],
    "authority": {
        "paper_calculation": True,
        "paper_runtime_enabled": False,
        "unattended_runtime_enabled": False,
        "real_trade": False,
        "wallet": False,
        "signing": False,
        "real_order": False,
        "broadcast": False,
    },
    "production_binding": False,
    "database_mutation": False,
    "service_mutation": False,
    "timer_mutation": False,
    "network_access": False,
    "next_safe_step": NEXT,
}
save("data/control/era63b_accelerated_paper_trading_core_build_v1.json", artifact)

runtime = load("PROJECT_RUNTIME.json")
runtime.update(
    {
        "current_version": "V4",
        "current_era": "ERA63",
        "current_era_title": "Accelerated Paper Trading Core",
        "current_stage": STAGE,
        "current_status": STATUS,
        "last_completed": STAGE,
        "last_result": "ERA63B_CORE_BUILD_13_OF_13_PASS",
        "next_safe_step": NEXT,
        "updated_at_utc": NOW,
        "project_status": "V4_ERA63_ACTIVE",
        "status": "ACTIVE",
    }
)
work = runtime.setdefault("work_unit", {})
completed = work.setdefault("completed_substeps", [])
for value in (
    "ERA63A_ACCELERATED_PAPER_TRADING_GAP_AUDIT",
    STAGE,
):
    if value not in completed:
        completed.append(value)
work.update(
    {
        "id": "ERA63_ACCELERATED_PAPER_TRADING_CORE",
        "status": STATUS,
        "next_substep": NEXT,
        "paper_trade_currently": "DISABLED_PENDING_ERA63C_VALIDATION",
        "live_trade": "DISABLED",
        "wallet_authority": 0,
        "signing_authority": 0,
        "real_order_create_authority": 0,
    }
)
runtime["era63b_core_build"] = artifact
runtime["open_risks"] = [
    "ERA63C_REQUIRED:END_TO_END_REPLAY",
    "ERA63C_REQUIRED:COST_MODEL_BOUNDARY_VALIDATION",
    "ERA63C_REQUIRED:PAPER_AUTHORITY_SPLIT_VALIDATION",
    "ERA63D_REQUIRED:UNATTENDED_RUNTIME_BINDING",
]
pointer = runtime.setdefault("canonical_runtime_pointer", {})
pointer.update(
    {
        "current_era": "ERA63",
        "current_stage": STAGE,
        "era63b_core_build_verified": True,
        "paper_runtime_enabled": False,
        "next_safe_step": NEXT,
    }
)
save("PROJECT_RUNTIME.json", runtime)

machine = load("data/control/latest_tk_machine_state.json")
machine.update(
    {
        "current_version": "V4",
        "current_era": "ERA63",
        "current_stage": STAGE,
        "current_status": STATUS,
        "last_completed": STAGE,
        "last_result": "ERA63B_CORE_BUILD_13_OF_13_PASS",
        "next_safe_step": NEXT,
        "updated_at_utc": NOW,
        "paper_trade_currently": "DISABLED_PENDING_ERA63C_VALIDATION",
        "era63b_build_artifact": "data/control/era63b_accelerated_paper_trading_core_build_v1.json",
    }
)
save("data/control/latest_tk_machine_state.json", machine)

roadmap = load("data/tokenoskobi_v1_v8_master_era_roadmap.json")
era63 = None
for version in roadmap.get("versions", []):
    if version.get("id") != "V4":
        continue
    for child in version.get("children", []):
        if child.get("id") == "ERA63":
            era63 = child
            break
assert isinstance(era63, dict)
era63.update(
    {
        "status": STATUS,
        "active_stage": STAGE,
        "paper_core_build_verified": True,
        "paper_runtime_enabled": False,
        "build_artifact": "data/control/era63b_accelerated_paper_trading_core_build_v1.json",
        "core_engine": "tools/era63_paper_trading_core_v1.py",
        "core_config": "config/era63_paper_trading_core_v1.json",
        "core_tests": "tests/test_era63b_paper_trading_core_v1.py",
        "next_safe_step": NEXT,
    }
)
substeps = era63.setdefault("substeps", {})
substeps["ERA63A"] = "REAL_GAP_AUDIT_COMPLETED"
substeps["ERA63B"] = "MINIMUM_PAPER_CORE_BUILD_COMPLETED_13_OF_13"
substeps["ERA63C"] = "END_TO_END_REPLAY_AND_COST_VALIDATION_NEXT"
direction = roadmap.setdefault("current_direction", {})
direction.update(
    {
        "current_era": "ERA63",
        "current_stage": STAGE,
        "current_status": STATUS,
        "next_safe_step": NEXT,
        "updated_at_utc": NOW,
    }
)
save("data/tokenoskobi_v1_v8_master_era_roadmap.json", roadmap)

history = load("PROJECT_HISTORY.json")
events = history.setdefault("events", [])
event_id = "ERA63B_ACCELERATED_PAPER_TRADING_CORE_BUILD"
events[:] = [
    item for item in events
    if not (isinstance(item, dict) and item.get("event_id") == event_id)
]
events.append(
    {
        "event_id": event_id,
        "event": "LOCAL_CORE_BUILD_AND_VERIFICATION",
        "era": "ERA63",
        "status": STATUS,
        "tests": "13/13_PASS",
        "artifact": "data/control/era63b_accelerated_paper_trading_core_build_v1.json",
        "paper_runtime_enabled": False,
        "real_financial_authority": 0,
        "next_safe_step": NEXT,
        "timestamp_utc": NOW,
    }
)
history["updated_at_utc"] = NOW
save("PROJECT_HISTORY.json", history)

roadmap_md = (ROOT / "03_ROADMAP.md").read_text(encoding="utf-8")
roadmap_md = roadmap_md.replace(
    "CURRENT_STAGE=ERA63A_ACCELERATED_PAPER_TRADING_GAP_AUDIT",
    f"CURRENT_STAGE={STAGE}",
)
roadmap_md = roadmap_md.replace(
    "ERA63_STATUS=OPEN_GAP_AUDIT_COMPLETED",
    f"ERA63_STATUS={STATUS}",
)
roadmap_md = roadmap_md.replace(
    "STATUS=OPEN_GAP_AUDIT_COMPLETED",
    f"STATUS={STATUS}",
)
roadmap_md = roadmap_md.replace(
    "NEXT_SAFE_STEP=ERA63B_ACCELERATED_PAPER_TRADING_CORE_BUILD",
    f"NEXT_SAFE_STEP={NEXT}",
)
roadmap_md = roadmap_md.replace(
    "ERA63B=MINIMUM_PAPER_CORE_BUILD=NEXT",
    "ERA63B=MINIMUM_PAPER_CORE_BUILD=COMPLETED_13_OF_13",
)
roadmap_md = roadmap_md.replace(
    "ERA63C=END_TO_END_REPLAY_AND_COST_VALIDATION",
    "ERA63C=END_TO_END_REPLAY_AND_COST_VALIDATION=NEXT",
)
(ROOT / "03_ROADMAP.md").write_text(roadmap_md, encoding="utf-8")

master_state = f"""# 06 PROJECT MASTER STATE - TOKENOSKOBI

## CURRENT POSITION

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_TITLE=Accelerated Paper Trading Core
CURRENT_STAGE={STAGE}
CURRENT_STATUS={STATUS}
LAST_CLOSED_ERA=ERA62
NEXT_SAFE_STEP={NEXT}

## ERA63B BUILD

CORE_ENGINE=tools/era63_paper_trading_core_v1.py
CORE_CONFIG=config/era63_paper_trading_core_v1.json
CORE_TEST=tests/test_era63b_paper_trading_core_v1.py
BUILD_ARTIFACT=data/control/era63b_accelerated_paper_trading_core_build_v1.json
TESTS=13/13_PASS

BUILT_CAPABILITIES:

- Market/candle validation and liquidity gate
- Technical indicators: SMA, RSI, ATR, volatility
- Gross and cost-adjusted edge
- Bounded position sizing
- Simulated paper fill
- Fee, spread, slippage, MEV and gas model
- Portfolio P&L and drawdown
- Stage and total latency

## AUTHORITY STATE

PAPER_CALCULATION=true
PAPER_RUNTIME=DISABLED_PENDING_ERA63C_VALIDATION
UNATTENDED_RUNTIME=false
LIVE_TRADE=DISABLED
REAL_WALLET=false
REAL_SIGNING=false
REAL_ORDER=false
REAL_BROADCAST=false
"""
write("06_PROJECT_MASTER_STATE.md", master_state)

handoff = f"""# 07 PROJECT HANDOFF - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={STAGE}
CURRENT_STATUS={STATUS}
NEXT_SAFE_STEP={NEXT}

ERA63A gap audit is complete.

ERA63B built one reusable deterministic paper core covering all eight mandatory capability gaps. The build passed 13/13 tests and one CLI fixture.

Paper calculation exists. Persistent or unattended paper runtime is not enabled yet.

ERA63C must validate:

1. end-to-end deterministic replay,
2. fee/slippage/MEV/gas boundary behavior,
3. paper-versus-real authority separation,
4. extreme volatility, stale data and low-liquidity blocks,
5. accounting and latency limits.

No real wallet, signing, order or broadcast authority exists.
"""
write("07_PROJECT_HANDOFF.md", handoff)

report = f"""# ERA63B PAPER-TRADING CORE BUILD

STATUS={STATUS}
TESTS=13/13_PASS
NEXT_SAFE_STEP={NEXT}

## Files

- `config/era63_paper_trading_core_v1.json`
- `tools/era63_paper_trading_core_v1.py`
- `tests/test_era63b_paper_trading_core_v1.py`
- `data/replay/era63b_paper_core_fixture_v1.json`
- `data/replay/era63b_paper_core_sample_result_v1.json`
- `data/control/era63b_accelerated_paper_trading_core_build_v1.json`

## Boundaries

- Zero real funds
- No network call
- No database mutation
- No service or timer mutation
- No wallet
- No signing
- No real order
- No broadcast
- Paper runtime remains disabled until ERA63C validation
"""
write("reports/LATEST_ERA63_PAPER_TRADING_CORE_BUILD.md", report)

write(
    "reports/LATEST_TK_AI_HANDOFF.md",
    f"""# TOKENOSKOBI LATEST AI HANDOFF

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={STAGE}
CURRENT_STATUS={STATUS}
LAST_COMPLETED={STAGE}
NEXT_SAFE_STEP={NEXT}

BUILD_ARTIFACT=data/control/era63b_accelerated_paper_trading_core_build_v1.json
BUILD_REPORT=reports/LATEST_ERA63_PAPER_TRADING_CORE_BUILD.md
TESTS=13/13_PASS
PAPER_RUNTIME=DISABLED_PENDING_ERA63C_VALIDATION
LIVE_TRADE=DISABLED
""",
)

upsert(
    "04_ALMANAC.md",
    "ERA63B_PAPER_CORE_BUILD",
    f"""## ERA63B PAPER-TRADING CORE BUILD

- Status: `{STATUS}`
- Engine: `tools/era63_paper_trading_core_v1.py`
- Tests: `13/13_PASS`
- Runtime binding: `NOT_ENABLED`
- Real financial authority: `0`
- Next: `{NEXT}`
- UTC: `{NOW}`""",
)

print("ERA63B_CANONICAL_SYNC=PASS")
PY

python3 -m json.tool config/era63_paper_trading_core_v1.json >/dev/null
python3 -m json.tool data/replay/era63b_paper_core_fixture_v1.json >/dev/null
python3 -m json.tool data/replay/era63b_paper_core_sample_result_v1.json >/dev/null
python3 -m json.tool data/control/era63b_accelerated_paper_trading_core_build_v1.json >/dev/null
python3 -m json.tool PROJECT_RUNTIME.json >/dev/null
python3 -m json.tool PROJECT_HISTORY.json >/dev/null
python3 -m json.tool data/tokenoskobi_v1_v8_master_era_roadmap.json >/dev/null

git diff --check
git add -f -- "${ALL_FILES[@]}"
git diff --cached --check
! git diff --cached --quiet

git commit -m "ERA63B: build accelerated paper trading core"
COMMITTED=1
HEAD="$(git rev-parse HEAD)"
git push origin main
git fetch origin main --quiet

[[ "$(git rev-parse origin/main)" == "$HEAD" ]]
[[ "$(git ls-remote origin refs/heads/main | awk '{print $1}')" == "$HEAD" ]]
[[ -z "$(git status --porcelain=v1)" ]]

trap - ERR

echo "ERA63B_STATUS=LOCAL_CORE_BUILD_VERIFIED"
echo "TESTS=13/13_PASS"
echo "PAPER_RUNTIME=DISABLED_PENDING_ERA63C_VALIDATION"
echo "LIVE_TRADE=DISABLED"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=ERA63C_END_TO_END_REPLAY_AND_COST_VALIDATION"
