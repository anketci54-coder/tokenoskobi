"""Tokenoskobi's BSC pool policy. No execution, signing or CEX connectors.

Deployment identities: https://developer.pancakeswap.finance/contracts/v2/addresses
and https://developer.pancakeswap.finance/contracts/v3/addresses (2026-10-16).
Pool membership comes from RPC reads, never names or vendor DEX labels.
"""
from __future__ import annotations

import re
from types import MappingProxyType

ADDRESS = re.compile(r"0x[0-9a-f]{40}")
WORD = re.compile(r"0x[0-9a-fA-F]{64}")
ZERO = "0x" + "0" * 40
POLICY_ID = "tokenoskobi.bsc-pancakeswap-v2-v3.2026-10-16"
DEPLOYMENTS = MappingProxyType({
    "v2": ("0xca143ce32fe78f1f7019d7d551a6402fc5350c73",
           "0x10ed43c718714eb63d5aa57b78b54704e256024e"),
    "v3": ("0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865",
           "0x1b81d678ffb9c0263b24a97847620c99d213eb14"),
})
# Address identities from PancakeSwap's BSC token list and the issuer sources
# below, retrieved 2026-10-16:
# https://github.com/pancakeswap/token-list/blob/main/src/tokens/pancakeswap-extended.json
# This is a bounded exclusion registry, not a claim that every other asset is
# non-stable. Symbols, prices, and CEX listings never classify target assets.
STABLE_SOURCE = "https://github.com/pancakeswap/token-list/blob/main/src/tokens/pancakeswap-extended.json"
STABLE_TARGETS = MappingProxyType({
    "0x55d398326f99059ff775485246999027b3197955": "USDT",
    "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d": "USDC",
    "0xe9e7cea3dedca5984780bafc599bd69add087d56": "BUSD",
    "0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3": "DAI",
    "0x40af3827f39d0eacbf4a168f8d4ee67c121d11c9": "TUSD",
    "0x14016e85a25aeb13065688cafb43044c2ef86784": "TUSD_OLD",
    "0xc5f0f7b66764f6ec8c8dff7ba683102295e16409": "FDUSD",
    "0x4bd17003473389a42daf6a0a729f6fdb328bbbd7": "VAI",
    "0x0782b6d8c4551b9760e74c0545a9bcd90bdc41e5": "lisUSD",
    "0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d": "USD1",
})
ISSUER_SOURCES = MappingProxyType({
    "TUSD": "https://tusd.io/", "TUSD_OLD": "https://tusd.io/",
    "FDUSD": "https://www.firstdigitallabs.com/fdusd",
    "USD1": "https://docs.worldlibertyfinancial.com/usd1-token/contract-addresses",
})
# First four bytes of Keccak-256 of the canonical Solidity signatures.
SELECTORS = MappingProxyType({
    "factory": "0xc45a0155", "token0": "0x0dfe1681", "token1": "0xd21220a7",
    "fee": "0xddca3f43", "getPair": "0xe6a43905", "getPool": "0x1698ee82",
})


class EvidenceError(ValueError):
    """A fixed Tokenoskobi reason code, safe to include in an evidence packet."""


def valid_address(value):
    return isinstance(value, str) and bool(ADDRESS.fullmatch(value)) and value != ZERO


def decode_address(raw):
    if not isinstance(raw, str) or not WORD.fullmatch(raw) or int(raw[2:26], 16):
        raise EvidenceError("INVALID_ABI_ADDRESS")
    value = "0x" + raw[-40:].lower()
    if not valid_address(value):
        raise EvidenceError("EMPTY_ABI_ADDRESS")
    return value


def target_policy(token):
    token = token.lower() if isinstance(token, str) else ""
    symbol = STABLE_TARGETS.get(token)
    return {"policy_id": POLICY_ID, "chain_id": 56, "target_token_address": token,
            "status": "STABLECOIN_TARGET_EXCLUDED" if symbol else "NOT_IN_VERIFIED_STABLE_REGISTRY",
            "stable_symbol": symbol, "registry_source": ISSUER_SOURCES.get(symbol, STABLE_SOURCE),
            "coverage": "BOUNDED_ADDRESS_REGISTRY", "stable_quotes_allowed": True,
            "cex_market_data_allowed": False, "cex_listing_excludes_asset": False}


def pool_is_verified(row, target=None):
    """Recheck evidence bindings at selection and decision/observation boundaries."""
    p = row.get("provenance") or {}
    version = p.get("version")
    if not isinstance(version, str) or version not in DEPLOYMENTS:
        return False
    tokens = (p.get("token0"), p.get("token1"))
    base, quote = row.get("base_token_address"), row.get("quote_token_address")
    return bool(
        p.get("verified") is True and p.get("policy_id") == POLICY_ID
        and type(p.get("chain_id")) is int and p["chain_id"] == 56
        and type(p.get("block_number")) is int and p["block_number"] > 0
        and (p.get("factory"), p.get("router")) == DEPLOYMENTS[version]
        and valid_address(row.get("address")) and p.get("pool_address") == row["address"]
        and all(valid_address(t) for t in tokens) and tokens[0] < tokens[1]
        and valid_address(base) and valid_address(quote) and base != quote
        and set(tokens) == {base, quote} and row.get("orientation_verified") is True
        and row.get("target_token_address") in tokens
        and (target is None or row.get("target_token_address") == target)
        and (version == "v2" or type(p.get("fee")) is int and 0 < p["fee"] < 2**24)
    )


class PoolVerifier:
    """One RPC snapshot per market request, with deployment checks reused locally.

    The selected provider is rechecked for chain 56. All code and contract reads
    use the same explicit block; no positive verification survives an RPC error.
    A trusted RPC is an evidence dependency, not a cryptographic state proof.
    """
    def __init__(self, rpc, selected):
        self.rpc, self.selected = rpc, selected
        self.block = None
        self.deployments = set()
        self.snapshot_error = None

    def _snapshot(self):
        if self.snapshot_error:
            raise EvidenceError(self.snapshot_error)
        if self.block is not None:
            return
        try:
            if not self.selected:
                raise EvidenceError("NO_BSC_RPC")
            self.url = self.selected["url"]
            if self.rpc(self.url, "eth_chainId", []) != "0x38":
                raise EvidenceError("WRONG_CHAIN")
            block = self.rpc(self.url, "eth_blockNumber", [])
            if not isinstance(block, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", block) or int(block, 16) <= 0:
                raise EvidenceError("INVALID_BLOCK")
            self.block = block
        except Exception:
            self.snapshot_error = "BSC_SNAPSHOT_UNAVAILABLE"
            raise EvidenceError(self.snapshot_error) from None

    def _call(self, contract, data):
        return self.rpc(self.url, "eth_call", [{"to": contract, "data": data}, self.block])

    def _code(self, contract):
        code = self.rpc(self.url, "eth_getCode", [contract, self.block])
        if not isinstance(code, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})+", code) or not int(code[2:], 16):
            raise EvidenceError("CONTRACT_CODE_UNVERIFIED")

    def verify(self, row):
        result = {"verified": False, "policy_id": POLICY_ID, "status": "UNVERIFIED"}
        try:
            pool = row.get("address")
            if not valid_address(pool) or row.get("network") != "bsc" or row.get("orientation_verified") is not True:
                raise EvidenceError("POOL_IDENTITY_UNVERIFIED")
            self._snapshot()
            self._code(pool)
            factory = decode_address(self._call(pool, SELECTORS["factory"]))
            version = next((v for v, (f, _) in DEPLOYMENTS.items() if f == factory), None)
            if version is None:
                result.update(status="REJECTED", reason="UNSUPPORTED_FACTORY", factory=factory)
                return result
            _, router = DEPLOYMENTS[version]
            if version not in self.deployments:
                self._code(factory)
                self._code(router)
                if decode_address(self._call(router, SELECTORS["factory"])) != factory:
                    raise EvidenceError("ROUTER_FACTORY_MISMATCH")
                self.deployments.add(version)
            token0 = decode_address(self._call(pool, SELECTORS["token0"]))
            token1 = decode_address(self._call(pool, SELECTORS["token1"]))
            if token0 >= token1 or {token0, token1} != {row.get("base_token_address"), row.get("quote_token_address")}:
                raise EvidenceError("POOL_TOKEN_MISMATCH")
            parameters = token0[2:].zfill(64) + token1[2:].zfill(64)
            fee = None
            if version == "v3":
                raw = self._call(pool, SELECTORS["fee"])
                if not isinstance(raw, str) or not WORD.fullmatch(raw) or not 0 < int(raw, 16) < 2**24:
                    raise EvidenceError("POOL_FEE_UNVERIFIED")
                fee = int(raw, 16)
                parameters += f"{fee:064x}"
            lookup = SELECTORS["getPair" if version == "v2" else "getPool"] + parameters
            if decode_address(self._call(factory, lookup)) != pool:
                raise EvidenceError("FACTORY_MEMBERSHIP_MISMATCH")
            result.update(verified=True, status="VERIFIED", chain_id=56,
                          block_number=int(self.block, 16), provider=self.selected.get("name"),
                          version=version, pool_address=pool, factory=factory, router=router,
                          token0=token0, token1=token1, fee=fee,
                          method="POOL_FACTORY_TOKENS_AND_FACTORY_REGISTRATION_AT_BLOCK")
        except EvidenceError as exc:
            result["reason"] = str(exc)
        except Exception as exc:
            # Never expose endpoint URLs, credentials or arbitrary provider text.
            result["reason"] = "RPC_EVIDENCE_UNAVAILABLE:" + type(exc).__name__
        return result
