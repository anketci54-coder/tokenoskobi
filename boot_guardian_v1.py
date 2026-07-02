#!/usr/bin/env python3
import json, sys
from pathlib import Path

rt=json.loads(Path("PROJECT_RUNTIME.json").read_text(encoding="utf-8"))
wu=rt.get("current_state",{}).get("active_work_unit",{})
status=wu.get("status")
nexts=wu.get("next_step")

SEALED_STATUSES={
    "GITHUB_SEALED",
    "GITHUB_SEALED_HEALTH_100"
}

if not wu:
    print("BOOT_GUARDIAN=FAIL active_work_unit missing")
    sys.exit(1)

if status not in SEALED_STATUSES and nexts == "NEXT_WORK_UNIT_PLAN":
    print("BOOT_GUARDIAN=FAIL unsealed work unit cannot open next work unit")
    sys.exit(1)

print("BOOT_GUARDIAN=PASS")
