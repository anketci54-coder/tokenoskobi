# Whale Event Identity and Economic Route Normalization Contract v1

CONTRACT_STATUS=SEALED_CANONICAL_DEFINITION
WORK_UNIT=WHALE_LARGE_VALUE_EVENT_AND_ECONOMIC_EVENT_IDENTITY_NORMALIZATION_CONTRACT

## 1. Purpose

This contract defines deterministic identity, linkage, deduplication, fragmentation, multi-hop route, and terminal-state ownership rules for Whale Economic Intelligence.

It does not create a new engine, script, schema, runtime binding, database writer, live fetch path, product-specific rule, token-specific rule, trade authority, or wallet authority.

## 2. Constitutional inheritance

This contract inherits and cannot weaken:

- NO_ESTIMATION=true
- MEASURE_BEFORE_DECIDE=true
- NO_ADDITION_WITHOUT_RETIREMENT=true
- INSUFFICIENT_EVIDENCE is not NO_SIGNIFICANT_IMPACT
- exactly one terminal state per assessment execution
- no single evidence source may determine the final decision
- decision and confidence are separate fields
- retirement requires proven replacement parity and constitutional compliance

## 3. Canonical object separation

### 3.1 Transfer Observation

A transfer observation is one source-reported movement record.

It is not automatically a Large Value Event, Economic Route Event, entity truth, intent truth, market-impact truth, or Whale decision.

### 3.2 Large Value Event

A Large Value Event is a normalized observation or bounded observation group that crosses an approved value, known-entity, anomaly, or economic-context admission gate.

Large Value Event means only that further analysis is justified.

### 3.3 Economic Route Event

An Economic Route Event is an evidence-supported grouping of one or more observations that represent one economically related movement path.

It may contain:

- one direct transfer,
- fragmented transfers,
- fan-in,
- fan-out,
- bridge ingress and egress,
- multi-hop routing,
- exchange deposit or withdrawal paths,
- treasury or custody movement paths,
- unresolved related observations.

Economic Route Event creation is an assessment result, not an ingest assumption.

### 3.4 Market Impact Assessment

Market impact belongs to the Economic Route Event assessment, not permanently to a wallet, entity, cluster, or label.

A wallet previously associated with NO_SIGNIFICANT_IMPACT remains eligible for future assessments.

## 4. Canonical identifiers

### 4.1 event_uid

`event_uid` identifies one normalized transfer observation.

Requirements:

- deterministic from canonical normalized fields,
- stable under replay of identical source evidence,
- different for materially different observations,
- source provenance retained separately,
- must not depend on database row ID, ingest order, wall-clock processing time, or random UUID generation.

Recommended identity inputs:

- chain,
- txid,
- transaction_index or log_index when available,
- source_wallet,
- destination_wallet,
- asset_uid,
- normalized amount,
- source event discriminator when required.

### 4.2 parent_event_uid

`parent_event_uid` links an observation to a directly preceding or enclosing observation when supported by evidence.

Rules:

- optional,
- cannot be self-referential,
- cannot create cycles,
- one parent link does not establish final economic-route truth,
- uncertainty must remain explicit.

### 4.3 route_uid

`route_uid` identifies an evidence-supported movement route across one or more observations.

Rules:

- created only after route-link evidence exists,
- deterministic from the ordered canonical route members and route version,
- must not double-count bridge ingress and egress as separate economic value,
- unresolved route membership cannot be silently forced,
- route changes create a new version or new route identity according to future versioning policy.

### 4.4 cluster_uid

`cluster_uid` identifies a bounded behavioral relationship candidate among wallets or observations.

Rules:

- cluster identity is evidence, not entity truth,
- static labels cannot create cluster truth alone,
- cluster membership must carry provenance, confidence, status, and validity time,
- conflicting cluster and entity evidence triggers LABEL_CONFLICT,
- cluster membership may remain UNRESOLVED.

### 4.5 economic_event_uid

`economic_event_uid` identifies one assessed Economic Route Event.

Rules:

- generated only after event-linkage assessment,
- deterministic from canonical member event identities, route identity when available, assessment version, and linkage policy version,
- must not be assigned at raw ingest,
- re-assessment must preserve lineage,
- materially changed membership creates a new assessment version or successor identity; it must not silently rewrite history.

## 5. Deduplication rules

Deduplication is separate from economic-event linkage.

### 5.1 Exact duplicate

Two observations are exact duplicates only when their canonical identity fields and source event discriminator resolve to the same event identity.

Action:

- retain one canonical observation,
- preserve all source provenance references,
- do not count value twice.

### 5.2 Near duplicate

Near-duplicate reports describe the same observation with non-material representation differences.

Action:

- link as duplicate candidates,
- require normalization evidence,
- do not merge when material fields conflict,
- conflicting material fields produce REVIEW_REQUIRED or INSUFFICIENT_EVIDENCE.

### 5.3 Related but not duplicate

Bridge legs, fan-in members, fan-out members, and fragmented transfers may be economically related but are not duplicates.

They retain distinct `event_uid` values and may share a `route_uid` or `economic_event_uid` only after evidence-supported linkage.

## 6. Fragmented transfer linkage

A set of individually small observations may become a Large Value Event candidate when evidence supports coordinated economic behavior.

Possible evidence categories include:

- common source funding,
- common destination,
- bounded temporal proximity,
- repeated amount pattern,
- shared route,
- shared cluster evidence,
- sequential nonce or transaction ordering,
- common bridge or exchange endpoint,
- historical behavior similarity.

Rules:

- no fixed history or time window is canonical in this contract,
- the window must be defined by measured policy later,
- one matching feature cannot determine linkage,
- fragmented aggregation must not double-count duplicate observations,
- unresolved aggregation remains REVIEW_REQUIRED or INSUFFICIENT_EVIDENCE,
- fragmented transfers cannot be promoted by value summation alone.

## 7. Multi-hop and bridge linkage

### 7.1 Route continuity

Route continuity requires evidence connecting ordered observations through wallet, transaction, bridge, asset-conversion, amount-conservation, timing, or protocol evidence.

### 7.2 Value conservation

The system must distinguish:

- transferred principal,
- fees,
- slippage,
- wrapped or bridged representation changes,
- partial fills or partial routes,
- unrelated coincident transfers.

The same principal must not be counted repeatedly across route hops.

### 7.3 Cross-chain identity

Cross-chain route linkage requires explicit chain and bridge provenance.

A bridge ingress and egress pair is not automatically one route when correlation evidence is insufficient.

### 7.4 Unresolved multi-hop state

When route continuity cannot be established after the bounded evidence cycle, the assessment must terminate as REVIEW_REQUIRED or INSUFFICIENT_EVIDENCE. It must not become NO_SIGNIFICANT_IMPACT by absence of proof.

## 8. Fan-in and fan-out linkage

Fan-in and fan-out are behavioral structures, not automatic entity truth.

Rules:

- fan-in may indicate aggregation, exchange deposit, custody, laundering, treasury consolidation, or unrelated coincidence,
- fan-out may indicate distribution, payments, internal rebalancing, laundering, airdrop, exploit dispersion, or unrelated coincidence,
- static labels do not resolve intent,
- behavior and known labels may conflict,
- label conflict is recorded as evidence,
- final resolution belongs to Evidence Synthesis.

## 9. Entity, behavior, history, and cluster conflict

The following inputs are independent evidence dimensions:

- entity labels,
- behavioral observations,
- known history,
- cluster linkage,
- economic context,
- liquidity or route depth,
- News and Technical cross-checks.

Rules:

- no dimension has unconditional precedence,
- no single source may break a tie,
- conflict cannot be converted into confidence by averaging alone,
- unresolved material conflict triggers LABEL_CONFLICT,
- LABEL_CONFLICT must result in REVIEW_REQUIRED or INSUFFICIENT_EVIDENCE unless synthesis produces sufficient independent resolution,
- confidence and decision remain separate.

## 10. Bounded reassessment

Each assessment may request bounded evidence expansion according to an approved future policy.

Rules:

- reassessment count must be finite,
- event ingestion must not be blocked while evidence is pending,
- this contract does not mandate queue, actor, coroutine, event bus, or database technology,
- timeout and evidence-arrival policies remain implementation-neutral,
- after the permitted reassessment cycle, exactly one terminal state is mandatory.

## 11. Terminal-state ownership

Terminal state belongs to one assessment execution identified by:

- economic_event_uid,
- assessment_version,
- policy_version.

Allowed terminal states:

- COMPLETED,
- REVIEW_REQUIRED,
- INSUFFICIENT_EVIDENCE,
- REJECTED.

Rules:

- exactly one terminal state per assessment execution,
- decision outcome is stored separately from terminal state,
- confidence is stored separately from both,
- a later reassessment creates a new assessment version; it does not overwrite the prior terminal result,
- terminal state cannot be assigned by source adapter, graph core, entity label, cluster label, or panel consumer,
- terminal-state authority belongs only to Evidence Synthesis under the approved decision contract.

## 12. Decision outcomes

Possible assessment outcomes may include:

- SIGNIFICANT_MARKET_IMPACT,
- NO_SIGNIFICANT_IMPACT,
- IMPACT_UNRESOLVED,
- ECONOMIC_ROUTE_CONFIRMED,
- ECONOMIC_ROUTE_UNRESOLVED,
- LABEL_CONFLICT,
- DUPLICATE_OBSERVATION,
- RELATED_ROUTE_MEMBER,
- REJECTED_INVALID_EVENT.

These outcomes are not wallet identities and must not permanently classify a wallet as Whale or Non-Whale.

## 13. History and retention boundary

This contract defines lineage requirements but does not authorize storage mutation or retention periods.

Locked status:

- HISTORY_RETENTION_POLICY=NOT_YET_DEFINED
- DATABASE_MUTATION=false
- COLD_STORAGE_POLICY=NOT_YET_DEFINED
- DELETION_POLICY=NOT_YET_DEFINED
- COMPRESSION_POLICY=NOT_YET_DEFINED

Any future storage policy requires separate measurement, Opportunity Cost evaluation, bounded approval, retention justification, and retirement or replacement analysis.

## 14. Reuse and no-duplication rules

- Existing `tools/runtime_whale_graph_v1.py` remains the first reuse candidate.
- Threshold logic must not be copied into a second engine.
- Known-wallet registry logic must not be duplicated.
- Existing Whale schema may be reused only after separate database-write authorization.
- Current fail-closed DATA_MISSING consumer remains until replacement parity is proven.
- No existing component is retired by this contract.
- No new permanent script is authorized.

## 15. Acceptance gates for future dry-run

A future bounded dry-run must prove at minimum:

1. deterministic event_uid generation,
2. exact-duplicate collapse without provenance loss,
3. related-but-not-duplicate preservation,
4. fragmented transfer candidate linkage without value-only promotion,
5. bridge principal counted once across hops,
6. unresolved route remains unresolved,
7. label conflict produces evidence and no forced precedence,
8. assessment terminates exactly once,
9. prior terminal result remains immutable under reassessment versioning,
10. existing graph core is reused without copied thresholds,
11. zero runtime, DB, panel, service, wallet, trade, and network mutation,
12. no product-specific or token-specific logic.

## 16. Hard bounds

NEW_ENGINE=false
NEW_SCRIPT=false
NEW_SCHEMA=false
RUNTIME_BINDING=false
DATABASE_MUTATION=false
PANEL_MUTATION=false
LIVE_FETCH=false
API_RPC=false
SERVICE_TIMER_CHANGE=false
PRODUCT_SPECIFIC_CODE=false
TOKEN_SPECIFIC_CODE=false
TRADE_AUTHORITY=false
WALLET_SIGNING_AUTHORITY=false
ERA57_OPENED=false
RETIREMENT_AUTHORIZED_COUNT=0

## 17. Completion state

CANONICAL_EVENT_IDENTITY_DEFINITION=SEALED
LARGE_VALUE_EVENT_DEFINITION=SEALED
ECONOMIC_ROUTE_EVENT_DEFINITION=SEALED
DEDUPLICATION_RULES=SEALED
FRAGMENTED_TRANSFER_LINKAGE_RULES=SEALED
MULTI_HOP_BRIDGE_LINKAGE_RULES=SEALED
LABEL_CONFLICT_RULES=SEALED
TERMINAL_STATE_OWNERSHIP=SEALED
IMPLEMENTATION_COMPLETE=false
RUNTIME_COMPLETE=false
LIVE_WHALE_INTELLIGENCE=false

NEXT_SAFE_STEP=WHALE_EVENT_IDENTITY_NORMALIZATION_EPHEMERAL_DRYRUN_TEST_DESIGN
HUMAN_APPROVAL_REQUIRED_FOR_NEXT_STEP=true
