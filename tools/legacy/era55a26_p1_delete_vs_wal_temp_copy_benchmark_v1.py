#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1").resolve()
PRODUCTION_DB = (ROOT / "data/tokenoskobi_clean_v1.sqlite").resolve()

TEMP_PARENT = Path("/tmp/tokenoskobi_era55a26").resolve()
TEMP_PREFIX = "era55a26_"

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

EXPECTED_SOURCE_MODE = "delete"

TRANSACTIONS = 100
ROWS_PER_TRANSACTION = 25
PAYLOAD_BYTES = 512

MIN_FREE_SPACE_MULTIPLIER = 8
P95_MATERIAL_GAIN_PERCENT = 15.0
THROUGHPUT_MATERIAL_GAIN_PERCENT = 20.0

RESULT_NAME = (
    "era55a26_p1_delete_vs_wal_temp_copy_benchmark_v1.json"
)


@dataclass(frozen=True)
class UnitState:
    active: str
    sub: str
    invocation_id: str
    result: str
    exec_main_status: str


def run(
    args: list[str],
    *,
    check: bool = True,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
        timeout=timeout,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def assert_path_is_safe(path: Path) -> None:
    candidate = resolved(path)
    source = resolved(PRODUCTION_DB)
    root = resolved(ROOT)
    parent = resolved(TEMP_PARENT)

    if candidate == source:
        raise RuntimeError("A26_TEMP_EQUALS_PRODUCTION_DB")

    if candidate == root or root in candidate.parents:
        raise RuntimeError("A26_TEMP_INSIDE_REPOSITORY")

    if candidate == parent:
        return

    if parent not in candidate.parents:
        raise RuntimeError("A26_TEMP_OUTSIDE_ALLOWLIST")


def safe_rmtree(path: Path) -> None:
    candidate = resolved(path)
    assert_path_is_safe(candidate)

    if candidate == TEMP_PARENT:
        raise RuntimeError("A26_REFUSE_DELETE_TEMP_PARENT")

    if not candidate.name.startswith(TEMP_PREFIX):
        raise RuntimeError("A26_TEMP_PREFIX_INVALID")

    if candidate.exists():
        shutil.rmtree(candidate)


def unit_state(unit: str) -> UnitState:
    properties = (
        "ActiveState,SubState,InvocationID,Result,ExecMainStatus"
    )

    process = run(
        [
            "systemctl",
            "show",
            unit,
            f"--property={properties}",
            "--no-pager",
        ],
        timeout=30,
    )

    values: dict[str, str] = {}

    for line in process.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value

    return UnitState(
        active=values.get("ActiveState", ""),
        sub=values.get("SubState", ""),
        invocation_id=values.get("InvocationID", ""),
        result=values.get("Result", ""),
        exec_main_status=values.get("ExecMainStatus", ""),
    )


def readonly_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(
        f"file:{path}?mode=ro",
        uri=True,
        timeout=5.0,
    )
    connection.execute("PRAGMA query_only=ON")
    return connection


def database_state(path: Path) -> dict[str, Any]:
    connection = readonly_connection(path)

    try:
        journal_mode = str(
            connection.execute("PRAGMA journal_mode").fetchone()[0]
        ).lower()

        synchronous = int(
            connection.execute("PRAGMA synchronous").fetchone()[0]
        )

        integrity = str(
            connection.execute("PRAGMA integrity_check").fetchone()[0]
        )

        quick = str(
            connection.execute("PRAGMA quick_check").fetchone()[0]
        )

        foreign_keys = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

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

        return {
            "journal_mode": journal_mode,
            "synchronous": synchronous,
            "integrity_check": integrity,
            "quick_check": quick,
            "foreign_key_check_rows": len(foreign_keys),
            "batch_rows": batch_rows,
            "ledger_rows": ledger_rows,
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    finally:
        connection.close()


def sqlite_backup_snapshot(source: Path, destination: Path) -> None:
    assert_path_is_safe(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)

    source_connection = readonly_connection(source)
    target_connection = sqlite3.connect(destination)

    try:
        source_connection.backup(
            target_connection,
            pages=256,
            sleep=0.01,
        )
        target_connection.commit()
    finally:
        target_connection.close()
        source_connection.close()


def clone_file(source: Path, destination: Path) -> None:
    assert_path_is_safe(destination)
    shutil.copy2(source, destination)


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)

    index = int(
        round((len(ordered) - 1) * percentile_value)
    )

    return ordered[index]


def io_counters() -> dict[str, int]:
    counters = {
        "read_bytes": 0,
        "write_bytes": 0,
        "syscr": 0,
        "syscw": 0,
    }

    io_path = Path("/proc/self/io")

    if not io_path.exists():
        return counters

    for line in io_path.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue

        key, raw = line.split(":", 1)

        if key in counters:
            counters[key] = int(raw.strip())

    return counters


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def total_variant_bytes(database: Path) -> int:
    return sum(
        file_size(path)
        for path in (
            database,
            Path(str(database) + "-journal"),
            Path(str(database) + "-wal"),
            Path(str(database) + "-shm"),
        )
    )


def configure_variant(
    database: Path,
    journal_mode: str,
    synchronous: int,
) -> None:
    connection = sqlite3.connect(database, timeout=10.0)

    try:
        selected = str(
            connection.execute(
                f"PRAGMA journal_mode={journal_mode}"
            ).fetchone()[0]
        ).lower()

        if selected != journal_mode:
            raise RuntimeError(
                f"A26_JOURNAL_MODE_NOT_APPLIED:{selected}"
            )

        connection.execute(f"PRAGMA synchronous={synchronous}")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.commit()
    finally:
        connection.close()


def benchmark_variant(
    database: Path,
    journal_mode: str,
    synchronous: int,
) -> dict[str, Any]:
    configure_variant(database, journal_mode, synchronous)

    before_io = io_counters()
    before_bytes = total_variant_bytes(database)

    connection = sqlite3.connect(database, timeout=10.0)
    latencies_ms: list[float] = []
    busy_errors = 0
    io_errors = 0
    corrupt_errors = 0

    payload = "x" * PAYLOAD_BYTES

    try:
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS
            era55a26_benchmark_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                variant TEXT NOT NULL,
                transaction_no INTEGER NOT NULL,
                row_no INTEGER NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        connection.commit()

        start_total = time.perf_counter()

        for transaction_no in range(TRANSACTIONS):
            started = time.perf_counter()

            try:
                connection.execute("BEGIN IMMEDIATE")

                connection.executemany(
                    """
                    INSERT INTO era55a26_benchmark_events (
                        variant,
                        transaction_no,
                        row_no,
                        payload
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    [
                        (
                            journal_mode,
                            transaction_no,
                            row_no,
                            payload,
                        )
                        for row_no in range(
                            ROWS_PER_TRANSACTION
                        )
                    ],
                )

                connection.commit()

            except sqlite3.OperationalError as exc:
                connection.rollback()
                text = str(exc).lower()

                if "busy" in text or "locked" in text:
                    busy_errors += 1
                elif "ioerr" in text or "disk i/o" in text:
                    io_errors += 1
                else:
                    raise

            except sqlite3.DatabaseError as exc:
                connection.rollback()
                text = str(exc).lower()

                if "corrupt" in text:
                    corrupt_errors += 1
                else:
                    raise

            latencies_ms.append(
                (time.perf_counter() - started) * 1000.0
            )

        total_seconds = time.perf_counter() - start_total

        inserted_rows = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM era55a26_benchmark_events
                WHERE variant = ?
                """,
                (journal_mode,),
            ).fetchone()[0]
        )

        checkpoint = None

        if journal_mode == "wal":
            checkpoint_started = time.perf_counter()
            checkpoint_result = connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()

            checkpoint = {
                "duration_ms": (
                    time.perf_counter() - checkpoint_started
                ) * 1000.0,
                "result": list(checkpoint_result),
            }

        connection.commit()

    finally:
        connection.close()

    after_io = io_counters()
    after_bytes = total_variant_bytes(database)

    final_state = database_state(database)

    expected_rows = TRANSACTIONS * ROWS_PER_TRANSACTION

    return {
        "journal_mode": journal_mode,
        "synchronous": synchronous,
        "transactions": TRANSACTIONS,
        "rows_per_transaction": ROWS_PER_TRANSACTION,
        "expected_rows": expected_rows,
        "inserted_rows": inserted_rows,
        "total_seconds": total_seconds,
        "throughput_rows_per_second": (
            inserted_rows / total_seconds
            if total_seconds > 0
            else 0.0
        ),
        "latency_ms": {
            "median": median(latencies_ms),
            "p95": percentile(latencies_ms, 0.95),
            "p99": percentile(latencies_ms, 0.99),
            "maximum": max(latencies_ms),
        },
        "busy_or_locked_errors": busy_errors,
        "sqlite_io_errors": io_errors,
        "sqlite_corrupt_errors": corrupt_errors,
        "file_bytes_before": before_bytes,
        "file_bytes_after": after_bytes,
        "file_bytes_delta": after_bytes - before_bytes,
        "process_io_delta": {
            key: after_io[key] - before_io[key]
            for key in before_io
        },
        "checkpoint": checkpoint,
        "integrity": final_state,
    }


def controlled_kill_worker(
    database: Path,
    journal_mode: str,
    synchronous: int,
) -> None:
    connection = sqlite3.connect(database, timeout=10.0)

    connection.execute(f"PRAGMA journal_mode={journal_mode}")
    connection.execute(f"PRAGMA synchronous={synchronous}")
    connection.execute("PRAGMA busy_timeout=5000")

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS
        era55a26_recovery_probe (
            id INTEGER PRIMARY KEY,
            payload TEXT NOT NULL
        )
        """
    )
    connection.commit()

    connection.execute("BEGIN IMMEDIATE")

    connection.executemany(
        """
        INSERT OR REPLACE INTO era55a26_recovery_probe (
            id,
            payload
        )
        VALUES (?, ?)
        """,
        [(index, "r" * 4096) for index in range(250)],
    )

    os._exit(91)


def recovery_probe(
    database: Path,
    journal_mode: str,
    synchronous: int,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--internal-kill-worker",
        "--database",
        str(database),
        "--journal-mode",
        journal_mode,
        "--synchronous",
        str(synchronous),
    ]

    process = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    state = database_state(database)

    return {
        "worker_return_code": process.returncode,
        "expected_forced_exit_code": 91,
        "integrity_check": state["integrity_check"],
        "quick_check": state["quick_check"],
        "foreign_key_check_rows": (
            state["foreign_key_check_rows"]
        ),
        "sqlite_corrupt_detected": (
            state["integrity_check"] != "ok"
            or state["quick_check"] != "ok"
        ),
        "sqlite_ioerr_detected": (
            "ioerr" in process.stderr.lower()
            or "disk i/o" in process.stderr.lower()
        ),
    }


def material_decision(
    delete_result: dict[str, Any],
    wal_result: dict[str, Any],
) -> dict[str, Any]:
    delete_p95 = delete_result["latency_ms"]["p95"]
    wal_p95 = wal_result["latency_ms"]["p95"]

    delete_throughput = (
        delete_result["throughput_rows_per_second"]
    )
    wal_throughput = (
        wal_result["throughput_rows_per_second"]
    )

    p95_gain = (
        ((delete_p95 - wal_p95) / delete_p95) * 100.0
        if delete_p95 > 0
        else 0.0
    )

    throughput_gain = (
        (
            (wal_throughput - delete_throughput)
            / delete_throughput
        )
        * 100.0
        if delete_throughput > 0
        else 0.0
    )

    correctness_ok = all(
        [
            wal_result["inserted_rows"]
            == wal_result["expected_rows"],
            wal_result["integrity"]["integrity_check"]
            == "ok",
            wal_result["integrity"]["quick_check"] == "ok",
            wal_result["integrity"][
                "foreign_key_check_rows"
            ]
            == 0,
            wal_result["busy_or_locked_errors"] == 0,
            wal_result["sqlite_io_errors"] == 0,
            wal_result["sqlite_corrupt_errors"] == 0,
        ]
    )

    materially_faster = (
        p95_gain >= P95_MATERIAL_GAIN_PERCENT
        or throughput_gain
        >= THROUGHPUT_MATERIAL_GAIN_PERCENT
    )

    decision = (
        "AUTHORIZE_FUTURE_BOUNDED_APPLY_REVIEW"
        if correctness_ok and materially_faster
        else "REJECT_OPTION_B"
        if correctness_ok and not materially_faster
        else "DEFER_OPTION_B"
    )

    return {
        "default_decision": "DEFER_OPTION_B",
        "p95_latency_gain_percent": p95_gain,
        "throughput_gain_percent": throughput_gain,
        "p95_material_threshold_percent": (
            P95_MATERIAL_GAIN_PERCENT
        ),
        "throughput_material_threshold_percent": (
            THROUGHPUT_MATERIAL_GAIN_PERCENT
        ),
        "correctness_ok": correctness_ok,
        "materially_faster": materially_faster,
        "benchmark_recommendation": decision,
        "production_apply_authorized": False,
    }


def disk_guard() -> dict[str, int]:
    TEMP_PARENT.mkdir(parents=True, exist_ok=True)

    usage = shutil.disk_usage(TEMP_PARENT)
    source_size = PRODUCTION_DB.stat().st_size
    required = source_size * MIN_FREE_SPACE_MULTIPLIER

    if usage.free < required:
        raise RuntimeError(
            "A26_INSUFFICIENT_FREE_SPACE:"
            f"required={required}:free={usage.free}"
        )

    return {
        "source_size_bytes": source_size,
        "required_free_bytes": required,
        "actual_free_bytes": usage.free,
    }


def benchmark() -> dict[str, Any]:
    if not PRODUCTION_DB.is_file():
        raise RuntimeError("A26_PRODUCTION_DB_MISSING")

    assert_path_is_safe(TEMP_PARENT)

    production_before = database_state(PRODUCTION_DB)

    if production_before["journal_mode"] != EXPECTED_SOURCE_MODE:
        raise RuntimeError(
            "A26_UNEXPECTED_PRODUCTION_JOURNAL_MODE:"
            + production_before["journal_mode"]
        )

    service_before = unit_state(SERVICE)
    timer_before = unit_state(TIMER)
    disk = disk_guard()

    temp_root = Path(
        tempfile.mkdtemp(
            prefix=TEMP_PREFIX,
            dir=TEMP_PARENT,
        )
    ).resolve()

    assert_path_is_safe(temp_root)

    snapshot = temp_root / "source_snapshot.sqlite"
    delete_db = temp_root / "delete_variant.sqlite"
    wal_db = temp_root / "wal_variant.sqlite"

    try:
        sqlite_backup_snapshot(PRODUCTION_DB, snapshot)

        snapshot_state = database_state(snapshot)

        if snapshot_state["integrity_check"] != "ok":
            raise RuntimeError(
                "A26_SNAPSHOT_INTEGRITY_FAILED"
            )

        if snapshot_state["quick_check"] != "ok":
            raise RuntimeError(
                "A26_SNAPSHOT_QUICK_CHECK_FAILED"
            )

        if snapshot_state["foreign_key_check_rows"] != 0:
            raise RuntimeError(
                "A26_SNAPSHOT_FOREIGN_KEY_FAILED"
            )

        clone_file(snapshot, delete_db)
        clone_file(snapshot, wal_db)

        synchronous = snapshot_state["synchronous"]

        delete_result = benchmark_variant(
            delete_db,
            "delete",
            synchronous,
        )

        wal_result = benchmark_variant(
            wal_db,
            "wal",
            synchronous,
        )

        delete_recovery = recovery_probe(
            delete_db,
            "delete",
            synchronous,
        )

        wal_recovery = recovery_probe(
            wal_db,
            "wal",
            synchronous,
        )

        service_after = unit_state(SERVICE)
        timer_after = unit_state(TIMER)
        production_after = database_state(PRODUCTION_DB)

        if service_after.invocation_id != service_before.invocation_id:
            raise RuntimeError(
                "A26_SERVICE_INVOCATION_CHANGED"
            )

        if timer_after.invocation_id != timer_before.invocation_id:
            raise RuntimeError(
                "A26_TIMER_INVOCATION_CHANGED"
            )

        if production_after["sha256"] != production_before["sha256"]:
            raise RuntimeError(
                "A26_PRODUCTION_DB_CHANGED_DURING_BENCHMARK"
            )

        if production_after["journal_mode"] != EXPECTED_SOURCE_MODE:
            raise RuntimeError(
                "A26_PRODUCTION_JOURNAL_MODE_CHANGED"
            )

        decision = material_decision(
            delete_result,
            wal_result,
        )

        if (
            wal_recovery["sqlite_corrupt_detected"]
            or wal_recovery["sqlite_ioerr_detected"]
        ):
            decision["benchmark_recommendation"] = (
                "DEFER_OPTION_B"
            )
            decision["correctness_ok"] = False

        return {
            "schema": (
                "era55a26_p1_delete_vs_wal_"
                "temp_copy_benchmark_v1"
            ),
            "status": "COMPLETED_TEMP_COPY_ONLY",
            "production_mutation": False,
            "production_apply_authorized": False,
            "source": {
                "path": str(PRODUCTION_DB),
                "opened_read_only": True,
                "state_before": production_before,
                "state_after": production_after,
            },
            "infrastructure": {
                "service_before": service_before.__dict__,
                "service_after": service_after.__dict__,
                "timer_before": timer_before.__dict__,
                "timer_after": timer_after.__dict__,
            },
            "disk_guard": disk,
            "snapshot": snapshot_state,
            "delete_variant": delete_result,
            "wal_variant": wal_result,
            "delete_recovery": delete_recovery,
            "wal_recovery": wal_recovery,
            "decision": decision,
        }
    finally:
        safe_rmtree(temp_root)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the isolated temp-copy benchmark.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp") / RESULT_NAME,
    )

    parser.add_argument(
        "--internal-kill-worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--database",
        type=Path,
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--journal-mode",
        choices=("delete", "wal"),
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--synchronous",
        type=int,
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()

    if args.internal_kill_worker:
        if (
            args.database is None
            or args.journal_mode is None
            or args.synchronous is None
        ):
            raise RuntimeError(
                "A26_INTERNAL_WORKER_ARGUMENTS_MISSING"
            )

        assert_path_is_safe(args.database)

        controlled_kill_worker(
            args.database,
            args.journal_mode,
            args.synchronous,
        )

        return 91

    if not args.run:
        print("A26_TOOL_BUILD=READY")
        print("A26_BENCHMARK_EXECUTED=false")
        print("USE_EXPLICIT_FLAG=--run")
        print("PRODUCTION_MUTATION=false")
        return 0

    output = resolved(args.output)

    if output == PRODUCTION_DB:
        raise RuntimeError(
            "A26_OUTPUT_COLLIDES_WITH_PRODUCTION_DB"
        )

    result = benchmark()

    output.parent.mkdir(parents=True, exist_ok=True)

    temp_output = output.with_suffix(
        output.suffix + ".tmp"
    )

    temp_output.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    os.replace(temp_output, output)

    print("ERA55A26_TEMP_COPY_BENCHMARK=SUCCESS")
    print("PRODUCTION_MUTATION=false")
    print("PRODUCTION_APPLY_AUTHORIZED=false")
    print(
        "BENCHMARK_RECOMMENDATION="
        + result["decision"]["benchmark_recommendation"]
    )
    print("ARTIFACT=" + str(output))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
