# NEWS Historical Access Layer Plan NOAPI V1

Generated UTC: 2026-07-09T14:23:27.504744+00:00

## Decision

`OK_NEWS_HISTORICAL_ACCESS_LAYER_PLAN_NOAPI`

## Purpose

NEWS geçmiş verisi sorgulanabilir veri ambarı haline getirilecek.

Bu adım sadece plandır:

- API yok
- Network yok
- DB write yok
- Index creation yok
- Backfill yok
- Trade yok

## Historical Scope

- news_raw_feed_events
- news_token_match_events
- news_signal_events
- news_score_events_v1
- sealed control artifacts

## Query Contract

Temel sorgular:

- date_range
- source_uid / source_id
- news_uid
- event_uid from new artifacts
- symbol/token
- chain
- risk_label / importance_label / fusion_label
- signal_type / signal_strength
- decision / route from artifacts
- title / evidence_text
- url_hash / raw_hash

## Index Strategy

Index stratejisi planlandı ama bu fazda index oluşturulmadı.

Candidate index count: 15

## Deduplication Policy

Dedup zorunlu.

Future backfill sırasında raw_feed_events duplicate üretmeyecek.

## Next

`NEWS_HISTORICAL_ACCESS_LAYER_DRYRUN_NOAPI`
