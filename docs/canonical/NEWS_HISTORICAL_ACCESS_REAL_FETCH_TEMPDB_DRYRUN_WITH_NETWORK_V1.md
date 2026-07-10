# NEWS Historical Access Real Fetch TempDB Dryrun With Network V1

Generated UTC: 2026-07-10T03:50:05.394966+00:00

Decision: OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_TEMPDB_DRYRUN_WITH_NETWORK

Repair note:
Batch flag check limited to generated_at_utc rows from this historical TempDB dryrun.

Fetched unique count:
55

Raw insert:
{
  "duplicates": 48,
  "failed": [],
  "inserted": 7,
  "inserted_news_uids": [
    "hist_news_f36c6c22f559f46498acce69",
    "hist_news_83d967a72e31517d9500a5ac",
    "hist_news_54f18820876fc1cc512bb274",
    "hist_news_0f36df09dffc5b6c7fd7df31",
    "hist_news_e690c71822d00d7c9d518f24",
    "hist_news_87d29fdbeaf69e1f32f3e5d7",
    "hist_news_0f7fa5501604267857040d24"
  ]
}

Derived backfill inserted:
{
  "news_score_events_v1": 7,
  "news_signal_events": 7,
  "news_token_match_events": 7
}

TempDB delta:
{
  "news_raw_feed_events": 7,
  "news_score_events_v1": 7,
  "news_signal_events": 7,
  "news_token_match_events": 7
}

Real DB delta:
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 0,
  "news_signal_events": 0,
  "news_token_match_events": 0
}

Next:
NEWS_HISTORICAL_ACCESS_REAL_FETCH_APPLY_WITH_BACKUP
