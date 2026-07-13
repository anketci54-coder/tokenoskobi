#!/usr/bin/env python3
from __future__ import annotations

import argparse
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

WORK = "GENERAL_RUNTIME_HARDENING_D_POLICY_AUTHORITY_REACHABILITY"
NEXT = "GENERAL_RUNTIME_HARDENING_E_FINAL_STRESS_GATE"
RESULT = "OK_POLICY_AUTHORITY_REACHABLE_FAIL_CLOSED"
SERVICE = "tokenoskobi-news-radar-refresh.service"
RUNNER = "tools/news_radar_refresh_runner_v1.py"
ARTIFACT_REL = (
    "data/control/"
    "general_runtime_hardening_d_policy_authority_reachability_v1.json"
)


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


def run(argv: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
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


def systemd_truth(root: Path, required_env: dict[str, str]) -> dict[str, Any]:
    result = run(
        [
            "systemctl",
            "show",
            SERVICE,
            "--no-pager",
            "-p",
            "ExecStart",
            "-p",
            "Environment",
            "-p",
            "FragmentPath",
            "-p",
            "DropInPaths",
            "-p",
            "ActiveState",
            "-p",
            "SubState",
            "-p",
            "Result",
        ],
        cwd=root,
    )
    if result.returncode != 0:
        raise RuntimeError("SYSTEMD_SHOW_FAILED:" + result.stderr.strip())
    props = dict(
        line.split("=", 1)
        for line in result.stdout.splitlines()
        if "=" in line
    )
    exec_start = props.get("ExecStart", "")
    environment = props.get("Environment", "")
    if str(root / RUNNER) not in exec_start:
        raise RuntimeError("SYSTEMD_RUNNER_NOT_BOUND")
    for key, expected in required_env.items():
        token = f"{key}={expected}"
        if token not in environment:
            raise RuntimeError(f"SYSTEMD_REQUIRED_ENV_MISSING:{key}")
    fragment = Path(props.get("FragmentPath") or "")
    dropins = [
        Path(value)
        for value in (props.get("DropInPaths") or "").split()
        if value
    ]
    return {
        "service": SERVICE,
        "active_state": props.get("ActiveState"),
        "sub_state": props.get("SubState"),
        "result": props.get("Result"),
        "exec_start": exec_start,
        "environment": environment,
        "fragment_path": str(fragment) if fragment else None,
        "fragment_sha256": sha256(fragment) if fragment.is_file() else None,
        "dropins": [
            {
                "path": str(path),
                "sha256": sha256(path) if path.is_file() else None,
            }
            for path in dropins
        ],
        "required_environment_match": True,
        "runner_binding_match": True,
    }


def update_config_metadata(root: Path) -> None:
    authority_path = root / "config" / "authority_state_v1.json"
    policy_path = root / "config" / "project_policy_registry_v1.json"

    authority = load(authority_path)
    authority["scaffold_status"] = "ACTIVE_RUNTIME_BASELINE_CONSUMED_BY_SCOPED_GATE"
    documentation = authority.setdefault("documentation", {})
    documentation["runtime_effect"] = (
        "Loaded and validated by core/runtime_policy_authority_gate.py. "
        "Broad deny-by-default remains unchanged; scoped runtime grants are "
        "stored separately in config/runtime_stage_grants_v1.json."
    )
    future = authority.setdefault("future_consumers", [])
    for value in (
        "core/runtime_policy_authority_gate.py",
        "tools/news_radar_refresh_runner_v1.py",
    ):
        if value not in future:
            future.append(value)
    authority.setdefault("audit", {})["migration_state"] = (
        "baseline_active_scoped_runtime_gate_bound"
    )
    save(authority_path, authority)

    policy = load(policy_path)
    policy["scaffold_status"] = "ACTIVE_RUNTIME_BASELINE_CONSUMED_BY_SCOPED_GATE"
    documentation = policy.setdefault("documentation", {})
    documentation["runtime_effect"] = (
        "Loaded and validated by core/runtime_policy_authority_gate.py. "
        "Broad deny-by-default remains unchanged; stage-specific existing "
        "authority is constrained by config/runtime_stage_grants_v1.json."
    )
    future = policy.setdefault("future_consumers", [])
    for value in (
        "core/runtime_policy_authority_gate.py",
        "tools/news_radar_refresh_runner_v1.py",
    ):
        if value not in future:
            future.append(value)
    policy.setdefault("audit", {})["migration_state"] = (
        "baseline_active_scoped_runtime_gate_bound"
    )
    save(policy_path, policy)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=os.getenv("TOKENOSKOBI_ROOT", "/root/tokenoskobi_clean_v1"),
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from core.runtime_policy_authority_gate import evaluate_runtime_stage

    runtime_path = root / "PROJECT_RUNTIME.json"
    history_path = root / "PROJECT_HISTORY.json"
    authority_path = root / "config" / "authority_state_v1.json"
    policy_path = root / "config" / "project_policy_registry_v1.json"
    grant_path = root / "config" / "runtime_stage_grants_v1.json"
    wrapper_path = root / RUNNER
    db_path = root / "data" / "tokenoskobi_clean_v1.sqlite"
    artifact_path = root / ARTIFACT_REL

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

    grant_registry = load(grant_path)
    grant = grant_registry["grants"]["news_radar_refresh_v1"]
    mutation_env = dict(grant["stages"]["LEDGER_RECOVERY"]["required_environment"])
    base_env = dict(os.environ)
    base_env.update(mutation_env)
    base_env["TOKENOSKOBI_ROOT"] = str(root)
    base_env["TOKENOSKOBI_SERVICE_IDENTITY"] = SERVICE

    systemd = systemd_truth(root, mutation_env)

    stage_decisions: dict[str, Any] = {}
    for stage in (
        "SOURCE_CONTRACT_RESOLUTION",
        "LEDGER_RECOVERY",
        "DERIVED_DB_WRITE",
        "HOT_PUBLISH",
    ):
        decision = evaluate_runtime_stage(
            stage,
            root=root,
            service_name=SERVICE,
            runner_path=RUNNER,
            environ=base_env,
        )
        if decision.get("decision") != "ALLOW" or decision.get("ok") is not True:
            raise RuntimeError(
                "EXPECTED_STAGE_ALLOW_FAILED:"
                + stage
                + ":"
                + json.dumps(decision, sort_keys=True)
            )
        stage_decisions[stage] = decision

    negative_tests: dict[str, Any] = {}

    wrong_env = dict(base_env)
    wrong_env.pop("TOKENOSKOBI_A23_GUARDED_PRODUCTION", None)
    negative_tests["missing_required_environment"] = evaluate_runtime_stage(
        "LEDGER_RECOVERY",
        root=root,
        service_name=SERVICE,
        runner_path=RUNNER,
        environ=wrong_env,
    )

    negative_tests["wrong_service_identity"] = evaluate_runtime_stage(
        "SOURCE_CONTRACT_RESOLUTION",
        root=root,
        service_name="unauthorized.service",
        runner_path=RUNNER,
        environ=base_env,
    )

    negative_tests["unknown_stage"] = evaluate_runtime_stage(
        "UNKNOWN_STAGE",
        root=root,
        service_name=SERVICE,
        runner_path=RUNNER,
        environ=base_env,
    )

    live_runtime = json.loads(json.dumps(runtime))
    live_runtime["canonical_runtime_pointer"]["live_source_fetch_authorized"] = True
    negative_tests["live_fetch_authority_expansion"] = evaluate_runtime_stage(
        "SOURCE_CONTRACT_RESOLUTION",
        root=root,
        service_name=SERVICE,
        runner_path=RUNNER,
        environ=base_env,
        runtime_override=live_runtime,
    )

    for name, decision in negative_tests.items():
        if decision.get("decision") != "DENY" or decision.get("ok") is not False:
            raise RuntimeError(f"NEGATIVE_TEST_NOT_DENIED:{name}")

    wrapper_text = wrapper_path.read_text(encoding="utf-8")
    for stage in (
        "SOURCE_CONTRACT_RESOLUTION",
        "LEDGER_RECOVERY",
        "DERIVED_DB_WRITE",
        "HOT_PUBLISH",
    ):
        if f'run_policy_authority_gate("{stage}")' not in wrapper_text:
            raise RuntimeError(f"WRAPPER_GATE_NOT_REACHABLE:{stage}")

    db_hash_before = sha256(db_path)
    with tempfile.TemporaryDirectory(prefix="tokenoskobi_policy_gate_") as temp_dir:
        temp = Path(temp_dir)
        temp_db = temp / "runtime.sqlite"
        shutil.copy2(db_path, temp_db)
        env = dict(base_env)
        env.update(
            {
                "TOKENOSKOBI_DB_PATH": str(temp_db),
                "TOKENOSKOBI_LEDGER_WRITER_ENABLED": "0",
                "TOKENOSKOBI_RUNNER_LOCK_ENABLED": "1",
                "TOKENOSKOBI_RUNNER_LOCK_PATH": str(temp / "runner.lock"),
                "TOKENOSKOBI_A10_ORDER_LOG": str(temp / "order.log"),
                "TOKENOSKOBI_HOT_OUTPUT_PATH": str(temp / "hot.json"),
                "TOKENOSKOBI_LEDGER_RECOVERY_STATE_PATH": str(temp / "recovery.json"),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        wrapper_result = run(
            [sys.executable, str(wrapper_path)],
            cwd=root,
            env=env,
        )
        if wrapper_result.returncode != 0:
            raise RuntimeError(
                "TEMP_WRAPPER_FAILED:"
                + str(wrapper_result.returncode)
                + ":"
                + wrapper_result.stderr[-1000:]
            )
        if "RUNTIME_POLICY_AUTHORITY_GATE" not in wrapper_result.stdout:
            raise RuntimeError("TEMP_WRAPPER_POLICY_GATE_NOT_OBSERVED")
        if "SUCCESS_NOOP_FAIL_CLOSED" not in wrapper_result.stdout:
            raise RuntimeError("TEMP_WRAPPER_NOOP_NOT_OBSERVED")
        temp_db_hash_after = sha256(temp_db)

    db_hash_after = sha256(db_path)
    if db_hash_before != db_hash_after:
        raise RuntimeError("PRODUCTION_DB_HASH_CHANGED")

    now = datetime.now(timezone.utc).isoformat()
    artifact = {
        "schema": "general_runtime_hardening_d_policy_authority_reachability_v1",
        "timestamp_utc": now,
        "work_unit": WORK,
        "status": "CLOSED_VERIFIED",
        "result": RESULT,
        "policy_engine": "project_policy_registry_v1",
        "authority_engine": "authority_state_v1",
        "runtime_gate": "core/runtime_policy_authority_gate.py",
        "grant_registry": "config/runtime_stage_grants_v1.json",
        "wrapper": RUNNER,
        "systemd_truth": systemd,
        "stage_decisions": stage_decisions,
        "negative_tests": negative_tests,
        "temp_wrapper": {
            "returncode": wrapper_result.returncode,
            "stdout_tail": wrapper_result.stdout[-4000:],
            "stderr_tail": wrapper_result.stderr[-2000:],
            "temp_db_hash_after": temp_db_hash_after,
            "success_noop_fail_closed": True,
        },
        "production_db_sha256_before": db_hash_before,
        "production_db_sha256_after": db_hash_after,
        "production_db_mutation": False,
        "service_execution": False,
        "service_timer_change": False,
        "live_fetch_change": False,
        "broad_authority_expansion": False,
        "era57_opened": False,
        "next_safe_step": NEXT,
    }

    print("POLICY_AUTHORITY_REACHABILITY=OK")
    print("STAGE_ALLOW_COUNT=4")
    print("NEGATIVE_DENY_COUNT=4")
    print("TEMP_WRAPPER_SUCCESS_NOOP_FAIL_CLOSED=true")
    print("PRODUCTION_DB_MUTATION=false")
    print("LIVE_SERVICE_EXECUTION=false")

    if not args.apply:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    update_config_metadata(root)
    save(artifact_path, artifact)

    runtime = load(runtime_path)
    pointer = runtime["canonical_runtime_pointer"]
    hardening = pointer.setdefault("general_runtime_hardening", {})
    substeps = hardening.setdefault("substeps", {})
    substeps["D_POLICY_AUTHORITY_REACHABILITY"] = "CLOSED_VERIFIED"
    substeps["E_FINAL_STRESS_GATE"] = "READY"
    hardening.update(
        {
            "policy_authority_reachable": True,
            "runtime_gate": "core/runtime_policy_authority_gate.py",
            "runtime_grant_registry": "config/runtime_stage_grants_v1.json",
            "broad_authority_expansion": False,
            "next_safe_step": NEXT,
            "updated_at_utc": now,
        }
    )
    pointer.update(
        {
            "current_stage": "GENERAL_RUNTIME_HARDENING_D_POLICY_AUTHORITY_REACHABILITY_CLOSED",
            "last_completed": WORK,
            "last_result": RESULT,
            "last_artifact": ARTIFACT_REL,
            "policy_authority_reachable": True,
            "runtime_policy_engine": "core/policy.py",
            "runtime_authority_engine": "core/authority.py",
            "runtime_policy_authority_gate": "core/runtime_policy_authority_gate.py",
            "runtime_stage_grant_registry": "config/runtime_stage_grants_v1.json",
            "runtime_stage_grant_scope": "NEWS_RADAR_EXISTING_AUTHORITY_ONLY",
            "broad_authority_expansion": False,
            "era57_opened": False,
            "live_source_fetch_authorized": False,
            "production_mutation": False,
            "next_safe_step": NEXT,
            "updated_at_utc": now,
        }
    )
    runtime.update(
        {
            "last_completed": WORK,
            "last_result": RESULT,
            "last_artifact": ARTIFACT_REL,
            "next_safe_step": NEXT,
            "updated_at": now,
            "updated_at_utc": now,
            "work_unit": WORK,
        }
    )
    runtime["current_problem"] = {
        "code": "FINAL_STRESS_GATE_REQUIRED",
        "severity": "P1",
        "evidence": ARTIFACT_REL,
    }
    runtime["current_state"] = {
        "project_status": "ERA56_CLOSED_PRE_ERA57_GENERAL_RUNTIME_HARDENING",
        "runtime_status": "POLICY_AUTHORITY_REACHABLE_FINAL_STRESS_READY",
        "mode": "PRE_ERA57_GENERAL_RUNTIME_HARDENING",
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
        "substep": "D_POLICY_AUTHORITY_REACHABILITY",
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
                "policy_authority_reachable": True,
                "broad_authority_expansion": False,
                "production_mutation": False,
                "era57_opened": False,
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
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
POLICY_AUTHORITY_REACHABLE=true
BROAD_AUTHORITY_EXPANSION=false
LIVE_FETCH_AUTHORIZED=false
ERA57_OPENED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}""",
    )
    master = section(
        master,
        "## 10 NEXT SAFE STEP",
        f"""```text
NEXT_SAFE_STEP={NEXT}
```

Run the reusable isolated stress harness against disposable copies and
close the final pre-ERA57 gate. Production chaos, live source activation,
service mutation and uncontrolled writes remain forbidden.""",
    )
    master_path.write_text(master.rstrip() + "\n", encoding="utf-8")

    handoff_path = root / "07_PROJECT_HANDOFF.md"
    handoff = handoff_path.read_text(encoding="utf-8")
    handoff = section(
        handoff,
        "## 03 LAST VERIFIED WORK",
        f"""LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
POLICY_AUTHORITY_REACHABLE=true
RUNTIME_GATE=core/runtime_policy_authority_gate.py
BROAD_AUTHORITY_EXPANSION=false
ERA57_OPENED=false
PRODUCTION_MUTATION=false""",
    )
    handoff = section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Run only the reusable isolated stress harness on disposable copies.
- Verify policy/authority positive and negative paths under stress.
- Do not run production chaos tests.
- Do not enable live source fetch.
- Do not broaden runtime stage grants.
- ERA57 remains closed.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff_path.write_text(handoff.rstrip() + "\n", encoding="utf-8")

    roadmap_path = root / "03_ROADMAP.md"
    roadmap = roadmap_path.read_text(encoding="utf-8")
    roadmap = roadmap.replace(
        "- Policy/authority reachability proof follows runner review.\n",
        "- Policy/authority reachability is closed with scoped fail-closed enforcement.\n",
    )
    roadmap = roadmap.replace(
        "- Final isolated stress verification remains the ERA57 gate.\n",
        "- Final isolated stress verification is the remaining ERA57 gate.\n",
    )
    roadmap = roadmap.replace(
        "- Next safe step: `GENERAL_RUNTIME_HARDENING_D_POLICY_AUTHORITY_REACHABILITY`.",
        f"- Next safe step: `{NEXT}`.",
    )
    roadmap_path.write_text(roadmap.rstrip() + "\n", encoding="utf-8")

    report_path = root / "reports" / "LATEST_TK_AI_HANDOFF.md"
    report_path.write_text(
        f"""# LATEST TK AI HANDOFF

CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_MAIN_LINE=GENERAL_RUNTIME_HARDENING
CURRENT_STAGE=GENERAL_RUNTIME_HARDENING_D_POLICY_AUTHORITY_REACHABILITY_CLOSED
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
POLICY_AUTHORITY_REACHABLE=true
RUNTIME_GATE=core/runtime_policy_authority_gate.py
RUNTIME_GRANTS=config/runtime_stage_grants_v1.json
BROAD_AUTHORITY_EXPANSION=false
LIVE_FETCH_AUTHORIZED=false
ERA57_OPENED=false
PRODUCTION_MUTATION=false
NEXT_SAFE_STEP={NEXT}
""",
        encoding="utf-8",
    )

    print("GENERAL_RUNTIME_HARDENING_D=SUCCESS")
    print(f"NEXT_SAFE_STEP={NEXT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
