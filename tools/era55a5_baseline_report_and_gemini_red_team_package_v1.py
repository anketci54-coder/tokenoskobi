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
WORK_UNIT = "ERA55A_5_BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE"
RESULT = "OK_BASELINE_REPORT_AND_GEMINI_PACKAGE_READY_NO_APPLY"
A1_REL = "data/control/era55_runtime_optimization_init_v1.json"
A2_REL = "data/control/era55a2_granular_instrumentation_and_baseline_measurement_plan_v1.json"
A3_REL = "data/control/era55a3_natural_cycle_baseline_collection_v1.json"
A4_REL = "data/control/era55a4_baseline_consolidation_and_extended_sample_review_v1.json"
ARTIFACT_REL = "data/control/era55a5_baseline_report_and_gemini_red_team_package_v1.json"
REPORT_REL = "reports/LATEST_ERA55A5_BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE.md"
NEXT_SAFE_STEP = "ERA55A_6_GEMINI_RED_TEAM_REVIEW_AND_FINDINGS_REGISTER"

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
    for rel in (A1_REL, A2_REL, A3_REL, A4_REL):
        if not (ROOT / rel).is_file():
            raise RuntimeError(f"BLOCKED=SOURCE_ARTIFACT_MISSING:{rel}")
    return local_head


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def build_package(
    generated_at: str,
    head_before: str,
    a1: dict[str, Any],
    a2: dict[str, Any],
    a3: dict[str, Any],
    a4: dict[str, Any],
) -> dict[str, Any]:
    review = a4.get("review") or {}
    timer = review.get("timer_runner_review") or {}
    queue = review.get("silent_drop_review") or {}
    cold = review.get("cold_start_review") or {}
    sqlite_review = review.get("sqlite_review") or {}
    panel = review.get("panel_propagation_review") or {}
    correctness = review.get("data_correctness_review") or {}
    sample = review.get("sample_decision") or {}

    require(a1.get("result") == "WARN_P0_FINDINGS_RECORDED_READONLY", "A1_RESULT_INVALID")
    require(a2.get("result") == "OK_PLAN_LOCKED_NO_LIVE_MUTATION", "A2_RESULT_INVALID")
    require(a3.get("status") == "CLOSED_BASELINE_EVIDENCE_RECORDED", "A3_STATUS_INVALID")
    require(a4.get("result") == "WARN_BASELINE_SUFFICIENT_FOR_A5_P0_REMAINS_OPEN", "A4_RESULT_INVALID")
    require(sample.get("baseline_sufficient_for_a5_report") is True, "A5_BASELINE_NOT_READY")
    require(sample.get("baseline_sufficient_for_gemini_review") is True, "GEMINI_BASELINE_NOT_READY")
    require(sample.get("baseline_sufficient_for_optimization_apply") is False, "UNEXPECTED_OPTIMIZATION_AUTHORIZATION")
    require(correctness.get("correctness_gate_status") == "OK_FOR_BASELINE_REPORT", "CORRECTNESS_GATE_NOT_OK")
    require(queue.get("capacity") == 50, "QUEUE_CAPACITY_UNEXPECTED")
    require(queue.get("candidate_count") == 50, "QUEUE_CANDIDATE_COUNT_UNEXPECTED")
    require(queue.get("capacity_utilization_pct") == 100.0, "QUEUE_NOT_AT_RECORDED_BOUNDARY")
    require(queue.get("drop_ledger_detected") is False, "DROP_LEDGER_STATE_UNEXPECTED")

    baseline = {
        "canonical_assessment": "OPERATIONALLY_STABLE_LOW_LOAD_WITH_BOUNDARY_RISKS",
        "era55_status": "OPEN",
        "low_load_operational_stability": {
            "historical_cycles_24h": timer.get("historical_cycle_count_24h"),
            "historical_coverage_ratio": timer.get("historical_coverage_ratio"),
            "precise_natural_runner_ms": timer.get("precise_natural_runner_ms"),
            "timer_interval_ms": timer.get("timer_interval_ms"),
            "precise_timer_margin_ms": timer.get("precise_natural_safety_margin_ms"),
            "service_timeout_ms": timer.get("timeout_ms"),
            "timeout_headroom_ms": timer.get("timeout_headroom_ms"),
            "runner_interval_utilization_pct": timer.get("runner_interval_utilization_pct"),
            "runner_timeout_utilization_pct": timer.get("runner_timeout_utilization_pct"),
            "timer_overlap_observed_24h": timer.get("overlap_observed_24h"),
            "service_timeout_observed_24h": timer.get("timeout_observed_24h"),
            "watchdog_decision": timer.get("watchdog_decision"),
        },
        "queue_boundary": {
            "capacity": queue.get("capacity"),
            "candidates": queue.get("candidate_count"),
            "admitted": queue.get("admitted_count"),
            "overflow_current_snapshot": queue.get("overflow_count"),
            "capacity_utilization_pct": queue.get("capacity_utilization_pct"),
            "drop_ledger_detected": queue.get("drop_ledger_detected"),
            "silent_drop_observed_current_snapshot": queue.get("silent_drop_observed_current_snapshot"),
            "silent_drop_capability_confirmed": queue.get("silent_drop_capability_confirmed"),
            "historical_zero_loss_claim_allowed": queue.get("historical_zero_loss_claim_allowed"),
            "p0_status": queue.get("p0_status"),
        },
        "sqlite": {
            "journal_mode": sqlite_review.get("journal_mode"),
            "synchronous": sqlite_review.get("synchronous"),
            "integrity_preserved": sqlite_review.get("integrity_preserved"),
            "duplicate_uid_groups": sqlite_review.get("duplicate_uid_groups"),
            "decision": sqlite_review.get("decision"),
        },
        "cold_start": {
            "classification": cold.get("classification"),
            "true_cold_start_observed": cold.get("true_cold_start_observed"),
            "sufficient_for_optimization_apply": cold.get("sufficient_for_optimization_apply"),
            "production_restart_authorized": cold.get("production_restart_authorized"),
        },
        "panel_propagation": {
            "status": panel.get("status"),
            "file_change_visibility_observed": panel.get("file_change_visibility_observed"),
            "exact_stage_latency_available": panel.get("exact_stage_latency_available"),
            "sufficient_for_optimization_apply": panel.get("sufficient_for_optimization_apply"),
        },
        "data_correctness": correctness,
    }

    epistemic_register = [
        {
            "claim": "The runtime is stable under the observed low-load profile.",
            "classification": "PROVEN_WITHIN_OBSERVED_SCOPE",
            "evidence": "72/72 natural timer cycles, no observed overlap or timeout, one precise 939.311 ms natural sample.",
            "limit": "Does not prove burst, lock-contention or cold-start stability.",
        },
        {
            "claim": "The hot queue is at its configured boundary.",
            "classification": "PROVEN_CURRENT_SNAPSHOT",
            "evidence": "50 deduplicated candidates, 50 admitted, capacity 50.",
            "limit": "Single/current snapshot; historical occupancy distribution is unavailable.",
        },
        {
            "claim": "A silent drop occurred in the measured snapshot.",
            "classification": "NOT_OBSERVED",
            "evidence": "Current overflow count is zero.",
            "limit": "Historical zero-loss cannot be claimed because no disposition/drop ledger exists.",
        },
        {
            "claim": "Silent truncation is possible.",
            "classification": "PROVEN_CAPABILITY",
            "evidence": "Deterministic top-50 policy exists and the queue is exactly saturated.",
            "limit": "Occurrence frequency is unknown.",
        },
        {
            "claim": "SQLite DELETE journal mode is the dominant cause of the 939.311 ms runtime.",
            "classification": "HYPOTHESIS_UNPROVEN",
            "evidence": "DELETE mode is present; no controlled DELETE-vs-WAL benchmark exists.",
            "limit": "Must be tested on immutable/temp copy with durability and recovery gates.",
        },
        {
            "claim": "The current 70-second timeout is unsafe under lock contention.",
            "classification": "UNTESTED_RISK",
            "evidence": "No timeout or overlap was observed at low load; lock and kill tests were not run.",
            "limit": "No production kill/restart is authorized.",
        },
        {
            "claim": "Historical runner p95/p99 is known at millisecond precision.",
            "classification": "NOT_PROVEN",
            "evidence": "Historical values are journal-derived; one monotonic natural sample is precise.",
            "limit": "Stage-level perf_counter_ns instrumentation is still absent.",
        },
        {
            "claim": "DB-to-panel propagation latency is known.",
            "classification": "NOT_PROVEN",
            "evidence": "File change visibility was observed but exact stage latency was not measured.",
            "limit": "Stale-data exposure duration is unknown.",
        },
    ]

    disposition_ledger_contract = {
        "priority": "P0",
        "purpose": "Make every candidate disposition observable before any speed optimization.",
        "must_record": [
            "batch_uid",
            "policy_version",
            "queue_capacity",
            "source_candidate_count",
            "normalized_candidate_count",
            "deduplicated_candidate_count",
            "candidate_rank",
            "hot_uid",
            "event_uid_or_news_uid",
            "lane",
            "priority_score",
            "disposition",
            "disposition_reason",
            "admitted_at_utc_or_dropped_at_utc",
            "lowest_admitted_priority",
            "highest_overflow_priority",
            "source_snapshot_hash",
        ],
        "allowed_dispositions": [
            "ADMITTED",
            "DUPLICATE_REMOVED",
            "UNSAFE_AUTHORITY_FILTERED",
            "OVERFLOW_TRUNCATED",
            "REPLACED_BY_HIGHER_PRIORITY",
            "INVALID_CANDIDATE",
        ],
        "hard_properties": {
            "atomic_write": True,
            "deterministic_uid": True,
            "no_silent_disposition": True,
            "append_or_immutable_batch_record": True,
            "bounded_retention_policy_must_be_explicit": True,
            "runtime_failure_must_fail_closed_or_emit_incomplete_batch_marker": True,
            "trade_wallet_signing_order_authority": 0,
        },
        "apply_status": "DESIGN_REQUIRED_NOT_AUTHORIZED",
    }

    temp_copy_matrix = {
        "environment": "IMMUTABLE_OR_DISPOSABLE_TEMP_COPY_ONLY",
        "production_db_burst_test": False,
        "production_service_kill_test": False,
        "test_families": [
            {
                "id": "DELETE_VS_WAL",
                "variants": ["DELETE_CURRENT", "WAL_CANDIDATE"],
                "measure": [
                    "total_runtime_ns",
                    "stage_runtime_ns",
                    "fsync_or_commit_latency_proxy",
                    "db_size_delta",
                    "wal_or_journal_size",
                    "write_amplification_bytes",
                    "reader_block_ms",
                    "writer_lock_ms",
                    "integrity_check",
                    "quick_check",
                    "event_count",
                    "uid_set_hash",
                ],
                "decision_rule": "WAL may proceed only if correctness and recovery are identical and measured benefit is material.",
            },
            {
                "id": "BURST_SATURATION_LOCK",
                "variants": ["NORMAL", "QUEUE_OVER_CAPACITY", "SLOW_IO", "CONCURRENT_READER", "CONCURRENT_WRITER"],
                "measure": [
                    "queue_candidate_count",
                    "admitted_count",
                    "overflow_count",
                    "drop_ledger_completeness",
                    "lock_wait_ms",
                    "timeout_count",
                    "stage_runtime_ns",
                    "recovery_result",
                ],
                "decision_rule": "No unledgered event disposition and no data-integrity regression.",
            },
            {
                "id": "PROCESS_KILL_RECOVERY",
                "variants": ["KILL_BEFORE_COMMIT", "KILL_DURING_COMMIT", "KILL_AFTER_COMMIT_BEFORE_PANEL_PUBLISH"],
                "measure": [
                    "atomic_batch_state",
                    "partial_rows",
                    "orphan_rows",
                    "duplicate_rows",
                    "integrity_check",
                    "quick_check",
                    "event_count",
                    "uid_set_hash",
                    "panel_snapshot_consistency",
                ],
                "decision_rule": "Recovery must be deterministic with no ambiguous committed state.",
            },
            {
                "id": "FULL_REFRESH_VS_DELTA",
                "variants": ["FULL_REFRESH_CURRENT", "DELTA_CANDIDATE"],
                "measure": [
                    "rows_read",
                    "rows_written",
                    "bytes_written",
                    "runtime_ns",
                    "lock_wait_ms",
                    "event_count",
                    "uid_set_hash",
                    "panel_equivalence_hash",
                ],
                "decision_rule": "Delta may proceed only with byte-for-byte or semantic equivalence and zero UID loss.",
            },
        ],
    }

    instrumentation_contract = {
        "priority": "P2_BEFORE_PERFORMANCE_CLAIM",
        "clock": "time.perf_counter_ns",
        "required_stages": [
            "RUNNER_TOTAL",
            "RAW_PRODUCER",
            "DERIVED_REFRESH",
            "QUEUE_BUILD",
            "QUEUE_LEDGER_WRITE",
            "HOT_GATEWAY_PUBLISH",
            "PANEL_BRIDGE_PUBLISH",
            "PANEL_VISIBLE_SNAPSHOT",
        ],
        "required_fields": [
            "run_uid",
            "stage",
            "start_ns",
            "end_ns",
            "duration_ns",
            "rows_in",
            "rows_out",
            "bytes_before",
            "bytes_after",
            "result",
            "error_code",
        ],
        "stale_guard_requirement": {
            "db_source_timestamp": True,
            "gateway_generated_at_utc": True,
            "panel_generated_at_utc": True,
            "age_ms": True,
            "stale_threshold_ms": True,
            "visible_stale_flag": True,
        },
        "apply_status": "PLAN_REQUIRED_NOT_AUTHORIZED",
    }

    correctness_gate = {
        "event_count_loss": 0,
        "uid_loss": 0,
        "duplicate_regression": 0,
        "integrity_check": "ok",
        "quick_check": "ok",
        "authority_regression": 0,
        "queue_disposition_without_ledger": 0,
        "panel_equivalence_required": True,
        "speed_gain_cannot_override_correctness": True,
        "failure_decision": "REJECT_OPTIMIZATION",
    }

    intervention_order = [
        {
            "order": 1,
            "priority": "P0",
            "id": "DISPOSITION_DROP_LEDGER",
            "mode": "DESIGN_THEN_TEMP_COPY_VALIDATION_BEFORE_PRODUCTION_APPLY",
            "reason": "Queue is 50/50 and historical zero-loss cannot be claimed.",
        },
        {
            "order": 2,
            "priority": "P1",
            "id": "TEMP_COPY_DELETE_VS_WAL_BENCHMARK",
            "mode": "HYPOTHESIS_TEST_ONLY",
            "reason": "DELETE mode is present; bottleneck attribution is not proven.",
        },
        {
            "order": 3,
            "priority": "P1",
            "id": "TEMP_COPY_BURST_LOCK_KILL_RECOVERY",
            "mode": "ISOLATED_FAILURE_TEST",
            "reason": "Stress, lock contention and atomic recovery remain untested.",
        },
        {
            "order": 4,
            "priority": "P2",
            "id": "PERF_COUNTER_NS_STAGE_TIMING",
            "mode": "GRANULAR_OBSERVABILITY",
            "reason": "Historical journal timing is insufficient for precise stage claims.",
        },
        {
            "order": 5,
            "priority": "P2",
            "id": "DB_TO_PANEL_PROPAGATION_AND_STALE_GUARD",
            "mode": "EXTERNAL_CORRELATION_THEN_GUARD_DESIGN",
            "reason": "Panel change is visible but exact latency and stale exposure are unknown.",
        },
        {
            "order": 6,
            "priority": "P2",
            "id": "FULL_REFRESH_VS_DELTA_WRITE_AMPLIFICATION",
            "mode": "TEMP_COPY_EQUIVALENCE_BENCHMARK",
            "reason": "Delta refresh is a candidate, not an approved optimization.",
        },
    ]

    gemini_request = {
        "role": "Tokenoskobi ERA55 independent adversarial runtime reviewer",
        "mission": "Attack the baseline conclusions, identify missing failure modes, and issue a structured verdict before any optimization apply.",
        "hard_rules": [
            "Do not assume facts not present in A1-A5 evidence.",
            "Separate proven facts, hypotheses, not-observed conditions and untested risks.",
            "Do not recommend production burst, kill, restart, WAL, index, cache or queue-policy changes.",
            "All destructive or load tests must use immutable/disposable temp copies and isolated subprocesses.",
            "Any performance recommendation that risks event or UID loss must be rejected.",
            "Trade, wallet, signing and order authority remain zero.",
        ],
        "required_reviews": [
            {
                "id": "QUEUE_LEDGER",
                "question": "Can the proposed disposition ledger prove every admitted, filtered, deduplicated, replaced and overflow-truncated candidate without becoming a new silent-failure point?",
            },
            {
                "id": "QUEUE_ATTACKS",
                "question": "Which adversarial burst, priority-tie, duplicate-UID, malformed-candidate and ledger-write-failure scenarios are missing?",
            },
            {
                "id": "SQLITE_DELETE_WAL",
                "question": "Is the DELETE-vs-WAL temp-copy matrix sufficient to measure latency, locks, durability, recovery and write amplification without bias?",
            },
            {
                "id": "KILL_RECOVERY",
                "question": "Which exact kill points and post-recovery invariants are required to prove atomic state across DB, gateway and panel publication?",
            },
            {
                "id": "TIMING",
                "question": "Does perf_counter_ns stage instrumentation avoid observer distortion and capture p50/p95/p99 under normal, cold, slow-IO and contention conditions?",
            },
            {
                "id": "PANEL_STALENESS",
                "question": "What minimum stale-data contract prevents users from treating old panel data as current?",
            },
            {
                "id": "DELTA_REFRESH",
                "question": "What equivalence and rollback gates are required before replacing full refresh with delta processing?",
            },
            {
                "id": "UNKNOWN_UNKNOWNS",
                "question": "Identify additional race conditions, crash windows, corruption paths, observability failures and adversarial inputs not covered by this package.",
            },
        ],
        "required_output_schema": {
            "overall_verdict": "ACCEPT | CONDITIONAL_ACCEPT | REJECT",
            "optimization_apply_verdict": "MUST_BE_REJECT_UNTIL_GATES_CLOSE",
            "findings": [
                {
                    "priority": "P0 | P1 | P2 | INFO",
                    "code": "stable_identifier",
                    "claim_attacked": "package claim",
                    "finding": "specific finding",
                    "evidence_basis": "provided evidence or explicit absence",
                    "required_fix_or_test": "concrete action",
                    "blocks_production_apply": True,
                }
            ],
            "ledger_verdict": {
                "design_sufficient": False,
                "missing_fields_or_failure_modes": [],
                "minimum_acceptance_tests": [],
            },
            "temp_copy_test_verdict": {
                "matrix_sufficient": False,
                "missing_variants": [],
                "required_metrics": [],
            },
            "correctness_gate_verdict": {
                "gate_sufficient": False,
                "missing_invariants": [],
            },
            "recommended_next_safe_step": "single canonical work unit",
        },
    }

    return {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "era": "ERA55",
        "title": "Runtime Optimization",
        "generated_at_utc": generated_at,
        "status": "PACKAGE_READY_REVIEW_PENDING",
        "result": RESULT,
        "head_before_commit": head_before,
        "source_artifacts": {
            "a1": A1_REL,
            "a2": A2_REL,
            "a3": A3_REL,
            "a4": A4_REL,
        },
        "baseline": baseline,
        "epistemic_register": epistemic_register,
        "red_team_intervention_order": intervention_order,
        "p0_disposition_ledger_contract": disposition_ledger_contract,
        "temp_copy_validation_matrix": temp_copy_matrix,
        "granular_instrumentation_contract": instrumentation_contract,
        "optimization_correctness_gate": correctness_gate,
        "gemini_review_request": gemini_request,
        "decision": {
            "baseline_report_complete": True,
            "gemini_package_ready": True,
            "gemini_review_complete": False,
            "optimization_apply_authorized": False,
            "production_burst_load_authorized": False,
            "production_process_kill_authorized": False,
            "production_service_timer_change_authorized": False,
            "production_database_change_authorized": False,
            "queue_policy_change_authorized": False,
            "drop_ledger_apply_authorized": False,
            "watchdog_apply_authorized": False,
            "wal_apply_authorized": False,
            "index_apply_authorized": False,
            "delta_refresh_apply_authorized": False,
        },
        "next_safe_step": NEXT_SAFE_STEP,
        "mutation_statement": {
            "live_runtime": False,
            "database": False,
            "service": False,
            "timer": False,
            "panel": False,
            "queue_policy": False,
            "drop_ledger": False,
            "watchdog": False,
            "index": False,
            "journal_mode": False,
            "cache": False,
            "delta_refresh": False,
        },
    }


def make_gemini_prompt(package: dict[str, Any]) -> str:
    baseline = package["baseline"]
    queue = baseline["queue_boundary"]
    runtime = baseline["low_load_operational_stability"]
    sqlite_data = baseline["sqlite"]
    cold = baseline["cold_start"]
    panel = baseline["panel_propagation"]
    request = package["gemini_review_request"]
    return f"""You are the independent Gemini Red Team reviewer for Tokenoskobi ERA55 Runtime Optimization.

CANONICAL ASSESSMENT
- State: {baseline['canonical_assessment']}
- ERA55: OPEN
- Optimization apply: NOT AUTHORIZED
- Production burst/kill/restart/DB mode change: NOT AUTHORIZED

PROVEN BASELINE
- 24h natural cycles: {runtime['historical_cycles_24h']}
- Coverage ratio: {runtime['historical_coverage_ratio']}
- Precise natural runner: {runtime['precise_natural_runner_ms']} ms
- Timer interval: {runtime['timer_interval_ms']} ms
- Precise timer margin: {runtime['precise_timer_margin_ms']} ms
- Service timeout: {runtime['service_timeout_ms']} ms
- Timer overlap observed: {runtime['timer_overlap_observed_24h']}
- Service timeout observed: {runtime['service_timeout_observed_24h']}
- Queue: {queue['candidates']}/{queue['capacity']} candidates, {queue['admitted']} admitted, overflow {queue['overflow_current_snapshot']}
- Queue utilization: {queue['capacity_utilization_pct']}%
- Drop ledger detected: {queue['drop_ledger_detected']}
- Silent drop current snapshot: {queue['silent_drop_observed_current_snapshot']}
- Silent truncation capability: {queue['silent_drop_capability_confirmed']}
- Historical zero-loss claim allowed: {queue['historical_zero_loss_claim_allowed']}
- SQLite journal_mode: {sqlite_data['journal_mode']}
- SQLite synchronous: {sqlite_data['synchronous']}
- SQLite integrity preserved: {sqlite_data['integrity_preserved']}
- True cold start: {cold['classification']}
- Panel propagation: {panel['status']}

MANDATORY INTERVENTION ORDER
1. P0 disposition/drop ledger design and temp-copy validation.
2. P1 DELETE-vs-WAL temp-copy benchmark.
3. P1 temp-copy burst, lock, kill and recovery tests.
4. P2 perf_counter_ns stage timing.
5. P2 DB-to-panel propagation and stale guard.
6. P2 full-refresh-vs-delta equivalence and write-amplification benchmark.

HARD CORRECTNESS GATE
{json.dumps(package['optimization_correctness_gate'], ensure_ascii=False, indent=2)}

P0 LEDGER CONTRACT
{json.dumps(package['p0_disposition_ledger_contract'], ensure_ascii=False, indent=2)}

TEMP-COPY TEST MATRIX
{json.dumps(package['temp_copy_validation_matrix'], ensure_ascii=False, indent=2)}

GRANULAR INSTRUMENTATION CONTRACT
{json.dumps(package['granular_instrumentation_contract'], ensure_ascii=False, indent=2)}

REVIEW QUESTIONS
{json.dumps(request['required_reviews'], ensure_ascii=False, indent=2)}

HARD RULES
{json.dumps(request['hard_rules'], ensure_ascii=False, indent=2)}

Return exactly one structured review using this schema:
{json.dumps(request['required_output_schema'], ensure_ascii=False, indent=2)}
"""


def make_report(package: dict[str, Any]) -> str:
    baseline = package["baseline"]
    runtime = baseline["low_load_operational_stability"]
    queue = baseline["queue_boundary"]
    sqlite_data = baseline["sqlite"]
    cold = baseline["cold_start"]
    panel = baseline["panel_propagation"]
    epistemic_lines = "\n".join(
        f"- **{item['classification']}** — {item['claim']} Evidence: {item['evidence']} Limit: {item['limit']}"
        for item in package["epistemic_register"]
    )
    intervention_lines = "\n".join(
        f"{item['order']}. **{item['priority']} {item['id']}** — {item['reason']} Mode: `{item['mode']}`"
        for item in package["red_team_intervention_order"]
    )
    prompt = make_gemini_prompt(package)
    return f"""# ERA55A_5 BASELINE REPORT AND GEMINI RED TEAM PACKAGE

Result: `{RESULT}`

Package status: `READY_REVIEW_PENDING`

Canonical assessment: `{baseline['canonical_assessment']}`

Live runtime/DB/service/timer/queue/panel mutation: `false`

## Executive Baseline

- 24-hour natural-cycle coverage: `{runtime['historical_cycles_24h']}` cycles, ratio `{runtime['historical_coverage_ratio']}`.
- Precise natural runner duration: `{runtime['precise_natural_runner_ms']} ms`.
- Timer interval: `{runtime['timer_interval_ms']} ms`; observed margin `{runtime['precise_timer_margin_ms']} ms`.
- No low-load timer overlap or service timeout was observed.
- Queue is `{queue['candidates']}/{queue['capacity']}` with `{queue['capacity_utilization_pct']}%` utilization.
- Current overflow: `{queue['overflow_current_snapshot']}`; drop ledger: `{str(queue['drop_ledger_detected']).lower()}`.
- Silent drop in current snapshot: `{str(queue['silent_drop_observed_current_snapshot']).lower()}`.
- Silent truncation capability: `{str(queue['silent_drop_capability_confirmed']).lower()}`.
- Historical zero-loss claim allowed: `{str(queue['historical_zero_loss_claim_allowed']).lower()}`.
- SQLite: `journal_mode={sqlite_data['journal_mode']}`, `synchronous={sqlite_data['synchronous']}`, integrity preserved `{str(sqlite_data['integrity_preserved']).lower()}`.
- Cold start: `{cold['classification']}`.
- Panel propagation: `{panel['status']}`.

## Epistemic Register

{epistemic_lines}

## Mandatory Intervention Order

{intervention_lines}

## P0 Disposition Ledger Contract

```json
{json.dumps(package['p0_disposition_ledger_contract'], ensure_ascii=False, indent=2)}
```

## Temp-Copy Validation Matrix

```json
{json.dumps(package['temp_copy_validation_matrix'], ensure_ascii=False, indent=2)}
```

## Granular Instrumentation and Stale Guard

```json
{json.dumps(package['granular_instrumentation_contract'], ensure_ascii=False, indent=2)}
```

## Optimization Correctness Gate

```json
{json.dumps(package['optimization_correctness_gate'], ensure_ascii=False, indent=2)}
```

## Current Decision

```json
{json.dumps(package['decision'], ensure_ascii=False, indent=2)}
```

## Gemini Red Team Copy-Paste Package

```text
{prompt.rstrip()}
```

## Next Safe Step

`{NEXT_SAFE_STEP}`

Gemini findings must be registered before any design/apply work begins. A5 does not authorize the disposition ledger, WAL, watchdog, index, cache, delta refresh, production burst, production kill or service/timer changes.
"""


def update_runtime(generated_at: str) -> None:
    path = ROOT / "PROJECT_RUNTIME.json"
    data = load_json(path)
    work_unit = {
        "id": WORK_UNIT,
        "type": "ERA55_BASELINE_REPORT_AND_EXTERNAL_RED_TEAM_PACKAGE",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "artifact": ARTIFACT_REL,
        "report": REPORT_REL,
        "status": "CLOSED_PACKAGE_READY_REVIEW_PENDING",
        "result": RESULT,
        "runtime_db_service_timer_panel_mutation": False,
        "next_step": NEXT_SAFE_STEP,
    }
    next_step = {
        "id": NEXT_SAFE_STEP,
        "type": "ERA55_EXTERNAL_RED_TEAM_REVIEW_REGISTER",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "serves": "V3_RUNTIME_INTELLIGENCE_OS",
        "purpose": "Submit the A5 package to Gemini, register its structured findings, and decide whether the package is accepted, conditionally accepted or rejected.",
        "human_authorization_required": True,
        "external_gemini_response_required": True,
        "optimization_apply_authorized": False,
        "production_burst_load_authorized": False,
        "status": "READY_FOR_EXTERNAL_REVIEW",
    }
    last_action = {
        "timestamp": generated_at,
        "task": WORK_UNIT,
        "result": RESULT,
        "artifact": ARTIFACT_REL,
    }
    data["mode"] = "ERA55A5_BASELINE_REPORT_GEMINI_PACKAGE_READY"
    data["project_status"] = "ACTIVE_ERA55_AWAITING_GEMINI_RED_TEAM_REVIEW"
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
            "updated_at": generated_at,
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
            "active_stage": "ERA55A_EXTERNAL_RED_TEAM_GATE",
            "last_completed_substep": WORK_UNIT,
            "next_safe_step": NEXT_SAFE_STEP,
            "a5_artifact": ARTIFACT_REL,
            "a5_report": REPORT_REL,
            "baseline_report_complete": True,
            "gemini_package_ready": True,
            "gemini_review_complete": False,
            "p0_queue_risk_open": True,
            "optimization_apply_authorized": False,
            "burst_load_authorized": False,
            "runtime_db_service_timer_panel_mutation": False,
            "gemini_red_team_required": True,
        }
    )
    data["open_risks"] = [
        "P0:QUEUE_SILENT_TRUNCATION_CAPABILITY:OPEN",
        "P0:GEMINI_RED_TEAM_REVIEW:PENDING",
        "P1:TRUE_COLD_START:UNTESTED",
        "P1:STRESS_LOCK_CONTENTION:UNTESTED",
        "P1:DELETE_VS_WAL_BOTTLENECK:HYPOTHESIS_UNPROVEN",
        "P2:GRANULAR_STAGE_TIMING:MISSING",
        "P2:PANEL_PROPAGATION_LATENCY:MISSING",
        "P2:FULL_REFRESH_VS_DELTA:EQUIVALENCE_UNTESTED",
        "Risk is minimized, never zero.",
    ]
    data["source"] = "era55a5_baseline_report_gemini_package_v1"
    data["updated_at"] = generated_at
    data["updated_at_utc"] = generated_at
    atomic_write_json(path, data)


def update_roadmap_json(generated_at: str) -> None:
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
                        "active_stage": "ERA55A_EXTERNAL_RED_TEAM_GATE",
                        "last_completed_substep": WORK_UNIT,
                        "last_result": RESULT,
                        "next_safe_step": NEXT_SAFE_STEP,
                        "a5_artifact": ARTIFACT_REL,
                        "a5_report": REPORT_REL,
                        "baseline_report_complete": True,
                        "gemini_package_ready": True,
                        "gemini_review_complete": False,
                        "p0_queue_risk_open": True,
                        "optimization_apply_authorized": False,
                        "burst_load_authorized": False,
                        "gemini_red_team_required": True,
                    }
                )
                found = True
    if not found:
        raise RuntimeError("ERA55_NOT_FOUND_IN_ROADMAP_JSON")
    data["updated_at"] = generated_at
    data["git_head"] = "DYNAMIC_USE_GIT_REV_PARSE_HEAD"
    data["work_unit"] = WORK_UNIT
    atomic_write_json(path, data)


def update_master(package: dict[str, Any]) -> None:
    path = ROOT / "06_PROJECT_MASTER_STATE.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "PROJECT_STATUS=ACTIVE_ERA55_BASELINE_READY_FOR_GEMINI_PACKAGE",
        "PROJECT_STATUS=ACTIVE_ERA55_AWAITING_GEMINI_RED_TEAM_REVIEW",
        1,
    )
    runtime = package["baseline"]["low_load_operational_stability"]
    queue = package["baseline"]["queue_boundary"]
    section_02 = """```text
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_EXTERNAL_RED_TEAM_GATE
LAST_COMPLETED_SUBSTEP=ERA55A_5_BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE
BASELINE_REPORT_COMPLETE=true
GEMINI_PACKAGE_READY=true
GEMINI_REVIEW_COMPLETE=false
P0_QUEUE_RISK_OPEN=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
```

A5 produced the canonical baseline report and structured Gemini Red Team package. No runtime optimization was applied."""
    section_03 = f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED_PACKAGE_READY_REVIEW_PENDING
LIVE_RUNTIME_MUTATION=false
```

Observed low-load runner duration is `{runtime['precise_natural_runner_ms']} ms`. Queue remains `{queue['candidates']}/{queue['capacity']}` with no drop ledger. The package separates proven facts, hypotheses and untested risks."""
    section_09 = """- `P0 QUEUE_SILENT_TRUNCATION_CAPABILITY` remains open; disposition ledger design and temp-copy validation are mandatory before production apply.
- `P0 GEMINI_RED_TEAM_REVIEW` is pending.
- DELETE journal bottleneck attribution is an unproven hypothesis.
- True cold-start, burst, slow-IO, lock-contention and kill-recovery behavior remain untested.
- Granular stage timing and exact DB-to-panel propagation latency remain unknown.
- Full refresh versus delta equivalence and write amplification remain untested.
- Optimization apply, production burst, production kill, WAL, index, watchdog, cache and queue changes remain blocked.
- Runtime risk is minimized, never zero.
- Git HEAD must be read dynamically."""
    section_10 = f"""```text
NEXT_SAFE_STEP={NEXT_SAFE_STEP}
```

Submit the copy-paste package in the A5 report to Gemini. Register its structured findings without altering or interpreting missing evidence. No implementation begins before this gate closes."""
    text = replace_section(text, "## 02 CURRENT MAJOR-LINE POSITION", section_02)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", section_03)
    text = replace_section(text, "## 09 OPEN RISKS AND DECISIONS", section_09)
    text = replace_section(text, "## 10 NEXT SAFE STEP", section_10)
    atomic_write_text(path, text)


def update_handoff(package: dict[str, Any]) -> None:
    path = ROOT / "07_PROJECT_HANDOFF.md"
    text = path.read_text(encoding="utf-8")
    queue = package["baseline"]["queue_boundary"]
    checkpoint = """PROJECT_STATUS=ACTIVE_ERA55_AWAITING_GEMINI_RED_TEAM_REVIEW
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_EXTERNAL_RED_TEAM_GATE
LAST_COMPLETED_SUBSTEP=ERA55A_5_BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE
BASELINE_REPORT_COMPLETE=true
GEMINI_PACKAGE_READY=true
GEMINI_REVIEW_COMPLETE=false
P0_QUEUE_RISK_OPEN=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A5 is closed. The package is ready, but external review is not yet complete."""
    last_work = f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED_PACKAGE_READY_REVIEW_PENDING
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=null

Queue is `{queue['candidates']}/{queue['capacity']}` and the P0 disposition-ledger gap remains open."""
    do_not = """- Do not reopen ERA54.
- Do not begin disposition-ledger implementation before Gemini findings are registered.
- Do not claim a DELETE-mode bottleneck without temp-copy comparison.
- Do not run production burst, kill, restart, service/timer or SQLite-mode tests.
- Do not apply watchdog, WAL, index, cache, delta refresh or queue-policy changes.
- Do not treat no current overflow as proof of historical zero loss.
- Do not infer cold-start, lock-contention, p99 or panel-latency results.
- Do not proceed to optimization implementation before the Gemini gate closes."""
    decisions = f"""Current authorized direction:

- The A5 report and Gemini package are ready.
- The next action is external Gemini review and exact findings registration.
- P0 disposition-ledger design is the first candidate intervention after review, not yet authorized for apply.
- All performance and runtime mutations remain blocked.

NEXT_SAFE_STEP={NEXT_SAFE_STEP}"""
    execution = f"""1. Read `PROJECT_RUNTIME.json`.
2. Confirm `{NEXT_SAFE_STEP}` is current.
3. Verify local and remote `main` synchronization.
4. Open `{REPORT_REL}`.
5. Copy the `Gemini Red Team Copy-Paste Package` section exactly to Gemini.
6. Return Gemini's complete structured response without summarizing away details.
7. Register every finding by priority and blocking status.
8. Reject any production apply recommendation that bypasses temp-copy or correctness gates.
9. Select the next canonical work unit only after the review verdict is recorded."""
    text = replace_section(text, "## 02 CURRENT CONTINUATION CHECKPOINT", checkpoint)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", last_work)
    text = replace_section(text, "## 06 DO NOT REOPEN OR REPEAT", do_not)
    text = replace_section(text, "## 07 ALLOWED NEXT DECISIONS", decisions)
    text = replace_section(text, "## 08 NEXT SESSION EXECUTION RULE", execution)
    atomic_write_text(path, text)


def append_history(generated_at: str, head_before: str) -> None:
    path = ROOT / "PROJECT_HISTORY.json"
    data = load_json(path)
    events = data.get("events")
    if not isinstance(events, list):
        raise RuntimeError("PROJECT_HISTORY_EVENTS_INVALID")
    event_id = "ERA55A5_BASELINE_REPORT_GEMINI_PACKAGE_V1"
    if not any(isinstance(item, dict) and item.get("event_id") == event_id for item in events):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": generated_at,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "BASELINE_REPORT_AND_GEMINI_RED_TEAM_PACKAGE_READY",
                "status": "CLOSED_PACKAGE_READY_REVIEW_PENDING",
                "result": RESULT,
                "head_before_commit": head_before,
                "artifact": ARTIFACT_REL,
                "report": REPORT_REL,
                "gemini_review_complete": False,
                "optimization_apply_authorized": False,
                "p0_queue_risk_open": True,
                "live_runtime_db_service_timer_panel_mutation": False,
                "next_safe_step": NEXT_SAFE_STEP,
            }
        )
    data["updated_at"] = generated_at
    data["updated_at_utc"] = generated_at
    atomic_write_json(path, data)


def append_almanac(package: dict[str, Any]) -> None:
    path = ROOT / "04_ALMANAC.md"
    text = path.read_text(encoding="utf-8")
    heading = "## ERA55A_5 BASELINE REPORT AND GEMINI RED TEAM PACKAGE"
    if heading in text:
        return
    marker = "\n---\n\n## ALMANAC RECORD INSERTION AND CORRECTION CONSTITUTION"
    if text.count(marker) != 1:
        raise RuntimeError("ALMANAC_INSERTION_MARKER_INVALID")
    queue = package["baseline"]["queue_boundary"]
    runtime = package["baseline"]["low_load_operational_stability"]
    entry = f"""
---

{heading}

- Status: `CLOSED_PACKAGE_READY_REVIEW_PENDING`
- Result: `{RESULT}`
- Canonical assessment: `OPERATIONALLY_STABLE_LOW_LOAD_WITH_BOUNDARY_RISKS`
- Precise natural runner: `{runtime['precise_natural_runner_ms']} ms`
- Queue: `{queue['candidates']}/{queue['capacity']}`; utilization `{queue['capacity_utilization_pct']}%`
- Current overflow: `{queue['overflow_current_snapshot']}`
- Drop ledger: `{str(queue['drop_ledger_detected']).lower()}`
- P0 queue risk: `OPEN`
- Gemini package: `READY`
- Gemini review: `PENDING`
- Optimization apply: `false`
- Live runtime mutation: `false`
- Next safe step: `{NEXT_SAFE_STEP}`
"""
    atomic_write_text(path, text.replace(marker, entry + marker, 1))


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


def commit_local(expected_files: list[str]) -> str:
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
    git("commit", "-m", "ERA55A5_BASELINE_REPORT_GEMINI_PACKAGE | OK | REVIEW_PENDING_NO_APPLY")
    local_head = git("rev-parse", "HEAD")
    if git("status", "--porcelain"):
        raise RuntimeError("POST_COMMIT_WORKTREE_NOT_CLEAN")
    return local_head


def main() -> int:
    head_before = preconditions()
    backup_dir = Path(tempfile.mkdtemp(prefix="era55a5_backup_", dir="/tmp"))
    for rel in CANONICAL_FILES:
        source = ROOT / rel
        target = backup_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    commit_created = False
    try:
        generated_at = utc_now()
        a1 = load_json(ROOT / A1_REL)
        a2 = load_json(ROOT / A2_REL)
        a3 = load_json(ROOT / A3_REL)
        a4 = load_json(ROOT / A4_REL)

        package = build_package(generated_at, head_before, a1, a2, a3, a4)
        atomic_write_json(ROOT / ARTIFACT_REL, package)
        atomic_write_text(ROOT / REPORT_REL, make_report(package))
        update_runtime(generated_at)
        update_roadmap_json(generated_at)
        update_master(package)
        update_handoff(package)
        append_history(generated_at, head_before)
        append_almanac(package)

        for rel in (
            ARTIFACT_REL,
            "PROJECT_RUNTIME.json",
            "PROJECT_HISTORY.json",
            "data/tokenoskobi_v1_v8_master_era_roadmap.json",
        ):
            load_json(ROOT / rel)

        local_head = commit_local(CANONICAL_FILES + GENERATED_FILES)
        commit_created = True

        baseline = package["baseline"]
        runtime = baseline["low_load_operational_stability"]
        queue = baseline["queue_boundary"]
        print("ERA55A5_BASELINE_REPORT_GEMINI_PACKAGE=SUCCESS")
        print(f"RESULT={RESULT}")
        print(f"HEAD_BEFORE={head_before}")
        print(f"LOCAL_COMMIT={local_head}")
        print("PUSH_REQUIRED=true")
        print("ERA55_STATUS=OPEN")
        print(f"LAST_COMPLETED={WORK_UNIT}")
        print(f"NEXT_SAFE_STEP={NEXT_SAFE_STEP}")
        print(f"CANONICAL_ASSESSMENT={baseline['canonical_assessment']}")
        print(f"PRECISE_NATURAL_RUNNER_MS={runtime['precise_natural_runner_ms']}")
        print(f"QUEUE_CAPACITY={queue['capacity']}")
        print(f"QUEUE_CANDIDATES={queue['candidates']}")
        print(f"QUEUE_UTILIZATION_PCT={queue['capacity_utilization_pct']}")
        print(f"QUEUE_OVERFLOW_CURRENT={queue['overflow_current_snapshot']}")
        print(f"DROP_LEDGER_DETECTED={str(queue['drop_ledger_detected']).lower()}")
        print(f"SILENT_TRUNCATION_CAPABILITY={str(queue['silent_drop_capability_confirmed']).lower()}")
        print("P0_INTERVENTION=DISPOSITION_DROP_LEDGER_DESIGN_THEN_TEMP_COPY_VALIDATION")
        print("GEMINI_PACKAGE_READY=true")
        print("GEMINI_REVIEW_COMPLETE=false")
        print("OPTIMIZATION_APPLY_AUTHORIZED=false")
        print("PRODUCTION_BURST_LOAD_AUTHORIZED=false")
        print("LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false")
        print(f"ARTIFACT={ARTIFACT_REL}")
        print(f"REPORT={REPORT_REL}")
        print("WORKTREE=CLEAN")
        print(f"BACKUP_DIR={backup_dir}")
        return 0
    except Exception:
        if not commit_created:
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
        print(f"ERA55A5_BASELINE_REPORT_GEMINI_PACKAGE=FAILED:{exc}", file=sys.stderr)
        raise
