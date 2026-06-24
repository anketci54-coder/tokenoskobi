# PHASE53A_02_READMODEL_FIELD_AUTHORITY_AUDIT_NOAPI

FINAL_GATE=FAIL_PHASE53A_02_READMODEL_FIELD_AUTHORITY_AUDIT_NOAPI
DECISION=REVIEW_PHASE53A_02_READMODEL_FIELD_AUTHORITY_AUDIT_NOAPI

MODE=READMODEL_FIELD_AUTHORITY_AUDIT_NOAPI
PATCH_ALLOWED_NOW=false
REQUIRES_EXPLICIT_APPROVAL=true

DB_WRITE=false
PANEL_WRITE=false
RUNTIME_CHANGE=false
SERVICE_CHANGE=false
PROVIDER_FETCH=false
TRADE_AUTHORITY=0
WALLET_AUTHORITY=0
LIVE_TRADE=0
PAPER_TRADE=0
AUTO_APPLY=0
HARD_BLOCK_BYPASS=0

## Metrics

DB_OBJECT_COUNT=300
DB_FIELD_AUTHORITY_HIT_COUNT=378
JSON_MODEL_FILE_COUNT=732
JSON_FIELD_AUTHORITY_HIT_COUNT=9158
TOTAL_FIELD_AUTHORITY_HIT_COUNT=9536
ORPHAN_CANDIDATE_COUNT=7347
REVIEW_RENAME_CANDIDATE_COUNT=565
SAFE_CONTEXT_KEEP_COUNT=1263
FALSE_POSITIVE_IGNORE_COUNT=354

## Class Counts

| Class | Count |
|---|---:|
| ORPHAN_CANDIDATE | 7347 |
| REVIEW_RENAME_CANDIDATE | 565 |
| SAFE_CONTEXT_KEEP | 1263 |
| FALSE_POSITIVE_IGNORE | 354 |
| SCAN_ERROR | 7 |

## Top Source Surfaces

| Source | Hits |
|---|---:|
| `data/tokenoskobi_clean_v1.sqlite` | 378 |
| `data/archive/phases/phase21/phase21a_known_wallet_source_registry_readmodel_plan_noapi.json` | 355 |
| `data/panel_route_map_v1.json` | 254 |
| `data/panel_route_map_candidate_plan_noapi.json` | 254 |
| `data/panel_route_map_routes_plan_noapi.jsonl` | 231 |
| `data/panel_style_aware_visual_review_layout_fix_plan_noapi.json` | 165 |
| `data/panel_style_aware_visual_review_layout_fix_plan_rows_noapi.jsonl` | 164 |
| `data/phase7e_decision_binding_dryrun_noapi_rows.jsonl` | 157 |
| `data/panel_bound_icon_visual_fit_fix_plan_rows_noapi.jsonl` | 154 |
| `data/icon_panel_asset_export_384_128_plan_rows_noapi.jsonl` | 154 |
| `data/phase7f_command_output_dryrun_noapi_rows.jsonl` | 144 |
| `data/phase6h_readmodel_apply_plan_noapi_rows.jsonl` | 135 |
| `data/phase7c_readmodel_seed_real_after_explicit_approval_rows.jsonl` | 134 |
| `data/icon_panel_asset_normalize_plan_rows_noapi.jsonl` | 130 |
| `data/phase7a_readmodel_seed_temp_dryrun_noapi_rows.jsonl` | 116 |
| `data/panel_bound_icon_visual_fit_fix_plan_noapi.json` | 88 |
| `data/phase6h_readmodel_apply_plan_noapi.json` | 83 |
| `data/phase7b_readmodel_seed_apply_plan_noapi_rows.jsonl` | 82 |
| `data/phase4_deep_risk_code_shape_quality_review_noapi_rows.jsonl` | 76 |
| `data/phase7d_readmodel_seed_post_audit_noapi_rows.jsonl` | 75 |

## Top Field Names

| Field | Hits |
|---|---:|
| `action_plan` | 284 |
| `action` | 279 |
| `trade_execution_allowed` | 261 |
| `db_mutation_allowed` | 237 |
| `api_fetch_allowed` | 237 |
| `live_trade` | 228 |
| `planned_action` | 220 |
| `order` | 195 |
| `permission_status` | 188 |
| `paper_live_allowed` | 159 |
| `planned_layout_action` | 154 |
| `planned_icon_action` | 154 |
| `paper_allowed` | 153 |
| `active_8096_allowed` | 151 |
| `paper_trade` | 132 |
| `apply_plan_action` | 126 |
| `apply_order` | 126 |
| `trade_permission` | 124 |
| `live_allowed` | 110 |
| `payload_json` | 76 |
| `paper_executions` | 76 |
| `TRADE_PERMISSION` | 69 |
| `paper_trade_execution` | 68 |
| `PAPER_TRADE_NOW` | 68 |
| `LIVE_TRADE_NOW` | 68 |
| `buy_enabled` | 64 |
| `statement_order` | 63 |
| `live_execution` | 61 |
| `execution_allowed` | 60 |
| `max_safe_buy_usd` | 58 |

## Field Authority Audit Log

Every ORPHAN_CANDIDATE and REVIEW_RENAME_CANDIDATE is locked as PATCH_ALLOWED_NOW=false.

| Audit ID | Source Type | Source | Field Path | Classification | Gap Class | Severity | Patch Allowed Now | Requires Approval |
|---|---|---|---|---|---|---|---|---|
| PH53A02-RM-0001 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `ai_feature_schema_registry_v1.allowed_targets_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0002 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `ai_model_artifact_registry_v1.production_allowed` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0003 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `api_budget_spend_ledger.allowed_before_call` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0004 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `api_budget_spend_ledger.approval_marker` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0005 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_birth_checkpoint_snapshots_20260616.buy_window_count` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0006 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_birth_checkpoint_snapshots_20260616.sell_window_count` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0007 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_birth_minute_candles_20260616.buy_count` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0008 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_birth_minute_candles_20260616.sell_count` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0009 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_birth_momentum_window_metrics_20260616.buy_count` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0010 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_birth_momentum_window_metrics_20260616.sell_count` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0011 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_birth_momentum_window_metrics_20260616.buy_sell_ratio` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0012 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_birth_momentum_window_metrics_20260616.net_buy_pressure` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0013 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_commercial_policy_review_events_v1_20260616.trade_permission_granted` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0014 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_commercial_scoreboard_alerts_v1_20260616.trade_permission` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0015 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_entity_reputation_evidence_events_20260616.reputation_action` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0016 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_entity_reputation_ledger_20260616.confirmed_severe_count` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0017 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_preflight_audit_events_v1_20260616` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0018 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_preflight_audit_events_v1_20260616.paper_allowed` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0019 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_preflight_audit_events_v1_20260616.live_allowed` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0020 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_rpc_budget_guard_events_v1_20260616` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0021 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v1_20260616` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0022 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v1_20260616.buy_price_impact_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0023 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v1_20260616.sell_price_impact_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0025 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v1_20260616.tax_buy_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0026 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v1_20260616.tax_sell_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0027 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v1_20260616.execution_permission` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0028 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0029 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v2_20260616` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0031 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v2_20260616.buy_price_impact_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0032 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v2_20260616.sell_price_impact_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0033 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v2_20260616.tax_buy_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0034 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v2_20260616.tax_sell_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0035 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v2_20260616.execution_permission` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0036 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_gate_events_v2_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0037 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_policy_v1_20260616` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0038 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_policy_v1_20260616.max_buy_impact_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0039 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_policy_v1_20260616.max_sell_impact_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0040 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_policy_v1_20260616.max_buy_tax_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0041 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_policy_v1_20260616.max_sell_tax_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0042 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_policy_v1_20260616.live_allowed` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0043 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_policy_v1_20260616.paper_allowed` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0044 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_policy_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0045 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_time_series_v1_20260616` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0046 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_time_series_v1_20260616.buy_price_impact_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0047 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_time_series_v1_20260616.sell_price_impact_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0049 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_time_series_v1_20260616.tax_buy_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0050 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_time_series_v1_20260616.tax_sell_pct` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0051 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_safety_time_series_v1_20260616.execution_permission` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0052 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_threshold_evaluation_events_v1_20260616` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0053 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_threshold_evaluation_events_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0054 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_execution_threshold_policy_v1_20260616` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0055 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_known_wallet_registry_20260616` | REVIEW_RENAME_CANDIDATE | SEMANTIC_ACTION_LEAK | HIGH | false | true |
| PH53A02-RM-0056 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_known_wallet_registry_20260616.wallet_uid` | REVIEW_RENAME_CANDIDATE | SEMANTIC_ACTION_LEAK | HIGH | false | true |
| PH53A02-RM-0057 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_known_wallet_registry_20260616.wallet_address` | REVIEW_RENAME_CANDIDATE | SEMANTIC_ACTION_LEAK | HIGH | false | true |
| PH53A02-RM-0058 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_known_wallet_source_registry_readmodel_v1_20260616` | REVIEW_RENAME_CANDIDATE | SEMANTIC_ACTION_LEAK | HIGH | false | true |
| PH53A02-RM-0059 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_known_wallet_source_registry_readmodel_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0060 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_known_wallet_source_registry_readmodel_v1_20260616.payload_sha256` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0061 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_moonshot_wallet_bridge_events_20260616` | REVIEW_RENAME_CANDIDATE | SEMANTIC_ACTION_LEAK | HIGH | false | true |
| PH53A02-RM-0062 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_moonshot_wallet_bridge_events_20260616.wallet_event_uid` | REVIEW_RENAME_CANDIDATE | SEMANTIC_ACTION_LEAK | HIGH | false | true |
| PH53A02-RM-0063 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_news_score_events_v1_20260616.trade_signal` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0064 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_news_score_events_v1_20260616.paper_signal` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0065 | db_schema_object | `data/tokenoskobi_clean_v1.sqlite` | `archive_news_signal_events_20260616` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0069 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_phase41_command_center_unified_readmodel_v1_20260616.panel_execution_authority` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0071 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_phase41_outcome_memory_event_v1_20260616.calibration_action` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0075 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_phase41_provider_paid_call_reason_ledger_v1_20260616.approved_by_user` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0077 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_risk_gate_events_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0078 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_risk_route_decision_events_20260616.paper_permission` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0079 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_risk_route_decision_events_20260616.live_permission` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0080 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_risk_tier_capital_policy_v1_20260616.capital_permission_now_usd` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0081 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_risk_tier_capital_policy_v1_20260616.future_capital_permission_usd` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0083 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_risk_tier_transition_policy_v1_20260616.permission_granted_now` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0084 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_state_aggregated_token_command_output_v1_20260616.permission_status` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0085 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_state_aggregated_token_command_output_v1_20260616.execution_status` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0086 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_state_aggregated_token_command_output_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0087 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_state_aggregated_token_decision_labels_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0088 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_state_aggregated_token_freshness_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0089 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_state_aggregated_token_missing_evidence_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0090 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_state_aggregated_token_negative_memory_summary_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0091 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_state_aggregated_token_risk_block_reasons_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-RM-0092 | db_column | `data/tokenoskobi_clean_v1.sqlite` | `archive_state_aggregated_token_source_map_v1_20260616.payload_json` | ORPHAN_CANDIDATE | FIELD_AUTHORITY_LEAK | CRITICAL | false | true |

## Allowed Consumer Field Contract

| Allowed Field |
|---|
| `risk_state` |
| `classification` |
| `evidence_ref` |
| `reason_code` |
| `review_required` |
| `display_hint` |
| `readonly_context` |
| `blocked_by_policy` |
| `observation_status` |
| `policy_state` |
| `snapshot_version` |
| `ttl_valid` |

## Forbidden Consumer Field Contract

| Forbidden Field |
|---|
| `trade_permission` |
| `wallet_permission` |
| `execute_allowed` |
| `buy_signal` |
| `sell_signal` |
| `action_payload` |
| `order_payload` |
| `auto_apply` |
| `override_allowed` |
| `route_execute` |
| `wallet_connect` |
| `approve_trade` |
| `confirm_trade` |
| `sign_payload` |
| `send_payload` |

## Protected State

DB_SHA_CHANGED=false
PANEL_SHA_CHANGED=false
PROTECTED_DIFF_EMPTY=true

AUDIT_CHECK_COUNT=57
AUDIT_FAIL_COUNT=1
REVIEW_FINDING_COUNT=4

NEXT_SAFE_STEP=REVIEW_PHASE53A_02_READMODEL_FIELD_AUTHORITY_AUDIT_NOAPI
