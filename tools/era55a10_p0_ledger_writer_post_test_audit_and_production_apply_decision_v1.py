#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
sys.dont_write_bytecode = True
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Dict

ROOT = Path("/root/tokenoskobi_clean_v1")
PROD_DB = ROOT / "data" / "tokenoskobi_clean_v1.sqlite"
GUARD = ROOT / "tools" / "news_ledger_recovery_guard_v1.py"
RUNNER = ROOT / "tools" / "news_radar_refresh_runner_v1.py"
CONTRACT = ROOT / "runtime" / "state" / "hot_intelligence_ingress_gateway_v1.json"
RECOVERY_STATE_PROD = (
    ROOT / "runtime" / "state" / "news_ledger_recovery_state_v1.json"
)
RUNBOOK = (
    ROOT
    / "docs"
    / "runbooks"
    / "ERA55A10_LEDGER_WRITER_ROLLBACK_RUNBOOK.md"
)
ARTIFACT = (
    ROOT
    / "data"
    / "control"
    / "era55a10_p0_ledger_writer_remediation_proof_package_v1.json"
)
REPORT = (
    ROOT
    / "reports"
    / "LATEST_ERA55A10_P0_LEDGER_WRITER_REMEDIATION_PROOF_PACKAGE.md"
)
EXPECTED_PARENT = "PREP_HEAD_REPLACED_BY_WRAPPER"
PYTHON_BIN = os.environ.get("TOKENOSKOBI_PYTHON_BIN", "/usr/bin/python3")
COMMIT_SUBJECT = (
    "ERA55A10_REMEDIATION_PROOF | OK | PRODUCTION_AUTH_REVIEW_PENDING"
)

EXPECTED_PRE_A10_RUNNER_SHA256 = '76794993a67cc50f7cd8d3c84fe3cc1a02485eea08688f35a4c7718e81d18500'
GUARD_SOURCE = r'''
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sqlite3
import sys
sys.dont_write_bytecode = True
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

SCHEMA_VERSION = "1.0"
DEFAULT_MAX_ATTEMPTS = 3
REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "gateway",
    "generated_at_utc",
    "mode",
    "sources",
    "authority",
    "source_health",
    "hot_queue_count",
    "hot_queue",
}
REQUIRED_HOT_ITEM_KEYS = {
    "hot_uid",
    "lane",
    "event_uid",
    "news_uid",
    "title",
    "hits",
    "published_at_utc",
    "source_uid",
    "priority_score",
    "gateway_decision",
    "authority",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"JSON_ROOT_NOT_OBJECT:{path}")
    return raw


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    fd = os.open(str(path), flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_atomic_write_bytes(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        with tmp.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        _fsync_directory(path.parent)
    finally:
        if tmp.exists():
            tmp.unlink()
    persisted = path.read_bytes()
    if persisted != data:
        raise IOError(f"DURABLE_WRITE_READBACK_MISMATCH:{path}")
    return sha256_bytes(persisted)


def durable_atomic_write_json(path: Path, payload: Dict[str, Any]) -> str:
    return durable_atomic_write_bytes(path, canonical_json_bytes(payload))


@contextmanager
def single_instance_lock(lock_path: Path) -> Iterator[Optional[Any]]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield None
            return
        handle.seek(0)
        handle.truncate()
        handle.write(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "acquired_at_utc": utc_now(),
                },
                sort_keys=True,
            )
            + "\n"
        )
        handle.flush()
        os.fsync(handle.fileno())
        yield handle
    finally:
        try:
            if not handle.closed:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _default_state() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at_utc": utc_now(),
        "batches": {},
    }


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return _default_state()
    state = read_json(path)
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("RECOVERY_STATE_SCHEMA_MISMATCH")
    if not isinstance(state.get("batches"), dict):
        raise ValueError("RECOVERY_STATE_BATCHES_INVALID")
    return state


def save_state(path: Path, state: Dict[str, Any]) -> str:
    state["updated_at_utc"] = utc_now()
    return durable_atomic_write_json(path, state)


def connect_ro(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def load_latest_committed_batch(
    db_path: Path,
    batch_sequence: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    conn = connect_ro(db_path)
    try:
        if batch_sequence is None:
            row = conn.execute(
                """
                SELECT rowid AS batch_sequence, *
                FROM news_disposition_batches_v2
                WHERE status='COMMITTED'
                ORDER BY rowid DESC
                LIMIT 1
                """
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT rowid AS batch_sequence, *
                FROM news_disposition_batches_v2
                WHERE status='COMMITTED' AND rowid=?
                LIMIT 1
                """,
                (int(batch_sequence),),
            ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def load_admitted_items(db_path: Path, batch_uid: str) -> list[Dict[str, Any]]:
    conn = connect_ro(db_path)
    try:
        rows = conn.execute(
            """
            SELECT payload_json
            FROM news_disposition_ledger_v2
            WHERE batch_uid=? AND disposition='ADMITTED'
            ORDER BY candidate_rank ASC, source_index ASC
            """,
            (batch_uid,),
        ).fetchall()
    finally:
        conn.close()

    items: list[Dict[str, Any]] = []
    for row in rows:
        item = json.loads(str(row["payload_json"]))
        if not isinstance(item, dict):
            raise ValueError("LEDGER_PAYLOAD_NOT_OBJECT")
        missing = REQUIRED_HOT_ITEM_KEYS - set(item)
        if missing:
            raise ValueError(
                "LEDGER_PAYLOAD_CONTRACT_MISSING:" + ",".join(sorted(missing))
            )
        items.append(item)
    return items


def queue_hash(queue: list[Dict[str, Any]]) -> str:
    return sha256_bytes(canonical_json_bytes(queue))


def _default_contract() -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "gateway": "HOT_INTELLIGENCE_INGRESS_GATEWAY_V1",
        "generated_at_utc": utc_now(),
        "mode": "NOAPI_READONLY_REVIEW_GATEWAY",
        "sources": {
            "display_json": "",
            "summary_json": "",
        },
        "authority": {
            "db_write": False,
            "db_schema_change": False,
            "hunter_authorized": False,
            "trade_signal": False,
            "paper_signal": False,
            "live_trade": False,
            "execution_authority": False,
            "service_change": False,
            "timer_change": False,
            "network_call": False,
            "external_api_call": False,
        },
        "source_health": {
            "display_exists": False,
            "summary_exists": False,
            "display_source_authority_ok": False,
            "summary_parse_errors": 0,
            "summary_duplicate_event_uids": 0,
            "summary_unsafe_events": 0,
        },
        "hot_queue_count": 0,
        "hot_queue": [],
    }


def build_output_payload(
    batch: Dict[str, Any],
    items: list[Dict[str, Any]],
    contract_seed_path: Optional[Path],
) -> Dict[str, Any]:
    seed = {}
    if contract_seed_path and contract_seed_path.exists():
        seed = read_json(contract_seed_path)

    payload = _default_contract()
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key in seed:
            payload[key] = seed[key]

    payload["generated_at_utc"] = utc_now()
    payload["hot_queue_count"] = len(items)
    payload["hot_queue"] = items
    payload["ledger_publish"] = {
        "output_batch_uid": str(batch["batch_uid"]),
        "output_batch_sequence": int(batch["batch_sequence"]),
        "source_snapshot_hash": str(batch["source_snapshot_hash"]),
        "queue_output_hash": queue_hash(items),
        "recovered_at_utc": utc_now(),
    }
    return payload


def inspect_target(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    payload = read_json(path)
    meta = payload.get("ledger_publish")
    if not isinstance(meta, dict):
        return {
            "exists": True,
            "has_ledger_publish": False,
            "payload": payload,
        }
    try:
        seq = int(meta["output_batch_sequence"])
        uid = str(meta["output_batch_uid"])
        qhash = str(meta["queue_output_hash"])
        snapshot_hash = str(meta["source_snapshot_hash"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("TARGET_LEDGER_METADATA_INVALID") from exc
    return {
        "exists": True,
        "has_ledger_publish": True,
        "batch_sequence": seq,
        "batch_uid": uid,
        "queue_output_hash": qhash,
        "source_snapshot_hash": snapshot_hash,
        "payload": payload,
    }


def _state_entry(state: Dict[str, Any], batch_uid: str) -> Dict[str, Any]:
    batches = state["batches"]
    entry = batches.setdefault(
        batch_uid,
        {
            "attempt_count": 0,
            "consecutive_failures": 0,
            "status": "PENDING",
            "first_attempt_at_utc": None,
            "last_attempt_at_utc": None,
            "last_error": None,
            "last_success_at_utc": None,
            "last_output_hash": None,
        },
    )
    return entry


def recover_committed_batch(
    db_path: Path,
    output_path: Path,
    state_path: Path,
    *,
    contract_seed_path: Optional[Path] = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    batch_sequence: Optional[int] = None,
) -> Dict[str, Any]:
    batch = load_latest_committed_batch(db_path, batch_sequence)
    if batch is None:
        return {
            "status": "NO_COMMITTED_BATCH",
            "recovery_executed": False,
        }

    batch_uid = str(batch["batch_uid"])
    batch_seq = int(batch["batch_sequence"])
    state = load_state(state_path)
    entry = _state_entry(state, batch_uid)

    if entry.get("status") == "QUARANTINED":
        print(
            f"[RECOVERY_QUARANTINED] batch_uid={batch_uid} "
            f"attempts={entry.get('attempt_count')}",
            flush=True,
        )
        return {
            "status": "QUARANTINED",
            "batch_uid": batch_uid,
            "batch_sequence": batch_seq,
            "recovery_executed": False,
            "attempt_count": int(entry.get("attempt_count") or 0),
        }

    target = inspect_target(output_path)
    if target.get("has_ledger_publish"):
        target_seq = int(target["batch_sequence"])
        target_uid = str(target["batch_uid"])
        if target_seq > batch_seq:
            print(
                f"[RECOVERY_STALE_BATCH_BLOCKED] recovery_seq={batch_seq} "
                f"target_seq={target_seq}",
                flush=True,
            )
            return {
                "status": "TARGET_NEWER_THAN_RECOVERY",
                "batch_uid": batch_uid,
                "batch_sequence": batch_seq,
                "target_batch_sequence": target_seq,
                "target_batch_uid": target_uid,
                "recovery_executed": False,
            }
        if target_seq == batch_seq and target_uid != batch_uid:
            raise RuntimeError("BATCH_SEQUENCE_UID_COLLISION")

    if target.get("has_ledger_publish"):
        target_payload = target.get("payload") or {}
        target_queue = target_payload.get("hot_queue")
        target_queue_count = target_payload.get("hot_queue_count")
        target_queue_hash_valid = (
            isinstance(target_queue, list)
            and str(target["queue_output_hash"]) == queue_hash(target_queue)
        )
        if (
            int(target["batch_sequence"]) == batch_seq
            and str(target["batch_uid"]) == batch_uid
            and str(target["source_snapshot_hash"])
            == str(batch["source_snapshot_hash"])
            and int(target_queue_count or 0) == int(batch["admitted_count"])
            and target_queue_hash_valid
        ):
            entry["status"] = "RECOVERED"
            entry["consecutive_failures"] = 0
            entry["last_error"] = None
            entry["last_success_at_utc"] = utc_now()
            entry["last_output_hash"] = sha256_bytes(output_path.read_bytes())
            save_state(state_path, state)
            return {
                "status": "OUTPUT_ALREADY_MATCHED",
                "batch_uid": batch_uid,
                "batch_sequence": batch_seq,
                "recovery_executed": False,
                "output_hash": entry["last_output_hash"],
            }

    previous_status = str(entry.get("status") or "PENDING")
    if previous_status == "RECOVERED":
        print(
            f"[RECOVERY_EXTERNAL_DRIFT_SUSPECTED] batch_uid={batch_uid} "
            f"target_exists={bool(target.get('exists'))}",
            flush=True,
        )

    now = utc_now()
    entry["attempt_count"] = int(entry.get("attempt_count") or 0) + 1
    entry["last_attempt_at_utc"] = now
    if entry.get("first_attempt_at_utc") is None:
        entry["first_attempt_at_utc"] = now
    entry["status"] = "ATTEMPTING"
    save_state(state_path, state)

    print(
        f"[RECOVERY_EVENT_TRIGGERED] batch_uid={batch_uid} "
        f"batch_sequence={batch_seq} attempt={entry['attempt_count']}",
        flush=True,
    )

    try:
        items = load_admitted_items(db_path, batch_uid)
        payload = build_output_payload(batch, items, contract_seed_path)
        expected_hash = sha256_bytes(canonical_json_bytes(payload))
        expected_queue_hash = str(payload["ledger_publish"]["queue_output_hash"])
        persisted_hash = durable_atomic_write_json(output_path, payload)
        if persisted_hash != expected_hash:
            raise IOError("OUTPUT_HASH_MISMATCH_AFTER_DURABLE_WRITE")
        target_after = inspect_target(output_path)
        if (
            not target_after.get("has_ledger_publish")
            or int(target_after["batch_sequence"]) != batch_seq
            or str(target_after["batch_uid"]) != batch_uid
            or str(target_after["queue_output_hash"]) != expected_queue_hash
        ):
            raise IOError("OUTPUT_METADATA_READBACK_MISMATCH")

        entry["status"] = "RECOVERED"
        entry["consecutive_failures"] = 0
        entry["last_error"] = None
        entry["last_success_at_utc"] = utc_now()
        entry["last_output_hash"] = persisted_hash
        save_state(state_path, state)
        print(
            f"[RECOVERY_EVENT_COMPLETED] batch_uid={batch_uid} "
            f"output_hash={persisted_hash}",
            flush=True,
        )
        return {
            "status": "RECOVERED",
            "batch_uid": batch_uid,
            "batch_sequence": batch_seq,
            "recovery_executed": True,
            "output_hash": persisted_hash,
            "queue_output_hash": expected_queue_hash,
            "attempt_count": int(entry["attempt_count"]),
        }
    except BaseException as exc:
        entry["consecutive_failures"] = (
            int(entry.get("consecutive_failures") or 0) + 1
        )
        entry["last_error"] = f"{type(exc).__name__}:{exc}"
        if entry["consecutive_failures"] >= int(max_attempts):
            entry["status"] = "QUARANTINED"
            print(
                f"[RECOVERY_QUARANTINED] batch_uid={batch_uid} "
                f"attempts={entry['attempt_count']} error={entry['last_error']}",
                flush=True,
            )
        else:
            entry["status"] = "RETRY_PENDING"
            print(
                f"[RECOVERY_RETRY_PENDING] batch_uid={batch_uid} "
                f"attempts={entry['attempt_count']} error={entry['last_error']}",
                flush=True,
            )
        save_state(state_path, state)
        return {
            "status": str(entry["status"]),
            "batch_uid": batch_uid,
            "batch_sequence": batch_seq,
            "recovery_executed": False,
            "attempt_count": int(entry["attempt_count"]),
            "consecutive_failures": int(entry["consecutive_failures"]),
            "error": str(entry["last_error"]),
        }


def cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--state-path", required=True)
    parser.add_argument("--contract-seed-path")
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--batch-sequence", type=int)
    args = parser.parse_args()

    result = recover_committed_batch(
        Path(args.db_path),
        Path(args.output_path),
        Path(args.state_path),
        contract_seed_path=(
            Path(args.contract_seed_path)
            if args.contract_seed_path
            else None
        ),
        max_attempts=args.max_attempts,
        batch_sequence=args.batch_sequence,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
'''
RUNNER_SOURCE = r'''
#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys
sys.dont_write_bytecode = True

from news_ledger_recovery_guard_v1 import (
    recover_committed_batch,
    single_instance_lock,
)

DEFAULT_ROOT = Path("/root/tokenoskobi_clean_v1")
PYTHON_BIN = os.environ.get("TOKENOSKOBI_PYTHON_BIN", "/usr/bin/python3")
ROOT = Path(os.environ.get("TOKENOSKOBI_ROOT", str(DEFAULT_ROOT)))
ORIGINAL = Path(
    os.environ.get(
        "TOKENOSKOBI_NEWS_ORIGINAL_PATH",
        str(
            ROOT
            / "tools"
            / "news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py"
        ),
    )
)
HELPER = Path(
    os.environ.get(
        "TOKENOSKOBI_NEWS_DERIVED_HELPER_PATH",
        str(ROOT / "tools" / "news_derived_layer_refresher_v1.py"),
    )
)
HOT = Path(
    os.environ.get(
        "TOKENOSKOBI_NEWS_HOT_PATH",
        str(
            ROOT
            / "tools"
            / "post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.py"
        ),
    )
)
DB = Path(
    os.environ.get(
        "TOKENOSKOBI_DB_PATH",
        str(ROOT / "data" / "tokenoskobi_clean_v1.sqlite"),
    )
)
HOT_OUTPUT = Path(
    os.environ.get(
        "TOKENOSKOBI_HOT_OUTPUT_PATH",
        str(ROOT / "runtime" / "state" / "hot_intelligence_ingress_gateway_v1.json"),
    )
)
RECOVERY_STATE = Path(
    os.environ.get(
        "TOKENOSKOBI_LEDGER_RECOVERY_STATE_PATH",
        str(ROOT / "runtime" / "state" / "news_ledger_recovery_state_v1.json"),
    )
)
RECOVERY_CONTRACT_SEED = Path(
    os.environ.get(
        "TOKENOSKOBI_RECOVERY_CONTRACT_SEED_PATH",
        str(HOT_OUTPUT),
    )
)
RUNNER_LOCK = Path(
    os.environ.get(
        "TOKENOSKOBI_RUNNER_LOCK_PATH",
        str(ROOT / "runtime" / "state" / "news_radar_refresh_runner_v1.lock"),
    )
)
ORDER_LOG = os.environ.get("TOKENOSKOBI_A10_ORDER_LOG")


def env_true(name: str) -> bool:
    return os.environ.get(name, "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def append_order(marker: str) -> None:
    if not ORDER_LOG:
        return
    path = Path(ORDER_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(marker + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def run_hot() -> int:
    append_order("HOT_START")
    result = subprocess.run(
        [PYTHON_BIN, str(HOT), "--runtime-refresh"],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    ).returncode
    append_order(f"HOT_END:{result}")
    return result


def run_recovery() -> dict:
    result = recover_committed_batch(
        DB,
        HOT_OUTPUT,
        RECOVERY_STATE,
        contract_seed_path=(
            RECOVERY_CONTRACT_SEED
            if RECOVERY_CONTRACT_SEED.exists()
            else None
        ),
        max_attempts=int(
            os.environ.get(
                "TOKENOSKOBI_LEDGER_RECOVERY_MAX_ATTEMPTS",
                "3",
            )
        ),
    )
    append_order("RECOVERY_DONE:" + str(result.get("status")))
    print(
        "[LEDGER_RECOVERY_RESULT] "
        + json.dumps(result, ensure_ascii=False, sort_keys=True),
        flush=True,
    )
    return result


def _run_pipeline() -> int:
    writer_enabled = env_true("TOKENOSKOBI_LEDGER_WRITER_ENABLED")
    hot_blocked = False

    if writer_enabled:
        recovery = run_recovery()
        recovery_status = str(recovery.get("status") or "UNKNOWN")

        if recovery_status in {"RETRY_PENDING", "ERROR"}:
            print(
                "[LEDGER_RECOVERY_FAIL_CLOSED] "
                f"status={recovery_status}",
                flush=True,
            )
            return 75

        if recovery_status == "QUARANTINED":
            hot_blocked = True
            print(
                "[LEDGER_RECOVERY_QUARANTINE_ACTIVE] "
                "raw_and_derived_continue hot_publish_blocked=true",
                flush=True,
            )

    if "--recovery-only" in sys.argv[1:]:
        return 0

    if "--hot-only" in sys.argv[1:]:
        if hot_blocked:
            print(
                "[HOT_PUBLISH_SKIPPED_DUE_TO_QUARANTINE]",
                flush=True,
            )
            return 0
        return run_hot()

    append_order("RAW_START")
    raw = subprocess.run(
        [PYTHON_BIN, str(ORIGINAL)] + sys.argv[1:],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    append_order(f"RAW_END:{raw.returncode}")
    if raw.returncode != 0:
        return raw.returncode

    append_order("DERIVED_START")
    derived = subprocess.run(
        [
            PYTHON_BIN,
            str(HELPER),
            "--db-path",
            str(DB),
            "--write",
            "--stage",
            "NEWS_SYSTEMD_TIMER_DERIVED_REFRESH",
        ],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    append_order(f"DERIVED_END:{derived.returncode}")
    if derived.returncode != 0:
        return derived.returncode

    if hot_blocked:
        print(
            "[HOT_PUBLISH_SKIPPED_DUE_TO_QUARANTINE]",
            flush=True,
        )
        return 0

    return run_hot()


def main() -> int:
    if env_true("TOKENOSKOBI_RUNNER_LOCK_ENABLED"):
        with single_instance_lock(RUNNER_LOCK) as lock_handle:
            if lock_handle is None:
                print(
                    "[RUNNER_ALREADY_ACTIVE] "
                    f"lock_path={RUNNER_LOCK}",
                    flush=True,
                )
                return 0
            append_order("LOCK_ACQUIRED")
            return _run_pipeline()

    return _run_pipeline()


if __name__ == "__main__":
    raise SystemExit(main())
'''
RUNBOOK_SOURCE = r'''
# ERA55A10 Ledger Writer Rollback Runbook

## Scope

This runbook covers only the ERA55 P0 disposition-ledger writer and recovery shields. It does not authorize trade, wallet, signing, external API, schema expansion, Option B, service activation, or timer mutation.

## Feature Flags

The remediation code is inert unless explicitly enabled by the service environment:

```text
TOKENOSKOBI_LEDGER_WRITER_ENABLED=1
TOKENOSKOBI_RUNNER_LOCK_ENABLED=1
TOKENOSKOBI_LEDGER_RECOVERY_MAX_ATTEMPTS=3
```

Removing or setting the first two flags to `0` disables the writer/recovery path and the new runner lock without deleting ledger tables.

## Tier 1 — Logical Rollback

Use this first unless the database itself is unreadable.

1. Disable the ledger writer and recovery shields in the systemd environment/drop-in.
2. Run `systemctl daemon-reload`.
3. Restart only `tokenoskobi-news-radar-refresh.service` if an active process must be replaced.
4. Confirm raw ingestion, derived refresh and the pre-A9 hot gateway path still execute.
5. Do not drop or delete `news_disposition_batches_v2` or `news_disposition_ledger_v2`.
6. Mark affected batch UIDs as quarantined in the recovery-state evidence and preserve the output/state files for audit.
7. Restore the pre-activation code HEAD only if disabling the flags is insufficient.
8. Verify database integrity, source-table row counts, timer status and gateway JSON contract.

Tier 1 preserves raw, match, signal and score data.

## Tier 2 — Physical Restore With Delta Recovery

Use only when the live SQLite database is unreadable or integrity checks fail.

1. Stop the news timer and service.
2. Copy the damaged database, WAL/SHM files if present, runtime state and journal evidence to a quarantine directory.
3. Record SHA-256, size and timestamp for every quarantined file.
4. Restore the verified pre-activation database backup.
5. Extract post-backup raw/derived deltas from the quarantined database in read-only mode.
6. Deduplicate delta rows by their canonical primary/unique identifiers before insertion.
7. Replay deltas into a disposable copy first.
8. Prove row-count parity, UID uniqueness, foreign-key integrity and zero duplicate notification risk.
9. Apply the validated delta only after explicit authorization.
10. Re-enable the timer only after natural-cycle verification.

A blind full-database restore without delta recovery is prohibited.

## Duplicate/Notification Guard

Delta replay must not emit historical notifications blindly. Gateway output and ledger batches must be reconciled by canonical UID and batch sequence. Existing downstream output with a newer batch sequence must never be overwritten by an older recovery batch.

## Poison-Batch Handling

Three consecutive recovery failures quarantine the batch. While quarantined:

- raw and derived processing may continue;
- hot publication is blocked;
- a loud recovery/quarantine alert is mandatory;
- operator review is required before retry-counter reset.

## Evidence Required Before Production Activation

- fresh-process recovery pass;
- natural runner recovery-before-raw pass;
- file fsync → atomic replace → parent-directory fsync pass;
- monotonic batch-sequence overwrite protection pass;
- strict single-instance lock pass;
- poison-pill quarantine pass;
- recovery alert pass;
- backward-compatible JSON contract pass;
- production DB and runtime-state guard unchanged during A10 test;
- explicit Red Team production authorization.

## Current Authorization

```text
PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```
'''

REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "gateway",
    "generated_at_utc",
    "mode",
    "sources",
    "authority",
    "source_health",
    "hot_queue_count",
    "hot_queue",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_guard(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    st = path.stat()
    return {
        "exists": True,
        "sha256": sha256_file(path),
        "size_bytes": st.st_size,
        "mtime_ns": st.st_mtime_ns,
    }


def choose_temp_root() -> Dict[str, Any]:
    db_size = PROD_DB.stat().st_size
    required = db_size * 6 + 96 * 1024 * 1024
    shm = Path("/dev/shm")
    if shm.is_dir():
        free = shutil.disk_usage(shm).free
        if free >= required:
            return {
                "root": shm,
                "mode": "TMPFS_CAPACITY_PROVEN",
                "free_bytes": free,
                "required_bytes": required,
            }
    tmp = Path("/tmp")
    return {
        "root": tmp,
        "mode": "DISK_TEMP_FALLBACK",
        "free_bytes": shutil.disk_usage(tmp).free,
        "required_bytes": required,
    }


def backup_sqlite(source: Path, target: Path) -> None:
    source_conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target_conn = sqlite3.connect(target)
    try:
        source_conn.backup(target_conn)
    finally:
        target_conn.close()
        source_conn.close()


def hot_item(i: int) -> Dict[str, Any]:
    return {
        "hot_uid": f"hot_a10_{i:03d}",
        "lane": "MARKET_INDICATOR",
        "event_uid": f"event_a10_{i:03d}",
        "news_uid": f"news_a10_{i:03d}",
        "title": f"A10 synthetic item {i}",
        "hits": ["BTC"],
        "published_at_utc": "2026-07-11T00:00:00+00:00",
        "source_uid": "source_a10",
        "priority_score": 100 - i,
        "gateway_decision": "REVIEW_ONLY",
        "authority": {
            "db_write": False,
            "hunter_authorized": False,
            "trade_signal": False,
            "paper_signal": False,
            "live_trade": False,
            "execution_authority": False,
        },
    }


def insert_batch(
    db_path: Path,
    batch_uid: str,
    *,
    offset: int = 0,
    poison: bool = False,
) -> int:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        row_counts = {
            "batches": conn.execute(
                "SELECT COUNT(*) FROM news_disposition_batches_v2"
            ).fetchone()[0],
            "ledger": conn.execute(
                "SELECT COUNT(*) FROM news_disposition_ledger_v2"
            ).fetchone()[0],
        }
        conn.execute(
            """
            INSERT INTO news_disposition_batches_v2(
                batch_uid, policy_version, queue_capacity,
                source_candidate_count, normalized_candidate_count,
                deduplicated_candidate_count, admitted_count,
                overflow_count, duplicate_removed_count,
                unsafe_filtered_count, invalid_candidate_count,
                replaced_count, lowest_admitted_priority,
                highest_overflow_priority, source_snapshot_hash,
                status, retention_expires_at_utc,
                created_at_utc, committed_at_utc
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                batch_uid,
                "A10_SYNTHETIC_LEDGER_POLICY_V1",
                50,
                71,
                66,
                61,
                50,
                10,
                5,
                3,
                2,
                1,
                5,
                0,
                f"snapshot_{batch_uid}",
                "COMMITTED",
                "2026-08-10T00:00:00+00:00",
                "2026-07-11T00:00:00+00:00",
                "2026-07-11T00:00:01+00:00",
            ),
        )
        batch_sequence = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

        dispositions = (
            ["ADMITTED"] * 50
            + ["OVERFLOW_TRUNCATED"] * 10
            + ["DUPLICATE_REMOVED"] * 5
            + ["UNSAFE_AUTHORITY_FILTERED"] * 3
            + ["INVALID_CANDIDATE"] * 2
            + ["REPLACED_BY_HIGHER_PRIORITY"]
        )
        reasons = {
            "ADMITTED": "TOP_50_ADMITTED",
            "OVERFLOW_TRUNCATED": "QUEUE_OVERFLOW",
            "DUPLICATE_REMOVED": "DUPLICATE_HOT_UID",
            "UNSAFE_AUTHORITY_FILTERED": "UNSAFE_AUTHORITY",
            "INVALID_CANDIDATE": "INVALID_INPUT",
            "REPLACED_BY_HIGHER_PRIORITY": "HIGHER_PRIORITY_REPLACEMENT",
        }

        for source_index, disposition in enumerate(dispositions):
            n = offset + source_index
            payload = hot_item(n) if disposition == "ADMITTED" else {
                "source_index": source_index
            }
            payload_json = json.dumps(payload, ensure_ascii=False)
            if poison and source_index == 0:
                payload_json = "{invalid-json"

            conn.execute(
                """
                INSERT INTO news_disposition_ledger_v2(
                    disposition_uid, batch_uid, source_index,
                    source_candidate_uid, hot_uid, event_uid,
                    news_uid, lane, priority_score, candidate_rank,
                    disposition, reason_code, lowest_admitted_priority,
                    highest_overflow_priority, source_snapshot_hash,
                    recorded_at_utc, payload_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    f"disp_{batch_uid}_{source_index}",
                    batch_uid,
                    source_index,
                    f"source_{batch_uid}_{source_index}",
                    f"hot_a10_{n:03d}" if disposition == "ADMITTED" else None,
                    f"event_a10_{n:03d}" if disposition == "ADMITTED" else None,
                    f"news_a10_{n:03d}" if disposition == "ADMITTED" else None,
                    "MARKET_INDICATOR" if disposition == "ADMITTED" else None,
                    100 - source_index if disposition == "ADMITTED" else None,
                    source_index + 1 if disposition == "ADMITTED" else None,
                    disposition,
                    reasons[disposition],
                    5,
                    0,
                    f"snapshot_{batch_uid}",
                    "2026-07-11T00:00:01+00:00",
                    payload_json,
                ),
            )
        conn.commit()
        assert row_counts["batches"] + 1 == conn.execute(
            "SELECT COUNT(*) FROM news_disposition_batches_v2"
        ).fetchone()[0]
        assert row_counts["ledger"] + 71 == conn.execute(
            "SELECT COUNT(*) FROM news_disposition_ledger_v2"
        ).fetchone()[0]
        return batch_sequence
    finally:
        conn.close()


def parse_last_json(stdout: str) -> Dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            value = json.loads(line)
            if isinstance(value, dict):
                return value
    raise AssertionError("JSON_RESULT_NOT_FOUND")


def run_guard(
    db: Path,
    output: Path,
    state: Path,
    *,
    batch_sequence: int | None = None,
) -> tuple[subprocess.CompletedProcess[str], Dict[str, Any]]:
    cmd = [
        PYTHON_BIN,
        str(GUARD),
        "--db-path",
        str(db),
        "--output-path",
        str(output),
        "--state-path",
        str(state),
        "--contract-seed-path",
        str(CONTRACT),
        "--max-attempts",
        "3",
    ]
    if batch_sequence is not None:
        cmd.extend(["--batch-sequence", str(batch_sequence)])
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return result, parse_last_json(result.stdout)


def write_stub(path: Path, marker: str, sleep_seconds: float = 0.0) -> None:
    path.write_text(
        f"""#!/usr/bin/env python3
import os
import time
p = os.environ['TOKENOSKOBI_A10_ORDER_LOG']
with open(p, 'a', encoding='utf-8') as handle:
    handle.write({marker!r} + '\\n')
    handle.flush()
    os.fsync(handle.fileno())
time.sleep({sleep_seconds!r})
""",
        encoding="utf-8",
    )


def runner_env(
    temp_dir: Path,
    db: Path,
    output: Path,
    state: Path,
    order: Path,
    original: Path,
    helper: Path,
    hot: Path,
    lock: Path,
) -> Dict[str, str]:
    return {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "TOKENOSKOBI_ROOT": str(temp_dir),
        "TOKENOSKOBI_NEWS_ORIGINAL_PATH": str(original),
        "TOKENOSKOBI_NEWS_DERIVED_HELPER_PATH": str(helper),
        "TOKENOSKOBI_NEWS_HOT_PATH": str(hot),
        "TOKENOSKOBI_DB_PATH": str(db),
        "TOKENOSKOBI_HOT_OUTPUT_PATH": str(output),
        "TOKENOSKOBI_LEDGER_RECOVERY_STATE_PATH": str(state),
        "TOKENOSKOBI_RECOVERY_CONTRACT_SEED_PATH": str(CONTRACT),
        "TOKENOSKOBI_RUNNER_LOCK_PATH": str(lock),
        "TOKENOSKOBI_A10_ORDER_LOG": str(order),
        "TOKENOSKOBI_LEDGER_WRITER_ENABLED": "1",
        "TOKENOSKOBI_RUNNER_LOCK_ENABLED": "1",
        "TOKENOSKOBI_LEDGER_RECOVERY_MAX_ATTEMPTS": "3",
        "PYTHONPATH": str(ROOT / "tools"),
    }


def import_guard_module():
    spec = importlib.util.spec_from_file_location(
        "news_ledger_recovery_guard_v1_a10",
        GUARD,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("GUARD_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fsync_order(temp_dir: Path) -> Dict[str, Any]:
    module = import_guard_module()
    events: list[str] = []
    original_fsync = module.os.fsync
    original_replace = module.os.replace

    def fsync_wrapper(fd: int):
        mode = os.fstat(fd).st_mode
        events.append(
            "DIR_FSYNC" if stat.S_ISDIR(mode) else "FILE_FSYNC"
        )
        return original_fsync(fd)

    def replace_wrapper(source, target):
        events.append("REPLACE")
        return original_replace(source, target)

    module.os.fsync = fsync_wrapper
    module.os.replace = replace_wrapper
    try:
        module.durable_atomic_write_json(
            temp_dir / "fsync_order.json",
            {"proof": "A10"},
        )
    finally:
        module.os.fsync = original_fsync
        module.os.replace = original_replace

    assert events == ["FILE_FSYNC", "REPLACE", "DIR_FSYNC"]
    return {
        "events": events,
        "pass": True,
    }


def benchmark_publish(temp_dir: Path) -> Dict[str, Any]:
    module = import_guard_module()
    durable_ns: list[int] = []
    nondurable_ns: list[int] = []
    payload = {"data": "x" * 65536}

    for i in range(5):
        start = time.perf_counter_ns()
        module.durable_atomic_write_json(
            temp_dir / f"durable_{i}.json",
            payload,
        )
        durable_ns.append(time.perf_counter_ns() - start)

        target = temp_dir / f"nondurable_{i}.json"
        tmp = target.with_suffix(".tmp")
        start = time.perf_counter_ns()
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(tmp, target)
        nondurable_ns.append(time.perf_counter_ns() - start)

    return {
        "durable_median_ns": int(median(durable_ns)),
        "nondurable_median_ns": int(median(nondurable_ns)),
        "durable_samples_ns": durable_ns,
        "nondurable_samples_ns": nondurable_ns,
        "decision_role": "MEASUREMENT_ONLY_NOT_A_SECURITY_BYPASS",
    }


def read_systemd_binding() -> Dict[str, Any]:
    result = subprocess.run(
        [
            "systemctl",
            "show",
            "tokenoskobi-news-radar-refresh.service",
            "-p",
            "ExecStart",
            "-p",
            "FragmentPath",
            "-p",
            "User",
        ],
        capture_output=True,
        text=True,
    )
    return {
        "rc": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "runner_bound": str(RUNNER) in result.stdout,
    }


def main() -> int:
    for path in (PROD_DB, RUNNER, CONTRACT):
        if not path.exists():
            raise FileNotFoundError(path)

    if subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip():
        raise RuntimeError("WORKTREE_NOT_CLEAN_BEFORE_A10")

    original_runner = RUNNER.read_bytes()
    original_guard = GUARD.read_bytes() if GUARD.exists() else None
    original_runbook = RUNBOOK.read_bytes() if RUNBOOK.exists() else None

    if sha256_file(RUNNER) != EXPECTED_PRE_A10_RUNNER_SHA256:
        raise RuntimeError("PRE_A10_RUNNER_HASH_MISMATCH")

    GUARD.parent.mkdir(parents=True, exist_ok=True)
    RUNBOOK.parent.mkdir(parents=True, exist_ok=True)
    GUARD.write_text(GUARD_SOURCE, encoding="utf-8")
    RUNNER.write_text(RUNNER_SOURCE, encoding="utf-8")
    RUNBOOK.write_text(RUNBOOK_SOURCE, encoding="utf-8")
    GUARD.chmod(0o755)
    RUNNER.chmod(0o755)

    production_guard_before = {
        "database": file_guard(PROD_DB),
        "gateway_output": file_guard(CONTRACT),
        "recovery_state": file_guard(RECOVERY_STATE_PROD),
    }

    choice = choose_temp_root()
    temp_dir = Path(
        tempfile.mkdtemp(
            prefix="era55a10_",
            dir=str(choice["root"]),
        )
    )

    tests: Dict[str, Any] = {}
    try:
        fresh_db = temp_dir / "fresh.sqlite"
        backup_sqlite(PROD_DB, fresh_db)
        fresh_seq = insert_batch(fresh_db, "a10_fresh_batch")
        fresh_output = temp_dir / "fresh_output.json"
        fresh_state = temp_dir / "fresh_state.json"
        fresh_proc, fresh_result = run_guard(
            fresh_db,
            fresh_output,
            fresh_state,
        )
        assert fresh_result["status"] == "RECOVERED"
        assert fresh_result["recovery_executed"] is True
        assert "[RECOVERY_EVENT_TRIGGERED]" in fresh_proc.stdout
        assert fresh_output.exists()
        tests["gate_1_fresh_process_recovery"] = {
            "pass": True,
            "batch_sequence": fresh_seq,
            "result": fresh_result,
            "fresh_subprocess": True,
            "shared_in_memory_state": False,
            "recovery_alert_present": True,
        }

        natural_db = temp_dir / "natural.sqlite"
        backup_sqlite(PROD_DB, natural_db)
        insert_batch(natural_db, "a10_natural_batch")
        natural_output = temp_dir / "natural_output.json"
        natural_state = temp_dir / "natural_state.json"
        order = temp_dir / "natural_order.log"
        original = temp_dir / "original_stub.py"
        helper = temp_dir / "helper_stub.py"
        hot = temp_dir / "hot_stub.py"
        lock = temp_dir / "natural.lock"
        write_stub(original, "RAW_STUB")
        write_stub(helper, "DERIVED_STUB")
        write_stub(hot, "HOT_STUB")
        env = runner_env(
            temp_dir,
            natural_db,
            natural_output,
            natural_state,
            order,
            original,
            helper,
            hot,
            lock,
        )
        natural_run = subprocess.run(
            [PYTHON_BIN, str(RUNNER)],
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        order_rows = order.read_text(encoding="utf-8").splitlines()
        recovery_index = next(
            i for i, value in enumerate(order_rows)
            if value.startswith("RECOVERY_DONE:")
        )
        raw_index = order_rows.index("RAW_START")
        assert recovery_index < raw_index
        assert natural_output.exists()
        systemd_binding = read_systemd_binding()
        assert systemd_binding["runner_bound"] is True
        tests["gate_2_natural_runner_trigger"] = {
            "pass": True,
            "order": order_rows,
            "recovery_before_raw": True,
            "runner_stdout": natural_run.stdout,
            "systemd_binding": systemd_binding,
            "scope": (
                "ACTUAL_RUNNER_CODEPATH_WITH_ISOLATED_ENV_AND_"
                "READONLY_SYSTEMD_EXECSTART_BINDING"
            ),
            "real_timer_with_writer_enabled": False,
        }

        lock_db = temp_dir / "lock.sqlite"
        backup_sqlite(PROD_DB, lock_db)
        insert_batch(lock_db, "a10_lock_batch")
        lock_output = temp_dir / "lock_output.json"
        lock_state = temp_dir / "lock_state.json"
        run_guard(lock_db, lock_output, lock_state)
        lock_order = temp_dir / "lock_order.log"
        lock_original = temp_dir / "lock_original_stub.py"
        lock_helper = temp_dir / "lock_helper_stub.py"
        lock_hot = temp_dir / "lock_hot_stub.py"
        lock_path = temp_dir / "single_instance.lock"
        write_stub(lock_original, "RAW_LOCK_STUB", 2.0)
        write_stub(lock_helper, "DERIVED_LOCK_STUB")
        write_stub(lock_hot, "HOT_LOCK_STUB")
        lock_env = runner_env(
            temp_dir,
            lock_db,
            lock_output,
            lock_state,
            lock_order,
            lock_original,
            lock_helper,
            lock_hot,
            lock_path,
        )
        first = subprocess.Popen(
            [PYTHON_BIN, str(RUNNER)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=lock_env,
        )
        time.sleep(0.35)
        second = subprocess.run(
            [PYTHON_BIN, str(RUNNER)],
            capture_output=True,
            text=True,
            env=lock_env,
            check=True,
        )
        first_stdout, first_stderr = first.communicate()
        if first.returncode != 0:
            raise RuntimeError(
                "FIRST_LOCK_RUN_FAILED:"
                + first_stdout
                + first_stderr
            )
        assert "[RUNNER_ALREADY_ACTIVE]" in second.stdout
        lock_rows = lock_order.read_text(encoding="utf-8").splitlines()
        assert lock_rows.count("RAW_LOCK_STUB") == 1
        tests["strict_single_instance_lock"] = {
            "pass": True,
            "second_runner_rc": second.returncode,
            "second_runner_stdout": second.stdout.strip(),
            "raw_execution_count": lock_rows.count("RAW_LOCK_STUB"),
        }

        tests["gate_3_fsync_durability"] = test_fsync_order(temp_dir)
        tests["fsync_cost_measurement"] = benchmark_publish(temp_dir)

        monotonic_db = temp_dir / "monotonic.sqlite"
        backup_sqlite(PROD_DB, monotonic_db)
        old_seq = insert_batch(
            monotonic_db,
            "a10_old_batch",
            offset=0,
        )
        new_seq = insert_batch(
            monotonic_db,
            "a10_new_batch",
            offset=100,
        )
        monotonic_output = temp_dir / "monotonic_output.json"
        monotonic_state = temp_dir / "monotonic_state.json"
        _, newest_result = run_guard(
            monotonic_db,
            monotonic_output,
            monotonic_state,
        )
        before_hash = sha256_file(monotonic_output)
        _, stale_result = run_guard(
            monotonic_db,
            monotonic_output,
            monotonic_state,
            batch_sequence=old_seq,
        )
        after_hash = sha256_file(monotonic_output)
        assert new_seq > old_seq
        assert newest_result["batch_sequence"] == new_seq
        assert stale_result["status"] == "TARGET_NEWER_THAN_RECOVERY"
        assert before_hash == after_hash
        tests["gate_4_monotonic_output_protection"] = {
            "pass": True,
            "ordering_key": "SQLITE_BATCH_ROWID",
            "uid_role": "IDENTITY_NOT_ORDERING",
            "old_sequence": old_seq,
            "new_sequence": new_seq,
            "stale_result": stale_result,
            "output_hash_unchanged": True,
        }

        poison_db = temp_dir / "poison.sqlite"
        backup_sqlite(PROD_DB, poison_db)
        insert_batch(
            poison_db,
            "a10_poison_batch",
            poison=True,
        )
        poison_output = temp_dir / "poison_output.json"
        poison_state = temp_dir / "poison_state.json"
        poison_results: list[Dict[str, Any]] = []
        poison_stdout: list[str] = []
        for _ in range(4):
            proc, result = run_guard(
                poison_db,
                poison_output,
                poison_state,
            )
            poison_results.append(result)
            poison_stdout.append(proc.stdout)
        assert [x["status"] for x in poison_results[:3]] == [
            "RETRY_PENDING",
            "RETRY_PENDING",
            "QUARANTINED",
        ]
        assert poison_results[3]["status"] == "QUARANTINED"
        assert poison_results[3]["attempt_count"] == 3
        assert not poison_output.exists()
        assert "[RECOVERY_QUARANTINED]" in poison_stdout[2]
        tests["poison_pill_quarantine"] = {
            "pass": True,
            "max_attempts": 3,
            "statuses": [x["status"] for x in poison_results],
            "attempt_count_after_fourth_call": poison_results[3][
                "attempt_count"
            ],
            "infinite_retry_prevented": True,
            "quarantine_alert_present": True,
        }

        old_contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        generated = json.loads(fresh_output.read_text(encoding="utf-8"))
        assert REQUIRED_TOP_LEVEL_KEYS <= set(old_contract)
        assert REQUIRED_TOP_LEVEL_KEYS <= set(generated)
        type_parity = {
            key: type(old_contract[key]).__name__
            == type(generated[key]).__name__
            for key in sorted(REQUIRED_TOP_LEVEL_KEYS)
        }
        assert all(type_parity.values())
        additive_keys = set(generated) - set(old_contract)
        assert additive_keys <= {"ledger_publish"}
        old_items = old_contract.get("hot_queue") or []
        generated_items = generated.get("hot_queue") or []
        assert generated["hot_queue_count"] == len(generated_items) == 50
        if old_items:
            old_item_keys = set(old_items[0])
            assert all(set(item) == old_item_keys for item in generated_items)
        else:
            old_item_keys = set(generated_items[0])
        tests["gate_6_json_contract_parity"] = {
            "pass": True,
            "required_top_level_type_parity": type_parity,
            "additive_top_level_keys": sorted(additive_keys),
            "old_hot_item_keys": sorted(old_item_keys),
            "generated_hot_item_keys": sorted(set(generated_items[0])),
            "existing_required_fields_removed": False,
            "existing_required_types_changed": False,
        }

        default_order = temp_dir / "default_flags_order.log"
        default_original = temp_dir / "default_original_stub.py"
        default_helper = temp_dir / "default_helper_stub.py"
        default_hot = temp_dir / "default_hot_stub.py"
        write_stub(default_original, "RAW_DEFAULT_STUB")
        write_stub(default_helper, "DERIVED_DEFAULT_STUB")
        write_stub(default_hot, "HOT_DEFAULT_STUB")
        default_env = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "TOKENOSKOBI_ROOT": str(temp_dir),
            "TOKENOSKOBI_NEWS_ORIGINAL_PATH": str(default_original),
            "TOKENOSKOBI_NEWS_DERIVED_HELPER_PATH": str(default_helper),
            "TOKENOSKOBI_NEWS_HOT_PATH": str(default_hot),
            "TOKENOSKOBI_DB_PATH": str(fresh_db),
            "TOKENOSKOBI_HOT_OUTPUT_PATH": str(
                temp_dir / "default_output.json"
            ),
            "TOKENOSKOBI_LEDGER_RECOVERY_STATE_PATH": str(
                temp_dir / "default_state.json"
            ),
            "TOKENOSKOBI_RUNNER_LOCK_PATH": str(
                temp_dir / "default.lock"
            ),
            "TOKENOSKOBI_A10_ORDER_LOG": str(default_order),
            "TOKENOSKOBI_LEDGER_WRITER_ENABLED": "0",
            "TOKENOSKOBI_RUNNER_LOCK_ENABLED": "0",
            "PYTHONPATH": str(ROOT / "tools"),
        }
        default_run = subprocess.run(
            [PYTHON_BIN, str(RUNNER)],
            capture_output=True,
            text=True,
            env=default_env,
            check=True,
        )
        default_rows = default_order.read_text(encoding="utf-8").splitlines()
        assert not any(row.startswith("RECOVERY_DONE:") for row in default_rows)
        assert "LOCK_ACQUIRED" not in default_rows
        tests["feature_flag_default_inactive"] = {
            "pass": True,
            "writer_default_enabled": False,
            "lock_default_enabled": False,
            "default_order": default_rows,
            "runner_stdout": default_run.stdout,
        }

        runbook_text = RUNBOOK.read_text(encoding="utf-8")
        required_runbook_terms = [
            "Tier 1",
            "Tier 2",
            "TOKENOSKOBI_LEDGER_WRITER_ENABLED",
            "TOKENOSKOBI_RUNNER_LOCK_ENABLED",
            "A blind full-database restore without delta recovery is prohibited.",
            "Three consecutive recovery failures quarantine the batch.",
        ]
        missing_terms = [
            term for term in required_runbook_terms
            if term not in runbook_text
        ]
        assert not missing_terms
        tests["gate_5_logical_rollback_runbook"] = {
            "pass": True,
            "path": str(RUNBOOK.relative_to(ROOT)),
            "required_terms_present": True,
            "full_db_blind_restore_prohibited": True,
            "ledger_tables_preserved_on_tier_1": True,
        }

        conn = sqlite3.connect(f"file:{PROD_DB}?mode=ro", uri=True)
        try:
            production_ledger_rows = conn.execute(
                "SELECT COUNT(*) FROM news_disposition_ledger_v2"
            ).fetchone()[0]
            production_batch_rows = conn.execute(
                "SELECT COUNT(*) FROM news_disposition_batches_v2"
            ).fetchone()[0]
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            quick = conn.execute("PRAGMA quick_check").fetchone()[0]
        finally:
            conn.close()

        production_guard_after = {
            "database": file_guard(PROD_DB),
            "gateway_output": file_guard(CONTRACT),
            "recovery_state": file_guard(RECOVERY_STATE_PROD),
        }
        production_unchanged = (
            production_guard_before == production_guard_after
        )
        if not production_unchanged:
            raise RuntimeError(
                "PRODUCTION_GUARD_CHANGED_DURING_A10_TEST"
            )

        artifact = {
            "schema_version": "1.0",
            "work_unit": (
                "ERA55A_10_P0_LEDGER_WRITER_POST_TEST_AUDIT_"
                "AND_PRODUCTION_APPLY_DECISION"
            ),
            "package_type": "REMEDIATION_PROOF_REVIEW_PENDING",
            "tested_at_utc": utc_now(),
            "status": "REMEDIATION_VALIDATED_REVIEW_PENDING",
            "result": (
                "OK_A10_SHIELDS_TEMP_COPY_VALIDATED_"
                "PRODUCTION_AUTHORIZATION_PENDING"
            ),
            "temp_environment": {
                "choice": {
                    **choice,
                    "root": str(choice["root"]),
                },
                "temp_dir": str(temp_dir),
            },
            "tests": tests,
            "production_guard_before": production_guard_before,
            "production_guard_after": production_guard_after,
            "production_unchanged": production_unchanged,
            "production_database": {
                "batch_rows": production_batch_rows,
                "ledger_rows": production_ledger_rows,
                "integrity_check": integrity,
                "quick_check": quick,
            },
            "decision": {
                "global_runner_lock_implemented": True,
                "natural_recovery_trigger_implemented": True,
                "poison_pill_quarantine_implemented": True,
                "fsync_protocol_implemented": True,
                "recovery_alerting_implemented": True,
                "json_contract_backward_compatible": True,
                "production_writer_activation_authorized": False,
                "p0_f1_closed": False,
                "option_b_authorized": False,
                "real_natural_timer_writer_cycle_proven": False,
                "red_team_review_required": True,
            },
            "next_safe_step": (
                "ERA55A_10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION"
            ),
        }

        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(
            json.dumps(
                artifact,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        REPORT.write_text(
            "\n".join(
                [
                    "# ERA55A10 Ledger Writer Remediation Proof Package",
                    "",
                    "- Status: `REMEDIATION_VALIDATED_REVIEW_PENDING`",
                    "- Production writer activation: `false`",
                    "- P0 F1 closed: `false`",
                    "- Production unchanged: `true`",
                    "",
                    "## Proof Gates",
                    "",
                    "- Fresh-process recovery: PASS",
                    "- Recovery-before-raw runner order: PASS",
                    "- Strict single-instance lock: PASS",
                    "- File fsync → replace → parent-directory fsync: PASS",
                    "- Monotonic rowid batch protection: PASS",
                    "- Poison-pill three-attempt quarantine: PASS",
                    "- Recovery alerts: PASS",
                    "- Backward-compatible gateway JSON contract: PASS",
                    "- Logical and physical rollback runbook: PRESENT",
                    "",
                    "## Deliberate Boundary",
                    "",
                    "The real natural systemd timer cycle with the production writer enabled was not executed because production activation remains blocked. The actual runner code path and current systemd ExecStart binding were verified with isolated paths.",
                    "",
                    "## Decision",
                    "",
                    "`PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false`",
                    "",
                    "`NEXT_SAFE_STEP=ERA55A_10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        subprocess.run(
            [
                "git",
                "add",
                str(GUARD.relative_to(ROOT)),
                str(RUNNER.relative_to(ROOT)),
                str(RUNBOOK.relative_to(ROOT)),
                str(ARTIFACT.relative_to(ROOT)),
                str(REPORT.relative_to(ROOT)),
            ],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", COMMIT_SUBJECT],
            cwd=ROOT,
            check=True,
        )

        print("ERA55A10_REMEDIATION_PROOF=SUCCESS")
        print(
            "RESULT="
            + artifact["result"]
        )
        print("FRESH_PROCESS_RECOVERY=true")
        print("RECOVERY_BEFORE_RAW=true")
        print("STRICT_SINGLE_INSTANCE_LOCK=true")
        print("FSYNC_FILE_REPLACE_DIRECTORY=true")
        print("MONOTONIC_OUTPUT_PROTECTION=true")
        print("POISON_PILL_QUARANTINE=true")
        print("RECOVERY_ALERTING=true")
        print("JSON_CONTRACT_BACKWARD_COMPATIBLE=true")
        print("PRODUCTION_UNCHANGED=true")
        print("PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print(
            "NEXT_SAFE_STEP="
            + artifact["next_safe_step"]
        )
        print(
            "LOCAL_COMMIT="
            + subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
        print(f"ARTIFACT={ARTIFACT.relative_to(ROOT)}")
        print(f"REPORT={REPORT.relative_to(ROOT)}")
        return 0
    except BaseException:
        RUNNER.write_bytes(original_runner)
        if original_guard is None:
            GUARD.unlink(missing_ok=True)
        else:
            GUARD.write_bytes(original_guard)
        if original_runbook is None:
            RUNBOOK.unlink(missing_ok=True)
        else:
            RUNBOOK.write_bytes(original_runbook)
        for cache_dir in (ROOT / "tools").glob("__pycache__"):
            shutil.rmtree(cache_dir, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
