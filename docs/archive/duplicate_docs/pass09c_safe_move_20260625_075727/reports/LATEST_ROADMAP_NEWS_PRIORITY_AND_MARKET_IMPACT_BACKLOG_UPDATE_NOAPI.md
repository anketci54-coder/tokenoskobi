# ROADMAP NEWS PRIORITY AND MARKET IMPACT BACKLOG UPDATE NOAPI

- final_status: **PASS**
- current_priority: `FINISH_BINANCE_OKX_NEWS_FLOW_FIRST`
- next_phase: `NEWS_SOURCE_RAW_INGESTION_DRYRUN_NOAPI`
- roadmap_items_added_or_updated: `13`
- completed_items_ensured: `6`

## Bitenler
- ✅ `NEWS_SOURCE_ENDPOINT_UPDATE_APPLY_REAL_AFTER_EXPLICIT_APPROVAL` — Binance+OKX endpointleri DB’ye yazıldı; fetch hâlâ kapalı.
- ✅ `NEWS_SOURCE_ENDPOINT_UPDATE_POST_APPLY_AUDIT_NOAPI` — Endpoint yazımı audit edildi; 2/2 endpoint OK.
- ✅ `NEWS_SOURCE_MINI_FETCH_PLAN_NOAPI` — Binance+OKX için küçük fetch planı hazırlandı.
- ✅ `NEWS_SOURCE_MINI_FETCH_REAL_AFTER_EXPLICIT_APPROVAL` — Binance+OKX temp mini fetch çalıştı; 10 sample item çıktı.
- ✅ `NEWS_SOURCE_MINI_FETCH_POST_AUDIT_NOAPI` — Mini fetch audit edildi; 10 item geçerli, raw ingestion planına hazır.
- ✅ `NEWS_SOURCE_RAW_INGESTION_PLAN_NOAPI` — 10 sample item için raw ingestion planı hazırlandı; canlı yazım yok.

## Sıradaki Haber Akışı Fazları
- ⏭️ `NEWS_SOURCE_RAW_INGESTION_DRYRUN_NOAPI` | 10 sample haber item için temp/dry-run ingestion kontrolü; canlı DB yazımı yok.
- ⏭️ `NEWS_SOURCE_RAW_INGESTION_APPLY_REAL_AFTER_EXPLICIT_APPROVAL` | Açık onayla sadece kontrollü 10 raw haber itemini news_raw_feed_events içine yaz; fetch enable yok.
- ⏭️ `NEWS_SOURCE_RAW_INGESTION_POST_APPLY_AUDIT_NOAPI` | Raw ingestion canlı yazım sonrası DB, FK, count, safety audit.
- ⏭️ `NEWS_SOURCE_INGESTION_RUNNER_INTEGRATION_PLAN_NOAPI` | Binance+OKX haber fetch/ingestion runner entegrasyonunu planla; timer/fetch enable ayrı onay.
- ⏭️ `NEWS_SOURCE_CONTROLLED_FETCH_ENABLE_PLAN_NOAPI` | Fetch enable/API budget için kontrollü plan; Coinbase hariç Binance+OKX.

## Haber Akışı Sonrası Backlog
- 📌 `INVESTING_SOURCE_FAMILY_PLAN_NOAPI` | Investing.com/TR kaynak ailesini genel source-family olarak planla; RSS/feed izinli yol, HTML scraping yok.
- 📌 `MARKET_SIGNAL_PANEL_SEPARATION_PLAN_NOAPI` | Paneli Haberler, Takvim, Göstergeler, Piyasa İklimi, ICO/Drop Radar, Token Özel Uyarılar olarak ayır.
- 📌 `CALENDAR_IMPACT_ENGINE_PLAN_NOAPI` | Piyasa etkili takvim olaylarını beklenti/olası etki/AI yorumuyla ayrı Calendar bölümüne koy.
- 📌 `MARKET_CALENDAR_HISTORICAL_ANALOGY_PLAN_NOAPI` | Takvim olayları için geçmiş benzer koşul analizi; veri yoksa tarih/sonuç uydurma.
- 📌 `MARKET_CLIMATE_SIGNAL_FRAMEWORK_PLAN_NOAPI` | Fear & Greed, BTC dominance, likidite akışı, ETF flow, DXY/Nasdaq gibi göstergeleri market climate skoruna bağla.
- 📌 `ICO_DROP_INTELLIGENCE_ENGINE_PLAN_NOAPI` | Yeni token/coin haberinde website, ekip, tokenomics, chain, launch, backer, risk ve uygunluk skorlarını çıkar.
- 📌 `TOKEN_COIN_SPECIFIC_ALERT_SYSTEM_PLAN_NOAPI` | Haber/takvim/gösterge takip edilen token/coin ile ilişkiliyse ayrı özel uyarı üret; panelde tekrar yazma.
- 📌 `COINBASE_ENDPOINT_REPAIR_RETRY_PLAN_NOAPI` | Coinbase eksik endpoint için ayrı repair/retry planı; mevcut Binance+OKX akışını bozma.

## Safety
- db_unchanged: `True`
- runner_unchanged: `True`
- fetch_enabled_sum: `0`
- api_budget_sum: `0`
- paper_trade_alone_sum: `0`
- news_raw_feed_events_count: `101`
