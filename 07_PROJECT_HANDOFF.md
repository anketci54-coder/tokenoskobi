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

PROJECT_STATUS=ACTIVE_ERA55_P0_SINGLE_CYCLE_CANARY_AUTHORIZED
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_SINGLE_CYCLE_CANARY
LAST_COMPLETED_SUBSTEP=ERA55A_16_P0_QUEUE_PARITY_POST_TEST_AUDIT_AND_SINGLE_CYCLE_CANARY_DECISION
FRESH_SOURCE_CANDIDATES=106
UNOBSERVABLE_ROWS=0
EXACT_LEGACY_OBJECT_PARITY=true
EXACT_LEGACY_UID_ORDER_PARITY=true
SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

---

## 03 LAST VERIFIED WORK

LAST_COMPLETED=ERA55A_16_P0_QUEUE_PARITY_POST_TEST_AUDIT_AND_SINGLE_CYCLE_CANARY_DECISION
LAST_RESULT=OK_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_AUTHORIZED
LAST_ARTIFACT=data/control/era55a16_p0_queue_parity_post_test_audit_and_single_cycle_canary_decision_v1.json
WORK_UNIT_STATUS=CLOSED_SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=SINGLE_CYCLE_BOUNDED_CANARY_NOT_YET_EXECUTED

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

- Do not rerun A9-A16 unless evidence is invalidated.
- Do not execute more than one full runner canary cycle.
- Do not leave writer, lock, or hot-path override enabled after A17.
- Do not authorize general production or close P0 F1 from the decision alone.
- Do not start Option B.

---

## 07 ALLOWED NEXT DECISIONS

- Complete accounting: `VALIDATED`.
- Exact legacy parity: `VALIDATED`.
- Single-cycle bounded canary: `AUTHORIZED_NOT_EXECUTED`.
- General production activation: `BLOCKED`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP=ERA55A_17_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_AND_POST_AUDIT

---

## 08 NEXT SESSION EXECUTION RULE

1. Confirm A17 and the one-cycle authorization.
2. Capture timer/service state and create backups.
3. Pause the timer and require the service to be inactive.
4. Install only a runtime systemd drop-in under /run.
5. Enable writer, runner lock and one-shot hot wrapper for one full service cycle.
6. Remove the drop-in immediately and restore timer state.
7. Post-audit DB, output parity, service/timer state and feature flags.
8. Roll back on any failed gate; do not enable general production.

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
