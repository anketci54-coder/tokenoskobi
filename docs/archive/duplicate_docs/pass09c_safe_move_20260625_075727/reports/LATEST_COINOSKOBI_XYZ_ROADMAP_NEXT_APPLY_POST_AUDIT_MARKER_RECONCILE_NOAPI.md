# COINOSKOBI_XYZ_ROADMAP_NEXT_APPLY_POST_AUDIT_MARKER_RECONCILE_NOAPI

FINAL_DECISION=REVIEW_REQUIRED_XYZ_ROADMAP_MARKER_RECONCILE
FINAL_OK=False
VALIDATION_ERROR_COUNT=3
VALIDATION_ERRORS=CHECK_FAILED_current_bad_old_text_absent,CHECK_FAILED_root_bad_old_text_absent,CHECK_FAILED_roadmap_bad_old_text_absent

PREVIOUS_REAL_FALSE_NEGATIVE=True
FALSE_NEGATIVE_REASON=strict Turkish marker check failed, but HTTP body matches current index and relaxed markers pass

CURRENT_TARGET=/var/www/coinoskobi_xyz_staging/releases/20260524_165636
CURRENT_INDEX=/var/www/coinoskobi_xyz_staging/current/index.html
CURRENT_INDEX_SHA=f5579cc643139f946902e8b29fac80da5eb340a5f9bcf0e89c3e66255847d5ef
CANDIDATE_SHA_FROM_PLAN=f5579cc643139f946902e8b29fac80da5eb340a5f9bcf0e89c3e66255847d5ef

ROOT_STATUS=200
ROOT_SIZE=11502
ROOT_BODY_SHA=f5579cc643139f946902e8b29fac80da5eb340a5f9bcf0e89c3e66255847d5ef
ROOT_BODY_MATCHES_CURRENT_INDEX=True

ROADMAP_STATUS=200
ROADMAP_SIZE=11502
ROADMAP_BODY_SHA=f5579cc643139f946902e8b29fac80da5eb340a5f9bcf0e89c3e66255847d5ef
ROADMAP_BODY_MATCHES_CURRENT_INDEX=True

ROOT_AND_ROADMAP_SAME_BODY=True

CURRENT_RELAXED_MARKERS={'xyz_staging': True, 'roadmap_word': True, 'auth_protected_tr': True, 'com_public': True, 'next_apply_phase': True, 'db_safety': True}
ROOT_RELAXED_MARKERS={'xyz_staging': True, 'roadmap_word': True, 'auth_protected_tr': True, 'com_public': True, 'next_apply_phase': True}
ROADMAP_RELAXED_MARKERS={'xyz_staging': True, 'roadmap_word': True, 'auth_protected_tr': True, 'com_public': True, 'next_apply_phase': True}

CURRENT_BAD_OLD_TEXT_HITS={'domain/nginx/ssl yok': True, 'domain, nginx, ssl değişikliği yapmaz': False, 'coinoskobi_domain_staging_binding_plan_noapi': False, 'xyz domain binding plan': False}
ROOT_BAD_OLD_TEXT_HITS={'domain/nginx/ssl yok': True, 'domain, nginx, ssl değişikliği yapmaz': False, 'coinoskobi_domain_staging_binding_plan_noapi': False, 'xyz domain binding plan': False}
ROADMAP_BAD_OLD_TEXT_HITS={'domain/nginx/ssl yok': True, 'domain, nginx, ssl değişikliği yapmaz': False, 'coinoskobi_domain_staging_binding_plan_noapi': False, 'xyz domain binding plan': False}

ACTIVE_INDEX_UNCHANGED=True
ACTIVE_DATA_UNCHANGED=True
ACTIVE_RISK_DATA_UNCHANGED=True
ACTIVE_MOBILE_INDEX_UNCHANGED=True
LIVE_DB_UNCHANGED=True
CURRENT_INDEX_UNCHANGED_DURING_AUDIT=True
NGINX_TARGET_UNCHANGED=True
AUTH_FILE_UNCHANGED=True

DB_READ_OK=True
INTEGRITY_CHECK=ok
FK_ERROR_COUNT=0
NGINX_TEST_OK=True

ROOT_HEADERS=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_ROADMAP_NEXT_APPLY_POST_AUDIT_MARKER_RECONCILE_NOAPI/20260524_170414/root_headers.txt
ROADMAP_HEADERS=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_ROADMAP_NEXT_APPLY_POST_AUDIT_MARKER_RECONCILE_NOAPI/20260524_170414/roadmap_headers.txt
ROOT_BODY=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_ROADMAP_NEXT_APPLY_POST_AUDIT_MARKER_RECONCILE_NOAPI/20260524_170414/root_body.html
ROADMAP_BODY=/root/tokenoskobi_clean_v1/_COINOSKOBI_XYZ_ROADMAP_NEXT_APPLY_POST_AUDIT_MARKER_RECONCILE_NOAPI/20260524_170414/roadmap_body.html

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

NEXT_PHASE=REVIEW_XYZ_ROADMAP_MARKER_RECONCILE_FAILURE
