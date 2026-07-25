#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

SOURCE="tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh"
FIX2="tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix2.sh"
SELF="tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix3.sh"
TEMP_SOURCE="/tmp/tokenoskobi_product_slice_02_external_500_recover_source.sh"
TEMP="/tmp/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix3_inner.sh"

[[ "$(git branch --show-current)" == main ]]
git fetch origin main --quiet
git show "origin/main:$SOURCE" > "$TEMP_SOURCE"
cp "$TEMP_SOURCE" "$SOURCE"
chmod 0755 "$SOURCE"

python3 - <<'PY'
from pathlib import Path
source=Path('/tmp/tokenoskobi_product_slice_02_external_500_recover_source.sh')
target=Path('/tmp/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix3_inner.sh')
text=source.read_text(encoding='utf-8')

text=text.replace(
    'SELF=tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh',
    'SELF=tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix3.sh',
    1,
)

old='''[[ -n "$NGINX_SITE" && -f "$NGINX_SITE" ]]
[[ -f "$REPO_NGINX" ]]
[[ -f config/product_slice_02_v1.json ]]
'''
new='''[[ -n "$NGINX_SITE" && -f "$NGINX_SITE" ]]
[[ -f config/product_slice_02_v1.json ]]
'''
if old not in text:
    raise SystemExit('BLOCKED=FIX3_PRECHECK_PATCH_TARGET_MISSING')
text=text.replace(old,new,1)

old='''cp -a "$NGINX_SITE" "$BACKUP_DIR/nginx_site.conf"
echo BACKUP="$BACKUP_DIR"

python3 - "$NGINX_SITE" "$REPO_NGINX" <<'PY'
'''
new='''cp -a "$NGINX_SITE" "$BACKUP_DIR/nginx_site.conf"
mkdir -p "$(dirname "$REPO_NGINX")"
cp -a "$NGINX_SITE" "$REPO_NGINX"
echo BACKUP="$BACKUP_DIR"
echo MAIN_WEBSITE_POLICY=TOKENOSKOBI_COM_PRIVATE_NOT_PUBLIC
echo MAIN_WEBSITE_MUTATION=NONE
echo STAGING_SCOPE=ONLY_PANEL_COINOSKOBI_XYZ

python3 - "$NGINX_SITE" "$REPO_NGINX" <<'PY'
'''
if old not in text:
    raise SystemExit('BLOCKED=FIX3_REPO_NGINX_COPY_PATCH_TARGET_MISSING')
text=text.replace(old,new,1)

old=""" 'next_safe_step':'PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING',
}
(root/'data/control/product_slice_02_single_token_decision_packet_v1.json')"""
new=""" 'next_safe_step':'PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING',
 'exposure_policy':{
   'tokenoskobi.com':'PRIVATE_NOT_PUBLIC_UNTIL_EXPLICIT_USER_APPROVAL',
   'main_website_mutation':False,
   'staging_panel_domain':'panel.coinoskobi.xyz',
   'staging_panel_scope':'CONTROLLED_TEST_PANEL_ONLY',
 },
}
(root/'data/control/product_slice_02_single_token_decision_packet_v1.json')"""
if old not in text:
    raise SystemExit('BLOCKED=FIX3_EXPOSURE_POLICY_PATCH_TARGET_MISSING')
text=text.replace(old,new,1)

old=""" f\"- NEWS fresh: `{n['fresh']}`\\n- Authority: `DISABLED / 0`\\n- Next: `{a['next_safe_step']}`\\n\"
"""
new=""" f\"- NEWS fresh: `{n['fresh']}`\\n- Tokenoskobi.com: `PRIVATE_NOT_PUBLIC`\\n- Main website mutation: `NONE`\\n- Authority: `DISABLED / 0`\\n- Next: `{a['next_safe_step']}`\\n\"
"""
if old not in text:
    raise SystemExit('BLOCKED=FIX3_REPORT_POLICY_PATCH_TARGET_MISSING')
text=text.replace(old,new,1)

old="""- NEWS fresh: `{n['fresh']}`
- Authority: `PAPER_DISABLED; LIVE_DISABLED; REAL_FINANCIAL_AUTHORITY_0`
"""
new="""- NEWS fresh: `{n['fresh']}`
- Tokenoskobi.com: `PRIVATE_NOT_PUBLIC`
- Main website mutation: `NONE`
- Authority: `PAPER_DISABLED; LIVE_DISABLED; REAL_FINANCIAL_AUTHORITY_0`
"""
if old not in text:
    raise SystemExit('BLOCKED=FIX3_CANONICAL_POLICY_PATCH_TARGET_MISSING')
text=text.replace(old,new,1)

old="""assert a['visible_product']['external_http_code']=='200' and a['visible_product']['external_api_http_code']=='200'
assert x['authority_change'] is False
"""
new="""assert a['visible_product']['external_http_code']=='200' and a['visible_product']['external_api_http_code']=='200'
assert a['exposure_policy']['tokenoskobi.com']=='PRIVATE_NOT_PUBLIC_UNTIL_EXPLICIT_USER_APPROVAL'
assert a['exposure_policy']['main_website_mutation'] is False
assert x['authority_change'] is False
"""
if old not in text:
    raise SystemExit('BLOCKED=FIX3_VALIDATION_POLICY_PATCH_TARGET_MISSING')
text=text.replace(old,new,1)

old='''  tools/tokenoskobi_product_slice_02_external_500_diagnose.sh \\
  "$SELF"
'''
new='''  tools/tokenoskobi_product_slice_02_external_500_diagnose.sh \\
  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh \\
  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix2.sh \\
  "$SELF"
'''
if text.count(old) != 2:
    raise SystemExit(f'BLOCKED=FIX3_CLEANUP_PATCH_TARGET_COUNT:{text.count(old)}')
text=text.replace(old,new)

old="""print('REAL_FINANCIAL_AUTHORITY=0')
print('NEXT_SAFE_STEP='+a['next_safe_step'])
"""
new="""print('REAL_FINANCIAL_AUTHORITY=0')
print('TOKENOSKOBI_COM=PRIVATE_NOT_PUBLIC')
print('MAIN_WEBSITE_MUTATION=NONE')
print('NEXT_SAFE_STEP='+a['next_safe_step'])
"""
if old not in text:
    raise SystemExit('BLOCKED=FIX3_FINAL_OUTPUT_PATCH_TARGET_MISSING')
text=text.replace(old,new,1)

target.write_text(text,encoding='utf-8')
target.chmod(0o700)
print('PRODUCT_SLICE_02_FIX3=PREPARED')
print('SOURCE=RESTORED_FROM_ORIGIN_MAIN')
print('TOKENOSKOBI_COM_POLICY=PRIVATE_NOT_PUBLIC')
PY

bash -n "$TEMP"
bash "$TEMP"
rm -f "$TEMP" "$TEMP_SOURCE"
