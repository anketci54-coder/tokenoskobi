#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

PASS = True

def ok(msg):
    print(f"[PASS] {msg}")

def fail(msg):
    global PASS
    PASS = False
    print(f"[FAIL] {msg}")

def load_json(path):
    p = Path(path)
    if not p.exists():
        fail(f"{path} not found")
        return None
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        ok(f"{path} JSON valid")
        return data
    except Exception as e:
        fail(f"{path} invalid JSON ({e})")
        return None

boot = load_json("PROJECT_BOOT.json")
runtime = load_json("PROJECT_RUNTIME.json")
history = load_json("PROJECT_HISTORY.json")

if runtime:
    try:
        git_head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True
        ).strip()

        runtime_head = runtime.get("git", {}).get("head")

        if git_head == runtime_head:
            ok("Git HEAD matches Runtime HEAD")
        else:
            fail(f"HEAD mismatch (git={git_head} runtime={runtime_head})")

    except Exception as e:
        fail(f"Cannot read git HEAD ({e})")

    state = runtime.get("current_state", {})
    wu = state.get("active_work_unit", {})

    required_runtime = [
        ("active_work_unit", wu),
        ("last_action", runtime.get("last_action")),
        ("next_safe_step", runtime.get("next_safe_step")),
        ("updated_at", runtime.get("updated_at"))
    ]

    for name, value in required_runtime:
        if value:
            ok(f"{name} exists")
        else:
            fail(f"{name} missing")

print()
print("=" * 60)

if PASS:
    print("BOOT_VALIDATION=PASS")
    sys.exit(0)
else:
    print("BOOT_VALIDATION=FAIL")
    sys.exit(1)

