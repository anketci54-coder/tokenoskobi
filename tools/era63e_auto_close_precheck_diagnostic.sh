#!/usr/bin/env bash
set -u

cd /root/tokenoskobi_clean_v1

BRANCH="$(git branch --show-current 2>/dev/null || true)"
STATUS="$(git status --porcelain=v1 2>/dev/null || true)"
LOCAL_HEAD="$(git rev-parse HEAD 2>/dev/null || true)"
git fetch origin main --quiet 2>/dev/null || true
REMOTE_HEAD="$(git rev-parse origin/main 2>/dev/null || true)"

check_state() {
  local unit="$1"
  local active enabled
  active="$(systemctl is-active "$unit" 2>/dev/null || true)"
  enabled="$(systemctl is-enabled "$unit" 2>/dev/null || true)"
  printf '%s_ACTIVE=%s\n' "${unit//[-.]/_}" "$active"
  printf '%s_ENABLED=%s\n' "${unit//[-.]/_}" "$enabled"
}

echo "DIAGNOSTIC=ERA63E_AUTO_CLOSE_PRECHECK"
echo "BRANCH=$BRANCH"
echo "LOCAL_HEAD=$LOCAL_HEAD"
echo "REMOTE_HEAD=$REMOTE_HEAD"
if [[ -z "$STATUS" ]]; then
  echo "WORKTREE=CLEAN"
else
  echo "WORKTREE=DIRTY"
  git status --short
fi

check_state tokenoskobi-era63e-always-on-market.service
check_state tokenoskobi-era63d-market-technical.timer
check_state tokenoskobi-era63e-auto-close.service
check_state tokenoskobi-era63e-auto-close-v2.service

if [[ -f /root/era63e_auto_close.log ]]; then
  echo "AUTO_CLOSE_LOG=FOUND"
  tail -n 80 /root/era63e_auto_close.log
else
  echo "AUTO_CLOSE_LOG=NOT_FOUND"
fi

echo "NEW_UNIT_STATUS_BEGIN"
systemctl status tokenoskobi-era63e-auto-close-v2.service --no-pager -l 2>&1 || true
echo "NEW_UNIT_STATUS_END"

echo "NEW_UNIT_JOURNAL_BEGIN"
journalctl -u tokenoskobi-era63e-auto-close-v2.service -n 80 --no-pager 2>&1 || true
echo "NEW_UNIT_JOURNAL_END"

python3 <<'PY'
import json
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
for rel in ('PROJECT_RUNTIME.json', 'runtime/era63e/always_on_state_v1.json', 'runtime/era63e/health_v1.json'):
    path = root / rel
    print(f'FILE_{rel.replace("/", "_").replace(".", "_")}_EXISTS={path.exists()}')
    if not path.exists():
        continue
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        print(f'FILE_{rel.replace("/", "_").replace(".", "_")}_JSON_ERROR={type(exc).__name__}:{exc}')
        continue
    if rel == 'PROJECT_RUNTIME.json':
        print('NEXT_SAFE_STEP=' + str(value.get('next_safe_step')))
    elif rel.endswith('always_on_state_v1.json'):
        last = value.get('last_refresh_result') or {}
        print('STATE_STATUS=' + str(value.get('status')))
        print('BLOCK_EVENTS=' + str(int(value.get('block_event_count') or 0)))
        print('REFRESH_SUCCESSES=' + str(int(value.get('full_refresh_count') or 0)))
        print('REFRESH_FAILURES=' + str(int(value.get('refresh_failure_count') or 0)))
        print('CONSECUTIVE_FAILURES=' + str(int(value.get('consecutive_refresh_failures') or 0)))
        print('LAST_REFRESH_STATUS=' + str(last.get('status')))
        print('BACKOFF_UNTIL_UTC=' + str(value.get('refresh_backoff_until_utc')))
    else:
        print('HEALTH_STATUS=' + str(value.get('status')))
PY

echo "DIAGNOSTIC_COMPLETE=YES"
