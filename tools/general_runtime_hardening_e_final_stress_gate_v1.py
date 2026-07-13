#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORK = "GENERAL_RUNTIME_HARDENING_E_FINAL_STRESS_GATE"
NEXT = "ERA57_AUTONOMOUS_RESEARCH_LAYER_OPENING_DECISION"
RESULT = "OK_GENERAL_RUNTIME_HARDENING_FINAL_STRESS_GATE_CLOSED"
ARTIFACT_REL = (
    "data/control/"
    "general_runtime_hardening_e_final_stress_gate_v1.json"
)
SERVICE = "tokenoskobi-news-radar-refresh.service"
RUNNER_REL = "tools/news_radar_refresh_runner_v1.py"
SYNTHETIC_SCENARIOS = {
    "db_latency",
    "lock_contention",
    "sigterm",
    "sigkill",
    "partial_publish",
    "stale_cache",
    "corrupt_cache",
    "disk_full",
    "network_timeout",
    "duplicate_replay",
}
POSITIVE_REPEATS = 25
NEGATIVE_REPEATS = 25
PARALLEL_WRAPPER_RUNS = 12
TAMPER_WRAPPER_RUNS = 6


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def optional_sha256(path: Path) -> str | None:
    return sha256(path) if path.is_file() else None


def run(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def section(text: str, heading: str, body: str) -> str:
    start = text.find(heading)
    if start < 0:
        return text.rstrip() + "\n\n" + heading + "\n\n" + body.rstrip() + "\n"
    end = text.find("\n## ", start + len(heading))
    if end < 0:
        end = len(text)
    return text[:start] + heading + "\n\n" + body.rstrip() + "\n" + text[end:]


def systemctl_value(root: Path, *args: str) -> str:
    result = run(["systemctl", *args], cwd=root, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(
            "SYSTEMCTL_FAILED:"
            + " ".join(args)
            + ":"
            + result.stderr.strip()
        )
    return result.stdout.strip()


def recursive_update_era57(value: Any, next_step: str) -> bool:
    changed = False
    if isinstance(value, dict):
        if value.get("id") == "ERA57":
            value["status"] = "PLANNED_OPENING_DECISION_READY"
            value["opened"] = False
            value["entry_gate"] = "GENERAL_RUNTIME_HARDENING_CLOSED_VERIFIED"
            value["next_safe_step"] = next_step
            changed = True
        for child in value.values():
            if recursive_update_era57(child, next_step):
                changed = True
    elif isinstance(value, list):
        for child in value:
            if recursive_update_era57(child, next_step):
                changed = True
    return changed


def validate_synthetic_harness(root: Path, temp: Path) -> dict[str, Any]:
    output_path = temp / "synthetic_stress_result.json"
    result = run(
        [
            sys.executable,
            str(root / "tests" / "general_runtime_stress_harness_v1.py"),
            "--scenario",
            "all",
            "--output",
            str(output_path),
        ],
        cwd=root,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=240,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "SYNTHETIC_HARNESS_FAILED:"
            + str(result.returncode)
            + ":"
            + result.stderr[-2000:]
        )
    data = load(output_path)
    if data.get("verdict") != "OK":
        raise RuntimeError("SYNTHETIC_HARNESS_VERDICT_NOT_OK")
    scenarios = data.get("scenarios") or {}
    if set(scenarios) != SYNTHETIC_SCENARIOS:
        raise RuntimeError("SYNTHETIC_SCENARIO_SET_MISMATCH")
    if not all(
        isinstance(item, dict) and item.get("status") == "OK"
        for item in scenarios.values()
    ):
        raise RuntimeError("SYNTHETIC_SCENARIO_FAILURE")
    if data.get("source_hash_verified") is not True:
        raise RuntimeError("SYNTHETIC_SOURCE_HASH_NOT_VERIFIED")
    if data.get("production_mutation") is not False:
        raise RuntimeError("SYNTHETIC_PRODUCTION_MUTATION_NOT_FALSE")
    return {
        "returncode": result.returncode,
        "scenario_count": len(scenarios),
        "scenario_names": sorted(scenarios),
        "verdict": data.get("verdict"),
        "source_hash_verified": data.get("source_hash_verified"),
        "production_mutation": data.get("production_mutation"),
        "result": data,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-1000:],
    }


def gate_stress(root: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from core.runtime_policy_authority_gate import evaluate_runtime_stage

    grants = load(root / "config" / "runtime_stage_grants_v1.json")
    grant = grants["grants"]["news_radar_refresh_v1"]
    required_env = dict(
        grant["stages"]["LEDGER_RECOVERY"]["required_environment"]
    )
    base_env = dict(os.environ)
    base_env.update(required_env)
    base_env["TOKENOSKOBI_ROOT"] = str(root)
    base_env["TOKENOSKOBI_SERVICE_IDENTITY"] = SERVICE

    positive_stages = (
        "SOURCE_CONTRACT_RESOLUTION",
        "LEDGER_RECOVERY",
        "DERIVED_DB_WRITE",
        "HOT_PUBLISH",
    )
    positive_count = 0
    positive_samples: dict[str, Any] = {}
    for repeat in range(POSITIVE_REPEATS):
        for stage in positive_stages:
            decision = evaluate_runtime_stage(
                stage,
                root=root,
                service_name=SERVICE,
                runner_path=RUNNER_REL,
                environ=base_env,
            )
            if decision.get("ok") is not True or decision.get("decision") != "ALLOW":
                raise RuntimeError(
                    f"GATE_POSITIVE_FAILED:{repeat}:{stage}:"
                    + json.dumps(decision, sort_keys=True)
                )
            positive_count += 1
            positive_samples.setdefault(stage, decision)

    negative_count = 0
    negative_samples: dict[str, Any] = {}
    for repeat in range(NEGATIVE_REPEATS):
        missing_env = dict(base_env)
        missing_env.pop("TOKENOSKOBI_A23_GUARDED_PRODUCTION", None)

        live_runtime = json.loads(json.dumps(runtime))
        live_runtime["canonical_runtime_pointer"][
            "live_source_fetch_authorized"
        ] = True

        cases = {
            "missing_required_environment": evaluate_runtime_stage(
                "LEDGER_RECOVERY",
                root=root,
                service_name=SERVICE,
                runner_path=RUNNER_REL,
                environ=missing_env,
            ),
            "wrong_service_identity": evaluate_runtime_stage(
                "SOURCE_CONTRACT_RESOLUTION",
                root=root,
                service_name="unauthorized.service",
                runner_path=RUNNER_REL,
                environ=base_env,
            ),
            "unknown_stage": evaluate_runtime_stage(
                "UNKNOWN_STAGE",
                root=root,
                service_name=SERVICE,
                runner_path=RUNNER_REL,
                environ=base_env,
            ),
            "live_fetch_authority_expansion": evaluate_runtime_stage(
                "SOURCE_CONTRACT_RESOLUTION",
                root=root,
                service_name=SERVICE,
                runner_path=RUNNER_REL,
                environ=base_env,
                runtime_override=live_runtime,
            ),
        }
        for name, decision in cases.items():
            if decision.get("ok") is not False or decision.get("decision") != "DENY":
                raise RuntimeError(
                    f"GATE_NEGATIVE_NOT_DENIED:{repeat}:{name}:"
                    + json.dumps(decision, sort_keys=True)
                )
            negative_count += 1
            negative_samples.setdefault(name, decision)

    return {
        "positive_repeats": POSITIVE_REPEATS,
        "positive_stage_count": len(positive_stages),
        "positive_evaluation_count": positive_count,
        "positive_samples": positive_samples,
        "negative_repeats": NEGATIVE_REPEATS,
        "negative_case_count": 4,
        "negative_evaluation_count": negative_count,
        "negative_samples": negative_samples,
        "all_positive_allowed": True,
        "all_negative_denied": True,
    }


def wrapper_env(
    root: Path,
    temp: Path,
    temp_db: Path,
    run_id: str,
    *,
    service_identity: str,
) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "TOKENOSKOBI_ROOT": str(root),
            "TOKENOSKOBI_DB_PATH": str(temp_db),
            "TOKENOSKOBI_SERVICE_IDENTITY": service_identity,
            "TOKENOSKOBI_LEDGER_WRITER_ENABLED": "0",
            "TOKENOSKOBI_RUNNER_LOCK_ENABLED": "1",
            "TOKENOSKOBI_RUNNER_LOCK_PATH": str(temp / f"{run_id}.lock"),
            "TOKENOSKOBI_A10_ORDER_LOG": str(temp / f"{run_id}.order.log"),
            "TOKENOSKOBI_HOT_OUTPUT_PATH": str(temp / f"{run_id}.hot.json"),
            "TOKENOSKOBI_LEDGER_RECOVERY_STATE_PATH": str(
                temp / f"{run_id}.recovery.json"
            ),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return env


def wrapper_stress(root: Path, temp: Path, production_db: Path) -> dict[str, Any]:
    temp_db = temp / "parallel_readonly.sqlite"
    shutil.copy2(production_db, temp_db)
    temp_hash_before = sha256(temp_db)
    wrapper = root / RUNNER_REL

    def good(index: int) -> dict[str, Any]:
        run_id = f"good_{index:02d}"
        result = run(
            [sys.executable, str(wrapper)],
            cwd=root,
            env=wrapper_env(
                root,
                temp,
                temp_db,
                run_id,
                service_identity=SERVICE,
            ),
            timeout=180,
        )
        order_path = temp / f"{run_id}.order.log"
        order = (
            order_path.read_text(encoding="utf-8")
            if order_path.is_file()
            else ""
        )
        ok = all(
            (
                result.returncode == 0,
                "RUNTIME_POLICY_AUTHORITY_GATE" in result.stdout,
                "SUCCESS_NOOP_FAIL_CLOSED" in result.stdout,
                '"network_call": false' in result.stdout,
                "DERIVED_START" not in order,
                "HOT_START" not in order,
            )
        )
        return {
            "index": index,
            "returncode": result.returncode,
            "ok": ok,
            "order": order,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-1000:],
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        good_results = list(
            executor.map(good, range(PARALLEL_WRAPPER_RUNS))
        )
    if not all(item["ok"] for item in good_results):
        raise RuntimeError("PARALLEL_WRAPPER_NOOP_STRESS_FAILED")

    tamper_results: list[dict[str, Any]] = []
    for index in range(TAMPER_WRAPPER_RUNS):
        run_id = f"tamper_{index:02d}"
        result = run(
            [sys.executable, str(wrapper)],
            cwd=root,
            env=wrapper_env(
                root,
                temp,
                temp_db,
                run_id,
                service_identity="unauthorized.service",
            ),
            timeout=180,
        )
        ok = all(
            (
                result.returncode == 76,
                "RUNTIME_POLICY_AUTHORITY_GATE" in result.stdout,
                '"decision": "DENY"' in result.stdout,
                "SUCCESS_NOOP_FAIL_CLOSED" not in result.stdout,
            )
        )
        tamper_results.append(
            {
                "index": index,
                "returncode": result.returncode,
                "ok": ok,
                "stdout_tail": result.stdout[-2000:],
                "stderr_tail": result.stderr[-1000:],
            }
        )
    if not all(item["ok"] for item in tamper_results):
        raise RuntimeError("WRAPPER_IDENTITY_TAMPER_NOT_FAIL_CLOSED")

    temp_hash_after = sha256(temp_db)
    if temp_hash_before != temp_hash_after:
        raise RuntimeError("TEMP_READONLY_DB_MUTATED")

    return {
        "parallel_wrapper_runs": PARALLEL_WRAPPER_RUNS,
        "parallel_success_count": sum(
            1 for item in good_results if item["ok"]
        ),
        "parallel_results": good_results,
        "tamper_wrapper_runs": TAMPER_WRAPPER_RUNS,
        "tamper_denied_count": sum(
            1 for item in tamper_results if item["ok"]
        ),
        "tamper_results": tamper_results,
        "temp_db_sha256_before": temp_hash_before,
        "temp_db_sha256_after": temp_hash_after,
        "temp_db_mutation": False,
        "network_call": False,
        "derived_execution": False,
        "hot_execution": False,
    }


def validate_broad_denies(root: Path) -> dict[str, Any]:
    authority = load(root / "config" / "authority_state_v1.json")
    policy = load(root / "config" / "project_policy_registry_v1.json")
    grants = load(root / "config" / "runtime_stage_grants_v1.json")

    checks = {
        "ai_authority_zero": authority["authority"]["ai"]["level"] == 0,
        "trade_live_denied": authority["authority"]["trade"]["live_allowed"] is False,
        "db_write_broad_denied": authority["authority"]["write"]["db_write_allowed"] is False,
        "file_write_broad_denied": authority["authority"]["write"]["file_write_allowed"] is False,
        "rpc_broad_denied": authority["authority"]["rpc"]["allowed"] is False,
        "policy_deny_default": policy["defaults"]["deny_by_default"] is True,
        "policy_deny_mutation": policy["decision_defaults"]["deny_mutation"] is True,
        "no_authority_expansion": grants["no_authority_expansion"] is True,
        "deny_unknown_grant": grants["deny_unknown_grant"] is True,
        "deny_unknown_stage": grants["deny_unknown_stage"] is True,
    }
    if not all(checks.values()):
        raise RuntimeError("BROAD_DENY_INVARIANT_FAILED")
    return checks


def apply_canonical_close(
    root: Path,
    artifact: dict[str, Any],
    now: str,
) -> None:
    runtime_path = root / "PROJECT_RUNTIME.json"
    history_path = root / "PROJECT_HISTORY.json"
    artifact_path = root / ARTIFACT_REL

    save(artifact_path, artifact)

    runtime = load(runtime_path)
    pointer = runtime["canonical_runtime_pointer"]
    hardening = pointer.setdefault("general_runtime_hardening", {})
    substeps = hardening.setdefault("substeps", {})
    substeps["E_FINAL_STRESS_GATE"] = "CLOSED_VERIFIED"
    hardening.update(
        {
            "status": "CLOSED_VERIFIED",
            "final_stress_gate_closed": True,
            "final_stress_result": RESULT,
            "final_stress_artifact": ARTIFACT_REL,
            "production_mutation": False,
            "era57_opened": False,
            "era57_opening_decision_ready": True,
            "next_safe_step": NEXT,
            "closed_at_utc": now,
            "updated_at_utc": now,
        }
    )
    pointer.update(
        {
            "current_stage": "GENERAL_RUNTIME_HARDENING_CLOSED_VERIFIED",
            "project_status": "ERA56_CLOSED_ERA57_OPENING_DECISION_READY",
            "last_completed": WORK,
            "last_result": RESULT,
            "last_artifact": ARTIFACT_REL,
            "general_runtime_stress_harness_verified": True,
            "stress_harness_execution_evidence": ARTIFACT_REL,
            "stress_harness_execution_result": RESULT,
            "stress_harness_final_gate_closed": True,
            "pre_era57_hardening_closed": True,
            "era57_opening_decision_ready": True,
            "broad_authority_expansion": False,
            "live_source_fetch_authorized": False,
            "era57_opened": False,
            "production_mutation": False,
            "production_chaos_test_authorized": False,
            "next_safe_step": NEXT,
            "updated_at_utc": now,
        }
    )
    runtime.update(
        {
            "project_status": "ERA56_CLOSED_ERA57_OPENING_DECISION_READY",
            "last_completed": WORK,
            "last_result": RESULT,
            "last_artifact": ARTIFACT_REL,
            "next_safe_step": NEXT,
            "work_unit": WORK,
            "updated_at": now,
            "updated_at_utc": now,
        }
    )
    runtime["current_problem"] = {
        "code": "NONE",
        "severity": "NONE",
        "evidence": ARTIFACT_REL,
    }
    runtime["current_state"] = {
        "project_status": "ERA56_CLOSED_ERA57_OPENING_DECISION_READY",
        "runtime_status": "GENERAL_RUNTIME_HARDENING_CLOSED_VERIFIED",
        "mode": "ERA57_OPENING_DECISION_READY_NO_AUTHORITY_GRANTED",
        "last_action": {
            "task": WORK,
            "result": RESULT,
            "artifact": ARTIFACT_REL,
            "timestamp": now,
        },
        "current_problem": runtime["current_problem"],
        "next_safe_step": {
            "id": NEXT,
            "status": "READY",
            "human_authorization_required": True,
            "production_mutation": False,
        },
        "updated_at": now,
    }
    runtime["current_work_unit"] = {
        "id": WORK,
        "main_line": "GENERAL_RUNTIME_HARDENING",
        "substep": "E_FINAL_STRESS_GATE",
        "status": "CLOSED_VERIFIED",
        "result": RESULT,
        "artifact": ARTIFACT_REL,
        "production_mutation": False,
        "next_step": NEXT,
    }
    save(runtime_path, runtime)

    history = load(history_path)
    events = history.setdefault("events", [])
    if not any(
        isinstance(event, dict) and event.get("event_id") == WORK
        for event in events
    ):
        events.append(
            {
                "event_id": WORK,
                "timestamp_utc": now,
                "status": "CLOSED_VERIFIED",
                "result": RESULT,
                "artifact": ARTIFACT_REL,
                "general_runtime_hardening_closed": True,
                "era57_opening_decision_ready": True,
                "era57_opened": False,
                "live_fetch_authorized": False,
                "production_mutation": False,
                "next_safe_step": NEXT,
            }
        )
    history["updated_at"] = now
    history["updated_at_utc"] = now
    save(history_path, history)

    master_path = root / "06_PROJECT_MASTER_STATE.md"
    master = master_path.read_text(encoding="utf-8")
    master = section(
        master,
        "## 01 PROJECT STATUS",
        """```text
PROJECT=TOKENOSKOBI / COINOSKOBI
PROJECT_STATUS=ERA56_CLOSED_ERA57_OPENING_DECISION_READY
CURRENT_VERSION_LINE=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
CURRENT_HUMAN_SUMMARY=06_PROJECT_MASTER_STATE.md
GIT_BRANCH=main
GIT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD
BOOT_HEALTH=100/100
```""",
    )
    master = section(
        master,
        "## 02 CURRENT MAJOR-LINE POSITION",
        """```text
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
ERA55_STATUS=CLOSED_SEALED
ERA56_STATUS=CLOSED_SEALED
GENERAL_RUNTIME_HARDENING_STATUS=CLOSED_VERIFIED
FINAL_STRESS_GATE=CLOSED_VERIFIED
ERA57_OPENING_DECISION_READY=true
ERA57_OPENED=false
LIVE_FETCH_AUTHORIZED=false
PRODUCTION_MUTATION=false
```""",
    )
    master = section(
        master,
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
SYNTHETIC_SCENARIOS=10/10
POLICY_AUTHORITY_POSITIVE=100/100
POLICY_AUTHORITY_NEGATIVE=100/100
PARALLEL_WRAPPER_NOOP=12/12
IDENTITY_TAMPER_DENIED=6/6
PRODUCTION_MUTATION=false
ERA57_OPENED=false
```

NEXT_SAFE_STEP={NEXT}""",
    )
    master = section(
        master,
        "## 10 NEXT SAFE STEP",
        f"""```text
NEXT_SAFE_STEP={NEXT}
```

The pre-ERA57 hardening line is closed. The next action is only the
explicit human decision on whether to open ERA57. No live source,
network budget, trade authority or production mutation is implied.""",
    )
    master_path.write_text(master.rstrip() + "\n", encoding="utf-8")

    handoff_path = root / "07_PROJECT_HANDOFF.md"
    handoff = handoff_path.read_text(encoding="utf-8")
    handoff = section(
        handoff,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        f"""PROJECT_STATUS=ERA56_CLOSED_ERA57_OPENING_DECISION_READY
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_MAIN_LINE=GENERAL_RUNTIME_HARDENING
CURRENT_STAGE=GENERAL_RUNTIME_HARDENING_CLOSED_VERIFIED
LAST_COMPLETED={WORK}
FINAL_STRESS_GATE=CLOSED_VERIFIED
ERA57_OPENING_DECISION_READY=true
ERA57_OPENED=false
LIVE_FETCH_AUTHORIZED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""",
    )
    handoff = section(
        handoff,
        "## 03 LAST VERIFIED WORK",
        f"""LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
SYNTHETIC_SCENARIOS=10/10
POLICY_AUTHORITY_POSITIVE=100/100
POLICY_AUTHORITY_NEGATIVE=100/100
PARALLEL_WRAPPER_NOOP=12/12
IDENTITY_TAMPER_DENIED=6/6
GENERAL_RUNTIME_HARDENING=CLOSED_VERIFIED
ERA57_OPENED=false
PRODUCTION_MUTATION=false""",
    )
    handoff = section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Decide whether to open ERA57 under a separate bounded scope.
- Do not treat readiness as ERA57 authorization.
- Do not enable live source fetch automatically.
- Do not grant network budget implicitly.
- Do not broaden policy/authority grants.
- Production mutation remains blocked.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff = section(
        handoff,
        "## 08 NEXT SESSION EXECUTION RULE",
        """1. Read PROJECT_RUNTIME.json first.
2. Confirm GENERAL_RUNTIME_HARDENING is CLOSED_VERIFIED.
3. Treat ERA57 as not opened until explicit human approval.
4. If opened, create a bounded ERA57 scope before implementation.
5. Preserve live-fetch, network-budget and production-mutation locks.""",
    )
    handoff_path.write_text(handoff.rstrip() + "\n", encoding="utf-8")

    roadmap_path = root / "03_ROADMAP.md"
    roadmap = roadmap_path.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "- Final isolated stress verification is the remaining ERA57 gate.\n",
        "- Final isolated stress verification is closed and verified.\n",
    )
    roadmap = roadmap.replace(
        "- General runtime hardening is active.\n",
        "- General runtime hardening is closed and verified.\n",
    )
    roadmap = roadmap.replace(
        "- Next safe step: `GENERAL_RUNTIME_HARDENING_E_FINAL_STRESS_GATE`.",
        f"- Next safe step: `{NEXT}`.",
    )
    roadmap_path.write_text(roadmap.rstrip() + "\n", encoding="utf-8")

    roadmap_json_path = root / "data" / "tokenoskobi_v1_v8_master_era_roadmap.json"
    roadmap_json = load(roadmap_json_path)
    roadmap_json["current_direction"] = {
        "status": "ERA57_OPENING_DECISION_READY",
        "completed_line": "GENERAL_RUNTIME_HARDENING",
        "completed_result": RESULT,
        "final_stress_gate_closed": True,
        "era57_opened": False,
        "live_source_fetch_authorized": False,
        "production_mutation": False,
        "next_safe_step": NEXT,
        "updated_at_utc": now,
    }
    recursive_update_era57(roadmap_json, NEXT)
    save(roadmap_json_path, roadmap_json)

    machine_path = root / "data" / "control" / "latest_tk_machine_state.json"
    if machine_path.is_file():
        machine = load(machine_path)
        machine["created_at_utc"] = now
        machine["collect_mode"] = "final_stress_gate_closure_no_runtime_mutation"
        machine["current_state"] = {
            "authority": "PROJECT_RUNTIME.json",
            "project_status": "ERA56_CLOSED_ERA57_OPENING_DECISION_READY",
            "runtime_status": "GENERAL_RUNTIME_HARDENING_CLOSED_VERIFIED",
            "active_work_unit": None,
            "last_action": {
                "task": WORK,
                "result": RESULT,
                "artifact": ARTIFACT_REL,
                "timestamp": now,
            },
            "next_safe_step": {
                "name": NEXT,
                "status": "READY",
            },
        }
        machine["known_facts"] = {
            "general_runtime_hardening_closed": True,
            "final_stress_gate_closed": True,
            "era57_opening_decision_ready": True,
            "era57_opened": False,
            "live_source_fetch_authorized": False,
            "production_mutation": False,
        }
        save(machine_path, machine)

    report_path = root / "reports" / "LATEST_TK_AI_HANDOFF.md"
    report_path.write_text(
        f"""# LATEST TK AI HANDOFF

CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_MAIN_LINE=GENERAL_RUNTIME_HARDENING
CURRENT_STAGE=GENERAL_RUNTIME_HARDENING_CLOSED_VERIFIED
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
SYNTHETIC_SCENARIOS=10/10
POLICY_AUTHORITY_POSITIVE=100/100
POLICY_AUTHORITY_NEGATIVE=100/100
PARALLEL_WRAPPER_NOOP=12/12
IDENTITY_TAMPER_DENIED=6/6
GENERAL_RUNTIME_HARDENING=CLOSED_VERIFIED
ERA57_OPENING_DECISION_READY=true
ERA57_OPENED=false
LIVE_FETCH_AUTHORIZED=false
PRODUCTION_MUTATION=false
NEXT_SAFE_STEP={NEXT}
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=os.getenv("TOKENOSKOBI_ROOT", "/root/tokenoskobi_clean_v1"),
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    runtime_path = root / "PROJECT_RUNTIME.json"
    db_path = root / "data" / "tokenoskobi_clean_v1.sqlite"
    service_path = Path(
        "/etc/systemd/system/tokenoskobi-news-radar-refresh.service"
    )
    timer_path = Path(
        "/etc/systemd/system/tokenoskobi-news-radar-refresh.timer"
    )
    dropin_path = Path(
        "/etc/systemd/system/tokenoskobi-news-radar-refresh.service.d/"
        "90-era55a23-guarded-production.conf"
    )
    hot_output_path = root / "runtime" / "state" / "hot_intelligence_ingress_gateway_v1.json"

    runtime = load(runtime_path)
    pointer = runtime["canonical_runtime_pointer"]
    if pointer.get("next_safe_step") != WORK:
        raise SystemExit(
            "UNEXPECTED_NEXT_SAFE_STEP=" + str(pointer.get("next_safe_step"))
        )
    if pointer.get("era57_opened") is not False:
        raise SystemExit("ERA57_MUST_REMAIN_CLOSED")
    if pointer.get("live_source_fetch_authorized") is not False:
        raise SystemExit("LIVE_FETCH_MUST_REMAIN_DISABLED")
    if pointer.get("production_mutation") is not False:
        raise SystemExit("PRODUCTION_MUTATION_MUST_REMAIN_FALSE")
    if pointer.get("production_chaos_test_authorized") is not False:
        raise SystemExit("PRODUCTION_CHAOS_MUST_REMAIN_BLOCKED")
    if pointer.get("policy_authority_reachable") is not True:
        raise SystemExit("POLICY_AUTHORITY_MUST_BE_REACHABLE")

    for required in (
        db_path,
        service_path,
        timer_path,
        dropin_path,
        root / RUNNER_REL,
        root / "tests" / "general_runtime_stress_harness_v1.py",
        root / "core" / "runtime_policy_authority_gate.py",
        root / "config" / "runtime_stage_grants_v1.json",
    ):
        if not required.is_file():
            raise SystemExit(f"REQUIRED_FILE_MISSING:{required}")

    protected_before = {
        "production_db": sha256(db_path),
        "service": sha256(service_path),
        "timer": sha256(timer_path),
        "dropin": sha256(dropin_path),
        "hot_output": optional_sha256(hot_output_path),
    }
    timer_active_before = systemctl_value(
        root,
        "is-active",
        "tokenoskobi-news-radar-refresh.timer",
    )
    timer_enabled_before = systemctl_value(
        root,
        "is-enabled",
        "tokenoskobi-news-radar-refresh.timer",
    )

    with tempfile.TemporaryDirectory(
        prefix="general_runtime_final_stress_"
    ) as temp_name:
        temp = Path(temp_name)
        synthetic = validate_synthetic_harness(root, temp)
        gate = gate_stress(root, runtime)
        wrapper = wrapper_stress(root, temp, db_path)

    broad_denies = validate_broad_denies(root)

    protected_after = {
        "production_db": sha256(db_path),
        "service": sha256(service_path),
        "timer": sha256(timer_path),
        "dropin": sha256(dropin_path),
        "hot_output": optional_sha256(hot_output_path),
    }
    if protected_before != protected_after:
        raise RuntimeError("PROTECTED_PRODUCTION_HASH_CHANGED")

    timer_active_after = systemctl_value(
        root,
        "is-active",
        "tokenoskobi-news-radar-refresh.timer",
    )
    timer_enabled_after = systemctl_value(
        root,
        "is-enabled",
        "tokenoskobi-news-radar-refresh.timer",
    )
    if timer_active_before != timer_active_after:
        raise RuntimeError("TIMER_ACTIVE_STATE_CHANGED")
    if timer_enabled_before != timer_enabled_after:
        raise RuntimeError("TIMER_ENABLED_STATE_CHANGED")
    if timer_active_after != "active":
        raise RuntimeError("TIMER_NOT_ACTIVE")
    if timer_enabled_after != "enabled":
        raise RuntimeError("TIMER_NOT_ENABLED")

    now = datetime.now(timezone.utc).isoformat()
    artifact = {
        "schema": "general_runtime_hardening_e_final_stress_gate_v1",
        "timestamp_utc": now,
        "work_unit": WORK,
        "status": "CLOSED_VERIFIED",
        "result": RESULT,
        "synthetic_harness": synthetic,
        "policy_authority_stress": gate,
        "wrapper_stress": wrapper,
        "broad_deny_invariants": broad_denies,
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "protected_hashes_unchanged": True,
        "timer_active_before": timer_active_before,
        "timer_active_after": timer_active_after,
        "timer_enabled_before": timer_enabled_before,
        "timer_enabled_after": timer_enabled_after,
        "production_db_mutation": False,
        "production_service_execution": False,
        "service_timer_change": False,
        "production_chaos_test": False,
        "network_call": False,
        "broad_authority_expansion": False,
        "live_source_fetch_authorized": False,
        "era57_opened": False,
        "era57_opening_decision_ready": True,
        "next_safe_step": NEXT,
    }

    print("GENERAL_RUNTIME_FINAL_STRESS=OK")
    print("SYNTHETIC_SCENARIOS=10/10")
    print("POLICY_AUTHORITY_POSITIVE=100/100")
    print("POLICY_AUTHORITY_NEGATIVE=100/100")
    print("PARALLEL_WRAPPER_NOOP=12/12")
    print("IDENTITY_TAMPER_DENIED=6/6")
    print("PROTECTED_HASHES_UNCHANGED=true")
    print("PRODUCTION_MUTATION=false")
    print("ERA57_OPENED=false")

    if args.apply:
        apply_canonical_close(root, artifact, now)
        print("GENERAL_RUNTIME_HARDENING=CLOSED_VERIFIED")
        print("ERA57_OPENING_DECISION_READY=true")
        print(f"NEXT_SAFE_STEP={NEXT}")
    else:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
