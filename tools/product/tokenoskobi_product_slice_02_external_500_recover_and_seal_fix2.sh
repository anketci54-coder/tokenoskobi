#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

SOURCE="tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh"
SELF="tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix2.sh"
TEMP="/tmp/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix2_inner.sh"

[[ -f "$SOURCE" ]] || { echo "BLOCKED=SLICE_02_RECOVERY_SOURCE_MISSING"; exit 1; }

python3 - <<'PY'
from pathlib import Path
source=Path('/root/tokenoskobi_clean_v1/tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh')
target=Path('/tmp/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix2_inner.sh')
text=source.read_text(encoding='utf-8')

text=text.replace(
    'SELF=tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh',
    'SELF=tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix2.sh',
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
    raise SystemExit('BLOCKED=FIX2_PRECHECK_PATCH_TARGET_MISSING')
text=text.replace(old,new,1)

old='''cp -a "$NGINX_SITE" "$BACKUP_DIR/nginx_site.conf"
echo BACKUP="$BACKUP_DIR"

python3 - "$NGINX_SITE" "$REPO_NGINX" <<'PY'
'''
new='''cp -a "$NGINX_SITE" "$BACKUP_DIR/nginx_site.conf"
mkdir -p "$(dirname "$REPO_NGINX")"
cp -a "$NGINX_SITE" "$REPO_NGINX"
echo BACKUP="$BACKUP_DIR"
echo WEBSITE_PRESERVATION=COINOSKOBI_COM_WWW_AND_DNS_UNTOUCHED
echo STAGING_SCOPE=ONLY_PANEL_COINOSKOBI_XYZ

python3 - "$NGINX_SITE" "$REPO_NGINX" <<'PY'
'''
if old not in text:
    raise SystemExit('BLOCKED=FIX2_REPO_NGINX_COPY_PATCH_TARGET_MISSING')
text=text.replace(old,new,1)

old='''  tools/tokenoskobi_product_slice_02_external_500_diagnose.sh \\
  "$SELF"
'''
new='''  tools/tokenoskobi_product_slice_02_external_500_diagnose.sh \\
  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh \\
  "$SELF"
'''
if text.count(old) != 2:
    raise SystemExit(f'BLOCKED=FIX2_CLEANUP_PATCH_TARGET_COUNT:{text.count(old)}')
text=text.replace(old,new)

target.write_text(text,encoding='utf-8')
target.chmod(0o700)
print('PRODUCT_SLICE_02_FIX2=PREPARED')
print('WEBSITE_SCOPE_LOCK=VERIFIED')
PY

bash -n "$TEMP"
bash "$TEMP"
rm -f "$TEMP"
