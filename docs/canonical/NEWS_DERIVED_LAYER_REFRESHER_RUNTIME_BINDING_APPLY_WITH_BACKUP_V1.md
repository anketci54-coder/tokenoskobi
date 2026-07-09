# NEWS Derived Layer Refresher Runtime Binding Apply With Backup V1

Generated UTC: 2026-07-09T17:12:45.106345+00:00

Decision: OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_APPLY_WITH_BACKUP

Apply action:
APPLIED_WRAPPER_WITH_BACKUP

Target runner:
tools/news_radar_refresh_runner_v1.py

Backup runner:
tools/news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py

DB delta:
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 0,
  "news_signal_events": 0,
  "news_token_match_events": 0
}

Tests:
- test_count: 8
- ok_count: 8
- fail_count: 0

Next:
NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_POST_APPLY_AUDIT_NOAPI
