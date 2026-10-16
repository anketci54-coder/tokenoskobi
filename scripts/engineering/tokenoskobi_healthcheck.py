#!/usr/bin/env python3
"""Check a checkout without network access or starting application services."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def health_checks(root: Path) -> dict:
    results = {}

    def check(title: str, ok: bool, detail: str = "") -> None:
        results[title] = {"status": bool(ok), "detail": detail}

    check("Python Version", sys.version_info >= (3, 11), platform.python_version())
    check("TOKENOSKOBI_ROOT", root.is_dir(), str(root))
    try:
        git = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        check("Git Repository", git.returncode == 0 and Path(git.stdout.strip()).resolve() == root)
    except OSError as exc:
        check("Git Repository", False, str(exc))
    required = {
        "Kernel File": "tokenoskobi_kernel.py",
        "Slice02": "services/market/tokenoskobi_product_slice_02_server.py",
        "Slice03": "services/market/tokenoskobi_product_slice_03_server.py",
        "Slice03 Runtime": "services/market/tokenoskobi_product_slice_03_runtime.py",
        "Market Configuration": "config/product_slice_02_v1.json",
        "Runtime State": "PROJECT_RUNTIME.json",
    }
    for title, relative in required.items():
        check(title, (root / relative).is_file(), relative)
    for title, relative in (("Market Configuration", "config/product_slice_02_v1.json"),
                            ("Runtime State", "PROJECT_RUNTIME.json")):
        try:
            value = json.loads((root / relative).read_text(encoding="utf-8-sig"))
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
        except (OSError, ValueError) as exc:
            check(title, False, str(exc))
    check("POSIX File Lock", importlib.util.find_spec("fcntl") is not None,
          "Market services require POSIX file locking.")
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=Path(os.getenv("TOKENOSKOBI_ROOT", REPOSITORY_ROOT)))
    parser.add_argument("--report", type=Path, help="Optional JSON report destination")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    checks = health_checks(root)
    report = {"tool": "TOKENOSKOBI_ENGINEERING_HEALTH_CHECK", "version": 2,
              "ok": all(item["status"] for item in checks.values()), "checks": checks}
    for title, result in checks.items():
        print(f"{title:<30} {'PASS' if result['status'] else 'FAIL'}")
        if result["detail"]:
            print(f"    {result['detail']}")
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(f"Report written: {args.report}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
