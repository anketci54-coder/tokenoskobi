# Product Slice 04 Branch Scope

This branch contains bounded read-only audit and candidate-enrichment tools for `PRODUCT_SLICE_04_DEX_WALLET_CEX_GRAPH_AND_PERFORMANCE`.

Current evidence gate:

- inspect the immutable ERA64I/ERA64J staging database
- enrich exactly 14 candidate BSC transactions and 3 tracked token contracts
- preserve historical transaction and receipt identity
- attempt historical token metadata first
- permit `latest` token metadata fallback only when all allowlisted endpoints explicitly report archive-state unavailability
- record that temporal limitation in the output
- do not classify swap direction, router/pool identity, closed loops, CEX identity, or profitability before later evidence gates

Authority remains read-only and non-financial. No panel, service, production database, paper-trade, live-trade, wallet, signing, order, or broadcast authority is created.
