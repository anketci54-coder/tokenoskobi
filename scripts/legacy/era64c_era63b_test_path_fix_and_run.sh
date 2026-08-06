#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SOURCE="tools/era64c_real_historical_wallet_replay_and_validation.sh"
TARGET="/tmp/era64c_real_historical_wallet_replay_and_validation_fixed_v3.sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -f "$SOURCE" ]]
[[ -f "tests/test_era63b_paper_trading_core_v1.py" ]]

python3 - "$SOURCE" "$TARGET" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
text = source.read_text(encoding='utf-8')

old_precheck = "assert r.get('paper_runtime_enabled') is False"
new_precheck = "assert r.get('paper_runtime_enabled', r.get('canonical_runtime_pointer', {}).get('paper_runtime_enabled')) is False"
if old_precheck in text:
    text = text.replace(old_precheck, new_precheck, 1)
elif new_precheck not in text:
    raise RuntimeError('ERA64C_PAPER_RUNTIME_PRECHECK_PATTERN_MISSING')

replacements = {
    "python3 -m unittest -v tests/test_era63_paper_trading_core_v1.py": "python3 -m unittest -v tests/test_era63b_paper_trading_core_v1.py",
    "python3 tests/test_era63_paper_trading_core_v1.py": "python3 tests/test_era63b_paper_trading_core_v1.py",
}
changed = False
for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new, 1)
        changed = True
if not changed and "tests/test_era63b_paper_trading_core_v1.py" not in text:
    raise RuntimeError('ERA64C_ERA63B_TEST_PATH_PATTERN_MISSING')

target.write_text(text, encoding='utf-8')
target.chmod(0o700)
print('ERA64C_ERA63B_TEST_PATH_FIX=VERIFIED')
PY

exec bash "$TARGET"
