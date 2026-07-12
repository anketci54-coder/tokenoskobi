#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
A26_DEFAULT = Path("/tmp/era55a26_p1_delete_vs_wal_temp_copy_benchmark_v1.json")
WORK_UNIT = "ERA55A_27_P1_WAL_BOUNDED_APPLY_READINESS_ROLLBACK_AND_AUTHORIZATION_DECISION"
RESULT = "OK_OPTION_B_DEFERRED_ERA24F_NET_UTILITY_BELOW_BASELINE"
NEXT = "ERA55_POST_OPTION_B_STRATEGIC_PRIORITY_SELECTION_DECISION"
SUBJECT = "ERA55A27_DECISION | OK | ERA24F_DEFER_OPTION_B"
ACCEPT_BASELINE = 95.0

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"
ARTIFACT = ROOT / "data/control/era55a27_p1_wal_readiness_rollback_and_opportunity_cost_decision_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A27_WAL_READINESS_ROLLBACK_AND_OPPORTUNITY_COST_DECISION.md"
MUTATED = (RUNTIME, HISTORY, MASTER, HANDOFF, ALMANAC, ARTIFACT, REPORT)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check, timeout=60)


def git(*args: str) -> str:
    return run(["git", *args]).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"A27_JSON_OBJECT_REQUIRED:{path}")
    return value


def clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 4)


def era24f(scores: dict[str, float]) -> dict[str, Any]:
    expected_gain = (scores["reliability"] + scores["security"] + scores["probability"]) / 3
    cost_penalty = max(0.0, 100.0 - scores["performance"])
    uncertainty_penalty = max(0.0, 100.0 - scores["statistics"])
    net_utility = expected_gain - cost_penalty - uncertainty_penalty
    return {
        "formula_contract": "ERA24F_EDE_OPPORTUNITY_COST_BASELINE",
        "expected_gain": round(expected_gain, 4),
        "cost_penalty": round(cost_penalty, 4),
        "uncertainty_penalty": round(uncertainty_penalty, 4),
        "net_utility": round(net_utility, 4),
        "accept_baseline": ACCEPT_BASELINE,
        "formula_decision": "ACCEPT" if net_utility >= ACCEPT_BASELINE else "DEFER",
        "scores": scores,
    }


def validate_and_map(a26: dict[str, Any]) -> tuple[dict[str, bool], dict[str, float], dict[str, Any]]:
    decision = a26["decision"]
    delete = a26["delete_variant"]
    wal = a26["wal_variant"]
    dr = a26["delete_recovery"]
    wr = a26["wal_recovery"]
    source = a26.get("source", {})
    before = source.get("state_before", {})
    after = source.get("state_after", {})

    checks = {
        "temp_copy_only": a26.get("status") == "COMPLETED_TEMP_COPY_ONLY",
        "production_mutation_false": a26.get("production_mutation") is False,
        "production_apply_false": a26.get("production_apply_authorized") is False,
        "correctness_ok": decision.get("correctness_ok") is True,
        "materially_faster": decision.get("materially_faster") is True,
        "delete_integrity_ok": delete["integrity"].get("integrity_check") == "ok",
        "wal_integrity_ok": wal["integrity"].get("integrity_check") == "ok",
        "wal_errors_zero": all(wal.get(k) == 0 for k in ("busy_or_locked_errors", "sqlite_io_errors", "sqlite_corrupt_errors")),
        "delete_recovery_ok": not dr.get("sqlite_corrupt_detected") and not dr.get("sqlite_ioerr_detected"),
        "wal_recovery_ok": not wr.get("sqlite_corrupt_detected") and not wr.get("sqlite_ioerr_detected"),
        "production_source_unchanged": bool(before.get("sha256")) and before.get("sha256") == after.get("sha256"),
    }
    if not all(checks.values()):
        raise RuntimeError("A27_A26_EVIDENCE_INVALID:" + ",".join(k for k, v in checks.items() if not v))

    p95_gain = float(decision["p95_latency_gain_percent"])
    throughput_gain = float(decision["throughput_gain_percent"])
    p95_score = clamp((p95_gain / 15.0) * 100.0)
    throughput_score = clamp((throughput_gain / 20.0) * 100.0)
    performance = clamp((p95_score + throughput_score) / 2.0)

    reliability_components = {
        "correctness": 100.0 if checks["correctness_ok"] else 0.0,
        "sqlite_error_free": 100.0 if checks["wal_errors_zero"] else 0.0,
        "controlled_recovery": 100.0 if checks["delete_recovery_ok"] and checks["wal_recovery_ok"] else 0.0,
    }
    reliability = clamp(sum(reliability_components.values()) / len(reliability_components))

    security_components = {
        "sandbox_isolation": 100.0 if checks["production_mutation_false"] and checks["production_source_unchanged"] else 0.0,
        "service_quiescence_proven": 0.0,
        "lossless_rollback_proven": 0.0,
        "interrupted_transition_recovery_proven": 0.0,
        "disk_full_recovery_proven": 0.0,
    }
    security = clamp(sum(security_components.values()) / len(security_components))

    # A26 contains one benchmark workload and one controlled-kill recovery class.
    # No natural-cycle diversity or additional failure-class evidence is present in the A26 artifact.
    statistics_components = {
        "benchmark_workload_diversity": 20.0,
        "recovery_risk_class_coverage": 20.0,
        "natural_cycle_diversity_in_a26": 0.0,
        "repeat_run_diversity": 0.0,
        "environment_diversity": 0.0,
    }
    statistics = clamp(sum(statistics_components.values()) / len(statistics_components))
    probability = clamp((performance * reliability) / 100.0)

    scores = {
        "reliability": reliability,
        "performance": performance,
        "security": security,
        "statistics": statistics,
        "probability": probability,
    }
    mapping = {
        "p95_latency_gain_percent": p95_gain,
        "throughput_gain_percent": throughput_gain,
        "performance_components": {"p95_threshold_normalized": p95_score, "throughput_threshold_normalized": throughput_score},
        "reliability_components": reliability_components,
        "security_components": security_components,
        "statistics_components": statistics_components,
        "probability_rule": "performance_x_reliability_div_100",
    }
    return checks, scores, mapping


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def replace_section(text: str, heading: str, body: str) -> str:
    start = text.find(heading)
    if start < 0:
        raise RuntimeError(f"A27_HEADING_MISSING:{heading}")
    end = text.find("\n## ", start + len(heading))
    if end < 0:
        end = len(text)
    return text[:start] + heading + "\n\n" + body.rstrip() + "\n" + text[end:]


def backup() -> tuple[Path, dict[Path, Path | None]]:
    root = Path(tempfile.mkdtemp(prefix="era55a27_backup_", dir="/tmp"))
    copies: dict[Path, Path | None] = {}
    for index, path in enumerate(MUTATED):
        if path.exists():
            target = root / f"{index:02d}.backup"
            shutil.copy2(path, target)
            copies[path] = target
        else:
            copies[path] = None
    return root, copies


def restore(copies: dict[Path, Path | None]) -> None:
    run(["git", "reset"], check=False)
    for path, saved in copies.items():
        if saved is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved, path)


def build_artifact(source: Path) -> dict[str, Any]:
    a26 = load(source)
    checks, scores, mapping = validate_and_map(a26)
    opportunity = era24f(scores)
    if opportunity["net_utility"] >= ACCEPT_BASELINE:
        raise RuntimeError("UNEXPECTED_HIGH_UTILITY_WARNING:A27_REQUIRES_HUMAN_REVIEW")
    return {
        "schema": "era55a27_p1_wal_readiness_rollback_and_opportunity_cost_decision_v2",
        "timestamp_utc": now(),
        "work_unit": WORK_UNIT,
        "status": "CLOSED_OPTION_B_DEFERRED",
        "result": RESULT,
        "decision": "DEFER_OPTION_B",
        "a26_source": str(source),
        "a26_validation": checks,
        "a27_specific_score_mapping": mapping,
        "era24f_opportunity_cost": opportunity,
        "authorization": {"production_mutation": False, "wal_apply_authorized": False, "bounded_apply_authorized": False, "human_final_authority": True},
        "next_safe_step": NEXT,
    }


def apply_canonical(artifact: dict[str, Any]) -> None:
    timestamp = artifact["timestamp_utc"]
    artifact_rel = str(ARTIFACT.relative_to(ROOT))
    opportunity = artifact["era24f_opportunity_cost"]
    atomic_json(ARTIFACT, artifact)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(f"""# ERA55A27 ERA24F OPPORTUNITY COST DECISION

- Decision: `DEFER_OPTION_B`
- Net utility: `{opportunity['net_utility']}`
- Accept baseline: `{opportunity['accept_baseline']}`
- Expected gain: `{opportunity['expected_gain']}`
- Cost penalty: `{opportunity['cost_penalty']}`
- Uncertainty penalty: `{opportunity['uncertainty_penalty']}`
- Production mutation: `false`
- WAL apply authorized: `false`

A26 proves strong sandbox performance. ERA24F rejects current production migration because security and statistical coverage remain insufficient.
""", encoding="utf-8")

    runtime = load(RUNTIME)
    runtime["current_era"] = "ERA55"
    runtime["current_era_status"] = "OPEN"
    runtime["current_problem"] = {"code": "POST_OPTION_B_STRATEGIC_PRIORITY_SELECTION_PENDING", "severity": "P1", "evidence": artifact_rel}
    runtime["canonical_runtime_pointer"] = {"authority": "PROJECT_RUNTIME.json", "project_status": "ACTIVE_ERA55_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING", "current_version_line": "V3_RUNTIME_INTELLIGENCE_OS", "current_era": "ERA55_RUNTIME_OPTIMIZATION", "current_stage": "ERA55A_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING", "last_completed": WORK_UNIT, "last_result": RESULT, "last_artifact": artifact_rel, "production_ledger_writer_active": True, "p0_f1_closed": True, "option_b_authorized": False, "wal_apply_authorized": False, "era24f_net_utility": opportunity["net_utility"], "next_safe_step": NEXT, "git_head": "DYNAMIC_USE_GIT_REV_PARSE_HEAD", "updated_at_utc": timestamp}
    runtime["current_state"] = {"project_status": "ACTIVE", "runtime_status": "WORK_UNIT_CLOSED", "mode": "ERA55A27_OPTION_B_DEFERRED_ERA24F", "last_action": {"task": WORK_UNIT, "result": RESULT, "artifact": artifact_rel, "timestamp": timestamp}, "current_problem": runtime["current_problem"], "next_safe_step": {"id": NEXT, "status": "READY", "human_authorization_required": True, "option_b_authorized": False, "wal_apply_authorized": False}, "updated_at": timestamp}
    runtime["current_work_unit"] = {"id": WORK_UNIT, "status": "CLOSED_OPTION_B_DEFERRED", "result": RESULT, "artifact": artifact_rel, "production_mutation": False, "next_step": NEXT}
    atomic_json(RUNTIME, runtime)

    history = load(HISTORY)
    events = history.setdefault("events", [])
    if not any(isinstance(e, dict) and e.get("event_id") == "ERA55A27_OPTION_B_DEFERRED_ERA24F" for e in events):
        events.append({"event_id": "ERA55A27_OPTION_B_DEFERRED_ERA24F", "timestamp_utc": timestamp, "era": "ERA55", "work_unit": WORK_UNIT, "status": "CLOSED_OPTION_B_DEFERRED", "result": RESULT, "artifact": artifact_rel, "decision": "DEFER_OPTION_B", "era24f_net_utility": opportunity["net_utility"], "production_mutation": False, "next_safe_step": NEXT})
    history["updated_at"] = timestamp
    history["updated_at_utc"] = timestamp
    atomic_json(HISTORY, history)

    master = MASTER.read_text(encoding="utf-8")
    master = replace_section(master, "## 02 CURRENT MAJOR-LINE POSITION", f"""```text
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_LEDGER_WRITER_ACTIVE=true
P0_F1_CLOSED=true
OPTION_B_DECISION=DEFER_OPTION_B
ERA24F_NET_UTILITY={opportunity['net_utility']}
ERA24F_ACCEPT_BASELINE={opportunity['accept_baseline']}
WAL_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
```""")
    master = replace_section(master, "## 03 LAST VERIFIED WORK", f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={artifact_rel}
WORK_UNIT_STATUS=CLOSED_OPTION_B_DEFERRED
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}""")
    master = replace_section(master, "## 09 OPEN RISKS AND DECISIONS", """- WAL showed strong sandbox performance gains.
- ERA24F net utility remains below the canonical acceptance baseline.
- Production migration security, quiescence and lossless rollback remain unproven.
- Statistical coverage is limited to one workload and one controlled recovery class.
- Option B production apply remains blocked.
- Opportunity-cost superiority over higher-value intelligence lines remains unproven.""")
    master = replace_section(master, "## 10 NEXT SAFE STEP", f"""```text
NEXT_SAFE_STEP={NEXT}
```

Select the highest-value strategic project line. Do not apply WAL without separate future authorization and new evidence.""")
    MASTER.write_text(master, encoding="utf-8")

    handoff = HANDOFF.read_text(encoding="utf-8")
    handoff = replace_section(handoff, "## 02 CURRENT CONTINUATION CHECKPOINT", f"""PROJECT_STATUS=ACTIVE_ERA55_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_LEDGER_WRITER_ACTIVE=true
P0_F1_CLOSED=true
OPTION_B_DECISION=DEFER_OPTION_B
ERA24F_NET_UTILITY={opportunity['net_utility']}
WAL_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""")
    handoff = replace_section(handoff, "## 03 LAST VERIFIED WORK", f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={artifact_rel}
WORK_UNIT_STATUS=CLOSED_OPTION_B_DEFERRED
PRODUCTION_MUTATION=false
CURRENT_PROBLEM=POST_OPTION_B_STRATEGIC_PRIORITY_SELECTION_PENDING""")
    handoff = replace_section(handoff, "## 07 ALLOWED NEXT DECISIONS", f"""- Guarded production writer: `ACTIVE`.
- P0 F1: `CLOSED`.
- Option B: `DEFERRED` by ERA24F.
- WAL production apply: `BLOCKED`.
- Strategic priority selection: `AUTHORIZED`.

NEXT_SAFE_STEP={NEXT}""")
    HANDOFF.write_text(handoff, encoding="utf-8")

    marker = "## ERA55A_27 ERA24F OPPORTUNITY COST DECISION"
    almanac = ALMANAC.read_text(encoding="utf-8")
    if marker not in almanac:
        ALMANAC.write_text(almanac.rstrip() + f"\n\n---\n\n{marker}\n\n- Status: `CLOSED_OPTION_B_DEFERRED`\n- Result: `{RESULT}`\n- Decision: `DEFER_OPTION_B`\n- ERA24F net utility: `{opportunity['net_utility']}`\n- Accept baseline: `{opportunity['accept_baseline']}`\n- Production mutation: `false`\n- WAL apply authorized: `false`\n- Next safe step: `{NEXT}`\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=A26_DEFAULT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.source.is_file():
        raise RuntimeError(f"A27_A26_ARTIFACT_MISSING:{args.source}")
    if git("status", "--short"):
        raise RuntimeError("A27_WORKTREE_NOT_CLEAN")
    expected = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()
    if expected and git("rev-parse", "HEAD") != expected:
        raise RuntimeError("A27_HEAD_MISMATCH")

    artifact = build_artifact(args.source)
    opportunity = artifact["era24f_opportunity_cost"]
    print("A27_DRY_RUN=" + str(not args.apply).lower())
    print("ERA24F_NET_UTILITY=" + str(opportunity["net_utility"]))
    print("ERA24F_ACCEPT_BASELINE=" + str(opportunity["accept_baseline"]))
    print("DECISION=DEFER_OPTION_B")
    print("WAL_APPLY_AUTHORIZED=false")
    print("PRODUCTION_MUTATION=false")
    if not args.apply:
        return 0

    backup_root, copies = backup()
    try:
        apply_canonical(artifact)
        git("add", str(ARTIFACT.relative_to(ROOT)), str(RUNTIME.relative_to(ROOT)), str(HISTORY.relative_to(ROOT)), str(MASTER.relative_to(ROOT)), str(HANDOFF.relative_to(ROOT)), str(ALMANAC.relative_to(ROOT)))
        run(["git", "add", "-f", str(REPORT.relative_to(ROOT))])
        git("diff", "--cached", "--check")
        if not git("diff", "--cached", "--name-only"):
            raise RuntimeError("A27_NO_STAGED_CHANGES")
        git("commit", "-m", SUBJECT)
    except Exception:
        restore(copies)
        raise
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)

    print("A27_APPLY=SUCCESS")
    print("NEXT_SAFE_STEP=" + NEXT)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
