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

PROJECT_STATUS=ACTIVE_ERA55_P0_LEDGER_POST_TEST_AUDIT_REQUIRED
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_DROP_LEDGER
LAST_COMPLETED_SUBSTEP=ERA55A_7_P0_DROP_LEDGER_DESIGN_AND_TEMP_COPY_TEST
P0_LEDGER_SCHEMA_TEMP_COPY_VALIDATED=true
P0_F1_STATUS=OPEN_PENDING_POST_TEST_AUDIT_AND_APPLY_DECISION
PRODUCTION_LEDGER_APPLY_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A7 is closed with temp-copy PASS. A8 audit is the only authorized next work.

---

## 03 LAST VERIFIED WORK

LAST_COMPLETED=ERA55A_7_P0_DROP_LEDGER_DESIGN_AND_TEMP_COPY_TEST
LAST_RESULT=PASS_P0_LEDGER_DESIGN_TEMP_COPY_VALIDATED_NO_PRODUCTION_MUTATION
LAST_ARTIFACT=data/control/era55a7_p0_drop_ledger_design_and_temp_copy_test_v1.json
LAST_REPORT=reports/LATEST_ERA55A7_P0_DROP_LEDGER_DESIGN_AND_TEMP_COPY_TEST.md
LAST_SCHEMA=data/control/era55a7_p0_disposition_ledger_schema_v1.sql
WORK_UNIT_STATUS=CLOSED_TEMP_COPY_TEST_PASS
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
- Do not rerun A7 unless evidence is invalidated.
- Do not apply the ledger schema to production before A8 audit and explicit approval.
- Do not modify the live gateway, queue policy, service, timer or panel.
- Do not run production burst, kill, restart or WAL tests.
- Do not mark F1 closed based only on temp-copy success.

---

## 07 ALLOWED NEXT DECISIONS

- A7 temp-copy design/test verdict: `PASS`.
- Production ledger apply: `NOT_AUTHORIZED`.
- F1 remains open until an audited production implementation is verified.
- A8 may prepare apply/reject decision and rollback controls only.

NEXT_SAFE_STEP=ERA55A_8_P0_DROP_LEDGER_POST_TEST_AUDIT_AND_APPLY_DECISION

---

## 08 NEXT SESSION EXECUTION RULE

1. Confirm A8 is current.
2. Read A6 and A7 artifacts and the SQL schema.
3. Audit schema compatibility, migration idempotency, retention and failure behavior.
4. Define production backup, rollback, shadow observation and post-apply gates.
5. Decide apply or reject; do not mutate production in A8.
6. Preserve event-count, UID, integrity and authority gates.

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
