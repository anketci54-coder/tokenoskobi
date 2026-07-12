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

PROJECT_STATUS=ACTIVE_ERA55_P0_POST_REMEDIATION_CANARY_AUTHORIZED
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_POST_REMEDIATION_PRODUCTION_CANARY
LAST_COMPLETED_SUBSTEP=ERA55A_20_P0_POST_REMEDIATION_AUDIT_AND_PRODUCTION_CANARY_DECISION
ARCHIVE_TRIGGER_SAFE_ROLLBACK_INDEPENDENTLY_REPRODUCED=true
ROLLBACK_FAILURE_TRANSACTION_REVERSION_INDEPENDENTLY_REPRODUCED=true
FRESH_SOURCE_CANDIDATES=107
FRESH_SOURCE_ACCOUNTED=107
UNOBSERVABLE_ROWS=0
PROSPECTIVE_BATCH_DISTINCT=true
ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

---

## 03 LAST VERIFIED WORK

LAST_COMPLETED=ERA55A_20_P0_POST_REMEDIATION_AUDIT_AND_PRODUCTION_CANARY_DECISION
LAST_RESULT=OK_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED
LAST_ARTIFACT=data/control/era55a20_p0_post_remediation_audit_and_production_canary_decision_v1.json
WORK_UNIT_STATUS=CLOSED_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED
PRODUCTION_MUTATION=false
CURRENT_PROBLEM=POST_REMEDIATION_PRODUCTION_CANARY_NOT_YET_EXECUTED

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

- Do not rerun A9-A20 unless evidence is invalidated.
- Execute at most one A21 production canary cycle.
- Do not enable general production.
- Do not delete or mutate the valid A17 batch.
- Do not start Option B or close P0 F1.

---

## 07 ALLOWED NEXT DECISIONS

- Rollback remediation: `INDEPENDENTLY_VALIDATED`.
- Fresh prospective batch: `DISTINCT_AND_FULLY_ACCOUNTED`.
- One post-remediation production canary: `AUTHORIZED_NOT_EXECUTED`.
- General production activation: `BLOCKED`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP=ERA55A_21_P0_SINGLE_NATURAL_CYCLE_POST_REMEDIATION_CANARY_APPLY_AND_POST_AUDIT

---

## 08 NEXT SESSION EXECUTION RULE

1. Confirm A21 and the exact one-cycle authorization.
2. Back up the production DB and all mutable runtime outputs.
3. Pause the timer and require the service to be inactive.
4. Install only a runtime systemd drop-in.
5. Execute one full runner cycle with writer, lock, byte-preserving bridge and rollback guard.
6. On post-commit failure, roll back only the new batch and expose both errors.
7. Remove all overrides and restore timer state.
8. Post-audit existing-batch preservation, new-batch accounting, DB integrity and panel parity.
9. Do not enable general production after A21.

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
