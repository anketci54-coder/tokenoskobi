# UI_BUILD4_MOTION_STATE_SNAPSHOT_DRYRUN_NOAPI

Timestamp: `20260517_192952`

## Final

- FINAL_STATUS=PASS
- FINAL_GATE=UI_BUILD4_MOTION_STATE_SNAPSHOT_DRYRUN_READY
- DB_UNCHANGED=True

## Scope

Dry-run only.

No `data/motion_states` directory was created.  
No production motion state file was written.  
The Token Yaşam motion snapshot exists only inside this phase JSON/report.

## Truth engine rule

**No source_uid means no motion.**

## Summary

- department_count=6
- moving_count=0
- silent_count=6
- stale_count=0
- fake_motion_count=0
- panel_generated_motion_count=0

## Department motion states

### Olay Yeri İnceleme

- state: `silent`
- intensity: `0.0`
- visual_policy: `static_icon`
- source_layer: `lifecycle_layer/onchain_layer`
- source_uid: `None`
- freshness_seconds: `None`
- expires_at: `None`
- reason: No canonical source rows found for required source: fresh event.
- blocked_motion_reason: `NO_SOURCE_ROWS`

### Adli Soruşturma

- state: `silent`
- intensity: `0.0`
- visual_policy: `static_icon`
- source_layer: `onchain_layer/identity_layer`
- source_uid: `None`
- freshness_seconds: `None`
- expires_at: `None`
- reason: Source too old for motion: source_gate_decisions.
- blocked_motion_reason: `SOURCE_TOO_OLD`

### Şüpheliler / Arananlar

- state: `silent`
- intensity: `0.0`
- visual_policy: `static_icon`
- source_layer: `onchain_layer/risk_layer`
- source_uid: `None`
- freshness_seconds: `None`
- expires_at: `None`
- reason: No canonical source rows found for required source: fresh suspect wallet/cluster evidence.
- blocked_motion_reason: `NO_SOURCE_ROWS`

### Klinik / Yoğun Bakım

- state: `silent`
- intensity: `0.0`
- visual_policy: `static_icon`
- source_layer: `lifecycle_layer/market_layer/risk_layer`
- source_uid: `None`
- freshness_seconds: `None`
- expires_at: `None`
- reason: No canonical source rows found for required source: clinical_watch.
- blocked_motion_reason: `NO_SOURCE_ROWS`

### Otopsi

- state: `silent`
- intensity: `0.0`
- visual_policy: `static_icon`
- source_layer: `lifecycle_layer/risk_layer/market_layer`
- source_uid: `None`
- freshness_seconds: `None`
- expires_at: `None`
- reason: No canonical source rows found for required source: active autopsy_status.
- blocked_motion_reason: `NO_SOURCE_ROWS`

### Morg

- state: `silent`
- intensity: `0.0`
- visual_policy: `static_icon`
- source_layer: `lifecycle_layer`
- source_uid: `None`
- freshness_seconds: `None`
- expires_at: `None`
- reason: No canonical source rows found for required source: morg_status.
- blocked_motion_reason: `NO_SOURCE_ROWS`

## Validation

- Moving states must have source_uid.
- Moving states must have reason.
- Moving states must have freshness.
- Moving states must have expiry.
- Silent/stale states must not animate.
- Fake motion count must be zero.
- Panel-generated motion count must be zero.

## Next phase

`UI_BUILD5_TOKEN_YASAM_LIVING_PREVIEW_PLAN_NOAPI`
