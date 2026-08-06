from pathlib import Path
import json, datetime

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/era24e_ede_probability_baseline_v1.json"

SRC=ROOT/"data/era24d_ede_statistics_baseline_v1.json"
d=json.loads(SRC.read_text(encoding="utf-8"))

s=d["statistics"]
mean=float(s["mean"])
stdev=float(s["stdev"])
ci95=float(s["ci95_half_width"])

confidence=max(0.0,min(100.0,mean-ci95))
stability=max(0.0,min(100.0,100.0-stdev))

decision="PASS" if confidence>=95 and stability>=95 else "FAIL"

obj={
  "work_unit":"ERA24E_EDE_PROBABILITY_BASELINE_PLAN",
  "created_at_utc":datetime.datetime.now(datetime.UTC).isoformat(),
  "input":"data/era24d_ede_statistics_baseline_v1.json",
  "probability":{
    "confidence_score":round(confidence,4),
    "stability_score":round(stability,4),
    "probability_score":round((confidence+stability)/2,4)
  },
  "decision":decision
}

OUT.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

print("ERA24E_PROBABILITY_BASELINE="+decision)
print("OUT=",OUT)
print("PROBABILITY=",obj["probability"])
