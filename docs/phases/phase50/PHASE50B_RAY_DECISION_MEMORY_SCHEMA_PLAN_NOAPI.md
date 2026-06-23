# PHASE50B_RAY_DECISION_MEMORY_SCHEMA_PLAN_NOAPI

## STATUS
PLAN_ONLY

## CORE RULE

NO_FIXED_SCORES=true
NO_FIXED_WEIGHTS=true
NO_FIXED_TIME_BUCKETS=true

MARKET_DETERMINES_IMPORTANCE=true
OUTCOME_DETERMINES_LEARNING=true

## CONSTITUTIONAL_GATE_V1

SPEED_NEVER_DOWN=true
SECURITY_NEVER_DOWN=true
POWER_NEVER_DOWN=true
DENGE_DENGE_DENGE=true

HOT_PATH_READMODEL_ONLY=true
TOKEN_BY_TOKEN_PROCESS=false
RAY_BATCH_REQUIRED=true

## PLANNED TABLES

decision_memory_case_v1

decision_memory_event_v1

decision_memory_outcome_v1

decision_memory_causal_chain_v1

decision_memory_similarity_link_v1

decision_memory_false_negative_v1

decision_memory_correct_rejection_v1

decision_memory_missed_opportunity_v1

decision_memory_morg_case_v1

decision_memory_autopsy_case_v1

## CASE MODEL

Every token becomes a case.

CASE_STATUS:

ACTIVE
WATCH
REJECTED
DEAD
SUCCESS
MISSED
UNKNOWN

## REQUIRED CASE FIELDS

case_id
token_uid
chain
token_address

ray_entry_stage
ray_exit_stage

discard_reason
discard_time

outcome_status

created_at
updated_at

## AUTOPSY FIELDS

death_reason
death_stage
death_evidence_refs
death_causal_chain

## MORG FIELDS

morg_case_id
similar_case_refs
prosecutor_refs

## MISSED OPPORTUNITY FIELDS

move_multiple

x10
x50
x100

why_not_entered
missed_signal_refs

## FALSE NEGATIVE FIELDS

discard_reason

later_outcome

confidence_at_rejection

## CORRECT REJECTION FIELDS

rejection_reason

later_failure_reason

## SIMILARITY LAYER

similar_case_id

similarity_type

threat_pattern
opportunity_pattern
lifecycle_pattern

## HOT PATH RULE

No joins.

No autopsy.

No morg analysis.

No similarity graph.

No memory reasoning.

Memory layer runs async only.

## AUTHORITY

MEMORY_AUTHORITY=0

AI_AUTHORITY=0

TRADE_AUTHORITY=0

RISK_ENGINE_FINAL_GATE=true

## HARD LOCKS

DB_WRITE=false
SCHEMA_APPLY=false
TEMPDB=false
API_CALL=false
RUNTIME_CHANGE=false
PANEL_WRITE=false
SERVICE_RESTART=false
GITHUB_PUSH=false

## NEXT_SAFE_STEP

PHASE50C_RAY_DECISION_MEMORY_TEMPDB_DRYRUN_NOAPI

## FINAL_GATE

PASS_PHASE50B_RAY_DECISION_MEMORY_SCHEMA_PLAN_NOAPI
