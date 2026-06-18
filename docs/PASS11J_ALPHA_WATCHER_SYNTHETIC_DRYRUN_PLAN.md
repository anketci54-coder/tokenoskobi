# PASS11J Alpha Watcher Synthetic Dryrun Plan

PHASE=PASS11J_ALPHA_WATCHER_SYNTHETIC_DRYRUN_DOC_REAL_APPLY
MODE=DOCUMENTATION_ONLY
SOURCE_OF_TRUTH=PROJECT_MASTER_STATE.md

## Purpose

Plan the first Alpha Watcher synthetic dryrun without DB/runtime/API/panel mutation.

## Input Contract

- docs/PASS11I_ALPHA_WATCHER_RUNTIME_CONTRACT_PLAN.md
- docs/PASS11E_ALPHA_WATCHER_OUTPUT_SCHEMA_PLAN.md
- docs/PASS11F_ALPHA_WATCHER_SAMPLE_OUTPUTS.md

## Synthetic Dryrun Cases

1. valid_whale_accumulation_context=EXPECTED_PASS
2. liquidity_mirage_quarantine_context=EXPECTED_PASS
3. unknown_anomaly_review_context=EXPECTED_PASS
4. adversarial_pattern_downgrade_context=EXPECTED_PASS
5. low_confidence_ignore_context=EXPECTED_PASS
6. forbidden_trade_authority_block=EXPECTED_BLOCK

## Expected Output Family

alpha_watcher_context_events

## Validation Rules

- Must follow PASS11E output schema.
- Must match PASS11F sample constraints.
- Must remain observation/enrichment only.
- Must not create trade authority.
- Must not override Risk Engine.
- Must not block HOT path.
- Must not call API.
- Must not write DB.
- Must not write panel.
- Must not change service/timer state.

## Synthetic Result Contract

Expected result artifact for next phase:

docs/PASS11K_ALPHA_WATCHER_SYNTHETIC_DRYRUN_RESULT.md

## Forbidden Now

NO_RUNTIME_IMPLEMENTATION=true
NO_DB_WRITE=true
NO_DB_SCHEMA_APPLY=true
NO_API_CALL=true
NO_PANEL_WRITE=true
NO_SERVICE_TIMER_CHANGE=true
NO_WALLET_PAPER_LIVE=true

## Next Safe Step

PASS11K_ALPHA_WATCHER_SYNTHETIC_DRYRUN_RESULT_PLAN_NOAPI
