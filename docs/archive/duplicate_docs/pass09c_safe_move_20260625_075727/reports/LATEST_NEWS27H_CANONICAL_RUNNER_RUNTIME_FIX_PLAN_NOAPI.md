# NEWS27H CANONICAL RUNNER RUNTIME FIX PLAN NOAPI

- created_at_utc: `2026-05-10T19:41:17.752166+00:00`
- final_status: **PASS**
- runtime_signals: `['INVALIDARGUMENT', 'status=2']`
- nameerror_vars: `[]`
- likely_cause: `['NAMEERROR_VARIABLE_NOT_VISIBLE_IN_CAPTURED_LOGS_NEED_TEMP_MOCK_REPRO']`
- runner_compile_ok: `True`
- original_runner_exists: `True`
- original_runner_compile_ok: `True`
- news_count: `34`
- lane_counts: `{'risk_top': 3, 'risk_watch': 8, 'general_info': 23}`
- display_counts: `{'Kritik Risk': 3, 'Risk İzle': 8, 'Bilgi': 23}`
- canonical_meta_exists: `False`
- canonical_html_marker_count: `0`
- db_unchanged: `True`
- runner_unchanged: `True`
- preview_unchanged: `True`
- paper_live_zero: `True`
- next_phase: `NEWS27I_CANONICAL_RUNNER_RUNTIME_FIX_DRYRUN_NOAPI`

## Plan Steps
- 1 `KEEP_TIMER_AS_IS_FOR_NOW` write_now=`False`
- 2 `NO_LIVE_PATCH_NO_ROLLBACK_NOW` write_now=`False`
- 3 `REPRO_WITH_TEMP_MOCK_ORIGINAL` write_now=`False`
- 4 `FIX_ONLY_CANONICAL_RENDER_RUNTIME` write_now=`False`
- 5 `TEMP_COMPILE_AND_EXEC_TEST` write_now=`False`
- 6 `REAL_FIX_OR_ROLLBACK_DECISION` write_now=`False`
- 7 `AFTER_REAL_AUDIT` write_now=`False`

## NameError Context
```text
L4: 2026-05-10T21:04:19+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L5: 2026-05-10T21:04:20+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.
L6: 2026-05-10T21:04:20+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
L7: 2026-05-10T21:24:43+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L8: 2026-05-10T21:24:44+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=2/INVALIDARGUMENT
L9: 2026-05-10T21:24:44+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
L10: 2026-05-10T21:24:44+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
L11: 2026-05-10T21:45:09+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L12: 2026-05-10T21:45:10+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=2/INVALIDARGUMENT
L13: 2026-05-10T21:45:10+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
L14: 2026-05-10T21:45:10+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
L15: 2026-05-10T22:05:13+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L16: 2026-05-10T22:05:14+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=2/INVALIDARGUMENT
L17: 2026-05-10T22:05:14+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
L18: 2026-05-10T22:05:14+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
L19: 2026-05-10T22:25:19+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L20: 2026-05-10T22:25:20+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=2/INVALIDARGUMENT
L21: 2026-05-10T22:25:20+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
L22: 2026-05-10T22:25:20+03:00 v2202604354387455154 systemd[1]: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
L23: 
L24: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L102: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L103: tokenoskobi-news-radar-refresh.service: Deactivated successfully.
L104: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
L105: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L106: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=2/INVALIDARGUMENT
L107: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
L108: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
L109: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L110: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=2/INVALIDARGUMENT
L111: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
L112: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
L113: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L114: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=2/INVALIDARGUMENT
L115: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
L116: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
L117: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...
L118: tokenoskobi-news-radar-refresh.service: Main process exited, code=exited, status=2/INVALIDARGUMENT
L119: tokenoskobi-news-radar-refresh.service: Failed with result 'exit-code'.
L120: Failed to start tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.
```

## Errors
- none

## Warnings
- none
