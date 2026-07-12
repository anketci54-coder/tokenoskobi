#!/usr/bin/env python3
from __future__ import annotations

import atexit
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
sys.dont_write_bytecode = True
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
EXPECTED_HEAD = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()

WORK_UNIT = "ERA55A_24_P0_POST_ACTIVATION_OBSERVATION_AND_P0_F1_CLOSURE_DECISION"
RESULT = "OK_POST_ACTIVATION_NATURAL_TIMER_OBSERVATION_P0_F1_CLOSED"
NEXT = "ERA55A_25_P0_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION"
SUBJECT = "ERA55A24_POST_ACTIVATION_OBSERVATION | OK | P0_F1_CLOSED"
LEDGER_POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"
ROLLBACK_POLICY = "POSTCOMMIT_ARCHIVE_TRIGGER_ROLLBACK_GUARD_V1"
MINIMUM_NATURAL_CYCLES = 1
MAX_SOURCE_ROWS = 5000
QUEUE_CAPACITY = 50
OBSERVATION_TIMEOUT_SECONDS = 2100

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

A23 = ROOT / "data/control/era55a23_p0_guarded_general_production_writer_runtime_integration_apply_and_post_audit_v1.json"
ARTIFACT = ROOT / "data/control/era55a24_p0_post_activation_observation_and_p0_f1_closure_decision_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A24_P0_POST_ACTIVATION_OBSERVATION_AND_P0_F1_CLOSURE_DECISION.md"

A23_TOOL = ROOT / "tools/era55a23_p0_guarded_general_production_writer_runtime_integration_apply_and_post_audit_v1.py"
ROLLBACK_GUARD = ROOT / "tools/news_disposition_postcommit_rollback_guard_v1.py"
RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"

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
    "/etc/systemd/system/"
    "tokenoskobi-news-radar-refresh.service.d/"
    "90-era55a23-guarded-production.conf"
)
RESULT_PATH = Path("/run/tokenoskobi/era55a23_guarded_result.json")
ERROR_PATH = Path("/run/tokenoskobi/era55a23_guarded_error.json")
ORDER_LOG = Path("/run/tokenoskobi/era55a23_guarded_order.log")


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
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def atomic_dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix="." + path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        directory_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temp.exists():
            temp.unlink()


def sha(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def database_inventory(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only=ON")
        batches: list[dict[str, Any]] = []
        rows = connection.execute(
            """
            SELECT rowid AS batch_sequence, *
            FROM news_disposition_batches_v2
            ORDER BY rowid
            """
        ).fetchall()
        for row in rows:
            batch = dict(row)
            uid = str(batch["batch_uid"])
            ledger_rows = [
                dict(item)
                for item in connection.execute(
                    """
                    SELECT *
                    FROM news_disposition_ledger_v2
                    WHERE batch_uid=?
                    ORDER BY source_index, disposition_uid
                    """,
                    (uid,),
                ).fetchall()
            ]
            disposition_counts = {
                str(name): int(count)
                for name, count in connection.execute(
                    """
                    SELECT disposition, COUNT(*)
                    FROM news_disposition_ledger_v2
                    WHERE batch_uid=?
                    GROUP BY disposition
                    ORDER BY disposition
                    """,
                    (uid,),
                ).fetchall()
            }
            batches.append(
                {
                    "batch_sequence": int(batch["batch_sequence"]),
                    "batch_uid": uid,
                    "status": str(batch["status"]),
                    "policy_version": str(batch["policy_version"]),
                    "queue_capacity": int(batch["queue_capacity"]),
                    "source_candidate_count": int(batch["source_candidate_count"]),
                    "admitted_count": int(batch["admitted_count"]),
                    "overflow_count": int(batch["overflow_count"]),
                    "duplicate_removed_count": int(batch["duplicate_removed_count"]),
                    "unsafe_filtered_count": int(batch["unsafe_filtered_count"]),
                    "invalid_candidate_count": int(batch["invalid_candidate_count"]),
                    "replaced_count": int(batch["replaced_count"]),
                    "ledger_rows": len(ledger_rows),
                    "disposition_counts": disposition_counts,
                    "batch_row_hash": canonical_hash(batch),
                    "ledger_rows_hash": canonical_hash(ledger_rows),
                }
            )
        return {
            "batch_rows": len(batches),
            "ledger_rows": int(
                connection.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2"
                ).fetchone()[0]
            ),
            "batches": batches,
            "integrity_check": str(
                connection.execute("PRAGMA integrity_check").fetchone()[0]
            ),
            "quick_check": str(
                connection.execute("PRAGMA quick_check").fetchone()[0]
            ),
            "foreign_key_check_rows": len(
                connection.execute("PRAGMA foreign_key_check").fetchall()
            ),
            "triggers": [
                str(name)
                for (name,) in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='trigger'
                      AND tbl_name IN (
                        'news_disposition_batches_v2',
                        'news_disposition_ledger_v2'
                      )
                    ORDER BY name
                    """
                ).fetchall()
            ],
        }
    finally:
        connection.close()


def batch_map(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(batch["batch_uid"]): batch
        for batch in inventory["batches"]
    }


def systemctl_state(unit: str) -> dict[str, Any]:
    active = run(["systemctl", "is-active", unit], check=False)
    enabled = run(["systemctl", "is-enabled", unit], check=False)
    return {
        "active": active.stdout.strip() or active.stderr.strip(),
        "active_rc": active.returncode,
        "enabled": enabled.stdout.strip() or enabled.stderr.strip(),
        "enabled_rc": enabled.returncode,
    }


def service_environment() -> dict[str, Any]:
    completed = run(
        [
            "systemctl",
            "show",
            SERVICE,
            "-p",
            "Environment",
            "-p",
            "ExecStart",
            "-p",
            "FragmentPath",
            "-p",
            "Result",
            "-p",
            "ExecMainStatus",
        ],
        check=False,
    )
    text = completed.stdout
    return {
        "runner_bound": str(RUNNER) in text,
        "writer_enabled": "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text,
        "runner_lock_enabled": "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text,
        "hot_override_enabled": (
            f"TOKENOSKOBI_NEWS_HOT_PATH={A23_TOOL}" in text
        ),
        "guarded_mode_enabled": "TOKENOSKOBI_A23_GUARDED_PRODUCTION=1" in text,
        "unexpected_a21_mode": "TOKENOSKOBI_A21_DYNAMIC_RETRY=1" in text,
        "result": next(
            (
                line.split("=", 1)[1]
                for line in text.splitlines()
                if line.startswith("Result=")
            ),
            "",
        ),
        "exec_main_status": next(
            (
                line.split("=", 1)[1]
                for line in text.splitlines()
                if line.startswith("ExecMainStatus=")
            ),
            "",
        ),
    }


def split_order_cycles(lines: list[str]) -> list[list[str]]:
    starts = [
        index
        for index, marker in enumerate(lines)
        if marker == "LOCK_ACQUIRED"
    ]
    cycles: list[list[str]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        cycles.append(lines[start:end])
    return cycles


def validate_order_cycle(cycle: list[str]) -> dict[str, Any]:
    recovery = [
        marker
        for marker in cycle
        if marker.startswith("RECOVERY_DONE:")
    ]
    if len(recovery) != 1:
        raise RuntimeError("A24_RECOVERY_MARKER_COUNT_INVALID")
    if recovery[0] not in {
        "RECOVERY_DONE:OUTPUT_ALREADY_MATCHED",
        "RECOVERY_DONE:RECOVERED",
    }:
        raise RuntimeError("A24_RECOVERY_MARKER_INVALID:" + recovery[0])

    ledger = [
        marker
        for marker in cycle
        if marker.startswith("A23_GUARDED_LEDGER_WRITE_DONE:")
    ]
    if len(ledger) != 1:
        raise RuntimeError("A24_LEDGER_MARKER_COUNT_INVALID")
    writer_status = ledger[0].split(":", 1)[1]
    if writer_status not in {"COMMITTED", "IDEMPOTENT_REPLAY_NOOP"}:
        raise RuntimeError("A24_WRITER_STATUS_INVALID:" + writer_status)

    required = [
        "LOCK_ACQUIRED",
        recovery[0],
        "RAW_START",
        "RAW_END:0",
        "DERIVED_START",
        "DERIVED_END:0",
        "HOT_START",
        "A23_GUARDED_HOT_START",
        "A23_GUARDED_ORIGINAL_HOT_END:0",
        ledger[0],
        "A23_GUARDED_PANEL_BRIDGE_END:0",
        "A23_GUARDED_HOT_END:0",
        "HOT_END:0",
    ]
    positions: list[int] = []
    for marker in required:
        if marker not in cycle:
            raise RuntimeError("A24_ORDER_MARKER_MISSING:" + marker)
        positions.append(cycle.index(marker))
    if positions != sorted(positions):
        raise RuntimeError("A24_ORDER_SEQUENCE_INVALID")
    if cycle[-1] != "HOT_END:0":
        raise RuntimeError("A24_ORDER_NOT_ENDING_HOT_ZERO")
    if "A23_GUARDED_HOT_END:1" in cycle or "HOT_END:1" in cycle:
        raise RuntimeError("A24_FAILED_ORDER_MARKER_PRESENT")
    return {
        "writer_status": writer_status,
        "recovery_marker": recovery[0],
        "markers": cycle,
    }


def journal_since(apply_finished: str) -> dict[str, Any]:
    moment = datetime.fromisoformat(apply_finished)
    since = moment.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
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
    payloads: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("{") and stripped.endswith("}")):
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(value, dict)
            and value.get("status")
            == "OK_A23_GUARDED_PRODUCTION_CYCLE_COMPLETED"
        ):
            payloads.append(value)

    failure_needles = (
        "A23_GUARDED_PRODUCTION_CYCLE_FAILED",
        "A23_GUARDED_HOT_END:1",
        "HOT_END:1",
        "Failed with result 'exit-code'",
        "Failed to start tokenoskobi-news-radar-refresh.service",
        "status=1/FAILURE",
        "Traceback (most recent call last)",
    )
    failures = [needle for needle in failure_needles if needle in text]
    return {
        "rc": completed.returncode,
        "since": since,
        "stdout": text,
        "stderr": completed.stderr,
        "cycle_payloads": payloads,
        "failure_markers": failures,
        "service_finished_count": text.count(
            "Finished tokenoskobi-news-radar-refresh.service"
        ),
    }


def validate_cycle_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("status") != "OK_A23_GUARDED_PRODUCTION_CYCLE_COMPLETED":
        raise RuntimeError("A24_PAYLOAD_STATUS_INVALID")
    writer_status = str(payload.get("writer_status"))
    if writer_status not in {"COMMITTED", "IDEMPOTENT_REPLAY_NOOP"}:
        raise RuntimeError("A24_PAYLOAD_WRITER_STATUS_INVALID")
    source_count = int(payload.get("source_candidate_count", -1))
    source_accounted = int(payload.get("source_accounted", -2))
    if not (1 <= source_count <= MAX_SOURCE_ROWS):
        raise RuntimeError("A24_PAYLOAD_SOURCE_BOUND_INVALID")
    if source_accounted != source_count:
        raise RuntimeError("A24_PAYLOAD_SOURCE_ACCOUNTING_INVALID")
    if int(payload.get("unobservable_rows", -1)) != 0:
        raise RuntimeError("A24_PAYLOAD_UNOBSERVABLE_ROWS_NONZERO")
    if not (0 < int(payload.get("legacy_queue_count", 0)) <= QUEUE_CAPACITY):
        raise RuntimeError("A24_PAYLOAD_QUEUE_BOUND_INVALID")
    for key in (
        "existing_batches_preserved",
        "exact_legacy_object_parity",
        "exact_legacy_uid_order_parity",
        "bridge_hash_match_all",
    ):
        if payload.get(key) is not True:
            raise RuntimeError("A24_PAYLOAD_BOOLEAN_GATE_FAILED:" + key)
    if int(payload.get("original_hot_rc", -1)) != 0:
        raise RuntimeError("A24_PAYLOAD_ORIGINAL_HOT_FAILED")
    if int(payload.get("bridge_rc", -1)) != 0:
        raise RuntimeError("A24_PAYLOAD_BRIDGE_FAILED")
    if payload.get("hot_output_sha256") != payload.get("panel_hot_sha256"):
        raise RuntimeError("A24_PAYLOAD_PANEL_HASH_MISMATCH")
    rollback = payload.get("rollback_guard")
    if not isinstance(rollback, dict):
        raise RuntimeError("A24_PAYLOAD_ROLLBACK_GUARD_MISSING")
    if rollback.get("policy_version") != ROLLBACK_POLICY:
        raise RuntimeError("A24_PAYLOAD_ROLLBACK_POLICY_INVALID")
    if rollback.get("armed") is not True or rollback.get("triggered") is not False:
        raise RuntimeError("A24_PAYLOAD_ROLLBACK_STATE_INVALID")
    if rollback.get("scope") != "NEW_CURRENT_CYCLE_BATCH_ONLY":
        raise RuntimeError("A24_PAYLOAD_ROLLBACK_SCOPE_INVALID")
    uid = str(payload.get("actual_batch_uid", ""))
    if not uid:
        raise RuntimeError("A24_PAYLOAD_BATCH_UID_MISSING")
    return {
        "writer_status": writer_status,
        "batch_uid": uid,
        "source_count": source_count,
        "timestamp_utc": str(payload.get("timestamp_utc", "")),
        "payload": payload,
    }


def observation_snapshot(a23: dict[str, Any]) -> dict[str, Any]:
    if not ORDER_LOG.exists():
        raise RuntimeError("A24_ORDER_LOG_MISSING")
    lines = ORDER_LOG.read_text(encoding="utf-8").splitlines()
    cycles = split_order_cycles(lines)
    if not cycles:
        raise RuntimeError("A24_NO_ORDER_CYCLES")
    if cycles[0] != a23["runner_order"]:
        raise RuntimeError("A24_CONTROLLED_CYCLE_ORDER_DRIFT")
    validated_order = [validate_order_cycle(cycle) for cycle in cycles]
    natural_order = validated_order[1:]

    journal = journal_since(str(a23["apply_finished_at_utc"]))
    if journal["failure_markers"]:
        raise RuntimeError(
            "A24_POST_ACTIVATION_FAILURE_MARKERS:"
            + ",".join(journal["failure_markers"])
        )
    payloads = [
        validate_cycle_payload(payload)
        for payload in journal["cycle_payloads"]
    ]
    if len(natural_order) != len(payloads):
        raise RuntimeError(
            "A24_ORDER_JOURNAL_CYCLE_COUNT_MISMATCH:"
            + str(len(natural_order))
            + ":"
            + str(len(payloads))
        )
    if journal["service_finished_count"] < len(payloads):
        raise RuntimeError("A24_SERVICE_SUCCESS_COUNT_TOO_LOW")
    for index, order_cycle in enumerate(natural_order):
        if order_cycle["writer_status"] != payloads[index]["writer_status"]:
            raise RuntimeError("A24_ORDER_PAYLOAD_WRITER_STATUS_MISMATCH")

    return {
        "order_log_lines": lines,
        "all_order_cycles": validated_order,
        "natural_order_cycles": natural_order,
        "journal": journal,
        "natural_payloads": payloads,
    }


def backup_repo_state(backup_root: Path) -> dict[Path, Path]:
    result: dict[Path, Path] = {}
    for index, path in enumerate((RUNTIME, HISTORY, MASTER, HANDOFF, ALMANAC)):
        target = backup_root / f"{index:02d}.backup"
        shutil.copy2(path, target)
        result[path] = target
    return result


def restore_repo_state(backups: dict[Path, Path]) -> None:
    for path, backup in backups.items():
        shutil.copy2(backup, path)
    for path in (ARTIFACT, REPORT):
        if path.exists():
            path.unlink()


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(
        rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND:{heading}")
    return (
        text[: match.start()]
        + heading
        + "\n\n"
        + body.rstrip()
        + "\n"
        + text[match.end() :]
    )


def verify_persistent_runtime(a23: dict[str, Any]) -> dict[str, Any]:
    if not DROPIN.exists():
        raise RuntimeError("A24_PERSISTENT_DROPIN_MISSING")
    if sha(DROPIN) != a23["persistent_integration"]["dropin_sha256"]:
        raise RuntimeError("A24_PERSISTENT_DROPIN_HASH_DRIFT")
    environment = service_environment()
    if not environment["runner_bound"]:
        raise RuntimeError("A24_RUNNER_NOT_BOUND")
    if not environment["writer_enabled"]:
        raise RuntimeError("A24_WRITER_FLAG_DISABLED")
    if not environment["runner_lock_enabled"]:
        raise RuntimeError("A24_RUNNER_LOCK_DISABLED")
    if not environment["hot_override_enabled"]:
        raise RuntimeError("A24_HOT_OVERRIDE_DRIFT")
    if not environment["guarded_mode_enabled"]:
        raise RuntimeError("A24_GUARDED_MODE_DISABLED")
    if environment["unexpected_a21_mode"]:
        raise RuntimeError("A24_UNEXPECTED_A21_MODE_ACTIVE")
    return environment


def verify_database(
    a23: dict[str, Any],
    natural_payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    inventory = database_inventory(DB)
    if inventory["integrity_check"] != "ok":
        raise RuntimeError("A24_DATABASE_INTEGRITY_FAILED")
    if inventory["quick_check"] != "ok":
        raise RuntimeError("A24_DATABASE_QUICK_CHECK_FAILED")
    if inventory["foreign_key_check_rows"] != 0:
        raise RuntimeError("A24_DATABASE_FOREIGN_KEY_FAILED")
    if set(inventory["triggers"]) != {
        "trg_news_disposition_batch_archive_before_delete_v2",
        "trg_news_disposition_ledger_archive_before_delete_v2",
    }:
        raise RuntimeError("A24_DATABASE_TRIGGER_SET_DRIFT")

    original = a23["production_after"]
    original_map = batch_map(original)
    current_map = batch_map(inventory)
    for uid, batch in original_map.items():
        if current_map.get(uid) != batch:
            raise RuntimeError("A24_ORIGINAL_BATCH_MUTATED:" + uid)

    expected_uids = set(original_map)
    expected_ledger_rows = int(original["ledger_rows"])
    committed_uids: list[str] = []
    replay_uids: list[str] = []
    for item in natural_payloads:
        uid = item["batch_uid"]
        if item["writer_status"] == "COMMITTED":
            if uid in expected_uids:
                raise RuntimeError("A24_COMMITTED_UID_ALREADY_EXISTED:" + uid)
            expected_uids.add(uid)
            committed_uids.append(uid)
            expected_ledger_rows += int(item["source_count"])
        else:
            if uid not in expected_uids:
                raise RuntimeError("A24_REPLAY_UID_NOT_PREEXISTING:" + uid)
            replay_uids.append(uid)

    if set(current_map) != expected_uids:
        raise RuntimeError("A24_FINAL_BATCH_UID_SET_MISMATCH")
    if inventory["batch_rows"] != len(expected_uids):
        raise RuntimeError("A24_FINAL_BATCH_COUNT_MISMATCH")
    if inventory["ledger_rows"] != expected_ledger_rows:
        raise RuntimeError("A24_FINAL_LEDGER_COUNT_MISMATCH")

    expected_sequence = 1
    for batch in inventory["batches"]:
        if batch["batch_sequence"] != expected_sequence:
            raise RuntimeError("A24_BATCH_SEQUENCE_GAP")
        expected_sequence += 1
        if batch["status"] != "COMMITTED":
            raise RuntimeError("A24_BATCH_NOT_COMMITTED:" + batch["batch_uid"])
        if batch["policy_version"] != LEDGER_POLICY:
            raise RuntimeError("A24_BATCH_POLICY_DRIFT:" + batch["batch_uid"])
        if not (1 <= batch["source_candidate_count"] <= MAX_SOURCE_ROWS):
            raise RuntimeError("A24_BATCH_SOURCE_BOUND_INVALID:" + batch["batch_uid"])
        if batch["queue_capacity"] != QUEUE_CAPACITY:
            raise RuntimeError("A24_BATCH_QUEUE_CAPACITY_DRIFT:" + batch["batch_uid"])
        if batch["ledger_rows"] != batch["source_candidate_count"]:
            raise RuntimeError("A24_BATCH_LEDGER_ACCOUNTING_FAILED:" + batch["batch_uid"])
        if sum(batch["disposition_counts"].values()) != batch["source_candidate_count"]:
            raise RuntimeError("A24_BATCH_DISPOSITION_ACCOUNTING_FAILED:" + batch["batch_uid"])

    return {
        "inventory": inventory,
        "committed_natural_cycle_uids": committed_uids,
        "replay_natural_cycle_uids": replay_uids,
    }


def main() -> int:
    if not EXPECTED_HEAD:
        raise RuntimeError("TOKENOSKOBI_EXPECTED_HEAD_REQUIRED")
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BRANCH_NOT_MAIN")
    if git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("UNEXPECTED_HEAD")
    if git("status", "--porcelain"):
        raise RuntimeError("WORKTREE_NOT_CLEAN")

    for path in (
        A23,
        A23_TOOL,
        ROLLBACK_GUARD,
        RUNNER,
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
    ):
        if not path.exists():
            raise FileNotFoundError(path)
    if ARTIFACT.exists():
        raise RuntimeError("A24_ARTIFACT_ALREADY_EXISTS")

    a23 = load(A23)
    assert a23["status"] == "CLOSED_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVE_POST_AUDIT"
    assert a23["result"] == "OK_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_ACTIVE"
    assert a23["authorization"]["production_writer_active"] is True
    assert a23["authorization"]["p0_f1_closed"] is False
    assert a23["authorization"]["option_b_authorized"] is False
    assert a23["persistent_integration"]["dropin_persistent"] is True
    assert a23["post_apply_audit"]["runner_hot_end_zero"] is True
    assert a23["post_apply_audit"]["complete_source_accounting"] is True
    assert a23["post_apply_audit"]["hot_panel_hash_match"] is True
    assert a23["rollback_protection"]["armed_for_every_cycle"] is True
    assert a23["next_safe_step"] == WORK_UNIT

    timer_initial = systemctl_state(TIMER)
    if timer_initial["active"] != "active" or timer_initial["enabled"] != "enabled":
        raise RuntimeError("A24_TIMER_PRECONDITION_FAILED")
    verify_persistent_runtime(a23)

    deadline = time.time() + OBSERVATION_TIMEOUT_SECONDS
    last_notice = 0.0
    while True:
        service = systemctl_state(SERVICE)
        if service["active"] not in {"active", "activating", "deactivating"}:
            try:
                snapshot = observation_snapshot(a23)
                if len(snapshot["natural_payloads"]) >= MINIMUM_NATURAL_CYCLES:
                    break
            except RuntimeError as exc:
                message = str(exc)
                if not (
                    message.startswith("A24_ORDER_JOURNAL_CYCLE_COUNT_MISMATCH")
                    or message in {
                        "A24_ORDER_LOG_MISSING",
                        "A24_NO_ORDER_CYCLES",
                    }
                ):
                    raise
        if time.time() >= deadline:
            raise RuntimeError("A24_NATURAL_TIMER_OBSERVATION_TIMEOUT")
        if time.time() - last_notice >= 60:
            print("A24_OBSERVATION_WAITING_FOR_NATURAL_TIMER_CYCLE=true", flush=True)
            last_notice = time.time()
        time.sleep(5)

    timer_restored = False
    repo_backup_root: Path | None = None
    repo_backups: dict[Path, Path] = {}

    def restore_timer() -> None:
        nonlocal timer_restored
        if timer_initial["active"] == "active":
            run(["systemctl", "start", TIMER], check=False, timeout=30)
        timer_restored = True

    def cleanup() -> None:
        if repo_backups:
            try:
                restore_repo_state(repo_backups)
            except Exception:
                pass
        if not timer_restored:
            restore_timer()
        if repo_backup_root is not None:
            shutil.rmtree(repo_backup_root, ignore_errors=True)

    atexit.register(cleanup)

    run(["systemctl", "stop", TIMER], check=True, timeout=30)
    deadline_inactive = time.time() + 180
    while time.time() < deadline_inactive:
        if systemctl_state(SERVICE)["active"] in {"inactive", "failed"}:
            break
        time.sleep(0.5)
    else:
        raise RuntimeError("A24_SERVICE_DID_NOT_BECOME_INACTIVE")

    snapshot = observation_snapshot(a23)
    natural_payloads = snapshot["natural_payloads"]
    if len(natural_payloads) < MINIMUM_NATURAL_CYCLES:
        raise RuntimeError("A24_NATURAL_CYCLE_COUNT_BELOW_MINIMUM")

    environment = verify_persistent_runtime(a23)
    database = verify_database(a23, natural_payloads)
    inventory = database["inventory"]

    if sha(HOT) != sha(PANEL_HOT):
        raise RuntimeError("A24_CURRENT_PANEL_HOT_HASH_MISMATCH")
    bridge = load(BRIDGE_STATE)
    if bridge.get("decision") != "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED":
        raise RuntimeError("A24_CURRENT_BRIDGE_DECISION_INVALID")
    if bridge.get("failures") != []:
        raise RuntimeError("A24_CURRENT_BRIDGE_FAILURES_PRESENT")
    hash_match = bridge.get("hash_match")
    if not isinstance(hash_match, dict) or not hash_match or not all(
        value is True for value in hash_match.values()
    ):
        raise RuntimeError("A24_CURRENT_BRIDGE_HASH_MISMATCH")

    latest_result = load(RESULT_PATH)
    guarded_state = load(GUARDED_STATE)
    latest_payload = natural_payloads[-1]["payload"]
    if canonical(latest_result) != canonical(guarded_state):
        raise RuntimeError("A24_RESULT_GUARDED_STATE_PARITY_FAILED")
    if canonical(latest_result) != canonical(latest_payload):
        raise RuntimeError("A24_LATEST_JOURNAL_RESULT_PARITY_FAILED")
    if ERROR_PATH.exists():
        error_value = load(ERROR_PATH)
        if error_value.get("status") == "A23_GUARDED_PRODUCTION_CYCLE_FAILED":
            raise RuntimeError("A24_ACTIVE_FAILURE_STATE_PRESENT")

    apply_finished = datetime.fromisoformat(str(a23["apply_finished_at_utc"]))
    latest_finished = datetime.fromisoformat(str(latest_payload["timestamp_utc"]))
    if latest_finished <= apply_finished:
        raise RuntimeError("A24_LATEST_CYCLE_NOT_POST_ACTIVATION")

    repo_backup_root = Path(tempfile.mkdtemp(prefix="era55a24_repo_"))
    repo_backups = backup_repo_state(repo_backup_root)

    timestamp = utc_now()
    closure_gates = {
        "a23_persistent_integration_verified": True,
        "minimum_natural_timer_cycles_observed": True,
        "all_observed_natural_cycles_successful": True,
        "all_observed_cycles_runner_hot_end_zero": True,
        "all_observed_cycles_complete_source_accounting": True,
        "all_observed_cycles_zero_unobservable_rows": True,
        "all_observed_cycles_exact_legacy_queue_parity": True,
        "all_observed_cycles_panel_hash_parity": True,
        "all_observed_cycles_rollback_guard_armed": True,
        "no_post_activation_failure_marker": True,
        "all_original_committed_batches_preserved": True,
        "all_natural_cycle_batches_accounted": True,
        "production_database_integrity_clean": True,
        "persistent_runtime_environment_unchanged": True,
        "timer_configuration_preserved": True,
    }
    assert all(closure_gates.values())

    artifact = {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "timestamp_utc": timestamp,
        "status": "CLOSED_POST_ACTIVATION_OBSERVATION_OK_P0_F1_CLOSED",
        "result": RESULT,
        "authorization_source": str(A23.relative_to(ROOT)),
        "observation_policy": {
            "forced_service_cycle": False,
            "minimum_natural_cycles_required": MINIMUM_NATURAL_CYCLES,
            "natural_cycles_observed": len(natural_payloads),
            "observation_started_after_utc": a23["apply_finished_at_utc"],
            "observation_finished_at_utc": timestamp,
        },
        "closure_gates": closure_gates,
        "natural_cycle_summaries": [
            {
                "timestamp_utc": item["timestamp_utc"],
                "writer_status": item["writer_status"],
                "batch_uid": item["batch_uid"],
                "source_candidate_count": item["source_count"],
                "source_accounted": item["source_count"],
                "unobservable_rows": 0,
                "runner_hot_end_zero": True,
                "panel_hash_parity": True,
                "rollback_guard_armed": True,
            }
            for item in natural_payloads
        ],
        "order_cycle_count_total": len(snapshot["all_order_cycles"]),
        "natural_order_cycle_count": len(snapshot["natural_order_cycles"]),
        "journal_service_finished_count": snapshot["journal"]["service_finished_count"],
        "journal_failure_markers": snapshot["journal"]["failure_markers"],
        "production_at_closure": inventory,
        "committed_natural_cycle_uids": database["committed_natural_cycle_uids"],
        "replay_natural_cycle_uids": database["replay_natural_cycle_uids"],
        "persistent_environment": environment,
        "persistent_dropin": {
            "path": str(DROPIN),
            "sha256": sha(DROPIN),
            "matches_a23": sha(DROPIN) == a23["persistent_integration"]["dropin_sha256"],
        },
        "current_output_audit": {
            "hot_sha256": sha(HOT),
            "panel_hot_sha256": sha(PANEL_HOT),
            "hot_panel_hash_match": sha(HOT) == sha(PANEL_HOT),
            "bridge_decision": bridge["decision"],
            "bridge_hash_match_all": True,
            "result_guarded_state_parity": True,
            "latest_journal_result_parity": True,
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
        f"""# ERA55A24 Post-Activation Observation and P0 F1 Closure

- Status: `CLOSED_POST_ACTIVATION_OBSERVATION_OK_P0_F1_CLOSED`
- Result: `{RESULT}`
- Forced service cycle: `false`
- Natural timer cycles observed: `{len(natural_payloads)}`
- All observed cycles successful: `true`
- Production batch rows: `{inventory['batch_rows']}`
- Production ledger rows: `{inventory['ledger_rows']}`
- Original committed batches preserved: `true`
- Runner HOT_END:0: `true`
- Complete source accounting: `true`
- Unobservable rows: `0`
- Panel hash parity: `true`
- Rollback guard armed for every cycle: `true`
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
            "mode": "ERA55A24_POST_ACTIVATION_OBSERVATION_P0_F1_CLOSED",
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
                "type": "ERA55_P0_POST_ACTIVATION_OBSERVATION_AND_P0_F1_CLOSURE_DECISION",
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
                "purpose": (
                    "Decide Option B readiness and authorization after P0 F1 closure; "
                    "do not apply Option B in the decision step."
                ),
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
    event_id = "ERA55A24_POST_ACTIVATION_OBSERVATION_P0_F1_CLOSED_V1"
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
                "event": "POST_ACTIVATION_NATURAL_TIMER_OBSERVATION_AND_P0_F1_CLOSURE",
                "status": artifact["status"],
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "natural_cycles_observed": len(natural_payloads),
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
NATURAL_TIMER_CYCLES_OBSERVED={len(natural_payloads)}
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

P0 F1 is closed. Option B remains blocked pending a separate readiness and authorization decision.""",
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
NATURAL_TIMER_CYCLES_OBSERVED={len(natural_payloads)}
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
        """- Do not rerun A9-A24 unless evidence is invalidated.
- Do not execute another canary.
- Do not remove or edit the A23 persistent integration without a rollback plan.
- Do not delete any valid committed production batch.
- Do not apply or authorize Option B inside A24.""",
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
        """1. Confirm A25 is current and A24 closure evidence remains valid.
2. Evaluate Option B scope, measurable benefit, safety, economy and rollback boundaries.
3. Do not apply Option B during the readiness decision.
4. Keep the guarded production writer active and unchanged.
5. Require explicit human authorization for any Option B apply step.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac = ALMANAC.read_text(encoding="utf-8")
    marker = "## ERA55A_24 POST-ACTIVATION OBSERVATION AND P0 F1 CLOSURE"
    if marker not in almanac:
        ALMANAC.write_text(
            almanac.rstrip()
            + f"""

---

{marker}

- Status: `CLOSED_POST_ACTIVATION_OBSERVATION_OK_P0_F1_CLOSED`
- Result: `{RESULT}`
- Forced service cycle: `false`
- Natural timer cycles observed: `{len(natural_payloads)}`
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
        raise RuntimeError("A24_NO_STAGED_CHANGES")
    git("commit", "-m", SUBJECT)

    repo_backups = {}
    restore_timer()
    timer_after = systemctl_state(TIMER)
    if timer_after["active"] != timer_initial["active"]:
        raise RuntimeError("A24_TIMER_ACTIVE_STATE_NOT_RESTORED")
    if timer_after["enabled"] != timer_initial["enabled"]:
        raise RuntimeError("A24_TIMER_ENABLED_STATE_CHANGED")
    verify_persistent_runtime(a23)

    atexit.unregister(cleanup)
    if repo_backup_root is not None:
        shutil.rmtree(repo_backup_root, ignore_errors=True)

    print("ERA55A24_POST_ACTIVATION_OBSERVATION=SUCCESS")
    print("RESULT=" + RESULT)
    print("FORCED_SERVICE_CYCLE=false")
    print("NATURAL_TIMER_CYCLES_OBSERVED=" + str(len(natural_payloads)))
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
