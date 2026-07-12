#!/usr/bin/env python3
from __future__ import annotations

import atexit
import importlib.util
import json
import os
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
EXPECTED_HEAD = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()

WORK_UNIT = "ERA55A_24_P0_POST_ACTIVATION_OBSERVATION_AND_P0_F1_CLOSURE_DECISION"
RESULT = "OK_POST_ACTIVATION_NATURAL_TIMER_OBSERVATION_P0_F1_CLOSED"
NEXT = "ERA55A_25_P0_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION"
SUBJECT = "ERA55A24_POST_ACTIVATION_OBSERVATION | OK | P0_F1_CLOSED"
LEDGER_POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"
ROLLBACK_POLICY = "POSTCOMMIT_ARCHIVE_TRIGGER_ROLLBACK_GUARD_V1"
QUEUE_CAPACITY = 50
MAX_SOURCE_ROWS = 5000
MINIMUM_NATURAL_CYCLES = 1

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

BASE_TOOL = ROOT / "tools/era55a24_p0_post_activation_observation_and_p0_f1_closure_decision_v1.py"
A23 = ROOT / "data/control/era55a23_p0_guarded_general_production_writer_runtime_integration_apply_and_post_audit_v1.json"
ARTIFACT = ROOT / "data/control/era55a24_p0_post_activation_observation_and_p0_f1_closure_decision_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A24_P0_POST_ACTIVATION_OBSERVATION_AND_P0_F1_CLOSURE_DECISION.md"

DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
GUARDED_STATE = ROOT / "runtime/state/news_guarded_production_writer_v1.json"
RESULT_PATH = Path("/run/tokenoskobi/era55a23_guarded_result.json")
ERROR_PATH = Path("/run/tokenoskobi/era55a23_guarded_error.json")
ORDER_LOG = Path("/run/tokenoskobi/era55a23_guarded_order.log")
DROPIN = Path(
    "/etc/systemd/system/"
    "tokenoskobi-news-radar-refresh.service.d/"
    "90-era55a23-guarded-production.conf"
)

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"


def load_base():
    spec = importlib.util.spec_from_file_location("era55a24_base", BASE_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError("A24_BASE_TOOL_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load_base()


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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def journal_evidence(a23: dict[str, Any]) -> dict[str, Any]:
    boundary = datetime.fromisoformat(str(a23["apply_finished_at_utc"])) + timedelta(seconds=1)
    since = boundary.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    completed = run(
        [
            "journalctl",
            "-u",
            SERVICE,
            "--since",
            since,
            "--no-pager",
            "-o",
            "cat",
        ],
        check=False,
        timeout=60,
    )
    text = completed.stdout
    failure_needles = (
        "Failed with result 'exit-code'",
        "Failed to start tokenoskobi-news-radar-refresh.service",
        "status=1/FAILURE",
        "status=2/INVALIDARGUMENT",
        "Traceback (most recent call last)",
        "A23_GUARDED_PRODUCTION_CYCLE_FAILED",
    )
    failures = [needle for needle in failure_needles if needle in text]
    start_count = text.count(
        "Starting tokenoskobi-news-radar-refresh.service"
    )
    finish_count = text.count(
        "Finished tokenoskobi-news-radar-refresh.service"
    )
    deactivated_count = text.count(
        "tokenoskobi-news-radar-refresh.service: Deactivated successfully."
    )
    return {
        "rc": completed.returncode,
        "since": since,
        "start_count": start_count,
        "finish_count": finish_count,
        "deactivated_success_count": deactivated_count,
        "failure_markers": failures,
        "stdout_tail": text[-20000:],
        "stderr_tail": completed.stderr[-3000:],
    }


def order_evidence(a23: dict[str, Any]) -> dict[str, Any]:
    if not ORDER_LOG.exists():
        raise RuntimeError("A24_ORDER_LOG_MISSING")
    lines = ORDER_LOG.read_text(encoding="utf-8").splitlines()
    cycles = B.split_order_cycles(lines)
    if not cycles:
        raise RuntimeError("A24_ORDER_CYCLES_MISSING")
    if cycles[0] != a23["runner_order"]:
        raise RuntimeError("A24_CONTROLLED_CYCLE_ORDER_DRIFT")
    validated = [B.validate_order_cycle(cycle) for cycle in cycles]
    natural = validated[1:]
    if len(natural) < MINIMUM_NATURAL_CYCLES:
        raise RuntimeError("A24_NATURAL_CYCLE_COUNT_BELOW_MINIMUM")
    return {
        "lines": lines,
        "all_cycles": validated,
        "natural_cycles": natural,
        "natural_writer_statuses": [
            str(cycle["writer_status"])
            for cycle in natural
        ],
    }


def database_evidence(
    a23: dict[str, Any],
    order: dict[str, Any],
) -> dict[str, Any]:
    current = B.database_inventory(DB)
    if current["integrity_check"] != "ok":
        raise RuntimeError("A24_DATABASE_INTEGRITY_FAILED")
    if current["quick_check"] != "ok":
        raise RuntimeError("A24_DATABASE_QUICK_CHECK_FAILED")
    if current["foreign_key_check_rows"] != 0:
        raise RuntimeError("A24_DATABASE_FOREIGN_KEY_FAILED")
    if set(current["triggers"]) != {
        "trg_news_disposition_batch_archive_before_delete_v2",
        "trg_news_disposition_ledger_archive_before_delete_v2",
    }:
        raise RuntimeError("A24_DATABASE_TRIGGER_SET_DRIFT")

    original = a23["production_after"]
    original_map = B.batch_map(original)
    current_map = B.batch_map(current)
    for uid, batch in original_map.items():
        if current_map.get(uid) != batch:
            raise RuntimeError("A24_ORIGINAL_BATCH_MUTATED:" + uid)

    original_count = int(original["batch_rows"])
    extra_batches = current["batches"][original_count:]
    committed_cycle_count = order["natural_writer_statuses"].count("COMMITTED")
    replay_cycle_count = order["natural_writer_statuses"].count(
        "IDEMPOTENT_REPLAY_NOOP"
    )
    if len(extra_batches) != committed_cycle_count:
        raise RuntimeError(
            "A24_COMMITTED_CYCLE_DATABASE_BATCH_COUNT_MISMATCH:"
            + str(committed_cycle_count)
            + ":"
            + str(len(extra_batches))
        )

    expected_ledger_rows = int(original["ledger_rows"])
    for expected_sequence, batch in enumerate(
        current["batches"],
        start=1,
    ):
        if int(batch["batch_sequence"]) != expected_sequence:
            raise RuntimeError("A24_BATCH_SEQUENCE_GAP")
        if batch["status"] != "COMMITTED":
            raise RuntimeError("A24_BATCH_NOT_COMMITTED:" + batch["batch_uid"])
        if batch["policy_version"] != LEDGER_POLICY:
            raise RuntimeError("A24_BATCH_POLICY_DRIFT:" + batch["batch_uid"])
        if batch["queue_capacity"] != QUEUE_CAPACITY:
            raise RuntimeError("A24_BATCH_QUEUE_CAPACITY_DRIFT:" + batch["batch_uid"])
        source_count = int(batch["source_candidate_count"])
        if not (1 <= source_count <= MAX_SOURCE_ROWS):
            raise RuntimeError("A24_BATCH_SOURCE_BOUND_INVALID:" + batch["batch_uid"])
        if int(batch["ledger_rows"]) != source_count:
            raise RuntimeError("A24_BATCH_LEDGER_ACCOUNTING_FAILED:" + batch["batch_uid"])
        if sum(int(value) for value in batch["disposition_counts"].values()) != source_count:
            raise RuntimeError("A24_BATCH_DISPOSITION_ACCOUNTING_FAILED:" + batch["batch_uid"])

    expected_ledger_rows += sum(
        int(batch["source_candidate_count"])
        for batch in extra_batches
    )
    if int(current["ledger_rows"]) != expected_ledger_rows:
        raise RuntimeError("A24_FINAL_LEDGER_COUNT_MISMATCH")

    return {
        "inventory": current,
        "extra_batches": extra_batches,
        "committed_cycle_count": committed_cycle_count,
        "replay_cycle_count": replay_cycle_count,
    }


def latest_cycle_evidence(
    order: dict[str, Any],
    database: dict[str, Any],
) -> dict[str, Any]:
    if not RESULT_PATH.exists():
        raise RuntimeError("A24_LATEST_RESULT_MISSING")
    result = B.load(RESULT_PATH)
    guarded = B.load(GUARDED_STATE)
    if B.canonical(result) != B.canonical(guarded):
        raise RuntimeError("A24_RESULT_GUARDED_STATE_PARITY_FAILED")
    if result.get("status") != "OK_A23_GUARDED_PRODUCTION_CYCLE_COMPLETED":
        raise RuntimeError("A24_LATEST_RESULT_STATUS_INVALID")
    expected_status = order["natural_writer_statuses"][-1]
    if result.get("writer_status") != expected_status:
        raise RuntimeError("A24_LATEST_RESULT_ORDER_STATUS_MISMATCH")
    source_count = int(result.get("source_candidate_count", -1))
    if not (1 <= source_count <= MAX_SOURCE_ROWS):
        raise RuntimeError("A24_LATEST_SOURCE_BOUND_INVALID")
    if int(result.get("source_accounted", -2)) != source_count:
        raise RuntimeError("A24_LATEST_SOURCE_ACCOUNTING_FAILED")
    if int(result.get("unobservable_rows", -1)) != 0:
        raise RuntimeError("A24_LATEST_UNOBSERVABLE_ROWS_NONZERO")
    if int(result.get("legacy_queue_count", 0)) != QUEUE_CAPACITY:
        raise RuntimeError("A24_LATEST_QUEUE_CAPACITY_INVALID")
    for key in (
        "existing_batches_preserved",
        "exact_legacy_object_parity",
        "exact_legacy_uid_order_parity",
        "bridge_hash_match_all",
    ):
        if result.get(key) is not True:
            raise RuntimeError("A24_LATEST_BOOLEAN_GATE_FAILED:" + key)
    if int(result.get("original_hot_rc", -1)) != 0:
        raise RuntimeError("A24_LATEST_ORIGINAL_HOT_FAILED")
    if int(result.get("bridge_rc", -1)) != 0:
        raise RuntimeError("A24_LATEST_BRIDGE_FAILED")
    if result.get("hot_output_sha256") != result.get("panel_hot_sha256"):
        raise RuntimeError("A24_LATEST_PANEL_HASH_MISMATCH")
    rollback = result.get("rollback_guard")
    if not isinstance(rollback, dict):
        raise RuntimeError("A24_LATEST_ROLLBACK_GUARD_MISSING")
    if rollback.get("policy_version") != ROLLBACK_POLICY:
        raise RuntimeError("A24_LATEST_ROLLBACK_POLICY_INVALID")
    if rollback.get("armed") is not True or rollback.get("triggered") is not False:
        raise RuntimeError("A24_LATEST_ROLLBACK_STATE_INVALID")
    if rollback.get("scope") != "NEW_CURRENT_CYCLE_BATCH_ONLY":
        raise RuntimeError("A24_LATEST_ROLLBACK_SCOPE_INVALID")
    uid = str(result.get("actual_batch_uid", ""))
    current_map = B.batch_map(database["inventory"])
    if uid not in current_map:
        raise RuntimeError("A24_LATEST_BATCH_UID_NOT_IN_DATABASE")
    if result.get("active_batch") != current_map[uid]:
        raise RuntimeError("A24_LATEST_ACTIVE_BATCH_DATABASE_PARITY_FAILED")
    if ERROR_PATH.exists():
        error = B.load(ERROR_PATH)
        if error.get("status") == "A23_GUARDED_PRODUCTION_CYCLE_FAILED":
            raise RuntimeError("A24_ACTIVE_FAILURE_STATE_PRESENT")
    return result


def natural_cycle_summaries(
    order: dict[str, Any],
    database: dict[str, Any],
    latest: dict[str, Any],
) -> list[dict[str, Any]]:
    extra_iter = iter(database["extra_batches"])
    summaries: list[dict[str, Any]] = []
    total = len(order["natural_cycles"])
    for index, cycle in enumerate(order["natural_cycles"], start=1):
        writer_status = str(cycle["writer_status"])
        item: dict[str, Any] = {
            "natural_cycle_index": index,
            "writer_status": writer_status,
            "recovery_marker": cycle["recovery_marker"],
            "runner_hot_end_zero": True,
            "service_result_success": True,
            "complete_source_accounting_gate_passed": True,
            "zero_unobservable_rows_gate_passed": True,
            "exact_legacy_queue_parity_gate_passed": True,
            "panel_hash_parity_gate_passed": True,
            "rollback_guard_armed_gate_passed": True,
        }
        if writer_status == "COMMITTED":
            batch = next(extra_iter)
            item.update(
                {
                    "database_mutation": True,
                    "batch_uid": batch["batch_uid"],
                    "source_candidate_count": batch["source_candidate_count"],
                    "source_accounted": batch["ledger_rows"],
                }
            )
        else:
            item["database_mutation"] = False
            if index == total:
                item.update(
                    {
                        "batch_uid": latest["actual_batch_uid"],
                        "source_candidate_count": latest["source_candidate_count"],
                        "source_accounted": latest["source_accounted"],
                    }
                )
            else:
                item.update(
                    {
                        "batch_uid": None,
                        "source_candidate_count": None,
                        "source_accounted": None,
                    }
                )
        summaries.append(item)
    return summaries


def update_documents(
    artifact: dict[str, Any],
    natural_count: int,
    inventory: dict[str, Any],
    timestamp: str,
) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# ERA55A24 Post-Activation Observation and P0 F1 Closure

- Status: `CLOSED_POST_ACTIVATION_OBSERVATION_OK_P0_F1_CLOSED`
- Result: `{RESULT}`
- Evidence model: `SYSTEMD_SUCCESS_ORDER_LOG_DATABASE_PARITY_LATEST_RESULT`
- Forced service cycle: `false`
- Natural timer cycles observed: `{natural_count}`
- Committed natural cycles: `{artifact['committed_natural_cycle_count']}`
- Idempotent natural cycles: `{artifact['idempotent_natural_cycle_count']}`
- Production batch rows: `{inventory['batch_rows']}`
- Production ledger rows: `{inventory['ledger_rows']}`
- Original committed batches preserved: `true`
- Runner HOT_END:0: `true`
- Complete source accounting gates: `true`
- Unobservable rows: `0`
- Panel hash parity: `true`
- Rollback guard armed for every cycle: `true`
- Production writer active: `true`
- P0 F1 closed: `true`
- Option B authorized: `false`
- Next safe step: `{NEXT}`
""",
        encoding="utf-8",
    )

    runtime = B.load(RUNTIME)
    current = runtime["current_state"]
    current.update(
        {
            "mode": "ERA55A24_POST_ACTIVATION_OBSERVATION_P0_F1_CLOSED",
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
                "type": "ERA55_P0_POST_ACTIVATION_OBSERVATION_AND_P0_F1_CLOSURE_DECISION",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "status": artifact["status"],
                "result": RESULT,
                "production_mutation": False,
                "next_step": NEXT,
            },
            "next_safe_step": {
                "id": NEXT,
                "type": "ERA55_P0_OPTION_B_READINESS_AND_AUTHORIZATION_DECISION",
                "parent": "ERA55_RUNTIME_OPTIMIZATION",
                "purpose": (
                    "Decide Option B readiness and authorization after P0 F1 closure; "
                    "do not apply Option B in the decision step."
                ),
                "human_authorization_required": True,
                "production_writer_active": True,
                "p0_f1_closed": True,
                "option_b_readiness_decision_authorized": True,
                "option_b_authorized": False,
                "optimization_apply_authorized": False,
                "status": "READY",
            },
            "current_problem": {
                "code": "OPTION_B_READINESS_AND_AUTHORIZATION_DECISION_PENDING",
                "severity": "P1",
                "evidence": str(ARTIFACT.relative_to(ROOT)),
            },
        }
    )
    runtime["current_work_unit"] = current["active_work_unit"]
    B.atomic_dump(RUNTIME, runtime)

    history = B.load(HISTORY)
    events = history.setdefault("events", [])
    event_id = "ERA55A24_POST_ACTIVATION_OBSERVATION_P0_F1_CLOSED_V1"
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
                "event": "POST_ACTIVATION_NATURAL_TIMER_OBSERVATION_AND_P0_F1_CLOSURE",
                "status": artifact["status"],
                "result": RESULT,
                "artifact": str(ARTIFACT.relative_to(ROOT)),
                "evidence_model": artifact["evidence_model"],
                "natural_cycles_observed": natural_count,
                "committed_natural_cycles": artifact["committed_natural_cycle_count"],
                "idempotent_natural_cycles": artifact["idempotent_natural_cycle_count"],
                "production_batch_rows": inventory["batch_rows"],
                "production_ledger_rows": inventory["ledger_rows"],
                "original_batches_preserved": True,
                "production_writer_active": True,
                "p0_f1_closed": True,
                "option_b_authorized": False,
                "next_safe_step": NEXT,
            }
        )
    history["updated_at"] = timestamp
    history["updated_at_utc"] = timestamp
    B.atomic_dump(HISTORY, history)

    master = MASTER.read_text(encoding="utf-8")
    master = B.replace_section(
        master,
        "## 01 PROJECT STATUS",
        """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_P0_F1_CLOSED_OPTION_B_DECISION_PENDING
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
CURRENT_HUMAN_SUMMARY=06_PROJECT_MASTER_STATE.md
GIT_BRANCH=main
GIT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD
BOOT_HEALTH=100/100
```""",
    )
    master = B.replace_section(
        master,
        "## 02 CURRENT MAJOR-LINE POSITION",
        f"""```text
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_F1_CLOSED_OPTION_B_DECISION_PENDING
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
NATURAL_TIMER_CYCLES_OBSERVED={natural_count}
COMMITTED_NATURAL_CYCLES={artifact['committed_natural_cycle_count']}
IDEMPOTENT_NATURAL_CYCLES={artifact['idempotent_natural_cycle_count']}
PRODUCTION_BATCH_ROWS={inventory['batch_rows']}
PRODUCTION_LEDGER_ROWS={inventory['ledger_rows']}
ORIGINAL_BATCHES_PRESERVED=true
RUNNER_HOT_END_ZERO=true
COMPLETE_SOURCE_ACCOUNTING=true
UNOBSERVABLE_ROWS=0
PANEL_HOT_HASH_PARITY=true
ROLLBACK_GUARD_ARMED_FOR_EVERY_CYCLE=true
PRODUCTION_LEDGER_WRITER_ACTIVE=true
P0_F1_CLOSED=true
OPTION_B_READINESS_DECISION_AUTHORIZED=true
OPTION_B_AUTHORIZED=false
```

P0 F1 is closed. Option B remains blocked pending a separate readiness and authorization decision.""",
    )
    master = B.replace_section(
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
    handoff = B.replace_section(
        handoff,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        f"""PROJECT_STATUS=ACTIVE_ERA55_P0_F1_CLOSED_OPTION_B_DECISION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_F1_CLOSED_OPTION_B_DECISION_PENDING
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
NATURAL_TIMER_CYCLES_OBSERVED={natural_count}
COMMITTED_NATURAL_CYCLES={artifact['committed_natural_cycle_count']}
IDEMPOTENT_NATURAL_CYCLES={artifact['idempotent_natural_cycle_count']}
PRODUCTION_BATCH_ROWS={inventory['batch_rows']}
PRODUCTION_LEDGER_ROWS={inventory['ledger_rows']}
ORIGINAL_BATCHES_PRESERVED=true
RUNNER_HOT_END_ZERO=true
COMPLETE_SOURCE_ACCOUNTING=true
UNOBSERVABLE_ROWS=0
PANEL_HOT_HASH_PARITY=true
ROLLBACK_GUARD_ARMED_FOR_EVERY_CYCLE=true
PRODUCTION_LEDGER_WRITER_ACTIVE=true
ADDITIONAL_CANARY_AUTHORIZED=false
P0_F1_CLOSED=true
OPTION_B_READINESS_DECISION_AUTHORIZED=true
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""",
    )
    handoff = B.replace_section(
        handoff,
        "## 03 LAST VERIFIED WORK",
        f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
PRODUCTION_MUTATION=false
CURRENT_PROBLEM=OPTION_B_READINESS_AND_AUTHORIZATION_DECISION_PENDING""",
    )
    handoff = B.replace_section(
        handoff,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not rerun A9-A24 unless evidence is invalidated.
- Do not execute another canary.
- Do not remove or edit the A23 persistent integration without a rollback plan.
- Do not delete any valid committed production batch.
- Do not apply or authorize Option B inside A24.""",
    )
    handoff = B.replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Guarded production writer: `ACTIVE`.
- P0 F1: `CLOSED`.
- Additional canary: `BLOCKED`.
- Option B readiness decision: `AUTHORIZED`.
- Option B apply: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff = B.replace_section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A25 is current and A24 closure evidence remains valid.
2. Evaluate Option B scope, measurable benefit, safety, economy and rollback boundaries.
3. Do not apply Option B during the readiness decision.
4. Keep the guarded production writer active and unchanged.
5. Require explicit human authorization for any Option B apply step.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac = ALMANAC.read_text(encoding="utf-8")
    marker = "## ERA55A_24 POST-ACTIVATION OBSERVATION AND P0 F1 CLOSURE"
    if marker not in almanac:
        ALMANAC.write_text(
            almanac.rstrip()
            + f"""

---

{marker}

- Status: `CLOSED_POST_ACTIVATION_OBSERVATION_OK_P0_F1_CLOSED`
- Result: `{RESULT}`
- Evidence model: `SYSTEMD_SUCCESS_ORDER_LOG_DATABASE_PARITY_LATEST_RESULT`
- Forced service cycle: `false`
- Natural timer cycles observed: `{natural_count}`
- Committed natural cycles: `{artifact['committed_natural_cycle_count']}`
- Idempotent natural cycles: `{artifact['idempotent_natural_cycle_count']}`
- Production batch rows: `{inventory['batch_rows']}`
- Production ledger rows: `{inventory['ledger_rows']}`
- Original committed batches preserved: `true`
- Production writer active: `true`
- P0 F1 closed: `true`
- Option B authorized: `false`
- Next safe step: `{NEXT}`
"""
            + "\n",
            encoding="utf-8",
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
        BASE_TOOL,
        A23,
        DB,
        HOT,
        PANEL_HOT,
        BRIDGE_STATE,
        GUARDED_STATE,
        RESULT_PATH,
        ORDER_LOG,
        DROPIN,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
    ):
        if not path.exists():
            raise FileNotFoundError(path)
    if ARTIFACT.exists():
        raise RuntimeError("A24_ARTIFACT_ALREADY_EXISTS")

    a23 = B.load(A23)
    assert a23["status"] == "CLOSED_GUARDED_GENERAL_PRODUCTION_WRITER_ACTIVE_POST_AUDIT"
    assert a23["result"] == "OK_GUARDED_GENERAL_PRODUCTION_WRITER_RUNTIME_INTEGRATION_ACTIVE"
    assert a23["authorization"]["production_writer_active"] is True
    assert a23["authorization"]["p0_f1_closed"] is False
    assert a23["authorization"]["option_b_authorized"] is False
    assert a23["persistent_integration"]["dropin_persistent"] is True
    assert a23["rollback_protection"]["armed_for_every_cycle"] is True
    assert a23["next_safe_step"] == WORK_UNIT

    timer_initial = B.systemctl_state(TIMER)
    if timer_initial["active"] != "active" or timer_initial["enabled"] != "enabled":
        raise RuntimeError("A24_TIMER_PRECONDITION_FAILED")
    B.verify_persistent_runtime(a23)

    timer_restored = False
    backup_root: Path | None = None
    repo_backups: dict[Path, Path] = {}

    def restore_timer() -> None:
        nonlocal timer_restored
        if timer_initial["active"] == "active":
            run(["systemctl", "start", TIMER], check=True, timeout=30)
        else:
            run(["systemctl", "stop", TIMER], check=True, timeout=30)
        timer_restored = True

    def cleanup() -> None:
        if repo_backups:
            try:
                B.restore_repo_state(repo_backups)
                run(["git", "reset", "--mixed", EXPECTED_HEAD], check=False, timeout=30)
            except Exception:
                pass
        if not timer_restored:
            try:
                restore_timer()
            except Exception:
                pass
        if backup_root is not None:
            shutil.rmtree(backup_root, ignore_errors=True)

    atexit.register(cleanup)

    run(["systemctl", "stop", TIMER], check=True, timeout=30)
    deadline = time.time() + 180
    while time.time() < deadline:
        if B.systemctl_state(SERVICE)["active"] in {"inactive", "failed"}:
            break
        time.sleep(0.5)
    else:
        raise RuntimeError("A24_SERVICE_DID_NOT_BECOME_INACTIVE")

    order = order_evidence(a23)
    journal = journal_evidence(a23)
    natural_count = len(order["natural_cycles"])
    if journal["failure_markers"]:
        raise RuntimeError(
            "A24_POST_ACTIVATION_FAILURE_MARKERS:"
            + ",".join(journal["failure_markers"])
        )
    if journal["start_count"] != natural_count:
        raise RuntimeError(
            "A24_SERVICE_START_COUNT_MISMATCH:"
            + str(journal["start_count"])
            + ":"
            + str(natural_count)
        )
    if journal["finish_count"] != natural_count:
        raise RuntimeError(
            "A24_SERVICE_FINISH_COUNT_MISMATCH:"
            + str(journal["finish_count"])
            + ":"
            + str(natural_count)
        )
    if journal["deactivated_success_count"] != natural_count:
        raise RuntimeError(
            "A24_SERVICE_DEACTIVATED_COUNT_MISMATCH:"
            + str(journal["deactivated_success_count"])
            + ":"
            + str(natural_count)
        )

    environment = B.verify_persistent_runtime(a23)
    database = database_evidence(a23, order)
    latest = latest_cycle_evidence(order, database)
    inventory = database["inventory"]

    if B.sha(HOT) != B.sha(PANEL_HOT):
        raise RuntimeError("A24_CURRENT_PANEL_HOT_HASH_MISMATCH")
    bridge = B.load(BRIDGE_STATE)
    if bridge.get("decision") != "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED":
        raise RuntimeError("A24_CURRENT_BRIDGE_DECISION_INVALID")
    if bridge.get("failures") != []:
        raise RuntimeError("A24_CURRENT_BRIDGE_FAILURES_PRESENT")
    hash_match = bridge.get("hash_match")
    if not isinstance(hash_match, dict) or not hash_match or not all(
        value is True for value in hash_match.values()
    ):
        raise RuntimeError("A24_CURRENT_BRIDGE_HASH_MISMATCH")

    summaries = natural_cycle_summaries(order, database, latest)
    timestamp = utc_now()
    closure_gates = {
        "a23_persistent_integration_verified": True,
        "minimum_natural_timer_cycles_observed": True,
        "all_observed_services_started": True,
        "all_observed_services_finished_successfully": True,
        "all_observed_services_deactivated_successfully": True,
        "all_observed_cycles_runner_hot_end_zero": True,
        "all_observed_cycles_complete_source_accounting_gate_passed": True,
        "all_observed_cycles_zero_unobservable_rows_gate_passed": True,
        "all_observed_cycles_exact_legacy_queue_parity_gate_passed": True,
        "all_observed_cycles_panel_hash_parity_gate_passed": True,
        "all_observed_cycles_rollback_guard_armed_gate_passed": True,
        "no_post_activation_failure_marker": True,
        "all_original_committed_batches_preserved": True,
        "all_committed_natural_cycles_accounted_in_database": True,
        "all_idempotent_natural_cycles_created_no_batch": True,
        "production_database_integrity_clean": True,
        "latest_result_guarded_state_parity": True,
        "persistent_runtime_environment_unchanged": True,
        "timer_configuration_preserved": True,
    }
    assert all(closure_gates.values())

    artifact = {
        "schema_version": "2.0",
        "work_unit": WORK_UNIT,
        "timestamp_utc": timestamp,
        "status": "CLOSED_POST_ACTIVATION_OBSERVATION_OK_P0_F1_CLOSED",
        "result": RESULT,
        "authorization_source": str(A23.relative_to(ROOT)),
        "evidence_model": "SYSTEMD_SUCCESS_ORDER_LOG_DATABASE_PARITY_LATEST_RESULT",
        "observation_policy": {
            "forced_service_cycle": False,
            "minimum_natural_cycles_required": MINIMUM_NATURAL_CYCLES,
            "natural_cycles_observed": natural_count,
            "observation_started_after_utc": a23["apply_finished_at_utc"],
            "observation_finished_at_utc": timestamp,
            "journal_payload_required": False,
            "journal_payload_absence_reason": "SERVICE_STDOUT_NOT_PERSISTED_AS_JSON_LINES",
        },
        "closure_gates": closure_gates,
        "natural_cycle_summaries": summaries,
        "natural_order_cycle_count": natural_count,
        "order_cycle_count_total": len(order["all_cycles"]),
        "committed_natural_cycle_count": database["committed_cycle_count"],
        "idempotent_natural_cycle_count": database["replay_cycle_count"],
        "systemd_journal_evidence": journal,
        "production_at_closure": inventory,
        "new_committed_batches_since_a23": database["extra_batches"],
        "latest_cycle_result": latest,
        "persistent_environment": environment,
        "persistent_dropin": {
            "path": str(DROPIN),
            "sha256": B.sha(DROPIN),
            "matches_a23": B.sha(DROPIN) == a23["persistent_integration"]["dropin_sha256"],
        },
        "current_output_audit": {
            "hot_sha256": B.sha(HOT),
            "panel_hot_sha256": B.sha(PANEL_HOT),
            "hot_panel_hash_match": B.sha(HOT) == B.sha(PANEL_HOT),
            "bridge_decision": bridge["decision"],
            "bridge_hash_match_all": True,
            "result_guarded_state_parity": True,
        },
        "authorization": {
            "general_production_writer_activation_authorized": True,
            "production_writer_active": True,
            "additional_canary_authorized": False,
            "p0_f1_closed": True,
            "option_b_readiness_decision_authorized": True,
            "option_b_authorized": False,
            "optimization_apply_authorized": False,
        },
        "next_safe_step": NEXT,
    }

    backup_root = Path(tempfile.mkdtemp(prefix="era55a24_v2_repo_"))
    repo_backups = B.backup_repo_state(backup_root)

    B.atomic_dump(ARTIFACT, artifact)
    update_documents(artifact, natural_count, inventory, timestamp)

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
        raise RuntimeError("A24_NO_STAGED_CHANGES")

    restore_timer()
    timer_after = B.systemctl_state(TIMER)
    if timer_after["active"] != timer_initial["active"]:
        raise RuntimeError("A24_TIMER_ACTIVE_STATE_NOT_RESTORED")
    if timer_after["enabled"] != timer_initial["enabled"]:
        raise RuntimeError("A24_TIMER_ENABLED_STATE_CHANGED")
    B.verify_persistent_runtime(a23)

    git("commit", "-m", SUBJECT)
    repo_backups = {}
    atexit.unregister(cleanup)
    if backup_root is not None:
        shutil.rmtree(backup_root, ignore_errors=True)

    print("ERA55A24_POST_ACTIVATION_OBSERVATION=SUCCESS")
    print("RESULT=" + RESULT)
    print("EVIDENCE_MODEL=SYSTEMD_SUCCESS_ORDER_LOG_DATABASE_PARITY_LATEST_RESULT")
    print("FORCED_SERVICE_CYCLE=false")
    print("NATURAL_TIMER_CYCLES_OBSERVED=" + str(natural_count))
    print("COMMITTED_NATURAL_CYCLES=" + str(database["committed_cycle_count"]))
    print("IDEMPOTENT_NATURAL_CYCLES=" + str(database["replay_cycle_count"]))
    print("PRODUCTION_BATCH_ROWS=" + str(inventory["batch_rows"]))
    print("PRODUCTION_LEDGER_ROWS=" + str(inventory["ledger_rows"]))
    print("ORIGINAL_BATCHES_PRESERVED=true")
    print("RUNNER_HOT_END_ZERO=true")
    print("COMPLETE_SOURCE_ACCOUNTING=true")
    print("UNOBSERVABLE_ROWS=0")
    print("PANEL_HOT_HASH_PARITY=true")
    print("ROLLBACK_GUARD_ARMED_FOR_EVERY_CYCLE=true")
    print("PRODUCTION_WRITER_ACTIVE=true")
    print("P0_F1_CLOSED=true")
    print("OPTION_B_READINESS_DECISION_AUTHORIZED=true")
    print("OPTION_B_AUTHORIZED=false")
    print("NEXT_SAFE_STEP=" + NEXT)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
