CODEX FULL-SYSTEM REVIEW PROMPT — NEXT

Repository: anketci54-coder/tokenoskobi
Closed work unit: ERA47_DISCIPLINE_LAYER_VALIDATION_NOAPI
Closed decision: WARN_ACCEPTED_NO_BLOCKER
Next safe step: ERA48_REACHABILITY_CLASSIFICATION_NOAPI

Review target:
Classify existing mutation/security/bloat surfaces as:
1. ACTIVE_RUNTIME
2. DORMANT_MANUAL
3. ARCHIVE
4. UNKNOWN_REQUIRES_PROOF

Focus:
- shell=True
- os.system
- subprocess usage
- external fetch tooling
- provider vault tooling
- panel/readmodel writers
- large legacy artifacts under data/shadow_runtime_lab and phase audit outputs

Hard rule:
Do not recommend implementation until active reachability is classified.

Return:
- Overall score
- PASS/WARN/FAIL
- Active runtime blockers
- Dormant/manual risks
- Archive-only risks
- Bloat classification
- Required next safe action
