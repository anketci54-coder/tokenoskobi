# 01_INDEX.md - TOKENOSKOBI / COINOSKOBI CANONICAL INDEX

## 1. BOOT POINTER

- `README.md` — kısa başlangıç ve güvenlik işaretçisi

## 2. HUMAN-READABLE CANONICAL DOCUMENTS

- `02_MANIFESTO.md` — anayasa, doktrin, yasaklar ve yetki sınırları
- `03_ROADMAP.md` — ileri yön, ana hatlar ve açılmamış işler
- `04_ALMANAC.md` — tamamlanan işler ve kapanış kayıtları
- `05_ATLAS.md` — mimari bağ ve veri akış haritası
- `06_PROJECT_MASTER_STATE.md` — güncel insan-okur proje özeti
- `07_PROJECT_HANDOFF.md` — yeni oturum devam bilgisi

## 3. MACHINE-READABLE CANONICAL AUTHORITIES

- `PROJECT_RUNTIME.json` — güncel durumun birincil kaynağı
- `PROJECT_BOOT.json` — sabit kimlik, doktrin ve başlangıç sözleşmesi
- `PROJECT_HISTORY.json` — eklemeli tarihsel kayıt; yalnız gerektiğinde okunur
- `data/tokenoskobi_v1_v8_master_era_roadmap.json` — V/ERA ana yol haritası

## 4. DOCUMENTATION LOCK

- `docs/canonical/CANONICAL_DOCUMENTATION_V1_LOCK.md` — canonical doküman sahipliği ve kapanış güncelleme sözleşmesi

## STARTUP READ ORDER

1. `PROJECT_RUNTIME.json`
2. `PROJECT_BOOT.json`
3. `06_PROJECT_MASTER_STATE.md`
4. `07_PROJECT_HANDOFF.md`
5. `02_MANIFESTO.md`
6. `03_ROADMAP.md`
7. `PROJECT_HISTORY.json` yalnız tarihsel bağlam gerektiğinde

## INDEX CONSTITUTION

`01_INDEX.md` yalnız navigation içindir.

Bu dosya şunları içermez:

- canlı runtime durumu
- GitHub HEAD veya zaman damgası
- proje tarihi veya kapanış ayrıntıları
- mimari teknik ayrıntı
- faz/ERA sonuçları
- root dizin envanteri
- geçici veya arşiv dosyaları

Navigation değişmedikçe bu dosya değiştirilmez.

<!-- STARTUP_RESUME_MAP_START -->
## STARTUP AND RESUME MAP

- Current state: `PROJECT_RUNTIME.json`
- Stable boot contract: `PROJECT_BOOT.json`
- Human-readable state: `06_PROJECT_MASTER_STATE.md`
- Continuation context: `07_PROJECT_HANDOFF.md`
- Constitution: `02_MANIFESTO.md`
- Future direction: `03_ROADMAP.md`
- History: `PROJECT_HISTORY.json`
- General isolated runtime stress harness: `tests/general_runtime_stress_harness_v1.py`
<!-- STARTUP_RESUME_MAP_END -->

## Runtime source contract

- `config/news_runtime_source_contract_v1.json` — policy-driven source activation contract; default deny.
