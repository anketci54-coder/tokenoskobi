#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.cwd()

report = ROOT / "engineering" / "reports" / "internal_dependency_graph.json"

if not report.exists():
    raise SystemExit("Run internal_dependency_graph.py first.")

graph = json.loads(report.read_text(encoding="utf-8"))

imports = set()

for modules in graph.values():
    for module in modules:
        imports.add(module)

dead = []

for file in sorted(graph):

    module = (
        file.replace("\\", ".")
            .replace("/", ".")
            .replace(".py", "")
    )

    if module.endswith("__init__"):
        continue

    if module not in imports:
        dead.append(file)

out = {
    "candidate_count": len(dead),
    "candidates": dead,
}

report_dir = ROOT / "engineering" / "reports"

output = report_dir / "dead_code_candidates.json"

output.write_text(
    json.dumps(
        out,
        indent=4,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)

print("=" * 72)
print("TOKENOSKOBI DEAD CODE DETECTOR")
print("=" * 72)
print()
print(f"Candidates : {len(dead)}")
print()
print("Report written:")
print(output)