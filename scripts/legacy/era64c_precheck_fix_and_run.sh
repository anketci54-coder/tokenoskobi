#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1
SOURCE=tools/era64c_real_historical_wallet_replay_and_validation.sh
TARGET=/tmp/era64c_real_historical_wallet_replay_and_validation_fixed.sh
[[ "$(git branch --show-current)" == main ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
cp "$SOURCE" "$TARGET"
python3 - "$TARGET" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')
a="assert r.get('paper_runtime_enabled') is False"
b="assert r.get('paper_runtime_enabled', r.get('canonical_runtime_pointer', {}).get('paper_runtime_enabled')) is False"
assert s.count(a)==1
p.write_text(s.replace(a,b,1),encoding='utf-8')
PY
chmod 700 "$TARGET"
echo ERA64C_PRECHECK_FIX=VERIFIED
bash "$TARGET"
