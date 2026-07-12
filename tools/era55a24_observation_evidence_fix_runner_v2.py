#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
sys.dont_write_bytecode = True
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
TARGET = ROOT / "tools/era55a24_p0_post_activation_observation_and_p0_f1_closure_decision_v1.py"
SAFETY_FIX = ROOT / "tools/era55a24_execution_safety_fix_runner_v1.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def utc_iso(value: str) -> str:
    return datetime.fromisoformat(value).astimezone(timezone.utc).isoformat()


def main() -> int:
    safety = load_module("a24_execution_safety_fix", SAFETY_FIX)
    source = TARGET.read_text(encoding="utf-8")
    transformed = safety.transform(source)
    compile(transformed, str(Path(__file__).resolve()), "exec")

    namespace: dict[str, Any] = {
        "__name__": "era55a24_runtime_module",
        "__file__": str(Path(__file__).resolve()),
        "__package__": None,
    }
    exec(compile(transformed, str(Path(__file__).resolve()), "exec"), namespace)

    def current_and_new_batches(a23: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        inventory = namespace["database_inventory"](namespace["DB"])
        original_map = namespace["batch_map"](a23["production_after"])
        current_map = namespace["batch_map"](inventory)
        for uid, batch in original_map.items():
            if current_map.get(uid) != batch:
                raise RuntimeError("A24_ORIGINAL_BATCH_MUTATED:" + uid)
        new_batches = [
            batch
            for batch in inventory["batches"]
            if batch["batch_uid"] not in original_map
        ]
        new_batches.sort(key=lambda item: int(item["batch_sequence"]))
        return inventory, new_batches

    def journal_finish_times(a23: dict[str, Any]) -> list[str]:
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
                "short-iso",
            ],
            check=False,
            timeout=60,
        )
        values: list[str] = []
        needle = "Finished tokenoskobi-news-radar-refresh.service"
        for line in completed.stdout.splitlines():
            if needle not in line:
                continue
            first = line.split(" ", 1)[0].strip()
            try:
                values.append(utc_iso(first))
            except ValueError as exc:
                raise RuntimeError(
                    "A24_JOURNAL_FINISH_TIMESTAMP_PARSE_FAILED:" + first
                ) from exc
        return values

    def patched_observation_snapshot(a23: dict[str, Any]) -> dict[str, Any]:
        order_log: Path = namespace["ORDER_LOG"]
        if not order_log.exists():
            raise RuntimeError("A24_ORDER_LOG_MISSING")
        lines = order_log.read_text(encoding="utf-8").splitlines()
        cycles = namespace["split_order_cycles"](lines)
        if not cycles:
            raise RuntimeError("A24_NO_ORDER_CYCLES")
        if cycles[0] != a23["runner_order"]:
            raise RuntimeError("A24_CONTROLLED_CYCLE_ORDER_DRIFT")

        validated_order = [
            namespace["validate_order_cycle"](cycle)
            for cycle in cycles
        ]
        natural_order = validated_order[1:]
        journal = namespace["journal_since"](
            str(a23["apply_finished_at_utc"])
        )
        if journal["failure_markers"]:
            raise RuntimeError(
                "A24_POST_ACTIVATION_FAILURE_MARKERS:"
                + ",".join(journal["failure_markers"])
            )
        if journal["service_finished_count"] < len(natural_order):
            raise RuntimeError(
                "A24_SERVICE_SUCCESS_COUNT_TOO_LOW:"
                + str(journal["service_finished_count"])
                + ":"
                + str(len(natural_order))
            )

        finish_times = journal_finish_times(a23)
        if len(finish_times) < len(natural_order):
            raise RuntimeError(
                "A24_JOURNAL_FINISH_TIME_COUNT_TOO_LOW:"
                + str(len(finish_times))
                + ":"
                + str(len(natural_order))
            )
        finish_times = finish_times[-len(natural_order):] if natural_order else []

        inventory, new_batches = current_and_new_batches(a23)
        committed_orders = [
            item
            for item in natural_order
            if item["writer_status"] == "COMMITTED"
        ]
        if len(committed_orders) != len(new_batches):
            raise RuntimeError(
                "A24_COMMITTED_ORDER_NEW_BATCH_COUNT_MISMATCH:"
                + str(len(committed_orders))
                + ":"
                + str(len(new_batches))
            )

        active_uid = str(a23["controlled_cycle"]["actual_batch_uid"])
        current_map = namespace["batch_map"](inventory)
        if active_uid not in current_map:
            raise RuntimeError("A24_INITIAL_ACTIVE_BATCH_MISSING")
        active_source_count = int(current_map[active_uid]["source_candidate_count"])
        new_index = 0
        payloads: list[dict[str, Any]] = []

        for index, order_cycle in enumerate(natural_order):
            writer_status = str(order_cycle["writer_status"])
            if writer_status == "COMMITTED":
                batch = new_batches[new_index]
                new_index += 1
                active_uid = str(batch["batch_uid"])
                active_source_count = int(batch["source_candidate_count"])
            payloads.append(
                {
                    "writer_status": writer_status,
                    "batch_uid": active_uid,
                    "source_count": active_source_count,
                    "timestamp_utc": finish_times[index],
                    "payload": {},
                    "evidence_source": "ORDER_LOG_JOURNAL_DB_RECONSTRUCTION",
                }
            )

        if natural_order:
            latest_result = namespace["load"](namespace["RESULT_PATH"])
            latest = namespace["validate_cycle_payload"](latest_result)
            if latest["writer_status"] != natural_order[-1]["writer_status"]:
                raise RuntimeError("A24_LATEST_ORDER_RESULT_STATUS_MISMATCH")
            if latest["batch_uid"] != payloads[-1]["batch_uid"]:
                raise RuntimeError("A24_LATEST_ORDER_RESULT_UID_MISMATCH")
            if int(latest["source_count"]) != int(payloads[-1]["source_count"]):
                raise RuntimeError("A24_LATEST_ORDER_RESULT_SOURCE_COUNT_MISMATCH")
            payloads[-1] = {
                **latest,
                "evidence_source": "LATEST_RESULT_EXACT",
            }

        return {
            "order_log_lines": lines,
            "all_order_cycles": validated_order,
            "natural_order_cycles": natural_order,
            "journal": journal,
            "natural_payloads": payloads,
        }

    def patched_verify_database(
        a23: dict[str, Any],
        natural_payloads: list[dict[str, Any]],
    ) -> dict[str, Any]:
        inventory, new_batches = current_and_new_batches(a23)
        if inventory["integrity_check"] != "ok":
            raise RuntimeError("A24_DATABASE_INTEGRITY_FAILED")
        if inventory["quick_check"] != "ok":
            raise RuntimeError("A24_DATABASE_QUICK_CHECK_FAILED")
        if inventory["foreign_key_check_rows"] != 0:
            raise RuntimeError("A24_DATABASE_FOREIGN_KEY_FAILED")
        if set(inventory["triggers"]) != {
            "trg_news_disposition_batch_archive_before_delete_v2",
            "trg_news_disposition_ledger_archive_before_delete_v2",
        }:
            raise RuntimeError("A24_DATABASE_TRIGGER_SET_DRIFT")

        expected_sequence = 1
        for batch in inventory["batches"]:
            uid = str(batch["batch_uid"])
            if int(batch["batch_sequence"]) != expected_sequence:
                raise RuntimeError("A24_BATCH_SEQUENCE_GAP")
            expected_sequence += 1
            if batch["status"] != "COMMITTED":
                raise RuntimeError("A24_BATCH_NOT_COMMITTED:" + uid)
            if batch["policy_version"] != namespace["LEDGER_POLICY"]:
                raise RuntimeError("A24_BATCH_POLICY_DRIFT:" + uid)
            if batch["queue_capacity"] != namespace["QUEUE_CAPACITY"]:
                raise RuntimeError("A24_BATCH_QUEUE_CAPACITY_DRIFT:" + uid)
            source_count = int(batch["source_candidate_count"])
            if not (1 <= source_count <= namespace["MAX_SOURCE_ROWS"]):
                raise RuntimeError("A24_BATCH_SOURCE_BOUND_INVALID:" + uid)
            if int(batch["ledger_rows"]) != source_count:
                raise RuntimeError("A24_BATCH_LEDGER_ACCOUNTING_FAILED:" + uid)
            if sum(int(value) for value in batch["disposition_counts"].values()) != source_count:
                raise RuntimeError("A24_BATCH_DISPOSITION_ACCOUNTING_FAILED:" + uid)

        committed_payloads = [
            item
            for item in natural_payloads
            if item["writer_status"] == "COMMITTED"
        ]
        if len(committed_payloads) != len(new_batches):
            raise RuntimeError("A24_COMMITTED_PAYLOAD_NEW_BATCH_COUNT_MISMATCH")
        for payload, batch in zip(committed_payloads, new_batches):
            if payload["batch_uid"] != batch["batch_uid"]:
                raise RuntimeError("A24_COMMITTED_PAYLOAD_UID_MISMATCH")
            if int(payload["source_count"]) != int(batch["source_candidate_count"]):
                raise RuntimeError("A24_COMMITTED_PAYLOAD_SOURCE_COUNT_MISMATCH")

        current_map = namespace["batch_map"](inventory)
        for item in natural_payloads:
            uid = str(item["batch_uid"])
            if uid not in current_map:
                raise RuntimeError("A24_OBSERVED_UID_NOT_IN_DATABASE:" + uid)
            if int(item["source_count"]) != int(current_map[uid]["source_candidate_count"]):
                raise RuntimeError("A24_OBSERVED_SOURCE_COUNT_DATABASE_MISMATCH:" + uid)

        return {
            "inventory": inventory,
            "committed_natural_cycle_uids": [
                str(batch["batch_uid"])
                for batch in new_batches
            ],
            "replay_natural_cycle_uids": [
                str(item["batch_uid"])
                for item in natural_payloads
                if item["writer_status"] == "IDEMPOTENT_REPLAY_NOOP"
            ],
        }

    namespace["observation_snapshot"] = patched_observation_snapshot
    namespace["verify_database"] = patched_verify_database
    return int(namespace["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
