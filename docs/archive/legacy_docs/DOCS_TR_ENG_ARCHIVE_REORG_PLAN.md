# DOCS TR / ENG / ARCHIVE REORG PLAN

PLAN_ONLY=true
DOC_ONLY=true
NO_DELETE=true
NO_GIT_RM=true
NO_RUNTIME_CHANGE=true
NO_DB_WRITE=true
NO_PANEL_WRITE=true

TARGET_STRUCTURE:
docs/ENG/
docs/TR/
docs/archive/
docs/archive/PASS11/
docs/archive/PASS13/
docs/archive/PASS14/
docs/archive/PASS15/
docs/archive/PASS16/
docs/archive/PASS17/
docs/archive/PASS18/
docs/archive/PASS19/
docs/archive/PASS20/
docs/archive/PASS21/
docs/archive/PASS22/
docs/archive/PASS23/
docs/archive/PASS24/
docs/archive/PASS25/
docs/archive/PASS26/
docs/archive/PASS27/
docs/archive/PHASES/
docs/archive/atlas_build_history/

RULE:
- ENG = canonical technical docs
- TR = human-readable Turkish summaries
- archive = historical pass/phase evidence
- No deletion in first apply
- Use git mv only for tracked historical docs

PASS11_ARCHIVE_RULE:
PASS11C-O files move under docs/archive/PASS11/
Create docs/archive/PASS11/README.md explaining every subpass.

NEXT_STEPS:
1_CREATE_STRUCTURE_AND_READMES_PLAN
2_REAL_APPLY_AFTER_APPROVAL
3_POST_AUDIT
4_GITHUB_PUSH

FINAL_GATE=PASS_DOCS_TR_ENG_ARCHIVE_REORG_PLAN_NOAPI
NEXT_SAFE_STEP=DOCS_TR_ENG_ARCHIVE_REORG_REAL_APPLY_AFTER_APPROVAL
