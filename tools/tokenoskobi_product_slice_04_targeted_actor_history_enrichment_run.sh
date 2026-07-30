#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_DB_HASH='99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_ENRICHMENT_HASH='34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
EXPECTED_SELECTION_HASH='e19adf42373e643a27c4c8f23815672ab42598af012d887a9a17398e92f19c61'
DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
PROVIDER="$ROOT/config/era63e_always_on_market_runtime_v1.json"
ENRICHMENT='/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json'
SELECTION='/var/lib/tokenoskobi-product-slice-04/first_swap_chain_selection_v1.json'
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/targeted_actor_history_enrichment_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'
MODULE="${PRODUCT_SLICE_04_TARGETED_HISTORY_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_TARGETED_HISTORY_TEST_PATH:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_targeted_history_${STAMP}"
OUTPUT_EXISTED=0
COMPLETED=0

fail() { printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
sha256_file() { sha256sum "$1" | awk '{print $1}'; }
rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/targeted_actor_history_enrichment_v1.json" ]]; then
      install -o root -g root -m 0600 "$BACKUP_DIR/targeted_actor_history_enrichment_v1.json" "$OUTPUT"
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
[[ -f "$DB" && -s "$DB" ]] || fail SOURCE_DATABASE_MISSING
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_HASH_CHANGED
[[ -f "$PROVIDER" && -s "$PROVIDER" ]] || fail PROVIDER_CONFIG_MISSING
[[ -f "$ENRICHMENT" && -s "$ENRICHMENT" ]] || fail ENRICHMENT_MISSING
[[ -f "$SELECTION" && -s "$SELECTION" ]] || fail SELECTION_MISSING
[[ -n "$MODULE" && -f "$MODULE" ]] || fail MODULE_MISSING
[[ -n "$TEST" && -f "$TEST" ]] || fail TEST_MISSING
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE

PRODUCT_PID_BEFORE="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_BEFORE="$(systemctl show "$SERVICE" -p NRestarts --value)"
DB_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$DB")"
ENRICHMENT_SHA_BEFORE="$(sha256_file "$ENRICHMENT")"
SELECTION_SHA_BEFORE="$(sha256_file "$SELECTION")"
REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"

python3 - "$ENRICHMENT" "$SELECTION" "$EXPECTED_ENRICHMENT_HASH" "$EXPECTED_SELECTION_HASH" <<'PY'
import json
import sys
from pathlib import Path

def require(condition, code):
    if not condition:
        print(f'BLOCKED={code}', file=sys.stderr)
        raise SystemExit(1)

enrichment = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
selection = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
require(enrichment.get('result_hash') == sys.argv[3], 'ENRICHMENT_RESULT_HASH_CHANGED')
require(selection.get('result_hash') == sys.argv[4], 'SELECTION_RESULT_HASH_CHANGED')
require(selection.get('status') == 'STRICT_FACTORY_AND_SWAP_CHAIN_SELECTION_COMPLETED', 'SELECTION_STATUS_INVALID')
summary = selection.get('summary')
require(isinstance(summary, dict), 'SELECTION_SUMMARY_MISSING')
require(summary.get('closed_loop_confirmed') is False, 'SELECTION_ALREADY_CLOSED')
require(summary.get('next_safe_step') == 'TARGETED_SAME_ACTOR_HISTORY_ENRICHMENT_FOR_CLOSED_LOOP', 'SELECTION_NEXT_STEP_INVALID')
PY

printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_DATABASE_SHA256=%s\n' "$(sha256_file "$DB")"
printf 'ENRICHMENT_RESULT_HASH=%s\n' "$EXPECTED_ENRICHMENT_HASH"
printf 'SELECTION_RESULT_HASH=%s\n' "$EXPECTED_SELECTION_HASH"
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_BEFORE"
printf 'TARGET_SCOPE_POLICY=SAME_ACTOR_SAME_TRACKED_TOKEN_OPPOSITE_NET_DIRECTIONS_MAX_10_ACTORS_MAX_80_TRANSACTIONS\n'
printf 'RPC_SCOPE=ETH_CHAIN_ID_PLUS_MISSING_ETH_GET_TRANSACTION_BY_HASH_ONLY\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$MODULE" "$TEST"
PRODUCT_SLICE_04_TARGETED_HISTORY_MODULE_PATH="$MODULE" python3 "$TEST"
printf 'DETERMINISTIC_TESTS=10_10_OK\n'

printf '\n===== 3 STATE BACKUP AND BOUNDED TARGETED HISTORY ENRICHMENT =====\n'
install -d -o root -g root -m 0700 "$STATE_DIR"
install -d -o root -g root -m 0700 "$BACKUP_DIR"
if [[ -f "$OUTPUT" ]]; then
  OUTPUT_EXISTED=1
  install -o root -g root -m 0600 "$OUTPUT" "$BACKUP_DIR/targeted_actor_history_enrichment_v1.json"
fi
python3 "$MODULE" --database "$DB" --provider "$PROVIDER" --enrichment "$ENRICHMENT" --selection "$SELECTION" --output "$OUTPUT"
[[ -f "$OUTPUT" && -s "$OUTPUT" ]] || fail TARGETED_HISTORY_OUTPUT_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail OUTPUT_MODE_INVALID

printf '\n===== 4 OUTPUT CONTRACT AND TARGETED ACTOR HISTORY =====\n'
python3 - "$OUTPUT" "$EXPECTED_DB_HASH" "$EXPECTED_ENRICHMENT_HASH" "$EXPECTED_SELECTION_HASH" <<'PY'
import json
import sys
from pathlib import Path

p = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert p.get('schema') == 'tokenoskobi.product_slice_04.targeted_actor_history_enrichment.v1'
assert p.get('status') == 'TARGETED_SAME_ACTOR_HISTORY_ENRICHMENT_COMPLETED'
assert p.get('chain') == 'BSC' and p.get('chain_id') == 56
source = p.get('source'); assert isinstance(source, dict)
assert source.get('database_sha256') == sys.argv[2]
assert source.get('candidate_enrichment_result_hash') == sys.argv[3]
assert source.get('first_swap_chain_selection_result_hash') == sys.argv[4]
authority = p.get('authority'); assert isinstance(authority, dict)
assert authority.get('network_access') is True and authority.get('staging_file_write') is True
for key in ('source_database_write','production_database_write','repository_write','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
    assert authority.get(key) is False, key
summary = p.get('summary'); assert isinstance(summary, dict)
actors = p.get('target_actors'); pairs = p.get('round_trip_pairs'); transactions = p.get('transactions')
assert isinstance(actors, list) and 1 <= len(actors) <= 10
assert isinstance(pairs, list) and 1 <= len(pairs) <= 100
assert isinstance(transactions, list) and 1 <= len(transactions) <= 80
assert summary.get('target_actor_count') == len(actors)
assert summary.get('round_trip_pair_count') == len(pairs)
assert summary.get('target_transaction_count') == len(transactions)
assert summary.get('transaction_input_coverage') == len(transactions)
assert summary.get('closed_loop_confirmed') is False
assert summary.get('next_safe_step') == 'TARGETED_SWAP_POOL_DECODE_AND_STRICT_CLOSED_LOOP_RESELECTION'
print('OUTPUT_STATUS=VERIFIED')
print(f'TARGET_ACTOR_COUNT={len(actors)}')
print(f'ROUND_TRIP_PAIR_COUNT={len(pairs)}')
print(f'TARGET_TRANSACTION_COUNT={len(transactions)}')
print(f'TRANSACTION_INPUT_COVERAGE={summary.get("transaction_input_coverage")}_OF_{len(transactions)}')
print(f'TWO_SIDED_ACTOR_FLOW_TRANSACTION_COUNT={summary.get("two_sided_actor_flow_transaction_count")}')
print(f'DATABASE_RAW_TRANSACTION_COUNT={p["rpc"].get("database_raw_transaction_count")}')
print(f'RPC_RAW_TRANSACTION_COUNT={p["rpc"].get("rpc_raw_transaction_count")}')
print(f'RPC_REQUEST_COUNT={p["rpc"].get("request_count")}')
print(f'RPC_ERROR_COUNT={p["rpc"].get("error_count")}')
print('TARGET_ACTORS=' + json.dumps(actors, separators=(',', ':')))
for index, pair in enumerate(pairs, start=1):
    print(f'ROUND_TRIP_PAIR_{index}=actor:{pair["actor"]},token:{pair["token_address"]},first_tx:{pair["first_tx_hash"]},first:{pair["first_direction"]},second_tx:{pair["second_tx_hash"]},second:{pair["second_direction"]},block_distance:{pair["block_distance"]}')
for index, tx in enumerate(transactions, start=1):
    print(f'TARGET_TX_{index}=tx:{tx["tx_hash"]},block:{tx["block_number"]},actor:{tx["actor"]},tx_to:{tx["tx_to"]},selector:{tx["selector"]},source:{tx["raw_transaction_source"]},two_sided:{str(bool(tx["actor_flow"].get("two_sided_actor_flow"))).lower()}')
print('SELECTOR_COUNTS=' + json.dumps(summary.get('selector_counts'), sort_keys=True, separators=(',', ':')))
print(f'RESULT_HASH={p.get("result_hash")}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_MUTATED
[[ "$(stat -c '%Y:%s:%a' "$DB")" == "$DB_MTIME_BEFORE" ]] || fail SOURCE_DATABASE_METADATA_MUTATED
[[ "$(sha256_file "$ENRICHMENT")" == "$ENRICHMENT_SHA_BEFORE" ]] || fail ENRICHMENT_MUTATED
[[ "$(sha256_file "$SELECTION")" == "$SELECTION_SHA_BEFORE" ]] || fail SELECTION_MUTATED
[[ "$(git status --porcelain=v1 --untracked-files=all)" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_MUTATED
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_STOPPED
PRODUCT_PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_AFTER" == "$PRODUCT_PID_BEFORE" ]] || fail PRODUCT_SERVICE_RESTARTED
[[ "$PRODUCT_NRESTARTS_AFTER" == "$PRODUCT_NRESTARTS_BEFORE" ]] || fail PRODUCT_RESTART_COUNT_CHANGED
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'ENRICHMENT_IMMUTABLE=VERIFIED\n'
printf 'SELECTION_IMMUTABLE=VERIFIED\n'
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
printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_04_TARGETED_ACTOR_HISTORY_ENRICHMENT=SUCCESS\n'
printf 'TARGET_SCOPE=BOUNDED_SAME_ACTOR_OPPOSITE_TRACKED_TOKEN_HISTORY\n'
printf 'TRANSACTION_INPUT_COVERAGE=VERIFIED\n'
printf 'ROUTER_IDENTITY_VERIFIED=false\n'
printf 'CLOSED_LOOP_CONFIRMED=false\n'
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_18=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_17=OPEN\n'
printf 'NEXT_SAFE_STEP=TARGETED_SWAP_POOL_DECODE_AND_STRICT_CLOSED_LOOP_RESELECTION\n'
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
