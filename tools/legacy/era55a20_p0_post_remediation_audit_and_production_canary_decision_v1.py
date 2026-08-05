#!/usr/bin/env python3
from __future__ import annotations

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

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

A18 = ROOT / "data/control/era55a18_p0_post_canary_red_team_production_activation_decision_v1.json"
A19 = ROOT / "data/control/era55a19_p0_automatic_rollback_and_end_to_end_success_remediation_temp_copy_test_v1.json"
ARTIFACT = ROOT / "data/control/era55a20_p0_post_remediation_audit_and_production_canary_decision_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A20_P0_POST_REMEDIATION_AUDIT_AND_PRODUCTION_CANARY_DECISION.md"

ROLLBACK_GUARD = ROOT / "tools/news_disposition_postcommit_rollback_guard_v1.py"
RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
ADAPTER = ROOT / "tools/news_disposition_admission_contract_v1.py"
EXTRACTOR = ROOT / "tools/news_pre_gateway_candidate_stream_v1.py"
GATEWAY = ROOT / "tools/hot_intelligence_ingress_gateway_v1.py"
BRIDGE = ROOT / "tools/news_active_panel_data_bridge_v1.py"

MARKET = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADVERSARIAL = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
DISPLAY = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

WORK_UNIT = "ERA55A_20_P0_POST_REMEDIATION_AUDIT_AND_PRODUCTION_CANARY_DECISION"
RESULT = "OK_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED"
NEXT = "ERA55A_21_P0_SINGLE_NATURAL_CYCLE_POST_REMEDIATION_CANARY_APPLY_AND_POST_AUDIT"
SUBJECT = "ERA55A20_CANARY_DECISION | OK | ONE_POST_REMEDIATION_CYCLE_AUTHORIZED"
LEDGER_POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"
ROLLBACK_POLICY = "POSTCOMMIT_ARCHIVE_TRIGGER_ROLLBACK_GUARD_V1"
MAX_SOURCE_ROWS = 5000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def git(*args: str) -> str:
    return run(["git", *args]).stdout.strip()


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
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def sqlite_backup(source: Path, target: Path) -> None:
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target_connection = sqlite3.connect(target)
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()


def database_state(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        latest_row = connection.execute(
            """
            SELECT rowid, batch_uid, status, policy_version,
                   source_candidate_count, admitted_count, overflow_count
            FROM news_disposition_batches_v2
            ORDER BY rowid DESC
            LIMIT 1
            """
        ).fetchone()
        if latest_row is None:
            raise RuntimeError("A20_PRODUCTION_BATCH_MISSING")
        uid = str(latest_row[1])
        latest = {
            "batch_sequence": int(latest_row[0]),
            "batch_uid": uid,
            "status": str(latest_row[2]),
            "policy_version": str(latest_row[3]),
            "source_candidate_count": int(latest_row[4]),
            "admitted_count": int(latest_row[5]),
            "overflow_count": int(latest_row[6]),
            "ledger_rows": int(
                connection.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?",
                    (uid,),
                ).fetchone()[0]
            ),
        }
        triggers = [
            str(name)
            for (name,) in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='trigger'
                  AND tbl_name IN (
                    'news_disposition_batches_v2',
                    'news_disposition_ledger_v2'
                  )
                ORDER BY name
                """
            ).fetchall()
        ]
        return {
            "batch_rows": int(
                connection.execute(
                    "SELECT COUNT(*) FROM news_disposition_batches_v2"
                ).fetchone()[0]
            ),
            "ledger_rows": int(
                connection.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2"
                ).fetchone()[0]
            ),
            "latest_batch": latest,
            "integrity_check": str(
                connection.execute("PRAGMA integrity_check").fetchone()[0]
            ),
            "quick_check": str(
                connection.execute("PRAGMA quick_check").fetchone()[0]
            ),
            "foreign_key_check_rows": len(
                connection.execute("PRAGMA foreign_key_check").fetchall()
            ),
            "triggers": triggers,
        }
    finally:
        connection.close()


def unit_state(unit: str) -> dict[str, Any]:
    active = run(["systemctl", "is-active", unit], check=False)
    enabled = run(["systemctl", "is-enabled", unit], check=False)
    return {
        "active": active.stdout.strip() or active.stderr.strip(),
        "enabled": enabled.stdout.strip() or enabled.stderr.strip(),
    }


def service_environment() -> dict[str, Any]:
    text = run(
        [
            "systemctl",
            "show",
            SERVICE,
            "-p",
            "Environment",
            "-p",
            "ExecStart",
            "-p",
            "FragmentPath",
        ],
        check=False,
    ).stdout
    return {
        "runner_bound": str(RUNNER) in text,
        "writer_enabled": "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text,
        "runner_lock_enabled": "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text,
        "hot_override_enabled": "TOKENOSKOBI_NEWS_HOT_PATH=" in text,
        "canary_mode_enabled": (
            "TOKENOSKOBI_A17_ONE_SHOT_HOT=1" in text
            or "TOKENOSKOBI_A21_ONE_SHOT_HOT=1" in text
        ),
    }


def stable_snapshot(temp: Path) -> dict[str, Any]:
    sources = {
        "market": MARKET,
        "adversarial": ADVERSARIAL,
        "display": DISPLAY,
        "hot": HOT,
        "panel_hot": PANEL_HOT,
    }
    for attempt in range(1, 9):
        before = {name: sha(path) for name, path in sources.items()}
        copies: dict[str, Path] = {}
        for name, source in sources.items():
            target = temp / (name + source.suffix)
            shutil.copy2(source, target)
            copies[name] = target
        after = {name: sha(path) for name, path in sources.items()}
        copied = {name: sha(path) for name, path in copies.items()}
        if before == after == copied:
            return {
                "attempt": attempt,
                "hashes": before,
                "paths": copies,
            }
        time.sleep(0.25)
    raise RuntimeError("A20_STABLE_SNAPSHOT_FAILED")


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
        A18,
        A19,
        ROLLBACK_GUARD,
        RUNNER,
        ADAPTER,
        EXTRACTOR,
        GATEWAY,
        BRIDGE,
        MARKET,
        ADVERSARIAL,
        DISPLAY,
        HOT,
        PANEL_HOT,
        DB,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
    ):
        if not path.exists():
            raise FileNotFoundError(path)
    if ARTIFACT.exists():
        raise RuntimeError("A20_ARTIFACT_ALREADY_EXISTS")

    a18 = load(A18)
    a19 = load(A19)

    assert a18["status"] == "CLOSED_GENERAL_PRODUCTION_ACTIVATION_REJECTED"
    assert a18["decision"]["general_production_writer_activation_authorized"] is False
    assert a18["decision"]["new_canary_authorized"] is False

    assert a19["status"] == "CLOSED_TEMP_COPY_REMEDIATION_OK"
    assert a19["result"] == (
        "OK_AUTOMATIC_ROLLBACK_AND_END_TO_END_"
        "SUCCESS_REMEDIATION_TEMP_COPY"
    )
    assert a19["production_unchanged"] is True
    assert a19["production_guard_before"] == a19["production_guard_after"]

    rollback_evidence = a19["rollback_guard"]
    isolated = a19["isolated_end_to_end"]
    assert rollback_evidence["policy_version"] == ROLLBACK_POLICY
    assert rollback_evidence["production_runtime_bound"] is False
    assert rollback_evidence["baseline_clear"]["status"] == "ROLLED_BACK_ARCHIVE_TRIGGER_SAFE"
    assert rollback_evidence["downstream_failure_rollback"]["status"] == "ROLLED_BACK_ARCHIVE_TRIGGER_SAFE"
    assert rollback_evidence["rollback_failure_exposure"]["status"] == "ROLLBACK_FAILED_TRANSACTION_REVERTED"
    assert rollback_evidence["rollback_failure_transaction_reverted"] is True
    assert rollback_evidence["original_error_preserved_on_success"] is True
    assert rollback_evidence["original_error_preserved_on_failure"] is True

    assert isolated["first_run_rc"] == 0
    assert isolated["second_run_rc"] == 0
    assert isolated["recovery_only_rc"] == 0
    assert isolated["first_writer_status"] == "COMMITTED"
    assert isolated["second_writer_status"] == "IDEMPOTENT_REPLAY_NOOP"
    assert isolated["hot_end_zero_proven"] is True
    assert isolated["bridge_byte_preserving_in_same_flow"] is True
    assert isolated["panel_hot_hash_match"] is True
    assert isolated["exact_legacy_queue_parity"] is True
    assert isolated["idempotent_replay"] is True
    assert isolated["recovery_after_output_loss"] is True
    assert isolated["source_accounted"] == isolated["source_candidate_count"]
    assert isolated["unobservable_rows"] == 0

    production_before = database_state(DB)
    environment = service_environment()
    timer = unit_state(TIMER)
    service = unit_state(SERVICE)

    assert production_before["batch_rows"] == 1
    assert production_before["ledger_rows"] == 106
    assert production_before["integrity_check"] == "ok"
    assert production_before["quick_check"] == "ok"
    assert production_before["foreign_key_check_rows"] == 0
    assert production_before["latest_batch"]["status"] == "COMMITTED"
    assert production_before["latest_batch"]["policy_version"] == LEDGER_POLICY
    assert production_before["latest_batch"]["ledger_rows"] == 106
    assert set(production_before["triggers"]) == {
        "trg_news_disposition_batch_archive_before_delete_v2",
        "trg_news_disposition_ledger_archive_before_delete_v2",
    }

    assert environment["runner_bound"] is True
    assert environment["writer_enabled"] is False
    assert environment["runner_lock_enabled"] is False
    assert environment["hot_override_enabled"] is False
    assert environment["canary_mode_enabled"] is False
    assert timer["active"] == "active"
    assert timer["enabled"] == "enabled"
    assert service["active"] in {"inactive", "failed"}

    tools = str(ROOT / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    rollback_guard = load_module("a20_rollback_guard", ROLLBACK_GUARD)
    extractor = load_module("a20_extractor", EXTRACTOR)
    adapter = load_module("a20_adapter", ADAPTER)
    gateway = load_module("a20_gateway", GATEWAY)

    assert rollback_guard.POLICY_VERSION == ROLLBACK_POLICY
    assert adapter.POLICY_VERSION == LEDGER_POLICY

    temp_root = Path(tempfile.mkdtemp(prefix="era55a20_", dir="/tmp"))
    try:
        snapshot = stable_snapshot(temp_root)
        paths = snapshot["paths"]
        assert snapshot["hashes"]["hot"] == snapshot["hashes"]["panel_hot"]

        display = load(paths["display"])
        current_hot = load(paths["hot"])
        legacy_queue = gateway.normalize_items(display)
        current_queue = current_hot.get("hot_queue")
        assert isinstance(current_queue, list)
        assert canonical(legacy_queue) == canonical(current_queue)

        full = extractor.build_candidate_display(paths["market"], paths["adversarial"])
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
        prospective_uid = str(plan["batch_uid"])
        existing_uid = str(production_before["latest_batch"]["batch_uid"])
        assert 0 < len(legacy_queue) <= 50
        assert len(legacy_queue) <= source_count <= MAX_SOURCE_ROWS
        assert accounted == source_count
        assert canonical(plan["hot_queue"]) == canonical(legacy_queue)
        assert prospective_uid != existing_uid

        rollback_success_db = temp_root / "rollback_success.sqlite"
        sqlite_backup(DB, rollback_success_db)
        rollback_success = rollback_guard.rollback_committed_batch(
            rollback_success_db,
            existing_uid,
            original_error="A20_INDEPENDENT_ROLLBACK_AUDIT",
            archive_location="rollback://a20/independent-audit",
        )
        assert rollback_success["status"] == "ROLLED_BACK_ARCHIVE_TRIGGER_SAFE"
        assert rollback_success["original_error"] == "A20_INDEPENDENT_ROLLBACK_AUDIT"
        assert rollback_success["rollback_error"] is None
        rollback_success_state = database_state(rollback_success_db)
        assert rollback_success_state["batch_rows"] == 0
        assert rollback_success_state["ledger_rows"] == 0
        assert rollback_success_state["integrity_check"] == "ok"
        assert rollback_success_state["quick_check"] == "ok"
        assert rollback_success_state["foreign_key_check_rows"] == 0

        rollback_failure_db = temp_root / "rollback_failure.sqlite"
        sqlite_backup(DB, rollback_failure_db)
        rollback_failure = rollback_guard.rollback_committed_batch(
            rollback_failure_db,
            existing_uid,
            original_error="A20_INDEPENDENT_FAILURE_AUDIT",
            archive_location="rollback://a20/failure-audit",
            inject_failure_stage="AFTER_LEDGER_DELETE",
        )
        assert rollback_failure["status"] == "ROLLBACK_FAILED_TRANSACTION_REVERTED"
        assert rollback_failure["original_error"] == "A20_INDEPENDENT_FAILURE_AUDIT"
        assert "INJECTED_ROLLBACK_FAILURE_AFTER_LEDGER_DELETE" in str(
            rollback_failure["rollback_error"]
        )
        assert rollback_failure["transaction_rolled_back"] is True
        rollback_failure_state = database_state(rollback_failure_db)
        assert rollback_failure_state == production_before

        require_success_error = None
        try:
            rollback_guard.require_success(rollback_failure)
        except RuntimeError as exc:
            require_success_error = str(exc)
        assert require_success_error is not None
        assert "POSTCOMMIT_ROLLBACK_FAILED:" in require_success_error
        assert "ORIGINAL_ERROR:A20_INDEPENDENT_FAILURE_AUDIT" in require_success_error

        production_after = database_state(DB)
        assert production_after == production_before

        gates = {
            "a18_blockers_understood": True,
            "a19_temp_copy_remediation_validated": True,
            "archive_trigger_safe_rollback_independently_reproduced": True,
            "rollback_failure_transaction_reversion_independently_reproduced": True,
            "original_and_rollback_errors_exposed_together": True,
            "isolated_actual_runner_hot_end_zero": True,
            "isolated_idempotent_replay": True,
            "isolated_recovery_after_output_loss": True,
            "byte_preserving_bridge_in_same_flow": True,
            "fresh_complete_candidate_accounting": accounted == source_count,
            "fresh_zero_unobservable_rows": accounted == source_count,
            "fresh_exact_legacy_queue_parity": canonical(plan["hot_queue"]) == canonical(legacy_queue),
            "fresh_prospective_batch_is_distinct": prospective_uid != existing_uid,
            "fresh_source_within_bound": source_count <= MAX_SOURCE_ROWS,
            "production_database_unchanged": production_after == production_before,
            "production_writer_default_off": environment["writer_enabled"] is False,
            "production_runtime_overrides_absent": (
                environment["runner_lock_enabled"] is False
                and environment["hot_override_enabled"] is False
                and environment["canary_mode_enabled"] is False
            ),
        }
        assert all(gates.values())

        timestamp = utc_now()
        artifact = {
            "schema_version": "1.0",
            "work_unit": WORK_UNIT,
            "timestamp_utc": timestamp,
            "status": "CLOSED_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED",
            "result": RESULT,
            "decision_gates": gates,
            "a19_evidence": {
                "artifact": str(A19.relative_to(ROOT)),
                "artifact_sha256": sha(A19),
                "rollback_guard_policy": ROLLBACK_POLICY,
                "isolated_first_writer_status": isolated["first_writer_status"],
                "isolated_second_writer_status": isolated["second_writer_status"],
                "isolated_hot_end_zero": isolated["hot_end_zero_proven"],
                "isolated_recovery_after_output_loss": isolated["recovery_after_output_loss"],
            },
            "independent_rollback_audit": {
                "rollback_guard_path": str(ROLLBACK_GUARD.relative_to(ROOT)),
                "rollback_guard_sha256": sha(ROLLBACK_GUARD),
                "success_result": rollback_success,
                "success_database_after": rollback_success_state,
                "failure_result": rollback_failure,
                "failure_database_after": rollback_failure_state,
                "require_success_error": require_success_error,
            },
            "fresh_prospective_canary": {
                "snapshot_attempt": snapshot["attempt"],
                "snapshot_hashes": snapshot["hashes"],
                "existing_batch_uid": existing_uid,
                "prospective_batch_uid": prospective_uid,
                "prospective_batch_is_distinct": True,
                "source_candidate_count": source_count,
                "source_accounted": accounted,
                "unobservable_rows": 0,
                "legacy_queue_count": len(legacy_queue),
                "admitted_count": int(counts["admitted_count"]),
                "overflow_count": int(counts["overflow_count"]),
                "exact_legacy_object_parity": True,
                "exact_legacy_uid_order_parity": True,
            },
            "production_database_before": production_before,
            "production_database_after": production_after,
            "production_ledger_unchanged": True,
            "runtime_observation": {
                "service": service,
                "timer": timer,
                "environment": environment,
            },
            "authorization": {
                "one_post_remediation_production_canary_authorized": True,
                "new_production_canary_authorized": True,
                "second_production_canary_authorized": True,
                "general_production_writer_activation_authorized": False,
                "production_writer_active": False,
                "p0_f1_closed": False,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
            },
            "canary_execution_contract": {
                "one_full_runner_cycle_only": True,
                "existing_batch_uid_must_be_preserved": existing_uid,
                "prospective_batch_uid": prospective_uid,
                "maximum_new_batch_rows": 1,
                "expected_total_batch_rows_on_success": production_before["batch_rows"] + 1,
                "expected_new_ledger_rows": source_count,
                "expected_total_ledger_rows_on_success": production_before["ledger_rows"] + source_count,
                "maximum_source_rows": MAX_SOURCE_ROWS,
                "database_backup_required": True,
                "runtime_output_backups_required": True,
                "timer_pause_during_canary_required": True,
                "service_inactive_precondition_required": True,
                "runtime_only_systemd_dropin_required": True,
                "writer_enabled_for_canary": True,
                "runner_lock_enabled_for_canary": True,
                "one_shot_hot_wrapper_required": True,
                "byte_preserving_bridge_in_same_cycle_required": True,
                "postcommit_rollback_guard_required": True,
                "postcommit_rollback_guard_policy": ROLLBACK_POLICY,
                "rollback_only_new_batch_on_failure": True,
                "preserve_existing_batch_on_failure": True,
                "original_and_rollback_errors_must_be_exposed": True,
                "runner_order_must_end_hot_end_zero": True,
                "panel_hot_hash_parity_required": True,
                "dropin_removal_after_cycle_required": True,
                "timer_state_restore_required": True,
                "database_integrity_post_audit_required": True,
                "general_activation_after_canary": False,
            },
            "next_safe_step": NEXT,
        }
        dump(ARTIFACT, artifact)

        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            f"""# ERA55A20 Post-Remediation Audit and Production Canary Decision

- Status: `CLOSED_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED`
- Result: `{RESULT}`
- Independent archive-trigger rollback audit: `true`
- Independent rollback-failure transaction audit: `true`
- Original and rollback errors exposed together: `true`
- Isolated actual runner HOT_END:0: `true`
- Fresh source candidates: `{source_count}`
- Fresh source accounted: `{accounted}`
- Unobservable rows: `0`
- Existing batch UID: `{existing_uid}`
- Prospective batch UID: `{prospective_uid}`
- Prospective batch distinct: `true`
- One post-remediation production canary authorized: `true`
- General production activation authorized: `false`
- Production writer active: `false`
- P0 F1 closed: `false`
- Option B authorized: `false`
- Next safe step: `{NEXT}`
""",
            encoding="utf-8",
        )

        runtime = load(RUNTIME)
        current = runtime["current_state"]
        current.update(
            {
                "mode": "ERA55A20_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED",
                "runtime_status": "WORK_UNIT_CLOSED",
                "updated_at": timestamp,
                "last_action": {
                    "timestamp": timestamp,
                    "task": WORK_UNIT,
                    "result": RESULT,
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                },
                "active_work_unit": {
                    "id": WORK_UNIT,
                    "type": "ERA55_P0_POST_REMEDIATION_AUDIT_PRODUCTION_CANARY_DECISION",
                    "parent": "ERA55_RUNTIME_OPTIMIZATION",
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "status": artifact["status"],
                    "result": RESULT,
                    "production_mutation": False,
                    "next_step": NEXT,
                },
                "next_safe_step": {
                    "id": NEXT,
                    "type": "ERA55_P0_SINGLE_NATURAL_CYCLE_POST_REMEDIATION_CANARY_APPLY_POST_AUDIT",
                    "parent": "ERA55_RUNTIME_OPTIMIZATION",
                    "purpose": (
                        "Execute exactly one guarded post-remediation production runner cycle "
                        "with automatic rollback guard and complete post-audit."
                    ),
                    "human_authorization_required": True,
                    "one_post_remediation_production_canary_authorized": True,
                    "new_production_canary_authorized": True,
                    "second_production_canary_authorized": True,
                    "general_production_writer_activation_authorized": False,
                    "option_b_authorized": False,
                    "optimization_apply_authorized": False,
                    "status": "READY",
                },
                "current_problem": {
                    "code": "POST_REMEDIATION_PRODUCTION_CANARY_NOT_YET_EXECUTED",
                    "severity": "P0",
                    "evidence": str(ARTIFACT.relative_to(ROOT)),
                },
            }
        )
        runtime["current_work_unit"] = current["active_work_unit"]
        dump(RUNTIME, runtime)

        history = load(HISTORY)
        events = history.setdefault("events", [])
        event_id = "ERA55A20_POST_REMEDIATION_PRODUCTION_CANARY_DECISION_V1"
        if not any(
            isinstance(event, dict) and event.get("event_id") == event_id
            for event in events
        ):
            events.append(
                {
                    "event_id": event_id,
                    "timestamp_utc": timestamp,
                    "era": "ERA55",
                    "work_unit": WORK_UNIT,
                    "event": "POST_REMEDIATION_AUDIT_AND_PRODUCTION_CANARY_DECISION",
                    "status": artifact["status"],
                    "result": RESULT,
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "independent_rollback_audit": True,
                    "fresh_prospective_batch_distinct": True,
                    "source_candidate_count": source_count,
                    "unobservable_rows": 0,
                    "one_post_remediation_production_canary_authorized": True,
                    "general_production_activation_authorized": False,
                    "production_unchanged": True,
                    "p0_f1_closed": False,
                    "option_b_authorized": False,
                    "next_safe_step": NEXT,
                }
            )
        history["updated_at"] = timestamp
        history["updated_at_utc"] = timestamp
        dump(HISTORY, history)

        master = MASTER.read_text(encoding="utf-8")
        master = replace_section(
            master,
            "## 01 PROJECT STATUS",
            """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_P0_POST_REMEDIATION_CANARY_AUTHORIZED
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
CURRENT_STAGE=ERA55A_P0_POST_REMEDIATION_PRODUCTION_CANARY
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
ARCHIVE_TRIGGER_SAFE_ROLLBACK_INDEPENDENTLY_REPRODUCED=true
ROLLBACK_FAILURE_TRANSACTION_REVERSION_INDEPENDENTLY_REPRODUCED=true
FRESH_SOURCE_CANDIDATES={source_count}
FRESH_SOURCE_ACCOUNTED={accounted}
UNOBSERVABLE_ROWS=0
PROSPECTIVE_BATCH_DISTINCT=true
ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

Exactly one new guarded production canary is authorized. General production activation remains blocked.""",
        )
        master = replace_section(
            master,
            "## 03 LAST VERIFIED WORK",
            f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}""",
        )
        MASTER.write_text(master, encoding="utf-8")

        handoff = HANDOFF.read_text(encoding="utf-8")
        handoff = replace_section(
            handoff,
            "## 02 CURRENT CONTINUATION CHECKPOINT",
            f"""PROJECT_STATUS=ACTIVE_ERA55_P0_POST_REMEDIATION_CANARY_AUTHORIZED
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_POST_REMEDIATION_PRODUCTION_CANARY
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
ARCHIVE_TRIGGER_SAFE_ROLLBACK_INDEPENDENTLY_REPRODUCED=true
ROLLBACK_FAILURE_TRANSACTION_REVERSION_INDEPENDENTLY_REPRODUCED=true
FRESH_SOURCE_CANDIDATES={source_count}
FRESH_SOURCE_ACCOUNTED={accounted}
UNOBSERVABLE_ROWS=0
PROSPECTIVE_BATCH_DISTINCT=true
ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""",
        )
        handoff = replace_section(
            handoff,
            "## 03 LAST VERIFIED WORK",
            f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
PRODUCTION_MUTATION=false
CURRENT_PROBLEM=POST_REMEDIATION_PRODUCTION_CANARY_NOT_YET_EXECUTED""",
        )
        handoff = replace_section(
            handoff,
            "## 06 DO NOT REOPEN OR REPEAT",
            """- Do not rerun A9-A20 unless evidence is invalidated.
- Execute at most one A21 production canary cycle.
- Do not enable general production.
- Do not delete or mutate the valid A17 batch.
- Do not start Option B or close P0 F1.""",
        )
        handoff = replace_section(
            handoff,
            "## 07 ALLOWED NEXT DECISIONS",
            f"""- Rollback remediation: `INDEPENDENTLY_VALIDATED`.
- Fresh prospective batch: `DISTINCT_AND_FULLY_ACCOUNTED`.
- One post-remediation production canary: `AUTHORIZED_NOT_EXECUTED`.
- General production activation: `BLOCKED`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
        )
        handoff = replace_section(
            handoff,
            "## 08 NEXT SESSION EXECUTION RULE",
            """1. Confirm A21 and the exact one-cycle authorization.
2. Back up the production DB and all mutable runtime outputs.
3. Pause the timer and require the service to be inactive.
4. Install only a runtime systemd drop-in.
5. Execute one full runner cycle with writer, lock, byte-preserving bridge and rollback guard.
6. On post-commit failure, roll back only the new batch and expose both errors.
7. Remove all overrides and restore timer state.
8. Post-audit existing-batch preservation, new-batch accounting, DB integrity and panel parity.
9. Do not enable general production after A21.""",
        )
        HANDOFF.write_text(handoff, encoding="utf-8")

        almanac = ALMANAC.read_text(encoding="utf-8")
        marker = "## ERA55A_20 POST-REMEDIATION PRODUCTION CANARY DECISION"
        if marker not in almanac:
            ALMANAC.write_text(
                almanac.rstrip()
                + f"""

---

{marker}

- Status: `CLOSED_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED`
- Result: `{RESULT}`
- Independent rollback audit: `true`
- Fresh source candidates: `{source_count}`
- Unobservable rows: `0`
- Prospective batch distinct: `true`
- One production canary authorized: `true`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Option B authorized: `false`
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
        run(["git", "add", "-f", str(REPORT.relative_to(ROOT))])
        if not git("diff", "--cached", "--name-only"):
            raise RuntimeError("NO_STAGED_CHANGES")
        git("commit", "-m", SUBJECT)

        print("ERA55A20_CANARY_DECISION=SUCCESS")
        print("RESULT=" + RESULT)
        print("INDEPENDENT_ARCHIVE_TRIGGER_ROLLBACK_AUDIT=true")
        print("INDEPENDENT_ROLLBACK_FAILURE_REVERSION_AUDIT=true")
        print("ORIGINAL_AND_ROLLBACK_ERRORS_EXPOSED=true")
        print("ISOLATED_ACTUAL_RUNNER_HOT_END_ZERO=true")
        print("FRESH_SOURCE_CANDIDATES=" + str(source_count))
        print("FRESH_SOURCE_ACCOUNTED=" + str(accounted))
        print("UNOBSERVABLE_ROWS=0")
        print("EXISTING_BATCH_UID=" + existing_uid)
        print("PROSPECTIVE_BATCH_UID=" + prospective_uid)
        print("PROSPECTIVE_BATCH_DISTINCT=true")
        print("ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED=true")
        print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
        print("PRODUCTION_WRITER_ACTIVE=false")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print("PRODUCTION_LEDGER_UNCHANGED=true")
        print("NEXT_SAFE_STEP=" + NEXT)
        print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
        return 0
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
