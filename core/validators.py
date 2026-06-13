#!/usr/bin/env python3
from .identity import (
    normalize_chain,
    normalize_address,
    is_valid_evm_address,
    make_token_uid,
    make_pair_uid,
    make_snapshot_uid,
    SUPPORTED_CHAINS,
)

BASE_QUOTE_ASSETS = {
    "bnb": {
        "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",  # WBNB
        "0x55d398326f99059ff775485246999027b3197955",  # USDT
        "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",  # USDC
        "0xe9e7cea3dedca5984780bafc599bd69add087d56",  # BUSD
    },
    "base": {
        "0x4200000000000000000000000000000000000006",  # WETH
        "0x833589fcd6edb6e08f4c7c32d4f71b54bdacef",  # USDC
        "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca",  # USDbC
    },
    "eth": {
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
        "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    },
}

def _err(errors, code, field=None, value=None):
    errors.append({"code": code, "field": field, "value": value})

def is_base_quote_asset(chain, address):
    c = normalize_chain(chain)
    a = normalize_address(address)
    return a in BASE_QUOTE_ASSETS.get(c, set())

def validate_token_identity(row):
    errors = []
    warnings = []

    chain = normalize_chain(row.get("chain"))
    token_address = normalize_address(row.get("token_address"))
    token_uid = str(row.get("token_uid") or "").strip()
    source = str(row.get("source") or "").strip()
    deployer = normalize_address(row.get("deployer_address"))

    if not chain:
        _err(errors, "CHAIN_EMPTY", "chain", chain)
    elif chain not in SUPPORTED_CHAINS:
        _err(errors, "UNSUPPORTED_CHAIN", "chain", chain)

    if not token_address:
        _err(errors, "TOKEN_ADDRESS_EMPTY", "token_address", token_address)
    elif not is_valid_evm_address(token_address):
        _err(errors, "TOKEN_ADDRESS_INVALID", "token_address", token_address)
    elif is_base_quote_asset(chain, token_address):
        _err(errors, "TOKEN_IS_BASE_OR_QUOTE_ASSET", "token_address", token_address)

    if deployer and not is_valid_evm_address(deployer):
        _err(errors, "DEPLOYER_ADDRESS_INVALID", "deployer_address", deployer)

    if not source:
        _err(errors, "SOURCE_EMPTY", "source", source)

    expected_uid = None
    if chain and token_address and is_valid_evm_address(token_address):
        expected_uid = make_token_uid(chain, token_address)
        if token_uid and token_uid != expected_uid:
            _err(errors, "TOKEN_UID_MISMATCH", "token_uid", token_uid)
        if not token_uid:
            _err(errors, "TOKEN_UID_EMPTY", "token_uid", token_uid)

    name = str(row.get("name") or "").strip()
    symbol = str(row.get("symbol") or "").strip()
    if not name and not symbol:
        warnings.append({"code": "NAME_SYMBOL_BOTH_EMPTY"})

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "normalized": {
            "chain": chain,
            "token_address": token_address,
            "deployer_address": deployer,
            "token_uid": expected_uid or token_uid,
            "source": source,
            "name": name,
            "symbol": symbol,
        }
    }

def validate_pair_identity(row):
    errors = []
    warnings = []

    chain = normalize_chain(row.get("chain"))
    token_address = normalize_address(row.get("token_address"))
    pair_address = normalize_address(row.get("pair_address"))
    token_uid = str(row.get("token_uid") or "").strip()
    pair_uid = str(row.get("pair_uid") or "").strip()
    source = str(row.get("source") or "").strip()

    if not chain:
        _err(errors, "CHAIN_EMPTY", "chain", chain)
    elif chain not in SUPPORTED_CHAINS:
        _err(errors, "UNSUPPORTED_CHAIN", "chain", chain)

    if not token_address:
        _err(errors, "TOKEN_ADDRESS_EMPTY", "token_address", token_address)
    elif not is_valid_evm_address(token_address):
        _err(errors, "TOKEN_ADDRESS_INVALID", "token_address", token_address)
    elif is_base_quote_asset(chain, token_address):
        _err(errors, "TOKEN_IS_BASE_OR_QUOTE_ASSET", "token_address", token_address)

    if not pair_address:
        _err(errors, "PAIR_ADDRESS_EMPTY", "pair_address", pair_address)
    elif not is_valid_evm_address(pair_address):
        _err(errors, "PAIR_ADDRESS_INVALID", "pair_address", pair_address)

    if token_address and pair_address and token_address == pair_address:
        _err(errors, "TOKEN_ADDRESS_EQUALS_PAIR_ADDRESS", "pair_address", pair_address)

    if not source:
        _err(errors, "SOURCE_EMPTY", "source", source)

    expected_token_uid = None
    expected_pair_uid = None

    if chain and token_address and is_valid_evm_address(token_address):
        expected_token_uid = make_token_uid(chain, token_address)
        if not token_uid:
            _err(errors, "TOKEN_UID_EMPTY", "token_uid", token_uid)
        elif token_uid != expected_token_uid:
            _err(errors, "TOKEN_UID_MISMATCH", "token_uid", token_uid)

    if chain and pair_address and is_valid_evm_address(pair_address):
        expected_pair_uid = make_pair_uid(chain, pair_address)
        if not pair_uid:
            _err(errors, "PAIR_UID_EMPTY", "pair_uid", pair_uid)
        elif pair_uid != expected_pair_uid:
            _err(errors, "PAIR_UID_MISMATCH", "pair_uid", pair_uid)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "normalized": {
            "chain": chain,
            "token_address": token_address,
            "pair_address": pair_address,
            "token_uid": expected_token_uid or token_uid,
            "pair_uid": expected_pair_uid or pair_uid,
            "source": source,
        }
    }

def validate_snapshot_identity(row):
    errors = []
    warnings = []

    kind = str(row.get("kind") or "").strip().lower()
    chain = normalize_chain(row.get("chain"))
    token_uid = str(row.get("token_uid") or "").strip()
    pair_uid = str(row.get("pair_uid") or "").strip()
    pair_address = normalize_address(row.get("pair_address"))
    snapshot_uid = str(row.get("snapshot_uid") or "").strip()
    observed_at_utc = str(row.get("observed_at_utc") or "").strip()
    source = str(row.get("source") or "").strip()

    if kind not in {"liquidity", "market", "holder", "risk", "deployer", "narrative"}:
        _err(errors, "SNAPSHOT_KIND_INVALID", "kind", kind)

    if not chain:
        _err(errors, "CHAIN_EMPTY", "chain", chain)
    elif chain not in SUPPORTED_CHAINS:
        _err(errors, "UNSUPPORTED_CHAIN", "chain", chain)

    if not token_uid:
        _err(errors, "TOKEN_UID_EMPTY", "token_uid", token_uid)

    if not pair_uid:
        _err(errors, "PAIR_UID_EMPTY", "pair_uid", pair_uid)

    if not pair_address:
        _err(errors, "PAIR_ADDRESS_EMPTY", "pair_address", pair_address)
    elif not is_valid_evm_address(pair_address):
        _err(errors, "PAIR_ADDRESS_INVALID", "pair_address", pair_address)

    if not observed_at_utc:
        _err(errors, "OBSERVED_AT_EMPTY", "observed_at_utc", observed_at_utc)

    if not source:
        _err(errors, "SOURCE_EMPTY", "source", source)

    expected_snapshot_uid = None
    if kind and token_uid and pair_uid and observed_at_utc and source and kind in {"liquidity", "market", "holder", "risk", "deployer", "narrative"}:
        expected_snapshot_uid = make_snapshot_uid(kind, token_uid, pair_uid, observed_at_utc, source)
        if not snapshot_uid:
            _err(errors, "SNAPSHOT_UID_EMPTY", "snapshot_uid", snapshot_uid)
        elif snapshot_uid != expected_snapshot_uid:
            _err(errors, "SNAPSHOT_UID_MISMATCH", "snapshot_uid", snapshot_uid)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "normalized": {
            "kind": kind,
            "chain": chain,
            "token_uid": token_uid,
            "pair_uid": pair_uid,
            "pair_address": pair_address,
            "snapshot_uid": expected_snapshot_uid or snapshot_uid,
            "observed_at_utc": observed_at_utc,
            "source": source,
        }
    }

def detect_duplicate_identities(rows, key_fields):
    seen = {}
    duplicates = []
    for idx, row in enumerate(rows, start=1):
        key = tuple(str(row.get(f) or "").strip().lower() for f in key_fields)
        if key in seen:
            duplicates.append({
                "first_index": seen[key],
                "duplicate_index": idx,
                "key_fields": key_fields,
                "key": key,
            })
        else:
            seen[key] = idx
    return duplicates
