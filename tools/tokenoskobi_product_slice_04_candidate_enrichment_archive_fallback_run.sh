#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_DB_HASH='99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
PROVIDER="$ROOT/config/era63e_always_on_market_runtime_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/candidate_enrichment_v1.json"

BASE_MODULE="${PRODUCT_SLICE_04_BASE_MODULE_PATH:-}"
WRAPPER_MODULE="${PRODUCT_SLICE_04_WRAPPER_MODULE_PATH:-}"
BASE_TEST="${PRODUCT_SLICE_04_BASE_TEST_PATH:-}"
WRAPPER_TEST="${PRODUCT_SLICE_04_WRAPPER_TEST_PATH:-}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_archive_fallback_${STAMP}"
STATE_DIR_EXISTED=0
OUTPUT_EXISTED=0
COMPLETED=0

fail() {
  printf 'BLOCKED=%s\n' "$1" >&2
  exit 1
}

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/candidate_enrichment_v1.json" ]]; then
      install -m 0600 "$BACKUP_DIR/candidate_enrichment_v1.json" "$OUTPUT"
    else
      rm -f "$OUTPUT" "$OUTPUT.tmp"
    fi
    if [[ "$STATE_DIR_EXISTED" -eq 0 ]]; then
      rmdir "$STATE_DIR" 2>/dev/null || true
    fi
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
[[ -f "$BASE_MODULE" && -f "$WRAPPER_MODULE" && -f "$BASE_TEST" && -f "$WRAPPER_TEST" ]] || fail LOADED_SOURCE_FILE_MISSING

systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE
PID_BEFORE="$(systemctl show "$SERVICE" -p MainPID --value)"
RESTARTS_BEFORE="$(systemctl show "$SERVICE" -p NRestarts --value)"
DB_HASH_BEFORE="$(sha256_file "$DB")"
DB_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$DB")"
REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"

printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_DATABASE_SHA256=%s\n' "$DB_HASH_BEFORE"
printf 'PRODUCT_PID=%s\n' "$PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$RESTARTS_BEFORE"
printf 'CANDIDATE_SCOPE=14_TRANSACTIONS_3_TOKENS\n'
printf 'ARCHIVE_FALLBACK_SCOPE=TOKEN_METADATA_ONLY\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$BASE_MODULE" "$WRAPPER_MODULE" "$BASE_TEST" "$WRAPPER_TEST"
PRODUCT_SLICE_04_MODULE_PATH="$BASE_MODULE" python3 "$BASE_TEST"
PRODUCT_SLICE_04_BASE_MODULE_PATH="$BASE_MODULE" \
PRODUCT_SLICE_04_WRAPPER_MODULE_PATH="$WRAPPER_MODULE" \
python3 "$WRAPPER_TEST"
printf 'DETERMINISTIC_TESTS=13_13_OK\n'

printf '\n===== 3 STATE BACKUP AND BOUNDED READ-ONLY RPC ENRICHMENT =====\n'
mkdir -p "$BACKUP_DIR"
chmod 0700 "$BACKUP_DIR"
if [[ -d "$STATE_DIR" ]]; then
  STATE_DIR_EXISTED=1
fi
install -d -m 0700 "$STATE_DIR"
if [[ -f "$OUTPUT" ]]; then
  OUTPUT_EXISTED=1
  cp -a "$OUTPUT" "$BACKUP_DIR/candidate_enrichment_v1.json"
fi

PRODUCT_SLICE_04_BASE_MODULE_PATH="$BASE_MODULE" \
python3 "$WRAPPER_MODULE" \
  --database "$DB" \
  --provider "$PROVIDER" \
  --output "$OUTPUT"

[[ -f "$OUTPUT" && -s "$OUTPUT" ]] || fail OUTPUT_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail OUTPUT_MODE_INVALID

printf '\n===== 4 OUTPUT CONTRACT AND CANDIDATE EVIDENCE =====\n'
OUTPUT="$OUTPUT" EXPECTED_DB_HASH="$EXPECTED_DB_HASH" python3 - <<'PY'
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

path = Path(os.environ['OUTPUT'])
data = json.loads(path.read_text(encoding='utf-8'))
assert data['schema'] == 'tokenoskobi.product_slice_04.candidate_enrichment.v1'
assert data['status'] == 'CANDIDATE_INPUT_AND_TOKEN_METADATA_ENRICHMENT_VERIFIED_WITH_ARCHIVE_FALLBACK_POLICY'
assert data['chain'] == 'BSC' and data['chain_id'] == 56
assert data['source']['database_sha256'] == os.environ['EXPECTED_DB_HASH']
assert data['source']['candidate_transaction_count'] == 14
assert data['source']['tracked_token_count'] == 3

transactions = data['transactions']
metadata = data['token_metadata']
assert len(transactions) == 14
assert len({row['tx_hash'] for row in transactions}) == 14
assert len(metadata) == 3
assert len({row['token_address'] for row in metadata}) == 3

allowed_modes = {
    'HISTORICAL_BLOCK_VERIFIED',
    'LATEST_STATE_FALLBACK_ARCHIVE_UNAVAILABLE',
}
for row in metadata:
    assert row['metadata_temporal_mode'] in allowed_modes
    assert 0 <= int(row['decimals']) <= 36
    assert str(row['symbol']).strip()
    assert str(row['name']).strip()
    assert row['provider_hosts']
    if row['archive_fallback_used']:
        assert row['effective_block_tag'] == 'latest'
        assert row['historical_state_verified'] is False
        assert len(row['historical_error_hash']) == 64
    else:
        assert row['historical_state_verified'] is True

summary = data['summary']
policy = data['metadata_temporal_policy']
assert summary['transaction_input_coverage'] == 14
assert summary['token_metadata_coverage'] == 3
assert summary['token_amount_normalization_ready'] is True
assert summary['swap_direction_classified'] is False
assert summary['router_pool_identity_verified'] is False
assert summary['closed_loop_confirmed'] is False
assert policy['fallback_allowed_only_for_archive_state_unavailable_errors'] is True
assert policy['historical_transaction_and_receipt_identity_preserved'] is True
assert policy['historical_metadata_verified_count'] + policy['latest_metadata_fallback_count'] == 3

authority = data['authority']
assert authority['network_access'] is True
assert authority['staging_file_write'] is True
for key in (
    'source_database_write', 'production_database_write', 'repository_write',
    'panel_mutation', 'service_mutation', 'timer_mutation', 'paper_trade',
    'live_trade', 'wallet', 'signing', 'order_create', 'broadcast',
):
    assert authority[key] is False, key

expected_hash = data.pop('result_hash')
raw = json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(',', ':'), default=str)
assert hashlib.sha256(raw.encode('utf-8')).hexdigest() == expected_hash

print(f'OUTPUT_STATUS=VERIFIED')
print(f'HISTORICAL_METADATA_VERIFIED_COUNT={policy["historical_metadata_verified_count"]}')
print(f'LATEST_METADATA_ARCHIVE_FALLBACK_COUNT={policy["latest_metadata_fallback_count"]}')
print(f'TWO_SIDED_ACTOR_FLOW_COUNT={summary["two_sided_actor_flow_count"]}')
for index, row in enumerate(metadata, start=1):
    print(
        f'TOKEN_METADATA_{index}=address:{row["token_address"]},symbol:{row["symbol"]},'
        f'name:{row["name"]},decimals:{row["decimals"]},mode:{row["metadata_temporal_mode"]}'
    )
for index, row in enumerate(transactions, start=1):
    flow = row['actor_flow']
    print(
        f'CANDIDATE_{index}=tx:{row["tx_hash"]},block:{row["block_number"]},'
        f'actor:{row["actor"]},tx_to:{row["tx_to"] or "CONTRACT_CREATION"},'
        f'selector:{row["selector"]},input_bytes:{row["input_bytes"]},'
        f'two_sided:{str(flow["two_sided_actor_flow"]).lower()}'
    )
print('SELECTOR_COUNTS=' + json.dumps(summary['selector_counts'], sort_keys=True, separators=(',', ':')))
print('TX_TO_COUNTS=' + json.dumps(summary['tx_to_counts'], sort_keys=True, separators=(',', ':')))
print(f'RESULT_HASH={expected_hash}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
DB_HASH_AFTER="$(sha256_file "$DB")"
DB_MTIME_AFTER="$(stat -c '%Y:%s:%a' "$DB")"
REPO_STATUS_AFTER="$(git status --porcelain=v1 --untracked-files=all)"
PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
RESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"

[[ "$DB_HASH_AFTER" == "$DB_HASH_BEFORE" ]] || fail SOURCE_DATABASE_MUTATED
[[ "$DB_MTIME_AFTER" == "$DB_MTIME_BEFORE" ]] || fail SOURCE_DATABASE_METADATA_CHANGED
[[ "$REPO_STATUS_AFTER" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_MUTATED
[[ "$PID_AFTER" == "$PID_BEFORE" ]] || fail PRODUCT_SERVICE_RESTARTED
[[ "$RESTARTS_AFTER" == "$RESTARTS_BEFORE" ]] || fail PRODUCT_SERVICE_RESTART_COUNT_CHANGED

printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'REPOSITORY_MUTATION=false\n'
printf 'PANEL_MUTATION=false\n'
printf 'SERVICE_RESTARTED=false\n'
printf 'PRODUCT_PID=%s\n' "$PID_AFTER"
printf 'PRODUCT_NRESTARTS=%s\n' "$RESTARTS_AFTER"
printf 'STATE_DIRECTORY_MODE=700\n'
printf 'OUTPUT_MODE=600\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'

COMPLETED=1
trap - ERR

printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_04_CANDIDATE_ENRICHMENT=SUCCESS\n'
printf 'CANDIDATE_TRANSACTION_INPUT_COVERAGE=14_14_VERIFIED\n'
printf 'TOKEN_METADATA_COVERAGE=3_3_VERIFIED\n'
printf 'ARCHIVE_FALLBACK_POLICY=FAIL_CLOSED_TOKEN_METADATA_ONLY\n'
printf 'HISTORICAL_TRANSACTION_RECEIPT_IDENTITY=PRESERVED\n'
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'ISSUE_17=OPEN\n'
printf 'NEXT_SAFE_STEP=ALLOWLISTED_DEX_ROUTER_POOL_AND_SWAP_EVENT_DECODE\n'
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
