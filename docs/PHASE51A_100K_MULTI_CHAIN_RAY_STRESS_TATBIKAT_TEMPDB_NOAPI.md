# PHASE51A_100K_MULTI_CHAIN_RAY_STRESS_TATBIKAT_TEMPDB_NOAPI

STATUS=TEMPDB_TATBIKAT_ONLY

TEMP_DB=/tmp/PHASE51A_100K_MULTI_CHAIN_RAY_STRESS_TATBIKAT_TEMPDB_NOAPI_20260622_090608/tokenoskobi_phase51a_100k_temp.sqlite
LIVE_DB_UNCHANGED=true

{
  "avg_batch_ms": 4.227,
  "avg_lookup_ms": 0.082,
  "avg_per_token_ms": 0.005634,
  "batch_count": 100,
  "batch_size": 1000,
  "candidate_count": 8184,
  "chain_count": 12,
  "dex_count": 6,
  "final_gate": "PASS_PHASE51A_100K_MULTI_CHAIN_RAY_STRESS_TATBIKAT_TEMPDB_NOAPI",
  "foreign_key_check_count": 0,
  "hot_path_ok": true,
  "integrity": "ok",
  "p95_batch_ms": 6.498,
  "p95_lookup_ms": 0.119,
  "p99_batch_ms": 6.732,
  "p99_lookup_ms": 0.133,
  "quarantine_count": 5627,
  "reject_count": 4347,
  "tokens_per_second": 177482.83,
  "total_ms": 563.435,
  "total_tokens": 100000,
  "watch_count": 81842
}

FINAL_GATE=PASS_PHASE51A_100K_MULTI_CHAIN_RAY_STRESS_TATBIKAT_TEMPDB_NOAPI
