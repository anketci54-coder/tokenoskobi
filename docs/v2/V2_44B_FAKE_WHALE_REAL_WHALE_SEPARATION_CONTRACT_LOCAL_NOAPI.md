# V2_44B_FAKE_WHALE_REAL_WHALE_SEPARATION_CONTRACT_LOCAL_NOAPI

STAMP_UTC=2026-06-27T10:30:00Z
MODE=LOCAL_ONLY_NOAPI_NO_PUSH

## RESULT

FINAL_GATE=PASS_V2_44B_FAKE_WHALE_REAL_WHALE_SEPARATION_CONTRACT_LOCAL_NOAPI
DECISION=V2_44B_FAKE_REAL_WHALE_SEPARATION_PASS_READY_FOR_FINAL_CLOSE
NEXT=V2_44_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI
GITHUB_PUSH=false

## PURPOSE

V2_44B defines the fake whale versus real whale candidate separation contract.

Default posture: fake/unknown until positively proven.

No whale signal has trade, runtime, wallet, API/RPC, live-feed, or outbound-packet authority.

## SEPARATION CONTRACT

FAKE_WHALE_DEFAULT=true
REAL_WHALE_REQUIRES_POSITIVE_EVIDENCE=true
CEX_OMNIBUS_DEFAULT_NOT_REAL_WHALE=true
MARKET_MAKER_WALLET_DEFAULT_NOT_REAL_WHALE=true
HOT_COLD_WALLET_DEFAULT_NOT_REAL_WHALE=true
WHALE_ECONOMIC_IMPACT_REQUIRED=true
SINGLE_SOURCE_ALARM_FORBIDDEN=true
CROSS_CHECK_REQUIRED=true
TRADE_AUTHORITY=false
RUNTIME_AUTHORITY=false
WALLET_AUTHORITY=false
API_RPC_ALLOWED=false
LIVE_FEED_ALLOWED=false
OUTBOUND_PACKET_ALLOWED=false

## FAKE WHALE CLASSES

- FW1: CEX_OMNIBUS_FALSE_WHALE | Exchange omnibus/custody wallet misread as individual whale. | STATUS=NOT_REAL_WHALE
- FW2: MM_OPERATIONAL_WALLET | Market maker operational wallet or inventory rotation. | STATUS=NOT_REAL_WHALE
- FW3: HOT_COLD_INTERNAL_TRANSFER | Internal hot/cold custody movement with no market intent proof. | STATUS=NOT_REAL_WHALE
- FW4: WASH_SYBIL_CLUSTER | Sybil/wash loop designed to fake size or activity. | STATUS=FAKE_WHALE_SUSPECT
- FW5: LOW_LIQUIDITY_GHOST_MOVE | Large nominal transfer without meaningful liquidity depth. | STATUS=FAKE_WHALE_SUSPECT
- FW6: FLASH_LOAN_MASKED_WHALE | Temporary liquidity or flash-loan style balance inflation. | STATUS=FAKE_WHALE_SUSPECT
- FW7: BRIDGE_OR_ROUTER_PASS_THROUGH | Router, bridge, relayer, aggregator or pass-through address. | STATUS=NOT_REAL_WHALE
- FW8: AIRDROP_FARM_OR_DUST_CLUSTER | Farmed, dusted, or split accounts designed to pollute holder reading. | STATUS=FAKE_WHALE_SUSPECT


## REAL WHALE CANDIDATE REQUIREMENTS

- RW1: non_cex_non_router_identity_or_cluster_context | MANDATORY=true
- RW2: economic_impact_context_available_Vt_over_Ld | MANDATORY=true
- RW3: low_liquidity_ghost_move_false | MANDATORY=true
- RW4: wash_sybil_score_below_block_threshold | MANDATORY=true
- RW5: cross_check_path_at_least_one_confirmed | MANDATORY=true
- RW6: evidence_level_at_least_L3_readable_state | MANDATORY=true
- RW7: confidence_level_medium_or_above_but_no_trade_authority | MANDATORY=true
- RW8: no_private_key_wallet_or_signature_data_required | MANDATORY=true


## SEPARATION DECISION MATRIX

- DM1: INPUT=cex_omnibus_or_custody_match | DECISION=NOT_REAL_WHALE | REAL_WHALE_CANDIDATE_ALLOWED=false
- DM2: INPUT=market_maker_or_operational_wallet_match | DECISION=NOT_REAL_WHALE | REAL_WHALE_CANDIDATE_ALLOWED=false
- DM3: INPUT=hot_cold_internal_transfer_match | DECISION=NOT_REAL_WHALE | REAL_WHALE_CANDIDATE_ALLOWED=false
- DM4: INPUT=wash_sybil_or_loop_pattern | DECISION=FAKE_WHALE_SUSPECT | REAL_WHALE_CANDIDATE_ALLOWED=false
- DM5: INPUT=low_liquidity_ghost_move | DECISION=FAKE_WHALE_SUSPECT | REAL_WHALE_CANDIDATE_ALLOWED=false
- DM6: INPUT=flash_loan_masking_or_temporary_balance | DECISION=FAKE_WHALE_SUSPECT | REAL_WHALE_CANDIDATE_ALLOWED=false
- DM7: INPUT=unknown_large_holder_without_economic_context | DECISION=REVIEW_REQUIRED | REAL_WHALE_CANDIDATE_ALLOWED=false
- DM8: INPUT=economic_context_plus_cross_check_plus_identity_context | DECISION=REAL_WHALE_CANDIDATE | REAL_WHALE_CANDIDATE_ALLOWED=true


## SCORING CONTRACT

SCORE_RANGE=0-100
FAKE_WHALE_SCORE_BLOCKS_AT_OR_ABOVE=60
REAL_WHALE_CANDIDATE_MIN_SCORE=70
ECONOMIC_IMPACT_REQUIRED=true

### SCORE COMPONENTS

- SC1: entity_identity_context | MAX_POINTS=15
- SC2: economic_impact_context_Vt_over_Ld | MAX_POINTS=20
- SC3: cross_check_confirmation | MAX_POINTS=20
- SC4: behavior_consistency | MAX_POINTS=15
- SC5: evidence_level | MAX_POINTS=15
- SC6: anti_sybil_cleanliness | MAX_POINTS=15


### NEGATIVE OVERRIDES

- cex_omnibus_match
- router_bridge_pass_through
- low_liquidity_ghost_move
- flash_loan_masking
- wash_sybil_cluster
- private_key_or_wallet_secret_required
- single_source_only


## CROSS-CHECK ENFORCEMENT

- X1: WHALE_TO_ONCHAIN | REQUIRED=true | PURPOSE=entity, holder, liquidity, deployer relation confirmation
- X2: WHALE_TO_RISK | REQUIRED=false | PURPOSE=risk escalation, block, quarantine or fail-closed hint
- X3: WHALE_TO_EVIDENCE | REQUIRED=true | PURPOSE=prosecutor-grade trace and evidence level
- X4: WHALE_TO_TECHNICAL | REQUIRED=false | PURPOSE=price/volume context; no standalone confirmation
- X5: WHALE_TO_NEWS | REQUIRED=false | PURPOSE=event/narrative context; no standalone confirmation
- X6: WHALE_TO_UNKNOWN_ANOMALY | REQUIRED=false | PURPOSE=unknown behavior profile escalation


## FAIL-CLOSED RULES

1. Single-source whale claim cannot become central alert.
2. CEX, router, bridge, relayer, hot/cold internal transfer, or MM operational wallet defaults to NOT_REAL_WHALE until disproven.
3. LOW_LIQUIDITY_GHOST_MOVE blocks REAL_WHALE_CANDIDATE.
4. Unknown liquidity depth blocks REAL_WHALE_CANDIDATE.
5. Flash-loan or temporary balance masking becomes FAKE_WHALE_SUSPECT.
6. Any wallet/private-key/signature requirement becomes FAIL_CLOSED.
7. Any API/RPC requirement becomes STOP_NOAPI.
8. Any trade or runtime pressure becomes FAIL_CLOSED.


## HARD BOUNDARIES

1. FAKE_WHALE_DEFAULT=true
2. REAL_WHALE_REQUIRES_POSITIVE_EVIDENCE=true
3. CEX_OMNIBUS_DEFAULT_NOT_REAL_WHALE=true
4. MM_OPERATIONAL_WALLET_DEFAULT_NOT_REAL_WHALE=true
5. HOT_COLD_WALLET_DEFAULT_NOT_REAL_WHALE=true
6. WHALE_ECONOMIC_IMPACT_REQUIRED=true
7. LOW_LIQUIDITY_GHOST_MOVE_BLOCKS_REAL_WHALE_CANDIDATE=true
8. SINGLE_SOURCE_ALARM_FORBIDDEN=true
9. CROSS_CHECK_REQUIRED=true
10. TRADE_AUTHORITY=false
11. RUNTIME_AUTHORITY=false
12. WALLET_AUTHORITY=false
13. API_RPC=false
14. LIVE_FEED=false
15. OUTBOUND_PACKET=false


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

## NEXT SUBSTEP

V2_44_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI

## PUSH POLICY

SUBTASK_PUSH=false
FINAL_CLOSE_PUSH=true
GITHUB_PUSH_ONLY_AT_VXX_FINAL_CLOSE=true
