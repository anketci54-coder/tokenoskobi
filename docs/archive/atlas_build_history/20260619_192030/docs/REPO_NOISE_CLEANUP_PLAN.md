# REPO NOISE CLEANUP PLAN

PLAN_ONLY=true
NO_DELETE=true
NO_GIT_RM=true
NO_RUNTIME_CHANGE=true
NO_DB_WRITE=true
NO_PANEL_WRITE=true

GOAL:
Classify untracked server noise without deleting anything.

NOISE_CLASSES:
- backup markdown files
- pre_dedupe files
- generated inventory txt files
- temporary audit docs
- local runtime folders
- panel/runtime/data folders that must not be blindly removed

SAFE_RULE:
First classify. Then optionally move only docs/markdown noise into docs/archive/atlas_build_history or server-only ignored area.

FINAL_GATE=PASS_REPO_NOISE_CLEANUP_PLAN_NOAPI
NEXT_SAFE_STEP=REPO_NOISE_INVENTORY_NOAPI
