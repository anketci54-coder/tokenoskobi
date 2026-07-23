# ERA63D REAL MARKET AND TECHNICAL RUNTIME BINDING

STATUS=READONLY_REAL_MARKET_TECHNICAL_RUNTIME_ACTIVE
PROVIDER=GECKOTERMINAL_KEYLESS_PUBLIC
NETWORK=bsc
SUCCESSFUL_POOLS=1
TESTS=51/51_PASS
PAPER_RUNTIME=false
LIVE_TRADE=DISABLED
TIMER=enabled/active
NEXT_SAFE_STEP=ERA63E_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE

## Real activation-cycle pools

- `BSB / USDT 0.007%` `0x26a8e4591b7a0efcd45a577ad0d54aa64a99efaf2546ad4d5b0454c99eb70eab`
  - liquidity_usd: `9862192.8925`
  - volume_h24_usd: `5621228.57304135`
  - engine_action: `WAIT`
  - runtime_status: `OBSERVE_WAIT`
  - paper_action: `DISABLED`

## Fail-closed limits

- Direct token-tax source is not bound.
- Direct mempool measurement is not bound.
- Pool reserves are estimated from TVL and price.
- Coordinated wallet/onchain/whale/news intelligence is not bound.
