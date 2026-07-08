CODEX REVIEW PROMPT — MAIN LINE SPLIT POLICY LOCK

Repository: anketci54-coder/tokenoskobi
Current HEAD before seal: 5cefea631e2b422358e7f708a2eeed4548fbf56b
Task: CANONICAL_MAIN_LINE_SPLIT_POLICY_LOCK_NO_NEW_LINE

Review whether the startup/canonical files now enforce:

- Main lines must contain related work only.
- Related work stays inside one main line using A/B/C/D/E/F.
- If one related topic is too large, split into 2-3 sibling main lines only with explicit reason.
- Splitting reasons must be scope, risk profile, impact area, independent testing/audit, or delivery speed.
- No new main line only for plan/test/audit/review/seal/cleanup/state normalization/minor fix/minor addition.
- Nested _1/_2/_3, FIX_1/FIX_2, and ADD_1/ADD_2 stay under the relevant letter.
- Next real software step remains ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI.
- No Runtime, DB, panel, service, timer, deploy mutation was performed.

Return:
- Overall score
- OK / WARN / FAIL
- Remaining ambiguity for new ChatGPT windows
- Any canonical drift
- Next safe recommendation
