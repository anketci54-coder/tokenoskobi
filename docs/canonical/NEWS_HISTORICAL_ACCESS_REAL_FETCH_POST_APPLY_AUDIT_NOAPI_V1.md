# NEWS Historical Access Real Fetch Post Apply Audit NOAPI V1

Generated UTC: 2026-07-10T04:31:40.358217+00:00

Decision: OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_POST_APPLY_AUDIT_NOAPI

Expected count:
8

DB counts:
{
  "news_raw_feed_events": 353,
  "news_score_events_v1": 166,
  "news_signal_events": 166,
  "news_token_match_events": 166
}

Expected chain:
[
  {
    "evidence_ok": true,
    "link_ok": true,
    "match_count": 1,
    "news_uid": "hist_news_f36c6c22f559f46498acce69",
    "raw_count": 1,
    "score_alignment_ok": true,
    "score_count": 1,
    "signal_count": 1
  },
  {
    "evidence_ok": true,
    "link_ok": true,
    "match_count": 1,
    "news_uid": "hist_news_83d967a72e31517d9500a5ac",
    "raw_count": 1,
    "score_alignment_ok": true,
    "score_count": 1,
    "signal_count": 1
  },
  {
    "evidence_ok": true,
    "link_ok": true,
    "match_count": 1,
    "news_uid": "hist_news_54f18820876fc1cc512bb274",
    "raw_count": 1,
    "score_alignment_ok": true,
    "score_count": 1,
    "signal_count": 1
  },
  {
    "evidence_ok": true,
    "link_ok": true,
    "match_count": 1,
    "news_uid": "hist_news_257b3286459432dcd3a95bf1",
    "raw_count": 1,
    "score_alignment_ok": true,
    "score_count": 1,
    "signal_count": 1
  },
  {
    "evidence_ok": true,
    "link_ok": true,
    "match_count": 1,
    "news_uid": "hist_news_0f36df09dffc5b6c7fd7df31",
    "raw_count": 1,
    "score_alignment_ok": true,
    "score_count": 1,
    "signal_count": 1
  },
  {
    "evidence_ok": true,
    "link_ok": true,
    "match_count": 1,
    "news_uid": "hist_news_e690c71822d00d7c9d518f24",
    "raw_count": 1,
    "score_alignment_ok": true,
    "score_count": 1,
    "signal_count": 1
  },
  {
    "evidence_ok": true,
    "link_ok": true,
    "match_count": 1,
    "news_uid": "hist_news_87d29fdbeaf69e1f32f3e5d7",
    "raw_count": 1,
    "score_alignment_ok": true,
    "score_count": 1,
    "signal_count": 1
  },
  {
    "evidence_ok": true,
    "link_ok": true,
    "match_count": 1,
    "news_uid": "hist_news_0f7fa5501604267857040d24",
    "raw_count": 1,
    "score_alignment_ok": true,
    "score_count": 1,
    "signal_count": 1
  }
]

Orphan checks:
{
  "news_score_events_v1": [],
  "news_signal_events": [],
  "news_token_match_events": []
}

Duplicate checks:
{
  "news_raw_feed_events": [],
  "news_score_events_v1": [],
  "news_signal_events": [],
  "news_token_match_events": []
}

Freshness:
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
  "latest_timestamp": "2026-07-10T03:31:21.155065+00:00",
  "latest_timestamp_column": "created_at_utc",
  "row_count": 2,
  "status": "STALE_BEFORE_APPLY",
  "table": "news_runtime_freshness_v1",
  "updated_after_apply": false
}

Outer DB delta:
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 0,
  "news_signal_events": 0,
  "news_token_match_events": 0
}

Next:
NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW
