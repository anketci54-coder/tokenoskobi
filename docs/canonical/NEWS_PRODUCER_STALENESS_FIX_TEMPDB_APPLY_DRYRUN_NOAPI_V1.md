# NEWS Producer Staleness Fix TEMPDB Apply Dryrun NOAPI V1

Generated UTC: 2026-07-09T15:52:37.416764+00:00

## Decision

`OK_NEWS_PRODUCER_STALENESS_FIX_TEMPDB_APPLY_DRYRUN_NOAPI`

## TEMPDB Delta

```json
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 96,
  "news_signal_events": 96,
  "news_token_match_events": 96
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

## TEMPDB Path

`/tmp/tokenoskobi_news_staleness_tempdb_apply_dryrun_20260709T155237Z.sqlite`

## Next

`NEWS_PRODUCER_STALENESS_FIX_TEMPDB_POST_AUDIT_NOAPI`
