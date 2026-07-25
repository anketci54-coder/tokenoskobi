#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

PAYLOAD="tools/.tokenoskobi_product_slice_01_payload_v1.zlib"
INNER="/tmp/tokenoskobi_product_slice_01_live_truth_verification_inner.sh"
EXPECTED_ORIGINAL_SHA256="f5a585781ddc8d2f9799d86b0db6f07c0c9e2704b37ee1d80e2e168ad7f3eae4"

# A failed inner-run rollback can remove the tracked payload from the working tree.
# Restore the exact payload from origin/main before validating it.
if [[ ! -f "$PAYLOAD" ]]; then
  git show "origin/main:$PAYLOAD" > "$PAYLOAD"
  echo "PRODUCT_SLICE_01_PAYLOAD=RESTORED_FROM_ORIGIN_MAIN"
fi

[[ -s "$PAYLOAD" ]] || { echo "BLOCKED=PAYLOAD_MISSING_OR_EMPTY:$PAYLOAD"; exit 1; }

python3 <<'PY'
import base64
import hashlib
import re
import zlib
from pathlib import Path

payload = Path('/root/tokenoskobi_clean_v1/tools/.tokenoskobi_product_slice_01_payload_v1.zlib')
inner = Path('/tmp/tokenoskobi_product_slice_01_live_truth_verification_inner.sh')
expected = 'f5a585781ddc8d2f9799d86b0db6f07c0c9e2704b37ee1d80e2e168ad7f3eae4'
raw = zlib.decompress(base64.b64decode(payload.read_text(encoding='utf-8').strip()))
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise SystemExit(f'BLOCKED=ORIGINAL_INNER_SHA256_MISMATCH:{actual}')
text = raw.decode('utf-8')
patched, count = re.subn(r'(?m)^(\s*)git add(\s+)', r'\1git add -f\2', text)
if count < 1:
    raise SystemExit('BLOCKED=GIT_ADD_PATCH_TARGET_NOT_FOUND')
inner.write_text(patched, encoding='utf-8')
inner.chmod(0o700)
print('PRODUCT_SLICE_01_PAYLOAD=VERIFIED')
print(f'PRODUCT_SLICE_01_IGNORED_REPORT_FIX=APPLIED:{count}')
PY

bash "$INNER"
rm -f "$INNER"
