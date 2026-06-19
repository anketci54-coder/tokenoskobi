# PASS11L Alpha Watcher TempDB Dryrun Plan

PHASE=PASS11L_ALPHA_WATCHER_TEMPDB_DRYRUN_DOC_REAL_APPLY
MODE=DOCUMENTATION_ONLY
SOURCE_OF_TRUTH=PROJECT_MASTER_STATE.md

## Purpose

Plan the first Alpha Watcher TempDB dryrun using isolated /tmp database only.

This phase does not write to live DB, does not apply live schema, does not start runtime, does not call API, and does not mutate panel/service/timer state.

## Inputs

- docs/PASS11K_ALPHA_WATCHER_SYNTHETIC_DRYRUN_RESULT.md
- docs/PASS11J_ALPHA_WATCHER_SYNTHETIC_DRYRUN_PLAN.md
- docs/PASS11I_ALPHA_WATCHER_RUNTIME_CONTRACT_PLAN.md
- docs/PASS11E_ALPHA_WATCHER_OUTPUT_SCHEMA_PLAN.md

## TempDB Scope

TEMPDB_ONLY=true
LIVE_DB_WRITE=false
LIVE_DB_SCHEMA_APPLY=false

Planned isolated TempDB table:

alpha_watcher_context_events_temp

## Planned Columns

- event_id
- observed_at_utc
- schema_version
- source_family
- chain
- token_address
- pair_address
- alpha_signal_type
- adversarial_pattern_type
- evidence_level
- confidence
- severity
- recommended_action
- authority_level
- trade_authority
- wallet_authority
- api_authority
- hot_path_safe
- risk_engine_required
- phase41_feed_candidate

## Planned Synthetic Rows

1. valid_whale_accumulation_context
2. liquidity_mirage_quarantine_context
3. unknown_anomaly_review_context
4. adversarial_pattern_downgrade_context
5. low_confidence_ignore_context
6. forbidden_trade_authority_block

## Validation Gates

- TempDB is under /tmp only
- Live DB SHA unchanged
- No live DB write
- No live schema apply
- No API call
- No panel write
- No service/timer change
- No wallet/paper/live
- All synthetic rows inserted into TempDB
- Required schema columns exist
- forbidden_trade_authority_block is blocked
- HOT_PATH_NEVER_WAITS preserved
- Risk Engine remains final authority

## Expected Result Artifact

docs/PASS11M_ALPHA_WATCHER_TEMPDB_DRYRUN_RESULT.md

## Forbidden Now

NO_LIVE_DB_WRITE=true
NO_LIVE_DB_SCHEMA_APPLY=true
NO_RUNTIME_IMPLEMENTATION=true
NO_API_CALL=true
NO_PANEL_WRITE=true
NO_SERVICE_TIMER_CHANGE=true
NO_WALLET_PAPER_LIVE=true

## Next Safe Step

PASS11M_ALPHA_WATCHER_TEMPDB_DRYRUN_RESULT_PLAN_NOAPI
