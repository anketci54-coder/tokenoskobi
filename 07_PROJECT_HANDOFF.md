# 07 PROJECT HANDOFF - TOKENOSKOBI / COINOSKOBI

Bu dosya yeni oturumun kısa ve güncel devam bağlamıdır.

Birincil makine-okunur güncel durum yetkisi `PROJECT_RUNTIME.json` dosyasındadır.

İnsan-okunur güncel özet `06_PROJECT_MASTER_STATE.md` dosyasındadır.

Bu dosya tarihçe, roadmap, mimari açıklama, audit dökümü, dosya envanteri veya bağımsız current-state kopyası değildir.

---

## 01 STARTUP READ ORDER

1. `PROJECT_RUNTIME.json`
2. `PROJECT_BOOT.json`
3. `06_PROJECT_MASTER_STATE.md`
4. `07_PROJECT_HANDOFF.md`
5. `02_MANIFESTO.md`
6. `03_ROADMAP.md`
7. `PROJECT_HISTORY.json` yalnız tarihsel bağlam gerektiğinde

---

## 02 CURRENT CONTINUATION CHECKPOINT

PROJECT_STATUS=ACTIVE_NEWS_OPERATIONAL_BASELINE_CLOSED_SELECTION_GATE_READY
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
CURRENT_GATE=ERA55_SELECTION_GATE
GATE_STATUS=READY
ERA55_CANDIDATE=ERA55_RUNTIME_OPTIMIZATION
ERA55_CANDIDATE_STATUS=PLANNED_CANDIDATE_NOT_OPENED
HUMAN_SELECTION_REQUIRED=true
NEW_ERA_OPENED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

No new major project line has been selected.

Documentation normalization does not open ERA55.

---

## 03 LAST VERIFIED WORK

LAST_COMPLETED=NEWS_READONLY_AUDIT_CLOSURE_20260710
LAST_RESULT=OK_ALL_GAP_ROWS_EXACT_WATERMARK_EXCLUDED
LAST_ARTIFACT=data/control/news_readonly_audit_closure_20260710_v1.json
WORK_UNIT_STATUS=CLOSED
CURRENT_PROBLEM=null

The last verification belongs to the closed ERA54 line.

Current runtime counts and detailed NEWS state must be read from `PROJECT_RUNTIME.json` and `06_PROJECT_MASTER_STATE.md`; they are not duplicated here.

---

## 04 CURRENT CANONICAL DOCUMENT CONDITION

README=SHORT_STARTUP_POINTER_ONLY
INDEX=NAVIGATION_ONLY
MANIFESTO=DOCTRINE_ONLY
ROADMAP=FUTURE_DIRECTION_ONLY
ALMANAC=HISTORY_ONLY
ATLAS=ARCHITECTURE_MAP_ONLY
MASTER_STATE=CURRENT_SUMMARY_ONLY
HANDOFF=CONTINUATION_CONTEXT_ONLY
BOOT=STABLE_BOOT_CONTRACT_ONLY
RUNTIME=CURRENT_MACHINE_STATE_AUTHORITY
HISTORY=APPEND_ONLY_HISTORY

Legacy `PROJECT_MASTER_STATE.md` and `PROJECT_HANDOFF.md` files are compatibility pointers only.

---

## 05 AUTHORITY AND SAFETY BOUNDARY

HUMAN_FINAL_AUTHORITY=true
AI_AUTHORITY=0
TRADE_AUTHORITY=0
LIVE_TRADE=LOCKED
PAPER_TRADE=LOCKED
WALLET_AUTHORITY=0
SIGNING_AUTHORITY=0
ORDER_CREATE_AUTHORITY=0
AUTO_APPLY=0
AUTO_BLOCK=0

Risk Engine remains the final risk gate.

NEWS, whale, technical, Fusion, Prosecutor or AI outputs cannot bypass a hard risk block.

No Runtime, DB, panel, service, timer or deployment mutation is permitted without explicit scope and human approval.

---

## 06 DO NOT REOPEN OR REPEAT

- Do not reopen ERA54.
- Do not reopen the closed HBR attempt without a new archive-capable source and new sealed input.
- Do not rebuild NEWS from zero.
- Do not recreate removed historical current-state blocks.
- Do not copy current state into Manifesto, Roadmap, Almanac, Atlas or Index.
- Do not create a new canonical file when an owner file already exists.
- Do not open micro ERA records for plan, test, audit, review, seal or documentation cleanup.
- Do not run `tk machine` unless explicitly requested.
- Do not open ERA55 without explicit human authorization.

---

## 07 ALLOWED NEXT DECISIONS

The user must choose exactly one of:

- `OPEN_ERA55_RUNTIME_OPTIMIZATION`
- `SELECT_ANOTHER_MAJOR_PROJECT_LINE`
- `HOLD_NO_NEW_MAJOR_LINE`

Until that choice is made:

NEXT_SAFE_STEP=ERA55_SELECTION_GATE
NEW_ERA_OPENED=false

---

## 08 NEXT SESSION EXECUTION RULE

1. Read `PROJECT_RUNTIME.json`.
2. Confirm `ERA55_SELECTION_GATE` remains the next safe step.
3. Read Git HEAD dynamically.
4. Confirm local and remote `main` are synchronized before mutation.
5. Do not infer current state from AI memory or historical documents.
6. Use GitHub inspection first.
7. Use the server only when local or runtime evidence is required.
8. Wait for explicit human selection before opening a new major line.

---

## 09 HANDOFF CONTENT BOUNDARY

Handoff contains only the minimum information required to continue safely.

Detailed current state belongs to `PROJECT_RUNTIME.json` and `06_PROJECT_MASTER_STATE.md`.

Historical records belong to `04_ALMANAC.md` and `PROJECT_HISTORY.json`.

Future direction belongs to `03_ROADMAP.md`.

Architecture belongs to `05_ATLAS.md`.

Doctrine belongs to `02_MANIFESTO.md`.

Navigation belongs to `01_INDEX.md`.

---

## HANDOFF INSERTION AND REPLACEMENT CONSTITUTION

Yeni doğrulanmış devam bilgisi mevcut Handoff bilgisiyle çakışıyorsa, eski bilgi kendi bölümünde yeni bilgiyle değiştirilir.

Değiştirilen eski devam bilgisi bu dosyada ikinci bir kopya olarak tutulmaz; tarihsel kayıt gerekiyorsa `04_ALMANAC.md` veya `PROJECT_HISTORY.json` içinde korunur.

Yeni doğrulanmış devam bilgisi bu dosyada mevcut değilse ve hiçbir mevcut bilgiyle çakışmıyorsa, ilgili checkpoint, güvenlik, yasak veya sonraki karar bölümüne eklenir.

Yeni bilgi sırf yeni olduğu için dosyanın sonuna rastgele eklenmez; Handoff içindeki doğru devam katmanına yerleştirilir.

Handoff'un mevcut yazım şekli, başlık düzeni, boşluk yapısı, yazı tipi ve biçimlendirmesi açık kullanıcı onayı olmadan değiştirilmez.
