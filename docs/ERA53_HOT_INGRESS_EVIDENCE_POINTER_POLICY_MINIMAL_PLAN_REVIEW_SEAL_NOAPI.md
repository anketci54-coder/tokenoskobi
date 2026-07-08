# ERA53 HOT Ingress Evidence Pointer Policy Minimal Plan Review Seal NOAPI

- stage: `ERA53_HOT_INGRESS_EVIDENCE_POINTER_POLICY_MINIMAL_PLAN_REVIEW_SEAL_NOAPI`
- generated_at_utc: `2026-07-08T15:45:00Z`
- decision: `OK_ERA53_HOT_INGRESS_EVIDENCE_POINTER_POLICY_MINIMAL_PLAN_REVIEW_SEALED`
- next_step: `ERA53_HOT_INGRESS_PROSECUTOR_HANDOFF_GATE_MINIMAL_PLAN_NOAPI`

## Purpose

Define how a normalized HOT ingress event or topic wave may carry evidence pointers without creating evidence records or runtime output.

## Scope

After normalization and topic deduplication, before evidence binding.

## Pointer Rule

- pointer is hash or reference only
- raw payload is not stored
- private material is not stored
- pointer UID is deterministic
- one event may have many pointers
- one topic wave may have many pointers
- pointer does not prove truth by itself
- pointer does not raise route by itself

## Hard Blocks

No evidence record. No DB write. No runtime queue. No outbound alarm. No trade or wallet action.

## Workflow Rule

Plan-only docs/contract used `PLAN -> REVIEW_SEAL`. Dryrun skipped because no executable system part changed.

## Tree Rule

Existing tree preserved. No directory restructure, move, rename, archive, or new top-level directory.

## Boundary

NOAPI. No live source connection. No DB/schema/runtime/systemd change. No wallet/signing. No paper/live trade. AI authority 0.
