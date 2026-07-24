#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

PAYLOAD="tools/.tokenoskobi_product_slice_01_payload_v1.zlib"
INNER="/tmp/tokenoskobi_product_slice_01_live_truth_verification_inner.sh"
EXPECTED_INNER_SHA256="f5a585781ddc8d2f9799d86b0db6f07c0c9e2704b37ee1d80e2e168ad7f3eae4"

[[ -f "$PAYLOAD" ]] || { echo "BLOCKED=PAYLOAD_MISSING:$PAYLOAD"; exit 1; }

python3 - <<'PY'
import base64
import hashlib
import zlib
from pathlib import Path

payload = Path('/root/tokenoskobi_clean_v1/tools/.tokenoskobi_product_slice_01_payload_v1.zlib')
inner = Path('/tmp/tokenoskobi_product_slice_01_live_truth_verification_inner.sh')
expected = 'f5a585781ddc8d2f9799d86b0db6f07c0c9e2704b37ee1d80e2e168ad7f3eae4'
raw = zlib.decompress(base64.b64decode(payload.read_text(encoding='utf-8').strip()))
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise SystemExit(f'BLOCKED=INNER_SHA256_MISMATCH:{actual}')
inner.write_bytes(raw)
inner.chmod(0o700)
print('PRODUCT_SLICE_01_PAYLOAD=VERIFIED')
PY

bash "$INNER"
rm -f "$INNER"
