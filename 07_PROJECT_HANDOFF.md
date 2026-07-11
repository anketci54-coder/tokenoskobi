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

PROJECT_STATUS=ACTIVE_ERA55_P0_DROP_LEDGER_TEMP_COPY_AUTHORIZED
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_DROP_LEDGER
LAST_COMPLETED_SUBSTEP=ERA55A_6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER
GEMINI_REVIEW_COMPLETE=true
GEMINI_BASELINE_VERDICT=BASELINE_ACCEPTED
OPTIMIZATION_APPLY_VERDICT=REJECTED_UNTIL_P0_CLEARED
P0_QUEUE_RISK_OPEN=true
A7_TEMP_COPY_TEST_AUTHORIZED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A6 is closed. A7 temp-copy work is the only authorized next step.

---

## 03 LAST VERIFIED WORK

LAST_COMPLETED=ERA55A_6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER
LAST_RESULT=BASELINE_ACCEPTED_OPTIMIZATION_REJECTED_UNTIL_P0_CLEARED
LAST_ARTIFACT=data/control/era55a6_gemini_red_team_review_and_findings_register_v1.json
LAST_REPORT=reports/LATEST_ERA55A6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER.md
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=null

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
- Do not apply a ledger schema to production.
- Do not modify the live gateway, queue policy, service, timer or panel.
- Do not run production overflow, burst, kill, restart or WAL tests.
- Do not claim an observed drop from the zero-overflow snapshot.
- Do not proceed to production optimization while F1 remains open.

---

## 07 ALLOWED NEXT DECISIONS

- Gemini baseline verdict: `BASELINE_ACCEPTED`.
- Production optimization verdict: `REJECTED_UNTIL_P0_CLEARED`.
- A7 disposable-copy schema/test is authorized.
- All live apply authority remains false.

NEXT_SAFE_STEP=ERA55A_7_P0_DROP_LEDGER_DESIGN_AND_TEMP_COPY_TEST

---

## 08 NEXT SESSION EXECUTION RULE

1. Confirm A7 is current.
2. Snapshot production DB and runtime-state hashes.
3. Create a disposable SQLite backup through a read-only source connection.
4. Apply the candidate ledger schema only to the copy.
5. Simulate overflow and every disposition.
6. Test rollback, uniqueness and foreign keys.
7. Verify event counts, UID sets and production hashes are unchanged.
8. Do not apply to production.

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
