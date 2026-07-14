#!/usr/bin/env python3
"""Validate isolated NEWS V3 candidate-intake records.

This tool performs no network calls, production database writes,
runtime mutation, panel mutation or execution action.
"""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path("/root/tokenoskobi_clean_v1")

DEFAULT_SCHEMA = (
    ROOT
    / "data/benchmarks/news/"
    "news_v3_candidate_intake_schema_v1.json"
)

DEFAULT_CANDIDATES = (
    ROOT
    / "data/benchmarks/news/"
    "news_v3_candidate_intake_queue_v1.jsonl"
)

DEFAULT_COLLECTION_QUEUE = (
    ROOT
    / "data/benchmarks/news/"
    "news_v3_collection_queue_v1.jsonl"
)

DEFAULT_SOURCE_REGISTRY = (
    ROOT
    / "data/benchmarks/news/"
    "news_v3_source_class_registry_v1.json"
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")

    return value


def load_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            stripped = raw.strip()

            if not stripped:
                continue

            value = json.loads(stripped)

            if not isinstance(value, dict):
                raise ValueError(
                    f"JSON object required at {path}:{line_number}"
                )

            rows.append((line_number, value))

    return rows


def collection_tasks(
    rows: list[tuple[int, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}

    for _, row in rows:
        task_uid = str(row.get("task_uid") or "")

        if not task_uid:
            raise ValueError("COLLECTION_TASK_UID_EMPTY")

        if task_uid in tasks:
            raise ValueError(
                f"DUPLICATE_COLLECTION_TASK_UID:{task_uid}"
            )

        tasks[task_uid] = row

    return tasks


def source_classes(registry: dict[str, Any]) -> set[str]:
    classes = registry.get("classes") or []

    return {
        str(item.get("source_class") or "")
        for item in classes
        if isinstance(item, dict)
        and str(item.get("source_class") or "")
    }


def validate(
    schema: dict[str, Any],
    candidates: list[tuple[int, dict[str, Any]]],
    tasks: dict[str, dict[str, Any]],
    known_source_classes: set[str],
) -> dict[str, Any]:
    required = set(schema.get("required") or [])
    allowed = set((schema.get("properties") or {}).keys())

    errors: list[str] = []
    warnings: list[str] = []
    candidate_uids: set[str] = set()

    for line_number, candidate in candidates:
        prefix = f"line={line_number}"

        missing = sorted(required - set(candidate.keys()))

        if missing:
            errors.append(
                f"{prefix}:MISSING_REQUIRED:{','.join(missing)}"
            )

        unknown = sorted(set(candidate.keys()) - allowed)

        if unknown:
            errors.append(
                f"{prefix}:UNKNOWN_PROPERTIES:{','.join(unknown)}"
            )

        candidate_uid = str(
            candidate.get("candidate_uid") or ""
        )

        if not candidate_uid:
            errors.append(f"{prefix}:CANDIDATE_UID_EMPTY")
        elif candidate_uid in candidate_uids:
            errors.append(
                f"{prefix}:DUPLICATE_CANDIDATE_UID:{candidate_uid}"
            )
        else:
            candidate_uids.add(candidate_uid)

        task_uid = str(
            candidate.get("collection_task_uid") or ""
        )

        task = tasks.get(task_uid)

        if task is None:
            errors.append(
                f"{prefix}:UNKNOWN_COLLECTION_TASK:{task_uid}"
            )

        source_class = str(
            candidate.get("source_class") or ""
        )

        if source_class not in known_source_classes:
            errors.append(
                f"{prefix}:UNKNOWN_SOURCE_CLASS:{source_class}"
            )

        labels = candidate.get(
            "proposed_adversarial_labels"
        )

        if not isinstance(labels, list) or not labels:
            errors.append(
                f"{prefix}:PROPOSED_ADVERSARIAL_LABELS_EMPTY"
            )
            label_set: set[str] = set()
        else:
            label_set = {
                str(item)
                for item in labels
                if str(item)
            }

        if {"NONE", "UNKNOWN"}.issubset(label_set):
            errors.append(
                f"{prefix}:NONE_UNKNOWN_COEXISTENCE"
            )

        narrative = candidate.get(
            "proposed_narrative_labels"
        )

        if not isinstance(narrative, list) or not narrative:
            errors.append(
                f"{prefix}:PROPOSED_NARRATIVE_LABELS_EMPTY"
            )

        is_synthetic = candidate.get("is_synthetic")

        if not isinstance(is_synthetic, bool):
            errors.append(
                f"{prefix}:IS_SYNTHETIC_NOT_BOOLEAN"
            )

        if task is not None and is_synthetic is True:
            if task.get("synthetic_records_allowed") is not True:
                errors.append(
                    f"{prefix}:SYNTHETIC_NOT_ALLOWED_FOR_TASK:"
                    f"{task_uid}"
                )

        if (
            source_class
            == "SYNTHETIC_ADVERSARIAL_STRESS"
            and is_synthetic is not True
        ):
            errors.append(
                f"{prefix}:SYNTHETIC_SOURCE_REQUIRES_FLAG"
            )

        status = str(
            candidate.get("candidate_status") or ""
        )

        positive_processing_states = {
            "EVIDENCE_CAPTURED",
            "NORMALIZED",
            "READY_FOR_LABELING",
        }

        if status in positive_processing_states:
            if not candidate.get(
                "evidence_snapshot_pointer"
            ):
                errors.append(
                    f"{prefix}:EVIDENCE_REQUIRED_FOR_STATUS:"
                    f"{status}"
                )

        if status == "READY_FOR_LABELING":
            if not candidate.get("normalized_text"):
                errors.append(
                    f"{prefix}:NORMALIZED_TEXT_REQUIRED"
                )

        if candidate.get("duplicate_candidate_uid"):
            if candidate.get("duplicate_candidate_uid") == candidate_uid:
                errors.append(
                    f"{prefix}:SELF_DUPLICATE_REFERENCE"
                )

    if not candidates:
        warnings.append("CANDIDATE_QUEUE_EMPTY")

    return {
        "ok": not errors,
        "candidate_count": len(candidates),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def valid_self_test_candidate() -> dict[str, Any]:
    return {
        "candidate_uid": "candidate-self-test-1",
        "collection_task_uid": "Q019",
        "candidate_status": "QUEUED",
        "source_uid": "source-self-test",
        "source_family_uid": "source-family-self-test",
        "source_name": "Synthetic Self Test",
        "source_class": "SYNTHETIC_ADVERSARIAL_STRESS",
        "source_locator_hash": "0123456789abcdef",
        "content_hash": "abcdef0123456789",
        "title": "Synthetic candidate self-test",
        "bounded_excerpt": "Validator self-test only.",
        "normalized_text": "",
        "language": "en",
        "published_at_utc": None,
        "captured_at_utc": "2026-01-01T00:00:00+00:00",
        "proposed_narrative_labels": ["UNKNOWN"],
        "proposed_adversarial_labels": ["UNKNOWN"],
        "proposed_severity": "UNKNOWN",
        "is_synthetic": True,
        "evidence_snapshot_pointer": None,
        "incident_uid_hint": None,
        "event_group_uid_hint": None,
        "content_cluster_uid_hint": None,
        "duplicate_candidate_uid": None,
        "collector_notes": "Self-test only.",
        "created_at_utc": "2026-01-01T00:00:00+00:00"
    }


def run_self_test(
    schema: dict[str, Any],
    tasks: dict[str, dict[str, Any]],
    known_source_classes: set[str],
) -> None:
    valid = valid_self_test_candidate()

    result = validate(
        schema,
        [(1, valid)],
        tasks,
        known_source_classes,
    )

    if not result["ok"]:
        raise RuntimeError(
            "VALID_SELF_TEST_FAILED:"
            + json.dumps(result, sort_keys=True)
        )

    invalid = copy.deepcopy(valid)
    invalid["candidate_uid"] = "candidate-self-test-invalid"
    invalid["proposed_adversarial_labels"] = [
        "NONE",
        "UNKNOWN",
    ]

    invalid_result = validate(
        schema,
        [(1, invalid)],
        tasks,
        known_source_classes,
    )

    if invalid_result["ok"]:
        raise RuntimeError(
            "INVALID_SELF_TEST_UNEXPECTEDLY_PASSED"
        )

    if not any(
        "NONE_UNKNOWN_COEXISTENCE" in item
        for item in invalid_result["errors"]
    ):
        raise RuntimeError(
            "EXPECTED_NONE_UNKNOWN_ERROR_NOT_FOUND"
        )

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "candidate.jsonl"

        path.write_text(
            json.dumps(valid, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        loaded = load_jsonl(path)

        if len(loaded) != 1:
            raise RuntimeError(
                "JSONL_LOAD_SELF_TEST_FAILED"
            )

    print("CANDIDATE_INTAKE_VALIDATOR_SELF_TEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
    )

    parser.add_argument(
        "--candidates",
        type=Path,
        default=DEFAULT_CANDIDATES,
    )

    parser.add_argument(
        "--collection-queue",
        type=Path,
        default=DEFAULT_COLLECTION_QUEUE,
    )

    parser.add_argument(
        "--source-registry",
        type=Path,
        default=DEFAULT_SOURCE_REGISTRY,
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
    )

    args = parser.parse_args()

    schema = load_json(args.schema)

    task_rows = load_jsonl(
        args.collection_queue
    )

    tasks = collection_tasks(task_rows)

    registry = load_json(args.source_registry)

    known_source_classes = source_classes(registry)

    if args.self_test:
        run_self_test(
            schema,
            tasks,
            known_source_classes,
        )

    candidates = load_jsonl(args.candidates)

    result = validate(
        schema,
        candidates,
        tasks,
        known_source_classes,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
