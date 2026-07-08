# NEWS-B FIX 1 Post Apply Audit NOAPI

- stage: `NEWS_B_FIX_1_POST_APPLY_AUDIT_NOAPI`
- generated_at_utc: `2026-07-08T12:23:33.254968+00:00`
- decision: `OK_NEWS_B_FIX_1_POST_APPLY_AUDIT_CLEAN`
- next_step: `NEWS_B_FIX_2_TIMER_ACTIVATION_TARGETED_APPLY_REQUIRES_APPROVAL`

## Authority

- readonly_audit: `True`
- real_db_write: `False`
- db_schema_write: `False`
- panel_write: `False`
- runner_code_change: `False`
- matcher_code_change: `False`
- unit_file_write: `False`
- systemd_start: `False`
- systemd_stop: `False`
- systemd_restart: `False`
- systemd_daemon_reload: `False`
- timer_enable: `False`
- timer_start: `False`
- timer_restart: `False`
- boot_update: `False`
- runtime_update: `False`
- external_api_call: `False`
- wallet: `False`
- signing: `False`
- live_trade: `False`
- paper_trade: `False`
- repo_artifact_write: `True`

## Summary

- raw_count: `269`
- match_count: `47`
- signal_count: `47`
- score_count: `47`
- freshness_count: `1`
- service_active: `inactive`
- timer_active: `inactive`
- timer_enabled: `disabled`
- journal_status_209_stdout_count: `0`
- journal_failed_set_up_stdout_count: `0`
- journal_invalidargument_count: `0`
- journal_rc2_count: `0`
- fail_count: `0`
- warn_count: `0`

## Findings

- `OK` FIX_1_ARTIFACT_READ: Fix-1 artifact okundu.
- `OK` LOG_DIR_EXISTS: logs/news_radar klasörü mevcut.
- `OK` LOG_FILES_EXIST: stdout/stderr log dosyaları mevcut.
- `OK` STDOUT_209_REMAINS_CLEARED: Fix sonrası journal penceresinde 209/STDOUT yok.
- `OK` INVALIDARGUMENT_REMAINS_ABSENT: Fix sonrası INVALIDARGUMENT yok.
- `OK` SERVICE_RESULT_CLEAN: Service Result=success ve ExecMainStatus=0.
- `OK` SERVICE_STATE_ACCEPTABLE: Service state kabul edilebilir: inactive
- `OK` TIMER_STILL_DISABLED_BY_DESIGN: Timer hâlâ disabled/inactive; Fix-1 kapsamında beklenen durum.
- `OK` DB_CHAIN_PRESERVED_AFTER_FIX: DB chain korunuyor: 269/47/47/47
- `OK` RAW_COUNT_NOT_DECREASING: Raw count fix sonrasına göre azalmadı; delta=0

## DB Current

| Table | Exists | Count | Max TS |
|---|---:|---:|---|
| news_raw_feed_events | True | 269 | 2026-07-08T12:17:38.011514+00:00 |
| news_token_match_events | True | 47 | 2026-07-06T06:44:10.282634+00:00 |
| news_signal_events | True | 47 | 2026-07-06T06:44:10.288481+00:00 |
| news_score_events_v1 | True | 47 | 2026-07-06T06:44:10.288486+00:00 |
| news_runtime_freshness_v1 | True | 1 | 2026-07-06T06:44:10.294353+00:00 |

## Service / Timer

- service_is_active: rc=`3` stdout=`inactive` stderr=``
- service_is_enabled: rc=`0` stdout=`static` stderr=``
- timer_is_active: rc=`3` stdout=`inactive` stderr=``
- timer_is_enabled: rc=`1` stdout=`disabled` stderr=``

### service_show
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

### timer_show
```text
NextElapseUSecRealtime=
LastTriggerUSec=
Result=success
ActiveState=inactive
SubState=dead
UnitFileState=disabled
```

### list_timers
```text
NEXT LEFT LAST PASSED UNIT ACTIVATES

0 timers listed.
```

## Journal Since Fix

- since_utc: `2026-07-08T12:15:42.251456+00:00`
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
- finished_count: `1`
- deactivated_successfully_count: `1`

```text
2026-07-08T15:17:38+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.
2026-07-08T15:17:38+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
```
