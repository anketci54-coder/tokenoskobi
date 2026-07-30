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
MODULE="${PRODUCT_SLICE_04_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_TEST_PATH:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_candidate_enrichment_${STAMP}"
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
  trap - ERR INT TERM
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/candidate_enrichment_v1.json" ]]; then
      install -m 0600 "$BACKUP_DIR/candidate_enrichment_v1.json" "$OUTPUT"
    else
      rm -f "$OUTPUT" "$OUTPUT.tmp"
    fi
    printf 'ROLLBACK=COMPLETED\n'
  fi
  exit "$rc"
}
trap rollback ERR INT TERM

printf '\n===== 1 EXACT PREFLIGHT =====\n'
cd "$ROOT"
[[ "$(git branch --show-current)" == 'main' ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$EXPECTED_MAIN" ]] || fail LOCAL_HEAD_CHANGED
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail WORKTREE_NOT_CLEAN
git fetch --quiet origin main
[[ "$(git rev-parse origin/main)" == "$EXPECTED_MAIN" ]] || fail ORIGIN_MAIN_CHANGED
[[ -n "$MODULE" && -f "$MODULE" ]] || fail MODULE_NOT_MATERIALIZED
[[ -n "$TEST" && -f "$TEST" ]] || fail TEST_NOT_MATERIALIZED
[[ -f "$DB" && -s "$DB" ]] || fail SOURCE_DATABASE_MISSING
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_HASH_CHANGED
[[ -f "$PROVIDER" ]] || fail PROVIDER_CONFIG_MISSING
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE

REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"
DB_HASH_BEFORE="$(sha256_file "$DB")"
DB_STAT_BEFORE="$(stat -c '%Y:%s:%a:%U:%G' "$DB")"
SERVICE_PID_BEFORE="$(systemctl show -p MainPID --value "$SERVICE")"
SERVICE_NRESTARTS_BEFORE="$(systemctl show -p NRestarts --value "$SERVICE")"

printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_DATABASE_SHA256=%s\n' "$DB_HASH_BEFORE"
printf 'PRODUCT_PID=%s\n' "$SERVICE_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$SERVICE_NRESTARTS_BEFORE"
printf 'CANDIDATE_SCOPE=14_TRANSACTIONS_3_TOKENS\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$MODULE" "$TEST"
PRODUCT_SLICE_04_MODULE_PATH="$MODULE" python3 "$TEST"
printf 'DETERMINISTIC_TESTS=8_8_OK\n'

printf '\n===== 3 STATE BACKUP AND BOUNDED READ-ONLY RPC ENRICHMENT =====\n'
mkdir -p "$BACKUP_DIR"
chmod 0700 "$BACKUP_DIR"
mkdir -p "$STATE_DIR"
chmod 0700 "$STATE_DIR"
if [[ -f "$OUTPUT" ]]; then
  OUTPUT_EXISTED=1
  install -m 0600 "$OUTPUT" "$BACKUP_DIR/candidate_enrichment_v1.json"
fi

python3 "$MODULE" --database "$DB" --provider "$PROVIDER" --output "$OUTPUT"
[[ -f "$OUTPUT" && -s "$OUTPUT" ]] || fail ENRICHMENT_OUTPUT_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail OUTPUT_MODE_INVALID

printf '\n===== 4 ENRICHMENT EVIDENCE =====\n'
OUTPUT="$OUTPUT" EXPECTED_DB_HASH="$EXPECTED_DB_HASH" python3 - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

path = Path(os.environ['OUTPUT'])
expected_db_hash = os.environ['EXPECTED_DB_HASH']
data = json.loads(path.read_text(encoding='utf-8'))
assert data['schema'] == 'tokenoskobi.product_slice_04.candidate_enrichment.v1'
assert data['status'] == 'CANDIDATE_INPUT_AND_TOKEN_METADATA_ENRICHMENT_VERIFIED'
assert data['chain_id'] == 56
assert data['source']['database_sha256'] == expected_db_hash
assert data['source']['candidate_transaction_count'] == 14
assert data['source']['tracked_token_count'] == 3
assert data['summary']['transaction_input_coverage'] == 14
assert data['summary']['token_metadata_coverage'] == 3
assert data['summary']['swap_direction_classified'] is False
assert data['summary']['router_pool_identity_verified'] is False
assert data['summary']['closed_loop_confirmed'] is False
assert data['summary']['cex_evidence_status'] == 'UNVERIFIED_OR_UNAVAILABLE'
assert len(data['transactions']) == 14
assert len({row['tx_hash'] for row in data['transactions']}) == 14
assert len(data['token_metadata']) == 3
assert len({row['token_address'] for row in data['token_metadata']}) == 3
for row in data['transactions']:
    assert row['input'].startswith('0x')
    assert row['selector'].startswith('0x')
    assert row['receipt_status'] in (0, 1)
    assert isinstance(row['actor_flow']['token_flows'], list)
for row in data['token_metadata']:
    assert 0 <= row['decimals'] <= 36
    assert row['symbol'] and row['name']
a = data['authority']
assert a['network_access'] is True
assert a['staging_file_write'] is True
for key in ('source_database_write','production_database_write','repository_write','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
    assert a[key] is False, key

print(f"ENRICHMENT_RESULT_HASH={data['result_hash']}")
print(f"RPC_REQUEST_COUNT={data['rpc']['request_count']}")
print(f"RPC_ERROR_COUNT={data['rpc']['error_count']}")
print(f"TWO_SIDED_ACTOR_FLOW_COUNT={data['summary']['two_sided_actor_flow_count']}")
for index, row in enumerate(data['token_metadata'], start=1):
    print(f"TOKEN_METADATA_{index}=address:{row['token_address']},symbol:{row['symbol']},name:{row['name']},decimals:{row['decimals']},block:{row['block_number']}")
for index, row in enumerate(data['transactions'], start=1):
    flow = row['actor_flow']
    flow_text = '|'.join(f"{item['symbol']}:{item['direction']}:{item['net_normalized']}" for item in flow['token_flows']) or 'NO_DIRECT_ACTOR_FLOW'
    print(f"CANDIDATE_{index}=tx:{row['tx_hash']},block:{row['block_number']},actor:{row['actor']},tx_to:{row['tx_to'] or 'CONTRACT_CREATION'},selector:{row['selector']},input_bytes:{row['input_bytes']},two_sided:{str(flow['two_sided_actor_flow']).lower()},flow:{flow_text}")
for selector, count in sorted(data['summary']['selector_counts'].items(), key=lambda item: (-item[1], item[0])):
    print(f"SELECTOR_COUNT=selector:{selector},count:{count}")
for address, count in sorted(data['summary']['tx_to_counts'].items(), key=lambda item: (-item[1], item[0])):
    print(f"TX_TO_COUNT=address:{address},count:{count}")
print('CEX_EVIDENCE_STATUS=UNVERIFIED_OR_UNAVAILABLE')
print('SWAP_DIRECTION_CLASSIFIED=false')
print('ROUTER_POOL_IDENTITY_VERIFIED=false')
print('CLOSED_LOOP_CONFIRMED=false')
PY

printf '\n===== 5 IMMUTABILITY AND AUTHORITY GATES =====\n'
DB_HASH_AFTER="$(sha256_file "$DB")"
DB_STAT_AFTER="$(stat -c '%Y:%s:%a:%U:%G' "$DB")"
REPO_STATUS_AFTER="$(git status --porcelain=v1 --untracked-files=all)"
SERVICE_PID_AFTER="$(systemctl show -p MainPID --value "$SERVICE")"
SERVICE_NRESTARTS_AFTER="$(systemctl show -p NRestarts --value "$SERVICE")"

[[ "$DB_HASH_AFTER" == "$DB_HASH_BEFORE" ]] || fail SOURCE_DATABASE_MUTATED
[[ "$DB_STAT_AFTER" == "$DB_STAT_BEFORE" ]] || fail SOURCE_DATABASE_METADATA_MUTATED
[[ "$REPO_STATUS_AFTER" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_MUTATED
[[ "$SERVICE_PID_AFTER" == "$SERVICE_PID_BEFORE" ]] || fail PRODUCT_SERVICE_RESTARTED
[[ "$SERVICE_NRESTARTS_AFTER" == "$SERVICE_NRESTARTS_BEFORE" ]] || fail PRODUCT_SERVICE_RESTART_COUNT_CHANGED

printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'REPOSITORY_MUTATION=false\n'
printf 'PRODUCTION_DATABASE_WRITE=false\n'
printf 'PANEL_MUTATION=false\n'
printf 'SERVICE_RESTARTED=false\n'
printf 'STATE_DIRECTORY_MODE=700\n'
printf 'OUTPUT_MODE=600\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'

COMPLETED=1
trap - ERR INT TERM

printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_04_CANDIDATE_ENRICHMENT=SUCCESS\n'
printf 'CANDIDATE_TRANSACTION_INPUT_COVERAGE=14_14_VERIFIED\n'
printf 'TOKEN_METADATA_COVERAGE=3_3_VERIFIED\n'
printf 'ISSUE_17=OPEN\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'OUTPUT=%s\n' "$OUTPUT"
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
printf 'NEXT_SAFE_STEP=ALLOWLISTED_DEX_ROUTER_POOL_AND_SWAP_EVENT_DECODE\n'
