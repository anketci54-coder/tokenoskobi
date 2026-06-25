# COINOSKOBI_XYZ_ROADMAP_NEXT_APPLY_COMPLETE_NOAPI

FINAL_DECISION=PASS_XYZ_ROADMAP_NEXT_APPLY_COMPLETE
FINAL_OK=True
VALIDATION_ERROR_COUNT=0
VALIDATION_ERRORS=NONE

CURRENT_TARGET=/var/www/coinoskobi_xyz_staging/releases/20260524_165636
CURRENT_INDEX_SHA=f5579cc643139f946902e8b29fac80da5eb340a5f9bcf0e89c3e66255847d5ef
CANDIDATE_SHA=f5579cc643139f946902e8b29fac80da5eb340a5f9bcf0e89c3e66255847d5ef

ROOT_URL=https://www.coinoskobi.xyz/
ROADMAP_URL=https://www.coinoskobi.xyz/roadmap/
PANEL_URL=https://www.coinoskobi.xyz/panel/
MOBILE_URL=https://www.coinoskobi.xyz/mobile/

ROOT_STATUS=200
ROADMAP_STATUS=200
PANEL_NOAUTH_STATUS=401
MOBILE_NOAUTH_STATUS=401

COMPLETE_CHECKS={'apply_real_json_parse_ok': True, 'marker_json_parse_ok': True, 'locator_json_parse_ok': True, 'plan_json_parse_ok': True, 'locator_final_ok': True, 'locator_decision_complete': True, 'locator_unsafe_hits_zero': True, 'marker_confirmed_current_sha': True, 'current_sha_matches_candidate': True, 'root_status_200': True, 'roadmap_status_200': True, 'root_body_matches_current': True, 'roadmap_body_matches_current': True, 'root_and_roadmap_same': True, 'panel_noauth_401': True, 'mobile_noauth_401': True, 'nginx_test_ok': True, 'db_read_ok': True, 'integrity_ok': True, 'fk_ok': True}
SAFETY={'active_index_unchanged': True, 'active_data_unchanged': True, 'active_risk_data_unchanged': True, 'active_mobile_index_unchanged': True, 'live_db_unchanged': True, 'current_index_unchanged_during_complete': True, 'nginx_target_unchanged': True, 'auth_file_unchanged': True}

DB_READ_OK=True
INTEGRITY_CHECK=ok
FK_ERROR_COUNT=0

NO_WEBROOT_WRITE=True
NO_CURRENT_SYMLINK_CHANGE=True
NO_NGINX_WRITE=True
NO_NGINX_RELOAD=True
NO_AUTH_WRITE=True
NO_ACTIVE_PANEL_WRITE=True
NO_DB_WRITE=True
NO_API_FETCH=True
LIVE_TRADE=0
PAPER_TRADE_EXECUTION=0
AUTH_PASSWORD_PRINTED=False

NEXT_PHASE=COINOSKOBI_COM_PUBLIC_SITE_PLAN_NOAPI
PARALLEL_HOLD=COINOSKOBI_PREVIEW_CLEANUP_ARCHIVE_TIGHT_REAL_AFTER_EXPLICIT_APPROVAL
