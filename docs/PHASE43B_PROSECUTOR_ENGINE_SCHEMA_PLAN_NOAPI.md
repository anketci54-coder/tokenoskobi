# PHASE43B_PROSECUTOR_ENGINE_SCHEMA_PLAN_NOAPI

## STATUS
PLAN_ONLY

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

## PURPOSE
Plan the Prosecutor Engine future schema.

This phase does not create tables.
This phase does not run TempDB.
This phase does not bind runtime.

## CORE QUESTION
Why is this token guilty, suspicious, or clean?

## FUTURE SCHEMA PLAN

### prosecutor_case_file_v1
Purpose:
One case file per token investigation.

Planned fields:
- case_id
- token_uid
- chain
- token_address
- case_status
- opened_reason
- opened_by_engine
- opened_at_utc
- updated_at_utc

### prosecutor_evidence_matrix_v1
Purpose:
Evidence weighing table.

Planned fields:
- evidence_row_id
- case_id
- token_uid
- evidence_source
- evidence_type
- evidence_strength
- evidence_direction
- evidence_reason
- evidence_ref
- confidence
- observed_at_utc

### prosecutor_verdict_readmodel_v1
Purpose:
Final prosecutor verdict readmodel for consumers.

Planned fields:
- token_uid
- case_id
- verdict_class
- verdict_score
- strongest_accusation
- strongest_defense
- evidence_count
- independent_source_count
- confidence
- recommended_route
- updated_at_utc

## VERDICT CLASSES
- CLEAN
- WATCH
- SUSPICIOUS
- HIGH_RISK
- GUILTY
- INSUFFICIENT_EVIDENCE

## NON-GOALS
- No DB write
- No schema apply
- No TempDB dry-run
- No runtime change
- No panel change
- No API call
- No service restart
- No git push

## NEXT_SAFE_STEP
PHASE43C_PROSECUTOR_ENGINE_TEMPDB_DRYRUN_NOAPI

## FINAL_GATE
PASS_PHASE43B_PROSECUTOR_ENGINE_SCHEMA_PLAN_NOAPI
