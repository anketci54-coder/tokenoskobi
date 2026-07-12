#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
sys.dont_write_bytecode = True
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
EXPECTED_HEAD = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

A19 = ROOT / "data/control/era55a19_p0_automatic_rollback_and_end_to_end_success_remediation_temp_copy_test_v1.json"
A20 = ROOT / "data/control/era55a20_p0_post_remediation_audit_and_production_canary_decision_v1.json"
A20R = ROOT / "data/control/era55a20r_p0_dynamic_batch_identity_authorization_correction_v1.json"
A21 = ROOT / "data/control/era55a21_p0_single_natural_cycle_post_remediation_canary_dynamic_identity_retry_and_post_audit_v2.json"
ARTIFACT = ROOT / "data/control/era55a22_p0_post_remediation_canary_red_team_general_production_activation_decision_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A22_P0_POST_REMEDIATION_CANARY_RED_TEAM_GENERAL_PRODUCTION_ACTIVATION_DECISION.md"

DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
ROLLBACK_GUARD = ROOT / "tools/news_disposition_postcommit_rollback_guard_v1.py"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

WORK_UNIT = "ERA55A_22_P0_POST_REMEDIATION_CANARY_RED_TEAM_GENERAL_PRODUCTION_ACTIVATION_DECISION"
RESULT = "OK_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVATION_APPLY_AUTHORIZED"
NEXT = "ERA55A_23_P0_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_APPLY_AND_POST_AUDIT"
SUBJECT = "ERA55A22_GENERAL_ACTIVATION_DECISION | OK | GUARDED_APPLY_AUTHORIZED"
LEDGER_POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"
ROLLBACK_POLICY = "POSTCOMMIT_ARCHIVE_TRIGGER_ROLLBACK_GUARD_V1"
BASELINE_UID = "batch_58401c9613b091aa251a130383ced8a5"
CANARY_UID = "batch_5b348d2eab80b2929c5ef5b66e407e46"


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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def database_state() -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only=ON")
        batches: list[dict[str, Any]] = []
        rows = connection.execute(
            """
            SELECT rowid AS batch_sequence, *
            FROM news_disposition_batches_v2
            ORDER BY rowid
            """
        ).fetchall()
        for row in rows:
            item = dict(row)
            uid = str(item["batch_uid"])
            ledger_rows = int(
                connection.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?",
                    (uid,),
                ).fetchone()[0]
            )
            dispositions = {
                str(name): int(count)
                for name, count in connection.execute(
                    """
                    SELECT disposition, COUNT(*)
                    FROM news_disposition_ledger_v2
                    WHERE batch_uid=?
                    GROUP BY disposition
                    ORDER BY disposition
                    """,
                    (uid,),
                ).fetchall()
            }
            batches.append(
                {
                    "batch_sequence": int(item["batch_sequence"]),
                    "batch_uid": uid,
                    "status": str(item["status"]),
                    "policy_version": str(item["policy_version"]),
                    "queue_capacity": int(item["queue_capacity"]),
                    "source_candidate_count": int(item["source_candidate_count"]),
                    "admitted_count": int(item["admitted_count"]),
                    "overflow_count": int(item["overflow_count"]),
                    "duplicate_removed_count": int(item["duplicate_removed_count"]),
                    "unsafe_filtered_count": int(item["unsafe_filtered_count"]),
                    "invalid_candidate_count": int(item["invalid_candidate_count"]),
                    "replaced_count": int(item["replaced_count"]),
                    "ledger_rows": ledger_rows,
                    "disposition_counts": dispositions,
                }
            )
        return {
            "batch_rows": len(batches),
            "ledger_rows": int(
                connection.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2"
                ).fetchone()[0]
            ),
            "batches": batches,
            "integrity_check": str(
                connection.execute("PRAGMA integrity_check").fetchone()[0]
            ),
            "quick_check": str(
                connection.execute("PRAGMA quick_check").fetchone()[0]
            ),
            "foreign_key_check_rows": len(
                connection.execute("PRAGMA foreign_key_check").fetchall()
            ),
            "triggers": [
                str(name)
                for (name,) in connection.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='trigger'
                      AND tbl_name IN (
                        'news_disposition_batches_v2',
                        'news_disposition_ledger_v2'
                      )
                    ORDER BY name
                    """
                ).fetchall()
            ],
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
        "a21_retry_enabled": "TOKENOSKOBI_A21_DYNAMIC_RETRY=1" in text,
    }


def production_guard() -> dict[str, Any]:
    return {
        "database_sha256": sha(DB),
        "database": database_state(),
        "hot_sha256": sha(HOT),
        "panel_hot_sha256": sha(PANEL_HOT),
        "bridge_state_sha256": sha(BRIDGE_STATE),
        "service": unit_state(SERVICE),
        "timer": unit_state(TIMER),
        "environment": service_environment(),
    }


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
        A19,
        A20,
        A20R,
        A21,
        DB,
        HOT,
        PANEL_HOT,
        BRIDGE_STATE,
        RUNNER,
        ROLLBACK_GUARD,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
    ):
        if not path.exists():
            raise FileNotFoundError(path)
    if ARTIFACT.exists():
        raise RuntimeError("A22_ARTIFACT_ALREADY_EXISTS")

    a19 = load(A19)
    a20 = load(A20)
    a20r = load(A20R)
    a21 = load(A21)

    assert a19["status"] == "CLOSED_TEMP_COPY_REMEDIATION_OK"
    assert a19["rollback_guard"]["policy_version"] == ROLLBACK_POLICY
    assert a19["rollback_guard"]["rollback_failure_transaction_reverted"] is True
    assert a19["isolated_end_to_end"]["hot_end_zero_proven"] is True
    assert a19["isolated_end_to_end"]["idempotent_replay"] is True
    assert a19["isolated_end_to_end"]["recovery_after_output_loss"] is True

    assert a20["status"] == "CLOSED_ONE_POST_REMEDIATION_PRODUCTION_CANARY_AUTHORIZED"
    assert a20["authorization"]["general_production_writer_activation_authorized"] is False
    assert a20r["status"] == "CLOSED_BOUNDED_DYNAMIC_BATCH_IDENTITY_AUTHORIZATION_CORRECTED"
    assert a20r["authorization"]["previous_failed_attempt_consumed_authorization"] is False
    assert a20r["authorization"]["additional_canary_after_retry_authorized"] is False

    assert a21["status"] == "CLOSED_POST_REMEDIATION_DYNAMIC_IDENTITY_SINGLE_CYCLE_CANARY_OK"
    assert a21["result"] == (
        "OK_POST_REMEDIATION_DYNAMIC_IDENTITY_"
        "SINGLE_CYCLE_PRODUCTION_CANARY_COMPLETED"
    )
    assert a21["baseline_batch_preserved"] is True
    assert a21["new_batch_only"] is True
    assert a21["runner_order_valid"] is True
    assert a21["runner_order"][-1] == "HOT_END:0"
    assert a21["runner_order"].count("A21_DYNAMIC_ONE_SHOT_START") == 1
    assert a21["one_shot_result"]["writer_status"] == "COMMITTED"
    assert a21["one_shot_result"]["bridge_rc"] == 0
    assert a21["one_shot_result"]["bridge_hash_match_all"] is True
    assert a21["one_shot_result"]["source_candidate_count"] == 107
    assert a21["one_shot_result"]["source_accounted"] == 107
    assert a21["one_shot_result"]["unobservable_rows"] == 0
    assert a21["one_shot_result"]["exact_legacy_object_parity"] is True
    assert a21["one_shot_result"]["exact_legacy_uid_order_parity"] is True
    assert a21["bounded_dynamic_identity"]["new_batch_uid_distinct"] is True
    assert a21["bounded_dynamic_identity"]["actual_new_batch_uid"] == CANARY_UID
    assert a21["rollback_protection"]["armed"] is True
    assert a21["rollback_protection"]["triggered"] is False
    assert a21["rollback_protection"]["policy_version"] == ROLLBACK_POLICY
    assert a21["runtime_cleanup"]["dropin_removed"] is True
    assert a21["runtime_cleanup"]["writer_flag_disabled"] is True
    assert a21["runtime_cleanup"]["runner_lock_flag_disabled"] is True
    assert a21["runtime_cleanup"]["hot_override_disabled"] is True
    assert a21["runtime_cleanup"]["retry_mode_disabled"] is True
    assert a21["runtime_cleanup"]["timer_state_restored"] is True
    assert a21["authorization"]["one_post_remediation_production_canary_retry_consumed"] is True
    assert a21["authorization"]["additional_canary_authorized"] is False
    assert a21["authorization"]["general_production_writer_activation_authorized"] is False

    guard_before = production_guard()
    database = guard_before["database"]
    assert database["batch_rows"] == 2
    assert database["ledger_rows"] == 213
    assert database["integrity_check"] == "ok"
    assert database["quick_check"] == "ok"
    assert database["foreign_key_check_rows"] == 0
    assert set(database["triggers"]) == {
        "trg_news_disposition_batch_archive_before_delete_v2",
        "trg_news_disposition_ledger_archive_before_delete_v2",
    }
    batch_map = {batch["batch_uid"]: batch for batch in database["batches"]}
    assert set(batch_map) == {BASELINE_UID, CANARY_UID}
    assert batch_map[BASELINE_UID]["batch_sequence"] == 1
    assert batch_map[BASELINE_UID]["status"] == "COMMITTED"
    assert batch_map[BASELINE_UID]["policy_version"] == LEDGER_POLICY
    assert batch_map[BASELINE_UID]["source_candidate_count"] == 106
    assert batch_map[BASELINE_UID]["ledger_rows"] == 106
    assert batch_map[CANARY_UID]["batch_sequence"] == 2
    assert batch_map[CANARY_UID]["status"] == "COMMITTED"
    assert batch_map[CANARY_UID]["policy_version"] == LEDGER_POLICY
    assert batch_map[CANARY_UID]["source_candidate_count"] == 107
    assert batch_map[CANARY_UID]["ledger_rows"] == 107
    assert sum(batch_map[CANARY_UID]["disposition_counts"].values()) == 107

    assert guard_before["hot_sha256"] == guard_before["panel_hot_sha256"]
    bridge = load(BRIDGE_STATE)
    assert bridge["decision"] == "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED"
    assert bridge["failures"] == []
    assert bridge["hash_match"]
    assert all(value is True for value in bridge["hash_match"].values())
    assert guard_before["timer"]["active"] == "active"
    assert guard_before["timer"]["enabled"] == "enabled"
    assert guard_before["environment"]["runner_bound"] is True
    assert guard_before["environment"]["writer_enabled"] is False
    assert guard_before["environment"]["runner_lock_enabled"] is False
    assert guard_before["environment"]["hot_override_enabled"] is False
    assert guard_before["environment"]["a21_retry_enabled"] is False

    decision_gates = {
        "temp_copy_archive_trigger_safe_rollback_proven": True,
        "temp_copy_rollback_failure_reversion_proven": True,
        "temp_copy_idempotent_replay_proven": True,
        "temp_copy_output_loss_recovery_proven": True,
        "real_service_dynamic_identity_canary_completed": True,
        "real_service_runner_hot_end_zero": True,
        "real_service_writer_commit_completed": True,
        "real_service_complete_source_accounting": True,
        "real_service_zero_unobservable_rows": True,
        "real_service_exact_legacy_queue_parity": True,
        "real_service_byte_preserving_panel_bridge": True,
        "baseline_batch_preserved": True,
        "new_batch_distinct_and_committed": True,
        "production_database_integrity_clean": True,
        "production_runtime_overrides_removed": True,
        "production_writer_currently_disabled": True,
        "timer_state_restored": True,
        "additional_canary_not_authorized": True,
    }
    assert all(decision_gates.values())

    authorization = {
        "guarded_general_production_writer_activation_apply_authorized": True,
        "general_production_writer_activation_authorized": True,
        "production_writer_active": False,
        "activation_apply_completed": False,
        "new_production_canary_authorized": False,
        "additional_canary_authorized": False,
        "p0_f1_closed": False,
        "option_b_authorized": False,
        "optimization_apply_authorized": False,
    }

    activation_contract = {
        "apply_work_unit": NEXT,
        "persistent_runtime_integration_required": True,
        "one_shot_canary_wrapper_forbidden": True,
        "bounded_dynamic_batch_identity_required": True,
        "batch_uid_computed_after_natural_refresh": True,
        "batch_uid_must_differ_from_all_existing_committed_batches": True,
        "source_candidate_minimum": 1,
        "source_candidate_maximum": 5000,
        "complete_source_accounting_required": True,
        "unobservable_rows_must_equal": 0,
        "queue_capacity": 50,
        "exact_legacy_object_parity_required": True,
        "exact_legacy_uid_order_parity_required": True,
        "idempotent_replay_required": True,
        "output_loss_recovery_required": True,
        "runner_lock_required": True,
        "byte_preserving_panel_bridge_in_same_cycle_required": True,
        "postcommit_rollback_guard_required": True,
        "postcommit_rollback_guard_policy": ROLLBACK_POLICY,
        "rollback_scope_new_batch_only": True,
        "all_existing_committed_batches_must_be_preserved": True,
        "original_and_rollback_errors_must_be_exposed": True,
        "fail_closed_on_any_contract_violation": True,
        "configuration_backup_required": True,
        "database_backup_required": True,
        "runtime_output_backups_required": True,
        "timer_pause_during_apply_required": True,
        "service_inactive_precondition_required": True,
        "single_controlled_post_apply_service_cycle_required": True,
        "post_apply_cycle_must_end_hot_end_zero": True,
        "post_apply_database_integrity_required": True,
        "post_apply_panel_hot_hash_parity_required": True,
        "rollback_or_disable_on_post_apply_failure": True,
        "timer_state_restore_required": True,
        "permanent_writer_enablement_allowed_only_after_post_audit": True,
        "additional_canary_allowed": False,
        "option_b_allowed": False,
        "p0_f1_close_allowed_during_a23": False,
    }

    guard_after = production_guard()
    assert guard_after == guard_before

    timestamp = utc_now()
    artifact = {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "timestamp_utc": timestamp,
        "status": "CLOSED_GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY_AUTHORIZED",
        "result": RESULT,
        "decision_gates": decision_gates,
        "production_guard_before": guard_before,
        "production_guard_after": guard_after,
        "production_unchanged": True,
        "verified_batches": {
            "baseline_batch_uid": BASELINE_UID,
            "canary_batch_uid": CANARY_UID,
            "batch_rows": 2,
            "ledger_rows": 213,
        },
        "authorization": authorization,
        "activation_apply_contract": activation_contract,
        "next_safe_step": NEXT,
    }
    dump(ARTIFACT, artifact)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# ERA55A22 General Production Writer Activation Decision

- Status: `CLOSED_GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY_AUTHORIZED`
- Result: `{RESULT}`
- A19 rollback remediation validated: `true`
- A21 real service canary validated: `true`
- Production batch rows: `2`
- Production ledger rows: `213`
- Baseline batch preserved: `true`
- Dynamic canary batch committed: `true`
- Runner HOT_END:0: `true`
- Panel hash parity: `true`
- Guarded general activation apply authorized: `true`
- Production writer active now: `false`
- Additional canary authorized: `false`
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
            "mode": "ERA55A22_GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY_AUTHORIZED",
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
                "type": "ERA55_P0_GENERAL_PRODUCTION_ACTIVATION_RED_TEAM_DECISION",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "status": artifact["status"],
                "result": RESULT,
                "production_mutation": False,
                "next_step": NEXT,
            },
            "next_safe_step": {
                "id": NEXT,
                "type": "ERA55_P0_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_APPLY_POST_AUDIT",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "purpose": (
                    "Install the persistent guarded writer integration, run one controlled "
                    "post-apply service cycle, and retain enablement only after a clean audit."
                ),
                "human_authorization_required": True,
                "guarded_general_production_writer_activation_apply_authorized": True,
                "general_production_writer_activation_authorized": True,
                "production_writer_active": False,
                "additional_canary_authorized": False,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
                "status": "READY",
            },
            "current_problem": {
                "code": "GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_NOT_YET_APPLIED",
                "severity": "P0",
                "evidence": str(ARTIFACT.relative_to(ROOT)),
            },
        }
    )
    runtime["current_work_unit"] = current["active_work_unit"]
    dump(RUNTIME, runtime)

    history = load(HISTORY)
    events = history.setdefault("events", [])
    event_id = "ERA55A22_GENERAL_PRODUCTION_ACTIVATION_DECISION_V1"
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
                "event": "POST_REMEDIATION_CANARY_RED_TEAM_GENERAL_PRODUCTION_ACTIVATION_DECISION",
                "status": artifact["status"],
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "baseline_batch_uid": BASELINE_UID,
                "canary_batch_uid": CANARY_UID,
                "production_batch_rows": 2,
                "production_ledger_rows": 213,
                "guarded_general_activation_apply_authorized": True,
                "production_writer_active": False,
                "additional_canary_authorized": False,
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
PROJECT_STATUS=ACTIVE_ERA55_P0_GUARDED_GENERAL_ACTIVATION_APPLY_AUTHORIZED
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
CURRENT_STAGE=ERA55A_P0_GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_BATCH_ROWS=2
PRODUCTION_LEDGER_ROWS=213
BASELINE_BATCH_UID={BASELINE_UID}
CANARY_BATCH_UID={CANARY_UID}
BASELINE_BATCH_PRESERVED=true
DYNAMIC_CANARY_COMPLETED=true
RUNNER_HOT_END_ZERO=true
PANEL_HOT_HASH_PARITY=true
GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY_AUTHORIZED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=true
PRODUCTION_LEDGER_WRITER_ACTIVE=false
ADDITIONAL_CANARY_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

A23 may apply the persistent guarded writer integration. The writer is not active yet.""",
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
        f"""PROJECT_STATUS=ACTIVE_ERA55_P0_GUARDED_GENERAL_ACTIVATION_APPLY_AUTHORIZED
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
PRODUCTION_BATCH_ROWS=2
PRODUCTION_LEDGER_ROWS=213
BASELINE_BATCH_UID={BASELINE_UID}
CANARY_BATCH_UID={CANARY_UID}
BASELINE_BATCH_PRESERVED=true
DYNAMIC_CANARY_COMPLETED=true
RUNNER_HOT_END_ZERO=true
PANEL_HOT_HASH_PARITY=true
GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY_AUTHORIZED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=true
PRODUCTION_LEDGER_WRITER_ACTIVE=false
ADDITIONAL_CANARY_AUTHORIZED=false
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
CURRENT_PROBLEM=GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_NOT_YET_APPLIED""",
    )
    handoff = replace_section(
        handoff,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not rerun A9-A22 unless evidence is invalidated.
- Do not execute another production canary.
- Do not enable the writer outside the A23 guarded apply contract.
- Do not delete either valid committed production batch.
- Do not start Option B or close P0 F1 during A23.""",
    )
    handoff = replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- A21 dynamic production canary: `COMPLETED_AND_CONSUMED`.
- Guarded general writer apply: `AUTHORIZED_ONCE_IN_A23`.
- Production writer active now: `false`.
- Additional canary: `BLOCKED`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff = replace_section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A23 is current and A22 authorization is unused.
2. Back up production DB, runtime outputs and service configuration.
3. Install a persistent non-one-shot guarded writer integration.
4. Keep dynamic identity, complete accounting, runner lock and rollback guard mandatory.
5. Run one controlled post-apply service cycle ending HOT_END:0.
6. Preserve both existing committed batches.
7. Retain permanent enablement only after clean DB, panel, service and timer audits.
8. On any failure, disable the integration and restore configuration and data.
9. Keep Option B blocked and P0 F1 open.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac = ALMANAC.read_text(encoding="utf-8")
    marker = "## ERA55A_22 GENERAL PRODUCTION WRITER ACTIVATION DECISION"
    if marker not in almanac:
        ALMANAC.write_text(
            almanac.rstrip()
            + f"""

---

{marker}

- Status: `CLOSED_GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY_AUTHORIZED`
- Result: `{RESULT}`
- Production batch rows: `2`
- Production ledger rows: `213`
- Dynamic canary validated: `true`
- Guarded general activation apply authorized: `true`
- Production writer active now: `false`
- Additional canary authorized: `false`
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
        raise RuntimeError("A22_NO_STAGED_CHANGES")
    git("commit", "-m", SUBJECT)

    print("ERA55A22_GENERAL_ACTIVATION_DECISION=SUCCESS")
    print("RESULT=" + RESULT)
    print("PRODUCTION_BATCH_ROWS=2")
    print("PRODUCTION_LEDGER_ROWS=213")
    print("BASELINE_BATCH_PRESERVED=true")
    print("DYNAMIC_CANARY_VALIDATED=true")
    print("RUNNER_HOT_END_ZERO=true")
    print("PANEL_HOT_HASH_PARITY=true")
    print("GUARDED_GENERAL_PRODUCTION_ACTIVATION_APPLY_AUTHORIZED=true")
    print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=true")
    print("PRODUCTION_WRITER_ACTIVE=false")
    print("ADDITIONAL_CANARY_AUTHORIZED=false")
    print("P0_F1_CLOSED=false")
    print("OPTION_B_AUTHORIZED=false")
    print("PRODUCTION_UNCHANGED=true")
    print("NEXT_SAFE_STEP=" + NEXT)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
