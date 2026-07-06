#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

RUNTIME = Path("PROJECT_RUNTIME.json")

if not RUNTIME.exists():
    raise SystemExit("PROJECT_RUNTIME.json not found")

with open(RUNTIME, encoding="utf-8") as f:
    rt = json.load(f)

def git(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()

now = datetime.now(timezone.utc).isoformat()

head = git("git rev-parse HEAD")
branch = git("git branch --show-current")
status = git("git status --short")

rt["updated_at"] = now

rt["git"] = {
    "branch": branch,
    "head": head,
    "status_clean": status == "",
    "status_summary": status if status else "CLEAN"
}

wu = rt.setdefault("current_state", {}).setdefault("active_work_unit", {})

wu.setdefault("id", "UNKNOWN")
wu.setdefault("type", "UNKNOWN")
wu.setdefault("status", "UNKNOWN")
wu.setdefault("last_completed_step", "UNKNOWN")
wu.setdefault("next_step", "UNKNOWN")

rt["last_action"] = {
    "timestamp": now,
    "task": "BOOT_AUTOSYNC_V1 runtime synchronization",
    "result": "PASS_LOCAL_AUTOSYNC",
    "git_head": head
}

if "next_safe_step" not in rt:
    rt["next_safe_step"] = {
        "name": "USER_DECISION_REQUIRED",
        "status": "WAITING",
        "instruction": "User approval required before continuing."
    }

with open(RUNTIME, "w", encoding="utf-8") as f:
    json.dump(rt, f, indent=2, ensure_ascii=False)

print("=" * 70)
print("BOOT AUTOSYNC V1")
print("=" * 70)
print(f"HEAD        : {head}")
print(f"BRANCH      : {branch}")
print(f"UPDATED_AT  : {now}")
print("PROJECT_RUNTIME.json synchronized.")
print()
print("NOTE:")
print("- No commit performed.")
print("- No push performed.")
print("- No workflow state modified.")
print("- Runtime metadata synchronized only.")
print("=" * 70)
