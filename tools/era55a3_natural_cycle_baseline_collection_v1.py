#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"
WORK_UNIT = "ERA55A_3_NATURAL_CYCLE_BASELINE_COLLECTION"
ARTIFACT_REL = "data/control/era55a3_natural_cycle_baseline_collection_v1.json"
REPORT_REL = "reports/LATEST_ERA55A3_NATURAL_CYCLE_BASELINE_COLLECTION.md"
A1_REL = "data/control/era55_runtime_optimization_init_v1.json"
A2_REL = "data/control/era55a2_granular_instrumentation_and_baseline_measurement_plan_v1.json"
NEXT_SAFE_STEP = "ERA55A_4_BASELINE_CONSOLIDATION_AND_EXTENDED_SAMPLE_REVIEW"
DB_REL = "data/tokenoskobi_clean_v1.sqlite"
DISPLAY_REL = "runtime/state/news_coverage_panel_display_v1.json"
HOT_REL = "runtime/state/hot_intelligence_ingress_gateway_v1.json"
BRIDGE_REL = "runtime/state/news_active_panel_data_bridge_v1.json"
ACTIVE_DISPLAY_REL = "active_panel_8096/current/data/news_coverage_panel_display_v1.json"
ACTIVE_HOT_REL = "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"

CANONICAL_FILES = [
    "PROJECT_RUNTIME.json",
    "PROJECT_HISTORY.json",
    "data/tokenoskobi_v1_v8_master_era_roadmap.json",
    "04_ALMANAC.md",
    "06_PROJECT_MASTER_STATE.md",
    "07_PROJECT_HANDOFF.md",
]
GENERATED_FILES = [ARTIFACT_REL, REPORT_REL]
FORCE_ADD = {REPORT_REL}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(
    cmd: list[str],
    *,
    timeout: int = 180,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            "COMMAND_FAILED="
            + json.dumps(
                {
                    "cmd": cmd,
                    "rc": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                },
                ensure_ascii=False,
            )
        )
    return completed


def git(*args: str, timeout: int = 180) -> str:
    return run(["git", *args], timeout=timeout).stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED={path}")
    return value


def read_json_optional(path: Path) -> dict[str, Any]:
    try:
        return load_json(path)
    except Exception:
        return {}


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
    )


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_iso_prefix(line: str) -> datetime | None:
    token = line.split(" ", 1)[0].strip()
    try:
        return datetime.fromisoformat(token).astimezone(timezone.utc)
    except Exception:
        return None


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
    return round(float(ordered[index]), 3)


def parse_service_cycles(text: str) -> dict[str, Any]:
    cycles: list[dict[str, Any]] = []
    active_start: datetime | None = None
    overlap_count = 0
    timeout_lines: list[str] = []
    failure_lines: list[str] = []

    for line in text.splitlines():
        timestamp = parse_iso_prefix(line)
        lower = line.lower()
        if "starting tokenoskobi-news-radar-refresh.service" in lower:
            if active_start is not None:
                overlap_count += 1
            active_start = timestamp
            continue
        if "timed out" in lower or "timeout" in lower and "timeoutstart" not in lower:
            timeout_lines.append(line)
        if any(term in lower for term in ("failed", "status=", "invalidargument", "killed")):
            failure_lines.append(line)
        if (
            "finished tokenoskobi-news-radar-refresh.service" in lower
            or "tokenoskobi-news-radar-refresh.service: deactivated successfully" in lower
        ):
            if active_start is not None and timestamp is not None:
                duration_ms = max(0.0, (timestamp - active_start).total_seconds() * 1000.0)
                cycles.append(
                    {
                        "started_at_utc": active_start.isoformat(),
                        "finished_at_utc": timestamp.isoformat(),
                        "duration_ms": round(duration_ms, 3),
                    }
                )
                active_start = None

    durations = [float(item["duration_ms"]) for item in cycles]
    return {
        "cycle_count": len(cycles),
        "cycles": cycles,
        "duration_ms": {
            "min": round(min(durations), 3) if durations else None,
            "p50": round(statistics.median(durations), 3) if durations else None,
            "p95": percentile(durations, 0.95),
            "max": round(max(durations), 3) if durations else None,
            "mean": round(statistics.fmean(durations), 3) if durations else None,
        },
        "overlap_count": overlap_count,
        "timeout_count": len(timeout_lines),
        "timeout_lines": timeout_lines[-20:],
        "failure_count": len(failure_lines),
        "failure_lines": failure_lines[-20:],
        "unclosed_start_present": active_start is not None,
    }


def service_show() -> dict[str, Any]:
    props = [
        "ActiveState",
        "SubState",
        "Result",
        "ExecMainStatus",
        "ExecMainStartTimestamp",
        "ExecMainExitTimestamp",
        "ExecMainStartTimestampMonotonic",
        "ExecMainExitTimestampMonotonic",
        "TimeoutStartUSec",
        "RuntimeMaxUSec",
        "MainPID",
    ]
    result = run(
        [
            "systemctl",
            "show",
            SERVICE,
            "--no-pager",
            "--property=" + ",".join(props),
        ],
        timeout=30,
    )
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def timer_show() -> dict[str, Any]:
    props = [
        "ActiveState",
        "SubState",
        "UnitFileState",
        "LastTriggerUSec",
        "NextElapseUSecRealtime",
        "NextElapseUSecMonotonic",
        "AccuracyUSec",
        "RandomizedDelayUSec",
        "OnUnitActiveUSec",
        "OnActiveUSec",
    ]
    result = run(
        [
            "systemctl",
            "show",
            TIMER,
            "--no-pager",
            "--property=" + ",".join(props),
        ],
        timeout=30,
    )
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    values["list_timers"] = run(
        ["systemctl", "list-timers", "--all", TIMER, "--no-pager"],
        timeout=30,
    ).stdout.strip()
    return values


def parse_usec(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    match = re.fullmatch(r"(\d+)min\s+(\d+)s", text)
    if match:
        return (int(match.group(1)) * 60 + int(match.group(2))) * 1_000_000
    match = re.fullmatch(r"(\d+)min", text)
    if match:
        return int(match.group(1)) * 60 * 1_000_000
    match = re.fullmatch(r"(\d+)s", text)
    if match:
        return int(match.group(1)) * 1_000_000
    match = re.fullmatch(r"(\d+)ms", text)
    if match:
        return int(match.group(1)) * 1_000
    return None


def db_snapshot() -> dict[str, Any]:
    db = ROOT / DB_REL
    if not db.is_file():
        return {"exists": False, "path": str(db)}
    connection = sqlite3.connect(
        f"file:{db}?mode=ro",
        uri=True,
        timeout=20,
    )
    try:
        connection.execute("PRAGMA query_only=ON")
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        target_tables = [
            "news_raw_feed_events",
            "news_token_match_events",
            "news_signal_events",
            "news_score_events_v1",
            "news_runtime_freshness_v1",
        ]
        counts: dict[str, int] = {}
        max_values: dict[str, Any] = {}
        uid_duplicates: dict[str, Any] = {}
        for table in target_tables:
            if table not in tables:
                continue
            qtable = '"' + table.replace('"', '""') + '"'
            counts[table] = int(
                connection.execute(f"SELECT COUNT(*) FROM {qtable}").fetchone()[0]
            )
            columns = [
                str(row[1])
                for row in connection.execute(f"PRAGMA table_info({qtable})").fetchall()
            ]
            for candidate in (
                "updated_at_utc",
                "created_at_utc",
                "published_at_utc",
                "timestamp_utc",
                "observed_at_utc",
                "ts_utc",
            ):
                if candidate in columns:
                    qcol = '"' + candidate.replace('"', '""') + '"'
                    max_values[table] = {
                        "column": candidate,
                        "value": connection.execute(
                            f"SELECT MAX({qcol}) FROM {qtable}"
                        ).fetchone()[0],
                    }
                    break
            uid_column = next(
                (
                    column
                    for column in (
                        "event_uid",
                        "news_uid",
                        "signal_uid",
                        "score_uid",
                    )
                    if column in columns
                ),
                None,
            )
            if uid_column:
                quid = '"' + uid_column.replace('"', '""') + '"'
                duplicate_groups = int(
                    connection.execute(
                        f"SELECT COUNT(*) FROM ("
                        f"SELECT {quid} FROM {qtable} "
                        f"WHERE {quid} IS NOT NULL AND {quid} <> '' "
                        f"GROUP BY {quid} HAVING COUNT(*) > 1)"
                    ).fetchone()[0]
                )
                uid_duplicates[table] = {
                    "uid_column": uid_column,
                    "duplicate_groups": duplicate_groups,
                }
        pragmas = {}
        for name in (
            "journal_mode",
            "synchronous",
            "page_count",
            "freelist_count",
            "page_size",
            "query_only",
        ):
            row = connection.execute(f"PRAGMA {name}").fetchone()
            pragmas[name] = row[0] if row else None
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        quick = connection.execute("PRAGMA quick_check").fetchone()
        return {
            "exists": True,
            "path": str(db),
            "size_bytes": db.stat().st_size,
            "mtime_utc": datetime.fromtimestamp(
                db.stat().st_mtime,
                timezone.utc,
            ).isoformat(),
            "sha256": sha256_file(db),
            "query_only": True,
            "total_changes": connection.total_changes,
            "pragmas": pragmas,
            "integrity_check": integrity[0] if integrity else None,
            "quick_check": quick[0] if quick else None,
            "table_counts": counts,
            "table_max_timestamps": max_values,
            "uid_duplicates": uid_duplicates,
        }
    finally:
        connection.close()


def file_snapshot(rel: str) -> dict[str, Any]:
    path = ROOT / rel
    if not path.is_file():
        return {"exists": False}
    result: dict[str, Any] = {
        "exists": True,
        "size_bytes": path.stat().st_size,
        "mtime_utc": datetime.fromtimestamp(
            path.stat().st_mtime,
            timezone.utc,
        ).isoformat(),
        "sha256": sha256_file(path),
    }
    if path.suffix == ".json":
        data = read_json_optional(path)
        for key in (
            "generated_at_utc",
            "updated_at_utc",
            "created_at_utc",
            "hot_queue_count",
        ):
            if key in data:
                result[key] = data.get(key)
    return result


def runtime_file_snapshots() -> dict[str, Any]:
    return {
        rel: file_snapshot(rel)
        for rel in (
            DISPLAY_REL,
            HOT_REL,
            BRIDGE_REL,
            ACTIVE_DISPLAY_REL,
            ACTIVE_HOT_REL,
        )
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


def queue_snapshot() -> dict[str, Any]:
    display = read_json_optional(ROOT / DISPLAY_REL)
    hot = read_json_optional(ROOT / HOT_REL)
    normalized: list[dict[str, Any]] = []
    source_items = 0
    unsafe_filtered = 0

    for section in display.get("sections") or []:
        section_id = section.get("id")
        if section_id == "news_market_indicator":
            lane = "MARKET_INDICATOR"
        elif section_id == "news_adversarial_intelligence":
            lane = "ADVERSARIAL_NEWS"
        else:
            continue
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            source_items += 1
            authority = item.get("authority") or {}
            if any(
                authority.get(key) is not False
                for key in (
                    "db_write",
                    "hunter_authorized",
                    "trade_signal",
                    "paper_signal",
                )
            ):
                unsafe_filtered += 1
                continue
            normalized.append(
                {
                    "hot_uid": uid_for(item, lane),
                    "lane": lane,
                    "event_uid": item.get("event_uid"),
                    "news_uid": item.get("news_uid"),
                    "title": item.get("title"),
                    "published_at_utc": item.get("published_at_utc"),
                    "priority_score": score_item(item, lane),
                }
            )

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    duplicate_removed: list[str] = []
    for item in sorted(
        normalized,
        key=lambda value: (
            -int(value.get("priority_score") or 0),
            str(value.get("hot_uid") or ""),
        ),
    ):
        uid = str(item.get("hot_uid") or "")
        if uid in seen:
            duplicate_removed.append(uid)
            continue
        seen.add(uid)
        deduped.append(item)

    admitted = deduped[:50]
    overflow = deduped[50:]
    actual_queue = hot.get("hot_queue") if isinstance(hot.get("hot_queue"), list) else []
    actual_uids = {
        str(item.get("hot_uid") or "")
        for item in actual_queue
        if isinstance(item, dict)
    }
    expected_uids = {str(item.get("hot_uid") or "") for item in admitted}
    missing_expected = sorted(expected_uids - actual_uids)
    unexpected_actual = sorted(actual_uids - expected_uids)

    ledger_keys = {
        "drop_ledger",
        "dropped_events",
        "overflow_events",
        "evicted_events",
        "overflow_count",
        "dropped_count",
        "evicted_count",
    }
    drop_ledger_detected = any(key in hot for key in ledger_keys)

    if overflow and not drop_ledger_detected:
        classification = "SILENT_TRUNCATION_CONFIRMED_CURRENT_SNAPSHOT"
    elif not overflow and not drop_ledger_detected:
        classification = "SILENT_TRUNCATION_CAPABILITY_EXISTS_NOT_OBSERVED"
    elif overflow and drop_ledger_detected:
        classification = "OVERFLOW_OBSERVED_WITH_LEDGER"
    else:
        classification = "NO_OVERFLOW_CURRENT_SNAPSHOT"

    gateway_time = hot.get("generated_at_utc")
    residence_values: list[float] = []
    if gateway_time:
        try:
            gateway_dt = datetime.fromisoformat(str(gateway_time).replace("Z", "+00:00"))
            if gateway_dt.tzinfo is None:
                gateway_dt = gateway_dt.replace(tzinfo=timezone.utc)
            for item in admitted:
                published = item.get("published_at_utc")
                if not published:
                    continue
                try:
                    published_dt = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
                    if published_dt.tzinfo is None:
                        published_dt = published_dt.replace(tzinfo=timezone.utc)
                    residence_values.append(
                        max(0.0, (gateway_dt - published_dt).total_seconds() * 1000.0)
                    )
                except Exception:
                    continue
        except Exception:
            pass

    return {
        "source_candidate_count": source_items,
        "unsafe_filtered_count": unsafe_filtered,
        "normalized_candidate_count": len(normalized),
        "deduplicated_candidate_count": len(deduped),
        "duplicate_removed_count": len(duplicate_removed),
        "duplicate_removed_uids": duplicate_removed,
        "admitted_count": len(admitted),
        "overflow_count": len(overflow),
        "lowest_admitted_priority": min(
            (int(item.get("priority_score") or 0) for item in admitted),
            default=None,
        ),
        "highest_overflow_priority": max(
            (int(item.get("priority_score") or 0) for item in overflow),
            default=None,
        ),
        "overflow_events": overflow,
        "overflow_event_uids": [item.get("hot_uid") for item in overflow],
        "actual_hot_queue_count": len(actual_queue),
        "actual_hot_queue_declared_count": hot.get("hot_queue_count"),
        "missing_expected_admitted_uids": missing_expected,
        "unexpected_actual_uids": unexpected_actual,
        "actual_matches_deterministic_top50": not missing_expected and not unexpected_actual,
        "drop_ledger_detected": drop_ledger_detected,
        "classification": classification,
        "queue_residence_proxy_ms": {
            "sample_count": len(residence_values),
            "min": round(min(residence_values), 3) if residence_values else None,
            "p50": round(statistics.median(residence_values), 3) if residence_values else None,
            "p95": percentile(residence_values, 0.95),
            "max": round(max(residence_values), 3) if residence_values else None,
        },
        "raw_to_queue_drop_claim_allowed": False,
        "reason": "Raw events are not all queue candidates; drop evidence must be derived from normalized display candidates.",
    }


def monotonic_usec() -> int:
    uptime_seconds = float(Path("/proc/uptime").read_text().split()[0])
    return int(uptime_seconds * 1_000_000)


def observe_next_natural_cycle(
    timer_interval_seconds: int,
    service_timeout_seconds: int,
) -> dict[str, Any]:
    before_service = service_show()
    before_start = int(before_service.get("ExecMainStartTimestampMonotonic") or 0)
    before = {
        "captured_at_utc": utc_now(),
        "service": before_service,
        "timer": timer_show(),
        "db": db_snapshot(),
        "files": runtime_file_snapshots(),
        "queue": queue_snapshot(),
    }

    maximum_wait = int(
        os.environ.get(
            "ERA55A3_MAX_WAIT_SECONDS",
            str(max(timer_interval_seconds + 120, 300)),
        )
    )
    deadline = time.monotonic() + maximum_wait
    observed_start_values: dict[str, Any] | None = None

    next_monotonic = parse_usec(before["timer"].get("NextElapseUSecMonotonic"))
    if next_monotonic:
        remaining = (next_monotonic - monotonic_usec()) / 1_000_000
        if remaining > 4:
            time.sleep(min(remaining - 3, max(0.0, deadline - time.monotonic())))

    while time.monotonic() < deadline:
        current = service_show()
        start_value = int(current.get("ExecMainStartTimestampMonotonic") or 0)
        if start_value and start_value != before_start:
            observed_start_values = current
            break
        time.sleep(1.0)

    if observed_start_values is None:
        return {
            "observed": False,
            "reason": "NEXT_NATURAL_CYCLE_NOT_OBSERVED_WITHIN_WINDOW",
            "maximum_wait_seconds": maximum_wait,
            "before": before,
        }

    start_monotonic = int(observed_start_values.get("ExecMainStartTimestampMonotonic") or 0)
    completion_deadline = time.monotonic() + max(service_timeout_seconds + 30, 120)
    observed_file_changes: dict[str, str] = {}
    initial_files = before["files"]

    while time.monotonic() < completion_deadline:
        current_files = runtime_file_snapshots()
        for rel, value in current_files.items():
            if value.get("mtime_utc") and value.get("mtime_utc") != (initial_files.get(rel) or {}).get("mtime_utc"):
                observed_file_changes.setdefault(rel, str(value.get("mtime_utc")))
        current_service = service_show()
        exit_monotonic = int(current_service.get("ExecMainExitTimestampMonotonic") or 0)
        if (
            exit_monotonic >= start_monotonic
            and current_service.get("ActiveState") == "inactive"
        ):
            after_service = current_service
            break
        time.sleep(0.1)
    else:
        after_service = service_show()

    after = {
        "captured_at_utc": utc_now(),
        "service": after_service,
        "timer": timer_show(),
        "db": db_snapshot(),
        "files": runtime_file_snapshots(),
        "queue": queue_snapshot(),
    }

    exit_monotonic = int(after_service.get("ExecMainExitTimestampMonotonic") or 0)
    runner_duration_ms = (
        round((exit_monotonic - start_monotonic) / 1000.0, 3)
        if exit_monotonic >= start_monotonic and start_monotonic > 0
        else None
    )
    timer_interval_ms = timer_interval_seconds * 1000
    safety_margin_ms = (
        round(timer_interval_ms - runner_duration_ms, 3)
        if runner_duration_ms is not None
        else None
    )

    before_counts = (before["db"] or {}).get("table_counts") or {}
    after_counts = (after["db"] or {}).get("table_counts") or {}
    count_deltas = {
        table: int(after_counts.get(table, 0)) - int(before_counts.get(table, 0))
        for table in sorted(set(before_counts) | set(after_counts))
    }

    stage_mtimes = {
        rel: value.get("mtime_utc")
        for rel, value in after["files"].items()
        if value.get("mtime_utc") != (before["files"].get(rel) or {}).get("mtime_utc")
    }

    return {
        "observed": True,
        "maximum_wait_seconds": maximum_wait,
        "before": before,
        "after": after,
        "runner_execution_ms": runner_duration_ms,
        "timer_interval_ms": timer_interval_ms,
        "timer_safety_margin_ms": safety_margin_ms,
        "service_result": after_service.get("Result"),
        "service_exit_status": after_service.get("ExecMainStatus"),
        "db_count_deltas": count_deltas,
        "observed_file_changes_during_cycle": observed_file_changes,
        "stage_file_mtimes_after_cycle": stage_mtimes,
        "db_integrity_preserved": (after["db"] or {}).get("integrity_check") == "ok",
        "db_quick_check_preserved": (after["db"] or {}).get("quick_check") == "ok",
        "queue_classification_before": (before["queue"] or {}).get("classification"),
        "queue_classification_after": (after["queue"] or {}).get("classification"),
    }


def boot_time_utc() -> datetime:
    uptime_seconds = float(Path("/proc/uptime").read_text().split()[0])
    return datetime.fromtimestamp(time.time() - uptime_seconds, timezone.utc)


def historical_baselines(timer_interval_seconds: int) -> dict[str, Any]:
    journal_24h = run(
        [
            "journalctl",
            "-u",
            SERVICE,
            "--since",
            "24 hours ago",
            "--no-pager",
            "-o",
            "short-iso",
        ],
        timeout=60,
    ).stdout
    journal_12h = run(
        [
            "journalctl",
            "-u",
            SERVICE,
            "--since",
            "12 hours ago",
            "--no-pager",
            "-o",
            "short-iso",
        ],
        timeout=60,
    ).stdout
    journal_boot = run(
        [
            "journalctl",
            "-b",
            "-u",
            SERVICE,
            "--no-pager",
            "-o",
            "short-iso",
        ],
        timeout=60,
    ).stdout

    all_24h = parse_service_cycles(journal_24h)
    hot_12h = parse_service_cycles(journal_12h)
    boot_cycles = parse_service_cycles(journal_boot)
    boot_time = boot_time_utc()
    first_three = boot_cycles["cycles"][:3]
    first_cycle_near_boot = False
    if first_three:
        first_start = datetime.fromisoformat(first_three[0]["started_at_utc"])
        first_cycle_near_boot = (first_start - boot_time).total_seconds() <= 1800

    cold_classification = (
        "CURRENT_BOOT_FIRST_THREE_CYCLES_OBSERVED"
        if len(first_three) == 3 and first_cycle_near_boot
        else "TRUE_COLD_START_NOT_OBSERVED"
    )

    max_duration = (all_24h.get("duration_ms") or {}).get("max")
    p95_duration = (all_24h.get("duration_ms") or {}).get("p95")
    timer_interval_ms = timer_interval_seconds * 1000

    return {
        "historical_24h": all_24h,
        "hot_state_12h": hot_12h,
        "cold_start_current_boot": {
            "boot_time_utc": boot_time.isoformat(),
            "classification": cold_classification,
            "first_cycle_within_30min_of_boot": first_cycle_near_boot,
            "first_three_cycles": first_three,
        },
        "timer_interval_ms": timer_interval_ms,
        "p95_safety_margin_ms": (
            round(timer_interval_ms - float(p95_duration), 3)
            if p95_duration is not None
            else None
        ),
        "max_safety_margin_ms": (
            round(timer_interval_ms - float(max_duration), 3)
            if max_duration is not None
            else None
        ),
        "overlap_observed": bool(all_24h.get("overlap_count")),
        "timeout_observed": bool(all_24h.get("timeout_count")),
    }


def preconditions() -> tuple[str, dict[str, Any]]:
    os.chdir(ROOT)
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BLOCKED=BRANCH_NOT_MAIN")
    status = git("status", "--porcelain")
    if status:
        raise RuntimeError("BLOCKED=WORKTREE_NOT_CLEAN\n" + status)
    git("fetch", "origin", "main")
    local_head = git("rev-parse", "HEAD")
    remote_head = git("rev-parse", "origin/main")
    if local_head != remote_head:
        raise RuntimeError(
            f"BLOCKED=LOCAL_REMOTE_NOT_SYNCED:LOCAL={local_head}:REMOTE={remote_head}"
        )
    runtime = load_json(ROOT / "PROJECT_RUNTIME.json")
    if runtime.get("current_era") != "ERA55":
        raise RuntimeError(f"BLOCKED=CURRENT_ERA_NOT_ERA55:{runtime.get('current_era')}")
    if (runtime.get("era55_status") or {}).get("status") != "OPEN":
        raise RuntimeError("BLOCKED=ERA55_NOT_OPEN")
    next_step = runtime.get("next_safe_step") or {}
    if next_step.get("id") != WORK_UNIT:
        raise RuntimeError(f"BLOCKED=UNEXPECTED_NEXT_SAFE_STEP:{next_step.get('id')}")
    a2 = load_json(ROOT / A2_REL)
    if a2.get("result") != "OK_PLAN_LOCKED_NO_LIVE_MUTATION":
        raise RuntimeError(f"BLOCKED=A2_PLAN_NOT_LOCKED:{a2.get('result')}")
    contract = a2.get("collector_contract") or {}
    if contract.get("must_not_invoke_runner") is not True:
        raise RuntimeError("BLOCKED=A2_RUNNER_GUARD_MISSING")
    if contract.get("sqlite_query_only") is not True:
        raise RuntimeError("BLOCKED=A2_SQLITE_READONLY_GUARD_MISSING")
    return local_head, a2


def derive_result(
    historical: dict[str, Any],
    natural: dict[str, Any],
    queue: dict[str, Any],
) -> tuple[str, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []

    classification = str(queue.get("classification") or "UNKNOWN")
    if classification == "SILENT_TRUNCATION_CONFIRMED_CURRENT_SNAPSHOT":
        findings.append(
            {
                "priority": "P0",
                "code": "SILENT_TRUNCATION_CONFIRMED_CURRENT_SNAPSHOT",
                "finding": f"{queue.get('overflow_count')} normalized candidates were outside deterministic top 50 and no drop ledger was detected.",
            }
        )
    elif classification == "SILENT_TRUNCATION_CAPABILITY_EXISTS_NOT_OBSERVED":
        findings.append(
            {
                "priority": "P0",
                "code": "SILENT_TRUNCATION_CAPABILITY_EXISTS_NOT_OBSERVED",
                "finding": "Top-50 truncation exists but current snapshot produced no overflow; absence of historical ledger prevents a no-loss claim.",
            }
        )

    if not queue.get("actual_matches_deterministic_top50"):
        findings.append(
            {
                "priority": "P0",
                "code": "HOT_QUEUE_OUTPUT_MISMATCH",
                "finding": "Actual hot queue does not match independently reconstructed deterministic top 50.",
            }
        )

    if historical.get("overlap_observed"):
        findings.append(
            {
                "priority": "P0",
                "code": "TIMER_OVERLAP_OBSERVED",
                "finding": "Historical journal contains a new start before the previous cycle was closed.",
            }
        )
    else:
        findings.append(
            {
                "priority": "INFO",
                "code": "TIMER_OVERLAP_NOT_OBSERVED_24H",
                "finding": "No overlap was observed in available 24-hour journal evidence.",
            }
        )

    if historical.get("timeout_observed"):
        findings.append(
            {
                "priority": "P0",
                "code": "SERVICE_TIMEOUT_OBSERVED",
                "finding": "Historical journal contains timeout evidence.",
            }
        )

    if natural.get("observed") is not True:
        findings.append(
            {
                "priority": "P1",
                "code": "NATURAL_CYCLE_NOT_OBSERVED",
                "finding": "The next natural timer cycle was not observed inside the bounded collection window.",
            }
        )
    else:
        if not natural.get("db_integrity_preserved") or not natural.get("db_quick_check_preserved"):
            findings.append(
                {
                    "priority": "P0",
                    "code": "SQLITE_INTEGRITY_REGRESSION",
                    "finding": "SQLite integrity or quick check was not preserved after the natural cycle.",
                }
            )

    p0 = [item for item in findings if item["priority"] == "P0"]
    if p0:
        return "WARN_P0_BASELINE_FINDINGS_RECORDED", findings
    if natural.get("observed") is not True:
        return "WARN_PARTIAL_BASELINE_NATURAL_CYCLE_NOT_OBSERVED", findings
    return "OK_BASELINE_EVIDENCE_COLLECTED", findings


def update_runtime(
    collected_at: str,
    result: str,
    findings: list[dict[str, str]],
) -> None:
    path = ROOT / "PROJECT_RUNTIME.json"
    data = load_json(path)
    work_unit = {
        "id": WORK_UNIT,
        "type": "ERA55_NATURAL_CYCLE_BASELINE_COLLECTION",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "artifact": ARTIFACT_REL,
        "report": REPORT_REL,
        "status": "CLOSED",
        "result": result,
        "runtime_db_service_timer_panel_mutation": False,
        "manual_runner_execution": False,
        "next_step": NEXT_SAFE_STEP,
    }
    next_step = {
        "id": NEXT_SAFE_STEP,
        "type": "ERA55_BASELINE_CONSOLIDATION_REVIEW",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "serves": "V3_RUNTIME_INTELLIGENCE_OS",
        "purpose": "Consolidate A1-A3 evidence, determine sample sufficiency and define any extended read-only baseline required before the A5 report.",
        "human_authorization_required": True,
        "optimization_apply_authorized": False,
        "production_burst_load_authorized": False,
        "gemini_red_team_review_after_baseline_report": True,
        "status": "READY",
    }
    last_action = {
        "timestamp": collected_at,
        "task": WORK_UNIT,
        "result": result,
        "artifact": ARTIFACT_REL,
    }
    data["mode"] = "ERA55A3_NATURAL_CYCLE_BASELINE_COLLECTION_CLOSED"
    data["project_status"] = "ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE_EVIDENCE"
    data["status"] = "WORK_UNIT_CLOSED"
    data["last_completed"] = WORK_UNIT
    data["last_action"] = last_action
    data["recent_event"] = dict(last_action)
    data["current_work_unit"] = work_unit
    data["next_safe_step"] = next_step
    state = data.setdefault("current_state", {})
    state.update(
        {
            "mode": data["mode"],
            "runtime_status": "WORK_UNIT_CLOSED",
            "project_status": "ACTIVE",
            "updated_at": collected_at,
            "last_action": dict(last_action),
            "active_work_unit": dict(work_unit),
            "next_safe_step": dict(next_step),
            "current_problem": None,
        }
    )
    era55 = data.setdefault("era55_status", {})
    era55.update(
        {
            "status": "OPEN",
            "active_stage": "ERA55A_BASELINE_MEASUREMENT",
            "last_completed_substep": WORK_UNIT,
            "next_safe_step": NEXT_SAFE_STEP,
            "a3_artifact": ARTIFACT_REL,
            "a3_report": REPORT_REL,
            "baseline_evidence_collected": True,
            "optimization_apply_authorized": False,
            "burst_load_authorized": False,
            "manual_runner_execution_authorized": False,
            "runtime_db_service_timer_panel_mutation": False,
            "gemini_red_team_required": True,
        }
    )
    data["open_risks"] = [
        f"{item['priority']}:{item['code']}:{item['finding']}"
        for item in findings
        if item["priority"] in ("P0", "P1")
    ] + ["Risk is minimized, never zero."]
    data["source"] = "era55a3_natural_cycle_baseline_collection_v1"
    data["updated_at"] = collected_at
    data["updated_at_utc"] = collected_at
    atomic_write_json(path, data)


def update_roadmap_json(collected_at: str, result: str) -> None:
    path = ROOT / "data/tokenoskobi_v1_v8_master_era_roadmap.json"
    data = load_json(path)
    found = False
    for version in data.get("versions", []):
        if version.get("id") != "V3":
            continue
        for child in version.get("children", []):
            if child.get("id") == "ERA55":
                child.update(
                    {
                        "status": "OPEN",
                        "active_stage": "ERA55A_BASELINE_MEASUREMENT",
                        "last_completed_substep": WORK_UNIT,
                        "last_result": result,
                        "next_safe_step": NEXT_SAFE_STEP,
                        "baseline_artifact": ARTIFACT_REL,
                        "optimization_apply_authorized": False,
                        "burst_load_authorized": False,
                        "gemini_red_team_required": True,
                    }
                )
                found = True
    if not found:
        raise RuntimeError("ERA55_NOT_FOUND_IN_ROADMAP_JSON")
    data["updated_at"] = collected_at
    data["git_head"] = "DYNAMIC_USE_GIT_REV_PARSE_HEAD"
    data["work_unit"] = WORK_UNIT
    atomic_write_json(path, data)


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(
        rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND={heading}")
    return text[: match.start()] + heading + "\n\n" + body.rstrip() + "\n" + text[match.end() :]


def update_master(result: str, findings: list[dict[str, str]]) -> None:
    path = ROOT / "06_PROJECT_MASTER_STATE.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "PROJECT_STATUS=ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE_PLAN_LOCKED",
        "PROJECT_STATUS=ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE_EVIDENCE",
        1,
    )
    section_02 = """```text
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_BASELINE_MEASUREMENT
LAST_COMPLETED_SUBSTEP=ERA55A_3_NATURAL_CYCLE_BASELINE_COLLECTION
BASELINE_EVIDENCE_COLLECTED=true
GEMINI_RED_TEAM_REQUIRED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
MANUAL_RUNNER_EXECUTION_AUTHORIZED=false
```

A3 collected historical and natural-cycle evidence through an external read-only observer. No live runtime configuration was changed."""
    section_03 = f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={result}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_MUTATION=false
```

The evidence includes reconstructed queue overflow, historical runner distributions, overlap/timeout review, SQLite checks and one bounded natural-cycle observation attempt."""
    risk_lines = "\n".join(
        f"- `{item['priority']} {item['code']}` — {item['finding']}"
        for item in findings
        if item["priority"] in ("P0", "P1")
    ) or "- No P0/P1 finding was recorded in A3."
    section_09 = risk_lines + "\n- Optimization apply and production burst load remain blocked.\n- Runtime risk is minimized, never zero.\n- Git HEAD must be read dynamically."
    section_10 = f"""```text
NEXT_SAFE_STEP={NEXT_SAFE_STEP}
```

A4 will judge whether A3 evidence is sufficient, define any additional read-only samples and prepare the consolidated baseline path toward A5 and Gemini review."""
    text = replace_section(text, "## 02 CURRENT MAJOR-LINE POSITION", section_02)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", section_03)
    text = replace_section(text, "## 09 OPEN RISKS AND DECISIONS", section_09)
    text = replace_section(text, "## 10 NEXT SAFE STEP", section_10)
    atomic_write_text(path, text)


def update_handoff(result: str, findings: list[dict[str, str]]) -> None:
    path = ROOT / "07_PROJECT_HANDOFF.md"
    text = path.read_text(encoding="utf-8")
    checkpoint = """PROJECT_STATUS=ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE_EVIDENCE
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_BASELINE_MEASUREMENT
LAST_COMPLETED_SUBSTEP=ERA55A_3_NATURAL_CYCLE_BASELINE_COLLECTION
BASELINE_EVIDENCE_COLLECTED=true
GEMINI_RED_TEAM_REQUIRED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
MANUAL_RUNNER_EXECUTION_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A3 is closed. No runner, service, timer, database, queue policy or panel mutation was applied."""
    last_work = f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={result}
LAST_ARTIFACT={ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=null

A4 must consolidate the evidence before any optimization target is selected."""
    do_not = """- Do not reopen ERA54.
- Do not rebuild NEWS from zero.
- Do not manually invoke the production runner for baseline claims.
- Do not start, restart, edit, enable or disable the service or timer.
- Do not apply watchdog, index, WAL, cache, queue-policy or incremental-write changes.
- Do not run production BURST_LOAD.
- Do not infer zero event loss from raw-to-queue absence.
- Do not infer missing latency measurements.
- Do not close ERA55 before Gemini Red Team findings are resolved."""
    decisions = f"""Current authorized direction:

- `ERA55_RUNTIME_OPTIMIZATION` is open.
- A1 inspection, A2 planning and A3 baseline evidence collection are complete.
- A4 evidence consolidation is the only next action.
- Optimization apply and burst load remain unauthorized.

NEXT_SAFE_STEP={NEXT_SAFE_STEP}"""
    execution = f"""1. Read `PROJECT_RUNTIME.json`.
2. Confirm `{NEXT_SAFE_STEP}` is current.
3. Verify local and remote `main` synchronization.
4. Review `{A1_REL}`, `{A2_REL}` and `{ARTIFACT_REL}`.
5. Decide sample sufficiency without inventing missing data.
6. Preserve P0 queue-loss, timer-margin and correctness gates.
7. Define any extended read-only collection required.
8. Prepare A5 baseline report only after A4 consolidation.
9. Do not apply optimization before Gemini Red Team review."""
    text = replace_section(text, "## 02 CURRENT CONTINUATION CHECKPOINT", checkpoint)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", last_work)
    text = replace_section(text, "## 06 DO NOT REOPEN OR REPEAT", do_not)
    text = replace_section(text, "## 07 ALLOWED NEXT DECISIONS", decisions)
    text = replace_section(text, "## 08 NEXT SESSION EXECUTION RULE", execution)
    atomic_write_text(path, text)


def append_history(
    collected_at: str,
    head_before: str,
    result: str,
    findings: list[dict[str, str]],
) -> None:
    path = ROOT / "PROJECT_HISTORY.json"
    data = load_json(path)
    events = data.get("events")
    if not isinstance(events, list):
        raise RuntimeError("PROJECT_HISTORY_EVENTS_INVALID")
    event_id = "ERA55A3_NATURAL_CYCLE_BASELINE_COLLECTION_V1"
    if not any(isinstance(item, dict) and item.get("event_id") == event_id for item in events):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": collected_at,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "NATURAL_CYCLE_BASELINE_EVIDENCE_COLLECTED",
                "status": "CLOSED",
                "result": result,
                "head_before_commit": head_before,
                "artifact": ARTIFACT_REL,
                "report": REPORT_REL,
                "finding_codes": [item["code"] for item in findings],
                "live_runtime_db_service_timer_panel_mutation": False,
                "manual_runner_execution": False,
                "next_safe_step": NEXT_SAFE_STEP,
                "gemini_red_team_required": True,
            }
        )
    data["updated_at"] = collected_at
    data["updated_at_utc"] = collected_at
    atomic_write_json(path, data)


def append_almanac(result: str, findings: list[dict[str, str]]) -> None:
    path = ROOT / "04_ALMANAC.md"
    text = path.read_text(encoding="utf-8")
    heading = "## ERA55A_3 NATURAL CYCLE BASELINE COLLECTION"
    if heading in text:
        return
    marker = "\n---\n\n## ALMANAC RECORD INSERTION AND CORRECTION CONSTITUTION"
    if text.count(marker) != 1:
        raise RuntimeError("ALMANAC_INSERTION_MARKER_INVALID")
    codes = ", ".join(item["code"] for item in findings)
    entry = f"""
---

{heading}

- Status: `CLOSED`
- Result: `{result}`
- Historical runner evidence: collected from systemd journal.
- Queue top-50 and overflow evidence: independently reconstructed from display candidates.
- Natural timer-cycle observation: bounded external read-only observer.
- Manual runner execution: `false`
- Service/timer/DB/queue/panel mutation: `false`
- Finding codes: `{codes}`
- Optimization apply: `blocked`
- Gemini Red Team review: required after baseline report.
- Next safe step: `{NEXT_SAFE_STEP}`
"""
    atomic_write_text(path, text.replace(marker, entry + marker, 1))


def make_report(artifact: dict[str, Any]) -> str:
    findings = "\n".join(
        f"- **{item['priority']} {item['code']}** — {item['finding']}"
        for item in artifact["findings"]
    )
    return f"""# ERA55A_3 NATURAL CYCLE BASELINE COLLECTION

Result: `{artifact['result']}`

ERA55 status: `OPEN`

Live runtime/DB/service/timer/queue/panel mutation: `false`

## Historical Baseline

```json
{json.dumps(artifact['historical_baseline'], ensure_ascii=False, indent=2)}
```

## Silent Drop Investigation

```json
{json.dumps(artifact['silent_drop_investigation'], ensure_ascii=False, indent=2)}
```

Raw-to-hot anti-join is not treated as drop proof. The evidence source is the deterministic candidate pipeline: display candidates → authority filter → normalization → dedupe → priority sort → top 50 → overflow.

## Natural Timer Cycle

```json
{json.dumps(artifact['natural_cycle'], ensure_ascii=False, indent=2)}
```

## Findings

{findings}

## Decision

- Baseline evidence is recorded.
- No watchdog was applied.
- No index was added.
- No SQLite mode was changed.
- No queue policy was changed.
- No production burst test was run.
- Next: `{NEXT_SAFE_STEP}`.
"""


def visible_changes(expected_files: list[str]) -> None:
    expected = set(expected_files)
    visible_expected = expected - FORCE_ADD
    tracked = {
        line
        for line in git("diff", "--name-only").splitlines()
        if line.strip()
    }
    untracked = {
        line
        for line in git("ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    }
    actual = tracked | untracked
    if actual != visible_expected:
        raise RuntimeError(
            "UNEXPECTED_VISIBLE_CHANGED_FILES\n"
            + "EXPECTED="
            + json.dumps(sorted(visible_expected))
            + "\nACTUAL="
            + json.dumps(sorted(actual))
        )


def commit_and_push(expected_files: list[str]) -> tuple[str, str]:
    expected = sorted(set(expected_files))
    for rel in expected:
        if not (ROOT / rel).is_file():
            raise RuntimeError(f"EXPECTED_FILE_MISSING={rel}")
    visible_changes(expected)
    run(["git", "diff", "--check"])
    normal = sorted(set(expected) - FORCE_ADD)
    if normal:
        run(["git", "add", "--", *normal])
    forced = sorted(set(expected) & FORCE_ADD)
    if forced:
        run(["git", "add", "-f", "--", *forced])
    staged = sorted(
        line
        for line in git("diff", "--cached", "--name-only").splitlines()
        if line.strip()
    )
    if staged != expected:
        raise RuntimeError(
            "STAGED_FILES_MISMATCH\nEXPECTED="
            + json.dumps(expected)
            + "\nACTUAL="
            + json.dumps(staged)
        )
    git("commit", "-m", "ERA55A3_NATURAL_CYCLE_BASELINE | OK | READONLY_EVIDENCE")
    local_head = git("rev-parse", "HEAD")
    run(["git", "push", "origin", "main"], timeout=240)
    git("fetch", "origin", "main")
    remote_head = git("rev-parse", "origin/main")
    if local_head != remote_head:
        raise RuntimeError(f"POST_PUSH_HEAD_MISMATCH:LOCAL={local_head}:REMOTE={remote_head}")
    if git("status", "--porcelain"):
        raise RuntimeError("POST_PUSH_WORKTREE_NOT_CLEAN")
    return local_head, remote_head


def main() -> int:
    head_before, a2 = preconditions()
    backup_dir = Path(tempfile.mkdtemp(prefix="era55a3_backup_", dir="/tmp"))
    for rel in CANONICAL_FILES:
        source = ROOT / rel
        target = backup_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    committed = False
    try:
        collected_at = utc_now()
        a1 = load_json(ROOT / A1_REL)
        facts = a2.get("a1_facts") or {}
        timer_interval_seconds = int(facts.get("timer_cadence_seconds") or 1200)
        service_timeout_seconds = int(facts.get("timeout_start_seconds") or 70)

        historical = historical_baselines(timer_interval_seconds)
        silent_drop = queue_snapshot()
        natural = observe_next_natural_cycle(
            timer_interval_seconds,
            service_timeout_seconds,
        )
        result, findings = derive_result(historical, natural, silent_drop)

        artifact = {
            "schema_version": "1.0",
            "work_unit": WORK_UNIT,
            "era": "ERA55",
            "title": "Runtime Optimization",
            "collected_at_utc": collected_at,
            "status": "CLOSED_BASELINE_EVIDENCE_RECORDED",
            "result": result,
            "head_before_commit": head_before,
            "sources": {
                "a1": A1_REL,
                "a2": A2_REL,
            },
            "scope": {
                "historical_systemd_journal_read": True,
                "natural_timer_cycle_observation": True,
                "sqlite_mode_ro": True,
                "queue_reconstruction": True,
                "manual_runner_execution": False,
                "service_change": False,
                "timer_change": False,
                "database_mutation": False,
                "queue_policy_change": False,
                "panel_mutation": False,
                "production_burst_load": False,
                "optimization_apply": False,
            },
            "historical_baseline": historical,
            "silent_drop_investigation": silent_drop,
            "natural_cycle": natural,
            "findings": findings,
            "hard_gates": {
                "silent_event_loss_allowed": False,
                "data_correctness_regression_allowed": False,
                "optimization_apply_authorized": False,
                "production_burst_load_authorized": False,
                "manual_runner_execution_authorized": False,
            },
            "next_safe_step": NEXT_SAFE_STEP,
            "gemini_red_team_required": True,
            "a1_result": a1.get("result"),
            "a2_result": a2.get("result"),
        }

        atomic_write_json(ROOT / ARTIFACT_REL, artifact)
        atomic_write_text(ROOT / REPORT_REL, make_report(artifact))
        update_runtime(collected_at, result, findings)
        update_roadmap_json(collected_at, result)
        update_master(result, findings)
        update_handoff(result, findings)
        append_history(collected_at, head_before, result, findings)
        append_almanac(result, findings)

        for rel in (
            ARTIFACT_REL,
            "PROJECT_RUNTIME.json",
            "PROJECT_HISTORY.json",
            "data/tokenoskobi_v1_v8_master_era_roadmap.json",
        ):
            load_json(ROOT / rel)

        head_after, remote_after = commit_and_push(CANONICAL_FILES + GENERATED_FILES)
        committed = True

        print("ERA55A3_NATURAL_CYCLE_BASELINE=SUCCESS")
        print(f"RESULT={result}")
        print(f"HEAD_BEFORE={head_before}")
        print(f"CANONICAL_HEAD={head_after}")
        print(f"REMOTE_HEAD={remote_after}")
        print("ERA55_STATUS=OPEN")
        print(f"LAST_COMPLETED={WORK_UNIT}")
        print(f"NEXT_SAFE_STEP={NEXT_SAFE_STEP}")
        print(f"HISTORICAL_24H_CYCLES={historical['historical_24h']['cycle_count']}")
        print(f"HOT_STATE_12H_CYCLES={historical['hot_state_12h']['cycle_count']}")
        print(f"HISTORICAL_P95_MS={historical['historical_24h']['duration_ms']['p95']}")
        print(f"HISTORICAL_MAX_MS={historical['historical_24h']['duration_ms']['max']}")
        print(f"P95_SAFETY_MARGIN_MS={historical['p95_safety_margin_ms']}")
        print(f"MAX_SAFETY_MARGIN_MS={historical['max_safety_margin_ms']}")
        print(f"TIMER_OVERLAP_OBSERVED={str(historical['overlap_observed']).lower()}")
        print(f"SERVICE_TIMEOUT_OBSERVED={str(historical['timeout_observed']).lower()}")
        print(f"QUEUE_CANDIDATES={silent_drop['deduplicated_candidate_count']}")
        print(f"QUEUE_ADMITTED={silent_drop['admitted_count']}")
        print(f"QUEUE_OVERFLOW={silent_drop['overflow_count']}")
        print(f"QUEUE_CLASSIFICATION={silent_drop['classification']}")
        print(f"DROP_LEDGER_DETECTED={str(silent_drop['drop_ledger_detected']).lower()}")
        print(f"NATURAL_CYCLE_OBSERVED={str(natural.get('observed')).lower()}")
        print(f"NATURAL_RUNNER_MS={natural.get('runner_execution_ms')}")
        print(f"NATURAL_TIMER_MARGIN_MS={natural.get('timer_safety_margin_ms')}")
        print("LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false")
        print(f"ARTIFACT={ARTIFACT_REL}")
        print(f"REPORT={REPORT_REL}")
        print("GEMINI_RED_TEAM_REQUIRED=true")
        print("WORKTREE=CLEAN")
        print(f"BACKUP_DIR={backup_dir}")
        return 0
    except Exception:
        if not committed:
            run(["git", "reset", "--mixed", "HEAD"], check=False)
            for rel in CANONICAL_FILES:
                backup = backup_dir / rel
                target = ROOT / rel
                if backup.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup, target)
            for rel in GENERATED_FILES:
                target = ROOT / rel
                if target.exists():
                    target.unlink()
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERA55A3_NATURAL_CYCLE_BASELINE=FAILED:{exc}", file=sys.stderr)
        raise
