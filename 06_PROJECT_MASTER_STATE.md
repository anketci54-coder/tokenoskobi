# 06 PROJECT MASTER STATE - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_STAGE=ERA63E_ADAPTIVE_ALWAYS_ON_MARKET_RUNTIME
CURRENT_STATUS=ALWAYS_ON_BLOCK_EVENT_RUNTIME_ACTIVE_RATE_LIMIT_HARDENED
NEXT_SAFE_STEP=ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE

## ACTIVE RUNTIME

- `tokenoskobi-era63e-always-on-market.service`: ACTIVE, resident, restart-always
- BSC block-event observation: ACTIVE
- Fixed 15-minute timer: DISABLED
- GeckoTerminal market/technical refresh: ADAPTIVE + RATE-LIMIT BACKOFF
- Request budget: max 2 pools, 2.5 sec request spacing
- Refresh bounds: 300..900 sec
- HTTP 429 backoff: 900..3600 sec
- Tests: `69/69_PASS`

## AUTHORITY

```text
OBSERVATION_RUNTIME=true
PAPER_RUNTIME=false
LIVE_TRADE=DISABLED
REAL_WALLET=false
REAL_SIGNING=false
REAL_ORDER=false
REAL_BROADCAST=false
```

ERA63 remains open until post-repair natural refresh reliability and continuity are observed.
