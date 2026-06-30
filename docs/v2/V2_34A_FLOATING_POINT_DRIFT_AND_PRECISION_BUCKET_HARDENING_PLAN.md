# V2_34A Floating Point Drift And Precision Bucket Hardening Plan

MODE=PLAN_ONLY_NOAPI
HIZDAN_ODUN_YOK=true
SPEED_NEVER_DOWN=true
SECURITY_NEVER_DOWN=true
POWER_NEVER_DOWN=true

## Red Team Finding
Floating point drift and undefined rounding can break deterministic scoring at scale.

## Decision
Hot path must use fixed-point integer math.
Float is forbidden for final score and hot path scoring.
Decimal is allowed only for offline audit comparison, not for hot path.

## Precision Policy
scale_factor=1000000
raw_score_precision=6 decimals
internal_calc_precision=12 decimals
final_score_precision=4 decimals
bucket_size=0.0001
max_allowed_drift=0.0000 deterministic mode

## Speed Policy
per_candidate_latency_guard_future_max_ms=5
integer_math_required=true
decimal_hot_path_forbidden=true
float_hot_path_forbidden=true

## Fail Closed
Any drift, non-determinism, undefined rounding, hot-path float, hot-path Decimal, overflow, or latency >5ms in future dryrun must fail closed.

## Locks
PLAN_ONLY_NOAPI=true
NO_FORMULA_EXECUTION_NOW=true
NO_LATENCY_TEST_EXECUTION_NOW=true
NO_SUCCESS_CLAIM=true
NO_PROFITABILITY_CLAIM=true
NO_RUNTIME_SCORING_APPLY=true
NO_LIVE_DECISION=true
NO_LIVE_TRADE=true
NO_WALLET=true
NO_API_RPC=true
NO_DB_WRITE=true
NO_PANEL_WRITE=true
FLOAT_FOR_FINAL_SCORE_FORBIDDEN=true
FIXED_POINT_INTEGER_MATH_REQUIRED=true
DECIMAL_ALLOWED_ONLY_FOR_OFFLINE_AUDIT_NOT_HOT_PATH=true
PRECISION_BUCKETS_REQUIRED=true
ROUNDING_POLICY_REQUIRED=true
DRIFT_DETECTION_REQUIRED=true
ZERO_DRIFT_REQUIRED_IN_DETERMINISTIC_MODE=true
SPEED_NEVER_DOWN=true
SECURITY_NEVER_DOWN=true
POWER_NEVER_DOWN=true
FAIL_CLOSED_ON_DRIFT=true
FAIL_CLOSED_ON_NON_DETERMINISM=true
FAIL_CLOSED_ON_ROUNDING_POLICY_MISSING=true

## Final Truth
V2_34A does not execute formula dryrun.
V2_34A does not execute latency test.
V2_34A does not prove formula works.
V2_34A hardens the future V2_34 dryrun against floating point drift without sacrificing speed.

## Audit Required Truth Lines
HIZDAN_ODUN_YOK=true
SPEED_NEVER_DOWN=true
FIXED_POINT_INTEGER_MATH_REQUIRED=true
FLOAT_HOT_PATH_FORBIDDEN=true
DECIMAL_HOT_PATH_FORBIDDEN=true
per_candidate_latency_guard_future_max_ms=5
max_allowed_drift=0.0000 deterministic mode
Any drift, non-determinism, undefined rounding, hot-path float, hot-path Decimal, overflow, or latency >5ms in future dryrun must fail closed.
V2_34A does not execute formula dryrun.
V2_34A does not execute latency test.
V2_34A does not prove formula works.
