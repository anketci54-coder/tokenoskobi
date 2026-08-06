#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

echo "ERA64J_EXPLICIT_PRECHECK=STARTED"

branch="$(git branch --show-current)"
echo "BRANCH=$branch"
if [[ "$branch" != "main" ]]; then
  echo "ERA64J_BLOCKED=NOT_ON_MAIN"
  exit 1
fi

git fetch origin main --quiet
local_head="$(git rev-parse HEAD)"
remote_head="$(git rev-parse origin/main)"
echo "LOCAL_HEAD=$local_head"
echo "REMOTE_HEAD=$remote_head"
if [[ "$local_head" != "$remote_head" ]]; then
  echo "ERA64J_BLOCKED=LOCAL_REMOTE_HEAD_MISMATCH"
  exit 1
fi

transient_files=(
  config/era64j_historical_transfer_receipt_cost_enrichment_v1.json
  tools/era64j_historical_transfer_receipt_cost_enrichment_v1.py
  tests/test_era64j_historical_transfer_receipt_cost_enrichment_v1.py
  data/control/era64j_historical_transfer_receipt_cost_enrichment_v1.json
  data/replay/era64j_historical_transfer_receipt_cost_enrichment_v1.json
  reports/LATEST_ERA64J_HISTORICAL_TRANSFER_RECEIPT_COST_ENRICHMENT.md
)

status_before="$(git status --porcelain=v1)"
if [[ -n "$status_before" ]]; then
  echo "WORKTREE_STATUS_BEFORE_BEGIN"
  printf '%s\n' "$status_before"
  echo "WORKTREE_STATUS_BEFORE_END"

  removed=0
  for path in "${transient_files[@]}"; do
    if [[ -e "$path" ]] && ! git ls-files --error-unmatch -- "$path" >/dev/null 2>&1; then
      rm -f -- "$path"
      echo "REMOVED_TRANSIENT=$path"
      removed=$((removed+1))
    fi
  done
  echo "TRANSIENT_REMOVED_COUNT=$removed"
fi

status_after="$(git status --porcelain=v1)"
if [[ -n "$status_after" ]]; then
  echo "ERA64J_BLOCKED=WORKTREE_NOT_CLEAN_AFTER_SAFE_TRANSIENT_CLEANUP"
  echo "WORKTREE_STATUS_AFTER_BEGIN"
  printf '%s\n' "$status_after"
  echo "WORKTREE_STATUS_AFTER_END"
  exit 1
fi

echo "WORKTREE=CLEAN"
echo "ERA64J_V3_RUN=STARTING"
bash tools/era64j_zero_gas_cost_observation_fix_v3_and_run.sh
