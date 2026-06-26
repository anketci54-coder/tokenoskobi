# V2_37C_SHADOW_OBSERVATION_EVENT_CONTRACT_LOCAL_NOAPI

STAMP_UTC=2026-06-26T14:58:38Z
MODE=LOCAL_ONLY_NOAPI_NO_PUSH

## PURPOSE

V2_37C defines the shadow observation event contract.

This is not live runtime.
This is not API/RPC.
This is not DB schema apply.
This is not trade authority.

The goal is to define how the system will record market noise, drift, anomaly, suspect attack, and confirmed threat observations without becoming paranoid.

## EVENT CONTRACT

event_type=shadow_observation
classification=NOISE|MARKET_DRIFT|UNKNOWN_ANOMALY|ATTACK_SUSPECT|CONFIRMED_THREAT
confidence_score=0.00_to_1.00
attack_similarity_score=0.00_to_1.00
decision_impact=true|false
source_count=integer
source_reputation=trusted|degraded|unstable|quarantined
persistence=true|false
correlation=true|false
volatility_regime=low|normal|high|extreme
liquidity_regime=thin|normal|deep|unstable
time_of_day_profile=quiet|active|overlap|illiquid_night
action=log_only|confidence_decay|shadow_watch|prosecutor_candidate|decision_fail_closed|hard_block_candidate

## REQUIRED FIELDS

token_uid
chain
token_address
observed_at_utc
event_type
classification
confidence_score
attack_similarity_score
decision_impact
source_count
source_reputation
persistence
correlation
volatility_regime
liquidity_regime
time_of_day_profile
action
reason_codes
evidence_refs

## CLASSIFICATION RULES

NOISE:
- single source
- short lived
- no decision impact
- action=log_only

MARKET_DRIFT:
- compatible with volatility/liquidity/time profile
- no confirmed attack similarity
- action=confidence_decay or shadow_watch

UNKNOWN_ANOMALY:
- not explainable by current market regime
- attack similarity below threshold
- action=shadow_watch

ATTACK_SUSPECT:
- confidence threshold met
- attack similarity threshold met
- persistence=true
- correlation=true
- decision_impact=true
- action=prosecutor_candidate or decision_fail_closed

CONFIRMED_THREAT:
- multi source evidence
- repeated pattern
- prosecutor evidence
- decision poisoning potential
- action=hard_block_candidate

## NON-PARANOIA LOCKS

DEFAULT_ASSUMPTION=NOISE
NO_SINGLE_SIGNAL_MAY_DECLARE_ATTACK=true
CONFIDENCE_ALONE_CANNOT_DECLARE_ATTACK=true
ATTACK_SIMILARITY_ALONE_CANNOT_DECLARE_ATTACK=true
DECISION_IMPACT_REQUIRED_FOR_FAIL_CLOSED=true
CONFIRMED_THREAT_REQUIRES_EVIDENCE=true
SHADOW_OBSERVATION_ONLY=true

## SAMPLE EVENT

{
  "event_type": "shadow_observation",
  "classification": "UNKNOWN_ANOMALY",
  "confidence_score": 0.42,
  "attack_similarity_score": 0.31,
  "decision_impact": false,
  "source_count": 1,
  "source_reputation": "degraded",
  "persistence": false,
  "correlation": false,
  "volatility_regime": "normal",
  "liquidity_regime": "thin",
  "time_of_day_profile": "illiquid_night",
  "action": "shadow_watch",
  "reason_codes": ["single_source_drift", "thin_liquidity"],
  "evidence_refs": []
}

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

FINAL_GATE=PASS_V2_37C_SHADOW_OBSERVATION_EVENT_CONTRACT_LOCAL_NOAPI
DECISION=V2_37C_LOCAL_SPEC_PASS_READY_FOR_NEXT_LOCAL_SUBTASK
NEXT=V2_37D_NOISE_ATTACK_DISCRIMINATION_LOCAL_REVIEW_NOAPI
