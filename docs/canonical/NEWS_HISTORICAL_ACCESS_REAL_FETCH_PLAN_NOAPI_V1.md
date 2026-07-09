# NEWS Historical Access Real Fetch Plan NOAPI V1

Generated UTC: 2026-07-09T18:16:19.473712+00:00

Decision: OK_NEWS_HISTORICAL_ACCESS_REAL_FETCH_PLAN_NOAPI

Purpose:
Prepare historical NEWS real fetch without network/API/DB write in this step.

Current DB:
{
  "counts": {
    "news_raw_feed_events": 333,
    "news_score_events_v1": 147,
    "news_signal_events": 147,
    "news_token_match_events": 147
  },
  "derived_balanced": true,
  "earliest_raw": "2026-05-09T11:12:08+00:00",
  "integrity": "ok",
  "latest_by_table": {
    "news_score_events_v1": "2026-07-09T17:30:27.251469+00:00",
    "news_signal_events": "2026-07-09T17:30:27.251469+00:00",
    "news_token_match_events": "2026-07-09T17:30:27.251469+00:00"
  },
  "latest_raw": "2026-07-09T17:09:01+00:00",
  "source_counts": [
    {
      "earliest_seen": "2026-05-09T11:12:08+00:00",
      "latest_seen": "2026-07-09T17:09:01+00:00",
      "row_count": 323,
      "source_uid": "src_seed_crypto_news_rss"
    },
    {
      "earliest_seen": "2026-05-12T09:08:26.842796+00:00",
      "latest_seen": "2026-05-12T09:08:26.842796+00:00",
      "row_count": 10,
      "source_uid": "src_seed_official_exchange_announcements"
    }
  ]
}

Source discovery:
{
  "source_uid_count": 10,
  "source_uids": [
    {
      "paths": [
        "tools/hot_ingress_source_registry_minimal_contract_dryrun_noapi_v1.py"
      ],
      "source_uid": "src_bad_field_alpha"
    },
    {
      "paths": [
        "tools/runtime_whale_graph_v1.py"
      ],
      "source_uid": "src_label"
    },
    {
      "paths": [
        "tools/hot_ingress_source_registry_minimal_contract_dryrun_noapi_v1.py"
      ],
      "source_uid": "src_manual_synthetic_alpha"
    },
    {
      "paths": [
        "tools/hot_ingress_source_registry_minimal_contract_dryrun_noapi_v1.py"
      ],
      "source_uid": "src_missing_rate_limit"
    },
    {
      "paths": [
        "tools/hot_ingress_source_registry_minimal_contract_dryrun_noapi_v1.py"
      ],
      "source_uid": "src_missing_trust_policy"
    },
    {
      "paths": [
        "tools/hot_ingress_source_registry_minimal_contract_dryrun_noapi_v1.py"
      ],
      "source_uid": "src_onchain_alpha"
    },
    {
      "paths": [
        "tools/hot_ingress_source_registry_minimal_contract_dryrun_noapi_v1.py"
      ],
      "source_uid": "src_rss_alpha"
    },
    {
      "paths": [
        "config/news_derived_layer_refresher_runtime_binding_plan_v1.json",
        "config/news_producer_staleness_fix_real_apply_plan_v1.json",
        "tools/news_radar_refresh_runner_v1.ORIGINAL_NEWS27A11_20260510_211813.py"
      ],
      "source_uid": "src_seed_crypto_news_rss"
    },
    {
      "paths": [
        "tools/hot_ingress_source_registry_minimal_contract_dryrun_noapi_v1.py"
      ],
      "source_uid": "src_telegram_alpha"
    },
    {
      "paths": [
        "tools/hot_ingress_source_registry_minimal_contract_dryrun_noapi_v1.py"
      ],
      "source_uid": "src_unknown_alpha"
    }
  ],
  "url_source_file_count": 13,
  "url_sources": [
    {
      "path": "tools/provider_secret_vault_handler_v1.py",
      "url_count": 1,
      "urls": [
        "https://bnb-mainnet\\.g\\.alchemy\\.com/v2/[A-Za-z0-9_\\-]+$"
      ]
    },
    {
      "path": "tools/news_source_ingestion_runner_adapter_contract_check_v1.py",
      "url_count": 2,
      "urls": [
        "https://dryrun.local/adapter/accepted",
        "https://dryrun.local/adapter/missing-source"
      ]
    },
    {
      "path": "tools/runtime_activation_truth_audit_v1.py",
      "url_count": 1,
      "urls": [
        "https://panel.coinoskobi.com/data/"
      ]
    },
    {
      "path": "tools/system_center_live_producer_v1.py",
      "url_count": 2,
      "urls": [
        "https://panel.coinoskobi.com/",
        "https://panel.coinoskobi.com/data/backpressure_readmodel_refresh_cache.json"
      ]
    },
    {
      "path": "tools/news_radar_refresh_runner_v1.ORIGINAL_NEWS27A11_20260510_211813.py",
      "url_count": 2,
      "urls": [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/"
      ]
    },
    {
      "path": "tools/archive/patch_debt_20260706_n17_n21/n21_multi_center_production_master_bundle_v1.py",
      "url_count": 1,
      "urls": [
        "https://panel.coinoskobi.com/data/"
      ]
    },
    {
      "path": "tools/archive/patch_debt_20260706_n17_n21/n21g_final_panel_system_post_audit_v1.py",
      "url_count": 1,
      "urls": [
        "https://panel.coinoskobi.com/data/"
      ]
    },
    {
      "path": "tools/archive/patch_debt_20260706_n17_n21/n21c_risk_source_proof_bundle_v1.py",
      "url_count": 1,
      "urls": [
        "https://panel.coinoskobi.com/data/risk_center_live_readmodel_v1.json"
      ]
    },
    {
      "path": "tools/archive/patch_debt_20260706_n17_n21/n21e_full_center_post_audit_v1.py",
      "url_count": 1,
      "urls": [
        "https://panel.coinoskobi.com/data/"
      ]
    },
    {
      "path": "tools/archive/patch_debt_20260706_n17_n21/n21d_lifecycle_source_proof_bundle_v1.py",
      "url_count": 1,
      "urls": [
        "https://panel.coinoskobi.com/data/lifecycle_center_live_readmodel_v1.json"
      ]
    },
    

Next:
NEWS_HISTORICAL_ACCESS_REAL_FETCH_TEMPDB_DRYRUN_WITH_NETWORK
