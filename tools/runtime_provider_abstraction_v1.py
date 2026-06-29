
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ProviderConfig:
    name: str
    tier: str
    payg: bool
    free_or_low_cost: bool
    enabled_live: bool
    read_only: bool
    max_calls_per_candidate: int

PROVIDERS = [
    ProviderConfig("alchemy","premium",True,False,False,True,3),
    ProviderConfig("quicknode","premium",True,False,False,True,3),
    ProviderConfig("ankr","low_cost",False,True,False,True,5),
    ProviderConfig("nodereal","low_cost",False,True,False,True,5),
    ProviderConfig("public_rpc","fallback",False,True,False,True,2)
]

def provider_summary():
    return {
        "provider_count": len(PROVIDERS),
        "payg_count": sum(1 for p in PROVIDERS if p.payg),
        "low_cost_count": sum(1 for p in PROVIDERS if p.free_or_low_cost),
        "live_enabled_count": sum(1 for p in PROVIDERS if p.enabled_live),
        "read_only_count": sum(1 for p in PROVIDERS if p.read_only),
        "names": [p.name for p in PROVIDERS]
    }

def select_provider(stage):
    if stage == "cheap_scan":
        return ["ankr","nodereal","public_rpc"]
    if stage == "premium_confirm":
        return ["alchemy","quicknode"]
    if stage == "critical_cross_check":
        return ["alchemy","quicknode","ankr"]
    raise ValueError("unknown_stage")
