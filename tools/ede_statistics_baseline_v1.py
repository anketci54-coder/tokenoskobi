from pathlib import Path
import json, datetime, statistics, math

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/era24d_ede_statistics_baseline_v1.json"

INPUTS=[
 ROOT/"data/era24a_ede_reliability_baseline_v1.json",
 ROOT/"data/era24b_ede_performance_baseline_v1.json",
 ROOT/"data/era24c_ede_security_baseline_v1.json",
]

values=[]
sources=[]

for p in INPUTS:
    if not p.exists():
        sources.append({"file":str(p.relative_to(ROOT)),"exists":False})
        continue
    d=json.loads(p.read_text(encoding="utf-8"))
    score=None
    if "score" in d and isinstance(d["score"],dict):
        score=d["score"].get("reliability_score") or d["score"].get("performance_score")
    if score is None:
        score=d.get("security_score")
    if score is not None:
        values.append(float(score))
    sources.append({"file":str(p.relative_to(ROOT)),"exists":True,"score":score})

if not values:
    decision="FAIL"
    stats={}
else:
    mean=statistics.mean(values)
    median=statistics.median(values)
    stdev=statistics.pstdev(values) if len(values)>1 else 0.0
    variance=statistics.pvariance(values) if len(values)>1 else 0.0
    min_v=min(values)
    max_v=max(values)
    ci95=1.96*(stdev/math.sqrt(len(values))) if len(values)>1 else 0.0
    stats={
        "n":len(values),
        "mean":round(mean,4),
        "median":round(median,4),
        "min":round(min_v,4),
        "max":round(max_v,4),
        "variance":round(variance,6),
        "stdev":round(stdev,6),
        "ci95_half_width":round(ci95,6)
    }
    decision="PASS" if mean>=95 and min_v>=90 else "FAIL"

obj={
 "work_unit":"ERA24D_EDE_STATISTICS_BASELINE_PLAN",
 "mode":"LOCAL_NOAPI",
 "created_at_utc":datetime.datetime.now(datetime.UTC).isoformat(),
 "purpose":"Build first statistics baseline from ERA24A/B/C EDE baseline artifacts.",
 "inputs":sources,
 "statistics":stats,
 "decision":decision
}

OUT.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

print("ERA24D_STATISTICS_BASELINE="+decision)
print("OUT=",OUT)
print("N=",stats.get("n"))
print("MEAN=",stats.get("mean"))
print("MIN=",stats.get("min"))
raise SystemExit(0 if decision=="PASS" else 1)
