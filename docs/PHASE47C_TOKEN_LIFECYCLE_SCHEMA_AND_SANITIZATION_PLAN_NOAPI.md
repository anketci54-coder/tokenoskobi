# PHASE47C_TOKEN_LIFECYCLE_SCHEMA_AND_SANITIZATION_PLAN_NOAPI

## STATUS
PLAN_ONLY

## CONSTITUTIONAL_GATE_V1
SPEED_NEVER_DOWN=true
SECURITY_NEVER_DOWN=true
POWER_NEVER_DOWN=true
DENGE_DENGE_DENGE=true
hot_path_waits=false
lifecycle_analysis_blocks_hot_path=false
risk_gate_weakens=false
learning_blocks_execution=false

## CORE RULES
MINIMUM_VIABLE_TAXONOMY=true
EXTENSIBLE_EVENT_SCHEMA=true
NO_EARLY_OVERMODELING=true
NO_FIXED_SCORE_WEIGHTS=true
NO_ASSUMED_TIME_BUCKETS=true
MARKET_DETERMINES_WEIGHTS=true
MARKET_DETERMINES_TIME_WINDOWS=true

## HARD LOCKS
V1_SCOPE=true
MODE=PLAN_ONLY
DB_WRITE=false
SCHEMA_APPLY=false
TEMPDB=false
RUNTIME_CHANGE=false
API_CALL=false
PANEL_WRITE=false
SERVICE_RESTART=false
GIT_PUSH=false
TRADE_AUTHORITY=false
AI_AUTHORITY=false
WALLET_AUTHORITY=false
AUTO_APPLY=false

## PURPOSE
Plan minimum viable token lifecycle schema with sanitization, quarantine, event linkage, discovery lag tracking, TTL/archive policy, and hot-path-safe fast readmodel.

No table is created.
No TempDB is used.
No runtime is changed.

## SCHEMA PRINCIPLES
JSON metadata is for flexible cold evidence only.
Frequently queried fields must be real columns.
HOT PATH never reads JSON metadata.
HOT PATH reads only lifecycle_fast_readmodel_v1.

## MINIMUM VIABLE EVENT TYPES
- token_birth_event
- liquidity_change_event
- holder_distribution_event
- sellability_failure_event
- rug_pull_event
- honeypot_event
- sandwich_attack_event
- mev_pressure_event

## FUTURE TABLE PLAN

### lifecycle_event_store_v1
Purpose:
Clean normalized lifecycle events.

Key planned fields:
- lifecycle_event_id
- token_uid
- chain
- token_address
- event_group
- event_type
- event_subtype
- lifecycle_stage
- chain_block_number
- chain_event_time
- system_detected_at
- discovery_lag_ms
- linkage_id
- parent_event_id
- correlation_group_id
- evidence_ref_id
- liquidity_delta
- holder_delta
- price_delta_pct
- tax_rate
- slippage_percentage
- sellability_state
- source_quality
- metadata_json
- created_at_utc

### lifecycle_quarantine_v1
Purpose:
Dirty, ambiguous, malformed, late, or suspicious raw lifecycle inputs.

Rules:
- dirty data never enters memory
- dirty data never enters lifecycle_fast_readmodel_v1
- quarantine requires reason
- quarantine can later be promoted only after validation

Key planned fields:
- quarantine_id
- raw_event_id
- token_uid
- reason
- severity
- source
- raw_payload_ref
- validation_status
- promoted_event_id
- created_at_utc

### lifecycle_event_linkage_v1
Purpose:
Support n-to-n evidence and event correlation.

Rules:
- one event may have many related events
- correlation groups may be split or merged by Prosecutor
- linkage does not create trade authority

Key planned fields:
- linkage_row_id
- linkage_id
- source_event_id
- target_event_id
- relation_type
- correlation_group_id
- confidence
- created_by
- created_at_utc

### lifecycle_evidence_archive_policy_v1
Purpose:
Plan TTL/archive behavior for heavy evidence references.

Rules:
- TTL policy required
- raw evidence may be archived
- compact evidence fingerprints remain
- Truth Verifier must retain enough evidence for audit

Key planned fields:
- policy_id
- evidence_type
- hot_retention_days
- warm_retention_days
- cold_archive_required
- compact_fingerprint_required
- created_at_utc

### lifecycle_fast_readmodel_v1
Purpose:
Hot-path-safe precomputed lifecycle state.

Hot path query rule:
1 token = 1 row = 1 indexed query

Key planned fields:
- token_uid
- lifecycle_stage
- lifecycle_health
- lifecycle_age_seconds
- death_risk_flags
- scam_pattern_hits
- mev_pressure
- sandwich_pressure
- rug_risk_context
- honeypot_context
- liquidity_life_state
- holder_life_state
- sellability_state
- market_discovered_time_bucket
- last_event_at_utc
- last_updated_ms

## SANITIZATION PIPELINE
raw_event
↓
sanitize
↓
normalize
↓
validate
↓
if clean: lifecycle_event_store_v1
if dirty_or_ambiguous: lifecycle_quarantine_v1
↓
only clean events update lifecycle_fast_readmodel_v1

## QUARANTINE LOCKS
QUARANTINE_FIRST=true
DIRTY_DATA_NEVER_ENTERS_MEMORY=true
DIRTY_DATA_NEVER_ENTERS_FAST_READMODEL=true
PROSECUTOR_CAN_SPLIT_CORRELATION_GROUP=true
PROSECUTOR_CAN_MERGE_CORRELATION_GROUP=true
TTL_POLICY_REQUIRED=true

## JSON INDEX POLICY
JSON_METADATA_INDEX_POLICY_REQUIRED=true

Policy:
- hot/filter fields must be columns
- metadata_json is cold-path context
- no hot path JSON scan
- no large raw payload in hot table

## NON-GOALS
- No DB write
- No schema apply
- No TempDB dry-run
- No runtime change
- No API call
- No panel write
- No service restart
- No git push
- No score weights
- No fixed time buckets
- No trade authority

## NEXT_SAFE_STEP
PHASE47D_TOKEN_LIFECYCLE_TEMPDB_DRYRUN_NOAPI

## FINAL_GATE
PASS_PHASE47C_TOKEN_LIFECYCLE_SCHEMA_AND_SANITIZATION_PLAN_NOAPI
