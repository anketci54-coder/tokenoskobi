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

PROJECT_STATUS=ACTIVE_ERA55_P0_PRE_GATEWAY_CANDIDATE_STREAM_REQUIRED
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_PRE_GATEWAY_CANDIDATE_STREAM
LAST_COMPLETED_SUBSTEP=ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION
A11_WRITER_MODULE_VALIDATED=true
CURRENT_BINDING_SOURCE=POST_FILTER_POST_DEDUP_POST_TRUNCATION_DISPLAY
PRE_GATEWAY_SOURCE_BOUND=false
BOUNDED_CANARY_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A12 rejected the bounded canary. Only A13 pre-gateway JSONL candidate-stream extraction and temp-copy binding is authorized.

---

## 03 LAST VERIFIED WORK

LAST_COMPLETED=ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION
LAST_RESULT=REJECT_BOUNDED_CANARY_SOURCE_ALREADY_FILTERED_AND_TRUNCATED
LAST_ARTIFACT=data/control/era55a12_p0_runtime_ledger_writer_post_test_audit_and_bounded_canary_decision_v1.json
WORK_UNIT_STATUS=CLOSED_BOUNDED_CANARY_REJECTED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=LEDGER_WRITER_SOURCE_ALREADY_FILTERED_AND_TRUNCATED

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

- Do not rerun A9-A11 unless evidence is invalidated.
- Do not authorize a bounded canary from the display-bound A11 evidence.
- Do not treat 50 admitted display rows as proof of complete candidate accounting.
- Do not enable production writer or runner-lock feature flags.
- Do not modify live DB, service, timer, gateway or panel during A13.
- Do not start Option B or mark P0 F1 closed.

---

## 07 ALLOWED NEXT DECISIONS

- Writer module: `VALIDATED`.
- Display-bound temp-copy integration: `VALIDATED_WITH_SOURCE_LIMITATION`.
- Pre-gateway complete candidate accounting: `NOT_PROVEN`.
- Bounded canary: `REJECTED_SOURCE_ALREADY_FILTERED_AND_TRUNCATED`.
- Production activation: `BLOCKED`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP=ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_EXTRACTION_AND_TEMP_COPY_BINDING_TEST

---

## 08 NEXT SESSION EXECUTION RULE

1. Confirm A13 is current.
2. Read both lane JSONL files directly before consumer filtering and truncation.
3. Convert every non-empty physical source line into one candidate observation, including parse failures.
4. Preserve duplicate and unsafe observations as ledger dispositions instead of dropping them.
5. Bind the existing writer to the extracted stream only on a disposable DB copy.
6. Prove complete accounting, queue parity, idempotency, rollback and recovery without production activation.

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
