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
WORK_UNIT = "ERA55A_4_BASELINE_CONSOLIDATION_AND_EXTENDED_SAMPLE_REVIEW"
RESULT = "WARN_BASELINE_SUFFICIENT_FOR_A5_P0_REMAINS_OPEN"
A1_REL = "data/control/era55_runtime_optimization_init_v1.json"
A2_REL = "data/control/era55a2_granular_instrumentation_and_baseline_measurement_plan_v1.json"
A3_REL = "data/control/era55a3_natural_cycle_baseline_collection_v1.json"
ARTIFACT_REL = "data/control/era55a4_baseline_consolidation_and_extended_sample_review_v1.json"
REPORT_REL = "reports/LATEST_ERA55A4_BASELINE_CONSOLIDATION_AND_EXTENDED_SAMPLE_REVIEW.md"
NEXT_SAFE_STEP = "ERA55A_5_BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE"

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


def run(
    cmd: list[str],
    *,
    timeout: int = 180,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
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
    if (runtime.get("era55_status") or {}).get("status") != "OPEN":
        raise RuntimeError("BLOCKED=ERA55_NOT_OPEN")
    next_step = runtime.get("next_safe_step") or {}
    if next_step.get("id") != WORK_UNIT:
        raise RuntimeError(f"BLOCKED=UNEXPECTED_NEXT_SAFE_STEP:{next_step.get('id')}")
    for rel in (A1_REL, A2_REL, A3_REL):
        if not (ROOT / rel).is_file():
            raise RuntimeError(f"BLOCKED=SOURCE_ARTIFACT_MISSING:{rel}")
    return local_head


def number(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def consolidate(a1: dict[str, Any], a2: dict[str, Any], a3: dict[str, Any]) -> dict[str, Any]:
    a1_inspection = a1.get("inspection") or {}
    a1_sqlite = a1_inspection.get("sqlite") or {}
    a1_systemd = a1_inspection.get("systemd") or {}
    a1_derived = a1_systemd.get("derived") or {}
    a1_queue = a1_inspection.get("queue_policy") or {}

    a2_facts = a2.get("a1_facts") or {}
    historical = a3.get("historical_baseline") or {}
    hist_24h = historical.get("historical_24h") or {}
    hist_duration = hist_24h.get("duration_ms") or {}
    hot_12h = historical.get("hot_state_12h") or {}
    cold = historical.get("cold_start_current_boot") or {}
    queue = a3.get("silent_drop_investigation") or {}
    natural = a3.get("natural_cycle") or {}

    timer_interval_seconds = int(a2_facts.get("timer_cadence_seconds") or 1200)
    timer_interval_ms = timer_interval_seconds * 1000
    timeout_seconds = int(a2_facts.get("timeout_start_seconds") or 70)
    timeout_ms = timeout_seconds * 1000
    expected_24h_cycles = int((24 * 60 * 60) / timer_interval_seconds)
    observed_24h_cycles = int(hist_24h.get("cycle_count") or 0)
    observed_12h_cycles = int(hot_12h.get("cycle_count") or 0)
    expected_12h_cycles = int((12 * 60 * 60) / timer_interval_seconds)

    hist_values = [
        number(hist_duration.get(key))
        for key in ("min", "p50", "p95", "max")
    ]
    hist_values_non_null = [value for value in hist_values if value is not None]
    journal_quantized = (
        len(hist_values_non_null) == 4
        and len(set(hist_values_non_null)) == 1
        and hist_values_non_null[0] in (0.0, 1000.0, 2000.0)
    )

    natural_runner_ms = number(natural.get("runner_execution_ms"))
    natural_margin_ms = number(natural.get("timer_safety_margin_ms"))
    if natural_margin_ms is None and natural_runner_ms is not None:
        natural_margin_ms = timer_interval_ms - natural_runner_ms
    timeout_headroom_ms = (
        timeout_ms - natural_runner_ms
        if natural_runner_ms is not None
        else None
    )
    runner_interval_utilization_pct = (
        natural_runner_ms / timer_interval_ms * 100.0
        if natural_runner_ms is not None and timer_interval_ms > 0
        else None
    )
    runner_timeout_utilization_pct = (
        natural_runner_ms / timeout_ms * 100.0
        if natural_runner_ms is not None and timeout_ms > 0
        else None
    )

    capacity = int(a2_facts.get("queue_capacity") or a1_queue.get("queue_capacity_detected") or 50)
    candidates = int(queue.get("deduplicated_candidate_count") or 0)
    admitted = int(queue.get("admitted_count") or 0)
    overflow = int(queue.get("overflow_count") or 0)
    queue_utilization_pct = admitted / capacity * 100.0 if capacity else None
    ledger_detected = bool(queue.get("drop_ledger_detected"))
    queue_classification = str(queue.get("classification") or "UNKNOWN")

    stage_mtimes = natural.get("stage_file_mtimes_after_cycle") or {}
    file_changes = natural.get("observed_file_changes_during_cycle") or {}
    propagation_visible = bool(stage_mtimes or file_changes)
    exact_panel_latency_available = any(
        key in natural
        for key in (
            "panel_propagation_observed_ms",
            "hot_gateway_observed_ms",
            "derived_refresh_observed_ms",
        )
    )

    sqlite_integrity_ok = (
        a1_sqlite.get("integrity_check") == "ok"
        and a1_sqlite.get("quick_check") == "ok"
        and natural.get("db_integrity_preserved") is True
        and natural.get("db_quick_check_preserved") is True
    )
    duplicate_groups = ((natural.get("after") or {}).get("db") or {}).get("uid_duplicates") or {}
    duplicate_total = sum(
        int((item or {}).get("duplicate_groups") or 0)
        for item in duplicate_groups.values()
        if isinstance(item, dict)
    )

    timer_decision = {
        "sample_sufficiency_for_low_load_baseline": (
            observed_24h_cycles >= max(12, int(expected_24h_cycles * 0.8))
            and natural.get("observed") is True
        ),
        "sample_sufficiency_for_stress_or_lock_claim": False,
        "historical_cycle_count_24h": observed_24h_cycles,
        "expected_cycle_count_24h": expected_24h_cycles,
        "historical_coverage_ratio": round(observed_24h_cycles / expected_24h_cycles, 4)
        if expected_24h_cycles else None,
        "hot_cycle_count_12h": observed_12h_cycles,
        "expected_hot_cycle_count_12h": expected_12h_cycles,
        "journal_duration_precision": (
            "SECOND_QUANTIZED_APPROXIMATION"
            if journal_quantized
            else "VARIABLE_PRECISION"
        ),
        "journal_p50_ms_reported": hist_duration.get("p50"),
        "journal_p95_ms_reported": hist_duration.get("p95"),
        "journal_max_ms_reported": hist_duration.get("max"),
        "precise_natural_runner_ms": round(natural_runner_ms, 3)
        if natural_runner_ms is not None
        else None,
        "timer_interval_ms": timer_interval_ms,
        "precise_natural_safety_margin_ms": round(natural_margin_ms, 3)
        if natural_margin_ms is not None
        else None,
        "timeout_ms": timeout_ms,
        "timeout_headroom_ms": round(timeout_headroom_ms, 3)
        if timeout_headroom_ms is not None
        else None,
        "runner_interval_utilization_pct": round(runner_interval_utilization_pct, 6)
        if runner_interval_utilization_pct is not None
        else None,
        "runner_timeout_utilization_pct": round(runner_timeout_utilization_pct, 6)
        if runner_timeout_utilization_pct is not None
        else None,
        "overlap_observed_24h": bool(historical.get("overlap_observed")),
        "timeout_observed_24h": bool(historical.get("timeout_observed")),
        "watchdog_decision": "NOT_URGENT_LOW_LOAD_NO_APPLY",
        "reason": "Large low-load margin is observed, but no stress or lock-contention evidence exists. Watchdog values must not be selected from a single low-load path.",
    }

    queue_decision = {
        "capacity": capacity,
        "candidate_count": candidates,
        "admitted_count": admitted,
        "overflow_count": overflow,
        "capacity_utilization_pct": round(queue_utilization_pct, 3)
        if queue_utilization_pct is not None
        else None,
        "drop_ledger_detected": ledger_detected,
        "snapshot_classification": queue_classification,
        "silent_drop_observed_current_snapshot": overflow > 0 and not ledger_detected,
        "silent_drop_capability_confirmed": True,
        "historical_zero_loss_claim_allowed": False,
        "p0_status": "OPEN",
        "reason": "The deterministic top-50 truncation exists, the current candidate set exactly saturates the bound and no overflow ledger exists. Current overflow was not observed, but loss cannot be disproved historically.",
        "minimum_future_fix_contract": {
            "silent_drop": False,
            "candidate_count": True,
            "admitted_count": True,
            "overflow_count": True,
            "overflow_event_uids": True,
            "eviction_reason": True,
            "priority_before_after": True,
            "atomic_drop_ledger": True,
        },
    }

    cold_decision = {
        "classification": cold.get("classification"),
        "true_cold_start_observed": cold.get("classification") == "CURRENT_BOOT_FIRST_THREE_CYCLES_OBSERVED",
        "sufficient_for_a5": True,
        "sufficient_for_optimization_apply": False,
        "future_test_location": "TEMP_COPY_OR_NATURAL_REBOOT_OBSERVATION",
        "production_restart_authorized": False,
    }

    sqlite_decision = {
        "journal_mode": a2_facts.get("sqlite_journal_mode"),
        "synchronous": a2_facts.get("sqlite_synchronous"),
        "integrity_preserved": sqlite_integrity_ok,
        "duplicate_uid_groups": duplicate_total,
        "wal_change_authorized": False,
        "index_change_authorized": False,
        "decision": "OBSERVE_ONLY_TEMP_COPY_BENCHMARK_REQUIRED",
        "reason": "DELETE mode alone is not proof that WAL is superior for this workload. Durability, lock and write-amplification tests are required on a copy before any PRAGMA change.",
    }

    panel_decision = {
        "file_change_visibility_observed": propagation_visible,
        "exact_stage_latency_available": exact_panel_latency_available,
        "sufficient_for_a5": True,
        "sufficient_for_optimization_apply": exact_panel_latency_available,
        "status": "VISIBLE_BUT_NOT_GRANULAR" if propagation_visible and not exact_panel_latency_available else (
            "GRANULAR" if exact_panel_latency_available else "UNOBSERVED"
        ),
        "future_requirement": "Add external timestamp correlation or temp-copy instrumentation before claiming panel latency improvement.",
    }

    data_correctness = {
        "sqlite_integrity_preserved": sqlite_integrity_ok,
        "actual_queue_matches_deterministic_top50": queue.get("actual_matches_deterministic_top50"),
        "duplicate_uid_groups": duplicate_total,
        "natural_service_result": natural.get("service_result"),
        "natural_service_exit_status": natural.get("service_exit_status"),
        "correctness_gate_status": "OK_FOR_BASELINE_REPORT" if sqlite_integrity_ok and queue.get("actual_matches_deterministic_top50") is True else "BLOCKED",
        "speed_cannot_override_correctness": True,
    }

    missing_for_apply = [
        "QUEUE_OVERFLOW_DROP_LEDGER",
        "TRUE_COLD_START_OR_TEMP_COPY_COLD_SIMULATION",
        "TEMP_COPY_BURST_SATURATION_LOCK_RECOVERY_TEST",
        "GRANULAR_STAGE_AND_PANEL_PROPAGATION_LATENCY",
        "QUERY_PLAN_AND_WRITE_AMPLIFICATION_EVIDENCE",
    ]

    a5_ready = (
        timer_decision["sample_sufficiency_for_low_load_baseline"]
        and natural.get("observed") is True
        and data_correctness["correctness_gate_status"] == "OK_FOR_BASELINE_REPORT"
    )

    return {
        "source_results": {
            "a1": a1.get("result"),
            "a2": a2.get("result"),
            "a3": a3.get("result"),
        },
        "timer_runner_review": timer_decision,
        "silent_drop_review": queue_decision,
        "cold_start_review": cold_decision,
        "sqlite_review": sqlite_decision,
        "panel_propagation_review": panel_decision,
        "data_correctness_review": data_correctness,
        "sample_decision": {
            "baseline_sufficient_for_a5_report": a5_ready,
            "baseline_sufficient_for_gemini_review": a5_ready,
            "baseline_sufficient_for_optimization_apply": False,
            "extended_passive_wait_before_a5_required": False,
            "extended_evidence_before_optimization_apply_required": True,
            "missing_before_optimization_apply": missing_for_apply,
            "decision": "PROCEED_TO_A5_WITH_OPEN_P0_AND_EXPLICIT_UNKNOWNS" if a5_ready else "BLOCK_A5_REPAIR_BASELINE_EVIDENCE",
        },
        "p0_gates": [
            {
                "code": "QUEUE_SILENT_TRUNCATION_CAPABILITY",
                "status": "OPEN",
                "blocks_a5": False,
                "blocks_optimization_apply": True,
            },
            {
                "code": "DATA_CORRECTNESS",
                "status": data_correctness["correctness_gate_status"],
                "blocks_a5": data_correctness["correctness_gate_status"] != "OK_FOR_BASELINE_REPORT",
                "blocks_optimization_apply": data_correctness["correctness_gate_status"] != "OK_FOR_BASELINE_REPORT",
            },
            {
                "code": "TIMER_OVERLAP_LOW_LOAD",
                "status": "NOT_OBSERVED",
                "blocks_a5": False,
                "blocks_optimization_apply": False,
            },
            {
                "code": "STRESS_LOCK_CONTENTION",
                "status": "UNTESTED",
                "blocks_a5": False,
                "blocks_optimization_apply": True,
            },
        ],
    }


def build_artifact(
    reviewed_at: str,
    head_before: str,
    review: dict[str, Any],
) -> dict[str, Any]:
    if review["sample_decision"]["baseline_sufficient_for_a5_report"] is not True:
        raise RuntimeError("BLOCKED=A5_BASELINE_NOT_SUFFICIENT")
    if review["data_correctness_review"]["correctness_gate_status"] != "OK_FOR_BASELINE_REPORT":
        raise RuntimeError("BLOCKED=DATA_CORRECTNESS_GATE_NOT_OK")

    return {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "era": "ERA55",
        "title": "Runtime Optimization",
        "reviewed_at_utc": reviewed_at,
        "status": "CLOSED_CONSOLIDATION_REVIEW",
        "result": RESULT,
        "head_before_commit": head_before,
        "sources": {
            "a1": A1_REL,
            "a2": A2_REL,
            "a3": A3_REL,
        },
        "review": review,
        "decision": {
            "proceed_to_a5": True,
            "a5_purpose": "Produce one consolidated baseline report and Gemini Red Team package without authorizing optimization apply.",
            "optimization_apply_authorized": False,
            "production_burst_load_authorized": False,
            "service_timer_change_authorized": False,
            "database_change_authorized": False,
            "queue_policy_change_authorized": False,
            "watchdog_apply_authorized": False,
            "wal_apply_authorized": False,
            "index_apply_authorized": False,
        },
        "gemini_package_requirements": [
            "A1 inspection evidence",
            "A2 measurement contract",
            "A3 historical and natural-cycle evidence",
            "A4 precision and sample-sufficiency review",
            "P0 silent-truncation capability",
            "journal duration quantization warning",
            "cold-start unknown",
            "stress and lock-contention unknown",
            "SQLite durability state",
            "panel propagation granularity gap",
        ],
        "next_safe_step": NEXT_SAFE_STEP,
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


def update_runtime(reviewed_at: str, artifact: dict[str, Any]) -> None:
    path = ROOT / "PROJECT_RUNTIME.json"
    data = load_json(path)
    work_unit = {
        "id": WORK_UNIT,
        "type": "ERA55_BASELINE_CONSOLIDATION_REVIEW",
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
        "type": "ERA55_BASELINE_REPORT_AND_EXTERNAL_RED_TEAM_PACKAGE",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "serves": "V3_RUNTIME_INTELLIGENCE_OS",
        "purpose": "Produce the consolidated baseline report and Gemini Red Team package with open P0 risks and explicit unknowns.",
        "human_authorization_required": True,
        "optimization_apply_authorized": False,
        "production_burst_load_authorized": False,
        "gemini_red_team_required": True,
        "status": "READY",
    }
    last_action = {
        "timestamp": reviewed_at,
        "task": WORK_UNIT,
        "result": RESULT,
        "artifact": ARTIFACT_REL,
    }
    data["mode"] = "ERA55A4_BASELINE_CONSOLIDATION_REVIEW_CLOSED"
    data["project_status"] = "ACTIVE_ERA55_BASELINE_READY_FOR_GEMINI_PACKAGE"
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
            "updated_at": reviewed_at,
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
            "a4_artifact": ARTIFACT_REL,
            "a4_report": REPORT_REL,
            "baseline_ready_for_a5": True,
            "baseline_sufficient_for_optimization_apply": False,
            "p0_queue_risk_open": True,
            "optimization_apply_authorized": False,
            "burst_load_authorized": False,
            "runtime_db_service_timer_panel_mutation": False,
            "gemini_red_team_required": True,
        }
    )
    review = artifact["review"]
    open_risks = []
    for gate in review["p0_gates"]:
        if gate["status"] in ("OPEN", "UNTESTED", "BLOCKED"):
            open_risks.append(
                f"P0:{gate['code']}:{gate['status']}"
            )
    for missing in review["sample_decision"]["missing_before_optimization_apply"]:
        open_risks.append(f"P1:MISSING_BEFORE_APPLY:{missing}")
    data["open_risks"] = open_risks + ["Risk is minimized, never zero."]
    data["source"] = "era55a4_baseline_consolidation_review_v1"
    data["updated_at"] = reviewed_at
    data["updated_at_utc"] = reviewed_at
    atomic_write_json(path, data)


def update_roadmap_json(reviewed_at: str) -> None:
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
                        "last_result": RESULT,
                        "next_safe_step": NEXT_SAFE_STEP,
                        "a4_artifact": ARTIFACT_REL,
                        "baseline_ready_for_a5": True,
                        "baseline_sufficient_for_optimization_apply": False,
                        "optimization_apply_authorized": False,
                        "burst_load_authorized": False,
                        "gemini_red_team_required": True,
                    }
                )
                found = True
    if not found:
        raise RuntimeError("ERA55_NOT_FOUND_IN_ROADMAP_JSON")
    data["updated_at"] = reviewed_at
    data["git_head"] = "DYNAMIC_USE_GIT_REV_PARSE_HEAD"
    data["work_unit"] = WORK_UNIT
    atomic_write_json(path, data)


def update_master(artifact: dict[str, Any]) -> None:
    path = ROOT / "06_PROJECT_MASTER_STATE.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "PROJECT_STATUS=ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE_EVIDENCE",
        "PROJECT_STATUS=ACTIVE_ERA55_BASELINE_READY_FOR_GEMINI_PACKAGE",
        1,
    )
    timer = artifact["review"]["timer_runner_review"]
    queue = artifact["review"]["silent_drop_review"]
    sample = artifact["review"]["sample_decision"]
    section_02 = """```text
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_BASELINE_MEASUREMENT
LAST_COMPLETED_SUBSTEP=ERA55A_4_BASELINE_CONSOLIDATION_AND_EXTENDED_SAMPLE_REVIEW
BASELINE_READY_FOR_A5=true
BASELINE_SUFFICIENT_FOR_OPTIMIZATION_APPLY=false
P0_QUEUE_RISK_OPEN=true
GEMINI_RED_TEAM_REQUIRED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
```

A4 determined that the baseline is sufficient for the A5 report and Gemini review, but insufficient for optimization apply."""
    section_03 = f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_MUTATION=false
```

Historical journal durations are treated as `{timer['journal_duration_precision']}`. The precise natural runner sample is `{timer['precise_natural_runner_ms']} ms`. Queue utilization is `{queue['capacity_utilization_pct']}%`; overflow was not observed, but the drop ledger is absent."""
    section_09 = f"""- `P0 QUEUE_SILENT_TRUNCATION_CAPABILITY` remains open: candidate count `{queue['candidate_count']}`, capacity `{queue['capacity']}`, overflow `{queue['overflow_count']}`, drop ledger `{str(queue['drop_ledger_detected']).lower()}`.
- Historical journal p50/p95/max values are second-quantized and must not be presented as millisecond-precision measurements.
- Low-load timer overlap was not observed; stress and lock contention remain untested.
- True cold-start performance remains unverified for optimization apply.
- SQLite remains unchanged; WAL and index changes require temp-copy evidence.
- Panel propagation is visible but not granular unless exact timestamps are present.
- Optimization apply and production burst load remain blocked.
- Runtime risk is minimized, never zero.
- Git HEAD must be read dynamically."""
    section_10 = f"""```text
NEXT_SAFE_STEP={NEXT_SAFE_STEP}
```

A5 will produce one consolidated baseline report and Gemini Red Team package. It will preserve all open P0 risks and unknowns and will not authorize optimization apply."""
    text = replace_section(text, "## 02 CURRENT MAJOR-LINE POSITION", section_02)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", section_03)
    text = replace_section(text, "## 09 OPEN RISKS AND DECISIONS", section_09)
    text = replace_section(text, "## 10 NEXT SAFE STEP", section_10)
    atomic_write_text(path, text)


def update_handoff(artifact: dict[str, Any]) -> None:
    path = ROOT / "07_PROJECT_HANDOFF.md"
    text = path.read_text(encoding="utf-8")
    queue = artifact["review"]["silent_drop_review"]
    checkpoint = """PROJECT_STATUS=ACTIVE_ERA55_BASELINE_READY_FOR_GEMINI_PACKAGE
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_BASELINE_MEASUREMENT
LAST_COMPLETED_SUBSTEP=ERA55A_4_BASELINE_CONSOLIDATION_AND_EXTENDED_SAMPLE_REVIEW
BASELINE_READY_FOR_A5=true
BASELINE_SUFFICIENT_FOR_OPTIMIZATION_APPLY=false
P0_QUEUE_RISK_OPEN=true
GEMINI_RED_TEAM_REQUIRED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A4 is closed. No runner, service, timer, database, queue policy or panel mutation was applied."""
    last_work = f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=null

A5 must package the evidence without hiding queue saturation or missing stress/cold-start evidence."""
    do_not = """- Do not reopen ERA54.
- Do not rebuild NEWS from zero.
- Do not treat second-precision journal durations as exact millisecond measurements.
- Do not claim zero queue loss while no drop ledger exists.
- Do not manually invoke or restart the production runner for baseline claims.
- Do not change the service, timer, SQLite mode, index, cache or queue policy.
- Do not run production BURST_LOAD.
- Do not infer cold-start, lock-contention or panel-latency results that were not measured.
- Do not apply optimization before Gemini Red Team review."""
    decisions = f"""Current authorized direction:

- A1 inspection, A2 plan, A3 evidence and A4 consolidation are complete.
- Baseline is sufficient for A5 and Gemini review.
- Queue capacity utilization is `{queue['capacity_utilization_pct']}%`; the P0 ledger gap remains open.
- Optimization apply and burst load remain unauthorized.

NEXT_SAFE_STEP={NEXT_SAFE_STEP}"""
    execution = f"""1. Read `PROJECT_RUNTIME.json`.
2. Confirm `{NEXT_SAFE_STEP}` is current.
3. Verify local and remote `main` synchronization.
4. Read A1-A4 artifacts.
5. Generate one concise baseline report and Gemini Red Team package.
6. Mark journal precision, cold-start, stress/lock and panel granularity limits explicitly.
7. Keep queue silent-truncation capability as P0 open.
8. Do not authorize optimization apply.
9. Wait for Gemini findings before selecting implementation targets."""
    text = replace_section(text, "## 02 CURRENT CONTINUATION CHECKPOINT", checkpoint)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", last_work)
    text = replace_section(text, "## 06 DO NOT REOPEN OR REPEAT", do_not)
    text = replace_section(text, "## 07 ALLOWED NEXT DECISIONS", decisions)
    text = replace_section(text, "## 08 NEXT SESSION EXECUTION RULE", execution)
    atomic_write_text(path, text)


def append_history(reviewed_at: str, head_before: str) -> None:
    path = ROOT / "PROJECT_HISTORY.json"
    data = load_json(path)
    events = data.get("events")
    if not isinstance(events, list):
        raise RuntimeError("PROJECT_HISTORY_EVENTS_INVALID")
    event_id = "ERA55A4_BASELINE_CONSOLIDATION_REVIEW_V1"
    if not any(isinstance(item, dict) and item.get("event_id") == event_id for item in events):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": reviewed_at,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "BASELINE_CONSOLIDATION_AND_SAMPLE_SUFFICIENCY_REVIEW",
                "status": "CLOSED",
                "result": RESULT,
                "head_before_commit": head_before,
                "artifact": ARTIFACT_REL,
                "report": REPORT_REL,
                "baseline_ready_for_a5": True,
                "baseline_sufficient_for_optimization_apply": False,
                "p0_queue_risk_open": True,
                "live_runtime_db_service_timer_panel_mutation": False,
                "next_safe_step": NEXT_SAFE_STEP,
                "gemini_red_team_required": True,
            }
        )
    data["updated_at"] = reviewed_at
    data["updated_at_utc"] = reviewed_at
    atomic_write_json(path, data)


def append_almanac(artifact: dict[str, Any]) -> None:
    path = ROOT / "04_ALMANAC.md"
    text = path.read_text(encoding="utf-8")
    heading = "## ERA55A_4 BASELINE CONSOLIDATION AND EXTENDED SAMPLE REVIEW"
    if heading in text:
        return
    marker = "\n---\n\n## ALMANAC RECORD INSERTION AND CORRECTION CONSTITUTION"
    if text.count(marker) != 1:
        raise RuntimeError("ALMANAC_INSERTION_MARKER_INVALID")
    timer = artifact["review"]["timer_runner_review"]
    queue = artifact["review"]["silent_drop_review"]
    entry = f"""
---

{heading}

- Status: `CLOSED`
- Result: `{RESULT}`
- Baseline sufficient for A5/Gemini: `true`
- Baseline sufficient for optimization apply: `false`
- Historical 24h cycles: `{timer['historical_cycle_count_24h']}`
- Journal duration precision: `{timer['journal_duration_precision']}`
- Precise natural runner duration: `{timer['precise_natural_runner_ms']} ms`
- Queue utilization: `{queue['capacity_utilization_pct']}%`
- Queue overflow current snapshot: `{queue['overflow_count']}`
- Drop ledger: `{str(queue['drop_ledger_detected']).lower()}`
- P0 queue risk: `OPEN`
- Service/timer/DB/queue/panel mutation: `false`
- Next safe step: `{NEXT_SAFE_STEP}`
"""
    atomic_write_text(path, text.replace(marker, entry + marker, 1))


def make_report(artifact: dict[str, Any]) -> str:
    review = artifact["review"]
    return f"""# ERA55A_4 BASELINE CONSOLIDATION AND EXTENDED SAMPLE REVIEW

Result: `{RESULT}`

ERA55 status: `OPEN`

Live runtime/DB/service/timer/queue/panel mutation: `false`

## Consolidated Decision

```json
{json.dumps(review['sample_decision'], ensure_ascii=False, indent=2)}
```

## Timer and Runner

```json
{json.dumps(review['timer_runner_review'], ensure_ascii=False, indent=2)}
```

The historical journal values are second-quantized. They show cycle completion and broad stability, not exact millisecond distribution. The natural systemd monotonic sample is the precise low-load duration evidence.

## Silent Drop

```json
{json.dumps(review['silent_drop_review'], ensure_ascii=False, indent=2)}
```

Current overflow was not observed. The queue was exactly at capacity and no ledger exists; therefore historical zero-loss cannot be claimed and the P0 capability remains open.

## Cold Start

```json
{json.dumps(review['cold_start_review'], ensure_ascii=False, indent=2)}
```

## SQLite

```json
{json.dumps(review['sqlite_review'], ensure_ascii=False, indent=2)}
```

## Panel Propagation

```json
{json.dumps(review['panel_propagation_review'], ensure_ascii=False, indent=2)}
```

## Data Correctness

```json
{json.dumps(review['data_correctness_review'], ensure_ascii=False, indent=2)}
```

## P0 Gates

```json
{json.dumps(review['p0_gates'], ensure_ascii=False, indent=2)}
```

## Decision

- Proceed to A5 baseline report and Gemini Red Team package.
- Do not wait passively for another production overflow before A5.
- Do not claim baseline sufficiency for optimization apply.
- Do not apply watchdog, WAL, index, cache or queue changes.
- Do not run production burst load.
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
            "UNEXPECTED_VISIBLE_CHANGED_FILES\nEXPECTED="
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
            "STAGED_FILES_MISMATCH\nEXPECTED="
            + json.dumps(expected)
            + "\nACTUAL="
            + json.dumps(staged)
        )
    git("commit", "-m", "ERA55A4_BASELINE_CONSOLIDATION | OK | A5_READY_NO_APPLY")
    local_head = git("rev-parse", "HEAD")
    run(["git", "push", "origin", "main"], timeout=300)
    git("fetch", "origin", "main")
    remote_head = git("rev-parse", "origin/main")
    if local_head != remote_head:
        raise RuntimeError(f"POST_PUSH_HEAD_MISMATCH:LOCAL={local_head}:REMOTE={remote_head}")
    if git("status", "--porcelain"):
        raise RuntimeError("POST_PUSH_WORKTREE_NOT_CLEAN")
    return local_head, remote_head


def main() -> int:
    head_before = preconditions()
    backup_dir = Path(tempfile.mkdtemp(prefix="era55a4_backup_", dir="/tmp"))
    for rel in CANONICAL_FILES:
        source = ROOT / rel
        target = backup_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    committed = False
    try:
        reviewed_at = utc_now()
        a1 = load_json(ROOT / A1_REL)
        a2 = load_json(ROOT / A2_REL)
        a3 = load_json(ROOT / A3_REL)

        review = consolidate(a1, a2, a3)
        artifact = build_artifact(reviewed_at, head_before, review)

        atomic_write_json(ROOT / ARTIFACT_REL, artifact)
        atomic_write_text(ROOT / REPORT_REL, make_report(artifact))
        update_runtime(reviewed_at, artifact)
        update_roadmap_json(reviewed_at)
        update_master(artifact)
        update_handoff(artifact)
        append_history(reviewed_at, head_before)
        append_almanac(artifact)

        for rel in (
            ARTIFACT_REL,
            "PROJECT_RUNTIME.json",
            "PROJECT_HISTORY.json",
            "data/tokenoskobi_v1_v8_master_era_roadmap.json",
        ):
            load_json(ROOT / rel)

        head_after, remote_after = commit_and_push(CANONICAL_FILES + GENERATED_FILES)
        committed = True

        timer = review["timer_runner_review"]
        queue = review["silent_drop_review"]
        sample = review["sample_decision"]
        panel = review["panel_propagation_review"]
        cold = review["cold_start_review"]
        sqlite_review = review["sqlite_review"]

        print("ERA55A4_BASELINE_CONSOLIDATION=SUCCESS")
        print(f"RESULT={RESULT}")
        print(f"HEAD_BEFORE={head_before}")
        print(f"CANONICAL_HEAD={head_after}")
        print(f"REMOTE_HEAD={remote_after}")
        print("ERA55_STATUS=OPEN")
        print(f"LAST_COMPLETED={WORK_UNIT}")
        print(f"NEXT_SAFE_STEP={NEXT_SAFE_STEP}")
        print(f"BASELINE_SUFFICIENT_FOR_A5={str(sample['baseline_sufficient_for_a5_report']).lower()}")
        print(f"BASELINE_SUFFICIENT_FOR_OPTIMIZATION_APPLY={str(sample['baseline_sufficient_for_optimization_apply']).lower()}")
        print(f"JOURNAL_DURATION_PRECISION={timer['journal_duration_precision']}")
        print(f"HISTORICAL_24H_CYCLES={timer['historical_cycle_count_24h']}")
        print(f"PRECISE_NATURAL_RUNNER_MS={timer['precise_natural_runner_ms']}")
        print(f"PRECISE_TIMER_MARGIN_MS={timer['precise_natural_safety_margin_ms']}")
        print(f"RUNNER_INTERVAL_UTILIZATION_PCT={timer['runner_interval_utilization_pct']}")
        print(f"RUNNER_TIMEOUT_UTILIZATION_PCT={timer['runner_timeout_utilization_pct']}")
        print(f"WATCHDOG_DECISION={timer['watchdog_decision']}")
        print(f"QUEUE_CAPACITY={queue['capacity']}")
        print(f"QUEUE_CANDIDATES={queue['candidate_count']}")
        print(f"QUEUE_UTILIZATION_PCT={queue['capacity_utilization_pct']}")
        print(f"QUEUE_OVERFLOW={queue['overflow_count']}")
        print(f"DROP_LEDGER_DETECTED={str(queue['drop_ledger_detected']).lower()}")
        print(f"P0_QUEUE_STATUS={queue['p0_status']}")
        print(f"COLD_START_STATUS={cold['classification']}")
        print(f"PANEL_PROPAGATION_STATUS={panel['status']}")
        print(f"SQLITE_DECISION={sqlite_review['decision']}")
        print("OPTIMIZATION_APPLY_AUTHORIZED=false")
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
        print(f"ERA55A4_BASELINE_CONSOLIDATION=FAILED:{exc}", file=sys.stderr)
        raise
