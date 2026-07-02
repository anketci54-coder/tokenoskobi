#!/usr/bin/env python3
import json, sys
from pathlib import Path
from datetime import datetime, timezone

SEQ=["PLAN","APPROVAL","APPLY","TEST","AUDIT","POST_AUDIT","COMMIT","PUSH","REMOTE_VERIFY","GITHUB_SEAL","RUNTIME_UPDATE","WORK_UNIT_CLOSED"]

if len(sys.argv)<2:
    print("USAGE: python3 boot_workunit_advance_v1.py NEXT_STEP_NAME")
    sys.exit(1)

target=sys.argv[1]
p=Path("PROJECT_RUNTIME.json")
rt=json.loads(p.read_text(encoding="utf-8"))
wu=rt["current_state"]["active_work_unit"]

current=wu["last_completed_step"]
if target not in SEQ:
    print("BOOT_WORKUNIT_ADVANCE=FAIL unknown step")
    sys.exit(1)

if current in SEQ:
    expected=SEQ[SEQ.index(current)+1] if current!="WORK_UNIT_CLOSED" else None
    if target != expected:
        print(f"BOOT_WORKUNIT_ADVANCE=FAIL expected {expected} got {target}")
        sys.exit(1)

now=datetime.now(timezone.utc).isoformat()
wu["last_completed_step"]=target
wu["next_step"]=SEQ[SEQ.index(target)+1] if target!="WORK_UNIT_CLOSED" else "NEXT_WORK_UNIT_PLAN"
wu["status"]=target

rt["updated_at"]=now
rt["last_action"]={
  "timestamp":now,
  "task":f"Advanced work unit {wu['id']} to {target}",
  "result":"PASS_LOCAL_UPDATE"
}
rt["next_safe_step"]={
  "name":wu["next_step"],
  "status":"READY",
  "instruction":"Continue only with the declared next step."
}

p.write_text(json.dumps(rt,indent=2,ensure_ascii=False),encoding="utf-8")
print(f"BOOT_WORKUNIT_ADVANCE=PASS {wu['id']} {target}")
