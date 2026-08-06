#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SOURCE="tools/era64c_real_historical_wallet_replay_and_validation.sh"
TARGET="/tmp/era64c_real_historical_wallet_replay_and_validation_fixed2.sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -f "$SOURCE" ]]
[[ -f tests/test_era63b_paper_trading_core_v1.py ]]

python3 - "$SOURCE" "$TARGET" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
text = source.read_text(encoding='utf-8')
old = "python3 -m unittest -v tests/test_era63_paper_trading_core_v1.py"
new = "python3 -m unittest -v tests/test_era63b_paper_trading_core_v1.py"
if text.count(old) != 1:
    raise RuntimeError('ERA64C_ERA63_TEST_PATH_PATTERN_MISMATCH')
target.write_text(text.replace(old, new, 1), encoding='utf-8')
target.chmod(0o700)
print('ERA64C_MISSING_TEST_PATH_REPAIR=VERIFIED')
PY

exec bash "$TARGET"
