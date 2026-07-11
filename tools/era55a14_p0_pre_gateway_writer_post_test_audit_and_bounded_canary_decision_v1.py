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
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
EXPECTED_HEAD = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()

A10_ARTIFACT = ROOT / "data/control/era55a10_p0_ledger_writer_remediation_proof_package_v1.json"
A13_ARTIFACT = ROOT / "data/control/era55a13_p0_pre_gateway_candidate_stream_extraction_and_temp_copy_binding_test_v1.json"
DECISION_ARTIFACT = ROOT / "data/control/era55a14_p0_pre_gateway_writer_post_test_audit_and_bounded_canary_decision_v1.json"
EXTRACTOR = ROOT / "tools/news_pre_gateway_candidate_stream_v1.py"
WRITER = ROOT / "tools/news_disposition_ledger_writer_v1.py"
LEGACY_GATEWAY = ROOT / "tools/hot_intelligence_ingress_gateway_v1.py"
RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
MARKET_JSONL = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADVERSARIAL_JSONL = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
DISPLAY = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
HOT_OUTPUT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
RECOVERY_STATE = ROOT / "runtime/state/news_ledger_recovery_state_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

AUTHORIZE_NEXT = "ERA55A_15_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_AND_POST_AUDIT"
REPAIR_NEXT = "ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST"
COMMIT_SUBJECT = "ERA55A14_CANARY_DECISION | EVIDENCE_BASED | QUEUE_PARITY_AUDITED"
MAX_CANARY_SOURCE_ROWS = 5000
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
        "runner_bound": str(RUNNER) in text,
    }


def production_guard() -> dict[str, Any]:
    return {
        "database_file": file_guard(DB),
        "market_jsonl": file_guard(MARKET_JSONL),
        "adversarial_jsonl": file_guard(ADVERSARIAL_JSONL),
        "display": file_guard(DISPLAY),
        "hot_output": file_guard(HOT_OUTPUT),
        "recovery_state": file_guard(RECOVERY_STATE),
        "database_state": production_db_state(),
        "service_environment": service_environment(),
    }


def stable_snapshot(temp_dir: Path, attempts: int = 5) -> dict[str, Path]:
    sources = {
        "market": MARKET_JSONL,
        "adversarial": ADVERSARIAL_JSONL,
        "display": DISPLAY,
        "hot_output": HOT_OUTPUT,
    }
    for attempt in range(1, attempts + 1):
        before = {name: file_guard(path) for name, path in sources.items()}
        copies: dict[str, Path] = {}
        for name, path in sources.items():
            target = temp_dir / f"snapshot_{name}{path.suffix}"
            shutil.copy2(path, target)
            copies[name] = target
        after = {name: file_guard(path) for name, path in sources.items()}
        copied = {name: file_guard(path) for name, path in copies.items()}
        stable = before == after and all(
            copied[name].get("sha256") == before[name].get("sha256")
            for name in sources
        )
        if stable:
            return {
                **copies,
                "attempt": Path(str(attempt)),
            }
        time.sleep(0.25)
    raise RuntimeError("LIVE_SOURCE_SNAPSHOT_NOT_STABLE_AFTER_RETRIES")


def validate_a10(value: dict[str, Any]) -> None:
    tests = value["tests"]
    assert value["status"] == "REMEDIATION_VALIDATED_REVIEW_PENDING"
    assert tests["gate_1_fresh_process_recovery"]["pass"] is True
    assert tests["gate_2_natural_runner_trigger"]["pass"] is True
    assert tests["strict_single_instance_lock"]["pass"] is True
    assert tests["gate_3_fsync_durability"]["pass"] is True
    assert tests["gate_4_monotonic_output_protection"]["pass"] is True
    assert tests["gate_5_logical_rollback_runbook"]["pass"] is True
    assert tests["gate_6_json_contract_parity"]["pass"] is True
    assert tests["poison_pill_quarantine"]["pass"] is True


def validate_a13(value: dict[str, Any]) -> None:
    assert value["status"] == "CLOSED_TEMP_COPY_BINDING_OK"
    assert value["result"] == (
        "OK_COMPLETE_PRE_GATEWAY_JSONL_STREAM_TEMP_COPY_BOUND"
    )
    real = value["real_pre_gateway_stream"]
    assert real["source_candidate_count"] == 106
    assert real["accounted_count"] == 106
    assert real["ledger_rows"] == 106
    assert real["unobservable_rows"] == 0
    assert real["queue_parity"] is True
    assert value["idempotency"]["output_hash_unchanged"] is True
    assert value["postcommit_publish_recovery"]["status"] == "RECOVERED"
    assert value["transaction_rollback"]["ok"] is True
    assert value["production_unchanged"] is True


def uid_list(items: Any) -> list[str]:
    if not isinstance(items, list):
        raise RuntimeError("QUEUE_NOT_LIST")
    return [str(item.get("hot_uid") or "") for item in items]


def mismatch_details(left: list[str], right: list[str]) -> dict[str, Any]:
    first_index = None
    for index, pair in enumerate(zip(left, right)):
        if pair[0] != pair[1]:
            first_index = index
            break
    if first_index is None and len(left) != len(right):
        first_index = min(len(left), len(right))
    left_only = sorted(set(left) - set(right))
    right_only = sorted(set(right) - set(left))
    return {
        "first_mismatch_index": first_index,
        "left_count": len(left),
        "right_count": len(right),
        "left_only_count": len(left_only),
        "right_only_count": len(right_only),
        "left_only_sample": left_only[:10],
        "right_only_sample": right_only[:10],
    }


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
        A10_ARTIFACT,
        A13_ARTIFACT,
        EXTRACTOR,
        WRITER,
        LEGACY_GATEWAY,
        RUNNER,
        MARKET_JSONL,
        ADVERSARIAL_JSONL,
        DISPLAY,
        HOT_OUTPUT,
        DB,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    validate_a10(load_json(A10_ARTIFACT))
    a13 = load_json(A13_ARTIFACT)
    validate_a13(a13)
    if sha256_file(EXTRACTOR) != a13["extractor_module"]["sha256"]:
        raise RuntimeError("EXTRACTOR_HASH_DRIFT")

    extractor_text = EXTRACTOR.read_text(encoding="utf-8")
    extractor_code_audit = {
        "binary_line_read": 'path.open("rb")' in extractor_text,
        "strict_utf8_decode": 'decode("utf-8", errors="strict")' in extractor_text,
        "parse_error_preserved": "PRE_GATEWAY_PARSE_ERROR" in extractor_text,
        "utf8_error_preserved": "PRE_GATEWAY_UTF8_ERROR" in extractor_text,
        "nonobject_preserved": "PRE_GATEWAY_NONOBJECT" in extractor_text,
        "physical_line_counter": "physical_lines += 1" in extractor_text,
    }
    if not all(extractor_code_audit.values()):
        raise RuntimeError("EXTRACTOR_CODE_AUDIT_FAILED")

    guard_before = production_guard()
    assert guard_before["database_state"]["batch_rows"] == 0
    assert guard_before["database_state"]["ledger_rows"] == 0
    assert guard_before["database_state"]["integrity_check"] == "ok"
    assert guard_before["database_state"]["quick_check"] == "ok"
    assert guard_before["database_state"]["foreign_key_check_rows"] == 0
    assert guard_before["service_environment"]["writer_enabled_explicitly"] is False
    assert guard_before["service_environment"]["runner_lock_enabled_explicitly"] is False
    assert guard_before["service_environment"]["runner_bound"] is True

    extractor = import_module("a14_extractor", EXTRACTOR)
    writer = import_module("a14_writer", WRITER)
    gateway = import_module("a14_gateway", LEGACY_GATEWAY)

    temp_dir = Path(tempfile.mkdtemp(prefix="era55a14_", dir="/tmp"))
    try:
        snap = stable_snapshot(temp_dir)
        current_display = load_json(snap["display"])
        current_hot = load_json(snap["hot_output"])
        pre_gateway_display = extractor.build_candidate_display(
            snap["market"],
            snap["adversarial"],
        )
        plan = writer.build_plan(pre_gateway_display, queue_capacity=50)
        legacy_queue = gateway.normalize_items(current_display)

        source_count = int(
            pre_gateway_display["extraction"]["source_candidate_count"]
        )
        counts = plan["counts"]
        accounted = sum(
            int(counts[key])
            for key in (
                "admitted_count",
                "overflow_count",
                "duplicate_removed_count",
                "unsafe_filtered_count",
                "invalid_candidate_count",
                "replaced_count",
            )
        )
        assert source_count > 0
        assert source_count == int(counts["source_candidate_count"])
        assert accounted == source_count
        assert source_count <= MAX_CANARY_SOURCE_ROWS

        plan_uids = uid_list(plan["hot_queue"])
        legacy_uids = uid_list(legacy_queue)
        hot_uids = uid_list(current_hot.get("hot_queue"))

        legacy_rebuild_matches_hot = legacy_uids == hot_uids
        pre_gateway_matches_legacy = plan_uids == legacy_uids

        top_level_contract_ok = REQUIRED_TOP_LEVEL_KEYS <= set(current_hot)
        hot_item_contract_ok = all(
            isinstance(item, dict)
            and REQUIRED_HOT_ITEM_KEYS <= set(item)
            for item in plan["hot_queue"]
        )
        current_hot_count_ok = (
            int(current_hot.get("hot_queue_count") or 0) == len(hot_uids)
        )
        queue_capacity_ok = len(plan_uids) <= 50 and len(legacy_uids) <= 50

        canary_authorized = all(
            (
                legacy_rebuild_matches_hot,
                pre_gateway_matches_legacy,
                top_level_contract_ok,
                hot_item_contract_ok,
                current_hot_count_ok,
                queue_capacity_ok,
                accounted == source_count,
                source_count <= MAX_CANARY_SOURCE_ROWS,
            )
        )

        if canary_authorized:
            status = "CLOSED_SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED"
            result = "AUTHORIZE_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY"
            next_step = AUTHORIZE_NEXT
            problem_code = "SINGLE_CYCLE_BOUNDED_CANARY_NOT_YET_EXECUTED"
        else:
            status = "CLOSED_BOUNDED_CANARY_REJECTED"
            result = "REJECT_BOUNDED_CANARY_QUEUE_SEMANTIC_PARITY_NOT_PROVEN"
            next_step = REPAIR_NEXT
            problem_code = "PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_NOT_PROVEN"

        guard_after = production_guard()
        assert guard_before == guard_after

        now = utc_now()
        artifact = {
            "schema_version": "1.0",
            "work_unit": (
                "ERA55A_14_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_"
                "AND_BOUNDED_CANARY_DECISION"
            ),
            "timestamp_utc": now,
            "status": status,
            "result": result,
            "a10_shields_validated": True,
            "a13_complete_stream_validated": True,
            "extractor_code_audit": extractor_code_audit,
            "stable_snapshot": {
                "attempt": int(str(snap["attempt"])),
                "market_sha256": sha256_file(snap["market"]),
                "adversarial_sha256": sha256_file(snap["adversarial"]),
                "display_sha256": sha256_file(snap["display"]),
                "hot_output_sha256": sha256_file(snap["hot_output"]),
            },
            "current_stream": {
                "source_candidate_count": source_count,
                "accounted_count": accounted,
                "unobservable_rows": source_count - accounted,
                "counts": counts,
                "queue_count": len(plan_uids),
                "max_canary_source_rows": MAX_CANARY_SOURCE_ROWS,
                "within_canary_row_bound": (
                    source_count <= MAX_CANARY_SOURCE_ROWS
                ),
            },
            "queue_semantic_parity": {
                "legacy_rebuild_matches_current_hot_output": (
                    legacy_rebuild_matches_hot
                ),
                "pre_gateway_writer_matches_legacy_gateway": (
                    pre_gateway_matches_legacy
                ),
                "pre_gateway_vs_legacy": mismatch_details(
                    plan_uids,
                    legacy_uids,
                ),
                "legacy_vs_current_hot": mismatch_details(
                    legacy_uids,
                    hot_uids,
                ),
                "pre_gateway_uid_hash": hashlib.sha256(
                    "\n".join(plan_uids).encode("utf-8")
                ).hexdigest(),
                "legacy_uid_hash": hashlib.sha256(
                    "\n".join(legacy_uids).encode("utf-8")
                ).hexdigest(),
                "current_hot_uid_hash": hashlib.sha256(
                    "\n".join(hot_uids).encode("utf-8")
                ).hexdigest(),
            },
            "json_contract": {
                "required_top_level_keys_present": top_level_contract_ok,
                "writer_hot_item_contract_present": hot_item_contract_ok,
                "current_hot_count_consistent": current_hot_count_ok,
                "queue_capacity_ok": queue_capacity_ok,
            },
            "authorization": {
                "single_natural_cycle_bounded_canary_authorized": (
                    canary_authorized
                ),
                "general_production_writer_activation_authorized": False,
                "production_writer_active": False,
                "p0_f1_closed": False,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
            },
            "canary_constraints": {
                "one_natural_runner_cycle_only": True,
                "maximum_new_batch_rows": 1,
                "maximum_source_rows": MAX_CANARY_SOURCE_ROWS,
                "preflight_snapshot_required": True,
                "database_backup_required": True,
                "automatic_feature_flag_removal_required": True,
                "post_cycle_integrity_and_contract_audit_required": True,
                "rollback_on_any_gate_failure": True,
            },
            "production_guard_before": guard_before,
            "production_guard_after": guard_after,
            "production_unchanged": True,
            "next_safe_step": next_step,
        }
        write_json(DECISION_ARTIFACT, artifact)

        runtime = load_json(RUNTIME)
        state = runtime["current_state"]
        state["mode"] = (
            "ERA55A14_SINGLE_CYCLE_CANARY_AUTHORIZED"
            if canary_authorized
            else "ERA55A14_CANARY_REJECTED_QUEUE_PARITY_NOT_PROVEN"
        )
        state["runtime_status"] = "WORK_UNIT_CLOSED"
        state["updated_at"] = now
        state["last_action"] = {
            "timestamp": now,
            "task": (
                "ERA55A_14_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_"
                "AND_BOUNDED_CANARY_DECISION"
            ),
            "result": result,
            "artifact": str(DECISION_ARTIFACT.relative_to(ROOT)),
        }
        state["active_work_unit"] = {
            "id": (
                "ERA55A_14_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_"
                "AND_BOUNDED_CANARY_DECISION"
            ),
            "type": "ERA55_P0_BOUNDED_CANARY_DECISION",
            "parent": "ERA55_RUNTIME_OPTIMIZATION",
            "artifact": str(DECISION_ARTIFACT.relative_to(ROOT)),
            "status": status,
            "result": result,
            "production_mutation": False,
            "next_step": next_step,
        }
        state["next_safe_step"] = {
            "id": next_step,
            "type": (
                "ERA55_P0_SINGLE_CYCLE_BOUNDED_CANARY_APPLY"
                if canary_authorized
                else "ERA55_P0_QUEUE_SEMANTIC_PARITY_REPAIR_TEMP_COPY_TEST"
            ),
            "parent": "ERA55_RUNTIME_OPTIMIZATION",
            "purpose": (
                "Execute one guarded natural runner cycle and post-audit."
                if canary_authorized
                else "Preserve complete ledger accounting while making the admitted output exactly match the legacy gateway queue."
            ),
            "human_authorization_required": canary_authorized,
            "single_cycle_bounded_canary_authorized": canary_authorized,
            "general_production_writer_activation_authorized": False,
            "option_b_authorized": False,
            "optimization_apply_authorized": False,
            "status": "READY",
        }
        state["current_problem"] = {
            "code": problem_code,
            "severity": "P0",
            "evidence": str(DECISION_ARTIFACT.relative_to(ROOT)),
        }
        runtime["current_work_unit"] = state["active_work_unit"]
        write_json(RUNTIME, runtime)

        history = load_json(HISTORY)
        events = history.setdefault("events", [])
        event_id = "ERA55A14_BOUNDED_CANARY_DECISION_V1"
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
                        "ERA55A_14_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_"
                        "AND_BOUNDED_CANARY_DECISION"
                    ),
                    "event": "BOUNDED_CANARY_DECISION",
                    "status": status,
                    "result": result,
                    "artifact": str(DECISION_ARTIFACT.relative_to(ROOT)),
                    "source_candidate_count": source_count,
                    "pre_gateway_matches_legacy": pre_gateway_matches_legacy,
                    "legacy_matches_current_hot": legacy_rebuild_matches_hot,
                    "single_cycle_bounded_canary_authorized": canary_authorized,
                    "production_unchanged": True,
                    "p0_f1_closed": False,
                    "next_safe_step": next_step,
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
PROJECT_STATUS=ACTIVE_ERA55_P0_CANARY_OR_PARITY_REPAIR
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
CURRENT_STAGE=ERA55A_P0_BOUNDED_CANARY_DECISION
LAST_COMPLETED_SUBSTEP=ERA55A_14_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION
COMPLETE_PRE_GATEWAY_ACCOUNTING=true
CURRENT_SOURCE_CANDIDATES={source_count}
UNOBSERVABLE_ROWS=0
LEGACY_REBUILD_MATCHES_CURRENT_HOT={str(legacy_rebuild_matches_hot).lower()}
PRE_GATEWAY_WRITER_MATCHES_LEGACY_GATEWAY={str(pre_gateway_matches_legacy).lower()}
SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED={str(canary_authorized).lower()}
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
```

A14 made an evidence-based decision. Complete ledger accounting is preserved; canary authorization depends on exact legacy queue UID parity.""",
        )
        master = replace_section(
            master,
            "## 03 LAST VERIFIED WORK",
            f"""```text
LAST_COMPLETED=ERA55A_14_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION
LAST_RESULT={result}
LAST_ARTIFACT={DECISION_ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={status}
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
```

NEXT_SAFE_STEP={next_step}""",
        )
        MASTER.write_text(master, encoding="utf-8")

        handoff = HANDOFF.read_text(encoding="utf-8")
        handoff = replace_section(
            handoff,
            "## 02 CURRENT CONTINUATION CHECKPOINT",
            f"""PROJECT_STATUS=ACTIVE_ERA55_P0_CANARY_OR_PARITY_REPAIR
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_BOUNDED_CANARY_DECISION
LAST_COMPLETED_SUBSTEP=ERA55A_14_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION
CURRENT_SOURCE_CANDIDATES={source_count}
COMPLETE_PRE_GATEWAY_ACCOUNTING=true
UNOBSERVABLE_ROWS=0
LEGACY_REBUILD_MATCHES_CURRENT_HOT={str(legacy_rebuild_matches_hot).lower()}
PRE_GATEWAY_WRITER_MATCHES_LEGACY_GATEWAY={str(pre_gateway_matches_legacy).lower()}
SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED={str(canary_authorized).lower()}
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A14 decision is canonical. Follow only the recorded next safe step.""",
        )
        handoff = replace_section(
            handoff,
            "## 03 LAST VERIFIED WORK",
            f"""LAST_COMPLETED=ERA55A_14_P0_PRE_GATEWAY_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION
LAST_RESULT={result}
LAST_ARTIFACT={DECISION_ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={status}
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM={problem_code}""",
        )
        handoff = replace_section(
            handoff,
            "## 06 DO NOT REOPEN OR REPEAT",
            """- Do not rerun A9-A14 unless evidence is invalidated.
- Do not activate a canary unless A14 explicitly authorizes it.
- Do not change the current gateway queue semantics silently.
- Do not enable general production writer activation.
- Do not start Option B or mark P0 F1 closed.""",
        )
        handoff = replace_section(
            handoff,
            "## 07 ALLOWED NEXT DECISIONS",
            f"""- Complete pre-gateway accounting: `VALIDATED`.
- Legacy gateway rebuild parity: `{legacy_rebuild_matches_hot}`.
- Pre-gateway writer queue parity: `{pre_gateway_matches_legacy}`.
- Single-cycle bounded canary: `{canary_authorized}`.
- General production activation: `BLOCKED`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={next_step}""",
        )
        handoff = replace_section(
            handoff,
            "## 08 NEXT SESSION EXECUTION RULE",
            (
                """1. Confirm the single-cycle canary authorization and constraints.
2. Prepare backup and automatic rollback.
3. Bind extractor and writer for exactly one natural runner cycle.
4. Remove feature flags immediately after the cycle.
5. Audit DB, queue contract, recovery state and service/timer health.
6. Do not authorize general production or close P0 F1."""
                if canary_authorized
                else """1. Confirm queue semantic parity repair is current.
2. Keep complete pre-gateway accounting as the ledger source.
3. Use the legacy gateway queue as the admitted-output contract.
4. Mark every other valid source observation as overflow without losing evidence.
5. Prove exact UID order parity on temp copy.
6. Do not activate production or close P0 F1."""
            ),
        )
        HANDOFF.write_text(handoff, encoding="utf-8")

        almanac = ALMANAC.read_text(encoding="utf-8")
        marker = "## ERA55A_14 BOUNDED CANARY DECISION"
        if marker not in almanac:
            ALMANAC.write_text(
                almanac.rstrip()
                + f"""

---

{marker}

- Status: `{status}`
- Result: `{result}`
- Source candidates: `{source_count}`
- Complete accounting: `true`
- Legacy rebuild matches current hot: `{str(legacy_rebuild_matches_hot).lower()}`
- Pre-gateway writer matches legacy queue: `{str(pre_gateway_matches_legacy).lower()}`
- Single-cycle bounded canary authorized: `{str(canary_authorized).lower()}`
- General production activation authorized: `false`
- Production mutation: `false`
- P0 F1 closed: `false`
- Next safe step: `{next_step}`
"""
                + "\n",
                encoding="utf-8",
            )

        git(
            "add",
            str(DECISION_ARTIFACT.relative_to(ROOT)),
            str(RUNTIME.relative_to(ROOT)),
            str(HISTORY.relative_to(ROOT)),
            str(MASTER.relative_to(ROOT)),
            str(HANDOFF.relative_to(ROOT)),
            str(ALMANAC.relative_to(ROOT)),
        )
        if not git("diff", "--cached", "--name-only"):
            raise RuntimeError("NO_STAGED_CHANGES")
        git("commit", "-m", COMMIT_SUBJECT)

        print("ERA55A14_CANARY_DECISION=SUCCESS")
        print("DECISION=" + result)
        print("CURRENT_SOURCE_CANDIDATES=" + str(source_count))
        print("CURRENT_SOURCE_ACCOUNTED=" + str(accounted))
        print("UNOBSERVABLE_ROWS=0")
        print(
            "LEGACY_REBUILD_MATCHES_CURRENT_HOT="
            + str(legacy_rebuild_matches_hot).lower()
        )
        print(
            "PRE_GATEWAY_WRITER_MATCHES_LEGACY_GATEWAY="
            + str(pre_gateway_matches_legacy).lower()
        )
        print(
            "SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED="
            + str(canary_authorized).lower()
        )
        print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
        print("PRODUCTION_UNCHANGED=true")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print("NEXT_SAFE_STEP=" + next_step)
        print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
        print("ARTIFACT=" + str(DECISION_ARTIFACT.relative_to(ROOT)))
        return 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
