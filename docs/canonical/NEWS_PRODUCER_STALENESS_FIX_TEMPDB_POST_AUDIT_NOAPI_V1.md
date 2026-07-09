# NEWS Producer Staleness Fix TEMPDB Post Audit NOAPI V1

Generated UTC: 2026-07-09T16:18:43.571866+00:00

## Decision

`OK_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_POST_AUDIT_NOAPI`

## TEMPDB Delta

```json
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 96,
  "news_signal_events": 96,
  "news_token_match_events": 96
}
```

## TEMPDB Counts

```json
{
  "news_raw_feed_events": 327,
  "news_score_events_v1": 143,
  "news_signal_events": 143,
  "news_token_match_events": 143
}
```

## Real DB Delta

```json
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 0,
  "news_signal_events": 0,
  "news_token_match_events": 0
}
```

## Tests

- test_count: 8
- ok_count: 8
- fail_count: 0

## Next

`NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_PLAN_NOAPI`
