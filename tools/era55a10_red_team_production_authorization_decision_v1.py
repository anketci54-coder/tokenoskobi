#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
EXPECTED_HEAD = "b434368a56289d65b68e618b69dbc53676ae00c0"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"
A10_ARTIFACT = (
    ROOT
    / "data/control/"
    "era55a10_p0_ledger_writer_remediation_proof_package_v1.json"
)
DECISION_ARTIFACT = (
    ROOT
    / "data/control/"
    "era55a10_red_team_production_authorization_decision_v1.json"
)
RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
HOT_RUNTIME = (
    ROOT
    / "tools/post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.py"
)
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
PROD_HOT_OUTPUT = (
    ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
)
PROD_RECOVERY_STATE = (
    ROOT / "runtime/state/news_ledger_recovery_state_v1.json"
)

NEXT_STEP = (
    "ERA55A_11_P0_RUNTIME_LEDGER_WRITER_MODULE_EXTRACTION_"
    "AND_TEMP_COPY_BINDING_TEST"
)
COMMIT_SUBJECT = (
    "ERA55A10_RED_TEAM_DECISION | BLOCK | RUNTIME_WRITER_NOT_BOUND"
)


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


def replace_section(
    text: str,
    heading: str,
    new_body: str,
) -> str:
    pattern = re.compile(
        rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND:{heading}")
    return text[: match.start()] + heading + "\n\n" + new_body.rstrip() + "\n" + text[match.end() :]


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
            "query_only": bool(
                conn.execute("PRAGMA query_only").fetchone()[0]
            ),
        }
    finally:
        conn.close()


def validate_a10(a10: dict[str, Any]) -> None:
    tests = a10["tests"]
    decision = a10["decision"]

    assert a10["status"] == "REMEDIATION_VALIDATED_REVIEW_PENDING"
    assert a10["production_unchanged"] is True
    assert tests["gate_1_fresh_process_recovery"]["pass"] is True
    assert tests["gate_2_natural_runner_trigger"]["pass"] is True
    assert tests["strict_single_instance_lock"]["pass"] is True
    assert tests["gate_3_fsync_durability"]["pass"] is True
    assert tests["gate_4_monotonic_output_protection"]["pass"] is True
    assert tests["gate_5_logical_rollback_runbook"]["pass"] is True
    assert tests["gate_6_json_contract_parity"]["pass"] is True
    assert tests["poison_pill_quarantine"]["pass"] is True
    assert tests["feature_flag_default_inactive"]["pass"] is True
    assert decision["production_writer_activation_authorized"] is False
    assert decision["real_natural_timer_writer_cycle_proven"] is False


def main() -> int:
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

    required = [
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
        A10_ARTIFACT,
        RUNNER,
        HOT_RUNTIME,
        DB,
    ]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)

    production_guard_before = {
        "database": file_guard(DB),
        "hot_output": file_guard(PROD_HOT_OUTPUT),
        "recovery_state": file_guard(PROD_RECOVERY_STATE),
    }
    db_before = production_db_state()

    a10 = load_json(A10_ARTIFACT)
    validate_a10(a10)

    runner_text = RUNNER.read_text(encoding="utf-8")
    hot_text = HOT_RUNTIME.read_text(encoding="utf-8")

    runner_has_recovery = "recover_committed_batch" in runner_text
    runner_has_ledger_insert = (
        "INSERT INTO news_disposition_batches_v2" in runner_text
        or "INSERT INTO news_disposition_ledger_v2" in runner_text
    )
    hot_has_ledger_insert = (
        "INSERT INTO news_disposition_batches_v2" in hot_text
        or "INSERT INTO news_disposition_ledger_v2" in hot_text
    )
    runtime_writer_module_candidates = [
        ROOT / "tools/news_disposition_ledger_writer_v1.py",
        ROOT / "tools/news_ledger_writer_v1.py",
        ROOT / "tools/hot_intelligence_disposition_ledger_writer_v1.py",
    ]
    existing_writer_modules = [
        str(path.relative_to(ROOT))
        for path in runtime_writer_module_candidates
        if path.exists()
    ]

    assert runner_has_recovery is True
    assert runner_has_ledger_insert is False
    assert hot_has_ledger_insert is False
    assert existing_writer_modules == []
    assert db_before["batch_rows"] == 0
    assert db_before["ledger_rows"] == 0
    assert db_before["integrity_check"] == "ok"
    assert db_before["quick_check"] == "ok"

    now = utc_now()
    decision_artifact = {
        "schema_version": "1.0",
        "work_unit": "ERA55A_10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION",
        "timestamp_utc": now,
        "status": "CLOSED_PRODUCTION_ACTIVATION_REJECTED",
        "result": "REJECT_PRODUCTION_ACTIVATION_RUNTIME_WRITER_NOT_BOUND",
        "a10_shield_proofs": {
            "fresh_process_recovery": True,
            "recovery_before_raw": True,
            "strict_single_instance_lock": True,
            "fsync_file_replace_directory": True,
            "monotonic_output_protection": True,
            "poison_pill_quarantine": True,
            "recovery_alerting": True,
            "json_contract_backward_compatible": True,
        },
        "runtime_gap": {
            "runner_has_recovery_guard": runner_has_recovery,
            "runner_has_new_ledger_batch_writer": runner_has_ledger_insert,
            "hot_runtime_has_new_ledger_batch_writer": hot_has_ledger_insert,
            "standalone_runtime_writer_modules": existing_writer_modules,
            "classification": "RECOVERY_PATH_PRESENT_WRITER_PATH_ABSENT",
            "meaning": (
                "Enabling the current feature flag can recover an already committed "
                "batch, but no runtime component creates a new production ledger batch."
            ),
        },
        "production_database": db_before,
        "authorization": {
            "bounded_canary_activation_authorized": False,
            "general_production_writer_activation_authorized": False,
            "production_writer_active": False,
            "p0_f1_closed": False,
            "option_b_authorized": False,
            "optimization_apply_authorized": False,
        },
        "a11_scope": {
            "id": NEXT_STEP,
            "temp_copy_only": True,
            "production_db_mutation": False,
            "service_timer_panel_mutation": False,
            "requirements": [
                "Extract or implement a reusable runtime disposition-ledger writer module.",
                "Bind it to the real hot candidate set before deduplication and truncation erase disposition evidence.",
                "Preserve the six-disposition reconciliation equation.",
                "Generate ledger batch plus backward-compatible hot output under the A10 recovery shields.",
                "Prove idempotent replay, replacement atomicity, lock, quarantine, fsync and monotonic output protection on a temp copy.",
                "Keep all production feature flags disabled.",
            ],
        },
        "next_safe_step": NEXT_STEP,
        "production_unchanged": True,
    }
    write_json(DECISION_ARTIFACT, decision_artifact)

    runtime = load_json(RUNTIME)
    current_state = runtime["current_state"]
    current_state["mode"] = "ERA55A10_PRODUCTION_ACTIVATION_REJECTED_WRITER_NOT_BOUND"
    current_state["runtime_status"] = "WORK_UNIT_CLOSED"
    current_state["updated_at"] = now
    current_state["last_action"] = {
        "timestamp": now,
        "task": "ERA55A_10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION",
        "result": "REJECT_PRODUCTION_ACTIVATION_RUNTIME_WRITER_NOT_BOUND",
        "artifact": str(DECISION_ARTIFACT.relative_to(ROOT)),
    }
    current_state["active_work_unit"] = {
        "id": "ERA55A_10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION",
        "type": "ERA55_P0_LEDGER_WRITER_PRODUCTION_AUTHORIZATION_DECISION",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "artifact": str(DECISION_ARTIFACT.relative_to(ROOT)),
        "status": "CLOSED_PRODUCTION_ACTIVATION_REJECTED",
        "result": "REJECT_PRODUCTION_ACTIVATION_RUNTIME_WRITER_NOT_BOUND",
        "production_mutation": False,
        "next_step": NEXT_STEP,
    }
    current_state["next_safe_step"] = {
        "id": NEXT_STEP,
        "type": "ERA55_P0_RUNTIME_LEDGER_WRITER_MODULE_EXTRACTION_TEMP_COPY_BINDING_TEST",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "purpose": (
            "Create the missing reusable runtime writer and prove its real candidate-set "
            "binding only on a disposable database copy."
        ),
        "temp_copy_required": True,
        "production_writer_activation_authorized": False,
        "option_b_authorized": False,
        "optimization_apply_authorized": False,
        "status": "READY",
    }
    current_state["current_problem"] = {
        "code": "RUNTIME_LEDGER_WRITER_MODULE_NOT_BOUND",
        "severity": "P0",
        "evidence": str(DECISION_ARTIFACT.relative_to(ROOT)),
    }
    runtime["current_work_unit"] = current_state["active_work_unit"]
    write_json(RUNTIME, runtime)

    history = load_json(HISTORY)
    events = history.setdefault("events", [])
    if not any(
        event.get("event_id") == "ERA55A10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION_V1"
        for event in events
        if isinstance(event, dict)
    ):
        events.append(
            {
                "event_id": "ERA55A10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION_V1",
                "timestamp_utc": now,
                "era": "ERA55",
                "work_unit": "ERA55A_10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION",
                "event": "PRODUCTION_AUTHORIZATION_DECISION",
                "status": "CLOSED_PRODUCTION_ACTIVATION_REJECTED",
                "result": "REJECT_PRODUCTION_ACTIVATION_RUNTIME_WRITER_NOT_BOUND",
                "artifact": str(DECISION_ARTIFACT.relative_to(ROOT)),
                "a10_shields_passed": True,
                "runtime_writer_bound": False,
                "production_unchanged": True,
                "production_writer_activation_authorized": False,
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
PROJECT_STATUS=ACTIVE_ERA55_P0_RUNTIME_LEDGER_WRITER_MODULE_REQUIRED
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
        """```text
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_RUNTIME_LEDGER_WRITER
LAST_COMPLETED_SUBSTEP=ERA55A_10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION
A10_REMEDIATION_SHIELDS_VALIDATED=true
RUNTIME_RECOVERY_PATH_PRESENT=true
RUNTIME_NEW_LEDGER_WRITER_BOUND=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
```

A10 shielding is valid, but production activation is rejected because the runtime can recover committed batches and cannot create a new ledger batch.""",
    )
    master = replace_section(
        master,
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED=ERA55A_10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION
LAST_RESULT=REJECT_PRODUCTION_ACTIVATION_RUNTIME_WRITER_NOT_BOUND
LAST_ARTIFACT={DECISION_ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS=CLOSED_PRODUCTION_ACTIVATION_REJECTED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
```

NEXT_SAFE_STEP={NEXT_STEP}""",
    )
    MASTER.write_text(master, encoding="utf-8")

    handoff = HANDOFF.read_text(encoding="utf-8")
    handoff = replace_section(
        handoff,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        f"""PROJECT_STATUS=ACTIVE_ERA55_P0_RUNTIME_LEDGER_WRITER_MODULE_REQUIRED
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_RUNTIME_LEDGER_WRITER
LAST_COMPLETED_SUBSTEP=ERA55A_10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION
A10_REMEDIATION_SHIELDS_VALIDATED=true
RUNTIME_RECOVERY_PATH_PRESENT=true
RUNTIME_NEW_LEDGER_WRITER_BOUND=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A10 production activation was rejected because the runtime writer path is absent. Only A11 temp-copy writer-module binding work is authorized.""",
    )
    handoff = replace_section(
        handoff,
        "## 03 LAST VERIFIED WORK",
        f"""LAST_COMPLETED=ERA55A_10_RED_TEAM_PRODUCTION_AUTHORIZATION_DECISION
LAST_RESULT=REJECT_PRODUCTION_ACTIVATION_RUNTIME_WRITER_NOT_BOUND
LAST_ARTIFACT={DECISION_ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS=CLOSED_PRODUCTION_ACTIVATION_REJECTED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=RUNTIME_LEDGER_WRITER_MODULE_NOT_BOUND""",
    )
    handoff = replace_section(
        handoff,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not rerun A9 or A10 remediation proofs unless their evidence is invalidated.
- Do not enable the production ledger writer flags.
- Do not treat the recovery guard as a ledger writer.
- Do not modify live DB, service, timer, gateway or panel during A11.
- Do not start Option B before the real runtime writer is bound and proven.
- Do not mark P0 F1 closed from temp-copy evidence.""",
    )
    handoff = replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- A10 shielding/remediation: `VALIDATED`.
- Production activation: `REJECTED_RUNTIME_WRITER_NOT_BOUND`.
- Recovery path: `PRESENT`.
- New ledger batch writer path: `ABSENT`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT_STEP}""",
    )
    handoff = replace_section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A11 is current.
2. Extract or implement one reusable runtime writer module from the A9-tested logic.
3. Bind it to the real hot candidate set before disposition evidence is lost.
4. Test only on a disposable DB copy with all production feature flags disabled.
5. Prove six-disposition accounting, idempotency, recovery, lock, quarantine, fsync and contract parity.
6. Do not activate production in A11.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac_entry = f"""

---

## ERA55A_10 RED TEAM PRODUCTION AUTHORIZATION DECISION

- Status: `CLOSED_PRODUCTION_ACTIVATION_REJECTED`
- Result: `REJECT_PRODUCTION_ACTIVATION_RUNTIME_WRITER_NOT_BOUND`
- A10 remediation shields: `PASS`
- Runtime recovery path: `PRESENT`
- Runtime new ledger writer path: `ABSENT`
- Production DB mutation: `false`
- Production writer activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `{NEXT_STEP}`
"""
    almanac = ALMANAC.read_text(encoding="utf-8")
    if "## ERA55A_10 RED TEAM PRODUCTION AUTHORIZATION DECISION" not in almanac:
        ALMANAC.write_text(almanac.rstrip() + almanac_entry + "\n", encoding="utf-8")

    production_guard_after = {
        "database": file_guard(DB),
        "hot_output": file_guard(PROD_HOT_OUTPUT),
        "recovery_state": file_guard(PROD_RECOVERY_STATE),
    }
    db_after = production_db_state()
    assert production_guard_before == production_guard_after
    assert db_before == db_after

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

    print("ERA55A10_RED_TEAM_DECISION=SUCCESS")
    print("DECISION=REJECT_PRODUCTION_ACTIVATION_RUNTIME_WRITER_NOT_BOUND")
    print("A10_SHIELDS_VALIDATED=true")
    print("RUNTIME_RECOVERY_PATH_PRESENT=true")
    print("RUNTIME_NEW_LEDGER_WRITER_BOUND=false")
    print("PRODUCTION_UNCHANGED=true")
    print("PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
    print("P0_F1_CLOSED=false")
    print("OPTION_B_AUTHORIZED=false")
    print("NEXT_SAFE_STEP=" + NEXT_STEP)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    print("ARTIFACT=" + str(DECISION_ARTIFACT.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
