# NEWS-B FIX 2 Timer Activation Targeted Apply

- stage: `NEWS_B_FIX_2_TIMER_ACTIVATION_TARGETED_APPLY`
- generated_at_utc: `2026-07-08T12:28:09.721881+00:00`
- decision: `OK_NEWS_B_FIX_2_TIMER_ACTIVATED`
- next_step: `NEWS_B_FIX_2_POST_ACTIVATION_AUDIT_NOAPI`

## Authority

- targeted_systemd_timer_apply: `True`
- timer_enable: `True`
- timer_start: `True`
- service_start_direct: `False`
- systemd_daemon_reload: `True`
- systemd_reset_failed_service: `True`
- unit_file_write: `False`
- real_db_write_by_this_script: `False`
- db_schema_write: `False`
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

- timer_active_after: `active`
- timer_enabled_after: `enabled`
- list_timers_has_schedule: `True`
- journal_status_209_stdout_count: `0`
- journal_failed_set_up_stdout_count: `0`
- journal_invalidargument_count: `0`
- journal_rc2_count: `0`
- raw_count_before: `269`
- raw_count_after: `269`
- match_count_after: `47`
- signal_count_after: `47`
- score_count_after: `47`
- freshness_count_after: `1`
- fail_count: `0`
- warn_count: `0`

## Findings

- `OK` FIX1_POST_AUDIT_REFERENCE_READ: Fix1 post-audit artifact okundu.
- `OK` TIMER_ENABLE_NOW_RC_ZERO: systemctl enable --now timer rc=0.
- `OK` TIMER_ACTIVE_AFTER_ENABLE: Timer active.
- `OK` TIMER_ENABLED_AFTER_ENABLE: Timer enabled.
- `OK` LIST_TIMERS_HAS_NEXT_SCHEDULE: list-timers içinde NEWS timer schedule görünüyor.
- `OK` TIMER_TRIGGERS_SERVICE: Timer service'i trigger ediyor.
- `OK` SERVICE_LAST_RESULT_STILL_CLEAN: Service last result success/0.
- `OK` STDOUT_209_NOT_REAPPEARED: Timer activation sonrası 209/STDOUT yok.
- `OK` INVALIDARGUMENT_NOT_SEEN: Timer activation sonrası INVALIDARGUMENT yok.
- `OK` DOWNSTREAM_47_CHAIN_PRESERVED: Downstream korunuyor: 47/47/47
- `OK` RAW_COUNT_NOT_DECREASING: Raw count azalmadı: 269 -> 269
- `OK` TIMER_INTERVAL_PRESENT: Timer interval alanı mevcut.

## Timer Unit Parsed

- on_boot_sec: `[]`
- on_unit_active_sec: `['20min']`
- on_active_sec: `['20min']`
- accuracy_sec: `['30s']`
- unit: `['tokenoskobi-news-radar-refresh.service']`
- wanted_by: `['timers.target']`

```text
[Unit]
Description=Run Tokenoskobi News Radar Refresh every 20 minutes
[Timer]
OnActiveSec=20min
OnUnitActiveSec=20min
AccuracySec=30s
RandomizedDelaySec=0
Persistent=false
Unit=tokenoskobi-news-radar-refresh.service
[Install]
WantedBy=timers.target
```

## Apply

- daemon_reload: rc=`0` stdout=`` stderr=``
- reset_failed_service: rc=`1` stdout=`` stderr=`Failed to reset failed state of unit tokenoskobi-news-radar-refresh.service: Unit tokenoskobi-news-radar-refresh.service not loaded.`
- enable_now_timer: rc=`0` stdout=`` stderr=`Created symlink '/etc/systemd/system/timers.target.wants/tokenoskobi-news-radar-refresh.timer' → '/etc/systemd/system/tokenoskobi-news-radar-refresh.timer'.`

## list-timers After

```text
NEXT                          LEFT LAST PASSED UNIT                                 ACTIVATES
Wed 2026-07-08 15:48:04 EEST 19min -         - tokenoskobi-news-radar-refresh.timer tokenoskobi-news-radar-refresh.service

1 timers listed.
```

## service_show After

```text
Result=success
ExecMainStatus=0
ExecStart={ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
StandardOutput=append
StandardError=append
ActiveState=inactive
SubState=dead
FragmentPath=/etc/systemd/system/tokenoskobi-news-radar-refresh.service
UnitFileState=static
```

## timer_show After

```text
NextElapseUSecRealtime=
LastTriggerUSec=
Result=success
Triggers=tokenoskobi-news-radar-refresh.service
ActiveState=active
SubState=waiting
UnitFileState=enabled
```

## DB Counts

| Table | Before | After |
|---|---:|---:|
| news_raw_feed_events | 269 | 269 |
| news_token_match_events | 47 | 47 |
| news_signal_events | 47 | 47 |
| news_score_events_v1 | 47 | 47 |
| news_runtime_freshness_v1 | 1 | 1 |

## Journal Since Activation

- since_utc: `2026-07-08T12:27:53.702966+00:00`
- cmd_rc: `0`
- line_count: `1`
- status_209_stdout_count: `0`
- failed_set_up_stdout_count: `0`
- failed_at_step_stdout_count: `0`
- no_such_file_count: `0`
- invalidargument_count: `0`
- rc2_count: `0`
- traceback_count: `0`
- error_count: `0`
- failed_count: `0`
- started_count: `1`
- finished_count: `0`
- deactivated_successfully_count: `0`

```text
2026-07-08T15:28:04+03:00 v2202604354387455154 systemd[1]: Started tokenoskobi-news-radar-refresh.timer - Run Tokenoskobi News Radar Refresh every 20 minutes.
```
