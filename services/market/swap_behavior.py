"""Observed swap behavior on a Pancake V2 pair: sell-ability and tax estimates.

Advisory only. It reads real recent swaps (no simulation) and never changes the
decision or score. Every number is an ESTIMATE from a small sample; anything that
cannot be measured is reported as UNKNOWN, never as safe or as zero.
"""
from __future__ import annotations

import time
from statistics import median
from typing import Any, Callable

from services.market.dex_policy import DEPLOYMENTS
from services.market.token_controls import keccak256, selector

TRANSFER_TOPIC = "0x" + keccak256(b"Transfer(address,address,uint256)").hex()
SWAP_TOPIC = "0x" + keccak256(b"Swap(address,uint256,uint256,uint256,uint256,address)").hex()
TOKEN0_CALL = "0x" + selector("token0()")
TOKEN1_CALL = "0x" + selector("token1()")
RESERVES_CALL = "0x" + selector("getReserves()")
ROUTER_V2 = "0x10ed43c718714eb63d5aa57b78b54704e256024e"
ROUTER_LABELS = {
    DEPLOYMENTS["v2"][1]: "PANCAKE_V2_ROUTER",
    DEPLOYMENTS["v3"][1]: "PANCAKE_V3_ROUTER",
}
SELL_ROUTER_SELECTORS = {
    selector(signature)
    for signature in (
        "swapExactTokensForETHSupportingFeeOnTransferTokens(uint256,uint256,address[],address,uint256)",
        "swapExactTokensForTokensSupportingFeeOnTransferTokens(uint256,uint256,address[],address,uint256)",
        "swapExactTokensForETH(uint256,uint256,address[],address,uint256)",
        "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)",
    )
}
LOOKBACK_STEPS = (3000, 1000, 300)
MIN_BUYS_FOR_SELL_SIGNAL = 10
MIN_TAX_SAMPLES = 3
MIN_FEE_DETECTIONS = 2
MAX_SAMPLES = 8
MAX_SELL_SAMPLES = 12
BUDGET_SEC = 15.0

LIMITS = (
    "Bunlar son işlemlerden yapılan TAHMİNLERDİR, simülasyon değildir. Az işlem varsa "
    "VERİ YETERSİZ çıkar. Satış gözlenmesi, herkesin satabildiği anlamına gelmez; vergi "
    "tahmini yalnızca doğrudan Pancake V2 router işlemlerinden ölçülür; ayrı transferle "
    "alınan vergi ek olarak aranır, ama bulunamaması vergi olmadığını göstermez. Ölçülemeyen "
    "UNKNOWN sayılır, güvenli sayılmaz."
)


def unavailable(reason: str) -> dict[str, Any]:
    return {"status": "UNKNOWN", "reason": reason, "limits": LIMITS}


def _addr(topic: str) -> str:
    return "0x" + topic[-40:].lower()


def _word(data: str, index: int) -> int:
    return int(data[2 + 64 * index : 2 + 64 * (index + 1)], 16)


def parse_swap(log: Any, target_is_token0: bool) -> dict[str, Any] | None:
    """A V2 Swap log as a buy/sell of the target token, or None if unusable."""
    try:
        topics = log["topics"]
        data = log["data"]
        if len(topics) != 3 or topics[0].lower() != SWAP_TOPIC:
            return None
        if not isinstance(data, str) or len(data) != 2 + 64 * 4:
            return None
        in0, in1, out0, out1 = (_word(data, i) for i in range(4))
        target_in, target_out = (in0, out0) if target_is_token0 else (in1, out1)
        if target_out > 0 and target_in == 0:
            kind = "buy"
        elif target_in > 0 and target_out == 0:
            kind = "sell"
        else:
            return None
        return {
            "kind": kind,
            "sender": _addr(topics[1]),
            "to": _addr(topics[2]),
            "target_in": target_in,
            "target_out": target_out,
            "tx": log["transactionHash"],
        }
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def buy_tax_sample(swap: dict[str, Any], receipt: Any, token: str, pair: str) -> float | None:
    """Fraction lost between the pair's amountOut and what the buyer's Transfer shows."""
    try:
        net = 0
        for log in receipt.get("logs") or []:
            topics = log.get("topics") or []
            if (log.get("address") or "").lower() != token:
                continue
            if len(topics) != 3 or topics[0].lower() != TRANSFER_TOPIC:
                continue
            if _addr(topics[1]) == pair and _addr(topics[2]) == swap["to"]:
                net += int(log["data"], 16)
        out = swap["target_out"]
        if net <= 0 or net > out:
            return None
        return 1 - net / out
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


def sell_tax_outcome(swap: dict[str, Any], tx: Any, token: str) -> tuple[float | None, str]:
    """(tax fraction or None, reason). Fraction lost between the router call's amountIn
    and what the pair received; only for a direct single-hop Pancake V2 router sell of
    this token, so the calldata amount is the seller's gross amount."""
    try:
        if swap["sender"] != ROUTER_V2:
            return None, "SENDER_NOT_V2_ROUTER"
        if (tx.get("to") or "").lower() != ROUTER_V2:
            return None, "TX_NOT_TO_V2_ROUTER"
        data = tx.get("input")
        if not isinstance(data, str) or data[2:10] not in SELL_ROUTER_SELECTORS:
            return None, "UNKNOWN_FUNCTION"
        args = data[10:]
        if len(args) < 64 * 5:
            return None, "BAD_CALLDATA"
        gross = int(args[0:64], 16)
        position = int(args[128:192], 16) * 2
        if int(args[position : position + 64], 16) != 2:
            return None, "MULTI_HOP"
        first = "0x" + args[position + 64 + 24 : position + 128]
        if first.lower() != token:
            return None, "FIRST_TOKEN_MISMATCH"
        net = swap["target_in"]
        if gross <= 0 or net <= 0 or net > gross:
            return None, "AMOUNT_INCONSISTENT"
        return 1 - net / gross, "OK"
    except (AttributeError, KeyError, TypeError, ValueError):
        return None, "BAD_CALLDATA"


def sell_tax_sample(swap: dict[str, Any], tx: Any, token: str) -> float | None:
    return sell_tax_outcome(swap, tx, token)[0]


def sell_fee_event_outcome(
    swap: dict[str, Any], receipt: Any, token: str, pool: str
) -> tuple[str, float | None]:
    """Router-independent: look for a separate fee Transfer by the seller in the same tx.

    FEE: a fee transfer was found (fraction = fee / (fee + net received by the pair)).
    NO_FEE_TRANSFER: the layout was clear and no fee transfer exists. This does NOT prove
    zero tax (reflection tokens take fees without a separate Transfer event).
    INCONCLUSIVE: anything ambiguous (several swaps, split routes, pool-like recipients).
    """
    inconclusive = ("INCONCLUSIVE", None)
    try:
        logs = receipt.get("logs") or []
        pool_swaps = [
            log for log in logs
            if (log.get("address") or "").lower() == pool
            and (log.get("topics") or [""])[0].lower() == SWAP_TOPIC
        ]
        if len(pool_swaps) != 1:
            return inconclusive
        transfers = []
        for log in logs:
            topics = log.get("topics") or []
            if (log.get("address") or "").lower() != token or len(topics) != 3:
                continue
            if topics[0].lower() == TRANSFER_TOPIC:
                transfers.append((_addr(topics[1]), _addr(topics[2]), int(log["data"], 16)))
        into_pool = [t for t in transfers if t[1] == pool]
        if len(into_pool) != 1:
            return inconclusive
        payer, _, net = into_pool[0]
        if net <= 0 or net != swap["target_in"]:
            return inconclusive
        fees = [t for t in transfers if t[0] == payer and t[1] != pool]
        recipients = {t[1] for t in fees}
        for log in logs:
            address = (log.get("address") or "").lower()
            topics = log.get("topics") or [""]
            if address in recipients and address != token and topics[0].lower() != TRANSFER_TOPIC:
                return inconclusive  # a recipient that acts like a pool or router
        fee = sum(t[2] for t in fees)
        if fee <= 0:
            return "NO_FEE_TRANSFER", 0.0
        return "FEE", fee / (net + fee)
    except (AttributeError, KeyError, TypeError, ValueError):
        return inconclusive


def summarize_fee_events(outcomes: list[tuple[str, float | None]]) -> dict[str, Any]:
    fees = [value for kind, value in outcomes if kind == "FEE" and value is not None]
    clear = sum(1 for kind, _ in outcomes if kind == "NO_FEE_TRANSFER")
    inconclusive = sum(1 for kind, _ in outcomes if kind == "INCONCLUSIVE")
    base = {"detected": len(fees), "not_detected": clear, "inconclusive": inconclusive,
            "median_pct": None, "max_pct": None}
    if len(fees) >= MIN_FEE_DETECTIONS:
        return {**base, "status": "DETECTED",
                "median_pct": round(median(fees) * 100, 2), "max_pct": round(max(fees) * 100, 2)}
    if not fees and clear >= MIN_TAX_SAMPLES:
        return {**base, "status": "NOT_DETECTED"}
    return {**base, "status": "UNKNOWN"}


def top_senders(swaps: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    """Which contracts called the pool (labels only for deployments the project knows)."""
    counts: dict[str, int] = {}
    for swap in swaps:
        counts[swap["sender"]] = counts.get(swap["sender"], 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [{"address": address, "label": ROUTER_LABELS.get(address), "count": count}
            for address, count in ranked]


def summarize_tax(samples: list[float]) -> dict[str, Any]:
    if len(samples) < MIN_TAX_SAMPLES:
        return {"status": "UNKNOWN", "median_pct": None, "max_pct": None, "samples": len(samples)}
    return {
        "status": "ESTIMATED",
        "median_pct": round(median(samples) * 100, 2),
        "max_pct": round(max(samples) * 100, 2),
        "samples": len(samples),
    }


def collect_swap_behavior(
    token: str,
    pool: str,
    rpc: Callable[[str, list[Any]], Any],
    budget_sec: float = BUDGET_SEC,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Read recent swaps of the pool. `rpc(method, params)` does the network call."""
    token, pool = token.lower(), pool.lower()
    try:
        raw0 = rpc("eth_call", [{"to": pool, "data": TOKEN0_CALL}, "latest"])
        if not isinstance(raw0, str) or len(raw0) != 66:
            return unavailable("POOL_NOT_V2_PAIR")
        target_is_token0 = _addr(raw0) == token
        if not target_is_token0:
            raw1 = rpc("eth_call", [{"to": pool, "data": TOKEN1_CALL}, "latest"])
            if not isinstance(raw1, str) or len(raw1) != 66 or _addr(raw1) != token:
                return unavailable("TOKEN_NOT_IN_POOL")
        # V3 pools also answer token0(); only a V2 pair answers getReserves() with 3 words.
        reserves = rpc("eth_call", [{"to": pool, "data": RESERVES_CALL}, "latest"])
        if not isinstance(reserves, str) or len(reserves) != 2 + 64 * 3:
            return unavailable("POOL_NOT_V2_PAIR")
        latest = int(rpc("eth_blockNumber", []), 16)
    except Exception:
        return unavailable("POOL_NOT_V2_PAIR")

    logs, window = None, None
    for span in LOOKBACK_STEPS:
        try:
            logs = rpc("eth_getLogs", [{
                "address": pool, "topics": [SWAP_TOPIC],
                "fromBlock": hex(max(0, latest - span)), "toBlock": hex(latest),
            }])
            window = span
            break
        except Exception:
            continue
    if not isinstance(logs, list):
        return unavailable("LOGS_UNAVAILABLE")

    swaps = [swap for swap in (parse_swap(log, target_is_token0) for log in logs) if swap]
    buys = [swap for swap in swaps if swap["kind"] == "buy"]
    sells = [swap for swap in swaps if swap["kind"] == "sell"]

    deadline = clock() + budget_sec
    buy_samples: list[float] = []
    seen: set[str] = set()
    for swap in reversed(buys):
        if len(buy_samples) >= MAX_SAMPLES or clock() > deadline:
            break
        if swap["tx"] in seen:
            continue
        seen.add(swap["tx"])
        try:
            value = buy_tax_sample(swap, rpc("eth_getTransactionReceipt", [swap["tx"]]), token, pool)
        except Exception:
            continue
        if value is not None:
            buy_samples.append(value)
    sell_samples: list[float] = []
    fee_outcomes: list[tuple[str, float | None]] = []
    skips: dict[str, int] = {}
    seen = set()
    for swap in reversed(sells):
        if len(fee_outcomes) >= MAX_SELL_SAMPLES or clock() > deadline:
            break
        if swap["tx"] in seen:
            continue
        seen.add(swap["tx"])
        if swap["sender"] == ROUTER_V2:
            try:
                value, reason = sell_tax_outcome(
                    swap, rpc("eth_getTransactionByHash", [swap["tx"]]), token)
            except Exception:
                value, reason = None, "TX_UNAVAILABLE"
        else:
            value, reason = None, "SENDER_NOT_V2_ROUTER"
        if value is not None:
            sell_samples.append(value)
        else:
            skips[reason] = skips.get(reason, 0) + 1
        try:
            fee_outcomes.append(sell_fee_event_outcome(
                swap, rpc("eth_getTransactionReceipt", [swap["tx"]]), token, pool))
        except Exception:
            fee_outcomes.append(("INCONCLUSIVE", None))

    if sells:
        ability = "SELLS_OBSERVED"
    elif len(buys) >= MIN_BUYS_FOR_SELL_SIGNAL:
        ability = "NO_SELLS_OBSERVED"
    else:
        ability = "SAMPLE_TOO_SMALL"
    return {
        "status": "OK",
        "reason": None,
        "window_blocks": window,
        "buys": len(buys),
        "sells": len(sells),
        "unique_buyers": len({swap["to"] for swap in buys}),
        "sell_ability": ability,
        "buy_tax": summarize_tax(buy_samples),
        "sell_tax": summarize_tax(sell_samples),
        "sell_tax_skips": skips,
        "sell_fee_events": summarize_fee_events(fee_outcomes),
        "sell_senders": top_senders(sells),
        "limits": LIMITS,
    }
