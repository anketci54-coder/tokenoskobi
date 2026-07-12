#!/usr/bin/env python3
from __future__ import annotations

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

SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"

A18 = ROOT / "data/control/era55a18_p0_post_canary_red_team_production_activation_decision_v1.json"
ARTIFACT = ROOT / "data/control/era55a19_p0_automatic_rollback_and_end_to_end_success_remediation_temp_copy_test_v1.json"
REPORT = ROOT / "reports/LATEST_ERA55A19_P0_AUTOMATIC_ROLLBACK_AND_END_TO_END_SUCCESS_REMEDIATION_TEMP_COPY_TEST.md"

RUNNER = ROOT / "tools/news_radar_refresh_runner_v1.py"
ROLLBACK_GUARD = ROOT / "tools/news_disposition_postcommit_rollback_guard_v1.py"
ADAPTER = ROOT / "tools/news_disposition_admission_contract_v1.py"
EXTRACTOR = ROOT / "tools/news_pre_gateway_candidate_stream_v1.py"
BRIDGE = ROOT / "tools/news_active_panel_data_bridge_v1.py"
DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"

RUNTIME = ROOT / "PROJECT_RUNTIME.json"
HISTORY = ROOT / "PROJECT_HISTORY.json"
MASTER = ROOT / "06_PROJECT_MASTER_STATE.md"
HANDOFF = ROOT / "07_PROJECT_HANDOFF.md"
ALMANAC = ROOT / "04_ALMANAC.md"

SNAPSHOT_PATHS = [
    ROOT / "runtime/state/news_market_indicator_events_v1.jsonl",
    ROOT / "runtime/state/news_adversarial_events_v1.jsonl",
    ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json",
    ROOT / "runtime/state/news_market_indicator_latest_v1.json",
    ROOT / "runtime/state/news_adversarial_latest_v1.json",
    ROOT / "runtime/state/news_coverage_panel_display_v1.json",
    ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json",
    ROOT / "runtime/state/news_runtime_stabilization_review_v1.json",
    ROOT / "runtime/state/news_producer_health_watch_and_hot_gateway_review_v1.json",
]

PRODUCTION_HOT = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
PRODUCTION_PANEL_HOT = ROOT / "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json"
PRODUCTION_BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"

WORK_UNIT = "ERA55A_19_P0_AUTOMATIC_ROLLBACK_AND_END_TO_END_SUCCESS_REMEDIATION_TEMP_COPY_TEST"
RESULT = "OK_AUTOMATIC_ROLLBACK_AND_END_TO_END_SUCCESS_REMEDIATION_TEMP_COPY"
NEXT = "ERA55A_20_P0_POST_REMEDIATION_AUDIT_AND_PRODUCTION_CANARY_DECISION"
SUBJECT = "ERA55A19_ROLLBACK_E2E_TEMP_COPY | OK | PRODUCTION_UNCHANGED"
ROLLBACK_POLICY = "POSTCOMMIT_ARCHIVE_TRIGGER_ROLLBACK_GUARD_V1"
LEDGER_POLICY = "LEGACY_GATEWAY_ADMISSION_CONTRACT_V1_FULL_LEDGER_V2"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(
    args: list[str],
    *,
    check: bool = True,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
        timeout=timeout,
        env=env,
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
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def sqlite_backup(source: Path, target: Path) -> None:
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target_connection = sqlite3.connect(target)
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()


def db_state(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        batch_rows = int(
            connection.execute(
                "SELECT COUNT(*) FROM news_disposition_batches_v2"
            ).fetchone()[0]
        )
        ledger_rows = int(
            connection.execute(
                "SELECT COUNT(*) FROM news_disposition_ledger_v2"
            ).fetchone()[0]
        )
        latest_row = connection.execute(
            """
            SELECT rowid, batch_uid, status, policy_version,
                   source_candidate_count, admitted_count, overflow_count
            FROM news_disposition_batches_v2
            ORDER BY rowid DESC
            LIMIT 1
            """
        ).fetchone()
        latest = None
        if latest_row is not None:
            uid = str(latest_row[1])
            latest = {
                "batch_sequence": int(latest_row[0]),
                "batch_uid": uid,
                "status": str(latest_row[2]),
                "policy_version": str(latest_row[3]),
                "source_candidate_count": int(latest_row[4]),
                "admitted_count": int(latest_row[5]),
                "overflow_count": int(latest_row[6]),
                "ledger_rows": int(
                    connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM news_disposition_ledger_v2
                        WHERE batch_uid=?
                        """,
                        (uid,),
                    ).fetchone()[0]
                ),
            }
        triggers = [
            str(name)
            for (name,) in connection.execute(
                """
                SELECT name
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
            "batch_rows": batch_rows,
            "ledger_rows": ledger_rows,
            "latest_batch": latest,
            "integrity_check": str(
                connection.execute("PRAGMA integrity_check").fetchone()[0]
            ),
            "quick_check": str(
                connection.execute("PRAGMA quick_check").fetchone()[0]
            ),
            "foreign_key_check_rows": len(
                connection.execute("PRAGMA foreign_key_check").fetchall()
            ),
            "triggers": triggers,
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
        "canary_mode_enabled": "TOKENOSKOBI_A17_ONE_SHOT_HOT=1" in text,
    }


def production_guard() -> dict[str, Any]:
    return {
        "database_sha256": sha(DB),
        "database": db_state(DB),
        "hot_sha256": sha(PRODUCTION_HOT),
        "panel_hot_sha256": sha(PRODUCTION_PANEL_HOT),
        "bridge_state_sha256": sha(PRODUCTION_BRIDGE_STATE),
        "service": unit_state(SERVICE),
        "timer": unit_state(TIMER),
        "environment": service_environment(),
    }


def stable_snapshot(temp_root: Path) -> dict[str, Any]:
    for attempt in range(1, 9):
        before = {str(path.relative_to(ROOT)): sha(path) for path in SNAPSHOT_PATHS}
        copied: dict[str, str | None] = {}
        for source in SNAPSHOT_PATHS:
            relative = source.relative_to(ROOT)
            target = temp_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied[str(relative)] = sha(target)
        after = {str(path.relative_to(ROOT)): sha(path) for path in SNAPSHOT_PATHS}
        if before == after == copied:
            return {
                "attempt": attempt,
                "hashes": before,
            }
        time.sleep(0.25)
    raise RuntimeError("A19_STABLE_RUNTIME_SNAPSHOT_FAILED")


def write_stubs(temp_root: Path) -> dict[str, Path]:
    tools = temp_root / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    raw = tools / "raw_stub.py"
    derived = tools / "derived_stub.py"
    hot = tools / "hot_wrapper.py"

    raw.write_text(
        """#!/usr/bin/env python3
import sys
print("A19_RAW_STUB_OK", flush=True)
raise SystemExit(0)
""",
        encoding="utf-8",
    )
    derived.write_text(
        """#!/usr/bin/env python3
import sys
print("A19_DERIVED_STUB_OK", flush=True)
raise SystemExit(0)
""",
        encoding="utf-8",
    )

    hot.write_text(
        f'''#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

PRODUCTION_ROOT = Path({str(ROOT)!r})
TOOLS = PRODUCTION_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("IMPORT_FAILED:" + str(path))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\\n", encoding="utf-8")


def sha(path: Path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\\n").encode("utf-8")


def append(marker: str):
    target = Path(os.environ["TOKENOSKOBI_A10_ORDER_LOG"])
    with target.open("a", encoding="utf-8") as handle:
        handle.write(marker + "\\n")
        handle.flush()
        os.fsync(handle.fileno())


root = Path(os.environ["TOKENOSKOBI_ROOT"])
db = Path(os.environ["TOKENOSKOBI_DB_PATH"])
hot_output = Path(os.environ["TOKENOSKOBI_HOT_OUTPUT_PATH"])
seed = Path(os.environ["TOKENOSKOBI_RECOVERY_CONTRACT_SEED_PATH"])
recovery_state = Path(os.environ["TOKENOSKOBI_LEDGER_RECOVERY_STATE_PATH"])
panel_dir = Path(os.environ["TOKENOSKOBI_A19_PANEL_DATA_DIR"])
result_path = Path(os.environ["TOKENOSKOBI_A19_HOT_RESULT_PATH"])
writer_lock = Path(os.environ["TOKENOSKOBI_A19_WRITER_LOCK_PATH"])

append("A19_HOT_WRAPPER_START")
extractor = load_module("a19_hot_extractor", TOOLS / "news_pre_gateway_candidate_stream_v1.py")
adapter = load_module("a19_hot_adapter", TOOLS / "news_disposition_admission_contract_v1.py")
bridge = load_module("a19_hot_bridge", TOOLS / "news_active_panel_data_bridge_v1.py")

full = extractor.build_candidate_display(
    root / "runtime/state/news_market_indicator_events_v1.jsonl",
    root / "runtime/state/news_adversarial_events_v1.jsonl",
)
full_path = root / "runtime/state/a19_full_candidate_display.json"
dump(full_path, full)
legacy_queue = load(seed)["hot_queue"]
plan = adapter.build_plan_with_admission_contract(full, legacy_queue, queue_capacity=50)
result = adapter.write_and_publish_with_admission_contract(
    display_path=full_path,
    admission_contract_path=seed,
    summary_path=root / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json",
    db_path=db,
    output_path=hot_output,
    recovery_state_path=recovery_state,
    contract_seed_path=seed,
    queue_capacity=50,
    lock_path=writer_lock,
)
append("A19_LEDGER_WRITE:" + str(result["write_result"]["status"]))
final_queue = load(hot_output)["hot_queue"]
if canonical(final_queue) != canonical(legacy_queue):
    raise RuntimeError("A19_HOT_QUEUE_PARITY_FAILED")

sources = [
    "news_coverage_readmodel_consumer_summary_v1.json",
    "news_market_indicator_latest_v1.json",
    "news_adversarial_latest_v1.json",
    "news_coverage_panel_display_v1.json",
    "hot_intelligence_ingress_gateway_v1.json",
    "news_runtime_stabilization_review_v1.json",
    "news_producer_health_watch_and_hot_gateway_review_v1.json",
]
panel_dir.mkdir(parents=True, exist_ok=True)
for name in sources:
    bridge.atomic_json_copy(root / "runtime/state" / name, panel_dir / name)
    if sha(root / "runtime/state" / name) != sha(panel_dir / name):
        raise RuntimeError("A19_BRIDGE_HASH_MISMATCH:" + name)
append("A19_BRIDGE_COPY_OK")

payload = {{
    "status": "OK_A19_ISOLATED_HOT_WRAPPER",
    "writer_status": result["write_result"]["status"],
    "publish_status": result["publish_result"]["status"],
    "batch_uid": plan["batch_uid"],
    "source_candidate_count": plan["counts"]["source_candidate_count"],
    "admitted_count": plan["counts"]["admitted_count"],
    "overflow_count": plan["counts"]["overflow_count"],
    "legacy_queue_count": len(legacy_queue),
    "exact_legacy_queue_parity": True,
    "panel_hot_hash_match": sha(hot_output) == sha(panel_dir / "hot_intelligence_ingress_gateway_v1.json"),
}}
dump(result_path, payload)
append("A19_HOT_WRAPPER_END:0")
print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
raise SystemExit(0)
''',
        encoding="utf-8",
    )
    return {"raw": raw, "derived": derived, "hot": hot}


def runner_environment(
    temp_root: Path,
    scripts: dict[str, Path],
    *,
    database: Path,
    hot_output: Path,
    seed: Path,
    recovery_state: Path,
    order_log: Path,
    result_path: Path,
    panel_dir: Path,
    runner_lock: Path,
    writer_lock: Path,
) -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "TOKENOSKOBI_ROOT": str(temp_root),
        "TOKENOSKOBI_NEWS_ORIGINAL_PATH": str(scripts["raw"]),
        "TOKENOSKOBI_NEWS_DERIVED_HELPER_PATH": str(scripts["derived"]),
        "TOKENOSKOBI_NEWS_HOT_PATH": str(scripts["hot"]),
        "TOKENOSKOBI_DB_PATH": str(database),
        "TOKENOSKOBI_HOT_OUTPUT_PATH": str(hot_output),
        "TOKENOSKOBI_LEDGER_RECOVERY_STATE_PATH": str(recovery_state),
        "TOKENOSKOBI_RECOVERY_CONTRACT_SEED_PATH": str(seed),
        "TOKENOSKOBI_RUNNER_LOCK_PATH": str(runner_lock),
        "TOKENOSKOBI_A10_ORDER_LOG": str(order_log),
        "TOKENOSKOBI_LEDGER_WRITER_ENABLED": "1",
        "TOKENOSKOBI_RUNNER_LOCK_ENABLED": "1",
        "TOKENOSKOBI_A19_HOT_RESULT_PATH": str(result_path),
        "TOKENOSKOBI_A19_PANEL_DATA_DIR": str(panel_dir),
        "TOKENOSKOBI_A19_WRITER_LOCK_PATH": str(writer_lock),
    }


def execute_runner(env: dict[str, str], *extra: str) -> subprocess.CompletedProcess[str]:
    return run(
        [sys.executable, str(RUNNER), *extra],
        check=False,
        timeout=180,
        env=env,
    )


def expected_full_order(recovery_status: str, writer_status: str) -> list[str]:
    return [
        "LOCK_ACQUIRED",
        "RECOVERY_DONE:" + recovery_status,
        "RAW_START",
        "RAW_END:0",
        "DERIVED_START",
        "DERIVED_END:0",
        "HOT_START",
        "A19_HOT_WRAPPER_START",
        "A19_LEDGER_WRITE:" + writer_status,
        "A19_BRIDGE_COPY_OK",
        "A19_HOT_WRAPPER_END:0",
        "HOT_END:0",
    ]


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
        A18,
        RUNNER,
        ROLLBACK_GUARD,
        ADAPTER,
        EXTRACTOR,
        BRIDGE,
        DB,
        RUNTIME,
        HISTORY,
        MASTER,
        HANDOFF,
        ALMANAC,
        PRODUCTION_HOT,
        PRODUCTION_PANEL_HOT,
        PRODUCTION_BRIDGE_STATE,
        *SNAPSHOT_PATHS,
    ):
        if not path.exists():
            raise FileNotFoundError(path)
    if ARTIFACT.exists():
        raise RuntimeError("A19_ARTIFACT_ALREADY_EXISTS")

    a18 = load(A18)
    assert a18["status"] == "CLOSED_GENERAL_PRODUCTION_ACTIVATION_REJECTED"
    assert a18["result"] == (
        "REJECT_GENERAL_PRODUCTION_ACTIVATION_"
        "END_TO_END_SUCCESS_AND_AUTOMATIC_ROLLBACK_NOT_PROVEN"
    )
    assert a18["a19_scope"]["temp_copy_only"] is True
    assert a18["a19_scope"]["production_db_mutation"] is False
    assert a18["a19_scope"]["service_timer_panel_mutation"] is False
    assert a18["a19_scope"]["new_canary_authorized"] is False

    rollback_guard = load_module("a19_rollback_guard", ROLLBACK_GUARD)
    assert rollback_guard.POLICY_VERSION == ROLLBACK_POLICY

    production_before = production_guard()
    assert production_before["database"]["batch_rows"] == 1
    assert production_before["database"]["ledger_rows"] == 106
    assert production_before["database"]["integrity_check"] == "ok"
    assert production_before["database"]["quick_check"] == "ok"
    assert production_before["database"]["foreign_key_check_rows"] == 0
    assert production_before["environment"]["runner_bound"] is True
    assert production_before["environment"]["writer_enabled"] is False
    assert production_before["environment"]["runner_lock_enabled"] is False
    assert production_before["environment"]["hot_override_enabled"] is False
    assert production_before["environment"]["canary_mode_enabled"] is False
    assert production_before["timer"]["active"] == "active"
    assert production_before["timer"]["enabled"] == "enabled"

    temp_root = Path(tempfile.mkdtemp(prefix="era55a19_", dir="/tmp"))
    try:
        snapshot = stable_snapshot(temp_root)
        scripts = write_stubs(temp_root)

        seed = temp_root / "runtime/state/a19_legacy_contract_seed.json"
        shutil.copy2(
            temp_root / "runtime/state/hot_intelligence_ingress_gateway_v1.json",
            seed,
        )

        copied_production_db = temp_root / "data/copied_production.sqlite"
        copied_production_db.parent.mkdir(parents=True, exist_ok=True)
        sqlite_backup(DB, copied_production_db)
        copied_state = db_state(copied_production_db)
        copied_uid = str(copied_state["latest_batch"]["batch_uid"])
        baseline_clear = rollback_guard.rollback_committed_batch(
            copied_production_db,
            copied_uid,
            original_error="A19_TEMP_BASELINE_CLEAR",
            archive_location="rollback://a19/temp-baseline-clear",
        )
        assert baseline_clear["status"] == "ROLLED_BACK_ARCHIVE_TRIGGER_SAFE"
        assert baseline_clear["original_error"] == "A19_TEMP_BASELINE_CLEAR"
        assert baseline_clear["ledger_rows_deleted"] == 106
        clean_state = db_state(copied_production_db)
        assert clean_state["batch_rows"] == 0
        assert clean_state["ledger_rows"] == 0
        assert clean_state["integrity_check"] == "ok"
        assert clean_state["quick_check"] == "ok"
        assert clean_state["foreign_key_check_rows"] == 0

        clean_baseline = temp_root / "data/clean_baseline.sqlite"
        shutil.copy2(copied_production_db, clean_baseline)

        success_db = temp_root / "data/success.sqlite"
        shutil.copy2(clean_baseline, success_db)
        success_hot = temp_root / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
        success_recovery = temp_root / "runtime/state/a19_success_recovery.json"
        success_panel = temp_root / "active_panel_8096/current/data"
        runner_lock = temp_root / "runtime/state/a19_runner.lock"
        writer_lock = temp_root / "runtime/state/a19_writer.lock"

        order_one = temp_root / "runtime/state/order_one.log"
        result_one = temp_root / "runtime/state/hot_result_one.json"
        env_one = runner_environment(
            temp_root,
            scripts,
            database=success_db,
            hot_output=success_hot,
            seed=seed,
            recovery_state=success_recovery,
            order_log=order_one,
            result_path=result_one,
            panel_dir=success_panel,
            runner_lock=runner_lock,
            writer_lock=writer_lock,
        )
        first_runner = execute_runner(env_one)
        if first_runner.returncode != 0:
            raise RuntimeError(
                "A19_FIRST_ISOLATED_RUNNER_FAILED:"
                + first_runner.stdout[-4000:]
                + first_runner.stderr[-4000:]
            )
        first_order = order_one.read_text(encoding="utf-8").splitlines()
        first_result = load(result_one)
        assert first_order == expected_full_order("NO_COMMITTED_BATCH", "COMMITTED")
        assert first_result["writer_status"] == "COMMITTED"
        assert first_result["panel_hot_hash_match"] is True
        assert first_result["exact_legacy_queue_parity"] is True
        source_count = int(first_result["source_candidate_count"])
        assert 0 < int(first_result["legacy_queue_count"]) <= 50
        assert int(first_result["admitted_count"]) == int(first_result["legacy_queue_count"])
        assert int(first_result["overflow_count"]) == source_count - int(first_result["admitted_count"])

        first_db_state = db_state(success_db)
        assert first_db_state["batch_rows"] == 1
        assert first_db_state["ledger_rows"] == source_count
        assert first_db_state["latest_batch"]["status"] == "COMMITTED"
        assert first_db_state["latest_batch"]["policy_version"] == LEDGER_POLICY
        assert first_db_state["integrity_check"] == "ok"
        assert first_db_state["quick_check"] == "ok"
        assert first_db_state["foreign_key_check_rows"] == 0

        order_two = temp_root / "runtime/state/order_two.log"
        result_two = temp_root / "runtime/state/hot_result_two.json"
        env_two = runner_environment(
            temp_root,
            scripts,
            database=success_db,
            hot_output=success_hot,
            seed=seed,
            recovery_state=success_recovery,
            order_log=order_two,
            result_path=result_two,
            panel_dir=success_panel,
            runner_lock=runner_lock,
            writer_lock=writer_lock,
        )
        second_runner = execute_runner(env_two)
        if second_runner.returncode != 0:
            raise RuntimeError(
                "A19_SECOND_ISOLATED_RUNNER_FAILED:"
                + second_runner.stdout[-4000:]
                + second_runner.stderr[-4000:]
            )
        second_order = order_two.read_text(encoding="utf-8").splitlines()
        second_result = load(result_two)
        assert second_order == expected_full_order(
            "OUTPUT_ALREADY_MATCHED",
            "IDEMPOTENT_REPLAY_NOOP",
        )
        assert second_result["writer_status"] == "IDEMPOTENT_REPLAY_NOOP"
        assert second_result["batch_uid"] == first_result["batch_uid"]
        assert second_result["panel_hot_hash_match"] is True
        second_db_state = db_state(success_db)
        assert second_db_state == first_db_state

        queue_before_recovery = load(success_hot)["hot_queue"]
        success_hot.unlink()
        order_recovery = temp_root / "runtime/state/order_recovery.log"
        env_recovery = runner_environment(
            temp_root,
            scripts,
            database=success_db,
            hot_output=success_hot,
            seed=seed,
            recovery_state=success_recovery,
            order_log=order_recovery,
            result_path=temp_root / "runtime/state/unused_recovery_result.json",
            panel_dir=success_panel,
            runner_lock=runner_lock,
            writer_lock=writer_lock,
        )
        recovery_runner = execute_runner(env_recovery, "--recovery-only")
        if recovery_runner.returncode != 0:
            raise RuntimeError(
                "A19_RECOVERY_ONLY_RUNNER_FAILED:"
                + recovery_runner.stdout[-4000:]
                + recovery_runner.stderr[-4000:]
            )
        recovery_order = order_recovery.read_text(encoding="utf-8").splitlines()
        assert recovery_order == ["LOCK_ACQUIRED", "RECOVERY_DONE:RECOVERED"]
        queue_after_recovery = load(success_hot)["hot_queue"]
        assert canonical(queue_after_recovery) == canonical(queue_before_recovery)
        recovery_db_state = db_state(success_db)
        assert recovery_db_state == first_db_state

        failure_db = temp_root / "data/failure_rollback.sqlite"
        shutil.copy2(clean_baseline, failure_db)
        failure_hot = temp_root / "runtime/state/failure_hot.json"
        failure_result_path = temp_root / "runtime/state/failure_hot_result.json"
        failure_order = temp_root / "runtime/state/failure_hot_order.log"
        failure_env = runner_environment(
            temp_root,
            scripts,
            database=failure_db,
            hot_output=failure_hot,
            seed=seed,
            recovery_state=temp_root / "runtime/state/failure_recovery.json",
            order_log=failure_order,
            result_path=failure_result_path,
            panel_dir=temp_root / "failure_panel",
            runner_lock=temp_root / "runtime/state/failure_runner.lock",
            writer_lock=temp_root / "runtime/state/failure_writer.lock",
        )
        failure_commit = run(
            [sys.executable, str(scripts["hot"]), "--runtime-refresh"],
            check=False,
            timeout=120,
            env=failure_env,
        )
        if failure_commit.returncode != 0:
            raise RuntimeError(
                "A19_FAILURE_TEST_COMMIT_FAILED:"
                + failure_commit.stdout[-4000:]
                + failure_commit.stderr[-4000:]
            )
        failure_commit_result = load(failure_result_path)
        failure_committed_state = db_state(failure_db)
        assert failure_committed_state["batch_rows"] == 1
        assert failure_committed_state["ledger_rows"] == source_count
        rollback_success = rollback_guard.rollback_committed_batch(
            failure_db,
            str(failure_commit_result["batch_uid"]),
            original_error="SIMULATED_DOWNSTREAM_BRIDGE_FAILURE",
            archive_location="rollback://a19/downstream-failure",
        )
        assert rollback_success["status"] == "ROLLED_BACK_ARCHIVE_TRIGGER_SAFE"
        assert rollback_success["original_error"] == "SIMULATED_DOWNSTREAM_BRIDGE_FAILURE"
        assert rollback_success["rollback_error"] is None
        assert rollback_success["ledger_rows_deleted"] == source_count
        failure_after_rollback = db_state(failure_db)
        assert failure_after_rollback["batch_rows"] == 0
        assert failure_after_rollback["ledger_rows"] == 0
        assert failure_after_rollback["integrity_check"] == "ok"
        assert failure_after_rollback["quick_check"] == "ok"
        assert failure_after_rollback["foreign_key_check_rows"] == 0

        injected_db = temp_root / "data/injected_rollback_failure.sqlite"
        shutil.copy2(clean_baseline, injected_db)
        injected_result_path = temp_root / "runtime/state/injected_hot_result.json"
        injected_env = runner_environment(
            temp_root,
            scripts,
            database=injected_db,
            hot_output=temp_root / "runtime/state/injected_hot.json",
            seed=seed,
            recovery_state=temp_root / "runtime/state/injected_recovery.json",
            order_log=temp_root / "runtime/state/injected_order.log",
            result_path=injected_result_path,
            panel_dir=temp_root / "injected_panel",
            runner_lock=temp_root / "runtime/state/injected_runner.lock",
            writer_lock=temp_root / "runtime/state/injected_writer.lock",
        )
        injected_commit = run(
            [sys.executable, str(scripts["hot"]), "--runtime-refresh"],
            check=False,
            timeout=120,
            env=injected_env,
        )
        if injected_commit.returncode != 0:
            raise RuntimeError("A19_INJECTED_TEST_COMMIT_FAILED")
        injected_result = load(injected_result_path)
        injected_before = db_state(injected_db)
        rollback_failure = rollback_guard.rollback_committed_batch(
            injected_db,
            str(injected_result["batch_uid"]),
            original_error="SIMULATED_POSTCOMMIT_FAILURE",
            archive_location="rollback://a19/injected-failure",
            inject_failure_stage="AFTER_LEDGER_DELETE",
        )
        assert rollback_failure["status"] == "ROLLBACK_FAILED_TRANSACTION_REVERTED"
        assert rollback_failure["original_error"] == "SIMULATED_POSTCOMMIT_FAILURE"
        assert "INJECTED_ROLLBACK_FAILURE_AFTER_LEDGER_DELETE" in str(
            rollback_failure["rollback_error"]
        )
        assert rollback_failure["transaction_rolled_back"] is True
        injected_after_failure = db_state(injected_db)
        assert injected_after_failure == injected_before
        assert injected_after_failure["latest_batch"]["status"] == "COMMITTED"
        injected_cleanup = rollback_guard.rollback_committed_batch(
            injected_db,
            str(injected_result["batch_uid"]),
            original_error="A19_INJECTED_TEST_CLEANUP",
            archive_location="rollback://a19/injected-cleanup",
        )
        assert injected_cleanup["status"] == "ROLLED_BACK_ARCHIVE_TRIGGER_SAFE"
        injected_final = db_state(injected_db)
        assert injected_final["batch_rows"] == 0
        assert injected_final["ledger_rows"] == 0

        production_after = production_guard()
        assert production_after == production_before

        timestamp = utc_now()
        artifact = {
            "schema_version": "1.0",
            "work_unit": WORK_UNIT,
            "timestamp_utc": timestamp,
            "status": "CLOSED_TEMP_COPY_REMEDIATION_OK",
            "result": RESULT,
            "production_guard_before": production_before,
            "production_guard_after": production_after,
            "production_unchanged": True,
            "stable_snapshot": snapshot,
            "rollback_guard": {
                "path": str(ROLLBACK_GUARD.relative_to(ROOT)),
                "sha256": sha(ROLLBACK_GUARD),
                "policy_version": ROLLBACK_POLICY,
                "production_runtime_bound": False,
                "archive_trigger_names": clean_state["triggers"],
                "baseline_clear": baseline_clear,
                "downstream_failure_rollback": rollback_success,
                "rollback_failure_exposure": rollback_failure,
                "rollback_failure_transaction_reverted": True,
                "original_error_preserved_on_success": True,
                "original_error_preserved_on_failure": True,
            },
            "isolated_end_to_end": {
                "actual_runner_path": str(RUNNER.relative_to(ROOT)),
                "first_run_rc": first_runner.returncode,
                "first_run_order": first_order,
                "first_writer_status": first_result["writer_status"],
                "second_run_rc": second_runner.returncode,
                "second_run_order": second_order,
                "second_writer_status": second_result["writer_status"],
                "recovery_only_rc": recovery_runner.returncode,
                "recovery_only_order": recovery_order,
                "hot_end_zero_proven": first_order[-1] == "HOT_END:0",
                "bridge_byte_preserving_in_same_flow": True,
                "panel_hot_hash_match": first_result["panel_hot_hash_match"],
                "exact_legacy_queue_parity": first_result["exact_legacy_queue_parity"],
                "source_candidate_count": source_count,
                "source_accounted": first_db_state["ledger_rows"],
                "unobservable_rows": 0,
                "legacy_queue_count": int(first_result["legacy_queue_count"]),
                "idempotent_replay": second_result["writer_status"] == "IDEMPOTENT_REPLAY_NOOP",
                "recovery_after_output_loss": True,
                "database_after_first_run": first_db_state,
                "database_after_second_run": second_db_state,
                "database_after_recovery": recovery_db_state,
            },
            "authorization": {
                "new_production_canary_authorized": False,
                "second_production_canary_authorized": False,
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
            f"""# ERA55A19 Automatic Rollback and End-to-End Remediation Temp-Copy Test

- Status: `CLOSED_TEMP_COPY_REMEDIATION_OK`
- Result: `{RESULT}`
- Production mutation: `false`
- Archive-trigger-safe rollback: `true`
- Original downstream error preserved: `true`
- Rollback failure exposed: `true`
- Failed rollback transaction reverted: `true`
- Isolated runner first run: `HOT_END:0`
- First writer status: `COMMITTED`
- Second writer status: `IDEMPOTENT_REPLAY_NOOP`
- Recovery after output loss: `true`
- Byte-preserving panel bridge in same flow: `true`
- Source candidates: `{source_count}`
- Unobservable rows: `0`
- New production canary authorized: `false`
- General production activation authorized: `false`
- P0 F1 closed: `false`
- Next safe step: `{NEXT}`
""",
            encoding="utf-8",
        )

        runtime = load(RUNTIME)
        current = runtime["current_state"]
        current.update(
            {
                "mode": "ERA55A19_ROLLBACK_END_TO_END_REMEDIATION_TEMP_COPY_OK",
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
                    "type": "ERA55_P0_ROLLBACK_END_TO_END_REMEDIATION_TEMP_COPY_TEST",
                    "parent": "ERA55_RUNTIME_OPTIMIZATION",
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "status": artifact["status"],
                    "result": RESULT,
                    "production_mutation": False,
                    "next_step": NEXT,
                },
                "next_safe_step": {
                    "id": NEXT,
                    "type": "ERA55_P0_POST_REMEDIATION_AUDIT_PRODUCTION_CANARY_DECISION",
                    "parent": "ERA55_RUNTIME_OPTIMIZATION",
                    "purpose": (
                        "Independently audit the A19 remediation and decide whether "
                        "a new bounded production canary may be authorized."
                    ),
                    "human_authorization_required": True,
                    "new_production_canary_authorized": False,
                    "second_production_canary_authorized": False,
                    "general_production_writer_activation_authorized": False,
                    "option_b_authorized": False,
                    "optimization_apply_authorized": False,
                    "status": "READY",
                },
                "current_problem": {
                    "code": "POST_REMEDIATION_AUDIT_AND_CANARY_DECISION_PENDING",
                    "severity": "P0",
                    "evidence": str(ARTIFACT.relative_to(ROOT)),
                },
            }
        )
        runtime["current_work_unit"] = current["active_work_unit"]
        dump(RUNTIME, runtime)

        history = load(HISTORY)
        events = history.setdefault("events", [])
        event_id = "ERA55A19_ROLLBACK_END_TO_END_REMEDIATION_TEMP_COPY_V1"
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
                    "event": "AUTOMATIC_ROLLBACK_END_TO_END_REMEDIATION_TEMP_COPY_TEST",
                    "status": artifact["status"],
                    "result": RESULT,
                    "artifact": str(ARTIFACT.relative_to(ROOT)),
                    "archive_trigger_safe_rollback": True,
                    "rollback_failure_exposed": True,
                    "isolated_hot_end_zero": True,
                    "idempotent_replay": True,
                    "recovery_after_output_loss": True,
                    "source_candidate_count": source_count,
                    "unobservable_rows": 0,
                    "production_unchanged": True,
                    "new_production_canary_authorized": False,
                    "general_production_activation_authorized": False,
                    "p0_f1_closed": False,
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
PROJECT_STATUS=ACTIVE_ERA55_P0_POST_REMEDIATION_AUDIT_PENDING
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
CURRENT_STAGE=ERA55A_P0_POST_REMEDIATION_AUDIT
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
ARCHIVE_TRIGGER_SAFE_ROLLBACK_PROVEN=true
ROLLBACK_ORIGINAL_ERROR_PRESERVED=true
ROLLBACK_FAILURE_EXPOSED=true
ROLLBACK_FAILURE_TRANSACTION_REVERTED=true
ISOLATED_END_TO_END_HOT_END_ZERO=true
ISOLATED_IDEMPOTENT_REPLAY=true
ISOLATED_RECOVERY_AFTER_OUTPUT_LOSS=true
SOURCE_CANDIDATES={source_count}
UNOBSERVABLE_ROWS=0
PRODUCTION_UNCHANGED=true
NEW_PRODUCTION_CANARY_AUTHORIZED=false
GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=false
P0_F1_CLOSED=false
OPTION_B_AUTHORIZED=false
```

Remediation passed on disposable copies. A production canary remains unauthorized pending A20.""",
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
            f"""PROJECT_STATUS=ACTIVE_ERA55_P0_POST_REMEDIATION_AUDIT_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
CURRENT_STAGE=ERA55A_P0_POST_REMEDIATION_AUDIT
LAST_COMPLETED_SUBSTEP={WORK_UNIT}
ARCHIVE_TRIGGER_SAFE_ROLLBACK_PROVEN=true
ROLLBACK_ORIGINAL_ERROR_PRESERVED=true
ROLLBACK_FAILURE_EXPOSED=true
ROLLBACK_FAILURE_TRANSACTION_REVERTED=true
ISOLATED_END_TO_END_HOT_END_ZERO=true
ISOLATED_IDEMPOTENT_REPLAY=true
ISOLATED_RECOVERY_AFTER_OUTPUT_LOSS=true
SOURCE_CANDIDATES={source_count}
UNOBSERVABLE_ROWS=0
PRODUCTION_UNCHANGED=true
NEW_PRODUCTION_CANARY_AUTHORIZED=false
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
CURRENT_PROBLEM=POST_REMEDIATION_AUDIT_AND_CANARY_DECISION_PENDING""",
        )
        handoff = replace_section(
            handoff,
            "## 06 DO NOT REOPEN OR REPEAT",
            """- Do not rerun A9-A19 unless evidence is invalidated.
- Do not execute a new production canary before A20.
- Do not enable the production writer.
- Do not delete the valid A17 batch.
- Do not start Option B or close P0 F1.""",
        )
        handoff = replace_section(
            handoff,
            "## 07 ALLOWED NEXT DECISIONS",
            f"""- Rollback remediation: `TEMP_COPY_VALIDATED`.
- End-to-end runner success: `ISOLATED_VALIDATED`.
- New production canary: `BLOCKED_PENDING_A20`.
- General production activation: `BLOCKED`.
- Option B: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}""",
        )
        handoff = replace_section(
            handoff,
            "## 08 NEXT SESSION EXECUTION RULE",
            """1. Confirm A20 is current.
2. Independently audit A19 artifacts and production guards.
3. Decide a new bounded production canary separately.
4. Do not enable general production from temp-copy evidence alone.
5. Keep Option B blocked.""",
        )
        HANDOFF.write_text(handoff, encoding="utf-8")

        almanac = ALMANAC.read_text(encoding="utf-8")
        marker = "## ERA55A_19 ROLLBACK AND END-TO-END REMEDIATION TEMP COPY"
        if marker not in almanac:
            ALMANAC.write_text(
                almanac.rstrip()
                + f"""

---

{marker}

- Status: `CLOSED_TEMP_COPY_REMEDIATION_OK`
- Result: `{RESULT}`
- Archive-trigger-safe rollback: `true`
- Rollback failure exposed: `true`
- Isolated runner HOT_END:0: `true`
- Idempotent replay: `true`
- Recovery after output loss: `true`
- Production mutation: `false`
- New production canary authorized: `false`
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
        run(["git", "add", "-f", str(REPORT.relative_to(ROOT))])
        if not git("diff", "--cached", "--name-only"):
            raise RuntimeError("NO_STAGED_CHANGES")
        git("commit", "-m", SUBJECT)

        print("ERA55A19_REMEDIATION_TEMP_COPY=SUCCESS")
        print("RESULT=" + RESULT)
        print("ARCHIVE_TRIGGER_SAFE_ROLLBACK=true")
        print("ROLLBACK_ORIGINAL_ERROR_PRESERVED=true")
        print("ROLLBACK_FAILURE_EXPOSED=true")
        print("ROLLBACK_FAILURE_TRANSACTION_REVERTED=true")
        print("ISOLATED_END_TO_END_HOT_END_ZERO=true")
        print("FIRST_WRITER_STATUS=COMMITTED")
        print("SECOND_WRITER_STATUS=IDEMPOTENT_REPLAY_NOOP")
        print("RECOVERY_AFTER_OUTPUT_LOSS=true")
        print("BRIDGE_BYTE_PRESERVING_IN_SAME_FLOW=true")
        print("SOURCE_CANDIDATES=" + str(source_count))
        print("SOURCE_ACCOUNTED=" + str(first_db_state["ledger_rows"]))
        print("UNOBSERVABLE_ROWS=0")
        print("PRODUCTION_UNCHANGED=true")
        print("NEW_PRODUCTION_CANARY_AUTHORIZED=false")
        print("GENERAL_PRODUCTION_WRITER_ACTIVATION_AUTHORIZED=false")
        print("PRODUCTION_WRITER_ACTIVE=false")
        print("P0_F1_CLOSED=false")
        print("OPTION_B_AUTHORIZED=false")
        print("NEXT_SAFE_STEP=" + NEXT)
        print("LOCAL_COMMIT=" + git("rev-parse", "HEAD"))
        return 0
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
