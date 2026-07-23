#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

UNIT="tokenoskobi-era63e-auto-close-v2.service"
OLD_UNIT="tokenoskobi-era63e-auto-close.service"
OBS_SERVICE="tokenoskobi-era63e-always-on-market.service"
TIMER="tokenoskobi-era63d-market-technical.timer"
UNIT_PATH="/etc/systemd/system/${UNIT}"
LOG="/root/era63e_auto_close.log"

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
systemctl is-enabled --quiet "$OBS_SERVICE"
systemctl is-active --quiet "$OBS_SERVICE"
! systemctl is-active --quiet "$TIMER"

echo "PRECHECK=VERIFIED"

systemctl stop "$OLD_UNIT" >/dev/null 2>&1 || true
systemctl reset-failed "$OLD_UNIT" >/dev/null 2>&1 || true
systemctl stop "$UNIT" >/dev/null 2>&1 || true
systemctl reset-failed "$UNIT" >/dev/null 2>&1 || true

cat > "$UNIT_PATH" <<'UNIT_EOF'
[Unit]
Description=Tokenoskobi ERA63E automatic observation closure watcher
After=network-online.target tokenoskobi-era63e-always-on-market.service
Wants=network-online.target
Requires=tokenoskobi-era63e-always-on-market.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/tokenoskobi_clean_v1
Environment=HOME=/root
Environment=GIT_TERMINAL_PROMPT=0
ExecStart=/bin/bash /root/tokenoskobi_clean_v1/tools/era63e_auto_wait_and_close.sh --worker
Restart=no
TimeoutStartSec=infinity
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
UNIT_EOF

chmod 0644 "$UNIT_PATH"
systemctl daemon-reload
rm -f "$LOG"
systemctl start "$UNIT"
sleep 3

if ! systemctl is-active --quiet "$UNIT"; then
  echo "AUTO_CLOSE_SERVICE=FAILED"
  systemctl status "$UNIT" --no-pager -l || true
  journalctl -u "$UNIT" -n 80 --no-pager || true
  [[ -f "$LOG" ]] && tail -n 80 "$LOG" || true
  exit 1
fi

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
print('BACKOFF_UNTIL_UTC=' + str(state.get('refresh_backoff_until_utc')))
PY_STATE

echo "AUTO_CLOSE_SERVICE=ACTIVE_BACKGROUND"
echo "UNIT=$UNIT"
echo "LOG=$LOG"
echo "SERVICE_TYPE=SIMPLE_LONG_RUNNING"
echo "MAX_WAIT_SEC=10800"
echo "POLL_SEC=30"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "WORKTREE=CLEAN"
echo "HEAD=$(git rev-parse HEAD)"
