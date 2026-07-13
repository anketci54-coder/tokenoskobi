# TOKENOSKOBI / COINOSKOBI

Bu dosya kısa başlangıç ve devam işaretçisidir. Canlı proje durumu burada kopyalanmaz; `PROJECT_RUNTIME.json` dosyasından okunur.

## Yeni pencere başlangıç sırası

1. `PROJECT_RUNTIME.json` — mevcut durum ve gerçek `NEXT_SAFE_STEP`
2. `PROJECT_BOOT.json` — kalıcı kimlik, anayasa ve başlangıç sözleşmesi
3. `06_PROJECT_MASTER_STATE.md` — okunabilir mevcut durum özeti
4. `07_PROJECT_HANDOFF.md` — devam bağlamı
5. `02_MANIFESTO.md` — kalıcı anayasal kurallar
6. `03_ROADMAP.md` — gelecek yönü
7. `PROJECT_HISTORY.json` — yalnız tarih gerektiğinde

Canonical navigation için `01_INDEX.md` kullanılır.

## Devam garantisi

- Önce `git rev-parse HEAD` ve tag doğrulaması yapılır.
- Mevcut ERA, son tamamlanan iş ve sonraki güvenli adım yalnız `PROJECT_RUNTIME.json` içinden okunur.
- README, Boot, Master State veya AI hafızası Runtime ile çelişirse Runtime üstün gelir.
- Local workspace ve Local Git, GitHub remote ve AI hafızasından üstündür.
- Yeni ERA yalnız açık insan kararıyla açılır.

## İcra modeli

`CONSTITUTION → RISK CLASSIFICATION → PLAYBOOK SELECTION → EXECUTION → EVIDENCE → SEAL`

Anayasal yaşam döngüsü değişmez. Temp-copy, shadow, canary, benchmark, stress veya red-team teknikleri zorunlu anayasa adımları değil; işin riskine göre seçilen playbook araçlarıdır.

## Kalıcı kısa kurallar

- Constitution is invariant; playbook is risk-driven.
- Genel çözüm özel yamadan üstündür; silinmiş legacy dosya geri getirmek genel onarım sayılmaz.
- Tek kullanımlık karar/test/audit script zincirleri oluşturulmaz.
- Complexity must pay for itself.
- Evidence never disappears; geçici araç kalıcı olmak zorunda değildir.
- One source of truth: current state owner is `PROJECT_RUNTIME.json`.
- Tek mantıksal operasyon, mümkünse tek commit ve tek push.
- Runtime, DB, panel, service, timer veya yetki mutasyonu yalnız açık kapsamla yapılır.
- Canlı trade, wallet signing, order creation ve AI trade authority kilitlidir.

## Script yaşam döngüsü

- `ACTIVE_RUNTIME`: doğrulanmış runtime zinciri tarafından çağrılır.
- `ACTIVE_LIBRARY`: aktif kod tarafından import edilir.
- `GENERAL_TOOL`: birden çok ERA ve bileşende yeniden kullanılabilen kalıcı araçtır.
- `MANUAL_ONLY`: yalnız açık insan komutuyla çalışır.
- `HISTORICAL_EVIDENCE`: geçmiş kanıtıdır; archive alanında korunur.
- `DISPOSABLE`: yeniden üretilebilir ve kanıt değeri olmayan geçici araçtır; silinir.
- Bir defalık karar aracı kapanışta silinir; ürettiği kanıt korunur.

## Runtime source contract

- Seed registry: `news_source_registry_v1`.
- Fetch policy: `news_source_fetch_policy_v1`.
- Seed presence does not authorize network access.
- Runtime eligibility is derived from registry + policy + explicit human authorization.
- Default behavior is deny/fail-closed.
- Current runtime-eligible source count: `0`.
- Canonical contract: `config/news_runtime_source_contract_v1.json`.
- No legacy raw runner restoration and no hardcoded runtime source list.
