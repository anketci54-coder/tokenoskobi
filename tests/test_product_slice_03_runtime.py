import importlib.util
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ.setdefault("TOKENOSKOBI_ROOT", str(REPO))
os.environ.setdefault(
    "TOKENOSKOBI_GT_RATE_DIR",
    tempfile.mkdtemp(prefix="tokenoskobi_gt_slice03_runtime_test_"),
)
os.environ.setdefault(
    "TOKENOSKOBI_SLICE03_STATE_DIR",
    tempfile.mkdtemp(prefix="tokenoskobi_slice03_runtime_import_"),
)
os.environ.setdefault(
    "TOKENOSKOBI_SLICE02_SERVER_PATH",
    str(REPO / "tools/tokenoskobi_product_slice_02_server.py"),
)
os.environ.setdefault(
    "TOKENOSKOBI_SLICE03_CORE_PATH",
    str(REPO / "tools/tokenoskobi_product_slice_03_server.py"),
)
RUNTIME_PATH = Path(
    os.getenv(
        "TOKENOSKOBI_SLICE03_RUNTIME_PATH",
        REPO / "tools/tokenoskobi_product_slice_03_runtime.py",
    )
)
SPEC = importlib.util.spec_from_file_location(
    "product_slice_03_runtime",
    RUNTIME_PATH,
)
assert SPEC and SPEC.loader
RUNTIME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNTIME)
CORE = RUNTIME.CORE
TOKEN = "0x" + "a" * 40


class ProductSlice03RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="slice03_runtime_")
        CORE.configure_state_dir(Path(self.temp.name))
        CORE.ensure_state()

    def tearDown(self):
        self.temp.cleanup()

    def analysis(self):
        return {
            "schema": "tokenoskobi.product_slice_02.packet.v1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "chain": "BSC",
            "token_address": TOKEN,
            "contract": {
                "code_exists": True,
                "metadata": {"symbol": "TEST", "name": "Test Token"},
            },
            "market": {
                "token": {
                    "symbol": "TEST",
                    "name": "Test Token",
                    "price_usd": 100.0,
                    "price_source": "TOKEN_ENDPOINT",
                },
                "selected_pool": {
                    "price_usd": 100.0,
                    "reserve_usd": 1_000_000,
                    "target_token_address": TOKEN,
                    "target_side": "base",
                    "orientation_verified": True,
                },
                "target_orientation_verified": True,
            },
            "technical_timeframes": {
                "1m": {
                    "status": "OK",
                    "target_token_address": TOKEN,
                    "last": 100.0,
                },
                "5m": {
                    "status": "OK",
                    "target_token_address": TOKEN,
                    "last": 100.0,
                },
            },
            "decision": {
                "decision": "ALLOW",
                "risk_score": 20,
                "data_quality": "SUFFICIENT",
                "blockers": [],
                "warnings": [],
                "evidence": ["TEST_EVIDENCE"],
                "authority": "ADVISORY_ONLY",
            },
            "authority": {
                "paper": False,
                "live": False,
                "wallet": False,
                "signing": False,
                "order": False,
                "broadcast": False,
                "human_action_required": True,
            },
        }

    def create(self):
        original = CORE.SLICE02.analyze
        CORE.SLICE02.analyze = lambda token: self.analysis()
        try:
            return CORE.create_analysis(TOKEN)
        finally:
            CORE.SLICE02.analyze = original

    def market(self):
        return {
            "token": {
                "price_usd": 110.0,
                "price_source": "TOKEN_ENDPOINT",
            },
            "selected_pool": {
                "price_usd": 110.0,
                "target_token_address": TOKEN,
                "orientation_verified": True,
            },
            "target_orientation_verified": True,
        }

    def test_runtime_patches_core_boundaries(self):
        self.assertIs(
            CORE.verify_event_chain,
            RUNTIME.verify_event_chain_locked,
        )
        self.assertIs(CORE.append_event, RUNTIME.append_event_locked)
        self.assertIs(
            CORE.record_human_decision,
            RUNTIME.record_human_decision,
        )
        self.assertIs(CORE.observe_outcome, RUNTIME.observe_outcome)

    def test_authenticated_actor_is_persisted(self):
        packet_id = self.create()["history"]["packet_id"]
        result = RUNTIME.record_human_decision(
            packet_id,
            "WAIT",
            "manual review",
            "coinoskobi_xyz",
        )
        self.assertEqual(
            result["event"]["payload"]["actor"],
            "coinoskobi_xyz",
        )
        persisted = RUNTIME.verify_event_chain_locked()[-1]
        self.assertEqual(
            persisted["payload"]["actor"],
            "coinoskobi_xyz",
        )

    def test_invalid_actor_fails_closed(self):
        packet_id = self.create()["history"]["packet_id"]
        with self.assertRaisesRegex(
            CORE.ValidationError,
            "INVALID_AUTHENTICATED_USER",
        ):
            RUNTIME.record_human_decision(
                packet_id,
                "WAIT",
                actor="../root",
            )

    def test_revision_pointer_uses_latest_decision(self):
        packet_id = self.create()["history"]["packet_id"]
        first = RUNTIME.record_human_decision(
            packet_id,
            "WAIT",
            actor="user",
        )
        second = RUNTIME.record_human_decision(
            packet_id,
            "ACCEPT",
            actor="user",
        )
        self.assertEqual(
            second["event"]["payload"]["previous_decision_event_hash"],
            first["event"]["event_hash"],
        )

    def test_outcome_requires_human_decision(self):
        packet_id = self.create()["history"]["packet_id"]
        original = CORE.SLICE02.market
        CORE.SLICE02.market = lambda token: self.market()
        try:
            with self.assertRaisesRegex(
                CORE.ValidationError,
                "HUMAN_DECISION_REQUIRED_BEFORE_OUTCOME",
            ):
                RUNTIME.observe_outcome(packet_id, "user")
        finally:
            CORE.SLICE02.market = original

    def test_outcome_persists_actor_and_decision_hash(self):
        packet_id = self.create()["history"]["packet_id"]
        decision = RUNTIME.record_human_decision(
            packet_id,
            "ACCEPT",
            actor="user",
        )
        original = CORE.SLICE02.market
        CORE.SLICE02.market = lambda token: self.market()
        try:
            outcome = RUNTIME.observe_outcome(packet_id, "user")
        finally:
            CORE.SLICE02.market = original
        payload = outcome["event"]["payload"]
        self.assertEqual(payload["actor"], "user")
        self.assertEqual(
            payload["human_decision_event_hash"],
            decision["event"]["event_hash"],
        )
        self.assertEqual(payload["change_pct"], 10.0)
        persisted = RUNTIME.verify_event_chain_locked()[-1]
        self.assertEqual(
            persisted["event_hash"],
            outcome["event"]["event_hash"],
        )
        self.assertEqual(persisted["payload"], payload)

    def test_zero_authority_is_preserved(self):
        self.assertTrue(
            all(
                RUNTIME.AUTHORITY[key] is False
                for key in (
                    "paper",
                    "live",
                    "wallet",
                    "signing",
                    "order",
                    "broadcast",
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
