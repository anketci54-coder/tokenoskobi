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

PROJECT_STATUS=ACTIVE_ERA55_P0_LEDGER_WRITER_TEMP_COPY_REQUIRED
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
LAST_COMPLETED_SUBSTEP=ERA55A_8_P0_DROP_LEDGER_POST_TEST_AUDIT_AND_APPLY_DECISION
PRODUCTION_LEDGER_SCHEMA_PRESENT=true
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTIMIZATION_APPLY_AUTHORIZED=false

---

## 03 LAST VERIFIED WORK

LAST_COMPLETED=ERA55A_8_P0_DROP_LEDGER_POST_TEST_AUDIT_AND_APPLY_DECISION
LAST_RESULT=OK_REPAIRED_SCHEMA_COMPLETE_TEMP_COPY_AND_PRODUCTION_DDL_ONLY
LAST_ARTIFACT=data/control/era55a8_p0_drop_ledger_post_test_audit_and_schema_only_migration_v1.json
LAST_REPORT=reports/LATEST_ERA55A8_P0_DROP_LEDGER_POST_TEST_AUDIT_AND_SCHEMA_ONLY_MIGRATION.md
LAST_SCHEMA=data/control/era55a8_p0_disposition_ledger_schema_v2.sql
WORK_UNIT_STATUS=CLOSED_SCHEMA_ONLY_MIGRATION_OK
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

- Do not rerun A8 unless evidence is invalidated.
- Do not insert production ledger rows manually.
- Do not activate the production writer.
- Do not mark P0 F1 closed.
- Do not begin performance optimization.

---

## 07 ALLOWED NEXT DECISIONS

- Production schema-only migration: `OK`.
- Production writer activation: `NOT_AUTHORIZED`.
- P0 F1: `OPEN`.
- A9 temp-copy writer test is authorized.

NEXT_SAFE_STEP=ERA55A_9_P0_LEDGER_WRITER_INTEGRATION_TEMP_COPY_TEST

---

## 08 NEXT SESSION EXECUTION RULE

1. Confirm A9 is current.
2. Integrate ledger generation only on a temp copy.
3. Couple ledger commit with queue publication or fail-closed marker.
4. Test all dispositions and writer failure.
5. Do not activate production writer.

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
