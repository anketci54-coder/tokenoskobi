# 07 PROJECT HANDOFF

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE=TOKENOSKOBI_USABLE_PRODUCT_VERTICAL_SLICE
STATUS=PRODUCT_COMPLETION_MODE_ACTIVE_PLAN_LOCKED
PRODUCT_COMPLETION_LOCK=true
NO_NEW_ERA=true
ERA64K_STATUS=DEFERRED_NOT_NEXT_STEP
NEXT_SAFE_STEP=PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION

## Son Doğrulanmış Teknik Temel

- ERA64J doğrulandı: 172/172 test, 367 gerçek BSC olayı, 277 işlem ve tam receipt/gas-cost coverage.
- Başarılı wallet sınıflandırması hazır değildir.
- Paper runtime ve live trade kapalıdır; gerçek wallet/signing/order/financial authority sıfırdır.
- `034b163` ürün builder denemesi `PAYLOAD_MISSING` ile durdu ve rollback edildi; ürün yüzeyi kurulmadı.

## Yeni Pencerenin Tek Görevi

Önce `README.md` dosyasını okuyup mandatory canonical boot sırasını eksiksiz uygula. Local workspace erişimi varsa local workspace ve local Git, GitHub remote’dan önce doğrulansın. Boot tamamlandıktan sonra yalnız `PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION` yürütülsün.

Bu adım read-only olacaktır ve şunları kanıtlayacaktır: NEWS katmanı canlı mı; panelin kesin canlı URL/auth yolu nedir ve telefondan açılıyor mu; Alchemy ve hibrit fallback zinciri çalışıyor mu; onchain-to-panel gecikmesi nedir; iç/dış güvenlik güncel olarak ne durumdadır.

Yeni ERA, alt ERA, yeni canonical belge, engine derinleştirmesi, paper runtime, live trade veya finansal authority açılmayacaktır. Sonuç tek doğrulanmış tablo olarak kullanıcıya sunulacaktır.
