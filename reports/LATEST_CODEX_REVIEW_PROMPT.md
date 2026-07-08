CODEX FULL-SYSTEM REVIEW PROMPT

Repository: anketci54-coder/tokenoskobi
Current HEAD: 8072a5104080ca1a9876665fa23a5a9401aa6a32
Closed work unit: ERA46_DISCIPLINE_LAYER_PLAN_NOAPI
Decision: PASS_WITH_GUARDS
Next safe step: ERA47_DISCIPLINE_LAYER_VALIDATION_NOAPI

Review only the delta introduced by this ERA plus any full-system risk it exposes.

Check:
1. Runtime/Lab boundary violation.
2. Lab read-only / NOAPI / air-gapped violation.
3. Heavy math in runtime hot path.
4. Canonical drift against Truth Priority.
5. Repo bloat or unnecessary script/file growth.
6. Security leaks, secrets, shell=True/os.system risks in reachable runtime.
7. Mutation risk or auto-fix behavior.
8. Opportunity Cost violation.
9. Missing schema/version guard.
10. Missing decision audit trail.

If Discipline Layer failure is detected, include:
BLOCKER: Discipline Layer Failure detected in work unit ERA46_DISCIPLINE_LAYER_PLAN_NOAPI. Implementation blocked.

Return:
- Overall score
- PASS/WARN/FAIL
- Top blockers
- Leaks/mutations
- Canonical drift
- Bloat impact
- Speed/security/power/frugality impact
- Next safe recommendation
