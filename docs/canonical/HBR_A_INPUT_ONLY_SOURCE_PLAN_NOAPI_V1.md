# HBR-A Input Only Source Plan NOAPI V1

Generated UTC: 2026-07-10T08:34:49.666881+00:00

Decision: OK_HBR_A_INPUT_ONLY_SOURCE_PLAN_NOAPI

## Purpose

Select historical input sources and settled time windows without fetching data, without fetching outcomes, and without writing to production DB.

## Source candidates

```text
CoinDesk RSS
Cointelegraph RSS
Settled input windows
2026-06-01T00:00:00+00:00 → 2026-06-15T23:59:59+00:00
2026-06-16T00:00:00+00:00 → 2026-06-30T23:59:59+00:00
Hard limits for next step
max_total_input_items = 150
max_items_per_source = 75
max_sources = 2
production_db_insert = false
write_target = tempfiles_only
Forbidden before prediction seal
outcome_label
price_after
future_return_pct
result
win_loss
success_failure
future_price
post_event_price_change
score_comparison
Next

HBR_B_INPUT_ONLY_FETCH_AND_SEAL_WITH_NETWORK_TEMPFILES
