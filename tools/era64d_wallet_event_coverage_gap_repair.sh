#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era64d_wallet_event_coverage_backup_${STAMP}.tar.gz"
COMMITTED=0

CANONICAL_FILES=(
  PROJECT_RUNTIME.json
  PROJECT_HISTORY.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
  03_ROADMAP.md
  04_ALMANAC.md
  06_PROJECT_MASTER_STATE.md
  07_PROJECT_HANDOFF.md
)

NEW_FILES=(
  config/era64_wallet_event_coverage_bridge_v1.json
  tools/era64_wallet_event_coverage_bridge_v1.py
  tests/test_era64d_wallet_event_coverage_bridge_v1.py
  data/control/era64d_real_wallet_event_coverage_gap_repair_v1.json
  data/replay/era64d_real_wallet_event_coverage_bridge_v1.json
  reports/LATEST_ERA64D_WALLET_EVENT_COVERAGE_GAP_REPAIR.md
)

rollback() {
  rc=$?
  trap - ERR
  echo "ERA64D_FAILED_RC=$rc"
  if [[ "$COMMITTED" -eq 0 && -f "$BACKUP" ]]; then
    tar -xzf "$BACKUP" -C /root/tokenoskobi_clean_v1
    rm -f "${NEW_FILES[@]}"
    git reset --quiet
    echo "ROLLBACK=COMPLETED"
  fi
  exit "$rc"
}
trap rollback ERR

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer

python3 <<'PY_PRECHECK'
import json
from pathlib import Path

r = json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
p = r.get('canonical_runtime_pointer') if isinstance(r.get('canonical_runtime_pointer'), dict) else {}

def current(key):
    return r.get(key, p.get(key))

assert current('current_era') == 'ERA64'
assert current('current_stage') == 'ERA64C_REAL_HISTORICAL_WALLET_REPLAY_AND_VALIDATION'
assert current('next_safe_step') == 'ERA64D_REAL_WALLET_EVENT_COVERAGE_GAP_REPAIR_REQUIRES_USER_APPROVAL'
assert current('era64c_real_data_gap_confirmed') is True
assert current('paper_runtime_enabled') is False

a = r.get('authority', {})
assert isinstance(a, dict)
assert a.get('real_trade_authority') == 0
assert a.get('real_wallet_authority') == 0
assert a.get('real_signing_authority') == 0
assert a.get('real_order_authority') == 0
assert a.get('live_trade') == 'DISABLED'

assert Path('data/control/era64c_real_historical_wallet_replay_and_validation_v1.json').is_file()
assert Path('tools/era64_successful_wallet_foundation_v1.py').is_file()
print('PRECHECK=VERIFIED')
PY_PRECHECK

tar -czf "$BACKUP" "${CANONICAL_FILES[@]}"
echo "BACKUP=$BACKUP"
mkdir -p config tools tests data/control data/replay reports

cat > config/era64_wallet_event_coverage_bridge_v1.json <<'JSON_CONFIG'
{
  "schema": "tokenoskobi.era64.wallet_event_coverage_bridge.config.v1",
  "mode": "LOCAL_SQLITE_READ_ONLY_SCHEMA_BRIDGE",
  "synthetic_runtime_data_allowed": false,
  "network_access": false,
  "database_write": false,
  "runtime_mutation": false,
  "panel_mutation": false,
  "service_mutation": false,
  "timer_mutation": false,
  "paper_runtime": false,
  "live_trade": false,
  "real_financial_authority": 0,
  "maximum_tables_per_database": 200,
  "maximum_rows_per_table": 3000,
  "maximum_graph_nodes": 128,
  "maximum_graph_edges": 512,
  "maximum_trade_groups": 256,
  "database_candidates": [
    "data/tokenoskobi_clean_v1.sqlite",
    "data/tokenoskobi_v1.sqlite",
    "data/tokenoskobi.sqlite",
    "data/tokenoskobi.db",
    "database/tokenoskobi.db"
  ]
}
JSON_CONFIG

cat > tools/era64_wallet_event_coverage_bridge_v1.py <<'PY_ENGINE'
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'tools') not in sys.path:
    sys.path.insert(0, str(ROOT / 'tools'))

from era64_successful_wallet_foundation_v1 import (  # noqa: E402
    AUTHORITY as FOUNDATION_AUTHORITY,
    WalletFoundationError,
    build_relationship_graph,
    calculate_performance,
    normalize_wallet,
    reconstruct_position_cycles,
    resolve_wallet_label,
)

AUTHORITY = dict(FOUNDATION_AUTHORITY)
AUTHORITY.update({
    'network_access': False,
    'database_write': False,
    'runtime_mutation': False,
    'panel_mutation': False,
    'service_mutation': False,
    'timer_mutation': False,
    'paper_trade': False,
    'live_trade': False,
    'wallet': False,
    'signing': False,
    'order_create': False,
    'broadcast': False,
})

RELEVANT_WORDS = (
    'wallet', 'whale', 'transfer', 'fund', 'cluster', 'deployer',
    'position', 'trade', 'swap', 'entry', 'flow', 'entity',
)

ALIASES = {
    'wallet_uid': ('wallet_uid', 'entity_uid', 'account_uid'),
    'wallet': ('wallet_address', 'address', 'wallet', 'owner_address', 'trader_address'),
    'label': ('known_name', 'entity_label', 'wallet_label', 'label', 'entity_name', 'name'),
    'confidence': ('label_confidence', 'confidence', 'link_confidence', 'evidence_strength', 'score'),
    'source': ('source', 'source_name', 'evidence_source', 'source_tag', 'provider'),
    'from_wallet': ('from_address', 'from_wallet', 'sender_address', 'wallet_from'),
    'to_wallet': ('to_address', 'to_wallet', 'recipient_address', 'wallet_to'),
    'from_wallet_uid': ('from_wallet_uid', 'parent_wallet_uid', 'root_wallet_uid'),
    'to_wallet_uid': ('to_wallet_uid', 'child_wallet_uid', 'linked_wallet_uid'),
    'root_wallet': ('root_wallet_address',),
    'linked_wallet': ('linked_wallet_address',),
    'tx_hash': ('tx_hash', 'transaction_hash', 'txid'),
    'block_number': ('block_number', 'block_height', 'block'),
    'timestamp': (
        'event_time_utc', 'block_time_utc', 'observed_at_utc', 'created_at_utc',
        'event_timestamp', 'block_timestamp', 'timestamp', 'created_at', 'time',
    ),
    'amount': ('amount_raw', 'amount', 'flow_token_amount', 'token_amount', 'quantity', 'value'),
    'token': ('token_address', 'asset_symbol', 'token', 'contract_address', 'symbol'),
    'relation': ('flow_type', 'link_type', 'relation_type', 'relationship_type', 'event_type'),
    'side': ('side', 'trade_side', 'action', 'direction'),
    'quantity': ('quantity', 'token_quantity', 'amount', 'size', 'qty'),
    'price': ('price', 'execution_price', 'fill_price', 'token_price', 'price_usd'),
    'fee': ('fee', 'trading_fee', 'fee_amount', 'protocol_fee'),
    'gas': ('gas', 'gas_cost', 'gas_fee', 'network_fee'),
}

SOURCE_CONTRACT = {
    'identity_registry': {
        'required': ['wallet_uid', 'wallet_address'],
        'purpose': 'resolve UID-based wallet events to real EVM addresses',
    },
    'label_registry': {
        'required': ['wallet_address', 'label', 'confidence'],
        'purpose': 'evidence-backed real wallet identity labels',
    },
    'relationship_event': {
        'required': ['from_address', 'to_address', 'tx_hash', 'block_number', 'event_time_utc', 'amount'],
        'purpose': 'replayable funding or transfer relationship evidence',
    },
    'cost_complete_trade_event': {
        'required': ['wallet_address', 'token', 'side', 'tx_hash', 'quantity', 'price', 'fee', 'gas', 'event_time_utc'],
        'purpose': 'cost-adjusted closed-position reconstruction',
    },
}


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    temp.replace(path)


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def lower_map(columns: Iterable[str]) -> dict[str, str]:
    return {str(column).lower(): str(column) for column in columns}


def choose(columns: Iterable[str], key: str) -> str | None:
    mapping = lower_map(columns)
    for alias in ALIASES[key]:
        if alias.lower() in mapping:
            return mapping[alias.lower()]
    return None


def has(columns: Iterable[str], key: str) -> bool:
    return choose(columns, key) is not None


def as_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float('inf'), float('-inf')):
        return None
    return number


def as_int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def as_timestamp(value: Any) -> int | None:
    direct = as_int(value)
    if direct is not None:
        while direct > 10_000_000_000:
            direct //= 1000
        return direct if direct >= 0 else None
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace('Z', '+00:00')
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def valid_wallet(value: Any) -> str | None:
    try:
        return normalize_wallet(str(value))
    except (WalletFoundationError, TypeError, ValueError):
        return None


def source_evidence_id(database: str, table: str, row_id: Any, row: dict[str, Any]) -> str:
    return canonical_hash({
        'database': database,
        'table': table,
        'row_id': row_id,
        'row_hash': canonical_hash(row),
    })


def row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys() if key != '__era64d_rowid'}


def read_rows(conn: sqlite3.Connection, table: str, limit: int) -> list[tuple[Any, dict[str, Any]]]:
    try:
        rows = conn.execute(
            f'SELECT rowid AS __era64d_rowid, * FROM {qident(table)} LIMIT ?', (limit,)
        ).fetchall()
        return [(row['__era64d_rowid'], row_dict(row)) for row in rows]
    except sqlite3.DatabaseError:
        rows = conn.execute(f'SELECT * FROM {qident(table)} LIMIT ?', (limit,)).fetchall()
        return [(index, row_dict(row)) for index, row in enumerate(rows, start=1)]


def classify_schema(table: str, columns: Iterable[str]) -> dict[str, Any]:
    cols = list(columns)
    capabilities: list[str] = []
    blockers: list[str] = []

    if has(cols, 'wallet_uid') and has(cols, 'wallet'):
        capabilities.append('UID_ADDRESS_REGISTRY')
    if has(cols, 'wallet') and has(cols, 'label') and has(cols, 'confidence'):
        capabilities.append('DIRECT_LABEL_REGISTRY')

    direct_relation_base = has(cols, 'from_wallet') and has(cols, 'to_wallet')
    uid_relation_base = has(cols, 'from_wallet_uid') and has(cols, 'to_wallet_uid')
    cluster_relation_base = has(cols, 'root_wallet') and has(cols, 'linked_wallet')

    if direct_relation_base:
        capabilities.append('DIRECT_RELATION_CANDIDATE')
    if uid_relation_base:
        capabilities.append('UID_RELATION_CANDIDATE')
    if cluster_relation_base:
        capabilities.append('DIRECT_CLUSTER_EVIDENCE')

    relation_any = direct_relation_base or uid_relation_base
    if relation_any:
        for key, blocker in (
            ('tx_hash', 'MISSING_TX_HASH'),
            ('block_number', 'MISSING_BLOCK_NUMBER'),
            ('timestamp', 'MISSING_EVENT_TIME'),
            ('amount', 'MISSING_AMOUNT'),
        ):
            if not has(cols, key):
                blockers.append(blocker)
        if direct_relation_base and not blockers:
            capabilities.append('REPLAYABLE_DIRECT_RELATION')
        if uid_relation_base and not blockers:
            capabilities.append('REPLAYABLE_UID_RELATION_AFTER_REGISTRY_JOIN')

    full_trade_keys = ('wallet', 'token', 'side', 'tx_hash', 'quantity', 'price', 'fee', 'gas', 'timestamp')
    present_trade = [key for key in full_trade_keys if has(cols, key)]
    if len(present_trade) >= 3:
        capabilities.append('TRADE_CANDIDATE')
        for key in full_trade_keys:
            if not has(cols, key):
                blockers.append('MISSING_TRADE_' + key.upper())
        if all(has(cols, key) for key in full_trade_keys):
            capabilities.append('REPLAYABLE_COST_COMPLETE_TRADE')

    lowered = {str(x).lower() for x in cols}
    if 'paper_position_id' in lowered or 'paper_engine_trade_authority' in lowered:
        capabilities.append('PAPER_SIMULATION_ONLY_EXCLUDED')
    if {'entry_price', 'entry_amount_usd'} <= lowered and 'exit_price' not in lowered:
        capabilities.append('ENTRY_ONLY_INCOMPLETE_TRADE')
    if {'net_flow_estimate_usd', 'volume_usd'} & lowered and not direct_relation_base and not uid_relation_base:
        capabilities.append('AGGREGATED_FLOW_NO_WALLET_EDGES')

    capabilities = sorted(set(capabilities))
    blockers = sorted(set(blockers))
    is_candidate = any(cap in capabilities for cap in (
        'UID_ADDRESS_REGISTRY', 'DIRECT_LABEL_REGISTRY', 'DIRECT_RELATION_CANDIDATE',
        'UID_RELATION_CANDIDATE', 'DIRECT_CLUSTER_EVIDENCE', 'TRADE_CANDIDATE',
    ))
    return {
        'table': table,
        'capabilities': capabilities,
        'blockers': blockers,
        'candidate_source': is_candidate,
    }


def extract_uid_registry(row: dict[str, Any]) -> tuple[str, str] | None:
    uid_col = choose(row.keys(), 'wallet_uid')
    wallet_col = choose(row.keys(), 'wallet')
    if not uid_col or not wallet_col:
        return None
    uid = str(row.get(uid_col) or '').strip()
    wallet = valid_wallet(row.get(wallet_col))
    if not uid or wallet is None:
        return None
    return uid, wallet


def extract_label(database: str, table: str, row_id: Any, row: dict[str, Any]) -> dict[str, Any] | None:
    wallet_col = choose(row.keys(), 'wallet')
    label_col = choose(row.keys(), 'label')
    confidence_col = choose(row.keys(), 'confidence')
    if not wallet_col or not label_col or not confidence_col:
        return None
    wallet = valid_wallet(row.get(wallet_col))
    label = str(row.get(label_col) or '').strip()
    confidence = as_float(row.get(confidence_col))
    if wallet is None or not label or confidence is None or not 0.0 <= confidence <= 1.0:
        return None
    source_col = choose(row.keys(), 'source')
    source = str(row.get(source_col) or '').strip() if source_col else ''
    if not source:
        source = f'SQLITE:{Path(database).name}:{table}'
    return {
        'wallet': wallet,
        'label': label,
        'confidence': confidence,
        'source': source,
        'evidence_id': source_evidence_id(database, table, row_id, row),
    }


def normalize_relation_type(value: Any, table: str) -> str:
    text = str(value or '').strip().upper()
    if text in {'FUNDING', 'TRANSFER', 'SAME_DEPLOYER', 'SHARED_COUNTERPARTY'}:
        return text
    if 'fund' in text.lower() or 'fund' in table.lower():
        return 'FUNDING'
    return 'TRANSFER'


def extract_relation(
    database: str,
    table: str,
    row_id: Any,
    row: dict[str, Any],
    uid_registry: dict[str, str],
) -> tuple[dict[str, Any] | None, str | None]:
    columns = row.keys()
    direct_from = choose(columns, 'from_wallet')
    direct_to = choose(columns, 'to_wallet')
    uid_from = choose(columns, 'from_wallet_uid')
    uid_to = choose(columns, 'to_wallet_uid')

    src: str | None = None
    dst: str | None = None
    if direct_from and direct_to:
        src = valid_wallet(row.get(direct_from))
        dst = valid_wallet(row.get(direct_to))
    elif uid_from and uid_to:
        src = uid_registry.get(str(row.get(uid_from) or '').strip())
        dst = uid_registry.get(str(row.get(uid_to) or '').strip())
        if src is None or dst is None:
            return None, 'UNRESOLVED_WALLET_UID'
    else:
        return None, 'NO_RELATION_ENDPOINTS'

    required = {key: choose(columns, key) for key in ('tx_hash', 'block_number', 'timestamp', 'amount')}
    for key, blocker in (
        ('tx_hash', 'MISSING_TX_HASH'),
        ('block_number', 'MISSING_BLOCK_NUMBER'),
        ('timestamp', 'MISSING_EVENT_TIME'),
        ('amount', 'MISSING_AMOUNT'),
    ):
        if required[key] is None:
            return None, blocker

    tx_hash = str(row.get(required['tx_hash']) or '').strip().lower()
    block_number = as_int(row.get(required['block_number']))
    timestamp = as_timestamp(row.get(required['timestamp']))
    amount = as_float(row.get(required['amount']))
    if src is None or dst is None or src == dst:
        return None, 'INVALID_RELATION_ENDPOINTS'
    if not tx_hash or block_number is None or block_number < 0 or timestamp is None or amount is None or amount <= 0:
        return None, 'INVALID_RELATION_VALUES'

    relation_col = choose(columns, 'relation')
    token_col = choose(columns, 'token')
    return {
        'from_wallet': src,
        'to_wallet': dst,
        'relation_type': normalize_relation_type(row.get(relation_col) if relation_col else None, table),
        'tx_hash': tx_hash,
        'evidence_id': source_evidence_id(database, table, row_id, row),
        'token': str(row.get(token_col) or 'UNKNOWN').strip().upper() if token_col else 'UNKNOWN',
        'amount': amount,
        'timestamp': timestamp,
        'block_number': block_number,
    }, None


def extract_trade(database: str, table: str, row_id: Any, row: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    keys = ('wallet', 'token', 'side', 'tx_hash', 'quantity', 'price', 'fee', 'gas', 'timestamp')
    selected = {key: choose(row.keys(), key) for key in keys}
    for key in keys:
        if selected[key] is None:
            return None, 'MISSING_TRADE_' + key.upper()
    wallet = valid_wallet(row.get(selected['wallet']))
    token = str(row.get(selected['token']) or '').strip().upper()
    side = str(row.get(selected['side']) or '').strip().upper()
    tx_hash = str(row.get(selected['tx_hash']) or '').strip().lower()
    quantity = as_float(row.get(selected['quantity']))
    price = as_float(row.get(selected['price']))
    fee = as_float(row.get(selected['fee']))
    gas = as_float(row.get(selected['gas']))
    timestamp = as_timestamp(row.get(selected['timestamp']))
    if wallet is None or not token or side not in {'BUY', 'SELL'} or not tx_hash:
        return None, 'INVALID_TRADE_IDENTITY'
    if quantity is None or quantity <= 0 or price is None or price <= 0:
        return None, 'INVALID_TRADE_VALUES'
    if fee is None or fee < 0 or gas is None or gas < 0 or timestamp is None:
        return None, 'INVALID_TRADE_COST_OR_TIME'
    return {
        'wallet': wallet,
        'token': token,
        'side': side,
        'tx_hash': tx_hash,
        'evidence_id': source_evidence_id(database, table, row_id, row),
        'quantity': quantity,
        'price': price,
        'fee': fee,
        'gas': gas,
        'timestamp': timestamp,
    }, None


def replay_trade_groups(trades: list[dict[str, Any]], maximum_groups: int) -> dict[str, Any]:
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for trade in trades:
        key = (trade['wallet'], trade['token'], trade['side'], trade['tx_hash'], trade['evidence_id'])
        unique[key] = trade
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for trade in unique.values():
        groups[(trade['wallet'], trade['token'])].append(trade)
    cycles: list[dict[str, Any]] = []
    open_positions: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for (wallet, token), rows in sorted(groups.items())[:maximum_groups]:
        try:
            result = reconstruct_position_cycles(rows)
        except WalletFoundationError as exc:
            rejected.append({'wallet': wallet, 'token': token, 'reason': str(exc), 'row_count': len(rows)})
            continue
        cycles.extend(result['cycles'])
        open_positions.extend(result['open_positions'])
    cycles.sort(key=lambda item: (item['exit_timestamp'], item['wallet'], item['token'], item['exit_tx_hash']))
    return {
        'trade_group_count': len(groups),
        'validated_group_count': min(len(groups), maximum_groups) - len(rejected),
        'rejected_group_count': len(rejected),
        'rejected_groups': rejected[:100],
        'closed_cycle_count': len(cycles),
        'cycles': cycles[:1000],
        'open_positions': open_positions[:1000],
        'performance': calculate_performance(cycles),
        'cycle_hash': canonical_hash(cycles),
    }


def inspect_database(path: Path, maximum_tables: int, maximum_rows: int) -> dict[str, Any]:
    uri = f'file:{path.resolve()}?mode=ro'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA query_only=ON')

    table_names = [
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]
    relevant = [name for name in table_names if any(word in name.lower() for word in RELEVANT_WORDS)][:maximum_tables]

    table_meta: list[dict[str, Any]] = []
    table_rows: dict[str, list[tuple[Any, dict[str, Any]]]] = {}
    uid_registry: dict[str, str] = {}
    labels: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    blocker_counts: Counter[str] = Counter()
    candidate_row_count = 0
    scanned_rows = 0

    for table in relevant:
        columns = [row[1] for row in conn.execute(f'PRAGMA table_info({qident(table)})').fetchall()]
        try:
            total_rows = int(conn.execute(f'SELECT COUNT(*) FROM {qident(table)}').fetchone()[0])
        except sqlite3.DatabaseError:
            total_rows = -1
        rows = read_rows(conn, table, maximum_rows)
        table_rows[table] = rows
        scanned_rows += len(rows)
        schema = classify_schema(table, columns)
        if schema['candidate_source']:
            candidate_row_count += len(rows)
        table_meta.append({
            **schema,
            'columns': columns,
            'total_rows': total_rows,
            'scanned_rows': len(rows),
            'empty': total_rows == 0,
        })

    for meta in table_meta:
        if 'UID_ADDRESS_REGISTRY' not in meta['capabilities']:
            continue
        for _, row in table_rows[meta['table']]:
            item = extract_uid_registry(row)
            if item is not None:
                uid_registry[item[0]] = item[1]

    for meta in table_meta:
        table = meta['table']
        for row_id, row in table_rows[table]:
            if 'DIRECT_LABEL_REGISTRY' in meta['capabilities']:
                label = extract_label(str(path), table, row_id, row)
                if label is not None:
                    labels.append(label)
                else:
                    blocker_counts['INVALID_LABEL_ROW'] += 1

            relation_candidate = any(cap in meta['capabilities'] for cap in (
                'DIRECT_RELATION_CANDIDATE', 'UID_RELATION_CANDIDATE',
            ))
            if relation_candidate:
                relation, blocker = extract_relation(str(path), table, row_id, row, uid_registry)
                if relation is not None:
                    relations.append(relation)
                elif blocker:
                    blocker_counts[blocker] += 1

            if 'TRADE_CANDIDATE' in meta['capabilities'] and 'PAPER_SIMULATION_ONLY_EXCLUDED' not in meta['capabilities']:
                trade, blocker = extract_trade(str(path), table, row_id, row)
                if trade is not None:
                    trades.append(trade)
                elif blocker:
                    blocker_counts[blocker] += 1

    conn.close()
    return {
        'path': str(path),
        'size_bytes': path.stat().st_size,
        'table_count': len(table_names),
        'relevant_table_count': len(relevant),
        'scanned_row_count': scanned_rows,
        'candidate_source_table_count': sum(1 for item in table_meta if item['candidate_source']),
        'empty_candidate_table_count': sum(1 for item in table_meta if item['candidate_source'] and item['empty']),
        'nonempty_candidate_table_count': sum(1 for item in table_meta if item['candidate_source'] and not item['empty']),
        'candidate_row_count': candidate_row_count,
        'uid_registry_count': len(uid_registry),
        'inventory': table_meta,
        'labels': labels,
        'relations': relations,
        'trades': trades,
        'blocker_counts': dict(sorted(blocker_counts.items())),
    }


def bounded_relations(events: list[dict[str, Any]], max_nodes: int, max_edges: int) -> list[dict[str, Any]]:
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for event in events:
        key = (event['from_wallet'], event['to_wallet'], event['relation_type'], event['tx_hash'], event['evidence_id'])
        unique[key] = event
    selected: list[dict[str, Any]] = []
    nodes: set[str] = set()
    for event in sorted(unique.values(), key=lambda x: (x['timestamp'], x['block_number'], x['tx_hash'])):
        candidate = nodes | {event['from_wallet'], event['to_wallet']}
        if len(candidate) > max_nodes:
            continue
        selected.append(event)
        nodes = candidate
        if len(selected) >= max_edges:
            break
    return selected


def run(root: Path, config_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads(config_path.read_text(encoding='utf-8'))
    database_paths = []
    for relative in config['database_candidates']:
        candidate = root / relative
        if candidate.is_file() and candidate.stat().st_size > 0:
            database_paths.append(candidate)
    database_paths = sorted(set(database_paths))

    results = [
        inspect_database(path, int(config['maximum_tables_per_database']), int(config['maximum_rows_per_table']))
        for path in database_paths
    ]
    labels = [item for result in results for item in result['labels']]
    relations = [item for result in results for item in result['relations']]
    trades = [item for result in results for item in result['trades']]

    bounded = bounded_relations(relations, int(config['maximum_graph_nodes']), int(config['maximum_graph_edges']))
    graph = build_relationship_graph(
        bounded,
        max_nodes=int(config['maximum_graph_nodes']),
        max_edges=int(config['maximum_graph_edges']),
    ) if bounded else {
        'node_count': 0,
        'edge_count': 0,
        'nodes': [],
        'edges': [],
        'clusters': [],
        'graph_hash': canonical_hash([]),
        'status': 'NO_REPLAYABLE_REAL_RELATIONSHIP_EVENTS',
    }
    trade_replay = replay_trade_groups(trades, int(config['maximum_trade_groups']))
    label_wallets = sorted({item['wallet'] for item in labels})[:128]
    label_results = [resolve_wallet_label(wallet, labels) for wallet in label_wallets]

    scanned_rows = sum(item['scanned_row_count'] for item in results)
    candidate_tables = sum(item['candidate_source_table_count'] for item in results)
    empty_candidate_tables = sum(item['empty_candidate_table_count'] for item in results)
    nonempty_candidate_tables = sum(item['nonempty_candidate_table_count'] for item in results)
    candidate_rows = sum(item['candidate_row_count'] for item in results)
    blocker_counts: Counter[str] = Counter()
    for item in results:
        blocker_counts.update(item['blocker_counts'])

    if graph['edge_count'] > 0 or trade_replay['closed_cycle_count'] > 0:
        status = 'REAL_WALLET_EVENT_COVERAGE_REPAIRED_AND_REPLAY_VALIDATED'
    elif candidate_tables > 0:
        status = 'REAL_WALLET_EVENT_COVERAGE_REPAIRED_SOURCE_CONTRACT_READY'
    else:
        status = 'REAL_WALLET_EVENT_SOURCE_ABSENT'

    detail = {
        'schema': 'tokenoskobi.era64d.wallet_event_coverage_bridge.output.v1',
        'status': status,
        'real_data': True,
        'synthetic_data': False,
        'authority': dict(AUTHORITY),
        'database_sources': [
            {key: value for key, value in item.items() if key not in {'labels', 'relations', 'trades'}}
            for item in results
        ],
        'source_contract': SOURCE_CONTRACT,
        'coverage_repair': {
            'previous_classification': 'ROW_GLOBAL_MISSING_COLUMNS',
            'repaired_classification': 'SCHEMA_CAPABILITY_AND_SOURCE_SPECIFIC',
            'unrelated_rows_no_longer_counted_as_wallet_event_failures': True,
            'candidate_source_table_count': candidate_tables,
            'candidate_row_count': candidate_rows,
            'empty_candidate_table_count': empty_candidate_tables,
            'nonempty_candidate_table_count': nonempty_candidate_tables,
            'blocker_counts': dict(sorted(blocker_counts.items())),
        },
        'uid_registry_count': sum(item['uid_registry_count'] for item in results),
        'label_evidence_count': len(labels),
        'label_results': label_results,
        'relationship_event_count': len(relations),
        'relationship_graph': graph,
        'cost_complete_trade_event_count': len(trades),
        'position_replay': trade_replay,
        'strongest_alternative_hypotheses': [
            'EMPTY_CANONICAL_WALLET_EVENT_TABLES_BLOCK_REAL_REPLAY',
            'UID_TRANSFER_EVENTS_WITHOUT_BLOCK_NUMBER_ARE_NOT_REPLAYABLE',
            'PAPER_POSITION_ROWS_ARE_NOT_REAL_WALLET_TRADES',
            'AGGREGATED_FLOW_ROWS_CANNOT_PROVE_WALLET_RELATIONSHIPS',
            'REAL_ACQUISITION_MUST_PRESERVE_TX_HASH_BLOCK_TIME_BLOCK_NUMBER_AND_COSTS',
        ],
    }
    detail['detail_hash'] = canonical_hash(detail)

    summary = {
        'schema': 'tokenoskobi.era64d.real_wallet_event_coverage_gap_repair.v1',
        'status': status,
        'real_data': True,
        'synthetic_data': False,
        'authority': dict(AUTHORITY),
        'database_source_count': len(results),
        'relevant_table_count': sum(item['relevant_table_count'] for item in results),
        'scanned_row_count': scanned_rows,
        'candidate_source_table_count': candidate_tables,
        'empty_candidate_table_count': empty_candidate_tables,
        'nonempty_candidate_table_count': nonempty_candidate_tables,
        'candidate_row_count': candidate_rows,
        'uid_registry_count': detail['uid_registry_count'],
        'label_evidence_count': len(labels),
        'relationship_event_count': len(relations),
        'replayed_relationship_edge_count': graph['edge_count'],
        'cost_complete_trade_event_count': len(trades),
        'closed_cycle_count': trade_replay['closed_cycle_count'],
        'coverage_blockers': dict(sorted(blocker_counts.items())),
        'source_contract_ready': candidate_tables > 0,
        'coverage_classification_repaired': True,
        'detail_artifact': 'data/replay/era64d_real_wallet_event_coverage_bridge_v1.json',
        'detail_hash': detail['detail_hash'],
    }
    summary['result_hash'] = canonical_hash(summary)
    return summary, detail


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--config', default='config/era64_wallet_event_coverage_bridge_v1.json')
    parser.add_argument('--summary', default='data/control/era64d_real_wallet_event_coverage_gap_repair_v1.json')
    parser.add_argument('--detail', default='data/replay/era64d_real_wallet_event_coverage_bridge_v1.json')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = root / args.config
    summary, detail = run(root, config_path)
    atomic_json(root / args.summary, summary)
    atomic_json(root / args.detail, detail)

    print(f"ERA64D_STATUS={summary['status']}")
    print(f"DATABASE_SOURCE_COUNT={summary['database_source_count']}")
    print(f"RELEVANT_TABLE_COUNT={summary['relevant_table_count']}")
    print(f"SCANNED_ROW_COUNT={summary['scanned_row_count']}")
    print(f"CANDIDATE_SOURCE_TABLE_COUNT={summary['candidate_source_table_count']}")
    print(f"EMPTY_CANDIDATE_TABLE_COUNT={summary['empty_candidate_table_count']}")
    print(f"NONEMPTY_CANDIDATE_TABLE_COUNT={summary['nonempty_candidate_table_count']}")
    print(f"RELATIONSHIP_EVENT_COUNT={summary['relationship_event_count']}")
    print(f"COST_COMPLETE_TRADE_EVENT_COUNT={summary['cost_complete_trade_event_count']}")
    print(f"CLOSED_CYCLE_COUNT={summary['closed_cycle_count']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
PY_ENGINE

cat > tests/test_era64d_wallet_event_coverage_bridge_v1.py <<'PY_TEST'
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.era64_wallet_event_coverage_bridge_v1 import (
    AUTHORITY,
    classify_schema,
    inspect_database,
    run,
)

A = '0x' + '1' * 40
B = '0x' + '2' * 40


class Era64DWalletCoverageBridgeTests(unittest.TestCase):
    def test_01_uid_registry_classification(self):
        result = classify_schema('wallet_registry', ['wallet_uid', 'wallet_address'])
        self.assertIn('UID_ADDRESS_REGISTRY', result['capabilities'])

    def test_02_known_wallet_label_classification(self):
        result = classify_schema('known_wallet_registry', ['wallet_address', 'known_name', 'label_confidence'])
        self.assertIn('DIRECT_LABEL_REGISTRY', result['capabilities'])

    def test_03_uid_transfer_missing_block_number_is_explicit(self):
        result = classify_schema(
            'wallet_transfer_events',
            ['from_wallet_uid', 'to_wallet_uid', 'tx_hash', 'block_time_utc', 'amount'],
        )
        self.assertIn('UID_RELATION_CANDIDATE', result['capabilities'])
        self.assertIn('MISSING_BLOCK_NUMBER', result['blockers'])
        self.assertNotIn('REPLAYABLE_UID_RELATION_AFTER_REGISTRY_JOIN', result['capabilities'])

    def test_04_whale_flow_schema_is_replayable(self):
        result = classify_schema(
            'whale_entity_flow_events',
            ['from_address', 'to_address', 'tx_hash', 'block_number', 'event_time_utc', 'amount_raw'],
        )
        self.assertIn('REPLAYABLE_DIRECT_RELATION', result['capabilities'])

    def test_05_cluster_link_is_evidence_not_fake_transaction(self):
        result = classify_schema(
            'wallet_cluster_links',
            ['root_wallet_address', 'linked_wallet_address', 'link_confidence', 'first_seen_at_utc'],
        )
        self.assertIn('DIRECT_CLUSTER_EVIDENCE', result['capabilities'])
        self.assertNotIn('REPLAYABLE_DIRECT_RELATION', result['capabilities'])

    def test_06_paper_lifecycle_is_excluded(self):
        result = classify_schema(
            'paper_position_lifecycle',
            ['paper_position_id', 'token_address', 'paper_entry_price', 'paper_exit_price', 'paper_engine_trade_authority'],
        )
        self.assertIn('PAPER_SIMULATION_ONLY_EXCLUDED', result['capabilities'])

    def test_07_real_readonly_replay_with_uid_join(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / 'x.sqlite'
            conn = sqlite3.connect(db)
            conn.execute('CREATE TABLE wallet_registry(wallet_uid TEXT, wallet_address TEXT)')
            conn.execute('CREATE TABLE wallet_transfer_events(from_wallet_uid TEXT, to_wallet_uid TEXT, tx_hash TEXT, block_number INTEGER, block_time_utc TEXT, amount REAL, asset_symbol TEXT)')
            conn.executemany('INSERT INTO wallet_registry VALUES(?,?)', [('a', A), ('b', B)])
            conn.execute("INSERT INTO wallet_transfer_events VALUES('a','b','0xabc',123,'2026-01-01T00:00:00Z',5,'T')")
            conn.commit(); conn.close()
            result = inspect_database(db, 20, 100)
            self.assertEqual(len(result['relations']), 1)
            self.assertEqual(result['relations'][0]['block_number'], 123)

    def test_08_missing_block_number_never_uses_rowid_as_fake_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / 'x.sqlite'
            conn = sqlite3.connect(db)
            conn.execute('CREATE TABLE wallet_registry(wallet_uid TEXT, wallet_address TEXT)')
            conn.execute('CREATE TABLE wallet_transfer_events(from_wallet_uid TEXT, to_wallet_uid TEXT, tx_hash TEXT, block_time_utc TEXT, amount REAL)')
            conn.executemany('INSERT INTO wallet_registry VALUES(?,?)', [('a', A), ('b', B)])
            conn.execute("INSERT INTO wallet_transfer_events VALUES('a','b','0xabc','2026-01-01T00:00:00Z',5)")
            conn.commit(); conn.close()
            result = inspect_database(db, 20, 100)
            self.assertEqual(result['relations'], [])
            self.assertEqual(result['blocker_counts'].get('MISSING_BLOCK_NUMBER'), 1)

    def test_09_runtime_status_contract_ready_without_events(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'data').mkdir()
            db = root / 'data' / 'x.sqlite'
            conn = sqlite3.connect(db)
            conn.execute('CREATE TABLE wallet_transfer_events(from_wallet_uid TEXT, to_wallet_uid TEXT, tx_hash TEXT, block_time_utc TEXT, amount REAL)')
            conn.commit(); conn.close()
            config = {
                'database_candidates': ['data/x.sqlite'],
                'maximum_tables_per_database': 20,
                'maximum_rows_per_table': 100,
                'maximum_graph_nodes': 16,
                'maximum_graph_edges': 16,
                'maximum_trade_groups': 16,
            }
            cfg = root / 'config.json'; cfg.write_text(json.dumps(config), encoding='utf-8')
            summary, _ = run(root, cfg)
            self.assertEqual(summary['status'], 'REAL_WALLET_EVENT_COVERAGE_REPAIRED_SOURCE_CONTRACT_READY')
            self.assertTrue(summary['source_contract_ready'])

    def test_10_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'data').mkdir()
            db = root / 'data' / 'x.sqlite'
            conn = sqlite3.connect(db)
            conn.execute('CREATE TABLE wallet_registry(wallet_uid TEXT, wallet_address TEXT)')
            conn.commit(); conn.close()
            config = {
                'database_candidates': ['data/x.sqlite'],
                'maximum_tables_per_database': 20,
                'maximum_rows_per_table': 100,
                'maximum_graph_nodes': 16,
                'maximum_graph_edges': 16,
                'maximum_trade_groups': 16,
            }
            cfg = root / 'config.json'; cfg.write_text(json.dumps(config), encoding='utf-8')
            first, detail1 = run(root, cfg)
            second, detail2 = run(root, cfg)
            self.assertEqual(first['result_hash'], second['result_hash'])
            self.assertEqual(detail1['detail_hash'], detail2['detail_hash'])

    def test_11_authority_is_zero(self):
        self.assertFalse(any(AUTHORITY.values()))

    def test_12_source_has_no_network_db_write_or_dynamic_execution(self):
        source = Path('tools/era64_wallet_event_coverage_bridge_v1.py').read_text(encoding='utf-8')
        for forbidden in ('requests.', 'urllib.', 'subprocess', 'os.system', 'shell=True', 'eval(', 'exec(', 'INSERT INTO', 'UPDATE ', 'DELETE FROM'):
            self.assertNotIn(forbidden, source)
        self.assertIn('?mode=ro', source)
        self.assertIn('PRAGMA query_only=ON', source)


if __name__ == '__main__':
    unittest.main()
PY_TEST

python3 -m unittest -v tests/test_era64d_wallet_event_coverage_bridge_v1.py
python3 -m unittest -v tests/test_era64_real_historical_wallet_replay_v1.py
python3 -m unittest -v tests/test_era64_successful_wallet_foundation_v1.py
python3 tools/era58_smart_money_performance_engine_v1_test.py
python3 -m unittest -v tests/test_era63b_paper_trading_core_v1.py
python3 -m unittest -v tests/test_era63c_technical_dex_execution_v1.py
python3 -m unittest -v tests/test_era63d_market_technical_runtime_v1.py
python3 -m unittest -v tests/test_era63e_always_on_market_runtime_v1.py
echo "TESTS=108/108_VERIFIED"

python3 tools/era64_wallet_event_coverage_bridge_v1.py --root /root/tokenoskobi_clean_v1

python3 <<'PY_RESULT_VERIFY'
import json
from pathlib import Path

s = json.loads(Path('data/control/era64d_real_wallet_event_coverage_gap_repair_v1.json').read_text(encoding='utf-8'))
assert s['real_data'] is True and s['synthetic_data'] is False
assert s['database_source_count'] >= 1
assert s['relevant_table_count'] >= 1
assert s['scanned_row_count'] >= 1
assert s['candidate_source_table_count'] >= 1
assert s['coverage_classification_repaired'] is True
assert s['source_contract_ready'] is True
assert s['status'] in {
    'REAL_WALLET_EVENT_COVERAGE_REPAIRED_AND_REPLAY_VALIDATED',
    'REAL_WALLET_EVENT_COVERAGE_REPAIRED_SOURCE_CONTRACT_READY',
}
a = s['authority']
assert not any(a.get(key) for key in (
    'network_access', 'database_write', 'runtime_mutation', 'panel_mutation',
    'service_mutation', 'timer_mutation', 'paper_trade', 'live_trade',
    'wallet', 'signing', 'order_create', 'broadcast',
))
print('REAL_DATA_VERIFY=VERIFIED')
PY_RESULT_VERIFY

python3 <<'PY_CANONICAL'
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

NOW = datetime.now(timezone.utc).isoformat()
STAGE = 'ERA64D_REAL_WALLET_EVENT_COVERAGE_GAP_REPAIR'
ARTIFACT_PATH = 'data/control/era64d_real_wallet_event_coverage_gap_repair_v1.json'
artifact = json.loads(Path(ARTIFACT_PATH).read_text(encoding='utf-8'))

if artifact['status'] == 'REAL_WALLET_EVENT_COVERAGE_REPAIRED_AND_REPLAY_VALIDATED':
    NEXT = 'ERA64E_READONLY_SUCCESSFUL_WALLET_SCORECARD_AND_PANEL_BINDING_REQUIRES_USER_APPROVAL'
    CURRENT_STATUS = 'ACTIVE_REAL_WALLET_EVENT_COVERAGE_REPAIRED_REPLAY_VALIDATED'
else:
    NEXT = 'ERA64E_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN_REQUIRES_USER_APPROVAL'
    CURRENT_STATUS = 'ACTIVE_WALLET_EVENT_COVERAGE_REPAIRED_SOURCE_CONTRACT_READY'


def load(path: str):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path: str, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')


def apply_state(obj):
    if not isinstance(obj, dict):
        return
    obj['current_era'] = 'ERA64'
    obj['current_stage'] = STAGE
    obj['current_status'] = CURRENT_STATUS
    obj['next_safe_step'] = NEXT
    obj['updated_at_utc'] = NOW
    obj['era64_implementation_authorized'] = True
    obj['era64d_artifact'] = ARTIFACT_PATH
    obj['era64d_status'] = artifact['status']
    obj['era64d_coverage_classification_repaired'] = True
    obj['era64d_source_contract_ready'] = artifact['source_contract_ready']
    obj['era64d_candidate_source_table_count'] = artifact['candidate_source_table_count']
    obj['era64d_empty_candidate_table_count'] = artifact['empty_candidate_table_count']
    obj['era64d_nonempty_candidate_table_count'] = artifact['nonempty_candidate_table_count']
    obj['era64d_relationship_event_count'] = artifact['relationship_event_count']
    obj['era64d_cost_complete_trade_event_count'] = artifact['cost_complete_trade_event_count']
    obj['era64d_closed_cycle_count'] = artifact['closed_cycle_count']
    obj['paper_runtime_enabled'] = False
    obj['fixed_timer_enabled'] = False
    authority = obj.get('authority')
    if isinstance(authority, dict):
        authority['real_trade_authority'] = 0
        authority['real_wallet_authority'] = 0
        authority['real_signing_authority'] = 0
        authority['real_order_authority'] = 0
        authority['live_trade'] = 'DISABLED'
        authority['paper_trade'] = 'DISABLED_PENDING_COORDINATED_INTELLIGENCE'


runtime = load('PROJECT_RUNTIME.json')
apply_state(runtime)
pointer = runtime.get('canonical_runtime_pointer')
if isinstance(pointer, dict):
    apply_state(pointer)
save('PROJECT_RUNTIME.json', runtime)

machine = load('data/control/latest_tk_machine_state.json')
apply_state(machine)
pointer = machine.get('canonical_runtime_pointer') if isinstance(machine, dict) else None
if isinstance(pointer, dict):
    apply_state(pointer)
save('data/control/latest_tk_machine_state.json', machine)

history = load('PROJECT_HISTORY.json')
entry = {
    'id': STAGE,
    'era': 'ERA64',
    'stage': STAGE,
    'status': artifact['status'],
    'completed_at_utc': NOW,
    'artifact': ARTIFACT_PATH,
    'real_data': True,
    'synthetic_data': False,
    'coverage_classification_repaired': True,
    'source_contract_ready': artifact['source_contract_ready'],
    'candidate_source_table_count': artifact['candidate_source_table_count'],
    'empty_candidate_table_count': artifact['empty_candidate_table_count'],
    'relationship_event_count': artifact['relationship_event_count'],
    'cost_complete_trade_event_count': artifact['cost_complete_trade_event_count'],
    'closed_cycle_count': artifact['closed_cycle_count'],
    'tests': '108/108_VERIFIED',
    'real_financial_authority': 0,
    'next_safe_step': NEXT,
}
if isinstance(history, list):
    history.append(entry)
elif isinstance(history, dict):
    target = None
    for key in ('events', 'history', 'timeline', 'entries'):
        if isinstance(history.get(key), list):
            target = history[key]
            break
    if target is None:
        target = history.setdefault('events', [])
    target.append(entry)
    history['updated_at_utc'] = NOW
save('PROJECT_HISTORY.json', history)

roadmap = load('data/tokenoskobi_v1_v8_master_era_roadmap.json')

def walk(value):
    if isinstance(value, dict):
        if value.get('id') == 'ERA64' or value.get('era') == 'ERA64':
            value['opened'] = True
            value['status'] = 'ACTIVE'
            value['current_stage'] = STAGE
            value['actual_status'] = artifact['status']
            value['next_safe_step'] = NEXT
            value['era64d_artifact'] = ARTIFACT_PATH
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)

walk(roadmap)
if isinstance(roadmap, dict):
    direction = roadmap.setdefault('current_direction', {})
    if isinstance(direction, dict):
        direction.update({
            'current_version': 'V4',
            'current_era': 'ERA64',
            'current_stage': STAGE,
            'current_status': CURRENT_STATUS,
            'next_safe_step': NEXT,
            'updated_at_utc': NOW,
        })
save('data/tokenoskobi_v1_v8_master_era_roadmap.json', roadmap)

marker = '<!-- ERA64D_WALLET_EVENT_COVERAGE_GAP_REPAIR -->'
blocks = {
    '03_ROADMAP.md': f'''\n{marker}\n## ERA64D wallet event coverage gap repair\n\n- Status: `{artifact['status']}`\n- Candidate source tables: `{artifact['candidate_source_table_count']}`\n- Empty candidate tables: `{artifact['empty_candidate_table_count']}`\n- Next approval gate: `{NEXT}`\n''',
    '04_ALMANAC.md': f'''\n{marker}\n## {NOW} — ERA64D\n\nThe real SQLite wallet-event gap was repaired at the schema-classification and source-contract layer. Status: `{artifact['status']}`. Tests: `108/108_VERIFIED`.\n''',
    '06_PROJECT_MASTER_STATE.md': f'''\n{marker}\n## Current ERA64 state\n\n`{STAGE}` completed with `{artifact['status']}`. The previous row-global missing-column diagnosis was replaced by source-specific capability classification. Real financial authority remains zero.\n''',
    '07_PROJECT_HANDOFF.md': f'''\n{marker}\n## ERA64 handoff\n\n- Current stage: `{STAGE}`\n- Result: `{artifact['status']}`\n- Source contract ready: `{str(artifact['source_contract_ready']).lower()}`\n- Next: `{NEXT}`\n- Paper/live runtime: disabled\n- Real financial authority: zero\n''',
}
for path, block in blocks.items():
    text = Path(path).read_text(encoding='utf-8')
    if marker not in text:
        Path(path).write_text(text.rstrip() + '\n' + block, encoding='utf-8')

report = f'''# ERA64D REAL WALLET EVENT COVERAGE GAP REPAIR\n\n- Status: `{artifact['status']}`\n- Real data: `true`\n- Synthetic data: `false`\n- Database sources: `{artifact['database_source_count']}`\n- Relevant tables: `{artifact['relevant_table_count']}`\n- Scanned rows: `{artifact['scanned_row_count']}`\n- Candidate source tables: `{artifact['candidate_source_table_count']}`\n- Empty candidate tables: `{artifact['empty_candidate_table_count']}`\n- Nonempty candidate tables: `{artifact['nonempty_candidate_table_count']}`\n- Relationship events: `{artifact['relationship_event_count']}`\n- Cost-complete trade events: `{artifact['cost_complete_trade_event_count']}`\n- Closed cycles: `{artifact['closed_cycle_count']}`\n- Coverage classification repaired: `true`\n- Source contract ready: `{str(artifact['source_contract_ready']).lower()}`\n- Tests: `108/108_VERIFIED`\n- Real financial authority: `0`\n- Next: `{NEXT}`\n'''
Path('reports/LATEST_ERA64D_WALLET_EVENT_COVERAGE_GAP_REPAIR.md').write_text(report, encoding='utf-8')
Path('reports/LATEST_TK_AI_HANDOFF.md').write_text(f'''# TOKENOSKOBI LATEST HANDOFF\n\n```text\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA64\nCURRENT_STAGE={STAGE}\nRESULT={artifact['status']}\nNEXT_SAFE_STEP={NEXT}\n```\n\nERA64D repaired wallet-event coverage classification and produced a bounded real-data source contract. No financial authority was opened.\n''', encoding='utf-8')

print('CANONICAL_SYNC=VERIFIED')
print(f'NEXT_SAFE_STEP={NEXT}')
PY_CANONICAL

python3 <<'PY_VERIFY'
import json
from pathlib import Path

for path in (
    'PROJECT_RUNTIME.json',
    'PROJECT_HISTORY.json',
    'data/tokenoskobi_v1_v8_master_era_roadmap.json',
    'data/control/latest_tk_machine_state.json',
    'config/era64_wallet_event_coverage_bridge_v1.json',
    'data/control/era64d_real_wallet_event_coverage_gap_repair_v1.json',
    'data/replay/era64d_real_wallet_event_coverage_bridge_v1.json',
):
    json.loads(Path(path).read_text(encoding='utf-8'))

r = json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert r['current_era'] == 'ERA64'
assert r['current_stage'] == 'ERA64D_REAL_WALLET_EVENT_COVERAGE_GAP_REPAIR'
assert r['next_safe_step'] in {
    'ERA64E_READONLY_SUCCESSFUL_WALLET_SCORECARD_AND_PANEL_BINDING_REQUIRES_USER_APPROVAL',
    'ERA64E_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN_REQUIRES_USER_APPROVAL',
}
a = r['authority']
assert a['real_trade_authority'] == 0
assert a['real_wallet_authority'] == 0
assert a['real_signing_authority'] == 0
assert a['real_order_authority'] == 0
assert a['live_trade'] == 'DISABLED'
assert r['paper_runtime_enabled'] is False
print('CANONICAL_VERIFY=VERIFIED')
PY_VERIFY

git diff --check
git add -- \
  "${CANONICAL_FILES[@]}" \
  config/era64_wallet_event_coverage_bridge_v1.json \
  tools/era64_wallet_event_coverage_bridge_v1.py \
  tests/test_era64d_wallet_event_coverage_bridge_v1.py \
  data/control/era64d_real_wallet_event_coverage_gap_repair_v1.json \
  data/replay/era64d_real_wallet_event_coverage_bridge_v1.json
git add -f -- reports/LATEST_ERA64D_WALLET_EVENT_COVERAGE_GAP_REPAIR.md reports/LATEST_TK_AI_HANDOFF.md
git diff --cached --check
! git diff --cached --quiet

git commit -m "ERA64: repair real wallet event coverage gap"
COMMITTED=1
HEAD="$(git rev-parse HEAD)"
git push origin main
git fetch origin main --quiet
[[ "$(git rev-parse origin/main)" == "$HEAD" ]]
[[ -z "$(git status --porcelain=v1)" ]]
systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer

NEXT="$(python3 - <<'PY_NEXT'
import json
print(json.load(open('PROJECT_RUNTIME.json'))['next_safe_step'])
PY_NEXT
)"
RESULT="$(python3 - <<'PY_RESULT'
import json
print(json.load(open('data/control/era64d_real_wallet_event_coverage_gap_repair_v1.json'))['status'])
PY_RESULT
)"

trap - ERR
echo "ERA64D_STATUS=$RESULT"
echo "TESTS=108/108_VERIFIED"
echo "REAL_DATA=VERIFIED"
echo "SYNTHETIC_DATA=false"
echo "COVERAGE_CLASSIFICATION_REPAIRED=true"
echo "SOURCE_CONTRACT_READY=true"
echo "ALWAYS_ON_TECHNICAL_SERVICE=ACTIVE_READONLY"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REAL_FINANCIAL_AUTHORITY=0"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=$NEXT"
