# TOKENOSKOBI / COINOSKOBI MANIFESTO

## PROJECT MEMORY RULE

PROJECT_HANDOFF.md is the authoritative human-readable recovery state.

The following events MUST update PROJECT_HANDOFF.md:

- Major phase closure
- PASS closure
- Roadmap change
- Architecture decision
- Security doctrine change
- Numbering rule change
- Project milestone

The following items MUST NOT be stored in PROJECT_HANDOFF.md:

- Temporary logs
- Long terminal outputs
- SHA dumps
- Large JSON payloads
- Inventory listings
- Transient diagnostics

## RECOVERY RULE

Before continuing work after:

- Context loss
- New chat
- Window change
- Recovery event

read:

cat /root/tokenoskobi_clean_v1/PROJECT_HANDOFF.md

and use it as the primary recovery source.

## AUTHORITATIVE FILES

PROJECT_HANDOFF.md = Human-readable project memory
PROJECT_MASTER_STATE.md = Technical inventory


================================================================
DOCUMENTATION GOVERNANCE UPDATE 2026-06-16
================================================================

AUTHORITATIVE PROJECT MEMORY SET

- PROJECT_HANDOFF.md
- PROJECT_MASTER_STATE.md
- PROJECT_TRUTH.md
- PROJECT_STRUCTURE_LOCK_V1.md
- PROJECT_PHILOSOPHY.md
- ROADMAP_14_PHASES.md

A phase is NOT considered CLOSED until required documentation has been updated.

IMPLEMENTATION WITHOUT DOCUMENTATION UPDATE STATUS:

IMPLEMENTED_BUT_NOT_DOCUMENTED


================================================================

DOCUMENT_GOVERNANCE_V1=CANONICALLY_BOUND
DOCUMENT_SINGLE_SOURCE_OF_TRUTH=true
NO_DUPLICATE_DOCS=true
NO_MIRROR_DOCS=true
STRUCTURED_ARCHIVE_REQUIRED=true
ARCHIVE_IS_NOT_TRASH=true
ROOT_ONLY_CANONICAL_SUMMARY=true
PHASE_DIRECTORY_REQUIRED=true
PHASE_FILES_UNDER_DOCS_PHASES=true
NO_DELETE_WITHOUT_EXPLICIT_APPROVAL=true
NO_MASS_MOVE_WITHOUT_DRYRUN_MANIFEST=true
NEXT_REPO_GOVERNANCE_STEP=REPO_GOVERNANCE_PASS02_REORG_DRYRUN_MANIFEST_NOAPI
