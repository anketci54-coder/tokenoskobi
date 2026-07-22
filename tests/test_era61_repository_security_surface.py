#!/usr/bin/env python3
"""Repository-wide ERA61 security surface regression audit.

This test scans active Python implementation surfaces only. Historical archives,
documentation and generated evidence are excluded because they are not executable
runtime sources.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIRS = (ROOT / "core", ROOT / "tools")
EXCLUDED_PARTS = {"archive", "__pycache__"}

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

FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "os.system",
    "os.popen",
}

FAIL_OPEN_MARKERS = {
    "proceeding without authority check",
    "authority_warn",
    "warn-and-continue",
}


def active_python_files():
    for base in ACTIVE_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts):
                continue
            yield path


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def test_no_shell_true_or_dynamic_execution():
    findings = []
    for path in active_python_files():
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = dotted_name(node.func)
            if name in FORBIDDEN_CALLS:
                findings.append(f"{path.relative_to(ROOT)}:{node.lineno}:{name}")
            if name in {"subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_call", "subprocess.check_output"}:
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        findings.append(f"{path.relative_to(ROOT)}:{node.lineno}:shell=True")
    assert not findings, "Forbidden dynamic execution surfaces:\n" + "\n".join(findings)


def test_no_authority_fail_open_markers():
    findings = []
    for path in active_python_files():
        lowered = path.read_text(encoding="utf-8").lower()
        for marker in FAIL_OPEN_MARKERS:
            if marker in lowered:
                findings.append(f"{path.relative_to(ROOT)}:{marker}")
    assert not findings, "Authority fail-open markers found:\n" + "\n".join(findings)


def test_no_direct_financial_execution_calls():
    findings = []
    for path in active_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = dotted_name(node.func)
            leaf = name.rsplit(".", 1)[-1]
            if leaf in FINANCIAL_CALL_NAMES:
                findings.append(f"{path.relative_to(ROOT)}:{node.lineno}:{name}")
    assert not findings, "Direct financial execution calls found:\n" + "\n".join(findings)


def test_research_execution_firewall_has_empty_execution_allowlist():
    from core import research_execution_firewall as firewall

    assert firewall.TRUSTED_EXECUTION_SCHEMAS == frozenset()
    result = firewall.validate_execution_input({"schema": "era57_research_report_v1"})
    assert result["decision"] == "DENY"
    assert "RESEARCH_SCHEMA_EXECUTION_HARD_REJECT" in result["reason_codes"]
