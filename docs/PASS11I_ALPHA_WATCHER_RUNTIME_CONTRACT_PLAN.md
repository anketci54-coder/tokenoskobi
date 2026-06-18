# PASS11I Alpha Watcher Runtime Contract Plan

PHASE=PASS11I_ALPHA_WATCHER_RUNTIME_CONTRACT_DOC_REAL_APPLY
MODE=DOCUMENTATION_ONLY
SOURCE_OF_TRUTH=PROJECT_MASTER_STATE.md

## Runtime Contract Purpose

Define the future Alpha Watcher runtime contract before implementation.

This document does not implement runtime code, does not write DB schema, does not call APIs, and does not mutate panel/service/timer state.

## Position

ALPHA_WATCHER_POSITION=CANONICAL_V1_SIDECAR_ENRICHMENT_LAYER
PIPELINE_POSITION=Hunter_and_Priority_sidecar_before_Prosecutor
AUTHORITY=OBSERVATION_AND_ENRICHMENT_ONLY
TRADE_AUTHORITY=0
RISK_ENGINE_FINAL_AUTHORITY=true
HOT_PATH_NEVER_WAITS=true

## Runtime Inputs

Allowed future input families:

- hunter_candidate_events
- priority_candidate_events
- token_context_snapshot
- whale_context_snapshot
- technical_context_snapshot
- news_context_snapshot
- risk_precheck_context

## Runtime Outputs

Future output event family:

- alpha_watcher_context_events

Output must follow PASS11E schema and PASS11F sample constraints.

## Runtime Rules

- Must be sidecar.
- Must not block hot path.
- Must not make trade decisions.
- Must not override Risk Engine.
- Must not sign or send transactions.
- Must not enable API providers.
- Must support dryrun-first execution.
- Must support TempDB validation before live DB consideration.
- Must emit observation/enrichment context only.

## First Execution Path

1. Documentation contract
2. Synthetic dryrun
3. TempDB dryrun
4. Read-only runtime skeleton
5. Readmodel binding
6. Phase41 context feed binding
7. Post-audit
8. GitHub checkpoint

## Forbidden Now

NO_RUNTIME_IMPLEMENTATION=true
NO_DB_WRITE=true
NO_DB_SCHEMA_APPLY=true
NO_API_CALL=true
NO_PANEL_WRITE=true
NO_SERVICE_TIMER_CHANGE=true
NO_WALLET_PAPER_LIVE=true

## Next Safe Step

PASS11J_ALPHA_WATCHER_SYNTHETIC_DRYRUN_PLAN_NOAPI
