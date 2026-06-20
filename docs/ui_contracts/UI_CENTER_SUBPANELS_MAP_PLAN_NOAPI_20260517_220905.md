# UI_CENTER_SUBPANELS_MAP_PLAN_NOAPI

Timestamp: `20260517_220905`

## Final

- FINAL_STATUS=PASS
- FINAL_GATE=UI_CENTER_SUBPANELS_MAP_PLAN_READY
- DB_UNCHANGED=True

## Scope

Plan only.

No panel mutation.  
No preview generation.  
No DB/API/fetch/paper/live.  
No asset mutation.  
No image generation.

## Ana karar

Sol ana menü **8 merkez** olarak kalır.

Paper Trade, AI Kalibrasyon, Outcome Memory, Backtest ve benzeri motorlar ayrı ana merkez olmaz.  
Bunlar ilgili merkezlerin altında alt modül olur.

## Global rules

- Sol ana menü 8 merkez olarak kalır.
- Paper Trade ayrı ana merkez olmaz; Komuta/Risk/Sistem altında alt modül olarak görünür.
- AI Kalibrasyon ayrı ana merkez olmaz; Sistem Kontrol Merkezi altında alt modül olur.
- Komuta Merkezi ana karar ekranında Paper ve AI güven özetini gösterir.
- Detaylar drawer/tab içinde açılır.
- Ana ekranlarda raw table/log dump yok.
- Veri yoksa iddia yok; empty_state gösterilir.
- Motion sadece motion_state_ref ile çalışır.
- No source_uid means no motion.
- Desktop sol menüde tam Merkezi isimleri korunur.
- Mobile kısa label kullanabilir: Komuta, Haber, Onchain, Balina, Teknik, Risk, Yaşam, Sistem.

## Center / subpanel map

### Komuta Merkezi

- id: `komuta_merkezi`
- desktop label: `Komuta Merkezi`
- mobile label: `Komuta`
- role: Ana karar ve operasyon yüzeyi

Alt modüller:

- **Canlı Karar** (`canli_karar`): Token bazlı al / sat / bekle / yasak karar özeti
- **Paper Trade Özeti** (`paper_trade_ozeti`): Paper plan, açık pozisyon ve simülasyon özeti
- **Açık Pozisyonlar** (`acik_pozisyonlar`): Açık paper/live olmayan izleme pozisyonları
- **SL / TP Durumu** (`sl_tp_durumu`): Stop loss ve take profit görünürlüğü
- **Aksiyon Geçmişi** (`aksiyon_gecmisi`): Son kararlar, bloklar ve kullanıcı aksiyon geçmişi
- **Merkez Skorları** (`merkez_skorlari`): Haber/onchain/teknik/risk/yaşam merkezlerinden gelen özet skorlar

### Haber Akış Merkezi

- id: `haber_akis_merkezi`
- desktop label: `Haber Akış Merkezi`
- mobile label: `Haber`
- role: Haber, kaynak güveni ve temel analiz istihbaratı

Alt modüller:

- **Kritik Haberler** (`kritik_haberler`): Yüksek etki ve teyitli haberler
- **Token Bağlantılı Haberler** (`token_baglantili_haberler`): Token ile eşleşmiş haberler
- **Borsa Duyuruları** (`borsa_duyurulari`): Binance/OKX/Coinbase vb. duyurular
- **Sosyal Söylenti / Teyitsiz** (`sosyal_soylenti`): Teyitsiz sosyal akış ayrı şeritte
- **Narratif Takibi** (`narratif_takibi`): Sektör/narratif trendleri
- **Haber Kaynak Sağlığı** (`haber_kaynak_sagligi`): Kaynak reliability ve fetch durumu

### Onchain Veri Merkezi

- id: `onchain_veri_merkezi`
- desktop label: `Onchain Veri Merkezi`
- mobile label: `Onchain`
- role: Onchain kanıt, transfer ve doğrulama yüzeyi

Alt modüller:

- **Pair Doğrulama** (`pair_dogrulama`): Token/pair kimlik doğrulama
- **Likidite Akışı** (`likidite_akisi`): Likidite giriş/çıkış ve doğum olayları
- **Transfer Akışı** (`transfer_akisi`): Büyük transfer ve token hareketleri
- **Holder Büyümesi** (`holder_buyume`): Holder artışı ve organik büyüme
- **Alıcı / Satıcı Dengesi** (`alici_satici_dengesi`): Buy/sell flow dengesi
- **Kontrat ve Deployer** (`kontrat_deployer`): Kontrat, deployer ve ilişki kanıtları
- **Kanıt Zaman Çizgisi** (`kanit_zaman_cizgisi`): Onchain olayların zaman çizgisi

### Balina Takip Merkezi

- id: `balina_takip_merkezi`
- desktop label: `Balina Takip Merkezi`
- mobile label: `Balina`
- role: Balina, smart wallet ve cüzdan radar merkezi

Alt modüller:

- **Canlı Balina Radarı** (`canli_balina_radari`): Fresh whale event varsa radar görünürlüğü
- **Smart Wallet Listesi** (`smart_wallet_listesi`): Başarı geçmişi olan wallet takibi
- **Whale Buy / Sell Akışı** (`buy_sell_akisi`): Büyük alım/satım hareketleri
- **Borsa Giriş / Çıkış** (`borsa_giris_cikis`): CEX giriş/çıkış hareketleri
- **Cüzdan Geçmişi** (`cuzdan_gecmisi`): Wallet geçmiş performansı
- **Cluster Haritası** (`cluster_haritasi`): Bağlantılı cüzdan kümeleri
- **Alarm Geçmişi** (`alarm_gecmisi`): Balina alarm kayıtları

### Teknik Analiz Merkezi

- id: `teknik_analiz_merkezi`
- desktop label: `Teknik Analiz Merkezi`
- mobile label: `Teknik`
- role: Fiyat, trend, momentum ve teknik teyit merkezi

Alt modüller:

- **Trend Paneli** (`trend_paneli`): Trend yönü ve market structure
- **Momentum Paneli** (`momentum_paneli`): RSI/MACD/ivme benzeri momentum
- **Destek / Direnç** (`destek_direnc`): Önemli fiyat seviyeleri
- **Hacim Teyidi** (`hacim_teyidi`): Hacim gerçekliği ve güç teyidi
- **Breakout Takibi** (`breakout_takibi`): Kırılım/kırılım iptali takibi
- **Zaman Dilimi Uyumu** (`zaman_dilimi_uyumu`): 1m/5m/15m/1h uyumu
- **Teknik Alarm Geçmişi** (`teknik_alarm_gecmisi`): Teknik sinyal geçmişi

### Risk Güvenlik Merkezi

- id: `risk_guvenlik_merkezi`
- desktop label: `Risk Güvenlik Merkezi`
- mobile label: `Risk`
- role: Para kaybetmeme, hard block ve güvenlik merkezi

Alt modüller:

- **Hard Block Kontrolü** (`hard_block_kontrolu`): Rug, sell block, identity conflict ve death block
- **Risk Skoru** (`risk_skoru`): Risk puanı ve güven seviyesi
- **Position Sizing** (`position_sizing`): Max güvenli alım ve önerilen büyüklük
- **SL / TP Planı** (`sl_tp_plani`): Stop loss ve take profit planı
- **Likidite Kapasitesi** (`likidite_kapasitesi`): Alım/satım kapasitesi ve derinlik
- **Slippage / MEV** (`slippage_mev`): Slippage, MEV ve sandwich riski
- **Exit Güvenliği** (`exit_guvenligi`): Satış testi, route ve çıkış güvenliği
- **Paper Trade Risk** (`paper_trade_risk`): Paper planlarının risk kontrolü

### Yaşam Destek Merkezi

- id: `yasam_destek_merkezi`
- desktop label: `Yaşam Destek Merkezi`
- mobile label: `Yaşam`
- role: Token yaşam döngüsü, klinik, otopsi, morg ve outcome hafızası

Alt modüller:

- **Olay Yeri İnceleme** (`olay_yeri`): Token olayının ilk kanıtları ve zaman çizgisi
- **Adli Soruşturma** (`adli_sorusturma`): Wallet/deployer/source ilişki soruşturması
- **Şüpheliler / Arananlar** (`supheliler`): Şüpheli cüzdanlar ve cluster takibi
- **Klinik / Yoğun Bakım** (`klinik`): Canlılık, recovery chance ve izleme yoğunluğu
- **Otopsi** (`otopsi`): Başarısızlık/ölüm sebebi ve ders çıkarımı
- **Morg** (`morg`): Ölü/stillborn token hafızası ve canlanma takibi

### Sistem Kontrol Merkezi

- id: `sistem_kontrol_merkezi`
- desktop label: `Sistem Kontrol Merkezi`
- mobile label: `Sistem`
- role: Makine dairesi, kalite, öğrenme ve sistem sağlığı

Alt modüller:

- **Servis Sağlığı** (`servis_sagligi`): systemd servisleri, runner ve timer durumu
- **Fetch / API Sağlığı** (`fetch_api_sagligi`): Kaynak fetch ve API bütçesi
- **DB Sağlığı** (`db_sagligi`): Integrity, FK, migration ve veri kalitesi
- **AI Kalibrasyon** (`ai_kalibrasyon`): Model/katman başarısı ve karar güveni
- **Outcome Memory** (`outcome_memory`): Geçmiş kararların sonuç hafızası
- **Backtest** (`backtest`): Strateji testleri ve historical performans
- **Paper Simülasyon Motoru** (`paper_simulasyon_motoru`): Paper plan/execution/outcome motoru
- **Panel Yayın Durumu** (`panel_yayin`): Preview/active panel ve promotion kontrolü
- **Loglar** (`loglar`): Runtime hata ve olay logları
- **Backup / Rollback** (`backup_rollback`): Yedek, rollback ve güvenli geri dönüş

## Paper Trade placement

- Komuta Merkezi: Paper Trade Özeti
- Risk Güvenlik Merkezi: Paper Trade Risk
- Sistem Kontrol Merkezi: Paper Simülasyon Motoru
- Yaşam Destek Merkezi: işlem sonucu / otopsi / outcome etkisi

## AI Kalibrasyon placement

- Sistem Kontrol Merkezi altında ana detay modülü
- Komuta Merkezi karar ekranında sadece AI Güven özeti
- Outcome Memory ile birlikte çalışır

## Next phase

`UI_CENTER_SUBPANELS_MAP_POST_AUDIT_NOAPI`
