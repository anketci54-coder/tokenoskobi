#!/usr/bin/env python3
"""ERA63D bounded real-market and technical-analysis observation runtime.

Uses the keyless GeckoTerminal public API at low frequency. It performs no
wallet, signing, order, swap, trade, database, service-management or policy
mutation. Dynamic outputs are observation-only and fail closed on unknown
execution-risk inputs.
"""
from __future__ import annotations

import argparse
import sys
import json
import math
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path("/root/tokenoskobi_clean_v1")
ENGINE_PATH = ROOT / "tools" / "era63_technical_dex_execution_v1.py"
ENGINE_CONFIG_PATH = ROOT / "config" / "era63c_technical_dex_execution_v1.json"
SCHEMA = "tokenoskobi.era63d.real_market_technical_runtime.v1"
PANEL_SCHEMA = "tokenoskobi.technical_center.live_readmodel.v2"


class Era63DRuntimeError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def finite(value: Any, name: str, default: float | None = None) -> float:
    if value is None and default is not None:
        return float(default)
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise Era63DRuntimeError(f"{name}:NOT_NUMERIC") from exc
    if not math.isfinite(number):
        raise Era63DRuntimeError(f"{name}:NOT_FINITE")
    return number


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Era63DRuntimeError(f"{path}:NOT_OBJECT")
    return value


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        json.loads(Path(temporary).read_text(encoding="utf-8"))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_jsonl(path: Path, value: dict[str, Any], max_bytes: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > max_bytes:
        rotated = path.with_suffix(path.suffix + ".1")
        rotated.unlink(missing_ok=True)
        path.replace(rotated)
    line = json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def load_engine():
    root_text = str(ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    from tools import era63_technical_dex_execution_v1 as module
    return module


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema") != "tokenoskobi.era63d.market_technical_runtime_config.v1":
        raise Era63DRuntimeError("CONFIG_SCHEMA_MISMATCH")
    if config.get("runtime_enabled") is not True:
        raise Era63DRuntimeError("RUNTIME_NOT_ENABLED")
    if config.get("observation_only") is not True:
        raise Era63DRuntimeError("OBSERVATION_ONLY_REQUIRED")
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
        if config.get(key) is not False:
            raise Era63DRuntimeError(f"{key}:MUST_BE_FALSE")
    provider = config.get("provider")
    if not isinstance(provider, dict):
        raise Era63DRuntimeError("PROVIDER_NOT_OBJECT")
    base_url = str(provider.get("base_url") or "")
    parsed = urllib.parse.urlparse(base_url)
    allowed_hosts = set(provider.get("allowed_hosts") or [])
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise Era63DRuntimeError("PROVIDER_BASE_URL_NOT_ALLOWLISTED_HTTPS")
    if str(provider.get("network") or "") != "bsc":
        raise Era63DRuntimeError("ERA63D_FIRST_CHAIN_MUST_BE_BSC")
    if not 1 <= int(provider.get("max_pools", 0)) <= 5:
        raise Era63DRuntimeError("MAX_POOLS_OUT_OF_BOUNDS")
    if float(provider.get("minimum_request_interval_sec", 0)) < 1.0:
        raise Era63DRuntimeError("REQUEST_INTERVAL_TOO_FAST")


class ApiClient:
    def __init__(self, config: dict[str, Any], sleeper: Callable[[float], None] = time.sleep):
        provider = config["provider"]
        self.base_url = str(provider["base_url"]).rstrip("/")
        self.allowed_hosts = set(provider["allowed_hosts"])
        self.timeout = float(provider["request_timeout_sec"])
        self.retries = int(provider["retries"])
        self.min_interval = float(provider["minimum_request_interval_sec"])
        self.user_agent = str(provider.get("user_agent") or "Tokenoskobi-ERA63D/1.0")
        self._last_request = 0.0
        self._sleep = sleeper
        self.request_count = 0

    def build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        if not path.startswith("/"):
            raise Era63DRuntimeError("PROVIDER_PATH_MUST_BE_ABSOLUTE")
        url = self.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise Era63DRuntimeError("PROVIDER_URL_NOT_ALLOWLISTED_HTTPS")
        return url

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.build_url(path, params)
        last_error = ""
        for attempt in range(self.retries + 1):
            elapsed = time.monotonic() - self._last_request
            if elapsed < self.min_interval:
                self._sleep(self.min_interval - elapsed)
            request = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": self.user_agent},
                method="GET",
            )
            self._last_request = time.monotonic()
            self.request_count += 1
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    status = int(getattr(response, "status", 200))
                    if status != 200:
                        raise Era63DRuntimeError(f"PROVIDER_HTTP_STATUS:{status}")
                    payload = json.loads(response.read().decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise Era63DRuntimeError("PROVIDER_RESPONSE_NOT_OBJECT")
                    return payload
            except urllib.error.HTTPError as exc:
                last_error = f"HTTP_{exc.code}"
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if not retryable or attempt >= self.retries:
                    break
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                wait = float(retry_after) if retry_after and retry_after.isdigit() else 2.0 ** attempt
                self._sleep(min(wait, 30.0))
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                last_error = f"{type(exc).__name__}:{exc}"
                if attempt >= self.retries:
                    break
                self._sleep(min(2.0 ** attempt, 30.0))
        raise Era63DRuntimeError(f"PROVIDER_REQUEST_FAILED:{last_error}:{url}")


def nested_number(value: Any, *keys: str, default: float = 0.0) -> float:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return float(default)
        current = current.get(key)
    try:
        number = float(current)
    except (TypeError, ValueError):
        return float(default)
    return number if math.isfinite(number) else float(default)


def parse_fee_bps(name: str, default_fee_bps: float) -> tuple[float, str]:
    matches = re.findall(r"(?<![\d.])(\d+(?:\.\d+)?)\s*%", name or "")
    if matches:
        fee_bps = float(matches[-1]) * 100.0
        if 0.1 <= fee_bps <= 1000.0:
            return fee_bps, "POOL_NAME_DISCLOSED"
    return float(default_fee_bps), "CONFIG_CONSERVATIVE_DEFAULT"


def parse_pool_candidates(payload: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise Era63DRuntimeError("DISCOVERY_DATA_NOT_LIST")
    provider = config["provider"]
    min_liquidity = float(provider["min_liquidity_usd"])
    min_volume = float(provider["min_volume_h24_usd"])
    candidates: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        attrs = row.get("attributes")
        if not isinstance(attrs, dict):
            continue
        address = str(attrs.get("address") or "").strip()
        name = str(attrs.get("name") or row.get("id") or address).strip()
        liquidity = nested_number(attrs, "reserve_in_usd")
        volume_h24 = nested_number(attrs, "volume_usd", "h24")
        base_price = nested_number(attrs, "base_token_price_usd")
        quote_price = nested_number(attrs, "quote_token_price_usd", default=1.0)
        if not address or liquidity <= 0 or base_price <= 0:
            continue
        candidates.append(
            {
                "pool_id": str(row.get("id") or address),
                "address": address,
                "name": name,
                "liquidity_usd": liquidity,
                "volume_h24_usd": volume_h24,
                "base_price_usd": base_price,
                "quote_price_usd": quote_price if quote_price > 0 else 1.0,
                "transactions_h1": int(
                    nested_number(attrs, "transactions", "h1", "buys")
                    + nested_number(attrs, "transactions", "h1", "sells")
                ),
                "pool_created_at": attrs.get("pool_created_at"),
                "meets_primary_filter": liquidity >= min_liquidity and volume_h24 >= min_volume,
            }
        )
    candidates.sort(
        key=lambda item: (
            1 if item["meets_primary_filter"] else 0,
            item["liquidity_usd"],
            item["volume_h24_usd"],
            item["address"],
        ),
        reverse=True,
    )
    return candidates[: int(provider["max_pools"])]


def parse_ohlcv(payload: dict[str, Any], minimum: int) -> list[dict[str, float]]:
    data = payload.get("data")
    attrs = data.get("attributes") if isinstance(data, dict) else None
    rows = attrs.get("ohlcv_list") if isinstance(attrs, dict) else None
    if not isinstance(rows, list):
        raise Era63DRuntimeError("OHLCV_LIST_MISSING")
    by_timestamp: dict[int, dict[str, float]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) < 6:
            continue
        timestamp = int(finite(row[0], f"ohlcv.{index}.timestamp"))
        candle = {
            "timestamp": float(timestamp),
            "open": finite(row[1], f"ohlcv.{index}.open"),
            "high": finite(row[2], f"ohlcv.{index}.high"),
            "low": finite(row[3], f"ohlcv.{index}.low"),
            "close": finite(row[4], f"ohlcv.{index}.close"),
            "volume": max(0.0, finite(row[5], f"ohlcv.{index}.volume")),
        }
        if min(candle["open"], candle["high"], candle["low"], candle["close"]) <= 0:
            continue
        if candle["high"] < max(candle["open"], candle["close"]):
            continue
        if candle["low"] > min(candle["open"], candle["close"]):
            continue
        by_timestamp[timestamp] = candle
    candles = [by_timestamp[key] for key in sorted(by_timestamp)]
    if len(candles) < minimum:
        raise Era63DRuntimeError(f"OHLCV_INSUFFICIENT:{len(candles)}<{minimum}")
    return candles


def timeframe_requests(config: dict[str, Any]) -> dict[str, tuple[str, int]]:
    configured = config["provider"].get("timeframes")
    if not isinstance(configured, dict) or not configured:
        raise Era63DRuntimeError("TIMEFRAMES_CONFIG_EMPTY")
    result: dict[str, tuple[str, int]] = {}
    for name, item in configured.items():
        if not isinstance(item, dict):
            raise Era63DRuntimeError(f"TIMEFRAME_{name}:NOT_OBJECT")
        timeframe = str(item.get("timeframe") or "")
        aggregate = int(item.get("aggregate", 0))
        if timeframe not in {"minute", "hour", "day"} or aggregate <= 0:
            raise Era63DRuntimeError(f"TIMEFRAME_{name}:INVALID")
        result[str(name)] = (timeframe, aggregate)
    return result


def fetch_frames(client: ApiClient, pool: dict[str, Any], config: dict[str, Any]) -> dict[str, list[dict[str, float]]]:
    provider = config["provider"]
    minimum = int(provider["minimum_candles"])
    limit = int(provider["ohlcv_limit"])
    network = str(provider["network"])
    frames: dict[str, list[dict[str, float]]] = {}
    for name, (timeframe, aggregate) in timeframe_requests(config).items():
        response = client.get_json(
            f"/networks/{network}/pools/{pool['address']}/ohlcv/{timeframe}",
            {
                "aggregate": aggregate,
                "limit": limit,
                "currency": "usd",
                "token": "base",
            },
        )
        frames[name] = parse_ohlcv(response, minimum)
    return frames


def build_engine_payload(
    pool: dict[str, Any],
    frames: dict[str, list[dict[str, float]]],
    config: dict[str, Any],
    now_epoch: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    runtime_model = config["runtime_model"]
    base_price = float(pool["base_price_usd"])
    liquidity = float(pool["liquidity_usd"])
    quote_reserve_usd = liquidity / 2.0
    base_reserve_units = quote_reserve_usd / base_price
    fee_bps, fee_source = parse_fee_bps(pool["name"], float(runtime_model["default_dex_fee_bps"]))
    latest_timestamp = max(frame[-1]["timestamp"] for frame in frames.values())
    latest_candle_age = max(0.0, now_epoch - latest_timestamp)
    market_age = float(runtime_model["provider_cache_age_bound_sec"])
    tx_h1 = max(0, int(pool.get("transactions_h1", 0)))
    pending_proxy = min(1000.0, float(tx_h1) * float(runtime_model["pending_tx_proxy_multiplier"]))
    gas_proxy = min(1.0, float(tx_h1) / float(runtime_model["gas_competition_tx_h1_saturation"]))
    payload = {
        "equity_usd": float(runtime_model["observation_equity_usd"]),
        "timeframes": frames,
        "mark_price_usd": frames[str(runtime_model["primary_timeframe"])][-1]["close"],
        "dex": {
            "routes": [
                {
                    "route_id": f"{pool['address']}:single_pool",
                    "hops": [
                        {
                            "pool_id": pool["address"],
                            "reserve_in": quote_reserve_usd,
                            "reserve_out": base_reserve_units,
                            "fee_bps": fee_bps,
                            "token_out_price_usd": base_price,
                        }
                    ],
                }
            ],
            "mempool": {
                "public": True,
                "private_relay": False,
                "pending_tx_count": pending_proxy,
                "gas_competition_ratio": gas_proxy,
                "historical_sandwich_rate": float(runtime_model["conservative_historical_sandwich_rate"]),
            },
            "token_tax": {"buy_bps": 0.0, "sell_bps": 0.0},
            "gas_usd": float(runtime_model["conservative_gas_usd"]),
            "market_age_sec": market_age,
            "slippage_tolerance_bps": float(runtime_model["observation_slippage_bps"]),
        },
    }
    quality = {
        "real_market_data": True,
        "ohlcv_source": "GECKOTERMINAL_KEYLESS_PUBLIC",
        "pool_liquidity_source": "GECKOTERMINAL_KEYLESS_PUBLIC",
        "pool_reserves": "ESTIMATED_FROM_TVL_AND_BASE_PRICE",
        "dex_fee_source": fee_source,
        "mempool_measurement": "TRANSACTION_ACTIVITY_PROXY_ONLY",
        "token_tax_measurement": "UNKNOWN_FAIL_CLOSED",
        "gas_measurement": "CONSERVATIVE_CONFIG_DEFAULT",
        "coordinated_intelligence": "NOT_BOUND_YET",
        "latest_candle_timestamp": latest_timestamp,
        "latest_candle_age_sec": latest_candle_age,
        "provider_cache_age_bound_sec": market_age,
        "market_age_sec": market_age,
    }
    return payload, quality


def runtime_guard(engine_result: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
    blocks = [
        "TOKEN_TAX_UNKNOWN",
        "MEMPOOL_DIRECT_MEASUREMENT_MISSING",
        "POOL_RESERVES_ESTIMATED_FROM_TVL",
        "COORDINATED_INTELLIGENCE_NOT_BOUND",
        "PAPER_RUNTIME_NOT_AUTHORIZED",
    ]
    engine_action = str(((engine_result.get("edge") or {}).get("action") or "WAIT"))
    status = "TECHNICAL_CANDIDATE_OBSERVE_ONLY" if engine_action == "BUY" else "OBSERVE_WAIT"
    return {
        "status": status,
        "engine_action": engine_action,
        "paper_action": "DISABLED",
        "final_trade_action": "NONE",
        "blocks": blocks,
        "quality": quality,
    }


def build_panel(snapshot: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for row in snapshot["items"]:
        result = row["engine_result"]
        technical = result["technical"]
        selected = result["execution_probe"]["selected"]
        items.append(
            {
                "key": row["pool_address"],
                "label": row["pool_name"],
                "status": row["runtime_guard"]["status"],
                "network": snapshot["network"],
                "source": snapshot["provider"],
                "live_ta_claim": True,
                "observation_only": True,
                "engine_action": row["runtime_guard"]["engine_action"],
                "paper_action": "DISABLED",
                "price_usd": technical["price"],
                "directional_score": technical["directional_score"],
                "confidence": technical["confidence"],
                "consensus": technical["consensus"],
                "gross_edge_bps": result["edge"]["gross_edge_bps"],
                "probe_net_edge_bps": result["edge"]["probe_net_edge_bps"],
                "sandwich_probability": selected["sandwich"]["probability"],
                "expected_sandwich_loss_bps": selected["sandwich"]["expected_loss_bps"],
                "price_impact_bps": selected["quote"]["price_impact_bps"],
                "execution_risk_score": selected["risk_score"],
                "liquidity_usd": row["liquidity_usd"],
                "volume_h24_usd": row["volume_h24_usd"],
                "data_quality": row["runtime_guard"]["quality"],
                "blocks": row["runtime_guard"]["blocks"],
            }
        )
    max_age = max((float(item["data_quality"]["market_age_sec"]) for item in items), default=0.0)
    return {
        "schema": PANEL_SCHEMA,
        "stage": "ERA63D_REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING",
        "generated_at_utc": snapshot["generated_at_utc"],
        "producer": "tools/era63d_market_technical_runtime_v1.py",
        "decision": "REAL_MARKET_TECHNICAL_OBSERVATION_ACTIVE",
        "data_freshness_sec": max_age,
        "source_count": len(items),
        "authority": {
            "trade": False,
            "paper_trade_write": False,
            "wallet": False,
            "signing": False,
            "real_order": False,
            "broadcast": False,
            "provider_call_from_browser": False,
            "policy_apply": False,
        },
        "items": items,
    }


def discovery_payload(client: ApiClient, config: dict[str, Any]) -> dict[str, Any]:
    provider = config["provider"]
    network = str(provider["network"])
    try:
        return client.get_json(
            f"/networks/{network}/pools",
            {"include": "base_token,quote_token,dex", "page": 1},
        )
    except Era63DRuntimeError:
        return client.get_json(
            f"/networks/{network}/trending_pools",
            {"include": "base_token,quote_token,dex", "page": 1, "duration": "24h"},
        )


def run_runtime(config: dict[str, Any], *, client: ApiClient | None = None, now: datetime | None = None) -> dict[str, Any]:
    validate_config(config)
    engine = load_engine()
    engine_config = read_json(ENGINE_CONFIG_PATH)
    api = client or ApiClient(config)
    current = now or utc_now()
    candidates = parse_pool_candidates(discovery_payload(api, config), config)
    if not candidates:
        raise Era63DRuntimeError("NO_VALID_BSC_POOL_CANDIDATES")
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for pool in candidates:
        try:
            frames = fetch_frames(api, pool, config)
            payload, quality = build_engine_payload(pool, frames, config, current.timestamp())
            result = engine.run_cycle(payload, engine_config)
            guard = runtime_guard(result, quality)
            items.append(
                {
                    "pool_id": pool["pool_id"],
                    "pool_address": pool["address"],
                    "pool_name": pool["name"],
                    "liquidity_usd": pool["liquidity_usd"],
                    "volume_h24_usd": pool["volume_h24_usd"],
                    "base_price_usd": pool["base_price_usd"],
                    "transactions_h1": pool["transactions_h1"],
                    "engine_result": result,
                    "runtime_guard": guard,
                }
            )
        except Exception as exc:  # bounded per-pool isolation; overall minimum still enforced
            errors.append({"pool_address": pool["address"], "error": f"{type(exc).__name__}:{exc}"})
    minimum_successful = int(config["provider"]["min_successful_pools"])
    if len(items) < minimum_successful:
        raise Era63DRuntimeError(
            f"SUCCESSFUL_POOL_COUNT_TOO_LOW:{len(items)}<{minimum_successful}:ERRORS={errors}"
        )
    snapshot = {
        "schema": SCHEMA,
        "generated_at_utc": current.isoformat(),
        "provider": "GECKOTERMINAL_KEYLESS_PUBLIC",
        "provider_base_url": config["provider"]["base_url"],
        "network": config["provider"]["network"],
        "mode": "READ_ONLY_REAL_MARKET_TECHNICAL_OBSERVATION",
        "request_count": api.request_count,
        "candidate_count": len(candidates),
        "successful_pool_count": len(items),
        "errors": errors,
        "authority": {
            "observation_runtime": True,
            "paper_runtime": False,
            "paper_position_write": False,
            "real_trade": False,
            "wallet": False,
            "signing": False,
            "real_order": False,
            "broadcast": False,
            "system_may_expand_policy": False,
            "risk_engine_veto": True,
        },
        "items": items,
    }
    return snapshot


def write_outputs(snapshot: dict[str, Any], config: dict[str, Any]) -> None:
    outputs = config["outputs"]
    latest = ROOT / str(outputs["latest_snapshot"])
    panel_path = ROOT / str(outputs["panel_readmodel"])
    health_path = ROOT / str(outputs["health"])
    observations = ROOT / str(outputs["observations_jsonl"])
    panel = build_panel(snapshot)
    atomic_write_json(latest, snapshot)
    atomic_write_json(panel_path, panel)
    atomic_write_json(
        health_path,
        {
            "schema": "tokenoskobi.era63d.runtime_health.v1",
            "generated_at_utc": snapshot["generated_at_utc"],
            "status": "PASS",
            "provider": snapshot["provider"],
            "successful_pool_count": snapshot["successful_pool_count"],
            "request_count": snapshot["request_count"],
            "paper_runtime": False,
            "real_financial_authority": 0,
        },
    )
    append_jsonl(
        observations,
        {
            "generated_at_utc": snapshot["generated_at_utc"],
            "provider": snapshot["provider"],
            "network": snapshot["network"],
            "items": [
                {
                    "pool_address": item["pool_address"],
                    "pool_name": item["pool_name"],
                    "status": item["runtime_guard"]["status"],
                    "engine_action": item["runtime_guard"]["engine_action"],
                    "price_usd": item["engine_result"]["technical"]["price"],
                    "directional_score": item["engine_result"]["technical"]["directional_score"],
                    "confidence": item["engine_result"]["technical"]["confidence"],
                    "probe_net_edge_bps": item["engine_result"]["edge"]["probe_net_edge_bps"],
                }
                for item in snapshot["items"]
            ],
        },
        int(outputs["observations_max_bytes"]),
    )


def write_failure(config: dict[str, Any], exc: Exception) -> None:
    try:
        health_path = ROOT / str(config["outputs"]["health"])
        atomic_write_json(
            health_path,
            {
                "schema": "tokenoskobi.era63d.runtime_health.v1",
                "generated_at_utc": iso_now(),
                "status": "FAIL_CLOSED",
                "error": f"{type(exc).__name__}:{exc}",
                "paper_runtime": False,
                "real_financial_authority": 0,
            },
        )
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "era63d_market_technical_runtime_v1.json",
    )
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    config = read_json(args.config)
    try:
        snapshot = run_runtime(config)
        write_outputs(snapshot, config)
    except Exception as exc:
        write_failure(config, exc)
        print(f"ERA63D_RUNTIME=FAIL_CLOSED:{type(exc).__name__}:{exc}")
        return 1
    print("ERA63D_RUNTIME=PASS_REAL_MARKET_TECHNICAL_OBSERVATION")
    print(f"PROVIDER={snapshot['provider']}")
    print(f"NETWORK={snapshot['network']}")
    print(f"SUCCESSFUL_POOLS={snapshot['successful_pool_count']}")
    print(f"REQUEST_COUNT={snapshot['request_count']}")
    print("PAPER_RUNTIME=DISABLED")
    print("LIVE_TRADE=DISABLED")
    if args.stdout:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
