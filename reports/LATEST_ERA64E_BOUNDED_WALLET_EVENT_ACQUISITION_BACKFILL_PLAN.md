# ERA64E Bounded Real Wallet Event Acquisition and Backfill Plan

STATUS=BOUNDED_REAL_WALLET_EVENT_ACQUISITION_BACKFILL_PLAN_LOCKED

ERA64D proved that the source contracts and classification bridge are ready, while all eight candidate real wallet event tables remain empty. ERA64E locks a bounded, read-only, real-data acquisition and historical backfill plan. No network acquisition or database write occurs in this stage.

The next stage may run only after separate user approval. It must use an allowlisted BSC read-only endpoint, a fixed historical block window, strict request and runtime budgets, reorg-safe confirmation depth, deterministic deduplication, and fail-closed rejection of incomplete evidence. Database writes remain separately gated.
