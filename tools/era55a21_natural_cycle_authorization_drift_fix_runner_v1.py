#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
sys.dont_write_bytecode = True
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
EXPECTED_HEAD = os.environ.get("TOKENOSKOBI_EXPECTED_HEAD", "").strip()
TARGET = ROOT / "tools/era55a21_p0_single_natural_cycle_post_remediation_canary_apply_and_post_audit_v1.py"
A20 = ROOT / "data/control/era55a20_p0_post_remediation_audit_and_production_canary_decision_v1.json"
FAILED_FULL_DISPLAY = Path("/run/tokenoskobi/era55a21_full_candidate_display.json")
ORDER_LOG = Path("/run/tokenoskobi/era55a21_order.log")
RESULT_FILE = Path("/run/tokenoskobi/era55a21_one_shot_result.json")
DROPIN = Path("/run/systemd/system/tokenoskobi-news-radar-refresh.service.d/90-era55a21-canary.conf")
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
ADAPTER = ROOT / "tools/news_disposition_admission_contract_v1.py"
SUBJECT = "ERA55A21_PREP_FIX | OK | NATURAL_CYCLE_DYNAMIC_BATCH_BINDING"
BASELINE_UID = "batch_58401c9613b091aa251a130383ced8a5"


def run(args: list[str], *, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
        env=env,
    )


def git(*args: str) -> str:
    return run(["git", *args]).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def load_module(name: str, path: Path):
    tools = str(ROOT / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"PATCH_ANCHOR_COUNT_INVALID:{label}:{count}")
    return source.replace(old, new, 1)


def baseline_state() -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        batches = connection.execute(
            """
            SELECT rowid, batch_uid, status, policy_version,
                   source_candidate_count
            FROM news_disposition_batches_v2
            ORDER BY rowid
            """
        ).fetchall()
        ledger_rows = int(
            connection.execute(
                "SELECT COUNT(*) FROM news_disposition_ledger_v2"
            ).fetchone()[0]
        )
        baseline_rows = int(
            connection.execute(
                "SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?",
                (BASELINE_UID,),
            ).fetchone()[0]
        )
        return {
            "batches": batches,
            "ledger_rows": ledger_rows,
            "baseline_rows": baseline_rows,
            "integrity": str(connection.execute("PRAGMA integrity_check").fetchone()[0]),
            "quick": str(connection.execute("PRAGMA quick_check").fetchone()[0]),
            "foreign_keys": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
        }
    finally:
        connection.close()


def main() -> int:
    if not EXPECTED_HEAD:
        raise RuntimeError("TOKENOSKOBI_EXPECTED_HEAD_REQUIRED")
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BRANCH_NOT_MAIN")
    if git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("UNEXPECTED_HEAD")
    if git("status", "--porcelain"):
        raise RuntimeError("WORKTREE_NOT_CLEAN")

    for path in (TARGET, A20, FAILED_FULL_DISPLAY, ORDER_LOG, DB, HOT, ADAPTER):
        if not path.exists():
            raise FileNotFoundError(path)
    if RESULT_FILE.exists():
        raise RuntimeError("UNEXPECTED_A21_SUCCESS_RESULT_PRESENT")
    if DROPIN.exists():
        raise RuntimeError("A21_DROPIN_PRESENT")

    order = ORDER_LOG.read_text(encoding="utf-8").splitlines()
    expected_order = [
        "LOCK_ACQUIRED",
        "RECOVERY_DONE:RECOVERED",
        "RAW_START",
        "RAW_END:0",
        "DERIVED_START",
        "DERIVED_END:0",
        "HOT_START",
        "A21_ONE_SHOT_HOT_START",
        "A21_ORIGINAL_HOT_END:0",
        "HOT_END:1",
    ]
    if order != expected_order:
        raise RuntimeError("FAILED_ATTEMPT_ORDER_NOT_RECOGNIZED:" + json.dumps(order))

    db = baseline_state()
    if not (
        len(db["batches"]) == 1
        and db["batches"][0][0] == 1
        and db["batches"][0][1] == BASELINE_UID
        and db["batches"][0][2] == "COMMITTED"
        and db["ledger_rows"] == 106
        and db["baseline_rows"] == 106
        and db["integrity"] == "ok"
        and db["quick"] == "ok"
        and db["foreign_keys"] == 0
    ):
        raise RuntimeError("BASELINE_DATABASE_NOT_PRESERVED")

    a20 = load(A20)
    contract = a20["canary_execution_contract"]
    expected_uid = str(contract["prospective_batch_uid"])
    expected_count = int(contract["expected_new_ledger_rows"])
    if str(contract["existing_batch_uid_must_be_preserved"]) != BASELINE_UID:
        raise RuntimeError("A20_BASELINE_UID_MISMATCH")

    adapter = load_module("a21_drift_adapter", ADAPTER)
    failed_display = load(FAILED_FULL_DISPLAY)
    legacy_queue = load(HOT).get("hot_queue")
    plan = adapter.build_plan_with_admission_contract(
        failed_display,
        legacy_queue,
        queue_capacity=50,
    )
    actual_uid = str(plan["batch_uid"])
    actual_count = int(plan["counts"]["source_candidate_count"])
    accounted = sum(
        int(plan["counts"][key])
        for key in (
            "admitted_count",
            "overflow_count",
            "duplicate_removed_count",
            "unsafe_filtered_count",
            "invalid_candidate_count",
            "replaced_count",
        )
    )
    if accounted != actual_count:
        raise RuntimeError("FAILED_ATTEMPT_ACCOUNTING_INVALID")
    if actual_uid == BASELINE_UID:
        raise RuntimeError("FAILED_ATTEMPT_NEW_UID_EQUALS_BASELINE")
    if actual_uid == expected_uid and actual_count == expected_count:
        raise RuntimeError("AUTHORIZATION_DRIFT_NOT_REPRODUCED")

    source = TARGET.read_text(encoding="utf-8")

    source = replace_once(
        source,
        '''    if str(plan["batch_uid"]) != expected_new_uid:\n        raise RuntimeError(\n            "A21_AUTHORIZED_BATCH_UID_DRIFT:"\n            + expected_new_uid\n            + ":"\n            + str(plan["batch_uid"])\n        )\n    if source_count != expected_source_count:\n        raise RuntimeError(\n            "A21_AUTHORIZED_SOURCE_COUNT_DRIFT:"\n            + str(expected_source_count)\n            + ":"\n            + str(source_count)\n        )\n''',
        '''    actual_new_uid = str(plan["batch_uid"])\n    if actual_new_uid == expected_baseline_uid:\n        raise RuntimeError("A21_DYNAMIC_NEW_UID_EQUALS_BASELINE")\n    expected_new_uid = actual_new_uid\n    expected_source_count = source_count\n''',
        "ONE_SHOT_DYNAMIC_BINDING",
    )

    source = replace_once(
        source,
        '''        if one_shot.get("status") != "OK_A21_ONE_SHOT_HOT_WRAPPER_COMPLETED":\n            raise RuntimeError("A21_ONE_SHOT_STATUS_NOT_OK")\n\n        order = ORDER_LOG.read_text(encoding="utf-8").splitlines()\n''',
        '''        if one_shot.get("status") != "OK_A21_ONE_SHOT_HOT_WRAPPER_COMPLETED":\n            raise RuntimeError("A21_ONE_SHOT_STATUS_NOT_OK")\n        actual_new_uid = str(one_shot.get("new_batch_uid") or "")\n        actual_new_rows = int(one_shot.get("source_candidate_count") or 0)\n        if not actual_new_uid or actual_new_uid == baseline_uid:\n            raise RuntimeError("A21_DYNAMIC_RESULT_UID_INVALID")\n        if not (1 <= actual_new_rows <= MAX_SOURCE_ROWS):\n            raise RuntimeError("A21_DYNAMIC_RESULT_SOURCE_COUNT_INVALID")\n        expected_new_uid = actual_new_uid\n        expected_new_rows = actual_new_rows\n        expected_total_rows = int(before_inventory["ledger_rows"]) + actual_new_rows\n\n        order = ORDER_LOG.read_text(encoding="utf-8").splitlines()\n''',
        "ORCHESTRATOR_DYNAMIC_BINDING",
    )

    source = replace_once(
        source,
        '''            "authorization_source": str(A20.relative_to(ROOT)),\n            "canary_token": token,\n''',
        '''            "authorization_source": str(A20.relative_to(ROOT)),\n            "natural_cycle_authorization_binding": {\n                "mode": "DYNAMIC_INVARIANT_BOUND_SINGLE_CYCLE_V1",\n                "a20_reference_batch_uid": str(contract["prospective_batch_uid"]),\n                "a20_reference_source_count": int(contract["expected_new_ledger_rows"]),\n                "actual_batch_uid": expected_new_uid,\n                "actual_source_count": expected_new_rows,\n                "actual_batch_distinct_from_baseline": expected_new_uid != baseline_uid,\n                "source_count_within_authorized_maximum": 1 <= expected_new_rows <= MAX_SOURCE_ROWS,\n                "reason": "Natural-cycle source snapshots are mutable; authorization binds safety invariants rather than a stale prospective hash.",\n            },\n            "canary_token": token,\n''',
        "ARTIFACT_BINDING_EVIDENCE",
    )

    TARGET.write_text(source, encoding="utf-8")
    run([sys.executable, "-B", "-m", "py_compile", str(TARGET)])
    cache = TARGET.parent / "__pycache__"
    if cache.exists():
        import shutil
        shutil.rmtree(cache)

    git("add", str(TARGET.relative_to(ROOT)))
    staged = git("diff", "--cached", "--name-only").splitlines()
    if staged != [str(TARGET.relative_to(ROOT))]:
        raise RuntimeError("UNEXPECTED_PATCH_SCOPE:" + json.dumps(staged))
    git("commit", "-m", SUBJECT)
    fixed_head = git("rev-parse", "HEAD")

    print("A21_AUTHORIZATION_DRIFT_DIAGNOSIS=CONFIRMED")
    print("A20_REFERENCE_BATCH_UID=" + expected_uid)
    print("FAILED_ATTEMPT_ACTUAL_BATCH_UID=" + actual_uid)
    print("A20_REFERENCE_SOURCE_COUNT=" + str(expected_count))
    print("FAILED_ATTEMPT_ACTUAL_SOURCE_COUNT=" + str(actual_count))
    print("FAILED_ATTEMPT_SOURCE_ACCOUNTED=" + str(accounted))
    print("BASELINE_BATCH_PRESERVED=true")
    print("FIX_MODE=DYNAMIC_INVARIANT_BOUND_SINGLE_CYCLE_V1")
    print("FIXED_HEAD=" + fixed_head)

    completed = run(
        [sys.executable, "-B", str(TARGET)],
        check=False,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "TOKENOSKOBI_EXPECTED_HEAD": fixed_head,
        },
    )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
