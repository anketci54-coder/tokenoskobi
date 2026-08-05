#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TOOLS = [
    "repository_validator.py",
    "repository_inventory.py",
    "repository_intelligence.py",
    "dependency_graph.py",
    "internal_dependency_graph.py",
    "dead_code_detector.py",
]


def run_all():

    print("=" * 72)
    print("TOKENOSKOBI ENGINEERING ENGINE")
    print("=" * 72)

    health_dir = ROOT / "engineering" / "health"

    for tool in TOOLS:

        print()
        print(f">>> {tool}")

        result = subprocess.run(
            [sys.executable, str(health_dir / tool)],
            cwd=ROOT,
        )

        if result.returncode == 0:
            print("[PASS]")
        else:
            print("[FAIL]")

    print()
    print("=" * 72)
    print("ENGINE FINISHED")
    print("=" * 72)


if __name__ == "__main__":
    run_all()