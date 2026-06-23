# 02 MANIFESTO - TOKENOSKOBI / COINOSKOBI

## ANA MOTTO

Şimşek kadar hızlı.
Balyoz kadar güçlü.
Kale kadar güvenli.
Karınca kadar tutumlu.

---

## VİZYON

Tokenoskobi;

rastgele sinyal üreten,

sosyal medya heyecanı kovalayan,

kör trade sistemi değildir.

Amaç:

kanıt toplamak,

riski ölçmek,

fırsatı değerlendirmek,

kararı disiplinli şekilde desteklemektir.

---

## EVIDENCE FIRST DOKTRİNİ

Önce kanıt.

Sonra analiz.

Sonra risk.

Sonra fırsat.

En son karar.

Kural:

EVIDENCE_FIRST=true

Kanıt olmadan:

- skor üretilmez
- karar üretilmez
- güven üretilmez

---

## RISK SUPREMACY DOKTRİNİ

Risk her şeyden üstündür.

Kural:

RISK_GATE_SUPREMACY=true

Aşağıdakiler Risk Gate'i geçersiz kılamaz:

- Teknik analiz
- Balina hareketi
- Haber akışı
- Sosyal medya
- AI önerisi
- Panel kararı

Risk reddediyorsa sistem reddeder.

---

## UNKNOWN UNKNOWN DOKTRİNİ

Bilinen saldırılar yeterli değildir.

Kural:

UNKNOWN_UNKNOWN_REQUIRED=true

Sistem sadece:

"Bu saldırı nedir?"

sorusunu değil,

"Bu davranış neden normal değil?"

sorusunu da cevaplamak zorundadır.

---

## AI DOKTRİNİ

AI yardımcıdır.

AI yönetici değildir.

AI trader değildir.

AI otorite değildir.

Kural:

AI_AUTHORITY=0

AI görevleri:

- açıklama
- özetleme
- sınıflandırma
- öneri

AI görevleri dışında:

- emir veremez
- risk aşamaz
- karar dayatamaz
- trade başlatamaz

---

## TRADE DOKTRİNİ

Trade motoru ile analiz motoru ayrı şeylerdir.

Kural:

TRADE_AUTHORITY=RISK_ENGINE_ONLY

Karar zinciri:

Evidence
↓
Risk
↓
Technical
↓
Opportunity
↓
Command Center

Risk motoru onaylamadan işlem yoktur.

---

## LIVE TRADE DOKTRİNİ

Canlı işlem varsayılan olarak kapalıdır.

Kural:

LIVE_TRADE=DISABLED

Ayrıca:

WALLET_SIGNING=DISABLED

Canlı işlem açılması:

ayrı faz,

ayrı onay,

ayrı audit gerektirir.

---

## LEARNING DOKTRİNİ

Öğrenme sistemi karar vermez.

Öğrenme sistemi hafıza oluşturur.

Görevleri:

- False Positive
- False Negative
- Missed Opportunity
- Avoided Loss
- Calibration

Öğrenme:

otorite değil,

geri besleme katmanıdır.

---

## SHADOW DOKTRİNİ

Önce Shadow.

Sonra gerçek.

Asla tersi değil.

Kural:

SHADOW_BEFORE_REAL=true

Aşamalar:

Radar
↓
Shadow
↓
Paper
↓
Micro
↓
Controlled Live

---

## RUNTIME DOKTRİNİ

Provider sınırlıdır.

Bütçe sınırlıdır.

Kaynak sınırlıdır.

Kural:

BOUNDED_RUNTIME=true

Amaç:

maksimum veri,

minimum maliyet.

---

## DOKÜMANTASYON DOKTRİNİ

Canonical doküman seti:

01_INDEX.md
02_MANIFESTO.md
03_ROADMAP.md
04_ALMANAC.md
05_ATLAS.md

Başka hiçbir doküman bu beşlinin yerini alamaz.

---

## CANONICAL GÜNCELLEME KURALI

Yeni PASS kapanırsa:

04_ALMANAC güncellenir.

Yeni PHASE kapanırsa:

03_ROADMAP güncellenir
04_ALMANAC güncellenir
05_ATLAS güncellenir

INDEX normalde değişmez.

MANIFESTO sadece doktrin değişirse güncellenir.

---

## YASAKLAR

Yasak:

- Kanıtsız karar
- Kanıtsız güven
- Risk bypass
- AI authority
- Doğrudan live trade
- Sınırsız provider kullanımı
- Kontrolsüz maliyet

---

## ALTIN KURALLAR

Kural 1:
Kanıt yoksa güven yok.

Kural 2:
Risk skordan üstündür.

Kural 3:
AI otorite değildir.

Kural 4:
Shadow canlıdan önce gelir.

Kural 5:
Önce hayatta kal.

Kural 6:
Kayıptan kaçınmak kazanç kadar değerlidir.

Kural 7:
Disiplin tahminden üstündür.

Kural 8:
Sistem amacı fırsat kovalamak değil,
kötü fırsatları elemekten başlamaktır.

Kural 9:
Her şey ölçülür.

Kural 10:
Her şey sorgulanır.

DOCUMENT_GOVERNANCE_V1=CANONICALLY_BOUND
DOCUMENT_SINGLE_SOURCE_OF_TRUTH=true
NO_DUPLICATE_DOCS=true
NO_MIRROR_DOCS=true
STRUCTURED_ARCHIVE_REQUIRED=true
ARCHIVE_IS_NOT_TRASH=true
ROOT_ONLY_CANONICAL_SUMMARY=true
PHASE_DIRECTORY_REQUIRED=true
PHASE_FILES_UNDER_DOCS_PHASES=true
NO_DELETE_WITHOUT_EXPLICIT_APPROVAL=true
NO_MASS_MOVE_WITHOUT_DRYRUN_MANIFEST=true
NEXT_REPO_GOVERNANCE_STEP=REPO_GOVERNANCE_PASS02_REORG_DRYRUN_MANIFEST_NOAPI

PHASE_CLOSE_DOCUMENT_UPDATE_RULE=CANONICALLY_BOUND
EVERY_PHASE_CLOSE_MUST_UPDATE_MANIFESTO=true
EVERY_PHASE_CLOSE_MUST_UPDATE_ROADMAP=true
EVERY_PHASE_CLOSE_MUST_UPDATE_ALMANAC=true
EVERY_PHASE_CLOSE_MUST_UPDATE_ATLAS=true
EVERY_PHASE_CLOSE_MUST_UPDATE_PROJECT_MASTER_STATE=true
EVERY_PHASE_CLOSE_MUST_UPDATE_PROJECT_HANDOFF=true
EVERY_PHASE_CLOSE_MUST_CREATE_DOCS_PHASE_FOLDER=true
NO_DUPLICATE_DOCS=true
DOCUMENT_SINGLE_SOURCE_OF_TRUTH=true
ARCHIVE_IS_NOT_TRASH=true


<!-- PHASE53F_FINAL_CANONICAL_DOC_UPDATE_LOCAL_APPLY_NOAPI:START -->
## PHASE53 Consumer / Readmodel Doctrine
PHASE53 binds PHASE52 Intelligence Officer Runtime output as observe-only consumer/readmodel contract. TRADE_AUTHORITY=0, AI_AUTHORITY=0, AUTO_APPLY=0, AUTO_BLOCK=0, WALLET_AUTHORITY=0, SIGNING_AUTHORITY=0 remain closed.
<!-- PHASE53F_FINAL_CANONICAL_DOC_UPDATE_LOCAL_APPLY_NOAPI:END -->
