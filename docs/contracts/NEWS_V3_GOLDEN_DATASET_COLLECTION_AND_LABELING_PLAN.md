# NEWS V3 Golden Dataset Collection and Labeling Plan

## 1. Identity

- Work unit: `NEWS_V3_GOLDEN_DATASET_COLLECTION_FOUNDATION`
- Target: `V3_NEWS_FEATURE_COMPLETE`
- Contract dependency:
  `docs/contracts/NEWS_V3_BENCHMARK_CONTRACT.md`
- Record schema:
  `data/benchmarks/news/news_v3_benchmark_schema_v1.json`
- Golden dataset:
  `data/benchmarks/news/news_v3_golden_dataset_v1.jsonl`
- Runtime authority: none
- Live-source authority: none
- Execution authority: none
- ERA57 opened: false

This plan governs the collection, evidence capture, normalization,
labeling, review and acceptance of NEWS V3 benchmark records.

It does not authorize automatic source fetching or production runtime
changes.

## 2. Collection Objective

The dataset must measure whether the NEWS engine can distinguish:

- real high-severity incidents
- ordinary crypto news
- false alarms
- misleading headlines
- fake announcements
- ambiguous entities
- duplicates
- stale information
- conflicting reports
- poisoned or malformed inputs

Attack-only datasets are prohibited.

## 2A. Candidate Intake Gate

All discovered records must first enter the isolated candidate-intake
layer defined by:

`docs/contracts/NEWS_V3_CANDIDATE_INTAKE_CONTRACT.md`

Candidate records are stored in:

`data/benchmarks/news/news_v3_candidate_intake_queue_v1.jsonl`

Candidate intake is not golden-dataset acceptance. Split assignment and
ground-truth promotion are prohibited until evidence, semantic validation,
labeling, review, clustering and leakage controls pass.

## 3. Collection Workflow

Every collection item moves through these states:

1. `QUEUED`
2. `EVIDENCE_CAPTURED`
3. `NORMALIZED`
4. `LABELED`
5. `REVIEW_REQUIRED`
6. `REVIEWED`
7. `ACCEPTED`
8. `REJECTED`
9. `QUARANTINED`

Only `ACCEPTED` records may enter the golden dataset.

Rejected or quarantined material must not silently re-enter the dataset.

## 4. Source-Class Coverage

Collection must cover multiple source classes:

- official security disclosure
- official project disclosure
- official exchange announcement
- regulator or court source
- blockchain-analysis source
- established news source
- specialist security research
- community or social claim
- synthetic adversarial stress input

No single source family may dominate the blind-test set.

Community or social claims cannot independently establish ground truth
for CRITICAL or HIGH events.

Synthetic records may be used only for adversarial-stress testing and
must be explicitly marked as synthetic.

## 5. Evidence Standard

Every accepted record must contain:

- traceable source identity
- canonical URL hash
- content hash
- evidence snapshot pointer
- ground-truth source list
- evidence pointer list
- collection timestamp
- reviewer count
- reviewer agreement

CRITICAL and HIGH records require at least two human reviewers.

A single reviewer is sufficient only for lower-severity records unless
the label is disputed.

Disagreement requires adjudication or `requires_human_review=true`.

Generated or nonexistent evidence pointers are fatal violations.

## 6. Content Policy

Full article text is not required.

Collection should prefer:

- title
- bounded excerpt
- normalized text
- hashes
- evidence snapshot pointer

Copyrighted full bodies must not be copied without explicit authorization.

## 7. Identity and Clustering

Before split assignment, records must be clustered by:

- canonical incident
- event group
- content similarity
- duplicate family
- source family

Split assignment before clustering is prohibited.

Rewritten, syndicated or translated copies of the same incident must
remain in the same protected split.

## 8. Labeling Rules

Narrative and adversarial labels are multi-label.

Severity is single-label.

Every assigned label requires:

- confidence
- evidence pointer
- reviewer agreement

`NONE` means reviewed evidence supports no adversarial condition.

`UNKNOWN` means evidence is insufficient or conflicting.

`NONE` and `UNKNOWN` must not coexist.

An empty label list is not equivalent to either value.

## 9. Initial Collection Strata

Initial queue targets are collection goals, not V3 closure thresholds.

Required strata include:

- smart-contract exploits
- bridge drains
- rug pulls and honeypots
- phishing and impersonation
- wallet compromise
- oracle manipulation
- liquidity manipulation
- MEV attacks
- social engineering
- fake announcements
- coordinated narrative manipulation
- normal informational news
- listings and delistings
- upgrades, funding and partnerships
- regulation and enforcement
- token unlocks
- ambiguous symbols and aliases
- duplicates and near-duplicates
- stale, conflicting and false timestamps
- malformed and poisoned stress inputs

Scenario quotas may overlap because one record may carry multiple labels.

## 10. Split Assignment

Allowed splits:

- TRAIN
- TUNING
- BLIND_TEST
- ADVERSARIAL_STRESS

Split assignment occurs only after:

- identity resolution
- cluster assignment
- duplicate analysis
- source-family assignment
- leakage audit

BLIND_TEST must contain chronologically newer records and at least one
withheld source family.

## 11. Acceptance Conditions

A record may be accepted only when:

- schema validation passes
- semantic validation passes
- evidence is traceable
- required reviewer count is met
- labels follow taxonomy
- cluster identifiers are assigned
- no protected-split leakage exists
- fatal violations are absent

## 12. Immediate Closure State

- Collection policy: defined
- Collection queue: initialized
- Golden dataset records: 0
- Baseline benchmark: not run
- Threshold lock: pending
- `NEWS_V3_FEATURE_COMPLETE`: NO
- `V3_NEWS_CLOSURE_APPROVAL`: BLOCKED
