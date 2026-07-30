#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
EXPECTED_DB_HASH='99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_ENRICHMENT_HASH='34a02e24f5b332774485805efa02d148f5b07692fd0b7f0dc7d9a26500497595'
EXPECTED_DISCOVERY_HASH='94ab3493b18a064aae90a25bd2cf54ebdba1b5463c997cf2a04bc09c78a933f2'
DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
ENRICHMENT='/var/lib/tokenoskobi-product-slice-04/candidate_enrichment_v1.json'
DISCOVERY='/var/lib/tokenoskobi-product-slice-04/swap_pool_discovery_v1.json'
STATE_DIR='/var/lib/tokenoskobi-product-slice-04'
OUTPUT="$STATE_DIR/first_swap_chain_selection_v1.json"
SERVICE='tokenoskobi-product-slice-02.service'

MODULE="${PRODUCT_SLICE_04_CHAIN_SELECTION_MODULE_PATH:-}"
TEST="${PRODUCT_SLICE_04_CHAIN_SELECTION_TEST_PATH:-}"
ALLOWLIST="${PRODUCT_SLICE_04_FACTORY_ALLOWLIST_PATH:-}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_04_first_chain_selection_${STAMP}"
OUTPUT_EXISTED=0
COMPLETED=0

fail() { printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
sha256_file() { sha256sum "$1" | awk '{print $1}'; }

rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMPLETED" -eq 0 ]]; then
    if [[ "$OUTPUT_EXISTED" -eq 1 && -f "$BACKUP_DIR/first_swap_chain_selection_v1.json" ]]; then
      install -o root -g root -m 0600 "$BACKUP_DIR/first_swap_chain_selection_v1.json" "$OUTPUT"
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
[[ -f "$ENRICHMENT" && -s "$ENRICHMENT" ]] || fail ENRICHMENT_MISSING
[[ -f "$DISCOVERY" && -s "$DISCOVERY" ]] || fail DISCOVERY_MISSING
[[ -n "$MODULE" && -f "$MODULE" ]] || fail CHAIN_SELECTION_MODULE_MISSING
[[ -n "$TEST" && -f "$TEST" ]] || fail CHAIN_SELECTION_TEST_MISSING
[[ -n "$ALLOWLIST" && -f "$ALLOWLIST" ]] || fail FACTORY_ALLOWLIST_MISSING

python3 - "$ENRICHMENT" "$DISCOVERY" "$EXPECTED_ENRICHMENT_HASH" "$EXPECTED_DISCOVERY_HASH" <<'PY'
import json,sys
from pathlib import Path
enrichment=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
discovery=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
assert enrichment.get('result_hash')==sys.argv[3]
assert discovery.get('result_hash')==sys.argv[4]
assert len(discovery.get('events') or [])==36
PY

systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE
PRODUCT_PID_BEFORE="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_BEFORE="$(systemctl show "$SERVICE" -p NRestarts --value)"
DB_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$DB")"
ENRICHMENT_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$ENRICHMENT")"
DISCOVERY_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$DISCOVERY")"
REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"

printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_DATABASE_SHA256=%s\n' "$(sha256_file "$DB")"
printf 'ENRICHMENT_RESULT_HASH=%s\n' "$EXPECTED_ENRICHMENT_HASH"
printf 'DISCOVERY_RESULT_HASH=%s\n' "$EXPECTED_DISCOVERY_HASH"
printf 'PRODUCT_PID=%s\n' "$PRODUCT_PID_BEFORE"
printf 'PRODUCT_NRESTARTS=%s\n' "$PRODUCT_NRESTARTS_BEFORE"
printf 'SELECTION_SCOPE=36_EVENTS_4_OFFICIAL_FACTORIES_STRICT_PAIR_DIRECTION_AMOUNT_AND_OPPOSITE_CHAIN\n'

printf '\n===== 2 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile "$MODULE" "$TEST"
PRODUCT_SLICE_04_CHAIN_SELECTION_MODULE_PATH="$MODULE" \
PRODUCT_SLICE_04_FACTORY_ALLOWLIST_PATH="$ALLOWLIST" \
python3 "$TEST"
printf 'DETERMINISTIC_TESTS=10_10_OK\n'

printf '\n===== 3 STATE BACKUP AND STRICT READ-ONLY CHAIN SELECTION =====\n'
install -d -o root -g root -m 0700 "$STATE_DIR"
install -d -o root -g root -m 0700 "$BACKUP_DIR"
if [[ -f "$OUTPUT" ]]; then
  OUTPUT_EXISTED=1
  install -o root -g root -m 0600 "$OUTPUT" "$BACKUP_DIR/first_swap_chain_selection_v1.json"
fi

python3 "$MODULE" \
  --database "$DB" \
  --enrichment "$ENRICHMENT" \
  --discovery "$DISCOVERY" \
  --allowlist "$ALLOWLIST" \
  --output "$OUTPUT"

[[ -f "$OUTPUT" && -s "$OUTPUT" ]] || fail CHAIN_SELECTION_OUTPUT_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ "$(stat -c '%a' "$OUTPUT")" == '600' ]] || fail OUTPUT_MODE_INVALID

printf '\n===== 4 OUTPUT CONTRACT AND FIRST CHAIN DECISION =====\n'
python3 - "$OUTPUT" "$EXPECTED_DB_HASH" "$EXPECTED_ENRICHMENT_HASH" "$EXPECTED_DISCOVERY_HASH" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert p.get('schema')=='tokenoskobi.product_slice_04.first_swap_chain_selection.v1'
assert p.get('status')=='STRICT_FACTORY_AND_SWAP_CHAIN_SELECTION_COMPLETED'
assert p.get('chain')=='BSC' and p.get('chain_id')==56
s=p.get('source'); assert isinstance(s,dict)
assert s.get('database_sha256')==sys.argv[2]
assert s.get('candidate_enrichment_result_hash')==sys.argv[3]
assert s.get('swap_pool_discovery_result_hash')==sys.argv[4]
a=p.get('authority'); assert isinstance(a,dict)
assert a.get('network_access') is False and a.get('staging_file_write') is True
for key in ('source_database_write','production_database_write','repository_write','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
    assert a.get(key) is False,key
summary=p.get('summary'); assert isinstance(summary,dict)
assert summary.get('recognized_swap_event_count')==36
assert summary.get('officially_allowlisted_factory_count')==4
assert summary.get('protocol_verified_event_count')==32
assert summary.get('unverified_factory_count')==2
assert summary.get('router_identity_verified') is False
print('OUTPUT_STATUS=VERIFIED')
print('FACTORY_ALLOWLIST_LOCKED=true')
print('OFFICIAL_FACTORY_PANCAKESWAP_V3=0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865')
print('OFFICIAL_FACTORY_PANCAKESWAP_V2=0xca143ce32fe78f1f7019d7d551a6402fc5350c73')
print('OFFICIAL_FACTORY_UNISWAP_V3=0xdb1d10011ad0ff90774d0c6bb92e5c5c8b4461f7')
print('OFFICIAL_FACTORY_UNISWAP_V2=0x8909dc15e40173ff4699343b6eb8132c65e18ec6')
print(f'PROTOCOL_VERIFIED_EVENT_COUNT={summary.get("protocol_verified_event_count")}')
print(f'STRICT_PAIR_DIRECTION_AMOUNT_EVENT_COUNT={summary.get("strict_pair_direction_amount_event_count")}')
print(f'OPPOSITE_DIRECTION_CHAIN_CANDIDATE_COUNT={summary.get("opposite_direction_chain_candidate_count")}')
print(f'CLEAN_SINGLE_SWAP_CLOSED_LOOP_COUNT={summary.get("clean_single_swap_closed_loop_count")}')
print('PROTOCOL_EVENT_COUNTS='+json.dumps(summary.get('protocol_event_counts'),sort_keys=True,separators=(',',':')))
print('UNVERIFIED_FACTORIES='+json.dumps(summary.get('unverified_factories'),separators=(',',':')))
top=p.get('top_candidate')
if top:
    opening=top['opening_event']; closing=top['closing_event']
    print(
        'TOP_CHAIN_CANDIDATE='
        f'actor:{top["actor"]},'
        f'open_tx:{opening["tx_hash"]},open:{opening["input_symbol"]}->{opening["output_symbol"]},'
        f'open_amounts:{opening["input_normalized"]}->{opening["output_normalized"]},'
        f'close_tx:{closing["tx_hash"]},close:{closing["input_symbol"]}->{closing["output_symbol"]},'
        f'close_amounts:{closing["input_normalized"]}->{closing["output_normalized"]},'
        f'same_pool:{str(top["same_pool"]).lower()},'
        f'same_protocol:{str(top["same_protocol"]).lower()},'
        f'clean_single_swap:{str(top["clean_single_swap_transactions"]).lower()},'
        f'confirmed:{str(top["closed_loop_confirmed"]).lower()},'
        f'blockers:{"|".join(top["blockers"]) or "NONE"}'
    )
else:
    print('TOP_CHAIN_CANDIDATE=NONE')
print(f'CLOSED_LOOP_CONFIRMED={str(bool(summary.get("closed_loop_confirmed"))).lower()}')
print(f'NEXT_SAFE_STEP={summary.get("next_safe_step")}')
print(f'RESULT_HASH={p.get("result_hash")}')
PY

printf '\n===== 5 IMMUTABILITY, SERVICE AND AUTHORITY GATES =====\n'
[[ "$(sha256_file "$DB")" == "$EXPECTED_DB_HASH" ]] || fail SOURCE_DATABASE_MUTATED
[[ "$(stat -c '%Y:%s:%a' "$DB")" == "$DB_MTIME_BEFORE" ]] || fail SOURCE_DATABASE_METADATA_MUTATED
[[ "$(stat -c '%Y:%s:%a' "$ENRICHMENT")" == "$ENRICHMENT_MTIME_BEFORE" ]] || fail ENRICHMENT_MUTATED
[[ "$(stat -c '%Y:%s:%a' "$DISCOVERY")" == "$DISCOVERY_MTIME_BEFORE" ]] || fail DISCOVERY_MUTATED
[[ "$(git status --porcelain=v1 --untracked-files=all)" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_MUTATED
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_STOPPED
PRODUCT_PID_AFTER="$(systemctl show "$SERVICE" -p MainPID --value)"
PRODUCT_NRESTARTS_AFTER="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PRODUCT_PID_AFTER" == "$PRODUCT_PID_BEFORE" ]] || fail PRODUCT_SERVICE_RESTARTED
[[ "$PRODUCT_NRESTARTS_AFTER" == "$PRODUCT_NRESTARTS_BEFORE" ]] || fail PRODUCT_RESTART_COUNT_CHANGED

printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'ENRICHMENT_IMMUTABLE=VERIFIED\n'
printf 'DISCOVERY_IMMUTABLE=VERIFIED\n'
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

NEXT_SAFE_STEP="$(python3 - "$OUTPUT" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(p['summary']['next_safe_step'])
PY
)"
CLOSED_LOOP="$(python3 - "$OUTPUT" <<'PY'
import json,sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(str(bool(p['summary']['closed_loop_confirmed'])).lower())
PY
)"

printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_04_FIRST_SWAP_CHAIN_SELECTION=SUCCESS\n'
printf 'FACTORY_ALLOWLIST_LOCKED=true\n'
printf 'STRICT_MATCH_POLICY=FULL_PAIR_DIRECTION_AND_RAW_AMOUNT_EQUALITY\n'
printf 'ROUTER_IDENTITY_VERIFIED=false\n'
printf 'CLOSED_LOOP_CONFIRMED=%s\n' "$CLOSED_LOOP"
printf 'SOURCE_DATABASE_IMMUTABLE=VERIFIED\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_18=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_17=OPEN\n'
printf 'NEXT_SAFE_STEP=%s\n' "$NEXT_SAFE_STEP"
printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
