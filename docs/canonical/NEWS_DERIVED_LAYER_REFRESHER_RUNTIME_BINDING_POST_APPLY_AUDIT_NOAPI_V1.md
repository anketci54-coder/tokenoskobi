# NEWS Derived Layer Refresher Runtime Binding Post Apply Audit NOAPI V1

Generated UTC: 2026-07-09T18:01:42.985572+00:00

Decision: OK_NEWS_DERIVED_LAYER_REFRESHER_RUNTIME_BINDING_POST_APPLY_AUDIT_NOAPI

Repair reason:
previous audit had brittle/missing outer helper; repaired audit validates wrapper, sha lock, systemd boundary, db health, and runtime effect

Target runner:
tools/news_radar_refresh_runner_v1.py

Helper:
tools/news_derived_layer_refresher_v1.py

Backup runner:
tools/news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py

Runtime effect observed:
True

DB preview:
{
  "counts": {
    "news_raw_feed_events": 333,
    "news_score_events_v1": 147,
    "news_signal_events": 147,
    "news_token_match_events": 147
  },
  "derived_counts_balanced": true,
  "integrity": "ok",
  "latest_bad_trade_flags": 0,
  "latest_by_table": {
    "news_score_events_v1": "2026-07-09T17:30:27.251469+00:00",
    "news_signal_events": "2026-07-09T17:30:27.251469+00:00",
    "news_token_match_events": "2026-07-09T17:30:27.251469+00:00"
  },
  "latest_derived": "2026-07-09T17:30:27.251469+00:00",
  "latest_raw": "2026-07-09T17:09:01+00:00",
  "tail_candidates": 0
}

Tests:
- test_count: 8
- ok_count: 8
- fail_count: 0

Warnings:
[]

Next:
NEWS_HISTORICAL_ACCESS_REAL_FETCH_PLAN_NOAPI
