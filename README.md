# TOKENOSKOBI / COINOSKOBI

BSC tokenları için veri toplama, teknik analiz ve insan incelemesine yönelik karar
paketleri. Ürün servislerinin tek kod kaynağı `services/market/` dizinidir.
Kararlar danışma niteliğindedir; canlı işlem, cüzdan, imzalama, emir ve yayın yetkisi
vermez. Paper yetkisi de ürün yapılandırmasında kapalıdır.

## Başlangıç ve kaynak sırası

Yerel çalışma alanı ve Git durumu, GitHub kopyasından ve sohbet hafızasından önce
gelir. Güncel proje kaydı ve çalışma sırası README içine kopyalanmaz.

1. [AGENTS.md](AGENTS.md) ve [.agents/skills/tokenoskobi-core/SKILL.md](.agents/skills/tokenoskobi-core/SKILL.md): yetki ve kanıt kuralları.
2. [docs/canonical/MANIFESTO.md](docs/canonical/MANIFESTO.md): proje doktrini.
3. [PROJECT_RUNTIME.json](PROJECT_RUNTIME.json): mevcut durumun sahibi `canonical_current_state_v4`; drift kaydı `canonical_drift_status_v4`.
4. [Ana yol haritası](data/tokenoskobi_v1_v8_master_era_roadmap.json): bağımlılıklar ve çalışma sırası.
5. [PROJECT_HISTORY.json](PROJECT_HISTORY.json): tarihsel kayıtlar.
6. [Mimari harita](docs/canonical/SYSTEM_MAP.md) ve [doküman dizini](docs/canonical/INDEX.md): destekleyici tarihsel bağlam.

Eski belgelerdeki yollar ve kapanış kayıtları bugünkü çalışan sistemin kanıtı
sayılmaz. Güncel durum sahibi ile tarihsel özetler çelişirse durum sahibi esas
alınır. Eksik kanıt açıkça bildirilir; tamamlanmış iş veya canlı erişim varsayılmaz.
İnsan nihai yetkilidir. Kullanıcı isteği dışında yeni çalışma birimi, üretim
servisi, ağ erişimi, veritabanı değişikliği veya finansal yetki açılmaz.

## Yerel doğrulama

Komutları depo kökünde çalıştırın. Ürün servisleri POSIX dosya kilidi kullandığı
için Linux/POSIX ortamı gerekir. Desteklenen Python sürümleri: 3.11–3.13.

```bash
python3 -m pip install -r requirements-test.txt
python3 -B -m unittest discover -s tests -v
python3 -B scripts/legacy/a30_process_crash_recovery_policy_test.py
python3 -B scripts/engineering/tokenoskobi_healthcheck.py --report /tmp/tokenoskobi-health.json
python3 -B engineering/tests/smoke_test.py
python3 -B engineering/tests/product_runtime_smoke.py
python3 -B -m engineering.tests.product_e2e
```

Sağlık kontrolü başarısızsa çıkış kodu 1 olur. `--report` verilmezse rapor dosyası
yazılmaz. Bu kontrol yerel dosyaları ve yapılandırmayı denetler; canlı API veya
üretim servislerinin sağlıklı olduğunu kanıtlamaz.

Ürün başlangıç testi geçici yerel portlarda iki servisi açar; paneli, sağlık
yanıtını ve geçersiz girdi reddini denetler, ardından süreçleri kapatır.
HTTP uçtan uca testi sentetik sağlayıcı yanıtlarıyla gerçek analiz, insan kararı,
sonuç kaydı, süreç yeniden başlatıldıktan sonra geçmişin korunması ve eski verinin
reddi akışlarını sınar. Canlı veri sağlayıcılarının erişilebilirliğini sınamaz.
`python3 tokenoskobi_kernel.py --machine` mevcut durumu dosya yazmadan okur;
grafik/registry üretimi yalnız açık `--write-registry` seçeneğiyle yapılır.

Testler canlı RPC/API kullanmaz. Araştırma testleri geçici imza anahtarları ve
manifestlerle çalışır. Staging testleri geçici SQLite veritabanları kullanır:
191 olaylık kayıt depodaki replay dosyasından yeniden okunur; tarihsel aktarım ve
receipt birim testleri açıkça sentetik, küçük örneklerle çalışır. Bunlar geçmiş
üretim veritabanının yeniden doğrulandığı anlamına gelmez. Tarihsel kontrol
kayıtlarına ait ayrı tutarlılık kontrolleri korunur.

## Ürün servisleri

```bash
python3 -m services.market.tokenoskobi_product_slice_02_server
# veya insan kararı ve geçmiş kaydı içeren servis:
python3 -m services.market.tokenoskobi_product_slice_03_runtime
```

İki servis varsayılan olarak aynı `127.0.0.1:8096` adresini kullanır; aynı anda
başlatmayın. `TOKENOSKOBI_PRODUCT_SLICE_02_PORT` ile port değiştirilebilir.
`TOKENOSKOBI_ROOT` verilmezse depo kökü kaynak dosyasından çözülür; çalışma dizinine
bağlı değildir. `TOKENOSKOBI_SLICE03_STATE_DIR` karar kayıtlarının konumunu belirler.
Eski `TOKENOSKOBI_SLICE02_SERVER_PATH` / `TOKENOSKOBI_SLICE03_CORE_PATH` dosya
override değişkenleri desteklenir, normal başlangıçta gerekli değildir.
Analiz isteği dış veri sağlayıcılarına erişir; sağlık uç noktası erişmez.

Teknik analiz en yeni mumun yaşını zaman diliminin iki katıyla sınırlar; gelecek,
sırasız veya tekrar eden zaman damgalarını ve pozitif olmayan kapanışları reddeder.
Yetersiz kanıt `ALLOW` üretemez. Haber güncelliği yalnız tokenla eşleşen kaydın
saat dilimi içeren yayın tarihinden hesaplanır; yeniden indirme zamanı eski haberi
güncel hale getirmez.

## Dizinler ve temizlik

- `core/`: yetki, doğrulama, kaynak ve platform sınırları.
- `services/market/`: ürün servislerinin tek uygulaması.
- `services/research/`: imzalı güven kökü gerektiren sınırlı araştırma motoru.
- `services/system/`: yetki kontrolüyle korunan sistem üreticisi.
- `scripts/legacy/`: mevcut testlerin kullandığı tarihsel motorlar ve araçlar.
- `config/systemd/`: servis örnekleri; dosyaların bulunması servisleri etkinleştirmez.
- `tests/`: çevrimdışı regresyon ve entegrasyon testleri.
- `data/`, `docs/`, `PROJECT_HISTORY.json`: kanıt ve tarihçe; otomatik silinmez.

Kopya ürün/kernel uygulamaları, kullanılmayan eski API/dağıtım kopyası ve eski
üretilmiş dosya envanterleri kaldırılmıştır. Önceki içerikler Git geçmişinden
alınabilir. Silinmiş ama testleri korunan motorlar Git geçmişinden yeni paket
konumlarına kurtarılmıştır. Üretilen rapor ve envanterler kaynak kod değildir.

GitHub Actions tüm PR'larda ve `main` güncellemelerinde aynı test takımını,
sağlık kontrolünü ve A30 çökme/kurtarma kontrollerini çalıştırır.
