#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path.cwd()

graph = {}

for file in sorted(ROOT.rglob("*.py")):
    try:
        source = file.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        tree = ast.parse(source)

    except Exception:
        continue

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    graph[str(file.relative_to(ROOT))] = sorted(set(imports))

report_dir = ROOT / "engineering" / "reports"
report_dir.mkdir(parents=True, exist_ok=True)

report = report_dir / "dependency_graph.json"

with open(report, "w", encoding="utf-8") as f:
    json.dump(
        graph,
        f,
        indent=4,
        ensure_ascii=False,
    )

print("=" * 72)
print("TOKENOSKOBI DEPENDENCY GRAPH")
print("=" * 72)
print(f"Python files analyzed : {len(graph)}")
print()
print("Report written:")
print(report)