#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

PAYLOAD="tools/.tokenoskobi_product_slice_01_payload_v1.zlib"
INNER="/tmp/tokenoskobi_product_slice_01_live_truth_verification_fix1_inner.sh"
EXPECTED_ORIGINAL_SHA256="f5a585781ddc8d2f9799d86b0db6f07c0c9e2704b37ee1d80e2e168ad7f3eae4"

[[ -f "$PAYLOAD" ]] || { echo "BLOCKED=PAYLOAD_MISSING:$PAYLOAD"; exit 1; }

python3 <<'PY'
from __future__ import annotations

import base64
import hashlib
import re
import zlib
from pathlib import Path

payload = Path('/root/tokenoskobi_clean_v1/tools/.tokenoskobi_product_slice_01_payload_v1.zlib')
inner = Path('/tmp/tokenoskobi_product_slice_01_live_truth_verification_fix1_inner.sh')
expected = 'f5a585781ddc8d2f9799d86b0db6f07c0c9e2704b37ee1d80e2e168ad7f3eae4'
raw = zlib.decompress(base64.b64decode(payload.read_text(encoding='utf-8').strip()))
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise SystemExit(f'BLOCKED=ORIGINAL_INNER_SHA256_MISMATCH:{actual}')

text = raw.decode('utf-8')
lines = []
patched = 0
for line in text.splitlines():
    if re.match(r'^\s*git add(?!\s+-f\b)', line):
        line = re.sub(r'git add', 'git add -f', line, count=1)
        patched += 1
    lines.append(line)

if patched < 1:
    raise SystemExit('BLOCKED=NO_GIT_ADD_LINE_PATCHED')

patched_text = '\n'.join(lines) + '\n'
inner.write_text(patched_text, encoding='utf-8')
inner.chmod(0o700)
print('PRODUCT_SLICE_01_ORIGINAL_PAYLOAD=VERIFIED')
print(f'PRODUCT_SLICE_01_GIT_ADD_FORCE_PATCH_COUNT={patched}')
PY

bash "$INNER"
rm -f "$INNER"
