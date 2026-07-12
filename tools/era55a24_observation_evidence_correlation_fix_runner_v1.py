#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
TARGET = ROOT / "tools/era55a24_p0_post_activation_observation_and_p0_f1_closure_decision_v1.py"
SAFETY_FIX = ROOT / "tools/era55a24_execution_safety_fix_runner_v1.py"


def load_safety_transform():
    spec = importlib.util.spec_from_file_location("era55a24_safety_fix", SAFETY_FIX)
    if spec is None or spec.loader is None:
        raise RuntimeError("A24_FIX2_SAFETY_FIX_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.transform


def load_transformed_namespace() -> dict[str, Any]:
    transform = load_safety_transform()
    source = TARGET.read_text(encoding="utf-8")
    transformed = transform(source)
    compile(transformed, str(TARGET), "exec")
    namespace: dict[str, Any] = {
        "__name__": "era55a24_transformed_runtime",
        "__file__": str(TARGET),
        "__package__": None,
    }
    exec(compile(transformed, str(TARGET), "exec"), namespace)
    return namespace


def install_observation_fix(namespace: dict[str, Any]) -> None:
    def corrected_observation_snapshot(a23: dict[str, Any]) -> dict[str, Any]:
        order_log: Path = namespace["ORDER_LOG"]
        if not order_log.exists():
            raise RuntimeError("A24_ORDER_LOG_MISSING")

        lines = order_log.read_text(encoding="utf-8").splitlines()
        cycles = namespace["split_order_cycles"](lines)
        if not cycles:
            raise RuntimeError("A24_NO_ORDER_CYCLES")
        if cycles[0] != a23["runner_order"]:
            raise RuntimeError("A24_CONTROLLED_CYCLE_ORDER_DRIFT")

        validated = [namespace["validate_order_cycle"](cycle) for cycle in cycles]
        natural_order = validated[1:]
        if not natural_order:
            raise RuntimeError("A24_NO_NATURAL_ORDER_CYCLE")

        apply_finished = datetime.fromisoformat(str(a23["apply_finished_at_utc"]))
        since = apply_finished.astimezone(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S.%f UTC"
        )
        completed = namespace["run"](
            [
                "journalctl",
                "-u",
                namespace["SERVICE"],
                "--since",
                since,
                "--no-pager",
                "-o",
                "json",
            ],
            check=False,
            timeout=60,
        )

        messages: list[str] = []
        finish_times: list[str] = []
        for raw in completed.stdout.splitlines():
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            message = str(entry.get("MESSAGE", ""))
            messages.append(message)
            if message.startswith(
                "Finished tokenoskobi-news-radar-refresh.service"
            ):
                micros = int(entry.get("__REALTIME_TIMESTAMP", "0"))
                if micros <= 0:
                    raise RuntimeError("A24_SERVICE_FINISH_TIMESTAMP_MISSING")
                finish_times.append(
                    datetime.fromtimestamp(
                        micros / 1_000_000,
                        tz=timezone.utc,
                    ).isoformat()
                )

        failure_needles = (
            "A23_GUARDED_PRODUCTION_CYCLE_FAILED",
            "A23_GUARDED_HOT_END:1",
            "HOT_END:1",
            "Failed with result 'exit-code'",
            "Failed to start tokenoskobi-news-radar-refresh.service",
            "status=1/FAILURE",
            "Traceback (most recent call last)",
        )
        journal_text = "\n".join(messages)
        failures = [needle for needle in failure_needles if needle in journal_text]
        if failures:
            raise RuntimeError(
                "A24_POST_ACTIVATION_FAILURE_MARKERS:" + ",".join(failures)
            )

        if len(finish_times) != len(natural_order):
            raise RuntimeError(
                "A24_ORDER_SERVICE_SUCCESS_COUNT_MISMATCH:"
                + str(len(natural_order))
                + ":"
                + str(len(finish_times))
            )

        inventory = namespace["database_inventory"](namespace["DB"])
        original = a23["production_after"]
        original_map = namespace["batch_map"](original)
        current_map = namespace["batch_map"](inventory)

        for uid, batch in original_map.items():
            if current_map.get(uid) != batch:
                raise RuntimeError("A24_ORIGINAL_BATCH_MUTATED:" + uid)

        new_batches = sorted(
            (
                batch
                for uid, batch in current_map.items()
                if uid not in original_map
            ),
            key=lambda batch: int(batch["batch_sequence"]),
        )
        committed_markers = sum(
            1 for cycle in natural_order if cycle["writer_status"] == "COMMITTED"
        )
        if committed_markers != len(new_batches):
            raise RuntimeError(
                "A24_COMMITTED_MARKER_NEW_BATCH_COUNT_MISMATCH:"
                + str(committed_markers)
                + ":"
                + str(len(new_batches))
            )

        initial_batch = max(
            original["batches"],
            key=lambda batch: int(batch["batch_sequence"]),
        )
        current_uid = str(initial_batch["batch_uid"])
        new_index = 0
        correlated: list[dict[str, Any]] = []

        for index, order_cycle in enumerate(natural_order):
            writer_status = str(order_cycle["writer_status"])
            if writer_status == "COMMITTED":
                if new_index >= len(new_batches):
                    raise RuntimeError("A24_COMMITTED_BATCH_CORRELATION_OVERFLOW")
                current_uid = str(new_batches[new_index]["batch_uid"])
                new_index += 1
            elif writer_status != "IDEMPOTENT_REPLAY_NOOP":
                raise RuntimeError("A24_UNEXPECTED_WRITER_STATUS:" + writer_status)

            batch = current_map.get(current_uid)
            if batch is None:
                raise RuntimeError("A24_CORRELATED_BATCH_MISSING:" + current_uid)

            correlated.append(
                {
                    "writer_status": writer_status,
                    "batch_uid": current_uid,
                    "source_count": int(batch["source_candidate_count"]),
                    "timestamp_utc": finish_times[index],
                    "payload": {
                        "evidence_source": "ORDER_LOG_SERVICE_JOURNAL_DATABASE_CORRELATION",
                    },
                }
            )

        if new_index != len(new_batches):
            raise RuntimeError("A24_NEW_BATCH_CORRELATION_INCOMPLETE")

        latest = namespace["validate_cycle_payload"](
            namespace["load"](namespace["RESULT_PATH"])
        )
        latest_correlated = correlated[-1]
        if latest["writer_status"] != latest_correlated["writer_status"]:
            raise RuntimeError("A24_LATEST_WRITER_STATUS_CORRELATION_FAILED")
        if latest["batch_uid"] != latest_correlated["batch_uid"]:
            raise RuntimeError("A24_LATEST_BATCH_UID_CORRELATION_FAILED")
        if latest["source_count"] != latest_correlated["source_count"]:
            raise RuntimeError("A24_LATEST_SOURCE_COUNT_CORRELATION_FAILED")

        latest_correlated["timestamp_utc"] = latest["timestamp_utc"]
        latest_correlated["payload"] = latest["payload"]

        return {
            "order_log_lines": lines,
            "all_order_cycles": validated,
            "natural_order_cycles": natural_order,
            "journal": {
                "rc": completed.returncode,
                "since": since,
                "stdout": journal_text,
                "stderr": completed.stderr,
                "cycle_payloads": [],
                "failure_markers": failures,
                "service_finished_count": len(finish_times),
                "evidence_mode": "ORDER_LOG_SERVICE_JOURNAL_DATABASE_CORRELATION",
            },
            "natural_payloads": correlated,
        }

    namespace["observation_snapshot"] = corrected_observation_snapshot


def main() -> int:
    namespace = load_transformed_namespace()
    install_observation_fix(namespace)
    return int(namespace["main"]())


if __name__ == "__main__":
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    raise SystemExit(main())
