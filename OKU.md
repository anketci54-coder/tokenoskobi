# OKU.md - TOKENOSKOBI / COINOSKOBI BAŞLANGIÇ DOSYASI

Bu dosya yeni bir sohbet açıldığında okunacak ilk ve tek başlangıç dosyasıdır.

Amacı; projenin mevcut durumunu, çalışma kurallarını ve okunacak canonical dosyaları tek noktadan göstermektir.

Bu dosya teknik dokümantasyon değildir. Teknik detaylar yalnızca canonical dokümanlarda bulunur.

---

# 1. PROJE DURUMU

## Proje

Tokenoskobi / Coinoskobi

## V1

- Kapatılmıştır.
- Doğrulanmıştır.
- GitHub'da mühürlenmiştir.

## V2

- Başlamıştır.
- Yeni repo değildir.
- Yeni DB değildir.
- V1 omurgası üzerinde kontrollü devam hattıdır.

## V3 Runtime

- Runtime geliştirme hattıdır.
- Trade authority açmaz.
- Wallet yetkisi açmaz.
- Signing açmaz.
- Live trade açmaz.
- Read-only mimari üzerinde geliştirilir.

---

# 2. SOURCE OF TRUTH

Tek kaynak:

PROJECT_MASTER_STATE.md

Teknik devam:

PROJECT_HANDOFF.md

Roadmap:

03_ROADMAP.md

Tarihçe:

04_ALMANAC.md

Mimari:

05_ATLAS.md

Anayasa:

02_MANIFESTO.md

Başlangıç:

OKU.md

Bu dosyalar okunmadan:

- yorum yapılmaz,
- plan kurulmaz,
- kod verilmez,
- yeni faz üretilmez,
- yeni pass üretilmez,
- yeni engine üretilmez,
- yeni roadmap yazılmaz.

---

# 3. OKUMA SIRASI

Yeni sohbet açıldığında aşağıdaki sıra uygulanır:

1. OKU.md
2. 01_INDEX.md
3. 02_MANIFESTO.md
4. 03_ROADMAP.md
5. 04_ALMANAC.md
6. 05_ATLAS.md
7. PROJECT_MASTER_STATE.md
8. PROJECT_HANDOFF.md

Bu sıra bozulmaz.

---

# 4. ANA MOTTO

Şimşek kadar hızlı.

Balyoz kadar güçlü.

Kale kadar güvenli.

Karınca kadar tutumlu.

---

# 5. TEMEL İLKELER

- Veriye göre konuş.
- Veri yoksa konuşma.
- Kanıt yoksa güven yok.
- Risk skordan üstündür.
- Önce hayatta kal.
- Disiplin tahminden üstündür.
- Genel çözüm özel yamadan üstündür.
- Shadow canlıdan önce gelir.

---

# 6. ÇALIŞMA DİSİPLİNİ

Kod istenmeden kod verilmez.

Kod gerekiyorsa:

- tek blok,
- yapıştır-çalıştır,
- compact,
- tekrar kullanılabilir,
- ürüne özel olmayan,
- yorum satırı gerektirmeyen biçimde hazırlanır.

Sunucu çöplüğe çevrilmez.

Gereksiz:

- log,
- backup,
- klasör,
- script,
- test dosyası,

üretilmez.

---

# 7. STANDART İŞ AKIŞI

Her geliştirme aşağıdaki sırayı izler:

PLAN

↓

ONAY

↓

APPLY

↓

TEST

↓

POST AUDIT

↓

GITHUB

↓

PROJECT_MASTER_STATE GÜNCELLEME

↓

ROADMAP

↓

ALMANAC

↓

ATLAS

Manifesto yalnızca anayasal kural değişirse güncellenir.

OKU.md yalnızca başlangıç davranışı değişirse güncellenir.

---

# 8. YETKİ SINIRLARI

AI yardımcıdır.

AI yönetici değildir.

AI trader değildir.

AI karar otoritesi değildir.

Varsayılan olarak kapalıdır:

- Trade
- Paper Trade
- Wallet
- Signing
- Live Execution
- Auto Apply
- Auto Block

Hard Block bypass edilemez.

Risk Engine onaylamadan işlem oluşmaz.

Execution Authority açılmadan işlem oluşmaz.

---

# 9. DOKÜMAN KURALLARI

Canonical bilgi yalnızca ilgili canonical dosyada bulunur.

Aynı bilgi ikinci kez farklı dosyaya taşınmaz.

Duplicate roadmap oluşturulmaz.

Duplicate phase oluşturulmaz.

Duplicate pass oluşturulmaz.

Duplicate engine oluşturulmaz.

Yeni isim uydurulmaz.

Yeni kapsam kullanıcı istemeden genişletilmez.

---

# 10. GITHUB KURALI

Hiçbir çalışma;

- GitHub'a gönderilmeden,
- doğrulanmadan,
- HEAD kontrol edilmeden,
- git status temizlenmeden

tamamlanmış sayılmaz.

Canonical HEAD kaydedilir.

Server ve GitHub senkron kalır.

---

# 11. YASAKLAR

Yasaktır:

- Kanıtsız karar
- Kanıtsız güven
- Risk bypass
- Hard Block bypass
- AI authority
- Trade authority açmak
- Wallet açmak
- Signing açmak
- Live trade açmak
- Ürüne özel kod
- Token özel yama
- Gereksiz dosya üretmek
- Gereksiz backup üretmek
- Gereksiz log üretmek
- Manifesto içine faz raporu yazmak
- Manifesto içine operasyon geçmişi yazmak

---

# 12. MEVCUT DURUM

V1 kapatılmıştır.

V2 kontrollü geliştirme hattıdır.

V3 Runtime geliştirme hattı başlamıştır.

Geliştirmeler yalnızca canonical mimariye uygun olarak devam eder.

Kullanıcı istemeden:

- yeni sistem kurulmaz,
- yeni mimari icat edilmez,
- yeni kapsam açılmaz,
- yeni faz tanımlanmaz.

---

# 13. SON KURAL

Önce oku.

Sonra anla.

Sonra mevcut state'i doğrula.

Sonra planla.

Sonra onay al.

Sonra uygula.

Sonra test et.

Sonra audit yap.

Sonra GitHub'a mühürle.

Son olarak canonical dokümanları güncelle.

Her zaman:

**Veriye göre konuş. Veri yoksa konuşma.**
## CURRENT STARTUP STATE — POST ERA15
ERA15_STATUS=CLOSED_VERIFIED_GITHUB_SEALED
ERA15_HEAD=76fd3ba861676c9e112b9ee71ac81af551dfafa4
CURRENT_ERA=ERA16
NEXT_WORK=ERA16_PHASE62

Runtime implementation line is closed.
New development continues under ERA16.

No new repo.
No new DB.
No trade authority.
No wallet authority.
No signing authority.
No AI authority.

## CURRENT STARTUP STATE — POST ERA16 PHASE63
CURRENT_HEAD=f716d4f1d4f943d0b6105c62aafe46b5f69cf385
CURRENT_ERA=ERA16
LAST_COMPLETED=ERA16_PHASE63_DISTRIBUTED_CONSTITUTION_GUARDIAN
PHASE63_STATUS=CLOSED_VERIFIED_GITHUB_SEALED
NEXT_WORK=ERA16_PHASE64

No new repo.
No new DB.
No trade authority.
No wallet authority.
No signing authority.
No AI authority.
