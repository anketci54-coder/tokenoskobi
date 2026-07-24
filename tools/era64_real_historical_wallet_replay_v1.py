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
