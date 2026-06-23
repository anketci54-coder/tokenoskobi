# DOCUMENT_GOVERNANCE_V1

## PURPOSE

Keep Tokenoskobi documentation readable, canonical, and non-duplicated.

## ROOT RULE

ROOT_ONLY_CANONICAL_SUMMARY=true

Root may contain only:

01_INDEX.md
02_MANIFESTO.md
03_ROADMAP.md
04_ALMANAC.md
05_ATLAS.md
README.md
.gitignore
.TOKENOSKOBI_CLEAN_V1_ROOT

## SINGLE SOURCE RULE

DOCUMENT_SINGLE_SOURCE_OF_TRUTH=true
NO_DUPLICATE_DOCS=true
NO_MIRROR_DOCS=true

A document may have one physical canonical location.

## DOCS RULE

docs/ contains active canonical documentation.

docs/phases/ contains phase folders.

Each phase must use:

docs/phases/phaseXX/

Example:

docs/phases/phase52/

## PHASE FOLDER RULE

PHASE_DIRECTORY_REQUIRED=true

Each closed phase must place phase artifacts under its phase folder.

Allowed contents:

PLAN
SCHEMA
TEMPDB
POST_AUDIT
CANONICAL_BIND
FINAL
POST_PUSH
SEAL
README

## ARCHIVE RULE

ARCHIVE_IS_NOT_TRASH=true
STRUCTURED_ARCHIVE_REQUIRED=true

archive/ must be structured:

archive/phases/
archive/passes/
archive/audits/
archive/backups/
archive/legacy/

No loose archive dumping.

## DUPLICATE RULE

If a file exists in docs/ and archive/, only one may remain canonical.

Duplicate candidates must be audited before action.

## APPLY RULE

No delete without explicit approval.
No mass move without dry-run manifest.
No archive without backup.
No root clutter.
No phase file directly under docs/ after reorg is complete.

## MANIFESTO BINDING

DOCUMENT_GOVERNANCE_IS_CONSTITUTIONAL=true

Speed never down.
Security never down.
Power never down.
Order never down.


<!-- MANIFESTO_STRUCTURE_RULE:START -->
## MANIFESTO STRUCTURE RULE

MANIFESTO_APPEND_TO_END_FORBIDDEN=true

MANIFESTO_UPDATE_UNDER_EXISTING_HEADINGS=true

MANIFESTO_RANDOM_NEW_SECTION_FORBIDDEN=true

MANIFESTO_PHASE_REPORT_FORBIDDEN=true

MANIFESTO_PASS_REPORT_FORBIDDEN=true

MANIFESTO_NEXT_STEP_FORBIDDEN=true

MANIFESTO_GOVERNANCE_LOG_FORBIDDEN=true

02_MANIFESTO.md must keep the fixed main heading system.

Future additions must be placed under the correct existing heading.

If no existing heading fits, a new main heading requires explicit approval before writing.
<!-- MANIFESTO_STRUCTURE_RULE:END -->

