#!/usr/bin/env python3
import json, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone

if len(sys.argv) < 3:
    print("USAGE: python3 boot_workunit_open_v1.py WORK_UNIT_ID WORK_UNIT_TYPE")
    sys.exit(1)

work_id=sys.argv[1]
work_type=sys.argv[2]

p=Path("PROJECT_RUNTIME.json")
rt=json.loads(p.read_text(encoding="utf-8"))

wu=rt.get("current_state",{}).get("active_work_unit",{})
if wu and wu.get("next_step") != "NEXT_WORK_UNIT_PLAN":
    print("BOOT_WORKUNIT_OPEN=FAIL current work unit not ready for next plan")
    sys.exit(1)

head=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
branch=subprocess.check_output(["git","branch","--show-current"],text=True).strip()
now=datetime.now(timezone.utc).isoformat()

rt["updated_at"]=now
rt["git"]["head"]=head
rt["git"]["branch"]=branch

rt["current_state"]["active_work_unit"]={
  "id":work_id,
  "type":work_type,
  "status":"PLAN_LOCAL",
  "last_completed_step":"PLAN",
  "next_step":"APPROVAL"
}

rt["last_action"]={
  "timestamp":now,
  "task":f"Opened work unit {work_id}",
  "result":"PLAN_LOCAL",
  "git_head":head
}

rt["next_safe_step"]={
  "name":f"APPROVE_{work_id}",
  "status":"WAITING_USER_APPROVAL",
  "instruction":"User approval required before APPLY."
}

p.write_text(json.dumps(rt,indent=2,ensure_ascii=False),encoding="utf-8")
print(f"BOOT_WORKUNIT_OPEN=PASS {work_id}")
