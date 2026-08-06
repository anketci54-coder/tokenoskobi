#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SOURCE="tools/era64b_build_foundation.sh"
TARGET="/tmp/era64b_build_foundation_payload_fixed.sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -f "$SOURCE" ]]

python3 <<'PY'
from __future__ import annotations

import base64
import gzip
import os
import re
from pathlib import Path

root = Path('/root/tokenoskobi_clean_v1')
source = root / 'tools/era64b_build_foundation.sh'
target = Path('/tmp/era64b_build_foundation_payload_fixed.sh')
text = source.read_text(encoding='utf-8')
match = re.search(r'payload\s*=\s*"""(.*?)"""\.replace\("\\n",\s*""\)', text, re.S)
if match is None:
    raise RuntimeError('ERA64B_PAYLOAD_NOT_FOUND')

payload = ''.join(match.group(1).split())
payload += '=' * (-len(payload) % 4)
compressed = base64.b64decode(payload, validate=True)
script = gzip.decompress(compressed)
if not script.startswith((b'#!/usr/bin/env bash', b'#!/bin/bash')):
    raise RuntimeError('ERA64B_DECODED_PAYLOAD_NOT_SHELL')

target.write_bytes(script)
os.chmod(target, 0o700)
print('ERA64B_PADDING_REPAIR=VERIFIED')
print(f'ERA64B_DECODED_BYTES={len(script)}')
os.execv('/bin/bash', ['bash', str(target)])
PY
