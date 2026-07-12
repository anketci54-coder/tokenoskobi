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
DROPIN = Path(
    "/run/systemd/system/"
    "tokenoskobi-news-radar-refresh.service.d/"
    "90-era55a17-canary.conf"
)

A16 = ROOT / "data/control/era55a16_p0_queue_parity_post_test_audit_and_single_cycle_canary_decision_v1.json"
ARTIFACT = ROOT / "data/control/era55a17r_p0_failed_panel_bridge_recovery_and_post_audit_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A17R_P0_FAILED_PANEL_BRIDGE_RECOVERY_AND_POST_AUDIT.md"

BRIDGE = ROOT / "tools/news_active_panel_data_bridge_v1.py"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
ORDER_LOG = Path("/run/tokenoskobi/era55a17_order.log")
INVOCATION_GUARD = Path("/run/tokenoskobi/era55a17_invocation.guard")
RESULT_PATH = Path("/run/tokenoskobi/era55a17_one_shot_result.json")

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

WORK_UNIT = "ERA55A_17R_P0_FAILED_PANEL_BRIDGE_RECOVERY_AND_POST_AUDIT"
RESULT = "OK_SINGLE_NATURAL_CYCLE_CANARY_RECOVERED_AND_POST_AUDITED"
NEXT = "ERA55A_18_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION"
SUBJECT = "ERA55A17R_RECOVERY | OK | PANEL_HASH_PARITY_RESTORED"
POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(
    args: list[str],
    *,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
        timeout=timeout,
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
        ],
        check=False,
    )
    text = completed.stdout
    return {
        "writer_enabled": "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text,
        "runner_lock_enabled": "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text,
        "hot_override_enabled": "TOKENOSKOBI_NEWS_HOT_PATH=" in text,
        "canary_mode_enabled": "TOKENOSKOBI_A17_ONE_SHOT_HOT=1" in text,
        "result": next(
            (
                line.split("=", 1)[1]
                for line in text.splitlines()
                if line.startswith("Result=")
            ),
            "",
        ),
        "exec_main_status": next(
            (
                line.split("=", 1)[1]
                for line in text.splitlines()
                if line.startswith("ExecMainStatus=")
            ),
            "",
        ),
    }


def database_evidence() -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        batch = connection.execute(
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
            raise RuntimeError("A17R_BATCH_MISSING")
        batch_uid = str(batch[1])
        ledger_rows = int(
            connection.execute(
                "SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?",
                (batch_uid,),
            ).fetchone()[0]
        )
        admitted_payloads = [
            json.loads(str(row[0]))
            for row in connection.execute(
                """
                SELECT payload_json
                FROM news_disposition_ledger_v2
                WHERE batch_uid=? AND disposition='ADMITTED'
                ORDER BY candidate_rank ASC, source_index ASC
                """,
                (batch_uid,),
            ).fetchall()
        ]
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
                (batch_uid,),
            ).fetchall()
        }
        total_batches = int(
            connection.execute(
                "SELECT COUNT(*) FROM news_disposition_batches_v2"
            ).fetchone()[0]
        )
        total_ledger = int(
            connection.execute(
                "SELECT COUNT(*) FROM news_disposition_ledger_v2"
            ).fetchone()[0]
        )
        return {
            "total_batch_rows": total_batches,
            "total_ledger_rows": total_ledger,
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
            "ledger_rows": ledger_rows,
            "admitted_payloads": admitted_payloads,
            "disposition_counts": dispositions,
            "integrity_check": str(
                connection.execute("PRAGMA integrity_check").fetchone()[0]
            ),
            "quick_check": str(
                connection.execute("PRAGMA quick_check").fetchone()[0]
            ),
            "foreign_key_check_rows": len(
                connection.execute("PRAGMA foreign_key_check").fetchall()
            ),
        }
    finally:
        connection.close()


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
        A16,
        BRIDGE,
        DB,
        HOT,
        BRIDGE_STATE,
        PANEL_HOT,
        ORDER_LOG,
        INVOCATION_GUARD,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    a16 = load(A16)
    assert a16["status"] == "CLOSED_SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED"
    assert a16["authorization"][
        "single_natural_cycle_bounded_canary_authorized"
    ] is True
    assert a16["authorization"][
        "general_production_writer_activation_authorized"
    ] is False

    order = ORDER_LOG.read_text(encoding="utf-8").splitlines()
    required = [
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
    positions = []
    for marker in required:
        if marker not in order:
            raise RuntimeError(f"A17R_ORDER_MARKER_MISSING:{marker}")
        positions.append(order.index(marker))
    assert positions == sorted(positions)
    assert order.count("A17_ONE_SHOT_HOT_START") == 1
    assert not RESULT_PATH.exists()

    before_bridge = load(BRIDGE_STATE)
    assert before_bridge["decision"] == "FAIL_NEWS_ACTIVE_PANEL_DATA_BRIDGE"
    assert before_bridge["failures"] == ["target_hash_mismatch"]
    assert before_bridge["hash_match"][
        "hot_intelligence_ingress_gateway_v1.json"
    ] is False

    evidence = database_evidence()
    assert evidence["total_batch_rows"] == 1
    assert evidence["batch_sequence"] == 1
    assert evidence["policy_version"] == POLICY
    assert evidence["queue_capacity"] == 50
    assert evidence["source_candidate_count"] == 106
    assert evidence["admitted_count"] == 50
    assert evidence["overflow_count"] == 56
    assert evidence["duplicate_removed_count"] == 0
    assert evidence["unsafe_filtered_count"] == 0
    assert evidence["invalid_candidate_count"] == 0
    assert evidence["replaced_count"] == 0
    assert evidence["ledger_rows"] == 106
    assert evidence["total_ledger_rows"] == 106
    assert evidence["disposition_counts"] == {
        "ADMITTED": 50,
        "OVERFLOW_TRUNCATED": 56,
    }
    assert evidence["integrity_check"] == "ok"
    assert evidence["quick_check"] == "ok"
    assert evidence["foreign_key_check_rows"] == 0

    hot = load(HOT)
    hot_queue = hot.get("hot_queue")
    assert isinstance(hot_queue, list)
    assert len(hot_queue) == 50
    assert hot.get("hot_queue_count") == 50
    assert canonical(evidence["admitted_payloads"]) == canonical(hot_queue)

    timer_before = unit_state(TIMER)
    service_before = unit_state(SERVICE)
    env_before = service_environment()
    assert timer_before["active"] == "active"
    assert timer_before["enabled"] == "enabled"
    assert service_before["active"] == "failed"
    assert env_before["writer_enabled"] is False
    assert env_before["runner_lock_enabled"] is False
    assert env_before["hot_override_enabled"] is False
    assert env_before["canary_mode_enabled"] is False
    assert not DROPIN.exists()

    run(["systemctl", "stop", TIMER], timeout=30)
    try:
        service_paused = unit_state(SERVICE)
        if service_paused["active"] not in {"inactive", "failed"}:
            raise RuntimeError("A17R_SERVICE_NOT_QUIESCENT")
        run(["systemctl", "reset-failed", SERVICE], check=False, timeout=30)

        bridge = run(
            [sys.executable, str(BRIDGE)],
            check=False,
            timeout=90,
        )
        if bridge.returncode != 0:
            raise RuntimeError(
                "A17R_BRIDGE_RECOVERY_FAILED:"
                + str(bridge.returncode)
                + ":"
                + bridge.stdout[-3000:]
                + ":"
                + bridge.stderr[-3000:]
            )

        after_bridge = load(BRIDGE_STATE)
        assert after_bridge["decision"] == "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED"
        assert after_bridge["failures"] == []
        assert after_bridge["hash_match"]
        assert all(value is True for value in after_bridge["hash_match"].values())
        assert sha(HOT) == sha(PANEL_HOT)

        evidence_after = database_evidence()
        assert evidence_after["batch_uid"] == evidence["batch_uid"]
        assert evidence_after["total_batch_rows"] == 1
        assert evidence_after["total_ledger_rows"] == 106
        assert evidence_after["integrity_check"] == "ok"
        assert evidence_after["quick_check"] == "ok"
        assert evidence_after["foreign_key_check_rows"] == 0
    finally:
        run(["systemctl", "start", TIMER], check=False, timeout=30)

    timer_after = unit_state(TIMER)
    service_after = unit_state(SERVICE)
    env_after = service_environment()
    assert timer_after["active"] == "active"
    assert timer_after["enabled"] == "enabled"
    assert service_after["active"] == "inactive"
    assert env_after["writer_enabled"] is False
    assert env_after["runner_lock_enabled"] is False
    assert env_after["hot_override_enabled"] is False
    assert env_after["canary_mode_enabled"] is False
    assert not DROPIN.exists()

    now = utc_now()
    artifact = {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "timestamp_utc": now,
        "status": "CLOSED_SINGLE_NATURAL_CYCLE_CANARY_RECOVERED_OK",
        "result": RESULT,
        "failure_classification": {
            "canary_core_write_completed": True,
            "runner_raw_stage_completed": True,
            "runner_derived_stage_completed": True,
            "original_hot_stage_completed": True,
            "ledger_commit_completed": True,
            "panel_bridge_failed": True,
            "panel_bridge_failure_reason": "BYTE_HASH_MISMATCH_AFTER_JSON_REFORMAT",
            "service_exit_failed": True,
            "canary_rerun_performed": False,
        },
        "original_order_log": order,
        "database_evidence": {
            key: value
            for key, value in evidence_after.items()
            if key != "admitted_payloads"
        },
        "ledger_hot_exact_object_parity": True,
        "ledger_hot_exact_uid_order_parity": True,
        "bridge_before": before_bridge,
        "bridge_recovery": {
            "rc": bridge.returncode,
            "stdout": bridge.stdout.strip(),
            "stderr": bridge.stderr.strip(),
            "decision": after_bridge["decision"],
            "failures": after_bridge["failures"],
            "hash_match": after_bridge["hash_match"],
            "hot_panel_sha256_match": sha(HOT) == sha(PANEL_HOT),
        },
        "runtime_cleanup": {
            "dropin_absent": not DROPIN.exists(),
            "writer_flag_disabled": not env_after["writer_enabled"],
            "runner_lock_flag_disabled": not env_after["runner_lock_enabled"],
            "hot_override_disabled": not env_after["hot_override_enabled"],
            "canary_mode_disabled": not env_after["canary_mode_enabled"],
            "service_failed_state_reset": service_after["active"] == "inactive",
            "timer_active_restored": timer_after["active"] == "active",
            "timer_enabled_preserved": timer_after["enabled"] == "enabled",
        },
        "authorization": {
            "single_natural_cycle_bounded_canary_authorized": False,
            "single_natural_cycle_bounded_canary_consumed": True,
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
                "# ERA55A17R Failed Panel Bridge Recovery and Post-Audit",
                "",
                "- Status: `CLOSED_SINGLE_NATURAL_CYCLE_CANARY_RECOVERED_OK`",
                f"- Result: `{RESULT}`",
                "- Canary rerun: `false`",
                "- Production batch rows: `1`",
                "- Production ledger rows: `106`",
                "- Admitted: `50`",
                "- Overflow: `56`",
                "- Ledger/Hot exact object parity: `true`",
                "- Ledger/Hot exact UID order parity: `true`",
                "- Panel bridge exact byte hash parity: `true`",
                "- Runtime overrides active: `false`",
                "- Timer active/enabled: `true`",
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
            "mode": "ERA55A17R_SINGLE_CYCLE_CANARY_RECOVERED_POST_AUDIT_OK",
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
                "type": "ERA55_P0_FAILED_PANEL_BRIDGE_RECOVERY_POST_AUDIT",
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
                "purpose": (
                    "Review the recovered one-cycle evidence and decide general "
                    "writer activation separately."
                ),
                "human_authorization_required": True,
                "single_cycle_bounded_canary_authorized": False,
                "single_cycle_bounded_canary_consumed": True,
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
    event_id = "ERA55A17R_FAILED_PANEL_BRIDGE_RECOVERY_V1"
    if not any(
        isinstance(event, dict) and event.get("event_id") == event_id
        for event in events
    ):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": now,
                "era": "ERA55",
                "work_unit": WORK_UNIT,
                "event": "FAILED_PANEL_BRIDGE_RECOVERY_AND_POST_AUDIT",
                "status": artifact["status"],
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "canary_rerun": False,
                "batch_rows": 1,
                "ledger_rows": 106,
                "source_candidate_count": 106,
                "admitted_count": 50,
                "overflow_count": 56,
                "unobservable_rows": 0,
                "ledger_hot_exact_parity": True,
                "panel_hash_parity": True,
                "runtime_overrides_removed": True,
                "timer_state_restored": True,
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
PRODUCTION_BATCH_ROWS=1
PRODUCTION_LEDGER_ROWS=106
SOURCE_CANDIDATES=106
ADMITTED_ROWS=50
OVERFLOW_ROWS=56
UNOBSERVABLE_ROWS=0
LEDGER_HOT_EXACT_OBJECT_PARITY=true
LEDGER_HOT_EXACT_UID_ORDER_PARITY=true
PANEL_HOT_HASH_PARITY=true
SINGLE_CYCLE_BOUNDED_CANARY_CONSUMED=true
CANARY_RERUN_PERFORMED=false
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

The panel bridge byte-copy defect was repaired without rerunning the canary.""",
    )
    master = replace_section(
        master,
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
SINGLE_NATURAL_CYCLE_CONSUMED=true
CANARY_RERUN=false
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
PRODUCTION_BATCH_ROWS=1
PRODUCTION_LEDGER_ROWS=106
SOURCE_CANDIDATES=106
ADMITTED_ROWS=50
OVERFLOW_ROWS=56
UNOBSERVABLE_ROWS=0
LEDGER_HOT_EXACT_OBJECT_PARITY=true
LEDGER_HOT_EXACT_UID_ORDER_PARITY=true
PANEL_HOT_HASH_PARITY=true
SINGLE_CYCLE_BOUNDED_CANARY_CONSUMED=true
CANARY_RERUN_PERFORMED=false
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
SINGLE_NATURAL_CYCLE_CONSUMED=true
CANARY_RERUN=false
RUNTIME_OVERRIDE_ACTIVE=false
CURRENT_PROBLEM=GENERAL_PRODUCTION_WRITER_ACTIVATION_NOT_AUTHORIZED""",
    )
    handoff = replace_section(
        handoff,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not rerun A9-A17R unless evidence is invalidated.
- Do not execute another bounded canary cycle.
- Do not re-enable writer, runner lock, or hot-path override.
- Do not authorize general production without A18.
- Do not start Option B or close P0 F1.""",
    )
    handoff = replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Complete accounting: `VALIDATED_PRODUCTION_CANARY`.
- Ledger/Hot exact parity: `VALIDATED_PRODUCTION_CANARY`.
- Panel exact byte hash parity: `RECOVERED_AND_VALIDATED`.
- One-cycle bounded canary: `COMPLETED_AND_CONSUMED`.
- General production activation: `BLOCKED_PENDING_A18`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff = replace_section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A18 is current.
2. Review A17R DB, ledger/hot parity, bridge recovery and cleanup evidence.
3. Decide general writer activation separately from canary recovery.
4. Do not run another canary.
5. Keep Option B blocked until the production decision is sealed.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac = ALMANAC.read_text(encoding="utf-8")
    marker = "## ERA55A_17R FAILED PANEL BRIDGE RECOVERY"
    if marker not in almanac:
        ALMANAC.write_text(
            almanac.rstrip()
            + f"""

---

{marker}

- Status: `CLOSED_SINGLE_NATURAL_CYCLE_CANARY_RECOVERED_OK`
- Result: `{RESULT}`
- Canary rerun: `false`
- Production batch rows: `1`
- Production ledger rows: `106`
- Source candidates: `106`
- Admitted: `50`
- Overflow: `56`
- Unobservable rows: `0`
- Ledger/Hot exact parity: `true`
- Panel hot byte-hash parity: `true`
- Runtime overrides removed: `true`
- Timer active/enabled: `true`
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
    run(
        ["git", "add", "-f", str(REPORT.relative_to(ROOT))],
        check=True,
    )
    if not git("diff", "--cached", "--name-only"):
        raise RuntimeError("NO_STAGED_CHANGES")
    git("commit", "-m", SUBJECT)

    for path in (ORDER_LOG, INVOCATION_GUARD, RESULT_PATH):
        if path.exists():
            path.unlink()

    print("ERA55A17R_RECOVERY=SUCCESS")
    print("RESULT=" + RESULT)
    print("CANARY_RERUN=false")
    print("PRODUCTION_BATCH_ROWS=1")
    print("PRODUCTION_LEDGER_ROWS=106")
    print("SOURCE_CANDIDATES=106")
    print("SOURCE_ACCOUNTED=106")
    print("ADMITTED_ROWS=50")
    print("OVERFLOW_ROWS=56")
    print("UNOBSERVABLE_ROWS=0")
    print("LEDGER_HOT_EXACT_OBJECT_PARITY=true")
    print("LEDGER_HOT_EXACT_UID_ORDER_PARITY=true")
    print("PANEL_HOT_HASH_PARITY=true")
    print("RUNTIME_DROPIN_ABSENT=true")
    print("RUNTIME_FLAGS_DISABLED=true")
    print("SERVICE_FAILED_STATE_RESET=true")
    print("TIMER_ACTIVE_ENABLED=true")
    print("SINGLE_CYCLE_BOUNDED_CANARY_CONSUMED=true")
    print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
    print("PRODUCTION_WRITER_ACTIVE=false")
    print("P0_F1_CLOSED=false")
    print("OPTION_B_AUTHORIZED=false")
    print("NEXT_SAFE_STEP=" + NEXT)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    print("ARTIFACT=" + str(ARTIFACT.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
