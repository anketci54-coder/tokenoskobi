# 07 PROJECT HANDOFF - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE=ERA63E_ADAPTIVE_ALWAYS_ON_MARKET_RUNTIME
CURRENT_STATUS=ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE_RATE_LIMIT_HARDENED
NEXT_SAFE_STEP=ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE

The resident BSC block-event service remains active. Diagnostic evidence confirmed GeckoTerminal HTTP 429 rate limiting. The runtime now uses a lower provider request budget, slower adaptive full-refresh bounds and exponential fail-closed provider backoff while continuing to process every BSC block.

Evidence:
- `data/control/era63e_rate_limit_reliability_repair_v1.json`
- `data/control/era63e_always_on_market_runtime_binding_v1.json`
- `runtime/era63e/always_on_state_v1.json`

ERA63 is not closed. Post-repair natural cycles must verify refresh reliability before technical-line closure. Paper/live trade and wallet, signing, order and broadcast remain disabled.
