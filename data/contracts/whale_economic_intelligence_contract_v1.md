# Whale Economic Intelligence Contract v1

## Status

- `CONTRACT_STATUS=SEALED_CANONICAL_DEFINITION`
- `RUNTIME_BINDING=false`
- `DATABASE_MUTATION=false`
- `LIVE_FETCH=false`
- `NEW_ENGINE=false`
- `NEW_SCRIPT=false`
- `PRODUCT_SPECIFIC_CODE=false`
- `TOKEN_SPECIFIC_CODE=false`
- `ERA57_OPENED=false`

This contract defines the canonical meaning, evidence rules, terminal states, conflict handling, and retirement conditions for Whale Economic Intelligence. It does not authorize implementation, runtime binding, database writes, live data collection, panel mutation, trade authority, or wallet authority.

## Constitutional Foundations

The contract is governed by these permanent rules:

1. `NO_ESTIMATION=true`
2. `MEASURE_BEFORE_DECIDE=true`
3. `NO_ADDITION_WITHOUT_RETIREMENT=true`
4. `GENERAL_SOLUTION_OVER_SPECIAL_PATCH=true`
5. `HUMAN_FINAL_AUTHORITY=true`
6. `TRADE_AUTHORITY=false`
7. `WALLET_SIGNING_AUTHORITY=false`

## Canonical Mission

Whale Intelligence does not exist to declare that a wallet is a whale.

Its mission is:

> Explain economically meaningful large-value movement through verifiable evidence, entity context, behavior, history, route identity, liquidity context, and bounded market-impact assessment.

The runtime concept must remain event-centred, not identity-biased.

Preferred internal terminology:

- `LARGE_VALUE_EVENT`
- `ECONOMIC_ROUTE_EVENT`
- `ENTITY_ATTRIBUTION`
- `BEHAVIORAL_EVIDENCE`
- `HISTORY_EVIDENCE`
- `MARKET_IMPACT_ASSESSMENT`

The word `Whale` may remain as a user-facing product or panel name, but it must not create a runtime presumption.

## Canonical Definition

A qualifying Whale Economic Intelligence conclusion is:

> A bounded assessment of whether a verified or sufficiently evidenced entity, or related entity cluster, produced a movement capable of meaningful economic or market impact within a defined liquidity, route, timing, and evidence context.

Four dimensions are mandatory:

1. `ENTITY_CONTEXT`
2. `VALUE_CONTEXT`
3. `ROUTE_AND_TIME_CONTEXT`
4. `ECONOMIC_IMPACT_CONTEXT`

Absence of any mandatory dimension prevents a positive economic-impact conclusion.

## Event-Centred Rule

Decisions attach to an economic event, not permanently to a wallet.

A wallet previously associated with a low-impact internal transfer must not be permanently classified as non-impacting. A future event involving the same wallet must be assessed again using current evidence.

Forbidden permanent shortcut:

- `WALLET = NOT_REAL_WHALE`

Allowed event conclusions include:

- `SIGNIFICANT_ECONOMIC_IMPACT_SUPPORTED`
- `NO_SIGNIFICANT_IMPACT_SUPPORTED`
- `REVIEW_REQUIRED`
- `INSUFFICIENT_EVIDENCE`
- `REJECTED`

## Large Value Event and Economic Event Separation

A `LARGE_VALUE_EVENT` is only an intake observation that value crossed an approved threshold or aggregate condition.

It is not proof of:

- entity identity,
- intent,
- smart-money behavior,
- market impact,
- risk,
- sell pressure,
- buy pressure,
- or a real economic event.

An `ECONOMIC_ROUTE_EVENT` is an evidence-derived grouping of one or more related movements that may represent one economic action across wallets, routes, chains, bridges, exchanges, or time windows.

An economic event is a result of evidence synthesis. It must not be presumed at intake.

## Event Identity

The future normalized event contract must support these identities when evidence permits:

- `event_uid`
- `parent_event_uid`
- `route_uid`
- `cluster_uid`
- `economic_event_uid`

These identifiers exist to prevent:

- double counting bridge entry and exit,
- treating multi-hop movement as separate independent events,
- missing fragmented transfers,
- losing fan-in and fan-out relationships,
- confusing internal rebalance with market-facing movement.

Identity linkage must remain evidence-based. Missing linkage must remain explicit `UNKNOWN`.

## Fragmented and Multi-Hop Movement

A single-transfer threshold is an intake filter only.

The system must be able to represent a candidate economic event formed from multiple smaller transfers when supported by evidence such as:

- shared funder,
- shared destination,
- temporal proximity,
- route continuity,
- common cluster behavior,
- bridge continuity,
- fan-in or fan-out structure.

No fixed aggregation window is canonical in this version. Any future window must be measured and approved by policy.

Bridge input and output legs must not be counted twice when evidence shows they belong to one route event.

## Entity Attribution

Entity labels are evidence signals, not absolute truth.

Examples include:

- CEX
- custodian
- market maker
- bridge
- treasury
- foundation
- deployer
- insider cluster
- sniper
- MEV or arbitrage actor
- hacker
- unknown holder

Every entity assertion must retain:

- source,
- evidence level,
- confidence band,
- observed time,
- last validation time when available,
- and conflict status.

Entity state may become stale. Historical labels must never silently override newer contradictory evidence.

## Intent Handling

Intent is not a fact field.

Intent must be represented as an evidence-backed candidate with separate status:

- `CONFIRMED`
- `SUPPORTED`
- `UNRESOLVED`
- `CONFLICTED`

No unverified intent may be converted into deterministic truth.

Examples such as internal rebalance, OTC settlement, accumulation, distribution, treasury move, liquidity add/remove, attack, laundering, or unknown must remain evidence-derived.

## Label Conflict Rule

A conflict between entity label, cluster behavior, current behavior, and known history is itself evidence.

Canonical conflict state:

- `LABEL_CONFLICT`

A label conflict must trigger bounded review or evidence expansion. It must not be resolved by a permanent rule such as "behavior always wins" or "history always wins."

No single source may break a tie by itself.

## Evidence Synthesis Principle

No single evidence source may determine the final decision.

This includes:

- entity label,
- behavior,
- cluster relation,
- known history,
- news,
- technical signal,
- liquidity signal,
- exchange label,
- external vendor label.

Final conclusions must be produced only through evidence synthesis under an approved policy.

Vendor claims, labels, or marketing statements are claims, not proof.

## Economic Impact Principle

Economic impact must be assessed against relevant context such as:

- liquidity depth,
- route depth,
- market depth,
- destination type,
- time context,
- exchange inflow or outflow context,
- bridge continuity,
- fragmented-flow aggregation,
- and supporting evidence.

Large nominal value alone is insufficient.

A large internal rebalance may produce `NO_SIGNIFICANT_IMPACT_SUPPORTED` for that event while preserving the entity and its future relevance.

## Evidence Insufficiency Principle

`INSUFFICIENT_EVIDENCE` must never be interpreted as `NO_SIGNIFICANT_IMPACT_SUPPORTED`.

Missing evidence is not evidence of absence.

If bounded evidence expansion is exhausted and evidence remains insufficient, the pipeline must terminate with `INSUFFICIENT_EVIDENCE` or `REVIEW_REQUIRED` according to policy. It must not invent a safe or impact-free conclusion.

## Bounded Feedback Principle

Evidence reassessment must be bounded.

Canonical behavior:

1. Initial assessment.
2. Explicit evidence-gap declaration.
3. At most the policy-authorized bounded history or relation expansion.
4. Final assessment.

Unbounded cyclic reassessment is forbidden.

No canonical fixed history window is defined in this contract. Future windows must be measured by event type and approved separately.

## Non-Blocking Principle

Evidence waiting must not block unrelated event ingestion or processing.

This contract does not prescribe queue, coroutine, actor, event bus, thread, or process technology. Implementation choice remains deferred until measured need exists.

A delayed evidence dependency must yield an explicit pending or terminal state according to policy; it must not create deadlock.

## Terminal State Principle

Every pipeline execution must terminate in exactly one terminal state.

Canonical terminal states:

- `COMPLETED`
- `REVIEW_REQUIRED`
- `INSUFFICIENT_EVIDENCE`
- `REJECTED`

Exactly one terminal state is allowed per execution.

Mutually incompatible final conclusions must never coexist for the same execution.

Examples of forbidden combinations:

- `COMPLETED + REVIEW_REQUIRED`
- `NO_SIGNIFICANT_IMPACT_SUPPORTED + INSUFFICIENT_EVIDENCE`
- `SIGNIFICANT_ECONOMIC_IMPACT_SUPPORTED + REJECTED`

Decision and confidence must remain separate fields.

Example:

- `decision=SIGNIFICANT_ECONOMIC_IMPACT_SUPPORTED`
- `confidence_band=HIGH`

Confidence must not be embedded into the decision label.

## History Principle

Historical behavior is evidence, not permanent guilt or permanent trust.

History may influence evidence synthesis but must not independently determine a current decision.

Storage engine, retention duration, compression, archival, and deletion policy are not defined in this contract.

Canonical state:

- `HISTORY_RETENTION_POLICY=NOT_YET_DEFINED`
- `HISTORY_STORAGE_DECISION=DEFERRED`

Any future storage or retention decision requires a separate bounded design, data-minimization review, mutation approval, and retirement plan.

## Runtime and Data Authority Boundaries

This contract grants no authority for:

- live API or RPC access,
- runtime binding,
- database mutation,
- panel mutation,
- service or timer changes,
- trade execution,
- order creation,
- wallet access,
- key or signature access,
- autonomous risk override.

All such actions require separate explicit authorization.

## Retirement and Replacement Principle

A component may be retired only after the replacement proves:

1. Functional parity for every owned responsibility.
2. Contract compliance.
3. Fail-closed parity.
4. Deterministic dry-run success.
5. Relevant benchmark success.
6. Approved runtime evidence where runtime replacement is involved.
7. Consumer migration completion.
8. Rollback or recovery evidence.
9. Opportunity Cost `ACCEPT` when the Opportunity Cost Meta-Engine is canonically available.
10. No degradation of speed, power, security, or economy beyond the approved measured trade-off.

A dry-run alone is insufficient for retirement.

A smoke test alone is insufficient for retirement.

No placeholder, legacy reader, registry, or producer may be removed immediately merely because a new design exists.

Current state:

- `PROVEN_DUPLICATE_COMPONENT_COUNT=0`
- `RETIREMENT_AUTHORIZED_COUNT=0`

## No Addition Without Retirement

The rule does not mean immediate deletion.

It means every future accepted component must identify:

- the responsibility it replaces or consolidates,
- the component that becomes a retirement candidate,
- the evidence required before retirement,
- and the complexity debt it removes.

If no retirement or consolidation path exists, the addition must justify why total architecture complexity does not increase or must be rejected/deferred.

## Fail-Closed Rules

The system must preserve these outcomes:

- Unknown remains unknown.
- Missing data is not zero activity.
- Missing evidence is not safety.
- A CEX label is not an individual whale conclusion.
- A large transfer is not market impact.
- A known wallet is not proof of intent.
- A cluster is not proof of common control without evidence.
- News and technical signals are cross-checks, not authority.
- Whale Intelligence never grants trade authority.

## Canonical Pipeline

The canonical logical order is:

```text
LARGE_VALUE_EVENT
→ EVENT_IDENTITY_AND_ROUTE_LINKAGE
→ EVIDENCE_COLLECTION
→ ENTITY_ATTRIBUTION
→ BEHAVIORAL_EVIDENCE
→ HISTORY_EVIDENCE
→ ECONOMIC_CONTEXT
→ ECONOMIC_ROUTE_EVENT
→ MARKET_IMPACT_ASSESSMENT
→ EVIDENCE_SYNTHESIS
→ EXACTLY_ONE_TERMINAL_STATE
```

A bounded evidence-gap expansion may occur once or as separately authorized by policy, but the execution must terminate.

## Implementation State

- `CANONICAL_DEFINITION_COMPLETE=true`
- `CONTRACT_SEALED=true`
- `EVENT_IDENTITY_SCHEMA_COMPLETE=false`
- `NORMALIZATION_IMPLEMENTED=false`
- `EVIDENCE_PIPELINE_IMPLEMENTED=false`
- `RUNTIME_BINDING=false`
- `DATABASE_MUTATION=false`
- `LIVE_WHALE_INTELLIGENCE=false`

## Next Safe Step

`WHALE_LARGE_VALUE_EVENT_AND_ECONOMIC_EVENT_IDENTITY_NORMALIZATION_CONTRACT`

The next step may define event identity and normalization only. It must not authorize executable code, database mutation, live fetch, runtime binding, or product-specific logic.
