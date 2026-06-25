# CORE28 Full Radar Master Roadmap

created_at: 2026-05-12T13:02:12.945261+00:00

## Final hedef
1 Eylül 2026 için Tokenoskobi / Coinoskobi tam radar sistemi.

Bu sistem sadece haber paneli değildir. Haber, cüzdan, token lifecycle, major coin rejimi, market calendar, market climate, ICO/drop intelligence, fusion scoring, paper trade, MEV/execution risk ve AI kalibrasyon katmanlarını birlikte kayıt altına alır.

## Ana kural
- Haber paneli değil; tam radar sistemi.
- Sinyal değil; önce kayıt, test, outcome, kalibrasyon.
- Paper trade var; live trade yok.
- Sınırsız paper para yok.
- Likiditeye göre gerçekçi kapasite var.
- Her gerçek işlemden önce plan → dry-run → apply plan → açık onay → real → post-audit.
- Fetch/API/timer ayrı açık onay olmadan açılmaz.
- Coine özel yama yok.
- Habere özel yama yok.
- Veri varsa veri kadar konuş; veri yoksa veri yok.

## Sistem modülleri
## 1. Haber etki radarı
- Amaç: Haberin token, coin, ağ, piyasa ve risk etkisini ölçmek.
- Fazlar:
  - NEWS28_NEWS_TRUTH_IMPACT_RADAR_PLAN_NOAPI
  - NEWS29_NEWS_RELEVANCE_IMPACT_GATE_DRYRUN_NOAPI
  - NEWS30_NEWS_IMPACT_OUTCOME_TRACKER_PLAN_NOAPI
  - NEWS31_NEWS_PANEL_FILTER_PLAN_NOAPI
- Veri kuralı: Haber varsa sınıflandır; veri yoksa NO_DATA.

## 2. Cüzdan takip sistemi
- Amaç: Bilinen cüzdan, whale, smart money, deployer ve risk adreslerini kayıt altına almak.
- Fazlar:
  - WALLET28_WALLET_REGISTRY_PLAN_NOAPI
  - WALLET29_KNOWN_WALLET_SEED_DRYRUN_NOAPI
  - WALLET30_WALLET_TIER_ENGINE_PLAN_NOAPI
  - WALLET31_WALLET_ACTIVITY_TRACKER_DRYRUN_NOAPI
  - WALLET32_WALLET_IMPACT_SCORE_PLAN_NOAPI
- Veri kuralı: Cüzdan etiketi kanıtlı değilse güvenli sınıfa yükseltme yok.

## 3. Token / pair lifecycle
- Amaç: Yeni pair doğumu, likidite, holder, risk, ölüm ve otopsi akışını genel kuralla izlemek.
- Fazlar:
  - TOKEN28_TOKEN_LIFECYCLE_PLAN_NOAPI
  - TOKEN29_NEW_PAIR_BIRTH_DETECTOR_PLAN_NOAPI
  - TOKEN30_LIQUIDITY_AND_HOLDER_TRACKER_DRYRUN_NOAPI
  - TOKEN31_TOKEN_RISK_ENGINE_PLAN_NOAPI
  - TOKEN32_MORGUE_AUTOPSY_OUTCOME_PLAN_NOAPI
- Veri kuralı: Coine özel yama yok; genel lifecycle kuralı var.

## 4. Major coin / market regime
- Amaç: BTC, ETH, BNB, SOL ve büyük piyasa ortamının küçük token kararlarına etkisini ölçmek.
- Fazlar:
  - COIN28_MAJOR_MARKET_REGIME_PLAN_NOAPI
  - COIN29_BTC_ETH_BNB_SOL_TRACKER_DRYRUN_NOAPI
  - COIN30_MAJOR_NETWORK_NEWS_IMPACT_LINK_NOAPI
  - COIN31_MARKET_RISK_APPETITE_SCORE_PLAN_NOAPI
- Takip edilecekler: BTC, ETH, BNB, SOL, Base/Coinbase ecosystem, ARB, OP, AVAX, TON, SUI, LINK, XRP, DOGE
- Veri kuralı: Major coin rejimi kanıtlanmadan token fırsat skoru şişirilmeyecek.

## 5. Market calendar
- Amaç: FED, CPI, unlock, ETF, regülasyon ve büyük piyasa olaylarını ayrı takvim katmanında tutmak.
- Fazlar:
  - MARKET28_CALENDAR_SOURCE_PLAN_NOAPI
  - MARKET29_CALENDAR_EVENT_SCHEMA_DRYRUN_NOAPI
  - MARKET30_CALENDAR_IMPACT_LINK_PLAN_NOAPI
- Veri kuralı: Haber ile takvim karıştırılmayacak.

## 6. Market climate / endeksler
- Amaç: Fear & Greed, BTC dominance, stablecoin flow, ETF flow, DXY, Nasdaq ve risk iştahı göstergelerini ayrı katmanda izlemek.
- Fazlar:
  - CLIMATE28_MARKET_INDEX_SOURCE_PLAN_NOAPI
  - CLIMATE29_INDEX_SCORE_DRYRUN_NOAPI
  - CLIMATE30_RISK_APPETITE_PANEL_PLAN_NOAPI
- Veri kuralı: Gösterge verisi yoksa tahmin üretme yok.

## 7. ICO / Drop intelligence
- Amaç: Yeni çıkacak token/coin için web, docs, ekip, arz, tokenomics, listing, risk ve piyasa uyumu araştırması yapmak.
- Fazlar:
  - ICO_DROP_INTELLIGENCE_ENGINE_PLAN_NOAPI
  - ICO_DROP_SCORE_AND_ALLOCATION_ENGINE_PLAN_NOAPI
- Çıktılar:
  - token_coin_score_0_100
  - risk_class
  - decision_bucket
  - paper_test_allocation_usdt
  - approx_token_amount
  - why_buy_why_not_summary
- Veri kuralı: Allocation canlı yatırım tavsiyesi değil; paper/test allocation.

## 8. Fusion scoring
- Amaç: Haber, cüzdan, token, coin, market, MEV ve paper sonuçlarını tek karar skorunda birleştirmek.
- Fazlar:
  - FUSION28_FULL_RADAR_SCORE_PLAN_NOAPI
  - FUSION29_SCORE_DRYRUN_NOAPI
  - FUSION30_SCORE_OUTCOME_COMPARISON_NOAPI
  - FUSION31_PANEL_DECISION_GATE_PLAN_NOAPI
- Veri kuralı: Tek sinyalle güçlü fırsat yok; çoklu kanıt gerekli.

## 9. Paper trade simulator
- Amaç: Gerçekçi likidite, slippage, gas, risk ve size kurallarıyla paper/test simülasyonu yapmak.
- Fazlar:
  - PAPER28_PAPER_TRADE_SIMULATOR_PLAN_NOAPI
  - PAPER29_LIQUIDITY_BASED_POSITION_SIZER_DRYRUN_NOAPI
  - PAPER30_ENTRY_TP_SL_ENGINE_PLAN_NOAPI
  - PAPER31_PAPER_TRADE_OUTCOME_TRACKER_PLAN_NOAPI
- Kurallar:
  - Sınırsız paper para yok.
  - Likiditeye göre dinamik size.
  - Risk yüksekse size düşer.
  - Slippage yüksekse size düşer.
  - Gas fee kârı yiyorsa paper reddedilir.
  - Major coinlerde daha büyük paper size olabilir.
  - Düşük likidite tokenlarda küçük paper.
- Veri kuralı: Paper simülasyon gerçek kapasiteye yakın olmalı.

## 10. MEV / execution risk
- Amaç: MEV, sandwich, slippage, gas ve giriş/çıkış maliyetini net PnL hesabına katmak.
- Fazlar:
  - MEV28_MEV_RISK_ENGINE_PLAN_NOAPI
  - MEV29_SANDWICH_RISK_SIM_DRYRUN_NOAPI
  - MEV30_ENTRY_EXIT_MEV_COST_MODEL_NOAPI
  - MEV31_MEV_ADJUSTED_NET_PNL_PLAN_NOAPI
- MEV karar kuralı:
  - 80_plus: paper yok
  - 60_80: çok küçük paper / yüksek risk
  - 40_60: sınırlı size
  - below_40: normal paper simülasyon
- Veri kuralı: MEV riski bilinmiyorsa güvenli varsayım yapılmaz.

## 11. AI eğitim / kalibrasyon
- Amaç: Outcome kayıtlarından false positive azaltma ve skor kalibrasyonu yapmak.
- Fazlar:
  - AI28_TRAINING_DATASET_PLAN_NOAPI
  - AI29_FEATURE_REGISTRY_PLAN_NOAPI
  - AI30_LABEL_AND_OUTCOME_CALIBRATION_NOAPI
  - AI31_BASELINE_MODEL_DRYRUN_NOAPI
  - AI32_FALSE_POSITIVE_REDUCTION_PLAN_NOAPI
  - AI33_FINAL_CALIBRATION_BEFORE_SEPTEMBER_NOAPI
- AI öğrenecek:
  - hangi haber gerçekten etkili
  - hangi cüzdan hareketi değerli
  - hangi yeni token doğum sinyali işe yaradı
  - hangi major coin ortamında küçük token iyi gidiyor
  - hangi risk alarmı doğru çıktı
  - hangi sinyal false positive
  - hangi paper trade size gerçekçi
  - slippage/MEV kârı ne kadar yedi
- Veri kuralı: Model sonuçtan öğrenir; veri yoksa öğrenme yok.

## 12. Tek sade hızlı karar paneli
- Amaç: Kafa karıştırmayan, tekrar etmeyen, hızlı karar ekranı oluşturmak.
- Fazlar:
  - PANEL28_SINGLE_URL_STABILITY_AUDIT_NOAPI
  - PANEL29_RADAR_SECTIONS_PLAN_NOAPI
  - PANEL30_RELEVANT_ONLY_DISPLAY_DRYRUN_NOAPI
  - PANEL31_FINAL_PANEL_APPLY_PLAN_NOAPI
  - PANEL32_FAST_DECISION_RADAR_UI_PLAN_NOAPI
  - PANEL33_ONE_CLICK_PAPER_ACTION_PLAN_NOAPI
  - PANEL34_ONE_CLICK_LIVE_ACTION_RISK_GATE_PLAN_NOAPI
- Panel bölümleri:
  - Kritik Risk
  - Haber Etki Radarı
  - Market Calendar
  - Market Climate / Endeksler
  - Fear & Greed
  - BTC Dominance
  - Likidite / Stablecoin / ETF Flow
  - ICO / Drop Radar
  - Yeni Token İstihbarat Kartı
  - Major Coin Etki Paneli
  - Token / Coin Özel Uyarılar
  - Paper Trade Adayları
  - Paper Trade Sonuçları
  - AI Kalibrasyon Özeti
- Veri kuralı: Raw/debug alanları ana panelde gösterilmez.


## Event / Outcome Registry
- Fazlar:
- EVENT_OUTCOME_REGISTRY_PLAN_NOAPI
- EVENT_OUTCOME_SCHEMA_DRYRUN_NOAPI
- EVENT_OUTCOME_SCHEMA_APPLY_PLAN_NOAPI
- EVENT_OUTCOME_SCHEMA_APPLY_REAL_AFTER_APPROVAL
- EVENT_OUTCOME_POST_AUDIT_NOAPI

- Outcome etiketleri:
- CONFIRMED
- WEAK
- FAILED
- TOO_EARLY
- FALSE_POSITIVE
- RISK_CONFIRMED
- NO_DATA

- Kural: Her sinyal outcome etiketi olmadan AI kalibrasyonuna alınmayacak.

## Tek tuş işlem paneli politikası
- Önce paper/test mode.
- Canlı işlem kapalı.
- Likidite kontrolü zorunlu.
- Slippage kontrolü zorunlu.
- MEV / sandwich risk kontrolü zorunlu.
- Max position size zorunlu.
- Günlük risk limiti zorunlu.
- Token başına limit zorunlu.
- Contract risk kontrolü zorunlu.
- Honeypot / sellability kontrolü zorunlu.
- Son onay ekranı zorunlu.

## Panel butonları
- Paper Alım Simüle Et
- Test Alım Planı Oluştur
- Riskleri Göster
- İzlemeye Al
- Alarm Kur
- Onaylı Canlı Alım en son ve ayrı onaylı aşama

## 1 Eylül takvimi

### 11 Mayıs – 31 Mayıs
- CORE28 roadmap
- Event/outcome registry
- Haber impact plan
- Cüzdan registry plan
- Token lifecycle plan
- Major coin regime plan

### Haziran
- Haber/cüzdan/token/coin kayıtları düzenli toplanacak
- Outcome etiketleri yazılacak
- Paper simulator dry-run başlayacak
- MEV risk dry-run başlayacak

### Temmuz
- Fusion scoring dry-run
- Paper trade outcome tracking
- AI training dataset oluşacak
- İlk model kalibrasyonu
- False positive azaltma

### Ağustos
- Panel sadeleştirme
- AI kalibrasyon final
- Paper trade performans raporu
- MEV-adjusted PnL kontrolü
- Final auditler
- Gereksiz dosya/klasör archive

### 1 Eylül
- Tam sistem teslim raporu
- 90 günlük kayıt özeti
- Haber/cüzdan/token/coin/fusion başarı oranları
- Paper trade net PnL raporu
- AI kalibrasyon raporu
- Risk ve false positive raporu

## Safety
- API calls: 0
- External network calls: 0
- DB mutation: False
- Panel mutation: False
- Runner changed: False
- Timer changed: False
- Fetch enabled: False
- API budget enabled: False
- Paper/live enabled: False
