"""Regression coverage for a fresh checkout under an ordinary user account."""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]


class ProductUsabilityTests(unittest.TestCase):
    def test_mutating_requests_reject_foreign_origins_and_form_content(self):
        from services.market import tokenoskobi_product_slice_03_server as market
        for headers in (
            {"Content-Type": "text/plain"},
            {"Content-Type": "application/json", "Origin": "https://unrelated.example"},
            {"Content-Type": "application/json", "Origin": "null"},
        ):
            handler = object.__new__(market.Handler)
            handler.headers = {"Content-Length": "2", "Host": "127.0.0.1:8096", **headers}
            handler.rfile = io.BytesIO(b"{}")
            with self.subTest(headers=headers), self.assertRaises(market.ValidationError):
                handler.read_json()

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the panel JavaScript check")
    def test_served_panel_renders_missing_prices_and_blockers(self):
        from services.market import tokenoskobi_product_slice_03_server as market
        result = subprocess.run(["node", str(REPO / "engineering/tests/panel_test.js")],
                                input=market.HTML, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_check_from_another_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {k: v for k, v in os.environ.items()
                   if not k.startswith("TOKENOSKOBI_")}
            result = subprocess.run([sys.executable, "-B", str(REPO / "tokenoskobi.py"), "check"],
                                    cwd=directory, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fresh_checkout_uses_user_state_and_cache_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {k: v for k, v in os.environ.items()
                   if not k.startswith("TOKENOSKOBI_")}
            env.update(PYTHONPATH=str(REPO), XDG_STATE_HOME=directory + "/state",
                       XDG_CACHE_HOME=directory + "/cache")
            result = subprocess.run([
                sys.executable, "-B", "-c",
                "from services.market import tokenoskobi_product_slice_03_runtime as r; "
                "r.CORE.ensure_state(); r.CORE.SLICE02.geckoterminal_slot(); "
                "print(r.CORE.STATE_DIR); print(r.CORE.SLICE02.GT_RATE_DIR)",
            ], cwd=directory, env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [
                directory + "/state/tokenoskobi/product-slice-03",
                directory + "/cache/tokenoskobi",
            ])

    def test_invalid_configuration_fails_even_with_python_optimization(self):
        original = json.loads((REPO / "config/product_slice_02_v1.json").read_text())
        for change in ({"host": "0.0.0.0"}, {"port": True}, {"port": 70000},
                       {"timeout_sec": -1}, {"rpc": []},
                       {"authority": {**original["authority"], "live": True}}):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "config").mkdir()
                (root / "config/product_slice_02_v1.json").write_text(
                    json.dumps({**original, **change}))
                env = {k: v for k, v in os.environ.items()
                       if not k.startswith("TOKENOSKOBI_")}
                env.update(TOKENOSKOBI_ROOT=directory, PYTHONPATH=str(REPO))
                result = subprocess.run([
                    sys.executable, "-B", "-O", "-c",
                    "from services.market import tokenoskobi_product_slice_02_server",
                ], env=env, capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0, change)
                self.assertIn("CONFIG", result.stderr)

    def test_health_rejects_unsafe_market_configuration(self):
        path = REPO / "scripts/engineering/tokenoskobi_healthcheck.py"
        spec = importlib.util.spec_from_file_location("usability_health", path)
        health = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(health)
        unsafe = json.loads((REPO / "config/product_slice_02_v1.json").read_text())
        unsafe["authority"]["live"] = True
        original = Path.read_text

        def read(path, *args, **kwargs):
            if path == REPO / "config/product_slice_02_v1.json":
                return json.dumps(unsafe)
            return original(path, *args, **kwargs)

        with patch.object(Path, "read_text", read):
            checks = health.health_checks(REPO)
        self.assertFalse(checks["Market Configuration"]["status"])

    def test_slice02_bad_json_is_a_client_error(self):
        from services.market import tokenoskobi_product_slice_02_server as market
        for payload in (b"[]", b"null", b'{"token_address": 2}', b"{", b"\xff"):
            with self.subTest(payload=payload):
                handler = object.__new__(market.H)
                handler.path = "/api/v1/analyze"
                handler.headers = {"Content-Length": str(len(payload)),
                                   "Content-Type": "application/json"}
                handler.rfile = io.BytesIO(payload)
                replies = []
                handler.sendj = lambda code, body: replies.append((code, body))
                handler.do_POST()
                self.assertEqual(replies[0][0], 400, replies)


if __name__ == "__main__":
    unittest.main()
