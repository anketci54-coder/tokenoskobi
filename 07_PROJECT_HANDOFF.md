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

PROJECT_STATUS=ERA56_CLOSED_ERA57_NOT_OPENED
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_STAGE=GENERAL_RUNTIME_CONTRACT_CLEANUP_CLOSED
LAST_COMPLETED=GENERAL_RUNTIME_EMERGENCY_PATCH_CLEANUP_AND_CANONICAL_REALIGN
EMERGENCY_PATCH_CHAIN_REMOVED=true
GENERAL_HARNESS=tests/general_runtime_stress_harness_v1.py
LEGACY_RAW_RESTORE_FORBIDDEN=true
ERA57_OPENED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

## 03 LAST VERIFIED WORK

LAST_COMPLETED=GENERAL_RUNTIME_SOURCE_ACTIVATION_DECISION
LAST_RESULT=DEFER_LIVE_SOURCE_ACTIVATION
LAST_ARTIFACT=data/control/general_runtime_source_activation_decision_v1.json
LIVE_FETCH_AUTHORIZED=false
RUNTIME_ELIGIBLE_SOURCE_COUNT=0
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

- Live source activation remains deferred.
- No source may be enabled automatically.
- No network budget has been authorized.
- ERA57 remains closed until its explicit opening decision.
- Production mutation remains blocked.

NEXT_SAFE_STEP=ERA57_AUTONOMOUS_RESEARCH_LAYER_OPENING_DECISION

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

<!-- PRE_ERA57_CONTINUATION_START -->
## PRE-ERA57 CONTINUATION

Read `PROJECT_RUNTIME.json` first. ERA56 is sealed. ERA57 is not opened.
The single reusable harness is `tests/pre_era57_stress_harness.py`.
It has not been executed by this preparation work unit.
NEXT_SAFE_STEP=PRE_ERA57_ISOLATED_ADVERSARIAL_STRESS_HARNESS_EXECUTION_DECISION
<!-- PRE_ERA57_CONTINUATION_END -->
