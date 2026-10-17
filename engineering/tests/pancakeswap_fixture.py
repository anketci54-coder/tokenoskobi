"""Synthetic ABI transport only; never evidence of an actual BSC deployment."""
FACTORIES = {
    "v2": "0xca143ce32fe78f1f7019d7d551a6402fc5350c73",
    "v3": "0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865",
}
ROUTERS = {
    "v2": "0x10ed43c718714eb63d5aa57b78b54704e256024e",
    "v3": "0x1b81d678ffb9c0263b24a97847620c99d213eb14",
}


def word(value):
    return "0x" + (value[2:] if isinstance(value, str) else f"{value:x}").zfill(64)


def verified_pool(token, quote, pool):
    t0, t1 = sorted((token, quote))
    return {"address": pool, "network": "bsc", "base_token_address": token,
            "quote_token_address": quote, "target_token_address": token,
            "target_side": "base", "orientation_verified": True,
            "provenance": {"verified": True, "policy_id": "tokenoskobi.bsc-pancakeswap-v2-v3.2026-10-16",
                           "chain_id": 56, "block_number": 1048576, "version": "v2",
                           "factory": FACTORIES["v2"], "router": ROUTERS["v2"],
                           "pool_address": pool, "token0": t0, "token1": t1}}


class BscPoolFixture:
    def __init__(self, pools):
        self.pools = pools
        self.calls = []

    def __call__(self, url, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId":
            return "0x38"
        if method == "eth_blockNumber":
            return "0x100000"
        if method == "eth_getCode":
            return "0x6000"
        assert method == "eth_call", method
        to, data = params[0]["to"], params[0]["data"]
        if to in ROUTERS.values() and data == "0xc45a0155":
            return word(FACTORIES[next(v for v, address in ROUTERS.items() if address == to)])
        if to in self.pools:
            row = self.pools[to]
            t0, t1 = sorted(row["tokens"])
            return {"0xc45a0155": word(row.get("factory") or FACTORIES[row["version"]]),
                    "0x0dfe1681": word(t0), "0xd21220a7": word(t1),
                    "0xddca3f43": word(row.get("fee", 500))}[data]
        for pool, row in self.pools.items():
            t0, t1 = sorted(row["tokens"])
            parameters = word(t0)[2:] + word(t1)[2:]
            lookup = "0xe6a43905" + parameters if row["version"] == "v2" else (
                "0x1698ee82" + parameters + word(row.get("fee", 500))[2:])
            if to == FACTORIES[row["version"]] and data == lookup:
                return word(pool) if row.get("registered", True) else word(0)
        raise AssertionError((method, params))
