# 02 MANIFESTO - TOKENOSKOBI CONSTITUTION

<!-- DEADLINE_LIVE_CANARY_LEARNING:BEGIN -->
## DEADLINE, LIVE CANARY AND LEARNING CONSTITUTION

- Usable product, paper-trade validation and initial bounded live canary target date is `2026-09-01`; the active date and schedule are owned by `PROJECT_RUNTIME.json`.
- Deadline pressure may remove bloat and nonessential work, but may not fabricate evidence or silently expand wallet, signing, order or capital authority.
- Initial live canary is BSC/PancakeSwap only, transaction notional is bounded to 1-2 USD, one open position, isolated canary wallet and exact-amount approvals.
- Unlimited token approval, automatic capital growth and hidden trade-authority expansion are forbidden.
- A monetary loss is counted as learning only when pre-trade evidence, decision, approval, execution, all costs, exit/outcome and error classification are stored and replayable.
- The learning layer may propose rule, model or code changes; it may not silently modify production code or activate a change without replay, regression/red-team evidence and human approval.
- The target date does not enable live trading today. Current live authority remains disabled until the final go/no-go and explicit user activation.
<!-- DEADLINE_LIVE_CANARY_LEARNING:END -->

<!-- PRODUCT_COMPLETION_CONSTITUTION:BEGIN -->
## PRODUCT COMPLETION AND DEFINITION OF DONE

- Test, schema, doküman, bağımsız engine, plan, commit veya audit tek başına ürün tamamlanması değildir.
- İlerleme; kullanıcının canlı yüzeyde açabildiği, gerçek veriyle çalışan, kanıt gösteren ve kabul ettiği uçtan uca akışla ölçülür.
- `PROJECT_RUNTIME.json` içinde product-completion lock aktifken yeni ERA veya alt ERA açılamaz.
- Yeni mimari veya engine derinleştirmesi yalnız aktif kullanıcı akışını doğrudan bloke eden eksik için yapılabilir.
- Aynı anda yalnız bir görünür ürün adımı yürütülür.
- Veri yoksa veya doğrulanamıyorsa sistem `VERI_YETERSIZ` der; sahte skor, sahte canlılık veya sahte karar üretmez.
- Tek token ekranı, gerçek karar paketi, insan kararı ve geçmiş takibi kullanıcı tarafından kabul edilmeden paper runtime açılamaz.
- Paper trade sıfır gerçek fonlu simülasyondur; live wallet, signing, order ve broadcast yetkisi oluşturmaz.
- Kapanış ölçütü etiket veya test sayısı değil, çalışan ve kullanıcı tarafından kabul edilmiş ürün döngüsüdür.
<!-- PRODUCT_COMPLETION_CONSTITUTION:END -->

## 0. CONSTITUTIONAL SCOPE AND SUPREMACY

Bu belge Tokenoskobi / Coinoskobi projesinin eksiksiz kalıcı anayasasıdır.

“Eksiksiz” ifadesi anayasa, doktrin, yasak, yetki sınırı, çalışma disiplini, güvenlik ilkesi ve AI rol sınırlarının tamamını kapsar.

Bu belge şunları içermez:

- Anlık runtime durumu
- Güncel `NEXT_SAFE_STEP`
- Git HEAD veya tag
- Kapanış tarihçesi
- Ayrıntılı roadmap
- Geçici ölçümler
- Operasyon logları

Bu içeriklerin sahipleri ayrı canonical dosyalardır.

Üstünlük kuralı:

```text
MANIFESTO
> AI önerisi
> dış red-team önerisi
> kolaylık
> hız baskısı
```

Manifesto ile çelişen roadmap, uygulama, öneri veya dokümantasyon geçersizdir.

---

## 1. PROJECT IDENTITY AND FINAL PURPOSE

Tokenoskobi:

- Risk-first kripto intelligence ve decision-support sistemidir.
- Sınırsız veya kendi yetkisini büyüten bir trade botu değildir; tam doğrulama sonrasında insanın tanımladığı politika zarfı içinde bounded otonom execution hedefler.
- Önce kanıt, sonra risk, sonra fırsat, en son insan kararı üretir.
- Amaç sermayeyi koruyarak kaliteli fırsatları bulmak, zayıf adayları çürütmek ve karar verene doğrulanabilir bağlam sağlamaktır.
- Sistemin gücü yalnız sinyal üretmekten değil; kanıt, itiraz, bilinmeyen anomali, hafıza ve fail-closed yönetiminden gelir.

Final authority insandır.

---

## 2. CORE MOTTO GATE

Kalıcı motto:

- Şimşek kadar hızlı.
- Balyoz kadar güçlü.
- Kale kadar güvenli.
- Karınca kadar tutumlu.
- Değişime uyumlu.

Zorunlu boyutlar:

```text
SPEED_NEVER_DOWN
POWER_NEVER_DOWN
SECURITY_NEVER_DOWN
ECONOMY_NEVER_DOWN
ADAPTABILITY_NEVER_DOWN
```

Yeni fikir, modül, AI önerisi, mimari değişiklik veya optimizasyon:

- En az bir boyutu iyileştirmeli.
- Diğer boyutları ölçülmeden düşürmemeli.
- Bloat, bakım yükü veya maliyet yaratıyorsa opportunity-cost testine girmeli.
- Negatif, belirsiz veya ölçülmemiş sonuçta reddedilmeli ya da ertelenmelidir.

Minimal güvenli yol, ölçülmüş üstünlük kanıtlanmadıkça ağır çözümden üstündür.

---

## 3. OPPORTUNITY COST FORMULA BINDING

Canonical temel:

```text
expected_gain = (reliability + security + probability) / 3
cost_penalty = max(0, 100 - performance)
uncertainty_penalty = max(0, 100 - statistics)
net_utility = expected_gain - cost_penalty - uncertainty_penalty
accept_baseline = net_utility >= 95
```

Eşleme:

```text
SPEED = performance
POWER = average(reliability, probability)
SECURITY = security
ECONOMY = inverse cost, bloat and maintenance burden
ADAPTABILITY = measured ability to evolve without breaking the other gates
```

Bir boyut gerilerse açık kullanıcı onayı ve pozitif opportunity cost zorunludur.

External AI çıktıları binding değildir.

---

## 4. EPISTEMIC DISCIPLINE

- Veriye göre konuş.
- Veri yoksa konuşma.
- Kanıt yoksa güven yok.
- Kanıt varsayımdan üstündür.
- Belirsizlik rahatlatıcı yorumla kapatılamaz.
- “Olabilir”, “sanırım”, “muhtemelen” kanıt yerine kullanılamaz.
- AI hiçbir zaman veri, mimari, roadmap, phase, pass, engine, status veya sonuç uyduramaz.
- Kanıt seviyesi açıkça ayrılır: isim referansı, schema, fiziksel varlık, veri, producer, runtime chain, consumer chain ve outcome aynı şey değildir.

---

## 5. SOURCE OF TRUTH AND CANONICAL OWNERSHIP

Çelişki halinde:

```text
LOCAL_WORKSPACE
> LOCAL_GIT
> GITHUB_REMOTE
> AI_MEMORY
```

Canonical sahiplik:

```text
README.md = single entry boot pointer
01_INDEX.md = navigation
02_MANIFESTO.md = constitutional doctrine
03_ROADMAP.md = future direction summary
04_ALMANAC.md = completed-work ledger
05_ATLAS.md = architecture map
06_PROJECT_MASTER_STATE.md = current human summary
07_PROJECT_HANDOFF.md = continuation context
PROJECT_BOOT.json = stable machine-readable boot contract
PROJECT_RUNTIME.json = current machine-state authority
PROJECT_HISTORY.json = append-only history
data/tokenoskobi_v1_v8_master_era_roadmap.json = detailed V1-V8 roadmap authority
```

Kurallar:

- One purpose = one canonical file.
- Duplicate canonical state yasaktır.
- Çelişen bilgi owner dosyada değiştirilir; ikinci kopya oluşturulmaz.
- Current-state sahibi yalnız `PROJECT_RUNTIME.json` dosyasıdır.
- Roadmap sırası yalnız master roadmap JSON’dan okunur.
- Kapanış kanıtı Almanac ve History’den doğrulanır.

---

## 6. SINGLE ENTRY BOOT CONSTITUTION

Tek giriş kapısı `README.md` dosyasıdır.

Yeni pencereye şu talimat yeterlidir:

> `README.md dosyasını oku ve canonical boot protocolünü uygula.`

README:

- Current state kopyalamaz.
- Bütün canonical dosyaların yerini, okuma sırasını ve owner sınırını gösterir.
- AI hafızasını source of truth olarak kullanmaz.
- Yeni pencerenin `NEXT_SAFE_STEP` değerini Runtime’dan, gelecek sırayı master roadmap’ten bulmasını zorunlu kılar.

Boot tamamlanmadan yeni iş başlatılamaz.

---

## 7. HUMAN AUTHORITY AND AUTONOMY BOUNDARY

```text
HUMAN_FINAL_AUTHORITY=true
AI_AUTHORITY=ADVISORY_ONLY
AI_TRADE_AUTHORITY=0
AI_WALLET_AUTHORITY=0
AI_SIGNING_AUTHORITY=0
AI_ORDER_AUTHORITY=0
```

Açık insan onayı olmadan:

- ERA/work unit açılamaz.
- Scope genişletilemez.
- Live fetch açılamaz.
- Production mutation yapılamaz.
- Runtime, DB, panel, service veya timer değiştirilemez.
- Wallet/signing/order/trade yetkisi verilemez.
- Paper veya live execution başlatılamaz.
- Risk kabul edilemez.

Otonom araştırma, otonom icra demek değildir.

Policy-based governance insan veto hakkını ortadan kaldırmaz.

---

## 8. FAIL-CLOSED SECURITY CONSTITUTION

- Güvenlik varsayılan durumdur.
- Least privilege zorunludur.
- Bilinmeyen veya eksik policy durumunda default deny uygulanır.
- Empty selection güvenli no-op/fail-closed davranır.
- Seed registry network izni değildir.
- Source kaydı runtime eligibility değildir.
- Runtime sözleşmesi canlı erişimi otomatik açmaz.
- Hard kill yalnız emergency içindir.
- Graceful decay varsayılan retirement yöntemidir.
- Runtime fail-silent olabilir; closure fail-safe olmak zorundadır.
- Güvenlik bariyeri “otonom esnetilemez”.

---

## 9. EXECUTION LIFECYCLE

Değişmez sıra:

```text
CURRENT_STATE_READ
→ IMPACT_ANALYSIS
→ PLAN
→ USER_APPROVAL
→ APPLY
→ TEST
→ AUDIT
→ POST_AUDIT
→ CANONICAL_SYNC
→ COMMIT
→ PUSH
→ REMOTE_VERIFY
→ GITHUB_SEAL
→ WORK_UNIT_CLOSED
→ NEXT_SAFE_STEP
```

İş:

- Clean status,
- başarılı test,
- post-audit,
- canonical sync,
- push,
- remote verification,
- seal

olmadan tamamlanmış sayılmaz.

Mümkünse tek mantıksal commit ve tek push kullanılır.

---

## 10. ONE ACTIVE WORK UNIT AND ROADMAP DISCIPLINE

- Aynı anda yalnız bir aktif work unit yürütülür.
- `NEXT_SAFE_STEP` dışına çıkılmaz.
- Kapanmış ERA/V immutable’dır.
- Kapanmış iş tekrar açılmaz.
- Yeni ERA açık insan kararı olmadan açılamaz.
- Canonical alt plan yoksa AI ayrıntı uyduramaz.
- Plan, test, audit, review, seal, küçük fix veya dokümantasyon için ayrı micro main-line açılmaz.
- One major capability per ERA.
- ERA purity korunur.
- Concept freeze aktif ERA boyunca geçerlidir.

Concept lifecycle:

```text
IDEA
→ HYPOTHESIS
→ EXPERIMENT
→ EVIDENCE
→ CAPABILITY
→ CORE
```

---

## 11. MAIN-LINE AND SUBSTEP CONSTITUTION

Ana hat gerçek yazılım, modül, büyük repair veya mimari milestone olmalıdır.

Varsayılan iç sıra:

```text
A = PLAN_OR_SCOPE
B = APPLY_OR_BUILD
C = TEST_OR_DRYRUN
D = AUDIT_OR_REVIEW
E = EXTERNAL_REVIEW_IF_NEEDED
F = GITHUB_SEAL_OR_CLOSURE
```

- İlgili işler aynı main-line altında kalır.
- Gerekiyorsa en fazla 2–3 sibling main-line’a gerekçeli bölünür.
- Sırf etiket üretmek için bölünmez.
- `_1/_2/_3` ötesinde nesting büyürse konsolidasyon yapılır.
- Fix/addition ilgili parent letter altında tutulur.

---

## 12. GENERAL SOLUTION AND ANTI-PATCH DOCTRINE

- Genel çözüm özel yamadan üstündür.
- Silinmiş legacy dosyayı geri getirmek general contract repair değildir.
- Aynı yetenek için ikinci engine oluşturulmaz.
- ERA/token/olay-özel kalıcı patch yasaktır.
- Tek kullanımlık plan/karar/test/audit/repair script zincirleri yasaktır.
- Reusable general tool korunur.
- Temporary tool kapanışta kaldırılabilir; kanıt korunur.
- Complexity must pay for itself.
- Emergency patch chain kapanışta sökülür ve general solution ile değiştirilir.

---

## 13. AI COMMAND AND RED-TEAM ROLE CONSTITUTION

### Başkomutan / Kullanıcı

- Nihai karar ve veto otoritesidir.
- Scope, risk, mutation, live erişim ve sermaye yetkisini yalnız kullanıcı verir.

### ChatGPT

- Planlar, analiz eder, kod tasarlar ve canonical bağlamı birleştirir.
- Kanıt olmadan tamamlandı demez.
- Onaysız write/apply yapmaz.

### Claude

- Code review, kontrol, mantık ve güvenlik eleştirisi yapar.
- Karar yetkisi yoktur.

### Gemini

- Red team ve mimari saldırı rolündedir.
- Zayıf varsayım, exploit yüzeyi, bypass ve adversarial senaryo arar.
- Çıktıları advisory-only’dir.

### GitHub Copilot

- Inline/repository destek sağlar.
- Doğrudan denetimsiz canonical write yapamaz.

### GitHub

- Source of truth zincirinde remote evidence, commit, diff, review ve seal katmanıdır.

### Harekât Subayı

- Tüm model çıktılarını karşılaştırır.
- Çelişki, risk, kanıt seviyesi ve opportunity cost skorlar.
- Merge/reject/defer önerisi verir.
- Trade, wallet, signing veya production authority yaratamaz.

Hiçbir AI başka bir AI’nın çıktısını otomatik onaylayamaz.

---

## 14. EVIDENCE, HUNTER, PROSECUTOR AND GUARDIAN DOCTRINE

- Hunter aday ve fırsat bulur.
- Prosecutor adayın karşı kanıtını, fraud/risk işaretlerini ve reddetme gerekçesini arar.
- Evidence Engine her iddiayı kaynak ve confidence ile bağlar.
- Guardian yalnız block/allow güvenlik kapısıdır; trade yetkisi yaratmaz.
- Fusion tek başına gerçeklik kaynağı değildir; kaynak kanıtlarını birleştirir.
- Recommendation, evidence ve authority birbirinden ayrıdır.
- Risk skordan üstündür.
- Capital preservation first.

---

## 15. UNKNOWN ANOMALY DOCTRINE

Sistem yalnız bilinen saldırı isimlerini aramaz.

Temel soru:

> “Bu saldırının adı nedir?” değil, “Bu davranış neden normal değil?”

Unknown Anomaly Engine:

- Normal davranış baseline’ını ölçer.
- Yeni ve etiketsiz sapmaları yakalar.
- Bilinmeyeni güvenli varsayımla ele alır.
- Yeni pattern’i evidence olmadan known attack olarak etiketlemez.
- Anomaliyi Prosecutor ve Guardian’a taşır.
- Unknown unknown riskini açık bırakır; sessizce yok saymaz.

---

## 16. ADVERSARIAL INTELLIGENCE DOCTRINE

Sistem saldırgan yöntemlerini sürekli öğrenilecek evolving doctrine olarak ele alır:

- Smart-contract exploit patternleri
- Rug pull ve upgradeable rug yöntemleri
- Honeypot ve hidden restriction teknikleri
- Liquidity/volume/price manipulation
- MEV, sandwich, bait ve route saldırıları
- Oracle manipulation
- Bridge exploitleri
- Wallet ve signing saldırıları
- Deployer/proxy/ownership deception
- Bot networkleri ve fake-volume ağları
- Social engineering ve psikolojik savaş
- News/narrative deception
- Exchange-flow ve market microstructure manipülasyonu

Her yeni taktik için:

```text
HOW_IT_WORKS
IS_TOKENOSKOBI_EXPOSED
DETECTION_SIGNAL
EVIDENCE_REQUIRED
DEFENSE
REPLAY_CASE
NEGATIVE_MEMORY_UPDATE
```

Bu bilgi saldırı yürütmek için değil, erken tespit ve savunma içindir.

---

## 17. MEMORY AND LEARNING DOCTRINE

### Negative Memory

- Doğrulanmış kötü pattern, reddedilme nedeni ve geçmiş failure korunur.
- Aynı hatanın sessizce tekrarına izin verilmez.

### Opportunity Memory

- Kaçan fırsatlar ve false negative’ler evidence ile kaydedilir.
- Gelecekteki aday bulma ve threshold kalibrasyonunda kullanılır.

### Outcome Memory

- Sinyal sonrası gerçek sonuç, fiyat etkisi, risk gerçekleşmesi ve karar kalitesi izlenir.
- Başarı iddiası outcome olmadan kurulmaz.

### Replay

- Geçmiş vakalar deterministik olarak yeniden çalıştırılabilir.
- Replay production mutation yaratmaz.

### Learning Boundary

- Öğrenme policy veya authority’yi kendi kendine genişletemez.
- Model improvement insan governance sınırına tabidir.

---

## 18. WHALE INTELLIGENCE DOCTRINE

- Önemli eşik: 50 BTC veya eşdeğer değer.
- Bilinen wallet gerçek entity adıyla yalnız evidence varsa etiketlenir.
- Sub-wallet, related-wallet ve cluster bağlantıları çıkarılır.
- Exchange inflow/outflow izlenir.
- Transfer sonrası fiyat hareketi karşılaştırılır.
- Wallet flow geçmiş haber ve event akışıyla korele edilir.
- Matematiksel, istatistiksel ve probabilistic pattern üretilir.
- Büyük transfer tek başına trade sinyali değildir.

---

## 19. NEWS AND TECHNOLOGY INTELLIGENCE DOCTRINE

News Intelligence:

- Kaynak güveni, identity match, evidence ledger, confidence ve freshness ile çalışır.
- Haber başlığı tek başına karar kanıtı değildir.
- Narrative, hype, opportunity ve risk ayrılır.
- Live source activation açık insan onayı gerektirir.
- Default deny geçerlidir.

Technology news geniş ve rastgele toplanmaz.

Yalnız Tokenoskobi’ye operasyonel etkisi olan gelişmeler öncelenir:

- AI model yetenekleri
- AI infrastructure
- GPU/CPU/AI accelerator
- Database/runtime/security tooling
- Blockchain/DEX/onchain altyapısı
- Kullanılan provider ve protokol değişiklikleri

---

## 20. DATA, EVIDENCE AND RETENTION CONSTITUTION

- Evidence never disappears.
- Provenance, timestamp, source, confidence ve decision link korunur.
- Immutable snapshot tercih edilir.
- Readmodel source of truth değildir.
- Cache yeniden üretilebilir olmalıdır.
- Historical evidence aktif runtime yüzeyinden ayrılabilir ama kaybolamaz.
- Blind bulk delete yasaktır.
- Unclassified/manual-only dosya kanıtsız silinemez.
- Production DB mutation açık kapsam ve rollback olmadan yapılamaz.
- Temp-copy test production kanıtı değildir; yalnız güvenli doğrulama aracıdır.

---

## 21. SCRIPT AND ARTIFACT LIFECYCLE

```text
ACTIVE_RUNTIME = runtime reachable; explicit scope olmadan dokunma
ACTIVE_LIBRARY = active code tarafından import edilir
ACTIVE_RUNTIME_DATA = active runtime tarafından kullanılan veri/contract
GENERAL_TOOL = birden çok ERA için reusable araç
MANUAL_ONLY = yalnız insan komutuyla çalışır
HISTORICAL_EVIDENCE = geçmiş kanıt; archive’da korunur
DISPOSABLE = reproducible, evidence-free, explicit inventory ile silinebilir
UNCLASSIFIED = körlemesine silinemez
```

Bir defalık araç kapanışta kaldırılır; ürettiği evidence korunur.

---

## 22. CODE GENERATION CONSTITUTION

Kullanıcı açıkça istemeden kod veya komut verilmez.

İstendiğinde:

- Tek paste-and-run blok
- Reusable
- Generic
- Minimal
- Compact
- Production-safe
- Idempotent
- Rollback-aware

`nano`, `vim` ve interaktif editor yasaktır.

Quoted Python heredoc içinde kırılabilir `$S`, `$TS` veya shell interpolation kullanılmaz; değer literal, argument veya environment ile güvenli aktarılır.

---

## 23. SERVER OPERATION CONSTITUTION

Bütün server komutları:

```text
cd /root/tokenoskobi_clean_v1
```

ile başlar.

Komutlar:

- SSH-safe
- Mobile-safe
- 4G-safe
- Re-runnable
- Disconnect-resilient
- Non-destructive by default

olmalıdır.

SSH oturumu gereksiz kapatılamaz, runtime gereksiz durdurulamaz ve kullanıcı manuel recovery’ye zorlanamaz.

---

## 24. RUNTIME AND MUTATION CONSTITUTION

Açık kapsam olmadan:

- Runtime mutation
- Database mutation
- Panel mutation
- Service mutation
- Timer mutation
- Deploy mutation
- Network mutation
- Authority expansion

yapılamaz.

Runtime hiçbir zaman Lab import etmez.

Lab:

- Read-only
- NOAPI varsayılan
- Hot path dışında
- Production authority’siz

kalır.

---

## 25. RECOVERY, ROLLBACK AND KILL-SWITCH DOCTRINE

- Recovery mutation’dan önce tasarlanır.
- Her riskli işlem rollback contractüne sahip olmalıdır.
- Atomic publish ve fail-closed tercih edilir.
- Partial publish kabul edilmez.
- Kill switch ayrı, basit ve test edilmiş olmalıdır.
- Emergency hard kill yalnız güvenli kapanış mümkün değilse kullanılır.
- Recovery kanıtlanmadan live readiness ilan edilemez.
- Backup, restore ve replay düzenli doğrulanır.

---

## 26. COST, PROVIDER AND SCALE DISCIPLINE

- Önce ölç, sonra harca.
- 0$ / free UI / local / GitHub tabanlı yol önce değerlendirilir.
- Ücretli API yalnız ölçülmüş fayda, bütçe, limit ve human approval ile açılır.
- Provider rate-limit, backpressure, timeout ve failover sözleşmesi olmadan hot path’e bağlanmaz.
- Ölçekleme capability kanıtından sonra gelir.
- GPU, distributed runtime ve multi-chain genişleme ölçülmüş ihtiyaç olmadan açılmaz.
- Maliyet saklanamaz; per-source/per-run görünür olmalıdır.

---

## 27. MULTI-CHAIN AND DEX EXPANSION SAFETY

- Yeni chain adapter read-only ve shadow-first başlar.
- Chain identity, address normalization ve unsupported-chain reject zorunludur.
- 13–15 chain hedefi roadmap konusudur; authority genişlemesi değildir.
- DEX route intelligence execution authority yaratmaz.
- Liquidity, slippage, fee, MEV ve route riskleri net expectancy’den önce değerlendirilir.
- Bridge ve cross-chain bağlantılar ayrı risk sınıfıdır.

---

## 28. GITHUB AND CLOSURE CONSTITUTION

İş tamamlanmadan önce:

```text
TEST=OK
POST_AUDIT=OK
CANONICAL_SYNC=OK
GIT_STATUS=CLEAN
COMMIT=CREATED
PUSH=OK
REMOTE_VERIFY=OK
GITHUB_SEAL=OK
```

olmalıdır.

- Tracked canonical dosya kendi gelecekteki commit hash’ini içermez.
- HEAD dinamik Git kaynağından okunur.
- Mid-substep push varsayılan değildir.
- Seal yalnız logical closure’da oluşturulur.
- GitHub remote AI hafızasından üstündür; local workspace/local Git remote’dan üstündür.

---

## 29. AMENDMENT CONSTITUTION

Manifesto değişikliği anayasa değişikliğidir.

Zorunludur:

- Açık kullanıcı onayı
- Impact analysis
- Çelişki kontrolü
- Eski çelişen kuralın kaldırılması
- Duplicate doctrine oluşmaması
- Verification
- GitHub synchronization
- Final seal

Yeni kural doğru başlığa eklenir; dosyanın sonuna rastgele yapıştırılmaz.

---

## 30. FINAL NON-NEGOTIABLE LOCK

```text
EVIDENCE_FIRST=true
RISK_FIRST=true
READ_ONLY_FIRST=true
SHADOW_FIRST=true
MEASURE_BEFORE_SPEND=true
CAPABILITY_BEFORE_EXPANSION=true
CAPITAL_PRESERVATION_FIRST=true
HUMAN_FINAL_AUTHORITY=true
FAIL_CLOSED_DEFAULT=true
ONE_PURPOSE_ONE_CANONICAL_FILE=true
ONE_ACTIVE_WORK_UNIT=true
CLOSED_ERA_IMMUTABLE=true
NEXT_SAFE_STEP_ONLY=true
NO_UNAUTHORIZED_LIVE_FETCH=true
NO_UNAUTHORIZED_PRODUCTION_MUTATION=true
NO_UNAUTHORIZED_TRADE=true
NO_UNAUTHORIZED_WALLET_ACCESS=true
NO_UNAUTHORIZED_SIGNING=true
NO_UNAUTHORIZED_ORDER_CREATION=true
GENERAL_SOLUTION_OVER_PATCH=true
EVIDENCE_NEVER_DISAPPEARS=true
COMPLEXITY_MUST_PAY_FOR_ITSELF=true
```

Final doctrine:

**Önce kanıt. Sonra risk. Sonra fırsat. En son insan kararı.**

<!-- BOUNDED_AUTONOMY:BEGIN -->
## BOUNDED AUTONOMY

Paper authority may create only simulated orders, fills, positions, costs, P&L and drawdown. Real wallet, signing, broadcast and capital authority remain locked. Human defines the policy envelope; Risk Engine has veto; the system cannot expand its own authority. Paper findings outrank speculative perfection work.
<!-- BOUNDED_AUTONOMY:END -->
