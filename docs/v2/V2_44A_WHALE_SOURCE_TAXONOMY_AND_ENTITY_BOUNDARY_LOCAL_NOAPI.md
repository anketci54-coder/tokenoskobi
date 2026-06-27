# V2_44A_WHALE_SOURCE_TAXONOMY_AND_ENTITY_BOUNDARY_LOCAL_NOAPI

STAMP_UTC=2026-06-27T10:22:49Z
MODE=LOCAL_ONLY_NOAPI_NO_PUSH

## RESULT

FINAL_GATE=PASS_V2_44A_WHALE_SOURCE_TAXONOMY_AND_ENTITY_BOUNDARY_LOCAL_NOAPI
DECISION=V2_44A_WHALE_SOURCE_ENTITY_ECONOMIC_BOUNDARY_PASS_READY_FOR_FAKE_REAL_SEPARATION
NEXT=V2_44B_FAKE_WHALE_REAL_WHALE_SEPARATION_CONTRACT_LOCAL_NOAPI
GITHUB_PUSH=false

## PURPOSE

V2_44A locks whale source taxonomy, entity boundaries, and economic impact filtering.

This step adds the Red Team GZ2 hard boundary:

WHALE_ECONOMIC_IMPACT_REQUIRED=true

A whale transfer cannot become a REAL_WHALE_CANDIDATE unless transfer value is evaluated against liquidity or route depth.

## ECONOMIC IMPACT BOUNDARY

WHALE_ECONOMIC_IMPACT_REQUIRED=true
RATIO=V_t / L_d
V_t=whale_transfer_value
L_d=liquidity_pool_or_route_depth
LOW_LIQUIDITY_GHOST_MOVE=true
TRADE_AUTHORITY=false
API_RPC_ALLOWED=false
LIVE_FEED_ALLOWED=false

RULE=A whale transfer cannot become REAL_WHALE_CANDIDATE unless transfer value is evaluated against liquidity depth or route depth.
FAIL_CLOSED_RULE=If liquidity depth is unknown, shallow, stale, or unavailable, classify as REVIEW_REQUIRED or LOW_LIQUIDITY_GHOST_MOVE; never escalate to trade authority.

## ECONOMIC IMPACT CLASSES

- EI1: NO_LIQUIDITY_CONTEXT | CONDITION=L_d missing or unknown | STATUS=REVIEW_REQUIRED | REAL_WHALE_CANDIDATE_ALLOWED=false
- EI2: LOW_LIQUIDITY_GHOST_MOVE | CONDITION=large V_t with shallow L_d | STATUS=FAKE_WHALE_SUSPECT | REAL_WHALE_CANDIDATE_ALLOWED=false
- EI3: ROUTE_DEPTH_MISMATCH | CONDITION=transfer size exceeds realistic route depth | STATUS=REVIEW_REQUIRED | REAL_WHALE_CANDIDATE_ALLOWED=false
- EI4: ECONOMIC_IMPACT_CANDIDATE | CONDITION=V_t and L_d both plausible after cross-check | STATUS=REVIEW_REQUIRED | REAL_WHALE_CANDIDATE_ALLOWED=false
- EI5: CROSS_CHECKED_ECONOMIC_WHALE | CONDITION=economic impact supported by liquidity and external evidence path | STATUS=REAL_WHALE_CANDIDATE | REAL_WHALE_CANDIDATE_ALLOWED=true


## FUTURE GREY-ZONE REGISTRY

- GZ1: Time-Drift & Sliding Window / TTL | ACTIVE_NOW=false | TARGET_PHASE=FUTURE_V2_45_TO_V2_48 | RISK=cross-check race condition, buffer bloat, TTL mismatch
- GZ2: Liquidity Depth / Economic Impact Ratio | ACTIVE_NOW=true | TARGET_PHASE=V2_44A | RISK=ghost whale, low-liquidity mirage, wash masking
- GZ3: AI Output Panic / Social Engineering Guardrail | ACTIVE_NOW=false | TARGET_PHASE=V2_52_TO_V2_55 | RISK=chatbot panic report, operator manipulation, self-DoS
- GZ4: Pattern Spoofing / Order Cancellation + Volume Divergence | ACTIVE_NOW=false | TARGET_PHASE=V2_46_TO_V2_48 | RISK=fakeout, orderbook spoofing, technical-pattern trap


## SOURCE TAXONOMY

- WS1: STATIC_FIXTURE | ALLOWED_NOW=true | API_REQUIRED=false | TRUST=TEST_ONLY | ENTITY_RISK=LOW
- WS2: LOCAL_DB_READONLY | ALLOWED_NOW=true | API_REQUIRED=false | TRUST=LOCAL_READONLY | ENTITY_RISK=MEDIUM
- WS3: LOCAL_JSONL_READONLY | ALLOWED_NOW=true | API_REQUIRED=false | TRUST=LOCAL_READONLY | ENTITY_RISK=MEDIUM
- WS4: FUTURE_INDEXED_ONCHAIN_READMODEL | ALLOWED_NOW=false | API_REQUIRED=false | TRUST=FUTURE_READMODEL | ENTITY_RISK=MEDIUM
- WS5: FUTURE_EXPLORER_API | ALLOWED_NOW=false | API_REQUIRED=true | TRUST=FUTURE_EXTERNAL | ENTITY_RISK=HIGH
- WS6: FUTURE_RPC_NODE | ALLOWED_NOW=false | API_REQUIRED=true | TRUST=FUTURE_EXTERNAL | ENTITY_RISK=HIGH
- WS7: FUTURE_THIRD_PARTY_LABEL_PROVIDER | ALLOWED_NOW=false | API_REQUIRED=true | TRUST=FUTURE_EXTERNAL_LABEL | ENTITY_RISK=HIGH
- WS8: FUTURE_CEX_LABEL_MAP | ALLOWED_NOW=false | API_REQUIRED=false | TRUST=FUTURE_LABEL_MAP | ENTITY_RISK=MEDIUM


## ENTITY BOUNDARIES

- EB1: CEX_OMNIBUS | Never treat exchange omnibus as individual whale without cluster split evidence. | TRADE_AUTHORITY=false
- EB2: DEX_LP_PROVIDER | Liquidity provider movement is pool context, not standalone whale conviction. | TRADE_AUTHORITY=false
- EB3: DEPLOYER_OWNER | Privileged control wallet is risk evidence, not positive whale signal. | TRADE_AUTHORITY=false
- EB4: INSIDER_CLUSTER | Cluster behavior requires evidence chain and cannot be single-wallet inference. | TRADE_AUTHORITY=false
- EB5: SNIPER_BOT | Sniper activity is adversarial behavior class, not smart-money proof. | TRADE_AUTHORITY=false
- EB6: SMART_MONEY_CANDIDATE | Requires outcome memory and repeated behavior; candidate only. | TRADE_AUTHORITY=false
- EB7: WASH_SYBIL_CLUSTER | Likely fake whale, wash routing, sybil fan-out, or liquidity mirage. | TRADE_AUTHORITY=false
- EB8: UNKNOWN_LARGE_HOLDER | Unknown remains unknown until evidence level improves. | TRADE_AUTHORITY=false


## SOURCE ADMISSION RULES

1. Only STATIC_FIXTURE, LOCAL_DB_READONLY, and LOCAL_JSONL_READONLY are allowed in V2_44A.
2. Any future API/RPC source remains forbidden until explicit later approval.
3. External labels cannot create whale truth without evidence level and cross-check.
4. CEX omnibus labels must default to non-individual whale.
5. Unknown wallet stays UNKNOWN_LARGE_HOLDER until evidence improves.
6. Every whale assertion must carry source_class, entity_class, confidence, evidence_level, and economic_impact_class.


## HARD BOUNDARIES

1. REAL_WALLET_TRACKING=false
2. API_RPC=false
3. LIVE_FEED=false
4. DB_WRITE=false
5. RUNTIME_APPLY=false
6. LIVE_TRADE=false
7. WALLET_ACCESS=false
8. PRIVATE_KEY_ACCESS=false
9. OUTBOUND_PACKET=false
10. SINGLE_SOURCE_ALARM_FORBIDDEN=true
11. WHALE_ECONOMIC_IMPACT_REQUIRED=true
12. LOW_LIQUIDITY_GHOST_MOVE_BLOCKS_REAL_WHALE_CANDIDATE=true


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

V2_44B_FAKE_WHALE_REAL_WHALE_SEPARATION_CONTRACT_LOCAL_NOAPI

## PUSH POLICY

SUBTASK_PUSH=false
FINAL_CLOSE_PUSH=true
GITHUB_PUSH_ONLY_AT_VXX_FINAL_CLOSE=true
