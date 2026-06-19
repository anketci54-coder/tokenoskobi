# FINAL REPO STRUCTURE DECISION

FINAL_DECISION=PASS_WITH_RUNTIME_UNTRACKED_PARKED

## CANONICAL TRACKED STRUCTURE

Core tracked:
- PROJECT_MASTER_STATE.md
- PROJECT_HANDOFF.md
- docs/INDEX.md
- docs/CANONICAL_V1_INTELLIGENCE_CORE.md
- docs/CANONICAL_V1_MASTER_PHASE_PASS_ATLAS.md

Root tracked:
- .TOKENOSKOBI_CLEAN_V1_ROOT
- GUARDS.md
- MANIFEST.md
- PROJECT_STRUCTURE_LOCK_V1.md
- PROJECT_TRUTH.md
- ROADMAP_14_PHASES.md

Documentation tracked:
- docs/ENG/
- docs/TR/
- docs/archive/PASS11/
- docs/archive/PASS13/ ... docs/archive/PASS27/
- docs/archive/PHASES/
- docs/archive/atlas_build_history/

## VERIFIED COUNTS

PASS_README_TRACKED_COUNT=16
PHASE_TRACKED_COUNT=42
ATLAS_BUILD_HISTORY_TRACKED_COUNT=76

## REMAINING UNTRACKED POLICY

Remaining untracked files are not GitHub documentation noise.

They are parked as:
- runtime folders
- panel folders
- data folders
- local archive
- source/runtime candidates
- preview/build artifacts

DO_NOT_TOUCH:
- active_panel_8096/
- data/
- panel_assets/
- public/
- internal_xyz_staging/
- maintenance/
- core/
- tools/
- accepted_baselines/
- baselines/
- config_fixed/
- control_dashboard_engine_v1/

## RESULT

GitHub documentation structure is accepted.
Runtime/data/panel leftovers are intentionally parked for separate runtime audit.

FINAL_GATE=PASS_FINAL_REPO_STRUCTURE_DECISION
NEXT_SAFE_STEP=FINAL_REPO_STRUCTURE_DECISION_GITHUB_PUSH_REAL_APPLY
