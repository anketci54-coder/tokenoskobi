# PHASE31C_CANONICAL_SUPERSEDE_AND_QUARANTINE_LIFECYCLE_CONTRACT_NOAPI

STAMP=20260608_181601
FINAL_GATE=PASS_PHASE31C_CANONICAL_SUPERSEDE_AND_QUARANTINE_LIFECYCLE_CONTRACT_NOAPI
RC=0
FAILED_CHECKS=[]
DECISION=OPEN_PHASE31D_CANONICAL_SUPERSEDE_AND_QUARANTINE_TEMPDB_DRYRUN_NOAPI

## DEPENDENCY
PHASE31B_PASS_AND_OPEN_31C=True
PHASE31B_FINAL_GATE=PASS_PHASE31B_DATA_PROVENANCE_CONSTRAINT_AND_LIFECYCLE_TEST_MATRIX_NOAPI
PHASE31B_DECISION=OPEN_PHASE31C_CANONICAL_SUPERSEDE_AND_QUARANTINE_LIFECYCLE_CONTRACT_NOAPI
PHASE31B_TEST_MATRIX_ALL_PASS=True
PHASE31B_TEST_MATRIX_FAILED=None

## CORE RULE
Canonical can only change by versioned append/supersede; quarantine is retained evidence and never truth. This phase is contract-only and does not mutate live DB/panel/runner/service/timer.

## LIFECYCLE STATES
- CANDIDATE: Artifact/event is proposed but not trusted as canonical. | active_use_allowed=False
- CANONICAL_ACTIVE: Current accepted version for a canonical entity. | active_use_allowed=only_after_future_explicit_real_apply
- CANONICAL_SUPERSEDED: Old canonical version is replaced by a newer version but retained as evidence. | active_use_allowed=False
- QUARANTINE_OPEN: Bad, conflicting, incomplete, stale, or suspicious evidence is retained for review. | active_use_allowed=False
- QUARANTINE_REJECTED: Evidence is retained but rejected from canonical path. | active_use_allowed=False
- QUARANTINE_PROMOTION_REVIEW: Quarantined evidence may be reviewed for future promotion but is still not truth. | active_use_allowed=False
- RESTORE_CANDIDATE: A superseded/quarantined artifact may only be restored via future restore plan, dry-run, approval, real apply, post-audit. | active_use_allowed=False
- RETIRED_DO_NOT_USE: Historical artifact retained for audit; never active without a new approved lifecycle. | active_use_allowed=False

## CANONICAL SUPERSEDE RULES
- Canonical silent overwrite is forbidden.
- Canonical update must be append-only with a new canonical_uid.
- canonical_version must increase monotonically per canonical_entity_uid.
- canonical_version=1 must not supersede anything.
- canonical_version>1 must reference supersedes_canonical_uid.
- supersedes_canonical_uid must exist and must belong to the same canonical_entity_uid.
- New canonical version must link to validated_uid.
- validated_uid must link back to staging_uid and raw_uid.
- parser_version, schema_version, raw_hash, source_hash, evidence_ref are mandatory.
- Old canonical version is retained as CANONICAL_SUPERSEDED, not deleted.
- Future real apply must backup first and provide rollback.
- No token-specific exception is allowed.

## QUARANTINE RULES
- Quarantine is not truth.
- truth_flag must remain false/0.
- Quarantined evidence must be retained with reason, source, hash, parser/schema version, and evidence_ref.
- Quarantine does not delete evidence.
- Quarantine blocks active use.
- Quarantine promotion requires separate plan, dry-run, explicit approval, real apply, and post-audit.
- Quarantine restore requires separate restore plan and explicit approval.
- Bad parse, missing hash, schema conflict, source conflict, FK break, stale evidence, and overwrite attempt may route to quarantine.
- Quarantine cannot open paper/live route.
- Quarantine cannot become canonical without validated chain.

## FUTURE TEST CASES
- canonical_v1_accept
- canonical_v2_without_supersedes_reject
- canonical_v2_with_same_entity_supersedes_accept
- canonical_v2_with_different_entity_supersedes_reject
- canonical_duplicate_version_reject
- canonical_same_validated_uid_reject
- canonical_missing_parser_version_reject
- canonical_missing_schema_version_reject
- canonical_missing_raw_hash_reject
- canonical_missing_source_hash_reject
- canonical_missing_evidence_ref_reject
- quarantine_truth_flag_reject
- quarantine_open_accept
- quarantine_promotion_review_not_truth
- quarantine_restore_requires_plan
- quarantine_blocks_active_use

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
LIVE_DB_UNCHANGED_DURING_CONTRACT=True
ACTIVE_INDEX_UNCHANGED_DURING_CONTRACT=True
RUNNER_UNCHANGED_DURING_CONTRACT=True
SERVICE_UNIT_UNCHANGED_DURING_CONTRACT=True
TIMER_UNIT_UNCHANGED_DURING_CONTRACT=True
NO_FORBIDDEN_ACTIONS=True

## NEXT
NEXT_PHASE=OPEN_PHASE31D_CANONICAL_SUPERSEDE_AND_QUARANTINE_TEMPDB_DRYRUN_NOAPI
REPORT=/root/tokenoskobi_clean_v1/reports/LATEST_PHASE31C_CANONICAL_SUPERSEDE_AND_QUARANTINE_LIFECYCLE_CONTRACT_NOAPI.md
JSON=/root/tokenoskobi_clean_v1/data/phase31c_canonical_supersede_and_quarantine_lifecycle_contract_noapi.json
ROWS=/root/tokenoskobi_clean_v1/data/phase31c_canonical_supersede_and_quarantine_lifecycle_contract_noapi_rows.jsonl
PROMPT_RETURNED_NO_LOGOUT=1
