# 03 ROADMAP - TOKENOSKOBI

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
