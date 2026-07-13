#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

WORK = "GENERAL_RUNTIME_HARDENING_C_GENERAL_RUNNER_CONTRACT"
NEXT = "GENERAL_RUNTIME_HARDENING_D_POLICY_AUTHORITY_REACHABILITY"
RESULT = "OK_GENERAL_RUNNER_CONTRACT_FAIL_CLOSED"
ARTIFACT_REL = "data/control/general_runtime_hardening_c_general_runner_contract_v1.json"
SERVICE = "tokenoskobi-news-radar-refresh.service"
TIMER = "tokenoskobi-news-radar-refresh.timer"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(argv: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def systemd_properties(name: str) -> dict[str, str]:
    result = subprocess.run(
        [
            "systemctl",
            "show",
            name,
            "--no-pager",
            "-p",
            "ActiveState",
            "-p",
            "SubState",
            "-p",
            "UnitFileState",
            "-p",
            "FragmentPath",
            "-p",
            "DropInPaths",
            "-p",
            "ExecStart",
            "-p",
            "Environment",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"SYSTEMD_SHOW_FAILED:{name}:{result.stderr.strip()}")
    return {
        line.split("=", 1)[0]: line.split("=", 1)[1]
        for line in result.stdout.splitlines()
        if "=" in line
    }


def replace_section(text: str, heading: str, body: str) -> str:
    start = text.find(heading)
    if start < 0:
        return text.rstrip() + "\n\n" + heading + "\n\n" + body.rstrip() + "\n"
    end = text.find("\n## ", start + len(heading))
    if end < 0:
        end = len(text)
    return text[:start] + heading + "\n\n" + body.rstrip() + "\n" + text[end:]


def validate(root: Path) -> dict:
    runtime_path = root / "PROJECT_RUNTIME.json"
    runtime = load(runtime_path)
    pointer = runtime["canonical_runtime_pointer"]

    if pointer.get("next_safe_step") != WORK:
        raise RuntimeError(f"UNEXPECTED_NEXT_SAFE_STEP:{pointer.get('next_safe_step')}")
    if pointer.get("era57_opened") is not False:
        raise RuntimeError("ERA57_MUST_REMAIN_CLOSED")
    if pointer.get("live_source_fetch_authorized") is not False:
        raise RuntimeError("LIVE_FETCH_MUST_REMAIN_DISABLED")
    if pointer.get("production_mutation") is not False:
        raise RuntimeError("PRODUCTION_MUTATION_MUST_REMAIN_FALSE")

    wrapper = root / "tools/news_radar_refresh_runner_v1.py"
    selector = root / "tools/news_source_runtime_contract_v1.py"
    contract = root / "config/news_runtime_source_contract_v1.json"
    database = root / "data/tokenoskobi_clean_v1.sqlite"

    for path in (wrapper, selector, contract, database):
        if not path.is_file():
            raise RuntimeError(f"REQUIRED_FILE_MISSING:{path}")

    wrapper_text = wrapper.read_text(encoding="utf-8")
    forbidden = (
        "PRE_DERIVED_BINDING",
        "TOKENOSKOBI_NEWS_ORIGINAL_PATH",
        "ORIGINAL_NEWS",
    )
    hits = [token for token in forbidden if token in wrapper_text]
    if hits:
        raise RuntimeError("LEGACY_RUNNER_REFERENCE_PRESENT:" + ",".join(hits))
    if "news_source_runtime_contract_v1.py" not in wrapper_text:
        raise RuntimeError("GENERAL_SOURCE_CONTRACT_NOT_BOUND")
    if "SUCCESS_NOOP_FAIL_CLOSED" not in wrapper_text:
        raise RuntimeError("EMPTY_SELECTION_NOOP_NOT_BOUND")
    if "TimeoutExpired" not in wrapper_text:
        raise RuntimeError("SUBPROCESS_TIMEOUT_NOT_ENFORCED")

    service = systemd_properties(SERVICE)
    timer = systemd_properties(TIMER)
    exec_start = service.get("ExecStart", "")
    environment = service.get("Environment", "")
    if str(wrapper) not in exec_start:
        raise RuntimeError("LIVE_SERVICE_NOT_BOUND_TO_WRAPPER")
    if "TOKENOSKOBI_NEWS_ORIGINAL_PATH" in environment:
        raise RuntimeError("LEGACY_ORIGINAL_OVERRIDE_STILL_ACTIVE")
    if timer.get("ActiveState") != "active":
        raise RuntimeError("NEWS_TIMER_NOT_ACTIVE")
    if timer.get("UnitFileState") != "enabled":
        raise RuntimeError("NEWS_TIMER_NOT_ENABLED")

    source_hash_before = sha256(database)

    with tempfile.TemporaryDirectory(prefix="tokenoskobi_runner_contract_") as temp_dir:
        temp = Path(temp_dir)
        temp_db = temp / "runtime.sqlite"
        shutil.copy2(database, temp_db)
        temp_hash_before = sha256(temp_db)

        selector_result = run(
            [
                "/usr/bin/python3",
                str(selector),
                "--db-path",
                str(temp_db),
                "--contract-path",
                str(contract),
            ],
            cwd=root,
        )
        if selector_result.returncode != 78:
            raise RuntimeError(
                "SELECTOR_EXPECTED_78_GOT_"
                + str(selector_result.returncode)
                + ":"
                + selector_result.stdout[-1000:]
                + selector_result.stderr[-1000:]
            )
        selector_payload = json.loads(selector_result.stdout.strip().splitlines()[-1])
        if selector_payload.get("status") != "SUCCESS_NOOP_FAIL_CLOSED":
            raise RuntimeError("SELECTOR_STATUS_MISMATCH")
        if int(selector_payload.get("runtime_eligible_source_count", -1)) != 0:
            raise RuntimeError("SELECTOR_ELIGIBLE_COUNT_NOT_ZERO")
        if selector_payload.get("network_call") is not False:
            raise RuntimeError("SELECTOR_NETWORK_CALL_NOT_FALSE")
        if selector_payload.get("database_write") is not False:
            raise RuntimeError("SELECTOR_DB_WRITE_NOT_FALSE")

        env = dict(os.environ)
        env.update(
            {
                "TOKENOSKOBI_ROOT": str(root),
                "TOKENOSKOBI_DB_PATH": str(temp_db),
                "TOKENOSKOBI_LEDGER_WRITER_ENABLED": "0",
                "TOKENOSKOBI_RUNNER_LOCK_ENABLED": "0",
                "TOKENOSKOBI_A10_ORDER_LOG": "",
                "TOKENOSKOBI_STAGE_TIMEOUT_SECONDS": "30",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        wrapper_result = run(
            ["/usr/bin/python3", str(wrapper)],
            cwd=root,
            env=env,
        )
        if wrapper_result.returncode != 0:
            raise RuntimeError(
                "WRAPPER_EXPECTED_0_GOT_"
                + str(wrapper_result.returncode)
                + ":"
                + wrapper_result.stdout[-1000:]
                + wrapper_result.stderr[-1000:]
            )
        if "SOURCE_CONTRACT_NO_AUTHORIZED_SOURCES" not in wrapper_result.stdout:
            raise RuntimeError("WRAPPER_NOOP_MARKER_MISSING")
        if "derived_skipped=true" not in wrapper_result.stdout:
            raise RuntimeError("DERIVED_SKIP_NOT_PROVEN")
        if "hot_skipped=true" not in wrapper_result.stdout:
            raise RuntimeError("HOT_SKIP_NOT_PROVEN")
        if sha256(temp_db) != temp_hash_before:
            raise RuntimeError("TEMP_DB_MUTATED")

    source_hash_after = sha256(database)
    if source_hash_before != source_hash_after:
        raise RuntimeError("PRODUCTION_DB_MUTATED")

    fragment = Path(service.get("FragmentPath", ""))
    dropin_text = service.get("DropInPaths", "")
    dropin_paths = [Path(item) for item in dropin_text.split() if item.startswith("/")]

    return {
        "schema": "general_runtime_runner_contract_validation_v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "work_unit": WORK,
        "status": "CLOSED_VERIFIED",
        "result": RESULT,
        "wrapper": str(wrapper.relative_to(root)),
        "source_contract_runner": str(selector.relative_to(root)),
        "source_contract": str(contract.relative_to(root)),
        "legacy_reference_count": 0,
        "source_selector_exit_code": 78,
        "source_selector_status": "SUCCESS_NOOP_FAIL_CLOSED",
        "wrapper_exit_code": 0,
        "derived_skipped": True,
        "hot_skipped": True,
        "runtime_eligible_source_count": 0,
        "network_call": False,
        "database_write": False,
        "production_db_sha256_before": source_hash_before,
        "production_db_sha256_after": source_hash_after,
        "production_db_mutation": False,
        "live_service_execution": False,
        "service_timer_change": False,
        "service": {
            "active": service.get("ActiveState"),
            "sub": service.get("SubState"),
            "enabled": service.get("UnitFileState"),
            "exec_start": exec_start,
            "environment": environment,
            "fragment": str(fragment) if fragment else None,
            "fragment_sha256": sha256(fragment) if fragment.is_file() else None,
            "dropins": [
                {
                    "path": str(path),
                    "sha256": sha256(path) if path.is_file() else None,
                }
                for path in dropin_paths
            ],
        },
        "timer": {
            "active": timer.get("ActiveState"),
            "sub": timer.get("SubState"),
            "enabled": timer.get("UnitFileState"),
            "fragment": timer.get("FragmentPath"),
        },
        "classifier_false_negative_corrected": True,
        "era57_opened": False,
        "live_fetch_authorized": False,
        "production_mutation": False,
        "next_safe_step": NEXT,
    }


def apply(root: Path, artifact: dict) -> None:
    now = artifact["timestamp_utc"]
    artifact_path = root / ARTIFACT_REL
    save(artifact_path, artifact)

    runtime_path = root / "PROJECT_RUNTIME.json"
    runtime = load(runtime_path)
    pointer = runtime["canonical_runtime_pointer"]
    hardening = pointer.setdefault("general_runtime_hardening", {})
    substeps = hardening.setdefault("substeps", {})
    substeps["C_GENERAL_RUNNER_CONTRACT"] = "CLOSED_VERIFIED"
    substeps["D_POLICY_AUTHORITY_REACHABILITY"] = "READY"
    hardening["status"] = "OPEN"
    hardening["next_safe_step"] = NEXT
    hardening["updated_at_utc"] = now

    pointer.update(
        {
            "current_stage": "GENERAL_RUNTIME_HARDENING_C_GENERAL_RUNNER_CONTRACT_CLOSED",
            "last_completed": WORK,
            "last_result": RESULT,
            "last_artifact": ARTIFACT_REL,
            "legacy_raw_runner_reference_present": False,
            "general_source_contract_bound": True,
            "empty_source_selection_behavior": "SUCCESS_NOOP_FAIL_CLOSED",
            "runner_subprocess_timeout_enforced": True,
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
        "code": "POLICY_AUTHORITY_REACHABILITY_PROOF_REQUIRED",
        "severity": "P1",
        "evidence": ARTIFACT_REL,
    }
    runtime["current_state"] = {
        "project_status": "ERA56_CLOSED_PRE_ERA57_GENERAL_RUNTIME_HARDENING",
        "runtime_status": "GENERAL_RUNNER_CONTRACT_CLOSED_POLICY_REACHABILITY_READY",
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
        "substep": "C_GENERAL_RUNNER_CONTRACT",
        "status": "CLOSED_VERIFIED",
        "result": RESULT,
        "artifact": ARTIFACT_REL,
        "production_mutation": False,
        "next_step": NEXT,
    }
    save(runtime_path, runtime)

    history_path = root / "PROJECT_HISTORY.json"
    history = load(history_path)
    events = history.setdefault("events", [])
    if not any(isinstance(item, dict) and item.get("event_id") == WORK for item in events):
        events.append(
            {
                "event_id": WORK,
                "timestamp_utc": now,
                "status": "CLOSED_VERIFIED",
                "result": RESULT,
                "artifact": ARTIFACT_REL,
                "legacy_reference_count": 0,
                "production_db_mutation": False,
                "service_timer_change": False,
                "era57_opened": False,
                "next_safe_step": NEXT,
            }
        )
    history["updated_at"] = now
    history["updated_at_utc"] = now
    save(history_path, history)

    master_path = root / "06_PROJECT_MASTER_STATE.md"
    master = master_path.read_text(encoding="utf-8")
    master = replace_section(
        master,
        "## 02 CURRENT MAJOR-LINE POSITION",
        """```text
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
ERA55_STATUS=CLOSED_SEALED
ERA56_STATUS=CLOSED_SEALED
ERA57_OPENED=false
CURRENT_MAIN_LINE=GENERAL_RUNTIME_HARDENING
CURRENT_STAGE=GENERAL_RUNTIME_HARDENING_C_GENERAL_RUNNER_CONTRACT_CLOSED
GENERAL_SOURCE_CONTRACT_BOUND=true
LEGACY_RAW_REFERENCE_PRESENT=false
LIVE_FETCH_AUTHORIZED=false
PRODUCTION_MUTATION=false
```""",
    )
    master = replace_section(
        master,
        "## 03 LAST VERIFIED WORK",
        f"""```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
SOURCE_SELECTION=SUCCESS_NOOP_FAIL_CLOSED
RUNTIME_ELIGIBLE_SOURCE_COUNT=0
PRODUCTION_DB_MUTATION=false
SERVICE_TIMER_CHANGE=false
ERA57_OPENED=false
```

NEXT_SAFE_STEP={NEXT}""",
    )
    master = replace_section(
        master,
        "## 10 NEXT SAFE STEP",
        f"""```text
NEXT_SAFE_STEP={NEXT}
```

Prove that the reachable live wrapper chain enforces the general policy and authority layers. File presence alone is not proof.""",
    )
    master_path.write_text(master.rstrip() + "\n", encoding="utf-8")

    handoff_path = root / "07_PROJECT_HANDOFF.md"
    handoff = handoff_path.read_text(encoding="utf-8")
    handoff = replace_section(
        handoff,
        "## 02 CURRENT CONTINUATION CHECKPOINT",
        f"""PROJECT_STATUS=ERA56_CLOSED_PRE_ERA57_GENERAL_RUNTIME_HARDENING
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_MAIN_LINE=GENERAL_RUNTIME_HARDENING
CURRENT_STAGE=GENERAL_RUNTIME_HARDENING_C_GENERAL_RUNNER_CONTRACT_CLOSED
LAST_COMPLETED={WORK}
GENERAL_SOURCE_CONTRACT_BOUND=true
LEGACY_RAW_REFERENCE_PRESENT=false
LIVE_FETCH_AUTHORIZED=false
ERA57_OPENED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD""",
    )
    handoff = replace_section(
        handoff,
        "## 03 LAST VERIFIED WORK",
        f"""LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
SOURCE_SELECTION=SUCCESS_NOOP_FAIL_CLOSED
PRODUCTION_DB_MUTATION=false
SERVICE_TIMER_CHANGE=false
ERA57_OPENED=false""",
    )
    handoff = replace_section(
        handoff,
        "## 07 ALLOWED NEXT DECISIONS",
        f"""- Trace the live wrapper to policy and authority enforcement.
- Prove reachable enforcement, not file existence.
- Do not enable live source fetch.
- Do not start ERA57.
- Do not change production DB, service, timer or panel.

NEXT_SAFE_STEP={NEXT}""",
    )
    handoff_path.write_text(handoff.rstrip() + "\n", encoding="utf-8")

    for rel in ("03_ROADMAP.md", "reports/LATEST_TK_AI_HANDOFF.md"):
        path = root / rel
        text = path.read_text(encoding="utf-8")
        text = text.replace(WORK, NEXT)
        text = text.replace(
            "GENERAL_RUNTIME_HARDENING_B_ACTIVE_SURFACE_CLASSIFICATION",
            NEXT,
        )
        text = text.replace(
            "GENERAL_RUNTIME_HARDENING_A_CANONICAL_SYNC_CLOSED",
            "GENERAL_RUNTIME_HARDENING_C_GENERAL_RUNNER_CONTRACT_CLOSED",
        )
        path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.getenv("TOKENOSKOBI_ROOT", "/root/tokenoskobi_clean_v1"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    artifact = validate(root)
    if args.apply:
        apply(root, artifact)

    print("GENERAL_RUNTIME_HARDENING_C=SUCCESS")
    print("LEGACY_REFERENCE_COUNT=0")
    print("SOURCE_SELECTION=SUCCESS_NOOP_FAIL_CLOSED")
    print("WRAPPER_EXIT_CODE=0")
    print("PRODUCTION_DB_MUTATION=false")
    print("LIVE_SERVICE_EXECUTION=false")
    print("SERVICE_TIMER_CHANGE=false")
    print("ERA57_OPENED=false")
    print(f"NEXT_SAFE_STEP={NEXT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
