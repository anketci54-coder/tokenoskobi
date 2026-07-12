#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
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


def validate_a26(data: dict[str, Any]) -> dict[str, bool]:
    decision = data["decision"]
    delete = data["delete_variant"]
    wal = data["wal_variant"]
    dr = data["delete_recovery"]
    wr = data["wal_recovery"]
    checks = {
        "temp_copy_only": data.get("status") == "COMPLETED_TEMP_COPY_ONLY",
        "production_mutation_false": data.get("production_mutation") is False,
        "production_apply_false": data.get("production_apply_authorized") is False,
        "correctness_ok": decision.get("correctness_ok") is True,
        "materially_faster": decision.get("materially_faster") is True,
        "p95_gain_material": float(decision.get("p95_latency_gain_percent", 0)) >= 15.0,
        "throughput_gain_material": float(decision.get("throughput_gain_percent", 0)) >= 20.0,
        "delete_integrity_ok": delete["integrity"].get("integrity_check") == "ok",
        "wal_integrity_ok": wal["integrity"].get("integrity_check") == "ok",
        "wal_errors_zero": all(wal.get(k) == 0 for k in ("busy_or_locked_errors", "sqlite_io_errors", "sqlite_corrupt_errors")),
        "delete_recovery_ok": not dr.get("sqlite_corrupt_detected") and not dr.get("sqlite_ioerr_detected"),
        "wal_recovery_ok": not wr.get("sqlite_corrupt_detected") and not wr.get("sqlite_ioerr_detected"),
    }
    if not all(checks.values()):
        raise RuntimeError("A27_A26_EVIDENCE_INVALID:" + ",".join(k for k, v in checks.items() if not v))
    return checks


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


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else A26_DEFAULT
    if not source.is_file():
        raise RuntimeError(f"A27_A26_ARTIFACT_MISSING:{source}")
    if git("status", "--short"):
        raise RuntimeError("A27_WORKTREE_NOT_CLEAN")
    expected = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()
    if expected and git("rev-parse", "HEAD") != expected:
        raise RuntimeError("A27_HEAD_MISMATCH")

    a26 = load(source)
    checks = validate_a26(a26)
    decision = a26["decision"]

    # Validate all target headings before any write.
    master_original = MASTER.read_text(encoding="utf-8")
    handoff_original = HANDOFF.read_text(encoding="utf-8")
    for heading in ("## 01 PROJECT STATUS", "## 02 CURRENT MAJOR-LINE POSITION", "## 03 LAST VERIFIED WORK", "## 09 OPEN RISKS AND DECISIONS", "## 10 NEXT SAFE STEP"):
        if heading not in master_original:
            raise RuntimeError(f"A27_MASTER_HEADING_MISSING:{heading}")
    for heading in ("## 02 CURRENT CONTINUATION CHECKPOINT", "## 03 LAST VERIFIED WORK", "## 07 ALLOWED NEXT DECISIONS", "## 08 NEXT SESSION EXECUTION RULE"):
        if heading not in handoff_original:
            raise RuntimeError(f"A27_HANDOFF_HEADING_MISSING:{heading}")

    backup_root, copies = backup()
    try:
        timestamp = now()
        artifact_rel = str(ARTIFACT.relative_to(ROOT))
        final_decision = "DEFER_OPTION_B"
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
                "human_final_authority": True,
            },
            "next_safe_step": NEXT,
        }
        atomic_json(ARTIFACT, artifact)

        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(f"""# ERA55A27 WAL READINESS, ROLLBACK AND OPPORTUNITY COST DECISION

- Status: `CLOSED_OPTION_B_DEFERRED`
- Result: `{RESULT}`
- Decision: `DEFER_OPTION_B`
- A26 P95 gain: `{decision['p95_latency_gain_percent']:.2f}%`
- A26 throughput gain: `{decision['throughput_gain_percent']:.2f}%`
- Production mutation: `false`
- WAL apply authorized: `false`

WAL produced strong sandbox gains, but production migration security, rollback, economics and opportunity-cost superiority remain unproven.
""", encoding="utf-8")

        runtime = load(RUNTIME)
        runtime["current_era"] = "ERA55"
        runtime["current_era_status"] = "OPEN"
        runtime["current_problem"] = {"code": "POST_OPTION_B_STRATEGIC_PRIORITY_SELECTION_PENDING", "severity": "P1", "evidence": artifact_rel}
        runtime["canonical_runtime_pointer"] = {
            "authority": "PROJECT_RUNTIME.json",
            "project_status": "ACTIVE_ERA55_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING",
            "current_version_line": "V3_RUNTIME_INTELLIGENCE_OS",
            "current_era": "ERA55_RUNTIME_OPTIMIZATION",
            "current_stage": "ERA55A_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING",
            "last_completed": WORK_UNIT,
            "last_result": RESULT,
            "last_artifact": artifact_rel,
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
            "last_action": {"task": WORK_UNIT, "result": RESULT, "artifact": artifact_rel, "timestamp": timestamp},
            "current_problem": runtime["current_problem"],
            "next_safe_step": {"id": NEXT, "status": "READY", "human_authorization_required": True, "option_b_authorized": False, "wal_apply_authorized": False},
            "updated_at": timestamp,
        }
        runtime["current_work_unit"] = {"id": WORK_UNIT, "status": "CLOSED_OPTION_B_DEFERRED", "result": RESULT, "artifact": artifact_rel, "production_mutation": False, "next_step": NEXT}
        atomic_json(RUNTIME, runtime)

        history = load(HISTORY)
        events = history.setdefault("events", [])
        if not any(isinstance(e, dict) and e.get("event_id") == "ERA55A27_OPTION_B_DEFERRED" for e in events):
            events.append({"event_id": "ERA55A27_OPTION_B_DEFERRED", "timestamp_utc": timestamp, "era": "ERA55", "work_unit": WORK_UNIT, "status": "CLOSED_OPTION_B_DEFERRED", "result": RESULT, "artifact": artifact_rel, "decision": final_decision, "production_mutation": False, "next_safe_step": NEXT})
        history["updated_at"] = timestamp
        history["updated_at_utc"] = timestamp
        atomic_json(HISTORY, history)

        master = replace_section(master_original, "## 01 PROJECT STATUS", """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
CURRENT_HUMAN_SUMMARY=06_PROJECT_MASTER_STATE.md
GIT_BRANCH=main
GIT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD
BOOT_HEALTH=100/100
```""")
        master = replace_section(master, "## 02 CURRENT MAJOR-LINE POSITION", f"""```text
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
        master = replace_section(master, "## 03 LAST VERIFIED WORK", f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={artifact_rel}
WORK_UNIT_STATUS=CLOSED_OPTION_B_DEFERRED
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}""")
        master = replace_section(master, "## 09 OPEN RISKS AND DECISIONS", """- P0 F1 is closed and the guarded production writer remains active.
- WAL showed strong sandbox gains but production migration readiness is not proven.
- Service quiescence and lossless rollback remain unproven.
- Disk-full, interrupted-transition and checkpoint-interruption recovery remain unproven.
- Maintenance-window budget and year-one economics remain unproven.
- Opportunity-cost superiority over higher-value intelligence lines remains unproven.
- Option B production apply remains blocked.
- Runtime risk is minimized, never zero.""")
        master = replace_section(master, "## 10 NEXT SAFE STEP", f"""```text
NEXT_SAFE_STEP={NEXT}
```

Select the highest-value strategic project line using speed, security, power, economy and opportunity-cost evidence. Do not apply WAL without separate future authorization.""")
        MASTER.write_text(master, encoding="utf-8")

        handoff = replace_section(handoff_original, "## 02 CURRENT CONTINUATION CHECKPOINT", f"""PROJECT_STATUS=ACTIVE_ERA55_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_OPTION_B_DEFERRED_PRIORITY_SELECTION_PENDING
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_LEDGER_WRITER_ACTIVE=true
P0_F1_CLOSED=true
OPTION_B_DECISION=DEFER_OPTION_B
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
- Option B: `DEFERRED`.
- WAL production apply: `BLOCKED`.
- Strategic priority selection: `AUTHORIZED`.

NEXT_SAFE_STEP={NEXT}""")
        handoff = replace_section(handoff, "## 08 NEXT SESSION EXECUTION RULE", """1. Confirm A27 evidence remains valid.
2. Compare the highest-value next lines using speed, security, power, economy and opportunity cost.
3. Do not apply WAL without separate future authorization.
4. Keep the guarded production writer active and unchanged.""")
        HANDOFF.write_text(handoff, encoding="utf-8")

        marker = "## ERA55A_27 WAL READINESS, ROLLBACK AND OPPORTUNITY COST DECISION"
        almanac = ALMANAC.read_text(encoding="utf-8")
        if marker not in almanac:
            ALMANAC.write_text(almanac.rstrip() + f"\n\n---\n\n{marker}\n\n- Status: `CLOSED_OPTION_B_DEFERRED`\n- Result: `{RESULT}`\n- Decision: `DEFER_OPTION_B`\n- A26 P95 gain: `{decision['p95_latency_gain_percent']:.2f}%`\n- A26 throughput gain: `{decision['throughput_gain_percent']:.2f}%`\n- Production mutation: `false`\n- WAL apply authorized: `false`\n- Next safe step: `{NEXT}`\n", encoding="utf-8")

        git("add", artifact_rel, str(RUNTIME.relative_to(ROOT)), str(HISTORY.relative_to(ROOT)), str(MASTER.relative_to(ROOT)), str(HANDOFF.relative_to(ROOT)), str(ALMANAC.relative_to(ROOT)))
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
