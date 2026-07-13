#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True

from news_ledger_recovery_guard_v1 import (
    recover_committed_batch,
    single_instance_lock,
)

DEFAULT_ROOT = Path("/root/tokenoskobi_clean_v1")
PYTHON_BIN = os.environ.get("TOKENOSKOBI_PYTHON_BIN", "/usr/bin/python3")
ROOT = Path(os.environ.get("TOKENOSKOBI_ROOT", str(DEFAULT_ROOT)))
SOURCE_CONTRACT_RUNNER = Path(
    os.environ.get(
        "TOKENOSKOBI_NEWS_SOURCE_CONTRACT_RUNNER_PATH",
        str(ROOT / "tools" / "news_source_runtime_contract_v1.py"),
    )
)
SOURCE_CONTRACT = Path(
    os.environ.get(
        "TOKENOSKOBI_NEWS_SOURCE_CONTRACT_PATH",
        str(ROOT / "config" / "news_runtime_source_contract_v1.json"),
    )
)
HELPER = Path(
    os.environ.get(
        "TOKENOSKOBI_NEWS_DERIVED_HELPER_PATH",
        str(ROOT / "tools" / "news_derived_layer_refresher_v1.py"),
    )
)
HOT = Path(
    os.environ.get(
        "TOKENOSKOBI_NEWS_HOT_PATH",
        str(
            ROOT
            / "tools"
            / "post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.py"
        ),
    )
)
DB = Path(
    os.environ.get(
        "TOKENOSKOBI_DB_PATH",
        str(ROOT / "data" / "tokenoskobi_clean_v1.sqlite"),
    )
)
HOT_OUTPUT = Path(
    os.environ.get(
        "TOKENOSKOBI_HOT_OUTPUT_PATH",
        str(ROOT / "runtime" / "state" / "hot_intelligence_ingress_gateway_v1.json"),
    )
)
RECOVERY_STATE = Path(
    os.environ.get(
        "TOKENOSKOBI_LEDGER_RECOVERY_STATE_PATH",
        str(ROOT / "runtime" / "state" / "news_ledger_recovery_state_v1.json"),
    )
)
RECOVERY_CONTRACT_SEED = Path(
    os.environ.get(
        "TOKENOSKOBI_RECOVERY_CONTRACT_SEED_PATH",
        str(HOT_OUTPUT),
    )
)
RUNNER_LOCK = Path(
    os.environ.get(
        "TOKENOSKOBI_RUNNER_LOCK_PATH",
        str(ROOT / "runtime" / "state" / "news_radar_refresh_runner_v1.lock"),
    )
)
ORDER_LOG = os.environ.get("TOKENOSKOBI_A10_ORDER_LOG")
STAGE_TIMEOUT = int(os.environ.get("TOKENOSKOBI_STAGE_TIMEOUT_SECONDS", "120"))
NO_AUTHORIZED_SOURCES = 78
ADAPTER_REQUIRED = 79


def env_true(name: str) -> bool:
    return os.environ.get(name, "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def append_order(marker: str) -> None:
    if not ORDER_LOG:
        return
    path = Path(ORDER_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(marker + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def run_stage(marker: str, argv: list[str]) -> int:
    target = Path(argv[1]) if len(argv) > 1 else None
    if target is not None and not target.is_file():
        print(f"[{marker}_TARGET_MISSING] path={target}", flush=True)
        append_order(f"{marker}_END:66")
        return 66

    append_order(f"{marker}_START")
    try:
        result = subprocess.run(
            argv,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            timeout=STAGE_TIMEOUT,
        ).returncode
    except subprocess.TimeoutExpired:
        print(
            f"[{marker}_TIMEOUT_FAIL_CLOSED] timeout_seconds={STAGE_TIMEOUT}",
            flush=True,
        )
        result = 124
    append_order(f"{marker}_END:{result}")
    return result


def run_hot() -> int:
    return run_stage(
        "HOT",
        [PYTHON_BIN, str(HOT), "--runtime-refresh"],
    )


def run_recovery() -> dict:
    result = recover_committed_batch(
        DB,
        HOT_OUTPUT,
        RECOVERY_STATE,
        contract_seed_path=(
            RECOVERY_CONTRACT_SEED
            if RECOVERY_CONTRACT_SEED.exists()
            else None
        ),
        max_attempts=int(
            os.environ.get(
                "TOKENOSKOBI_LEDGER_RECOVERY_MAX_ATTEMPTS",
                "3",
            )
        ),
    )
    append_order("RECOVERY_DONE:" + str(result.get("status")))
    print(
        "[LEDGER_RECOVERY_RESULT] "
        + json.dumps(result, ensure_ascii=False, sort_keys=True),
        flush=True,
    )
    return result


def run_source_contract() -> int:
    if not SOURCE_CONTRACT.is_file():
        print(
            f"[SOURCE_CONTRACT_MISSING] path={SOURCE_CONTRACT}",
            flush=True,
        )
        return 66
    return run_stage(
        "SOURCE_CONTRACT",
        [
            PYTHON_BIN,
            str(SOURCE_CONTRACT_RUNNER),
            "--db-path",
            str(DB),
            "--contract-path",
            str(SOURCE_CONTRACT),
        ],
    )


def _run_pipeline() -> int:
    writer_enabled = env_true("TOKENOSKOBI_LEDGER_WRITER_ENABLED")
    hot_blocked = False

    if writer_enabled:
        recovery = run_recovery()
        recovery_status = str(recovery.get("status") or "UNKNOWN")

        if recovery_status in {"RETRY_PENDING", "ERROR"}:
            print(
                "[LEDGER_RECOVERY_FAIL_CLOSED] "
                f"status={recovery_status}",
                flush=True,
            )
            return 75

        if recovery_status == "QUARANTINED":
            hot_blocked = True
            print(
                "[LEDGER_RECOVERY_QUARANTINE_ACTIVE] "
                "source_and_derived_continue hot_publish_blocked=true",
                flush=True,
            )

    if "--recovery-only" in sys.argv[1:]:
        return 0

    if "--hot-only" in sys.argv[1:]:
        if hot_blocked:
            print("[HOT_PUBLISH_SKIPPED_DUE_TO_QUARANTINE]", flush=True)
            return 0
        return run_hot()

    source_result = run_source_contract()

    if source_result == NO_AUTHORIZED_SOURCES:
        print(
            "[SOURCE_CONTRACT_NO_AUTHORIZED_SOURCES] "
            "status=SUCCESS_NOOP_FAIL_CLOSED "
            "derived_skipped=true hot_skipped=true",
            flush=True,
        )
        return 0

    if source_result == ADAPTER_REQUIRED:
        print(
            "[SOURCE_ADAPTER_REQUIRED_FAIL_CLOSED]",
            flush=True,
        )
        return ADAPTER_REQUIRED

    if source_result != 0:
        return source_result

    derived = run_stage(
        "DERIVED",
        [
            PYTHON_BIN,
            str(HELPER),
            "--db-path",
            str(DB),
            "--write",
            "--stage",
            "NEWS_SYSTEMD_TIMER_DERIVED_REFRESH",
        ],
    )
    if derived != 0:
        return derived

    if hot_blocked:
        print("[HOT_PUBLISH_SKIPPED_DUE_TO_QUARANTINE]", flush=True)
        return 0

    return run_hot()


def main() -> int:
    if env_true("TOKENOSKOBI_RUNNER_LOCK_ENABLED"):
        with single_instance_lock(RUNNER_LOCK) as lock_handle:
            if lock_handle is None:
                print(
                    "[RUNNER_ALREADY_ACTIVE] "
                    f"lock_path={RUNNER_LOCK}",
                    flush=True,
                )
                return 0
            append_order("LOCK_ACQUIRED")
            return _run_pipeline()

    return _run_pipeline()


if __name__ == "__main__":
    raise SystemExit(main())
