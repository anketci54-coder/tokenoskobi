# WHALE_THIN_GENERAL_EVENT_IDENTITY_ADAPTER_CONTRACT_V1

CONTRACT_STATUS=SEALED_DESIGN_ONLY
WORK_UNIT=WHALE_THIN_GENERAL_EVENT_IDENTITY_ADAPTER_CONTRACT_AND_NO_DUPLICATION_DESIGN

## 1. Purpose

Define one thin, general, reusable adapter boundary between approved read-only normalized flow inputs and the existing `tools/runtime_whale_graph_v1.py` core.

The adapter exists only to provide canonical event identity, relation metadata, normalization, and bounded core input translation. It is not a second Whale engine, not a decision engine, not a database writer, and not a runtime service.

## 2. Constitutional gates

- NO_ESTIMATION=true
- MEASURE_BEFORE_DECIDE=true
- GENERAL_SOLUTION_OVER_SPECIAL_PATCH=true
- NO_ADDITION_WITHOUT_RETIREMENT=true
- NO_SINGLE_EVIDENCE_SOURCE_MAY_DECIDE=true
- EXACTLY_ONE_TERMINAL_STATE=true
- INSUFFICIENT_EVIDENCE_IS_NOT_NO_SIGNIFICANT_IMPACT=true

## 3. Hard bounds

- NEW_ENGINE=false
- ADAPTER_CODE_AUTHORIZED=false
- NEW_PERMANENT_SCRIPT=false
- CORE_CODE_CHANGE=false
- CORE_INTERFACE_CHANGE=false
- THRESHOLD_LOGIC_COPY=false
- WALLET_REGISTRY_COPY=false
- GRAPH_LOGIC_COPY=false
- PROBABILITY_LOGIC_COPY=false
- TERMINAL_DECISION_AUTHORITY=false
- ENTITY_TRUTH_AUTHORITY=false
- ECONOMIC_IMPACT_AUTHORITY=false
- RUNTIME_BINDING=false
- DATABASE_WRITE=false
- SCHEMA_MUTATION=false
- PANEL_MUTATION=false
- LIVE_FETCH=false
- API_RPC=false
- PRODUCT_SPECIFIC_CODE=false
- TOKEN_SPECIFIC_CODE=false
- WALLET_SIGNING_AUTHORITY=false
- TRADE_ORDER_AUTHORITY=false
- ERA57_OPENED=false

## 4. Single responsibility

The adapter may perform only these functions:

1. Validate approved read-only source payload shape.
2. Normalize field names and primitive value types.
3. Preserve explicit UNKNOWN values.
4. Produce deterministic `event_uid`.
5. Carry or derive bounded relation identifiers when evidence supports them:
   - `parent_event_uid`
   - `route_uid`
   - `cluster_uid`
   - `economic_event_uid`
6. Classify event relations without making market-impact or entity-truth decisions:
   - `EXACT_DUPLICATE`
   - `NEAR_DUPLICATE`
   - `RELATED_NOT_DUPLICATE`
   - `UNRELATED`
7. Mark candidate linkage evidence for:
   - fragmented transfers
   - fan-in
   - fan-out
   - multi-hop bridge routes
8. Translate one validated normalized event into the existing core input fields:
   - `txid`
   - `src`
   - `dst`
   - `btc_eq`
   - `gas_btc_eq`
   - `depth`
   - `ts_mono_ns`
9. Preserve provenance and adapter decision evidence outside the core input object.

## 5. Forbidden responsibilities

The adapter must never:

- decide `REAL_WHALE`, `NO_SIGNIFICANT_IMPACT`, or any terminal state;
- assign final entity identity;
- infer intent as fact;
- calculate or replace core thresholds;
- maintain a second wallet-label registry;
- traverse or implement a second graph;
- calculate the core probability score independently;
- suppress UNKNOWN values by converting them to zero or safe;
- write to database, runtime state, panel state, files, queues, services, or network;
- issue trade, order, wallet-signing, or runtime commands.

## 6. Input contract

Required normalized input fields:

- `chain`
- `txid`
- `transaction_index`
- `source_wallet`
- `destination_wallet`
- `asset_uid`
- `amount_native`
- `amount_usd`
- `btc_equivalent`
- `gas_btc_equivalent`
- `event_time_utc`
- `source_class`
- `evidence_level`
- `ingest_provenance`
- `schema_version`

Optional evidence fields:

- `token_address`
- `pair_address`
- `block_number`
- `route_hint`
- `principal_hint`
- `source_label_hint`
- `destination_label_hint`
- `liquidity_depth_usd`
- `route_depth_usd`
- `parent_event_uid_hint`
- `cluster_hint`

Forbidden fields:

- private keys
- seed phrases
- wallet signatures
- trade instructions
- order instructions
- runtime commands
- provider secrets

## 7. Output contract

The adapter design output consists of two separate bounded objects.

### 7.1 Canonical identity envelope

- `event_uid`
- `parent_event_uid`
- `route_uid`
- `cluster_uid`
- `economic_event_uid`
- `relation_type`
- `fragmented_link_candidate`
- `flow_shape`
- `multi_hop_route_candidate`
- `label_conflict_candidate`
- `identity_evidence`
- `ingest_provenance`
- `schema_version`

### 7.2 Existing core input

- `txid`
- `src`
- `dst`
- `btc_eq`
- `gas_btc_eq`
- `depth`
- `ts_mono_ns`

The identity envelope must remain separate from the existing core input so the core can remain unchanged.

## 8. Deterministic identity rules

### 8.1 Event UID

`event_uid` must be deterministic from canonicalized identity fields. Reprocessing the same event must produce the same UID.

Minimum identity material:

- chain
- txid
- transaction_index
- normalized source wallet
- normalized destination wallet
- asset UID

### 8.2 Exact duplicate

An exact duplicate must not create a second economic observation or second core edge.

### 8.3 Near duplicate

A near duplicate remains separately auditable but cannot be double-counted as an independent economic event without additional evidence.

### 8.4 Related but not duplicate

Shared wallets, routes, principals, or timing may create relation evidence, but they do not authorize deduplication or aggregation by themselves.

## 9. Fragmented transfer linkage

Fragmented transfer linkage requires multiple independent evidence dimensions. Amount aggregation alone is forbidden.

Supporting evidence may include:

- same evidenced principal;
- same or related destination;
- compatible asset identity;
- bounded time relation;
- common funding origin;
- deterministic fan-in or fan-out structure;
- common route evidence.

If linkage evidence is insufficient, events remain separate and the result is explicit unresolved relation evidence.

## 10. Multi-hop and bridge linkage

Bridge entry, technical mirror legs, and bridge exit may be linked to one route when evidence supports a common principal and route.

Rules:

- principal economic value must not be double-counted;
- technical mirror legs must remain auditable;
- route linkage is not entity truth;
- missing route evidence remains UNKNOWN or REVIEW_REQUIRED downstream;
- the adapter may mark route candidates but may not decide market impact.

## 11. Cluster and label conflict

`cluster_uid` is behavioral relation evidence, not final entity identity.

If static label evidence conflicts with cluster or behavioral evidence:

- the adapter records `label_conflict_candidate=true`;
- neither source wins automatically;
- the conflict proceeds to Evidence Engine synthesis;
- the adapter must not rewrite or erase either evidence source.

## 12. Existing core reuse boundary

The adapter must import and call the existing core rather than copy its implementation.

The following remain exclusively owned by `tools/runtime_whale_graph_v1.py`:

- 50 BTC core threshold;
- 45 BTC soft threshold;
- 35 BTC watch threshold;
- known-wallet trigger behavior;
- dust and gas-ratio filter;
- graph depth bound;
- graph node bound;
- existing wallet registry;
- CEX inflow detection;
- edge hash behavior;
- probability score;
- trade-authority false state.

## 13. No-duplication gates

A future implementation fails design review if it contains any of the following:

- copied threshold constants;
- copied `whale_tier` logic;
- copied dust/gas filter;
- copied wallet registry;
- copied graph engine or graph bounds;
- copied probability score;
- a second duplicate classifier outside the canonical identity boundary;
- product-specific or token-specific branches;
- permanent scripts created solely for one smoke test.

## 14. Error and unknown handling

- Invalid required schema: fail closed.
- Unknown economic context: preserve UNKNOWN.
- Unknown attribution: preserve UNKNOWN.
- Unsupported source class: reject before core invocation.
- Duplicate ambiguity: do not merge automatically.
- Identity conflict: preserve evidence and defer final decision.
- Adapter failure: must not block unrelated event ingestion at architectural level.

No implementation technology for non-blocking behavior is selected by this contract.

## 15. Future validation requirements

Before adapter code may be authorized, a bounded implementation plan must prove:

1. one general module can serve all approved chains and assets;
2. existing core is imported unchanged;
3. all eight measured identity gaps are addressed;
4. no core capability is duplicated;
5. deterministic hashes remain stable;
6. exact duplicate rejection works;
7. fragmented positive and negative cases remain distinct;
8. multi-hop principal value is counted once;
9. UNKNOWN handling is explicit;
10. repository, DB, runtime, panel, service, and network mutations remain zero during dry-run;
11. no permanent test-only script is required unless a reusable general capability is proven necessary.

## 16. Retirement decision

- PROVEN_DUPLICATE_COMPONENT_COUNT=0
- RETIREMENT_AUTHORIZED_COUNT=0

No component may be retired from this design alone.

`tools/whale_center_live_producer_v1.py` remains a conditional retirement candidate only after a real general small-readmodel producer demonstrates replacement parity, fail-closed behavior, consumer migration, benchmark success, runtime validation, and Opportunity Cost ACCEPT.

## 17. Completion state

- ADAPTER_CONTRACT_COMPLETE=true
- NO_DUPLICATION_DESIGN_COMPLETE=true
- ADAPTER_CODE_COMPLETE=false
- CORE_CODE_CHANGED=false
- RUNTIME_PIPELINE_COMPLETE=false
- LIVE_WHALE_INTELLIGENCE=false

NEXT_SAFE_STEP=WHALE_THIN_GENERAL_EVENT_IDENTITY_ADAPTER_EPHEMERAL_REFERENCE_IMPLEMENTATION_PLAN
HUMAN_APPROVAL_REQUIRED_FOR_NEXT_STEP=true
