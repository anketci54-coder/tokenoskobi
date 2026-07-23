#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

UNIT="tokenoskobi-era63e-auto-close.service"
LOG="/root/era63e_auto_close.log"
SERVICE="tokenoskobi-era63e-always-on-market.service"
TIMER="tokenoskobi-era63d-market-technical.timer"
MAX_WAIT_SEC=10800
POLL_SEC=30

show_snapshot() {
  python3 <<'PY'
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from pathlib import Path

root = Path('/root/tokenoskobi_clean_v1')
state_path = root / 'runtime/era63e/always_on_state_v1.json'
runtime_path = root / 'PROJECT_RUNTIME.json'
if runtime_path.exists():
    runtime = json.loads(runtime_path.read_text(encoding='utf-8'))
    print('NEXT_SAFE_STEP=' + str(runtime.get('next_safe_step')))
if not state_path.exists():
    print('STATE=NOT_FOUND')
    raise SystemExit(0)
state = json.loads(state_path.read_text(encoding='utf-8'))
last = state.get('last_refresh_result') or {}
print('STATE_STATUS=' + str(state.get('status')))
print('BLOCK_EVENTS=' + str(int(state.get('block_event_count') or 0)))
print('REFRESH_SUCCESSES=' + str(int(state.get('full_refresh_count') or 0)))
print('REFRESH_FAILURES=' + str(int(state.get('refresh_failure_count') or 0)))
print('CONSECUTIVE_FAILURES=' + str(int(state.get('consecutive_refresh_failures') or 0)))
print('LAST_REFRESH_STATUS=' + str(last.get('status')))
print('LAST_REFRESH_REASON=' + str(state.get('last_refresh_reason')))
print('BACKOFF_UNTIL_UTC=' + str(state.get('refresh_backoff_until_utc')))
print('REFRESH_IN_PROGRESS=' + str(bool(state.get('refresh_in_progress'))).lower())
PY
}

worker() {
  exec >>"$LOG" 2>&1
  echo "AUTO_CLOSE_STARTED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "MAX_WAIT_SEC=$MAX_WAIT_SEC"
  echo "POLL_SEC=$POLL_SEC"

  [[ "$(git branch --show-current)" == "main" ]]
  [[ -z "$(git status --porcelain=v1)" ]]
  git fetch origin main --quiet
  [[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
  systemctl is-enabled --quiet "$SERVICE"
  systemctl is-active --quiet "$SERVICE"
  ! systemctl is-active --quiet "$TIMER"

  start_epoch="$(date +%s)"
  last_report_epoch=0

  while true; do
    now_epoch="$(date +%s)"
    elapsed=$((now_epoch - start_epoch))
    if (( elapsed > MAX_WAIT_SEC )); then
      echo "AUTO_CLOSE_RESULT=TIMEOUT"
      show_snapshot
      exit 2
    fi

    if ! systemctl is-active --quiet "$SERVICE"; then
      echo "AUTO_CLOSE_RESULT=BLOCKED_OBSERVATION_SERVICE_INACTIVE"
      show_snapshot
      exit 3
    fi
    if systemctl is-active --quiet "$TIMER"; then
      echo "AUTO_CLOSE_RESULT=BLOCKED_FIXED_TIMER_ACTIVE"
      exit 4
    fi
    if [[ -n "$(git status --porcelain=v1)" ]]; then
      echo "AUTO_CLOSE_RESULT=BLOCKED_WORKTREE_DIRTY"
      git status --short
      exit 5
    fi

    ready="$(python3 <<'PY_READY'
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from pathlib import Path

root = Path('/root/tokenoskobi_clean_v1')
state_path = root / 'runtime/era63e/always_on_state_v1.json'
health_path = root / 'runtime/era63e/health_v1.json'
runtime_path = root / 'PROJECT_RUNTIME.json'
if not state_path.exists() or not health_path.exists() or not runtime_path.exists():
    print('0')
    raise SystemExit(0)
state = json.loads(state_path.read_text(encoding='utf-8'))
health = json.loads(health_path.read_text(encoding='utf-8'))
runtime = json.loads(runtime_path.read_text(encoding='utf-8'))
if runtime.get('next_safe_step') == 'ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION':
    print('2')
    raise SystemExit(0)
last = state.get('last_refresh_result') or {}
successes = int(state.get('full_refresh_count') or 0)
failures = int(state.get('refresh_failure_count') or 0)
attempts = successes + failures
failure_rate = failures / attempts if attempts else 1.0
heartbeat = state.get('heartbeat_at_utc')
if isinstance(heartbeat, str) and heartbeat.endswith('Z'):
    heartbeat = heartbeat[:-1] + '+00:00'
try:
    heartbeat_dt = datetime.fromisoformat(str(heartbeat))
    if heartbeat_dt.tzinfo is None:
        heartbeat_dt = heartbeat_dt.replace(tzinfo=timezone.utc)
    heartbeat_age = (datetime.now(timezone.utc) - heartbeat_dt.astimezone(timezone.utc)).total_seconds()
except Exception:
    heartbeat_age = 10**9
backoff_until = float(state.get('refresh_backoff_until_monotonic') or 0.0)
ready = (
    state.get('status') == 'RUNNING'
    and health.get('status') == 'RUNNING'
    and heartbeat_age <= 25.0
    and not bool(state.get('refresh_in_progress'))
    and successes >= 3
    and attempts >= 3
    and failure_rate <= 0.20
    and int(state.get('consecutive_refresh_failures') or 0) == 0
    and backoff_until <= time.monotonic()
    and last.get('status') == 'PASS'
    and int(last.get('successful_pool_count') or 0) >= 1
)
print('1' if ready else '0')
PY_READY
)"

    if [[ "$ready" == "2" ]]; then
      echo "AUTO_CLOSE_RESULT=ALREADY_CLOSED"
      show_snapshot
      exit 0
    fi

    if [[ "$ready" == "1" ]]; then
      echo "NATURAL_CYCLE_GATE=READY"
      show_snapshot
      set +e
      bash tools/era63e_observe_close.sh
      rc=$?
      set -e
      next="$(python3 - <<'PY_NEXT'
import json
from pathlib import Path
v=json.loads(Path('/root/tokenoskobi_clean_v1/PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
print(v.get('next_safe_step'))
PY_NEXT
)"
      if [[ "$rc" -eq 0 && "$next" == "ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION" ]]; then
        echo "AUTO_CLOSE_RESULT=ERA63_CLOSED_VERIFIED_GITHUB_SEALED"
        echo "HEAD=$(git rev-parse HEAD)"
        echo "REMOTE_HEAD=$(git rev-parse origin/main)"
        echo "WORKTREE=$(if [[ -z "$(git status --porcelain=v1)" ]]; then echo CLEAN; else echo DIRTY; fi)"
        echo "AUTO_CLOSE_FINISHED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        exit 0
      fi
      echo "CLOSURE_ATTEMPT_RESULT=PENDING_OR_FAILED_RC_${rc}"
      show_snapshot
    fi

    if (( now_epoch - last_report_epoch >= 300 )); then
      echo "AUTO_CLOSE_PROGRESS_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "ELAPSED_SEC=$elapsed"
      show_snapshot
      last_report_epoch=$now_epoch
    fi
    sleep "$POLL_SEC"
  done
}

if [[ "${1:-}" == "--worker" ]]; then
  worker
  exit 0
fi

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
systemctl is-enabled --quiet "$SERVICE"
systemctl is-active --quiet "$SERVICE"
! systemctl is-active --quiet "$TIMER"

if systemctl is-active --quiet "$UNIT"; then
  echo "AUTO_CLOSE_WATCHER=ALREADY_ACTIVE"
  show_snapshot
  echo "LOG=$LOG"
  exit 0
fi

current_next="$(python3 - <<'PY_NEXT'
import json
from pathlib import Path
v=json.loads(Path('/root/tokenoskobi_clean_v1/PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
print(v.get('next_safe_step'))
PY_NEXT
)"
if [[ "$current_next" == "ERA64_SUCCESSFUL_WALLET_STATS_AND_CLUSTERING_OPENING_DECISION" ]]; then
  echo "AUTO_CLOSE_WATCHER=NOT_REQUIRED_ALREADY_CLOSED"
  show_snapshot
  exit 0
fi
[[ "$current_next" == "ERA63E_CONTINUOUS_REAL_DATA_OBSERVATION_AND_TECHNICAL_LINE_CLOSURE" ]]

rm -f "$LOG"
systemctl reset-failed "$UNIT" >/dev/null 2>&1 || true
systemd-run \
  --unit="${UNIT%.service}" \
  --collect \
  --property=Type=oneshot \
  --property=WorkingDirectory=/root/tokenoskobi_clean_v1 \
  /bin/bash /root/tokenoskobi_clean_v1/tools/era63e_auto_wait_and_close.sh --worker >/dev/null

sleep 2
systemctl is-active --quiet "$UNIT"
echo "AUTO_CLOSE_WATCHER=STARTED_BACKGROUND"
echo "UNIT=$UNIT"
echo "LOG=$LOG"
show_snapshot
