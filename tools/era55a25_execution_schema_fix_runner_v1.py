#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path("/root/tokenoskobi_clean_v1")
TARGET = ROOT / "tools/era55a25_p1_option_b_readiness_and_authorization_decision_v1.py"


def load_target():
    spec = importlib.util.spec_from_file_location("era55a25_target", TARGET)
    if spec is None or spec.loader is None:
        raise RuntimeError("A25_TARGET_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixed_database_snapshot(module) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{module.DB}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
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
        batches = [
            {
                "batch_sequence": int(row[0]),
                "batch_uid": str(row[1]),
                "status": str(row[2]),
                "source_candidate_count": int(row[3]),
            }
            for row in connection.execute(
                """
                SELECT
                    rowid AS batch_sequence,
                    batch_uid,
                    status,
                    source_candidate_count
                FROM news_disposition_batches_v2
                ORDER BY rowid
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
            "size_bytes": module.DB.stat().st_size,
            "sha256": module.sha(module.DB),
        }
    finally:
        connection.close()


def main() -> int:
    module = load_target()

    base_systemctl_state = module.systemctl_state

    def fixed_systemctl_state(unit: str) -> dict[str, Any]:
        state = dict(base_systemctl_state(unit))
        if unit == module.SERVICE:
            environment = module.service_environment()
            state["result"] = environment.get("result", "")
            state["exec_main_status"] = environment.get(
                "exec_main_status",
                "",
            )
        return state

    module.systemctl_state = fixed_systemctl_state
    module.database_snapshot = lambda: fixed_database_snapshot(module)

    probe = module.database_snapshot()
    if probe["batch_rows"] < 3:
        raise RuntimeError("A25_FIX_PROBE_BATCH_ROWS_TOO_LOW")
    if probe["ledger_rows"] < 321:
        raise RuntimeError("A25_FIX_PROBE_LEDGER_ROWS_TOO_LOW")
    if probe["integrity_check"] != "ok":
        raise RuntimeError("A25_FIX_PROBE_INTEGRITY_FAILED")

    service = module.systemctl_state(module.SERVICE)
    if service.get("result") != "success":
        raise RuntimeError("A25_FIX_PROBE_SERVICE_RESULT_INVALID")
    if str(service.get("exec_main_status")) != "0":
        raise RuntimeError("A25_FIX_PROBE_SERVICE_STATUS_INVALID")

    print("A25_EXECUTION_SCHEMA_FIX_VALIDATION=SUCCESS")
    print("BATCH_ROWID_BINDING=true")
    print("SERVICE_RESULT_BINDING=true")

    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
