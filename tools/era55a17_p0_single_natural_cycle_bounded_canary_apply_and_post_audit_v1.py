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

WORK_UNIT = "ERA55A_17_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_AND_POST_AUDIT"
RESULT = "OK_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_COMPLETED"
NEXT = "ERA55A_18_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION"
SUBJECT = "ERA55A17_SINGLE_CYCLE_CANARY | OK | GENERAL_ACTIVATION_BLOCKED"
POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"
MAX_SOURCE_ROWS = 5000

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

A16 = ROOT / "data/control/era55a16_p0_queue_parity_post_test_audit_and_single_cycle_canary_decision_v1.json"
ARTIFACT = ROOT / "data/control/era55a17_p0_single_natural_cycle_bounded_canary_apply_and_post_audit_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A17_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_AND_POST_AUDIT.md"

SELF = Path(__file__).resolve()
ADAPTER = ROOT / "tools/news_disposition_admission_contract_v1.py"
EXTRACTOR = ROOT / "tools/news_pre_gateway_candidate_stream_v1.py"
WRITER = ROOT / "tools/news_disposition_ledger_writer_v1.py"
RECOVERY = ROOT / "tools/news_ledger_recovery_guard_v1.py"
GATEWAY = ROOT / "tools/hot_intelligence_ingress_gateway_v1.py"
RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
ORIGINAL_HOT = ROOT / "tools/post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.py"
PANEL_BRIDGE = ROOT / "tools/news_active_panel_data_bridge_v1.py"

MARKET = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADVERSARIAL = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
DISPLAY = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
RECOVERY_STATE = ROOT / "runtime/state/news_ledger_recovery_state_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
PANEL_MANIFEST = ROOT / "active_panel_8096/current/data/news_active_panel_data_bridge_manifest_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

RUNTIME_ROOT = Path("/run/tokenoskobi")
DROPIN_DIR = Path("/run/systemd/system") / f"{SERVICE}.d"
DROPIN = DROPIN_DIR / "90-era55a17-canary.conf"
RESULT_PATH = RUNTIME_ROOT / "era55a17_one_shot_result.json"
INVOCATION_GUARD = RUNTIME_ROOT / "era55a17_invocation.guard"
ORDER_LOG = RUNTIME_ROOT / "era55a17_order.log"
FULL_DISPLAY = RUNTIME_ROOT / "era55a17_full_candidate_display.json"
WRITER_LOCK = RUNTIME_ROOT / "era55a17_writer.lock"

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

def dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=str(path.parent))
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

def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")

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
    source_conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target_conn = sqlite3.connect(target)
    try:
        source_conn.backup(target_conn)
    finally:
        target_conn.close()
        source_conn.close()

def db_state(path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        return {
            "batch_rows": int(
                conn.execute(
                    "SELECT COUNT(*) FROM news_disposition_batches_v2"
                ).fetchone()[0]
            ),
            "ledger_rows": int(
                conn.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2"
                ).fetchone()[0]
            ),
            "integrity_check": str(
                conn.execute("PRAGMA integrity_check").fetchone()[0]
            ),
            "quick_check": str(
                conn.execute("PRAGMA quick_check").fetchone()[0]
            ),
            "foreign_key_check_rows": len(
                conn.execute("PRAGMA foreign_key_check").fetchall()
            ),
        }
    finally:
        conn.close()

def latest_batch(path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        row = conn.execute(
            """
            SELECT
                rowid,
                batch_uid,
                policy_version,
                queue_capacity,
                source_candidate_count,
                admitted_count,
                overflow_count,
                duplicate_removed_count,
                unsafe_filtered_count,
                invalid_candidate_count,
                replaced_count
            FROM news_disposition_batches_v2
            ORDER BY rowid DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return {"exists": False}
        dispositions = {
            str(name): int(count)
            for name, count in conn.execute(
                """
                SELECT disposition, COUNT(*)
                FROM news_disposition_ledger_v2
                WHERE batch_uid=?
                GROUP BY disposition
                """,
                (row[1],),
            ).fetchall()
        }
        ledger_rows = int(
            conn.execute(
                "SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?",
                (row[1],),
            ).fetchone()[0]
        )
        return {
            "exists": True,
            "batch_sequence": int(row[0]),
            "batch_uid": str(row[1]),
            "policy_version": str(row[2]),
            "queue_capacity": int(row[3]),
            "source_candidate_count": int(row[4]),
            "admitted_count": int(row[5]),
            "overflow_count": int(row[6]),
            "duplicate_removed_count": int(row[7]),
            "unsafe_filtered_count": int(row[8]),
            "invalid_candidate_count": int(row[9]),
            "replaced_count": int(row[10]),
            "ledger_rows": ledger_rows,
            "disposition_counts": dispositions,
        }
    finally:
        conn.close()

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
        "rc": completed.returncode,
        "runner_bound": str(RUNNER) in text,
        "writer_enabled": "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text,
        "runner_lock_enabled": "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text,
        "any_hot_override": "TOKENOSKOBI_NEWS_HOT_PATH=" in text,
        "hot_override_enabled": f"TOKENOSKOBI_NEWS_HOT_PATH={SELF}" in text,
        "canary_mode_enabled": "TOKENOSKOBI_A17_ONE_SHOT_HOT=1" in text,
        "result": next(
            (line.split("=", 1)[1] for line in text.splitlines() if line.startswith("Result=")),
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
        "raw": text,
    }

def validate_authorization() -> dict[str, Any]:
    a16 = load(A16)
    assert a16["status"] == "CLOSED_SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED"
    assert a16["result"] == "OK_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_AUTHORIZED"
    auth = a16["authorization"]
    assert auth["single_natural_cycle_bounded_canary_authorized"] is True
    assert auth["general_production_writer_activation_authorized"] is False
    contract = a16["canary_execution_contract"]
    assert contract["one_full_runner_cycle_only"] is True
    assert contract["maximum_new_batch_rows"] == 1
    assert contract["maximum_source_rows"] == MAX_SOURCE_ROWS
    assert contract["runtime_only_systemd_dropin_required"] is True
    assert contract["dropin_removal_after_cycle_required"] is True
    assert contract["timer_state_restore_required"] is True
    return a16

def one_shot_hot() -> int:
    token = os.environ.get("TOKENOSKOBI_A17_CANARY_TOKEN", "").strip()
    expected = os.environ.get("TOKENOSKOBI_A17_EXPECTED_HEAD", "").strip()
    result_path = Path(os.environ.get("TOKENOSKOBI_A17_RESULT_PATH", str(RESULT_PATH)))
    invocation_guard = Path(
        os.environ.get(
            "TOKENOSKOBI_A17_INVOCATION_GUARD",
            str(INVOCATION_GUARD),
        )
    )
    if not token or not expected:
        raise RuntimeError("A17_CANARY_ENVIRONMENT_INCOMPLETE")
    if git("rev-parse", "HEAD") != expected:
        raise RuntimeError("A17_CANARY_HEAD_MISMATCH")

    invocation_guard.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(invocation_guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, token.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)

    append_order("A17_ONE_SHOT_HOT_START")
    original = run(
        [sys.executable, str(ORIGINAL_HOT), "--runtime-refresh"],
        check=False,
        timeout=180,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    append_order(f"A17_ORIGINAL_HOT_END:{original.returncode}")
    if original.returncode != 0:
        raise RuntimeError(
            "A17_ORIGINAL_HOT_FAILED:"
            + str(original.returncode)
            + ":"
            + original.stderr[-2000:]
        )

    legacy_contract = load(HOT)
    legacy_queue = legacy_contract.get("hot_queue")
    if not isinstance(legacy_queue, list):
        raise RuntimeError("A17_LEGACY_HOT_QUEUE_NOT_LIST")

    tools_path = str(ROOT / "tools")
    if tools_path not in sys.path:
        sys.path.insert(0, tools_path)
    extractor = load_module("a17_extractor", EXTRACTOR)
    adapter = load_module("a17_adapter", ADAPTER)
    if adapter.POLICY_VERSION != POLICY:
        raise RuntimeError("A17_POLICY_VERSION_MISMATCH")

    full_display = extractor.build_candidate_display(MARKET, ADVERSARIAL)
    dump(FULL_DISPLAY, full_display)

    plan = adapter.build_plan_with_admission_contract(
        full_display,
        legacy_queue,
        queue_capacity=50,
    )
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
    if not (0 < len(legacy_queue) <= 50):
        raise RuntimeError("A17_LEGACY_QUEUE_BOUND_FAILED")
    if not (len(legacy_queue) <= source_count <= MAX_SOURCE_ROWS):
        raise RuntimeError("A17_SOURCE_BOUND_FAILED")
    if accounted != source_count:
        raise RuntimeError("A17_SOURCE_ACCOUNTING_FAILED")

    writer_result = adapter.write_and_publish_with_admission_contract(
        display_path=FULL_DISPLAY,
        admission_contract_path=HOT,
        summary_path=SUMMARY,
        db_path=DB,
        output_path=HOT,
        recovery_state_path=RECOVERY_STATE,
        contract_seed_path=HOT,
        queue_capacity=50,
        lock_path=WRITER_LOCK,
    )
    append_order(
        "A17_LEDGER_WRITE_DONE:"
        + str(writer_result.get("write_result", {}).get("status"))
    )
    if writer_result.get("write_result", {}).get("status") != "COMMITTED":
        raise RuntimeError("A17_LEDGER_WRITE_NOT_COMMITTED")

    final_hot = load(HOT)
    final_queue = final_hot.get("hot_queue")
    if canonical(final_queue) != canonical(legacy_queue):
        raise RuntimeError("A17_FINAL_QUEUE_PARITY_FAILED")

    bridge = run(
        [sys.executable, str(PANEL_BRIDGE)],
        check=False,
        timeout=90,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    append_order(f"A17_PANEL_BRIDGE_END:{bridge.returncode}")
    if bridge.returncode != 0:
        raise RuntimeError(
            "A17_PANEL_BRIDGE_FAILED:"
            + str(bridge.returncode)
            + ":"
            + bridge.stderr[-2000:]
        )
    bridge_state = load(BRIDGE_STATE)
    if bridge_state.get("decision") != "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED":
        raise RuntimeError("A17_PANEL_BRIDGE_DECISION_NOT_OK")
    hash_match = bridge_state.get("hash_match")
    if not isinstance(hash_match, dict) or not hash_match or not all(
        value is True for value in hash_match.values()
    ):
        raise RuntimeError("A17_PANEL_BRIDGE_HASH_MISMATCH")
    if sha(HOT) != sha(PANEL_HOT):
        raise RuntimeError("A17_PANEL_HOT_HASH_MISMATCH")

    latest = latest_batch(DB)
    if not latest.get("exists"):
        raise RuntimeError("A17_BATCH_NOT_FOUND")
    if latest["batch_uid"] != plan["batch_uid"]:
        raise RuntimeError("A17_BATCH_UID_MISMATCH")
    if latest["source_candidate_count"] != source_count:
        raise RuntimeError("A17_BATCH_SOURCE_COUNT_MISMATCH")
    if latest["ledger_rows"] != source_count:
        raise RuntimeError("A17_LEDGER_ROW_COUNT_MISMATCH")

    payload = {
        "schema_version": "1.0",
        "token": token,
        "status": "OK_ONE_SHOT_HOT_WRAPPER_COMPLETED",
        "timestamp_utc": utc_now(),
        "original_hot_rc": original.returncode,
        "bridge_rc": bridge.returncode,
        "bridge_decision": bridge_state["decision"],
        "bridge_hash_match_all": True,
        "source_candidate_count": source_count,
        "source_accounted": accounted,
        "legacy_queue_count": len(legacy_queue),
        "exact_legacy_object_parity": True,
        "exact_legacy_uid_order_parity": True,
        "batch_uid": latest["batch_uid"],
        "batch_sequence": latest["batch_sequence"],
        "ledger_rows": latest["ledger_rows"],
        "disposition_counts": latest["disposition_counts"],
        "writer_status": writer_result["write_result"]["status"],
        "publish_status": writer_result["publish_result"]["status"],
        "hot_output_sha256": sha(HOT),
        "panel_hot_sha256": sha(PANEL_HOT),
        "policy_version": latest["policy_version"],
    }
    dump(result_path, payload)
    append_order("A17_ONE_SHOT_HOT_END:0")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
    return 0

def remove_dropin() -> None:
    if DROPIN.exists():
        DROPIN.unlink()
    try:
        DROPIN_DIR.rmdir()
    except OSError:
        pass
    run(["systemctl", "daemon-reload"], check=False, timeout=30)

def restore_file(path: Path, backup: Path | None, existed: bool) -> None:
    if existed:
        if backup is None or not backup.exists():
            raise RuntimeError(f"BACKUP_MISSING:{path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.parent / ("." + path.name + ".a17restore")
        shutil.copy2(backup, temp)
        os.replace(temp, path)
    elif path.exists():
        path.unlink()

def logical_ledger_rollback(before: dict[str, Any]) -> dict[str, Any]:
    current = db_state(DB)
    if current["integrity_check"] != "ok" or current["quick_check"] != "ok":
        return {"mode": "FULL_DB_RESTORE_REQUIRED", "current": current}
    conn = sqlite3.connect(DB)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM news_disposition_ledger_v2")
        conn.execute("DELETE FROM news_disposition_batches_v2")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    after = db_state(DB)
    if after["batch_rows"] != before["batch_rows"] or after["ledger_rows"] != before["ledger_rows"]:
        raise RuntimeError("A17_LOGICAL_ROLLBACK_COUNT_MISMATCH")
    return {"mode": "LOGICAL_LEDGER_DELETE", "after": after}

def restore_timer(timer_before: dict[str, Any]) -> None:
    if timer_before["active"] == "active":
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
        A16,
        SELF,
        ADAPTER,
        EXTRACTOR,
        WRITER,
        RECOVERY,
        GATEWAY,
        RUNNER,
        ORIGINAL_HOT,
        PANEL_BRIDGE,
        MARKET,
        ADVERSARIAL,
        DISPLAY,
        SUMMARY,
        HOT,
        DB,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    validate_authorization()
    before_db = db_state(DB)
    if before_db != {
        "batch_rows": 0,
        "ledger_rows": 0,
        "integrity_check": "ok",
        "quick_check": "ok",
        "foreign_key_check_rows": 0,
    }:
        raise RuntimeError("A17_PRODUCTION_DB_PRECONDITION_FAILED")

    timer_before = systemctl_state(TIMER)
    service_before = systemctl_state(SERVICE)
    environment_before = service_environment()
    if service_before["active"] not in {"inactive", "failed"}:
        raise RuntimeError("A17_SERVICE_NOT_INACTIVE")
    if environment_before["writer_enabled"]:
        raise RuntimeError("A17_WRITER_ALREADY_ENABLED")
    if environment_before["runner_lock_enabled"]:
        raise RuntimeError("A17_RUNNER_LOCK_ALREADY_ENABLED")
    if environment_before["any_hot_override"]:
        raise RuntimeError("A17_HOT_OVERRIDE_ALREADY_ENABLED")
    if DROPIN.exists():
        raise RuntimeError("A17_DROPIN_ALREADY_PRESENT")

    backup_root = Path(
        tempfile.mkdtemp(
            prefix="era55a17_",
            dir="/dev/shm" if Path("/dev/shm").exists() else "/tmp",
        )
    )
    db_backup = backup_root / "database.sqlite"
    backup_sqlite(DB, db_backup)

    backup_targets = {
        "hot": HOT,
        "recovery_state": RECOVERY_STATE,
        "bridge_state": BRIDGE_STATE,
        "panel_hot": PANEL_HOT,
        "panel_manifest": PANEL_MANIFEST,
    }
    backup_meta: dict[str, Any] = {}
    for name, path in backup_targets.items():
        existed = path.exists()
        backup = backup_root / (name + ".backup") if existed else None
        if existed and backup is not None:
            shutil.copy2(path, backup)
        backup_meta[name] = {
            "path": path,
            "existed": existed,
            "backup": backup,
            "state": file_state(path),
        }

    lifecycle = {
        "canary_succeeded": False,
        "finalized": False,
        "rollback_done": False,
        "timer_restored": False,
    }

    def emergency_cleanup() -> None:
        try:
            remove_dropin()
        except Exception:
            pass
        if (
            lifecycle["canary_succeeded"]
            and not lifecycle["finalized"]
            and not lifecycle["rollback_done"]
        ):
            try:
                run(["systemctl", "stop", TIMER], check=False, timeout=30)
                lifecycle["timer_restored"] = False
                run(["systemctl", "stop", SERVICE], check=False, timeout=30)
                emergency_rollback = logical_ledger_rollback(before_db)
                if emergency_rollback.get("mode") == "FULL_DB_RESTORE_REQUIRED":
                    for suffix in ("-wal", "-shm"):
                        candidate = Path(str(DB) + suffix)
                        if candidate.exists():
                            candidate.unlink()
                    restore_temp = DB.parent / ("." + DB.name + ".a17restore")
                    shutil.copy2(db_backup, restore_temp)
                    os.replace(restore_temp, DB)
                for meta in backup_meta.values():
                    restore_file(
                        meta["path"],
                        meta["backup"],
                        bool(meta["existed"]),
                    )
                lifecycle["rollback_done"] = True
            except Exception:
                pass
        if not lifecycle["timer_restored"]:
            try:
                restore_timer(timer_before)
                lifecycle["timer_restored"] = True
            except Exception:
                pass

    atexit.register(emergency_cleanup)

    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    for path in (
        RESULT_PATH,
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
    canary_succeeded = False
    rollback: dict[str, Any] | None = None
    service_start: dict[str, Any] = {}
    error_text: str | None = None

    try:
        if timer_before["active"] == "active":
            run(["systemctl", "stop", TIMER], check=True, timeout=30)
        service_check = systemctl_state(SERVICE)
        if service_check["active"] not in {"inactive", "failed"}:
            raise RuntimeError("A17_SERVICE_ACTIVE_AFTER_TIMER_PAUSE")
        run(["systemctl", "reset-failed", SERVICE], check=False, timeout=20)

        DROPIN_DIR.mkdir(parents=True, exist_ok=True)
        DROPIN.write_text(
            "\n".join(
                [
                    "[Service]",
                    'Environment="TOKENOSKOBI_LEDGER_WRITER_ENABLED=1"',
                    'Environment="TOKENOSKOBI_RUNNER_LOCK_ENABLED=1"',
                    f'Environment="TOKENOSKOBI_NEWS_HOT_PATH={SELF}"',
                    'Environment="TOKENOSKOBI_A17_ONE_SHOT_HOT=1"',
                    f'Environment="TOKENOSKOBI_A17_CANARY_TOKEN={token}"',
                    f'Environment="TOKENOSKOBI_A17_EXPECTED_HEAD={EXPECTED_HEAD}"',
                    f'Environment="TOKENOSKOBI_A17_RESULT_PATH={RESULT_PATH}"',
                    f'Environment="TOKENOSKOBI_A17_INVOCATION_GUARD={INVOCATION_GUARD}"',
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
            and active_environment["canary_mode_enabled"]
        ):
            raise RuntimeError("A17_RUNTIME_DROPIN_NOT_ACTIVE")

        start = run(
            ["systemctl", "start", SERVICE],
            check=False,
            timeout=300,
        )
        service_start = {
            "rc": start.returncode,
            "stdout": start.stdout.strip(),
            "stderr": start.stderr.strip(),
        }
        if start.returncode != 0:
            raise RuntimeError(
                "A17_SERVICE_START_FAILED:"
                + str(start.returncode)
                + ":"
                + start.stderr[-3000:]
            )

        deadline = time.time() + 300
        while time.time() < deadline:
            current_service = systemctl_state(SERVICE)
            if RESULT_PATH.exists() and current_service["active"] in {
                "inactive",
                "failed",
            }:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("A17_SERVICE_COMPLETION_TIMEOUT")

        after_service = service_environment()
        if after_service["result"] not in {"success", ""}:
            raise RuntimeError("A17_SERVICE_RESULT_NOT_SUCCESS")
        if after_service["exec_main_status"] not in {"0", ""}:
            raise RuntimeError("A17_SERVICE_MAIN_STATUS_NOT_ZERO")
        if not RESULT_PATH.exists():
            raise RuntimeError("A17_ONE_SHOT_RESULT_MISSING")
        one_shot = load(RESULT_PATH)
        if one_shot.get("token") != token:
            raise RuntimeError("A17_ONE_SHOT_TOKEN_MISMATCH")
        if one_shot.get("status") != "OK_ONE_SHOT_HOT_WRAPPER_COMPLETED":
            raise RuntimeError("A17_ONE_SHOT_STATUS_NOT_OK")

        order = ORDER_LOG.read_text(encoding="utf-8").splitlines()
        required_markers = [
            "LOCK_ACQUIRED",
            "RAW_START",
            "RAW_END:0",
            "DERIVED_START",
            "DERIVED_END:0",
            "HOT_START",
            "A17_ONE_SHOT_HOT_START",
            "A17_ORIGINAL_HOT_END:0",
            "A17_LEDGER_WRITE_DONE:COMMITTED",
            "A17_PANEL_BRIDGE_END:0",
            "A17_ONE_SHOT_HOT_END:0",
            "HOT_END:0",
        ]
        positions: list[int] = []
        for marker in required_markers:
            if marker not in order:
                raise RuntimeError(f"A17_ORDER_MARKER_MISSING:{marker}")
            positions.append(order.index(marker))
        if positions != sorted(positions):
            raise RuntimeError("A17_ORDER_SEQUENCE_INVALID")
        if order.count("A17_ONE_SHOT_HOT_START") != 1:
            raise RuntimeError("A17_ONE_SHOT_INVOCATION_COUNT_INVALID")

        after_db = db_state(DB)
        latest = latest_batch(DB)
        if after_db["batch_rows"] != 1:
            raise RuntimeError("A17_BATCH_ROW_BOUND_FAILED")
        if not latest.get("exists"):
            raise RuntimeError("A17_LATEST_BATCH_MISSING")
        if latest["batch_uid"] != one_shot["batch_uid"]:
            raise RuntimeError("A17_POST_AUDIT_BATCH_UID_MISMATCH")
        if latest["source_candidate_count"] != one_shot["source_candidate_count"]:
            raise RuntimeError("A17_POST_AUDIT_SOURCE_COUNT_MISMATCH")
        if latest["ledger_rows"] != latest["source_candidate_count"]:
            raise RuntimeError("A17_POST_AUDIT_LEDGER_COUNT_MISMATCH")
        if latest["source_candidate_count"] > MAX_SOURCE_ROWS:
            raise RuntimeError("A17_POST_AUDIT_SOURCE_BOUND_FAILED")
        if after_db["integrity_check"] != "ok":
            raise RuntimeError("A17_DB_INTEGRITY_FAILED")
        if after_db["quick_check"] != "ok":
            raise RuntimeError("A17_DB_QUICK_CHECK_FAILED")
        if after_db["foreign_key_check_rows"] != 0:
            raise RuntimeError("A17_DB_FOREIGN_KEY_FAILED")

        hot = load(HOT)
        queue = hot.get("hot_queue")
        if not isinstance(queue, list):
            raise RuntimeError("A17_FINAL_HOT_QUEUE_NOT_LIST")
        if len(queue) != one_shot["legacy_queue_count"]:
            raise RuntimeError("A17_FINAL_HOT_QUEUE_COUNT_MISMATCH")
        if sha(HOT) != one_shot["hot_output_sha256"]:
            raise RuntimeError("A17_FINAL_HOT_HASH_MISMATCH")
        if sha(PANEL_HOT) != sha(HOT):
            raise RuntimeError("A17_FINAL_PANEL_HOT_HASH_MISMATCH")
        if load(BRIDGE_STATE).get("decision") != "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED":
            raise RuntimeError("A17_FINAL_BRIDGE_DECISION_FAILED")

        canary_succeeded = True
        lifecycle["canary_succeeded"] = True
    except Exception as exc:
        error_text = f"{type(exc).__name__}:{exc}"
        raise
    finally:
        remove_dropin()
        if not canary_succeeded:
            try:
                rollback = logical_ledger_rollback(before_db)
                if rollback.get("mode") == "FULL_DB_RESTORE_REQUIRED":
                    run(["systemctl", "stop", SERVICE], check=False, timeout=30)
                    for suffix in ("-wal", "-shm"):
                        candidate = Path(str(DB) + suffix)
                        if candidate.exists():
                            candidate.unlink()
                    restore_temp = DB.parent / ("." + DB.name + ".a17restore")
                    shutil.copy2(db_backup, restore_temp)
                    os.replace(restore_temp, DB)
                    rollback = {
                        "mode": "CONTROLLED_FULL_DB_RESTORE",
                        "after": db_state(DB),
                    }
                for name, meta in backup_meta.items():
                    restore_file(
                        meta["path"],
                        meta["backup"],
                        bool(meta["existed"]),
                    )
                if PANEL_HOT.exists() and HOT.exists() and sha(PANEL_HOT) != sha(HOT):
                    restore_file(
                        PANEL_HOT,
                        backup_meta["panel_hot"]["backup"],
                        bool(backup_meta["panel_hot"]["existed"]),
                    )
                lifecycle["rollback_done"] = True
            except Exception as rollback_exc:
                rollback = {
                    "mode": "ROLLBACK_FAILED",
                    "error": f"{type(rollback_exc).__name__}:{rollback_exc}",
                    "original_error": error_text,
                }
        if not canary_succeeded:
            restore_timer(timer_before)
            lifecycle["timer_restored"] = True

    if not canary_succeeded:
        raise RuntimeError("A17_CANARY_NOT_COMPLETED")

    service_after_cleanup = service_environment()
    timer_post_audit_paused = systemctl_state(TIMER)
    service_after = systemctl_state(SERVICE)
    if service_after_cleanup["writer_enabled"]:
        raise RuntimeError("A17_WRITER_FLAG_STILL_ENABLED")
    if service_after_cleanup["runner_lock_enabled"]:
        raise RuntimeError("A17_LOCK_FLAG_STILL_ENABLED")
    if service_after_cleanup["any_hot_override"]:
        raise RuntimeError("A17_HOT_OVERRIDE_STILL_ENABLED")
    if service_after_cleanup["canary_mode_enabled"]:
        raise RuntimeError("A17_CANARY_MODE_STILL_ENABLED")
    if DROPIN.exists():
        raise RuntimeError("A17_DROPIN_STILL_PRESENT")
    if timer_post_audit_paused["active"] != "inactive":
        raise RuntimeError("A17_TIMER_NOT_PAUSED_DURING_POST_AUDIT")
    if service_after["active"] not in {"inactive", "failed"}:
        raise RuntimeError("A17_SERVICE_NOT_INACTIVE_AFTER_CYCLE")

    after_db = db_state(DB)
    latest = latest_batch(DB)
    one_shot = load(RESULT_PATH)
    order = ORDER_LOG.read_text(encoding="utf-8").splitlines()
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
        raise RuntimeError("A17_TIMER_ACTIVE_STATE_NOT_RESTORED")
    if timer_after["enabled"] != timer_before["enabled"]:
        raise RuntimeError("A17_TIMER_ENABLED_STATE_CHANGED")

    now = utc_now()
    artifact = {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "timestamp_utc": now,
        "status": "CLOSED_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_OK",
        "result": RESULT,
        "authorization_source": str(A16.relative_to(ROOT)),
        "canary_token": token,
        "canary_started_at_utc": started_at,
        "canary_finished_at_utc": now,
        "service_start": service_start,
        "runner_order": order,
        "runner_order_valid": True,
        "one_shot_result": one_shot,
        "production_before": before_db,
        "production_after": after_db,
        "latest_batch": latest,
        "timer_before": timer_before,
        "timer_post_audit_paused": timer_post_audit_paused,
        "timer_after": timer_after,
        "service_before": service_before,
        "service_after": service_after,
        "service_environment_after_cleanup": {
            key: value
            for key, value in service_after_cleanup.items()
            if key != "raw"
        },
        "runtime_cleanup": {
            "dropin_removed": not DROPIN.exists(),
            "writer_flag_disabled": not service_after_cleanup["writer_enabled"],
            "runner_lock_flag_disabled": not service_after_cleanup["runner_lock_enabled"],
            "hot_override_disabled": not service_after_cleanup["any_hot_override"],
            "canary_mode_disabled": not service_after_cleanup["canary_mode_enabled"],
            "timer_state_restored": timer_after == timer_before,
        },
        "output_post_audit": {
            "hot_output": file_state(HOT),
            "panel_hot": file_state(PANEL_HOT),
            "hot_panel_hash_match": sha(HOT) == sha(PANEL_HOT),
            "bridge_state": file_state(BRIDGE_STATE),
            "bridge_decision": load(BRIDGE_STATE).get("decision"),
            "exact_legacy_object_parity": one_shot["exact_legacy_object_parity"],
            "exact_legacy_uid_order_parity": one_shot[
                "exact_legacy_uid_order_parity"
            ],
        },
        "database_post_audit": {
            "one_new_batch_row": after_db["batch_rows"] == 1,
            "all_source_rows_accounted": (
                latest["ledger_rows"] == latest["source_candidate_count"]
            ),
            "source_within_bound": (
                latest["source_candidate_count"] <= MAX_SOURCE_ROWS
            ),
            "integrity_check": after_db["integrity_check"],
            "quick_check": after_db["quick_check"],
            "foreign_key_check_rows": after_db["foreign_key_check_rows"],
        },
        "journal_excerpt": {
            "rc": journal.returncode,
            "stdout_tail": journal.stdout[-12000:],
            "stderr_tail": journal.stderr[-3000:],
        },
        "authorization": {
            "single_natural_cycle_bounded_canary_authorized": False,
            "single_natural_cycle_bounded_canary_consumed": True,
            "general_production_writer_activation_authorized": False,
            "production_writer_active": False,
            "p0_f1_closed": False,
            "option_b_authorized": False,
            "optimization_apply_authorized": False,
        },
        "rollback": rollback,
        "next_safe_step": NEXT,
    }
    dump(ARTIFACT, artifact)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "\n".join(
            [
                "# ERA55A17 Single Natural Cycle Bounded Canary",
                "",
                "- Status: `CLOSED_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_OK`",
                f"- Result: `{RESULT}`",
                f"- Batch rows: `{after_db['batch_rows']}`",
                f"- Ledger rows: `{after_db['ledger_rows']}`",
                f"- Source candidates: `{latest['source_candidate_count']}`",
                "- Unobservable rows: `0`",
                "- Exact legacy object parity: `true`",
                "- Exact legacy UID order parity: `true`",
                "- Panel hot hash parity: `true`",
                "- Runtime drop-in removed: `true`",
                "- Timer state restored: `true`",
                "- General production activation authorized: `false`",
                "- P0 F1 closed: `false`",
                f"- Next safe step: `{NEXT}`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    runtime = load(RUNTIME)
    current = runtime["current_state"]
    current.update(
        {
            "mode": "ERA55A17_SINGLE_CYCLE_BOUNDED_CANARY_COMPLETED",
            "runtime_status": "WORK_UNIT_CLOSED",
            "updated_at": now,
            "last_action": {
                "timestamp": now,
                "task": WORK_UNIT,
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
            },
            "active_work_unit": {
                "id": WORK_UNIT,
                "type": "ERA55_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_POST_AUDIT",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "status": artifact["status"],
                "result": RESULT,
                "production_mutation": True,
                "next_step": NEXT,
            },
            "next_safe_step": {
                "id": NEXT,
                "type": "ERA55_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "purpose": (
                    "Review the successful one-cycle production evidence and decide "
                    "whether general writer activation may be authorized."
                ),
                "human_authorization_required": True,
                "single_cycle_bounded_canary_authorized": False,
                "single_cycle_bounded_canary_consumed": True,
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
    dump(RUNTIME, runtime)

    history = load(HISTORY)
    events = history.setdefault("events", [])
    event_id = "ERA55A17_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_V1"
    if not any(
        isinstance(event, dict) and event.get("event_id") == event_id
        for event in events
    ):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": now,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_POST_AUDIT",
                "status": artifact["status"],
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "batch_rows": after_db["batch_rows"],
                "ledger_rows": after_db["ledger_rows"],
                "source_candidate_count": latest["source_candidate_count"],
                "unobservable_rows": 0,
                "exact_legacy_queue_parity": True,
                "panel_hash_parity": True,
                "runtime_overrides_removed": True,
                "timer_state_restored": True,
                "general_production_activation_authorized": False,
                "p0_f1_closed": False,
                "next_safe_step": NEXT,
            }
        )
    history["updated_at"] = now
    history["updated_at_utc"] = now
    dump(HISTORY, history)

    master = MASTER.read_text(encoding="utf-8")
    master = replace_section(
        master,
        "## 01 PROJECT STATUS",
        """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_P0_POST_CANARY_DECISION_PENDING
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
CURRENT_STAGE=ERA55A_P0_POST_CANARY_DECISION
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_BATCH_ROWS={after_db['batch_rows']}
PRODUCTION_LEDGER_ROWS={after_db['ledger_rows']}
SOURCE_CANDIDATES={latest['source_candidate_count']}
UNOBSERVABLE_ROWS=0
EXACT_LEGACY_OBJECT_PARITY=true
EXACT_LEGACY_UID_ORDER_PARITY=true
PANEL_HOT_HASH_PARITY=true
SINGLE_CYCLE_BOUNDED_CANARY_CONSUMED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

The authorized canary was consumed exactly once. All runtime overrides were removed.""",
    )
    master = replace_section(
        master,
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
SINGLE_NATURAL_CYCLE_EXECUTED=true
RUNTIME_OVERRIDE_ACTIVE=false
```

NEXT_SAFE_STEP={NEXT}""",
    )
    MASTER.write_text(master, encoding="utf-8")

    handoff = HANDOFF.read_text(encoding="utf-8")
    handoff = replace_section(
        handoff,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        f"""PROJECT_STATUS=ACTIVE_ERA55_P0_POST_CANARY_DECISION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_POST_CANARY_DECISION
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_BATCH_ROWS={after_db['batch_rows']}
PRODUCTION_LEDGER_ROWS={after_db['ledger_rows']}
SOURCE_CANDIDATES={latest['source_candidate_count']}
UNOBSERVABLE_ROWS=0
EXACT_LEGACY_OBJECT_PARITY=true
EXACT_LEGACY_UID_ORDER_PARITY=true
PANEL_HOT_HASH_PARITY=true
SINGLE_CYCLE_BOUNDED_CANARY_CONSUMED=true
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
SINGLE_NATURAL_CYCLE_EXECUTED=true
RUNTIME_OVERRIDE_ACTIVE=false
CURRENT_PROBLEM=GENERAL_PRODUCTION_WRITER_ACTIVATION_NOT_AUTHORIZED""",
    )
    handoff = replace_section(
        handoff,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not rerun A9-A17 unless evidence is invalidated.
- Do not execute another bounded canary cycle.
- Do not re-enable writer, runner lock, or hot-path override.
- Do not authorize general production without A18.
- Do not start Option B or close P0 F1.""",
    )
    handoff = replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Complete accounting: `VALIDATED_PRODUCTION_CANARY`.
- Exact legacy parity: `VALIDATED_PRODUCTION_CANARY`.
- One-cycle bounded canary: `COMPLETED_AND_CONSUMED`.
- General production activation: `BLOCKED_PENDING_A18`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff = replace_section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A18 is current.
2. Review the A17 artifact, journal ordering, DB integrity and cleanup state.
3. Decide general writer activation separately from canary success.
4. Do not run another canary.
5. Keep Option B blocked until the production decision is sealed.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac = ALMANAC.read_text(encoding="utf-8")
    marker = "## ERA55A_17 SINGLE NATURAL CYCLE BOUNDED CANARY"
    if marker not in almanac:
        ALMANAC.write_text(
            almanac.rstrip()
            + f"""

---

{marker}

- Status: `CLOSED_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_OK`
- Result: `{RESULT}`
- Production batch rows: `{after_db['batch_rows']}`
- Production ledger rows: `{after_db['ledger_rows']}`
- Source candidates: `{latest['source_candidate_count']}`
- Unobservable rows: `0`
- Exact legacy queue parity: `true`
- Panel hot hash parity: `true`
- Runtime overrides removed: `true`
- Timer state restored: `true`
- General production activation authorized: `false`
- P0 F1 closed: `false`
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
    run(
        ["git", "add", "-f", str(REPORT.relative_to(ROOT))],
        check=True,
    )
    if not git("diff", "--cached", "--name-only"):
        raise RuntimeError("NO_STAGED_CHANGES")
    git("commit", "-m", SUBJECT)
    lifecycle["finalized"] = True
    atexit.unregister(emergency_cleanup)

    print("ERA55A17_SINGLE_CYCLE_CANARY=SUCCESS")
    print("RESULT=" + RESULT)
    print("PRODUCTION_BATCH_ROWS=" + str(after_db["batch_rows"]))
    print("PRODUCTION_LEDGER_ROWS=" + str(after_db["ledger_rows"]))
    print("SOURCE_CANDIDATES=" + str(latest["source_candidate_count"]))
    print("SOURCE_ACCOUNTED=" + str(latest["ledger_rows"]))
    print("UNOBSERVABLE_ROWS=0")
    print("LEGACY_QUEUE_EXACT_OBJECT_PARITY=true")
    print("LEGACY_QUEUE_EXACT_UID_ORDER_PARITY=true")
    print("PANEL_HOT_HASH_PARITY=true")
    print("RUNNER_ORDER_VALID=true")
    print("RUNTIME_DROPIN_REMOVED=true")
    print("TIMER_STATE_RESTORED=true")
    print("SINGLE_CYCLE_BOUNDED_CANARY_CONSUMED=true")
    print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
    print("PRODUCTION_WRITER_ACTIVE=false")
    print("P0_F1_CLOSED=false")
    print("OPTION_B_AUTHORIZED=false")
    print("NEXT_SAFE_STEP=" + NEXT)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    print("ARTIFACT=" + str(ARTIFACT.relative_to(ROOT)))
    shutil.rmtree(backup_root, ignore_errors=True)
    for path in (
        RESULT_PATH,
        INVOCATION_GUARD,
        ORDER_LOG,
        FULL_DISPLAY,
        WRITER_LOCK,
    ):
        if path.exists():
            path.unlink()
    return 0

def main() -> int:
    if os.environ.get("TOKENOSKOBI_A17_ONE_SHOT_HOT", "0").strip() == "1":
        return one_shot_hot()
    return orchestrate()

if __name__ == "__main__":
    raise SystemExit(main())
