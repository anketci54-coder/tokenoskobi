
# === ERA23D_TRACKED_RUNTIME ===
class TrackedRuntime(dict):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._usage = {}

    def _hit(self, key):
        self._usage[key] = self._usage.get(key, 0) + 1

    def get(self, key, default=None):
        self._hit(key)
        return super().get(key, default)

    def __getitem__(self, key):
        self._hit(key)
        return super().__getitem__(key)

    def report(self):
        print("\n=== TRACKED RUNTIME USAGE ===")
        for k, v in sorted(self._usage.items()):
            print(f"{k}: {v}")


# === ERA23D_DYNAMIC_USAGE_TRACE ===
import os

_USAGE = {}

def rt_get(d, key, default=None):
    _USAGE[key] = _USAGE.get(key, 0) + 1
    return d.get(key, default)

def rt_dump():
    if os.getenv("TOKENOSKOBI_TRACE_RUNTIME","0") != "1":
        return
    print("\n=== RUNTIME USAGE TRACE ===")
    for k,v in sorted(_USAGE.items()):
        print(f"{k}: {v}")

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
        d = TrackedRuntime(json.loads(p.stdout))
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


try:
    rt_dump()
except Exception:
    pass


try:
    runtime.report()
except Exception:
    pass
