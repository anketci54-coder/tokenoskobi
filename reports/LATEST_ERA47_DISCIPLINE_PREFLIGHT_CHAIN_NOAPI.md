# ERA47 DISCIPLINE PREFLIGHT CHAIN NOAPI

- Updated UTC: 2026-07-08T10:34:05.417432Z
- Base HEAD: `9bd7bf9730f06a83c03bad9b8115520256c94ddd`
- Status: `CONSOLIDATED`
- Next real software step: `ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI`

## Why this exists

ERA47 through ERA51 were one logical safety/preflight chain.
They are now consolidated under one parent:

`ERA47_DISCIPLINE_PREFLIGHT_CHAIN_NOAPI`

## Canonical Substeps

- `ERA47A_PLAN_VALIDATION_NOAPI`
- `ERA47B_REACHABILITY_CLASSIFICATION_NOAPI`
- `ERA47C_ACTIVE_SURFACE_FALSE_POSITIVE_REVIEW_NOAPI`
- `ERA47D_ACTIVE_RUNTIME_RISK_DECISION_NOAPI`
- `ERA47E_DISCIPLINE_IMPLEMENTATION_GO_NOGO_NOAPI`

## Historical Aliases

- Old `ERA48` = now `ERA47B`
- Old `ERA49` = now `ERA47C`
- Old `ERA50` = now `ERA47D`
- Old `ERA51` = now `ERA47E`

## Rule From Now On

Do not create a new ERA for plan/test/audit/decision inside the same logical work.

Use:

- `ERA52A`
- `ERA52B`
- `ERA52C`
- `ERA52A_1` only when needed

## Deadline Correction

The next work must produce small working code:

`ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI`

No new decision chain before that.
