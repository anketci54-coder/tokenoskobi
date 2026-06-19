# PASS13 RUNTIME DISCOVERY AUDIT

MODE=READ_ONLY
NO_DB_WRITE=true
NO_RUNTIME_CHANGE=true
NO_API_CALL=true
NO_PANEL_WRITE=true

GOAL=discover existing evidence runtime/readmodel/table/consumer chain for PASS13

===== PASS13 REPORTS =====
reports/LATEST_PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI.md
reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md
reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md
reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md
reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md
reports/LATEST_PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI.md
reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md

===== PASS13 REPORT SIGNALS =====
reports/LATEST_PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI.md:1:# PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI
reports/LATEST_PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI.md:9:DB_WRITES=0
reports/LATEST_PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI.md:12:SERVICE_CHANGES=0
reports/LATEST_PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI.md:16:CORE_EVIDENCE_FAMILIES
reports/LATEST_PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI.md:18:EVIDENCE_TOPOLOGY
reports/LATEST_PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI.md:27:PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI
reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:1:# PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI
reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:9:DB_WRITES=0
reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:12:SERVICE_CHANGES=0
reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:16:EVIDENCE_UNIVERSE_DEFINITION
reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:21:NO_EVIDENCE_NO_DECISION
reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:23:EVIDENCE_DECIDES
reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:29:CORE_EVIDENCE_FAMILIES
reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:32:EVIDENCE_TOPOLOGY
reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:37:PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI
reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md:1:# PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI
reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md:11:PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI
reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md:15:CORE_EVIDENCE_FAMILIES_PRESENT
reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md:17:EVIDENCE_TOPOLOGY_PRESENT
reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md:22:DB_WRITES=0
reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md:25:SERVICE_CHANGES=0
reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md:29:PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI
reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:1:# PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI
reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:11:PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI
reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:15:- evidence_dictionary_v1
reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:16:- evidence_family_registry_v1
reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:17:- evidence_topology_registry_v1
reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:18:- evidence_center_coverage_registry_v1
reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:22:DB_WRITES=0
reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:25:SERVICE_CHANGES=0
reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:34:PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI
reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:1:# PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI
reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:7:MODE=TEMPDB_APPLY_DRYRUN
reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:11:PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI
reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:13:TEMPDB
reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:15:/tmp/pass13d_evidence_dictionary_apply_dryrun_20260611_183434.sqlite
reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:19:DB_WRITES=0
reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:22:SERVICE_CHANGES=0
reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:26:PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI
reports/LATEST_PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI.md:1:# PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI
reports/LATEST_PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI.md:9:DB_WRITES=0
reports/LATEST_PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI.md:12:SERVICE_CHANGES=0
reports/LATEST_PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI.md:22:TEMPDB_EXISTS
reports/LATEST_PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI.md:23:TEMPDB_INTEGRITY
reports/LATEST_PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI.md:27:PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI
reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:1:# PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI
reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:11:PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI
reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:24:- NO_SERVICE_RESTART
reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:31:- evidence_dictionary_v1
reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:32:- evidence_family_registry_v1
reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:33:- evidence_topology_registry_v1
reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:34:- evidence_center_coverage_registry_v1
reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:38:PASS13G_EVIDENCE_DICTIONARY_REAL_APPLY_APPROVAL_GATE_NOAPI

===== PROJECT FILE SIGNALS =====
PROJECT_MASTER_STATE.md:1426:PASS13=EVIDENCE_DICTIONARY -> EVIDENCE_RUNTIME / evidence_event_readmodel
PROJECT_HANDOFF.md:130:PASS13=EVIDENCE_DICTIONARY -> EVIDENCE_RUNTIME / evidence_event_readmodel
docs/INDEX.md:142:EVIDENCE_RUNTIME
docs/INDEX.md:207:PASS13=EVIDENCE_DICTIONARY -> EVIDENCE_RUNTIME / evidence_event_readmodel
docs/CANONICAL_V1_INTELLIGENCE_CORE.md:58:PASS13=EVIDENCE_DICTIONARY -> EVIDENCE_RUNTIME / evidence_event_readmodel
docs/CANONICAL_V1_MASTER_PHASE_PASS_ATLAS.md:246:EVIDENCE_RUNTIME=OPEN
docs/CANONICAL_V1_MASTER_PHASE_PASS_ATLAS.md:271:PURPOSE=EVIDENCE_DICTIONARY
docs/CANONICAL_V1_MASTER_PHASE_PASS_ATLAS.md:355:PASS13=EVIDENCE_DICTIONARY -> EVIDENCE_RUNTIME / evidence_event_readmodel

===== CODE / DB OBJECT NAME SIGNALS READONLY =====
./reports/LATEST_PHASE19N_REPUTATION_SCHEMA_BASELINE_ACCEPTANCE_NOAPI.md:44:TARGET_TABLES=rejection_micro_log,entity_reputation_ledger,entity_reputation_evidence_events,repeat_offender_fast_kill_cache,external_reputation_comparison_events
./reports/LATEST_PHASE19N_REPUTATION_SCHEMA_BASELINE_ACCEPTANCE_NOAPI.md:48:LIVE_ROW_COUNTS={rejection_micro_log: 0, entity_reputation_ledger: 0, entity_reputation_evidence_events: 0, repeat_offender_fast_kill_cache: 0, external_reputation_comparison_events: 0}
./reports/LATEST_PASS16C_MARKET_STRUCTURE_SCHEMA_PLAN_NOAPI.md:14:market_structure_evidence_ledger_v1
./reports/LATEST_PHASE20A_WHALE_ENTITY_INTELLIGENCE_ARCHITECTURE_PLAN_NOAPI.md:44:- `P02_EVIDENCE_BEFORE_LABEL`: Her entity etiketi evidence_event ve confidence ile taşınır; kanıtsız whale etiketi yok. Reason: Manifesto: veri varsa veri kadar konuş; kanıtsız bilgi yok.
./reports/LATEST_PHASE20A_WHALE_ENTITY_INTELLIGENCE_ARCHITECTURE_PLAN_NOAPI.md:71:- `whale_entity_evidence_events_v1`: Her entity/cluster etiketi için kanıt satırı. Action: `PLAN_ONLY_NO_SCHEMA`
./reports/LATEST_PHASE19V_REPUTATION_MICRO_LOG_LIVE_WRITER_DRYRUN_ACCEPTANCE_NOAPI.md:44:TEMP_DB_ROW_COUNTS={'dryrun_rejection_micro_log': 10, 'dryrun_entity_reputation_ledger': 25, 'dryrun_entity_reputation_evidence_events': 27, 'dryrun_repeat_offender_fast_kill_cache': 19, 'dryrun_external_reputation_comparison_events': 1}
./reports/LATEST_PHASE5E1_SCHEMA_TEMP_DRYRUN_FAILURE_DIAGNOSE_NOAPI.md:15:- table=`outcome_memory_events_v2` variants=`2` sources=`['/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql', '/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql', '/root/tokenoskobi_clean_v1/_PHASE5D_OUTCOME_MEMORY_SKELETON_PLAN_NOAPI/20260601_000102/phase5d_future_outcome_memory_schema_plan_noapi.sql']`
./reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md:1:# PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI
./reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md:11:PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI
./reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md:29:PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI
./reports/LATEST_PHASE22CLEANUP3_POST_ARCHIVE_AND_DB_STATUS_CHECK_NOAPI.md:41:- token_score_evidence_events: `10`
./reports/LATEST_NEWS1_NARRATIVE_CORE_DESIGN_NOAPI.md:39:- token_score_evidence_events: exists=`True` rows=`10`
./reports/LATEST_NEWS1_NARRATIVE_CORE_DESIGN_NOAPI.md:58:- existing_tables: `news_signal_events, token_score_evidence_events`
./reports/LATEST_NEWS1_NARRATIVE_CORE_DESIGN_NOAPI.md:76:- existing_tables: `news_signal_events, token_score_evidence_events`
./reports/LATEST_NEWS1_NARRATIVE_CORE_DESIGN_NOAPI.md:94:- existing_tables: `token_score_snapshots, token_score_evidence_events, source_gate_decisions`
./reports/LATEST_NEWS1_NARRATIVE_CORE_DESIGN_NOAPI.md:129:- present_existing_tables: `news_signal_events, token_score_evidence_events`
./reports/LATEST_NEWS1_NARRATIVE_CORE_DESIGN_NOAPI.md:141:- present_existing_tables: `news_signal_events, token_score_evidence_events`
./reports/LATEST_NEWS1_NARRATIVE_CORE_DESIGN_NOAPI.md:153:- present_existing_tables: `token_score_snapshots, token_score_evidence_events, source_gate_decisions`
./reports/LATEST_PHASE19E_REJECTION_MICRO_LOG_AND_INTERNAL_REPUTATION_LEDGER_PLAN_NOAPI.md:38:PLANNED_MODULES=REJECTION_MICRO_LOG_V1,ENTITY_REPUTATION_LEDGER_V1,ENTITY_REPUTATION_EVIDENCE_EVENTS_V1,REPEAT_OFFENDER_FAST_KILL_CACHE_V1,EXTERNAL_REPUTATION_COMPARISON_EVENTS_V1,CRITICAL_PATH_LATENCY_GUARD_V1
./reports/LATEST_DATA_PIPELINE_SCORE_ARCHITECTURE_PLAN_NOAPI.md:35:| `normalized_evidence_layer` | convert all raw inputs to a common evidence shape | `normalized_evidence_events` |
./reports/LATEST_DATA_PIPELINE_SCORE_ARCHITECTURE_PLAN_NOAPI.md:104:- `normalized_evidence_events`
./reports/LATEST_PHASE5L_EVIDENCE_BACKFILL_POST_AUDIT_NOAPI.md:25:- `deployer_receipt_evidence_events_v1` current=`18` delta=`18` expected_delta=`18`
./reports/LATEST_PHASE5L_EVIDENCE_BACKFILL_POST_AUDIT_NOAPI.md:26:- `evidence_event_ledger_v1` current=`1` delta=`1` expected_delta=`1`
./reports/LATEST_PHASE5L_EVIDENCE_BACKFILL_POST_AUDIT_NOAPI.md:27:- `initial_holder_evidence_events_v1` current=`7` delta=`7` expected_delta=`7`
./reports/LATEST_PHASE19F_REJECTION_MICRO_LOG_AND_INTERNAL_REPUTATION_LEDGER_DRYRUN_NOAPI.md:42:EVIDENCE_EVENT_COUNT=47
./reports/LATEST_PHASE19F_REJECTION_MICRO_LOG_AND_INTERNAL_REPUTATION_LEDGER_DRYRUN_NOAPI.md:104:EVIDENCE_EVENTS_JSONL=/root/tokenoskobi_clean_v1/_PHASE19F_REJECTION_MICRO_LOG_AND_INTERNAL_REPUTATION_LEDGER_DRYRUN_NOAPI/20260604_133623/phase19f_dryrun_entity_reputation_evidence_events.jsonl
./reports/LATEST_PASS15D_CONTRACT_DNA_SCHEMA_DRYRUN_NOAPI.md:18:contract_dna_evidence_ledger_v1
./reports/LATEST_PASS16B_MARKET_STRUCTURE_MODEL_PLAN_NOAPI.md:21:market_structure_evidence_ledger_v1
./reports/LATEST_PHASE19U_REPUTATION_MICRO_LOG_LIVE_WRITER_DRYRUN_POST_AUDIT_NOAPI.md:41:TEMP_DB_ROW_COUNTS={'dryrun_rejection_micro_log': 10, 'dryrun_entity_reputation_ledger': 25, 'dryrun_entity_reputation_evidence_events': 27, 'dryrun_repeat_offender_fast_kill_cache': 19, 'dryrun_external_reputation_comparison_events': 1}
./reports/LATEST_BACKBONE4_SCHEMA_APPLY_REAL_AFTER_EXPLICIT_APPROVAL.md:59:- `rug_evidence_events` — existed_before=`False` exists_after=`True` action=`created_on_live_db` rows_after=`0`
./reports/LATEST_PRIORITY_ENGINE_PLAN_NOAPI.md:69:EVIDENCE_EVENTS
./reports/LATEST_PASS16D_MARKET_STRUCTURE_SCHEMA_DRYRUN_NOAPI.md:18:market_structure_evidence_ledger_v1
./reports/LATEST_BACKBONE3B_SCHEMA_APPLY_DRYRUN_TEMP_COPY_FIX_NOAPI.md:72:- `rug_evidence_events` — existed_before=`False` exists_after=`True` action=`created_on_temp_copy`
./reports/LATEST_PHASE5I2_EVIDENCE_BACKFILL_PLAN_REPAIR_NOAPI.md:20:- `phase4_source_manifest` target=`evidence_event_ledger_v1` rows=`1`
./reports/LATEST_PHASE5I2_EVIDENCE_BACKFILL_PLAN_REPAIR_NOAPI.md:21:- `initial_holder_group_evidence` target=`initial_holder_evidence_events_v1` rows=`7`
./reports/LATEST_PHASE5I2_EVIDENCE_BACKFILL_PLAN_REPAIR_NOAPI.md:22:- `deployer_receipt_evidence` target=`deployer_receipt_evidence_events_v1` rows=`11`
./reports/LATEST_PHASE5I2_EVIDENCE_BACKFILL_PLAN_REPAIR_NOAPI.md:23:- `deployer_receipt_group_summary` target=`deployer_receipt_evidence_events_v1` rows=`7`
./reports/LATEST_PHASE19J_REPUTATION_SCHEMA_APPLY_DRYRUN_NOAPI.md:45:TARGET_TABLES=rejection_micro_log,entity_reputation_ledger,entity_reputation_evidence_events,repeat_offender_fast_kill_cache,external_reputation_comparison_events
./reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md:1:# PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI
./reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md:3:- FINAL_GATE: `PASS_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI`
./reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md:76:- `evidence_event_ledger_v1` | group=`event_backbone` | writer=`single_writer:evidence_normalizer` | exists_now=`False`
./reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md:78:- `initial_holder_evidence_events_v1` | group=`phase4_persistence` | writer=`single_writer:phase4_backfill_importer` | exists_now=`False`
./reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md:79:- `deployer_receipt_evidence_events_v1` | group=`phase4_persistence` | writer=`single_writer:phase4_receipt_importer` | exists_now=`False`
./reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md:118:- JSON: `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json`
./reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md:119:- ROWS: `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi_rows.jsonl`
./reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md:120:- WORK_DIR: `/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825`
./reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md:121:- SCHEMA_PLAN_SQL: `/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql`
./reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md:122:- PLANNED_TABLE_ROWS: `/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_planned_backbone_tables.jsonl`
./reports/LATEST_PHASE20I_CEX_DEPOSIT_BRIDGE_AND_MIXER_POLICY_PLAN_NOAPI.md:93:- `cex_bridge_evidence_type` target=`whale_entity_evidence_events_v1 or future cex bridge table` purpose=CEX ilişkisinin türünü belirtir.
./reports/PHASE_HISTORY_MASTER_AUDIT_READONLY_NOAPI.md:280:- /root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md
./reports/PHASE_HISTORY_MASTER_AUDIT_READONLY_NOAPI.md:540:- /root/tokenoskobi_clean_v1/reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md
./reports/PHASE_HISTORY_MASTER_AUDIT_READONLY_NOAPI.md:541:- /root/tokenoskobi_clean_v1/reports/LATEST_PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI.md
./reports/PHASE_HISTORY_MASTER_AUDIT_READONLY_NOAPI.md:545:- /root/tokenoskobi_clean_v1/reports/LATEST_PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI.md
./reports/PHASE_HISTORY_MASTER_AUDIT_READONLY_NOAPI.md:550:- /root/tokenoskobi_clean_v1/reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md
./reports/PHASE_HISTORY_MASTER_AUDIT_READONLY_NOAPI.md:553:- /root/tokenoskobi_clean_v1/reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md
./reports/PHASE_HISTORY_MASTER_AUDIT_READONLY_NOAPI.md:558:- /root/tokenoskobi_clean_v1/reports/LATEST_PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI.md
./reports/PHASE_HISTORY_MASTER_AUDIT_READONLY_NOAPI.md:562:- /root/tokenoskobi_clean_v1/reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md
./reports/LATEST_FW1_FORENSIC_WAREHOUSE_BACKBONE_DESIGN_NOAPI.md:89:- future_needed: `stillborn_events, early_death_events, autopsy_evidence_events`
./reports/LATEST_FW1_FORENSIC_WAREHOUSE_BACKBONE_DESIGN_NOAPI.md:106:- existing_tables: `token_revival_watch_events, token_score_snapshots, token_score_evidence_events`
./reports/LATEST_FW1_FORENSIC_WAREHOUSE_BACKBONE_DESIGN_NOAPI.md:176:- future_needed: `stillborn_events, early_death_events, autopsy_evidence_events`
./reports/LATEST_FW1_FORENSIC_WAREHOUSE_BACKBONE_DESIGN_NOAPI.md:186:- present_existing_tables: `token_revival_watch_events, token_score_snapshots, token_score_evidence_events`
./reports/LATEST_BACKBONE5_POST_SCHEMA_STATUS_AND_ROADMAP_RELOCK_NOAPI.md:61:- `rug_evidence_events` exists=`True` rows=`0` columns=`11` empty_now=`True`
./reports/LATEST_PASS17D_WALLET_CLUSTER_SCHEMA_DRYRUN_NOAPI.md:18:wallet_cluster_evidence_ledger_v1
./reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:1:# PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI
./reports/LATEST_PASS13A_EVIDENCE_DICTIONARY_PLAN_NOAPI.md:37:PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI
./reports/LATEST_MEV1_SANDWICH_SHIELD_DESIGN_NOAPI.md:42:- rug_evidence_events: exists=`True` rows=`0`
./reports/LATEST_MEV1_SANDWICH_SHIELD_DESIGN_NOAPI.md:127:- existing_tables: `rug_evidence_events, slippage_estimates`
./reports/LATEST_PASS14D_DEPLOYER_SCHEMA_DRYRUN_NOAPI.md:18:deployer_evidence_ledger_v1
./reports/LATEST_PASS18D_TECHNICAL_SIGNAL_SCHEMA_DRYRUN_NOAPI.md:18:technical_signal_evidence_ledger_v1
./reports/LATEST_LIFE1_LIFE_CORE_DESIGN_NOAPI.md:36:- token_score_evidence_events: `10`
./reports/LATEST_LIFE1_LIFE_CORE_DESIGN_NOAPI.md:107:- existing_tables: `token_lifecycle, token_status_history, token_score_snapshots, token_score_evidence_events`
./reports/LATEST_LIFE1_LIFE_CORE_DESIGN_NOAPI.md:169:- present_existing_tables: `token_lifecycle, token_status_history, token_score_snapshots, token_score_evidence_events`
./reports/LATEST_SCORE1_100_POINT_SCORING_AND_VALIDATION_POLICY_NOAPI.md:48:- `rug_evidence_events` exists=`True` rows=`0` columns=`11`
./reports/LATEST_SCORE1_100_POINT_SCORING_AND_VALIDATION_POLICY_NOAPI.md:68:- `token_score_evidence_events` exists=`True` rows=`10` columns=`13`
./reports/LATEST_PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI.md:1:# PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI
./reports/LATEST_PASS13AA_EVIDENCE_DICTIONARY_COVERAGE_REVIEW_NOAPI.md:27:PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI
./reports/LATEST_PHASE5E_SCHEMA_TEMP_DB_DRYRUN_NOAPI.md:41:- `/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql` exists=`True` sha=`d1990c7911716954bda001c22380fbd45cea715b1a9b10d4b2660fa03eded690`
./reports/LATEST_PHASE5E_SCHEMA_TEMP_DB_DRYRUN_NOAPI.md:42:- `/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql` exists=`True` sha=`d1990c7911716954bda001c22380fbd45cea715b1a9b10d4b2660fa03eded690`
./reports/LATEST_PHASE5E_SCHEMA_TEMP_DB_DRYRUN_NOAPI.md:50:- `/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232550/phase5a_future_schema_plan_noapi.sql` apply_ok=`True` error=`None`
./reports/LATEST_PHASE5E_SCHEMA_TEMP_DB_DRYRUN_NOAPI.md:51:- `/root/tokenoskobi_clean_v1/_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI/20260531_232825/phase5a_future_schema_plan_noapi.sql` apply_ok=`True` error=`None`
./reports/LATEST_PHASE5E_SCHEMA_TEMP_DB_DRYRUN_NOAPI.md:63:- `deployer_receipt_evidence_events_v1` live_before=`False` temp_before=`False` temp_after=`True` conflict=`False`
./reports/LATEST_PHASE5E_SCHEMA_TEMP_DB_DRYRUN_NOAPI.md:64:- `evidence_event_ledger_v1` live_before=`False` temp_before=`False` temp_after=`True` conflict=`False`
./reports/LATEST_PHASE5E_SCHEMA_TEMP_DB_DRYRUN_NOAPI.md:73:- `initial_holder_evidence_events_v1` live_before=`False` temp_before=`False` temp_after=`True` conflict=`False`
./reports/LATEST_PHASE28B_DATA_PROVENANCE_AND_CANONICALIZATION_CONTRACT_NOAPI.md:80:RELEVANT_EXISTING_TABLES=["ai_feature_schema_registry_v1", "asymmetric_route_guard_events_v1", "asymmetric_speculative_route_policy_v1", "autopsy_evidence_events", "backpressure_rollup_snapshot_v1", "birth_checkpoint_snapshots", "bsc_event_source_probes", "bsc_pair_created_candidates", "commercial_roi_score_inputs_v1", "commercial_scoreboard_alerts_v1", "commercial_scoreboard_metrics_v1", "commercial_scoreboard_periods_v1", "control_dashboard_view_model_events_v1__old_nullable_source_counts", "data_evidence_policy", "deployer_receipt_evidence_events_v1", "dex_microstructure_technical_evidence_events_v1", "entity_reputation_evidence_events", "event_source_safety_ledger", "evidence_event_ledger_v1", "evidence_object_store_v1", "fusion_score_events_v1", "high_risk_tiny_route_events", "holder_snapshots", "initial_holder_evidence_events_v1", "known_wallet_quarantine_seed_v1", "known_wallet_source_registry_readmodel_v1", "known_wallet_source_registry_v1", "liquidity_snapshots", "market_snapshots", "mev_route_profiles", "micro_route_size_plan_events_v1", "moonshot_source_pressure_events", "morgue_route_decisions", "narrative_token_match_events", "net_commercial_score_v1", "news_impact_events_v1", "news_narrative_time_series_v1", "news_raw_feed_events", "news_score_component_events_v1", "news_score_events_v1", "news_signal_events", "news_source_budget_ledger_v1", "news_source_dedup_policy_v1", "news_source_fetch_policy_v1", "news_source_panel_lane_policy_v1", "news_source_quality_stats_v1", "news_source_registry", "news_source_registry_v1", "news_source_reliability_events", "news_token_match_events", "news_translation_cache_v1", "news_translation_quality_events_v1", "no_pair_memory", "opportunity_outcome_snapshot_v1", "pair_birth_events", "pair_verification_events", "pairs", "paper_route_decision_events_v1", "parsed_live_observation_staging", "private_route_guard_events", "raw_discovery_events_v1", "raw_response_archive", "rejected_token_followup_queue_v1", "risk_route_decision_events", "route_performance_memory_events_v1", "route_quality_feedback_events", "rug_evidence_events", "schema_metadata", "score_calibration_events", "score_validation_events", "sell_route_guard_events", "snapshot_commit_ledger", "snapshot_strength_events", "source_conflict_events", "source_gate_decisions", "source_reliability_ledger", "stale_snapshot_blocks", "state_aggregated_token_command_output_v1", "state_aggregated_token_decision_labels_v1", "state_aggregated_token_freshness_v1"]
./reports/LATEST_PHASE20E_WHALE_ENTITY_SCHEMA_REAL_AFTER_EXPLICIT_APPROVAL.md:63:- `whale_entity_evidence_events_v1` exists=`True` rows=`0`
./reports/FILE_CLASSIFICATION_AUDIT_READONLY_NOAPI.md:29:0.35 MB | /root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json
./reports/LATEST_PHASE4_RISK_EVIDENCE_INPUT_MATRIX_PLAN_NOAPI.md:137:TABLE=autopsy_evidence_events ROWS=0 COLUMNS=['evidence_uid', 'autopsy_uid', 'evidence_type', 'evidence_status', 'evidence_value_json', 'source', 'observed_at_utc', 'created_at_utc']
./reports/LATEST_PHASE4_RISK_EVIDENCE_INPUT_MATRIX_PLAN_NOAPI.md:251:TABLE=rug_evidence_events ROWS=0 COLUMNS=['event_uid', 'token_uid', 'pair_uid', 'chain', 'evidence_type', 'evidence_source', 'evidence_hash', 'confidence', 'rug_status', 'observed_at_utc', 'created_at_utc']
./reports/LATEST_PHASE4_RISK_EVIDENCE_INPUT_MATRIX_PLAN_NOAPI.md:284:TABLE=token_score_evidence_events ROWS=10 COLUMNS=['evidence_uid', 'score_uid', 'token_uid', 'pair_uid', 'created_at_utc', 'score_family', 'component_name', 'evidence_source', 'evidence_value', 'score_delta', 'confidence_level', 'data_missing', 'no_invention_rule']
./reports/LATEST_DATA_PIPELINE_SCORE_ARCHITECTURE_PLAN_V2_EDGE_SCHEMA_FIX_NOAPI.md:103:- `normalized_evidence_events`
./reports/LATEST_PHASE5K_EVIDENCE_BACKFILL_REAL_AFTER_EXPLICIT_APPROVAL.md:29:- `deployer_receipt_evidence_events_v1` before=`0` after=`18` delta=`18` expected=`18` match=`True`
./reports/LATEST_PHASE5K_EVIDENCE_BACKFILL_REAL_AFTER_EXPLICIT_APPROVAL.md:30:- `evidence_event_ledger_v1` before=`0` after=`1` delta=`1` expected=`1` match=`True`
./reports/LATEST_PHASE5K_EVIDENCE_BACKFILL_REAL_AFTER_EXPLICIT_APPROVAL.md:31:- `initial_holder_evidence_events_v1` before=`0` after=`7` delta=`7` expected=`7` match=`True`
./reports/LATEST_PHASE20C_WHALE_ENTITY_READMODEL_BUILDER_PLAN_NOAPI.md:53:- `whale_entity_evidence_events_v1`: Evidence drawer için kanıt satırlarını sağlar. Status: `PLANNED_ONLY`
./reports/LATEST_PHASE19Q_REPUTATION_MICRO_LOG_DATA_BINDING_DRYRUN_POST_AUDIT_NOAPI.md:36:EVIDENCE_EVENT_COUNT=35
./reports/LATEST_PHASE4_TOKEN_BIRTH_BLOCK_ANCHOR_CONTRACT_CREATION_SOURCE_ARTIFACT_SANITIZE_PLAN_NOAPI.md:58:AUTOPSY_EVIDENCE_EVENTS=0
./reports/LATEST_PHASE4_TOKEN_BIRTH_BLOCK_ANCHOR_CONTRACT_CREATION_SOURCE_ARTIFACT_SANITIZE_PLAN_NOAPI.md:177:RUG_EVIDENCE_EVENTS=0
./reports/LATEST_PHASE4_TOKEN_BIRTH_BLOCK_ANCHOR_CONTRACT_CREATION_SOURCE_ARTIFACT_SANITIZE_PLAN_NOAPI.md:210:TOKEN_SCORE_EVIDENCE_EVENTS=10
./reports/LATEST_MOON1_MOONSHOT_CORE_DESIGN_NOAPI.md:40:- token_score_evidence_events: exists=`True` rows=`10`
./reports/LATEST_MOON1_MOONSHOT_CORE_DESIGN_NOAPI.md:47:- existing_tables: `token_score_snapshots, token_score_evidence_events, life_signal_events, source_gate_decisions`
./reports/LATEST_MOON1_MOONSHOT_CORE_DESIGN_NOAPI.md:56:- existing_tables: `token_score_snapshots, token_score_evidence_events, token_archive_evidence, negative_memory`
./reports/LATEST_MOON1_MOONSHOT_CORE_DESIGN_NOAPI.md:121:- present_existing_tables: `token_score_snapshots, token_score_evidence_events, life_signal_events, source_gate_decisions`
./reports/LATEST_MOON1_MOONSHOT_CORE_DESIGN_NOAPI.md:127:- present_existing_tables: `token_score_snapshots, token_score_evidence_events, token_archive_evidence, negative_memory`
./reports/LATEST_PHASE5M_PHASE5_FINAL_REVIEW_NOAPI.md:20:- `5A` pass=`True` gate=`PASS_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI`
./reports/LATEST_PHASE20F_WHALE_ENTITY_SCHEMA_POST_AUDIT_NOAPI.md:47:- `whale_entity_evidence_events_v1` exists=`True` rows=`0`
./reports/LATEST_PHASE19R_REPUTATION_MICRO_LOG_DATA_BINDING_ACCEPTANCE_NOAPI.md:38:EVIDENCE_EVENT_COUNT=35
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:15:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` exists=`True` sha=`372798f9d521650bd3ca438c791f27b869b0cd37654e2ef82f68edbdfa2d74e1` size=`365311`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:16:- `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md` exists=`True` sha=`a5df426ffa5061741e7c063a24e32d9fab2ff0067d2f06739b1f8baa31de9714` size=`5145`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:47:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `base_counts.deployer_wallet_events` = `0`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:48:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `existing_tables.8.columns.4.name` = `confirmed_cause`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:49:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `existing_tables.30.columns.4.name` = `deployer_address`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:50:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `existing_tables.30.table` = `deployer_wallet_events`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:51:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `existing_tables.78.columns.6.name` = `deployer_address`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:52:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `existing_tables.87.columns.8.name` = `confirmed_label_count`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:53:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `existing_tables.161.columns.3.name` = `deployer_address`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:54:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `expected.confirmed_token_creation_receipt_match` = `2`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:55:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `expected.deployer_receipt_group_count` = `7`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:56:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `expected.receipt_found` = `11`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:57:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `expected.receipt_rows` = `11`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:58:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `expected.token_log_match` = `11`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:59:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `expected.unproven_zero_mint_receipt` = `9`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:60:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `failed_phase4_checks.0` = `confirmed_token_creation_receipt_match_2`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:61:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `phase4_hard_checks.confirmed_token_creation_receipt_match_2` = `False`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:62:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `phase4_hard_checks.deployer_receipt_group_count_7` = `True`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:63:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `phase4_hard_checks.receipt_found_11` = `True`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:64:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `phase4_hard_checks.receipt_rows_11` = `True`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:65:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `phase4_hard_checks.token_log_match_11` = `True`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:66:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `phase4_hard_checks.unproven_zero_mint_receipt_9` = `True`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:67:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `planned_table_exists_map.deployer_receipt_evidence_events_v1` = `False`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:68:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `planned_tables.2.fields.6` = `transfer_mint_summary_json TEXT NOT NULL`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:69:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `planned_tables.2.purpose` = `Phase 4 initial-holder transfer/mint evidence persistence without risk clearance.`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:70:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `planned_tables.3.fields.4` = `receipt_found INTEGER NOT NULL`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:71:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `planned_tables.3.fields.5` = `token_log_match INTEGER NOT NULL`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:72:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `planned_tables.3.fields.6` = `creation_proof INTEGER NOT NULL`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:73:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `planned_tables.3.fields.7` = `zero_mint_unproven INTEGER NOT NULL`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:74:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `planned_tables.3.purpose` = `Creation proof and zero-mint WAIT_MORE_DATA receipt separation.`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:75:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `planned_tables.3.table` = `deployer_receipt_evidence_events_v1`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:76:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` :: `planned_tables.3.writer` = `single_writer:phase4_receipt_importer`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:150:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L4:     "deployer_wallet_events": 0,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:151:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L764:           "name": "confirmed_cause",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:152:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L2824:           "name": "deployer_address",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:153:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L2871:       "table": "deployer_wallet_events"
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:154:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L7344:           "name": "deployer_address",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:155:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L8270:           "name": "confirmed_label_count",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:156:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L15194:           "name": "deployer_address",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:157:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16432:     "confirmed_token_creation_receipt_match": 2,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:158:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16434:     "deployer_receipt_group_count": 7,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:159:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16443:     "receipt_found": 11,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:160:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16444:     "receipt_rows": 11,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:161:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16445:     "token_log_match": 11,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:162:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16446:     "unproven_zero_mint_receipt": 9
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:163:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16452:     "confirmed_token_creation_receipt_match_2"
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:164:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16495:     "confirmed_token_creation_receipt_match_2": false,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:165:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16496:     "deployer_receipt_group_count_7": true,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:166:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16507:     "receipt_found_11": true,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:167:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16508:     "receipt_rows_11": true,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:168:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16509:     "token_log_match_11": true,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:169:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16510:     "unproven_zero_mint_receipt_9": true
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:170:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16521:     "deployer_receipt_evidence_events_v1": false,
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:171:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16584:         "transfer_mint_summary_json TEXT NOT NULL",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:172:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16590:       "purpose": "Phase 4 initial-holder transfer/mint evidence persistence without risk clearance.",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:173:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16601:         "receipt_found INTEGER NOT NULL",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:174:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16602:         "token_log_match INTEGER NOT NULL",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:175:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16603:         "creation_proof INTEGER NOT NULL",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:176:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16604:         "zero_mint_unproven INTEGER NOT NULL",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:177:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16611:       "purpose": "Creation proof and zero-mint WAIT_MORE_DATA receipt separation.",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:178:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16612:       "table": "deployer_receipt_evidence_events_v1",
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:179:- `/root/tokenoskobi_clean_v1/data/phase5a_evidence_event_backbone_and_execution_safety_plan_noapi.json` L16613:       "writer": "single_writer:phase4_receipt_importer"
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:180:- `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md` L24: - confirmed_token_creation_receipt_match_2: `False`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:181:- `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md` L25: - deployer_receipt_group_count_7: `True`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:182:- `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md` L36: - receipt_found_11: `True`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:183:- `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md` L37: - receipt_rows_11: `True`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:184:- `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md` L38: - token_log_match_11: `True`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:185:- `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md` L39: - unproven_zero_mint_receipt_9: `True`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:186:- `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md` L53: - deployer_wallet_events: `0`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:187:- `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md` L79: - `deployer_receipt_evidence_events_v1` | group=`phase4_persistence` | writer=`single_writer:phase4_receipt_importer` | exists_now=`False`
./reports/LATEST_PHASE5A_RECEIPT_CREATION_PROOF_FIELD_DIAGNOSE_NOAPI.md:188:- `/root/tokenoskobi_clean_v1/reports/LATEST_PHASE5A_EVIDENCE_EVENT_BACKBONE_AND_EXECUTION_SAFETY_PLAN_NOAPI.md` L110: - `confirmed_token_creation_receipt_match_2`
./reports/LATEST_SCORE2_SCORING_ENGINE_DRYRUN_NOAPI.md:78:- `rug_evidence_events` rows=`0`
./reports/LATEST_PHASE22P4C_GENERIC_PAPER_PLAN_SCHEMA_GAP_PLAN_NOAPI.md:88:- matched_anywhere: `autopsy_cases:token_uid,pair_uid; confirmation_events:token_uid,token_address,pair_uid,pair_address; liquidity_snapshots:token_uid,pair_uid,pair_address; live_data_quality_events:token_uid,pair_uid; live_fetch_ledger:token_uid,token_address,pair_uid,pair_address; live_refresh_queue:token_uid,pair_uid; market_snapshots:token_uid,pair_uid,pair_address; mev_sandwich_risk_events:token_uid,pair_uid; morgue_entries:token_uid,token_address,pair_uid,pair_address; negative_memory:token_address,pair_address; news_signal_events:token_uid; pairs:token_uid,pair_uid,pair_address; paper_decision_reports:token_uid,pair_uid; paper_trade_plans:token_uid,token_address,pair_uid,pair_address; paper_trade_positions:token_uid,pair_uid; parsed_live_observation_staging:token_uid,token_address,pair_uid,pair_address; radar_alerts:token_uid,pair_uid; raw_response_archive:token_uid,pair_uid; risk_to_morgue_transitions:token_uid,pair_uid; slippage_estimates:token_uid,pair_uid; snapshot_commit_ledger:token_uid,pair_uid; token_archive_evidence:token_uid,pair_uid; token_birth_events:token_uid,token_address,pair_uid,pair_address; token_death_events:token_uid,pair_uid; token_lifecycle:token_uid,token_address,pair_uid,pair_address; token_lifecycle_events:token_uid,pair_uid; token_radar_scores:token_uid,pair_uid; token_revival_watch_events:token_uid,pair_uid; token_risk_events:token_uid,pair_uid; token_score_evidence_events:token_uid,pair_uid; token_score_snapshots:token_uid,pair_uid; token_status_history:token_uid,pair_uid; tokens:token_uid,token_address; whale_wallet_events:token_address,pair_address`
./reports/LATEST_PHASE22P4C_GENERIC_PAPER_PLAN_SCHEMA_GAP_PLAN_NOAPI.md:205:- matched_anywhere: `autopsy_evidence_events:observed_at_utc; liquidity_snapshots:snapshot_uid,observed_at_utc,freshness_status; market_snapshots:snapshot_uid,observed_at_utc,freshness_status; news_signal_events:observed_at_utc; parsed_live_observation_staging:observed_at_utc; snapshot_commit_ledger:market_snapshot_uid; token_archive_evidence:snapshot_uid; whale_wallet_events:observed_at_utc`
./reports/LATEST_PHASE19O_REPUTATION_MICRO_LOG_DATA_BINDING_PLAN_NOAPI.md:43:TARGET_TABLES=rejection_micro_log,entity_reputation_ledger,entity_reputation_evidence_events,repeat_offender_fast_kill_cache,external_reputation_comparison_events
./reports/LATEST_PHASE19O_REPUTATION_MICRO_LOG_DATA_BINDING_PLAN_NOAPI.md:93:EVIDENCE_BINDING_JSON=/root/tokenoskobi_clean_v1/_PHASE19O_REPUTATION_MICRO_LOG_DATA_BINDING_PLAN_NOAPI/20260604_163649/phase19o_evidence_events_binding_plan_v1.json
./reports/LATEST_PHASE19L_REPUTATION_SCHEMA_APPLY_REAL_AFTER_EXPLICIT_APPROVAL.md:47:TARGET_TABLES=rejection_micro_log,entity_reputation_ledger,entity_reputation_evidence_events,repeat_offender_fast_kill_cache,external_reputation_comparison_events
./reports/LATEST_PHASE19L_REPUTATION_SCHEMA_APPLY_REAL_AFTER_EXPLICIT_APPROVAL.md:51:POST_ROW_COUNTS={'rejection_micro_log': 0, 'entity_reputation_ledger': 0, 'entity_reputation_evidence_events': 0, 'repeat_offender_fast_kill_cache': 0, 'external_reputation_comparison_events': 0}
./reports/LATEST_PHASE19G_REJECTION_MICRO_LOG_AND_INTERNAL_REPUTATION_LEDGER_DRYRUN_POST_AUDIT_NOAPI.md:44:EVIDENCE_EVENT_COUNT=47
./reports/LATEST_RISK1_DYNAMIC_POSITION_SIZING_DESIGN_NOAPI.md:41:- rug_evidence_events: exists=`True` rows=`0`
./reports/LATEST_RISK1_DYNAMIC_POSITION_SIZING_DESIGN_NOAPI.md:125:- existing_tables: `rug_evidence_events, slippage_estimates`
./reports/LATEST_PHASE19I_REPUTATION_SCHEMA_APPLY_PLAN_NOAPI.md:44:TARGET_TABLES=rejection_micro_log,entity_reputation_ledger,entity_reputation_evidence_events,repeat_offender_fast_kill_cache,external_reputation_comparison_events
./reports/LATEST_PHASE19K_REPUTATION_SCHEMA_APPLY_DRYRUN_POST_AUDIT_NOAPI.md:46:TARGET_TABLES=rejection_micro_log,entity_reputation_ledger,entity_reputation_evidence_events,repeat_offender_fast_kill_cache,external_reputation_comparison_events
./reports/LATEST_PHASE19T_REPUTATION_MICRO_LOG_LIVE_WRITER_DRYRUN_NOAPI.md:43:TEMP_DB_ROW_COUNTS={'dryrun_rejection_micro_log': 10, 'dryrun_entity_reputation_ledger': 25, 'dryrun_entity_reputation_evidence_events': 27, 'dryrun_repeat_offender_fast_kill_cache': 19, 'dryrun_external_reputation_comparison_events': 1}
./reports/LATEST_BACKBONE1B_GENERIC_EVIDENCE_SCHEMA_DRYRUN_FIX_NOAPI.md:48:- `autopsy_evidence_events` rows=`1`
./reports/LATEST_BACKBONE1B_GENERIC_EVIDENCE_SCHEMA_DRYRUN_FIX_NOAPI.md:66:- `rug_evidence_events` rows=`0`
./reports/LATEST_WHALE1_WALLET_MOVEMENT_CORE_DESIGN_NOAPI.md:39:- rug_evidence_events: exists=`True` rows=`0`
./reports/LATEST_WHALE1_WALLET_MOVEMENT_CORE_DESIGN_NOAPI.md:59:- existing_tables: `tokens, pairs, negative_memory, token_score_evidence_events`
./reports/LATEST_WHALE1_WALLET_MOVEMENT_CORE_DESIGN_NOAPI.md:68:- existing_tables: `liquidity_snapshots, rug_evidence_events, morgue_route_decisions`
./reports/LATEST_WHALE1_WALLET_MOVEMENT_CORE_DESIGN_NOAPI.md:104:- existing_tables: `negative_memory, source_conflict_events, rug_evidence_events`
./reports/LATEST_WHALE1_WALLET_MOVEMENT_CORE_DESIGN_NOAPI.md:148:- present_existing_tables: `tokens, pairs, negative_memory, token_score_evidence_events`
./reports/LATEST_WHALE1_WALLET_MOVEMENT_CORE_DESIGN_NOAPI.md:154:- present_existing_tables: `liquidity_snapshots, rug_evidence_events, morgue_route_decisions`
./reports/LATEST_WHALE1_WALLET_MOVEMENT_CORE_DESIGN_NOAPI.md:178:- present_existing_tables: `negative_memory, source_conflict_events, rug_evidence_events`
./reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:1:# PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI
./reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:11:PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI
./reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:15:/tmp/pass13d_evidence_dictionary_apply_dryrun_20260611_183434.sqlite
./reports/LATEST_PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI.md:26:PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI
./reports/LATEST_PASS15C_CONTRACT_DNA_SCHEMA_PLAN_NOAPI.md:14:contract_dna_evidence_ledger_v1
./reports/LATEST_PHASE19M_REPUTATION_SCHEMA_APPLY_REAL_POST_AUDIT_NOAPI.md:41:TARGET_TABLES=rejection_micro_log,entity_reputation_ledger,entity_reputation_evidence_events,repeat_offender_fast_kill_cache,external_reputation_comparison_events
./reports/LATEST_PHASE19M_REPUTATION_SCHEMA_APPLY_REAL_POST_AUDIT_NOAPI.md:45:LIVE_ROW_COUNTS={rejection_micro_log: 0, entity_reputation_ledger: 0, entity_reputation_evidence_events: 0, repeat_offender_fast_kill_cache: 0, external_reputation_comparison_events: 0}}
./reports/LATEST_PASS14C_DEPLOYER_EVIDENCE_SCHEMA_PLAN_NOAPI.md:14:deployer_evidence_ledger_v1
./reports/LATEST_PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI.md:1:# PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI
./reports/LATEST_PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI.md:27:PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI
./reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:1:# PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI
./reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:11:PASS13E_EVIDENCE_DICTIONARY_POST_AUDIT_NOAPI
./reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:31:- evidence_dictionary_v1
./reports/LATEST_PASS13F_EVIDENCE_DICTIONARY_REAL_APPLY_PLAN_NOAPI.md:38:PASS13G_EVIDENCE_DICTIONARY_REAL_APPLY_APPROVAL_GATE_NOAPI
./reports/LATEST_PHASE5I_EVIDENCE_BACKFILL_PLAN_NOAPI.md:23:- `initial_holder_group_evidence` target=`initial_holder_evidence_events_v1` planned_rows=`7` write_now=`False`
./reports/LATEST_PHASE5I_EVIDENCE_BACKFILL_PLAN_NOAPI.md:24:- `deployer_receipt_evidence` target=`deployer_receipt_evidence_events_v1` planned_rows=`11` write_now=`False`
./reports/LATEST_PHASE5I_EVIDENCE_BACKFILL_PLAN_NOAPI.md:25:- `deployer_receipt_group_summary` target=`deployer_receipt_evidence_events_v1` planned_rows=`7` write_now=`False`
./reports/LATEST_DEATH1_DEATH_CORE_DESIGN_NOAPI.md:80:- future_needed: `rug_evidence_events, lp_removal_events, deployer_dump_events`
./reports/LATEST_DEATH1_DEATH_CORE_DESIGN_NOAPI.md:89:- future_needed: `sellability_events, honeypot_evidence_events, exit_failure_events`
./reports/LATEST_DEATH1_DEATH_CORE_DESIGN_NOAPI.md:107:- future_needed: `autopsy_evidence_events, autopsy_reason_labels`
./reports/LATEST_DEATH1_DEATH_CORE_DESIGN_NOAPI.md:152:- future_needed: `rug_evidence_events, lp_removal_events, deployer_dump_events`
./reports/LATEST_DEATH1_DEATH_CORE_DESIGN_NOAPI.md:158:- future_needed: `sellability_events, honeypot_evidence_events, exit_failure_events`
./reports/LATEST_DEATH1_DEATH_CORE_DESIGN_NOAPI.md:170:- future_needed: `autopsy_evidence_events, autopsy_reason_labels`
./reports/LATEST_DEATH1_DEATH_CORE_DESIGN_NOAPI.md:229:### `rug_evidence_events`
./reports/LATEST_DEATH1_DEATH_CORE_DESIGN_NOAPI.md:239:### `autopsy_evidence_events`
./reports/LATEST_PHASE20B_WHALE_ENTITY_DATA_CONTRACT_AND_SCHEMA_DRYRUN_NOAPI.md:43:- `whale_entity_evidence_events_v1`: `True`, rows=`0`
./reports/LATEST_PHASE20B_WHALE_ENTITY_DATA_CONTRACT_AND_SCHEMA_DRYRUN_NOAPI.md:61:- `whale_entity_evidence_events_v1`: Her label/risk/entity ilişkisinin kanıt satırlarını tutar.
./reports/LATEST_PHASE5L2_EVIDENCE_BACKFILL_POST_AUDIT_REPAIR_NOAPI.md:34:- `deployer_receipt_evidence_events_v1` current=`18` delta=`18` expected_delta=`18`
./reports/LATEST_PHASE5L2_EVIDENCE_BACKFILL_POST_AUDIT_REPAIR_NOAPI.md:35:- `evidence_event_ledger_v1` current=`1` delta=`1` expected_delta=`1`
./reports/LATEST_PHASE5L2_EVIDENCE_BACKFILL_POST_AUDIT_REPAIR_NOAPI.md:36:- `initial_holder_evidence_events_v1` current=`7` delta=`7` expected_delta=`7`
./reports/LATEST_PHASE19P_REPUTATION_MICRO_LOG_DATA_BINDING_DRYRUN_NOAPI.md:46:EVIDENCE_EVENT_COUNT=35
./reports/LATEST_PHASE19P_REPUTATION_MICRO_LOG_DATA_BINDING_DRYRUN_NOAPI.md:103:EVIDENCE_ROWS_JSONL=/root/tokenoskobi_clean_v1/_PHASE19P_REPUTATION_MICRO_LOG_DATA_BINDING_DRYRUN_NOAPI/20260604_170321/phase19p_dryrun_entity_reputation_evidence_events.jsonl
./reports/LATEST_PASS15B_CONTRACT_DNA_EVIDENCE_MODEL_PLAN_NOAPI.md:27:contract_dna_evidence_ledger_v1
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:49:- `deployer_receipt_evidence_events_v1` exists_now=`False` action=`CREATE_IF_NOT_EXISTS` fields=`12`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:50:- `evidence_event_ledger_v1` exists_now=`False` action=`CREATE_IF_NOT_EXISTS` fields=`13`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:59:- `initial_holder_evidence_events_v1` exists_now=`False` action=`CREATE_IF_NOT_EXISTS` fields=`10`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:85:- `idx_deployer_receipt_evidence_events_v1_chain` table=`deployer_receipt_evidence_events_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:86:- `idx_deployer_receipt_evidence_events_v1_created_at_utc` table=`deployer_receipt_evidence_events_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:87:- `idx_deployer_receipt_evidence_events_v1_token_uid` table=`deployer_receipt_evidence_events_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:88:- `idx_evidence_event_ledger_v1_chain` table=`evidence_event_ledger_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:89:- `idx_evidence_event_ledger_v1_created_at_utc` table=`evidence_event_ledger_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:90:- `idx_evidence_event_ledger_v1_event_ts_utc` table=`evidence_event_ledger_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:91:- `idx_evidence_event_ledger_v1_pair_uid` table=`evidence_event_ledger_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:92:- `idx_evidence_event_ledger_v1_token_uid` table=`evidence_event_ledger_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:101:- `idx_initial_holder_evidence_events_v1_chain` table=`initial_holder_evidence_events_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:102:- `idx_initial_holder_evidence_events_v1_created_at_utc` table=`initial_holder_evidence_events_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:103:- `idx_initial_holder_evidence_events_v1_pair_uid` table=`initial_holder_evidence_events_v1` reason=`duplicate_index_name`
./reports/LATEST_PHASE5F_SCHEMA_APPLY_PLAN_NOAPI.md:104:- `idx_initial_holder_evidence_events_v1_token_uid` table=`initial_holder_evidence_events_v1` reason=`duplicate_index_name`
./reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:1:# PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI
./reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:11:PASS13B_EVIDENCE_DICTIONARY_DRYRUN_NOAPI
./reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:15:- evidence_dictionary_v1
./reports/LATEST_PASS13C_EVIDENCE_DICTIONARY_APPLY_PLAN_NOAPI.md:34:PASS13D_EVIDENCE_DICTIONARY_APPLY_DRYRUN_NOAPI
./reports/LATEST_PHASE5J_EVIDENCE_BACKFILL_DRYRUN_NOAPI.md:25:- `deployer_receipt_evidence_events_v1` before=`0` after=`18` delta=`18` expected=`18` match=`True`
./reports/LATEST_PHASE5J_EVIDENCE_BACKFILL_DRYRUN_NOAPI.md:26:- `evidence_event_ledger_v1` before=`0` after=`1` delta=`1` expected=`1` match=`True`
./reports/LATEST_PHASE5J_EVIDENCE_BACKFILL_DRYRUN_NOAPI.md:27:- `initial_holder_evidence_events_v1` before=`0` after=`7` delta=`7` expected=`7` match=`True`
./reports/LATEST_BACKBONE2_SCHEMA_APPLY_PLAN_NOAPI.md:178:### `rug_evidence_events`
./reports/LATEST_BACKBONE2_SCHEMA_APPLY_PLAN_NOAPI.md:198:### `autopsy_evidence_events`
./reports/LATEST_BACKBONE2_SCHEMA_APPLY_PLAN_NOAPI.md:304:- tables: `stillborn_events, early_death_events, fast_decay_events, rug_evidence_events, morgue_route_decisions`
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:7:{"exists_now": true, "expected_exists": true, "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "phase6i_exists_after": true, "row_type": "post_table", "table": "dex_microstructure_technical_evidence_events_v1"}
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:38:{"exists_now": true, "expected_exists": true, "index": "idx_dex_tech_event_signal", "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "phase6i_exists_after": true, "row_type": "post_index", "target_table": "dex_microstructure_technical_evidence_events_v1"}
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:39:{"exists_now": true, "expected_exists": true, "index": "idx_dex_tech_event_status", "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "phase6i_exists_after": true, "row_type": "post_index", "target_table": "dex_microstructure_technical_evidence_events_v1"}
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:40:{"exists_now": true, "expected_exists": true, "index": "idx_dex_tech_event_token", "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "phase6i_exists_after": true, "row_type": "post_index", "target_table": "dex_microstructure_technical_evidence_events_v1"}
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:70:{"empty_now": true, "expected_empty": true, "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "row_count_now": 0, "row_type": "target_count", "table": "dex_microstructure_technical_evidence_events_v1"}
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:97:{"count_after_phase6i": 0, "count_before_phase6i": 0, "count_now": 0, "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "row_type": "core_count", "table": "autopsy_evidence_events", "unchanged_vs_before": true, "unchanged_vs_phase6i_after": true}
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:122:{"count_after_phase6i": 18, "count_before_phase6i": 18, "count_now": 18, "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "row_type": "core_count", "table": "deployer_receipt_evidence_events_v1", "unchanged_vs_before": true, "unchanged_vs_phase6i_after": true}
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:131:{"count_after_phase6i": 1, "count_before_phase6i": 1, "count_now": 1, "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "row_type": "core_count", "table": "evidence_event_ledger_v1", "unchanged_vs_before": true, "unchanged_vs_phase6i_after": true}
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:149:{"count_after_phase6i": 7, "count_before_phase6i": 7, "count_now": 7, "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "row_type": "core_count", "table": "initial_holder_evidence_events_v1", "unchanged_vs_before": true, "unchanged_vs_phase6i_after": true}
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:242:{"count_after_phase6i": 0, "count_before_phase6i": 0, "count_now": 0, "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "row_type": "core_count", "table": "rug_evidence_events", "unchanged_vs_before": true, "unchanged_vs_phase6i_after": true}
./data/phase6j_readmodel_post_audit_noapi_rows.jsonl:277:{"count_after_phase6i": 10, "count_before_phase6i": 10, "count_now": 10, "phase": "PHASE6J_READMODEL_POST_AUDIT_NOAPI", "row_type": "core_count", "table": "token_score_evidence_events", "unchanged_vs_before": true, "unchanged_vs_phase6i_after": true}
./data/phase19l_reputation_schema_apply_real_after_explicit_approval.json:71:    "entity_reputation_evidence_events": 0,
./data/phase19l_reputation_schema_apply_real_after_explicit_approval.json:102:    "entity_reputation_evidence_events",
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:60:      "rug_evidence_events": 0,
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:62:      "autopsy_evidence_events": 0,
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:82:      "autopsy_evidence_events",
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:186:      "rug_evidence_events",
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:219:      "token_score_evidence_events",
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:296:        "rug_evidence_events": 0,
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:298:        "autopsy_evidence_events": 0,
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:495:          "autopsy_evidence_events",
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:496:          "rug_evidence_events",
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:504:          "autopsy_evidence_events",
./data/ui_build3_view_model_snapshot_dryrun_noapi.json:505:          "rug_evidence_events",
./data/phase19j_reputation_schema_apply_dryrun_noapi.json:122:    "entity_reputation_evidence_events",
./data/phase20g_known_wallet_source_registry_plan_noapi.json:51:        "whale_entity_evidence_events_v1": 0,
./data/phase20g_known_wallet_source_registry_plan_noapi.json:85:        "whale_entity_evidence_events_v1": 0,
./data/phase20g_known_wallet_source_registry_plan_noapi.json:381:        "whale_entity_evidence_events_v1": 0,
./data/phase5i1_backfill_plan_failure_diagnose_noapi.json:238:        "source_evidence_events_v1",
./data/phase5i1_backfill_plan_failure_diagnose_noapi.json:239:        "evidence_event_backbone_v1"
./data/phase5i1_backfill_plan_failure_diagnose_noapi.json:249:        "initial_holder_transfer_mint_evidence_events_v1",
./data/phase5i1_backfill_plan_failure_diagnose_noapi.json:250:        "initial_holder_evidence_events_v1",
./data/phase5i1_backfill_plan_failure_diagnose_noapi.json:255:      "chosen_table": "initial_holder_evidence_events_v1",
./data/phase5i1_backfill_plan_failure_diagnose_noapi.json:273:        "deployer_receipt_evidence_events_v1",
./data/phase5i1_backfill_plan_failure_diagnose_noapi.json:274:        "deployer_wallet_evidence_events_v1",
./data/phase5i1_backfill_plan_failure_diagnose_noapi.json:279:      "chosen_table": "deployer_receipt_evidence_events_v1",
./data/phase5i1_backfill_plan_failure_diagnose_noapi_rows.jsonl:4:{"candidate_tables": ["evidence_source_events_v1", "source_evidence_events_v1", "evidence_event_backbone_v1"], "chosen_exists": false, "chosen_table": null, "columns": [], "logical_bucket": "phase4_run_manifest", "phase": "PHASE5I1_BACKFILL_PLAN_FAILURE_DIAGNOSE_NOAPI", "row_count": null, "row_type": "target_diag"}
./data/phase5i1_backfill_plan_failure_diagnose_noapi_rows.jsonl:5:{"candidate_tables": ["initial_holder_transfer_mint_evidence_events_v1", "initial_holder_evidence_events_v1", "holder_distribution_events_v1", "holder_distribution_events"], "chosen_exists": true, "chosen_table": "initial_holder_evidence_events_v1", "columns": ["event_uid", "token_uid", "pair_uid", "chain", "holder_group_key", "scan_window_json", "transfer_mint_summary_json", "risk_interpretation", "source_object_uid", "created_at_utc"], "logical_bucket": "initial_holder_groups", "phase": "PHASE5I1_BACKFILL_PLAN_FAILURE_DIAGNOSE_NOAPI", "row_count": 0, "row_type": "target_diag"}
./data/phase5i1_backfill_plan_failure_diagnose_noapi_rows.jsonl:6:{"candidate_tables": ["deployer_receipt_evidence_events_v1", "deployer_wallet_evidence_events_v1", "deployer_wallet_events_v1", "deployer_wallet_events"], "chosen_exists": true, "chosen_table": "deployer_receipt_evidence_events_v1", "columns": ["event_uid", "token_uid", "chain", "tx_hash", "receipt_found", "token_log_match", "creation_proof", "zero_mint_unproven", "interpretation_label", "source_object_uid", "payload_json", "created_at_utc"], "logical_bucket": "deployer_receipts", "phase": "PHASE5I1_BACKFILL_PLAN_FAILURE_DIAGNOSE_NOAPI", "row_count": 0, "row_type": "target_diag"}
./data/phase4_risk_evidence_input_matrix_plan_noapi.json:141:      "autopsy_evidence_events": 0,
./data/phase4_risk_evidence_input_matrix_plan_noapi.json:255:      "rug_evidence_events": 0,
./data/phase4_risk_evidence_input_matrix_plan_noapi.json:288:      "token_score_evidence_events": 10,
./data/phase4_risk_evidence_input_matrix_plan_noapi.json:423:      "autopsy_evidence_events": [

===== SYSTEMD READONLY SIGNALS =====
● run-p3024005-i15606010.service                                                            loaded    failed   failed  [systemd-run] /usr/bin/test -f /root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite
● run-p3050930-i15632935.service                                                            loaded    failed   failed  [systemd-run] /usr/bin/test -f /root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite
● run-p3051711-i15633716.service                                                            loaded    failed   failed  [systemd-run] /usr/bin/test -f /root/tokenoskobi_clean_v1/public/backpressure_readmodel_refresh_staging_v1/backpressure_readmodel_refresh_cache.json
● run-p3052164-i15634169.service                                                            loaded    failed   failed  [systemd-run] /usr/bin/test -f /root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite
  tokenoskobi-active-panel-8096.service                                                     loaded    active   running Tokenoskobi/Coinoskobi Active Panel 8096
  tokenoskobi-news-radar-refresh.service                                                    loaded    inactive dead    Tokenoskobi News Radar Refresh Runner
  tokenoskobi-phase9-observation-runtime.service                                            loaded    inactive dead    Tokenoskobi Phase9 Commercial Observation Runtime Watch-Only
  tokenoskobi-news-radar-refresh.timer                                                      loaded    inactive dead    Run Tokenoskobi News Radar Refresh every 20 minutes
  tokenoskobi-phase9-observation-runtime.timer                                              loaded    active   waiting Tokenoskobi Phase9 Commercial Observation Runtime Timer Draft

===== DECISION PLACEHOLDER =====
PASS13_RUNTIME_DISCOVERY_STATUS=UNCLASSIFIED_PENDING_REVIEW
