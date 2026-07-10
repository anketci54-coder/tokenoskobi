# BAD Trade Flags Root Cause Audit NOAPI V1

Generated UTC: 2026-07-10T05:00:39.043550+00:00

Decision: OK_BAD_TRADE_FLAGS_ROOT_CAUSE_AUDIT_NOAPI

Bad trade flags:
{
  "count": 47,
  "distinct_news_uid_count": 47,
  "groupings": {
    "by_chain": [
      {
        "bucket": "Bitcoin",
        "count": 35
      },
      {
        "bucket": "XRP",
        "count": 6
      },
      {
        "bucket": "Solana",
        "count": 4
      },
      {
        "bucket": "Ethereum",
        "count": 2
      }
    ],
    "by_created_at_day": [
      {
        "bucket": "2026-07-06",
        "count": 47
      }
    ],
    "by_flag_tuple": [
      {
        "bucket": "1/0/0",
        "count": 47
      }
    ],
    "by_match_type": [
      {
        "bucket": "REAL_ENTITY_MATCH",
        "count": 47
      }
    ],
    "by_namespace": [
      {
        "bucket": "timer_news",
        "count": 47
      }
    ],
    "by_paper_signal": [
      {
        "bucket": 0,
        "count": 47
      }
    ],
    "by_symbol": [
      {
        "bucket": "BTC",
        "count": 35
      },
      {
        "bucket": "XRP",
        "count": 6
      },
      {
        "bucket": "SOL",
        "count": 4
      },
      {
        "bucket": "ETH",
        "count": 2
      }
    ],
    "by_trade_signal": [
      {
        "bucket": 0,
        "count": 47
      }
    ],
    "by_write_allowed": [
      {
        "bucket": 1,
        "count": 47
      }
    ]
  },
  "samples": [
    {
      "chain": "Bitcoin",
      "created_at_utc": "2026-07-06T06:44:10.281722+00:00",
      "evidence_text": "Bitcoin price taps new July high above $62K on weak US jobs data",
      "match_confidence": "MEDIUM",
      "match_reasons_json": "[\"NAME_SUBSTRING\", \"CHAIN_HINT\", \"TRACKED_TOKEN_PAIR_PRESENT\"]",
      "match_score": 45,
      "match_type": "REAL_ENTITY_MATCH",
      "match_uid": "match_fd92150eabfab66dd086",
      "news_uid": "timer_news_6dd83885fc858ec914f2",
      "pair_uid": "dict_btc_usd",
      "paper_signal": 0,
      "source_uid": "src_seed_crypto_news_rss",
      "symbol": "BTC",
      "token_uid": "dict_btc",
      "trade_signal": 0,
      "write_allowed": 1
    },
    {
      "chain": "Bitcoin",
      "created_at_utc": "2026-07-06T06:44:10.282166+00:00",
      "evidence_text": "SBI Crypto to shut down mining pool that holds roughly 2% of Bitcoin's hashrate",
      "match_confidence": "MEDIUM",
      "match_reasons_json": "[\"NAME_SUBSTRING\", \"CHAIN_HINT\", \"TRACKED_TOKEN_PAIR_PRESENT\"]",
      "match_score": 45,
      "match_type": "REAL_ENTITY_MATCH",
      "match_uid": "match_9c2f763d48f5fa110be4",
      "news_uid": "timer_news_4cbd493333460ebb5d57",
      "pair_uid": "dict_btc_usd",
      "paper_signal": 0,
      "source_uid": "src_seed_crypto_news_rss",
      "symbol": "BTC",
      "token_uid": "dict_btc",
      "trade_signal": 0,
      "write_allowed": 1
    },
    {
      "chain": "Bitcoin",
      "created_at_utc": "2026-07-06T06:44:10.282197+00:00",
      "evidence_text": "JPMorgan says Strategy's bitcoin sales policy adds 'two-way risk' to crypto markets",
      "match_confidence": "MEDIUM",
      "match_reasons_json": "[\"NAME_SUBSTRING\", \"CHAIN_HINT\", \"TRACKED_TOKEN_PAIR_PRESENT\"]",
      "match_score": 45,
      "match_type": "REAL_ENTITY_MATCH",
      "match_uid": "match_e1706d3ff10b792fcbdf",
      "news_uid": "timer_news_f8d0b373f0e3824d392f",
      "pair_uid": "dict_btc_usd",
      "paper_signal": 0,
      "source_uid": "src_seed_crypto_news_rss",
      "symbol": "BTC",
      "token_uid": "dict_btc",
      "trade_signal": 0,
      "write_allowed": 1
    },
    {
      "chain": "Bitcoin",
      "created_at_utc": "2026-07-06T06:44:10.282210+00:00",
      "evidence_text": "A struggling Nasdaq-listed company that tried to copy Saylor's Bitcoin playbook is completely dumping crypto for AI",
      "match_confidence": "MEDIUM",
      "match_reasons_json": "[\"NAME_SUBSTRING\", \"CHAIN_HINT\", \"TRACKED_TOKEN_PAIR_PRESENT\"]",
      "match_score": 45,
      "match_type": "REAL_ENTITY_MATCH",
      "match_uid": "match_bad39759a14a7cecbdb7",
      "news_uid": "timer_news_873307132f8c8647cef8",
      "pair_uid": "dict_btc_usd",
      "paper_signal": 0,
      "source_uid": "src_seed_crypto_news_rss",
      "symbol": "BTC",
      "token_uid": "dict_btc",
      "trade_signal": 0,
      "write_allowed": 1
    },
    {
      "chain": "Bitcoin",
      "created_at_utc": "2026-07-06T06:44:10.282227+00:00",
      "evidence_text": "Warsh's comments set the stage for U.S. jobs data to ignite bitcoin, gold rally",
      "match_confidence": "MEDIUM",
      "match_reasons_json": "[\"NAME_SUBSTRING\", \"CHAIN_HINT\", \"TRACKED_TOKEN_PAIR_PRESENT\"]",
      "match_score": 45,
      "match_type": "REAL_ENTITY_MATCH",
      "match_uid": "match_029378f0ac1a4ea6c69e",
      "news_uid": "timer_news_64b82e5238d536886500",
      "pair_uid": "dict_btc_usd",
      "paper_signal": 0,
      "source_uid": "src_seed_crypto_news_rss",
      "symbol": "BTC",
      "token_uid": "dict_btc",
      "trade_signal": 0,
      "write_allowed": 1
    },
    {
      "chain": "Solana",
      "created_at_utc": "2026-07-06T06:44:10.282237+00:00",
      "evidence_text": "Smaller tokens lead as bitcoin, sol rally in 'first real bounce of the selloff'",
      "match_confidence": "MEDIUM",
      "match_reasons_json": "[\"SYMBOL_EXACT_WORD\", \"TRACKED_TOKEN_PAIR_PRESENT\"]",
      "match_score": 50,
      "match_type": "REAL_ENTITY_MATCH",
      "match_uid": "match_9159c3432325bbe081e8",
      "news_uid": "timer_news_112ba97cd3e8bf297fb2",
      "pair_uid": "dict_sol_usd",
      "paper_signal": 0,
      "source_uid": "src_seed_crypto_news_rss",
      "symbol": "SOL",
      "token_uid": "dict_sol",
      "trade_signal": 0,
      "write_allowed": 1
    },
    {
      "chain": "Solana",
      "created_at_utc": "2026-07-06T06:44:10.282250+00:00",
      "evidence_text": "Solana Foundation launches framework for protocol-level governance",
      "match_confidence": "MEDIUM",
      "match_reasons_json": "[\"NAME_SUBSTRING\", \"CHAIN_HINT\", \"TRACKED_TOKEN_PAIR_PRESENT\"]",
      "match_score": 45,
      "match_type": "REAL_ENTITY_MATCH",
      "match_uid": "match_c022edbc4af0dfc7923d",
      "news_uid": "timer_news_57301c6f675b5cb997ab",
      "pair_uid": "dict_sol_usd",
      "paper_signal": 0,
      "source_uid": "src_seed_crypto_news_rss",
      "symbol": "SOL",
      "token_uid": "dict_sol",
      "trade_signal": 0,
      "write_allowed": 1
    },
    {
      "chain": "Bitcoin",
      "created_at_utc": "2026-07-06T06:44:10.282259+00:00",
      "evidence_text": "SBI Crypto shuts Bitcoin mining pool after 5-year run",
      "match_confidence": "MEDIUM",
      "match_reasons_json": "[\"NAME_SUBSTRING\", \"CHAIN_HINT\", \"TRACKED_TOKEN_PAIR_PRESENT\"]",
      "match_score": 45,
      "match_type": "REAL_ENTITY_MATCH",
      "match_uid": "match_da3bdaeeac42ca83ca96",
      "news_uid": "timer_news_014484a8e6600f095248",
      "pair_uid": "dict_btc_usd",
      "paper_signal": 0,
      "source_uid": "src_seed_crypto_news_rss",
      "symbol": "BTC",
      "token_uid": "dict_btc",
      "trade_signal": 0,

Cleanup scope:
{
  "bad_distinct_news_uid_count": 47,
  "bad_total_rows": 47,
  "candidate_cleanup_action": "SET write_allowed=0, trade_signal=0, paper_signal=0 for rows where any flag is nonzero",
  "historical_bad_rows": 0,
  "historical_layer_impacted": false,
  "network_required": false,
  "requires_backup": true,
  "schema_change_required": false,
  "service_timer_required": false
}

Derived impact:
{
  "all_bad_uids_have_match": true,
  "all_bad_uids_have_raw": true,
  "chain_status_sample": [
    {
      "match_count": 1,
      "news_uid": "timer_news_014484a8e6600f095248",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_06190b518f19edcc6633",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_0863d150362d73c15fa4",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_09ea01131dc0a66aa19c",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_0c694e29c809e9b661d4",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_0d4a76a59efa908efdee",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_0daccd38bf6d129fe28c",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_112ba97cd3e8bf297fb2",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_1897e0cb89fce98d1215",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_1b3772ad88fa8f306d73",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_24cee79f74834ad00c59",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_25aee68a19064fbbba0c",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_2a603920e3189528b093",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_2b54cc059b6c68708912",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_2fb47c476037403d0c77",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_3413a4b88c44aea4fc8f",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_392414ecfa44ca43c30b",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_3e4656db83bffe9a1b00",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_4cbd493333460ebb5d57",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_540e85ba60cdf01de2b6",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_5724c620274a106c442a",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_57301c6f675b5cb997ab",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_64b82e5238d536886500",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_6b16dc3d58d80d632d0f",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_6dd83885fc858ec914f2",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_873307132f8c8647cef8",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_8787ed77f2ebf5bbaef6",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_89eea240b54e4bca0eae",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_8cbf5c693da62f7ca26c",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_8ef3e1483e093f65535e",
      "raw_count": 1,
      "score_count": 1,
      "signal_count": 1
    },
    {
      "match_count": 1,
      "news_uid": "timer_news_9053a2455b12b6fbe33b",
      "raw_count": 1

Outer news delta:
{
  "news_raw_feed_events": 0,
  "news_score_events_v1": 0,
  "news_signal_events": 0,
  "news_token_match_events": 0
}

Remaining after this if OK:
[
  "BAD_TRADE_FLAGS_CLEANUP_APPLY_WITH_BACKUP_NOAPI",
  "NEWS_RUNTIME_STABILIZATION_REVIEW_RETRY_NOAPI",
  "NEWS_CONTINUOUS_PRODUCER_DRYRUN_PLAN_NOAPI",
  "NEWS_CONTINUOUS_PRODUCER_CONTROLLED_DRYRUN_AND_POST_AUDIT_SEAL"
]

Next:
BAD_TRADE_FLAGS_CLEANUP_APPLY_WITH_BACKUP_NOAPI
