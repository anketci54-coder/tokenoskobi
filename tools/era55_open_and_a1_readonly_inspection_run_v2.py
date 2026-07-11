#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
TOOL = ROOT / "tools/era55_open_and_a1_readonly_inspection_v1.py"
FORCE_ADD = {"reports/LATEST_ERA55A1_READONLY_INSPECTION.md"}


def run(cmd: list[str], *, check: bool = True, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            "COMMAND_FAILED=" + json.dumps(
                {
                    "cmd": cmd,
                    "rc": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                },
                ensure_ascii=False,
            )
        )
    return completed


def lines(cmd: list[str]) -> list[str]:
    return [
        line
        for line in run(cmd).stdout.splitlines()
        if line.strip()
    ]


def load_module() -> Any:
    if not TOOL.is_file():
        raise RuntimeError(f"TOOL_MISSING={TOOL}")
    spec = importlib.util.spec_from_file_location(
        "era55_open_and_a1_readonly_inspection_v1",
        TOOL,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("TOOL_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    original_sqlite_inspection = module.sqlite_inspection

    def strict_sqlite_inspection() -> dict[str, Any]:
        result = original_sqlite_inspection()
        if result.get("exists") is not True:
            raise RuntimeError("SQLITE_DB_NOT_FOUND")
        if result.get("integrity_check") != "ok":
            raise RuntimeError(
                "SQLITE_INTEGRITY_NOT_OK="
                + str(result.get("integrity_check"))
            )
        if result.get("quick_check") != "ok":
            raise RuntimeError(
                "SQLITE_QUICK_CHECK_NOT_OK="
                + str(result.get("quick_check"))
            )
        if result.get("total_changes") != 0:
            raise RuntimeError(
                "SQLITE_READONLY_TOTAL_CHANGES_NOT_ZERO="
                + str(result.get("total_changes"))
            )
        return result

    def fixed_commit_and_push(
        expected_files: list[str],
    ) -> tuple[str, str]:
        expected = sorted(set(expected_files))

        for rel in expected:
            if not (ROOT / rel).is_file():
                raise RuntimeError(f"EXPECTED_FILE_MISSING={rel}")

        tracked_changed = set(
            lines(["git", "diff", "--name-only"])
        )
        untracked_visible = set(
            lines(
                [
                    "git",
                    "ls-files",
                    "--others",
                    "--exclude-standard",
                ]
            )
        )
        visible_actual = tracked_changed | untracked_visible
        visible_expected = set(expected) - FORCE_ADD

        if visible_actual != visible_expected:
            raise RuntimeError(
                "UNEXPECTED_VISIBLE_CHANGED_FILES\n"
                + "EXPECTED="
                + json.dumps(sorted(visible_expected), ensure_ascii=False)
                + "\nACTUAL="
                + json.dumps(sorted(visible_actual), ensure_ascii=False)
            )

        run(["git", "diff", "--check"])

        normal_add = sorted(set(expected) - FORCE_ADD)
        if normal_add:
            run(["git", "add", "--", *normal_add])

        forced = sorted(set(expected) & FORCE_ADD)
        if forced:
            run(["git", "add", "-f", "--", *forced])

        staged = sorted(
            lines(["git", "diff", "--cached", "--name-only"])
        )
        if staged != expected:
            raise RuntimeError(
                "STAGED_FILES_MISMATCH\n"
                + "EXPECTED="
                + json.dumps(expected, ensure_ascii=False)
                + "\nACTUAL="
                + json.dumps(staged, ensure_ascii=False)
            )

        run(
            [
                "git",
                "commit",
                "-m",
                "ERA55_OPEN_A1_READONLY_INSPECTION | OK | NO_LIVE_MUTATION",
            ]
        )

        local_head = run(
            ["git", "rev-parse", "HEAD"]
        ).stdout.strip()

        run(["git", "push", "origin", "main"], timeout=240)
        run(["git", "fetch", "origin", "main"])

        remote_head = run(
            ["git", "rev-parse", "origin/main"]
        ).stdout.strip()

        if local_head != remote_head:
            raise RuntimeError(
                f"POST_PUSH_HEAD_MISMATCH:LOCAL={local_head}:REMOTE={remote_head}"
            )

        status = run(
            ["git", "status", "--porcelain"]
        ).stdout.strip()
        if status:
            raise RuntimeError("POST_PUSH_WORKTREE_NOT_CLEAN\n" + status)

        return local_head, remote_head

    module.sqlite_inspection = strict_sqlite_inspection
    module.commit_and_push = fixed_commit_and_push
    return int(module.main())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"ERA55A1_RUNNER_V2=FAILED:{exc}",
            file=sys.stderr,
        )
        raise
