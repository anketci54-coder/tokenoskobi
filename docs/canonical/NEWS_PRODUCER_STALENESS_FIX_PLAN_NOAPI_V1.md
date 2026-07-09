# NEWS Producer Staleness Fix Plan NOAPI V1

Generated UTC: 2026-07-09T14:58:54.307153+00:00

## Decision

`OK_NEWS_PRODUCER_STALENESS_FIX_PLAN_NOAPI`

## Locked Root Cause

`RAW_FEED_IS_CURRENT_BUT_DERIVED_LAYERS_ARE_STALE`

## Fix Strategy

Plan: create a controlled derived-layer refresh path after raw feed refresh.

Order:
- raw_feed_current_check
- token_match_refresh
- signal_refresh
- score_refresh
- freshness_recheck

## Boundary

- api_call: false
- network_call: false
- db_write: false
- db_schema_change: false
- index_creation: false
- service_change: false
- timer_change: false
- nginx_change: false
- paper_trade: false
- live_trade: false
- execution_authority: false

## DB Delta

```json
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 0,
  "news_signal_events": 0,
  "news_token_match_events": 0
}
```

## Next

`NEWS_PRODUCER_STALENESS_FIX_DRYRUN_NOAPI`
