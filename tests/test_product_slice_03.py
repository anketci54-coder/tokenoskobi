import importlib.util
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ.setdefault("TOKENOSKOBI_ROOT", str(REPO))
os.environ.setdefault(
    "TOKENOSKOBI_GT_RATE_DIR",
    tempfile.mkdtemp(prefix="tokenoskobi_gt_slice03_test_"),
)
os.environ.setdefault(
    "TOKENOSKOBI_SLICE03_STATE_DIR",
    tempfile.mkdtemp(prefix="tokenoskobi_slice03_import_"),
)
os.environ.setdefault(
    "TOKENOSKOBI_SLICE02_SERVER_PATH",
    str(REPO / "tools/tokenoskobi_product_slice_02_server.py"),
)
SERVER = Path(
    os.getenv(
        "TOKENOSKOBI_SLICE03_SERVER_PATH",
        REPO / "tools/tokenoskobi_product_slice_03_server.py",
    )
)
SPEC = importlib.util.spec_from_file_location("product_slice_03", SERVER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
TOKEN = "0x" + "a" * 40


class ProductSlice03Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="slice03_test_")
        MODULE.configure_state_dir(Path(self.temp.name))
        MODULE.ensure_state()

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
        original = MODULE.SLICE02.analyze
        MODULE.SLICE02.analyze = lambda token: self.analysis()
        try:
            return MODULE.create_analysis(TOKEN)
        finally:
            MODULE.SLICE02.analyze = original

    def current_market(self, token=TOKEN, token_price=110.0, pool_price=110.0):
        return {
            "token": {
                "price_usd": token_price,
                "price_source": "TOKEN_ENDPOINT",
            },
            "selected_pool": {
                "price_usd": pool_price,
                "target_token_address": token,
                "orientation_verified": True,
            },
            "target_orientation_verified": True,
        }

    def test_digest_is_stable(self):
        self.assertEqual(
            MODULE.digest({"b": 2, "a": 1}),
            MODULE.digest({"a": 1, "b": 2}),
        )

    def test_packet_is_immutable_and_reopenable(self):
        analysis = self.analysis()
        envelope = MODULE.persist_packet(analysis)
        packet_id = envelope["packet_id"]
        self.assertEqual(MODULE.load_packet(packet_id)["analysis"], analysis)
        self.assertEqual(
            MODULE.packet_response(packet_id)["integrity"],
            "VERIFIED",
        )
        self.assertEqual(MODULE.packet_path(packet_id).stat().st_mode & 0o777, 0o600)

    def test_packet_tamper_is_rejected(self):
        envelope = MODULE.persist_packet(self.analysis())
        path = MODULE.packet_path(envelope["packet_id"])
        value = json.loads(path.read_text())
        value["analysis"]["decision"]["risk_score"] = 99
        path.write_text(json.dumps(value))
        with self.assertRaises(MODULE.HistoryCorruption):
            MODULE.load_packet(envelope["packet_id"])

    def test_event_chain_and_sequence(self):
        envelope = MODULE.persist_packet(self.analysis())
        first = MODULE.append_event(
            "ANALYSIS_CREATED",
            envelope["packet_id"],
            {"x": 1},
        )
        second = MODULE.append_event(
            "HUMAN_DECISION_RECORDED",
            envelope["packet_id"],
            {"action": "WAIT"},
        )
        events = MODULE.verify_event_chain()
        self.assertEqual([event["seq"] for event in events], [1, 2])
        self.assertEqual(second["prev_hash"], first["event_hash"])

    def test_event_tamper_is_rejected(self):
        envelope = MODULE.persist_packet(self.analysis())
        MODULE.append_event(
            "ANALYSIS_CREATED",
            envelope["packet_id"],
            {"x": 1},
        )
        event = json.loads(MODULE.EVENTS_FILE.read_text().splitlines()[0])
        event["payload"]["x"] = 2
        MODULE.EVENTS_FILE.write_text(json.dumps(event) + "\n")
        with self.assertRaises(MODULE.HistoryCorruption):
            MODULE.verify_event_chain()

    def test_create_analysis_persists_zero_authority_packet(self):
        result = self.create()
        packet_id = result["history"]["packet_id"]
        self.assertTrue(result["history"]["immutable"])
        packet = MODULE.load_packet(packet_id)
        self.assertTrue(
            all(
                packet["authority"][key] is False
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
        self.assertEqual(
            MODULE.verify_event_chain()[0]["event_type"],
            "ANALYSIS_CREATED",
        )

    def test_create_analysis_rejects_nonzero_authority(self):
        analysis = self.analysis()
        analysis["authority"]["live"] = True
        original = MODULE.SLICE02.analyze
        MODULE.SLICE02.analyze = lambda token: analysis
        try:
            with self.assertRaisesRegex(
                MODULE.HistoryCorruption,
                "ANALYSIS_AUTHORITY_NOT_ZERO",
            ):
                MODULE.create_analysis(TOKEN)
        finally:
            MODULE.SLICE02.analyze = original

    def test_invalid_human_action_is_rejected(self):
        result = self.create()
        with self.assertRaisesRegex(
            MODULE.ValidationError,
            "INVALID_HUMAN_ACTION",
        ):
            MODULE.record_human_decision(
                result["history"]["packet_id"],
                "BUY",
            )

    def test_human_decisions_are_append_only_revisions(self):
        packet_id = self.create()["history"]["packet_id"]
        first = MODULE.record_human_decision(packet_id, "WAIT", "first")
        second = MODULE.record_human_decision(packet_id, "ACCEPT", "second")
        self.assertEqual(
            second["event"]["payload"]["previous_decision_event_hash"],
            first["event"]["event_hash"],
        )
        self.assertEqual(
            [event["event_type"] for event in MODULE.verify_event_chain()],
            [
                "ANALYSIS_CREATED",
                "HUMAN_DECISION_RECORDED",
                "HUMAN_DECISION_RECORDED",
            ],
        )

    def test_note_length_is_bounded(self):
        packet_id = self.create()["history"]["packet_id"]
        with self.assertRaisesRegex(MODULE.ValidationError, "NOTE_TOO_LONG"):
            MODULE.record_human_decision(packet_id, "WAIT", "x" * 501)

    def test_outcome_observation_uses_requested_token_price(self):
        packet_id = self.create()["history"]["packet_id"]
        original = MODULE.SLICE02.market
        MODULE.SLICE02.market = lambda token: self.current_market(token)
        try:
            outcome = MODULE.observe_outcome(packet_id)
        finally:
            MODULE.SLICE02.market = original
        payload = outcome["event"]["payload"]
        self.assertEqual(payload["current_price_usd"], 110.0)
        self.assertEqual(payload["change_pct"], 10.0)
        self.assertTrue(payload["target_orientation_verified"])
        self.assertEqual(payload["classification"], "UP")

    def test_outcome_fails_closed_on_price_mismatch(self):
        packet_id = self.create()["history"]["packet_id"]
        original = MODULE.SLICE02.market
        MODULE.SLICE02.market = lambda token: self.current_market(
            token,
            token_price=110.0,
            pool_price=1.0,
        )
        try:
            with self.assertRaisesRegex(
                MODULE.ValidationError,
                "CURRENT_TARGET_PRICE_MISMATCH",
            ):
                MODULE.observe_outcome(packet_id)
        finally:
            MODULE.SLICE02.market = original

    def test_history_lists_latest_decision_and_outcome(self):
        packet_id = self.create()["history"]["packet_id"]
        MODULE.record_human_decision(packet_id, "REVIEW", "check")
        original = MODULE.SLICE02.market
        MODULE.SLICE02.market = lambda token: self.current_market(token)
        try:
            MODULE.observe_outcome(packet_id)
        finally:
            MODULE.SLICE02.market = original
        history = MODULE.history_records(20)
        record = history["records"][0]
        self.assertEqual(history["integrity"], "VERIFIED")
        self.assertEqual(record["packet_id"], packet_id)
        self.assertEqual(
            record["latest_human_decision"]["payload"]["action"],
            "REVIEW",
        )
        self.assertEqual(
            record["latest_outcome"]["event_type"],
            "OUTCOME_OBSERVED",
        )

    def test_invalid_packet_id_blocks_path_traversal(self):
        with self.assertRaisesRegex(MODULE.ValidationError, "INVALID_PACKET_ID"):
            MODULE.load_packet("../../etc/passwd")

    def test_missing_packet_is_not_found(self):
        with self.assertRaises(MODULE.EvidenceNotFound):
            MODULE.load_packet("0" * 64)

    def test_history_limit_is_bounded(self):
        with self.assertRaisesRegex(
            MODULE.ValidationError,
            "INVALID_HISTORY_LIMIT",
        ):
            MODULE.history_records(101)

    def test_config_authority_remains_zero(self):
        self.assertTrue(
            all(
                MODULE.AUTHORITY[key] is False
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
