#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1
PAYLOAD_DIR="tools/.tokenoskobi_product_vertical_slice_payload_v1"

python3 <<'PY'
from pathlib import Path
import base64
import os
import zlib

root=Path('/root/tokenoskobi_clean_v1')
payload_dir=root/'tools/.tokenoskobi_product_vertical_slice_payload_v1'
mapping={
    'inner':Path('/tmp/tokenoskobi_product_vertical_slice_inner_v1.zlib'),
    'server':Path('/tmp/tokenoskobi_product_server_v1.zlib'),
    'index':Path('/tmp/tokenoskobi_product_index_v1.zlib'),
    'test':Path('/tmp/tokenoskobi_product_test_v1.zlib'),
}
for name,target in mapping.items():
    parts=sorted(payload_dir.glob(name+'.*'))
    if not parts:
        raise SystemExit('PAYLOAD_PARTS_MISSING:'+name)
    encoded=''.join(part.read_text(encoding='ascii').strip() for part in parts)
    target.write_bytes(base64.b64decode(encoded,validate=True))
inner=Path('/tmp/tokenoskobi_product_vertical_slice_inner_v1.sh')
inner.write_bytes(zlib.decompress(mapping['inner'].read_bytes()))
os.chmod(inner,0o700)
print('PRODUCT_BOOTSTRAP_PAYLOADS=VERIFIED')
PY

exec bash /tmp/tokenoskobi_product_vertical_slice_inner_v1.sh
