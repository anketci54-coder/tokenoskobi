# NEWS Producer Staleness Fix Apply Plan NOAPI V1

Generated UTC: 2026-07-09T15:36:13.954306+00:00

## Decision

`OK_NEWS_PRODUCER_STALENESS_FIX_APPLY_PLAN_NOAPI`

## Scope

- real_db_apply_now: false
- tempdb_apply_next: true
- service_timer_change_now: false
- api_network_enable_now: false
- trade_authority_now: false

## Expected TEMPDB Delta

```json
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 94,
  "news_signal_events": 94,
  "news_token_match_events": 94
}
```

## Real DB Delta This Step

```json
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 0,
  "news_signal_events": 0,
  "news_token_match_events": 0
}
```

## Next

`NEWS_PRODUCER_STALENESS_FIX_TEMPDB_APPLY_DRYRUN_NOAPI`
