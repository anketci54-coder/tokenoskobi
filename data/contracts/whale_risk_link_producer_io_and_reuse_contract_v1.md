# Whale Risk Link Producer IO and Existing Component Reuse Contract v1

CONTRACT_STATUS=SEALED_DESIGN_ONLY

## 1. Purpose

Define a bounded, read-only contract for transforming a previously assembled Whale Evidence Package into a standardized Risk Engine input package without producing any risk score, market-impact decision, terminal decision, trade signal, or execution authority.

## 2. Canonical Role

RISK_LINK_PRODUCER_ROLE=STANDARDIZED_RISK_INPUT_ASSEMBLY_ONLY

The Risk Link Producer is a transducer. It may organize, normalize, reference, and forward already-produced evidence. It must not synthesize a final risk conclusion.

## 3. Required Inputs

- event_identity_reference
- graph_evidence_reference
- entity_attribution_readmodel_reference
- evidence_package_reference
- source_provenance
- evidence_staleness_metadata
- preserved_conflicts
- insufficient_evidence_marker
- schema_version

## 4. Allowed Output

A deterministic standardized risk input package containing only:

- risk_input_uid
- event_uid
- economic_event_uid
- evidence_package_uid
- evidence_references
- source_provenance
- stale_evidence_present
- conflict_markers
- insufficient_evidence
- schema_version
- producer_version

## 5. Forbidden Output

The following fields and authorities are forbidden:

- risk_score
- final_risk_class
- market_impact_score
- market_impact_decision
- intent_class
- entity_decision
- trade_signal
- order_instruction
- terminal_state
- execution_instruction

## 6. Mandatory Non-Decision Clause

RISK_SCORE_AUTHORITY=false
FINAL_RISK_AUTHORITY=false
ENTITY_DECISION_AUTHORITY=false
INTENT_INFERENCE_AUTHORITY=false
MARKET_IMPACT_DECISION_AUTHORITY=false
TERMINAL_DECISION_AUTHORITY=false
TRADE_AUTHORITY=false
ORDER_CREATE_AUTHORITY=false
WALLET_SIGNING_AUTHORITY=false

The Risk Link Producer must never interpret insufficient evidence as low risk or no significant impact. It must preserve the insufficiency marker for downstream Risk Engine handling.

## 7. Existing Component Reuse Decision

EVENT_IDENTITY_REUSE=UNCHANGED
GRAPH_CORE_REUSE=UNCHANGED
ENTITY_ATTRIBUTION_READMODEL_REUSE=EVIDENCE_REFERENCE_ONLY
EVIDENCE_PRODUCER_REUSE=UNCHANGED
RISK_ENGINE_REUSE=REFERENCE_ONLY
KNOWN_WALLET_REGISTRY_REUSE=REFERENCE_ONLY

## 8. No-Copy Rules

GRAPH_LOGIC_COPY=false
THRESHOLD_LOGIC_COPY=false
REGISTRY_COPY=false
ENTITY_LOGIC_COPY=false
EVIDENCE_ASSEMBLY_LOGIC_COPY=false
RISK_ENGINE_LOGIC_COPY=false
TRADE_LOGIC_COPY=false

The producer may reference canonical outputs but may not reimplement their logic.

## 9. Conflict and Staleness Preservation

- Label conflicts remain explicit conflict markers.
- Stale evidence remains marked stale.
- Unknown values remain UNKNOWN.
- Insufficient evidence remains INSUFFICIENT_EVIDENCE.
- No forced tie-break is allowed.
- No evidence item may be silently dropped because it conflicts with another source.

## 10. Determinism

The same canonical inputs and schema version must produce the same risk_input_uid and equivalent standardized output.

## 11. Immutability and Runtime Bounds

NEW_PRODUCER_CODE_AUTHORIZED=false
NEW_SCRIPT_AUTHORIZED=false
NEW_ENGINE_AUTHORIZED=false
RISK_ENGINE_CHANGE_AUTHORIZED=false
PERMANENT_IMPLEMENTATION_AUTHORIZED=false
RUNTIME_BINDING_AUTHORIZED=false
DATABASE_SCHEMA_CHANGE_AUTHORIZED=false
DATABASE_MUTATION_AUTHORIZED=false
LIVE_FETCH_AUTHORIZED=false
NETWORK_ACCESS_AUTHORIZED=false
PANEL_MUTATION_AUTHORIZED=false

## 12. Product-Neutrality

PRODUCT_SPECIFIC_CODE=false
TOKEN_SPECIFIC_CODE=false
CHAIN_SPECIFIC_CODE=false
PROVIDER_SPECIFIC_CODE=false

The contract must remain usable for any evidence domain that needs bounded standardized risk input assembly.

## 13. No Addition Without Retirement

RETIREMENT_AUTHORIZED_COUNT=0

No existing component is proven duplicate or eligible for retirement at this stage. A future permanent implementation requires measured operational demand, comparative benchmark evidence, an explicit replacement plan, and Opportunity Cost ACCEPT.

## 14. Validation Scope

This contract authorizes design and ephemeral compatibility testing only. It does not prove:

- real-world risk accuracy
- runtime throughput
- production reliability
- live onchain ingestion
- final Risk Engine integration
- trade safety

## 15. Next Safe Step

NEXT_SAFE_STEP=WHALE_RISK_LINK_PRODUCER_EPHEMERAL_COMPATIBILITY_TEST_DESIGN
