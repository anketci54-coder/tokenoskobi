# COINOSKOBI_XYZ_ROADMAP_NEXT_APPLY_PLAN_NOAPI

FINAL_DECISION=PASS_XYZ_ROADMAP_NEXT_APPLY_PLAN_READY_NOAPI
FINAL_OK=True
VALIDATION_ERROR_COUNT=0
VALIDATION_ERRORS=NONE

## Source

SOURCE_PREVIEW_ROOT=/root/tokenoskobi_clean_v1/panel_previews/coinoskobi_xyz_roadmap_content_current_state_fix_preview_8144_20260524_164608
SOURCE_INDEX=/root/tokenoskobi_clean_v1/panel_previews/coinoskobi_xyz_roadmap_content_current_state_fix_preview_8144_20260524_164608/index.html

## Candidate

CANDIDATE_RELEASE=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_ROADMAP_NEXT_APPLY_PLAN_NOAPI/20260524_165221/candidate_xyz_roadmap_release
CANDIDATE_INDEX=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_ROADMAP_NEXT_APPLY_PLAN_NOAPI/20260524_165221/candidate_xyz_roadmap_release/index.html
DIFF_OUT=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_ROADMAP_NEXT_APPLY_PLAN_NOAPI/20260524_165221/current_vs_candidate_roadmap.diff

## Live apply plan

Planned real apply:
- backup current release target
- create new release under /var/www/coinoskobi_xyz_staging/releases/<stamp>
- copy corrected roadmap index/data into new release
- atomically switch /var/www/coinoskobi_xyz_staging/current symlink
- curl root and /roadmap/
- write rollback script

Forbidden in real apply:
- no active 8096 panel write
- no DB write
- no API/fetch
- no nginx config write
- no auth write
- no live/paper trade

## Required approval

COINOSKOBI XYZ ROADMAP NEXT APPLY REAL için onay veriyorum

## Safety in this plan phase

ACTIVE_INDEX_UNCHANGED=True
ACTIVE_DATA_UNCHANGED=True
ACTIVE_RISK_DATA_UNCHANGED=True
ACTIVE_MOBILE_INDEX_UNCHANGED=True
LIVE_DB_UNCHANGED=True
CURRENT_INDEX_UNCHANGED=True
NGINX_TARGET_UNCHANGED=True
AUTH_FILE_UNCHANGED=True
