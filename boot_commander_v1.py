#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

FILES = [
    "PROJECT_BOOT.json",
    "PROJECT_RUNTIME.json",
    "PROJECT_HISTORY.json"
]

def run(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def exists_and_valid(path):
    p = Path(path)
    if not p.exists():
        return False, "NOT_FOUND"
    try:
        with open(p, encoding="utf-8") as f:
            json.load(f)
        return True, "PASS"
    except Exception as e:
        return False, str(e)

print("="*70)
print("TOKENOSKOBI DEVELOPMENT OS")
print("="*70)

overall = True

print("\n[BOOT FILES]")

for f in FILES:
    ok, msg = exists_and_valid(f)
    if ok:
        print(f"{f:30} PASS")
    else:
        overall = False
        print(f"{f:30} FAIL ({msg})")

print("\n[VALIDATOR]")

rc, out, err = run("python3 boot_validator_v1.py")

print(out)

if rc != 0:
    overall = False

print("\n[WORKFLOW MANAGER]")

rc, out, err = run("python3 boot_workflow_manager_v1.py")

print(out)

if rc != 0:
    overall = False

print("\n[CONTINUATION ENGINE]")

rc, out, err = run("python3 boot_continuation_engine_v1.py")

if rc == 0:
    try:
        data = json.loads(out)

        pos = data.get("current_position", {})
        git = data.get("git", {})
        nxt = data.get("next_safe_step", {})

        print(f"HEAD             : {git.get('head')}")
        print(f"BRANCH           : {git.get('branch')}")
        print(f"WORK UNIT        : {pos.get('active_work_unit_id')}")
        print(f"STATUS           : {pos.get('active_work_unit_status')}")
        print(f"LAST STEP        : {pos.get('last_completed_step')}")
        print(f"NEXT STEP        : {pos.get('next_step')}")
        print(f"NEXT SAFE STEP   : {nxt.get('name')}")
    except Exception:
        overall = False
        print("Cannot parse continuation output.")
else:
    overall = False
    print(out)
    print(err)

print("\n"+"="*70)

if overall:
    print("SYSTEM STATUS : READY")
    sys.exit(0)
else:
    print("SYSTEM STATUS : FAIL")
    sys.exit(1)

