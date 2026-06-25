# PHASE31D2_CANONICAL_MISSING_RAW_HASH_TEST_REPAIR_TEMPDB_DRYRUN_NOAPI

STAMP=20260608_204641
FINAL_GATE=PASS_PHASE31D2_CANONICAL_MISSING_RAW_HASH_TEST_REPAIR_TEMPDB_DRYRUN_NOAPI
RC=0
FAILED_CHECKS=[]
DECISION=OPEN_PHASE31E_CANONICAL_SUPERSEDE_AND_QUARANTINE_POST_DRYRUN_AUDIT_NOAPI

## D09 REPAIR
D09_TRUE_NULL_REPAIR_TESTED=True
D09_EXPECTED_REJECT=True
D09_ACTUAL_REJECT=True
D09_OK_TRUE=True
D09_ERROR=NOT NULL constraint failed: provenance_canonical_events_v1.raw_hash

## TEST MATRIX
TEST_CASE_COUNT=21
TEST_PASSED=21
TEST_FAILED=0
TEST_MATRIX_ALL_PASS=True
- D01 canonical_v1_accept | expected=ACCEPT | actual=ACCEPT | ok=True | error=None
- D02 canonical_v2_without_supersedes_reject | expected=REJECT | actual=REJECT | ok=True | error=canonical_v2_plus_requires_supersedes_canonical_uid
- D03 canonical_v2_same_entity_supersedes_accept | expected=ACCEPT | actual=ACCEPT | ok=True | error=None
- D04 canonical_v2_different_entity_supersedes_reject | expected=REJECT | actual=REJECT | ok=True | error=supersedes_must_belong_to_same_entity_uid
- D05 canonical_duplicate_version_reject | expected=REJECT | actual=REJECT | ok=True | error=UNIQUE constraint failed: provenance_canonical_events_v1.canonical_entity_uid, provenance_canonical_events_v1.canonical_version
- D06 canonical_same_validated_uid_reject | expected=REJECT | actual=REJECT | ok=True | error=UNIQUE constraint failed: provenance_canonical_events_v1.validated_uid
- D07 canonical_missing_parser_version_reject | expected=REJECT | actual=REJECT | ok=True | error=NOT NULL constraint failed: provenance_canonical_events_v1.parser_version
- D08 canonical_missing_schema_version_reject | expected=REJECT | actual=REJECT | ok=True | error=NOT NULL constraint failed: provenance_canonical_events_v1.schema_version
- D09 canonical_missing_raw_hash_reject | expected=REJECT | actual=REJECT | ok=True | error=NOT NULL constraint failed: provenance_canonical_events_v1.raw_hash
- D10 canonical_missing_source_hash_reject | expected=REJECT | actual=REJECT | ok=True | error=NOT NULL constraint failed: provenance_canonical_events_v1.source_hash
- D11 canonical_missing_evidence_ref_reject | expected=REJECT | actual=REJECT | ok=True | error=NOT NULL constraint failed: provenance_canonical_events_v1.evidence_ref
- D12 quarantine_truth_flag_reject | expected=REJECT | actual=REJECT | ok=True | error=CHECK constraint failed: truth_flag = 0
- D13 quarantine_open_accept | expected=ACCEPT | actual=ACCEPT | ok=True | error=None
- D14 quarantine_promotion_review_not_truth_accept | expected=ACCEPT | actual=ACCEPT | ok=True | error=None
- D15 quarantine_restore_requires_plan_reject | expected=REJECT | actual=REJECT | ok=True | error=restore_requires_plan
- D16 quarantine_blocks_active_use_block | expected=BLOCK | actual=BLOCK | ok=True | error=quarantine_blocks_active_use
- D17 canonical_v1_with_supersedes_reject | expected=REJECT | actual=REJECT | ok=True | error=canonical_v1_must_not_supersede
- D18 canonical_old_status_retained_superseded_accept | expected=ACCEPT | actual=ACCEPT | ok=True | error=None
- D19 quarantine_invalid_status_reject | expected=REJECT | actual=REJECT | ok=True | error=CHECK constraint failed: quarantine_status IN ('OPEN','REJECTED','PROMOTION_REVIEW','PROMOTED_BY_FUTURE_APPROVAL')
- D20 canonical_delete_forbidden_reject | expected=REJECT | actual=REJECT | ok=True | error=delete_forbidden_retention_required
- D21 quarantine_cannot_open_paper_live_block | expected=BLOCK | actual=BLOCK | ok=True | error=quarantine_cannot_open_paper_live

## CORE CHECKS
CANONICAL_MISSING_FIELDS_REJECT=True
CANONICAL_V2_WITHOUT_SUPERSEDES_REJECT=True
CANONICAL_V2_SAME_ENTITY_SUPERSEDES_ACCEPT=True
CANONICAL_V2_DIFFERENT_ENTITY_SUPERSEDES_REJECT=True
QUARANTINE_TRUTH_FLAG_REJECT=True
QUARANTINE_OPEN_ACCEPT=True
QUARANTINE_BLOCKS_ACTIVE_USE=True
QUARANTINE_CANNOT_OPEN_PAPER_LIVE=True

## SPEED GUARD
FAST_PATH_NOT_TOUCHED=True
MAINTENANCE_ONLY=True
AI_NOT_TOUCHED=True

## SYSTEM STATE
SERVICE_RESULT=success
SERVICE_EXEC_MAIN_STATUS=0
SERVICE_NEED_DAEMON_RELOAD=no
TIMER_ACTIVE=active
TIMER_ENABLED=enabled
TIMER_NEED_DAEMON_RELOAD=no
LIVE_DB_INTEGRITY_OK=True
LIVE_DB_QUICK_CHECK_OK=True
LIVE_DB_FOREIGN_KEY_0=True
PAPER_RUNTIME_ZERO=True
ACTIVE_INDEX_EXPECTED_SHA=True
RUNNER_EXPECTED_SHA=True

## IMMUTABILITY
LIVE_DB_UNCHANGED_DURING_DRYRUN=True
ACTIVE_INDEX_UNCHANGED_DURING_DRYRUN=True
RUNNER_UNCHANGED_DURING_DRYRUN=True
SERVICE_UNIT_UNCHANGED_DURING_DRYRUN=True
TIMER_UNIT_UNCHANGED_DURING_DRYRUN=True
NO_FORBIDDEN_ACTIONS=True

## NEXT
NEXT_PHASE=OPEN_PHASE31E_CANONICAL_SUPERSEDE_AND_QUARANTINE_POST_DRYRUN_AUDIT_NOAPI
REPORT=/root/tokenoskobi_clean_v1/reports/LATEST_PHASE31D2_CANONICAL_MISSING_RAW_HASH_TEST_REPAIR_TEMPDB_DRYRUN_NOAPI.md
JSON=/root/tokenoskobi_clean_v1/data/phase31d2_canonical_missing_raw_hash_test_repair_tempdb_dryrun_noapi.json
ROWS=/root/tokenoskobi_clean_v1/data/phase31d2_canonical_missing_raw_hash_test_repair_tempdb_dryrun_noapi_rows.jsonl
PROMPT_RETURNED_NO_LOGOUT=1
