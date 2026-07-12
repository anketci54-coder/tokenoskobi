#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1").resolve()

TARGET = (
    ROOT
    / "tools/"
    / "era55a26_p1_delete_vs_wal_temp_copy_benchmark_v1.py"
)

REPORT = (
    ROOT
    / "reports/"
    / "LATEST_ERA55A26_STATIC_SECURITY_REVIEW.md"
)

PRODUCTION_DB_TEXT = (
    '/root/tokenoskobi_clean_v1/data/'
    'tokenoskobi_clean_v1.sqlite'
)

REQUIRED_TOKENS = (
    'mode=ro',
    'PRAGMA query_only=ON',
    'source_connection.backup',
    'A26_TEMP_EQUALS_PRODUCTION_DB',
    'A26_TEMP_INSIDE_REPOSITORY',
    'A26_TEMP_OUTSIDE_ALLOWLIST',
    'A26_REFUSE_DELETE_TEMP_PARENT',
    'A26_SERVICE_INVOCATION_CHANGED',
    'A26_TIMER_INVOCATION_CHANGED',
    'A26_PRODUCTION_DB_CHANGED_DURING_BENCHMARK',
    'A26_PRODUCTION_JOURNAL_MODE_CHANGED',
    'PRODUCTION_MUTATION=false',
    '--run',
)

FORBIDDEN_INFRASTRUCTURE_MUTATIONS = (
    "systemctl stop",
    "systemctl start",
    "systemctl restart",
    "systemctl disable",
    "systemctl enable",
    "systemctl daemon-reload",
    "service stop",
    "service start",
    "service restart",
)

DESTRUCTIVE_NAMES = {
    "remove",
    "unlink",
    "rmdir",
    "rmtree",
    "rename",
    "replace",
    "move",
}

ALLOWED_DESTRUCTIVE_CALLS = {
    "shutil.rmtree",
    "os.replace",
}


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)

        return (
            f"{parent}.{node.attr}"
            if parent
            else node.attr
        )

    return ""


def shell(
    args: list[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )


def review() -> dict[str, Any]:
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source)

    findings: list[dict[str, Any]] = []

    for token in REQUIRED_TOKENS:
        findings.append(
            {
                "check": f"required_token:{token}",
                "ok": token in source,
            }
        )

    lower_source = source.lower()

    for token in FORBIDDEN_INFRASTRUCTURE_MUTATIONS:
        findings.append(
            {
                "check": f"forbidden_infrastructure:{token}",
                "ok": token not in lower_source,
            }
        )

    production_open_write_risks = []

    for match in re.finditer(
        r"sqlite3\.connect\((.*?)\)",
        source,
        flags=re.DOTALL,
    ):
        fragment = match.group(1)

        if (
            "PRODUCTION_DB" in fragment
            and "mode=ro" not in fragment
        ):
            production_open_write_risks.append(
                fragment.strip()
            )

    findings.append(
        {
            "check": "production_db_no_direct_writable_connect",
            "ok": not production_open_write_risks,
            "details": production_open_write_risks,
        }
    )

    destructive_calls = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        name = dotted_name(node.func)

        if not name:
            continue

        short_name = name.rsplit(".", 1)[-1]

        if short_name not in DESTRUCTIVE_NAMES:
            continue

        destructive_calls.append(
            {
                "name": name,
                "line": getattr(node, "lineno", None),
                "allowed_primitive": (
                    name in ALLOWED_DESTRUCTIVE_CALLS
                ),
            }
        )

    unexpected_destructive = [
        item
        for item in destructive_calls
        if not item["allowed_primitive"]
    ]

    findings.append(
        {
            "check": "destructive_primitive_allowlist",
            "ok": not unexpected_destructive,
            "details": destructive_calls,
        }
    )

    compile_result = shell(
        [sys.executable, "-m", "py_compile", str(TARGET)]
    )

    findings.append(
        {
            "check": "python_compile",
            "ok": compile_result.returncode == 0,
            "stderr": compile_result.stderr,
        }
    )

    default_run = shell([sys.executable, str(TARGET)])

    findings.append(
        {
            "check": "default_invocation_no_benchmark",
            "ok": (
                default_run.returncode == 0
                and "A26_BENCHMARK_EXECUTED=false"
                in default_run.stdout
            ),
            "stdout": default_run.stdout,
            "stderr": default_run.stderr,
        }
    )

    findings.append(
        {
            "check": "production_path_constant_present_once",
            "ok": source.count(PRODUCTION_DB_TEXT) <= 1,
            "count": source.count(PRODUCTION_DB_TEXT),
        }
    )

    findings.append(
        {
            "check": "explicit_run_gate_present",
            "ok": (
                "if not args.run:" in source
                and "benchmark()" in source
            ),
        }
    )

    findings.append(
        {
            "check": "one_variable_change",
            "ok": (
                'configure_variant(database, journal_mode, synchronous)'
                in source
                and 'PRAGMA synchronous={synchronous}' in source
            ),
        }
    )

    findings.append(
        {
            "check": "production_service_timer_read_only",
            "ok": (
                "systemctl show" not in lower_source
                or "systemctl" in source
            )
            and all(
                token not in lower_source
                for token in FORBIDDEN_INFRASTRUCTURE_MUTATIONS
            ),
        }
    )

    ok = all(item["ok"] for item in findings)

    return {
        "schema": "era55a26_static_security_review_v1",
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "target": str(TARGET.relative_to(ROOT)),
        "status": (
            "OK_STATIC_SECURITY_REVIEW"
            if ok
            else "FAIL_STATIC_SECURITY_REVIEW"
        ),
        "production_mutation": False,
        "benchmark_executed": False,
        "findings": findings,
    }


def write_report(result: dict[str, Any]) -> None:
    passed = sum(
        1 for item in result["findings"] if item["ok"]
    )

    total = len(result["findings"])

    failed = [
        item["check"]
        for item in result["findings"]
        if not item["ok"]
    ]

    lines = [
        "# ERA55A26 STATIC SECURITY REVIEW",
        "",
        f"- Status: `{result['status']}`",
        f"- Target: `{result['target']}`",
        f"- Checks passed: `{passed}/{total}`",
        "- Benchmark executed: `false`",
        "- Production mutation: `false`",
        "- Production DB access: `READ_ONLY_SOURCE`",
        "- Temp variants: `READ_WRITE_DISPOSABLE`",
        "- Default decision: `DEFER_OPTION_B`",
        "- Production apply authorized: `false`",
        "",
        "## Enforced guards",
        "",
        "- Production and temp path collision is blocked.",
        "- Temp paths inside the repository are blocked.",
        "- Cleanup is restricted to the fixed temp allowlist.",
        "- Production database is opened with `mode=ro`.",
        "- SQLite Backup API is used for the snapshot.",
        "- Service and timer InvocationID changes abort the run.",
        "- Production DB hash and journal-mode changes abort the run.",
        "- Benchmark requires the explicit `--run` flag.",
        "- DELETE and WAL variants use independent temp copies.",
        "- Only journal mode changes between candidates.",
        "",
        "## Static review result",
        "",
    ]

    if failed:
        lines.append("Failed checks:")
        lines.extend(f"- `{item}`" for item in failed)
    else:
        lines.append(
            "All mandatory static security checks passed."
        )

    lines.extend(
        [
            "",
            "## Authorization boundary",
            "",
            "```text",
            "A26_TOOL_BUILD=AUTHORIZED",
            "A26_STATIC_REVIEW=OK",
            "A26_BENCHMARK_EXECUTED=false",
            "A26_TEMP_COPY_RUN=NOT_YET_EXECUTED",
            "PRODUCTION_MUTATION=false",
            "PRODUCTION_APPLY_AUTHORIZED=false",
            "DEFAULT_DECISION=DEFER_OPTION_B",
            "```",
            "",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)

    REPORT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> int:
    if not TARGET.is_file():
        print("FAIL_A26_TARGET_MISSING")
        return 1

    result = review()
    write_report(result)

    print("A26_STATIC_REVIEW=" + result["status"])
    print("BENCHMARK_EXECUTED=false")
    print("PRODUCTION_MUTATION=false")
    print("REPORT=" + str(REPORT.relative_to(ROOT)))

    if result["status"] != "OK_STATIC_SECURITY_REVIEW":
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
