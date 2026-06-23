# PHASE45B_HAREKAT_SUBAYI_SCHEMA_PLAN_NOAPI

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
WALLET_AUTHORITY=false
AUTO_APPLY=false

## PURPOSE
Plan future schema for Harekât Subayı.

No tables are created.
No schema is applied.
No TempDB is used.

## FUTURE TABLE PLAN

### operations_officer_sessions_v1
Purpose:
Conversation/session tracking for Harekât Subayı.

Planned fields:
- session_id
- opened_at_utc
- closed_at_utc
- topic
- context_source
- diagnosis_count
- repair_plan_count
- export_plan_count
- confidence_score

### operations_officer_diagnosis_v1
Purpose:
Root cause analysis memory.

Planned fields:
- diagnosis_id
- session_id
- subsystem
- symptom
- root_cause
- severity
- confidence
- evidence_refs
- created_at_utc

### operations_officer_repair_plans_v1
Purpose:
Track proposed repair plans.

Planned fields:
- repair_plan_id
- diagnosis_id
- repair_title
- repair_strategy
- rollback_required
- post_audit_required
- approval_required
- created_at_utc

### operations_officer_training_exports_v1
Purpose:
Training/export planning history.

Planned fields:
- export_id
- export_mode
- export_scope
- sanitized
- secrets_removed
- bundle_size
- destination_type
- created_at_utc

## TRAINING EXPORT MODES

- last_24h
- last_7d
- last_30d
- only_errors
- only_missed_opportunities
- only_scam_rug_honeypot_cases
- only_paper_outcomes

## SECURITY RULES

- no_secrets
- no_wallet_data
- no_auth_files
- no_api_keys
- sanitized_exports_only
- no_raw_live_db_export

## NEXT_SAFE_STEP

PHASE45C_HAREKAT_SUBAYI_TEMPDB_DRYRUN_NOAPI

## FINAL_GATE

PASS_PHASE45B_HAREKAT_SUBAYI_SCHEMA_PLAN_NOAPI
