"""Offline regressions for the bounded 36ccdcf remediation."""
import json
import sqlite3
import subprocess
import sys
import os
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from email.message import Message
from pathlib import Path
from unittest.mock import patch

from core.platform import paths
from services.market import tokenoskobi_product_slice_02_server as market
from services.market.config import validate_config
from services.market.request_validation import validate_json_headers
from tests.test_market_data_validation import NOW, TOKEN, decision_inputs

REPO = Path(__file__).resolve().parents[1]

# Redirect only the legacy location. Real production persistence, locking,
# chain/packet verification and revision links execute in separate OS processes.
LEDGER_CHILD = """
import json, sys
from pathlib import Path
from core.platform import paths
paths.LEGACY_PRODUCT_STATE_DIR = Path(sys.argv[1]) / 'legacy'
from services.market import tokenoskobi_product_slice_03_runtime as r
c = r.CORE
if sys.argv[2] == 'seed':
    analysis = {'generated_at_utc': c.utc_now(), 'token_address': '0x' + 'a' * 40,
                'decision': {'decision': 'REVIEW'},
                'authority': {**c.CFG['authority'], 'human_action_required': True}}
    packet = c.persist_packet(analysis)
    c.append_event('ANALYSIS_CREATED', packet['packet_id'], c.analysis_summary(analysis))
elif sys.argv[2] in ('WAIT', 'REVIEW'):
    events = r.verify_event_chain_locked()
    r.record_human_decision(events[0]['packet_id'], sys.argv[2], 'isolated fixture')
print(json.dumps({'state': str(c.STATE_DIR), 'events': r.verify_event_chain_locked(),
                  'history': c.history_records()}))
"""


class LedgerLocationTests(unittest.TestCase):
    def test_legacy_ledger_precedes_xdg_without_an_explicit_override(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "legacy"
            legacy.mkdir()
            with patch.dict(os.environ, {"XDG_STATE_HOME": directory + "/xdg"}, clear=True), \
                    patch.object(paths, "LEGACY_PRODUCT_STATE_DIR", legacy):
                self.assertEqual(paths.product_state_dir(), legacy)
                legacy.rmdir()
                legacy.symlink_to(Path(directory) / "missing-ledger")
                self.assertEqual(paths.product_state_dir(), legacy)

    def test_legacy_access_error_never_selects_a_new_ledger(self):
        with patch.dict(os.environ, {"XDG_STATE_HOME": "/tmp/fresh-xdg"}, clear=True), \
                patch.object(Path, "lstat", side_effect=PermissionError("legacy denied")), \
                self.assertRaises(PermissionError):
            paths.product_state_dir()

    def test_explicit_state_dir_precedes_legacy(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, {"TOKENOSKOBI_SLICE03_STATE_DIR": directory,
                                        "XDG_STATE_HOME": "/tmp/fresh-xdg"}, clear=True), \
                patch.object(Path, "lstat", side_effect=AssertionError("explicit override must win")):
            self.assertEqual(paths.product_state_dir(), Path(directory))

    def test_fresh_install_uses_xdg_or_home(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(paths, "LEGACY_PRODUCT_STATE_DIR", Path(directory) / "absent"):
            with patch.dict(os.environ, {"XDG_STATE_HOME": directory}, clear=True):
                self.assertEqual(paths.product_state_dir(), Path(directory) / "tokenoskobi/product-slice-03")
            with patch.dict(os.environ, {}, clear=True), patch.object(Path, "home", return_value=Path(directory)):
                self.assertEqual(paths.product_state_dir(), Path(directory) / ".local/state/tokenoskobi/product-slice-03")


class LedgerContinuityTests(unittest.TestCase):
    def child(self, root, action="read", explicit=None, success=True):
        env = {key: value for key, value in os.environ.items() if not key.startswith("TOKENOSKOBI_")}
        env.update(PYTHONPATH=str(REPO), XDG_STATE_HOME=str(root / "xdg"))
        if explicit is not None:
            env["TOKENOSKOBI_SLICE03_STATE_DIR"] = str(explicit)
        result = subprocess.run([sys.executable, "-B", "-c", LEDGER_CHILD, str(root), action],
                                cwd=root, env=env, capture_output=True, text=True, timeout=10)
        if not success:
            return result
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_verified_legacy_chain_reopens_and_continues_across_processes_with_xdg_set(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "legacy"
            alternate = root / "xdg/tokenoskobi/product-slice-03"
            original = self.child(root, "seed", legacy)
            alternate_history = self.child(root, "seed", alternate)
            self.assertNotEqual(original["events"][0]["packet_id"], alternate_history["events"][0]["packet_id"])
            packet_id = original["events"][0]["packet_id"]
            packet_file = legacy / "packets" / f"{packet_id}.json"
            packet_bytes = packet_file.read_bytes()
            alternate_file = alternate / "decision_history_v1.jsonl"
            alternate_bytes = alternate_file.read_bytes()

            self.assertEqual(self.child(root), original)
            continued = self.child(root, "WAIT")
            revised = self.child(root, "REVIEW")
            self.assertEqual(revised["state"], str(legacy))
            self.assertEqual(revised["events"][:2], continued["events"])
            self.assertEqual(revised["events"][:1], original["events"])
            self.assertEqual([event["seq"] for event in revised["events"]], [1, 2, 3])
            self.assertEqual(revised["events"][2]["prev_hash"], continued["events"][1]["event_hash"])
            self.assertEqual(revised["events"][2]["payload"]["previous_decision_event_hash"],
                             continued["events"][1]["event_hash"])
            self.assertEqual(self.child(root), revised)
            self.assertEqual(packet_file.read_bytes(), packet_bytes)
            self.assertEqual(alternate_file.read_bytes(), alternate_bytes)
            self.assertEqual(self.child(root, explicit=alternate), alternate_history)

    def test_corrupt_legacy_is_rejected_without_fallback_or_history_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "legacy"
            alternate = root / "xdg/tokenoskobi/product-slice-03"
            self.child(root, "seed", legacy)
            self.child(root, "seed", alternate)
            event_file = legacy / "decision_history_v1.jsonl"
            event_file.write_bytes(event_file.read_bytes() + b"corrupt\n")
            before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
            failed = self.child(root, "WAIT", success=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("EVENT_LOG_INVALID_JSON", failed.stderr)
            self.assertEqual({path: path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)


class RequestTrustTests(unittest.TestCase):
    def headers(self, host="127.0.0.1:8096", origin=None):
        headers = Message()
        headers["Host"] = host
        headers["Content-Type"] = "application/json"
        if origin is not None:
            headers["Origin"] = origin
        return headers

    def test_host_cannot_grant_trust_to_its_own_origin(self):
        for origin in (None, "http://attacker.example"):
            with self.subTest(origin=origin), self.assertRaisesRegex(ValueError, "UNTRUSTED_HOST"):
                validate_json_headers(self.headers("attacker.example", origin), market.CFG)

    def test_origin_must_be_a_trusted_serialized_origin(self):
        for origin in ("null", "https://127.0.0.1:8096", "http://127.0.0.1:8096/path",
                       "http://127.0.0.1:8096?query", "http://127.0.0.1:8096#fragment",
                       "http://user@127.0.0.1:8096", "http://127.0.0.1:bad"):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                validate_json_headers(self.headers(origin=origin), market.CFG)

    def test_proxy_origin_is_trusted_only_by_explicit_configuration(self):
        headers = self.headers("panel.example", "https://panel.example")
        with self.assertRaises(ValueError):
            validate_json_headers(headers, market.CFG)
        config = {**market.CFG, "trusted_origins": ["https://panel.example"]}
        validate_config(config)
        validate_json_headers(headers, config)
        headers.replace_header("Origin", "http://panel.example")
        with self.assertRaises(ValueError):
            validate_json_headers(headers, config)

    def test_invalid_trusted_origin_configuration_is_rejected(self):
        for value in (None, "https://panel.example", ["null"], [True],
                      ["https://panel.example/path"], ["https://user@panel.example"],
                      ["https://panel.example:65536"], ["https://panel.example:0"]):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "CONFIG_TRUSTED_ORIGINS"):
                validate_config({**market.CFG, "trusted_origins": value})


class RequiredNewsTests(unittest.TestCase):
    def test_missing_stale_or_nonboolean_news_cannot_allow(self):
        for news in ({}, {"fresh": False}, {"fresh": None}, {"fresh": "true"}):
            values = decision_inputs()
            values[3] = news
            with self.subTest(news=news):
                result = market.decide(*values)
                self.assertNotEqual(result["decision"], "ALLOW")
                self.assertEqual(result["data_quality"], "VERI_YETERSIZ")
                self.assertIn("NEWS_STALE_OR_UNAVAILABLE", result["warnings"])

    def test_alchemy_is_optional_with_other_required_evidence(self):
        values = decision_inputs()
        values[4] = {"public_rpc_ok": 1, "hybrid_ready": False}
        self.assertEqual(market.decide(*values)["decision"], "ALLOW")

    def test_real_news_reader_and_decision_gate_for_fresh_stale_and_absent_news(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "news.sqlite"
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute("CREATE TABLE news_raw_feed_events (title TEXT, published_at_utc TEXT)")
            for age in (60, market.CFG["news_stale_sec"] + 1, None):
                with self.subTest(age=age):
                    with closing(sqlite3.connect(database)) as connection, connection:
                        connection.execute("DELETE FROM news_raw_feed_events")
                        if age is not None:
                            stamp = datetime.fromtimestamp(NOW - age, timezone.utc).isoformat()
                            connection.execute("INSERT INTO news_raw_feed_events VALUES (?, ?)", (TOKEN, stamp))
                    with patch.object(market, "ROOT", root), patch.object(market, "DBS", [database]), \
                            patch.object(market.time, "time", return_value=NOW):
                        values = decision_inputs()
                        values[3] = market.news(TOKEN, {})
                        values[4] = {"public_rpc_ok": 1, "hybrid_ready": False}
                        result = market.decide(*values)
                    self.assertEqual(result["decision"], "ALLOW" if age == 60 else "REVIEW")


if __name__ == "__main__":
    unittest.main()
