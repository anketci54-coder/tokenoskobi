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

PROJECT_STATUS=ACTIVE_ERA55_OPTION_B_TEMP_COPY_BENCHMARK_READY
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_OPTION_B_TEMP_COPY_BENCHMARK_READY
LAST_COMPLETED_SUBSTEP=ERA55A_25_P1_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION
NATURAL_TIMER_CYCLES_OBSERVED=12
PRODUCTION_BATCH_ROWS=4
PRODUCTION_LEDGER_ROWS=430
PRODUCTION_JOURNAL_MODE=delete
PRODUCTION_LEDGER_WRITER_ACTIVE=true
ADDITIONAL_CANARY_AUTHORIZED=false
P0_F1_CLOSED=true
OPTION_B_READINESS_CONFIRMED=true
OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED=true
OPTION_B_PRODUCTION_APPLY_AUTHORIZED=false
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

---

## 03 LAST VERIFIED WORK

LAST_COMPLETED=ERA55A_25_P1_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION
LAST_RESULT=OK_OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED_PRODUCTION_APPLY_BLOCKED
LAST_ARTIFACT=data/control/era55a25_p1_option_b_readiness_and_authorization_decision_v1.json
WORK_UNIT_STATUS=CLOSED_OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED_PRODUCTION_APPLY_BLOCKED
PRODUCTION_MUTATION=false
CURRENT_PROBLEM=OPTION_B_DELETE_VS_WAL_HYPOTHESIS_UNPROVEN

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

- Do not rerun A9-A25 unless evidence is invalidated.
- Do not execute another canary.
- Do not remove or edit the A23 persistent integration without a rollback plan.
- Do not delete or mutate any valid committed production batch.
- Do not change the production database journal mode in A26.
- Do not treat temp-copy benchmark authorization as production apply authorization.

---

## 07 ALLOWED NEXT DECISIONS

- Guarded production writer: `ACTIVE`.
- P0 F1: `CLOSED`.
- Additional canary: `BLOCKED`.
- Option B temp-copy benchmark: `AUTHORIZED`.
- Option B production apply: `BLOCKED`.

NEXT_SAFE_STEP=ERA55A_26_P1_OPTION_B_DELETE_VS_WAL_TEMP_COPY_BENCHMARK

---

## 08 NEXT SESSION EXECUTION RULE

1. Confirm A26 is current and A25 decision evidence remains valid.
2. Create independent immutable/disposable copies for DELETE-current and WAL-candidate variants.
3. Measure runtime, stage timing, commit proxy, write amplification, reader/writer blocking, integrity, event count and UID hash.
4. Do not modify the production database, service, timer, panel or guarded writer integration.
5. Do not authorize production WAL/apply unless correctness and recovery are identical and benefit is material.
6. Require a separate explicit human decision after the benchmark.

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
