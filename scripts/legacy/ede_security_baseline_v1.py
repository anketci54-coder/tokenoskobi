from pathlib import Path
import subprocess,json,datetime,re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/era24c_ede_security_baseline_v1.json"

checks=[]

def run(name,cmd):
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    checks.append({
        "name":name,
        "pass":p.returncode==0,
        "rc":p.returncode
    })

run("boot_health",["python3","boot_health_v1.py"])
run("commander",["python3","boot_commander_v2.py"])
run("guardian",["python3","boot_guardian_v1.py"])
run("workflow",["python3","boot_workflow_manager_v1.py"])

rt=json.loads((ROOT/"PROJECT_RUNTIME.json").read_text())

rules={
 "live_trade_locked":rt["hard_rules"]["live_trade_locked"],
 "paper_trade_locked":rt["hard_rules"]["paper_trade_locked_until_explicit_phase"],
 "ai_has_no_trade_authority":rt["hard_rules"]["ai_has_no_trade_authority"],
 "human_approval_required":rt["hard_rules"]["human_approval_required"]
}

security_score=100.0 if all(check["pass"] for check in checks) and all(rules.values()) else 0.0

obj={
 "work_unit":"ERA24C_EDE_SECURITY_BASELINE_PLAN",
 "created_at_utc":datetime.datetime.now(datetime.UTC).isoformat(),
 "decision":"PASS" if security_score==100 else "FAIL",
 "boot_checks":checks,
 "security_rules":rules,
 "security_score":security_score
}

OUT.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

print("ERA24C_SECURITY_BASELINE=PASS" if obj["decision"]=="PASS" else "ERA24C_SECURITY_BASELINE=FAIL")
print("OUT=",OUT)
