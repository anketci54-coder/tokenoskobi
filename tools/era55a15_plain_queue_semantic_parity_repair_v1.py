#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path("/root/tokenoskobi_clean_v1")
EXPECTED_HEAD = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()

A14_ARTIFACT = ROOT / "data/control/era55a14_p0_pre_gateway_writer_post_test_audit_and_bounded_canary_decision_v1.json"
ARTIFACT = ROOT / "data/control/era55a15_p0_pre_gateway_queue_semantic_parity_repair_and_temp_copy_test_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST.md"
EXTRACTOR = ROOT / "tools/news_pre_gateway_candidate_stream_v1.py"
WRITER = ROOT / "tools/news_disposition_ledger_writer_v1.py"
RECOVERY = ROOT / "tools/news_ledger_recovery_guard_v1.py"
GATEWAY = ROOT / "tools/hot_intelligence_ingress_gateway_v1.py"
MARKET = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADVERSARIAL = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
DISPLAY = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
HOT_OUTPUT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
RECOVERY_STATE = ROOT / "runtime/state/news_ledger_recovery_state_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

RESULT = "OK_COMPLETE_LEDGER_LEGACY_QUEUE_SEMANTIC_PARITY_TEMP_COPY"
NEXT_STEP = "ERA55A_16_P0_QUEUE_PARITY_POST_TEST_AUDIT_AND_SINGLE_CYCLE_CANARY_DECISION"
COMMIT_SUBJECT = "ERA55A15_QUEUE_PARITY_REPAIR_TEMP_COPY | OK | PRODUCTION_UNBOUND"
POLICY_VERSION = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"
PATCH_MARKER = "# ERA55A15_ADMISSION_CONTRACT_PATCH_V1"

ADMISSION_PATCH = r'''

# ERA55A15_ADMISSION_CONTRACT_PATCH_V1
ADMISSION_CONTRACT_POLICY_VERSION = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"


def _validate_admission_contract(admission_queue: list[Dict[str, Any]]) -> list[str]:
    if not isinstance(admission_queue, list) or not admission_queue:
        raise ValueError("ADMISSION_CONTRACT_QUEUE_REQUIRED")
    if len(admission_queue) > DEFAULT_QUEUE_CAPACITY:
        raise ValueError("ADMISSION_CONTRACT_EXCEEDS_QUEUE_CAPACITY")
    uids: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(admission_queue):
        if not isinstance(item, dict):
            raise ValueError(f"ADMISSION_CONTRACT_ITEM_NOT_OBJECT:{index}")
        uid = str(item.get("hot_uid") or "")
        if not uid:
            raise ValueError(f"ADMISSION_CONTRACT_UID_MISSING:{index}")
        if uid in seen:
            raise ValueError(f"ADMISSION_CONTRACT_DUPLICATE_UID:{uid}")
        seen.add(uid)
        uids.append(uid)
    return uids


def build_plan_with_admission_contract(
    display: Dict[str, Any],
    admission_queue: list[Dict[str, Any]],
    *,
    policy_version: str = ADMISSION_CONTRACT_POLICY_VERSION,
) -> Dict[str, Any]:
    admission_uids = _validate_admission_contract(admission_queue)
    queue_capacity = len(admission_uids)
    source_rows = list(iter_source_candidates(display))
    snapshot_projection = [
        {
            "source_index": row["source_index"],
            "section_index": row["section_index"],
            "item_index": row["item_index"],
            "lane": row["lane"],
            "raw": row["raw"],
        }
        for row in source_rows
    ]
    source_snapshot_hash = sha256_bytes(canonical_json_bytes(snapshot_projection))
    admission_contract_hash = sha256_bytes(canonical_json_bytes(admission_queue))
    batch_uid = "batch_" + sha256_bytes(
        canonical_json_bytes(
            {
                "policy_version": policy_version,
                "queue_capacity": queue_capacity,
                "source_snapshot_hash": source_snapshot_hash,
                "admission_contract_hash": admission_contract_hash,
            }
        )
    )[:32]

    analyzed: list[Dict[str, Any]] = []
    safe_candidates: list[Dict[str, Any]] = []
    for source in source_rows:
        raw = source["raw"]
        if not isinstance(raw, dict):
            analyzed.append(
                {
                    **source,
                    "hot": None,
                    "disposition": "INVALID_CANDIDATE",
                    "candidate_rank": None,
                }
            )
            continue
        hot = make_hot_item(raw, source["lane"])
        if not authority_safe(raw):
            analyzed.append(
                {
                    **source,
                    "hot": hot,
                    "disposition": "UNSAFE_AUTHORITY_FILTERED",
                    "candidate_rank": None,
                }
            )
            continue
        row = {
            **source,
            "hot": hot,
            "disposition": None,
            "candidate_rank": None,
        }
        analyzed.append(row)
        safe_candidates.append(row)

    sorted_safe = sorted(
        safe_candidates,
        key=lambda row: (
            -int(row["hot"].get("priority_score") or 0),
            str(row["hot"].get("hot_uid") or ""),
        ),
    )
    winner_by_uid: Dict[str, Dict[str, Any]] = {}
    duplicate_losers: list[Dict[str, Any]] = []
    for row in sorted_safe:
        uid = str(row["hot"].get("hot_uid") or "")
        if uid not in winner_by_uid:
            winner_by_uid[uid] = row
        else:
            duplicate_losers.append(row)

    for index, contract_item in enumerate(admission_queue):
        uid = admission_uids[index]
        winner = winner_by_uid.get(uid)
        if winner is None:
            raise ValueError(f"ADMISSION_CONTRACT_UID_NOT_FOUND:{uid}")
        if canonical_json_bytes(winner["hot"]) != canonical_json_bytes(contract_item):
            raise ValueError(f"ADMISSION_CONTRACT_PAYLOAD_MISMATCH:{uid}")

    admitted_rows: list[Dict[str, Any]] = []
    for rank, uid in enumerate(admission_uids, start=1):
        row = winner_by_uid[uid]
        row["candidate_rank"] = rank
        row["disposition"] = "ADMITTED"
        admitted_rows.append(row)

    remaining = [
        row
        for row in sorted_safe
        if winner_by_uid[str(row["hot"].get("hot_uid") or "")] is row
        and str(row["hot"].get("hot_uid") or "") not in set(admission_uids)
    ]
    for offset, row in enumerate(remaining, start=queue_capacity + 1):
        row["candidate_rank"] = offset
        row["disposition"] = "OVERFLOW_TRUNCATED"

    rank_by_winner_source = {
        int(row["source_index"]): int(row["candidate_rank"])
        for row in winner_by_uid.values()
    }
    replaced_count = 0
    duplicate_count = 0
    for loser in duplicate_losers:
        uid = str(loser["hot"].get("hot_uid") or "")
        winner = winner_by_uid[uid]
        loser_priority = int(loser["hot"].get("priority_score") or 0)
        winner_priority = int(winner["hot"].get("priority_score") or 0)
        was_earlier = int(loser["source_index"]) < int(winner["source_index"])
        if was_earlier and loser_priority < winner_priority:
            loser["disposition"] = "REPLACED_BY_HIGHER_PRIORITY"
            replaced_count += 1
        else:
            loser["disposition"] = "DUPLICATE_REMOVED"
            duplicate_count += 1
        loser["candidate_rank"] = rank_by_winner_source[int(winner["source_index"])]

    analyzed.sort(key=lambda row: int(row["source_index"]))
    winners = list(winner_by_uid.values())
    overflow = [row for row in winners if row["disposition"] == "OVERFLOW_TRUNCATED"]
    unsafe = [row for row in analyzed if row["disposition"] == "UNSAFE_AUTHORITY_FILTERED"]
    invalid = [row for row in analyzed if row["disposition"] == "INVALID_CANDIDATE"]
    lowest_admitted_priority = min(
        (int(row["hot"]["priority_score"]) for row in admitted_rows),
        default=None,
    )
    highest_overflow_priority = max(
        (int(row["hot"]["priority_score"]) for row in overflow),
        default=None,
    )

    ledger_rows: list[Dict[str, Any]] = []
    for row in analyzed:
        disposition = str(row["disposition"])
        hot = row.get("hot")
        payload_value = (
            hot
            if disposition == "ADMITTED"
            else compact_nonadmitted_payload(row, hot, disposition)
        )
        payload_json = encode_payload(payload_value)
        source_candidate_uid = (
            str((hot or {}).get("hot_uid") or "")
            or f"source_{row['source_index']}"
        )
        disposition_uid = "disp_" + sha256_bytes(
            canonical_json_bytes(
                {
                    "batch_uid": batch_uid,
                    "source_index": row["source_index"],
                    "disposition": disposition,
                    "source_candidate_uid": source_candidate_uid,
                }
            )
        )[:32]
        ledger_rows.append(
            {
                "disposition_uid": disposition_uid,
                "batch_uid": batch_uid,
                "source_index": int(row["source_index"]),
                "source_candidate_uid": source_candidate_uid,
                "hot_uid": (hot or {}).get("hot_uid"),
                "event_uid": (hot or {}).get("event_uid"),
                "news_uid": (hot or {}).get("news_uid"),
                "lane": (hot or {}).get("lane") or row.get("lane"),
                "priority_score": (hot or {}).get("priority_score"),
                "candidate_rank": row.get("candidate_rank"),
                "disposition": disposition,
                "reason_code": DISPOSITION_REASON[disposition],
                "lowest_admitted_priority": lowest_admitted_priority,
                "highest_overflow_priority": highest_overflow_priority,
                "source_snapshot_hash": source_snapshot_hash,
                "payload_json": payload_json,
            }
        )

    counts = {
        "source_candidate_count": len(source_rows),
        "normalized_candidate_count": len(safe_candidates),
        "deduplicated_candidate_count": len(winners) + replaced_count,
        "admitted_count": len(admitted_rows),
        "overflow_count": len(overflow),
        "duplicate_removed_count": duplicate_count,
        "unsafe_filtered_count": len(unsafe),
        "invalid_candidate_count": len(invalid),
        "replaced_count": replaced_count,
    }
    if counts["source_candidate_count"] != sum(
        counts[key]
        for key in (
            "admitted_count",
            "overflow_count",
            "duplicate_removed_count",
            "unsafe_filtered_count",
            "invalid_candidate_count",
            "replaced_count",
        )
    ):
        raise AssertionError("SOURCE_ACCOUNTING_MISMATCH")
    if counts["normalized_candidate_count"] != (
        counts["deduplicated_candidate_count"]
        + counts["duplicate_removed_count"]
    ):
        raise AssertionError("NORMALIZED_ACCOUNTING_MISMATCH")
    if counts["deduplicated_candidate_count"] != (
        counts["admitted_count"]
        + counts["overflow_count"]
        + counts["replaced_count"]
    ):
        raise AssertionError("DEDUPLICATED_ACCOUNTING_MISMATCH")

    return {
        "policy_version": policy_version,
        "queue_capacity": queue_capacity,
        "batch_uid": batch_uid,
        "source_snapshot_hash": source_snapshot_hash,
        "admission_contract_hash": admission_contract_hash,
        "counts": counts,
        "lowest_admitted_priority": lowest_admitted_priority,
        "highest_overflow_priority": highest_overflow_priority,
        "ledger_rows": ledger_rows,
        "hot_queue": [row["hot"] for row in admitted_rows],
    }


def write_and_publish_with_admission_contract(
    *,
    display_path: Path,
    admission_queue: list[Dict[str, Any]],
    summary_path: Path,
    db_path: Path,
    output_path: Path,
    recovery_state_path: Path,
    contract_seed_path: Optional[Path],
    lock_path: Optional[Path] = None,
    inject_failure_after_ledger_rows: bool = False,
) -> Dict[str, Any]:
    display = read_json(display_path)
    plan = build_plan_with_admission_contract(display, admission_queue)

    def execute() -> Dict[str, Any]:
        write_result = write_plan(
            db_path,
            plan,
            inject_failure_after_ledger_rows=inject_failure_after_ledger_rows,
        )
        publish_result = recover_committed_batch(
            db_path,
            output_path,
            recovery_state_path,
            contract_seed_path=contract_seed_path,
            batch_sequence=int(write_result["batch_sequence"]),
        )
        return {
            "status": "OK_LEDGER_BATCH_AND_OUTPUT_CONVERGED",
            "batch_uid": plan["batch_uid"],
            "batch_sequence": int(write_result["batch_sequence"]),
            "write_result": write_result,
            "publish_result": publish_result,
            "counts": plan["counts"],
            "hot_queue_count": len(plan["hot_queue"]),
            "source_snapshot_hash": plan["source_snapshot_hash"],
            "admission_contract_hash": plan["admission_contract_hash"],
            "display_path": str(display_path),
            "summary_path": str(summary_path),
            "db_path": str(db_path),
            "output_path": str(output_path),
        }

    if lock_path is None:
        return execute()
    with single_instance_lock(lock_path) as lock_handle:
        if lock_handle is None:
            return {
                "status": "WRITER_ALREADY_ACTIVE",
                "db_write_performed": False,
                "output_path": str(output_path),
            }
        return execute()
'''


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_guard(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    stat = path.stat()
    return {
        "exists": True,
        "sha256": sha256_file(path),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def service_guard() -> dict[str, Any]:
    result = subprocess.run(
        [
            "systemctl",
            "show",
            "tokenoskobi-news-radar-refresh.service",
            "-p",
            "Environment",
            "-p",
            "ExecStart",
        ],
        text=True,
        capture_output=True,
    )
    text = result.stdout.strip()
    return {
        "rc": result.returncode,
        "stdout": text,
        "writer_enabled_explicitly": "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text,
        "runner_lock_enabled_explicitly": "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text,
    }


def db_guard() -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        return {
            "batch_rows": int(connection.execute("SELECT COUNT(*) FROM news_disposition_batches_v2").fetchone()[0]),
            "ledger_rows": int(connection.execute("SELECT COUNT(*) FROM news_disposition_ledger_v2").fetchone()[0]),
            "integrity_check": str(connection.execute("PRAGMA integrity_check").fetchone()[0]),
            "quick_check": str(connection.execute("PRAGMA quick_check").fetchone()[0]),
            "foreign_key_check_rows": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
        }
    finally:
        connection.close()


def production_guard() -> dict[str, Any]:
    return {
        "database": file_guard(DB),
        "market": file_guard(MARKET),
        "adversarial": file_guard(ADVERSARIAL),
        "display": file_guard(DISPLAY),
        "hot_output": file_guard(HOT_OUTPUT),
        "recovery_state": file_guard(RECOVERY_STATE),
        "database_state": db_guard(),
        "service": service_guard(),
    }


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def backup_sqlite(source: Path, target: Path) -> None:
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target_connection = sqlite3.connect(target)
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(
        rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)", re.DOTALL
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND:{heading}")
    return text[: match.start()] + heading + "\n\n" + body.rstrip() + "\n" + text[match.end() :]


def stable_snapshot(temp_dir: Path, attempts: int = 6) -> dict[str, Path]:
    sources = {
        "market": MARKET,
        "adversarial": ADVERSARIAL,
        "display": DISPLAY,
        "hot": HOT_OUTPUT,
    }
    for _ in range(attempts):
        before = {name: file_guard(path) for name, path in sources.items()}
        copies: dict[str, Path] = {}
        for name, path in sources.items():
            target = temp_dir / f"snapshot_{name}{path.suffix}"
            shutil.copy2(path, target)
            copies[name] = target
        after = {name: file_guard(path) for name, path in sources.items()}
        if before == after and all(
            file_guard(copies[name]).get("sha256") == before[name].get("sha256")
            for name in sources
        ):
            return copies
        time.sleep(0.25)
    raise RuntimeError("STABLE_SNAPSHOT_FAILED")


def batch_metrics(db_path: Path, batch_uid: str) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT disposition, COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=? GROUP BY disposition",
            (batch_uid,),
        ).fetchall()
        return {
            "ledger_rows": int(connection.execute("SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?", (batch_uid,)).fetchone()[0]),
            "disposition_counts": {str(row[0]): int(row[1]) for row in rows},
            "batch_rows": int(connection.execute("SELECT COUNT(*) FROM news_disposition_batches_v2 WHERE batch_uid=?", (batch_uid,)).fetchone()[0]),
            "integrity_check": str(connection.execute("PRAGMA integrity_check").fetchone()[0]),
            "quick_check": str(connection.execute("PRAGMA quick_check").fetchone()[0]),
            "foreign_key_check_rows": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
        }
    finally:
        connection.close()


def main() -> int:
    if not EXPECTED_HEAD:
        raise RuntimeError("TOKENOSKOBI_EXPECTED_HEAD_REQUIRED")
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BRANCH_NOT_MAIN")
    if git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("UNEXPECTED_HEAD")
    if git("status", "--porcelain"):
        raise RuntimeError("WORKTREE_NOT_CLEAN")

    for path in (
        A14_ARTIFACT, EXTRACTOR, WRITER, RECOVERY, GATEWAY, MARKET,
        ADVERSARIAL, DISPLAY, SUMMARY, HOT_OUTPUT, DB, RUNTIME,
        HISTORY, MASTER, HANDOFF, ALMANAC,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    a14 = load_json(A14_ARTIFACT)
    assert a14["result"] == "REJECT_BOUNDED_CANARY_QUEUE_SEMANTIC_PARITY_NOT_PROVEN"
    assert a14["authorization"]["single_natural_cycle_bounded_canary_authorized"] is False

    original_text = {
        WRITER: WRITER.read_text(encoding="utf-8"),
        RUNTIME: RUNTIME.read_text(encoding="utf-8"),
        HISTORY: HISTORY.read_text(encoding="utf-8"),
        MASTER: MASTER.read_text(encoding="utf-8"),
        HANDOFF: HANDOFF.read_text(encoding="utf-8"),
        ALMANAC: ALMANAC.read_text(encoding="utf-8"),
    }
    guard_before = production_guard()
    temp_dir = Path(tempfile.mkdtemp(prefix="era55a15_plain_", dir="/tmp"))
    committed = False

    try:
        writer_text = original_text[WRITER]
        if PATCH_MARKER not in writer_text:
            WRITER.write_text(writer_text.rstrip() + ADMISSION_PATCH + "\n", encoding="utf-8")
        compile(WRITER.read_text(encoding="utf-8"), str(WRITER), "exec")

        extractor = import_module("a15_extractor", EXTRACTOR)
        writer = import_module("a15_writer", WRITER)
        gateway = import_module("a15_gateway", GATEWAY)
        recovery = import_module("a15_recovery", RECOVERY)

        snap = stable_snapshot(temp_dir)
        display = load_json(snap["display"])
        current_hot = load_json(snap["hot"])
        legacy_queue = gateway.normalize_items(display)
        assert legacy_queue == current_hot.get("hot_queue")

        candidate_display = extractor.build_candidate_display(snap["market"], snap["adversarial"])
        candidate_path = temp_dir / "candidate_display.json"
        write_json(candidate_path, candidate_display)

        standard_plan = writer.build_plan(candidate_display, queue_capacity=50)
        repaired_plan = writer.build_plan_with_admission_contract(candidate_display, legacy_queue)
        assert standard_plan["hot_queue"] != legacy_queue
        assert repaired_plan["hot_queue"] == legacy_queue

        source_count = int(repaired_plan["counts"]["source_candidate_count"])
        accounted = sum(
            int(repaired_plan["counts"][key])
            for key in (
                "admitted_count", "overflow_count", "duplicate_removed_count",
                "unsafe_filtered_count", "invalid_candidate_count", "replaced_count",
            )
        )
        assert source_count == accounted
        assert int(repaired_plan["counts"]["admitted_count"]) == len(legacy_queue)

        temp_db = temp_dir / "parity.sqlite"
        backup_sqlite(DB, temp_db)
        temp_output = temp_dir / "hot_output.json"
        temp_state = temp_dir / "recovery_state.json"
        temp_lock = temp_dir / "writer.lock"

        first = writer.write_and_publish_with_admission_contract(
            display_path=candidate_path,
            admission_queue=legacy_queue,
            summary_path=SUMMARY,
            db_path=temp_db,
            output_path=temp_output,
            recovery_state_path=temp_state,
            contract_seed_path=snap["hot"],
            lock_path=temp_lock,
        )
        first_hash = sha256_file(temp_output)
        assert load_json(temp_output).get("hot_queue") == legacy_queue

        second = writer.write_and_publish_with_admission_contract(
            display_path=candidate_path,
            admission_queue=legacy_queue,
            summary_path=SUMMARY,
            db_path=temp_db,
            output_path=temp_output,
            recovery_state_path=temp_state,
            contract_seed_path=snap["hot"],
            lock_path=temp_lock,
        )
        second_hash = sha256_file(temp_output)
        assert first["write_result"]["status"] == "COMMITTED"
        assert second["write_result"]["status"] == "IDEMPOTENT_REPLAY_NOOP"
        assert first_hash == second_hash

        metrics = batch_metrics(temp_db, repaired_plan["batch_uid"])
        assert metrics["batch_rows"] == 1
        assert metrics["ledger_rows"] == source_count
        assert metrics["integrity_check"] == "ok"
        assert metrics["quick_check"] == "ok"
        assert metrics["foreign_key_check_rows"] == 0

        temp_output.unlink()
        recovered = recovery.recover_committed_batch(
            temp_db,
            temp_output,
            temp_state,
            contract_seed_path=snap["hot"],
            batch_sequence=int(first["batch_sequence"]),
        )
        assert recovered["status"] == "RECOVERED"
        assert load_json(temp_output).get("hot_queue") == legacy_queue

        fail_closed: dict[str, str] = {}
        tests = {
            "duplicate_uid_error": [legacy_queue[0], legacy_queue[0]],
            "unknown_uid_error": [
                {**legacy_queue[0], "hot_uid": "hot_unknown_contract_uid"},
                *legacy_queue[1:],
            ],
            "payload_drift_error": [
                {**legacy_queue[0], "title": str(legacy_queue[0].get("title") or "") + " drift"},
                *legacy_queue[1:],
            ],
        }
        for key, queue in tests.items():
            try:
                writer.build_plan_with_admission_contract(candidate_display, queue)
            except ValueError as exc:
                fail_closed[key] = str(exc)
            else:
                raise AssertionError(f"FAIL_CLOSED_TEST_DID_NOT_FAIL:{key}")
        assert fail_closed["duplicate_uid_error"].startswith("ADMISSION_CONTRACT_DUPLICATE_UID:")
        assert fail_closed["unknown_uid_error"].startswith("ADMISSION_CONTRACT_UID_NOT_FOUND:")
        assert fail_closed["payload_drift_error"].startswith("ADMISSION_CONTRACT_PAYLOAD_MISMATCH:")

        rollback_db = temp_dir / "rollback.sqlite"
        backup_sqlite(DB, rollback_db)
        injected_error = None
        try:
            writer.write_plan(rollback_db, repaired_plan, inject_failure_after_ledger_rows=True)
        except RuntimeError as exc:
            injected_error = str(exc)
        assert injected_error == "INJECTED_FAILURE_AFTER_LEDGER_ROWS"
        rollback_connection = sqlite3.connect(f"file:{rollback_db}?mode=ro", uri=True)
        try:
            rollback_batch_rows = int(rollback_connection.execute("SELECT COUNT(*) FROM news_disposition_batches_v2").fetchone()[0])
            rollback_ledger_rows = int(rollback_connection.execute("SELECT COUNT(*) FROM news_disposition_ledger_v2").fetchone()[0])
        finally:
            rollback_connection.close()
        assert rollback_batch_rows == 0
        assert rollback_ledger_rows == 0

        guard_after = production_guard()
        assert guard_before == guard_after

        now = utc_now()
        artifact = {
            "schema_version": "1.0",
            "work_unit": "ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST",
            "tested_at_utc": now,
            "status": "CLOSED_TEMP_COPY_PARITY_REPAIR_OK",
            "result": RESULT,
            "writer_module": {
                "path": str(WRITER.relative_to(ROOT)),
                "sha256": sha256_file(WRITER),
                "policy_version": POLICY_VERSION,
                "admission_contract_function_present": True,
                "production_runtime_bound": False,
            },
            "parity_repair": {
                "source_candidate_count": source_count,
                "accounted_count": accounted,
                "unobservable_rows": source_count - accounted,
                "legacy_queue_count": len(legacy_queue),
                "ledger_rows": metrics["ledger_rows"],
                "standard_pre_gateway_queue_mismatched_before_repair": True,
                "repaired_queue_exact_object_parity": True,
                "repaired_queue_exact_uid_order_parity": True,
                "legacy_uid_hash": hashlib.sha256("\n".join(str(item.get("hot_uid")) for item in legacy_queue).encode()).hexdigest(),
                "repaired_uid_hash": hashlib.sha256("\n".join(str(item.get("hot_uid")) for item in repaired_plan["hot_queue"]).encode()).hexdigest(),
                "counts": repaired_plan["counts"],
                "disposition_counts": metrics["disposition_counts"],
            },
            "idempotency": {
                "first_write_status": first["write_result"]["status"],
                "second_write_status": second["write_result"]["status"],
                "output_hash_unchanged": first_hash == second_hash,
                "batch_rows_after_replay": metrics["batch_rows"],
                "ledger_rows_after_replay": metrics["ledger_rows"],
            },
            "postcommit_publish_recovery": {
                "status": recovered["status"],
                "exact_legacy_queue_parity": True,
                "db_rewrite": False,
            },
            "fail_closed_contract_tests": {**fail_closed, "all_passed": True},
            "transaction_rollback": {
                "injected_error": injected_error,
                "batch_rows_after_rollback": rollback_batch_rows,
                "ledger_rows_after_rollback": rollback_ledger_rows,
                "ok": True,
            },
            "production_guard_before": guard_before,
            "production_guard_after": guard_after,
            "production_ledger_unchanged": True,
            "authorization": {
                "single_natural_cycle_bounded_canary_authorized": False,
                "general_production_writer_activation_authorized": False,
                "production_writer_active": False,
                "p0_f1_closed": False,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
            },
            "next_safe_step": NEXT_STEP,
        }
        write_json(ARTIFACT, artifact)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            "\n".join(
                [
                    "# ERA55A15 Queue Semantic Parity Repair",
                    "",
                    "- Status: `CLOSED_TEMP_COPY_PARITY_REPAIR_OK`",
                    f"- Result: `{RESULT}`",
                    f"- Source candidates: `{source_count}`",
                    f"- Legacy queue: `{len(legacy_queue)}`",
                    "- Unobservable rows: `0`",
                    "- Exact object parity: `true`",
                    "- Exact UID order parity: `true`",
                    "- Idempotent replay: `true`",
                    "- Post-commit recovery parity: `true`",
                    "- Fail-closed contract tests: `true`",
                    "- Production runtime bound: `false`",
                    "- Production unchanged: `true`",
                    f"- Next safe step: `{NEXT_STEP}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        runtime = load_json(RUNTIME)
        state = runtime["current_state"]
        state["mode"] = "ERA55A15_QUEUE_SEMANTIC_PARITY_REPAIR_TEMP_COPY_OK"
        state["runtime_status"] = "WORK_UNIT_CLOSED"
        state["updated_at"] = now
        state["last_action"] = {
            "timestamp": now,
            "task": "ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST",
            "result": RESULT,
            "artifact": str(ARTIFACT.relative_to(ROOT)),
        }
        state["active_work_unit"] = {
            "id": "ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST",
            "type": "ERA55_P0_QUEUE_SEMANTIC_PARITY_REPAIR_TEMP_COPY_TEST",
            "parent": "ERA55_RUNTIME_OPTIMIZATION",
            "artifact": str(ARTIFACT.relative_to(ROOT)),
            "status": "CLOSED_TEMP_COPY_PARITY_REPAIR_OK",
            "result": RESULT,
            "production_mutation": False,
            "next_step": NEXT_STEP,
        }
        state["next_safe_step"] = {
            "id": NEXT_STEP,
            "type": "ERA55_P0_QUEUE_PARITY_POST_TEST_AUDIT_SINGLE_CYCLE_CANARY_DECISION",
            "parent": "ERA55_RUNTIME_OPTIMIZATION",
            "purpose": "Independently audit exact legacy output parity and decide whether one guarded natural-cycle canary may be authorized.",
            "human_authorization_required": True,
            "single_cycle_bounded_canary_authorized": False,
            "general_production_writer_activation_authorized": False,
            "option_b_authorized": False,
            "optimization_apply_authorized": False,
            "status": "READY",
        }
        state["current_problem"] = {
            "code": "QUEUE_PARITY_REPAIR_NOT_YET_INDEPENDENTLY_AUDITED",
            "severity": "P0",
            "evidence": str(ARTIFACT.relative_to(ROOT)),
        }
        runtime["current_work_unit"] = state["active_work_unit"]
        write_json(RUNTIME, runtime)

        history = load_json(HISTORY)
        events = history.setdefault("events", [])
        event_id = "ERA55A15_QUEUE_SEMANTIC_PARITY_REPAIR_TEMP_COPY_V1"
        if not any(isinstance(event, dict) and event.get("event_id") == event_id for event in events):
            events.append(
                {
                    "event_id": event_id,
                    "timestamp_utc": now,
                    "era": "ERA55",
                    "work_unit": "ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST",
                    "event": "TEMP_COPY_PARITY_REPAIR_TEST",
                    "status": "CLOSED_TEMP_COPY_PARITY_REPAIR_OK",
                    "result": RESULT,
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "source_candidate_count": source_count,
                    "unobservable_rows": 0,
                    "exact_legacy_queue_parity": True,
                    "production_unchanged": True,
                    "single_cycle_bounded_canary_authorized": False,
                    "p0_f1_closed": False,
                    "next_safe_step": NEXT_STEP,
                }
            )
        history["updated_at"] = now
        history["updated_at_utc"] = now
        write_json(HISTORY, history)

        master = replace_section(
            original_text[MASTER],
            "## 01 PROJECT STATUS",
            """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_P0_QUEUE_PARITY_AUDIT_PENDING
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
CURRENT_STAGE=ERA55A_P0_QUEUE_PARITY_POST_TEST_AUDIT
LAST_COMPLETED_SUBSTEP=ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST
SOURCE_CANDIDATES={source_count}
UNOBSERVABLE_ROWS=0
LEGACY_QUEUE_EXACT_OBJECT_PARITY=true
LEGACY_QUEUE_EXACT_UID_ORDER_PARITY=true
PRODUCTION_LEDGER_WRITER_ACTIVE=false
SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED=false
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

A15 repaired output semantics on a disposable database copy while preserving complete ledger accounting.""",
        )
        master = replace_section(
            master,
            "## 03 LAST VERIFIED WORK",
            f"""```text
LAST_COMPLETED=ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS=CLOSED_TEMP_COPY_PARITY_REPAIR_OK
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
```

NEXT_SAFE_STEP={NEXT_STEP}""",
        )
        MASTER.write_text(master, encoding="utf-8")

        handoff = replace_section(
            original_text[HANDOFF],
            "## 02 CURRENT CONTINUATION CHECKPOINT",
            f"""PROJECT_STATUS=ACTIVE_ERA55_P0_QUEUE_PARITY_AUDIT_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_QUEUE_PARITY_POST_TEST_AUDIT
LAST_COMPLETED_SUBSTEP=ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST
SOURCE_CANDIDATES={source_count}
UNOBSERVABLE_ROWS=0
LEGACY_QUEUE_EXACT_OBJECT_PARITY=true
LEGACY_QUEUE_EXACT_UID_ORDER_PARITY=true
PRODUCTION_LEDGER_WRITER_ACTIVE=false
SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED=false
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""",
        )
        handoff = replace_section(
            handoff,
            "## 03 LAST VERIFIED WORK",
            f"""LAST_COMPLETED=ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS=CLOSED_TEMP_COPY_PARITY_REPAIR_OK
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=QUEUE_PARITY_REPAIR_NOT_YET_INDEPENDENTLY_AUDITED""",
        )
        handoff = replace_section(
            handoff,
            "## 06 DO NOT REOPEN OR REPEAT",
            """- Do not rerun A9-A15 unless evidence is invalidated.
- Do not use the broken compressed A15 wrapper.
- Do not activate production before A16 independent audit.
- Do not change legacy gateway queue semantics.
- Do not start Option B or close P0 F1.""",
        )
        handoff = replace_section(
            handoff,
            "## 07 ALLOWED NEXT DECISIONS",
            f"""- Complete ledger accounting: `VALIDATED`.
- Legacy queue exact object parity: `VALIDATED_TEMP_COPY`.
- Legacy queue exact UID order parity: `VALIDATED_TEMP_COPY`.
- Single-cycle bounded canary: `PENDING_A16_DECISION`.
- General production activation: `BLOCKED`.

NEXT_SAFE_STEP={NEXT_STEP}""",
        )
        handoff = replace_section(
            handoff,
            "## 08 NEXT SESSION EXECUTION RULE",
            """1. Confirm A16 is current.
2. Independently audit the A15 writer patch and artifact.
3. Rebuild the complete stream and legacy admission contract on temp copy.
4. Verify exact object and UID order parity, recovery and production guards.
5. Decide only whether one guarded natural-cycle canary may be authorized.
6. Do not authorize general production or close P0 F1.""",
        )
        HANDOFF.write_text(handoff, encoding="utf-8")

        almanac = original_text[ALMANAC]
        marker = "## ERA55A_15 QUEUE SEMANTIC PARITY REPAIR"
        if marker not in almanac:
            almanac = almanac.rstrip() + f"""

---

{marker}

- Status: `CLOSED_TEMP_COPY_PARITY_REPAIR_OK`
- Result: `{RESULT}`
- Source candidates: `{source_count}`
- Unobservable rows: `0`
- Exact legacy object parity: `true`
- Exact legacy UID order parity: `true`
- Production mutation: `false`
- Single-cycle bounded canary authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `{NEXT_STEP}`
""" + "\n"
        ALMANAC.write_text(almanac, encoding="utf-8")

        git(
            "add",
            str(WRITER.relative_to(ROOT)),
            str(ARTIFACT.relative_to(ROOT)),
            str(RUNTIME.relative_to(ROOT)),
            str(HISTORY.relative_to(ROOT)),
            str(MASTER.relative_to(ROOT)),
            str(HANDOFF.relative_to(ROOT)),
            str(ALMANAC.relative_to(ROOT)),
        )
        subprocess.run(
            ["git", "add", "-f", str(REPORT.relative_to(ROOT))], cwd=ROOT, check=True
        )
        git("commit", "-m", COMMIT_SUBJECT)
        committed = True

        print("ERA55A15_PLAIN_PARITY_REPAIR=SUCCESS")
        print("RESULT=" + RESULT)
        print("SOURCE_CANDIDATES=" + str(source_count))
        print("SOURCE_ACCOUNTED=" + str(accounted))
        print("UNOBSERVABLE_ROWS=0")
        print("LEGACY_QUEUE_EXACT_OBJECT_PARITY=true")
        print("LEGACY_QUEUE_EXACT_UID_ORDER_PARITY=true")
        print("IDEMPOTENT_REPLAY=true")
        print("POSTCOMMIT_PUBLISH_RECOVERY_PARITY=true")
        print("FAIL_CLOSED_CONTRACT_TESTS=true")
        print("TRANSACTION_ROLLBACK=true")
        print("PRODUCTION_RUNTIME_BOUND=false")
        print("PRODUCTION_LEDGER_UNCHANGED=true")
        print("SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED=false")
        print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print("NEXT_SAFE_STEP=" + NEXT_STEP)
        print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
        return 0
    except BaseException:
        if not committed:
            for path, text in original_text.items():
                path.write_text(text, encoding="utf-8")
            for path in (ARTIFACT, REPORT):
                if path.exists():
                    path.unlink()
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
