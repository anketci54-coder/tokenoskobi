# PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI

- FINAL_GATE: `PASS_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI`
- NEXT_PHASE: `PHASE6G4_BASE_READMODEL_TABLE_SQL_REPAIR_TEMP_DRYRUN_NOAPI`
- LIVE_DB_UNCHANGED: `True`
- APPLY_ERROR_COUNT: `5`
- ERROR_CLASS_COUNTS: `{'BASE_TABLE_CREATE_SQL_SYNTAX_ERROR': 1, 'DEPENDENT_INDEX_TARGET_TABLE_MISSING': 4}`
- BASE_TABLE: `state_aggregated_token_readmodel_v1`
- BASE_TABLE_ERROR_COUNT: `1`
- DEPENDENT_INDEX_ERROR_COUNT: `4`
- ROOT_CAUSE_CLASS: `BASE_TABLE_SQL_SYNTAX`
- NEAR_TOKEN: `no`

## Base table diagnosis

- `state_aggregated_token_readmodel_v1` error=`near "no": syntax error` diagnosis=`base table create statement did not apply; dependent indexes failed because table was absent`

## Dependent indexes

- `idx_state_token_readmodel_chain_token` missing=`True` diagnosis=`DEPENDENT_FAILURE_CAUSED_BY_BASE_TABLE_NOT_CREATED`
- `idx_state_token_readmodel_decision` missing=`True` diagnosis=`DEPENDENT_FAILURE_CAUSED_BY_BASE_TABLE_NOT_CREATED`
- `idx_state_token_readmodel_token_uid` missing=`True` diagnosis=`DEPENDENT_FAILURE_CAUSED_BY_BASE_TABLE_NOT_CREATED`
- `idx_state_token_readmodel_updated` missing=`True` diagnosis=`DEPENDENT_FAILURE_CAUSED_BY_BASE_TABLE_NOT_CREATED`

## Failed checks

- none

## Outputs

- report: `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI.md`
- json: `/root/tokenoskobi_clean_v1/data/phase6g3_canonical_temp_dryrun_failure_diagnose_noapi.json`
- rows: `/root/tokenoskobi_clean_v1/data/phase6g3_canonical_temp_dryrun_failure_diagnose_noapi_rows.jsonl`
- work_dir: `/root/tokenoskobi_clean_v1/_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI/20260601_114517`
- apply_error_diag_rows: `/root/tokenoskobi_clean_v1/_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI/20260601_114517/phase6g3_apply_error_diagnose.jsonl`
- base_table_diag_rows: `/root/tokenoskobi_clean_v1/_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI/20260601_114517/phase6g3_base_readmodel_table_diagnose.jsonl`
- dependent_index_diag_rows: `/root/tokenoskobi_clean_v1/_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI/20260601_114517/phase6g3_dependent_index_failure_diagnose.jsonl`
- canonical_stmt_diag_rows: `/root/tokenoskobi_clean_v1/_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI/20260601_114517/phase6g3_canonical_statement_diagnose.jsonl`
- ordered_stmt_diag_rows: `/root/tokenoskobi_clean_v1/_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI/20260601_114517/phase6g3_ordered_statement_diagnose.jsonl`
- repair_hint_rows: `/root/tokenoskobi_clean_v1/_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI/20260601_114517/phase6g3_repair_hints.jsonl`
- readiness_rows: `/root/tokenoskobi_clean_v1/_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI/20260601_114517/phase6g3_next_readiness.jsonl`
- plan_json: `/root/tokenoskobi_clean_v1/_PHASE6G3_CANONICAL_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI/20260601_114517/phase6g3_canonical_temp_dryrun_failure_diagnose_noapi.json`