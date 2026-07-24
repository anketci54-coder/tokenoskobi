# 07 PROJECT HANDOFF

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE=TOKENOSKOBI_USABLE_PRODUCT_VERTICAL_SLICE
STATUS=PRODUCT_COMPLETION_DEADLINE_LOCKED_2026_09_01
PRODUCT_COMPLETION_DEADLINE=2026-09-01
NO_NEW_ERA=true
SCOPE_FREEZE=true
NEXT_SAFE_STEP=PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION

## Kesin yön

1 Eylül 2026 tarihinde kullanılabilir ürün, tamamlanmış paper-trade test hattı ve BSC/PancakeSwap üzerinde işlem başına 1-2 USD bounded gerçek para canary başlangıcı hedeflenmiştir. Yeni ERA, alt ERA veya ürün dışı engine derinleştirmesi yoktur.

## İlk canlı canary

- BSC ve PancakeSwap V2/V3.
- İşlem başına 1-2 USD.
- Başlangıçta her işlem insan onaylı.
- İzole wallet, tek açık pozisyon, exact approval, unlimited approval yasağı.
- Live trade şu anda kapalıdır; 30-31 Ağustos go/no-go ve açık kullanıcı aktivasyonu gerekir.

## Öğrenme gerçeği

Öğrenme sistemi bugün uçtan uca doğrulanmış değildir. Zorunlu akış: pre-trade snapshot -> karar -> onay -> execution/receipt -> gerçek maliyetler -> exit/outcome -> hata sınıfı -> lesson candidate -> replay/test/red-team -> insan onayı -> kontrollü güncelleme. Bu akış kurulmadan kayıp yalnız giderdir; kurulduğunda ölçülebilir tecrübeye dönüşür.

## Yeni pencerenin tek işi

README boot protocolünü eksiksiz uygula ve yalnız `PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION` adımını yürüt. NEWS, panel URL/auth, Alchemy hibrit bağlantısı, onchain gecikmesi ve iç/dış güvenliği güncel read-only kanıtla doğrula. Sonra takvimdeki bir sonraki görünür ürün teslimatına geç.
