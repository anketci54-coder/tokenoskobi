#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
sys.dont_write_bytecode = True
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from news_ledger_recovery_guard_v1 import recover_committed_batch, single_instance_lock

POLICY_VERSION = "PRIORITY_DESC_THEN_HOT_UID_TOP_50_LEDGER_V2"
DEFAULT_QUEUE_CAPACITY = 50
MAX_PAYLOAD_BYTES = 16384
REQUIRED_AUTHORITY_FALSE = ("db_write", "hunter_authorized", "trade_signal", "paper_signal")
DISPOSITION_REASON = {
    "ADMITTED": "TOP_50_ADMITTED",
    "DUPLICATE_REMOVED": "DUPLICATE_HOT_UID",
    "UNSAFE_AUTHORITY_FILTERED": "UNSAFE_AUTHORITY",
    "OVERFLOW_TRUNCATED": "QUEUE_OVERFLOW",
    "REPLACED_BY_HIGHER_PRIORITY": "HIGHER_PRIORITY_REPLACEMENT",
    "INVALID_CANDIDATE": "INVALID_INPUT",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def uid_for(obj: Dict[str, Any], lane: str) -> str:
    raw = "|".join([lane, str(obj.get("event_uid") or ""), str(obj.get("news_uid") or ""), str(obj.get("title") or "")])
    return "hot_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def score_item(item: Dict[str, Any], lane: str) -> int:
    hits = item.get("hits") if isinstance(item.get("hits"), list) else []
    base = len(hits) * 10
    if lane == "ADVERSARIAL_NEWS":
        base += 15
    if item.get("published_at_utc"):
        base += 5
    return base


def authority_safe(item: Dict[str, Any]) -> bool:
    authority = item.get("authority") if isinstance(item.get("authority"), dict) else {}
    return all(authority.get(key) is False for key in REQUIRED_AUTHORITY_FALSE)


def make_hot_item(item: Dict[str, Any], lane: str) -> Dict[str, Any]:
    return {
        "hot_uid": uid_for(item, lane),
        "lane": lane,
        "event_uid": item.get("event_uid"),
        "news_uid": item.get("news_uid"),
        "title": item.get("title"),
        "hits": item.get("hits") or [],
        "published_at_utc": item.get("published_at_utc"),
        "source_uid": item.get("source_uid"),
        "priority_score": score_item(item, lane),
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


def iter_source_candidates(display: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    source_index = 0
    for section_index, section in enumerate(display.get("sections") or []):
        if not isinstance(section, dict):
            continue
        sid = section.get("id")
        if sid == "news_market_indicator":
            lane = "MARKET_INDICATOR"
        elif sid == "news_adversarial_intelligence":
            lane = "ADVERSARIAL_NEWS"
        else:
            continue
        items = section.get("items")
        if not isinstance(items, list):
            continue
        for item_index, raw in enumerate(items):
            yield {
                "source_index": source_index,
                "section_index": section_index,
                "item_index": item_index,
                "lane": lane,
                "raw": raw,
            }
            source_index += 1


def compact_nonadmitted_payload(source: Dict[str, Any], hot: Optional[Dict[str, Any]], disposition: str) -> Dict[str, Any]:
    raw = source["raw"]
    payload: Dict[str, Any] = {
        "source_index": int(source["source_index"]),
        "section_index": int(source["section_index"]),
        "item_index": int(source["item_index"]),
        "lane": source["lane"],
        "disposition": disposition,
        "raw_type": type(raw).__name__,
    }
    if hot is not None:
        payload.update({
            "hot_uid": hot.get("hot_uid"),
            "event_uid": hot.get("event_uid"),
            "news_uid": hot.get("news_uid"),
            "priority_score": hot.get("priority_score"),
        })
    elif isinstance(raw, dict):
        payload.update({
            "event_uid": raw.get("event_uid"),
            "news_uid": raw.get("news_uid"),
            "title": str(raw.get("title") or "")[:256],
        })
    else:
        payload["raw_preview"] = repr(raw)[:256]
    return payload


def encode_payload(value: Dict[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError("LEDGER_PAYLOAD_EXCEEDS_16384_BYTES")
    return encoded


def build_plan(display: Dict[str, Any], *, queue_capacity: int = DEFAULT_QUEUE_CAPACITY, policy_version: str = POLICY_VERSION) -> Dict[str, Any]:
    if queue_capacity <= 0:
        raise ValueError("QUEUE_CAPACITY_MUST_BE_POSITIVE")

    source_rows = list(iter_source_candidates(display))
    snapshot_projection = [{
        "source_index": row["source_index"],
        "section_index": row["section_index"],
        "item_index": row["item_index"],
        "lane": row["lane"],
        "raw": row["raw"],
    } for row in source_rows]
    source_snapshot_hash = sha256_bytes(canonical_json_bytes(snapshot_projection))
    batch_uid = "batch_" + sha256_bytes(canonical_json_bytes({
        "policy_version": policy_version,
        "queue_capacity": queue_capacity,
        "source_snapshot_hash": source_snapshot_hash,
    }))[:32]

    analyzed: list[Dict[str, Any]] = []
    safe_candidates: list[Dict[str, Any]] = []
    for source in source_rows:
        raw = source["raw"]
        if not isinstance(raw, dict):
            analyzed.append({**source, "hot": None, "disposition": "INVALID_CANDIDATE", "candidate_rank": None})
            continue
        hot = make_hot_item(raw, source["lane"])
        if not authority_safe(raw):
            analyzed.append({**source, "hot": hot, "disposition": "UNSAFE_AUTHORITY_FILTERED", "candidate_rank": None})
            continue
        row = {**source, "hot": hot, "disposition": None, "candidate_rank": None}
        analyzed.append(row)
        safe_candidates.append(row)

    sorted_safe = sorted(safe_candidates, key=lambda row: (-int(row["hot"].get("priority_score") or 0), str(row["hot"].get("hot_uid") or "")))
    winner_by_uid: Dict[str, Dict[str, Any]] = {}
    duplicate_losers: list[Dict[str, Any]] = []
    for row in sorted_safe:
        uid = str(row["hot"].get("hot_uid") or "")
        winner = winner_by_uid.get(uid)
        if winner is None:
            winner_by_uid[uid] = row
        else:
            duplicate_losers.append(row)

    winners = list(winner_by_uid.values())
    winner_rank = {int(row["source_index"]): rank for rank, row in enumerate(winners, start=1)}
    for rank, row in enumerate(winners, start=1):
        row["candidate_rank"] = rank
        row["disposition"] = "ADMITTED" if rank <= queue_capacity else "OVERFLOW_TRUNCATED"

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
        loser["candidate_rank"] = winner_rank[int(winner["source_index"])]

    analyzed.sort(key=lambda row: int(row["source_index"]))
    admitted = [row for row in winners if row["disposition"] == "ADMITTED"]
    overflow = [row for row in winners if row["disposition"] == "OVERFLOW_TRUNCATED"]
    unsafe = [row for row in analyzed if row["disposition"] == "UNSAFE_AUTHORITY_FILTERED"]
    invalid = [row for row in analyzed if row["disposition"] == "INVALID_CANDIDATE"]
    lowest_admitted_priority = min((int(row["hot"]["priority_score"]) for row in admitted), default=None)
    highest_overflow_priority = max((int(row["hot"]["priority_score"]) for row in overflow), default=None)

    ledger_rows: list[Dict[str, Any]] = []
    for row in analyzed:
        disposition = str(row["disposition"])
        hot = row.get("hot")
        payload_value = hot if disposition == "ADMITTED" else compact_nonadmitted_payload(row, hot, disposition)
        payload_json = encode_payload(payload_value)
        source_candidate_uid = str((hot or {}).get("hot_uid") or "") or f"source_{row['source_index']}"
        disposition_uid = "disp_" + sha256_bytes(canonical_json_bytes({
            "batch_uid": batch_uid,
            "source_index": row["source_index"],
            "disposition": disposition,
            "source_candidate_uid": source_candidate_uid,
        }))[:32]
        ledger_rows.append({
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
        })

    counts = {
        "source_candidate_count": len(source_rows),
        "normalized_candidate_count": len(safe_candidates),
        "deduplicated_candidate_count": len(winners) + replaced_count,
        "admitted_count": len(admitted),
        "overflow_count": len(overflow),
        "duplicate_removed_count": duplicate_count,
        "unsafe_filtered_count": len(unsafe),
        "invalid_candidate_count": len(invalid),
        "replaced_count": replaced_count,
    }
    if counts["source_candidate_count"] != sum(counts[key] for key in (
        "admitted_count", "overflow_count", "duplicate_removed_count", "unsafe_filtered_count", "invalid_candidate_count", "replaced_count"
    )):
        raise AssertionError("SOURCE_ACCOUNTING_MISMATCH")
    if counts["normalized_candidate_count"] != counts["deduplicated_candidate_count"] + counts["duplicate_removed_count"]:
        raise AssertionError("NORMALIZED_ACCOUNTING_MISMATCH")
    if counts["deduplicated_candidate_count"] != counts["admitted_count"] + counts["overflow_count"] + counts["replaced_count"]:
        raise AssertionError("DEDUPLICATED_ACCOUNTING_MISMATCH")

    return {
        "policy_version": policy_version,
        "queue_capacity": queue_capacity,
        "batch_uid": batch_uid,
        "source_snapshot_hash": source_snapshot_hash,
        "counts": counts,
        "lowest_admitted_priority": lowest_admitted_priority,
        "highest_overflow_priority": highest_overflow_priority,
        "ledger_rows": ledger_rows,
        "hot_queue": [row["hot"] for row in admitted],
    }


def connect_rw(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def verify_existing_batch(conn: sqlite3.Connection, plan: Dict[str, Any]) -> Dict[str, Any]:
    batch = conn.execute("SELECT rowid AS batch_sequence, * FROM news_disposition_batches_v2 WHERE batch_uid=?", (plan["batch_uid"],)).fetchone()
    if batch is None:
        raise RuntimeError("EXISTING_BATCH_NOT_FOUND")
    row = dict(batch)
    counts = plan["counts"]
    expected = {**counts, "policy_version": plan["policy_version"], "queue_capacity": plan["queue_capacity"], "source_snapshot_hash": plan["source_snapshot_hash"], "status": "COMMITTED"}
    for key, value in expected.items():
        if row.get(key) != value:
            raise RuntimeError(f"EXISTING_BATCH_MISMATCH:{key}")
    ledger_count = int(conn.execute("SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?", (plan["batch_uid"],)).fetchone()[0])
    if ledger_count != counts["source_candidate_count"]:
        raise RuntimeError("EXISTING_LEDGER_COUNT_MISMATCH")
    return {"status": "IDEMPOTENT_REPLAY_NOOP", "batch_uid": plan["batch_uid"], "batch_sequence": int(row["batch_sequence"]), "ledger_rows": ledger_count, "db_write_performed": False}


def write_plan(db_path: Path, plan: Dict[str, Any], *, inject_failure_after_ledger_rows: bool = False) -> Dict[str, Any]:
    conn = connect_rw(db_path)
    try:
        if conn.execute("SELECT 1 FROM news_disposition_batches_v2 WHERE batch_uid=?", (plan["batch_uid"],)).fetchone() is not None:
            return verify_existing_batch(conn, plan)
        counts = plan["counts"]
        now = utc_now()
        retention = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""
            INSERT INTO news_disposition_batches_v2(
                batch_uid, policy_version, queue_capacity,
                source_candidate_count, normalized_candidate_count,
                deduplicated_candidate_count, admitted_count,
                overflow_count, duplicate_removed_count,
                unsafe_filtered_count, invalid_candidate_count,
                replaced_count, lowest_admitted_priority,
                highest_overflow_priority, source_snapshot_hash,
                status, retention_class, retention_expires_at_utc,
                created_at_utc, committed_at_utc, incomplete_reason
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            plan["batch_uid"], plan["policy_version"], plan["queue_capacity"],
            counts["source_candidate_count"], counts["normalized_candidate_count"], counts["deduplicated_candidate_count"],
            counts["admitted_count"], counts["overflow_count"], counts["duplicate_removed_count"], counts["unsafe_filtered_count"],
            counts["invalid_candidate_count"], counts["replaced_count"], plan["lowest_admitted_priority"], plan["highest_overflow_priority"],
            plan["source_snapshot_hash"], "BUILDING", "STANDARD_30D", retention, now, None, None,
        ))
        for row in plan["ledger_rows"]:
            conn.execute("""
                INSERT INTO news_disposition_ledger_v2(
                    disposition_uid, batch_uid, source_index,
                    source_candidate_uid, hot_uid, event_uid, news_uid,
                    lane, priority_score, candidate_rank, disposition,
                    reason_code, lowest_admitted_priority,
                    highest_overflow_priority, source_snapshot_hash,
                    recorded_at_utc, payload_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                row["disposition_uid"], row["batch_uid"], row["source_index"], row["source_candidate_uid"], row["hot_uid"], row["event_uid"], row["news_uid"],
                row["lane"], row["priority_score"], row["candidate_rank"], row["disposition"], row["reason_code"], row["lowest_admitted_priority"],
                row["highest_overflow_priority"], row["source_snapshot_hash"], now, row["payload_json"],
            ))
        if inject_failure_after_ledger_rows:
            raise RuntimeError("INJECTED_FAILURE_AFTER_LEDGER_ROWS")
        cursor = conn.execute("UPDATE news_disposition_batches_v2 SET status='COMMITTED', committed_at_utc=? WHERE batch_uid=? AND status='BUILDING'", (utc_now(), plan["batch_uid"]))
        if cursor.rowcount != 1:
            raise RuntimeError("BATCH_COMMIT_UPDATE_FAILED")
        conn.commit()
        batch_sequence = int(conn.execute("SELECT rowid FROM news_disposition_batches_v2 WHERE batch_uid=?", (plan["batch_uid"],)).fetchone()[0])
        return {"status": "COMMITTED", "batch_uid": plan["batch_uid"], "batch_sequence": batch_sequence, "ledger_rows": counts["source_candidate_count"], "db_write_performed": True}
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def write_and_publish(*, display_path: Path, summary_path: Path, db_path: Path, output_path: Path, recovery_state_path: Path, contract_seed_path: Optional[Path], queue_capacity: int = DEFAULT_QUEUE_CAPACITY, lock_path: Optional[Path] = None, inject_failure_after_ledger_rows: bool = False) -> Dict[str, Any]:
    display = read_json(display_path)
    plan = build_plan(display, queue_capacity=queue_capacity)
    def execute() -> Dict[str, Any]:
        write_result = write_plan(db_path, plan, inject_failure_after_ledger_rows=inject_failure_after_ledger_rows)
        publish_result = recover_committed_batch(db_path, output_path, recovery_state_path, contract_seed_path=contract_seed_path, batch_sequence=int(write_result["batch_sequence"]))
        return {
            "status": "OK_LEDGER_BATCH_AND_OUTPUT_CONVERGED",
            "batch_uid": plan["batch_uid"],
            "batch_sequence": int(write_result["batch_sequence"]),
            "write_result": write_result,
            "publish_result": publish_result,
            "counts": plan["counts"],
            "hot_queue_count": len(plan["hot_queue"]),
            "source_snapshot_hash": plan["source_snapshot_hash"],
            "display_path": str(display_path),
            "summary_path": str(summary_path),
            "db_path": str(db_path),
            "output_path": str(output_path),
        }
    if lock_path is None:
        return execute()
    with single_instance_lock(lock_path) as lock_handle:
        if lock_handle is None:
            return {"status": "WRITER_ALREADY_ACTIVE", "db_write_performed": False, "output_path": str(output_path)}
        return execute()


def cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--display-path", required=True)
    parser.add_argument("--summary-path", required=True)
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--recovery-state-path", required=True)
    parser.add_argument("--contract-seed-path")
    parser.add_argument("--lock-path")
    parser.add_argument("--queue-capacity", type=int, default=DEFAULT_QUEUE_CAPACITY)
    args = parser.parse_args()
    result = write_and_publish(
        display_path=Path(args.display_path), summary_path=Path(args.summary_path), db_path=Path(args.db_path), output_path=Path(args.output_path),
        recovery_state_path=Path(args.recovery_state_path), contract_seed_path=Path(args.contract_seed_path) if args.contract_seed_path else None,
        queue_capacity=args.queue_capacity, lock_path=Path(args.lock_path) if args.lock_path else None,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
