# TOKENOSKOBI MASTER ROADMAP

================================================================
CANONICAL_V1_ROADMAP_AUTHORITY_HEADER
================================================================

FINALIZED_AT_UTC=2026-06-17
PROJECT_MODE=CANONICAL_V1_ONLY
SOURCE_OF_TRUTH=PROJECT_MASTER_STATE.md
CURRENT_PHASE=CANONICAL_V1_MASTER_ROADMAP_2_0_ALIGNMENT
NEXT_PHASE=CANONICAL_V1_MASTER_ROADMAP_2_0_FINALIZATION
ROADMAP_STATUS=CANONICAL_V1_ALIGNMENT_FINALIZATION
CANONICAL_INTELLIGENCE_CORE=docs/CANONICAL_V1_INTELLIGENCE_CORE.md

NO_V2=True
NO_NEW_REPO=True
NO_NEW_DB=True

NO_NEW_ROADMAP_BRANCH=True
NO_NEW_ARCHITECTURE=True
NO_NEW_ENGINE=True
NO_RUNTIME_CHANGE=True
NO_DB_WRITE=True
NO_PANEL_WRITE=True
NO_SERVICE_TIMER_CHANGE=True
NO_API_PROVIDER_CALL=True
NO_WALLET_PAPER_LIVE=True

OFFICIAL_BLOCKERS:
- PASSWORD_INPUT_MISSING
- STATE_FILE_STRUCTURE_MISSING

HISTORICAL_TECHNICAL_PENDING:
- PASS11C_ALPHA_WATCHER_AND_ADVERSARIAL_INTELLIGENCE_POST_AUDIT_NOAPI

NOTE:
Existing NEWS_SOURCE_* and intelligence runtime items below are preserved as roadmap backlog/history.
They are not the current source of truth while PROJECT_MASTER_STATE.md points to CANONICAL_V1_MASTER_ROADMAP_2_0_FINALIZATION.

================================================================


- updated_at_utc: `2026-05-12T11:29:20.053352+00:00`
- current_priority: `NEWS_SOURCE_INGESTION_RUNNER_INTEGRATION_PLAN_NOAPI`
- next_phase: `NEWS_SOURCE_INGESTION_RUNNER_INTEGRATION_PLAN_NOAPI`

## Roadmap Items
- `NEWS_SOURCE_MAP_POLICY` | status=`added` | priority=`HIGH` | Haber kaynak sınıfları, güven puanları, panel görünürlüğü ve AI/paper uygunluk kuralları netleşecek.
- `NEWS_FILTER_ENGINE_GENERAL` | status=`planned` | priority=`HIGH` | Her haber için genel geçerli filtre: kaynak, sınıf, güven, token eşleşmesi, major piyasa etkisi, risk durumu.
- `NEWS_SOURCE_EXPANSION_PLAN` | status=`planned` | priority=`HIGH` | Borsa duyuruları, listing/TGE, security, unlock, resmi proje kanalları kaynak planı.
- `PANEL_NEWS_LANES` | status=`planned` | priority=`MEDIUM_HIGH` | Panelde CRITICAL/WATCH/TOKEN_MATCH/RISK/INFO/HIDDEN ayrımı.
- `CLEANUP_UNUSED_FILE_AUDIT` | status=`planned` | priority=`MEDIUM` | Kullanılmayan dosya/klasör adayları sadece raporlanacak; silme yok, arşiv için ayrıca onay gerekir.
- `AI_DATASET_EXPANSION` | status=`planned` | priority=`MEDIUM_HIGH` | Model eğitimi için min 50 row ve label çeşitliliği hedefi.
- `PAPER_TRADE_FUSION` | status=`planned` | priority=`HIGH` | Haber + cüzdan + token + likidite + risk birleşince paper trade planı üretme.
- `CORE_CLEAN2_UNUSED_FILE_ARCHIVE_PLAN_NOAPI` | status=`done` | priority=`MEDIUM` | Cleanup adaylarını arşiv adayı / keep / review olarak ayır; dosya silme veya arşivleme yapma.
- `CORE_CLEAN3_UNUSED_FILE_ARCHIVE_DRYRUN_NOAPI` | status=`planned` | priority=`MEDIUM` | Arşiv adayları için dry-run manifest, hedef path ve rollback planı oluştur; hâlâ dosya taşıma yok.
- `CORE_CLEAN4_UNUSED_FILE_ARCHIVE_APPLY_REAL_AFTER_EXPLICIT_APPROVAL` | status=`planned` | priority=`MEDIUM` | Açık onay sonrası sadece dry-run manifestindeki güvenli adayları arşive taşı; silme yok.
- `CORE_CLEAN5_UNUSED_FILE_ARCHIVE_POST_APPLY_AUDIT_NOAPI` | status=`review` | priority=`MEDIUM` | Arşiv sonrası read-only audit: hedefler var, kaynaklar taşındı, rollback hazır, DB/core değişmedi.
- `CORE_CLEAN5A_ARCHIVE_AUDIT_SINGLE_SOURCE_STILL_EXISTS_REVIEW_NOAPI` | status=`done` | priority=`MEDIUM` | CORE_CLEAN5 fail sebebindeki tek source_still_exists satırını read-only incele; dosya taşıma/silme yok.
- `CORE_CLEAN5B_NONEMPTY_SOURCE_REVIEW_PLAN_NOAPI` | status=`done` | priority=`MEDIUM` | Kalan nonempty source klasörü için diff ve aktif referans kontrolü yap; dosya taşıma/silme yok.
- `CORE_CLEAN5C_ACTIVE_REFERENCE_DECISION_PLAN_NOAPI` | status=`done` | priority=`MEDIUM` | Aktif referanslı kaynak için genel politika kararı: kaynak korunur, canonical referans politikası planlanır.
- `CORE_CLEAN5D_CANONICAL_PANEL_REFERENCE_POLICY_PLAN_NOAPI` | status=`done` | priority=`MEDIUM` | Aktif referanslı legacy panel/workdir için canonical panel/reference policy oluşturuldu; dosya taşıma/silme yok.
- `NEWS_SOURCE_ENGINE_GENERAL_POLICY_IMPLEMENTATION_PLAN_NOAPI` | status=`planned` | priority=`HIGH` | Haber kaynak haritasını genel haber kaynak motoru ve panel filtre politikasına çevirmek; no API/no DB mutation plan ile başlamak.
- `NEWS_SOURCE_REGISTRY_SCHEMA_PLAN_NOAPI` | status=`planned` | priority=`HIGH` | Kaynak registry tabloları için plan çıkar; no API/no DB mutation.
- `NEWS_SOURCE_FILTER_DRYRUN_NOAPI` | status=`planned` | priority=`HIGH` | Mevcut haberleri source class/lane/güven/gürültü filtresinden dry-run geçir.
- `NEWS_PANEL_LANE_MAPPING_DRYRUN_NOAPI` | status=`planned` | priority=`MEDIUM_HIGH` | Panel haber şeritlerini generic kurallarla dry-run üret.
- `NEWS_SOURCE_REGISTRY_SCHEMA_DRYRUN_NOAPI` | status=`planned` | priority=`HIGH` | Schema planı temp DB üzerinde dene; canlı DB yazımı yok.
- `NEWS_SOURCE_REGISTRY_SCHEMA_APPLY_PLAN_NOAPI` | status=`planned` | priority=`HIGH` | Dry-run sonrası canlı DB schema apply planı çıkar; gerçek apply için ayrıca onay iste.
- `NEWS_SOURCE_REGISTRY_SCHEMA_APPLY_REAL_AFTER_EXPLICIT_APPROVAL` | status=`planned` | priority=`HIGH` | Açık onay sonrası sadece 6 source-registry tablosunu canlı DB’ye ekle; seed/API/timer/model/paper yok.
- `NEWS_SOURCE_REGISTRY_SCHEMA_POST_APPLY_AUDIT_NOAPI` | status=`planned` | priority=`HIGH` | Canlı schema apply sonrası read-only audit.
- `NEWS_SOURCE_SEED_PLAN_NOAPI` | status=`planned` | priority=`HIGH` | Kaynak seed planı çıkar; gerçek seed yok, API yok.
- `NEWS_SOURCE_SEED_DRYRUN_NOAPI` | status=`planned` | priority=`HIGH` | Seed planını temp DB üzerinde dene; canlı DB değişmesin.
- `NEWS_SOURCE_SEED_WRITE_PLAN_NOAPI` | status=`planned` | priority=`HIGH` | Seed dry-run sonrası gerçek seed write planı çıkar; onay olmadan yazma.
- `NEWS_SOURCE_SEED_DRYRUN_FAILURE_DIAGNOSE_NOAPI` | status=`done` | priority=`HIGH` | Seed dry-run fail sebebi read-only teşhis edildi; canlı DB değişmedi.
- `NEWS_SOURCE_SEED_PLAN_FIX_NOAPI` | status=`planned` | priority=`HIGH` | Seed planı schema ile uyumlu hale getir; canlı DB’ye yazma.
- `NEWS_SOURCE_SEED_DRYRUN_AFTER_FIX_NOAPI` | status=`planned` | priority=`HIGH` | Düzeltilmiş seed SQL temp DB üzerinde denensin; canlı DB değişmesin.
- `NEWS_SOURCE_SEED_WRITE_REAL_AFTER_EXPLICIT_APPROVAL` | status=`planned` | priority=`HIGH` | Açık onay sonrası 56 source registry seed satırını canlı DB’ye yaz; API/fetch/timer/model/paper yok.
- `NEWS_SOURCE_SEED_WRITE_POST_AUDIT_NOAPI` | status=`planned` | priority=`HIGH` | Canlı source seed yazımı sonrası read-only audit.
- `NEWS_SOURCE_FETCH_POLICY_REVIEW_PLAN_NOAPI` | status=`planned` | priority=`HIGH` | Kaynak fetch politikası, bütçe ve ilk kontrollü fetch planı çıkar; API/fetch açma yok.
- `NEWS_SOURCE_ENDPOINT_CONFIRMATION_PLAN_NOAPI` | status=`planned` | priority=`HIGH` | Placeholder endpointleri gerçek RSS/HTTP kaynaklarıyla eşleştirme planı çıkar; API/fetch yok.
- `NEWS_SOURCE_FETCH_POLICY_ENABLE_DRYRUN_NOAPI` | status=`blocked_until_endpoint_confirmation` | priority=`HIGH` | Endpointler doğrulandıktan sonra yalnızca temp DB’de capped fetch policy enable dry-run.
- `NEWS_SOURCE_ENDPOINT_CONFIRMATION_DRYRUN_NOAPI` | status=`planned` | priority=`HIGH` | Candidate endpoint planını temp/local format dry-run ile kontrol et; dış ağ yok.
- `NEWS_SOURCE_ENDPOINT_CONFIRMATION_SMOKE_REAL_AFTER_EXPLICIT_APPROVAL` | status=`blocked_until_dryrun_and_explicit_approval` | priority=`HIGH` | Ayrı açık onay sonrası çok küçük external HTTP smoke check; fetch ingestion yok.
- `NEWS_SOURCE_ENDPOINT_CONFIRMATION_SMOKE_PLAN_NOAPI` | status=`planned` | priority=`HIGH` | İlk küçük external HTTP smoke test planını çıkar; gerçek ağ çağrısı yok.
- `NEWS_SOURCE_ENDPOINT_CONFIRMATION_SMOKE_POST_AUDIT_NOAPI` | status=`planned` | priority=`HIGH` | Smoke sonuçlarını ve güvenlik kilitlerini read-only audit et.
- `NEWS_SOURCE_ENDPOINT_CANDIDATE_REPAIR_PLAN_NOAPI` | status=`planned` | priority=`HIGH` | Doğrulanmayan endpointler için daha doğru resmi/RSS adayları planla; API/fetch/DB write yok.
- `NEWS_SOURCE_RAW_INGESTION_DRYRUN_NOAPI` | status=`next` | priority=`P0` | 10 sample haber item için temp/dry-run ingestion kontrolü; canlı DB yazımı yok.
- `NEWS_SOURCE_RAW_INGESTION_APPLY_REAL_AFTER_EXPLICIT_APPROVAL` | status=`requires_explicit_approval_after_dryrun` | priority=`P0` | Açık onayla sadece kontrollü 10 raw haber itemini news_raw_feed_events içine yaz; fetch enable yok.
- `NEWS_SOURCE_RAW_INGESTION_POST_APPLY_AUDIT_NOAPI` | status=`planned` | priority=`P0` | Raw ingestion canlı yazım sonrası DB, FK, count, safety audit.
- `NEWS_SOURCE_INGESTION_RUNNER_INTEGRATION_PLAN_NOAPI` | status=`planned` | priority=`P0` | Binance+OKX haber fetch/ingestion runner entegrasyonunu planla; timer/fetch enable ayrı onay.
- `NEWS_SOURCE_CONTROLLED_FETCH_ENABLE_PLAN_NOAPI` | status=`planned` | priority=`P0` | Fetch enable/API budget için kontrollü plan; Coinbase hariç Binance+OKX.
- `INVESTING_SOURCE_FAMILY_PLAN_NOAPI` | status=`backlog_after_news_flow` | priority=`P1` | Investing.com/TR kaynak ailesini genel source-family olarak planla; RSS/feed izinli yol, HTML scraping yok.
- `MARKET_SIGNAL_PANEL_SEPARATION_PLAN_NOAPI` | status=`backlog_after_news_flow` | priority=`P1` | Paneli Haberler, Takvim, Göstergeler, Piyasa İklimi, ICO/Drop Radar, Token Özel Uyarılar olarak ayır.
- `CALENDAR_IMPACT_ENGINE_PLAN_NOAPI` | status=`backlog_after_news_flow` | priority=`P1` | Piyasa etkili takvim olaylarını beklenti/olası etki/AI yorumuyla ayrı Calendar bölümüne koy.
- `MARKET_CALENDAR_HISTORICAL_ANALOGY_PLAN_NOAPI` | status=`backlog_after_news_flow` | priority=`P1` | Takvim olayları için geçmiş benzer koşul analizi; veri yoksa tarih/sonuç uydurma.
- `MARKET_CLIMATE_SIGNAL_FRAMEWORK_PLAN_NOAPI` | status=`backlog_after_news_flow` | priority=`P1` | Fear & Greed, BTC dominance, likidite akışı, ETF flow, DXY/Nasdaq gibi göstergeleri market climate skoruna bağla.
- `ICO_DROP_INTELLIGENCE_ENGINE_PLAN_NOAPI` | status=`backlog_after_news_flow` | priority=`P1` | Yeni token/coin haberinde website, ekip, tokenomics, chain, launch, backer, risk ve uygunluk skorlarını çıkar.
- `TOKEN_COIN_SPECIFIC_ALERT_SYSTEM_PLAN_NOAPI` | status=`backlog_after_news_flow` | priority=`P1` | Haber/takvim/gösterge takip edilen token/coin ile ilişkiliyse ayrı özel uyarı üret; panelde tekrar yazma.
- `COINBASE_ENDPOINT_REPAIR_RETRY_PLAN_NOAPI` | status=`backlog_parallel_low_risk` | priority=`P2` | Coinbase eksik endpoint için ayrı repair/retry planı; mevcut Binance+OKX akışını bozma.

- `PRIORITY_ENGINE_PLAN_NOAPI` | status=`P0`
- `INTELLIGENCE_ORCHESTRATOR_PLAN_NOAPI` | status=`P0`
- `HUNTER_TRIGGER_CONTRACT_PLAN_NOAPI` | status=`P0`
- `NEWS_HUNTER_PLAN_NOAPI` | status=`P1`
- `PROSECUTOR_PLAN_NOAPI` | status=`P1`
- `OPPORTUNITY_MEMORY_PLAN_NOAPI` | status=`P1`
- `UNKNOWN_ANOMALY_ENGINE_PLAN_NOAPI` | status=`P1`

- `NEWS_HUNTER_RUNTIME_GAP_AUDIT_NOAPI` | status=`done` | priority=`P0` | Raw news mevcut, matcher mevcut, runtime producer yok. Match/score/impact zinciri çalışmıyor.
- `NEWS_HUNTER_RUNTIME_PLAN_NOAPI` | status=`next` | priority=`P0` | news_raw_feed_events → news_token_match_events producer zincirini tasarla.

- `NEWS_HUNTER_RUNTIME_PLAN_NOAPI` | status=`done` | priority=`P0` | Raw news → token match producer tasarlandı.
- `PRIORITY_ENGINE_RUNTIME_PLAN_NOAPI` | status=`next` | priority=`P0` | Token match → score producer tasarla.

- `PRIORITY_ENGINE_RUNTIME_PLAN_NOAPI` | status=`done` | priority=`P0` | Token match → score producer tasarlandı.
- `PROSECUTOR_RUNTIME_PLAN_NOAPI` | status=`next` | priority=`P0` | Score → impact producer tasarla.


- `PROSECUTOR_RUNTIME_PLAN_NOAPI` | status=`done` | priority=`P0` | Score → impact producer tasarlandı.
- `PHASE41_LIVE_FEED_BINDING_PLAN_NOAPI` | status=`next` | priority=`P0` | Impact → Phase41 canlı feed bağını tasarla.


- `PHASE41_LIVE_FEED_BINDING_PLAN_NOAPI` | status=`done` | priority=`P0` | Impact → Phase41 feed bağlandı.
- `INTELLIGENCE_RUNTIME_MASTER_PLAN_NOAPI` | status=`next` | priority=`P0` | Hunter → Priority → Prosecutor → Phase41 zincirini tek runtime altında birleştir.


- `INTELLIGENCE_RUNTIME_MASTER_PLAN_NOAPI` | status=`done` | priority=`P0` | Hunter → Priority → Prosecutor → Phase41 zinciri tanımlandı.
- `INTELLIGENCE_RUNTIME_GAP_ANALYSIS_NOAPI` | status=`next` | priority=`P0` | Tanımlanan zincirde eksik producer/runtime bileşenlerini çıkar.


- `INTELLIGENCE_RUNTIME_GAP_ANALYSIS_NOAPI` | status=`done` | priority=`P0` | Runtime producer eksikleri grep ve table audit ile doğrulandı.
- `INTELLIGENCE_RUNTIME_APPLY_PLAN_NOAPI` | status=`next` | priority=`P0` | Hunter/Priority/Prosecutor/Phase41 runtime implementasyon planı.


- `CANONICAL_MATCH_LAYER_GAP_AUDIT_NOAPI` | status=`done` | priority=`P0` | Canonical match katmanı eksik, runtime producer yok.
- `CANONICAL_MATCH_SCHEMA_PLAN_NOAPI` | status=`next` | priority=`P0` | Canonical news_token_match_events kontratını tanımla.


- `INTELLIGENCE_RUNTIME_APPLY_PLAN_NOAPI` | status=`done` | priority=`P0` | Runtime producer inşa sırası tanımlandı.
- `HUNTER_RUNTIME_PRODUCER_PLAN_NOAPI` | status=`next` | priority=`P0` | İlk gerçek producer tasarımı.


- `HUNTER_RUNTIME_PRODUCER_PLAN_NOAPI` | status=`done` | priority=`P0` | Raw news → canonical match producer tanımlandı.
- `PRIORITY_RUNTIME_PRODUCER_PLAN_NOAPI` | status=`next` | priority=`P0` | Match → score producer tanımla.


- `PRIORITY_RUNTIME_PRODUCER_PLAN_NOAPI` | status=`done` | priority=`P0` | Match → score producer tanımlandı.
- `PROSECUTOR_RUNTIME_PRODUCER_PLAN_NOAPI` | status=`next` | priority=`P0` | Score → impact producer tanımla.


- `PROSECUTOR_RUNTIME_PRODUCER_PLAN_NOAPI` | status=`done` | priority=`P0` | Score → impact producer tanımlandı.
- `PHASE41_BINDING_RUNTIME_PLAN_NOAPI` | status=`next` | priority=`P0` | Impact → Phase41 binding runtime tanımla.


- `PHASE41_BINDING_RUNTIME_PLAN_NOAPI` | status=`done` | priority=`P0` | Impact → Phase41 binding tanımlandı.
- `INTELLIGENCE_PIPELINE_CLOSURE_AUDIT_NOAPI` | status=`next` | priority=`P0` | Tanımlanan tüm producer ve binding katmanlarını doğrula.


- `INTELLIGENCE_PIPELINE_CLOSURE_AUDIT_NOAPI` | status=`done` | priority=`P0` | Pipeline planları ve kontratlar doğrulandı.
- `RUNTIME_IMPLEMENTATION_BACKLOG_PLAN_NOAPI` | status=`next` | priority=`P0` | Gerçek runtime implementasyon backlog'u oluştur.


- `RUNTIME_IMPLEMENTATION_BACKLOG_PLAN_NOAPI` | status=`done` | priority=`P0` | Runtime eksikleri backlog olarak tanımlandı.
- `HUNTER_RUNTIME_IMPLEMENTATION_PLAN_NOAPI` | status=`next` | priority=`P0` | İlk gerçek runtime implementasyon tasarımı.


- `HUNTER_RUNTIME_IMPLEMENTATION_PLAN_NOAPI` | status=`done` | priority=`P0` | İlk executable runtime tasarlandı.
- `HUNTER_RUNTIME_SCHEMA_AUDIT_NOAPI` | status=`next` | priority=`P0` | Hunter implementasyonu öncesi tablo/alan doğrulaması.


- `HUNTER_RUNTIME_SCHEMA_AUDIT_NOAPI` | status=`done` | priority=`P0` | tokens/pairs mevcut, canonical output table yok.
- `CANONICAL_MATCH_TABLE_SCHEMA_PLAN_NOAPI` | status=`next` | priority=`P0` | news_token_match_events fiziksel tablo kontratını tanımla.

