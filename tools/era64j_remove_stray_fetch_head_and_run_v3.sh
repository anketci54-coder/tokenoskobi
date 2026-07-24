#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

echo "ERA64J_STRAY_FETCH_HEAD_CLEANUP=STARTED"

[[ "$(git branch --show-current)" == "main" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]

STATUS="$(git status --porcelain=v1 --untracked-files=all)"
if [[ "$STATUS" != "?? FETCH_HEAD" ]]; then
  echo "ERA64J_BLOCKED=UNEXPECTED_WORKTREE_STATE"
  printf '%s\n' "$STATUS"
  exit 1
fi

if git ls-files --error-unmatch -- FETCH_HEAD >/dev/null 2>&1; then
  echo "ERA64J_BLOCKED=FETCH_HEAD_IS_TRACKED"
  exit 1
fi

[[ -f FETCH_HEAD ]]
[[ ! -L FETCH_HEAD ]]
rm -f -- FETCH_HEAD
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]]

echo "ERA64J_STRAY_FETCH_HEAD_CLEANUP=VERIFIED"
bash tools/era64j_zero_gas_cost_observation_fix_v3_and_run.sh
