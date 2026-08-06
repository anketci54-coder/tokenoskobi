#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

POLICY_VERSION = "POSTCOMMIT_ARCHIVE_TRIGGER_ROLLBACK_GUARD_V1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _database_counts(connection: sqlite3.Connection) -> dict[str, int]:
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
    }


def rollback_committed_batch(
    db_path: str | Path,
    batch_uid: str,
    *,
    original_error: str,
    archive_location: str | None = None,
    inject_failure_stage: str | None = None,
) -> dict[str, Any]:
    """Rollback one committed batch while satisfying archive-before-delete triggers.

    The function never hides the downstream/original error. It returns both the
    original failure and the rollback result. Test-only failure injection is
    supported to prove transaction rollback and error exposure.
    """
    database = Path(db_path)
    location = archive_location or (
        "rollback://postcommit/" + batch_uid
    )
    started_at = utc_now()
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row

    before: dict[str, int] | None = None
    batch_before: dict[str, Any] | None = None
    ledger_rows_before: int | None = None

    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        before = _database_counts(connection)

        row = connection.execute(
            """
            SELECT
                batch_uid,
                status,
                retention_expires_at_utc,
                archived_at_utc,
                archive_location
            FROM news_disposition_batches_v2
            WHERE batch_uid=?
            """,
            (batch_uid,),
        ).fetchone()

        if row is None:
            return {
                "policy_version": POLICY_VERSION,
                "status": "ROLLBACK_BATCH_NOT_FOUND",
                "batch_uid": batch_uid,
                "original_error": original_error,
                "rollback_error": None,
                "started_at_utc": started_at,
                "finished_at_utc": utc_now(),
                "database_before": before,
                "database_after": before,
                "transaction_rolled_back": False,
                "batch_deleted": False,
                "ledger_rows_deleted": 0,
            }

        batch_before = dict(row)
        ledger_rows_before = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM news_disposition_ledger_v2
                WHERE batch_uid=?
                """,
                (batch_uid,),
            ).fetchone()[0]
        )

        if row["status"] != "COMMITTED":
            raise RuntimeError(
                "ROLLBACK_REQUIRES_COMMITTED_BATCH:"
                + str(row["status"])
            )

        connection.execute("BEGIN IMMEDIATE")
        archived_at = utc_now()
        connection.execute(
            """
            UPDATE news_disposition_batches_v2
            SET
                status='ARCHIVED',
                archived_at_utc=?,
                archive_location=?,
                retention_expires_at_utc='1970-01-01T00:00:00+00:00'
            WHERE batch_uid=?
              AND status='COMMITTED'
            """,
            (archived_at, location, batch_uid),
        )

        if connection.total_changes < 1:
            raise RuntimeError("ROLLBACK_ARCHIVE_TRANSITION_NOT_APPLIED")

        if inject_failure_stage == "AFTER_ARCHIVE_TRANSITION":
            raise RuntimeError(
                "INJECTED_ROLLBACK_FAILURE_AFTER_ARCHIVE_TRANSITION"
            )

        deleted_ledger = connection.execute(
            "DELETE FROM news_disposition_ledger_v2 WHERE batch_uid=?",
            (batch_uid,),
        ).rowcount

        if deleted_ledger != ledger_rows_before:
            raise RuntimeError(
                "ROLLBACK_LEDGER_DELETE_COUNT_MISMATCH:"
                + str(deleted_ledger)
                + ":"
                + str(ledger_rows_before)
            )

        if inject_failure_stage == "AFTER_LEDGER_DELETE":
            raise RuntimeError(
                "INJECTED_ROLLBACK_FAILURE_AFTER_LEDGER_DELETE"
            )

        deleted_batch = connection.execute(
            "DELETE FROM news_disposition_batches_v2 WHERE batch_uid=?",
            (batch_uid,),
        ).rowcount

        if deleted_batch != 1:
            raise RuntimeError(
                "ROLLBACK_BATCH_DELETE_COUNT_MISMATCH:"
                + str(deleted_batch)
            )

        if inject_failure_stage == "BEFORE_COMMIT":
            raise RuntimeError(
                "INJECTED_ROLLBACK_FAILURE_BEFORE_COMMIT"
            )

        connection.commit()
        after = _database_counts(connection)
        target_batch_rows = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM news_disposition_batches_v2
                WHERE batch_uid=?
                """,
                (batch_uid,),
            ).fetchone()[0]
        )
        target_ledger_rows = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM news_disposition_ledger_v2
                WHERE batch_uid=?
                """,
                (batch_uid,),
            ).fetchone()[0]
        )

        if target_batch_rows != 0 or target_ledger_rows != 0:
            raise RuntimeError("ROLLBACK_TARGET_ROWS_STILL_PRESENT")

        return {
            "policy_version": POLICY_VERSION,
            "status": "ROLLED_BACK_ARCHIVE_TRIGGER_SAFE",
            "batch_uid": batch_uid,
            "original_error": original_error,
            "rollback_error": None,
            "started_at_utc": started_at,
            "finished_at_utc": utc_now(),
            "archive_location": location,
            "batch_before": batch_before,
            "database_before": before,
            "database_after": after,
            "transaction_rolled_back": False,
            "archive_transition_applied": True,
            "batch_deleted": True,
            "ledger_rows_deleted": deleted_ledger,
            "target_batch_rows_after": target_batch_rows,
            "target_ledger_rows_after": target_ledger_rows,
        }
    except Exception as exc:
        connection.rollback()
        after_failure = _database_counts(connection)
        target = connection.execute(
            """
            SELECT status, archived_at_utc, archive_location,
                   retention_expires_at_utc
            FROM news_disposition_batches_v2
            WHERE batch_uid=?
            """,
            (batch_uid,),
        ).fetchone()
        target_ledger_rows = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM news_disposition_ledger_v2
                WHERE batch_uid=?
                """,
                (batch_uid,),
            ).fetchone()[0]
        )
        return {
            "policy_version": POLICY_VERSION,
            "status": "ROLLBACK_FAILED_TRANSACTION_REVERTED",
            "batch_uid": batch_uid,
            "original_error": original_error,
            "rollback_error": f"{type(exc).__name__}:{exc}",
            "started_at_utc": started_at,
            "finished_at_utc": utc_now(),
            "batch_before": batch_before,
            "database_before": before,
            "database_after": after_failure,
            "transaction_rolled_back": True,
            "batch_deleted": False,
            "ledger_rows_deleted": 0,
            "target_batch_after": dict(target) if target is not None else None,
            "target_ledger_rows_after": target_ledger_rows,
            "injected_failure_stage": inject_failure_stage,
        }
    finally:
        connection.close()


def require_success(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("status") != "ROLLED_BACK_ARCHIVE_TRIGGER_SAFE":
        raise RuntimeError(
            "POSTCOMMIT_ROLLBACK_FAILED:"
            + str(result.get("rollback_error") or result.get("status"))
            + ":ORIGINAL_ERROR:"
            + str(result.get("original_error"))
        )
    return result
