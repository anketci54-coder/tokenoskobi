# PHASE52_9_REPO_CLEAN_FINAL_CLASSIFICATION_NOAPI

## STATUS
FINAL_CLASSIFICATION_ONLY

## PURPOSE

Classify repository clutter before PHASE53.

No delete.
No move.
No git add.
No commit.

## FINAL POLICY

KEEP_ROOT:
- 01_INDEX.md
- 02_MANIFESTO.md
- 03_ROADMAP.md
- 04_ALMANAC.md
- 05_ATLAS.md
- README.md
- .gitignore
- .TOKENOSKOBI_CLEAN_V1_ROOT

KEEP_DOCS_ACTIVE:
- docs/PROJECT_MASTER_STATE.md
- docs/PROJECT_HANDOFF.md
- docs/CANONICAL_DOCUMENTATION_V1_LOCK.md
- docs/INDEX.md
- docs/MANIFEST.md
- docs/CANONICAL_V1_INTELLIGENCE_CORE.md
- docs/PHASE50*
- docs/PHASE51*
- docs/PHASE52*

ARCHIVE_CANDIDATE:
- docs/PHASE42*
- docs/PHASE43*
- docs/PHASE44*
- docs/PHASE45*
- docs/PHASE46*
- docs/PHASE47*
- docs/PHASE48*
- docs/PHASE49*
- data/phase42*
- data/phase43*
- data/phase44*
- data/phase45*
- data/phase46*
- data/phase47*
- data/phase48*
- data/phase49*

DO_NOT_TOUCH:
- archive/
- schema/
- tests/
- tools/
- panel_assets/
- panel_static_shells/
- public/
- internal_xyz_staging/
- systemd_drafts/
- maintenance/
- ui_contracts/
- ENG/
- TR/

UNTRACKED_POLICY:
- backup files: ARCHIVE_OR_IGNORE_CANDIDATE
- phase43e duplicate: COMPARE_REQUIRED_BEFORE_ACTION
- phase47 post-push duplicate: COMPARE_REQUIRED_BEFORE_ACTION
- phase52_5/52_6/52_7/52_8/52_9 audit files: COMMIT_CANDIDATE

## NEXT_SAFE_STEP

PHASE52_10_REPO_CLEAN_DRYRUN_PLAN_NOAPI

## HARD LOCKS

DELETE=false
MOVE=false
GIT_ADD=false
GIT_COMMIT=false
DB_WRITE=false
RUNTIME_CHANGE=false
PANEL_WRITE=false
SERVICE_RESTART=false

## FINAL_GATE

PASS_PHASE52_9_REPO_CLEAN_FINAL_CLASSIFICATION_NOAPI
