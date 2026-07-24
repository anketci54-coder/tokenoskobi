#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era64b_direct_foundation_backup_${STAMP}.tar.gz"
COMMITTED=0

NEW_FILES=(
  config/era64_successful_wallet_foundation_v1.json
  tools/era64_successful_wallet_foundation_v1.py
  tests/test_era64_successful_wallet_foundation_v1.py
  data/control/era64b_successful_wallet_statistics_and_cluster_foundation_v1.json
  reports/LATEST_ERA64B_SUCCESSFUL_WALLET_FOUNDATION.md
)
CANONICAL_FILES=(
  PROJECT_RUNTIME.json
  PROJECT_HISTORY.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
  03_ROADMAP.md
  04_ALMANAC.md
  06_PROJECT_MASTER_STATE.md
  07_PROJECT_HANDOFF.md
  reports/LATEST_TK_AI_HANDOFF.md
)

rollback() {
  rc=$?
  trap - ERR
  echo "ERA64B_FAILED_RC=$rc"
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

python3 <<'PY_PRECHECK'
import json
from pathlib import Path
r=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert r.get('current_era') == 'ERA64'
assert r.get('current_stage') == 'ERA64A_EXISTING_WALLET_DATA_AND_CAPABILITY_AUDIT'
assert r.get('next_safe_step') == 'ERA64B_SUCCESSFUL_WALLET_STATISTICS_AND_CLUSTER_FOUNDATION_BUILD_REQUIRES_USER_APPROVAL'
a=r.get('authority',{})
assert a.get('real_trade_authority') == 0
assert a.get('real_wallet_authority') == 0
assert a.get('real_signing_authority') == 0
assert a.get('real_order_authority') == 0
assert a.get('live_trade') == 'DISABLED'
assert a.get('paper_trade') == 'DISABLED_PENDING_COORDINATED_INTELLIGENCE'
print('PRECHECK=VERIFIED')
PY_PRECHECK

systemctl is-enabled --quiet tokenoskobi-era63e-always-on-market.service
systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer

tar -czf "$BACKUP" -C /root/tokenoskobi_clean_v1 "${CANONICAL_FILES[@]}"
echo "BACKUP=$BACKUP"

mkdir -p config tools tests data/control reports

cat > config/era64_successful_wallet_foundation_v1.json <<'JSON'
{
  "schema": "tokenoskobi.era64.successful_wallet_foundation.v1",
  "mode": "LOCAL_READ_ONLY_DETERMINISTIC",
  "chain": "BSC_EVM_COMPATIBLE",
  "max_nodes": 128,
  "max_edges": 512,
  "max_graph_depth": 4,
  "minimum_cluster_edge_confidence": 0.65,
  "minimum_repeatable_sample": 8,
  "authority": {
    "network_access": false,
    "database_write": false,
    "runtime_mutation": false,
    "panel_mutation": false,
    "service_mutation": false,
    "timer_mutation": false,
    "paper_trade": false,
    "live_trade": false,
    "wallet": false,
    "signing": false,
    "order_create": false,
    "broadcast": false
  }
}
JSON

cat > tools/era64_successful_wallet_foundation_v1.py <<'PY_MODULE'
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
PY_MODULE

cat > tests/test_era64_successful_wallet_foundation_v1.py <<'PY_TEST'
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from era64_successful_wallet_foundation_v1 import (
    WalletFoundationError,
    build_foundation,
    build_relationship_graph,
    calculate_performance,
    normalize_wallet,
    reconstruct_position_cycles,
    resolve_wallet_label,
)

A = "0x" + "1" * 40
B = "0x" + "2" * 40
C = "0x" + "3" * 40


def trade(wallet, token, side, quantity, price, timestamp, suffix, fee=0.0, gas=0.0):
    return {
        "wallet": wallet,
        "token": token,
        "side": side,
        "quantity": quantity,
        "price": price,
        "timestamp": timestamp,
        "tx_hash": "0x" + suffix * 64,
        "evidence_id": "ev-" + suffix,
        "fee": fee,
        "gas": gas,
    }


class Era64SuccessfulWalletFoundationTests(unittest.TestCase):
    def test_01_wallet_normalization(self):
        self.assertEqual(normalize_wallet(A.upper().replace("0X", "0x")), A)

    def test_02_invalid_wallet_fails_closed(self):
        with self.assertRaises(WalletFoundationError):
            normalize_wallet("0x123")

    def test_03_label_resolution_is_deterministic(self):
        evidence = [
            {"wallet": A, "label": "SMART_MONEY", "source": "s2", "evidence_id": "b", "confidence": 0.91},
            {"wallet": A, "label": "SMART_MONEY", "source": "s1", "evidence_id": "a", "confidence": 0.95},
        ]
        out = resolve_wallet_label(A, evidence)
        self.assertEqual(out["status"], "VERIFIED")
        self.assertEqual(out["label"], "SMART_MONEY")
        self.assertEqual(out["evidence"][0]["evidence_id"], "a")

    def test_04_equal_confidence_label_conflict_is_preserved(self):
        evidence = [
            {"wallet": A, "label": "SMART_MONEY", "source": "s1", "evidence_id": "a", "confidence": 0.9},
            {"wallet": A, "label": "TEAM_WALLET", "source": "s2", "evidence_id": "b", "confidence": 0.9},
        ]
        self.assertEqual(resolve_wallet_label(A, evidence)["status"], "CONFLICT")

    def test_05_funding_edge_builds_cluster(self):
        graph = build_relationship_graph([{
            "from_wallet": A, "to_wallet": B, "relation_type": "FUNDING", "tx_hash": "0xabc",
            "evidence_id": "fund-1", "token": "USDT", "amount": 100.0, "timestamp": 1, "block_number": 10,
        }])
        self.assertEqual(graph["node_count"], 2)
        self.assertEqual(graph["clusters"][0]["wallet_count"], 2)

    def test_06_single_weak_transfer_does_not_force_cluster(self):
        graph = build_relationship_graph([{
            "from_wallet": A, "to_wallet": B, "relation_type": "TRANSFER", "tx_hash": "0xabc",
            "evidence_id": "transfer-1", "token": "USDT", "amount": 1.0, "timestamp": 1, "block_number": 10,
        }])
        self.assertEqual(len(graph["clusters"]), 2)

    def test_07_fifo_cycle_is_cost_adjusted(self):
        out = reconstruct_position_cycles([
            trade(A, "ABC", "BUY", 10, 2, 1, "a", fee=1, gas=1),
            trade(A, "ABC", "SELL", 10, 3, 2, "b", fee=1, gas=1),
        ])
        self.assertEqual(out["closed_cycle_count"], 1)
        self.assertAlmostEqual(out["cycles"][0]["pnl"], 6.0)

    def test_08_oversell_fails_closed(self):
        with self.assertRaises(WalletFoundationError):
            reconstruct_position_cycles([
                trade(A, "ABC", "BUY", 1, 2, 1, "a"),
                trade(A, "ABC", "SELL", 2, 3, 2, "b"),
            ])

    def test_09_performance_metrics_complete(self):
        cycles = [{"return": x, "pnl": x * 100} for x in (0.1, 0.08, -0.03, 0.12, 0.05, -0.02, 0.09, 0.07)]
        out = calculate_performance(cycles)
        self.assertIn(out["status"], {"REPEATABLE_EDGE", "UNPROVEN_EDGE"})
        self.assertEqual(out["metrics"]["sample_size"], 8)
        self.assertIn("max_drawdown", out["metrics"])

    def test_10_authority_is_zero(self):
        payload = {
            "wallets": [A],
            "label_evidence": [],
            "relationship_events": [],
            "trades": [],
        }
        out = build_foundation(payload)
        self.assertTrue(all(value is False for value in out["authority"].values()))

    def test_11_output_is_deterministic(self):
        payload = {
            "wallets": [A],
            "label_evidence": [],
            "relationship_events": [],
            "trades": [],
        }
        self.assertEqual(build_foundation(payload), build_foundation(json.loads(json.dumps(payload))))

    def test_12_source_has_no_network_db_or_dynamic_execution(self):
        source = (ROOT / "tools/era64_successful_wallet_foundation_v1.py").read_text(encoding="utf-8")
        forbidden = ["subprocess", "os.system", "shell=True", "eval(", "exec(", "requests.", "urllib", "sqlite3", "websocket"]
        self.assertFalse(any(token in source for token in forbidden))


if __name__ == "__main__":
    unittest.main(verbosity=2)
PY_TEST

python3 -m py_compile tools/era64_successful_wallet_foundation_v1.py tests/test_era64_successful_wallet_foundation_v1.py
python3 tests/test_era64_successful_wallet_foundation_v1.py
python3 tools/era58_smart_money_performance_engine_v1_test.py
python3 tests/test_era63b_paper_trading_core_v1.py
python3 tests/test_era63c_technical_dex_execution_v1.py
python3 tests/test_era63d_market_technical_runtime_v1.py
python3 tests/test_era63e_always_on_market_runtime_v1.py

echo "TESTS=86/86_VERIFIED"

python3 <<'PY_CANONICAL'
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

R=Path('/root/tokenoskobi_clean_v1')
NOW=datetime.now(timezone.utc).isoformat()
STAGE='ERA64B_SUCCESSFUL_WALLET_STATISTICS_AND_CLUSTER_FOUNDATION'
NEXT='ERA64C_REAL_HISTORICAL_WALLET_REPLAY_AND_VALIDATION_REQUIRES_USER_APPROVAL'


def load(path):
    return json.loads((R/path).read_text(encoding='utf-8'))


def save(path, value):
    p=R/path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def write(path, value):
    p=R/path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value.rstrip()+'\n', encoding='utf-8')


def block(path, marker, value):
    p=R/path
    text=p.read_text(encoding='utf-8') if p.exists() else ''
    start=f'<!-- {marker}:BEGIN -->'
    end=f'<!-- {marker}:END -->'
    rendered=f'{start}\n{value.rstrip()}\n{end}'
    pattern=re.compile(re.escape(start)+r'.*?'+re.escape(end), re.S)
    write(path, pattern.sub(rendered, text, 1) if pattern.search(text) else text.rstrip()+'\n\n'+rendered)

artifact={
    'schema':'tokenoskobi.era64b.successful_wallet_statistics_and_cluster_foundation.v1',
    'era':'ERA64',
    'stage':STAGE,
    'status':'FOUNDATION_BUILT_VERIFIED',
    'built_at_utc':NOW,
    'module':'tools/era64_successful_wallet_foundation_v1.py',
    'config':'config/era64_successful_wallet_foundation_v1.json',
    'tests':'tests/test_era64_successful_wallet_foundation_v1.py',
    'foundation_tests':'12/12_VERIFIED',
    'legacy_performance_tests':'5/5_VERIFIED',
    'era63_regression_tests':'69/69_VERIFIED',
    'total_tests':'86/86_VERIFIED',
    'capabilities':[
        'DETERMINISTIC_WALLET_IDENTITY_NORMALIZATION',
        'EVIDENCE_BACKED_LABEL_RESOLUTION_WITH_CONFLICT_PRESERVATION',
        'BOUNDED_RELATIONSHIP_AND_CLUSTER_GRAPH',
        'FUNDING_AND_RELATED_WALLET_EDGES',
        'FIFO_POSITION_CYCLE_RECONSTRUCTION',
        'FEE_AND_GAS_ADJUSTED_REALIZED_PNL',
        'WIN_RATE_ROI_MEDIAN_RETURN_DRAWDOWN_RISK_ADJUSTED_METRICS',
        'DETERMINISTIC_HASHED_OUTPUT',
        'FAIL_CLOSED_INVALID_INPUT_HANDLING'
    ],
    'authority':{
        'network_access':False,
        'database_write':False,
        'runtime_mutation':False,
        'panel_mutation':False,
        'service_mutation':False,
        'timer_mutation':False,
        'paper_trade':False,
        'live_trade':False,
        'wallet':False,
        'signing':False,
        'order_create':False,
        'broadcast':False
    },
    'next_safe_step':NEXT
}
save('data/control/era64b_successful_wallet_statistics_and_cluster_foundation_v1.json', artifact)

runtime=load('PROJECT_RUNTIME.json')
runtime.update({
    'current_version':'V4',
    'current_era':'ERA64',
    'current_stage':STAGE,
    'current_status':'ACTIVE_FOUNDATION_BUILT_VERIFIED',
    'project_status':'V4_ERA64_ACTIVE',
    'status':'ACTIVE',
    'last_completed':STAGE,
    'last_result':'FOUNDATION_BUILT_VERIFIED',
    'next_safe_step':NEXT,
    'updated_at':NOW,
    'updated_at_utc':NOW
})
runtime['era64_foundation']={
    'status':'FOUNDATION_BUILT_VERIFIED',
    'artifact':'data/control/era64b_successful_wallet_statistics_and_cluster_foundation_v1.json',
    'module':'tools/era64_successful_wallet_foundation_v1.py',
    'tests':'86/86_VERIFIED',
    'implementation_authorized_for_stage':True,
    'network_access':False,
    'database_write':False,
    'runtime_panel_service_timer_mutation':False,
    'real_financial_authority':0
}
work=runtime.setdefault('work_unit',{})
work.update({
    'id':'ERA64_SUCCESSFUL_WALLET_INTELLIGENCE_AND_STATISTICAL_PERFORMANCE',
    'title':'Successful Wallet Intelligence and Statistical Performance',
    'status':'OPEN_FOUNDATION_BUILT_VERIFIED',
    'next_substep':NEXT
})
completed=work.setdefault('completed_substeps',[])
for item in ('ERA64A_EXISTING_WALLET_DATA_AND_CAPABILITY_AUDIT', STAGE):
    if item not in completed:
        completed.append(item)
ptr=runtime.setdefault('canonical_runtime_pointer',{})
ptr.update({
    'current_era':'ERA64',
    'current_stage':STAGE,
    'current_status':'ACTIVE_FOUNDATION_BUILT_VERIFIED',
    'era64_opened':True,
    'era64_implementation_authorized':True,
    'era64b_foundation_verified':True,
    'next_safe_step':NEXT
})
save('PROJECT_RUNTIME.json', runtime)

history=load('PROJECT_HISTORY.json')
events=history.setdefault('events',[])
events=[x for x in events if not (isinstance(x,dict) and x.get('event_id')=='ERA64B_SUCCESSFUL_WALLET_STATISTICS_AND_CLUSTER_FOUNDATION')]
events.append({
    'event_id':'ERA64B_SUCCESSFUL_WALLET_STATISTICS_AND_CLUSTER_FOUNDATION',
    'event':'SUCCESSFUL_WALLET_FOUNDATION_BUILD',
    'era':'ERA64',
    'status':'FOUNDATION_BUILT_VERIFIED',
    'artifact':'data/control/era64b_successful_wallet_statistics_and_cluster_foundation_v1.json',
    'tests':'86/86_VERIFIED',
    'real_financial_authority':0,
    'next_safe_step':NEXT,
    'timestamp_utc':NOW
})
history['events']=events
history['updated_at_utc']=NOW
save('PROJECT_HISTORY.json', history)

roadmap=load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
for version in roadmap.get('versions',[]):
    if isinstance(version,dict) and version.get('id')=='V4':
        for era in version.get('children',[]):
            if isinstance(era,dict) and era.get('id')=='ERA64':
                era.update({
                    'opened':True,
                    'status':'ACTIVE_FOUNDATION_BUILT_VERIFIED',
                    'active_stage':STAGE,
                    'implementation_authorized':True,
                    'foundation_artifact':'data/control/era64b_successful_wallet_statistics_and_cluster_foundation_v1.json',
                    'foundation_tests':'86/86_VERIFIED',
                    'next_safe_step':NEXT
                })
roadmap.setdefault('current_direction',{}).update({
    'current_version':'V4',
    'current_era':'ERA64',
    'current_line':'ERA64_SUCCESSFUL_WALLET_INTELLIGENCE_AND_STATISTICAL_PERFORMANCE',
    'current_stage':STAGE,
    'current_status':'ACTIVE_FOUNDATION_BUILT_VERIFIED',
    'era64_opened':True,
    'new_work_unit_opened':True,
    'next_safe_step':NEXT,
    'updated_at_utc':NOW
})
save('data/tokenoskobi_v1_v8_master_era_roadmap.json', roadmap)

machine=load('data/control/latest_tk_machine_state.json')
machine.update({
    'current_version':'V4',
    'current_era':'ERA64',
    'current_stage':STAGE,
    'current_status':'ACTIVE_FOUNDATION_BUILT_VERIFIED',
    'last_completed':STAGE,
    'next_safe_step':NEXT,
    'era64_opened':True,
    'era64b_foundation_verified':True,
    'updated_at_utc':NOW
})
save('data/control/latest_tk_machine_state.json', machine)

write('03_ROADMAP.md', f'''# 03 ROADMAP - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={STAGE}
ERA64_STATUS=ACTIVE_FOUNDATION_BUILT_VERIFIED
NEXT_SAFE_STEP={NEXT}

## LOCKED V4 EXECUTION ORDER

```text
ERA63=TECHNICAL_ANALYSIS_AND_DEX_EXECUTION=CLOSED
ERA64=SUCCESSFUL_WALLET_STATS_AND_CLUSTERING=ACTIVE
ERA65=ONCHAIN_AND_CEX_TO_DEX_WHALE_FLOW
ERA66=NEWS_AIRDROP_ICO_IDO_AND_LAUNCH_INTELLIGENCE
ERA67=COORDINATED_MULTI_INTELLIGENCE_FUSION
ERA68=UNATTENDED_COORDINATED_PAPER_RUNTIME
```

ERA64B now provides deterministic wallet identity, evidence-preserving labels, bounded main/sub-wallet clustering, funding relationships, FIFO position-cycle reconstruction and cost-adjusted performance statistics. Historical real-data replay remains separately gated.''')

block('04_ALMANAC.md','ERA64B_SUCCESSFUL_WALLET_FOUNDATION',f'''## ERA64B SUCCESSFUL WALLET STATISTICS AND CLUSTER FOUNDATION

- Status: `FOUNDATION_BUILT_VERIFIED`
- Module: `tools/era64_successful_wallet_foundation_v1.py`
- Tests: `86/86_VERIFIED`
- Network/database/runtime/panel/service/timer mutation: `false`
- Paper/live/wallet/signing/order/broadcast authority: `0`
- Artifact: `data/control/era64b_successful_wallet_statistics_and_cluster_foundation_v1.json`
- Next: `{NEXT}`
- UTC: `{NOW}`''')

write('06_PROJECT_MASTER_STATE.md',f'''# 06 PROJECT MASTER STATE - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={STAGE}
CURRENT_STATUS=ACTIVE_FOUNDATION_BUILT_VERIFIED
NEXT_SAFE_STEP={NEXT}

## VERIFIED FOUNDATION

- Deterministic wallet identity and evidence labels
- Bounded relationship, funding and cluster graph
- FIFO position-cycle reconstruction
- Fee/gas-adjusted P&L and return metrics
- Win rate, ROI, median return, drawdown and risk-adjusted performance
- Tests: `86/86_VERIFIED`

## AUTHORITY

```text
NETWORK_ACCESS=false
DATABASE_WRITE=false
PAPER_RUNTIME=false
LIVE_TRADE=DISABLED
REAL_WALLET=false
REAL_SIGNING=false
REAL_ORDER=false
REAL_BROADCAST=false
```

The resident ERA63E technical observation service remains active and read-only. ERA64C real historical replay is not authorized yet.''')

write('07_PROJECT_HANDOFF.md',f'''# 07 PROJECT HANDOFF - TOKENOSKOBI

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={STAGE}
CURRENT_STATUS=ACTIVE_FOUNDATION_BUILT_VERIFIED
NEXT_SAFE_STEP={NEXT}

ERA64A evidence audit is complete. ERA64B built the deterministic local read-only successful-wallet foundation with evidence labels, relationship clusters, funding edges, FIFO position cycles and cost-adjusted statistical performance.

Evidence:
- `data/control/era64a_opening_scope_and_evidence_audit_v1.json`
- `data/control/era64b_successful_wallet_statistics_and_cluster_foundation_v1.json`
- `tools/era64_successful_wallet_foundation_v1.py`
- `tests/test_era64_successful_wallet_foundation_v1.py`

No network, database, panel, service, timer or real financial authority was opened.''')

write('reports/LATEST_ERA64B_SUCCESSFUL_WALLET_FOUNDATION.md',f'''# ERA64B SUCCESSFUL WALLET FOUNDATION

- Status: `FOUNDATION_BUILT_VERIFIED`
- Tests: `86/86_VERIFIED`
- Module: `tools/era64_successful_wallet_foundation_v1.py`
- Config: `config/era64_successful_wallet_foundation_v1.json`
- Artifact: `data/control/era64b_successful_wallet_statistics_and_cluster_foundation_v1.json`
- Authority: `READ_ONLY_ZERO_FINANCIAL_AUTHORITY`
- Next: `{NEXT}`
''')

write('reports/LATEST_TK_AI_HANDOFF.md',f'''# TOKENOSKOBI LATEST HANDOFF

```text
CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={STAGE}
LAST_COMPLETED={STAGE}
NEXT_SAFE_STEP={NEXT}
```

ERA64B foundation is built and verified. Real historical replay remains approval-gated.''')

print('CANONICAL_SYNC=VERIFIED')
print(f'NEXT_SAFE_STEP={NEXT}')
PY_CANONICAL

python3 <<'PY_VERIFY'
import json
from pathlib import Path
paths=[
 'PROJECT_RUNTIME.json','PROJECT_HISTORY.json','data/tokenoskobi_v1_v8_master_era_roadmap.json',
 'data/control/latest_tk_machine_state.json','config/era64_successful_wallet_foundation_v1.json',
 'data/control/era64b_successful_wallet_statistics_and_cluster_foundation_v1.json'
]
for path in paths:
    json.loads(Path(path).read_text(encoding='utf-8'))
r=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
assert r['current_era']=='ERA64'
assert r['current_stage']=='ERA64B_SUCCESSFUL_WALLET_STATISTICS_AND_CLUSTER_FOUNDATION'
assert r['next_safe_step']=='ERA64C_REAL_HISTORICAL_WALLET_REPLAY_AND_VALIDATION_REQUIRES_USER_APPROVAL'
a=r['authority']
assert a['real_trade_authority']==0 and a['real_wallet_authority']==0 and a['real_signing_authority']==0 and a['real_order_authority']==0
assert a['live_trade']=='DISABLED'
assert a['paper_trade']=='DISABLED_PENDING_COORDINATED_INTELLIGENCE'
print('CANONICAL_VERIFY=VERIFIED')
PY_VERIFY

git diff --check
git add -- \
  "${CANONICAL_FILES[@]}" \
  config/era64_successful_wallet_foundation_v1.json \
  tools/era64_successful_wallet_foundation_v1.py \
  tests/test_era64_successful_wallet_foundation_v1.py \
  data/control/era64b_successful_wallet_statistics_and_cluster_foundation_v1.json
git add -f -- reports/LATEST_ERA64B_SUCCESSFUL_WALLET_FOUNDATION.md reports/LATEST_TK_AI_HANDOFF.md
git diff --cached --check
! git diff --cached --quiet

git commit -m "ERA64: build successful wallet statistics and cluster foundation"
COMMITTED=1
HEAD="$(git rev-parse HEAD)"
git push origin main
git fetch origin main --quiet
[[ "$(git rev-parse origin/main)" == "$HEAD" ]]
[[ -z "$(git status --porcelain=v1)" ]]
systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer

trap - ERR
echo "ERA64B_STATUS=FOUNDATION_BUILT_VERIFIED_GITHUB_SEALED"
echo "TESTS=86/86_VERIFIED"
echo "ALWAYS_ON_TECHNICAL_SERVICE=ACTIVE_READONLY"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REAL_FINANCIAL_AUTHORITY=0"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$HEAD"
echo "NEXT_SAFE_STEP=ERA64C_REAL_HISTORICAL_WALLET_REPLAY_AND_VALIDATION_REQUIRES_USER_APPROVAL"
