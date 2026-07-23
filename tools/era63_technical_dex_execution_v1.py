#!/usr/bin/env python3
"""ERA63C technical analysis and DEX execution-risk engine.

Pure deterministic computation:
- multi-timeframe technical analysis,
- constant-product AMM route simulation,
- dynamic MEV/sandwich probability and expected-loss estimation,
- token tax, gas, route, price-impact and slippage controls,
- bounded paper sizing and simulated fill.

No network, wallet, signing, exchange, database, service or timer access.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "tokenoskobi.era63c.technical_dex_execution.v1"


class Era63CError(ValueError):
    pass


def finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise Era63CError(f"{name}:NOT_NUMERIC") from exc
    if not math.isfinite(number):
        raise Era63CError(f"{name}:NOT_FINITE")
    return number


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        raise Era63CError("MEAN_EMPTY")
    return sum(items) / len(items)


def stdev(values: Iterable[float]) -> float:
    items = list(values)
    if len(items) < 2:
        return 0.0
    avg = mean(items)
    return math.sqrt(sum((item - avg) ** 2 for item in items) / len(items))


def validate_config(config: dict[str, Any]) -> None:
    if not isinstance(config, dict):
        raise Era63CError("CONFIG_NOT_OBJECT")
    positive = (
        "ema_fast",
        "ema_slow",
        "ema_long",
        "rsi_window",
        "atr_window",
        "adx_window",
        "bollinger_window",
        "bollinger_stddev",
        "min_net_edge_bps",
        "max_gross_edge_bps",
        "risk_fraction",
        "max_position_fraction",
        "atr_stop_multiple",
        "min_stop_bps",
        "min_notional_usd",
        "probe_notional_usd",
        "max_market_age_sec",
        "max_price_impact_bps",
        "max_expected_sandwich_loss_bps",
        "max_round_trip_token_tax_bps",
        "max_slippage_tolerance_bps",
        "max_route_hops",
        "max_participation_fraction",
        "max_split_count",
        "other_mev_max_bps",
    )
    for key in positive:
        if finite(config.get(key), f"config.{key}") <= 0:
            raise Era63CError(f"config.{key}:MUST_BE_POSITIVE")
    if int(config["ema_fast"]) >= int(config["ema_slow"]):
        raise Era63CError("EMA_FAST_MUST_BE_LT_EMA_SLOW")
    if int(config["ema_slow"]) >= int(config["ema_long"]):
        raise Era63CError("EMA_SLOW_MUST_BE_LT_EMA_LONG")
    if finite(config["risk_fraction"], "risk_fraction") > 0.1:
        raise Era63CError("RISK_FRACTION_TOO_HIGH")
    if finite(config["max_position_fraction"], "max_position_fraction") > 1.0:
        raise Era63CError("MAX_POSITION_FRACTION_TOO_HIGH")
    if finite(config.get("max_sandwich_probability"), "max_sandwich_probability") > 1.0:
        raise Era63CError("MAX_SANDWICH_PROBABILITY_GT_ONE")
    if config.get("paper_runtime_enabled") is not False:
        raise Era63CError("PAPER_RUNTIME_MUST_REMAIN_DISABLED")
    for key in (
        "unattended_runtime_enabled",
        "real_trade_enabled",
        "wallet_enabled",
        "signing_enabled",
        "real_order_broadcast_enabled",
    ):
        if config.get(key) is not False:
            raise Era63CError(f"{key}:MUST_BE_FALSE")


def validate_candles(candles: Any, minimum: int) -> list[dict[str, float]]:
    if not isinstance(candles, list) or len(candles) < minimum:
        raise Era63CError(f"CANDLES_MINIMUM:{minimum}")
    normalized: list[dict[str, float]] = []
    previous_ts = -1.0
    for index, row in enumerate(candles):
        if not isinstance(row, dict):
            raise Era63CError(f"CANDLE_{index}:NOT_OBJECT")
        item = {
            "timestamp": finite(row.get("timestamp"), f"candle.{index}.timestamp"),
            "open": finite(row.get("open"), f"candle.{index}.open"),
            "high": finite(row.get("high"), f"candle.{index}.high"),
            "low": finite(row.get("low"), f"candle.{index}.low"),
            "close": finite(row.get("close"), f"candle.{index}.close"),
            "volume": finite(row.get("volume", 0.0), f"candle.{index}.volume"),
        }
        if min(item["open"], item["high"], item["low"], item["close"]) <= 0:
            raise Era63CError(f"CANDLE_{index}:NONPOSITIVE_PRICE")
        if item["volume"] < 0:
            raise Era63CError(f"CANDLE_{index}:NEGATIVE_VOLUME")
        if item["high"] < max(item["open"], item["close"]):
            raise Era63CError(f"CANDLE_{index}:HIGH_INVALID")
        if item["low"] > min(item["open"], item["close"]):
            raise Era63CError(f"CANDLE_{index}:LOW_INVALID")
        if item["timestamp"] <= previous_ts:
            raise Era63CError(f"CANDLE_{index}:TIMESTAMP_NOT_INCREASING")
        previous_ts = item["timestamp"]
        normalized.append(item)
    return normalized


def ema_series(values: list[float], window: int) -> list[float]:
    if len(values) < window:
        raise Era63CError(f"EMA_INSUFFICIENT_DATA:{window}")
    alpha = 2.0 / (window + 1.0)
    current = mean(values[:window])
    result = [current]
    for value in values[window:]:
        current = alpha * value + (1.0 - alpha) * current
        result.append(current)
    return result


def ema(values: list[float], window: int) -> float:
    return ema_series(values, window)[-1]


def rsi(values: list[float], window: int) -> float:
    if len(values) <= window:
        raise Era63CError("RSI_INSUFFICIENT_DATA")
    changes = [values[i] - values[i - 1] for i in range(len(values) - window, len(values))]
    gains = mean(max(change, 0.0) for change in changes)
    losses = mean(max(-change, 0.0) for change in changes)
    if losses == 0:
        return 100.0 if gains > 0 else 50.0
    relative = gains / losses
    return 100.0 - 100.0 / (1.0 + relative)


def atr(candles: list[dict[str, float]], window: int) -> float:
    if len(candles) <= window:
        raise Era63CError("ATR_INSUFFICIENT_DATA")
    ranges: list[float] = []
    for index in range(len(candles) - window, len(candles)):
        current = candles[index]
        previous_close = candles[index - 1]["close"]
        ranges.append(
            max(
                current["high"] - current["low"],
                abs(current["high"] - previous_close),
                abs(current["low"] - previous_close),
            )
        )
    return mean(ranges)


def adx(candles: list[dict[str, float]], window: int) -> float:
    if len(candles) <= window + 1:
        raise Era63CError("ADX_INSUFFICIENT_DATA")
    trs: list[float] = []
    plus_dm: list[float] = []
    minus_dm: list[float] = []
    start = len(candles) - window
    for index in range(start, len(candles)):
        current = candles[index]
        previous = candles[index - 1]
        up = current["high"] - previous["high"]
        down = previous["low"] - current["low"]
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)
        trs.append(
            max(
                current["high"] - current["low"],
                abs(current["high"] - previous["close"]),
                abs(current["low"] - previous["close"]),
            )
        )
    tr_avg = mean(trs)
    if tr_avg <= 0:
        return 0.0
    plus_di = 100.0 * mean(plus_dm) / tr_avg
    minus_di = 100.0 * mean(minus_dm) / tr_avg
    denominator = plus_di + minus_di
    if denominator <= 0:
        return 0.0
    return 100.0 * abs(plus_di - minus_di) / denominator


def obv(candles: list[dict[str, float]]) -> list[float]:
    values = [0.0]
    for index in range(1, len(candles)):
        if candles[index]["close"] > candles[index - 1]["close"]:
            values.append(values[-1] + candles[index]["volume"])
        elif candles[index]["close"] < candles[index - 1]["close"]:
            values.append(values[-1] - candles[index]["volume"])
        else:
            values.append(values[-1])
    return values


def technical_frame(candles: list[dict[str, float]], config: dict[str, Any]) -> dict[str, float]:
    closes = [row["close"] for row in candles]
    volumes = [row["volume"] for row in candles]
    price = closes[-1]
    fast = ema(closes, int(config["ema_fast"]))
    slow = ema(closes, int(config["ema_slow"]))
    long_value = ema(closes, int(config["ema_long"]))
    rsi_value = rsi(closes, int(config["rsi_window"]))
    atr_value = atr(candles, int(config["atr_window"]))
    adx_value = adx(candles, int(config["adx_window"]))

    macd_fast = ema_series(closes, 12)
    macd_slow = ema_series(closes, 26)
    aligned = min(len(macd_fast), len(macd_slow))
    macd_values = [
        macd_fast[-aligned + index] - macd_slow[-aligned + index]
        for index in range(aligned)
    ]
    macd_line = macd_values[-1]
    signal_window = min(9, len(macd_values))
    signal_line = ema(macd_values, signal_window)
    macd_histogram = macd_line - signal_line

    bb_window = int(config["bollinger_window"])
    recent = closes[-bb_window:]
    bb_mid = mean(recent)
    bb_sigma = stdev(recent)
    bb_upper = bb_mid + float(config["bollinger_stddev"]) * bb_sigma
    bb_lower = bb_mid - float(config["bollinger_stddev"]) * bb_sigma
    bb_width = max(bb_upper - bb_lower, price * 1e-9)
    bb_position = clamp((price - bb_lower) / bb_width, 0.0, 1.0)

    volume_window = min(20, len(volumes))
    volume_recent = volumes[-volume_window:]
    volume_sigma = stdev(volume_recent)
    volume_z = 0.0 if volume_sigma == 0 else (volumes[-1] - mean(volume_recent)) / volume_sigma

    obv_values = obv(candles)
    obv_window = min(10, len(obv_values) - 1)
    obv_base = max(1.0, sum(abs(value) for value in volumes[-obv_window:]))
    obv_slope = (obv_values[-1] - obv_values[-1 - obv_window]) / obv_base

    support_window = min(20, len(candles))
    support = min(row["low"] for row in candles[-support_window:])
    resistance = max(row["high"] for row in candles[-support_window:])

    trend = clamp(((fast / slow) - 1.0) * 250.0, -1.0, 1.0)
    long_trend = clamp(((slow / long_value) - 1.0) * 180.0, -1.0, 1.0)
    momentum = clamp((rsi_value - 50.0) / 25.0, -1.0, 1.0)
    macd_score = clamp(macd_histogram / max(price * 0.002, 1e-12), -1.0, 1.0)
    breakout = clamp((bb_position - 0.5) * 2.0, -1.0, 1.0)
    volume_score = clamp(volume_z / 3.0, -1.0, 1.0)
    obv_score = clamp(obv_slope * 5.0, -1.0, 1.0)
    directional = (
        0.25 * trend
        + 0.15 * long_trend
        + 0.20 * momentum
        + 0.15 * macd_score
        + 0.10 * breakout
        + 0.075 * volume_score
        + 0.075 * obv_score
    )
    confidence = clamp(0.35 + 0.45 * clamp(adx_value / 50.0) + 0.20 * abs(directional))

    return {
        "price": price,
        "ema_fast": fast,
        "ema_slow": slow,
        "ema_long": long_value,
        "rsi": rsi_value,
        "atr": atr_value,
        "atr_bps": atr_value / price * 10000.0,
        "adx": adx_value,
        "macd": macd_line,
        "macd_signal": signal_line,
        "macd_histogram": macd_histogram,
        "bollinger_mid": bb_mid,
        "bollinger_upper": bb_upper,
        "bollinger_lower": bb_lower,
        "bollinger_position": bb_position,
        "volume_zscore": volume_z,
        "obv_slope": obv_slope,
        "support": support,
        "resistance": resistance,
        "directional_score": directional,
        "confidence": confidence,
    }


def technical_analysis(payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    raw_frames = payload.get("timeframes")
    if raw_frames is None:
        raw_frames = {"primary": payload.get("candles")}
    if not isinstance(raw_frames, dict) or not raw_frames:
        raise Era63CError("TIMEFRAMES_NOT_OBJECT_OR_EMPTY")

    minimum = max(
        int(config["ema_long"]) + 10,
        int(config["rsi_window"]) + 2,
        int(config["atr_window"]) + 2,
        int(config["adx_window"]) + 2,
        int(config["bollinger_window"]) + 2,
        40,
    )
    frames: dict[str, dict[str, float]] = {}
    for name, candles in sorted(raw_frames.items()):
        frames[str(name)] = technical_frame(validate_candles(candles, minimum), config)

    weights_config = config.get("timeframe_weights") or {}
    raw_weights: dict[str, float] = {}
    for name in frames:
        raw_weights[name] = max(0.0, float(weights_config.get(name, 1.0)))
    if sum(raw_weights.values()) <= 0:
        raw_weights = {name: 1.0 for name in frames}
    weight_total = sum(raw_weights.values())
    weights = {name: value / weight_total for name, value in raw_weights.items()}

    score = sum(frames[name]["directional_score"] * weights[name] for name in frames)
    confidence = sum(frames[name]["confidence"] * weights[name] for name in frames)
    positive_weight = sum(weights[name] for name in frames if frames[name]["directional_score"] > 0.1)
    negative_weight = sum(weights[name] for name in frames if frames[name]["directional_score"] < -0.1)
    consensus = max(positive_weight, negative_weight)
    confidence = clamp(confidence * (0.5 + 0.5 * consensus))
    gross_edge_bps = max(
        0.0,
        score * confidence * float(config["max_gross_edge_bps"]),
    )

    primary_name = str(config.get("primary_timeframe") or "")
    if primary_name not in frames:
        primary_name = max(weights, key=weights.get)
    primary = frames[primary_name]

    return {
        "frames": frames,
        "weights": weights,
        "primary_timeframe": primary_name,
        "directional_score": score,
        "confidence": confidence,
        "consensus": consensus,
        "gross_edge_bps": gross_edge_bps,
        "price": primary["price"],
        "atr": primary["atr"],
        "atr_bps": primary["atr_bps"],
    }


def cpmm_amount_out(amount_in: float, reserve_in: float, reserve_out: float, fee_bps: float) -> float:
    amount = finite(amount_in, "amount_in")
    x = finite(reserve_in, "reserve_in")
    y = finite(reserve_out, "reserve_out")
    fee = finite(fee_bps, "fee_bps")
    if amount <= 0 or x <= 0 or y <= 0:
        raise Era63CError("CPMM_INPUT_OR_RESERVE_NONPOSITIVE")
    if fee < 0 or fee >= 10000:
        raise Era63CError("CPMM_FEE_INVALID")
    amount_after_fee = amount * (1.0 - fee / 10000.0)
    return y * amount_after_fee / (x + amount_after_fee)


def validate_hop(hop: Any, index: int) -> dict[str, Any]:
    if not isinstance(hop, dict):
        raise Era63CError(f"ROUTE_HOP_{index}:NOT_OBJECT")
    normalized = {
        "pool_id": str(hop.get("pool_id") or f"pool_{index}"),
        "reserve_in": finite(hop.get("reserve_in"), f"hop.{index}.reserve_in"),
        "reserve_out": finite(hop.get("reserve_out"), f"hop.{index}.reserve_out"),
        "fee_bps": finite(hop.get("fee_bps", 30.0), f"hop.{index}.fee_bps"),
        "token_out_price_usd": finite(
            hop.get("token_out_price_usd", 1.0),
            f"hop.{index}.token_out_price_usd",
        ),
    }
    if normalized["reserve_in"] <= 0 or normalized["reserve_out"] <= 0:
        raise Era63CError(f"ROUTE_HOP_{index}:RESERVE_NONPOSITIVE")
    if normalized["token_out_price_usd"] <= 0:
        raise Era63CError(f"ROUTE_HOP_{index}:OUTPUT_PRICE_NONPOSITIVE")
    return normalized


def route_quote(amount_in: float, hops: list[dict[str, Any]]) -> dict[str, Any]:
    if not hops:
        raise Era63CError("ROUTE_EMPTY")
    amount = finite(amount_in, "route.amount_in")
    ideal_no_fee = amount
    ideal_after_fee = amount
    outputs: list[dict[str, float | str]] = []
    fee_survival = 1.0
    for index, hop in enumerate(hops):
        ratio = hop["reserve_out"] / hop["reserve_in"]
        fee_fraction = hop["fee_bps"] / 10000.0
        ideal_no_fee *= ratio
        ideal_after_fee *= ratio * (1.0 - fee_fraction)
        output = cpmm_amount_out(
            amount,
            hop["reserve_in"],
            hop["reserve_out"],
            hop["fee_bps"],
        )
        outputs.append(
            {
                "pool_id": hop["pool_id"],
                "amount_in": amount,
                "amount_out": output,
                "participation_fraction": amount / hop["reserve_in"],
            }
        )
        amount = output
        fee_survival *= 1.0 - fee_fraction
    price_impact_bps = max(
        0.0,
        (1.0 - amount / max(ideal_after_fee, 1e-18)) * 10000.0,
    )
    return {
        "amount_in": float(amount_in),
        "amount_out": amount,
        "ideal_output_no_fee": ideal_no_fee,
        "ideal_output_after_fee": ideal_after_fee,
        "dex_fee_bps": (1.0 - fee_survival) * 10000.0,
        "price_impact_bps": price_impact_bps,
        "hops": outputs,
        "route_hops": len(hops),
        "max_participation_fraction": max(
            float(item["participation_fraction"]) for item in outputs
        ),
    }


def sandwich_on_hop(
    victim_amount_in: float,
    hop: dict[str, Any],
    factors: list[float],
) -> dict[str, Any]:
    normal_out = cpmm_amount_out(
        victim_amount_in,
        hop["reserve_in"],
        hop["reserve_out"],
        hop["fee_bps"],
    )
    best = {
        "attacker_amount_in": 0.0,
        "attacker_profit_input": 0.0,
        "attacker_profit_bps": 0.0,
        "victim_normal_out": normal_out,
        "victim_attacked_out": normal_out,
        "victim_loss_bps": 0.0,
    }
    max_attack = hop["reserve_in"] * 0.05
    for factor in factors:
        attacker_in = min(victim_amount_in * factor, max_attack)
        if attacker_in <= 0:
            continue
        attacker_out = cpmm_amount_out(
            attacker_in,
            hop["reserve_in"],
            hop["reserve_out"],
            hop["fee_bps"],
        )
        reserve_in_1 = hop["reserve_in"] + attacker_in
        reserve_out_1 = hop["reserve_out"] - attacker_out
        victim_attacked = cpmm_amount_out(
            victim_amount_in,
            reserve_in_1,
            reserve_out_1,
            hop["fee_bps"],
        )
        reserve_in_2 = reserve_in_1 + victim_amount_in
        reserve_out_2 = reserve_out_1 - victim_attacked
        attacker_back = cpmm_amount_out(
            attacker_out,
            reserve_out_2,
            reserve_in_2,
            hop["fee_bps"],
        )
        profit = attacker_back - attacker_in
        victim_loss_bps = max(
            0.0,
            (normal_out - victim_attacked) / max(normal_out, 1e-18) * 10000.0,
        )
        candidate = {
            "attacker_amount_in": attacker_in,
            "attacker_profit_input": profit,
            "attacker_profit_bps": profit / attacker_in * 10000.0,
            "victim_normal_out": normal_out,
            "victim_attacked_out": victim_attacked,
            "victim_loss_bps": victim_loss_bps,
        }
        if profit > 0 and (
            candidate["attacker_profit_input"] > best["attacker_profit_input"]
            or (
                math.isclose(
                    candidate["attacker_profit_input"],
                    best["attacker_profit_input"],
                )
                and candidate["victim_loss_bps"] > best["victim_loss_bps"]
            )
        ):
            best = candidate
    return best


def dynamic_sandwich_probability(
    quote: dict[str, Any],
    dex: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, float]:
    mempool = dex.get("mempool") or {}
    if not isinstance(mempool, dict):
        raise Era63CError("MEMPOOL_NOT_OBJECT")
    public = bool(mempool.get("public", True))
    private_relay = bool(mempool.get("private_relay", False))
    pending_score = clamp(finite(mempool.get("pending_tx_count", 0.0), "pending_tx_count") / 1000.0)
    gas_score = clamp(finite(mempool.get("gas_competition_ratio", 0.0), "gas_competition_ratio"))
    historical = clamp(
        finite(mempool.get("historical_sandwich_rate", 0.0), "historical_sandwich_rate")
    )
    participation_score = clamp(
        quote["max_participation_fraction"]
        / float(config["max_participation_fraction"])
    )
    slippage_score = clamp(
        finite(
            dex.get("slippage_tolerance_bps", 0.0),
            "dex.slippage_tolerance_bps",
        )
        / float(config["max_slippage_tolerance_bps"])
    )
    route_score = clamp((quote["route_hops"] - 1) / max(1.0, float(config["max_route_hops"]) - 1.0))
    probability = (
        0.03
        + 0.26 * participation_score
        + 0.18 * slippage_score
        + 0.18 * historical
        + 0.14 * gas_score
        + 0.11 * pending_score
        + 0.10 * route_score
    )
    if not public:
        probability *= 0.40
    if private_relay:
        probability *= float(config["private_relay_probability_multiplier"])
    probability = clamp(probability, 0.0, 0.99)
    return {
        "probability": probability,
        "participation_score": participation_score,
        "slippage_score": slippage_score,
        "historical_score": historical,
        "gas_score": gas_score,
        "pending_score": pending_score,
        "route_score": route_score,
        "public_mempool": 1.0 if public else 0.0,
        "private_relay": 1.0 if private_relay else 0.0,
    }


def normalize_routes(dex: dict[str, Any]) -> list[dict[str, Any]]:
    routes = dex.get("routes")
    if routes is None:
        route = dex.get("route")
        routes = [{"route_id": "default", "hops": route}]
    if not isinstance(routes, list) or not routes:
        raise Era63CError("DEX_ROUTES_EMPTY")
    normalized: list[dict[str, Any]] = []
    for route_index, route in enumerate(routes):
        if not isinstance(route, dict):
            raise Era63CError(f"ROUTE_{route_index}:NOT_OBJECT")
        hops_raw = route.get("hops")
        if not isinstance(hops_raw, list) or not hops_raw:
            raise Era63CError(f"ROUTE_{route_index}:HOPS_EMPTY")
        normalized.append(
            {
                "route_id": str(route.get("route_id") or f"route_{route_index}"),
                "hops": [
                    validate_hop(hop, index)
                    for index, hop in enumerate(hops_raw)
                ],
            }
        )
    return normalized


def evaluate_route(
    notional_usd: float,
    route: dict[str, Any],
    dex: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    quote = route_quote(notional_usd, route["hops"])
    factors = [
        finite(value, "sandwich_attack_factor")
        for value in config.get("sandwich_attack_factors", [])
    ]
    if not factors:
        raise Era63CError("SANDWICH_FACTORS_EMPTY")

    hop_attacks: list[dict[str, Any]] = []
    victim_input = notional_usd
    combined_survival = 1.0
    for hop in route["hops"]:
        attack = sandwich_on_hop(victim_input, hop, factors)
        attack["pool_id"] = hop["pool_id"]
        hop_attacks.append(attack)
        combined_survival *= 1.0 - clamp(attack["victim_loss_bps"] / 10000.0)
        victim_input = cpmm_amount_out(
            victim_input,
            hop["reserve_in"],
            hop["reserve_out"],
            hop["fee_bps"],
        )
    attack_loss_bps = (1.0 - combined_survival) * 10000.0
    probability_detail = dynamic_sandwich_probability(quote, dex, config)
    expected_sandwich_loss_bps = probability_detail["probability"] * attack_loss_bps

    mempool = dex.get("mempool") or {}
    other_mev_score = clamp(
        0.45 * finite(mempool.get("gas_competition_ratio", 0.0), "gas_competition_ratio")
        + 0.35 * clamp(finite(mempool.get("pending_tx_count", 0.0), "pending_tx_count") / 1000.0)
        + 0.20 * probability_detail["historical_score"]
    )
    if bool(mempool.get("private_relay", False)):
        other_mev_score *= float(config["private_relay_probability_multiplier"])
    expected_other_mev_bps = other_mev_score * float(config["other_mev_max_bps"])

    tax = dex.get("token_tax") or {}
    if not isinstance(tax, dict):
        raise Era63CError("TOKEN_TAX_NOT_OBJECT")
    buy_tax_bps = finite(tax.get("buy_bps", 0.0), "token_tax.buy_bps")
    sell_tax_bps = finite(tax.get("sell_bps", 0.0), "token_tax.sell_bps")
    if buy_tax_bps < 0 or sell_tax_bps < 0:
        raise Era63CError("TOKEN_TAX_NEGATIVE")
    round_trip_tax_bps = buy_tax_bps + sell_tax_bps

    gas_usd = finite(dex.get("gas_usd", 0.0), "dex.gas_usd")
    if gas_usd < 0:
        raise Era63CError("GAS_NEGATIVE")
    gas_bps = gas_usd / notional_usd * 10000.0
    market_age_sec = finite(dex.get("market_age_sec", 0.0), "dex.market_age_sec")
    slippage_tolerance_bps = finite(
        dex.get("slippage_tolerance_bps", 0.0),
        "dex.slippage_tolerance_bps",
    )

    total_cost_bps = (
        quote["dex_fee_bps"]
        + quote["price_impact_bps"]
        + round_trip_tax_bps
        + gas_bps
        + expected_sandwich_loss_bps
        + expected_other_mev_bps
    )
    split_count = max(
        1,
        min(
            int(config["max_split_count"]),
            math.ceil(
                quote["max_participation_fraction"]
                / float(config["max_participation_fraction"])
            ),
        ),
    )

    blocks: list[str] = []
    if market_age_sec > float(config["max_market_age_sec"]):
        blocks.append("DEX_MARKET_DATA_STALE")
    if quote["price_impact_bps"] > float(config["max_price_impact_bps"]):
        blocks.append("PRICE_IMPACT_TOO_HIGH")
    if probability_detail["probability"] > float(config["max_sandwich_probability"]):
        blocks.append("SANDWICH_PROBABILITY_TOO_HIGH")
    if expected_sandwich_loss_bps > float(config["max_expected_sandwich_loss_bps"]):
        blocks.append("EXPECTED_SANDWICH_LOSS_TOO_HIGH")
    if round_trip_tax_bps > float(config["max_round_trip_token_tax_bps"]):
        blocks.append("TOKEN_TAX_TOO_HIGH")
    if slippage_tolerance_bps > float(config["max_slippage_tolerance_bps"]):
        blocks.append("SLIPPAGE_TOLERANCE_TOO_HIGH")
    if quote["route_hops"] > int(config["max_route_hops"]):
        blocks.append("ROUTE_TOO_LONG")
    if quote["max_participation_fraction"] > float(config["absolute_max_participation_fraction"]):
        blocks.append("POOL_PARTICIPATION_TOO_HIGH")

    protections: list[str] = []
    if probability_detail["public_mempool"] == 1.0 and probability_detail["private_relay"] == 0.0:
        protections.append("USE_PRIVATE_OR_PROTECTED_RELAY")
    if split_count > 1:
        protections.append(f"SPLIT_ORDER_INTO_{split_count}_PARTS")
    if slippage_tolerance_bps > float(config["recommended_slippage_bps"]):
        protections.append("REDUCE_SLIPPAGE_TOLERANCE")
    if quote["price_impact_bps"] > float(config["recommended_price_impact_bps"]):
        protections.append("SELECT_DEEPER_ROUTE")
    if round_trip_tax_bps > 0:
        protections.append("ACCOUNT_FOR_BUY_AND_SELL_TOKEN_TAX")

    output_after_buy_tax = quote["amount_out"] * (1.0 - buy_tax_bps / 10000.0)
    output_price_usd = route["hops"][-1]["token_out_price_usd"]
    fill_price_usd = notional_usd / max(output_after_buy_tax, 1e-18)
    reference_price_usd = notional_usd / max(quote["ideal_output_no_fee"], 1e-18)

    risk_score = clamp(
        0.35 * probability_detail["probability"]
        + 0.25 * clamp(quote["price_impact_bps"] / float(config["max_price_impact_bps"]))
        + 0.15 * clamp(expected_other_mev_bps / float(config["other_mev_max_bps"]))
        + 0.15 * clamp(round_trip_tax_bps / float(config["max_round_trip_token_tax_bps"]))
        + 0.10 * clamp(quote["route_hops"] / float(config["max_route_hops"]))
    )

    return {
        "route_id": route["route_id"],
        "status": "ALLOW" if not blocks else "BLOCK",
        "blocks": sorted(set(blocks)),
        "protections": sorted(set(protections)),
        "quote": quote,
        "sandwich": {
            "probability": probability_detail["probability"],
            "probability_components": probability_detail,
            "attack_loss_bps": attack_loss_bps,
            "expected_loss_bps": expected_sandwich_loss_bps,
            "hop_attacks": hop_attacks,
        },
        "mev": {
            "other_mev_score": other_mev_score,
            "expected_other_mev_bps": expected_other_mev_bps,
        },
        "token_tax": {
            "buy_bps": buy_tax_bps,
            "sell_bps": sell_tax_bps,
            "round_trip_bps": round_trip_tax_bps,
        },
        "gas": {
            "gas_usd": gas_usd,
            "gas_bps": gas_bps,
        },
        "slippage_tolerance_bps": slippage_tolerance_bps,
        "market_age_sec": market_age_sec,
        "split_count_recommendation": split_count,
        "total_execution_cost_bps": total_cost_bps,
        "total_execution_cost_usd": notional_usd * total_cost_bps / 10000.0,
        "reference_price_usd": reference_price_usd,
        "fill_price_usd": fill_price_usd,
        "output_units_after_buy_tax": output_after_buy_tax,
        "output_token_price_usd": output_price_usd,
        "risk_score": risk_score,
    }


def evaluate_routes(
    notional_usd: float,
    dex: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(dex, dict):
        raise Era63CError("DEX_NOT_OBJECT")
    routes = normalize_routes(dex)
    evaluations = [
        evaluate_route(notional_usd, route, dex, config)
        for route in routes
    ]
    allowed = [
        item for item in evaluations
        if item["status"] == "ALLOW"
    ]
    pool = allowed or evaluations
    selected = min(
        pool,
        key=lambda item: (
            item["total_execution_cost_bps"],
            item["risk_score"],
            item["route_id"],
        ),
    )
    return {
        "status": "ALLOW" if allowed else "BLOCK",
        "selected_route_id": selected["route_id"],
        "selected": selected,
        "routes": evaluations,
    }


def proposed_position_size(
    equity_usd: float,
    technical: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, float]:
    equity = finite(equity_usd, "equity_usd")
    if equity <= 0:
        raise Era63CError("EQUITY_NONPOSITIVE")
    stop_fraction = max(
        technical["atr_bps"]
        * float(config["atr_stop_multiple"])
        / 10000.0,
        float(config["min_stop_bps"]) / 10000.0,
    )
    risk_budget = equity * float(config["risk_fraction"])
    by_risk = risk_budget / stop_fraction
    cap = equity * float(config["max_position_fraction"])
    notional = min(by_risk, cap)
    return {
        "risk_budget_usd": risk_budget,
        "stop_fraction": stop_fraction,
        "proposed_notional_usd": notional,
    }


def find_safe_size(
    proposed: float,
    gross_edge_bps: float,
    dex: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    notional = proposed
    for _ in range(int(config["max_size_reduction_steps"]) + 1):
        if notional < float(config["min_notional_usd"]):
            break
        execution = evaluate_routes(notional, dex, config)
        selected = execution["selected"]
        net_edge = gross_edge_bps - selected["total_execution_cost_bps"]
        accepted = execution["status"] == "ALLOW" and net_edge >= float(config["min_net_edge_bps"])
        attempts.append(
            {
                "notional_usd": notional,
                "execution_status": execution["status"],
                "selected_route_id": execution["selected_route_id"],
                "total_execution_cost_bps": selected["total_execution_cost_bps"],
                "net_edge_bps": net_edge,
                "accepted": accepted,
            }
        )
        if accepted:
            return {
                "status": "ACCEPTED",
                "notional_usd": notional,
                "net_edge_bps": net_edge,
                "execution": execution,
                "attempts": attempts,
            }
        notional /= 2.0
    return {
        "status": "REJECTED",
        "notional_usd": 0.0,
        "net_edge_bps": gross_edge_bps,
        "execution": attempts[-1] if attempts else None,
        "attempts": attempts,
    }


def simulate_fill(
    decision: str,
    sizing: dict[str, Any],
) -> dict[str, Any]:
    if decision != "BUY" or sizing["status"] != "ACCEPTED":
        return {
            "status": "NO_FILL",
            "side": "NONE",
            "notional_usd": 0.0,
            "units": 0.0,
            "reference_price_usd": 0.0,
            "fill_price_usd": 0.0,
            "selected_route_id": None,
            "costs": {},
        }
    selected = sizing["execution"]["selected"]
    return {
        "status": "SIMULATED_FILLED",
        "side": "BUY",
        "notional_usd": sizing["notional_usd"],
        "units": selected["output_units_after_buy_tax"],
        "reference_price_usd": selected["reference_price_usd"],
        "fill_price_usd": selected["fill_price_usd"],
        "selected_route_id": selected["route_id"],
        "costs": {
            "dex_fee_bps": selected["quote"]["dex_fee_bps"],
            "price_impact_bps": selected["quote"]["price_impact_bps"],
            "expected_sandwich_loss_bps": selected["sandwich"]["expected_loss_bps"],
            "expected_other_mev_bps": selected["mev"]["expected_other_mev_bps"],
            "round_trip_token_tax_bps": selected["token_tax"]["round_trip_bps"],
            "gas_bps": selected["gas"]["gas_bps"],
            "total_bps": selected["total_execution_cost_bps"],
            "total_usd": selected["total_execution_cost_usd"],
        },
    }


def portfolio_outcome(
    equity_usd: float,
    fill: dict[str, Any],
    mark_price_usd: float,
) -> dict[str, float]:
    equity = finite(equity_usd, "equity_usd")
    mark = finite(mark_price_usd, "mark_price_usd")
    if fill["status"] != "SIMULATED_FILLED":
        return {
            "equity_before_usd": equity,
            "equity_after_usd": equity,
            "unrealized_pnl_usd": 0.0,
            "drawdown_fraction": 0.0,
        }
    pnl = fill["units"] * mark - fill["notional_usd"]
    after = equity + pnl
    return {
        "equity_before_usd": equity,
        "equity_after_usd": after,
        "unrealized_pnl_usd": pnl,
        "drawdown_fraction": max(0.0, (equity - after) / equity),
    }


def run_cycle(payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    validate_config(config)
    if not isinstance(payload, dict):
        raise Era63CError("PAYLOAD_NOT_OBJECT")
    timings: dict[str, float] = {}
    started = time.perf_counter()

    stage = time.perf_counter()
    technical = technical_analysis(payload, config)
    timings["technical_ms"] = (time.perf_counter() - stage) * 1000.0

    stage = time.perf_counter()
    probe = evaluate_routes(
        float(config["probe_notional_usd"]),
        payload.get("dex"),
        config,
    )
    probe_cost = probe["selected"]["total_execution_cost_bps"]
    probe_net_edge = technical["gross_edge_bps"] - probe_cost
    timings["probe_execution_ms"] = (time.perf_counter() - stage) * 1000.0

    technical_buy = (
        technical["directional_score"] > float(config["min_directional_score"])
        and technical["consensus"] >= float(config["min_timeframe_consensus"])
        and technical["confidence"] >= float(config["min_technical_confidence"])
    )
    initial_decision = (
        "BUY"
        if technical_buy
        and probe["status"] == "ALLOW"
        and probe_net_edge >= float(config["min_net_edge_bps"])
        else "WAIT"
    )
    blocks: list[str] = []
    if not technical_buy:
        blocks.append("TECHNICAL_CONSENSUS_OR_CONFIDENCE_LOW")
    if probe["status"] != "ALLOW":
        blocks.extend(probe["selected"]["blocks"])
    if probe_net_edge < float(config["min_net_edge_bps"]):
        blocks.append("NET_EDGE_BELOW_MINIMUM")

    stage = time.perf_counter()
    proposed = proposed_position_size(
        payload.get("equity_usd"),
        technical,
        config,
    )
    sizing = (
        find_safe_size(
            proposed["proposed_notional_usd"],
            technical["gross_edge_bps"],
            payload["dex"],
            config,
        )
        if initial_decision == "BUY"
        else {
            "status": "REJECTED",
            "notional_usd": 0.0,
            "net_edge_bps": probe_net_edge,
            "execution": probe,
            "attempts": [],
        }
    )
    decision = "BUY" if initial_decision == "BUY" and sizing["status"] == "ACCEPTED" else "WAIT"
    if initial_decision == "BUY" and sizing["status"] != "ACCEPTED":
        blocks.append("NO_SAFE_POSITION_SIZE")
    fill = simulate_fill(decision, sizing)
    timings["sizing_and_execution_ms"] = (time.perf_counter() - stage) * 1000.0

    stage = time.perf_counter()
    default_mark = technical["price"]
    if fill["status"] == "SIMULATED_FILLED":
        default_mark = fill["fill_price_usd"]
    portfolio = portfolio_outcome(
        payload["equity_usd"],
        fill,
        payload.get("mark_price_usd", default_mark),
    )
    timings["accounting_ms"] = (time.perf_counter() - stage) * 1000.0
    timings["total_ms"] = (time.perf_counter() - started) * 1000.0

    return {
        "schema": SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "ZERO_REAL_FUNDS_PURE_SIMULATION",
        "authority": {
            "paper_simulation": True,
            "paper_order_create": True,
            "paper_position_management": True,
            "real_trade": False,
            "wallet": False,
            "signing": False,
            "real_order": False,
            "broadcast": False,
            "system_may_expand_policy": False,
            "risk_engine_veto": True,
        },
        "technical": technical,
        "execution_probe": probe,
        "edge": {
            "action": decision,
            "gross_edge_bps": technical["gross_edge_bps"],
            "probe_execution_cost_bps": probe_cost,
            "probe_net_edge_bps": probe_net_edge,
            "blocks": sorted(set(blocks)),
        },
        "proposed_sizing": proposed,
        "sizing": sizing,
        "fill": fill,
        "portfolio": portfolio,
        "latency_ms": timings,
    }


def run_matrix(value: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    scenarios = value.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise Era63CError("SCENARIOS_EMPTY")
    results = []
    for item in scenarios:
        if not isinstance(item, dict):
            raise Era63CError("SCENARIO_NOT_OBJECT")
        scenario_id = str(item.get("scenario_id") or "")
        payload = item.get("payload")
        result = run_cycle(payload, config)
        results.append(
            {
                "scenario_id": scenario_id,
                "expected_action": item.get("expected_action"),
                "actual_action": result["edge"]["action"],
                "pass": item.get("expected_action") == result["edge"]["action"],
                "result": result,
            }
        )
    return {
        "schema": "tokenoskobi.era63c.replay_matrix_result.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_count": len(results),
        "pass_count": sum(1 for item in results if item["pass"]),
        "results": results,
    }


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Era63CError(f"{path}:NOT_OBJECT")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--matrix", action="store_true")
    args = parser.parse_args()
    config = load_json(args.config)
    source = load_json(args.input)
    result = run_matrix(source, config) if args.matrix else run_cycle(source, config)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name(args.output.name + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(args.output)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
