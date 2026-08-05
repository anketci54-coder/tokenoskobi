#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

SOURCE="tools/tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix4.sh"
SELF="tools/tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix5.sh"
TEMP="/tmp/tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix5_inner.sh"

[[ -f "$SOURCE" ]] || { echo "BLOCKED=FIX4_SOURCE_MISSING"; exit 1; }

python3 - <<'PY'
from pathlib import Path

source=Path('/root/tokenoskobi_clean_v1/tools/tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix4.sh')
target=Path('/tmp/tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix5_inner.sh')
text=source.read_text(encoding='utf-8')

old_name='tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix4.sh'
new_name='tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix5.sh'
if old_name not in text:
    raise SystemExit('BLOCKED=FIX5_RUNNER_NAME_PATCH_TARGET_MISSING')
text=text.replace(old_name,new_name)

label="'FIX4_REPORT_POLICY'"
pos=text.find(label)
if pos < 0:
    raise SystemExit('BLOCKED=FIX5_REPORT_POLICY_LABEL_MISSING')
start=text.rfind('text=rep(',0,pos)
end=text.find('\n)',pos)
if start < 0 or end < 0:
    raise SystemExit('BLOCKED=FIX5_REPORT_POLICY_BLOCK_BOUNDARY_MISSING')
end += 2
replacement=r'''text=rep(
 "- NEWS fresh: `{n['fresh']}`\\n- Authority: `DISABLED / 0`\\n- Next: `{a['next_safe_step']}`\\n",
 "- NEWS fresh: `{n['fresh']}`\\n- Tokenoskobi.com: `PRIVATE_NOT_PUBLIC`\\n- Main website mutation: `NONE`\\n- Authority: `DISABLED / 0`\\n- Next: `{a['next_safe_step']}`\\n",
 'FIX5_REPORT_POLICY',
)'''
text=text[:start]+replacement+text[end:]

needle='''  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix3.sh \\
  "$RUNNER"'''
insert='''  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix3.sh \\
  tools/tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix4.sh \\
  "$RUNNER"'''
count=text.count(needle)
if count != 2:
    raise SystemExit(f'BLOCKED=FIX5_FIX4_CLEANUP_PATCH_COUNT:{count}')
text=text.replace(needle,insert)

text=text.replace('FIX4_', 'FIX5_')
target.write_text(text,encoding='utf-8')
target.chmod(0o700)
print('PRODUCT_SLICE_02_FIX5=PREPARED')
print('FIX5_REPORT_PATCH=CORRECTED')
print('TOKENOSKOBI_COM_POLICY=PRIVATE_NOT_PUBLIC_UNTIL_EXPLICIT_USER_APPROVAL')
PY

bash -n "$TEMP"
bash "$TEMP"
rm -f "$TEMP"
