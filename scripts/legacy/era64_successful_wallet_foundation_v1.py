from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from collections import defaultdict, deque
from typing import Any

ADDRESS_RE = re.compile(r"0x[0-9a-fA-F]{40}")
ALLOWED_RELATIONS = {"FUNDING", "TRANSFER", "SAME_DEPLOYER", "SHARED_COUNTERPARTY"}
RELATION_BASE_CONFIDENCE = {
    "FUNDING": 0.90,
    "SAME_DEPLOYER": 0.82,
    "SHARED_COUNTERPARTY": 0.68,
    "TRANSFER": 0.55,
}
AUTHORITY = {
    "network_access": False,
    "database_write": False,
    "runtime_mutation": False,
    "panel_mutation": False,
    "service_mutation": False,
    "timer_mutation": False,
    "paper_trade": False,
    "live_trade": False,
    "wallet": False,
    "signing": False,
    "order_create": False,
    "broadcast": False,
}


class WalletFoundationError(ValueError):
    pass


def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_wallet(value: str) -> str:
    if not isinstance(value, str) or ADDRESS_RE.fullmatch(value) is None:
        raise WalletFoundationError("INVALID_EVM_WALLET")
    return value.lower()


def resolve_wallet_label(wallet: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    address = normalize_wallet(wallet)
    rows: list[dict[str, Any]] = []
    for item in evidence:
        if normalize_wallet(str(item.get("wallet", ""))) != address:
            continue
        label = str(item.get("label", "")).strip().upper()
        source = str(item.get("source", "")).strip()
        evidence_id = str(item.get("evidence_id", "")).strip()
        confidence = float(item.get("confidence", -1))
        if not label or not source or not evidence_id or not 0.0 <= confidence <= 1.0:
            raise WalletFoundationError("INVALID_LABEL_EVIDENCE")
        rows.append({
            "label": label,
            "source": source,
            "evidence_id": evidence_id,
            "confidence": round(confidence, 6),
        })
    if not rows:
        return {"wallet": address, "status": "UNLABELED", "label": "UNKNOWN", "evidence": []}
    rows.sort(key=lambda x: (-x["confidence"], x["label"], x["source"], x["evidence_id"]))
    top_confidence = rows[0]["confidence"]
    top_labels = sorted({x["label"] for x in rows if x["confidence"] == top_confidence})
    if len(top_labels) > 1:
        return {"wallet": address, "status": "CONFLICT", "label": "UNKNOWN", "evidence": rows}
    return {"wallet": address, "status": "VERIFIED", "label": top_labels[0], "evidence": rows}


def build_relationship_graph(
    events: list[dict[str, Any]],
    *,
    max_nodes: int = 128,
    max_edges: int = 512,
    minimum_cluster_confidence: float = 0.65,
) -> dict[str, Any]:
    if max_nodes < 2 or max_edges < 1:
        raise WalletFoundationError("INVALID_GRAPH_BOUNDS")
    normalized: list[dict[str, Any]] = []
    pair_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    nodes: set[str] = set()
    for event in events:
        src = normalize_wallet(str(event.get("from_wallet", "")))
        dst = normalize_wallet(str(event.get("to_wallet", "")))
        if src == dst:
            raise WalletFoundationError("SELF_EDGE_REJECTED")
        relation = str(event.get("relation_type", "TRANSFER")).upper()
        if relation not in ALLOWED_RELATIONS:
            raise WalletFoundationError("UNKNOWN_RELATION_TYPE")
        tx_hash = str(event.get("tx_hash", "")).strip().lower()
        evidence_id = str(event.get("evidence_id", "")).strip()
        token = str(event.get("token", "UNKNOWN")).strip().upper()
        amount = float(event.get("amount", 0))
        timestamp = int(event.get("timestamp", -1))
        block_number = int(event.get("block_number", -1))
        if not tx_hash or not evidence_id or amount <= 0 or timestamp < 0 or block_number < 0:
            raise WalletFoundationError("INVALID_RELATION_EVIDENCE")
        nodes.update((src, dst))
        if len(nodes) > max_nodes:
            raise WalletFoundationError("MAX_GRAPH_NODES_EXCEEDED")
        key = (src, dst, relation)
        pair_counts[key] += 1
        normalized.append({
            "from_wallet": src,
            "to_wallet": dst,
            "relation_type": relation,
            "tx_hash": tx_hash,
            "evidence_id": evidence_id,
            "token": token,
            "amount": amount,
            "timestamp": timestamp,
            "block_number": block_number,
        })
        if len(normalized) > max_edges:
            raise WalletFoundationError("MAX_GRAPH_EDGES_EXCEEDED")

    normalized.sort(key=lambda x: (x["timestamp"], x["block_number"], x["tx_hash"], x["from_wallet"], x["to_wallet"]))
    parent = {node: node for node in nodes}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    edges: list[dict[str, Any]] = []
    for row in normalized:
        count = pair_counts[(row["from_wallet"], row["to_wallet"], row["relation_type"])]
        confidence = min(0.99, RELATION_BASE_CONFIDENCE[row["relation_type"]] + min(count - 1, 4) * 0.05)
        edge = dict(row)
        edge["repeat_count"] = count
        edge["confidence"] = round(confidence, 6)
        edge["edge_id"] = _hash({k: edge[k] for k in ("from_wallet", "to_wallet", "relation_type", "tx_hash", "evidence_id")})
        edges.append(edge)
        if confidence >= minimum_cluster_confidence:
            union(row["from_wallet"], row["to_wallet"])

    components: dict[str, list[str]] = defaultdict(list)
    for node in sorted(nodes):
        components[find(node)].append(node)
    clusters = []
    for members in sorted(components.values(), key=lambda x: (x[0], len(x))):
        members = sorted(members)
        clusters.append({
            "cluster_id": _hash({"wallets": members}),
            "main_wallet": members[0],
            "wallets": members,
            "wallet_count": len(members),
        })
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": sorted(nodes),
        "edges": edges,
        "clusters": clusters,
        "graph_hash": _hash({"nodes": sorted(nodes), "edges": edges, "clusters": clusters}),
    }


def reconstruct_position_cycles(trades: list[dict[str, Any]]) -> dict[str, Any]:
    ordered: list[dict[str, Any]] = []
    for trade in trades:
        wallet = normalize_wallet(str(trade.get("wallet", "")))
        token = str(trade.get("token", "")).strip().upper()
        side = str(trade.get("side", "")).strip().upper()
        tx_hash = str(trade.get("tx_hash", "")).strip().lower()
        evidence_id = str(trade.get("evidence_id", "")).strip()
        quantity = float(trade.get("quantity", 0))
        price = float(trade.get("price", 0))
        fee = float(trade.get("fee", 0))
        gas = float(trade.get("gas", 0))
        timestamp = int(trade.get("timestamp", -1))
        if not token or side not in {"BUY", "SELL"} or not tx_hash or not evidence_id:
            raise WalletFoundationError("INVALID_TRADE_IDENTITY")
        if quantity <= 0 or price <= 0 or fee < 0 or gas < 0 or timestamp < 0:
            raise WalletFoundationError("INVALID_TRADE_VALUES")
        ordered.append({
            "wallet": wallet,
            "token": token,
            "side": side,
            "tx_hash": tx_hash,
            "evidence_id": evidence_id,
            "quantity": quantity,
            "price": price,
            "fee": fee,
            "gas": gas,
            "timestamp": timestamp,
        })
    ordered.sort(key=lambda x: (x["timestamp"], x["tx_hash"], x["wallet"], x["token"], x["side"]))
    lots: dict[tuple[str, str], deque[dict[str, float]]] = defaultdict(deque)
    cycles: list[dict[str, Any]] = []
    total_costs = 0.0
    for row in ordered:
        key = (row["wallet"], row["token"])
        trade_costs = row["fee"] + row["gas"]
        total_costs += trade_costs
        if row["side"] == "BUY":
            unit_cost = (row["quantity"] * row["price"] + trade_costs) / row["quantity"]
            lots[key].append({"quantity": row["quantity"], "unit_cost": unit_cost, "entry_timestamp": row["timestamp"]})
            continue
        remaining = row["quantity"]
        available = sum(lot["quantity"] for lot in lots[key])
        if remaining > available + 1e-12:
            raise WalletFoundationError("SELL_EXCEEDS_POSITION")
        allocated_sell_cost = trade_costs
        while remaining > 1e-12:
            lot = lots[key][0]
            used = min(remaining, lot["quantity"])
            proportion = used / row["quantity"]
            cost_basis = used * lot["unit_cost"]
            proceeds = used * row["price"] - allocated_sell_cost * proportion
            pnl = proceeds - cost_basis
            cycles.append({
                "wallet": row["wallet"],
                "token": row["token"],
                "quantity": round(used, 12),
                "entry_timestamp": int(lot["entry_timestamp"]),
                "exit_timestamp": row["timestamp"],
                "cost_basis": round(cost_basis, 12),
                "proceeds": round(proceeds, 12),
                "pnl": round(pnl, 12),
                "return": round(pnl / cost_basis, 12) if cost_basis > 0 else 0.0,
                "exit_tx_hash": row["tx_hash"],
                "evidence_id": row["evidence_id"],
            })
            lot["quantity"] -= used
            remaining -= used
            if lot["quantity"] <= 1e-12:
                lots[key].popleft()
    open_positions = []
    for (wallet, token), queue in sorted(lots.items()):
        quantity = sum(x["quantity"] for x in queue)
        if quantity > 1e-12:
            open_positions.append({"wallet": wallet, "token": token, "quantity": round(quantity, 12)})
    return {
        "closed_cycle_count": len(cycles),
        "cycles": cycles,
        "open_positions": open_positions,
        "total_costs": round(total_costs, 12),
        "cycle_hash": _hash(cycles),
    }


def calculate_performance(cycles: list[dict[str, Any]], minimum_repeatable_sample: int = 8) -> dict[str, Any]:
    returns = [float(x["return"]) for x in cycles]
    pnls = [float(x["pnl"]) for x in cycles]
    if not returns:
        return {"status": "NO_CLOSED_POSITIONS", "sample_size": 0, "copyable": False}
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in returns:
        if value <= -1.0:
            raise WalletFoundationError("RETURN_BELOW_MINUS_ONE")
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, 1.0 - equity / peak)
    downside = [min(0.0, value) for value in returns]
    std = statistics.pstdev(returns) if len(returns) > 1 else 0.0
    mean = statistics.mean(returns)
    risk_adjusted = mean / std if std > 0 else (99.0 if mean > 0 else 0.0)
    wins = [value for value in pnls if value > 0]
    losses = [-value for value in pnls if value < 0]
    profit_factor = sum(wins) / sum(losses) if losses else (99.0 if wins else 0.0)
    metrics = {
        "sample_size": len(returns),
        "win_rate": round(len(wins) / len(returns), 12),
        "roi": round(equity - 1.0, 12),
        "mean_return": round(mean, 12),
        "median_return": round(statistics.median(returns), 12),
        "max_drawdown": round(max_drawdown, 12),
        "downside_deviation": round(math.sqrt(sum(x * x for x in downside) / len(downside)), 12),
        "risk_adjusted_performance": round(risk_adjusted, 12),
        "profit_factor": round(profit_factor, 12),
        "consistency": round(len(wins) / len(returns), 12),
        "total_realized_pnl": round(sum(pnls), 12),
    }
    if len(returns) < minimum_repeatable_sample:
        status = "INSUFFICIENT_SAMPLE"
    elif max_drawdown > 0.35:
        status = "FRAGILE_EDGE"
    elif profit_factor >= 1.5 and metrics["win_rate"] >= 0.55 and mean > 0:
        status = "REPEATABLE_EDGE"
    else:
        status = "UNPROVEN_EDGE"
    return {"status": status, "copyable": status == "REPEATABLE_EDGE", "metrics": metrics}


def build_foundation(payload: dict[str, Any]) -> dict[str, Any]:
    labels = [resolve_wallet_label(wallet, payload.get("label_evidence", [])) for wallet in payload.get("wallets", [])]
    graph = build_relationship_graph(payload.get("relationship_events", []))
    positions = reconstruct_position_cycles(payload.get("trades", []))
    performance = calculate_performance(positions["cycles"])
    result = {
        "schema": "tokenoskobi.era64.successful_wallet_foundation.output.v1",
        "status": "FOUNDATION_READY" if not any(x["status"] == "CONFLICT" for x in labels) else "LABEL_CONFLICT_REVIEW",
        "authority": dict(AUTHORITY),
        "labels": labels,
        "relationship_graph": graph,
        "position_cycles": positions,
        "performance": performance,
    }
    result["result_hash"] = _hash(result)
    return result
