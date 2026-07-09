# NEWS Producer Staleness Fix Real Apply Plan NOAPI V1

Generated UTC: 2026-07-09T16:25:47.370314+00:00

Decision: OK_NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_PLAN_NOAPI

Scope:
- real_db_apply_now: false
- real_db_apply_next: true
- requires_commander_approval_before_next: true
- backup_required_before_write: true
- transaction_required: true
- trade_authority_now: false

Current candidates:
98

Expected real apply delta:
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 98,
  "news_signal_events": 98,
  "news_token_match_events": 98
}

Backup plan:
{
  "backup_db": "/root/tokenoskobi_clean_v1/data/backups/news_producer_staleness_real_apply/20260709T162547Z/tokenoskobi_clean_v1.sqlite.before_news_real_apply",
  "backup_dir": "/root/tokenoskobi_clean_v1/data/backups/news_producer_staleness_real_apply/20260709T162547Z",
  "backup_method": "copy2 real sqlite before transaction",
  "record_sha256_before_and_after": true,
  "rollback_method": "stop apply, restore backup db only if post-apply audit fails before runtime binding"
}

Real DB delta this step:
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 0,
  "news_signal_events": 0,
  "news_token_match_events": 0
}

Next:
NEWS_PRODUCER_STALENESS_FIX_REAL_APPLY_WITH_BACKUP
