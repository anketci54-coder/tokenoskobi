#!/usr/bin/env python3
import hashlib
import re
from datetime import datetime, timezone

ZERO_ADDR = "0x0000000000000000000000000000000000000000"
EVM_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

CHAIN_ALIASES = {
    "bsc": "bnb",
    "binance": "bnb",
    "binance smart chain": "bnb",
    "bnb smart chain": "bnb",
    "bnbchain": "bnb",
    "basechain": "base",
    "ethereum": "eth",
    "ethereum mainnet": "eth",
}

SUPPORTED_CHAINS = {"base", "bnb", "eth"}

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def normalize_chain(chain):
    if chain is None:
        return ""
    c = str(chain).strip().lower()
    c = CHAIN_ALIASES.get(c, c)
    return c

def normalize_address(address):
    if address is None:
        return ""
    a = str(address).strip().lower()
    return a

def is_valid_evm_address(address):
    a = normalize_address(address)
    return bool(EVM_RE.match(a)) and a != ZERO_ADDR

def require_chain(chain):
    c = normalize_chain(chain)
    if not c:
        raise ValueError("chain_empty")
    if c not in SUPPORTED_CHAINS:
        raise ValueError(f"unsupported_chain:{c}")
    return c

def require_address(address, field_name="address"):
    a = normalize_address(address)
    if not a:
        raise ValueError(f"{field_name}_empty")
    if not is_valid_evm_address(a):
        raise ValueError(f"{field_name}_invalid:{a}")
    return a

def short_hash(text, length=24):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]

def make_token_uid(chain, token_address):
    c = require_chain(chain)
    a = require_address(token_address, "token_address")
    return "tok_" + short_hash(f"{c}:{a}")

def make_pair_uid(chain, pair_address):
    c = require_chain(chain)
    a = require_address(pair_address, "pair_address")
    return "pair_" + short_hash(f"{c}:{a}")

def make_snapshot_uid(kind, token_uid, pair_uid, observed_at_utc, source):
    k = str(kind).strip().lower()
    tu = str(token_uid or "").strip()
    pu = str(pair_uid or "").strip()
    obs = str(observed_at_utc or "").strip()
    src = str(source or "").strip()
    if k not in {"liquidity", "market", "holder", "risk", "deployer", "narrative"}:
        raise ValueError(f"snapshot_kind_invalid:{k}")
    if not tu:
        raise ValueError("token_uid_empty")
    if not pu:
        raise ValueError("pair_uid_empty")
    if not obs:
        raise ValueError("observed_at_utc_empty")
    if not src:
        raise ValueError("source_empty")
    return "snap_" + short_hash(f"{k}:{tu}:{pu}:{obs}:{src}", 32)

def canonical_token_identity(chain, token_address, deployer_address=None, name=None, symbol=None, source="MANUAL_PILOT"):
    c = require_chain(chain)
    token = require_address(token_address, "token_address")
    deployer = normalize_address(deployer_address)
    if deployer and not is_valid_evm_address(deployer):
        raise ValueError(f"deployer_address_invalid:{deployer}")
    return {
        "chain": c,
        "token_address": token,
        "deployer_address": deployer,
        "token_uid": make_token_uid(c, token),
        "name": "" if name is None else str(name).strip(),
        "symbol": "" if symbol is None else str(symbol).strip(),
        "source": "" if source is None else str(source).strip(),
    }

def canonical_pair_identity(chain, token_address, pair_address, source="MANUAL_PILOT", dex_name=None):
    c = require_chain(chain)
    token = require_address(token_address, "token_address")
    pair = require_address(pair_address, "pair_address")
    return {
        "chain": c,
        "token_address": token,
        "pair_address": pair,
        "token_uid": make_token_uid(c, token),
        "pair_uid": make_pair_uid(c, pair),
        "source": "" if source is None else str(source).strip(),
        "dex_name": "" if dex_name is None else str(dex_name).strip(),
    }
