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
