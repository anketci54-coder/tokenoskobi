from pathlib import Path
import json, datetime

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/era24f_ede_opportunity_cost_baseline_v1.json"

inputs=[
 ("reliability","data/era24a_ede_reliability_baseline_v1.json"),
 ("performance","data/era24b_ede_performance_baseline_v1.json"),
 ("security","data/era24c_ede_security_baseline_v1.json"),
 ("statistics","data/era24d_ede_statistics_baseline_v1.json"),
 ("probability","data/era24e_ede_probability_baseline_v1.json"),
]

scores={}
missing=[]

for name,rel in inputs:
    p=ROOT/rel
    if not p.exists():
        missing.append(rel)
        continue
    d=json.loads(p.read_text(encoding="utf-8"))
    if name=="reliability":
        scores[name]=d["score"]["reliability_score"]
    elif name=="performance":
        scores[name]=d["score"]["performance_score"]
    elif name=="security":
        scores[name]=d["security_score"]
    elif name=="statistics":
        scores[name]=d["statistics"]["mean"]
    elif name=="probability":
        scores[name]=d["probability"]["probability_score"]

if missing:
    decision="FAIL"
    opportunity={}
else:
    expected_gain=(scores["reliability"]+scores["security"]+scores["probability"])/3
    cost_penalty=max(0,100-scores["performance"])
    uncertainty_penalty=max(0,100-scores["statistics"])
    net_utility=expected_gain-cost_penalty-uncertainty_penalty
    opportunity={
      "expected_gain":round(expected_gain,4),
      "cost_penalty":round(cost_penalty,4),
      "uncertainty_penalty":round(uncertainty_penalty,4),
      "net_utility":round(net_utility,4),
      "scores":scores
    }
    decision="PASS" if net_utility>=95 else "FAIL"

obj={
 "work_unit":"ERA24F_EDE_OPPORTUNITY_COST_BASELINE_PLAN",
 "created_at_utc":datetime.datetime.now(datetime.UTC).isoformat(),
 "inputs":[{"name":n,"file":f} for n,f in inputs],
 "missing":missing,
 "opportunity_cost":opportunity,
 "decision":decision
}

OUT.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

print("ERA24F_OPPORTUNITY_COST_BASELINE="+decision)
print("OUT=",OUT)
print("NET_UTILITY=",opportunity.get("net_utility"))
raise SystemExit(0 if decision=="PASS" else 1)
