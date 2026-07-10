# NEWS Continuous Producer One Shot Completion V1

Generated UTC: 2026-07-10T05:43:35.663066+00:00

Decision: OK_NEWS_CONTINUOUS_PRODUCER_ONE_SHOT_COMPLETION

Summary:
{
  "compile": {
    "tool_rc": 0,
    "tool_stderr": "",
    "tool_stdout": ""
  },
  "decision": "OK_NEWS_CONTINUOUS_PRODUCER_ONE_SHOT_COMPLETION",
  "failures": [],
  "generated_at_utc": "2026-07-10T05:43:35.663066+00:00",
  "next": "NEWS_CONTINUOUS_PRODUCER_OBSERVATION_WINDOW_NOAPI",
  "outer_real_news_counts_after": {
    "news_raw_feed_events": 356,
    "news_score_events_v1": 169,
    "news_signal_events": 169,
    "news_token_match_events": 169
  },
  "outer_real_news_counts_before": {
    "news_raw_feed_events": 356,
    "news_score_events_v1": 169,
    "news_signal_events": 169,
    "news_token_match_events": 169
  },
  "outer_real_news_delta": {
    "news_raw_feed_events": 0,
    "news_score_events_v1": 0,
    "news_signal_events": 0,
    "news_token_match_events": 0
  },
  "prior": "data/control/bad_trade_flags_cleanup_apply_with_backup_noapi_v1.json",
  "result": {
    "decision": "OK_NEWS_CONTINUOUS_PRODUCER_ONE_SHOT_COMPLETION",
    "failures": [],
    "generated_at_utc": "2026-07-10T05:43:35.108401+00:00",
    "next": "NEWS_CONTINUOUS_PRODUCER_OBSERVATION_WINDOW_NOAPI",
    "remaining_after_this_if_ok": [
      "NEWS_CONTINUOUS_PRODUCER_OBSERVATION_WINDOW_NOAPI"
    ],
    "stage": "NEWS_CONTINUOUS_PRODUCER_ONE_SHOT_COMPLETION",
    "steps": {
      "controlled_dryrun": {
        "authority": {
          "api_call": false,
          "db_schema_change": false,
          "execution_authority": false,
          "index_creation": false,
          "live_trade": false,
          "network_call": true,
          "nginx_change": false,
          "paper_trade": false,
          "real_db_write": false,
          "service_change": false,
          "temp_db_write": true,
          "timer_change": false
        },
        "balanced_temp_delta": true,
        "decision": "OK_NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN_AND_POST_AUDIT_SEAL",
        "fail_count": 0,
        "failures": [],
        "generated_at_utc": "2026-07-10T05:43:35.158782+00:00",
        "next": "NEWS_CONTINUOUS_PRODUCER_OBSERVATION_WINDOW_NOAPI",
        "ok_count": 7,
        "real_after": {
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
        "real_before": {
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
        "real_delta": {
          "news_raw_feed_events": 0,
          "news_score_events_v1": 0,
          "news_signal_events": 0,
          "news_token_match_events": 0
        },
        "runner_result": {
          "cmd": [
            "python3",
            "/root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py",
            "--db-path",
            "/tmp/tokenoskobi_news_producer_dryrun_zyyv379w/tokenoskobi_clean_v1.CONTINUOUS_PRODUCER_DRYRUN.sqlite",
            "--stage",
            "NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN",
            "--write"
          ],
          "rc": 0,
          "stderr": "",
          "stdout": "TOKENOSKOBI_WRAPPER_TRACE_V1: main_enter\nTOKENOSKOBI_WRAPPER_TRACE_V1: before_count_start\nTOKENOSKOBI_WRAPPER_TRACE_V1: before_count_done | 356\nTOKENOSKOBI_WRAPPER_TRACE_V1: subprocess_start\nTOKENOSKOBI_WRAPPER_TRACE_V1: after_count_done | 356\nTOKENOSKOBI_WRAPPER_TRACE_V1: news_downstream_hook_bounded_catchup | raw_delta<=0 unprocessed=187\nTOKENOSKOBI_WRAPPER_TRACE_V1: news_downstream_hook_noop | candidates=0 tokens=19 market_events=0 adversarial_events=0\nTOKENOSKOBI_WRAPPER_TRACE_V1: final_return_after_downstream_hook | 0\nTOKENOSKOBI_WRAPPER_TRACE_V1: return_rc | 0\n{\n  \"authority\": {\n    \"api_call\": false,\n    \"execution_authority\": false,\n    \"index_creation\": false,\n    \"live_trade\": false,\n    \"network_call\": false,\n    \"paper_trade\": false,\n    \"schema_change\": false\n  },\n  \"bad_trade_flags\": 0,\n  \"candidate_count\": 0,\n  \"counts_after\": {\n    \"news_raw_feed_events\": 356,\n    \"news_score_events_v1\": 169,\n    \"news_signal_events\": 169,\n    \"news_token_match_events\": 169\n  },\n  \"counts_before\": {\n    \"news_raw_feed_events\": 356,\n    \"news_score_events_v1\": 169,\n    \"news_signal_events\": 169,\n    \"news_token_match_events\": 169\n  },\n  \"db_path\": \"/root/tokenoskobi_clean_v1/
