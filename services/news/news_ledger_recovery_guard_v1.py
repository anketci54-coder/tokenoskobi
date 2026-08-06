
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
