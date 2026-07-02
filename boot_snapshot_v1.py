#!/usr/bin/env python3
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

ts=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
out=Path("boot_snapshots")/ts
out.mkdir(parents=True,exist_ok=True)

for f in ["PROJECT_BOOT.json","PROJECT_RUNTIME.json","PROJECT_HISTORY.json"]:
    shutil.copy2(f,out/f)

print(f"BOOT_SNAPSHOT=PASS {out}")
