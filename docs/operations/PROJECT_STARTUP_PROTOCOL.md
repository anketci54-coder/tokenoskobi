# TOKENOSKOBI_STARTUP_PROTOCOL

PURPOSE

Yeni sohbet açıldığında veya yeni geliştirici projeye dahil olduğunda uygulanacak zorunlu başlangıç prosedürü.

---

MANDATORY_STARTUP_ORDER

1. READ PROJECT_MASTER_STATE.md

2. READ PROJECT_HANDOFF.md

3. READ docs/CANONICAL_V1_INTELLIGENCE_CORE.md

4. READ docs/INDEX.md

5. EXTRACT

CURRENT_PHASE
LAST_COMPLETED
NEXT_PHASE
KNOWN_BLOCKERS
DO_NOT_REPEAT

6. CONTINUE FROM NEXT_PHASE

---

DO_NOT_REPEAT_AUDITS

CANONICAL_ALIGNMENT_AUDIT

NEWS_PIPELINE_EXISTENCE_AUDIT

PRODUCER_EXISTENCE_AUDIT

GITHUB_SYNC_VERIFICATION

ROADMAP_REGENERATION

Unless explicitly requested.

---

SERVER_WORK_RULES

Never use nano.

Always provide paste-and-run commands.

Always start command blocks with:

cd /root/tokenoskobi_clean_v1

Assume session may have disconnected.

Never rely on current working directory.

---

PHASE_COMPLETION_PROTOCOL

When a phase completes:

1. Update related phase markdown.

2. Update PROJECT_MASTER_STATE.md.

3. Commit changes.

4. Push to GitHub.

5. Only then move to next phase.

---

CHAT_TRANSFER_PROTOCOL

Before moving to a new chat:

Update PROJECT_MASTER_STATE.md

Push latest state to GitHub

Record:

LAST_COMPLETED

NEXT_PHASE

KNOWN_BLOCKERS

DO_NOT_REPEAT

---

SOURCE_OF_TRUTH

PROJECT_MASTER_STATE.md

takes precedence over chat memory.

If chat memory and PROJECT_MASTER_STATE.md conflict:

PROJECT_MASTER_STATE.md wins.
