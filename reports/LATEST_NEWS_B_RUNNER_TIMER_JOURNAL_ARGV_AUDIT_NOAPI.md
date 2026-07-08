# NEWS-B Runner / Timer / Journal / ARGV Audit NOAPI

- stage: `NEWS_B_RUNNER_TIMER_JOURNAL_ARGV_AUDIT_NOAPI`
- generated_at_utc: `2026-07-08T11:59:25.780571+00:00`
- decision: `FAIL_NEWS_B_STDOUT_PATH_ROOT_CAUSE_CONFIRMED`
- next_step: `NEWS_B_FIX_1_SYSTEMD_STDOUT_STDERR_PATH_TARGETED_APPLY_REQUIRES_APPROVAL`

## Authority

- readonly: `True`
- real_db_write: `False`
- panel_write: `False`
- boot_update: `False`
- runtime_update: `False`
- systemd_start: `False`
- systemd_stop: `False`
- systemd_restart: `False`
- timer_restart: `False`
- unit_file_write: `False`
- external_api_call: `False`
- provider_call: `False`
- wallet: `False`
- signing: `False`
- live_trade: `False`
- paper_trade: `False`
- repo_artifact_write: `True`

## Summary

- service_active: `failed`
- service_enabled: `static`
- timer_active: `inactive`
- timer_enabled: `disabled`
- stdio_path_rows: `2`
- stdio_missing_parent_count: `2`
- journal_status_209_stdout_count: `37`
- journal_failed_set_up_stdout_count: `36`
- journal_invalidargument_count: `0`
- journal_rc2_count: `37`
- postprocess_trace_count: `31`
- fail_count: `2`
- warn_count: `4`

## Findings

- `OK` SERVICE_UNIT_READ: Service unit okundu.
- `OK` TIMER_UNIT_READ: Timer unit okundu.
- `OK` EXECSTART_FOUND: ExecStart bulundu.
- `OK` EXECSTART_RUNNER_BOUND: ExecStart NEWS runner'a bağlı görünüyor.
- `OK` RUNNER_EXISTS: runner dosyası var.
- `OK` ORIGINAL_RUNNER_EXISTS: original_runner dosyası var.
- `OK` MATCHER_EXISTS: matcher dosyası var.
- `FAIL` STDIO_PARENT_PATH_MISSING: StandardOutput/StandardError parent path eksik.
- `FAIL` JOURNAL_STDOUT_209_CONFIRMED: journal 209/STDOUT ve StandardOutput kurulum hatasını doğruluyor.
- `OK` INVALIDARGUMENT_NOT_SEEN: journal tail içinde INVALIDARGUMENT yok.
- `WARN` RC2_OR_STATUS2_SEEN: journal rc=2/status=2 count: 37
- `OK` POSTPROCESS_TRACE_SEEN: postprocess trace/log count: 31
- `WARN` RUNNER_POSTPROCESS_DEAD_CODE_SUSPECT: Runner içinde return sonrası _postprocess dead-code adayı.
- `WARN` TIMER_NOT_ACTIVE: Timer active değil: inactive
- `WARN` TIMER_NOT_ENABLED: Timer enabled değil: disabled
- `OK` NEWS_A_JSON_READ: NEWS-A JSON okundu.

## Service Unit Parsed

### ExecStart
```text
ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py
```

### StandardOutput / StandardError
```text
StandardOutput=append:/root/tokenoskobi_clean_v1/logs/news_radar/news_radar_refresh.log
StandardError=append:/root/tokenoskobi_clean_v1/logs/news_radar/news_radar_refresh.err.log
```

### Stdio Path Checks

| Key | Raw | Path | Parent Exists | Target Exists |
|---|---|---|---:|---:|
| StandardOutput | `append:/root/tokenoskobi_clean_v1/logs/news_radar/news_radar_refresh.log` | `/root/tokenoskobi_clean_v1/logs/news_radar/news_radar_refresh.log` | False | False |
| StandardError | `append:/root/tokenoskobi_clean_v1/logs/news_radar/news_radar_refresh.err.log` | `/root/tokenoskobi_clean_v1/logs/news_radar/news_radar_refresh.err.log` | False | False |

## Systemd Status

- service_is_active: rc=`3` stdout=`failed` stderr=``
- service_is_enabled: rc=`0` stdout=`static` stderr=``
- timer_is_active: rc=`3` stdout=`inactive` stderr=``
- timer_is_enabled: rc=`1` stdout=`disabled` stderr=``

### list-timers
```text
NEXT LEFT LAST PASSED UNIT ACTIVATES

0 timers listed.

```

## Journal Summary

- cmd: `['journalctl', '-u', 'tokenoskobi-news-radar-refresh.service', '-n', '220', '--no-pager', '--output=short-iso']`
- rc: `0`
- line_count: `220`
- status_209_stdout_count: `37`
- failed_set_up_stdout_count: `36`
- failed_at_step_stdout_count: `37`
- no_such_file_count: `73`
- invalidargument_count: `0`
- rc2_count: `37`
- postprocess_count: `0`
- return_rc_count: `0`
- traceback_count: `0`
- failed_count: `147`

### Journal Interesting Tail
```text
2026-07-08T07:29:39+03:00 v2202604354387455154 (python3)[2566623]: tokenoskobi-news-radar-refresh.service: Failed to set up standard output: No such file or directory
2026-07-08T07:29:39+03:00 v2202604354387455154 (python3)[2566623]: tokenoskobi-news-radar-refresh.service: Failed at step STDOUT spawning /usr/bin/python3: No such file or directory
2026-07-08T07:29:39+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=209/STDOUT
2026-07-08T07:29:39+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
2026-07-08T07:29:39+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
2026-07-08T07:49:41+03:00 v2202604354387455154 (python3)[2588995]: tokenoskobi-news-radar-refresh.service: Failed to set up standard output: No such file or directory
2026-07-08T07:49:41+03:00 v2202604354387455154 (python3)[2588995]: tokenoskobi-news-radar-refresh.service: Failed at step STDOUT spawning /usr/bin/python3: No such file or directory
2026-07-08T07:49:41+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=209/STDOUT
2026-07-08T07:49:41+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
2026-07-08T07:49:41+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
2026-07-08T08:09:41+03:00 v2202604354387455154 (python3)[2611060]: tokenoskobi-news-radar-refresh.service: Failed to set up standard output: No such file or directory
2026-07-08T08:09:41+03:00 v2202604354387455154 (python3)[2611060]: tokenoskobi-news-radar-refresh.service: Failed at step STDOUT spawning /usr/bin/python3: No such file or directory
2026-07-08T08:09:41+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=209/STDOUT
2026-07-08T08:09:41+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
2026-07-08T08:09:41+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
2026-07-08T08:29:49+03:00 v2202604354387455154 (python3)[2631536]: tokenoskobi-news-radar-refresh.service: Failed to set up standard output: No such file or directory
2026-07-08T08:29:49+03:00 v2202604354387455154 (python3)[2631536]: tokenoskobi-news-radar-refresh.service: Failed at step STDOUT spawning /usr/bin/python3: No such file or directory
2026-07-08T08:29:49+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=209/STDOUT
2026-07-08T08:29:49+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
2026-07-08T08:29:49+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
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

## Runner Static

| File | Exists | Syntax OK | Dead-code suspect | Contains argv | Contains postprocess |
|---|---:|---:|---:|---:|---:|
| runner | True | True | True | True | True |
| original_runner | True | True | False | False | False |
| matcher | True | True | False | False | False |

## Recommended Next

```text
NEWS_B_FIX_1_SYSTEMD_STDOUT_STDERR_PATH_TARGETED_APPLY_REQUIRES_APPROVAL
```
