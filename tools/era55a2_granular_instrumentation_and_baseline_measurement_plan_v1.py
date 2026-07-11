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
WORK_UNIT = "ERA55A_2_GRANULAR_INSTRUMENTATION_AND_BASELINE_MEASUREMENT_PLAN"
RESULT = "OK_PLAN_LOCKED_NO_LIVE_MUTATION"
ARTIFACT_REL = "data/control/era55a2_granular_instrumentation_and_baseline_measurement_plan_v1.json"
REPORT_REL = "reports/LATEST_ERA55A2_GRANULAR_INSTRUMENTATION_AND_BASELINE_MEASUREMENT_PLAN.md"
A1_REL = "data/control/era55_runtime_optimization_init_v1.json"
NEXT_SAFE_STEP = "ERA55A_3_NATURAL_CYCLE_BASELINE_COLLECTION"

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
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
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
    atomic_write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
    )


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(
        rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)",
        re.S,
    )
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
    git("fetch", "origin", "main")
    local_head = git("rev-parse", "HEAD")
    remote_head = git("rev-parse", "origin/main")
    if local_head != remote_head:
        raise RuntimeError(
            f"BLOCKED=LOCAL_REMOTE_NOT_SYNCED:LOCAL={local_head}:REMOTE={remote_head}"
        )
    runtime = load_json(ROOT / "PROJECT_RUNTIME.json")
    if runtime.get("current_era") != "ERA55":
        raise RuntimeError(f"BLOCKED=CURRENT_ERA_NOT_ERA55:{runtime.get('current_era')}")
    era55 = runtime.get("era55_status") or {}
    if era55.get("status") != "OPEN":
        raise RuntimeError(f"BLOCKED=ERA55_NOT_OPEN:{era55.get('status')}")
    next_step = runtime.get("next_safe_step") or {}
    if next_step.get("id") != WORK_UNIT:
        raise RuntimeError(f"BLOCKED=UNEXPECTED_NEXT_SAFE_STEP:{next_step.get('id')}")
    if not (ROOT / A1_REL).is_file():
        raise RuntimeError(f"BLOCKED=A1_ARTIFACT_MISSING:{A1_REL}")
    return local_head


def extract_a1_facts(a1: dict[str, Any]) -> dict[str, Any]:
    inspection = a1.get("inspection") or {}
    systemd = inspection.get("systemd") or {}
    service_values = ((systemd.get("service") or {}).get("values") or {})
    timer_values = ((systemd.get("timer") or {}).get("values") or {})
    derived = systemd.get("derived") or {}
    sqlite_data = inspection.get("sqlite") or {}
    queue = inspection.get("queue_policy") or {}

    timer_text = str((systemd.get("timer_unit_text") or {}).get("stdout") or "")
    cadence_seconds = None
    cadence_match = re.search(r"OnUnitActiveSec=(\d+)\s*min", timer_text, re.I)
    if cadence_match:
        cadence_seconds = int(cadence_match.group(1)) * 60

    timeout_seconds = None
    timeout_text = str(service_values.get("TimeoutStartUSec") or "")
    match = re.fullmatch(r"(\d+)min\s+(\d+)s", timeout_text)
    if match:
        timeout_seconds = int(match.group(1)) * 60 + int(match.group(2))
    else:
        match = re.fullmatch(r"(\d+)s", timeout_text)
        if match:
            timeout_seconds = int(match.group(1))

    return {
        "a1_result": a1.get("result"),
        "service_type": service_values.get("Type"),
        "service_result": service_values.get("Result"),
        "timeout_start_seconds": timeout_seconds,
        "runtime_max": service_values.get("RuntimeMaxUSec"),
        "restart_policy": service_values.get("Restart"),
        "kill_mode": service_values.get("KillMode"),
        "timer_active_state": timer_values.get("ActiveState"),
        "timer_sub_state": timer_values.get("SubState"),
        "timer_enabled_state": timer_values.get("UnitFileState"),
        "timer_cadence_seconds": cadence_seconds,
        "timer_accuracy": timer_values.get("AccuracyUSec"),
        "timer_randomized_delay": timer_values.get("RandomizedDelayUSec"),
        "last_runner_duration_ms": derived.get("last_execution_duration_ms"),
        "timer_safety_margin_ms": derived.get("timer_safety_margin_ms"),
        "queue_capacity": queue.get("queue_capacity_detected"),
        "queue_policy": queue.get("selection_policy"),
        "queue_drop_ledger_detected": queue.get("drop_ledger_detected"),
        "queue_silent_truncation_risk": queue.get("silent_truncation_risk"),
        "sqlite_journal_mode": (sqlite_data.get("pragmas") or {}).get("journal_mode"),
        "sqlite_synchronous": (sqlite_data.get("pragmas") or {}).get("synchronous"),
        "sqlite_integrity": sqlite_data.get("integrity_check"),
        "sqlite_quick_check": sqlite_data.get("quick_check"),
    }


def build_plan(planned_at: str, head_before: str, facts: dict[str, Any]) -> dict[str, Any]:
    stage_map = [
        {
            "stage": "TIMER_WAIT",
            "source": "systemd timer properties and list-timers",
            "start_signal": "previous service exit or timer activation",
            "end_signal": "service ExecMainStartTimestampMonotonic",
            "metric": "timer_wait_ms",
            "method": "external read-only observation",
        },
        {
            "stage": "RUNNER_TOTAL",
            "source": "systemd service monotonic timestamps",
            "start_signal": "ExecMainStartTimestampMonotonic",
            "end_signal": "ExecMainExitTimestampMonotonic",
            "metric": "runner_execution_ms",
            "method": "external read-only observation",
        },
        {
            "stage": "RAW_PRODUCER",
            "source": "news_raw_feed_events count/max timestamp",
            "start_signal": "service start snapshot",
            "end_signal": "raw count or max timestamp change",
            "metric": "raw_producer_observed_ms",
            "method": "SQLite mode=ro polling; no write",
        },
        {
            "stage": "DERIVED_REFRESH",
            "source": "match/signal/score/freshness counts and timestamps",
            "start_signal": "raw stage change",
            "end_signal": "derived table change",
            "metric": "derived_refresh_observed_ms",
            "method": "SQLite mode=ro polling; no write",
        },
        {
            "stage": "HOT_GATEWAY",
            "source": "hot_intelligence_ingress_gateway_v1.json",
            "start_signal": "derived stage change",
            "end_signal": "generated_at_utc or file mtime change",
            "metric": "hot_gateway_observed_ms",
            "method": "read-only file observation",
        },
        {
            "stage": "PANEL_BRIDGE",
            "source": "news_active_panel_data_bridge_v1.json and active panel files",
            "start_signal": "hot gateway change",
            "end_signal": "bridge/panel generated time or mtime change",
            "metric": "panel_propagation_observed_ms",
            "method": "read-only file observation",
        },
        {
            "stage": "QUEUE_RESIDENCE_PROXY",
            "source": "display candidate timestamps versus hot queue generated time",
            "start_signal": "candidate published/generated timestamp",
            "end_signal": "gateway generated_at_utc",
            "metric": "queue_residence_proxy_ms",
            "method": "read-only JSON correlation",
        },
    ]

    profiles = [
        {
            "id": "HISTORICAL_24H",
            "purpose": "Immediate runner duration and cadence distribution",
            "source": "journalctl and systemd properties",
            "runner_invocation": False,
            "required_samples": "all complete natural cycles in 24h",
        },
        {
            "id": "NATURAL_NEXT_CYCLE",
            "purpose": "One end-to-end stage propagation observation",
            "source": "next timer-triggered natural cycle",
            "runner_invocation": False,
            "required_samples": 1,
        },
        {
            "id": "HOT_STEADY_STATE",
            "purpose": "Steady-state variance across consecutive cycles",
            "source": "natural timer cycles",
            "runner_invocation": False,
            "required_samples": 3,
        },
        {
            "id": "LOGICAL_COLD_START",
            "purpose": "First natural cycle after reboot or at least two timer cadences without a completed cycle",
            "source": "natural condition only",
            "runner_invocation": False,
            "required_samples": 1,
            "forced_cache_drop": False,
            "if_unavailable": "REPORT_NOT_OBSERVED",
        },
    ]

    metrics = [
        "timer_interval_ms",
        "timer_accuracy_ms",
        "service_timeout_ms",
        "runner_execution_ms",
        "timer_safety_margin_ms",
        "raw_count_before_after",
        "raw_max_timestamp_before_after",
        "match_count_before_after",
        "signal_count_before_after",
        "score_count_before_after",
        "freshness_count_before_after",
        "derived_refresh_observed_ms",
        "hot_gateway_observed_ms",
        "panel_propagation_observed_ms",
        "source_candidate_count",
        "queue_admitted_count",
        "queue_overflow_count",
        "queue_drop_ledger_count",
        "queue_residence_proxy_ms",
        "db_size_before_after",
        "db_freelist_before_after",
        "journal_mode",
        "synchronous",
        "integrity_check",
        "quick_check",
        "duplicate_uid_count",
        "unsafe_authority_count",
    ]

    hard_gates = {
        "silent_event_loss_allowed": False,
        "data_correctness_regression_allowed": False,
        "manual_runner_execution_allowed": False,
        "production_burst_load_allowed": False,
        "service_or_timer_change_allowed": False,
        "watchdog_apply_allowed": False,
        "index_apply_allowed": False,
        "journal_mode_change_allowed": False,
        "cache_apply_allowed": False,
        "queue_policy_change_allowed": False,
        "incremental_write_apply_allowed": False,
        "database_write_allowed": False,
        "panel_write_allowed": False,
        "trade_wallet_signing_order_authority": 0,
    }

    collector_contract = {
        "mode": "EXTERNAL_READONLY_OBSERVER",
        "must_not_import_runtime_modules": True,
        "must_not_invoke_runner": True,
        "must_not_start_or_restart_service": True,
        "must_not_enable_disable_or_edit_timer": True,
        "sqlite_uri": "file:/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite?mode=ro",
        "sqlite_query_only": True,
        "polling_interval_ms": 250,
        "maximum_observation_window": "next natural timer cycle plus completion buffer",
        "output_atomic_write_only": True,
        "output_location": "data/control and reports only",
        "failure_behavior": "FAIL_CLOSED_WITH_PARTIAL_EVIDENCE",
        "hash_or_count_before_after_required": True,
        "git_clean_before_and_after_required": True,
    }

    red_team_gates = [
        {
            "priority": "P0",
            "code": "QUEUE_OVERFLOW_SILENT_TRUNCATION",
            "current_state": "OPEN_RISK" if facts.get("queue_silent_truncation_risk") else "NOT_PROVEN",
            "closure_requirement": "candidate_count, admitted_count and overflow_count must be measured; no claim of zero loss without ledger",
        },
        {
            "priority": "P0",
            "code": "TIMER_RUNNER_MARGIN",
            "current_state": "BASELINE_REQUIRED",
            "closure_requirement": "timer interval, timeout, p50/p95/max runner duration and overlap evidence must be reported",
        },
        {
            "priority": "P0",
            "code": "DATA_CORRECTNESS",
            "current_state": "HARD_GATE",
            "closure_requirement": "counts, UIDs, authority flags and integrity checks must remain correct",
        },
        {
            "priority": "P1",
            "code": "PANEL_PROPAGATION_VISIBILITY",
            "current_state": "BASELINE_REQUIRED",
            "closure_requirement": "DB-to-gateway-to-panel timing must be observable or explicitly marked unmeasurable",
        },
        {
            "priority": "P1",
            "code": "SQLITE_DURABILITY",
            "current_state": f"journal={facts.get('sqlite_journal_mode')};sync={facts.get('sqlite_synchronous')}",
            "closure_requirement": "no PRAGMA mutation in baseline; temp-copy recovery testing required before any mode change",
        },
    ]

    next_step_contract = {
        "id": NEXT_SAFE_STEP,
        "scope": "COLLECT_BASELINE_ONLY",
        "allowed": [
            "read systemd properties and journal",
            "read SQLite with mode=ro and query_only",
            "read runtime JSON/JSONL/HTML metadata",
            "observe one or more natural timer cycles",
            "write isolated evidence artifact and report",
            "update canonical state after evidence",
        ],
        "forbidden": [
            "manual runner invocation",
            "service start restart or edit",
            "timer start restart enable disable or edit",
            "database mutation",
            "watchdog apply",
            "index apply",
            "WAL or synchronous change",
            "cache apply",
            "queue policy change",
            "production burst load",
        ],
        "completion_output": "ERA55A_3 baseline artifact with historical, natural-cycle and steady-state measurements",
    }

    return {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "era": "ERA55",
        "title": "Runtime Optimization",
        "planned_at_utc": planned_at,
        "status": "CLOSED_PLAN_LOCKED",
        "result": RESULT,
        "head_before_commit": head_before,
        "source_artifact": A1_REL,
        "a1_facts": facts,
        "objective": "Measure the existing runtime before any optimization, separate latency stages, expose queue overflow and preserve data correctness.",
        "stage_map": stage_map,
        "baseline_profiles": profiles,
        "required_metrics": metrics,
        "collector_contract": collector_contract,
        "hard_gates": hard_gates,
        "red_team_gates": red_team_gates,
        "acceptance_logic": {
            "baseline_may_close_with_warnings": True,
            "optimization_may_start_with_open_p0": False,
            "unknown_metric_must_be_reported_as_unknown": True,
            "missing_evidence_must_not_be_inferred": True,
            "speed_gain_cannot_override_correctness": True,
        },
        "gemini_review": {
            "required_after": "ERA55A_5_BASELINE_REPORT",
            "before_optimization_apply": True,
            "minimum_inputs": [
                "A1 inspection artifact",
                "A2 measurement plan",
                "A3/A4 baseline evidence",
                "A5 baseline report",
                "queue overflow evidence",
                "timer overlap evidence",
                "SQLite durability evidence",
                "panel propagation evidence",
            ],
        },
        "next_safe_step": next_step_contract,
        "mutation_statement": {
            "live_runtime": False,
            "database": False,
            "service": False,
            "timer": False,
            "panel": False,
            "queue_policy": False,
            "watchdog": False,
            "index": False,
            "journal_mode": False,
            "cache": False,
        },
    }


def update_runtime(planned_at: str, plan: dict[str, Any]) -> None:
    path = ROOT / "PROJECT_RUNTIME.json"
    data = load_json(path)
    work_unit = {
        "id": WORK_UNIT,
        "type": "ERA55_BASELINE_MEASUREMENT_PLAN",
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
        "type": "ERA55_NATURAL_CYCLE_BASELINE_COLLECTION",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "serves": "V3_RUNTIME_INTELLIGENCE_OS",
        "purpose": "Collect historical and natural timer-cycle baseline evidence with an external read-only observer.",
        "human_authorization_required": True,
        "manual_runner_execution_authorized": False,
        "production_burst_load_authorized": False,
        "runtime_mutation_authorized": False,
        "gemini_red_team_review_after_baseline_report": True,
        "status": "READY",
    }
    last_action = {
        "timestamp": planned_at,
        "task": WORK_UNIT,
        "result": RESULT,
        "artifact": ARTIFACT_REL,
    }
    data["mode"] = "ERA55A2_BASELINE_MEASUREMENT_PLAN_CLOSED"
    data["project_status"] = "ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE_PLAN_LOCKED"
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
            "updated_at": planned_at,
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
            "active_stage": "ERA55A_BASELINE_MEASUREMENT",
            "last_completed_substep": WORK_UNIT,
            "next_safe_step": NEXT_SAFE_STEP,
            "a2_artifact": ARTIFACT_REL,
            "a2_report": REPORT_REL,
            "measurement_plan_locked": True,
            "optimization_apply_authorized": False,
            "burst_load_authorized": False,
            "manual_runner_execution_authorized": False,
            "runtime_db_service_timer_panel_mutation": False,
            "gemini_red_team_required": True,
        }
    )
    a1_risks = [
        gate
        for gate in plan["red_team_gates"]
        if gate["current_state"] in ("OPEN_RISK", "BASELINE_REQUIRED")
    ]
    data["open_risks"] = [
        f"{item['priority']}:{item['code']}:{item['current_state']}"
        for item in a1_risks
    ] + ["Risk is minimized, never zero."]
    data["source"] = "era55a2_baseline_measurement_plan_v1"
    data["updated_at"] = planned_at
    data["updated_at_utc"] = planned_at
    atomic_write_json(path, data)


def update_roadmap_json(planned_at: str) -> None:
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
                        "active_stage": "ERA55A_BASELINE_MEASUREMENT",
                        "last_completed_substep": WORK_UNIT,
                        "next_safe_step": NEXT_SAFE_STEP,
                        "measurement_plan_artifact": ARTIFACT_REL,
                        "measurement_plan_locked": True,
                        "optimization_apply_authorized": False,
                        "burst_load_authorized": False,
                        "gemini_red_team_required": True,
                    }
                )
                found = True
    if not found:
        raise RuntimeError("ERA55_NOT_FOUND_IN_ROADMAP_JSON")
    data["updated_at"] = planned_at
    data["git_head"] = "DYNAMIC_USE_GIT_REV_PARSE_HEAD"
    data["work_unit"] = WORK_UNIT
    atomic_write_json(path, data)


def update_master() -> None:
    path = ROOT / "06_PROJECT_MASTER_STATE.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "PROJECT_STATUS=ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE",
        "PROJECT_STATUS=ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE_PLAN_LOCKED",
        1,
    )
    section_02 = """```text
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_BASELINE_MEASUREMENT
LAST_COMPLETED_SUBSTEP=ERA55A_2_GRANULAR_INSTRUMENTATION_AND_BASELINE_MEASUREMENT_PLAN
MEASUREMENT_PLAN_LOCKED=true
GEMINI_RED_TEAM_REQUIRED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
MANUAL_RUNNER_EXECUTION_AUTHORIZED=false
```

The measurement plan uses an external read-only observer. It does not modify the runner, service, timer, database, queue policy or panel."""
    section_03 = f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_MUTATION=false
```

A2 locked stage boundaries, baseline profiles, metrics, hard gates and the A3 collector contract."""
    section_09 = """- `P0 QUEUE_OVERFLOW_SILENT_TRUNCATION` remains open until candidate, admitted and overflow counts are measured and a later explicit policy is approved.
- `P0 TIMER_RUNNER_MARGIN` requires historical and natural-cycle duration evidence.
- `P0 DATA_CORRECTNESS` is a permanent hard gate.
- Panel propagation latency remains unmeasured.
- SQLite remains `journal_mode=delete`, `synchronous=2`; no PRAGMA change is authorized.
- Manual runner execution and production burst load remain blocked.
- Runtime risk is minimized, never zero.
- Git HEAD must be read dynamically."""
    section_10 = f"""```text
NEXT_SAFE_STEP={NEXT_SAFE_STEP}
```

A3 may only observe historical logs and natural timer cycles. It may not invoke the runner or mutate service, timer, database, queue policy or panel."""
    text = replace_section(text, "## 02 CURRENT MAJOR-LINE POSITION", section_02)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", section_03)
    text = replace_section(text, "## 09 OPEN RISKS AND DECISIONS", section_09)
    text = replace_section(text, "## 10 NEXT SAFE STEP", section_10)
    atomic_write_text(path, text)


def update_handoff() -> None:
    path = ROOT / "07_PROJECT_HANDOFF.md"
    text = path.read_text(encoding="utf-8")
    checkpoint = """PROJECT_STATUS=ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE_PLAN_LOCKED
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_BASELINE_MEASUREMENT
LAST_COMPLETED_SUBSTEP=ERA55A_2_GRANULAR_INSTRUMENTATION_AND_BASELINE_MEASUREMENT_PLAN
MEASUREMENT_PLAN_LOCKED=true
GEMINI_RED_TEAM_REQUIRED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
MANUAL_RUNNER_EXECUTION_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A2 is closed. No live runtime mutation was applied."""
    last_work = f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=null

The next action is natural-cycle baseline collection through an external read-only observer."""
    do_not = """- Do not reopen ERA54.
- Do not rebuild NEWS from zero.
- Do not manually invoke the production runner for baseline collection.
- Do not start, restart, edit, enable or disable the service or timer.
- Do not apply watchdog, index, WAL, cache, queue-policy or incremental-write changes before baseline evidence.
- Do not run production BURST_LOAD.
- Do not accept silent event loss.
- Do not infer missing measurements.
- Do not close ERA55 before Gemini Red Team findings are resolved."""
    decisions = f"""Current authorized direction:

- `ERA55_RUNTIME_OPTIMIZATION` is open.
- A1 inspection and A2 measurement planning are complete.
- Natural-cycle read-only baseline collection is the only next technical action.
- Optimization apply and burst load remain unauthorized.

NEXT_SAFE_STEP={NEXT_SAFE_STEP}"""
    execution = f"""1. Read `PROJECT_RUNTIME.json`.
2. Confirm `{NEXT_SAFE_STEP}` is current.
3. Verify local and remote `main` are synchronized.
4. Read `{ARTIFACT_REL}`.
5. Run the external read-only A3 collector.
6. Observe historical logs and natural timer cycles only.
7. Record unknown values as unknown.
8. Preserve P0 queue-loss and correctness gates.
9. Do not apply optimization before the completed baseline and Gemini review."""
    text = replace_section(text, "## 02 CURRENT CONTINUATION CHECKPOINT", checkpoint)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", last_work)
    text = replace_section(text, "## 06 DO NOT REOPEN OR REPEAT", do_not)
    text = replace_section(text, "## 07 ALLOWED NEXT DECISIONS", decisions)
    text = replace_section(text, "## 08 NEXT SESSION EXECUTION RULE", execution)
    atomic_write_text(path, text)


def append_history(planned_at: str, head_before: str) -> None:
    path = ROOT / "PROJECT_HISTORY.json"
    data = load_json(path)
    events = data.get("events")
    if not isinstance(events, list):
        raise RuntimeError("PROJECT_HISTORY_EVENTS_INVALID")
    event_id = "ERA55A2_BASELINE_MEASUREMENT_PLAN_V1"
    if not any(isinstance(item, dict) and item.get("event_id") == event_id for item in events):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": planned_at,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "GRANULAR_INSTRUMENTATION_AND_BASELINE_MEASUREMENT_PLAN_LOCKED",
                "status": "CLOSED",
                "result": RESULT,
                "head_before_commit": head_before,
                "artifact": ARTIFACT_REL,
                "report": REPORT_REL,
                "live_runtime_db_service_timer_panel_mutation": False,
                "manual_runner_execution_authorized": False,
                "production_burst_load_authorized": False,
                "next_safe_step": NEXT_SAFE_STEP,
                "gemini_red_team_required": True,
            }
        )
    data["updated_at"] = planned_at
    data["updated_at_utc"] = planned_at
    atomic_write_json(path, data)


def append_almanac() -> None:
    path = ROOT / "04_ALMANAC.md"
    text = path.read_text(encoding="utf-8")
    heading = "## ERA55A_2 GRANULAR INSTRUMENTATION AND BASELINE MEASUREMENT PLAN"
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
- Measurement approach: external read-only observer.
- Baseline profiles: historical 24h, next natural cycle, hot steady state and logical cold start when naturally available.
- Manual production runner execution: `false`
- Service/timer/DB/queue/panel mutation: `false`
- Production burst load: `false`
- P0 gates: silent queue loss, timer margin and data correctness.
- Gemini Red Team review: required after baseline report.
- Next safe step: `{NEXT_SAFE_STEP}`
"""
    atomic_write_text(path, text.replace(marker, entry + marker, 1))


def make_report(plan: dict[str, Any]) -> str:
    facts = plan["a1_facts"]
    stage_lines = "\n".join(
        f"- `{item['stage']}` → `{item['metric']}` — {item['method']}"
        for item in plan["stage_map"]
    )
    profile_lines = "\n".join(
        f"- `{item['id']}` — {item['purpose']}; runner invocation: `{str(item['runner_invocation']).lower()}`"
        for item in plan["baseline_profiles"]
    )
    gate_lines = "\n".join(
        f"- **{item['priority']} {item['code']}** — {item['closure_requirement']}"
        for item in plan["red_team_gates"]
    )
    return f"""# ERA55A_2 GRANULAR INSTRUMENTATION AND BASELINE MEASUREMENT PLAN

Result: `{RESULT}`

ERA55 status: `OPEN`

Live runtime/DB/service/timer/queue/panel mutation: `false`

## A1 Facts Used

```json
{json.dumps(facts, ensure_ascii=False, indent=2)}
```

## Measurement Stages

{stage_lines}

## Baseline Profiles

{profile_lines}

## Collector Contract

```json
{json.dumps(plan['collector_contract'], ensure_ascii=False, indent=2)}
```

## Hard Gates

```json
{json.dumps(plan['hard_gates'], ensure_ascii=False, indent=2)}
```

## Red Team Gates

{gate_lines}

## Decision

- Measurement plan is locked.
- No runner instrumentation was applied.
- No systemd unit was changed.
- No SQLite PRAGMA was changed.
- No queue policy was changed.
- No production burst test was executed.
- Next: `{NEXT_SAFE_STEP}`.
"""


def validate_visible_changes(expected_files: list[str]) -> None:
    expected = set(expected_files)
    visible_expected = expected - FORCE_ADD
    tracked = {
        line
        for line in git("diff", "--name-only").splitlines()
        if line.strip()
    }
    untracked = {
        line
        for line in git("ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    }
    actual = tracked | untracked
    if actual != visible_expected:
        raise RuntimeError(
            "UNEXPECTED_VISIBLE_CHANGED_FILES\n"
            + "EXPECTED="
            + json.dumps(sorted(visible_expected))
            + "\nACTUAL="
            + json.dumps(sorted(actual))
        )


def commit_and_push(expected_files: list[str]) -> tuple[str, str]:
    expected = sorted(set(expected_files))
    for rel in expected:
        if not (ROOT / rel).is_file():
            raise RuntimeError(f"EXPECTED_FILE_MISSING={rel}")
    validate_visible_changes(expected)
    run(["git", "diff", "--check"])
    normal = sorted(set(expected) - FORCE_ADD)
    if normal:
        run(["git", "add", "--", *normal])
    forced = sorted(set(expected) & FORCE_ADD)
    if forced:
        run(["git", "add", "-f", "--", *forced])
    staged = sorted(
        line
        for line in git("diff", "--cached", "--name-only").splitlines()
        if line.strip()
    )
    if staged != expected:
        raise RuntimeError(
            "STAGED_FILES_MISMATCH\n"
            + "EXPECTED="
            + json.dumps(expected)
            + "\nACTUAL="
            + json.dumps(staged)
        )
    git("commit", "-m", "ERA55A2_BASELINE_MEASUREMENT_PLAN | OK | NO_LIVE_MUTATION")
    local_head = git("rev-parse", "HEAD")
    run(["git", "push", "origin", "main"], timeout=240)
    git("fetch", "origin", "main")
    remote_head = git("rev-parse", "origin/main")
    if local_head != remote_head:
        raise RuntimeError(f"POST_PUSH_HEAD_MISMATCH:LOCAL={local_head}:REMOTE={remote_head}")
    if git("status", "--porcelain"):
        raise RuntimeError("POST_PUSH_WORKTREE_NOT_CLEAN")
    return local_head, remote_head


def main() -> int:
    head_before = preconditions()
    backup_dir = Path(tempfile.mkdtemp(prefix="era55a2_backup_", dir="/tmp"))
    for rel in CANONICAL_FILES:
        source = ROOT / rel
        target = backup_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    committed = False
    try:
        planned_at = utc_now()
        a1 = load_json(ROOT / A1_REL)
        facts = extract_a1_facts(a1)
        if facts.get("sqlite_integrity") != "ok":
            raise RuntimeError("BLOCKED=A1_SQLITE_INTEGRITY_NOT_OK")
        if facts.get("sqlite_quick_check") != "ok":
            raise RuntimeError("BLOCKED=A1_SQLITE_QUICK_CHECK_NOT_OK")

        plan = build_plan(planned_at, head_before, facts)
        atomic_write_json(ROOT / ARTIFACT_REL, plan)
        atomic_write_text(ROOT / REPORT_REL, make_report(plan))
        update_runtime(planned_at, plan)
        update_roadmap_json(planned_at)
        update_master()
        update_handoff()
        append_history(planned_at, head_before)
        append_almanac()

        for rel in (
            ARTIFACT_REL,
            "PROJECT_RUNTIME.json",
            "PROJECT_HISTORY.json",
            "data/tokenoskobi_v1_v8_master_era_roadmap.json",
        ):
            load_json(ROOT / rel)

        head_after, remote_after = commit_and_push(CANONICAL_FILES + GENERATED_FILES)
        committed = True

        print("ERA55A2_BASELINE_MEASUREMENT_PLAN=SUCCESS")
        print(f"RESULT={RESULT}")
        print(f"HEAD_BEFORE={head_before}")
        print(f"CANONICAL_HEAD={head_after}")
        print(f"REMOTE_HEAD={remote_after}")
        print("ERA55_STATUS=OPEN")
        print(f"LAST_COMPLETED={WORK_UNIT}")
        print(f"NEXT_SAFE_STEP={NEXT_SAFE_STEP}")
        print("MEASUREMENT_MODE=EXTERNAL_READONLY_OBSERVER")
        print("MANUAL_RUNNER_EXECUTION_AUTHORIZED=false")
        print("PRODUCTION_BURST_LOAD_AUTHORIZED=false")
        print("LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false")
        print(f"ARTIFACT={ARTIFACT_REL}")
        print(f"REPORT={REPORT_REL}")
        print("GEMINI_RED_TEAM_REQUIRED=true")
        print("WORKTREE=CLEAN")
        print(f"BACKUP_DIR={backup_dir}")
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
        print(f"ERA55A2_BASELINE_MEASUREMENT_PLAN=FAILED:{exc}", file=sys.stderr)
        raise
