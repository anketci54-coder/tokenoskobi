# NEWS V3 Candidate Intake Contract

## 1. Contract Identity

- Contract ID: `NEWS_V3_CANDIDATE_INTAKE_CONTRACT`
- Version: `1.0`
- Status: `LOCKED_EMPTY_INTAKE_QUEUE`
- Parent contract:
  `docs/contracts/NEWS_V3_BENCHMARK_CONTRACT.md`
- Collection plan:
  `docs/contracts/NEWS_V3_GOLDEN_DATASET_COLLECTION_AND_LABELING_PLAN.md`
- Candidate schema:
  `data/benchmarks/news/news_v3_candidate_intake_schema_v1.json`
- Candidate queue:
  `data/benchmarks/news/news_v3_candidate_intake_queue_v1.jsonl`
- Golden dataset:
  `data/benchmarks/news/news_v3_golden_dataset_v1.jsonl`
- ERA57 opened: false

This contract defines the isolated intake layer between external or
historical candidate discovery and the reviewed golden benchmark dataset.

Candidate intake is not golden-dataset acceptance.

## 2. Authority Boundary

This contract does not authorize:

- live source fetching
- network automation
- production database writes
- runtime mutation
- panel mutation
- service or timer mutation
- trade execution
- paper execution
- wallet activity
- signing
- order creation

Candidate records may be written only by a separately approved,
bounded benchmark-collection work unit.

## 3. Candidate Lifecycle

Allowed candidate states:

1. `QUEUED`
2. `EVIDENCE_CAPTURED`
3. `NORMALIZED`
4. `READY_FOR_LABELING`
5. `REJECTED`
6. `QUARANTINED`

A candidate cannot directly become an accepted golden record.

Promotion requires a separate labeling and review process governed by
`news_v3_labeling_policy_v1.json`.

## 4. Intake Requirements

Every candidate must identify:

- candidate UID
- collection task UID
- candidate status
- source UID
- source family UID
- source name
- source class
- source locator hash
- content hash
- title
- bounded excerpt
- normalized text
- language
- capture timestamp
- proposed narrative labels
- proposed adversarial labels
- proposed severity
- synthetic status
- evidence state
- collector notes

Proposed labels are hypotheses and are not ground truth.

## 5. Evidence Rules

`QUEUED` candidates may temporarily lack an evidence snapshot.

Candidates in any later positive processing state must have:

- evidence snapshot pointer
- canonical source locator hash
- content hash
- traceable source identity

Fabricated or unverifiable evidence requires `QUARANTINED`.

## 6. Source-Class Rules

Source classes must exist in:

`data/benchmarks/news/news_v3_source_class_registry_v1.json`

Unknown source classes are invalid.

Community or social claims cannot independently establish CRITICAL or
HIGH ground truth.

Synthetic candidates are permitted only when the associated collection
task explicitly allows synthetic records.

Synthetic candidates cannot establish real-incident ground truth.

## 7. Label Ambiguity Rule

`NONE` and `UNKNOWN` must never coexist in one candidate's proposed
adversarial labels.

Duplicate scenarios are divided into:

- reviewed non-adversarial duplicate cases using `NONE`
- uncertain or conflicting duplicate cases using `UNKNOWN`

The queue-level `Q017` ambiguity is therefore replaced by `Q017A` and
`Q017B`.

## 8. Duplicate and Cluster Hints

Candidate intake may carry preliminary:

- incident UID hint
- event-group UID hint
- content-cluster UID hint
- duplicate-candidate UID

These are provisional until the clustering and leakage audit is complete.

Split assignment at candidate-intake stage is prohibited.

## 9. Promotion Gate

A candidate may be promoted to labeling only when:

- candidate schema validation passes
- semantic validation passes
- source class is recognized
- collection task exists
- evidence requirements are satisfied
- synthetic rules are satisfied
- `NONE` and `UNKNOWN` do not coexist
- no fatal provenance violation exists

## 10. Current State

- Candidate intake contract: defined
- Candidate queue records: 0
- Golden dataset records: 0
- Live collection: not authorized
- Baseline benchmark: not run
- `NEWS_V3_FEATURE_COMPLETE`: NO
- `V3_NEWS_CLOSURE_APPROVAL`: BLOCKED
