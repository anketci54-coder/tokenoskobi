# V2_46_NEXT_APPROVED_PHASE_SELECTION_NOAPI

STAMP_UTC=2026-06-27T11:07:58Z
MODE=LOCAL_ONLY_NOAPI_NO_PUSH

## RESULT

FINAL_GATE=PASS_V2_46_NEXT_APPROVED_PHASE_SELECTION_NOAPI
DECISION=V2_46_SELECTION_PASS_READY_FOR_DEX_CUSTOM_MICROSTRUCTURE_TA_PLAN
SELECTED_PHASE=V2_46_DEX_TECHNICAL_PATTERN_AND_CUSTOM_MICROSTRUCTURE_ENGINE_PLAN_NOAPI
NEXT=V2_46_DEX_TECHNICAL_PATTERN_AND_CUSTOM_MICROSTRUCTURE_ENGINE_PLAN_NOAPI
GITHUB_PUSH=false

## SELECTED CANONICAL ROUTE

V2_46_DEX_TECHNICAL_PATTERN_AND_CUSTOM_MICROSTRUCTURE_ENGINE_PLAN_NOAPI

## PURPOSE

V2_46 selects a DEX-native technical analysis path.

Classic lagging indicators such as MACD, EMA, RSI and MA crosses are not authority in this DEX engine. They may be context only, never command or confirmation authority.

The selected path requires custom DEX microstructure indicators and oscillators.

## DEX TA LOCKS

DEX_NATIVE_TA_REQUIRED=true
CUSTOM_INDICATOR_REQUIRED=true
MACD_EMA_RSI_NOT_AUTHORITY=true
CLASSIC_PATTERN_NOT_SOLE_SIGNAL=true
TA_PATTERN_REQUIRES_VOLUME_PROFILE=true
ORDER_CANCELLATION_THRESHOLD=0.80
GHOST_LIQUIDITY_SHORT_CIRCUIT=true
PATTERN_SPOOFING_GUARD_REQUIRED=true
MULTI_TIMEFRAME_DIVERGENCE_GUARD=true
LAGGING_INDICATOR_SYNC_GUARD=true
ONCHAIN_OVERDELIVERY_PRIORITY=true
NEGATIVE_ONCHAIN_OVERRIDES_TA=true

## CUSTOM INDICATOR FAMILY

- CI1: DEX_MOMENTUM_IMBALANCE_V1 | PURPOSE=Measure fast buy/sell pressure imbalance without lagging MA dependency.
- CI2: LIQUIDITY_ABSORPTION_RATIO_V1 | PURPOSE=Detect whether price move is supported by real pool/route depth.
- CI3: FLOW_PRESSURE_OSCILLATOR_V1 | PURPOSE=Oscillate between buy-flow pressure and sell-flow pressure under DEX microstructure.
- CI4: SLIPPAGE_STRESS_INDEX_V1 | PURPOSE=Detect whether apparent breakout is tradable or slippage trap.
- CI5: VOLUME_PROFILE_DIVERGENCE_V1 | PURPOSE=Reject candle pattern when real vertical volume profile does not support it.
- CI6: GHOST_LIQUIDITY_SCORE_V1 | PURPOSE=Detect liquidity that disappears or is economically non-credible.
- CI7: ONCHAIN_NEGATIVE_OVERRIDE_V1 | PURPOSE=Let negative whale/onchain evidence suppress lagging TA signals.
- CI8: TIME_SYNC_PATTERN_VALIDITY_V1 | PURPOSE=Check whether TA signal is temporally compatible with V2_45 TTL/window rules.


## TA GREY ZONES

- TAGZ1: Pattern Spoofing / Painting the Tape | ACTIVE_NOW=true | GUARD=PATTERN_SPOOFING_GUARD_REQUIRED
- TAGZ2: Order Cancellation / Ghost Liquidity | ACTIVE_NOW=true | GUARD=ORDER_CANCELLATION_THRESHOLD_0_80
- TAGZ3: Multi-Timeframe Divergence / Signal Obesity | ACTIVE_NOW=true | GUARD=MULTI_TIMEFRAME_DIVERGENCE_GUARD
- TAGZ4: Lagging Indicator Sync Risk | ACTIVE_NOW=true | GUARD=LAGGING_INDICATOR_SYNC_GUARD


## LEGACY INDICATOR POLICY

- LI1: MACD | AUTHORITY=DEMOTED_CONTEXT_ONLY | REASON=lagging after price already moves
- LI2: EMA | AUTHORITY=DEMOTED_CONTEXT_ONLY | REASON=lagging trend smoother; not DEX-fast enough
- LI3: RSI | AUTHORITY=DEMOTED_CONTEXT_ONLY | REASON=lagging oscillator; can stay overbought/oversold during manipulation
- LI4: MA_CROSS | AUTHORITY=DEMOTED_CONTEXT_ONLY | REASON=late confirmation, not primary DEX signal
- LI5: CLASSIC_CANDLE_PATTERN_ONLY | AUTHORITY=FORBIDDEN_AS_SOLE_SIGNAL | REASON=easy to spoof on shallow DEX liquidity


## DEX SIGNAL DOMAINS

- DX1: DEX Microstructure Momentum | FOCUS=fast flow imbalance, not moving averages
- DX2: Liquidity Depth And Slippage | FOCUS=route depth, pool depth, slippage stress
- DX3: Volume Profile Integrity | FOCUS=volume-profile support behind pattern
- DX4: Ghost Liquidity And Spoof Filter | FOCUS=order cancellation, disappearing depth, fake walls
- DX5: Onchain Override Layer | FOCUS=negative whale/onchain evidence beats lagging TA
- DX6: Multi-Timeframe Conflict Filter | FOCUS=micro/macro contradiction control
- DX7: TTL And Causality Alignment | FOCUS=V2_45 time window compatibility
- DX8: Short-Circuit Pattern Rejection | FOCUS=reject spoofed or unsupported patterns before queue bloat


## HARD BOUNDARIES

1. DEX_NATIVE_TA_REQUIRED=true
2. CUSTOM_INDICATOR_REQUIRED=true
3. MACD_EMA_RSI_NOT_AUTHORITY=true
4. CLASSIC_PATTERN_NOT_SOLE_SIGNAL=true
5. TA_PATTERN_REQUIRES_VOLUME_PROFILE=true
6. ORDER_CANCELLATION_THRESHOLD=0.80
7. GHOST_LIQUIDITY_SHORT_CIRCUIT=true
8. PATTERN_SPOOFING_GUARD_REQUIRED=true
9. MULTI_TIMEFRAME_DIVERGENCE_GUARD=true
10. LAGGING_INDICATOR_SYNC_GUARD=true
11. ONCHAIN_OVERDELIVERY_PRIORITY=true
12. NEGATIVE_ONCHAIN_OVERRIDES_TA=true
13. SINGLE_SOURCE_ALARM_FORBIDDEN=true
14. HUB_AND_SPOKE_REQUIRED=true
15. HG2_LATENCY_FALSE_POSITIVE_BUDGET_REQUIRED=true
16. API_RPC=false
17. LIVE_FEED=false
18. DB_WRITE=false
19. RUNTIME_APPLY=false
20. LIVE_TRADE=false
21. WALLET_ACCESS=false
22. PRIVATE_KEY_ACCESS=false
23. OUTBOUND_PACKET=false


## REQUIRED V2_46 SUBSTEPS

V2_46_DEX_TECHNICAL_PATTERN_AND_CUSTOM_MICROSTRUCTURE_ENGINE_PLAN_NOAPI
V2_46A_DEX_CUSTOM_INDICATOR_AND_OSCILLATOR_CONTRACT_LOCAL_NOAPI
V2_46B_PATTERN_SPOOFING_GHOST_LIQUIDITY_AND_OVERRIDE_GUARD_LOCAL_NOAPI
V2_46_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI

## FORBIDDEN

REAL_DATA_EXECUTION=false
API_RPC=false
LIVE_FEED=false
DB_WRITE=false
PANEL_WRITE=false
RUNTIME_APPLY=false
SERVICE_RESTART=false
TIMER_CHANGE=false
LIVE_DECISION=false
LIVE_TRADE=false
WALLET_ACCESS=false
PRIVATE_KEY_ACCESS=false
AI_TOOL_EXECUTION=false
OUTBOUND_PACKET=false
GITHUB_PUSH=false

## PUSH POLICY

SUBTASK_PUSH=false
FINAL_CLOSE_PUSH=true
GITHUB_PUSH_ONLY_AT_VXX_FINAL_CLOSE=true
