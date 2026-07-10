# NEWS Runtime Freshness State Cleanup Apply With Backup NOAPI V1

Generated UTC: 2026-07-10T04:42:43.002201+00:00

Decision: OK_NEWS_RUNTIME_FRESHNESS_STATE_CLEANUP_APPLY_WITH_BACKUP_NOAPI

Backup:
/root/tokenoskobi_clean_v1/data/backups/tokenoskobi_clean_v1.PRE_NEWS_RUNTIME_FRESHNESS_STATE_CLEANUP_20260710T044242Z.sqlite

Checkpoint:
{
  "checkpoint_utc": "2026-07-10T04:00:44.505461+00:00",
  "preferred_columns": [
    "fetched_at_utc",
    "published_at_utc"
  ],
  "received_at_column_exists": false,
  "rows": [
    {
      "news_uid": "hist_news_f36c6c22f559f46498acce69",
      "timestamps": {
        "fetched_at_utc": "2026-07-10T04:00:44.428364+00:00",
        "published_at_utc": "2026-07-09T20:17:33+00:00"
      }
    },
    {
      "news_uid": "hist_news_83d967a72e31517d9500a5ac",
      "timestamps": {
        "fetched_at_utc": "2026-07-10T04:00:44.428375+00:00",
        "published_at_utc": "2026-07-09T19:48:37+00:00"
      }
    },
    {
      "news_uid": "hist_news_54f18820876fc1cc512bb274",
      "timestamps": {
        "fetched_at_utc": "2026-07-10T04:00:44.428539+00:00",
        "published_at_utc": "2026-07-09T08:51:48+00:00"
      }
    },
    {
      "news_uid": "hist_news_257b3286459432dcd3a95bf1",
      "timestamps": {
        "fetched_at_utc": "2026-07-10T04:00:44.505181+00:00",
        "published_at_utc": "2026-07-10T03:57:58+00:00"
      }
    },
    {
      "news_uid": "hist_news_0f36df09dffc5b6c7fd7df31",
      "timestamps": {
        "fetched_at_utc": "2026-07-10T04:00:44.505292+00:00",
        "published_at_utc": "2026-07-09T15:53:42+00:00"
      }
    },
    {
      "news_uid": "hist_news_e690c71822d00d7c9d518f24",
      "timestamps": {
        "fetched_at_utc": "2026-07-10T04:00:44.505420+00:00",
        "published_at_utc": "2026-07-09T09:31:56+00:00"
      }
    },
    {
      "news_uid": "hist_news_87d29fdbeaf69e1f32f3e5d7",
      "timestamps": {
        "fetched_at_utc": "2026-07-10T04:00:44.505440+00:00",
        "published_at_utc": "2026-07-09T06:51:10+00:00"
      }
    },
    {
      "news_uid": "hist_news_0f7fa5501604267857040d24",
      "timestamps": {
        "fetched_at_utc": "2026-07-10T04:00:44.505461+00:00",
        "published_at_utc": "2026-07-09T06:40:50+00:00"
      }
    }
  ],
  "warning": "received_at_utc_absent_used_fetched_or_published_checkpoint"
}

Upsert result:
{
  "action": "INSERTED_NEW_ROW",
  "row": {
    "component": "NEWS_HISTORICAL_ACCESS_LAYER",
    "created_at_utc": "2026-07-10T04:42:42.934777+00:00",
    "freshness_uid": "news_runtime_freshness_historical_access_v1",
    "heartbeat_status": "OK_HISTORICAL_ACCESS_SYNCED",
    "last_observed_at_utc": "2026-07-10T04:00:44.505461+00:00",
    "match_count": 166,
    "raw_count": 353,
    "score_count": 166,
    "signal_count": 166
  }
}

News delta:
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 0,
  "news_signal_events": 0,
  "news_token_match_events": 0
}

After freshness:
{
  "columns": [
    "freshness_uid",
    "component",
    "last_observed_at_utc",
    "raw_count",
    "match_count",
    "signal_count",
    "score_count",
    "heartbeat_status",
    "created_at_utc"
  ],
  "exists": true,
  "latest_created_at_utc": "2026-07-10T04:42:42.934777+00:00",
  "latest_last_observed_at_utc": "2026-07-10T04:00:44.505461+00:00",
  "row_count": 3,
  "target_rows": [
    {
      "component": "NEWS_HISTORICAL_ACCESS_LAYER",
      "created_at_utc": "2026-07-10T04:42:42.934777+00:00",
      "freshness_uid": "news_runtime_freshness_historical_access_v1",
      "heartbeat_status": "OK_HISTORICAL_ACCESS_SYNCED",
      "last_observed_at_utc": "2026-07-10T04:00:44.505461+00:00",
      "match_count": 166,
      "raw_count": 353,
      "score_count": 166,
      "signal_count": 166
    }
  ]
}

Next:
NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW
