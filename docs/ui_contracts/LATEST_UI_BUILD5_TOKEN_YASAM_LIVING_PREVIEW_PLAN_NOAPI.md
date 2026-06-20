# UI_BUILD5_TOKEN_YASAM_LIVING_PREVIEW_PLAN_NOAPI

Timestamp: `20260517_193230`

## Final

- FINAL_STATUS=PASS
- FINAL_GATE=UI_BUILD5_TOKEN_YASAM_LIVING_PREVIEW_PLAN_READY
- DB_UNCHANGED=True

## Scope

Plan only.

No preview generated.  
No active panel mutation.  
No DB/API/fetch/paper/live.  
No production view_model file written.  
No production motion_state file written.

## Source

Source baseline:

`/root/tokenoskobi_clean_v1/accepted_baselines/token_yasam_merkezi_final_panel64_20260515_175146`

Accepted logo preview:

`/root/tokenoskobi_clean_v1/panel_previews/tokenyasam_left_logo_circle_bigger_cleanbg_latest`

Master asset pack:

`/root/tokenoskobi_clean_v1/panel_assets/token_yasam_master_pack_v1`

## Build3 / View model gate

- vm_has_six_departments=True
- all_departments_have_detail_ref=True
- all_departments_have_motion_state_ref=True
- all_departments_no_fake_rule=True
- primary_screen_body_scroll_allowed=False

## Build4 / Motion truth gate

- has_six_department_motion_states=True
- fake_motion_count=0
- panel_generated_motion_count=0
- moving_count=0
- silent_count=6

## Preview plan

Next preview, if approved, will:

- create a separate 8104 preview only
- preserve accepted baseline layout
- preserve circular clean logo placement
- keep six department cards summary-only
- use detail_ref for detail surfaces
- keep icons static when motion state has no source_uid
- fail any primary body scroll
- not promote to baseline automatically
- not touch active 8096 / 8101 / 8102

## Required next approval sentence

`UI_BUILD6_TOKEN_YASAM_LIVING_PREVIEW_AFTER_APPROVAL için onay veriyorum`

## Next phase

`UI_BUILD6_TOKEN_YASAM_LIVING_PREVIEW_AFTER_APPROVAL`
