# V2_44_WHALE_WALLET_TRACKING_ARCHITECTURE_PLAN_NOAPI

STAMP_UTC=2026-06-27T10:13:50Z
MODE=LOCAL_ONLY_NOAPI_NO_PUSH

## RESULT

FINAL_GATE=PASS_V2_44_WHALE_WALLET_TRACKING_ARCHITECTURE_PLAN_NOAPI
DECISION=V2_44_WHALE_ARCHITECTURE_PLAN_PASS_READY_FOR_SOURCE_TAXONOMY
NEXT=V2_44A_WHALE_SOURCE_TAXONOMY_AND_ENTITY_BOUNDARY_LOCAL_NOAPI
GITHUB_PUSH=false

## PURPOSE

V2_44 plans the whale wallet tracking architecture under strict NOAPI laboratory constraints.

This phase creates architecture, source taxonomy outline, entity classes, behavior signals, cross-check paths, confidence levels, and hard boundaries.

No real wallet tracking, API/RPC, live feed, DB write, runtime binding, trade authority, wallet/private-key access, AI tool execution, or outbound packet is allowed.

## HUB-AND-SPOKE HARD GATE

HARD_GATE_1=Hub-and-Spoke Cross-Check Pipeline
HUB_AND_SPOKE_REQUIRED=true
SINGLE_SOURCE_ALARM_FORBIDDEN=true

A whale signal cannot directly alert the central core from a single source. It must pass at least one cross-check path through onchain, risk, technical, news, evidence, or unknown anomaly layer.

## WHALE DATA CONTRACT

CONTRACT_NAME=whale_wallet_tracking_data_contract_v1
SIGNAL_NATURE=evidence_and_classification_only
AUTHORITY=NO_TRADE_NO_RUNTIME_NO_WALLET_AUTHORITY

### REQUIRED FIELDS

- chain
- entity_uid
- wallet_or_cluster_ref
- entity_class
- source_class
- direction
- amount_band
- confidence
- evidence_level
- cross_check_required
- risk_interaction_hint
- timestamp_hint

### FORBIDDEN FIELDS

- private_key
- seed_phrase
- wallet_signature
- raw_secret
- live_order_instruction
- trade_authorization
- runtime_command
- api_endpoint_secret

## WHALE ENTITY CLASSES

- WC1: CEX_OMNIBUS | Exchange omnibus or custody wallet; not individual whale by default. | TRADE_IMPACT_ALLOWED=false
- WC2: DEX_LP_PROVIDER | Liquidity provider or pool-adjacent wallet. | TRADE_IMPACT_ALLOWED=false
- WC3: DEPLOYER_OWNER | Token deployer, owner, or privileged control wallet. | TRADE_IMPACT_ALLOWED=false
- WC4: INSIDER_CLUSTER | Coordinated insider-style wallet group. | TRADE_IMPACT_ALLOWED=false
- WC5: SNIPER_BOT | Early-entry or automated sniping wallet. | TRADE_IMPACT_ALLOWED=false
- WC6: SMART_MONEY_CANDIDATE | Candidate wallet with repeated profitable behavior, not proven authority. | TRADE_IMPACT_ALLOWED=false
- WC7: WASH_SYBIL_CLUSTER | Likely fake whale, wash cluster, sybil or liquidity mirage. | TRADE_IMPACT_ALLOWED=false
- WC8: UNKNOWN_LARGE_HOLDER | Large holder with insufficient identity confidence. | TRADE_IMPACT_ALLOWED=false


## SOURCE TAXONOMY

- WS1: STATIC_FIXTURE | ALLOWED_NOW=true | API_REQUIRED=false
- WS2: LOCAL_DB_READONLY | ALLOWED_NOW=true | API_REQUIRED=false
- WS3: LOCAL_JSONL_READONLY | ALLOWED_NOW=true | API_REQUIRED=false
- WS4: FUTURE_INDEXED_ONCHAIN_READMODEL | ALLOWED_NOW=false | API_REQUIRED=false
- WS5: FUTURE_EXPLORER_API | ALLOWED_NOW=false | API_REQUIRED=true
- WS6: FUTURE_RPC_NODE | ALLOWED_NOW=false | API_REQUIRED=true
- WS7: FUTURE_THIRD_PARTY_LABEL_PROVIDER | ALLOWED_NOW=false | API_REQUIRED=true
- WS8: FUTURE_CEX_LABEL_MAP | ALLOWED_NOW=false | API_REQUIRED=false


## BEHAVIOR SIGNALS

- WB1: ACCUMULATION | Repeated buys/inflows with non-trivial size band. | CROSS_CHECK_REQUIRED=true
- WB2: DISTRIBUTION | Repeated sells/outflows or staged exits. | CROSS_CHECK_REQUIRED=true
- WB3: LIQUIDITY_MIRAGE | Large wallet activity that simulates demand without durable liquidity. | CROSS_CHECK_REQUIRED=true
- WB4: INSIDER_ROTATION | Coordinated movement among privileged or early wallets. | CROSS_CHECK_REQUIRED=true
- WB5: EXIT_PREPARATION | Pattern suggests possible dump, LP withdrawal, or risk escalation. | CROSS_CHECK_REQUIRED=true
- WB6: CEX_FLOW_HINT | Inflow/outflow hint near CEX-related cluster; no direct conclusion. | CROSS_CHECK_REQUIRED=true
- WB7: WASH_VOLUME_SUSPECT | Self-referential or sybil-like circulation. | CROSS_CHECK_REQUIRED=true
- WB8: UNKNOWN_ANOMALY | Whale behavior does not match normal class profile. | CROSS_CHECK_REQUIRED=true


## CROSS-CHECK PATHS

- CC1: WHALE_TO_ONCHAIN | REQUIRED_FOR=entity, holder, liquidity, deployer relation confirmation
- CC2: WHALE_TO_RISK | REQUIRED_FOR=risk escalation, block, quarantine, fail-closed hint
- CC3: WHALE_TO_TECHNICAL | REQUIRED_FOR=price/volume regime confirmation
- CC4: WHALE_TO_NEWS | REQUIRED_FOR=narrative, announcement, exploit or event context
- CC5: WHALE_TO_EVIDENCE | REQUIRED_FOR=prosecutor-grade trace and evidence level
- CC6: WHALE_TO_UNKNOWN_ANOMALY | REQUIRED_FOR=unknown behavior profile escalation


## CONFIDENCE MODEL

- LOW: RANGE=0.00-0.39 | observe only; no escalation
- MEDIUM: RANGE=0.40-0.69 | review candidate; cross-check mandatory
- HIGH: RANGE=0.70-0.89 | risk/evidence review; still no trade authority
- CRITICAL: RANGE=0.90-1.00 | fail-closed or review escalation; still no trade authority


## HARD BOUNDARIES

1. Whale engine cannot create a central alarm from a single source.
2. Whale engine cannot call API/RPC in V2_44.
3. Whale engine cannot track live wallets in V2_44.
4. Whale engine cannot write DB in V2_44.
5. Whale engine cannot bind runtime in V2_44.
6. Whale engine cannot authorize trade.
7. Whale engine cannot touch wallet/private-key material.
8. Whale engine cannot send outbound packet.
9. Whale signal must remain evidence/classification only.
10. Any whale signal requiring live data becomes STOP_NOAPI.


## REQUIRED SUBSTEPS

V2_44A_WHALE_SOURCE_TAXONOMY_AND_ENTITY_BOUNDARY_LOCAL_NOAPI
V2_44B_FAKE_WHALE_REAL_WHALE_SEPARATION_CONTRACT_LOCAL_NOAPI
V2_44_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI

## LOCKS

REAL_WALLET_TRACKING=false
API_RPC_ALLOWED=false
LIVE_FEED_ALLOWED=false
DB_WRITE_ALLOWED=false
PANEL_WRITE_ALLOWED=false
RUNTIME_APPLY_ALLOWED=false
SERVICE_RESTART_ALLOWED=false
TIMER_CHANGE_ALLOWED=false
LIVE_DECISION_ALLOWED=false
LIVE_TRADE_ALLOWED=false
WALLET_ACCESS_ALLOWED=false
PRIVATE_KEY_ACCESS_ALLOWED=false
AI_TOOL_EXECUTION_ALLOWED=false
OUTBOUND_PACKET_ALLOWED=false

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
