#!/usr/bin/env python3
"""Tokenoskobi Product Slice 02 read-only single-token decision packet."""
from __future__ import annotations

import json
import math
import re
import sqlite3
import statistics
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
UI_FILE = ROOT / "web/product_slice_02/index.html"
HOST = "127.0.0.1"
PORT = 8098
ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
PUBLIC_RPCS = (
    "https://bsc-dataseed.bnbchain.org",
    "https://bsc-dataseed-public.bnbchain.org",
    "https://bsc-dataseed.nariox.org",
    "https://bsc-dataseed.defibit.io",
)
DB_CANDIDATES = (
    ROOT / "data/tokenoskobi_clean_v1.sqlite",
    ROOT / "data/tokenoskobi_v1.sqlite",
    ROOT / "data/tokenoskobi.sqlite",
    ROOT / "tokenoskobi.sqlite",
)
SELECTORS = {
    "name": "0x06fdde03",
    "symbol": "0x95d89b41",
    "decimals": "0x313ce567",
    "totalSupply": "0x18160ddd",
}
AUTHORITY = {
    "read_only": True,
    "ai_authority": 0,
    "trade_authority": 0,
    "wallet_authority": 0,
    "signing_authority": 0,
    "order_create_authority": 0,
    "real_financial_authority": 0,
    "paper_trade": "DISABLED",
    "live_trade": "DISABLED",
    "broadcast": False,
}


class ProductError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def read_alchemy_url() -> str | None:
    path = ROOT / ".secrets/alchemy_bnb.env"
    if not path.exists():
        return None
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("BSC_ALCHEMY_URL="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if re.match(r"^https://bnb-mainnet\.g\.alchemy\.com/v2/[A-Za-z0-9_-]+$", value):
                    return value
    except OSError:
        return None
    return None


def redact_provider(url: str) -> str:
    if "/v2/" in url:
        return url.split("/v2/", 1)[0] + "/v2/<REDACTED>"
    return urllib.parse.urlsplit(url).netloc


def http_json(url: str, *, data: bytes | None = None, timeout: float = 8.0) -> tuple[dict[str, Any], float]:
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Tokenoskobi-Product-Slice-02/1.0",
        },
        method="POST" if data is not None else "GET",
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload, round((time.monotonic() - started) * 1000.0, 2)


def rpc_call(url: str, method: str, params: list[Any]) -> tuple[Any, float]:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
    payload, latency = http_json(url, data=body)
    if payload.get("error"):
        raise ProductError(f"RPC_ERROR:{payload['error']}")
    if "result" not in payload:
        raise ProductError("RPC_RESULT_MISSING")
    return payload["result"], latency


def provider_chain() -> list[tuple[str, str]]:
    providers: list[tuple[str, str]] = []
    alchemy = read_alchemy_url()
    if alchemy:
        providers.append(("alchemy", alchemy))
    providers.extend(("public_rpc", url) for url in PUBLIC_RPCS)
    return providers


def choose_rpc() -> tuple[str, str, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    for kind, url in provider_chain():
        try:
            chain_id, chain_latency = rpc_call(url, "eth_chainId", [])
            block_hex, block_latency = rpc_call(url, "eth_blockNumber", [])
            if int(chain_id, 16) != 56:
                raise ProductError(f"WRONG_CHAIN:{chain_id}")
            attempts.append({
                "provider": kind,
                "endpoint": redact_provider(url),
                "ok": True,
                "chain_id": 56,
                "latest_block": int(block_hex, 16),
                "latency_ms": round(chain_latency + block_latency, 2),
            })
            return kind, url, attempts
        except Exception as exc:
            attempts.append({
                "provider": kind,
                "endpoint": redact_provider(url),
                "ok": False,
                "error": f"{type(exc).__name__}:{str(exc)[:180]}",
            })
    raise ProductError("NO_BSC_RPC_AVAILABLE:" + json.dumps(attempts, ensure_ascii=False))


def decode_abi_string(hex_value: str | None) -> str | None:
    if not hex_value or hex_value == "0x":
        return None
    try:
        raw = bytes.fromhex(hex_value[2:] if hex_value.startswith("0x") else hex_value)
    except ValueError:
        return None
    if len(raw) == 32:
        text = raw.rstrip(b"\x00").decode("utf-8", errors="ignore").strip()
        return text or None
    if len(raw) >= 64:
        try:
            offset = int.from_bytes(raw[:32], "big")
            if offset + 32 > len(raw):
                return None
            length = int.from_bytes(raw[offset:offset + 32], "big")
            data = raw[offset + 32:offset + 32 + length]
            text = data.decode("utf-8", errors="ignore").strip()
            return text or None
        except Exception:
            return None
    return None


def decode_uint(hex_value: str | None) -> int | None:
    if not hex_value or hex_value == "0x":
        return None
    try:
        return int(hex_value, 16)
    except ValueError:
        return None


def contract_snapshot(address: str) -> dict[str, Any]:
    kind, url, attempts = choose_rpc()
    code, code_latency = rpc_call(url, "eth_getCode", [address, "latest"])
    calls: dict[str, Any] = {}
    call_latencies: dict[str, float] = {}
    for name, selector in SELECTORS.items():
        try:
            value, latency = rpc_call(url, "eth_call", [{"to": address, "data": selector}, "latest"])
            calls[name] = value
            call_latencies[name] = latency
        except Exception as exc:
            calls[name] = None
            call_latencies[name] = -1.0
            attempts.append({"provider": kind, "method": f"eth_call:{name}", "ok": False, "error": str(exc)[:180]})
    name = decode_abi_string(calls["name"])
    symbol = decode_abi_string(calls["symbol"])
    decimals = decode_uint(calls["decimals"])
    total_supply_raw = decode_uint(calls["totalSupply"])
    total_supply = None
    if total_supply_raw is not None and decimals is not None and 0 <= decimals <= 36:
        total_supply = total_supply_raw / (10 ** decimals)
    return {
        "address": address,
        "provider": kind,
        "provider_endpoint": redact_provider(url),
        "provider_attempts": attempts,
        "code_present": bool(code and code != "0x"),
        "code_bytes": max(0, (len(code) - 2) // 2) if isinstance(code, str) else 0,
        "code_latency_ms": code_latency,
        "name": name,
        "symbol": symbol,
        "decimals": decimals,
        "total_supply_raw": str(total_supply_raw) if total_supply_raw is not None else None,
        "total_supply": total_supply,
        "call_latencies_ms": call_latencies,
    }


def gecko_pool_snapshot(address: str) -> dict[str, Any]:
    url = f"https://api.geckoterminal.com/api/v2/networks/bsc/tokens/{address}/pools?page=1"
    try:
        payload, latency = http_json(url, timeout=10.0)
    except Exception as exc:
        return {"available": False, "source": "geckoterminal", "error": f"{type(exc).__name__}:{str(exc)[:200]}", "pools": []}
    pools = []
    for item in payload.get("data") or []:
        attrs = item.get("attributes") or {}
        reserve = finite_float(attrs.get("reserve_in_usd"))
        volume = attrs.get("volume_usd") or {}
        changes = attrs.get("price_change_percentage") or {}
        transactions = attrs.get("transactions") or {}
        pool_address = attrs.get("address")
        if not pool_address:
            ident = str(item.get("id") or "")
            pool_address = ident.split("_", 1)[-1] if "_" in ident else ident
        relationships = item.get("relationships") or {}
        base_id = str((relationships.get("base_token") or {}).get("data", {}).get("id") or "").lower()
        quote_id = str((relationships.get("quote_token") or {}).get("data", {}).get("id") or "").lower()
        token_side = "quote" if address.lower() in quote_id and address.lower() not in base_id else "base"
        token_price = attrs.get("quote_token_price_usd") if token_side == "quote" else attrs.get("base_token_price_usd")
        pools.append({
            "pool_address": pool_address,
            "name": attrs.get("name"),
            "dex": (relationships.get("dex") or {}).get("data", {}).get("id"),
            "token_side": token_side,
            "token_price_usd": finite_float(token_price),
            "base_token_price_usd": finite_float(attrs.get("base_token_price_usd")),
            "quote_token_price_usd": finite_float(attrs.get("quote_token_price_usd")),
            "reserve_usd": reserve,
            "fdv_usd": finite_float(attrs.get("fdv_usd")),
            "market_cap_usd": finite_float(attrs.get("market_cap_usd")),
            "volume_usd": {k: finite_float(v) for k, v in volume.items()},
            "price_change_percentage": {k: finite_float(v) for k, v in changes.items()},
            "transactions": transactions,
            "pool_created_at": attrs.get("pool_created_at"),
        })
    pools.sort(key=lambda p: p.get("reserve_usd") or 0.0, reverse=True)
    return {
        "available": bool(pools),
        "source": "geckoterminal",
        "latency_ms": latency,
        "pool_count": len(pools),
        "pools": pools[:10],
        "primary_pool": pools[0] if pools else None,
    }


def gecko_ohlcv(pool_address: str | None, token_side: str = "base") -> dict[str, Any]:
    if not pool_address or not ADDRESS_RE.match(pool_address):
        return {"available": False, "error": "POOL_ADDRESS_UNAVAILABLE", "timeframes": {}}
    side = "quote" if token_side == "quote" else "base"
    endpoints = {
        "minute": f"https://api.geckoterminal.com/api/v2/networks/bsc/pools/{pool_address}/ohlcv/minute?aggregate=1&limit=300&currency=usd&token={side}",
        "day": f"https://api.geckoterminal.com/api/v2/networks/bsc/pools/{pool_address}/ohlcv/day?aggregate=1&limit=3&currency=usd&token={side}",
    }
    series: dict[str, list[list[Any]]] = {}
    errors: list[str] = []
    latencies: dict[str, float] = {}
    for key, url in endpoints.items():
        try:
            payload, latency = http_json(url, timeout=10.0)
            rows = (((payload.get("data") or {}).get("attributes") or {}).get("ohlcv_list") or [])
            clean = [row for row in rows if isinstance(row, list) and len(row) >= 6]
            clean.sort(key=lambda row: int(row[0]))
            series[key] = clean
            latencies[key] = latency
        except Exception as exc:
            series[key] = []
            errors.append(f"{key}:{type(exc).__name__}:{str(exc)[:140]}")
    minute = series.get("minute") or []
    day = series.get("day") or []

    def frame(rows: list[list[Any]], bars: int) -> dict[str, Any]:
        if len(rows) <= bars:
            return {"status": "VERI_YETERSIZ", "required_bars": bars + 1, "available_bars": len(rows)}
        current = finite_float(rows[-1][4])
        previous = finite_float(rows[-1 - bars][4])
        if current is None or previous in (None, 0):
            return {"status": "VERI_YETERSIZ", "available_bars": len(rows)}
        closes = [finite_float(row[4]) for row in rows[-min(len(rows), max(bars + 1, 20)):]]
        closes = [value for value in closes if value is not None]
        returns = []
        for left, right in zip(closes, closes[1:]):
            if left:
                returns.append((right / left - 1.0) * 100.0)
        change = (current / previous - 1.0) * 100.0
        return {
            "status": "OK",
            "change_pct": round(change, 4),
            "trend": "YUKARI" if change > 0.1 else "ASAGI" if change < -0.1 else "YATAY",
            "volatility_pct": round(statistics.pstdev(returns), 4) if len(returns) >= 2 else None,
            "last_close_usd": current,
            "available_bars": len(rows),
        }

    timeframes = {
        "1m": frame(minute, 1),
        "5m": frame(minute, 5),
        "15m": frame(minute, 15),
        "1h": frame(minute, 60),
        "4h": frame(minute, 240),
        "1d": frame(day, 1),
    }
    return {
        "available": any(value.get("status") == "OK" for value in timeframes.values()),
        "source": "geckoterminal_ohlcv",
        "latency_ms": latencies,
        "errors": errors,
        "minute_bars": len(minute),
        "day_bars": len(day),
        "timeframes": timeframes,
    }


def sql_identifier(value: str) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value):
        raise ProductError("UNSAFE_SQL_IDENTIFIER")
    return '"' + value + '"'


def news_context(address: str, symbol: str | None, name: str | None) -> dict[str, Any]:
    db = next((candidate for candidate in DB_CANDIDATES if candidate.exists() and candidate.is_file()), None)
    if db is None:
        return {"available": False, "status": "VERI_YETERSIZ", "error": "NEWS_DB_NOT_FOUND"}
    result: dict[str, Any] = {"available": True, "database": str(db.relative_to(ROOT)), "tables": {}, "matches": []}
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        tables = [row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        target_tables = [table for table in tables if table in {
            "news_raw_feed_events", "news_token_match_events", "news_signal_events", "news_score_events_v1"
        }]
        terms = [address.lower()]
        if symbol and len(symbol) >= 2:
            terms.append(symbol.lower())
        if name and len(name) >= 3:
            terms.append(name.lower())
        newest_global = None
        for table in target_tables:
            cols = [row[1] for row in con.execute(f"PRAGMA table_info({sql_identifier(table)})")]
            count = con.execute(f"SELECT COUNT(*) FROM {sql_identifier(table)}").fetchone()[0]
            timestamp_cols = [col for col in cols if any(x in col.lower() for x in ("time", "date", "created", "published", "observed"))]
            newest = None
            for col in timestamp_cols[:5]:
                try:
                    candidate = con.execute(f"SELECT MAX({sql_identifier(col)}) FROM {sql_identifier(table)}").fetchone()[0]
                    if candidate and (newest is None or str(candidate) > str(newest)):
                        newest = candidate
                except sqlite3.Error:
                    pass
            text_cols = [col for col in cols if any(x in col.lower() for x in (
                "address", "token", "symbol", "title", "summary", "content", "text", "headline"
            ))]
            matched = 0
            samples = []
            for col in text_cols[:10]:
                for term in terms:
                    try:
                        rows = con.execute(
                            f"SELECT * FROM {sql_identifier(table)} WHERE lower(CAST({sql_identifier(col)} AS TEXT)) LIKE ? LIMIT 3",
                            (f"%{term}%",),
                        ).fetchall()
                    except sqlite3.Error:
                        continue
                    matched += len(rows)
                    for row in rows:
                        compact = {}
                        for key in row.keys():
                            value = row[key]
                            if value is not None and len(compact) < 8:
                                compact[key] = str(value)[:240]
                        samples.append(compact)
            result["tables"][table] = {"count": count, "newest": newest, "matched_rows": matched}
            if newest and (newest_global is None or str(newest) > str(newest_global)):
                newest_global = newest
            if samples:
                result["matches"].extend(samples[:5])
        con.close()
        result["newest"] = newest_global
        result["status"] = "OK" if result["matches"] else "TOKEN_ESLESMESI_YOK"
        result["freshness"] = "BILINMIYOR"
        if newest_global:
            try:
                parsed = datetime.fromisoformat(str(newest_global).replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                age_hours = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 3600.0
                result["age_hours"] = round(age_hours, 2)
                result["freshness"] = "GUNCEL" if age_hours <= 6 else "BAYAT"
            except Exception:
                pass
        result["matches"] = result["matches"][:10]
        return result
    except Exception as exc:
        return {"available": False, "status": "VERI_YETERSIZ", "error": f"{type(exc).__name__}:{str(exc)[:200]}"}


def make_decision(contract: dict[str, Any], market: dict[str, Any], technical: dict[str, Any], news: dict[str, Any]) -> dict[str, Any]:
    hard_blocks: list[str] = []
    reviews: list[str] = []
    warnings: list[str] = []
    if not contract.get("code_present"):
        hard_blocks.append("CONTRACT_CODE_YOK")
    if not contract.get("name") or not contract.get("symbol"):
        reviews.append("TOKEN_METADATA_EKSIK")
    decimals = contract.get("decimals")
    if decimals is None or not (0 <= decimals <= 36):
        hard_blocks.append("DECIMALS_GECERSIZ")
    if contract.get("total_supply") in (None, 0):
        reviews.append("TOTAL_SUPPLY_DOGRULANAMADI")
    primary = market.get("primary_pool") or {}
    liquidity = finite_float(primary.get("reserve_usd"))
    price = finite_float(primary.get("token_price_usd"))
    volume_24h = finite_float((primary.get("volume_usd") or {}).get("h24"))
    if not market.get("available"):
        reviews.append("DEX_POOL_VERISI_YOK")
    if liquidity is None:
        reviews.append("LIKIDITE_DOGRULANAMADI")
    elif liquidity < 10_000:
        hard_blocks.append("LIKIDITE_10000_USD_ALTINDA")
    elif liquidity < 50_000:
        reviews.append("LIKIDITE_50000_USD_ALTINDA")
    if price is None:
        reviews.append("FIYAT_DOGRULANAMADI")
    if volume_24h is None:
        warnings.append("24H_HACIM_DOGRULANAMADI")
    elif volume_24h < 1_000:
        reviews.append("24H_HACIM_COK_DUSUK")
    ok_frames = sum(1 for value in (technical.get("timeframes") or {}).values() if value.get("status") == "OK")
    if ok_frames < 3:
        reviews.append("TEKNIK_ZAMAN_DILIMI_YETERSIZ")
    if news.get("freshness") == "BAYAT":
        warnings.append("NEWS_VERISI_BAYAT")
    if not news.get("available"):
        warnings.append("NEWS_VERISI_YOK")
    verdict = "BLOCK" if hard_blocks else "REVIEW" if reviews else "ALLOW"
    completeness_inputs = [
        contract.get("code_present"),
        bool(contract.get("name")),
        bool(contract.get("symbol")),
        decimals is not None,
        contract.get("total_supply") is not None,
        market.get("available"),
        liquidity is not None,
        price is not None,
        ok_frames >= 3,
        news.get("available"),
    ]
    completeness = sum(bool(value) for value in completeness_inputs) / len(completeness_inputs)
    risk_score = min(100, int(round(10 + 35 * len(hard_blocks) + 12 * len(reviews) + 4 * len(warnings))))
    confidence = min(95, max(5, int(round(completeness * 100 - len(warnings) * 3))))
    return {
        "verdict": verdict,
        "risk_score_0_100": risk_score,
        "confidence_0_100": confidence,
        "hard_blocks": hard_blocks,
        "review_reasons": reviews,
        "wait_reasons": [],
        "warnings": warnings,
        "position_sizing": {
            "status": "VERI_YETERSIZ",
            "reason": "CANARY_WALLET_BALANCE_AND_HUMAN_POLICY_ENVELOPE_NOT_CONNECTED_IN_SLICE_02",
            "fixed_1_to_2_usd_cap": False,
        },
    }


def analyze(address: str) -> dict[str, Any]:
    if not ADDRESS_RE.match(address):
        raise ProductError("INVALID_BSC_TOKEN_ADDRESS")
    normalized = "0x" + address[2:].lower()
    started = time.monotonic()
    contract = contract_snapshot(normalized)
    market = gecko_pool_snapshot(normalized)
    primary = market.get("primary_pool") or {}
    technical = gecko_ohlcv(primary.get("pool_address"), primary.get("token_side") or "base")
    news = news_context(normalized, contract.get("symbol"), contract.get("name"))
    decision = make_decision(contract, market, technical, news)
    missing = []
    if not market.get("available"):
        missing.append("MARKET_POOL")
    for frame_name, value in (technical.get("timeframes") or {}).items():
        if value.get("status") != "OK":
            missing.append(f"TIMEFRAME_{frame_name}")
    if not news.get("available"):
        missing.append("NEWS")
    return {
        "schema": "tokenoskobi.product.single_token_decision_packet.v1",
        "analysis_id": str(uuid.uuid4()),
        "generated_at_utc": utc_now(),
        "chain": "BSC",
        "chain_id": 56,
        "token_address": normalized,
        "decision": decision,
        "contract": contract,
        "market": market,
        "technical": technical,
        "news": news,
        "data_quality": {
            "missing": missing,
            "explicit_insufficient_data": bool(missing),
            "policy": "MISSING_DATA_IS_SHOWN_AS_VERI_YETERSIZ_AND_IS_NEVER_FABRICATED",
        },
        "authority": AUTHORITY,
        "elapsed_ms": round((time.monotonic() - started) * 1000.0, 2),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "TokenoskobiProductSlice02/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}", flush=True)

    def send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_bytes(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/healthz":
            return self.send_json(200, {"ok": True, "service": "tokenoskobi-product-slice-02", "authority": AUTHORITY, "generated_at_utc": utc_now()})
        if parsed.path == "/api/v1/status":
            return self.send_json(200, {"ok": True, "chain": "BSC", "providers": [kind for kind, _ in provider_chain()], "alchemy_configured": bool(read_alchemy_url()), "authority": AUTHORITY})
        if parsed.path == "/api/v1/analyze":
            query = urllib.parse.parse_qs(parsed.query)
            address = (query.get("address") or [""])[0].strip()
            try:
                return self.send_json(200, {"ok": True, "packet": analyze(address)})
            except ProductError as exc:
                return self.send_json(400, {"ok": False, "error": str(exc), "authority": AUTHORITY})
            except Exception as exc:
                return self.send_json(502, {"ok": False, "error": "ANALYSIS_FAILED", "detail": f"{type(exc).__name__}:{str(exc)[:220]}", "authority": AUTHORITY})
        if UI_FILE.exists():
            return self.send_bytes(200, UI_FILE.read_bytes(), "text/html; charset=utf-8")
        return self.send_json(404, {"ok": False, "error": "UI_NOT_FOUND"})

    def do_POST(self) -> None:
        self.send_json(405, {"ok": False, "error": "READ_ONLY_GET_ONLY_SERVICE", "authority": AUTHORITY})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"TOKENOSKOBI_PRODUCT_SLICE_02_LISTEN={HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
