#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
WORK_UNIT = "ERA55A_7_P0_DROP_LEDGER_DESIGN_AND_TEMP_COPY_TEST"
RESULT = "PASS_P0_LEDGER_DESIGN_TEMP_COPY_VALIDATED_NO_PRODUCTION_MUTATION"
A6_REL = "data/control/era55a6_gemini_red_team_review_and_findings_register_v1.json"
ARTIFACT_REL = "data/control/era55a7_p0_drop_ledger_design_and_temp_copy_test_v1.json"
SCHEMA_REL = "data/control/era55a7_p0_disposition_ledger_schema_v1.sql"
REPORT_REL = "reports/LATEST_ERA55A7_P0_DROP_LEDGER_DESIGN_AND_TEMP_COPY_TEST.md"
NEXT_SAFE_STEP = "ERA55A_8_P0_DROP_LEDGER_POST_TEST_AUDIT_AND_APPLY_DECISION"
PROD_DB_REL = "data/tokenoskobi_clean_v1.sqlite"
RUNTIME_GUARD_RELS = [
    "runtime/state/news_coverage_panel_display_v1.json",
    "runtime/state/hot_intelligence_ingress_gateway_v1.json",
    "runtime/state/news_active_panel_data_bridge_v1.json",
    "active_panel_8096/current/data/news_coverage_panel_display_v1.json",
    "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json",
]
UNIT_GUARDS = [
    Path("/etc/systemd/system/tokenoskobi-news-radar-refresh.service"),
    Path("/etc/systemd/system/tokenoskobi-news-radar-refresh.timer"),
]
CANONICAL = [
    "PROJECT_RUNTIME.json",
    "PROJECT_HISTORY.json",
    "data/tokenoskobi_v1_v8_master_era_roadmap.json",
    "04_ALMANAC.md",
    "06_PROJECT_MASTER_STATE.md",
    "07_PROJECT_HANDOFF.md",
]
GENERATED = [ARTIFACT_REL, SCHEMA_REL, REPORT_REL]
FORCE_ADD = {REPORT_REL}

SCHEMA_SQL = """PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS news_disposition_batches_v1 (
    batch_uid TEXT PRIMARY KEY,
    policy_version TEXT NOT NULL,
    queue_capacity INTEGER NOT NULL CHECK(queue_capacity > 0),
    source_candidate_count INTEGER NOT NULL CHECK(source_candidate_count >= 0),
    normalized_candidate_count INTEGER NOT NULL CHECK(normalized_candidate_count >= 0),
    deduplicated_candidate_count INTEGER NOT NULL CHECK(deduplicated_candidate_count >= 0),
    admitted_count INTEGER NOT NULL CHECK(admitted_count >= 0),
    overflow_count INTEGER NOT NULL CHECK(overflow_count >= 0),
    duplicate_removed_count INTEGER NOT NULL CHECK(duplicate_removed_count >= 0),
    unsafe_filtered_count INTEGER NOT NULL CHECK(unsafe_filtered_count >= 0),
    invalid_candidate_count INTEGER NOT NULL CHECK(invalid_candidate_count >= 0),
    lowest_admitted_priority INTEGER,
    highest_overflow_priority INTEGER,
    source_snapshot_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('BUILDING','COMMITTED','INCOMPLETE')),
    created_at_utc TEXT NOT NULL,
    committed_at_utc TEXT,
    incomplete_reason TEXT,
    CHECK(
        source_candidate_count = admitted_count + overflow_count
        + duplicate_removed_count + unsafe_filtered_count + invalid_candidate_count
    ),
    CHECK(deduplicated_candidate_count = admitted_count + overflow_count)
);

CREATE TABLE IF NOT EXISTS news_disposition_ledger_v1 (
    disposition_uid TEXT PRIMARY KEY,
    batch_uid TEXT NOT NULL,
    source_index INTEGER NOT NULL CHECK(source_index >= 0),
    source_candidate_uid TEXT NOT NULL,
    hot_uid TEXT,
    event_uid TEXT,
    news_uid TEXT,
    lane TEXT,
    priority_score INTEGER,
    candidate_rank INTEGER CHECK(candidate_rank IS NULL OR candidate_rank > 0),
    disposition TEXT NOT NULL CHECK(disposition IN (
        'ADMITTED',
        'DUPLICATE_REMOVED',
        'UNSAFE_AUTHORITY_FILTERED',
        'OVERFLOW_TRUNCATED',
        'REPLACED_BY_HIGHER_PRIORITY',
        'INVALID_CANDIDATE'
    )),
    reason_code TEXT NOT NULL CHECK(reason_code IN (
        'TOP_50_ADMITTED',
        'DUPLICATE_HOT_UID',
        'UNSAFE_AUTHORITY',
        'QUEUE_OVERFLOW',
        'HIGHER_PRIORITY_REPLACEMENT',
        'INVALID_INPUT'
    )),
    lowest_admitted_priority INTEGER,
    highest_overflow_priority INTEGER,
    source_snapshot_hash TEXT NOT NULL,
    recorded_at_utc TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY(batch_uid) REFERENCES news_disposition_batches_v1(batch_uid) ON DELETE RESTRICT,
    UNIQUE(batch_uid, source_index)
);

CREATE INDEX IF NOT EXISTS idx_news_disposition_ledger_batch_v1
ON news_disposition_ledger_v1(batch_uid, candidate_rank);

CREATE INDEX IF NOT EXISTS idx_news_disposition_ledger_hot_uid_v1
ON news_disposition_ledger_v1(hot_uid);

CREATE INDEX IF NOT EXISTS idx_news_disposition_ledger_disposition_v1
ON news_disposition_ledger_v1(disposition, reason_code);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if check and cp.returncode:
        raise RuntimeError(
            "COMMAND_FAILED="
            + json.dumps(
                {"cmd": cmd, "rc": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr},
                ensure_ascii=False,
            )
        )
    return cp


def git(*args: str) -> str:
    return run(["git", *args]).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED={path}")
    return value


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def write_json(path: Path, value: dict[str, Any]) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def replace_section(text: str, heading: str, body: str) -> str:
    match = re.search(rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)", text, re.S)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND={heading}")
    return text[: match.start()] + heading + "\n\n" + body.rstrip() + "\n" + text[match.end() :]


def require_preconditions() -> str:
    os.chdir(ROOT)
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BLOCKED=BRANCH_NOT_MAIN")
    if git("status", "--porcelain"):
        raise RuntimeError("BLOCKED=WORKTREE_NOT_CLEAN")
    runtime = load(ROOT / "PROJECT_RUNTIME.json")
    if runtime.get("current_era") != "ERA55":
        raise RuntimeError("BLOCKED=CURRENT_ERA_NOT_ERA55")
    if (runtime.get("era55_status") or {}).get("status") != "OPEN":
        raise RuntimeError("BLOCKED=ERA55_NOT_OPEN")
    if (runtime.get("next_safe_step") or {}).get("id") != WORK_UNIT:
        raise RuntimeError("BLOCKED=UNEXPECTED_NEXT_SAFE_STEP")
    a6 = load(ROOT / A6_REL)
    if a6.get("status") != "CLOSED_FINDINGS_REGISTERED":
        raise RuntimeError("BLOCKED=A6_STATUS_INVALID")
    if (a6.get("verdict") or {}).get("baseline_verdict") != "BASELINE_ACCEPTED":
        raise RuntimeError("BLOCKED=A6_BASELINE_NOT_ACCEPTED")
    if (a6.get("verdict") or {}).get("optimization_apply_verdict") != "REJECTED_UNTIL_P0_CLEARED":
        raise RuntimeError("BLOCKED=A6_OPTIMIZATION_GATE_INVALID")
    if (a6.get("verdict") or {}).get("a7_design_and_temp_copy_test_authorized") is not True:
        raise RuntimeError("BLOCKED=A7_NOT_AUTHORIZED")
    if not (ROOT / PROD_DB_REL).is_file():
        raise RuntimeError("BLOCKED=PRODUCTION_DB_MISSING")
    return git("rev-parse", "HEAD")


def guard_snapshot() -> dict[str, Any]:
    return {
        "production_db": {
            "path": PROD_DB_REL,
            "sha256": sha256_file(ROOT / PROD_DB_REL),
            "size_bytes": (ROOT / PROD_DB_REL).stat().st_size,
            "mtime_ns": (ROOT / PROD_DB_REL).stat().st_mtime_ns,
        },
        "runtime_files": {
            rel: {
                "exists": (ROOT / rel).is_file(),
                "sha256": sha256_file(ROOT / rel),
                "size_bytes": (ROOT / rel).stat().st_size if (ROOT / rel).is_file() else None,
                "mtime_ns": (ROOT / rel).stat().st_mtime_ns if (ROOT / rel).is_file() else None,
            }
            for rel in RUNTIME_GUARD_RELS
        },
        "systemd_units": {
            str(path): {
                "exists": path.is_file(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size if path.is_file() else None,
                "mtime_ns": path.stat().st_mtime_ns if path.is_file() else None,
            }
            for path in UNIT_GUARDS
        },
    }


def uid_for(item: dict[str, Any], lane: str) -> str:
    raw = "|".join(
        [
            lane,
            str(item.get("event_uid") or ""),
            str(item.get("news_uid") or ""),
            str(item.get("title") or ""),
        ]
    )
    return "hot_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def score_item(item: dict[str, Any], lane: str) -> int:
    hits = item.get("hits") if isinstance(item.get("hits"), list) else []
    score = len(hits) * 10
    if lane == "ADVERSARIAL_NEWS":
        score += 15
    if item.get("published_at_utc"):
        score += 5
    return score


def authority_safe(item: dict[str, Any]) -> bool:
    authority = item.get("authority") or {}
    return all(
        authority.get(key) is False
        for key in ("db_write", "hunter_authorized", "trade_signal", "paper_signal")
    )


def synthetic_candidates() -> list[Any]:
    safe_authority = {
        "db_write": False,
        "hunter_authorized": False,
        "trade_signal": False,
        "paper_signal": False,
    }
    candidates: list[Any] = []
    for index in range(60):
        lane = "ADVERSARIAL_NEWS" if index % 3 == 0 else "MARKET_INDICATOR"
        candidates.append(
            {
                "source_candidate_uid": f"src_unique_{index:03d}",
                "lane": lane,
                "event_uid": f"event_{index:03d}",
                "news_uid": f"news_{index:03d}",
                "title": f"Synthetic Event {index:03d}",
                "hits": [f"hit_{n}" for n in range(index % 6)],
                "published_at_utc": "2026-07-11T00:00:00+00:00",
                "authority": dict(safe_authority),
            }
        )
    for index in range(5):
        duplicate = dict(candidates[index])
        duplicate["source_candidate_uid"] = f"src_duplicate_{index:03d}"
        duplicate["authority"] = dict(safe_authority)
        candidates.append(duplicate)
    for index in range(3):
        candidates.append(
            {
                "source_candidate_uid": f"src_unsafe_{index:03d}",
                "lane": "ADVERSARIAL_NEWS",
                "event_uid": f"unsafe_event_{index:03d}",
                "news_uid": f"unsafe_news_{index:03d}",
                "title": f"Unsafe Event {index:03d}",
                "hits": ["unsafe"],
                "published_at_utc": "2026-07-11T00:00:00+00:00",
                "authority": {
                    "db_write": True,
                    "hunter_authorized": False,
                    "trade_signal": False,
                    "paper_signal": False,
                },
            }
        )
    candidates.extend([None, "invalid_candidate"])
    if len(candidates) != 70:
        raise RuntimeError("SYNTHETIC_COUNT_INVALID")
    return candidates


def snapshot_hash(candidates: list[Any]) -> str:
    encoded = json.dumps(candidates, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_dispositions(candidates: list[Any], capacity: int = 50) -> dict[str, Any]:
    source_hash = snapshot_hash(candidates)
    immediate: dict[int, dict[str, Any]] = {}
    normalized: list[dict[str, Any]] = []

    for source_index, raw in enumerate(candidates):
        source_uid = (
            str(raw.get("source_candidate_uid") or f"source_{source_index}")
            if isinstance(raw, dict)
            else f"invalid_{source_index}"
        )
        if not isinstance(raw, dict):
            immediate[source_index] = {
                "source_index": source_index,
                "source_candidate_uid": source_uid,
                "hot_uid": None,
                "event_uid": None,
                "news_uid": None,
                "lane": None,
                "priority_score": None,
                "candidate_rank": None,
                "disposition": "INVALID_CANDIDATE",
                "reason_code": "INVALID_INPUT",
                "payload": raw,
            }
            continue
        lane = str(raw.get("lane") or "")
        if lane not in ("MARKET_INDICATOR", "ADVERSARIAL_NEWS"):
            immediate[source_index] = {
                "source_index": source_index,
                "source_candidate_uid": source_uid,
                "hot_uid": None,
                "event_uid": raw.get("event_uid"),
                "news_uid": raw.get("news_uid"),
                "lane": lane or None,
                "priority_score": None,
                "candidate_rank": None,
                "disposition": "INVALID_CANDIDATE",
                "reason_code": "INVALID_INPUT",
                "payload": raw,
            }
            continue
        hot_uid = uid_for(raw, lane)
        priority = score_item(raw, lane)
        if not authority_safe(raw):
            immediate[source_index] = {
                "source_index": source_index,
                "source_candidate_uid": source_uid,
                "hot_uid": hot_uid,
                "event_uid": raw.get("event_uid"),
                "news_uid": raw.get("news_uid"),
                "lane": lane,
                "priority_score": priority,
                "candidate_rank": None,
                "disposition": "UNSAFE_AUTHORITY_FILTERED",
                "reason_code": "UNSAFE_AUTHORITY",
                "payload": raw,
            }
            continue
        normalized.append(
            {
                "source_index": source_index,
                "source_candidate_uid": source_uid,
                "hot_uid": hot_uid,
                "event_uid": raw.get("event_uid"),
                "news_uid": raw.get("news_uid"),
                "lane": lane,
                "priority_score": priority,
                "payload": raw,
            }
        )

    sorted_items = sorted(
        normalized,
        key=lambda item: (-int(item["priority_score"]), str(item["hot_uid"])),
    )
    first_by_uid: dict[str, dict[str, Any]] = {}
    duplicate_rows: list[dict[str, Any]] = []
    for item in sorted_items:
        hot_uid = str(item["hot_uid"])
        if hot_uid in first_by_uid:
            duplicate_rows.append(item)
        else:
            first_by_uid[hot_uid] = item
    deduped = list(first_by_uid.values())
    admitted = deduped[:capacity]
    overflow = deduped[capacity:]
    rank_by_uid = {str(item["hot_uid"]): rank for rank, item in enumerate(deduped, start=1)}
    admitted_uids = {str(item["hot_uid"]) for item in admitted}
    overflow_uids = {str(item["hot_uid"]) for item in overflow}
    duplicate_indices = {int(item["source_index"]) for item in duplicate_rows}
    lowest_admitted = min((int(item["priority_score"]) for item in admitted), default=None)
    highest_overflow = max((int(item["priority_score"]) for item in overflow), default=None)

    dispositions: list[dict[str, Any]] = []
    for source_index in range(len(candidates)):
        if source_index in immediate:
            row = dict(immediate[source_index])
        else:
            item = next(x for x in normalized if int(x["source_index"]) == source_index)
            hot_uid = str(item["hot_uid"])
            row = dict(item)
            if source_index in duplicate_indices:
                row.update(
                    {
                        "candidate_rank": rank_by_uid[hot_uid],
                        "disposition": "DUPLICATE_REMOVED",
                        "reason_code": "DUPLICATE_HOT_UID",
                    }
                )
            elif hot_uid in admitted_uids:
                row.update(
                    {
                        "candidate_rank": rank_by_uid[hot_uid],
                        "disposition": "ADMITTED",
                        "reason_code": "TOP_50_ADMITTED",
                    }
                )
            elif hot_uid in overflow_uids:
                row.update(
                    {
                        "candidate_rank": rank_by_uid[hot_uid],
                        "disposition": "OVERFLOW_TRUNCATED",
                        "reason_code": "QUEUE_OVERFLOW",
                    }
                )
            else:
                raise RuntimeError("UNCLASSIFIED_NORMALIZED_CANDIDATE")
        row["lowest_admitted_priority"] = lowest_admitted
        row["highest_overflow_priority"] = highest_overflow
        row["source_snapshot_hash"] = source_hash
        row["disposition_uid"] = "disp_" + hashlib.sha256(
            f"{source_hash}|{source_index}|{row['disposition']}".encode("utf-8")
        ).hexdigest()[:28]
        dispositions.append(row)

    counts: dict[str, int] = {}
    for row in dispositions:
        counts[row["disposition"]] = counts.get(row["disposition"], 0) + 1
    return {
        "source_snapshot_hash": source_hash,
        "source_count": len(candidates),
        "normalized_count": len(normalized),
        "deduplicated_count": len(deduped),
        "admitted_count": len(admitted),
        "overflow_count": len(overflow),
        "duplicate_removed_count": counts.get("DUPLICATE_REMOVED", 0),
        "unsafe_filtered_count": counts.get("UNSAFE_AUTHORITY_FILTERED", 0),
        "invalid_candidate_count": counts.get("INVALID_CANDIDATE", 0),
        "lowest_admitted_priority": lowest_admitted,
        "highest_overflow_priority": highest_overflow,
        "disposition_counts": counts,
        "dispositions": dispositions,
        "unique_valid_hot_uids": sorted(set(str(item["hot_uid"]) for item in normalized)),
        "admitted_hot_uids": sorted(admitted_uids),
        "overflow_hot_uids": sorted(overflow_uids),
    }


def quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def existing_table_snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
    excluded = {"news_disposition_batches_v1", "news_disposition_ledger_v1"}
    tables = [
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        if str(row[0]) not in excluded
    ]
    result: dict[str, Any] = {}
    uid_candidates = ("event_uid", "news_uid", "signal_uid", "score_uid", "hot_uid", "uid")
    for table in tables:
        qtable = quote_ident(table)
        count = int(connection.execute(f"SELECT COUNT(*) FROM {qtable}").fetchone()[0])
        columns = [str(row[1]) for row in connection.execute(f"PRAGMA table_info({qtable})").fetchall()]
        uid_hashes: dict[str, str] = {}
        for column in uid_candidates:
            if column not in columns:
                continue
            qcol = quote_ident(column)
            digest = hashlib.sha256()
            cursor = connection.execute(
                f"SELECT CAST({qcol} AS TEXT) FROM {qtable} WHERE {qcol} IS NOT NULL ORDER BY CAST({qcol} AS TEXT)"
            )
            for row in cursor:
                digest.update(str(row[0]).encode("utf-8"))
                digest.update(b"\n")
            uid_hashes[column] = digest.hexdigest()
        result[table] = {"row_count": count, "uid_hashes": uid_hashes}
    return result


def backup_production(temp_db: Path) -> None:
    source = sqlite3.connect(f"file:{ROOT / PROD_DB_REL}?mode=ro", uri=True, timeout=30)
    destination = sqlite3.connect(temp_db, timeout=30)
    try:
        source.execute("PRAGMA query_only=ON")
        source.backup(destination)
        destination.commit()
    finally:
        destination.close()
        source.close()


def insert_main_batch(connection: sqlite3.Connection, model: dict[str, Any], batch_uid: str, ts: str) -> None:
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            """INSERT INTO news_disposition_batches_v1 (
                batch_uid, policy_version, queue_capacity,
                source_candidate_count, normalized_candidate_count,
                deduplicated_candidate_count, admitted_count, overflow_count,
                duplicate_removed_count, unsafe_filtered_count, invalid_candidate_count,
                lowest_admitted_priority, highest_overflow_priority,
                source_snapshot_hash, status, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'BUILDING', ?)""",
            (
                batch_uid,
                "PRIORITY_DESC_THEN_HOT_UID_TOP_50_V1",
                50,
                model["source_count"],
                model["normalized_count"],
                model["deduplicated_count"],
                model["admitted_count"],
                model["overflow_count"],
                model["duplicate_removed_count"],
                model["unsafe_filtered_count"],
                model["invalid_candidate_count"],
                model["lowest_admitted_priority"],
                model["highest_overflow_priority"],
                model["source_snapshot_hash"],
                ts,
            ),
        )
        for row in model["dispositions"]:
            connection.execute(
                """INSERT INTO news_disposition_ledger_v1 (
                    disposition_uid, batch_uid, source_index, source_candidate_uid,
                    hot_uid, event_uid, news_uid, lane, priority_score, candidate_rank,
                    disposition, reason_code, lowest_admitted_priority,
                    highest_overflow_priority, source_snapshot_hash, recorded_at_utc,
                    payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["disposition_uid"],
                    batch_uid,
                    row["source_index"],
                    row["source_candidate_uid"],
                    row.get("hot_uid"),
                    row.get("event_uid"),
                    row.get("news_uid"),
                    row.get("lane"),
                    row.get("priority_score"),
                    row.get("candidate_rank"),
                    row["disposition"],
                    row["reason_code"],
                    row.get("lowest_admitted_priority"),
                    row.get("highest_overflow_priority"),
                    row["source_snapshot_hash"],
                    ts,
                    json.dumps(row.get("payload"), ensure_ascii=False, sort_keys=True),
                ),
            )
        connection.execute(
            "UPDATE news_disposition_batches_v1 SET status='COMMITTED', committed_at_utc=? WHERE batch_uid=?",
            (now(), batch_uid),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def atomic_rollback_test(connection: sqlite3.Connection, model: dict[str, Any]) -> dict[str, Any]:
    rollback_batch = "batch_atomic_rollback_test"
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            """INSERT INTO news_disposition_batches_v1 (
                batch_uid, policy_version, queue_capacity,
                source_candidate_count, normalized_candidate_count,
                deduplicated_candidate_count, admitted_count, overflow_count,
                duplicate_removed_count, unsafe_filtered_count, invalid_candidate_count,
                lowest_admitted_priority, highest_overflow_priority,
                source_snapshot_hash, status, created_at_utc
            ) VALUES (?, ?, 50, 10, 10, 10, 10, 0, 0, 0, 0, ?, NULL, ?, 'BUILDING', ?)""",
            (
                rollback_batch,
                "ROLLBACK_TEST_V1",
                model["lowest_admitted_priority"],
                model["source_snapshot_hash"],
                now(),
            ),
        )
        for index, source in enumerate(model["dispositions"][:10]):
            connection.execute(
                """INSERT INTO news_disposition_ledger_v1 (
                    disposition_uid, batch_uid, source_index, source_candidate_uid,
                    hot_uid, event_uid, news_uid, lane, priority_score, candidate_rank,
                    disposition, reason_code, lowest_admitted_priority,
                    highest_overflow_priority, source_snapshot_hash, recorded_at_utc,
                    payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ADMITTED', 'TOP_50_ADMITTED', ?, NULL, ?, ?, '{}')""",
                (
                    f"rollback_disp_{index}",
                    rollback_batch,
                    index,
                    f"rollback_source_{index}",
                    source.get("hot_uid"),
                    source.get("event_uid"),
                    source.get("news_uid"),
                    source.get("lane"),
                    source.get("priority_score"),
                    index + 1,
                    model["lowest_admitted_priority"],
                    model["source_snapshot_hash"],
                    now(),
                ),
            )
        raise RuntimeError("INTENTIONAL_ROLLBACK")
    except RuntimeError as exc:
        if str(exc) != "INTENTIONAL_ROLLBACK":
            connection.rollback()
            raise
        connection.rollback()
    batch_rows = int(
        connection.execute("SELECT COUNT(*) FROM news_disposition_batches_v1 WHERE batch_uid=?", (rollback_batch,)).fetchone()[0]
    )
    ledger_rows = int(
        connection.execute("SELECT COUNT(*) FROM news_disposition_ledger_v1 WHERE batch_uid=?", (rollback_batch,)).fetchone()[0]
    )
    return {
        "batch_rows_after_rollback": batch_rows,
        "ledger_rows_after_rollback": ledger_rows,
        "pass": batch_rows == 0 and ledger_rows == 0,
    }


def constraint_tests(connection: sqlite3.Connection, main_batch: str, model: dict[str, Any]) -> dict[str, Any]:
    duplicate_rejected = False
    foreign_key_rejected = False
    existing = connection.execute(
        "SELECT * FROM news_disposition_ledger_v1 WHERE batch_uid=? ORDER BY source_index LIMIT 1",
        (main_batch,),
    ).fetchone()
    if existing is None:
        raise RuntimeError("NO_LEDGER_ROW_FOR_CONSTRAINT_TEST")
    try:
        connection.execute("BEGIN")
        connection.execute(
            "INSERT INTO news_disposition_ledger_v1 SELECT * FROM news_disposition_ledger_v1 WHERE disposition_uid=?",
            (existing[0],),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        duplicate_rejected = True
        connection.rollback()
    try:
        connection.execute("BEGIN")
        connection.execute(
            """INSERT INTO news_disposition_ledger_v1 (
                disposition_uid, batch_uid, source_index, source_candidate_uid,
                disposition, reason_code, source_snapshot_hash, recorded_at_utc, payload_json
            ) VALUES ('fk_test_disp', 'missing_batch', 999, 'fk_test_source',
                'INVALID_CANDIDATE', 'INVALID_INPUT', ?, ?, '{}')""",
            (model["source_snapshot_hash"], now()),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        foreign_key_rejected = True
        connection.rollback()
    return {
        "duplicate_disposition_uid_rejected": duplicate_rejected,
        "missing_batch_foreign_key_rejected": foreign_key_rejected,
        "pass": duplicate_rejected and foreign_key_rejected,
    }


def run_temp_copy_test(temp_dir: Path) -> dict[str, Any]:
    temp_db = temp_dir / "tokenoskobi_temp_copy.sqlite"
    backup_production(temp_db)
    connection = sqlite3.connect(temp_db, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        integrity_before = connection.execute("PRAGMA integrity_check").fetchone()[0]
        quick_before = connection.execute("PRAGMA quick_check").fetchone()[0]
        original_snapshot = existing_table_snapshot(connection)
        connection.executescript(SCHEMA_SQL)
        connection.commit()

        candidates = synthetic_candidates()
        model = build_dispositions(candidates, capacity=50)
        if model["admitted_count"] != 50 or model["overflow_count"] != 10:
            raise RuntimeError("OVERFLOW_MODEL_COUNTS_INVALID")
        if model["duplicate_removed_count"] != 5:
            raise RuntimeError("DUPLICATE_MODEL_COUNT_INVALID")
        if model["unsafe_filtered_count"] != 3:
            raise RuntimeError("UNSAFE_MODEL_COUNT_INVALID")
        if model["invalid_candidate_count"] != 2:
            raise RuntimeError("INVALID_MODEL_COUNT_INVALID")

        batch_uid = "batch_" + model["source_snapshot_hash"][:24]
        insert_main_batch(connection, model, batch_uid, now())
        rollback_result = atomic_rollback_test(connection, model)
        constraint_result = constraint_tests(connection, batch_uid, model)

        ledger_count = int(
            connection.execute("SELECT COUNT(*) FROM news_disposition_ledger_v1 WHERE batch_uid=?", (batch_uid,)).fetchone()[0]
        )
        disposition_counts = {
            str(row[0]): int(row[1])
            for row in connection.execute(
                "SELECT disposition, COUNT(*) FROM news_disposition_ledger_v1 WHERE batch_uid=? GROUP BY disposition ORDER BY disposition",
                (batch_uid,),
            ).fetchall()
        }
        overflow_wrong_reason = int(
            connection.execute(
                "SELECT COUNT(*) FROM news_disposition_ledger_v1 WHERE batch_uid=? AND disposition='OVERFLOW_TRUNCATED' AND reason_code<>'QUEUE_OVERFLOW'",
                (batch_uid,),
            ).fetchone()[0]
        )
        source_index_distinct = int(
            connection.execute(
                "SELECT COUNT(DISTINCT source_index) FROM news_disposition_ledger_v1 WHERE batch_uid=?",
                (batch_uid,),
            ).fetchone()[0]
        )
        admitted_overflow_uids = {
            str(row[0])
            for row in connection.execute(
                "SELECT hot_uid FROM news_disposition_ledger_v1 WHERE batch_uid=? AND disposition IN ('ADMITTED','OVERFLOW_TRUNCATED')",
                (batch_uid,),
            ).fetchall()
        }
        expected_unique_uids = set(model["unique_valid_hot_uids"])
        uid_loss_set = sorted(expected_unique_uids - admitted_overflow_uids)
        duplicate_canonical_uids = int(
            connection.execute(
                """SELECT COUNT(*) FROM (
                    SELECT hot_uid FROM news_disposition_ledger_v1
                    WHERE batch_uid=? AND disposition IN ('ADMITTED','OVERFLOW_TRUNCATED')
                    GROUP BY hot_uid HAVING COUNT(*) > 1
                )""",
                (batch_uid,),
            ).fetchone()[0]
        )
        unledgered_disposition = model["source_count"] - ledger_count
        event_count_loss = model["source_count"] - ledger_count
        uid_loss = len(uid_loss_set)

        foreign_key_check = connection.execute("PRAGMA foreign_key_check").fetchall()
        integrity_after = connection.execute("PRAGMA integrity_check").fetchone()[0]
        quick_after = connection.execute("PRAGMA quick_check").fetchone()[0]
        final_snapshot = existing_table_snapshot(connection)
        source_tables_unchanged = original_snapshot == final_snapshot

        batch = dict(
            connection.execute(
                "SELECT * FROM news_disposition_batches_v1 WHERE batch_uid=?",
                (batch_uid,),
            ).fetchone()
        )

        gates = {
            "event_count_loss": event_count_loss,
            "uid_loss": uid_loss,
            "duplicate_regression": duplicate_canonical_uids,
            "unledgered_disposition": unledgered_disposition,
            "overflow_wrong_reason_count": overflow_wrong_reason,
            "source_index_distinct": source_index_distinct,
            "ledger_count": ledger_count,
            "expected_source_count": model["source_count"],
            "integrity_check": integrity_after,
            "quick_check": quick_after,
            "foreign_key_check_rows": len(foreign_key_check),
            "source_tables_unchanged": source_tables_unchanged,
            "atomic_rollback_pass": rollback_result["pass"],
            "constraint_tests_pass": constraint_result["pass"],
        }
        passed = (
            integrity_before == "ok"
            and quick_before == "ok"
            and event_count_loss == 0
            and uid_loss == 0
            and duplicate_canonical_uids == 0
            and unledgered_disposition == 0
            and overflow_wrong_reason == 0
            and source_index_distinct == model["source_count"]
            and ledger_count == model["source_count"]
            and integrity_after == "ok"
            and quick_after == "ok"
            and not foreign_key_check
            and source_tables_unchanged
            and rollback_result["pass"]
            and constraint_result["pass"]
            and disposition_counts == {
                "ADMITTED": 50,
                "DUPLICATE_REMOVED": 5,
                "INVALID_CANDIDATE": 2,
                "OVERFLOW_TRUNCATED": 10,
                "UNSAFE_AUTHORITY_FILTERED": 3,
            }
        )
        return {
            "pass": passed,
            "temp_db_path": str(temp_db),
            "temp_db_sha256": sha256_file(temp_db),
            "integrity_before": integrity_before,
            "quick_before": quick_before,
            "integrity_after": integrity_after,
            "quick_after": quick_after,
            "main_batch": batch,
            "model": {
                key: value
                for key, value in model.items()
                if key not in ("dispositions", "unique_valid_hot_uids", "admitted_hot_uids", "overflow_hot_uids")
            },
            "disposition_counts": disposition_counts,
            "overflow_event_uids": [
                row["hot_uid"]
                for row in model["dispositions"]
                if row["disposition"] == "OVERFLOW_TRUNCATED"
            ],
            "uid_loss_set": uid_loss_set,
            "atomic_rollback": rollback_result,
            "constraint_tests": constraint_result,
            "gates": gates,
            "existing_source_table_snapshot_before": original_snapshot,
            "existing_source_table_snapshot_after": final_snapshot,
        }
    finally:
        connection.close()


def build_artifact(ts: str, head: str, before: dict[str, Any], after: dict[str, Any], test: dict[str, Any], temp_dir: Path) -> dict[str, Any]:
    production_unchanged = before == after
    if not test["pass"]:
        raise RuntimeError("TEMP_COPY_LEDGER_TEST_FAILED")
    if not production_unchanged:
        raise RuntimeError("PRODUCTION_GUARD_CHANGED")
    schema_hash = hashlib.sha256(SCHEMA_SQL.encode("utf-8")).hexdigest()
    return {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "era": "ERA55",
        "tested_at_utc": ts,
        "status": "CLOSED_TEMP_COPY_TEST_PASS",
        "result": RESULT,
        "head_before_commit": head,
        "source_review": A6_REL,
        "design": {
            "schema_file": SCHEMA_REL,
            "schema_sha256": schema_hash,
            "batch_table": "news_disposition_batches_v1",
            "ledger_table": "news_disposition_ledger_v1",
            "policy_version": "PRIORITY_DESC_THEN_HOT_UID_TOP_50_V1",
            "atomicity": "SINGLE_TRANSACTION_FAIL_CLOSED",
            "production_apply_authorized": False,
        },
        "test_environment": {
            "mode": "DISPOSABLE_TEMP_COPY",
            "temp_dir": str(temp_dir),
            "production_db_open_mode": "READ_ONLY_BACKUP_SOURCE",
            "production_burst": False,
            "production_service_kill": False,
            "production_service_timer_change": False,
        },
        "test_result": test,
        "production_guard_before": before,
        "production_guard_after": after,
        "production_unchanged": production_unchanged,
        "hard_gates": {
            "event_count_loss": test["gates"]["event_count_loss"],
            "uid_loss": test["gates"]["uid_loss"],
            "duplicate_regression": test["gates"]["duplicate_regression"],
            "unledgered_disposition": test["gates"]["unledgered_disposition"],
            "overflow_wrong_reason_count": test["gates"]["overflow_wrong_reason_count"],
            "integrity_check": test["gates"]["integrity_check"],
            "quick_check": test["gates"]["quick_check"],
            "atomic_rollback_pass": test["gates"]["atomic_rollback_pass"],
            "constraint_tests_pass": test["gates"]["constraint_tests_pass"],
            "production_unchanged": production_unchanged,
        },
        "decision": {
            "p0_ledger_schema_design_validated": True,
            "temp_copy_overflow_accounting_validated": True,
            "production_implementation_authorized": False,
            "p0_f1_closed": False,
            "p0_f1_status": "OPEN_PENDING_PRODUCTION_DESIGN_AUDIT_AND_APPLY_DECISION",
            "optimization_apply_authorized": False,
        },
        "next_safe_step": NEXT_SAFE_STEP,
        "mutation_statement": {
            "production_database": False,
            "live_runtime": False,
            "service": False,
            "timer": False,
            "panel": False,
            "queue_policy": False,
        },
    }


def make_report(artifact: dict[str, Any]) -> str:
    test = artifact["test_result"]
    gates = artifact["hard_gates"]
    return f"""# ERA55A_7 P0 DROP LEDGER DESIGN AND TEMP-COPY TEST

Result: `{RESULT}`

Test mode: `DISPOSABLE_TEMP_COPY`

Production mutation: `false`

## Schema

- Batch table: `news_disposition_batches_v1`
- Ledger table: `news_disposition_ledger_v1`
- Atomicity: `SINGLE_TRANSACTION_FAIL_CLOSED`
- Schema artifact: `{SCHEMA_REL}`

## Overflow Simulation

- Source candidates: `{test['model']['source_count']}`
- Normalized candidates: `{test['model']['normalized_count']}`
- Deduplicated candidates: `{test['model']['deduplicated_count']}`
- Admitted: `{test['model']['admitted_count']}`
- Overflow: `{test['model']['overflow_count']}`
- Duplicate removed: `{test['model']['duplicate_removed_count']}`
- Unsafe filtered: `{test['model']['unsafe_filtered_count']}`
- Invalid candidates: `{test['model']['invalid_candidate_count']}`

```json
{json.dumps(test['disposition_counts'], ensure_ascii=False, indent=2)}
```

Every overflow event was written with `reason_code=QUEUE_OVERFLOW`.

## Hard Gates

```json
{json.dumps(gates, ensure_ascii=False, indent=2)}
```

## Atomicity and Constraints

```json
{json.dumps({'atomic_rollback': test['atomic_rollback'], 'constraint_tests': test['constraint_tests']}, ensure_ascii=False, indent=2)}
```

## Production Guard

Production DB, runtime-state files and systemd unit hashes were identical before and after the test.

## Decision

- Ledger schema design: `VALIDATED_ON_TEMP_COPY`
- Overflow accounting: `VALIDATED_ON_TEMP_COPY`
- Production implementation: `NOT_AUTHORIZED`
- F1 P0: `OPEN_PENDING_POST_TEST_AUDIT_AND_APPLY_DECISION`
- Optimization apply: `false`
- Next: `{NEXT_SAFE_STEP}`
"""


def update_runtime(ts: str) -> None:
    path = ROOT / "PROJECT_RUNTIME.json"
    data = load(path)
    work = {
        "id": WORK_UNIT,
        "type": "ERA55_P0_DROP_LEDGER_DESIGN_TEMP_COPY_TEST",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "artifact": ARTIFACT_REL,
        "report": REPORT_REL,
        "schema": SCHEMA_REL,
        "status": "CLOSED_TEMP_COPY_TEST_PASS",
        "result": RESULT,
        "runtime_db_service_timer_panel_mutation": False,
        "next_step": NEXT_SAFE_STEP,
    }
    next_step = {
        "id": NEXT_SAFE_STEP,
        "type": "ERA55_P0_DROP_LEDGER_POST_TEST_AUDIT_APPLY_DECISION",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "purpose": "Audit the validated temp-copy design and produce a production apply or reject plan without changing live runtime.",
        "human_authorization_required": True,
        "production_mutation_authorized": False,
        "optimization_apply_authorized": False,
        "status": "READY",
    }
    action = {"timestamp": ts, "task": WORK_UNIT, "result": RESULT, "artifact": ARTIFACT_REL}
    data.update(
        {
            "mode": "ERA55A7_P0_LEDGER_TEMP_COPY_TEST_PASS",
            "project_status": "ACTIVE_ERA55_P0_LEDGER_POST_TEST_AUDIT_REQUIRED",
            "status": "WORK_UNIT_CLOSED",
            "last_completed": WORK_UNIT,
            "last_action": action,
            "recent_event": dict(action),
            "current_work_unit": work,
            "next_safe_step": next_step,
            "source": "era55a7_p0_drop_ledger_temp_copy_test_v1",
            "updated_at": ts,
            "updated_at_utc": ts,
        }
    )
    state = data.setdefault("current_state", {})
    state.update(
        {
            "mode": data["mode"],
            "runtime_status": "WORK_UNIT_CLOSED",
            "project_status": "ACTIVE",
            "updated_at": ts,
            "last_action": dict(action),
            "active_work_unit": dict(work),
            "next_safe_step": dict(next_step),
            "current_problem": None,
        }
    )
    era = data.setdefault("era55_status", {})
    era.update(
        {
            "status": "OPEN",
            "active_stage": "ERA55A_P0_DROP_LEDGER",
            "last_completed_substep": WORK_UNIT,
            "next_safe_step": NEXT_SAFE_STEP,
            "a7_artifact": ARTIFACT_REL,
            "a7_report": REPORT_REL,
            "a7_schema": SCHEMA_REL,
            "p0_ledger_schema_temp_copy_validated": True,
            "p0_f1_status": "OPEN_PENDING_POST_TEST_AUDIT_AND_APPLY_DECISION",
            "production_ledger_apply_authorized": False,
            "optimization_apply_authorized": False,
            "runtime_db_service_timer_panel_mutation": False,
        }
    )
    data["open_risks"] = [
        "P0:F1_PRODUCTION_DISPOSITION_LEDGER_NOT_APPLIED:OPEN",
        "P1:F2_DELETE_VS_WAL_HYPOTHESIS:OPEN",
        "P1:F3_ATOMIC_KILL_RECOVERY:UNTESTED",
        "P2:F4_STAGE_TIMING_AND_PANEL_LATENCY:MISSING",
        "Risk is minimized, never zero.",
    ]
    write_json(path, data)


def update_roadmap(ts: str) -> None:
    path = ROOT / "data/tokenoskobi_v1_v8_master_era_roadmap.json"
    data = load(path)
    found = False
    for version in data.get("versions", []):
        if version.get("id") != "V3":
            continue
        for child in version.get("children", []):
            if child.get("id") == "ERA55":
                child.update(
                    {
                        "status": "OPEN",
                        "active_stage": "ERA55A_P0_DROP_LEDGER",
                        "last_completed_substep": WORK_UNIT,
                        "last_result": RESULT,
                        "next_safe_step": NEXT_SAFE_STEP,
                        "a7_artifact": ARTIFACT_REL,
                        "a7_schema": SCHEMA_REL,
                        "p0_ledger_schema_temp_copy_validated": True,
                        "p0_f1_status": "OPEN_PENDING_POST_TEST_AUDIT_AND_APPLY_DECISION",
                        "production_ledger_apply_authorized": False,
                        "optimization_apply_authorized": False,
                    }
                )
                found = True
    if not found:
        raise RuntimeError("ERA55_NOT_FOUND_IN_ROADMAP_JSON")
    data.update({"updated_at": ts, "git_head": "DYNAMIC_USE_GIT_REV_PARSE_HEAD", "work_unit": WORK_UNIT})
    write_json(path, data)


def update_docs(artifact: dict[str, Any]) -> None:
    master = ROOT / "06_PROJECT_MASTER_STATE.md"
    text = master.read_text(encoding="utf-8").replace(
        "PROJECT_STATUS=ACTIVE_ERA55_P0_DROP_LEDGER_TEMP_COPY_AUTHORIZED",
        "PROJECT_STATUS=ACTIVE_ERA55_P0_LEDGER_POST_TEST_AUDIT_REQUIRED",
        1,
    )
    text = replace_section(
        text,
        "## 02 CURRENT MAJOR-LINE POSITION",
        """```text
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_DROP_LEDGER
LAST_COMPLETED_SUBSTEP=ERA55A_7_P0_DROP_LEDGER_DESIGN_AND_TEMP_COPY_TEST
P0_LEDGER_SCHEMA_TEMP_COPY_VALIDATED=true
P0_F1_STATUS=OPEN_PENDING_POST_TEST_AUDIT_AND_APPLY_DECISION
PRODUCTION_LEDGER_APPLY_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
```

A7 validated the ledger schema and deterministic overflow accounting on a disposable copy. Production remains unchanged.""",
    )
    text = replace_section(
        text,
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
LAST_SCHEMA={SCHEMA_REL}
WORK_UNIT_STATUS=CLOSED_TEMP_COPY_TEST_PASS
LIVE_RUNTIME_MUTATION=false
```

All temp-copy correctness gates passed, including atomic rollback and zero unledgered disposition.""",
    )
    text = replace_section(
        text,
        "## 09 OPEN RISKS AND DECISIONS",
        """- P0 ledger design passed temp-copy tests but is not applied to production; F1 remains open.
- A8 post-test audit must decide production apply or reject scope.
- F2 DELETE-vs-WAL remains untested.
- F3 kill recovery remains untested.
- F4 stage timing and panel latency remain incomplete.
- Production DB, service, timer, panel and queue policy remain unchanged.
- Runtime risk is minimized, never zero.
- Git HEAD must be read dynamically.""",
    )
    text = replace_section(
        text,
        "## 10 NEXT SAFE STEP",
        f"""```text
NEXT_SAFE_STEP={NEXT_SAFE_STEP}
```

Audit the A7 schema and test evidence, define rollback and migration controls, then issue a production apply or reject decision. Do not apply yet.""",
    )
    write_text(master, text)

    handoff = ROOT / "07_PROJECT_HANDOFF.md"
    text = handoff.read_text(encoding="utf-8")
    text = replace_section(
        text,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        """PROJECT_STATUS=ACTIVE_ERA55_P0_LEDGER_POST_TEST_AUDIT_REQUIRED
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_DROP_LEDGER
LAST_COMPLETED_SUBSTEP=ERA55A_7_P0_DROP_LEDGER_DESIGN_AND_TEMP_COPY_TEST
P0_LEDGER_SCHEMA_TEMP_COPY_VALIDATED=true
P0_F1_STATUS=OPEN_PENDING_POST_TEST_AUDIT_AND_APPLY_DECISION
PRODUCTION_LEDGER_APPLY_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A7 is closed with temp-copy PASS. A8 audit is the only authorized next work.""",
    )
    text = replace_section(
        text,
        "## 03 LAST VERIFIED WORK",
        f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
LAST_SCHEMA={SCHEMA_REL}
WORK_UNIT_STATUS=CLOSED_TEMP_COPY_TEST_PASS
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=null""",
    )
    text = replace_section(
        text,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not reopen ERA54.
- Do not rerun A7 unless evidence is invalidated.
- Do not apply the ledger schema to production before A8 audit and explicit approval.
- Do not modify the live gateway, queue policy, service, timer or panel.
- Do not run production burst, kill, restart or WAL tests.
- Do not mark F1 closed based only on temp-copy success.""",
    )
    text = replace_section(
        text,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- A7 temp-copy design/test verdict: `PASS`.
- Production ledger apply: `NOT_AUTHORIZED`.
- F1 remains open until an audited production implementation is verified.
- A8 may prepare apply/reject decision and rollback controls only.

NEXT_SAFE_STEP={NEXT_SAFE_STEP}""",
    )
    text = replace_section(
        text,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A8 is current.
2. Read A6 and A7 artifacts and the SQL schema.
3. Audit schema compatibility, migration idempotency, retention and failure behavior.
4. Define production backup, rollback, shadow observation and post-apply gates.
5. Decide apply or reject; do not mutate production in A8.
6. Preserve event-count, UID, integrity and authority gates.""",
    )
    write_text(handoff, text)


def update_history_almanac(ts: str, head: str, artifact: dict[str, Any]) -> None:
    path = ROOT / "PROJECT_HISTORY.json"
    data = load(path)
    events = data.get("events")
    if not isinstance(events, list):
        raise RuntimeError("PROJECT_HISTORY_EVENTS_INVALID")
    event_id = "ERA55A7_P0_DROP_LEDGER_TEMP_COPY_TEST_V1"
    if not any(isinstance(x, dict) and x.get("event_id") == event_id for x in events):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": ts,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "P0_DROP_LEDGER_SCHEMA_AND_TEMP_COPY_TEST",
                "status": "CLOSED_TEMP_COPY_TEST_PASS",
                "result": RESULT,
                "head_before_commit": head,
                "artifact": ARTIFACT_REL,
                "schema": SCHEMA_REL,
                "report": REPORT_REL,
                "event_count_loss": artifact["hard_gates"]["event_count_loss"],
                "uid_loss": artifact["hard_gates"]["uid_loss"],
                "production_unchanged": artifact["production_unchanged"],
                "production_apply_authorized": False,
                "next_safe_step": NEXT_SAFE_STEP,
            }
        )
    data.update({"updated_at": ts, "updated_at_utc": ts})
    write_json(path, data)

    path = ROOT / "04_ALMANAC.md"
    text = path.read_text(encoding="utf-8")
    heading = "## ERA55A_7 P0 DROP LEDGER DESIGN AND TEMP-COPY TEST"
    if heading not in text:
        marker = "\n---\n\n## ALMANAC RECORD INSERTION AND CORRECTION CONSTITUTION"
        if text.count(marker) != 1:
            raise RuntimeError("ALMANAC_INSERTION_MARKER_INVALID")
        gates = artifact["hard_gates"]
        model = artifact["test_result"]["model"]
        entry = f"""
---

{heading}

- Status: `CLOSED_TEMP_COPY_TEST_PASS`
- Result: `{RESULT}`
- Source candidates: `{model['source_count']}`
- Admitted: `{model['admitted_count']}`
- Overflow ledgered: `{model['overflow_count']}`
- Event count loss: `{gates['event_count_loss']}`
- UID loss: `{gates['uid_loss']}`
- Unledgered disposition: `{gates['unledgered_disposition']}`
- Integrity/quick check: `{gates['integrity_check']}/{gates['quick_check']}`
- Atomic rollback: `{str(gates['atomic_rollback_pass']).lower()}`
- Production unchanged: `{str(gates['production_unchanged']).lower()}`
- Production apply: `false`
- Next safe step: `{NEXT_SAFE_STEP}`
"""
        write_text(path, text.replace(marker, entry + marker, 1))


def commit_local() -> str:
    expected = sorted(set(CANONICAL + GENERATED))
    visible_expected = set(expected) - FORCE_ADD
    actual = {
        line for line in git("diff", "--name-only").splitlines() if line.strip()
    } | {
        line for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line.strip()
    }
    if actual != visible_expected:
        raise RuntimeError("UNEXPECTED_CHANGED_FILES=" + json.dumps(sorted(actual)))
    run(["git", "diff", "--check"])
    run(["git", "add", "--", *sorted(set(expected) - FORCE_ADD)])
    run(["git", "add", "-f", "--", *sorted(FORCE_ADD)])
    staged = sorted(x for x in git("diff", "--cached", "--name-only").splitlines() if x.strip())
    if staged != expected:
        raise RuntimeError("STAGED_FILES_MISMATCH")
    git("commit", "-m", "ERA55A7_P0_DROP_LEDGER_TEMP_COPY_TEST | PASS | NO_PRODUCTION_MUTATION")
    if git("status", "--porcelain"):
        raise RuntimeError("POST_COMMIT_WORKTREE_NOT_CLEAN")
    return git("rev-parse", "HEAD")


def main() -> int:
    head = require_preconditions()
    backup = Path(tempfile.mkdtemp(prefix="era55a7_backup_", dir="/tmp"))
    temp_dir = Path(tempfile.mkdtemp(prefix="era55a7_temp_copy_", dir="/tmp"))
    for rel in CANONICAL:
        src = ROOT / rel
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    committed = False
    try:
        ts = now()
        production_before = guard_snapshot()
        test = run_temp_copy_test(temp_dir)
        production_after = guard_snapshot()
        artifact = build_artifact(ts, head, production_before, production_after, test, temp_dir)
        write_text(ROOT / SCHEMA_REL, SCHEMA_SQL)
        write_json(ROOT / ARTIFACT_REL, artifact)
        write_text(ROOT / REPORT_REL, make_report(artifact))
        update_runtime(ts)
        update_roadmap(ts)
        update_docs(artifact)
        update_history_almanac(ts, head, artifact)
        for rel in (ARTIFACT_REL, "PROJECT_RUNTIME.json", "PROJECT_HISTORY.json", "data/tokenoskobi_v1_v8_master_era_roadmap.json"):
            load(ROOT / rel)
        commit = commit_local()
        committed = True
        gates = artifact["hard_gates"]
        model = artifact["test_result"]["model"]
        print("ERA55A7_P0_DROP_LEDGER_TEMP_COPY_TEST=SUCCESS")
        print(f"RESULT={RESULT}")
        print(f"LOCAL_COMMIT={commit}")
        print(f"SOURCE_CANDIDATES={model['source_count']}")
        print(f"ADMITTED={model['admitted_count']}")
        print(f"OVERFLOW_LEDGERED={model['overflow_count']}")
        print(f"DUPLICATE_REMOVED={model['duplicate_removed_count']}")
        print(f"UNSAFE_FILTERED={model['unsafe_filtered_count']}")
        print(f"INVALID_CANDIDATES={model['invalid_candidate_count']}")
        print(f"EVENT_COUNT_LOSS={gates['event_count_loss']}")
        print(f"UID_LOSS={gates['uid_loss']}")
        print(f"DUPLICATE_REGRESSION={gates['duplicate_regression']}")
        print(f"UNLEDGERED_DISPOSITION={gates['unledgered_disposition']}")
        print(f"OVERFLOW_WRONG_REASON={gates['overflow_wrong_reason_count']}")
        print(f"INTEGRITY_CHECK={gates['integrity_check']}")
        print(f"QUICK_CHECK={gates['quick_check']}")
        print(f"ATOMIC_ROLLBACK_PASS={str(gates['atomic_rollback_pass']).lower()}")
        print(f"CONSTRAINT_TESTS_PASS={str(gates['constraint_tests_pass']).lower()}")
        print(f"PRODUCTION_UNCHANGED={str(gates['production_unchanged']).lower()}")
        print("P0_LEDGER_SCHEMA_TEMP_COPY_VALIDATED=true")
        print("P0_F1_CLOSED=false")
        print("PRODUCTION_LEDGER_APPLY_AUTHORIZED=false")
        print("OPTIMIZATION_APPLY_AUTHORIZED=false")
        print("LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false")
        print(f"NEXT_SAFE_STEP={NEXT_SAFE_STEP}")
        print(f"SCHEMA={SCHEMA_REL}")
        print(f"ARTIFACT={ARTIFACT_REL}")
        print(f"REPORT={REPORT_REL}")
        print(f"TEMP_DIR={temp_dir}")
        print("WORKTREE=CLEAN")
        return 0
    except Exception:
        if not committed:
            run(["git", "reset", "--mixed", "HEAD"], check=False)
            for rel in CANONICAL:
                src = backup / rel
                dst = ROOT / rel
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            for rel in GENERATED:
                path = ROOT / rel
                if path.exists():
                    path.unlink()
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERA55A7_P0_DROP_LEDGER_TEMP_COPY_TEST=FAILED:{exc}", file=sys.stderr)
        raise
