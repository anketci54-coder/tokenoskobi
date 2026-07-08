# ERA45 REACHABILITY FIX AND SPEED BASELINE NOAPI

- Created UTC: 2026-07-08T06:39:57.335580+00:00
- Decision: `WARN_ERA45_REACHABILITY_FIX_AND_SPEED_BASELINE_BLOCKERS_REMAIN`
- Next step: `ERA45_REACHABILITY_FIX_OR_GATE_REQUIRED_NOAPI`
- News active: `True`
- Provider active: `True`
- High findings: 2

## Speed Baseline
- `compile_active_tools`: `456.764 ms`, ok=`True`
- `parse_json_surface`: `25.339 ms`, ok=`True`
- `sqlite_readonly_metadata`: `118.817 ms`, ok=`True`
- `scan_public_leakage_keywords`: `4.882 ms`, ok=`True`
- `scan_shell_subprocess_surface`: `15.089 ms`, ok=`True`
- `scan_write_mutation_surface`: `0.28 ms`, ok=`False`
- `large_non_archive_files`: `119.105 ms`, ok=`True`

## Findings
- **HIGH `NEWS_RUNNER_ACTIVE`** — `ERA43_REAL_PLANNING_BLOCKED_UNTIL_GATE_OR_DISABLE`
- **HIGH `PROVIDER_VAULT_ACTIVE`** — `ERA43_REAL_PLANNING_BLOCKED_UNTIL_GATE_OR_DISABLE`
- **MEDIUM `WATER_POOLING_NON_ARCHIVE`** — `BACKLOG_CLASSIFY`
