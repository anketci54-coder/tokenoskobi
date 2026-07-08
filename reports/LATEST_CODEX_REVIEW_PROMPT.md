CODEX REVIEW PROMPT — ERA47 PREFLIGHT CHAIN CONSOLIDATION

Repository: anketci54-coder/tokenoskobi
Current HEAD before seal: 9bd7bf9730f06a83c03bad9b8115520256c94ddd
Task: ERA47_DISCIPLINE_PREFLIGHT_CHAIN_CONSOLIDATION_NOAPI

Review whether the current tree correctly consolidates old ERA47-ERA51 work under one parent chain:

ERA47_DISCIPLINE_PREFLIGHT_CHAIN_NOAPI

Expected canonical mapping:
- ERA47A = old ERA47 plan validation
- ERA47B = old ERA48 reachability classification
- ERA47C = old ERA49 false-positive / active surface review
- ERA47D = old ERA50 active runtime risk decision
- ERA47E = old ERA51 Go/No-Go

Check:
- No new software implementation was performed.
- Old labels remain only as historical aliases.
- Next real software step remains ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI.
- A/B/C/D substep policy is restored.
- No Runtime, DB, panel, service, timer, or deploy mutation was performed.
- Deadline mode reduces label/document growth.

Return:
- Overall score
- OK / WARN / FAIL
- Any canonical drift
- Any remaining bloat risk
- Whether ERA52 can proceed as a single A/B/C/D work unit
- Next safe recommendation
