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
EXPECTED_HEAD = "7884710390f8965b1dd7687bd038ea7524f49eb1"

A11_ARTIFACT = ROOT / "data/control/era55a11_p0_runtime_ledger_writer_module_extraction_and_temp_copy_binding_test_v1.json"
DECISION_ARTIFACT = ROOT / "data/control/era55a12_p0_runtime_ledger_writer_post_test_audit_and_bounded_canary_decision_v1.json"
WRITER = ROOT / "tools/news_disposition_ledger_writer_v1.py"
CONSUMER = ROOT / "tools/news_coverage_readmodel_consumer_v1.py"
DISPLAY_ADAPTER = ROOT / "tools/news_coverage_panel_display_adapter_v1.py"
HOT_GATEWAY = ROOT / "tools/hot_intelligence_ingress_gateway_v1.py"
RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
HOT_OUTPUT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
RECOVERY_STATE = ROOT / "runtime/state/news_ledger_recovery_state_v1.json"

NEXT_STEP = "ERA55A_13_P0_PRE_GATEWAY_CANDIDATE_STREAM_EXTRACTION_AND_TEMP_COPY_BINDING_TEST"
COMMIT_SUBJECT = "ERA55A12_CANARY_DECISION | BLOCK | SOURCE_ALREADY_TRUNCATED"


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


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(
        rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND:{heading}")
    return text[: match.start()] + heading + "\n\n" + body.rstrip() + "\n" + text[match.end() :]


def production_db_state() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        return {
            "batch_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_batches_v2").fetchone()[0]),
            "ledger_rows": int(conn.execute("SELECT COUNT(*) FROM news_disposition_ledger_v2").fetchone()[0]),
            "integrity_check": str(conn.execute("PRAGMA integrity_check").fetchone()[0]),
            "quick_check": str(conn.execute("PRAGMA quick_check").fetchone()[0]),
            "foreign_key_check_rows": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
            "query_only": bool(conn.execute("PRAGMA query_only").fetchone()[0]),
        }
    finally:
        conn.close()


def service_environment() -> dict[str, Any]:
    completed = subprocess.run(
        [
            "systemctl",
            "show",
            "tokenoskobi-news-radar-refresh.service",
            "-p",
            "Environment",
            "-p",
            "ExecStart",
        ],
        text=True,
        capture_output=True,
    )
    text = completed.stdout
    return {
        "rc": completed.returncode,
        "stdout": text.strip(),
        "writer_enabled_explicitly": "TOKENOSKOBI_LEDGER_WRITER_ENABLED=1" in text,
        "runner_lock_enabled_explicitly": "TOKENOSKOBI_RUNNER_LOCK_ENABLED=1" in text,
    }


def validate_a11(a11: dict[str, Any]) -> None:
    assert a11["status"] == "CLOSED_TEMP_COPY_BINDING_OK"
    assert a11["result"] == "OK_RUNTIME_WRITER_MODULE_REAL_SOURCE_TEMP_COPY_BOUND"
    assert a11["real_source_snapshot"]["unobservable_rows"] == 0
    assert a11["real_source_snapshot"]["queue_parity"] is True
    assert a11["idempotency"]["write_status"] == "IDEMPOTENT_REPLAY_NOOP"
    assert a11["postcommit_publish_recovery"]["publish_status"] == "RECOVERED"
    assert a11["synthetic_six_disposition_model"]["exact_match"] is True
    assert a11["transaction_rollback"]["ok"] is True
    assert a11["production_guard"]["production_db_mutation"] is False
    assert a11["production_guard"]["production_runtime_bound"] is False
    assert a11["authorization"]["bounded_canary_authorized"] is False


def main() -> int:
    if git("branch", "--show-current") != "main":
        raise RuntimeError("BRANCH_NOT_MAIN")
    if git("rev-parse", "HEAD") != EXPECTED_HEAD:
        raise RuntimeError(
            "UNEXPECTED_HEAD expected=" + EXPECTED_HEAD + " actual=" + git("rev-parse", "HEAD")
        )
    if git("status", "--porcelain"):
        raise RuntimeError("WORKTREE_NOT_CLEAN")

    required = [
        A11_ARTIFACT,
        WRITER,
        CONSUMER,
        DISPLAY_ADAPTER,
        HOT_GATEWAY,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
        DB,
    ]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)

    production_guard_before = {
        "database": file_guard(DB),
        "hot_output": file_guard(HOT_OUTPUT),
        "recovery_state": file_guard(RECOVERY_STATE),
        "service_environment": service_environment(),
        "database_state": production_db_state(),
    }

    a11 = load_json(A11_ARTIFACT)
    validate_a11(a11)

    writer_text = WRITER.read_text(encoding="utf-8")
    consumer_text = CONSUMER.read_text(encoding="utf-8")
    display_text = DISPLAY_ADAPTER.read_text(encoding="utf-8")
    gateway_text = HOT_GATEWAY.read_text(encoding="utf-8")

    source_chain = {
        "writer_reads_display_sections": (
            "def iter_source_candidates(display" in writer_text
            and 'display.get("sections")' in writer_text
        ),
        "consumer_deduplicates_before_summary": (
            "if uid in seen:" in consumer_text
            and "duplicate_event_uids += 1" in consumer_text
            and "continue" in consumer_text
        ),
        "consumer_filters_unsafe_before_summary": (
            "unsafe_events += 1" in consumer_text
            and 'obj.get("lane") != expected_lane' in consumer_text
        ),
        "consumer_latest_market_capped_25": 'latest_market": list(reversed(market["events"]))[:25]' in consumer_text,
        "consumer_latest_adversarial_capped_25": 'latest_adversarial": list(reversed(adversarial["events"]))[:25]' in consumer_text,
        "display_safe_items_default_25": "def safe_items(items: Any, max_items: int = 25)" in display_text,
        "display_market_capped_25": 'safe_items(summary.get("latest_market"), 25)' in display_text,
        "display_adversarial_capped_25": 'safe_items(summary.get("latest_adversarial"), 25)' in display_text,
        "gateway_final_cap_50": "return deduped[:50]" in gateway_text,
    }
    if not all(source_chain.values()):
        missing = sorted(key for key, value in source_chain.items() if not value)
        raise RuntimeError("SOURCE_CHAIN_EVIDENCE_MISSING:" + ",".join(missing))

    real = a11["real_source_snapshot"]
    assert real["source_candidate_count"] == 50
    assert real["writer_queue_count"] == 50
    assert real["gateway_queue_count"] == 50
    assert real["counts"]["duplicate_removed_count"] == 0
    assert real["counts"]["unsafe_filtered_count"] == 0
    assert real["counts"]["invalid_candidate_count"] == 0
    assert real["counts"]["overflow_count"] == 0
    assert real["counts"]["replaced_count"] == 0

    now = utc_now()
    result = "REJECT_BOUNDED_CANARY_SOURCE_ALREADY_FILTERED_AND_TRUNCATED"

    artifact = {
        "schema_version": "1.0",
        "work_unit": "ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION",
        "timestamp_utc": now,
        "status": "CLOSED_BOUNDED_CANARY_REJECTED",
        "result": result,
        "a11_evidence": {
            "writer_module_implemented": True,
            "temp_copy_binding_ok": True,
            "idempotent_replay_ok": True,
            "postcommit_recovery_ok": True,
            "six_disposition_synthetic_model_ok": True,
            "transaction_rollback_ok": True,
            "production_unchanged": True,
        },
        "source_chain_audit": source_chain,
        "critical_finding": {
            "classification": "BOUND_SOURCE_IS_POST_FILTER_POST_DEDUP_POST_TRUNCATION",
            "writer_input": "runtime/state/news_coverage_panel_display_v1.json",
            "consumer_behavior": "DEDUPLICATE_AND_UNSAFE_FILTER_BEFORE_SUMMARY",
            "consumer_lane_caps": {"market": 25, "adversarial": 25},
            "display_lane_caps": {"market": 25, "adversarial": 25},
            "gateway_total_cap": 50,
            "real_a11_candidate_count": int(real["source_candidate_count"]),
            "real_a11_negative_dispositions": 0,
            "meaning": (
                "The writer algorithm is correct, but the bound live-shaped source cannot expose records "
                "already discarded by consumer deduplication, unsafe filtering, parse rejection, lane caps, "
                "or the final gateway cap. Zero unobservable rows is therefore not proven for an unbounded real cycle."
            ),
        },
        "authorization": {
            "bounded_canary_authorized": False,
            "production_writer_activation_authorized": False,
            "production_writer_active": False,
            "p0_f1_closed": False,
            "option_b_authorized": False,
            "optimization_apply_authorized": False,
        },
        "a13_scope": {
            "id": NEXT_STEP,
            "temp_copy_only": True,
            "production_db_mutation": False,
            "service_timer_panel_mutation": False,
            "requirements": [
                "Extract a deterministic candidate stream directly from the market and adversarial JSONL inputs before consumer deduplication and truncation.",
                "Preserve parse failures, duplicate candidates and unsafe candidates as explicit ledger dispositions.",
                "Bind the existing writer module to that pre-gateway stream on a disposable database copy.",
                "Prove real source count exceeds or independently differs from the 50-row display projection when historical input contains more records.",
                "Prove zero unobservable rows across the complete pre-gateway candidate stream.",
                "Preserve current gateway output parity and keep all production feature flags disabled.",
            ],
        },
        "production_guard_before": production_guard_before,
        "production_unchanged": True,
        "next_safe_step": NEXT_STEP,
    }
    write_json(DECISION_ARTIFACT, artifact)

    runtime = load_json(RUNTIME)
    state = runtime["current_state"]
    state["mode"] = "ERA55A12_BOUNDED_CANARY_REJECTED_SOURCE_ALREADY_TRUNCATED"
    state["runtime_status"] = "WORK_UNIT_CLOSED"
    state["updated_at"] = now
    state["last_action"] = {
        "timestamp": now,
        "task": "ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION",
        "result": result,
        "artifact": str(DECISION_ARTIFACT.relative_to(ROOT)),
    }
    state["active_work_unit"] = {
        "id": "ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION",
        "type": "ERA55_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_CANARY_DECISION",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "artifact": str(DECISION_ARTIFACT.relative_to(ROOT)),
        "status": "CLOSED_BOUNDED_CANARY_REJECTED",
        "result": result,
        "production_mutation": False,
        "next_step": NEXT_STEP,
    }
    state["next_safe_step"] = {
        "id": NEXT_STEP,
        "type": "ERA55_P0_PRE_GATEWAY_CANDIDATE_STREAM_EXTRACTION_TEMP_COPY_BINDING_TEST",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "purpose": (
            "Bind the existing writer to a complete pre-gateway JSONL candidate stream on a disposable database copy."
        ),
        "temp_copy_required": True,
        "human_authorization_required": False,
        "production_writer_activation_authorized": False,
        "bounded_canary_authorized": False,
        "option_b_authorized": False,
        "optimization_apply_authorized": False,
        "status": "READY",
    }
    state["current_problem"] = {
        "code": "LEDGER_WRITER_SOURCE_ALREADY_FILTERED_AND_TRUNCATED",
        "severity": "P0",
        "evidence": str(DECISION_ARTIFACT.relative_to(ROOT)),
    }
    runtime["current_work_unit"] = state["active_work_unit"]
    write_json(RUNTIME, runtime)

    history = load_json(HISTORY)
    events = history.setdefault("events", [])
    event_id = "ERA55A12_BOUNDED_CANARY_DECISION_V1"
    if not any(isinstance(event, dict) and event.get("event_id") == event_id for event in events):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": now,
                "era": "ERA55",
                "work_unit": "ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION",
                "event": "BOUNDED_CANARY_DECISION",
                "status": "CLOSED_BOUNDED_CANARY_REJECTED",
                "result": result,
                "artifact": str(DECISION_ARTIFACT.relative_to(ROOT)),
                "writer_module_validated": True,
                "source_pre_gateway": False,
                "production_unchanged": True,
                "bounded_canary_authorized": False,
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
PROJECT_STATUS=ACTIVE_ERA55_P0_PRE_GATEWAY_CANDIDATE_STREAM_REQUIRED
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
CURRENT_STAGE=ERA55A_P0_PRE_GATEWAY_CANDIDATE_STREAM
LAST_COMPLETED_SUBSTEP=ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION
A11_WRITER_MODULE_VALIDATED=true
A11_REAL_DISPLAY_BINDING_VALIDATED=true
A12_SOURCE_CHAIN_AUDITED=true
PRE_GATEWAY_SOURCE_BOUND=false
BOUNDED_CANARY_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
```

The writer module is valid. Canary activation is rejected because the current binding starts after consumer filtering, deduplication and 25+25 truncation.""",
    )
    master = replace_section(
        master,
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED=ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION
LAST_RESULT={result}
LAST_ARTIFACT={DECISION_ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS=CLOSED_BOUNDED_CANARY_REJECTED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
```

NEXT_SAFE_STEP={NEXT_STEP}""",
    )
    MASTER.write_text(master, encoding="utf-8")

    handoff = HANDOFF.read_text(encoding="utf-8")
    handoff = replace_section(
        handoff,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        f"""PROJECT_STATUS=ACTIVE_ERA55_P0_PRE_GATEWAY_CANDIDATE_STREAM_REQUIRED
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_P0_PRE_GATEWAY_CANDIDATE_STREAM
LAST_COMPLETED_SUBSTEP=ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION
A11_WRITER_MODULE_VALIDATED=true
CURRENT_BINDING_SOURCE=POST_FILTER_POST_DEDUP_POST_TRUNCATION_DISPLAY
PRE_GATEWAY_SOURCE_BOUND=false
BOUNDED_CANARY_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
OPTIMIZATION_APPLY_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

A12 rejected the bounded canary. Only A13 pre-gateway JSONL candidate-stream extraction and temp-copy binding is authorized.""",
    )
    handoff = replace_section(
        handoff,
        "## 03 LAST VERIFIED WORK",
        f"""LAST_COMPLETED=ERA55A_12_P0_RUNTIME_LEDGER_WRITER_POST_TEST_AUDIT_AND_BOUNDED_CANARY_DECISION
LAST_RESULT={result}
LAST_ARTIFACT={DECISION_ARTIFACT.relative_to(ROOT)}
WORK_UNIT_STATUS=CLOSED_BOUNDED_CANARY_REJECTED
LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=LEDGER_WRITER_SOURCE_ALREADY_FILTERED_AND_TRUNCATED""",
    )
    handoff = replace_section(
        handoff,
        "## 06 DO NOT REOPEN OR REPEAT",
        """- Do not rerun A9-A11 unless evidence is invalidated.
- Do not authorize a bounded canary from the display-bound A11 evidence.
- Do not treat 50 admitted display rows as proof of complete candidate accounting.
- Do not enable production writer or runner-lock feature flags.
- Do not modify live DB, service, timer, gateway or panel during A13.
- Do not start Option B or mark P0 F1 closed.""",
    )
    handoff = replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Writer module: `VALIDATED`.
- Display-bound temp-copy integration: `VALIDATED_WITH_SOURCE_LIMITATION`.
- Pre-gateway complete candidate accounting: `NOT_PROVEN`.
- Bounded canary: `REJECTED_SOURCE_ALREADY_FILTERED_AND_TRUNCATED`.
- Production activation: `BLOCKED`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT_STEP}""",
    )
    handoff = replace_section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Confirm A13 is current.
2. Read both lane JSONL files directly before consumer filtering and truncation.
3. Convert every non-empty physical source line into one candidate observation, including parse failures.
4. Preserve duplicate and unsafe observations as ledger dispositions instead of dropping them.
5. Bind the existing writer to the extracted stream only on a disposable DB copy.
6. Prove complete accounting, queue parity, idempotency, rollback and recovery without production activation.""",
    )
    HANDOFF.write_text(handoff, encoding="utf-8")

    almanac = ALMANAC.read_text(encoding="utf-8")
    marker = "## ERA55A_12 BOUNDED CANARY DECISION"
    if marker not in almanac:
        ALMANAC.write_text(
            almanac.rstrip()
            + f"""

---

{marker}

- Status: `CLOSED_BOUNDED_CANARY_REJECTED`
- Result: `{result}`
- Writer module: `VALIDATED`
- Current source: `POST_FILTER_POST_DEDUP_POST_TRUNCATION`
- Pre-gateway source bound: `false`
- Production mutation: `false`
- Bounded canary authorized: `false`
- Production writer activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `{NEXT_STEP}`
"""
            + "\n",
            encoding="utf-8",
        )

    production_guard_after = {
        "database": file_guard(DB),
        "hot_output": file_guard(HOT_OUTPUT),
        "recovery_state": file_guard(RECOVERY_STATE),
        "service_environment": service_environment(),
        "database_state": production_db_state(),
    }
    assert production_guard_before == production_guard_after
    artifact["production_guard_after"] = production_guard_after
    write_json(DECISION_ARTIFACT, artifact)

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

    print("ERA55A12_CANARY_DECISION=SUCCESS")
    print("DECISION=" + result)
    print("WRITER_MODULE_VALIDATED=true")
    print("BOUND_SOURCE_PRE_GATEWAY=false")
    print("BOUND_SOURCE_POST_FILTER=true")
    print("BOUND_SOURCE_POST_DEDUP=true")
    print("BOUND_SOURCE_TRUNCATED_25_PLUS_25=true")
    print("BOUNDED_CANARY_AUTHORIZED=false")
    print("PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
    print("PRODUCTION_UNCHANGED=true")
    print("P0_F1_CLOSED=false")
    print("OPTION_B_AUTHORIZED=false")
    print("NEXT_SAFE_STEP=" + NEXT_STEP)
    print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
    print("ARTIFACT=" + str(DECISION_ARTIFACT.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
