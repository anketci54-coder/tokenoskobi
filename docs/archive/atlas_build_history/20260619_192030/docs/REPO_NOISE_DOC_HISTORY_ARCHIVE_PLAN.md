# REPO NOISE DOC HISTORY ARCHIVE PLAN

PLAN_ONLY=true
NO_DELETE=true
NO_GIT_RM=true
NO_RUNTIME_CHANGE=true
NO_DB_WRITE=true
NO_PANEL_WRITE=true

TARGET_ARCHIVE_DIR=docs/archive/atlas_build_history/

ARCHIVE_ONLY:
- untracked docs/* audit/plan/discovery/classification/inventory/draft files
- untracked docs/*.bak_* files
- untracked docs/*pre_dedupe files
- generated text inventory files

DO_NOT_TOUCH:
- data/
- active_panel_8096/
- panel_assets/
- public/
- internal_xyz_staging/
- maintenance/
- accepted_baselines/
- baselines/
- config_fixed/
- control_dashboard_engine_v1/
- core/
- tools/

FINAL_GATE=PASS_REPO_NOISE_DOC_HISTORY_ARCHIVE_PLAN_NOAPI
NEXT_SAFE_STEP=REQUEST_EXPLICIT_APPROVAL_FOR_REPO_NOISE_DOC_HISTORY_ARCHIVE_REAL_APPLY
