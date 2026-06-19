# PASS11H Alpha Watcher Runtime Position Decision

PHASE=PASS11H_RUNTIME_POSITION_DECISION_DOC_REAL_APPLY
MODE=DOCUMENTATION_ONLY
SOURCE_OF_TRUTH=PROJECT_MASTER_STATE.md

## Final Decision

ALPHA_WATCHER_POSITION=CANONICAL_V1_SIDECAR_ENRICHMENT_LAYER

PIPELINE_POSITION=Hunter_and_Priority_sidecar_before_Prosecutor

AUTHORITY=OBSERVATION_AND_ENRICHMENT_ONLY

TRADE_AUTHORITY=0

RISK_ENGINE_FINAL_AUTHORITY=true

HOT_PATH_NEVER_WAITS=true

## Approved Flow

Hunter
  ->
Priority
  ->
Alpha Watcher (Sidecar Enrichment)
  ->
Prosecutor
  ->
Risk Engine
  ->
Phase41 Context Feed

## Responsibilities

### Alpha Watcher

- Early alpha detection
- Adversarial intelligence enrichment
- Unknown anomaly observation
- Context generation
- Priority enrichment

### Not Allowed

- Trade decisions
- Wallet actions
- API authority escalation
- Risk override
- Hot path blocking
- Market manipulation

## Rejected Positions

### Position A

Hunter -> Alpha Watcher -> Priority -> Prosecutor -> Risk

REJECTED=true

REASON=Could block HOT path

### Position C

UnknownAnomaly-only sublayer

REJECTED=true

REASON=Too narrow for Alpha Watcher mission

## Safety

NO_RUNTIME_IMPLEMENTATION=true
NO_DB_WRITE=true
NO_API_CALL=true
NO_PANEL_WRITE=true
NO_SERVICE_TIMER_CHANGE=true
NO_WALLET_PAPER_LIVE=true

## Outcome

PASS11H_RUNTIME_POSITION_ACCEPTED=true
READY_FOR_RUNTIME_CONTRACT_PLANNING=true

