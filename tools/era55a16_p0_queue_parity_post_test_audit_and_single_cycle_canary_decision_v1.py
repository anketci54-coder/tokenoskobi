#!/usr/bin/env python3
from __future__ import annotations

import copy
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

A10 = ROOT / "data/control/era55a10_p0_ledger_writer_remediation_proof_package_v1.json"
A15 = ROOT / "data/control/era55a15_p0_pre_gateway_queue_semantic_parity_repair_and_temp_copy_test_v1.json"
ARTIFACT = ROOT / "data/control/era55a16_p0_queue_parity_post_test_audit_and_single_cycle_canary_decision_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A16_P0_QUEUE_PARITY_POST_TEST_AUDIT_AND_SINGLE_CYCLE_CANARY_DECISION.md"

ADAPTER = ROOT / "tools/news_disposition_admission_contract_v1.py"
EXTRACTOR = ROOT / "tools/news_pre_gateway_candidate_stream_v1.py"
WRITER = ROOT / "tools/news_disposition_ledger_writer_v1.py"
RECOVERY = ROOT / "tools/news_ledger_recovery_guard_v1.py"
GATEWAY = ROOT / "tools/hot_intelligence_ingress_gateway_v1.py"
RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
ORIGINAL_HOT = ROOT / "tools/post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.py"

MARKET = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADVERSARIAL = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
DISPLAY = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
RECOVERY_STATE = ROOT / "runtime/state/news_ledger_recovery_state_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

RESULT = "OK_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_AUTHORIZED"
NEXT = "ERA55A_17_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_AND_POST_AUDIT"
SUBJECT = "ERA55A16_CANARY_DECISION | OK | SINGLE_CYCLE_AUTHORIZED"
POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"
MAX_SOURCE_ROWS = 5000


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canon(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def db_state(path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
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
        }
    finally:
        conn.close()


def service_config() -> dict[str, Any]:
    completed = subprocess.run(
        [
            "systemctl",
            "show",
            "tokenoskobi-news-radar-refresh.service",
            "-p",
            "Environment",
            "-p",
            "ExecStart",
            "-p",
            "FragmentPath",
        ],
        text=True,
        capture_output=True,
    )
    text = completed.stdout
    return {
        "rc": completed.returncode,
        "runner_bound": str(RUNNER) in text,
        "writer_enabled": "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text,
        "runner_lock_enabled": "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text,
        "hot_override_enabled": "TOKENOSKOBI_NEWS_HOT_PATH=" in text,
        "fragment_path": next(
            (
                line.split("=", 1)[1]
                for line in text.splitlines()
                if line.startswith("FragmentPath=")
            ),
            "",
        ),
    }


def timer_state() -> dict[str, str]:
    active = subprocess.run(
        ["systemctl", "is-active", "tokenoskobi-news-radar-refresh.timer"],
        text=True,
        capture_output=True,
    )
    enabled = subprocess.run(
        ["systemctl", "is-enabled", "tokenoskobi-news-radar-refresh.timer"],
        text=True,
        capture_output=True,
    )
    service = subprocess.run(
        ["systemctl", "is-active", "tokenoskobi-news-radar-refresh.service"],
        text=True,
        capture_output=True,
    )
    return {
        "timer_active": active.stdout.strip() or active.stderr.strip(),
        "timer_enabled": enabled.stdout.strip() or enabled.stderr.strip(),
        "service_active": service.stdout.strip() or service.stderr.strip(),
    }


def stable_snapshot(temp: Path) -> dict[str, Any]:
    sources = {
        "market": MARKET,
        "adversarial": ADVERSARIAL,
        "display": DISPLAY,
        "hot": HOT,
    }
    for attempt in range(1, 9):
        before = {key: sha(path) for key, path in sources.items()}
        copies: dict[str, Path] = {}
        for key, source in sources.items():
            target = temp / f"snapshot_{key}{source.suffix}"
            shutil.copy2(source, target)
            copies[key] = target
        after = {key: sha(path) for key, path in sources.items()}
        copied = {key: sha(path) for key, path in copies.items()}
        if before == after == copied:
            return {
                "attempt": attempt,
                "hashes": before,
                "paths": copies,
            }
        time.sleep(0.25)
    raise RuntimeError("STABLE_SNAPSHOT_FAILED")


def backup(source: Path, target: Path) -> None:
    source_conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target_conn = sqlite3.connect(target)
    try:
        source_conn.backup(target_conn)
    finally:
        target_conn.close()
        source_conn.close()


def batch_metrics(path: Path, batch_uid: str) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return {
            "batch_rows": int(
                conn.execute(
                    "SELECT COUNT(*) FROM news_disposition_batches_v2 WHERE batch_uid=?",
                    (batch_uid,),
                ).fetchone()[0]
            ),
            "ledger_rows": int(
                conn.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?",
                    (batch_uid,),
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
        }
    finally:
        conn.close()


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


def validate_a10(value: dict[str, Any]) -> None:
    tests = value["tests"]
    assert value["status"] == "REMEDIATION_VALIDATED_REVIEW_PENDING"
    assert tests["gate_1_fresh_process_recovery"]["pass"] is True
    assert tests["gate_2_natural_runner_trigger"]["pass"] is True
    assert tests["gate_3_fsync_durability"]["pass"] is True
    assert tests["gate_4_monotonic_output_protection"]["pass"] is True
    assert tests["gate_5_logical_rollback_runbook"]["pass"] is True
    assert tests["gate_6_json_contract_parity"]["pass"] is True
    assert tests["feature_flag_default_inactive"]["pass"] is True


def validate_a15(value: dict[str, Any]) -> None:
    assert value["status"] == "CLOSED_TEMP_COPY_PARITY_REPAIR_OK"
    assert value["result"] == (
        "OK_COMPLETE_LEDGER_LEGACY_QUEUE_SEMANTIC_PARITY_TEMP_COPY"
    )
    parity = value["parity_repair"]
    assert parity["accounted_count"] == parity["source_candidate_count"]
    assert parity["unobservable_rows"] == 0
    assert parity["ledger_rows"] == parity["source_candidate_count"]
    assert parity["repaired_queue_exact_object_parity"] is True
    assert parity["repaired_queue_exact_uid_order_parity"] is True
    assert value["idempotency"]["output_hash_unchanged"] is True
    assert value["postcommit_publish_recovery"]["status"] == "RECOVERED"
    assert value["fail_closed_contract_tests"]["all_passed"] is True
    assert value["transaction_rollback"]["ok"] is True
    assert value["production_ledger_unchanged"] is True


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
        A10,
        A15,
        ADAPTER,
        EXTRACTOR,
        WRITER,
        RECOVERY,
        GATEWAY,
        RUNNER,
        ORIGINAL_HOT,
        MARKET,
        ADVERSARIAL,
        DISPLAY,
        SUMMARY,
        HOT,
        DB,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    a10 = load(A10)
    a15 = load(A15)
    validate_a10(a10)
    validate_a15(a15)
    assert sha(ADAPTER) == a15["adapter_module"]["sha256"]
    assert a15["adapter_module"]["policy_version"] == POLICY

    runner_text = RUNNER.read_text(encoding="utf-8")
    runner_audit = {
        "hot_path_environment_override": (
            "TOKENOSKOBI_NEWS_HOT_PATH" in runner_text
        ),
        "writer_feature_flag": (
            "TOKENOSKOBI_LEDGER_WRITER_ENABLED" in runner_text
        ),
        "runner_lock_feature_flag": (
            "TOKENOSKOBI_RUNNER_LOCK_ENABLED" in runner_text
        ),
        "recovery_function_present": "def run_recovery()" in runner_text,
        "hot_function_present": "def run_hot()" in runner_text,
        "recovery_before_raw": (
            runner_text.index("if writer_enabled:")
            < runner_text.index('append_order("RAW_START")')
        ),
        "derived_before_hot": (
            runner_text.index('append_order("DERIVED_START")')
            < runner_text.rindex("return run_hot()")
        ),
        "single_instance_lock_present": (
            "with single_instance_lock(RUNNER_LOCK)" in runner_text
        ),
        "hot_subprocess_inherits_environment": (
            'env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}'
            in runner_text
        ),
    }
    assert all(runner_audit.values())

    production_before = db_state(DB)
    service_before = service_config()
    timer_before = timer_state()
    assert production_before == {
        "batch_rows": 0,
        "ledger_rows": 0,
        "integrity_check": "ok",
        "quick_check": "ok",
        "foreign_key_check_rows": 0,
    }
    assert service_before["rc"] == 0
    assert service_before["runner_bound"] is True
    assert service_before["writer_enabled"] is False
    assert service_before["runner_lock_enabled"] is False
    assert service_before["hot_override_enabled"] is False

    tools = str(ROOT / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    extractor = module("a16_extractor", EXTRACTOR)
    writer = module("a16_writer", WRITER)
    recovery = module("a16_recovery", RECOVERY)
    gateway = module("a16_gateway", GATEWAY)
    adapter = module("a16_adapter", ADAPTER)
    assert adapter.POLICY_VERSION == POLICY

    temp = Path(tempfile.mkdtemp(prefix="era55a16_", dir="/tmp"))
    try:
        snap = stable_snapshot(temp)
        paths = snap["paths"]
        display = load(paths["display"])
        legacy_queue = gateway.normalize_items(display)
        current_hot = load(paths["hot"])
        current_queue = current_hot.get("hot_queue")
        assert isinstance(current_queue, list)
        assert canon(legacy_queue) == canon(current_queue)

        full = extractor.build_candidate_display(
            paths["market"],
            paths["adversarial"],
        )
        full_path = temp / "full.json"
        dump(full_path, full)
        plan = adapter.build_plan_with_admission_contract(
            full,
            legacy_queue,
            queue_capacity=50,
        )
        counts = plan["counts"]
        source_count = int(counts["source_candidate_count"])
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
        assert 0 < len(legacy_queue) <= 50
        assert len(legacy_queue) <= source_count <= MAX_SOURCE_ROWS
        assert accounted == source_count
        assert canon(plan["hot_queue"]) == canon(legacy_queue)

        temp_db = temp / "audit.sqlite"
        backup(DB, temp_db)
        output = temp / "hot.json"
        state = temp / "recovery.json"
        lock = temp / "writer.lock"

        first = adapter.write_and_publish_with_admission_contract(
            display_path=full_path,
            admission_contract_path=paths["hot"],
            summary_path=SUMMARY,
            db_path=temp_db,
            output_path=output,
            recovery_state_path=state,
            contract_seed_path=paths["hot"],
            queue_capacity=50,
            lock_path=lock,
        )
        first_hash = sha(output)
        metrics = batch_metrics(temp_db, plan["batch_uid"])
        assert canon(load(output)["hot_queue"]) == canon(legacy_queue)

        second = adapter.write_and_publish_with_admission_contract(
            display_path=full_path,
            admission_contract_path=paths["hot"],
            summary_path=SUMMARY,
            db_path=temp_db,
            output_path=output,
            recovery_state_path=state,
            contract_seed_path=paths["hot"],
            queue_capacity=50,
            lock_path=lock,
        )
        assert first["write_result"]["status"] == "COMMITTED"
        assert second["write_result"]["status"] == "IDEMPOTENT_REPLAY_NOOP"
        assert sha(output) == first_hash
        assert metrics["batch_rows"] == 1
        assert metrics["ledger_rows"] == source_count
        assert metrics["integrity_check"] == "ok"
        assert metrics["quick_check"] == "ok"
        assert metrics["foreign_key_check_rows"] == 0

        output.unlink()
        recovered = recovery.recover_committed_batch(
            temp_db,
            output,
            state,
            contract_seed_path=paths["hot"],
            batch_sequence=int(first["batch_sequence"]),
        )
        assert recovered["status"] == "RECOVERED"
        assert canon(load(output)["hot_queue"]) == canon(legacy_queue)

        duplicate = copy.deepcopy(legacy_queue)
        duplicate[-1] = copy.deepcopy(legacy_queue[0])
        duplicate_error = None
        try:
            adapter.build_plan_with_admission_contract(
                full,
                duplicate,
                queue_capacity=50,
            )
        except ValueError as exc:
            duplicate_error = str(exc)
        assert duplicate_error is not None
        assert duplicate_error.startswith("ADMISSION_CONTRACT_DUPLICATE_UID:")

        production_after = db_state(DB)
        service_after = service_config()
        assert production_before == production_after
        assert service_before == service_after

        decision_gates = {
            "a10_shields_validated": True,
            "a15_parity_repair_validated": True,
            "fresh_complete_accounting": accounted == source_count,
            "fresh_zero_unobservable_rows": accounted == source_count,
            "fresh_exact_legacy_object_parity": (
                canon(plan["hot_queue"]) == canon(legacy_queue)
            ),
            "fresh_idempotent_replay": (
                second["write_result"]["status"]
                == "IDEMPOTENT_REPLAY_NOOP"
            ),
            "fresh_recovery_parity": recovered["status"] == "RECOVERED",
            "source_within_bound": source_count <= MAX_SOURCE_ROWS,
            "runner_code_audit": all(runner_audit.values()),
            "service_writer_default_off": service_after["writer_enabled"] is False,
            "service_lock_default_off": (
                service_after["runner_lock_enabled"] is False
            ),
            "service_hot_override_default_off": (
                service_after["hot_override_enabled"] is False
            ),
            "production_ledger_empty": (
                production_after["batch_rows"] == 0
                and production_after["ledger_rows"] == 0
            ),
        }
        assert all(decision_gates.values())

        now = datetime.now(timezone.utc).isoformat()
        artifact = {
            "schema_version": "1.0",
            "work_unit": (
                "ERA55A_16_P0_QUEUE_PARITY_POST_TEST_AUDIT_"
                "AND_SINGLE_CYCLE_CANARY_DECISION"
            ),
            "timestamp_utc": now,
            "status": "CLOSED_SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED",
            "result": RESULT,
            "decision_gates": decision_gates,
            "runner_audit": runner_audit,
            "fresh_snapshot": {
                "attempt": snap["attempt"],
                "hashes": snap["hashes"],
                "source_candidate_count": source_count,
                "source_accounted": accounted,
                "unobservable_rows": 0,
                "legacy_queue_count": len(legacy_queue),
                "exact_legacy_object_parity": True,
                "exact_legacy_uid_order_parity": True,
                "idempotent_replay": True,
                "postcommit_recovery_parity": True,
            },
            "production_before": production_before,
            "production_after": production_after,
            "service_before": service_before,
            "service_after": service_after,
            "timer_observation": timer_before,
            "authorization": {
                "single_natural_cycle_bounded_canary_authorized": True,
                "general_production_writer_activation_authorized": False,
                "production_writer_active": False,
                "p0_f1_closed": False,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
            },
            "canary_execution_contract": {
                "one_full_runner_cycle_only": True,
                "maximum_new_batch_rows": 1,
                "maximum_source_rows": MAX_SOURCE_ROWS,
                "database_backup_required": True,
                "hot_output_backup_required": True,
                "recovery_state_backup_required": True,
                "timer_state_capture_required": True,
                "timer_pause_during_canary_required": True,
                "service_inactive_precondition_required": True,
                "runtime_only_systemd_dropin_required": True,
                "runner_lock_enabled_for_canary": True,
                "writer_enabled_for_canary": True,
                "hot_path_override_to_one_shot_wrapper_required": True,
                "dropin_removal_after_cycle_required": True,
                "timer_state_restore_required": True,
                "exact_hot_queue_parity_required": True,
                "database_integrity_audit_required": True,
                "rollback_on_any_gate_failure": True,
                "general_activation_after_canary": False,
            },
            "next_safe_step": NEXT,
        }
        dump(ARTIFACT, artifact)

        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            "\n".join(
                [
                    "# ERA55A16 Queue Parity Post-Test Audit and Canary Decision",
                    "",
                    "- Status: `CLOSED_SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED`",
                    f"- Result: `{RESULT}`",
                    f"- Fresh source candidates: `{source_count}`",
                    "- Unobservable rows: `0`",
                    "- Exact legacy queue parity: `true`",
                    "- Idempotent replay: `true`",
                    "- Post-commit recovery parity: `true`",
                    "- Production mutation: `false`",
                    "- Single-cycle canary authorized: `true`",
                    "- General production activation: `false`",
                    f"- Next safe step: `{NEXT}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        runtime = load(RUNTIME)
        current = runtime["current_state"]
        current.update(
            {
                "mode": "ERA55A16_SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED",
                "runtime_status": "WORK_UNIT_CLOSED",
                "updated_at": now,
                "last_action": {
                    "timestamp": now,
                    "task": artifact["work_unit"],
                    "result": RESULT,
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                },
                "active_work_unit": {
                    "id": artifact["work_unit"],
                    "type": "ERA55_P0_SINGLE_CYCLE_CANARY_DECISION",
                    "parent": "ERA55_RUNTIME_OPTIMIZATION",
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "status": artifact["status"],
                    "result": RESULT,
                    "production_mutation": False,
                    "next_step": NEXT,
                },
                "next_safe_step": {
                    "id": NEXT,
                    "type": "ERA55_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_POST_AUDIT",
                    "parent": "ERA55_RUNTIME_OPTIMIZATION",
                    "purpose": (
                        "Execute exactly one guarded full runner cycle, "
                        "remove all runtime overrides, and post-audit."
                    ),
                    "human_authorization_required": True,
                    "single_cycle_bounded_canary_authorized": True,
                    "general_production_writer_activation_authorized": False,
                    "option_b_authorized": False,
                    "optimization_apply_authorized": False,
                    "status": "READY",
                },
                "current_problem": {
                    "code": "SINGLE_CYCLE_BOUNDED_CANARY_NOT_YET_EXECUTED",
                    "severity": "P0",
                    "evidence": str(ARTIFACT.relative_to(ROOT)),
                },
            }
        )
        runtime["current_work_unit"] = current["active_work_unit"]
        dump(RUNTIME, runtime)

        history = load(HISTORY)
        events = history.setdefault("events", [])
        event_id = "ERA55A16_SINGLE_CYCLE_CANARY_DECISION_V1"
        if not any(
            isinstance(event, dict) and event.get("event_id") == event_id
            for event in events
        ):
            events.append(
                {
                    "event_id": event_id,
                    "timestamp_utc": now,
                    "era": "ERA55",
                    "work_unit": artifact["work_unit"],
                    "event": "SINGLE_CYCLE_BOUNDED_CANARY_DECISION",
                    "status": artifact["status"],
                    "result": RESULT,
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "source_candidate_count": source_count,
                    "unobservable_rows": 0,
                    "exact_legacy_queue_parity": True,
                    "single_cycle_bounded_canary_authorized": True,
                    "general_production_activation_authorized": False,
                    "production_unchanged": True,
                    "p0_f1_closed": False,
                    "next_safe_step": NEXT,
                }
            )
        history["updated_at"] = now
        history["updated_at_utc"] = now
        dump(HISTORY, history)

        master = MASTER.read_text(encoding="utf-8")
        master = replace_section(
            master,
            "## 01 PROJECT STATUS",
            """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_P0_SINGLE_CYCLE_CANARY_AUTHORIZED
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
CURRENT_STAGE=ERA55A_P0_SINGLE_CYCLE_CANARY
LAST_COMPLETED_SUBSTEP={artifact['work_unit']}
FRESH_SOURCE_CANDIDATES={source_count}
UNOBSERVABLE_ROWS=0
EXACT_LEGACY_OBJECT_PARITY=true
EXACT_LEGACY_UID_ORDER_PARITY=true
SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

Only one guarded full runner cycle is authorized. General production activation remains blocked.""",
        )
        master = replace_section(
            master,
            "## 03 LAST VERIFIED WORK",
            f"""```text
LAST_COMPLETED={artifact['work_unit']}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}""",
        )
        MASTER.write_text(master, encoding="utf-8")

        handoff = HANDOFF.read_text(encoding="utf-8")
        handoff = replace_section(
            handoff,
            "## 02 CURRENT CONTINUATION CHECKPOINT",
            f"""PROJECT_STATUS=ACTIVE_ERA55_P0_SINGLE_CYCLE_CANARY_AUTHORIZED
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_SINGLE_CYCLE_CANARY
LAST_COMPLETED_SUBSTEP={artifact['work_unit']}
FRESH_SOURCE_CANDIDATES={source_count}
UNOBSERVABLE_ROWS=0
EXACT_LEGACY_OBJECT_PARITY=true
EXACT_LEGACY_UID_ORDER_PARITY=true
SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""",
        )
        handoff = replace_section(
            handoff,
            "## 03 LAST VERIFIED WORK",
            f"""LAST_COMPLETED={artifact['work_unit']}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=SINGLE_CYCLE_BOUNDED_CANARY_NOT_YET_EXECUTED""",
        )
        handoff = replace_section(
            handoff,
            "## 06 DO NOT REOPEN OR REPEAT",
            """- Do not rerun A9-A16 unless evidence is invalidated.
- Do not execute more than one full runner canary cycle.
- Do not leave writer, lock, or hot-path override enabled after A17.
- Do not authorize general production or close P0 F1 from the decision alone.
- Do not start Option B.""",
        )
        handoff = replace_section(
            handoff,
            "## 07 ALLOWED NEXT DECISIONS",
            f"""- Complete accounting: `VALIDATED`.
- Exact legacy parity: `VALIDATED`.
- Single-cycle bounded canary: `AUTHORIZED_NOT_EXECUTED`.
- General production activation: `BLOCKED`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
        )
        handoff = replace_section(
            handoff,
            "## 08 NEXT SESSION EXECUTION RULE",
            """1. Confirm A17 and the one-cycle authorization.
2. Capture timer/service state and create backups.
3. Pause the timer and require the service to be inactive.
4. Install only a runtime systemd drop-in under /run.
5. Enable writer, runner lock and one-shot hot wrapper for one full service cycle.
6. Remove the drop-in immediately and restore timer state.
7. Post-audit DB, output parity, service/timer state and feature flags.
8. Roll back on any failed gate; do not enable general production.""",
        )
        HANDOFF.write_text(handoff, encoding="utf-8")

        almanac = ALMANAC.read_text(encoding="utf-8")
        marker = "## ERA55A_16 SINGLE-CYCLE CANARY DECISION"
        if marker not in almanac:
            ALMANAC.write_text(
                almanac.rstrip()
                + f"""

---

{marker}

- Status: `CLOSED_SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED`
- Result: `{RESULT}`
- Fresh source candidates: `{source_count}`
- Unobservable rows: `0`
- Exact legacy parity: `true`
- Production mutation: `false`
- Single-cycle canary authorized: `true`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `{NEXT}`
"""
                + "\n",
                encoding="utf-8",
            )

        git(
            "add",
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
        git("commit", "-m", SUBJECT)

        print("ERA55A16_CANARY_DECISION=SUCCESS")
        print("RESULT=" + RESULT)
        print("FRESH_SOURCE_CANDIDATES=" + str(source_count))
        print("FRESH_SOURCE_ACCOUNTED=" + str(accounted))
        print("UNOBSERVABLE_ROWS=0")
        print("LEGACY_QUEUE_EXACT_OBJECT_PARITY=true")
        print("LEGACY_QUEUE_EXACT_UID_ORDER_PARITY=true")
        print("IDEMPOTENT_REPLAY=true")
        print("POSTCOMMIT_PUBLISH_RECOVERY_PARITY=true")
        print("RUNNER_CODE_AUDIT=true")
        print("SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED=true")
        print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
        print("PRODUCTION_UNCHANGED=true")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print("NEXT_SAFE_STEP=" + NEXT)
        print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
        print("ARTIFACT=" + str(ARTIFACT.relative_to(ROOT)))
        return 0
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
