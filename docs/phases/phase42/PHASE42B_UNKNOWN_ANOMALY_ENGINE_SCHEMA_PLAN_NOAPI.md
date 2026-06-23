# PHASE42B_UNKNOWN_ANOMALY_ENGINE_SCHEMA_PLAN_NOAPI

## STATUS
PLAN_ONLY

## HARD LOCKS
V1_SCOPE=true
NEW_REPO=false
NEW_DB_LOGIC=false
MODE=PLAN_ONLY
APPLY=false
DB_WRITE=false
SCHEMA_APPLY=false
TEMPDB=false
RUNTIME_CHANGE=false
API_CALL=false
PANEL_WRITE=false
SERVICE_RESTART=false
GIT_PUSH=false

## PURPOSE
This phase plans the future schema/event/readmodel structure for the V1 Unknown Anomaly Engine.

This phase does not create tables.

This phase does not run tempdb dry-run.

This phase does not bind runtime.

## CORE DOCTRINE
Known attack library is not the target.

The target is abnormal token lifecycle behavior.

Core question:

"Why does this token behavior not look like normal token life?"

## FUTURE SCHEMA PLAN

### 1. unknown_anomaly_events_v1
Purpose:
Record detected abnormal lifecycle signals.

Planned fields:
- anomaly_event_id
- token_uid
- chain
- token_address
- anomaly_family
- anomaly_dimension
- anomaly_score
- anomaly_reason
- evidence_refs
- source_engine
- observed_at_utc
- created_at_utc

### 2. unknown_anomaly_baselines_v1
Purpose:
Store expected normal lifecycle baselines.

Planned fields:
- baseline_id
- baseline_type
- chain
- segment
- metric_name
- expected_min
- expected_max
- expected_pattern
- confidence
- created_at_utc

### 3. unknown_anomaly_scorecards_v1
Purpose:
Aggregate multiple anomaly events into token-level anomaly score.

Planned fields:
- scorecard_id
- token_uid
- chain
- token_address
- total_anomaly_score
- lifecycle_deviation_score
- holder_deviation_score
- liquidity_deviation_score
- trading_deviation_score
- contract_deviation_score
- news_whale_mismatch_score
- evidence_consistency_score
- final_anomaly_label
- created_at_utc

### 4. unknown_anomaly_readmodel_v1
Purpose:
Future readmodel for panel/risk/prosecutor consumers.

Planned fields:
- token_uid
- chain
- token_address
- latest_total_anomaly_score
- latest_final_anomaly_label
- top_anomaly_reason
- strongest_evidence_refs
- recommended_route
- updated_at_utc

## FUTURE ENGINE RELATIONS
Planned future consumers/producers:

Producers:
- Data Acquisition Engine
- Risk Engine
- Whale Intelligence
- News Intelligence
- Technical/Tactical Engine
- Evidence Engine

Consumers:
- Risk and Decision Engine
- Prosecutor Engine
- Intelligence Fusion Engine
- Runtime Truth Verifier
- Opportunity Memory Engine
- Panel readmodel layer

## NON-GOALS
- No table creation
- No DB write
- No migration
- No tempdb dry-run
- No runtime producer
- No runtime consumer
- No panel change
- No API call
- No canonical update
- No git push

## NEXT PHASE
PHASE42C_UNKNOWN_ANOMALY_ENGINE_TEMPDB_DRYRUN_NOAPI

## FINAL GATE
PASS_PHASE42B_UNKNOWN_ANOMALY_ENGINE_SCHEMA_PLAN_NOAPI
