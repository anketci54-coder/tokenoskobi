# GITHUB REPO CLEANUP AND ARCHIVE PLAN

PLAN_ONLY=true
DOC_ONLY=true
NO_DELETE=true
NO_GIT_RM=true
NO_RUNTIME_CHANGE=true
NO_DB_WRITE=true
NO_PANEL_WRITE=true

GOAL:
Clean visible GitHub root/docs structure after atlas locks.

KEEP_ROOT:
- README.md
- MANIFESTO.md
- PROJECT_MASTER_STATE.md
- PROJECT_HANDOFF.md
- PROJECT_PHILOSOPHY.md
- PROJECT_STARTUP_PROTOCOL.md
- TOKENOSKOBI_STARTUP_PROTOCOL.md

KEEP_DOCS_CORE:
- docs/INDEX.md
- docs/CANONICAL_V1_INTELLIGENCE_CORE.md
- docs/CANONICAL_V1_MASTER_PHASE_PASS_ATLAS.md
- docs/CANONICAL_V1_UNIFIED_MASTER_ATLAS_DRAFT.md

ARCHIVE_CANDIDATES:
- PASS11C_PASS11O historical docs
- old audit discovery docs
- temporary atlas plan/draft helper docs after final lock
- .bak_* files
- pre_dedupe files
- generated inventory/search files

ARCHIVE_TARGETS:
- docs/archive/pass11_alpha_watcher/
- docs/archive/atlas_build_history/
- docs/archive/backups/
- docs/archive/inventory_outputs/

ALMANAC_NEXT:
PROJECT_ALMANAC.md will summarize final architecture in human-readable Turkish + canonical English keys.

FINAL_GATE=PASS_GITHUB_REPO_CLEANUP_AND_ARCHIVE_PLAN_NOAPI
NEXT_SAFE_STEP=GITHUB_REPO_CLEANUP_INVENTORY_NOAPI
