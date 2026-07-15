# WHALE ENTITY ATTRIBUTION READMODEL INPUT/OUTPUT AND REUSE CONTRACT V1

CONTRACT_STATUS=SEALED_DESIGN_ONLY
WORK_UNIT=WHALE_ENTITY_ATTRIBUTION_READMODEL_INPUT_OUTPUT_CONTRACT_AND_EXISTING_COMPONENT_REUSE_DECISION

## 1. Purpose

This contract defines the bounded, read-only input/output boundary for a future Whale Entity Attribution Readmodel.

The readmodel exists to organize evidence about addresses, clusters and known entities. It must not convert labels into truth, infer intent, decide market impact, produce risk decisions or authorize trade actions.

This contract does not authorize executable implementation.

## 2. Canonical position

Required flow position:

SOURCE_EVENT
→ EVENT_IDENTITY_NORMALIZATION
→ EXISTING_GRAPH_CORE
→ ENTITY_ATTRIBUTION_READMODEL
→ EVIDENCE_SYNTHESIS
→ RISK_LINK

The readmodel is downstream of canonical event identity and graph observations. It is upstream of Evidence Synthesis.

## 3. Mandatory non-decision clause

The Entity Attribution Readmodel is evidence organization only.

It must not:

- declare an address or cluster to be absolutely owned by an entity,
- infer intent,
- decide whether an event is a whale event,
- decide market impact,
- decide risk,
- select a terminal assessment state,
- issue trade, order, signing or wallet instructions.

ENTITY_DECISION_AUTHORITY=false
INTENT_INFERENCE_AUTHORITY=false
MARKET_IMPACT_DECISION_AUTHORITY=false
RISK_DECISION_AUTHORITY=false
TERMINAL_DECISION_AUTHORITY=false
TRADE_AUTHORITY=false
WALLET_SIGNING_AUTHORITY=false

## 4. Required input contract

The readmodel may accept only normalized, bounded records with fields equivalent to:

- event_uid
- parent_event_uid
- route_uid
- cluster_uid
- chain_uid
- source_wallet
- destination_wallet
- asset_uid
- event_time_utc
- graph_edge_reference
- graph_depth
- source_class
- evidence_reference_ids
- evidence_observed_at_utc
- schema_version
- ingest_provenance

Optional attribution evidence fields may include:

- claimed_entity_name
- claimed_entity_type
- label_source
- label_source_class
- label_observed_at_utc
- label_valid_from_utc
- label_valid_until_utc
- behavior_class
- historical_interaction_reference_ids
- contradiction_reference_ids

No input may contain:

- private keys,
- seed phrases,
- wallet signatures,
- provider secrets,
- order instructions,
- trade instructions,
- runtime commands,
- live-fetch authorization.

## 5. Evidence-source separation

The readmodel must preserve source separation.

The following evidence classes must remain independently visible:

- STATIC_LABEL_EVIDENCE
- BEHAVIORAL_CLUSTER_EVIDENCE
- TRANSACTION_HISTORY_EVIDENCE
- COUNTERPARTY_EVIDENCE
- SOURCE_PROVENANCE_EVIDENCE
- CONTRADICTION_EVIDENCE

No source class may silently overwrite another.

STATIC_LABEL_IS_TRUTH=false
BEHAVIORAL_CLUSTER_IS_TRUTH=false
HISTORY_IS_TRUTH=false
SINGLE_SOURCE_FINAL_AUTHORITY=false

## 6. Required output contract

The readmodel may output only an evidence-oriented structure equivalent to:

- attribution_readmodel_uid
- subject_type
- subject_uid
- event_uid
- cluster_uid
- candidate_entity_labels
- candidate_entity_types
- supporting_evidence_refs
- contradicting_evidence_refs
- stale_evidence_refs
- unresolved_fields
- label_conflict
- freshness_state
- evidence_snapshot_time_utc
- schema_version

Allowed subject types:

- ADDRESS
- CLUSTER
- ROUTE
- EVENT_COUNTERPARTY

Allowed freshness states:

- CURRENT
- STALE
- UNKNOWN
- CONFLICTING

The output must not contain a final intent, market-impact, risk or trade decision.

## 7. Candidate-label rule

All entity labels are candidates supported by evidence.

Required representation:

- label value,
- source reference,
- source class,
- observation time,
- validity window when available,
- contradiction references,
- freshness state.

A candidate label must not become canonical truth merely because it appears in a registry.

## 8. Label-conflict rule

If static attribution and behavioral evidence conflict:

- both must remain visible,
- neither may silently replace the other,
- label_conflict=true must be emitted,
- Evidence Synthesis must receive the conflict,
- the readmodel must not break the tie.

BEHAVIOR_ALWAYS_OVERRIDES_STATIC=false
STATIC_ALWAYS_OVERRIDES_BEHAVIOR=false
FORCED_TIE_BREAK=false

## 9. Staleness and lifecycle rule

Every attribution observation must carry time context.

Evidence without a reliable observation time must be marked UNKNOWN freshness.

Expired, outdated or superseded labels must remain auditable as stale evidence and must not be deleted from the evidence chain merely because a newer label exists.

SILENT_LABEL_REFRESH=false
SILENT_LABEL_OVERWRITE=false
HISTORY_ERASURE=false

## 10. Unknown-preservation rule

Unknown values must remain UNKNOWN.

The readmodel must not convert missing or conflicting evidence into:

- NOT_A_WHALE,
- NO_SIGNIFICANT_IMPACT,
- LOW_RISK,
- BENIGN,
- KNOWN_ENTITY.

UNKNOWN_IS_NEGATIVE=false
INSUFFICIENT_EVIDENCE_IS_NO_IMPACT=false

## 11. Existing component reuse decision

The following existing capabilities must be reused unchanged where applicable:

- existing Whale Graph Core for graph boundaries and observations,
- existing known-wallet seed/registry as one evidence source only,
- existing canonical event identity contract,
- existing evidence/provenance contracts,
- existing generic ephemeral harness for future bounded compatibility tests.

The readmodel must not copy:

- Whale thresholds,
- graph traversal logic,
- known-wallet registries,
- event UID generation,
- route linkage logic,
- duplicate guards,
- risk scoring,
- terminal-state logic.

GRAPH_CORE_REUSE=UNCHANGED
KNOWN_WALLET_REGISTRY_REUSE=EVIDENCE_SOURCE_ONLY
EVENT_IDENTITY_REUSE=UNCHANGED
THRESHOLD_LOGIC_COPY=false
GRAPH_LOGIC_COPY=false
REGISTRY_COPY=false
EVENT_IDENTITY_COPY=false
RISK_LOGIC_COPY=false

## 12. Read-only boundary

This contract authorizes no database schema or writer.

The future compatibility path must begin with process-local fixtures and ephemeral outputs.

DATABASE_SCHEMA_CHANGE_AUTHORIZED=false
DATABASE_MUTATION_AUTHORIZED=false
PERSISTENT_READMODEL_AUTHORIZED=false
RUNTIME_BINDING_AUTHORIZED=false
LIVE_FETCH_AUTHORIZED=false
PANEL_BINDING_AUTHORIZED=false

## 13. No-addition-without-retirement rule

No new permanent component is authorized by this contract.

Before permanent implementation, evidence must prove:

1. recurring operational need,
2. existing component insufficiency,
3. measured benefit,
4. no duplicated capability,
5. a retirement or replacement plan where applicable,
6. Opportunity Cost ACCEPT.

RETIREMENT_AUTHORIZED_COUNT=0
PERMANENT_IMPLEMENTATION_AUTHORIZED=false

## 14. Terminal responsibility separation

The readmodel has no pipeline terminal-state ownership.

It may only emit structured evidence conditions such as:

- label_conflict=true,
- freshness_state=STALE,
- unresolved_fields present,
- supporting evidence present,
- contradiction evidence present.

Evidence Synthesis remains responsible for downstream assessment handling.

## 15. Compatibility requirements

A future bounded compatibility test must prove at least:

- normalized event input acceptance,
- address subject output,
- cluster subject output,
- multiple candidate labels preserved,
- static/behavior conflict preserved,
- stale label preserved,
- unknown preserved,
- no single-source truth promotion,
- no threshold copy,
- no registry copy,
- no graph logic copy,
- deterministic output,
- exactly one structured readmodel result per subject snapshot,
- repository immutability,
- production database immutability,
- no network access.

## 16. Explicit non-authorizations

NEW_ENGINE=false
NEW_SCRIPT=false
NEW_SCHEMA=false
NEW_DATABASE_WRITER=false
NEW_REGISTRY=false
CORE_INTERFACE_CHANGE=false
PRODUCT_SPECIFIC_CODE=false
TOKEN_SPECIFIC_CODE=false
CHAIN_SPECIFIC_CODE=false
ERA57_OPENED=false

## 17. Canonical reuse decision

REUSE_DECISION=USE_EXISTING_GRAPH_EVENT_AND_REGISTRY_EVIDENCE_WITHOUT_COPY
READMODEL_ROLE=EVIDENCE_ORGANIZATION_ONLY
IMPLEMENTATION_DECISION=DEFER_PENDING_EPHEMERAL_COMPATIBILITY_PROOF

## 18. Next safe step

NEXT_SAFE_STEP=WHALE_ENTITY_ATTRIBUTION_READMODEL_EPHEMERAL_COMPATIBILITY_TEST_DESIGN
