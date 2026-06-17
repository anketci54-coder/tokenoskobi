
================================================================
MANDATORY_STATE_DISCOVERY
================================================================

Before any planning:

READ PROJECT_MASTER_STATE.md

Extract:

CURRENT_PHASE
LAST_COMPLETED
NEXT_PHASE
KNOWN_BLOCKERS
DO_NOT_REPEAT

If any of these fields cannot be located:

STOP

Do not create:

- new roadmap
- new architecture
- new runtime plan
- new manifesto

Run audit first.

================================================================
MANDATORY_WORKFLOW
================================================================

READ
↓
VERIFY
↓
PLAN
↓
APPROVAL
↓
APPLY
↓
TEST
↓
POST_AUDIT
↓
UPDATE_PROJECT_MASTER_STATE
↓
GITHUB_PUSH

================================================================
ANTI_LOOP_RULES
================================================================

Do not restart already completed planning phases.

Do not redesign existing architecture unless explicitly requested.

Do not create duplicate roadmap generations.

PROJECT_MASTER_STATE.md overrides chat memory.

================================================================

