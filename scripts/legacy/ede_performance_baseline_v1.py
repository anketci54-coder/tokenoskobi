from pathlib import Path
import subprocess,json,time,datetime,statistics

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/era24b_ede_performance_baseline_v1.json"

CMDS=[
 ("boot_health",["python3","boot_health_v1.py"]),
 ("commander",["python3","boot_commander_v2.py"]),
 ("guardian",["python3","boot_guardian_v1.py"]),
 ("workflow",["python3","boot_workflow_manager_v1.py"]),
]

N=5
rows=[]

for name,cmd in CMDS:
    samples=[]
    rc_ok=True
    for _ in range(N):
        t0=time.perf_counter()
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        dt=(time.perf_counter()-t0)*1000
        samples.append(round(dt,3))
        rc_ok &= (p.returncode==0)
    rows.append({
        "name":name,
        "pass":rc_ok,
        "runs":N,
        "min_ms":min(samples),
        "mean_ms":round(statistics.mean(samples),3),
        "max_ms":max(samples)
    })

score={
 "checks":len(rows),
 "passed":sum(r["pass"] for r in rows),
 "overall_mean_ms":round(statistics.mean([r["mean_ms"] for r in rows]),3),
 "performance_score":100.0 if all(r["pass"] for r in rows) else 0.0
}

obj={
 "work_unit":"ERA24B_EDE_PERFORMANCE_BASELINE_PLAN",
 "created_at_utc":datetime.datetime.now(datetime.UTC).isoformat(),
 "decision":"PASS" if score["performance_score"]==100 else "FAIL",
 "results":rows,
 "score":score
}

OUT.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

print("ERA24B_PERFORMANCE_BASELINE=PASS" if obj["decision"]=="PASS" else "ERA24B_PERFORMANCE_BASELINE=FAIL")
print("OUT=",OUT)
