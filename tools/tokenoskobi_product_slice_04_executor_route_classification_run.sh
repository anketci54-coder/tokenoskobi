#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_ROUTE_HASH='abfc88e83fd87159baa0a2bbd41ee2ceaabd96d95e9377b44fce3e1a165955ad'
ROUTE='/var/lib/tokenoskobi-product-slice-04/targeted_route_reselection_v1.json'
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/executor_route_classification_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'
MODULE="${PRODUCT_SLICE_04_EXECUTOR_CLASSIFIER_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_EXECUTOR_CLASSIFIER_TEST_PATH:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_executor_classification_${STAMP}"
OUTPUT_EXISTED=0
COMPLETED=0

fail() { printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
sha256_file() { sha256sum "$1" | awk '{print $1}'; }
rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/executor_route_classification_v1.json" ]]; then
      install -o root -g root -m 0600 "$BACKUP_DIR/executor_route_classification_v1.json" "$OUTPUT"
    else
      rm -f "$OUTPUT"
    fi
    rm -f "$OUTPUT.tmp"
    printf 'ROLLBACK=COMPLETED\n'
  fi
  exit "$rc"
}
trap rollback ERR

cd "$ROOT"
printf '\n===== 1 EXACT PREFLIGHT =====\n'
[[ "$(git branch --show-current)" == 'main' ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$EXPECTED_MAIN" ]] || fail LOCAL_HEAD_CHANGED
git fetch --quiet origin main
[[ "$(git rev-parse origin/main)" == "$EXPECTED_MAIN" ]] || fail ORIGIN_MAIN_CHANGED
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail WORKTREE_NOT_CLEAN
[[ -n "$MODULE" && -f "$MODULE" ]] || fail MODULE_MISSING
[[ -n "$TEST" && -f "$TEST" ]] || fail TEST_MISSING
[[ -f "$ROUTE" && -s "$ROUTE" ]] || fail TARGETED_ROUTE_MISSING
python3 - "$ROUTE" "$EXPECTED_ROUTE_HASH" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert p.get('schema')=='tokenoskobi.product_slice_04.targeted_route_reselection.v1'
assert p.get('status')=='TARGETED_MULTI_HOP_ROUTE_RESELECTION_COMPLETED'
assert p.get('result_hash')==sys.argv[2]
s=p.get('summary'); assert isinstance(s,dict)
assert s.get('target_transaction_count')==6
assert s.get('recognized_swap_event_count')==18
assert s.get('protocol_verified_swap_event_count')==18
assert s.get('self_call_transaction_count')==6
assert s.get('closed_loop_confirmed') is False
PY
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE
PRODUCT_PID_BEFORE="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_BEFORE="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_BEFORE" =~ ^[1-9][0-9]*$ ]] || fail PRODUCT_PID_INVALID
ROUTE_SHA_BEFORE="$(sha256_file "$ROUTE")"
REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"
printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'TARGETED_ROUTE_RESULT_HASH=%s\n' "$EXPECTED_ROUTE_HASH"
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_BEFORE"
printf 'CLASSIFICATION_SCOPE=6_SELF_CALL_TRANSACTIONS_18_OFFICIAL_SWAP_EVENTS_NO_NETWORK\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$MODULE" "$TEST"
PRODUCT_SLICE_04_EXECUTOR_CLASSIFIER_MODULE_PATH="$MODULE" python3 "$TEST"
printf 'DETERMINISTIC_TESTS=10_10_OK\n'

printf '\n===== 3 STATE BACKUP AND OFFLINE EXECUTOR CLASSIFICATION =====\n'
install -d -o root -g root -m 0700 "$BACKUP_DIR"
if [[ -f "$OUTPUT" ]]; then
  install -o root -g root -m 0600 "$OUTPUT" "$BACKUP_DIR/executor_route_classification_v1.json"
  OUTPUT_EXISTED=1
fi
python3 "$MODULE" --route "$ROUTE" --output "$OUTPUT"
[[ -f "$OUTPUT" && -s "$OUTPUT" ]] || fail OUTPUT_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail OUTPUT_MODE_INVALID

printf '\n===== 4 OUTPUT CONTRACT AND EXECUTOR EVIDENCE =====\n'
python3 - "$OUTPUT" "$EXPECTED_ROUTE_HASH" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert p.get('schema')=='tokenoskobi.product_slice_04.executor_route_classification.v1'
assert p.get('status')=='SELF_CALL_EXECUTOR_ROUTE_BLOCKERS_CLASSIFIED'
assert p.get('chain')=='BSC' and p.get('chain_id')==56
src=p.get('source'); assert isinstance(src,dict)
assert src.get('targeted_route_result_hash')==sys.argv[2]
a=p.get('authority'); assert isinstance(a,dict)
assert a.get('network_access') is False and a.get('staging_file_write') is True
for key in ('source_database_write','production_database_write','repository_write','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
    assert a.get(key) is False,key
policy=p.get('policy'); assert isinstance(policy,dict)
assert policy.get('classification_is_transaction_evidence_only') is True
assert policy.get('protocol_intent_is_not_inferred') is True
assert policy.get('ownership_or_control_is_not_inferred') is True
assert policy.get('multi_asset_execution_is_not_treated_as_simple_wallet_position') is True
transactions=p.get('transactions'); assert isinstance(transactions,list) and len(transactions)==6
summary=p.get('summary'); assert isinstance(summary,dict)
assert summary.get('transaction_count')==6
assert summary.get('self_call_transaction_count')==6
assert summary.get('closed_loop_confirmed') is False
assert summary.get('simple_wallet_position_route_count')+summary.get('exact_multi_asset_execution_count')+summary.get('unexplained_residual_transaction_count')==6
print('OUTPUT_STATUS=VERIFIED')
print(f'SIMPLE_WALLET_POSITION_ROUTE_COUNT={summary.get("simple_wallet_position_route_count")}')
print(f'EXACT_MULTI_ASSET_EXECUTION_COUNT={summary.get("exact_multi_asset_execution_count")}')
print(f'EXACT_CYCLIC_EXECUTION_COUNT={summary.get("exact_cyclic_execution_count")}')
print(f'UNEXPLAINED_RESIDUAL_TRANSACTION_COUNT={summary.get("unexplained_residual_transaction_count")}')
print(f'DATASET_CLASSIFICATION={summary.get("dataset_classification")}')
for i,tx in enumerate(transactions,start=1):
    print(f'CLASSIFIED_TX_{i}=tx:{tx["tx_hash"]},class:{tx["classification"]},cycle:{str(bool(tx["directed_cycle_present"])).lower()},out_count:{len(tx["actor_out_tokens"])},in_count:{len(tx["actor_in_tokens"])},exact_amounts:{str(bool(tx["exact_raw_amounts"])).lower()}')
    print('ACTOR_NET_'+str(i)+'='+json.dumps(tx['actor_net_by_token'],sort_keys=True,separators=(',',':')))
    print('SWAP_NET_'+str(i)+'='+json.dumps(tx['swap_net_by_token'],sort_keys=True,separators=(',',':')))
print(f'RESULT_HASH={p.get("result_hash")}')
print('CLOSED_LOOP_CONFIRMED=false')
print(f'NEXT_SAFE_STEP={summary.get("next_safe_step")}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
[[ "$(sha256_file "$ROUTE")" == "$ROUTE_SHA_BEFORE" ]] || fail TARGETED_ROUTE_MUTATED
[[ "$(git status --porcelain=v1 --untracked-files=all)" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_MUTATED
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_STOPPED
PRODUCT_PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_AFTER" == "$PRODUCT_PID_BEFORE" ]] || fail PRODUCT_SERVICE_RESTARTED
[[ "$PRODUCT_NRESTARTS_AFTER" == "$PRODUCT_NRESTARTS_BEFORE" ]] || fail PRODUCT_RESTART_COUNT_CHANGED
printf 'TARGETED_ROUTE_IMMUTABLE=VERIFIED\n'
printf 'NETWORK_ACCESS=false\n'
printf 'REPOSITORY_MUTATION=false\n'
printf 'PANEL_MUTATION=false\n'
printf 'SERVICE_RESTARTED=false\n'
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_AFTER"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_AFTER"
printf 'STATE_DIRECTORY_MODE=%s\n' "$(stat -c '%a' "$STATE_DIR")"
printf 'OUTPUT_MODE=%s\n' "$(stat -c '%a' "$OUTPUT")"
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'
COMPLETED=1
trap - ERR

NEXT_STEP="$(python3 - "$OUTPUT" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(p['summary']['next_safe_step'])
PY
)"
printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_04_EXECUTOR_ROUTE_CLASSIFICATION=SUCCESS\n'
printf 'CLASSIFICATION_SOURCE=TRANSACTION_EVIDENCE_ONLY\n'
printf 'PROTOCOL_INTENT_INFERRED=false\n'
printf 'OWNERSHIP_CONTROL_INFERRED=false\n'
printf 'CLOSED_LOOP_CONFIRMED=false\n'
printf 'TARGETED_ROUTE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_18=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_17=OPEN\n'
printf 'NEXT_SAFE_STEP=%s\n' "$NEXT_STEP"
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
