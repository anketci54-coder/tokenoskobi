# Maintenance AI Control Center Contract v1

Phase: PHASE32A_MAINTENANCE_AI_CONTROL_CENTER_PLAN_NOAPI

## Mission
Build a maintenance control plane that preserves Fast Path speed while enabling safe AI-assisted planning, audit, proposal, approval, apply and rollback workflows.

## Absolute rule
Fast Path must not wait for AI, maintenance bundle generation, proposal validation, report generation, or external model calls.

## Authority model
- ai_authority: proposal_only
- human_authority: explicit_approval_required_for_apply
- runner_authority: read_only_fast_path_runtime
- db_authority: guarded_migration_only_after_explicit_approval
- live_trade_authority: locked_off_until_future_micro_live_readiness_and_explicit_approval

## Components
### State Capsule Reader
- Purpose: Read current system position from /state without relying on chat memory.
- Writes live: False
- Fast Path dependency: none
- Output: normalized current state summary

### Maintenance Bundle Generator
- Purpose: Collect safe system context, recent phase reports, checks, hashes, errors and next action into a redacted bundle.
- Writes live: False
- Fast Path dependency: none
- Output: maintenance_context_bundle_runtime.json

### AI Proposal Contract
- Purpose: Allow AI to produce proposed actions only as structured plans with forbidden-action flags and rollback requirements.
- Writes live: False
- Fast Path dependency: none
- Output: ai_proposal_candidate.json

### Proposal Validator
- Purpose: Reject proposals that touch forbidden areas, weaken hard blocks, modify Fast Path incorrectly, or lack rollback.
- Writes live: False
- Fast Path dependency: none
- Output: proposal_validation_result.json

### Approval Queue
- Purpose: Hold validated proposals until explicit approval phrase is provided.
- Writes live: False
- Fast Path dependency: none
- Output: pending_approval_queue.jsonl

### Apply Executor Boundary
- Purpose: Define future executor boundaries; no executor implementation in Phase32A.
- Writes live: False
- Fast Path dependency: none
- Output: apply_boundary_contract.md

### Rollback Registry
- Purpose: Require every future real apply to register backup path, rollback script and post-audit gate.
- Writes live: False
- Fast Path dependency: none
- Output: rollback_registry_contract.json

### Component Version Registry
- Purpose: Track DB schema, runner, panel, timer, services, state capsule and adapters by sha/version.
- Writes live: False
- Fast Path dependency: none
- Output: component_version_registry_contract.json

## Forbidden in Phase32A
- no live DB schema apply
- no service/timer restart
- no runner patch
- no active panel write
- no local AI install
- no external network/API call
- no paper/live trade
- no wallet connection
- no transaction signing

## Phase32 sequence
- PHASE32A_MAINTENANCE_AI_CONTROL_CENTER_PLAN_NOAPI
- PHASE32B_MAINTENANCE_STATE_READER_AND_BUNDLE_CONTRACT_NOAPI
- PHASE32C_AI_PROPOSAL_SCHEMA_AND_VALIDATOR_CONTRACT_NOAPI
- PHASE32D_APPROVAL_QUEUE_AND_ROLLBACK_REGISTRY_PLAN_NOAPI
- PHASE32E_CONTROL_CENTER_TEMPDB_DRYRUN_NOAPI
- PHASE32F_CONTROL_CENTER_FILE_DRYRUN_NOAPI
- PHASE32G_CONTROL_CENTER_REAL_APPLY_AFTER_EXPLICIT_APPROVAL
- PHASE32H_CONTROL_CENTER_POST_AUDIT_NOAPI

## Exit criteria
- state_capsule_readable: True
- maintenance_components_defined: True
- ai_authority_limited_to_proposal: True
- approval_required_for_apply: True
- rollback_required_for_apply: True
- fast_path_not_slowed: True
- next_phase_opened: PHASE32B_MAINTENANCE_STATE_READER_AND_BUNDLE_CONTRACT_NOAPI
