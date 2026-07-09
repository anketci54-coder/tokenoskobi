# NEWS Runtime Freshness Monitor Plan NOAPI V1

Generated UTC: 2026-07-09T13:55:37.363643+00:00

## Decision

`OK_NEWS_RUNTIME_FRESHNESS_MONITOR_PLAN_NOAPI`

## Purpose

NEWS hattı artık iki taraflı izlenecek:

1. Freshness: veri taze mi, producer çalışıyor mu, NEWS katmanları bayatladı mı?
2. History: geçmiş veri sorgulanabilir mi, replay/backtest/evidence search için hazır mı?

## NOAPI Boundary

- API call: false
- Network call: false
- DB write: false
- DB schema change: false
- Index creation: false
- Service change: false
- Timer change: false
- Live trade: false
- Paper trade: false

## Monitored Tables

- news_raw_feed_events
- news_token_match_events
- news_signal_events
- news_score_events_v1

## Historical Alignment Locked

Historical Access Layer ayrı fazda kurulacak.

Zorunlu başlıklar:

- date_range query
- source_id query
- token/project query
- chain query
- severity/decision/route query
- event_uid lookup
- index strategy
- deduplication policy
- no duplicate raw_feed_events during future backfill

## Next

`NEWS_RUNTIME_FRESHNESS_MONITOR_DRYRUN_NOAPI`
