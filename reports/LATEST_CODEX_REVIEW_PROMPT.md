CODEX REVIEW PROMPT — ERA52 MINIMAL READONLY SCAFFOLD

Repository: anketci54-coder/tokenoskobi
Current HEAD before seal: ba605ee220ae1058274c8c2ecfb1e10fc9cb697a
Task: ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI

Review whether ERA52 closes only the minimal read-only scaffold.

Expected:
- tools/discipline_layer_readonly_scaffold_v1.py exists.
- The scaffold only reads canonical machine state files.
- It does not write DB, panel, runtime, service, timer, deploy, wallet, or trade state.
- It does not call API/providers.
- It has no trading authority.
- It outputs a JSON snapshot.
- data/control/era52_discipline_layer_minimal_readonly_scaffold_noapi_v1.json records checks and authority boundaries.
- reports/LATEST_ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI.md summarizes closure.
- PROJECT_RUNTIME.json moves next safe step to NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW.
- No new micro main line was opened.
- No unrelated NEWS implementation was performed inside ERA52.

Return:
- Overall score
- OK / WARN / FAIL
- Boundary violations if any
- Missing closure evidence if any
- Whether NEWS stabilization can start next
