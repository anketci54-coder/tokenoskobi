
#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import os
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
ORIGINAL = Path(
    os.environ.get(
        "TOKENOSKOBI_NEWS_ORIGINAL_PATH",
        str(
            ROOT
            / "tools"
            / "news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py"
        ),
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


def run_hot() -> int:
    append_order("HOT_START")
    result = subprocess.run(
        [PYTHON_BIN, str(HOT), "--runtime-refresh"],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    ).returncode
    append_order(f"HOT_END:{result}")
    return result


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
                "raw_and_derived_continue hot_publish_blocked=true",
                flush=True,
            )

    if "--recovery-only" in sys.argv[1:]:
        return 0

    if "--hot-only" in sys.argv[1:]:
        if hot_blocked:
            print(
                "[HOT_PUBLISH_SKIPPED_DUE_TO_QUARANTINE]",
                flush=True,
            )
            return 0
        return run_hot()

    append_order("RAW_START")
    raw = subprocess.run(
        [PYTHON_BIN, str(ORIGINAL)] + sys.argv[1:],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    append_order(f"RAW_END:{raw.returncode}")
    if raw.returncode != 0:
        return raw.returncode

    append_order("DERIVED_START")
    derived = subprocess.run(
        [
            PYTHON_BIN,
            str(HELPER),
            "--db-path",
            str(DB),
            "--write",
            "--stage",
            "NEWS_SYSTEMD_TIMER_DERIVED_REFRESH",
        ],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    append_order(f"DERIVED_END:{derived.returncode}")
    if derived.returncode != 0:
        return derived.returncode

    if hot_blocked:
        print(
            "[HOT_PUBLISH_SKIPPED_DUE_TO_QUARANTINE]",
            flush=True,
        )
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
