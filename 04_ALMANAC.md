# 04 ALMANAC - TOKENOSKOBI / COINOSKOBI MASTER ALMANAC

<!-- ERA55_SELECTION_GATE_SYNC_ALMANAC_START -->
## ERA55 SELECTION GATE CANONICAL BINDING SYNC

- Status: `CLOSED`
- Result: `OK_ERA55_SELECTION_GATE_CANONICAL_BINDING_SYNC`
- Parent: `ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME`
- Gate: `ERA55_SELECTION_GATE`
- Candidate ERA55 status: `PLANNED_CANDIDATE_NOT_OPENED`
- New ERA opened: `false`
- Timestamp UTC: `2026-07-10T14:02:44.985843+00:00`
<!-- ERA55_SELECTION_GATE_SYNC_ALMANAC_END -->

<!-- ERA54_FINAL_CLOSURE_INDEX_SYNC_CURRENT_START -->
## ERA54 FINAL CLOSURE CANONICAL SYNC RECORD

STATE_SYNC_UTC=2026-07-10T12:45:23.567774+00:00
PREVIOUS_HEAD_BEFORE_CLOSURE_COMMIT=89d7371474aa0772c8d8265b82a712fa4c80c125
TECHNICAL_CLOSURE_HEAD=c72995c352a76fe8557de369228f86e6f7d2846e
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
LAST_COMPLETED=ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI
LAST_DECISION=OK_ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI
CURRENT_ERA=ERA54
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
NEWS_OPERATIONAL_BASELINE=CLOSED_VERIFIED_BOUNDED_RUNTIME
NATURAL_TIMER_FULL_CYCLE=OBSERVED_VERIFIED
RAW_COUNT=372
MATCH_COUNT=184
SIGNAL_COUNT=184
SCORE_COUNT=184
MARKET_INDICATOR_COUNT=39
ADVERSARIAL_COUNT=59
HOT_QUEUE_COUNT=50
HOT_QUEUE_BOUND=50
PANEL_BRIDGE_DECISION=OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED
INDEX_STATUS=CANONICAL_NAVIGATION_CORRECTED
ERA_CLOSURE_DOCUMENT_SET=COMPLETE
ERA55_OPENED=false
NEXT_SAFE_STEP=NEXT_MAJOR_PROJECT_LINE_SELECTION_AFTER_NEWS_OPERATIONAL_BASELINE_CLOSURE
<!-- ERA54_FINAL_CLOSURE_INDEX_SYNC_CURRENT_END -->

<!-- HBR_CURRENT_ATTEMPT_CLOSE_START -->
## HBR ATTEMPT CLOSURE RECORD

STATE_SYNC_UTC=2026-07-10T11:28:35.885453+00:00
PREVIOUS_HEAD_BEFORE_CLOSURE_COMMIT=e7c850dc238cc10af2a2e47966d6bcd0876f592c
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
LAST_COMPLETED=HBR_SOURCE_WINDOW_REPAIR_OR_CLOSE_DECISION_NOAPI
LAST_DECISION=OK_HBR_SOURCE_WINDOW_CLOSE_DECISION_NOAPI
HBR_CLOSE_CHOICE=CLOSE_CURRENT_HBR_ATTEMPT_NO_WINDOW_REPAIR
HBR_CURRENT_ATTEMPT_STATUS=CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT
HBR_C_COLLISION_RESULT=NO_PRODUCTION_COLLISION
SEALED_INPUT_COUNT=55
LOCKED_WINDOW_ELIGIBLE_COUNT=0
SOURCE_WINDOW_REPAIR_NOW=false
HBR_B_RESEAL_NOW=false
HBR_D_PREDICTION_RUN=false
HBR_E_OUTCOME_FETCH=false
HBR_F_SCORE_COMPARISON=false
FUTURE_HBR_RETRY=BACKLOG_ARCHIVE_CAPABLE_SOURCE_NEW_SEAL_REQUIRED
NEXT_SAFE_STEP=POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_NOAPI
TK_MACHINE_EXECUTED=false
DB_OR_SCHEMA_MUTATION=false
<!-- HBR_CURRENT_ATTEMPT_CLOSE_END -->

<!-- ERA54_FINAL_CLOSURE_ALMANAC_START -->
## ERA54 FINAL CLOSURE NOAPI

CLOSED_UTC: 2026-07-08T17:25:07+00:00

Decision:
- OK_ERA54_FINAL_CLOSED_VERIFIED_NOAPI

Evidence:
- data/control/era54a_scope_fix_lock_noapi_v1.json
- data/control/era54b_standalone_scaffold_apply_plan_noapi_v1.json
- tools/hot_ingress_minimal_readonly_scaffold_v1.py
- data/control/era54c_hot_ingress_minimal_readonly_scaffold_dryrun_noapi_v1.json
- data/control/era54d_static_and_boundary_audit_noapi_v1.json
- data/control/era54f_final_closure_noapi_v1.json

Boundary:
- NOAPI true.
- Runtime unchanged.
- DB unchanged.
- Service unchanged.
- Panel unchanged.
- Wallet/trade unchanged.
<!-- ERA54_FINAL_CLOSURE_ALMANAC_END -->

<!-- ERA53_FINAL_CLOSE_ALMANAC_START -->
## ERA53 HOT INTELLIGENCE INGRESS GATEWAY FINAL CLOSE NOAPI

- Updated UTC: 2026-07-08T16:20:47.630453+00:00
- Status: FINAL_CLOSED
- Final seal: `data/control/era53_final_close_seal_noapi_v1.json`
- Final head: `cd4c043bf79840b69b95ec38ad85ba4dada2502a`
- Key artifacts:
  - `data/control/era53_hot_ingress_minimal_contract_consolidated_review_seal_noapi_v1.json`
  - `data/control/era53_hot_ingress_canonical_state_sync_noapi_v1.json`
  - `data/control/era53_post_sync_docs_only_apply_final_seal_noapi_v1.json`
  - `data/control/era53_final_close_seal_noapi_v1.json`
- Boundary: NOAPI; no DB/schema/runtime/systemd/source-adapter/queue/alarm/wallet/trade change.
- Next: `ERA54_PLAN_ONLY_IF_USER_REQUESTS`
<!-- ERA53_FINAL_CLOSE_ALMANAC_END -->

<!-- ERA52_READONLY_SCAFFOLD_ALMANAC_START -->
## ERA52 DISCIPLINE LAYER MINIMAL READONLY SCAFFOLD NOAPI

- Updated UTC: 2026-07-08T11:06:16.159789Z
- Status: CLOSED
- Module: `tools/discipline_layer_readonly_scaffold_v1.py`
- Artifact: `data/control/era52_discipline_layer_minimal_readonly_scaffold_noapi_v1.json`
- Report: `reports/LATEST_ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI.md`
- Boundary: read-only; no DB/panel/service/timer/API/wallet/trade mutation
- Next: `NEWS_RUNTIME_STABILIZATION_AND_CONTINUOUS_PRODUCER_REVIEW`
<!-- ERA52_READONLY_SCAFFOLD_ALMANAC_END -->

<!-- ERA47_PREFLIGHT_CHAIN_ALMANAC_START -->
## ERA47_DISCIPLINE_PREFLIGHT_CHAIN_NOAPI

- Updated UTC: 2026-07-08T10:34:05.417432Z
- Status: CONSOLIDATED
- Parent: `ERA47`
- Substeps: `ERA47A`, `ERA47B`, `ERA47C`, `ERA47D`, `ERA47E`
- Historical aliases: old `ERA48`, `ERA49`, `ERA50`, `ERA51`
- Reason: previous records were one preflight chain, not separate active work lanes.
- Next real software step: `ERA52_DISCIPLINE_LAYER_MINIMAL_READONLY_SCAFFOLD_NOAPI`
- Deadline correction: stop opening micro ERA records; use A/B/C/D inside the active ERA.
<!-- ERA47_PREFLIGHT_CHAIN_ALMANAC_END -->

## ÖNSÖZ - BİR FİKRİN BAŞLANGICI

Bu eser yalnızca bir yazılım projesinin hikâyesini anlatmaz.

Aynı zamanda, sınırlı imkânlarla büyük hedeflerin peşinden gitmeye çalışan sıradan bir insanın yolculuğunu da anlatır.

Bu proje başladığında ben bir yazılım mühendisi değildim.

Üniversite mezunu değildim.

Yüksek lisans yapmamıştım.

Düz lise mezunuydum.

Hayatımı yazılımcı olarak kazanmıyordum.

Tam zamanlı olarak özel bir şirkette, satın alma departmanında çalışıyordum.

Sabah 8 akşam 5 çalışıyor, ardından kalan zamanımı bu projeye ayırıyordum.

Bu yolculuk boyunca çoğu zaman ailemle geçireceğim zamandan fedakârlık ettim.

Bazen uykumdan fedakârlık ettim.

Bazen günün yorgunluğu bitmeden bilgisayarın başına tekrar oturdum.

Çünkü aklımdaki fikrin gerçekleşebileceğine inanıyordum.

Bu projenin arkasında büyük bir yatırım fonu yoktu.

Bir ekip yoktu.

Bir şirket yoktu.

Büyük sermaye yoktu.

Doğru düzgün bir başlangıç bütçesi bile yoktu.

Başlangıçta elimde yalnızca eski bir dizüstü bilgisayar vardı.

O kadar eskiydi ki üzerinde Windows'u bile sağlıklı çalıştıramıyordum.

Linux kullanmayı bilmiyordum.

Buna rağmen araştırarak Lubuntu kurdum.

İlk günlerde her şey yolunda görünüyordu.

Ancak proje büyüdükçe bilgisayar da sınırlarına ulaştı.

Yapay zekâ sohbetleri uzuyor, pencereler ağırlaşıyor, sistem donuyor, terminal cevap veremez hâle geliyordu.

Linux'u da o sırada öğreniyordum.

Karşıma çıkan hemen her problemi ya araştırarak ya da yapay zekâların yardımıyla çözmeye çalışıyordum.

O dönemde ücretsiz yapay zekâ modellerini kullandığım için günlük kullanım kotam çoğu zaman saatler içinde doluyordu.

Çalışmak istesem bile beklemek zorunda kalıyordum.

Bir süre sonra bunun sürdürülebilir olmadığını fark ettim.

Aylık yalnızca birkaç avroya kiralayabildiğim ilk bulut sunucumu kurdum.

Ardından ücretli yapay zekâ modellerini kullanmaya başladım.

Bunlar projenin hızını önemli ölçüde artırdı.

Fakat bu kez başka bir sorun ortaya çıktı.

Sistem büyüdükçe karmaşıklığı da büyüyordu.

Bir noktadan sonra yalnızca bilgisayar değil, ben de yaptığımız her şeyi takip etmekte zorlanmaya başladım.

Yüzlerce faz, onlarca geçiş, sayısız karar ve binlerce satır üretim...

İşte Canonical yapı, Index, Almanac, Atlas ve diğer düzenleme çalışmalarının doğuş nedeni de buydu.

Bu eser yalnızca başarıları anlatmayacak.

Yanlış kararları da anlatacak.

Çöpe atılan mimarileri de anlatacak.

Saatler süren çıkmazları da anlatacak.

Çünkü gerçek ilerleme yalnızca başarıların değil, hataların da dürüstçe kaydedilmesiyle mümkündür.

Eğer bu kitabı yıllar sonra biri okursa, şunu görmesini isterim:

Büyük işler yalnızca büyük bütçelerle yapılmaz.

Bazen bir fikir, sınırlı imkânlar, sabır, disiplin ve vazgeçmemek; en büyük sermaye olabilir.

---


Bu dosya projenin aile bazlı canonical hafıza kitabıdır.

Roadmap yönü gösterir.
Almanac yapılan işleri ve kayıt dosyalarını isimleriyle gösterir.
Atlas mimari bağı gösterir.
Index içerik haritasıdır.
Manifesto doktrindir.

İLK_CANONICAL_DERLEME_UTC=2026-06-29 09:53:06 UTC

---

## KURAL

Almanac ana aileye göre gruplanır.

PASS13A, PASS13B, PASS13C ayrı ana başlık olmaz; PASS13 altında listelenir.

PHASE42A, PHASE42B, PHASE42C ayrı ana başlık olmaz; PHASE42 altında listelenir.

V2_53A, V2_53B, V2_53C ayrı ana başlık olmaz; V2_53 altında listelenir.

Panel görselleri, ikon kaynakları, preview assetleri ve static UI dosyaları Almanac phase/pass kaydı değildir.

---

## PASS ALMANAC - PASS AİLE KAYITLARI

## PASS_SHADOW_AUDIT_READONLY — CANONICAL SHADOW AUDIT READONLY SEAL

İş türü: READ_ONLY_AUDIT

Durum:
- STATUS=PASS
- HEAD=79ca5ce17c46bfdbf551ebc7235520c22f7a4648
- REMOTE_SYNC=PASS
- HARD_FAIL_COUNT=0
- NEXT_SAFE_STEP=USER_APPROVED_NEXT_ERA_OR_POST_SEAL_MAINTENANCE

Kayıt dosyaları:
- data/shadow_audit_readonly_fix1_20260701T103401Z.json

---

### PASS01 — REPO GOVERNANCE POLICY AND MANIFESTO BINDING REAL APPLY

İş türü: REAL_APPLY

Kayıt dosyaları:
- data/repo_governance_pass01_policy_and_manifesto_binding_real_apply.json
- data/repo_governance_pass01_policy_and_manifesto_binding_real_apply_rows.jsonl

---

### PASS02 — REPO GOVERNANCE REORG DRYRUN MANIFEST

İş türü: DRYRUN

Kayıt dosyaları:
- data/repo_governance_pass02_reorg_dryrun_manifest.tsv
- data/repo_governance_pass02_reorg_dryrun_manifest_noapi.json
- data/repo_governance_pass02_reorg_dryrun_manifest_noapi_rows.jsonl
- data/repo_governance_pass02b_reorg_dryrun_manifest_refined.tsv
- data/repo_governance_pass02b_reorg_dryrun_manifest_refined_noapi.json
- data/repo_governance_pass02b_reorg_dryrun_manifest_refined_noapi_rows.jsonl

---

### PASS03 — REPO GOVERNANCE DOCS PHASE REORG REAL APPLY ROWS

İş türü: REAL_APPLY

Kayıt dosyaları:
- data/repo_governance_pass03_docs_phase_reorg_real_apply_manifest.tsv
- data/repo_governance_pass03_docs_phase_reorg_real_apply_rows.jsonl
- data/repo_governance_pass03b_docs_phase_reorg_real_apply_resume.json
- data/repo_governance_pass03b_docs_phase_reorg_real_apply_resume_manifest.tsv
- data/repo_governance_pass03b_docs_phase_reorg_real_apply_resume_rows.jsonl

---

### PASS04 — REPO GOVERNANCE DOCS PHASE REORG POST AUDIT NOAPI

İş türü: AUDIT

Kayıt dosyaları:
- data/repo_governance_pass04_docs_phase_reorg_post_audit_noapi.json
- data/repo_governance_pass04_docs_phase_reorg_post_audit_noapi_rows.jsonl

---

### PASS05 — REPO GOVERNANCE DATA ARCHIVE REORG REAL APPLY

İş türü: REAL_APPLY

Kayıt dosyaları:
- data/repo_governance_pass05_data_archive_reorg_real_apply.json
- data/repo_governance_pass05_data_archive_reorg_real_apply_manifest.tsv
- data/repo_governance_pass05_data_archive_reorg_real_apply_rows.jsonl

---

### PASS06 — REPO GOVERNANCE DATA ARCHIVE REORG POST AUDIT NOAPI

İş türü: AUDIT

Kayıt dosyaları:
- data/repo_governance_pass06_data_archive_reorg_post_audit_noapi.json
- data/repo_governance_pass06_data_archive_reorg_post_audit_noapi_rows.jsonl

---

### PASS07 — REPO GOVERNANCE REMAINING DATA CLASSIFICATION NOAPI

İş türü: KAYIT

Kayıt dosyaları:
- data/repo_governance_pass07_remaining_data_classification_noapi.json
- data/repo_governance_pass07_remaining_data_classification_noapi_rows.jsonl
- data/repo_governance_pass07_remaining_data_classification_report.tsv
- data/repo_governance_pass07b_remaining_data_classification_refined_noapi.json
- data/repo_governance_pass07b_remaining_data_classification_refined_noapi_rows.jsonl

---

### PASS08 — REPO GOVERNANCE CANONICAL DOCS ROOT REORG REAL APPLY

İş türü: REAL_APPLY

Kayıt dosyaları:
- data/repo_governance_pass08_canonical_docs_root_reorg_real_apply.json
- data/repo_governance_pass08_canonical_docs_root_reorg_real_apply_rows.jsonl

---

### PASS09 — REPO GOVERNANCE ROADMAP AND MANIFESTO PHASE LEDGER BINDING REAL APPLY

İş türü: REAL_APPLY

Kayıt dosyaları:
- data/repo_governance_pass09_roadmap_and_manifesto_phase_ledger_binding_real_apply.json
- data/repo_governance_pass09_roadmap_and_manifesto_phase_ledger_binding_real_apply_rows.jsonl

---

### PASS13 — EVIDENCE DICTIONARY PLAN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT

Kayıt dosyaları:
- data/pass13a_evidence_dictionary_plan_noapi.json
- data/pass13aa_evidence_dictionary_coverage_review_noapi.json
- data/pass13b_evidence_dictionary_dryrun_noapi.json
- data/pass13c_evidence_dictionary_apply_plan_noapi.json
- data/pass13d_evidence_dictionary_apply_dryrun_noapi.json
- data/pass13e_evidence_dictionary_post_audit_noapi.json
- data/pass13f_evidence_dictionary_real_apply_plan_noapi.json

---

### PASS14 — DEPLOYER SCHEMA DRYRUN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass14_deployer_intelligence_plan_noapi.json
- data/pass14a_deployer_outcome_taxonomy_audit_noapi.json
- data/pass14b_deployer_evidence_model_plan_noapi.json
- data/pass14c_deployer_evidence_schema_plan_noapi.json
- data/pass14d_deployer_schema_dryrun_noapi.json
- data/pass14e_deployer_schema_post_audit_noapi.json

---

### PASS15 — CONTRACT DNA SCHEMA PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass15_contract_dna_fast_filter_plan_noapi.json
- data/pass15a_contract_dna_evidence_audit_noapi.json
- data/pass15b_contract_dna_evidence_model_plan_noapi.json
- data/pass15c_contract_dna_schema_plan_noapi.json
- data/pass15d_contract_dna_schema_dryrun_noapi.json
- data/pass15e_contract_dna_schema_post_audit_noapi.json

---

### PASS16 — MARKET REGIME PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass16_market_regime_plan_noapi.json
- data/pass16a_market_regime_evidence_audit_noapi.json
- data/pass16b_market_structure_model_plan_noapi.json
- data/pass16c_market_structure_schema_plan_noapi.json
- data/pass16d_market_structure_schema_dryrun_noapi.json
- data/pass16e_market_structure_post_audit_noapi.json

---

### PASS17 — WALLET CLUSTER MODEL PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass17_wallet_cluster_intelligence_plan_noapi.json
- data/pass17a_wallet_cluster_evidence_audit_noapi.json
- data/pass17b_wallet_cluster_model_plan_noapi.json
- data/pass17c_wallet_cluster_schema_plan_noapi.json
- data/pass17d_wallet_cluster_schema_dryrun_noapi.json
- data/pass17e_wallet_cluster_post_audit_noapi.json

---

### PASS18 — TECHNICAL SIGNAL MODEL PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass18_technical_signal_family_plan_noapi.json
- data/pass18a_technical_signal_evidence_audit_noapi.json
- data/pass18b_technical_signal_model_plan_noapi.json
- data/pass18c_technical_signal_schema_plan_noapi.json
- data/pass18d_technical_signal_schema_dryrun_noapi.json
- data/pass18e_technical_signal_post_audit_noapi.json

---

### PASS19 — LEARNING FEEDBACK PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass19_learning_feedback_plan_noapi.json
- data/pass19a_learning_feedback_evidence_audit_noapi.json
- data/pass19b_learning_feedback_model_plan_noapi.json
- data/pass19c_learning_feedback_schema_plan_noapi.json
- data/pass19d_learning_feedback_schema_dryrun_noapi.json
- data/pass19e_learning_feedback_post_audit_noapi.json

---

### PASS20 — DECISION MODEL PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass20_decision_intelligence_plan_noapi.json
- data/pass20a_decision_evidence_audit_noapi.json
- data/pass20b_decision_model_plan_noapi.json
- data/pass20c_decision_schema_plan_noapi.json
- data/pass20d_decision_schema_dryrun_noapi.json
- data/pass20e_decision_post_audit_noapi.json

---

### PASS21 — EXECUTION REALISM PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass21_execution_realism_plan_noapi.json
- data/pass21a_execution_realism_audit_noapi.json
- data/pass21b_execution_realism_model_plan_noapi.json
- data/pass21c_execution_realism_schema_plan_noapi.json
- data/pass21d_execution_realism_schema_dryrun_noapi.json
- data/pass21e_execution_realism_post_audit_noapi.json

---

### PASS22 — POSITION SIZING AUDIT NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass22_position_sizing_intelligence_plan_noapi.json
- data/pass22a_position_sizing_audit_noapi.json
- data/pass22b_position_sizing_model_plan_noapi.json
- data/pass22c_position_sizing_schema_plan_noapi.json
- data/pass22d_position_sizing_schema_dryrun_noapi.json
- data/pass22e_position_sizing_post_audit_noapi.json

---

### PASS23 — PORTFOLIO RISK AUDIT NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass23_portfolio_risk_intelligence_plan_noapi.json
- data/pass23a_portfolio_risk_audit_noapi.json
- data/pass23b_portfolio_risk_model_plan_noapi.json
- data/pass23c_portfolio_risk_schema_plan_noapi.json
- data/pass23d_portfolio_risk_schema_dryrun_noapi.json
- data/pass23e_portfolio_risk_post_audit_noapi.json

---

### PASS24 — LAUNCH MODEL PLAN NOAPI

İş türü: PLAN, AUDIT

Kayıt dosyaları:
- data/pass24_launch_intelligence_plan_noapi.json
- data/pass24a_launch_evidence_audit_noapi.json
- data/pass24b_launch_model_plan_noapi.json

---

### PASS25 — HISTORICAL LAUNCH MODEL PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass25_historical_launch_intelligence_plan_noapi.json
- data/pass25a_historical_launch_evidence_audit_noapi.json
- data/pass25b_historical_launch_model_plan_noapi.json
- data/pass25c_historical_launch_schema_plan_noapi.json
- data/pass25d_historical_launch_schema_dryrun_noapi.json
- data/pass25e_historical_launch_post_audit_noapi.json

---

### PASS26 — LAUNCH OUTCOME MODEL PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/pass26_launch_outcome_intelligence_plan_noapi.json
- data/pass26a_launch_outcome_evidence_audit_noapi.json
- data/pass26b_launch_outcome_model_plan_noapi.json
- data/pass26c_launch_outcome_schema_plan_noapi.json
- data/pass26d_launch_outcome_schema_dryrun_noapi.json
- data/pass26e_launch_outcome_post_audit_noapi.json

---

### PASS27 — ENGINE CONSOLIDATION LOCK NOAPI

İş türü: PLAN, DRYRUN, AUDIT

Kayıt dosyaları:
- data/pass27_engine_consolidation_lock_noapi.json
- data/pass27a_execution_accounting_and_pnl_ledger_plan_noapi.json
- data/pass27b_execution_accounting_and_pnl_ledger_dryrun_noapi.json
- data/pass27c_execution_accounting_and_pnl_ledger_post_audit_noapi.json
- data/pass27d_execution_accounting_and_pnl_ledger_acceptance_noapi.json

---

## PHASE ALMANAC - PHASE AİLE KAYITLARI

### PHASE3 — HANDOFF AND STRATEGY REVIEW NOAPI

İş türü: PLAN, REAL_APPLY, AUDIT, CLOSE, SCHEMA

Kayıt dosyaları:
- data/archive/phases/phase3/phase3_active_8096_listener_status_review_noapi.json
- data/archive/phases/phase3/phase3_checkpoint_row_audit_mapping_review_noapi.json
- data/archive/phases/phase3/phase3_close_current_targets_and_phase3_status_review_noapi.json
- data/archive/phases/phase3/phase3_close_current_targets_and_phase3_status_review_retry_after_row_mapping_noapi.json
- data/archive/phases/phase3/phase3_evidence3i_scan_provider_recovery_review_noapi.json
- data/archive/phases/phase3/phase3_evidence3j_alchemy_rpc_indexer_path_plan_noapi.json
- data/archive/phases/phase3/phase3_evidence3k1_rpc_config_source_review_noapi.json
- data/archive/phases/phase3/phase3_evidence3k_alchemy_rpc_indexer_discovery_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_evidence3k_alchemy_rpc_indexer_discovery_real_retry_after_explicit_approval.json
- data/archive/phases/phase3/phase3_evidence3l_alchemy_rpc_indexer_discovery_review_noapi.json
- data/archive/phases/phase3/phase3_evidence3m_getlogs_strategy_repair_plan_noapi.json
- data/archive/phases/phase3/phase3_evidence3n_getlogs_repair_smoke_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_evidence3o_rpc_provider_fallback_plan_noapi.json
- data/archive/phases/phase3/phase3_evidence3p_rpc_provider_fallback_smoke_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_evidence3q_bounded_deployer_log_discovery_plan_noapi.json
- data/archive/phases/phase3/phase3_evidence3r_bounded_deployer_log_discovery_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_evidence3t_deployer_provider_limit_review_noapi.json
- data/archive/phases/phase3/phase3_evidence3u_adaptive_bounded_deployer_chunk_plan_noapi.json
- data/archive/phases/phase3/phase3_evidence3v_adaptive_bounded_deployer_chunk_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_evidence3w_deployer_unresolved_route_review_noapi.json
- data/archive/phases/phase3/phase3_evidence3x_deployer_unresolved_ghost_decision_staging_plan_noapi.json
- data/archive/phases/phase3/phase3_evidence3y1_ghost_staging_schema_mapping_review_noapi.json
- data/archive/phases/phase3/phase3_evidence3y2_deployer_unresolved_ghost_staging_real_retry_after_schema_mapping.json
- data/archive/phases/phase3/phase3_evidence3y_deployer_unresolved_ghost_staging_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_evidence3z_deployer_unresolved_ghost_staging_post_audit_noapi.json
- data/archive/phases/phase3/phase3_evidence4_or_phase3_close_decision_plan_noapi.json
- data/archive/phases/phase3/phase3_handoff_and_strategy_review_noapi.json
- data/archive/phases/phase3/phase3_target2_adaptive_bounded_deployer_chunk_plan_noapi.json
- data/archive/phases/phase3/phase3_target2_adaptive_bounded_deployer_chunk_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target2_adaptive_bounded_deployer_chunk_review_noapi.json
- data/archive/phases/phase3/phase3_target2_candidate_selection_plan_noapi.json
- data/archive/phases/phase3/phase3_target2_deployer_discovery_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target2_deployer_discovery_review_noapi.json
- data/archive/phases/phase3/phase3_target2_deployer_source_plan_noapi.json
- data/archive/phases/phase3/phase3_target2_deployer_unresolved_ghost_decision_staging_plan_noapi.json
- data/archive/phases/phase3/phase3_target2_deployer_unresolved_ghost_staging_post_audit_noapi.json
- data/archive/phases/phase3/phase3_target2_deployer_unresolved_ghost_staging_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target2_deployer_unresolved_ghost_staging_real_retry_after_sha_review.json
- data/archive/phases/phase3/phase3_target2_ghost_staging_payload_sha_review_noapi.json
- data/archive/phases/phase3/phase3_target2_route_close_or_target3_selection_plan_noapi.json
- data/archive/phases/phase3/phase3_target3_adaptive_bounded_deployer_chunk_plan_noapi.json
- data/archive/phases/phase3/phase3_target3_adaptive_bounded_deployer_chunk_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target3_adaptive_bounded_deployer_chunk_review_noapi.json
- data/archive/phases/phase3/phase3_target3_candidate_selection_plan_noapi.json
- data/archive/phases/phase3/phase3_target3_deployer_discovery_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target3_deployer_discovery_review_noapi.json
- data/archive/phases/phase3/phase3_target3_deployer_source_plan_noapi.json
- data/archive/phases/phase3/phase3_target3_deployer_unresolved_ghost_decision_staging_plan_noapi.json
- data/archive/phases/phase3/phase3_target3_deployer_unresolved_ghost_staging_post_audit_noapi.json
- data/archive/phases/phase3/phase3_target3_deployer_unresolved_ghost_staging_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target3_route_close_or_phase3_status_review_noapi.json
- data/archive/phases/phase3/phase3_target4_adaptive_bounded_deployer_chunk_plan_noapi.json
- data/archive/phases/phase3/phase3_target4_adaptive_bounded_deployer_chunk_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target4_adaptive_bounded_deployer_chunk_review_noapi.json
- data/archive/phases/phase3/phase3_target4_candidate_selection_plan_noapi.json
- data/archive/phases/phase3/phase3_target4_deployer_discovery_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target4_deployer_discovery_review_noapi.json
- data/archive/phases/phase3/phase3_target4_deployer_source_plan_noapi.json
- data/archive/phases/phase3/phase3_target4_deployer_unresolved_ghost_decision_staging_plan_noapi.json
- data/archive/phases/phase3/phase3_target4_deployer_unresolved_ghost_staging_post_audit_noapi.json
- data/archive/phases/phase3/phase3_target4_deployer_unresolved_ghost_staging_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target4_route_close_or_target5_selection_plan_noapi.json
- data/archive/phases/phase3/phase3_target5_adaptive_bounded_deployer_chunk_plan_noapi.json
- data/archive/phases/phase3/phase3_target5_adaptive_bounded_deployer_chunk_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target5_adaptive_bounded_deployer_chunk_review_noapi.json
- data/archive/phases/phase3/phase3_target5_candidate_selection_plan_noapi.json
- data/archive/phases/phase3/phase3_target5_deployer_discovery_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target5_deployer_discovery_real_key_alias_rerun_plan_noapi.json
- data/archive/phases/phase3/phase3_target5_deployer_discovery_real_rerun_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target5_deployer_discovery_rerun_review_noapi.json
- data/archive/phases/phase3/phase3_target5_deployer_source_plan_noapi.json
- data/archive/phases/phase3/phase3_target5_deployer_unresolved_ghost_decision_staging_plan_noapi.json
- data/archive/phases/phase3/phase3_target5_deployer_unresolved_ghost_staging_post_audit_noapi.json
- data/archive/phases/phase3/phase3_target5_deployer_unresolved_ghost_staging_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target5_discovery_real_false_fail_review_noapi.json
- data/archive/phases/phase3/phase3_target5_false_fail_artifact_cleanup_plan_noapi.json
- data/archive/phases/phase3/phase3_target5_route_close_or_target6_selection_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_alchemy_payg_capability_recheck_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_alchemy_payg_capability_recheck_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_alchemy_payg_capability_recheck_real_after_payg_activation.json
- data/archive/phases/phase3/phase3_target6_alchemy_payg_key_replace_and_capability_recheck_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_alt_base_provider_source_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_base_rpc_hosts_override_repair_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_base_rpc_hosts_override_repair_post_audit_noapi.json
- data/archive/phases/phase3/phase3_target6_base_rpc_hosts_override_repair_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_base_rpc_hosts_override_review_noapi.json
- data/archive/phases/phase3/phase3_target6_base_rpc_server_tls_diag_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_base_rpc_server_tls_diag_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_base_rpc_source_locator_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_base_rpc_source_repair_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_base_rpc_source_repair_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_base_rpc_source_setup_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_base_rpc_source_setup_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_base_rpc_ssl_host_review_noapi.json
- data/archive/phases/phase3/phase3_target6_base_rpc_tls_smoke_plan_after_hosts_repair_noapi.json
- data/archive/phases/phase3/phase3_target6_base_rpc_tls_smoke_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_candidate_selection_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_deployer_discovery_payg_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_deployer_discovery_payg_replan_noapi.json
- data/archive/phases/phase3/phase3_target6_deployer_discovery_payg_review_noapi.json
- data/archive/phases/phase3/phase3_target6_deployer_discovery_real_after_base_rpc_tls_smoke_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_deployer_discovery_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_deployer_source_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_deployer_source_plan_retry_after_base_rpc_setup_noapi.json
- data/archive/phases/phase3/phase3_target6_deployer_source_plan_retry_after_base_rpc_tls_smoke_noapi.json
- data/archive/phases/phase3/phase3_target6_getlogs_10_block_micro_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_getlogs_10_block_micro_review_noapi.json
- data/archive/phases/phase3/phase3_target6_getlogs_http400_body_capture_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_getlogs_http400_body_capture_real_after_explicit_approval.json
- data/archive/phases/phase3/phase3_target6_getlogs_http400_body_capture_review_noapi.json
- data/archive/phases/phase3/phase3_target6_getlogs_http400_review_noapi.json
- data/archive/phases/phase3/phase3_target6_getlogs_range_limit_strategy_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_payg_bounded_empty_close_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_payg_bounded_empty_route_decision_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_provider_limited_route_close_plan_noapi.json
- data/archive/phases/phase3/phase3_target6_provider_limited_route_decision_plan_noapi.json
- data/phase3_evidence3j_alchemy_rpc_indexer_path_plan_noapi_rows.jsonl
- data/phase3_evidence3y2_deployer_unresolved_ghost_staging_real_retry_after_schema_mapping_rows.jsonl
- data/phase3_evidence3y_deployer_unresolved_ghost_staging_real_after_explicit_approval_rows.jsonl
- data/phase3_target2_deployer_unresolved_ghost_staging_real_after_explicit_approval_rows.jsonl
- data/phase3_target2_deployer_unresolved_ghost_staging_real_retry_after_sha_review_rows.jsonl
- data/phase3_target3_deployer_unresolved_ghost_staging_real_after_explicit_approval_rows.jsonl
- data/phase3_target4_deployer_unresolved_ghost_staging_real_after_explicit_approval_rows.jsonl
- data/phase3_target5_deployer_unresolved_ghost_staging_real_after_explicit_approval_rows.jsonl
- data/phase3_target6_alchemy_payg_capability_recheck_real_after_explicit_approval_rows.jsonl
- data/phase3_target6_alchemy_payg_capability_recheck_real_after_payg_activation_rows.jsonl
- data/phase3_target6_alchemy_payg_key_replace_and_capability_recheck_real_after_explicit_approval_rows.jsonl
- data/phase3_target6_base_rpc_hosts_override_repair_real_after_explicit_approval_rows.jsonl
- data/phase3_target6_base_rpc_server_tls_diag_real_after_explicit_approval_rows.jsonl
- data/phase3_target6_base_rpc_source_repair_real_after_explicit_approval_rows.jsonl
- data/phase3_target6_base_rpc_tls_smoke_real_after_explicit_approval_rows.jsonl
- data/phase3_target6_deployer_discovery_payg_real_after_explicit_approval_rows.jsonl
- data/phase3_target6_deployer_discovery_real_after_base_rpc_tls_smoke_explicit_approval_rows.jsonl
- data/phase3_target6_getlogs_10_block_micro_real_after_explicit_approval_rows.jsonl
- data/phase3_target6_getlogs_http400_body_capture_real_after_explicit_approval_rows.jsonl

---

### PHASE4 — FINAL REVIEW NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase4/phase4_backlog_priority_and_gated_evidence_plan_noapi.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_dryrun_noapi.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_plan_noapi.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_review_noapi.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_slice2_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_slice2_dryrun_noapi.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_slice2_plan_noapi.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_slice2_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_slice2_real_rerun_prereq_reader_fix_after_explicit_approval.json
- data/archive/phases/phase4/phase4_bsc_base_evidence_backfill_slice2_review_noapi.json
- data/archive/phases/phase4/phase4_deep_risk_code_shape_quality_review_noapi.json
- data/archive/phases/phase4/phase4_deep_risk_evidence_backfill_plan_noapi.json
- data/archive/phases/phase4/phase4_deployer_creation_tx_receipt_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_deployer_creation_tx_receipt_dryrun_noapi.json
- data/archive/phases/phase4/phase4_deployer_creation_tx_receipt_plan_noapi.json
- data/archive/phases/phase4/phase4_deployer_creation_tx_receipt_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_deployer_creation_tx_receipt_review_fix_noapi.json
- data/archive/phases/phase4/phase4_deployer_creation_tx_receipt_review_noapi.json
- data/archive/phases/phase4/phase4_deployer_initial_holder_bounded_evidence_plan_noapi.json
- data/archive/phases/phase4/phase4_entry_decision_and_backlog_plan_noapi.json
- data/archive/phases/phase4/phase4_evidence_gap_and_next_backfill_decision_plan_noapi.json
- data/archive/phases/phase4/phase4_final_review_noapi.json
- data/archive/phases/phase4/phase4_guarded_rpc_shape_smoke_dryrun_noapi.json
- data/archive/phases/phase4/phase4_guarded_rpc_shape_smoke_plan_noapi.json
- data/archive/phases/phase4/phase4_guarded_rpc_shape_smoke_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_guarded_rpc_shape_smoke_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch1_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch2_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch2_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch2_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch2_provider_or_batch_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch2_provider_or_batch_review_repair_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch2_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch2_real_retry_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch2_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_review_repair2_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_review_repair_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_provider_or_batch_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch3_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch4_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch4_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch4_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch4_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch4_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch5_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch5_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch5_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch5_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch5_real_approval_hash_reclassify_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch5_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_failed_getlogs_split_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_failed_getlogs_split_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_failed_getlogs_split_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_failed_getlogs_split_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_failed_getlogs_split_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_provider_or_batch_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch6_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch7_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch7_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch7_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch7_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch7_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch8_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch8_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch8_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch8_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_batch8_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_failed_getlogs_split_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_failed_getlogs_split_dryrun_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_failed_getlogs_split_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_failed_getlogs_split_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_failed_getlogs_split_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_plan_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_provider_or_batch_review_noapi.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_initial_holder_transfer_mint_scan_review_noapi.json
- data/archive/phases/phase4/phase4_pair_address_shape_and_pair_code_backfill_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_pair_address_shape_and_pair_code_backfill_dryrun_noapi.json
- data/archive/phases/phase4/phase4_pair_address_shape_and_pair_code_backfill_plan_noapi.json
- data/archive/phases/phase4/phase4_pair_address_shape_and_pair_code_backfill_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_pair_address_shape_and_pair_code_backfill_review_noapi.json
- data/archive/phases/phase4/phase4_pair_code_backfill_slice2_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_pair_code_backfill_slice2_dryrun_noapi.json
- data/archive/phases/phase4/phase4_pair_code_backfill_slice2_plan_noapi.json
- data/archive/phases/phase4/phase4_pair_code_backfill_slice2_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_pair_code_backfill_slice2_review_noapi.json
- data/archive/phases/phase4/phase4_pair_created_at_timestamp_anchor_fallback_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_pair_created_at_timestamp_anchor_fallback_apply_plan_repair_noapi.json
- data/archive/phases/phase4/phase4_pair_created_at_timestamp_anchor_fallback_dryrun_noapi.json
- data/archive/phases/phase4/phase4_pair_created_at_timestamp_anchor_fallback_plan_noapi.json
- data/archive/phases/phase4/phase4_pair_created_at_timestamp_anchor_fallback_plan_repair_noapi.json
- data/archive/phases/phase4/phase4_pair_created_at_timestamp_anchor_fallback_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_pair_created_at_timestamp_anchor_fallback_review_noapi.json
- data/archive/phases/phase4/phase4_payg_rpc_budget_guard_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_payg_rpc_budget_guard_dryrun_noapi.json
- data/archive/phases/phase4/phase4_payg_rpc_budget_guard_plan_noapi.json
- data/archive/phases/phase4/phase4_payg_rpc_budget_guard_post_audit_noapi.json
- data/archive/phases/phase4/phase4_payg_rpc_budget_guard_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_risk_evidence_input_matrix_plan_noapi.json
- data/archive/phases/phase4/phase4_rpc_guard_eth_getblockbynumber_policy_expansion_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_rpc_guard_eth_getblockbynumber_policy_expansion_dryrun_noapi.json
- data/archive/phases/phase4/phase4_rpc_guard_eth_getblockbynumber_policy_expansion_plan_noapi.json
- data/archive/phases/phase4/phase4_rpc_guard_eth_getblockbynumber_policy_expansion_post_audit_noapi.json
- data/archive/phases/phase4/phase4_rpc_guard_eth_getblockbynumber_policy_expansion_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_timestamp_to_block_bounded_conversion_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_timestamp_to_block_bounded_conversion_dryrun_noapi.json
- data/archive/phases/phase4/phase4_timestamp_to_block_bounded_conversion_plan_noapi.json
- data/archive/phases/phase4/phase4_timestamp_to_block_bounded_conversion_provider_or_policy_review_noapi.json
- data/archive/phases/phase4/phase4_timestamp_to_block_bounded_conversion_real_after_explicit_approval.json
- data/archive/phases/phase4/phase4_timestamp_to_block_bounded_conversion_repair_apply_plan_noapi.json
- data/archive/phases/phase4/phase4_timestamp_to_block_bounded_conversion_repair_dryrun_noapi.json
- data/archive/phases/phase4/phase4_timestamp_to_block_bounded_conversion_repair_plan_noapi.json
- data/archive/phases/phase4/phase4_timestamp_to_block_bounded_conversion_repair_provider_review_noapi.json
- data/archive/phases/phase4/phase4_timestamp_to_block_bounded_conversion_repair_real_after_explicit_approval.json
- data/phase4_backlog_priority_and_gated_evidence_plan_noapi_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_apply_plan_noapi_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_dryrun_noapi_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_plan_noapi_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_real_after_explicit_approval_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_review_noapi_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_slice2_apply_plan_noapi_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_slice2_dryrun_noapi_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_slice2_plan_noapi_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_slice2_real_after_explicit_approval_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_slice2_real_rerun_prereq_reader_fix_after_explicit_approval_rows.jsonl
- data/phase4_bsc_base_evidence_backfill_slice2_review_noapi_rows.jsonl
- data/phase4_deep_risk_code_shape_quality_review_noapi_rows.jsonl
- data/phase4_deep_risk_evidence_backfill_plan_noapi_rows.jsonl
- data/phase4_deployer_creation_tx_receipt_apply_plan_noapi_rows.jsonl
- data/phase4_deployer_creation_tx_receipt_dryrun_noapi_rows.jsonl
- data/phase4_deployer_creation_tx_receipt_plan_noapi_rows.jsonl
- data/phase4_deployer_creation_tx_receipt_real_after_explicit_approval_rows.jsonl
- data/phase4_deployer_creation_tx_receipt_review_fix_noapi_rows.jsonl
- data/phase4_deployer_creation_tx_receipt_review_noapi_rows.jsonl
- data/phase4_deployer_initial_holder_bounded_evidence_plan_noapi_rows.jsonl
- data/phase4_entry_decision_and_backlog_plan_noapi_rows.jsonl
- data/phase4_evidence_gap_and_next_backfill_decision_plan_noapi_rows.jsonl
- data/phase4_final_review_noapi_rows.jsonl
- data/phase4_guarded_rpc_shape_smoke_dryrun_noapi_rows.jsonl
- data/phase4_guarded_rpc_shape_smoke_plan_noapi_rows.jsonl
- data/phase4_guarded_rpc_shape_smoke_real_after_explicit_approval_rows.jsonl
- data/phase4_guarded_rpc_shape_smoke_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch1_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch2_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch2_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch2_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch2_provider_or_batch_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch2_provider_or_batch_review_repair_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch2_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch2_real_retry_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch2_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_review_repair2_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_failed_getlogs_split_review_repair_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_provider_or_batch_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch3_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch4_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch4_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch4_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch4_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch4_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch5_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch5_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch5_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch5_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch5_real_approval_hash_reclassify_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch5_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_failed_getlogs_split_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_failed_getlogs_split_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_failed_getlogs_split_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_failed_getlogs_split_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_failed_getlogs_split_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_provider_or_batch_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch6_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch7_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch7_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch7_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch7_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch7_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch8_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch8_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch8_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch8_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_batch8_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_failed_getlogs_split_apply_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_failed_getlogs_split_dryrun_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_failed_getlogs_split_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_failed_getlogs_split_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_failed_getlogs_split_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_plan_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_provider_or_batch_review_noapi_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_real_after_explicit_approval_rows.jsonl
- data/phase4_initial_holder_transfer_mint_scan_review_noapi_rows.jsonl
- data/phase4_pair_address_shape_and_pair_code_backfill_apply_plan_noapi_rows.jsonl
- data/phase4_pair_address_shape_and_pair_code_backfill_dryrun_noapi_rows.jsonl
- data/phase4_pair_address_shape_and_pair_code_backfill_plan_noapi_rows.jsonl
- data/phase4_pair_address_shape_and_pair_code_backfill_real_after_explicit_approval_rows.jsonl
- data/phase4_pair_address_shape_and_pair_code_backfill_review_noapi_rows.jsonl
- data/phase4_pair_code_backfill_slice2_apply_plan_noapi_rows.jsonl
- data/phase4_pair_code_backfill_slice2_dryrun_noapi_rows.jsonl
- data/phase4_pair_code_backfill_slice2_plan_noapi_rows.jsonl
- data/phase4_pair_code_backfill_slice2_real_after_explicit_approval_rows.jsonl
- data/phase4_pair_code_backfill_slice2_review_noapi_rows.jsonl
- data/phase4_pair_created_at_timestamp_anchor_fallback_apply_plan_noapi_rows.jsonl
- data/phase4_pair_created_at_timestamp_anchor_fallback_apply_plan_repair_noapi_rows.jsonl
- data/phase4_pair_created_at_timestamp_anchor_fallback_dryrun_noapi_rows.jsonl
- data/phase4_pair_created_at_timestamp_anchor_fallback_plan_noapi_rows.jsonl
- data/phase4_pair_created_at_timestamp_anchor_fallback_plan_repair_noapi_rows.jsonl
- data/phase4_pair_created_at_timestamp_anchor_fallback_real_after_explicit_approval_rows.jsonl
- data/phase4_pair_created_at_timestamp_anchor_fallback_review_noapi_rows.jsonl
- data/phase4_payg_rpc_budget_guard_post_audit_noapi_rows.jsonl
- data/phase4_payg_rpc_budget_guard_real_after_explicit_approval_rows.jsonl
- data/phase4_risk_evidence_input_matrix_plan_noapi_rows.jsonl
- data/phase4_rpc_guard_eth_getblockbynumber_policy_expansion_apply_plan_noapi_rows.jsonl
- data/phase4_rpc_guard_eth_getblockbynumber_policy_expansion_dryrun_noapi_rows.jsonl
- data/phase4_rpc_guard_eth_getblockbynumber_policy_expansion_plan_noapi_rows.jsonl
- data/phase4_rpc_guard_eth_getblockbynumber_policy_expansion_post_audit_noapi_rows.jsonl
- data/phase4_rpc_guard_eth_getblockbynumber_policy_expansion_real_after_explicit_approval_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_apply_plan_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_dryrun_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_plan_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_provider_or_policy_review_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_real_after_explicit_approval_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_apply_plan_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_dryrun_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_plan_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_provider_review_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_real_after_explicit_approval_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_real_retry_after_explicit_approval.json
- data/phase4_timestamp_to_block_bounded_conversion_repair_real_retry_after_explicit_approval_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_review_noapi.json
- data/phase4_timestamp_to_block_bounded_conversion_repair_review_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_apply_plan_noapi.json
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_apply_plan_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_dryrun_noapi.json
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_dryrun_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_plan_noapi.json
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_plan_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_real_after_explicit_approval.json
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_real_after_explicit_approval_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_review_noapi.json
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_review_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_review_repair_noapi.json
- data/phase4_timestamp_to_block_bounded_conversion_repair_slice2_review_repair_noapi_rows.jsonl
- data/phase4_timestamp_to_block_bounded_conversion_review_noapi.json
- data/phase4_timestamp_to_block_bounded_conversion_review_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_contract_creation_source_apply_plan_noapi.json
- data/phase4_token_birth_block_anchor_contract_creation_source_apply_plan_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_contract_creation_source_artifact_sanitize_plan_noapi.json
- data/phase4_token_birth_block_anchor_contract_creation_source_artifact_sanitize_plan_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_contract_creation_source_artifact_sanitize_real_after_explicit_approval.json
- data/phase4_token_birth_block_anchor_contract_creation_source_artifact_sanitize_real_after_explicit_approval_rows.jsonl
- data/phase4_token_birth_block_anchor_contract_creation_source_artifact_sanitize_review_noapi.json
- data/phase4_token_birth_block_anchor_contract_creation_source_artifact_sanitize_review_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_contract_creation_source_dryrun_noapi.json
- data/phase4_token_birth_block_anchor_contract_creation_source_dryrun_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_contract_creation_source_fallback_plan_noapi.json
- data/phase4_token_birth_block_anchor_contract_creation_source_fallback_plan_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_contract_creation_source_plan_noapi.json
- data/phase4_token_birth_block_anchor_contract_creation_source_plan_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_contract_creation_source_provider_error_review_noapi.json
- data/phase4_token_birth_block_anchor_contract_creation_source_provider_error_review_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_contract_creation_source_real_after_explicit_approval.json
- data/phase4_token_birth_block_anchor_contract_creation_source_real_after_explicit_approval_rows.jsonl
- data/phase4_token_birth_block_anchor_local_artifact_review_noapi.json
- data/phase4_token_birth_block_anchor_local_artifact_review_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_source_decision_plan_noapi.json
- data/phase4_token_birth_block_anchor_source_decision_plan_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_source_decision_plan_repair_noapi.json
- data/phase4_token_birth_block_anchor_source_decision_plan_repair_noapi_rows.jsonl
- data/phase4_token_birth_block_anchor_source_plan_noapi.json
- data/phase4_token_birth_block_anchor_source_plan_noapi_rows.jsonl

---

### PHASE5 — SCHEMA APPLY PLAN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, SCHEMA

Kayıt dosyaları:
- data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json
- data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi_rows.jsonl
- data/phase5a_receipt_creation_proof_field_diagnose_noapi.json
- data/phase5b_time_series_schema_gap_plan_noapi.json
- data/phase5b_time_series_schema_gap_plan_noapi_rows.jsonl
- data/phase5c2_cascading_execution_filter_plan_noapi.json
- data/phase5c2_cascading_execution_filter_plan_noapi_rows.jsonl
- data/phase5c_execution_safety_and_micro_route_plan_noapi.json
- data/phase5c_execution_safety_and_micro_route_plan_noapi_rows.jsonl
- data/phase5d_outcome_memory_skeleton_plan_noapi.json
- data/phase5d_outcome_memory_skeleton_plan_noapi_rows.jsonl
- data/phase5e1_schema_temp_dryrun_failure_diagnose_noapi.json
- data/phase5e2_schema_canonical_temp_dryrun_repair_noapi.json
- data/phase5e2_schema_canonical_temp_dryrun_repair_noapi_rows.jsonl
- data/phase5e_schema_temp_db_dryrun_noapi.json
- data/phase5e_schema_temp_db_dryrun_noapi_rows.jsonl
- data/phase5f1_skipped_index_and_canonical_sql_review_noapi.json
- data/phase5f1_skipped_index_and_canonical_sql_review_noapi_rows.jsonl
- data/phase5f_schema_apply_plan_noapi.json
- data/phase5f_schema_apply_plan_noapi_rows.jsonl
- data/phase5g1_schema_apply_count_diff_classify_noapi.json
- data/phase5g1_schema_apply_count_diff_classify_noapi_rows.jsonl
- data/phase5g_schema_apply_real_after_explicit_approval.json
- data/phase5g_schema_apply_real_after_explicit_approval_rows.jsonl
- data/phase5h_schema_apply_post_audit_noapi.json
- data/phase5h_schema_apply_post_audit_noapi_rows.jsonl
- data/phase5i1_backfill_plan_failure_diagnose_noapi.json
- data/phase5i1_backfill_plan_failure_diagnose_noapi_rows.jsonl
- data/phase5i2_evidence_backfill_plan_repair_noapi.json
- data/phase5i2_evidence_backfill_plan_repair_noapi_rows.jsonl
- data/phase5i_evidence_backfill_plan_noapi.json
- data/phase5i_evidence_backfill_plan_noapi_rows.jsonl
- data/phase5j1_evidence_backfill_real_readiness_noapi.json
- data/phase5j1_evidence_backfill_real_readiness_noapi_rows.jsonl
- data/phase5j_evidence_backfill_dryrun_noapi.json
- data/phase5j_evidence_backfill_dryrun_noapi_rows.jsonl
- data/phase5k_evidence_backfill_real_after_explicit_approval.json
- data/phase5k_evidence_backfill_real_after_explicit_approval_rows.jsonl
- data/phase5l1_paper_live_clean_false_diagnose_noapi.json
- data/phase5l1_paper_live_clean_false_diagnose_noapi_rows.jsonl
- data/phase5l2_evidence_backfill_post_audit_repair_noapi.json
- data/phase5l2_evidence_backfill_post_audit_repair_noapi_rows.jsonl
- data/phase5l_evidence_backfill_post_audit_noapi.json
- data/phase5l_evidence_backfill_post_audit_noapi_rows.jsonl
- data/phase5m1_final_review_gate_failure_diagnose_noapi.json
- data/phase5m1_final_review_gate_failure_diagnose_noapi_rows.jsonl
- data/phase5m2_phase5_final_review_repair_noapi.json
- data/phase5m2_phase5_final_review_repair_noapi_rows.jsonl
- data/phase5m_phase5_final_review_noapi.json
- data/phase5m_phase5_final_review_noapi_rows.jsonl

---

### PHASE6 — PHASE6 FINAL REVIEW NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, SCHEMA

Kayıt dosyaları:
- data/phase6_evidence_readmodel_and_decision_binding_plan_noapi.json
- data/phase6_evidence_readmodel_and_decision_binding_plan_noapi_rows.jsonl
- data/phase6a_sqlite_wal_and_write_pressure_readiness_plan_noapi.json
- data/phase6a_sqlite_wal_and_write_pressure_readiness_plan_noapi_rows.jsonl
- data/phase6b2_stale_data_guard_plan_noapi.json
- data/phase6b2_stale_data_guard_plan_noapi_rows.jsonl
- data/phase6b_state_aggregated_readmodel_schema_gap_plan_noapi.json
- data/phase6b_state_aggregated_readmodel_schema_gap_plan_noapi_rows.jsonl
- data/phase6c2_asymmetric_speculative_micro_route_policy_plan_noapi.json
- data/phase6c2_asymmetric_speculative_micro_route_policy_plan_noapi_rows.jsonl
- data/phase6c3_dex_microstructure_technical_evidence_plan_noapi.json
- data/phase6c3_dex_microstructure_technical_evidence_plan_noapi_rows.jsonl
- data/phase6c4_emergency_monitor_trigger_loop_plan_noapi.json
- data/phase6c4_emergency_monitor_trigger_loop_plan_noapi_rows.jsonl
- data/phase6c_execution_threshold_matrix_plan_noapi.json
- data/phase6c_execution_threshold_matrix_plan_noapi_rows.jsonl
- data/phase6d_negative_memory_lookup_plan_noapi.json
- data/phase6d_negative_memory_lookup_plan_noapi_rows.jsonl
- data/phase6e_decision_binding_rule_matrix_noapi.json
- data/phase6e_decision_binding_rule_matrix_noapi_rows.jsonl
- data/phase6f1_command_output_permission_sentence_repair_noapi.json
- data/phase6f1_command_output_permission_sentence_repair_noapi_rows.jsonl
- data/phase6f2_command_output_permission_sentence_repair_strict_noapi.json
- data/phase6f2_command_output_permission_sentence_repair_strict_noapi_rows.jsonl
- data/phase6f3_command_output_permission_sentence_repair_normalized_check_noapi.json
- data/phase6f3_command_output_permission_sentence_repair_normalized_check_noapi_rows.jsonl
- data/phase6f_command_center_output_contract_plan_noapi.json
- data/phase6f_command_center_output_contract_plan_noapi_rows.jsonl
- data/phase6g1_readmodel_temp_dryrun_failure_diagnose_noapi.json
- data/phase6g1_readmodel_temp_dryrun_failure_diagnose_noapi_rows.jsonl
- data/phase6g2_canonical_temp_dryrun_repair_noapi.json
- data/phase6g2_canonical_temp_dryrun_repair_noapi_rows.jsonl
- data/phase6g3_canonical_temp_dryrun_failure_diagnose_noapi.json
- data/phase6g3_canonical_temp_dryrun_failure_diagnose_noapi_rows.jsonl
- data/phase6g4_base_readmodel_table_sql_repair_temp_dryrun_noapi.json
- data/phase6g4_base_readmodel_table_sql_repair_temp_dryrun_noapi_rows.jsonl
- data/phase6g_readmodel_temp_db_dryrun_noapi.json
- data/phase6g_readmodel_temp_db_dryrun_noapi_rows.jsonl
- data/phase6h_readmodel_apply_plan_noapi.json
- data/phase6h_readmodel_apply_plan_noapi_rows.jsonl
- data/phase6i_readmodel_real_after_explicit_approval.json
- data/phase6i_readmodel_real_after_explicit_approval_rows.jsonl
- data/phase6j_readmodel_post_audit_noapi.json
- data/phase6j_readmodel_post_audit_noapi_rows.jsonl
- data/phase6k_phase6_final_review_noapi.json
- data/phase6k_phase6_final_review_noapi_rows.jsonl

---

### PHASE7 — PHASE7 FINAL REVIEW NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT

Kayıt dosyaları:
- data/phase7_readmodel_seed_and_binding_plan_noapi.json
- data/phase7_readmodel_seed_and_binding_plan_noapi_rows.jsonl
- data/phase7a_readmodel_seed_temp_dryrun_noapi.json
- data/phase7a_readmodel_seed_temp_dryrun_noapi_rows.jsonl
- data/phase7b_readmodel_seed_apply_plan_noapi.json
- data/phase7b_readmodel_seed_apply_plan_noapi_rows.jsonl
- data/phase7c_readmodel_seed_real_after_explicit_approval.json
- data/phase7c_readmodel_seed_real_after_explicit_approval_rows.jsonl
- data/phase7d_readmodel_seed_post_audit_noapi.json
- data/phase7d_readmodel_seed_post_audit_noapi_rows.jsonl
- data/phase7e_decision_binding_dryrun_noapi.json
- data/phase7e_decision_binding_dryrun_noapi_rows.jsonl
- data/phase7f_command_output_dryrun_noapi.json
- data/phase7f_command_output_dryrun_noapi_rows.jsonl
- data/phase7g_phase7_final_review_noapi.json
- data/phase7g_phase7_final_review_noapi_rows.jsonl

---

### PHASE8 — PHASE8 FINAL REVIEW NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, SCHEMA

Kayıt dosyaları:
- data/phase8_commercial_roi_and_opportunity_capture_plan_noapi.json
- data/phase8_commercial_roi_and_opportunity_capture_plan_noapi_rows.jsonl
- data/phase8a_missed_opportunity_audit_schema_plan_noapi.json
- data/phase8a_missed_opportunity_audit_schema_plan_noapi_rows.jsonl
- data/phase8b_risk_tier_capital_policy_plan_noapi.json
- data/phase8b_risk_tier_capital_policy_plan_noapi_rows.jsonl
- data/phase8c_asymmetric_micro_route_observation_plan_noapi.json
- data/phase8c_asymmetric_micro_route_observation_plan_noapi_rows.jsonl
- data/phase8d_cost_recovery_scoreboard_plan_noapi.json
- data/phase8d_cost_recovery_scoreboard_plan_noapi_rows.jsonl
- data/phase8e_phase8_final_review_noapi.json
- data/phase8e_phase8_final_review_noapi_rows.jsonl
- data/phase8f_commercial_schema_apply_plan_noapi.json
- data/phase8f_commercial_schema_apply_plan_noapi_rows.jsonl
- data/phase8g_commercial_schema_temp_db_dryrun_noapi.json
- data/phase8g_commercial_schema_temp_db_dryrun_noapi_rows.jsonl
- data/phase8h_commercial_schema_apply_final_plan_noapi.json
- data/phase8h_commercial_schema_apply_final_plan_noapi_rows.jsonl
- data/phase8i_commercial_schema_real_after_explicit_approval.json
- data/phase8i_commercial_schema_real_after_explicit_approval_rows.jsonl
- data/phase8j_commercial_schema_post_audit_noapi.json
- data/phase8j_commercial_schema_post_audit_noapi_rows.jsonl
- data/phase8k_commercial_schema_final_review_noapi.json
- data/phase8k_commercial_schema_final_review_noapi_rows.jsonl

---

### PHASE9 — COMMERCIAL OBSERVATION CONFIG

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, RUNTIME

Kayıt dosyaları:
- data/phase9_commercial_observation_config.json
- data/phase9_commercial_observation_runtime_plan_noapi.json
- data/phase9_commercial_observation_runtime_plan_noapi_rows.jsonl
- data/phase9a_observation_runtime_temp_dryrun_fix1_noapi.json
- data/phase9a_observation_runtime_temp_dryrun_fix1_noapi_rows.jsonl
- data/phase9a_observation_runtime_temp_dryrun_fix2_noapi.json
- data/phase9a_observation_runtime_temp_dryrun_fix2_noapi_rows.jsonl
- data/phase9b_observation_runtime_apply_plan_noapi.json
- data/phase9b_observation_runtime_apply_plan_noapi_rows.jsonl
- data/phase9c_observation_runtime_real_after_explicit_approval.json
- data/phase9c_observation_runtime_real_after_explicit_approval_rows.jsonl
- data/phase9d_observation_runtime_post_audit_noapi.json
- data/phase9d_observation_runtime_post_audit_noapi_rows.jsonl
- data/phase9e_observation_runtime_final_review_noapi.json
- data/phase9e_observation_runtime_final_review_noapi_rows.jsonl

---

### PHASE10 — OBSERVATION RUNTIME FINAL REVIEW NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, RUNTIME

Kayıt dosyaları:
- data/archive/phases/phase10/phase10_observation_runtime_inert_selftest_plan_noapi.json
- data/archive/phases/phase10/phase10a_observation_runtime_inert_selftest_dryrun_noapi.json
- data/archive/phases/phase10/phase10b_observation_runtime_selftest_post_audit_fix1_noapi.json
- data/archive/phases/phase10/phase10b_observation_runtime_selftest_post_audit_noapi.json
- data/archive/phases/phase10/phase10c_observation_runtime_final_review_noapi.json
- data/archive/phases/phase10/phase10d_observation_runtime_service_enable_plan_noapi.json
- data/archive/phases/phase10/phase10e_observation_runtime_service_dryrun_noapi.json
- data/archive/phases/phase10/phase10f_observation_runtime_service_enable_real_after_explicit_approval.json
- data/archive/phases/phase10/phase10g_observation_runtime_service_enable_post_audit_noapi.json
- data/archive/phases/phase10/phase10h_observation_runtime_service_enable_final_review_noapi.json
- data/phase10_observation_runtime_inert_selftest_plan_noapi_rows.jsonl
- data/phase10a_observation_runtime_inert_selftest_dryrun_noapi_rows.jsonl
- data/phase10b_observation_runtime_selftest_post_audit_fix1_noapi_rows.jsonl
- data/phase10b_observation_runtime_selftest_post_audit_noapi_rows.jsonl
- data/phase10c_observation_runtime_final_review_noapi_rows.jsonl
- data/phase10d_observation_runtime_service_enable_plan_noapi_rows.jsonl
- data/phase10e_observation_runtime_service_dryrun_noapi_rows.jsonl
- data/phase10f_observation_runtime_service_enable_real_after_explicit_approval_rows.jsonl
- data/phase10g_observation_runtime_service_enable_post_audit_noapi_rows.jsonl
- data/phase10h_observation_runtime_service_enable_final_review_noapi_rows.jsonl

---

### PHASE11 — OBSERVATION RUNTIME STATUS READMODEL PLAN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, RUNTIME

Kayıt dosyaları:
- data/archive/phases/phase11/phase11_observation_runtime_status_readmodel_plan_noapi.json
- data/archive/phases/phase11/phase11a_observation_runtime_status_readmodel_dryrun_noapi.json
- data/archive/phases/phase11/phase11b_observation_runtime_status_readmodel_apply_plan_fix1_noapi.json
- data/archive/phases/phase11/phase11b_observation_runtime_status_readmodel_apply_plan_noapi.json
- data/archive/phases/phase11/phase11c_observation_runtime_status_readmodel_temp_dryrun_noapi.json
- data/archive/phases/phase11/phase11d_observation_runtime_status_readmodel_final_apply_plan_noapi.json
- data/archive/phases/phase11/phase11e_observation_runtime_status_readmodel_real_after_explicit_approval.json
- data/archive/phases/phase11/phase11f_observation_runtime_status_readmodel_post_audit_noapi.json
- data/archive/phases/phase11/phase11g_observation_runtime_status_readmodel_final_review_noapi.json
- data/phase11_observation_runtime_status_readmodel_plan_noapi_rows.jsonl
- data/phase11a_observation_runtime_status_readmodel_dryrun_noapi_rows.jsonl
- data/phase11b_observation_runtime_status_readmodel_apply_plan_fix1_noapi_rows.jsonl
- data/phase11b_observation_runtime_status_readmodel_apply_plan_noapi_rows.jsonl
- data/phase11c_observation_runtime_status_readmodel_temp_dryrun_noapi_rows.jsonl
- data/phase11d_observation_runtime_status_readmodel_final_apply_plan_noapi_rows.jsonl
- data/phase11e_observation_runtime_status_readmodel_real_after_explicit_approval_rows.jsonl
- data/phase11f_observation_runtime_status_readmodel_post_audit_noapi_rows.jsonl
- data/phase11g_observation_runtime_status_readmodel_final_review_noapi_rows.jsonl

---

### PHASE12 — SYSTEM CONTROL STATUS PANEL BIND PLAN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase12/phase12_system_control_status_panel_bind_plan_noapi.json
- data/archive/phases/phase12/phase12a_system_control_status_panel_bind_dryrun_noapi.json
- data/archive/phases/phase12/phase12b_system_control_status_panel_bind_apply_plan_fix1_noapi.json
- data/archive/phases/phase12/phase12b_system_control_status_panel_bind_apply_plan_fix2_noapi.json
- data/archive/phases/phase12/phase12b_system_control_status_panel_bind_apply_plan_fix3_noapi.json
- data/archive/phases/phase12/phase12b_system_control_status_panel_bind_apply_plan_fix4_noapi.json
- data/archive/phases/phase12/phase12b_system_control_status_panel_bind_apply_plan_noapi.json
- data/archive/phases/phase12/phase12c_system_control_status_panel_bind_real_after_explicit_approval.json
- data/archive/phases/phase12/phase12d_system_control_status_panel_bind_post_audit_noapi.json
- data/archive/phases/phase12/phase12e_system_control_status_panel_bind_final_review_noapi.json
- data/phase12_system_control_status_panel_bind_plan_noapi_rows.jsonl
- data/phase12a_system_control_status_panel_bind_dryrun_noapi_rows.jsonl
- data/phase12b_system_control_status_panel_bind_apply_plan_fix1_noapi_rows.jsonl
- data/phase12b_system_control_status_panel_bind_apply_plan_fix2_noapi_rows.jsonl
- data/phase12b_system_control_status_panel_bind_apply_plan_fix3_noapi_rows.jsonl
- data/phase12b_system_control_status_panel_bind_apply_plan_fix4_noapi_rows.jsonl
- data/phase12b_system_control_status_panel_bind_apply_plan_noapi_rows.jsonl
- data/phase12c_system_control_status_panel_bind_real_after_explicit_approval_rows.jsonl
- data/phase12d_system_control_status_panel_bind_post_audit_noapi_rows.jsonl
- data/phase12e_system_control_status_panel_bind_final_review_noapi_rows.jsonl

---

### PHASE13 — SYSTEM CONTROL STATUS REFRESH PLAN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase13/phase13_system_control_status_refresh_plan_noapi.json
- data/archive/phases/phase13/phase13a_system_control_status_refresh_dryrun_fix1_noapi.json
- data/archive/phases/phase13/phase13a_system_control_status_refresh_dryrun_fix2_timestamp_alias_reconcile_noapi.json
- data/archive/phases/phase13/phase13a_system_control_status_refresh_dryrun_noapi.json
- data/archive/phases/phase13/phase13b_system_control_status_refresh_temp_dryrun_noapi.json
- data/archive/phases/phase13/phase13c_system_control_status_refresh_apply_plan_noapi.json
- data/archive/phases/phase13/phase13d_system_control_status_refresh_real_after_explicit_approval.json
- data/archive/phases/phase13/phase13e_system_control_status_refresh_post_audit_noapi.json
- data/archive/phases/phase13/phase13f_system_control_status_refresh_final_review_noapi.json
- data/phase13_system_control_status_refresh_plan_noapi_rows.jsonl
- data/phase13a_system_control_status_refresh_dryrun_fix1_noapi_rows.jsonl
- data/phase13a_system_control_status_refresh_dryrun_fix2_timestamp_alias_reconcile_noapi_rows.jsonl
- data/phase13a_system_control_status_refresh_dryrun_noapi_rows.jsonl
- data/phase13b_system_control_status_refresh_temp_dryrun_noapi_rows.jsonl
- data/phase13c_system_control_status_refresh_apply_plan_noapi_rows.jsonl
- data/phase13d_system_control_status_refresh_real_after_explicit_approval_rows.jsonl
- data/phase13e_system_control_status_refresh_post_audit_noapi_rows.jsonl
- data/phase13f_system_control_status_refresh_final_review_noapi_rows.jsonl

---

### PHASE14 — SYSTEM CONTROL STATUS REFRESH LOOP PLAN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, CLOSE

Kayıt dosyaları:
- data/archive/phases/phase14/phase14_system_control_status_refresh_loop_plan_fix1_noapi.json
- data/archive/phases/phase14/phase14_system_control_status_refresh_loop_plan_noapi.json
- data/archive/phases/phase14/phase14a_system_control_status_refresh_loop_dryrun_noapi.json
- data/archive/phases/phase14/phase14b_system_control_status_refresh_loop_temp_dryrun_noapi.json
- data/archive/phases/phase14/phase14c_system_control_status_refresh_loop_runner_plan_noapi.json
- data/archive/phases/phase14/phase14d_system_control_status_refresh_loop_runner_file_dryrun_noapi.json
- data/archive/phases/phase14/phase14e_system_control_status_refresh_loop_runner_file_apply_plan_noapi.json
- data/archive/phases/phase14/phase14f_system_control_status_refresh_loop_runner_file_apply_real_after_explicit_approval.json
- data/archive/phases/phase14/phase14g_system_control_status_refresh_loop_runner_file_post_apply_audit_noapi.json
- data/archive/phases/phase14/phase14h_system_control_status_refresh_loop_single_manual_run_plan_noapi.json
- data/archive/phases/phase14/phase14i_system_control_status_refresh_loop_single_manual_run_temp_dryrun_noapi.json
- data/archive/phases/phase14/phase14j_system_control_status_refresh_loop_single_manual_refresh_real_after_explicit_approval.json
- data/archive/phases/phase14/phase14k_system_control_status_refresh_loop_single_manual_refresh_post_audit_noapi.json
- data/archive/phases/phase14/phase14l_system_control_status_refresh_loop_close_single_manual_chain_noapi.json
- data/phase14_system_control_status_refresh_loop_plan_fix1_noapi_rows.jsonl
- data/phase14_system_control_status_refresh_loop_plan_noapi_rows.jsonl
- data/phase14a_system_control_status_refresh_loop_dryrun_noapi_rows.jsonl
- data/phase14b_system_control_status_refresh_loop_temp_dryrun_noapi_rows.jsonl
- data/phase14c_system_control_status_refresh_loop_runner_plan_noapi_rows.jsonl
- data/phase14d_system_control_status_refresh_loop_runner_file_dryrun_noapi_rows.jsonl
- data/phase14e_system_control_status_refresh_loop_runner_file_apply_plan_noapi_rows.jsonl
- data/phase14f_system_control_status_refresh_loop_runner_file_apply_real_after_explicit_approval_rows.jsonl
- data/phase14g_system_control_status_refresh_loop_runner_file_post_apply_audit_noapi_rows.jsonl
- data/phase14h_system_control_status_refresh_loop_single_manual_run_plan_noapi_rows.jsonl
- data/phase14i_system_control_status_refresh_loop_single_manual_run_temp_dryrun_noapi_rows.jsonl
- data/phase14j_system_control_status_refresh_loop_single_manual_refresh_real_after_explicit_approval_rows.jsonl
- data/phase14k_system_control_status_refresh_loop_single_manual_refresh_post_audit_noapi_rows.jsonl
- data/phase14l_system_control_status_refresh_loop_close_single_manual_chain_noapi_rows.jsonl

---

### PHASE15 — Q FIX3 DRYRUN ONCE BRANCH REVIEW NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, CLOSE, RUNTIME

Kayıt dosyaları:
- data/archive/phases/phase15/phase15a_fix1_system_control_status_refresh_service_timer_plan_noapi.json
- data/archive/phases/phase15/phase15a_system_control_status_refresh_service_timer_plan_noapi.json
- data/archive/phases/phase15/phase15b_system_control_status_refresh_service_timer_dryrun_noapi.json
- data/archive/phases/phase15/phase15c_system_control_status_refresh_service_timer_apply_plan_noapi.json
- data/archive/phases/phase15/phase15d_system_control_status_refresh_service_timer_unit_file_apply_real_after_explicit_approval.json
- data/archive/phases/phase15/phase15e_system_control_status_refresh_service_timer_unit_file_post_apply_audit_noapi.json
- data/archive/phases/phase15/phase15f_system_control_status_refresh_service_timer_daemon_reload_plan_noapi.json
- data/archive/phases/phase15/phase15g_system_control_status_refresh_service_timer_daemon_reload_real_after_explicit_approval.json
- data/archive/phases/phase15/phase15h_system_control_status_refresh_service_timer_daemon_reload_post_audit_noapi.json
- data/archive/phases/phase15/phase15i_system_control_status_refresh_service_timer_service_manual_run_plan_noapi.json
- data/archive/phases/phase15/phase15j_system_control_status_refresh_service_timer_service_manual_run_real_after_explicit_approval.json
- data/archive/phases/phase15/phase15k_system_control_status_refresh_service_timer_service_manual_run_post_audit_noapi.json
- data/archive/phases/phase15/phase15l_fix1_system_control_status_refresh_service_timer_dryrun_once_unit_patch_scope_correction_noapi.json
- data/archive/phases/phase15/phase15l_system_control_status_refresh_service_timer_real_refresh_unit_patch_plan_noapi.json
- data/archive/phases/phase15/phase15m_system_control_status_refresh_service_timer_dryrun_once_unit_patch_real_after_explicit_approval.json
- data/archive/phases/phase15/phase15n_fix1_system_control_status_refresh_service_timer_dryrun_once_unit_patch_post_audit_noapi.json
- data/archive/phases/phase15/phase15n_system_control_status_refresh_service_timer_dryrun_once_unit_patch_post_audit_noapi.json
- data/archive/phases/phase15/phase15o_system_control_status_refresh_service_timer_dryrun_once_daemon_reload_plan_noapi.json
- data/archive/phases/phase15/phase15p_system_control_status_refresh_service_timer_dryrun_once_service_manual_run_plan_noapi.json
- data/archive/phases/phase15/phase15q_fix10_dryrun_once_full_temp_unit_patch_real_after_explicit_approval.json
- data/archive/phases/phase15/phase15q_fix11_dryrun_once_full_temp_unit_patch_post_apply_audit_noapi.json
- data/archive/phases/phase15/phase15q_fix11_fix1_dryrun_once_full_temp_unit_patch_post_apply_audit_noapi.json
- data/archive/phases/phase15/phase15q_fix12_dryrun_once_daemon_reload_plan_noapi.json
- data/archive/phases/phase15/phase15q_fix13_dryrun_once_daemon_reload_real_after_explicit_approval.json
- data/archive/phases/phase15/phase15q_fix14_dryrun_once_daemon_reload_post_audit_noapi.json
- data/archive/phases/phase15/phase15q_fix15_dryrun_once_service_manual_run_plan_noapi.json
- data/archive/phases/phase15/phase15q_fix16_dryrun_once_service_manual_run_real_after_explicit_approval.json
- data/archive/phases/phase15/phase15q_fix17_dryrun_once_service_manual_run_post_audit_noapi.json
- data/archive/phases/phase15/phase15q_fix18_dryrun_once_closure_and_timer_chain_plan_noapi.json
- data/archive/phases/phase15/phase15q_fix1_dryrun_once_failure_diagnose_noapi.json
- data/archive/phases/phase15/phase15q_fix2_dryrun_once_cli_scope_review_noapi.json
- data/archive/phases/phase15/phase15q_fix3_dryrun_once_branch_review_noapi.json
- data/archive/phases/phase15/phase15q_fix4_dryrun_once_full_temp_execstart_plan_noapi.json
- data/archive/phases/phase15/phase15q_fix5_dryrun_once_temp_runtime_path_plan_noapi.json
- data/archive/phases/phase15/phase15q_fix6_fix1_dryrun_once_temp_runtime_path_apply_plan_noapi.json
- data/archive/phases/phase15/phase15q_fix7_dryrun_once_temp_runtime_path_apply_real_after_explicit_approval.json
- data/archive/phases/phase15/phase15q_fix8_dryrun_once_temp_runtime_path_post_apply_audit_noapi.json
- data/archive/phases/phase15/phase15q_fix9_dryrun_once_full_temp_unit_patch_plan_noapi.json
- data/archive/phases/phase15/phase15q_system_control_status_refresh_service_timer_dryrun_once_service_manual_run_real_after_explicit_approval.json
- data/archive/phases/phase15/phase15s_system_control_status_refresh_timer_enable_start_plan_noapi.json
- data/archive/phases/phase15/phase15t_system_control_status_refresh_timer_enable_start_real_after_explicit_approval.json
- data/archive/phases/phase15/phase15u_system_control_status_refresh_timer_enable_start_post_audit_noapi.json
- data/archive/phases/phase15/phase15v_system_control_status_refresh_final_closure_noapi.json
- data/phase15a_fix1_system_control_status_refresh_service_timer_plan_noapi_rows.jsonl
- data/phase15a_system_control_status_refresh_service_timer_plan_noapi_rows.jsonl
- data/phase15b_system_control_status_refresh_service_timer_dryrun_noapi_rows.jsonl
- data/phase15c_system_control_status_refresh_service_timer_apply_plan_noapi_rows.jsonl
- data/phase15d_system_control_status_refresh_service_timer_unit_file_apply_real_after_explicit_approval_rows.jsonl
- data/phase15e_system_control_status_refresh_service_timer_unit_file_post_apply_audit_noapi_rows.jsonl
- data/phase15f_system_control_status_refresh_service_timer_daemon_reload_plan_noapi_rows.jsonl
- data/phase15g_system_control_status_refresh_service_timer_daemon_reload_real_after_explicit_approval_rows.jsonl
- data/phase15h_system_control_status_refresh_service_timer_daemon_reload_post_audit_noapi_rows.jsonl
- data/phase15i_system_control_status_refresh_service_timer_service_manual_run_plan_noapi_rows.jsonl
- data/phase15j_system_control_status_refresh_service_timer_service_manual_run_real_after_explicit_approval_rows.jsonl
- data/phase15k_system_control_status_refresh_service_timer_service_manual_run_post_audit_noapi_rows.jsonl
- data/phase15l_fix1_system_control_status_refresh_service_timer_dryrun_once_unit_patch_scope_correction_noapi_rows.jsonl
- data/phase15l_system_control_status_refresh_service_timer_real_refresh_unit_patch_plan_noapi_rows.jsonl
- data/phase15m_system_control_status_refresh_service_timer_dryrun_once_unit_patch_real_after_explicit_approval_rows.jsonl
- data/phase15n_fix1_system_control_status_refresh_service_timer_dryrun_once_unit_patch_post_audit_noapi_rows.jsonl
- data/phase15n_system_control_status_refresh_service_timer_dryrun_once_unit_patch_post_audit_noapi_rows.jsonl
- data/phase15o_system_control_status_refresh_service_timer_dryrun_once_daemon_reload_plan_noapi_rows.jsonl
- data/phase15p_system_control_status_refresh_service_timer_dryrun_once_service_manual_run_plan_noapi_rows.jsonl
- data/phase15q_fix10_dryrun_once_full_temp_unit_patch_real_after_explicit_approval_rows.jsonl
- data/phase15q_fix11_dryrun_once_full_temp_unit_patch_post_apply_audit_noapi_rows.jsonl
- data/phase15q_fix11_fix1_dryrun_once_full_temp_unit_patch_post_apply_audit_noapi_rows.jsonl
- data/phase15q_fix12_dryrun_once_daemon_reload_plan_noapi_rows.jsonl
- data/phase15q_fix13_dryrun_once_daemon_reload_real_after_explicit_approval_rows.jsonl
- data/phase15q_fix14_dryrun_once_daemon_reload_post_audit_noapi_rows.jsonl
- data/phase15q_fix15_dryrun_once_service_manual_run_plan_noapi_rows.jsonl
- data/phase15q_fix16_dryrun_once_service_manual_run_real_after_explicit_approval_rows.jsonl
- data/phase15q_fix17_dryrun_once_service_manual_run_post_audit_noapi_rows.jsonl
- data/phase15q_fix18_dryrun_once_closure_and_timer_chain_plan_noapi_rows.jsonl
- data/phase15q_fix1_dryrun_once_failure_diagnose_noapi_rows.jsonl
- data/phase15q_fix2_dryrun_once_cli_scope_review_noapi_rows.jsonl
- data/phase15q_fix3_dryrun_once_branch_review_noapi_rows.jsonl
- data/phase15q_fix4_dryrun_once_full_temp_execstart_plan_noapi_rows.jsonl
- data/phase15q_fix5_dryrun_once_temp_runtime_path_plan_noapi_rows.jsonl
- data/phase15q_fix6_fix1_dryrun_once_temp_runtime_path_apply_plan_noapi_rows.jsonl
- data/phase15q_fix7_dryrun_once_temp_runtime_path_apply_real_after_explicit_approval_rows.jsonl
- data/phase15q_fix8_dryrun_once_temp_runtime_path_post_apply_audit_noapi_rows.jsonl
- data/phase15q_fix9_dryrun_once_full_temp_unit_patch_plan_noapi_rows.jsonl
- data/phase15q_system_control_status_refresh_service_timer_dryrun_once_service_manual_run_real_after_explicit_approval_rows.jsonl
- data/phase15s_system_control_status_refresh_timer_enable_start_plan_noapi_rows.jsonl
- data/phase15t_system_control_status_refresh_timer_enable_start_real_after_explicit_approval_rows.jsonl
- data/phase15u_system_control_status_refresh_timer_enable_start_post_audit_noapi_rows.jsonl
- data/phase15v_system_control_status_refresh_final_closure_noapi_rows.jsonl

---

### PHASE16 — SYSTEM CONTROL TIMER CADENCE REVIEW NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, CLOSE, RUNTIME

Kayıt dosyaları:
- data/archive/phases/phase16/phase16_system_control_true_refresh_or_timer_cadence_plan_noapi.json
- data/archive/phases/phase16/phase16a_system_control_timer_cadence_review_noapi.json
- data/archive/phases/phase16/phase16b_system_control_timer_cadence_correction_plan_noapi.json
- data/archive/phases/phase16/phase16c_system_control_timer_cadence_correction_real_after_explicit_approval.json
- data/archive/phases/phase16/phase16d_system_control_timer_cadence_correction_post_apply_audit_noapi.json
- data/archive/phases/phase16/phase16e_system_control_timer_cadence_daemon_reload_plan_noapi.json
- data/archive/phases/phase16/phase16f_system_control_timer_cadence_daemon_reload_real_after_explicit_approval.json
- data/archive/phases/phase16/phase16g_system_control_timer_cadence_daemon_reload_post_audit_noapi.json
- data/archive/phases/phase16/phase16h_system_control_timer_cadence_restart_or_reenable_plan_noapi.json
- data/archive/phases/phase16/phase16i_fix1_system_control_timer_runtime_deep_diagnose_noapi.json
- data/archive/phases/phase16/phase16i_fix2_system_control_timer_cadence_model_review_noapi.json
- data/archive/phases/phase16/phase16i_fix3_system_control_timer_cadence_audit_policy_repair_plan_noapi.json
- data/archive/phases/phase16/phase16i_fix4_system_control_timer_cadence_audit_policy_repair_real_after_explicit_approval.json
- data/archive/phases/phase16/phase16i_fix5_fix1_system_control_timer_cadence_audit_policy_repair_post_apply_audit_volatile_temp_fix_noapi.json
- data/archive/phases/phase16/phase16i_fix5_system_control_timer_cadence_audit_policy_repair_post_apply_audit_noapi.json
- data/archive/phases/phase16/phase16i_system_control_timer_cadence_timer_restart_real_after_explicit_approval.json
- data/archive/phases/phase16/phase16j_fix1_system_control_true_refresh_output_binding_plan_noapi.json
- data/archive/phases/phase16/phase16k_system_control_true_refresh_output_binding_dryrun_noapi.json
- data/archive/phases/phase16/phase16l_system_control_true_refresh_output_binding_dryrun_post_review_noapi.json
- data/archive/phases/phase16/phase16m_system_control_true_refresh_output_binding_real_plan_noapi.json
- data/archive/phases/phase16/phase16n_system_control_true_refresh_output_binding_real_after_explicit_approval.json
- data/archive/phases/phase16/phase16o_system_control_true_refresh_output_binding_post_apply_audit_noapi.json
- data/archive/phases/phase16/phase16p_system_control_true_refresh_output_binding_final_closure_noapi.json
- data/archive/phases/phase16/phase16q_system_control_active_status_panel_visibility_audit_noapi.json
- data/phase16_system_control_true_refresh_or_timer_cadence_plan_noapi_rows.jsonl
- data/phase16a_system_control_timer_cadence_review_noapi_rows.jsonl
- data/phase16b_system_control_timer_cadence_correction_plan_noapi_rows.jsonl
- data/phase16c_system_control_timer_cadence_correction_real_after_explicit_approval_rows.jsonl
- data/phase16d_system_control_timer_cadence_correction_post_apply_audit_noapi_rows.jsonl
- data/phase16e_system_control_timer_cadence_daemon_reload_plan_noapi_rows.jsonl
- data/phase16f_system_control_timer_cadence_daemon_reload_real_after_explicit_approval_rows.jsonl
- data/phase16g_system_control_timer_cadence_daemon_reload_post_audit_noapi_rows.jsonl
- data/phase16h_system_control_timer_cadence_restart_or_reenable_plan_noapi_rows.jsonl
- data/phase16i_fix1_system_control_timer_runtime_deep_diagnose_noapi_rows.jsonl
- data/phase16i_fix2_system_control_timer_cadence_model_review_noapi_rows.jsonl
- data/phase16i_fix3_system_control_timer_cadence_audit_policy_repair_plan_noapi_rows.jsonl
- data/phase16i_fix4_system_control_timer_cadence_audit_policy_repair_real_after_explicit_approval_rows.jsonl
- data/phase16i_fix5_fix1_system_control_timer_cadence_audit_policy_repair_post_apply_audit_volatile_temp_fix_noapi_rows.jsonl
- data/phase16i_fix5_system_control_timer_cadence_audit_policy_repair_post_apply_audit_noapi_rows.jsonl
- data/phase16i_system_control_timer_cadence_timer_restart_real_after_explicit_approval_rows.jsonl
- data/phase16j_fix1_system_control_true_refresh_output_binding_plan_noapi_rows.jsonl
- data/phase16k_system_control_true_refresh_output_binding_dryrun_noapi_rows.jsonl
- data/phase16l_system_control_true_refresh_output_binding_dryrun_post_review_noapi_rows.jsonl
- data/phase16m_system_control_true_refresh_output_binding_real_plan_noapi_rows.jsonl
- data/phase16n_system_control_true_refresh_output_binding_real_after_explicit_approval_rows.jsonl
- data/phase16o_system_control_true_refresh_output_binding_post_apply_audit_noapi_rows.jsonl
- data/phase16p_system_control_true_refresh_output_binding_final_closure_noapi_rows.jsonl
- data/phase16q_system_control_active_status_panel_visibility_audit_noapi_rows.jsonl

---

### PHASE17 — Y RECONCILE SOURCE KEY AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, SCHEMA, RUNTIME

Kayıt dosyaları:
- data/archive/phases/phase17/phase17_onchain_whale_pipeline_architecture_plan_noapi.json
- data/archive/phases/phase17/phase17a_bsc_event_source_and_provider_policy_plan_noapi.json
- data/archive/phases/phase17/phase17aa_conveyor_readmodel_envelope_module_apply_real_after_explicit_approval.json
- data/archive/phases/phase17/phase17aa_fix0_conveyor_envelope_apply_real_failure_audit_noapi.json
- data/archive/phases/phase17/phase17aa_fix1_conveyor_envelope_selftest_failure_review_noapi.json
- data/archive/phases/phase17/phase17aa_fix2_conveyor_envelope_apply_real_selftest_args_plan_noapi.json
- data/archive/phases/phase17/phase17aa_fix2a_reader_out_source_locator_and_args_plan_noapi.json
- data/archive/phases/phase17/phase17aa_fix2b_generate_reader_out_and_args_plan_noapi.json
- data/archive/phases/phase17/phase17aa_fix2c_envelope_source_selftest_acceptance_plan_noapi.json
- data/archive/phases/phase17/phase17aa_fix3_conveyor_envelope_apply_real_with_selftest_args_after_explicit_approval.json
- data/archive/phases/phase17/phase17ab_conveyor_readmodel_envelope_module_apply_post_audit_noapi.json
- data/archive/phases/phase17/phase17ac_reader_envelope_contract_bridge_plan_noapi.json
- data/archive/phases/phase17/phase17ad_fix1_reader_envelope_bridge_dryrun_reconcile_noapi.json
- data/archive/phases/phase17/phase17ad_fix2_envelope_selftest_evidence_reconcile_noapi.json
- data/archive/phases/phase17/phase17ad_reader_envelope_contract_bridge_dryrun_noapi.json
- data/archive/phases/phase17/phase17ae_reader_envelope_contract_bridge_dryrun_post_audit_noapi.json
- data/archive/phases/phase17/phase17af_reader_envelope_contract_bridge_acceptance_noapi.json
- data/archive/phases/phase17/phase17b_bsc_event_source_and_provider_policy_dryrun_noapi.json
- data/archive/phases/phase17/phase17c_bsc_readonly_provider_probe_real_after_explicit_approval.json
- data/archive/phases/phase17/phase17c_fix1_bsc_provider_config_and_service_settle_diagnose_noapi.json
- data/archive/phases/phase17/phase17c_fix2_bsc_provider_env_setup_plan_noapi.json
- data/archive/phases/phase17/phase17c_fix3_bsc_provider_env_setup_real_after_explicit_approval.json
- data/archive/phases/phase17/phase17c_fix4_bsc_provider_env_setup_post_audit_noapi.json
- data/archive/phases/phase17/phase17c_fix4_fix1_bsc_provider_env_setup_post_audit_nested_fix_noapi.json
- data/archive/phases/phase17/phase17c_retry_bsc_readonly_provider_probe_real_after_explicit_approval.json
- data/archive/phases/phase17/phase17d_bsc_readonly_provider_probe_post_audit_noapi.json
- data/archive/phases/phase17/phase17d_fix1_bsc_provider_probe_post_audit_nested_fix_noapi.json
- data/archive/phases/phase17/phase17e_bsc_event_source_schema_and_storage_plan_noapi.json
- data/archive/phases/phase17/phase17f_bsc_event_source_schema_storage_dryrun_noapi.json
- data/archive/phases/phase17/phase17g_bsc_event_source_schema_apply_plan_noapi.json
- data/archive/phases/phase17/phase17h_bsc_event_source_schema_apply_real_after_explicit_approval.json
- data/archive/phases/phase17/phase17i_bsc_event_source_schema_apply_post_audit_noapi.json
- data/archive/phases/phase17/phase17j_bsc_event_source_first_row_write_plan_noapi.json
- data/archive/phases/phase17/phase17j_fix1_bsc_event_source_first_row_write_plan_ready_audit_noapi.json
- data/archive/phases/phase17/phase17j_fix2_bsc_event_source_first_row_write_plan_ready_audit_noapi.json
- data/archive/phases/phase17/phase17k_bsc_event_source_first_row_write_real_after_explicit_approval.json
- data/archive/phases/phase17/phase17l_bsc_event_source_first_row_write_post_audit_noapi.json
- data/archive/phases/phase17/phase17m_bsc_event_source_reader_and_validation_plan_noapi.json
- data/archive/phases/phase17/phase17n_bsc_event_source_reader_and_validation_dryrun_noapi.json
- data/archive/phases/phase17/phase17o_bsc_event_source_reader_module_build_plan_noapi.json
- data/archive/phases/phase17/phase17p_bsc_event_source_reader_module_build_dryrun_noapi.json
- data/archive/phases/phase17/phase17p_fix1_bsc_event_source_reader_module_build_dryrun_import_audit_fix_noapi.json
- data/archive/phases/phase17/phase17p_fix2_bsc_event_source_reader_module_build_dryrun_call_audit_fix_noapi.json
- data/archive/phases/phase17/phase17q_bsc_event_source_reader_module_build_dryrun_post_audit_noapi.json
- data/archive/phases/phase17/phase17r_bsc_event_source_reader_module_apply_plan_noapi.json
- data/archive/phases/phase17/phase17s_fix0_bsc_event_source_reader_module_apply_real_failure_audit_noapi.json
- data/archive/phases/phase17/phase17s_fix1_bsc_event_source_reader_module_apply_real_after_explicit_approval.json
- data/archive/phases/phase17/phase17t_bsc_event_source_reader_module_apply_post_audit_noapi.json
- data/archive/phases/phase17/phase17t_fix1_bsc_reader_module_network_literal_locator_noapi.json
- data/archive/phases/phase17/phase17t_fix2_bsc_reader_module_post_audit_literal_rule_fix_noapi.json
- data/archive/phases/phase17/phase17u_bsc_event_source_reader_runtime_contract_plan_noapi.json
- data/archive/phases/phase17/phase17v_bsc_event_source_reader_runtime_contract_dryrun_noapi.json
- data/archive/phases/phase17/phase17v_fix1_bsc_reader_contract_output_shape_review_noapi.json
- data/archive/phases/phase17/phase17v_fix2_conveyor_readmodel_envelope_contract_plan_noapi.json
- data/archive/phases/phase17/phase17v_fix2_envelope_plan_readiness_reconcile_noapi.json
- data/archive/phases/phase17/phase17v_fix2_generic_patch_artifact_locator_and_cleanup_plan_noapi.json
- data/archive/phases/phase17/phase17v_fix3_conveyor_readmodel_envelope_contract_dryrun_noapi.json
- data/archive/phases/phase17/phase17v_fix3_conveyor_readmodel_envelope_contract_dryrun_noapi_envelope_output.json
- data/archive/phases/phase17/phase17v_fix4_conveyor_readmodel_envelope_contract_post_audit_noapi.json
- data/archive/phases/phase17/phase17w_conveyor_readmodel_envelope_module_plan_noapi.json
- data/archive/phases/phase17/phase17x_conveyor_readmodel_envelope_module_dryrun_noapi.json
- data/archive/phases/phase17/phase17x_fix1_conveyor_envelope_ast_call_audit_reconcile_noapi.json
- data/archive/phases/phase17/phase17y2_conveyor_readmodel_envelope_module_post_audit_acceptance_noapi.json
- data/archive/phases/phase17/phase17y2_reconcile_artifact_path_source_audit_noapi.json
- data/archive/phases/phase17/phase17y3_conveyor_readmodel_envelope_module_acceptance_noapi.json
- data/archive/phases/phase17/phase17y_conveyor_readmodel_envelope_module_dryrun_post_audit_noapi.json
- data/archive/phases/phase17/phase17y_reconcile_source_key_audit_noapi.json
- data/archive/phases/phase17/phase17z_conveyor_readmodel_envelope_module_apply_plan_noapi.json
- data/phase17_onchain_whale_pipeline_architecture_plan_noapi_rows.jsonl
- data/phase17a_bsc_event_source_and_provider_policy_plan_noapi_rows.jsonl
- data/phase17aa_conveyor_readmodel_envelope_module_apply_real_after_explicit_approval_rows.jsonl
- data/phase17aa_fix0_conveyor_envelope_apply_real_failure_audit_noapi_rows.jsonl
- data/phase17aa_fix1_conveyor_envelope_selftest_failure_review_noapi_rows.jsonl
- data/phase17aa_fix2_conveyor_envelope_apply_real_selftest_args_plan_noapi_rows.jsonl
- data/phase17aa_fix2a_reader_out_source_locator_and_args_plan_noapi_rows.jsonl
- data/phase17aa_fix2b_generate_reader_out_and_args_plan_noapi_rows.jsonl
- data/phase17aa_fix2c_envelope_source_selftest_acceptance_plan_noapi_rows.jsonl
- data/phase17aa_fix3_conveyor_envelope_apply_real_with_selftest_args_after_explicit_approval_rows.jsonl
- data/phase17ab_conveyor_readmodel_envelope_module_apply_post_audit_noapi_rows.jsonl
- data/phase17ac_reader_envelope_contract_bridge_plan_noapi_rows.jsonl
- data/phase17ad_fix1_reader_envelope_bridge_dryrun_reconcile_noapi_rows.jsonl
- data/phase17ad_fix2_envelope_selftest_evidence_reconcile_noapi_rows.jsonl
- data/phase17ad_reader_envelope_contract_bridge_dryrun_noapi_rows.jsonl
- data/phase17ae_reader_envelope_contract_bridge_dryrun_post_audit_noapi_rows.jsonl
- data/phase17af_reader_envelope_contract_bridge_acceptance_noapi_rows.jsonl
- data/phase17b_bsc_event_source_and_provider_policy_dryrun_noapi_rows.jsonl
- data/phase17c_bsc_readonly_provider_probe_real_after_explicit_approval_rows.jsonl
- data/phase17c_fix1_bsc_provider_config_and_service_settle_diagnose_noapi_rows.jsonl
- data/phase17c_fix2_bsc_provider_env_setup_plan_noapi_rows.jsonl
- data/phase17c_fix3_bsc_provider_env_setup_real_after_explicit_approval_rows.jsonl
- data/phase17c_fix4_bsc_provider_env_setup_post_audit_noapi_rows.jsonl
- data/phase17c_fix4_fix1_bsc_provider_env_setup_post_audit_nested_fix_noapi_rows.jsonl
- data/phase17c_retry_bsc_readonly_provider_probe_real_after_explicit_approval_rows.jsonl
- data/phase17d_bsc_readonly_provider_probe_post_audit_noapi_rows.jsonl
- data/phase17d_fix1_bsc_provider_probe_post_audit_nested_fix_noapi_rows.jsonl
- data/phase17e_bsc_event_source_schema_and_storage_plan_noapi_rows.jsonl
- data/phase17f_bsc_event_source_schema_storage_dryrun_noapi_rows.jsonl
- data/phase17g_bsc_event_source_schema_apply_plan_noapi_rows.jsonl
- data/phase17h_bsc_event_source_schema_apply_real_after_explicit_approval_rows.jsonl
- data/phase17i_bsc_event_source_schema_apply_post_audit_noapi_rows.jsonl
- data/phase17j_bsc_event_source_first_row_write_plan_noapi_rows.jsonl
- data/phase17j_fix1_bsc_event_source_first_row_write_plan_ready_audit_noapi_rows.jsonl
- data/phase17j_fix2_bsc_event_source_first_row_write_plan_ready_audit_noapi_rows.jsonl
- data/phase17k_bsc_event_source_first_row_write_real_after_explicit_approval_rows.jsonl
- data/phase17l_bsc_event_source_first_row_write_post_audit_noapi_rows.jsonl
- data/phase17m_bsc_event_source_reader_and_validation_plan_noapi_rows.jsonl
- data/phase17n_bsc_event_source_reader_and_validation_dryrun_noapi_rows.jsonl
- data/phase17o_bsc_event_source_reader_module_build_plan_noapi_rows.jsonl
- data/phase17p_bsc_event_source_reader_module_build_dryrun_noapi_rows.jsonl
- data/phase17p_fix1_bsc_event_source_reader_module_build_dryrun_import_audit_fix_noapi_rows.jsonl
- data/phase17p_fix2_bsc_event_source_reader_module_build_dryrun_call_audit_fix_noapi_rows.jsonl
- data/phase17q_bsc_event_source_reader_module_build_dryrun_post_audit_noapi_rows.jsonl
- data/phase17r_bsc_event_source_reader_module_apply_plan_noapi_rows.jsonl
- data/phase17s_fix0_bsc_event_source_reader_module_apply_real_failure_audit_noapi_rows.jsonl
- data/phase17s_fix1_bsc_event_source_reader_module_apply_real_after_explicit_approval_rows.jsonl
- data/phase17t_bsc_event_source_reader_module_apply_post_audit_noapi_rows.jsonl
- data/phase17t_fix1_bsc_reader_module_network_literal_locator_noapi_rows.jsonl
- data/phase17t_fix2_bsc_reader_module_post_audit_literal_rule_fix_noapi_rows.jsonl
- data/phase17u_bsc_event_source_reader_runtime_contract_plan_noapi_rows.jsonl
- data/phase17v_bsc_event_source_reader_runtime_contract_dryrun_noapi_rows.jsonl
- data/phase17v_fix1_bsc_reader_contract_output_shape_review_noapi_rows.jsonl
- data/phase17v_fix2_conveyor_readmodel_envelope_contract_plan_noapi_rows.jsonl
- data/phase17v_fix2_envelope_plan_readiness_reconcile_noapi_rows.jsonl
- data/phase17v_fix2_generic_patch_artifact_locator_and_cleanup_plan_noapi_rows.jsonl
- data/phase17v_fix3_conveyor_readmodel_envelope_contract_dryrun_noapi_rows.jsonl
- data/phase17v_fix4_conveyor_readmodel_envelope_contract_post_audit_noapi_rows.jsonl
- data/phase17w_conveyor_readmodel_envelope_module_plan_noapi_rows.jsonl
- data/phase17x_conveyor_readmodel_envelope_module_dryrun_noapi_rows.jsonl
- data/phase17x_fix1_conveyor_envelope_ast_call_audit_reconcile_noapi_rows.jsonl
- data/phase17y2_conveyor_readmodel_envelope_module_post_audit_acceptance_noapi_rows.jsonl
- data/phase17y2_reconcile_artifact_path_source_audit_noapi_rows.jsonl
- data/phase17y3_conveyor_readmodel_envelope_module_acceptance_noapi_rows.jsonl
- data/phase17y_conveyor_readmodel_envelope_module_dryrun_post_audit_noapi_rows.jsonl
- data/phase17y_reconcile_source_key_audit_noapi_rows.jsonl
- data/phase17z_conveyor_readmodel_envelope_module_apply_plan_noapi_rows.jsonl

---

### PHASE18 — PROVIDER POOL BUDGET CACHE GUARD PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase18/phase18a_provider_pool_budget_cache_guard_plan_noapi.json
- data/archive/phases/phase18/phase18b_provider_pool_budget_cache_guard_dryrun_noapi.json
- data/archive/phases/phase18/phase18c_provider_pool_budget_cache_guard_dryrun_post_audit_noapi.json
- data/archive/phases/phase18/phase18d_provider_pool_budget_cache_guard_acceptance_noapi.json
- data/phase18a_provider_pool_budget_cache_guard_plan_noapi_rows.jsonl
- data/phase18b_provider_pool_budget_cache_guard_dryrun_noapi_rows.jsonl
- data/phase18c_provider_pool_budget_cache_guard_dryrun_post_audit_noapi_rows.jsonl
- data/phase18d_provider_pool_budget_cache_guard_acceptance_noapi_rows.jsonl

---

### PHASE19 — REPUTATION SCHEMA APPLY PLAN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, CLOSE, SCHEMA

Kayıt dosyaları:
- data/archive/phases/phase19/phase19a_mass_intake_fast_snapshot_architecture_plan_noapi.json
- data/archive/phases/phase19/phase19b_fix1_fast_snapshot_required_field_reconcile_noapi.json
- data/archive/phases/phase19/phase19b_mass_intake_fast_snapshot_contract_dryrun_noapi.json
- data/archive/phases/phase19/phase19c_fix1_red_mode_provider_evidence_reconcile_noapi.json
- data/archive/phases/phase19/phase19c_mass_intake_fast_snapshot_contract_dryrun_post_audit_noapi.json
- data/archive/phases/phase19/phase19d_mass_intake_fast_snapshot_contract_acceptance_noapi.json
- data/archive/phases/phase19/phase19e_rejection_micro_log_and_internal_reputation_ledger_plan_noapi.json
- data/archive/phases/phase19/phase19f_rejection_micro_log_and_internal_reputation_ledger_dryrun_noapi.json
- data/archive/phases/phase19/phase19g_rejection_micro_log_and_internal_reputation_ledger_dryrun_post_audit_noapi.json
- data/archive/phases/phase19/phase19h_repeat_offender_fast_kill_cache_acceptance_noapi.json
- data/archive/phases/phase19/phase19i_reputation_schema_apply_plan_noapi.json
- data/archive/phases/phase19/phase19j_reputation_schema_apply_dryrun_noapi.json
- data/archive/phases/phase19/phase19k_reputation_schema_apply_dryrun_post_audit_noapi.json
- data/archive/phases/phase19/phase19l_reputation_schema_apply_real_after_explicit_approval.json
- data/archive/phases/phase19/phase19m_reputation_schema_apply_real_post_audit_noapi.json
- data/archive/phases/phase19/phase19n_reputation_schema_baseline_acceptance_noapi.json
- data/archive/phases/phase19/phase19o_reputation_micro_log_data_binding_plan_noapi.json
- data/archive/phases/phase19/phase19p_reputation_micro_log_data_binding_dryrun_noapi.json
- data/archive/phases/phase19/phase19q_reputation_micro_log_data_binding_dryrun_post_audit_noapi.json
- data/archive/phases/phase19/phase19r_reputation_micro_log_data_binding_acceptance_noapi.json
- data/archive/phases/phase19/phase19s_reputation_micro_log_live_writer_plan_noapi.json
- data/archive/phases/phase19/phase19t_reputation_micro_log_live_writer_dryrun_noapi.json
- data/archive/phases/phase19/phase19u_reputation_micro_log_live_writer_dryrun_post_audit_noapi.json
- data/archive/phases/phase19/phase19v_reputation_micro_log_live_writer_dryrun_acceptance_noapi.json
- data/archive/phases/phase19/phase19w_phase19_final_closeout_and_phase20_handoff_noapi.json
- data/phase19a_mass_intake_fast_snapshot_architecture_plan_noapi_rows.jsonl
- data/phase19b_fix1_fast_snapshot_required_field_reconcile_noapi_rows.jsonl
- data/phase19b_mass_intake_fast_snapshot_contract_dryrun_noapi_rows.jsonl
- data/phase19c_fix1_red_mode_provider_evidence_reconcile_noapi_rows.jsonl
- data/phase19c_mass_intake_fast_snapshot_contract_dryrun_post_audit_noapi_rows.jsonl
- data/phase19d_mass_intake_fast_snapshot_contract_acceptance_noapi_rows.jsonl
- data/phase19e_rejection_micro_log_and_internal_reputation_ledger_plan_noapi_rows.jsonl
- data/phase19f_rejection_micro_log_and_internal_reputation_ledger_dryrun_noapi_rows.jsonl
- data/phase19g_rejection_micro_log_and_internal_reputation_ledger_dryrun_post_audit_noapi_rows.jsonl
- data/phase19h_repeat_offender_fast_kill_cache_acceptance_noapi_rows.jsonl
- data/phase19i_reputation_schema_apply_plan_noapi_rows.jsonl
- data/phase19j_reputation_schema_apply_dryrun_noapi_rows.jsonl
- data/phase19k_reputation_schema_apply_dryrun_post_audit_noapi_rows.jsonl
- data/phase19l_reputation_schema_apply_real_after_explicit_approval_rows.jsonl
- data/phase19m_reputation_schema_apply_real_post_audit_noapi_rows.jsonl
- data/phase19n_reputation_schema_baseline_acceptance_noapi_rows.jsonl
- data/phase19o_reputation_micro_log_data_binding_plan_noapi_rows.jsonl
- data/phase19p_reputation_micro_log_data_binding_dryrun_noapi_rows.jsonl
- data/phase19q_reputation_micro_log_data_binding_dryrun_post_audit_noapi_rows.jsonl
- data/phase19r_reputation_micro_log_data_binding_acceptance_noapi_rows.jsonl
- data/phase19s_reputation_micro_log_live_writer_plan_noapi_rows.jsonl
- data/phase19t_reputation_micro_log_live_writer_dryrun_noapi_rows.jsonl
- data/phase19u_reputation_micro_log_live_writer_dryrun_post_audit_noapi_rows.jsonl
- data/phase19v_reputation_micro_log_live_writer_dryrun_acceptance_noapi_rows.jsonl
- data/phase19w_phase19_final_closeout_and_phase20_handoff_noapi_rows.jsonl

---

### PHASE20 — N MEV POLICY DRYRUN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, SCHEMA

Kayıt dosyaları:
- data/archive/phases/phase20/phase20a_whale_entity_intelligence_architecture_plan_noapi.json
- data/archive/phases/phase20/phase20b_whale_entity_data_contract_and_schema_dryrun_noapi.json
- data/archive/phases/phase20/phase20c_whale_entity_readmodel_builder_plan_noapi.json
- data/archive/phases/phase20/phase20d2_whale_entity_screen_wireframe_acceptance_noapi.json
- data/archive/phases/phase20/phase20d_whale_entity_screen_wireframe_plan_noapi.json
- data/archive/phases/phase20/phase20e_whale_entity_schema_real_after_explicit_approval.json
- data/archive/phases/phase20/phase20f_whale_entity_schema_post_audit_noapi.json
- data/archive/phases/phase20/phase20g_known_wallet_source_registry_plan_noapi.json
- data/archive/phases/phase20/phase20h_source_trust_policy_and_label_quality_plan_noapi.json
- data/archive/phases/phase20/phase20i_cex_deposit_bridge_and_mixer_policy_plan_noapi.json
- data/archive/phases/phase20/phase20j_mev_bot_exemption_and_arbitrage_noise_policy_plan_noapi.json
- data/archive/phases/phase20/phase20k_behavioral_shadow_labeling_policy_plan_noapi.json
- data/archive/phases/phase20/phase20l2_known_wallet_source_registry_schema_real_after_explicit_approval.json
- data/archive/phases/phase20/phase20l_known_wallet_source_registry_schema_dryrun_noapi.json
- data/archive/phases/phase20/phase20m_cex_bridge_policy_dryrun_noapi.json
- data/archive/phases/phase20/phase20n2_cex_mev_shadow_gray_areas_policy_plan_noapi.json
- data/archive/phases/phase20/phase20n_mev_policy_dryrun_noapi.json
- data/archive/phases/phase20/phase20o_shadow_label_policy_dryrun_noapi.json
- data/archive/phases/phase20/phase20p_gray_area_policy_dryrun_noapi.json
- data/archive/phases/phase20/phase20q_whale_entity_phase20_policy_baseline_acceptance_noapi.json
- data/archive/phases/phase20/phase20r_known_wallet_source_registry_schema_apply_plan_noapi.json
- data/archive/phases/phase20/phase20s_known_wallet_source_registry_schema_apply_dryrun_noapi.json
- data/archive/phases/phase20/phase20t_known_wallet_source_registry_schema_real_readiness_audit_noapi.json
- data/archive/phases/phase20/phase20u_known_wallet_source_registry_schema_real_post_audit_noapi.json
- data/archive/phases/phase20/phase20v_known_wallet_source_registry_schema_baseline_acceptance_noapi.json
- data/archive/phases/phase20/phase20w_known_wallet_source_seed_plan_noapi.json
- data/archive/phases/phase20/phase20x_known_wallet_source_seed_dryrun_noapi.json
- data/archive/phases/phase20/phase20y_known_wallet_source_seed_real_after_explicit_approval.json
- data/archive/phases/phase20/phase20z2_known_wallet_source_seed_baseline_acceptance_noapi.json
- data/archive/phases/phase20/phase20z_known_wallet_source_seed_real_post_audit_noapi.json
- data/phase20a_whale_entity_intelligence_architecture_plan_noapi_rows.jsonl
- data/phase20b_whale_entity_data_contract_and_schema_dryrun_noapi_rows.jsonl
- data/phase20c_whale_entity_readmodel_builder_plan_noapi_rows.jsonl
- data/phase20d2_whale_entity_screen_wireframe_acceptance_noapi_rows.jsonl
- data/phase20d_whale_entity_screen_wireframe_plan_noapi_rows.jsonl
- data/phase20e_whale_entity_schema_real_after_explicit_approval_rows.jsonl
- data/phase20f_whale_entity_schema_post_audit_noapi_rows.jsonl
- data/phase20g_known_wallet_source_registry_plan_noapi_rows.jsonl
- data/phase20h_source_trust_policy_and_label_quality_plan_noapi_rows.jsonl
- data/phase20i_cex_deposit_bridge_and_mixer_policy_plan_noapi_rows.jsonl
- data/phase20j_mev_bot_exemption_and_arbitrage_noise_policy_plan_noapi_rows.jsonl
- data/phase20k_behavioral_shadow_labeling_policy_plan_noapi_rows.jsonl
- data/phase20l2_known_wallet_source_registry_schema_real_after_explicit_approval_rows.jsonl
- data/phase20l_known_wallet_source_registry_schema_dryrun_noapi_rows.jsonl
- data/phase20m_cex_bridge_policy_dryrun_noapi_rows.jsonl
- data/phase20n2_cex_mev_shadow_gray_areas_policy_plan_noapi_rows.jsonl
- data/phase20n_mev_policy_dryrun_noapi_rows.jsonl
- data/phase20o_shadow_label_policy_dryrun_noapi_rows.jsonl
- data/phase20p_gray_area_policy_dryrun_noapi_rows.jsonl
- data/phase20q_whale_entity_phase20_policy_baseline_acceptance_noapi_rows.jsonl
- data/phase20r_known_wallet_source_registry_schema_apply_plan_noapi_rows.jsonl
- data/phase20s_known_wallet_source_registry_schema_apply_dryrun_noapi_rows.jsonl
- data/phase20t_known_wallet_source_registry_schema_real_readiness_audit_noapi_rows.jsonl
- data/phase20u_known_wallet_source_registry_schema_real_post_audit_noapi_rows.jsonl
- data/phase20v_known_wallet_source_registry_schema_baseline_acceptance_noapi_rows.jsonl
- data/phase20w_known_wallet_source_seed_plan_noapi_rows.jsonl
- data/phase20x_known_wallet_source_seed_dryrun_noapi_rows.jsonl
- data/phase20y_known_wallet_source_seed_real_after_explicit_approval_rows.jsonl
- data/phase20z2_known_wallet_source_seed_baseline_acceptance_noapi_rows.jsonl
- data/phase20z_known_wallet_source_seed_real_post_audit_noapi_rows.jsonl

---

### PHASE21 — WALLET SEED QUEUE PLAN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, SCHEMA

Kayıt dosyaları:
- data/archive/phases/phase21/phase21a_known_wallet_source_registry_readmodel_plan_noapi.json
- data/archive/phases/phase21/phase21f_wallet_seed_queue_plan_noapi.json
- data/archive/phases/phase21/phase21g2_wallet_seed_queue_dirty_data_dryrun_schema_repair_noapi.json
- data/archive/phases/phase21/phase21g3_wallet_seed_queue_dirty_data_dryrun_check_repair_noapi.json
- data/archive/phases/phase21/phase21g_wallet_seed_queue_dirty_data_dryrun_noapi.json
- data/archive/phases/phase21/phase21h2_real_wallet_seed_input_batch_plan_noapi.json
- data/archive/phases/phase21/phase21h3_real_wallet_seed_input_batch_dryrun_noapi.json
- data/archive/phases/phase21/phase21h4_real_wallet_seed_input_batch_build_plan_noapi.json
- data/archive/phases/phase21/phase21h5_real_wallet_seed_batch_stage_from_manual_input_noapi.json
- data/archive/phases/phase21/phase21h_wallet_seed_queue_real_apply_plan_noapi.json
- data/archive/phases/phase21/phase21i_wallet_seed_queue_real_after_explicit_approval.json
- data/archive/phases/phase21/phase21i_wallet_seed_queue_real_apply_pre_audit_noapi.json
- data/archive/phases/phase21/phase21j_wallet_seed_queue_real_post_audit_noapi.json
- data/archive/phases/phase21/phase21k_wallet_seed_queue_live_baseline_acceptance_noapi.json
- data/archive/phases/phase21/phase21l_reputation_decay_backpressure_balance_plan_noapi.json
- data/archive/phases/phase21/phase21m_reputation_decay_backpressure_schema_plan_noapi.json
- data/archive/phases/phase21/phase21n2_reputation_schema_dryrun_forbidden_reference_review_noapi.json
- data/archive/phases/phase21/phase21n3_reputation_schema_dryrun_comment_safe_temp_copy_noapi.json
- data/archive/phases/phase21/phase21n4_backpressure_rollup_field_semantics_review_noapi.json
- data/archive/phases/phase21/phase21n5_reputation_schema_dryrun_precise_field_temp_copy_noapi.json
- data/archive/phases/phase21/phase21n_reputation_decay_backpressure_schema_dryrun_temp_copy_noapi.json
- data/archive/phases/phase21/phase21o2_reputation_decay_backpressure_schema_real_after_explicit_approval.json
- data/archive/phases/phase21/phase21o_reputation_decay_backpressure_schema_real_readiness_audit_noapi.json
- data/archive/phases/phase21/phase21p_reputation_decay_backpressure_schema_real_post_audit_noapi.json
- data/archive/phases/phase21/phase21q_reputation_decay_backpressure_schema_live_baseline_acceptance_noapi.json
- data/archive/phases/phase21/phase21r_reputation_policy_registry_seed_plan_noapi.json
- data/archive/phases/phase21/phase21s_reputation_policy_registry_seed_dryrun_noapi.json
- data/archive/phases/phase21/phase21t_reputation_policy_registry_seed_real_after_explicit_approval.json
- data/archive/phases/phase21/phase21u_reputation_policy_registry_seed_real_post_audit_noapi.json
- data/archive/phases/phase21/phase21v_reputation_policy_registry_live_baseline_acceptance_noapi.json
- data/archive/phases/phase21/phase21w_final_summary_and_next_lock_noapi.json
- data/phase21a_known_wallet_source_registry_readmodel_plan_noapi_rows.jsonl
- data/phase21f_wallet_seed_queue_plan_noapi_rows.jsonl
- data/phase21g3_wallet_seed_queue_dirty_data_dryrun_check_repair_noapi_rows.jsonl
- data/phase21h2_real_wallet_seed_input_batch_plan_noapi_rows.jsonl
- data/phase21h3_real_wallet_seed_input_batch_dryrun_noapi_rows.jsonl
- data/phase21h4_real_wallet_seed_input_batch_build_plan_noapi_rows.jsonl
- data/phase21h5_real_wallet_seed_batch_stage_from_manual_input_noapi_rows.jsonl
- data/phase21h_wallet_seed_queue_real_apply_plan_noapi_rows.jsonl
- data/phase21i_wallet_seed_queue_real_after_explicit_approval_rows.jsonl
- data/phase21i_wallet_seed_queue_real_apply_pre_audit_noapi_rows.jsonl
- data/phase21j_wallet_seed_queue_real_post_audit_noapi_rows.jsonl
- data/phase21k_wallet_seed_queue_live_baseline_acceptance_noapi_rows.jsonl
- data/phase21l_reputation_decay_backpressure_balance_plan_noapi_rows.jsonl
- data/phase21m_reputation_decay_backpressure_schema_plan_noapi_rows.jsonl
- data/phase21n2_reputation_schema_dryrun_forbidden_reference_review_noapi_rows.jsonl
- data/phase21n3_reputation_schema_dryrun_comment_safe_temp_copy_noapi_rows.jsonl
- data/phase21n4_backpressure_rollup_field_semantics_review_noapi_rows.jsonl
- data/phase21n5_reputation_schema_dryrun_precise_field_temp_copy_noapi_rows.jsonl
- data/phase21o2_reputation_decay_backpressure_schema_real_after_explicit_approval_rows.jsonl
- data/phase21o_reputation_decay_backpressure_schema_real_readiness_audit_noapi_rows.jsonl
- data/phase21p_reputation_decay_backpressure_schema_real_post_audit_noapi_rows.jsonl
- data/phase21q_reputation_decay_backpressure_schema_live_baseline_acceptance_noapi_rows.jsonl
- data/phase21r_reputation_policy_registry_seed_plan_noapi_rows.jsonl
- data/phase21s_reputation_policy_registry_seed_dryrun_noapi_rows.jsonl
- data/phase21t_reputation_policy_registry_seed_real_after_explicit_approval_rows.jsonl
- data/phase21u_reputation_policy_registry_seed_real_post_audit_noapi_rows.jsonl
- data/phase21v_reputation_policy_registry_live_baseline_acceptance_noapi_rows.jsonl
- data/phase21w_final_summary_and_next_lock_noapi_rows.jsonl

---

### PHASE22 — REPUTATION READMODEL DRYRUN NOAPI

İş türü: PLAN, DRYRUN

Kayıt dosyaları:
- data/archive/phases/phase22/phase22a_reputation_readmodel_and_panel_clarity_plan_noapi.json
- data/archive/phases/phase22/phase22b_reputation_readmodel_dryrun_noapi.json
- data/archive/phases/phase22/phase22c_entity_uid_and_chain_guard_plan_noapi.json
- data/archive/phases/phase22/phase22d_policy_cache_and_hot_path_budget_plan_noapi.json
- data/archive/phases/phase22/phase22e_stale_score_and_lazy_decay_order_dryrun_noapi.json
- data/archive/phases/phase22/phase22f2_hard_block_sync_gate_false_positive_review_noapi.json
- data/archive/phases/phase22/phase22f2b_hard_block_sync_gate_review_json_path_repair_noapi.json
- data/archive/phases/phase22/phase22f3_hard_block_sync_gate_repaired_dryrun_noapi.json
- data/archive/phases/phase22/phase22f_hard_block_sync_gate_contract_dryrun_noapi.json
- data/archive/phases/phase22/phase22g_slippage_drift_and_quote_ttl_plan_noapi.json
- data/archive/phases/phase22/phase22h_self_review_agent_state_machine_plan_noapi.json
- data/archive/phases/phase22/phase22i_readmodel_and_self_review_baseline_acceptance_noapi.json
- data/archive/phases/phase22/phase22j_phase22_final_summary_and_phase23_lock_noapi.json
- data/phase22a_reputation_readmodel_and_panel_clarity_plan_noapi_rows.jsonl
- data/phase22b_reputation_readmodel_dryrun_noapi_rows.jsonl
- data/phase22c_entity_uid_and_chain_guard_plan_noapi_rows.jsonl
- data/phase22d_policy_cache_and_hot_path_budget_plan_noapi_rows.jsonl
- data/phase22e_stale_score_and_lazy_decay_order_dryrun_noapi_rows.jsonl
- data/phase22f2_hard_block_sync_gate_false_positive_review_noapi_rows.jsonl
- data/phase22f2b_hard_block_sync_gate_review_json_path_repair_noapi_rows.jsonl
- data/phase22f3_hard_block_sync_gate_repaired_dryrun_noapi_rows.jsonl
- data/phase22f_hard_block_sync_gate_contract_dryrun_noapi_rows.jsonl
- data/phase22g_slippage_drift_and_quote_ttl_plan_noapi_rows.jsonl
- data/phase22h_self_review_agent_state_machine_plan_noapi_rows.jsonl
- data/phase22i_readmodel_and_self_review_baseline_acceptance_noapi_rows.jsonl
- data/phase22j_phase22_final_summary_and_phase23_lock_noapi_rows.jsonl

---

### PHASE23 — PAPER REAL DRIFT SCORE PLAN NOAPI

İş türü: PLAN, DRYRUN

Kayıt dosyaları:
- data/archive/phases/phase23/phase23a_outcome_memory_and_loss_cause_plan_noapi.json
- data/archive/phases/phase23/phase23b_outcome_memory_and_loss_cause_dryrun_noapi.json
- data/archive/phases/phase23/phase23c_risk_math_position_size_plan_noapi.json
- data/archive/phases/phase23/phase23d_risk_math_position_size_dryrun_noapi.json
- data/archive/phases/phase23/phase23e_paper_real_drift_score_plan_noapi.json
- data/archive/phases/phase23/phase23f2_market_reality_penalty_and_battlefield_mode_plan_noapi.json
- data/archive/phases/phase23/phase23f3_market_reality_penalty_and_battlefield_mode_dryrun_noapi.json
- data/archive/phases/phase23/phase23f_paper_real_drift_score_dryrun_noapi.json
- data/archive/phases/phase23/phase23g_atis_poligonu_panel_clarity_plan_noapi.json
- data/archive/phases/phase23/phase23h_atis_poligonu_panel_clarity_dryrun_noapi.json
- data/archive/phases/phase23/phase23i_phase23_final_summary_and_phase24_lock_noapi.json
- data/phase23a_outcome_memory_and_loss_cause_plan_noapi_rows.jsonl
- data/phase23b_outcome_memory_and_loss_cause_dryrun_noapi_rows.jsonl
- data/phase23c_risk_math_position_size_plan_noapi_rows.jsonl
- data/phase23d_risk_math_position_size_dryrun_noapi_rows.jsonl
- data/phase23e_paper_real_drift_score_plan_noapi_rows.jsonl
- data/phase23f2_market_reality_penalty_and_battlefield_mode_plan_noapi_rows.jsonl
- data/phase23f3_market_reality_penalty_and_battlefield_mode_dryrun_noapi_rows.jsonl
- data/phase23f_paper_real_drift_score_dryrun_noapi_rows.jsonl
- data/phase23g_atis_poligonu_panel_clarity_plan_noapi_rows.jsonl
- data/phase23h_atis_poligonu_panel_clarity_dryrun_noapi_rows.jsonl
- data/phase23i_phase23_final_summary_and_phase24_lock_noapi_rows.jsonl

---

### PHASE24 — POLICY CANDIDATE SCORE DRYRUN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase24/phase24a_backpressure_killswitch_commander_guard_plan_noapi.json
- data/archive/phases/phase24/phase24b2_same_route_context_backpressure_precedence_repair_noapi.json
- data/archive/phases/phase24/phase24b2b_backpressure_repair_validation_scope_review_noapi.json
- data/archive/phases/phase24/phase24b3_backpressure_killswitch_commander_guard_repaired_dryrun_noapi.json
- data/archive/phases/phase24/phase24b_backpressure_killswitch_commander_guard_dryrun_noapi.json
- data/archive/phases/phase24/phase24c_backpressure_policy_candidate_score_plan_noapi.json
- data/archive/phases/phase24/phase24d_policy_candidate_score_dryrun_noapi.json
- data/archive/phases/phase24/phase24e_policy_candidate_readmodel_apply_plan_noapi.json
- data/archive/phases/phase24/phase24f1_policy_candidate_readmodel_dryrun_exception_review_noapi.json
- data/archive/phases/phase24/phase24f2_policy_candidate_readmodel_apply_dryrun_repair_noapi.json
- data/archive/phases/phase24/phase24f_policy_candidate_readmodel_apply_dryrun_noapi.json
- data/archive/phases/phase24/phase24g_policy_candidate_readmodel_inactive_apply_real_after_explicit_approval.json
- data/archive/phases/phase24/phase24h_policy_candidate_readmodel_inactive_apply_post_audit_noapi.json
- data/archive/phases/phase24/phase24i_backpressure_policy_readmodel_bind_plan_noapi.json
- data/archive/phases/phase24/phase24j_backpressure_policy_readmodel_bind_dryrun_noapi.json
- data/archive/phases/phase24/phase24k_backpressure_policy_readmodel_bind_real_apply_plan_noapi.json
- data/archive/phases/phase24/phase24l_backpressure_policy_readmodel_bind_real_after_explicit_approval.json
- data/archive/phases/phase24/phase24m_backpressure_policy_readmodel_bind_post_audit_noapi.json
- data/archive/phases/phase24/phase24n_backpressure_policy_readmodel_active_panel_bind_plan_noapi.json
- data/archive/phases/phase24/phase24o_backpressure_policy_readmodel_active_panel_bind_dryrun_noapi.json
- data/archive/phases/phase24/phase24p_backpressure_policy_readmodel_active_panel_bind_real_after_explicit_approval.json
- data/archive/phases/phase24/phase24q_backpressure_policy_readmodel_active_panel_bind_post_audit_noapi.json
- data/archive/phases/phase24/phase24r_phase24_final_summary_and_phase25_lock_noapi.json
- data/phase24a_backpressure_killswitch_commander_guard_plan_noapi_rows.jsonl
- data/phase24b2_same_route_context_backpressure_precedence_repair_noapi_rows.jsonl
- data/phase24b2b_backpressure_repair_validation_scope_review_noapi_rows.jsonl
- data/phase24b3_backpressure_killswitch_commander_guard_repaired_dryrun_noapi_rows.jsonl
- data/phase24b_backpressure_killswitch_commander_guard_dryrun_noapi_rows.jsonl
- data/phase24c_backpressure_policy_candidate_score_plan_noapi_rows.jsonl
- data/phase24d_policy_candidate_score_dryrun_noapi_rows.jsonl
- data/phase24e_policy_candidate_readmodel_apply_plan_noapi_rows.jsonl
- data/phase24f1_policy_candidate_readmodel_dryrun_exception_review_noapi_rows.jsonl
- data/phase24f2_policy_candidate_readmodel_apply_dryrun_repair_noapi_rows.jsonl
- data/phase24g_policy_candidate_readmodel_inactive_apply_real_after_explicit_approval_rows.jsonl
- data/phase24h_policy_candidate_readmodel_inactive_apply_post_audit_noapi_rows.jsonl
- data/phase24i_backpressure_policy_readmodel_bind_plan_noapi_rows.jsonl
- data/phase24j_backpressure_policy_readmodel_bind_dryrun_noapi_rows.jsonl
- data/phase24k_backpressure_policy_readmodel_bind_real_apply_plan_noapi_rows.jsonl
- data/phase24l_backpressure_policy_readmodel_bind_real_after_explicit_approval_rows.jsonl
- data/phase24m_backpressure_policy_readmodel_bind_post_audit_noapi_rows.jsonl
- data/phase24n_backpressure_policy_readmodel_active_panel_bind_plan_noapi_rows.jsonl
- data/phase24o_backpressure_policy_readmodel_active_panel_bind_dryrun_noapi_rows.jsonl
- data/phase24p_backpressure_policy_readmodel_active_panel_bind_real_after_explicit_approval_rows.jsonl
- data/phase24q_backpressure_policy_readmodel_active_panel_bind_post_audit_noapi_rows.jsonl
- data/phase24r_phase24_final_summary_and_phase25_lock_noapi_rows.jsonl

---

### PHASE25 — BACKPRESSURE READMODEL REFRESH LOOP PLAN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase25/phase25a1_backpressure_readmodel_refresh_loop_review_scope_noapi.json
- data/archive/phases/phase25/phase25a2_backpressure_readmodel_refresh_loop_plan_repair_noapi.json
- data/archive/phases/phase25/phase25a_backpressure_readmodel_refresh_loop_plan_noapi.json
- data/archive/phases/phase25/phase25b2_backpressure_readmodel_refresh_real_local_dryrun_repair_noapi.json
- data/archive/phases/phase25/phase25b_backpressure_readmodel_refresh_loop_dryrun_noapi.json
- data/archive/phases/phase25/phase25c_backpressure_refresh_output_inactive_apply_plan_noapi.json
- data/archive/phases/phase25/phase25d_backpressure_refresh_output_inactive_apply_real_after_explicit_approval.json
- data/archive/phases/phase25/phase25e_backpressure_refresh_output_inactive_apply_post_audit_noapi.json
- data/archive/phases/phase25/phase25f_phase25_refresh_loop_field_summary_and_phase26_lock_noapi.json
- data/phase25a1_backpressure_readmodel_refresh_loop_review_scope_noapi_rows.jsonl
- data/phase25a2_backpressure_readmodel_refresh_loop_plan_repair_noapi_rows.jsonl
- data/phase25a_backpressure_readmodel_refresh_loop_plan_noapi_rows.jsonl
- data/phase25b2_backpressure_readmodel_refresh_real_local_dryrun_repair_noapi_rows.jsonl
- data/phase25b_backpressure_readmodel_refresh_loop_dryrun_noapi_rows.jsonl
- data/phase25c_backpressure_refresh_output_inactive_apply_plan_noapi_rows.jsonl
- data/phase25d_backpressure_refresh_output_inactive_apply_real_after_explicit_approval_rows.jsonl
- data/phase25e_backpressure_refresh_output_inactive_apply_post_audit_noapi_rows.jsonl
- data/phase25f_phase25_refresh_loop_field_summary_and_phase26_lock_noapi_rows.jsonl

---

### PHASE26 — T25 REPORT KEY FIX FINALIZE V2 NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, CLOSE

Kayıt dosyaları:
- data/archive/phases/phase26/phase26a1_backpressure_refresh_runner_file_plan_scope_repair_noapi.json
- data/archive/phases/phase26/phase26a2_backpressure_refresh_runner_plan_hard_gate_accept_noapi.json
- data/archive/phases/phase26/phase26a_backpressure_refresh_runner_file_plan_noapi.json
- data/archive/phases/phase26/phase26b1_backpressure_refresh_runner_file_dryrun_static_audit_repair_noapi.json
- data/archive/phases/phase26/phase26b_backpressure_refresh_runner_file_dryrun_noapi.json
- data/archive/phases/phase26/phase26c_backpressure_refresh_runner_file_apply_plan_noapi.json
- data/archive/phases/phase26/phase26d_backpressure_refresh_runner_file_apply_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26e1_backpressure_refresh_runner_file_post_audit_scope_repair_noapi.json
- data/archive/phases/phase26/phase26e_backpressure_refresh_runner_file_post_apply_audit_noapi.json
- data/archive/phases/phase26/phase26f_backpressure_refresh_runner_manual_dryrun_plan_noapi.json
- data/archive/phases/phase26/phase26g_backpressure_refresh_runner_manual_dryrun_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26h_backpressure_refresh_runner_manual_dryrun_post_audit_noapi.json
- data/archive/phases/phase26/phase26i_backpressure_refresh_runner_service_timer_plan_noapi.json
- data/archive/phases/phase26/phase26j1_backpressure_refresh_runner_service_timer_dryrun_scope_repair_noapi.json
- data/archive/phases/phase26/phase26j2_backpressure_refresh_runner_service_timer_dryrun_hard_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26j_backpressure_refresh_runner_service_timer_dryrun_noapi.json
- data/archive/phases/phase26/phase26k_backpressure_refresh_runner_service_timer_apply_plan_noapi.json
- data/archive/phases/phase26/phase26l_backpressure_refresh_runner_service_timer_apply_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26m_backpressure_refresh_runner_service_timer_apply_post_audit_noapi.json
- data/archive/phases/phase26/phase26n_backpressure_refresh_runner_daemon_reload_plan_noapi.json
- data/archive/phases/phase26/phase26o1_backpressure_refresh_runner_daemon_reload_precheck_scope_repair_noapi.json
- data/archive/phases/phase26/phase26o2_backpressure_refresh_runner_daemon_reload_real_retry_after_explicit_approval.json
- data/archive/phases/phase26/phase26o_backpressure_refresh_runner_daemon_reload_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26p_backpressure_refresh_runner_daemon_reload_post_audit_noapi.json
- data/archive/phases/phase26/phase26q1_backpressure_refresh_runner_manual_service_run_plan_scope_repair_noapi.json
- data/archive/phases/phase26/phase26q2_backpressure_refresh_runner_manual_service_run_plan_hard_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26q_backpressure_refresh_runner_manual_service_run_plan_noapi.json
- data/archive/phases/phase26/phase26r1_backpressure_refresh_runner_manual_service_start_fail_diagnose_noapi.json
- data/archive/phases/phase26/phase26r1b_backpressure_refresh_runner_systemd_sandbox_and_chdir_deep_diagnose_noapi.json
- data/archive/phases/phase26/phase26r2_backpressure_refresh_runner_service_unit_repair_plan_noapi.json
- data/archive/phases/phase26/phase26r2a_backpressure_refresh_runner_service_unit_repair_plan_scope_accept_noapi.json
- data/archive/phases/phase26/phase26r3_backpressure_refresh_runner_service_unit_repair_dryrun_noapi.json
- data/archive/phases/phase26/phase26r3a1_backpressure_refresh_runner_protecthome_script_access_repair_plan_scope_accept_noapi.json
- data/archive/phases/phase26/phase26r3a_backpressure_refresh_runner_protecthome_script_access_repair_plan_noapi.json
- data/archive/phases/phase26/phase26r3b_backpressure_refresh_runner_protecthome_script_access_repair_dryrun_noapi.json
- data/archive/phases/phase26/phase26r4_backpressure_refresh_runner_protecthome_script_access_repair_apply_plan_noapi.json
- data/archive/phases/phase26/phase26r5_backpressure_refresh_runner_protecthome_script_access_repair_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26r5a_backpressure_refresh_runner_real_precheck_scope_accept_noapi.json
- data/archive/phases/phase26/phase26r5b_backpressure_refresh_runner_protecthome_script_access_repair_real_retry_after_explicit_approval.json
- data/archive/phases/phase26/phase26r6_backpressure_refresh_runner_protecthome_script_access_repair_real_post_audit_noapi.json
- data/archive/phases/phase26/phase26r6a_backpressure_refresh_runner_post_audit_scope_accept_noapi.json
- data/archive/phases/phase26/phase26r6b_backpressure_refresh_runner_post_audit_hard_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26r7_backpressure_refresh_runner_daemon_reload_plan_noapi.json
- data/archive/phases/phase26/phase26r7a_backpressure_refresh_runner_daemon_reload_plan_hard_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26r8_backpressure_refresh_runner_daemon_reload_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26r8a_backpressure_refresh_runner_daemon_reload_real_precheck_scope_accept_noapi.json
- data/archive/phases/phase26/phase26r8b_backpressure_refresh_runner_daemon_reload_real_retry_after_explicit_approval.json
- data/archive/phases/phase26/phase26r8c_backpressure_refresh_runner_daemon_reload_direct_hard_evidence_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26r9_backpressure_refresh_runner_daemon_reload_post_audit_noapi.json
- data/archive/phases/phase26/phase26r_backpressure_refresh_runner_manual_service_run_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26s1_backpressure_refresh_runner_manual_service_run_plan_hard_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26s2_backpressure_refresh_runner_manual_service_run_plan_direct_hard_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26s_backpressure_refresh_runner_manual_service_run_plan_noapi.json
- data/archive/phases/phase26/phase26t10_backpressure_refresh_runner_path_contract_daemon_reload_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26t11_backpressure_refresh_runner_path_contract_daemon_reload_post_audit_noapi.json
- data/archive/phases/phase26/phase26t11a_backpressure_refresh_runner_daemon_reload_post_audit_timer_guard_accept_noapi.json
- data/archive/phases/phase26/phase26t11b_backpressure_refresh_runner_daemon_reload_post_audit_timer_block_direct_accept_noapi.json
- data/archive/phases/phase26/phase26t12_backpressure_refresh_runner_path_contract_manual_service_run_plan_noapi.json
- data/archive/phases/phase26/phase26t13_backpressure_refresh_runner_path_contract_manual_service_run_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26t14_backpressure_refresh_runner_path_contract_manual_service_run_post_audit_noapi.json
- data/archive/phases/phase26/phase26t15_backpressure_refresh_runner_service_start_fail_repair_plan_noapi.json
- data/archive/phases/phase26/phase26t16_backpressure_refresh_runner_cache_validation_repair_dryrun_noapi.json
- data/archive/phases/phase26/phase26t17_backpressure_refresh_runner_cache_validation_repair_apply_plan_noapi.json
- data/archive/phases/phase26/phase26t18_backpressure_refresh_runner_cache_validation_repair_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26t19_backpressure_refresh_runner_cache_validation_repair_real_post_audit_noapi.json
- data/archive/phases/phase26/phase26t1_backpressure_refresh_runner_real_precheck_direct_hard_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26t20_backpressure_refresh_runner_cache_validation_manual_service_run_plan_noapi.json
- data/archive/phases/phase26/phase26t21_backpressure_refresh_runner_cache_validation_manual_service_run_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26t22_backpressure_refresh_runner_cache_validation_manual_service_run_post_audit_noapi.json
- data/archive/phases/phase26/phase26t22a_backpressure_refresh_runner_post_audit_direct_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26t22b_backpressure_refresh_runner_post_audit_current_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26t23_backpressure_refresh_runner_timer_enable_start_plan_noapi.json
- data/archive/phases/phase26/phase26t23a_backpressure_refresh_runner_timer_trigger_direct_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26t24_backpressure_refresh_runner_timer_enable_start_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26t25_backpressure_refresh_runner_timer_enable_start_post_audit_noapi.json
- data/archive/phases/phase26/phase26t25_report_key_fix_finalize_v2_noapi.json
- data/archive/phases/phase26/phase26t26_backpressure_refresh_runner_phase26_close_audit_noapi.json
- data/archive/phases/phase26/phase26t26a_backpressure_refresh_runner_close_audit_exit_contract_direct_accept_noapi.json
- data/archive/phases/phase26/phase26t2_backpressure_refresh_runner_manual_service_run_real_retry_after_explicit_approval.json
- data/archive/phases/phase26/phase26t3_backpressure_refresh_runner_service_start_fail_diagnose_noapi.json
- data/archive/phases/phase26/phase26t4_backpressure_refresh_runner_service_start_fail_repair_plan_noapi.json
- data/archive/phases/phase26/phase26t4a_backpressure_refresh_runner_config_path_contract_repair_plan_noapi.json
- data/archive/phases/phase26/phase26t4b_backpressure_refresh_runner_config_path_contract_direct_hard_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26t4c_backpressure_refresh_runner_config_output_file_contract_repair_plan_noapi.json
- data/archive/phases/phase26/phase26t4d_backpressure_refresh_runner_output_contract_direct_hard_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26t4e_backpressure_refresh_runner_output_contract_direct_current_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26t4f_backpressure_refresh_runner_path_contract_direct_file_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26t5_backpressure_refresh_runner_path_contract_repair_dryrun_noapi.json
- data/archive/phases/phase26/phase26t6_backpressure_refresh_runner_path_contract_repair_apply_plan_noapi.json
- data/archive/phases/phase26/phase26t7_backpressure_refresh_runner_path_contract_repair_real_after_explicit_approval.json
- data/archive/phases/phase26/phase26t8_backpressure_refresh_runner_path_contract_repair_real_post_audit_noapi.json
- data/archive/phases/phase26/phase26t8a_backpressure_refresh_runner_path_contract_post_audit_hard_evidence_accept_noapi.json
- data/archive/phases/phase26/phase26t9_backpressure_refresh_runner_path_contract_repair_daemon_reload_plan_noapi.json
- data/archive/phases/phase26/phase26t_backpressure_refresh_runner_manual_service_run_real_after_explicit_approval.json
- data/phase26a1_backpressure_refresh_runner_file_plan_scope_repair_noapi_rows.jsonl
- data/phase26a2_backpressure_refresh_runner_plan_hard_gate_accept_noapi_rows.jsonl
- data/phase26a_backpressure_refresh_runner_file_plan_noapi_rows.jsonl
- data/phase26b1_backpressure_refresh_runner_file_dryrun_static_audit_repair_noapi_rows.jsonl
- data/phase26b_backpressure_refresh_runner_file_dryrun_noapi_rows.jsonl
- data/phase26c_backpressure_refresh_runner_file_apply_plan_noapi_rows.jsonl
- data/phase26d_backpressure_refresh_runner_file_apply_real_after_explicit_approval_rows.jsonl
- data/phase26e1_backpressure_refresh_runner_file_post_audit_scope_repair_noapi_rows.jsonl
- data/phase26e_backpressure_refresh_runner_file_post_apply_audit_noapi_rows.jsonl
- data/phase26f_backpressure_refresh_runner_manual_dryrun_plan_noapi_rows.jsonl
- data/phase26g_backpressure_refresh_runner_manual_dryrun_real_after_explicit_approval_rows.jsonl
- data/phase26h_backpressure_refresh_runner_manual_dryrun_post_audit_noapi_rows.jsonl
- data/phase26i_backpressure_refresh_runner_service_timer_plan_noapi_rows.jsonl
- data/phase26j1_backpressure_refresh_runner_service_timer_dryrun_scope_repair_noapi_rows.jsonl
- data/phase26j2_backpressure_refresh_runner_service_timer_dryrun_hard_evidence_accept_noapi_rows.jsonl
- data/phase26j_backpressure_refresh_runner_service_timer_dryrun_noapi_rows.jsonl
- data/phase26k_backpressure_refresh_runner_service_timer_apply_plan_noapi_rows.jsonl
- data/phase26l_backpressure_refresh_runner_service_timer_apply_real_after_explicit_approval_rows.jsonl
- data/phase26m_backpressure_refresh_runner_service_timer_apply_post_audit_noapi_rows.jsonl
- data/phase26n_backpressure_refresh_runner_daemon_reload_plan_noapi_rows.jsonl
- data/phase26o1_backpressure_refresh_runner_daemon_reload_precheck_scope_repair_noapi_rows.jsonl
- data/phase26o2_backpressure_refresh_runner_daemon_reload_real_retry_after_explicit_approval_rows.jsonl
- data/phase26p_backpressure_refresh_runner_daemon_reload_post_audit_noapi_rows.jsonl
- data/phase26q1_backpressure_refresh_runner_manual_service_run_plan_scope_repair_noapi_rows.jsonl
- data/phase26q2_backpressure_refresh_runner_manual_service_run_plan_hard_evidence_accept_noapi_rows.jsonl
- data/phase26q_backpressure_refresh_runner_manual_service_run_plan_noapi_rows.jsonl
- data/phase26r1_backpressure_refresh_runner_manual_service_start_fail_diagnose_noapi_rows.jsonl
- data/phase26r1b_backpressure_refresh_runner_systemd_sandbox_and_chdir_deep_diagnose_noapi_rows.jsonl
- data/phase26r2_backpressure_refresh_runner_service_unit_repair_plan_noapi_rows.jsonl
- data/phase26r2a_backpressure_refresh_runner_service_unit_repair_plan_scope_accept_noapi_rows.jsonl
- data/phase26r3_backpressure_refresh_runner_service_unit_repair_dryrun_noapi_rows.jsonl
- data/phase26r3a1_backpressure_refresh_runner_protecthome_script_access_repair_plan_scope_accept_noapi_rows.jsonl
- data/phase26r3a_backpressure_refresh_runner_protecthome_script_access_repair_plan_noapi_rows.jsonl
- data/phase26r3b_backpressure_refresh_runner_protecthome_script_access_repair_dryrun_noapi_rows.jsonl
- data/phase26r4_backpressure_refresh_runner_protecthome_script_access_repair_apply_plan_noapi_rows.jsonl
- data/phase26r5a_backpressure_refresh_runner_real_precheck_scope_accept_noapi_rows.jsonl
- data/phase26r5b_backpressure_refresh_runner_protecthome_script_access_repair_real_retry_after_explicit_approval_rows.jsonl
- data/phase26r6_backpressure_refresh_runner_protecthome_script_access_repair_real_post_audit_noapi_rows.jsonl
- data/phase26r6a_backpressure_refresh_runner_post_audit_scope_accept_noapi_rows.jsonl
- data/phase26r6b_backpressure_refresh_runner_post_audit_hard_evidence_accept_noapi_rows.jsonl
- data/phase26r7_backpressure_refresh_runner_daemon_reload_plan_noapi_rows.jsonl
- data/phase26r7a_backpressure_refresh_runner_daemon_reload_plan_hard_evidence_accept_noapi_rows.jsonl
- data/phase26r8_backpressure_refresh_runner_daemon_reload_real_after_explicit_approval_rows.jsonl
- data/phase26r8a_backpressure_refresh_runner_daemon_reload_real_precheck_scope_accept_noapi_rows.jsonl
- data/phase26r8b_backpressure_refresh_runner_daemon_reload_real_retry_after_explicit_approval_rows.jsonl
- data/phase26r8c_backpressure_refresh_runner_daemon_reload_direct_hard_evidence_real_after_explicit_approval_rows.jsonl
- data/phase26r9_backpressure_refresh_runner_daemon_reload_post_audit_noapi_rows.jsonl
- data/phase26r_backpressure_refresh_runner_manual_service_run_real_after_explicit_approval_rows.jsonl
- data/phase26s1_backpressure_refresh_runner_manual_service_run_plan_hard_evidence_accept_noapi_rows.jsonl
- data/phase26s2_backpressure_refresh_runner_manual_service_run_plan_direct_hard_evidence_accept_noapi_rows.jsonl
- data/phase26s_backpressure_refresh_runner_manual_service_run_plan_noapi_rows.jsonl
- data/phase26t10_backpressure_refresh_runner_path_contract_daemon_reload_real_after_explicit_approval_rows.jsonl
- data/phase26t11_backpressure_refresh_runner_path_contract_daemon_reload_post_audit_noapi_rows.jsonl
- data/phase26t11a_backpressure_refresh_runner_daemon_reload_post_audit_timer_guard_accept_noapi_rows.jsonl
- data/phase26t11b_backpressure_refresh_runner_daemon_reload_post_audit_timer_block_direct_accept_noapi_rows.jsonl
- data/phase26t12_backpressure_refresh_runner_path_contract_manual_service_run_plan_noapi_rows.jsonl
- data/phase26t13_backpressure_refresh_runner_path_contract_manual_service_run_real_after_explicit_approval_rows.jsonl
- data/phase26t14_backpressure_refresh_runner_path_contract_manual_service_run_post_audit_noapi_rows.jsonl
- data/phase26t15_backpressure_refresh_runner_service_start_fail_repair_plan_noapi_rows.jsonl
- data/phase26t16_backpressure_refresh_runner_cache_validation_repair_dryrun_noapi_rows.jsonl
- data/phase26t17_backpressure_refresh_runner_cache_validation_repair_apply_plan_noapi_rows.jsonl
- data/phase26t18_backpressure_refresh_runner_cache_validation_repair_real_after_explicit_approval_rows.jsonl
- data/phase26t19_backpressure_refresh_runner_cache_validation_repair_real_post_audit_noapi_rows.jsonl
- data/phase26t1_backpressure_refresh_runner_real_precheck_direct_hard_evidence_accept_noapi_rows.jsonl
- data/phase26t20_backpressure_refresh_runner_cache_validation_manual_service_run_plan_noapi_rows.jsonl
- data/phase26t21_backpressure_refresh_runner_cache_validation_manual_service_run_real_after_explicit_approval_rows.jsonl
- data/phase26t22_backpressure_refresh_runner_cache_validation_manual_service_run_post_audit_noapi_rows.jsonl
- data/phase26t22a_backpressure_refresh_runner_post_audit_direct_evidence_accept_noapi_rows.jsonl
- data/phase26t22b_backpressure_refresh_runner_post_audit_current_evidence_accept_noapi_rows.jsonl
- data/phase26t23_backpressure_refresh_runner_timer_enable_start_plan_noapi_rows.jsonl
- data/phase26t23a_backpressure_refresh_runner_timer_trigger_direct_evidence_accept_noapi_rows.jsonl
- data/phase26t24_backpressure_refresh_runner_timer_enable_start_real_after_explicit_approval_rows.jsonl
- data/phase26t25_backpressure_refresh_runner_timer_enable_start_post_audit_noapi_rows.jsonl
- data/phase26t26_backpressure_refresh_runner_phase26_close_audit_noapi_rows.jsonl
- data/phase26t26a_backpressure_refresh_runner_close_audit_exit_contract_direct_accept_noapi_rows.jsonl
- data/phase26t2_backpressure_refresh_runner_manual_service_run_real_retry_after_explicit_approval_rows.jsonl
- data/phase26t3_backpressure_refresh_runner_service_start_fail_diagnose_noapi_rows.jsonl
- data/phase26t4_backpressure_refresh_runner_service_start_fail_repair_plan_noapi_rows.jsonl
- data/phase26t4a_backpressure_refresh_runner_config_path_contract_repair_plan_noapi_rows.jsonl
- data/phase26t4b_backpressure_refresh_runner_config_path_contract_direct_hard_evidence_accept_noapi_rows.jsonl
- data/phase26t4c_backpressure_refresh_runner_config_output_file_contract_repair_plan_noapi_rows.jsonl
- data/phase26t4d_backpressure_refresh_runner_output_contract_direct_hard_evidence_accept_noapi_rows.jsonl
- data/phase26t4e_backpressure_refresh_runner_output_contract_direct_current_evidence_accept_noapi_rows.jsonl
- data/phase26t4f_backpressure_refresh_runner_path_contract_direct_file_evidence_accept_noapi_rows.jsonl
- data/phase26t5_backpressure_refresh_runner_path_contract_repair_dryrun_noapi_rows.jsonl
- data/phase26t6_backpressure_refresh_runner_path_contract_repair_apply_plan_noapi_rows.jsonl
- data/phase26t7_backpressure_refresh_runner_path_contract_repair_real_after_explicit_approval_rows.jsonl
- data/phase26t8_backpressure_refresh_runner_path_contract_repair_real_post_audit_noapi_rows.jsonl
- data/phase26t8a_backpressure_refresh_runner_path_contract_post_audit_hard_evidence_accept_noapi_rows.jsonl
- data/phase26t9_backpressure_refresh_runner_path_contract_repair_daemon_reload_plan_noapi_rows.jsonl
- data/phase26t_backpressure_refresh_runner_manual_service_run_real_after_explicit_approval_rows.jsonl

---

### PHASE27 — BACKPRESSURE REFRESH RUNNER PHASE27 CLOSE AUDIT NOAPI

İş türü: AUDIT, CLOSE, RUNTIME

Kayıt dosyaları:
- data/archive/phases/phase27/phase27a1_backpressure_timer_trigger_direct_evidence_accept_noapi.json
- data/archive/phases/phase27/phase27a_backpressure_refresh_runner_timer_runtime_observation_audit_noapi.json
- data/archive/phases/phase27/phase27b_backpressure_refresh_runner_timer_cycle_count_audit_noapi.json
- data/archive/phases/phase27/phase27c_backpressure_refresh_runner_runtime_output_cache_quality_audit_noapi.json
- data/archive/phases/phase27/phase27d_backpressure_refresh_runner_safety_boundary_audit_noapi.json
- data/archive/phases/phase27/phase27e1_backpressure_refresh_runner_semantic_contract_detail_accept_noapi.json
- data/archive/phases/phase27/phase27e1a_backpressure_refresh_runner_wallet_sign_negative_policy_accept_noapi.json
- data/archive/phases/phase27/phase27e_backpressure_refresh_runner_readmodel_meaning_audit_noapi.json
- data/archive/phases/phase27/phase27f1_backpressure_refresh_runner_cadence_trigger_direct_accept_noapi.json
- data/archive/phases/phase27/phase27f_backpressure_refresh_runner_load_and_cadence_decision_audit_noapi.json
- data/archive/phases/phase27/phase27g_backpressure_refresh_runner_phase27_close_audit_noapi.json
- data/phase27a1_backpressure_timer_trigger_direct_evidence_accept_noapi_rows.jsonl
- data/phase27b_backpressure_refresh_runner_timer_cycle_count_audit_noapi_rows.jsonl
- data/phase27c_backpressure_refresh_runner_runtime_output_cache_quality_audit_noapi_rows.jsonl
- data/phase27d_backpressure_refresh_runner_safety_boundary_audit_noapi_rows.jsonl
- data/phase27e1_backpressure_refresh_runner_semantic_contract_detail_accept_noapi_rows.jsonl
- data/phase27e1a_backpressure_refresh_runner_wallet_sign_negative_policy_accept_noapi_rows.jsonl
- data/phase27e_backpressure_refresh_runner_readmodel_meaning_audit_noapi_rows.jsonl
- data/phase27f1_backpressure_refresh_runner_cadence_trigger_direct_accept_noapi_rows.jsonl
- data/phase27f_backpressure_refresh_runner_load_and_cadence_decision_audit_noapi_rows.jsonl
- data/phase27g_backpressure_refresh_runner_phase27_close_audit_noapi_rows.jsonl

---

### PHASE28 — PHASE28 CLOSE AUDIT NOAPI

İş türü: PLAN, AUDIT, CLOSE

Kayıt dosyaları:
- data/archive/phases/phase28/phase28a_center_inventory_gate_cascade_data_integrity_map_plan_noapi.json
- data/archive/phases/phase28/phase28b1_data_provenance_no_silent_overwrite_rule_repair_noapi.json
- data/archive/phases/phase28/phase28b_data_provenance_and_canonicalization_contract_noapi.json
- data/archive/phases/phase28/phase28c_hard_gate_and_emergency_brake_contract_noapi.json
- data/archive/phases/phase28/phase28d_precomputed_route_matrix_plan_noapi.json
- data/archive/phases/phase28/phase28e_validator_raw_trace_and_severity_audit_plan_noapi.json
- data/archive/phases/phase28/phase28f_ai_calibration_and_learning_boundary_plan_noapi.json
- data/archive/phases/phase28/phase28g_center_subpanel_icon_prune_plan_noapi.json
- data/archive/phases/phase28/phase28h1_close_audit_failed_must_have_detail_noapi.json
- data/archive/phases/phase28/phase28h2_close_audit_direct_evidence_accept_noapi.json
- data/archive/phases/phase28/phase28h_phase28_close_audit_noapi.json
- data/phase28a_center_inventory_gate_cascade_data_integrity_map_plan_noapi_rows.jsonl
- data/phase28b1_data_provenance_no_silent_overwrite_rule_repair_noapi_rows.jsonl
- data/phase28b_data_provenance_and_canonicalization_contract_noapi_rows.jsonl
- data/phase28c_hard_gate_and_emergency_brake_contract_noapi_rows.jsonl
- data/phase28d_precomputed_route_matrix_plan_noapi_rows.jsonl
- data/phase28e_validator_raw_trace_and_severity_audit_plan_noapi_rows.jsonl
- data/phase28f_ai_calibration_and_learning_boundary_plan_noapi_rows.jsonl
- data/phase28g_center_subpanel_icon_prune_plan_noapi_rows.jsonl
- data/phase28h1_close_audit_failed_must_have_detail_noapi_rows.jsonl
- data/phase28h2_close_audit_direct_evidence_accept_noapi_rows.jsonl
- data/phase28h_phase28_close_audit_noapi_rows.jsonl

---

### PHASE29 — CLOSE AUDIT KEY PATH GUARD PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, CLOSE

Kayıt dosyaları:
- data/archive/phases/phase29/phase29a_system_gate_self_test_and_false_alarm_hardening_plan_noapi.json
- data/archive/phases/phase29/phase29b_system_gate_evidence_priority_contract_noapi.json
- data/archive/phases/phase29/phase29c_system_gate_false_alarm_real_fail_test_matrix_noapi.json
- data/archive/phases/phase29/phase29d_close_audit_key_path_guard_plan_noapi.json
- data/archive/phases/phase29/phase29e1_tempdb_acceptance_event_threshold_detail_noapi.json
- data/archive/phases/phase29/phase29e2_tempdb_acceptance_threshold_direct_accept_noapi.json
- data/archive/phases/phase29/phase29e_system_gate_self_test_tempdb_dryrun_plan_noapi.json
- data/archive/phases/phase29/phase29f_system_gate_self_test_tempdb_post_audit_noapi.json
- data/archive/phases/phase29/phase29g_system_gate_self_test_phase29_close_audit_noapi.json
- data/phase29a_system_gate_self_test_and_false_alarm_hardening_plan_noapi_rows.jsonl
- data/phase29b_system_gate_evidence_priority_contract_noapi_rows.jsonl
- data/phase29c_system_gate_false_alarm_real_fail_test_matrix_noapi_rows.jsonl
- data/phase29d_close_audit_key_path_guard_plan_noapi_rows.jsonl
- data/phase29e1_tempdb_acceptance_event_threshold_detail_noapi_rows.jsonl
- data/phase29e2_tempdb_acceptance_threshold_direct_accept_noapi_rows.jsonl
- data/phase29e_system_gate_self_test_tempdb_dryrun_plan_noapi_rows.jsonl
- data/phase29f_system_gate_self_test_tempdb_post_audit_noapi_rows.jsonl
- data/phase29g_system_gate_self_test_phase29_close_audit_noapi_rows.jsonl

---

### PHASE30 — PHASE30 CLOSE AUDIT NOAPI

İş türü: PLAN, DRYRUN, AUDIT, CLOSE

Kayıt dosyaları:
- data/archive/phases/phase30/phase30a_system_gate_live_integration_inventory_plan_noapi.json
- data/archive/phases/phase30/phase30b_system_gate_compact_state_contract_noapi.json
- data/archive/phases/phase30/phase30c_compact_state_stale_policy_noapi.json
- data/archive/phases/phase30/phase30d_live_evidence_collector_dryrun_noapi.json
- data/archive/phases/phase30/phase30e_adaptive_self_test_cadence_plan_noapi.json
- data/archive/phases/phase30/phase30f1_failure_latency_matrix_failed_case_detail_noapi.json
- data/archive/phases/phase30/phase30f2_failure_latency_matrix_expectation_direct_accept_noapi.json
- data/archive/phases/phase30/phase30f_failure_mode_and_latency_matrix_noapi.json
- data/archive/phases/phase30/phase30g_phase30_close_audit_noapi.json
- data/phase30a_system_gate_live_integration_inventory_plan_noapi_rows.jsonl
- data/phase30b_system_gate_compact_state_contract_noapi_rows.jsonl
- data/phase30c_compact_state_stale_policy_noapi_rows.jsonl
- data/phase30d_live_evidence_collector_dryrun_noapi_rows.jsonl
- data/phase30e_adaptive_self_test_cadence_plan_noapi_rows.jsonl
- data/phase30f1_failure_latency_matrix_failed_case_detail_noapi_rows.jsonl
- data/phase30f2_failure_latency_matrix_expectation_direct_accept_noapi_rows.jsonl
- data/phase30f_failure_mode_and_latency_matrix_noapi_rows.jsonl
- data/phase30g_phase30_close_audit_noapi_rows.jsonl

---

### PHASE31 — STATE CAPSULE POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, CLOSE, SCHEMA

Kayıt dosyaları:
- data/archive/phases/phase31/phase31a1_data_provenance_tempdb_schema_sample_insert_repair_noapi.json
- data/archive/phases/phase31/phase31a_data_provenance_staging_canonical_tempdb_schema_plan_noapi.json
- data/archive/phases/phase31/phase31b_data_provenance_constraint_and_lifecycle_test_matrix_noapi.json
- data/archive/phases/phase31/phase31c_canonical_supersede_and_quarantine_lifecycle_contract_noapi.json
- data/archive/phases/phase31/phase31d1_canonical_missing_raw_hash_failed_case_detail_noapi.json
- data/archive/phases/phase31/phase31d2_canonical_missing_raw_hash_test_repair_tempdb_dryrun_noapi.json
- data/archive/phases/phase31/phase31d_canonical_supersede_and_quarantine_tempdb_dryrun_noapi.json
- data/archive/phases/phase31/phase31e_canonical_supersede_and_quarantine_post_dryrun_audit_noapi.json
- data/archive/phases/phase31/phase31f1_data_provenance_phase31_close_audit_repair_noapi.json
- data/archive/phases/phase31/phase31f_data_provenance_phase31_close_audit_noapi.json
- data/archive/phases/phase31/phase31g_session_independence_state_capsule_plan_noapi.json
- data/archive/phases/phase31/phase31h_session_independence_state_capsule_dryrun_noapi.json
- data/archive/phases/phase31/phase31i_state_capsule_write_real_after_explicit_approval.json
- data/archive/phases/phase31/phase31j_state_capsule_post_audit_noapi.json
- data/archive/phases/phase31/phase31x_local_ai_maintenance_assistant_feasibility_noapi.json
- data/phase31a1_data_provenance_tempdb_schema_sample_insert_repair_noapi_rows.jsonl
- data/phase31b_data_provenance_constraint_and_lifecycle_test_matrix_noapi_rows.jsonl
- data/phase31c_canonical_supersede_and_quarantine_lifecycle_contract_noapi_rows.jsonl
- data/phase31d1_canonical_missing_raw_hash_failed_case_detail_noapi_rows.jsonl
- data/phase31d2_canonical_missing_raw_hash_test_repair_tempdb_dryrun_noapi_rows.jsonl
- data/phase31d_canonical_supersede_and_quarantine_tempdb_dryrun_noapi_rows.jsonl
- data/phase31e_canonical_supersede_and_quarantine_post_dryrun_audit_noapi_rows.jsonl
- data/phase31f1_data_provenance_phase31_close_audit_repair_noapi_rows.jsonl
- data/phase31f_data_provenance_phase31_close_audit_noapi_rows.jsonl
- data/phase31g_session_independence_state_capsule_plan_noapi_rows.jsonl
- data/phase31h_session_independence_state_capsule_dryrun_noapi_rows.jsonl
- data/phase31i_state_capsule_write_real_after_explicit_approval_rows.jsonl
- data/phase31j_state_capsule_post_audit_noapi_rows.jsonl
- data/phase31x_local_ai_maintenance_assistant_feasibility_noapi_rows.jsonl

---

### PHASE32 — CONTROL CENTER FILE DRYRUN NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, CLOSE, SCHEMA

Kayıt dosyaları:
- data/archive/phases/phase32/phase32a_maintenance_ai_control_center_plan_noapi.json
- data/archive/phases/phase32/phase32b_maintenance_state_reader_and_bundle_contract_noapi.json
- data/archive/phases/phase32/phase32c_ai_proposal_schema_and_validator_contract_noapi.json
- data/archive/phases/phase32/phase32d_approval_queue_and_rollback_registry_plan_noapi.json
- data/archive/phases/phase32/phase32e1_control_center_tempdb_dryrun_decision_print_repair_noapi.json
- data/archive/phases/phase32/phase32e_control_center_tempdb_dryrun_noapi.json
- data/archive/phases/phase32/phase32f_control_center_file_dryrun_noapi.json
- data/archive/phases/phase32/phase32g_control_center_real_apply_after_explicit_approval.json
- data/archive/phases/phase32/phase32h1_control_center_post_apply_audit_required_path_repair_noapi.json
- data/archive/phases/phase32/phase32h_control_center_post_apply_audit_noapi.json
- data/archive/phases/phase32/phase32i_control_center_closeout_and_state_sync_plan_noapi.json
- data/archive/phases/phase32/phase32j_control_center_state_sync_dryrun_noapi.json
- data/archive/phases/phase32/phase32k_control_center_state_sync_real_after_explicit_approval.json
- data/archive/phases/phase32/phase32l_control_center_state_sync_post_apply_audit_noapi.json
- data/archive/phases/phase32/phase32m_control_center_final_closeout_and_next_roadmap_plan_noapi.json
- data/archive/phases/phase32/phase32n_control_center_next_target_state_correction_dryrun_noapi.json
- data/archive/phases/phase32/phase32o_control_center_next_target_state_correction_real_after_explicit_approval.json
- data/archive/phases/phase32/phase32p1_next_target_state_correction_post_audit_backup_scope_repair_noapi.json
- data/archive/phases/phase32/phase32p_control_center_next_target_state_correction_post_apply_audit_noapi.json
- data/phase32a_maintenance_ai_control_center_plan_noapi_rows.jsonl
- data/phase32b_maintenance_state_reader_and_bundle_contract_noapi_rows.jsonl
- data/phase32c_ai_proposal_schema_and_validator_contract_noapi_rows.jsonl
- data/phase32d_approval_queue_and_rollback_registry_plan_noapi_rows.jsonl
- data/phase32e1_control_center_tempdb_dryrun_decision_print_repair_noapi_rows.jsonl
- data/phase32e_control_center_tempdb_dryrun_noapi_rows.jsonl
- data/phase32f_control_center_file_dryrun_noapi_rows.jsonl
- data/phase32g_control_center_real_apply_after_explicit_approval_rows.jsonl
- data/phase32h1_control_center_post_apply_audit_required_path_repair_noapi_rows.jsonl
- data/phase32h_control_center_post_apply_audit_noapi_rows.jsonl
- data/phase32i_control_center_closeout_and_state_sync_plan_noapi_rows.jsonl
- data/phase32j_control_center_state_sync_dryrun_noapi_rows.jsonl
- data/phase32k_control_center_state_sync_real_after_explicit_approval_rows.jsonl
- data/phase32l_control_center_state_sync_post_apply_audit_noapi_rows.jsonl
- data/phase32m_control_center_final_closeout_and_next_roadmap_plan_noapi_rows.jsonl
- data/phase32n_control_center_next_target_state_correction_dryrun_noapi_rows.jsonl
- data/phase32o_control_center_next_target_state_correction_real_after_explicit_approval_rows.jsonl
- data/phase32p1_next_target_state_correction_post_audit_backup_scope_repair_noapi_rows.jsonl
- data/phase32p_control_center_next_target_state_correction_post_apply_audit_noapi_rows.jsonl

---

### PHASE33 — MAINTENANCE AI PROPOSAL SMOKE TEST PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase33/phase33_maintenance_ai_proposal_smoke_test_plan_noapi.json
- data/archive/phases/phase33/phase33a_maintenance_ai_proposal_smoke_test_dryrun_noapi.json
- data/archive/phases/phase33/phase33b_maintenance_ai_proposal_smoke_test_dryrun_post_audit_noapi.json
- data/phase33_maintenance_ai_proposal_smoke_test_plan_noapi_rows.jsonl
- data/phase33a_maintenance_ai_proposal_smoke_test_dryrun_noapi_rows.jsonl
- data/phase33b_maintenance_ai_proposal_smoke_test_dryrun_post_audit_noapi_rows.jsonl

---

### PHASE35 — FAST PATH COMPACT STATE AND MATRIX TEMPDB NOAPI

İş türü: DRYRUN, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase35/phase35_fast_path_compact_state_and_matrix_tempdb_noapi.json
- data/archive/phases/phase35/phase35a_fast_path_compact_state_and_matrix_tempdb_post_audit_noapi.json
- data/phase35_fast_path_compact_state_and_matrix_tempdb_noapi_rows.jsonl
- data/phase35a_fast_path_compact_state_and_matrix_tempdb_post_audit_noapi_rows.jsonl

---

### PHASE36 — 38 FUNCTION SPLIT AUDIT READONLY NOAPI

İş türü: DRYRUN, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase36/phase36_38_function_split_audit_readonly_noapi.json
- data/archive/phases/phase36/phase36_slow_path_learning_calibration_ledger_noapi.json
- data/archive/phases/phase36/phase36a_slow_path_learning_calibration_ledger_tempdb_dryrun_noapi.json
- data/archive/phases/phase36/phase36b_slow_path_learning_calibration_ledger_tempdb_post_audit_noapi.json
- data/phase36_slow_path_learning_calibration_ledger_noapi_rows.jsonl
- data/phase36a_slow_path_learning_calibration_ledger_tempdb_dryrun_noapi_rows.jsonl
- data/phase36b_slow_path_learning_calibration_ledger_tempdb_post_audit_noapi_rows.jsonl

---

### PHASE37 — OPPORTUNITY RADAR SCORING DRYRUN NOAPI

İş türü: DRYRUN, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase37/phase37_opportunity_radar_scoring_dryrun_noapi.json
- data/archive/phases/phase37/phase37a_opportunity_radar_scoring_dryrun_post_audit_noapi.json
- data/phase37_opportunity_radar_scoring_dryrun_noapi_rows.jsonl
- data/phase37a_opportunity_radar_scoring_dryrun_post_audit_noapi_rows.jsonl

---

### PHASE38 — PAPER LIFECYCLE LEDGER COST RISK MODEL NOAPI

İş türü: DRYRUN, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase38/phase38_paper_lifecycle_ledger_cost_risk_model_noapi.json
- data/archive/phases/phase38/phase38a_paper_lifecycle_ledger_cost_risk_model_tempdb_dryrun_noapi.json
- data/archive/phases/phase38/phase38b_paper_lifecycle_ledger_cost_risk_model_tempdb_post_audit_noapi.json
- data/phase38_paper_lifecycle_ledger_cost_risk_model_noapi_rows.jsonl
- data/phase38a_paper_lifecycle_ledger_cost_risk_model_tempdb_dryrun_noapi_rows.jsonl
- data/phase38b_paper_lifecycle_ledger_cost_risk_model_tempdb_post_audit_noapi_rows.jsonl

---

### PHASE39 — SHADOW PAPER SIMULATION NOAPI

İş türü: DRYRUN, AUDIT

Kayıt dosyaları:
- data/archive/phases/phase39/phase39_shadow_paper_simulation_noapi.json
- data/archive/phases/phase39/phase39a_shadow_paper_simulation_tempdb_dryrun_noapi.json
- data/archive/phases/phase39/phase39b_shadow_paper_simulation_tempdb_post_audit_noapi.json
- data/phase39_shadow_paper_simulation_noapi_rows.jsonl
- data/phase39a_shadow_paper_simulation_tempdb_dryrun_noapi_rows.jsonl
- data/phase39b_shadow_paper_simulation_tempdb_post_audit_noapi_rows.jsonl

---

### PHASE40 — README

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, SCHEMA

Kayıt dosyaları:
- data/archive/phases/phase40/phase40_split_audit_readonly_noapi.json
- data/archive/phases/phase40/phase40_technical_tactical_learning_engine_plan_noapi.json
- data/archive/phases/phase40/phase40a_technical_indicator_contract_plan_noapi.json
- data/archive/phases/phase40/phase40b_technical_freshness_and_buffer_tempdb_dryrun_noapi.json
- data/archive/phases/phase40/phase40c_technical_freshness_and_buffer_post_audit_noapi.json
- data/archive/phases/phase40/phase40d_technical_attack_trap_escape_tempdb_dryrun_noapi.json
- data/archive/phases/phase40/phase40e_technical_rwd_and_false_negative_memory_plan_noapi.json
- data/archive/phases/phase40/phase40e_technical_rwd_false_negative_and_ai_contract_analyst_plan_noapi.json
- data/archive/phases/phase40/phase40f_hybrid_ai_contract_analyst_and_provider_budget_plan_noapi.json
- data/archive/phases/phase40/phase40f_news_social_launch_signal_integration_plan_noapi.json
- data/archive/phases/phase40/phase40g_news_social_launch_signal_schema_tempdb_dryrun_noapi.json
- data/archive/phases/phase40/phase40h_news_social_launch_signal_schema_apply_plan_noapi.json
- data/archive/phases/phase40/phase40i_news_social_launch_signal_schema_apply_real_after_explicit_approval.json
- data/archive/phases/phase40/phase40j_news_social_launch_signal_schema_post_audit_noapi.json
- data/archive/phases/phase40/phase40k_news_social_launch_signal_write_path_plan_noapi.json
- data/archive/phases/phase40/phase40l_news_social_launch_signal_write_path_tempdb_dryrun_noapi.json
- data/archive/phases/phase40/phase40m_news_social_launch_signal_write_path_apply_plan_noapi.json
- data/archive/phases/phase40/phase40n_news_social_launch_signal_writer_tool_apply_real_after_explicit_approval.json
- data/archive/phases/phase40/phase40o_news_social_launch_signal_writer_tool_post_audit_noapi.json
- data/archive/phases/phase40/phase40p_news_social_local_input_sample_write_plan_noapi.json
- data/archive/phases/phase40/phase40q_news_social_local_input_sample_write_real_noapi.json
- data/news_social_local_inputs/phase40q_current/README.md
- data/news_social_local_inputs/phase40q_current/manifest.json
- data/news_social_local_inputs/phase40q_current/news_social_local_samples.jsonl
- data/news_social_local_inputs/phase40q_current/news_social_source_policy.json
- data/phase40_technical_tactical_learning_engine_plan_noapi_rows.jsonl
- data/phase40a_technical_indicator_contract_plan_noapi_rows.jsonl
- data/phase40b_technical_freshness_and_buffer_tempdb_dryrun_noapi_rows.jsonl
- data/phase40c_technical_freshness_and_buffer_post_audit_noapi_rows.jsonl
- data/phase40d_technical_attack_trap_escape_tempdb_dryrun_noapi_rows.jsonl
- data/phase40e_technical_rwd_and_false_negative_memory_plan_noapi_rows.jsonl
- data/phase40e_technical_rwd_false_negative_and_ai_contract_analyst_plan_noapi_rows.jsonl
- data/phase40f_hybrid_ai_contract_analyst_and_provider_budget_plan_noapi_rows.jsonl
- data/phase40f_news_social_launch_signal_integration_plan_noapi_rows.jsonl
- data/phase40g_news_social_launch_signal_schema_tempdb_dryrun_noapi_rows.jsonl
- data/phase40h_news_social_launch_signal_schema_apply_plan_noapi_rows.jsonl
- data/phase40i_news_social_launch_signal_schema_apply_real_after_explicit_approval_rows.jsonl
- data/phase40j_news_social_launch_signal_schema_post_audit_noapi_rows.jsonl
- data/phase40k_news_social_launch_signal_write_path_plan_noapi_rows.jsonl
- data/phase40l_news_social_launch_signal_write_path_tempdb_dryrun_noapi_rows.jsonl
- data/phase40m_news_social_launch_signal_write_path_apply_plan_noapi_rows.jsonl
- data/phase40n_news_social_launch_signal_writer_tool_apply_real_after_explicit_approval_rows.jsonl
- data/phase40o_news_social_launch_signal_writer_tool_post_audit_noapi_rows.jsonl
- data/phase40p_news_social_local_input_sample_write_plan_noapi_rows.jsonl
- data/phase40q_news_social_local_input_sample_write_real_noapi_rows.jsonl

---

### PHASE42 — POST PUSH CANONICAL AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL, SCHEMA

Kayıt dosyaları:
- docs/phases/phase42/PHASE42A_UNKNOWN_ANOMALY_ENGINE_ARCHITECTURE_PLAN_NOAPI.md
- docs/phases/phase42/PHASE42B_UNKNOWN_ANOMALY_ENGINE_SCHEMA_PLAN_NOAPI.md
- docs/phases/phase42/PHASE42C_UNKNOWN_ANOMALY_ENGINE_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase42/PHASE42D_UNKNOWN_ANOMALY_ENGINE_POST_AUDIT_NOAPI.md
- docs/phases/phase42/PHASE42E_UNKNOWN_ANOMALY_ENGINE_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase42/PHASE42_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- data/archive/phases/phase42/phase42_post_push_canonical_audit_noapi.json
- data/archive/phases/phase42/phase42a_unknown_anomaly_engine_architecture_plan_noapi.json
- data/archive/phases/phase42/phase42b_unknown_anomaly_engine_schema_plan_noapi.json
- data/archive/phases/phase42/phase42c_unknown_anomaly_engine_tempdb_dryrun_noapi.json
- data/archive/phases/phase42/phase42d_unknown_anomaly_engine_post_audit_noapi.json
- data/archive/phases/phase42/phase42e_unknown_anomaly_engine_canonical_binding_real_apply.json
- data/phase42_post_push_canonical_audit_noapi_rows.jsonl
- data/phase42a_unknown_anomaly_engine_architecture_plan_noapi_rows.jsonl
- data/phase42b_unknown_anomaly_engine_schema_plan_noapi_rows.jsonl
- data/phase42c_unknown_anomaly_engine_tempdb_dryrun_noapi_rows.jsonl
- data/phase42d_unknown_anomaly_engine_post_audit_noapi_rows.jsonl
- data/phase42e_unknown_anomaly_engine_canonical_binding_real_apply_rows.jsonl

---

### PHASE43 — FINAL POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL, SCHEMA

Kayıt dosyaları:
- docs/phases/phase43/PHASE43B_PROSECUTOR_ENGINE_SCHEMA_PLAN_NOAPI.md
- docs/phases/phase43/PHASE43C_PROSECUTOR_ENGINE_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase43/PHASE43D_PROSECUTOR_ENGINE_POST_AUDIT_NOAPI.md
- docs/phases/phase43/PHASE43E_CANONICAL_BINDING_REPAIR_REAL_APPLY.md
- docs/phases/phase43/PHASE43E_PROSECUTOR_ENGINE_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase43/PHASE43_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase43/PHASE43_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- docs/phases/phase43/PHASE43_PROSECUTOR_ENGINE_PLAN_NOAPI.md
- data/archive/phases/phase43/phase43_final_post_audit_noapi.json
- data/archive/phases/phase43/phase43_post_push_canonical_audit_noapi.json
- data/archive/phases/phase43/phase43_prosecutor_engine_plan_noapi.json
- data/archive/phases/phase43/phase43b_prosecutor_engine_schema_plan_noapi.json
- data/archive/phases/phase43/phase43c_prosecutor_engine_tempdb_dryrun_noapi.json
- data/archive/phases/phase43/phase43d_prosecutor_engine_post_audit_noapi.json
- data/archive/phases/phase43/phase43e_canonical_binding_repair_real_apply.json
- data/phase43_final_post_audit_noapi_rows.jsonl
- data/phase43_post_push_canonical_audit_noapi_rows.jsonl
- data/phase43_prosecutor_engine_plan_noapi_rows.jsonl
- data/phase43b_prosecutor_engine_schema_plan_noapi_rows.jsonl
- data/phase43c_prosecutor_engine_tempdb_dryrun_noapi_rows.jsonl
- data/phase43d_prosecutor_engine_post_audit_noapi_rows.jsonl
- data/phase43e_canonical_binding_repair_real_apply_rows.jsonl
- data/phase43e_prosecutor_engine_canonical_binding_real_apply_rows.jsonl

---

### PHASE44 — FINAL POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL, SCHEMA

Kayıt dosyaları:
- docs/phases/phase44/PHASE44A_TOKENOSKOBI_CONSTITUTION_V1_PLAN_NOAPI.md
- docs/phases/phase44/PHASE44B_INTELLIGENCE_FUSION_ENGINE_PLAN_NOAPI.md
- docs/phases/phase44/PHASE44C_INTELLIGENCE_FUSION_ENGINE_SCHEMA_PLAN_NOAPI.md
- docs/phases/phase44/PHASE44D_INTELLIGENCE_FUSION_ENGINE_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase44/PHASE44E_INTELLIGENCE_FUSION_ENGINE_POST_AUDIT_NOAPI.md
- docs/phases/phase44/PHASE44F_INTELLIGENCE_FUSION_ENGINE_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase44/PHASE44_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase44/PHASE44_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- data/archive/phases/phase44/phase44_final_post_audit_noapi.json
- data/archive/phases/phase44/phase44_post_push_canonical_audit_noapi.json
- data/archive/phases/phase44/phase44a_tokenoskobi_constitution_v1_plan_noapi.json
- data/archive/phases/phase44/phase44b_intelligence_fusion_engine_plan_noapi.json
- data/archive/phases/phase44/phase44c_intelligence_fusion_engine_schema_plan_noapi.json
- data/archive/phases/phase44/phase44d_intelligence_fusion_engine_tempdb_dryrun_noapi.json
- data/archive/phases/phase44/phase44e_intelligence_fusion_engine_post_audit_noapi.json
- data/archive/phases/phase44/phase44f_intelligence_fusion_engine_canonical_binding_real_apply.json
- data/phase44_final_post_audit_noapi_rows.jsonl
- data/phase44_post_push_canonical_audit_noapi_rows.jsonl
- data/phase44a_tokenoskobi_constitution_v1_plan_noapi_rows.jsonl
- data/phase44b_intelligence_fusion_engine_plan_noapi_rows.jsonl
- data/phase44c_intelligence_fusion_engine_schema_plan_noapi_rows.jsonl
- data/phase44d_intelligence_fusion_engine_tempdb_dryrun_noapi_rows.jsonl
- data/phase44e_intelligence_fusion_engine_post_audit_noapi_rows.jsonl
- data/phase44f_intelligence_fusion_engine_canonical_binding_real_apply_rows.jsonl

---

### PHASE45 — FINAL POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL, SCHEMA

Kayıt dosyaları:
- docs/phases/phase45/PHASE45B_HAREKAT_SUBAYI_SCHEMA_PLAN_NOAPI.md
- docs/phases/phase45/PHASE45C_HAREKAT_SUBAYI_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase45/PHASE45D_HAREKAT_SUBAYI_POST_AUDIT_NOAPI.md
- docs/phases/phase45/PHASE45E_HAREKAT_SUBAYI_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase45/PHASE45_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase45/PHASE45_HAREKAT_SUBAYI_EVOLUTION_PLAN_NOAPI.md
- docs/phases/phase45/PHASE45_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- data/archive/phases/phase45/phase45_final_post_audit_noapi.json
- data/archive/phases/phase45/phase45_harekat_subayi_evolution_plan_noapi.json
- data/archive/phases/phase45/phase45_post_push_canonical_audit_noapi.json
- data/archive/phases/phase45/phase45b_harekat_subayi_schema_plan_noapi.json
- data/archive/phases/phase45/phase45c_harekat_subayi_tempdb_dryrun_noapi.json
- data/archive/phases/phase45/phase45d_harekat_subayi_post_audit_noapi.json
- data/archive/phases/phase45/phase45e_harekat_subayi_canonical_binding_real_apply.json
- data/phase45_final_post_audit_noapi_rows.jsonl
- data/phase45_harekat_subayi_evolution_plan_noapi_rows.jsonl
- data/phase45_post_push_canonical_audit_noapi_rows.jsonl
- data/phase45b_harekat_subayi_schema_plan_noapi_rows.jsonl
- data/phase45c_harekat_subayi_tempdb_dryrun_noapi_rows.jsonl
- data/phase45d_harekat_subayi_post_audit_noapi_rows.jsonl
- data/phase45e_harekat_subayi_canonical_binding_real_apply_rows.jsonl

---

### PHASE46 — FINAL POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL, SCHEMA

Kayıt dosyaları:
- docs/phases/phase46/PHASE46B_TRAINING_EXPORT_SCHEMA_PLAN_NOAPI.md
- docs/phases/phase46/PHASE46C_TRAINING_EXPORT_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase46/PHASE46D_TRAINING_EXPORT_POST_AUDIT_NOAPI.md
- docs/phases/phase46/PHASE46E_TRAINING_EXPORT_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase46/PHASE46_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase46/PHASE46_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- docs/phases/phase46/PHASE46_TRAINING_EXPORT_AND_GPU_ORCHESTRATION_PLAN_NOAPI.md
- data/archive/phases/phase46/phase46_final_post_audit_noapi.json
- data/archive/phases/phase46/phase46_post_push_canonical_audit_noapi.json
- data/archive/phases/phase46/phase46_training_export_and_gpu_orchestration_plan_noapi.json
- data/archive/phases/phase46/phase46b_training_export_schema_plan_noapi.json
- data/archive/phases/phase46/phase46c_training_export_tempdb_dryrun_noapi.json
- data/archive/phases/phase46/phase46d_training_export_post_audit_noapi.json
- data/archive/phases/phase46/phase46e_training_export_canonical_binding_real_apply.json
- data/phase46_final_post_audit_noapi_rows.jsonl
- data/phase46_post_push_canonical_audit_noapi_rows.jsonl
- data/phase46_training_export_and_gpu_orchestration_plan_noapi_rows.jsonl
- data/phase46b_training_export_schema_plan_noapi_rows.jsonl
- data/phase46c_training_export_tempdb_dryrun_noapi_rows.jsonl
- data/phase46d_training_export_post_audit_noapi_rows.jsonl
- data/phase46e_training_export_canonical_binding_real_apply_rows.jsonl

---

### PHASE47 — FINAL POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL, SCHEMA

Kayıt dosyaları:
- docs/phases/phase47/PHASE47B_TOKEN_LIFECYCLE_EVENT_TAXONOMY_PLAN_NOAPI.md
- docs/phases/phase47/PHASE47C_TOKEN_LIFECYCLE_SCHEMA_AND_SANITIZATION_PLAN_NOAPI.md
- docs/phases/phase47/PHASE47D_TOKEN_LIFECYCLE_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase47/PHASE47E_TOKEN_LIFECYCLE_POST_AUDIT_NOAPI.md
- docs/phases/phase47/PHASE47F_TOKEN_LIFECYCLE_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase47/PHASE47_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase47/PHASE47_POST_PUSH_AUDIT_GITHUB_SEAL.md
- docs/phases/phase47/PHASE47_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- docs/phases/phase47/PHASE47_TOKEN_LIFECYCLE_INTELLIGENCE_FAST_READMODEL_PLAN_NOAPI.md
- data/archive/phases/phase47/phase47_final_post_audit_noapi.json
- data/archive/phases/phase47/phase47_post_push_audit_github_seal.json
- data/archive/phases/phase47/phase47_token_lifecycle_intelligence_fast_readmodel_plan_noapi.json
- data/archive/phases/phase47/phase47b_token_lifecycle_event_taxonomy_plan_noapi.json
- data/archive/phases/phase47/phase47c_token_lifecycle_schema_and_sanitization_plan_noapi.json
- data/archive/phases/phase47/phase47d_token_lifecycle_tempdb_dryrun_noapi.json
- data/archive/phases/phase47/phase47e_token_lifecycle_post_audit_noapi.json
- data/archive/phases/phase47/phase47f_token_lifecycle_canonical_binding_real_apply.json
- data/phase47_final_post_audit_noapi_rows.jsonl
- data/phase47_post_push_audit_github_seal_rows.jsonl
- data/phase47_post_push_canonical_audit_noapi_rows.jsonl
- data/phase47_token_lifecycle_intelligence_fast_readmodel_plan_noapi_rows.jsonl
- data/phase47b_token_lifecycle_event_taxonomy_plan_noapi_rows.jsonl
- data/phase47c_token_lifecycle_schema_and_sanitization_plan_noapi_rows.jsonl
- data/phase47d_token_lifecycle_tempdb_dryrun_noapi_rows.jsonl
- data/phase47e_token_lifecycle_post_audit_noapi_rows.jsonl
- data/phase47f_token_lifecycle_canonical_binding_real_apply_rows.jsonl

---

### PHASE48 — FINAL POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL, SCHEMA

Kayıt dosyaları:
- docs/phases/phase48/PHASE48B_THREAT_MEMORY_SCHEMA_PLAN_NOAPI.md
- docs/phases/phase48/PHASE48C_THREAT_MEMORY_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase48/PHASE48D_THREAT_MEMORY_POST_AUDIT_NOAPI.md
- docs/phases/phase48/PHASE48E_THREAT_MEMORY_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase48/PHASE48_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase48/PHASE48_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- docs/phases/phase48/PHASE48_THREAT_MEMORY_AND_OUTCOME_INTELLIGENCE_PLAN_NOAPI.md
- data/archive/phases/phase48/phase48_final_post_audit_noapi.json
- data/archive/phases/phase48/phase48_post_push_canonical_audit_noapi.json
- data/archive/phases/phase48/phase48_threat_memory_and_outcome_intelligence_plan_noapi.json
- data/archive/phases/phase48/phase48b_threat_memory_schema_plan_noapi.json
- data/archive/phases/phase48/phase48c_threat_memory_tempdb_dryrun_noapi.json
- data/archive/phases/phase48/phase48d_threat_memory_post_audit_noapi.json
- data/archive/phases/phase48/phase48e_threat_memory_canonical_binding_real_apply.json
- data/phase48_final_post_audit_noapi_rows.jsonl
- data/phase48_post_push_canonical_audit_noapi_rows.jsonl
- data/phase48_threat_memory_and_outcome_intelligence_plan_noapi_rows.jsonl
- data/phase48b_threat_memory_schema_plan_noapi_rows.jsonl
- data/phase48c_threat_memory_tempdb_dryrun_noapi_rows.jsonl
- data/phase48d_threat_memory_post_audit_noapi_rows.jsonl
- data/phase48e_threat_memory_canonical_binding_real_apply_rows.jsonl

---

### PHASE49 — FINAL POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL

Kayıt dosyaları:
- docs/phases/phase49/PHASE49A_100_COIN_BURST_RESPONSE_TATBIKAT_TEMPDB_NOAPI.md
- docs/phases/phase49/PHASE49A_RAY_BATCH_RESPONSE_RECHECK_TEMPDB_NOAPI.md
- docs/phases/phase49/PHASE49B_RAY_BATCH_AND_FULL_ANALYSIS_SCALABILITY_DOCTRINE_PLAN_NOAPI.md
- docs/phases/phase49/PHASE49C_SCALABILITY_DOCTRINE_POST_AUDIT_NOAPI.md
- docs/phases/phase49/PHASE49D_SCALABILITY_DOCTRINE_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase49/PHASE49_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase49/PHASE49_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- data/archive/phases/phase49/phase49_final_post_audit_noapi.json
- data/archive/phases/phase49/phase49_post_push_canonical_audit_noapi.json
- data/archive/phases/phase49/phase49a_100_coin_burst_response_tatbikat_tempdb_noapi.json
- data/archive/phases/phase49/phase49a_ray_batch_response_recheck_tempdb_noapi.json
- data/archive/phases/phase49/phase49b_ray_batch_and_full_analysis_scalability_doctrine_plan_noapi.json
- data/archive/phases/phase49/phase49c_scalability_doctrine_post_audit_noapi.json
- data/archive/phases/phase49/phase49d_scalability_doctrine_canonical_binding_real_apply.json
- data/phase49_final_post_audit_noapi_rows.jsonl
- data/phase49_post_push_canonical_audit_noapi_rows.jsonl
- data/phase49a_100_coin_burst_response_tatbikat_tempdb_noapi_rows.jsonl
- data/phase49a_ray_batch_response_recheck_tempdb_noapi_rows.jsonl
- data/phase49b_ray_batch_and_full_analysis_scalability_doctrine_plan_noapi_rows.jsonl
- data/phase49c_scalability_doctrine_post_audit_noapi_rows.jsonl
- data/phase49d_scalability_doctrine_canonical_binding_real_apply_rows.jsonl

---

### PHASE50 — FINAL POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL, SCHEMA

Kayıt dosyaları:
- docs/phases/phase50/PHASE50B_RAY_DECISION_MEMORY_SCHEMA_PLAN_NOAPI.md
- docs/phases/phase50/PHASE50C_RAY_DECISION_MEMORY_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase50/PHASE50D_RAY_DECISION_MEMORY_POST_AUDIT_NOAPI.md
- docs/phases/phase50/PHASE50E_RAY_DECISION_MEMORY_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase50/PHASE50_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase50/PHASE50_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- docs/phases/phase50/PHASE50_RAY_DECISION_MEMORY_AND_LIFECYCLE_REASONING_PLAN_NOAPI.md
- data/phase50_final_post_audit_noapi.json
- data/phase50_final_post_audit_noapi_rows.jsonl
- data/phase50_post_push_canonical_audit_noapi.json
- data/phase50_post_push_canonical_audit_noapi_rows.jsonl
- data/phase50_ray_decision_memory_and_lifecycle_reasoning_plan_noapi.json
- data/phase50_ray_decision_memory_and_lifecycle_reasoning_plan_noapi_rows.jsonl
- data/phase50b_ray_decision_memory_schema_plan_noapi.json
- data/phase50b_ray_decision_memory_schema_plan_noapi_rows.jsonl
- data/phase50c_ray_decision_memory_tempdb_dryrun_noapi.json
- data/phase50c_ray_decision_memory_tempdb_dryrun_noapi_rows.jsonl
- data/phase50d_ray_decision_memory_post_audit_noapi.json
- data/phase50d_ray_decision_memory_post_audit_noapi_rows.jsonl
- data/phase50e_ray_decision_memory_canonical_binding_real_apply.json
- data/phase50e_ray_decision_memory_canonical_binding_real_apply_rows.jsonl

---

### PHASE51 — FINAL POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL, SCHEMA

Kayıt dosyaları:
- docs/phases/phase51/PHASE51A_100K_MULTI_CHAIN_RAY_STRESS_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase51/PHASE51A_100K_MULTI_CHAIN_RAY_STRESS_POST_AUDIT_NOAPI.md
- docs/phases/phase51/PHASE51A_100K_MULTI_CHAIN_RAY_STRESS_TATBIKAT_TEMPDB_NOAPI.md
- docs/phases/phase51/PHASE51A_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase51/PHASE51A_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- docs/phases/phase51/PHASE51B_BACKGROUND_INTELLIGENCE_SCHEMA_PLAN_NOAPI.md
- docs/phases/phase51/PHASE51C_BACKGROUND_INTELLIGENCE_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase51/PHASE51C_BACKGROUND_INTELLIGENCE_TEMPDB_DRYRUN_RECHECK_NOAPI.md
- docs/phases/phase51/PHASE51D_BACKGROUND_INTELLIGENCE_POST_AUDIT_NOAPI.md
- docs/phases/phase51/PHASE51E_BACKGROUND_INTELLIGENCE_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase51/PHASE51_BACKGROUND_INTELLIGENCE_OFFICER_PLAN_NOAPI.md
- docs/phases/phase51/PHASE51_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase51/PHASE51_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- data/phase51_background_intelligence_officer_plan_noapi.json
- data/phase51_background_intelligence_officer_plan_noapi_rows.jsonl
- data/phase51_final_post_audit_noapi.json
- data/phase51_final_post_audit_noapi_rows.jsonl
- data/phase51_post_push_canonical_audit_noapi.json
- data/phase51_post_push_canonical_audit_noapi_rows.jsonl
- data/phase51a_100k_multi_chain_ray_stress_canonical_binding_real_apply.json
- data/phase51a_100k_multi_chain_ray_stress_canonical_binding_real_apply_rows.jsonl
- data/phase51a_100k_multi_chain_ray_stress_post_audit_noapi.json
- data/phase51a_100k_multi_chain_ray_stress_post_audit_noapi_rows.jsonl
- data/phase51a_100k_multi_chain_ray_stress_tatbikat_tempdb_noapi.json
- data/phase51a_100k_multi_chain_ray_stress_tatbikat_tempdb_noapi_rows.jsonl
- data/phase51a_final_post_audit_noapi.json
- data/phase51a_final_post_audit_noapi_rows.jsonl
- data/phase51a_post_push_canonical_audit_noapi.json
- data/phase51a_post_push_canonical_audit_noapi_rows.jsonl
- data/phase51b_background_intelligence_schema_plan_noapi.json
- data/phase51b_background_intelligence_schema_plan_noapi_rows.jsonl
- data/phase51c_background_intelligence_tempdb_dryrun_noapi.json
- data/phase51c_background_intelligence_tempdb_dryrun_noapi_rows.jsonl
- data/phase51c_background_intelligence_tempdb_dryrun_recheck_noapi.json
- data/phase51c_background_intelligence_tempdb_dryrun_recheck_noapi_rows.jsonl
- data/phase51d_background_intelligence_post_audit_noapi.json
- data/phase51d_background_intelligence_post_audit_noapi_rows.jsonl
- data/phase51e_background_intelligence_canonical_binding_real_apply.json
- data/phase51e_background_intelligence_canonical_binding_real_apply_rows.jsonl

---

### PHASE52 — FINAL POST AUDIT NOAPI

İş türü: PLAN, DRYRUN, REAL_APPLY, AUDIT, GITHUB_SEAL, SCHEMA, RUNTIME

Kayıt dosyaları:
- docs/phases/phase52/PHASE52B_INTELLIGENCE_OFFICER_RUNTIME_SCHEMA_PLAN_NOAPI.md
- docs/phases/phase52/PHASE52C_INTELLIGENCE_OFFICER_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase52/PHASE52D_INTELLIGENCE_OFFICER_POST_AUDIT_NOAPI.md
- docs/phases/phase52/PHASE52E_INTELLIGENCE_OFFICER_CANONICAL_BINDING_REAL_APPLY.md
- docs/phases/phase52/PHASE52_5_REPO_CLUTTER_AND_CANONICAL_PATH_AUDIT_NOAPI.md
- docs/phases/phase52/PHASE52_6_UNTRACKED_ARTIFACT_CLASSIFICATION_NOAPI.md
- docs/phases/phase52/PHASE52_7_REPO_CLEAN_POLICY_PLAN_NOAPI.md
- docs/phases/phase52/PHASE52_8_UNTRACKED_COMPARE_AUDIT_NOAPI.md
- docs/phases/phase52/PHASE52_9_REPO_CLEAN_FINAL_CLASSIFICATION_NOAPI.md
- docs/phases/phase52/PHASE52_FINAL_POST_AUDIT_NOAPI.md
- docs/phases/phase52/PHASE52_INTELLIGENCE_OFFICER_RUNTIME_ARCHITECTURE_PLAN_NOAPI.md
- docs/phases/phase52/PHASE52_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- data/phase52_5_repo_clutter_and_canonical_path_audit_noapi.json
- data/phase52_5_repo_clutter_and_canonical_path_audit_noapi_rows.jsonl
- data/phase52_6_untracked_artifact_classification_noapi.json
- data/phase52_6_untracked_artifact_classification_noapi_rows.jsonl
- data/phase52_7_repo_clean_policy_plan_noapi.json
- data/phase52_7_repo_clean_policy_plan_noapi_rows.jsonl
- data/phase52_8_untracked_compare_audit_noapi.json
- data/phase52_8_untracked_compare_audit_noapi_rows.jsonl
- data/phase52_9_repo_clean_final_classification_noapi.json
- data/phase52_9_repo_clean_final_classification_noapi_rows.jsonl
- data/phase52_final_post_audit_noapi.json
- data/phase52_final_post_audit_noapi_rows.jsonl
- data/phase52_intelligence_officer_runtime_architecture_plan_noapi.json
- data/phase52_intelligence_officer_runtime_architecture_plan_noapi_rows.jsonl
- data/phase52_post_push_canonical_audit_noapi.json
- data/phase52_post_push_canonical_audit_noapi_rows.jsonl
- data/phase52b_intelligence_officer_runtime_schema_plan_noapi.json
- data/phase52b_intelligence_officer_runtime_schema_plan_noapi_rows.jsonl
- data/phase52c_intelligence_officer_tempdb_dryrun_noapi.json
- data/phase52c_intelligence_officer_tempdb_dryrun_noapi_rows.jsonl
- data/phase52d_intelligence_officer_post_audit_noapi.json
- data/phase52d_intelligence_officer_post_audit_noapi_rows.jsonl
- data/phase52e_intelligence_officer_canonical_binding_real_apply.json
- data/phase52e_intelligence_officer_canonical_binding_real_apply_rows.jsonl

---

### PHASE53 — FINAL SUMMARY GITHUB SEAL

İş türü: PLAN, REAL_APPLY, AUDIT, GITHUB_SEAL, CLOSE, SCHEMA, RUNTIME

Kayıt dosyaları:
- docs/phases/phase53/PHASE53A_01_AUTHORITY_BOUNDARY_AND_BINDING_GAP_MAP_NOAPI.md
- docs/phases/phase53/PHASE53A_02_BRIDGE_TO_CONSUMER_PAYLOAD_MASKING_CONTRACT_PLAN_NOAPI.md
- docs/phases/phase53/PHASE53A_02_BRIDGE_TO_CONSUMER_PAYLOAD_SCHEMA_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53A_02_FINAL_REVIEW_AND_GITHUB_SEAL_NOAPI.md
- docs/phases/phase53/PHASE53A_02_NEGATIVE_ACTION_TRIGGER_TEST_NOAPI.md
- docs/phases/phase53/PHASE53A_02_PANEL_DISPLAY_LANGUAGE_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53A_02_PANEL_READONLY_DISPLAY_LANGUAGE_REWRITE_PLAN_NOAPI.md
- docs/phases/phase53/PHASE53A_02_READMODEL_FIELD_AUTHORITY_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53A_02_READMODEL_FIELD_AUTHORITY_MASKING_PLAN_NOAPI.md
- docs/phases/phase53/PHASE53A_03A_REAL_APPLY_SCOPE_FREEZE_NOAPI.md
- docs/phases/phase53/PHASE53A_03B2_PANEL_DISPLAY_RULE_RESIDUAL_REPAIR_REAL.md
- docs/phases/phase53/PHASE53A_03B2_PANEL_READONLY_LANGUAGE_POST_REPAIR_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53A_03B_PANEL_READONLY_LANGUAGE_APPLY_REAL.md
- docs/phases/phase53/PHASE53A_03B_PANEL_READONLY_LANGUAGE_GITHUB_SEAL.md
- docs/phases/phase53/PHASE53A_03B_PANEL_READONLY_LANGUAGE_POST_APPLY_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53A_03C2_BRIDGE_CONSUMER_PAYLOAD_FILTER_POST_REPAIR_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53A_03C2_BRIDGE_CONSUMER_PAYLOAD_FILTER_RESIDUAL_REPAIR_REAL.md
- docs/phases/phase53/PHASE53A_03C_BRIDGE_CONSUMER_PAYLOAD_FILTER_APPLY_REAL.md
- docs/phases/phase53/PHASE53A_03C_BRIDGE_CONSUMER_PAYLOAD_FILTER_GITHUB_SEAL.md
- docs/phases/phase53/PHASE53A_03D2_FINAL_RESIDUAL_REPAIR_AND_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53A_03D2_FINAL_RESIDUAL_REPAIR_GITHUB_SEAL.md
- docs/phases/phase53/PHASE53A_03E_FINAL_CLOSURE_AND_HANDOFF_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53A_03E_FINAL_CLOSURE_GITHUB_SEAL.md
- docs/phases/phase53/PHASE53A_CANONICAL_SCOPE_AND_GAP_MAP_PLAN_NOAPI.md
- docs/phases/phase53/PHASE53A_FINAL_SUMMARY_GITHUB_SEAL.md
- docs/phases/phase53/PHASE53A_FINAL_SUMMARY_OR_NEXT_PHASE_DECISION_NOAPI.md
- docs/phases/phase53/PHASE53B2_RUNTIME_PRODUCER_RESIDUAL_REPAIR_AND_POST_REPAIR_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53B2_RUNTIME_PRODUCER_RESIDUAL_REPAIR_GITHUB_SEAL.md
- docs/phases/phase53/PHASE53B_CONSUMER_READMODEL_CONTRACT_PLAN_NOAPI.md
- docs/phases/phase53/PHASE53B_RETRY_RUNTIME_PRODUCER_ACTION_BOUNDARY_AND_E2E_TRUTH_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53B_RUNTIME_PRODUCER_ACTION_BOUNDARY_AND_E2E_TRUTH_AUDIT_GITHUB_SEAL.md
- docs/phases/phase53/PHASE53C_CONSUMER_READMODEL_CONTRACT_POST_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53D_CONSUMER_READMODEL_CONTRACT_LOCAL_ACCEPTANCE_NOAPI.md
- docs/phases/phase53/PHASE53E_FINAL_PHASE_CLOSURE_DOC_UPDATE_PLAN_NOAPI.md
- docs/phases/phase53/PHASE53F_FINAL_CANONICAL_DOC_UPDATE_LOCAL_APPLY_NOAPI.md
- docs/phases/phase53/PHASE53G_FINAL_LOCAL_POST_AUDIT_AND_TESTS_NOAPI.md
- docs/phases/phase53/PHASE53I_LOCAL_COMMIT_POST_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53J_FINAL_PUSH_APPROVAL_GATE_NOAPI.md
- docs/phases/phase53/PHASE53K_FINAL_GITHUB_PUSH_AFTER_APPROVAL.md
- docs/phases/phase53/PHASE53L_POST_PUSH_CANONICAL_AUDIT_NOAPI.md
- docs/phases/phase53/PHASE53M_FINAL_SEAL_AND_PUSH_LOCAL_RECORDS.md
- data/phase53a_01_authority_boundary_and_binding_gap_map_noapi.json
- data/phase53a_01_authority_boundary_and_binding_gap_map_noapi_rows.jsonl
- data/phase53a_02_bridge_to_consumer_payload_masking_contract_plan_noapi.json
- data/phase53a_02_bridge_to_consumer_payload_masking_contract_plan_noapi_rows.jsonl
- data/phase53a_02_bridge_to_consumer_payload_schema_audit_noapi.json
- data/phase53a_02_bridge_to_consumer_payload_schema_audit_noapi_rows.jsonl
- data/phase53a_02_final_review_and_github_seal_noapi.json
- data/phase53a_02_final_review_and_github_seal_noapi_rows.jsonl
- data/phase53a_02_negative_action_trigger_test_noapi.json
- data/phase53a_02_negative_action_trigger_test_noapi_rows.jsonl
- data/phase53a_02_panel_display_language_audit_noapi.json
- data/phase53a_02_panel_display_language_audit_noapi_rows.jsonl
- data/phase53a_02_panel_readonly_display_language_rewrite_plan_noapi.json
- data/phase53a_02_panel_readonly_display_language_rewrite_plan_noapi_rows.jsonl
- data/phase53a_02_readmodel_field_authority_audit_noapi.json
- data/phase53a_02_readmodel_field_authority_audit_noapi_rows.jsonl
- data/phase53a_02_readmodel_field_authority_masking_plan_noapi.json
- data/phase53a_02_readmodel_field_authority_masking_plan_noapi_rows.jsonl
- data/phase53a_03a_real_apply_scope_freeze_noapi.json
- data/phase53a_03a_real_apply_scope_freeze_noapi_rows.jsonl
- data/phase53a_03b2_panel_display_rule_residual_repair_real.json
- data/phase53a_03b2_panel_display_rule_residual_repair_real_rows.jsonl
- data/phase53a_03b2_panel_readonly_language_post_repair_audit_noapi.json
- data/phase53a_03b2_panel_readonly_language_post_repair_audit_noapi_rows.jsonl
- data/phase53a_03b_panel_readonly_language_apply_real.json
- data/phase53a_03b_panel_readonly_language_apply_real_rows.jsonl
- data/phase53a_03b_panel_readonly_language_github_seal.json
- data/phase53a_03b_panel_readonly_language_github_seal_rows.jsonl
- data/phase53a_03b_panel_readonly_language_post_apply_audit_noapi.json
- data/phase53a_03b_panel_readonly_language_post_apply_audit_noapi_rows.jsonl
- data/phase53a_03c2_bridge_consumer_payload_filter_post_repair_audit_noapi.json
- data/phase53a_03c2_bridge_consumer_payload_filter_post_repair_audit_noapi_rows.jsonl
- data/phase53a_03c2_bridge_consumer_payload_filter_residual_repair_real.json
- data/phase53a_03c2_bridge_consumer_payload_filter_residual_repair_real_rows.jsonl
- data/phase53a_03c_bridge_consumer_payload_filter_apply_real.json
- data/phase53a_03c_bridge_consumer_payload_filter_apply_real_rows.jsonl
- data/phase53a_03c_bridge_consumer_payload_filter_github_seal.json
- data/phase53a_03c_bridge_consumer_payload_filter_github_seal_rows.jsonl
- data/phase53a_03d2_final_residual_repair_and_audit.json
- data/phase53a_03d2_final_residual_repair_and_audit_rows.jsonl
- data/phase53a_03d2_final_residual_repair_github_seal.json
- data/phase53a_03d2_final_residual_repair_github_seal_rows.jsonl
- data/phase53a_03e_final_closure_and_handoff_audit_noapi.json
- data/phase53a_03e_final_closure_and_handoff_audit_noapi_rows.jsonl
- data/phase53a_03e_final_closure_github_seal.json
- data/phase53a_03e_final_closure_github_seal_rows.jsonl
- data/phase53a_canonical_scope_and_gap_map_plan_noapi.json
- data/phase53a_canonical_scope_and_gap_map_plan_noapi_rows.jsonl
- data/phase53a_final_summary_github_seal.json
- data/phase53a_final_summary_github_seal_rows.jsonl
- data/phase53a_final_summary_or_next_phase_decision_noapi.json
- data/phase53a_final_summary_or_next_phase_decision_noapi_rows.jsonl
- data/phase53b2_runtime_producer_residual_repair_and_post_repair_audit.json
- data/phase53b2_runtime_producer_residual_repair_and_post_repair_audit_rows.jsonl
- data/phase53b2_runtime_producer_residual_repair_github_seal.json
- data/phase53b2_runtime_producer_residual_repair_github_seal_rows.jsonl
- data/phase53b_consumer_readmodel_contract_plan_noapi.json
- data/phase53b_consumer_readmodel_contract_plan_noapi_rows.jsonl
- data/phase53b_retry_runtime_producer_action_boundary_and_e2e_truth_audit_noapi.json
- data/phase53b_retry_runtime_producer_action_boundary_and_e2e_truth_audit_noapi_rows.jsonl
- data/phase53b_runtime_producer_action_boundary_and_e2e_truth_audit_github_seal.json
- data/phase53b_runtime_producer_action_boundary_and_e2e_truth_audit_github_seal_rows.jsonl
- data/phase53c_consumer_readmodel_contract_post_audit_noapi.json
- data/phase53c_consumer_readmodel_contract_post_audit_noapi_rows.jsonl
- data/phase53d_consumer_readmodel_contract_local_acceptance_noapi.json
- data/phase53d_consumer_readmodel_contract_local_acceptance_noapi_rows.jsonl
- data/phase53e_final_phase_closure_doc_update_plan_noapi.json
- data/phase53e_final_phase_closure_doc_update_plan_noapi_rows.jsonl
- data/phase53f_final_canonical_doc_update_local_apply_noapi.json
- data/phase53f_final_canonical_doc_update_local_apply_noapi_rows.jsonl
- data/phase53g_final_local_post_audit_and_tests_noapi.json
- data/phase53g_final_local_post_audit_and_tests_noapi_rows.jsonl
- data/phase53i_local_commit_post_audit_noapi.json
- data/phase53i_local_commit_post_audit_noapi_rows.jsonl
- data/phase53j_final_push_approval_gate_noapi.json
- data/phase53j_final_push_approval_gate_noapi_rows.jsonl
- data/phase53k_final_github_push_after_approval.json
- data/phase53k_final_github_push_after_approval_rows.jsonl
- data/phase53l_post_push_canonical_audit_noapi.json
- data/phase53l_post_push_canonical_audit_noapi_rows.jsonl
- data/phase53m_final_seal_and_push_local_records.json
- data/phase53m_final_seal_and_push_local_records_rows.jsonl
- data/protocol/phase53a_01_authority_boundary_and_binding_gap_map_v1_contract_noapi.json
- data/protocol/phase53a_02_bridge_to_consumer_payload_masking_contract_plan_v1_contract_noapi.json
- data/protocol/phase53a_02_bridge_to_consumer_payload_schema_audit_v1_contract_noapi.json
- data/protocol/phase53a_02_final_review_and_github_seal_v1_contract_noapi.json
- data/protocol/phase53a_02_negative_action_trigger_test_v1_contract_noapi.json
- data/protocol/phase53a_02_panel_display_language_audit_v1_contract_noapi.json
- data/protocol/phase53a_02_panel_readonly_display_language_rewrite_plan_v1_contract_noapi.json
- data/protocol/phase53a_02_readmodel_field_authority_audit_v1_contract_noapi.json
- data/protocol/phase53a_02_readmodel_field_authority_masking_plan_v1_contract_noapi.json
- data/protocol/phase53a_03a_real_apply_scope_freeze_v1_contract_noapi.json
- data/protocol/phase53a_03b2_panel_display_rule_residual_repair_real_v1_contract.json
- data/protocol/phase53a_03b2_panel_readonly_language_post_repair_audit_v1_contract_noapi.json
- data/protocol/phase53a_03b_panel_readonly_language_apply_real_v1_contract.json
- data/protocol/phase53a_03b_panel_readonly_language_github_seal_v1_contract.json
- data/protocol/phase53a_03b_panel_readonly_language_post_apply_audit_v1_contract_noapi.json
- data/protocol/phase53a_03c2_bridge_consumer_payload_filter_post_repair_audit_v1_contract_noapi.json
- data/protocol/phase53a_03c2_bridge_consumer_payload_filter_residual_repair_real_v1_contract.json
- data/protocol/phase53a_03c_bridge_consumer_payload_filter_apply_real_v1_contract.json
- data/protocol/phase53a_03c_bridge_consumer_payload_filter_github_seal_v1_contract.json
- data/protocol/phase53a_03d2_final_residual_repair_and_audit_v1_contract.json
- data/protocol/phase53a_03d2_final_residual_repair_github_seal_v1_contract.json
- data/protocol/phase53a_03e_final_closure_and_handoff_audit_v1_contract_noapi.json
- data/protocol/phase53a_03e_final_closure_github_seal_v1_contract.json
- data/protocol/phase53a_final_summary_github_seal_v1_contract.json
- data/protocol/phase53a_final_summary_or_next_phase_decision_v1_contract_noapi.json
- data/protocol/phase53b2_runtime_producer_residual_repair_and_post_repair_audit_v1_contract.json
- data/protocol/phase53b2_runtime_producer_residual_repair_github_seal_v1_contract.json
- data/protocol/phase53b_retry_runtime_producer_action_boundary_and_e2e_truth_audit_v1_contract_noapi.json
- data/protocol/phase53b_runtime_producer_action_boundary_and_e2e_truth_audit_github_seal_v1_contract.json

---

### PHASE54 — CANONICAL NEXT SCOPE SELECTION PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, CLOSE

Kayıt dosyaları:
- docs/phases/phase54/PHASE54A_CANONICAL_NEXT_SCOPE_SELECTION_PLAN_NOAPI.md
- docs/phases/phase54/PHASE54B_READONLY_DECISION_SURFACE_CONTRACT_PLAN_NOAPI.md
- docs/phases/phase54/PHASE54C_READONLY_DECISION_SURFACE_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/phase54/PHASE54D_READONLY_DECISION_SURFACE_POST_AUDIT_NOAPI.md
- docs/phases/phase54/PHASE54E_READONLY_DECISION_SURFACE_CANONICAL_BINDING_PLAN_NOAPI.md
- docs/phases/phase54/PHASE54F_READONLY_DECISION_SURFACE_CANONICAL_DOC_UPDATE_LOCAL_APPLY_NOAPI.md
- docs/phases/phase54/PHASE54G_READONLY_DECISION_SURFACE_CANONICAL_DOC_UPDATE_POST_AUDIT_NOAPI.md
- docs/phases/phase54/PHASE54Z_READONLY_DECISION_SURFACE_FINAL_CLOSURE_NOAPI.md
- data/phase54a_canonical_next_scope_selection_plan_noapi.json
- data/phase54a_canonical_next_scope_selection_plan_noapi_rows.jsonl
- data/phase54b_readonly_decision_surface_contract_plan_noapi.json
- data/phase54b_readonly_decision_surface_contract_plan_noapi_rows.jsonl
- data/phase54c_readonly_decision_surface_tempdb_dryrun_noapi.json
- data/phase54c_readonly_decision_surface_tempdb_dryrun_noapi_rows.jsonl
- data/phase54d_readonly_decision_surface_post_audit_noapi.json
- data/phase54d_readonly_decision_surface_post_audit_noapi_rows.jsonl
- data/phase54e_readonly_decision_surface_canonical_binding_plan_noapi.json
- data/phase54e_readonly_decision_surface_canonical_binding_plan_noapi_rows.jsonl
- data/phase54f_readonly_decision_surface_canonical_doc_update_local_apply_noapi.json
- data/phase54f_readonly_decision_surface_canonical_doc_update_local_apply_noapi_rows.jsonl
- data/phase54g_readonly_decision_surface_canonical_doc_update_post_audit_noapi.json
- data/phase54g_readonly_decision_surface_canonical_doc_update_post_audit_noapi_rows.jsonl
- data/phase54z_readonly_decision_surface_final_closure_noapi.json
- data/phase54z_readonly_decision_surface_final_closure_noapi_rows.jsonl

---

### PHASE55 — NEXT CANONICAL SCOPE SELECTION PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/phases/phase55/PHASE55_NEXT_CANONICAL_SCOPE_SELECTION_PLAN_NOAPI.md
- data/phase55_next_canonical_scope_selection_plan_noapi.json
- data/phase55_next_canonical_scope_selection_plan_noapi_rows.jsonl

---

### PHASE56 — CRITICAL GAP REPAIR PLAN NOAPI

İş türü: PLAN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/phases/phase56/PHASE56B_V1_FINAL_PATH_CANONICAL_REPAIR_LOCAL_APPLY_NOAPI.md
- docs/phases/phase56/PHASE56C_V1_FINAL_PATH_CANONICAL_REPAIR_POST_AUDIT_NOAPI.md
- docs/phases/phase56/PHASE56D_V1_FINAL_PATH_CANONICAL_REPAIR_COMMIT_PUSH_VERIFY.md
- docs/phases/phase56/PHASE56Z_V1_FINAL_PATH_CANONICAL_REPAIR_FINAL_CLOSURE_NOAPI.md
- docs/phases/phase56/PHASE56_CRITICAL_GAP_REPAIR_PLAN_NOAPI.md
- data/phase56_critical_gap_repair_plan_noapi.json
- data/phase56_critical_gap_repair_plan_noapi_rows.jsonl
- data/phase56b_v1_final_path_canonical_repair_local_apply_noapi.json
- data/phase56b_v1_final_path_canonical_repair_local_apply_noapi_rows.jsonl
- data/phase56c_v1_final_path_canonical_repair_post_audit_noapi.json
- data/phase56c_v1_final_path_canonical_repair_post_audit_noapi_rows.jsonl
- data/phase56d_v1_final_path_canonical_repair_commit_push_verify.json
- data/phase56d_v1_final_path_canonical_repair_commit_push_verify_rows.jsonl
- data/phase56z_v1_final_path_canonical_repair_final_closure_noapi.json
- data/phase56z_v1_final_path_canonical_repair_final_closure_noapi_rows.jsonl

---

### PHASE57 — CANONICAL DOCUMENTATION CONSOLIDATION PLAN NOAPI

İş türü: PLAN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/phases/phase57/PHASE57B_CANONICAL_DOCUMENTATION_CONSOLIDATION_LOCAL_APPLY_NOAPI.md
- docs/phases/phase57/PHASE57C_CANONICAL_DOCUMENTATION_CONSOLIDATION_POST_AUDIT_NOAPI.md
- docs/phases/phase57/PHASE57D_CANONICAL_DOCUMENTATION_CONSOLIDATION_COMMIT_PUSH_VERIFY.md
- docs/phases/phase57/PHASE57Z_CANONICAL_DOCUMENTATION_CONSOLIDATION_FINAL_CLOSURE_NOAPI.md
- docs/phases/phase57/PHASE57_CANONICAL_DOCUMENTATION_CONSOLIDATION_PLAN_NOAPI.md
- data/phase57_canonical_documentation_consolidation_plan_noapi.json
- data/phase57_canonical_documentation_consolidation_plan_noapi_rows.jsonl
- data/phase57b_canonical_documentation_consolidation_local_apply_noapi.json
- data/phase57b_canonical_documentation_consolidation_local_apply_noapi_rows.jsonl
- data/phase57c_canonical_documentation_consolidation_post_audit_noapi.json
- data/phase57c_canonical_documentation_consolidation_post_audit_noapi_rows.jsonl
- data/phase57d_canonical_documentation_consolidation_commit_push_verify.json
- data/phase57d_canonical_documentation_consolidation_commit_push_verify_rows.jsonl
- data/phase57z_canonical_documentation_consolidation_final_closure_noapi.json
- data/phase57z_canonical_documentation_consolidation_final_closure_noapi_rows.jsonl

---

### PHASE58 — FULL SYSTEM READONLY AUDIT PLAN NOAPI

İş türü: PLAN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/phases/phase58/PHASE58B_FULL_SYSTEM_READONLY_AUDIT_EXECUTION_READONLY_NOAPI.md
- docs/phases/phase58/PHASE58C_FULL_SYSTEM_READONLY_AUDIT_POST_AUDIT_NOAPI.md
- docs/phases/phase58/PHASE58D_FULL_SYSTEM_READONLY_AUDIT_COMMIT_PUSH_VERIFY.md
- docs/phases/phase58/PHASE58Z_FULL_SYSTEM_READONLY_AUDIT_FINAL_CLOSURE_NOAPI.md
- docs/phases/phase58/PHASE58_FULL_SYSTEM_READONLY_AUDIT_PLAN_NOAPI.md
- data/phase58_full_system_readonly_audit_plan_noapi.json
- data/phase58_full_system_readonly_audit_plan_noapi_rows.jsonl
- data/phase58b_full_system_readonly_audit_execution_readonly_noapi.json
- data/phase58b_full_system_readonly_audit_execution_readonly_noapi_rows.jsonl
- data/phase58c_full_system_readonly_audit_post_audit_noapi.json
- data/phase58c_full_system_readonly_audit_post_audit_noapi_rows.jsonl
- data/phase58d_full_system_readonly_audit_commit_push_verify.json
- data/phase58d_full_system_readonly_audit_commit_push_verify_rows.jsonl
- data/phase58z_full_system_readonly_audit_final_closure_noapi.json
- data/phase58z_full_system_readonly_audit_final_closure_noapi_rows.jsonl

---

### PHASE59 — RELEASE CANDIDATE AND FREEZE PLAN NOAPI

İş türü: PLAN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/phases/phase59/PHASE59B_RELEASE_CANDIDATE_READINESS_AUDIT_READONLY_NOAPI.md
- docs/phases/phase59/PHASE59C_RELEASE_CANDIDATE_READINESS_POST_AUDIT_NOAPI.md
- docs/phases/phase59/PHASE59D_RELEASE_CANDIDATE_AND_FREEZE_COMMIT_PUSH_VERIFY.md
- docs/phases/phase59/PHASE59E_RELEASE_CANDIDATE_MINOR_DOC_MARKER_FIX_PLAN_NOAPI.md
- docs/phases/phase59/PHASE59F_RELEASE_CANDIDATE_MINOR_DOC_MARKER_FIX_LOCAL_APPLY_NOAPI.md
- docs/phases/phase59/PHASE59G_RELEASE_CANDIDATE_MINOR_DOC_MARKER_FIX_POST_AUDIT_NOAPI.md
- docs/phases/phase59/PHASE59H_RELEASE_CANDIDATE_MINOR_DOC_MARKER_FIX_COMMIT_PUSH_VERIFY.md
- docs/phases/phase59/PHASE59Z_RELEASE_CANDIDATE_AND_FREEZE_FINAL_CLOSURE_NOAPI.md
- docs/phases/phase59/PHASE59_RELEASE_CANDIDATE_AND_FREEZE_PLAN_NOAPI.md
- data/phase59_release_candidate_and_freeze_plan_noapi.json
- data/phase59_release_candidate_and_freeze_plan_noapi_rows.jsonl
- data/phase59b_release_candidate_readiness_audit_readonly_noapi.json
- data/phase59b_release_candidate_readiness_audit_readonly_noapi_rows.jsonl
- data/phase59c_release_candidate_readiness_post_audit_noapi.json
- data/phase59c_release_candidate_readiness_post_audit_noapi_rows.jsonl
- data/phase59d_release_candidate_and_freeze_commit_push_verify.json
- data/phase59d_release_candidate_and_freeze_commit_push_verify_rows.jsonl
- data/phase59e_release_candidate_minor_doc_marker_fix_plan_noapi.json
- data/phase59e_release_candidate_minor_doc_marker_fix_plan_noapi_rows.jsonl
- data/phase59f_release_candidate_minor_doc_marker_fix_local_apply_noapi.json
- data/phase59f_release_candidate_minor_doc_marker_fix_local_apply_noapi_rows.jsonl
- data/phase59g_release_candidate_minor_doc_marker_fix_post_audit_noapi.json
- data/phase59g_release_candidate_minor_doc_marker_fix_post_audit_noapi_rows.jsonl
- data/phase59h_release_candidate_minor_doc_marker_fix_commit_push_verify.json
- data/phase59h_release_candidate_minor_doc_marker_fix_commit_push_verify_rows.jsonl
- data/phase59z_release_candidate_and_freeze_final_closure_noapi.json
- data/phase59z_release_candidate_and_freeze_final_closure_noapi_rows.jsonl

---

### PHASE60 — TOKENOSKOBI V1 FINAL CLOSURE AND GITHUB SEAL

İş türü: PLAN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/phases/phase60/PHASE60B_TOKENOSKOBI_V1_FINAL_CLOSURE_READINESS_AUDIT_READONLY_NOAPI.md
- docs/phases/phase60/PHASE60C_TOKENOSKOBI_V1_FINAL_CLOSURE_POST_AUDIT_NOAPI.md
- docs/phases/phase60/PHASE60Z_TOKENOSKOBI_V1_FINAL_CLOSURE_AND_GITHUB_SEAL.md
- docs/phases/phase60/PHASE60_TOKENOSKOBI_V1_FINAL_CLOSURE_AND_GITHUB_SEAL_PLAN_NOAPI.md
- data/phase60_tokenoskobi_v1_final_closure_and_github_seal_plan_noapi.json
- data/phase60_tokenoskobi_v1_final_closure_and_github_seal_plan_noapi_rows.jsonl
- data/phase60b_tokenoskobi_v1_final_closure_readiness_audit_readonly_noapi.json
- data/phase60b_tokenoskobi_v1_final_closure_readiness_audit_readonly_noapi_rows.jsonl
- data/phase60c_tokenoskobi_v1_final_closure_post_audit_noapi.json
- data/phase60c_tokenoskobi_v1_final_closure_post_audit_noapi_rows.jsonl
- data/phase60z_tokenoskobi_v1_final_closure_and_github_seal.json
- data/phase60z_tokenoskobi_v1_final_closure_and_github_seal_rows.jsonl

---

## V2 ALMANAC - CONTROLLED CONTINUATION AİLE KAYITLARI

### V2_00 — 5 V1 FROZEN BASELINE SNAPSHOT READONLY NOAPI

İş türü: PLAN, RUNTIME

Kayıt dosyaları:
- docs/phases/v2/V2_00_5_V1_FROZEN_BASELINE_SNAPSHOT_READONLY_NOAPI.md
- docs/phases/v2/V2_00_TOKENOSKOBI_V2_PRODUCTIZATION_AND_REAL_EVIDENCE_RUNTIME_CHARTER_PLAN_NOAPI.md
- data/v2_00_5_v1_frozen_baseline_snapshot_readonly_noapi.json
- data/v2_00_5_v1_frozen_baseline_snapshot_readonly_noapi_rows.jsonl
- data/v2_00_tokenoskobi_v2_productization_and_real_evidence_runtime_charter_plan_noapi.json
- data/v2_00_tokenoskobi_v2_productization_and_real_evidence_runtime_charter_plan_noapi_rows.jsonl

---

### V2_01 — GRAY AREA PARAM REGISTRY PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/phases/v2/V2_01_GRAY_AREA_PARAM_REGISTRY_PLAN_NOAPI.md
- data/registry/v2_01_gray_area_param_registry_contract_plan_noapi.json
- data/v2_01_gray_area_param_registry_plan_noapi.json
- data/v2_01_gray_area_param_registry_plan_noapi_rows.jsonl

---

### V2_02 — CMP V1 MESSAGE PROTOCOL PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/phases/v2/V2_02A_CMP_V1_MTU_AND_FRAGMENTATION_GUARD_ADDENDUM_NOAPI.md
- docs/phases/v2/V2_02_CMP_V1_MESSAGE_PROTOCOL_PLAN_NOAPI.md
- data/v2_02_cmp_v1_message_protocol_plan_noapi.json
- data/v2_02_cmp_v1_message_protocol_plan_noapi_rows.jsonl
- data/v2_02a_cmp_v1_mtu_fragmentation_guard_addendum_noapi.json
- data/v2_02a_cmp_v1_mtu_fragmentation_guard_addendum_noapi_rows.jsonl

---

### V2_03 — HUNTER ALERT V1 SCHEMA PLAN NOAPI

İş türü: PLAN, SCHEMA

Kayıt dosyaları:
- docs/phases/v2/V2_03_HUNTER_ALERT_V1_SCHEMA_PLAN_NOAPI.md
- data/v2_03_hunter_alert_v1_schema_plan_noapi.json
- data/v2_03_hunter_alert_v1_schema_plan_noapi_rows.jsonl

---

### V2_04 — PROSECUTOR EVIDENCE REQUEST V1 SCHEMA PLAN NOAPI

İş türü: PLAN, SCHEMA

Kayıt dosyaları:
- docs/phases/v2/V2_04_PROSECUTOR_EVIDENCE_REQUEST_V1_SCHEMA_PLAN_NOAPI.md
- data/v2_04_prosecutor_evidence_request_v1_schema_plan_noapi.json
- data/v2_04_prosecutor_evidence_request_v1_schema_plan_noapi_rows.jsonl

---

### V2_05 — PROVIDER REPUTATION AND SOURCE TRUST SCORING PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/phases/v2/V2_05_PROVIDER_REPUTATION_AND_SOURCE_TRUST_SCORING_PLAN_NOAPI.md
- data/v2_05_provider_reputation_and_source_trust_scoring_plan_noapi.json
- data/v2_05_provider_reputation_and_source_trust_scoring_plan_noapi_rows.jsonl

---

### V2_06 — HUNTER PROSECUTOR TRUST ORCHESTRATOR PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/phases/v2/V2_06_HUNTER_PROSECUTOR_TRUST_ORCHESTRATOR_PLAN_NOAPI.md
- data/v2_06_hunter_prosecutor_trust_orchestrator_plan_noapi.json
- data/v2_06_hunter_prosecutor_trust_orchestrator_plan_noapi_rows.jsonl

---

### V2_07 — ORCHESTRATOR REPLAY AND SHADOW TRACE DRYRUN PLAN NOAPI

İş türü: PLAN, DRYRUN

Kayıt dosyaları:
- docs/phases/v2/V2_07_ORCHESTRATOR_REPLAY_AND_SHADOW_TRACE_DRYRUN_PLAN_NOAPI.md
- data/v2_07_orchestrator_replay_and_shadow_trace_dryrun_plan_noapi.json
- data/v2_07_orchestrator_replay_and_shadow_trace_dryrun_plan_noapi_rows.jsonl

---

### V2_08 — ORCHESTRATOR REPLAY SHADOW TRACE TEMPDB DRYRUN NOAPI

İş türü: DRYRUN

Kayıt dosyaları:
- docs/phases/v2/V2_08_ORCHESTRATOR_REPLAY_SHADOW_TRACE_TEMPDB_DRYRUN_NOAPI.md
- data/v2_08_orchestrator_replay_shadow_trace_tempdb_dryrun_noapi.json
- data/v2_08_orchestrator_replay_shadow_trace_tempdb_dryrun_noapi_rows.jsonl

---

### V2_09 — ORCHESTRATOR TEMPDB POST PUSH AUDIT NOAPI

İş türü: DRYRUN, AUDIT, GITHUB_SEAL

Kayıt dosyaları:
- docs/phases/v2/V2_09_ORCHESTRATOR_TEMPDB_POST_PUSH_AUDIT_NOAPI.md
- data/v2_09_orchestrator_tempdb_post_push_audit_noapi.json
- data/v2_09_orchestrator_tempdb_post_push_audit_noapi_rows.jsonl

---

### V2_10 — REAL EVIDENCE RUNTIME READONLY ADAPTER PLAN NOAPI

İş türü: PLAN, RUNTIME

Kayıt dosyaları:
- docs/phases/v2/V2_10_REAL_EVIDENCE_RUNTIME_READONLY_ADAPTER_PLAN_NOAPI.md
- data/v2_10_real_evidence_runtime_readonly_adapter_plan_noapi.json
- data/v2_10_real_evidence_runtime_readonly_adapter_plan_noapi_rows.jsonl

---

### V2_11 — REAL EVIDENCE ADAPTER TEMPDB DRYRUN NOAPI

İş türü: DRYRUN

Kayıt dosyaları:
- docs/phases/v2/V2_11_FIX1_ADVERSARIAL_SOURCE_FIREWALL_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/v2/V2_11_FIX2_STRESS_FAILURE_INJECTION_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/v2/V2_11_REAL_EVIDENCE_ADAPTER_TEMPDB_DRYRUN_NOAPI.md
- data/v2_11_fix1_adversarial_source_firewall_tempdb_dryrun_noapi.json
- data/v2_11_fix1_adversarial_source_firewall_tempdb_dryrun_noapi_rows.jsonl
- data/v2_11_fix2_stress_failure_injection_tempdb_dryrun_noapi.json
- data/v2_11_fix2_stress_failure_injection_tempdb_dryrun_noapi_rows.jsonl
- data/v2_11_real_evidence_adapter_tempdb_dryrun_noapi.json
- data/v2_11_real_evidence_adapter_tempdb_dryrun_noapi_rows.jsonl

---

### V2_12 — REAL EVIDENCE ADAPTER POST PUSH AUDIT NOAPI

İş türü: AUDIT, GITHUB_SEAL

Kayıt dosyaları:
- docs/phases/v2/V2_12_REAL_EVIDENCE_ADAPTER_POST_PUSH_AUDIT_NOAPI.md
- data/v2_12_real_evidence_adapter_post_push_audit_noapi.json
- data/v2_12_real_evidence_adapter_post_push_audit_noapi_rows.jsonl

---

### V2_13 — FIX1 PRODUCTIZATION SURVIVAL GUARDS PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/phases/v2/V2_13_FIX1_PRODUCTIZATION_SURVIVAL_GUARDS_PLAN_NOAPI.md
- docs/phases/v2/V2_13_REAL_EVIDENCE_ADAPTER_PRODUCTIZATION_PLAN_NOAPI.md
- data/v2_13_fix1_productization_survival_guards_plan_noapi.json
- data/v2_13_fix1_productization_survival_guards_plan_noapi_rows.jsonl
- data/v2_13_real_evidence_adapter_productization_plan_noapi.json
- data/v2_13_real_evidence_adapter_productization_plan_noapi_rows.jsonl

---

### V2_14 — PRODUCTIZATION POST PUSH AUDIT NOAPI

İş türü: AUDIT, GITHUB_SEAL

Kayıt dosyaları:
- docs/phases/v2/V2_14_PRODUCTIZATION_POST_PUSH_AUDIT_NOAPI.md
- data/v2_14_productization_post_push_audit_noapi.json
- data/v2_14_productization_post_push_audit_noapi_rows.jsonl

---

### V2_15 — REAL PROVIDER GENESIS CONFIG PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/phases/v2/V2_15_REAL_PROVIDER_GENESIS_CONFIG_PLAN_NOAPI.md
- data/v2_15_real_provider_genesis_config_plan_noapi.json
- data/v2_15_real_provider_genesis_config_plan_noapi_rows.jsonl

---

### V2_16 — REAL PROVIDER GENESIS CONFIG POST PUSH AUDIT NOAPI

İş türü: AUDIT, GITHUB_SEAL

Kayıt dosyaları:
- docs/phases/v2/V2_16_REAL_PROVIDER_GENESIS_CONFIG_POST_PUSH_AUDIT_NOAPI.md
- data/v2_16_real_provider_genesis_config_post_push_audit_noapi.json
- data/v2_16_real_provider_genesis_config_post_push_audit_noapi_rows.jsonl

---

### V2_17 — PROVIDER SELECTION AND BUDGET POLICY PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/phases/v2/V2_17_FIX1_100K_TOKEN_BLITZKRIEG_STRESS_POLICY_PLAN_NOAPI.md
- docs/phases/v2/V2_17_PROVIDER_SELECTION_AND_BUDGET_POLICY_PLAN_NOAPI.md
- data/v2_17_fix1_100k_token_blitzkrieg_stress_policy_plan_noapi.json
- data/v2_17_fix1_100k_token_blitzkrieg_stress_policy_plan_noapi_rows.jsonl
- data/v2_17_provider_selection_and_budget_policy_plan_noapi.json
- data/v2_17_provider_selection_and_budget_policy_plan_noapi_rows.jsonl

---

### V2_18 — HEAD TREE ARTIFACT DISCOVERY NOAPI

İş türü: PLAN, DRYRUN, AUDIT, GITHUB_SEAL

Kayıt dosyaları:
- docs/phases/v2/V2_18A_100K_BLITZKRIEG_FULL_FORENSIC_LIFECYCLE_SHADOW_EXECUTION_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/v2/V2_18A_EVIDENTIARY_PATH_RECONCILIATION_NOAPI.md
- docs/phases/v2/V2_18A_FIX1_AND_FP_TRACE_DEDUP_RECHECK_EVIDENCE_SEAL.md
- docs/phases/v2/V2_18A_FIX1_FP_TRACE_DEDUP_RECHECK_PATH_CORRECTION_NOAPI.md
- docs/phases/v2/V2_18A_FIX1_REALISM_HARDENING_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/v2/V2_18A_HEAD_TREE_ARTIFACT_DISCOVERY_NOAPI.md
- docs/phases/v2/V2_18B_100K_TOKEN_BLITZKRIEG_POST_AUDIT_AND_SURVIVAL_REPORT_NOAPI.md
- docs/phases/v2/V2_18B_FIX1_NETWORK_STRESS_DRYRUN_AND_POST_AUDIT_SEAL.md
- docs/phases/v2/V2_18B_FIX1_NETWORK_STRESS_TEST_PLAN_COMMIT_PUSH_SEAL.md
- docs/phases/v2/V2_18B_FIX1_NETWORK_STRESS_TEST_PLAN_NOAPI.md
- docs/phases/v2/V2_18B_FIX1_NETWORK_STRESS_TEST_POST_AUDIT_NOAPI.md
- docs/phases/v2/V2_18B_FIX1_NETWORK_STRESS_TEST_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/v2/V2_18C_BACKPRESSURE_THRESHOLD_CALIBRATION_PLAN_FIX1_SEAL.md
- docs/phases/v2/V2_18C_BACKPRESSURE_THRESHOLD_CALIBRATION_PLAN_NOAPI_FIX1_BASELINE_RECONCILIATION.md
- docs/phases/v2/V2_18C_FIX1_BACKPRESSURE_THRESHOLD_RETUNE_DRYRUN_AND_POST_AUDIT_SEAL.md
- docs/phases/v2/V2_18C_FIX1_BACKPRESSURE_THRESHOLD_RETUNE_POST_AUDIT_NOAPI.md
- docs/phases/v2/V2_18C_FIX1_BACKPRESSURE_THRESHOLD_RETUNE_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/v2/V2_18D_OPPORTUNITY_COST_AND_MISSED_SIGNAL_REPLAY_PLAN_NOAPI.md
- docs/phases/v2/V2_18D_OPPORTUNITY_COST_AND_MISSED_SIGNAL_REPLAY_POST_AUDIT_NOAPI.md
- docs/phases/v2/V2_18D_OPPORTUNITY_COST_AND_MISSED_SIGNAL_REPLAY_SEAL.md
- docs/phases/v2/V2_18D_OPPORTUNITY_COST_AND_MISSED_SIGNAL_REPLAY_TEMPDB_DRYRUN_NOAPI.md
- docs/phases/v2/V2_18_100K_TOKEN_BLITZKRIEG_TEMPDB_DRYRUN_PLAN_NOAPI.md
- data/protocol/v2_18a_evidentiary_path_reconciliation_v1_contract_noapi.json
- data/protocol/v2_18a_fix1_and_fp_trace_dedup_recheck_evidence_seal_v1_contract.json
- data/protocol/v2_18a_fix1_fp_trace_dedup_recheck_path_correction_v1_contract_noapi.json
- data/protocol/v2_18a_head_tree_artifact_discovery_v1_contract_noapi.json
- data/protocol/v2_18b_fix1_network_stress_dryrun_and_post_audit_seal_v1_contract.json
- data/protocol/v2_18b_fix1_network_stress_test_plan_v1_contract_noapi.json
- data/protocol/v2_18b_fix1_network_stress_test_post_audit_v1_contract_noapi.json
- data/protocol/v2_18b_fix1_network_stress_test_tempdb_dryrun_v1_contract_noapi.json
- data/protocol/v2_18c_backpressure_threshold_calibration_plan_fix1_baseline_reconciliation_v1_contract_noapi.json
- data/protocol/v2_18c_backpressure_threshold_calibration_plan_fix1_seal_v1_contract.json
- data/protocol/v2_18c_fix1_backpressure_threshold_retune_dryrun_and_post_audit_seal_v1_contract.json
- data/protocol/v2_18c_fix1_backpressure_threshold_retune_post_audit_v1_contract_noapi.json
- data/protocol/v2_18c_fix1_backpressure_threshold_retune_tempdb_dryrun_v1_contract_noapi.json
- data/protocol/v2_18d_opportunity_cost_and_missed_signal_replay_plan_v1_contract_noapi.json
- data/protocol/v2_18d_opportunity_cost_and_missed_signal_replay_post_audit_v1_contract_noapi.json
- data/protocol/v2_18d_opportunity_cost_and_missed_signal_replay_seal_v1_contract.json
- data/protocol/v2_18d_opportunity_cost_and_missed_signal_replay_tempdb_dryrun_v1_contract_noapi.json
- data/v2_18_100k_token_blitzkrieg_tempdb_dryrun_plan_noapi.json
- data/v2_18_100k_token_blitzkrieg_tempdb_dryrun_plan_noapi_rows.jsonl
- data/v2_18a_100k_blitzkrieg_full_forensic_lifecycle_shadow_execution_tempdb_dryrun_noapi.json
- data/v2_18a_100k_blitzkrieg_full_forensic_lifecycle_shadow_execution_tempdb_dryrun_noapi_rows.jsonl
- data/v2_18a_evidentiary_path_reconciliation_noapi.json
- data/v2_18a_evidentiary_path_reconciliation_noapi_rows.jsonl
- data/v2_18a_fix1_and_fp_trace_dedup_recheck_evidence_seal.json
- data/v2_18a_fix1_and_fp_trace_dedup_recheck_evidence_seal_rows.jsonl
- data/v2_18a_fix1_fp_trace_dedup_recheck_path_correction_noapi.json
- data/v2_18a_fix1_fp_trace_dedup_recheck_path_correction_noapi_rows.jsonl
- data/v2_18a_fix1_realism_hardening_tempdb_dryrun_noapi.json
- data/v2_18a_fix1_realism_hardening_tempdb_dryrun_noapi_rows.jsonl
- data/v2_18a_head_tree_artifact_discovery_noapi.json
- data/v2_18a_head_tree_artifact_discovery_noapi_rows.jsonl
- data/v2_18b_100k_token_blitzkrieg_post_audit_and_survival_report_noapi.json
- data/v2_18b_100k_token_blitzkrieg_post_audit_and_survival_report_noapi_rows.jsonl
- data/v2_18b_fix1_network_stress_dryrun_and_post_audit_seal.json
- data/v2_18b_fix1_network_stress_dryrun_and_post_audit_seal_rows.jsonl
- data/v2_18b_fix1_network_stress_test_plan_commit_push_seal.json
- data/v2_18b_fix1_network_stress_test_plan_commit_push_seal_rows.jsonl
- data/v2_18b_fix1_network_stress_test_plan_noapi.json
- data/v2_18b_fix1_network_stress_test_plan_noapi_rows.jsonl
- data/v2_18b_fix1_network_stress_test_post_audit_noapi.json
- data/v2_18b_fix1_network_stress_test_post_audit_noapi_rows.jsonl
- data/v2_18b_fix1_network_stress_test_tempdb_dryrun_noapi.json
- data/v2_18b_fix1_network_stress_test_tempdb_dryrun_noapi_rows.jsonl
- data/v2_18c_backpressure_threshold_calibration_plan_fix1_baseline_reconciliation_noapi.json
- data/v2_18c_backpressure_threshold_calibration_plan_fix1_baseline_reconciliation_noapi_rows.jsonl
- data/v2_18c_backpressure_threshold_calibration_plan_fix1_seal.json
- data/v2_18c_backpressure_threshold_calibration_plan_fix1_seal_rows.jsonl
- data/v2_18c_fix1_backpressure_threshold_retune_dryrun_and_post_audit_seal.json
- data/v2_18c_fix1_backpressure_threshold_retune_dryrun_and_post_audit_seal_rows.jsonl
- data/v2_18c_fix1_backpressure_threshold_retune_post_audit_noapi.json
- data/v2_18c_fix1_backpressure_threshold_retune_post_audit_noapi_rows.jsonl
- data/v2_18c_fix1_backpressure_threshold_retune_tempdb_dryrun_noapi.json
- data/v2_18c_fix1_backpressure_threshold_retune_tempdb_dryrun_noapi_rows.jsonl
- data/v2_18d_opportunity_cost_and_missed_signal_replay_plan_noapi.json
- data/v2_18d_opportunity_cost_and_missed_signal_replay_plan_noapi_rows.jsonl
- data/v2_18d_opportunity_cost_and_missed_signal_replay_post_audit_noapi.json
- data/v2_18d_opportunity_cost_and_missed_signal_replay_post_audit_noapi_rows.jsonl
- data/v2_18d_opportunity_cost_and_missed_signal_replay_seal.json
- data/v2_18d_opportunity_cost_and_missed_signal_replay_seal_rows.jsonl
- data/v2_18d_opportunity_cost_and_missed_signal_replay_tempdb_dryrun_noapi.json
- data/v2_18d_opportunity_cost_and_missed_signal_replay_tempdb_dryrun_noapi_rows.jsonl

---

### V2_19 — REAL MARKET RISK ANALYSIS READONLY SEAL

İş türü: PLAN, DRYRUN, AUDIT, GITHUB_SEAL

Kayıt dosyaları:
- docs/phases/v2/V2_19_REAL_MARKET_RISK_ANALYSIS_READONLY_PLAN_NOAPI.md
- docs/phases/v2/V2_19_REAL_MARKET_RISK_ANALYSIS_READONLY_POST_AUDIT_NOAPI.md
- docs/phases/v2/V2_19_REAL_MARKET_RISK_ANALYSIS_READONLY_SEAL.md
- docs/phases/v2/V2_19_REAL_MARKET_RISK_ANALYSIS_READONLY_TEMPDB_DRYRUN_NOAPI.md
- data/protocol/v2_19_real_market_risk_analysis_readonly_plan_v1_contract_noapi.json
- data/protocol/v2_19_real_market_risk_analysis_readonly_post_audit_v1_contract_noapi.json
- data/protocol/v2_19_real_market_risk_analysis_readonly_seal_v1_contract.json
- data/protocol/v2_19_real_market_risk_analysis_readonly_tempdb_dryrun_v1_contract_noapi.json
- data/v2_19_real_market_risk_analysis_readonly_plan_noapi.json
- data/v2_19_real_market_risk_analysis_readonly_plan_noapi_rows.jsonl
- data/v2_19_real_market_risk_analysis_readonly_post_audit_noapi.json
- data/v2_19_real_market_risk_analysis_readonly_post_audit_noapi_rows.jsonl
- data/v2_19_real_market_risk_analysis_readonly_seal.json
- data/v2_19_real_market_risk_analysis_readonly_seal_rows.jsonl
- data/v2_19_real_market_risk_analysis_readonly_tempdb_dryrun_noapi.json
- data/v2_19_real_market_risk_analysis_readonly_tempdb_dryrun_noapi_rows.jsonl

---

### V2_20 — REAL READONLY PROVIDER FETCH POLICY SEAL

İş türü: PLAN, DRYRUN, AUDIT, GITHUB_SEAL

Kayıt dosyaları:
- docs/phases/v2/V2_20_REAL_READONLY_PROVIDER_FETCH_POLICY_PLAN_NOAPI.md
- docs/phases/v2/V2_20_REAL_READONLY_PROVIDER_FETCH_POLICY_POST_AUDIT_NOAPI.md
- docs/phases/v2/V2_20_REAL_READONLY_PROVIDER_FETCH_POLICY_SEAL.md
- docs/phases/v2/V2_20_REAL_READONLY_PROVIDER_FETCH_POLICY_TEMPDB_DRYRUN_NOAPI.md
- data/protocol/v2_20_real_readonly_provider_fetch_policy_plan_v1_contract_noapi.json
- data/protocol/v2_20_real_readonly_provider_fetch_policy_post_audit_v1_contract_noapi.json
- data/protocol/v2_20_real_readonly_provider_fetch_policy_seal_v1_contract.json
- data/protocol/v2_20_real_readonly_provider_fetch_policy_tempdb_dryrun_v1_contract_noapi.json
- data/v2_20_real_readonly_provider_fetch_policy_plan_noapi.json
- data/v2_20_real_readonly_provider_fetch_policy_plan_noapi_rows.jsonl
- data/v2_20_real_readonly_provider_fetch_policy_post_audit_noapi.json
- data/v2_20_real_readonly_provider_fetch_policy_post_audit_noapi_rows.jsonl
- data/v2_20_real_readonly_provider_fetch_policy_seal.json
- data/v2_20_real_readonly_provider_fetch_policy_seal_rows.jsonl
- data/v2_20_real_readonly_provider_fetch_policy_tempdb_dryrun_noapi.json
- data/v2_20_real_readonly_provider_fetch_policy_tempdb_dryrun_noapi_rows.jsonl

---

### V2_23 — INTELLIGENCE CORE SOCIAL LAUNCH WAR ROOM DOCTRINE PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- data/v2_23_intelligence_core_social_launch_war_room_doctrine_plan_noapi.json
- data/v2_23_intelligence_core_social_launch_war_room_doctrine_plan_noapi_rows.jsonl

---

### V2_24 — DECISION AUDIT LOG CONTRACT PLAN NOAPI

İş türü: PLAN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/v2_24_decision_audit_log_contract_plan_noapi.json
- data/v2_24_decision_audit_log_contract_schema_plan_noapi.json
- data/v2_24_decision_audit_log_contract_test_vectors_noapi.jsonl

---

### V2_25 — BLIND TRAINING CONTRACT PLAN NOAPI

İş türü: PLAN, SCHEMA

Kayıt dosyaları:
- data/v2_25_blind_training_contract_plan_noapi.json
- data/v2_25_statistical_signal_schema_and_weight_validation_doctrine_plan_noapi.json
- data/v2_25_statistical_signal_schema_plan_noapi.json
- data/v2_25_weight_validation_doctrine_plan_noapi.json

---

### V2_26 — OUTCOME LEAKAGE GUARD PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- data/v2_26_historical_correlation_source_contract_plan_noapi.json
- data/v2_26_historical_event_contract_plan_noapi.json
- data/v2_26_historical_source_contract_plan_noapi.json
- data/v2_26_outcome_leakage_guard_plan_noapi.json
- data/v2_26_source_classification_matrix_plan_noapi.json

---

### V2_27 — HISTORICAL CORRELATION TEMPDB CASES NOAPI

İş türü: DRYRUN

Kayıt dosyaları:
- data/v2_27_historical_correlation_tempdb_cases_noapi.jsonl
- data/v2_27_historical_correlation_tempdb_dryrun_noapi.json
- data/v2_27_historical_correlation_tempdb_results_noapi.jsonl

---

### V2_28 — HISTORICAL CORRELATION TEMPDB POST AUDIT NOAPI

İş türü: DRYRUN, AUDIT

Kayıt dosyaları:
- data/v2_28_historical_correlation_tempdb_post_audit_noapi.json
- data/v2_28_historical_correlation_tempdb_post_audit_rows_noapi.jsonl

---

### V2_29 — HISTORICAL SCHEMA BINDING PLAN NOAPI

İş türü: PLAN, AUDIT, SCHEMA

Kayıt dosyaları:
- data/v2_29_historical_correlation_schema_binding_post_plan_audit_noapi.json
- data/v2_29_historical_correlation_schema_binding_post_plan_audit_rows_noapi.jsonl
- data/v2_29_historical_live_path_guard_plan_noapi.json
- data/v2_29_historical_migration_guard_plan_noapi.json
- data/v2_29_historical_relationship_map_plan_noapi.json
- data/v2_29_historical_schema_binding_plan_noapi.json
- data/v2_29_historical_table_contracts_plan_noapi.json
- data/v2_29_stress_test_ready_schema_contract_plan_noapi.json

---

### V2_30 — LATENCY SUMMARY NOAPI

İş türü: AUDIT

Kayıt dosyaları:
- data/v2_30_audit_bottleneck_results_noapi.jsonl
- data/v2_30_echo_chamber_results_noapi.jsonl
- data/v2_30_flash_crash_50k_results_noapi.jsonl
- data/v2_30_hard_block_summary_noapi.json
- data/v2_30_latency_summary_noapi.json
- data/v2_30_stress_test_and_reaction_simulation_noapi.json
- data/v2_30_stress_test_and_reaction_simulation_post_audit_noapi.json
- data/v2_30_stress_test_and_reaction_simulation_post_audit_rows_noapi.jsonl
- data/v2_30_stress_test_rows_noapi.jsonl

---

### V2_31 — NO FIXED WEIGHT GUARD PLAN NOAPI

İş türü: PLAN, AUDIT

Kayıt dosyaları:
- data/v2_31_blind_validation_protocol_plan_noapi.json
- data/v2_31_candidate_formula_contract_plan_noapi.json
- data/v2_31_final_score_candidate_formula_plan_noapi.json
- data/v2_31_mathematical_scoring_engine_contract_post_plan_audit_noapi.json
- data/v2_31_mathematical_scoring_engine_contract_post_plan_audit_rows_noapi.jsonl
- data/v2_31_no_fixed_weight_guard_plan_noapi.json
- data/v2_31_scoring_audit_contract_plan_noapi.json
- data/v2_31_trust_evidence_factor_contract_plan_noapi.json
- data/v2_31_v2_32_v2_33_reserved_roadmap_plan_noapi.json
- data/v2_31_vurkac_score_candidate_formula_plan_noapi.json

---

### V2_32 — EXECUTION GATE MATRIX PLAN NOAPI

İş türü: PLAN, AUDIT

Kayıt dosyaları:
- data/v2_32_emergency_kill_switch_contract_plan_noapi.json
- data/v2_32_execution_authority_doctrine_plan_noapi.json
- data/v2_32_execution_gate_matrix_plan_noapi.json
- data/v2_32_execution_risk_limits_plan_noapi.json
- data/v2_32_human_approval_protocol_plan_noapi.json
- data/v2_32_hybrid_execution_authority_doctrine_post_plan_audit_noapi.json
- data/v2_32_hybrid_execution_authority_doctrine_post_plan_audit_rows_noapi.jsonl
- data/v2_32_order_lifecycle_contract_plan_noapi.json
- data/v2_32_v2_33_penetration_test_reserved_roadmap_plan_noapi.json
- data/v2_32_wallet_authority_lock_plan_noapi.json

---

### V2_33 — RULE FUZZING TEST PLAN NOAPI

İş türü: PLAN, AUDIT

Kayıt dosyaları:
- data/v2_33_attack_surface_matrix_plan_noapi.json
- data/v2_33_audit_evasion_test_plan_noapi.json
- data/v2_33_authority_bypass_test_plan_noapi.json
- data/v2_33_isolation_and_non_destructive_safety_contract_noapi.json
- data/v2_33_leakage_mutation_test_plan_noapi.json
- data/v2_33_logic_poisoning_test_plan_noapi.json
- data/v2_33_resource_exhaustion_test_plan_noapi.json
- data/v2_33_rule_fuzzing_test_plan_noapi.json
- data/v2_33_security_forensic_penetration_test_plan_noapi.json
- data/v2_33_security_forensic_penetration_test_post_plan_audit_noapi.json
- data/v2_33_security_forensic_penetration_test_post_plan_audit_rows_noapi.jsonl

---

### V2_34 — DETERMINISM CONTRACT PLAN NOAPI

İş türü: PLAN, DRYRUN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- data/v2_34_determinism_contract_plan_noapi.json
- data/v2_34_error_handling_contract_plan_noapi.json
- data/v2_34_formula_dryrun_latency_test_plan_noapi.json
- data/v2_34_formula_execution_contract_plan_noapi.json
- data/v2_34_latency_benchmark_contract_plan_noapi.json
- data/v2_34_no_success_claim_boundary_plan_noapi.json
- data/v2_34_scale_buckets_contract_plan_noapi.json
- data/v2_34_synthetic_input_contract_plan_noapi.json
- data/v2_34a_drift_detection_contract_plan_noapi.json
- data/v2_34a_fixed_point_integer_math_contract_plan_noapi.json
- data/v2_34a_floating_point_drift_precision_bucket_hardening_plan_noapi.json
- data/v2_34a_floating_point_drift_precision_bucket_hardening_post_plan_audit_noapi.json
- data/v2_34a_floating_point_drift_precision_bucket_hardening_post_plan_audit_rows_noapi.jsonl
- data/v2_34a_precision_bucket_contract_plan_noapi.json
- data/v2_34a_precision_fail_closed_contract_plan_noapi.json
- data/v2_34a_rounding_policy_contract_plan_noapi.json
- data/v2_34a_speed_never_down_contract_plan_noapi.json
- data/v2_34b_commit_json_reseal_and_post_push_seal_fix_noapi.json
- data/v2_34b_critical_fast_lane_contract_plan_noapi.json
- data/v2_34b_degraded_mode_observation_contract_plan_noapi.json
- data/v2_34b_dos_resilience_dynamic_threshold_degraded_mode_plan_noapi.json
- data/v2_34b_dos_resilience_dynamic_threshold_degraded_mode_post_plan_audit_current_head_noapi.json
- data/v2_34b_dos_resilience_dynamic_threshold_degraded_mode_post_plan_audit_current_head_rows_noapi.jsonl
- data/v2_34b_dos_resilience_dynamic_threshold_degraded_mode_post_plan_audit_noapi.json
- data/v2_34b_dos_resilience_dynamic_threshold_degraded_mode_post_plan_audit_rows_noapi.jsonl
- data/v2_34b_dynamic_threshold_contract_plan_noapi.json
- data/v2_34b_final_post_push_seal_on_reseal_head_noapi.json
- data/v2_34b_git_commit_and_push_current_head_noapi.json
- data/v2_34b_git_truth_based_final_close_noapi.json
- data/v2_34b_logic_poisoning_resilience_bridge_plan_noapi.json
- data/v2_34b_noise_bucket_rate_limit_dedup_contract_plan_noapi.json
- data/v2_34b_plan_report_latest_reseal_current_head_noapi.json
- data/v2_34b_post_push_seal_current_head_noapi.json
- data/v2_34b_priority_audit_queue_contract_plan_noapi.json
- data/v2_34b_rebased_repo_state_reconciliation_audit_noapi.json
- data/v2_34b_scoped_circuit_breaker_contract_plan_noapi.json
- data/v2_34c_adversarial_conflict_marker_contract_plan_noapi.json
- data/v2_34c_fast_lane_evidence_cross_check_contract_plan_noapi.json
- data/v2_34c_fast_lane_poisoning_protection_plan_noapi.json
- data/v2_34c_fast_lane_poisoning_protection_post_plan_audit_noapi.json
- data/v2_34c_fast_lane_poisoning_protection_post_plan_audit_rows_noapi.jsonl
- data/v2_34c_fast_lane_poisoning_protection_reconcile_audit_noapi.json
- data/v2_34c_multi_source_independence_contract_plan_noapi.json
- data/v2_34c_poisoned_source_quarantine_contract_plan_noapi.json
- data/v2_34c_poisoning_fail_closed_execution_contract_plan_noapi.json
- data/v2_34c_post_push_reseal_on_current_head_noapi.json
- data/v2_34c_reconcile_dirty_v34b_close_json_include_and_reseal_noapi.json
- data/v2_34c_reseal_json_fix_and_final_close_noapi.json
- data/v2_34c_source_reputation_decay_contract_plan_noapi.json
- data/v2_34c_truth_path_hashing_contract_plan_noapi.json

---

### V2_35 — POST PUSH SEAL NOAPI

İş türü: PLAN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- data/v2_35_archive_allowlist_and_v2_34b_current_head_rerun_fix_noapi.json
- data/v2_35_archive_allowlist_normalize_fix_noapi.json
- data/v2_35_dirty_trace_safe_archive_then_rerun_v2_34b_current_head_noapi.json
- data/v2_35_duplicate_trace_review_include_audit_and_proceed_noapi.json
- data/v2_35_duplicate_trace_review_noapi.json
- data/v2_35_git_commit_and_push_noapi.json
- data/v2_35_git_truth_based_commit_and_push_seal_noapi.json
- data/v2_35_git_truth_based_post_plan_audit_close_noapi.json
- data/v2_35_human_approval_integrity_archive_reopen_audit_noapi.json
- data/v2_35_human_approval_integrity_post_plan_audit_noapi.json
- data/v2_35_post_push_seal_noapi.json

---

### V2_36 — POST PUSH SEAL NOAPI

İş türü: PLAN, AUDIT, GITHUB_SEAL

Kayıt dosyaları:
- docs/v2/V2_36_HUMAN_APPROVAL_INTEGRITY_TO_EXECUTION_BOUNDARY_BINDING_PLAN_NOAPI.md
- data/v2_36_all_git_verify_dirty_jsons_include_and_push_noapi.json
- data/v2_36_dirty_retry_json_include_and_plan_push_seal_noapi.json
- data/v2_36_final_seal_json_include_and_git_verify_retry_noapi.json
- data/v2_36_git_commit_and_push_noapi.json
- data/v2_36_git_verify_dirty_jsons_include_and_push_noapi.json
- data/v2_36_human_approval_integrity_to_execution_boundary_binding_plan_noapi.json
- data/v2_36_human_approval_integrity_to_execution_boundary_binding_plan_noapi_rows.jsonl
- data/v2_36_human_approval_integrity_to_execution_boundary_binding_post_plan_audit_noapi.json
- data/v2_36_metadata_dirty_parser_fix_and_git_verify_seal_noapi.json
- data/v2_36_next_approved_phase_or_canonical_roadmap_selection_audit_noapi.json
- data/v2_36_plan_push_retry_and_seal_noapi.json
- data/v2_36_porcelain_strip_safe_metadata_seal_noapi.json
- data/v2_36_post_plan_audit_local_commit_push_and_metadata_seal_noapi.json
- data/v2_36_post_push_seal_dirty_verify_json_include_noapi.json
- data/v2_36_post_push_seal_noapi.json
- data/v2_36_push_seal_json_include_and_post_plan_audit_retry_noapi.json
- data/v2_36_selection_json_include_and_plan_retry_noapi.json
- data/v2_36_trace_classification_and_v35_seal_json_include_noapi.json
- data/v2_36_two_local_commits_push_and_final_seal_noapi.json

---

### V2_37 — SHADOW OBSERVATION EVENT CONTRACT LOCAL NOAPI

İş türü: PLAN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_37A_SEMANTIC_NOISE_ATTACK_CLASSIFICATION_AND_CONFIDENCE_MODEL_LOCAL_NOAPI.md
- docs/v2/V2_37B_DYNAMIC_THRESHOLD_AND_SECURITY_FLOOR_MODEL_LOCAL_NOAPI.md
- docs/v2/V2_37C_SHADOW_OBSERVATION_EVENT_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_37D_NOISE_ATTACK_DISCRIMINATION_LOCAL_REVIEW_NOAPI.md
- docs/v2/V2_37_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_37_NOISE_ATTACK_DISCRIMINATION_AND_SHADOW_OBSERVATION_PLAN_NOAPI.md
- docs/v2/V2_37_NOISE_ATTACK_DISCRIMINATION_AND_SHADOW_OBSERVATION_POST_PLAN_AUDIT_NOAPI.md
- data/v2_37_final_close_local_and_single_github_push_noapi.json
- data/v2_37_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_37_noise_attack_discrimination_and_shadow_observation_plan_noapi.json
- data/v2_37_noise_attack_discrimination_and_shadow_observation_plan_noapi_rows.jsonl
- data/v2_37_noise_attack_discrimination_and_shadow_observation_post_plan_audit_noapi.json
- data/v2_37_noise_attack_discrimination_and_shadow_observation_post_plan_audit_noapi_rows.jsonl
- data/v2_37a_semantic_noise_attack_classification_and_confidence_model_local_noapi.json
- data/v2_37a_semantic_noise_attack_classification_and_confidence_model_local_noapi_rows.jsonl
- data/v2_37b_dynamic_threshold_and_security_floor_model_local_noapi.json
- data/v2_37b_dynamic_threshold_and_security_floor_model_local_noapi_rows.jsonl
- data/v2_37c_shadow_observation_event_contract_local_noapi.json
- data/v2_37c_shadow_observation_event_contract_local_noapi_rows.jsonl
- data/v2_37d_noise_attack_discrimination_local_review_noapi.json
- data/v2_37d_noise_attack_discrimination_local_review_noapi_rows.jsonl

---

### V2_38 — REPLAY HARNESS DRYRUN RESULTS

İş türü: PLAN, DRYRUN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_38A_SYNTHETIC_EVENT_SET_AND_EXPECTED_CLASSIFICATION_LOCAL_NOAPI.md
- docs/v2/V2_38B1_REPLAY_HARNESS_ACTION_MATRIX_AND_PROMOTION_RULE_ADJUST_LOCAL_NOAPI.md
- docs/v2/V2_38B_REPLAY_HARNESS_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_38C_REPLAY_HARNESS_LOCAL_REVIEW_NOAPI.md
- docs/v2/V2_38_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_38_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- docs/v2/V2_38_SHADOW_OBSERVATION_CLASSIFICATION_REPLAY_HARNESS_PLAN_LOCAL_NOAPI.md
- data/v2_38_final_close_local_and_single_github_push_noapi.json
- data/v2_38_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_38_next_approved_phase_selection_noapi.json
- data/v2_38_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_38_shadow_observation_classification_replay_harness_plan_local_noapi.json
- data/v2_38_shadow_observation_classification_replay_harness_plan_local_noapi_rows.jsonl
- data/v2_38a_synthetic_event_set_and_expected_classification_local_noapi.json
- data/v2_38a_synthetic_event_set_and_expected_classification_local_noapi_rows.jsonl
- data/v2_38a_synthetic_shadow_observation_events.jsonl
- data/v2_38b1_replay_harness_action_matrix_and_promotion_rule_adjust_local_noapi.json
- data/v2_38b1_replay_harness_action_matrix_and_promotion_rule_adjust_local_noapi_rows.jsonl
- data/v2_38b1_replay_harness_adjusted_results.jsonl
- data/v2_38b_replay_harness_dryrun_local_noapi.json
- data/v2_38b_replay_harness_dryrun_local_noapi_rows.jsonl
- data/v2_38b_replay_harness_dryrun_results.jsonl
- data/v2_38c_replay_harness_local_review_noapi.json
- data/v2_38c_replay_harness_local_review_noapi_rows.jsonl

---

### V2_39 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: PLAN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_39A_REAL_DATA_INTAKE_BOUNDARY_AND_SOURCE_POLICY_LOCAL_NOAPI.md
- docs/v2/V2_39B_REAL_DATA_SHADOW_EVENT_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_39C_CRITICAL_THRESHOLD_DEVIATION_MODEL_LOCAL_NOAPI.md
- docs/v2/V2_39D_ATTACK_ISOLATION_CANDIDATE_RULES_LOCAL_NOAPI.md
- docs/v2/V2_39E_FALSE_POSITIVE_AND_NON_PARANOIA_REVIEW_LOCAL_NOAPI.md
- docs/v2/V2_39_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_39_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- docs/v2/V2_39_REAL_DATA_SHADOW_OBSERVATION_INTAKE_AND_ATTACK_ISOLATION_THRESHOLD_PLAN_NOAPI.md
- data/v2_39_final_close_local_and_single_github_push_noapi.json
- data/v2_39_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_39_next_approved_phase_selection_noapi.json
- data/v2_39_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_39_real_data_shadow_observation_intake_and_attack_isolation_threshold_plan_noapi.json
- data/v2_39_real_data_shadow_observation_intake_and_attack_isolation_threshold_plan_noapi_rows.jsonl
- data/v2_39a_real_data_intake_boundary_and_source_policy_local_noapi.json
- data/v2_39a_real_data_intake_boundary_and_source_policy_local_noapi_rows.jsonl
- data/v2_39b_real_data_shadow_event_contract_local_noapi.json
- data/v2_39b_real_data_shadow_event_contract_local_noapi_rows.jsonl
- data/v2_39c_critical_threshold_deviation_model_local_noapi.json
- data/v2_39c_critical_threshold_deviation_model_local_noapi_rows.jsonl
- data/v2_39d_attack_isolation_candidate_rules_local_noapi.json
- data/v2_39d_attack_isolation_candidate_rules_local_noapi_rows.jsonl
- data/v2_39e_false_positive_and_non_paranoia_review_local_noapi.json
- data/v2_39e_false_positive_and_non_paranoia_review_local_noapi_rows.jsonl

---

### V2_40 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: DRYRUN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_40A_REAL_DATA_SHAPED_FIXTURE_REPLAY_REVIEW_LOCAL_NOAPI.md
- docs/v2/V2_40_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_40_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- docs/v2/V2_40_REAL_DATA_SHAPED_SHADOW_OBSERVATION_FIXTURE_REPLAY_DRYRUN_NOAPI.md
- data/v2_40_final_close_local_and_single_github_push_noapi.json
- data/v2_40_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_40_next_approved_phase_selection_noapi.json
- data/v2_40_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_40_real_data_shaped_shadow_fixture_events.jsonl
- data/v2_40_real_data_shaped_shadow_fixture_replay_results.jsonl
- data/v2_40_real_data_shaped_shadow_observation_fixture_replay_dryrun_noapi.json
- data/v2_40_real_data_shaped_shadow_observation_fixture_replay_dryrun_noapi_rows.jsonl
- data/v2_40a_real_data_shaped_fixture_replay_review_local_noapi.json
- data/v2_40a_real_data_shaped_fixture_replay_review_local_noapi_rows.jsonl

---

### V2_41 — SHADOW INTAKE QUEUE STATE

İş türü: DRYRUN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_41A_SHADOW_INTAKE_LOCAL_DRYRUN_REVIEW_NOAPI.md
- docs/v2/V2_41_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_41_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- docs/v2/V2_41_SHADOW_INTAKE_LOCAL_DRYRUN_NOAPI.md
- data/v2_41_final_close_local_and_single_github_push_noapi.json
- data/v2_41_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_41_next_approved_phase_selection_noapi.json
- data/v2_41_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_41_shadow_intake_accepted_events.jsonl
- data/v2_41_shadow_intake_dedupe_state.jsonl
- data/v2_41_shadow_intake_local_dryrun_noapi.json
- data/v2_41_shadow_intake_local_dryrun_noapi_rows.jsonl
- data/v2_41_shadow_intake_queue_state.jsonl
- data/v2_41a_shadow_intake_local_dryrun_review_noapi.json
- data/v2_41a_shadow_intake_local_dryrun_review_noapi_rows.jsonl

---

### V2_42 — DOMAIN PRIORITY AND GAP REVIEW LOCAL NOAPI

İş türü: PLAN, DRYRUN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_42A_DOMAIN_PRIORITY_AND_GAP_REVIEW_LOCAL_NOAPI.md
- docs/v2/V2_42_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_42_POST_DRYRUN_SYSTEM_CAPABILITY_MAP_AND_NEXT_DOMAINS_PLAN_NOAPI.md
- data/v2_42_final_close_local_and_single_github_push_noapi.json
- data/v2_42_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_42_post_dryrun_system_capability_map_and_next_domains_plan_noapi.json
- data/v2_42_post_dryrun_system_capability_map_and_next_domains_plan_noapi_rows.jsonl
- data/v2_42a_domain_priority_and_gap_review_local_noapi.json
- data/v2_42a_domain_priority_and_gap_review_local_noapi_rows.jsonl

---

### V2_43 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: PLAN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_43A_SYSTEM_MONITORING_SCOPE_AND_OBSERVATION_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_43B_SYSTEM_MONITORING_FAIL_CLOSED_AND_INTERVENTION_BOUNDARY_LOCAL_NOAPI.md
- docs/v2/V2_43_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_43_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- docs/v2/V2_43_SYSTEM_MONITORING_BOUNDARY_PLAN_NOAPI.md
- data/v2_43_final_close_local_and_single_github_push_noapi.json
- data/v2_43_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_43_next_approved_phase_selection_noapi.json
- data/v2_43_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_43_system_monitoring_boundary_plan_noapi.json
- data/v2_43_system_monitoring_boundary_plan_noapi_rows.jsonl
- data/v2_43a_system_monitoring_scope_and_observation_contract_local_noapi.json
- data/v2_43a_system_monitoring_scope_and_observation_contract_local_noapi_rows.jsonl
- data/v2_43b_system_monitoring_fail_closed_and_intervention_boundary_local_noapi.json
- data/v2_43b_system_monitoring_fail_closed_and_intervention_boundary_local_noapi_rows.jsonl

---

### V2_44 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: PLAN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_44A_WHALE_SOURCE_TAXONOMY_AND_ENTITY_BOUNDARY_LOCAL_NOAPI.md
- docs/v2/V2_44B_FAKE_WHALE_REAL_WHALE_SEPARATION_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_44_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_44_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- docs/v2/V2_44_WHALE_WALLET_TRACKING_ARCHITECTURE_PLAN_NOAPI.md
- data/v2_44_final_close_local_and_single_github_push_noapi.json
- data/v2_44_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_44_next_approved_phase_selection_noapi.json
- data/v2_44_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_44_whale_wallet_tracking_architecture_plan_noapi.json
- data/v2_44_whale_wallet_tracking_architecture_plan_noapi_rows.jsonl
- data/v2_44a_whale_source_taxonomy_and_entity_boundary_local_noapi.json
- data/v2_44a_whale_source_taxonomy_and_entity_boundary_local_noapi_rows.jsonl
- data/v2_44b_fake_whale_real_whale_separation_contract_local_noapi.json
- data/v2_44b_fake_whale_real_whale_separation_contract_local_noapi_rows.jsonl

---

### V2_45 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: PLAN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_45A_SIGNAL_TIMESTAMP_AND_TTL_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_45B_SLIDING_WINDOW_BUFFER_BLOAT_AND_RACE_GUARD_LOCAL_NOAPI.md
- docs/v2/V2_45_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_45_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- docs/v2/V2_45_TIME_DRIFT_SIGNAL_TTL_AND_SLIDING_WINDOW_PLAN_NOAPI.md
- data/v2_45_final_close_local_and_single_github_push_noapi.json
- data/v2_45_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_45_next_approved_phase_selection_noapi.json
- data/v2_45_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_45_time_drift_signal_ttl_and_sliding_window_plan_noapi.json
- data/v2_45_time_drift_signal_ttl_and_sliding_window_plan_noapi_rows.jsonl
- data/v2_45a_signal_timestamp_and_ttl_contract_local_noapi.json
- data/v2_45a_signal_timestamp_and_ttl_contract_local_noapi_rows.jsonl
- data/v2_45b_sliding_window_buffer_bloat_and_race_guard_local_noapi.json
- data/v2_45b_sliding_window_buffer_bloat_and_race_guard_local_noapi_rows.jsonl

---

### V2_46 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: PLAN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_46A_DEX_CUSTOM_INDICATOR_AND_OSCILLATOR_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_46A_FIX2_NIS_CONTINUOUS_BAND_BOUNDARY_GUARD_LOCAL_NOAPI.md
- docs/v2/V2_46A_FIX3_NIS_BOUNDARY_COUNT_AND_ANOMALY_FLOOR_LOCAL_NOAPI.md
- docs/v2/V2_46A_FIX_NIS_SEMANTIC_MATH_FIXED_POINT_AND_POISONING_GUARD_LOCAL_NOAPI.md
- docs/v2/V2_46B_PATTERN_SPOOFING_GHOST_LIQUIDITY_AND_OVERRIDE_GUARD_LOCAL_NOAPI.md
- docs/v2/V2_46_DEX_TECHNICAL_PATTERN_AND_CUSTOM_MICROSTRUCTURE_ENGINE_PLAN_NOAPI.md
- docs/v2/V2_46_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_46_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- data/v2_46_dex_technical_pattern_and_custom_microstructure_engine_plan_noapi.json
- data/v2_46_dex_technical_pattern_and_custom_microstructure_engine_plan_noapi_rows.jsonl
- data/v2_46_final_close_local_and_single_github_push_noapi.json
- data/v2_46_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_46_next_approved_phase_selection_noapi.json
- data/v2_46_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_46a_dex_custom_indicator_and_oscillator_contract_local_noapi.json
- data/v2_46a_dex_custom_indicator_and_oscillator_contract_local_noapi_rows.jsonl
- data/v2_46a_fix2_nis_continuous_band_boundary_guard_local_noapi.json
- data/v2_46a_fix2_nis_continuous_band_boundary_guard_local_noapi_rows.jsonl
- data/v2_46a_fix3_nis_boundary_count_and_anomaly_floor_local_noapi.json
- data/v2_46a_fix3_nis_boundary_count_and_anomaly_floor_local_noapi_rows.jsonl
- data/v2_46a_fix_nis_semantic_math_fixed_point_and_poisoning_guard_local_noapi.json
- data/v2_46a_fix_nis_semantic_math_fixed_point_and_poisoning_guard_local_noapi_rows.jsonl
- data/v2_46b_pattern_spoofing_ghost_liquidity_and_override_guard_local_noapi.json
- data/v2_46b_pattern_spoofing_ghost_liquidity_and_override_guard_local_noapi_rows.jsonl

---

### V2_47 — FINAL CLOSE LOCAL AND SINGLE GITHUB PUSH NOAPI

İş türü: PLAN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_47A_REAL_OPPORTUNITY_VS_FAKE_OPPORTUNITY_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_47B_FAST_PATH_HEAVY_PATH_QUEUE_BUDGET_AND_PRIORITY_CLASSIFIER_LOCAL_NOAPI.md
- docs/v2/V2_47B_FIX_QUEUE_BUDGET_AND_DYNAMIC_SLOT_GUARD_LOCAL_NOAPI.md
- docs/v2/V2_47_DECISION_POISONING_RESISTANT_DEX_ALPHA_OPPORTUNITY_ENGINE_PLAN_NOAPI.md
- docs/v2/V2_47_DECISION_POISONING_RESISTANT_DEX_ALPHA_OPPORTUNITY_ENGINE_SELECTION_NOAPI.md
- docs/v2/V2_47_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- data/v2_47_decision_poisoning_resistant_dex_alpha_opportunity_engine_plan_noapi.json
- data/v2_47_decision_poisoning_resistant_dex_alpha_opportunity_engine_plan_noapi_rows.jsonl
- data/v2_47_decision_poisoning_resistant_dex_alpha_opportunity_engine_selection_noapi.json
- data/v2_47_decision_poisoning_resistant_dex_alpha_opportunity_engine_selection_noapi_rows.jsonl
- data/v2_47_final_close_local_and_single_github_push_noapi.json
- data/v2_47_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_47a_real_opportunity_vs_fake_opportunity_contract_local_noapi.json
- data/v2_47a_real_opportunity_vs_fake_opportunity_contract_local_noapi_rows.jsonl
- data/v2_47b_fast_path_heavy_path_queue_budget_and_priority_classifier_local_noapi.json
- data/v2_47b_fast_path_heavy_path_queue_budget_and_priority_classifier_local_noapi_rows.jsonl
- data/v2_47b_fix_queue_budget_and_dynamic_slot_guard_local_noapi.json
- data/v2_47b_fix_queue_budget_and_dynamic_slot_guard_local_noapi_rows.jsonl

---

### V2_48 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: PLAN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_48A_ALPHA_REPLAY_MEMORY_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_48A_FIX_FAKE_STRENGTHENING_PRECEDENCE_LOCAL_NOAPI.md
- docs/v2/V2_48B_MISSED_OPPORTUNITY_FEEDBACK_AND_FALSE_NEGATIVE_GUARD_LOCAL_NOAPI.md
- docs/v2/V2_48_ALPHA_REPLAY_MEMORY_AND_MISSED_OPPORTUNITY_FEEDBACK_ENGINE_PLAN_NOAPI.md
- docs/v2/V2_48_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_48_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- data/v2_48_alpha_replay_memory_and_missed_opportunity_feedback_engine_plan_noapi.json
- data/v2_48_alpha_replay_memory_and_missed_opportunity_feedback_engine_plan_noapi_rows.jsonl
- data/v2_48_final_close_local_and_single_github_push_noapi.json
- data/v2_48_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_48_next_approved_phase_selection_noapi.json
- data/v2_48_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_48a_alpha_replay_memory_contract_local_noapi.json
- data/v2_48a_alpha_replay_memory_contract_local_noapi_rows.jsonl
- data/v2_48a_fix_fake_strengthening_precedence_local_noapi.json
- data/v2_48a_fix_fake_strengthening_precedence_local_noapi_rows.jsonl
- data/v2_48b_missed_opportunity_feedback_and_false_negative_guard_local_noapi.json
- data/v2_48b_missed_opportunity_feedback_and_false_negative_guard_local_noapi_rows.jsonl

---

### V2_49 — FIX HARD BOUNDARY COUNT LOCAL NOAPI

İş türü: PLAN, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_49A_CASE_FINGERPRINT_AND_HASH_LOOKUP_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_49A_FIX_HARD_BOUNDARY_COUNT_LOCAL_NOAPI.md
- docs/v2/V2_49B_LOSSLESS_COMPACTION_AND_HOT_PATH_ISOLATION_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_49_CASE_REASONING_AND_ALPHA_MEMORY_COMPACTION_ENGINE_PLAN_NOAPI.md
- docs/v2/V2_49_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_49_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- data/v2_49_case_reasoning_and_alpha_memory_compaction_engine_plan_noapi.json
- data/v2_49_case_reasoning_and_alpha_memory_compaction_engine_plan_noapi_rows.jsonl
- data/v2_49_final_close_local_and_single_github_push_noapi.json
- data/v2_49_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_49_next_approved_phase_selection_noapi.json
- data/v2_49_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_49a_case_fingerprint_and_hash_lookup_contract_local_noapi.json
- data/v2_49a_case_fingerprint_and_hash_lookup_contract_local_noapi_rows.jsonl
- data/v2_49a_fix_hard_boundary_count_local_noapi.json
- data/v2_49a_fix_hard_boundary_count_local_noapi_rows.jsonl
- data/v2_49b_lossless_compaction_and_hot_path_isolation_contract_local_noapi.json
- data/v2_49b_lossless_compaction_and_hot_path_isolation_contract_local_noapi_rows.jsonl

---

### V2_50 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: PLAN, DRYRUN, AUDIT, GITHUB_SEAL, CLOSE, RUNTIME

Kayıt dosyaları:
- docs/v2/V2_50A_SHADOW_STALENESS_AND_NEGATIVE_PRECHECK_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_50B_SHADOW_BOUNDED_CACHE_AND_POISONING_GUARD_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_50ZA_HARDCORE_CHAOS_TEMPDB_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_50ZB_HARDCORE_CHAOS_POST_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_50Z_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_50Z_HARDCORE_CHAOS_AND_DESTRUCTION_SIMULATION_PLAN_NOAPI.md
- docs/v2/V2_50Z_HARDCORE_CHAOS_AND_DESTRUCTION_SIMULATION_SELECTION_NOAPI.md
- docs/v2/V2_50_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_50_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- docs/v2/V2_50_RUNTIME_SHADOW_READ_MODEL_AND_DECISION_PRECHECK_PLAN_NOAPI.md
- data/v2_50_final_close_local_and_single_github_push_noapi.json
- data/v2_50_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_50_next_approved_phase_selection_noapi.json
- data/v2_50_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_50_runtime_shadow_read_model_and_decision_precheck_plan_noapi.json
- data/v2_50_runtime_shadow_read_model_and_decision_precheck_plan_noapi_rows.jsonl
- data/v2_50a_shadow_staleness_and_negative_precheck_contract_local_noapi.json
- data/v2_50a_shadow_staleness_and_negative_precheck_contract_local_noapi_rows.jsonl
- data/v2_50b_shadow_bounded_cache_and_poisoning_guard_contract_local_noapi.json
- data/v2_50b_shadow_bounded_cache_and_poisoning_guard_contract_local_noapi_rows.jsonl
- data/v2_50z_final_close_local_and_single_github_push_noapi.json
- data/v2_50z_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_50z_hardcore_chaos_and_destruction_simulation_plan_noapi.json
- data/v2_50z_hardcore_chaos_and_destruction_simulation_plan_noapi_rows.jsonl
- data/v2_50z_hardcore_chaos_and_destruction_simulation_selection_noapi.json
- data/v2_50z_hardcore_chaos_and_destruction_simulation_selection_noapi_rows.jsonl
- data/v2_50za_hardcore_chaos_tempdb_dryrun_local_noapi.json
- data/v2_50za_hardcore_chaos_tempdb_dryrun_local_noapi_rows.jsonl
- data/v2_50zb_hardcore_chaos_post_audit_local_noapi.json
- data/v2_50zb_hardcore_chaos_post_audit_local_noapi_rows.jsonl

---

### V2_51 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: AUDIT, GITHUB_SEAL, CLOSE, RUNTIME

Kayıt dosyaları:
- docs/v2/V2_51A_QUARANTINE_TTL_PROBATION_AND_BYPASS_LIMITER_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_51B_DIRTY_PACKET_AND_FRESH_RISK_PRIORITY_CONTRACT_LOCAL_NOAPI.md
- docs/v2/V2_51C_GATE_OF_HELL_HARDENING_POST_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_51_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_51_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- docs/v2/V2_51_RUNTIME_SHADOW_READ_MODEL_CONTRACT_HARDENING_NOAPI.md
- data/v2_51_final_close_local_and_single_github_push_noapi.json
- data/v2_51_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_51_next_approved_phase_selection_noapi.json
- data/v2_51_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_51_runtime_shadow_read_model_contract_hardening_noapi.json
- data/v2_51_runtime_shadow_read_model_contract_hardening_noapi_rows.jsonl
- data/v2_51a_quarantine_ttl_probation_and_bypass_limiter_contract_local_noapi.json
- data/v2_51a_quarantine_ttl_probation_and_bypass_limiter_contract_local_noapi_rows.jsonl
- data/v2_51b_dirty_packet_and_fresh_risk_priority_contract_local_noapi.json
- data/v2_51b_dirty_packet_and_fresh_risk_priority_contract_local_noapi_rows.jsonl
- data/v2_51c_gate_of_hell_hardening_post_audit_local_noapi.json
- data/v2_51c_gate_of_hell_hardening_post_audit_local_noapi_rows.jsonl

---

### V2_52 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: AUDIT, GITHUB_SEAL, CLOSE, RUNTIME

Kayıt dosyaları:
- docs/v2/V2_52A_CORE_RISK_AUTHORITY_BOUNDARY_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_52A_FIX_CORE_RISK_AUTHORITY_BOUNDARY_AUDIT_CONTRACT_COUNT_LOCAL_NOAPI.md
- docs/v2/V2_52B_FRESH_RISK_BYPASS_DIRTY_PACKET_PRE_BINDING_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_52C_PRE_BINDING_SIDE_EFFECT_AND_HASH_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_52D_CORE_RISK_PRE_BINDING_POST_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_52_CORE_RISK_RUNTIME_PRE_BINDING_AUDIT_NOAPI.md
- docs/v2/V2_52_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_52_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- data/v2_52_core_risk_runtime_pre_binding_audit_noapi.json
- data/v2_52_core_risk_runtime_pre_binding_audit_noapi_rows.jsonl
- data/v2_52_final_close_local_and_single_github_push_noapi.json
- data/v2_52_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_52_next_approved_phase_selection_noapi.json
- data/v2_52_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_52a_core_risk_authority_boundary_audit_local_noapi.json
- data/v2_52a_core_risk_authority_boundary_audit_local_noapi_rows.jsonl
- data/v2_52a_fix_core_risk_authority_boundary_audit_contract_count_local_noapi.json
- data/v2_52a_fix_core_risk_authority_boundary_audit_contract_count_local_noapi_rows.jsonl
- data/v2_52b_fresh_risk_bypass_dirty_packet_pre_binding_audit_local_noapi.json
- data/v2_52b_fresh_risk_bypass_dirty_packet_pre_binding_audit_local_noapi_rows.jsonl
- data/v2_52c_pre_binding_side_effect_and_hash_audit_local_noapi.json
- data/v2_52c_pre_binding_side_effect_and_hash_audit_local_noapi_rows.jsonl
- data/v2_52d_core_risk_pre_binding_post_audit_local_noapi.json
- data/v2_52d_core_risk_pre_binding_post_audit_local_noapi_rows.jsonl

---

### V2_53 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: DRYRUN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_53A_DECISION_PIPELINE_ORCHESTRATOR_TRACE_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_53B_FIX_RISK_PRIORITY_EVIDENCE_OUTPUT_NEXT_MATCH_LOCAL_NOAPI.md
- docs/v2/V2_53B_RISK_PRIORITY_EVIDENCE_OUTPUT_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_53C_FIX_SIDE_EFFECT_HASH_NO_PACKET_AUDIT_CONTRACT_COUNT_LOCAL_NOAPI.md
- docs/v2/V2_53C_SIDE_EFFECT_HASH_NO_PACKET_DRYRUN_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_53D_DECISION_PIPELINE_POST_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_53_DECISION_PIPELINE_DRY_RUN_ORCHESTRATOR_NOAPI.md
- docs/v2/V2_53_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_53_FIX_DECISION_PIPELINE_DRY_RUN_ORCHESTRATOR_CONTRACT_COUNT_LOCAL_NOAPI.md
- docs/v2/V2_53_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- data/v2_53_decision_pipeline_dry_run_orchestrator_noapi.json
- data/v2_53_decision_pipeline_dry_run_orchestrator_noapi_rows.jsonl
- data/v2_53_final_close_local_and_single_github_push_noapi.json
- data/v2_53_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_53_fix_decision_pipeline_dry_run_orchestrator_contract_count_local_noapi.json
- data/v2_53_fix_decision_pipeline_dry_run_orchestrator_contract_count_local_noapi_rows.jsonl
- data/v2_53_next_approved_phase_selection_noapi.json
- data/v2_53_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_53a_decision_pipeline_orchestrator_trace_dryrun_local_noapi.json
- data/v2_53a_decision_pipeline_orchestrator_trace_dryrun_local_noapi_rows.jsonl
- data/v2_53b_fix_risk_priority_evidence_output_next_match_local_noapi.json
- data/v2_53b_fix_risk_priority_evidence_output_next_match_local_noapi_rows.jsonl
- data/v2_53b_risk_priority_evidence_output_dryrun_local_noapi.json
- data/v2_53b_risk_priority_evidence_output_dryrun_local_noapi_rows.jsonl
- data/v2_53c_fix_side_effect_hash_no_packet_audit_contract_count_local_noapi.json
- data/v2_53c_fix_side_effect_hash_no_packet_audit_contract_count_local_noapi_rows.jsonl
- data/v2_53c_side_effect_hash_no_packet_dryrun_audit_local_noapi.json
- data/v2_53c_side_effect_hash_no_packet_dryrun_audit_local_noapi_rows.jsonl
- data/v2_53d_decision_pipeline_post_audit_local_noapi.json
- data/v2_53d_decision_pipeline_post_audit_local_noapi_rows.jsonl

---

### V2_54 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: DRYRUN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_54A_CONFLICT_PRIORITY_MATRIX_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_54B_AUTHORITY_EVIDENCE_OUTPUT_CONFLICT_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_54C_SIDE_EFFECT_HASH_NO_PACKET_DRYRUN_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_54D_MULTI_ENGINE_CONFLICT_RESOLVER_POST_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_54_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_54_MULTI_ENGINE_CONFLICT_RESOLVER_NOAPI.md
- docs/v2/V2_54_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- data/v2_54_final_close_local_and_single_github_push_noapi.json
- data/v2_54_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_54_multi_engine_conflict_resolver_noapi.json
- data/v2_54_multi_engine_conflict_resolver_noapi_rows.jsonl
- data/v2_54_next_approved_phase_selection_noapi.json
- data/v2_54_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_54a_conflict_priority_matrix_dryrun_local_noapi.json
- data/v2_54a_conflict_priority_matrix_dryrun_local_noapi_rows.jsonl
- data/v2_54b_authority_evidence_output_conflict_dryrun_local_noapi.json
- data/v2_54b_authority_evidence_output_conflict_dryrun_local_noapi_rows.jsonl
- data/v2_54c_side_effect_hash_no_packet_dryrun_audit_local_noapi.json
- data/v2_54c_side_effect_hash_no_packet_dryrun_audit_local_noapi_rows.jsonl
- data/v2_54d_multi_engine_conflict_resolver_post_audit_local_noapi.json
- data/v2_54d_multi_engine_conflict_resolver_post_audit_local_noapi_rows.jsonl

---

### V2_55 — NEXT APPROVED PHASE SELECTION NOAPI

İş türü: DRYRUN, AUDIT, GITHUB_SEAL, CLOSE, SCHEMA

Kayıt dosyaları:
- docs/v2/V2_55A_DECISION_OUTPUT_SCHEMA_BINDING_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_55A_FIX_SAMPLE_PAYLOAD_FIELD_COMPLETION_LOCAL_NOAPI.md
- docs/v2/V2_55B_MEMORY_MUTATION_AUTHORITY_O1_LOOKUP_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_55C_FIX_AUDIT_CONTRACT_COUNT_LOCAL_NOAPI.md
- docs/v2/V2_55C_SIDE_EFFECT_HASH_NO_PACKET_DRYRUN_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_55D_DECISION_OUTPUT_CONTRACT_BINDING_POST_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_55_DECISION_OUTPUT_CONTRACT_BINDING_NOAPI.md
- docs/v2/V2_55_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_55_NEXT_APPROVED_PHASE_SELECTION_NOAPI.md
- data/v2_55_decision_output_contract_binding_noapi.json
- data/v2_55_decision_output_contract_binding_noapi_rows.jsonl
- data/v2_55_final_close_local_and_single_github_push_noapi.json
- data/v2_55_final_close_local_and_single_github_push_noapi.jsonl
- data/v2_55_next_approved_phase_selection_noapi.json
- data/v2_55_next_approved_phase_selection_noapi_rows.jsonl
- data/v2_55a_decision_output_schema_binding_dryrun_local_noapi.json
- data/v2_55a_decision_output_schema_binding_dryrun_local_noapi_rows.jsonl
- data/v2_55a_fix_sample_payload_field_completion_local_noapi.json
- data/v2_55a_fix_sample_payload_field_completion_local_noapi_rows.jsonl
- data/v2_55b_memory_mutation_authority_o1_lookup_dryrun_local_noapi.json
- data/v2_55b_memory_mutation_authority_o1_lookup_dryrun_local_noapi_rows.jsonl
- data/v2_55c_fix_audit_contract_count_local_noapi.json
- data/v2_55c_fix_audit_contract_count_local_noapi_rows.jsonl
- data/v2_55c_side_effect_hash_no_packet_dryrun_audit_local_noapi.json
- data/v2_55c_side_effect_hash_no_packet_dryrun_audit_local_noapi_rows.jsonl
- data/v2_55d_decision_output_contract_binding_post_audit_local_noapi.json
- data/v2_55d_decision_output_contract_binding_post_audit_local_noapi.jsonl

---

### V2_56 — STATE MACHINE SCHEMA DRYRUN LOCAL NOAPI

İş türü: PLAN, DRYRUN, AUDIT, GITHUB_SEAL, CLOSE, SCHEMA

Kayıt dosyaları:
- docs/v2/V2_56A_STATE_MACHINE_SCHEMA_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_56B_STATE_MACHINE_MEMORY_SYNC_POST_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_56_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_56_STATE_MACHINE_AND_MEMORY_SYNC_LOCK_PLAN_NOAPI.md
- data/v2_56_final_close_local_and_single_github_push_noapi.json
- data/v2_56_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_56_state_machine_and_memory_sync_lock_plan_noapi.json
- data/v2_56_state_machine_and_memory_sync_lock_plan_noapi_rows.jsonl
- data/v2_56a_state_machine_schema_dryrun_local_noapi.json
- data/v2_56a_state_machine_schema_dryrun_local_noapi_rows.jsonl
- data/v2_56b_state_machine_memory_sync_post_audit_local_noapi.json
- data/v2_56b_state_machine_memory_sync_post_audit_local_noapi_rows.jsonl

---

### V2_57 — RUNTIME BOUNDARY POST AUDIT LOCAL NOAPI

İş türü: PLAN, DRYRUN, AUDIT, GITHUB_SEAL, CLOSE, SCHEMA, RUNTIME

Kayıt dosyaları:
- docs/v2/V2_57A_RUNTIME_BOUNDARY_SCHEMA_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_57B_RUNTIME_BOUNDARY_POST_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_57_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_57_RUNTIME_READINESS_BOUNDARY_AUDIT_PLAN_NOAPI.md
- data/v2_57_final_close_local_and_single_github_push_noapi.json
- data/v2_57_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_57_runtime_readiness_boundary_audit_plan_noapi.json
- data/v2_57_runtime_readiness_boundary_audit_plan_noapi_rows.jsonl
- data/v2_57a_runtime_boundary_schema_dryrun_local_noapi.json
- data/v2_57a_runtime_boundary_schema_dryrun_local_noapi_rows.jsonl
- data/v2_57b_runtime_boundary_post_audit_local_noapi.json
- data/v2_57b_runtime_boundary_post_audit_local_noapi_rows.jsonl

---

### V2_58 — END TO END CHAIN POST AUDIT LOCAL NOAPI

İş türü: PLAN, DRYRUN, AUDIT, GITHUB_SEAL, CLOSE, SCHEMA

Kayıt dosyaları:
- docs/v2/V2_58A_END_TO_END_CHAIN_SCHEMA_DRYRUN_LOCAL_NOAPI.md
- docs/v2/V2_58B_END_TO_END_CHAIN_REPLAY_AND_IDEMPOTENCY_LOCAL_NOAPI.md
- docs/v2/V2_58C_END_TO_END_CHAIN_POST_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_58_END_TO_END_DRY_RUN_DECISION_CHAIN_PLAN_NOAPI.md
- docs/v2/V2_58_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- data/v2_58_end_to_end_dry_run_decision_chain_plan_noapi.json
- data/v2_58_end_to_end_dry_run_decision_chain_plan_noapi_rows.jsonl
- data/v2_58_final_close_local_and_single_github_push_noapi.json
- data/v2_58_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_58a_end_to_end_chain_schema_dryrun_local_noapi.json
- data/v2_58a_end_to_end_chain_schema_dryrun_local_noapi_rows.jsonl
- data/v2_58b_end_to_end_chain_replay_and_idempotency_local_noapi.json
- data/v2_58b_end_to_end_chain_replay_and_idempotency_local_noapi_rows.jsonl
- data/v2_58c_end_to_end_chain_post_audit_local_noapi.json
- data/v2_58c_end_to_end_chain_post_audit_local_noapi_rows.jsonl

---

### V2_59 — FINAL CLOSE LOCAL AND SINGLE GITHUB PUSH NOAPI

İş türü: PLAN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_59A_FINAL_V2_PRE_SEAL_CONSISTENCY_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_59_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- docs/v2/V2_59_FINAL_V2_PRE_SEAL_CONSISTENCY_AUDIT_PLAN_NOAPI.md
- data/v2_59_final_close_local_and_single_github_push_noapi.json
- data/v2_59_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_59_final_v2_pre_seal_consistency_audit_plan_noapi.json
- data/v2_59_final_v2_pre_seal_consistency_audit_plan_noapi_rows.jsonl
- data/v2_59a_final_v2_pre_seal_consistency_audit_local_noapi.json
- data/v2_59a_final_v2_pre_seal_consistency_audit_local_noapi_rows.jsonl

---

### V2_60 — CANONICAL V2 FINAL CLOSURE AUDIT LOCAL NOAPI

İş türü: PLAN, AUDIT, GITHUB_SEAL, CLOSE

Kayıt dosyaları:
- docs/v2/V2_60A_CANONICAL_V2_FINAL_CLOSURE_AUDIT_LOCAL_NOAPI.md
- docs/v2/V2_60_CANONICAL_V2_CLOSURE_AND_GITHUB_SEAL_PLAN_NOAPI.md
- docs/v2/V2_60_FINAL_CLOSE_LOCAL_AND_SINGLE_GITHUB_PUSH_NOAPI.md
- data/v2_60_canonical_v2_closure_and_github_seal_plan_noapi.json
- data/v2_60_canonical_v2_closure_and_github_seal_plan_noapi_rows.jsonl
- data/v2_60_final_close_local_and_single_github_push_noapi.json
- data/v2_60_final_close_local_and_single_github_push_noapi_rows.jsonl
- data/v2_60a_canonical_v2_final_closure_audit_local_noapi.json
- data/v2_60a_canonical_v2_final_closure_audit_local_noapi_rows.jsonl

---

### V2_8104 — TOKENYASAM BASELINE ICON MERGE RECHECK NOAPI

İş türü: KAYIT

Kayıt dosyaları:
- data/tokenyasam_baseline_icon_merge_v2_8104_recheck_noapi.json

---

## V3 ALMANAC - RUNTIME IMPLEMENTATION AİLE KAYITLARI

### RUNTIME_SLICE_01 — GITHUB SEAL NOAPI

İş türü: AUDIT, GITHUB_SEAL, RUNTIME

Kayıt dosyaları:
- docs/runtime/RUNTIME_SLICE_01_GITHUB_SEAL_NOAPI.md
- docs/runtime/RUNTIME_SLICE_01_OBSERVABILITY_POST_AUDIT_NOAPI.md
- docs/runtime/RUNTIME_SLICE_01_OBSERVABILITY_READONLY_APPLY_NOAPI.md
- data/runtime_slice_01_github_seal_noapi.json
- data/runtime_slice_01_github_seal_noapi_rows.jsonl
- data/runtime_slice_01_observability_post_audit_noapi.json
- data/runtime_slice_01_observability_post_audit_noapi_rows.jsonl
- data/runtime_slice_01_observability_readonly_apply_noapi.json
- data/runtime_slice_01_observability_readonly_apply_noapi_rows.jsonl

---

### RUNTIME_SLICE_02 — GITHUB SEAL NOAPI

İş türü: AUDIT, GITHUB_SEAL, RUNTIME

Kayıt dosyaları:
- docs/runtime/RUNTIME_SLICE_02_GITHUB_SEAL_NOAPI.md
- docs/runtime/RUNTIME_SLICE_02_SHADOW_FEED_LOCAL_APPLY_NOAPI.md
- docs/runtime/RUNTIME_SLICE_02_SHADOW_FEED_POST_AUDIT_NOAPI.md
- data/runtime_slice_02_github_seal_noapi.json
- data/runtime_slice_02_github_seal_noapi_rows.jsonl
- data/runtime_slice_02_shadow_feed_local_apply_noapi.json
- data/runtime_slice_02_shadow_feed_local_apply_noapi_rows.jsonl
- data/runtime_slice_02_shadow_feed_post_audit_noapi.json
- data/runtime_slice_02_shadow_feed_post_audit_noapi_rows.jsonl

---

### RUNTIME_SLICE_03 — POST AUDIT NOAPI

İş türü: AUDIT, GITHUB_SEAL, RUNTIME

Kayıt dosyaları:
- docs/runtime/RUNTIME_SLICE_03_GITHUB_SEAL_NOAPI.md
- docs/runtime/RUNTIME_SLICE_03_MULTI_RPC_TRUST_ENGINE_LOCAL_APPLY_NOAPI.md
- docs/runtime/RUNTIME_SLICE_03_POST_AUDIT_NOAPI.md
- data/runtime_slice_03_github_seal_noapi.json
- data/runtime_slice_03_github_seal_noapi_rows.jsonl
- data/runtime_slice_03_multi_rpc_trust_engine_local_apply_noapi.json
- data/runtime_slice_03_multi_rpc_trust_engine_local_apply_noapi_rows.jsonl
- data/runtime_slice_03_post_audit_noapi.json
- data/runtime_slice_03_post_audit_noapi_rows.jsonl

---

### V3_01 — RUNTIME READINESS AND BLOCKER RESOLUTION PLAN NOAPI

İş türü: PLAN, RUNTIME

Kayıt dosyaları:
- docs/v3/V3_01_RUNTIME_READINESS_AND_BLOCKER_RESOLUTION_PLAN_NOAPI.md
- data/v3_01_runtime_readiness_and_blocker_resolution_plan_noapi.json
- data/v3_01_runtime_readiness_and_blocker_resolution_plan_noapi_rows.jsonl

---

### V3_02 — RUNTIME OBSERVABILITY AND METRICS PLAN NOAPI

İş türü: PLAN, RUNTIME

Kayıt dosyaları:
- docs/v3/V3_02_RUNTIME_OBSERVABILITY_AND_METRICS_PLAN_NOAPI.md
- data/v3_02_runtime_observability_and_metrics_plan_noapi.json
- data/v3_02_runtime_observability_and_metrics_plan_noapi_rows.jsonl

---

### V3_03 — ASYNC LOGGER AND PERSISTENCE ISOLATION PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/v3/V3_03_ASYNC_LOGGER_AND_PERSISTENCE_ISOLATION_PLAN_NOAPI.md
- data/v3_03_async_logger_and_persistence_isolation_plan_noapi.json
- data/v3_03_async_logger_and_persistence_isolation_plan_noapi_rows.jsonl

---

### V3_04 — MULTI RPC TRUST ENGINE AND SHADOW FEED PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/v3/V3_04_MULTI_RPC_TRUST_ENGINE_AND_SHADOW_FEED_PLAN_NOAPI.md
- data/v3_04_multi_rpc_trust_engine_and_shadow_feed_plan_noapi.json
- data/v3_04_multi_rpc_trust_engine_and_shadow_feed_plan_noapi_rows.jsonl

---

### V3_05 — WARM UP ENGINE PLAN NOAPI

İş türü: PLAN

Kayıt dosyaları:
- docs/v3/V3_05_WARM_UP_ENGINE_PLAN_NOAPI.md
- data/v3_05_warm_up_engine_plan_noapi.json
- data/v3_05_warm_up_engine_plan_noapi_rows.jsonl

---

### V3_06 — CHAOS RUNTIME AND STRESS TESTS PLAN NOAPI

İş türü: PLAN, RUNTIME

Kayıt dosyaları:
- docs/v3/V3_06_CHAOS_RUNTIME_AND_STRESS_TESTS_PLAN_NOAPI.md
- data/v3_06_chaos_runtime_and_stress_tests_plan_noapi.json
- data/v3_06_chaos_runtime_and_stress_tests_plan_noapi_rows.jsonl

---

### V3_07 — RUNTIME FINAL AUDIT NOAPI

İş türü: AUDIT, RUNTIME

Kayıt dosyaları:
- docs/v3/V3_07_RUNTIME_FINAL_AUDIT_NOAPI.md
- data/v3_07_runtime_final_audit_noapi.json
- data/v3_07_runtime_final_audit_noapi_rows.jsonl

---

### V3_08 — GITHUB SEAL NOAPI

İş türü: GITHUB_SEAL

Kayıt dosyaları:
- docs/v3/V3_08_GITHUB_SEAL_NOAPI.md
- data/v3_08_github_seal_noapi.json
- data/v3_08_github_seal_noapi_rows.jsonl

---

### RUNTIME_SLICE_04 — WHALE GRAPH POST AUDIT NOAPI

İş türü: AUDIT, GITHUB_SEAL, RUNTIME

Kayıt dosyaları:
- docs/runtime/RUNTIME_SLICE_04_WHALE_INTELLIGENCE_GRAPH_GITHUB_SEAL_NOAPI.md
- docs/runtime/RUNTIME_SLICE_04_WHALE_INTELLIGENCE_GRAPH_LOCAL_APPLY_NOAPI.md
- docs/runtime/RUNTIME_SLICE_04_WHALE_INTELLIGENCE_GRAPH_POST_AUDIT_NOAPI.md
- data/runtime_slice_04_whale_graph_github_seal_noapi.json
- data/runtime_slice_04_whale_graph_github_seal_noapi_rows.jsonl
- data/runtime_slice_04_whale_graph_local_apply_noapi.json
- data/runtime_slice_04_whale_graph_local_apply_noapi_rows.jsonl
- data/runtime_slice_04_whale_graph_post_audit_noapi.json
- data/runtime_slice_04_whale_graph_post_audit_noapi_rows.jsonl

---

### RUNTIME_SLICE_05 — POST AUDIT NOAPI

İş türü: AUDIT, GITHUB_SEAL, RUNTIME

Kayıt dosyaları:
- docs/runtime/RUNTIME_SLICE_05_GITHUB_SEAL_NOAPI.md
- docs/runtime/RUNTIME_SLICE_05_HYBRID_RPC_COST_GUARD_LOCAL_APPLY_NOAPI.md
- docs/runtime/RUNTIME_SLICE_05_POST_AUDIT_NOAPI.md
- data/runtime_slice_05_github_seal_noapi.json
- data/runtime_slice_05_github_seal_noapi_rows.jsonl
- data/runtime_slice_05_hybrid_rpc_cost_guard_local_apply_noapi.json
- data/runtime_slice_05_hybrid_rpc_cost_guard_local_apply_noapi_rows.jsonl
- data/runtime_slice_05_post_audit_noapi.json
- data/runtime_slice_05_post_audit_noapi_rows.jsonl

---

### RUNTIME_SLICE_06 — POST AUDIT NOAPI

İş türü: AUDIT, GITHUB_SEAL, RUNTIME

Kayıt dosyaları:
- docs/runtime/RUNTIME_SLICE_06_CHAIN_ABSTRACTION_LOCAL_APPLY_NOAPI.md
- docs/runtime/RUNTIME_SLICE_06_GITHUB_SEAL_NOAPI.md
- docs/runtime/RUNTIME_SLICE_06_POST_AUDIT_NOAPI.md
- data/runtime_slice_06_chain_abstraction_local_apply_noapi.json
- data/runtime_slice_06_chain_abstraction_local_apply_noapi_rows.jsonl
- data/runtime_slice_06_github_seal_noapi.json
- data/runtime_slice_06_github_seal_noapi_rows.jsonl
- data/runtime_slice_06_post_audit_noapi.json
- data/runtime_slice_06_post_audit_noapi_rows.jsonl

---

### RUNTIME_SLICE_07 — POST AUDIT NOAPI

İş türü: AUDIT, GITHUB_SEAL, RUNTIME

Kayıt dosyaları:
- docs/runtime/RUNTIME_SLICE_07_GITHUB_SEAL_NOAPI.md
- docs/runtime/RUNTIME_SLICE_07_POST_AUDIT_NOAPI.md
- docs/runtime/RUNTIME_SLICE_07_READ_ONLY_RPC_SHADOW_INTAKE_LOCAL_APPLY_NOAPI.md
- data/runtime_slice_07_github_seal_noapi.json
- data/runtime_slice_07_github_seal_noapi_rows.jsonl
- data/runtime_slice_07_post_audit_noapi.json
- data/runtime_slice_07_post_audit_noapi_rows.jsonl
- data/runtime_slice_07_readonly_rpc_shadow_intake_local_apply_noapi.json
- data/runtime_slice_07_readonly_rpc_shadow_intake_local_apply_noapi_rows.jsonl

---

### RUNTIME_SLICE_08 — POST AUDIT NOAPI

İş türü: AUDIT, GITHUB_SEAL, RUNTIME

Kayıt dosyaları:
- docs/runtime/RUNTIME_SLICE_08_GITHUB_SEAL_NOAPI.md
- docs/runtime/RUNTIME_SLICE_08_POST_AUDIT_NOAPI.md
- docs/runtime/RUNTIME_SLICE_08_PROVIDER_ABSTRACTION_LOCAL_APPLY_NOAPI.md
- data/runtime_slice_08_github_seal_noapi.json
- data/runtime_slice_08_github_seal_noapi_rows.jsonl
- data/runtime_slice_08_post_audit_noapi.json
- data/runtime_slice_08_post_audit_noapi_rows.jsonl
- data/runtime_slice_08_provider_abstraction_local_apply_noapi.json
- data/runtime_slice_08_provider_abstraction_local_apply_noapi_rows.jsonl

---

## GÜNCEL DURUM

- V1 closed / verified / GitHub sealed durumdadır.
- V2 controlled continuation kayıtları aile bazlı izlenir.
- V3 runtime implementation kayıtları aile bazlı izlenir.
- Live trade kapalıdır.
- AI authority sıfırdır.
- Wallet / signing kapalıdır.

## SON KURAL

Almanac boş tekrar cümlesi yazmaz.
Almanac dosya adı yazar.
Almanac alt kayıtları ana aile altında toplar.
Detay Almanac içindedir.
Yön Roadmap içindedir.
Bağ Atlas içindedir.
## ERA15 FINAL CLOSURE RECORD
UTC=2026-06-29T13:49:31Z
HEAD=76fd3ba861676c9e112b9ee71ac81af551dfafa4
STATUS=CLOSED_VERIFIED_GITHUB_SEALED

Closed records:
- Runtime Slice 09: CLOSED_BLOCKED_WITH_ACCEPTED_REPAIR
- Runtime Slice 10: PROVIDER_TRUST_AND_TOXIC_SIGNAL_GUARD_SEALED
- Runtime Slice 11: RUNTIME_CONFIDENCE_AND_HEALTH_CLOSURE_SEALED
- ERA15 Final Audit: PASS_FINAL_AUDIT_NOAPI
- ERA15 GitHub Seal: CLOSED_VERIFIED_GITHUB_SEALED

Next:
ERA16

## ERA16 PHASE63 CLOSURE RECORD
UTC=2026-06-29T14:49:59Z
HEAD=f716d4f1d4f943d0b6105c62aafe46b5f69cf385
STATUS=CLOSED_VERIFIED_GITHUB_SEALED

Closed records:
- ERA16_PHASE63_DISTRIBUTED_CONSTITUTION_GUARDIAN_PLAN_NOAPI
- ERA16_PHASE63B_GUARDIAN_DRYRUN_NOAPI
- ERA16_PHASE63C_SILENT_FAILURE_AND_GLOBAL_KILL_SWITCH_DRYRUN_NOAPI
- ERA16_PHASE63D_ATOMIC_CONSTITUTION_UPDATE_PLAN_NOAPI
- ERA16_PHASE63E_APPEND_ONLY_AUDIT_LEDGER_PLAN_NOAPI
- ERA16_PHASE63F_POST_AUDIT_NOAPI
- ERA16_PHASE63G_GITHUB_SEAL

Next:
ERA16_PHASE64


================================================================================
ERA16 FINAL CANONICAL CLOSURE
Timestamp: 2026-06-29T17:04:05Z

ERA16_STATUS=CLOSED_VERIFIED_READY_FOR_GITHUB_SEAL

CANONICAL_PHASE=PHASE62

PHASE62 IMPLEMENTATION MODULES
- Constitution Engine
- Conflict Resolver
- Distributed Guardian
- Runtime Integration
- Intelligence Fabric
- Event Ledger
- Decision Pipeline
- Execution Governance

CANONICAL MAPPING
PHASE63 -> PHASE62/GUARDIAN_MODULE
PHASE64 -> PHASE62/RUNTIME_INTEGRATION_MODULE
PHASE65 -> PHASE62/INTELLIGENCE_FABRIC_MODULE
PHASE66 -> PHASE62/DECISION_PIPELINE_MODULE
PHASE67 -> PHASE62/EXECUTION_GOVERNANCE_MODULE

PHASE ENUMERATION FROZEN
NEXT_ERA=ERA17
================================================================================

================================================================================
ERA17+ WORKFLOW TERMINOLOGY LOCK
Timestamp: 2026-06-29T18:41:46Z
Base HEAD: ecddc11273192bf2e41384b87bdc7a340bbbae9f

DECISION
PASS terminology is not used for ERA17+ workflow units.

REASON
PASS was already used historically in Canonical V1 construction and audits
(PASS0-PASS27 and sub-pass variants). Reusing PASS inside ERA17+ would create
naming ambiguity.

NEW STANDARD
ERA17+ workflow unit = GATE

CANONICAL MEANING
PASS = Legacy construction/audit workflow term.
GATE = ERA17+ certification workflow term.

ERA17+ STRUCTURE
ERA
  GATE01
  GATE02
  GATE03
  FINAL_AUDIT
  GITHUB_SEAL
  ERA_CLOSED

RULES
- No new PHASE identifiers after ERA16 closure.
- No new PASS identifiers after ERA16 closure.
- ERA17+ uses GATE only.
- GATE count is not fixed; minimum necessary gates only.
- Canonical V1 remains the active architecture.
- ERA20 remains the maximum planned ERA boundary for Canonical V1 certification.
================================================================================

================================================================================
ERA18 CLOSURE UPDATE
Timestamp: 2026-06-29T19:58:29Z
HEAD: 3bf2a540d97f32eac652928d46daf115f1a03983

ERA18_STATUS=CLOSED_VERIFIED_GITHUB_SEALED

CURRENT_ERA=ERA19
CURRENT_GATE=GATE01

LAST_COMPLETED=ERA18_GITHUB_SEAL

NEXT_SAFE_STEP=ERA19_GATE01_RUNTIME_CERTIFICATION_PLAN_NOAPI

ERA18 SUMMARY

GATE02
Paper Execution Engine
PASS

GATE03
Paper Risk Engine
PASS

GATE04
Final Audit + GitHub Seal
PASS

CONSTITUTION

Paper/Live Provider Split
Logical Time Only
Rolling Checksum
Replay Certification
Replay Diff
Paper-Live Boundary
Penalty Factor
Delta Ledger
Kill Switch

HEAD
3bf2a540d97f32eac652928d46daf115f1a03983

================================================================================

================================================================================
ERA19 CLOSURE UPDATE
Timestamp: 2026-06-30T05:39:27Z
HEAD: d635900bd363ba9d8437a65181382b3b2568d6db

ERA19_STATUS=CLOSED_VERIFIED_GITHUB_SEALED

CURRENT_ERA=ERA20
CURRENT_GATE=GATE01

LAST_COMPLETED=ERA19_GITHUB_SEAL

NEXT_SAFE_STEP=ERA20_GATE01_LIVE_READINESS_DOCTRINE_PLAN_NOAPI

ERA19 SUMMARY

GATE01
Runtime Activation and Resilience
PASS

GATE02
Long Run Stability
PASS

GATE03
Paper Performance
PASS

GATE04
Replay Certification
PASS

GATE05
Shadow Market
PASS

GATE06
Drift Monitor
PASS

GATE07
War Game
PASS

GATE08
Runtime Certification
PASS

GATE09
Final Runtime Audit
PASS_READY_FOR_GITHUB_SEAL

CERTIFIED
Paper Runtime
Event-Driven Runtime
Logical Time Only
Triple Ledger
GSN Chain
Append-Only + WAL + Immutable Seal
Replay Proof
Shadow Market
Drift Monitor
War Game Resilience
Live Boundary Disabled

LIVE SAFETY
LIVE_TRADE=false
WALLET=false
SIGNING=false
REAL_ORDER=false
ORDER_CREATE=false

HEAD
d635900bd363ba9d8437a65181382b3b2568d6db

================================================================================



----------------------------------------------------------------------------

## ERA23A FIX1 - V1/V8 DETAILED ROADMAP AND ALMANAC BINDING

Updated: 2026-07-03T07:40:37.535380Z
HEAD: d76341c1c7067ebc3ea0fdbb9ba2efe587baad2e

This update binds every V line to its ERA range, purpose, next connection,
and closure-update requirement.

Rule:
Every V closure and every ERA closure must update:
- PROJECT_RUNTIME.json
- data/tokenoskobi_v1_v8_master_era_roadmap.json
- 03_ROADMAP.md
- 04_ALMANAC.md
- 05_ATLAS.md
- 06_PROJECT_MASTER_STATE.md
- 07_PROJECT_HANDOFF.md

Next work unit:
ERA23B_AI_COMMAND_AND_RED_TEAM_ORCHESTRATION_PROTOCOL_PLAN

NO_DUPLICATE_CANON_RULE:
ONE PURPOSE = ONE CANONICAL FILE.

----------------------------------------------------------------------------



----------------------------------------------------------------------------

## ERA23A_FIX2_FULL_V1_V8_MASTER_ROADMAP_CANONICAL_REPAIR

Updated: 2026-07-03T08:39:33.400590+00:00
HEAD: 0aca774f1b72a8c87995697b60918a262cdc022d

Full Tokenoskobi OS V1-V8 roadmap is now canonical in:

data/tokenoskobi_v1_v8_master_era_roadmap.json

This JSON contains:
- V1 PHASE0-PHASE60 summary
- V2 V2_00-V2_60 summary
- V3 ERA21-ERA60 detailed chain
- V4 ERA61-ERA80 planned chain
- V5 ERA81-ERA100 planned chain
- V6 ERA101-ERA120 planned chain
- V7 ERA121-ERA140 planned chain
- V8 ERA141-ERA160 planned chain
- ERA/V closure update rule
- NO_DUPLICATE_CANON_RULE
- MEASURE_BEFORE_SPEND
- GRACEFUL_DECAY retirement doctrine

Next work unit:
ERA23B_AI_COMMAND_AND_RED_TEAM_ORCHESTRATION_PROTOCOL_PLAN

----------------------------------------------------------------------------


----------------------------------------------------------------------------

## ERA23A_FIX3_SELF_BOOTABLE_CANONICAL_BOOT_REPAIR

UPDATED_AT: 2026-07-03T09:55:26.862443+00:00
HEAD: a1827a5bd39a6bfc526e12a16e2ad91546010279

SELF-BOOTABLE CANONICAL BOOT

Yeni pencere eski sohbete dönmeden yalnızca repo dosyalarından devam edebilmelidir.

READ ORDER:
1. PROJECT_RUNTIME.json
2. data/tokenoskobi_v1_v8_master_era_roadmap.json
3. 03_ROADMAP.md
4. 04_ALMANAC.md
5. 06_PROJECT_MASTER_STATE.md

SOURCE RULES:
- Current state source: PROJECT_RUNTIME.json
- Roadmap source: data/tokenoskobi_v1_v8_master_era_roadmap.json
- Register/almanac source: 04_ALMANAC.md
- AI memory is not source of truth.

ROADMAP MAP:
- V1 = PHASE0-PHASE60 CLOSED
- V2 = V2_00-V2_60 CLOSED
- V3 = ERA21-ERA60 ACTIVE
- V4 = ERA61-ERA80 PLANNED
- V5 = ERA81-ERA100 PLANNED
- V6 = ERA101-ERA120 PLANNED
- V7 = ERA121-ERA140 PLANNED
- V8 = ERA141-ERA160 PLANNED

ROLLING_ROADMAP_POLICY:
- Current V = HIGH DETAIL
- Next V = MEDIUM DETAIL
- Future V = STRATEGIC DETAIL
- When a V closes, next V is expanded.
- Closed ERA/V is immutable.

LAST CLOSED:
ERA23A_FIX2_FULL_V1_V8_MASTER_ROADMAP_CANONICAL_REPAIR

NEXT WORK UNIT:
ERA23B_AI_COMMAND_AND_RED_TEAM_ORCHESTRATION_PROTOCOL_PLAN

NO_DUPLICATE_CANON_RULE:
ONE PURPOSE = ONE CANONICAL FILE.

----------------------------------------------------------------------------

<!-- ERA23C_CANONICAL_SYNCHRONIZATION_RECORD_BEGIN -->

# ERA23C CANONICAL SYNCHRONIZATION RECORD

- RECORD_STATUS: SUPERSEDED_BY_ERA23Z
- WORK_UNIT: ERA23C_CANONICAL_SYNCHRONIZATION_AND_DRIFT_REPAIR
- CHANGE_TYPE: APPEND_CANONICAL_SYNC_RECORD
- LAST_CLOSED_WORK_UNIT: ERA23B_AI_COMMAND_AND_RED_TEAM_ORCHESTRATION_PROTOCOL_PLAN
- ACTIVE_WORK_UNIT: ERA23C_CANONICAL_SYNCHRONIZATION_AND_DRIFT_REPAIR
- NEXT_SAFE_STEP: USER_APPROVAL_FOR_GIT_ADD_COMMIT_PUSH
- SOURCE_OWNER_RUNTIME: PROJECT_RUNTIME.json
- SOURCE_OWNER_ROADMAP: data/tokenoskobi_v1_v8_master_era_roadmap.json
- UPDATED_AT_UTC: 2026-07-03T11:21:03.099692+00:00
- GIT_HEAD_AT_APPLY: 723912fc7e7142beddffddf9bf8b117857744469
- RULE: Historical records are preserved. Older current markers are superseded, not deleted.
- ACTIVE_STATE_SOURCE_AFTER_ERA23Z: PROJECT_RUNTIME.json
<!-- ERA23C_CANONICAL_SYNCHRONIZATION_RECORD_END -->

<!-- ERA23_FINAL_CLOSURE_RECORD_BEGIN -->

## 2026-07-03T16:08:02.806475+00:00 — ERA23Z_OS_CORE_HARDENING_FINAL_CLOSURE

STATUS: LOCAL_READY_FOR_FINAL_SEAL
RESULT: ERA23 final canonical governance and closure documents prepared.
HEAD: d30d1f086178e858788b1176dbf790bc95d2f472
PUSH_POLICY: Single push only at ERA closure.
NEXT: Final local test, commit and push after PASS.
<!-- ERA23_FINAL_CLOSURE_RECORD_END -->

<!-- ERA24_WORKFLOW_CONSOLIDATION_RECORD_BEGIN -->
## ERA24 WORKFLOW CONSOLIDATION

STATUS: LOCAL_ACTIVE
UPDATED_AT_UTC: 2026-07-04T04:30:43.992133+00:00
HEAD_AT_UPDATE: e50aca319ba99fede7521254e6dca5cac80a74ab

ERA24 is treated as one capability: Engineering Decision Engine.

Internal baseline outputs are preserved as evidence:
- Reliability
- Performance
- Security
- Statistics
- Probability
- Opportunity Cost

RULE:
Do not continue ERA24 as ERA24A/B/C/D/E/F/G chain.
Continue as one ERA-level capability with local test, close, and single ERA push.
<!-- ERA24_WORKFLOW_CONSOLIDATION_RECORD_END -->

<!-- ERA24_ENGINEERING_DECISION_ENGINE_RECORD_BEGIN -->
## ERA24 ENGINEERING DECISION ENGINE

STATUS: LOCAL_CLOSED_READY_FOR_GITHUB_SEAL
UPDATED_AT_UTC: 2026-07-04T04:34:28.994997+00:00
HEAD_AT_UPDATE: e50aca319ba99fede7521254e6dca5cac80a74ab

ERA24 is one consolidated capability, not an A/B/C/D/E/F work-unit chain.

INTERNAL EVIDENCE:
- Reliability baseline: PASS
- Performance baseline: PASS
- Security baseline: PASS
- Statistics baseline: PASS
- Probability baseline: PASS
- Opportunity Cost baseline: PASS

RESULT:
Engineering Decision Engine foundation baseline is locally closed and ready for single ERA-level GitHub seal.

NEXT:
ERA25 planning starts only after ERA24 GitHub seal verification.
<!-- ERA24_ENGINEERING_DECISION_ENGINE_RECORD_END -->

<!-- ERA25_SCIENTIFIC_DECISION_FRAMEWORK_RECORD_BEGIN -->
## ERA25 SCIENTIFIC DECISION FRAMEWORK

STATUS: LOCAL_CLOSED_READY_FOR_GITHUB_SEAL
UPDATED_AT_UTC: 2026-07-04T05:35:41.099868+00:00
HEAD_AT_UPDATE: f6e2be9537dacbdcf5f2dfb226c19da529087d72

ERA25 defines the Scientific Decision Framework contract.

RESULT:
- ECG v1 contract check: PASS
- SDF contract definition: PASS
- SDF contract test: PASS
- Runtime trade execution: NOT INCLUDED
- Orchestration: NOT INCLUDED
- A/B/C work-unit chain: NOT USED

OUTPUTS:
- data/era25_ecg_v1_contract_check.json
- data/era25_sdf_contract_v1.json
- data/era25_sdf_contract_test_v1.json

NEXT:
ERA26 planning starts only after ERA25 GitHub seal verification.
<!-- ERA25_SCIENTIFIC_DECISION_FRAMEWORK_RECORD_END -->

<!-- ERA26_ADAPTIVE_INTELLIGENCE_ENGINE_RECORD_BEGIN -->
## ERA26 ADAPTIVE INTELLIGENCE ENGINE

STATUS: LOCAL_CLOSED_READY_FOR_GITHUB_SEAL
UPDATED_AT_UTC: 2026-07-04T06:14:01.985735+00:00
HEAD_AT_UPDATE: bea7dddb066c8dcba933309e6475b42342f11014

ERA26 defines Adaptive Intelligence for selecting and weighting existing ERA25 decision models.

RESULT:
- Adaptive intelligence contract: PASS
- Contract test: PASS
- Adaptive weight table: PASS
- Weight table test: PASS
- New math model creation: NOT INCLUDED
- Trade execution: NOT INCLUDED
- Hot path execution: NOT INCLUDED

OUTPUTS:
- data/era26_adaptive_intelligence_contract_v1.json
- data/era26_contract_test_v1.json
- data/era26_adaptive_weight_table_v1.json
- data/era26_adaptive_weight_table_test_v1.json

NEXT:
ERA27 planning starts only after ERA26 GitHub seal verification.
<!-- ERA26_ADAPTIVE_INTELLIGENCE_ENGINE_RECORD_END -->

<!-- ERA27_PREDICTIVE_INTELLIGENCE_ENGINE_RECORD_BEGIN -->
## ERA27 PREDICTIVE INTELLIGENCE ENGINE

STATUS: LOCAL_CLOSED_READY_FOR_GITHUB_SEAL
UPDATED_AT_UTC: 2026-07-04T06:37:20.756489+00:00
HEAD_AT_UPDATE: f918cab606eb1a739a27ef762daf2fc283fba140

ERA27 defines Predictive Intelligence for probabilistic future scenarios.

RESULT:
- Predictive intelligence contract: PASS
- Prediction contract test: PASS
- Scenario engine: PASS
- Scenario engine test: PASS
- Trade execution: NOT INCLUDED
- Risk modification: NOT INCLUDED
- Decision authority: NOT INCLUDED

OUTPUTS:
- data/era27_predictive_intelligence_contract_v1.json
- data/era27_prediction_contract_test_v1.json
- data/era27_scenario_engine_v1.json
- data/era27_scenario_engine_test_v1.json

NEXT:
ERA28 planning starts only after ERA27 GitHub seal verification.
<!-- ERA27_PREDICTIVE_INTELLIGENCE_ENGINE_RECORD_END -->

<!-- ERA28_AI_ORCHESTRATION_AND_VETO_GATE_BEGIN -->
## ERA28 AI ORCHESTRATION AND VETO GATE

STATUS: LOCAL_CLOSED_READY_FOR_GITHUB_SEAL
UPDATED_AT_UTC: 2026-07-04T07:31:43.860699+00:00
HEAD_AT_UPDATE: 31c90a6654a5d50b1868a308bd16b759bc05b92c

RESULT:
- Orchestration Contract: PASS
- Veto Gate Contract: PASS
- Contract Test: PASS
- Human Final Authority: PASS
- Trade Authority: NONE
- Wallet Authority: NONE
- Merge Authority: NONE

OUTPUTS:
- data/era28_ai_orchestration_veto_gate_contract_v1.json
- data/era28_orchestration_contract_test_v1.json

NEXT:
ERA29 starts only after ERA28 GitHub seal verification.
<!-- ERA28_AI_ORCHESTRATION_AND_VETO_GATE_END -->

<!-- ERA29_CONTINUOUS_EVOLUTION_AND_MODULAR_HEALTH_LAYER_RECORD_BEGIN -->
## ERA29 CONTINUOUS EVOLUTION AND MODULAR HEALTH LAYER

STATUS: LOCAL_CLOSED_READY_FOR_GITHUB_SEAL
UPDATED_AT_UTC: 2026-07-04T10:03:06.053917+00:00
HEAD_AT_UPDATE: 5b54d68f6c51450f60b255ff53cf13d0d2f30f44

RESULT:
- Module Registry: PASS
- Module Registry Test: PASS
- Health Matrix: PASS
- Health Matrix Test: PASS
- Complexity Budget v1: PASS
- Complexity Budget v3 + Final Evolution Score Ledger: PASS
- Continuous Evolution Protocol: PASS
- CEP Test: PASS

DOCTRINE:
- No module is permanent.
- Constitution and Evidence Chain are permanent.
- Every change must leave the system measurably stronger.
- Evolution Score is decision support only, not final authority.

OUTPUTS:
- data/era29_module_registry_v1.json
- data/era29_module_registry_test_v1.json
- data/era29_health_matrix_v1.json
- data/era29_health_matrix_test_v1.json
- data/era29_complexity_budget_v1.json
- data/era29_complexity_budget_v3.json
- data/final_evolution_score_ledger_v1.json
- data/era29_cep_v1.json
- data/era29_cep_test_v1.json

NEXT:
Shadow Runtime Decision Integrity starts only after ERA29 GitHub seal verification.
<!-- ERA29_CONTINUOUS_EVOLUTION_AND_MODULAR_HEALTH_LAYER_RECORD_END -->

---

## ALMANAC YAZIM STANDARDI

Bu eser aşağıdaki canonical rehbere göre geliştirilir:

`docs/design/ALMANAC_AUTHORING_GUIDE.md`

## ERA42 Final Close — 2026-07-07T10:34:59.172133+00:00
- Status: CLOSED
- Final gate: PASS_ERA42_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI
- Next: ERA43_NEWS_SHADOW_REALTIME_READONLY_REAL_RUN_PLAN_NOAPI
- Health: root/database size check recorded.


## ERA44 Final Close — 2026-07-08T05:04:37.765358+00:00
- Status: CLOSED
- Final gate: PASS_ERA44_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI
- Next: ERA45_CODEX_FULL_VERIFICATION_AUDIT_NOAPI
- Health: root/database size check recorded.


## ERA44 Final Close — 2026-07-08T05:05:45.104744+00:00
- Status: CLOSED
- Final gate: PASS_ERA44_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI
- Next: ERA45_CODEX_FULL_VERIFICATION_AUDIT_NOAPI
- Health: root/database size check recorded.


## ERA44 Final Close — 2026-07-08T05:08:46.042076+00:00
- Status: CLOSED
- Final gate: PASS_ERA44_FINAL_REVIEW_AND_CANONICAL_CLOSE_NOAPI
- Next: ERA45_CODEX_FULL_VERIFICATION_AUDIT_NOAPI
- Health: root/database size check recorded.

## ERA46_DISCIPLINE_LAYER_PLAN_NOAPI
- UTC: 2026-07-08T09:33:39.212698Z
- Status: CLOSED / PUSHED_PENDING_VERIFY
- Scope: PLAN_ONLY_NO_IMPLEMENTATION
- Decision: PASS_WITH_GUARDS
- Based on HEAD: 8072a5104080ca1a9876665fa23a5a9401aa6a32
- Next: ERA47_DISCIPLINE_LAYER_VALIDATION_NOAPI

## ERA48_REACHABILITY_CLASSIFICATION_NOAPI
- UTC: 2026-07-08T10:03:11.060911Z
- Status: CLOSED
- Decision: WARN_ACTIVE_RED_REQUIRES_REVIEW
- Scope: CLASSIFICATION_ONLY_NO_IMPLEMENTATION
- Based on HEAD: 442fc6ea970e1a51d5dd8c4774f43cb590cceeb6
- Next: ERA49_ACTIVE_SURFACE_REVIEW_NOAPI

## ERA50_ACTIVE_RUNTIME_RISK_DECISION_NOAPI
- UTC: 2026-07-08T10:11:02.446239Z
- Status: CLOSED
- Decision: PASS_RISK_DECIDED_NO_DISCIPLINE_BLOCKER
- Scope: RISK_DECISION_ONLY_NO_IMPLEMENTATION
- Based on HEAD: 96ea75d404ce2064c879396e821ed16c71cc8aa3
- Next: ERA51_DISCIPLINE_IMPLEMENTATION_GO_NOGO_NOAPI

## HBR_CANONICAL_STATE_SYNC_NOAPI — 2026-07-10T10:48:41.748229+00:00

- Decision: `OK_HBR_CANONICAL_STATE_SYNC_NOAPI`
- Authority: `PROJECT_RUNTIME.json`
- HBR-B seal: `SOLID`
- HBR-C status: `READY_NOT_EXECUTED`
- Next: `HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI`
- Collision: `UNKNOWN_UNTIL_HBR_C`
- Previous HEAD: `86f4547bd97129e23bb40a57cfeb4a2ff4b6bf89`

## HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI — 2026-07-10T11:23:01.070211+00:00

- Decision: `OK_HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI`
- Collision result: `NO_PRODUCTION_COLLISION`
- Policy gate: `HOLD_ZERO_ELIGIBLE_INPUT`
- Input count: `55`
- Locked-window eligible count: `0`
- DB mode: `SQLITE_MODE_RO_QUERY_ONLY`
- DB total changes: `0`
- Production insert: `false`
- Next safe step: `HBR_SOURCE_WINDOW_REPAIR_OR_CLOSE_DECISION_NOAPI`
- Previous HEAD: `d9b6c8bc95217b7161694a73903fe4e8e676be93`

## HBR_SOURCE_WINDOW_REPAIR_OR_CLOSE_DECISION_NOAPI — 2026-07-10T11:28:35.885453+00:00

- Decision: `OK_HBR_SOURCE_WINDOW_CLOSE_DECISION_NOAPI`
- Choice: `CLOSE_CURRENT_HBR_ATTEMPT_NO_WINDOW_REPAIR`
- Current HBR attempt: `CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT`
- HBR-C collision result: `NO_PRODUCTION_COLLISION`
- Sealed input count: `55`
- Locked-window eligible count: `0`
- Window repair now: `false`
- HBR-D/E/F executed: `false`
- Future retry: `archive-capable source + new input seal`
- Next safe step: `POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_NOAPI`
- Previous HEAD: `e7c850dc238cc10af2a2e47966d6bcd0876f592c`

## POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_NOAPI — 2026-07-10T11:41:45.442938+00:00

- Decision: `OK_POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_NOAPI`
- HBR: `CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT`
- Runtime binding: `BOUND_HOT_ONLY_EXECUTION_VERIFIED`
- Runtime order: `raw/derived success → bounded hot refresh`
- Hot queue: `50/50`
- DB delta: `0`
- Service/timer change: `false`
- Trade authority: `false`
- Dynamic runtime outputs: `removed from Git index; local live files preserved and ignored`
- Full timer cycle after binding: `not yet observed`
- Next: `POST_ERA54_HOT_INGRESS_BOUND_RUNTIME_FIRST_OBSERVATION_NOAPI`
- Previous HEAD: `49824938a074e51842d35dd2640f22dbd92f4277`

## POST_ERA54_HOT_INGRESS_BOUND_RUNTIME_FIRST_OBSERVATION_NOAPI — 2026-07-10T12:30:25.265514+00:00

- Decision: `OK_POST_ERA54_HOT_INGRESS_BOUND_RUNTIME_FIRST_OBSERVATION_NOAPI`
- Natural timer cycle: `OBSERVED_VERIFIED`
- Evidence source: `RUNTIME_STATE_CORRELATED_TO_SYSTEMD_SERVICE_CYCLE`
- Service success: `true`
- Derived counts equal: `true`
- Hot queue: `50/50`
- Panel bridge: `OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED`
- NEWS operational baseline: `CLOSED_VERIFIED_BOUNDED_RUNTIME`
- Next safe step: `NEXT_MAJOR_PROJECT_LINE_SELECTION_AFTER_NEWS_OPERATIONAL_BASELINE_CLOSURE`
- Previous HEAD: `4b72e4cb675e7011a379135cffa1e92c08463908`

<!-- ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_ENTRY_V1 -->
## ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI — 2026-07-10T12:45:23.567774+00:00

- Decision: `OK_ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI`
- ERA54: `CLOSED_VERIFIED_BOUNDED_RUNTIME`
- NEWS baseline: `CLOSED_VERIFIED_BOUNDED_RUNTIME`
- Natural timer cycle: `OBSERVED_VERIFIED`
- DB counts: raw `372`, match `184`, signal `184`, score `184`
- Coverage: market `39`, adversarial `59`
- Hot queue: `50/50`
- Index and README startup pointers corrected.
- Mandatory ERA closure document set completed, including `PROJECT_HISTORY.json` and `05_ATLAS.md`.
- ERA55 opened: `false`
- Next: `NEXT_MAJOR_PROJECT_LINE_SELECTION_AFTER_NEWS_OPERATIONAL_BASELINE_CLOSURE`
- Technical closure HEAD: `c72995c352a76fe8557de369228f86e6f7d2846e`

---

## ROOT CANONICAL REMAINING SCOPE NORMALIZATION

- UTC: `2026-07-10T15:59:48.209051+00:00`
- Status: `CLOSED_VERIFIED`
- `07_PROJECT_HANDOFF.md` reduced to continuation context only.
- `PROJECT_BOOT.json` reduced to stable boot contract only.
- `PROJECT_RUNTIME.json` transient workflow metadata normalized.
- `06_PROJECT_MASTER_STATE.md` aligned with the runtime contract.
- `01_INDEX.md` verified unchanged as navigation only.
- `PROJECT_HISTORY.json` preserved as append-only history.
- Next safe step remains `ERA55_SELECTION_GATE`.
- New ERA opened: `false`.

---

## ERA55 OPEN AND ERA55A_1 READ-ONLY INSPECTION

- UTC: `2026-07-11T06:15:55.480509+00:00`
- ERA55 status: `OPEN`
- Completed substep: `ERA55A_1_READONLY_INSPECTION`
- Result: `WARN_P0_FINDINGS_RECORDED_READONLY`
- Inspection scope: systemd, timer, runner, queue policy, SQLite PRAGMA/integrity and panel visibility.
- Live runtime, DB, service, timer and panel mutation: `false`
- Identified risk codes: `QUEUE_OVERFLOW_SILENT_TRUNCATION_RISK, SQLITE_JOURNAL_MODE_NOT_WAL, PANEL_PROPAGATION_LATENCY_NOT_YET_INSTRUMENTED`
- Gemini Red Team review: `required`
- Next safe step: `ERA55A_2_GRANULAR_INSTRUMENTATION_AND_BASELINE_MEASUREMENT_PLAN`

---

## ERA55A_2 GRANULAR INSTRUMENTATION AND BASELINE MEASUREMENT PLAN

- Status: `CLOSED`
- Result: `OK_PLAN_LOCKED_NO_LIVE_MUTATION`
- Measurement approach: external read-only observer.
- Baseline profiles: historical 24h, next natural cycle, hot steady state and logical cold start when naturally available.
- Manual production runner execution: `false`
- Service/timer/DB/queue/panel mutation: `false`
- Production burst load: `false`
- P0 gates: silent queue loss, timer margin and data correctness.
- Gemini Red Team review: required after baseline report.
- Next safe step: `ERA55A_3_NATURAL_CYCLE_BASELINE_COLLECTION`

---

## ERA55A_3 NATURAL CYCLE BASELINE COLLECTION

- Status: `CLOSED`
- Result: `WARN_P0_BASELINE_FINDINGS_RECORDED`
- Historical runner evidence: collected from systemd journal.
- Queue top-50 and overflow evidence: independently reconstructed from display candidates.
- Natural timer-cycle observation: bounded external read-only observer.
- Manual runner execution: `false`
- Service/timer/DB/queue/panel mutation: `false`
- Finding codes: `SILENT_TRUNCATION_CAPABILITY_EXISTS_NOT_OBSERVED, TIMER_OVERLAP_NOT_OBSERVED_24H`
- Optimization apply: `blocked`
- Gemini Red Team review: required after baseline report.
- Next safe step: `ERA55A_4_BASELINE_CONSOLIDATION_AND_EXTENDED_SAMPLE_REVIEW`

---

## ERA55A_4 BASELINE CONSOLIDATION AND EXTENDED SAMPLE REVIEW

- Status: `CLOSED`
- Result: `WARN_BASELINE_SUFFICIENT_FOR_A5_P0_REMAINS_OPEN`
- Baseline sufficient for A5/Gemini: `true`
- Baseline sufficient for optimization apply: `false`
- Historical 24h cycles: `72`
- Journal duration precision: `VARIABLE_PRECISION`
- Precise natural runner duration: `939.311 ms`
- Queue utilization: `100.0%`
- Queue overflow current snapshot: `0`
- Drop ledger: `false`
- P0 queue risk: `OPEN`
- Service/timer/DB/queue/panel mutation: `false`
- Next safe step: `ERA55A_5_BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE`

---

## ERA55A_5 BASELINE REPORT AND GEMINI RED TEAM PACKAGE

- Status: `CLOSED_PACKAGE_READY_REVIEW_PENDING`
- Result: `OK_BASELINE_REPORT_AND_GEMINI_PACKAGE_READY_NO_APPLY`
- Canonical assessment: `OPERATIONALLY_STABLE_LOW_LOAD_WITH_BOUNDARY_RISKS`
- Precise natural runner: `939.311 ms`
- Queue: `50/50`; utilization `100.0%`
- Current overflow: `0`
- Drop ledger: `false`
- P0 queue risk: `OPEN`
- Gemini package: `READY`
- Gemini review: `PENDING`
- Optimization apply: `false`
- Live runtime mutation: `false`
- Next safe step: `ERA55A_6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER`

---

## ERA55A_6 GEMINI RED TEAM REVIEW AND FINDINGS REGISTER

- Status: `CLOSED`
- Result: `BASELINE_ACCEPTED_OPTIMIZATION_REJECTED_UNTIL_P0_CLEARED`
- Baseline verdict: `BASELINE_ACCEPTED`
- Production optimization verdict: `REJECTED_UNTIL_P0_CLEARED`
- Findings: `F1 P0`, `F2 P1`, `F3 P1`, `F4 P2`
- A7 temp-copy design/test: `AUTHORIZED`
- Production apply: `false`
- Next safe step: `ERA55A_7_P0_DROP_LEDGER_DESIGN_AND_TEMP_COPY_TEST`

---

## ERA55A_7 P0 DROP LEDGER DESIGN AND TEMP-COPY TEST

- Status: `CLOSED_TEMP_COPY_TEST_PASS`
- Result: `PASS_P0_LEDGER_DESIGN_TEMP_COPY_VALIDATED_NO_PRODUCTION_MUTATION`
- Source candidates: `70`
- Admitted: `50`
- Overflow ledgered: `10`
- Event count loss: `0`
- UID loss: `0`
- Unledgered disposition: `0`
- Integrity/quick check: `ok/ok`
- Atomic rollback: `true`
- Production unchanged: `true`
- Production apply: `false`
- Next safe step: `ERA55A_8_P0_DROP_LEDGER_POST_TEST_AUDIT_AND_APPLY_DECISION`

---

## ERA55A_8 P0 DROP LEDGER POST-TEST AUDIT AND SCHEMA-ONLY MIGRATION

- Status: `CLOSED_SCHEMA_ONLY_MIGRATION_OK`
- Result: `OK_REPAIRED_SCHEMA_COMPLETE_TEMP_COPY_AND_PRODUCTION_DDL_ONLY`
- Complete disposition test: `OK`
- Production DDL-only migration: `OK`
- Production rows: `0/0`
- Writer active: `false`
- P0 F1 closed: `false`
- Next: `ERA55A_9_P0_LEDGER_WRITER_INTEGRATION_TEMP_COPY_TEST`

---

## ERA55A_9 P0 LEDGER WRITER INTEGRATION TEMP-COPY TEST

- Status: `CLOSED_TEMP_COPY_INTEGRATION_OK`
- Result: `OK_LEDGER_WRITER_TEMP_COPY_INTEGRATION_WITH_RECOVERABLE_PUBLISH_BOUNDARY`
- Source candidates/accounted: `71/71`
- New ledger batch unobservable rows: `0`
- Idempotent replay: `true`
- Replacement atomic rollback: `true`
- Publish recovery: `true`
- Production unchanged: `true`
- Production writer active: `false`
- P0 F1 closed: `false`
- Next safe step: `ERA55A_10_P0_LEDGER_WRITER_POST_TEST_AUDIT_AND_PRODUCTION_APPLY_DECISION`

---

## ALMANAC RECORD INSERTION AND CORRECTION CONSTITUTION

Yeni tamamlanmış kayıt ilgili PASS, PHASE, V veya ERA ailesinin altında tarihsel sıraya eklenir.
Yeni doğrulanmış bilgi mevcut Almanac kaydıyla çakışıyorsa, hatalı kayıt kendi yerinde düzeltilir.
Değiştirilen hatalı kayıt Almanac içinde ikinci bir kopya olarak tutulmaz.
Aynı kapanış, audit, karar veya senkronizasyon olayı birden fazla bağımsız kayıt olarak eklenmez.
Yeni ve çakışmayan tamamlanmış kayıt ilgili aile veya kronolojik kayıt alanına yerleştirilir.
Current state, current gate ve next step ifadeleri yalnız olay tarihindeki tarihsel bağlamı gösterir; güncel durum yetkisi PROJECT_RUNTIME.json dosyasındadır.
Roadmap yönü, Atlas mimari bağı, Manifesto doktrini ve Index navigation bilgisini taşır; Almanac yalnız gerçekleşmiş olayları ve kanıtlanmış geçmişi kaydeder.
Almanacın mevcut yazım şekli, başlık düzeni, boşluk yapısı, yazı tipi ve biçimlendirmesi açık kullanıcı onayı olmadan değiştirilmez.

---

## ERA55A_10 RED TEAM PRODUCTION AUTHORIZATION DECISION

- Status: `CLOSED_PRODUCTION_ACTIVATION_REJECTED`
- Result: `REJECT_PRODUCTION_ACTIVATION_RUNTIME_WRITER_NOT_BOUND`
- A10 remediation shields: `PASS`
- Runtime recovery path: `PRESENT`
- Runtime new ledger writer path: `ABSENT`
- Production DB mutation: `false`
- Production writer activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `ERA55A_11_P0_RUNTIME_LEDGER_WRITER_MODULE_EXTRACTION_AND_TEMP_COPY_BINDING_TEST`

---

## ERA55A_11 RUNTIME LEDGER WRITER MODULE TEMP-COPY BINDING

- Status: `CLOSED_TEMP_COPY_BINDING_OK`
- Result: `OK_RUNTIME_WRITER_MODULE_REAL_SOURCE_TEMP_COPY_BOUND`
- Real source candidates/accounted: `50/50`
- Current gateway queue parity: `true`
- Six-disposition synthetic model: `true`
- Production runtime bound: `false`
- Production mutation: `false`
- P0 F1 closed: `false`
- Next safe step: `ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION`

---

## ERA55A_12 BOUNDED CANARY DECISION

- Status: `CLOSED_BOUNDED_CANARY_REJECTED`
- Result: `REJECT_BOUNDED_CANARY_SOURCE_ALREADY_FILTERED_AND_TRUNCATED`
- Writer module: `VALIDATED`
- Current source: `POST_FILTER_POST_DEDUP_POST_TRUNCATION`
- Pre-gateway source bound: `false`
- Production mutation: `false`
- Bounded canary authorized: `false`
- Production writer activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_EXTRACTION_AND_TEMP_COPY_BINDING_TEST`

---

## ERA55A_13 PRE-GATEWAY STREAM TEMP-COPY BINDING

- Status: `CLOSED_TEMP_COPY_BINDING_OK`
- Result: `OK_COMPLETE_PRE_GATEWAY_JSONL_STREAM_TEMP_COPY_BOUND`
- Real pre-gateway candidates: `106`
- Display projection candidates: `50`
- Physical non-empty line accounting: `true`
- Unobservable rows: `0`
- Queue parity: `true`
- Production mutation: `false`
- Bounded canary authorized: `false`
- Production writer activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `ERA55A_14_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION`

---

## ERA55A_14 BOUNDED CANARY DECISION

- Status: `CLOSED_BOUNDED_CANARY_REJECTED`
- Result: `REJECT_BOUNDED_CANARY_QUEUE_SEMANTIC_PARITY_NOT_PROVEN`
- Source candidates: `106`
- Complete accounting: `true`
- Legacy rebuild matches current hot: `true`
- Pre-gateway writer matches legacy queue: `false`
- Single-cycle bounded canary authorized: `false`
- General production activation authorized: `false`
- Production mutation: `false`
- P0 F1 closed: `false`
- Next safe step: `ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST`

---

## ERA55A_15 QUEUE SEMANTIC PARITY REPAIR

- Status: `CLOSED_TEMP_COPY_PARITY_REPAIR_OK`
- Result: `OK_COMPLETE_LEDGER_LEGACY_QUEUE_SEMANTIC_PARITY_TEMP_COPY`
- Source candidates: `106`
- Legacy queue: `50`
- Unobservable rows: `0`
- Exact legacy parity: `true`
- Production mutation: `false`
- Next: `ERA55A_16_P0_QUEUE_PARITY_POST_TEST_AUDIT_AND_SINGLE_CYCLE_CANARY_DECISION`

---

## ERA55A_16 SINGLE-CYCLE CANARY DECISION

- Status: `CLOSED_SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED`
- Result: `OK_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_AUTHORIZED`
- Fresh source candidates: `106`
- Unobservable rows: `0`
- Exact legacy parity: `true`
- Production mutation: `false`
- Single-cycle canary authorized: `true`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `ERA55A_17_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_AND_POST_AUDIT`

---

## ERA55A_17 SINGLE NATURAL CYCLE BOUNDED CANARY

- Status: `CLOSED_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_OK_WITH_POST_COMMIT_BRIDGE_RECOVERY`
- Result: `OK_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_COMPLETED_POST_COMMIT_BRIDGE_RECOVERY`
- Runner cycles executed: `1`
- Second canary cycle executed: `false`
- Production batch rows: `1`
- Production ledger rows: `106`
- Source candidates: `106`
- Unobservable rows: `0`
- Panel bridge recovery: `byte-preserving atomic copy`
- Panel hot hash parity: `true`
- Runtime overrides removed: `true`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `ERA55A_18_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION`

---

## ERA55A_18 POST-CANARY RED-TEAM PRODUCTION DECISION

- Status: `CLOSED_GENERAL_PRODUCTION_ACTIVATION_REJECTED`
- Result: `REJECT_GENERAL_PRODUCTION_ACTIVATION_END_TO_END_SUCCESS_AND_AUTOMATIC_ROLLBACK_NOT_PROVEN`
- Valid canary batch: `true`
- Automatic rollback observed: `false`
- End-to-end runner success proven: `false`
- General production activation authorized: `false`
- New canary authorized: `false`
- P0 F1 closed: `false`
- Option B authorized: `false`
- Next safe step: `ERA55A_19_P0_AUTOMATIC_ROLLBACK_AND_END_TO_END_SUCCESS_REMEDIATION_TEMP_COPY_TEST`

---

## ERA55A_19 ROLLBACK AND END-TO-END REMEDIATION TEMP COPY

- Status: `CLOSED_TEMP_COPY_REMEDIATION_OK`
- Result: `OK_AUTOMATIC_ROLLBACK_AND_END_TO_END_SUCCESS_REMEDIATION_TEMP_COPY`
- Archive-trigger-safe rollback: `true`
- Rollback failure exposed: `true`
- Isolated runner HOT_END:0: `true`
- Idempotent replay: `true`
- Recovery after output loss: `true`
- Production mutation: `false`
- New production canary authorized: `false`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `ERA55A_20_P0_POST_REMEDIATION_AUDIT_AND_PRODUCTION_CANARY_DECISION`

---

## ERA55A_20 POST-REMEDIATION PRODUCTION CANARY DECISION

- Status: `CLOSED_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED`
- Result: `OK_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED`
- Independent rollback audit: `true`
- Fresh source candidates: `107`
- Unobservable rows: `0`
- Prospective batch distinct: `true`
- One production canary authorized: `true`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Option B authorized: `false`
- Next safe step: `ERA55A_21_P0_SINGLE_NATURAL_CYCLE_POST_REMEDIATION_CANARY_APPLY_AND_POST_AUDIT`

---

## ERA55A_21 DYNAMIC-IDENTITY POST-REMEDIATION CANARY

- Status: `CLOSED_POST_REMEDIATION_DYNAMIC_IDENTITY_SINGLE_CYCLE_CANARY_OK`
- Result: `OK_POST_REMEDIATION_DYNAMIC_IDENTITY_SINGLE_CYCLE_PRODUCTION_CANARY_COMPLETED`
- Baseline batch preserved: `true`
- New batch UID: `batch_5b348d2eab80b2929c5ef5b66e407e46`
- New source rows: `107`
- Total batch rows: `2`
- Total ledger rows: `213`
- Runner HOT_END:0: `true`
- Panel hot hash parity: `true`
- Runtime overrides removed: `true`
- Timer state restored: `true`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Option B authorized: `false`
- Next safe step: `ERA55A_22_P0_POST_REMEDIATION_CANARY_RED_TEAM_GENERAL_PRODUCTION_ACTIVATION_DECISION`

---

## ERA55A_22 GENERAL PRODUCTION WRITER ACTIVATION DECISION

- Status: `CLOSED_GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY_AUTHORIZED`
- Result: `OK_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVATION_APPLY_AUTHORIZED`
- Production batch rows: `2`
- Production ledger rows: `213`
- Dynamic canary validated: `true`
- Guarded general activation apply authorized: `true`
- Production writer active now: `false`
- Additional canary authorized: `false`
- P0 F1 closed: `false`
- Option B authorized: `false`
- Next safe step: `ERA55A_23_P0_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_APPLY_AND_POST_AUDIT`

---

## ERA55A_23 GUARDED GENERAL PRODUCTION WRITER ACTIVE

- Status: `CLOSED_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVE_POST_AUDIT`
- Result: `OK_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_ACTIVE`
- Persistent guarded integration: `true`
- Controlled cycle writer status: `IDEMPOTENT_REPLAY_NOOP`
- Controlled cycle batch UID: `batch_5b348d2eab80b2929c5ef5b66e407e46`
- Controlled source rows: `107`
- Production batch rows: `2`
- Production ledger rows: `213`
- Existing batches preserved: `true`
- Runner HOT_END:0: `true`
- Panel hash parity: `true`
- Production writer active: `true`
- P0 F1 closed: `false`
- Option B authorized: `false`
- Next safe step: `ERA55A_24_P0_POST_ACTIVATION_OBSERVATION_AND_P0_F1_CLOSURE_DECISION`

---

## ERA55A_24R NATURAL CYCLE EVIDENCE RECOVERY AND P0 F1 CLOSURE

- Status: `CLOSED_NATURAL_CYCLE_EVIDENCE_RECOVERED_P0_F1_CLOSED`
- Result: `OK_NATURAL_TIMER_EVIDENCE_RECOVERED_P0_F1_CLOSED`
- Recovery reason: `SYSTEMD_SERVICE_STDOUT_DID_NOT_RETAIN_PER_CYCLE_JSON_PAYLOADS`
- Forced service cycle: `false`
- Natural timer cycles observed: `12`
- Production batch rows: `3`
- Production ledger rows: `321`
- Original committed batches preserved: `true`
- Production writer active: `true`
- P0 F1 closed: `true`
- Option B authorized: `false`
- Next safe step: `ERA55A_25_P0_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION`

---

## ERA55A_25 OPTION B READINESS AND AUTHORIZATION DECISION

- Status: `CLOSED_OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED_PRODUCTION_APPLY_BLOCKED`
- Result: `OK_OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED_PRODUCTION_APPLY_BLOCKED`
- Option B: `P1_DELETE_VS_WAL_DURABILITY_LOCK_WRITE_AMPLIFICATION_BENCHMARK`
- Readiness confirmed: `true`
- Temp-copy benchmark authorized: `true`
- Production apply authorized: `false`
- Production mutation: `false`
- Production writer active: `true`
- P0 F1 closed: `true`
- Next safe step: `ERA55A_26_P1_OPTION_B_DELETE_VS_WAL_TEMP_COPY_BENCHMARK`

---

## ERA55A_27 ERA24F OPPORTUNITY COST DECISION

- Status: `CLOSED_OPTION_B_DEFERRED`
- Result: `OK_OPTION_B_DEFERRED_ERA24F_NET_UTILITY_BELOW_BASELINE`
- Decision: `DEFER_OPTION_B`
- ERA24F net utility: `-18.6667`
- Accept baseline: `95.0`
- Production mutation: `false`
- WAL apply authorized: `false`
- Next safe step: `ERA55_POST_OPTION_B_STRATEGIC_PRIORITY_SELECTION_DECISION`


---

## ERA55A27 POST-DECISION CANONICAL ALIGNMENT

- Status: `CLOSED_VERIFIED`
- Result: `OK_A27_AND_NESTED_ERA55_CANONICAL_STATE_ALIGNED`
- ERA55 status: `OPEN`
- Option B: `DEFERRED`
- ERA24F net utility: `-18.6667`
- Production mutation: `false`
- ERA56 opened: `false`
- Next safe step: `ERA55A_28_ERA55_FINAL_CLOSURE_READINESS_AND_CANONICAL_ALIGNMENT_DECISION`

---

## ERA55A_28 FINAL CLOSURE READINESS DECISION

- Status: `CLOSED_READY_FOR_FINAL_ERA55_CLOSURE_DECISION`
- Result: `OK_ERA55_FINAL_CLOSURE_READINESS_CONFIRMED_NOT_YET_CLOSED`
- ERA55 final closure ready: `true`
- ERA55 closed: `false`
- ERA56 opened: `false`
- Production mutation: `false`
- Next safe step: `ERA55_FINAL_CLOSURE_AND_GITHUB_SEAL_DECISION`

---

## ERA55 FINAL CLOSURE AND GITHUB SEAL

- Status: `CLOSED_VERIFIED_READY_FOR_SEAL`
- Result: `OK_ERA55_CLOSED_VERIFIED_READY_FOR_SEAL`
- ERA55 closed: `true`
- ERA56 opened: `false`
- Option B: `DEFERRED`
- Production mutation: `false`
- Next safe step: `ERA56_GLOBAL_INTELLIGENCE_CACHE_OPENING_DECISION`

---

## ERA55 POST-CLOSE CLEANUP AND ERA56 ENTRY HARDENING

- Status: `CLOSED_VERIFIED`
- Result: `OK_CONTROLLED_ARCHIVE_CANONICAL_HARDENING_ERA56_STILL_CLOSED`
- Immutable ERA55 seal tag: `ERA55_FINAL_SEAL`
- Immutable ERA55 seal commit: `f22ce4f07788ec7fbe22a72f872467705b72db5a`
- Runner lock: `ENABLED`
- Active runtime files protected: `2`
- Historical runner copies archived: `2`
- Bulk delete: `false`
- ERA56 opened: `false`
- Next safe step: `ERA56_GLOBAL_INTELLIGENCE_CACHE_OPENING_DECISION`

---

## ERA56 GLOBAL INTELLIGENCE CACHE OPENING

- Status: `OPENED_BOUNDED_DESIGN_ONLY`
- Result: `OK_ERA56_OPENED_OWNERSHIP_AND_OVERLAP_CONTRACT_REQUIRED`
- ERA55 seal preserved: `true`
- Production mutation: `false`
- Cache production apply authorized: `false`
- Source authority duplicated: `false`
- Next safe step: `ERA56A_GLOBAL_CACHE_OWNERSHIP_OVERLAP_AND_REBUILD_CONTRACT`

---

## ERA56A GLOBAL CACHE OWNERSHIP OVERLAP AND REBUILD CONTRACT

- Status: `CLOSED_CONTRACT_LOCKED`
- Result: `OK_ERA56A_OWNERSHIP_OVERLAP_REBUILD_CONTRACT_LOCKED`
- Production mutation: `false`
- Production apply authorized: `false`
- Next safe step: `ERA56B_GLOBAL_CACHE_READONLY_SCHEMA_AND_TEMP_COPY_BUILD`
