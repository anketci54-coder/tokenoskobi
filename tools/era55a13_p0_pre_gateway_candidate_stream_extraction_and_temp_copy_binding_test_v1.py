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
sys.dont_write_bytecode = True
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
EXPECTED_HEAD = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()

A12_ARTIFACT = ROOT / "data/control/era55a12_p0_runtime_ledger_writer_post_test_audit_and_bounded_canary_decision_v1.json"
EXTRACTOR = ROOT / "tools/news_pre_gateway_candidate_stream_v1.py"
WRITER = ROOT / "tools/news_disposition_ledger_writer_v1.py"
RECOVERY_GUARD = ROOT / "tools/news_ledger_recovery_guard_v1.py"
MARKET_JSONL = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADVERSARIAL_JSONL = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
DISPLAY_PROJECTION = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
HOT_SEED = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
PROD_RECOVERY_STATE = ROOT / "runtime/state/news_ledger_recovery_state_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

ARTIFACT = ROOT / "data/control/era55a13_p0_pre_gateway_candidate_stream_extraction_and_temp_copy_binding_test_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A13_P0_PRE_GATEWAY_CANDIDATE_STREAM_EXTRACTION_AND_TEMP_COPY_BINDING_TEST.md"
RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

NEXT_STEP = "ERA55A_14_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION"
COMMIT_SUBJECT = "ERA55A13_PRE_GATEWAY_STREAM_TEMP_COPY | OK | PRODUCTION_UNBOUND"

EXTRACTOR_SOURCE = r"""#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

SCHEMA_VERSION = "1.0"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_authority(obj: Dict[str, Any], expected_lane: str) -> Dict[str, Any]:
    lane_ok = obj.get("lane") == expected_lane
    db_write = obj.get("db_match_write")
    hunter = obj.get("hunter_authorized")
    trade = obj.get("trade_signal")
    paper = obj.get("paper_signal")

    if not lane_ok:
        db_write = True

    return {
        "db_write": db_write,
        "hunter_authorized": hunter,
        "trade_signal": trade,
        "paper_signal": paper,
        "live_trade": False,
        "execution_authority": False,
    }


def _convert_object(
    obj: Dict[str, Any],
    *,
    expected_lane: str,
    source_path: Path,
    line_number: int,
    raw_line: str,
) -> Dict[str, Any]:
    return {
        "event_uid": obj.get("event_uid"),
        "news_uid": obj.get("news_uid"),
        "title": obj.get("title"),
        "hits": obj.get("hits") if isinstance(obj.get("hits"), list) else [],
        "published_at_utc": obj.get("published_at_utc"),
        "source_uid": obj.get("source_uid"),
        "authority": _safe_authority(obj, expected_lane),
        "_pre_gateway": {
            "source_path": str(source_path),
            "line_number": line_number,
            "expected_lane": expected_lane,
            "observed_lane": obj.get("lane"),
            "raw_line_sha256": sha256_text(raw_line),
        },
    }


def read_lane_observations(
    path: Path,
    *,
    section_id: str,
    expected_lane: str,
) -> Dict[str, Any]:
    items: list[Any] = []
    physical_lines = 0
    nonempty_lines = 0
    blank_lines = 0
    parsed_object_rows = 0
    parsed_nonobject_rows = 0
    parse_error_rows = 0
    unsafe_rows = 0

    with path.open("rb") as handle:
        for line_number, physical in enumerate(handle, start=1):
            physical_lines += 1
            raw_bytes = physical.rstrip(b"\r\n")
            if not raw_bytes.strip():
                blank_lines += 1
                continue
            nonempty_lines += 1

            try:
                raw_line = raw_bytes.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                parse_error_rows += 1
                items.append(
                    "PRE_GATEWAY_UTF8_ERROR|"
                    f"path={path}|line={line_number}|"
                    f"error={type(exc).__name__}|"
                    f"raw_sha256={hashlib.sha256(raw_bytes).hexdigest()}|"
                    f"raw_hex_preview={raw_bytes[:256].hex()}"
                )
                continue

            try:
                value = json.loads(raw_line)
            except Exception as exc:
                parse_error_rows += 1
                items.append(
                    "PRE_GATEWAY_PARSE_ERROR|"
                    f"path={path}|line={line_number}|"
                    f"error={type(exc).__name__}|"
                    f"raw_sha256={sha256_text(raw_line)}|"
                    f"preview={raw_line[:512]}"
                )
                continue

            if not isinstance(value, dict):
                parsed_nonobject_rows += 1
                items.append(
                    "PRE_GATEWAY_NONOBJECT|"
                    f"path={path}|line={line_number}|"
                    f"type={type(value).__name__}|"
                    f"raw_sha256={sha256_text(raw_line)}|"
                    f"preview={raw_line[:512]}"
                )
                continue

            parsed_object_rows += 1
            converted = _convert_object(
                value,
                expected_lane=expected_lane,
                source_path=path,
                line_number=line_number,
                raw_line=raw_line,
            )
            authority = converted["authority"]
            if not all(
                authority.get(key) is False
                for key in (
                    "db_write",
                    "hunter_authorized",
                    "trade_signal",
                    "paper_signal",
                )
            ):
                unsafe_rows += 1
            items.append(converted)

    return {
        "section": {
            "id": section_id,
            "title": section_id,
            "count": nonempty_lines,
            "items": items,
        },
        "stats": {
            "path": str(path),
            "expected_lane": expected_lane,
            "physical_lines": physical_lines,
            "nonempty_lines": nonempty_lines,
            "blank_lines": blank_lines,
            "parsed_object_rows": parsed_object_rows,
            "parsed_nonobject_rows": parsed_nonobject_rows,
            "parse_error_rows": parse_error_rows,
            "unsafe_rows": unsafe_rows,
        },
    }


def build_candidate_display(
    market_path: Path,
    adversarial_path: Path,
) -> Dict[str, Any]:
    lane_specs = (
        (market_path, "news_market_indicator", "MARKET_INDICATOR"),
        (
            adversarial_path,
            "news_adversarial_intelligence",
            "ADVERSARIAL_NEWS",
        ),
    )
    sections: list[Dict[str, Any]] = []
    stats: list[Dict[str, Any]] = []

    for path, section_id, expected_lane in lane_specs:
        lane = read_lane_observations(
            path,
            section_id=section_id,
            expected_lane=expected_lane,
        )
        sections.append(lane["section"])
        stats.append(lane["stats"])

    total_nonempty = sum(int(row["nonempty_lines"]) for row in stats)
    total_parse_errors = sum(int(row["parse_error_rows"]) for row in stats)
    total_nonobjects = sum(int(row["parsed_nonobject_rows"]) for row in stats)
    total_unsafe = sum(int(row["unsafe_rows"]) for row in stats)

    return {
        "schema_version": SCHEMA_VERSION,
        "adapter": "NEWS_PRE_GATEWAY_CANDIDATE_STREAM_V1",
        "authority": {
            "db_write": False,
            "db_schema_change": False,
            "hunter_authorized": False,
            "trade_signal": False,
            "paper_signal": False,
            "live_trade": False,
            "execution_authority": False,
        },
        "health": {
            "source_authority_ok": True,
            "parse_errors": total_parse_errors,
            "nonobject_rows": total_nonobjects,
            "unsafe_rows": total_unsafe,
        },
        "extraction": {
            "lane_stats": stats,
            "source_candidate_count": total_nonempty,
            "physical_nonempty_line_accounting": True,
        },
        "sections": sections,
    }


def write_candidate_display(
    market_path: Path,
    adversarial_path: Path,
    output_path: Path,
) -> Dict[str, Any]:
    payload = build_candidate_display(market_path, adversarial_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return payload
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_guard(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    st = path.stat()
    return {
        "exists": True,
        "sha256": sha256_file(path),
        "size_bytes": st.st_size,
        "mtime_ns": st.st_mtime_ns,
    }


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


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_SPEC_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def backup_sqlite(source: Path, target: Path) -> None:
    source_conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target_conn = sqlite3.connect(target)
    try:
        source_conn.backup(target_conn)
    finally:
        target_conn.close()
        source_conn.close()


def production_db_state() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        return {
            "batch_rows": int(
                conn.execute(
                    "SELECT COUNT(*) FROM news_disposition_batches_v2"
                ).fetchone()[0]
            ),
            "ledger_rows": int(
                conn.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2"
                ).fetchone()[0]
            ),
            "integrity_check": str(
                conn.execute("PRAGMA integrity_check").fetchone()[0]
            ),
            "quick_check": str(
                conn.execute("PRAGMA quick_check").fetchone()[0]
            ),
            "foreign_key_check_rows": len(
                conn.execute("PRAGMA foreign_key_check").fetchall()
            ),
            "query_only": bool(
                conn.execute("PRAGMA query_only").fetchone()[0]
            ),
        }
    finally:
        conn.close()


def service_environment() -> dict[str, Any]:
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
    text = result.stdout
    return {
        "rc": result.returncode,
        "stdout": text.strip(),
        "writer_enabled_explicitly": (
            "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text
        ),
        "runner_lock_enabled_explicitly": (
            "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text
        ),
    }


def choose_temp_root() -> dict[str, Any]:
    required = DB.stat().st_size * 8 + 256 * 1024 * 1024
    shm = Path("/dev/shm")
    if shm.is_dir() and shutil.disk_usage(shm).free >= required:
        return {
            "root": shm,
            "mode": "TMPFS_CAPACITY_PROVEN",
            "required_bytes": required,
            "free_bytes": shutil.disk_usage(shm).free,
        }
    tmp = Path("/tmp")
    return {
        "root": tmp,
        "mode": "DISK_TEMP_FALLBACK",
        "required_bytes": required,
        "free_bytes": shutil.disk_usage(tmp).free,
    }


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(
        rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND:{heading}")
    return (
        text[: match.start()]
        + heading
        + "\n\n"
        + body.rstrip()
        + "\n"
        + text[match.end() :]
    )


def validate_a12(value: dict[str, Any]) -> None:
    assert value["status"] == "CLOSED_BOUNDED_CANARY_REJECTED"
    assert value["result"] == (
        "REJECT_BOUNDED_CANARY_SOURCE_ALREADY_FILTERED_AND_TRUNCATED"
    )
    assert value["authorization"]["bounded_canary_authorized"] is False
    assert value["critical_finding"]["classification"] == (
        "BOUND_SOURCE_IS_POST_FILTER_POST_DEDUP_POST_TRUNCATION"
    )
    assert value["production_unchanged"] is True


def count_display_items(display: dict[str, Any]) -> int:
    total = 0
    for section in display.get("sections") or []:
        if not isinstance(section, dict):
            continue
        if section.get("id") not in {
            "news_market_indicator",
            "news_adversarial_intelligence",
        }:
            continue
        items = section.get("items")
        if isinstance(items, list):
            total += len(items)
    return total


def build_synthetic_files(temp_dir: Path) -> tuple[Path, Path]:
    market = temp_dir / "synthetic_market.jsonl"
    adversarial = temp_dir / "synthetic_adversarial.jsonl"

    rows = [
        {
            "event_uid": "event_unique_a",
            "news_uid": "news_unique_a",
            "title": "Unique A",
            "hits": ["BTC"],
            "published_at_utc": "2026-07-11T00:00:00+00:00",
            "source_uid": "synthetic",
            "lane": "MARKET_INDICATOR",
            "hunter_authorized": False,
            "db_match_write": False,
            "trade_signal": False,
            "paper_signal": False,
        },
        {
            "event_uid": "event_replace",
            "news_uid": "news_replace",
            "title": "Replacement candidate",
            "hits": [],
            "published_at_utc": "2026-07-11T00:00:00+00:00",
            "source_uid": "synthetic",
            "lane": "MARKET_INDICATOR",
            "hunter_authorized": False,
            "db_match_write": False,
            "trade_signal": False,
            "paper_signal": False,
        },
        {
            "event_uid": "event_replace",
            "news_uid": "news_replace",
            "title": "Replacement candidate",
            "hits": ["BTC", "ETH"],
            "published_at_utc": "2026-07-11T00:00:00+00:00",
            "source_uid": "synthetic",
            "lane": "MARKET_INDICATOR",
            "hunter_authorized": False,
            "db_match_write": False,
            "trade_signal": False,
            "paper_signal": False,
        },
        {
            "event_uid": "event_duplicate",
            "news_uid": "news_duplicate",
            "title": "Equal duplicate",
            "hits": ["BTC"],
            "published_at_utc": "2026-07-11T00:00:00+00:00",
            "source_uid": "synthetic",
            "lane": "MARKET_INDICATOR",
            "hunter_authorized": False,
            "db_match_write": False,
            "trade_signal": False,
            "paper_signal": False,
        },
        {
            "event_uid": "event_duplicate",
            "news_uid": "news_duplicate",
            "title": "Equal duplicate",
            "hits": ["BTC"],
            "published_at_utc": "2026-07-11T00:00:00+00:00",
            "source_uid": "synthetic",
            "lane": "MARKET_INDICATOR",
            "hunter_authorized": False,
            "db_match_write": False,
            "trade_signal": False,
            "paper_signal": False,
        },
        {
            "event_uid": "event_unsafe",
            "news_uid": "news_unsafe",
            "title": "Unsafe candidate",
            "hits": ["BTC"],
            "published_at_utc": "2026-07-11T00:00:00+00:00",
            "source_uid": "synthetic",
            "lane": "WRONG_LANE",
            "hunter_authorized": False,
            "db_match_write": False,
            "trade_signal": False,
            "paper_signal": False,
        },
    ]

    with market.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            )
        handle.write("{invalid-json\n")

    adv_row = {
        "event_uid": "event_unique_b",
        "news_uid": "news_unique_b",
        "title": "Unique B",
        "hits": ["bridge"],
        "published_at_utc": "2026-07-11T00:00:00+00:00",
        "source_uid": "synthetic",
        "lane": "ADVERSARIAL_NEWS",
        "hunter_authorized": False,
        "db_match_write": False,
        "trade_signal": False,
        "paper_signal": False,
    }
    adversarial.write_text(
        json.dumps(adv_row, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return market, adversarial


def db_batch_metrics(db_path: Path, batch_uid: str) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        batch = conn.execute(
            """
            SELECT rowid AS batch_sequence, *
            FROM news_disposition_batches_v2
            WHERE batch_uid=?
            """,
            (batch_uid,),
        ).fetchone()
        if batch is None:
            raise RuntimeError("BATCH_NOT_FOUND")
        ledger_rows = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM news_disposition_ledger_v2
                WHERE batch_uid=?
                """,
                (batch_uid,),
            ).fetchone()[0]
        )
        dispositions = {
            str(row[0]): int(row[1])
            for row in conn.execute(
                """
                SELECT disposition, COUNT(*)
                FROM news_disposition_ledger_v2
                WHERE batch_uid=?
                GROUP BY disposition
                """,
                (batch_uid,),
            ).fetchall()
        }
        return {
            "batch_sequence": int(batch[0]),
            "ledger_rows": ledger_rows,
            "disposition_counts": dispositions,
            "integrity_check": str(
                conn.execute("PRAGMA integrity_check").fetchone()[0]
            ),
            "quick_check": str(
                conn.execute("PRAGMA quick_check").fetchone()[0]
            ),
            "foreign_key_check_rows": len(
                conn.execute("PRAGMA foreign_key_check").fetchall()
            ),
        }
    finally:
        conn.close()


def main() -> int:
    if not EXPECTED_HEAD:
        raise RuntimeError("TOKENOSKOBI_EXPECTED_HEAD_REQUIRED")
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BRANCH_NOT_MAIN")
    if git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError(
            "UNEXPECTED_HEAD expected="
            + EXPECTED_HEAD
            + " actual="
            + git("rev-parse", "HEAD")
        )
    if git("status", "--porcelain"):
        raise RuntimeError("WORKTREE_NOT_CLEAN")

    for path in (
        A12_ARTIFACT,
        WRITER,
        RECOVERY_GUARD,
        MARKET_JSONL,
        ADVERSARIAL_JSONL,
        DISPLAY_PROJECTION,
        SUMMARY,
        HOT_SEED,
        DB,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    validate_a12(load_json(A12_ARTIFACT))

    production_guard_before = {
        "database_file": file_guard(DB),
        "market_jsonl": file_guard(MARKET_JSONL),
        "adversarial_jsonl": file_guard(ADVERSARIAL_JSONL),
        "display_projection": file_guard(DISPLAY_PROJECTION),
        "hot_output": file_guard(HOT_SEED),
        "recovery_state": file_guard(PROD_RECOVERY_STATE),
        "database_state": production_db_state(),
        "service_environment": service_environment(),
    }

    EXTRACTOR.write_text(EXTRACTOR_SOURCE, encoding="utf-8")
    EXTRACTOR.chmod(0o755)
    compile(EXTRACTOR_SOURCE, str(EXTRACTOR), "exec")

    extractor = import_module(
        "news_pre_gateway_candidate_stream_v1_a13",
        EXTRACTOR,
    )
    writer = import_module(
        "news_disposition_ledger_writer_v1_a13",
        WRITER,
    )
    recovery = import_module(
        "news_ledger_recovery_guard_v1_a13",
        RECOVERY_GUARD,
    )

    temp_choice = choose_temp_root()
    temp_dir = Path(
        tempfile.mkdtemp(
            prefix="era55a13_",
            dir=str(temp_choice["root"]),
        )
    )

    try:
        real_display_path = temp_dir / "pre_gateway_candidate_display.json"
        real_display = extractor.write_candidate_display(
            MARKET_JSONL,
            ADVERSARIAL_JSONL,
            real_display_path,
        )
        real_plan = writer.build_plan(real_display, queue_capacity=50)

        extraction_count = int(
            real_display["extraction"]["source_candidate_count"]
        )
        projection_count = count_display_items(
            load_json(DISPLAY_PROJECTION)
        )

        assert extraction_count > 0
        assert real_plan["counts"]["source_candidate_count"] == extraction_count
        assert extraction_count > projection_count
        assert projection_count == 50

        real_counts = real_plan["counts"]
        assert extraction_count == sum(
            int(real_counts[key])
            for key in (
                "admitted_count",
                "overflow_count",
                "duplicate_removed_count",
                "unsafe_filtered_count",
                "invalid_candidate_count",
                "replaced_count",
            )
        )
        assert real_counts["normalized_candidate_count"] == (
            real_counts["deduplicated_candidate_count"]
            + real_counts["duplicate_removed_count"]
        )
        assert real_counts["deduplicated_candidate_count"] == (
            real_counts["admitted_count"]
            + real_counts["overflow_count"]
            + real_counts["replaced_count"]
        )

        temp_db = temp_dir / "real.sqlite"
        backup_sqlite(DB, temp_db)
        temp_output = temp_dir / "hot_output.json"
        temp_state = temp_dir / "recovery_state.json"
        temp_lock = temp_dir / "writer.lock"

        first = writer.write_and_publish(
            display_path=real_display_path,
            summary_path=SUMMARY,
            db_path=temp_db,
            output_path=temp_output,
            recovery_state_path=temp_state,
            contract_seed_path=HOT_SEED,
            queue_capacity=50,
            lock_path=temp_lock,
        )
        first_hash = sha256_file(temp_output)
        first_metrics = db_batch_metrics(temp_db, real_plan["batch_uid"])

        second = writer.write_and_publish(
            display_path=real_display_path,
            summary_path=SUMMARY,
            db_path=temp_db,
            output_path=temp_output,
            recovery_state_path=temp_state,
            contract_seed_path=HOT_SEED,
            queue_capacity=50,
            lock_path=temp_lock,
        )
        second_hash = sha256_file(temp_output)

        assert first["write_result"]["status"] == "COMMITTED"
        assert second["write_result"]["status"] == "IDEMPOTENT_REPLAY_NOOP"
        assert first_hash == second_hash
        assert first_metrics["ledger_rows"] == extraction_count
        assert first_metrics["integrity_check"] == "ok"
        assert first_metrics["quick_check"] == "ok"
        assert first_metrics["foreign_key_check_rows"] == 0

        output_payload = load_json(temp_output)
        output_queue = output_payload.get("hot_queue")
        assert isinstance(output_queue, list)
        assert len(output_queue) == len(real_plan["hot_queue"])
        assert [
            row.get("hot_uid") for row in output_queue
        ] == [
            row.get("hot_uid") for row in real_plan["hot_queue"]
        ]

        temp_output.unlink()
        recovered = recovery.recover_committed_batch(
            temp_db,
            temp_output,
            temp_state,
            contract_seed_path=HOT_SEED,
            batch_sequence=int(first["batch_sequence"]),
        )
        recovered_payload = load_json(temp_output)
        recovered_queue = recovered_payload.get("hot_queue")
        assert recovered["status"] == "RECOVERED"
        assert isinstance(recovered_queue, list)
        assert [
            row.get("hot_uid") for row in recovered_queue
        ] == [
            row.get("hot_uid") for row in real_plan["hot_queue"]
        ]

        rollback_db = temp_dir / "rollback.sqlite"
        backup_sqlite(DB, rollback_db)
        injected_error = None
        try:
            writer.write_plan(
                rollback_db,
                real_plan,
                inject_failure_after_ledger_rows=True,
            )
        except RuntimeError as exc:
            injected_error = str(exc)
        assert injected_error == "INJECTED_FAILURE_AFTER_LEDGER_ROWS"

        rollback_conn = sqlite3.connect(
            f"file:{rollback_db}?mode=ro",
            uri=True,
        )
        try:
            rollback_batch_rows = int(
                rollback_conn.execute(
                    "SELECT COUNT(*) FROM news_disposition_batches_v2"
                ).fetchone()[0]
            )
            rollback_ledger_rows = int(
                rollback_conn.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2"
                ).fetchone()[0]
            )
        finally:
            rollback_conn.close()
        assert rollback_batch_rows == 0
        assert rollback_ledger_rows == 0

        synth_market, synth_adv = build_synthetic_files(temp_dir)
        synth_display = extractor.build_candidate_display(
            synth_market,
            synth_adv,
        )
        synth_plan = writer.build_plan(synth_display, queue_capacity=50)
        expected_synth_counts = {
            "source_candidate_count": 8,
            "normalized_candidate_count": 6,
            "deduplicated_candidate_count": 5,
            "admitted_count": 4,
            "overflow_count": 0,
            "duplicate_removed_count": 1,
            "unsafe_filtered_count": 1,
            "invalid_candidate_count": 1,
            "replaced_count": 1,
        }
        assert synth_plan["counts"] == expected_synth_counts

        production_guard_after = {
            "database_file": file_guard(DB),
            "market_jsonl": file_guard(MARKET_JSONL),
            "adversarial_jsonl": file_guard(ADVERSARIAL_JSONL),
            "display_projection": file_guard(DISPLAY_PROJECTION),
            "hot_output": file_guard(HOT_SEED),
            "recovery_state": file_guard(PROD_RECOVERY_STATE),
            "database_state": production_db_state(),
            "service_environment": service_environment(),
        }
        assert production_guard_before == production_guard_after

        now = utc_now()
        artifact = {
            "schema_version": "1.0",
            "work_unit": (
                "ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_"
                "EXTRACTION_AND_TEMP_COPY_BINDING_TEST"
            ),
            "tested_at_utc": now,
            "status": "CLOSED_TEMP_COPY_BINDING_OK",
            "result": (
                "OK_COMPLETE_PRE_GATEWAY_JSONL_STREAM_"
                "TEMP_COPY_BOUND"
            ),
            "extractor_module": {
                "path": str(EXTRACTOR.relative_to(ROOT)),
                "sha256": sha256_file(EXTRACTOR),
                "production_runtime_bound": False,
                "physical_nonempty_line_accounting": True,
            },
            "real_pre_gateway_stream": {
                "market_jsonl": str(MARKET_JSONL),
                "adversarial_jsonl": str(ADVERSARIAL_JSONL),
                "lane_stats": real_display["extraction"]["lane_stats"],
                "source_candidate_count": extraction_count,
                "display_projection_count": projection_count,
                "source_exceeds_display_projection": (
                    extraction_count > projection_count
                ),
                "counts": real_counts,
                "accounted_count": sum(
                    int(real_counts[key])
                    for key in (
                        "admitted_count",
                        "overflow_count",
                        "duplicate_removed_count",
                        "unsafe_filtered_count",
                        "invalid_candidate_count",
                        "replaced_count",
                    )
                ),
                "unobservable_rows": 0,
                "ledger_rows": first_metrics["ledger_rows"],
                "queue_count": len(real_plan["hot_queue"]),
                "queue_parity": True,
                "disposition_counts": first_metrics[
                    "disposition_counts"
                ],
            },
            "idempotency": {
                "first_write_status": first["write_result"]["status"],
                "second_write_status": second["write_result"]["status"],
                "batch_rows_after_replay": 1,
                "ledger_rows_after_replay": first_metrics["ledger_rows"],
                "output_hash_unchanged": first_hash == second_hash,
            },
            "postcommit_publish_recovery": {
                "status": recovered["status"],
                "queue_parity": True,
                "db_rewrite": False,
            },
            "transaction_rollback": {
                "injected_error": injected_error,
                "batch_rows_after_rollback": rollback_batch_rows,
                "ledger_rows_after_rollback": rollback_ledger_rows,
                "ok": True,
            },
            "synthetic_extractor_disposition_model": {
                "expected_counts": expected_synth_counts,
                "actual_counts": synth_plan["counts"],
                "exact_match": True,
                "parse_error_preserved": True,
                "unsafe_preserved": True,
                "duplicate_preserved": True,
                "replacement_preserved": True,
            },
            "production_guard_before": production_guard_before,
            "production_guard_after": production_guard_after,
            "production_unchanged": True,
            "authorization": {
                "bounded_canary_authorized": False,
                "production_writer_activation_authorized": False,
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
                    "# ERA55A13 Pre-Gateway Candidate Stream Temp-Copy Binding",
                    "",
                    "- Status: `CLOSED_TEMP_COPY_BINDING_OK`",
                    "- Result: `OK_COMPLETE_PRE_GATEWAY_JSONL_STREAM_TEMP_COPY_BOUND`",
                    f"- Real pre-gateway candidates: `{extraction_count}`",
                    f"- Display projection candidates: `{projection_count}`",
                    "- Physical non-empty line accounting: `true`",
                    "- Unobservable rows: `0`",
                    "- Queue parity: `true`",
                    "- Idempotent replay: `true`",
                    "- Post-commit publish recovery: `true`",
                    "- Transaction rollback: `true`",
                    "- Production runtime bound: `false`",
                    "- Production unchanged: `true`",
                    "- Bounded canary authorized: `false`",
                    f"- Next safe step: `{NEXT_STEP}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        runtime = load_json(RUNTIME)
        state = runtime["current_state"]
        state["mode"] = (
            "ERA55A13_PRE_GATEWAY_STREAM_TEMP_COPY_BINDING_OK"
        )
        state["runtime_status"] = "WORK_UNIT_CLOSED"
        state["updated_at"] = now
        state["last_action"] = {
            "timestamp": now,
            "task": (
                "ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_"
                "EXTRACTION_AND_TEMP_COPY_BINDING_TEST"
            ),
            "result": artifact["result"],
            "artifact": str(ARTIFACT.relative_to(ROOT)),
        }
        state["active_work_unit"] = {
            "id": (
                "ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_"
                "EXTRACTION_AND_TEMP_COPY_BINDING_TEST"
            ),
            "type": (
                "ERA55_P0_PRE_GATEWAY_CANDIDATE_STREAM_"
                "TEMP_COPY_BINDING_TEST"
            ),
            "parent": "ERA55_RUNTIME_OPTIMIZATION",
            "artifact": str(ARTIFACT.relative_to(ROOT)),
            "status": "CLOSED_TEMP_COPY_BINDING_OK",
            "result": artifact["result"],
            "production_mutation": False,
            "next_step": NEXT_STEP,
        }
        state["next_safe_step"] = {
            "id": NEXT_STEP,
            "type": (
                "ERA55_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_"
                "BOUNDED_CANARY_DECISION"
            ),
            "parent": "ERA55_RUNTIME_OPTIMIZATION",
            "purpose": (
                "Independently audit complete JSONL accounting and decide "
                "whether a single-cycle bounded canary may be authorized."
            ),
            "human_authorization_required": True,
            "production_writer_activation_authorized": False,
            "bounded_canary_authorized": False,
            "option_b_authorized": False,
            "optimization_apply_authorized": False,
            "status": "READY",
        }
        state["current_problem"] = {
            "code": (
                "PRE_GATEWAY_WRITER_NOT_PRODUCTION_BOUND_"
                "CANARY_DECISION_PENDING"
            ),
            "severity": "P0",
            "evidence": str(ARTIFACT.relative_to(ROOT)),
        }
        runtime["current_work_unit"] = state["active_work_unit"]
        write_json(RUNTIME, runtime)

        history = load_json(HISTORY)
        events = history.setdefault("events", [])
        event_id = "ERA55A13_PRE_GATEWAY_STREAM_TEMP_COPY_BINDING_V1"
        if not any(
            isinstance(event, dict)
            and event.get("event_id") == event_id
            for event in events
        ):
            events.append(
                {
                    "event_id": event_id,
                    "timestamp_utc": now,
                    "era": "ERA55",
                    "work_unit": (
                        "ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_"
                        "EXTRACTION_AND_TEMP_COPY_BINDING_TEST"
                    ),
                    "event": "TEMP_COPY_BINDING_TEST",
                    "status": "CLOSED_TEMP_COPY_BINDING_OK",
                    "result": artifact["result"],
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "source_candidate_count": extraction_count,
                    "display_projection_count": projection_count,
                    "unobservable_rows": 0,
                    "production_unchanged": True,
                    "bounded_canary_authorized": False,
                    "p0_f1_closed": False,
                    "next_safe_step": NEXT_STEP,
                }
            )
        history["updated_at"] = now
        history["updated_at_utc"] = now
        write_json(HISTORY, history)

        master = MASTER.read_text(encoding="utf-8")
        master = replace_section(
            master,
            "## 01 PROJECT STATUS",
            """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_P0_PRE_GATEWAY_WRITER_CANARY_DECISION_PENDING
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
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_PRE_GATEWAY_WRITER
LAST_COMPLETED_SUBSTEP=ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_EXTRACTION_AND_TEMP_COPY_BINDING_TEST
PRE_GATEWAY_JSONL_STREAM_EXTRACTED=true
PHYSICAL_NONEMPTY_LINE_ACCOUNTING=true
REAL_SOURCE_CANDIDATES={extraction_count}
DISPLAY_PROJECTION_CANDIDATES={projection_count}
UNOBSERVABLE_ROWS=0
QUEUE_PARITY=true
PRODUCTION_LEDGER_WRITER_ACTIVE=false
BOUNDED_CANARY_AUTHORIZED=false
PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
```

The complete pre-gateway JSONL stream is now proven on a disposable database copy. Production remains unbound pending A14 independent audit and canary decision.""",
        )
        master = replace_section(
            master,
            "## 03 LAST VERIFIED WORK",
            f"""```text
LAST_COMPLETED=ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_EXTRACTION_AND_TEMP_COPY_BINDING_TEST
LAST_RESULT={artifact["result"]}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS=CLOSED_TEMP_COPY_BINDING_OK
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
```

NEXT_SAFE_STEP={NEXT_STEP}""",
        )
        MASTER.write_text(master, encoding="utf-8")

        handoff = HANDOFF.read_text(encoding="utf-8")
        handoff = replace_section(
            handoff,
            "## 02 CURRENT CONTINUATION CHECKPOINT",
            f"""PROJECT_STATUS=ACTIVE_ERA55_P0_PRE_GATEWAY_WRITER_CANARY_DECISION_PENDING
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_PRE_GATEWAY_WRITER
LAST_COMPLETED_SUBSTEP=ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_EXTRACTION_AND_TEMP_COPY_BINDING_TEST
PRE_GATEWAY_JSONL_STREAM_EXTRACTED=true
PHYSICAL_NONEMPTY_LINE_ACCOUNTING=true
REAL_SOURCE_CANDIDATES={extraction_count}
DISPLAY_PROJECTION_CANDIDATES={projection_count}
UNOBSERVABLE_ROWS=0
QUEUE_PARITY=true
PRODUCTION_LEDGER_WRITER_ACTIVE=false
BOUNDED_CANARY_AUTHORIZED=false
PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A13 completed on a disposable database copy. Only A14 independent audit and bounded-canary decision is authorized next.""",
        )
        handoff = replace_section(
            handoff,
            "## 03 LAST VERIFIED WORK",
            f"""LAST_COMPLETED=ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_EXTRACTION_AND_TEMP_COPY_BINDING_TEST
LAST_RESULT={artifact["result"]}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS=CLOSED_TEMP_COPY_BINDING_OK
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=PRE_GATEWAY_WRITER_NOT_PRODUCTION_BOUND_CANARY_DECISION_PENDING""",
        )
        handoff = replace_section(
            handoff,
            "## 06 DO NOT REOPEN OR REPEAT",
            """- Do not rerun A9-A13 unless evidence is invalidated.
- Do not fall back to the 25+25 display projection as the writer source.
- Do not enable production writer or runner-lock flags before A14 decision.
- Do not modify live DB, service, timer, gateway or panel from A13 evidence alone.
- Do not start Option B or mark P0 F1 closed.""",
        )
        handoff = replace_section(
            handoff,
            "## 07 ALLOWED NEXT DECISIONS",
            f"""- Writer module: `VALIDATED`.
- Complete pre-gateway JSONL extraction: `VALIDATED_TEMP_COPY`.
- Physical non-empty line accounting: `VALIDATED`.
- Zero unobservable rows: `VALIDATED_TEMP_COPY`.
- Bounded canary: `PENDING_A14_DECISION`.
- Production activation: `BLOCKED`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT_STEP}""",
        )
        handoff = replace_section(
            handoff,
            "## 08 NEXT SESSION EXECUTION RULE",
            """1. Confirm A14 is current.
2. Independently audit the A13 extractor and artifact.
3. Reconcile physical JSONL line counts, ledger counts and output queue.
4. Verify production guards and feature flags remain unchanged.
5. Decide only whether one bounded natural-cycle canary may be authorized.
6. Do not close P0 F1 or authorize general production from temp-copy evidence.""",
        )
        HANDOFF.write_text(handoff, encoding="utf-8")

        almanac = ALMANAC.read_text(encoding="utf-8")
        marker = "## ERA55A_13 PRE-GATEWAY STREAM TEMP-COPY BINDING"
        if marker not in almanac:
            ALMANAC.write_text(
                almanac.rstrip()
                + f"""

---

{marker}

- Status: `CLOSED_TEMP_COPY_BINDING_OK`
- Result: `{artifact["result"]}`
- Real pre-gateway candidates: `{extraction_count}`
- Display projection candidates: `{projection_count}`
- Physical non-empty line accounting: `true`
- Unobservable rows: `0`
- Queue parity: `true`
- Production mutation: `false`
- Bounded canary authorized: `false`
- Production writer activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `{NEXT_STEP}`
"""
                + "\n",
                encoding="utf-8",
            )

        final_runtime_guard = {
            "database_file": file_guard(DB),
            "market_jsonl": file_guard(MARKET_JSONL),
            "adversarial_jsonl": file_guard(ADVERSARIAL_JSONL),
            "display_projection": file_guard(DISPLAY_PROJECTION),
            "hot_output": file_guard(HOT_SEED),
            "recovery_state": file_guard(PROD_RECOVERY_STATE),
            "database_state": production_db_state(),
            "service_environment": service_environment(),
        }
        assert production_guard_before == final_runtime_guard

        git(
            "add",
            str(EXTRACTOR.relative_to(ROOT)),
            str(ARTIFACT.relative_to(ROOT)),
            str(RUNTIME.relative_to(ROOT)),
            str(HISTORY.relative_to(ROOT)),
            str(MASTER.relative_to(ROOT)),
            str(HANDOFF.relative_to(ROOT)),
            str(ALMANAC.relative_to(ROOT)),
        )
        subprocess.run(
            ["git", "add", "-f", str(REPORT.relative_to(ROOT))],
            cwd=ROOT,
            check=True,
        )
        if not git("diff", "--cached", "--name-only"):
            raise RuntimeError("NO_STAGED_CHANGES")
        git("commit", "-m", COMMIT_SUBJECT)

        print("ERA55A13_PRE_GATEWAY_STREAM_TEMP_COPY=SUCCESS")
        print("RESULT=" + artifact["result"])
        print("EXTRACTOR_MODULE_IMPLEMENTED=true")
        print("PHYSICAL_NONEMPTY_LINE_ACCOUNTING=true")
        print("REAL_SOURCE_CANDIDATES=" + str(extraction_count))
        print("DISPLAY_PROJECTION_CANDIDATES=" + str(projection_count))
        print("SOURCE_EXCEEDS_DISPLAY_PROJECTION=true")
        print("REAL_SOURCE_ACCOUNTED=" + str(extraction_count))
        print("UNOBSERVABLE_ROWS=0")
        print("QUEUE_PARITY=true")
        print("IDEMPOTENT_REPLAY=true")
        print("POSTCOMMIT_PUBLISH_RECOVERY=true")
        print("TRANSACTION_ROLLBACK=true")
        print("SYNTHETIC_PARSE_UNSAFE_DUPLICATE_REPLACEMENT=true")
        print("PRODUCTION_RUNTIME_BOUND=false")
        print("PRODUCTION_UNCHANGED=true")
        print("BOUNDED_CANARY_AUTHORIZED=false")
        print("PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print("NEXT_SAFE_STEP=" + NEXT_STEP)
        print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
        print("ARTIFACT=" + str(ARTIFACT.relative_to(ROOT)))
        print("REPORT=" + str(REPORT.relative_to(ROOT)))
        return 0
    except BaseException:
        if EXTRACTOR.exists():
            EXTRACTOR.unlink()
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
