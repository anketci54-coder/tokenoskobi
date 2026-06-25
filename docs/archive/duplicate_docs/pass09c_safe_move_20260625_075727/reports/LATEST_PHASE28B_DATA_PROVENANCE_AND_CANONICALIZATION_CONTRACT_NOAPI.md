# PHASE28B_DATA_PROVENANCE_AND_CANONICALIZATION_CONTRACT_NOAPI

STAMP=20260608_074845
FINAL_GATE=REVIEW_PHASE28B_DATA_PROVENANCE_AND_CANONICALIZATION_CONTRACT_NOAPI
RC=1
FAILED_CHECKS=["NO_SILENT_OVERWRITE_RULE_PRESENT"]
DECISION=REVIEW_PHASE28B_BEFORE_PHASE28C

## PHASE28A DEPENDENCY
PHASE28A_PASS_AND_OPEN_28B=True
PHASE28A_FINAL_GATE=PASS_PHASE28A_CENTER_INVENTORY_GATE_CASCADE_DATA_INTEGRITY_MAP_PLAN_NOAPI
PHASE28A_DECISION=OPEN_PHASE28B_DATA_PROVENANCE_AND_CANONICALIZATION_CONTRACT_NOAPI

## CORE RULE
No canonical interpretation without provenance, versioning, confidence, and raw traceability.

## DATA PIPELINE
RAW -> STAGING -> VALIDATED -> CANONICAL -> SCORE_ROUTE_AI_MEMORY
QUARANTINE is side path from STAGING/VALIDATED when ambiguous, weak, conflicting, stale, or poisoned.

## DATA LAYERS
### RAW
PURPOSE=Immutable source capture/reference.
WRITE_POLICY_FUTURE=append_only
MUST_HAVE_FIELDS=["raw_uid", "source_name", "source_ref", "chain", "fetched_at", "observed_at", "raw_payload_ref_or_body", "raw_hash", "ingest_run_id", "fetcher_version", "source_version", "api_budget_context", "created_at"]
RULES=["RAW can be compressed or file-referenced, but raw_hash must be stable.", "RAW record is not interpretation.", "RAW retention policy must protect future reprocessing."]

### STAGING
PURPOSE=Parser/normalizer output before trust promotion.
WRITE_POLICY_FUTURE=append_versioned_interpretation
MUST_HAVE_FIELDS=["staging_uid", "raw_uid", "raw_hash", "parser_version", "schema_version", "normalization_version", "chain", "token_address", "pair_address", "parsed_at", "parse_status", "normalization_status", "confidence_level", "freshness_state", "source_minimum_ok", "field_error_count", "ambiguity_flags", "created_at"]
RULES=["STAGING may be wrong; therefore it cannot directly train AI or drive canonical truth.", "STAGING can produce MORE_DATA or QUARANTINE, not final trust by itself."]

### VALIDATED
PURPOSE=Evidence-backed interpreted data eligible for canonical consideration.
WRITE_POLICY_FUTURE=append_validation_result
MUST_HAVE_FIELDS=["validated_uid", "staging_uid", "raw_uid", "raw_hash", "parser_version", "schema_version", "validation_version", "validation_status", "evidence_ref", "source_count", "source_reliability_class", "confidence_level", "freshness_state", "false_positive_risk", "canonical_allowed", "validated_at", "created_at"]
RULES=["VALIDATED does not mean canonical by default.", "canonical_allowed=True requires versioned, traceable, confidence-backed validation.", "Weak data can remain validated as weak evidence but not canonical truth."]

### CANONICAL
PURPOSE=Compact trusted current interpretation used by route/scoring/fast path.
WRITE_POLICY_FUTURE=versioned_upsert_with_lineage_no_silent_overwrite
MUST_HAVE_FIELDS=["canonical_uid", "entity_uid", "entity_type", "chain", "token_address", "pair_address", "canonical_state", "canonical_version", "parser_version", "schema_version", "source_version", "raw_hash_ref", "evidence_ref", "confidence_level", "freshness_state", "valid_from", "valid_until", "created_at", "supersedes_canonical_uid"]
RULES=["CANONICAL must be compact and fast.", "Heavy evidence belongs to sidecar/evidence/audit table.", "If parser_version or schema_version changes, new interpretation is versioned.", "Old canonical state is superseded, not erased."]

### QUARANTINE
PURPOSE=Ambiguous, conflicting, stale, parser-failed, weak-source, or poison-risk data lifecycle.
WRITE_POLICY_FUTURE=append_or_update_review_state_only
MUST_HAVE_FIELDS=["quarantine_uid", "raw_uid", "staging_uid", "raw_hash", "parser_version", "schema_version", "quarantine_reason", "source_name", "chain", "token_address", "pair_address", "confidence_level", "freshness_state", "first_seen_at", "last_reviewed_at", "review_state", "next_review_action", "retry_after", "retention_policy", "outcome"]
RULES=["Quarantine is not a digital graveyard.", "Every quarantine item needs a next_review_action.", "Promotion requires evidence and version traceability."]

### EVIDENCE_SIDECAR
PURPOSE=Heavy provenance, validation detail, cross-source proof, and audit trace.
WRITE_POLICY_FUTURE=append_only
MUST_HAVE_FIELDS=["evidence_ref", "entity_uid", "raw_uid_list", "raw_hash_list", "source_list", "parser_version_list", "schema_version_list", "evidence_hash", "evidence_quality_class", "confidence_level", "created_at"]
RULES=["Sidecar prevents canonical bloat.", "Fast Path should not parse heavy evidence sidecar."]

## CANONICALIZATION DECISION MATRIX
- raw_valid_single_strong_source_low_risk | staging=PARSE_OK | validated=VALIDATED_WEAK_OR_MEDIUM | canonical=CANONICAL_ALLOWED_IF_REQUIRED_IDENTITY_CONFIRMED | quarantine=NO
- single_weak_source_claims_honeypot | staging=PARSE_OK | validated=RISK_EVIDENCE_WEAK | canonical=NO_HARD_VETO | quarantine=RISK_REVIEW_OR_SECOND_SOURCE_REQUIRED
- wrong_chain_suspected | staging=CHAIN_MISMATCH | validated=INVALID_FOR_ENTITY | canonical=NO | quarantine=AUTO_REJECT_OR_MANUAL_REVIEW
- token_pair_mismatch_suspected | staging=IDENTITY_AMBIGUOUS | validated=NOT_VALIDATED | canonical=NO | quarantine=MANUAL_REVIEW_REQUIRED
- parser_failed_schema_unknown | staging=PARSE_FAILED | validated=NO | canonical=NO | quarantine=AUTO_RETRY_AFTER_PARSER_UPDATE
- parser_version_changed_reprocess_old_raw | staging=NEW_VERSIONED_INTERPRETATION | validated=NEW_VALIDATION_RESULT | canonical=NEW_CANONICAL_VERSION_IF_PROMOTED | quarantine=OLD_INTERPRETATION_NOT_DELETED
- stale_critical_data | staging=STALE | validated=NOT_CURRENT | canonical=NO_CURRENT_UPDATE | quarantine=AUTO_RETRY_OR_MORE_DATA
- conflicting_sources | staging=CONFLICT | validated=CONFLICT_REVIEW | canonical=NO_UNTIL_RESOLVED | quarantine=KEEP_QUARANTINED

## FAST PATH DATA STATE
FAST_PATH_READS_ONLY=["entity_uid", "canonical_state", "confidence_level", "freshness_state", "canonical_version", "valid_until", "emergency_brake_hint", "data_minimum_state", "risk_critical_state"]
FAST_PATH_MUST_NOT_READ=["raw_payload_body", "large_evidence_sidecar", "bulk_quarantine", "long_ai_explanation", "full_news_text", "deep_whale_cluster"]
EMERGENCY_BRAKE_PRECEDENCE=Emergency Brake > Authority Gate > System Gate > Data Gate > Risk Gate > Precomputed Matrix > Route

## FUTURE TABLE PLAN
NO_LIVE_SCHEMA_APPLY_NOW=True
PLANNED_TABLES_OR_SIDECARS=["data_raw_events_v1", "data_staging_interpretations_v1", "data_validation_results_v1", "data_canonical_entities_v1", "data_quarantine_events_v1", "data_evidence_sidecar_v1", "parser_schema_versions_v1", "canonical_version_history_v1"]
IMPLEMENTATION_RULE=Future schema must be dryrun/tempdb first, then explicit approval before live DB write.

## CURRENT DB INVENTORY
DB_TABLE_COUNT=284
RELEVANT_EXISTING_TABLES=["ai_feature_schema_registry_v1", "asymmetric_route_guard_events_v1", "asymmetric_speculative_route_policy_v1", "autopsy_evidence_events", "backpressure_rollup_snapshot_v1", "birth_checkpoint_snapshots", "bsc_event_source_probes", "bsc_pair_created_candidates", "commercial_roi_score_inputs_v1", "commercial_scoreboard_alerts_v1", "commercial_scoreboard_metrics_v1", "commercial_scoreboard_periods_v1", "control_dashboard_view_model_events_v1__old_nullable_source_counts", "data_evidence_policy", "deployer_receipt_evidence_events_v1", "dex_microstructure_technical_evidence_events_v1", "entity_reputation_evidence_events", "event_source_safety_ledger", "evidence_event_ledger_v1", "evidence_object_store_v1", "fusion_score_events_v1", "high_risk_tiny_route_events", "holder_snapshots", "initial_holder_evidence_events_v1", "known_wallet_quarantine_seed_v1", "known_wallet_source_registry_readmodel_v1", "known_wallet_source_registry_v1", "liquidity_snapshots", "market_snapshots", "mev_route_profiles", "micro_route_size_plan_events_v1", "moonshot_source_pressure_events", "morgue_route_decisions", "narrative_token_match_events", "net_commercial_score_v1", "news_impact_events_v1", "news_narrative_time_series_v1", "news_raw_feed_events", "news_score_component_events_v1", "news_score_events_v1", "news_signal_events", "news_source_budget_ledger_v1", "news_source_dedup_policy_v1", "news_source_fetch_policy_v1", "news_source_panel_lane_policy_v1", "news_source_quality_stats_v1", "news_source_registry", "news_source_registry_v1", "news_source_reliability_events", "news_token_match_events", "news_translation_cache_v1", "news_translation_quality_events_v1", "no_pair_memory", "opportunity_outcome_snapshot_v1", "pair_birth_events", "pair_verification_events", "pairs", "paper_route_decision_events_v1", "parsed_live_observation_staging", "private_route_guard_events", "raw_discovery_events_v1", "raw_response_archive", "rejected_token_followup_queue_v1", "risk_route_decision_events", "route_performance_memory_events_v1", "route_quality_feedback_events", "rug_evidence_events", "schema_metadata", "score_calibration_events", "score_validation_events", "sell_route_guard_events", "snapshot_commit_ledger", "snapshot_strength_events", "source_conflict_events", "source_gate_decisions", "source_reliability_ledger", "stale_snapshot_blocks", "state_aggregated_token_command_output_v1", "state_aggregated_token_decision_labels_v1", "state_aggregated_token_freshness_v1"]

## SYSTEM STATE
SERVICE_RESULT=success
SERVICE_EXEC_MAIN_STATUS=0
SERVICE_NEED_DAEMON_RELOAD=no
TIMER_ACTIVE=active
TIMER_ENABLED=enabled
TIMER_NEED_DAEMON_RELOAD=no
TIMER_DIRECT_ONBOOT_60S=True
TIMER_DIRECT_ONUNITACTIVE_15S=True
DB_INTEGRITY_OK=True
DB_QUICK_CHECK_OK=True
DB_FOREIGN_KEY_0=True
PAPER_RUNTIME_ZERO=True

## CONTRACT CHECKS
CONTRACT_REQUIRED_LAYERS_PRESENT=True
RAW_CONTRACT_OK=True
STAGING_CONTRACT_OK=True
VALIDATED_CONTRACT_OK=True
CANONICAL_CONTRACT_OK=True
QUARANTINE_CONTRACT_OK=True
EVIDENCE_SIDECAR_CONTRACT_OK=True
CANONICALIZATION_MATRIX_CASES_OK=True
FAST_PATH_COMPACT_OK=True
PARSER_VERSION_REQUIRED=True
SCHEMA_VERSION_REQUIRED=True
RAW_HASH_REQUIRED=True
NO_SILENT_OVERWRITE_RULE_PRESENT=False
QUARANTINE_LIFECYCLE_NOT_TRASH=True

## IMMUTABILITY
DB_UNCHANGED=True
ACTIVE_INDEX_UNCHANGED=True
RUNNER_UNCHANGED=True
SERVICE_UNIT_UNCHANGED=True
TIMER_UNIT_UNCHANGED=True
NO_FORBIDDEN_ACTIONS=True

## SAFETY
NOAPI=True
PLAN_ONLY=True
PROVENANCE_CONTRACT_ONLY=True
NO_LIVE_SCHEMA_APPLY=True
NO_TEMP_DB_SCHEMA_APPLY=True
NO_PATCH=True
SERVICE_START=False
SERVICE_RESTART=False
SERVICE_STOP=False
SERVICE_RESET_FAILED=False
TIMER_ENABLE=False
TIMER_START=False
TIMER_STOP=False
DAEMON_RELOAD=False
RUNNER_EXECUTE=False
PROJECTED_RUNNER_EXECUTE=False
SYSTEMD_RUN=False
DB_WRITE=False
ACTIVE_PANEL_WRITE=False
SERVICE_WRITE=False
TIMER_WRITE=False
RUNNER_WRITE=False
CANONICAL_WRITE=False
QUARANTINE_WRITE=False
STAGING_WRITE=False
RAW_WRITE=False
EXTERNAL_NETWORK_CALLS=0
API_CALLS=0
PAPER_TRADE=False
LIVE_TRADE=False
WALLET_CONNECTION=False
TRANSACTION_SIGNING=False
AUTO_PILOT=False
POLICY_APPLY=False
HARDBLOCK_WEAKENING=False
AI_POLICY_EDIT=False
AI_SCORE_UPGRADE=False
PROTECTHOME_RELAX=False
BROAD_CHMOD=False
BLIND_RETRY=False
REBOOT=False
SHUTDOWN=False
LOGOUT=False
PROMPT_RETURNED_NO_LOGOUT=True

## NEXT
NEXT_PHASE=PHASE28C_HARD_GATE_AND_EMERGENCY_BRAKE_CONTRACT_NOAPI
REPORT=/root/tokenoskobi_clean_v1/reports/LATEST_PHASE28B_DATA_PROVENANCE_AND_CANONICALIZATION_CONTRACT_NOAPI.md
JSON=/root/tokenoskobi_clean_v1/data/phase28b_data_provenance_and_canonicalization_contract_noapi.json
ROWS=/root/tokenoskobi_clean_v1/data/phase28b_data_provenance_and_canonicalization_contract_noapi_rows.jsonl
PROMPT_RETURNED_NO_LOGOUT=1
