# NEWS Producer Staleness Root Cause Audit NOAPI V1

Generated UTC: 2026-07-09T14:50:34.752854+00:00

## Decision

`OK_NEWS_PRODUCER_STALENESS_ROOT_CAUSE_AUDIT_NOAPI`

## Root Cause Hypothesis

- RAW_FEED_IS_CURRENT_BUT_DERIVED_LAYERS_ARE_STALE

## Findings

- raw_latest_published_at_utc: `2026-07-09T13:30:00+00:00`
- raw_latest_fetched_at_utc: `2026-07-09T13:50:09.941412+00:00`
- raw_published_age_minutes: `80.58`
- raw_fetched_age_minutes: `60.42`
- derived_created_at_age_minutes: `{"news_score_events_v1": 4806.41, "news_signal_events": 4806.41, "news_token_match_events": 4806.41}`

## Authority

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

## Warnings

```json
[
  "news_token_match_events:derived_layer_stale_age_minutes_4806.41",
  "news_signal_events:derived_layer_stale_age_minutes_4806.41",
  "news_score_events_v1:derived_layer_stale_age_minutes_4806.41",
  "JOURNAL_INVALIDARGUMENT_FOUND"
]
```

## Next

`NEWS_PRODUCER_STALENESS_FIX_PLAN_NOAPI`
