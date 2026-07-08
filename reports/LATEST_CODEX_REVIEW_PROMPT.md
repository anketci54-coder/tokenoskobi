CODEX FULL-SYSTEM REVIEW PROMPT — ERA48

Repository: anketci54-coder/tokenoskobi
Current HEAD before ERA48 close: 442fc6ea970e1a51d5dd8c4774f43cb590cceeb6
Work unit: ERA48_REACHABILITY_CLASSIFICATION_NOAPI
Decision candidate: WARN_ACTIVE_RED_REQUIRES_REVIEW
Next safe step candidate: ERA49_ACTIVE_SURFACE_REVIEW_NOAPI

Review:
- data/control/era48_reachability_classification_noapi_v1.json
- reports/LATEST_ERA48_REACHABILITY_CLASSIFICATION_NOAPI.md

Classify risky surfaces as:
1. ACTIVE_RUNTIME
2. DORMANT_MANUAL
3. ARCHIVE
4. UNKNOWN_REQUIRES_PROOF

Hard fail if:
- ACTIVE_RUNTIME mutation/security risk is mislabeled as archive.
- Discipline Layer write/mutation path exists.
- Implementation is recommended before classification is complete.

Return:
- Overall score
- PASS/WARN/FAIL
- Misclassified active surfaces
- Remaining UNKNOWN_REQUIRES_PROOF
- Bloat classification
- Implementation Go/No-Go
- Next safe recommendation
