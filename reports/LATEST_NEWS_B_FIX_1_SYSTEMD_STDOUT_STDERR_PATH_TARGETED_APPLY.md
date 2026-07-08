# NEWS-B FIX 1 Systemd STDOUT STDERR Path Targeted Apply

- stage: `NEWS_B_FIX_1_SYSTEMD_STDOUT_STDERR_PATH_TARGETED_APPLY`
- generated_at_utc: `2026-07-08T12:17:42.251456+00:00`
- decision: `OK_NEWS_B_FIX_1_STDOUT_STDERR_PATH_CLEARED`
- next_step: `NEWS_B_FIX_1_POST_APPLY_AUDIT_NOAPI`

## Authority

- targeted_filesystem_apply: `True`
- created_log_directory: `True`
- systemd_daemon_reload: `True`
- service_start_once: `True`
- timer_enable: `False`
- timer_start: `False`
- timer_restart: `False`
- unit_file_write: `False`
- db_schema_write: `False`
- db_data_write_by_this_script: `False`
- panel_write: `False`
- runner_code_change: `False`
- matcher_code_change: `False`
- boot_update: `False`
- runtime_update: `False`
- external_api_call_by_this_script: `False`
- wallet: `False`
- signing: `False`
- live_trade: `False`
- paper_trade: `False`
- repo_artifact_write: `True`

## Summary

- service_start_rc: `0`
- stdio_missing_parent_after: `0`
- journal_status_209_stdout_after: `0`
- journal_failed_set_up_stdout_after: `0`
- journal_invalidargument_after: `0`
- raw_count_after: `269`
- match_count_after: `47`
- signal_count_after: `47`
- score_count_after: `47`
- freshness_count_after: `1`
- fail_count: `0`
- warn_count: `0`

## Findings

- `OK` LOG_DIR_CREATED_OR_EXISTS: logs/news_radar klasörü mevcut.
- `OK` STDIO_PARENT_EXISTS_AFTER: StandardOutput/StandardError parent path mevcut.
- `OK` STDOUT_209_CLEARED_AFTER_START: Yeni service start denemesinde 209/STDOUT görülmedi.
- `OK` SERVICE_START_RC_ZERO: systemctl start service rc=0.
- `OK` DB_CHAIN_PRESERVED: DB chain preserved raw/match/signal/score=269/47/47/47
- `OK` INVALIDARGUMENT_NOT_SEEN_AFTER_START: Yeni start sonrası INVALIDARGUMENT görülmedi.

## Stdio Path Checks

| Phase | Key | Raw | Path | Parent Exists | Target Exists |
|---|---|---|---|---:|---:|
| before | StandardOutput | `append` | `None` | None | None |
| before | StandardError | `append` | `None` | None | None |
| after | StandardOutput | `append` | `None` | None | None |
| after | StandardError | `append` | `None` | None | None |

## Apply Commands

- mkdir_log_dir: rc=`0` stdout=`/root/tokenoskobi_clean_v1/logs/news_radar` stderr=``
- daemon_reload: rc=`0` stdout=`` stderr=``
- reset_failed_service: rc=`0` stdout=`` stderr=``
- start_service_once: rc=`0` stdout=`` stderr=``

## Journal After Apply

- cmd_rc: `0`
- line_count: `3`
- status_209_stdout_count: `0`
- failed_set_up_stdout_count: `0`
- failed_at_step_stdout_count: `0`
- no_such_file_count: `0`
- invalidargument_count: `0`
- rc2_count: `0`
- traceback_count: `0`
- error_count: `0`
- failed_count: `0`
- postprocess_count: `0`
- return_rc_count: `0`

```text
2026-07-08T15:17:38+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.
2026-07-08T15:17:38+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
```

## DB Counts After

| Table | Exists | Count | Max TS |
|---|---:|---:|---|
| news_raw_feed_events | True | 269 | 2026-07-08T12:17:38.011514+00:00 |
| news_token_match_events | True | 47 | 2026-07-06T06:44:10.282634+00:00 |
| news_signal_events | True | 47 | 2026-07-06T06:44:10.288481+00:00 |
| news_score_events_v1 | True | 47 | 2026-07-06T06:44:10.288486+00:00 |
| news_runtime_freshness_v1 | True | 1 | 2026-07-06T06:44:10.294353+00:00 |
