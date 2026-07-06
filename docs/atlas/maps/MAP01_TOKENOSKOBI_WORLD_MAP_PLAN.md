# MAP01 - TOKENOSKOBI WORLD MAP PLAN
## Atlas Ana Katlanabilir Harita Tasarım Planı

---

# AMAÇ

Bu dosya, Tokenoskobi Atlas'ın ana dünya haritasının nasıl tasarlanacağını tanımlar.

Hedef, Almanac'ın sonuna katlanabilir büyük harita olarak eklenebilecek tek parça bir sistem atlası üretmektir.

Bu harita, Tokenoskobi'nin tamamını kod okumadan anlaşılabilir hale getirmelidir.

---

# HARİTA VİZYONU

Tokenoskobi bir kıta gibi ele alınır.

Her ana sistem bölgesi haritada bir coğrafi bölge olarak gösterilir.

Her engine bir şehir, her güvenlik katmanı bir kale, her veri akışı bir nehir veya yol, her dış kaynak bir liman gibi temsil edilir.

Okuyucu haritaya baktığında şunu hissetmelidir:

"Bu sistemin dünyasını görüyorum."

---

# ANA BÖLGELER

## 1. Canonical Doküman Adası

Bu bölgede şunlar bulunur:

- 01_INDEX.md
- 02_MANIFESTO.md
- 03_ROADMAP.md
- 04_ALMANAC.md
- 05_ATLAS.md
- 06_PROJECT_MASTER_STATE.md
- 07_PROJECT_HANDOFF.md
- README.md

Görevi:

Sistemin hafıza, yön, doktrin ve devam merkezini göstermek.

## 2. Runtime Okyanusu

Bu bölgede runtime akışı gösterilir.

İçerik:

- scheduler
- runner
- monitor
- event flow
- state
- logs
- read-only boundary

## 3. Evidence Kıtası

Bu bölgede kanıt üretim zinciri gösterilir.

İçerik:

- raw data
- normalized data
- evidence
- audit
- immutable records

## 4. Engine Şehirleri

Haritada şehirler olarak gösterilecek ana engine'ler:

- Hunter Engine
- Prosecutor Engine
- Unknown Anomaly Engine
- Whale Intelligence
- News Intelligence
- Fusion Engine
- Risk Engine
- Tactical / Technical Engine
- Background Intelligence Officer
- Harekât Subayı

## 5. Risk Kaleleri

Güvenlik ve karar sınırları burada gösterilir.

İçerik:

- risk gate
- hard block
- kill switch
- authority boundary
- live trade disabled
- signing disabled
- wallet disabled

## 6. Data Denizleri

Veri havuzları burada gösterilir.

İçerik:

- data/
- readmodels
- state
- control JSON
- evidence JSON / JSONL
- historical records

## 7. Panel Limanları

Kullanıcı yüzeyleri ve yayınlanan görseller burada gösterilir.

İçerik:

- public/
- panel surfaces
- decision cockpit
- command center
- news center
- risk center
- whale center

## 8. Dış Dünya Limanları

Sistemin dış kaynaklarla ilişkisi burada gösterilir.

İçerik:

- blockchain RPC
- DEX data
- news sources
- whale wallets
- market feeds
- AI tools
- GitHub

## 9. Archive Kıtası

Artık aktif olmayan ama tarihsel değeri olan yapılar burada gösterilir.

İçerik:

- archive/
- legacy boot files
- old panel previews
- retired outputs
- root cleanup records

---

# HARİTA AKIŞLARI

Haritada gösterilecek ana akışlar:

1. Dış kaynaklardan veri girişi
2. Raw data to normalized data
3. Normalized data to evidence
4. Evidence to engine processing
5. Engine output to risk gate
6. Risk gate to readmodel
7. Readmodel to panel
8. Panel to human decision
9. Human decision to approved action boundary
10. Logs and audit back to Almanac / evidence memory

---

# AUTHORITY SINIRLARI

Haritada açık şekilde gösterilecek kilitler:

- Runtime trade authority vermez.
- Runtime wallet authority vermez.
- Runtime signing authority vermez.
- Runtime real order oluşturmaz.
- AI final authority değildir.
- Human final authority korunur.
- Risk gate bypass edilmez.

Bu bölgeler kale, kapı, kilit veya sınır sembolleriyle gösterilecektir.

---

# HARİTA LEJANTI

Kullanılacak semboller:

- Kıta = Ana sistem alanı
- Ada = Canonical veya izole yapı
- Şehir = Engine
- Kale = Güvenlik katmanı
- Liman = Dış giriş / API
- Nehir = Veri akışı
- Yol = Süreç akışı
- Köprü = Entegrasyon
- Dağ = Risk / engel
- Orman = Unknown / anomaly alanı
- Deniz = Veri havuzu
- Fener = Monitoring
- Pusula = Doktrin / yön
- Parşömen = Doküman
- Sınır kapısı = Gate

---

# GÖRSEL FORMAT

İdeal çıktı:

- A0 veya A1 boyutunda katlanabilir harita
- Eski dünya atlası estetiği
- Okunabilir büyük başlıklar
- Kısa açıklamalar
- Net lejant
- Tutarlı renk ve sembol dili
- Almanac arka cebine konabilecek yapı

---

# ALMANAC BAĞLANTISI

Almanac bu haritanın hikâyesini anlatır.

Atlas bu hikâyenin coğrafyasını gösterir.

MAP01 tamamlandığında Almanac'ın sonunda "Tokenoskobi Dünya Haritası" olarak konumlandırılacaktır.

---

# TAMAMLANMA KRİTERİ

Bu harita tamamlandığında okuyucu:

- sistemin ana bölgelerini,
- engine şehirlerini,
- veri yollarını,
- güvenlik kalelerini,
- dış dünya limanlarını,
- archive kıtasını,
- insan karar noktasını

tek bakışta anlayabilmelidir.
