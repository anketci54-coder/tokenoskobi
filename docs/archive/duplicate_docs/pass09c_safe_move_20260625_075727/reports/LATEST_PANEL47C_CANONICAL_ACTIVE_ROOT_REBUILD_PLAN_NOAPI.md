# PANEL47C_CANONICAL_ACTIVE_ROOT_REBUILD_PLAN_NOAPI

created_at: 20260514_113317
status: CANONICAL_ACTIVE_ROOT_REBUILD_PLAN_ONLY

## Plan Özeti

- 8096 şu an silinmiş cwd üzerinden orphan http.server ile çalışıyor.
- Bu faz gerçek değişiklik yapmaz.
- Kalıcı canonical root ve managed service için real-apply planı hazırlar.
- Eski PANEL48 hâlâ yasak.

## İki URL

- ANA PANEL: `http://159.195.74.132:8096/`
- TEST PANEL: `http://159.195.74.132:8101/`

## Canonical Target

- canonical_root: `/root/tokenoskobi_clean_v1/active_panel_8096/current`
- canonical_index: `/root/tokenoskobi_clean_v1/active_panel_8096/current/index.html`
- canonical_dashboard_json: `/root/tokenoskobi_clean_v1/active_panel_8096/current/data/dashboard_shell_compact.json`
- service_name: `tokenoskobi-active-panel-8096.service`
- service_file: `/etc/systemd/system/tokenoskobi-active-panel-8096.service`

## Kaynak Test Panel

- source_index: `/root/tokenoskobi_clean_v1/panel_previews/panel46d_dashboard_shell_compact_mobile_polish_20260514_094242/index.html`
- source_dashboard: `/root/tokenoskobi_clean_v1/panel_previews/panel46d_dashboard_shell_compact_mobile_polish_20260514_094242/data/dashboard_shell_compact.json`
- source_index_sha: `2f88d220640a1ad4b633dd6fb8b9c641e7485e8ea9177726a634ae9b19d18a9d`
- source_dashboard_sha: `0eb2f2981ecd17b734eab57e71d622363b6b1424e4f669255554d88f6a0802a9`
- row_count: 10
- buy_enabled: 0
- simulation_only: 10

## Açık Onay Cümlesi

`PANEL48A canonical active root real için onay veriyorum`

## Output Files

- plan_json: `/root/tokenoskobi_clean_v1/_panel47c_canonical_active_root_rebuild_plan_noapi/20260514_113317/panel47c_canonical_active_root_rebuild_plan.json`
- backup_plan: `/root/tokenoskobi_clean_v1/_panel47c_canonical_active_root_rebuild_plan_noapi/20260514_113317/panel47c_backup_and_rollback_plan.json`
- validation_plan: `/root/tokenoskobi_clean_v1/_panel47c_canonical_active_root_rebuild_plan_noapi/20260514_113317/panel47c_post_apply_validation_plan.json`
- apply_contract: `/root/tokenoskobi_clean_v1/_panel47c_canonical_active_root_rebuild_plan_noapi/20260514_113317/panel47c_to_panel48a_real_apply_contract.json`
- service_unit_draft: `/root/tokenoskobi_clean_v1/_panel47c_canonical_active_root_rebuild_plan_noapi/20260514_113317/tokenoskobi-active-panel-8096.service.DRAFT_NOT_APPLIED`
- future_apply_draft: `/root/tokenoskobi_clean_v1/_panel47c_canonical_active_root_rebuild_plan_noapi/20260514_113317/PANEL48A_REAL_APPLY_DRAFT_REFUSES_EXECUTION.sh`
- rollback_draft: `/root/tokenoskobi_clean_v1/_panel47c_canonical_active_root_rebuild_plan_noapi/20260514_113317/ROLLBACK_PANEL48A_DRAFT_REFUSES_EXECUTION.sh`

## Checks

- OK | panel47b2_passed
- OK | deleted_cwd_confirmed
- OK | orphan_8096_confirmed
- OK | panel46d_passed
- OK | panel46e_passed
- OK | source_index_exists
- OK | source_dashboard_exists
- OK | source_index_sha_present
- OK | source_dashboard_sha_present
- OK | source_rows_10
- OK | source_buy_enabled_0
- OK | source_simulation_only_10
- OK | main_8096_listen_now
- OK | test_8101_listen_now
- OK | old_ports_closed_now
- OK | pid_8096_found
- OK | deleted_cwd_count_positive
- OK | orphan_http_count_positive
- OK | canonical_root_does_not_exist_yet
- OK | canonical_index_not_written
- OK | canonical_dashboard_not_written
- OK | plan_written
- OK | backup_plan_written
- OK | validation_plan_written
- OK | apply_contract_written
- OK | service_unit_draft_written
- OK | future_script_draft_written
- OK | rollback_draft_written
- OK | db_unchanged
- OK | wrapper_unchanged
- OK | original_unchanged
- OK | builder_unchanged
- OK | customer_binding_unchanged
- OK | canonical_index_unchanged
- OK | canonical_dashboard_unchanged
- OK | service_file_unchanged
- OK | db_integrity_ok
- OK | db_quick_ok
- OK | db_fk_zero
- OK | paper_runtime_zero
- OK | service_result_success
- OK | service_exec_status_zero
- OK | timer_active_unchanged
- OK | timer_enabled_unchanged
- OK | runner_zero
- OK | lock_absent
- OK | builder_compile_zero
- OK | builder_sha_expected

## Failed Checks

- none

## Safety Result

- DB write: 0
- API/fetch/external network: 0
- schema apply: 0
- canonical root write: 0
- service file write to /etc: 0
- active panel changed: 0
- public copy to active panel: 0
- service restart: 0
- timer change: 0
- runner change: 0
- paper/live: 0

## Decision

- canonical_rebuild_plan_ready: True
- real_apply_allowed_now: False
- exact_approval_required: True
- approval_phrase: PANEL48A canonical active root real için onay veriyorum
- panel48a_allowed_after_exact_approval: True
- old_panel48_still_blocked: True
- canonical_root: /root/tokenoskobi_clean_v1/active_panel_8096/current
- service_name: tokenoskobi-active-panel-8096.service
- active_panel_apply_allowed_now: False
- public_copy_to_active_panel_allowed_now: False
- db_write_allowed_now: False
- api_fetch_allowed_now: False
- paper_live_allowed_now: False
- service_restart_allowed_now: False
- next_phase: PANEL48A_CANONICAL_ACTIVE_ROOT_REAL_AFTER_EXPLICIT_APPROVAL
- post_apply_audit_phase: PANEL49_CANONICAL_ACTIVE_ROOT_POST_APPLY_AUDIT_NOAPI
- alternate_next_phase: RISK30_CUSTOMER_SHORTLIST_RISK_REWARD_DETAIL_PLAN_NOAPI
