# V2_24 Decision Audit Log Contract

TASK=V2_24_DECISION_AUDIT_LOG_CONTRACT_PLAN_NOAPI
MODE=PLAN_ONLY_CONTRACT_NOAPI
STAMP_UTC=2026-06-26T05:30:26.867066+00:00
PARENT_HEAD=b548a66621266732bf60c2f0c9783e1096fb6081

## Purpose

V2_24 defines the strict audit-log contract for every Tokenoskobi decision.

No scoring DB write is allowed before this contract is post-audited and GitHub sealed.

## Locked Rules

DECISION_AUDIT_LOG_CONTRACT_SCHEMA=strict
FIELD_MANDATORY_VALIDATION=enabled
AUDIT_JSON_AUDITABLE_BY_DESIGN=true
NO_SCORE_WITHOUT_AUDIT_TRACE=true
NO_RED_WITHOUT_REASON=true
NO_HARD_BLOCK_WITHOUT_REASON=true
NO_VUR_KAC_DECISION_WITHOUT_EXIT_SAFETY=true
NO_POLIGON_DECISION_WITHOUT_DECISION_REASON=true
SHILL_COIN_TEST_VECTOR_REQUIRED=true

## Mandatory Fields

- decision_id
- token_uid
- chain
- contract_address
- decision_time
- decision_type
- final_decision
- final_score
- source_score
- team_score
- onchain_score
- liquidity_score
- whale_score
- simulation_score
- risk_penalty
- hard_block_triggered
- hard_block_reasons
- source_count
- same_origin_cluster_count
- independent_source_count
- unique_platform_count
- diversity_score
- independence_factor
- evidence_level
- echo_chamber_flag
- wash_trade_suspected
- critical_holder_concentration
- team_wallet_concentration
- vesting_or_lock
- vur_kac_score
- vur_kac_decision
- poligon_decision
- short_reason
- audit_json
- created_at

## Logic

Hard block is evaluated before score.
RED must always include short_reason.
Hard block must always include hard_block_reasons.
Echo chamber decisions must include source cluster evidence.
Vur-Kac decisions must include exit safety and net potential evidence.
Poligon decisions must include decision reason.
audit_json must preserve the decision ancestry.

## SHILL_COIN Test Vector

SHILL_COIN is the required Red Team test vector.

Expected:
FINAL_DECISION=RED
HARD_BLOCK=true
ECHO_CHAMBER_FLAG=true
INDEPENDENCE_FACTOR=0.446
DIVERSITY_SCORE=0.2
VUR_KAC=NO
POLIGON=NO

## Final Statement

No decision may be trusted unless its audit trace can explain why it exists.
