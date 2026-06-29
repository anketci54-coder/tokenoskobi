from dataclasses import dataclass

@dataclass(frozen=True)
class RPCCostPolicy:
    alchemy_payg: bool=True
    hybrid_rpc_model: bool=True
    cache_required: bool=True
    fallback_required: bool=True
    monthly_budget_guard: bool=True
    api_call=False

POLICY=RPCCostPolicy()
