import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HEALTH = REPO / "scripts/engineering/tokenoskobi_healthcheck.py"


def clean_environment():
    env = dict(os.environ)
    for key in list(env):
        if key.startswith("TOKENOSKOBI_"):
            del env[key]
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(REPO)
    return env


class RepositoryEntrypointTests(unittest.TestCase):
    def test_failed_health_checks_return_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            env = clean_environment()
            env["TOKENOSKOBI_ROOT"] = directory
            result = subprocess.run([sys.executable, "-B", str(HEALTH)],
                                    cwd=directory, env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_health_uses_repository_location_and_current_services(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "health.json"
            result = subprocess.run(
                [sys.executable, "-B", str(HEALTH), "--report", str(report)],
                cwd=directory, env=clean_environment(), capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            checks = json.loads(report.read_text())["checks"]
            self.assertTrue(all(item["status"] for item in checks.values()), checks)

    def test_runtime_imports_without_path_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            env = clean_environment()
            env["TOKENOSKOBI_SLICE03_STATE_DIR"] = str(Path(directory) / "state")
            result = subprocess.run([
                sys.executable, "-B", "-c",
                "from services.market import tokenoskobi_product_slice_03_runtime as r; "
                "assert r.CORE.SLICE02.CFG['authority']['live'] is False; "
                "assert r.CORE.ROOT == r.ROOT; print(r.ROOT)",
            ], cwd=directory, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), str(REPO))


if __name__ == "__main__":
    unittest.main()
