#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

OBS_SERVICE="tokenoskobi-era63e-always-on-market.service"
TIMER="tokenoskobi-era63d-market-technical.timer"
WATCHER="tokenoskobi-era63e-auto-close-v2.service"
OLD_WATCHER="tokenoskobi-era63e-auto-close.service"
LOG="/root/era63e_auto_close.log"

fail() {
  echo "AUTO_CLOSE_PRECHECK=FAILED"
  echo "REASON=$1"
  exit 1
}

echo "BRANCH=$(git branch --show-current)"
[[ "$(git branch --show-current)" == "main" ]] || fail "BRANCH_NOT_MAIN"

git fetch origin main --quiet
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git rev-parse origin/main)"
echo "LOCAL_HEAD=$LOCAL_HEAD"
echo "REMOTE_HEAD=$REMOTE_HEAD"
[[ "$LOCAL_HEAD" == "$REMOTE_HEAD" ]] || fail "LOCAL_REMOTE_HEAD_MISMATCH"

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "WORKTREE=DIRTY"
  git status --short
  fail "WORKTREE_DIRTY_REVIEW_REQUIRED"
fi
echo "WORKTREE=CLEAN"

OBS_ENABLED="$(systemctl is-enabled "$OBS_SERVICE" 2>/dev/null || true)"
OBS_ACTIVE="$(systemctl is-active "$OBS_SERVICE" 2>/dev/null || true)"
TIMER_ENABLED="$(systemctl is-enabled "$TIMER" 2>/dev/null || true)"
TIMER_ACTIVE="$(systemctl is-active "$TIMER" 2>/dev/null || true)"
echo "OBS_SERVICE_ENABLED=$OBS_ENABLED"
echo "OBS_SERVICE_ACTIVE=$OBS_ACTIVE"
echo "FIXED_TIMER_ENABLED=$TIMER_ENABLED"
echo "FIXED_TIMER_ACTIVE=$TIMER_ACTIVE"

if [[ "$OBS_ENABLED" != "enabled" ]]; then
  systemctl enable "$OBS_SERVICE"
fi
if [[ "$OBS_ACTIVE" != "active" ]]; then
  systemctl restart "$OBS_SERVICE"
  sleep 3
fi
systemctl is-active --quiet "$OBS_SERVICE" || {
  systemctl status "$OBS_SERVICE" --no-pager -l || true
  journalctl -u "$OBS_SERVICE" -n 80 --no-pager || true
  fail "OBSERVATION_SERVICE_INACTIVE"
}

if systemctl is-active --quiet "$TIMER" || [[ "$TIMER_ENABLED" == "enabled" ]]; then
  systemctl disable --now "$TIMER" >/dev/null 2>&1 || true
fi
! systemctl is-active --quiet "$TIMER" || fail "FIXED_TIMER_STILL_ACTIVE"

systemctl stop "$OLD_WATCHER" >/dev/null 2>&1 || true
systemctl reset-failed "$OLD_WATCHER" >/dev/null 2>&1 || true
systemctl stop "$WATCHER" >/dev/null 2>&1 || true
systemctl reset-failed "$WATCHER" >/dev/null 2>&1 || true
systemctl daemon-reload

echo "AUTO_CLOSE_PRECHECK=VERIFIED"

set +e
bash tools/era63e_auto_close_service_repair.sh
RC=$?
set -e

if [[ "$RC" -ne 0 ]]; then
  echo "AUTO_CLOSE_REPAIR_RESULT=FAILED_RC_$RC"
  systemctl status "$WATCHER" --no-pager -l || true
  journalctl -u "$WATCHER" -n 120 --no-pager || true
  [[ -f "$LOG" ]] && tail -n 120 "$LOG" || true
  exit "$RC"
fi

systemctl is-active --quiet "$WATCHER" || {
  echo "AUTO_CLOSE_REPAIR_RESULT=WATCHER_NOT_ACTIVE"
  systemctl status "$WATCHER" --no-pager -l || true
  journalctl -u "$WATCHER" -n 120 --no-pager || true
  [[ -f "$LOG" ]] && tail -n 120 "$LOG" || true
  exit 1
}

echo "AUTO_CLOSE_REPAIR_RESULT=ACTIVE_BACKGROUND"
echo "WATCHER_UNIT=$WATCHER"
echo "LOG=$LOG"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "HEAD=$(git rev-parse HEAD)"
