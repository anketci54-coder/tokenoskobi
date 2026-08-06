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
