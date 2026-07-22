#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.runtime_policy_authority_gate import evaluate_runtime_stage


class Era61RuntimeGateAdversarialTests(unittest.TestCase):
    def test_read_only_stage_remains_available(self):
        result = evaluate_runtime_stage(
            "SOURCE_CONTRACT_RESOLUTION",
            root=ROOT,
            environ={},
        )
        self.assertEqual("ALLOW", result["decision"], result)
        self.assertTrue(result["fail_closed"])

    def test_unknown_stage_denied(self):
        result = evaluate_runtime_stage(
            "UNKNOWN_STAGE",
            root=ROOT,
            environ={},
        )
        self.assertEqual("DENY", result["decision"], result)
        self.assertIn("RUNTIME_STAGE_NOT_GRANTED", result["reason_codes"])

    def test_mutating_stages_remain_denied_without_authority(self):
        env = {
            "TOKENOSKOBI_LEDGER_WRITER_ENABLED": "1",
            "TOKENOSKOBI_RUNNER_LOCK_ENABLED": "1",
            "TOKENOSKOBI_A23_GUARDED_PRODUCTION": "1",
            "TOKENOSKOBI_NEWS_HOT_PATH": str(
                ROOT
                / "tools"
                / "era55a23_p0_guarded_general_production_writer_runtime_integration_apply_and_post_audit_v1.py"
            ),
        }
        for stage in ("LEDGER_RECOVERY", "DERIVED_DB_WRITE", "HOT_PUBLISH"):
            with self.subTest(stage=stage):
                result = evaluate_runtime_stage(stage, root=ROOT, environ=env)
                self.assertEqual("DENY", result["decision"], result)
                self.assertTrue(result["fail_closed"])
                self.assertEqual("DENY", result["baseline_authority"]["decision"])

    def test_path_override_outside_repository_denied(self):
        result = evaluate_runtime_stage(
            "SOURCE_CONTRACT_RESOLUTION",
            root=ROOT,
            runner_path="../../tmp/escape.py",
            environ={},
        )
        self.assertEqual("DENY", result["decision"], result)
        self.assertTrue(
            any("RUNNER" in code or "IDENTITY" in code for code in result["reason_codes"]),
            result,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
