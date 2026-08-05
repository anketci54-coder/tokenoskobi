#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.getenv("TOKENOSKOBI_ROOT", Path.cwd()))

results = {}


def check(title: str, ok: bool, detail: str = ""):
    results[title] = {
        "status": ok,
        "detail": detail,
    }

    icon = "PASS" if ok else "FAIL"
    print(f"{title:<30} {icon}")

    if detail:
        print(f"    {detail}")


print("=" * 70)
print("TOKENOSKOBI ENGINEERING HEALTH CHECK")
print("=" * 70)

# Python
check(
    "Python Version",
    sys.version_info >= (3, 10),
    platform.python_version(),
)

# Platform
check(
    "Operating System",
    True,
    platform.system(),
)

# Root
check(
    "TOKENOSKOBI_ROOT",
    ROOT.exists(),
    str(ROOT),
)

# Git
try:
    subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check("Git Repository", True)
except Exception:
    check("Git Repository", False)

# Kernel
kernel = ROOT / "tokenoskobi_kernel.py"
check(
    "Kernel File",
    kernel.exists(),
    str(kernel),
)

# Slice02
slice02 = ROOT / "tools" / "tokenoskobi_product_slice_02_server.py"
check(
    "Slice02",
    slice02.exists(),
)

# Slice03
slice03 = ROOT / "tools" / "tokenoskobi_product_slice_03_server.py"
check(
    "Slice03",
    slice03.exists(),
)

# POSIX File Lock
try:
    import fcntl  # Linux / macOS

    check("POSIX File Lock", True)
except Exception:
    check(
        "POSIX File Lock",
        False,
        "Windows ortamında normaldir.",
    )

print("=" * 70)

# ------------------------------------------------------------------
# JSON REPORT
# ------------------------------------------------------------------

report_dir = ROOT / "engineering" / "reports"
report_dir.mkdir(parents=True, exist_ok=True)

report = {
    "tool": "TOKENOSKOBI_ENGINEERING_HEALTH_CHECK",
    "version": 1,
    "checks": results,
}

with open(
    report_dir / "health.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        report,
        f,
        indent=4,
        ensure_ascii=False,
    )

print()
print("Report written:")
print(report_dir / "health.json")