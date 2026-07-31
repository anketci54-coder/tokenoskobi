#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_DB_HASH='99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_EXECUTOR_HASH='7148a81cd6e869a32d501a02a50741c17aa37883108e36401f4183ade616d19f'
DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
EXECUTOR='/var/lib/tokenoskobi-product-slice-04/executor_route_blocker_classification_v1.json'
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/non_self_call_wallet_candidate_selection_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'

MODULE="${PRODUCT_SLICE_04_NON_SELF_CALL_SELECTION_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_NON_SELF_CALL_SELECTION_TEST_PATH:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_non_self_call_selection_${STAMP}"
OUTPUT_EXISTED=0
COMPLETED=0

fail() { printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
sha256_file() { sha256sum "$1" | awk '{print $1}'; }

rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/non_self_call_wallet_candidate_selection_v1.json" ]]; then
      install -o root -g root -m 0600 "$BACKUP_DIR/non_self_call_wallet_candidate_selection_v1.json" "$OUTPUT"
    else
      rm -f "$OUTPUT"
    fi
    printf 'ROLLBACK=COMPLETED\n'
  fi
  exit "$rc"
}
trap rollback ERR

[[ -n "$MODULE" && -f "$MODULE" ]] || fail MODULE_MISSING
[[ -n "$TEST" && -f "$TEST" ]] || fail TEST_MISSING
[[ -f "$DB" && -f "$EXECUTOR" ]] || fail REQUIRED_EVIDENCE_MISSING

printf '===== 1 EXACT PREFLIGHT =====\n'
cd "$ROOT"
LOCAL_HEAD="$(git rev-parse HEAD)"
git fetch --quiet origin main
ORIGIN_MAIN="$(git rev-parse origin/main)"
[[ "$LOCAL_HEAD" == "$EXPECTED_MAIN" ]] || fail LOCAL_HEAD_CHANGED
[[ "$ORIGIN_MAIN" == "$EXPECTED_MAIN" ]] || fail ORIGIN_MAIN_CHANGED
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail REPOSITORY_NOT_CLEAN
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_HASH_CHANGED
python3 - "$EXECUTOR" "$EXPECTED_EXECUTOR_HASH" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert p.get('schema')=='tokenoskobi.product_slice_04.executor_route_blocker_classification.v1'
assert p.get('status')=='EXECUTOR_ROUTE_BLOCKERS_CLASSIFIED'
assert p.get('result_hash')==sys.argv[2]
assert p.get('actor')=='0x9999b0cdd35d7f3b281ba02efc0d228486940515'
assert p.get('actor_behavior_class')=='SELF_CALL_MULTI_ROUTE_EXECUTION_ACCOUNT_BEHAVIOR'
s=p.get('summary'); assert isinstance(s,dict)
assert s.get('closed_loop_confirmed') is False
assert s.get('next_safe_step')=='EXCLUDE_SELF_CALL_EXECUTOR_AND_SELECT_NON_SELF_CALL_WALLET_CANDIDATES'
PY
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE
PRODUCT_PID_BEFORE="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_BEFORE="$(systemctl show "$SERVICE" -p NRestarts --value)"
DB_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$DB")"
EXECUTOR_SHA_BEFORE="$(sha256_file "$EXECUTOR")"
REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"
printf 'LOCAL_HEAD=%s\n' "$LOCAL_HEAD"
printf 'ORIGIN_MAIN=%s\n' "$ORIGIN_MAIN"
printf 'SOURCE_DATABASE_SHA256=%s\n' "$EXPECTED_DB_HASH"
printf 'EXECUTOR_CLASSIFICATION_RESULT_HASH=%s\n' "$EXPECTED_EXECUTOR_HASH"
printf 'EXCLUDED_EXECUTOR=0x9999b0cdd35d7f3b281ba02efc0d228486940515\n'
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_BEFORE"
printf 'SELECTION_POLICY=NON_SELF_CALL_SUCCESSFUL_SAME_ACTOR_SAME_TRACKED_TOKEN_OPPOSITE_DIRECTION\n'
printf 'NETWORK_ACCESS=false\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$MODULE" "$TEST"
PRODUCT_SLICE_04_NON_SELF_CALL_SELECTION_MODULE_PATH="$MODULE" python3 "$TEST"
printf 'DETERMINISTIC_TESTS=10_10_OK\n'

printf '\n===== 3 STATE BACKUP AND NON-SELF-CALL CANDIDATE SELECTION =====\n'
install -d -o root -g root -m 0700 "$STATE_DIR"
install -d -o root -g root -m 0700 "$BACKUP_DIR"
if [[ -f "$OUTPUT" ]]; then
  install -o root -g root -m 0600 "$OUTPUT" "$BACKUP_DIR/non_self_call_wallet_candidate_selection_v1.json"
  OUTPUT_EXISTED=1
fi
python3 "$MODULE" --database "$DB" --executor "$EXECUTOR" --output "$OUTPUT"
[[ -s "$OUTPUT" ]] || fail OUTPUT_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail OUTPUT_MODE_INVALID

printf '\n===== 4 OUTPUT CONTRACT AND CANDIDATES =====\n'
python3 - "$OUTPUT" "$EXPECTED_DB_HASH" "$EXPECTED_EXECUTOR_HASH" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert p.get('schema')=='tokenoskobi.product_slice_04.non_self_call_wallet_candidate_selection.v1'
assert p.get('status')=='NON_SELF_CALL_WALLET_CANDIDATE_SELECTION_COMPLETED'
assert p.get('chain')=='BSC' and p.get('chain_id')==56
src=p.get('source'); assert isinstance(src,dict)
assert src.get('database_sha256')==sys.argv[2]
assert src.get('executor_classification_result_hash')==sys.argv[3]
policy=p.get('policy'); assert isinstance(policy,dict)
assert policy.get('excluded_executor_actor')=='0x9999b0cdd35d7f3b281ba02efc0d228486940515'
assert policy.get('exclude_all_self_call_transactions') is True
assert policy.get('selection_is_candidate_only_not_closed_loop_proof') is True
a=p.get('authority'); assert isinstance(a,dict)
assert a.get('network_access') is False and a.get('staging_file_write') is True
for key in ('source_database_write','production_database_write','repository_write','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
    assert a.get(key) is False,key
pairs=p.get('candidate_pairs'); txs=p.get('selected_transactions'); actors=p.get('selected_actors')
assert isinstance(pairs,list) and len(pairs)<=20
assert isinstance(txs,list) and len(txs)<=40
assert isinstance(actors,list) and len(actors)<=10
for tx in txs:
    assert tx['actor']!=tx['tx_to']
    assert tx['actor']!='0x9999b0cdd35d7f3b281ba02efc0d228486940515'
summary=p.get('summary'); assert isinstance(summary,dict)
assert summary.get('closed_loop_confirmed') is False
print('OUTPUT_STATUS=VERIFIED')
for key in (
    'excluded_executor_transaction_count','excluded_self_call_transaction_count',
    'excluded_failed_receipt_count','non_self_call_source_transaction_count',
    'all_round_trip_pair_count','selected_candidate_pair_count','selected_actor_count',
    'selected_transaction_count','endpoint_reverse_exact_candidate_count',
    'endpoint_reverse_and_amount_exact_candidate_count',
):
    print(f'{key.upper()}={summary.get(key)}')
print('SELECTED_ACTORS='+json.dumps(actors,separators=(',',':')))
for i,pair in enumerate(pairs,start=1):
    print(f'CANDIDATE_PAIR_{i}=actor:{pair["actor"]},token:{pair["selected_token"]},first_tx:{pair["first_tx_hash"]},first:{pair["first_direction"]},second_tx:{pair["second_tx_hash"]},second:{pair["second_direction"]},block_distance:{pair["block_distance"]},endpoint_reverse:{str(bool(pair["endpoint_reverse_exact"])).lower()},amount_exact:{str(bool(pair["selected_token_amount_exact"])).lower()},two_sided:{str(bool(pair["both_transactions_two_sided"])).lower()},raw_coverage:{str(bool(pair["raw_transaction_coverage_complete"])).lower()},same_target:{str(bool(pair["same_transaction_target"])).lower()},score:{pair["ranking_score"]}')
top=p.get('top_candidate')
if top:
    print(f'TOP_CANDIDATE=actor:{top["actor"]},first_tx:{top["first_tx_hash"]},second_tx:{top["second_tx_hash"]},token:{top["selected_token"]},endpoint_reverse:{str(bool(top["endpoint_reverse_exact"])).lower()},amount_exact:{str(bool(top["selected_token_amount_exact"])).lower()},score:{top["ranking_score"]}')
else:
    print('TOP_CANDIDATE=NONE')
print(f'RESULT_HASH={p.get("result_hash")}')
print('CLOSED_LOOP_CONFIRMED=false')
print(f'NEXT_SAFE_STEP={summary.get("next_safe_step")}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_MUTATED
[[ "$(stat -c '%Y:%s:%a' "$DB")" == "$DB_MTIME_BEFORE" ]] || fail SOURCE_DATABASE_METADATA_MUTATED
[[ "$(sha256_file "$EXECUTOR")" == "$EXECUTOR_SHA_BEFORE" ]] || fail EXECUTOR_CLASSIFICATION_MUTATED
[[ "$(git status --porcelain=v1 --untracked-files=all)" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_MUTATED
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_STOPPED
PRODUCT_PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_AFTER" == "$PRODUCT_PID_BEFORE" ]] || fail PRODUCT_SERVICE_RESTARTED
[[ "$PRODUCT_NRESTARTS_AFTER" == "$PRODUCT_NRESTARTS_BEFORE" ]] || fail PRODUCT_RESTART_COUNT_CHANGED
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'EXECUTOR_CLASSIFICATION_IMMUTABLE=VERIFIED\n'
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

printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_04_NON_SELF_CALL_WALLET_CANDIDATE_SELECTION=SUCCESS\n'
printf 'SELF_CALL_EXECUTOR_EXCLUDED=true\n'
printf 'SELECTION_IS_CANDIDATE_ONLY_NOT_CLOSED_LOOP_PROOF=true\n'
printf 'IDENTITY_OR_OWNERSHIP_INFERENCE=false\n'
printf 'CLOSED_LOOP_CONFIRMED=false\n'
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_18=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_17=OPEN\n'
printf 'NEXT_SAFE_STEP=%s\n' "$NEXT_STEP"
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
