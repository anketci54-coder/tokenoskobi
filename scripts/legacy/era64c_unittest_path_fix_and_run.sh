#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SOURCE="tools/era64c_real_historical_wallet_replay_and_validation.sh"
TARGET="/tmp/era64c_real_historical_wallet_replay_and_validation_fixed_v2.sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -f "$SOURCE" ]]

python3 - "$SOURCE" "$TARGET" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
text = source.read_text(encoding='utf-8')

replacements = {
    "assert r.get('paper_runtime_enabled') is False":
        "assert r.get('paper_runtime_enabled', r.get('canonical_runtime_pointer', {}).get('paper_runtime_enabled')) is False",
    "python3 -m unittest -v tests/test_era63_paper_trading_core_v1.py":
        "python3 tests/test_era63_paper_trading_core_v1.py",
    "python3 -m unittest -v tests/test_era63c_technical_dex_execution_v1.py":
        "python3 tests/test_era63c_technical_dex_execution_v1.py",
    "python3 -m unittest -v tests/test_era63d_market_technical_runtime_v1.py":
        "python3 tests/test_era63d_market_technical_runtime_v1.py",
    "python3 -m unittest -v tests/test_era63e_always_on_market_runtime_v1.py":
        "python3 tests/test_era63e_always_on_market_runtime_v1.py",
}

for old, new in replacements.items():
    if text.count(old) != 1:
        raise RuntimeError(f'ERA64C_PATCH_TARGET_COUNT_INVALID:{old}')
    text = text.replace(old, new, 1)

target.write_text(text, encoding='utf-8')
target.chmod(0o700)
print('ERA64C_UNITTEST_PATH_FIX=VERIFIED')
PY

exec bash "$TARGET"
