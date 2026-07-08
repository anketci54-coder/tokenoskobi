CODEX FULL-SYSTEM REVIEW PROMPT — ERA49

Repository: anketci54-coder/tokenoskobi
Current HEAD before ERA49 close: 00ba8df5d00ebfdeeb5f6f3b80741dbf4f96610d
Work unit: ERA49_ACTIVE_SURFACE_REVIEW_NOAPI
Decision candidate: WARN_ACTIVE_REVIEW_REQUIRED
Next safe step candidate: ERA50_ACTIVE_RUNTIME_RISK_DECISION_NOAPI

Review:
- data/control/era49_active_surface_review_noapi_v1.json
- reports/LATEST_ERA49_ACTIVE_SURFACE_REVIEW_NOAPI.md

Question:
Did ERA49 correctly refine ERA48 false positives?

Hard fail if:
- A real ACTIVE_RUNTIME executable risk is downgraded to archive/doc/control without evidence.
- A Discipline Layer write/mutation path exists.
- Implementation is allowed while active RED or UNKNOWN_REQUIRES_PROOF remains.
- Runtime/Lab boundary is violated.
- NOAPI/read-only doctrine is violated.

Return:
- Overall score
- PASS/WARN/FAIL
- Misclassified active runtime files
- Remaining active RED
- Remaining UNKNOWN_REQUIRES_PROOF
- False-positive cleanup accuracy
- Implementation Go/No-Go
- Next safe recommendation
