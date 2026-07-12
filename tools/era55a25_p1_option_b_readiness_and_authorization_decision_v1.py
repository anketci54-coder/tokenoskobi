#!/usr/bin/env python3
from __future__ import annotations

import atexit
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
EXPECTED_HEAD = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()

WORK_UNIT = "ERA55A_25_P1_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION"
RESULT = "OK_OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED_PRODUCTION_APPLY_BLOCKED"
NEXT = "ERA55A_26_P1_OPTION_B_DELETE_VS_WAL_TEMP_COPY_BENCHMARK"
SUBJECT = "ERA55A25_OPTION_B_DECISION | OK | TEMP_COPY_BENCHMARK_AUTHORIZED_APPLY_BLOCKED"

OPTION_B_ID = "P1_DELETE_VS_WAL_DURABILITY_LOCK_WRITE_AMPLIFICATION_BENCHMARK"
OPTION_B_FINDING = "F2_DELETE_VS_WAL_IO_HYPOTHESIS"

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

A24R = ROOT / "data/control/era55a24r_p0_natural_cycle_evidence_recovery_and_p0_f1_closure_v1.json"
A5 = ROOT / "data/control/era55a5_baseline_report_and_gemini_red_team_package_v1.json"
A6 = ROOT / "data/control/era55a6_gemini_red_team_review_and_findings_register_v1.json"
A23 = ROOT / "data/control/era55a23_p0_guarded_general_production_writer_runtime_integration_apply_and_post_audit_v1.json"

ARTIFACT = ROOT / "data/control/era55a25_p1_option_b_readiness_and_authorization_decision_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A25_P1_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION.md"

DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
GUARDED_STATE = ROOT / "runtime/state/news_guarded_production_writer_v1.json"
RESULT_PATH = Path("/run/tokenoskobi/era55a23_guarded_result.json")
ERROR_PATH = Path("/run/tokenoskobi/era55a23_guarded_error.json")
DROPIN = Path(
    "/etc/systemd/system/tokenoskobi-news-radar-refresh.service.d/"
    "90-era55a23-guarded-production.conf"
)

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

HELPER = ROOT / "tools/era55a24_p0_post_activation_observation_and_p0_f1_closure_decision_v1.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("era55a25_helper", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("A25_HELPER_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load_helper()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(
    args: list[str],
    *,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
        timeout=timeout,
    )


def git(*args: str) -> str:
    return run(["git", *args], timeout=60).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("A25_JSON_OBJECT_REQUIRED:" + str(path))
    return value


def atomic_dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def sha(path: Path) -> str | None:
    return H.sha(path)


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def systemctl_state(unit: str) -> dict[str, Any]:
    return H.systemctl_state(unit)


def service_environment() -> dict[str, Any]:
    return H.service_environment()


def replace_section(text: str, heading: str, body: str) -> str:
    return H.replace_section(text, heading, body)


def database_snapshot() -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        quick = str(connection.execute("PRAGMA quick_check").fetchone()[0])
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        batch_rows = int(
            connection.execute(
                "SELECT COUNT(*) FROM news_disposition_batches_v2"
            ).fetchone()[0]
        )
        ledger_rows = int(
            connection.execute(
                "SELECT COUNT(*) FROM news_disposition_ledger_v2"
            ).fetchone()[0]
        )
        batches = [
            {
                "batch_sequence": int(row[0]),
                "batch_uid": str(row[1]),
                "status": str(row[2]),
                "source_candidate_count": int(row[3]),
            }
            for row in connection.execute(
                """
                SELECT batch_sequence, batch_uid, status, source_candidate_count
                FROM news_disposition_batches_v2
                ORDER BY batch_sequence
                """
            ).fetchall()
        ]
        return {
            "query_only": True,
            "journal_mode": journal_mode,
            "synchronous": synchronous,
            "integrity_check": integrity,
            "quick_check": quick,
            "foreign_key_check_rows": len(foreign_keys),
            "batch_rows": batch_rows,
            "ledger_rows": ledger_rows,
            "batches": batches,
            "size_bytes": DB.stat().st_size,
            "sha256": sha(DB),
        }
    finally:
        connection.close()


def find_finding(a6: dict[str, Any], finding_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in a6.get("findings", [])
        if isinstance(item, dict) and item.get("finding_id") == finding_id
    ]
    if len(matches) != 1:
        raise RuntimeError("A25_FINDING_CARDINALITY_INVALID:" + finding_id)
    return matches[0]


def find_matrix(a5: dict[str, Any], matrix_id: str) -> dict[str, Any]:
    matrix = a5.get("temp_copy_validation_matrix", {})
    matches = [
        item
        for item in matrix.get("test_families", [])
        if isinstance(item, dict) and item.get("id") == matrix_id
    ]
    if len(matches) != 1:
        raise RuntimeError("A25_MATRIX_CARDINALITY_INVALID:" + matrix_id)
    return matches[0]


def backup_files(directory: Path) -> dict[Path, Path]:
    backups: dict[Path, Path] = {}
    for index, path in enumerate((RUNTIME, HISTORY, MASTER, HANDOFF, ALMANAC)):
        target = directory / f"{index:02d}.backup"
        shutil.copy2(path, target)
        backups[path] = target
    return backups


def restore_files(backups: dict[Path, Path], expected_head: str) -> None:
    for path, backup in backups.items():
        shutil.copy2(backup, path)
    for path in (ARTIFACT, REPORT):
        if path.exists():
            path.unlink()
    run(["git", "reset", "--mixed", expected_head], check=False, timeout=30)


def main() -> int:
    if not EXPECTED_HEAD:
        raise RuntimeError("TOKENOSKOBI_EXPECTED_HEAD_REQUIRED")
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BRANCH_NOT_MAIN")
    if git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("UNEXPECTED_HEAD")
    if git("status", "--porcelain"):
        raise RuntimeError("WORKTREE_NOT_CLEAN")
    if ARTIFACT.exists() or REPORT.exists():
        raise RuntimeError("A25_OUTPUT_ALREADY_EXISTS")

    required = (
        A24R,
        A5,
        A6,
        A23,
        DB,
        HOT,
        PANEL_HOT,
        BRIDGE_STATE,
        GUARDED_STATE,
        RESULT_PATH,
        DROPIN,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
        HELPER,
    )
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)

    runtime = load(RUNTIME)
    current = runtime.get("current_state", {})
    next_state = current.get("next_safe_step", {})
    if next_state.get("id") != "ERA55A_25_P0_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION":
        raise RuntimeError("A25_NOT_CURRENT_NEXT_SAFE_STEP")
    if next_state.get("p0_f1_closed") is not True:
        raise RuntimeError("A25_RUNTIME_P0_F1_NOT_CLOSED")
    if next_state.get("option_b_readiness_decision_authorized") is not True:
        raise RuntimeError("A25_READINESS_DECISION_NOT_AUTHORIZED")
    if next_state.get("option_b_authorized") is not False:
        raise RuntimeError("A25_OPTION_B_ALREADY_AUTHORIZED")
    if next_state.get("optimization_apply_authorized") is not False:
        raise RuntimeError("A25_OPTIMIZATION_APPLY_ALREADY_AUTHORIZED")

    a24r = load(A24R)
    a5 = load(A5)
    a6 = load(A6)
    a23 = load(A23)

    if a24r.get("result") != "OK_NATURAL_TIMER_EVIDENCE_RECOVERED_P0_F1_CLOSED":
        raise RuntimeError("A25_A24R_RESULT_INVALID")
    a24_auth = a24r.get("authorization", {})
    if a24_auth.get("production_writer_active") is not True:
        raise RuntimeError("A25_WRITER_NOT_ACTIVE_IN_A24R")
    if a24_auth.get("p0_f1_closed") is not True:
        raise RuntimeError("A25_P0_F1_NOT_CLOSED_IN_A24R")
    if a24_auth.get("option_b_authorized") is not False:
        raise RuntimeError("A25_OPTION_B_ALREADY_AUTHORIZED_IN_A24R")
    if a24_auth.get("optimization_apply_authorized") is not False:
        raise RuntimeError("A25_APPLY_ALREADY_AUTHORIZED_IN_A24R")

    closure_gates = a24r.get("closure_gates", {})
    if not closure_gates or not all(value is True for value in closure_gates.values()):
        raise RuntimeError("A25_A24R_CLOSURE_GATES_NOT_ALL_TRUE")

    natural_cycles = int(a24r.get("natural_order_cycle_count", 0))
    writer_counts = a24r.get("writer_status_counts", {})
    committed_cycles = int(writer_counts.get("COMMITTED", 0))
    replay_cycles = int(writer_counts.get("IDEMPOTENT_REPLAY_NOOP", 0))
    if natural_cycles < 1 or committed_cycles < 1 or replay_cycles < 1:
        raise RuntimeError("A25_NATURAL_CYCLE_EVIDENCE_INSUFFICIENT")

    f2 = find_finding(a6, "F2")
    if f2.get("priority") != "P1":
        raise RuntimeError("A25_F2_PRIORITY_DRIFT")
    if f2.get("title") != "DELETE_VS_WAL_IO_HYPOTHESIS":
        raise RuntimeError("A25_F2_TITLE_DRIFT")
    if f2.get("canonical_interpretation") != "HYPOTHESIS_UNPROVEN_TEMP_COPY_COMPARISON_REQUIRED":
        raise RuntimeError("A25_F2_INTERPRETATION_DRIFT")
    if f2.get("required_action") != "TEMP_COPY_DELETE_VS_WAL_DURABILITY_LOCK_WRITE_AMPLIFICATION_BENCHMARK":
        raise RuntimeError("A25_F2_REQUIRED_ACTION_DRIFT")

    matrix = find_matrix(a5, "DELETE_VS_WAL")
    if matrix.get("variants") != ["DELETE_CURRENT", "WAL_CANDIDATE"]:
        raise RuntimeError("A25_DELETE_VS_WAL_VARIANTS_DRIFT")
    decision_rule = str(matrix.get("decision_rule", ""))
    if "correctness and recovery are identical" not in decision_rule:
        raise RuntimeError("A25_DELETE_VS_WAL_DECISION_RULE_WEAK")
    if "measured benefit is material" not in decision_rule:
        raise RuntimeError("A25_MATERIAL_BENEFIT_RULE_MISSING")

    database = database_snapshot()
    if database["journal_mode"] != "delete":
        raise RuntimeError("A25_PRODUCTION_JOURNAL_MODE_NOT_DELETE")
    if database["integrity_check"] != "ok" or database["quick_check"] != "ok":
        raise RuntimeError("A25_PRODUCTION_DB_INTEGRITY_FAILED")
    if database["foreign_key_check_rows"] != 0:
        raise RuntimeError("A25_PRODUCTION_DB_FOREIGN_KEY_FAILED")
    if database["batch_rows"] < 3 or database["ledger_rows"] < 321:
        raise RuntimeError("A25_PRODUCTION_LEDGER_EVIDENCE_REGRESSED")
    if any(batch["status"] != "COMMITTED" for batch in database["batches"]):
        raise RuntimeError("A25_NONCOMMITTED_PRODUCTION_BATCH_PRESENT")

    timer = systemctl_state(TIMER)
    service = systemctl_state(SERVICE)
    if timer.get("active") != "active" or timer.get("enabled") != "enabled":
        raise RuntimeError("A25_TIMER_NOT_ACTIVE_ENABLED")
    if service.get("result") != "success" or int(service.get("exec_main_status", -1)) != 0:
        raise RuntimeError("A25_SERVICE_RESULT_NOT_SUCCESS")

    environment = service_environment()
    for key in (
        "runner_bound",
        "writer_enabled",
        "runner_lock_enabled",
        "hot_override_enabled",
        "guarded_mode_enabled",
    ):
        if environment.get(key) is not True:
            raise RuntimeError("A25_ENVIRONMENT_GATE_FAILED:" + key)
    if environment.get("unexpected_a21_mode") is True:
        raise RuntimeError("A25_UNEXPECTED_A21_MODE")

    latest_result = load(RESULT_PATH)
    guarded_state = load(GUARDED_STATE)
    if canonical(latest_result) != canonical(guarded_state):
        raise RuntimeError("A25_RESULT_GUARDED_STATE_PARITY_FAILED")
    if latest_result.get("status") != "OK_A23_GUARDED_PRODUCTION_CYCLE_COMPLETED":
        raise RuntimeError("A25_LATEST_GUARDED_RESULT_INVALID")
    if latest_result.get("writer_status") not in {"COMMITTED", "IDEMPOTENT_REPLAY_NOOP"}:
        raise RuntimeError("A25_LATEST_WRITER_STATUS_INVALID")
    if latest_result.get("unobservable_rows") != 0:
        raise RuntimeError("A25_UNOBSERVABLE_ROWS_PRESENT")
    rollback_guard = latest_result.get("rollback_guard", {})
    if rollback_guard.get("armed") is not True or rollback_guard.get("triggered") is not False:
        raise RuntimeError("A25_ROLLBACK_GUARD_INVALID")
    if ERROR_PATH.exists():
        error_value = load(ERROR_PATH)
        if error_value.get("status") == "A23_GUARDED_PRODUCTION_CYCLE_FAILED":
            raise RuntimeError("A25_ACTIVE_FAILURE_STATE_PRESENT")

    if sha(HOT) != sha(PANEL_HOT):
        raise RuntimeError("A25_HOT_PANEL_HASH_MISMATCH")
    bridge = load(BRIDGE_STATE)
    if bridge.get("decision") != "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED":
        raise RuntimeError("A25_BRIDGE_DECISION_INVALID")
    if bridge.get("failures") != []:
        raise RuntimeError("A25_BRIDGE_FAILURES_PRESENT")
    hash_match = bridge.get("hash_match")
    if not isinstance(hash_match, dict) or not hash_match or not all(
        value is True for value in hash_match.values()
    ):
        raise RuntimeError("A25_BRIDGE_HASH_PARITY_FAILED")

    disk = shutil.disk_usage(ROOT)
    minimum_free_bytes = max(256 * 1024 * 1024, database["size_bytes"] * 8)
    if disk.free < minimum_free_bytes:
        raise RuntimeError("A25_TEMP_COPY_FREE_SPACE_INSUFFICIENT")

    baseline = a5.get("baseline", {})
    low_load = baseline.get("low_load_operational_stability", {})
    precise_runner_ms = float(low_load.get("precise_natural_runner_ms", 0.0))
    if precise_runner_ms <= 0:
        raise RuntimeError("A25_BASELINE_RUNTIME_MISSING")

    measurement_fields = list(matrix.get("measure", []))
    required_measurements = {
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
    }
    if not required_measurements.issubset(set(measurement_fields)):
        raise RuntimeError("A25_OPTION_B_MEASUREMENT_CONTRACT_INCOMPLETE")

    readiness_gates = {
        "a24r_p0_f1_closed": True,
        "production_writer_active": True,
        "natural_timer_evidence_valid": True,
        "production_database_integrity_clean": True,
        "original_committed_batches_preserved": True,
        "complete_source_accounting": True,
        "zero_unobservable_rows": True,
        "panel_hash_parity": True,
        "rollback_guard_armed_not_triggered": True,
        "persistent_guarded_environment_unchanged": True,
        "option_b_hypothesis_identified": True,
        "delete_vs_wal_temp_copy_matrix_present": True,
        "measurable_benefit_rule_present": True,
        "correctness_and_recovery_equivalence_required": True,
        "temp_copy_disk_capacity_sufficient": True,
        "production_apply_remains_blocked": True,
        "human_authorization_required_for_execution": True,
    }

    timestamp = utc_now()
    artifact = {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "timestamp_utc": timestamp,
        "status": "CLOSED_OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED_PRODUCTION_APPLY_BLOCKED",
        "result": RESULT,
        "source_artifacts": {
            "p0_f1_closure": str(A24R.relative_to(ROOT)),
            "baseline_and_red_team_package": str(A5.relative_to(ROOT)),
            "gemini_findings_register": str(A6.relative_to(ROOT)),
            "guarded_writer_activation": str(A23.relative_to(ROOT)),
        },
        "option_b_definition": {
            "id": OPTION_B_ID,
            "finding": OPTION_B_FINDING,
            "priority": "P1",
            "hypothesis": "SQLite DELETE journal mode may contribute materially to runtime IO and lock cost.",
            "epistemic_status": "UNPROVEN_HYPOTHESIS",
            "authorized_scope": "IMMUTABLE_OR_DISPOSABLE_TEMP_COPY_ONLY",
            "variants": matrix["variants"],
            "measurements": measurement_fields,
            "decision_rule": decision_rule,
            "production_journal_mode_at_decision": database["journal_mode"],
            "production_synchronous_at_decision": database["synchronous"],
            "baseline_precise_runner_ms": precise_runner_ms,
        },
        "readiness_gates": readiness_gates,
        "production_snapshot": database,
        "runtime_snapshot": {
            "natural_timer_cycles_observed": natural_cycles,
            "committed_natural_cycles": committed_cycles,
            "idempotent_replay_cycles": replay_cycles,
            "timer_active": timer.get("active"),
            "timer_enabled": timer.get("enabled"),
            "service_result": service.get("result"),
            "service_exec_main_status": service.get("exec_main_status"),
            "latest_writer_status": latest_result.get("writer_status"),
            "hot_panel_hash_match": True,
            "bridge_hash_match_all": True,
            "rollback_guard_armed": True,
            "rollback_guard_triggered": False,
        },
        "economy": {
            "network_api_required": False,
            "paid_provider_required": False,
            "new_server_required": False,
            "production_downtime_required": False,
            "available_bytes": disk.free,
            "minimum_required_bytes": minimum_free_bytes,
            "measure_before_spend": True,
        },
        "authorization": {
            "option_b_readiness_confirmed": True,
            "option_b_temp_copy_benchmark_authorized": True,
            "option_b_production_apply_authorized": False,
            "option_b_authorized": False,
            "optimization_apply_authorized": False,
            "production_database_mutation_authorized": False,
            "production_service_timer_mutation_authorized": False,
            "production_writer_active": True,
            "additional_canary_authorized": False,
            "p0_f1_closed": True,
            "human_authorization_required_for_next_execution": True,
        },
        "next_safe_step": NEXT,
    }

    if not all(readiness_gates.values()):
        raise RuntimeError("A25_READINESS_GATE_FAILED")

    backup_root = Path(tempfile.mkdtemp(prefix="era55a25_repo_"))
    backups = backup_files(backup_root)

    def cleanup() -> None:
        try:
            restore_files(backups, EXPECTED_HEAD)
        except Exception:
            pass
        shutil.rmtree(backup_root, ignore_errors=True)

    atexit.register(cleanup)

    atomic_dump(ARTIFACT, artifact)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# ERA55A25 Option B Readiness and Authorization Decision

- Status: `CLOSED_OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED_PRODUCTION_APPLY_BLOCKED`
- Result: `{RESULT}`
- Option B: `{OPTION_B_ID}`
- Epistemic status: `UNPROVEN_HYPOTHESIS`
- Authorized scope: `IMMUTABLE_OR_DISPOSABLE_TEMP_COPY_ONLY`
- Production journal mode: `{database['journal_mode']}`
- Production synchronous: `{database['synchronous']}`
- Baseline precise runner: `{precise_runner_ms:.3f} ms`
- Natural timer cycles observed: `{natural_cycles}`
- Production batch rows: `{database['batch_rows']}`
- Production ledger rows: `{database['ledger_rows']}`
- Production writer active: `true`
- P0 F1 closed: `true`
- Option B temp-copy benchmark authorized: `true`
- Option B production apply authorized: `false`
- Production mutation in A25: `false`
- Paid provider required: `false`
- Next safe step: `{NEXT}`
""",
        encoding="utf-8",
    )

    current.update(
        {
            "mode": "ERA55A25_OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED_APPLY_BLOCKED",
            "runtime_status": "WORK_UNIT_CLOSED",
            "updated_at": timestamp,
            "last_action": {
                "timestamp": timestamp,
                "task": WORK_UNIT,
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
            },
            "active_work_unit": {
                "id": WORK_UNIT,
                "type": "ERA55_P1_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "status": artifact["status"],
                "result": RESULT,
                "production_mutation": False,
                "next_step": NEXT,
            },
            "next_safe_step": {
                "id": NEXT,
                "type": "ERA55_P1_OPTION_B_DELETE_VS_WAL_TEMP_COPY_BENCHMARK",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "purpose": "Benchmark DELETE current versus WAL candidate on immutable or disposable temp copies; do not mutate production.",
                "human_authorization_required": True,
                "temp_copy_only": True,
                "production_mutation": False,
                "production_writer_active": True,
                "p0_f1_closed": True,
                "option_b_temp_copy_benchmark_authorized": True,
                "option_b_production_apply_authorized": False,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
                "status": "READY",
            },
            "current_problem": {
                "code": "OPTION_B_DELETE_VS_WAL_HYPOTHESIS_UNPROVEN",
                "severity": "P1",
                "evidence": str(ARTIFACT.relative_to(ROOT)),
            },
        }
    )
    runtime["current_work_unit"] = current["active_work_unit"]
    atomic_dump(RUNTIME, runtime)

    history = load(HISTORY)
    events = history.setdefault("events", [])
    event_id = "ERA55A25_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION_V1"
    if not any(
        isinstance(event, dict) and event.get("event_id") == event_id
        for event in events
    ):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": timestamp,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "OPTION_B_READINESS_AND_AUTHORIZATION_DECISION",
                "status": artifact["status"],
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "option_b": OPTION_B_ID,
                "temp_copy_benchmark_authorized": True,
                "production_apply_authorized": False,
                "production_mutation": False,
                "production_writer_active": True,
                "p0_f1_closed": True,
                "next_safe_step": NEXT,
            }
        )
    history["updated_at"] = timestamp
    history["updated_at_utc"] = timestamp
    atomic_dump(HISTORY, history)

    master = MASTER.read_text(encoding="utf-8")
    master = replace_section(
        master,
        "## 01 PROJECT STATUS",
        """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_OPTION_B_TEMP_COPY_BENCHMARK_READY
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
CURRENT_HUMAN_SUMMARY=06_PROJECT_MASTER_STATE.md
GIT_BRANCH=main
GIT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD
BOOT_HEALTH=100/100
```""",
    )
    master = replace_section(
        master,
        "## 02 CURRENT MAJOR-LINE POSITION",
        f"""```text
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_OPTION_B_TEMP_COPY_BENCHMARK_READY
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
NATURAL_TIMER_CYCLES_OBSERVED={natural_cycles}
PRODUCTION_BATCH_ROWS={database['batch_rows']}
PRODUCTION_LEDGER_ROWS={database['ledger_rows']}
PRODUCTION_JOURNAL_MODE={database['journal_mode']}
PRODUCTION_LEDGER_WRITER_ACTIVE=true
P0_F1_CLOSED=true
OPTION_B_READINESS_CONFIRMED=true
OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED=true
OPTION_B_PRODUCTION_APPLY_AUTHORIZED=false
OPTION_B_AUTHORIZED=false
```

Option B is the P1 DELETE-vs-WAL hypothesis test. Only an immutable or disposable temp-copy benchmark is authorized; production WAL/apply remains blocked.""",
    )
    master = replace_section(
        master,
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}""",
    )
    master = replace_section(
        master,
        "## 09 OPEN RISKS AND DECISIONS",
        """- P0 F1 is closed and the guarded production writer remains active.
- Option B remains an unproven DELETE-vs-WAL performance and lock-cost hypothesis.
- A temp-copy benchmark is authorized; production WAL/apply is not authorized.
- Correctness, durability, recovery, event count, UID set and panel equivalence must not regress.
- Process-kill recovery remains partial and is outside the A26 benchmark unless separately authorized.
- Stage timing and exact panel latency remain incomplete.
- Runtime risk is minimized, never zero.
- Git HEAD must be read dynamically.""",
    )
    master = replace_section(
        master,
        "## 10 NEXT SAFE STEP",
        f"""```text
NEXT_SAFE_STEP={NEXT}
```

Run an immutable/disposable temp-copy DELETE-current versus WAL-candidate benchmark. Do not change the production database, service, timer, panel or guarded writer integration. Production apply requires a separate decision after measured equivalence and material benefit are proven.""",
    )
    MASTER.write_text(master, encoding="utf-8")

    handoff = HANDOFF.read_text(encoding="utf-8")
    handoff = replace_section(
        handoff,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        f"""PROJECT_STATUS=ACTIVE_ERA55_OPTION_B_TEMP_COPY_BENCHMARK_READY
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_OPTION_B_TEMP_COPY_BENCHMARK_READY
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
NATURAL_TIMER_CYCLES_OBSERVED={natural_cycles}
PRODUCTION_BATCH_ROWS={database['batch_rows']}
PRODUCTION_LEDGER_ROWS={database['ledger_rows']}
PRODUCTION_JOURNAL_MODE={database['journal_mode']}
PRODUCTION_LEDGER_WRITER_ACTIVE=true
ADDITIONAL_CANARY_AUTHORIZED=false
P0_F1_CLOSED=true
OPTION_B_READINESS_CONFIRMED=true
OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED=true
OPTION_B_PRODUCTION_APPLY_AUTHORIZED=false
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""",
    )
    handoff = replace_section(
        handoff,
        "## 03 LAST VERIFIED WORK",
        f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
PRODUCTION_MUTATION=false
CURRENT_PROBLEM=OPTION_B_DELETE_VS_WAL_HYPOTHESIS_UNPROVEN""",
    )
    handoff = replace_section(
        handoff,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not rerun A9-A25 unless evidence is invalidated.
- Do not execute another canary.
- Do not remove or edit the A23 persistent integration without a rollback plan.
- Do not delete or mutate any valid committed production batch.
- Do not change the production database journal mode in A26.
- Do not treat temp-copy benchmark authorization as production apply authorization.""",
    )
    handoff = replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Guarded production writer: `ACTIVE`.
- P0 F1: `CLOSED`.
- Additional canary: `BLOCKED`.
- Option B temp-copy benchmark: `AUTHORIZED`.
- Option B production apply: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff = replace_section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A26 is current and A25 decision evidence remains valid.
2. Create independent immutable/disposable copies for DELETE-current and WAL-candidate variants.
3. Measure runtime, stage timing, commit proxy, write amplification, reader/writer blocking, integrity, event count and UID hash.
4. Do not modify the production database, service, timer, panel or guarded writer integration.
5. Do not authorize production WAL/apply unless correctness and recovery are identical and benefit is material.
6. Require a separate explicit human decision after the benchmark.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac = ALMANAC.read_text(encoding="utf-8")
    marker = "## ERA55A_25 OPTION B READINESS AND AUTHORIZATION DECISION"
    if marker not in almanac:
        ALMANAC.write_text(
            almanac.rstrip()
            + f"""

---

{marker}

- Status: `CLOSED_OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED_PRODUCTION_APPLY_BLOCKED`
- Result: `{RESULT}`
- Option B: `{OPTION_B_ID}`
- Readiness confirmed: `true`
- Temp-copy benchmark authorized: `true`
- Production apply authorized: `false`
- Production mutation: `false`
- Production writer active: `true`
- P0 F1 closed: `true`
- Next safe step: `{NEXT}`
"""
            + "\n",
            encoding="utf-8",
        )

    git(
        "add",
        str(ARTIFACT.relative_to(ROOT)),
        str(RUNTIME.relative_to(ROOT)),
        str(HISTORY.relative_to(ROOT)),
        str(MASTER.relative_to(ROOT)),
        str(HANDOFF.relative_to(ROOT)),
        str(ALMANAC.relative_to(ROOT)),
    )
    run(["git", "add", "-f", str(REPORT.relative_to(ROOT))], timeout=30)

    staged = git("diff", "--cached", "--name-only")
    if not staged:
        raise RuntimeError("A25_NO_STAGED_CHANGES")

    if systemctl_state(TIMER).get("active") != "active":
        raise RuntimeError("A25_TIMER_CHANGED_DURING_DECISION")
    if systemctl_state(TIMER).get("enabled") != "enabled":
        raise RuntimeError("A25_TIMER_DISABLED_DURING_DECISION")
    if database_snapshot()["sha256"] != database["sha256"]:
        raise RuntimeError("A25_PRODUCTION_DB_CHANGED_DURING_DECISION")

    git("commit", "-m", SUBJECT)

    backups = {}
    atexit.unregister(cleanup)
    shutil.rmtree(backup_root, ignore_errors=True)

    print("ERA55A25_OPTION_B_DECISION=SUCCESS")
    print("RESULT=" + RESULT)
    print("OPTION_B=" + OPTION_B_ID)
    print("OPTION_B_EPISTEMIC_STATUS=UNPROVEN_HYPOTHESIS")
    print("OPTION_B_TEMP_COPY_BENCHMARK_AUTHORIZED=true")
    print("OPTION_B_PRODUCTION_APPLY_AUTHORIZED=false")
    print("OPTION_B_AUTHORIZED=false")
    print("OPTIMIZATION_APPLY_AUTHORIZED=false")
    print("PRODUCTION_MUTATION=false")
    print("PRODUCTION_JOURNAL_MODE=" + database["journal_mode"])
    print("PRODUCTION_BATCH_ROWS=" + str(database["batch_rows"]))
    print("PRODUCTION_LEDGER_ROWS=" + str(database["ledger_rows"]))
    print("NATURAL_TIMER_CYCLES_OBSERVED=" + str(natural_cycles))
    print("PRODUCTION_WRITER_ACTIVE=true")
    print("P0_F1_CLOSED=true")
    print("NEXT_SAFE_STEP=" + NEXT)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
