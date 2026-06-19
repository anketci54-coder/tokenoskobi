# PASS11C Alpha Watcher Output Contract

OUTPUT_MODE=DOCUMENTATION_CONTRACT_ONLY

Required fields:

- event_id
- observed_at_utc
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
- hot_path_safe
- phase41_feed_candidate
- risk_engine_required
- notes

Allowed actions:

- WATCH
- DOWNGRADE
- QUARANTINE
- REVIEW
- IGNORE

Forbidden actions:

- TRADE
- SIGN
- SEND_TRANSACTION
- ENABLE_API
- OVERRIDE_RISK_ENGINE
- MANIPULATE_MARKET
