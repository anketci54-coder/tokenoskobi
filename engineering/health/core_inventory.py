#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()

KEYWORDS = (
    "kernel",
    "product_slice",
    "panel",
    "ledger",
    "runtime",
    "evidence",
    "news",
)

print("=" * 70)
print("TOKENOSKOBI CORE INVENTORY")
print("=" * 70)

count = 0

for path in ROOT.rglob("*.py"):
    name = path.name.lower()

    if any(word in name for word in KEYWORDS):
        count += 1
        print(path.relative_to(ROOT))

print("=" * 70)
print(f"TOTAL CORE FILES : {count}")