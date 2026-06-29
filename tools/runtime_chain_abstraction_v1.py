from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ChainConfig:
    key: str
    chain_id: int
    family: str
    native_symbol: str
    dex_support: bool
    swap_support: bool
    rpc_tier: str
    live_enabled: bool=False

CHAINS = [
    ChainConfig("ethereum",1,"evm","ETH",True,True,"premium"),
    ChainConfig("bsc",56,"evm","BNB",True,True,"primary"),
    ChainConfig("base",8453,"evm","ETH",True,True,"primary"),
    ChainConfig("arbitrum",42161,"evm","ETH",True,True,"standard"),
    ChainConfig("optimism",10,"evm","ETH",True,True,"standard"),
    ChainConfig("polygon",137,"evm","MATIC",True,True,"standard"),
    ChainConfig("avalanche",43114,"evm","AVAX",True,True,"standard"),
    ChainConfig("fantom",250,"evm","FTM",True,True,"standard"),
    ChainConfig("linea",59144,"evm","ETH",True,True,"standard"),
    ChainConfig("scroll",534352,"evm","ETH",True,True,"standard"),
    ChainConfig("zksync",324,"evm","ETH",True,True,"standard"),
    ChainConfig("blast",81457,"evm","ETH",True,True,"standard"),
    ChainConfig("solana",101,"non_evm","SOL",True,True,"future_adapter"),
    ChainConfig("tron",728126428,"non_evm","TRX",True,True,"future_adapter"),
    ChainConfig("bitcoin",0,"utxo","BTC",False,False,"future_adapter")
]

def get_chain(key):
    for c in CHAINS:
        if c.key == key:
            return c
    raise KeyError(key)

def registry_summary():
    return {
        "chain_count": len(CHAINS),
        "evm_count": sum(1 for c in CHAINS if c.family == "evm"),
        "non_evm_count": sum(1 for c in CHAINS if c.family == "non_evm"),
        "utxo_count": sum(1 for c in CHAINS if c.family == "utxo"),
        "swap_supported_count": sum(1 for c in CHAINS if c.swap_support),
        "live_enabled_count": sum(1 for c in CHAINS if c.live_enabled),
        "keys": [c.key for c in CHAINS]
    }
