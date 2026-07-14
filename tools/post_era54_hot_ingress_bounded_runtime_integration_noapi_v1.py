#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import ast
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path("/root/tokenoskobi_clean_v1")
SELF = Path(__file__).resolve()
WORK_UNIT = "POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_NOAPI"
DECISION = "OK_POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_NOAPI"

# Ensure core/ is importable from ROOT
_ROOT_STR = str(ROOT)
if _ROOT_STR not in sys.path:
    sys.path.insert(0, _ROOT_STR)

DB = ROOT / "data/tokenoskobi_clean_v1.sqlite"
ACTIVE_WRAPPER = ROOT / "tools/news_radar_refresh_runner_v1.py"
HBR_CLOSE = ROOT / "data/control/hbr_source_window_repair_or_close_decision_noapi_v1.json"
ERA54_CLOSE = ROOT / "data/control/era54f_final_closure_noapi_v1.json"

CONTROL_REL = "data/control/post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.json"
DOC_REL = "docs/canonical/POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_NOAPI_V1.md"
RUNTIME_STATE = ROOT / "runtime/state/news_hot_ingress_bounded_runtime_refresh_v1.json"
LOCK_PATH = Path("/run/tokenoskobi/news_hot_ingress_bounded_runtime_refresh_v1.lock")

MARKET_JSONL = ROOT / "runtime/state/news_market_indicator_events_v1.jsonl"
ADVERSARIAL_JSONL = ROOT / "runtime/state/news_adversarial_events_v1.jsonl"

SUMMARY = ROOT / "runtime/state/news_coverage_readmodel_consumer_summary_v1.json"
MARKET_LATEST = ROOT / "runtime/state/news_market_indicator_latest_v1.json"
ADVERSARIAL_LATEST = ROOT / "runtime/state/news_adversarial_latest_v1.json"
DISPLAY_JSON = ROOT / "runtime/state/news_coverage_panel_display_v1.json"
DISPLAY_HTML = ROOT / "runtime/state/news_coverage_panel_display_v1.html"
HOT_STATE = ROOT / "runtime/state/hot_intelligence_ingress_gateway_v1.json"
BRIDGE_STATE = ROOT / "runtime/state/news_active_panel_data_bridge_v1.json"
ACTIVE_DATA = ROOT / "active_panel_8096/current/data"

DYNAMIC_TRACKED_OUTPUTS = [
    "runtime/state/news_market_indicator_events_v1.jsonl",
    "runtime/state/news_adversarial_events_v1.jsonl",
    "runtime/state/news_coverage_readmodel_consumer_summary_v1.json",
    "runtime/state/news_market_indicator_latest_v1.json",
    "runtime/state/news_adversarial_latest_v1.json",
    "runtime/state/news_coverage_panel_display_v1.json",
    "runtime/state/news_coverage_panel_display_v1.html",
    "runtime/state/hot_intelligence_ingress_gateway_v1.json",
    "runtime/state/news_active_panel_data_bridge_v1.json",
    "active_panel_8096/current/data/news_coverage_readmodel_consumer_summary_v1.json",
    "active_panel_8096/current/data/news_market_indicator_latest_v1.json",
    "active_panel_8096/current/data/news_adversarial_latest_v1.json",
    "active_panel_8096/current/data/news_coverage_panel_display_v1.json",
    "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json",
    "active_panel_8096/current/data/news_runtime_stabilization_review_v1.json",
    "active_panel_8096/current/data/news_producer_health_watch_and_hot_gateway_review_v1.json",
    "active_panel_8096/current/data/news_active_panel_data_bridge_manifest_v1.json",
]

GITIGNORE_BLOCK = """# TOKENOSKOBI HOT INGRESS LIVE OUTPUTS BEGIN
active_panel_8096/current/data/news_coverage_readmodel_consumer_summary_v1.json
active_panel_8096/current/data/news_market_indicator_latest_v1.json
active_panel_8096/current/data/news_adversarial_latest_v1.json
active_panel_8096/current/data/news_coverage_panel_display_v1.json
active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json
active_panel_8096/current/data/news_runtime_stabilization_review_v1.json
active_panel_8096/current/data/news_producer_health_watch_and_hot_gateway_review_v1.json
active_panel_8096/current/data/news_active_panel_data_bridge_manifest_v1.json
# TOKENOSKOBI HOT INGRESS LIVE OUTPUTS END
"""

HELPER_STEPS = [
    ("consumer", ROOT / "tools/news_coverage_readmodel_consumer_v1.py", 30),
    ("display_adapter", ROOT / "tools/news_coverage_panel_display_adapter_v1.py", 30),
    ("hot_gateway", ROOT / "tools/hot_intelligence_ingress_gateway_v1.py", 30),
    ("active_panel_bridge", ROOT / "tools/news_active_panel_data_bridge_v1.py", 45),
]

TABLES = [
    "news_raw_feed_events",
    "news_token_match_events",
    "news_signal_events",
    "news_score_events_v1",
    "news_runtime_freshness_v1",
]

OLD_WRAPPER = """#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path('/root/tokenoskobi_clean_v1')
ORIGINAL = ROOT / 'tools' / 'news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py'
HELPER = ROOT / 'tools' / 'news_derived_layer_refresher_v1.py'
DB = ROOT / 'data' / 'tokenoskobi_clean_v1.sqlite'

def main():
    raw = subprocess.run([sys.executable, str(ORIGINAL)])
    if raw.returncode != 0:
        return raw.returncode
    derived = subprocess.run([sys.executable, str(HELPER), '--db-path', str(DB), '--write', '--stage', 'NEWS_SYSTEMD_TIMER_DERIVED_REFRESH'])
    return derived.returncode

if __name__ == '__main__':
    raise SystemExit(main())
"""

NEW_WRAPPER = """#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path('/root/tokenoskobi_clean_v1')
ORIGINAL = ROOT / 'tools' / 'news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py'
HELPER = ROOT / 'tools' / 'news_derived_layer_refresher_v1.py'
HOT = ROOT / 'tools' / 'post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.py'
DB = ROOT / 'data' / 'tokenoskobi_clean_v1.sqlite'

def run_hot():
    return subprocess.run(
        [sys.executable, str(HOT), '--runtime-refresh'],
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
    ).returncode

def main():
    if '--hot-only' in sys.argv[1:]:
        return run_hot()

    raw = subprocess.run([sys.executable, str(ORIGINAL)] + sys.argv[1:])
    if raw.returncode != 0:
        return raw.returncode

    derived = subprocess.run([
        sys.executable,
        str(HELPER),
        '--db-path',
        str(DB),
        '--write',
        '--stage',
        'NEWS_SYSTEMD_TIMER_DERIVED_REFRESH',
    ])
    if derived.returncode != 0:
        return derived.returncode

    return run_hot()

if __name__ == '__main__':
    raise SystemExit(main())
"""

NEW_WRAPPER = NEW_WRAPPER.replace(
    "import subprocess\nimport sys\n",
    "import os\nimport subprocess\nimport sys\n",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=str(path.parent))
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n")


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def db_snapshot() -> dict[str, Any]:
    connection = sqlite3.connect("file:" + str(DB) + "?mode=ro", uri=True, timeout=10)
    try:
        connection.execute("PRAGMA query_only=ON")
        existing = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        missing = [table for table in TABLES if table not in existing]
        counts = {
            table: int(connection.execute("SELECT COUNT(*) FROM " + q(table)).fetchone()[0])
            for table in TABLES
            if table in existing
        }
        return {
            "query_only": bool(connection.execute("PRAGMA query_only").fetchone()[0]),
            "total_changes": connection.total_changes,
            "integrity": str(connection.execute("PRAGMA integrity_check").fetchone()[0]),
            "missing_tables": missing,
            "counts": counts,
        }
    finally:
        connection.close()


def authority_false(value: Any) -> bool:
    return value is False


def validate_authority(authority: dict[str, Any], prefix: str, failures: list[str]) -> None:
    keys = [
        "db_write",
        "db_schema_change",
        "hunter_authorized",
        "trade_signal",
        "paper_signal",
        "live_trade",
        "execution_authority",
        "service_change",
        "timer_change",
        "network_call",
        "external_api_call",
    ]
    for key in keys:
        if key in authority and not authority_false(authority.get(key)):
            failures.append(f"{prefix}:{key}_not_false")


def acquire_lock() -> tuple[bool, str]:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if LOCK_PATH.exists():
        age = time.time() - LOCK_PATH.stat().st_mtime
        if age > 600:
            LOCK_PATH.unlink()
        else:
            return False, f"LOCK_BUSY_AGE_SECONDS={int(age)}"
    fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode("utf-8"))
    finally:
        os.close(fd)
    return True, "LOCK_ACQUIRED"


def release_lock() -> None:
    try:
        if LOCK_PATH.exists():
            LOCK_PATH.unlink()
    except Exception:
        pass


def run_step(name: str, path: Path, timeout: int) -> dict[str, Any]:
    started = utc_now()
    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    parsed_stdout: dict[str, Any] | None = None
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if lines:
        try:
            candidate = json.loads(lines[-1])
            if isinstance(candidate, dict):
                parsed_stdout = candidate
        except Exception:
            parsed_stdout = None
    return {
        "name": name,
        "path": str(path.relative_to(ROOT)),
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "rc": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "parsed_stdout": parsed_stdout,
    }


def runtime_refresh() -> int:
    try:
        from core.authority import check_operation  # noqa: PLC0415
        _auth = check_operation(
            "news_runner_pipeline", ROOT / "config/authority_state_v1.json"
        )
        if _auth.get("decision") != "ALLOW":
            print(
                "[AUTHORITY_DENIED] hot_ingress_runtime_refresh "
                + json.dumps(_auth, ensure_ascii=False, sort_keys=True),
                flush=True,
            )
            return _auth.get("exit_code", 1)
    except ImportError:
        print(
            "[AUTHORITY_WARN] core.authority not importable; proceeding without authority check",
            flush=True,
        )

    generated = utc_now()
    locked, lock_message = acquire_lock()
    if not locked:
        payload = {
            "stage": "NEWS_HOT_INGRESS_BOUNDED_RUNTIME_REFRESH_V1",
            "generated_at_utc": generated,
            "decision": "SKIP_HOT_REFRESH_LOCK_BUSY",
            "lock": lock_message,
            "authority": {
                "db_write": False,
                "network_call": False,
                "service_change": False,
                "timer_change": False,
                "trade_signal": False,
                "paper_signal": False,
                "live_trade": False,
                "execution_authority": False,
            },
            "failures": [],
            "warnings": [lock_message],
        }
        atomic_write_json(RUNTIME_STATE, payload)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0

    failures: list[str] = []
    warnings: list[str] = []
    steps: list[dict[str, Any]] = []
    before_lane_sha = {
        "market": sha256_file(MARKET_JSONL),
        "adversarial": sha256_file(ADVERSARIAL_JSONL),
    }

    try:
        for name, path, timeout in HELPER_STEPS:
            if not path.exists():
                failures.append("missing_helper:" + str(path.relative_to(ROOT)))
                break
            result = run_step(name, path, timeout)
            steps.append(result)
            if result["rc"] != 0:
                failures.append(f"step_failed:{name}:rc={result['rc']}")
                break

        after_lane_sha = {
            "market": sha256_file(MARKET_JSONL),
            "adversarial": sha256_file(ADVERSARIAL_JSONL),
        }
        if before_lane_sha != after_lane_sha:
            failures.append("coverage_jsonl_changed_by_hot_refresh")

        required_outputs = [
            SUMMARY,
            MARKET_LATEST,
            ADVERSARIAL_LATEST,
            DISPLAY_JSON,
            DISPLAY_HTML,
            HOT_STATE,
            BRIDGE_STATE,
        ]
        missing_outputs = [str(path.relative_to(ROOT)) for path in required_outputs if not path.exists()]
        if missing_outputs:
            failures.append("missing_outputs:" + ",".join(missing_outputs))

        summary: dict[str, Any] = {}
        display: dict[str, Any] = {}
        hot: dict[str, Any] = {}
        bridge: dict[str, Any] = {}
        if not failures:
            summary = load_json(SUMMARY)
            display = load_json(DISPLAY_JSON)
            hot = load_json(HOT_STATE)
            bridge = load_json(BRIDGE_STATE)

            for prefix, obj in [
                ("summary", summary),
                ("display", display),
                ("hot", hot),
                ("bridge", bridge),
            ]:
                authority = obj.get("authority")
                if isinstance(authority, dict):
                    validate_authority(authority, prefix, failures)

            if int(summary.get("parse_errors", -1)) != 0:
                failures.append("summary_parse_errors_nonzero")
            if int(summary.get("duplicate_event_uids", -1)) != 0:
                failures.append("summary_duplicate_event_uids_nonzero")
            if int(summary.get("unsafe_events", -1)) != 0:
                failures.append("summary_unsafe_events_nonzero")

            health = display.get("health") or {}
            if health.get("source_authority_ok") is not True:
                failures.append("display_source_authority_not_ok")
            for key in ["parse_errors", "duplicate_event_uids", "unsafe_events"]:
                if int(health.get(key, -1)) != 0:
                    failures.append("display_" + key + "_nonzero")

            queue = hot.get("hot_queue")
            queue_count = hot.get("hot_queue_count")
            if not isinstance(queue, list):
                failures.append("hot_queue_not_list")
                queue = []
            if not isinstance(queue_count, int):
                failures.append("hot_queue_count_not_int")
                queue_count = -1
            if queue_count != len(queue):
                failures.append("hot_queue_count_mismatch")
            if queue_count < 0 or queue_count > 50:
                failures.append("hot_queue_out_of_bound")
            for item in queue:
                if not isinstance(item, dict):
                    failures.append("hot_queue_item_not_object")
                    continue
                auth = item.get("authority")
                if isinstance(auth, dict):
                    validate_authority(auth, "hot_item", failures)
                if item.get("gateway_decision") != "REVIEW_ONLY":
                    failures.append("hot_item_gateway_decision_not_review_only")

            if bridge.get("decision") != "OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED":
                failures.append("panel_bridge_decision_not_ok")
            hash_match = bridge.get("hash_match")
            if not isinstance(hash_match, dict) or not hash_match or not all(value is True for value in hash_match.values()):
                failures.append("panel_bridge_hash_match_not_all_true")

        payload = {
            "stage": "NEWS_HOT_INGRESS_BOUNDED_RUNTIME_REFRESH_V1",
            "generated_at_utc": generated,
            "finished_at_utc": utc_now(),
            "decision": (
                "OK_NEWS_HOT_INGRESS_BOUNDED_RUNTIME_REFRESH_V1"
                if not failures
                else "FAIL_NEWS_HOT_INGRESS_BOUNDED_RUNTIME_REFRESH_V1"
            ),
            "lock": lock_message,
            "authority": {
                "db_write": False,
                "db_schema_change": False,
                "network_call": False,
                "external_api_call": False,
                "service_change": False,
                "timer_change": False,
                "panel_data_write": True,
                "hunter_authorized": False,
                "trade_signal": False,
                "paper_signal": False,
                "live_trade": False,
                "execution_authority": False,
            },
            "bounds": {
                "max_hot_queue": 50,
                "helper_count": len(HELPER_STEPS),
                "helper_timeouts_seconds": {
                    name: timeout for name, _, timeout in HELPER_STEPS
                },
            },
            "lane_sha_before": before_lane_sha,
            "lane_sha_after": after_lane_sha,
            "steps": steps,
            "summary": {
                "market_indicator_count": summary.get("market_indicator_count"),
                "adversarial_count": summary.get("adversarial_count"),
                "parse_errors": summary.get("parse_errors"),
                "duplicate_event_uids": summary.get("duplicate_event_uids"),
                "unsafe_events": summary.get("unsafe_events"),
                "hot_queue_count": hot.get("hot_queue_count"),
                "panel_bridge_decision": bridge.get("decision"),
            },
            "failures": failures,
            "warnings": warnings,
        }
        atomic_write_json(RUNTIME_STATE, payload)
        print(json.dumps({
            "decision": payload["decision"],
            "market_indicator_count": payload["summary"]["market_indicator_count"],
            "adversarial_count": payload["summary"]["adversarial_count"],
            "hot_queue_count": payload["summary"]["hot_queue_count"],
            "panel_bridge_decision": payload["summary"]["panel_bridge_decision"],
            "failures": failures,
            "output": str(RUNTIME_STATE),
        }, ensure_ascii=False, sort_keys=True))
        return 0 if not failures else 2
    finally:
        release_lock()


def service_snapshot() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for unit in [
        "tokenoskobi-news-radar-refresh.service",
        "tokenoskobi-news-radar-refresh.timer",
    ]:
        active = subprocess.run(
            ["systemctl", "is-active", unit],
            text=True,
            capture_output=True,
        )
        enabled = subprocess.run(
            ["systemctl", "is-enabled", unit],
            text=True,
            capture_output=True,
        )
        result[unit] = {
            "active": active.stdout.strip(),
            "active_rc": active.returncode,
            "enabled": enabled.stdout.strip(),
            "enabled_rc": enabled.returncode,
        }
    return result


def apply_runtime_output_index_hygiene() -> dict[str, Any]:
    gitignore = ROOT / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    begin = "# TOKENOSKOBI HOT INGRESS LIVE OUTPUTS BEGIN"
    end = "# TOKENOSKOBI HOT INGRESS LIVE OUTPUTS END"
    if begin in text and end in text:
        import re
        pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", re.S)
        text = pattern.sub(GITIGNORE_BLOCK, text, count=1)
    else:
        text = text.rstrip() + "\n\n" + GITIGNORE_BLOCK
    atomic_write_text(gitignore, text)

    tracked_before = set(
        line for line in git_output("ls-files", "--", *DYNAMIC_TRACKED_OUTPUTS).splitlines()
        if line.strip()
    )
    completed = subprocess.run(
        ["git", "rm", "--cached", "--ignore-unmatch", "--", *DYNAMIC_TRACKED_OUTPUTS],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("GIT_RM_CACHED_FAILED:" + completed.stderr.strip())

    missing_local = [
        relative
        for relative in DYNAMIC_TRACKED_OUTPUTS
        if not (ROOT / relative).exists()
    ]
    if missing_local:
        raise RuntimeError("DYNAMIC_OUTPUT_LOCAL_FILE_MISSING:" + ",".join(missing_local))

    tracked_after = set(
        line for line in git_output("ls-files", "--", *DYNAMIC_TRACKED_OUTPUTS).splitlines()
        if line.strip()
    )
    if tracked_after:
        raise RuntimeError("DYNAMIC_OUTPUT_STILL_TRACKED:" + ",".join(sorted(tracked_after)))

    return {
        "completed": True,
        "tracked_before": sorted(tracked_before),
        "tracked_after": sorted(tracked_after),
        "local_files_preserved": True,
        "gitignore_updated": True,
        "paths": DYNAMIC_TRACKED_OUTPUTS,
        "git_rm_stdout": completed.stdout.strip(),
    }


def replace_current_block(original: str, block: str) -> str:
    marker_sets = [
        (
            "<!-- HBR_SOURCE_WINDOW_CLOSE_CURRENT_START -->",
            "<!-- HBR_SOURCE_WINDOW_CLOSE_CURRENT_END -->",
        ),
        (
            "<!-- POST_ERA54_HOT_INGRESS_BOUND_CURRENT_START -->",
            "<!-- POST_ERA54_HOT_INGRESS_BOUND_CURRENT_END -->",
        ),
    ]
    import re
    replacement = block.rstrip() + "\n\n"
    for start, end in marker_sets:
        pattern = re.compile(re.escape(start) + r".*?" + re.escape(end) + r"\n*", re.S)
        if pattern.search(original):
            return pattern.sub(replacement, original, count=1)
    return replacement + original.lstrip("\ufeff")


def update_markdown(relative: str, block: str, append: str | None = None) -> None:
    path = ROOT / relative
    updated = replace_current_block(path.read_text(encoding="utf-8"), block)
    if append and append.strip() not in updated:
        updated = updated.rstrip() + "\n\n" + append.rstrip() + "\n"
    atomic_write_text(path, updated)


def apply_integration(expected_head: str) -> int:
    generated = utc_now()
    failures: list[str] = []
    warnings: list[str] = []

    current_head = git_output("rev-parse", "HEAD")
    branch = git_output("branch", "--show-current")
    if current_head != expected_head:
        raise RuntimeError(f"HEAD_MISMATCH:expected={expected_head}:actual={current_head}")
    if branch != "main":
        raise RuntimeError("BRANCH_NOT_MAIN:" + branch)

    hbr = load_json(HBR_CLOSE)
    era54 = load_json(ERA54_CLOSE)
    if hbr.get("decision") != "OK_HBR_SOURCE_WINDOW_CLOSE_DECISION_NOAPI":
        failures.append("hbr_close_not_ok")
    if hbr.get("next") != WORK_UNIT:
        failures.append("hbr_close_next_mismatch")
    if era54.get("decision") != "OK_ERA54_FINAL_CLOSED_VERIFIED_NOAPI":
        failures.append("era54_close_not_ok")

    if ACTIVE_WRAPPER.read_text(encoding="utf-8") != OLD_WRAPPER:
        failures.append("active_wrapper_baseline_mismatch")

    for _, helper, _ in HELPER_STEPS:
        if not helper.exists():
            failures.append("missing_helper:" + str(helper.relative_to(ROOT)))

    systemd = service_snapshot()
    service = systemd["tokenoskobi-news-radar-refresh.service"]
    if service["active"] not in {"inactive", "failed"}:
        failures.append("news_service_not_idle:" + str(service["active"]))

    db_before = db_snapshot()
    if db_before["integrity"] != "ok":
        failures.append("db_integrity_before_not_ok")
    if db_before["missing_tables"]:
        failures.append("db_missing_tables:" + ",".join(db_before["missing_tables"]))
    if db_before["query_only"] is not True or db_before["total_changes"] != 0:
        failures.append("db_readonly_before_invalid")

    lane_before = {
        "market": sha256_file(MARKET_JSONL),
        "adversarial": sha256_file(ADVERSARIAL_JSONL),
    }

    runtime_files = [
        MARKET_JSONL,
        ADVERSARIAL_JSONL,
        SUMMARY,
        MARKET_LATEST,
        ADVERSARIAL_LATEST,
        DISPLAY_JSON,
        DISPLAY_HTML,
        HOT_STATE,
        BRIDGE_STATE,
        RUNTIME_STATE,
    ]
    active_files = [
        ACTIVE_DATA / "news_coverage_readmodel_consumer_summary_v1.json",
        ACTIVE_DATA / "news_market_indicator_latest_v1.json",
        ACTIVE_DATA / "news_adversarial_latest_v1.json",
        ACTIVE_DATA / "news_coverage_panel_display_v1.json",
        ACTIVE_DATA / "hot_intelligence_ingress_gateway_v1.json",
        ACTIVE_DATA / "news_runtime_stabilization_review_v1.json",
        ACTIVE_DATA / "news_producer_health_watch_and_hot_gateway_review_v1.json",
        ACTIVE_DATA / "news_active_panel_data_bridge_manifest_v1.json",
    ]

    backup_dir = Path(tempfile.mkdtemp(prefix="post_era54_hot_integration_"))
    backup_map: dict[str, str | None] = {}
    for path in runtime_files + active_files:
        key = str(path)
        if path.exists():
            destination = backup_dir / hashlib.sha256(key.encode("utf-8")).hexdigest()
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            backup_map[key] = str(destination)
        else:
            backup_map[key] = None

    wrapper_patched = False
    try:
        if failures:
            raise RuntimeError("PREFLIGHT_FAILURE:" + "|".join(failures))

        direct = subprocess.run(
            [sys.executable, str(SELF), "--runtime-refresh"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=180,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        if direct.returncode != 0:
            failures.append("direct_hot_refresh_failed:" + direct.stderr.strip())
        direct_state = load_json(RUNTIME_STATE) if RUNTIME_STATE.exists() else {}
        if direct_state.get("decision") != "OK_NEWS_HOT_INGRESS_BOUNDED_RUNTIME_REFRESH_V1":
            failures.append("direct_hot_refresh_state_not_ok")

        if failures:
            raise RuntimeError("DIRECT_REFRESH_FAILURE:" + "|".join(failures))

        ast.parse(NEW_WRAPPER, filename=str(ACTIVE_WRAPPER))
        atomic_write_text(ACTIVE_WRAPPER, NEW_WRAPPER)
        wrapper_patched = True

        hot_only = subprocess.run(
            [sys.executable, str(ACTIVE_WRAPPER), "--hot-only"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=180,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        if hot_only.returncode != 0:
            failures.append("wrapper_hot_only_failed:" + hot_only.stderr.strip())
        hot_only_state = load_json(RUNTIME_STATE) if RUNTIME_STATE.exists() else {}
        if hot_only_state.get("decision") != "OK_NEWS_HOT_INGRESS_BOUNDED_RUNTIME_REFRESH_V1":
            failures.append("wrapper_hot_only_state_not_ok")

        db_after = db_snapshot()
        lane_after = {
            "market": sha256_file(MARKET_JSONL),
            "adversarial": sha256_file(ADVERSARIAL_JSONL),
        }

        if db_before != db_after:
            failures.append("db_changed_during_noapi_integration")
        if lane_before != lane_after:
            failures.append("coverage_jsonl_changed_during_noapi_integration")
        if ACTIVE_WRAPPER.read_text(encoding="utf-8") != NEW_WRAPPER:
            failures.append("active_wrapper_patch_not_exact")

        if failures:
            raise RuntimeError("INTEGRATION_VALIDATION_FAILURE:" + "|".join(failures))

        index_hygiene = apply_runtime_output_index_hygiene()

        runtime_state = load_json(RUNTIME_STATE)
        hot = load_json(HOT_STATE)
        bridge = load_json(BRIDGE_STATE)
        decision_id = (
            "POST_ERA54__HOT_INGRESS_BOUND_RUNTIME__"
            + current_head[:12]
            + "__"
            + generated
        )
        next_step = "POST_ERA54_HOT_INGRESS_BOUND_RUNTIME_FIRST_OBSERVATION_NOAPI"

        artifact = {
            "stage": WORK_UNIT,
            "generated_at_utc": generated,
            "decision": DECISION,
            "decision_id": decision_id,
            "previous_head_before_closure_commit": current_head,
            "authority": {
                "api_call": False,
                "network_call": False,
                "db_read": True,
                "db_write": False,
                "db_schema_change": False,
                "service_change": False,
                "timer_change": False,
                "panel_data_write": True,
                "panel_html_change": False,
                "hunter_authorized": False,
                "trade_signal": False,
                "paper_signal": False,
                "live_trade": False,
                "execution_authority": False,
                "new_era_opened": False,
                "runtime_output_index_hygiene": True,
            },
            "failures": [],
            "warnings": warnings,
            "next": next_step,
            "result": {
                "hbr_status": "CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT",
                "era54_status": "CLOSED_VERIFIED_NOAPI",
                "integration_status": "BOUND_HOT_ONLY_EXECUTION_VERIFIED",
                "active_wrapper": str(ACTIVE_WRAPPER.relative_to(ROOT)),
                "runtime_refresh_tool": str(SELF.relative_to(ROOT)),
                "runtime_chain": [
                    "news_coverage_readmodel_consumer_v1.py",
                    "news_coverage_panel_display_adapter_v1.py",
                    "hot_intelligence_ingress_gateway_v1.py",
                    "news_active_panel_data_bridge_v1.py",
                ],
                "runtime_order": "RAW_AND_DERIVED_SUCCESS_THEN_BOUNDED_HOT_REFRESH",
                "fail_policy": "HOT_REFRESH_NONZERO_PROPAGATES_TO_RUNNER",
                "hot_only_test": {
                    "rc": hot_only.returncode,
                    "stdout": hot_only.stdout.strip(),
                    "state_decision": hot_only_state.get("decision"),
                },
                "direct_test": {
                    "rc": direct.returncode,
                    "stdout": direct.stdout.strip(),
                    "state_decision": direct_state.get("decision"),
                },
                "db_before": db_before,
                "db_after": db_after,
                "db_delta": {
                    table: db_after["counts"][table] - db_before["counts"][table]
                    for table in TABLES
                },
                "coverage_jsonl_sha_before": lane_before,
                "coverage_jsonl_sha_after": lane_after,
                "market_indicator_count": runtime_state.get("summary", {}).get("market_indicator_count"),
                "adversarial_count": runtime_state.get("summary", {}).get("adversarial_count"),
                "hot_queue_count": hot.get("hot_queue_count"),
                "hot_queue_bound": 50,
                "panel_bridge_decision": bridge.get("decision"),
                "service_snapshot": systemd,
                "runtime_output_index_hygiene": index_hygiene,
                "service_file_changed": False,
                "timer_file_changed": False,
                "full_timer_cycle_observed_after_binding": False,
                "next_safe_step": next_step,
            },
        }
        atomic_write_json(ROOT / CONTROL_REL, artifact)

        runtime = load_json(ROOT / "PROJECT_RUNTIME.json")
        last_action = {
            "timestamp": generated,
            "task": WORK_UNIT,
            "result": DECISION,
            "artifact": CONTROL_REL,
        }
        active_work_unit = {
            "id": WORK_UNIT,
            "type": "POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION",
            "artifact": CONTROL_REL,
            "module": str(SELF.relative_to(ROOT)),
            "status": "CLOSED",
            "next_step": next_step,
        }
        next_safe_step = {"name": next_step, "status": "READY"}
        pointer = {
            "authority": "PROJECT_RUNTIME.json",
            "previous_head_before_closure_commit": current_head,
            "last_completed": WORK_UNIT,
            "decision": DECISION,
            "hbr_status": "CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT",
            "hot_ingress_integration_status": "BOUND_HOT_ONLY_EXECUTION_VERIFIED",
            "full_timer_cycle_observed_after_binding": False,
            "next_safe_step": next_step,
            "updated_at_utc": generated,
        }

        runtime.setdefault("current_state", {})
        runtime["current_state"].update({
            "mode": "POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_CLOSED",
            "runtime_status": "WORK_UNIT_CLOSED",
            "project_status": "ACTIVE",
            "updated_at": generated,
            "last_action": last_action,
            "active_work_unit": active_work_unit,
            "next_safe_step": next_safe_step,
            "current_problem": None,
        })
        runtime["current_work_unit"] = active_work_unit
        runtime["last_completed"] = WORK_UNIT
        runtime["mode"] = "POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_CLOSED"
        runtime["next_safe_step"] = next_safe_step
        runtime["current_problem"] = None
        runtime["updated_at_utc"] = generated
        runtime["canonical_runtime_pointer"] = pointer
        runtime["post_era54_hot_ingress_bounded_runtime_state"] = {
            "status": "BOUND_HOT_ONLY_EXECUTION_VERIFIED",
            "artifact": CONTROL_REL,
            "module": str(SELF.relative_to(ROOT)),
            "active_wrapper": str(ACTIVE_WRAPPER.relative_to(ROOT)),
            "runtime_chain": artifact["result"]["runtime_chain"],
            "hot_queue_count": artifact["result"]["hot_queue_count"],
            "hot_queue_bound": 50,
            "db_write": False,
            "service_change": False,
            "timer_change": False,
            "trade_authority": False,
            "full_timer_cycle_observed_after_binding": False,
            "next": next_step,
        }
        runtime["current_checkpoint"] = {
            "git_branch": "main",
            "previous_head_before_closure_commit": current_head,
            "head_semantics": "PREVIOUS_HEAD_BEFORE_ATOMIC_CLOSURE_COMMIT",
            "source": "local_git",
        }
        atomic_write_json(ROOT / "PROJECT_RUNTIME.json", runtime)

        boot = load_json(ROOT / "PROJECT_BOOT.json")
        boot["current_work_unit"] = active_work_unit
        boot["last_completed"] = WORK_UNIT
        boot["last_action"] = last_action
        boot["next_safe_step"] = next_safe_step
        boot["current_problem"] = None
        boot["canonical_runtime_pointer"] = pointer
        boot["current_checkpoint"] = runtime["current_checkpoint"]
        boot["new_chat_instruction"] = (
            "Read PROJECT_RUNTIME.json first. HBR is closed. "
            "Post-ERA54 hot ingress bounded runtime binding is closed and hot-only verified. "
            f"Proceed only to {next_step}. Do not run tk machine or change DB/schema/trade authority."
        )
        if isinstance(boot.get("new_window_startup_instruction"), dict):
            boot["new_window_startup_instruction"]["instruction"] = boot["new_chat_instruction"]
        boot.setdefault("project", {})
        boot["project"]["mode"] = "POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_CLOSED"
        boot["project"]["status"] = "ACTIVE"
        atomic_write_json(ROOT / "PROJECT_BOOT.json", boot)

        tk = load_json(ROOT / "data/control/latest_tk_machine_state.json")
        tk["collect_mode"] = "canonical_sync_snapshot_no_tk_machine"
        tk["created_at_utc"] = generated
        tk["generated_by"] = WORK_UNIT
        tk["tk_machine_executed"] = False
        tk["current_state"] = {
            "active_work_unit": active_work_unit,
            "next_safe_step": next_safe_step,
            "runtime_status": "WORK_UNIT_CLOSED",
            "updated_at": generated,
            "last_action": last_action,
            "authority": "PROJECT_RUNTIME.json",
        }
        tk["canonical_runtime_pointer"] = pointer
        tk["graphs_stale_non_authoritative"] = True
        atomic_write_json(ROOT / "data/control/latest_tk_machine_state.json", tk)

        roadmap = load_json(ROOT / "data/tokenoskobi_v1_v8_master_era_roadmap.json")
        roadmap["updated_at"] = generated
        roadmap["git_head"] = current_head
        roadmap["git_head_semantics"] = "PREVIOUS_HEAD_BEFORE_ATOMIC_CLOSURE_COMMIT"
        roadmap["work_unit"] = WORK_UNIT
        roadmap["current_state_authority"] = "PROJECT_RUNTIME.json"
        roadmap["runtime_alignment"] = pointer
        roadmap["hbr_chain"] = {
            "HBR_CURRENT_ATTEMPT": "CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT",
            "FUTURE_RETRY": "BACKLOG_ARCHIVE_CAPABLE_SOURCE_REQUIRED",
        }
        roadmap["post_era54_hot_ingress"] = {
            "status": "BOUND_HOT_ONLY_EXECUTION_VERIFIED",
            "active_wrapper": str(ACTIVE_WRAPPER.relative_to(ROOT)),
            "runtime_refresh_tool": str(SELF.relative_to(ROOT)),
            "hot_queue_bound": 50,
            "full_timer_cycle_observed_after_binding": False,
            "next_safe_step": next_step,
        }
        atomic_write_json(ROOT / "data/tokenoskobi_v1_v8_master_era_roadmap.json", roadmap)

        block = f"""<!-- POST_ERA54_HOT_INGRESS_BOUND_CURRENT_START -->
## CANONICAL CURRENT STATE — POST-ERA54 HOT INGRESS BOUND

STATE_SYNC_UTC={generated}
PREVIOUS_HEAD_BEFORE_CLOSURE_COMMIT={current_head}
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
LAST_COMPLETED={WORK_UNIT}
LAST_DECISION={DECISION}
CURRENT_ERA=ERA54
NEW_ERA_OPENED=false
HBR_STATUS=CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT
HOT_INGRESS_RUNTIME_BINDING=BOUND_HOT_ONLY_EXECUTION_VERIFIED
RUNTIME_ORDER=RAW_AND_DERIVED_SUCCESS_THEN_BOUNDED_HOT_REFRESH
HOT_QUEUE_COUNT={artifact['result']['hot_queue_count']}
HOT_QUEUE_BOUND=50
DB_WRITE=false
DB_DELTA=0
SERVICE_CHANGE=false
TIMER_CHANGE=false
TRADE_AUTHORITY=false
RUNTIME_OUTPUT_INDEX_HYGIENE=COMPLETED_LOCAL_FILES_PRESERVED
FULL_TIMER_CYCLE_OBSERVED_AFTER_BINDING=false
NEXT_SAFE_STEP={next_step}
<!-- POST_ERA54_HOT_INGRESS_BOUND_CURRENT_END -->"""

        update_markdown("03_ROADMAP.md", block)
        update_markdown(
            "04_ALMANAC.md",
            block,
            f"""## {WORK_UNIT} — {generated}

- Decision: `{DECISION}`
- HBR: `CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT`
- Runtime binding: `BOUND_HOT_ONLY_EXECUTION_VERIFIED`
- Runtime order: `raw/derived success → bounded hot refresh`
- Hot queue: `{artifact['result']['hot_queue_count']}/50`
- DB delta: `0`
- Service/timer change: `false`
- Trade authority: `false`
- Dynamic runtime outputs: `removed from Git index; local live files preserved and ignored`
- Full timer cycle after binding: `not yet observed`
- Next: `{next_step}`
- Previous HEAD: `{current_head}`""",
        )
        update_markdown("06_PROJECT_MASTER_STATE.md", block)
        update_markdown("07_PROJECT_HANDOFF.md", block)

        atomic_write_text(
            ROOT / "reports/LATEST_TK_AI_HANDOFF.md",
            f"""# LATEST TK AI HANDOFF

{block}

`PROJECT_RUNTIME.json` is current-state authority.

Proceed only to `{next_step}`.

The existing NEWS runner now calls the bounded hot chain only after raw and derived success. The binding was executed through `--hot-only`; production DB, service files, timer files and trade authority were not changed.
""",
        )

        atomic_write_text(
            ROOT / DOC_REL,
            f"""# POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_NOAPI_V1

- Decision: `{DECISION}`
- Generated: `{generated}`
- Previous HEAD: `{current_head}`
- HBR status: `CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT`
- ERA54 scaffold: `CLOSED_VERIFIED_NOAPI`
- Active wrapper: `tools/news_radar_refresh_runner_v1.py`
- Runtime refresh tool: `{SELF.relative_to(ROOT)}`
- Binding: `raw success → derived success → bounded hot refresh`
- Hot-only binding execution: `verified`
- Hot queue: `{artifact['result']['hot_queue_count']}/50`
- DB before/after: `equal`
- DB write by this operation: `false`
- Coverage JSONL before/after SHA: `equal`
- Service file change: `false`
- Timer file change: `false`
- Trade authority: `false`
- Dynamic runtime outputs: `removed from Git index; local live files preserved and ignored`
- Full timer cycle after binding: `not yet observed`
- Next: `{next_step}`

## Runtime chain

1. `news_coverage_readmodel_consumer_v1.py`
2. `news_coverage_panel_display_adapter_v1.py`
3. `hot_intelligence_ingress_gateway_v1.py`
4. `news_active_panel_data_bridge_v1.py`

The runtime refresh is lock-protected, helper-timeout-bounded, hot-queue-bounded to 50, fail-closed, and does not mutate the production database.
""",
        )

        print(json.dumps({
            "decision": DECISION,
            "decision_id": decision_id,
            "integration_status": "BOUND_HOT_ONLY_EXECUTION_VERIFIED",
            "market_indicator_count": artifact["result"]["market_indicator_count"],
            "adversarial_count": artifact["result"]["adversarial_count"],
            "hot_queue_count": artifact["result"]["hot_queue_count"],
            "db_delta": artifact["result"]["db_delta"],
            "next_safe_step": next_step,
        }, ensure_ascii=False, indent=2))
        return 0

    except Exception:
        if wrapper_patched:
            atomic_write_text(ACTIVE_WRAPPER, OLD_WRAPPER)
        for key, backup in backup_map.items():
            path = Path(key)
            if backup is None:
                if path.exists():
                    if path.is_file():
                        path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(Path(backup), path)
        raise
    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-refresh", action="store_true")
    parser.add_argument("--apply-integration", action="store_true")
    args = parser.parse_args()

    if args.runtime_refresh:
        return runtime_refresh()
    if args.apply_integration:
        expected = os.environ.get("POST_ERA54_EXPECTED_HEAD", "").strip()
        if not expected:
            raise RuntimeError("POST_ERA54_EXPECTED_HEAD_REQUIRED")
        return apply_integration(expected)

    parser.error("choose --runtime-refresh or --apply-integration")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
