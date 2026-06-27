# V2_45_TIME_DRIFT_SIGNAL_TTL_AND_SLIDING_WINDOW_PLAN_NOAPI

STAMP_UTC=2026-06-27T10:41:23Z
MODE=LOCAL_ONLY_NOAPI_NO_PUSH

## RESULT

FINAL_GATE=PASS_V2_45_TIME_DRIFT_SIGNAL_TTL_AND_SLIDING_WINDOW_PLAN_NOAPI
DECISION=V2_45_TIME_DRIFT_PLAN_PASS_READY_FOR_TIMESTAMP_TTL_CONTRACT
NEXT=V2_45A_SIGNAL_TIMESTAMP_AND_TTL_CONTRACT_LOCAL_NOAPI
GITHUB_PUSH=false

## PURPOSE

V2_45 plans GZ1 time-drift defense: signal TTL, sliding windows, race-condition guard, buffer-bloat guard and HG2 latency/false-positive budget.

## RED TEAM ADDITIONS LOCKED

TIERED_TTL_DECAY_REQUIRED=true
SHORT_CIRCUIT_WINDOW_CLEARANCE_REQUIRED=true
MATRIX_INTERSECT_OVER_TIME_REQUIRED=true

## TIMESTAMP CONTRACT

CONTRACT_NAME=signal_timestamp_contract_v1

### REQUIRED TIME FIELDS

- event_time
- observed_time
- ingest_time
- normalized_time
- expiry_time
- window_open_time
- window_close_time
- last_cross_check_time

### TIMESTAMP RULES

- event_time is the source event time when available.
- observed_time is the local observed time.
- ingest_time is when the signal enters the system.
- normalized_time is deterministic canonical time used for comparison.
- expiry_time is calculated by dynamic TTL.
- late events cannot rewrite already closed decisions.
- out-of-order events are review-only unless explicitly reconciled.
- missing or contradictory timestamps become TIME_POISON_SUSPECT or FAIL_CLOSED.

## TIERED TTL DECAY

- TTL1: WHALE_ECONOMIC_IMPACT_CONFIRMED | BASE_TTL_MINUTES=45 | DECAY_MODE=tiered_slow | MEMORY_PRIORITY=HIGH
- TTL2: WHALE_UNKNOWN_OR_REVIEW_REQUIRED | BASE_TTL_MINUTES=20 | DECAY_MODE=tiered_medium | MEMORY_PRIORITY=MEDIUM
- TTL3: LOW_LIQUIDITY_GHOST_MOVE | BASE_TTL_MINUTES=0 | DECAY_MODE=short_circuit_drop | MEMORY_PRIORITY=DROP
- TTL4: NEWS_EVENT_UNCONFIRMED | BASE_TTL_MINUTES=20 | DECAY_MODE=tiered_medium | MEMORY_PRIORITY=MEDIUM
- TTL5: NEWS_EVENT_CONFIRMED | BASE_TTL_MINUTES=35 | DECAY_MODE=tiered_slow | MEMORY_PRIORITY=HIGH
- TTL6: TECHNICAL_INDICATOR_SIGNAL | BASE_TTL_MINUTES=10 | DECAY_MODE=tiered_fast | MEMORY_PRIORITY=LOW
- TTL7: RISK_FAIL_CLOSED_HINT | BASE_TTL_MINUTES=60 | DECAY_MODE=tiered_slow | MEMORY_PRIORITY=CRITICAL
- TTL8: UNKNOWN_ANOMALY_SIGNAL | BASE_TTL_MINUTES=30 | DECAY_MODE=tiered_medium | MEMORY_PRIORITY=HIGH


## DECAY FORMULA

FORMULA=active_weight = signal_confidence * class_weight * time_decay_factor
DROP_RULE=if active_weight <= expiry_threshold then evict_or_stale
SHORT_CIRCUIT_RULE=hard-blocked classes are evicted immediately without waiting for window close
CONFIDENCE_FLOOR_REQUIRED=true
LATENCY_BUDGET_REQUIRED=true

## SLIDING WINDOW CONTRACT

CONTRACT_NAME=sliding_window_contract_v1
DEFAULT_POLICY=bounded_window_no_unbounded_wait
WINDOW_JOIN_RULE=signals may join only if time window and impact window intersect
LATE_JOIN_RULE=late signal can trigger REVIEW_REQUIRED but cannot rewrite prior fail-closed or rejection
CROSS_CHECK_MINIMUM=at least one valid cross-check path required before central escalation
SINGLE_SOURCE_ALARM_FORBIDDEN=true

## WINDOW CLASSES

- WIN1: WHALE_TO_ONCHAIN | MAX_MINUTES=45 | REQUIRES_IMPACT_INTERSECTION=true
- WIN2: WHALE_TO_RISK | MAX_MINUTES=45 | REQUIRES_IMPACT_INTERSECTION=true
- WIN3: WHALE_TO_TECHNICAL | MAX_MINUTES=20 | REQUIRES_IMPACT_INTERSECTION=true
- WIN4: WHALE_TO_NEWS | MAX_MINUTES=35 | REQUIRES_IMPACT_INTERSECTION=true
- WIN5: NEWS_TO_TECHNICAL | MAX_MINUTES=20 | REQUIRES_IMPACT_INTERSECTION=true
- WIN6: TECHNICAL_TO_RISK | MAX_MINUTES=10 | REQUIRES_IMPACT_INTERSECTION=true
- WIN7: UNKNOWN_ANOMALY_TO_EVIDENCE | MAX_MINUTES=30 | REQUIRES_IMPACT_INTERSECTION=false
- WIN8: FAIL_CLOSED_HINT_TO_ALL | MAX_MINUTES=60 | REQUIRES_IMPACT_INTERSECTION=false


## SHORT-CIRCUIT EVICTION RULES

- EV1: TRIGGER=LOW_LIQUIDITY_GHOST_MOVE | ACTION=EVICT_IMMEDIATELY | REASON=economic ghost move should not occupy window
- EV2: TRIGGER=FAKE_WHALE_SUSPECT_HIGH | ACTION=EVICT_OR_REVIEW_SUMMARY_ONLY | REASON=fake whale noise should not bloat queue
- EV3: TRIGGER=TTL_EXPIRED | ACTION=STALE_AND_EVICT | REASON=expired signal cannot keep cross-check alive
- EV4: TRIGGER=SINGLE_SOURCE_ONLY_AFTER_WINDOW | ACTION=WINDOW_MISS_AND_EVICT | REASON=single source alarm forbidden
- EV5: TRIGGER=BUFFER_LIMIT_EXCEEDED | ACTION=BUFFER_BLOAT_BLOCKED | REASON=latency and memory budget protection
- EV6: TRIGGER=TIME_POISON_SUSPECT | ACTION=FAIL_CLOSED_OR_REVIEW | REASON=timestamp manipulation risk
- EV7: TRIGGER=OUT_OF_ORDER_UNRECONCILED | ACTION=REVIEW_REQUIRED_NO_MERGE | REASON=prevent false causality
- EV8: TRIGGER=API_RPC_REQUIRED | ACTION=STOP_NOAPI_AND_EVICT | REASON=NOAPI hard boundary


## MATRIX INTERSECT OVER TIME

CONTRACT_NAME=matrix_intersect_over_time_v1
REQUIRED=true
RULE=Two signals are not correlated only because they arrive in sequence. Their market impact windows must intersect.
NON_CORRELATION_RULE=If whale move occurs but price/volume/liquidity impact does not overlap with later technical signal, mark TEMPORAL_INDEPENDENCE_REVIEW.
FAKE_CAUSALITY_GUARD=true
HG2_LATENCY_BUDGET_GUARD=true

### IMPACT WINDOW FIELDS

- price_delta_window
- volume_profile_delta_window
- liquidity_depth_delta_window
- spread_delta_window
- route_depth_delta_window

## TIME STATUSES

- TS1: FRESH | inside TTL and valid sliding window
- TS2: STALE | TTL expired
- TS3: DELAYED_REVIEW | late but potentially relevant; review only
- TS4: OUT_OF_ORDER | arrival order conflicts with event order
- TS5: WINDOW_MISS | cross-check window closed without valid merge
- TS6: TIME_POISON_SUSPECT | timestamp manipulation suspected
- TS7: BUFFER_BLOAT_BLOCKED | queue or memory budget exceeded
- TS8: TEMPORAL_INDEPENDENCE_REVIEW | arrival sequence exists but impact windows do not intersect
- TS9: FAIL_CLOSED | unsafe temporal ambiguity


## HARD BOUNDARIES

1. GZ1_TIME_DRIFT_ACTIVE=true
2. TIERED_TTL_DECAY_REQUIRED=true
3. DYNAMIC_TTL_REQUIRED=true
4. SLIDING_WINDOW_CONTRACT_REQUIRED=true
5. SHORT_CIRCUIT_WINDOW_CLEARANCE_REQUIRED=true
6. GARBAGE_COLLECTOR_EVICTION_REQUIRED=true
7. MATRIX_INTERSECT_OVER_TIME_REQUIRED=true
8. IMPACT_WINDOW_INTERSECTION_REQUIRED=true
9. BUFFER_BLOAT_GUARD_REQUIRED=true
10. LATENCY_BUDGET_REQUIRED=true
11. HG2_LATENCY_FALSE_POSITIVE_BUDGET_REQUIRED=true
12. SINGLE_SOURCE_ALARM_FORBIDDEN=true
13. HUB_AND_SPOKE_REQUIRED=true
14. API_RPC=false
15. LIVE_FEED=false
16. DB_WRITE=false
17. RUNTIME_APPLY=false
18. LIVE_TRADE=false
19. WALLET_ACCESS=false
20. PRIVATE_KEY_ACCESS=false
21. OUTBOUND_PACKET=false


## REQUIRED SUBSTEPS

V2_45A_SIGNAL_TIMESTAMP_AND_TTL_CONTRACT_LOCAL_NOAPI
V2_45B_SLIDING_WINDOW_BUFFER_BLOAT_AND_RACE_GUARD_LOCAL_NOAPI
V2_45_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI

## FORBIDDEN

REAL_DATA_EXECUTION=false
API_RPC=false
LIVE_FEED=false
DB_WRITE=false
PANEL_WRITE=false
RUNTIME_APPLY=false
SERVICE_RESTART=false
TIMER_CHANGE=false
LIVE_DECISION=false
LIVE_TRADE=false
WALLET_ACCESS=false
PRIVATE_KEY_ACCESS=false
AI_TOOL_EXECUTION=false
OUTBOUND_PACKET=false
GITHUB_PUSH=false

## PUSH POLICY

SUBTASK_PUSH=false
FINAL_CLOSE_PUSH=true
GITHUB_PUSH_ONLY_AT_VXX_FINAL_CLOSE=true
