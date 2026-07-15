# GENERAL RUNTIME HARNESS GENERIC EPHEMERAL CASE INTERFACE CONTRACT V1

CONTRACT_STATUS=SEALED_DESIGN_ONLY
WORK_UNIT=GENERAL_RUNTIME_HARNESS_GENERIC_EPHEMERAL_CASE_INTERFACE_CONTRACT_AND_COMPATIBILITY_PLAN

## 1. Purpose

This contract defines a generic, deterministic, process-local case interface for the existing `tests/general_runtime_stress_harness_v1.py` capability.

The purpose is to reuse the existing isolation, temporary-path, cleanup, production-hash, pass/fail aggregation and mutation-detection boundaries without creating a second harness or a Whale-specific harness.

This contract does not authorize executable changes.

## 2. Canonical reuse decision

- EXISTING_GENERAL_RUNTIME_HARNESS=REUSE
- NEW_STANDALONE_HARNESS=false
- NEW_WHALE_SPECIFIC_HARNESS=false
- SECOND_GENERAL_NORMALIZER=false
- PERMANENT_THIN_ADAPTER=false
- CORE_CHANGE=false

## 3. Required interface role

The generic ephemeral case interface may only:

1. accept a deterministic case specification,
2. execute the case inside the harness-owned temporary isolation boundary,
3. return a structured result,
4. participate in the existing immutability and cleanup gates,
5. remain domain-neutral.

It must not become a normalizer, inference engine, decision engine, runtime worker, producer, consumer or persistence layer.

## 4. Generic case specification

A case specification must contain only generic fields equivalent to:

- `case_id`
- `case_version`
- `fixture`
- `executor_reference`
- `expected_result`
- `required_invariants`
- `forbidden_effects`
- `timeout_policy`

No field may contain:

- private keys,
- seed phrases,
- wallet signatures,
- provider secrets,
- order instructions,
- trade instructions,
- runtime commands,
- live-fetch authorization.

## 5. Generic executor boundary

The harness may invoke only an explicitly supplied process-local callable or bounded ephemeral command approved for the current test decision.

The interface must not:

- discover arbitrary executables,
- import arbitrary network code,
- install packages,
- write into the repository,
- mutate the production database,
- bind to runtime services,
- activate timers,
- publish panel state.

## 6. Structured result contract

Each case must produce a result equivalent to:

- `case_id`
- `status`
- `passed`
- `observed`
- `expected`
- `error_count`
- `warning_count`
- `elapsed_ms`
- `repository_write`
- `database_mutation`
- `runtime_mutation`
- `network_access`
- `cleanup_complete`

Allowed terminal statuses:

- `PASS`
- `FAIL`
- `REJECTED`
- `TIMEOUT`

Exactly one terminal status is required for every case.

## 7. Mandatory invariants

The existing harness guarantees must remain authoritative:

- temporary-root allowlist,
- production-path denial,
- production database hash before/after equality,
- cleanup of temporary files,
- deterministic scenario aggregation,
- fail-closed behavior,
- no silent mutation.

The generic interface must not copy or replace these protections.

## 8. Domain-neutrality rule

The interface must not contain Whale-specific, News-specific, token-specific, chain-specific, panel-specific or product-specific logic.

Domain-specific fixtures may be supplied by an authorized ephemeral execution decision, but the harness interface itself must remain general.

## 9. No-duplication rule

The interface must reuse the existing harness functions and lifecycle wherever possible.

It must not duplicate:

- temporary directory guards,
- source hash functions,
- cleanup logic,
- result aggregation,
- mutation checks,
- timeout handling,
- duplicate replay protection,
- production runtime guards.

If implementation would require copying these capabilities, implementation must be rejected and redesigned.

## 10. Compatibility plan

Compatibility must be assessed in this order:

1. Can the existing harness accept a generic case through its current `run_scenario` lifecycle without structural change?
2. Can a minimal general interface be added without changing existing scenario semantics?
3. Can the interface preserve all current stress scenarios unchanged?
4. Can the interface run deterministic ephemeral cases without repository or production mutation?
5. Can Whale event-identity fixtures be supplied externally without embedding Whale logic in the harness?

No implementation is authorized until all five questions have evidence-backed answers.

## 11. Required compatibility tests

A future bounded ephemeral compatibility test must cover at least:

- existing scenario regression unchanged,
- deterministic generic case execution,
- one terminal status per case,
- timeout termination,
- forbidden-effect rejection,
- repository immutability,
- production database immutability,
- temporary cleanup,
- no network access,
- external fixture acceptance,
- domain-neutral harness source,
- no copied isolation or hash logic.

## 12. Acceptance gate

A future implementation decision may be considered only if:

- all existing harness scenarios remain PASS,
- all generic interface compatibility cases remain PASS,
- error_count=0,
- warning_count=0,
- repository mutation during execution=false,
- production database mutation=false,
- runtime mutation=false,
- network access=false,
- duplicate harness capability count=0.

## 13. Retirement rule

No component is authorized for retirement by this contract.

- RETIREMENT_AUTHORIZED_COUNT=0

The existing harness remains canonical until a replacement proves full functional equivalence, constitutional compliance and Opportunity Cost ACCEPT.

## 14. Explicit non-authorizations

- IMPLEMENTATION_AUTHORIZED=false
- NEW_SCRIPT_AUTHORIZED=false
- EXISTING_HARNESS_CHANGE_AUTHORIZED=false
- RUNTIME_BINDING_AUTHORIZED=false
- DATABASE_MUTATION_AUTHORIZED=false
- LIVE_FETCH_AUTHORIZED=false
- PANEL_MUTATION_AUTHORIZED=false
- ERA57_OPENED=false

## 15. Next safe step

NEXT_SAFE_STEP=GENERAL_RUNTIME_HARNESS_GENERIC_EPHEMERAL_CASE_INTERFACE_COMPATIBILITY_TEST_DESIGN
