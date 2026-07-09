# NEWS Producer Staleness Fix Dryrun NOAPI V1

Generated UTC: 2026-07-09T15:05:16.233948+00:00

## Decision

`OK_NEWS_PRODUCER_STALENESS_FIX_DRYRUN_NOAPI`

## Preview

```json
{
  "apply_plan_needed": true,
  "candidate_counts": {
    "projected_score_candidate_count_after_token_match_apply": 94,
    "projected_signal_candidate_count_after_token_match_apply": 94,
    "score_candidate_count_without_write_existing_match_based": 0,
    "score_candidate_count_without_write_existing_signal_based": 0,
    "signal_candidate_count_without_write_existing": 0,
    "token_match_candidate_count_without_write": 94
  },
  "latest_derived_created_at_utc": "2026-07-06T06:44:10.288486+00:00",
  "new_raw_rows_since_latest_derived": 94,
  "raw_candidate_samples": [
    {
      "fetched_at_utc": "2026-07-09T13:50:09.941412+00:00",
      "news_uid": "timer_news_d209ed0bc1a34c65c12f",
      "published_at_utc": "2026-07-09T13:30:00+00:00",
      "source_uid": "src_seed_crypto_news_rss",
      "title": "Bitcoin’s quantum dilemma: Bigger blocks or STARK proofs?"
    },
    {
      "fetched_at_utc": "2026-07-09T13:10:06.077198+00:00",
      "news_uid": "timer_news_4b2cb90b3f72815ec9b1",
      "published_at_utc": "2026-07-09T13:01:38+00:00",
      "source_uid": "src_seed_crypto_news_rss",
      "title": "Aave rolls out vaults for yield-hungry fintech investors"
    },
    {
      "fetched_at_utc": "2026-07-09T13:10:06.077249+00:00",
      "news_uid": "timer_news_ba26332a05561486dd6d",
      "published_at_utc": "2026-07-09T13:00:00+00:00",
      "source_uid": "src_seed_crypto_news_rss",
      "title": "Age verification is the surveillance nobody voted for"
    },
    {
      "fetched_at_utc": "2026-07-09T13:10:05.973957+00:00",
      "news_uid": "timer_news_35a37a44429e2a28a1d6",
      "published_at_utc": "2026-07-09T12:53:44+00:00",
      "source_uid": "src_seed_crypto_news_rss",
      "title": "Hong Kong regulator orders new anti-phishing measures for crypto platforms"
    },
    {
      "fetched_at_utc": "2026-07-09T12:10:00.335034+00:00",
      "news_uid": "timer_news_c35d7f2d1542918f1b28",
      "published_at_utc": "2026-07-09T12:00:00+00:00",
      "source_uid": "src_seed_crypto_news_rss",
      "title": "Over $7.2 billion have migrated from LayerZero to Chainlink CCIP as Mantle joins exodus"
    },
    {
      "fetched_at_utc": "2026-07-09T11:29:55.303350+00:00",
      "news_uid": "timer_news_ee5bd8538292693d88d7",
      "published_at_utc": "2026-07-09T11:27:10+00:00",
      "source_uid": "src_seed_crypto_news_rss",
      "title": "Pricing houses in bitcoin exposes dollar's loss of value"
    },
    {
      "fetched_at_utc": "2026-07-09T11:29:55.165069+00:00",
      "news_uid": "timer_news_dd89330dacbb4d9f37a1",
      "published_at_utc": "2026-07-09T11:18:41+00:00",
      "source_uid": "src_seed_crypto_news_rss",
      "title": "Sony Bank gets US regulator nod to issue stablecoins"
    },
    {
      "fetched_at_utc": "2026-07-09T11:29:55.165177+00:00",
      "news_uid": "timer_news_484ae2580800d3d3a1d6",
      "published_at_utc": "2026-07-09T11:18:21+00:00",
      "source_uid": "src_seed_crypto_news_rss",
      "title": "Interpol operation exposes $122M crypto wallet tied to romance scam laundering"
    },
    {
      "fetched_at_utc": "2026-07-09T11:09:54.966480+00:00",
      "news_uid": "timer_news_9928da42c898c8c994d5",
      "published_at_utc": "2026-07-09T11:08:37+00:00",
      "source_uid": "src_seed_crypto_news_rss",
      "title": "Swift rolls out new blockchain ledger to bring 24/7 banking to 17 global giants"
    },
    {
      "fetched_at_utc": "2026-07-09T11:09:54.966587+00:00",
      "news_uid": "timer_news_74beb9df224fa92c2af4",
      "published_at_utc": "2026-07-09T10:55:37+00:00",
      "source_uid": "src_seed_crypto_news_rss",
      "title": "Latin America’s biggest stock exchange now offers options on bitcoin, ether and solana futures"
    }
  ]
}
```

## Tests

- test_count: 9
- ok_count: 9
- fail_count: 0

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

`NEWS_PRODUCER_STALENESS_FIX_APPLY_PLAN_NOAPI`
