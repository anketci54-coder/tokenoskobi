#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

SOURCE="tools/tokenoskobi_product_slice_02_single_token_deploy.sh"
SELF="tools/tokenoskobi_product_slice_02_single_token_deploy_fix1.sh"
TEMP="/tmp/tokenoskobi_product_slice_02_single_token_deploy_fix1_inner.sh"

[[ -f "$SOURCE" ]] || { echo "BLOCKED=SLICE_02_SOURCE_RUNNER_MISSING"; exit 1; }

python3 - <<'PY'
from pathlib import Path
source = Path('/root/tokenoskobi_clean_v1/tools/tokenoskobi_product_slice_02_single_token_deploy.sh')
target = Path('/tmp/tokenoskobi_product_slice_02_single_token_deploy_fix1_inner.sh')
text = source.read_text(encoding='utf-8')
text = text.replace(
    'RUNNER="tools/tokenoskobi_product_slice_02_single_token_deploy.sh"',
    'RUNNER="tools/tokenoskobi_product_slice_02_single_token_deploy_fix1.sh"'
)
text = text.replace(
    'FILES=(\n',
    'FILES=(\n  tools/tokenoskobi_product_slice_02_single_token_deploy.sh\n',
    1
)
old = 'rm -f tools/.tokenoskobi_product_slice_02_deploy_payload.zlib "$RUNNER"\n'
new = 'rm -f tools/.tokenoskobi_product_slice_02_deploy_payload.zlib "$RUNNER" tools/tokenoskobi_product_slice_02_single_token_deploy.sh\n'
if old not in text:
    raise SystemExit('BLOCKED=CLEANUP_PATCH_TARGET_MISSING')
text = text.replace(old, new, 1)
old = 'git add -A tools/.tokenoskobi_product_slice_02_deploy_payload.zlib "$RUNNER"\n'
new = '''git add -u -- "$RUNNER" tools/tokenoskobi_product_slice_02_single_token_deploy.sh
if git ls-files --error-unmatch tools/.tokenoskobi_product_slice_02_deploy_payload.zlib >/dev/null 2>&1; then
  git add -u -- tools/.tokenoskobi_product_slice_02_deploy_payload.zlib
fi
'''
if old not in text:
    raise SystemExit('BLOCKED=GIT_STAGE_PATCH_TARGET_MISSING')
text = text.replace(old, new, 1)
target.write_text(text, encoding='utf-8')
target.chmod(0o700)
print('PRODUCT_SLICE_02_FIX1=PREPARED')
PY

bash -n "$TEMP"
bash "$TEMP"
rm -f "$TEMP"
