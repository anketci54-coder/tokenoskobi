# ERA53 HOT Ingress Topic Deduplication Policy Minimal Plan Review Seal NOAPI

- stage: `ERA53_HOT_INGRESS_TOPIC_DEDUPLICATION_POLICY_MINIMAL_PLAN_REVIEW_SEAL_NOAPI`
- generated_at_utc: `2026-07-08T15:36:00Z`
- decision: `OK_ERA53_HOT_INGRESS_TOPIC_DEDUPLICATION_POLICY_MINIMAL_PLAN_REVIEW_SEALED`
- next_step: `ERA53_HOT_INGRESS_EVIDENCE_POINTER_POLICY_MINIMAL_PLAN_NOAPI`

## Purpose

Group repeated HOT ingress events into deterministic topic waves without amplifying noise.

## Scope

After admission and normalization, before evidence binding.

## Core Rules

- same payload hash is duplicate
- same normalized topic key inside the window is same wave
- same transaction hash is same wave when present
- conflicting chain or asset prevents merge
- duplicate count alone cannot raise route
- same message flood does not increase trust score
- source count only counts distinct source UID

## Route Rule

- DROP events do not create wave
- QUARANTINE overrides WATCH and INFO
- CRITICAL_CANDIDATE remains candidate only
- merged wave cannot raise to critical alarm

## Hard Blocks

No DB write. No runtime queue. No outbound alarm. No wallet action. No Evidence binding in this step.

## Workflow Rule

Plan-only docs/contract used `PLAN -> REVIEW_SEAL`. Dryrun skipped because no executable system part changed.

## Tree Rule

Existing tree preserved. No directory restructure, move, rename, archive, or new top-level directory.

## Boundary

NOAPI. No live source connection. No DB/schema/runtime/systemd change. No wallet/signing. No paper/live trade. AI authority 0.
