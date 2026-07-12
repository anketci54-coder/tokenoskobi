#!/usr/bin/env python3
from __future__ import annotations

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
DROPIN = Path("/run/systemd/system/tokenoskobi-news-radar-refresh.service.d/90-era55a17-canary.conf")

A16 = ROOT / "data/control/era55a16_p0_queue_parity_post_test_audit_and_single_cycle_canary_decision_v1.json"
A17 = ROOT / "data/control/era55a17_p0_single_natural_cycle_bounded_canary_apply_and_post_audit_v1.json"
ARTIFACT = ROOT / "data/control/era55a18_p0_post_canary_red_team_production_activation_decision_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A18_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION.md"

RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
A17_TOOL = ROOT / "tools/era55a17_p0_single_natural_cycle_bounded_canary_apply_and_post_audit_v1.py"
BRIDGE = ROOT / "tools/news_active_panel_data_bridge_v1.py"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

WORK_UNIT = "ERA55A_18_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION"
RESULT = "REJECT_GENERAL_PRODUCTION_ACTIVATION_END_TO_END_SUCCESS_AND_AUTOMATIC_ROLLBACK_NOT_PROVEN"
NEXT = "ERA55A_19_P0_AUTOMATIC_ROLLBACK_AND_END_TO_END_SUCCESS_REMEDIATION_TEMP_COPY_TEST"
SUBJECT = "ERA55A18_RED_TEAM_DECISION | BLOCK | END_TO_END_AND_ROLLBACK_GAPS"


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
            ORDER BY rowid DESC
            LIMIT 1
            """
        ).fetchone()
        if batch is None:
            raise RuntimeError("A18_PRODUCTION_BATCH_MISSING")
        uid = str(batch[1])
        dispositions = {
            str(name): int(count)
            for name, count in conn.execute(
                """
                SELECT disposition, COUNT(*)
                FROM news_disposition_ledger_v2
                WHERE batch_uid=?
                GROUP BY disposition
                """,
                (uid,),
            ).fetchall()
        }
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
            "ledger_rows": int(
                conn.execute(
                    "SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?",
                    (uid,),
                ).fetchone()[0]
            ),
            "disposition_counts": dispositions,
        }
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
            "latest_batch": latest,
        }
    finally:
        conn.close()


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
        "canary_mode_enabled": "TOKENOSKOBI_A17_ONE_SHOT_HOT=1" in text,
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
        A16,
        A17,
        RUNNER,
        A17_TOOL,
        BRIDGE,
        HOT,
        PANEL_HOT,
        BRIDGE_STATE,
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
        raise RuntimeError("A18_ARTIFACT_ALREADY_EXISTS")
    if DROPIN.exists():
        raise RuntimeError("A18_RUNTIME_DROPIN_PRESENT")

    a16 = load(A16)
    a17 = load(A17)

    assert a16["authorization"]["single_natural_cycle_bounded_canary_authorized"] is True
    assert a16["authorization"]["general_production_writer_activation_authorized"] is False

    assert a17["status"] == (
        "CLOSED_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_"
        "OK_WITH_POST_COMMIT_BRIDGE_RECOVERY"
    )
    assert a17["result"] == (
        "OK_SINGLE_NATURAL_CYCLE_BOUNDED_CANARY_"
        "COMPLETED_POST_COMMIT_BRIDGE_RECOVERY"
    )

    failure = a17["failure_classification"]
    rollback = a17["rollback_observation"]
    cleanup = a17["runtime_cleanup"]
    recovery = a17["panel_bridge_recovery"]
    authorization = a17["authorization"]
    order = a17["failure_evidence"]["runner_order"]

    assert failure["runner_cycles_executed"] == 1
    assert failure["second_canary_cycle_executed"] is False
    assert failure["ledger_commit_completed"] is True
    assert failure["panel_bridge_failed_after_commit"] is True
    assert failure["source_candidate_count"] == 106
    assert failure["source_accounted"] == 106
    assert failure["unobservable_rows"] == 0
    assert order[-2:] == ["A17_PANEL_BRIDGE_END:2", "HOT_END:1"]
    assert "A17_ONE_SHOT_HOT_END:0" not in order
    assert "HOT_END:0" not in order

    assert rollback["automatic_rollback_expected_after_bridge_failure"] is True
    assert rollback["automatic_rollback_observed"] is False
    assert rollback["valid_committed_batch_preserved"] is True
    assert rollback["destructive_cleanup_performed"] is False

    assert recovery["bridge_decision"] == "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED"
    assert recovery["hash_match_all"] is True
    assert recovery["hot_unchanged_during_recovery"] is True
    assert recovery["panel_hot_converged"] is True

    assert cleanup["dropin_removed"] is True
    assert cleanup["writer_flag_disabled"] is True
    assert cleanup["runner_lock_flag_disabled"] is True
    assert cleanup["hot_override_disabled"] is True
    assert cleanup["canary_mode_disabled"] is True
    assert cleanup["service_failed_state_reset"] is True

    assert authorization["single_natural_cycle_bounded_canary_consumed"] is True
    assert authorization["second_canary_cycle_authorized"] is False
    assert authorization["general_production_writer_activation_authorized"] is False
    assert authorization["production_writer_active"] is False
    assert authorization["p0_f1_closed"] is False
    assert authorization["option_b_authorized"] is False

    database_before = database_state()
    latest = database_before["latest_batch"]
    assert database_before["batch_rows"] == 1
    assert database_before["ledger_rows"] == 106
    assert database_before["integrity_check"] == "ok"
    assert database_before["quick_check"] == "ok"
    assert database_before["foreign_key_check_rows"] == 0
    assert latest["batch_sequence"] == 1
    assert latest["source_candidate_count"] == 106
    assert latest["ledger_rows"] == 106
    assert latest["admitted_count"] == 50
    assert latest["overflow_count"] == 56
    assert sum(int(value) for value in latest["disposition_counts"].values()) == 106

    bridge_state = load(BRIDGE_STATE)
    assert bridge_state["decision"] == "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED"
    assert bridge_state["failures"] == []
    assert bridge_state["hash_match"]
    assert all(value is True for value in bridge_state["hash_match"].values())

    service = service_environment()
    timer = unit_state(TIMER)
    service_unit = unit_state(SERVICE)
    assert service["runner_bound"] is True
    assert service["writer_enabled"] is False
    assert service["runner_lock_enabled"] is False
    assert service["hot_override_enabled"] is False
    assert service["canary_mode_enabled"] is False
    assert timer["active"] == "active"
    assert timer["enabled"] == "enabled"
    assert service_unit["active"] in {"inactive", "failed"}

    blockers = [
        {
            "code": "AUTOMATIC_ROLLBACK_NOT_OBSERVED",
            "severity": "P0",
            "evidence": "A17 rollback expected true, observed false",
        },
        {
            "code": "END_TO_END_RUNNER_SUCCESS_NOT_PROVEN",
            "severity": "P0",
            "evidence": "A17 runner order ends A17_PANEL_BRIDGE_END:2 then HOT_END:1",
        },
        {
            "code": "POST_COMMIT_MANUAL_RECOVERY_REQUIRED",
            "severity": "P0",
            "evidence": "Panel bridge convergence required a separate recovery work unit",
        },
        {
            "code": "CLEAN_POST_FIX_NATURAL_CYCLE_NOT_PROVEN",
            "severity": "P0",
            "evidence": "No second canary cycle was authorized or executed after the bridge fix",
        },
    ]

    positive_evidence = {
        "one_canary_cycle_consumed": True,
        "ledger_batch_committed": True,
        "source_candidate_count": 106,
        "ledger_rows": 106,
        "unobservable_rows": 0,
        "queue_capacity": 50,
        "admitted_count": 50,
        "overflow_count": 56,
        "database_integrity_ok": True,
        "panel_bridge_recovered": True,
        "panel_hash_parity": True,
        "hot_unchanged_during_recovery": True,
        "runtime_overrides_removed": True,
        "timer_active_and_enabled": True,
    }

    decision = {
        "general_production_writer_activation_authorized": False,
        "production_writer_active": False,
        "new_canary_authorized": False,
        "second_canary_cycle_authorized": False,
        "p0_f1_closed": False,
        "option_b_authorized": False,
        "optimization_apply_authorized": False,
        "decision_basis": (
            "A valid ledger canary batch is necessary but not sufficient. "
            "General activation remains blocked until deterministic automatic rollback "
            "and clean end-to-end runner completion are proven."
        ),
    }

    database_after = database_state()
    assert database_after == database_before

    timestamp = utc_now()
    artifact = {
        "schema_version": "1.0",
        "work_unit": WORK_UNIT,
        "timestamp_utc": timestamp,
        "status": "CLOSED_GENERAL_PRODUCTION_ACTIVATION_REJECTED",
        "result": RESULT,
        "positive_canary_evidence": positive_evidence,
        "red_team_blockers": blockers,
        "decision": decision,
        "production_database_before": database_before,
        "production_database_after": database_after,
        "production_unchanged": True,
        "runtime_observation": {
            "service": service_unit,
            "timer": timer,
            "environment": service,
            "runtime_dropin_present": DROPIN.exists(),
        },
        "a19_scope": {
            "id": NEXT,
            "temp_copy_only": True,
            "production_db_mutation": False,
            "service_timer_panel_mutation": False,
            "new_canary_authorized": False,
            "requirements": [
                "Make post-commit failure handling preserve the original error and expose rollback result.",
                "Prove deterministic automatic rollback against archive triggers on a disposable database copy.",
                "Prove a clean end-to-end runner sequence ending HOT_END:0 in an isolated temp environment.",
                "Prove bridge byte-preserving copy inside the same isolated end-to-end flow.",
                "Prove idempotent replay and recovery after the rollback remediation.",
                "Keep all production feature flags and runtime overrides disabled.",
            ],
        },
        "next_safe_step": NEXT,
    }
    dump(ARTIFACT, artifact)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# ERA55A18 Post-Canary Red-Team Production Activation Decision

- Status: `CLOSED_GENERAL_PRODUCTION_ACTIVATION_REJECTED`
- Result: `{RESULT}`
- Valid canary batch: `true`
- Production batch rows: `1`
- Production ledger rows: `106`
- Unobservable rows: `0`
- Panel bridge recovered: `true`
- Automatic rollback observed: `false`
- End-to-end runner success proven: `false`
- Clean post-fix natural cycle proven: `false`
- General production writer activation authorized: `false`
- New canary authorized: `false`
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
            "mode": "ERA55A18_GENERAL_PRODUCTION_ACTIVATION_REJECTED",
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
                "type": "ERA55_P0_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "status": artifact["status"],
                "result": RESULT,
                "production_mutation": False,
                "next_step": NEXT,
            },
            "next_safe_step": {
                "id": NEXT,
                "type": "ERA55_P0_AUTOMATIC_ROLLBACK_END_TO_END_REMEDIATION_TEMP_COPY_TEST",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "purpose": (
                    "Repair and prove deterministic automatic rollback plus clean end-to-end "
                    "runner completion only on disposable copies."
                ),
                "temp_copy_required": True,
                "human_authorization_required": True,
                "new_canary_authorized": False,
                "second_canary_cycle_authorized": False,
                "general_production_writer_activation_authorized": False,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
                "status": "READY",
            },
            "current_problem": {
                "code": "AUTOMATIC_ROLLBACK_AND_END_TO_END_SUCCESS_NOT_PROVEN",
                "severity": "P0",
                "evidence": str(ARTIFACT.relative_to(ROOT)),
            },
        }
    )
    runtime["current_work_unit"] = current["active_work_unit"]
    dump(RUNTIME, runtime)

    history = load(HISTORY)
    events = history.setdefault("events", [])
    event_id = "ERA55A18_POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION_V1"
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
                "event": "POST_CANARY_RED_TEAM_PRODUCTION_ACTIVATION_DECISION",
                "status": artifact["status"],
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "valid_canary_batch": True,
                "automatic_rollback_observed": False,
                "end_to_end_runner_success_proven": False,
                "general_production_activation_authorized": False,
                "new_canary_authorized": False,
                "p0_f1_closed": False,
                "option_b_authorized": False,
                "production_unchanged": True,
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
PROJECT_STATUS=ACTIVE_ERA55_P0_ROLLBACK_END_TO_END_REMEDIATION_PENDING
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
CURRENT_STAGE=ERA55A_P0_ROLLBACK_END_TO_END_REMEDIATION
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
VALID_CANARY_BATCH=true
PRODUCTION_BATCH_ROWS=1
PRODUCTION_LEDGER_ROWS=106
UNOBSERVABLE_ROWS=0
PANEL_BRIDGE_RECOVERED=true
AUTOMATIC_ROLLBACK_OBSERVED=false
END_TO_END_RUNNER_SUCCESS_PROVEN=false
CLEAN_POST_FIX_NATURAL_CYCLE_PROVEN=false
NEW_CANARY_AUTHORIZED=false
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

A valid canary batch exists, but general activation is blocked by rollback and end-to-end completion gaps.""",
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
        f"""PROJECT_STATUS=ACTIVE_ERA55_P0_ROLLBACK_END_TO_END_REMEDIATION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_ROLLBACK_END_TO_END_REMEDIATION
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
VALID_CANARY_BATCH=true
PRODUCTION_BATCH_ROWS=1
PRODUCTION_LEDGER_ROWS=106
UNOBSERVABLE_ROWS=0
PANEL_BRIDGE_RECOVERED=true
AUTOMATIC_ROLLBACK_OBSERVED=false
END_TO_END_RUNNER_SUCCESS_PROVEN=false
CLEAN_POST_FIX_NATURAL_CYCLE_PROVEN=false
NEW_CANARY_AUTHORIZED=false
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
CURRENT_PROBLEM=AUTOMATIC_ROLLBACK_AND_END_TO_END_SUCCESS_NOT_PROVEN""",
    )
    handoff = replace_section(
        handoff,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not rerun A9-A18 unless evidence is invalidated.
- Do not execute another production canary.
- Do not delete the valid A17 batch.
- Do not enable the production writer.
- Do not start Option B or close P0 F1.""",
    )
    handoff = replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Valid canary ledger batch: `PRESERVED`.
- General production activation: `REJECTED`.
- New production canary: `NOT_AUTHORIZED`.
- Rollback and end-to-end remediation: `TEMP_COPY_ONLY`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff = replace_section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A19 is current.
2. Work only on disposable DB and runtime-state copies.
3. Repair deterministic automatic rollback and expose rollback failures.
4. Prove a clean isolated runner sequence ending HOT_END:0.
5. Keep all production flags disabled.
6. Do not authorize a new production canary from A19 alone.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac = ALMANAC.read_text(encoding="utf-8")
    marker = "## ERA55A_18 POST-CANARY RED-TEAM PRODUCTION DECISION"
    if marker not in almanac:
        ALMANAC.write_text(
            almanac.rstrip()
            + f"""

---

{marker}

- Status: `CLOSED_GENERAL_PRODUCTION_ACTIVATION_REJECTED`
- Result: `{RESULT}`
- Valid canary batch: `true`
- Automatic rollback observed: `false`
- End-to-end runner success proven: `false`
- General production activation authorized: `false`
- New canary authorized: `false`
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

    print("ERA55A18_RED_TEAM_DECISION=SUCCESS")
    print("RESULT=" + RESULT)
    print("VALID_CANARY_BATCH=true")
    print("PRODUCTION_BATCH_ROWS=1")
    print("PRODUCTION_LEDGER_ROWS=106")
    print("UNOBSERVABLE_ROWS=0")
    print("PANEL_BRIDGE_RECOVERED=true")
    print("AUTOMATIC_ROLLBACK_OBSERVED=false")
    print("END_TO_END_RUNNER_SUCCESS_PROVEN=false")
    print("CLEAN_POST_FIX_NATURAL_CYCLE_PROVEN=false")
    print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
    print("NEW_CANARY_AUTHORIZED=false")
    print("PRODUCTION_WRITER_ACTIVE=false")
    print("P0_F1_CLOSED=false")
    print("OPTION_B_AUTHORIZED=false")
    print("PRODUCTION_UNCHANGED=true")
    print("NEXT_SAFE_STEP=" + NEXT)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
