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

PROJECT_STATUS=ACTIVE_ERA55_AWAITING_GEMINI_RED_TEAM_REVIEW
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_EXTERNAL_RED_TEAM_GATE
LAST_COMPLETED_SUBSTEP=ERA55A_5_BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE
BASELINE_REPORT_COMPLETE=true
GEMINI_PACKAGE_READY=true
GEMINI_REVIEW_COMPLETE=false
P0_QUEUE_RISK_OPEN=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A5 is closed. The package is ready, but external review is not yet complete.

---

## 03 LAST VERIFIED WORK

LAST_COMPLETED=ERA55A_5_BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE
LAST_RESULT=OK_BASELINE_REPORT_AND_GEMINI_PACKAGE_READY_NO_APPLY
LAST_ARTIFACT=data/control/era55a5_baseline_report_and_gemini_red_team_package_v1.json
LAST_REPORT=reports/LATEST_ERA55A5_BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE.md
WORK_UNIT_STATUS=CLOSED_PACKAGE_READY_REVIEW_PENDING
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=null

Queue is `50/50` and the P0 disposition-ledger gap remains open.

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
- Do not begin disposition-ledger implementation before Gemini findings are registered.
- Do not claim a DELETE-mode bottleneck without temp-copy comparison.
- Do not run production burst, kill, restart, service/timer or SQLite-mode tests.
- Do not apply watchdog, WAL, index, cache, delta refresh or queue-policy changes.
- Do not treat no current overflow as proof of historical zero loss.
- Do not infer cold-start, lock-contention, p99 or panel-latency results.
- Do not proceed to optimization implementation before the Gemini gate closes.

---

## 07 ALLOWED NEXT DECISIONS

Current authorized direction:

- The A5 report and Gemini package are ready.
- The next action is external Gemini review and exact findings registration.
- P0 disposition-ledger design is the first candidate intervention after review, not yet authorized for apply.
- All performance and runtime mutations remain blocked.

NEXT_SAFE_STEP=ERA55A_6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER

---

## 08 NEXT SESSION EXECUTION RULE

1. Read `PROJECT_RUNTIME.json`.
2. Confirm `ERA55A_6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER` is current.
3. Verify local and remote `main` synchronization.
4. Open `reports/LATEST_ERA55A5_BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE.md`.
5. Copy the `Gemini Red Team Copy-Paste Package` section exactly to Gemini.
6. Return Gemini's complete structured response without summarizing away details.
7. Register every finding by priority and blocking status.
8. Reject any production apply recommendation that bypasses temp-copy or correctness gates.
9. Select the next canonical work unit only after the review verdict is recorded.

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
