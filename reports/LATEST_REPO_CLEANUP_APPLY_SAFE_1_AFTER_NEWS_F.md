# Repo Cleanup Apply Safe 1 After NEWS-F

- stage: `REPO_CLEANUP_APPLY_SAFE_1_AFTER_NEWS_F`
- generated_at_utc: `2026-07-08T13:09:41.084843+00:00`
- decision: `OK_REPO_CLEANUP_APPLY_SAFE_1_DONE`
- next_step: `REPO_CLEANUP_POST_APPLY_AUDIT_NOAPI`

## Scope

- delete: `__pycache__`, `*.pyc`, generated cache files
- external archive: `_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096`
- untouched: `backups`, `logs`, `*.bak`, `*.log`, DB, docs, runtime, systemd

## Summary

- cache_target_count: `73`
- cache_deleted_ok_count: `73`
- cache_delete_fail_count: `0`
- phase_dir_archived: `True`
- phase_dir_archive_target: `/root/tokenoskobi_external_archive/repo_cleanup_after_news_f_20260708T130941Z/_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096`
- archive_failed: `False`
- fail_count: `0`
- warn_count: `0`

## Archived

```json
{
  "action": "ARCHIVE_EXTERNAL_PHASE_DIR",
  "before": {
    "absolute_path": "/root/tokenoskobi_clean_v1/_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096",
    "exists": true,
    "is_dir": true,
    "is_file": false,
    "mtime_utc": "2026-07-08T12:17:37.813431+00:00",
    "path": "_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096",
    "sha256": null,
    "size_bytes": null
  },
  "error": null,
  "ok": true,
  "skipped": false,
  "source": "/root/tokenoskobi_clean_v1/_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096",
  "target": "/root/tokenoskobi_external_archive/repo_cleanup_after_news_f_20260708T130941Z/_phase20h_tokonoskobi_radar_panel_turkish_sentence_cleaner_8096",
  "target_exists": true
}
```

## Deleted Cache Targets

- `runtime/__pycache__/bsc_event_source_reader_v1_selftest.cpython-313.pyc` ok=`True` error=`None`
- `runtime/__pycache__/bsc_event_source_reader_v1.cpython-313.pyc` ok=`True` error=`None`
- `runtime/__pycache__/system_control_status_refresh_loop_runner.cpython-313.pyc` ok=`True` error=`None`
- `runtime/__pycache__/conveyor_readmodel_envelope_v1.cpython-313.pyc` ok=`True` error=`None`
- `runtime/__pycache__/conveyor_readmodel_envelope_v1_selftest.cpython-313.pyc` ok=`True` error=`None`
- `core/__pycache__/policy.cpython-313.pyc` ok=`True` error=`None`
- `core/__pycache__/authority.cpython-313.pyc` ok=`True` error=`None`
- `core/__pycache__/approval.cpython-313.pyc` ok=`True` error=`None`
- `core/__pycache__/paths.cpython-313.pyc` ok=`True` error=`None`
- `core/__pycache__/secrets.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/news_center_live_producer_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n17a5_news_matcher_binding_tempdb_runner_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/command_center_live_producer_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21f_command_fusion_bind_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/panel_public_readmodel_bridge_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/risk_center_live_producer_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/era44_public_exposure_post_fix_audit_noapi.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/phase9_commercial_observation_runtime.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21_multi_center_production_master_bundle_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/runtime_observability_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/provider_secret_vault_handler_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/runtime_provider_abstraction_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/era44_public_exposure_boundary_fix_noapi.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/payg_rpc_budget_guard_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/news_runtime_probe_readonly_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n17_news_runtime_decision_audit_bundle_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/technical_center_live_producer_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/era44_governance_and_graph_truth_repair_noapi.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n17a3_news_pipeline_deep_audit_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21a_whale_source_proof_bundle_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n9_source_to_public_readmodel_binding_probe.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/news_radar_refresh_runner_v1.ORIGINAL_NEWS27A11_20260510_211813.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21g_final_panel_system_post_audit_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n17a4_news_matcher_write_binding_audit_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21e_full_center_post_audit_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/runtime_whale_graph_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/news_token_matcher_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/runtime_readonly_rpc_shadow_intake_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/runtime_chain_abstraction_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/whale_center_live_producer_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/onchain_center_live_producer_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/era45_reachability_fix_and_speed_baseline_noapi.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/runtime_multi_rpc_trust_engine_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/news_source_ingestion_runner_adapter_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/era_close.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21c2_risk_panel_bind_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21d_lifecycle_source_proof_bundle_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/runtime_hybrid_rpc_cost_guard_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/runtime_shadow_feed_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/full_radar_panel_data_builder_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21b2_onchain_panel_bind_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/lifecycle_center_live_producer_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/backpressure_readmodel_refresh_runner_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/runtime_activation_truth_audit_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/era43_preflight_readonly_audit_noapi.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n18_n19_n20_news_production_bundle_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n17a2_news_matcher_dryrun_probe_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21d2_lifecycle_panel_bind_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n17a1_news_runner_static_audit_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/news_radar_refresh_runner_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/system_center_live_producer_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/panel_live_readmodel_builder_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/era45_live_reachability_verification_noapi.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21b_onchain_source_proof_bundle_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/news_social_launch_signal_writer_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/test_news_token_matcher_v1_noapi.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/news_source_ingestion_runner_adapter_contract_check_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__/n21c_risk_source_proof_bundle_v1.cpython-313.pyc` ok=`True` error=`None`
- `tools/__pycache__` ok=`True` error=`None`
- `__pycache__/tokenoskobi_kernel.cpython-313.pyc` ok=`True` error=`None`
- `core/__pycache__` ok=`True` error=`None`
- `runtime/__pycache__` ok=`True` error=`None`
- `__pycache__` ok=`True` error=`None`

## Git Status After

```text
M data/control/ACTIVE_CORE_RANKING.json
 M data/control/ACTIVE_EXECUTION_GRAPH.json
 M data/control/MINIMAL_ACTIVE_CORE_MANIFEST.json
 M data/control/USED_BY_RUNTIME_INDEX.json
?? tools/repo_cleanup_apply_safe_1_after_news_f_v1.py
```
