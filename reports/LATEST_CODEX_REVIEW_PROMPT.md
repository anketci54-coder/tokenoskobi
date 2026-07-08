CODEX FULL-SYSTEM REVIEW PROMPT — ERA51

Repository: anketci54-coder/tokenoskobi
Current HEAD before ERA51 close: 0b91c981c238c05dba701285a8f3080255ed63bd
Work unit: ERA51_DISCIPLINE_IMPLEMENTATION_GO_NOGO_NOAPI
Decision candidate: GO_LIMITED_READONLY_SCAFFOLD_NOAPI
Next safe step candidate: ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI

Review:
- data/control/era51_discipline_implementation_go_nogo_noapi_v1.json
- reports/LATEST_ERA51_DISCIPLINE_IMPLEMENTATION_GO_NOGO_NOAPI.md

Question:
Does ERA51 correctly authorize only a minimal read-only scaffold for the next ERA, without implementing anything now?

Hard fail if:
- ERA51 creates engine code.
- ERA51 authorizes full implementation instead of limited scaffold.
- ERA51 permits Runtime import of Discipline/Lab.
- ERA51 permits DB/panel/service/timer/deploy mutation by Discipline Layer.
- ERA51 permits API/fetch/network access.
- ERA51 permits auto-fix or automatic repair.
- ERA51 permits wallet/signing/trade authority.
- ERA51 skips human approval.

Return:
- Overall score
- PASS/WARN/FAIL
- Wrongly authorized scope
- Runtime/Lab boundary verdict
- NOAPI/read-only verdict
- Implementation Go/No-Go verdict
- Next safe recommendation
