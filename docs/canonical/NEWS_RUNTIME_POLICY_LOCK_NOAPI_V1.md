# NEWS Runtime Policy Lock NOAPI V1

Generated UTC: 2026-07-10T07:25:46.480526+00:00

Final Decision After Repair: OK_NEWS_RUNTIME_POLICY_LOCK_REPAIR_NOAPI

## Repair

Legacy runtime UID prefixes were added as controlled namespaces:

```text
news12_
news21_

These are not historical namespaces. They are classified as legacy_runtime.

Locked rule
raw_delta >= match_delta = signal_delta = score_delta >= 0

+2 is observation evidence only. It is not a fixed runtime threshold.

Code-as-policy artifacts
runtime/policies/news_runtime_policy_lock_v1.json
tools/news_runtime_policy_verifier_v1.py
Red lines
NEWS cannot emit trade authority.
NEWS cannot emit paper trade.
NEWS cannot emit live trade.
BAD flags route to HOLD.
Duplicate UID routes to HOLD.
Orphan derived rows route to HOLD.
UID namespace collision routes to HOLD.
Verifier is bounded-window only; default recent limit is 500.
Blind replay rule

Historical blind replay must seal input data first. Outcome labels/results are fetched only after input manifest sealing.

ERA60 backlog
event_hash column
quarantine table
conflict resolution table
Next

ERA60_SCHEMA_HARDENING_BACKLOG_PLAN_NOAPI
