#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import math
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from core.platform.paths import get_root
ROOT = get_root()
CFG = json.loads((ROOT / "config/product_slice_02_v1.json").read_text(encoding="utf-8"))
if os.getenv("TOKENOSKOBI_PRODUCT_SLICE_02_PORT"):
    CFG = dict(CFG)
    CFG["port"] = int(os.environ["TOKENOSKOBI_PRODUCT_SLICE_02_PORT"])

ADDR = re.compile(r"^0x[a-fA-F0-9]{40}$")
SEL = {
    "name": "0x06fdde03",
    "symbol": "0x95d89b41",
    "decimals": "0x313ce567",
    "supply": "0x18160ddd",
    "owner": "0x8da5cb5b",
}
DBS = [
    ROOT / "data/tokenoskobi_clean_v1.sqlite",
    ROOT / "data/tokenoskobi_v1.sqlite",
    ROOT / "data/tokenoskobi.sqlite",
    ROOT / "tokenoskobi.sqlite",
]
TABLES = (
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1",
)

GT_RATE_DIR = Path(os.getenv("TOKENOSKOBI_GT_RATE_DIR", "/run"))
GT_LOCK = GT_RATE_DIR / "tokenoskobi_geckoterminal_rate.lock"
GT_STATE = GT_RATE_DIR / "tokenoskobi_geckoterminal_rate.state"
GT_MIN_INTERVAL_SEC = 6.5
GT_MAX_ATTEMPTS = 4
GT_THREAD_LOCK = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def num(value: Any) -> float | None:
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    except (TypeError, ValueError):
        return None


def is_geckoterminal(url: str) -> bool:
    return urllib.parse.urlsplit(url).netloc.lower() == "api.geckoterminal.com"


def geckoterminal_slot() -> None:
    GT_RATE_DIR.mkdir(parents=True, exist_ok=True)
    with GT_THREAD_LOCK:
        with GT_LOCK.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            last = 0.0
            try:
                last = float(GT_STATE.read_text(encoding="utf-8").strip() or 0)
            except (OSError, ValueError):
                pass
            delay = GT_MIN_INTERVAL_SEC - (time.time() - last)
            if delay > 0:
                time.sleep(delay)
            stamp = time.time()
            temporary = GT_STATE.with_name(
                f"{GT_STATE.name}.{os.getpid()}.{threading.get_ident()}.tmp"
            )
            temporary.write_text(str(stamp), encoding="utf-8")
            os.replace(temporary, GT_STATE)
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def request(url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"Accept": "application/json", "User-Agent": "Tokenoskobi-Slice02/2"}
    data = None
    method = "GET"
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
        method = "POST"

    gecko = is_geckoterminal(url)
    attempts = GT_MAX_ATTEMPTS if gecko else 1
    for attempt in range(1, attempts + 1):
        if gecko:
            geckoterminal_slot()
        query = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(query, timeout=CFG["timeout_sec"]) as response:
                return json.loads(response.read(2_000_000))
        except urllib.error.HTTPError as exc:
            if not (gecko and exc.code == 429 and attempt < attempts):
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = max(GT_MIN_INTERVAL_SEC, float(retry_after))
            except (TypeError, ValueError):
                delay = min(60.0, GT_MIN_INTERVAL_SEC * (2**attempt))
            time.sleep(delay)
    raise RuntimeError("GECKOTERMINAL_RETRY_EXHAUSTED")


def rpc(url: str, method: str, params: list[Any]) -> Any:
    result = request(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    if result.get("error"):
        raise RuntimeError(str(result["error"])[:160])
    return result["result"]


def alchemy() -> str | None:
    path = ROOT / ".secrets/alchemy_bnb.env"
    if path.exists():
        for line in path.read_text(errors="ignore").splitlines():
            if line.startswith("BSC_ALCHEMY_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv("BSC_ALCHEMY_URL")


def providers() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    selected = None
    urls: list[tuple[str, str]] = []
    if alchemy_url := alchemy():
        urls.append(("alchemy", alchemy_url))
    urls += [(f"public_{index + 1}", url) for index, url in enumerate(CFG["rpc"])]

    for name, url in urls:
        started = time.monotonic()
        try:
            chain = int(rpc(url, "eth_chainId", []), 16)
            block = int(rpc(url, "eth_blockNumber", []), 16)
            ok = chain == 56
            row = {
                "name": name,
                "ok": ok,
                "block": block,
                "latency_ms": round((time.monotonic() - started) * 1000, 1),
            }
            if ok and selected is None:
                selected = {"name": name, "url": url, "block": block}
        except Exception as exc:
            row = {"name": name, "ok": False, "error": f"{type(exc).__name__}:{str(exc)[:120]}"}
        rows.append(row)

    alchemy_ok = any(row.get("name") == "alchemy" and row.get("ok") for row in rows)
    public_ok = sum(
        1 for row in rows if row.get("name", "").startswith("public_") and row.get("ok")
    )
    return {
        "rows": rows,
        "selected": selected,
        "alchemy_http_ok": alchemy_ok,
        "public_rpc_ok": public_ok,
        "hybrid_ready": bool(alchemy_ok and public_ok),
    }


def text(raw: str | None) -> str | None:
    if not raw or raw == "0x":
        return None
    try:
        data = bytes.fromhex(raw[2:])
    except ValueError:
        return None
    if len(data) == 32:
        return data.rstrip(b"\0").decode(errors="ignore").strip() or None
    if len(data) >= 64:
        try:
            offset = int.from_bytes(data[:32], "big")
            length = int.from_bytes(data[offset : offset + 32], "big")
            return (
                data[offset + 32 : offset + 32 + length]
                .decode(errors="ignore")
                .strip()
                or None
            )
        except Exception:
            return None
    return None


def uint(raw: str | None) -> int | None:
    try:
        return int(raw, 16) if raw and raw != "0x" else None
    except ValueError:
        return None


def address(raw: str | None) -> str | None:
    if not raw or raw == "0x":
        return None
    value = "0x" + raw.replace("0x", "")[-40:].lower()
    return None if value == "0x" + "0" * 40 else value


def contract(token: str, provider_state: dict[str, Any]) -> dict[str, Any]:
    selected = provider_state.get("selected")
    output: dict[str, Any] = {"code_exists": None, "metadata": {}, "errors": []}
    if not selected:
        output["errors"].append("NO_RPC")
        return output

    try:
        code = rpc(selected["url"], "eth_getCode", [token, "latest"])
        output["code_exists"] = code not in ("0x", "0x0", "")
    except Exception as exc:
        output["errors"].append("CODE:" + str(exc)[:100])

    raw: dict[str, str | None] = {}
    for key, selector in SEL.items():
        try:
            raw[key] = rpc(
                selected["url"], "eth_call", [{"to": token, "data": selector}, "latest"]
            )
        except Exception:
            raw[key] = None

    decimals = uint(raw["decimals"])
    supply = uint(raw["supply"])
    output["metadata"] = {
        "name": text(raw["name"]),
        "symbol": text(raw["symbol"]),
        "decimals": decimals,
        "total_supply": (
            supply / (10**decimals)
            if supply is not None and decimals is not None and 0 <= decimals <= 36
            else None
        ),
        "owner": address(raw["owner"]),
    }
    return output


def relationship_address(item: dict[str, Any], key: str) -> str | None:
    relationship = ((item.get("relationships") or {}).get(key) or {}).get("data") or {}
    candidate = str(relationship.get("id") or "").rsplit("_", 1)[-1].lower()
    return candidate if ADDR.fullmatch(candidate) else None


def oriented_pool(item: dict[str, Any], token: str) -> dict[str, Any]:
    token = token.lower()
    attributes = item.get("attributes") or {}
    base = relationship_address(item, "base_token")
    quote = relationship_address(item, "quote_token")
    side = "base" if token == base else "quote" if token == quote else None

    base_price = num(attributes.get("base_token_price_usd"))
    quote_price = num(attributes.get("quote_token_price_usd"))
    base_change = num((attributes.get("price_change_percentage") or {}).get("h24"))
    target_price = base_price if side == "base" else quote_price if side == "quote" else None
    target_change = base_change
    if side == "quote":
        target_change = (
            (1 / (1 + base_change / 100) - 1) * 100
            if base_change is not None and base_change > -100
            else None
        )

    return {
        "address": attributes.get("address") or item.get("id", "").split("_")[-1],
        "name": attributes.get("name"),
        "reserve_usd": num(attributes.get("reserve_in_usd")),
        "price_usd": target_price,
        "base_token_price_usd": base_price,
        "quote_token_price_usd": quote_price,
        "base_token_address": base,
        "quote_token_address": quote,
        "target_token_address": token if side else None,
        "target_side": side,
        "orientation_verified": bool(side),
        "volume_24h_usd": num((attributes.get("volume_usd") or {}).get("h24")),
        "change_24h_pct": target_change,
    }


def market(token: str) -> dict[str, Any]:
    base = "https://api.geckoterminal.com/api/v2"
    output: dict[str, Any] = {
        "available": False,
        "token": {},
        "pools": [],
        "selected_pool": None,
        "target_orientation_verified": False,
        "errors": [],
    }

    try:
        attributes = request(f"{base}/networks/bsc/tokens/{token}")["data"]["attributes"]
        output["token"] = {
            "name": attributes.get("name"),
            "symbol": attributes.get("symbol"),
            "price_usd": num(attributes.get("price_usd")),
            "market_cap_usd": num(attributes.get("market_cap_usd")),
            "fdv_usd": num(attributes.get("fdv_usd")),
        }
        if output["token"]["price_usd"] is not None:
            output["token"]["price_source"] = "TOKEN_ENDPOINT"
        output["available"] = True
    except Exception as exc:
        output["errors"].append(f"TOKEN:{type(exc).__name__}:{str(exc)[:100]}")

    try:
        rows = [
            oriented_pool(item, token)
            for item in request(
                f"{base}/networks/bsc/tokens/{token}/pools?page=1"
            ).get("data", [])
        ]
        rows.sort(
            key=lambda row: (
                1 if row.get("orientation_verified") else 0,
                row.get("reserve_usd") or 0,
            ),
            reverse=True,
        )
        oriented = [row for row in rows if row.get("orientation_verified")]
        output["pools"] = rows[:8]
        output["selected_pool"] = oriented[0] if oriented else None
        output["target_orientation_verified"] = bool(oriented)
        output["available"] = output["available"] or bool(rows)

        selected = output.get("selected_pool") or {}
        token_row = output.setdefault("token", {})
        if (
            selected.get("orientation_verified")
            and token_row.get("price_usd") is None
            and selected.get("price_usd") is not None
        ):
            token_row["price_usd"] = selected["price_usd"]
            token_row["price_source"] = "SELECTED_POOL_ORIENTED_FALLBACK"

        if rows and not oriented:
            output["errors"].append("TARGET_ASSET_ORIENTATION_UNVERIFIED")
    except Exception as exc:
        output["errors"].append(f"POOLS:{type(exc).__name__}:{str(exc)[:100]}")

    return output


def technical_row(payload: dict[str, Any], token: str) -> tuple[list[float], str]:
    metadata = payload.get("meta") or {}
    base_address = str((metadata.get("base") or {}).get("address") or "").lower()
    quote_address = str((metadata.get("quote") or {}).get("address") or "").lower()
    if token not in {base_address, quote_address}:
        raise ValueError("TARGET_TOKEN_NOT_IN_OHLCV_META")
    side = "base" if token == base_address else "quote"
    rows = payload["data"]["attributes"]["ohlcv_list"]
    closes: list[float] = []
    for row in rows:
        if len(row) >= 6 and (close := num(row[4])) is not None:
            closes.append(close)
    return list(reversed(closes)), side


def tech(pool: str | None, token: str) -> dict[str, Any]:
    specs = {
        "1m": ("minute", 1),
        "5m": ("minute", 5),
        "15m": ("minute", 15),
        "1h": ("hour", 1),
        "4h": ("hour", 4),
        "1d": ("day", 1),
    }
    token = token.lower()
    if not pool:
        return {
            key: {"status": "VERI_YETERSIZ", "target_token_address": token}
            for key in specs
        }

    output: dict[str, Any] = {}
    base = "https://api.geckoterminal.com/api/v2"
    for key, (timeframe, aggregate) in specs.items():
        try:
            selector = urllib.parse.quote(token, safe="")
            url = (
                f"{base}/networks/bsc/pools/{pool}/ohlcv/{timeframe}"
                f"?aggregate={aggregate}&limit=100&currency=usd&token={selector}"
            )
            closes, side = technical_row(request(url), token)
            if len(closes) < 3:
                output[key] = {
                    "status": "VERI_YETERSIZ",
                    "bars": len(closes),
                    "target_token_address": token,
                    "target_side": side,
                }
                continue
            change = (closes[-1] / closes[0] - 1) * 100 if closes[0] else None
            fast = sum(closes[-5:]) / min(5, len(closes))
            slow = sum(closes[-20:]) / min(20, len(closes))
            trend = (
                "UP"
                if fast > slow * 1.002
                else "DOWN"
                if fast < slow * 0.998
                else "FLAT"
            )
            output[key] = {
                "status": "OK",
                "bars": len(closes),
                "last": closes[-1],
                "change_pct": round(change, 4) if change is not None else None,
                "trend": trend,
                "target_token_address": token,
                "target_side": side,
            }
        except Exception as exc:
            output[key] = {
                "status": "VERI_YETERSIZ",
                "error": f"{type(exc).__name__}:{str(exc)[:120]}",
                "target_token_address": token,
            }
    return output


def news(token: str, metadata: dict[str, Any]) -> dict[str, Any]:
    terms = {token.lower()}
    terms |= {
        str(metadata.get(key)).lower()
        for key in ("name", "symbol")
        if metadata.get(key)
    }
    database = next((path for path in DBS if path.exists()), None)
    output: dict[str, Any] = {
        "database": str(database.relative_to(ROOT)) if database else None,
        "fresh": False,
        "matches": [],
        "latest": None,
    }
    if not database:
        return output

    latest = 0.0
    try:
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        connection.execute("PRAGMA query_only=ON")
        for table in TABLES:
            if not connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone():
                continue
            columns = [
                column[1]
                for column in connection.execute(f'PRAGMA table_info("{table}")')
            ]
            for row in connection.execute(
                f'SELECT * FROM "{table}" ORDER BY rowid DESC LIMIT 100'
            ):
                record = {
                    columns[index]: (
                        row[index]
                        if isinstance(row[index], (str, int, float, type(None)))
                        else str(row[index])
                    )
                    for index in range(len(columns))
                }
                blob = json.dumps(record, ensure_ascii=False).lower()
                if any(term in blob for term in terms) and len(output["matches"]) < 20:
                    output["matches"].append({"table": table, "record": record})
                for value in record.values():
                    if isinstance(value, str):
                        try:
                            timestamp = datetime.fromisoformat(
                                value.replace("Z", "+00:00")
                            ).timestamp()
                            if timestamp > latest:
                                latest = timestamp
                                output["latest"] = datetime.fromtimestamp(
                                    timestamp, timezone.utc
                                ).isoformat()
                        except Exception:
                            pass
        connection.close()
    except Exception as exc:
        output["error"] = f"{type(exc).__name__}:{str(exc)[:120]}"

    if latest:
        output["age_sec"] = round(time.time() - latest, 1)
        output["fresh"] = output["age_sec"] <= CFG["news_stale_sec"]
    return output


def ratio_ok(left: float | None, right: float | None, low: float, high: float) -> bool:
    return bool(left is not None and right not in (None, 0) and low <= left / right <= high)


def decide(
    contract_state: dict[str, Any],
    market_state: dict[str, Any],
    technical_state: dict[str, Any],
    news_state: dict[str, Any],
    provider_state: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    score = 50

    if contract_state.get("code_exists") is False:
        blockers.append("CONTRACT_CODE_MISSING")
        score = 100
    elif contract_state.get("code_exists") is True:
        evidence.append("CONTRACT_CODE_PRESENT")
        score -= 10
    else:
        warnings.append("CONTRACT_CODE_UNVERIFIED")
        score += 20

    selected = market_state.get("selected_pool") or {}
    target = selected.get("target_token_address")
    orientation = bool(
        market_state.get("target_orientation_verified")
        and selected.get("orientation_verified")
        and target
    )
    if orientation:
        evidence.append("TARGET_ASSET_ORIENTATION_VERIFIED")
    else:
        blockers.append("TARGET_ASSET_ORIENTATION_UNVERIFIED")
        score = 100

    liquidity = num(selected.get("reserve_usd"))
    if liquidity is None:
        warnings.append("LIQUIDITY_UNVERIFIED")
        score += 20
    elif liquidity < 5000:
        blockers.append("LIQUIDITY_BELOW_5000_USD")
        score += 35
    elif liquidity < 50000:
        warnings.append("LOW_LIQUIDITY")
        score += 15
    else:
        evidence.append("LIQUIDITY_AT_LEAST_50000_USD")
        score -= 15

    token_price = num((market_state.get("token") or {}).get("price_usd"))
    pool_price = num(selected.get("price_usd"))
    price_source = (market_state.get("token") or {}).get("price_source")
    if orientation and (token_price is None or pool_price is None):
        blockers.append("TARGET_PRICE_UNVERIFIED")
        score = 100
    elif orientation and not ratio_ok(token_price, pool_price, 0.75, 1.25):
        blockers.append("TARGET_PRICE_SOURCE_MISMATCH")
        score = 100
    elif price_source == "SELECTED_POOL_ORIENTED_FALLBACK":
        evidence.append("TARGET_PRICE_FROM_ORIENTED_POOL_FALLBACK")
    elif price_source == "TOKEN_ENDPOINT":
        evidence.append("TARGET_PRICE_FROM_TOKEN_ENDPOINT")

    wrong_target = sum(
        1
        for row in technical_state.values()
        if row.get("status") == "OK" and row.get("target_token_address") != target
    )
    wrong_price = sum(
        1
        for row in technical_state.values()
        if row.get("status") == "OK"
        and row.get("target_token_address") == target
        and not ratio_ok(num(row.get("last")), pool_price, 0.5, 2.0)
    )
    valid_technical = sum(
        1
        for row in technical_state.values()
        if row.get("status") == "OK"
        and row.get("target_token_address") == target
        and ratio_ok(num(row.get("last")), pool_price, 0.5, 2.0)
    )
    if wrong_target:
        blockers.append("TECHNICAL_TARGET_MISMATCH")
        score = 100
    if wrong_price:
        blockers.append("TECHNICAL_TARGET_PRICE_MISMATCH")
        score = 100
    if valid_technical < 2:
        warnings.append("TECHNICAL_DATA_INSUFFICIENT")
        score += 15
    elif valid_technical >= 4 and orientation and not wrong_target and not wrong_price:
        evidence.append("MULTI_TIMEFRAME_AVAILABLE")
        score -= 5

    if provider_state["public_rpc_ok"]:
        evidence.append("PUBLIC_RPC_FALLBACK_AVAILABLE")
    else:
        blockers.append("NO_BSC_RPC")
        score += 40
    if not provider_state["hybrid_ready"]:
        warnings.append("ALCHEMY_HYBRID_NOT_READY")
        score += 5
    if not news_state["fresh"]:
        warnings.append("NEWS_STALE_OR_UNAVAILABLE")
        score += 5

    score = max(0, min(100, score))
    decision = (
        "BLOCK"
        if blockers
        else "REVIEW"
        if len(warnings) >= 3 or score >= 65
        else "WAIT"
        if score >= 45
        else "ALLOW"
    )
    quality = (
        "SUFFICIENT"
        if contract_state.get("code_exists") is True
        and liquidity is not None
        and orientation
        and token_price is not None
        and pool_price is not None
        and not wrong_target
        and not wrong_price
        and valid_technical >= 2
        else "VERI_YETERSIZ"
    )
    return {
        "decision": decision,
        "risk_score": score,
        "data_quality": quality,
        "blockers": blockers,
        "warnings": warnings,
        "evidence": evidence,
        "authority": "ADVISORY_ONLY",
    }


def analyze(token: str) -> dict[str, Any]:
    token = token.lower()
    provider_state = providers()
    contract_state = contract(token, provider_state)
    market_state = market(token)
    metadata = contract_state["metadata"]
    metadata["name"] = metadata.get("name") or (market_state.get("token") or {}).get("name")
    metadata["symbol"] = metadata.get("symbol") or (market_state.get("token") or {}).get(
        "symbol"
    )
    technical_state = tech((market_state.get("selected_pool") or {}).get("address"), token)
    news_state = news(token, metadata)
    decision = decide(
        contract_state, market_state, technical_state, news_state, provider_state
    )
    safe_provider = {
        key: value for key, value in provider_state.items() if key != "selected"
    }
    safe_provider["selected"] = {
        key: value
        for key, value in (provider_state.get("selected") or {}).items()
        if key != "url"
    } or None
    return {
        "schema": "tokenoskobi.product_slice_02.packet.v1",
        "generated_at_utc": now(),
        "chain": "BSC",
        "token_address": token,
        "provider": safe_provider,
        "contract": contract_state,
        "market": market_state,
        "technical_timeframes": technical_state,
        "news": news_state,
        "decision": decision,
        "authority": {
            "paper": False,
            "live": False,
            "wallet": False,
            "signing": False,
            "order": False,
            "broadcast": False,
            "human_action_required": True,
        },
    }


HTML = """<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tokenoskobi</title><style>body{margin:0;background:#091019;color:#e8eef5;font-family:system-ui}.w{max-width:1100px;margin:auto;padding:18px}.box{background:#111b27;border:1px solid #2a3b4e;border-radius:15px;padding:18px;margin:12px 0}input,button{padding:14px;border-radius:10px;border:1px solid #3b5068;background:#0b131c;color:white;font-size:16px}input{width:min(720px,70%)}button{background:#dbeaff;color:#06101a;font-weight:800}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.card{background:#0b131c;border-radius:12px;padding:13px}.ALLOW{color:#75eca2}.WAIT{color:#ffd173}.REVIEW{color:#ffa56d}.BLOCK{color:#ff7784}pre{white-space:pre-wrap;word-break:break-word}@media(max-width:700px){.grid{grid-template-columns:1fr}input{width:100%;margin-bottom:8px}}</style></head><body><main class="w"><h2>TOKENOSKOBİ — Tek Token Karar Paketi</h2><div class="box">BSC token adresi: <input id="a" placeholder="0x…"><button id="b" onclick="go()">Analiz Et</button><p id="s"></p></div><div id="r"></div></main><script>const a=document.getElementById('a'),b=document.getElementById('b'),s=document.getElementById('s'),r=document.getElementById('r'),e=x=>String(x??'—').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));async function go(){b.disabled=true;s.textContent='Gerçek veriler toplanıyor…';r.innerHTML='';try{let z=await fetch('/api/v1/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token_address:a.value.trim()})}),d=await z.json();if(!z.ok)throw Error(d.error);let q=d.decision,m=d.contract.metadata,p=d.market.selected_pool||{},t=d.market.token||{};r.innerHTML=`<div class="grid"><div class="card"><b>Karar</b><h1 class="${e(q.decision)}">${e(q.decision)}</h1>${e(q.data_quality)}</div><div class="card"><b>Risk</b><h1>${e(q.risk_score)}/100</h1></div><div class="card"><b>Token</b><h1>${e(m.symbol)}</h1>${e(m.name)}</div></div><div class="box"><b>Fiyat / Likidite</b><p>${e(t.price_usd)} USD / ${e(p.reserve_usd)} USD</p><small>Fiyat kaynağı: ${e(t.price_source)}</small><p><b>Uyarılar</b><br>${e(q.warnings.join(' • '))}</p><p><b>Kanıt</b><br>${e(q.evidence.join(' • '))}</p></div><details class="box"><summary>Ham paket</summary><pre>${e(JSON.stringify(d,null,2))}</pre></details>`;s.textContent='Karar paketi üretildi';}catch(x){s.textContent=x.message}finally{b.disabled=false}}</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *_: Any) -> None:
        pass

    def sendj(
        self,
        code: int,
        obj: dict[str, Any] | str,
        content_type: str = "application/json; charset=utf-8",
    ) -> None:
        body = (
            json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj
        ).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        if path == "/healthz":
            return self.sendj(200, {"ok": True, "authority": "READ_ONLY_ADVISORY"})
        if path in ("/", "/panel", "/panel/", "/panel/panel_v2", "/panel/panel_v2/"):
            return self.sendj(200, HTML, "text/html; charset=utf-8")
        self.sendj(404, {"error": "NOT_FOUND"})

    def do_POST(self) -> None:
        if urllib.parse.urlsplit(self.path).path != "/api/v1/analyze":
            return self.sendj(404, {"error": "NOT_FOUND"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                return self.sendj(400, {"error": "INVALID_REQUEST_SIZE"})
            payload = json.loads(self.rfile.read(length))
            token_address = payload.get("token_address", "")
            if not ADDR.fullmatch(token_address):
                return self.sendj(400, {"error": "INVALID_BSC_TOKEN_ADDRESS"})
            self.sendj(200, analyze(token_address))
        except Exception as exc:
            self.sendj(
                500,
                {
                    "error": "ANALYSIS_FAILED",
                    "detail": f"{type(exc).__name__}:{str(exc)[:140]}",
                },
            )


AUTHORITY = CFG["authority"]
if __name__ == "__main__":
    assert CFG["host"] == "127.0.0.1"
    assert all(
        AUTHORITY[key] is False
        for key in ("paper", "live", "wallet", "signing", "order", "broadcast")
    )
    ThreadingHTTPServer((CFG["host"], CFG["port"]), H).serve_forever()
