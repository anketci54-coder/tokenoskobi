#!/usr/bin/env python3
import json, sys
from pathlib import Path

rt=json.loads(Path("PROJECT_RUNTIME.json").read_text(encoding="utf-8"))
wu=rt.get("current_state",{}).get("active_work_unit",{})
status=wu.get("status")
last=wu.get("last_completed_step")
nexts=wu.get("next_step")

if not wu:
    print("BOOT_GUARDIAN=FAIL active_work_unit missing"); sys.exit(1)

if status != "GITHUB_SEALED" and nexts == "NEXT_WORK_UNIT_PLAN":
    print("BOOT_GUARDIAN=FAIL unsealed work unit cannot open next work unit"); sys.exit(1)

print("BOOT_GUARDIAN=PASS")
