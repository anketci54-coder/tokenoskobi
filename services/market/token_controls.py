"""Token-level control hints read from the chain (owner, proxy, bytecode selectors).

Advisory only. Every result is a hint, never a verdict: a selector found in the
bytecode does not mean anyone can call it, and a missing one does not prove the
contract is safe (proxies keep logic elsewhere). A failed or impossible check is
reported as UNKNOWN, never as safe. Nothing here changes the decision or score.
"""
from __future__ import annotations

from typing import Any, Callable

MASK64 = (1 << 64) - 1


def _rol(value: int, count: int) -> int:
    count %= 64
    return ((value << count) | (value >> (64 - count))) & MASK64 if count else value


def _permute(lanes: list[list[int]]) -> None:
    """Keccak-f[1600] on lanes[x][y], in place."""
    r = 1
    for _ in range(24):
        c = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4] for x in range(5)]
        d = [c[(x + 4) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                lanes[x][y] ^= d[x]
        x, y = 1, 0
        current = lanes[x][y]
        for t in range(24):
            x, y = y, (2 * x + 3 * y) % 5
            current, lanes[x][y] = lanes[x][y], _rol(current, (t + 1) * (t + 2) // 2)
        for y in range(5):
            row = [lanes[x][y] for x in range(5)]
            for x in range(5):
                lanes[x][y] = row[x] ^ ((~row[(x + 1) % 5]) & row[(x + 2) % 5])
        for j in range(7):
            r = ((r << 1) ^ ((r >> 7) * 0x71)) % 256
            if r & 2:
                lanes[0][0] ^= 1 << ((1 << j) - 1)


def _sponge(data: bytes, suffix: int) -> bytes:
    rate = 136
    padded = bytearray(data)
    padded.append(suffix)
    while len(padded) % rate:
        padded.append(0)
    padded[-1] |= 0x80
    lanes = [[0] * 5 for _ in range(5)]
    for offset in range(0, len(padded), rate):
        block = padded[offset : offset + rate]
        for i in range(rate // 8):
            lanes[i % 5][i // 5] ^= int.from_bytes(block[8 * i : 8 * i + 8], "little")
        _permute(lanes)
    return b"".join(lanes[i % 5][i // 5].to_bytes(8, "little") for i in range(4))


def keccak256(data: bytes) -> bytes:
    """Original Keccak-256 (Ethereum), not NIST SHA3-256."""
    return _sponge(data, 0x01)


def selector(signature: str) -> str:
    return keccak256(signature.encode()).hex()[:8]


EIP1967_IMPLEMENTATION_SLOT = "0x" + format(
    int.from_bytes(keccak256(b"eip1967.proxy.implementation"), "big") - 1, "064x"
)
DEAD_OWNER = 0xDEAD
OWNER_SELECTORS = {"owner()": "0x8da5cb5b", "getOwner()": "0x893d20e8"}

SELECTOR_HINTS: dict[str, tuple[str, ...]] = {
    "MINT_SELECTOR_PRESENT": ("mint(address,uint256)", "mint(uint256)"),
    "PAUSE_SELECTOR_PRESENT": ("pause()", "unpause()"),
    "BLACKLIST_SELECTOR_PRESENT": (
        "blacklist(address)",
        "addToBlacklist(address)",
        "addBlackList(address)",
        "setBlacklist(address,bool)",
        "blacklistAddress(address,bool)",
    ),
    "FEE_SETTER_SELECTOR_PRESENT": (
        "setTaxFee(uint256)",
        "setFee(uint256)",
        "setBuyFee(uint256)",
        "setSellFee(uint256)",
        "setBuyTax(uint256)",
        "setSellTax(uint256)",
    ),
}
HINT_SELECTORS = {
    code: {selector(signature) for signature in signatures}
    for code, signatures in SELECTOR_HINTS.items()
}

LIMITS = (
    "Bunlar ipucudur, kesin hüküm değildir: bytecode'da seçici bulunması çağrılabilir "
    "olduğunu göstermez, bulunmaması güvenli olduğunu göstermez (proxy arkasında olabilir). "
    "Yapılamayan kontrol UNKNOWN sayılır, güvenli sayılmaz."
)


def push4_selectors(code: bytes) -> set[str]:
    """4-byte values pushed by PUSH4, skipping push data so it cannot be misread."""
    found: set[str] = set()
    i, size = 0, len(code)
    while i < size:
        op = code[i]
        if op == 0x63 and i + 5 <= size:
            found.add(code[i + 1 : i + 5].hex())
        i += 1 + (op - 0x5F if 0x60 <= op <= 0x7F else 0)
    return found


def scan_selector_hints(code_hex: str | None) -> list[str] | None:
    """Hint codes present in the bytecode, or None when the code cannot be scanned."""
    try:
        if not isinstance(code_hex, str) or code_hex in ("", "0x"):
            return None
        code = bytes.fromhex(code_hex[2:] if code_hex.startswith("0x") else code_hex)
    except ValueError:
        return None
    pushed = push4_selectors(code)
    return sorted(name for name, values in HINT_SELECTORS.items() if pushed & values)


def classify_owner(raw: Any, is_contract: bool | None) -> dict[str, Any]:
    """Owner state from a raw 32-byte eth_call result. Zero and 'no answer' differ."""
    unknown = {"status": "OWNER_UNKNOWN", "address": None}
    if not isinstance(raw, str) or len(raw) != 66 or not raw.startswith("0x"):
        return unknown
    try:
        value = int(raw, 16)
    except ValueError:
        return unknown
    if value >> 160:
        return unknown
    address = "0x" + format(value, "040x")
    if value in (0, DEAD_OWNER):
        return {"status": "OWNER_RENOUNCED", "address": address}
    if is_contract is True:
        return {"status": "OWNER_ACTIVE_CONTRACT", "address": address}
    if is_contract is False:
        return {"status": "OWNER_ACTIVE_EOA", "address": address}
    return {"status": "OWNER_ACTIVE_UNVERIFIED_TYPE", "address": address}


def classify_proxy(raw: Any) -> dict[str, Any]:
    """EIP-1967 implementation slot only. 'Not detected' is not 'not a proxy'."""
    if not isinstance(raw, str) or len(raw) != 66 or not raw.startswith("0x"):
        return {"status": "PROXY_CHECK_UNKNOWN", "implementation": None}
    try:
        value = int(raw, 16)
    except ValueError:
        return {"status": "PROXY_CHECK_UNKNOWN", "implementation": None}
    if value == 0:
        return {"status": "EIP1967_PROXY_NOT_DETECTED", "implementation": None}
    return {
        "status": "EIP1967_PROXY_DETECTED",
        "implementation": "0x" + format(value & ((1 << 160) - 1), "040x"),
    }


def collect_controls(
    code_hex: str | None,
    owner_raw: Any,
    call: Callable[[str], Any],
    get_code: Callable[[str], Any],
    get_storage: Callable[[str], Any],
) -> dict[str, Any]:
    """Gather all hints. The callables do the RPC; any failure becomes UNKNOWN."""
    source = "owner()" if classify_owner(owner_raw, None)["status"] != "OWNER_UNKNOWN" else None
    raw = owner_raw
    if source is None:
        try:
            raw = call(OWNER_SELECTORS["getOwner()"])
        except Exception:
            raw = None
        if classify_owner(raw, None)["status"] != "OWNER_UNKNOWN":
            source = "getOwner()"

    is_contract: bool | None = None
    owner = classify_owner(raw, None)
    if owner["status"] == "OWNER_ACTIVE_UNVERIFIED_TYPE":
        try:
            owner_code = get_code(owner["address"])
            if isinstance(owner_code, str):
                is_contract = owner_code not in ("0x", "0x0", "")
        except Exception:
            is_contract = None
        owner = classify_owner(raw, is_contract)
    owner["source"] = source

    try:
        proxy = classify_proxy(get_storage(EIP1967_IMPLEMENTATION_SLOT))
    except Exception:
        proxy = classify_proxy(None)

    hints = scan_selector_hints(code_hex)
    return {
        "owner": owner,
        "proxy": proxy,
        "selector_hints": hints if hints is not None else [],
        "selector_scan": "OK" if hints is not None else "UNAVAILABLE",
        "limits": LIMITS,
    }
