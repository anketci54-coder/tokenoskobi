# RUNTIME_SLICE_09B_REPAIR_EXPLICIT_PROVIDER_ALLOWLIST_NOAPI

STATUS=PLAN_ONLY_NOAPI
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

REPAIR_RULES
- wildcard env RPC discovery is forbidden
- allowed env names only: TOKENOSKOBI_RPC_BSC, TOKENOSKOBI_RPC_BASE
- max_provider=1
- allowed_methods=eth_chainId,eth_blockNumber
- timeout_seconds_max=3
- sequential=true
- async_required=false

NEXT
RUNTIME_SLICE_09B_RETRY_LIVE_READONLY_RPC_SMOKE_TEST_AFTER_EXPLICIT_APPROVAL
