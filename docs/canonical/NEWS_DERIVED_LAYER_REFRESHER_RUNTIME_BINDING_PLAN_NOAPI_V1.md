# NEWS Derived Layer Refresher Runtime Binding Plan NOAPI V1

Generated UTC: 2026-07-09T16:56:09.339966+00:00

Decision: OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_PLAN_NOAPI

Binding mode:
PATCH_EXISTING_RUNNER_TO_CALL_DERIVED_REFRESHER_AFTER_RAW_REFRESH

Current counts:
{
  "news_raw_feed_events": 332,
  "news_score_events_v1": 145,
  "news_signal_events": 145,
  "news_token_match_events": 145
}

Latest:
{
  "latest_derived": "2026-07-09T16:32:24.615974+00:00",
  "latest_raw": "2026-07-09T16:42:18+00:00",
  "tail_candidates": 1
}

Scope this step:
- plan_only: true
- real_db_write_now: false
- service_change_now: false
- timer_change_now: false
- api_network_enable_now: false
- trade_authority_now: false

Tests:
- test_count: 8
- ok_count: 8
- fail_count: 0

Next:
NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_DRYRUN_NOAPI
