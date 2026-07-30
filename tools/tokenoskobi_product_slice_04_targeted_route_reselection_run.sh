#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_DB_HASH='99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_TARGETED_HASH='1929f555b30c9bf987acb1929a6c26ca7ebbfe90cfddb631d1f5a60fe378d18b'
EXPECTED_ENRICHMENT_HASH='34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
PROVIDER="$ROOT/config/era63e_always_on_market_runtime_v1.json"
TARGETED='/var/lib/tokenoskobi-product-slice-04/targeted_actor_history_enrichment_v1.json'
ENRICHMENT='/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json'
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/targeted_route_reselection_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'

MODULE="${PRODUCT_SLICE_04_TARGETED_ROUTE_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_TARGETED_ROUTE_TEST_PATH:-}"
BASE="${PRODUCT_SLICE_04_DISCOVERY_BASE_MODULE_PATH:-}"
ALLOWLIST="${PRODUCT_SLICE_04_FACTORY_ALLOWLIST_PATH:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_targeted_route_${STAMP}"
OUTPUT_EXISTED=0
COMPLETED=0

fail() { printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
sha256_file() { sha256sum "$1" | awk '{print $1}'; }
rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/targeted_route_reselection_v1.json" ]]; then
      install -o root -g root -m 0600 "$BACKUP_DIR/targeted_route_reselection_v1.json" "$OUTPUT"
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
[[ -f "$TARGETED" && -s "$TARGETED" ]] || fail TARGETED_HISTORY_MISSING
[[ -f "$ENRICHMENT" && -s "$ENRICHMENT" ]] || fail ENRICHMENT_MISSING
[[ -n "$MODULE" && -f "$MODULE" ]] || fail MODULE_MISSING
[[ -n "$TEST" && -f "$TEST" ]] || fail TEST_MISSING
[[ -n "$BASE" && -f "$BASE" ]] || fail DISCOVERY_BASE_MISSING
[[ -n "$ALLOWLIST" && -f "$ALLOWLIST" ]] || fail FACTORY_ALLOWLIST_MISSING
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE
PRODUCT_PID_BEFORE="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_BEFORE="$(systemctl show "$SERVICE" -p NRestarts --value)"
DB_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$DB")"
TARGETED_SHA_BEFORE="$(sha256_file "$TARGETED")"
ENRICHMENT_SHA_BEFORE="$(sha256_file "$ENRICHMENT")"
REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"

python3 - "$TARGETED" "$ENRICHMENT" "$ALLOWLIST" <<'PY'
import json,sys
from pathlib import Path

targeted=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
enrichment=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
allowlist=json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
assert targeted.get('schema')=='tokenoskobi.product_slice_04.targeted_actor_history_enrichment.v1'
assert targeted.get('status')=='TARGETED_SAME_ACTOR_HISTORY_ENRICHMENT_COMPLETED'
assert targeted.get('result_hash')=='1929f555b30c9bf987acb1929a6c26ca7ebbfe90cfddb631d1f5a60fe378d18b'
assert len(targeted.get('transactions') or [])==6
assert len(targeted.get('round_trip_pairs') or [])==5
assert enrichment.get('result_hash')=='34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
assert len(enrichment.get('token_metadata') or [])==3
assert allowlist.get('schema')=='tokenoskobi.product_slice_04.factory_allowlist.v1'
assert len(allowlist.get('factories') or {})==4
PY

printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_DATABASE_SHA256=%s\n' "$(sha256_file "$DB")"
printf 'TARGETED_HISTORY_RESULT_HASH=%s\n' "$EXPECTED_TARGETED_HASH"
printf 'ENRICHMENT_RESULT_HASH=%s\n' "$EXPECTED_ENRICHMENT_HASH"
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_BEFORE"
printf 'ROUTE_POLICY=ALL_RECEIPT_TRANSFERS_PLUS_ALLOWLISTED_SWAP_NET_EXACT_MULTI_HOP_FULL_POSITION_REVERSAL\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$MODULE" "$TEST" "$BASE"
PRODUCT_SLICE_04_TARGETED_ROUTE_MODULE_PATH="$MODULE" python3 "$TEST"
printf 'DETERMINISTIC_TESTS=10_10_OK\n'

printf '\n===== 3 STATE BACKUP AND TARGETED MULTI-HOP ROUTE RESELECTION =====\n'
install -d -o root -g root -m 0700 "$STATE_DIR"
install -d -o root -g root -m 0700 "$BACKUP_DIR"
if [[ -f "$OUTPUT" ]]; then
  OUTPUT_EXISTED=1
  install -o root -g root -m 0600 "$OUTPUT" "$BACKUP_DIR/targeted_route_reselection_v1.json"
fi
python3 "$MODULE" \
  --database "$DB" \
  --provider "$PROVIDER" \
  --targeted "$TARGETED" \
  --enrichment "$ENRICHMENT" \
  --allowlist "$ALLOWLIST" \
  --output "$OUTPUT" \
  --base-module "$BASE"
[[ -f "$OUTPUT" && -s "$OUTPUT" ]] || fail OUTPUT_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail OUTPUT_MODE_INVALID

printf '\n===== 4 OUTPUT CONTRACT AND ROUTE EVIDENCE =====\n'
python3 - "$OUTPUT" "$EXPECTED_DB_HASH" "$EXPECTED_TARGETED_HASH" "$EXPECTED_ENRICHMENT_HASH" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert p.get('schema')=='tokenoskobi.product_slice_04.targeted_route_reselection.v1'
assert p.get('status')=='TARGETED_MULTI_HOP_ROUTE_RESELECTION_COMPLETED'
assert p.get('chain')=='BSC' and p.get('chain_id')==56
s=p.get('source'); assert isinstance(s,dict)
assert s.get('database_sha256')==sys.argv[2]
assert s.get('targeted_history_result_hash')==sys.argv[3]
assert s.get('candidate_enrichment_result_hash')==sys.argv[4]
a=p.get('authority'); assert isinstance(a,dict)
assert a.get('network_access') is True and a.get('staging_file_write') is True
for key in ('source_database_write','production_database_write','repository_write','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
    assert a.get(key) is False,key
policy=p.get('policy'); assert isinstance(policy,dict)
assert policy.get('transaction_level_net_reconstruction') is True
assert policy.get('multi_hop_and_split_routes_supported') is True
assert policy.get('actor_and_swap_raw_amounts_must_match_exactly') is True
assert policy.get('closed_loop_requires_full_position_raw_amount_reversal') is True
assert policy.get('same_pool_required') is False
assert policy.get('same_protocol_required') is False
transactions=p.get('transactions'); assert isinstance(transactions,list) and len(transactions)==6
summary=p.get('summary'); assert isinstance(summary,dict)
assert summary.get('target_transaction_count')==6
assert summary.get('recognized_swap_event_count')>=0
assert summary.get('protocol_verified_swap_event_count')<=summary.get('recognized_swap_event_count')
assert summary.get('route_verified_transaction_count')<=6
assert summary.get('full_position_closed_loop_count')<=summary.get('reversed_route_candidate_count')
print('OUTPUT_STATUS=VERIFIED')
print(f'TARGET_TRANSACTION_COUNT={summary.get("target_transaction_count")}')
print(f'RECOGNIZED_SWAP_EVENT_COUNT={summary.get("recognized_swap_event_count")}')
print(f'PROTOCOL_VERIFIED_SWAP_EVENT_COUNT={summary.get("protocol_verified_swap_event_count")}')
print(f'ROUTE_VERIFIED_TRANSACTION_COUNT={summary.get("route_verified_transaction_count")}')
print(f'REVERSED_ROUTE_CANDIDATE_COUNT={summary.get("reversed_route_candidate_count")}')
print(f'FULL_POSITION_CLOSED_LOOP_COUNT={summary.get("full_position_closed_loop_count")}')
print(f'SELF_CALL_TRANSACTION_COUNT={summary.get("self_call_transaction_count")}')
print('PROTOCOL_EVENT_COUNTS='+json.dumps(summary.get('protocol_event_counts'),sort_keys=True,separators=(',',':')))
for i,tx in enumerate(transactions,start=1):
    route=tx['route']
    print(f'ROUTE_TX_{i}=tx:{tx["tx_hash"]},block:{tx["block_number"]},swaps:{tx["recognized_swap_event_count"]},verified_swaps:{tx["protocol_verified_swap_event_count"]},input:{route.get("route_input_token") or "NONE"},output:{route.get("route_output_token") or "NONE"},exact_tokens:{str(bool(route.get("exact_token_set"))).lower()},exact_amounts:{str(bool(route.get("exact_raw_amounts"))).lower()},verified:{str(bool(route.get("route_verified"))).lower()},blockers:{"|".join(route.get("blockers") or []) or "NONE"}')
top=p.get('top_candidate')
if top:
    print(f'TOP_CLOSED_LOOP_CANDIDATE=open_tx:{top["opening_tx_hash"]},close_tx:{top["closing_tx_hash"]},base:{top["base_token"]},position:{top["position_token"]},position_acquired:{top["position_acquired_raw"]},position_sold:{top["position_sold_raw"]},full_position:{str(bool(top["position_amount_exact"])).lower()},confirmed:{str(bool(top["closed_loop_confirmed"])).lower()},blockers:{"|".join(top.get("blockers") or []) or "NONE"}')
else:
    print('TOP_CLOSED_LOOP_CANDIDATE=NONE')
print(f'RPC_REQUEST_COUNT={p.get("rpc",{}).get("request_count")}')
print(f'RPC_ERROR_COUNT={p.get("rpc",{}).get("error_count")}')
print(f'RESULT_HASH={p.get("result_hash")}')
print(f'CLOSED_LOOP_CONFIRMED={str(bool(summary.get("closed_loop_confirmed"))).lower()}')
print(f'NEXT_SAFE_STEP={summary.get("next_safe_step")}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_MUTATED
[[ "$(stat -c '%Y:%s:%a' "$DB")" == "$DB_MTIME_BEFORE" ]] || fail SOURCE_DATABASE_METADATA_MUTATED
[[ "$(sha256_file "$TARGETED")" == "$TARGETED_SHA_BEFORE" ]] || fail TARGETED_HISTORY_MUTATED
[[ "$(sha256_file "$ENRICHMENT")" == "$ENRICHMENT_SHA_BEFORE" ]] || fail ENRICHMENT_MUTATED
[[ "$(git status --porcelain=v1 --untracked-files=all)" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_MUTATED
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_STOPPED
PRODUCT_PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_AFTER" == "$PRODUCT_PID_BEFORE" ]] || fail PRODUCT_SERVICE_RESTARTED
[[ "$PRODUCT_NRESTARTS_AFTER" == "$PRODUCT_NRESTARTS_BEFORE" ]] || fail PRODUCT_RESTART_COUNT_CHANGED
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'TARGETED_HISTORY_IMMUTABLE=VERIFIED\n'
printf 'ENRICHMENT_IMMUTABLE=VERIFIED\n'
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
CLOSED="$(python3 - "$OUTPUT" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(str(bool(p['summary']['closed_loop_confirmed'])).lower())
PY
)"
printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_04_TARGETED_ROUTE_RESELECTION=SUCCESS\n'
printf 'MULTI_HOP_AND_SPLIT_ROUTE_SUPPORT=true\n'
printf 'TRANSACTION_LEVEL_NET_MATCH=EXACT_RAW_FAIL_CLOSED\n'
printf 'FULL_POSITION_REVERSAL_REQUIRED=true\n'
printf 'CLOSED_LOOP_CONFIRMED=%s\n' "$CLOSED"
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_18=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_17=OPEN\n'
printf 'NEXT_SAFE_STEP=%s\n' "$NEXT_STEP"
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
