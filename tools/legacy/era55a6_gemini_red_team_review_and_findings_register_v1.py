#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
WORK_UNIT = "ERA55A_6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER"
RESULT = "BASELINE_ACCEPTED_OPTIMIZATION_REJECTED_UNTIL_P0_CLEARED"
A5_REL = "data/control/era55a5_baseline_report_and_gemini_red_team_package_v1.json"
ARTIFACT_REL = "data/control/era55a6_gemini_red_team_review_and_findings_register_v1.json"
REPORT_REL = "reports/LATEST_ERA55A6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER.md"
NEXT_SAFE_STEP = "ERA55A_7_P0_DROP_LEDGER_DESIGN_AND_TEMP_COPY_TEST"
REVIEWED_HEAD = "c916660b1f1047370d04893a504d7867fd7597c5"
CANONICAL = [
    "PROJECT_RUNTIME.json",
    "PROJECT_HISTORY.json",
    "data/tokenoskobi_v1_v8_master_era_roadmap.json",
    "04_ALMANAC.md",
    "06_PROJECT_MASTER_STATE.md",
    "07_PROJECT_HANDOFF.md",
]
GENERATED = [ARTIFACT_REL, REPORT_REL]
FORCE_ADD = {REPORT_REL}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if check and cp.returncode:
        raise RuntimeError(
            "COMMAND_FAILED="
            + json.dumps(
                {"cmd": cmd, "rc": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr},
                ensure_ascii=False,
            )
        )
    return cp


def git(*args: str) -> str:
    return run(["git", *args]).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED={path}")
    return value


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def write_json(path: Path, value: dict[str, Any]) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def replace_section(text: str, heading: str, body: str) -> str:
    match = re.search(rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)", text, re.S)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND={heading}")
    return text[: match.start()] + heading + "\n\n" + body.rstrip() + "\n" + text[match.end() :]


def require_preconditions() -> str:
    os.chdir(ROOT)
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BLOCKED=BRANCH_NOT_MAIN")
    if git("status", "--porcelain"):
        raise RuntimeError("BLOCKED=WORKTREE_NOT_CLEAN")
    runtime = load(ROOT / "PROJECT_RUNTIME.json")
    if runtime.get("current_era") != "ERA55":
        raise RuntimeError("BLOCKED=CURRENT_ERA_NOT_ERA55")
    if (runtime.get("era55_status") or {}).get("status") != "OPEN":
        raise RuntimeError("BLOCKED=ERA55_NOT_OPEN")
    if (runtime.get("next_safe_step") or {}).get("id") != WORK_UNIT:
        raise RuntimeError("BLOCKED=UNEXPECTED_NEXT_SAFE_STEP")
    a5 = load(ROOT / A5_REL)
    if a5.get("status") != "PACKAGE_READY_REVIEW_PENDING":
        raise RuntimeError("BLOCKED=A5_STATUS_INVALID")
    if a5.get("result") != "OK_BASELINE_REPORT_AND_GEMINI_PACKAGE_READY_NO_APPLY":
        raise RuntimeError("BLOCKED=A5_RESULT_INVALID")
    return git("rev-parse", "HEAD")


def build_register(ts: str, head: str, a5: dict[str, Any]) -> dict[str, Any]:
    baseline = a5["baseline"]
    queue = baseline["queue_boundary"]
    runtime = baseline["low_load_operational_stability"]
    sqlite_state = baseline["sqlite"]
    cold = baseline["cold_start"]
    panel = baseline["panel_propagation"]

    if queue["capacity"] != 50 or queue["candidates"] != 50:
        raise RuntimeError("BLOCKED=QUEUE_BASELINE_CHANGED")
    if queue["drop_ledger_detected"] is not False:
        raise RuntimeError("BLOCKED=DROP_LEDGER_STATE_CHANGED")
    if queue["silent_drop_capability_confirmed"] is not True:
        raise RuntimeError("BLOCKED=TRUNCATION_CAPABILITY_NOT_CONFIRMED")

    findings = [
        {
            "finding_id": "F1",
            "priority": "P0",
            "title": "SILENT_TRUNCATION_DISPOSITION_BLINDNESS",
            "received_finding": "Queue is 50/50 and no drop ledger exists.",
            "canonical_interpretation": "CURRENT_OVERFLOW_NOT_OBSERVED_BUT_TOP50_SILENT_TRUNCATION_CAPABILITY_PROVEN",
            "evidence": {
                "capacity": queue["capacity"],
                "candidates": queue["candidates"],
                "admitted": queue["admitted"],
                "overflow_current_snapshot": queue["overflow_current_snapshot"],
                "drop_ledger_detected": queue["drop_ledger_detected"],
                "silent_drop_current_snapshot": queue["silent_drop_observed_current_snapshot"],
                "silent_truncation_capability": queue["silent_drop_capability_confirmed"],
                "historical_zero_loss_claim_allowed": queue["historical_zero_loss_claim_allowed"],
            },
            "required_action": "ATOMIC_DISPOSITION_LEDGER_DESIGN_AND_TEMP_COPY_VALIDATION",
            "blocks_production_apply": True,
            "status": "OPEN",
        },
        {
            "finding_id": "F2",
            "priority": "P1",
            "title": "DELETE_VS_WAL_IO_HYPOTHESIS",
            "canonical_interpretation": "HYPOTHESIS_UNPROVEN_TEMP_COPY_COMPARISON_REQUIRED",
            "evidence": {
                "runner_ms": runtime["precise_natural_runner_ms"],
                "journal_mode": sqlite_state["journal_mode"],
                "synchronous": sqlite_state["synchronous"],
            },
            "required_action": "TEMP_COPY_DELETE_VS_WAL_DURABILITY_LOCK_WRITE_AMPLIFICATION_BENCHMARK",
            "blocks_production_apply": True,
            "status": "OPEN",
        },
        {
            "finding_id": "F3",
            "priority": "P1",
            "title": "ATOMIC_KILL_RECOVERY_UNTESTED",
            "canonical_interpretation": "LOW_LOAD_FAILURE_NOT_OBSERVED_BUT_KILL_RECOVERY_UNTESTED",
            "evidence": {
                "service_timeout_ms": runtime["service_timeout_ms"],
                "timeout_observed": runtime["service_timeout_observed_24h"],
                "overlap_observed": runtime["timer_overlap_observed_24h"],
                "cold_start": cold["classification"],
            },
            "required_action": "ISOLATED_TEMP_COPY_PROCESS_KILL_ATOMIC_RECOVERY_MATRIX",
            "blocks_production_apply": True,
            "status": "OPEN",
        },
        {
            "finding_id": "F4",
            "priority": "P2",
            "title": "STAGE_TIMING_AND_PANEL_LATENCY_GAP",
            "canonical_interpretation": "ONE_PRECISE_TOTAL_SAMPLE_EXISTS_STAGE_P95_P99_AND_PANEL_LATENCY_NOT_PROVEN",
            "evidence": {
                "runner_ms": runtime["precise_natural_runner_ms"],
                "panel_status": panel["status"],
                "exact_stage_latency_available": panel["exact_stage_latency_available"],
            },
            "required_action": "PERF_COUNTER_NS_STAGE_AND_DB_TO_PANEL_PROPAGATION_INSTRUMENTATION",
            "blocks_production_apply": True,
            "status": "OPEN",
        },
    ]

    return {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "era": "ERA55",
        "registered_at_utc": ts,
        "status": "CLOSED_FINDINGS_REGISTERED",
        "result": RESULT,
        "head_before_commit": head,
        "review_source": {
            "reviewer": "GEMINI_RED_TEAM",
            "canonical_head_reviewed": REVIEWED_HEAD,
            "source_artifact": A5_REL,
        },
        "verdict": {
            "baseline_verdict": "BASELINE_ACCEPTED",
            "canonical_assessment": "OPERATIONALLY_STABLE_LOW_LOAD_WITH_BOUNDARY_RISKS",
            "optimization_apply_verdict": "REJECTED_UNTIL_P0_CLEARED",
            "a7_design_and_temp_copy_test_authorized": True,
            "production_apply_authorized": False,
        },
        "findings": findings,
        "hard_gates": {
            "event_count_loss": 0,
            "uid_loss": 0,
            "duplicate_regression": 0,
            "integrity_check": "ok",
            "quick_check": "ok",
            "authority_regression": 0,
            "unledgered_disposition": 0,
        },
        "authorized_next_work": {
            "id": NEXT_SAFE_STEP,
            "temp_copy_required": True,
            "overflow_simulation_required": True,
            "production_mutation_authorized": False,
            "every_overflow_reason_code": "QUEUE_OVERFLOW",
        },
        "next_safe_step": NEXT_SAFE_STEP,
        "mutation_statement": {
            "live_runtime": False,
            "production_database": False,
            "service": False,
            "timer": False,
            "panel": False,
            "queue_policy": False,
        },
    }


def report(register: dict[str, Any]) -> str:
    rows = "\n".join(
        f"- **{f['finding_id']} [{f['priority']}] {f['title']}** — `{f['canonical_interpretation']}`; required `{f['required_action']}`."
        for f in register["findings"]
    )
    return f"""# ERA55A_6 GEMINI RED TEAM REVIEW AND FINDINGS REGISTER

Result: `{RESULT}`

Baseline verdict: `BASELINE_ACCEPTED`

Optimization apply verdict: `REJECTED_UNTIL_P0_CLEARED`

## Findings

{rows}

F1 does not assert an observed drop in the measured snapshot. It records a proven top-50 silent-truncation capability and the absence of historical loss evidence.

## Hard Gates

```json
{json.dumps(register['hard_gates'], ensure_ascii=False, indent=2)}
```

## Authorized Next Work

```json
{json.dumps(register['authorized_next_work'], ensure_ascii=False, indent=2)}
```

## Next Safe Step

`{NEXT_SAFE_STEP}`

Production optimization remains blocked.
"""


def update_runtime(ts: str) -> None:
    path = ROOT / "PROJECT_RUNTIME.json"
    data = load(path)
    work = {
        "id": WORK_UNIT,
        "type": "ERA55_EXTERNAL_RED_TEAM_REVIEW_REGISTER",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "artifact": ARTIFACT_REL,
        "report": REPORT_REL,
        "status": "CLOSED",
        "result": RESULT,
        "runtime_db_service_timer_panel_mutation": False,
        "next_step": NEXT_SAFE_STEP,
    }
    next_step = {
        "id": NEXT_SAFE_STEP,
        "type": "ERA55_P0_DROP_LEDGER_DESIGN_TEMP_COPY_TEST",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "purpose": "Design and validate an atomic disposition ledger only on a disposable SQLite copy.",
        "temp_copy_required": True,
        "production_mutation_authorized": False,
        "optimization_apply_authorized": False,
        "status": "READY",
    }
    action = {"timestamp": ts, "task": WORK_UNIT, "result": RESULT, "artifact": ARTIFACT_REL}
    data.update(
        {
            "mode": "ERA55A6_GEMINI_FINDINGS_REGISTERED",
            "project_status": "ACTIVE_ERA55_P0_DROP_LEDGER_TEMP_COPY_AUTHORIZED",
            "status": "WORK_UNIT_CLOSED",
            "last_completed": WORK_UNIT,
            "last_action": action,
            "recent_event": dict(action),
            "current_work_unit": work,
            "next_safe_step": next_step,
            "source": "era55a6_gemini_red_team_findings_register_v1",
            "updated_at": ts,
            "updated_at_utc": ts,
        }
    )
    state = data.setdefault("current_state", {})
    state.update(
        {
            "mode": data["mode"],
            "runtime_status": "WORK_UNIT_CLOSED",
            "project_status": "ACTIVE",
            "updated_at": ts,
            "last_action": dict(action),
            "active_work_unit": dict(work),
            "next_safe_step": dict(next_step),
            "current_problem": None,
        }
    )
    era = data.setdefault("era55_status", {})
    era.update(
        {
            "status": "OPEN",
            "active_stage": "ERA55A_P0_DROP_LEDGER",
            "last_completed_substep": WORK_UNIT,
            "next_safe_step": NEXT_SAFE_STEP,
            "a6_artifact": ARTIFACT_REL,
            "a6_report": REPORT_REL,
            "gemini_review_complete": True,
            "gemini_baseline_verdict": "BASELINE_ACCEPTED",
            "optimization_apply_verdict": "REJECTED_UNTIL_P0_CLEARED",
            "p0_queue_risk_open": True,
            "a7_temp_copy_test_authorized": True,
            "optimization_apply_authorized": False,
            "runtime_db_service_timer_panel_mutation": False,
        }
    )
    data["open_risks"] = [
        "P0:F1_SILENT_TRUNCATION_DISPOSITION_BLINDNESS:OPEN",
        "P1:F2_DELETE_VS_WAL_HYPOTHESIS:OPEN",
        "P1:F3_ATOMIC_KILL_RECOVERY:UNTESTED",
        "P2:F4_STAGE_TIMING_AND_PANEL_LATENCY:MISSING",
        "Risk is minimized, never zero.",
    ]
    write_json(path, data)


def update_roadmap(ts: str) -> None:
    path = ROOT / "data/tokenoskobi_v1_v8_master_era_roadmap.json"
    data = load(path)
    found = False
    for version in data.get("versions", []):
        if version.get("id") != "V3":
            continue
        for child in version.get("children", []):
            if child.get("id") == "ERA55":
                child.update(
                    {
                        "status": "OPEN",
                        "active_stage": "ERA55A_P0_DROP_LEDGER",
                        "last_completed_substep": WORK_UNIT,
                        "last_result": RESULT,
                        "next_safe_step": NEXT_SAFE_STEP,
                        "a6_artifact": ARTIFACT_REL,
                        "gemini_review_complete": True,
                        "gemini_baseline_verdict": "BASELINE_ACCEPTED",
                        "optimization_apply_verdict": "REJECTED_UNTIL_P0_CLEARED",
                        "p0_queue_risk_open": True,
                        "optimization_apply_authorized": False,
                    }
                )
                found = True
    if not found:
        raise RuntimeError("ERA55_NOT_FOUND_IN_ROADMAP_JSON")
    data.update({"updated_at": ts, "git_head": "DYNAMIC_USE_GIT_REV_PARSE_HEAD", "work_unit": WORK_UNIT})
    write_json(path, data)


def update_docs() -> None:
    master = ROOT / "06_PROJECT_MASTER_STATE.md"
    text = master.read_text(encoding="utf-8").replace(
        "PROJECT_STATUS=ACTIVE_ERA55_AWAITING_GEMINI_RED_TEAM_REVIEW",
        "PROJECT_STATUS=ACTIVE_ERA55_P0_DROP_LEDGER_TEMP_COPY_AUTHORIZED",
        1,
    )
    text = replace_section(
        text,
        "## 02 CURRENT MAJOR-LINE POSITION",
        """```text
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_DROP_LEDGER
LAST_COMPLETED_SUBSTEP=ERA55A_6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER
GEMINI_REVIEW_COMPLETE=true
GEMINI_BASELINE_VERDICT=BASELINE_ACCEPTED
OPTIMIZATION_APPLY_VERDICT=REJECTED_UNTIL_P0_CLEARED
P0_QUEUE_RISK_OPEN=true
A7_TEMP_COPY_TEST_AUTHORIZED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
```

A6 registered Gemini findings. Only A7 disposable-copy design and testing are authorized.""",
    )
    text = replace_section(
        text,
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_MUTATION=false
```

F1-F4 are registered with evidence limits preserved.""",
    )
    text = replace_section(
        text,
        "## 09 OPEN RISKS AND DECISIONS",
        """- `P0 F1 SILENT_TRUNCATION_DISPOSITION_BLINDNESS` remains open and blocks production apply.
- Current snapshot overflow is zero; historical zero-loss is unprovable without a ledger.
- F2 DELETE-vs-WAL is an unproven hypothesis.
- F3 kill/atomic recovery is untested.
- F4 stage timing and panel latency are incomplete.
- Production DB, service, timer, panel and queue policy remain immutable.
- Runtime risk is minimized, never zero.
- Git HEAD must be read dynamically.""",
    )
    text = replace_section(
        text,
        "## 10 NEXT SAFE STEP",
        f"""```text
NEXT_SAFE_STEP={NEXT_SAFE_STEP}
```

Design and test the disposition ledger only on a disposable SQLite copy.""",
    )
    write_text(master, text)

    handoff = ROOT / "07_PROJECT_HANDOFF.md"
    text = handoff.read_text(encoding="utf-8")
    text = replace_section(
        text,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        """PROJECT_STATUS=ACTIVE_ERA55_P0_DROP_LEDGER_TEMP_COPY_AUTHORIZED
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_DROP_LEDGER
LAST_COMPLETED_SUBSTEP=ERA55A_6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER
GEMINI_REVIEW_COMPLETE=true
GEMINI_BASELINE_VERDICT=BASELINE_ACCEPTED
OPTIMIZATION_APPLY_VERDICT=REJECTED_UNTIL_P0_CLEARED
P0_QUEUE_RISK_OPEN=true
A7_TEMP_COPY_TEST_AUTHORIZED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A6 is closed. A7 temp-copy work is the only authorized next step.""",
    )
    text = replace_section(
        text,
        "## 03 LAST VERIFIED WORK",
        f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=null""",
    )
    text = replace_section(
        text,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not reopen ERA54.
- Do not apply a ledger schema to production.
- Do not modify the live gateway, queue policy, service, timer or panel.
- Do not run production overflow, burst, kill, restart or WAL tests.
- Do not claim an observed drop from the zero-overflow snapshot.
- Do not proceed to production optimization while F1 remains open.""",
    )
    text = replace_section(
        text,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Gemini baseline verdict: `BASELINE_ACCEPTED`.
- Production optimization verdict: `REJECTED_UNTIL_P0_CLEARED`.
- A7 disposable-copy schema/test is authorized.
- All live apply authority remains false.

NEXT_SAFE_STEP={NEXT_SAFE_STEP}""",
    )
    text = replace_section(
        text,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A7 is current.
2. Snapshot production DB and runtime-state hashes.
3. Create a disposable SQLite backup through a read-only source connection.
4. Apply the candidate ledger schema only to the copy.
5. Simulate overflow and every disposition.
6. Test rollback, uniqueness and foreign keys.
7. Verify event counts, UID sets and production hashes are unchanged.
8. Do not apply to production.""",
    )
    write_text(handoff, text)


def update_history_almanac(ts: str, head: str) -> None:
    path = ROOT / "PROJECT_HISTORY.json"
    data = load(path)
    events = data.get("events")
    if not isinstance(events, list):
        raise RuntimeError("PROJECT_HISTORY_EVENTS_INVALID")
    event_id = "ERA55A6_GEMINI_RED_TEAM_FINDINGS_REGISTER_V1"
    if not any(isinstance(x, dict) and x.get("event_id") == event_id for x in events):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": ts,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "GEMINI_RED_TEAM_REVIEW_REGISTERED",
                "status": "CLOSED",
                "result": RESULT,
                "head_before_commit": head,
                "artifact": ARTIFACT_REL,
                "report": REPORT_REL,
                "baseline_verdict": "BASELINE_ACCEPTED",
                "optimization_apply_verdict": "REJECTED_UNTIL_P0_CLEARED",
                "finding_ids": ["F1", "F2", "F3", "F4"],
                "next_safe_step": NEXT_SAFE_STEP,
            }
        )
    data.update({"updated_at": ts, "updated_at_utc": ts})
    write_json(path, data)

    path = ROOT / "04_ALMANAC.md"
    text = path.read_text(encoding="utf-8")
    heading = "## ERA55A_6 GEMINI RED TEAM REVIEW AND FINDINGS REGISTER"
    if heading not in text:
        marker = "\n---\n\n## ALMANAC RECORD INSERTION AND CORRECTION CONSTITUTION"
        if text.count(marker) != 1:
            raise RuntimeError("ALMANAC_INSERTION_MARKER_INVALID")
        entry = f"""
---

{heading}

- Status: `CLOSED`
- Result: `{RESULT}`
- Baseline verdict: `BASELINE_ACCEPTED`
- Production optimization verdict: `REJECTED_UNTIL_P0_CLEARED`
- Findings: `F1 P0`, `F2 P1`, `F3 P1`, `F4 P2`
- A7 temp-copy design/test: `AUTHORIZED`
- Production apply: `false`
- Next safe step: `{NEXT_SAFE_STEP}`
"""
        write_text(path, text.replace(marker, entry + marker, 1))


def commit_local() -> str:
    expected = sorted(set(CANONICAL + GENERATED))
    visible_expected = set(expected) - FORCE_ADD
    actual = {
        line for line in git("diff", "--name-only").splitlines() if line.strip()
    } | {
        line for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line.strip()
    }
    if actual != visible_expected:
        raise RuntimeError("UNEXPECTED_CHANGED_FILES=" + json.dumps(sorted(actual)))
    run(["git", "diff", "--check"])
    normal = sorted(set(expected) - FORCE_ADD)
    run(["git", "add", "--", *normal])
    run(["git", "add", "-f", "--", *sorted(FORCE_ADD)])
    staged = sorted(x for x in git("diff", "--cached", "--name-only").splitlines() if x.strip())
    if staged != expected:
        raise RuntimeError("STAGED_FILES_MISMATCH")
    git("commit", "-m", "ERA55A6_GEMINI_RED_TEAM_REGISTER | OK | P0_APPLY_BLOCKED")
    if git("status", "--porcelain"):
        raise RuntimeError("POST_COMMIT_WORKTREE_NOT_CLEAN")
    return git("rev-parse", "HEAD")


def main() -> int:
    head = require_preconditions()
    backup = Path(tempfile.mkdtemp(prefix="era55a6_backup_", dir="/tmp"))
    for rel in CANONICAL:
        src = ROOT / rel
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    committed = False
    try:
        ts = now()
        a5 = load(ROOT / A5_REL)
        register = build_register(ts, head, a5)
        write_json(ROOT / ARTIFACT_REL, register)
        write_text(ROOT / REPORT_REL, report(register))
        update_runtime(ts)
        update_roadmap(ts)
        update_docs()
        update_history_almanac(ts, head)
        for rel in (ARTIFACT_REL, "PROJECT_RUNTIME.json", "PROJECT_HISTORY.json", "data/tokenoskobi_v1_v8_master_era_roadmap.json"):
            load(ROOT / rel)
        commit = commit_local()
        committed = True
        print("ERA55A6_GEMINI_RED_TEAM_REGISTER=SUCCESS")
        print(f"RESULT={RESULT}")
        print(f"LOCAL_COMMIT={commit}")
        print("BASELINE_VERDICT=BASELINE_ACCEPTED")
        print("OPTIMIZATION_APPLY_VERDICT=REJECTED_UNTIL_P0_CLEARED")
        print("FINDINGS=F1_P0,F2_P1,F3_P1,F4_P2")
        print("P0_F1_STATUS=OPEN")
        print("A7_TEMP_COPY_TEST_AUTHORIZED=true")
        print("PRODUCTION_APPLY_AUTHORIZED=false")
        print("LIVE_RUNTIME_MUTATION=false")
        print(f"NEXT_SAFE_STEP={NEXT_SAFE_STEP}")
        print(f"ARTIFACT={ARTIFACT_REL}")
        print(f"REPORT={REPORT_REL}")
        print("WORKTREE=CLEAN")
        return 0
    except Exception:
        if not committed:
            run(["git", "reset", "--mixed", "HEAD"], check=False)
            for rel in CANONICAL:
                src = backup / rel
                dst = ROOT / rel
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            for rel in GENERATED:
                path = ROOT / rel
                if path.exists():
                    path.unlink()
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERA55A6_GEMINI_RED_TEAM_REGISTER=FAILED:{exc}", file=sys.stderr)
        raise
