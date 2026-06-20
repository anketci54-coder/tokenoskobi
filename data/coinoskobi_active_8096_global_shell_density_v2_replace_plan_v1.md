# COINOSKOBI_ACTIVE_8096_GLOBAL_SHELL_DENSITY_V2_REPLACE_PLAN_NOAPI

## Final

`REVIEW_REQUIRED_GLOBAL_SHELL_DENSITY_V2_REPLACE_PLAN_NOAPI`

## Why replace

- V2 technical state is valid, but desktop 100% visual failed.
- Current V2 is over-compressed and creates overlap/clipping.
- Mobile portrait flow is readable and should be preserved.
- Do not add V3. Replace the existing V2 block.

## Replacement strategy

- Replace only the existing global V2 block between current V2 markers.
- Do not touch V1 global patch.
- Do not touch risk-security patch/block.
- Do not mutate active data, risk data, DB, service, timer, nginx, paper/live/auto.

## Replacement visual target

- Desktop: remove right-sidebar overlap.
- Desktop: hero icon not clipped.
- Desktop: sections no longer collide.
- Mobile portrait: preserve current good card flow.
- Mobile landscape: keep compact but less crushed.

## Required approval

`COINOSKOBI ACTIVE 8096 GLOBAL SHELL DENSITY V2 REPLACE REAL için onay veriyorum`

## Next

`REVIEW_GLOBAL_SHELL_DENSITY_V2_REPLACE_PLAN_FAILURE`
