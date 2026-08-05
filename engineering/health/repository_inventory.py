#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path.cwd()

GROUPS = {
    "CORE": [],
    "PRODUCT": [],
    "ENGINEERING": [],
    "TEST": [],
    "OTHER": [],
}

for file in sorted(ROOT.rglob("*.py")):

    text = str(file.relative_to(ROOT)).replace("\\", "/")

    # Archive tamamen yok sayılır
    if text.startswith("archive/"):
        continue

    if text.startswith("core/"):
        GROUPS["CORE"].append(text)

    elif "tokenoskobi_product_slice" in text:
        GROUPS["PRODUCT"].append(text)

    elif text.startswith("engineering/"):
        GROUPS["ENGINEERING"].append(text)

    elif text.startswith("tests/"):
        GROUPS["TEST"].append(text)

    else:
        GROUPS["OTHER"].append(text)

print("=" * 70)
print("TOKENOSKOBI REPOSITORY INVENTORY")
print("=" * 70)

for group, files in GROUPS.items():

    print()
    print(group)
    print("-" * 40)
    print(f"{len(files)} files")

    for name in sorted(files)[:15]:
        print(name)

    if len(files) > 15:
        print("...")

report_dir = ROOT / "engineering" / "reports"
report_dir.mkdir(parents=True, exist_ok=True)

report = {
    "groups": {
        group: len(files)
        for group, files in GROUPS.items()
    },
    "files": GROUPS,
}

with open(
    report_dir / "repository_inventory.json",
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
print(report_dir / "repository_inventory.json")