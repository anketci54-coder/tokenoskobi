#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import news_disposition_ledger_writer_v1 as writer

POLICY_VERSION = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"


def _canonical(value: Any) -> bytes:
    return writer.canonical_json_bytes(value)


def _validate_contract(admission_queue: Any, queue_capacity: int) -> list[Dict[str, Any]]:
    if not isinstance(admission_queue, list):
        raise ValueError("ADMISSION_CONTRACT_QUEUE_NOT_LIST")
    if queue_capacity <= 0:
        raise ValueError("QUEUE_CAPACITY_MUST_BE_POSITIVE")
    if len(admission_queue) > queue_capacity:
        raise ValueError("ADMISSION_CONTRACT_EXCEEDS_QUEUE_CAPACITY")

    result: list[Dict[str, Any]] = []
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
        result.append(item)
    return result


def build_plan_with_admission_contract(
    display: Dict[str, Any],
    admission_queue: Any,
    *,
    queue_capacity: int = writer.DEFAULT_QUEUE_CAPACITY,
    policy_version: str = POLICY_VERSION,
) -> Dict[str, Any]:
    contract = _validate_contract(admission_queue, queue_capacity)
    source_rows = list(writer.iter_source_candidates(display))
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
    source_snapshot_hash = writer.sha256_bytes(_canonical(snapshot_projection))
    admission_contract_hash = writer.sha256_bytes(_canonical(contract))
    batch_uid = "batch_" + writer.sha256_bytes(
        _canonical(
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

        hot = writer.make_hot_item(raw, source["lane"])
        if not writer.authority_safe(raw):
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
        winner = winner_by_uid.get(uid)
        if winner is None:
            winner_by_uid[uid] = row
        else:
            duplicate_losers.append(row)

    contract_uids: list[str] = []
    for item in contract:
        uid = str(item["hot_uid"])
        winner = winner_by_uid.get(uid)
        if winner is None:
            raise ValueError(f"ADMISSION_CONTRACT_UID_NOT_FOUND:{uid}")
        if _canonical(winner["hot"]) != _canonical(item):
            raise ValueError(f"ADMISSION_CONTRACT_PAYLOAD_MISMATCH:{uid}")
        contract_uids.append(uid)

    contract_rank = {uid: rank for rank, uid in enumerate(contract_uids, start=1)}
    overflow_winners = [
        row
        for uid, row in winner_by_uid.items()
        if uid not in contract_rank
    ]
    overflow_winners.sort(
        key=lambda row: (
            -int(row["hot"].get("priority_score") or 0),
            str(row["hot"].get("hot_uid") or ""),
        )
    )

    for uid in contract_uids:
        row = winner_by_uid[uid]
        row["candidate_rank"] = contract_rank[uid]
        row["disposition"] = "ADMITTED"

    for offset, row in enumerate(overflow_winners, start=len(contract_uids) + 1):
        row["candidate_rank"] = offset
        row["disposition"] = "OVERFLOW_TRUNCATED"

    winner_rank = {
        str(row["hot"].get("hot_uid") or ""): int(row["candidate_rank"])
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

        loser["candidate_rank"] = winner_rank[uid]

    analyzed.sort(key=lambda row: int(row["source_index"]))
    admitted = [winner_by_uid[uid] for uid in contract_uids]
    overflow = overflow_winners
    unsafe = [
        row
        for row in analyzed
        if row["disposition"] == "UNSAFE_AUTHORITY_FILTERED"
    ]
    invalid = [
        row
        for row in analyzed
        if row["disposition"] == "INVALID_CANDIDATE"
    ]
    lowest_admitted_priority = min(
        (int(row["hot"]["priority_score"]) for row in admitted),
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
            else writer.compact_nonadmitted_payload(row, hot, disposition)
        )
        payload_json = writer.encode_payload(payload_value)
        source_candidate_uid = (
            str((hot or {}).get("hot_uid") or "")
            or f"source_{row['source_index']}"
        )
        disposition_uid = "disp_" + writer.sha256_bytes(
            _canonical(
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
                "reason_code": writer.DISPOSITION_REASON[disposition],
                "lowest_admitted_priority": lowest_admitted_priority,
                "highest_overflow_priority": highest_overflow_priority,
                "source_snapshot_hash": source_snapshot_hash,
                "payload_json": payload_json,
            }
        )

    counts = {
        "source_candidate_count": len(source_rows),
        "normalized_candidate_count": len(safe_candidates),
        "deduplicated_candidate_count": len(winner_by_uid) + replaced_count,
        "admitted_count": len(admitted),
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

    hot_queue = [winner_by_uid[uid]["hot"] for uid in contract_uids]
    if _canonical(hot_queue) != _canonical(contract):
        raise AssertionError("ADMISSION_CONTRACT_OUTPUT_PARITY_FAILED")

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
        "hot_queue": hot_queue,
    }


def _read_admission_queue(path: Path) -> list[Dict[str, Any]]:
    payload = writer.read_json(path)
    queue = payload.get("hot_queue")
    if not isinstance(queue, list):
        raise ValueError("ADMISSION_CONTRACT_HOT_QUEUE_NOT_LIST")
    return queue


def write_and_publish_with_admission_contract(
    *,
    display_path: Path,
    admission_contract_path: Path,
    summary_path: Path,
    db_path: Path,
    output_path: Path,
    recovery_state_path: Path,
    contract_seed_path: Optional[Path],
    queue_capacity: int = writer.DEFAULT_QUEUE_CAPACITY,
    lock_path: Optional[Path] = None,
    inject_failure_after_ledger_rows: bool = False,
) -> Dict[str, Any]:
    display = writer.read_json(display_path)
    admission_queue = _read_admission_queue(admission_contract_path)
    plan = build_plan_with_admission_contract(
        display,
        admission_queue,
        queue_capacity=queue_capacity,
    )

    def execute() -> Dict[str, Any]:
        write_result = writer.write_plan(
            db_path,
            plan,
            inject_failure_after_ledger_rows=inject_failure_after_ledger_rows,
        )
        publish_result = writer.recover_committed_batch(
            db_path,
            output_path,
            recovery_state_path,
            contract_seed_path=contract_seed_path,
            batch_sequence=int(write_result["batch_sequence"]),
        )
        return {
            "status": "OK_LEDGER_BATCH_AND_CONTRACT_OUTPUT_CONVERGED",
            "batch_uid": plan["batch_uid"],
            "batch_sequence": int(write_result["batch_sequence"]),
            "write_result": write_result,
            "publish_result": publish_result,
            "counts": plan["counts"],
            "hot_queue_count": len(plan["hot_queue"]),
            "source_snapshot_hash": plan["source_snapshot_hash"],
            "admission_contract_hash": plan["admission_contract_hash"],
            "display_path": str(display_path),
            "admission_contract_path": str(admission_contract_path),
            "summary_path": str(summary_path),
            "db_path": str(db_path),
            "output_path": str(output_path),
        }

    if lock_path is None:
        return execute()

    with writer.single_instance_lock(lock_path) as lock_handle:
        if lock_handle is None:
            return {
                "status": "WRITER_ALREADY_ACTIVE",
                "db_write_performed": False,
                "output_path": str(output_path),
            }
        return execute()
