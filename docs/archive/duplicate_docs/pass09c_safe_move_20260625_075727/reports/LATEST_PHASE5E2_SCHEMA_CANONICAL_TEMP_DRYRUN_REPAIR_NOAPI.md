# PHASE5E2_SCHEMA_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI

- FINAL_GATE: `PASS_PHASE5E2_SCHEMA_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI`
- NEXT_PHASE: `PHASE5F_SCHEMA_APPLY_PLAN_NOAPI`
- LIVE_DB_UNCHANGED: `True`
- ACTIVE_INDEX_UNCHANGED: `True`
- HOSTS_UNCHANGED: `True`
- POLICY_SHA_MATCH_START: `True`
- POLICY_SHA_MATCH_END: `True`
- POLICY_MATCH_PATHS_SAME: `True`
- TEMP_APPLY_OK: `True`
- TEMP_DB_INTEGRITY_AFTER: `ok`
- TEMP_DB_FK_AFTER: `0`
- API_RPC_FETCH: `0`
- LIVE_DB_MUTATION: `False`
- TEMP_DB_MUTATION: `True`
- PANEL_MUTATION: `False`
- SERVICE_TIMER_MUTATION: `False`
- PAPER_LIVE_WATCHLIST_SCORE: `False`

## Canonical conflict review

- `outcome_memory_events_v2` variants=`2` chosen=`/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql` rule=`prefer_latest_phase_then_widest_definition`

## Summary

- canonical_table_count: `37`
- canonical_index_count: `178`
- skipped_index_count: `57`
- planned_tables_exist_in_temp_after: `True`
- new_tables_in_temp_count: `37`
- live_counts_unchanged: `True`

## Failed checks

- none

## Warnings

- `SCHEMA_CONFLICT_CANONICALIZED_REVIEW_BEFORE_LIVE_APPLY`
- `TEMP_DB_CREATED_NEW_TABLES_AS_EXPECTED`
- `SOME_INDEXES_SKIPPED_DURING_CANONICALIZATION`

## Outputs

- JSON: `/root/tokenoskobi_clean_v1/data/phase5e2_schema_canonical_temp_dryrun_repair_noapi.json`
- ROWS: `/root/tokenoskobi_clean_v1/data/phase5e2_schema_canonical_temp_dryrun_repair_noapi_rows.jsonl`
- WORK_DIR: `/root/tokenoskobi_clean_v1/_PHASE5E2_SCHEMA_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_000935`
- TEMP_DB: `/root/tokenoskobi_clean_v1/_PHASE5E2_SCHEMA_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_000935/phase5e2_canonical_temp_schema_dryrun.sqlite`
- CANONICAL_SQL: `/root/tokenoskobi_clean_v1/_PHASE5E2_SCHEMA_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_000935/phase5e2_canonical_combined_schema_temp_apply_noapi.sql`
- CANONICAL_TABLE_ROWS: `/root/tokenoskobi_clean_v1/_PHASE5E2_SCHEMA_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_000935/phase5e2_canonical_table_choice.jsonl`
- INDEX_ROWS: `/root/tokenoskobi_clean_v1/_PHASE5E2_SCHEMA_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_000935/phase5e2_canonical_index_choice.jsonl`
- APPLY_ROWS: `/root/tokenoskobi_clean_v1/_PHASE5E2_SCHEMA_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_000935/phase5e2_canonical_temp_apply_results.jsonl`
- TABLE_AUDIT_ROWS: `/root/tokenoskobi_clean_v1/_PHASE5E2_SCHEMA_CANONICAL_TEMP_DRYRUN_REPAIR_NOAPI/20260601_000935/phase5e2_canonical_temp_table_audit.jsonl`