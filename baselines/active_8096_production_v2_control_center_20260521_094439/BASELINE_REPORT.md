# ACTIVE 8096 Production V2 Baseline

FINAL_DECISION=PASS  
STAMP=20260521_094439  
ACTIVE_URL=http://159.195.74.132:8096/?v=20260521_094439

## Baseline

Current active 8096 production panel is locked as:

ACTIVE_8096_PRODUCTION_V2_CONTROL_CENTER

## Checks

- INDEX_MATCH=1
- DATA_MATCH=1
- ROLLBACK_READY=1
- ASSET_OK=1
- HTTP_CODE=200
- HTTP_BYTES=35104
- VISIBLE_BAD_COUNT=0
- RULE_FINAL=PASS
- RULE_REFINED_BAD_COUNT=0
- RULE_VISIBLE_BAD_COUNT=0
- RULE_DISALLOWED_RAW_COUNT=0

## Hashes

- ACTIVE_INDEX_SHA=6983f94e7a5a2465bfe914adfa7b148d3de31b58b6efa2ce95b5e9e182eb9691
- ACTIVE_DATA_SHA=a0a4e45466000bd7358b471a6724797216321a5cf8af6e062a0bb2976b13b253
- SOURCE_INDEX_SHA=6983f94e7a5a2465bfe914adfa7b148d3de31b58b6efa2ce95b5e9e182eb9691
- SOURCE_DATA_SHA=a0a4e45466000bd7358b471a6724797216321a5cf8af6e062a0bb2976b13b253
- DB_SHA_NOW=3c6e1aafba1914a3e9bb30598980fde0d0891d25838c5b3d823ec4218ad4ff26

## Evidence

- APPLY_JSON=/root/tokenoskobi_clean_v1/data/active_8096_production_v2_control_center_apply_real_after_explicit_approval.json
- APPLY_REPORT=/root/tokenoskobi_clean_v1/reports/LATEST_ACTIVE_8096_PRODUCTION_V2_CONTROL_CENTER_APPLY_REAL_AFTER_EXPLICIT_APPROVAL.md
- RULE_JSON=/root/tokenoskobi_clean_v1/data/active_8096_production_v2_post_audit_rule_recheck_noapi.json
- RULE_REPORT=/root/tokenoskobi_clean_v1/reports/LATEST_ACTIVE_8096_PRODUCTION_V2_POST_AUDIT_RULE_RECHECK_NOAPI.md
- ROLLBACK_SCRIPT=/root/tokenoskobi_clean_v1/backups/ACTIVE_8096_PRODUCTION_V2_CONTROL_CENTER_APPLY_REAL_AFTER_EXPLICIT_APPROVAL_20260521_093232/ROLLBACK_ACTIVE_8096_PRODUCTION_V2_CONTROL_CENTER_APPLY_REAL_AFTER_EXPLICIT_APPROVAL.sh

## Domain assets reserved for later

- www.coinoskobi.com
- www.coinoskobi.xyz

No DNS/Nginx/SSL change in this phase.

## Safety

- NOAPI=true
- Active panel mutation=false
- DB mutation=false
- Service restart=false
- DNS/Nginx/SSL mutation=false
- Paper/live trade=false
- Source preview mutation=false
- Old preview delete=false
