from pathlib import Path
import json, datetime, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
NOW=datetime.datetime.now(datetime.UTC).isoformat()
HEAD=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()

required=[
"data/era24a_ede_reliability_baseline_v1.json",
"data/era24b_ede_performance_baseline_v1.json",
"data/era24c_ede_security_baseline_v1.json",
"data/era24d_ede_statistics_baseline_v1.json",
"data/era24e_ede_probability_baseline_v1.json",
"data/era24f_ede_opportunity_cost_baseline_v1.json",
"data/era25_sdf_contract_v1.json",
"data/era25_ecg_v1_contract_check.json",
"data/era25_sdf_contract_test_v1.json",
"data/era25_war_game_v1.json",
"data/era26_adaptive_intelligence_contract_v1.json",
"data/era26_contract_test_v1.json",
"data/era26_adaptive_weight_table_v1.json",
"data/era26_adaptive_weight_table_test_v1.json",
"data/era27_predictive_intelligence_contract_v1.json",
"data/era27_prediction_contract_test_v1.json",
"data/era27_scenario_engine_v1.json",
"data/era27_scenario_engine_test_v1.json",
"data/era27_post_seal_war_game_v1.json"
]

checks=[]
fail=0

for f in required:
    p=ROOT/f
    ok=p.exists()
    checks.append({"file":f,"exists":ok})
    print(("PASS" if ok else "FAIL"),f)
    if not ok: fail+=1

for cmd in [["python3","boot_health_v1.py"],["python3","boot_commander_v2.py"],["python3","boot_guardian_v1.py"]]:
    r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    ok=r.returncode==0
    checks.append({"cmd":" ".join(cmd),"pass":ok})
    print(("PASS" if ok else "FAIL")," ".join(cmd))
    if not ok: fail+=1

report={
 "work_unit":"ERA24_28_FOUNDATION_AUDIT_V1",
 "created_at_utc":NOW,
 "git_head":HEAD,
 "mode":"READ_ONLY_AUDIT",
 "decision":"PASS" if fail==0 else "FAIL",
 "checks":checks
}

out=ROOT/"data/era24_28_foundation_audit_v1.json"
out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

print("ERA24_28_FOUNDATION_AUDIT=",report["decision"])
print("OUT=data/era24_28_foundation_audit_v1.json")
print("WRITE=REPORT_ONLY")
print("PUSH=NO")
sys.exit(1 if fail else 0)
