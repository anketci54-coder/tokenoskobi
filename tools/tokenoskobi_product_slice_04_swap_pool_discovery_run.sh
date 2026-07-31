#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_DB_HASH='99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_ENRICHMENT_RESULT_HASH='34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
PROVIDER="$ROOT/config/era63e_always_on_market_runtime_v1.json"
ENRICHMENT='/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json'
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/swap_pool_discovery_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'
MODULE="${PRODUCT_SLICE_04_DISCOVERY_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_DISCOVERY_TEST_PATH:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_swap_pool_discovery_${STAMP}"
OUTPUT_EXISTED=0
COMPLETED=0

fail() { printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
sha256_file() { sha256sum "$1" | awk '{print $1}'; }
rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/swap_pool_discovery_v1.json" ]]; then
      install -o root -g root -m 0600 "$BACKUP_DIR/swap_pool_discovery_v1.json" "$OUTPUT"
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
[[ -f "$ENRICHMENT" && -s "$ENRICHMENT" ]] || fail CANDIDATE_ENRICHMENT_MISSING
[[ -n "$MODULE" && -f "$MODULE" ]] || fail DISCOVERY_MODULE_MISSING
[[ -n "$TEST" && -f "$TEST" ]] || fail DISCOVERY_TEST_MISSING
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE
PRODUCT_PID_BEFORE="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_BEFORE="$(systemctl show "$SERVICE" -p NRestarts --value)"
DB_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$DB")"
REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"
ENRICHMENT_RESULT_HASH="$(python3 - "$ENRICHMENT" <<'PY'
import json,sys
from pathlib import Path

def require(condition, code):
    if not condition:
        print(f'BLOCKED={code}', file=sys.stderr)
        raise SystemExit(1)

p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
require(p.get('schema')=='tokenoskobi.product_slice_04.candidate_enrichment.v1','ENRICHMENT_SCHEMA_INVALID')
require(p.get('status')=='CANDIDATE_INPUT_AND_TOKEN_METADATA_ENRICHMENT_VERIFIED_WITH_ARCHIVE_FALLBACK_POLICY','ENRICHMENT_STATUS_INVALID')
require(len(p.get('transactions') or [])==14,'ENRICHMENT_TRANSACTION_COUNT_INVALID')
require(len(p.get('token_metadata') or [])==3,'ENRICHMENT_TOKEN_METADATA_COUNT_INVALID')
policy=p.get('metadata_temporal_policy')
require(isinstance(policy,dict),'ENRICHMENT_TEMPORAL_POLICY_MISSING')
require(policy.get('historical_block_attempt_required') is True,'HISTORICAL_METADATA_ATTEMPT_NOT_RECORDED')
require(policy.get('fallback_allowed_only_for_archive_state_unavailable_errors') is True,'ARCHIVE_FALLBACK_NOT_FAIL_CLOSED')
require(policy.get('fallback_target')=='latest','ARCHIVE_FALLBACK_TARGET_INVALID')
require(policy.get('historical_metadata_verified_count')==0,'HISTORICAL_METADATA_COUNT_CHANGED')
require(policy.get('latest_metadata_fallback_count')==3,'LATEST_METADATA_FALLBACK_COUNT_CHANGED')
require(policy.get('historical_transaction_and_receipt_identity_preserved') is True,'HISTORICAL_TRANSACTION_RECEIPT_IDENTITY_NOT_PRESERVED')
require(policy.get('token_amount_normalization_ready') is True,'TOKEN_NORMALIZATION_NOT_READY')
print(p.get('result_hash') or '')
PY
)"
[[ "$ENRICHMENT_RESULT_HASH" == "$EXPECTED_ENRICHMENT_RESULT_HASH" ]] || fail ENRICHMENT_RESULT_HASH_CHANGED
printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_DATABASE_SHA256=%s\n' "$(sha256_file "$DB")"
printf 'ENRICHMENT_RESULT_HASH=%s\n' "$ENRICHMENT_RESULT_HASH"
printf 'ENRICHMENT_STATUS=ARCHIVE_FALLBACK_POLICY_VERIFIED\n'
printf 'HISTORICAL_METADATA_VERIFIED_COUNT=0\n'
printf 'LATEST_METADATA_ARCHIVE_FALLBACK_COUNT=3\n'
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_BEFORE"
printf 'DISCOVERY_SCOPE=14_CANDIDATE_RECEIPTS_RECOGNIZED_SWAP_TOPICS_POOL_INTROSPECTION\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$MODULE" "$TEST"
PRODUCT_SLICE_04_DISCOVERY_MODULE_PATH="$MODULE" python3 "$TEST"
printf 'DETERMINISTIC_TESTS=10_10_OK\n'

printf '\n===== 3 STATE BACKUP AND READ-ONLY SWAP POOL DISCOVERY =====\n'
install -d -o root -g root -m 0700 "$STATE_DIR"
install -d -o root -g root -m 0700 "$BACKUP_DIR"
if [[ -f "$OUTPUT" ]]; then
  OUTPUT_EXISTED=1
  install -o root -g root -m 0600 "$OUTPUT" "$BACKUP_DIR/swap_pool_discovery_v1.json"
fi
python3 "$MODULE" --database "$DB" --provider "$PROVIDER" --enrichment "$ENRICHMENT" --output "$OUTPUT"
[[ -f "$OUTPUT" && -s "$OUTPUT" ]] || fail DISCOVERY_OUTPUT_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail OUTPUT_MODE_INVALID

printf '\n===== 4 OUTPUT CONTRACT AND DISCOVERED POOLS =====\n'
python3 - "$OUTPUT" "$EXPECTED_DB_HASH" "$EXPECTED_ENRICHMENT_RESULT_HASH" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert p.get('schema')=='tokenoskobi.product_slice_04.swap_pool_discovery.v1'
assert p.get('status')=='SWAP_POOL_DISCOVERY_COMPLETED'
assert p.get('chain')=='BSC' and p.get('chain_id')==56
s=p.get('source'); assert isinstance(s,dict)
assert s.get('database_sha256')==sys.argv[2]
assert s.get('candidate_enrichment_result_hash')==sys.argv[3]
assert s.get('candidate_transaction_count')==14
a=p.get('authority'); assert isinstance(a,dict)
assert a.get('network_access') is True and a.get('staging_file_write') is True
for key in ('source_database_write','production_database_write','repository_write','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
    assert a.get(key) is False,key
summary=p.get('summary'); assert isinstance(summary,dict)
assert summary.get('factory_allowlist_locked') is False
assert summary.get('protocol_identity_verified') is False
assert summary.get('router_identity_verified') is False
assert summary.get('closed_loop_confirmed') is False
events=p.get('events'); assert isinstance(events,list)
assert summary.get('recognized_swap_event_count')==len(events)
print('OUTPUT_STATUS=VERIFIED')
print(f'RECOGNIZED_SWAP_EVENT_COUNT={len(events)}')
print(f'CANDIDATE_TRANSACTION_WITH_SWAP_COUNT={summary.get("candidate_transaction_with_swap_count")}')
print(f'CANDIDATE_TRANSACTION_WITHOUT_SWAP_COUNT={summary.get("candidate_transaction_without_recognized_swap_count")}')
print(f'DISTINCT_POOL_COUNT={summary.get("distinct_pool_count")}')
print(f'DIRECTION_DECODED_EVENT_COUNT={summary.get("direction_decoded_event_count")}')
print(f'EXACT_ACTOR_FLOW_PAIR_MATCH_COUNT={summary.get("exact_actor_flow_pair_match_count")}')
print('EVENT_TYPE_COUNTS='+json.dumps(summary.get('event_type_counts'),sort_keys=True,separators=(',',':')))
print('FACTORY_COUNTS='+json.dumps(summary.get('factory_counts'),sort_keys=True,separators=(',',':')))
for i,e in enumerate(events,start=1):
    identity=e['pool_identity']; swap=e['swap']; match=e['actor_flow_pair_match']
    print(f'SWAP_EVENT_{i}=tx:{e["tx_hash"]},block:{e["block_number"]},type:{swap["event_type"]},pool:{identity["pool_address"]},factory:{identity["factory"]},token0:{identity["token0"]},token1:{identity["token1"]},fee:{identity.get("fee")},input:{swap.get("input_token")},output:{swap.get("output_token")},actor_pair_match:{str(bool(match.get("matched"))).lower()}')
print(f'RESULT_HASH={p.get("result_hash")}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_MUTATED
[[ "$(stat -c '%Y:%s:%a' "$DB")" == "$DB_MTIME_BEFORE" ]] || fail SOURCE_DATABASE_METADATA_MUTATED
[[ "$(git status --porcelain=v1 --untracked-files=all)" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_MUTATED
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_STOPPED
PRODUCT_PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_AFTER" == "$PRODUCT_PID_BEFORE" ]] || fail PRODUCT_SERVICE_RESTARTED
[[ "$PRODUCT_NRESTARTS_AFTER" == "$PRODUCT_NRESTARTS_BEFORE" ]] || fail PRODUCT_RESTART_COUNT_CHANGED
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
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
printf 'PRODUCT_SLICE_04_SWAP_POOL_DISCOVERY=SUCCESS\n'
printf 'SWAP_EVENT_DECODE=RECOGNIZED_TOPICS_ONLY_FAIL_CLOSED\n'
printf 'POOL_IDENTITY=TOKEN0_TOKEN1_FACTORY_AND_OPTIONAL_FEE_INTROSPECTED\n'
printf 'FACTORY_ALLOWLIST_LOCKED=false\n'
printf 'PROTOCOL_IDENTITY_VERIFIED=false\n'
printf 'ROUTER_IDENTITY_VERIFIED=false\n'
printf 'CLOSED_LOOP_CONFIRMED=false\n'
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_18=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_17=OPEN\n'
printf 'NEXT_SAFE_STEP=VERIFY_FACTORY_ADDRESSES_AND_SELECT_FIRST_REAL_SWAP_CHAIN\n'
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
