
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
import json, sys
from pathlib import Path

rt = TrackedRuntime(json.loads(Path("PROJECT_RUNTIME.json").read_text(encoding="utf-8")))
wu=rt.get("current_state",{}).get("active_work_unit",{})
status=wu.get("status")
nexts=wu.get("next_step")

SEALED_STATUSES={
    "GITHUB_SEALED",
    "GITHUB_SEALED_HEALTH_100",
    "WORK_UNIT_CLOSED"
}

if not wu:
    print("BOOT_GUARDIAN=FAIL active_work_unit missing")
    sys.exit(1)

if status not in SEALED_STATUSES and nexts == "NEXT_WORK_UNIT_PLAN":
    print("BOOT_GUARDIAN=FAIL unsealed work unit cannot open next work unit")
    sys.exit(1)

print("BOOT_GUARDIAN=PASS")


try:
    rt_dump()
except Exception:
    pass


try:
    runtime.report()
except Exception:
    pass
