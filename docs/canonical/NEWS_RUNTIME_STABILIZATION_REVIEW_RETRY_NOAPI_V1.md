# NEWS Runtime Stabilization Review Retry NOAPI V1

Generated UTC: 2026-07-10T05:43:35.663066+00:00

Decision: OK_NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI

Summary:
{
  "decision": "OK_NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI",
  "generated_at_utc": "2026-07-10T05:43:35.663066+00:00",
  "result": {
    "authority": {
      "api_call": false,
      "db_write": false,
      "execution_authority": false,
      "live_trade": false,
      "network_call": false,
      "paper_trade": false,
      "runner_executed": false,
      "service_change": false,
      "timer_change": false
    },
    "decision": "OK_NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI",
    "fail_count": 0,
    "failures": [],
    "generated_at_utc": "2026-07-10T05:43:35.108442+00:00",
    "next": "NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI",
    "ok_count": 7,
    "runner_review": {
      "derived_helper_exists": true,
      "helper_line_count": 377,
      "helper_sha256": "e5e516456376d45c977a0a4aa2508fdd57ccd21f8394db960db8c9ec471ff532",
      "runner_exists": true,
      "runner_line_count": 19,
      "runner_mentions_db_path": true,
      "runner_mentions_derived_helper": true,
      "runner_mentions_stage": true,
      "runner_mentions_write": true,
      "runner_sha256": "173a6bd91913b306dddf71f31d1cb76d45f5ef992dcb1efe8df9c2550167faf2"
    },
    "snapshot": {
      "bad_flags": 0,
      "collision": {
        "hist_prefix_count": 8,
        "match_news_uid_duplicates": [],
        "namespace_stats": [
          {
            "count": 8,
            "namespace": "historical_hist_news"
          },
          {
            "count": 34,
            "namespace": "runtime_news"
          },
          {
            "count": 314,
            "namespace": "timer_news"
          }
        ],
        "raw_news_uid_duplicates": [],
        "score_news_uid_duplicates": [],
        "signal_news_uid_duplicates": [],
        "timer_prefix_count": 314
      },
      "counts": {
        "news_raw_feed_events": 356,
        "news_score_events_v1": 169,
        "news_signal_events": 169,
        "news_token_match_events": 169
      },
      "duplicates": {
        "news_raw_feed_events": [],
        "news_score_events_v1": [],
        "news_signal_events": [],
        "news_token_match_events": []
      },
      "freshness": {
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
        "latest": {
          "created_at_utc": "2026-07-10T05:31:32.746256+00:00",
          "last_observed_at_utc": "2026-07-10T05:31:32.746256+00:00"
        },
        "ok_historical_access_synced": true,
        "target_historical_access": [
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
      },
      "integrity": "ok",
      "orphans": {
        "news_score_events_v1": [],
        "news_signal_events": [],
        "news_token_match_events": []
      }
    },
    "stage": "NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI",
    "systemd_review": {
      "service_active": "inactive",
      "service_execstart_lines": [
        "ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py"
      ],
      "service_text_sha256": "97829c2a13305a6b011dec317f89b710d6c605715cfbfdecab7bb5291fc5fe4b",
      "service_unit_exists": true,
      "timer_active": "active",
      "timer_enabled": "enabled",
      "timer_schedule_lines": [
        "OnActiveSec=20min",
        "OnUnitActiveSec=20min",
        "Unit=tokenoskobi-news-radar-refresh.service"
      ],
      "timer_text_sha256": "47e5dacef0e068480bb2de67960f5320469910ab6ded80937266cf68081f1af5",
      "timer_unit_exists": true
    },
    "test_count": 7,
    "tests": [
      {
        "ok": true,
        "test_id": "T01_PRIOR_CLEANUP_OK"
      },
      {
        "integrity": "ok",
        "ok": true,
        "test_id": "T02_DB_INTEGRITY_OK"
      },
      {
        "bad_flags": 0,
        "ok": true,
        "test_id": "T03_BAD_FLAGS_ZERO"
      },
      {
        "duplicates": {
          "news_raw_feed_events": [],
          "news_score_events_v1": [],
          "news_signal_events": [],
          "news_token_match_events": []
        },
        "ok": true,
        "orphans": {
          "news_score_events_v1": [],
          "news_signal_events": [],
          "news_token_match_events": []
        },
        "test_id": "T04_NO_ORPHANS_AND_DUPLICATES"
      },
      {
        "freshness": {
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
          "latest": {
            "created_at_utc": "2026-07-10T05:31:32.746256+00:00",
            "last_observed_at_utc": "2026-07-10T05:31:32.746256+00:00"
          },
          "ok_historical_access_synced": true,
          "target_historical_access": [
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
        },
        "ok": true,
        "test_id": "T05_FRESHNESS_SYNCED"
      },
      {
        "ok": true,
        "runner": {
          "derived_helper_exists": true,
          "helper_line_count": 377,
          "helper_sha256": "e5e516456376d45c977a0a4aa2508fdd57ccd21f8394db960db8c9ec471ff532",
          "runner_exists": true,
          "runner_line_count": 19,
          "runner_mentions_db_path": true,
          "runner_mentions_derived_helper": true,
          "runner_mentions_stage": true,
          "runner_mentions_write": true,
          "runner_sha256": "173a6bd91913b306dddf71f31d1cb76d45f5ef992dcb1efe8df9c2550167faf2"
        },
        "systemd": {
          "service_active": "inactive",
          "service_execstart_lines": [
            "ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py"
          ],
          "service_text_sha256": "97829c2a13305a6b011dec317f89b710d6c605715cfbfdecab7bb5291fc5fe4b",
          "service_unit_exists": true,
          "timer_active": "active",
          "timer_enabled": "enabled",
          "timer_schedule_lines": [
            "OnActiveSec=20min",
            "OnUnitActiveSec=20min",
            "Unit=tokenoskobi-news-radar-refresh.service"
          ],
          "timer_text_sha256": "47e5dacef0e068480bb2de67960f5320469910ab6ded80937266cf68081f1af5",
          "timer_unit_exists": true
        },
        "test_id": "T06_RUNNER_AND_SYSTEMD_DISCOVERED"
      },
      {
        "api_call": false,
        "db_write": false,
        "network_call": false,
        "ok": true,
        "runner_executed": false,
        "service_change": false,
        "test_id": "T07_NOAPI_RETRY_BOUNDARY",
        "timer_change": false
      }
    ],
    "warnings": []
  },
  "stage": "NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI"
}
