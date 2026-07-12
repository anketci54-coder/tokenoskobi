#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
A26_DEFAULT = Path("/tmp/era55a26_p1_delete_vs_wal_temp_copy_benchmark_v1.json")
WORK_UNIT = "ERA55A_27_P1_WAL_BOUNDED_APPLY_READINESS_ROLLBACK_AND_AUTHORIZATION_DECISION"
RESULT = "OK_OPTION_B_DEFERRED_OPPORTUNITY_COST_AND_ROLLBACK_READINESS_NOT_PROVEN"
NEXT = "ERA55_POST_OPTION_B_STRATEGIC_PRIORITY_SELECTION_DECISION"
SUBJECT = "ERA55A27_DECISION | OK | DEFER_OPTION_B_OPPORTUNITY_COST"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"
ARTIFACT = ROOT / "data/control/era55a27_p1_wal_readiness_rollback_and_opportunity_cost_decision_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A27_WAL_READINESS_ROLLBACK_AND_OPPORTUNITY_COST_DECISION.md"

PRODUCTION_DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"


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


def section(text: str, heading: str, body: str) -> str:
    start = text.find(heading)
    if start < 0:
        raise RuntimeError(f"A27_HEADING_MISSING:{heading}")
    next_heading = text.find("\n## ", start + len(heading))
    if next_heading < 0:
        next_heading = len(text)
    return text[:start] + heading + "\n\n" + body.rstrip() + "\n" + text[next_heading:]


def unit_state(unit: str) -> dict[str, str]:
    result = run([
        "systemctl", "show", unit,
        "--property=ActiveState,SubState,InvocationID,Result,ExecMainStatus",
        "--no-pager",
    ])
    output: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            output[key] = value
    return output


def validate_a26(data: dict[str, Any]) -> dict[str, Any]:
    decision = data["decision"]
    delete = data["delete_variant"]
    wal = data["wal_variant"]
    delete_recovery = data["delete_recovery"]
    wal_recovery = data["wal_recovery"]

    checks = {
        "temp_copy_only": data.get("status") == "COMPLETED_TEMP_COPY_ONLY",
        "production_mutation_false": data.get("production_mutation") is False,
        "production_apply_false": data.get("production_apply_authorized") is False,
        "correctness_ok": decision.get("correctness_ok") is True,
        "materially_faster": decision.get("materially_faster") is True,
        "wal_busy_zero": wal.get("busy_or_locked_errors") == 0,
        "wal_ioerr_zero": wal.get("sqlite_io_errors") == 0,
        "wal_corrupt_zero": wal.get("sqlite_corrupt_errors") == 0,
        "wal_recovery_corrupt_false": wal_recovery.get("sqlite_corrupt_detected") is False,
        "wal_recovery_ioerr_false": wal_recovery.get("sqlite_ioerr_detected") is False,
        "delete_recovery_corrupt_false": delete_recovery.get("sqlite_corrupt_detected") is False,
        "delete_recovery_ioerr_false": delete_recovery.get("sqlite_ioerr_detected") is False,
        "p95_gain_material": float(decision.get("p95_latency_gain_percent", 0)) >= 15.0,
        "throughput_gain_material": float(decision.get("throughput_gain_percent", 0)) >= 20.0,
        "delete_integrity_ok": delete["integrity"].get("integrity_check") == "ok",
        "wal_integrity_ok": wal["integrity"].get("integrity_check") == "ok",
    }
    if not all(checks.values()):
        failed = [name for name, ok in checks.items() if not ok]
        raise RuntimeError("A27_A26_EVIDENCE_INVALID:" + ",".join(failed))
    return checks


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else A26_DEFAULT
    if not source.is_file():
        raise RuntimeError(f"A27_A26_ARTIFACT_MISSING:{source}")
    if git("status", "--short"):
        raise RuntimeError("A27_WORKTREE_NOT_CLEAN")

    expected = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()
    head = git("rev-parse", "HEAD")
    if expected and head != expected:
        raise RuntimeError(f"A27_HEAD_MISMATCH:{head}")

    db_stat_before = PRODUCTION_DB.stat()
    service_before = unit_state(SERVICE)
    timer_before = unit_state(TIMER)

    a26 = load(source)
    checks = validate_a26(a26)
    decision = a26["decision"]

    # A26 proves measured sandbox benefit, but A27 intentionally does not
    # authorize production apply because quiescence, rollback, failure
    # coverage and opportunity-cost superiority remain unproven.
    gates = {
        "a26_material_benefit_proven": True,
        "service_quiescence_protocol_proven": False,
        "rollback_without_data_loss_proven": False,
        "disk_full_failure_path_proven": False,
        "partial_transition_recovery_proven": False,
        "checkpoint_interruption_recovery_proven": False,
        "maintenance_window_budget_proven": False,
        "year_one_value_exceeds_implementation_cost": False,
        "opportunity_cost_superior_to_hunter_unknown_whale_adversarial_fusion": False,
    }

    final_decision = "DEFER_OPTION_B"
    timestamp = now()
    artifact = {
        "schema": "era55a27_p1_wal_readiness_rollback_and_opportunity_cost_decision_v1",
        "timestamp_utc": timestamp,
        "work_unit": WORK_UNIT,
        "status": "CLOSED_OPTION_B_DEFERRED",
        "result": RESULT,
        "decision": final_decision,
        "a26_source": str(source),
        "a26_metrics": {
            "p95_latency_gain_percent": decision["p95_latency_gain_percent"],
            "throughput_gain_percent": decision["throughput_gain_percent"],
            "correctness_ok": decision["correctness_ok"],
            "materially_faster": decision["materially_faster"],
            "benchmark_recommendation": decision["benchmark_recommendation"],
        },
        "a26_validation": checks,
        "readiness_gates": gates,
        "motto_gate": {
            "speed": "PROVEN_IN_SANDBOX",
            "security": "PRODUCTION_MIGRATION_NOT_PROVEN",
            "power": "POTENTIAL_GAIN_PROVEN_IN_SANDBOX",
            "economy": "YEAR_ONE_COST_BENEFIT_NOT_PROVEN",
            "opportunity": "NOT_PROVEN_SUPERIOR_TO_HIGHER_VALUE_BACKLOG",
        },
        "authorization": {
            "production_mutation": False,
            "wal_apply_authorized": False,
            "bounded_apply_authorized": False,
            "planning_only": True,
            "human_final_authority": True,
        },
        "next_safe_step": NEXT,
    }
    atomic_json(ARTIFACT, artifact)

    report = f"""# ERA55A27 WAL READINESS, ROLLBACK AND OPPORTUNITY COST DECISION

- Status: `CLOSED_OPTION_B_DEFERRED`
- Result: `{RESULT}`
- Decision: `{final_decision}`
- A26 P95 gain: `{decision['p95_latency_gain_percent']:.2f}%`
- A26 throughput gain: `{decision['throughput_gain_percent']:.2f}%`
- Production mutation: `false`
- WAL apply authorized: `false`

## Decision

WAL produced strong sandbox gains, but production migration readiness is not proven. Service quiescence, lossless rollback, disk-full and interrupted-transition recovery, maintenance-window cost, year-one economics and strategic opportunity-cost superiority remain unresolved.

## Motto and opportunity-cost result

```text
SPEED=PROVEN_IN_SANDBOX
SECURITY=PRODUCTION_MIGRATION_NOT_PROVEN
POWER=POTENTIAL_GAIN_PROVEN_IN_SANDBOX
ECONOMY=NOT_PROVEN
OPPORTUNITY=NOT_PROVEN
FINAL_DECISION=DEFER_OPTION_B
```

## Authorization boundary

No production database, service, timer, panel or guarded-writer mutation is authorized.
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")

    runtime = load(RUNTIME)
    runtime["current_era"] = "ERA55"
    runtime["current_era_status"] = "OPEN"
    runtime["current_problem"] = {
        "code": "POST_OPTION_B_STRATEGIC_PRIORITY_SELECTION_PENDING",
        "severity": "P1",
        "evidence": str(ARTIFACT.relative_to(ROOT)),
    }
    runtime["canonical_runtime_pointer"] = {
        "authority": "PROJECT_RUNTIME.json",
        "project_status": "ACTIVE_ERA55_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING",
        "current_version_line": "V3_RUNTIME_INTELLIGENCE_OS",
        "current_era": "ERA55_RUNTIME_OPTIMIZATION",
        "current_stage": "ERA55A_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING",
        "last_completed": WORK_UNIT,
        "last_result": RESULT,
        "last_artifact": str(ARTIFACT.relative_to(ROOT)),
        "production_ledger_writer_active": True,
        "p0_f1_closed": True,
        "option_b_authorized": False,
        "wal_apply_authorized": False,
        "next_safe_step": NEXT,
        "git_head": "DYNAMIC_USE_GIT_REV_PARSE_HEAD",
        "updated_at_utc": timestamp,
    }
    runtime["current_state"] = {
        "project_status": "ACTIVE",
        "runtime_status": "WORK_UNIT_CLOSED",
        "mode": "ERA55A27_OPTION_B_DEFERRED",
        "last_action": {
            "task": WORK_UNIT,
            "result": RESULT,
            "artifact": str(ARTIFACT.relative_to(ROOT)),
            "timestamp": timestamp,
        },
        "current_problem": runtime["current_problem"],
        "next_safe_step": {
            "id": NEXT,
            "status": "READY",
            "human_authorization_required": True,
            "option_b_authorized": False,
            "wal_apply_authorized": False,
            "purpose": "Select the highest-value strategic project line after deferring Option B.",
        },
        "updated_at": timestamp,
    }
    runtime["current_work_unit"] = {
        "id": WORK_UNIT,
        "status": "CLOSED_OPTION_B_DEFERRED",
        "result": RESULT,
        "artifact": str(ARTIFACT.relative_to(ROOT)),
        "production_mutation": False,
        "next_step": NEXT,
    }
    atomic_json(RUNTIME, runtime)

    history = load(HISTORY)
    events = history.setdefault("events", [])
    event_id = "ERA55A27_OPTION_B_DEFERRED"
    if not any(isinstance(item, dict) and item.get("event_id") == event_id for item in events):
        events.append({
            "event_id": event_id,
            "timestamp_utc": timestamp,
            "era": "ERA55",
            "work_unit": WORK_UNIT,
            "event": "WAL_READINESS_ROLLBACK_AND_OPPORTUNITY_COST_DECISION",
            "status": "CLOSED_OPTION_B_DEFERRED",
            "result": RESULT,
            "artifact": str(ARTIFACT.relative_to(ROOT)),
            "decision": final_decision,
            "production_mutation": False,
            "wal_apply_authorized": False,
            "next_safe_step": NEXT,
        })
    history["updated_at"] = timestamp
    history["updated_at_utc"] = timestamp
    atomic_json(HISTORY, history)

    master = MASTER.read_text(encoding="utf-8")
    master = section(master, "## 01 PROJECT STATUS", """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
CURRENT_HUMAN_SUMMARY=06_PROJECT_MASTER_STATE.md
GIT_BRANCH=main
GIT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD
BOOT_HEALTH=100/100
```""")
    master = section(master, "## 02 CURRENT MAJOR-LINE POSITION", f"""```text
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_LEDGER_WRITER_ACTIVE=true
P0_F1_CLOSED=true
OPTION_B_DECISION=DEFER_OPTION_B
WAL_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
```

A26 proved strong sandbox benefit. A27 deferred production WAL because migration security, rollback, economics and opportunity-cost superiority are not proven.""")
    master = section(master, "## 03 LAST VERIFIED WORK", f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS=CLOSED_OPTION_B_DEFERRED
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}""")
    master = section(master, "## 09 OPEN RISKS AND DECISIONS", """- P0 F1 is closed and the guarded production writer remains active.
- WAL showed strong sandbox gains but production migration readiness is not proven.
- Service quiescence and lossless rollback remain unproven.
- Disk-full, interrupted transition and checkpoint interruption recovery remain unproven.
- Maintenance-window budget and year-one economics remain unproven.
- Opportunity-cost superiority over Hunter, Unknown Anomaly, Whale, Adversarial Intelligence and Fusion remains unproven.
- Option B production apply remains blocked.
- Runtime risk is minimized, never zero.
- Git HEAD must be read dynamically.""")
    master = section(master, "## 10 NEXT SAFE STEP", f"""```text
NEXT_SAFE_STEP={NEXT}
```

Select the highest-value strategic project line using speed, security, power, economy and opportunity-cost evidence. Do not apply WAL without a separate future authorization.""")
    MASTER.write_text(master, encoding="utf-8")

    handoff = HANDOFF.read_text(encoding="utf-8")
    handoff = section(handoff, "## 02 CURRENT CONTINUATION CHECKPOINT", f"""PROJECT_STATUS=ACTIVE_ERA55_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_LEDGER_WRITER_ACTIVE=true
P0_F1_CLOSED=true
OPTION_B_DECISION=DEFER_OPTION_B
WAL_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""")
    handoff = section(handoff, "## 03 LAST VERIFIED WORK", f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS=CLOSED_OPTION_B_DEFERRED
PRODUCTION_MUTATION=false
CURRENT_PROBLEM=POST_OPTION_B_STRATEGIC_PRIORITY_SELECTION_PENDING""")
    handoff = section(handoff, "## 07 ALLOWED NEXT DECISIONS", f"""- Guarded production writer: `ACTIVE`.
- P0 F1: `CLOSED`.
- Option B: `DEFERRED`.
- WAL production apply: `BLOCKED`.
- Strategic priority selection: `AUTHORIZED`.

NEXT_SAFE_STEP={NEXT}""")
    handoff = section(handoff, "## 08 NEXT SESSION EXECUTION RULE", """1. Confirm A27 evidence remains valid.
2. Compare the highest-value next lines using speed, security, power, economy and opportunity cost.
3. Prefer Hunter, Unknown Anomaly, Whale, Adversarial Intelligence or Fusion when evidence shows higher strategic value.
4. Do not apply WAL without a separate future authorization.
5. Keep the guarded production writer active and unchanged.""")
    HANDOFF.write_text(handoff, encoding="utf-8")

    marker = "## ERA55A_27 WAL READINESS, ROLLBACK AND OPPORTUNITY COST DECISION"
    almanac = ALMANAC.read_text(encoding="utf-8")
    if marker not in almanac:
        ALMANAC.write_text(almanac.rstrip() + f"\n\n---\n\n{marker}\n\n- Status: `CLOSED_OPTION_B_DEFERRED`\n- Result: `{RESULT}`\n- Decision: `DEFER_OPTION_B`\n- A26 P95 gain: `{decision['p95_latency_gain_percent']:.2f}%`\n- A26 throughput gain: `{decision['throughput_gain_percent']:.2f}%`\n- Production mutation: `false`\n- WAL apply authorized: `false`\n- Next safe step: `{NEXT}`\n", encoding="utf-8")

    db_stat_after = PRODUCTION_DB.stat()
    if (db_stat_before.st_size, db_stat_before.st_mtime_ns) != (db_stat_after.st_size, db_stat_after.st_mtime_ns):
        raise RuntimeError("A27_PRODUCTION_DB_CHANGED")
    if unit_state(SERVICE).get("InvocationID") != service_before.get("InvocationID"):
        raise RuntimeError("A27_SERVICE_INVOCATION_CHANGED")
    if unit_state(TIMER).get("InvocationID") != timer_before.get("InvocationID"):
        raise RuntimeError("A27_TIMER_INVOCATION_CHANGED")

    git("add", str(ARTIFACT.relative_to(ROOT)), str(RUNTIME.relative_to(ROOT)), str(HISTORY.relative_to(ROOT)), str(MASTER.relative_to(ROOT)), str(HANDOFF.relative_to(ROOT)), str(ALMANAC.relative_to(ROOT)))
    run(["git", "add", "-f", str(REPORT.relative_to(ROOT))])
    if not git("diff", "--cached", "--name-only"):
        raise RuntimeError("A27_NO_STAGED_CHANGES")
    git("diff", "--cached", "--check")
    git("commit", "-m", SUBJECT)

    print("ERA55A27_DECISION=SUCCESS")
    print("DECISION=DEFER_OPTION_B")
    print("A26_SANDBOX_BENEFIT=STRONG_POSITIVE")
    print("WAL_APPLY_AUTHORIZED=false")
    print("PRODUCTION_MUTATION=false")
    print("NEXT_SAFE_STEP=" + NEXT)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
