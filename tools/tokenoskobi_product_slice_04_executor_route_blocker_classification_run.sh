#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_DB_HASH='99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_ROUTE_HASH='abfc88e83fd87159baa0a2bbd41ee2ceaabd96d95e9377b44fce3e1a165955ad'
DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
ROUTE='/var/lib/tokenoskobi-product-slice-04/targeted_route_reselection_v1.json'
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/executor_route_blocker_classification_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'
MODULE="${PRODUCT_SLICE_04_EXECUTOR_CLASSIFIER_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_EXECUTOR_CLASSIFIER_TEST_PATH:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_executor_classifier_${STAMP}"
OUTPUT_EXISTED=0
COMPLETED=0

fail() { printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
sha256_file() { sha256sum "$1" | awk '{print $1}'; }
rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/executor_route_blocker_classification_v1.json" ]]; then
      install -o root -g root -m 0600 "$BACKUP_DIR/executor_route_blocker_classification_v1.json" "$OUTPUT"
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
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail WORKTREE_NOT_CLEAN

git fetch --quiet origin main
[[ "$(git rev-parse origin/main)" == "$EXPECTED_MAIN" ]] || fail ORIGIN_MAIN_CHANGED
[[ -n "$MODULE" && -f "$MODULE" ]] || fail MODULE_MISSING
[[ -n "$TEST" && -f "$TEST" ]] || fail TEST_MISSING
[[ -f "$DB" && -f "$ROUTE" ]] || fail REQUIRED_EVIDENCE_MISSING
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_HASH_CHANGED

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
DB_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$DB")"
ROUTE_SHA_BEFORE="$(sha256_file "$ROUTE")"
REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"

printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_DATABASE_SHA256=%s\n' "$EXPECTED_DB_HASH"
printf 'TARGETED_ROUTE_RESULT_HASH=%s\n' "$EXPECTED_ROUTE_HASH"
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_BEFORE"
printf 'CLASSIFICATION_SCOPE=6_SELF_CALL_TRANSACTIONS_18_OFFICIAL_SWAPS_COMPONENT_AND_SETTLEMENT_ATTRIBUTION\n'
printf 'NETWORK_ACCESS=false\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$MODULE" "$TEST"
env PRODUCT_SLICE_04_EXECUTOR_CLASSIFIER_MODULE_PATH="$MODULE" python3 "$TEST"
printf 'DETERMINISTIC_TESTS=10_10_OK\n'

printf '\n===== 3 STATE BACKUP AND EXECUTOR BLOCKER CLASSIFICATION =====\n'
install -d -o root -g root -m 0700 "$STATE_DIR" "$BACKUP_DIR"
if [[ -f "$OUTPUT" ]]; then
  OUTPUT_EXISTED=1
  install -o root -g root -m 0600 "$OUTPUT" "$BACKUP_DIR/executor_route_blocker_classification_v1.json"
fi

python3 "$MODULE" --database "$DB" --route "$ROUTE" --output "$OUTPUT"
[[ -f "$OUTPUT" && -s "$OUTPUT" ]] || fail OUTPUT_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail OUTPUT_MODE_INVALID

printf '\n===== 4 OUTPUT CONTRACT AND EXECUTOR EVIDENCE =====\n'
python3 - "$OUTPUT" "$EXPECTED_DB_HASH" "$EXPECTED_ROUTE_HASH" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert p.get('schema')=='tokenoskobi.product_slice_04.executor_route_blocker_classification.v1'
assert p.get('status')=='EXECUTOR_ROUTE_BLOCKERS_CLASSIFIED'
assert p.get('chain')=='BSC' and p.get('chain_id')==56
source=p.get('source'); assert isinstance(source,dict)
assert source.get('database_sha256')==sys.argv[2]
assert source.get('targeted_route_result_hash')==sys.argv[3]
a=p.get('authority'); assert isinstance(a,dict)
assert a.get('network_access') is False and a.get('staging_file_write') is True
for key in ('source_database_write','production_database_write','repository_write','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
    assert a.get(key) is False,key
policy=p.get('policy'); assert isinstance(policy,dict)
assert policy.get('identity_or_ownership_inference_allowed') is False
assert policy.get('component_closed_loop_requires_actor_settlement_attribution') is True
assert policy.get('position_raw_amount_must_reverse_exactly') is True
transactions=p.get('transactions'); assert isinstance(transactions,list) and len(transactions)==6
summary=p.get('summary'); assert isinstance(summary,dict)
assert summary.get('target_transaction_count')==6
assert summary.get('self_call_transaction_count')==6
assert summary.get('confirmed_component_closed_loop_count')<=summary.get('actor_attributed_component_reverse_candidate_count')
print('OUTPUT_STATUS=VERIFIED')
print(f'ACTOR={p.get("actor")}')
print(f'ACTOR_BEHAVIOR_CLASS={p.get("actor_behavior_class")}')
for key in ('target_transaction_count','self_call_transaction_count','exact_multi_asset_executor_transaction_count','unexplained_settlement_transaction_count','total_component_count','two_endpoint_component_count','zero_net_cycle_component_count','multi_endpoint_component_count','component_reverse_candidate_count','actor_attributed_component_reverse_candidate_count','confirmed_component_closed_loop_count'):
    print(f'{key.upper()}={summary.get(key)}')
for i,tx in enumerate(transactions,start=1):
    print(f'EXECUTOR_TX_{i}=tx:{tx["tx_hash"]},behavior:{tx["behavior_class"]},actor_out:{tx["actor_out_token_count"]},actor_in:{tx["actor_in_token_count"]},components:{tx["component_count"]},two_endpoint:{tx["two_endpoint_component_count"]},zero_cycle:{tx["zero_net_cycle_component_count"]},multi_endpoint:{tx["multi_endpoint_component_count"]},counterparties:{len(tx["actor_counterparties"])}')
    print('ACTOR_NET_'+str(i)+'='+json.dumps(tx.get('actor_net_by_token'),sort_keys=True,separators=(',',':')))
    print('SWAP_NET_'+str(i)+'='+json.dumps(tx.get('swap_net_by_token'),sort_keys=True,separators=(',',':')))
    for j,c in enumerate(tx.get('components') or [],start=1):
        print(f'COMPONENT_{i}_{j}=class:{c["classification"]},events:{c["event_count"]},input:{c.get("input_token") or "NONE"},output:{c.get("output_token") or "NONE"},input_raw:{c.get("input_raw") or "NONE"},output_raw:{c.get("output_raw") or "NONE"}')
for i,c in enumerate(p.get('component_reverse_candidates') or [],start=1):
    print(f'COMPONENT_REVERSE_{i}=open:{c["opening_tx_hash"]},close:{c["closing_tx_hash"]},base:{c["base_token"]},position:{c["position_token"]},position_exact:{str(bool(c["position_amount_exact"])).lower()},actor_attributed:{str(bool(c["actor_settlement_attribution_verified"])).lower()},confirmed:{str(bool(c["closed_loop_confirmed"])).lower()}')
print(f'RESULT_HASH={p.get("result_hash")}')
print(f'CLOSED_LOOP_CONFIRMED={str(bool(summary.get("closed_loop_confirmed"))).lower()}')
print(f'NEXT_SAFE_STEP={summary.get("next_safe_step")}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_MUTATED
[[ "$(stat -c '%Y:%s:%a' "$DB")" == "$DB_MTIME_BEFORE" ]] || fail SOURCE_DATABASE_METADATA_MUTATED
[[ "$(sha256_file "$ROUTE")" == "$ROUTE_SHA_BEFORE" ]] || fail TARGETED_ROUTE_MUTATED
[[ "$(git status --porcelain=v1 --untracked-files=all)" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_MUTATED
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_STOPPED
PRODUCT_PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_AFTER" == "$PRODUCT_PID_BEFORE" ]] || fail PRODUCT_SERVICE_RESTARTED
[[ "$PRODUCT_NRESTARTS_AFTER" == "$PRODUCT_NRESTARTS_BEFORE" ]] || fail PRODUCT_RESTART_COUNT_CHANGED
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'TARGETED_ROUTE_IMMUTABLE=VERIFIED\n'
printf 'REPOSITORY_MUTATION=false\n'
printf 'PANEL_MUTATION=false\n'
printf 'SERVICE_RESTARTED=false\n'
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_AFTER"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_AFTER"
printf 'STATE_DIRECTORY_MODE=%s\n' "$(stat -c '%a' "$STATE_DIR")"
printf 'OUTPUT_MODE=%s\n' "$(stat -c '%a' "$OUTPUT")"
printf 'NETWORK_ACCESS=false\n'
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
CLOSED="$(python3 - "$OUTPUT" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(str(bool(p['summary']['closed_loop_confirmed'])).lower())
PY
)"
printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_04_EXECUTOR_ROUTE_BLOCKER_CLASSIFICATION=SUCCESS\n'
printf 'IDENTITY_OR_OWNERSHIP_INFERENCE=false\n'
printf 'COMPONENT_CLOSED_LOOP_REQUIRES_ACTOR_ATTRIBUTION=true\n'
printf 'CLOSED_LOOP_CONFIRMED=%s\n' "$CLOSED"
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_18=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_17=OPEN\n'
printf 'NEXT_SAFE_STEP=%s\n' "$NEXT_STEP"
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
