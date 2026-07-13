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

PROJECT_STATUS=ERA56_CLOSED_PRE_ERA57_GENERAL_RUNTIME_HARDENING
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_MAIN_LINE=GENERAL_RUNTIME_HARDENING
CURRENT_STAGE=GENERAL_RUNTIME_HARDENING_A_CANONICAL_SYNC_CLOSED
LAST_COMPLETED=GENERAL_RUNTIME_HARDENING_A_CANONICAL_SYNC
GENERAL_HARNESS=tests/general_runtime_stress_harness_v1.py
STRESS_FINAL_GATE_CLOSED=false
LEGACY_RAW_RESTORE_FORBIDDEN=true
LIVE_FETCH_AUTHORIZED=false
ERA57_OPENED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

## 03 LAST VERIFIED WORK

LAST_COMPLETED=GENERAL_RUNTIME_HARDENING_A_CANONICAL_SYNC
LAST_RESULT=OK_CANONICAL_DRIFT_ZEROED
LAST_ARTIFACT=data/control/general_runtime_hardening_a_canonical_sync_v1.json
STRESS_GATE_STATUS=EVIDENCE_PRESENT_NOT_ACCEPTED_AS_FINAL_GATE
STRESS_EVIDENCE=archive/evidence/pre_era57_runtime_review/pre_era57_isolated_stress_harness_result_v1.json
ERA57_OPENED=false
PRODUCTION_MUTATION=false

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

- Build the reachable runtime and import graph.
- Classify active runtime, libraries, general tools, manual tools,
  historical evidence and disposable files.
- Do not delete or move files by name alone.
- Do not change the runtime wrapper in this substep.
- Do not enable live source fetch.
- ERA57 remains closed.

NEXT_SAFE_STEP=GENERAL_RUNTIME_HARDENING_B_ACTIVE_SURFACE_CLASSIFICATION

## 08 NEXT SESSION EXECUTION RULE

1. Read live systemd ExecStart, Environment and drop-ins.
2. Build the reachable runtime/import/reference graph.
3. Classify tools, data, runtime/state, reports and shadow lab.
4. Produce a keep/archive/delete proposal.
5. Do not move or delete anything during classification.
6. Do not modify DB, service, timer, panel or wrapper.

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
