# NEWS Runtime Policy Lock NOAPI V1

Generated UTC: 2026-07-10T07:06:50.066446+00:00

Decision: FAIL_NEWS_RUNTIME_POLICY_LOCK_NOAPI

## Locked rule

```text
raw_delta >= match_delta = signal_delta = score_delta >= 0

+2 is accepted as observation evidence only. It is not a fixed runtime threshold.

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
UID namespace violation routes to HOLD/QUARANTINE.
Verifier is bounded-window only; default recent limit is 500.
ERA60 backlog
event_hash column
quarantine table
conflict resolution table
Next

NEWS_RUNTIME_POLICY_LOCK_HOLD
