#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path.cwd()

PREFIXES = (
    "core",
    "services",
    "tools",
    "engineering",
)

graph = {}

for file in sorted(ROOT.rglob("*.py")):

    try:
        tree = ast.parse(
            file.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        )
    except Exception:
        continue

    imports = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:

                top = alias.name.split(".")[0]

                if top in PREFIXES:
                    imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):

            if node.module:

                top = node.module.split(".")[0]

                if top in PREFIXES:
                    imports.append(node.module)

    graph[str(file.relative_to(ROOT))] = sorted(set(imports))

report_dir = ROOT / "engineering" / "reports"
report_dir.mkdir(parents=True, exist_ok=True)

report = report_dir / "internal_dependency_graph.json"

with open(
    report,
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        graph,
        f,
        indent=4,
        ensure_ascii=False,
    )

print("=" * 72)
print("TOKENOSKOBI INTERNAL DEPENDENCY GRAPH")
print("=" * 72)
print()
print(f"Python files analyzed : {len(graph)}")
print()
print("Report written:")
print(report)