# PHASE44C_INTELLIGENCE_FUSION_ENGINE_SCHEMA_PLAN_NOAPI

## STATUS
PLAN_ONLY

## CONSTITUTIONAL_GATE_V1
SPEED_NEVER_DOWN=true
SECURITY_NEVER_DOWN=true
POWER_NEVER_DOWN=true
speed_degrades=false
security_degrades=false
power_degrades=false
hot_path_waits=false
risk_gate_weakens=false
ai_blocks_decision_chain=false
learning_blocks_execution=false

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
Plan the future schema/readmodel structure for Intelligence Fusion Engine.

This phase does not create tables.
This phase does not run TempDB.
This phase does not bind runtime.

## FUTURE SCHEMA PLAN

### fusion_case_file_v1
Purpose:
One fusion case per token decision context.

Planned fields:
- fusion_case_id
- token_uid
- chain
- token_address
- case_status
- opened_reason
- input_source_count
- conflict_present
- opened_at_utc
- updated_at_utc

### fusion_conflict_matrix_v1
Purpose:
Track cross-engine agreement/conflict.

Planned fields:
- conflict_row_id
- fusion_case_id
- token_uid
- source_engine
- source_signal
- source_score
- signal_direction
- conflict_group
- conflict_reason
- confidence
- observed_at_utc

### fusion_consensus_readmodel_v1
Purpose:
Final explainable FINAL_FUSION_SIGNAL readmodel.

Planned fields:
- token_uid
- fusion_case_id
- girilir_mi
- neden
- engel
- risk
- firsat
- yasam_evresi
- manuel_onay_gerekir_mi
- evidence_refs
- confidence
- route_recommendation
- risk_final_gate_required
- updated_at_utc

## SIGNAL CLASSES
- HAYIR
- IZLE
- DENEME
- ADAY

## NON-GOALS
- No DB write
- No schema apply
- No TempDB dry-run
- No runtime binding
- No panel update
- No API call
- No service restart
- No git push

## NEXT_SAFE_STEP
PHASE44D_INTELLIGENCE_FUSION_ENGINE_TEMPDB_DRYRUN_NOAPI

## FINAL_GATE
PASS_PHASE44C_INTELLIGENCE_FUSION_ENGINE_SCHEMA_PLAN_NOAPI
