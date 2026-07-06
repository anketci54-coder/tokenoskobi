#!/usr/bin/env python3
import subprocess, sys

checks=[
 ("validator","python3 boot_validator_v2.py"),
 ("workflow","python3 boot_workflow_manager_v1.py"),
 ("guardian","python3 boot_guardian_v1.py"),
 ("schema","python3 boot_schema_v1.py"),
 ("commander","python3 boot_commander_v2.py")
]

score=0
for name,cmd in checks:
    rc=subprocess.call(cmd,shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if rc==0:
        print(f"{name}: PASS"); score+=20
    else:
        print(f"{name}: FAIL")

print(f"BOOT_HEALTH={score}/100")
sys.exit(0 if score==100 else 1)
