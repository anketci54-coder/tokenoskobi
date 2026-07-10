#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
WORK_UNIT = "ERA55A_1_READONLY_INSPECTION"
ERA_ID = "ERA55"
ERA_TITLE = "Runtime Optimization"
OPEN_ARTIFACT_REL = "data/control/era55_runtime_optimization_init_v1.json"
REPORT_REL = "reports/LATEST_ERA55A1_READONLY_INSPECTION.md"
NEXT_SAFE_STEP = "ERA55A_2_GRANULAR_INSTRUMENTATION_AND_BASELINE_MEASUREMENT_PLAN"
SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"
DB_REL = "data/tokenoskobi_clean_v1.sqlite"
QUEUE_REL = "tools/hot_intelligence_ingress_gateway_v1.py"
RUNNER_REL = "tools/news_radar_refresh_runner_v1.py"
HOT_RUNTIME_REL = "tools/post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.py"

CANONICAL_FILES = [
    "PROJECT_RUNTIME.json",
    "PROJECT_HISTORY.json",
    "data/tokenoskobi_v1_v8_master_era_roadmap.json",
    "03_ROADMAP.md",
    "04_ALMANAC.md",
    "06_PROJECT_MASTER_STATE.md",
    "07_PROJECT_HANDOFF.md",
]

GENERATED_FILES = [OPEN_ARTIFACT_REL, REPORT_REL]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(cmd: list[str], *, timeout: int = 30, check: bool = False) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        result = {
            "cmd": cmd,
            "rc": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
        if check and completed.returncode != 0:
            raise RuntimeError(json.dumps(result, ensure_ascii=False))
        return result
    except subprocess.TimeoutExpired as exc:
        result = {
            "cmd": cmd,
            "rc": 124,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            "timeout_seconds": timeout,
        }
        if check:
            raise RuntimeError(json.dumps(result, ensure_ascii=False))
        return result


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n")


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str, check: bool = True) -> str:
    result = run(["git", *args], timeout=90, check=check)
    return str(result.get("stdout") or "")


def ensure_preconditions() -> str:
    if ROOT.resolve() != Path.cwd().resolve():
        os.chdir(ROOT)
    branch = git("branch", "--show-current")
    if branch != "main":
        raise RuntimeError(f"BLOCKED=BRANCH_NOT_MAIN:{branch}")
    status = git("status", "--porcelain")
    if status:
        raise RuntimeError("BLOCKED=WORKTREE_NOT_CLEAN\n" + status)
    git("fetch", "origin", "main")
    local_head = git("rev-parse", "HEAD")
    remote_head = git("rev-parse", "origin/main")
    if local_head != remote_head:
        raise RuntimeError(f"BLOCKED=LOCAL_REMOTE_NOT_SYNCED:LOCAL={local_head}:REMOTE={remote_head}")
    runtime = load_json(ROOT / "PROJECT_RUNTIME.json")
    next_step = runtime.get("next_safe_step") or {}
    if next_step.get("id") != "ERA55_SELECTION_GATE":
        raise RuntimeError(f"BLOCKED=UNEXPECTED_NEXT_SAFE_STEP:{next_step.get('id')}")
    if next_step.get("new_era_opened") is not False:
        raise RuntimeError("BLOCKED=ERA55_ALREADY_MARKED_OPEN")
    return local_head


def parse_systemctl_show(unit: str, properties: list[str]) -> dict[str, Any]:
    result = run(["systemctl", "show", unit, "--no-pager", "--property=" + ",".join(properties)], timeout=20)
    values: dict[str, str] = {}
    if result["rc"] == 0:
        for line in str(result["stdout"]).splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value
    return {"unit": unit, "values": values, "command": result}


def int_or_none(value: Any) -> int | None:
    try:
        return int(str(value))
    except Exception:
        return None


def systemd_inspection() -> dict[str, Any]:
    service_props = [
        "LoadState",
        "ActiveState",
        "SubState",
        "UnitFileState",
        "FragmentPath",
        "Type",
        "ExecStart",
        "ExecMainStartTimestamp",
        "ExecMainExitTimestamp",
        "ExecMainStartTimestampMonotonic",
        "ExecMainExitTimestampMonotonic",
        "ExecMainStatus",
        "Result",
        "TimeoutStartUSec",
        "TimeoutStopUSec",
        "RuntimeMaxUSec",
        "Restart",
        "RestartUSec",
        "KillMode",
        "MainPID",
        "NRestarts",
    ]
    timer_props = [
        "LoadState",
        "ActiveState",
        "SubState",
        "UnitFileState",
        "FragmentPath",
        "Unit",
        "OnBootUSec",
        "OnUnitActiveUSec",
        "OnActiveUSec",
        "AccuracyUSec",
        "RandomizedDelayUSec",
        "Persistent",
        "LastTriggerUSec",
        "NextElapseUSecRealtime",
        "Result",
    ]
    service = parse_systemctl_show(SERVICE, service_props)
    timer = parse_systemctl_show(TIMER, timer_props)
    service_cat = run(["systemctl", "cat", SERVICE, "--no-pager"], timeout=20)
    timer_cat = run(["systemctl", "cat", TIMER, "--no-pager"], timeout=20)
    list_timers = run(["systemctl", "list-timers", "--all", TIMER, "--no-pager"], timeout=20)
    journal = run(["journalctl", "-u", SERVICE, "--since", "24 hours ago", "--no-pager", "-n", "300", "-o", "short-iso"], timeout=30)

    service_values = service["values"]
    start_us = int_or_none(service_values.get("ExecMainStartTimestampMonotonic"))
    exit_us = int_or_none(service_values.get("ExecMainExitTimestampMonotonic"))
    last_duration_ms = None
    if start_us is not None and exit_us is not None and exit_us >= start_us:
        last_duration_ms = round((exit_us - start_us) / 1000, 3)

    timer_values = timer["values"]
    cadence_us = int_or_none(timer_values.get("OnUnitActiveUSec"))
    safety_margin_ms = None
    if cadence_us is not None and last_duration_ms is not None:
        safety_margin_ms = round((cadence_us / 1000) - last_duration_ms, 3)

    return {
        "service": service,
        "timer": timer,
        "service_unit_text": service_cat,
        "timer_unit_text": timer_cat,
        "list_timers": list_timers,
        "journal_last_24h": journal,
        "derived": {
            "last_execution_duration_ms": last_duration_ms,
            "timer_cadence_usec": cadence_us,
            "timer_safety_margin_ms": safety_margin_ms,
            "duration_baseline_complete": last_duration_ms is not None,
            "overlap_risk_status": (
                "MEASURED_MARGIN_AVAILABLE"
                if safety_margin_ms is not None
                else "NEEDS_GRANULAR_DURATION_BASELINE"
            ),
        },
    }


def sqlite_inspection() -> dict[str, Any]:
    db = ROOT / DB_REL
    if not db.is_file():
        return {"db_path": str(db), "exists": False, "error": "DB_NOT_FOUND"}

    uri = f"file:{db}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=20)
    try:
        connection.execute("PRAGMA query_only=ON")
        pragma_names = [
            "journal_mode",
            "synchronous",
            "locking_mode",
            "foreign_keys",
            "busy_timeout",
            "cache_size",
            "temp_store",
            "mmap_size",
            "page_size",
            "page_count",
            "freelist_count",
            "query_only",
        ]
        pragmas: dict[str, Any] = {}
        for name in pragma_names:
            try:
                row = connection.execute(f"PRAGMA {name}").fetchone()
                pragmas[name] = row[0] if row else None
            except Exception as exc:
                pragmas[name] = {"error": str(exc)}

        integrity_row = connection.execute("PRAGMA integrity_check").fetchone()
        quick_row = connection.execute("PRAGMA quick_check").fetchone()
        tables = [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        target_tables = [
            "news_raw_feed_events",
            "news_token_match_events",
            "news_signal_events",
            "news_score_events_v1",
            "news_runtime_freshness_v1",
        ]
        counts: dict[str, int] = {}
        timestamp_max: dict[str, dict[str, Any]] = {}
        for table in target_tables:
            if table not in tables:
                continue
            quoted = '"' + table.replace('"', '""') + '"'
            counts[table] = int(connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0])
            columns = [str(row[1]) for row in connection.execute(f"PRAGMA table_info({quoted})").fetchall()]
            candidates = [
                name
                for name in (
                    "updated_at_utc",
                    "created_at_utc",
                    "published_at_utc",
                    "timestamp_utc",
                    "ts_utc",
                    "observed_at_utc",
                )
                if name in columns
            ]
            if candidates:
                column = candidates[0]
                qcol = '"' + column.replace('"', '""') + '"'
                value = connection.execute(f"SELECT MAX({qcol}) FROM {quoted}").fetchone()[0]
                timestamp_max[table] = {"column": column, "max": value}

        return {
            "db_path": str(db),
            "exists": True,
            "size_bytes": db.stat().st_size,
            "mtime_utc": datetime.fromtimestamp(db.stat().st_mtime, timezone.utc).isoformat(),
            "readonly_uri": uri,
            "query_only": True,
            "total_changes": connection.total_changes,
            "pragmas": pragmas,
            "integrity_check": integrity_row[0] if integrity_row else None,
            "quick_check": quick_row[0] if quick_row else None,
            "table_counts": counts,
            "table_max_timestamps": timestamp_max,
        }
    finally:
        connection.close()


def analyze_python(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "exists": False}
    text = path.read_text(encoding="utf-8", errors="replace")
    result: dict[str, Any] = {
        "path": str(path.relative_to(ROOT)),
        "exists": True,
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "syntax_ok": False,
        "subprocess_calls": [],
        "timeout_literals": [],
    }
    try:
        tree = ast.parse(text)
        result["syntax_ok"] = True
    except SyntaxError as exc:
        result["syntax_error"] = str(exc)
        return result

    subprocess_calls: list[str] = []
    timeout_literals: list[Any] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            try:
                name = ast.unparse(node.func)
            except Exception:
                name = ""
            if "subprocess" in name:
                try:
                    subprocess_calls.append(ast.unparse(node)[:1000])
                except Exception:
                    pass
            for keyword in node.keywords:
                if keyword.arg == "timeout":
                    try:
                        timeout_literals.append(ast.literal_eval(keyword.value))
                    except Exception:
                        try:
                            timeout_literals.append(ast.unparse(keyword.value))
                        except Exception:
                            timeout_literals.append("UNKNOWN")
    result["subprocess_calls"] = subprocess_calls
    result["timeout_literals"] = timeout_literals
    return result


def queue_policy_inspection() -> dict[str, Any]:
    path = ROOT / QUEUE_REL
    base = analyze_python(path)
    if not base.get("exists") or not base.get("syntax_ok"):
        return base

    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)
    slice_limits: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            upper = node.slice.upper
            if isinstance(upper, ast.Constant) and isinstance(upper.value, int):
                slice_limits.append(upper.value)

    priority_sort = "-int(x.get(\"priority_score\") or 0)" in text or "-int(x.get('priority_score') or 0)" in text
    uid_tiebreak = "hot_uid" in text and "sorted(" in text
    drop_ledger_terms = any(term in text.lower() for term in ["drop_ledger", "dropped_count", "evicted", "overflow_count"])
    top_n_50 = 50 in slice_limits and "deduped[:50]" in text.replace(" ", "")

    base.update(
        {
            "slice_limits": slice_limits,
            "queue_capacity_detected": 50 if top_n_50 else (max(slice_limits) if slice_limits else None),
            "selection_policy": (
                "PRIORITY_DESC_THEN_HOT_UID_TOP_50"
                if top_n_50 and priority_sort and uid_tiebreak
                else "UNRESOLVED_FROM_STATIC_ANALYSIS"
            ),
            "dedupe_detected": "seen = set()" in text and "deduped.append" in text,
            "drop_ledger_detected": drop_ledger_terms,
            "silent_truncation_risk": bool(top_n_50 and not drop_ledger_terms),
            "silent_drop_compliance": "FAIL_P0" if top_n_50 and not drop_ledger_terms else "NOT_PROVEN_FAIL",
            "policy_evidence": [
                "items sorted by priority_score descending",
                "hot_uid used as deterministic tie-break",
                "deduplicated list sliced to first 50",
                "no explicit overflow/drop ledger found",
            ] if top_n_50 else [],
        }
    )
    return base


def filesystem_visibility() -> dict[str, Any]:
    paths = [
        DB_REL,
        "runtime/state/news_coverage_panel_display_v1.json",
        "runtime/state/hot_intelligence_ingress_gateway_v1.json",
        "runtime/state/news_active_panel_data_bridge_v1.json",
        "active_panel_8096/current/data/news_coverage_panel_display_v1.json",
        "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json",
    ]
    values: dict[str, Any] = {}
    for rel in paths:
        path = ROOT / rel
        if path.is_file():
            stat = path.stat()
            values[rel] = {
                "exists": True,
                "size_bytes": stat.st_size,
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "sha256": sha256_file(path),
            }
        else:
            values[rel] = {"exists": False}
    return values


def derive_risks(inspection: dict[str, Any]) -> list[dict[str, str]]:
    risks: list[dict[str, str]] = []
    queue = inspection.get("queue_policy", {})
    if queue.get("silent_truncation_risk"):
        risks.append(
            {
                "priority": "P0",
                "code": "QUEUE_OVERFLOW_SILENT_TRUNCATION_RISK",
                "finding": "Queue keeps deterministic top 50 but no overflow/drop ledger was found.",
                "required_action": "Define overflow policy and record every dropped or displaced event before optimization.",
            }
        )
    systemd = inspection.get("systemd", {}).get("derived", {})
    if not systemd.get("duration_baseline_complete"):
        risks.append(
            {
                "priority": "P0",
                "code": "RUNNER_TIMER_MARGIN_UNMEASURED",
                "finding": "Reliable runner duration versus timer cadence margin is not yet measured.",
                "required_action": "Add granular read-only timestamps before burst or watchdog changes.",
            }
        )
    sqlite_data = inspection.get("sqlite", {})
    if sqlite_data.get("integrity_check") not in ("ok", None):
        risks.append(
            {
                "priority": "P0",
                "code": "SQLITE_INTEGRITY_NOT_OK",
                "finding": f"SQLite integrity_check={sqlite_data.get('integrity_check')}",
                "required_action": "Stop optimization and investigate database integrity.",
            }
        )
    journal_mode = str((sqlite_data.get("pragmas") or {}).get("journal_mode") or "").lower()
    if journal_mode and journal_mode != "wal":
        risks.append(
            {
                "priority": "P1",
                "code": "SQLITE_JOURNAL_MODE_NOT_WAL",
                "finding": f"Current journal_mode={journal_mode}.",
                "required_action": "Do not change mode yet; test durability and lock behavior on a temp copy first.",
            }
        )
    risks.append(
        {
            "priority": "P1",
            "code": "PANEL_PROPAGATION_LATENCY_NOT_YET_INSTRUMENTED",
            "finding": "Filesystem timestamps provide visibility but not end-to-end propagation latency.",
            "required_action": "ERA55A_2 must add granular read-only stage timestamps.",
        }
    )
    return risks


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(rf"({re.escape(heading)}\n)(.*?)(?=\n---\n|\Z)", re.S)
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"SECTION_NOT_FOUND:{heading}")
    return text[: match.start()] + heading + "\n\n" + body.rstrip() + "\n" + text[match.end() :]


def update_roadmap_md() -> None:
    path = ROOT / "03_ROADMAP.md"
    text = path.read_text(encoding="utf-8")
    old = """Current major-line selection gate:\n\n- `ERA55_SELECTION_GATE`\n- Parent line: `ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME`\n- Candidate major line: `ERA55_RUNTIME_OPTIMIZATION`\n- Candidate status: `PLANNED_CANDIDATE_NOT_OPENED`\n- Human authorization required: `true`\n- New ERA opened: `false`"""
    new = """Current major line:\n\n- `ERA55_RUNTIME_OPTIMIZATION`\n- Parent line: `ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME`\n- Status: `OPEN`\n- Human authorization recorded: `true`\n- Active baseline stage: `ERA55A`\n- Last completed substep: `ERA55A_1_READONLY_INSPECTION`\n- Next safe step: `ERA55A_2_GRANULAR_INSTRUMENTATION_AND_BASELINE_MEASUREMENT_PLAN`\n- Gemini Red Team review required before optimization apply: `true`"""
    if old not in text:
        raise RuntimeError("ROADMAP_GATE_BLOCK_NOT_FOUND")
    atomic_write_text(path, text.replace(old, new, 1))


def update_roadmap_json(opened_at: str, artifact: dict[str, Any]) -> None:
    path = ROOT / "data/tokenoskobi_v1_v8_master_era_roadmap.json"
    data = load_json(path)
    found = False
    for version in data.get("versions", []):
        if version.get("id") != "V3":
            continue
        for child in version.get("children", []):
            if child.get("id") == "ERA55":
                child.update(
                    {
                        "status": "OPEN",
                        "selection_required": False,
                        "authorization_recorded": True,
                        "human_authorization_required": True,
                        "provisional_only": False,
                        "new_era_opened": True,
                        "opened_at_utc": opened_at,
                        "active_stage": "ERA55A_BASELINE_MEASUREMENT",
                        "last_completed_substep": WORK_UNIT,
                        "next_safe_step": NEXT_SAFE_STEP,
                        "opening_artifact": OPEN_ARTIFACT_REL,
                        "gemini_red_team_required": True,
                    }
                )
                found = True
        gate = version.get("current_selection_gate")
        if isinstance(gate, dict) and gate.get("id") == "ERA55_SELECTION_GATE":
            gate.update(
                {
                    "status": "CONSUMED",
                    "selected_decision": "OPEN_ERA55_RUNTIME_OPTIMIZATION",
                    "candidate_status": "OPEN",
                    "human_authorization_recorded": True,
                    "new_era_opened": True,
                    "consumed_at_utc": opened_at,
                }
            )
    if not found:
        raise RuntimeError("ERA55_NOT_FOUND_IN_ROADMAP_JSON")
    data["updated_at"] = opened_at
    data["git_head"] = "DYNAMIC_USE_GIT_REV_PARSE_HEAD"
    data["work_unit"] = WORK_UNIT
    atomic_write_json(path, data)


def update_runtime(opened_at: str, artifact: dict[str, Any], risks: list[dict[str, str]]) -> None:
    path = ROOT / "PROJECT_RUNTIME.json"
    data = load_json(path)
    data["current_era"] = ERA_ID
    data["mode"] = "ERA55_RUNTIME_OPTIMIZATION_A1_READONLY_INSPECTION_CLOSED"
    data["project_status"] = "ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE"
    data["status"] = "WORK_UNIT_CLOSED"
    data["last_completed"] = WORK_UNIT
    data["last_action"] = {
        "timestamp": opened_at,
        "task": WORK_UNIT,
        "result": artifact["result"],
        "artifact": OPEN_ARTIFACT_REL,
    }
    data["recent_event"] = dict(data["last_action"])
    work_unit = {
        "id": WORK_UNIT,
        "type": "ERA55_BASELINE_READONLY_INSPECTION",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "artifact": OPEN_ARTIFACT_REL,
        "report": REPORT_REL,
        "status": "CLOSED",
        "mutation_scope": "CANONICAL_STATE_AND_REPORT_ONLY",
        "runtime_db_service_timer_panel_mutation": False,
        "next_step": NEXT_SAFE_STEP,
    }
    next_step = {
        "id": NEXT_SAFE_STEP,
        "type": "ERA55_BASELINE_INSTRUMENTATION_PLAN",
        "parent": "ERA55_RUNTIME_OPTIMIZATION",
        "serves": "V3_RUNTIME_INTELLIGENCE_OS",
        "purpose": "Define granular read-only timing instrumentation and cold/hot normal-load baseline commands before burst testing or optimization apply.",
        "human_authorization_required": True,
        "gemini_red_team_review_after_baseline_report": True,
        "runtime_mutation_authorized": False,
        "status": "READY_FOR_PLAN",
    }
    data["current_work_unit"] = work_unit
    data["next_safe_step"] = next_step
    state = data.setdefault("current_state", {})
    state.update(
        {
            "mode": data["mode"],
            "runtime_status": "WORK_UNIT_CLOSED",
            "project_status": "ACTIVE",
            "updated_at": opened_at,
            "last_action": dict(data["last_action"]),
            "active_work_unit": dict(work_unit),
            "next_safe_step": dict(next_step),
            "current_problem": None,
        }
    )
    data["era55_status"] = {
        "era": ERA_ID,
        "title": ERA_TITLE,
        "status": "OPEN",
        "opened_at_utc": opened_at,
        "authorization": "USER_APPROVED_OPEN_ERA55_RUNTIME_OPTIMIZATION",
        "parent": "ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME",
        "serves": "V3_RUNTIME_INTELLIGENCE_OS",
        "active_stage": "ERA55A_BASELINE_MEASUREMENT",
        "last_completed_substep": WORK_UNIT,
        "next_safe_step": NEXT_SAFE_STEP,
        "opening_artifact": OPEN_ARTIFACT_REL,
        "report": REPORT_REL,
        "gemini_red_team_required": True,
        "optimization_apply_authorized": False,
        "burst_load_authorized": False,
        "runtime_db_service_timer_panel_mutation": False,
    }
    data["open_risks"] = [f"{item['priority']}:{item['code']}:{item['finding']}" for item in risks] + ["Risk is minimized, never zero."]
    data["source"] = "era55_open_and_a1_readonly_inspection_v1"
    data["updated_at"] = opened_at
    data["updated_at_utc"] = opened_at
    atomic_write_json(path, data)


def update_master_state(artifact: dict[str, Any], risks: list[dict[str, str]]) -> None:
    path = ROOT / "06_PROJECT_MASTER_STATE.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "PROJECT_STATUS=ACTIVE_NEWS_OPERATIONAL_BASELINE_CLOSED_SELECTION_GATE_READY",
        "PROJECT_STATUS=ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE",
        1,
    )
    section_02 = """```text
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_BASELINE_MEASUREMENT
LAST_COMPLETED_SUBSTEP=ERA55A_1_READONLY_INSPECTION
HUMAN_AUTHORIZATION_RECORDED=true
GEMINI_RED_TEAM_REQUIRED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
```

ERA55 is open only for measured runtime optimization. No optimization apply, watchdog, index, WAL, cache, queue-policy or incremental-write change is authorized yet."""
    section_03 = f"""```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={artifact['result']}
LAST_ARTIFACT={OPEN_ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
SYSTEM_INSPECTION=READ_ONLY
RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
```

ERA55A_1 recorded the natural system configuration and static queue policy without changing the live runtime."""
    risks_body = "\n".join(f"- `{r['priority']} {r['code']}` — {r['finding']}" for r in risks)
    section_09 = risks_body + "\n- Runtime risk is minimized, never zero.\n- Git HEAD remains dynamic and is not embedded self-referentially."
    section_10 = f"""```text
NEXT_SAFE_STEP={NEXT_SAFE_STEP}
```

The next step defines granular read-only timestamps and cold/hot normal-load baseline commands. Burst testing and optimization apply remain unauthorized."""
    text = replace_section(text, "## 02 CURRENT MAJOR-LINE POSITION", section_02)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", section_03)
    text = replace_section(text, "## 09 OPEN RISKS AND DECISIONS", section_09)
    text = replace_section(text, "## 10 NEXT SAFE STEP", section_10)
    atomic_write_text(path, text)


def update_handoff(artifact: dict[str, Any], risks: list[dict[str, str]]) -> None:
    path = ROOT / "07_PROJECT_HANDOFF.md"
    text = path.read_text(encoding="utf-8")
    checkpoint = """PROJECT_STATUS=ACTIVE_ERA55_RUNTIME_OPTIMIZATION_BASELINE
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
LAST_CLOSED_MAJOR_LINE=ERA54_HOT_INTELLIGENCE_INGRESS_BOUNDED_RUNTIME
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=OPEN
CURRENT_STAGE=ERA55A_BASELINE_MEASUREMENT
LAST_COMPLETED_SUBSTEP=ERA55A_1_READONLY_INSPECTION
GEMINI_RED_TEAM_REQUIRED=true
OPTIMIZATION_APPLY_AUTHORIZED=false
BURST_LOAD_AUTHORIZED=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD

ERA55 was opened by explicit user authorization. ERA55A_1 is closed as read-only inspection; no live runtime mutation was applied."""
    last_work = f"""LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={artifact['result']}
LAST_ARTIFACT={OPEN_ARTIFACT_REL}
LAST_REPORT={REPORT_REL}
WORK_UNIT_STATUS=CLOSED
SYSTEM_INSPECTION=READ_ONLY
RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false
CURRENT_PROBLEM=null

The next action is granular read-only instrumentation planning, not optimization apply."""
    do_not = """- Do not reopen ERA54.
- Do not rebuild NEWS from zero.
- Do not apply watchdog, index, WAL, cache, queue-policy or incremental-write changes before baseline evidence.
- Do not run production BURST_LOAD before temp-copy test authorization.
- Do not accept silent event loss.
- Do not recreate removed historical current-state blocks.
- Do not copy current state into Manifesto, Roadmap, Almanac, Atlas or Index.
- Do not create a new canonical file when an owner file already exists.
- Do not open micro ERA records for plan, test, audit, review or seal.
- Do not run `tk machine` unless explicitly requested.
- Do not close ERA55 before Gemini Red Team findings are resolved."""
    decisions = f"""Current authorized direction:

- `ERA55_RUNTIME_OPTIMIZATION` is open.
- `ERA55A_1_READONLY_INSPECTION` is complete.
- Optimization apply is not authorized.
- Burst load is not authorized.

NEXT_SAFE_STEP={NEXT_SAFE_STEP}"""
    execution = f"""1. Read `PROJECT_RUNTIME.json`.
2. Confirm `ERA55_STATUS=OPEN` and `{NEXT_SAFE_STEP}` remains the next safe step.
3. Read Git HEAD dynamically and verify local/remote synchronization.
4. Review `{OPEN_ARTIFACT_REL}` and `{REPORT_REL}`.
5. Define granular read-only stage timestamps.
6. Collect normal cold-start and hot-state baselines.
7. Submit the completed baseline report to Gemini Red Team.
8. Use a temp DB copy for burst, saturation, lock and recovery tests.
9. Do not apply optimization until evidence and Red Team review support it."""
    text = replace_section(text, "## 02 CURRENT CONTINUATION CHECKPOINT", checkpoint)
    text = replace_section(text, "## 03 LAST VERIFIED WORK", last_work)
    text = replace_section(text, "## 06 DO NOT REOPEN OR REPEAT", do_not)
    text = replace_section(text, "## 07 ALLOWED NEXT DECISIONS", decisions)
    text = replace_section(text, "## 08 NEXT SESSION EXECUTION RULE", execution)
    atomic_write_text(path, text)


def append_history(opened_at: str, artifact: dict[str, Any], risks: list[dict[str, str]], head_before: str) -> None:
    path = ROOT / "PROJECT_HISTORY.json"
    data = load_json(path)
    events = data.get("events")
    if not isinstance(events, list):
        raise RuntimeError("PROJECT_HISTORY_EVENTS_INVALID")
    event_id = "ERA55_RUNTIME_OPTIMIZATION_OPEN_AND_A1_READONLY_INSPECTION_V1"
    if not any(isinstance(item, dict) and item.get("event_id") == event_id for item in events):
        events.append(
            {
                "event_id": event_id,
                "timestamp_utc": opened_at,
                "era": ERA_ID,
                "event": "OPEN_AND_READONLY_BASELINE_INSPECTION",
                "status": "ERA_OPEN_A1_CLOSED",
                "result": artifact["result"],
                "head_before_commit": head_before,
                "artifact": OPEN_ARTIFACT_REL,
                "report": REPORT_REL,
                "risk_codes": [item["code"] for item in risks],
                "runtime_db_service_timer_panel_mutation": False,
                "next_safe_step": NEXT_SAFE_STEP,
                "gemini_red_team_required": True,
            }
        )
    data["updated_at"] = opened_at
    data["updated_at_utc"] = opened_at
    atomic_write_json(path, data)


def append_almanac(opened_at: str, artifact: dict[str, Any], risks: list[dict[str, str]]) -> None:
    path = ROOT / "04_ALMANAC.md"
    text = path.read_text(encoding="utf-8")
    heading = "## ERA55 OPEN AND ERA55A_1 READ-ONLY INSPECTION"
    if heading in text:
        return
    marker = "\n---\n\n## ALMANAC RECORD INSERTION AND CORRECTION CONSTITUTION"
    if text.count(marker) != 1:
        raise RuntimeError("ALMANAC_INSERTION_MARKER_INVALID")
    risk_codes = ", ".join(item["code"] for item in risks)
    entry = f"""
---

{heading}

- UTC: `{opened_at}`
- ERA55 status: `OPEN`
- Completed substep: `{WORK_UNIT}`
- Result: `{artifact['result']}`
- Inspection scope: systemd, timer, runner, queue policy, SQLite PRAGMA/integrity and panel visibility.
- Live runtime, DB, service, timer and panel mutation: `false`
- Identified risk codes: `{risk_codes}`
- Gemini Red Team review: `required`
- Next safe step: `{NEXT_SAFE_STEP}`
"""
    atomic_write_text(path, text.replace(marker, entry + marker, 1))


def make_report(opened_at: str, inspection: dict[str, Any], risks: list[dict[str, str]], result: str) -> str:
    systemd = inspection.get("systemd", {})
    sqlite_data = inspection.get("sqlite", {})
    queue = inspection.get("queue_policy", {})
    runner = inspection.get("runner", {})
    risk_lines = "\n".join(
        f"- **{item['priority']} {item['code']}** — {item['finding']} Required: {item['required_action']}"
        for item in risks
    )
    return f"""# ERA55A_1 READ-ONLY INSPECTION REPORT

UTC: `{opened_at}`

Result: `{result}`

ERA55 status: `OPEN`

Live runtime/DB/service/timer/panel mutation: `false`

## Systemd and Timer

```json
{json.dumps(systemd, ensure_ascii=False, indent=2)}
```

## SQLite Durability and Integrity

```json
{json.dumps(sqlite_data, ensure_ascii=False, indent=2)}
```

## Queue Policy

```json
{json.dumps(queue, ensure_ascii=False, indent=2)}
```

Static conclusion: the current gateway deterministically sorts by priority and retains the top 50. No explicit overflow/drop ledger was detected. Until disproved by runtime evidence, this is treated as a P0 silent intelligence-loss risk.

## Runner Static Inspection

```json
{json.dumps(runner, ensure_ascii=False, indent=2)}
```

## Panel and Runtime File Visibility

```json
{json.dumps(inspection.get('filesystem_visibility', {}), ensure_ascii=False, indent=2)}
```

## Red Team Risks

{risk_lines}

## Decision

- No watchdog applied.
- No index added.
- No journal mode changed.
- No cache added.
- No queue policy changed.
- No incremental write applied.
- No burst load executed.
- Next: `{NEXT_SAFE_STEP}`.
"""


def commit_and_push(expected_files: list[str]) -> tuple[str, str]:
    changed = sorted(line for line in git("diff", "--name-only").splitlines() if line.strip())
    expected = sorted(expected_files)
    if changed != expected:
        raise RuntimeError("UNEXPECTED_CHANGED_FILES\nEXPECTED=" + json.dumps(expected) + "\nACTUAL=" + json.dumps(changed))
    run(["git", "diff", "--check"], timeout=30, check=True)
    git("add", *expected_files)
    git("commit", "-m", "ERA55_OPEN_A1_READONLY_INSPECTION | OK | NO_LIVE_MUTATION")
    head = git("rev-parse", "HEAD")
    push = run(["git", "push", "origin", "main"], timeout=180)
    if push["rc"] != 0:
        raise RuntimeError("COMMIT_CREATED_PUSH_FAILED\n" + json.dumps(push, ensure_ascii=False))
    git("fetch", "origin", "main")
    remote = git("rev-parse", "origin/main")
    if head != remote:
        raise RuntimeError(f"POST_PUSH_HEAD_MISMATCH:LOCAL={head}:REMOTE={remote}")
    if git("status", "--porcelain"):
        raise RuntimeError("POST_PUSH_WORKTREE_NOT_CLEAN")
    return head, remote


def main() -> int:
    head_before = ensure_preconditions()
    backup_dir = Path(tempfile.mkdtemp(prefix="era55a1_backup_", dir="/tmp"))
    for rel in CANONICAL_FILES:
        source = ROOT / rel
        target = backup_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    try:
        opened_at = utc_now()
        inspection = {
            "systemd": systemd_inspection(),
            "sqlite": sqlite_inspection(),
            "queue_policy": queue_policy_inspection(),
            "runner": analyze_python(ROOT / RUNNER_REL),
            "hot_runtime": analyze_python(ROOT / HOT_RUNTIME_REL),
            "filesystem_visibility": filesystem_visibility(),
        }
        risks = derive_risks(inspection)
        has_p0 = any(item["priority"] == "P0" for item in risks)
        integrity = inspection.get("sqlite", {}).get("integrity_check")
        result = "WARN_P0_FINDINGS_RECORDED_READONLY" if has_p0 else "OK_READONLY_INSPECTION_RECORDED"
        if integrity not in ("ok", None):
            result = "BLOCKED_SQLITE_INTEGRITY_NOT_OK"

        artifact = {
            "schema_version": "1.0",
            "work_unit": WORK_UNIT,
            "era": ERA_ID,
            "title": ERA_TITLE,
            "opened_at_utc": opened_at,
            "authorization": "USER_APPROVED_OPEN_ERA55_RUNTIME_OPTIMIZATION",
            "status": "ERA55_OPEN_A1_INSPECTION_CLOSED",
            "result": result,
            "head_before_commit": head_before,
            "scope": {
                "canonical_state_update": True,
                "systemd_readonly_inspection": True,
                "sqlite_readonly_inspection": True,
                "queue_ast_static_inspection": True,
                "runner_static_inspection": True,
                "panel_visibility_inspection": True,
                "runtime_db_service_timer_panel_mutation": False,
                "network_api_call": False,
                "burst_load": False,
                "optimization_apply": False,
            },
            "inspection": inspection,
            "red_team_risks": risks,
            "hard_gates": {
                "silent_drop_allowed": False,
                "data_correctness_regression_allowed": False,
                "watchdog_apply_authorized": False,
                "index_apply_authorized": False,
                "wal_apply_authorized": False,
                "cache_apply_authorized": False,
                "queue_policy_apply_authorized": False,
                "incremental_write_apply_authorized": False,
            },
            "next_safe_step": NEXT_SAFE_STEP,
            "gemini_red_team_required": True,
        }

        update_roadmap_md()
        update_roadmap_json(opened_at, artifact)
        update_runtime(opened_at, artifact, risks)
        update_master_state(artifact, risks)
        update_handoff(artifact, risks)
        append_history(opened_at, artifact, risks, head_before)
        append_almanac(opened_at, artifact, risks)
        atomic_write_json(ROOT / OPEN_ARTIFACT_REL, artifact)
        atomic_write_text(ROOT / REPORT_REL, make_report(opened_at, inspection, risks, result))

        for rel in ["PROJECT_RUNTIME.json", "PROJECT_HISTORY.json", "data/tokenoskobi_v1_v8_master_era_roadmap.json", OPEN_ARTIFACT_REL]:
            load_json(ROOT / rel)

        expected = CANONICAL_FILES + GENERATED_FILES
        head_after, remote_after = commit_and_push(expected)

        print("ERA55_OPEN_AND_A1_READONLY_INSPECTION=SUCCESS")
        print(f"RESULT={result}")
        print(f"HEAD_BEFORE={head_before}")
        print(f"CANONICAL_HEAD={head_after}")
        print(f"REMOTE_HEAD={remote_after}")
        print("ERA55_STATUS=OPEN")
        print(f"LAST_COMPLETED={WORK_UNIT}")
        print(f"NEXT_SAFE_STEP={NEXT_SAFE_STEP}")
        print("LIVE_RUNTIME_DB_SERVICE_TIMER_PANEL_MUTATION=false")
        print(f"ARTIFACT={OPEN_ARTIFACT_REL}")
        print(f"REPORT={REPORT_REL}")
        print("GEMINI_RED_TEAM_REQUIRED=true")
        print("WORKTREE=CLEAN")
        print(f"BACKUP_DIR={backup_dir}")
        return 0
    except Exception:
        if not git("log", "-1", "--pretty=%s", check=False).startswith("ERA55_OPEN_A1_READONLY_INSPECTION"):
            for rel in CANONICAL_FILES:
                backup = backup_dir / rel
                target = ROOT / rel
                if backup.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup, target)
            for rel in GENERATED_FILES:
                target = ROOT / rel
                if target.exists():
                    target.unlink()
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERA55_OPEN_AND_A1_READONLY_INSPECTION=FAILED:{exc}", file=sys.stderr)
        raise
