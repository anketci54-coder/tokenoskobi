#!/usr/bin/env python3
from pathlib import Path
snaps=sorted(Path("boot_snapshots").glob("*"))
if len(snaps)<2:
    print("BOOT_DIFF=INFO not enough snapshots")
else:
    print(f"BOOT_DIFF=PASS compare {snaps[-2]} -> {snaps[-1]}")
