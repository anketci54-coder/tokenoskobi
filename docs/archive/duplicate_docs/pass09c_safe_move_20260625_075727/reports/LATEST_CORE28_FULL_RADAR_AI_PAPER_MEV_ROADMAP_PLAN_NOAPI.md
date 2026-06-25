# Tokenoskobi / Coinoskobi — Full Radar Roadmap v3

phase: CORE28_FULL_RADAR_AI_PAPER_MEV_ROADMAP_PLAN_NOAPI
created_at: 20260513_104540
status: PLAN_ONLY_NOAPI

## Güvenlik Kuralı

- DB yazımı yok.
- API yok.
- Panel apply yok.
- Timer değişimi yok.
- Runner değişimi yok.
- Patch/yama yok.
- Paper/live yok.
- Sadece resmi plan/checklist dosyası yazıldı.

## Ana Vizyon

Tokenoskobi / Coinoskobi artık haber paneli değildir.

Ana panel beyin olacak.
Alt paneller organlar olacak.
Fusion motoru sinir sistemi olacak.
Outcome registry hafıza olacak.
AI kalibrasyon öğrenme olacak.
Paper trade simülasyon olacak.
Morg / Otopsi hatalardan öğrenme olacak.

## Ana Misyon

1. Geleceğin büyük yıldızlarını erken bulmak.
2. İlk doğumdan gençlik dönemine kadar para kazandırabilecek küçük yıldızları yakalamak.
3. Rug / fake / ölü doğan / noise tokenları ayıklamak.
4. Live trade açmadan paper trade ile test etmek.
5. Outcome kayıtlarıyla sistemi kalibre etmek.
6. Kaybedenlerden de öğrenmek.

## Mevcut Stabil Temel

- RUNTIME76 success audit PASS.
- Service Result=success.
- ExecMainStatus=0.
- Timer inactive/enabled, değiştirilmedi.
- DB integrity/quick/FK temiz.
- Lock yok.
- Runner process yok.
- Panel 8096/8097 LISTEN.
- Paper/live runtime 0.
- Sistem STABLE_MONITOR_ONLY.

## Fazlar

### FAZ 0A — GitHub / DevOps / Güvenli Versiyon Kontrolü

- [ ] DEVOPS28_GITHUB_PRIVATE_REPO_PLAN_NOAPI
- [ ] DEVOPS29_REPO_STRUCTURE_AND_GITIGNORE_PLAN_NOAPI
- [ ] DEVOPS30_ISSUE_PROJECT_BOARD_PLAN_NOAPI
- [ ] DEVOPS31_SAFE_DEPLOY_BRANCH_POLICY_NOAPI

Amaç:
- Private repo.
- main / dev / lab branch düzeni.
- Issue/project board.
- Secret/key sızıntı koruması.
- Güvenli deploy politikası.

Yasak:
- API key yok.
- Telegram token yok.
- .env yok.
- Private DB yok.
- Wallet private key yok.
- Server şifresi yok.

### FAZ 0B — Multi-source Truth Engine

- [ ] SOURCE28_MULTI_SOURCE_TRUTH_ENGINE_PLAN_NOAPI
- [ ] SOURCE29_MARKET_SOURCE_STACK_PLAN_NOAPI
- [ ] SOURCE30_WALLET_IDENTITY_SOURCE_STACK_PLAN_NOAPI
- [ ] SOURCE31_MACRO_CALENDAR_SOURCE_STACK_PLAN_NOAPI
- [ ] SOURCE32_ONCHAIN_LIQUIDITY_SOURCE_STACK_PLAN_NOAPI
- [ ] SOURCE33_MEV_SIMULATION_SOURCE_STACK_PLAN_NOAPI

Kaynak kuralı:
- Tek kaynak = bilgi.
- 2 kaynak aynı = güven artar.
- 3 kaynak aynı = panelde gösterilebilir.
- Kaynak çelişirse = conflict / no-entry.
- Stale data kullanılmaz.
- Her kaynak reliability score alır.

### FAZ 1 — CORE28 Ana Omurga

- [x] CORE28_FULL_RADAR_AI_PAPER_MEV_ROADMAP_PLAN_NOAPI

Bu faz resmi roadmap/checklist dosyasını oluşturdu.

### FAZ 2 — Panel Blueprint ve Data Contract

- [ ] PANEL28_FULL_RADAR_UI_BLUEPRINT_NOAPI
- [ ] PANEL29_STATIC_FULL_RADAR_SHELL_NOAPI
- [ ] DATA28_PANEL_DATA_CONTRACT_PLAN_NOAPI
- [ ] DATA29_PANEL_JSON_ENDPOINT_PLAN_NOAPI

Alt paneller:
- Ana Panel
- Ekonomik Takvim
- Haber Etki
- Balina / Cüzdan
- Token Lifecycle
- Morg / Otopsi
- Major Coin Rejimi
- ICO / Drop / TGE
- Paper Simülasyon
- Risk / Güvenlik / MEV
- AI Kalibrasyon

### FAZ 3 — Event / Outcome Registry

- [ ] EVENT28_OUTCOME_REGISTRY_PLAN_NOAPI
- [ ] EVENT29_OUTCOME_SCHEMA_DRYRUN_NOAPI
- [ ] EVENT30_OUTCOME_SCHEMA_APPLY_PLAN_NOAPI
- [ ] EVENT31_OUTCOME_SCHEMA_APPLY_REAL_AFTER_APPROVAL
- [ ] EVENT32_OUTCOME_POST_AUDIT_NOAPI

Kayıt edilecek olaylar:
- Haber geldi.
- Ekonomi takvimi olayı gerçekleşti.
- Whale hareketi oldu.
- Cüzdan takip edilen tokene yöneldi.
- Yeni pair doğdu.
- İlk likidite geldi.
- Holder arttı.
- Stablecoin / likidite akışı değişti.
- Risk alarmı çıktı.
- MEV riski yükseldi.
- Paper trade planı üretildi.
- Paper trade açıldı.
- TP1 / TP2 / TP3 / SL sonucu oluştu.
- Net PnL hesaplandı.
- Morg/Otopsi sonucu oluştu.

Outcome etiketleri:
- CONFIRMED
- WEAK
- FAILED
- TOO_EARLY
- FALSE_POSITIVE
- RISK_CONFIRMED
- NO_DATA
- PROFITABLE
- LOSS
- NEUTRAL
- MISSED_OPPORTUNITY
- DEAD_BORN
- RUG_CONFIRMED
- REVIVAL

### FAZ 4 — Haber Etki Radarı

- [ ] NEWS28_NEWS_TRUTH_IMPACT_RADAR_PLAN_NOAPI
- [ ] NEWS29_NEWS_RELEVANCE_IMPACT_GATE_DRYRUN_NOAPI
- [ ] NEWS30_NEWS_IMPACT_OUTCOME_TRACKER_PLAN_NOAPI
- [ ] NEWS31_NEWS_PANEL_FILTER_PLAN_NOAPI
- [ ] NEWS32_TURKISH_MEANING_LAYER_PLAN_NOAPI

Haber tek başına işlem/paper izni vermez.

### FAZ 5 — Ekonomi Takvimi / Makro Radar

- [ ] ECON28_MACRO_CALENDAR_PLAN_NOAPI
- [ ] ECON29_CPI_FOMC_NFP_EVENT_REGISTRY_PLAN_NOAPI
- [ ] ECON30_MACRO_EVENT_IMPACT_SCORE_DRYRUN_NOAPI
- [ ] ECON31_MACRO_CALENDAR_PANEL_PLAN_NOAPI
- [ ] ECON32_MACRO_EVENT_OUTCOME_TRACKER_NOAPI

Takip:
- CPI
- PPI
- FOMC
- FOMC tutanakları
- Fed konuşmaları
- NFP / işsizlik
- PMI
- GDP
- DXY
- ABD 10Y
- S&P 500 / Nasdaq
- ETF flow

### FAZ 6 — Likidite / On-chain Flow / Anomaly

- [ ] FLOW28_LIQUIDITY_FLOW_RADAR_PLAN_NOAPI
- [ ] FLOW29_EXCHANGE_INFLOW_OUTFLOW_DRYRUN_NOAPI
- [ ] FLOW30_STABLECOIN_RESERVE_AND_SSR_PLAN_NOAPI
- [ ] FLOW31_SECTOR_ROTATION_SCORE_PLAN_NOAPI
- [ ] FLOW32_RISK_ON_RISK_OFF_PANEL_PLAN_NOAPI
- [ ] ANOMALY28_ONCHAIN_SEISMIC_MOVEMENT_PLAN_NOAPI

Kural:
- Exchange inflow = satış baskısı.
- Exchange outflow = accumulation / arz şoku.
- Stablecoin reserve artışı = alım gücü.
- Stablecoin reserve düşüşü = buy-wall zayıflığı.
- Sismik hareket = red-alert.

### FAZ 7 — Wallet / Balina / Smart Money Radar

- [ ] WALLET28_WALLET_REGISTRY_PLAN_NOAPI
- [ ] WALLET29_KNOWN_WALLET_SEED_DRYRUN_NOAPI
- [ ] WALLET30_WALLET_TIER_ENGINE_PLAN_NOAPI
- [ ] WHALE28_WHALE_MOVEMENT_RADAR_PLAN_NOAPI
- [ ] WHALE29_SMART_MONEY_CLUSTER_PLAN_NOAPI
- [ ] WHALE30_CEX_INFLOW_OUTFLOW_PLAN_NOAPI
- [ ] WHALE31_LP_DEPLOYER_INSIDER_RISK_PLAN_NOAPI
- [ ] WHALE32_WALLET_IMPACT_SCORE_PLAN_NOAPI
- [ ] WHALE33_WALLET_OUTCOME_TRACKER_PLAN_NOAPI

Cüzdan türleri:
- Smart wallet
- Whale
- Mega whale
- Deployer
- Insider
- LP wallet
- Market maker
- CEX wallet
- Bridge wallet
- Scam/rug geçmişi olan wallet
- Burn/dead wallet
- Fresh wallet cluster

### FAZ 8 — Token Lifecycle / Yıldız Avı

- [ ] TOKEN28_TOKEN_LIFECYCLE_PLAN_NOAPI
- [ ] TOKEN29_NEW_PAIR_BIRTH_DETECTOR_PLAN_NOAPI
- [ ] TOKEN30_FIRST_LIQUIDITY_AND_HOLDER_TRACKER_DRYRUN_NOAPI
- [ ] TOKEN31_TOKEN_RISK_ENGINE_PLAN_NOAPI
- [ ] STAR28_FUTURE_STAR_DETECTION_PLAN_NOAPI
- [ ] STAR29_SMALL_YOUNG_STAR_PAPER_CANDIDATE_PLAN_NOAPI

Yaşam döngüsü:
- Birth
- First pair
- First liquidity
- First trusted price
- Early TX flow
- Holder growth
- Volume expansion
- Liquidity strengthen
- Momentum
- Decay
- Rug / death / morgue

Yıldız sınıfları:
- Yeni doğan
- Genç yıldız
- Küçük yıldız paper adayı
- Geleceğin büyük yıldızı
- Riskli ama izlenir
- Noise
- Dead-born
- Morgue / otopsi

### FAZ 8B — Morg / Otopsi

- [ ] MORGUE28_DEAD_TOKEN_REGISTRY_PLAN_NOAPI
- [ ] MORGUE29_RUG_FAKE_NOISE_CLASSIFIER_PLAN_NOAPI
- [ ] MORGUE30_AUTOPSY_REASON_ENGINE_PLAN_NOAPI
- [ ] MORGUE31_AUTOPSY_TO_AI_FEEDBACK_PLAN_NOAPI
- [ ] MORGUE32_REVIVAL_WATCH_PLAN_NOAPI

AI sadece kazananlardan değil, ölenlerden de öğrenecek.

### FAZ 9 — Major Coin / Market Rejimi

- [ ] COIN28_MAJOR_MARKET_REGIME_PLAN_NOAPI
- [ ] COIN29_BTC_ETH_BNB_SOL_TRACKER_DRYRUN_NOAPI
- [ ] COIN30_MAJOR_NETWORK_NEWS_IMPACT_LINK_NOAPI
- [ ] COIN31_MARKET_RISK_APPETITE_SCORE_PLAN_NOAPI

Çıktı:
- Risk-on / risk-off
- BTC baskısı
- ETH/L2 gücü
- BNB ortamı
- SOL rejimi
- Altcoin uygunluğu
- Küçük token paper size etkisi

### FAZ 10 — ICO / Drop / TGE / Pre-birth Intelligence

- [ ] ICO28_ICO_DROP_TGE_RADAR_PLAN_NOAPI
- [ ] ICO29_LAUNCH_LISTING_CALENDAR_PLAN_NOAPI
- [ ] ICO30_PRE_BIRTH_INTELLIGENCE_DRYRUN_NOAPI
- [ ] ICO31_DROP_AIRDROP_TRACKER_PLAN_NOAPI
- [ ] ICO32_LAUNCH_RISK_SCORE_PLAN_NOAPI

### FAZ 11 — Risk / Güvenlik / MEV

- [ ] RISK28_SECURITY_RISK_ENGINE_PLAN_NOAPI
- [ ] MEV28_MEV_RISK_ENGINE_PLAN_NOAPI
- [ ] MEV29_SANDWICH_RISK_SIM_DRYRUN_NOAPI
- [ ] MEV30_ENTRY_EXIT_MEV_COST_MODEL_NOAPI
- [ ] MEV31_MEV_ADJUSTED_NET_PNL_PLAN_NOAPI

MEV karar kuralı:
- MEV risk 80+ → paper yok.
- MEV risk 60-80 → çok küçük paper.
- MEV risk 40-60 → sınırlı size.
- MEV risk <40 → normal paper simülasyon.

### FAZ 12 — Paper Trade Simulator

- [ ] PAPER28_PAPER_TRADE_SIMULATOR_PLAN_NOAPI
- [ ] PAPER29_LIQUIDITY_BASED_POSITION_SIZER_DRYRUN_NOAPI
- [ ] PAPER30_ENTRY_TP_SL_ENGINE_PLAN_NOAPI
- [ ] PAPER31_PAPER_TRADE_OUTCOME_TRACKER_PLAN_NOAPI
- [ ] PAPER32_MEV_ADJUSTED_PAPER_PNL_NOAPI

Aktif işlem alanları:
- Varlık
- Entry
- SL
- TP1
- TP2
- TP3
- Anlık fiyat
- PnL %
- Süre
- Max profit
- Max drawdown
- Slippage
- Gas
- MEV cost
- Net PnL

### FAZ 13 — Fusion Scoring Motoru

- [ ] FUSION28_FULL_RADAR_SCORE_PLAN_NOAPI
- [ ] FUSION29_SCORE_DRYRUN_NOAPI
- [ ] FUSION30_SCORE_OUTCOME_COMPARISON_NOAPI
- [ ] FUSION31_PANEL_DECISION_GATE_PLAN_NOAPI

Fusion kararları:
- Gizle
- İzle
- Kritik Risk
- Yeni Fırsat Radar
- Küçük Yıldız Adayı
- Geleceğin Yıldızı
- Paper Trade Adayı
- Paper Trade Reddedildi
- Morgue Candidate
- Autopsy Required
- Revival Watch

### FAZ 14 — AI Eğitim / Kalibrasyon

- [ ] AI28_TRAINING_DATASET_PLAN_NOAPI
- [ ] AI29_FEATURE_REGISTRY_PLAN_NOAPI
- [ ] AI30_LABEL_AND_OUTCOME_CALIBRATION_NOAPI
- [ ] AI31_BASELINE_MODEL_DRYRUN_NOAPI
- [ ] AI32_FALSE_POSITIVE_REDUCTION_PLAN_NOAPI
- [ ] AI33_FINAL_CALIBRATION_BEFORE_SEPTEMBER_NOAPI

AI öğrenecek:
- Hangi haber gerçekten etkili?
- Hangi ekonomi olayı piyasayı oynattı?
- Hangi cüzdan hareketi değerli?
- Hangi yeni token doğum sinyali işe yaradı?
- Hangi morg pattern’i tekrar etti?
- Hangi risk alarmı doğru çıktı?
- Hangi sinyal false positive?
- Hangi paper trade size gerçekçi?
- MEV/slippage kârı ne kadar yedi?

## 1 Eylül Hedefi

Mayıs:
- GitHub/devops plan
- Source truth engine plan
- CORE28 roadmap
- Panel blueprint
- Data contract
- Event/outcome registry plan
- Haber impact plan
- Ekonomi takvimi plan
- Wallet/balina plan
- Token lifecycle plan
- Morg/Otopsi plan

Haziran:
- Static full radar shell
- Panel data contract
- Haber / makro / wallet / token veri boruları
- Ekonomi takvimi ilk veri akışı
- Wallet/balina temel takip
- Token lifecycle temel takip
- Outcome kayıtları başlangıcı
- Paper simulator dry-run
- MEV risk dry-run

Temmuz:
- Fusion scoring dry-run
- Paper trade outcome tracking
- Yeni yıldız / küçük yıldız sınıflaması
- Morg/Otopsi kayıtları
- AI training dataset oluşumu
- İlk model kalibrasyonu
- False positive azaltma

Ağustos:
- Panel sadeleştirme
- Fusion karar gate final
- AI kalibrasyon final
- Paper trade performans raporu
- MEV-adjusted PnL kontrolü
- Morg/Otopsi öğrenme raporu
- Risk / false positive raporu
- Final auditler

1 Eylül:
- Tam sistem teslim raporu
- 90 günlük kayıt özeti
- Haber / ekonomi / wallet / token / coin / fusion başarı oranları
- Paper trade net PnL raporu
- AI kalibrasyon raporu
- Risk ve false positive raporu
- Morg/Otopsi raporu
- Geleceğin yıldızları / küçük yıldızlar performans analizi
