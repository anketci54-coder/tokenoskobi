# TOKENOSKOBI / COINOSKOBI

Bu README yalnız başlangıç işaretçisidir. Canlı proje durumu burada tutulmaz.

## Yetkili başlangıç sırası

1. `PROJECT_RUNTIME.json`
2. `PROJECT_BOOT.json`
3. `06_PROJECT_MASTER_STATE.md`
4. `07_PROJECT_HANDOFF.md`
5. `02_MANIFESTO.md`
6. `03_ROADMAP.md`
7. `PROJECT_HISTORY.json` yalnız tarihsel bağlam gerektiğinde

Canonical navigation için `01_INDEX.md` kullanılır.

## Kaynak önceliği

1. Local workspace
2. Local Git
3. GitHub remote
4. AI memory

## Çalışma kuralları

- Yeni ERA yalnız açık insan kararıyla açılır.
- Kapanmış audit veya hat, kanıtlı drift yoksa yeniden açılmaz.
- Tek mantıksal operasyon, tek doğrulama seti, mümkünse tek commit ve tek push kullanılır.
- Runtime, DB, panel, service, timer veya yetki değişikliği yalnız açık kapsamla yapılır.
- Canlı trade, wallet signing, order creation ve AI trade authority kilitlidir.
- GitHub incelemesi önce; server yalnız local/runtime kanıtı gerektiğinde kullanılır.
- `tk machine` güncel canonical akışta çalıştırılmaz.
- Manifestoya eklenecek onaylı bir kural mevcut kuralla çakışıyorsa eski kuralın yerinde onun yerine geçer; manifestoda bulunmayan yeni kural en sona eklenir; mevcut yazım şekli, başlık düzeni, boşluk yapısı, yazı tipi ve biçimlendirme korunur.
## Script yaşam döngüsü

- `ACTIVE_RUNTIME`: systemd, timer veya doğrulanmış runtime zinciri tarafından çağrılır; açık runtime kapsamı olmadan taşınmaz veya değiştirilmez.
- `ACTIVE_LIBRARY`: aktif kod tarafından import edilir; caller doğrulanmadan taşınmaz.
- `MANUAL_ONLY`: yalnız açık insan komutuyla çalıştırılır; production entrypoint sayılmaz.
- `HISTORICAL_EVIDENCE`: geçmiş karar veya repair kanıtıdır; aktif `tools/` yüzeyinden archive alanına taşınabilir fakat kanıt zinciri korunur.
- `DISPOSABLE`: yeniden üretilebilir ve kanıt değeri olmayan geçici araçtır; yalnız kanıtlı sınıflandırma ve insan onayıyla repo dışına çıkarılabilir.
- Aynı yetenek için ikinci bir motor oluşturulmaz; yeni karmaşıklık yalnız net faydası kanıtlanırsa kabul edilir.
