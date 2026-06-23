# PHASE43_PROSECUTOR_ENGINE_PLAN_NOAPI

## STATUS
PLAN_ONLY

## HARD LOCKS
V1_SCOPE=true
MODE=PLAN_ONLY
DB_WRITE=false
RUNTIME_CHANGE=false
API_CALL=false
PANEL_WRITE=false
SERVICE_RESTART=false
GIT_PUSH=false
TRADE_AUTHORITY=false
AI_AUTHORITY=false

## PURPOSE
Hunter finds candidates.
Unknown Anomaly Engine raises suspicion.
Prosecutor Engine weighs the evidence.

Core question:

Why is this token guilty, suspicious, or clean?

## ROLE
The Prosecutor Engine is an evidence weighing and accusation/defense layer.

It does not trade.
It does not override Risk Engine.
It does not call APIs.
It does not create runtime authority.
It does not write to live DB in this phase.

## FUTURE INPUTS
- Unknown Anomaly Engine signals
- Risk Engine hard/soft blocks
- Evidence Backbone events
- Whale Intelligence signals
- News Intelligence signals
- Technical/Tactical signals
- Token lifecycle events
- Contract/deployer evidence
- Liquidity and sellability evidence

## FUTURE OUTPUTS
- prosecutor_case_file_v1
- prosecutor_evidence_matrix_v1
- prosecutor_verdict_readmodel_v1

## VERDICT CLASSES
- CLEAN
- WATCH
- SUSPICIOUS
- HIGH_RISK
- GUILTY
- INSUFFICIENT_EVIDENCE

## EVIDENCE RULE
No single weak signal should convict a token alone.

Strong verdict requires:
- multiple independent evidence sources
- clear reason text
- evidence references
- confidence score
- route recommendation

## NON-GOALS
- No schema apply
- No DB write
- No runtime binding
- No panel update
- No API/provider call
- No service restart
- No git push

## NEXT SAFE STEP
PHASE43B_PROSECUTOR_ENGINE_SCHEMA_PLAN_NOAPI

## FINAL_GATE
PASS_PHASE43_PROSECUTOR_ENGINE_PLAN_NOAPI
