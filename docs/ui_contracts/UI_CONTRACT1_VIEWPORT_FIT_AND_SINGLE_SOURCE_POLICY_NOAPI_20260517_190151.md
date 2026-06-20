# Tokenoskobi / Coinoskobi Living UI Contract v1

Phase: `UI_CONTRACT1_VIEWPORT_FIT_AND_SINGLE_SOURCE_POLICY_NOAPI`  
Timestamp: `20260517_190151`

## 1. Ana manifesto

- Veriye göre konuş, veri yoksa konuşma.
- Görsel efekt gerçek veri/state olmadan çalışmaz.
- Ana ekranlarda dikey scroll yok; her ekran viewport içine oturur.
- Her veri tek canonical source’dan gelir; farklı panellerde veri kopyalanmaz.
- Ana ekran özet verir; detaylar drawer, modal veya detay sekmesiyle açılır.
- Teknik PASS ürün PASS değildir; görsel kalite ve kullanım hissi ayrıca onaylanır.
- Yama yok, ürüne özel tekil hack yok, gereksiz preview/script çöplüğü yok.

## 2. Viewport-fit politikası

Ana ekranlar ve alt paneller `100vh` viewport içinde çalışır. Kullanıcı temel ekranda aşağı scroll yapmaz.

### Laptop

- Hedef genişlik: 1280-1536
- Hedef yükseklik: 720-900
- Kural: yoğun ama okunabilir kompakt grid; ana ekranda scroll yok.

### Desktop

- Hedef genişlik: 1537+
- Hedef yükseklik: 900+
- Kural: daha geniş grid, daha büyük radar/ikon; yine ana ekranda scroll yok.

### Scroll sadece nerede olabilir?

- Detay drawer/modal içinde uzun inceleme gerekiyorsa lokal scroll olabilir.
- Rapor/dump/log okuma ekranında ana panelden ayrı scroll olabilir.

## 3. Single-source data politikası

Bir veri sadece bir canonical yerde üretilir/saklanır. Paneller bu verinin view model’ini okur.

Yasaklar:

- Aynı token risk skorunu farklı dosyalarda ayrı ayrı hesaplamak.
- Aynı haber etkisini hem haber panelinde hem ana panelde farklı mantıkla üretmek.
- Panel içinde hardcoded fake metric basmak.
- Mock/demo veriyi canlı veri gibi göstermek.

Gerekli katmanlar:

1. canonical_data_layer
2. view_model_layer
3. screen_fit_layer
4. detail_layer
5. motion_state_layer

## 4. Living UI Truth politikası

Animasyon, glow, pulse, radar sweep, whale flash, badge hareketi gerçek data/state olmadan tetiklenmez.

State örnekleri:

- calm: Veri var ama eşik aşımı yok.
- watch: İzleme verisi var; düşük yoğunluklu dikkat.
- active: Taze olay veya anlamlı hareket var.
- critical: Kritik eşik aşıldı.
- dead: Lifecycle dead/morg durumu.
- revival: Canlanma sinyali gerçek veriye bağlıysa çalışır.

Veri yoksa:

- Animasyon yok.
- Değer gösterme yok.
- Panel “veri yok / beklemede” der.
- Sistem tahmin gibi konuşmaz.

## 5. Ana Panel sözleşmesi

Amaç: takip edilen coin/tokenların işlem ve karar merkezi.

Gösterilecekler:

- Takip edilen coin/token durumu
- Alım / satım kontrolleri
- SL durumu
- TP durumu
- Pozisyon durumu
- Paper/live ayrımı
- Risk/karar özeti
- Son veri tazeliği

Gösterilmeyecekler:

- Aşırı detay tablo yığını
- Aynı verinin tekrarları
- Veri olmayan fake hareket
- Ana ekranda scroll gerektiren uzun açıklamalar

Detay davranışı: Token detayına tıklanınca detay drawer/modal açılır; ana panel fit bozulmaz.

## 6. Token Yaşam Merkezi sözleşmesi

Amaç: Token lifecycle, olay yeri, klinik, otopsi, morg ve adli inceleme merkezi.

Departmanlar:

- Olay Yeri: ana kartta olay özeti; detayda ilk izler, tx, zaman çizgisi.
- Adli: ana kartta soruşturma durumu; detayda wallet/deployer/source bağları.
- Şüpheliler: ana kartta riskli aktör sayısı; detayda wallet listesi ve ilişki güveni.
- Klinik: ana kartta yoğun bakım/iyileşme özeti; detayda tedavi/izleme metrikleri.
- Otopsi: ana kartta analiz bekleyen/bitmiş sayısı; detayda ölüm sebebi ve outcome.
- Morg: ana kartta arşiv/dead/revival watch özeti; detayda morg kayıtları.

Kural: 6 departman kartı tek ekranda kalır; kartlarda özet, detaylar tıklanınca açılır.

## 7. PASS matrisi

- TECH_PASS: Kod çalıştı, dosyalar oluştu, hata yok.
- DATA_PASS: Veri canonical source’dan geliyor; tekrar/hardcode yok.
- FIT_PASS: Ekran scrollsuz viewport’a oturuyor.
- TRUTH_PASS: Efekt/animasyon gerçek veri/state ile tetikleniyor.
- PRODUCT_PASS: Görsel kalite, his, okunabilirlik ve kullanıcı onayı var.

## 8. Faz politikası

Sıra:

1. plan
2. dry-run
3. apply plan
4. explicit approval
5. real
6. post-audit

Açık onay olmadan gerçek apply yok.

## 9. Sonraki faz

`UI_CONTRACT2_SCREEN_MAP_AND_DATA_OWNERSHIP_NOAPI`
