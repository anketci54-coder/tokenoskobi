#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

ROOT="/root/tokenoskobi_clean_v1"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era63d_real_market_technical_backup_${STAMP}.tar.gz"
SYSTEMD_BACKUP="/root/era63d_systemd_backup_${STAMP}"
BASE_HEAD="$(git rev-parse HEAD)"
REMOTE_PUSHED=0
SYSTEMD_TOUCHED=0
COMMIT_CREATED=0
SERVICE_NAME="tokenoskobi-era63d-market-technical.service"
TIMER_NAME="tokenoskobi-era63d-market-technical.timer"

NEW_FILES=(
  "config/era63d_market_technical_runtime_v1.json"
  "tools/era63d_market_technical_runtime_v1.py"
  "tests/test_era63d_market_technical_runtime_v1.py"
  "systemd_drafts/tokenoskobi-era63d-market-technical.service"
  "systemd_drafts/tokenoskobi-era63d-market-technical.timer"
  "data/control/era63d_real_market_technical_runtime_binding_v1.json"
  "reports/LATEST_ERA63D_REAL_MARKET_TECHNICAL_RUNTIME_BINDING.md"
)

TRACKED_FILES=(
  ".gitignore"
  "03_ROADMAP.md"
  "04_ALMANAC.md"
  "05_ATLAS.md"
  "06_PROJECT_MASTER_STATE.md"
  "07_PROJECT_HANDOFF.md"
  "PROJECT_RUNTIME.json"
  "PROJECT_HISTORY.json"
  "data/tokenoskobi_v1_v8_master_era_roadmap.json"
  "data/control/latest_tk_machine_state.json"
  "data/control/n16d_technical_center_live_producer_result_v1.json"
  "reports/LATEST_TK_AI_HANDOFF.md"
  "tools/technical_center_live_producer_v1.py"
)

ALL_FILES=("${TRACKED_FILES[@]}" "${NEW_FILES[@]}")
declare -A PREEXISTED=()
OLD_TIMER_ENABLED="$(systemctl is-enabled "$TIMER_NAME" 2>/dev/null || true)"
OLD_TIMER_ACTIVE="$(systemctl is-active "$TIMER_NAME" 2>/dev/null || true)"
mkdir -p "$SYSTEMD_BACKUP"
[[ -e "/etc/systemd/system/$SERVICE_NAME" ]] && cp -a "/etc/systemd/system/$SERVICE_NAME" "$SYSTEMD_BACKUP/$SERVICE_NAME"
[[ -e "/etc/systemd/system/$TIMER_NAME" ]] && cp -a "/etc/systemd/system/$TIMER_NAME" "$SYSTEMD_BACKUP/$TIMER_NAME"

rollback() {
  rc=$?
  trap - ERR
  echo "ERA63D_FAILED_RC=$rc"
  if [[ "$REMOTE_PUSHED" -eq 0 ]]; then
    if [[ "$SYSTEMD_TOUCHED" -eq 1 ]]; then
      systemctl disable --now "$TIMER_NAME" >/dev/null 2>&1 || true
      if [[ -e "$SYSTEMD_BACKUP/$SERVICE_NAME" ]]; then
        cp -a "$SYSTEMD_BACKUP/$SERVICE_NAME" "/etc/systemd/system/$SERVICE_NAME"
      else
        rm -f "/etc/systemd/system/$SERVICE_NAME"
      fi
      if [[ -e "$SYSTEMD_BACKUP/$TIMER_NAME" ]]; then
        cp -a "$SYSTEMD_BACKUP/$TIMER_NAME" "/etc/systemd/system/$TIMER_NAME"
      else
        rm -f "/etc/systemd/system/$TIMER_NAME"
      fi
      systemctl daemon-reload >/dev/null 2>&1 || true
      if [[ "$OLD_TIMER_ENABLED" == "enabled" ]]; then
        systemctl enable "$TIMER_NAME" >/dev/null 2>&1 || true
      fi
      if [[ "$OLD_TIMER_ACTIVE" == "active" ]]; then
        systemctl start "$TIMER_NAME" >/dev/null 2>&1 || true
      fi
    fi
    if [[ "$COMMIT_CREATED" -eq 1 ]]; then
      git reset --hard "$BASE_HEAD" >/dev/null 2>&1 || true
    fi
    if [[ -f "$BACKUP" ]]; then
      tar -xzf "$BACKUP" -C "$ROOT"
    fi
    for file in "${NEW_FILES[@]}"; do
      if [[ -z "${PREEXISTED[$file]+x}" ]]; then
        rm -f -- "$ROOT/$file"
      fi
    done
    git reset --quiet >/dev/null 2>&1 || true
    echo "ROLLBACK=COMPLETED"
  else
    echo "ROLLBACK=NOT_APPLIED_REMOTE_PUSHED"
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
root = Path('/root/tokenoskobi_clean_v1')
runtime = json.loads((root / 'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert runtime.get('current_era') == 'ERA63'
assert runtime.get('current_stage') == 'ERA63C_TECHNICAL_DEX_EXECUTION_VALIDATION'
assert runtime.get('next_safe_step') == 'ERA63D_REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING'
assert runtime.get('current_status') == 'LOCAL_TECHNICAL_DEX_EXECUTION_VALIDATED'
print('PRECHECK=VERIFIED')
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
if [[ "${#existing[@]}" -gt 0 ]]; then
  tar -czf "$BACKUP" -C "$ROOT" "${existing[@]}"
else
  tar -czf "$BACKUP" -C "$ROOT" --files-from /dev/null
fi
echo "BACKUP=$BACKUP"

mkdir -p config tools tests systemd_drafts data/control reports runtime/era63d active_panel_8096/current/data
cat >config/era63d_market_technical_runtime_v1.json <<'ERA63D_CONFIG'
{
  "schema": "tokenoskobi.era63d.market_technical_runtime_config.v1",
  "mode": "READ_ONLY_REAL_MARKET_TECHNICAL_OBSERVATION",
  "runtime_enabled": true,
  "observation_only": true,
  "paper_runtime_enabled": false,
  "paper_position_write_enabled": false,
  "real_trade_enabled": false,
  "wallet_enabled": false,
  "signing_enabled": false,
  "real_order_enabled": false,
  "broadcast_enabled": false,
  "policy_expansion_enabled": false,
  "provider": {
    "name": "GECKOTERMINAL_KEYLESS_PUBLIC",
    "base_url": "https://api.geckoterminal.com/api/v2",
    "allowed_hosts": ["api.geckoterminal.com"],
    "network": "bsc",
    "max_pools": 3,
    "min_successful_pools": 1,
    "min_liquidity_usd": 250000.0,
    "min_volume_h24_usd": 100000.0,
    "minimum_candles": 60,
    "ohlcv_limit": 100,
    "request_timeout_sec": 25,
    "retries": 3,
    "minimum_request_interval_sec": 1.1,
    "user_agent": "Tokenoskobi-ERA63D/1.0 read-only",
    "timeframes": {
      "5m": {"timeframe": "minute", "aggregate": 5},
      "15m": {"timeframe": "minute", "aggregate": 15},
      "1h": {"timeframe": "hour", "aggregate": 1}
    }
  },
  "runtime_model": {
    "primary_timeframe": "1h",
    "observation_equity_usd": 10000.0,
    "observation_slippage_bps": 80.0,
    "default_dex_fee_bps": 30.0,
    "conservative_gas_usd": 0.15,
    "provider_cache_age_bound_sec": 60.0,
    "conservative_historical_sandwich_rate": 0.08,
    "pending_tx_proxy_multiplier": 2.0,
    "gas_competition_tx_h1_saturation": 500.0,
    "unknown_token_tax_policy": "BLOCK",
    "unknown_direct_mempool_policy": "PROXY_AND_BLOCK_PAPER",
    "estimated_reserve_policy": "ALLOW_OBSERVATION_BLOCK_PAPER",
    "coordinated_intelligence_policy": "BLOCK_PAPER_UNTIL_ERA67"
  },
  "outputs": {
    "latest_snapshot": "runtime/era63d/latest_real_market_technical_snapshot_v1.json",
    "health": "runtime/era63d/health_v1.json",
    "observations_jsonl": "runtime/era63d/technical_observations_v1.jsonl",
    "observations_max_bytes": 52428800,
    "panel_readmodel": "active_panel_8096/current/data/technical_center_live_readmodel_v1.json"
  },
  "schedule": {
    "interval_minutes": 15,
    "randomized_delay_seconds": 45,
    "persistent": true
  }
}
ERA63D_CONFIG

cat >tools/era63d_market_technical_runtime_v1.py <<'ERA63D_RUNTIME'
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
ERA63D_RUNTIME

cat >tests/test_era63d_market_technical_runtime_v1.py <<'ERA63D_TESTS'
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
ERA63D_TESTS

cat >systemd_drafts/tokenoskobi-era63d-market-technical.service <<'ERA63D_SERVICE'
[Unit]
Description=Tokenoskobi ERA63D real-market technical observation runtime
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/root/tokenoskobi_clean_v1
ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/era63d_market_technical_runtime_v1.py --config /root/tokenoskobi_clean_v1/config/era63d_market_technical_runtime_v1.json
Environment=PYTHONUNBUFFERED=1
UMask=0077
Nice=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
CapabilityBoundingSet=
ReadWritePaths=/root/tokenoskobi_clean_v1/runtime/era63d /root/tokenoskobi_clean_v1/active_panel_8096/current/data
TimeoutStartSec=180
ERA63D_SERVICE

cat >systemd_drafts/tokenoskobi-era63d-market-technical.timer <<'ERA63D_TIMER'
[Unit]
Description=Run Tokenoskobi ERA63D market technical observation every 15 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=15min
RandomizedDelaySec=45
AccuracySec=30s
Persistent=true
Unit=tokenoskobi-era63d-market-technical.service

[Install]
WantedBy=timers.target
ERA63D_TIMER

cat >tools/technical_center_live_producer_v1.py <<'ERA63D_PRODUCER'
#!/usr/bin/env python3
"""Bridge the ERA63D runtime snapshot into the technical-center panel readmodel."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/root/tokenoskobi_clean_v1")
LATEST = ROOT / "runtime/era63d/latest_real_market_technical_snapshot_v1.json"
PANEL = ROOT / "active_panel_8096/current/data/technical_center_live_readmodel_v1.json"
OUT = ROOT / "data/control/n16d_technical_center_live_producer_result_v1.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        read_json(Path(temporary))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def missing(reason: str):
    return {
        "schema": "tokenoskobi.technical_center.live_readmodel.v2",
        "stage": "ERA63D_REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING",
        "generated_at_utc": now(),
        "producer": "tools/technical_center_live_producer_v1.py",
        "decision": "TECHNICAL_CENTER_DATA_MISSING",
        "data_freshness_sec": 0,
        "source_count": 0,
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
        "items": [{
            "key": "technical_center",
            "label": "Teknik Analiz Merkezi",
            "status": "DATA_MISSING",
            "live_ta_claim": False,
            "note": reason,
        }],
    }


def main() -> int:
    if not LATEST.exists():
        model = missing("ERA63D runtime snapshot is not available yet.")
    else:
        root_text = str(ROOT)
        if root_text not in sys.path:
            sys.path.insert(0, root_text)
        from tools.era63d_market_technical_runtime_v1 import build_panel
        snapshot = read_json(LATEST)
        model = build_panel(snapshot)
    atomic_write(PANEL, model)
    atomic_write(OUT, model)
    print("FINAL_GATE=PASS_ERA63D_TECHNICAL_CENTER_BRIDGE")
    print(f"DECISION={model['decision']}")
    print(f"SOURCE_COUNT={model['source_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
ERA63D_PRODUCER

python3 <<'PY_GITIGNORE'
from pathlib import Path
path = Path('/root/tokenoskobi_clean_v1/.gitignore')
text = path.read_text(encoding='utf-8')
start = '# TOKENOSKOBI ERA63D LIVE TECHNICAL OUTPUTS BEGIN'
end = '# TOKENOSKOBI ERA63D LIVE TECHNICAL OUTPUTS END'
block = '''# TOKENOSKOBI ERA63D LIVE TECHNICAL OUTPUTS BEGIN
runtime/era63d/
active_panel_8096/current/data/technical_center_live_readmodel_v1.json
# TOKENOSKOBI ERA63D LIVE TECHNICAL OUTPUTS END'''
if start in text and end in text:
    before = text.split(start, 1)[0].rstrip()
    after = text.split(end, 1)[1].lstrip()
    text = before + '\n\n' + block + ('\n\n' + after if after else '') + '\n'
else:
    text = text.rstrip() + '\n\n' + block + '\n'
path.write_text(text, encoding='utf-8')
PY_GITIGNORE

chmod 0755 tools/era63d_market_technical_runtime_v1.py tests/test_era63d_market_technical_runtime_v1.py tools/technical_center_live_producer_v1.py
chmod 0644 config/era63d_market_technical_runtime_v1.json systemd_drafts/tokenoskobi-era63d-market-technical.service systemd_drafts/tokenoskobi-era63d-market-technical.timer

python3 -m py_compile tools/era63d_market_technical_runtime_v1.py tools/technical_center_live_producer_v1.py tests/test_era63d_market_technical_runtime_v1.py
python3 -m json.tool config/era63d_market_technical_runtime_v1.json >/dev/null
python3 tests/test_era63b_paper_trading_core_v1.py
python3 tests/test_era63c_technical_dex_execution_v1.py
python3 tests/test_era63d_market_technical_runtime_v1.py
python3 tools/era63_technical_dex_execution_v1.py \
  --input data/replay/era63c_technical_dex_execution_replay_matrix_v1.json \
  --config config/era63c_technical_dex_execution_v1.json \
  --matrix \
  --output /tmp/era63d_era63c_regression_matrix.json
python3 <<'PY_MATRIX'
import json
from pathlib import Path
value = json.loads(Path('/tmp/era63d_era63c_regression_matrix.json').read_text(encoding='utf-8'))
assert value['scenario_count'] == 8
assert value['pass_count'] == 8
print('ERA63C_REPLAY_REGRESSION=8/8_PASS')
PY_MATRIX

if command -v systemd-analyze >/dev/null 2>&1; then
  systemd-analyze verify \
    systemd_drafts/tokenoskobi-era63d-market-technical.service \
    systemd_drafts/tokenoskobi-era63d-market-technical.timer >/tmp/era63d_systemd_verify.log 2>&1 || {
      cat /tmp/era63d_systemd_verify.log
      false
    }
fi

python3 tools/era63d_market_technical_runtime_v1.py --config config/era63d_market_technical_runtime_v1.json
python3 tools/technical_center_live_producer_v1.py
python3 <<'PY_LIVE'
import json
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
snapshot = json.loads((root / 'runtime/era63d/latest_real_market_technical_snapshot_v1.json').read_text(encoding='utf-8'))
panel = json.loads((root / 'active_panel_8096/current/data/technical_center_live_readmodel_v1.json').read_text(encoding='utf-8'))
assert snapshot['schema'] == 'tokenoskobi.era63d.real_market_technical_runtime.v1'
assert snapshot['provider'] == 'GECKOTERMINAL_KEYLESS_PUBLIC'
assert snapshot['network'] == 'bsc'
assert snapshot['successful_pool_count'] >= 1
assert snapshot['authority']['paper_runtime'] is False
assert snapshot['authority']['real_trade'] is False
assert panel['decision'] == 'REAL_MARKET_TECHNICAL_OBSERVATION_ACTIVE'
assert panel['source_count'] >= 1
assert all(value is False for value in panel['authority'].values())
print(f"REAL_PROVIDER_CYCLE=PASS:{snapshot['successful_pool_count']}_POOLS")
PY_LIVE

install -m 0644 systemd_drafts/tokenoskobi-era63d-market-technical.service "/etc/systemd/system/$SERVICE_NAME"
install -m 0644 systemd_drafts/tokenoskobi-era63d-market-technical.timer "/etc/systemd/system/$TIMER_NAME"
SYSTEMD_TOUCHED=1
systemctl daemon-reload
systemctl start "$SERVICE_NAME"
systemctl enable --now "$TIMER_NAME"
[[ "$(systemctl is-enabled "$TIMER_NAME")" == "enabled" ]]
[[ "$(systemctl is-active "$TIMER_NAME")" == "active" ]]
[[ "$(systemctl show -p Result --value "$SERVICE_NAME")" == "success" ]]

export ERA63D_TIMER_ENABLED="$(systemctl is-enabled "$TIMER_NAME")"
export ERA63D_TIMER_ACTIVE="$(systemctl is-active "$TIMER_NAME")"
export ERA63D_SERVICE_RESULT="$(systemctl show -p Result --value "$SERVICE_NAME")"
export ERA63D_BASE_HEAD="$BASE_HEAD"

python3 <<'PY_CANONICAL'
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
NOW = datetime.now(timezone.utc).isoformat()
STAGE = "ERA63D_REAL_MARKET_AND_TECHNICAL_RUNTIME_BINDING"
STATUS = "READONLY_REAL_MARKET_TECHNICAL_RUNTIME_ACTIVE"
NEXT = "ERA63E_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE"
CONTROL = "data/control/era63d_real_market_technical_runtime_binding_v1.json"
REPORT = "reports/LATEST_ERA63D_REAL_MARKET_TECHNICAL_RUNTIME_BINDING.md"
SNAPSHOT = ROOT / "runtime/era63d/latest_real_market_technical_snapshot_v1.json"
TIMER_ENABLED = os.environ.get("ERA63D_TIMER_ENABLED", "unknown")
TIMER_ACTIVE = os.environ.get("ERA63D_TIMER_ACTIVE", "unknown")
SERVICE_RESULT = os.environ.get("ERA63D_SERVICE_RESULT", "unknown")
BASE_HEAD = os.environ.get("ERA63D_BASE_HEAD", "")


def load(relative: str, default=None):
    path = ROOT / relative
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save(relative: str, value: Any) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write(relative: str, text: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def upsert(relative: str, marker: str, body: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    block = f"{start}\n{body.rstrip()}\n{end}"
    if start in text and end in text:
        before = text.split(start, 1)[0].rstrip()
        after = text.split(end, 1)[1].lstrip()
        text = before + "\n\n" + block + ("\n\n" + after if after else "")
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8")


def find_id(value: Any, target: str):
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


snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
if snapshot.get("schema") != "tokenoskobi.era63d.real_market_technical_runtime.v1":
    raise RuntimeError("ERA63D snapshot schema mismatch")
if int(snapshot.get("successful_pool_count", 0)) < 1:
    raise RuntimeError("ERA63D real successful pool count is zero")
authority = snapshot.get("authority") or {}
for key in ("paper_runtime", "paper_position_write", "real_trade", "wallet", "signing", "real_order", "broadcast"):
    if authority.get(key) is not False:
        raise RuntimeError(f"ERA63D authority must remain false: {key}")

pool_summaries = []
for item in snapshot["items"]:
    result = item["engine_result"]
    selected = result["execution_probe"]["selected"]
    pool_summaries.append({
        "pool_address": item["pool_address"],
        "pool_name": item["pool_name"],
        "liquidity_usd": item["liquidity_usd"],
        "volume_h24_usd": item["volume_h24_usd"],
        "engine_action": item["runtime_guard"]["engine_action"],
        "runtime_status": item["runtime_guard"]["status"],
        "price_usd": result["technical"]["price"],
        "directional_score": result["technical"]["directional_score"],
        "confidence": result["technical"]["confidence"],
        "consensus": result["technical"]["consensus"],
        "gross_edge_bps": result["edge"]["gross_edge_bps"],
        "probe_net_edge_bps": result["edge"]["probe_net_edge_bps"],
        "sandwich_probability": selected["sandwich"]["probability"],
        "expected_sandwich_loss_bps": selected["sandwich"]["expected_loss_bps"],
        "price_impact_bps": selected["quote"]["price_impact_bps"],
        "execution_risk_score": selected["risk_score"],
        "paper_action": "DISABLED",
        "blocks": item["runtime_guard"]["blocks"],
    })

control = {
    "schema": "tokenoskobi.era63d.real_market_technical_runtime_binding.v1",
    "era": "ERA63",
    "stage": STAGE,
    "status": STATUS,
    "bound_at_utc": NOW,
    "baseline_head": BASE_HEAD,
    "provider": {
        "name": snapshot["provider"],
        "base_url": snapshot["provider_base_url"],
        "network": snapshot["network"],
        "mode": "KEYLESS_PUBLIC_LOW_VOLUME_READ_ONLY",
        "request_count_last_cycle": snapshot["request_count"],
    },
    "real_data": {
        "verified": True,
        "candidate_count": snapshot["candidate_count"],
        "successful_pool_count": snapshot["successful_pool_count"],
        "generated_at_utc": snapshot["generated_at_utc"],
        "pool_summaries": pool_summaries,
    },
    "runtime": {
        "engine": "tools/era63d_market_technical_runtime_v1.py",
        "technical_engine": "tools/era63_technical_dex_execution_v1.py",
        "technical_center_bridge": "tools/technical_center_live_producer_v1.py",
        "config": "config/era63d_market_technical_runtime_v1.json",
        "service": "tokenoskobi-era63d-market-technical.service",
        "timer": "tokenoskobi-era63d-market-technical.timer",
        "timer_enabled": TIMER_ENABLED,
        "timer_active": TIMER_ACTIVE,
        "service_result": SERVICE_RESULT,
        "interval_minutes": 15,
        "dynamic_state": "runtime/era63d",
        "panel_readmodel": "active_panel_8096/current/data/technical_center_live_readmodel_v1.json",
    },
    "verification": {
        "era63b_regression": "13/13_PASS",
        "era63c_regression": "21/21_PASS",
        "era63d_tests": "17/17_PASS",
        "combined_static_and_regression": "51/51_PASS",
        "real_provider_cycle": "PASS",
        "technical_center_bridge": "PASS",
        "systemd_timer": "ACTIVE_ENABLED",
    },
    "known_fail_closed_limits": [
        "TOKEN_TAX_DIRECT_SOURCE_NOT_BOUND",
        "DIRECT_MEMPOOL_MEASUREMENT_NOT_BOUND",
        "POOL_RESERVES_ESTIMATED_FROM_TVL_AND_BASE_PRICE",
        "COORDINATED_WALLET_ONCHAIN_WHALE_NEWS_INTELLIGENCE_NOT_BOUND",
        "PAPER_RUNTIME_DISABLED",
    ],
    "authority": {
        "observation_runtime": True,
        "paper_runtime": False,
        "paper_position_write": False,
        "real_trade": False,
        "wallet": False,
        "signing": False,
        "real_order": False,
        "broadcast": False,
        "risk_engine_veto": True,
        "system_may_expand_policy": False,
    },
    "sha256": {
        "runtime": sha256("tools/era63d_market_technical_runtime_v1.py"),
        "config": sha256("config/era63d_market_technical_runtime_v1.json"),
        "tests": sha256("tests/test_era63d_market_technical_runtime_v1.py"),
        "service": sha256("systemd_drafts/tokenoskobi-era63d-market-technical.service"),
        "timer": sha256("systemd_drafts/tokenoskobi-era63d-market-technical.timer"),
    },
    "next_safe_step": NEXT,
}
save(CONTROL, control)

runtime = load("PROJECT_RUNTIME.json", {})
if not isinstance(runtime, dict):
    raise TypeError("PROJECT_RUNTIME.json must be object")
runtime.update({
    "current_version": "V4",
    "current_stage": STAGE,
    "current_status": STATUS,
    "last_completed": STAGE,
    "last_result": "REAL_BSC_MARKET_TECHNICAL_OBSERVATION_AND_TIMER_ACTIVE",
    "next_safe_step": NEXT,
    "updated_at_utc": NOW,
})
runtime["authority"] = {
    "paper_trade": "DISABLED_PENDING_COORDINATED_INTELLIGENCE",
    "paper_order_authority": "SIMULATION_ENGINE_ONLY_NO_RUNTIME_WRITE",
    "paper_position_authority": "SIMULATION_ENGINE_ONLY_NO_RUNTIME_WRITE",
    "paper_unattended_execution": "NOT_ALLOWED_YET",
    "human_per_paper_trade_approval": False,
    "real_trade_authority": 0,
    "real_wallet_authority": 0,
    "real_signing_authority": 0,
    "real_order_authority": 0,
    "live_trade": "DISABLED",
    "risk_engine_veto": True,
    "system_may_not_expand_policy": True,
}
runtime["open_risks"] = [
    "ERA63E_REQUIRED:NATURAL_TIMER_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE",
    "ERA64_REQUIRED:SUCCESSFUL_WALLET_STATS_AND_CLUSTERING",
    "ERA65_REQUIRED:ONCHAIN_AND_CEX_TO_DEX_WHALE_FLOW",
    "ERA66_REQUIRED:NEWS_AIRDROP_ICO_IDO_LAUNCH_INTELLIGENCE",
    "ERA67_REQUIRED:COORDINATED_MULTI_INTELLIGENCE_FUSION",
    "ERA68_REQUIRED:UNATTENDED_COORDINATED_PAPER_RUNTIME",
    "DATA_GAP:TOKEN_TAX_DIRECT_SOURCE",
    "DATA_GAP:DIRECT_MEMPOOL_MEASUREMENT",
]
work = runtime.setdefault("work_unit", {})
work.update({
    "id": "ERA63_ACCELERATED_PAPER_TRADING_CORE",
    "title": "Technical Analysis and DEX Execution Foundation",
    "status": STATUS,
    "next_substep": NEXT,
    "paper_trade_currently": "DISABLED_PENDING_COORDINATED_INTELLIGENCE",
    "observation_runtime": "ACTIVE_READ_ONLY",
    "live_trade": "DISABLED",
    "wallet_authority": 0,
    "signing_authority": 0,
    "real_order_create_authority": 0,
})
completed = work.setdefault("completed_substeps", [])
for value in (
    "ERA63A_ACCELERATED_PAPER_TRADING_GAP_AUDIT",
    "ERA63B_ACCELERATED_PAPER_TRADING_CORE_BUILD",
    "ERA63C_TECHNICAL_DEX_EXECUTION_VALIDATION",
    STAGE,
):
    if value not in completed:
        completed.append(value)
runtime["era63d_runtime"] = control
pointer = runtime.setdefault("canonical_runtime_pointer", {})
pointer.update({
    "current_version_line": "V4",
    "current_era": "ERA63",
    "current_stage": STAGE,
    "era63d_real_market_runtime_active": True,
    "paper_runtime_enabled": False,
    "next_safe_step": NEXT,
})
runtime["recent_event"] = {"event": STAGE, "result": STATUS, "timestamp": NOW}
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
    "last_result": "REAL_BSC_MARKET_TECHNICAL_RUNTIME_ACTIVE",
    "next_safe_step": NEXT,
    "updated_at_utc": NOW,
    "observation_runtime_enabled": True,
    "paper_runtime_enabled": False,
    "live_trade": "DISABLED",
    "era63d_control_artifact": CONTROL,
    "era63d_timer_enabled": TIMER_ENABLED,
    "era63d_timer_active": TIMER_ACTIVE,
})
save("data/control/latest_tk_machine_state.json", machine)

history = load("PROJECT_HISTORY.json", {})
if not isinstance(history, dict):
    raise TypeError("PROJECT_HISTORY.json must be object")
events = history.setdefault("events", [])
events[:] = [
    event for event in events
    if not (isinstance(event, dict) and event.get("event_id") == STAGE)
]
events.append({
    "event_id": STAGE,
    "event": "REAL_BSC_MARKET_TECHNICAL_READONLY_RUNTIME_BINDING",
    "era": "ERA63",
    "status": STATUS,
    "provider": snapshot["provider"],
    "successful_pool_count": snapshot["successful_pool_count"],
    "tests": "51/51_PASS",
    "artifact": CONTROL,
    "timer_enabled": TIMER_ENABLED,
    "timer_active": TIMER_ACTIVE,
    "paper_runtime_enabled": False,
    "real_financial_authority": 0,
    "next_safe_step": NEXT,
    "timestamp_utc": NOW,
})
history["updated_at_utc"] = NOW
save("PROJECT_HISTORY.json", history)

master = load("data/tokenoskobi_v1_v8_master_era_roadmap.json", {})
if not isinstance(master, dict):
    raise TypeError("Master roadmap must be object")
v4 = find_id(master, "V4")
era63 = find_id(master, "ERA63")
if v4 is None or era63 is None:
    raise RuntimeError("V4 or ERA63 missing")
v4.update({
    "title": "Coordinated Intelligence and Paper-Trading Proving Ground",
    "purpose": (
        "Complete real technical execution, successful-wallet intelligence, onchain and "
        "CEX-to-DEX whale flow, launch/news intelligence, coordinated fusion and then "
        "unattended zero-real-funds paper runtime."
    ),
    "status": "ACTIVE",
})
era63.update({
    "title": "Technical Analysis and DEX Execution Foundation",
    "actual_title": "Technical Analysis and DEX Execution Foundation",
    "status": STATUS,
    "opened": True,
    "active_stage": STAGE,
    "next_safe_step": NEXT,
    "real_market_runtime_active": True,
    "paper_runtime_enabled": False,
    "control_artifact": CONTROL,
})
substeps = era63.setdefault("substeps", {})
if isinstance(substeps, dict):
    substeps.update({
        "ERA63A": "REAL_GAP_AUDIT_COMPLETED",
        "ERA63B": "MINIMUM_PAPER_CORE_BUILD_COMPLETED",
        "ERA63C": "TECHNICAL_DEX_EXECUTION_VALIDATED_34_OF_34_AND_8_OF_8",
        "ERA63D": "REAL_BSC_MARKET_TECHNICAL_READONLY_RUNTIME_ACTIVE",
        "ERA63E": "NATURAL_TIMER_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE_NEXT",
    })
sequence = {
    "ERA64": (
        "Successful Wallet Intelligence and Statistical Performance",
        "Measure win rate, ROI, median return, drawdown, risk-adjusted performance, consistency, entry/exit quality, funding relationships, sub-wallets and evidence-backed clusters.",
    ),
    "ERA65": (
        "Onchain and CEX-to-DEX Whale Flow Intelligence",
        "Track CEX-to-DEX and DEX-to-CEX flow, successful-wallet clusters, sub-wallet distribution, bridge, deployer, holder, liquidity and post-flow price effects.",
    ),
    "ERA66": (
        "News, Airdrop, ICO/IDO and Launch Intelligence",
        "Track trusted crypto news, listing/delisting, airdrop, snapshot, ICO, IDO, launchpad, TGE, unlock, vesting, hack, rug and protocol events with identity and freshness controls.",
    ),
    "ERA67": (
        "Coordinated Multi-Intelligence Fusion",
        "Align technical, wallet, onchain, whale, news and execution evidence by token, pair, chain, wallet cluster, event and timestamp before Risk Engine and paper decision.",
    ),
    "ERA68": (
        "Unattended Coordinated Paper-Trading Runtime",
        "Run bounded zero-real-funds paper positions only after all coordinated intelligence lines are bound, measured and governed by Risk Engine veto.",
    ),
}
for era_id, (title, purpose) in sequence.items():
    record = find_id(master, era_id)
    if record is not None:
        record.update({
            "title": title,
            "actual_title": title,
            "purpose": purpose,
            "status": "PLANNED_LOCKED_SEQUENCE",
            "opened": False,
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
master["v4_locked_execution_sequence"] = [
    "ERA63_TECHNICAL_ANALYSIS_AND_DEX_EXECUTION",
    "ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING",
    "ERA65_ONCHAIN_AND_CEX_TO_DEX_WHALE_FLOW",
    "ERA66_NEWS_AIRDROP_ICO_IDO_AND_LAUNCH_INTELLIGENCE",
    "ERA67_COORDINATED_MULTI_INTELLIGENCE_FUSION",
    "ERA68_UNATTENDED_COORDINATED_PAPER_RUNTIME",
]
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
ERA63D=REAL_BSC_MARKET_TECHNICAL_READONLY_RUNTIME=ACTIVE_VERIFIED
ERA63E=NATURAL_TIMER_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE=NEXT
```

ERA63D reads real BSC pool and OHLCV data through a bounded keyless provider runtime every 15 minutes. It writes technical observation and panel readmodels only.

Direct token-tax and direct mempool measurements remain fail-closed data gaps. Paper position writes and all real financial authority remain disabled.

ERA69-ERA80 remain reserved only for evidence-proven gaps.
"""
write("03_ROADMAP.md", roadmap_text)

atlas_block = f"""## ERA63D REAL MARKET TECHNICAL RUNTIME CONTRACT

```text
PROVIDER=GECKOTERMINAL_KEYLESS_PUBLIC
FIRST_CHAIN=BSC
MODE=READ_ONLY_OBSERVATION
INTERVAL=15_MINUTES
REAL_OHLCV=true
REAL_POOL_LIQUIDITY=true
DIRECT_TOKEN_TAX=false
DIRECT_MEMPOOL=false
PAPER_RUNTIME=false
LIVE_TRADE=DISABLED
NEXT={NEXT}
```

The runtime may calculate technical and DEX execution evidence, but unknown token tax, proxy-only mempool data, estimated reserves and missing coordinated intelligence block paper action.
"""
upsert("05_ATLAS.md", "ERA63D_REAL_MARKET_TECHNICAL_RUNTIME", atlas_block)

master_state = f"""# 06 PROJECT MASTER STATE - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE={STAGE}
CURRENT_STATUS={STATUS}
NEXT_SAFE_STEP={NEXT}

## ACTIVE RUNTIME

- Provider: `GECKOTERMINAL_KEYLESS_PUBLIC`
- Chain: `BSC`
- Cycle: `15_MINUTES`
- Successful real pools in activation cycle: `{snapshot['successful_pool_count']}`
- Timer: `{TIMER_ENABLED}/{TIMER_ACTIVE}`
- Technical panel readmodel: active

## VERIFIED FOUNDATION

- ERA63B regression: `13/13_PASS`
- ERA63C execution tests: `21/21_PASS`
- ERA63D runtime tests: `17/17_PASS`
- Combined: `51/51_PASS`
- ERA63C replay: `8/8_PASS`
- Real provider cycle: `PASS`

## FAIL-CLOSED LIMITS

- Direct token-tax source not bound
- Direct mempool measurement not bound
- Pool reserves estimated from TVL and price
- Wallet, onchain, whale and launch/news coordination not bound

## AUTHORITY

OBSERVATION_RUNTIME=true
PAPER_RUNTIME=false
PAPER_POSITION_WRITE=false
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

ERA63D bound a real BSC market and technical-analysis observation runtime.

Evidence:

- `{CONTROL}`
- `{REPORT}`
- Dynamic latest snapshot: `runtime/era63d/latest_real_market_technical_snapshot_v1.json`
- Dynamic panel readmodel: `active_panel_8096/current/data/technical_center_live_readmodel_v1.json`

The timer runs every 15 minutes. It is observation-only. It cannot create paper positions, real orders, wallet connections, signatures or broadcasts.

ERA63E must verify natural timer cycles, freshness, provider failure behavior and panel continuity, then close the technical foundation before ERA64 successful-wallet statistics and clustering.
"""
write("07_PROJECT_HANDOFF.md", handoff)

report_lines = [
    "# ERA63D REAL MARKET AND TECHNICAL RUNTIME BINDING",
    "",
    f"STATUS={STATUS}",
    f"PROVIDER={snapshot['provider']}",
    f"NETWORK={snapshot['network']}",
    f"SUCCESSFUL_POOLS={snapshot['successful_pool_count']}",
    "TESTS=51/51_PASS",
    "PAPER_RUNTIME=false",
    "LIVE_TRADE=DISABLED",
    f"TIMER={TIMER_ENABLED}/{TIMER_ACTIVE}",
    f"NEXT_SAFE_STEP={NEXT}",
    "",
    "## Real activation-cycle pools",
    "",
]
for item in pool_summaries:
    report_lines.extend([
        f"- `{item['pool_name']}` `{item['pool_address']}`",
        f"  - liquidity_usd: `{item['liquidity_usd']}`",
        f"  - volume_h24_usd: `{item['volume_h24_usd']}`",
        f"  - engine_action: `{item['engine_action']}`",
        f"  - runtime_status: `{item['runtime_status']}`",
        f"  - paper_action: `DISABLED`",
    ])
report_lines.extend([
    "",
    "## Fail-closed limits",
    "",
    "- Direct token-tax source is not bound.",
    "- Direct mempool measurement is not bound.",
    "- Pool reserves are estimated from TVL and price.",
    "- Coordinated wallet/onchain/whale/news intelligence is not bound.",
])
write(REPORT, "\n".join(report_lines))

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
REPORT={REPORT}
REAL_MARKET_PROVIDER={snapshot['provider']}
REAL_POOL_COUNT={snapshot['successful_pool_count']}
OBSERVATION_TIMER={TIMER_ENABLED}/{TIMER_ACTIVE}
PAPER_RUNTIME=false
LIVE_TRADE=DISABLED

LOCKED_CONTINUATION=ERA63E→ERA64→ERA65→ERA66→ERA67→ERA68
""",
)

almanac_block = f"""## ERA63D REAL MARKET TECHNICAL RUNTIME BINDING

- Status: `{STATUS}`
- Provider: `{snapshot['provider']}`
- Chain: `BSC`
- Real pools: `{snapshot['successful_pool_count']}`
- Timer: `{TIMER_ENABLED}/{TIMER_ACTIVE}`
- Tests: `51/51_PASS`
- Paper runtime: `false`
- Real financial authority: `0`
- Artifact: `{CONTROL}`
- Next: `{NEXT}`
- UTC: `{NOW}`"""
upsert("04_ALMANAC.md", "ERA63D_REAL_MARKET_TECHNICAL_RUNTIME", almanac_block)

print("ERA63D_CANONICAL_SYNC=PASS")
PY_CANONICAL

python3 -m json.tool PROJECT_RUNTIME.json >/dev/null
python3 -m json.tool PROJECT_HISTORY.json >/dev/null
python3 -m json.tool data/tokenoskobi_v1_v8_master_era_roadmap.json >/dev/null
python3 -m json.tool data/control/latest_tk_machine_state.json >/dev/null
python3 -m json.tool data/control/era63d_real_market_technical_runtime_binding_v1.json >/dev/null
python3 -m json.tool data/control/n16d_technical_center_live_producer_result_v1.json >/dev/null

git diff --check
git add -f -- "${ALL_FILES[@]}"
git diff --cached --check
! git diff --cached --quiet

git commit -m "ERA63D: bind real BSC market technical observation runtime"
COMMIT_CREATED=1
HEAD="$(git rev-parse HEAD)"
git push origin main
REMOTE_PUSHED=1
git fetch origin main --quiet
[[ "$(git rev-parse origin/main)" == "$HEAD" ]]
[[ "$(git ls-remote origin refs/heads/main | awk '{print $1}')" == "$HEAD" ]]
[[ -z "$(git status --porcelain=v1)" ]]
[[ "$(systemctl is-enabled "$TIMER_NAME")" == "enabled" ]]
[[ "$(systemctl is-active "$TIMER_NAME")" == "active" ]]

trap - ERR

echo "ERA63D_STATUS=READONLY_REAL_MARKET_TECHNICAL_RUNTIME_ACTIVE"
echo "PROVIDER=GECKOTERMINAL_KEYLESS_PUBLIC"
echo "NETWORK=BSC"
echo "TESTS=51/51_PASS"
echo "ERA63C_REPLAY=8/8_PASS"
echo "REAL_PROVIDER_CYCLE=PASS"
echo "TIMER=ENABLED_ACTIVE_15_MINUTES"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=ERA63E_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE"
