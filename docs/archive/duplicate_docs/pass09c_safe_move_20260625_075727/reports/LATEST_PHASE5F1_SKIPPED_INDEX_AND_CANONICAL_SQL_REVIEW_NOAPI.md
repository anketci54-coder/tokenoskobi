# PHASE5F1_SKIPPED_INDEX_AND_CANONICAL_SQL_REVIEW_NOAPI

- FINAL_GATE: `PASS_PHASE5F1_SKIPPED_INDEX_AND_CANONICAL_SQL_REVIEW_NOAPI`
- NEXT_PHASE: `PHASE5G_SCHEMA_APPLY_REAL_AFTER_EXPLICIT_APPROVAL`
- LIVE_DB_UNCHANGED: `True`
- ACTIVE_INDEX_UNCHANGED: `True`
- HOSTS_UNCHANGED: `True`
- POLICY_SHA_MATCH_START: `True`
- POLICY_SHA_MATCH_END: `True`
- POLICY_MATCH_PATHS_SAME: `True`
- PHASE5F_DEPENDENCY_OK: `True`
- REAL_APPLY_ALLOWED_NOW: `False`
- APPROVAL_REQUIRED_EXACT: `PHASE5G_SCHEMA_APPLY_REAL_AFTER_EXPLICIT_APPROVAL için onay veriyorum`
- API_RPC_FETCH: `0`
- LIVE_DB_MUTATION: `False`
- PANEL_MUTATION: `False`
- SERVICE_TIMER_MUTATION: `False`
- PAPER_LIVE_WATCHLIST_SCORE: `False`

## Skipped index review

- skipped_index_count: `57`
- unknown_skipped_reasons: `0`
- reason `duplicate_index_name`: `57`

## Canonical SQL review

- canonical_table_count: `37`
- canonical_index_count: `178`
- canonical_index_errors: `0`
- duplicate_selected_index_names: `0`

## Apply readiness

- `phase5f_passed` required=`True` status=`True`
- `exact_approval_still_required` required=`True` status=`True`
- `real_apply_allowed_now_false` required=`True` status=`True`
- `backup_before_write_required` required=`True` status=`True`
- `rollback_required` required=`True` status=`True`
- `skipped_index_review_completed` required=`True` status=`True`
- `unknown_skipped_reasons_none` required=`True` status=`True`
- `canonical_sql_review_clean` required=`True` status=`True`

## Failed checks

- none

## Warnings

- `SKIPPED_INDEX_REVIEW_COMPLETED_ACCEPTED_IN_PLAN`
- `SKIPPED_INDEX_REASON_COUNTS_RECORDED`
- `REAL_APPLY_STILL_REQUIRES_EXACT_APPROVAL`

## Outputs

- JSON: `/root/tokenoskobi_clean_v1/data/phase5f1_skipped_index_and_canonical_sql_review_noapi.json`
- ROWS: `/root/tokenoskobi_clean_v1/data/phase5f1_skipped_index_and_canonical_sql_review_noapi_rows.jsonl`
- WORK_DIR: `/root/tokenoskobi_clean_v1/_PHASE5F1_SKIPPED_INDEX_AND_CANONICAL_SQL_REVIEW_NOAPI/20260601_071753`
- SKIPPED_INDEX_REVIEW_ROWS: `/root/tokenoskobi_clean_v1/_PHASE5F1_SKIPPED_INDEX_AND_CANONICAL_SQL_REVIEW_NOAPI/20260601_071753/phase5f1_skipped_index_review.jsonl`
- CANONICAL_SQL_REVIEW_ROWS: `/root/tokenoskobi_clean_v1/_PHASE5F1_SKIPPED_INDEX_AND_CANONICAL_SQL_REVIEW_NOAPI/20260601_071753/phase5f1_canonical_sql_review.jsonl`
- APPLY_READINESS_ROWS: `/root/tokenoskobi_clean_v1/_PHASE5F1_SKIPPED_INDEX_AND_CANONICAL_SQL_REVIEW_NOAPI/20260601_071753/phase5f1_apply_readiness_review.jsonl`
- PLAN_JSON: `/root/tokenoskobi_clean_v1/_PHASE5F1_SKIPPED_INDEX_AND_CANONICAL_SQL_REVIEW_NOAPI/20260601_071753/phase5f1_skipped_index_and_canonical_sql_review_plan_noapi.json`