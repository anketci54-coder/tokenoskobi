#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

ROOT="/root/tokenoskobi_clean_v1"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era63c_technical_dex_backup_${STAMP}.tar.gz"
COMMITTED=0

NEW_FILES=(
  "config/era63c_technical_dex_execution_v1.json"
  "tools/era63_technical_dex_execution_v1.py"
  "tests/test_era63c_technical_dex_execution_v1.py"
  "data/replay/era63c_technical_dex_execution_replay_matrix_v1.json"
  "data/replay/era63c_technical_dex_execution_replay_matrix_result_v1.json"
  "data/control/era63c_technical_dex_execution_validation_v1.json"
  "reports/LATEST_ERA63C_TECHNICAL_DEX_EXECUTION_VALIDATION.md"
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

rollback() {
  rc=$?
  trap - ERR
  echo "ERA63C_FAILED_RC=$rc"
  if [[ "$COMMITTED" -eq 0 && -f "$BACKUP" ]]; then
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
root = Path("/root/tokenoskobi_clean_v1")
runtime = json.loads((root / "PROJECT_RUNTIME.json").read_text(encoding="utf-8"))
assert runtime.get("current_era") == "ERA63"
assert runtime.get("next_safe_step") == "ERA63C_END_TO_END_REPLAY_AND_COST_VALIDATION"
assert runtime.get("current_stage") == "ERA63B_ACCELERATED_PAPER_TRADING_CORE_BUILD"
print("PRECHECK=VERIFIED")
PY_PRECHECK

existing=()
for file in "${ALL_FILES[@]}"; do
  if [[ -e "$file" ]]; then
    existing+=("$file")
  fi
done
for file in "${NEW_FILES[@]}"; do
  if [[ -e "$file" ]]; then
    PREEXISTED["$file"]=1
  fi
done
tar -czf "$BACKUP" -C "$ROOT" "${existing[@]}"
echo "BACKUP=$BACKUP"

mkdir -p config tools tests data/replay data/control reports

cat >config/era63c_technical_dex_execution_v1.json <<'ERA63C_CONFIG'
{
  "schema": "tokenoskobi.era63c.technical_dex_execution_config.v1",
  "mode": "VALIDATION_ONLY_ZERO_REAL_FUNDS",
  "paper_runtime_enabled": false,
  "unattended_runtime_enabled": false,
  "real_trade_enabled": false,
  "wallet_enabled": false,
  "signing_enabled": false,
  "real_order_broadcast_enabled": false,
  "ema_fast": 9,
  "ema_slow": 21,
  "ema_long": 50,
  "rsi_window": 14,
  "atr_window": 14,
  "adx_window": 14,
  "bollinger_window": 20,
  "bollinger_stddev": 2.0,
  "primary_timeframe": "1h",
  "timeframe_weights": {
    "5m": 0.2,
    "15m": 0.3,
    "1h": 0.5
  },
  "min_directional_score": 0.08,
  "min_timeframe_consensus": 0.6,
  "min_technical_confidence": 0.4,
  "min_net_edge_bps": 8.0,
  "max_gross_edge_bps": 300.0,
  "risk_fraction": 0.01,
  "max_position_fraction": 0.15,
  "atr_stop_multiple": 2.0,
  "min_stop_bps": 50.0,
  "min_notional_usd": 10.0,
  "probe_notional_usd": 100.0,
  "max_size_reduction_steps": 8,
  "max_market_age_sec": 120.0,
  "max_price_impact_bps": 120.0,
  "recommended_price_impact_bps": 50.0,
  "max_expected_sandwich_loss_bps": 30.0,
  "max_sandwich_probability": 0.5,
  "max_round_trip_token_tax_bps": 300.0,
  "max_slippage_tolerance_bps": 150.0,
  "recommended_slippage_bps": 80.0,
  "max_route_hops": 3,
  "max_participation_fraction": 0.01,
  "absolute_max_participation_fraction": 0.05,
  "max_split_count": 8,
  "other_mev_max_bps": 25.0,
  "private_relay_probability_multiplier": 0.15,
  "sandwich_attack_factors": [
    0.1,
    0.25,
    0.5,
    1.0,
    2.0,
    4.0
  ]
}
ERA63C_CONFIG

cat >tools/era63_technical_dex_execution_v1.py <<'ERA63C_ENGINE'
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
ERA63C_ENGINE
chmod +x tools/era63_technical_dex_execution_v1.py

cat >tests/test_era63c_technical_dex_execution_v1.py <<'ERA63C_TESTS'
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
ERA63C_TESTS
chmod +x tests/test_era63c_technical_dex_execution_v1.py

python3 <<'PY_FIXTURE'
from __future__ import annotations
import json
import math
from pathlib import Path

ROOT = Path("/root/tokenoskobi_clean_v1")
OUT = ROOT / "data/replay/era63c_technical_dex_execution_replay_matrix_v1.json"

def candles(step: float, interval: int, falling: bool = False) -> list[dict]:
    rows = []
    price = 1.0
    direction = -1.0 if falling else 1.0
    for index in range(90):
        delta = direction * step * (1.0 + 0.2 * math.sin(index / 5.0))
        open_price = price
        close_price = max(0.05, price + delta)
        high = max(open_price, close_price) + abs(delta) * 0.5 + 0.001
        low = max(0.001, min(open_price, close_price) - abs(delta) * 0.5 - 0.001)
        rows.append({
            "timestamp": 1_700_000_000 + index * interval,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close_price,
            "volume": 10_000.0 * (1.0 + 0.01 * index),
        })
        price = close_price
    return rows

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
            "5m": candles(0.0025, 300, falling),
            "15m": candles(0.0030, 900, falling),
            "1h": candles(0.0035, 3600, falling),
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

matrix = {
    "schema": "tokenoskobi.era63c.replay_matrix.v1",
    "scenarios": [
        {"scenario_id": "SAFE_DEEP_PUBLIC", "expected_action": "BUY", "payload": payload()},
        {
            "scenario_id": "HIGH_SANDWICH_PUBLIC",
            "expected_action": "WAIT",
            "payload": payload(
                reserve=20_000.0,
                slippage=300.0,
                historical=0.8,
                gas_competition=0.9,
                pending=900.0,
            ),
        },
        {
            "scenario_id": "PROTECTED_PRIVATE_RELAY",
            "expected_action": "BUY",
            "payload": payload(
                reserve=100_000.0,
                historical=0.5,
                gas_competition=0.7,
                pending=700.0,
                public=False,
                private_relay=True,
            ),
        },
        {"scenario_id": "HIGH_TOKEN_TAX", "expected_action": "WAIT", "payload": payload(tax_bps=1000.0)},
        {"scenario_id": "STALE_DEX_DATA", "expected_action": "WAIT", "payload": payload(age=999.0)},
        {"scenario_id": "FALLING_TECHNICAL", "expected_action": "WAIT", "payload": payload(falling=True)},
        {
            "scenario_id": "ROUTE_SELECTION",
            "expected_action": "BUY",
            "payload": payload(
                routes=[
                    route("shallow", 10_000.0),
                    route("deep", 1_000_000.0, 30.0),
                ]
            ),
        },
        {
            "scenario_id": "MULTIHOP_ROUTE",
            "expected_action": "BUY",
            "payload": payload(routes=[route("multi", 1_000_000.0, hops=2)]),
        },
    ],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"REPLAY_FIXTURE={OUT.relative_to(ROOT)}")
PY_FIXTURE

python3 -m py_compile tools/era63_technical_dex_execution_v1.py
python3 tests/test_era63b_paper_trading_core_v1.py
python3 tests/test_era63c_technical_dex_execution_v1.py

python3 tools/era63_technical_dex_execution_v1.py \
  --input data/replay/era63c_technical_dex_execution_replay_matrix_v1.json \
  --config config/era63c_technical_dex_execution_v1.json \
  --matrix \
  --output data/replay/era63c_technical_dex_execution_replay_matrix_result_v1.json

python3 <<'PY_MATRIX_CHECK'
import json
from pathlib import Path
path = Path("/root/tokenoskobi_clean_v1/data/replay/era63c_technical_dex_execution_replay_matrix_result_v1.json")
value = json.loads(path.read_text(encoding="utf-8"))
assert value["scenario_count"] == 8
assert value["pass_count"] == 8
assert all(item["pass"] for item in value["results"])
print("REPLAY_MATRIX=8/8_PASS")
PY_MATRIX_CHECK

python3 <<'PY_CANONICAL'
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
NOW = datetime.now(timezone.utc).isoformat()

STAGE = "ERA63C_TECHNICAL_DEX_EXECUTION_VALIDATION"
STATUS = "LOCAL_TECHNICAL_DEX_EXECUTION_VALIDATED"
NEXT = "ERA63D_REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING"
CONTROL = "data/control/era63c_technical_dex_execution_validation_v1.json"
REPORT = "reports/LATEST_ERA63C_TECHNICAL_DEX_EXECUTION_VALIDATION.md"
MATRIX = "data/replay/era63c_technical_dex_execution_replay_matrix_result_v1.json"

def load(relative: str, default: Any = None) -> Any:
    path = ROOT / relative
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def save(relative: str, value: Any) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)

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
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if pattern.search(text):
        text = pattern.sub(block, text, count=1)
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8")

def find_id(value: Any, target: str) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if value.get("id") == target:
            return value
        for child in value.values():
            found = find_id(child, target)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_id(child, target)
            if found is not None:
                return found
    return None

matrix = load(MATRIX, {})
assert matrix.get("scenario_count") == 8
assert matrix.get("pass_count") == 8

control = {
    "schema": "tokenoskobi.era63c.technical_dex_execution_validation.v1",
    "era": "ERA63",
    "stage": STAGE,
    "status": STATUS,
    "validated_at_utc": NOW,
    "tests": {
        "era63b_regression": "13/13_PASS",
        "era63c_new_tests": "21/21_PASS",
        "combined": "34/34_PASS",
    },
    "replay_matrix": {
        "artifact": MATRIX,
        "scenarios": "8/8_PASS",
    },
    "implemented": [
        "MULTI_TIMEFRAME_TECHNICAL_ANALYSIS",
        "EMA_RSI_ATR_ADX_MACD_BOLLINGER_VOLUME_OBV_SUPPORT_RESISTANCE",
        "CONSTANT_PRODUCT_AMM_PRICE_IMPACT",
        "MULTI_ROUTE_AND_MULTIHOP_EVALUATION",
        "DYNAMIC_SANDWICH_PROBABILITY",
        "FRONT_RUN_BACK_RUN_SANDWICH_SIMULATION",
        "EXPECTED_SANDWICH_LOSS",
        "OTHER_MEV_EXPECTED_COST",
        "BUY_SELL_TOKEN_TAX",
        "GAS_AND_DEX_FEE",
        "ADAPTIVE_POSITION_SIZING",
        "PRIVATE_RELAY_SPLIT_AND_ROUTE_PROTECTION_RECOMMENDATIONS",
        "END_TO_END_ZERO_REAL_FUNDS_REPLAY",
    ],
    "authority": {
        "paper_simulation": True,
        "paper_order_create": "SIMULATION_ONLY",
        "paper_position_management": "SIMULATION_ONLY",
        "paper_runtime_enabled": False,
        "unattended_runtime_enabled": False,
        "real_trade_authority": 0,
        "wallet_authority": 0,
        "signing_authority": 0,
        "real_order_authority": 0,
        "broadcast_authority": 0,
        "risk_engine_veto": True,
    },
    "remaining_before_technical_line_complete": [
        "REAL_MARKET_AND_CANDLE_SOURCE_BINDING",
        "REAL_DEX_POOL_RESERVE_AND_ROUTE_SOURCE_BINDING",
        "REAL_MEMPOOL_MEV_SIGNAL_SOURCE_BINDING",
        "OBSERVATION_WITH_FRESHNESS_AND_LATENCY_EVIDENCE",
    ],
    "locked_v4_sequence": [
        "ERA63_TECHNICAL_AND_DEX_EXECUTION",
        "ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING",
        "ERA65_ONCHAIN_CEX_TO_DEX_WHALE_FLOW",
        "ERA66_NEWS_AIRDROP_ICO_IDO_LAUNCH_INTELLIGENCE",
        "ERA67_COORDINATED_MULTI_INTELLIGENCE_FUSION",
        "ERA68_UNATTENDED_PAPER_RUNTIME",
    ],
    "next_safe_step": NEXT,
}
save(CONTROL, control)

runtime = load("PROJECT_RUNTIME.json", {})
if not isinstance(runtime, dict):
    raise TypeError("PROJECT_RUNTIME.json must be an object")
runtime.update({
    "current_version": "V4",
    "current_era": "ERA63",
    "current_stage": STAGE,
    "current_status": STATUS,
    "last_completed": STAGE,
    "last_result": "ERA63C_34_OF_34_TESTS_AND_8_OF_8_REPLAY_PASS",
    "next_safe_step": NEXT,
    "updated_at_utc": NOW,
    "status": "ACTIVE",
    "project_status": "V4_ERA63_ACTIVE",
})
runtime["open_risks"] = [
    "ERA63D_REQUIRED:REAL_MARKET_AND_CANDLE_SOURCE_BINDING",
    "ERA63D_REQUIRED:REAL_DEX_POOL_ROUTE_AND_MEMPOOL_BINDING",
    "ERA64_REQUIRED:SUCCESSFUL_WALLET_STATS_AND_CLUSTERING",
    "ERA65_REQUIRED:CEX_TO_DEX_WHALE_AND_SUBWALLET_FLOW",
    "ERA66_REQUIRED:NEWS_AIRDROP_ICO_IDO_LAUNCH_INTELLIGENCE",
    "ERA67_REQUIRED:COORDINATED_MULTI_INTELLIGENCE_FUSION",
    "ERA68_REQUIRED:UNATTENDED_PAPER_RUNTIME",
]
work = runtime.setdefault("work_unit", {})
work.update({
    "id": "ERA63_ACCELERATED_PAPER_TRADING_CORE",
    "title": "Technical Analysis and DEX Execution Foundation",
    "status": STATUS,
    "next_substep": NEXT,
    "paper_trade_currently": "DISABLED_PENDING_REAL_DATA_BINDING_AND_COORDINATED_INTELLIGENCE",
    "live_trade": "DISABLED",
    "wallet_authority": 0,
    "signing_authority": 0,
    "real_order_create_authority": 0,
})
completed = work.setdefault("completed_substeps", [])
for item in (
    "ERA63A_ACCELERATED_PAPER_TRADING_GAP_AUDIT",
    "ERA63B_ACCELERATED_PAPER_TRADING_CORE_BUILD",
    STAGE,
):
    if item not in completed:
        completed.append(item)
runtime["era63c_validation"] = control
pointer = runtime.setdefault("canonical_runtime_pointer", {})
pointer.update({
    "current_version_line": "V4",
    "current_era": "ERA63",
    "current_stage": STAGE,
    "era63c_technical_dex_execution_validated": True,
    "paper_runtime_enabled": False,
    "next_safe_step": NEXT,
})
runtime["recent_event"] = {
    "event": STAGE,
    "result": STATUS,
    "timestamp": NOW,
}
save("PROJECT_RUNTIME.json", runtime)

machine = load("data/control/latest_tk_machine_state.json", {})
if not isinstance(machine, dict):
    machine = {}
machine.update({
    "current_version": "V4",
    "current_era": "ERA63",
    "current_stage": STAGE,
    "current_status": STATUS,
    "last_completed": STAGE,
    "last_result": "34/34_TESTS_AND_8/8_REPLAY_PASS",
    "next_safe_step": NEXT,
    "updated_at_utc": NOW,
    "paper_runtime_enabled": False,
    "live_trade": "DISABLED",
    "era63c_control_artifact": CONTROL,
})
save("data/control/latest_tk_machine_state.json", machine)

history = load("PROJECT_HISTORY.json", {})
if not isinstance(history, dict):
    raise TypeError("PROJECT_HISTORY.json must be an object")
events = history.setdefault("events", [])
event_id = "ERA63C_TECHNICAL_DEX_EXECUTION_VALIDATION"
events[:] = [
    event for event in events
    if not (isinstance(event, dict) and event.get("event_id") == event_id)
]
events.append({
    "event_id": event_id,
    "event": "TECHNICAL_ANALYSIS_DEX_EXECUTION_BUILD_AND_REPLAY_VALIDATION",
    "era": "ERA63",
    "status": STATUS,
    "tests": "34/34_PASS",
    "replay": "8/8_PASS",
    "artifact": CONTROL,
    "paper_runtime_enabled": False,
    "real_financial_authority": 0,
    "next_safe_step": NEXT,
    "timestamp_utc": NOW,
})
history["updated_at_utc"] = NOW
save("PROJECT_HISTORY.json", history)

master = load("data/tokenoskobi_v1_v8_master_era_roadmap.json", {})
if not isinstance(master, dict):
    raise TypeError("Master roadmap must be an object")
v4 = find_id(master, "V4")
era63 = find_id(master, "ERA63")
if v4 is None or era63 is None:
    raise RuntimeError("V4 or ERA63 not found")
v4.update({
    "title": "Coordinated Intelligence and Paper-Trading Proving Ground",
    "purpose": (
        "Complete technical execution, successful-wallet intelligence, "
        "onchain and CEX-to-DEX whale flow, launch/news intelligence, "
        "coordinated fusion and then unattended zero-real-funds paper runtime."
    ),
    "status": "ACTIVE",
})
era63.update({
    "title": "Technical Analysis and DEX Execution Foundation",
    "actual_title": "Technical Analysis and DEX Execution Foundation",
    "purpose": (
        "Build and bind multi-timeframe technical analysis with real DEX "
        "price-impact, dynamic MEV/sandwich, token-tax, route and execution protection."
    ),
    "status": STATUS,
    "opened": True,
    "active_stage": STAGE,
    "next_safe_step": NEXT,
    "paper_runtime_enabled": False,
})
substeps = era63.setdefault("substeps", {})
if isinstance(substeps, dict):
    substeps.update({
        "ERA63A": "REAL_GAP_AUDIT_COMPLETED",
        "ERA63B": "MINIMUM_PAPER_CORE_BUILD_COMPLETED",
        "ERA63C": "TECHNICAL_DEX_EXECUTION_VALIDATED_34_OF_34_AND_8_OF_8",
        "ERA63D": "REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING_NEXT",
        "ERA63E": "REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE",
    })

roadmap_definitions = {
    "ERA64": (
        "Successful Wallet Intelligence and Statistical Performance",
        "Measure wallet win rate, ROI, drawdown, consistency, entry/exit quality, "
        "funding relationships, sub-wallets and evidence-backed wallet clusters.",
    ),
    "ERA65": (
        "Onchain and CEX-to-DEX Whale Flow Intelligence",
        "Track CEX-to-DEX and DEX-to-CEX flows, successful-wallet clusters, "
        "sub-wallet distribution, bridge, deployer, holder, liquidity and post-flow price effects.",
    ),
    "ERA66": (
        "News, Airdrop, ICO/IDO and Launch Intelligence",
        "Track trusted crypto news, listing/delisting, airdrop, snapshot, ICO, IDO, "
        "launchpad, TGE, unlock, vesting, hack, rug and protocol events with identity and freshness controls.",
    ),
    "ERA67": (
        "Coordinated Multi-Intelligence Fusion",
        "Align technical, wallet, onchain, whale, news and execution evidence by token, "
        "pair, chain, wallet cluster, event and timestamp before Risk Engine and paper decision.",
    ),
    "ERA68": (
        "Unattended Coordinated Paper-Trading Runtime",
        "Run bounded zero-real-funds paper positions only after all coordinated intelligence lines "
        "are bound, measured and governed by Risk Engine veto.",
    ),
}
for era_id, (title, purpose) in roadmap_definitions.items():
    record = find_id(master, era_id)
    if record is not None:
        record.update({
            "title": title,
            "actual_title": title,
            "purpose": purpose,
            "status": "PLANNED_LOCKED_SEQUENCE",
            "opened": False,
        })
for number in range(69, 81):
    record = find_id(master, f"ERA{number}")
    if record is not None:
        record.update({
            "status": "RESERVED_AFTER_COORDINATED_PAPER_EVIDENCE",
            "opened": False,
            "purpose": (
                "Reserved for evidence-proven capability gaps after ERA68. "
                "Not mandatory and not opened by placeholder sequence."
            ),
        })
direction = master.setdefault("current_direction", {})
direction.update({
    "current_line": "ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION",
    "current_version": "V4",
    "current_version_label": "Coordinated Intelligence and Paper-Trading Proving Ground",
    "current_era": "ERA63",
    "current_stage": STAGE,
    "current_status": STATUS,
    "next_safe_step": NEXT,
    "updated_at_utc": NOW,
})
save("data/tokenoskobi_v1_v8_master_era_roadmap.json", master)

roadmap_text = f"""# 03 ROADMAP - TOKENOSKOBI

```text
CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={STAGE}
ERA63_STATUS={STATUS}
NEXT_SAFE_STEP={NEXT}
```

## LOCKED V4 EXECUTION ORDER

```text
ERA63=TECHNICAL_ANALYSIS_AND_DEX_EXECUTION
ERA64=SUCCESSFUL_WALLET_STATS_AND_CLUSTERING
ERA65=ONCHAIN_AND_CEX_TO_DEX_WHALE_FLOW
ERA66=NEWS_AIRDROP_ICO_IDO_AND_LAUNCH_INTELLIGENCE
ERA67=COORDINATED_MULTI_INTELLIGENCE_FUSION
ERA68=UNATTENDED_COORDINATED_PAPER_RUNTIME
```

## ERA63

```text
ERA63A=REAL_GAP_AUDIT=COMPLETED
ERA63B=BASE_PAPER_CORE=COMPLETED_13_OF_13
ERA63C=TECHNICAL_DEX_EXECUTION=COMPLETED_34_OF_34_AND_8_OF_8
ERA63D=REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING=NEXT
ERA63E=REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE
```

ERA63C includes multi-timeframe technical analysis, AMM price impact, dynamic MEV and sandwich simulation, route selection, token tax, adaptive sizing and execution protection.

Paper runtime remains disabled until real data binding and the coordinated V4 intelligence sequence are complete.

ERA69-ERA80 are reserved only for evidence-proven gaps. They are not mandatory placeholders.
"""
write("03_ROADMAP.md", roadmap_text)

atlas_block = """## COORDINATED V4 INTELLIGENCE AND PAPER DECISION FLOW

```text
REAL MARKET / CANDLES / DEX POOLS / MEMPOOL
→ MULTI-TIMEFRAME TECHNICAL ANALYSIS
→ AMM PRICE IMPACT + MEV + SANDWICH + TOKEN TAX + ROUTE RISK

SUCCESSFUL WALLET PERFORMANCE
→ MAIN WALLET + SUB-WALLET + FUNDING + CLUSTER GRAPH

ONCHAIN + CEX-TO-DEX / DEX-TO-CEX FLOW
→ WHALE + LIQUIDITY + HOLDER + BRIDGE + POST-FLOW PRICE EFFECT

NEWS + AIRDROP + ICO/IDO + LAUNCH + LISTING + UNLOCK
→ IDENTITY + SOURCE TRUST + FRESHNESS + EVENT EVIDENCE

ALL LINES
→ TOKEN / PAIR / CHAIN / WALLET_CLUSTER / EVENT / TIMESTAMP ALIGNMENT
→ OPPORTUNITY ENGINE
→ PROSECUTOR
→ RISK ENGINE VETO
→ ZERO-REAL-FUNDS PAPER DECISION
→ OUTCOME MEMORY
```

Rules:

- No intelligence line acts alone.
- Successful-wallet activity is measured statistically before influence.
- Whale scope includes CEX-to-DEX movement and related sub-wallets, not only large transfers.
- News includes airdrop, snapshot, ICO, IDO, launchpad, TGE, listing, unlock and vesting.
- Dynamic MEV and sandwich expected loss are deducted from edge before sizing.
- Paper runtime is not enabled before all required lines are coordinated.
"""
upsert("05_ATLAS.md", "V4_COORDINATED_INTELLIGENCE_FLOW", atlas_block)

master_state = f"""# 06 PROJECT MASTER STATE - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={STAGE}
CURRENT_STATUS={STATUS}
NEXT_SAFE_STEP={NEXT}

## VERIFIED

- ERA63B regression: `13/13_PASS`
- ERA63C technical/execution tests: `21/21_PASS`
- Combined tests: `34/34_PASS`
- End-to-end replay matrix: `8/8_PASS`

## ERA63C CAPABILITY

- Multi-timeframe EMA/RSI/ATR/ADX/MACD/Bollinger/volume/OBV/support-resistance
- Constant-product AMM price impact
- Dynamic sandwich probability
- Front-run/back-run attack simulation
- Expected sandwich and other MEV loss
- Buy/sell token tax
- Route and multi-hop selection
- Adaptive sizing and execution protections

## CURRENT BOUNDARY

PAPER_CALCULATION=true
PAPER_RUNTIME=false
UNATTENDED_RUNTIME=false
LIVE_TRADE=DISABLED
REAL_WALLET=false
REAL_SIGNING=false
REAL_ORDER=false
REAL_BROADCAST=false

Real market, pool, route and mempool binding is the next technical step.
"""
write("06_PROJECT_MASTER_STATE.md", master_state)

handoff = f"""# 07 PROJECT HANDOFF - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={STAGE}
CURRENT_STATUS={STATUS}
NEXT_SAFE_STEP={NEXT}

ERA63C completed the deterministic technical-analysis and DEX-execution layer.

Evidence:

- `{CONTROL}`
- `{MATRIX}`
- `{REPORT}`

Locked continuation:

1. ERA63D real market/candle/pool/route/mempool binding
2. ERA63E observation and technical-line closure
3. ERA64 successful-wallet statistics and sub-wallet clustering
4. ERA65 onchain and CEX-to-DEX whale flows
5. ERA66 news, airdrop, ICO/IDO and launch intelligence
6. ERA67 coordinated fusion
7. ERA68 unattended coordinated paper runtime

No real wallet, signing, order or broadcast authority is enabled.
"""
write("07_PROJECT_HANDOFF.md", handoff)

report = f"""# ERA63C TECHNICAL AND DEX EXECUTION VALIDATION

STATUS={STATUS}
TESTS=34/34_PASS
REPLAY_MATRIX=8/8_PASS
NEXT_SAFE_STEP={NEXT}

## Implemented

- Multi-timeframe technical analysis
- AMM price-impact simulation
- Dynamic sandwich probability and front-run/back-run simulation
- Expected sandwich and other MEV loss
- Token buy/sell tax
- Gas and DEX fees
- Multi-route and multi-hop comparison
- Adaptive position sizing
- Private relay, split-order, slippage and deeper-route protections

## Remaining

This is deterministic replay validation. It is not yet real runtime proof.

Required next:

- Real candle and market source
- Real DEX pool reserves and route source
- Real mempool/MEV context
- Freshness, latency and observation evidence

PAPER_RUNTIME=false
LIVE_TRADE=DISABLED
"""
write(REPORT, report)

write(
    "reports/LATEST_TK_AI_HANDOFF.md",
    f"""# TOKENOSKOBI LATEST AI HANDOFF

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={STAGE}
CURRENT_STATUS={STATUS}
LAST_COMPLETED={STAGE}
NEXT_SAFE_STEP={NEXT}

CONTROL_ARTIFACT={CONTROL}
VALIDATION_REPORT={REPORT}
REPLAY_RESULT={MATRIX}
TESTS=34/34_PASS
REPLAY=8/8_PASS
PAPER_RUNTIME=false
LIVE_TRADE=DISABLED
""",
)

upsert(
    "04_ALMANAC.md",
    "ERA63C_TECHNICAL_DEX_EXECUTION_VALIDATION",
    f"""## ERA63C TECHNICAL AND DEX EXECUTION VALIDATION

- Status: `{STATUS}`
- Tests: `34/34_PASS`
- Replay: `8/8_PASS`
- Dynamic MEV/sandwich: `IMPLEMENTED_AND_REPLAY_VALIDATED`
- Paper runtime: `DISABLED`
- Real financial authority: `0`
- Next: `{NEXT}`
- UTC: `{NOW}`""",
)

print("ERA63C_CANONICAL_SYNC=PASS")
PY_CANONICAL

python3 -m json.tool config/era63c_technical_dex_execution_v1.json >/dev/null
python3 -m json.tool data/replay/era63c_technical_dex_execution_replay_matrix_v1.json >/dev/null
python3 -m json.tool data/replay/era63c_technical_dex_execution_replay_matrix_result_v1.json >/dev/null
python3 -m json.tool data/control/era63c_technical_dex_execution_validation_v1.json >/dev/null
python3 -m json.tool PROJECT_RUNTIME.json >/dev/null
python3 -m json.tool PROJECT_HISTORY.json >/dev/null
python3 -m json.tool data/tokenoskobi_v1_v8_master_era_roadmap.json >/dev/null

git diff --check
git add -f -- "${ALL_FILES[@]}"
git diff --cached --check
! git diff --cached --quiet

git commit -m "ERA63C: validate technical analysis and DEX execution risk"
COMMITTED=1
HEAD="$(git rev-parse HEAD)"

git push origin main
git fetch origin main --quiet

[[ "$(git rev-parse origin/main)" == "$HEAD" ]]
[[ "$(git ls-remote origin refs/heads/main | awk '{print $1}')" == "$HEAD" ]]
[[ -z "$(git status --porcelain=v1)" ]]

trap - ERR

echo "ERA63C_STATUS=LOCAL_TECHNICAL_DEX_EXECUTION_VALIDATED"
echo "TESTS=34/34_PASS"
echo "REPLAY_MATRIX=8/8_PASS"
echo "DYNAMIC_MEV_SANDWICH=VALIDATED"
echo "PAPER_RUNTIME=DISABLED_PENDING_REAL_DATA_AND_COORDINATED_INTELLIGENCE"
echo "LIVE_TRADE=DISABLED"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=ERA63D_REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING"
