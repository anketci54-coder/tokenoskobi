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
EXPECTED_A5_HEAD = "c916660b1f1047370d04893a504d7867fd7597c5"

CANONICAL_FILES = [
    "PROJECT_RUNTIME.json",
    "PROJECT_HISTORY.json",
    "data/tokenoskobi_v1_v8_master_era_roadmap.json",
    "04_ALMANAC.md",
    "06_PROJECT_MASTER_STATE.md",
    "07_PROJECT_HANDOFF.md",
]
GENERATED_FILES = [ARTIFACT_REL, REPORT_REL]
FORCE_ADD = {REPORT_REL}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(cmd: list[str], *, timeout: int = 180, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            "COMMAND_FAILED="
            + json.dumps(
                {
                    "cmd": cmd,
                    "rc": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                },
                ensure_ascii=False,
            )
        )
    return completed


def git(*args: str, timeout: int = 180) -> str:
    return run(["git", *args], timeout=timeout).stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED={path}")
    return value


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)", re.S)
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND={heading}")
    return text[: match.start()] + heading + "\n\n" + body.rstrip() + "\n" + text[match.end() :]


def preconditions() -> str:
    os.chdir(ROOT)
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BLOCKED=BRANCH_NOT_MAIN")
    status = git("status", "--porcelain")
    if status:
        raise RuntimeError("BLOCKED=WORKTREE_NOT_CLEAN\n" + status)
    local_head = git("rev-parse", "HEAD")
    runtime = load_json(ROOT / "PROJECT_RUNTIME.json")
    if runtime.get("current_era") != "ERA55":
        raise RuntimeError("BLOCKED=CURRENT_ERA_NOT_ERA55")
    if (runtime.get("era55_status") or {}).get("status") != "OPEN":
        raise RuntimeError("BLOCKED=ERA55_NOT_OPEN")
    next_step = runtime.get("next_safe_step") or {}
    if next_step.get("id") != WORK_UNIT:
        raise RuntimeError(f"BLOCKED=UNEXPECTED_NEXT_SAFE_STEP:{next_step.get('id')}")
    a5 = load_json(ROOT / A5_REL)
    if a5.get("head_before_commit") is None:
        raise RuntimeError("BLOCKED=A5_HEAD_EVIDENCE_MISSING")
    if a5.get("status") != "PACKAGE_READY_REVIEW_PENDING":
        raise RuntimeError(f"BLOCKED=A5_STATUS_INVALID:{a5.get('status')}")
    if a5.get("result") != "OK_BASELINE_REPORT_AND_GEMINI_PACKAGE_READY_NO_APPLY":
        raise RuntimeError(f"BLOCKED=A5_RESULT_INVALID:{a5.get('result')}")
    if (a5.get("decision") or {}).get("optimization_apply_authorized") is not False:
        raise RuntimeError("BLOCKED=A5_OPTIMIZATION_GUARD_INVALID")
    return local_head


def build_register(registered_at: str, head_before: str, a5: dict[str, Any]) -> dict[str, Any]:
    queue = ((a5.get("baseline") or {}).get("queue_boundary") or {})
    runtime = ((a5.get("baseline") or {}).get("low_load_operational_stability") or {})
    sqlite_data = ((a5.get("baseline") or {}).get("sqlite") or {})
    cold = ((a5.get("baseline") or {}).get("cold_start") or {})
    panel = ((a5.get("baseline") or {}).get("panel_propagation") or {})

    if queue.get("capacity") != 50 or queue.get("candidates") != 50:
        raise RuntimeError("BLOCKED=A5_QUEUE_BASELINE_CHANGED")
    if queue.get("drop_ledger_detected") is not False:
        raise RuntimeError("BLOCKED=A5_DROP_LEDGER_STATE_CHANGED")
    if queue.get("silent_truncation_capability_confirmed") is not True:
        raise RuntimeError("BLOCKED=A5_TRUNCATION_CAPABILITY_NOT_CONFIRMED")

    findings = [
        {
            "finding_id": "F1",
            "priority": "P0",
            "title": "ISTIHBARAT_KAYBI_KORLUGU_SILENT_TRUNCATION",
            "received_finding": "Kuyruk 50/50 kapasitededir. Yeni aday geldiğinde top-50 dışında kalan düşük öncelikli istihbarat görünür bir disposition kaydı olmadan çıktıdan elenebilir.",
            "canonical_evidence": {
                "queue_capacity": queue.get("capacity"),
                "candidate_count": queue.get("candidates"),
                "admitted_count": queue.get("admitted"),
                "overflow_current_snapshot": queue.get("overflow_current_snapshot"),
                "drop_ledger_detected": queue.get("drop_ledger_detected"),
                "silent_drop_current_snapshot": queue.get("silent_drop_observed_current_snapshot"),
                "silent_truncation_capability": queue.get("silent_truncation_capability_confirmed"),
                "historical_zero_loss_claim_allowed": queue.get("historical_zero_loss_claim_allowed"),
            },
            "canonical_interpretation": "CURRENT_OVERFLOW_NOT_OBSERVED_BUT_TOP50_SILENT_TRUNCATION_CAPABILITY_PROVEN",
            "blocks_production_optimization_apply": True,
            "required_action": "DESIGN_AND_TEMP_COPY_VALIDATE_ATOMIC_DISPOSITION_LEDGER",
            "status": "OPEN",
        },
        {
            "finding_id": "F2",
            "priority": "P1",
            "title": "IO_DARBOGAZI_HIPOTEZI_DELETE_VS_WAL",
            "received_finding": "939 ms runner süresinde journal_mode=delete kaynaklı write amplification olup olmadığı temp-copy üzerinde kanıtlanmalıdır.",
            "canonical_evidence": {
                "precise_natural_runner_ms": runtime.get("precise_natural_runner_ms"),
                "journal_mode": sqlite_data.get("journal_mode"),
                "synchronous": sqlite_data.get("synchronous"),
                "integrity_preserved": sqlite_data.get("integrity_preserved"),
            },
            "canonical_interpretation": "HYPOTHESIS_UNPROVEN_TEMP_COPY_COMPARISON_REQUIRED",
            "blocks_production_optimization_apply": True,
            "required_action": "TEMP_COPY_DELETE_VS_WAL_DURABILITY_LOCK_WRITE_AMPLIFICATION_BENCHMARK",
            "status": "OPEN",
        },
        {
            "finding_id": "F3",
            "priority": "P1",
            "title": "ATOMIC_RECOVERY_ZAFIYETI_UNTESTED",
            "received_finding": "Timeout, OOM veya SIGKILL sırasında DB-gateway-panel zincirinin atomik ve tutarlı kalıp kalmadığı belirsizdir.",
            "canonical_evidence": {
                "service_timeout_ms": runtime.get("service_timeout_ms"),
                "timeout_observed_24h": runtime.get("service_timeout_observed_24h"),
                "timer_overlap_observed_24h": runtime.get("timer_overlap_observed_24h"),
                "true_cold_start": cold.get("classification"),
            },
            "canonical_interpretation": "LOW_LOAD_FAILURE_NOT_OBSERVED_BUT_KILL_RECOVERY_UNTESTED",
            "blocks_production_optimization_apply": True,
            "required_action": "ISOLATED_TEMP_COPY_PROCESS_KILL_ATOMIC_RECOVERY_MATRIX",
            "status": "OPEN",
        },
        {
            "finding_id": "F4",
            "priority": "P2",
            "title": "ZAMAN_OLCUM_HASSASIYETI",
            "received_finding": "Optimizasyon kazanımlarının kanıtlanması için stage bazlı time.perf_counter_ns ölçümü gereklidir.",
            "canonical_evidence": {
                "precise_natural_runner_ms": runtime.get("precise_natural_runner_ms"),
                "panel_propagation_status": panel.get("status"),
                "panel_exact_stage_latency_available": panel.get("exact_stage_latency_available"),
            },
            "canonical_interpretation": "ONE_PRECISE_TOTAL_SAMPLE_EXISTS_STAGE_P95_P99_AND_PANEL_LATENCY_NOT_PROVEN",
            "blocks_production_optimization_apply": True,
            "required_action": "PERF_COUNTER_NS_STAGE_AND_DB_TO_PANEL_PROPAGATION_INSTRUMENTATION",
            "status": "OPEN",
        },
    ]

    return {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "era": "ERA55",
        "registered_at_utc": registered_at,
        "status": "CLOSED_FINDINGS_REGISTERED",
        "result": RESULT,
        "head_before_commit": head_before,
        "review_source": {
            "reviewer": "GEMINI_RED_TEAM",
            "source_artifact": A5_REL,
            "canonical_head_reviewed": EXPECTED_A5_HEAD,
            "submitted_review_type": "OFFICIAL_EXTERNAL_RED_TEAM_REPORT",
        },
        "verdict": {
            "baseline_verdict": "BASELINE_ACCEPTED",
            "canonical_assessment": "OPERATIONALLY_STABLE_LOW_LOAD_WITH_BOUNDARY_RISKS",
            "optimization_apply_verdict": "REJECTED_UNTIL_P0_CLEARED",
            "live_mutation_verified": False,
            "production_code_touch_authorized": False,
            "a7_design_and_temp_copy_test_authorized": True,
        },
        "findings": findings,
        "authorized_next_work": {
            "id": NEXT_SAFE_STEP,
            "purpose": "Design an atomic disposition ledger schema and validate deterministic overflow accounting only on a temp copy.",
            "production_db_mutation": False,
            "production_service_timer_panel_mutation": False,
            "temp_copy_required": True,
            "overflow_simulation_required": True,
            "event_count_loss_required": 0,
            "uid_loss_required": 0,
            "every_overflow_event_requires_reason_code": "QUEUE_OVERFLOW",
            "optimization_apply_authorized": False,
        },
        "hard_gates": {
            "event_count_loss": 0,
            "uid_loss": 0,
            "duplicate_regression": 0,
            "integrity_check": "ok",
            "quick_check": "ok",
            "authority_regression": 0,
            "unledgered_disposition": 0,
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


def make_report(register: dict[str, Any]) -> str:
    finding_lines = "\n".join(
        f"- **{item['finding_id']} [{item['priority']}] {item['title']}** — {item['canonical_interpretation']}. Required: `{item['required_action']}`."
        for item in register["findings"]
    )
    return f"""# ERA55A_6 GEMINI RED TEAM REVIEW AND FINDINGS REGISTER

Result: `{RESULT}`

Baseline verdict: `BASELINE_ACCEPTED`

Optimization apply verdict: `REJECTED_UNTIL_P0_CLEARED`

Live mutation: `false`

## Findings Register

{finding_lines}

## Evidence Discipline

F1 does not claim a drop in the measured snapshot. It records that the deterministic top-50 mechanism can silently truncate candidates and that historical zero-loss cannot be proven without a disposition ledger.

F2 remains a hypothesis until DELETE and WAL are compared on a disposable copy.

F3 remains untested until isolated failure injection proves atomic recovery.

F4 requires stage-level `time.perf_counter_ns()` and exact DB-to-panel propagation evidence before performance claims.

## Authorized Next Work

```json
{json.dumps(register['authorized_next_work'], ensure_ascii=False, indent=2)}
```

## Hard Gates

```json
{json.dumps(register['hard_gates'], ensure_ascii=False, indent=2)}
```

## Next Safe Step

`{NEXT_SAFE_STEP}`

No production optimization or runtime mutation is authorized.
"""


def update_runtime(registered_at: str) -> None:
    path = ROOT / "PROJECT_RUNTIME.json"
    data = load_json(path)
    work_unit = {
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
        "serves": "V3_RUNTIME_INTELLIGENCE_OS",
        "purpose": "Design the P0 disposition ledger and validate overflow accounting, atomic rollback and correctness on a disposable SQLite copy.",
        "human_authorization_required": True,
        "temp_copy_required": True,
        "production_mutation_authorized": False,
        "optimization_apply_authorized": False,
        "status": "READY",
    }
    last_action = {
        "timestamp": registered_at,
        "task": WORK_UNIT,
        "result": RESULT,
        "artifact": ARTIFACT_REL,
    }
    data["mode"] = "ERA55A6_GEMINI_FINDINGS_REGISTERED"
    data["project_status"] = "ACTIVE_ERA55_P0_DROP_LEDGER_TEMP_COPY_AUTHORIZED"
    data["status"] = "WORK_UNIT_CLOSED"
    data["last_completed"] = WORK_UNIT
    data["last_action"] = last_action
    data["recent_event"] = dict(last_action)
    data["current_work_unit"] = work_unit
    data["next_safe_step"] = next_step
    state = data.setdefault("current_state", {})
    state.update(
        {
            "mode": data["mode"],
            "runtime_status": "WORK_UNIT_CLOSED",
            "project_status": "ACTIVE",
            "updated_at": registered_at,
            "last_action": dict(last_action),
            "active_work_unit": dict(work_unit),
            "next_safe_step": dict(next_step),
            "current_problem": None,
        }
    )
    era55 = data.setdefault("era55_status", {})
    era55.update(
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
    data["source"] = "era55a6_gemini_red_team_findings_register_v1"
    data["updated_at"] = registered_at
    data["updated_at_utc"] = registered_at
    atomic_write_json(path, data)


def update_roadmap(registered_at: str) -> None:
    path = ROOT / "data/tokenoskobi_v1_v8_master_era_roadmap.json"
    data = load_json(path)
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
    data["updated_at"] = registered_at
    data["git_head"] = "DYNAMIC_USE_GIT_REV_PARSE_HEAD"
    data["work_unit"] = WORK_UNIT
    atomic_write_json(path, data)


def update_master() -> None:
    path = ROOT / "06_PROJECT_MASTER_STATE.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "PROJECT_STATUS=ACTIVE_ERA55_AWAITING_GEMINI_RED_TEAM_REVIEW",
        "PROJECT_STATUS=ACTIVE_ERA55_P0_DROP_LEDGER_TEMP_COPY_AUTHORIZED",
        1,
    )
    section_02 = """```text
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

Gemini accepted the measured baseline and rejected production optimization until the P0 disposition-blindness gate is cleared."""
    section_03 = f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_MUTATION=false
```

F1-F4 were registered with evidence limits preserved. A7 is authorized only for schema design and disposable temp-copy validation."""
    section_09 = """- `P0 F1 SILENT_TRUNCATION_DISPOSITION_BLINDNESS` is open and blocks production optimization apply.
- Current snapshot overflow remains zero; historical zero-loss remains unprovable without a ledger.
- `P1 F2 DELETE_VS_WAL` is an unproven hypothesis.
- `P1 F3 ATOMIC_KILL_RECOVERY` is untested.
- `P2 F4 STAGE_TIMING_AND_PANEL_LATENCY` is incomplete.
- Production DB, service, timer, panel, queue-policy and optimization mutations remain blocked.
- Runtime risk is minimized, never zero.
- Git HEAD must be read dynamically."""
    section_10 = f"""```text
NEXT_SAFE_STEP={NEXT_SAFE_STEP}
```

Design the disposition ledger and execute overflow, rollback, UID conservation and integrity tests only on a disposable SQLite copy. Do not apply the schema to production."""
    text = replace_section(text, "## 02 CURRENT MAJOR-LINE POSITION", section_02)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", section_03)
    text = replace_section(text, "## 09 OPEN RISKS AND DECISIONS", section_09)
    text = replace_section(text, "## 10 NEXT SAFE STEP", section_10)
    atomic_write_text(path, text)


def update_handoff() -> None:
    path = ROOT / "07_PROJECT_HANDOFF.md"
    text = path.read_text(encoding="utf-8")
    checkpoint = """PROJECT_STATUS=ACTIVE_ERA55_P0_DROP_LEDGER_TEMP_COPY_AUTHORIZED
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

A6 is closed. A7 temp-copy design/test is the only authorized next work."""
    last_work = f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=null

The review accepted the baseline and preserved F1 as the production-apply blocking P0 gate."""
    do_not = """- Do not reopen ERA54.
- Do not apply a ledger schema to the production database.
- Do not modify the live gateway, queue policy, service, timer or panel.
- Do not run production overflow, burst, kill, restart or WAL tests.
- Do not claim an observed drop from the zero-overflow A3 snapshot.
- Do not claim DELETE-mode causality without controlled comparison.
- Do not proceed to production optimization while F1 remains open."""
    decisions = f"""Current authorized direction:

- Gemini baseline verdict: `BASELINE_ACCEPTED`.
- Production optimization verdict: `REJECTED_UNTIL_P0_CLEARED`.
- A7 may design and test the disposition ledger only on a disposable copy.
- All live apply authority remains false.

NEXT_SAFE_STEP={NEXT_SAFE_STEP}"""
    execution = f"""1. Read `PROJECT_RUNTIME.json`.
2. Confirm `{NEXT_SAFE_STEP}` is current.
3. Verify A5 and A6 artifacts.
4. Snapshot production DB and runtime-state hashes.
5. Create a disposable SQLite copy through read-only backup.
6. Apply the candidate ledger schema only to the copy.
7. Simulate deterministic top-50 overflow and all disposition types.
8. Test atomic rollback and foreign-key/uniqueness enforcement.
9. Verify event counts, UID sets, integrity and production hashes are unchanged.
10. Produce the A7 report; do not apply to production."""
    text = replace_section(text, "## 02 CURRENT CONTINUATION CHECKPOINT", checkpoint)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", last_work)
    text = replace_section(text, "## 06 DO NOT REOPEN OR REPEAT", do_not)
    text = replace_section(text, "## 07 ALLOWED NEXT DECISIONS", decisions)
    text = replace_section(text, "## 08 NEXT SESSION EXECUTION RULE", execution)
    atomic_write_text(path, text)


def append_history(registered_at: str, head_before: str) -> None:
    path = ROOT / "PROJECT_HISTORY.json"
    data = load_json(path)
    events = data.get("events")
    if not isinstance(events, list):
        raise RuntimeError("PROJECT_HISTORY_EVENTS_INVALID")
    event_id = "ERA55A6_GEMINI_RED_TEAM_FINDINGS_REGISTER_V1"
    if not any(isinstance(item, dict) and item.get("event_id") == event_id for item in events):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": registered_at,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "GEMINI_RED_TEAM_REVIEW_REGISTERED",
                "status": "CLOSED",
                "result": RESULT,
                "head_before_commit": head_before,
                "artifact": ARTIFACT_REL,
                "report": REPORT_REL,
                "baseline_verdict": "BASELINE_ACCEPTED",
                "optimization_apply_verdict": "REJECTED_UNTIL_P0_CLEARED",
                "finding_ids": ["F1", "F2", "F3", "F4"],
                "live_runtime_mutation": False,
                "next_safe_step": NEXT_SAFE_STEP,
            }
        )
    data["updated_at"] = registered_at
    data["updated_at_utc"] = registered_at
    atomic_write_json(path, data)


def append_almanac() -> None:
    path = ROOT / "04_ALMANAC.md"
    text = path.read_text(encoding="utf-8")
    heading = "## ERA55A_6 GEMINI RED TEAM REVIEW AND FINDINGS REGISTER"
    if heading in text:
        return
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
- Registered findings: `F1 P0`, `F2 P1`, `F3 P1`, `F4 P2`
- P0 F1 status: `OPEN`
- A7 temp-copy design/test: `AUTHORIZED`
- Production apply: `false`
- Live mutation: `false`
- Next safe step: `{NEXT_SAFE_STEP}`
"""
    atomic_write_text(path, text.replace(marker, entry + marker, 1))


def validate_visible_changes(expected_files: list[str]) -> None:
    expected = set(expected_files)
    visible_expected = expected - FORCE_ADD
    tracked = {line for line in git("diff", "--name-only").splitlines() if line.strip()}
    untracked = {line for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line.strip()}
    actual = tracked | untracked
    if actual != visible_expected:
        raise RuntimeError(
            "UNEXPECTED_VISIBLE_CHANGED_FILES\nEXPECTED="
            + json.dumps(sorted(visible_expected))
            + "\nACTUAL="
            + json.dumps(sorted(actual))
        )


def commit_local(expected_files: list[str]) -> str:
    expected = sorted(set(expected_files))
    validate_visible_changes(expected)
    run(["git", "diff", "--check"])
    normal = sorted(set(expected) - FORCE_ADD)
    if normal:
        run(["git", "add", "--", *normal])
    forced = sorted(set(expected) & FORCE_ADD)
    if forced:
        run(["git", "add", "-f", "--", *forced])
    staged = sorted(line for line in git("diff", "--cached", "--name-only").splitlines() if line.strip())
    if staged != expected:
        raise RuntimeError("STAGED_FILES_MISMATCH\nEXPECTED=" + json.dumps(expected) + "\nACTUAL=" + json.dumps(staged))
    git("commit", "-m", "ERA55A6_GEMINI_RED_TEAM_REGISTER | OK | P0_APPLY_BLOCKED")
    if git("status", "--porcelain"):
        raise RuntimeError("POST_COMMIT_WORKTREE_NOT_CLEAN")
    return git("rev-parse", "HEAD")


def main() -> int:
    head_before = preconditions()
    backup_dir = Path(tempfile.mkdtemp(prefix="era55a6_backup_", dir="/tmp"))
    for rel in CANONICAL_FILES:
        source = ROOT / rel
        target = backup_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    committed = False
    try:
        registered_at = utc_now()
        a5 = load_json(ROOT / A5_REL)
        register = build_register(registered_at, head_before, a5)
        atomic_write_json(ROOT / ARTIFACT_REL, register)
        atomic_write_text(ROOT / REPORT_REL, make_report(register))
        update_runtime(registered_at)
        update_roadmap(registered_at)
        update_master()
        update_handoff()
        append_history(registered_at, head_before)
        append_almanac()

        for rel in (ARTIFACT_REL, "PROJECT_RUNTIME.json", "PROJECT_HISTORY.json", "data/tokenoskobi_v1_v8_master_era_roadmap.json"):
            load_json(ROOT / rel)

        local_commit = commit_local(CANONICAL_FILES + GENERATED_FILES)
        committed = True
        print("ERA55A6_GEMINI_RED_TEAM_REGISTER=SUCCESS")
        print(f"RESULT={RESULT}")
        print(f"LOCAL_COMMIT={local_commit}")
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
            for rel in CANONICAL_FILES:
                backup = backup_dir / rel
                target = ROOT / rel
                if backup.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup, target)
            for rel in GENERATED_FILES:
                target = ROOT / rel
                if target.exists():
                    target.unlink()
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERA55A6_GEMINI_RED_TEAM_REGISTER=FAILED:{exc}", file=sys.stderr)
        raise
