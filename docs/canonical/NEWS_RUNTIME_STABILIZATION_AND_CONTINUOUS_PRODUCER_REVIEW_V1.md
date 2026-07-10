# NEWS Runtime Stabilization And Continuous Producer Review V1

Generated UTC: 2026-07-10T04:48:17.043753+00:00

Decision: FAIL_NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW

DB counts:
{
  "news_raw_feed_events": 353,
  "news_score_events_v1": 166,
  "news_signal_events": 166,
  "news_token_match_events": 166
}

UID collision review:
{
  "collision_risk": "LOW_HIST_AND_NON_HIST_NAMESPACES_SEPARATED",
  "hist_prefix_count": 8,
  "match_news_uid_duplicates": [],
  "namespace_stats": [
    {
      "count": 8,
      "namespace": "historical_hist_news"
    },
    {
      "count": 34,
      "namespace": "live_or_runtime_news"
    },
    {
      "count": 311,
      "namespace": "other"
    }
  ],
  "non_hist_count": 345,
  "notes": [
    "raw_event_hash_column_absent_schema_hardening_backlog"
  ],
  "raw_news_uid_duplicates": [],
  "sample_hist": [
    {
      "fetched_at_utc": "2026-07-10T04:00:44.505461+00:00",
      "news_uid": "hist_news_0f7fa5501604267857040d24",
      "published_at_utc": "2026-07-09T06:40:50+00:00",
      "title": "A trader turns $800 into over $1 million on Robinhood's brand new blockchain betting on memecoin"
    },
    {
      "fetched_at_utc": "2026-07-10T04:00:44.505440+00:00",
      "news_uid": "hist_news_87d29fdbeaf69e1f32f3e5d7",
      "published_at_utc": "2026-07-09T06:51:10+00:00",
      "title": "Live updates: Bitcoin rises to $63,000, oil and bond yields drop as markets look past latest Iran dustup"
    },
    {
      "fetched_at_utc": "2026-07-10T04:00:44.505420+00:00",
      "news_uid": "hist_news_e690c71822d00d7c9d518f24",
      "published_at_utc": "2026-07-09T09:31:56+00:00",
      "title": "Two blockbuster public debut of AI stocks could pull away more capital from crypto"
    },
    {
      "fetched_at_utc": "2026-07-10T04:00:44.505292+00:00",
      "news_uid": "hist_news_0f36df09dffc5b6c7fd7df31",
      "published_at_utc": "2026-07-09T15:53:42+00:00",
      "title": "AI contracts, not bitcoin, now drive miner valuations, and Cipher and TeraWulf look cheap, says analyst"
    },
    {
      "fetched_at_utc": "2026-07-10T04:00:44.505181+00:00",
      "news_uid": "hist_news_257b3286459432dcd3a95bf1",
      "published_at_utc": "2026-07-10T03:57:58+00:00",
      "title": "Bitcoin zips higher to nearly $64,000 as chip rally and yen strength drive gains"
    },
    {
      "fetched_at_utc": "2026-07-10T04:00:44.428539+00:00",
      "news_uid": "hist_news_54f18820876fc1cc512bb274",
      "published_at_utc": "2026-07-09T08:51:48+00:00",
      "title": "Swift launches blockchain ledger with 17-bank tokenized deposit pilot"
    },
    {
      "fetched_at_utc": "2026-07-10T04:00:44.428375+00:00",
      "news_uid": "hist_news_83d967a72e31517d9500a5ac",
      "published_at_utc": "2026-07-09T19:48:37+00:00",
      "title": "White House says it received no Democratic response related to SEC, CFTC vacancies"
    },
    {
      "fetched_at_utc": "2026-07-10T04:00:44.428364+00:00",
      "news_uid": "hist_news_f36c6c22f559f46498acce69",
      "published_at_utc": "2026-07-09T20:17:33+00:00",
      "title": "Here’s what happened in crypto today"
    }
  ],
  "sample_non_hist": [
    {
      "fetched_at_utc": "2026-07-10T03:31:20.961475+00:00",
      "news_uid": "timer_news_bd7bde495d74e70b1ac4",
      "published_at_utc": "2026-07-10T03:07:47+00:00",
      "title": "Hackers tried to backdoor Injective npm package to steal wallet keys"
    },
    {
      "fetched_at_utc": "2026-07-10T02:51:19.922047+00:00",
      "news_uid": "timer_news_65a979dd9dd455bbb598",
      "published_at_utc": "2026-07-10T02:30:44+00:00",
      "title": "DeFi may be ‘quietly re-rating’ given outperformance against Bitcoin: Bitwise"
    },
    {
      "fetched_at_utc": "2026-07-09T22:30:58.023649+00:00",
      "news_uid": "timer_news_1a2f927195e1cfbe7475",
      "published_at_utc": "2026-07-09T22:19:54+00:00",
      "title": "New Hampshire snuffs out trailblazing state-government bitcoin bond effort"
    },
    {
      "fetched_at_utc": "2026-07-09T21:50:52.404383+00:00",
      "news_uid": "timer_news_de862dceaaa079b6ed99",
      "published_at_utc": "2026-07-09T21:35:12+00:00",
      "title": "Coinbase chief legal officer to transition to advisory role on July 31"
    },
    {
      "fetched_at_utc": "2026-07-09T20:50:49.062980+00:00",
      "news_uid": "timer_news_a456fca26f2671acfe93",
      "published_at_utc": "2026-07-09T20:31:39+00:00",
      "title": "With SEC fight over, Coinbase's top legal exec Grewal moves on, and others reassigned"
    },
    {
      "fetched_at_utc": "2026-07-09T20:50:49.062932+00:00",
      "news_uid": "timer_news_d72002723e2285d45a60",
      "published_at_utc": "2026-07-09T20:42:49+00:00",
      "title": "Grayscale's CFO exits after 7 years with crypto asset manager"
    },
    {
      "fetched_at_utc": "2026-07-09T20:30:47.928999+00:00",
      "news_uid": "timer_news_1f28652692d50a836eb0",
      "published_at_utc": "2026-07-09T20:28:51+00:00",
      "title": "Arbitrum jumps 19% benefitting from Robinhood's $568 million onchain trading frenzy"
    },
    {
      "fetched_at_utc": "2026-07-09T20:30:47.849160+00:00",
      "news_uid": "timer_news_3188dd26ecb52d49fbcc",
      "published_at_utc": "2026-07-09T20:19:15+00:00",
      "title": "Bitdeer stock jumps 14% as company expands US mining hardware production"
    },
    {

Freshness review:
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
  "latest": {
    "created_at_utc": "2026-07-10T04:42:42.934777+00:00",
    "last_observed_at_utc": "2026-07-10T04:00:44.505461+00:00"
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
}

Systemd review:
{
  "service_active": "inactive",
  "service_active_rc": 3,
  "service_execstart_lines": [
    "ExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py"
  ],
  "service_show_rc": 0,
  "service_text_sha256": "97829c2a13305a6b011dec317f89b710d6c605715cfbfdecab7bb5291fc5fe4b",
  "service_unit_exists": true,
  "timer_active": "active",
  "timer_active_rc": 0,
  "timer_enabled": "enabled",
  "timer_enabled_rc": 0,
  "timer_schedule_lines": [
    "OnActiveSec=20min",
    "OnUnitActiveSec=20min",
    "Unit=tokenoskobi-news-radar-refresh.service"
  ],
  "timer_show_rc": 0,
  "timer_text_sha256": "47e5dacef0e068480bb2de67960f5320469910ab6ded80937266cf68081f1af5",
  "timer_unit_exists": true
}

Runner review:
{
  "derived_helper_exists": true,
  "derived_helper_sha256": "e5e516456376d45c977a0a4aa2508fdd57ccd21f8394db960db8c9ec471ff532",
  "helper_line_count": 377,
  "runner_exists": true,
  "runner_line_count": 19,
  "runner_mentions_db_path": true,
  "runner_mentions_derived_helper": true,
  "runner_mentions_original_backup": true,
  "runner_mentions_stage": true,
  "runner_mentions_write": true,
  "runner_sha256": "173a6bd91913b306dddf71f31d1cb76d45f5ef992dcb1efe8df9c2550167faf2"
}

Remaining after this if OK:
[
  "NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI",
  "NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN_AND_POST_AUDIT_SEAL"
]

Next:
NEWS_RUNTIME_STABILIZATION_REVIEW_HOLD
