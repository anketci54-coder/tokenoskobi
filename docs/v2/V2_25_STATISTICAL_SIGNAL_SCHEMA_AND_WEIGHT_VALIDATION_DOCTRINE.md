# V2_25 Statistical Signal Schema And Weight Validation Doctrine

TASK=V2_25_STATISTICAL_SIGNAL_SCHEMA_AND_WEIGHT_VALIDATION_DOCTRINE_PLAN_NOAPI
MODE=PLAN_ONLY_NOAPI
STAMP_UTC=2026-06-26T06:27:14.397302+00:00
PARENT_HEAD=85c17f0e569882d75c0c249675980f401f96fb4d

## Red Team Decision

The old fixed scoring formula is rejected as a final scientific model.

V2_25 does not lock fixed weights.
V2_25 locks the scientific signal schema and the validation doctrine.

## Core Locks

NO_FIXED_WEIGHT_WITHOUT_BACKTEST=true
NO_SCIENTIFIC_CLAIM_WITHOUT_EVIDENCE=true
WEIGHTS_ARE_CANDIDATE_ONLY=true
HISTORICAL_CORRELATION_REQUIRED=true
NEWS_TO_MARKET_IMPACT_MEASUREMENT=true
EVENT_TYPE_PRIOR_REQUIRED=true
MARKET_REACTION_REQUIRED=true
ONCHAIN_CONFIRMATION_REQUIRED=true
REGIME_CONTEXT_REQUIRED=true
CONFIDENCE_INTERVAL_REQUIRED=true
OUTCOME_LEAKAGE_FORBIDDEN=true
MODEL_MUST_SCORE_BEFORE_OUTCOME=true
OUTCOME_REVEALED_AFTER_DECISION=true
REASONING_PATH_AUDIT_REQUIRED=true
AUTO_LEARNING_APPLY_FORBIDDEN=true
HUMAN_APPROVAL_REQUIRED_FOR_WEIGHT_CHANGE=true

## SignalVector

The system must produce a SignalVector before any final score claim.

Required signal classes:

- Event type
- Source type and source credibility
- Evidence level
- Freshness factor
- Independence factor
- Diversity score
- Market regime
- Price reaction windows
- Volume reaction windows
- Liquidity reaction windows
- Onchain confirmation
- Whale netflow
- Holder change
- Top holder pressure
- DEX / CEX / launchpad / airdrop / unlock context
- Risk flags
- Hard block flags

## Historical Correlation Doctrine

A news item is not intelligence by itself.

Historical intelligence requires:
- source timestamp
- event timestamp
- market regime
- price reaction
- volume reaction
- liquidity reaction
- onchain context
- whale context
- outcome window

## Blind Training Doctrine

Historical outcome is hidden until the model creates its blind decision.

Required sequence:
1. Build visible data up to historical event time.
2. Hide the actual outcome.
3. Produce SignalVector.
4. Produce candidate score / decision.
5. Freeze blind audit trace.
6. Reveal outcome.
7. Compare prediction against actual outcome.
8. Audit reasoning path.
9. Extract lesson.
10. Propose candidate weight or rule change only.
11. Human approval required before applying any change.

## Scientific Claim Doctrine

The system cannot claim scientific validity from a fixed hand-made score.

Scientific validity requires:
- sufficient historical sample
- blind validation
- repeatability
- precision / recall
- false positive / false negative analysis
- confidence interval
- outcome correlation
- reasoning path audit

## Final Statement

Tokenoskobi must not be a score-inventing system.
Tokenoskobi must be a hypothesis-producing and hypothesis-testing intelligence system.


## V2_25B Hot Path Speed Doctrine Patch

PATCH_TASK=V2_25B_HOT_PATH_SPEED_LOCK_PATCH_NOAPI
PATCH_STAMP_UTC=2026-06-26T06:37:53.964041+00:00

FAST_REACTION_PATH_REQUIRED=true
HEAVY_ANALYSIS_ASYNC_REQUIRED=true
HOT_PATH_MUST_NOT_WAIT_FOR_COLD_PATH=true
HOT_PATH_LATENCY_BUDGET_REQUIRED=true
COLD_PATH_CAN_ENRICH_AUDIT_LATER=true
HOT_PATH_FIRST_DECISION_ALLOWED=true
COLD_PATH_DEEP_ANALYSIS_BACKGROUND_ONLY=true
HOT_PATH_OUTPUT_MINIMAL_SIGNAL_VECTOR_REQUIRED=true
NETWORK_RPC_API_LATENCY_SEPARATED_FROM_CORE_DECISION_LATENCY=true

## Hot Path / Cold Path Boundary

Hot Path:
- minimal fast signal vector
- hard block flags
- first label: RED / IZLE / HOT_CANDIDATE
- no waiting for deep historical training
- no waiting for cold-path audit enrichment
- no waiting for slow external API/RPC enrichment

Cold Path:
- historical correlation
- blind training
- outcome reveal
- reasoning path audit
- confidence interval
- candidate weight validation
- audit enrichment

## Latency Budget

single_token_hot_path_ms_lt=50
batch_100_hot_path_ms_lt=1000
batch_1000_hot_path_ms_lt=5000
batch_10000_hot_path_ms_lt=45000
p99_token_hot_path_ms_lt=5

Note:
This latency budget covers local hot-path decision core only.
API, RPC, network, parsing, DB write and cold-path analysis must be measured separately.

## Speed Doctrine Final Lock

SPEED_NEVER_DOWN=true
HOT_PATH_MUST_NOT_WAIT_FOR_COLD_PATH=true
HEAVY_ANALYSIS_ASYNC_REQUIRED=true
