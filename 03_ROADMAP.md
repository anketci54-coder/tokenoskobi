# 03 ROADMAP - TOKENOSKOBI

<!-- PRODUCT_SLICE_01_TRUTH:BEGIN -->
## Product Slice 01 Live Truth

- Status: `VERIFIED_WITH_BLOCKERS`
- NEWS raw/fresh: `416` / `False`
- Panel local/HTTPS/auth: `True` / `True` / `False`
- Alchemy HTTP/WS: `False` / `False`
- Public RPC: `4/4`
- Hybrid: `False`
- Critical/high/medium: `1/5/4`
- Artifact: `data/control/product_slice_01_live_truth_verification_v1.json`
- Next: `PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET`
<!-- PRODUCT_SLICE_01_TRUTH:END -->


<!-- DYNAMIC_POSITION_SIZING_ROADMAP:BEGIN -->
## Dinamik İşlem Büyüklüğü Düzeltmesi

`LIVE_CANARY_TRADE_USD=1_TO_2` kalıcı sistem sınırı değildir ve bu anlamıyla yürürlükten kaldırılmıştır.

```text
POSITION_SIZE
  = human policy envelope içinde
    kullanılabilir canary wallet bakiyesi
    + fırsat kalitesi ve confidence
    + Risk Engine kararı
    + likidite / price impact / slippage
    + gas, fee, tax ve toplam maliyet oranı
    + açık risk / günlük kalan risk bütçesi / drawdown
    + ölçülmüş kapanmış işlem ve öğrenme kanıtı
```

- 1–2 USD yalnız isteğe bağlı ilk canary probe olabilir.
- Sistem fırsat ve cüzdan koşullarına göre daha düşük veya daha yüksek pozisyon önerebilir.
- Nihai üst sınırlar kullanıcı tarafından belirlenen işlem başı maksimum, günlük zarar ve toplam açık risk zarfıdır.
- Risk Engine veto aşılamaz.
- Bu düzeltme şu anda live authority açmaz; mevcut ürün tamamlama ve 1 Eylül hedef sırası değişmez.
<!-- DYNAMIC_POSITION_SIZING_ROADMAP:END -->

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE=TOKENOSKOBI_USABLE_PRODUCT_VERTICAL_SLICE
CURRENT_STATUS=PRODUCT_COMPLETION_DEADLINE_LOCKED_2026_09_01
PRODUCT_COMPLETION_DEADLINE=2026-09-01
NO_NEW_ERA=true
SCOPE_FREEZE=true
ERA64K_STATUS=DEFERRED_NOT_NEXT_STEP
NEXT_SAFE_STEP=PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION

## Kesin teslim hedefi

Tokenoskobi kullanılabilir ürün döngüsü, paper-trade testleri ve ilk bounded gerçek para canary başlangıcı **1 Eylül 2026** hedefiyle kilitlenmiştir. Tarihi kaçırmamak için önce kapsam daraltılır; yeni ERA, alt ERA, mimari gösteri, belge zinciri veya ürünü doğrudan bloke etmeyen engine derinleştirmesi açılmaz.

## Sıkıştırılmış takvim

| Tarih | Tek teslimat |
|---|---|
| 25-27 Temmuz | NEWS, panel URL/auth, Alchemy hibrit bağlantısı, onchain gecikmesi ve iç/dış güvenliğin read-only gerçeklik doğrulaması |
| 28 Temmuz-5 Ağustos | Canlı tek token giriş ekranı, gerçek karar paketi, online timeframe ve kanıtlar |
| 6-10 Ağustos | İnsan onayı, karar geçmişi ve sonuç takibi |
| 11-17 Ağustos | DEX swap yönü, tam maliyet, başarılı wallet, CEX balina ve Obsidian grafiği |
| 18-22 Ağustos | Harekât Subayı chatbotu, AI konseyi, self-healing önerisi ve operasyonel istihbarat |
| 23-29 Ağustos | En az 7 günlük sınırlı paper-trade koşusu ve hata/restart testleri |
| 30-31 Ağustos | Son signer/wallet izolasyonu, kill switch, recovery ve go/no-go |
| 1 Eylül | BSC/PancakeSwap üzerinde işlem başına 1-2 USD gerçek para canary başlangıcı |

## İlk canlı canary sınırı

- BSC ve PancakeSwap V2/V3.
- İşlem başına 1-2 USD.
- Başlangıçta her işlem insan onaylı.
- İzole canary wallet, tek açık pozisyon ve exact-amount approval.
- Unlimited approval ve otomatik sermaye artırımı yok.
- Risk Engine veto ve kill switch zorunlu.
- Live trade bugün açılmaz; 31 Ağustos go/no-go ve açık kullanıcı aktivasyonu sonrası hedef 1 Eylül'dür.

## Öğrenme şartı

Kaybedilen para ancak pre-trade veri snapshotı, karar, insan onayı, quote, receipt, gerçek gas/fee/slippage/tax, exit/outcome ve hata sınıfı kaydedilip replay edilebiliyorsa tecrübeye dönüşür. Sistem bu veriden değişiklik önerir; production kodunu veya trade yetkisini kendiliğinden değiştirmez. Değişiklik replay, regression/red-team ve insan onayından sonra uygulanır.
