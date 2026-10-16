# TOKENOSKOBI / COINOSKOBI

BSC tokenları için veri toplama, teknik analiz ve insan incelemesine yönelik karar
paketleri. Ürün servislerinin tek kod kaynağı `services/market/` dizinidir.
Kararlar danışma niteliğindedir; canlı işlem, cüzdan, imzalama, emir ve yayın yetkisi
vermez. Paper yetkisi de ürün yapılandırmasında kapalıdır.

## Hızlı başlangıç

Linux, macOS veya WSL üzerinde Python 3.11–3.13 gerekir. Depo kökünde:

```bash
./start.sh
```

Tarayıcıdan **http://127.0.0.1:8096** adresini açın. Panelin çalışması için ek Python
paketi veya API anahtarı gerekmez. Analiz sırasında internet erişimi gerekir;
sağlayıcı hataları ve eksik kanıtlar karar paketinde gösterilir. Sağlık kontrolü
yalnız uygulamayı ve kayıt bütünlüğünü doğrular; sağlayıcı erişimini doğrulamaz.

Panelde BSC token adresiyle analiz yapabilir, engelleme nedenlerini görebilir,
kararınızı notuyla kaydedebilir, sonucu güncelleyebilir ve kanıt paketini JSON
olarak indirebilirsiniz. Geçmiş, uygulama kapatılıp açıldığında korunur.

```bash
./start.sh --port 8097 --state-dir "$HOME/.local/state/tokenoskobi/product-slice-03"
python3 -B tokenoskobi.py check
```

Araştırma/haber araçları ve tüm testler için izole ortam kurulumu:

```bash
./setup.sh
.venv/bin/python -B tokenoskobi.py test
```

`setup.sh`, yalnız `cryptography` ve `jsonschema` bağımlılıklarını kurar.
`start.sh` varsa `.venv` Python'unu kullanır. Panel JavaScript testi için Node.js
gerekir; Node.js yoksa bu tek kontrol atlanır ve test çıktısında bildirilir.
`Ctrl+C` ile servis durdurulur.

İsteğe bağlı Chromium testi analiz, karar, sonuç, JSON indirme, sayfa yenileme ve
1280/390/320 piksel ekran kontrollerini çalıştırır. Yerelde çalıştırmak için:

```bash
npm install --prefix /tmp/tokenoskobi-browser playwright@1.64.1
node /tmp/tokenoskobi-browser/node_modules/playwright/cli.js install chromium --with-deps
TOKENOSKOBI_PLAYWRIGHT_MODULE=/tmp/tokenoskobi-browser/node_modules/playwright \
  node engineering/tests/browser_e2e.cjs
```

| Ayar | Davranış |
| --- | --- |
| `TOKENOSKOBI_PRODUCT_SLICE_02_PORT` | HTTP portu; `--port` bunu geçersiz kılar. |
| `TOKENOSKOBI_SLICE03_STATE_DIR` | Kalıcı karar geçmişi; `--state-dir` bunu geçersiz kılar. |
| `XDG_STATE_HOME` | Açık kayıt yolu yoksa `<değer>/tokenoskobi/product-slice-03`. |
| Varsayılan kayıt yolu | Eski `/var/lib/tokenoskobi-product-slice-03` varsa korunur; yoksa `~/.local/state/tokenoskobi/product-slice-03`. |
| `TOKENOSKOBI_GT_RATE_DIR` | Sağlayıcı hız sınırı kilitlerinin dizini. Varsayılan: `$XDG_CACHE_HOME/tokenoskobi` veya `~/.cache/tokenoskobi`. |
| `BSC_ALCHEMY_URL` | İsteğe bağlı RPC adresi. Anahtarları Git'e eklemeyin. |

Eski kayıt dizinine erişim hatası alırsanız mevcut geçmişin yedeğini alıp sahipliğini
düzeltin veya açıkça başka bir `--state-dir` seçin. Başka dizin seçmek mevcut
geçmişi taşımaz. Yedek almak için servisi durdurup **kayıt dizininin tamamını**
kopyalayın; paketler ve olay zinciri birlikte korunmalıdır.

Sürekli çalıştırma için [kullanıcı systemd servisi](config/systemd/tokenoskobi-product.service)
mevcuttur. Şablondaki depo ve kayıt yollarını kendi kurulumunuza göre düzenleyin,
`~/.config/systemd/user/` altına kopyalayın ve `systemctl --user daemon-reload`
ardından `systemctl --user enable --now tokenoskobi-product.service` çalıştırın.
Mevcut kurulumdaki kayıt dizinini şablonda da aynı tutun.
Uzak erişim için [Nginx şablonu](deploy/nginx/coinoskobi_panel_8096_proxy.conf.template)
kimlik doğrulaması ister; alan adı, parola dosyası ve HTTPS kurulmalıdır.
Depodaki şablonlar mevcut sunuculara otomatik uygulanmaz.

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
- `web/index.html`: her iki ürün servisi için ortak panel.
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
Kullanılmayan ML bağımlılıkları, eski uyumsuz panel ve `core/registry/` altındaki
kopya proje durum dosyaları da kaldırılmıştır. Kök dizindeki proje kayıtları ile
testlerin başvurduğu tarihsel kanıtlar korunur.

GitHub Actions tüm PR'larda ve `main` güncellemelerinde aynı test takımını,
sağlık kontrolünü ve A30 çökme/kurtarma kontrollerini çalıştırır.
