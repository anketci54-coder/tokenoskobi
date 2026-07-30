# TOKENOSKOBI / COINOSKOBI

## SINGLE ENTRY BOOT CONTRACT

Bu repository için tek başlangıç kapısı `README.md` dosyasıdır.

Yeni bir ChatGPT/AI penceresine yalnız şu talimat verilmesi yeterlidir:

> `README.md dosyasını oku ve içindeki canonical boot protocolünü eksiksiz uygula. Hafızaya göre karar verme.`

README mevcut proje durumunu kopyalamaz. Mevcut durum her zaman `PROJECT_RUNTIME.json` içinden okunur.

---

## 1. SOURCE OF TRUTH ORDER

Çelişki halinde kesin üstünlük sırası:

```text
LOCAL_WORKSPACE
> LOCAL_GIT
> GITHUB_REMOTE
> AI_MEMORY
```

Dosya yetkisi:

```text
PROJECT_RUNTIME.json
= güncel machine-state, son doğrulanmış iş ve NEXT_SAFE_STEP

data/tokenoskobi_v1_v8_master_era_roadmap.json
= ayrıntılı V1-V8 / ERA sırası, status, depends_on ve connects_to

02_MANIFESTO.md
= değişmez anayasa, doktrin, yasaklar ve yetki sınırları

PROJECT_BOOT.json
= sabit kimlik, boot sözleşmesi ve machine-readable kalıcı kurallar

03_ROADMAP.md
= insan-okunur gelecek yön özeti

04_ALMANAC.md
= kapanmış işlerin insan-okunur kayıt defteri

PROJECT_HISTORY.json
= append-only machine-readable tarihçe

05_ATLAS.md
= mimari bileşen ve bağlantı haritası

06_PROJECT_MASTER_STATE.md
= güncel insan-okunur durum özeti

07_PROJECT_HANDOFF.md
= devam bağlamı ve son oturum aktarımı

01_INDEX.md
= canonical navigation
```

Bir özet dosyası kendi owner kaynağıyla çelişirse owner kaynak üstün gelir.

---

## 2. MANDATORY READ ORDER

Yeni pencere aşağıdaki dosyaları bu sırayla okumalıdır:

1. `README.md`
2. `02_MANIFESTO.md`
3. `PROJECT_BOOT.json`
4. `PROJECT_RUNTIME.json`
5. `data/tokenoskobi_v1_v8_master_era_roadmap.json`
6. `03_ROADMAP.md`
7. `04_ALMANAC.md`
8. `05_ATLAS.md`
9. `06_PROJECT_MASTER_STATE.md`
10. `07_PROJECT_HANDOFF.md`
11. `PROJECT_HISTORY.json`
12. `01_INDEX.md`

Hiçbir dosya sohbet hafızasıyla ikame edilemez.

---

## 3. REPOSITORY AND SERVER VERIFICATION

Server erişimi varsa önce repository doğrulanır:

```bash
cd /root/tokenoskobi_clean_v1
git status --short
git rev-parse HEAD
git rev-parse origin/main
git tag --points-at HEAD
```

Kurallar:

- Working tree kirliyse nedenini raporla; körlemesine silme veya reset yapma.
- Local HEAD ile `origin/main` farklıysa senkron varsayma.
- Tag yalnız gerçek ref doğrulamasıyla kabul edilir.
- Server erişimi yoksa GitHub `main` okunur ve local workspace’in doğrulanamadığı açıkça belirtilir.
- AI hafızasındaki HEAD, status veya next-step kanıt sayılmaz.

---

## 4. BOOT RESOLUTION ALGORITHM

Yeni pencere şu algoritmayı uygular:

```text
A. Manifestodan anayasal sınırları yükle.
B. Boot dosyasından kalıcı kimlik, mimari ve startup contractünü yükle.
C. Runtime içinden current_version, current_era, current_stage,
   last_completed, last_result ve NEXT_SAFE_STEP değerlerini çıkar.
D. Master roadmap JSON içinde NEXT_SAFE_STEP ile ilgili ERA/work unit'i bul.
E. İlgili kaydın status, depends_on, purpose ve connects_to alanlarını doğrula.
F. Almanac ve History içinden kapanış kanıtını doğrula.
G. Atlas içinden etkilenecek mimariyi doğrula.
H. Master State ve Handoff ile insan-okunur devam bağlamını karşılaştır.
I. Çelişki varsa owner dosyaya dön; tahmin yapma.
J. Kullanıcıya yalnız doğrulanmış mevcut durum ve sıradaki tek güvenli adımı söyle.
```

---

## 5. NEXT WORK DETERMINATION

Sıradaki iş yalnız şu şekilde belirlenir:

```text
PROJECT_RUNTIME.NEXT_SAFE_STEP
→ master roadmap kaydını bul
→ depends_on kapanmış mı doğrula
→ status/opened durumunu doğrula
→ purpose ve connects_to alanlarını oku
→ açık insan onayı olmadan ERA/work unit açma
```

Alt plan canonical kaynaklarda yoksa:

- Uydurma.
- Hafızadan üretme.
- Önce kapsam, güvenlik sınırı, test planı ve kapanış kriteri öner.
- Kullanıcı onayı olmadan apply/write/refactor yapma.

Kapanmış ERA/V tekrar açılmaz.

---

## 6. MANDATORY BOOT OUTPUT

Boot tamamlanınca yeni pencere önce yalnız şu özeti vermelidir:

```text
REPOSITORY_SYNC=
CURRENT_VERSION=
CURRENT_ERA_OR_STAGE=
LAST_COMPLETED=
NEXT_SAFE_STEP=
BLOCKERS=
```

Ardından:

- Kod verme.
- Yeni ERA açma.
- Dosya değiştirme.
- Live fetch, runtime, DB, service, timer, wallet, signing veya trade yetkisi açma.
- Kullanıcıdan daha önce canonical dosyalarda bulunan bilgiyi tekrar isteme.

---

## 7. CANONICAL COMPACT WORKFLOW

Tokenoskobi içindeki bütün işler tek ana çalışma modeliyle yürütülür:

```text
READ
↓
VERIFY
↓
WORK
↓
VERIFY
↓
SEAL
```

### READ

- `README.md` tek başlangıç kapısıdır.
- README içindeki mandatory read order eksiksiz uygulanır.
- Güncel durum yalnız owner dosyalardan okunur.
- AI hafızası, eski sohbet veya tarihsel next-step çalışma otoritesi değildir.

### VERIFY

İş başlamadan önce yalnız gerekli doğrulamalar yapılır:

- local workspace
- local Git
- `origin/main`
- working tree
- `PROJECT_RUNTIME.json`
- ilgili roadmap/work-unit kaydı
- güvenlik ve yetki sınırları
- gerekli dependency ve closure durumu

Çelişki varsa owner dosya üstün gelir. Tahmin yapılmaz.

### WORK

- Aynı anda yalnız bir aktif bounded work unit yürütülür.
- İşin ihtiyacı neyse uygulanır: araştırma, planlama, kodlama, veri hazırlama,
  düzeltme, test, audit veya dokümantasyon.
- Her işe gereksiz, sabit ve uzun bir alt workflow zorlanmaz.
- Kullanıcı onayı gerektiren mutation veya yetki değişikliği açık onay olmadan
  uygulanmaz.
- `NEXT_SAFE_STEP` dışına çıkılmaz.
- Genel ve tekrar kullanılabilir çözüm, özel yamadan üstündür.

### VERIFY

Yapılan işe uygun kanıt üretilir:

- kod için test ve regression kontrolü
- veri için schema, semantic, evidence ve checksum kontrolü
- runtime için dry-run, fail-closed ve post-audit
- dokümantasyon için consistency ve authority kontrolü
- araştırma için kaynak ve doğruluk kontrolü

Kanıt yoksa tamamlandı denmez.

### SEAL

Mantıksal iş kapanışında gerekli olanlar tek kapanış altında uygulanır:

- canonical state sync
- ilgili runtime/history/handoff güncellemesi
- mümkünse tek commit
- mümkünse tek push
- remote verification
- gerekiyorsa checkpoint tag
- yeni tek `NEXT_SAFE_STEP`

Her küçük alt adım için ayrı commit, push, tag veya kapanış dosyası oluşturulmaz.

### Tek başlangıç promptu

Yeni bir AI penceresine yalnız şu talimat verilir:

> `README.md dosyasını oku ve içindeki canonical boot protocolünü eksiksiz uygula. Hafızaya göre karar verme.`

Başka devir promptu, uzun sohbet özeti veya elle yazılmış next-step metni gerekmez.

---

## 8. HARD SAFETY BOUNDARIES

```text
HUMAN_FINAL_AUTHORITY=true
AI_TRADE_AUTHORITY=0
AUTOMATIC_LIVE_FETCH=false
AUTOMATIC_PRODUCTION_MUTATION=false
AUTOMATIC_WALLET_AUTHORITY=false
AUTOMATIC_SIGNING_AUTHORITY=false
AUTOMATIC_ORDER_CREATION=false
FAIL_CLOSED_DEFAULT=true
```

Seed/source kaydı network erişim izni değildir.

---

## 9. CODE AND SERVER RULES

Kullanıcı açıkça istemeden kod veya komut verilmez.

Kod/komut istendiğinde:

- Tek paste-and-run blok.
- İlk satır `cd /root/tokenoskobi_clean_v1`.
- `nano`, `vim` veya interaktif editor yok.
- İdempotent, SSH-safe, mobile/4G-safe ve rollback-aware.
- Uzun işlemler bağlantı kopmasına dayanıklı tasarlanır.
- Quoted Python heredoc içinde kırılabilir shell değişkeni kullanılmaz.

---

## 10. SUCCESS CONDITION

Yeni pencere başarılı şekilde boot olmuş sayılır ancak:

- Manifesto sınırlarını biliyorsa,
- Runtime’daki gerçek mevcut durumu biliyorsa,
- Master roadmap’ten gelecek sırayı bulabiliyorsa,
- Kapanmış işleri tekrar açmıyorsa,
- Mimari owner dosyalarını ayırabiliyorsa,
- `NEXT_SAFE_STEP` dışına çıkmıyorsa,
- Kullanıcı onayı olmadan mutation yapmıyorsa.

Bu README tek giriş kapısıdır; current state veya roadmap’in ikinci kopyası değildir.


---

<!-- README_AUTO_CONTINUATION:BEGIN -->
## README AUTO-CONTINUATION CONTRACT

Reading `README.md` alone does not complete boot.

```text
README_ONLY_IS_NOT_BOOT_COMPLETE=true
MANDATORY_READ_ORDER_AUTO_CONTINUES=true
DO_NOT_STOP_AFTER_README_SUMMARY=true
DO_NOT_REQUEST_ALREADY_ACCESSIBLE_CANONICAL_FILES=true
```

After reading README, the AI must continue the mandatory read order automatically without waiting for another instruction.

Rules:

1. Use the local workspace when available.
2. Otherwise read the same canonical files from GitHub `main`.
3. Do not stop after summarizing README.
4. Do not ask the user to resend canonical files that are already accessible.
5. Do not state HEAD, current state, or `NEXT_SAFE_STEP` before the mandatory read order is complete.
6. Only when neither local nor GitHub canonical access is available, return:

```text
BOOT_RESULT=BLOCKED
BLOCKER=NO_CANONICAL_REPOSITORY_ACCESS
```

Required final boot output:

```text
REPOSITORY_SOURCE=
REPOSITORY_SYNC=
CURRENT_VERSION=
CURRENT_ERA_OR_STAGE=
LAST_COMPLETED=
NEXT_SAFE_STEP=
BLOCKERS=
BOOT_RESULT=
```
<!-- README_AUTO_CONTINUATION:END -->

<!-- PAPER_LIVE_AUTHORITY_SPLIT:BEGIN -->
## PAPER / LIVE AUTHORITY SPLIT

README remains a boot pointer. Current state is read only from `PROJECT_RUNTIME.json`.

Paper trade is zero-real-funds simulation authority. Live trade is real wallet, signing, broadcast and capital authority. Paper may run unattended only after build and validation. External AI and red team are advisory and outside the synchronous hot path.
<!-- PAPER_LIVE_AUTHORITY_SPLIT:END -->

<!-- CANONICAL_BOOT_V4:BEGIN -->
## CANONICAL BOOT V4.2 — TEK GİRİŞ, ACTIVE BRANCH, TAKVİM VE DRIFT DENETİMİ

Yeni pencereye yalnız şu talimat verilir:

> `README.md dosyasını oku ve içindeki canonical boot protocolünü eksiksiz uygula. Hafızaya göre karar verme.`

README özeti boot değildir. Mandatory read order 12/12 otomatik tamamlanır. Local workspace varsa local kaynak GitHub'dan üstündür. Local yoksa `main` sealed baseline olarak okunur ve açık aktif PR/work branch aynı 12 dosya setiyle ayrıca okunur.

### Canonical drift denetimi

Boot sırasında `PROJECT_RUNTIME.json` içindeki iki owner kayıt zorunlu okunur:

```text
CURRENT_STATE_OWNER=canonical_current_state_v4
DRIFT_STATUS_OWNER=canonical_drift_status_v4
```

Yalnız `canonical_drift_status_v4.unresolved_items` içindeki kayıtlar aktif drift sayılır. Tarihsel kapanışlarda bulunan eski `next_safe_step` değerleri current pointer değildir ve warning üretemez.

Boot çıktısına şunlar eklenir:

```text
CANONICAL_DRIFT_STATUS=
SCHEMA_GAPS=
OWNER_DUPLICATION_STATUS=
```

`PROJECT_BOOT.json` current state taşımaz. Current state yalnız Runtime owner kaydından, takvim master roadmap JSON'dan, history append-only kayıttan okunur.

### Takvim

Plan, gerçekleşen ve tahmin ayrı raporlanır. Hedef tarih `2026-09-01`; canlı canary bütün önceki kapılar ve ayrı insan onayına bağlıdır.

### Kod teslimi

```text
CODE_DELIVERY_MODE=DOWNLOADABLE_SH_ARTIFACT
FILE_EXTENSION=.sh
FULL_CODE_IN_CHAT=false
SINGLE_SELF_CONTAINED_FILE=true
```

Tam kod kullanıcı açıkça inline istemedikçe sohbet gövdesine yazılmaz.
<!-- CANONICAL_BOOT_V4:END -->
