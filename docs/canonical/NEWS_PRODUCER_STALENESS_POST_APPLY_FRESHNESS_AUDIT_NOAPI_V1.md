# NEWS Producer Staleness Post Apply Freshness Audit NOAPI V1

Generated UTC: 2026-07-09T16:47:41.712591+00:00

Decision: OK_NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI

Repair reason:
previous_audit_used_global_layer_link_scope; repaired audit validates real-apply batch scope and current freshness

Current counts:
{
  "news_raw_feed_events": 329,
  "news_score_events_v1": 145,
  "news_signal_events": 145,
  "news_token_match_events": 145
}

Batch counts:
{
  "news_score_events_v1": 98,
  "news_signal_events": 98,
  "news_token_match_events": 98
}

Latest:
{
  "latest_derived": "2026-07-09T16:32:24.615974+00:00",
  "latest_raw": "2026-07-09T15:56:59+00:00",
  "tail_candidates_after_apply": 0
}

Tests:
- test_count: 8
- ok_count: 8
- fail_count: 0

Warnings:
[]

Next:
NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_PLAN_NOAPI
