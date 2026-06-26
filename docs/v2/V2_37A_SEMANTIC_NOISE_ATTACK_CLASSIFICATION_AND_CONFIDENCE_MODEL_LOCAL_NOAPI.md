# V2_37A_SEMANTIC_NOISE_ATTACK_CLASSIFICATION_AND_CONFIDENCE_MODEL_LOCAL_NOAPI

STAMP_UTC=2026-06-26T14:52:26Z
MODE=LOCAL_ONLY_NOAPI_NO_PUSH

## PURPOSE

V2_37A replaces numeric/paranoid L0-L4 classification language with semantic market-intelligence classification.

The system must not become paranoid.

## CLASSIFICATION MODEL

NOISE
MARKET_DRIFT
UNKNOWN_ANOMALY
ATTACK_SUSPECT
CONFIRMED_THREAT

## RETIRED LANGUAGE

L0_L4_NUMERIC_LADDER_RETIRED=true
NUMERIC_ALARM_BIAS_AVOIDED=true
SEMANTIC_CLASSIFICATION_REQUIRED=true

## CONFIDENCE MODEL

CONFIDENCE_SCORE_REQUIRED=true
ATTACK_SIMILARITY_SCORE_REQUIRED=true
DECISION_IMPACT_REQUIRED=true
SOURCE_REPUTATION_REQUIRED=true
PERSISTENCE_REQUIRED=true
CORRELATION_REQUIRED=true

## MEANINGS

NOISE:
- single-source deviation
- short-lived latency
- no decision impact
- action: log only

MARKET_DRIFT:
- natural volatility
- spread or route movement
- time-of-day or liquidity-regime compatible
- action: confidence decay, shadow observation

UNKNOWN_ANOMALY:
- abnormal behavior not explained by current noise profile
- no confirmed attack similarity
- action: shadow watch, evidence capture

ATTACK_SUSPECT:
- anomaly resembles known attack/noise-poisoning vectors
- requires confidence + persistence + correlation
- action: prosecutor candidate, decision fail-closed if impact exists

CONFIRMED_THREAT:
- repeated multi-source evidence
- decision poisoning potential exists
- prosecutor evidence exists
- action: hard block / source reputation decay / case lock

## NON-PARANOIA RULES

DEFAULT_ASSUMPTION=NOISE
NO_SINGLE_SIGNAL_MAY_DECLARE_ATTACK=true
ATTACK_SUSPECT_REQUIRES_CONFIDENCE_THRESHOLD=true
CONFIRMED_THREAT_REQUIRES_EVIDENCE=true
CONFIDENCE_ALONE_CANNOT_DECLARE_ATTACK=true
ATTACK_SIMILARITY_ALONE_CANNOT_DECLARE_ATTACK=true
DECISION_IMPACT_REQUIRED_FOR_FAIL_CLOSED=true

## SAMPLE EVENT CONTRACT

classification=UNKNOWN_ANOMALY
confidence_score=0.42
attack_similarity_score=0.31
decision_impact=false
source_count=1
persistence=false
correlation=false
action=shadow_watch

## FORBIDDEN

DB_WRITE=false
PANEL_WRITE=false
API_RPC=false
RUNTIME_APPLY=false
SERVICE_RESTART=false
TIMER_CHANGE=false
LIVE_DECISION=false
LIVE_TRADE=false
WALLET_ACCESS=false
PRIVATE_KEY_ACCESS=false
GITHUB_PUSH=false

## FINAL

FINAL_GATE=PASS_V2_37A_SEMANTIC_NOISE_ATTACK_CLASSIFICATION_AND_CONFIDENCE_MODEL_LOCAL_NOAPI
DECISION=V2_37A_LOCAL_SPEC_PASS_READY_FOR_NEXT_LOCAL_SUBTASK
NEXT=V2_37B_DYNAMIC_THRESHOLD_AND_SECURITY_FLOOR_MODEL_LOCAL_NOAPI
