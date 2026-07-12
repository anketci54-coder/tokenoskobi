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

A14 = ROOT / "data/control/era55a14_p0_pre_gateway_writer_post_test_audit_and_bounded_canary_decision_v1.json"
ADAPTER = ROOT / "tools/news_disposition_admission_contract_v1.py"
EXTRACTOR = ROOT / "tools/news_pre_gateway_candidate_stream_v1.py"
WRITER = ROOT / "tools/news_disposition_ledger_writer_v1.py"
RECOVERY = ROOT / "tools/news_ledger_recovery_guard_v1.py"
GATEWAY = ROOT / "tools/hot_intelligence_ingress_gateway_v1.py"
MARKET = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADVERSARIAL = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"
DISPLAY = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
OBSOLETE = ROOT / "tools/era55a15_payload_padding_recovery_runner_v1.py"

ARTIFACT = ROOT / "data/control/era55a15_p0_pre_gateway_queue_semantic_parity_repair_and_temp_copy_test_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST.md"
RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

RESULT = "OK_COMPLETE_LEDGER_LEGACY_QUEUE_SEMANTIC_PARITY_TEMP_COPY"
NEXT = "ERA55A_16_P0_QUEUE_PARITY_POST_TEST_AUDIT_AND_SINGLE_CYCLE_CANARY_DECISION"
SUBJECT = "ERA55A15_QUEUE_PARITY_REPAIR_TEMP_COPY | OK | PRODUCTION_UNBOUND"
POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def canon(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def uid_hash(queue: list[dict[str, Any]]) -> str:
    return hashlib.sha256("\n".join(str(x.get("hot_uid") or "") for x in queue).encode()).hexdigest()


def db_state(path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        return {
            "batch_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_batches_v2").fetchone()[0]),
            "ledger_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_ledger_v2").fetchone()[0]),
            "integrity_check": str(conn.execute("PRAGMA integrity_check").fetchone()[0]),
            "quick_check": str(conn.execute("PRAGMA quick_check").fetchone()[0]),
            "foreign_key_check_rows": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
        }
    finally:
        conn.close()


def service_state() -> dict[str, Any]:
    r = subprocess.run(
        ["systemctl", "show", "tokenoskobi-news-radar-refresh.service", "-p", "Environment", "-p", "ExecStart", "-p", "FragmentPath"],
        text=True,
        capture_output=True,
    )
    text = r.stdout
    return {
        "rc": r.returncode,
        "runner_bound": str(ROOT / "tools/news_radar_refresh_runner_v1.py") in text,
        "writer_enabled": "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text,
        "lock_enabled": "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text,
        "fragment": next((line.split("=", 1)[1] for line in text.splitlines() if line.startswith("FragmentPath=")), ""),
    }


def guard() -> dict[str, Any]:
    return {"database": db_state(DB), "service": service_state()}


def snapshot(temp: Path) -> dict[str, Any]:
    sources = {"market": MARKET, "adversarial": ADVERSARIAL, "display": DISPLAY, "hot": HOT}
    for attempt in range(1, 9):
        before = {k: sha(v) for k, v in sources.items()}
        paths: dict[str, Path] = {}
        for key, source in sources.items():
            target = temp / f"{key}{source.suffix}"
            shutil.copy2(source, target)
            paths[key] = target
        after = {k: sha(v) for k, v in sources.items()}
        copied = {k: sha(v) for k, v in paths.items()}
        if before == after == copied:
            return {"attempt": attempt, "hashes": before, "paths": paths}
        time.sleep(0.25)
    raise RuntimeError("STABLE_SNAPSHOT_FAILED")


def backup(source: Path, target: Path) -> None:
    a = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    b = sqlite3.connect(target)
    try:
        a.backup(b)
    finally:
        b.close(); a.close()


def batch_metrics(path: Path, batch_uid: str) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return {
            "batch_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_batches_v2 WHERE batch_uid=?", (batch_uid,)).fetchone()[0]),
            "ledger_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=?", (batch_uid,)).fetchone()[0]),
            "dispositions": {str(r[0]): int(r[1]) for r in conn.execute("SELECT disposition, COUNT(*) FROM news_disposition_ledger_v2 WHERE batch_uid=? GROUP BY disposition", (batch_uid,)).fetchall()},
            "integrity": str(conn.execute("PRAGMA integrity_check").fetchone()[0]),
            "quick": str(conn.execute("PRAGMA quick_check").fetchone()[0]),
            "fk": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
        }
    finally:
        conn.close()


def contract_error(adapter: Any, display: dict[str, Any], queue: list[dict[str, Any]]) -> str:
    try:
        adapter.build_plan_with_admission_contract(display, queue, queue_capacity=50)
    except ValueError as exc:
        return str(exc)
    raise AssertionError("EXPECTED_CONTRACT_ERROR")


def section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)", re.DOTALL)
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND:{heading}")
    return text[:match.start()] + heading + "\n\n" + body.rstrip() + "\n" + text[match.end():]


def main() -> int:
    if not EXPECTED_HEAD:
        raise RuntimeError("TOKENOSKOBI_EXPECTED_HEAD_REQUIRED")
    if git("branch", "--show-current") != "main" or git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("HEAD_OR_BRANCH_MISMATCH")
    if git("status", "--porcelain"):
        raise RuntimeError("WORKTREE_NOT_CLEAN")

    for path in (A14, ADAPTER, EXTRACTOR, WRITER, RECOVERY, GATEWAY, MARKET, ADVERSARIAL, DISPLAY, SUMMARY, HOT, DB, RUNTIME, HISTORY, MASTER, HANDOFF, ALMANAC):
        if not path.exists():
            raise FileNotFoundError(path)

    a14 = load(A14)
    assert a14["result"] == "REJECT_BOUNDED_CANARY_QUEUE_SEMANTIC_PARITY_NOT_PROVEN"
    assert a14["production_unchanged"] is True

    before = guard()
    assert before["database"] == {"batch_rows": 0, "ledger_rows": 0, "integrity_check": "ok", "quick_check": "ok", "foreign_key_check_rows": 0}
    assert before["service"]["runner_bound"] is True
    assert before["service"]["writer_enabled"] is False
    assert before["service"]["lock_enabled"] is False

    tools = str(ROOT / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    extractor = module("a15_extractor", EXTRACTOR)
    writer = module("a15_writer", WRITER)
    recovery = module("a15_recovery", RECOVERY)
    gateway = module("a15_gateway", GATEWAY)
    adapter = module("a15_adapter", ADAPTER)
    assert adapter.POLICY_VERSION == POLICY

    temp = Path(tempfile.mkdtemp(prefix="era55a15_", dir="/tmp"))
    try:
        snap = snapshot(temp)
        paths = snap["paths"]
        legacy = gateway.normalize_items(load(paths["display"]))
        current = load(paths["hot"])["hot_queue"]
        assert canon(legacy) == canon(current)

        full = extractor.build_candidate_display(paths["market"], paths["adversarial"])
        full_path = temp / "full.json"
        dump(full_path, full)
        standard = writer.build_plan(full, queue_capacity=50)
        repaired = adapter.build_plan_with_admission_contract(full, legacy, queue_capacity=50)

        counts = repaired["counts"]
        source_count = int(counts["source_candidate_count"])
        accounted = sum(int(counts[k]) for k in ("admitted_count", "overflow_count", "duplicate_removed_count", "unsafe_filtered_count", "invalid_candidate_count", "replaced_count"))
        assert 0 < len(legacy) <= 50 <= source_count <= 5000
        assert accounted == source_count
        assert canon(repaired["hot_queue"]) == canon(legacy)
        standard_mismatch = canon(standard["hot_queue"]) != canon(legacy)

        temp_db = temp / "test.sqlite"
        backup(DB, temp_db)
        out = temp / "out.json"
        state = temp / "state.json"
        lock = temp / "lock"
        first = adapter.write_and_publish_with_admission_contract(
            display_path=full_path, admission_contract_path=paths["hot"], summary_path=SUMMARY,
            db_path=temp_db, output_path=out, recovery_state_path=state,
            contract_seed_path=paths["hot"], queue_capacity=50, lock_path=lock,
        )
        first_hash = sha(out)
        metrics = batch_metrics(temp_db, repaired["batch_uid"])
        assert canon(load(out)["hot_queue"]) == canon(legacy)
        second = adapter.write_and_publish_with_admission_contract(
            display_path=full_path, admission_contract_path=paths["hot"], summary_path=SUMMARY,
            db_path=temp_db, output_path=out, recovery_state_path=state,
            contract_seed_path=paths["hot"], queue_capacity=50, lock_path=lock,
        )
        assert first["write_result"]["status"] == "COMMITTED"
        assert second["write_result"]["status"] == "IDEMPOTENT_REPLAY_NOOP"
        assert first_hash == sha(out)
        assert metrics["batch_rows"] == 1 and metrics["ledger_rows"] == source_count
        assert metrics["integrity"] == "ok" and metrics["quick"] == "ok" and metrics["fk"] == 0

        out.unlink()
        recovered = recovery.recover_committed_batch(temp_db, out, state, contract_seed_path=paths["hot"], batch_sequence=int(first["batch_sequence"]))
        assert recovered["status"] == "RECOVERED"
        assert canon(load(out)["hot_queue"]) == canon(legacy)

        duplicate = copy.deepcopy(legacy); duplicate[-1] = copy.deepcopy(legacy[0])
        unknown = copy.deepcopy(legacy); unknown[0]["hot_uid"] = "hot_unknown_a15"
        drift = copy.deepcopy(legacy); drift[0]["title"] = str(drift[0].get("title") or "") + " [DRIFT]"
        duplicate_error = contract_error(adapter, full, duplicate)
        unknown_error = contract_error(adapter, full, unknown)
        drift_error = contract_error(adapter, full, drift)
        assert duplicate_error.startswith("ADMISSION_CONTRACT_DUPLICATE_UID:")
        assert unknown_error.startswith("ADMISSION_CONTRACT_UID_NOT_FOUND:")
        assert drift_error.startswith("ADMISSION_CONTRACT_PAYLOAD_MISMATCH:")

        rollback_db = temp / "rollback.sqlite"
        backup(DB, rollback_db)
        injected = None
        try:
            writer.write_plan(rollback_db, repaired, inject_failure_after_ledger_rows=True)
        except RuntimeError as exc:
            injected = str(exc)
        assert injected == "INJECTED_FAILURE_AFTER_LEDGER_ROWS"
        assert db_state(rollback_db)["batch_rows"] == 0 and db_state(rollback_db)["ledger_rows"] == 0

        after = guard()
        assert before == after
        now = datetime.now(timezone.utc).isoformat()
        artifact = {
            "schema_version": "1.0",
            "work_unit": "ERA55A_15_P0_PRE_GATEWAY_QUEUE_SEMANTIC_PARITY_REPAIR_AND_TEMP_COPY_TEST",
            "tested_at_utc": now,
            "status": "CLOSED_TEMP_COPY_PARITY_REPAIR_OK",
            "result": RESULT,
            "adapter_module": {"path": str(ADAPTER.relative_to(ROOT)), "sha256": sha(ADAPTER), "policy_version": POLICY, "production_runtime_bound": False},
            "stable_snapshot": {"attempt": snap["attempt"], **snap["hashes"]},
            "parity_repair": {
                "source_candidate_count": source_count, "accounted_count": accounted, "unobservable_rows": 0,
                "legacy_queue_count": len(legacy), "standard_pre_gateway_queue_mismatched_before_repair": standard_mismatch,
                "repaired_queue_exact_object_parity": True, "repaired_queue_exact_uid_order_parity": True,
                "legacy_uid_hash": uid_hash(legacy), "repaired_uid_hash": uid_hash(repaired["hot_queue"]),
                "counts": counts, "ledger_rows": metrics["ledger_rows"], "disposition_counts": metrics["dispositions"],
            },
            "idempotency": {"first_write_status": first["write_result"]["status"], "second_write_status": second["write_result"]["status"], "batch_rows_after_replay": 1, "ledger_rows_after_replay": source_count, "output_hash_unchanged": True},
            "postcommit_publish_recovery": {"status": recovered["status"], "exact_legacy_queue_parity": True, "db_rewrite": False},
            "fail_closed_contract_tests": {"duplicate_uid_error": duplicate_error, "unknown_uid_error": unknown_error, "payload_drift_error": drift_error, "all_passed": True},
            "transaction_rollback": {"injected_error": injected, "batch_rows_after_rollback": 0, "ledger_rows_after_rollback": 0, "ok": True},
            "production_guard_before": before, "production_guard_after": after, "production_ledger_unchanged": True,
            "authorization": {"single_natural_cycle_bounded_canary_authorized": False, "general_production_writer_activation_authorized": False, "production_writer_active": False, "p0_f1_closed": False, "option_b_authorized": False, "optimization_apply_authorized": False},
            "next_safe_step": NEXT,
        }
        dump(ARTIFACT, artifact)
        REPORT.write_text(f"# ERA55A15 Queue Semantic Parity Repair\n\n- Result: `{RESULT}`\n- Source candidates: `{source_count}`\n- Legacy queue: `{len(legacy)}`\n- Unobservable rows: `0`\n- Exact object parity: `true`\n- Exact UID order parity: `true`\n- Production unchanged: `true`\n- Next: `{NEXT}`\n", encoding="utf-8")

        runtime = load(RUNTIME); current = runtime["current_state"]
        current.update({
            "mode": "ERA55A15_QUEUE_SEMANTIC_PARITY_REPAIR_TEMP_COPY_OK", "runtime_status": "WORK_UNIT_CLOSED", "updated_at": now,
            "last_action": {"timestamp": now, "task": artifact["work_unit"], "result": RESULT, "artifact": str(ARTIFACT.relative_to(ROOT))},
            "active_work_unit": {"id": artifact["work_unit"], "type": "ERA55_P0_QUEUE_SEMANTIC_PARITY_REPAIR_TEMP_COPY_TEST", "parent": "ERA55_RUNTIME_OPTIMIZATION", "artifact": str(ARTIFACT.relative_to(ROOT)), "status": artifact["status"], "result": RESULT, "production_mutation": False, "next_step": NEXT},
            "next_safe_step": {"id": NEXT, "type": "ERA55_P0_QUEUE_PARITY_POST_TEST_AUDIT_SINGLE_CYCLE_CANARY_DECISION", "parent": "ERA55_RUNTIME_OPTIMIZATION", "purpose": "Audit exact legacy parity and decide one guarded natural cycle.", "human_authorization_required": True, "single_cycle_bounded_canary_authorized": False, "general_production_writer_activation_authorized": False, "option_b_authorized": False, "optimization_apply_authorized": False, "status": "READY"},
            "current_problem": {"code": "QUEUE_PARITY_REPAIR_NOT_YET_INDEPENDENTLY_AUDITED", "severity": "P0", "evidence": str(ARTIFACT.relative_to(ROOT))},
        })
        runtime["current_work_unit"] = current["active_work_unit"]; dump(RUNTIME, runtime)

        history = load(HISTORY); events = history.setdefault("events", [])
        if not any(isinstance(x, dict) and x.get("event_id") == "ERA55A15_QUEUE_SEMANTIC_PARITY_REPAIR_TEMP_COPY_V1" for x in events):
            events.append({"event_id": "ERA55A15_QUEUE_SEMANTIC_PARITY_REPAIR_TEMP_COPY_V1", "timestamp_utc": now, "era": "ERA55", "work_unit": artifact["work_unit"], "event": "TEMP_COPY_PARITY_REPAIR_TEST", "status": artifact["status"], "result": RESULT, "artifact": str(ARTIFACT.relative_to(ROOT)), "source_candidate_count": source_count, "legacy_queue_count": len(legacy), "unobservable_rows": 0, "exact_legacy_queue_parity": True, "production_unchanged": True, "single_cycle_bounded_canary_authorized": False, "p0_f1_closed": False, "next_safe_step": NEXT})
        history["updated_at"] = history["updated_at_utc"] = now; dump(HISTORY, history)

        master = MASTER.read_text(encoding="utf-8")
        master = section(master, "## 01 PROJECT STATUS", """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ACTIVE_ERA55_P0_QUEUE_PARITY_CANARY_DECISION_PENDING
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
CURRENT_HUMAN_SUMMARY=06_PROJECT_MASTER_STATE.md
GIT_BRANCH=main
GIT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD
BOOT_HEALTH=100/100
```""")
        master = section(master, "## 02 CURRENT MAJOR-LINE POSITION", f"""```text
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_QUEUE_PARITY_REPAIR
LAST_COMPLETED_SUBSTEP={artifact['work_unit']}
COMPLETE_PRE_GATEWAY_ACCOUNTING=true
SOURCE_CANDIDATES={source_count}
LEGACY_QUEUE_COUNT={len(legacy)}
UNOBSERVABLE_ROWS=0
EXACT_LEGACY_OBJECT_PARITY=true
EXACT_LEGACY_UID_ORDER_PARITY=true
SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED=false
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```""")
        master = section(master, "## 03 LAST VERIFIED WORK", f"""```text
LAST_COMPLETED={artifact['work_unit']}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}"""); MASTER.write_text(master, encoding="utf-8")

        handoff = HANDOFF.read_text(encoding="utf-8")
        handoff = section(handoff, "## 02 CURRENT CONTINUATION CHECKPOINT", f"""PROJECT_STATUS=ACTIVE_ERA55_P0_QUEUE_PARITY_CANARY_DECISION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_QUEUE_PARITY_REPAIR
LAST_COMPLETED_SUBSTEP={artifact['work_unit']}
SOURCE_CANDIDATES={source_count}
LEGACY_QUEUE_COUNT={len(legacy)}
UNOBSERVABLE_ROWS=0
EXACT_LEGACY_OBJECT_PARITY=true
EXACT_LEGACY_UID_ORDER_PARITY=true
SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED=false
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""")
        handoff = section(handoff, "## 03 LAST VERIFIED WORK", f"""LAST_COMPLETED={artifact['work_unit']}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS={artifact['status']}
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=QUEUE_PARITY_REPAIR_NOT_YET_INDEPENDENTLY_AUDITED""")
        handoff = section(handoff, "## 06 DO NOT REOPEN OR REPEAT", """- Do not rerun A9-A15 unless evidence is invalidated.
- Do not bind the admission-contract adapter before A16.
- Do not enable production writer or runner-lock flags.
- Do not start Option B or close P0 F1.""")
        handoff = section(handoff, "## 07 ALLOWED NEXT DECISIONS", f"""- Complete accounting: `VALIDATED`.
- Exact legacy parity: `VALIDATED_TEMP_COPY`.
- Single-cycle canary: `PENDING_A16_DECISION`.
- General production: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""")
        handoff = section(handoff, "## 08 NEXT SESSION EXECUTION RULE", """1. Confirm A16 is current.
2. Independently audit A15 on a fresh temp copy.
3. Decide only one guarded natural cycle.
4. Do not authorize general production or close P0 F1."""); HANDOFF.write_text(handoff, encoding="utf-8")

        almanac = ALMANAC.read_text(encoding="utf-8")
        if "## ERA55A_15 QUEUE SEMANTIC PARITY REPAIR" not in almanac:
            ALMANAC.write_text(almanac.rstrip() + f"\n\n---\n\n## ERA55A_15 QUEUE SEMANTIC PARITY REPAIR\n\n- Status: `{artifact['status']}`\n- Result: `{RESULT}`\n- Source candidates: `{source_count}`\n- Legacy queue: `{len(legacy)}`\n- Unobservable rows: `0`\n- Exact legacy parity: `true`\n- Production mutation: `false`\n- Next: `{NEXT}`\n", encoding="utf-8")

        if OBSOLETE.exists():
            subprocess.run(["git", "rm", "-f", str(OBSOLETE.relative_to(ROOT))], cwd=ROOT, check=True)
        git("add", str(ADAPTER.relative_to(ROOT)), str(ARTIFACT.relative_to(ROOT)), str(RUNTIME.relative_to(ROOT)), str(HISTORY.relative_to(ROOT)), str(MASTER.relative_to(ROOT)), str(HANDOFF.relative_to(ROOT)), str(ALMANAC.relative_to(ROOT)))
        subprocess.run(["git", "add", "-f", str(REPORT.relative_to(ROOT))], cwd=ROOT, check=True)
        git("commit", "-m", SUBJECT)

        print("ERA55A15_QUEUE_PARITY_REPAIR_TEMP_COPY=SUCCESS")
        print("RESULT=" + RESULT)
        print("SOURCE_CANDIDATES=" + str(source_count))
        print("SOURCE_ACCOUNTED=" + str(accounted))
        print("UNOBSERVABLE_ROWS=0")
        print("LEGACY_QUEUE_EXACT_OBJECT_PARITY=true")
        print("LEGACY_QUEUE_EXACT_UID_ORDER_PARITY=true")
        print("IDEMPOTENT_REPLAY=true")
        print("POSTCOMMIT_PUBLISH_RECOVERY_PARITY=true")
        print("FAIL_CLOSED_CONTRACT_TESTS=true")
        print("TRANSACTION_ROLLBACK=true")
        print("PRODUCTION_RUNTIME_BOUND=false")
        print("PRODUCTION_LEDGER_UNCHANGED=true")
        print("SINGLE_CYCLE_BOUNDED_CANARY_AUTHORIZED=false")
        print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print("NEXT_SAFE_STEP=" + NEXT)
        print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
        return 0
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
