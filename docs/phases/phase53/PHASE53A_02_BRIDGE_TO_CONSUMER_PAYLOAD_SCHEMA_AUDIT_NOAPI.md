# PHASE53A_02_BRIDGE_TO_CONSUMER_PAYLOAD_SCHEMA_AUDIT_NOAPI

FINAL_GATE=PASS_PHASE53A_02_BRIDGE_TO_CONSUMER_PAYLOAD_SCHEMA_AUDIT_NOAPI
DECISION=BRIDGE_TO_CONSUMER_FORBIDDEN_FIELDS_FOUND_READY_FOR_PAYLOAD_MASKING_CONTRACT_PLAN

MODE=BRIDGE_TO_CONSUMER_PAYLOAD_SCHEMA_AUDIT_NOAPI
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

SCANNED_JSON_MODEL_FILE_COUNT=121
SCANNED_DB_BRIDGE_READMODEL_HIT_COUNT=9
SCAN_ERROR_COUNT=0
TOTAL_BRIDGE_CONSUMER_SCHEMA_HIT_COUNT=1192
FORBIDDEN_PAYLOAD_FIELD_COUNT=976
SEMANTIC_REVIEW_FIELD_COUNT=106
AUTHORITY_LOCK_REVIEW_COUNT=3
SAFE_PAYLOAD_OR_LOCK_FIELD_COUNT=107
MASK_REQUIRED_COUNT=1085
CRITICAL_SCHEMA_HIT_COUNT=976
HIGH_SCHEMA_HIT_COUNT=106

## Class Counts

| Class | Count |
|---|---:|
| FORBIDDEN_PAYLOAD_FIELD | 976 |
| SEMANTIC_REVIEW_FIELD | 106 |
| AUTHORITY_LOCK_KEEP | 83 |
| SAFE_PAYLOAD_FIELD | 24 |
| AUTHORITY_LOCK_REVIEW | 3 |

## Source Rank

| Source | Hits |
|---|---:|
| `data/phase7e_decision_binding_dryrun_noapi_rows.jsonl` | 138 |
| `data/phase7c_readmodel_seed_real_after_explicit_approval_rows.jsonl` | 95 |
| `data/phase6i_readmodel_real_after_explicit_approval_rows.jsonl` | 63 |
| `data/phase6g4_base_readmodel_table_sql_repair_temp_dryrun_noapi_rows.jsonl` | 63 |
| `data/phase6e_decision_binding_rule_matrix_noapi.json` | 55 |
| `data/phase20m_cex_bridge_policy_dryrun_noapi_rows.jsonl` | 48 |
| `data/phase11a_observation_runtime_status_readmodel_dryrun_noapi_rows.jsonl` | 45 |
| `data/phase24o_backpressure_policy_readmodel_active_panel_bind_dryrun_noapi_rows.jsonl` | 41 |
| `data/phase7a_readmodel_seed_temp_dryrun_noapi_rows.jsonl` | 40 |
| `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | 35 |
| `data/phase24j_backpressure_policy_readmodel_bind_dryrun_noapi_rows.jsonl` | 34 |
| `data/panel_icon_card_mask_style_visual_decision_noapi.json` | 31 |
| `data/data43b_customer_shortlist_real_binding_dryrun_review_noapi.json` | 26 |
| `active_panel_8096/current/data/risk_security_preview_data.json` | 26 |
| `data/phase24l_backpressure_policy_readmodel_bind_real_after_explicit_approval_rows.jsonl` | 22 |
| `data/phase24f2_policy_candidate_readmodel_apply_dryrun_repair_noapi_rows.jsonl` | 17 |
| `data/phase7e_decision_binding_dryrun_noapi.json` | 16 |
| `data/phase6g1_readmodel_temp_dryrun_failure_diagnose_noapi.json` | 16 |
| `data/phase6e_decision_binding_rule_matrix_noapi_rows.jsonl` | 16 |
| `data/panel_icon_binding_v1.json` | 16 |
| `active_panel_8096/current/data/system_control_status_readmodel_view.json` | 15 |
| `data/phase24p_backpressure_policy_readmodel_active_panel_bind_real_after_explicit_approval_rows.jsonl` | 14 |
| `data/phase24g_policy_candidate_readmodel_inactive_apply_real_after_explicit_approval_rows.jsonl` | 14 |
| `data/phase24f1_policy_candidate_readmodel_dryrun_exception_review_noapi_rows.jsonl` | 14 |
| `data/phase25a1_backpressure_readmodel_refresh_loop_review_scope_noapi_rows.jsonl` | 13 |

## Forbidden Payload Hit Sample

| Audit ID | Source | Field Path | Classification | Gap Class | Severity | Patch Allowed Now | Requires Approval |
|---|---|---|---|---|---|---|---|
| PH53A02-BCP-0003 | `active_panel_8096/current/data/phase41_command_center_binding_v1.json` | `phase41_command_center_binding_v1.json.authority.panel_execution_authority` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0006 | `active_panel_8096/current/data/phase41_command_center_binding_v1.json` | `phase41_command_center_binding_v1.json.status.execution_disabled` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0008 | `active_panel_8096/current/data/production_v2_control_center_data.json` | `production_v2_control_center_data.json.risk_security_integration_v1.summary.live_button_execution_locked` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0010 | `active_panel_8096/current/data/production_v2_control_center_data.json` | `production_v2_control_center_data.json.risk_security_integration_v1.summary.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0011 | `active_panel_8096/current/data/production_v2_control_center_data.json` | `production_v2_control_center_data.json.risk_security_integration_v1.summary.auto_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0012 | `active_panel_8096/current/data/production_v2_control_center_data.json` | `production_v2_control_center_data.json.risk_security_integration_v1.live_execution_locked` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0013 | `active_panel_8096/current/data/production_v2_control_center_data.json` | `production_v2_control_center_data.json.risk_security_integration_v1.paper_execution_live_write` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0014 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.summary.live_button_execution_locked` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0016 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.summary.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0017 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.summary.auto_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0018 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.cards.4.plan.live_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0019 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.cards.4.plan.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0020 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.cards.5.plan.live_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0021 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.cards.5.plan.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0022 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.cards.6.plan.live_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0023 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.cards.6.plan.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0024 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.cards.7.plan.live_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0025 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.cards.7.plan.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0026 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.risk_execution_summary` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0027 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.normal_execution_plan` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0028 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.normal_execution_plan.plan.live_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0029 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.normal_execution_plan.plan.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0030 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.vur_kac_execution_plan` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0031 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.vur_kac_execution_plan.plan.live_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0032 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.vur_kac_execution_plan.plan.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0033 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.blocked_execution_plan` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0034 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.blocked_execution_plan.plan.live_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0035 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.blocked_execution_plan.plan.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0036 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.paper_only_execution_plan` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0037 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.paper_only_execution_plan.plan.live_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0038 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.paper_only_execution_plan.plan.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0039 | `active_panel_8096/current/data/risk_security_preview_data.json` | `risk_security_preview_data.json.card_by_key.execution_outcome_memory_stub` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0040 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json._system_control_true_refresh_binding_candidate.temp_status_payload` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0041 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json._system_control_true_refresh_binding_candidate.temp_status_payload.live_allowed` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0042 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json._system_control_true_refresh_binding_candidate.temp_status_payload.paper_allowed` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0043 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json._system_control_true_refresh_binding_candidate.temp_status_payload.trade_permission` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0044 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json.allowed_real_mutation_scope` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0045 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json.forbidden_runtime_actions` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0048 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json.forbidden_runtime_actions.TRADE_PERMISSION` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0049 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json.live_allowed` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0050 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json.panel_apply_allowed` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0051 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json.panel_status_cannot_grant_permission` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0052 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json.paper_allowed` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0053 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json.pure_green_reserved_for_future_trade_allowed_state` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0054 | `active_panel_8096/current/data/system_control_status_readmodel_view.json` | `system_control_status_readmodel_view.json.trade_permission` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0061 | `data/active_8096_style_binding_apply_real_after_explicit_approval.json` | `active_8096_style_binding_apply_real_after_explicit_approval.json.safety.db_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0062 | `data/active_8096_style_binding_apply_real_after_explicit_approval.json` | `active_8096_style_binding_apply_real_after_explicit_approval.json.safety.active_panel_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0063 | `data/active_8096_style_binding_apply_real_after_explicit_approval.json` | `active_8096_style_binding_apply_real_after_explicit_approval.json.safety.dns_nginx_ssl_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0065 | `data/coinoskobi_domain_role_decision_freeze_noapi.json` | `coinoskobi_domain_role_decision_freeze_noapi.json.safety.dns_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0066 | `data/coinoskobi_domain_role_decision_freeze_noapi.json` | `coinoskobi_domain_role_decision_freeze_noapi.json.safety.nginx_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0067 | `data/coinoskobi_domain_role_decision_freeze_noapi.json` | `coinoskobi_domain_role_decision_freeze_noapi.json.safety.active_panel_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0068 | `data/coinoskobi_domain_role_decision_freeze_noapi.json` | `coinoskobi_domain_role_decision_freeze_noapi.json.safety.db_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0070 | `data/coinoskobi_domain_role_decision_freeze_noapi_rows.jsonl` | `coinoskobi_domain_role_decision_freeze_noapi_rows.jsonl.4.dns_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0071 | `data/coinoskobi_domain_role_decision_freeze_noapi_rows.jsonl` | `coinoskobi_domain_role_decision_freeze_noapi_rows.jsonl.4.nginx_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0072 | `data/coinoskobi_domain_role_decision_freeze_noapi_rows.jsonl` | `coinoskobi_domain_role_decision_freeze_noapi_rows.jsonl.4.active_panel_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0073 | `data/coinoskobi_domain_role_decision_freeze_noapi_rows.jsonl` | `coinoskobi_domain_role_decision_freeze_noapi_rows.jsonl.4.db_mutation` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0076 | `data/coinoskobi_xyz_panel_staging_binding_auth_permission_fix_real_after_explicit_approval.json` | `coinoskobi_xyz_panel_staging_binding_auth_permission_fix_real_after_explicit_approval.json.auth_file_permission_write` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0078 | `data/coinoskobi_xyz_panel_staging_binding_auth_permission_fix_real_after_explicit_approval.json` | `coinoskobi_xyz_panel_staging_binding_auth_permission_fix_real_after_explicit_approval.json.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0079 | `data/coinoskobi_xyz_panel_staging_binding_post_apply_audit_log_window_reconcile_noapi.json` | `coinoskobi_xyz_panel_staging_binding_post_apply_audit_log_window_reconcile_noapi.json.fresh_log_window.fresh_permission_denied` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0080 | `data/coinoskobi_xyz_panel_staging_binding_post_apply_audit_log_window_reconcile_noapi.json` | `coinoskobi_xyz_panel_staging_binding_post_apply_audit_log_window_reconcile_noapi.json.post_checks.no_fresh_permission_denied` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0082 | `data/coinoskobi_xyz_panel_staging_binding_post_apply_audit_log_window_reconcile_noapi.json` | `coinoskobi_xyz_panel_staging_binding_post_apply_audit_log_window_reconcile_noapi.json.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0083 | `data/coinoskobi_xyz_panel_staging_binding_post_apply_audit_noapi.json` | `coinoskobi_xyz_panel_staging_binding_post_apply_audit_noapi.json.post_checks.no_recent_permission_denied` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0084 | `data/coinoskobi_xyz_panel_staging_binding_post_apply_audit_noapi.json` | `coinoskobi_xyz_panel_staging_binding_post_apply_audit_noapi.json.recent_permission_denied` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0086 | `data/coinoskobi_xyz_panel_staging_binding_post_apply_audit_noapi.json` | `coinoskobi_xyz_panel_staging_binding_post_apply_audit_noapi.json.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0089 | `data/coinoskobi_xyz_panel_staging_binding_real_after_explicit_approval.json` | `coinoskobi_xyz_panel_staging_binding_real_after_explicit_approval.json.paper_trade_execution` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0090 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.action` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0091 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.decision.active_panel_apply_allowed_now` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0092 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.decision.public_copy_to_active_panel_allowed_now` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0093 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.decision.db_write_allowed_now` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0094 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.decision.api_fetch_allowed_now` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0095 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.decision.paper_live_allowed_now` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0096 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.db_before.columns.mev_permission_gate_events` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0098 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.db_before.columns.paper_trade_executions` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0102 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.db_before.table_counts.mev_permission_gate_events` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0104 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.db_before.table_counts.paper_trade_executions` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0108 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.db_before.paper_executions` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0109 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.db_after.columns.mev_permission_gate_events` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0111 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.db_after.columns.paper_trade_executions` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0115 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.db_after.table_counts.mev_permission_gate_events` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |
| PH53A02-BCP-0117 | `data/data43_customer_shortlist_real_binding_dryrun_noapi.json` | `data43_customer_shortlist_real_binding_dryrun_noapi.json.db_after.table_counts.paper_trade_executions` | FORBIDDEN_PAYLOAD_FIELD | BRIDGE_TO_CONSUMER_AUTHORITY_LEAK | CRITICAL | false | true |

## Bridge → Consumer Payload Rules

| Rule ID | Rule |
|---|---|
| BCP_RULE_01 | Consumer payload may include only allowed_fields plus false/zero authority-lock defense fields. |
| BCP_RULE_02 | Forbidden fields must be masked before Consumer Binding. |
| BCP_RULE_03 | Fields matching permission/allowed/action/mutation/trigger/payload/execute/order/wallet/trade require mask or rename review. |
| BCP_RULE_04 | Masked field must not be displayed in panel or exported into Consumer payload. |
| BCP_RULE_05 | Hard-block and policy states render as readonly observation state, never as failed trade/execution. |
| BCP_RULE_06 | Missing evidence_ref routes to review_required, never allow/permission. |

## Allowed Consumer Payload Fields

| Field |
|---|
| `blocked_by_policy` |
| `classification` |
| `display_hint` |
| `evidence_count` |
| `evidence_ref` |
| `hard_block_state` |
| `observation_status` |
| `policy_state` |
| `quarantine_state` |
| `readonly_context` |
| `reason_code` |
| `review_required` |
| `risk_context` |
| `risk_state` |
| `snapshot_version` |
| `source_state` |
| `stale_state` |
| `ttl_valid` |

## Forbidden Consumer Payload Fields

| Field |
|---|
| `action` |
| `action_payload` |
| `action_plan` |
| `api_fetch_allowed` |
| `apply_order` |
| `apply_plan_action` |
| `approve_trade` |
| `auto_apply` |
| `buy_signal` |
| `confirm_trade` |
| `db_mutation_allowed` |
| `execute_allowed` |
| `live_allowed` |
| `order` |
| `order_payload` |
| `override_allowed` |
| `paper_allowed` |
| `paper_live_allowed` |
| `payload_json` |
| `planned_action` |
| `planned_icon_action` |
| `planned_layout_action` |
| `route_execute` |
| `sell_signal` |
| `send_payload` |
| `sign_payload` |
| `trade_execution_allowed` |
| `trade_permission` |
| `trigger_allowed` |
| `wallet_connect` |
| `wallet_permission` |

## Protected State

DB_SHA_CHANGED=false
PANEL_SHA_CHANGED=false
PROTECTED_DIFF_EMPTY=true

AUDIT_CHECK_COUNT=74
AUDIT_FAIL_COUNT=0
REVIEW_FINDING_COUNT=4

NEXT_SAFE_STEP=PHASE53A_02_BRIDGE_TO_CONSUMER_PAYLOAD_MASKING_CONTRACT_PLAN_NOAPI
