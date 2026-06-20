# COINOSKOBI_ACTIVE_8096_GLOBAL_SHELL_DENSITY_V2_REPLACE_PLAN_FIX1_NOAPI

## Final

`PASS_GLOBAL_SHELL_DENSITY_V2_REPLACE_PLAN_FIX1_READY_NOAPI`

## Fix

- Previous replacement plan failed because the replacement CSS text contained a blocked literal token in a comment.
- This fix rewrites the replacement CSS text without that token.
- No active panel write happened.

## Replacement strategy

- Replace only the existing global V2 block between current V2 markers.
- Do not touch V1 global patch.
- Do not touch risk-security patch/block.
- Do not mutate active data, risk data, DB, service, timer, nginx, paper/live/auto.

## Required approval

`COINOSKOBI ACTIVE 8096 GLOBAL SHELL DENSITY V2 REPLACE REAL için onay veriyorum`

## Next

`COINOSKOBI_ACTIVE_8096_GLOBAL_SHELL_DENSITY_V2_REPLACE_REAL_AFTER_EXPLICIT_APPROVAL`
