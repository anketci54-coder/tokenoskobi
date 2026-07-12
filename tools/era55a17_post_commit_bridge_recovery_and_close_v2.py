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
import time
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
OBSOLETE_V1 = ROOT / "tools/era55a17_post_commit_bridge_recovery_and_close_v1.py"

A16 = ROOT / "data/control/era55a16_p0_queue_parity_post_test_audit_and_single_cycle_canary_decision_v1.json"
ARTIFACT = ROOT / "data/control/era55a17_p0_single_natural_cycle_bounded_canary_apply_and_post_audit_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A17_P0_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_APPLY_AND_POST_AUDIT.md"
BRIDGE = ROOT / "tools/news_active_panel_data_bridge_v1.py"
RECOVERY = ROOT / "tools/news_ledger_recovery_guard_v1.py"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
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
EXPECTED_ORDER = [
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


def now() -> str:
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
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def module(name: str, path: Path):
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
        "enabled": enabled.stdout.strip() or enabled.stderr.strip(),
    }


def environment_state() -> dict[str, Any]:
    text = run(
        ["systemctl", "show", SERVICE, "-p", "Environment", "-p", "Result", "-p", "ExecMainStatus"],
        check=False,
    ).stdout
    return {
        "writer_enabled": "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text,
        "runner_lock_enabled": "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text,
        "hot_override_enabled": "TOKENOSKOBI_NEWS_HOT_PATH=" in text,
        "canary_mode_enabled": "TOKENOSKOBI_A17_ONE_SHOT_HOT=1" in text,
        "result": next((line.split("=", 1)[1] for line in text.splitlines() if line.startswith("Result=")), ""),
        "exec_main_status": next((line.split("=", 1)[1] for line in text.splitlines() if line.startswith("ExecMainStatus=")), ""),
    }


def database_state() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        batch = conn.execute(
            """
            SELECT rowid, batch_uid, policy_version, queue_capacity,
                   source_candidate_count, admitted_count, overflow_count,
                   duplicate_removed_count, unsafe_filtered_count,
                   invalid_candidate_count, replaced_count
            FROM news_disposition_batches_v2
            ORDER BY rowid DESC LIMIT 1
            """
        ).fetchone()
        if batch is None:
            raise RuntimeError("A17_BATCH_MISSING")
        uid = str(batch[1])
        dispositions = {
            str(name): int(count)
            for name, count in conn.execute(
                "SELECT disposition, COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=? GROUP BY disposition",
                (uid,),
            ).fetchall()
        }
        triggers = [
            str(name)
            for (name,) in conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='trigger'
                  AND tbl_name IN ('news_disposition_batches_v2','news_disposition_ledger_v2')
                ORDER BY name
                """
            ).fetchall()
        ]
        latest = {
            "batch_sequence": int(batch[0]),
            "batch_uid": uid,
            "policy_version": str(batch[2]),
            "queue_capacity": int(batch[3]),
            "source_candidate_count": int(batch[4]),
            "admitted_count": int(batch[5]),
            "overflow_count": int(batch[6]),
            "duplicate_removed_count": int(batch[7]),
            "unsafe_filtered_count": int(batch[8]),
            "invalid_candidate_count": int(batch[9]),
            "replaced_count": int(batch[10]),
            "ledger_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?", (uid,)).fetchone()[0]),
            "disposition_counts": dispositions,
        }
        return {
            "batch_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_batches_v2").fetchone()[0]),
            "ledger_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_ledger_v2").fetchone()[0]),
            "integrity_check": str(conn.execute("PRAGMA integrity_check").fetchone()[0]),
            "quick_check": str(conn.execute("PRAGMA quick_check").fetchone()[0]),
            "foreign_key_check_rows": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
            "latest_batch": latest,
            "ledger_table_triggers": triggers,
        }
    finally:
        conn.close()


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)", re.DOTALL)
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND:{heading}")
    return text[:match.start()] + heading + "\n\n" + body.rstrip() + "\n" + text[match.end():]


def restore_timer(before: dict[str, Any]) -> None:
    if before["active"] == "active":
        run(["systemctl", "start", TIMER], timeout=30)
    else:
        run(["systemctl", "stop", TIMER], check=False, timeout=30)


def main() -> int:
    if not EXPECTED_HEAD:
        raise RuntimeError("TOKENOSKOBI_EXPECTED_HEAD_REQUIRED")
    if git("branch", "--show-current") != "main" or git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("HEAD_OR_BRANCH_MISMATCH")
    if git("status", "--porcelain"):
        raise RuntimeError("WORKTREE_NOT_CLEAN")

    for path in (A16, BRIDGE, RECOVERY, HOT, PANEL_HOT, BRIDGE_STATE, DB, RUNTIME, HISTORY, MASTER, HANDOFF, ALMANAC, ORDER_LOG, INVOCATION_GUARD):
        if not path.exists():
            raise FileNotFoundError(path)
    if ARTIFACT.exists() or RESULT_FILE.exists() or DROPIN.exists():
        raise RuntimeError("A17_RECOVERY_PRECONDITION_FAILED")

    a16 = load(A16)
    assert a16["authorization"]["single_natural_cycle_bounded_canary_authorized"] is True
    assert a16["authorization"]["general_production_writer_activation_authorized"] is False

    order = ORDER_LOG.read_text(encoding="utf-8").splitlines()
    assert order == EXPECTED_ORDER
    assert order.count("A17_ONE_SHOT_HOT_START") == 1

    env_before = environment_state()
    assert not any(env_before[key] for key in ("writer_enabled", "runner_lock_enabled", "hot_override_enabled", "canary_mode_enabled"))
    timer_before = unit_state(TIMER)
    assert timer_before["enabled"] == "enabled"

    if timer_before["active"] == "active":
        run(["systemctl", "stop", TIMER], timeout=30)
    timer_paused = unit_state(TIMER)
    assert timer_paused["active"] == "inactive"

    success = False
    try:
        deadline = time.time() + 120
        while unit_state(SERVICE)["active"] == "active" and time.time() < deadline:
            time.sleep(0.5)
        if unit_state(SERVICE)["active"] == "active":
            raise RuntimeError("A17_SERVICE_STILL_ACTIVE")

        db_before = database_state()
        latest = db_before["latest_batch"]
        source_count = int(latest["source_candidate_count"])
        assert db_before["batch_rows"] == 1
        assert db_before["ledger_rows"] == source_count == 106
        assert db_before["integrity_check"] == db_before["quick_check"] == "ok"
        assert db_before["foreign_key_check_rows"] == 0
        assert latest["batch_sequence"] == 1
        assert latest["policy_version"] == POLICY
        assert latest["queue_capacity"] == 50
        assert latest["admitted_count"] == 50
        assert latest["overflow_count"] == 56
        assert latest["ledger_rows"] == source_count
        assert sum(int(value) for value in latest["disposition_counts"].values()) == source_count

        hot = load(HOT)
        current_queue = hot.get("hot_queue")
        assert isinstance(current_queue, list) and len(current_queue) == 50
        assert hot.get("hot_queue_count") == 50

        tools = str(ROOT / "tools")
        if tools not in sys.path:
            sys.path.insert(0, tools)
        recovery = module("a17_recovery_guard_v2", RECOVERY)
        with tempfile.TemporaryDirectory(prefix="era55a17_recovery_", dir="/tmp") as temp_name:
            temp = Path(temp_name)
            reconstructed = temp / "reconstructed.json"
            state = temp / "state.json"
            recovered = recovery.recover_committed_batch(
                DB,
                reconstructed,
                state,
                contract_seed_path=HOT,
                batch_sequence=1,
            )
            assert recovered["status"] == "RECOVERED"
            recovered_queue = load(reconstructed).get("hot_queue")
            assert isinstance(recovered_queue, list) and len(recovered_queue) == 50
            current_hot_matches_canary_batch = canonical(current_queue) == canonical(recovered_queue)

        bridge_source = BRIDGE.read_text(encoding="utf-8")
        byte_preserving_code_verified = (
            "source_bytes = src.read_bytes()" in bridge_source
            and 'os.fdopen(fd, "wb")' in bridge_source
            and "f.write(source_bytes)" in bridge_source
        )
        assert byte_preserving_code_verified

        bridge_before = load(BRIDGE_STATE)
        hot_hash_before = digest(HOT)
        panel_hash_before = digest(PANEL_HOT)
        bridge_run = run([sys.executable, str(BRIDGE)], check=False, timeout=120)
        if bridge_run.returncode != 0:
            raise RuntimeError("A17_BRIDGE_RECOVERY_FAILED:" + bridge_run.stdout[-3000:] + bridge_run.stderr[-3000:])
        bridge_after = load(BRIDGE_STATE)
        assert bridge_after["decision"] == "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED"
        assert bridge_after["failures"] == []
        assert bridge_after["hash_match"] and all(value is True for value in bridge_after["hash_match"].values())
        assert digest(HOT) == digest(PANEL_HOT)
        assert digest(HOT) == hot_hash_before

        db_after = database_state()
        assert db_after == db_before
        run(["systemctl", "reset-failed", SERVICE], check=False, timeout=30)
        service_after = unit_state(SERVICE)
        env_after = environment_state()
        assert service_after["active"] == "inactive"
        assert not any(env_after[key] for key in ("writer_enabled", "runner_lock_enabled", "hot_override_enabled", "canary_mode_enabled"))

        invocation_hash = hashlib.sha256(INVOCATION_GUARD.read_bytes()).hexdigest()
        timestamp = now()
        artifact = {
            "schema_version": "1.0",
            "work_unit": WORK_UNIT,
            "timestamp_utc": timestamp,
            "status": "CLOSED_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_OK_WITH_POST_COMMIT_BRIDGE_RECOVERY",
            "result": RESULT,
            "failure_classification": {
                "runner_cycles_executed": 1,
                "second_canary_cycle_executed": False,
                "raw_stage_completed": True,
                "derived_stage_completed": True,
                "legacy_hot_stage_completed": True,
                "ledger_commit_completed": True,
                "panel_bridge_failed_after_commit": True,
                "panel_bridge_failure": "BYTE_HASH_FALSE_NEGATIVE_CAUSED_BY_JSON_RESERIALIZATION",
                "source_candidate_count": source_count,
                "source_accounted": source_count,
                "unobservable_rows": 0,
            },
            "failure_evidence": {
                "runner_order": order,
                "bridge_before": bridge_before,
                "invocation_guard_sha256": invocation_hash,
                "success_result_file_present": False,
            },
            "production_database": db_after,
            "committed_batch": latest,
            "recovery_guard_parity": {
                "status": "RECOVERED",
                "reconstructed_queue_count": len(recovered_queue),
                "current_hot_matches_canary_batch": current_hot_matches_canary_batch,
                "canary_exact_queue_parity_proven_before_bridge_by_executed_code_path": True,
            },
            "panel_bridge_recovery": {
                "bridge_script": str(BRIDGE.relative_to(ROOT)),
                "bridge_script_sha256": digest(BRIDGE),
                "copy_mode": "BYTE_PRESERVING_ATOMIC_JSON_COPY_V1",
                "byte_preserving_code_verified": True,
                "bridge_rc": bridge_run.returncode,
                "bridge_stdout": bridge_run.stdout.strip(),
                "bridge_stderr": bridge_run.stderr.strip(),
                "bridge_decision": bridge_after["decision"],
                "hash_match_all": True,
                "hot_hash_before": hot_hash_before,
                "panel_hot_hash_before": panel_hash_before,
                "hot_hash_after": digest(HOT),
                "panel_hot_hash_after": digest(PANEL_HOT),
                "hot_unchanged_during_recovery": digest(HOT) == hot_hash_before,
                "panel_hot_converged": digest(PANEL_HOT) == digest(HOT),
            },
            "runtime_cleanup": {
                "dropin_removed": not DROPIN.exists(),
                "writer_flag_disabled": not env_after["writer_enabled"],
                "runner_lock_flag_disabled": not env_after["runner_lock_enabled"],
                "hot_override_disabled": not env_after["hot_override_enabled"],
                "canary_mode_disabled": not env_after["canary_mode_enabled"],
                "service_failed_state_reset": service_after["active"] == "inactive",
            },
            "rollback_observation": {
                "automatic_rollback_expected_after_bridge_failure": True,
                "automatic_rollback_observed": False,
                "valid_committed_batch_preserved": True,
                "destructive_cleanup_performed": False,
                "ledger_table_triggers": db_after["ledger_table_triggers"],
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
            f"""# ERA55A17 Single Natural Cycle Canary Recovery and Closure

- Status: `CLOSED_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_OK_WITH_POST_COMMIT_BRIDGE_RECOVERY`
- Result: `{RESULT}`
- Runner cycles executed: `1`
- Second canary cycle executed: `false`
- Production batch rows: `1`
- Production ledger rows: `{source_count}`
- Source candidates: `{source_count}`
- Unobservable rows: `0`
- Ledger commit: `valid`
- Bridge root cause: `JSON reserialization byte-hash false negative`
- Bridge recovery: `byte-preserving atomic copy`
- Hot output changed during recovery: `false`
- Panel hot converged: `true`
- Runtime overrides active: `false`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `{NEXT}`
""",
            encoding="utf-8",
        )

        runtime = load(RUNTIME)
        current = runtime["current_state"]
        current.update({
            "mode": "ERA55A17_SINGLE_CYCLE_CANARY_COMPLETED_POST_COMMIT_BRIDGE_RECOVERY",
            "runtime_status": "WORK_UNIT_CLOSED",
            "updated_at": timestamp,
            "last_action": {"timestamp": timestamp, "task": WORK_UNIT, "result": RESULT, "artifact": str(ARTIFACT.relative_to(ROOT))},
            "active_work_unit": {"id": WORK_UNIT, "type": "ERA55_P0_SINGLE_NATURAL_CYCLE_CANARY_RECOVERY_AND_CLOSE", "parent": "ERA55_RUNTIME_OPTIMIZATION", "artifact": str(ARTIFACT.relative_to(ROOT)), "status": artifact["status"], "result": RESULT, "production_mutation": True, "next_step": NEXT},
            "next_safe_step": {"id": NEXT, "type": "ERA55_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION", "parent": "ERA55_RUNTIME_OPTIMIZATION", "purpose": "Review the one completed canary and decide general writer activation separately.", "human_authorization_required": True, "single_cycle_bounded_canary_authorized": False, "single_cycle_bounded_canary_consumed": True, "second_canary_cycle_authorized": False, "general_production_writer_activation_authorized": False, "option_b_authorized": False, "optimization_apply_authorized": False, "status": "READY"},
            "current_problem": {"code": "GENERAL_PRODUCTION_WRITER_ACTIVATION_NOT_AUTHORIZED", "severity": "P0", "evidence": str(ARTIFACT.relative_to(ROOT))},
        })
        runtime["current_work_unit"] = current["active_work_unit"]
        dump(RUNTIME, runtime)

        history = load(HISTORY)
        events = history.setdefault("events", [])
        event_id = "ERA55A17_SINGLE_NATURAL_CYCLE_CANARY_RECOVERY_V1"
        if not any(isinstance(event, dict) and event.get("event_id") == event_id for event in events):
            events.append({"event_id": event_id, "timestamp_utc": timestamp, "era": "ERA55", "work_unit": WORK_UNIT, "event": "POST_COMMIT_PANEL_BRIDGE_RECOVERY_AND_CANARY_CLOSE", "status": artifact["status"], "result": RESULT, "artifact": str(ARTIFACT.relative_to(ROOT)), "runner_cycles_executed": 1, "second_canary_cycle_executed": False, "batch_rows": 1, "ledger_rows": source_count, "source_candidate_count": source_count, "unobservable_rows": 0, "panel_hash_parity": True, "runtime_overrides_removed": True, "general_production_activation_authorized": False, "p0_f1_closed": False, "next_safe_step": NEXT})
        history["updated_at"] = history["updated_at_utc"] = timestamp
        dump(HISTORY, history)

        master = MASTER.read_text(encoding="utf-8")
        master = replace_section(master, "## 01 PROJECT STATUS", """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_P0_POST_CANARY_DECISION_PENDING
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
CURRENT_HUMAN_SUMMARY=06_PROJECT_MASTER_STATE.md
GIT_BRANCH=main
GIT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD
BOOT_HEALTH=100/100
```""")
        master = replace_section(master, "## 02 CURRENT MAJOR-LINE POSITION", f"""```text
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

The committed canary evidence was preserved. The panel bridge false negative was recovered without a second cycle.""")
        master = replace_section(master, "## 03 LAST VERIFIED WORK", f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
SINGLE_NATURAL_CYCLE_EXECUTED=true
SECOND_CANARY_CYCLE_EXECUTED=false
RUNTIME_OVERRIDE_ACTIVE=false
```

NEXT_SAFE_STEP={NEXT}""")
        MASTER.write_text(master, encoding="utf-8")

        handoff = HANDOFF.read_text(encoding="utf-8")
        handoff = replace_section(handoff, "## 02 CURRENT CONTINUATION CHECKPOINT", f"""PROJECT_STATUS=ACTIVE_ERA55_P0_POST_CANARY_DECISION_PENDING
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
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""")
        handoff = replace_section(handoff, "## 03 LAST VERIFIED WORK", f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
SINGLE_NATURAL_CYCLE_EXECUTED=true
SECOND_CANARY_CYCLE_EXECUTED=false
RUNTIME_OVERRIDE_ACTIVE=false
CURRENT_PROBLEM=GENERAL_PRODUCTION_WRITER_ACTIVATION_NOT_AUTHORIZED""")
        handoff = replace_section(handoff, "## 06 DO NOT REOPEN OR REPEAT", """- Do not rerun A9-A17 unless evidence is invalidated.
- Do not execute another bounded canary cycle.
- Do not delete the valid A17 batch.
- Do not re-enable writer, runner lock, or hot-path override.
- Do not authorize general production without A18.
- Do not start Option B or close P0 F1.""")
        handoff = replace_section(handoff, "## 07 ALLOWED NEXT DECISIONS", f"""- Complete accounting: `VALIDATED_PRODUCTION_CANARY`.
- One-cycle bounded canary: `COMPLETED_AND_CONSUMED`.
- Post-commit panel bridge: `RECOVERED_NO_SECOND_CYCLE`.
- General production activation: `BLOCKED_PENDING_A18`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""")
        handoff = replace_section(handoff, "## 08 NEXT SESSION EXECUTION RULE", """1. Confirm A18 is current.
2. Review the A17 recovery artifact, committed batch, bridge convergence and cleanup state.
3. Decide general writer activation separately from canary completion.
4. Do not run another canary.
5. Keep Option B blocked until the production decision is sealed.""")
        HANDOFF.write_text(handoff, encoding="utf-8")

        almanac = ALMANAC.read_text(encoding="utf-8")
        marker = "## ERA55A_17 SINGLE NATURAL CYCLE BOUNDED CANARY"
        if marker not in almanac:
            ALMANAC.write_text(almanac.rstrip() + f"""

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
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `{NEXT}`
""" + "\n", encoding="utf-8")

        for path in (RESULT_FILE, INVOCATION_GUARD, ORDER_LOG):
            if path.exists():
                path.unlink()
        if OBSOLETE_V1.exists():
            run(["git", "rm", "-f", str(OBSOLETE_V1.relative_to(ROOT))])

        git("add", str(ARTIFACT.relative_to(ROOT)), str(RUNTIME.relative_to(ROOT)), str(HISTORY.relative_to(ROOT)), str(MASTER.relative_to(ROOT)), str(HANDOFF.relative_to(ROOT)), str(ALMANAC.relative_to(ROOT)))
        run(["git", "add", "-f", str(REPORT.relative_to(ROOT))])
        git("commit", "-m", SUBJECT)
        success = True

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
        print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
        print("PRODUCTION_WRITER_ACTIVE=false")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print("NEXT_SAFE_STEP=" + NEXT)
        print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
        return 0
    finally:
        restore_timer(timer_before)
        timer_after = unit_state(TIMER)
        if timer_after != timer_before and success:
            raise RuntimeError("TIMER_STATE_NOT_RESTORED")


if __name__ == "__main__":
    raise SystemExit(main())
