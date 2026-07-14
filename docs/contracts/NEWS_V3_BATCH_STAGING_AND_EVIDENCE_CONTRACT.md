# NEWS V3 Batch Staging and Evidence Contract

## 1. Identity

- Contract ID: `NEWS_V3_BATCH_STAGING_AND_EVIDENCE_CONTRACT`
- Version: `1.0`
- Status: `LOCKED_EMPTY_BATCH_01`
- Batch: `batch_01`
- Candidate intake contract:
  `docs/contracts/NEWS_V3_CANDIDATE_INTAKE_CONTRACT.md`
- Canonical candidate queue:
  `data/benchmarks/news/news_v3_candidate_intake_queue_v1.jsonl`
- Staging candidate file:
  `data/benchmarks/news/batches/batch_01/candidates.jsonl`
- Batch manifest:
  `data/benchmarks/news/batches/batch_01/batch_manifest.json`
- Evidence directory:
  `data/benchmarks/news/batches/batch_01/evidence/`
- ERA57 opened: false

## 2. Authority Boundary

- Automated live fetch: false
- Runtime network access: false
- Manual historical source research: allowed
- Offline canonical ingestion: allowed only after full validation
- Runtime mutation: false
- Production database mutation: false
- Panel mutation: false
- Trade, paper, wallet, signing and order authority: false

## 3. Staging Rule

Historical candidates must first be written to the batch staging file.

Direct manual append to the canonical candidate queue is prohibited.

Promotion to the canonical queue requires:

- JSON Schema validation
- semantic validation
- evidence validation
- manifest validation
- duplicate UID validation
- content-hash validation
- evidence checksum validation
- atomic merge

## 4. Evidence Snapshot

Each non-queued candidate must reference a local evidence snapshot JSON.

The canonical pointer format is:

`batch://<batch_uid>/evidence/<filename>.json`

Relative filesystem pointers without a batch UID are prohibited because they
lose their meaning after promotion to the canonical candidate queue.

The candidate source fields represent the primary evidence source. Independent
corroborating evidence may and should use a different source UID, source family,
source class, locator and content hash.


Evidence snapshot records must contain:

- evidence UID
- candidate UID
- source UID
- source family UID
- source class
- canonical source locator
- canonical source locator hash
- title
- bounded excerpt
- published timestamp
- captured timestamp
- capture method
- content hash
- canonical payload checksum calculated without the `snapshot_checksum` field
- verification status
- source availability status
- reviewer notes

Full copyrighted article bodies are prohibited unless separately
authorized.

## 5. High and Critical Rule

HIGH and CRITICAL proposed candidates require:

- at least one primary or official source
- at least one independent corroborating source
- at least two evidence snapshot records
- the candidate pointer resolving to the primary evidence record

A single community post or news article is insufficient.

## 6. Batch-01 Role

Batch-01 is a smoke batch only.

It does not establish:

- production readiness
- baseline benchmark performance
- threshold satisfaction
- V3 NEWS closure

Initial target size: 5–10 candidates.

## 7. Atomic Merge

The merge tool must:

- validate staging again immediately before merge
- reject duplicate candidate UIDs
- reject duplicate candidate content hashes
- create a temporary output file
- fsync the temporary file
- atomically replace the canonical queue
- leave the staging batch unchanged
- emit a deterministic merge report

## 8. Current State

- Batch-01 staging records: 0
- Evidence snapshots: 0
- Canonical candidate records: 0
- Automated live fetch: false
- `V3_NEWS_CLOSURE_APPROVAL`: BLOCKED
- `ERA57_OPENED`: false
