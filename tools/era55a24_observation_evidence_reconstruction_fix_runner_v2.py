#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path("/root/tokenoskobi_clean_v1")
TARGET = ROOT / "tools/era55a24_p0_post_activation_observation_and_p0_f1_closure_decision_v1.py"
BASE_FIX = ROOT / "tools/era55a24_execution_safety_fix_runner_v1.py"


def load_base_fix():
    spec = importlib.util.spec_from_file_location("era55a24_base_fix", BASE_FIX)
    if spec is None or spec.loader is None:
        raise RuntimeError("A24_BASE_FIX_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"A24_FIX2_REPLACEMENT_COUNT_INVALID:{label}:{count}")
    return source.replace(old, new, 1)


def transform(source: str) -> str:
    source = load_base_fix().transform(source)

    old = '''def observation_snapshot(a23: dict[str, Any]) -> dict[str, Any]:
    if not ORDER_LOG.exists():
        raise RuntimeError("A24_ORDER_LOG_MISSING")
    lines = ORDER_LOG.read_text(encoding="utf-8").splitlines()
    cycles = split_order_cycles(lines)
    if not cycles:
        raise RuntimeError("A24_NO_ORDER_CYCLES")
    if cycles[0] != a23["runner_order"]:
        raise RuntimeError("A24_CONTROLLED_CYCLE_ORDER_DRIFT")
    validated_order = [validate_order_cycle(cycle) for cycle in cycles]
    natural_order = validated_order[1:]

    journal = journal_since(str(a23["apply_finished_at_utc"]))
    if journal["failure_markers"]:
        raise RuntimeError(
            "A24_POST_ACTIVATION_FAILURE_MARKERS:"
            + ",".join(journal["failure_markers"])
        )
    payloads = [
        validate_cycle_payload(payload)
        for payload in journal["cycle_payloads"]
    ]
    if len(natural_order) != len(payloads):
        raise RuntimeError(
            "A24_ORDER_JOURNAL_CYCLE_COUNT_MISMATCH:"
            + str(len(natural_order))
            + ":"
            + str(len(payloads))
        )
    if journal["service_finished_count"] < len(payloads):
        raise RuntimeError("A24_SERVICE_SUCCESS_COUNT_TOO_LOW")
    for index, order_cycle in enumerate(natural_order):
        if order_cycle["writer_status"] != payloads[index]["writer_status"]:
            raise RuntimeError("A24_ORDER_PAYLOAD_WRITER_STATUS_MISMATCH")

    return {
        "order_log_lines": lines,
        "all_order_cycles": validated_order,
        "natural_order_cycles": natural_order,
        "journal": journal,
        "natural_payloads": payloads,
    }
'''

    new = '''def observation_snapshot(a23: dict[str, Any]) -> dict[str, Any]:
    if not ORDER_LOG.exists():
        raise RuntimeError("A24_ORDER_LOG_MISSING")
    lines = ORDER_LOG.read_text(encoding="utf-8").splitlines()
    cycles = split_order_cycles(lines)
    if not cycles:
        raise RuntimeError("A24_NO_ORDER_CYCLES")
    if cycles[0] != a23["runner_order"]:
        raise RuntimeError("A24_CONTROLLED_CYCLE_ORDER_DRIFT")

    validated_order = [validate_order_cycle(cycle) for cycle in cycles]
    natural_order = validated_order[1:]
    if not natural_order:
        raise RuntimeError("A24_NO_NATURAL_ORDER_CYCLES")

    journal = journal_since(str(a23["apply_finished_at_utc"]))
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

    original_inventory = a23["production_after"]
    original_map = batch_map(original_inventory)
    current_inventory = database_inventory(DB)
    current_map = batch_map(current_inventory)

    for uid, batch in original_map.items():
        if current_map.get(uid) != batch:
            raise RuntimeError("A24_RECONSTRUCTION_ORIGINAL_BATCH_MUTATED:" + uid)

    original_batches = sorted(
        original_inventory["batches"],
        key=lambda item: int(item["batch_sequence"]),
    )
    if not original_batches:
        raise RuntimeError("A24_RECONSTRUCTION_ORIGINAL_BATCHES_EMPTY")

    new_batches = sorted(
        [
            batch
            for uid, batch in current_map.items()
            if uid not in original_map
        ],
        key=lambda item: int(item["batch_sequence"]),
    )
    committed_markers = sum(
        1
        for cycle in natural_order
        if cycle["writer_status"] == "COMMITTED"
    )
    if committed_markers != len(new_batches):
        raise RuntimeError(
            "A24_RECONSTRUCTION_COMMIT_COUNT_MISMATCH:"
            + str(committed_markers)
            + ":"
            + str(len(new_batches))
        )

    current_uid = str(original_batches[-1]["batch_uid"])
    new_index = 0
    reconstructed: list[dict[str, Any]] = []

    for sequence, cycle in enumerate(natural_order, start=1):
        writer_status = str(cycle["writer_status"])
        if writer_status == "COMMITTED":
            if new_index >= len(new_batches):
                raise RuntimeError("A24_RECONSTRUCTION_NEW_BATCH_EXHAUSTED")
            active_batch = new_batches[new_index]
            new_index += 1
            current_uid = str(active_batch["batch_uid"])
        else:
            active_batch = current_map.get(current_uid)
            if active_batch is None:
                raise RuntimeError(
                    "A24_RECONSTRUCTION_REPLAY_ACTIVE_BATCH_MISSING:"
                    + current_uid
                )

        reconstructed.append(
            {
                "writer_status": writer_status,
                "batch_uid": current_uid,
                "source_count": int(active_batch["source_candidate_count"]),
                "timestamp_utc": "",
                "payload": None,
                "evidence_source": "ORDER_LOG_AND_DATABASE_RECONSTRUCTION",
                "order_cycle_sequence": sequence,
            }
        )

    if new_index != len(new_batches):
        raise RuntimeError("A24_RECONSTRUCTION_NEW_BATCH_NOT_CONSUMED")

    if not RESULT_PATH.exists():
        raise RuntimeError("A24_LATEST_RESULT_MISSING")
    latest = validate_cycle_payload(load(RESULT_PATH))
    reconstructed_latest = reconstructed[-1]
    for key in ("writer_status", "batch_uid", "source_count"):
        if reconstructed_latest[key] != latest[key]:
            raise RuntimeError(
                "A24_LATEST_RESULT_RECONSTRUCTION_MISMATCH:"
                + key
                + ":"
                + str(reconstructed_latest[key])
                + ":"
                + str(latest[key])
            )
    latest["evidence_source"] = "LATEST_RESULT_FILE"
    latest["order_cycle_sequence"] = len(natural_order)
    reconstructed[-1] = latest

    return {
        "order_log_lines": lines,
        "all_order_cycles": validated_order,
        "natural_order_cycles": natural_order,
        "journal": journal,
        "natural_payloads": reconstructed,
        "evidence_mode": "ORDER_LOG_DB_LATEST_RESULT_RECONSTRUCTION",
        "journal_payloads_available": len(journal["cycle_payloads"]),
    }
'''

    source = replace_once(
        source,
        old,
        new,
        "OBSERVATION_EVIDENCE_RECONSTRUCTION",
    )
    return source


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    transformed = transform(source)
    code = compile(transformed, str(Path(__file__).resolve()), "exec")
    namespace = {
        "__name__": "__main__",
        "__file__": str(Path(__file__).resolve()),
        "__package__": None,
    }
    exec(code, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
