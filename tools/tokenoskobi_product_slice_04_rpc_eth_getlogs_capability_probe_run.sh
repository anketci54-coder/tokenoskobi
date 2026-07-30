#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_DB_HASH='99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'

DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
PROVIDER="$ROOT/config/era63e_always_on_market_runtime_v1.json"
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/rpc_eth_getlogs_capability_probe_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'

BASE="${PRODUCT_SLICE_04_HISTORICAL_REVERSE_SCAN_BASE_MODULE_PATH:-}"
MODULE="${PRODUCT_SLICE_04_RPC_CAPABILITY_PROBE_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_RPC_CAPABILITY_PROBE_TEST_PATH:-}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_rpc_capability_probe_${STAMP}"
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
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/rpc_eth_getlogs_capability_probe_v1.json" ]]; then
      install -o root -g root -m 0600 \
        "$BACKUP_DIR/rpc_eth_getlogs_capability_probe_v1.json" \
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

[[ -n "$BASE" && -f "$BASE" ]] || fail 'BASE_MODULE_MISSING'
[[ -n "$MODULE" && -f "$MODULE" ]] || fail 'PROBE_MODULE_MISSING'
[[ -n "$TEST" && -f "$TEST" ]] || fail 'PROBE_TEST_MISSING'
[[ -f "$DB" ]] || fail 'SOURCE_DATABASE_MISSING'
[[ -f "$PROVIDER" ]] || fail 'PROVIDER_CONFIG_MISSING'

LOCAL_HEAD="$(git rev-parse HEAD)"
git fetch --quiet origin main
ORIGIN_MAIN="$(git rev-parse origin/main)"
[[ "$LOCAL_HEAD" == "$EXPECTED_MAIN" ]] || fail 'LOCAL_HEAD_CHANGED'
[[ "$ORIGIN_MAIN" == "$EXPECTED_MAIN" ]] || fail 'ORIGIN_MAIN_CHANGED'
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail 'REPOSITORY_NOT_CLEAN'

DB_HASH_BEFORE="$(sha256_file "$DB")"
[[ "$DB_HASH_BEFORE" == "$EXPECTED_DB_HASH" ]] || fail 'SOURCE_DATABASE_HASH_CHANGED'

python3 - "$PROVIDER" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
rpc = payload['rpc']
assert payload['schema'] == 'tokenoskobi.era63e.always_on_market_runtime_config.v1'
assert rpc['chain_id'] == 56
assert rpc['endpoints'] == [
    'https://bsc-dataseed.bnbchain.org',
    'https://bsc-dataseed-public.bnbchain.org',
    'https://bsc-dataseed.nariox.org',
    'https://bsc-dataseed.defibit.io',
]
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
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_BEFORE"
printf 'PROBE_SCOPE=4_CURRENT_ALLOWLISTED_ENDPOINTS_KNOWN_EXACT_LOG_AND_FAILED_HISTORICAL_EXACT_FILTER\n'
printf 'RPC_SCOPE=ETH_CHAIN_ID_ETH_GET_BLOCK_BY_NUMBER_ETH_GET_LOGS_READ_ONLY_MAX_24_REQUESTS\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$BASE" "$MODULE" "$TEST"
PRODUCT_SLICE_04_RPC_CAPABILITY_PROBE_MODULE_PATH="$MODULE" \
  python3 "$TEST"
printf 'DETERMINISTIC_TESTS=10_10_OK\n'

printf '\n===== 3 STATE BACKUP AND ISOLATED RPC CAPABILITY PROBE =====\n'
install -d -o root -g root -m 0700 "$STATE_DIR"
install -d -o root -g root -m 0700 "$BACKUP_DIR"
if [[ -f "$OUTPUT" ]]; then
  install -o root -g root -m 0600 "$OUTPUT" \
    "$BACKUP_DIR/rpc_eth_getlogs_capability_probe_v1.json"
  OUTPUT_EXISTED=1
fi

PRODUCT_SLICE_04_HISTORICAL_REVERSE_SCAN_BASE_MODULE_PATH="$BASE" \
  python3 "$MODULE" \
    --database "$DB" \
    --provider "$PROVIDER" \
    --output "$OUTPUT"

printf '\n===== 4 OUTPUT CONTRACT AND ENDPOINT CLASSIFICATION =====\n'
python3 - "$OUTPUT" "$EXPECTED_DB_HASH" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected_db_hash = sys.argv[2]
payload = json.loads(path.read_text(encoding='utf-8'))

assert payload['schema'] == 'tokenoskobi.product_slice_04.rpc_eth_getlogs_capability_probe.v1'
assert payload['status'] == 'RPC_ETH_GETLOGS_CAPABILITY_PROBE_COMPLETED'
assert payload['chain'] == 'BSC'
assert payload['chain_id'] == 56
assert payload['source']['database_sha256'] == expected_db_hash
assert payload['policy']['current_allowlisted_endpoints_only'] is True
assert payload['policy']['endpoint_isolation_required'] is True
assert payload['policy']['known_exact_transfer_log_required'] is True
assert payload['policy']['probe_only_no_historical_scan'] is True
assert payload['policy']['maximum_total_requests'] == 24

summary = payload['summary']
assert summary['endpoint_count'] == 4
assert 0 <= summary['chain_56_endpoint_count'] <= 4
assert 0 <= summary['known_block_available_endpoint_count'] <= 4
assert 0 <= summary['known_exact_log_success_endpoint_count'] <= 4
assert 0 <= summary['historical_exact_filter_success_endpoint_count'] <= 4
assert summary['request_count'] == 16
assert summary['closed_loop_confirmed'] is False
assert summary['overall_classification'] in {
    'AT_LEAST_ONE_CURRENT_ENDPOINT_SUPPORTS_REQUIRED_ETH_GETLOGS',
    'CURRENT_ENDPOINT_SET_HAS_HISTORICAL_FILTER_OR_DEPTH_RESTRICTION',
    'CURRENT_ENDPOINT_SET_RETURNS_INCOMPLETE_KNOWN_LOG_EVIDENCE',
    'CURRENT_ENDPOINT_SET_ETH_GETLOGS_UNUSABLE',
}

assert len(payload['endpoint_results']) == 4
for endpoint in payload['endpoint_results']:
    assert endpoint['endpoint'].startswith('https://')
    assert endpoint['classification'] in {
        'CHAIN_UNAVAILABLE_OR_MISMATCH',
        'KNOWN_BLOCK_UNAVAILABLE',
        'ETH_GETLOGS_UNUSABLE_ON_KNOWN_EXACT_EVENT',
        'ETH_GETLOGS_KNOWN_EVENT_NOT_RETURNED',
        'ETH_GETLOGS_KNOWN_EVENT_OK_HISTORICAL_FILTER_REJECTED',
        'ETH_GETLOGS_AVAILABLE_FOR_EXACT_HISTORICAL_FILTER',
    }

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

stored_hash = payload.pop('result_hash')
raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(',', ':'), default=str)
assert stored_hash == hashlib.sha256(raw.encode('utf-8')).hexdigest()
assert (os.stat(path).st_mode & 0o777) == 0o600
assert (os.stat(path.parent).st_mode & 0o777) == 0o700

print('OUTPUT_STATUS=VERIFIED')
for key in (
    'endpoint_count',
    'chain_56_endpoint_count',
    'known_block_available_endpoint_count',
    'known_exact_log_success_endpoint_count',
    'historical_exact_filter_success_endpoint_count',
    'request_count',
):
    print(f'{key.upper()}={summary[key]}')
print(f'OVERALL_CLASSIFICATION={summary["overall_classification"]}')
print(f'RESULT_HASH={stored_hash}')
print('CLOSED_LOOP_CONFIRMED=false')
print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
DB_HASH_AFTER="$(sha256_file "$DB")"
[[ "$DB_HASH_AFTER" == "$DB_HASH_BEFORE" ]] || fail 'SOURCE_DATABASE_MUTATED'
[[ "$(repo_state)" == "$REPO_STATE_BEFORE" ]] || fail 'REPOSITORY_MUTATED'
systemctl is-active --quiet "$SERVICE" || fail 'PRODUCT_SERVICE_NOT_ACTIVE_AFTER'
PRODUCT_PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_AFTER" == "$PRODUCT_PID_BEFORE" ]] || fail 'PRODUCT_PID_CHANGED'
[[ "$PRODUCT_NRESTARTS_AFTER" == "$PRODUCT_NRESTARTS_BEFORE" ]] || fail 'PRODUCT_RESTART_COUNT_CHANGED'
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail 'STATE_DIRECTORY_MODE_INVALID'
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail 'OUTPUT_MODE_INVALID'

printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
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
printf 'PRODUCT_SLICE_04_RPC_ETH_GETLOGS_CAPABILITY_PROBE=SUCCESS\n'
printf 'PROBE_ONLY_NO_HISTORICAL_SCAN=true\n'
printf 'CURRENT_ALLOWLISTED_ENDPOINTS_ONLY=true\n'
printf 'CLOSED_LOOP_CONFIRMED=false\n'
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_18=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_17=OPEN\n'
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
