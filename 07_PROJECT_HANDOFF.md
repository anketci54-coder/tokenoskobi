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

PROJECT_STATUS=ACTIVE_ERA55_P0_ROLLBACK_END_TO_END_REMEDIATION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_ROLLBACK_END_TO_END_REMEDIATION
LAST_COMPLETED_SUBSTEP=ERA55A_18_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION
VALID_CANARY_BATCH=true
PRODUCTION_BATCH_ROWS=1
PRODUCTION_LEDGER_ROWS=106
UNOBSERVABLE_ROWS=0
PANEL_BRIDGE_RECOVERED=true
AUTOMATIC_ROLLBACK_OBSERVED=false
END_TO_END_RUNNER_SUCCESS_PROVEN=false
CLEAN_POST_FIX_NATURAL_CYCLE_PROVEN=false
NEW_CANARY_AUTHORIZED=false
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

---

## 03 LAST VERIFIED WORK

LAST_COMPLETED=ERA55A_18_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION
LAST_RESULT=REJECT_GENERAL_PRODUCTION_ACTIVATION_END_TO_END_SUCCESS_AND_AUTOMATIC_ROLLBACK_NOT_PROVEN
LAST_ARTIFACT=data/control/era55a18_p0_post_canary_red_team_production_activation_decision_v1.json
WORK_UNIT_STATUS=CLOSED_GENERAL_PRODUCTION_ACTIVATION_REJECTED
PRODUCTION_MUTATION=false
CURRENT_PROBLEM=AUTOMATIC_ROLLBACK_AND_END_TO_END_SUCCESS_NOT_PROVEN

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

- Do not rerun A9-A18 unless evidence is invalidated.
- Do not execute another production canary.
- Do not delete the valid A17 batch.
- Do not enable the production writer.
- Do not start Option B or close P0 F1.

---

## 07 ALLOWED NEXT DECISIONS

- Valid canary ledger batch: `PRESERVED`.
- General production activation: `REJECTED`.
- New production canary: `NOT_AUTHORIZED`.
- Rollback and end-to-end remediation: `TEMP_COPY_ONLY`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP=ERA55A_19_P0_AUTOMATIC_ROLLBACK_AND_END_TO_END_SUCCESS_REMEDIATION_TEMP_COPY_TEST

---

## 08 NEXT SESSION EXECUTION RULE

1. Confirm A19 is current.
2. Work only on disposable DB and runtime-state copies.
3. Repair deterministic automatic rollback and expose rollback failures.
4. Prove a clean isolated runner sequence ending HOT_END:0.
5. Keep all production flags disabled.
6. Do not authorize a new production canary from A19 alone.

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
