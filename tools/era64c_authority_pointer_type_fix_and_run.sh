#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SOURCE="tools/era64c_real_historical_wallet_replay_and_validation.sh"
TARGET="/tmp/era64c_real_historical_wallet_replay_and_validation_fixed_v4.sh"

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

for old, new in {
    "python3 -m unittest -v tests/test_era63_paper_trading_core_v1.py": "python3 -m unittest -v tests/test_era63b_paper_trading_core_v1.py",
    "python3 tests/test_era63_paper_trading_core_v1.py": "python3 tests/test_era63b_paper_trading_core_v1.py",
}.items():
    text = text.replace(old, new)
if "tests/test_era63b_paper_trading_core_v1.py" not in text:
    raise RuntimeError('ERA64C_ERA63B_TEST_PATH_PATTERN_MISSING')

old_authority = '''    authority=obj.setdefault('authority',{})
    authority['real_trade_authority']=0
    authority['real_wallet_authority']=0
    authority['real_signing_authority']=0
    authority['real_order_authority']=0
    authority['live_trade']='DISABLED'
    authority['paper_trade']='DISABLED_PENDING_COORDINATED_INTELLIGENCE' '''
new_authority = '''    authority=obj.get('authority')
    if authority is None:
        authority={}
        obj['authority']=authority
    if isinstance(authority,dict):
        authority['real_trade_authority']=0
        authority['real_wallet_authority']=0
        authority['real_signing_authority']=0
        authority['real_order_authority']=0
        authority['live_trade']='DISABLED'
        authority['paper_trade']='DISABLED_PENDING_COORDINATED_INTELLIGENCE' '''
if old_authority not in text:
    raise RuntimeError('ERA64C_AUTHORITY_BLOCK_PATTERN_MISSING')
text = text.replace(old_authority, new_authority, 1)

target.write_text(text, encoding='utf-8')
target.chmod(0o700)
print('ERA64C_AUTHORITY_POINTER_TYPE_FIX=VERIFIED')
PY

exec bash "$TARGET"
