# NEWS Producer Staleness Fix Real Apply With Backup V1

Generated UTC: 2026-07-09T16:32:24.695095+00:00

Decision: OK_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_WITH_BACKUP

Real DB delta:
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 98,
  "news_signal_events": 98,
  "news_token_match_events": 98
}

Inserted:
{
  "news_score_events_v1": 98,
  "news_signal_events": 98,
  "news_token_match_events": 98
}

Backup:
{
  "backup_db": "/root/tokenoskobi_clean_v1/data/backups/news_producer_staleness_real_apply/20260709T162547Z/tokenoskobi_clean_v1.sqlite.before_news_real_apply",
  "backup_sha256": "0b81cda2eed7dd276d6480ecc5cae1b763b112ae57083593e37540e1001838d0",
  "real_db_sha256_after": "188dea8f61f63ea422b4c198699696c0fffa20cd80885e4009b3d45ea9eda1d4",
  "real_db_sha256_before": "0b81cda2eed7dd276d6480ecc5cae1b763b112ae57083593e37540e1001838d0"
}

Tests:
- test_count: 7
- ok_count: 7
- fail_count: 0

Next:
NEWS_PRODUCER_STALENESS_POST_APPLY_FRESHNESS_AUDIT_NOAPI
