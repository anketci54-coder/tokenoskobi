from __future__ import annotations

import errno
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def record_hash(seq: int, epoch: int, parent: str | None, payload: dict[str, Any]) -> str:
    material = {"seq": seq, "epoch": epoch, "parent": parent, "payload": payload}
    return hashlib.sha256(canonical_json(material)).hexdigest()


def make_record(seq: int, epoch: int, parent: str | None) -> dict[str, Any]:
    payload = {"snapshot_id": f"snapshot-{seq}", "state": "ACTIVE"}
    return {
        "seq": seq,
        "epoch": epoch,
        "parent": parent,
        "payload": payload,
        "hash": record_hash(seq, epoch, parent, payload),
    }


R1 = make_record(1, 50, None)
R2 = make_record(2, 50, R1["hash"])
R3 = make_record(3, 50, R2["hash"])
R4 = make_record(4, 50, R3["hash"])
BASE = [R1, R2, R3]
NEXT = [R1, R2, R3, R4]


@dataclass(frozen=True)
class Result:
    case: str
    passed: bool
    route: str
    reason: str


class InjectedFailure(OSError):
    pass


def serialize_history(records: list[dict[str, Any]]) -> bytes:
    return b"".join(canonical_json(record) for record in records)


def serialize_checkpoint(record: dict[str, Any]) -> bytes:
    return canonical_json({"seq": record["seq"], "epoch": record["epoch"], "hash": record["hash"]})


def fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def install_base(root: Path) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    history = root / "history.jsonl"
    checkpoint = root / "checkpoint.json"
    history.write_bytes(serialize_history(BASE))
    checkpoint.write_bytes(serialize_checkpoint(R3))
    with history.open("rb") as handle:
        os.fsync(handle.fileno())
    with checkpoint.open("rb") as handle:
        os.fsync(handle.fileno())
    fsync_dir(root)
    return history, checkpoint


def validate(history: Path, checkpoint: Path) -> tuple[bool, str]:
    try:
        raw_history = history.read_bytes()
        if not raw_history.endswith(b"\n"):
            return False, "PARTIAL_HISTORY_RECORD"

        records: list[dict[str, Any]] = []
        for line in raw_history.splitlines():
            if not line:
                return False, "EMPTY_HISTORY_RECORD"
            records.append(json.loads(line))

        if not records:
            return False, "HISTORY_EMPTY"

        previous: dict[str, Any] | None = None
        seen_hashes: set[str] = set()

        for index, record in enumerate(records):
            if set(record) != {"seq", "epoch", "parent", "payload", "hash"}:
                return False, "HISTORY_SCHEMA_INVALID"

            expected_hash = record_hash(
                record["seq"], record["epoch"], record["parent"], record["payload"]
            )
            if record["hash"] != expected_hash:
                return False, "RECORD_HASH_MISMATCH"
            if record["hash"] in seen_hashes:
                return False, "RECORD_HASH_REPLAY"

            if index == 0:
                if record["seq"] != 1 or record["parent"] is not None:
                    return False, "GENESIS_INVALID"
            else:
                assert previous is not None
                if record["seq"] != previous["seq"] + 1:
                    return False, "SEQUENCE_DISCONTINUITY"
                if record["epoch"] != previous["epoch"]:
                    return False, "EPOCH_DISCONTINUITY"
                if record["parent"] != previous["hash"]:
                    return False, "PARENT_HASH_MISMATCH"

            seen_hashes.add(record["hash"])
            previous = record

        raw_checkpoint = checkpoint.read_bytes()
        if not raw_checkpoint.endswith(b"\n"):
            return False, "PARTIAL_CHECKPOINT"

        checkpoint_data = json.loads(raw_checkpoint)
        if set(checkpoint_data) != {"seq", "epoch", "hash"}:
            return False, "CHECKPOINT_SCHEMA_INVALID"

        final_record = records[-1]
        if checkpoint_data["seq"] != final_record["seq"]:
            return False, "CHECKPOINT_SEQUENCE_MISMATCH"
        if checkpoint_data["epoch"] != final_record["epoch"]:
            return False, "CHECKPOINT_EPOCH_MISMATCH"
        if checkpoint_data["hash"] != final_record["hash"]:
            return False, "CHECKPOINT_HASH_MISMATCH"

        return True, "NONE"
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, KeyError) as exc:
        return False, type(exc).__name__.upper()


def atomic_write(path: Path, data: bytes, *, fail: str | None = None, error_number: int = errno.EIO) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("wb") as handle:
            if fail == "write":
                raise InjectedFailure(error_number, "WRITE")
            handle.write(data)
            handle.flush()
            if fail == "file_fsync":
                raise InjectedFailure(error_number, "FILE_FSYNC")
            os.fsync(handle.fileno())

        if fail == "replace":
            raise InjectedFailure(error_number, "REPLACE")
        os.replace(temporary, path)

        if fail == "dir_fsync":
            raise InjectedFailure(error_number, "DIR_FSYNC")
        fsync_dir(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def update_pair(
    root: Path,
    *,
    history_fail: str | None = None,
    checkpoint_fail: str | None = None,
    error_number: int = errno.EIO,
) -> None:
    atomic_write(
        root / "history.jsonl",
        serialize_history(NEXT),
        fail=history_fail,
        error_number=error_number,
    )
    atomic_write(
        root / "checkpoint.json",
        serialize_checkpoint(R4),
        fail=checkpoint_fail,
        error_number=error_number,
    )


def failure_case(
    case: str,
    target: str,
    phase: str,
    error_number: int,
    expected_reason: str,
) -> Result:
    with tempfile.TemporaryDirectory(prefix="a30-") as directory:
        root = Path(directory)
        history, checkpoint = install_base(root)
        try:
            arguments = {"history_fail": phase} if target == "history" else {"checkpoint_fail": phase}
            update_pair(root, error_number=error_number, **arguments)
            return Result(case, False, "FAIL_CLOSED_QUARANTINE", "FAILURE_NOT_TRIGGERED")
        except InjectedFailure:
            valid, reason = validate(history, checkpoint)
            passed = (not valid and reason == expected_reason) or (
                valid and expected_reason == "NONE"
            )
            return Result(case, passed, "FAIL_CLOSED_QUARANTINE", reason)


def torn_case(case: str, target: str) -> Result:
    with tempfile.TemporaryDirectory(prefix="a30-") as directory:
        root = Path(directory)
        history, checkpoint = install_base(root)
        path = history if target == "history" else checkpoint
        data = serialize_history(NEXT) if target == "history" else serialize_checkpoint(R4)
        path.write_bytes(data[: max(1, len(data) // 2)])
        valid, reason = validate(history, checkpoint)
        expected = "PARTIAL_HISTORY_RECORD" if target == "history" else "PARTIAL_CHECKPOINT"
        return Result(case, not valid and reason == expected, "FAIL_CLOSED_QUARANTINE", reason)


def orphan_temp_case(case: str, target: str) -> Result:
    with tempfile.TemporaryDirectory(prefix="a30-") as directory:
        root = Path(directory)
        history, checkpoint = install_base(root)
        canonical = history if target == "history" else checkpoint
        data = serialize_history(NEXT) if target == "history" else serialize_checkpoint(R4)
        canonical.with_suffix(canonical.suffix + ".tmp").write_bytes(data[: len(data) // 2])
        valid, reason = validate(history, checkpoint)
        return Result(case, valid and reason == "NONE", "RECOVERY_GATE", reason)


def subprocess_crash_case(
    case: str,
    target: str,
    point: str,
    expected_valid: bool,
    expected_reason: str,
) -> Result:
    with tempfile.TemporaryDirectory(prefix="a30-") as directory:
        root = Path(directory)
        history, checkpoint = install_base(root)
        child = r'''
import os, sys
from pathlib import Path
root=Path(sys.argv[1]); target=sys.argv[2]; point=sys.argv[3]
history=root/'history.jsonl'; checkpoint=root/'checkpoint.json'
new_history=bytes.fromhex(sys.argv[4]); new_checkpoint=bytes.fromhex(sys.argv[5])
def write(path,data,inject):
 temporary=path.with_suffix(path.suffix+'.tmp'); handle=temporary.open('wb')
 if inject and point=='after_open': os._exit(71)
 handle.write(data); handle.flush()
 if inject and point=='after_write': os._exit(72)
 os.fsync(handle.fileno()); handle.close()
 if inject and point=='after_fsync': os._exit(73)
 os.replace(temporary,path)
 if inject and point=='after_replace': os._exit(74)
 descriptor=os.open(root,os.O_RDONLY); os.fsync(descriptor); os.close(descriptor)
 if inject and point=='after_dir_fsync': os._exit(75)
if target=='history':
 write(history,new_history,True)
else:
 write(history,new_history,False)
 write(checkpoint,new_checkpoint,True)
'''
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                child,
                str(root),
                target,
                point,
                serialize_history(NEXT).hex(),
                serialize_checkpoint(R4).hex(),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode not in {71, 72, 73, 74, 75}:
            return Result(case, False, "FAIL_CLOSED_QUARANTINE", f"EXIT_{completed.returncode}")
        valid, reason = validate(history, checkpoint)
        return Result(
            case,
            valid == expected_valid and reason == expected_reason,
            "RECOVERY_GATE" if valid else "FAIL_CLOSED_QUARANTINE",
            reason,
        )


def main() -> int:
    cases = [
        failure_case("HISTORY_WRITE_EIO", "history", "write", errno.EIO, "NONE"),
        failure_case("HISTORY_FILE_FSYNC_EIO", "history", "file_fsync", errno.EIO, "NONE"),
        failure_case("HISTORY_REPLACE_EIO", "history", "replace", errno.EIO, "NONE"),
        failure_case(
            "HISTORY_DIR_FSYNC_EIO",
            "history",
            "dir_fsync",
            errno.EIO,
            "CHECKPOINT_SEQUENCE_MISMATCH",
        ),
        failure_case(
            "CHECKPOINT_WRITE_ENOSPC",
            "checkpoint",
            "write",
            errno.ENOSPC,
            "CHECKPOINT_SEQUENCE_MISMATCH",
        ),
        failure_case(
            "CHECKPOINT_REPLACE_EROFS",
            "checkpoint",
            "replace",
            errno.EROFS,
            "CHECKPOINT_SEQUENCE_MISMATCH",
        ),
        failure_case(
            "CHECKPOINT_FSYNC_EACCES",
            "checkpoint",
            "file_fsync",
            errno.EACCES,
            "CHECKPOINT_SEQUENCE_MISMATCH",
        ),
        orphan_temp_case("ORPHAN_TORN_HISTORY_TEMP", "history"),
        orphan_temp_case("ORPHAN_TORN_CHECKPOINT_TEMP", "checkpoint"),
        torn_case("TORN_CANONICAL_HISTORY", "history"),
        torn_case("TORN_CANONICAL_CHECKPOINT", "checkpoint"),
        subprocess_crash_case("CRASH_HISTORY_AFTER_OPEN", "history", "after_open", True, "NONE"),
        subprocess_crash_case("CRASH_HISTORY_AFTER_WRITE", "history", "after_write", True, "NONE"),
        subprocess_crash_case("CRASH_HISTORY_AFTER_FSYNC", "history", "after_fsync", True, "NONE"),
        subprocess_crash_case(
            "CRASH_HISTORY_AFTER_REPLACE",
            "history",
            "after_replace",
            False,
            "CHECKPOINT_SEQUENCE_MISMATCH",
        ),
        subprocess_crash_case(
            "CRASH_HISTORY_AFTER_DIR_FSYNC",
            "history",
            "after_dir_fsync",
            False,
            "CHECKPOINT_SEQUENCE_MISMATCH",
        ),
        subprocess_crash_case(
            "CRASH_CHECKPOINT_AFTER_OPEN",
            "checkpoint",
            "after_open",
            False,
            "CHECKPOINT_SEQUENCE_MISMATCH",
        ),
        subprocess_crash_case(
            "CRASH_CHECKPOINT_AFTER_WRITE",
            "checkpoint",
            "after_write",
            False,
            "CHECKPOINT_SEQUENCE_MISMATCH",
        ),
        subprocess_crash_case(
            "CRASH_CHECKPOINT_AFTER_FSYNC",
            "checkpoint",
            "after_fsync",
            False,
            "CHECKPOINT_SEQUENCE_MISMATCH",
        ),
        subprocess_crash_case(
            "CRASH_CHECKPOINT_AFTER_REPLACE",
            "checkpoint",
            "after_replace",
            True,
            "NONE",
        ),
        subprocess_crash_case(
            "CRASH_CHECKPOINT_AFTER_DIR_FSYNC",
            "checkpoint",
            "after_dir_fsync",
            True,
            "NONE",
        ),
    ]

    for result in cases:
        status = "PASS" if result.passed else "FAIL"
        print(f"A30_{result.case}={status} ROUTE={result.route} REASON={result.reason}")

    passed = all(result.passed for result in cases)
    print(f"A30_CASE_COUNT={len(cases)}")
    print(
        "A30_PROCESS_CRASH_TORN_WRITE_DISK_FAILURE_AND_RECOVERY_POLICY="
        + ("PASS" if passed else "FAIL")
    )
    print("AUTO_REPAIR=false")
    print("NETWORK_ACCESS=false")
    print("REPOSITORY_MUTATION=false")
    print("DATABASE_MUTATION=false")
    print("RUNTIME_MUTATION=false")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
