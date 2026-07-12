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

WORK_UNIT = "ERA55A_23_P0_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_APPLY_AND_POST_AUDIT"
RESULT = "OK_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_ACTIVE"
NEXT = "ERA55A_24_P0_POST_ACTIVATION_OBSERVATION_AND_P0_F1_CLOSURE_DECISION"
SUBJECT = "ERA55A23_GUARDED_PRODUCTION_WRITER | OK | ACTIVE_POST_AUDIT"
LEDGER_POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"
ROLLBACK_POLICY = "POSTCOMMIT_ARCHIVE_TRIGGER_ROLLBACK_GUARD_V1"
MAX_SOURCE_ROWS = 5000
QUEUE_CAPACITY = 50

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

A22 = ROOT / "data/control/era55a22_p0_post_remediation_canary_red_team_general_production_activation_decision_v1.json"
ARTIFACT = ROOT / "data/control/era55a23_p0_guarded_general_production_writer_runtime_integration_apply_and_post_audit_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A23_P0_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_APPLY_AND_POST_AUDIT.md"

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
GUARDED_STATE = ROOT / "runtime/state/news_guarded_production_writer_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

RUNTIME_ROOT = Path("/run/tokenoskobi")
DROPIN_DIR = Path("/etc/systemd/system") / f"{SERVICE}.d"
DROPIN = DROPIN_DIR / "90-era55a23-guarded-production.conf"
RESULT_PATH = RUNTIME_ROOT / "era55a23_guarded_result.json"
ERROR_PATH = RUNTIME_ROOT / "era55a23_guarded_error.json"
ORDER_LOG = RUNTIME_ROOT / "era55a23_guarded_order.log"
FULL_DISPLAY = RUNTIME_ROOT / "era55a23_guarded_full_candidate_display.json"
WRITER_LOCK = RUNTIME_ROOT / "era55a23_guarded_writer.lock"


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


def restore_database_from_backup(backup: Path) -> None:
    for suffix in ("-wal", "-shm"):
        candidate = Path(str(DB) + suffix)
        if candidate.exists():
            candidate.unlink()
    temp = DB.parent / ("." + DB.name + ".a23restore")
    shutil.copy2(backup, temp)
    os.replace(temp, DB)


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
        "guarded_mode_enabled": "TOKENOSKOBI_A23_GUARDED_PRODUCTION=1" in text,
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


def managed_output_paths() -> list[Path]:
    return [
        SUMMARY,
        HOT,
        RECOVERY_STATE,
        BRIDGE_STATE,
        GUARDED_STATE,
        PANEL_HOT,
    ]


def backup_files(paths: list[Path], backup_root: Path) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for index, path in enumerate(paths):
        relative = str(path.relative_to(ROOT))
        item: dict[str, Any] = {
            "path": path,
            "exists": path.exists(),
            "state": file_state(path),
        }
        if path.exists():
            backup = backup_root / "files" / f"{index:04d}.backup"
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
            item["backup"] = backup
        metadata[relative] = item
    return metadata


def restore_managed_outputs(metadata: dict[str, dict[str, Any]]) -> None:
    for item in metadata.values():
        path = Path(item["path"])
        if item["exists"]:
            backup = Path(item["backup"])
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.parent / ("." + path.name + ".a23restore")
            shutil.copy2(backup, temp)
            os.replace(temp, path)
        elif path.exists():
            path.unlink()


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


def remove_persistent_dropin() -> None:
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


def record_cycle_error(payload: dict[str, Any]) -> None:
    try:
        atomic_dump(ERROR_PATH, payload)
        atomic_dump(GUARDED_STATE, payload)
    except Exception:
        pass


def guarded_production_hot() -> int:
    cycle_started = utc_now()
    cycle_backup_root: Path | None = None
    before_inventory: dict[str, Any] | None = None
    before_outputs: dict[str, dict[str, Any]] = {}
    db_backup: Path | None = None
    actual_uid: str | None = None
    writer_status: str | None = None
    rollback_result: dict[str, Any] | None = None
    try:
        if os.environ.get("TOKENOSKOBI_LEDGER_WRITER_ENABLED", "0").strip() != "1":
            raise RuntimeError("A23_WRITER_FLAG_NOT_ENABLED")
        if os.environ.get("TOKENOSKOBI_RUNNER_LOCK_ENABLED", "0").strip() != "1":
            raise RuntimeError("A23_RUNNER_LOCK_FLAG_NOT_ENABLED")

        append_order("A23_GUARDED_HOT_START")
        before_inventory = database_inventory(DB)
        before_map = batch_map(before_inventory)
        before_uids = set(before_map)
        if not before_uids:
            raise RuntimeError("A23_NO_EXISTING_COMMITTED_BATCHES")
        if any(batch["status"] != "COMMITTED" for batch in before_map.values()):
            raise RuntimeError("A23_EXISTING_BATCH_NOT_COMMITTED")
        if before_inventory["integrity_check"] != "ok":
            raise RuntimeError("A23_PRE_CYCLE_INTEGRITY_FAILED")
        if before_inventory["quick_check"] != "ok":
            raise RuntimeError("A23_PRE_CYCLE_QUICK_CHECK_FAILED")
        if before_inventory["foreign_key_check_rows"] != 0:
            raise RuntimeError("A23_PRE_CYCLE_FOREIGN_KEY_FAILED")

        cycle_backup_root = Path(
            tempfile.mkdtemp(
                prefix="era55a23_cycle_",
                dir="/dev/shm" if Path("/dev/shm").exists() else "/tmp",
            )
        )
        db_backup = cycle_backup_root / "production.sqlite"
        backup_sqlite(DB, db_backup)
        before_outputs = backup_files(managed_output_paths(), cycle_backup_root)

        original = run(
            [sys.executable, str(ORIGINAL_HOT), "--runtime-refresh"],
            check=False,
            timeout=180,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        append_order(f"A23_GUARDED_ORIGINAL_HOT_END:{original.returncode}")
        if original.returncode != 0:
            raise RuntimeError(
                "A23_ORIGINAL_HOT_FAILED:"
                + str(original.returncode)
                + ":"
                + original.stderr[-3000:]
            )

        legacy_contract = load(HOT)
        legacy_queue = legacy_contract.get("hot_queue")
        if not isinstance(legacy_queue, list):
            raise RuntimeError("A23_LEGACY_HOT_QUEUE_NOT_LIST")
        if not (0 < len(legacy_queue) <= QUEUE_CAPACITY):
            raise RuntimeError("A23_LEGACY_QUEUE_BOUND_FAILED")

        tools_path = str(ROOT / "tools")
        if tools_path not in sys.path:
            sys.path.insert(0, tools_path)
        extractor = load_module("a23_extractor", EXTRACTOR)
        adapter = load_module("a23_adapter", ADAPTER)
        rollback_guard = load_module("a23_rollback_guard", ROLLBACK_GUARD)
        if adapter.POLICY_VERSION != LEDGER_POLICY:
            raise RuntimeError("A23_LEDGER_POLICY_MISMATCH")
        if rollback_guard.POLICY_VERSION != ROLLBACK_POLICY:
            raise RuntimeError("A23_ROLLBACK_POLICY_MISMATCH")

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
        if not (1 <= source_count <= MAX_SOURCE_ROWS):
            raise RuntimeError("A23_SOURCE_BOUND_FAILED")
        if accounted != source_count:
            raise RuntimeError("A23_SOURCE_ACCOUNTING_FAILED")
        if int(counts["admitted_count"]) != len(legacy_queue):
            raise RuntimeError("A23_ADMITTED_COUNT_PARITY_FAILED")

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
        append_order("A23_GUARDED_LEDGER_WRITE_DONE:" + writer_status)
        if writer_status not in {"COMMITTED", "IDEMPOTENT_REPLAY_NOOP"}:
            raise RuntimeError("A23_LEDGER_WRITE_STATUS_INVALID:" + writer_status)

        final_queue = load(HOT).get("hot_queue")
        if canonical(final_queue) != canonical(legacy_queue):
            raise RuntimeError("A23_FINAL_QUEUE_PARITY_FAILED")

        bridge = run(
            [sys.executable, str(PANEL_BRIDGE)],
            check=False,
            timeout=120,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        append_order(f"A23_GUARDED_PANEL_BRIDGE_END:{bridge.returncode}")
        if bridge.returncode != 0:
            raise RuntimeError(
                "A23_PANEL_BRIDGE_FAILED:"
                + str(bridge.returncode)
                + ":"
                + bridge.stdout[-3000:]
                + bridge.stderr[-3000:]
            )
        bridge_state = load(BRIDGE_STATE)
        if bridge_state.get("decision") != "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED":
            raise RuntimeError("A23_PANEL_BRIDGE_DECISION_NOT_OK")
        hash_match = bridge_state.get("hash_match")
        if not isinstance(hash_match, dict) or not hash_match or not all(
            value is True for value in hash_match.values()
        ):
            raise RuntimeError("A23_PANEL_BRIDGE_HASH_MISMATCH")
        if sha(HOT) != sha(PANEL_HOT):
            raise RuntimeError("A23_PANEL_HOT_HASH_MISMATCH")

        after_inventory = database_inventory(DB)
        after_map = batch_map(after_inventory)
        if any(after_map[uid] != before_map[uid] for uid in before_uids):
            raise RuntimeError("A23_EXISTING_BATCH_MUTATED")

        new_uids = sorted(set(after_map) - before_uids)
        if writer_status == "COMMITTED":
            if new_uids != [actual_uid]:
                raise RuntimeError("A23_COMMITTED_NEW_BATCH_SET_INVALID")
            new_batch = after_map[actual_uid]
            if new_batch["status"] != "COMMITTED":
                raise RuntimeError("A23_NEW_BATCH_NOT_COMMITTED")
            if new_batch["policy_version"] != LEDGER_POLICY:
                raise RuntimeError("A23_NEW_BATCH_POLICY_MISMATCH")
            if new_batch["source_candidate_count"] != source_count:
                raise RuntimeError("A23_NEW_BATCH_SOURCE_COUNT_MISMATCH")
            if new_batch["ledger_rows"] != source_count:
                raise RuntimeError("A23_NEW_BATCH_LEDGER_COUNT_MISMATCH")
            if sum(new_batch["disposition_counts"].values()) != source_count:
                raise RuntimeError("A23_NEW_BATCH_ACCOUNTING_FAILED")
        else:
            if new_uids:
                raise RuntimeError("A23_IDEMPOTENT_REPLAY_CREATED_NEW_BATCH")
            if actual_uid not in before_uids:
                raise RuntimeError("A23_IDEMPOTENT_REPLAY_UID_NOT_EXISTING")
            new_batch = after_map[actual_uid]

        if after_inventory["integrity_check"] != "ok":
            raise RuntimeError("A23_POST_CYCLE_INTEGRITY_FAILED")
        if after_inventory["quick_check"] != "ok":
            raise RuntimeError("A23_POST_CYCLE_QUICK_CHECK_FAILED")
        if after_inventory["foreign_key_check_rows"] != 0:
            raise RuntimeError("A23_POST_CYCLE_FOREIGN_KEY_FAILED")

        payload = {
            "schema_version": "1.0",
            "status": "OK_A23_GUARDED_PRODUCTION_CYCLE_COMPLETED",
            "timestamp_utc": utc_now(),
            "cycle_started_at_utc": cycle_started,
            "writer_status": writer_status,
            "publish_status": writer_result["publish_result"]["status"],
            "original_hot_rc": original.returncode,
            "bridge_rc": bridge.returncode,
            "bridge_decision": bridge_state["decision"],
            "bridge_hash_match_all": True,
            "actual_batch_uid": actual_uid,
            "batch_uid_preexisting": actual_uid in before_uids,
            "new_batch_committed": writer_status == "COMMITTED",
            "source_candidate_count": source_count,
            "source_accounted": accounted,
            "unobservable_rows": source_count - accounted,
            "legacy_queue_count": len(legacy_queue),
            "exact_legacy_object_parity": True,
            "exact_legacy_uid_order_parity": True,
            "existing_batch_uids_before": sorted(before_uids),
            "existing_batches_preserved": True,
            "new_batch_uids": new_uids,
            "batch_rows_before": before_inventory["batch_rows"],
            "batch_rows_after": after_inventory["batch_rows"],
            "ledger_rows_before": before_inventory["ledger_rows"],
            "ledger_rows_after": after_inventory["ledger_rows"],
            "active_batch": new_batch,
            "hot_output_sha256": sha(HOT),
            "panel_hot_sha256": sha(PANEL_HOT),
            "rollback_guard": {
                "policy_version": ROLLBACK_POLICY,
                "armed": True,
                "triggered": False,
                "scope": "NEW_CURRENT_CYCLE_BATCH_ONLY",
            },
        }
        atomic_dump(RESULT_PATH, payload)
        atomic_dump(GUARDED_STATE, payload)
        if ERROR_PATH.exists():
            ERROR_PATH.unlink()
        append_order("A23_GUARDED_HOT_END:0")
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
        return 0
    except Exception as exc:
        original_error = f"{type(exc).__name__}:{exc}"
        emergency_restore = False
        try:
            if before_inventory is not None:
                before_map = batch_map(before_inventory)
                before_uids = set(before_map)
                current = database_inventory(DB)
                current_map = batch_map(current)
                if actual_uid and actual_uid not in before_uids and actual_uid in current_map:
                    rollback_guard = load_module("a23_failure_rollback_guard", ROLLBACK_GUARD)
                    rollback_result = rollback_guard.rollback_committed_batch(
                        DB,
                        actual_uid,
                        original_error=original_error,
                        archive_location="rollback://era55a23/guarded-production-failure",
                    )
                    try:
                        rollback_guard.require_success(rollback_result)
                    except Exception as rollback_error:
                        rollback_result["require_success_error"] = (
                            f"{type(rollback_error).__name__}:{rollback_error}"
                        )
                after_rollback = database_inventory(DB)
                if after_rollback != before_inventory:
                    if db_backup is None:
                        raise RuntimeError("A23_CYCLE_DATABASE_BACKUP_MISSING")
                    restore_database_from_backup(db_backup)
                    emergency_restore = True
                if database_inventory(DB) != before_inventory:
                    raise RuntimeError("A23_CYCLE_DATABASE_RESTORE_PARITY_FAILED")
            if before_outputs:
                restore_managed_outputs(before_outputs)
        except Exception as restore_error:
            original_error += (
                ":RESTORE_ERROR:"
                + f"{type(restore_error).__name__}:{restore_error}"
            )
        payload = {
            "schema_version": "1.0",
            "status": "A23_GUARDED_PRODUCTION_CYCLE_FAILED",
            "timestamp_utc": utc_now(),
            "cycle_started_at_utc": cycle_started,
            "error": original_error,
            "actual_batch_uid": actual_uid,
            "writer_status": writer_status,
            "rollback_result": rollback_result,
            "emergency_database_restore": emergency_restore,
            "outputs_restored": bool(before_outputs),
        }
        record_cycle_error(payload)
        append_order("A23_GUARDED_HOT_END:1")
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), file=sys.stderr, flush=True)
        return 1
    finally:
        if cycle_backup_root is not None:
            shutil.rmtree(cycle_backup_root, ignore_errors=True)
        if WRITER_LOCK.exists():
            WRITER_LOCK.unlink()


def verify_authorization() -> dict[str, Any]:
    a22 = load(A22)
    assert a22["status"] == "CLOSED_GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY_AUTHORIZED"
    assert a22["result"] == "OK_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVATION_APPLY_AUTHORIZED"
    authorization = a22["authorization"]
    assert authorization["guarded_general_production_writer_activation_apply_authorized"] is True
    assert authorization["general_production_writer_activation_authorized"] is True
    assert authorization["production_writer_active"] is False
    assert authorization["activation_apply_completed"] is False
    assert authorization["additional_canary_authorized"] is False
    contract = a22["activation_apply_contract"]
    assert contract["apply_work_unit"] == WORK_UNIT
    assert contract["persistent_runtime_integration_required"] is True
    assert contract["one_shot_canary_wrapper_forbidden"] is True
    assert contract["bounded_dynamic_batch_identity_required"] is True
    assert contract["batch_uid_computed_after_natural_refresh"] is True
    assert contract["source_candidate_minimum"] == 1
    assert contract["source_candidate_maximum"] == MAX_SOURCE_ROWS
    assert contract["complete_source_accounting_required"] is True
    assert contract["unobservable_rows_must_equal"] == 0
    assert contract["queue_capacity"] == QUEUE_CAPACITY
    assert contract["exact_legacy_object_parity_required"] is True
    assert contract["exact_legacy_uid_order_parity_required"] is True
    assert contract["runner_lock_required"] is True
    assert contract["postcommit_rollback_guard_policy"] == ROLLBACK_POLICY
    assert contract["rollback_scope_new_batch_only"] is True
    assert contract["all_existing_committed_batches_must_be_preserved"] is True
    assert contract["single_controlled_post_apply_service_cycle_required"] is True
    assert contract["post_apply_cycle_must_end_hot_end_zero"] is True
    assert contract["permanent_writer_enablement_allowed_only_after_post_audit"] is True
    assert contract["additional_canary_allowed"] is False
    assert contract["p0_f1_close_allowed_during_a23"] is False
    return a22


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
        A22,
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
        RECOVERY_STATE,
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
        raise RuntimeError("A23_ARTIFACT_ALREADY_EXISTS")
    if DROPIN.exists():
        raise RuntimeError("A23_PERSISTENT_DROPIN_ALREADY_EXISTS")

    a22 = verify_authorization()
    timer_before = systemctl_state(TIMER)
    service_initial = systemctl_state(SERVICE)
    environment_initial = service_environment()
    if timer_before["active"] != "active" or timer_before["enabled"] != "enabled":
        raise RuntimeError("A23_TIMER_PRECONDITION_FAILED")
    if environment_initial["writer_enabled"]:
        raise RuntimeError("A23_WRITER_ALREADY_ENABLED")
    if environment_initial["runner_lock_enabled"]:
        raise RuntimeError("A23_RUNNER_LOCK_ALREADY_ENABLED")
    if environment_initial["any_hot_override"]:
        raise RuntimeError("A23_HOT_OVERRIDE_ALREADY_ENABLED")
    if environment_initial["guarded_mode_enabled"]:
        raise RuntimeError("A23_GUARDED_MODE_ALREADY_ENABLED")

    lifecycle = {
        "backup_ready": False,
        "dropin_installed": False,
        "cycle_started": False,
        "finalized": False,
        "timer_restored": False,
    }
    backup_root: Path | None = None
    db_backup: Path | None = None
    output_backups: dict[str, dict[str, Any]] = {}
    repo_backups: dict[Path, Path] = {}
    before_inventory: dict[str, Any] | None = None

    def emergency_cleanup() -> None:
        try:
            run(["systemctl", "stop", TIMER], check=False, timeout=30)
            run(["systemctl", "stop", SERVICE], check=False, timeout=30)
        except Exception:
            pass
        if lifecycle["dropin_installed"] and not lifecycle["finalized"]:
            try:
                remove_persistent_dropin()
            except Exception:
                pass
        if lifecycle["backup_ready"] and not lifecycle["finalized"]:
            try:
                if before_inventory is not None and database_inventory(DB) != before_inventory:
                    if db_backup is not None:
                        restore_database_from_backup(db_backup)
                if output_backups:
                    restore_managed_outputs(output_backups)
                if repo_backups:
                    restore_repo_state(repo_backups)
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
            state = systemctl_state(SERVICE)
            if state["active"] in {"inactive", "failed"}:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("A23_SERVICE_DID_NOT_BECOME_INACTIVE")
        run(["systemctl", "reset-failed", SERVICE], check=False, timeout=20)

        before_inventory = database_inventory(DB)
        before_map = batch_map(before_inventory)
        if before_inventory["batch_rows"] != 2 or before_inventory["ledger_rows"] != 213:
            raise RuntimeError("A23_BASELINE_DATABASE_COUNTS_DRIFT")
        if set(before_map) != set(a22["verified_batches"].values()) - {2, 213}:
            expected_uids = {
                str(a22["verified_batches"]["baseline_batch_uid"]),
                str(a22["verified_batches"]["canary_batch_uid"]),
            }
            if set(before_map) != expected_uids:
                raise RuntimeError("A23_BASELINE_BATCH_UID_SET_DRIFT")
        if any(batch["status"] != "COMMITTED" for batch in before_map.values()):
            raise RuntimeError("A23_BASELINE_BATCH_STATUS_INVALID")
        if before_inventory["integrity_check"] != "ok":
            raise RuntimeError("A23_BASELINE_INTEGRITY_FAILED")
        if before_inventory["quick_check"] != "ok":
            raise RuntimeError("A23_BASELINE_QUICK_CHECK_FAILED")
        if before_inventory["foreign_key_check_rows"] != 0:
            raise RuntimeError("A23_BASELINE_FOREIGN_KEY_FAILED")

        backup_root = Path(
            tempfile.mkdtemp(
                prefix="era55a23_apply_",
                dir="/dev/shm" if Path("/dev/shm").exists() else "/tmp",
            )
        )
        db_backup = backup_root / "production.sqlite"
        backup_sqlite(DB, db_backup)
        output_backups = backup_files(managed_output_paths(), backup_root)
        repo_backups = backup_repo_state(backup_root)
        lifecycle["backup_ready"] = True

        RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
        for path in (RESULT_PATH, ERROR_PATH, ORDER_LOG, FULL_DISPLAY, WRITER_LOCK):
            if path.exists():
                path.unlink()

        DROPIN_DIR.mkdir(parents=True, exist_ok=True)
        DROPIN.write_text(
            "\n".join(
                [
                    "[Service]",
                    'Environment="TOKENOSKOBI_LEDGER_WRITER_ENABLED=1"',
                    'Environment="TOKENOSKOBI_RUNNER_LOCK_ENABLED=1"',
                    f'Environment="TOKENOSKOBI_NEWS_HOT_PATH={SELF}"',
                    'Environment="TOKENOSKOBI_A23_GUARDED_PRODUCTION=1"',
                    f'Environment="TOKENOSKOBI_A10_ORDER_LOG={ORDER_LOG}"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        lifecycle["dropin_installed"] = True
        run(["systemctl", "daemon-reload"], check=True, timeout=30)
        active_environment = service_environment()
        if not (
            active_environment["writer_enabled"]
            and active_environment["runner_lock_enabled"]
            and active_environment["hot_override_enabled"]
            and active_environment["guarded_mode_enabled"]
        ):
            raise RuntimeError("A23_PERSISTENT_DROPIN_NOT_ACTIVE")

        started_epoch = int(time.time())
        started_at = utc_now()
        lifecycle["cycle_started"] = True
        start = run(["systemctl", "start", SERVICE], check=False, timeout=360)
        service_start = {
            "rc": start.returncode,
            "stdout": start.stdout.strip(),
            "stderr": start.stderr.strip(),
        }
        if start.returncode != 0:
            detail = load(ERROR_PATH) if ERROR_PATH.exists() else None
            raise RuntimeError(
                "A23_CONTROLLED_SERVICE_START_FAILED:"
                + str(start.returncode)
                + ":"
                + json.dumps(detail, ensure_ascii=False, sort_keys=True)
                + ":"
                + start.stdout[-3000:]
                + start.stderr[-3000:]
            )

        deadline = time.time() + 300
        while time.time() < deadline:
            state = systemctl_state(SERVICE)
            if RESULT_PATH.exists() and state["active"] in {"inactive", "failed"}:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("A23_CONTROLLED_SERVICE_COMPLETION_TIMEOUT")

        service_after_cycle_environment = service_environment()
        if service_after_cycle_environment["result"] not in {"success", ""}:
            raise RuntimeError("A23_CONTROLLED_SERVICE_RESULT_NOT_SUCCESS")
        if service_after_cycle_environment["exec_main_status"] not in {"0", ""}:
            raise RuntimeError("A23_CONTROLLED_SERVICE_MAIN_STATUS_NOT_ZERO")
        if not RESULT_PATH.exists():
            raise RuntimeError("A23_CONTROLLED_RESULT_MISSING")
        cycle = load(RESULT_PATH)
        if cycle.get("status") != "OK_A23_GUARDED_PRODUCTION_CYCLE_COMPLETED":
            raise RuntimeError("A23_CONTROLLED_RESULT_STATUS_NOT_OK")
        if cycle["writer_status"] not in {"COMMITTED", "IDEMPOTENT_REPLAY_NOOP"}:
            raise RuntimeError("A23_CONTROLLED_WRITER_STATUS_INVALID")
        if int(cycle["source_candidate_count"]) != int(cycle["source_accounted"]):
            raise RuntimeError("A23_CONTROLLED_SOURCE_ACCOUNTING_FAILED")
        if int(cycle["unobservable_rows"]) != 0:
            raise RuntimeError("A23_CONTROLLED_UNOBSERVABLE_ROWS_NONZERO")
        if cycle["existing_batches_preserved"] is not True:
            raise RuntimeError("A23_CONTROLLED_EXISTING_BATCH_PRESERVATION_FAILED")
        if cycle["bridge_hash_match_all"] is not True:
            raise RuntimeError("A23_CONTROLLED_BRIDGE_HASH_FAILED")

        order = ORDER_LOG.read_text(encoding="utf-8").splitlines()
        required_prefix = [
            "LOCK_ACQUIRED",
            "RAW_START",
            "RAW_END:0",
            "DERIVED_START",
            "DERIVED_END:0",
            "HOT_START",
            "A23_GUARDED_HOT_START",
            "A23_GUARDED_ORIGINAL_HOT_END:0",
        ]
        positions: list[int] = []
        for marker in required_prefix:
            if marker not in order:
                raise RuntimeError(f"A23_ORDER_MARKER_MISSING:{marker}")
            positions.append(order.index(marker))
        ledger_markers = [
            marker
            for marker in order
            if marker.startswith("A23_GUARDED_LEDGER_WRITE_DONE:")
        ]
        if ledger_markers != ["A23_GUARDED_LEDGER_WRITE_DONE:" + cycle["writer_status"]]:
            raise RuntimeError("A23_LEDGER_ORDER_MARKER_INVALID")
        suffix = [
            ledger_markers[0],
            "A23_GUARDED_PANEL_BRIDGE_END:0",
            "A23_GUARDED_HOT_END:0",
            "HOT_END:0",
        ]
        for marker in suffix:
            if marker not in order:
                raise RuntimeError(f"A23_ORDER_MARKER_MISSING:{marker}")
            positions.append(order.index(marker))
        if positions != sorted(positions):
            raise RuntimeError("A23_ORDER_SEQUENCE_INVALID")
        if order[-1] != "HOT_END:0":
            raise RuntimeError("A23_ORDER_NOT_ENDING_HOT_ZERO")
        recovery_markers = [
            marker for marker in order if marker.startswith("RECOVERY_DONE:")
        ]
        if len(recovery_markers) != 1:
            raise RuntimeError("A23_RECOVERY_MARKER_COUNT_INVALID")
        if recovery_markers[0] not in {
            "RECOVERY_DONE:OUTPUT_ALREADY_MATCHED",
            "RECOVERY_DONE:RECOVERED",
        }:
            raise RuntimeError("A23_RECOVERY_MARKER_INVALID:" + recovery_markers[0])

        after_inventory = database_inventory(DB)
        before_map = batch_map(before_inventory)
        after_map = batch_map(after_inventory)
        if any(after_map[uid] != before_map[uid] for uid in before_map):
            raise RuntimeError("A23_POST_APPLY_EXISTING_BATCH_MUTATED")
        new_uids = sorted(set(after_map) - set(before_map))
        actual_uid = str(cycle["actual_batch_uid"])
        source_count = int(cycle["source_candidate_count"])
        if cycle["writer_status"] == "COMMITTED":
            if new_uids != [actual_uid]:
                raise RuntimeError("A23_POST_APPLY_NEW_BATCH_SET_INVALID")
            if after_inventory["batch_rows"] != before_inventory["batch_rows"] + 1:
                raise RuntimeError("A23_POST_APPLY_BATCH_COUNT_INVALID")
            if after_inventory["ledger_rows"] != before_inventory["ledger_rows"] + source_count:
                raise RuntimeError("A23_POST_APPLY_LEDGER_COUNT_INVALID")
        else:
            if new_uids:
                raise RuntimeError("A23_POST_APPLY_IDEMPOTENT_CREATED_BATCH")
            if after_inventory != before_inventory:
                raise RuntimeError("A23_POST_APPLY_IDEMPOTENT_DATABASE_CHANGED")
        if after_inventory["integrity_check"] != "ok":
            raise RuntimeError("A23_POST_APPLY_INTEGRITY_FAILED")
        if after_inventory["quick_check"] != "ok":
            raise RuntimeError("A23_POST_APPLY_QUICK_CHECK_FAILED")
        if after_inventory["foreign_key_check_rows"] != 0:
            raise RuntimeError("A23_POST_APPLY_FOREIGN_KEY_FAILED")
        if sha(HOT) != sha(PANEL_HOT):
            raise RuntimeError("A23_POST_APPLY_PANEL_HASH_MISMATCH")
        bridge_state = load(BRIDGE_STATE)
        if bridge_state.get("decision") != "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED":
            raise RuntimeError("A23_POST_APPLY_BRIDGE_DECISION_FAILED")
        if not bridge_state.get("hash_match") or not all(
            value is True for value in bridge_state["hash_match"].values()
        ):
            raise RuntimeError("A23_POST_APPLY_BRIDGE_HASH_FAILED")

        timer_post_audit_paused = systemctl_state(TIMER)
        if timer_post_audit_paused["active"] != "inactive":
            raise RuntimeError("A23_TIMER_NOT_PAUSED_DURING_POST_AUDIT")
        service_after_cycle = systemctl_state(SERVICE)
        if service_after_cycle["active"] not in {"inactive", "failed"}:
            raise RuntimeError("A23_SERVICE_NOT_INACTIVE_AFTER_CONTROLLED_CYCLE")
        persistent_environment = service_environment()
        if not (
            persistent_environment["writer_enabled"]
            and persistent_environment["runner_lock_enabled"]
            and persistent_environment["hot_override_enabled"]
            and persistent_environment["guarded_mode_enabled"]
        ):
            raise RuntimeError("A23_PERSISTENT_INTEGRATION_NOT_RETAINED")
        if not DROPIN.exists():
            raise RuntimeError("A23_PERSISTENT_DROPIN_MISSING")

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
            raise RuntimeError("A23_TIMER_ACTIVE_STATE_NOT_RESTORED")
        if timer_after["enabled"] != timer_before["enabled"]:
            raise RuntimeError("A23_TIMER_ENABLED_STATE_CHANGED")
        final_environment = service_environment()
        if not (
            final_environment["writer_enabled"]
            and final_environment["runner_lock_enabled"]
            and final_environment["hot_override_enabled"]
            and final_environment["guarded_mode_enabled"]
        ):
            raise RuntimeError("A23_FINAL_PERSISTENT_ENVIRONMENT_INVALID")

        finished_at = utc_now()
        artifact = {
            "schema_version": "1.0",
            "work_unit": WORK_UNIT,
            "timestamp_utc": finished_at,
            "status": "CLOSED_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVE_POST_AUDIT",
            "result": RESULT,
            "authorization_source": str(A22.relative_to(ROOT)),
            "apply_started_at_utc": started_at,
            "apply_finished_at_utc": finished_at,
            "service_start": service_start,
            "runner_order": order,
            "runner_order_valid": True,
            "runner_recovery_marker": recovery_markers[0],
            "controlled_cycle": cycle,
            "production_before": before_inventory,
            "production_after": after_inventory,
            "existing_batches_preserved": True,
            "controlled_cycle_writer_status": cycle["writer_status"],
            "controlled_cycle_new_batch_uids": new_uids,
            "persistent_integration": {
                "dropin_path": str(DROPIN),
                "dropin_sha256": sha(DROPIN),
                "dropin_persistent": True,
                "hot_wrapper_path": str(SELF),
                "writer_flag_enabled": final_environment["writer_enabled"],
                "runner_lock_enabled": final_environment["runner_lock_enabled"],
                "hot_override_enabled": final_environment["hot_override_enabled"],
                "guarded_mode_enabled": final_environment["guarded_mode_enabled"],
                "timer_active": timer_after["active"] == "active",
                "timer_enabled": timer_after["enabled"] == "enabled",
                "service_execution_model": "TIMER_TRIGGERED_ONESHOT_SERVICE",
            },
            "post_apply_audit": {
                "database_integrity": after_inventory["integrity_check"],
                "database_quick_check": after_inventory["quick_check"],
                "foreign_key_check_rows": after_inventory["foreign_key_check_rows"],
                "hot_panel_hash_match": sha(HOT) == sha(PANEL_HOT),
                "bridge_decision": bridge_state["decision"],
                "bridge_hash_match_all": True,
                "complete_source_accounting": (
                    int(cycle["source_accounted"])
                    == int(cycle["source_candidate_count"])
                ),
                "unobservable_rows": int(cycle["unobservable_rows"]),
                "existing_batches_preserved": True,
                "runner_hot_end_zero": order[-1] == "HOT_END:0",
            },
            "rollback_protection": {
                "policy_version": ROLLBACK_POLICY,
                "guard_path": str(ROLLBACK_GUARD.relative_to(ROOT)),
                "guard_sha256": sha(ROLLBACK_GUARD),
                "armed_for_every_cycle": True,
                "controlled_cycle_triggered": False,
                "scope": "NEW_CURRENT_CYCLE_BATCH_ONLY",
                "emergency_database_backup_used": False,
            },
            "configuration_backup": {
                "service_environment_before": environment_initial,
                "service_environment_after": final_environment,
                "dropin_absent_before": True,
                "dropin_present_after": DROPIN.exists(),
            },
            "timer_before": timer_before,
            "timer_post_audit_paused": timer_post_audit_paused,
            "timer_after": timer_after,
            "service_initial": service_initial,
            "service_after_controlled_cycle": service_after_cycle,
            "journal_excerpt": {
                "rc": journal.returncode,
                "stdout_tail": journal.stdout[-12000:],
                "stderr_tail": journal.stderr[-3000:],
            },
            "authorization": {
                "guarded_general_production_writer_activation_apply_authorized": False,
                "general_production_writer_activation_authorized": True,
                "activation_apply_completed": True,
                "production_writer_active": True,
                "additional_canary_authorized": False,
                "p0_f1_closed": False,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
            },
            "next_safe_step": NEXT,
        }
        atomic_dump(ARTIFACT, artifact)

        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            f"""# ERA55A23 Guarded General Production Writer Runtime Integration

- Status: `CLOSED_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVE_POST_AUDIT`
- Result: `{RESULT}`
- Persistent drop-in installed: `true`
- Persistent guarded wrapper: `{SELF.relative_to(ROOT)}`
- Controlled cycle writer status: `{cycle['writer_status']}`
- Controlled cycle batch UID: `{actual_uid}`
- Controlled source candidates: `{source_count}`
- Controlled source accounted: `{cycle['source_accounted']}`
- Existing committed batches preserved: `true`
- Production batch rows after: `{after_inventory['batch_rows']}`
- Production ledger rows after: `{after_inventory['ledger_rows']}`
- Runner HOT_END:0: `true`
- Panel hash parity: `true`
- Rollback guard armed for every cycle: `true`
- Timer active and enabled: `true`
- Production writer active: `true`
- Additional canary authorized: `false`
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
                "mode": "ERA55A23_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVE",
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
                    "type": "ERA55_P0_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_APPLY_POST_AUDIT",
                    "parent": "ERA55_RUNTIME_OPTIMIZATION",
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "status": artifact["status"],
                    "result": RESULT,
                    "production_mutation": True,
                    "next_step": NEXT,
                },
                "next_safe_step": {
                    "id": NEXT,
                    "type": "ERA55_P0_POST_ACTIVATION_OBSERVATION_AND_P0_F1_CLOSURE_DECISION",
                    "parent": "ERA55_RUNTIME_OPTIMIZATION",
                    "purpose": (
                        "Observe scheduled guarded production cycles, verify stable operation, "
                        "and decide P0 F1 closure without opening Option B automatically."
                    ),
                    "human_authorization_required": True,
                    "general_production_writer_activation_authorized": True,
                    "production_writer_active": True,
                    "additional_canary_authorized": False,
                    "p0_f1_closed": False,
                    "option_b_authorized": False,
                    "optimization_apply_authorized": False,
                    "status": "READY",
                },
                "current_problem": {
                    "code": "POST_ACTIVATION_OBSERVATION_AND_P0_F1_DECISION_PENDING",
                    "severity": "P0",
                    "evidence": str(ARTIFACT.relative_to(ROOT)),
                },
            }
        )
        runtime["current_work_unit"] = current["active_work_unit"]
        atomic_dump(RUNTIME, runtime)

        history = load(HISTORY)
        events = history.setdefault("events", [])
        event_id = "ERA55A23_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVE_V1"
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
                    "event": "GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_APPLY_POST_AUDIT",
                    "status": artifact["status"],
                    "result": RESULT,
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "persistent_dropin": str(DROPIN),
                    "controlled_cycle_writer_status": cycle["writer_status"],
                    "controlled_cycle_batch_uid": actual_uid,
                    "controlled_cycle_source_rows": source_count,
                    "production_batch_rows": after_inventory["batch_rows"],
                    "production_ledger_rows": after_inventory["ledger_rows"],
                    "existing_batches_preserved": True,
                    "runner_hot_end_zero": True,
                    "panel_hash_parity": True,
                    "production_writer_active": True,
                    "additional_canary_authorized": False,
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
PROJECT_STATUS=ACTIVE_ERA55_P0_GUARDED_PRODUCTION_WRITER_ACTIVE
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
CURRENT_STAGE=ERA55A_P0_POST_ACTIVATION_OBSERVATION
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_BATCH_ROWS={after_inventory['batch_rows']}
PRODUCTION_LEDGER_ROWS={after_inventory['ledger_rows']}
CONTROLLED_CYCLE_WRITER_STATUS={cycle['writer_status']}
CONTROLLED_CYCLE_BATCH_UID={actual_uid}
CONTROLLED_CYCLE_SOURCE_ROWS={source_count}
CONTROLLED_CYCLE_SOURCE_ACCOUNTED={cycle['source_accounted']}
EXISTING_BATCHES_PRESERVED=true
RUNNER_HOT_END_ZERO=true
PANEL_HOT_HASH_PARITY=true
PERSISTENT_GUARDED_WRITER_INTEGRATION=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=true
PRODUCTION_LEDGER_WRITER_ACTIVE=true
ADDITIONAL_CANARY_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

The guarded writer is active under the timer. P0 F1 closure requires post-activation observation.""",
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
PERSISTENT_RUNTIME_INTEGRATION=true
```

NEXT_SAFE_STEP={NEXT}""",
        )
        MASTER.write_text(master, encoding="utf-8")

        handoff = HANDOFF.read_text(encoding="utf-8")
        handoff = replace_section(
            handoff,
            "## 02 CURRENT CONTINUATION CHECKPOINT",
            f"""PROJECT_STATUS=ACTIVE_ERA55_P0_GUARDED_PRODUCTION_WRITER_ACTIVE
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_POST_ACTIVATION_OBSERVATION
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_BATCH_ROWS={after_inventory['batch_rows']}
PRODUCTION_LEDGER_ROWS={after_inventory['ledger_rows']}
CONTROLLED_CYCLE_WRITER_STATUS={cycle['writer_status']}
CONTROLLED_CYCLE_BATCH_UID={actual_uid}
CONTROLLED_CYCLE_SOURCE_ROWS={source_count}
CONTROLLED_CYCLE_SOURCE_ACCOUNTED={cycle['source_accounted']}
EXISTING_BATCHES_PRESERVED=true
RUNNER_HOT_END_ZERO=true
PANEL_HOT_HASH_PARITY=true
PERSISTENT_GUARDED_WRITER_INTEGRATION=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=true
PRODUCTION_LEDGER_WRITER_ACTIVE=true
ADDITIONAL_CANARY_AUTHORIZED=false
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
CURRENT_PROBLEM=POST_ACTIVATION_OBSERVATION_AND_P0_F1_DECISION_PENDING""",
        )
        handoff = replace_section(
            handoff,
            "## 06 DO NOT REOPEN OR REPEAT",
            """- Do not rerun A9-A23 unless evidence is invalidated.
- Do not execute another canary.
- Do not remove or edit the A23 persistent integration without a rollback plan.
- Do not delete any valid committed production batch.
- Do not start Option B or close P0 F1 before A24 observation.""",
        )
        handoff = replace_section(
            handoff,
            "## 07 ALLOWED NEXT DECISIONS",
            f"""- Guarded production writer: `ACTIVE`.
- Additional canary: `BLOCKED`.
- P0 F1 closure: `PENDING_POST_ACTIVATION_OBSERVATION`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
        )
        handoff = replace_section(
            handoff,
            "## 08 NEXT SESSION EXECUTION RULE",
            """1. Confirm A24 is current.
2. Observe scheduled timer-triggered guarded writer cycles without forcing another canary.
3. Verify service success, runner HOT_END:0, complete accounting, DB integrity and panel hash parity.
4. Confirm rollback guard remains armed and no runtime override drift exists.
5. Decide P0 F1 closure separately.
6. Keep Option B blocked unless explicitly authorized after closure.""",
        )
        HANDOFF.write_text(handoff, encoding="utf-8")

        almanac = ALMANAC.read_text(encoding="utf-8")
        marker = "## ERA55A_23 GUARDED GENERAL PRODUCTION WRITER ACTIVE"
        if marker not in almanac:
            ALMANAC.write_text(
                almanac.rstrip()
                + f"""

---

{marker}

- Status: `CLOSED_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVE_POST_AUDIT`
- Result: `{RESULT}`
- Persistent guarded integration: `true`
- Controlled cycle writer status: `{cycle['writer_status']}`
- Controlled cycle batch UID: `{actual_uid}`
- Controlled source rows: `{source_count}`
- Production batch rows: `{after_inventory['batch_rows']}`
- Production ledger rows: `{after_inventory['ledger_rows']}`
- Existing batches preserved: `true`
- Runner HOT_END:0: `true`
- Panel hash parity: `true`
- Production writer active: `true`
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
            raise RuntimeError("A23_NO_STAGED_CHANGES")
        git("commit", "-m", SUBJECT)
        lifecycle["finalized"] = True
        atexit.unregister(emergency_cleanup)

        print("ERA55A23_GUARDED_PRODUCTION_WRITER=SUCCESS")
        print("RESULT=" + RESULT)
        print("CONTROLLED_CYCLE_WRITER_STATUS=" + str(cycle["writer_status"]))
        print("CONTROLLED_CYCLE_BATCH_UID=" + actual_uid)
        print("CONTROLLED_SOURCE_CANDIDATES=" + str(source_count))
        print("CONTROLLED_SOURCE_ACCOUNTED=" + str(cycle["source_accounted"]))
        print("UNOBSERVABLE_ROWS=0")
        print("PRODUCTION_BATCH_ROWS=" + str(after_inventory["batch_rows"]))
        print("PRODUCTION_LEDGER_ROWS=" + str(after_inventory["ledger_rows"]))
        print("EXISTING_BATCHES_PRESERVED=true")
        print("RUNNER_HOT_END_ZERO=true")
        print("PANEL_HOT_HASH_PARITY=true")
        print("PERSISTENT_DROPIN_INSTALLED=true")
        print("ROLLBACK_GUARD_ARMED_FOR_EVERY_CYCLE=true")
        print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=true")
        print("PRODUCTION_WRITER_ACTIVE=true")
        print("ADDITIONAL_CANARY_AUTHORIZED=false")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print("NEXT_SAFE_STEP=" + NEXT)
        print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
        return 0
    except Exception:
        try:
            run(["systemctl", "stop", TIMER], check=False, timeout=30)
            run(["systemctl", "stop", SERVICE], check=False, timeout=30)
        except Exception:
            pass
        remove_persistent_dropin()
        if before_inventory is not None and database_inventory(DB) != before_inventory:
            if db_backup is None:
                raise RuntimeError("A23_APPLY_DATABASE_BACKUP_MISSING")
            restore_database_from_backup(db_backup)
        if output_backups:
            restore_managed_outputs(output_backups)
        if repo_backups:
            restore_repo_state(repo_backups)
        restore_timer(timer_before)
        lifecycle["timer_restored"] = True
        lifecycle["dropin_installed"] = False
        atexit.unregister(emergency_cleanup)
        raise
    finally:
        if backup_root is not None and lifecycle["finalized"]:
            shutil.rmtree(backup_root, ignore_errors=True)


def main() -> int:
    if os.environ.get("TOKENOSKOBI_A23_GUARDED_PRODUCTION", "0").strip() == "1":
        return guarded_production_hot()
    return orchestrate()


if __name__ == "__main__":
    raise SystemExit(main())
