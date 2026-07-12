#!/usr/bin/env python3
from __future__ import annotations

import atexit
import hashlib
import importlib.util
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

WORK_UNIT = "ERA55A_21_P0_SINGLE_NATURAL_CYCLE_POST_REMEDIATION_CANARY_DYNAMIC_IDENTITY_RETRY_AND_POST_AUDIT"
RESULT = "OK_POST_REMEDIATION_DYNAMIC_IDENTITY_SINGLE_CYCLE_PRODUCTION_CANARY_COMPLETED"
NEXT = "ERA55A_22_P0_POST_REMEDIATION_CANARY_RED_TEAM_GENERAL_PRODUCTION_ACTIVATION_DECISION"
SUBJECT = "ERA55A21_DYNAMIC_IDENTITY_CANARY | OK | GENERAL_ACTIVATION_BLOCKED"
LEDGER_POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"
ROLLBACK_POLICY = "POSTCOMMIT_ARCHIVE_TRIGGER_ROLLBACK_GUARD_V1"
MAX_SOURCE_ROWS = 5000
QUEUE_CAPACITY = 50

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

A20 = ROOT / "data/control/era55a20_p0_post_remediation_audit_and_production_canary_decision_v1.json"
A20R = ROOT / "data/control/era55a20r_p0_dynamic_batch_identity_authorization_correction_v1.json"
ARTIFACT = ROOT / "data/control/era55a21_p0_single_natural_cycle_post_remediation_canary_dynamic_identity_retry_and_post_audit_v2.json"
REPORT = ROOT / "reports/LATEST_ERA55A21_P0_SINGLE_NATURAL_CYCLE_POST_REMEDIATION_CANARY_DYNAMIC_IDENTITY_RETRY_AND_POST_AUDIT.md"

SELF = Path(__file__).resolve()
ADAPTER = ROOT / "tools/news_disposition_admission_contract_v1.py"
EXTRACTOR = ROOT / "tools/news_pre_gateway_candidate_stream_v1.py"
ROLLBACK_GUARD = ROOT / "tools/news_disposition_postcommit_rollback_guard_v1.py"
RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
ORIGINAL_HOT = ROOT / "tools/post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.py"
PANEL_BRIDGE = ROOT / "tools/news_active_panel_data_bridge_v1.py"

MARKET = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADVERSARIAL = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
RECOVERY_STATE = ROOT / "runtime/state/news_ledger_recovery_state_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

RUNTIME_ROOT = Path("/run/tokenoskobi")
DROPIN_DIR = Path("/run/systemd/system") / f"{SERVICE}.d"
DROPIN = DROPIN_DIR / "90-era55a21-dynamic-retry.conf"
RESULT_PATH = RUNTIME_ROOT / "era55a21_dynamic_retry_result.json"
ERROR_PATH = RUNTIME_ROOT / "era55a21_dynamic_retry_error.json"
INVOCATION_GUARD = RUNTIME_ROOT / "era55a21_dynamic_retry_invocation.guard"
ORDER_LOG = RUNTIME_ROOT / "era55a21_dynamic_retry_order.log"
FULL_DISPLAY = RUNTIME_ROOT / "era55a21_dynamic_retry_full_candidate_display.json"
WRITER_LOCK = RUNTIME_ROOT / "era55a21_dynamic_retry_writer.lock"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(
    args: list[str],
    *,
    check: bool = True,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
        timeout=timeout,
        env=env,
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


def file_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    stat = path.stat()
    return {
        "exists": True,
        "sha256": sha(path),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def append_order(marker: str) -> None:
    path = Path(os.environ.get("TOKENOSKOBI_A10_ORDER_LOG", str(ORDER_LOG)))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(marker + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def record_one_shot_error(exc: BaseException) -> None:
    try:
        atomic_dump(
            ERROR_PATH,
            {
                "status": "A21_DYNAMIC_RETRY_ONE_SHOT_FAILED",
                "timestamp_utc": utc_now(),
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
    except Exception:
        pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def backup_sqlite(source: Path, target: Path) -> None:
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target_connection = sqlite3.connect(target)
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()


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
            dispositions = {
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
                    "disposition_counts": dispositions,
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
        "any_hot_override": "TOKENOSKOBI_NEWS_HOT_PATH=" in text,
        "hot_override_enabled": f"TOKENOSKOBI_NEWS_HOT_PATH={SELF}" in text,
        "retry_mode_enabled": "TOKENOSKOBI_A21_DYNAMIC_RETRY=1" in text,
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


def mutable_output_paths() -> list[Path]:
    result: set[Path] = set()
    runtime_state = ROOT / "runtime/state"
    panel_data = ROOT / "active_panel_8096/current/data"
    for pattern in ("news_*", "hot_intelligence_ingress_gateway_v1.json"):
        result.update(path for path in runtime_state.glob(pattern) if path.is_file())
        result.update(path for path in panel_data.glob(pattern) if path.is_file())
    return sorted(result, key=lambda path: str(path))


def backup_files(paths: list[Path], backup_root: Path) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for index, path in enumerate(paths):
        relative = str(path.relative_to(ROOT))
        backup = backup_root / "files" / f"{index:04d}.backup"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        metadata[relative] = {
            "path": path,
            "backup": backup,
            "state": file_state(path),
        }
    return metadata


def restore_mutable_outputs(metadata: dict[str, dict[str, Any]]) -> None:
    original_paths = {Path(item["path"]) for item in metadata.values()}
    current_paths = set(mutable_output_paths())
    for path in sorted(
        current_paths - original_paths,
        key=lambda item: str(item),
        reverse=True,
    ):
        path.unlink()
    for item in metadata.values():
        path = Path(item["path"])
        backup = Path(item["backup"])
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.parent / ("." + path.name + ".a21dynamicrestore")
        shutil.copy2(backup, temp)
        os.replace(temp, path)


def backup_repo_state(backup_root: Path) -> dict[Path, Path]:
    result: dict[Path, Path] = {}
    for index, path in enumerate((RUNTIME, HISTORY, MASTER, HANDOFF, ALMANAC)):
        target = backup_root / "repo" / f"{index:02d}.backup"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        result[path] = target
    return result


def restore_repo_state(backups: dict[Path, Path]) -> None:
    for path, backup in backups.items():
        shutil.copy2(backup, path)
    for path in (ARTIFACT, REPORT):
        if path.exists():
            path.unlink()


def restore_database_from_backup(backup: Path) -> None:
    for suffix in ("-wal", "-shm"):
        candidate = Path(str(DB) + suffix)
        if candidate.exists():
            candidate.unlink()
    temp = DB.parent / ("." + DB.name + ".a21dynamicrestore")
    shutil.copy2(backup, temp)
    os.replace(temp, DB)


def remove_dropin() -> None:
    if DROPIN.exists():
        DROPIN.unlink()
    try:
        DROPIN_DIR.rmdir()
    except OSError:
        pass
    run(["systemctl", "daemon-reload"], check=False, timeout=30)


def restore_timer(before: dict[str, Any]) -> None:
    if before["active"] == "active":
        run(["systemctl", "start", TIMER], check=True, timeout=30)
    else:
        run(["systemctl", "stop", TIMER], check=False, timeout=30)


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


def verify_authorization() -> tuple[dict[str, Any], dict[str, Any]]:
    a20 = load(A20)
    a20r = load(A20R)
    assert a20["status"] == "CLOSED_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED"
    assert a20["authorization"]["general_production_writer_activation_authorized"] is False
    assert a20r["status"] == "CLOSED_BOUNDED_DYNAMIC_BATCH_IDENTITY_AUTHORIZATION_CORRECTED"
    assert a20r["result"] == "OK_BOUNDED_DYNAMIC_BATCH_IDENTITY_AND_ONE_PREWRITE_RETRY_AUTHORIZED"
    failed = a20r["failed_attempt_evidence"]
    assert failed["failure_stage"] == "PREWRITE_AFTER_ORIGINAL_HOT_REFRESH"
    assert failed["ledger_write_started"] is False
    assert failed["new_batch_committed"] is False
    assert failed["baseline_preserved"] is True
    contract = a20r["corrected_canary_contract"]
    assert contract["exactly_one_full_runner_cycle"] is True
    assert contract["one_retry_after_prewrite_failure_authorized"] is True
    assert contract["maximum_new_batch_rows"] == 1
    assert contract["new_batch_uid_must_be_computed_after_original_hot_refresh"] is True
    assert contract["new_batch_uid_must_differ_from_baseline"] is True
    assert contract["minimum_source_candidate_count"] == 1
    assert contract["maximum_source_candidate_count"] == MAX_SOURCE_ROWS
    assert contract["source_accounting_must_be_complete"] is True
    assert contract["queue_capacity"] == QUEUE_CAPACITY
    assert contract["rollback_guard_policy"] == ROLLBACK_POLICY
    auth = a20r["authorization"]
    assert auth["one_post_remediation_production_canary_retry_authorized"] is True
    assert auth["previous_failed_attempt_consumed_authorization"] is False
    assert auth["new_production_canary_authorized"] is True
    assert auth["additional_canary_after_retry_authorized"] is False
    assert auth["general_production_writer_activation_authorized"] is False
    return a20, a20r


def one_shot_hot() -> int:
    try:
        token = os.environ.get("TOKENOSKOBI_A21_DYNAMIC_TOKEN", "").strip()
        expected = os.environ.get("TOKENOSKOBI_A21_DYNAMIC_EXPECTED_HEAD", "").strip()
        if not token or not expected:
            raise RuntimeError("A21_DYNAMIC_CANARY_ENVIRONMENT_INCOMPLETE")
        if git("rev-parse", "HEAD") != expected:
            raise RuntimeError("A21_DYNAMIC_CANARY_HEAD_MISMATCH")

        _, a20r = verify_authorization()
        baseline_uid = str(
            a20r["corrected_canary_contract"][
                "baseline_batch_uid_must_be_preserved"
            ]
        )

        INVOCATION_GUARD.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(
            INVOCATION_GUARD,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        try:
            os.write(fd, token.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)

        append_order("A21_DYNAMIC_ONE_SHOT_START")
        original = run(
            [sys.executable, str(ORIGINAL_HOT), "--runtime-refresh"],
            check=False,
            timeout=180,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        append_order(f"A21_DYNAMIC_ORIGINAL_HOT_END:{original.returncode}")
        if original.returncode != 0:
            raise RuntimeError(
                "A21_DYNAMIC_ORIGINAL_HOT_FAILED:"
                + str(original.returncode)
                + ":"
                + original.stderr[-3000:]
            )

        legacy_contract = load(HOT)
        legacy_queue = legacy_contract.get("hot_queue")
        if not isinstance(legacy_queue, list):
            raise RuntimeError("A21_DYNAMIC_LEGACY_HOT_QUEUE_NOT_LIST")

        tools_path = str(ROOT / "tools")
        if tools_path not in sys.path:
            sys.path.insert(0, tools_path)
        extractor = load_module("a21_dynamic_extractor", EXTRACTOR)
        adapter = load_module("a21_dynamic_adapter", ADAPTER)
        if adapter.POLICY_VERSION != LEDGER_POLICY:
            raise RuntimeError("A21_DYNAMIC_LEDGER_POLICY_MISMATCH")

        full_display = extractor.build_candidate_display(MARKET, ADVERSARIAL)
        atomic_dump(FULL_DISPLAY, full_display)
        plan = adapter.build_plan_with_admission_contract(
            full_display,
            legacy_queue,
            queue_capacity=QUEUE_CAPACITY,
        )
        actual_uid = str(plan["batch_uid"])
        counts = plan["counts"]
        source_count = int(counts["source_candidate_count"])
        accounted = sum(
            int(counts[key])
            for key in (
                "admitted_count",
                "overflow_count",
                "duplicate_removed_count",
                "unsafe_filtered_count",
                "invalid_candidate_count",
                "replaced_count",
            )
        )
        if not (0 < len(legacy_queue) <= QUEUE_CAPACITY):
            raise RuntimeError("A21_DYNAMIC_LEGACY_QUEUE_BOUND_FAILED")
        if not (1 <= source_count <= MAX_SOURCE_ROWS):
            raise RuntimeError("A21_DYNAMIC_SOURCE_BOUND_FAILED")
        if accounted != source_count:
            raise RuntimeError("A21_DYNAMIC_SOURCE_ACCOUNTING_FAILED")
        if int(counts["admitted_count"]) != len(legacy_queue):
            raise RuntimeError("A21_DYNAMIC_ADMITTED_COUNT_PARITY_FAILED")
        if actual_uid == baseline_uid:
            raise RuntimeError("A21_DYNAMIC_NEW_UID_EQUALS_BASELINE")

        before = database_inventory(DB)
        before_map = batch_map(before)
        if set(before_map) != {baseline_uid}:
            raise RuntimeError("A21_DYNAMIC_BASELINE_BATCH_SET_DRIFT")

        writer_result = adapter.write_and_publish_with_admission_contract(
            display_path=FULL_DISPLAY,
            admission_contract_path=HOT,
            summary_path=SUMMARY,
            db_path=DB,
            output_path=HOT,
            recovery_state_path=RECOVERY_STATE,
            contract_seed_path=HOT,
            queue_capacity=QUEUE_CAPACITY,
            lock_path=WRITER_LOCK,
        )
        writer_status = str(
            writer_result.get("write_result", {}).get("status")
        )
        append_order("A21_DYNAMIC_LEDGER_WRITE_DONE:" + writer_status)
        if writer_status != "COMMITTED":
            raise RuntimeError(
                "A21_DYNAMIC_LEDGER_WRITE_NOT_COMMITTED:" + writer_status
            )

        final_queue = load(HOT).get("hot_queue")
        if canonical(final_queue) != canonical(legacy_queue):
            raise RuntimeError("A21_DYNAMIC_FINAL_QUEUE_PARITY_FAILED")

        bridge = run(
            [sys.executable, str(PANEL_BRIDGE)],
            check=False,
            timeout=120,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        append_order(f"A21_DYNAMIC_PANEL_BRIDGE_END:{bridge.returncode}")
        if bridge.returncode != 0:
            raise RuntimeError(
                "A21_DYNAMIC_PANEL_BRIDGE_FAILED:"
                + str(bridge.returncode)
                + ":"
                + bridge.stdout[-3000:]
                + bridge.stderr[-3000:]
            )
        bridge_state = load(BRIDGE_STATE)
        if bridge_state.get("decision") != "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED":
            raise RuntimeError("A21_DYNAMIC_PANEL_BRIDGE_DECISION_NOT_OK")
        hash_match = bridge_state.get("hash_match")
        if not isinstance(hash_match, dict) or not hash_match or not all(
            value is True for value in hash_match.values()
        ):
            raise RuntimeError("A21_DYNAMIC_PANEL_BRIDGE_HASH_MISMATCH")
        if sha(HOT) != sha(PANEL_HOT):
            raise RuntimeError("A21_DYNAMIC_PANEL_HOT_HASH_MISMATCH")

        after = database_inventory(DB)
        after_map = batch_map(after)
        if set(after_map) != {baseline_uid, actual_uid}:
            raise RuntimeError("A21_DYNAMIC_POSTWRITE_BATCH_SET_INVALID")
        if after_map[baseline_uid] != before_map[baseline_uid]:
            raise RuntimeError("A21_DYNAMIC_BASELINE_BATCH_MUTATED")
        new_batch = after_map[actual_uid]
        if new_batch["source_candidate_count"] != source_count:
            raise RuntimeError("A21_DYNAMIC_NEW_BATCH_SOURCE_COUNT_MISMATCH")
        if new_batch["ledger_rows"] != source_count:
            raise RuntimeError("A21_DYNAMIC_NEW_BATCH_LEDGER_COUNT_MISMATCH")

        payload = {
            "schema_version": "1.0",
            "token": token,
            "status": "OK_A21_DYNAMIC_IDENTITY_ONE_SHOT_COMPLETED",
            "timestamp_utc": utc_now(),
            "original_hot_rc": original.returncode,
            "bridge_rc": bridge.returncode,
            "bridge_decision": bridge_state["decision"],
            "bridge_hash_match_all": True,
            "baseline_batch_uid": baseline_uid,
            "new_batch_uid": actual_uid,
            "new_batch_sequence": new_batch["batch_sequence"],
            "source_candidate_count": source_count,
            "source_accounted": accounted,
            "unobservable_rows": source_count - accounted,
            "legacy_queue_count": len(legacy_queue),
            "exact_legacy_object_parity": True,
            "exact_legacy_uid_order_parity": True,
            "new_batch_ledger_rows": new_batch["ledger_rows"],
            "disposition_counts": new_batch["disposition_counts"],
            "writer_status": writer_status,
            "publish_status": writer_result["publish_result"]["status"],
            "hot_output_sha256": sha(HOT),
            "panel_hot_sha256": sha(PANEL_HOT),
            "policy_version": new_batch["policy_version"],
            "bounded_dynamic_identity": True,
        }
        atomic_dump(RESULT_PATH, payload)
        append_order("A21_DYNAMIC_ONE_SHOT_END:0")
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
        return 0
    except Exception as exc:
        record_one_shot_error(exc)
        raise


def orchestrate() -> int:
    if not EXPECTED_HEAD:
        raise RuntimeError("TOKENOSKOBI_EXPECTED_HEAD_REQUIRED")
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BRANCH_NOT_MAIN")
    if git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("UNEXPECTED_HEAD")
    if git("status", "--porcelain"):
        raise RuntimeError("WORKTREE_NOT_CLEAN")

    for path in (
        A20,
        A20R,
        SELF,
        ADAPTER,
        EXTRACTOR,
        ROLLBACK_GUARD,
        RUNNER,
        ORIGINAL_HOT,
        PANEL_BRIDGE,
        MARKET,
        ADVERSARIAL,
        SUMMARY,
        HOT,
        BRIDGE_STATE,
        PANEL_HOT,
        DB,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
    ):
        if not path.exists():
            raise FileNotFoundError(path)
    if ARTIFACT.exists():
        raise RuntimeError("A21_DYNAMIC_ARTIFACT_ALREADY_EXISTS")
    if DROPIN.exists():
        raise RuntimeError("A21_DYNAMIC_DROPIN_ALREADY_PRESENT")

    _, a20r = verify_authorization()
    baseline_uid = str(
        a20r["corrected_canary_contract"][
            "baseline_batch_uid_must_be_preserved"
        ]
    )

    timer_before = systemctl_state(TIMER)
    service_initial = systemctl_state(SERVICE)
    environment_initial = service_environment()
    if timer_before["active"] != "active" or timer_before["enabled"] != "enabled":
        raise RuntimeError("A21_DYNAMIC_TIMER_PRECONDITION_FAILED")
    if environment_initial["writer_enabled"]:
        raise RuntimeError("A21_DYNAMIC_WRITER_ALREADY_ENABLED")
    if environment_initial["runner_lock_enabled"]:
        raise RuntimeError("A21_DYNAMIC_RUNNER_LOCK_ALREADY_ENABLED")
    if environment_initial["any_hot_override"]:
        raise RuntimeError("A21_DYNAMIC_HOT_OVERRIDE_ALREADY_ENABLED")
    if environment_initial["retry_mode_enabled"]:
        raise RuntimeError("A21_DYNAMIC_RETRY_MODE_ALREADY_ENABLED")

    lifecycle = {
        "backup_ready": False,
        "canary_started": False,
        "finalized": False,
        "rollback_done": False,
        "timer_restored": False,
    }
    backup_root: Path | None = None
    db_backup: Path | None = None
    output_backups: dict[str, dict[str, Any]] = {}
    repo_backups: dict[Path, Path] = {}
    before_inventory: dict[str, Any] | None = None
    rollback_guard = load_module("a21_dynamic_rollback_guard", ROLLBACK_GUARD)
    if rollback_guard.POLICY_VERSION != ROLLBACK_POLICY:
        raise RuntimeError("A21_DYNAMIC_ROLLBACK_POLICY_MISMATCH")

    def rollback_and_restore(original_error: str) -> dict[str, Any]:
        nonlocal before_inventory
        if not lifecycle["backup_ready"] or before_inventory is None:
            return {
                "status": "NO_BACKUP_AVAILABLE",
                "original_error": original_error,
            }
        current = database_inventory(DB)
        before_uids = set(batch_map(before_inventory))
        current_uids = set(batch_map(current))
        new_uids = sorted(current_uids - before_uids)
        result: dict[str, Any] = {
            "status": "NO_NEW_BATCH",
            "original_error": original_error,
            "new_batch_uids": new_uids,
        }
        full_restore_required = False
        if len(new_uids) > 1:
            result = {
                "status": "MULTIPLE_NEW_BATCHES_FULL_RESTORE_REQUIRED",
                "original_error": original_error,
                "new_batch_uids": new_uids,
            }
            full_restore_required = True
        elif len(new_uids) == 1:
            new_uid = new_uids[0]
            if new_uid == baseline_uid:
                result = {
                    "status": "BASELINE_ROLLBACK_REFUSED",
                    "original_error": original_error,
                    "new_batch_uids": new_uids,
                }
                full_restore_required = True
            else:
                result = rollback_guard.rollback_committed_batch(
                    DB,
                    new_uid,
                    original_error=original_error,
                    archive_location="rollback://era55a21/dynamic-retry-failure",
                )
                try:
                    rollback_guard.require_success(result)
                except Exception as rollback_error:
                    result["require_success_error"] = (
                        f"{type(rollback_error).__name__}:{rollback_error}"
                    )
                    full_restore_required = True
        restore_mutable_outputs(output_backups)
        if full_restore_required:
            if db_backup is None:
                raise RuntimeError("A21_DYNAMIC_DATABASE_BACKUP_MISSING")
            restore_database_from_backup(db_backup)
            result["emergency_full_database_restore"] = True
        after_restore = database_inventory(DB)
        if after_restore != before_inventory:
            if db_backup is None:
                raise RuntimeError("A21_DYNAMIC_DATABASE_BACKUP_MISSING")
            restore_database_from_backup(db_backup)
            after_restore = database_inventory(DB)
            result["emergency_full_database_restore"] = True
        if after_restore != before_inventory:
            raise RuntimeError("A21_DYNAMIC_DATABASE_RESTORE_PARITY_FAILED")
        result["baseline_preserved"] = True
        result["database_after_restore"] = after_restore
        lifecycle["rollback_done"] = True
        return result

    def emergency_cleanup() -> None:
        try:
            remove_dropin()
        except Exception:
            pass
        if lifecycle["canary_started"] and not lifecycle["finalized"] and not lifecycle["rollback_done"]:
            try:
                run(["systemctl", "stop", SERVICE], check=False, timeout=30)
                rollback_and_restore("A21_DYNAMIC_EMERGENCY_CLEANUP")
            except Exception:
                pass
        if not lifecycle["timer_restored"]:
            try:
                restore_timer(timer_before)
                lifecycle["timer_restored"] = True
            except Exception:
                pass

    atexit.register(emergency_cleanup)

    try:
        run(["systemctl", "stop", TIMER], check=True, timeout=30)
        deadline = time.time() + 120
        while time.time() < deadline:
            current_service = systemctl_state(SERVICE)
            if current_service["active"] in {"inactive", "failed"}:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("A21_DYNAMIC_SERVICE_DID_NOT_BECOME_INACTIVE")
        run(["systemctl", "reset-failed", SERVICE], check=False, timeout=20)

        environment_before = service_environment()
        if environment_before["writer_enabled"] or environment_before["runner_lock_enabled"]:
            raise RuntimeError("A21_DYNAMIC_RUNTIME_FLAGS_ACTIVE_AFTER_TIMER_PAUSE")
        if environment_before["any_hot_override"] or environment_before["retry_mode_enabled"]:
            raise RuntimeError("A21_DYNAMIC_RUNTIME_OVERRIDE_ACTIVE_AFTER_TIMER_PAUSE")

        before_inventory = database_inventory(DB)
        before_map = batch_map(before_inventory)
        if before_inventory["batch_rows"] != 1 or before_inventory["ledger_rows"] != 106:
            raise RuntimeError("A21_DYNAMIC_BASELINE_DATABASE_COUNTS_DRIFT")
        if set(before_map) != {baseline_uid}:
            raise RuntimeError("A21_DYNAMIC_BASELINE_BATCH_UID_DRIFT")
        baseline_before = before_map[baseline_uid]
        if baseline_before["status"] != "COMMITTED":
            raise RuntimeError("A21_DYNAMIC_BASELINE_NOT_COMMITTED")
        if baseline_before["policy_version"] != LEDGER_POLICY:
            raise RuntimeError("A21_DYNAMIC_BASELINE_POLICY_MISMATCH")
        if baseline_before["ledger_rows"] != 106:
            raise RuntimeError("A21_DYNAMIC_BASELINE_LEDGER_COUNT_DRIFT")
        if before_inventory["integrity_check"] != "ok":
            raise RuntimeError("A21_DYNAMIC_BASELINE_INTEGRITY_FAILED")
        if before_inventory["quick_check"] != "ok":
            raise RuntimeError("A21_DYNAMIC_BASELINE_QUICK_CHECK_FAILED")
        if before_inventory["foreign_key_check_rows"] != 0:
            raise RuntimeError("A21_DYNAMIC_BASELINE_FOREIGN_KEY_FAILED")

        backup_root = Path(
            tempfile.mkdtemp(
                prefix="era55a21_dynamic_",
                dir="/dev/shm" if Path("/dev/shm").exists() else "/tmp",
            )
        )
        db_backup = backup_root / "production.sqlite"
        backup_sqlite(DB, db_backup)
        output_backups = backup_files(mutable_output_paths(), backup_root)
        repo_backups = backup_repo_state(backup_root)
        lifecycle["backup_ready"] = True

        RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
        for path in (
            RESULT_PATH,
            ERROR_PATH,
            INVOCATION_GUARD,
            ORDER_LOG,
            FULL_DISPLAY,
            WRITER_LOCK,
        ):
            if path.exists():
                path.unlink()

        token = hashlib.sha256(
            f"{EXPECTED_HEAD}:{time.time_ns()}:{os.getpid()}".encode("utf-8")
        ).hexdigest()[:32]
        started_epoch = int(time.time())
        started_at = utc_now()

        DROPIN_DIR.mkdir(parents=True, exist_ok=True)
        DROPIN.write_text(
            "\n".join(
                [
                    "[Service]",
                    'Environment="TOKENOSKOBI_LEDGER_WRITER_ENABLED=1"',
                    'Environment="TOKENOSKOBI_RUNNER_LOCK_ENABLED=1"',
                    f'Environment="TOKENOSKOBI_NEWS_HOT_PATH={SELF}"',
                    'Environment="TOKENOSKOBI_A21_DYNAMIC_RETRY=1"',
                    f'Environment="TOKENOSKOBI_A21_DYNAMIC_TOKEN={token}"',
                    f'Environment="TOKENOSKOBI_A21_DYNAMIC_EXPECTED_HEAD={EXPECTED_HEAD}"',
                    f'Environment="TOKENOSKOBI_A10_ORDER_LOG={ORDER_LOG}"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        run(["systemctl", "daemon-reload"], check=True, timeout=30)
        active_environment = service_environment()
        if not (
            active_environment["writer_enabled"]
            and active_environment["runner_lock_enabled"]
            and active_environment["hot_override_enabled"]
            and active_environment["retry_mode_enabled"]
        ):
            raise RuntimeError("A21_DYNAMIC_RUNTIME_DROPIN_NOT_ACTIVE")

        lifecycle["canary_started"] = True
        start = run(
            ["systemctl", "start", SERVICE],
            check=False,
            timeout=360,
        )
        service_start = {
            "rc": start.returncode,
            "stdout": start.stdout.strip(),
            "stderr": start.stderr.strip(),
        }
        if start.returncode != 0:
            detail = load(ERROR_PATH) if ERROR_PATH.exists() else None
            raise RuntimeError(
                "A21_DYNAMIC_SERVICE_START_FAILED:"
                + str(start.returncode)
                + ":"
                + json.dumps(detail, ensure_ascii=False, sort_keys=True)
                + ":"
                + start.stdout[-3000:]
                + start.stderr[-3000:]
            )

        deadline = time.time() + 300
        while time.time() < deadline:
            current_service = systemctl_state(SERVICE)
            if RESULT_PATH.exists() and current_service["active"] in {"inactive", "failed"}:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("A21_DYNAMIC_SERVICE_COMPLETION_TIMEOUT")

        after_service_environment = service_environment()
        if after_service_environment["result"] not in {"success", ""}:
            raise RuntimeError("A21_DYNAMIC_SERVICE_RESULT_NOT_SUCCESS")
        if after_service_environment["exec_main_status"] not in {"0", ""}:
            raise RuntimeError("A21_DYNAMIC_SERVICE_MAIN_STATUS_NOT_ZERO")
        if not RESULT_PATH.exists():
            raise RuntimeError("A21_DYNAMIC_ONE_SHOT_RESULT_MISSING")
        one_shot = load(RESULT_PATH)
        if one_shot.get("token") != token:
            raise RuntimeError("A21_DYNAMIC_ONE_SHOT_TOKEN_MISMATCH")
        if one_shot.get("status") != "OK_A21_DYNAMIC_IDENTITY_ONE_SHOT_COMPLETED":
            raise RuntimeError("A21_DYNAMIC_ONE_SHOT_STATUS_NOT_OK")

        actual_uid = str(one_shot["new_batch_uid"])
        source_count = int(one_shot["source_candidate_count"])
        source_accounted = int(one_shot["source_accounted"])
        if actual_uid == baseline_uid:
            raise RuntimeError("A21_DYNAMIC_RESULT_UID_EQUALS_BASELINE")
        if not (1 <= source_count <= MAX_SOURCE_ROWS):
            raise RuntimeError("A21_DYNAMIC_RESULT_SOURCE_BOUND_FAILED")
        if source_accounted != source_count:
            raise RuntimeError("A21_DYNAMIC_RESULT_SOURCE_ACCOUNTING_FAILED")
        if int(one_shot["unobservable_rows"]) != 0:
            raise RuntimeError("A21_DYNAMIC_RESULT_UNOBSERVABLE_ROWS_NONZERO")

        order = ORDER_LOG.read_text(encoding="utf-8").splitlines()
        required_markers = [
            "LOCK_ACQUIRED",
            "RAW_START",
            "RAW_END:0",
            "DERIVED_START",
            "DERIVED_END:0",
            "HOT_START",
            "A21_DYNAMIC_ONE_SHOT_START",
            "A21_DYNAMIC_ORIGINAL_HOT_END:0",
            "A21_DYNAMIC_LEDGER_WRITE_DONE:COMMITTED",
            "A21_DYNAMIC_PANEL_BRIDGE_END:0",
            "A21_DYNAMIC_ONE_SHOT_END:0",
            "HOT_END:0",
        ]
        positions: list[int] = []
        for marker in required_markers:
            if marker not in order:
                raise RuntimeError(f"A21_DYNAMIC_ORDER_MARKER_MISSING:{marker}")
            positions.append(order.index(marker))
        if positions != sorted(positions):
            raise RuntimeError("A21_DYNAMIC_ORDER_SEQUENCE_INVALID")
        if order.count("A21_DYNAMIC_ONE_SHOT_START") != 1:
            raise RuntimeError("A21_DYNAMIC_ONE_SHOT_INVOCATION_COUNT_INVALID")
        recovery_markers = [
            marker for marker in order if marker.startswith("RECOVERY_DONE:")
        ]
        if len(recovery_markers) != 1:
            raise RuntimeError("A21_DYNAMIC_RECOVERY_MARKER_COUNT_INVALID")
        if recovery_markers[0] not in {
            "RECOVERY_DONE:OUTPUT_ALREADY_MATCHED",
            "RECOVERY_DONE:RECOVERED",
        }:
            raise RuntimeError("A21_DYNAMIC_RECOVERY_MARKER_INVALID:" + recovery_markers[0])

        after_inventory = database_inventory(DB)
        after_map = batch_map(after_inventory)
        if after_inventory["batch_rows"] != 2:
            raise RuntimeError("A21_DYNAMIC_TOTAL_BATCH_COUNT_MISMATCH")
        if after_inventory["ledger_rows"] != 106 + source_count:
            raise RuntimeError("A21_DYNAMIC_TOTAL_LEDGER_COUNT_MISMATCH")
        if set(after_map) != {baseline_uid, actual_uid}:
            raise RuntimeError("A21_DYNAMIC_FINAL_BATCH_SET_INVALID")
        if after_map[baseline_uid] != baseline_before:
            raise RuntimeError("A21_DYNAMIC_BASELINE_BATCH_MUTATED")
        new_batch = after_map[actual_uid]
        if new_batch["status"] != "COMMITTED":
            raise RuntimeError("A21_DYNAMIC_NEW_BATCH_NOT_COMMITTED")
        if new_batch["policy_version"] != LEDGER_POLICY:
            raise RuntimeError("A21_DYNAMIC_NEW_BATCH_POLICY_MISMATCH")
        if new_batch["source_candidate_count"] != source_count:
            raise RuntimeError("A21_DYNAMIC_NEW_BATCH_SOURCE_COUNT_MISMATCH")
        if new_batch["ledger_rows"] != source_count:
            raise RuntimeError("A21_DYNAMIC_NEW_BATCH_LEDGER_COUNT_MISMATCH")
        if sum(new_batch["disposition_counts"].values()) != source_count:
            raise RuntimeError("A21_DYNAMIC_NEW_BATCH_DISPOSITION_ACCOUNTING_FAILED")
        if after_inventory["integrity_check"] != "ok":
            raise RuntimeError("A21_DYNAMIC_POST_INTEGRITY_FAILED")
        if after_inventory["quick_check"] != "ok":
            raise RuntimeError("A21_DYNAMIC_POST_QUICK_CHECK_FAILED")
        if after_inventory["foreign_key_check_rows"] != 0:
            raise RuntimeError("A21_DYNAMIC_POST_FOREIGN_KEY_FAILED")
        if sha(HOT) != sha(PANEL_HOT):
            raise RuntimeError("A21_DYNAMIC_FINAL_PANEL_HOT_HASH_MISMATCH")

        remove_dropin()
        environment_after_cleanup = service_environment()
        if environment_after_cleanup["writer_enabled"]:
            raise RuntimeError("A21_DYNAMIC_WRITER_FLAG_STILL_ENABLED")
        if environment_after_cleanup["runner_lock_enabled"]:
            raise RuntimeError("A21_DYNAMIC_LOCK_FLAG_STILL_ENABLED")
        if environment_after_cleanup["any_hot_override"]:
            raise RuntimeError("A21_DYNAMIC_HOT_OVERRIDE_STILL_ENABLED")
        if environment_after_cleanup["retry_mode_enabled"]:
            raise RuntimeError("A21_DYNAMIC_RETRY_MODE_STILL_ENABLED")
        if DROPIN.exists():
            raise RuntimeError("A21_DYNAMIC_DROPIN_STILL_PRESENT")
        timer_post_audit_paused = systemctl_state(TIMER)
        if timer_post_audit_paused["active"] != "inactive":
            raise RuntimeError("A21_DYNAMIC_TIMER_NOT_PAUSED_DURING_POST_AUDIT")

        journal = run(
            [
                "journalctl",
                "-u",
                SERVICE,
                "--since",
                f"@{started_epoch}",
                "--no-pager",
                "-o",
                "cat",
            ],
            check=False,
            timeout=30,
        )

        restore_timer(timer_before)
        lifecycle["timer_restored"] = True
        timer_after = systemctl_state(TIMER)
        if timer_after["active"] != timer_before["active"]:
            raise RuntimeError("A21_DYNAMIC_TIMER_ACTIVE_STATE_NOT_RESTORED")
        if timer_after["enabled"] != timer_before["enabled"]:
            raise RuntimeError("A21_DYNAMIC_TIMER_ENABLED_STATE_CHANGED")

        finished_at = utc_now()
        artifact = {
            "schema_version": "1.0",
            "work_unit": WORK_UNIT,
            "timestamp_utc": finished_at,
            "status": "CLOSED_POST_REMEDIATION_DYNAMIC_IDENTITY_SINGLE_CYCLE_CANARY_OK",
            "result": RESULT,
            "authorization_source": str(A20R.relative_to(ROOT)),
            "authorization_correction": {
                "precomputed_uid_advisory_only": True,
                "dynamic_uid_computed_after_original_hot": True,
                "failed_prewrite_attempt_consumed_authorization": False,
                "retry_consumed_authorization": True,
            },
            "canary_token": token,
            "canary_started_at_utc": started_at,
            "canary_finished_at_utc": finished_at,
            "service_start": service_start,
            "runner_order": order,
            "runner_order_valid": True,
            "runner_recovery_marker": recovery_markers[0],
            "one_shot_result": one_shot,
            "production_before": before_inventory,
            "production_after": after_inventory,
            "baseline_batch": baseline_before,
            "new_batch": new_batch,
            "baseline_batch_preserved": True,
            "new_batch_only": True,
            "bounded_dynamic_identity": {
                "baseline_batch_uid": baseline_uid,
                "actual_new_batch_uid": actual_uid,
                "new_batch_uid_distinct": actual_uid != baseline_uid,
                "minimum_source_rows": 1,
                "maximum_source_rows": MAX_SOURCE_ROWS,
                "actual_source_rows": source_count,
                "source_accounted": source_accounted,
                "unobservable_rows": 0,
            },
            "timer_before": timer_before,
            "timer_post_audit_paused": timer_post_audit_paused,
            "timer_after": timer_after,
            "service_initial": service_initial,
            "service_environment_after_cleanup": environment_after_cleanup,
            "runtime_cleanup": {
                "dropin_removed": not DROPIN.exists(),
                "writer_flag_disabled": not environment_after_cleanup["writer_enabled"],
                "runner_lock_flag_disabled": not environment_after_cleanup["runner_lock_enabled"],
                "hot_override_disabled": not environment_after_cleanup["any_hot_override"],
                "retry_mode_disabled": not environment_after_cleanup["retry_mode_enabled"],
                "timer_state_restored": timer_after == timer_before,
            },
            "output_post_audit": {
                "hot_output": file_state(HOT),
                "panel_hot": file_state(PANEL_HOT),
                "hot_panel_hash_match": sha(HOT) == sha(PANEL_HOT),
                "bridge_state": file_state(BRIDGE_STATE),
                "bridge_decision": load(BRIDGE_STATE)["decision"],
                "exact_legacy_object_parity": one_shot["exact_legacy_object_parity"],
                "exact_legacy_uid_order_parity": one_shot["exact_legacy_uid_order_parity"],
            },
            "database_post_audit": {
                "expected_total_batch_rows": 2,
                "actual_total_batch_rows": after_inventory["batch_rows"],
                "expected_total_ledger_rows": 106 + source_count,
                "actual_total_ledger_rows": after_inventory["ledger_rows"],
                "new_batch_source_rows": source_count,
                "new_batch_ledger_rows": new_batch["ledger_rows"],
                "all_new_source_rows_accounted": True,
                "integrity_check": after_inventory["integrity_check"],
                "quick_check": after_inventory["quick_check"],
                "foreign_key_check_rows": after_inventory["foreign_key_check_rows"],
            },
            "rollback_protection": {
                "policy_version": ROLLBACK_POLICY,
                "guard_path": str(ROLLBACK_GUARD.relative_to(ROOT)),
                "guard_sha256": sha(ROLLBACK_GUARD),
                "armed": True,
                "triggered": False,
                "scope": "NEW_DYNAMIC_RETRY_BATCH_ONLY",
                "baseline_batch_uid": baseline_uid,
            },
            "journal_excerpt": {
                "rc": journal.returncode,
                "stdout_tail": journal.stdout[-12000:],
                "stderr_tail": journal.stderr[-3000:],
            },
            "authorization": {
                "one_post_remediation_production_canary_retry_authorized": False,
                "one_post_remediation_production_canary_retry_consumed": True,
                "new_production_canary_authorized": False,
                "additional_canary_authorized": False,
                "general_production_writer_activation_authorized": False,
                "production_writer_active": False,
                "p0_f1_closed": False,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
            },
            "next_safe_step": NEXT,
        }
        atomic_dump(ARTIFACT, artifact)

        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            f"""# ERA55A21 Dynamic-Identity Post-Remediation Production Canary

- Status: `CLOSED_POST_REMEDIATION_DYNAMIC_IDENTITY_SINGLE_CYCLE_CANARY_OK`
- Result: `{RESULT}`
- Failed pre-write attempt consumed authorization: `false`
- Dynamic retry consumed authorization: `true`
- Baseline batch UID: `{baseline_uid}`
- Baseline batch preserved: `true`
- New batch UID: `{actual_uid}`
- New batch UID distinct: `true`
- New source candidates: `{source_count}`
- New source accounted: `{source_accounted}`
- Total batch rows: `2`
- Total ledger rows: `{106 + source_count}`
- Unobservable rows: `0`
- Runner order HOT_END:0: `true`
- Panel hot hash parity: `true`
- Runtime drop-in removed: `true`
- Timer state restored: `true`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Option B authorized: `false`
- Next safe step: `{NEXT}`
""",
            encoding="utf-8",
        )

        runtime = load(RUNTIME)
        current = runtime["current_state"]
        current.update(
            {
                "mode": "ERA55A21_DYNAMIC_IDENTITY_SINGLE_CYCLE_CANARY_COMPLETED",
                "runtime_status": "WORK_UNIT_CLOSED",
                "updated_at": finished_at,
                "last_action": {
                    "timestamp": finished_at,
                    "task": WORK_UNIT,
                    "result": RESULT,
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                },
                "active_work_unit": {
                    "id": WORK_UNIT,
                    "type": "ERA55_P0_DYNAMIC_IDENTITY_SINGLE_CYCLE_CANARY_APPLY_POST_AUDIT",
                    "parent": "ERA55_RUNTIME_OPTIMIZATION",
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "status": artifact["status"],
                    "result": RESULT,
                    "production_mutation": True,
                    "next_step": NEXT,
                },
                "next_safe_step": {
                    "id": NEXT,
                    "type": "ERA55_P0_POST_REMEDIATION_CANARY_RED_TEAM_GENERAL_ACTIVATION_DECISION",
                    "parent": "ERA55_RUNTIME_OPTIMIZATION",
                    "purpose": (
                        "Review the successful dynamic-identity canary and decide general "
                        "production writer activation separately."
                    ),
                    "human_authorization_required": True,
                    "new_production_canary_authorized": False,
                    "general_production_writer_activation_authorized": False,
                    "option_b_authorized": False,
                    "optimization_apply_authorized": False,
                    "status": "READY",
                },
                "current_problem": {
                    "code": "GENERAL_PRODUCTION_WRITER_ACTIVATION_NOT_AUTHORIZED",
                    "severity": "P0",
                    "evidence": str(ARTIFACT.relative_to(ROOT)),
                },
            }
        )
        runtime["current_work_unit"] = current["active_work_unit"]
        atomic_dump(RUNTIME, runtime)

        history = load(HISTORY)
        events = history.setdefault("events", [])
        event_id = "ERA55A21_DYNAMIC_IDENTITY_SINGLE_CYCLE_CANARY_V2"
        if not any(
            isinstance(event, dict) and event.get("event_id") == event_id
            for event in events
        ):
            events.append(
                {
                    "event_id": event_id,
                    "timestamp_utc": finished_at,
                    "era": "ERA55",
                    "work_unit": WORK_UNIT,
                    "event": "DYNAMIC_IDENTITY_POST_REMEDIATION_SINGLE_CYCLE_CANARY",
                    "status": artifact["status"],
                    "result": RESULT,
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "baseline_batch_uid": baseline_uid,
                    "baseline_batch_preserved": True,
                    "new_batch_uid": actual_uid,
                    "new_batch_source_rows": source_count,
                    "new_batch_ledger_rows": source_accounted,
                    "total_batch_rows": 2,
                    "total_ledger_rows": 106 + source_count,
                    "unobservable_rows": 0,
                    "runner_hot_end_zero": True,
                    "panel_hash_parity": True,
                    "runtime_overrides_removed": True,
                    "timer_state_restored": True,
                    "general_production_activation_authorized": False,
                    "p0_f1_closed": False,
                    "option_b_authorized": False,
                    "next_safe_step": NEXT,
                }
            )
        history["updated_at"] = finished_at
        history["updated_at_utc"] = finished_at
        atomic_dump(HISTORY, history)

        master = MASTER.read_text(encoding="utf-8")
        master = replace_section(
            master,
            "## 01 PROJECT STATUS",
            """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_P0_POST_REMEDIATION_CANARY_DECISION_PENDING
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
CURRENT_STAGE=ERA55A_P0_POST_REMEDIATION_CANARY_DECISION
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
BASELINE_BATCH_UID={baseline_uid}
BASELINE_BATCH_PRESERVED=true
NEW_BATCH_UID={actual_uid}
NEW_SOURCE_CANDIDATES={source_count}
NEW_SOURCE_ACCOUNTED={source_accounted}
PRODUCTION_BATCH_ROWS=2
PRODUCTION_LEDGER_ROWS={106 + source_count}
UNOBSERVABLE_ROWS=0
RUNNER_HOT_END_ZERO=true
PANEL_HOT_HASH_PARITY=true
DYNAMIC_RETRY_CONSUMED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

The bounded dynamic-identity canary completed once. General activation remains blocked.""",
        )
        master = replace_section(
            master,
            "## 03 LAST VERIFIED WORK",
            f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
PRODUCTION_MUTATION=true
RUNTIME_OVERRIDE_ACTIVE=false
```

NEXT_SAFE_STEP={NEXT}""",
        )
        MASTER.write_text(master, encoding="utf-8")

        handoff = HANDOFF.read_text(encoding="utf-8")
        handoff = replace_section(
            handoff,
            "## 02 CURRENT CONTINUATION CHECKPOINT",
            f"""PROJECT_STATUS=ACTIVE_ERA55_P0_POST_REMEDIATION_CANARY_DECISION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_POST_REMEDIATION_CANARY_DECISION
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
BASELINE_BATCH_UID={baseline_uid}
BASELINE_BATCH_PRESERVED=true
NEW_BATCH_UID={actual_uid}
NEW_SOURCE_CANDIDATES={source_count}
NEW_SOURCE_ACCOUNTED={source_accounted}
PRODUCTION_BATCH_ROWS=2
PRODUCTION_LEDGER_ROWS={106 + source_count}
UNOBSERVABLE_ROWS=0
RUNNER_HOT_END_ZERO=true
PANEL_HOT_HASH_PARITY=true
DYNAMIC_RETRY_CONSUMED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
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
PRODUCTION_MUTATION=true
RUNTIME_OVERRIDE_ACTIVE=false
CURRENT_PROBLEM=GENERAL_PRODUCTION_WRITER_ACTIVATION_NOT_AUTHORIZED""",
        )
        handoff = replace_section(
            handoff,
            "## 06 DO NOT REOPEN OR REPEAT",
            """- Do not rerun A9-A21 unless evidence is invalidated.
- Do not execute another production canary.
- Do not enable the production writer generally before A22.
- Do not delete either valid production batch.
- Do not start Option B or close P0 F1.""",
        )
        handoff = replace_section(
            handoff,
            "## 07 ALLOWED NEXT DECISIONS",
            f"""- Dynamic-identity production canary: `COMPLETED_AND_CONSUMED`.
- Baseline batch: `PRESERVED`.
- New batch accounting: `COMPLETE`.
- General production activation: `BLOCKED_PENDING_A22`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
        )
        handoff = replace_section(
            handoff,
            "## 08 NEXT SESSION EXECUTION RULE",
            """1. Confirm A22 is current.
2. Independently audit baseline preservation, dynamic new-batch accounting and runtime cleanup.
3. Decide general production writer activation separately.
4. Do not run another canary.
5. Keep Option B blocked until the production decision is sealed.""",
        )
        HANDOFF.write_text(handoff, encoding="utf-8")

        almanac = ALMANAC.read_text(encoding="utf-8")
        marker = "## ERA55A_21 DYNAMIC-IDENTITY POST-REMEDIATION CANARY"
        if marker not in almanac:
            ALMANAC.write_text(
                almanac.rstrip()
                + f"""

---

{marker}

- Status: `CLOSED_POST_REMEDIATION_DYNAMIC_IDENTITY_SINGLE_CYCLE_CANARY_OK`
- Result: `{RESULT}`
- Baseline batch preserved: `true`
- New batch UID: `{actual_uid}`
- New source rows: `{source_count}`
- Total batch rows: `2`
- Total ledger rows: `{106 + source_count}`
- Runner HOT_END:0: `true`
- Panel hot hash parity: `true`
- Runtime overrides removed: `true`
- Timer state restored: `true`
- General production activation authorized: `false`
- P0 F1 closed: `false`
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
            raise RuntimeError("A21_DYNAMIC_NO_STAGED_CHANGES")
        git("commit", "-m", SUBJECT)
        lifecycle["finalized"] = True
        atexit.unregister(emergency_cleanup)

        print("ERA55A21_DYNAMIC_IDENTITY_CANARY=SUCCESS")
        print("RESULT=" + RESULT)
        print("FAILED_PREWRITE_ATTEMPT_CONSUMED_AUTHORIZATION=false")
        print("DYNAMIC_RETRY_CONSUMED_AUTHORIZATION=true")
        print("BASELINE_BATCH_UID=" + baseline_uid)
        print("BASELINE_BATCH_PRESERVED=true")
        print("NEW_BATCH_UID=" + actual_uid)
        print("NEW_BATCH_UID_DISTINCT=true")
        print("NEW_SOURCE_CANDIDATES=" + str(source_count))
        print("NEW_SOURCE_ACCOUNTED=" + str(source_accounted))
        print("UNOBSERVABLE_ROWS=0")
        print("PRODUCTION_BATCH_ROWS=2")
        print("PRODUCTION_LEDGER_ROWS=" + str(106 + source_count))
        print("RUNNER_HOT_END_ZERO=true")
        print("PANEL_HOT_HASH_PARITY=true")
        print("RUNTIME_DROPIN_REMOVED=true")
        print("TIMER_STATE_RESTORED=true")
        print("ROLLBACK_GUARD_ARMED=true")
        print("ROLLBACK_TRIGGERED=false")
        print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
        print("PRODUCTION_WRITER_ACTIVE=false")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print("NEXT_SAFE_STEP=" + NEXT)
        print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
        return 0
    except Exception as exc:
        original_error = f"{type(exc).__name__}:{exc}"
        try:
            remove_dropin()
        except Exception:
            pass
        rollback_result: dict[str, Any]
        if lifecycle["canary_started"]:
            rollback_result = rollback_and_restore(original_error)
        else:
            rollback_result = {
                "status": "CANARY_NOT_STARTED",
                "original_error": original_error,
            }
        if repo_backups:
            restore_repo_state(repo_backups)
        if not lifecycle["timer_restored"]:
            restore_timer(timer_before)
            lifecycle["timer_restored"] = True
        lifecycle["rollback_done"] = True
        atexit.unregister(emergency_cleanup)
        print("A21_DYNAMIC_FAILURE=" + original_error, file=sys.stderr)
        print(
            "A21_DYNAMIC_ROLLBACK="
            + json.dumps(rollback_result, ensure_ascii=False, sort_keys=True),
            file=sys.stderr,
        )
        raise RuntimeError(
            "A21_DYNAMIC_CANARY_FAILED:"
            + original_error
            + ":ROLLBACK_STATUS:"
            + str(rollback_result.get("status"))
        ) from exc
    finally:
        if backup_root is not None and lifecycle["finalized"]:
            shutil.rmtree(backup_root, ignore_errors=True)
        if lifecycle["finalized"]:
            for path in (
                RESULT_PATH,
                ERROR_PATH,
                INVOCATION_GUARD,
                ORDER_LOG,
                FULL_DISPLAY,
                WRITER_LOCK,
            ):
                if path.exists():
                    path.unlink()


def main() -> int:
    if os.environ.get("TOKENOSKOBI_A21_DYNAMIC_RETRY", "0").strip() == "1":
        return one_shot_hot()
    return orchestrate()


if __name__ == "__main__":
    raise SystemExit(main())
