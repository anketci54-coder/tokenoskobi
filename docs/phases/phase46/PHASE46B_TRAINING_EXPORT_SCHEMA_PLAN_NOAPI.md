# PHASE46B_TRAINING_EXPORT_SCHEMA_PLAN_NOAPI

## STATUS
PLAN_ONLY

## CONSTITUTIONAL_GATE_V1
SPEED_NEVER_DOWN=true
SECURITY_NEVER_DOWN=true
POWER_NEVER_DOWN=true
hot_path_waits=false
learning_blocks_execution=false
training_blocks_hot_path=false
gpu_unavailable_blocks_system=false

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
GPU_JOB_LAUNCH=false
TRAINING_RUN=false
FILE_TRANSFER=false
TRADE_AUTHORITY=false
WALLET_AUTHORITY=false
AUTO_APPLY=false

## PURPOSE
Plan future schema for training export, GPU orchestration, model registry, cost control, and learning ingestion.

No table is created.
No TempDB is used.
No file is exported.
No GPU job is launched.

## FUTURE TABLE PLAN

### training_export_bundles_v1
Purpose:
Track sanitized training bundles.

Fields:
- bundle_id
- export_mode
- export_scope
- sanitized
- secrets_removed
- wallet_data_removed
- auth_removed
- api_keys_removed
- raw_live_db_included
- bundle_manifest_path
- bundle_size_bytes
- created_at_utc

### training_gpu_jobs_v1
Purpose:
Track planned GPU training jobs.

Fields:
- gpu_job_id
- bundle_id
- gpu_provider
- gpu_type
- rental_mode
- max_duration_minutes
- budget_limit_usd
- user_approval_required
- job_status
- created_at_utc

### training_model_registry_v1
Purpose:
Track trained model artifacts.

Fields:
- model_id
- parent_model_id
- gpu_job_id
- bundle_id
- model_role
- validation_status
- approved_for_sandbox
- approved_for_live
- rollback_model_id
- created_at_utc

### learning_ingestion_queue_v1
Purpose:
Queue trained outputs for sandbox-first ingestion.

Fields:
- ingestion_id
- model_id
- ingestion_status
- sandbox_required
- post_audit_required
- rollback_required
- human_approval_required
- live_activation_allowed
- created_at_utc

### training_cost_control_v1
Purpose:
Track cost guards.

Fields:
- cost_guard_id
- gpu_job_id
- hourly_budget_usd
- daily_budget_usd
- max_training_duration_minutes
- estimated_cost_usd
- actual_cost_usd
- cost_report_required
- created_at_utc

## SECURITY RULES
- no_secrets
- no_wallet_data
- no_auth_files
- no_api_keys
- no_raw_live_db_export
- sanitized_training_bundles_only

## NEXT_SAFE_STEP
PHASE46C_TRAINING_EXPORT_TEMPDB_DRYRUN_NOAPI

## FINAL_GATE
PASS_PHASE46B_TRAINING_EXPORT_SCHEMA_PLAN_NOAPI
