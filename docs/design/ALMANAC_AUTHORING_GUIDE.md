# TOKENOSKOBI ALMANAC AUTHORING GUIDE
## Canonical Writing & Design Standard

---

# 1. AMAÇ

Almanac;

- Teknik log değildir.
- Changelog değildir.
- Audit raporu değildir.
- Phase listesi değildir.

Almanac, Tokenoskobi'nin doğuşundan geleceğine kadar olan tüm teknik ve insani yolculuğu anlatan yaşayan tarih eseridir.

Amaç;

gelecekte bu projeyi okuyacak insanların;

- nasıl başladığını,
- neden bu kararların alındığını,
- mimarinin nasıl evrildiğini,
- hangi bedellerin ödendiğini,
- hangi hataların yapıldığını

tam olarak anlayabilmesidir.

---

# 2. TEMEL FELSEFE

Her bölüm şu dört soruya cevap vermelidir.

- Neden?
- Nasıl?
- Ne öğrendik?
- Bundan sonra ne değişti?

---

# 3. CİLT MANTIĞI

Almanac tek dosya olarak büyümez.

Ana Almanac yalnızca:

- Önsöz
- Cilt listesi
- Genel zaman çizelgesi
- Ana dönüm noktaları

içerir.

Detaylar ayrı ciltlerde tutulur.

Örnek:

VOL01
VOL02
VOL03
...

İleride fiziksel kitap olarak basılabilecek yapıda hazırlanır.

---

# 4. İNSAN HİKÂYESİ

Teknik kayıtların yanında mutlaka;

- çalışma şartları
- kullanılan bilgisayar
- kullanılan sunucu
- maddi imkanlar
- iş hayatı
- aile hayatından yapılan fedakarlıklar
- psikolojik durum
- yaşanan çıkmazlar

dürüst şekilde anlatılır.

Başarı kadar başarısızlık da yazılır.

---

# 5. TEKNİK HİKÂYE

Her;

- Phase
- Pass
- ERA
- V

için aşağıdaki bilgiler bulunmalıdır.

Amaç

Problem

Çözüm

Sonuç

Öğrenilen ders

---

# 6. DOSYA YAŞAM DÖNGÜSÜ

Projede geçen önemli her dosya ilk geçtiği yerde anlatılır.

Örneğin;

boot_validator_v1.py

Neden yazıldı?

Neyi çözdü?

Ne kadar kullanıldı?

Yerine ne geldi?

Neden kaldırıldı?

Bugünkü durumu nedir?

Aynı standart;

script

service

timer

panel

json

schema

python

için de uygulanır.

---

# 7. MİMARİNİN EVRİMİ

Her büyük mimari değişiklik anlatılır.

Önceki yapı

Sorunları

Yeni yapı

Neden değiştirildi

Kazandırdıkları

---

# 8. PHASE / PASS / ERA ŞABLONU

Her kayıt mümkün olduğunca şu sırayı takip eder.

İnsan tarafı

Teknik ihtiyaç

Alınan karar

Üretilen dosyalar

Bağlı olduğu engine

Bağlı olduğu runtime

Bağlı olduğu panel

Sonraki adıma etkisi

Öğrenilen ders

---

# 9. GÖRSEL POLİTİKASI

Almanac mümkün olduğunca görsel destekli hazırlanacaktır.

Kullanılabilecek görseller;

- terminal görüntüleri
- ilk server
- ilk laptop
- ilk panel
- ilk github
- klasör ağaçları
- mimari şemalar
- veri akışları
- zaman çizelgeleri
- commit akışları
- phase diyagramları
- engine bağlantıları
- sistem haritaları

Hiçbir görsel süs amacıyla kullanılmayacaktır.

Her görsel bir hikâye anlatacaktır.

---

# 10. ATLAS BAĞLANTISI

Almanac hikâyeyi anlatır.

Atlas aynı olayın;

- mimarisini
- dosya ağacını
- veri akışını
- engine bağlantısını

gösterir.

İki eser birbirini tamamlar.

---

# 11. KANIT

Önemli olaylar mümkün olduğunca;

- Git Commit
- Audit
- JSON
- Runtime
- Panel
- Log

ile desteklenir.

---

# 12. YAZIM KURALLARI

Tamamen Türkçe.

Abartı yok.

Gerçek dışı anlatım yok.

Başarısızlık gizlenmez.

Yanlış kararlar yazılır.

Çöpe atılan fikirler yazılır.

Silinen dosyalar yazılır.

Mimari değişikliklerin gerekçeleri mutlaka anlatılır.

---

# 13. NİHAİ AMAÇ

Bu eser;

yalnızca Tokenoskobi'nin geçmişini belgelemek için değil,

gelecekte;

bir insanın,

bir geliştiricinin,

veya bir yapay zekânın

bu projeyi neden bu şekilde inşa ettiğimizi anlayabilmesi için hazırlanacaktır.

Hedef;

sıradan bir dokümantasyon üretmek değil,

yıllar sonra bile okunabilecek,

referans gösterilebilecek,

teknik ve insani değeri olan kalıcı bir eser bırakmaktır.
