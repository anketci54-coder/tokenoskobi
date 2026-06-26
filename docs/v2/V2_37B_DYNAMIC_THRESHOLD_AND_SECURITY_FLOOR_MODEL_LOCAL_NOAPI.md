# V2_37B_DYNAMIC_THRESHOLD_AND_SECURITY_FLOOR_MODEL_LOCAL_NOAPI

STAMP_UTC=2026-06-26T14:56:24Z
MODE=LOCAL_ONLY_NOAPI_NO_PUSH

## PURPOSE

V2_37B defines dynamic thresholds without allowing the system to become paranoid or unsafe.

Thresholds may adapt to market regime, but security floor is immutable.

## CORE DOCTRINE

DYNAMIC_THRESHOLD_REQUIRED=true
SECURITY_FLOOR_IMMUTABLE=true
DYNAMIC_THRESHOLD_CANNOT_LOWER_SECURITY_FLOOR=true
VOLATILITY_REGIME_AWARE=true
LIQUIDITY_REGIME_AWARE=true
TIME_OF_DAY_NOISE_PROFILE=true
SOURCE_REPUTATION_WEIGHTED=true
FALSE_POSITIVE_OBESITY_GUARD_REQUIRED=true
NOISE_FIRST_CLASSIFICATION=true
NO_SINGLE_SIGNAL_MAY_DECLARE_ATTACK=true

## THRESHOLD MODEL

threshold_effective = max(dynamic_threshold, security_floor)

dynamic_threshold:
- may increase tolerance during high-noise regimes
- may reduce false positive pressure
- may adjust by time-of-day, liquidity, volatility, source reputation

security_floor:
- cannot be lowered by market noise
- cannot be lowered by source instability
- cannot be lowered by repeated provocation
- cannot be lowered by attacker-induced noise

## REGIME INPUTS

VOLATILITY_REGIME:
- low
- normal
- high
- extreme

LIQUIDITY_REGIME:
- thin
- normal
- deep
- unstable

TIME_OF_DAY_PROFILE:
- quiet
- active
- overlap
- illiquid_night

SOURCE_REPUTATION:
- trusted
- degraded
- unstable
- quarantined

## ANTI-PARANOIA RULES

NOISE_CAN_RAISE_OBSERVATION=false
NOISE_CAN_FORCE_ATTACK=false
SINGLE_SOURCE_DEGRADATION_ACTION=source_confidence_decay
SINGLE_SOURCE_DEGRADATION_ATTACK=false
REPEATED_NOISE_ACTION=shadow_watch
REPEATED_NOISE_ATTACK=false_without_correlation

## ATTACK ESCALATION REQUIREMENTS

ATTACK_SUSPECT_REQUIRES:
- confidence_score >= threshold_effective
- attack_similarity_score >= threshold_effective
- persistence=true
- correlation=true
- decision_impact=true

CONFIRMED_THREAT_REQUIRES:
- multi_source_evidence=true
- repeated_pattern=true
- decision_poisoning_potential=true
- prosecutor_evidence=true

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

FINAL_GATE=PASS_V2_37B_DYNAMIC_THRESHOLD_AND_SECURITY_FLOOR_MODEL_LOCAL_NOAPI
DECISION=V2_37B_LOCAL_SPEC_PASS_READY_FOR_NEXT_LOCAL_SUBTASK
NEXT=V2_37C_SHADOW_OBSERVATION_EVENT_CONTRACT_LOCAL_NOAPI
