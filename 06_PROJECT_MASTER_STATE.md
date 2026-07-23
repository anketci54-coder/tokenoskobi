# 06 PROJECT MASTER STATE - TOKENOSKOBI

## CURRENT POSITION

CURRENT_VERSION=V4
CURRENT_ERA=ERA63
CURRENT_TITLE=Accelerated Paper Trading Core
CURRENT_STAGE=ERA63B_ACCELERATED_PAPER_TRADING_CORE_BUILD
CURRENT_STATUS=LOCAL_CORE_BUILD_VERIFIED
LAST_CLOSED_ERA=ERA62
NEXT_SAFE_STEP=ERA63C_END_TO_END_REPLAY_AND_COST_VALIDATION

## ERA63B BUILD

CORE_ENGINE=tools/era63_paper_trading_core_v1.py
CORE_CONFIG=config/era63_paper_trading_core_v1.json
CORE_TEST=tests/test_era63b_paper_trading_core_v1.py
BUILD_ARTIFACT=data/control/era63b_accelerated_paper_trading_core_build_v1.json
TESTS=13/13_PASS

BUILT_CAPABILITIES:

- Market/candle validation and liquidity gate
- Technical indicators: SMA, RSI, ATR, volatility
- Gross and cost-adjusted edge
- Bounded position sizing
- Simulated paper fill
- Fee, spread, slippage, MEV and gas model
- Portfolio P&L and drawdown
- Stage and total latency

## AUTHORITY STATE

PAPER_CALCULATION=true
PAPER_RUNTIME=DISABLED_PENDING_ERA63C_VALIDATION
UNATTENDED_RUNTIME=false
LIVE_TRADE=DISABLED
REAL_WALLET=false
REAL_SIGNING=false
REAL_ORDER=false
REAL_BROADCAST=false
