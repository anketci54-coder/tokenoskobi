#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.authority import evaluate_authority, load_authority_state, validate_authority_state

CONFIG = ROOT / "config" / "authority_state_v1.json"


class Era61AuthorityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        loaded = load_authority_state(CONFIG)
        if not loaded.get("ok"):
            raise AssertionError(loaded)
        cls.state = loaded["state"]

    def decision(self, operation_type: str, effects: dict[str, bool], target=None):
        return evaluate_authority(
            {
                "operation_id": f"test:{operation_type}",
                "operation_type": operation_type,
                "effects": effects,
                "target": target or {},
            },
            state=self.state,
        )

    def test_config_contract_is_complete(self):
        result = validate_authority_state(self.state)
        self.assertTrue(result["ok"], result)

    def test_unknown_operation_denied(self):
        result = self.decision("unknown_magic_apply", {})
        self.assertEqual("DENY", result["decision"])

    def test_mutating_operation_requires_declared_effects(self):
        result = self.decision("db_write", {})
        self.assertEqual("DENY", result["decision"])
        self.assertIn("AUTHORITY_MUTATING_OPERATION_EFFECTS_REQUIRED", result["reason_codes"])

    def test_read_only_cannot_hide_mutation(self):
        result = self.decision("read_only", {"writes_db": True})
        self.assertEqual("DENY", result["decision"])
        self.assertIn("AUTHORITY_READ_ONLY_WITH_MUTATING_EFFECTS", result["reason_codes"])

    def test_unknown_effect_denied(self):
        result = self.decision("read_only", {"executes_unknown_side_effect": True})
        self.assertEqual("DENY", result["decision"])
        self.assertTrue(any(code.startswith("AUTHORITY_EFFECT_UNKNOWN:") for code in result["reason_codes"]))

    def test_financial_operations_are_default_deny(self):
        cases = {
            "trade_execution": {"executes_trade": True},
            "paper_trade_execution": {"executes_paper_trade": True},
            "wallet_connect": {"connects_wallet": True},
            "wallet_read": {"reads_wallet": True},
            "wallet_sign": {"signs_wallet": True},
            "transaction_broadcast": {"broadcasts_transaction": True},
            "order_create": {"creates_order": True},
            "order_cancel": {"cancels_order": True},
            "order_replace": {"replaces_order": True},
            "swap_execution": {"executes_swap": True},
        }
        for operation_type, effects in cases.items():
            with self.subTest(operation_type=operation_type):
                result = self.decision(operation_type, effects)
                self.assertEqual("DENY", result["decision"], result)

    def test_hot_publish_requires_every_authority(self):
        result = self.decision(
            "hot_path_publish",
            {
                "writes_db": True,
                "writes_file": True,
                "mutates_dashboard_active": True,
                "publishes_hot_path": True,
            },
            {"hot_path": True},
        )
        self.assertEqual("DENY", result["decision"])
        self.assertIn("HOT_PATH_MUTATION_AUTHORITY_DENIED", result["reason_codes"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
