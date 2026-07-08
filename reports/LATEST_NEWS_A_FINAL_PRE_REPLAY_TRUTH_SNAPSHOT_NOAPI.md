# NEWS-A Final Pre-Replay Truth Snapshot NOAPI

- stage: `NEWS_A_FINAL_PRE_REPLAY_TRUTH_SNAPSHOT_NOAPI`
- generated_at_utc: `2026-07-08T11:49:21.916798+00:00`
- decision: `WARN_NEWS_A_CURRENT_TRUTH_CAPTURED_REVIEW_REQUIRED`
- selected_db: `/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite`

## Authority

- readonly_db_open_mode: `sqlite_uri_mode_ro_query_only`
- real_db_write: `False`
- panel_write: `False`
- boot_update: `False`
- runtime_update: `False`
- systemd_start: `False`
- systemd_stop: `False`
- systemd_restart: `False`
- timer_restart: `False`
- external_api_call: `False`
- provider_call: `False`
- wallet: `False`
- signing: `False`
- live_trade: `False`
- paper_trade: `False`
- repo_artifact_write: `True`

## Boot / Runtime / Current DB Drift Table

| Metric | PROJECT_BOOT | PROJECT_RUNTIME | Current DB | Delta DB-Boot | Drift |
|---|---:|---:|---:|---:|---|
| news_raw_feed_events | 151 | not_found | 250 | 99 | YES |
| news_token_match_events | 0 | not_found | 47 | 47 | YES |
| news_signal_events | 0 | not_found | 47 | 47 | YES |
| news_score_events_v1 | 0 | not_found | 47 | 47 | YES |
| news_runtime_freshness_v1 | not_found | not_found | 1 | n/a | BOOT_COUNT_NOT_FOUND |

## DB Snapshot

| Table | Exists | Count | Timestamp Col | Max TS | Error |
|---|---:|---:|---|---|---|
| news_raw_feed_events | True | 250 | fetched_at_utc | 2026-07-06T13:14:21.914417+00:00 | None |
| news_token_match_events | True | 47 | created_at_utc | 2026-07-06T06:44:10.282634+00:00 | None |
| news_signal_events | True | 47 | created_at_utc | 2026-07-06T06:44:10.288481+00:00 | None |
| news_score_events_v1 | True | 47 | created_at_utc | 2026-07-06T06:44:10.288486+00:00 | None |
| news_runtime_freshness_v1 | True | 1 | created_at_utc | 2026-07-06T06:44:10.294353+00:00 | None |

## Backup Check

- backup_path: `/root/tokenoskobi_clean_v1/data/backups/news_real_apply/tokenoskobi_clean_v1.sqlite.before_n18_n19_n20_news_real_apply_20260706T064410Z`
- exists: `True`
- size_bytes: `5517312`

## Systemd Snapshot

### tokenoskobi-news-radar-refresh.timer
- active: `inactive`
- enabled: `disabled`
- Result=success
- ActiveState=inactive
- SubState=dead
- FragmentPath=/etc/systemd/system/tokenoskobi-news-radar-refresh.timer
- UnitFileState=disabled

### tokenoskobi-news-radar-refresh.service
- active: `failed`
- enabled: `static`
- Result=exit-code
- NRestarts=0
- ExecMainStatus=209
- ExecStart={ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
- ActiveState=failed
- SubState=failed
- FragmentPath=/etc/systemd/system/tokenoskobi-news-radar-refresh.service
- UnitFileState=static

### list-timers
```text
NEXT LEFT LAST PASSED UNIT ACTIVATES

0 timers listed.
```

## Journal / Log Summary

- cmd_rc: `0`
- line_count: `160`
- invalidargument_count: `0`
- rc2_count: `27`
- return_rc_count: `0`
- postprocess_count: `0`
- traceback_count: `0`
- error_count: `0`
- failed_count: `107`
- finished_successfully_count: `0`

### Interesting journal lines tail
```text
2026-07-08T08:49:49+03:00 v2202604354387455154 (python3)[2660188]: tokenoskobi-news-radar-refresh.service: Failed to set up standard output: No such file or directory
2026-07-08T08:49:49+03:00 v2202604354387455154 (python3)[2660188]: tokenoskobi-news-radar-refresh.service: Failed at step STDOUT spawning /usr/bin/python3: No such file or directory
2026-07-08T08:49:49+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=209/STDOUT
2026-07-08T08:49:49+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
2026-07-08T08:49:49+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
2026-07-08T09:09:54+03:00 v2202604354387455154 (python3)[2685139]: tokenoskobi-news-radar-refresh.service: Failed to set up standard output: No such file or directory
2026-07-08T09:09:54+03:00 v2202604354387455154 (python3)[2685139]: tokenoskobi-news-radar-refresh.service: Failed at step STDOUT spawning /usr/bin/python3: No such file or directory
2026-07-08T09:09:54+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=209/STDOUT
2026-07-08T09:09:54+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
2026-07-08T09:09:54+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
2026-07-08T09:29:54+03:00 v2202604354387455154 (python3)[2707971]: tokenoskobi-news-radar-refresh.service: Failed to set up standard output: No such file or directory
2026-07-08T09:29:54+03:00 v2202604354387455154 (python3)[2707971]: tokenoskobi-news-radar-refresh.service: Failed at step STDOUT spawning /usr/bin/python3: No such file or directory
2026-07-08T09:29:54+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=209/STDOUT
2026-07-08T09:29:54+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
2026-07-08T09:29:54+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
2026-07-08T09:49:54+03:00 v2202604354387455154 (python3)[2732438]: tokenoskobi-news-radar-refresh.service: Failed to set up standard output: No such file or directory
2026-07-08T09:49:54+03:00 v2202604354387455154 (python3)[2732438]: tokenoskobi-news-radar-refresh.service: Failed at step STDOUT spawning /usr/bin/python3: No such file or directory
2026-07-08T09:49:54+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=209/STDOUT
2026-07-08T09:49:54+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
2026-07-08T09:49:54+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
```

## Panel / Readmodel Freshness

| Panel | Exists | generated_at_utc | mtime_utc | generated_age_sec | mtime_age_sec | Freshness | stale_data_fresh_file |
|---|---:|---|---|---:|---:|---|---:|
| news | False | None | None | None | None | UNKNOWN_TIMESTAMP | False |
| command | False | None | None | None | None | UNKNOWN_TIMESTAMP | False |

## Canonical State Integrity Check

- runtime_mode: `None`
- runtime_next_safe_step: `{'name': 'NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW', 'status': 'READY'}`
- runtime_status: `None`
- runtime_last_action: `{'timestamp': '2026-07-08T11:06:16.159789Z', 'task': 'ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI', 'result': 'OK_ERA52_MINIMAL_READONLY_SCAFFOLD_CLOSED', 'artifact': 'data/control/era52_discipline_layer_minimal_readonly_scaffold_noapi_v1.json'}`
- runtime_last_activity_candidates_count: `12`

- project_master_state_root: exists=`False`, mentions_NEWS_RUNTIME_STABILIZATION=`None`, mentions_ERA52=`None`
- project_handoff_root: exists=`False`, mentions_NEWS_RUNTIME_STABILIZATION=`None`, mentions_ERA52=`None`
- master_state_06: exists=`True`, mentions_NEWS_RUNTIME_STABILIZATION=`True`, mentions_ERA52=`True`
- handoff_07: exists=`True`, mentions_NEWS_RUNTIME_STABILIZATION=`True`, mentions_ERA52=`True`
- almanac_04: exists=`True`, mentions_NEWS_RUNTIME_STABILIZATION=`True`, mentions_ERA52=`True`
- latest_tk_ai_handoff: exists=`True`, mentions_NEWS_RUNTIME_STABILIZATION=`True`, mentions_ERA52=`True`

## Findings

- `OK` DB_SELECTED: Selected DB: /root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite
- `OK` RAW_NEWS_PRESENT: Raw news count: 250
- `OK` DOWNSTREAM_47_CHAIN_PRESENT: match/signal/score = 47/47/47
- `OK` FRESHNESS_TABLE_PRESENT: news_runtime_freshness_v1 count: 1
- `OK` REAL_APPLY_BACKUP_EXISTS: N18/N19/N20 real apply backup dosyası yerinde.
- `WARN` NEWS_TIMER_NOT_ACTIVE: NEWS timer active görünmüyor.
- `WARN` NEWS_SERVICE_LAST_RESULT_NOT_CLEAN: Service show success/0 net göstermiyor.
- `OK` JOURNAL_INVALIDARGUMENT_NOT_SEEN: journal tail içinde INVALIDARGUMENT görülmedi.
- `WARN` POSTPROCESS_TRACE_NOT_SEEN: postprocess izi görülmedi; NEWS-B için non-blocking dead-code adayı.
- `WARN` BOOT_DRIFT_CONFIRMED: PROJECT_BOOT NEWS sayımları current DB ile farklı.
- `WARN` PANEL_FRESHNESS_UNKNOWN: Timestamp bilinmeyen panel/readmodel: news,command

## Next

```text
NEWS_B_RUNNER_TIMER_JOURNAL_ARGV_AUDIT_NOAPI
```
