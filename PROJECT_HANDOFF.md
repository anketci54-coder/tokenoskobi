<!-- NEWS_F_CURRENT_HANDOFF:START -->
# NEWS-F Current State

- generated_at_utc: `2026-07-08T13:04:26.805247+00:00`
- head: `8c0cdb3c3c63797959a0dd83b2872956dc67f47c`
- decision: `WARN_NEWS_F_FINAL_OPERATIONAL_SEAL_CLOSED_WITH_KNOWN_WARNINGS`
- status: `COLD_NEWS_PRODUCER_OPERATIONAL_WITH_KNOWN_WARNINGS`
- next_safe_step: `HOT_INTELLIGENCE_INGRESS_GATEWAY_PLAN_NOAPI`

## Counts

- raw: `270`
- match: `47`
- signal: `47`
- score: `47`
- freshness: `1`

## Timer

- active: `active`
- enabled: `enabled`
- role: `COLD_BACKFILL_FALLBACK_ONLY`

## Known Warnings

- `PANEL_READMODEL_COUNT_MATCH_NOT_FOUND`: DB sayılarıyla güçlü JSON/readmodel count eşleşmesi bulunamadı.
- `RAW_NEWER_THAN_DOWNSTREAM`: Raw haberler downstream match/signal/score zamanından daha yeni; downstream freshness/staleness takip edilmeli.
- `FRESHNESS_HEARTBEAT_STALER_THAN_RAW`: freshness heartbeat raw max timestamp'ten daha eski.
- `RAW_NEWER_THAN_DOWNSTREAM_CONFIRMED`: Raw producer yeni haber alıyor; downstream 47/47/47 zinciri yeni raw haberleri henüz işlemiyor.
- `PANEL_READMODEL_STRONG_COUNT_MATCH_ZERO`: DB sayılarıyla güçlü panel/readmodel JSON count eşleşmesi bulunmadı.

## Do Not Claim

- `NEWS_FULLY_CLEAN`
- `PANEL_FULLY_VERIFIED`
- `FRESHNESS_FULLY_CURRENT`
- `HOT_INTELLIGENCE_IMPLEMENTED`
- `REAL_TIME_INTELLIGENCE_COMPLETE`
- `TRADE_OR_PAPER_AUTHORITY_ENABLED`

## Doctrine

- `CENGIZHAN_INTELLIGENCE_DOCTRINE` is preserved.
- `HOT_INTELLIGENCE_INGRESS_GATEWAY` opens after this seal as a separate plan.
<!-- NEWS_F_CURRENT_HANDOFF:END -->

