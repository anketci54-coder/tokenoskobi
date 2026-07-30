#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_HEAD='3bd89d728b1420090447c7f8c09a1a8f271b54b1'
DB="$ROOT/runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
SERVICE='tokenoskobi-product-slice-02.service'

cd "$ROOT"

fail() {
  printf 'BLOCKED=%s\n' "$1" >&2
  exit 1
}

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

printf '\n===== 1 EXACT READ-ONLY PREFLIGHT =====\n'
[[ "$(git branch --show-current)" == 'main' ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail LOCAL_HEAD_CHANGED
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail WORKTREE_NOT_CLEAN

git fetch --quiet origin main
[[ "$(git rev-parse origin/main)" == "$EXPECTED_HEAD" ]] || fail ORIGIN_MAIN_CHANGED
[[ -f "$DB" && -s "$DB" ]] || fail ERA64I_DATABASE_MISSING
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE

DB_HASH_BEFORE="$(sha256_file "$DB")"
DB_MTIME_BEFORE="$(stat -c '%Y:%s:%a' "$DB")"
REPO_STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=all)"

printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'DATABASE=%s\n' "$DB"
printf 'DATABASE_SHA256_BEFORE=%s\n' "$DB_HASH_BEFORE"
printf 'PRODUCT_SERVICE_ACTIVE=true\n'

printf '\n===== 2 SQLITE SCHEMA, COUNTS AND REAL DATA INVENTORY =====\n'
DB="$DB" python3 - <<'PY'
from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DB = Path(os.environ['DB']).resolve()
SOURCE = 'era64i_historical_wallet_transfer_staging_v1'
RECEIPTS = 'era64j_historical_receipt_cost_enrichment_v1'
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ZERO = '0x0000000000000000000000000000000000000000'
PCS_V2_ROUTER_CANDIDATE = '0x10ed43c718714eb63d5aa57b78b54704e256024e'


def safe_json(value: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(str(value or ''))
    except (json.JSONDecodeError, TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def short(value: str, width: int = 18) -> str:
    value = str(value)
    return value if len(value) <= width else value[:width] + '…'


uri = f'file:{DB}?mode=ro&immutable=1'
conn = sqlite3.connect(uri, uri=True)
conn.row_factory = sqlite3.Row
try:
    conn.execute('PRAGMA query_only=ON')
    integrity = str(conn.execute('PRAGMA integrity_check').fetchone()[0])
    tables = [str(row[0]) for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )]
    print(f'DATABASE_INTEGRITY={integrity}')
    print(f'TABLE_COUNT={len(tables)}')
    print('TABLES=' + ','.join(tables))
    if integrity.lower() != 'ok':
        raise SystemExit('DATABASE_INTEGRITY_FAILED')
    if SOURCE not in tables or RECEIPTS not in tables:
        raise SystemExit('REQUIRED_TABLE_MISSING')

    source_columns = [str(row['name']) for row in conn.execute(f'PRAGMA table_info({SOURCE})')]
    receipt_columns = [str(row['name']) for row in conn.execute(f'PRAGMA table_info({RECEIPTS})')]
    print('SOURCE_COLUMNS=' + ','.join(source_columns))
    print('RECEIPT_COLUMNS=' + ','.join(receipt_columns))

    required_source = {
        'event_uid', 'token_address', 'from_address', 'to_address', 'amount_raw',
        'tx_hash', 'log_index', 'block_number', 'block_time_utc', 'evidence_hash',
    }
    required_receipt = {
        'tx_hash', 'receipt_status', 'gas_cost_wei', 'tx_from_address',
        'tx_to_address', 'raw_receipt_json', 'raw_transaction_json', 'evidence_hash',
    }
    if not required_source.issubset(source_columns):
        raise SystemExit('SOURCE_SCHEMA_INCOMPLETE')
    if not required_receipt.issubset(receipt_columns):
        raise SystemExit('RECEIPT_SCHEMA_INCOMPLETE')

    source_count = int(conn.execute(f'SELECT COUNT(*) FROM {SOURCE}').fetchone()[0])
    tx_count = int(conn.execute(f'SELECT COUNT(DISTINCT tx_hash) FROM {SOURCE}').fetchone()[0])
    token_count = int(conn.execute(f'SELECT COUNT(DISTINCT token_address) FROM {SOURCE}').fetchone()[0])
    wallet_count = int(conn.execute(f'''
        SELECT COUNT(*) FROM (
          SELECT from_address AS wallet FROM {SOURCE}
          UNION
          SELECT to_address AS wallet FROM {SOURCE}
        )
    ''').fetchone()[0])
    receipt_count = int(conn.execute(f'SELECT COUNT(*) FROM {RECEIPTS}').fetchone()[0])
    joined_events = int(conn.execute(f'''
        SELECT COUNT(*) FROM {SOURCE} s JOIN {RECEIPTS} r ON r.tx_hash=s.tx_hash
    ''').fetchone()[0])
    failed_receipts = int(conn.execute(f'SELECT COUNT(*) FROM {RECEIPTS} WHERE receipt_status!=1').fetchone()[0])
    total_gas_wei = sum(int(str(row[0])) for row in conn.execute(f'SELECT gas_cost_wei FROM {RECEIPTS}'))

    print(f'SOURCE_EVENT_COUNT={source_count}')
    print(f'SOURCE_TRANSACTION_COUNT={tx_count}')
    print(f'SOURCE_DISTINCT_WALLET_COUNT={wallet_count}')
    print(f'SOURCE_DISTINCT_TOKEN_COUNT={token_count}')
    print(f'RECEIPT_COUNT={receipt_count}')
    print(f'RECEIPT_JOINED_EVENT_COUNT={joined_events}')
    print(f'FAILED_RECEIPT_COUNT={failed_receipts}')
    print(f'TOTAL_GAS_COST_WEI={total_gas_wei}')
    print(f'REAL_DATA_COUNTS_MATCH_EXPECTED={str((source_count, tx_count, wallet_count, token_count, receipt_count) == (367, 277, 340, 3, 277)).lower()}')

    print('\n===== TOKEN DISTRIBUTION =====')
    token_rows = conn.execute(f'''
      SELECT token_address,COUNT(*) AS events,COUNT(DISTINCT tx_hash) AS txs,
             COUNT(DISTINCT from_address) AS senders,COUNT(DISTINCT to_address) AS receivers
      FROM {SOURCE}
      GROUP BY token_address
      ORDER BY events DESC,token_address
    ''').fetchall()
    for index, row in enumerate(token_rows, start=1):
        print(
            f'TOKEN_{index}=address:{row["token_address"]},events:{row["events"]},'
            f'txs:{row["txs"]},senders:{row["senders"]},receivers:{row["receivers"]}'
        )

    source_rows = [dict(row) for row in conn.execute(f'''
      SELECT event_uid,token_address,from_address,to_address,amount_raw,tx_hash,
             log_index,block_number,block_time_utc,evidence_hash
      FROM {SOURCE}
      ORDER BY block_number,tx_hash,log_index
    ''')]
    receipt_rows = [dict(row) for row in conn.execute(f'''
      SELECT tx_hash,block_number,receipt_status,gas_cost_wei,tx_from_address,
             tx_to_address,raw_receipt_json,raw_transaction_json,evidence_hash
      FROM {RECEIPTS}
      ORDER BY block_number,transaction_index,tx_hash
    ''')]
finally:
    conn.close()

receipts_by_tx = {str(row['tx_hash']).lower(): row for row in receipt_rows}
events_by_tx: dict[str, list[dict[str, Any]]] = defaultdict(list)
for row in source_rows:
    events_by_tx[str(row['tx_hash']).lower()].append(row)

print('\n===== 3 RECEIPT LOG AND TRANSACTION SURFACE =====')
topic0_counts: Counter[str] = Counter()
non_transfer_topic_counts: Counter[str] = Counter()
log_address_counts: Counter[str] = Counter()
log_shape_counts: Counter[str] = Counter()
tx_to_counts: Counter[str] = Counter()
selector_counts: Counter[str] = Counter()
raw_tx_available = 0
raw_tx_missing = 0
receipt_parse_errors = 0
receipt_log_count = 0
pcs_v2_router_candidate_count = 0

for row in receipt_rows:
    tx_to = str(row.get('tx_to_address') or '').lower()
    tx_to_counts[tx_to or 'EMPTY'] += 1
    if tx_to == PCS_V2_ROUTER_CANDIDATE:
        pcs_v2_router_candidate_count += 1

    raw_tx = safe_json(row.get('raw_transaction_json'))
    if raw_tx:
        raw_tx_available += 1
        selector = str(raw_tx.get('input') or '')[:10].lower()
        selector_counts[selector or 'EMPTY'] += 1
    else:
        raw_tx_missing += 1

    receipt = safe_json(row.get('raw_receipt_json'))
    logs = receipt.get('logs')
    if not isinstance(logs, list):
        receipt_parse_errors += 1
        continue
    for log in logs:
        if not isinstance(log, dict):
            continue
        receipt_log_count += 1
        address = str(log.get('address') or '').lower()
        topics = log.get('topics')
        data = str(log.get('data') or '')
        if address:
            log_address_counts[address] += 1
        topic0 = ''
        topic_count = 0
        if isinstance(topics, list):
            topic_count = len(topics)
            if topics:
                topic0 = str(topics[0]).lower()
        if topic0:
            topic0_counts[topic0] += 1
            if topic0 != TRANSFER_TOPIC:
                non_transfer_topic_counts[topic0] += 1
        log_shape_counts[f'topics:{topic_count},data_hex:{max(0, len(data)-2)}'] += 1

print(f'RECEIPT_LOG_COUNT={receipt_log_count}')
print(f'RECEIPT_PARSE_ERROR_COUNT={receipt_parse_errors}')
print(f'RAW_TRANSACTION_JSON_AVAILABLE={raw_tx_available}')
print(f'RAW_TRANSACTION_JSON_MISSING={raw_tx_missing}')
print(f'PCS_V2_ROUTER_ADDRESS_APPEARANCE_COUNT={pcs_v2_router_candidate_count}')

for index, (address, count) in enumerate(tx_to_counts.most_common(20), start=1):
    print(f'TOP_TX_TO_{index}=address:{address},tx_count:{count}')
for index, (address, count) in enumerate(log_address_counts.most_common(20), start=1):
    print(f'TOP_LOG_ADDRESS_{index}=address:{address},log_count:{count}')
for index, (topic, count) in enumerate(topic0_counts.most_common(20), start=1):
    print(f'TOP_TOPIC0_{index}=topic:{topic},log_count:{count},is_transfer:{str(topic == TRANSFER_TOPIC).lower()}')
for index, (topic, count) in enumerate(non_transfer_topic_counts.most_common(20), start=1):
    print(f'TOP_NON_TRANSFER_TOPIC0_{index}=topic:{topic},log_count:{count}')
for index, (selector, count) in enumerate(selector_counts.most_common(20), start=1):
    print(f'TOP_INPUT_SELECTOR_{index}=selector:{selector},tx_count:{count}')
for index, (shape, count) in enumerate(log_shape_counts.most_common(15), start=1):
    print(f'TOP_LOG_SHAPE_{index}={shape},count:{count}')

print('\n===== 4 MULTI-TOKEN AND WALLET-NET-FLOW CANDIDATES =====')
multi_token_txs: list[dict[str, Any]] = []
two_sided_actor_candidates: list[dict[str, Any]] = []
actor_token_series: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

for tx_hash, events in events_by_tx.items():
    receipt = receipts_by_tx.get(tx_hash, {})
    actor = str(receipt.get('tx_from_address') or '').lower()
    tx_to = str(receipt.get('tx_to_address') or '').lower()
    block_number = int(receipt.get('block_number') or events[0]['block_number'])
    tokens = sorted({str(event['token_address']).lower() for event in events})
    if len(tokens) >= 2:
        multi_token_txs.append({
            'tx_hash': tx_hash,
            'actor': actor,
            'tx_to': tx_to,
            'block_number': block_number,
            'event_count': len(events),
            'tokens': tokens,
        })

    if not actor or actor == ZERO:
        continue
    net: dict[str, int] = defaultdict(int)
    for event in events:
        token = str(event['token_address']).lower()
        amount = int(str(event['amount_raw']))
        src = str(event['from_address']).lower()
        dst = str(event['to_address']).lower()
        if src == actor:
            net[token] -= amount
        if dst == actor:
            net[token] += amount
    positives = sorted(token for token, amount in net.items() if amount > 0)
    negatives = sorted(token for token, amount in net.items() if amount < 0)
    for token, amount in net.items():
        if amount:
            actor_token_series[(actor, token)].append({
                'block_number': block_number,
                'tx_hash': tx_hash,
                'net_raw': amount,
                'tx_to': tx_to,
            })
    if positives and negatives:
        two_sided_actor_candidates.append({
            'tx_hash': tx_hash,
            'actor': actor,
            'tx_to': tx_to,
            'block_number': block_number,
            'positive_tokens': positives,
            'negative_tokens': negatives,
            'event_count': len(events),
            'gas_cost_wei': str(receipt.get('gas_cost_wei') or '0'),
        })

multi_token_txs.sort(key=lambda item: (item['block_number'], item['tx_hash']))
two_sided_actor_candidates.sort(key=lambda item: (item['block_number'], item['tx_hash']))

print(f'MULTI_TOKEN_TRANSACTION_COUNT={len(multi_token_txs)}')
print(f'TWO_SIDED_TX_FROM_FLOW_CANDIDATE_COUNT={len(two_sided_actor_candidates)}')
for index, item in enumerate(multi_token_txs[:20], start=1):
    print(
        f'MULTI_TOKEN_CANDIDATE_{index}=tx:{item["tx_hash"]},block:{item["block_number"]},'
        f'actor:{item["actor"]},tx_to:{item["tx_to"]},events:{item["event_count"]},'
        f'tokens:{"|".join(item["tokens"])}'
    )
for index, item in enumerate(two_sided_actor_candidates[:20], start=1):
    print(
        f'TWO_SIDED_ACTOR_CANDIDATE_{index}=tx:{item["tx_hash"]},block:{item["block_number"]},'
        f'actor:{item["actor"]},tx_to:{item["tx_to"]},'
        f'in:{"|".join(item["positive_tokens"])},out:{"|".join(item["negative_tokens"])},'
        f'events:{item["event_count"]},gas_wei:{item["gas_cost_wei"]}'
    )

round_trip_candidates: list[dict[str, Any]] = []
for (actor, token), rows in actor_token_series.items():
    ordered = sorted(rows, key=lambda item: (item['block_number'], item['tx_hash']))
    positive = [item for item in ordered if item['net_raw'] > 0]
    negative = [item for item in ordered if item['net_raw'] < 0]
    if not positive or not negative:
        continue
    valid_pair = None
    for first in ordered:
        for second in ordered:
            if second['block_number'] < first['block_number']:
                continue
            if first['tx_hash'] == second['tx_hash']:
                continue
            if (first['net_raw'] > 0 > second['net_raw']) or (first['net_raw'] < 0 < second['net_raw']):
                valid_pair = (first, second)
                break
        if valid_pair:
            break
    if valid_pair:
        first, second = valid_pair
        round_trip_candidates.append({
            'actor': actor,
            'token': token,
            'first': first,
            'second': second,
            'observation_count': len(ordered),
        })

round_trip_candidates.sort(key=lambda item: (
    item['first']['block_number'], item['second']['block_number'], item['actor'], item['token']
))
print(f'TRANSFER_FLOW_ROUND_TRIP_CANDIDATE_COUNT={len(round_trip_candidates)}')
for index, item in enumerate(round_trip_candidates[:20], start=1):
    first = item['first']
    second = item['second']
    print(
        f'ROUND_TRIP_CANDIDATE_{index}=actor:{item["actor"]},token:{item["token"]},'
        f'first_tx:{first["tx_hash"]},first_block:{first["block_number"]},first_sign:{"IN" if first["net_raw"] > 0 else "OUT"},'
        f'second_tx:{second["tx_hash"]},second_block:{second["block_number"]},second_sign:{"IN" if second["net_raw"] > 0 else "OUT"},'
        f'observations:{item["observation_count"]}'
    )

print('\n===== 5 FAIL-CLOSED READINESS CLASSIFICATION =====')
raw_tx_complete = raw_tx_available == len(receipt_rows)
closed_loop_ready = bool(two_sided_actor_candidates and round_trip_candidates and raw_tx_complete)
print(f'RAW_TRANSACTION_COVERAGE_COMPLETE={str(raw_tx_complete).lower()}')
print(f'SWAP_DIRECTION_CLASSIFIED=false')
print(f'ROUTER_POOL_IDENTITY_VERIFIED=false')
print(f'TOKEN_METADATA_DECIMALS_COMPLETE=false')
print(f'EXECUTION_PRICE_COMPLETE=false')
print(f'DEX_FEE_SLIPPAGE_TAX_COMPLETE=false')
print(f'CLOSED_LOOP_CONFIRMED=false')
print(f'TRANSFER_FLOW_CANDIDATES_PRESENT={str(bool(round_trip_candidates)).lower()}')
print(f'EXISTING_DATA_ALONE_CLOSED_LOOP_READY={str(closed_loop_ready).lower()}')
print('CEX_EVIDENCE_STATUS=UNVERIFIED_OR_UNAVAILABLE')
print('LEGACY_PLACEHOLDER_WHALE_REGISTRY_ADMISSIBLE=false')
print('NEXT_REQUIRED_ENRICHMENT=ALL_CANDIDATE_TRANSACTION_INPUTS_PLUS_TOKEN_METADATA_PLUS_ALLOWLISTED_DEX_DECODE')
print('AUDIT_AUTHORITY=READ_ONLY_NO_DATABASE_WRITE_NO_PANEL_MUTATION_NO_TRADE')
PY

printf '\n===== 6 IMMUTABILITY AND AUTHORITY GATES =====\n'
DB_HASH_AFTER="$(sha256_file "$DB")"
DB_MTIME_AFTER="$(stat -c '%Y:%s:%a' "$DB")"
REPO_STATUS_AFTER="$(git status --porcelain=v1 --untracked-files=all)"

[[ "$DB_HASH_AFTER" == "$DB_HASH_BEFORE" ]] || fail DATABASE_HASH_CHANGED
[[ "$DB_MTIME_AFTER" == "$DB_MTIME_BEFORE" ]] || fail DATABASE_METADATA_CHANGED
[[ "$REPO_STATUS_AFTER" == "$REPO_STATUS_BEFORE" ]] || fail REPOSITORY_STATE_CHANGED
[[ -z "$REPO_STATUS_AFTER" ]] || fail WORKTREE_NOT_CLEAN_AFTER_AUDIT

printf 'DATABASE_SHA256_AFTER=%s\n' "$DB_HASH_AFTER"
printf 'DATABASE_IMMUTABLE=VERIFIED\n'
printf 'REPOSITORY_MUTATION=false\n'
printf 'PRODUCTION_DATABASE_WRITE=false\n'
printf 'PANEL_MUTATION=false\n'
printf 'SERVICE_RESTARTED=false\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'

printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_04_READONLY_DATASET_AUDIT=SUCCESS\n'
printf 'ISSUE_17=OPEN\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'NEXT_SAFE_STEP=INTERPRET_REAL_DATA_AND_LOCK_FIRST_CLOSED_LOOP_SCOPE\n'
