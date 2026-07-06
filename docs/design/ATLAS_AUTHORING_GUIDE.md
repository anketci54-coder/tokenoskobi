# TOKENOSKOBI ATLAS AUTHORING GUIDE
## Canonical Visual Architecture & Map Standard

---

# 1. AMAÇ

Atlas;

- Teknik log değildir.
- Changelog değildir.
- Audit raporu değildir.
- Dosya listesi değildir.

Atlas, Tokenoskobi sisteminin görsel mimari hafızasıdır.

Amacı;

kod okumadan sistemin;

- nasıl kurulduğunu,
- parçalarının nasıl bağlandığını,
- verinin nereden gelip nereye gittiğini,
- engine'lerin hangi bölgelerde yaşadığını,
- runtime'ın nasıl aktığını,
- canonical dosyaların nasıl ilişkilendiğini

anlaşılır hale getirmektir.

---

# 2. ATLAS FELSEFESİ

Atlas bir klasör dökümü değil, bir dünya haritasıdır.

Tokenoskobi bir sistem değil, yaşayan bir kıta gibi ele alınır.

Her bileşen bu haritada bir yer tutar.

Her bağlantı bir yol, nehir, köprü, liman veya geçit gibi gösterilir.

Okuyucu Atlas'a baktığında şu duyguyu almalıdır:

"Bu sistemin dünyasını görüyorum."

---

# 3. ALMANAC İLE İLİŞKİ

Almanac hikâyeyi anlatır.

Atlas yapıyı gösterir.

Almanac şu soruları cevaplar:

- Ne oldu?
- Neden oldu?
- Nasıl oldu?
- Ne öğrendik?

Atlas şu soruları cevaplar:

- Nerede oldu?
- Ne nereye bağlı?
- Hangi parça hangi parçaya veri verir?
- Hangi dosya hangi göreve hizmet eder?
- Hangi engine hangi bölgenin sorumlusudur?

İki eser birbirini tamamlar.

---

# 4. TEK PARÇA BÜYÜK HARİTA VİZYONU

Atlas'ın ana hedeflerinden biri, Almanac'ın sonuna katlanabilir büyük harita olarak eklenebilecek tek parça Tokenoskobi Dünya Haritası üretmektir.

Bu harita;

- projenin tüm ana bileşenlerini,
- veri akışlarını,
- engine bölgelerini,
- canonical doküman adasını,
- runtime okyanusunu,
- klasör kıyılarını,
- güvenlik kalelerini,
- risk dağlarını,
- dış dünya limanlarını,
- kullanıcı karar noktasını

tek bakışta gösterecek şekilde tasarlanır.

---

# 5. GÖRSEL DİL

Atlas görsel dili şu kaynaklardan ilham alabilir:

- Eski dünya atlasları
- Katlanabilir keşif haritaları
- El çizimi mühendislik eskizleri
- Denizcilik haritaları
- Pusulalar
- Ölçek çizgileri
- Bölge adları
- Harita lejantları
- Parşömen / eski kâğıt estetiği

Ancak estetik, açıklığın önüne geçemez.

Her görsel önce anlaşılır olmalıdır.

---

# 6. HARİTA METAFORLARI

Atlas boyunca semboller tutarlı kullanılmalıdır.

- Kıta = Ana sistem bölgesi
- Ada = İzole veya özel görevli yapı
- Şehir = Engine
- Kale = Güvenlik katmanı
- Liman = API / dış giriş noktası
- Nehir = Veri akışı
- Yol = Süreç akışı
- Köprü = Entegrasyon
- Dağ = Risk / engel
- Orman = Bilinmeyen alan / anomaly
- Deniz = Veri havuzu / runtime alanı
- Fener = İzleme / monitoring
- Pusula = Yön / karar ilkesi
- Parşömen = Canonical doküman
- Kervan yolu = Pipeline
- Sınır kapısı = Gate / risk kontrol noktası

---

# 7. ATLAS CİLT YAPISI

Atlas ciltler halinde büyüyebilir.

Önerilen cilt yapısı:

## Cilt I - Tokenoskobi Dünya Haritası

Tek parça genel sistem haritası.

## Cilt II - Dosya Atlası

Klasörler, dosyalar, yaşam döngüleri ve bağımlılıklar.

## Cilt III - Engine Atlası

Hunter, Prosecutor, Unknown, Whale, News, Fusion ve diğer engine bölgeleri.

## Cilt IV - Runtime Atlası

Runtime akışı, event bus, scheduler, monitor, state ve log sistemleri.

## Cilt V - Canonical Atlası

Index, Manifesto, Roadmap, Almanac, Atlas, Master State ve Handoff ilişkileri.

## Cilt VI - Phase / Pass / ERA Atlası

Phase, Pass, ERA ve V zincirlerinin haritalı gösterimi.

## Cilt VII - Panel Atlası

Panel evrimi, kullanıcı yüzeyleri ve görsel karar noktaları.

## Cilt VIII - Data Atlası

Raw data, evidence, analysis, state, config, log ve audit store ilişkileri.

## Cilt IX - Security Atlası

Risk kapıları, kill-switch, authority boundaries, live trade kilitleri ve savunma yapıları.

## Cilt X - Future Atlası

Henüz yapılmamış ama planlanan uzun vadeli mimari dünya.

---

# 8. HER HARİTA SAYFASINDA OLMASI GEREKENLER

Her Atlas sayfası mümkün olduğunca şu bilgileri içerir:

- Haritanın adı
- Kapsadığı sistem bölgesi
- Amacı
- Ana bileşenler
- Veri girişleri
- Veri çıkışları
- Bağlı engine'ler
- Bağlı dosyalar
- Bağlı runtime parçaları
- Bağlı paneller
- Risk noktaları
- Kontrol noktaları
- Lejant
- Bugünkü durum
- Almanac referansı

---

# 9. DOSYA HARİTALAMA STANDARDI

Atlas'ta geçen önemli her dosya için şu bilgiler gösterilir:

- Dosya adı
- Bulunduğu klasör
- Görevi
- Neden oluşturuldu
- Kim kullanıyor
- Ne üretir
- Neye bağlıdır
- Hangi phase / pass / era sırasında ortaya çıktı
- Bugünkü durumu: active / archived / removed / superseded
- Kaldırıldıysa neden kaldırıldı
- Yerine ne geldi

---

# 10. ENGINE HARİTALAMA STANDARDI

Her engine için şu bilgiler gösterilir:

- Engine adı
- Görevi
- Girdi kaynakları
- Çıktıları
- Konuştuğu engine'ler
- Bağlı olduğu store
- Bağlı olduğu readmodel
- Panel bağlantısı
- Authority sınırı
- Risk sınırı
- Human approval ilişkisi

---

# 11. VERİ AKIŞ STANDARDI

Veri akışları haritada açık yönlü gösterilir.

Her akışın türü belirtilir:

- raw data
- normalized data
- evidence
- score
- risk
- signal
- decision support
- log
- audit
- alert
- human approval

Aynı ok rengi ve sembol mantığı korunur.

---

# 12. AUTHORITY VE GÜVENLİK STANDARDI

Atlas'ta authority sınırları özellikle görünür olmalıdır.

Açık kurallar:

- Runtime trade authority vermez.
- Runtime wallet authority vermez.
- Runtime signing authority vermez.
- Runtime real order oluşturmaz.
- AI final authority değildir.
- Human final authority korunur.
- Risk gate bypass edilmez.

Bu sınırlar haritalarda kale, sınır, gate veya kilit sembolleriyle gösterilir.

---

# 13. GÖRSEL KALİTE KURALLARI

Atlas görselleri;

- okunabilir,
- öğretici,
- estetik,
- tutarlı,
- sade ama zengin,
- tek bakışta yön veren

olmalıdır.

Görseller süs olarak kullanılmaz.

Her görsel bir şeyi öğretmelidir.

---

# 14. YASAKLAR

Atlas içinde şunlar yapılmaz:

- Rastgele ekran görüntüsü yığmak
- Bağlamı olmayan dosya listesi koymak
- Açıklanmayan diyagram kullanmak
- Birbiriyle çelişen semboller kullanmak
- Güncel olmayan mimariyi aktifmiş gibi göstermek
- Roadmap içeriğini Atlas'a taşımak
- Almanac hikâyesini Atlas'a taşımak
- Audit dump koymak
- HEAD / timestamp / GitHub logu yığmak

---

# 15. SEAL KURALI

Atlas güncellendiğinde şu kontrol yapılır:

- Harita gerçekten bir mimari ilişkiyi gösteriyor mu?
- Almanac ile çakışıyor mu?
- Roadmap ile çakışıyor mu?
- Current state bilgisi doğru kaynağa mı bırakılmış?
- Görselin bir öğretici amacı var mı?
- Sembol dili tutarlı mı?
- Authority sınırları korunuyor mu?

---

# 16. NİHAİ AMAÇ

Atlas'ın amacı yalnızca sistemi belgelemek değildir.

Amaç;

yıllar sonra bu projeyi gören bir insanın,

tek bir haritaya bakarak,

Tokenoskobi'nin nasıl bir dünya olduğunu,

hangi bölgelerden oluştuğunu,

hangi yollarla veri taşıdığını,

hangi kalelerle kendini koruduğunu,

hangi engine şehirlerinde karar desteği ürettiğini,

ve neden bu mimariyle inşa edildiğini

anlayabilmesidir.

Atlas, Tokenoskobi'nin görsel hafızasıdır.
