CODEX FULL-SYSTEM REVIEW PROMPT — ERA50

Repository: anketci54-coder/tokenoskobi
Current HEAD before ERA50 close: 96ea75d404ce2064c879396e821ed16c71cc8aa3
Work unit: ERA50_ACTIVE_RUNTIME_RISK_DECISION_NOAPI
Decision candidate: PASS_RISK_DECIDED_NO_DISCIPLINE_BLOCKER
Next safe step candidate: ERA51_DISCIPLINE_IMPLEMENTATION_GO_NOGO_NOAPI

Review:
- data/control/era50_active_runtime_risk_decision_noapi_v1.json
- reports/LATEST_ERA50_ACTIVE_RUNTIME_RISK_DECISION_NOAPI.md

Question:
Did ERA50 correctly distinguish expected runtime mutation-capable surfaces from Discipline Layer blockers?

Hard fail if:
- Discipline Layer implementation is authorized directly by ERA50.
- Any Discipline Layer path imports, invokes, or mutates Runtime.
- Manual deploy scripts are allowed to run automatically.
- Runtime DB/panel/service/timer writes are assigned to Discipline Layer.
- Active RED is ignored without a risk decision.
- Implementation is recommended without a separate Go/No-Go review.

Return:
- Overall score
- PASS/WARN/FAIL
- Wrongly accepted risks
- Remaining hard blockers
- Runtime/Lab boundary verdict
- Deploy/manual surface verdict
- Implementation Go/No-Go recommendation
- Next safe recommendation
