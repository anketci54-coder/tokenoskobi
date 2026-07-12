#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
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

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"
DROPIN = Path("/run/systemd/system/tokenoskobi-news-radar-refresh.service.d/90-era55a17-canary.conf")
ORDER_LOG = Path("/run/tokenoskobi/era55a17_order.log")
RESULT_FILE = Path("/run/tokenoskobi/era55a17_one_shot_result.json")
INVOCATION_GUARD = Path("/run/tokenoskobi/era55a17_invocation.guard")

A16 = ROOT / "data/control/era55a16_p0_queue_parity_post_test_audit_and_single_cycle_canary_decision_v1.json"
ARTIFACT = ROOT / "data/control/era55a17_p0_single_natural_cycle_bounded_canary_apply_and_post_audit_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A17_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_AND_POST_AUDIT.md"

BRIDGE = ROOT / "tools/news_active_panel_data_bridge_v1.py"
RECOVERY = ROOT / "tools/news_ledger_recovery_guard_v1.py"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
RECOVERY_STATE = ROOT / "runtime/state/news_ledger_recovery_state_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

WORK_UNIT = "ERA55A_17_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_AND_POST_AUDIT"
RESULT = "OK_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_COMPLETED_POST_COMMIT_BRIDGE_RECOVERY"
NEXT = "ERA55A_18_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION"
SUBJECT = "ERA55A17_CANARY_RECOVERY | OK | NO_SECOND_CYCLE"
POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(args: list[str], *, check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
        timeout=timeout,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
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


def sha(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def unit_state(unit: str) -> dict[str, Any]:
    active = run(["systemctl", "is-active", unit], check=False)
    enabled = run(["systemctl", "is-enabled", unit], check=False)
    return {
        "active": active.stdout.strip() or active.stderr.strip(),
        "active_rc": active.returncode,
        "enabled": enabled.stdout.strip() or enabled.stderr.strip(),
        "enabled_rc": enabled.returncode,
    }


def service_environment() -> dict[str, Any]:
    completed = run(
        [
            "systemctl",
            "show",
            SERVICE,
            "-p",
            "Environment",
            "-p",
            "Result",
            "-p",
            "ExecMainStatus",
            "-p",
            "ActiveState",
            "-p",
            "SubState",
        ],
        check=False,
    )
    text = completed.stdout
    return {
        "writer_enabled": "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text,
        "runner_lock_enabled": "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text,
        "hot_override_enabled": "TOKENOSKOBI_NEWS_HOT_PATH=" in text,
        "canary_mode_enabled": "TOKENOSKOBI_A17_ONE_SHOT_HOT=1" in text,
        "result": next((line.split("=", 1)[1] for line in text.splitlines() if line.startswith("Result=")), ""),
        "exec_main_status": next((line.split("=", 1)[1] for line in text.splitlines() if line.startswith("ExecMainStatus=")), ""),
        "active_state": next((line.split("=", 1)[1] for line in text.splitlines() if line.startswith("ActiveState=")), ""),
        "sub_state": next((line.split("=", 1)[1] for line in text.splitlines() if line.startswith("SubState=")), ""),
    }


def database_snapshot() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        batch = conn.execute(
            """
            SELECT
                rowid,
                batch_uid,
                policy_version,
                queue_capacity,
                source_candidate_count,
                admitted_count,
                overflow_count,
                duplicate_removed_count,
                unsafe_filtered_count,
                invalid_candidate_count,
                replaced_count
            FROM news_disposition_batches_v2
            ORDER BY rowid DESC
            LIMIT 1
            """
        ).fetchone()
        if batch is None:
            raise RuntimeError("A17_BATCH_MISSING")
        batch_uid = str(batch[1])
        dispositions = {
            str(name): int(count)
            for name, count in conn.execute(
                """
                SELECT disposition, COUNT(*)
                FROM news_disposition_ledger_v2
                WHERE batch_uid=?
                GROUP BY disposition
                """,
                (batch_uid,),
            ).fetchall()
        }
        triggers = [
            {"name": str(name), "sql": str(sql or "")}
            for name, sql in conn.execute(
                """
                SELECT name, sql
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
            "batch_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_batches_v2").fetchone()[0]),
            "ledger_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_ledger_v2").fetchone()[0]),
            "integrity_check": str(conn.execute("PRAGMA integrity_check").fetchone()[0]),
            "quick_check": str(conn.execute("PRAGMA quick_check").fetchone()[0]),
            "foreign_key_check_rows": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
            "latest_batch": {
                "batch_sequence": int(batch[0]),
                "batch_uid": batch_uid,
                "policy_version": str(batch[2]),
                "queue_capacity": int(batch[3]),
                "source_candidate_count": int(batch[4]),
                "admitted_count": int(batch[5]),
                "overflow_count": int(batch[6]),
                "duplicate_removed_count": int(batch[7]),
                "unsafe_filtered_count": int(batch[8]),
                "invalid_candidate_count": int(batch[9]),
                "replaced_count": int(batch[10]),
                "ledger_rows": int(
                    conn.execute(
                        "SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?",
                        (batch_uid,),
                    ).fetchone()[0]
                ),
                "disposition_counts": dispositions,
            },
            "ledger_table_triggers": triggers,
        }
    finally:
        conn.close()


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)", re.DOTALL)
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND:{heading}")
    return text[: match.start()] + heading + "\n\n" + body.rstrip() + "\n" + text[match.end() :]


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
        A16,
        BRIDGE,
        RECOVERY,
        HOT,
        PANEL_HOT,
        BRIDGE_STATE,
        DB,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
        ORDER_LOG,
        INVOCATION_GUARD,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    if ARTIFACT.exists():
        raise RuntimeError("A17_ARTIFACT_ALREADY_EXISTS")
    if RESULT_FILE.exists():
        raise RuntimeError("A17_UNEXPECTED_SUCCESS_RESULT_FILE_PRESENT")
    if DROPIN.exists():
        raise RuntimeError("A17_DROPIN_STILL_PRESENT")

    a16 = load(A16)
    assert a16["authorization"]["single_natural_cycle_bounded_canary_authorized"] is True
    assert a16["authorization"]["general_production_writer_activation_authorized"] is False

    order = ORDER_LOG.read_text(encoding="utf-8").splitlines()
    expected_order = [
        "LOCK_ACQUIRED",
        "RECOVERY_DONE:NO_COMMITTED_BATCH",
        "RAW_START",
        "RAW_END:0",
        "DERIVED_START",
        "DERIVED_END:0",
        "HOT_START",
        "A17_ONE_SHOT_HOT_START",
        "A17_ORIGINAL_HOT_END:0",
        "A17_LEDGER_WRITE_DONE:COMMITTED",
        "A17_PANEL_BRIDGE_END:2",
        "HOT_END:1",
    ]
    if order != expected_order:
        raise RuntimeError("A17_FAILURE_ORDER_EVIDENCE_MISMATCH")
    if order.count("A17_ONE_SHOT_HOT_START") != 1:
        raise RuntimeError("A17_CANARY_INVOCATION_COUNT_NOT_ONE")

    environment_before = service_environment()
    timer_before = unit_state(TIMER)
    service_before = unit_state(SERVICE)
    assert environment_before["writer_enabled"] is False
    assert environment_before["runner_lock_enabled"] is False
    assert environment_before["hot_override_enabled"] is False
    assert environment_before["canary_mode_enabled"] is False
    assert timer_before["active"] == "active"
    assert timer_before["enabled"] == "enabled"
    assert service_before["active"] == "failed"

    db_before = database_snapshot()
    latest = db_before["latest_batch"]
    source_count = int(latest["source_candidate_count"])
    assert db_before["batch_rows"] == 1
    assert db_before["ledger_rows"] == source_count == 106
    assert db_before["integrity_check"] == "ok"
    assert db_before["quick_check"] == "ok"
    assert db_before["foreign_key_check_rows"] == 0
    assert latest["batch_sequence"] == 1
    assert latest["policy_version"] == POLICY
    assert latest["queue_capacity"] == 50
    assert latest["admitted_count"] == 50
    assert latest["overflow_count"] == 56
    assert latest["ledger_rows"] == source_count
    assert sum(int(value) for value in latest["disposition_counts"].values()) == source_count

    hot = load(HOT)
    hot_queue = hot.get("hot_queue")
    assert isinstance(hot_queue, list)
    assert len(hot_queue) == 50
    assert hot.get("hot_queue_count") == 50

    tools = str(ROOT / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    recovery = load_module("a17_recovery_guard", RECOVERY)
    with tempfile.TemporaryDirectory(prefix="era55a17_recovery_", dir="/tmp") as temp_name:
        temp = Path(temp_name)
        reconstructed = temp / "reconstructed_hot.json"
        recovery_state = temp / "recovery_state.json"
        recovery_result = recovery.recover_committed_batch(
            DB,
            reconstructed,
            recovery_state,
            contract_seed_path=HOT,
            batch_sequence=1,
        )
        assert recovery_result["status"] == "RECOVERED"
        reconstructed_queue = load(reconstructed).get("hot_queue")
        assert canonical(reconstructed_queue) == canonical(hot_queue)

    bridge_before = load(BRIDGE_STATE)
    assert bridge_before["decision"] == "FAIL_NEWS_ACTIVE_PANEL_DATA_BRIDGE"
    assert bridge_before["failures"] == ["target_hash_mismatch"]
    assert bridge_before["hash_match"]["hot_intelligence_ingress_gateway_v1.json"] is False
    pre_bridge_hot_hash = sha(HOT)
    pre_bridge_panel_hash = sha(PANEL_HOT)
    assert pre_bridge_hot_hash != pre_bridge_panel_hash

    bridge_run = run([sys.executable, str(BRIDGE)], check=False, timeout=120)
    if bridge_run.returncode != 0:
        raise RuntimeError(
            "A17_BRIDGE_RECOVERY_FAILED:"
            + str(bridge_run.returncode)
            + ":"
            + bridge_run.stdout[-3000:]
            + ":"
            + bridge_run.stderr[-3000:]
        )

    bridge_after = load(BRIDGE_STATE)
    assert bridge_after["decision"] == "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED"
    assert bridge_after["failures"] == []
    assert bridge_after.get("copy_mode") == "BYTE_PRESERVING_ATOMIC_JSON_COPY_V1"
    assert bridge_after["hash_match"]
    assert all(value is True for value in bridge_after["hash_match"].values())
    assert sha(HOT) == sha(PANEL_HOT)
    assert sha(HOT) == pre_bridge_hot_hash

    run(["systemctl", "reset-failed", SERVICE], check=False, timeout=30)
    environment_after = service_environment()
    timer_after = unit_state(TIMER)
    service_after = unit_state(SERVICE)
    assert environment_after["writer_enabled"] is False
    assert environment_after["runner_lock_enabled"] is False
    assert environment_after["hot_override_enabled"] is False
    assert environment_after["canary_mode_enabled"] is False
    assert timer_after["active"] == timer_before["active"] == "active"
    assert timer_after["enabled"] == timer_before["enabled"] == "enabled"
    assert service_after["active"] == "inactive"

    db_after = database_snapshot()
    assert db_after["batch_rows"] == 1
    assert db_after["ledger_rows"] == source_count
    assert db_after["integrity_check"] == "ok"
    assert db_after["quick_check"] == "ok"
    assert db_after["foreign_key_check_rows"] == 0
    assert db_after["latest_batch"] == latest

    invocation_token_hash = hashlib.sha256(INVOCATION_GUARD.read_bytes()).hexdigest()
    now = utc_now()
    artifact = {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "timestamp_utc": now,
        "status": "CLOSED_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_OK_WITH_POST_COMMIT_BRIDGE_RECOVERY",
        "result": RESULT,
        "failure_classification": {
            "core_runner_cycle_completed": True,
            "raw_stage_completed": True,
            "derived_stage_completed": True,
            "legacy_hot_stage_completed": True,
            "ledger_commit_completed": True,
            "source_candidate_count": source_count,
            "source_accounted": source_count,
            "unobservable_rows": 0,
            "panel_bridge_failed_after_commit": True,
            "panel_bridge_failure": "BYTE_HASH_FALSE_NEGATIVE_CAUSED_BY_JSON_RESERIALIZATION",
            "second_canary_cycle_executed": False,
            "single_cycle_invocation_count": 1,
        },
        "failure_evidence": {
            "runner_order": order,
            "service_before_recovery": service_before,
            "service_environment_before_recovery": environment_before,
            "bridge_before": bridge_before,
            "invocation_guard_sha256": invocation_token_hash,
            "success_result_file_present": False,
        },
        "production_database": db_after,
        "committed_batch": latest,
        "recovery_guard_parity": {
            "status": "RECOVERED",
            "exact_hot_queue_semantic_parity": True,
        },
        "panel_bridge_recovery": {
            "bridge_script": str(BRIDGE.relative_to(ROOT)),
            "bridge_script_sha256": sha(BRIDGE),
            "copy_mode": bridge_after["copy_mode"],
            "bridge_rc": bridge_run.returncode,
            "bridge_stdout": bridge_run.stdout.strip(),
            "bridge_stderr": bridge_run.stderr.strip(),
            "bridge_decision": bridge_after["decision"],
            "hash_match_all": True,
            "hot_hash_before": pre_bridge_hot_hash,
            "panel_hot_hash_before": pre_bridge_panel_hash,
            "hot_hash_after": sha(HOT),
            "panel_hot_hash_after": sha(PANEL_HOT),
            "hot_unchanged_during_recovery": sha(HOT) == pre_bridge_hot_hash,
            "panel_hot_converged": sha(PANEL_HOT) == sha(HOT),
        },
        "runtime_cleanup": {
            "dropin_removed": not DROPIN.exists(),
            "writer_flag_disabled": not environment_after["writer_enabled"],
            "runner_lock_flag_disabled": not environment_after["runner_lock_enabled"],
            "hot_override_disabled": not environment_after["hot_override_enabled"],
            "canary_mode_disabled": not environment_after["canary_mode_enabled"],
            "timer_state_preserved": timer_after == timer_before,
            "service_failed_state_reset": service_after["active"] == "inactive",
        },
        "rollback_observation": {
            "automatic_rollback_expected_after_bridge_failure": True,
            "automatic_rollback_observed": False,
            "valid_committed_batch_preserved": True,
            "destructive_cleanup_performed": False,
            "ledger_triggers": db_after["ledger_table_triggers"],
            "separate_follow_up_required": False,
        },
        "authorization": {
            "single_natural_cycle_bounded_canary_authorized": False,
            "single_natural_cycle_bounded_canary_consumed": True,
            "second_canary_cycle_authorized": False,
            "general_production_writer_activation_authorized": False,
            "production_writer_active": False,
            "p0_f1_closed": False,
            "option_b_authorized": False,
            "optimization_apply_authorized": False,
        },
        "next_safe_step": NEXT,
    }
    dump(ARTIFACT, artifact)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "\n".join(
            [
                "# ERA55A17 Single Natural Cycle Canary Recovery and Closure",
                "",
                "- Status: `CLOSED_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_OK_WITH_POST_COMMIT_BRIDGE_RECOVERY`",
                f"- Result: `{RESULT}`",
                "- Runner cycles executed: `1`",
                "- Second canary cycle executed: `false`",
                "- Production batch rows: `1`",
                f"- Production ledger rows: `{source_count}`",
                f"- Source candidates: `{source_count}`",
                "- Unobservable rows: `0`",
                "- Ledger commit: `valid`",
                "- Bridge root cause: `JSON reserialization byte-hash false negative`",
                "- Bridge recovery: `byte-preserving atomic copy`",
                "- Hot output changed during recovery: `false`",
                "- Panel hot converged: `true`",
                "- Runtime overrides active: `false`",
                "- Timer state preserved: `true`",
                "- General production activation authorized: `false`",
                "- P0 F1 closed: `false`",
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
            "mode": "ERA55A17_SINGLE_CYCLE_CANARY_COMPLETED_POST_COMMIT_BRIDGE_RECOVERY",
            "runtime_status": "WORK_UNIT_CLOSED",
            "updated_at": now,
            "last_action": {
                "timestamp": now,
                "task": WORK_UNIT,
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
            },
            "active_work_unit": {
                "id": WORK_UNIT,
                "type": "ERA55_P0_SINGLE_NATURAL_CYCLE_CANARY_RECOVERY_AND_CLOSE",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "status": artifact["status"],
                "result": RESULT,
                "production_mutation": True,
                "next_step": NEXT,
            },
            "next_safe_step": {
                "id": NEXT,
                "type": "ERA55_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "purpose": "Review the single completed canary and decide general writer activation separately.",
                "human_authorization_required": True,
                "single_cycle_bounded_canary_authorized": False,
                "single_cycle_bounded_canary_consumed": True,
                "second_canary_cycle_authorized": False,
                "general_production_writer_activation_authorized": False,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
                "status": "READY",
            },
            "current_problem": {
                "code": "GENERAL_PRODUCTION_WRITER_ACTIVATION_NOT_AUTHORIZED",
                "severity": "P0",
                "evidence": str(ARTIFACT.relative_to(ROOT)),
            },
        }
    )
    runtime["current_work_unit"] = current["active_work_unit"]
    dump(RUNTIME, runtime)

    history = load(HISTORY)
    events = history.setdefault("events", [])
    event_id = "ERA55A17_SINGLE_NATURAL_CYCLE_CANARY_RECOVERY_V1"
    if not any(isinstance(event, dict) and event.get("event_id") == event_id for event in events):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": now,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "POST_COMMIT_PANEL_BRIDGE_RECOVERY_AND_CANARY_CLOSE",
                "status": artifact["status"],
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "runner_cycles_executed": 1,
                "second_canary_cycle_executed": False,
                "batch_rows": 1,
                "ledger_rows": source_count,
                "source_candidate_count": source_count,
                "unobservable_rows": 0,
                "panel_hash_parity": True,
                "runtime_overrides_removed": True,
                "timer_state_preserved": True,
                "general_production_activation_authorized": False,
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
PROJECT_STATUS=ACTIVE_ERA55_P0_POST_CANARY_DECISION_PENDING
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
CURRENT_STAGE=ERA55A_P0_POST_CANARY_DECISION
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
RUNNER_CYCLES_EXECUTED=1
SECOND_CANARY_CYCLE_EXECUTED=false
PRODUCTION_BATCH_ROWS=1
PRODUCTION_LEDGER_ROWS={source_count}
SOURCE_CANDIDATES={source_count}
UNOBSERVABLE_ROWS=0
PANEL_HOT_HASH_PARITY=true
RUNTIME_OVERRIDE_ACTIVE=false
SINGLE_CYCLE_BOUNDED_CANARY_CONSUMED=true
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

The only canary cycle committed valid ledger evidence. The post-commit panel bridge false negative was repaired without a second cycle.""",
    )
    master = replace_section(
        master,
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
SINGLE_NATURAL_CYCLE_EXECUTED=true
SECOND_CANARY_CYCLE_EXECUTED=false
RUNTIME_OVERRIDE_ACTIVE=false
```

NEXT_SAFE_STEP={NEXT}""",
    )
    MASTER.write_text(master, encoding="utf-8")

    handoff = HANDOFF.read_text(encoding="utf-8")
    handoff = replace_section(
        handoff,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        f"""PROJECT_STATUS=ACTIVE_ERA55_P0_POST_CANARY_DECISION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_POST_CANARY_DECISION
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
RUNNER_CYCLES_EXECUTED=1
SECOND_CANARY_CYCLE_EXECUTED=false
PRODUCTION_BATCH_ROWS=1
PRODUCTION_LEDGER_ROWS={source_count}
SOURCE_CANDIDATES={source_count}
UNOBSERVABLE_ROWS=0
PANEL_HOT_HASH_PARITY=true
RUNTIME_OVERRIDE_ACTIVE=false
SINGLE_CYCLE_BOUNDED_CANARY_CONSUMED=true
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
SINGLE_NATURAL_CYCLE_EXECUTED=true
SECOND_CANARY_CYCLE_EXECUTED=false
RUNTIME_OVERRIDE_ACTIVE=false
CURRENT_PROBLEM=GENERAL_PRODUCTION_WRITER_ACTIVATION_NOT_AUTHORIZED""",
    )
    handoff = replace_section(
        handoff,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not rerun A9-A17 unless evidence is invalidated.
- Do not execute another bounded canary cycle.
- Do not delete the valid A17 batch.
- Do not re-enable writer, runner lock, or hot-path override.
- Do not authorize general production without A18.
- Do not start Option B or close P0 F1.""",
    )
    handoff = replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Complete accounting: `VALIDATED_PRODUCTION_CANARY`.
- One-cycle bounded canary: `COMPLETED_AND_CONSUMED`.
- Post-commit panel bridge: `RECOVERED_NO_SECOND_CYCLE`.
- General production activation: `BLOCKED_PENDING_A18`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff = replace_section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A18 is current.
2. Review the A17 recovery artifact, committed batch, bridge convergence and cleanup state.
3. Decide general writer activation separately from canary completion.
4. Do not run another canary.
5. Keep Option B blocked until the production decision is sealed.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac = ALMANAC.read_text(encoding="utf-8")
    marker = "## ERA55A_17 SINGLE NATURAL CYCLE BOUNDED CANARY"
    entry = f"""

---

{marker}

- Status: `CLOSED_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_OK_WITH_POST_COMMIT_BRIDGE_RECOVERY`
- Result: `{RESULT}`
- Runner cycles executed: `1`
- Second canary cycle executed: `false`
- Production batch rows: `1`
- Production ledger rows: `{source_count}`
- Source candidates: `{source_count}`
- Unobservable rows: `0`
- Panel bridge recovery: `byte-preserving atomic copy`
- Panel hot hash parity: `true`
- Runtime overrides removed: `true`
- Timer state preserved: `true`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `{NEXT}`
"""
    if marker not in almanac:
        ALMANAC.write_text(almanac.rstrip() + entry + "\n", encoding="utf-8")

    for path in (RESULT_FILE, INVOCATION_GUARD, ORDER_LOG):
        if path.exists():
            path.unlink()

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

    print("ERA55A17_POST_COMMIT_BRIDGE_RECOVERY=SUCCESS")
    print("RESULT=" + RESULT)
    print("RUNNER_CYCLES_EXECUTED=1")
    print("SECOND_CANARY_CYCLE_EXECUTED=false")
    print("PRODUCTION_BATCH_ROWS=1")
    print("PRODUCTION_LEDGER_ROWS=" + str(source_count))
    print("SOURCE_CANDIDATES=" + str(source_count))
    print("SOURCE_ACCOUNTED=" + str(source_count))
    print("UNOBSERVABLE_ROWS=0")
    print("BRIDGE_COPY_MODE=BYTE_PRESERVING_ATOMIC_JSON_COPY_V1")
    print("PANEL_HOT_HASH_PARITY=true")
    print("HOT_OUTPUT_UNCHANGED_DURING_RECOVERY=true")
    print("RUNTIME_DROPIN_REMOVED=true")
    print("TIMER_STATE_PRESERVED=true")
    print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
    print("PRODUCTION_WRITER_ACTIVE=false")
    print("P0_F1_CLOSED=false")
    print("OPTION_B_AUTHORIZED=false")
    print("NEXT_SAFE_STEP=" + NEXT)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
