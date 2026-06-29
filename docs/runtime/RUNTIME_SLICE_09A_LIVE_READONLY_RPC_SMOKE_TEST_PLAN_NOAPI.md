# RUNTIME_SLICE_09A_LIVE_READONLY_RPC_SMOKE_TEST_PLAN_NOAPI
STATUS=PLAN_ONLY
API_CALLS=0
DB_WRITE=False
PANEL_WRITE=False
LIVE_TRADE=False
PAPER_TRADE=False
WALLET=False
SIGNING=False
ORDER_CREATE=False

PURPOSE
Plan explicit-approval live readonly RPC smoke test.

BOUNDARY
09A produces only plan artifacts. No RPC/API call. No DB write. No panel write. No service/timer change. No trade, wallet, signing or order authority.

ALLOWED_METHODS_FOR_09B
- eth_chainId
- eth_blockNumber

FORBIDDEN_FOR_09B
- eth_send*
- personal_*
- wallet_*
- debug_*
- miner_*
- admin_*
- transaction creation
- signing
- DB write
- panel write
- service restart
- timer enable

NEXT
RUNTIME_SLICE_09B_LIVE_READONLY_RPC_SMOKE_TEST_APPLY_AFTER_EXPLICIT_APPROVAL
