#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

OBS_SERVICE="tokenoskobi-era63e-always-on-market.service"
TIMER="tokenoskobi-era63d-market-technical.timer"
TMP_SCRIPT=""

cleanup_tmp() {
  [[ -n "$TMP_SCRIPT" && -f "$TMP_SCRIPT" ]] && rm -f "$TMP_SCRIPT"
}
trap cleanup_tmp EXIT

fail() {
  echo "ERA63E_DIRTY_CLOSURE_RECOVERY=FAILED"
  echo "REASON=$1"
  exit 1
}

[[ "$(git branch --show-current)" == "main" ]] || fail "BRANCH_NOT_MAIN"
git fetch origin main --quiet
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git rev-parse origin/main)"
echo "LOCAL_HEAD=$LOCAL_HEAD"
echo "REMOTE_HEAD=$REMOTE_HEAD"
[[ "$LOCAL_HEAD" == "$REMOTE_HEAD" ]] || fail "LOCAL_REMOTE_HEAD_MISMATCH"

BACKUP_DIR="/root/era63e_dirty_closure_recovery_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"
git status --porcelain=v1 > "$BACKUP_DIR/status.txt"
git diff --binary > "$BACKUP_DIR/worktree.patch" || true
git diff --cached --binary > "$BACKUP_DIR/index.patch" || true

python3 <<'PY_VERIFY_DIRTY'
from __future__ import annotations
import subprocess
from pathlib import Path

root = Path('/root/tokenoskobi_clean_v1')
allowed = {
    '03_ROADMAP.md',
    '04_ALMANAC.md',
    '05_ATLAS.md',
    '06_PROJECT_MASTER_STATE.md',
    '07_PROJECT_HANDOFF.md',
    'PROJECT_HISTORY.json',
    'PROJECT_RUNTIME.json',
    'data/control/era63e_continuous_observation_and_technical_closure_v1.json',
    'data/control/latest_tk_machine_state.json',
    'data/tokenoskobi_v1_v8_master_era_roadmap.json',
    'reports/LATEST_ERA63E_CONTINUOUS_OBSERVATION_AND_TECHNICAL_CLOSURE.md',
    'reports/LATEST_TK_AI_HANDOFF.md',
}
raw = subprocess.check_output(
    ['git', 'status', '--porcelain=v1', '-z'], cwd=root
)
entries = [item for item in raw.decode('utf-8', errors='strict').split('\0') if item]
paths = set()
for entry in entries:
    if len(entry) < 4:
        raise SystemExit(f'INVALID_STATUS_ENTRY:{entry!r}')
    path = entry[3:]
    if ' -> ' in path:
        path = path.split(' -> ', 1)[1]
    paths.add(path)
unexpected = sorted(paths - allowed)
if unexpected:
    print('UNEXPECTED_DIRTY_PATHS=' + ','.join(unexpected))
    raise SystemExit(2)
print('DIRTY_PATH_COUNT=' + str(len(paths)))
print('DIRTY_PATHS=' + (','.join(sorted(paths)) if paths else 'NONE'))
PY_VERIFY_DIRTY

echo "RECOVERY_BACKUP=$BACKUP_DIR"

if [[ -n "$(git status --porcelain=v1)" ]]; then
  git reset --hard HEAD
  rm -f -- \
    data/control/era63e_continuous_observation_and_technical_closure_v1.json \
    reports/LATEST_ERA63E_CONTINUOUS_OBSERVATION_AND_TECHNICAL_CLOSURE.md
fi

[[ -z "$(git status --porcelain=v1)" ]] || fail "WORKTREE_NOT_CLEAN_AFTER_SAFE_RESET"
echo "STALE_PARTIAL_CLOSURE=REMOVED"
echo "WORKTREE=CLEAN"

systemctl is-enabled --quiet "$OBS_SERVICE" || fail "OBSERVATION_SERVICE_NOT_ENABLED"
systemctl is-active --quiet "$OBS_SERVICE" || fail "OBSERVATION_SERVICE_NOT_ACTIVE"
! systemctl is-active --quiet "$TIMER" || fail "FIXED_TIMER_ACTIVE"

python3 <<'PY_AUTHORITY'
import json
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
runtime = json.loads((root / 'PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert runtime['next_safe_step'] == 'ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE'
assert runtime['authority']['live_trade'] == 'DISABLED'
assert runtime['authority']['real_wallet_authority'] == 0
assert runtime['authority']['real_signing_authority'] == 0
assert runtime['authority']['real_order_authority'] == 0
print('AUTHORITY_BOUNDARY=VERIFIED_READ_ONLY')
PY_AUTHORITY

TMP_SCRIPT="$(mktemp /tmp/era63e_observe_close_repaired.XXXXXX.sh)"
cp tools/era63e_observe_close.sh "$TMP_SCRIPT"

python3 - "$TMP_SCRIPT" <<'PY_PATCH'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
marker = '\ngit add -- \\\n'
if text.count(marker) != 1:
    raise SystemExit('PATCH_MARKER_COUNT_INVALID')
normalizer = r'''
python3 <<'PY_NORMALIZE_MARKDOWN'
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
for rel in (
    '03_ROADMAP.md',
    '04_ALMANAC.md',
    '05_ATLAS.md',
    '06_PROJECT_MASTER_STATE.md',
    '07_PROJECT_HANDOFF.md',
    'reports/LATEST_ERA63E_CONTINUOUS_OBSERVATION_AND_TECHNICAL_CLOSURE.md',
    'reports/LATEST_TK_AI_HANDOFF.md',
):
    target = root / rel
    lines = target.read_text(encoding='utf-8').splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    target.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('MARKDOWN_EOF_NORMALIZATION=PASS')
PY_NORMALIZE_MARKDOWN
'''
text = text.replace(marker, '\n' + normalizer + marker, 1)
path.write_text(text, encoding='utf-8')
PY_PATCH
chmod 0700 "$TMP_SCRIPT"

echo "CLOSURE_RETRY=STARTED"
set +e
bash "$TMP_SCRIPT"
RC=$?
set -e

if [[ "$RC" -ne 0 ]]; then
  echo "CLOSURE_RETRY=FAILED_RC_$RC"
  python3 <<'PY_VERIFY_FAILURE_DIRTY'
from __future__ import annotations
import subprocess
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
allowed = {
    '03_ROADMAP.md','04_ALMANAC.md','05_ATLAS.md','06_PROJECT_MASTER_STATE.md','07_PROJECT_HANDOFF.md',
    'PROJECT_HISTORY.json','PROJECT_RUNTIME.json',
    'data/control/era63e_continuous_observation_and_technical_closure_v1.json',
    'data/control/latest_tk_machine_state.json','data/tokenoskobi_v1_v8_master_era_roadmap.json',
    'reports/LATEST_ERA63E_CONTINUOUS_OBSERVATION_AND_TECHNICAL_CLOSURE.md','reports/LATEST_TK_AI_HANDOFF.md',
}
raw = subprocess.check_output(['git','status','--porcelain=v1','-z'], cwd=root)
entries = [x for x in raw.decode().split('\0') if x]
paths = {e[3:].split(' -> ',1)[-1] for e in entries}
unexpected = paths - allowed
if unexpected:
    print('UNEXPECTED_POST_FAILURE_DIRTY=' + ','.join(sorted(unexpected)))
    raise SystemExit(2)
PY_VERIFY_FAILURE_DIRTY
  git reset --hard HEAD
  rm -f -- \
    data/control/era63e_continuous_observation_and_technical_closure_v1.json \
    reports/LATEST_ERA63E_CONTINUOUS_OBSERVATION_AND_TECHNICAL_CLOSURE.md
  [[ -z "$(git status --porcelain=v1)" ]] || fail "POST_FAILURE_CLEANUP_FAILED"
  echo "POST_FAILURE_WORKTREE=CLEAN"
  exit "$RC"
fi

NEXT_SAFE_STEP="$(python3 - <<'PY_NEXT'
import json
from pathlib import Path
v=json.loads(Path('/root/tokenoskobi_clean_v1/PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
print(v.get('next_safe_step'))
PY_NEXT
)"

echo "NEXT_SAFE_STEP=$NEXT_SAFE_STEP"
if [[ "$NEXT_SAFE_STEP" == "ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION" ]]; then
  git fetch origin main --quiet
  [[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || fail "POST_CLOSURE_REMOTE_MISMATCH"
  [[ -z "$(git status --porcelain=v1)" ]] || fail "POST_CLOSURE_WORKTREE_DIRTY"
  systemctl is-active --quiet "$OBS_SERVICE" || fail "OBSERVATION_SERVICE_LOST_AFTER_CLOSURE"
  ! systemctl is-active --quiet "$TIMER" || fail "FIXED_TIMER_REACTIVATED"
  echo "ERA63E_DIRTY_CLOSURE_RECOVERY=ERA63_CLOSED_VERIFIED_GITHUB_SEALED"
  echo "REMOTE_VERIFY=VERIFIED"
  echo "WORKTREE=CLEAN"
  echo "HEAD=$(git rev-parse HEAD)"
else
  [[ -z "$(git status --porcelain=v1)" ]] || fail "PENDING_RESULT_LEFT_DIRTY_WORKTREE"
  echo "ERA63E_DIRTY_CLOSURE_RECOVERY=OBSERVATION_PENDING_CLEAN"
  echo "HEAD=$(git rev-parse HEAD)"
fi
