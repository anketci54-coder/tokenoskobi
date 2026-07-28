#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_DB_HASH='99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_SELECTION_HASH='a6f4779363a0993cab9f82510eee5139a7f7fabc7996701ef2bb1bf4cf1906ba'

DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
PROVIDER="$ROOT/config/era63e_always_on_market_runtime_v1.json"
SELECTION='/var/lib/tokenoskobi-product-slice-04/non_self_call_wallet_candidate_selection_v1.json'
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/targeted_historical_reverse_scan_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'

MODULE="${PRODUCT_SLICE_04_HISTORICAL_REVERSE_SCAN_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_HISTORICAL_REVERSE_SCAN_TEST_PATH:-}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_targeted_historical_reverse_scan_${STAMP}"
OUTPUT_EXISTED=0
COMPLETED=0

fail() {
  printf 'BLOCKED=%s\n' "$1" >&2
  exit 1
}

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

repo_state() {
  {
    git status --porcelain=v1 --untracked-files=all
    git diff --binary
    git diff --cached --binary
  } | sha256sum | awk '{print $1}'
}

rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/targeted_historical_reverse_scan_v1.json" ]]; then
      install -o root -g root -m 0600 \
        "$BACKUP_DIR/targeted_historical_reverse_scan_v1.json" \
        "$OUTPUT"
    else
      rm -f "$OUTPUT"
    fi
    printf 'ROLLBACK=COMPLETED\n'
  fi
  exit "$rc"
}
trap rollback ERR

cd "$ROOT"

printf '\n===== 1 EXACT PREFLIGHT =====\n'

[[ -n "$MODULE" && -f "$MODULE" ]] || fail 'MODULE_MISSING'
[[ -n "$TEST" && -f "$TEST" ]] || fail 'TEST_MISSING'
[[ -f "$DB" ]] || fail 'SOURCE_DATABASE_MISSING'
[[ -f "$PROVIDER" ]] || fail 'PROVIDER_CONFIG_MISSING'
[[ -f "$SELECTION" ]] || fail 'SELECTION_EVIDENCE_MISSING'

LOCAL_HEAD="$(git rev-parse HEAD)"
git fetch --quiet origin main
ORIGIN_MAIN="$(git rev-parse origin/main)"
[[ "$LOCAL_HEAD" == "$EXPECTED_MAIN" ]] || fail 'LOCAL_HEAD_CHANGED'
[[ "$ORIGIN_MAIN" == "$EXPECTED_MAIN" ]] || fail 'ORIGIN_MAIN_CHANGED'
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail 'REPOSITORY_NOT_CLEAN'

DB_HASH_BEFORE="$(sha256_file "$DB")"
[[ "$DB_HASH_BEFORE" == "$EXPECTED_DB_HASH" ]] || fail 'SOURCE_DATABASE_HASH_CHANGED'

python3 - "$SELECTION" "$EXPECTED_SELECTION_HASH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected_hash = sys.argv[2]
payload = json.loads(path.read_text(encoding='utf-8'))
assert payload['schema'] == 'tokenoskobi.product_slice_04.non_self_call_wallet_candidate_selection.v1'
assert payload['status'] == 'NON_SELF_CALL_WALLET_CANDIDATE_SELECTION_COMPLETED'
assert payload['result_hash'] == expected_hash
summary = payload['summary']
assert summary['non_self_call_source_transaction_count'] == 101
assert summary['all_round_trip_pair_count'] == 0
assert summary['selected_candidate_pair_count'] == 0
assert summary['closed_loop_confirmed'] is False
assert summary['next_safe_step'] == 'CURRENT_DATASET_HAS_NO_NON_SELF_CALL_ROUND_TRIP_CANDIDATE_EXTEND_HISTORICAL_SCAN'
PY

systemctl is-active --quiet "$SERVICE" || fail 'PRODUCT_SERVICE_NOT_ACTIVE'
PRODUCT_PID_BEFORE="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_BEFORE="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_BEFORE" =~ ^[0-9]+$ && "$PRODUCT_PID_BEFORE" -gt 0 ]] || fail 'PRODUCT_PID_INVALID'
[[ "$PRODUCT_NRESTARTS_BEFORE" =~ ^[0-9]+$ ]] || fail 'PRODUCT_NRESTARTS_INVALID'

REPO_STATE_BEFORE="$(repo_state)"

printf 'LOCAL_HEAD=%s\n' "$LOCAL_HEAD"
printf 'ORIGIN_MAIN=%s\n' "$ORIGIN_MAIN"
printf 'SOURCE_DATABASE_SHA256=%s\n' "$DB_HASH_BEFORE"
printf 'NON_SELF_CALL_SELECTION_RESULT_HASH=%s\n' "$EXPECTED_SELECTION_HASH"
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_BEFORE"
printf 'SCAN_SCOPE=16_ANCHORS_12_ACTORS_65536_OLDER_BLOCKS_2048_BLOCK_CHUNKS\n'
printf 'RPC_SCOPE=ETH_CHAIN_ID_ETH_GET_LOGS_TX_RECEIPT_BLOCK_READ_ONLY\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$MODULE" "$TEST"
PRODUCT_SLICE_04_HISTORICAL_REVERSE_SCAN_MODULE_PATH="$MODULE" \
  python3 "$TEST"
printf 'DETERMINISTIC_TESTS=10_10_OK\n'

printf '\n===== 3 STATE BACKUP AND TARGETED HISTORICAL REVERSE SCAN =====\n'
install -d -o root -g root -m 0700 "$STATE_DIR"
install -d -o root -g root -m 0700 "$BACKUP_DIR"
if [[ -f "$OUTPUT" ]]; then
  install -o root -g root -m 0600 "$OUTPUT" \
    "$BACKUP_DIR/targeted_historical_reverse_scan_v1.json"
  OUTPUT_EXISTED=1
fi

python3 "$MODULE" \
  --database "$DB" \
  --provider "$PROVIDER" \
  --selection "$SELECTION" \
  --output "$OUTPUT"

printf '\n===== 4 OUTPUT CONTRACT AND REVERSE CANDIDATES =====\n'
python3 - "$OUTPUT" "$EXPECTED_DB_HASH" "$EXPECTED_SELECTION_HASH" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected_db_hash = sys.argv[2]
expected_selection_hash = sys.argv[3]
payload = json.loads(path.read_text(encoding='utf-8'))

assert payload['schema'] == 'tokenoskobi.product_slice_04.targeted_historical_reverse_scan.v1'
assert payload['status'] == 'TARGETED_HISTORICAL_REVERSE_SCAN_COMPLETED'
assert payload['chain'] == 'BSC'
assert payload['chain_id'] == 56
assert payload['source']['database_sha256'] == expected_db_hash
assert payload['source']['selection_result_hash'] == expected_selection_hash
assert payload['source']['source_event_count'] == 367
assert payload['source']['source_receipt_count'] == 277
assert payload['source']['eligible_non_self_call_transaction_count'] == 101
assert len(payload['source']['tracked_tokens']) == 3

policy = payload['policy']
assert policy['scan_direction'] == 'OLDER_ADJACENT_BLOCKS_ONLY'
assert policy['scan_block_span'] == 65536
assert policy['log_chunk_size'] == 2048
assert policy['maximum_anchors'] == 16
assert policy['maximum_actors'] == 12
assert policy['maximum_rpc_requests'] == 700
assert policy['indexed_transfer_topic_filter_required'] is True
assert policy['missing_opposite_direction_only'] is True
assert policy['successful_receipt_required'] is True
assert policy['tx_from_must_equal_actor'] is True
assert policy['tx_to_must_not_equal_actor'] is True
assert policy['selection_is_candidate_only_not_closed_loop_proof'] is True
assert policy['identity_or_ownership_inference_allowed'] is False

authority = payload['authority']
assert authority['network_access'] is True
assert authority['staging_file_write'] is True
for key in (
    'source_database_write',
    'production_database_write',
    'repository_write',
    'panel_mutation',
    'service_mutation',
    'timer_mutation',
    'paper_trade',
    'live_trade',
    'wallet',
    'signing',
    'order_create',
    'broadcast',
):
    assert authority[key] is False, key

scan_range = payload['scan_range']
assert scan_range['block_count'] == 65536
assert scan_range['end_block'] - scan_range['start_block'] + 1 == 65536
assert scan_range['end_block'] == scan_range['minimum_existing_source_block'] - 1

summary = payload['summary']
assert 1 <= summary['anchor_count'] <= 16
assert 1 <= summary['anchor_actor_count'] <= 12
assert summary['raw_indexed_transfer_hit_count'] <= 500
assert summary['distinct_discovered_transaction_hash_count'] <= 40
assert summary['closed_loop_confirmed'] is False
assert payload['rpc']['request_count'] <= 700
assert len(payload['candidate_pairs']) <= 40
assert payload['top_candidate'] == (payload['candidate_pairs'][0] if payload['candidate_pairs'] else None)

for anchor in payload['anchors']:
    assert anchor['missing_direction'] in {'IN', 'OUT'}
    assert anchor['observed_direction'] in {'IN', 'OUT'}
    assert anchor['missing_direction'] != anchor['observed_direction']
    assert anchor['actor'] != policy['executor_actor_excluded']

for tx in payload['discovered_transactions']:
    assert tx['actor'] != tx['tx_to']
    assert tx['single_endpoint_pair'] in {True, False}
    assert tx['two_sided_actor_flow'] in {True, False}

for pair in payload['candidate_pairs']:
    assert pair['candidate_only'] is True
    assert pair['closed_loop_confirmed'] is False
    assert pair['direction_opposite_exact'] is True
    if pair['position_amount_exact']:
        assert pair['endpoint_reverse_exact'] is True

stored_hash = payload.pop('result_hash')
raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(',', ':'), default=str)
assert stored_hash == hashlib.sha256(raw.encode('utf-8')).hexdigest()

mode = os.stat(path).st_mode & 0o777
assert mode == 0o600
dir_mode = os.stat(path.parent).st_mode & 0o777
assert dir_mode == 0o700

print('OUTPUT_STATUS=VERIFIED')
print(f'SCAN_START_BLOCK={scan_range["start_block"]}')
print(f'SCAN_END_BLOCK={scan_range["end_block"]}')
print(f'SCAN_BLOCK_COUNT={scan_range["block_count"]}')
for key in (
    'anchor_count',
    'anchor_actor_count',
    'raw_indexed_transfer_hit_count',
    'distinct_discovered_transaction_hash_count',
    'validated_discovered_transaction_count',
    'opposite_direction_candidate_count',
    'endpoint_reverse_exact_candidate_count',
    'endpoint_reverse_and_position_amount_exact_candidate_count',
):
    print(f'{key.upper()}={summary[key]}')
print(f'RPC_REQUEST_COUNT={payload["rpc"]["request_count"]}')
print(f'RPC_ERROR_COUNT={payload["rpc"]["error_count"]}')
print(f'RESULT_HASH={stored_hash}')
print('CLOSED_LOOP_CONFIRMED=false')
print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
DB_HASH_AFTER="$(sha256_file "$DB")"
[[ "$DB_HASH_AFTER" == "$DB_HASH_BEFORE" ]] || fail 'SOURCE_DATABASE_MUTATED'

REPO_STATE_AFTER="$(repo_state)"
[[ "$REPO_STATE_AFTER" == "$REPO_STATE_BEFORE" ]] || fail 'REPOSITORY_MUTATED'

systemctl is-active --quiet "$SERVICE" || fail 'PRODUCT_SERVICE_STOPPED'
PRODUCT_PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_AFTER" == "$PRODUCT_PID_BEFORE" ]] || fail 'PRODUCT_SERVICE_PID_CHANGED'
[[ "$PRODUCT_NRESTARTS_AFTER" == "$PRODUCT_NRESTARTS_BEFORE" ]] || fail 'PRODUCT_SERVICE_RESTART_COUNT_CHANGED'

[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail 'STATE_DIRECTORY_MODE_INVALID'
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail 'OUTPUT_MODE_INVALID'

printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'NON_SELF_CALL_SELECTION_IMMUTABLE=VERIFIED\n'
printf 'REPOSITORY_MUTATION=false\n'
printf 'PANEL_MUTATION=false\n'
printf 'SERVICE_RESTARTED=false\n'
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_AFTER"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_AFTER"
printf 'STATE_DIRECTORY_MODE=700\n'
printf 'OUTPUT_MODE=600\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'

COMPLETED=1
trap - ERR

printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_04_TARGETED_HISTORICAL_REVERSE_SCAN=SUCCESS\n'
printf 'INDEXED_TRANSFER_FILTER=true\n'
printf 'MISSING_OPPOSITE_DIRECTION_ONLY=true\n'
printf 'SELECTION_IS_CANDIDATE_ONLY_NOT_CLOSED_LOOP_PROOF=true\n'
printf 'IDENTITY_OR_OWNERSHIP_INFERENCE=false\n'
printf 'CLOSED_LOOP_CONFIRMED=false\n'
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_18=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_17=OPEN\n'
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
