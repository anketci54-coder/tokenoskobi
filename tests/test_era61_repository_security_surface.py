#!/usr/bin/env python3
"""ERA61 active authority-boundary regression audit.

The repository contains historical and one-shot operational tools with known
legacy execution surfaces. This blocking gate deliberately covers the active
security boundary changed by ERA61. Repository-wide legacy findings remain
post-audit debt and are not silently reclassified as new ERA61 regressions.
"""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SECURITY_CRITICAL_FILES = (
    ROOT / "core" / "authority.py",
    ROOT / "core" / "runtime_policy_authority_gate.py",
    ROOT / "core" / "research_execution_firewall.py",
    ROOT / "tools" / "system_center_live_producer_v1.py",
)

FINANCIAL_CALL_NAMES = {
    "sign_transaction",
    "send_raw_transaction",
    "send_transaction",
    "create_order",
    "execute_order",
    "place_order",
    "cancel_order",
    "replace_order",
    "swap_exact_tokens_for_tokens",
    "swap_exact_eth_for_tokens",
    "swap_exact_tokens_for_eth",
    "broadcast_transaction",
}

FORBIDDEN_CALLS = {"eval", "exec", "os.system", "os.popen"}
FAIL_OPEN_MARKERS = {
    "proceeding without authority check",
    "authority_warn",
    "warn-and-continue",
}


def security_critical_python_files():
    missing = [path for path in SECURITY_CRITICAL_FILES if not path.is_file()]
    if missing:
        raise AssertionError(
            "Missing security-critical files: "
            + ", ".join(str(path.relative_to(ROOT)) for path in missing)
        )
    yield from SECURITY_CRITICAL_FILES


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


class Era61RepositorySecuritySurfaceTests(unittest.TestCase):
    def test_no_shell_true_or_dynamic_execution(self):
        findings = []
        for path in security_critical_python_files():
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = dotted_name(node.func)
                if name in FORBIDDEN_CALLS:
                    findings.append(f"{path.relative_to(ROOT)}:{node.lineno}:{name}")
                if name in {
                    "subprocess.run",
                    "subprocess.Popen",
                    "subprocess.call",
                    "subprocess.check_call",
                    "subprocess.check_output",
                }:
                    for kw in node.keywords:
                        if (
                            kw.arg == "shell"
                            and isinstance(kw.value, ast.Constant)
                            and kw.value.value is True
                        ):
                            findings.append(
                                f"{path.relative_to(ROOT)}:{node.lineno}:shell=True"
                            )
        self.assertFalse(
            findings,
            "Forbidden dynamic execution surfaces:\n" + "\n".join(findings),
        )

    def test_no_authority_fail_open_markers(self):
        findings = []
        for path in security_critical_python_files():
            lowered = path.read_text(encoding="utf-8").lower()
            for marker in FAIL_OPEN_MARKERS:
                if marker in lowered:
                    findings.append(f"{path.relative_to(ROOT)}:{marker}")
        self.assertFalse(
            findings,
            "Authority fail-open markers found:\n" + "\n".join(findings),
        )

    def test_no_direct_financial_execution_calls(self):
        findings = []
        for path in security_critical_python_files():
            tree = ast.parse(
                path.read_text(encoding="utf-8"), filename=str(path)
            )
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = dotted_name(node.func)
                leaf = name.rsplit(".", 1)[-1]
                if leaf in FINANCIAL_CALL_NAMES:
                    findings.append(f"{path.relative_to(ROOT)}:{node.lineno}:{name}")
        self.assertFalse(
            findings,
            "Direct financial execution calls found:\n" + "\n".join(findings),
        )

    def test_research_execution_firewall_has_empty_execution_allowlist(self):
        from core import research_execution_firewall as firewall

        self.assertEqual(frozenset(), firewall.TRUSTED_EXECUTION_SCHEMAS)
        result = firewall.validate_execution_input(
            {"schema": "era57_research_report_v1"}
        )
        self.assertEqual("DENY", result["decision"])
        self.assertIn(
            "RESEARCH_SCHEMA_EXECUTION_HARD_REJECT", result["reason_codes"]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
