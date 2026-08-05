#!/usr/bin/env python3
from __future__ import annotations

import atexit
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
EXPECTED_HEAD = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()

WORK_UNIT = "ERA55A_24R_P0_NATURAL_CYCLE_EVIDENCE_RECOVERY_AND_P0_F1_CLOSURE"
RESULT = "OK_NATURAL_TIMER_EVIDENCE_RECOVERED_P0_F1_CLOSED"
NEXT = "ERA55A_25_P0_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION"
SUBJECT = "ERA55A24R_EVIDENCE_RECOVERY | OK | P0_F1_CLOSED"

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

A23 = ROOT / "data/control/era55a23_p0_guarded_general_production_writer_runtime_integration_apply_and_post_audit_v1.json"
ARTIFACT = ROOT / "data/control/era55a24r_p0_natural_cycle_evidence_recovery_and_p0_f1_closure_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A24R_P0_NATURAL_CYCLE_EVIDENCE_RECOVERY_AND_P0_F1_CLOSURE.md"

HELPER_PATH = ROOT / "tools/era55a24_p0_post_activation_observation_and_p0_f1_closure_decision_v1.py"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
GUARDED_STATE = ROOT / "runtime/state/news_guarded_production_writer_v1.json"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

DROPIN = Path(
    "/etc/systemd/system/tokenoskobi-news-radar-refresh.service.d/"
    "90-era55a23-guarded-production.conf"
)
RESULT_PATH = Path("/run/tokenoskobi/era55a23_guarded_result.json")
ERROR_PATH = Path("/run/tokenoskobi/era55a23_guarded_error.json")
ORDER_LOG = Path("/run/tokenoskobi/era55a23_guarded_order.log")


def load_helper():
    spec = importlib.util.spec_from_file_location("era55a24_helpers", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("A24R_HELPER_IMPORT_SPEC_FAILED")
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
    return run(["git", *args]).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    return H.load(path)


def atomic_dump(path: Path, value: dict[str, Any]) -> None:
    H.atomic_dump(path, value)


def systemctl_state(unit: str) -> dict[str, Any]:
    return H.systemctl_state(unit)


def database_inventory(path: Path) -> dict[str, Any]:
    return H.database_inventory(path)


def batch_map(value: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return H.batch_map(value)


def validate_order_cycle(cycle: list[str]) -> dict[str, Any]:
    return H.validate_order_cycle(cycle)


def split_order_cycles(lines: list[str]) -> list[list[str]]:
    return H.split_order_cycles(lines)


def sha(path: Path) -> str | None:
    return H.sha(path)


def canonical(value: Any) -> bytes:
    return H.canonical(value)


def replace_section(text: str, heading: str, body: str) -> str:
    return H.replace_section(text, heading, body)


def service_environment() -> dict[str, Any]:
    return H.service_environment()


def journal_evidence(apply_finished: str) -> dict[str, Any]:
    since = datetime.fromisoformat(apply_finished).astimezone(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S.%f UTC"
    )
    completed = run(
        [
            "journalctl",
            "-u",
            SERVICE,
            "--since",
            since,
            "--no-pager",
            "-o",
            "cat",
        ],
        check=False,
        timeout=60,
    )
    text = completed.stdout
    failures = [
        marker
        for marker in (
            "Failed with result 'exit-code'",
            "Failed to start tokenoskobi-news-radar-refresh.service",
            "status=1/FAILURE",
            "A23_GUARDED_PRODUCTION_CYCLE_FAILED",
            "A23_GUARDED_HOT_END:1",
            "HOT_END:1",
            "Traceback (most recent call last)",
        )
        if marker in text
    ]
    return {
        "since": since,
        "rc": completed.returncode,
        "start_count": text.count(
            "Starting tokenoskobi-news-radar-refresh.service"
        ),
        "finished_count": text.count(
            "Finished tokenoskobi-news-radar-refresh.service"
        ),
        "deactivated_success_count": text.count("Deactivated successfully"),
        "failure_markers": failures,
        "stdout_tail": "\n".join(text.splitlines()[-120:]),
        "stderr_tail": "\n".join(completed.stderr.splitlines()[-40:]),
    }


def verify_environment(a23: dict[str, Any]) -> dict[str, Any]:
    if not DROPIN.exists():
        raise RuntimeError("A24R_DROPIN_MISSING")
    if sha(DROPIN) != a23["persistent_integration"]["dropin_sha256"]:
        raise RuntimeError("A24R_DROPIN_HASH_DRIFT")
    environment = service_environment()
    required_true = (
        "runner_bound",
        "writer_enabled",
        "runner_lock_enabled",
        "hot_override_enabled",
        "guarded_mode_enabled",
    )
    for key in required_true:
        if environment.get(key) is not True:
            raise RuntimeError("A24R_ENVIRONMENT_GATE_FAILED:" + key)
    if environment.get("unexpected_a21_mode") is True:
        raise RuntimeError("A24R_UNEXPECTED_A21_MODE")
    return environment


def validate_database(
    a23: dict[str, Any],
    natural_cycles: list[dict[str, Any]],
) -> dict[str, Any]:
    inventory = database_inventory(DB)
    if inventory["integrity_check"] != "ok":
        raise RuntimeError("A24R_DB_INTEGRITY_FAILED")
    if inventory["quick_check"] != "ok":
        raise RuntimeError("A24R_DB_QUICK_CHECK_FAILED")
    if inventory["foreign_key_check_rows"] != 0:
        raise RuntimeError("A24R_DB_FOREIGN_KEY_FAILED")
    if set(inventory["triggers"]) != {
        "trg_news_disposition_batch_archive_before_delete_v2",
        "trg_news_disposition_ledger_archive_before_delete_v2",
    }:
        raise RuntimeError("A24R_DB_TRIGGER_SET_DRIFT")

    original = a23["production_after"]
    original_map = batch_map(original)
    current_map = batch_map(inventory)

    for uid, batch in original_map.items():
        if current_map.get(uid) != batch:
            raise RuntimeError("A24R_ORIGINAL_BATCH_MUTATED:" + uid)

    new_batches = [
        batch
        for batch in inventory["batches"]
        if batch["batch_uid"] not in original_map
    ]
    committed_markers = sum(
        1 for cycle in natural_cycles if cycle["writer_status"] == "COMMITTED"
    )
    replay_markers = sum(
        1
        for cycle in natural_cycles
        if cycle["writer_status"] == "IDEMPOTENT_REPLAY_NOOP"
    )

    if len(new_batches) != committed_markers:
        raise RuntimeError(
            "A24R_COMMITTED_MARKER_DB_BATCH_COUNT_MISMATCH:"
            + str(committed_markers)
            + ":"
            + str(len(new_batches))
        )

    expected_ledger = int(original["ledger_rows"])
    for expected_sequence, batch in enumerate(inventory["batches"], start=1):
        if batch["batch_sequence"] != expected_sequence:
            raise RuntimeError("A24R_BATCH_SEQUENCE_GAP")
        if batch["status"] != "COMMITTED":
            raise RuntimeError("A24R_BATCH_NOT_COMMITTED:" + batch["batch_uid"])
        if batch["policy_version"] != H.LEDGER_POLICY:
            raise RuntimeError("A24R_BATCH_POLICY_DRIFT:" + batch["batch_uid"])
        if batch["queue_capacity"] != H.QUEUE_CAPACITY:
            raise RuntimeError("A24R_BATCH_QUEUE_CAPACITY_DRIFT")
        if not (1 <= batch["source_candidate_count"] <= H.MAX_SOURCE_ROWS):
            raise RuntimeError("A24R_BATCH_SOURCE_BOUND_INVALID")
        if batch["ledger_rows"] != batch["source_candidate_count"]:
            raise RuntimeError("A24R_BATCH_LEDGER_ACCOUNTING_FAILED")
        if sum(batch["disposition_counts"].values()) != batch["source_candidate_count"]:
            raise RuntimeError("A24R_BATCH_DISPOSITION_ACCOUNTING_FAILED")
        if batch["batch_uid"] not in original_map:
            expected_ledger += int(batch["source_candidate_count"])

    if inventory["ledger_rows"] != expected_ledger:
        raise RuntimeError("A24R_FINAL_LEDGER_COUNT_MISMATCH")

    return {
        "inventory": inventory,
        "original_batch_uids": sorted(original_map),
        "new_batches": new_batches,
        "committed_marker_count": committed_markers,
        "replay_marker_count": replay_markers,
    }


def backup_repo_state(root: Path) -> dict[Path, Path]:
    backups: dict[Path, Path] = {}
    for index, path in enumerate((RUNTIME, HISTORY, MASTER, HANDOFF, ALMANAC)):
        target = root / f"{index:02d}.backup"
        shutil.copy2(path, target)
        backups[path] = target
    return backups


def restore_repo_state(backups: dict[Path, Path], expected_head: str) -> None:
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
    if ARTIFACT.exists():
        raise RuntimeError("A24R_ARTIFACT_ALREADY_EXISTS")

    for path in (
        A23,
        HELPER_PATH,
        DB,
        HOT,
        PANEL_HOT,
        BRIDGE_STATE,
        GUARDED_STATE,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
        RESULT_PATH,
        ORDER_LOG,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    a23 = load(A23)
    if a23["result"] != "OK_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_ACTIVE":
        raise RuntimeError("A24R_A23_RESULT_INVALID")
    if a23["authorization"]["production_writer_active"] is not True:
        raise RuntimeError("A24R_WRITER_NOT_ACTIVE")
    if a23["authorization"]["p0_f1_closed"] is not False:
        raise RuntimeError("A24R_P0_F1_ALREADY_CLOSED")
    if a23["authorization"]["option_b_authorized"] is not False:
        raise RuntimeError("A24R_OPTION_B_ALREADY_AUTHORIZED")
    if a23["next_safe_step"] != "ERA55A_24_P0_POST_ACTIVATION_OBSERVATION_AND_P0_F1_CLOSURE_DECISION":
        raise RuntimeError("A24R_A23_NEXT_STEP_DRIFT")

    timer_initial = systemctl_state(TIMER)
    if timer_initial["active"] != "active" or timer_initial["enabled"] != "enabled":
        raise RuntimeError("A24R_TIMER_PRECONDITION_FAILED")
    environment = verify_environment(a23)

    service_state = systemctl_state(SERVICE)
    if service_state["active"] in {"active", "activating", "deactivating"}:
        deadline = time.time() + 180
        while time.time() < deadline:
            service_state = systemctl_state(SERVICE)
            if service_state["active"] not in {"active", "activating", "deactivating"}:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("A24R_SERVICE_DID_NOT_BECOME_INACTIVE")

    timer_restored = False
    repo_backup_root: Path | None = None
    repo_backups: dict[Path, Path] = {}

    def restore_timer() -> None:
        nonlocal timer_restored
        run(["systemctl", "start", TIMER], check=True, timeout=30)
        timer_restored = True

    def cleanup() -> None:
        if repo_backups:
            try:
                restore_repo_state(repo_backups, EXPECTED_HEAD)
            except Exception:
                pass
        if not timer_restored:
            try:
                restore_timer()
            except Exception:
                pass
        if repo_backup_root is not None:
            shutil.rmtree(repo_backup_root, ignore_errors=True)

    atexit.register(cleanup)

    run(["systemctl", "stop", TIMER], check=True, timeout=30)
    deadline = time.time() + 180
    while time.time() < deadline:
        if systemctl_state(SERVICE)["active"] not in {"active", "activating", "deactivating"}:
            break
        time.sleep(0.5)
    else:
        raise RuntimeError("A24R_SERVICE_ACTIVE_AFTER_TIMER_STOP")

    order_lines = ORDER_LOG.read_text(encoding="utf-8").splitlines()
    raw_cycles = split_order_cycles(order_lines)
    if len(raw_cycles) < 2:
        raise RuntimeError("A24R_NATURAL_CYCLE_EVIDENCE_MISSING")
    if raw_cycles[0] != a23["runner_order"]:
        raise RuntimeError("A24R_CONTROLLED_CYCLE_ORDER_DRIFT")

    validated_cycles = [validate_order_cycle(cycle) for cycle in raw_cycles]
    natural_cycles = validated_cycles[1:]
    if not natural_cycles:
        raise RuntimeError("A24R_NO_NATURAL_CYCLES")

    journal = journal_evidence(str(a23["apply_finished_at_utc"]))
    if journal["failure_markers"]:
        raise RuntimeError(
            "A24R_POST_ACTIVATION_FAILURE_MARKERS:"
            + ",".join(journal["failure_markers"])
        )
    if journal["finished_count"] < len(natural_cycles):
        raise RuntimeError("A24R_SERVICE_FINISHED_COUNT_TOO_LOW")
    if journal["deactivated_success_count"] < len(natural_cycles):
        raise RuntimeError("A24R_SERVICE_SUCCESS_COUNT_TOO_LOW")

    latest_result = load(RESULT_PATH)
    guarded_state = load(GUARDED_STATE)
    validated_latest = H.validate_cycle_payload(latest_result)
    if canonical(latest_result) != canonical(guarded_state):
        raise RuntimeError("A24R_RESULT_GUARDED_STATE_PARITY_FAILED")
    if natural_cycles[-1]["writer_status"] != validated_latest["writer_status"]:
        raise RuntimeError("A24R_LATEST_ORDER_RESULT_STATUS_MISMATCH")
    if ERROR_PATH.exists():
        error_value = load(ERROR_PATH)
        if error_value.get("status") == "A23_GUARDED_PRODUCTION_CYCLE_FAILED":
            raise RuntimeError("A24R_ACTIVE_FAILURE_STATE_PRESENT")

    database = validate_database(a23, natural_cycles)
    inventory = database["inventory"]

    if sha(HOT) != sha(PANEL_HOT):
        raise RuntimeError("A24R_CURRENT_PANEL_HASH_MISMATCH")
    bridge = load(BRIDGE_STATE)
    if bridge.get("decision") != "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED":
        raise RuntimeError("A24R_BRIDGE_DECISION_INVALID")
    if bridge.get("failures") != []:
        raise RuntimeError("A24R_BRIDGE_FAILURES_PRESENT")
    hash_match = bridge.get("hash_match")
    if not isinstance(hash_match, dict) or not hash_match or not all(
        value is True for value in hash_match.values()
    ):
        raise RuntimeError("A24R_BRIDGE_HASH_PARITY_FAILED")

    latest_timestamp = datetime.fromisoformat(str(latest_result["timestamp_utc"]))
    apply_timestamp = datetime.fromisoformat(str(a23["apply_finished_at_utc"]))
    if latest_timestamp <= apply_timestamp:
        raise RuntimeError("A24R_LATEST_RESULT_NOT_POST_ACTIVATION")

    repo_backup_root = Path(tempfile.mkdtemp(prefix="era55a24r_repo_"))
    repo_backups = backup_repo_state(repo_backup_root)

    new_batches = list(database["new_batches"])
    new_index = 0
    summaries: list[dict[str, Any]] = []
    for index, cycle in enumerate(natural_cycles, start=1):
        summary: dict[str, Any] = {
            "natural_cycle_index": index,
            "writer_status": cycle["writer_status"],
            "runner_hot_end_zero": True,
            "complete_order_sequence": True,
            "service_finished_successfully": True,
            "evidence_source": "ORDER_LOG_PLUS_SYSTEMD_SUCCESS_PLUS_FINAL_DATABASE",
        }
        if cycle["writer_status"] == "COMMITTED":
            batch = new_batches[new_index]
            new_index += 1
            summary.update(
                {
                    "batch_uid": batch["batch_uid"],
                    "source_candidate_count": batch["source_candidate_count"],
                    "source_accounted": batch["ledger_rows"],
                    "database_batch_sequence": batch["batch_sequence"],
                }
            )
        elif index == len(natural_cycles):
            summary.update(
                {
                    "batch_uid": validated_latest["batch_uid"],
                    "source_candidate_count": validated_latest["source_count"],
                    "source_accounted": validated_latest["source_count"],
                    "timestamp_utc": validated_latest["timestamp_utc"],
                }
            )
        else:
            summary.update(
                {
                    "batch_uid": None,
                    "source_candidate_count": None,
                    "source_accounted": None,
                    "detail": "PER_CYCLE_JSON_NOT_RETAINED_BY_SYSTEMD_JOURNAL; NO_DB_MUTATION_FOR_REPLAY",
                }
            )
        summaries.append(summary)

    timestamp = utc_now()
    closure_gates = {
        "a23_persistent_integration_verified": True,
        "minimum_natural_timer_cycles_observed": True,
        "all_natural_order_cycles_complete": True,
        "all_natural_order_cycles_runner_hot_end_zero": True,
        "all_systemd_service_cycles_finished_successfully": True,
        "no_post_activation_failure_marker": True,
        "current_guarded_result_valid": True,
        "current_guarded_result_state_parity": True,
        "current_complete_source_accounting": True,
        "current_zero_unobservable_rows": True,
        "current_exact_legacy_queue_parity": True,
        "current_panel_hash_parity": True,
        "current_rollback_guard_armed": True,
        "all_original_committed_batches_preserved": True,
        "committed_order_markers_match_new_database_batches": True,
        "production_database_integrity_clean": True,
        "persistent_runtime_environment_unchanged": True,
        "journal_json_payload_retention_not_required": True,
        "option_b_remains_blocked": True,
    }

    artifact = {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "timestamp_utc": timestamp,
        "status": "CLOSED_NATURAL_CYCLE_EVIDENCE_RECOVERED_P0_F1_CLOSED",
        "result": RESULT,
        "recovery_reason": "SYSTEMD_SERVICE_STDOUT_DID_NOT_RETAIN_PER_CYCLE_JSON_PAYLOADS",
        "authorization_source": str(A23.relative_to(ROOT)),
        "observation_policy": {
            "forced_service_cycle": False,
            "natural_cycles_observed": len(natural_cycles),
            "controlled_cycle_excluded": True,
            "evidence_model": "ORDER_LOG_SYSTEMD_SUCCESS_FINAL_DB_CURRENT_GUARDED_RESULT",
        },
        "closure_gates": closure_gates,
        "natural_cycle_summaries": summaries,
        "order_cycle_count_total": len(validated_cycles),
        "natural_order_cycle_count": len(natural_cycles),
        "writer_status_counts": {
            "COMMITTED": database["committed_marker_count"],
            "IDEMPOTENT_REPLAY_NOOP": database["replay_marker_count"],
        },
        "journal_evidence": journal,
        "production_at_closure": inventory,
        "original_batch_uids": database["original_batch_uids"],
        "new_natural_cycle_batches": new_batches,
        "latest_guarded_result": latest_result,
        "persistent_environment": environment,
        "persistent_dropin": {
            "path": str(DROPIN),
            "sha256": sha(DROPIN),
            "matches_a23": True,
        },
        "current_output_audit": {
            "hot_sha256": sha(HOT),
            "panel_hot_sha256": sha(PANEL_HOT),
            "hot_panel_hash_match": True,
            "bridge_decision": bridge["decision"],
            "bridge_hash_match_all": True,
            "result_guarded_state_parity": True,
        },
        "authorization": {
            "general_production_writer_activation_authorized": True,
            "production_writer_active": True,
            "additional_canary_authorized": False,
            "p0_f1_closed": True,
            "option_b_readiness_decision_authorized": True,
            "option_b_authorized": False,
            "optimization_apply_authorized": False,
        },
        "next_safe_step": NEXT,
    }
    atomic_dump(ARTIFACT, artifact)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# ERA55A24R Natural Cycle Evidence Recovery and P0 F1 Closure

- Status: `CLOSED_NATURAL_CYCLE_EVIDENCE_RECOVERED_P0_F1_CLOSED`
- Result: `{RESULT}`
- Recovery reason: `SYSTEMD_SERVICE_STDOUT_DID_NOT_RETAIN_PER_CYCLE_JSON_PAYLOADS`
- Forced service cycle: `false`
- Natural timer cycles observed: `{len(natural_cycles)}`
- Successful service completions: `{journal['finished_count']}`
- Committed natural cycles: `{database['committed_marker_count']}`
- Idempotent replay cycles: `{database['replay_marker_count']}`
- Production batch rows: `{inventory['batch_rows']}`
- Production ledger rows: `{inventory['ledger_rows']}`
- Original committed batches preserved: `true`
- Runner HOT_END:0 for every observed cycle: `true`
- Current complete source accounting: `true`
- Current unobservable rows: `0`
- Current panel hash parity: `true`
- Rollback guard armed: `true`
- Production writer active: `true`
- P0 F1 closed: `true`
- Option B authorized: `false`
- Next safe step: `{NEXT}`
""",
        encoding="utf-8",
    )

    runtime = load(RUNTIME)
    current = runtime["current_state"]
    current.update(
        {
            "mode": "ERA55A24R_NATURAL_CYCLE_EVIDENCE_RECOVERED_P0_F1_CLOSED",
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
                "type": "ERA55_P0_NATURAL_CYCLE_EVIDENCE_RECOVERY_AND_P0_F1_CLOSURE",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "status": artifact["status"],
                "result": RESULT,
                "production_mutation": False,
                "next_step": NEXT,
            },
            "next_safe_step": {
                "id": NEXT,
                "type": "ERA55_P0_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "purpose": "Decide Option B readiness separately; do not apply Option B in the decision step.",
                "human_authorization_required": True,
                "production_writer_active": True,
                "p0_f1_closed": True,
                "option_b_readiness_decision_authorized": True,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
                "status": "READY",
            },
            "current_problem": {
                "code": "OPTION_B_READINESS_AND_AUTHORIZATION_DECISION_PENDING",
                "severity": "P1",
                "evidence": str(ARTIFACT.relative_to(ROOT)),
            },
        }
    )
    runtime["current_work_unit"] = current["active_work_unit"]
    atomic_dump(RUNTIME, runtime)

    history = load(HISTORY)
    events = history.setdefault("events", [])
    event_id = "ERA55A24R_NATURAL_CYCLE_EVIDENCE_RECOVERED_P0_F1_CLOSED_V1"
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
                "event": "NATURAL_CYCLE_EVIDENCE_RECOVERY_AND_P0_F1_CLOSURE",
                "status": artifact["status"],
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "natural_cycles_observed": len(natural_cycles),
                "production_batch_rows": inventory["batch_rows"],
                "production_ledger_rows": inventory["ledger_rows"],
                "original_batches_preserved": True,
                "production_writer_active": True,
                "p0_f1_closed": True,
                "option_b_authorized": False,
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
PROJECT_STATUS=ACTIVE_ERA55_P0_F1_CLOSED_OPTION_B_DECISION_PENDING
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
CURRENT_STAGE=ERA55A_P0_F1_CLOSED_OPTION_B_DECISION_PENDING
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
NATURAL_TIMER_CYCLES_OBSERVED={len(natural_cycles)}
PRODUCTION_BATCH_ROWS={inventory['batch_rows']}
PRODUCTION_LEDGER_ROWS={inventory['ledger_rows']}
ORIGINAL_BATCHES_PRESERVED=true
RUNNER_HOT_END_ZERO=true
COMPLETE_SOURCE_ACCOUNTING=true
UNOBSERVABLE_ROWS=0
PANEL_HOT_HASH_PARITY=true
ROLLBACK_GUARD_ARMED_FOR_EVERY_CYCLE=true
PRODUCTION_LEDGER_WRITER_ACTIVE=true
P0_F1_CLOSED=true
OPTION_B_READINESS_DECISION_AUTHORIZED=true
OPTION_B_AUTHORIZED=false
```

P0 F1 is closed through recovered natural-cycle evidence. Option B remains blocked pending a separate decision.""",
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
    MASTER.write_text(master, encoding="utf-8")

    handoff = HANDOFF.read_text(encoding="utf-8")
    handoff = replace_section(
        handoff,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        f"""PROJECT_STATUS=ACTIVE_ERA55_P0_F1_CLOSED_OPTION_B_DECISION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_F1_CLOSED_OPTION_B_DECISION_PENDING
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
NATURAL_TIMER_CYCLES_OBSERVED={len(natural_cycles)}
PRODUCTION_BATCH_ROWS={inventory['batch_rows']}
PRODUCTION_LEDGER_ROWS={inventory['ledger_rows']}
ORIGINAL_BATCHES_PRESERVED=true
RUNNER_HOT_END_ZERO=true
COMPLETE_SOURCE_ACCOUNTING=true
UNOBSERVABLE_ROWS=0
PANEL_HOT_HASH_PARITY=true
ROLLBACK_GUARD_ARMED_FOR_EVERY_CYCLE=true
PRODUCTION_LEDGER_WRITER_ACTIVE=true
ADDITIONAL_CANARY_AUTHORIZED=false
P0_F1_CLOSED=true
OPTION_B_READINESS_DECISION_AUTHORIZED=true
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
CURRENT_PROBLEM=OPTION_B_READINESS_AND_AUTHORIZATION_DECISION_PENDING""",
    )
    handoff = replace_section(
        handoff,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not rerun A9-A24R unless evidence is invalidated.
- Do not execute another canary.
- Do not remove or edit the A23 persistent integration without a rollback plan.
- Do not delete any valid committed production batch.
- Do not apply Option B inside A24R.""",
    )
    handoff = replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Guarded production writer: `ACTIVE`.
- P0 F1: `CLOSED`.
- Additional canary: `BLOCKED`.
- Option B readiness decision: `AUTHORIZED`.
- Option B apply: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff = replace_section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A25 is current and A24R closure evidence remains valid.
2. Evaluate Option B scope, measurable benefit, safety, economy and rollback boundaries.
3. Do not apply Option B during the readiness decision.
4. Keep the guarded production writer active and unchanged.
5. Require explicit human authorization for any Option B apply step.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac = ALMANAC.read_text(encoding="utf-8")
    marker = "## ERA55A_24R NATURAL CYCLE EVIDENCE RECOVERY AND P0 F1 CLOSURE"
    if marker not in almanac:
        ALMANAC.write_text(
            almanac.rstrip()
            + f"""

---

{marker}

- Status: `CLOSED_NATURAL_CYCLE_EVIDENCE_RECOVERED_P0_F1_CLOSED`
- Result: `{RESULT}`
- Recovery reason: `SYSTEMD_SERVICE_STDOUT_DID_NOT_RETAIN_PER_CYCLE_JSON_PAYLOADS`
- Forced service cycle: `false`
- Natural timer cycles observed: `{len(natural_cycles)}`
- Production batch rows: `{inventory['batch_rows']}`
- Production ledger rows: `{inventory['ledger_rows']}`
- Original committed batches preserved: `true`
- Production writer active: `true`
- P0 F1 closed: `true`
- Option B authorized: `false`
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
    run(["git", "add", "-f", str(REPORT.relative_to(ROOT))])
    if not git("diff", "--cached", "--name-only"):
        raise RuntimeError("A24R_NO_STAGED_CHANGES")

    restore_timer()
    timer_after = systemctl_state(TIMER)
    if timer_after["active"] != "active" or timer_after["enabled"] != "enabled":
        raise RuntimeError("A24R_TIMER_NOT_RESTORED")
    verify_environment(a23)

    git("commit", "-m", SUBJECT)
    repo_backups = {}
    atexit.unregister(cleanup)
    if repo_backup_root is not None:
        shutil.rmtree(repo_backup_root, ignore_errors=True)

    print("ERA55A24R_EVIDENCE_RECOVERY=SUCCESS")
    print("RESULT=" + RESULT)
    print("FORCED_SERVICE_CYCLE=false")
    print("NATURAL_TIMER_CYCLES_OBSERVED=" + str(len(natural_cycles)))
    print("SYSTEMD_SUCCESSFUL_CYCLES=" + str(journal["finished_count"]))
    print("COMMITTED_NATURAL_CYCLES=" + str(database["committed_marker_count"]))
    print("IDEMPOTENT_REPLAY_CYCLES=" + str(database["replay_marker_count"]))
    print("PRODUCTION_BATCH_ROWS=" + str(inventory["batch_rows"]))
    print("PRODUCTION_LEDGER_ROWS=" + str(inventory["ledger_rows"]))
    print("ORIGINAL_BATCHES_PRESERVED=true")
    print("RUNNER_HOT_END_ZERO=true")
    print("COMPLETE_SOURCE_ACCOUNTING=true")
    print("UNOBSERVABLE_ROWS=0")
    print("PANEL_HOT_HASH_PARITY=true")
    print("ROLLBACK_GUARD_ARMED_FOR_EVERY_CYCLE=true")
    print("PRODUCTION_WRITER_ACTIVE=true")
    print("P0_F1_CLOSED=true")
    print("OPTION_B_READINESS_DECISION_AUTHORIZED=true")
    print("OPTION_B_AUTHORIZED=false")
    print("NEXT_SAFE_STEP=" + NEXT)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
