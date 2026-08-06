#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

OBS_SERVICE="tokenoskobi-era63e-always-on-market.service"
TIMER="tokenoskobi-era63d-market-technical.timer"
WATCHER="tokenoskobi-era63e-auto-close-v3.service"
WATCHER_PATH="/etc/systemd/system/${WATCHER}"
LOG="/root/era63e_auto_close_v3.log"
MAX_WAIT_SEC=10800
POLL_SEC=30

KNOWN_DIRTY=(
  03_ROADMAP.md
  04_ALMANAC.md
  05_ATLAS.md
  06_PROJECT_MASTER_STATE.md
  07_PROJECT_HANDOFF.md
  PROJECT_HISTORY.json
  PROJECT_RUNTIME.json
  data/control/era63e_continuous_observation_and_technical_closure_v1.json
  data/control/latest_tk_machine_state.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  reports/LATEST_ERA63E_CONTINUOUS_OBSERVATION_AND_TECHNICAL_CLOSURE.md
  reports/LATEST_TK_AI_HANDOFF.md
)

fail() {
  echo "ERA63E_RECOVERY=FAILED"
  echo "REASON=$1"
  exit 1
}

prepare_fixed_closer() {
  python3 <<'PY_PATCH'
from pathlib import Path

root = Path('/root/tokenoskobi_clean_v1')
source = root / 'tools/era63e_observe_close.sh'
target = Path('/tmp/era63e_observe_close_rollback_safe.sh')
text = source.read_text(encoding='utf-8')

old_atlas = "(ROOT / '05_ATLAS.md').write_text(replace_marker(atlas, start, end, block), encoding='utf-8')"
new_atlas = "(ROOT / '05_ATLAS.md').write_text(replace_marker(atlas, start, end, block).rstrip() + '\\n', encoding='utf-8')"
if old_atlas not in text:
    raise SystemExit('PATCH_TARGET_ATLAS_WRITE_NOT_FOUND')
text = text.replace(old_atlas, new_atlas, 1)

old_rollback = '''  if [[ "$PUSHED" -eq 0 ]]; then
    if [[ "$COMMITTED" -eq 1 ]]; then'''
new_rollback = '''  if [[ "$PUSHED" -eq 0 ]]; then
    git reset --mixed HEAD >/dev/null 2>&1 || true
    if [[ "$COMMITTED" -eq 1 ]]; then'''
if old_rollback not in text:
    raise SystemExit('PATCH_TARGET_ROLLBACK_NOT_FOUND')
text = text.replace(old_rollback, new_rollback, 1)

target.write_text(text, encoding='utf-8')
target.chmod(0o700)
print('FIXED_CLOSER=PREPARED')
PY_PATCH
}

snapshot() {
  python3 <<'PY_STATE'
import json
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
state = json.loads((root / 'runtime/era63e/always_on_state_v1.json').read_text(encoding='utf-8'))
last = state.get('last_refresh_result') or {}
print('STATE_STATUS=' + str(state.get('status')))
print('BLOCK_EVENTS=' + str(int(state.get('block_event_count') or 0)))
print('REFRESH_SUCCESSES=' + str(int(state.get('full_refresh_count') or 0)))
print('REFRESH_FAILURES=' + str(int(state.get('refresh_failure_count') or 0)))
print('CONSECUTIVE_FAILURES=' + str(int(state.get('consecutive_refresh_failures') or 0)))
print('LAST_REFRESH_STATUS=' + str(last.get('status')))
print('LAST_REFRESH_REASON=' + str(state.get('last_refresh_reason')))
print('BACKOFF_UNTIL_UTC=' + str(state.get('refresh_backoff_until_utc')))
PY_STATE
}

worker() {
  exec >>"$LOG" 2>&1
  echo "ERA63E_AUTO_CLOSE_V3_STARTED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  start_epoch="$(date +%s)"
  last_report_epoch=0

  while true; do
    now_epoch="$(date +%s)"
    elapsed=$((now_epoch - start_epoch))
    if (( elapsed > MAX_WAIT_SEC )); then
      echo "ERA63E_AUTO_CLOSE_V3=TIMEOUT"
      snapshot
      exit 2
    fi

    systemctl is-active --quiet "$OBS_SERVICE" || {
      echo "ERA63E_AUTO_CLOSE_V3=BLOCKED_OBSERVATION_SERVICE_INACTIVE"
      exit 3
    }
    ! systemctl is-active --quiet "$TIMER" || {
      echo "ERA63E_AUTO_CLOSE_V3=BLOCKED_FIXED_TIMER_ACTIVE"
      exit 4
    }
    if [[ -n "$(git status --porcelain=v1)" ]]; then
      echo "ERA63E_AUTO_CLOSE_V3=BLOCKED_WORKTREE_DIRTY"
      git status --short
      exit 5
    fi

    next="$(python3 - <<'PY_NEXT'
import json
from pathlib import Path
v=json.loads(Path('/root/tokenoskobi_clean_v1/PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
print(v.get('next_safe_step'))
PY_NEXT
)"
    if [[ "$next" == "ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION" ]]; then
      echo "ERA63E_AUTO_CLOSE_V3=ALREADY_CLOSED"
      exit 0
    fi

    ready="$(python3 <<'PY_READY'
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
state = json.loads((root / 'runtime/era63e/always_on_state_v1.json').read_text(encoding='utf-8'))
health = json.loads((root / 'runtime/era63e/health_v1.json').read_text(encoding='utf-8'))
last = state.get('last_refresh_result') or {}
successes = int(state.get('full_refresh_count') or 0)
failures = int(state.get('refresh_failure_count') or 0)
attempts = successes + failures
rate = failures / attempts if attempts else 1.0
heartbeat = str(state.get('heartbeat_at_utc') or '')
if heartbeat.endswith('Z'):
    heartbeat = heartbeat[:-1] + '+00:00'
try:
    dt = datetime.fromisoformat(heartbeat)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
except Exception:
    age = 10**9
ready = (
    state.get('status') == 'RUNNING'
    and health.get('status') == 'RUNNING'
    and age <= 25
    and not bool(state.get('refresh_in_progress'))
    and successes >= 3
    and attempts >= 3
    and rate <= 0.20
    and int(state.get('consecutive_refresh_failures') or 0) == 0
    and float(state.get('refresh_backoff_until_monotonic') or 0.0) <= time.monotonic()
    and last.get('status') == 'PASS'
    and int(last.get('successful_pool_count') or 0) >= 1
)
print('1' if ready else '0')
PY_READY
)"

    if [[ "$ready" == "1" ]]; then
      echo "NATURAL_CYCLE_GATE=READY"
      snapshot
      prepare_fixed_closer
      set +e
      bash /tmp/era63e_observe_close_rollback_safe.sh
      rc=$?
      set -e
      next="$(python3 - <<'PY_NEXT2'
import json
from pathlib import Path
v=json.loads(Path('/root/tokenoskobi_clean_v1/PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
print(v.get('next_safe_step'))
PY_NEXT2
)"
      if [[ "$rc" -eq 0 && "$next" == "ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION" ]]; then
        echo "ERA63E_AUTO_CLOSE_V3=ERA63_CLOSED_VERIFIED_GITHUB_SEALED"
        echo "HEAD=$(git rev-parse HEAD)"
        echo "REMOTE_HEAD=$(git rev-parse origin/main)"
        echo "WORKTREE=CLEAN"
        exit 0
      fi
      echo "CLOSURE_ATTEMPT=PENDING_OR_FAILED_RC_${rc}"
      if [[ -n "$(git status --porcelain=v1)" ]]; then
        echo "POST_FAILURE_WORKTREE_DIRTY"
        git status --short
        exit 6
      fi
    fi

    if (( now_epoch - last_report_epoch >= 300 )); then
      echo "ERA63E_AUTO_CLOSE_V3_PROGRESS_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "ELAPSED_SEC=$elapsed"
      snapshot
      last_report_epoch=$now_epoch
    fi
    sleep "$POLL_SEC"
  done
}

if [[ "${1:-}" == "--worker" ]]; then
  worker
  exit 0
fi

[[ "$(git branch --show-current)" == "main" ]] || fail "BRANCH_NOT_MAIN"
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || fail "LOCAL_REMOTE_HEAD_MISMATCH"
systemctl is-enabled --quiet "$OBS_SERVICE" || fail "OBSERVATION_SERVICE_NOT_ENABLED"
systemctl is-active --quiet "$OBS_SERVICE" || fail "OBSERVATION_SERVICE_NOT_ACTIVE"
! systemctl is-active --quiet "$TIMER" || fail "FIXED_TIMER_ACTIVE"

systemctl stop tokenoskobi-era63e-auto-close.service >/dev/null 2>&1 || true
systemctl stop tokenoskobi-era63e-auto-close-v2.service >/dev/null 2>&1 || true
systemctl stop "$WATCHER" >/dev/null 2>&1 || true
systemctl reset-failed tokenoskobi-era63e-auto-close.service >/dev/null 2>&1 || true
systemctl reset-failed tokenoskobi-era63e-auto-close-v2.service >/dev/null 2>&1 || true
systemctl reset-failed "$WATCHER" >/dev/null 2>&1 || true

python3 <<'PY_VALIDATE_DIRTY'
import subprocess
from pathlib import Path
root = Path('/root/tokenoskobi_clean_v1')
allowed = {
    '03_ROADMAP.md', '04_ALMANAC.md', '05_ATLAS.md', '06_PROJECT_MASTER_STATE.md',
    '07_PROJECT_HANDOFF.md', 'PROJECT_HISTORY.json', 'PROJECT_RUNTIME.json',
    'data/control/era63e_continuous_observation_and_technical_closure_v1.json',
    'data/control/latest_tk_machine_state.json',
    'data/tokenoskobi_v1_v8_master_era_roadmap.json',
    'reports/LATEST_ERA63E_CONTINUOUS_OBSERVATION_AND_TECHNICAL_CLOSURE.md',
    'reports/LATEST_TK_AI_HANDOFF.md',
}
raw = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=root, text=True)
unknown = []
for line in raw.splitlines():
    path = line[3:]
    if ' -> ' in path:
        path = path.split(' -> ', 1)[1]
    if path not in allowed:
        unknown.append(line)
if unknown:
    print('UNKNOWN_DIRTY_PATHS=FOUND')
    print('\n'.join(unknown))
    raise SystemExit(1)
print('DIRTY_SCOPE=KNOWN_FAILED_CLOSURE_ARTIFACTS_ONLY')
PY_VALIDATE_DIRTY

git reset --mixed HEAD >/dev/null
for path in "${KNOWN_DIRTY[@]}"; do
  if git cat-file -e "HEAD:${path}" 2>/dev/null; then
    git restore --source=HEAD --worktree -- "$path"
  else
    rm -f -- "$path"
  fi
done
[[ -z "$(git status --porcelain=v1)" ]] || {
  git status --short
  fail "WORKTREE_RECOVERY_INCOMPLETE"
}

echo "FAILED_CLOSURE_ROLLBACK_RECOVERY=PASS"
echo "WORKTREE=CLEAN"
prepare_fixed_closer

cat > "$WATCHER_PATH" <<'UNIT_EOF'
[Unit]
Description=Tokenoskobi ERA63E rollback-safe automatic closure watcher
After=network-online.target tokenoskobi-era63e-always-on-market.service
Wants=network-online.target
Requires=tokenoskobi-era63e-always-on-market.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/tokenoskobi_clean_v1
Environment=HOME=/root
Environment=GIT_TERMINAL_PROMPT=0
ExecStart=/bin/bash /root/tokenoskobi_clean_v1/tools/era63e_dirty_rollback_recover_and_close.sh --worker
Restart=no
TimeoutStartSec=infinity
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
UNIT_EOF
chmod 0644 "$WATCHER_PATH"
systemctl daemon-reload
rm -f "$LOG"
systemctl start "$WATCHER"
sleep 3
systemctl is-active --quiet "$WATCHER" || {
  systemctl status "$WATCHER" --no-pager -l || true
  journalctl -u "$WATCHER" -n 120 --no-pager || true
  [[ -f "$LOG" ]] && tail -n 120 "$LOG" || true
  fail "WATCHER_V3_NOT_ACTIVE"
}

echo "ERA63E_RECOVERY=APPLIED"
echo "AUTO_CLOSE_WATCHER=ACTIVE_BACKGROUND"
echo "UNIT=$WATCHER"
echo "LOG=$LOG"
snapshot
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "HEAD=$(git rev-parse HEAD)"
