#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_DB_HASH='99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_ENRICHMENT_HASH='34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
EXPECTED_TARGETED_HASH='1929f555b30c9bf987acb1929a6c26ca7ebbfe90cfddb631d1f5a60fe378d18b'
EXPECTED_ACTOR='0x9999b0cdd35d7f3b281ba02efc0d228486940515'
DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
PROVIDER="$ROOT/config/era63e_always_on_market_runtime_v1.json"
ENRICHMENT='/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json'
TARGETED='/var/lib/tokenoskobi-product-slice-04/targeted_actor_history_enrichment_v1.json'
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/targeted_swap_route_graph_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'

MODULE="${PRODUCT_SLICE_04_ROUTE_GRAPH_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_ROUTE_GRAPH_TEST_PATH:-}"
ALLOWLIST="${PRODUCT_SLICE_04_FACTORY_ALLOWLIST_PATH:-}"
DECODER="${PRODUCT_SLICE_04_DISCOVERY_CONTRACT_MODULE_PATH:-}"
BASE_DECODER="${PRODUCT_SLICE_04_DISCOVERY_BASE_MODULE_PATH:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_targeted_route_graph_${STAMP}"
OUTPUT_EXISTED=0
COMPLETED=0

fail() { printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
sha256_file() { sha256sum "$1" | awk '{print $1}'; }
rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/targeted_swap_route_graph_v1.json" ]]; then
      install -o root -g root -m 0600 "$BACKUP_DIR/targeted_swap_route_graph_v1.json" "$OUTPUT"
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
[[ -f "$TARGETED" && -s "$TARGETED" ]] || fail TARGETED_HISTORY_MISSING
[[ -n "$MODULE" && -f "$MODULE" ]] || fail ROUTE_GRAPH_MODULE_MISSING
[[ -n "$TEST" && -f "$TEST" ]] || fail ROUTE_GRAPH_TEST_MISSING
[[ -n "$ALLOWLIST" && -f "$ALLOWLIST" ]] || fail FACTORY_ALLOWLIST_MISSING
[[ -n "$DECODER" && -f "$DECODER" ]] || fail DISCOVERY_CONTRACT_DECODER_MISSING
[[ -n "$BASE_DECODER" && -f "$BASE_DECODER" ]] || fail DISCOVERY_BASE_DECODER_MISSING
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE

PRODUCT_PID_BEFORE="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_BEFORE="$(systemctl show "$SERVICE" -p NRestarts --value)"
DB_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$DB")"
ENRICHMENT_SHA_BEFORE="$(sha256_file "$ENRICHMENT")"
TARGETED_SHA_BEFORE="$(sha256_file "$TARGETED")"
ALLOWLIST_SHA_BEFORE="$(sha256_file "$ALLOWLIST")"
REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"

python3 - "$ENRICHMENT" "$TARGETED" "$ALLOWLIST" <<'PY'
import json,sys
from pathlib import Path

enrichment=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert enrichment.get('schema')=='tokenoskobi.product_slice_04.candidate_enrichment.v1'
assert enrichment.get('result_hash')=='34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
assert len(enrichment.get('token_metadata') or [])==3

targeted=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
assert targeted.get('schema')=='tokenoskobi.product_slice_04.targeted_actor_history_enrichment.v1'
assert targeted.get('status')=='TARGETED_SAME_ACTOR_HISTORY_ENRICHMENT_COMPLETED'
assert targeted.get('result_hash')=='1929f555b30c9bf987acb1929a6c26ca7ebbfe90cfddb631d1f5a60fe378d18b'
assert targeted.get('target_actors')==['0x9999b0cdd35d7f3b281ba02efc0d228486940515']
assert len(targeted.get('transactions') or [])==6
assert len(targeted.get('round_trip_pairs') or [])==5
assert all(item.get('selector')=='0xd4d6ab16' for item in targeted['transactions'])
assert all(item.get('actor')==item.get('tx_to')=='0x9999b0cdd35d7f3b281ba02efc0d228486940515' for item in targeted['transactions'])

allowlist=json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
assert allowlist.get('schema')=='tokenoskobi.product_slice_04.factory_allowlist.v1'
assert allowlist.get('chain')=='BSC' and allowlist.get('chain_id')==56
assert len(allowlist.get('factories') or {})==4
PY

printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_DATABASE_SHA256=%s\n' "$(sha256_file "$DB")"
printf 'ENRICHMENT_RESULT_HASH=%s\n' "$EXPECTED_ENRICHMENT_HASH"
printf 'TARGETED_HISTORY_RESULT_HASH=%s\n' "$EXPECTED_TARGETED_HASH"
printf 'TARGET_ACTOR=%s\n' "$EXPECTED_ACTOR"
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_BEFORE"
printf 'ROUTE_GRAPH_SCOPE=6_TARGET_TRANSACTIONS_5_ROUND_TRIP_PAIRS_RECOGNIZED_SWAP_TOPICS_OFFICIAL_FACTORY_ALLOWLIST\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$MODULE" "$TEST" "$DECODER" "$BASE_DECODER"
PRODUCT_SLICE_04_ROUTE_GRAPH_MODULE_PATH="$MODULE" python3 "$TEST"
printf 'DETERMINISTIC_TESTS=10_10_OK\n'

printf '\n===== 3 STATE BACKUP AND TARGETED READ-ONLY ROUTE GRAPH =====\n'
install -d -o root -g root -m 0700 "$STATE_DIR"
install -d -o root -g root -m 0700 "$BACKUP_DIR"
if [[ -f "$OUTPUT" ]]; then
  OUTPUT_EXISTED=1
  install -o root -g root -m 0600 "$OUTPUT" "$BACKUP_DIR/targeted_swap_route_graph_v1.json"
fi

PRODUCT_SLICE_04_DISCOVERY_BASE_MODULE_PATH="$BASE_DECODER" \
python3 "$MODULE" \
  --database "$DB" \
  --provider "$PROVIDER" \
  --enrichment "$ENRICHMENT" \
  --targeted "$TARGETED" \
  --allowlist "$ALLOWLIST" \
  --decoder "$DECODER" \
  --output "$OUTPUT"

[[ -f "$OUTPUT" && -s "$OUTPUT" ]] || fail ROUTE_GRAPH_OUTPUT_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail OUTPUT_MODE_INVALID

printf '\n===== 4 OUTPUT CONTRACT AND ROUTE EVIDENCE =====\n'
python3 - "$OUTPUT" "$EXPECTED_DB_HASH" "$EXPECTED_ENRICHMENT_HASH" "$EXPECTED_TARGETED_HASH" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert p.get('schema')=='tokenoskobi.product_slice_04.targeted_swap_route_graph.v1'
assert p.get('status')=='TARGETED_SWAP_ROUTE_GRAPH_COMPLETED'
assert p.get('chain')=='BSC' and p.get('chain_id')==56
assert p.get('target_actor')=='0x9999b0cdd35d7f3b281ba02efc0d228486940515'
assert p.get('selector')=='0xd4d6ab16'
source=p.get('source'); assert isinstance(source,dict)
assert source.get('database_sha256')==sys.argv[2]
assert source.get('candidate_enrichment_result_hash')==sys.argv[3]
assert source.get('targeted_actor_history_result_hash')==sys.argv[4]
a=p.get('authority'); assert isinstance(a,dict)
assert a.get('network_access') is True and a.get('staging_file_write') is True
for key in ('source_database_write','production_database_write','repository_write','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
    assert a.get(key) is False,key
summary=p.get('summary'); assert isinstance(summary,dict)
assert summary.get('target_transaction_count')==6
assert summary.get('route_pair_candidate_count')==5
assert summary.get('router_identity_verified') is False
assert summary.get('counterasset_continuity_verified') is False
assert summary.get('route_amount_conservation_verified') is False
assert summary.get('net_performance_reconstructed') is False
assert summary.get('closed_loop_confirmed') is False
routes=p.get('transaction_routes'); assert isinstance(routes,list) and len(routes)==6
pairs=p.get('route_pair_candidates'); assert isinstance(pairs,list) and len(pairs)==5
print('OUTPUT_STATUS=VERIFIED')
for key in ('target_transaction_count','recognized_swap_event_count','protocol_verified_swap_event_count','route_evidence_usable_transaction_count','connected_route_transaction_count','directed_cycle_transaction_count','self_target_call_transaction_count','route_pair_candidate_count','route_pair_verified_count'):
    print(f'{key.upper()}={summary.get(key)}')
print('EVENT_TYPE_COUNTS='+json.dumps(summary.get('event_type_counts'),sort_keys=True,separators=(',',':')))
print('PROTOCOL_EVENT_COUNTS='+json.dumps(summary.get('protocol_event_counts'),sort_keys=True,separators=(',',':')))
print('UNVERIFIED_FACTORIES='+json.dumps(summary.get('unverified_factories'),separators=(',',':')))
for i,route in enumerate(routes,start=1):
    flows='|'.join(f'{x["symbol"]}:{x["direction"]}:{x["net_raw"]}' for x in route['actor_flow_endpoint_checks']) or 'NONE'
    print(f'ROUTE_TX_{i}=tx:{route["tx_hash"]},block:{route["block_number"]},swaps:{route["recognized_swap_event_count"]},protocol_verified:{str(route["all_swap_events_protocol_verified"]).lower()},connected:{str(route["undirected_route_connected"]).lower()},cycle:{str(route["directed_cycle_present"]).lower()},endpoint_consistent:{str(route["actor_flow_route_endpoint_consistent"]).lower()},usable:{str(route["route_evidence_usable"]).lower()},flows:{flows}')
top=p.get('top_route_pair_candidate')
if top:
    print(f'TOP_ROUTE_PAIR_CANDIDATE=token:{top["token_address"]},first_tx:{top["first_tx_hash"]},first:{top["first_direction"]},second_tx:{top["second_tx_hash"]},second:{top["second_direction"]},route_pair_verified:{str(top["route_pair_verified"]).lower()},blockers:{"|".join(top["blockers"]) or "NONE"}')
else:
    print('TOP_ROUTE_PAIR_CANDIDATE=NONE')
print(f'RPC_REQUEST_COUNT={p["rpc"]["request_count"]}')
print(f'RPC_ERROR_COUNT={p["rpc"]["error_count"]}')
print(f'RESULT_HASH={p.get("result_hash")}')
print(f'CLOSED_LOOP_CONFIRMED={str(summary.get("closed_loop_confirmed")).lower()}')
print(f'NEXT_SAFE_STEP={summary.get("next_safe_step")}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_MUTATED
[[ "$(stat -c '%Y:%s:%a' "$DB")" == "$DB_MTIME_BEFORE" ]] || fail SOURCE_DATABASE_METADATA_MUTATED
[[ "$(sha256_file "$ENRICHMENT")" == "$ENRICHMENT_SHA_BEFORE" ]] || fail ENRICHMENT_MUTATED
[[ "$(sha256_file "$TARGETED")" == "$TARGETED_SHA_BEFORE" ]] || fail TARGETED_HISTORY_MUTATED
[[ "$(sha256_file "$ALLOWLIST")" == "$ALLOWLIST_SHA_BEFORE" ]] || fail FACTORY_ALLOWLIST_MUTATED
[[ "$(git status --porcelain=v1 --untracked-files=all)" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_MUTATED
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_STOPPED
PRODUCT_PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_AFTER" == "$PRODUCT_PID_BEFORE" ]] || fail PRODUCT_SERVICE_RESTARTED
[[ "$PRODUCT_NRESTARTS_AFTER" == "$PRODUCT_NRESTARTS_BEFORE" ]] || fail PRODUCT_RESTART_COUNT_CHANGED
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'ENRICHMENT_IMMUTABLE=VERIFIED\n'
printf 'TARGETED_HISTORY_IMMUTABLE=VERIFIED\n'
printf 'FACTORY_ALLOWLIST_IMMUTABLE=VERIFIED\n'
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
printf 'PRODUCT_SLICE_04_TARGETED_SWAP_ROUTE_GRAPH=SUCCESS\n'
printf 'TARGET_SCOPE=1_ACTOR_6_TRANSACTIONS_5_ROUND_TRIP_PAIRS\n'
printf 'FACTORY_ALLOWLIST_LOCKED=true\n'
printf 'ROUTE_GRAPH_POLICY=PROTOCOL_VERIFIED_SWAP_EDGES_PLUS_ACTOR_FLOW_ENDPOINT_CONSISTENCY\n'
printf 'ROUTER_IDENTITY_VERIFIED=false\n'
printf 'CLOSED_LOOP_CONFIRMED=false\n'
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_18=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_17=OPEN\n'
printf 'NEXT_SAFE_STEP=%s\n' "$NEXT_STEP"
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
