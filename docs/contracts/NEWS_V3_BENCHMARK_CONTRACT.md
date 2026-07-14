# NEWS V3 Benchmark Contract

## 1. Contract Identity

- Contract ID: `NEWS_V3_BENCHMARK_CONTRACT`
- Contract version: `1.0`
- Status: `LOCKED_DESIGN_BASELINE_PENDING`
- Target: `V3_NEWS_FEATURE_COMPLETE`
- Runtime authority: none
- Trade authority: zero
- Wallet authority: zero
- Signing authority: zero
- Order authority: zero
- ERA57 opened: false

This contract defines the minimum benchmark, evidence, safety and repeatability conditions required before the Tokenoskobi NEWS engine may be declared `V3_NEWS_FEATURE_COMPLETE`.

It does not authorize live source activation, runtime mutation, database mutation, service changes, timer changes, panel mutation or execution authority.

## 2. Canonical Files

- Contract:
  `docs/contracts/NEWS_V3_BENCHMARK_CONTRACT.md`
- Golden dataset record schema:
  `data/benchmarks/news/news_v3_benchmark_schema_v1.json`
- Dataset manifest:
  `data/benchmarks/news/news_v3_benchmark_manifest_v1.json`
- Golden dataset:
  `data/benchmarks/news/news_v3_golden_dataset_v1.jsonl`
- Latest valid run pointer:
  `reports/news_v3_benchmark_report_v1.json`
- Immutable run report:
  `reports/benchmarks/news/<run_uid>/benchmark_report.json`

Immutable benchmark run artifacts must never be edited after publication.

The latest pointer may be atomically replaced only after a completed report has passed schema, integrity and closure-decision validation.

## 3. Golden Dataset Scope

The dataset must contain both positive and negative examples:

- confirmed critical and high-severity attacks
- normal informational news
- misleading but non-malicious headlines
- fake official announcements
- duplicate and near-duplicate reports
- ambiguous symbols and entity collisions
- stale events
- false and future timestamps
- conflicting trusted sources
- poisoned or compromised sources
- social narrative manipulation
- low-trust social claims
- events requiring human review

A dataset consisting only of attacks is invalid.

## 4. Identity and Leakage Protection

Every record must explicitly contain:

- `record_uid`
- `event_uid`
- `canonical_incident_uid`
- `event_group_uid`
- `content_cluster_uid`
- `source_family_uid`

Records sharing any incident, event group, duplicate cluster or content cluster must not be split across training, tuning, blind-test or adversarial-stress partitions.

Rewritten versions of the same report must remain in the same split.

## 5. Content Storage Policy

Full article bodies are not mandatory.

Required bounded content fields:

- `title`
- `bounded_excerpt`
- `normalized_text`
- `canonical_url_hash`
- `content_hash`
- `evidence_snapshot_pointer`
- `body_available`

Full copyrighted content must not be copied into the dataset unless storage and use are explicitly lawful and authorized.

## 6. Labeling Contract

Narrative labels are multi-label.

Adversarial labels are multi-label.

Severity is single-label.

Every assigned label must contain:

- label name
- label confidence
- evidence pointer
- reviewer agreement

`NONE` means evidence supports the conclusion that no adversarial condition exists.

`UNKNOWN` means evidence is incomplete, conflicting or insufficient.

`NONE`, `UNKNOWN` and an empty label set are not equivalent.

`NONE` and `UNKNOWN` must not coexist in the same adversarial label set.

### Narrative Taxonomy

- LISTING
- DELISTING
- MAINNET
- UPGRADE
- PARTNERSHIP
- FUNDING
- TOKEN_UNLOCK
- REGULATION
- ENFORCEMENT
- MARKET_IMPACT
- NORMAL_INFORMATION
- UNKNOWN

### Adversarial Taxonomy

- SMART_CONTRACT_EXPLOIT
- BRIDGE_DRAIN
- RUG_PULL
- HONEYPOT
- PHISHING
- WALLET_COMPROMISE
- ORACLE_MANIPULATION
- LIQUIDITY_MANIPULATION
- MEV_ATTACK
- SOCIAL_ENGINEERING
- FAKE_ANNOUNCEMENT
- IMPERSONATION
- COORDINATED_NARRATIVE
- NONE
- UNKNOWN

### Severity Taxonomy

- CRITICAL
- HIGH
- MEDIUM
- LOW
- INFORMATIONAL
- UNKNOWN

## 7. Market Impact Boundary

Required fields:

- `expected_market_impact`
- `market_impact_horizon`

`expected_market_direction` is optional and is not a V3 NEWS security-closure blocker.

Market impact labels:

- POSITIVE
- NEGATIVE
- MIXED
- NEUTRAL
- UNCERTAIN

Market impact horizons:

- IMMEDIATE
- SHORT_TERM
- MEDIUM_TERM
- UNKNOWN

Long-term price-outcome validation belongs to Outcome Intelligence.

## 8. Dataset Splits

Allowed splits:

- TRAIN
- TUNING
- BLIND_TEST
- ADVERSARIAL_STRESS

Rules:

- Blind-test labels must be unavailable to the evaluated engine.
- Blind-test data must be chronologically newer than training and tuning data.
- At least one source family must be reserved for blind testing.
- Incident, event, duplicate and content clusters must not cross split boundaries.
- Leakage audit must pass before any benchmark result is valid.

## 9. Required Metrics

Every completed benchmark run must calculate:

- entity precision
- entity recall
- entity F1
- ambiguous-symbol error rate
- narrative macro precision
- narrative macro recall
- narrative macro F1
- adversarial precision
- adversarial recall
- adversarial F1
- critical recall
- high-severity recall
- high-severity false-negative rate
- false-positive rate
- duplicate precision
- duplicate recall
- provenance completeness
- confidence calibration error
- unauthorized authority violation count
- per-class metrics
- failed cases
- confusion matrix
- threshold results
- closure decision

## 10. Threshold Locking

The following thresholds remain `PENDING_BASELINE` until a valid baseline dataset and baseline engine report exist:

- minimum total dataset size
- minimum examples per critical class
- minimum blind-test size
- critical recall threshold
- high-severity recall threshold
- high-severity false-negative threshold
- entity matching threshold
- duplicate detection threshold
- confidence calibration threshold

The following values are already non-negotiable:

- provenance completeness: 100%
- unauthorized authority violations: 0
- blind-test leakage: 0
- consecutive successful benchmark runs required: 3

A pending threshold can never be interpreted as passed.

While any blocking threshold remains pending, `V3_NEWS_CLOSURE_APPROVAL` must remain `BLOCKED`.

## 11. Fatal Closure Blockers

Any single occurrence of the following blocks V3 NEWS closure regardless of aggregate metrics:

### UNAUTHORIZED_MUTATION

Any unauthorized:

- trade action
- paper execution
- wallet operation
- signature
- order creation
- runtime database mutation
- active panel mutation
- service or timer mutation

Authorized creation of isolated benchmark reports is not an unauthorized mutation.

### BLIND_TEST_LEAKAGE

Any incident, event, content, duplicate or rewritten-content leakage between protected splits.

### FAIL_CLOSED_VIOLATION

Continuing to publish trusted output after:

- source timeout
- malformed payload
- poisoned source
- failed authority check
- runner crash
- quarantine condition
- evidence validation failure

### PROVENANCE_LOSS

Any CRITICAL or HIGH signal without valid:

- source identity
- evidence pointer
- provenance chain
- traceable classification basis

### FABRICATED_EVIDENCE

Any generated, nonexistent or unverifiable evidence pointer.

## 12. Stability Requirement

V3 NEWS closure requires at least three consecutive successful benchmark runs:

- using the same locked engine version
- using the same locked dataset version
- performed at separate recorded run times
- with no fatal blocker
- with every locked blocking threshold passed

Selecting only the best run is prohibited.

## 13. V3 and V4 Boundary

V3 must include:

- bounded approved source intake
- approved source adapters
- dynamic identity matching
- fixed versioned taxonomy
- basic narrative classification
- basic adversarial classification
- evidence and provenance
- confidence scoring
- blind benchmark
- replay
- fail-closed behavior
- operational readmodel
- human review
- zero execution authority

V4 may include:

- autonomous research
- automatic discovery of new tactics
- unknown narrative clustering
- self-training
- automatic taxonomy evolution
- multi-model research synthesis
- long-term doctrine adaptation

V3 operational necessities must not be deferred to V4.

Open-ended autonomous intelligence must not be forced into V3.

## 14. Current Closure Decision

- Benchmark contract: defined
- Golden dataset: not populated
- Baseline: not executed
- Blocking thresholds: pending baseline
- Successful consecutive runs: 0
- `NEWS_V3_FEATURE_COMPLETE`: NO
- `V3_NEWS_CLOSURE_APPROVAL`: BLOCKED
