# TOKENOSKOBI CLEAN V1 GUARDS

## Hard write guards

- No token row without token_uid.
- No pair row without pair_uid.
- No snapshot row without token_uid.
- No snapshot row without pair_uid.
- No snapshot row without chain.
- No snapshot row without pair_address.
- No source expansion if source is stale or identity is weak.
- No row-order matching.
- No metric-only relink.
- No old dirty snapshot import.

## Route guards

- Hard fail = REJECT.
- Medium risk + high opportunity = WATCH_ONLY / PAPER_TEST later, not live.
- High asymmetry can reduce size; it does not bypass safety.
- Sandwich Shield required before any micro-live.
- Live and paper must remain separate.

## API guards

- API default: blocked.
- Alchemy default: blocked.
- JSON-RPC default: blocked.
- DexScreener default: blocked until capped refresh phase.
- Telegram default: blocked until reporting phase.
- Timers default: blocked until explicit approval.
