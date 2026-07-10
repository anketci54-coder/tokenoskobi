# BAD Trade Flags Cleanup Apply With Backup NOAPI V1

Generated UTC: 2026-07-10T05:27:44.704207+00:00

Decision: OK_BAD_TRADE_FLAGS_CLEANUP_APPLY_WITH_BACKUP_NOAPI

Backup:
/root/tokenoskobi_clean_v1/data/backups/tokenoskobi_clean_v1.PRE_BAD_TRADE_FLAGS_CLEANUP_20260710T052744Z.sqlite

Before / After:
{
  "after_bad_flags": 0,
  "before_bad_flags": 47,
  "integrity_after": "ok",
  "integrity_before": "ok",
  "news_delta": {
    "news_raw_feed_events": 0,
    "news_score_events_v1": 0,
    "news_signal_events": 0,
    "news_token_match_events": 0
  },
  "updated_rows": 47
}

After flag grouping:
[
  {
    "count": 168,
    "flag_tuple": "0/0/0"
  }
]

Next:
NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI
