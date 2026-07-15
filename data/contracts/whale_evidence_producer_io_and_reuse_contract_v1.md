# WHALE EVIDENCE PRODUCER IO AND REUSE CONTRACT V1

CONTRACT_STATUS=SEALED_DESIGN_ONLY
WORK_UNIT=WHALE_EVIDENCE_PRODUCER_INPUT_OUTPUT_CONTRACT_AND_EXISTING_COMPONENT_REUSE_DECISION

## 1. Purpose

This contract defines the bounded input, output, authority and reuse boundaries for the Whale Evidence Producer stage.

The Evidence Producer is not a final decision engine. Its sole role is to assemble a deterministic, provenance-preserving evidence package from already normalized and bounded upstream records.

This contract does not authorize executable implementation, runtime binding, database mutation, live fetch or trade-related action.

## 2. Canonical position

Canonical flow:

EVENT_IDENTITY
-> GRAPH_CORE
-> ENTITY_ATTRIBUTION_READMODEL
-> EVIDENCE_PRODUCER
-> RISK_LINK_PRODUCER

The Evidence Producer may consume upstream evidence. It must not replace or duplicate upstream responsibilities.

## 3. Producer role

EVIDENCE_PRODUCER_ROLE=EVIDENCE_PACKAGE_ASSEMBLY_ONLY

The Evidence Producer may only:

1. validate required evidence references,
2. preserve source provenance,
3. preserve staleness and conflict metadata,
4. group related evidence under one deterministic evidence package identity,
5. report missing, conflicting, stale or insufficient evidence conditions,
6. produce a bounded package for downstream Evidence Synthesis or Risk Link consumption.

It must not:

- classify a wallet as a definitive entity,
- infer intent,
- decide market impact,
- issue a risk decision,
- issue a terminal pipeline decision,
- create trade instructions,
- write orders,
- sign transactions,
- mutate runtime state.

## 4. Required input contract

A valid input must contain references equivalent to:

- `event_uid`
- `economic_event_uid` when available
- `route_uid` when available
- `cluster_uid` when available
- `graph_evidence`
- `entity_attribution_evidence`
- `behavior_evidence`
- `history_references`
- `source_provenance`
- `observed_at_utc`
- `schema_version`

Optional input may include:

- label conflict metadata,
- stale evidence metadata,
- unknown markers,
- fragmentation linkage,
- multi-hop linkage,
- source quality metadata,
- evidence availability state.

Missing required identity or provenance fields must fail closed.

## 5. Required output contract

A valid evidence package must contain fields equivalent to:

- `evidence_package_uid`
- `event_uid`
- `economic_event_uid`
- `route_uid`
- `cluster_uid`
- `evidence_items`
- `source_provenance`
- `conflict_flags`
- `staleness_flags`
- `missing_evidence_flags`
- `unknown_preserved`
- `evidence_count`
- `package_created_at_utc`
- `schema_version`

The package must also contain explicit non-decision fields:

- `entity_decision=null`
- `intent_inference=null`
- `market_impact_decision=null`
- `risk_decision=null`
- `terminal_state=null`
- `trade_instruction=null`

## 6. Deterministic identity rule

`evidence_package_uid` must be derived deterministically from canonical identity references and canonicalized evidence references.

The same canonical input must produce the same evidence package identity.

Ordering differences in equivalent evidence lists must not produce a different package identity after canonical sorting.

No random value, local clock value or process-specific identifier may participate in evidence package identity.

## 7. Evidence preservation rule

The producer must preserve evidence; it must not silently rewrite it.

- UNKNOWN must remain UNKNOWN.
- Conflicting labels must remain conflicting.
- Stale evidence must remain marked stale.
- Missing evidence must remain marked missing.
- Weak provenance must not be upgraded.
- Multiple evidence items must not be collapsed into one unsupported assertion.

INSUFFICIENT_EVIDENCE must never be converted into NO_SIGNIFICANT_IMPACT.

## 8. Evidence synthesis boundary

The Evidence Producer assembles evidence but does not synthesize a final conclusion.

EVIDENCE_ASSEMBLY=true
FINAL_EVIDENCE_SYNTHESIS_AUTHORITY=false

Any scoring, weighting, precedence, tie-break, impact or risk conclusion belongs to a separately authorized downstream contract.

No single evidence source may become a final decision through this producer.

## 9. Reuse decision

Canonical reuse decisions:

- EVENT_IDENTITY=REUSE_UNCHANGED
- GRAPH_CORE=REUSE_UNCHANGED
- ENTITY_ATTRIBUTION_READMODEL=REUSE_AS_EVIDENCE_INPUT_ONLY
- KNOWN_WALLET_REGISTRY=REFERENCE_ONLY
- HISTORY_REFERENCE=REFERENCE_ONLY
- GENERAL_PROVENANCE_CONTRACT=REUSE

The producer must not copy:

- graph traversal logic,
- whale threshold logic,
- known-wallet registry contents,
- entity attribution rules,
- event identity generation,
- route-linking logic,
- risk scoring logic,
- terminal-state logic.

## 10. No-duplication rule

- GRAPH_LOGIC_COPY=false
- THRESHOLD_LOGIC_COPY=false
- REGISTRY_COPY=false
- ENTITY_RULE_COPY=false
- EVENT_IDENTITY_COPY=false
- RISK_LOGIC_COPY=false
- TERMINAL_DECISION_LOGIC_COPY=false

If implementation requires copying any of these responsibilities, implementation must be rejected and redesigned.

## 11. Conflict handling

A conflict is evidence, not an error to erase.

The producer must preserve:

- static label versus behavioral evidence conflict,
- multiple registry label conflict,
- stale versus current evidence conflict,
- route identity conflict,
- cluster identity conflict,
- history inconsistency.

Conflict handling output may set `conflict_flags`, but must not break ties.

FORCED_TIE_BREAK=false
STATIC_ALWAYS_OVERRIDES_BEHAVIOR=false
BEHAVIOR_ALWAYS_OVERRIDES_STATIC=false

## 12. Missing evidence handling

Missing evidence must be represented explicitly.

Allowed package-level evidence availability states:

- `SUFFICIENT_FOR_DOWNSTREAM_REVIEW`
- `PARTIAL_EVIDENCE`
- `INSUFFICIENT_EVIDENCE`
- `REJECTED_INVALID_INPUT`

These are evidence availability states only. They are not final Whale, impact, risk or trade decisions.

## 13. Security and authority bounds

- TRADE_AUTHORITY=false
- WALLET_AUTHORITY=false
- SIGNING_AUTHORITY=false
- ORDER_CREATE_AUTHORITY=false
- LIVE_TRADE=false
- PAPER_TRADE=false
- ENTITY_DECISION_AUTHORITY=false
- INTENT_INFERENCE_AUTHORITY=false
- MARKET_IMPACT_DECISION_AUTHORITY=false
- RISK_DECISION_AUTHORITY=false
- TERMINAL_DECISION_AUTHORITY=false

## 14. Data and runtime bounds

- DATABASE_MUTATION_AUTHORIZED=false
- DATABASE_SCHEMA_CHANGE_AUTHORIZED=false
- RUNTIME_BINDING_AUTHORIZED=false
- LIVE_FETCH_AUTHORIZED=false
- NETWORK_ACCESS_AUTHORIZED=false
- PANEL_MUTATION_AUTHORIZED=false
- PRODUCTION_WRITE_AUTHORIZED=false

## 15. Generality rule

The Evidence Producer contract is asset-neutral, chain-neutral and product-neutral.

- PRODUCT_SPECIFIC_LOGIC=false
- TOKEN_SPECIFIC_LOGIC=false
- CHAIN_SPECIFIC_LOGIC=false
- VENDOR_SPECIFIC_LOGIC=false

Chain or asset values may exist only as data supplied through canonical inputs.

## 16. Validation requirements before implementation consideration

A future bounded ephemeral compatibility test must cover at least:

1. valid package assembly,
2. deterministic package UID,
3. evidence ordering invariance,
4. unknown preservation,
5. conflict preservation,
6. stale evidence preservation,
7. missing evidence preservation,
8. provenance preservation,
9. graph evidence reference,
10. entity evidence reference,
11. history evidence reference,
12. no forced tie-break,
13. no intent inference,
14. no market-impact decision,
15. no risk or terminal decision,
16. no copied upstream logic and repository immutability.

Required result:

- CASE_COUNT=16
- PASS_COUNT=16
- ERROR_COUNT=0
- WARNING_COUNT=0
- EVIDENCE_PACKAGE_ASSEMBLY_ONLY=true
- IMMUTABILITY=true

## 17. Opportunity Cost and implementation rule

Passing an ephemeral reference test will not automatically authorize permanent implementation.

Permanent implementation may be considered only after:

- real upstream data flow exists,
- a real downstream consumer exists,
- repeated operational demand is measured,
- an ephemeral bottleneck is measured,
- maintenance and complexity costs are measured,
- duplicate capability count remains zero,
- a retirement or replacement plan exists where constitutionally required,
- Opportunity Cost returns ACCEPT.

## 18. Retirement rule

No component is authorized for retirement by this contract.

RETIREMENT_AUTHORIZED_COUNT=0

The Graph Core, Event Identity contracts, Entity Attribution evidence boundary, registry and provenance contracts remain canonical.

## 19. Explicit non-authorizations

- PERMANENT_IMPLEMENTATION_AUTHORIZED=false
- NEW_ENGINE_AUTHORIZED=false
- NEW_SCRIPT_AUTHORIZED=false
- NEW_PRODUCER_CODE_AUTHORIZED=false
- EXISTING_COMPONENT_CHANGE_AUTHORIZED=false
- RUNTIME_BINDING_AUTHORIZED=false
- DATABASE_MUTATION_AUTHORIZED=false
- LIVE_FETCH_AUTHORIZED=false
- ERA57_OPENED=false

## 20. Next safe step

NEXT_SAFE_STEP=WHALE_EVIDENCE_PRODUCER_EPHEMERAL_COMPATIBILITY_TEST_DESIGN
