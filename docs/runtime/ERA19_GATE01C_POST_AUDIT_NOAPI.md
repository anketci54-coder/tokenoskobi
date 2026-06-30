# ERA19_GATE01C_POST_AUDIT_NOAPI

STATUS=PASS_READY_FOR_NEXT_GATE

CHECKS

{
  "GATE01": {
    "actual": "PLAN_ONLY_NOAPI",
    "exists": true,
    "expected": "PLAN_ONLY_NOAPI",
    "pass": true
  },
  "GATE01B": {
    "actual": "PASS_DRYRUN_NOAPI",
    "exists": true,
    "expected": "PASS_DRYRUN_NOAPI",
    "pass": true
  }
}

CROSS_CHECKS

{
  "event_driven_runtime": true,
  "gsn_enabled": true,
  "ledger_priority": true,
  "live_trade_disabled": true,
  "logical_time_only": true,
  "observe_full_load": true,
  "order_create_disabled": true,
  "recovery_ready": true,
  "runtime_ready": true,
  "signing_disabled": true,
  "triple_ledger": true,
  "wallet_disabled": true
}

DECISION

ERA19_GATE01_APPROVED

NEXT

ERA19_GATE02_LONG_RUN_STABILITY_PLAN_NOAPI
