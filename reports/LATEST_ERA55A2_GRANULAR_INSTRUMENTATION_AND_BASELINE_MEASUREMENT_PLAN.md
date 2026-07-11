# ERA55A_2 GRANULAR INSTRUMENTATION AND BASELINE MEASUREMENT PLAN

Result: `OK_PLAN_LOCKED_NO_LIVE_MUTATION`

ERA55 status: `OPEN`

Live runtime/DB/service/timer/queue/panel mutation: `false`

## A1 Facts Used

```json
{
  "a1_result": "WARN_P0_FINDINGS_RECORDED_READONLY",
  "service_type": "oneshot",
  "service_result": "success",
  "timeout_start_seconds": 70,
  "runtime_max": "infinity",
  "restart_policy": "no",
  "kill_mode": "control-group",
  "timer_active_state": "active",
  "timer_sub_state": "waiting",
  "timer_enabled_state": "enabled",
  "timer_cadence_seconds": 1200,
  "timer_accuracy": "30s",
  "timer_randomized_delay": "0",
  "last_runner_duration_ms": 726.154,
  "timer_safety_margin_ms": null,
  "queue_capacity": 50,
  "queue_policy": "PRIORITY_DESC_THEN_HOT_UID_TOP_50",
  "queue_drop_ledger_detected": false,
  "queue_silent_truncation_risk": true,
  "sqlite_journal_mode": "delete",
  "sqlite_synchronous": 2,
  "sqlite_integrity": "ok",
  "sqlite_quick_check": "ok"
}
```

## Measurement Stages

- `TIMER_WAIT` → `timer_wait_ms` — external read-only observation
- `RUNNER_TOTAL` → `runner_execution_ms` — external read-only observation
- `RAW_PRODUCER` → `raw_producer_observed_ms` — SQLite mode=ro polling; no write
- `DERIVED_REFRESH` → `derived_refresh_observed_ms` — SQLite mode=ro polling; no write
- `HOT_GATEWAY` → `hot_gateway_observed_ms` — read-only file observation
- `PANEL_BRIDGE` → `panel_propagation_observed_ms` — read-only file observation
- `QUEUE_RESIDENCE_PROXY` → `queue_residence_proxy_ms` — read-only JSON correlation

## Baseline Profiles

- `HISTORICAL_24H` — Immediate runner duration and cadence distribution; runner invocation: `false`
- `NATURAL_NEXT_CYCLE` — One end-to-end stage propagation observation; runner invocation: `false`
- `HOT_STEADY_STATE` — Steady-state variance across consecutive cycles; runner invocation: `false`
- `LOGICAL_COLD_START` — First natural cycle after reboot or at least two timer cadences without a completed cycle; runner invocation: `false`

## Collector Contract

```json
{
  "mode": "EXTERNAL_READONLY_OBSERVER",
  "must_not_import_runtime_modules": true,
  "must_not_invoke_runner": true,
  "must_not_start_or_restart_service": true,
  "must_not_enable_disable_or_edit_timer": true,
  "sqlite_uri": "file:/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite?mode=ro",
  "sqlite_query_only": true,
  "polling_interval_ms": 250,
  "maximum_observation_window": "next natural timer cycle plus completion buffer",
  "output_atomic_write_only": true,
  "output_location": "data/control and reports only",
  "failure_behavior": "FAIL_CLOSED_WITH_PARTIAL_EVIDENCE",
  "hash_or_count_before_after_required": true,
  "git_clean_before_and_after_required": true
}
```

## Hard Gates

```json
{
  "silent_event_loss_allowed": false,
  "data_correctness_regression_allowed": false,
  "manual_runner_execution_allowed": false,
  "production_burst_load_allowed": false,
  "service_or_timer_change_allowed": false,
  "watchdog_apply_allowed": false,
  "index_apply_allowed": false,
  "journal_mode_change_allowed": false,
  "cache_apply_allowed": false,
  "queue_policy_change_allowed": false,
  "incremental_write_apply_allowed": false,
  "database_write_allowed": false,
  "panel_write_allowed": false,
  "trade_wallet_signing_order_authority": 0
}
```

## Red Team Gates

- **P0 QUEUE_OVERFLOW_SILENT_TRUNCATION** — candidate_count, admitted_count and overflow_count must be measured; no claim of zero loss without ledger
- **P0 TIMER_RUNNER_MARGIN** — timer interval, timeout, p50/p95/max runner duration and overlap evidence must be reported
- **P0 DATA_CORRECTNESS** — counts, UIDs, authority flags and integrity checks must remain correct
- **P1 PANEL_PROPAGATION_VISIBILITY** — DB-to-gateway-to-panel timing must be observable or explicitly marked unmeasurable
- **P1 SQLITE_DURABILITY** — no PRAGMA mutation in baseline; temp-copy recovery testing required before any mode change

## Decision

- Measurement plan is locked.
- No runner instrumentation was applied.
- No systemd unit was changed.
- No SQLite PRAGMA was changed.
- No queue policy was changed.
- No production burst test was executed.
- Next: `ERA55A_3_NATURAL_CYCLE_BASELINE_COLLECTION`.
