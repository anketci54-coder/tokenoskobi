#!/usr/bin/env python3
import json, sys
from pathlib import Path

required={
 "PROJECT_BOOT.json":["boot_version","project","source_of_truth","hard_rules"],
 "PROJECT_RUNTIME.json":["runtime_version","updated_at","git","current_state","last_action","next_safe_step"],
 "PROJECT_HISTORY.json":["history_version","events"]
}

ok=True
for f,keys in required.items():
    p=Path(f)
    if not p.exists():
        print(f"BOOT_SCHEMA=FAIL {f} missing"); ok=False; continue
    d=json.loads(p.read_text(encoding="utf-8"))
    for k in keys:
        if k not in d:
            print(f"BOOT_SCHEMA=FAIL {f}.{k} missing"); ok=False

print("BOOT_SCHEMA=PASS" if ok else "BOOT_SCHEMA=FAIL")
sys.exit(0 if ok else 1)
