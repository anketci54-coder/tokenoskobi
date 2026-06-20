# Coinoskobi XYZ Panel V2 Real UI Bind Apply Plan

FINAL_DECISION=PASS_PANEL_V2_REAL_UI_BIND_APPLY_PLAN_READY
FINAL_OK=True
VALIDATION_ERROR_COUNT=0
VALIDATION_ERRORS=NONE

## Target

After explicit approval, create/replace:

TARGET_ROUTE=/root/tokenoskobi_clean_v1/active_panel_8096/current/panel_v2
TARGET_LIVE_URL=https://www.coinoskobi.xyz/panel/panel_v2/

Because Nginx has /panel/ -> 127.0.0.1:8096/ proxy, this route maps to 8096 /panel_v2/.

## Candidate

CANDIDATE_ROUTE_DIR=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_PANEL_V2_REAL_UI_BIND_APPLY_PLAN_NOAPI/20260524_211408/candidate_active_panel_v2_route
CANDIDATE_INDEX=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_PANEL_V2_REAL_UI_BIND_APPLY_PLAN_NOAPI/20260524_211408/candidate_active_panel_v2_route/index.html
CANDIDATE_MODEL=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_PANEL_V2_REAL_UI_BIND_APPLY_PLAN_NOAPI/20260524_211408/candidate_active_panel_v2_route/data/panel_v2_model.json
PREVIEW_URL=http://159.195.74.132:8146/

## Bind sources

ACTIVE_DATA=/root/tokenoskobi_clean_v1/active_panel_8096/current/data/production_v2_control_center_data.json
ACTIVE_RISK_DATA=/root/tokenoskobi_clean_v1/active_panel_8096/current/data/risk_security_preview_data.json
DB=/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite
XYZ_COMPLETE_JSON=/root/tokenoskobi_clean_v1/data/coinoskobi_xyz_roadmap_next_apply_complete_noapi.json
COM_PREVIEW_JSON=/root/tokenoskobi_clean_v1/data/coinoskobi_com_public_site_preview_noapi.json

## Real apply shape

1. Backup current active panel_v2 route if exists.
2. Copy candidate route to /root/tokenoskobi_clean_v1/active_panel_8096/current/panel_v2.
3. Do not modify active root index.
4. Do not modify active production data/risk/mobile.
5. Do not write DB.
6. Do not change Nginx/auth.
7. HTTP check:
   - https://www.coinoskobi.xyz/panel/panel_v2/ with auth
   - noauth remains 401 through /panel/ parent
8. Post-audit SHA and safety.

## Required approval

COINOSKOBI XYZ PANEL V2 REAL UI BIND APPLY REAL için onay veriyorum

## Safety now

ACTIVE_INDEX_UNCHANGED=True
ACTIVE_DATA_UNCHANGED=True
ACTIVE_RISK_DATA_UNCHANGED=True
ACTIVE_MOBILE_INDEX_UNCHANGED=True
LIVE_DB_UNCHANGED=True
NGINX_TARGET_UNCHANGED=True
AUTH_FILE_UNCHANGED=True
TARGET_ROUTE_UNCHANGED=True

NO_ACTIVE_PANEL_WRITE=True
NO_DB_WRITE=True
NO_NGINX_WRITE=True
NO_NGINX_RELOAD=True
NO_AUTH_WRITE=True
NO_API_FETCH=True
LIVE_TRADE=0
PAPER_TRADE_EXECUTION=0
AUTH_PASSWORD_PRINTED=False
