#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ok_all = True

def ok(msg): print(f"[PASS] {msg}")
def warn(msg): print(f"[WARN] {msg}")
def fail(msg):
    global ok_all
    ok_all = False
    print(f"[FAIL] {msg}")

def load(path):
    p = Path(path)
    if not p.exists():
        fail(f"{path} not found")
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        ok(f"{path} JSON valid")
        return data
    except Exception as e:
        fail(f"{path} invalid JSON: {e}")
        return None

boot = load("PROJECT_BOOT.json")
runtime = load("PROJECT_RUNTIME.json")
history = load("PROJECT_HISTORY.json")

def git(c):
    return subprocess.check_output(c, shell=True, text=True, stderr=subprocess.DEVNULL).strip()

if runtime:
    git_head = git("git rev-parse HEAD")
    runtime_head = runtime.get("git", {}).get("head")

    if runtime_head == git_head:
        ok("Runtime observed HEAD matches current Git HEAD")
    else:
        warn(f"Runtime observed HEAD differs from current Git HEAD (current={git_head} runtime={runtime_head})")
        warn("V2 policy: this is not fatal. Current Git HEAD is live source; runtime HEAD is last observed metadata.")

    state = runtime.get("current_state", {})
    wu = state.get("active_work_unit", {})

    for key in ["id", "type", "status", "last_completed_step", "next_step"]:
        if wu.get(key):
            ok(f"active_work_unit.{key} exists")
        else:
            fail(f"active_work_unit.{key} missing")

    for key in ["last_action", "next_safe_step", "updated_at"]:
        if runtime.get(key):
            ok(f"{key} exists")
        else:
            fail(f"{key} missing")

print()
print("=" * 60)
print("BOOT_VALIDATION_V2=PASS" if ok_all else "BOOT_VALIDATION_V2=FAIL")
sys.exit(0 if ok_all else 1)
