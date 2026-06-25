# PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI

- FINAL_GATE: `REVIEW_REQUIRED_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI`
- NEXT_PHASE: `REVIEW_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_FAILURES_NOAPI`
- LIVE_DB_UNCHANGED: `True`
- SCHEMA_SOURCE_COUNT: `10`
- ORDERED_STATEMENT_COUNT: `63`
- APPLY_OK_COUNT: `58`
- APPLY_ERROR_COUNT: `5`
- CANONICALIZED_OBJECT_COUNT: `0`
- SKIPPED_STATEMENT_COUNT: `1`
- SKIPPED_IF_COUNT: `0`
- SKIPPED_MISSING_TARGET_INDEX_COUNT: `0`
- EXPECTED_TABLE_COUNT: `24`
- EXPECTED_INDEX_COUNT: `39`
- MISSING_TABLE_COUNT_AFTER: `1`
- MISSING_INDEX_COUNT_AFTER: `4`
- TEMP_INTEGRITY_AFTER: `ok`
- TEMP_FK_COUNT_AFTER: `0`

## Failed checks

- `temp_apply_ok`
- `all_expected_tables_exist_after`
- `all_expected_indexes_exist_after`

## Warnings

- `TEMP_DB_ONLY_NO_LIVE_DB_SCHEMA_APPLY`
- `ROBUST_OBJECT_PARSER_USED_NO_IF_CAPTURE`
- `CANONICAL_OBJECT_DEDUP_AND_TABLE_FIRST_ORDER_USED`
- `NO_PANEL_OR_ACTIVE_8096_WRITE`
- `NO_API_RPC_FETCH_EXTERNAL_CALLS`
- `NO_PAPER_LIVE_WATCHLIST_SCORE_PERMISSION`

## Outputs

- report: `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI.md`
- json: `/root/tokenoskobi_clean_v1/data/phase6g2_canonical_temp_dryrun_repair_noapi.json`
- rows: `/root/tokenoskobi_clean_v1/data/phase6g2_canonical_temp_dryrun_repair_noapi_rows.jsonl`
- work_dir: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723`
- temp_db: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_canonical_temp_readmodel_schema_dryrun.sqlite`
- canonical_sql: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_canonical_readmodel_schema_temp_apply_noapi.sql`
- source_review_rows: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_schema_source_review.jsonl`
- object_choice_rows: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_canonical_object_choice.jsonl`
- skipped_stmt_rows: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_skipped_statement_review.jsonl`
- ordered_stmt_rows: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_ordered_statement_plan.jsonl`
- apply_rows: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_temp_apply_results.jsonl`
- table_audit_rows: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_temp_table_audit.jsonl`
- index_audit_rows: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_temp_index_audit.jsonl`
- temp_object_rows: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_temp_db_object_snapshot.jsonl`
- readiness_rows: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_next_readiness.jsonl`
- plan_json: `/root/tokenoskobi_clean_v1/_PHASE6G2_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_112723/phase6g2_canonical_temp_dryrun_repair_noapi.json`