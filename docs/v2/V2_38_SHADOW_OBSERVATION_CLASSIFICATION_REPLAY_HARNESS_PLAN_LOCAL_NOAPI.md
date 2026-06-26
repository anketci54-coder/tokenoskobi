# V2_38_SHADOW_OBSERVATION_CLASSIFICATION_REPLAY_HARNESS_PLAN_LOCAL_NOAPI

STAMP_UTC=2026-06-26T16:48:15Z
MODE=LOCAL_ONLY_NOAPI_NO_PUSH

## PURPOSE

V2_38 plans a local replay harness for shadow-observation classification.

This phase does not use live market data.

The purpose is to test whether the V2_37 semantic classifier behaves without paranoia before any real market feed is allowed.

## WHY REPLAY FIRST

Replay/synthetic events allow safe testing of:

- NOISE classification
- MARKET_DRIFT classification
- UNKNOWN_ANOMALY classification
- ATTACK_SUSPECT classification
- CONFIRMED_THREAT classification
- false positive pressure
- confidence threshold behavior
- security floor behavior
- source reputation behavior
- decision impact behavior

## HARNESS MODE

REPLAY_HARNESS_ONLY=true
SYNTHETIC_EVENTS_ALLOWED=true
REAL_MARKET_DATA_BLOCKED=true
LIVE_MARKET_DATA=false
API_RPC=false
RUNTIME_APPLY=false
DB_WRITE=false
PANEL_WRITE=false
LIVE_TRADE=false
GITHUB_PUSH=false

## INPUT EVENT CONTRACT

event_type=shadow_observation
classification_candidate=NOISE|MARKET_DRIFT|UNKNOWN_ANOMALY|ATTACK_SUSPECT|CONFIRMED_THREAT
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

## EXPECTED OUTPUT CONTRACT

classification_final=NOISE|MARKET_DRIFT|UNKNOWN_ANOMALY|ATTACK_SUSPECT|CONFIRMED_THREAT
action=log_only|confidence_decay|shadow_watch|prosecutor_candidate|decision_fail_closed|hard_block_candidate
reason_codes=array
anti_paranoia_guard_triggered=true|false
security_floor_applied=true|false
false_positive_pressure_score=0.00_to_1.00

## TEST CASE GROUPS

CASE_GROUP_NOISE:
- single source
- low confidence
- low attack similarity
- no persistence
- no correlation
- no decision impact
- expected classification: NOISE

CASE_GROUP_MARKET_DRIFT:
- volatility/liquidity/time profile compatible
- source reputation not quarantined
- low attack similarity
- expected classification: MARKET_DRIFT

CASE_GROUP_UNKNOWN_ANOMALY:
- unexplained abnormality
- attack similarity below threshold
- no decision impact
- expected classification: UNKNOWN_ANOMALY

CASE_GROUP_ATTACK_SUSPECT:
- confidence threshold met
- attack similarity threshold met
- persistence=true
- correlation=true
- decision_impact=true
- expected classification: ATTACK_SUSPECT

CASE_GROUP_CONFIRMED_THREAT:
- multi source evidence
- repeated pattern
- prosecutor evidence
- decision poisoning potential
- expected classification: CONFIRMED_THREAT

## NON-PARANOIA LOCKS

DEFAULT_ASSUMPTION=NOISE
NO_SINGLE_SIGNAL_MAY_DECLARE_ATTACK=true
CONFIDENCE_ALONE_CANNOT_DECLARE_ATTACK=true
ATTACK_SIMILARITY_ALONE_CANNOT_DECLARE_ATTACK=true
DECISION_IMPACT_REQUIRED_FOR_FAIL_CLOSED=true
CONFIRMED_THREAT_REQUIRES_EVIDENCE=true
FALSE_POSITIVE_OBESITY_GUARD_REQUIRED=true

## THRESHOLD LOCKS

DYNAMIC_THRESHOLD_REQUIRED=true
SECURITY_FLOOR_IMMUTABLE=true
DYNAMIC_THRESHOLD_CANNOT_LOWER_SECURITY_FLOOR=true
THRESHOLD_EFFECTIVE=max(dynamic_threshold,security_floor)

## PASS CRITERIA

PASS requires:

- NOISE case does not escalate
- MARKET_DRIFT case does not become attack
- UNKNOWN_ANOMALY does not become attack without correlation
- ATTACK_SUSPECT requires confidence + similarity + persistence + correlation + decision impact
- CONFIRMED_THREAT requires evidence
- no single signal declares attack
- no live data used
- no API/RPC used
- no DB write
- no runtime apply
- no GitHub push

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

FINAL_GATE=PASS_V2_38_SHADOW_OBSERVATION_CLASSIFICATION_REPLAY_HARNESS_PLAN_LOCAL_NOAPI
DECISION=V2_38_REPLAY_HARNESS_PLAN_LOCAL_PASS_READY_FOR_SYNTHETIC_EVENT_SET
NEXT=V2_38A_SYNTHETIC_EVENT_SET_AND_EXPECTED_CLASSIFICATION_LOCAL_NOAPI
