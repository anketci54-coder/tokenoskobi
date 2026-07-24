# ERA64I Bounded Historical Wallet Event Backfill

STATUS=BOUNDED_HISTORICAL_WALLET_TRANSFER_BACKFILL_VERIFIED

ERA64I performs a bounded historical BSC scan using allowlisted read-only RPC methods. It samples ERC-20 Transfer logs for canonical BSC base and quote assets across a bounded 4,096-block historical range using wallet-topic filters and writes only to a dedicated ERA64I staging SQLite database.

The dataset is real and non-synthetic. It preserves transaction hash, log index, block number, verified block timestamp, token address, transfer endpoints, raw amount, provider provenance and evidence hashes. It does not yet include transaction receipts, gas costs, swap direction, execution price or closed trade cycles. Therefore successful-wallet classification remains blocked.

No production database, panel, service or timer is mutated. Paper trading, live trading, wallet, signing, order creation and broadcast authority remain disabled.
