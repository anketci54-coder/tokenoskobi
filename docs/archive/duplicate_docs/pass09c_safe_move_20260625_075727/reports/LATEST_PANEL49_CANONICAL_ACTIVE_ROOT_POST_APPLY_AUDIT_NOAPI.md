# PANEL49_CANONICAL_ACTIVE_ROOT_POST_APPLY_AUDIT_NOAPI

created_at: 20260514_123533
status: CANONICAL_ACTIVE_ROOT_POST_APPLY_AUDIT

## URLs

- ANA PANEL: `http://159.195.74.132:8096/`
- TEST PANEL: `http://159.195.74.132:8101/`

## Canonical Active Root

- canonical_root: `/root/tokenoskobi_clean_v1/active_panel_8096/current`
- canonical_index: `/root/tokenoskobi_clean_v1/active_panel_8096/current/index.html`
- canonical_dashboard_json: `/root/tokenoskobi_clean_v1/active_panel_8096/current/data/dashboard_shell_compact.json`
- canonical_index_sha: `2f88d220640a1ad4b633dd6fb8b9c641e7485e8ea9177726a634ae9b19d18a9d`
- canonical_dashboard_sha: `0eb2f2981ecd17b734eab57e71d622363b6b1424e4f669255554d88f6a0802a9`

## Service / Process

- service: `tokenoskobi-active-panel-8096.service`
- active: `active`
- enabled: `enabled`
- pids_8096: `[559310]`
- deleted_cwd_count: 0
- canonical_cwd_count: 1
- service_pid_count: 1

## HTTP

- http_8096_status: 200
- http_8096_sha: `2f88d220640a1ad4b633dd6fb8b9c641e7485e8ea9177726a634ae9b19d18a9d`
- http_8096_data_status: 200
- http_8096_data_sha: `0eb2f2981ecd17b734eab57e71d622363b6b1424e4f669255554d88f6a0802a9`
- http_8101_status: 200
- http_8101_sha: `2f88d220640a1ad4b633dd6fb8b9c641e7485e8ea9177726a634ae9b19d18a9d`

## Data Counts

- rows: 10
- ready_manual: 3
- vur_kac: 3
- watching: 4
- buy_enabled: 0
- simulation_only: 10

## Rollback

- backup_dir: `/root/tokenoskobi_clean_v1/backups/PANEL48A_CANONICAL_ACTIVE_ROOT_REAL_AFTER_EXPLICIT_APPROVAL_20260514_122921`
- rollback_script: `/root/tokenoskobi_clean_v1/backups/PANEL48A_CANONICAL_ACTIVE_ROOT_REAL_AFTER_EXPLICIT_APPROVAL_20260514_122921/ROLLBACK_PANEL48A_CANONICAL_ACTIVE_ROOT.sh`

## Checks

- OK | panel48a_passed
- OK | panel47c_passed
- OK | canonical_root_exists
- OK | canonical_index_exists
- OK | canonical_dashboard_exists
- OK | canonical_index_sha_expected
- OK | canonical_dashboard_sha_expected
- OK | active_service_file_exists
- OK | active_service_active
- OK | active_service_enabled
- OK | active_service_main_pid_present
- OK | port_8096_listen
- OK | port_8101_listen
- OK | old_ports_closed
- OK | pids_8096_found
- OK | deleted_cwd_zero
- OK | canonical_cwd_pid_found
- OK | service_pid_found
- OK | http_8096_ok
- OK | http_8096_sha_matches_canonical
- OK | http_8096_data_ok
- OK | http_8096_data_sha_matches_canonical
- OK | http_8101_ok
- OK | required_terms_present
- OK | forbidden_terms_absent
- OK | data_rows_10
- OK | data_ready_manual_3
- OK | data_vur_kac_3
- OK | data_watching_4
- OK | data_buy_enabled_0
- OK | data_simulation_only_10
- OK | rollback_script_exists
- OK | backup_dir_exists
- OK | db_unchanged_during_audit
- OK | wrapper_unchanged_during_audit
- OK | original_unchanged_during_audit
- OK | builder_unchanged_during_audit
- OK | customer_binding_unchanged_during_audit
- OK | canonical_index_unchanged_during_audit
- OK | canonical_dashboard_unchanged_during_audit
- OK | service_file_unchanged_during_audit
- OK | db_integrity_ok
- OK | db_quick_ok
- OK | db_fk_zero
- OK | paper_runtime_zero
- OK | news_service_result_success
- OK | news_service_exec_status_zero
- OK | news_timer_inactive
- OK | news_timer_enabled
- OK | runner_zero
- OK | lock_absent
- OK | builder_compile_zero

## Failed Checks

- none

## Safety Result

- DB write: 0
- API/fetch/external network: 0
- schema apply: 0
- active panel file write in this audit: 0
- service restart in this audit: 0
- timer change: 0
- runner change: 0
- paper/live: 0

## Decision

- canonical_active_root_post_audit_passed: True
- main_panel_confirmed_canonical: True
- orphan_deleted_cwd_removed: True
- managed_service_confirmed: True
- two_url_policy_clean: True
- rollback_ready: True
- safe_to_continue_product_layers: True
- main_panel_url: http://159.195.74.132:8096/
- test_panel_url: http://159.195.74.132:8101/
- next_phase: RISK30_CUSTOMER_SHORTLIST_RISK_REWARD_DETAIL_PLAN_NOAPI
- alternate_next_phase: PANEL50_ACTIVE_PANEL_STABILITY_MONITOR_PLAN_NOAPI
