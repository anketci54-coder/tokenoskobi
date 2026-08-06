from pathlib import Path
import subprocess, json, time, datetime, statistics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/era24a_ede_reliability_baseline_v1.json"

CHECKS = [
    ("boot_health", ["python3", "boot_health_v1.py"]),
    ("commander", ["python3", "boot_commander_v2.py"]),
    ("guardian", ["python3", "boot_guardian_v1.py"]),
    ("workflow", ["python3", "boot_workflow_manager_v1.py"]),
]

runs = []
for name, cmd in CHECKS:
    t0 = time.perf_counter()
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    ms = round((time.perf_counter() - t0) * 1000, 3)
    runs.append({
        "name": name,
        "cmd": " ".join(cmd),
        "rc": p.returncode,
        "pass": p.returncode == 0,
        "duration_ms": ms,
        "stdout_tail": p.stdout[-1200:],
        "stderr_tail": p.stderr[-1200:]
    })

pass_count = sum(1 for r in runs if r["pass"])
durations = [r["duration_ms"] for r in runs]

score = {
    "boot_success_rate": 1.0 if all(r["pass"] for r in runs) else pass_count / len(runs),
    "checks_passed": pass_count,
    "checks_total": len(runs),
    "mean_duration_ms": round(statistics.mean(durations), 3),
    "max_duration_ms": max(durations),
    "reliability_score": round((pass_count / len(runs)) * 100, 2)
}

result = {
    "work_unit": "ERA24A_ENGINEERING_DECISION_ENGINE_FOUNDATION_PLAN",
    "mode": "LOCAL_NOAPI",
    "created_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
    "purpose": "First EDE reliability baseline using existing boot tools.",
    "checks": runs,
    "score": score,
    "decision": "PASS" if score["reliability_score"] == 100 else "FAIL"
}

OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print("ERA24A_EDE_RELIABILITY_BASELINE=PASS" if result["decision"] == "PASS" else "ERA24A_EDE_RELIABILITY_BASELINE=FAIL")
print("RELIABILITY_SCORE=", score["reliability_score"])
print("CHECKS=", f"{pass_count}/{len(runs)}")
print("MEAN_DURATION_MS=", score["mean_duration_ms"])
print("OUT=", OUT)
raise SystemExit(0 if result["decision"] == "PASS" else 1)
