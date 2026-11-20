"""How much of a Pancake V2 pair's liquidity-provider (LP) supply sits at the burn addresses.

Advisory only. LP tokens held by the zero or 0x...dEaD address can never be redeemed, so a high burned
share means the pool's liquidity cannot be pulled by the people who added it. A low burned share does
NOT mean the liquidity is unlocked: it may sit in a locker contract this module does not recognise.
Anything that cannot be read is UNKNOWN, never safe.
"""
from __future__ import annotations

from typing import Any, Callable

from services.market.swap_behavior import RESERVES_CALL
from services.market.token_controls import selector

ZERO_ADDRESS = "0x" + "0" * 40
DEAD_ADDRESS = "0x" + "0" * 36 + "dead"
TOTAL_SUPPLY_CALL = "0x" + selector("totalSupply()")
BALANCE_OF_SELECTOR = "0x" + selector("balanceOf(address)")
MIN_LIQUIDITY_WEI = 1000  # a V2 pair permanently locks this much LP at the zero address on first mint
LIMITS = ("Yakılan pay yalnızca sıfır ve 0x…dEaD adreslerindeki LP'dir. Düşük pay 'kilitli değil' demek "
          "değildir: LP, tanınmayan bir kilit sözleşmesinde olabilir. Okunamayan UNKNOWN sayılır.")

Call = Callable[[str, str], Any]


def unavailable(reason: str) -> dict[str, Any]:
    return {"status": "UNKNOWN", "reason": reason, "burned_pct": None, "limits": LIMITS}


def _word(raw: Any, words: int = 1) -> list[int] | None:
    if not isinstance(raw, str) or len(raw) != 2 + 64 * words or not raw.startswith("0x"):
        return None
    try:
        return [int(raw[2 + 64 * i: 66 + 64 * i], 16) for i in range(words)]
    except ValueError:
        return None


def _balance(call: Call, pool: str, holder: str) -> int | None:
    data = BALANCE_OF_SELECTOR + "0" * 24 + holder[2:]
    value = _word(call(pool, data))
    return value[0] if value else None


def collect_lp(pool: str, call: Call) -> dict[str, Any]:
    """`call(to, data)` performs an eth_call and returns the hex result. May raise; never trusted."""
    try:
        if _word(call(pool, RESERVES_CALL), 3) is None:
            return unavailable("POOL_NOT_V2_PAIR")
        supply = _word(call(pool, TOTAL_SUPPLY_CALL))
        zero = _balance(call, pool, ZERO_ADDRESS)
        dead = _balance(call, pool, DEAD_ADDRESS)
    except Exception as exc:
        return unavailable(f"LP_READ_FAILED:{type(exc).__name__}")
    if supply is None or zero is None or dead is None:
        return unavailable("LP_READ_FAILED")
    total = supply[0]
    if total <= 0:
        return unavailable("LP_SUPPLY_EMPTY")
    if zero + dead > total:
        return unavailable("LP_INCONSISTENT")
    return {
        "status": "OK",
        "pool": pool,
        "total_supply": str(total),  # string: LP supplies exceed what JSON numbers hold exactly
        "burned_pct": round(100.0 * (zero + dead) / total, 4),
        "zero_pct": round(100.0 * zero / total, 4),
        "dead_pct": round(100.0 * dead / total, 4),
        "limits": LIMITS,
    }
