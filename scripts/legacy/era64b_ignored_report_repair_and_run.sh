#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

SOURCE="tools/era64b_direct_foundation_rebuild.sh"
TARGET="/tmp/era64b_direct_foundation_rebuild_fixed.sh"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -f "$SOURCE" ]]

python3 <<'PY'
from pathlib import Path

source = Path('/root/tokenoskobi_clean_v1/tools/era64b_direct_foundation_rebuild.sh')
target = Path('/tmp/era64b_direct_foundation_rebuild_fixed.sh')
text = source.read_text(encoding='utf-8')
needle = '''CANONICAL_FILES=(
  PROJECT_RUNTIME.json
  PROJECT_HISTORY.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
  03_ROADMAP.md
  04_ALMANAC.md
  06_PROJECT_MASTER_STATE.md
  07_PROJECT_HANDOFF.md
  reports/LATEST_TK_AI_HANDOFF.md
)'''
replacement = '''CANONICAL_FILES=(
  PROJECT_RUNTIME.json
  PROJECT_HISTORY.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
  03_ROADMAP.md
  04_ALMANAC.md
  06_PROJECT_MASTER_STATE.md
  07_PROJECT_HANDOFF.md
)'''
if text.count(needle) != 1:
    raise RuntimeError('ERA64B_CANONICAL_FILES_BLOCK_MISMATCH')
text = text.replace(needle, replacement, 1)
force_line = 'git add -f -- reports/LATEST_ERA64B_SUCCESSFUL_WALLET_FOUNDATION.md reports/LATEST_TK_AI_HANDOFF.md'
if force_line not in text:
    raise RuntimeError('ERA64B_FORCE_ADD_LINE_MISSING')
target.write_text(text, encoding='utf-8')
target.chmod(0o700)
print('ERA64B_IGNORED_REPORT_REPAIR=VERIFIED')
PY

exec bash "$TARGET"
