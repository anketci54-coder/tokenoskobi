# RUNTIME_SLICE_10B_TOXIC_SIGNAL_INJECTION_DRYRUN_NOAPI

STATUS=PASS_DRYRUN_NOAPI
API_CALLS=0
DB_WRITE=false
PANEL_WRITE=false
SERVICE_RESTART=false
TIMER_CHANGE=false
LIVE_TRADE=false
PAPER_TRADE=false
WALLET=false
SIGNING=false
ORDER_CREATE=false

DECISION_MATRIX
wrong_chain_id -> FAIL_CLOSED
negative_block -> FAIL_CLOSED
non_hex_block -> FAIL_CLOSED
stale_block -> OBSERVE_ONLY
future_block_jump -> FAIL_CLOSED
provider_disagreement -> OBSERVE_ONLY
malformed_rpc_response -> FAIL_CLOSED
rpc_error_as_result -> FAIL_CLOSED
