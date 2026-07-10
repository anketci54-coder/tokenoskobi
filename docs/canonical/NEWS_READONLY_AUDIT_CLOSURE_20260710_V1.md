# NEWS READ-ONLY AUDIT CLOSURE — 2026-07-10

## Final decision

`PASS_ALL_GAP_ROWS_EXACT_WATERMARK_EXCLUDED`

## Verified evidence

- Audited canonical HEAD: `f2ccbc1784d0f7a4a7555dcad348abe0fd3729da`
- Source quick check: `ok`
- Snapshot integrity: `ok`
- Snapshot SHA unchanged during audit: `true`
- Raw / match / signal / score UID counts: `374 / 185 / 185 / 185`
- Raw rows without score: `189`
- Exact historical watermark exclusions: `189`
- After-watermark unresolved rows: `0`
- Proven data-loss count: `0`
- Duplicate `news_uid` count across all four pipeline tables: `0`
- Bad trade flags: `0`

## Correct interpretation

The raw-to-score difference is a historical watermark coverage gap, not proven runtime data loss. Runtime candidate-time semantics are:

`COALESCE(published_at_utc, fetched_at_utc)`

All 189 raw rows without scores were at or before the latest derived watermark. No unresolved record remained.

## Authority boundaries

- No DB write
- No schema/index mutation
- No service/timer mutation
- No repository mutation by the server auditor
- No trade, paper-trade, wallet, signing, or execution authority
- No new ERA opened

## Decision

- Schema change: `HOLD_NOT_REQUIRED`
- Historical backfill: `HOLD_NOT_REQUIRED`
- Runner refactor: `HOLD_NOT_REQUIRED`
- Disposition ledger: `HOLD_NOT_REQUIRED_FROM_THIS_AUDIT`
- Next safe step: `NEXT_MAJOR_PROJECT_LINE_SELECTION`
