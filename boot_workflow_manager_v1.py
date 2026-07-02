#!/usr/bin/env python3
import json
import sys
from pathlib import Path

RUNTIME = Path("PROJECT_RUNTIME.json")

MANDATORY_SEQUENCE = [
    "PLAN",
    "APPROVAL",
    "APPLY",
    "TEST",
    "AUDIT",
    "POST_AUDIT",
    "COMMIT",
    "PUSH",
    "REMOTE_VERIFY",
    "GITHUB_SEAL",
    "RUNTIME_UPDATE",
    "WORK_UNIT_CLOSED"
]

def fail(msg):
    print("BOOT_WORKFLOW=FAIL")
    print(f"REASON={msg}")
    sys.exit(1)

def ok(msg):
    print(f"[PASS] {msg}")

if not RUNTIME.exists():
    fail("PROJECT_RUNTIME.json not found")

try:
    rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
except Exception as e:
    fail(f"PROJECT_RUNTIME.json invalid JSON: {e}")

wu = rt.get("current_state", {}).get("active_work_unit")
if not wu:
    fail("active_work_unit missing")

for key in ["id", "type", "status", "last_completed_step", "next_step"]:
    if not wu.get(key):
        fail(f"active_work_unit.{key} missing")

last_step = wu["last_completed_step"]
next_step = wu["next_step"]
status = wu["status"]

if last_step not in MANDATORY_SEQUENCE and last_step not in ["LOCAL_UPDATE", "BOOT_RUNTIME_SYNC"]:
    fail(f"Unknown last_completed_step: {last_step}")

if next_step not in MANDATORY_SEQUENCE and next_step not in ["NEXT_WORK_UNIT_PLAN", "TEST_IN_NEW_WINDOW", "VALIDATE_BOOT_THEN_COMMIT_PUSH_SEAL"]:
    fail(f"Unknown next_step: {next_step}")

if last_step in MANDATORY_SEQUENCE and next_step in MANDATORY_SEQUENCE:
    expected = MANDATORY_SEQUENCE[MANDATORY_SEQUENCE.index(last_step) + 1] if last_step != "WORK_UNIT_CLOSED" else "NEXT_WORK_UNIT_PLAN"
    if next_step != expected:
        fail(f"Invalid workflow order: after {last_step}, expected {expected}, got {next_step}")

if status == "GITHUB_SEALED":
    if last_step != "GITHUB_SEAL":
        fail("GITHUB_SEALED status requires last_completed_step=GITHUB_SEAL")
    if next_step not in ["NEXT_WORK_UNIT_PLAN", "RUNTIME_UPDATE", "WORK_UNIT_CLOSED"]:
        fail("GITHUB_SEALED status has invalid next_step")

ok(f"active_work_unit.id={wu['id']}")
ok(f"status={status}")
ok(f"last_completed_step={last_step}")
ok(f"next_step={next_step}")

print("BOOT_WORKFLOW=PASS")
