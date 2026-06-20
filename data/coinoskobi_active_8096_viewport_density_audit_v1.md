# COINOSKOBI_ACTIVE_8096_VIEWPORT_DENSITY_AUDIT_NOAPI

## Status

- Final OK: `True`
- Density status: `PATCH_REQUIRED`
- Density score: `46`
- Warnings: `NO_CLAMP_RESPONSIVE_FONT_OR_SPACING_FOUND, NO_MAX_HEIGHT_CONTROL_FOUND, PADDING_TOO_LARGE_FOR_100_PERCENT_VIEWPORT, GAP_TOO_LARGE_FOR_100_PERCENT_VIEWPORT, GRID_MINMAX_CARD_WIDTH_TOO_WIDE_FOR_COMPACT_VIEW, BORDER_RADIUS_VISUAL_DENSITY_HIGH`

## User visual symptom

At 50% zoom the dashboard fits, but at 100% zoom not all panels are visible. This is classified as a viewport density issue, not a data/risk-engine issue.

## Recommended patch direction

- Do not change the 8-center architecture.
- Do not change DB/API/live/paper/auto.
- Add active 8096 compact density CSS only.
- Target browser 100% zoom at 1366x768 and 1536x864.
- Reduce spacing, card min width, card padding, hero heights, sidebar density.
- Add controlled scroll only where needed.
- Keep Risk & Güvenlik block mounted under existing active shell.

## Next phase

`COINOSKOBI_ACTIVE_8096_VIEWPORT_DENSITY_PATCH_PLAN_NOAPI`
