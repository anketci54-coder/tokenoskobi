# 03 ROADMAP - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
ERA64_DEEPENING=FROZEN_AFTER_ERA64J
CURRENT_STAGE=TOKENOSKOBI_USABLE_PRODUCT_VERTICAL_SLICE
CURRENT_STATUS=PRODUCT_COMPLETION_MODE_ACTIVE_PLAN_LOCKED
NO_NEW_ERA=true
ERA64K_STATUS=DEFERRED_NOT_NEXT_STEP
NEXT_SAFE_STEP=PRODUCT_SLICE_01_READONLY_LIVE_TRUTH_AND_PANEL_ACCESS_VERIFICATION

## Ürün Tamamlama Kuralı

Test, schema, doküman veya bağımsız motor artık ilerleme ölçüsü değildir. İlerleme yalnız kullanıcının canlı URL üzerinde açtığı ve kabul ettiği uçtan uca ürün akışıyla ölçülür. Aktif ürün adımını doğrudan bloke etmeyen engine derinleştirmesi, mimari genişleme, yeni belge, yeni ERA veya alt ERA yasaktır.

## Son Doğrulanmış Teknik Temel

- ERA64J receipt ve gas-cost zenginleştirmesi doğrulandı.
- 172/172 test geçti.
- 367 gerçek BSC transfer olayı ve 277 gerçek işlem kapsandı.
- Wallet, signing, order, live trade ve gerçek finansal yetki sıfır kaldı.
- Başarılı wallet sınıflandırması henüz hazır değildir.
- İlk kullanılabilir ürün kurulum denemesi hata verdi ve tamamen rollback edildi; canlı ürün yüzeyi kurulmadı.

## Zorunlu Ürün Kapanış Sırası

1. **Canlı gerçeklik, panel erişimi ve güvenlik doğrulaması** — NEWS canlılığı, kesin panel URL/auth, servisler, Alchemy hibrit bağlantısı, onchain gecikmesi ve iç/dış güvenlik read-only doğrulanır.
2. **Tek token giriş ekranı ve gerçek karar paketi** — BSC token adresi; gerçek onchain, kontrat, likidite, teknik, NEWS ve wallet bağlamı; 1m/5m/15m/1h/4h/1d online analiz; Risk Engine kararı; kanıtlar ve `VERI_YETERSIZ` davranışı.
3. **İnsan onayı, karar geçmişi ve sonuç takibi** — ACCEPT/REJECT/WAIT/REVIEW kaydı, tekrar açılabilir kanıt paketi ve zaman içindeki sonuç değişimi.
4. **DEX wallet/CEX balina performansı ve Obsidian grafiği** — Swap yönü, router/pool, metadata, fiyat, tüm maliyetler, kapalı döngü, kanıtlı başarılı wallet, 50 BTC eşdeğer balina ve CEX akışları.
5. **Harekât Subayı, AI konseyi, self-healing önerisi ve operasyonel istihbarat** — Chatbot; NVIDIA, ChatGPT/Codex, Claude, Gemini ve Copilot advisory rolleri; arıza teşhis/diff/test/onay döngüsü; DEX-relevant teknoloji ve saldırı istihbaratı; opportunity-cost kararı.
6. **Sınırlı paper trade** — Yalnız önceki adımlar kullanıcı tarafından kabul edildikten sonra, sıfır gerçek fonla, Risk Engine veto ve insan politika zarfı içinde.

## Ürün Bitti Sayılma Şartı

Canlı URL açılır; BSC token adresi kabul edilir; gerçek karar paketi üretilir; eksik veri açıkça gösterilir; risk kararı ve kanıtları görünür; insan kararı kaydedilir ve geçmişten açılır; sonuç takibi çalışır; sonrasında paper trade aynı akışa bağlanır.
