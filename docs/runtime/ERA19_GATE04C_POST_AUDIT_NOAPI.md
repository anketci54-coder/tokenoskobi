# ERA19_GATE04C_POST_AUDIT_NOAPI

STATUS=PASS_READY_FOR_NEXT_GATE

CHECKS

{
  "GATE04": {
    "actual": "PLAN_ONLY_NOAPI",
    "exists": true,
    "expected": "PLAN_ONLY_NOAPI",
    "pass": true
  },
  "GATE04B": {
    "actual": "PASS_DRYRUN_NOAPI",
    "exists": true,
    "expected": "PASS_DRYRUN_NOAPI",
    "pass": true
  }
}

CROSS_CHECKS

{
  "dataset_time_authoritative": true,
  "deterministic_chain": true,
  "diff_reporting": true,
  "dryrun_all_pass": true,
  "event_driven": true,
  "gsn_chain": true,
  "live_trade_disabled": true,
  "logical_time_only": true,
  "order_create_disabled": true,
  "rolling_checksum": true,
  "signing_disabled": true,
  "snapshot_checksum": true,
  "system_time_forbidden": true,
  "wallet_disabled": true
}

DECISION

ERA19_GATE04_APPROVED

NEXT

ERA19_GATE05_SHADOW_MARKET_PLAN_NOAPI
