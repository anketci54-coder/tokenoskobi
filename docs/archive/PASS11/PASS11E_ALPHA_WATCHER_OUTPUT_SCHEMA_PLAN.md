# PASS11E Alpha Watcher Output Schema Plan

PHASE=PASS11E_ALPHA_WATCHER_OUTPUT_SCHEMA_REAL_APPLY
MODE=DOCUMENTATION_ONLY
SOURCE_OF_TRUTH=PROJECT_MASTER_STATE.md

## Purpose

Define Alpha Watcher output schema before any DB/runtime/panel integration.

## Schema Areas

### Identity Fields
- event_id
- observed_at_utc
- schema_version

### Source and Chain Fields
- source_family
- source_name
- chain
- network

### Token and Pair Fields
- token_address
- pair_address
- base_asset
- quote_asset

### Signal Classification Fields
- alpha_signal_type
- signal_family
- signal_age_seconds
- signal_freshness_state

### Adversarial Pattern Fields
- adversarial_pattern_type
- adversarial_confidence
- adversarial_evidence_summary

### Evidence / Confidence / Severity Fields
- evidence_level
- confidence
- severity
- evidence_refs
- evidence_hash

### Recommended Action Fields
- recommended_action
- action_reason
- review_required

### Authority and Safety Fields
- authority_level
- trade_authority
- wallet_authority
- api_authority
- hot_path_safe
- risk_engine_required

### Phase41 Feed Candidate Fields
- phase41_feed_candidate
- phase41_feed_reason
- phase41_context_only

### Audit / Debug Fields
- producer_name
- contract_version
- created_at_utc
- notes

## Allowed Actions

- WATCH
- DOWNGRADE
- QUARANTINE
- REVIEW
- IGNORE

## Forbidden Actions

- TRADE
- SIGN
- SEND_TRANSACTION
- ENABLE_API
- OVERRIDE_RISK_ENGINE
- MANIPULATE_MARKET

## Safety

NO_DB_SCHEMA_APPLY=true
NO_RUNTIME_IMPLEMENTATION=true
NO_API_CALL=true
NO_PANEL_WRITE=true
NO_SERVICE_TIMER_CHANGE=true
NO_WALLET_PAPER_LIVE=true
