# V2_18B_FIX1_NETWORK_STRESS_TEST_PLAN_NOAPI

FINAL_GATE=PASS_V2_18B_FIX1_NETWORK_STRESS_TEST_PLAN_NOAPI
DECISION=NETWORK_STRESS_PLAN_ACCEPTED_READY_FOR_TEMPDB_DRYRUN

## Amaç

Ağ sürtünmesi, RPC gecikmesi, jitter, quote TTL expiry, pending tx delay, reorg mock ve mempool congestion baskısını planlamak.

Bu faz plan-only NOAPI'dir.

## Hız Doktrini

HIZDAN_TAVIZ=false
HOT_PATH_NEVER_WAITS=true
NETWORK_LATENCY_MODE=MODELED_NOT_SLEPT

Latency gerçek sleep olarak uygulanmaz.
Latency sadece risk, TTL, cancel/wait ve backpressure kararına etki eder.

## Ana Kurallar

STALE_QUOTE_CANNOT_TRADE=true
PENDING_TX_CANNOT_FORCE_ENTRY=true
REORG_RISK_REQUIRES_CONFIRMATION=true
BACKPRESSURE_CANNOT_EXPAND_HUMAN_GATEWAY=true
HUMAN_GATEWAY_TOP3_CAP_REQUIRED=true

## Stress Profilleri

[
  {
    "profile": "BASELINE_GOOD_RPC",
    "latency_p50_ms": 120,
    "latency_p95_ms": 220,
    "latency_p99_ms": 280,
    "jitter_ms": 40,
    "ttl_sec": 5,
    "expected_action": "ALLOW_IF_QUOTE_FRESH"
  },
  {
    "profile": "JITTER_SPIKE",
    "latency_p50_ms": 220,
    "latency_p95_ms": 650,
    "latency_p99_ms": 1100,
    "jitter_ms": 420,
    "ttl_sec": 5,
    "expected_action": "REQUOTE_OR_WAIT"
  },
  {
    "profile": "QUOTE_TTL_EXPIRY",
    "latency_p50_ms": 480,
    "latency_p95_ms": 1200,
    "latency_p99_ms": 2400,
    "jitter_ms": 900,
    "ttl_sec": 2,
    "expected_action": "HARD_BLOCK_STALE_QUOTE"
  },
  {
    "profile": "PENDING_TX_DELAY",
    "latency_p50_ms": 350,
    "latency_p95_ms": 1500,
    "latency_p99_ms": 4000,
    "jitter_ms": 1400,
    "ttl_sec": 4,
    "expected_action": "CANCEL_OR_SHADOW_ONLY"
  },
  {
    "profile": "MEMPOOL_CONGESTION",
    "latency_p50_ms": 700,
    "latency_p95_ms": 2500,
    "latency_p99_ms": 6000,
    "jitter_ms": 2100,
    "ttl_sec": 3,
    "expected_action": "BACKPRESSURE_AND_NO_ENTRY"
  },
  {
    "profile": "REORG_MOCK",
    "latency_p50_ms": 500,
    "latency_p95_ms": 1800,
    "latency_p99_ms": 3500,
    "jitter_ms": 1000,
    "ttl_sec": 4,
    "expected_action": "WAIT_FOR_CONFIRMATION"
  },
  {
    "profile": "RPC_DEGRADED_PROVIDER",
    "latency_p50_ms": 1000,
    "latency_p95_ms": 4500,
    "latency_p99_ms": 9000,
    "jitter_ms": 3500,
    "ttl_sec": 2,
    "expected_action": "PROVIDER_DEGRADED_ROUTE_BLOCK"
  }
]

## Decision Matrix

[
  {
    "condition": "quote_fresh_and_latency_ok",
    "action": "ALLOW_SHADOW_CANDIDATE_ONLY"
  },
  {
    "condition": "quote_ttl_expired",
    "action": "HARD_BLOCK_REQUOTE_REQUIRED"
  },
  {
    "condition": "pending_tx_delay_high",
    "action": "CANCEL_OR_WAIT"
  },
  {
    "condition": "reorg_risk_detected",
    "action": "WAIT_CONFIRMATION"
  },
  {
    "condition": "mempool_congestion_high",
    "action": "BACKPRESSURE_DOWNRANK"
  },
  {
    "condition": "rpc_degraded",
    "action": "PROVIDER_ROUTE_BLOCK_NO_CALL"
  },
  {
    "condition": "human_top3_overflow",
    "action": "SUPPRESS_TO_WATCHLIST"
  }
]

## Yetki Kilitleri

REAL_BUY_COUNT=0
REAL_SELL_COUNT=0
TRADE_AUTHORITY=0
WALLET_AUTHORITY=0
LIVE_TRADE=0
AUTO_EXECUTE=0
AUTO_APPLY=0
AUTO_PATCH=0
PROVIDER_CALL_NOW=0
EXTERNAL_API_CALL_NOW=0
LIVE_DB_WRITE=0
PANEL_WRITE=0

## Canlı Koruma

DB_INTEGRITY=ok
DB_QUICK=ok
DB_FK_COUNT=0
DB_SHA_CHANGED=false
PANEL_SHA_CHANGED=false
PROTECTED_DIFF_EMPTY=true

## Audit

AUDIT_CHECK_COUNT=28
AUDIT_FAIL_COUNT=0

## Sonraki Güvenli Adım

V2_18B_FIX1_NETWORK_STRESS_TEST_TEMPDB_DRYRUN_NOAPI
