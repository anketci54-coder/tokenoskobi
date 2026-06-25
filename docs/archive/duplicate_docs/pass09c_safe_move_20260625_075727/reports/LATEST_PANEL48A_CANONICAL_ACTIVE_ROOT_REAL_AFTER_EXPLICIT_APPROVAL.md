# PANEL48A_CANONICAL_ACTIVE_ROOT_REAL_AFTER_EXPLICIT_APPROVAL

created_at: 20260514_122921
status: CANONICAL_ACTIVE_ROOT_REAL_APPLY

## Applied

- canonical_root: `/root/tokenoskobi_clean_v1/active_panel_8096/current`
- canonical_index: `/root/tokenoskobi_clean_v1/active_panel_8096/current/index.html`
- canonical_dashboard_json: `/root/tokenoskobi_clean_v1/active_panel_8096/current/data/dashboard_shell_compact.json`
- service: `tokenoskobi-active-panel-8096.service`
- service_file: `/etc/systemd/system/tokenoskobi-active-panel-8096.service`

## Backup / Rollback

- backup_dir: `/root/tokenoskobi_clean_v1/backups/PANEL48A_CANONICAL_ACTIVE_ROOT_REAL_AFTER_EXPLICIT_APPROVAL_20260514_122921`
- process_meta: `/root/tokenoskobi_clean_v1/backups/PANEL48A_CANONICAL_ACTIVE_ROOT_REAL_AFTER_EXPLICIT_APPROVAL_20260514_122921/previous_8096_process_metadata.json`
- rollback_script: `/root/tokenoskobi_clean_v1/backups/PANEL48A_CANONICAL_ACTIVE_ROOT_REAL_AFTER_EXPLICIT_APPROVAL_20260514_122921/ROLLBACK_PANEL48A_CANONICAL_ACTIVE_ROOT.sh`

## Process

- pids_8096_before: [299919]
- pids_8096_after: [559310]
- stop_results: [{'pid': 299919, 'term_sent': True, 'kill_sent': False, 'stopped': True, 'error': ''}]
- active_service_active_after: active
- active_service_enabled_after: enabled

## HTTP

- http_8096_status: 200
- http_8096_sha: `2f88d220640a1ad4b633dd6fb8b9c641e7485e8ea9177726a634ae9b19d18a9d`
- canonical_index_sha: `2f88d220640a1ad4b633dd6fb8b9c641e7485e8ea9177726a634ae9b19d18a9d`
- http_8096_data_status: 200
- http_8096_data_sha: `0eb2f2981ecd17b734eab57e71d622363b6b1424e4f669255554d88f6a0802a9`
- canonical_dashboard_sha: `0eb2f2981ecd17b734eab57e71d622363b6b1424e4f669255554d88f6a0802a9`

## Checks

- OK | preflight_ok
- OK | apply_error_empty
- OK | backup_dir_exists
- OK | process_meta_exists
- OK | rollback_script_exists
- OK | canonical_index_exists
- OK | canonical_dashboard_exists
- OK | canonical_index_sha_matches_source
- OK | canonical_dashboard_sha_matches_source
- OK | service_file_exists
- OK | service_file_written
- OK | old_8096_stop_attempted
- OK | old_8096_stop_success
- OK | daemon_reload_ok
- OK | enable_ok
- OK | start_ok
- OK | active_service_active
- OK | active_service_enabled
- OK | port_8096_listen
- OK | port_8101_listen
- OK | old_ports_closed
- OK | http_8096_ok
- OK | http_8096_sha_matches_canonical
- OK | http_8096_data_ok
- OK | http_8096_data_sha_matches_canonical
- OK | http_8101_ok
- OK | required_terms_present
- OK | forbidden_terms_absent
- OK | db_unchanged
- OK | wrapper_unchanged
- OK | original_unchanged
- OK | builder_unchanged
- OK | customer_binding_unchanged
- OK | db_integrity_ok
- OK | db_quick_ok
- OK | db_fk_zero
- OK | paper_runtime_zero
- OK | news_service_result_success
- OK | news_service_exec_status_zero
- OK | news_timer_active_unchanged
- OK | news_timer_enabled_unchanged
- OK | runner_zero
- OK | lock_absent

## Failed Checks

- none

## Safety Result

- DB write: 0
- API/fetch/external network: 0
- schema apply: 0
- news runner/timer change: 0
- paper/live: 0
- active panel canonical root write: 1
- managed 8096 service write/start: 1

## Decision

- canonical_active_root_real_apply_passed: True
- main_panel_now_served_from_canonical_root: True
- managed_service_active: True
- rollback_ready: True
- post_apply_audit_required_next: True
- next_phase: PANEL49_CANONICAL_ACTIVE_ROOT_POST_APPLY_AUDIT_NOAPI
- alternate_next_phase: RISK30_CUSTOMER_SHORTLIST_RISK_REWARD_DETAIL_PLAN_NOAPI
