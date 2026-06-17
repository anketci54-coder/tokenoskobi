# PASS11F Alpha Watcher Sample Outputs

PHASE=PASS11F_ALPHA_WATCHER_SAMPLE_OUTPUT_REAL_APPLY
MODE=DOCUMENTATION_ONLY
SOURCE_OF_TRUTH=PROJECT_MASTER_STATE.md

## Safety

NO_DB_WRITE=true
NO_RUNTIME_IMPLEMENTATION=true
NO_API_CALL=true
NO_PANEL_WRITE=true
NO_SERVICE_TIMER_CHANGE=true
NO_WALLET_PAPER_LIVE=true

## Sample Outputs

### 1. whale_accumulation_watch

event_id=SAMPLE_ALPHA_001
alpha_signal_type=WHALE_ACCUMULATION
adversarial_pattern_type=NONE
evidence_level=L1_SAMPLE
confidence=0.62
severity=MEDIUM
recommended_action=WATCH
authority_level=OBSERVATION_ONLY
hot_path_safe=true
risk_engine_required=true
phase41_feed_candidate=true

### 2. liquidity_risk_quarantine

event_id=SAMPLE_ALPHA_002
alpha_signal_type=LIQUIDITY_RISK
adversarial_pattern_type=LIQUIDITY_MIRAGE
evidence_level=L1_SAMPLE
confidence=0.78
severity=HIGH
recommended_action=QUARANTINE
authority_level=OBSERVATION_ONLY
hot_path_safe=true
risk_engine_required=true
phase41_feed_candidate=true

### 3. unknown_anomaly_review

event_id=SAMPLE_ALPHA_003
alpha_signal_type=UNKNOWN_ANOMALY
adversarial_pattern_type=UNKNOWN
evidence_level=L1_SAMPLE
confidence=0.55
severity=MEDIUM
recommended_action=REVIEW
authority_level=OBSERVATION_ONLY
hot_path_safe=false
risk_engine_required=true
phase41_feed_candidate=false

### 4. adversarial_pattern_detected

event_id=SAMPLE_ALPHA_004
alpha_signal_type=ADVERSARIAL_PATTERN
adversarial_pattern_type=SANDWICH_BAIT
evidence_level=L1_SAMPLE
confidence=0.81
severity=HIGH
recommended_action=DOWNGRADE
authority_level=OBSERVATION_ONLY
hot_path_safe=true
risk_engine_required=true
phase41_feed_candidate=true

### 5. phase41_feed_candidate

event_id=SAMPLE_ALPHA_005
alpha_signal_type=EARLY_ALPHA
adversarial_pattern_type=NONE
evidence_level=L1_SAMPLE
confidence=0.67
severity=LOW
recommended_action=WATCH
authority_level=OBSERVATION_ONLY
hot_path_safe=true
risk_engine_required=true
phase41_feed_candidate=true

### 6. low_confidence_ignore

event_id=SAMPLE_ALPHA_006
alpha_signal_type=LOW_CONFIDENCE_NOISE
adversarial_pattern_type=NONE
evidence_level=L1_SAMPLE
confidence=0.21
severity=LOW
recommended_action=IGNORE
authority_level=OBSERVATION_ONLY
hot_path_safe=true
risk_engine_required=false
phase41_feed_candidate=false

## Forbidden

TRADE=false
SIGN=false
SEND_TRANSACTION=false
ENABLE_API=false
OVERRIDE_RISK_ENGINE=false
MANIPULATE_MARKET=false
