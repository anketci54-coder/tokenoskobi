# PHASE48B_THREAT_MEMORY_SCHEMA_PLAN_NOAPI

## STATUS
PLAN_ONLY

## CORE RULES
NO_FIXED_SCORE_WEIGHTS=true
NO_FIXED_TIME_WINDOWS=true
MARKET_DETERMINES_IMPORTANCE=true
OUTCOME_FIRST=true
MEMORY_BEFORE_SCORING=true

## CONSTITUTIONAL_GATE_V1
SPEED_NEVER_DOWN=true
SECURITY_NEVER_DOWN=true
POWER_NEVER_DOWN=true
DENGE_DENGE_DENGE=true

hot_path_waits=false
memory_lookup_blocks_hot_path=false
risk_gate_weakens=false

## THREAT MEMORY TABLES

### threat_memory_cases_v1

Stores completed historical cases.

Fields:

case_id
token_uid
case_class

RUG_PULL
HONEYPOT
MEV_ATTACK
SANDWICH_ATTACK
LIQUIDITY_DRAIN
FAKE_VOLUME
WASH_TRADING
FALSE_POSITIVE
FALSE_NEGATIVE
MISSED_OPPORTUNITY
UNKNOWN

outcome_class
first_seen_at_utc
resolved_at_utc
resolution_confidence
correlation_group_id

### outcome_memory_v1

Stores final outcomes.

Fields:

outcome_id
token_uid
outcome_type
outcome_value
evidence_ref
created_at_utc

### threat_pattern_memory_v1

Stores reusable patterns.

pattern_id
pattern_class
pattern_signature
pattern_version
occurrence_count
success_count
failure_count
last_seen_at_utc

### lifecycle_outcome_linkage_v1

Links PHASE47 lifecycle events
to final outcomes.

linkage_id
lifecycle_event_id
outcome_id
relationship_type

### threat_memory_fast_readmodel_v1

Hot path only.

Fields:

token_uid
known_pattern_count
similar_case_count
last_known_outcome
memory_risk_context
memory_updated_at_utc

## SANITIZATION

All memory records must pass:

source_validation
schema_validation
duplicate_validation
outcome_validation

Invalid records:

QUARANTINE_REQUIRED=true

## HOT PATH RULE

Never scan historical memory directly.

Read only:

threat_memory_fast_readmodel_v1

## NON GOALS

No DB write
No schema apply
No tempdb
No runtime
No api
No panel
No scoring engine

## NEXT SAFE STEP

PHASE48C_THREAT_MEMORY_TEMPDB_DRYRUN_NOAPI

## FINAL_GATE

PASS_PHASE48B_THREAT_MEMORY_SCHEMA_PLAN_NOAPI
