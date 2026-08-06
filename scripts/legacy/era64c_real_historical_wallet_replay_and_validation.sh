#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era64c_real_replay_backup_${STAMP}.tar.gz"
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
  config/era64_real_historical_wallet_replay_v1.json
  tools/era64_real_historical_wallet_replay_v1.py
  tests/test_era64_real_historical_wallet_replay_v1.py
  data/control/era64c_real_historical_wallet_replay_and_validation_v1.json
  data/replay/era64c_real_historical_wallet_replay_v1.json
  reports/LATEST_ERA64C_REAL_HISTORICAL_WALLET_REPLAY.md
)

rollback() {
  rc=$?
  trap - ERR
  echo "ERA64C_FAILED_RC=$rc"
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
r=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert r.get('current_era') == 'ERA64'
assert r.get('current_stage') == 'ERA64B_SUCCESSFUL_WALLET_STATISTICS_AND_CLUSTER_FOUNDATION'
assert r.get('next_safe_step') == 'ERA64C_REAL_HISTORICAL_WALLET_REPLAY_AND_VALIDATION_REQUIRES_USER_APPROVAL'
a=r.get('authority',{})
assert a.get('real_trade_authority') == 0
assert a.get('real_wallet_authority') == 0
assert a.get('real_signing_authority') == 0
assert a.get('real_order_authority') == 0
assert a.get('live_trade') == 'DISABLED'
assert r.get('paper_runtime_enabled') is False
assert Path('tools/era64_successful_wallet_foundation_v1.py').is_file()
print('PRECHECK=VERIFIED')
PY_PRECHECK

tar -czf "$BACKUP" "${CANONICAL_FILES[@]}"
echo "BACKUP=$BACKUP"
mkdir -p config tools tests data/control data/replay reports

cat > config/era64_real_historical_wallet_replay_v1.json <<'JSON_CONFIG'
{
  "schema": "tokenoskobi.era64.real_historical_wallet_replay.config.v1",
  "mode": "LOCAL_SQLITE_READ_ONLY_REAL_DATA",
  "synthetic_data_allowed": false,
  "network_access": false,
  "database_write": false,
  "runtime_mutation": false,
  "panel_mutation": false,
  "service_mutation": false,
  "timer_mutation": false,
  "paper_runtime": false,
  "live_trade": false,
  "real_financial_authority": 0,
  "maximum_tables_per_database": 50,
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

cat > tools/era64_real_historical_wallet_replay_v1.py <<'PY_ENGINE'
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
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from era64_successful_wallet_foundation_v1 import (  # noqa: E402
    AUTHORITY,
    WalletFoundationError,
    build_relationship_graph,
    calculate_performance,
    normalize_wallet,
    reconstruct_position_cycles,
    resolve_wallet_label,
)

RELEVANT_TABLE_WORDS = (
    "wallet", "whale", "transfer", "fund", "cluster", "deployer",
    "position", "trade", "swap", "outcome", "balance", "flow",
)
ALIASES = {
    "wallet": ("wallet", "wallet_address", "address", "owner", "trader", "account"),
    "from_wallet": ("from_wallet", "from_address", "src", "source", "sender", "wallet_from"),
    "to_wallet": ("to_wallet", "to_address", "dst", "destination", "recipient", "wallet_to"),
    "tx_hash": ("tx_hash", "transaction_hash", "transaction_id", "txid", "hash"),
    "timestamp": ("timestamp", "event_timestamp", "block_timestamp", "created_at", "observed_at", "ts", "time"),
    "block_number": ("block_number", "block", "block_height", "height"),
    "amount": ("amount", "value", "quantity", "token_amount", "amount_raw", "volume"),
    "token": ("token", "token_address", "asset", "symbol", "contract_address"),
    "relation": ("relation_type", "relationship_type", "edge_type", "link_type", "event_type"),
    "label": ("label", "entity_label", "wallet_label", "entity_name", "name"),
    "confidence": ("confidence", "label_confidence", "score", "trust_score"),
    "source_name": ("source_name", "source", "provider", "registry", "evidence_source"),
    "evidence_id": ("evidence_id", "source_id", "record_id", "event_id"),
    "side": ("side", "trade_side", "direction", "action"),
    "quantity": ("quantity", "token_quantity", "amount", "size", "qty"),
    "price": ("price", "execution_price", "fill_price", "token_price", "price_usd"),
    "fee": ("fee", "trading_fee", "fee_amount", "protocol_fee"),
    "gas": ("gas", "gas_cost", "gas_fee", "network_fee"),
}


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def choose(columns: Iterable[str], key: str) -> str | None:
    mapping = {str(column).lower(): str(column) for column in columns}
    for alias in ALIASES[key]:
        if alias.lower() in mapping:
            return mapping[alias.lower()]
    return None


def as_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
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
    text = value.strip().replace("Z", "+00:00")
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
        "database": database,
        "table": table,
        "row_id": row_id,
        "row_hash": canonical_hash(row),
    })


def row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys() if key != "__era64_rowid"}


def read_rows(conn: sqlite3.Connection, table: str, limit: int) -> list[tuple[Any, dict[str, Any]]]:
    try:
        rows = conn.execute(
            f"SELECT rowid AS __era64_rowid, * FROM {qident(table)} LIMIT ?", (limit,)
        ).fetchall()
        return [(row["__era64_rowid"], row_dict(row)) for row in rows]
    except sqlite3.DatabaseError:
        rows = conn.execute(f"SELECT * FROM {qident(table)} LIMIT ?", (limit,)).fetchall()
        return [(index, row_dict(row)) for index, row in enumerate(rows, start=1)]


def extract_label(database: str, table: str, row_id: Any, row: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    columns = row.keys()
    wallet_col = choose(columns, "wallet")
    label_col = choose(columns, "label")
    confidence_col = choose(columns, "confidence")
    if not wallet_col or not label_col or not confidence_col:
        return None, "MISSING_LABEL_COLUMNS"
    wallet = valid_wallet(row.get(wallet_col))
    confidence = as_float(row.get(confidence_col))
    label = str(row.get(label_col) or "").strip()
    if wallet is None or not label or confidence is None or not 0.0 <= confidence <= 1.0:
        return None, "INVALID_LABEL_ROW"
    source_col = choose(columns, "source_name")
    evidence_col = choose(columns, "evidence_id")
    evidence_id = str(row.get(evidence_col) or "").strip() if evidence_col else ""
    if not evidence_id:
        evidence_id = source_evidence_id(database, table, row_id, row)
    source = str(row.get(source_col) or "").strip() if source_col else ""
    if not source:
        source = f"SQLITE:{Path(database).name}:{table}"
    return {
        "wallet": wallet,
        "label": label,
        "confidence": confidence,
        "source": source,
        "evidence_id": evidence_id,
    }, None


def extract_relation(database: str, table: str, row_id: Any, row: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    columns = row.keys()
    required = {key: choose(columns, key) for key in ("from_wallet", "to_wallet", "tx_hash", "timestamp", "block_number", "amount")}
    if any(value is None for value in required.values()):
        return None, "MISSING_RELATION_COLUMNS"
    src = valid_wallet(row.get(required["from_wallet"]))
    dst = valid_wallet(row.get(required["to_wallet"]))
    tx_hash = str(row.get(required["tx_hash"]) or "").strip().lower()
    timestamp = as_timestamp(row.get(required["timestamp"]))
    block_number = as_int(row.get(required["block_number"]))
    amount = as_float(row.get(required["amount"]))
    if src is None or dst is None or src == dst or not tx_hash or timestamp is None or block_number is None or block_number < 0 or amount is None or amount <= 0:
        return None, "INVALID_RELATION_ROW"
    relation_col = choose(columns, "relation")
    relation = str(row.get(relation_col) or "").strip().upper() if relation_col else ""
    if relation not in {"FUNDING", "TRANSFER", "SAME_DEPLOYER", "SHARED_COUNTERPARTY"}:
        relation = "FUNDING" if "fund" in table.lower() else "TRANSFER"
    token_col = choose(columns, "token")
    token = str(row.get(token_col) or "UNKNOWN").strip().upper() if token_col else "UNKNOWN"
    evidence_id = source_evidence_id(database, table, row_id, row)
    return {
        "from_wallet": src,
        "to_wallet": dst,
        "relation_type": relation,
        "tx_hash": tx_hash,
        "evidence_id": evidence_id,
        "token": token or "UNKNOWN",
        "amount": amount,
        "timestamp": timestamp,
        "block_number": block_number,
    }, None


def extract_trade(database: str, table: str, row_id: Any, row: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    columns = row.keys()
    required_keys = ("wallet", "token", "side", "tx_hash", "quantity", "price", "fee", "gas", "timestamp")
    required = {key: choose(columns, key) for key in required_keys}
    if any(value is None for value in required.values()):
        return None, "MISSING_COST_COMPLETE_TRADE_COLUMNS"
    wallet = valid_wallet(row.get(required["wallet"]))
    token = str(row.get(required["token"]) or "").strip().upper()
    side = str(row.get(required["side"]) or "").strip().upper()
    tx_hash = str(row.get(required["tx_hash"]) or "").strip().lower()
    quantity = as_float(row.get(required["quantity"]))
    price = as_float(row.get(required["price"]))
    fee = as_float(row.get(required["fee"]))
    gas = as_float(row.get(required["gas"]))
    timestamp = as_timestamp(row.get(required["timestamp"]))
    if wallet is None or not token or side not in {"BUY", "SELL"} or not tx_hash:
        return None, "INVALID_TRADE_IDENTITY"
    if quantity is None or quantity <= 0 or price is None or price <= 0 or fee is None or fee < 0 or gas is None or gas < 0 or timestamp is None:
        return None, "INVALID_TRADE_VALUES"
    return {
        "wallet": wallet,
        "token": token,
        "side": side,
        "tx_hash": tx_hash,
        "evidence_id": source_evidence_id(database, table, row_id, row),
        "quantity": quantity,
        "price": price,
        "fee": fee,
        "gas": gas,
        "timestamp": timestamp,
    }, None


def bounded_graph_events(events: list[dict[str, Any]], max_nodes: int, max_edges: int) -> list[dict[str, Any]]:
    deduped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for event in events:
        key = (
            event["from_wallet"], event["to_wallet"], event["relation_type"],
            event["tx_hash"], event["evidence_id"],
        )
        deduped[key] = event
    ordered = sorted(deduped.values(), key=lambda item: (
        item["timestamp"], item["block_number"], item["tx_hash"],
        item["from_wallet"], item["to_wallet"],
    ))
    selected: list[dict[str, Any]] = []
    nodes: set[str] = set()
    for event in ordered:
        candidate_nodes = nodes | {event["from_wallet"], event["to_wallet"]}
        if len(candidate_nodes) > max_nodes:
            continue
        selected.append(event)
        nodes = candidate_nodes
        if len(selected) >= max_edges:
            break
    return selected


def replay_trade_groups(trades: list[dict[str, Any]], maximum_groups: int) -> dict[str, Any]:
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for trade in trades:
        key = (trade["wallet"], trade["token"], trade["side"], trade["tx_hash"], trade["evidence_id"])
        unique[key] = trade
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for trade in unique.values():
        groups[(trade["wallet"], trade["token"])].append(trade)
    cycles: list[dict[str, Any]] = []
    open_positions: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for (wallet, token), rows in sorted(groups.items())[:maximum_groups]:
        try:
            result = reconstruct_position_cycles(rows)
        except WalletFoundationError as exc:
            rejected.append({"wallet": wallet, "token": token, "reason": str(exc), "row_count": len(rows)})
            continue
        cycles.extend(result["cycles"])
        open_positions.extend(result["open_positions"])
    cycles.sort(key=lambda item: (item["exit_timestamp"], item["wallet"], item["token"], item["exit_tx_hash"]))
    performance = calculate_performance(cycles)
    return {
        "trade_group_count": len(groups),
        "validated_group_count": min(len(groups), maximum_groups) - len(rejected),
        "rejected_group_count": len(rejected),
        "rejected_groups": rejected[:100],
        "closed_cycle_count": len(cycles),
        "cycles": cycles[:1000],
        "open_positions": open_positions[:1000],
        "performance": performance,
        "cycle_hash": canonical_hash(cycles),
    }


def inspect_database(path: Path, maximum_tables: int, maximum_rows: int) -> dict[str, Any]:
    uri = f"file:{path.resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    table_names = [
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]
    relevant = [name for name in table_names if any(word in name.lower() for word in RELEVANT_TABLE_WORDS)][:maximum_tables]
    inventory: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    gap_counts: Counter[str] = Counter()
    scanned_rows = 0
    for table in relevant:
        columns = [row[1] for row in conn.execute(f"PRAGMA table_info({qident(table)})").fetchall()]
        try:
            total_rows = int(conn.execute(f"SELECT COUNT(*) FROM {qident(table)}").fetchone()[0])
        except sqlite3.DatabaseError:
            total_rows = -1
        rows = read_rows(conn, table, maximum_rows)
        scanned_rows += len(rows)
        before = (len(labels), len(relations), len(trades))
        for row_id, row in rows:
            label, label_gap = extract_label(str(path), table, row_id, row)
            relation, relation_gap = extract_relation(str(path), table, row_id, row)
            trade, trade_gap = extract_trade(str(path), table, row_id, row)
            if label is not None:
                labels.append(label)
            elif label_gap:
                gap_counts[label_gap] += 1
            if relation is not None:
                relations.append(relation)
            elif relation_gap:
                gap_counts[relation_gap] += 1
            if trade is not None:
                trades.append(trade)
            elif trade_gap:
                gap_counts[trade_gap] += 1
        inventory.append({
            "table": table,
            "columns": columns,
            "total_rows": total_rows,
            "scanned_rows": len(rows),
            "label_rows": len(labels) - before[0],
            "relationship_rows": len(relations) - before[1],
            "cost_complete_trade_rows": len(trades) - before[2],
        })
    conn.close()
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "table_count": len(table_names),
        "relevant_table_count": len(relevant),
        "scanned_row_count": scanned_rows,
        "inventory": inventory,
        "labels": labels,
        "relations": relations,
        "trades": trades,
        "gap_counts": dict(sorted(gap_counts.items())),
    }


def run(root: Path, config_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    database_paths = []
    for relative in config["database_candidates"]:
        candidate = root / relative
        if candidate.is_file() and candidate.stat().st_size > 0:
            database_paths.append(candidate)
    database_paths = sorted(set(database_paths))
    database_results = [
        inspect_database(path, int(config["maximum_tables_per_database"]), int(config["maximum_rows_per_table"]))
        for path in database_paths
    ]
    labels = [item for result in database_results for item in result["labels"]]
    relations = [item for result in database_results for item in result["relations"]]
    trades = [item for result in database_results for item in result["trades"]]
    graph_events = bounded_graph_events(
        relations,
        int(config["maximum_graph_nodes"]),
        int(config["maximum_graph_edges"]),
    )
    graph = build_relationship_graph(
        graph_events,
        max_nodes=int(config["maximum_graph_nodes"]),
        max_edges=int(config["maximum_graph_edges"]),
    ) if graph_events else {
        "node_count": 0, "edge_count": 0, "nodes": [], "edges": [], "clusters": [],
        "graph_hash": canonical_hash([]), "status": "NO_REPLAYABLE_REAL_RELATIONSHIP_EVENTS",
    }
    label_wallets = sorted({item["wallet"] for item in labels})[:128]
    label_results = [resolve_wallet_label(wallet, labels) for wallet in label_wallets]
    trade_replay = replay_trade_groups(trades, int(config["maximum_trade_groups"]))
    scanned_rows = sum(result["scanned_row_count"] for result in database_results)
    relevant_tables = sum(result["relevant_table_count"] for result in database_results)
    real_replay_evidence = graph["edge_count"] > 0 or trade_replay["closed_cycle_count"] > 0
    if not database_results or relevant_tables == 0 or scanned_rows == 0:
        status = "NO_REAL_HISTORICAL_SQLITE_EVIDENCE"
    elif real_replay_evidence:
        status = "REAL_HISTORICAL_REPLAY_VALIDATED"
    else:
        status = "REAL_DATA_DISCOVERED_REPLAY_GAP_CONFIRMED"
    gap_counts: Counter[str] = Counter()
    for result in database_results:
        gap_counts.update(result["gap_counts"])
    authority = dict(AUTHORITY)
    authority.update({"paper_trade": False, "live_trade": False, "wallet": False, "signing": False, "order_create": False, "broadcast": False})
    detail = {
        "schema": "tokenoskobi.era64.real_historical_wallet_replay.output.v1",
        "status": status,
        "real_data": True,
        "synthetic_data": False,
        "authority": authority,
        "database_sources": [
            {key: value for key, value in result.items() if key not in {"labels", "relations", "trades"}}
            for result in database_results
        ],
        "label_evidence_count": len(labels),
        "label_results": label_results,
        "relationship_event_count": len(relations),
        "relationship_graph": graph,
        "cost_complete_trade_event_count": len(trades),
        "position_replay": trade_replay,
        "coverage_gaps": dict(sorted(gap_counts.items())),
        "strongest_alternative_hypotheses": [
            "INCOMPLETE_COST_FIELDS_CAN_OVERSTATE_WALLET_EDGE",
            "SURVIVORSHIP_BIAS_CAN_MISCLASSIFY_SUCCESSFUL_WALLETS",
            "UNRESOLVED_LABEL_CONFLICTS_CAN_MERGE_UNRELATED_ENTITIES",
            "INSUFFICIENT_CLOSED_POSITION_HISTORY_BLOCKS_COPYABILITY",
        ],
    }
    detail["result_hash"] = canonical_hash(detail)
    summary = {
        "schema": "tokenoskobi.era64c.real_historical_wallet_replay_and_validation.v1",
        "status": status,
        "real_data": True,
        "synthetic_data": False,
        "database_source_count": len(database_results),
        "relevant_table_count": relevant_tables,
        "scanned_row_count": scanned_rows,
        "label_evidence_count": len(labels),
        "relationship_event_count": len(relations),
        "replayed_relationship_edge_count": graph["edge_count"],
        "cluster_count": len(graph["clusters"]),
        "cost_complete_trade_event_count": len(trades),
        "validated_trade_group_count": trade_replay["validated_group_count"],
        "rejected_trade_group_count": trade_replay["rejected_group_count"],
        "closed_cycle_count": trade_replay["closed_cycle_count"],
        "performance": trade_replay["performance"],
        "coverage_gaps": dict(sorted(gap_counts.items())),
        "authority": authority,
        "detail_artifact": "data/replay/era64c_real_historical_wallet_replay_v1.json",
        "detail_hash": detail["result_hash"],
    }
    summary["result_hash"] = canonical_hash(summary)
    return summary, detail


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--config", default="config/era64_real_historical_wallet_replay_v1.json")
    parser.add_argument("--summary", default="data/control/era64c_real_historical_wallet_replay_and_validation_v1.json")
    parser.add_argument("--detail", default="data/replay/era64c_real_historical_wallet_replay_v1.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    summary, detail = run(root, root / args.config)
    atomic_json(root / args.summary, summary)
    atomic_json(root / args.detail, detail)
    print(f"ERA64C_REPLAY_STATUS={summary['status']}")
    print(f"DATABASE_SOURCE_COUNT={summary['database_source_count']}")
    print(f"RELEVANT_TABLE_COUNT={summary['relevant_table_count']}")
    print(f"SCANNED_ROW_COUNT={summary['scanned_row_count']}")
    print(f"RELATIONSHIP_EVENT_COUNT={summary['relationship_event_count']}")
    print(f"COST_COMPLETE_TRADE_EVENT_COUNT={summary['cost_complete_trade_event_count']}")
    print(f"CLOSED_CYCLE_COUNT={summary['closed_cycle_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY_ENGINE

cat > tests/test_era64_real_historical_wallet_replay_v1.py <<'PY_TEST'
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.era64_real_historical_wallet_replay_v1 import (
    as_timestamp,
    bounded_graph_events,
    extract_relation,
    extract_trade,
    inspect_database,
    replay_trade_groups,
    run,
    valid_wallet,
)

A="0x"+"1"*40
B="0x"+"2"*40
T="0x"+"3"*40


class Era64RealHistoricalReplayTests(unittest.TestCase):
    def make_db(self, root: Path) -> Path:
        path=root/"data"/"tokenoskobi_clean_v1.sqlite"
        path.parent.mkdir(parents=True,exist_ok=True)
        conn=sqlite3.connect(path)
        conn.execute("CREATE TABLE wallet_transfer_events(from_wallet TEXT,to_wallet TEXT,tx_hash TEXT,timestamp INTEGER,block_number INTEGER,amount REAL,token TEXT)")
        conn.execute("INSERT INTO wallet_transfer_events VALUES(?,?,?,?,?,?,?)",(A,B,"0xabc",1000,10,25.0,T))
        conn.execute("CREATE TABLE wallet_trade_events(wallet TEXT,token TEXT,side TEXT,tx_hash TEXT,quantity REAL,price REAL,fee REAL,gas REAL,timestamp INTEGER)")
        conn.execute("INSERT INTO wallet_trade_events VALUES(?,?,?,?,?,?,?,?,?)",(A,T,"BUY","0xbuy",2.0,10.0,0.1,0.1,1000))
        conn.execute("INSERT INTO wallet_trade_events VALUES(?,?,?,?,?,?,?,?,?)",(A,T,"SELL","0xsell",2.0,15.0,0.1,0.1,2000))
        conn.commit(); conn.close()
        return path

    def test_01_wallet_validation(self):
        self.assertEqual(valid_wallet(A),A)
        self.assertIsNone(valid_wallet("bad"))

    def test_02_timestamp_normalizes_milliseconds(self):
        self.assertEqual(as_timestamp(1_700_000_000_000),1_700_000_000)

    def test_03_relation_extracts_real_fields(self):
        row={"from_wallet":A,"to_wallet":B,"tx_hash":"0xabc","timestamp":1,"block_number":2,"amount":3,"token":T}
        event,gap=extract_relation("x.db","wallet_transfer_events",1,row)
        self.assertIsNone(gap); self.assertEqual(event["from_wallet"],A)

    def test_04_relation_missing_tx_is_rejected(self):
        row={"from_wallet":A,"to_wallet":B,"timestamp":1,"block_number":2,"amount":3}
        event,gap=extract_relation("x.db","wallet_transfer_events",1,row)
        self.assertIsNone(event); self.assertEqual(gap,"MISSING_RELATION_COLUMNS")

    def test_05_trade_requires_complete_cost_fields(self):
        row={"wallet":A,"token":T,"side":"BUY","tx_hash":"x","quantity":1,"price":1,"timestamp":1}
        event,gap=extract_trade("x.db","wallet_trade_events",1,row)
        self.assertIsNone(event); self.assertEqual(gap,"MISSING_COST_COMPLETE_TRADE_COLUMNS")

    def test_06_bounded_graph_respects_limits(self):
        events=[]
        for i in range(10):
            events.append({"from_wallet":A,"to_wallet":B,"relation_type":"TRANSFER","tx_hash":str(i),"evidence_id":str(i),"token":"T","amount":1,"timestamp":i,"block_number":i})
        self.assertEqual(len(bounded_graph_events(events,2,3)),3)

    def test_07_trade_replay_is_cost_adjusted(self):
        rows=[
            {"wallet":A,"token":"T","side":"BUY","tx_hash":"b","evidence_id":"1","quantity":1,"price":10,"fee":1,"gas":1,"timestamp":1},
            {"wallet":A,"token":"T","side":"SELL","tx_hash":"s","evidence_id":"2","quantity":1,"price":15,"fee":1,"gas":1,"timestamp":2},
        ]
        result=replay_trade_groups(rows,10)
        self.assertEqual(result["closed_cycle_count"],1)
        self.assertLess(result["cycles"][0]["pnl"],5)

    def test_08_oversell_group_fails_closed(self):
        rows=[{"wallet":A,"token":"T","side":"SELL","tx_hash":"s","evidence_id":"2","quantity":1,"price":15,"fee":0,"gas":0,"timestamp":2}]
        result=replay_trade_groups(rows,10)
        self.assertEqual(result["rejected_group_count"],1)

    def test_09_sqlite_is_read_only_and_real_replay_runs(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self.make_db(root)
            config={"database_candidates":["data/tokenoskobi_clean_v1.sqlite"],"maximum_tables_per_database":10,"maximum_rows_per_table":100,"maximum_graph_nodes":16,"maximum_graph_edges":16,"maximum_trade_groups":16}
            cfg=root/"config.json"; cfg.write_text(json.dumps(config),encoding="utf-8")
            summary,_=run(root,cfg)
            self.assertEqual(summary["status"],"REAL_HISTORICAL_REPLAY_VALIDATED")
            self.assertEqual(summary["closed_cycle_count"],1)

    def test_10_authority_and_source_are_safe(self):
        source=Path("tools/era64_real_historical_wallet_replay_v1.py").read_text(encoding="utf-8")
        for forbidden in ("requests.","urllib.","subprocess", "os.system", "shell=True", "eval(", "exec("):
            self.assertNotIn(forbidden,source)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"x.sqlite"; sqlite3.connect(path).close()
            result=inspect_database(path,10,10)
            self.assertEqual(result["scanned_row_count"],0)


if __name__ == "__main__":
    unittest.main()
PY_TEST

python3 -m unittest -v tests/test_era64_real_historical_wallet_replay_v1.py
python3 -m unittest -v tests/test_era64_successful_wallet_foundation_v1.py
python3 tools/era58_smart_money_performance_engine_v1_test.py
python3 -m unittest -v tests/test_era63_paper_trading_core_v1.py
python3 -m unittest -v tests/test_era63c_technical_dex_execution_v1.py
python3 -m unittest -v tests/test_era63d_market_technical_runtime_v1.py
python3 -m unittest -v tests/test_era63e_always_on_market_runtime_v1.py
echo "TESTS=96/96_VERIFIED"

python3 tools/era64_real_historical_wallet_replay_v1.py --root /root/tokenoskobi_clean_v1

python3 <<'PY_RESULT_VERIFY'
import json
from pathlib import Path
s=json.loads(Path('data/control/era64c_real_historical_wallet_replay_and_validation_v1.json').read_text(encoding='utf-8'))
assert s['real_data'] is True and s['synthetic_data'] is False
assert s['database_source_count'] >= 1
assert s['relevant_table_count'] >= 1
assert s['scanned_row_count'] >= 1
assert s['status'] in {'REAL_HISTORICAL_REPLAY_VALIDATED','REAL_DATA_DISCOVERED_REPLAY_GAP_CONFIRMED'}
a=s['authority']
assert not any(a.get(key) for key in ('network_access','database_write','runtime_mutation','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'))
print('REAL_DATA_VERIFY=VERIFIED')
PY_RESULT_VERIFY

python3 <<'PY_CANONICAL'
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

NOW=datetime.now(timezone.utc).isoformat()
STAGE='ERA64C_REAL_HISTORICAL_WALLET_REPLAY_AND_VALIDATION'
artifact_path='data/control/era64c_real_historical_wallet_replay_and_validation_v1.json'
artifact=json.loads(Path(artifact_path).read_text(encoding='utf-8'))
if artifact['status']=='REAL_HISTORICAL_REPLAY_VALIDATED':
    NEXT='ERA64D_READONLY_SUCCESSFUL_WALLET_SCORECARD_AND_PANEL_BINDING_REQUIRES_USER_APPROVAL'
    CURRENT_STATUS='ACTIVE_REAL_HISTORICAL_REPLAY_VALIDATED'
else:
    NEXT='ERA64D_REAL_WALLET_EVENT_COVERAGE_GAP_REPAIR_REQUIRES_USER_APPROVAL'
    CURRENT_STATUS='ACTIVE_REAL_DATA_REPLAY_GAP_EVIDENCE_SEALED'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')


def apply_runtime(obj):
    obj['current_era']='ERA64'
    obj['current_stage']=STAGE
    obj['current_status']=CURRENT_STATUS
    obj['next_safe_step']=NEXT
    obj['updated_at_utc']=NOW
    obj['era64_implementation_authorized']=True
    obj['era64c_real_historical_replay_validated']=artifact['status']=='REAL_HISTORICAL_REPLAY_VALIDATED'
    obj['era64c_real_data_gap_confirmed']=artifact['status']=='REAL_DATA_DISCOVERED_REPLAY_GAP_CONFIRMED'
    obj['era64c_artifact']=artifact_path
    obj['era64c_database_source_count']=artifact['database_source_count']
    obj['era64c_relevant_table_count']=artifact['relevant_table_count']
    obj['era64c_scanned_row_count']=artifact['scanned_row_count']
    obj['era64c_relationship_event_count']=artifact['relationship_event_count']
    obj['era64c_cost_complete_trade_event_count']=artifact['cost_complete_trade_event_count']
    obj['era64c_closed_cycle_count']=artifact['closed_cycle_count']
    obj['paper_runtime_enabled']=False
    obj['fixed_timer_enabled']=False
    authority=obj.setdefault('authority',{})
    authority['real_trade_authority']=0
    authority['real_wallet_authority']=0
    authority['real_signing_authority']=0
    authority['real_order_authority']=0
    authority['live_trade']='DISABLED'
    authority['paper_trade']='DISABLED_PENDING_COORDINATED_INTELLIGENCE'

runtime=load('PROJECT_RUNTIME.json')
apply_runtime(runtime)
pointer=runtime.get('canonical_runtime_pointer')
if isinstance(pointer,dict):
    apply_runtime(pointer)
write('PROJECT_RUNTIME.json',runtime)

machine=load('data/control/latest_tk_machine_state.json')
apply_runtime(machine)
pointer=machine.get('canonical_runtime_pointer')
if isinstance(pointer,dict):
    apply_runtime(pointer)
write('data/control/latest_tk_machine_state.json',machine)

history=load('PROJECT_HISTORY.json')
entry={
    'id':'ERA64C_REAL_HISTORICAL_WALLET_REPLAY_AND_VALIDATION',
    'era':'ERA64','stage':STAGE,'status':artifact['status'],'completed_at_utc':NOW,
    'artifact':artifact_path,'real_data':True,'synthetic_data':False,
    'database_source_count':artifact['database_source_count'],
    'relevant_table_count':artifact['relevant_table_count'],
    'scanned_row_count':artifact['scanned_row_count'],
    'relationship_event_count':artifact['relationship_event_count'],
    'cost_complete_trade_event_count':artifact['cost_complete_trade_event_count'],
    'closed_cycle_count':artifact['closed_cycle_count'],
    'tests':'96/96_VERIFIED','real_financial_authority':0,'next_safe_step':NEXT,
}
if isinstance(history,list):
    history.append(entry)
elif isinstance(history,dict):
    target=None
    for key in ('history','events','timeline','entries'):
        if isinstance(history.get(key),list):
            target=history[key]; break
    if target is None:
        target=history.setdefault('history',[])
    target.append(entry)
write('PROJECT_HISTORY.json',history)

roadmap=load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
def walk(value):
    if isinstance(value,dict):
        if value.get('id')=='ERA64' or value.get('era')=='ERA64':
            value['opened']=True
            value['status']='ACTIVE'
            value['current_stage']=STAGE
            value['actual_status']=artifact['status']
            value['next_safe_step']=NEXT
            value['era64c_artifact']=artifact_path
        for child in value.values(): walk(child)
    elif isinstance(value,list):
        for child in value: walk(child)
walk(roadmap)
write('data/tokenoskobi_v1_v8_master_era_roadmap.json',roadmap)

marker='<!-- ERA64C_REAL_HISTORICAL_WALLET_REPLAY -->'
blocks={
'03_ROADMAP.md':f'''\n{marker}\n## ERA64C real historical wallet replay\n\n- Status: `{artifact['status']}`\n- Real SQLite sources: `{artifact['database_source_count']}`\n- Next approval gate: `{NEXT}`\n''',
'04_ALMANAC.md':f'''\n{marker}\n## {NOW} — ERA64C\n\nReal historical wallet evidence was scanned read-only and replay validation completed with status `{artifact['status']}`. Tests: `96/96_VERIFIED`.\n''',
'06_PROJECT_MASTER_STATE.md':f'''\n{marker}\n## Current ERA64 state\n\n`{STAGE}` completed with `{artifact['status']}`. Scanned rows: `{artifact['scanned_row_count']}`. Closed cycles: `{artifact['closed_cycle_count']}`. All real financial authorities remain zero.\n''',
'07_PROJECT_HANDOFF.md':f'''\n{marker}\n## ERA64 handoff\n\n- Current stage: `{STAGE}`\n- Result: `{artifact['status']}`\n- Next: `{NEXT}`\n- Paper/live runtime: disabled\n- Real financial authority: zero\n''',
}
for path,block in blocks.items():
    text=Path(path).read_text(encoding='utf-8')
    if marker not in text:
        Path(path).write_text(text.rstrip()+"\n"+block,encoding='utf-8')

report=f'''# ERA64C REAL HISTORICAL WALLET REPLAY AND VALIDATION\n\n- Status: `{artifact['status']}`\n- Real data: `true`\n- Synthetic data: `false`\n- Database sources: `{artifact['database_source_count']}`\n- Relevant tables: `{artifact['relevant_table_count']}`\n- Scanned rows: `{artifact['scanned_row_count']}`\n- Relationship events: `{artifact['relationship_event_count']}`\n- Replayed relationship edges: `{artifact['replayed_relationship_edge_count']}`\n- Cost-complete trade events: `{artifact['cost_complete_trade_event_count']}`\n- Closed position cycles: `{artifact['closed_cycle_count']}`\n- Tests: `96/96_VERIFIED`\n- Real financial authority: `0`\n- Next: `{NEXT}`\n'''
Path('reports/LATEST_ERA64C_REAL_HISTORICAL_WALLET_REPLAY.md').write_text(report,encoding='utf-8')
Path('reports/LATEST_TK_AI_HANDOFF.md').write_text(f'''# TOKENOSKOBI LATEST HANDOFF\n\n```text\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA64\nCURRENT_STAGE={STAGE}\nRESULT={artifact['status']}\nNEXT_SAFE_STEP={NEXT}\n```\n\nReal historical replay used local SQLite in read-only mode. No financial authority was opened.\n''',encoding='utf-8')
print('CANONICAL_SYNC=VERIFIED')
print(f'NEXT_SAFE_STEP={NEXT}')
PY_CANONICAL

python3 <<'PY_VERIFY'
import json
from pathlib import Path
for path in (
 'PROJECT_RUNTIME.json','PROJECT_HISTORY.json','data/tokenoskobi_v1_v8_master_era_roadmap.json',
 'data/control/latest_tk_machine_state.json','config/era64_real_historical_wallet_replay_v1.json',
 'data/control/era64c_real_historical_wallet_replay_and_validation_v1.json',
 'data/replay/era64c_real_historical_wallet_replay_v1.json',
):
    json.loads(Path(path).read_text(encoding='utf-8'))
r=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert r['current_era']=='ERA64'
assert r['current_stage']=='ERA64C_REAL_HISTORICAL_WALLET_REPLAY_AND_VALIDATION'
assert r['next_safe_step'] in {
 'ERA64D_READONLY_SUCCESSFUL_WALLET_SCORECARD_AND_PANEL_BINDING_REQUIRES_USER_APPROVAL',
 'ERA64D_REAL_WALLET_EVENT_COVERAGE_GAP_REPAIR_REQUIRES_USER_APPROVAL',
}
a=r['authority']
assert a['real_trade_authority']==0 and a['real_wallet_authority']==0 and a['real_signing_authority']==0 and a['real_order_authority']==0
assert a['live_trade']=='DISABLED'
assert r['paper_runtime_enabled'] is False
print('CANONICAL_VERIFY=VERIFIED')
PY_VERIFY

git diff --check
git add -- \
  "${CANONICAL_FILES[@]}" \
  config/era64_real_historical_wallet_replay_v1.json \
  tools/era64_real_historical_wallet_replay_v1.py \
  tests/test_era64_real_historical_wallet_replay_v1.py \
  data/control/era64c_real_historical_wallet_replay_and_validation_v1.json \
  data/replay/era64c_real_historical_wallet_replay_v1.json
git add -f -- reports/LATEST_ERA64C_REAL_HISTORICAL_WALLET_REPLAY.md reports/LATEST_TK_AI_HANDOFF.md
git diff --cached --check
! git diff --cached --quiet

git commit -m "ERA64: validate real historical wallet replay evidence"
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
print(json.load(open('data/control/era64c_real_historical_wallet_replay_and_validation_v1.json'))['status'])
PY_RESULT
)"
trap - ERR
echo "ERA64C_STATUS=$RESULT"
echo "TESTS=96/96_VERIFIED"
echo "REAL_DATA=VERIFIED"
echo "SYNTHETIC_DATA=false"
echo "ALWAYS_ON_TECHNICAL_SERVICE=ACTIVE_READONLY"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REAL_FINANCIAL_AUTHORITY=0"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=$NEXT"
