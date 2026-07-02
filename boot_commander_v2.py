#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

def run(c):
    return subprocess.run(c, shell=True, text=True, capture_output=True)

print("=" * 70)
print("TOKENOSKOBI DEVELOPMENT OS V2")
print("=" * 70)

overall = True

for f in ["PROJECT_BOOT.json", "PROJECT_RUNTIME.json", "PROJECT_HISTORY.json"]:
    try:
        json.loads(Path(f).read_text(encoding="utf-8"))
        print(f"{f:30} PASS")
    except Exception as e:
        overall = False
        print(f"{f:30} FAIL ({e})")

print("\n[VALIDATOR V2]")
p = run("python3 boot_validator_v2.py")
print(p.stdout.strip())
if p.returncode != 0:
    overall = False

print("\n[WORKFLOW]")
p = run("python3 boot_workflow_manager_v1.py")
print(p.stdout.strip())
if p.returncode != 0:
    overall = False

print("\n[CONTINUATION]")
p = run("python3 boot_continuation_engine_v1.py")
if p.returncode == 0:
    try:
        d = json.loads(p.stdout)
        pos = d.get("current_position", {})
        git = d.get("git", {})
        nxt = d.get("next_safe_step", {})
        print(f"HEAD             : {git.get('head')}")
        print(f"BRANCH           : {git.get('branch')}")
        print(f"WORK UNIT        : {pos.get('active_work_unit_id')}")
        print(f"STATUS           : {pos.get('active_work_unit_status')}")
        print(f"LAST STEP        : {pos.get('last_completed_step')}")
        print(f"NEXT STEP        : {pos.get('next_step')}")
        print(f"NEXT SAFE STEP   : {nxt.get('name')}")
    except Exception as e:
        overall = False
        print(f"Continuation parse failed: {e}")
else:
    overall = False
    print(p.stdout.strip())

print("\n" + "=" * 70)
print("SYSTEM STATUS : READY" if overall else "SYSTEM STATUS : FAIL")
sys.exit(0 if overall else 1)
