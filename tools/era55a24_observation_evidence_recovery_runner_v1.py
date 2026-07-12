#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
sys.dont_write_bytecode = True
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
TARGET = ROOT / "tools/era55a24_p0_post_activation_observation_and_p0_f1_closure_decision_v1.py"
SAFETY_FIX = ROOT / "tools/era55a24_execution_safety_fix_runner_v1.py"
RESULT_PATH = Path("/run/tokenoskobi/era55a23_guarded_result.json")
ERROR_PATH = Path("/run/tokenoskobi/era55a23_guarded_error.json")
ORDER_LOG = Path("/run/tokenoskobi/era55a23_guarded_order.log")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_transformed_a24():
    safety = load_module("era55a24_safety_fix", SAFETY_FIX)
    source = TARGET.read_text(encoding="utf-8")
    transformed = safety.transform(source)
    code = compile(transformed, str(TARGET), "exec")
    namespace: dict[str, Any] = {
        "__name__": "era55a24_recovered_module",
        "__file__": str(TARGET),
        "__package__": None,
    }
    exec(code, namespace)
    return namespace


def journal_evidence(a24: dict[str, Any], apply_finished: str) -> dict[str, Any]:
    moment = datetime.fromisoformat(apply_finished).astimezone(timezone.utc)
    since = moment.strftime("%Y-%m-%d %H:%M:%S.%f UTC")
    completed = subprocess.run(
        [
            "journalctl",
            "-u",
            a24["SERVICE"],
            "--since",
            since,
            "--no-pager",
            "-o",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    entries: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            entries.append(value)

    finished: list[dict[str, str]] = []
    text_messages: list[str] = []
    for entry in entries:
        message = str(entry.get("MESSAGE", ""))
        text_messages.append(message)
        if message.startswith(
            "Finished tokenoskobi-news-radar-refresh.service"
        ):
            raw = str(entry.get("__REALTIME_TIMESTAMP", "0"))
            timestamp = datetime.fromtimestamp(
                int(raw) / 1_000_000,
                tz=timezone.utc,
            ).isoformat()
            finished.append(
                {
                    "timestamp_utc": timestamp,
                    "message": message,
                    "invocation_id": str(entry.get("_SYSTEMD_INVOCATION_ID", "")),
                }
            )

    joined = "\n".join(text_messages)
    failure_needles = (
        "Failed with result 'exit-code'",
        "Failed to start tokenoskobi-news-radar-refresh.service",
        "status=1/FAILURE",
        "status=2/INVALIDARGUMENT",
        "Traceback (most recent call last)",
    )
    failures = [needle for needle in failure_needles if needle in joined]
    return {
        "rc": completed.returncode,
        "since": since,
        "stderr": completed.stderr,
        "finished_events": finished,
        "service_finished_count": len(finished),
        "failure_markers": failures,
    }


def corrected_snapshot(a24: dict[str, Any], a23: dict[str, Any]) -> dict[str, Any]:
    if not ORDER_LOG.exists():
        raise RuntimeError("A24_ORDER_LOG_MISSING")
    lines = ORDER_LOG.read_text(encoding="utf-8").splitlines()
    cycles = a24["split_order_cycles"](lines)
    if not cycles:
        raise RuntimeError("A24_NO_ORDER_CYCLES")
    if cycles[0] != a23["runner_order"]:
        raise RuntimeError("A24_CONTROLLED_CYCLE_ORDER_DRIFT")

    validated = [a24["validate_order_cycle"](cycle) for cycle in cycles]
    natural_order = validated[1:]
    if not natural_order:
        raise RuntimeError("A24_NO_NATURAL_ORDER_CYCLE")

    journal = journal_evidence(a24, str(a23["apply_finished_at_utc"]))
    if journal["failure_markers"]:
        raise RuntimeError(
            "A24_POST_ACTIVATION_FAILURE_MARKERS:"
            + ",".join(journal["failure_markers"])
        )
    if journal["service_finished_count"] != len(natural_order):
        raise RuntimeError(
            "A24_ORDER_JOURNAL_CYCLE_COUNT_MISMATCH:"
            + str(len(natural_order))
            + ":"
            + str(journal["service_finished_count"])
        )

    inventory = a24["database_inventory"](a24["DB"])
    original = a23["production_after"]
    original_map = a24["batch_map"](original)
    current_map = a24["batch_map"](inventory)
    for uid, batch in original_map.items():
        if current_map.get(uid) != batch:
            raise RuntimeError("A24_ORIGINAL_BATCH_MUTATED:" + uid)

    new_batches = [
        batch
        for batch in inventory["batches"]
        if batch["batch_uid"] not in original_map
    ]
    committed_order_count = sum(
        1 for cycle in natural_order if cycle["writer_status"] == "COMMITTED"
    )
    if committed_order_count != len(new_batches):
        raise RuntimeError(
            "A24_COMMITTED_MARKER_DATABASE_DELTA_MISMATCH:"
            + str(committed_order_count)
            + ":"
            + str(len(new_batches))
        )

    current_uid = str(a23["controlled_cycle"]["actual_batch_uid"])
    current_batch = current_map.get(current_uid)
    if current_batch is None:
        raise RuntimeError("A24_A23_ACTIVE_BATCH_MISSING")
    current_source_count = int(current_batch["source_candidate_count"])
    new_index = 0
    payloads: list[dict[str, Any]] = []

    latest_result = a24["load"](RESULT_PATH)
    latest_validated = a24["validate_cycle_payload"](latest_result)

    for index, cycle in enumerate(natural_order):
        status = cycle["writer_status"]
        if status == "COMMITTED":
            batch = new_batches[new_index]
            new_index += 1
            current_uid = str(batch["batch_uid"])
            current_source_count = int(batch["source_candidate_count"])
        elif status != "IDEMPOTENT_REPLAY_NOOP":
            raise RuntimeError("A24_UNSUPPORTED_ORDER_STATUS:" + status)

        timestamp = journal["finished_events"][index]["timestamp_utc"]
        item = {
            "writer_status": status,
            "batch_uid": current_uid,
            "source_count": current_source_count,
            "timestamp_utc": timestamp,
            "payload": {
                "evidence_mode": "ORDER_LOG_DB_JOURNAL_BINDING",
                "writer_status": status,
                "actual_batch_uid": current_uid,
                "source_candidate_count": current_source_count,
                "timestamp_utc": timestamp,
            },
        }
        payloads.append(item)

    final = payloads[-1]
    if final["writer_status"] != latest_validated["writer_status"]:
        raise RuntimeError("A24_LATEST_RESULT_ORDER_STATUS_MISMATCH")
    if final["batch_uid"] != latest_validated["batch_uid"]:
        raise RuntimeError("A24_LATEST_RESULT_BATCH_UID_MISMATCH")
    if final["source_count"] != latest_validated["source_count"]:
        raise RuntimeError("A24_LATEST_RESULT_SOURCE_COUNT_MISMATCH")
    final.update(latest_validated)

    if ERROR_PATH.exists():
        error = a24["load"](ERROR_PATH)
        if error.get("status") == "A23_GUARDED_PRODUCTION_CYCLE_FAILED":
            raise RuntimeError("A24_ACTIVE_FAILURE_STATE_PRESENT")

    return {
        "order_log_lines": lines,
        "all_order_cycles": validated,
        "natural_order_cycles": natural_order,
        "journal": journal,
        "natural_payloads": payloads,
    }


def main() -> int:
    a24 = load_transformed_a24()
    original_snapshot = a24["observation_snapshot"]

    def observation_snapshot(a23: dict[str, Any]) -> dict[str, Any]:
        return corrected_snapshot(a24, a23)

    a24["observation_snapshot"] = observation_snapshot
    try:
        return int(a24["main"]())
    finally:
        a24["observation_snapshot"] = original_snapshot


if __name__ == "__main__":
    raise SystemExit(main())
