#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

[[ "$(git branch --show-current)" == "main" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]

if git ls-files --error-unmatch FETCH_HEAD >/dev/null 2>&1; then
  echo "ERA64J_BLOCKED=ROOT_FETCH_HEAD_IS_TRACKED"
  exit 1
fi

status_before="$(git status --porcelain=v1 --untracked-files=all)"
echo "WORKTREE_STATUS_BEFORE_BEGIN"
printf '%s\n' "$status_before"
echo "WORKTREE_STATUS_BEFORE_END"

if [[ -e FETCH_HEAD ]]; then
  exact_line="$(git status --porcelain=v1 --untracked-files=all -- FETCH_HEAD)"
  if [[ "$exact_line" != "?? FETCH_HEAD" ]]; then
    echo "ERA64J_BLOCKED=ROOT_FETCH_HEAD_NOT_SAFE_UNTRACKED_FILE"
    exit 1
  fi
  rm -f -- FETCH_HEAD
  echo "ROOT_FETCH_HEAD_REMOVED=true"
else
  echo "ROOT_FETCH_HEAD_REMOVED=false"
fi

status_after="$(git status --porcelain=v1 --untracked-files=all)"
if [[ -n "$status_after" ]]; then
  echo "ERA64J_BLOCKED=WORKTREE_NOT_CLEAN_AFTER_FETCH_HEAD_REMOVAL"
  echo "WORKTREE_STATUS_AFTER_BEGIN"
  printf '%s\n' "$status_after"
  echo "WORKTREE_STATUS_AFTER_END"
  exit 1
fi

echo "ERA64J_FETCH_HEAD_CLEANUP=VERIFIED"
bash tools/era64j_zero_gas_cost_observation_fix_v3_and_run.sh
