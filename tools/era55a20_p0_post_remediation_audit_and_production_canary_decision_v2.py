#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sqlite3
import sys
sys.dont_write_bytecode = True
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
V1 = ROOT / "tools/era55a20_p0_post_remediation_audit_and_production_canary_decision_v1.py"


def load_v1():
    spec = importlib.util.spec_from_file_location("era55a20_v1", V1)
    if spec is None or spec.loader is None:
        raise RuntimeError("A20_V1_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tolerant_database_state(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        latest_row = connection.execute(
            """
            SELECT rowid, batch_uid, status, policy_version,
                   source_candidate_count, admitted_count, overflow_count
            FROM news_disposition_batches_v2
            ORDER BY rowid DESC
            LIMIT 1
            """
        ).fetchone()
        latest = None
        if latest_row is not None:
            uid = str(latest_row[1])
            latest = {
                "batch_sequence": int(latest_row[0]),
                "batch_uid": uid,
                "status": str(latest_row[2]),
                "policy_version": str(latest_row[3]),
                "source_candidate_count": int(latest_row[4]),
                "admitted_count": int(latest_row[5]),
                "overflow_count": int(latest_row[6]),
                "ledger_rows": int(
                    connection.execute(
                        "SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?",
                        (uid,),
                    ).fetchone()[0]
                ),
            }
        triggers = [
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
        ]
        return {
            "batch_rows": int(
                connection.execute(
                    "SELECT COUNT(*) FROM news_disposition_batches_v2"
                ).fetchone()[0]
            ),
            "ledger_rows": int(
                connection.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2"
                ).fetchone()[0]
            ),
            "latest_batch": latest,
            "integrity_check": str(
                connection.execute("PRAGMA integrity_check").fetchone()[0]
            ),
            "quick_check": str(
                connection.execute("PRAGMA quick_check").fetchone()[0]
            ),
            "foreign_key_check_rows": len(
                connection.execute("PRAGMA foreign_key_check").fetchall()
            ),
            "triggers": triggers,
        }
    finally:
        connection.close()


def main() -> int:
    module = load_v1()
    module.database_state = tolerant_database_state
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
