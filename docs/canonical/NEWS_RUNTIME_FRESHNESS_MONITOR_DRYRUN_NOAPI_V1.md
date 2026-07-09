# NEWS Runtime Freshness Monitor Dryrun NOAPI V1

Generated UTC: 2026-07-09T14:13:47.145653+00:00

## Decision

`OK_NEWS_RUNTIME_FRESHNESS_MONITOR_DRYRUN_NOAPI`

## Producer

`OK_TIMER_ACTIVE_ONESHOT_SERVICE_CAN_BE_INACTIVE`

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
  "freshness_observation:news_raw_feed_events:UNKNOWN_TIMESTAMP",
  "freshness_observation:news_token_match_events:STALE_FAIL_WINDOW",
  "freshness_observation:news_signal_events:STALE_FAIL_WINDOW",
  "freshness_observation:news_score_events_v1:STALE_FAIL_WINDOW"
]
```

## Next

`NEWS_HISTORICAL_ACCESS_LAYER_PLAN_NOAPI`
