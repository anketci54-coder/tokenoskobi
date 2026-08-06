#!/usr/bin/env python3
"""Semantic validator for the NEWS V3 golden benchmark dataset.

This tool is isolated benchmark tooling. It performs no network calls,
runtime writes, database writes, panel mutations or execution actions.
"""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path("/root/tokenoskobi_clean_v1")
DEFAULT_SCHEMA = (
    DEFAULT_ROOT
    / "data/benchmarks/news/news_v3_benchmark_schema_v1.json"
)
DEFAULT_DATASET = (
    DEFAULT_ROOT
    / "data/benchmarks/news/news_v3_golden_dataset_v1.jsonl"
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
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


def label_names(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    names: list[str] = []
    for item in items:
        if isinstance(item, dict):
            names.append(str(item.get("label") or ""))
    return names


def validate_dataset(
    schema: dict[str, Any],
    rows: list[tuple[int, dict[str, Any]]],
) -> dict[str, Any]:
    required = set(schema.get("required") or [])
    allowed = set((schema.get("properties") or {}).keys())

    errors: list[str] = []
    warnings: list[str] = []

    record_uids: set[str] = set()
    cluster_splits: dict[tuple[str, str], set[str]] = {}
    content_hash_splits: dict[str, set[str]] = {}

    for line_number, record in rows:
        prefix = f"line={line_number}"

        missing = sorted(required - set(record.keys()))
        if missing:
            errors.append(f"{prefix}:MISSING_REQUIRED:{','.join(missing)}")

        unknown = sorted(set(record.keys()) - allowed)
        if unknown:
            errors.append(f"{prefix}:UNKNOWN_PROPERTIES:{','.join(unknown)}")

        record_uid = str(record.get("record_uid") or "")
        if not record_uid:
            errors.append(f"{prefix}:RECORD_UID_EMPTY")
        elif record_uid in record_uids:
            errors.append(f"{prefix}:DUPLICATE_RECORD_UID:{record_uid}")
        else:
            record_uids.add(record_uid)

        split = str(record.get("dataset_split") or "")
        content_hash = str(record.get("content_hash") or "")
        if content_hash:
            content_hash_splits.setdefault(content_hash, set()).add(split)

        for field in (
            "canonical_incident_uid",
            "event_group_uid",
            "content_cluster_uid",
            "duplicate_cluster_uid",
        ):
            value = record.get(field)
            if value:
                cluster_splits.setdefault(
                    (field, str(value)),
                    set(),
                ).add(split)

        adversarial = label_names(
            record.get("expected_adversarial_labels")
        )
        adversarial_set = set(adversarial)

        if "NONE" in adversarial_set and "UNKNOWN" in adversarial_set:
            errors.append(f"{prefix}:NONE_UNKNOWN_COEXISTENCE")

        if not adversarial:
            errors.append(f"{prefix}:ADVERSARIAL_LABELS_EMPTY")

        narrative = record.get("expected_narrative_labels")
        if not isinstance(narrative, list) or not narrative:
            errors.append(f"{prefix}:NARRATIVE_LABELS_EMPTY")

        severity = record.get("expected_severity")
        severity_name = ""
        if isinstance(severity, dict):
            severity_name = str(severity.get("label") or "")
        else:
            errors.append(f"{prefix}:SEVERITY_NOT_OBJECT")

        reviewer_count = record.get("reviewer_count")
        if not isinstance(reviewer_count, int):
            errors.append(f"{prefix}:REVIEWER_COUNT_INVALID")
        elif severity_name in {"CRITICAL", "HIGH"} and reviewer_count < 2:
            errors.append(
                f"{prefix}:HIGH_SEVERITY_REVIEWER_COUNT_LT_2"
            )

        for family in (
            "expected_narrative_labels",
            "expected_adversarial_labels",
        ):
            items = record.get(family)
            if not isinstance(items, list):
                continue
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(
                        f"{prefix}:{family}[{index}]:LABEL_NOT_OBJECT"
                    )
                    continue
                if not str(item.get("evidence_pointer") or ""):
                    errors.append(
                        f"{prefix}:{family}[{index}]:EVIDENCE_POINTER_EMPTY"
                    )
                confidence = item.get("label_confidence")
                if not isinstance(confidence, (int, float)):
                    errors.append(
                        f"{prefix}:{family}[{index}]:CONFIDENCE_INVALID"
                    )
                agreement = item.get("reviewer_agreement")
                if not isinstance(agreement, (int, float)):
                    errors.append(
                        f"{prefix}:{family}[{index}]:AGREEMENT_INVALID"
                    )

        if isinstance(severity, dict):
            if not str(severity.get("evidence_pointer") or ""):
                errors.append(f"{prefix}:SEVERITY_EVIDENCE_POINTER_EMPTY")

        if record.get("is_duplicate") is True and not record.get(
            "duplicate_cluster_uid"
        ):
            errors.append(
                f"{prefix}:DUPLICATE_WITHOUT_CLUSTER_UID"
            )

        if not record.get("source_uid"):
            errors.append(f"{prefix}:SOURCE_UID_EMPTY")

        evidence_pointers = record.get("evidence_pointers")
        if not isinstance(evidence_pointers, list) or not evidence_pointers:
            errors.append(f"{prefix}:EVIDENCE_POINTERS_EMPTY")

        ground_truth_sources = record.get("ground_truth_sources")
        if not isinstance(ground_truth_sources, list) or not ground_truth_sources:
            errors.append(f"{prefix}:GROUND_TRUTH_SOURCES_EMPTY")

    for (field, uid), splits in sorted(cluster_splits.items()):
        cleaned = {item for item in splits if item}
        if len(cleaned) > 1:
            errors.append(
                f"CROSS_SPLIT_LEAKAGE:{field}:{uid}:{sorted(cleaned)}"
            )

    for content_hash, splits in sorted(content_hash_splits.items()):
        cleaned = {item for item in splits if item}
        if len(cleaned) > 1:
            errors.append(
                f"CONTENT_HASH_CROSS_SPLIT_LEAKAGE:"
                f"{content_hash}:{sorted(cleaned)}"
            )

    if not rows:
        warnings.append("DATASET_EMPTY")

    return {
        "ok": not errors,
        "record_count": len(rows),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def valid_self_test_record() -> dict[str, Any]:
    label = {
        "label": "NORMAL_INFORMATION",
        "label_confidence": 1.0,
        "evidence_pointer": "evidence://self-test/narrative",
        "reviewer_agreement": 1.0,
    }
    adversarial = {
        "label": "NONE",
        "label_confidence": 1.0,
        "evidence_pointer": "evidence://self-test/adversarial",
        "reviewer_agreement": 1.0,
    }
    severity = {
        "label": "INFORMATIONAL",
        "label_confidence": 1.0,
        "evidence_pointer": "evidence://self-test/severity",
        "reviewer_agreement": 1.0,
    }
    return {
        "record_uid": "self-test-record-1",
        "event_uid": "self-test-event-1",
        "canonical_incident_uid": None,
        "event_group_uid": "self-test-event-group-1",
        "content_cluster_uid": "self-test-content-cluster-1",
        "source_family_uid": "self-test-source-family",
        "source_uid": "self-test-source",
        "source_name": "Self Test",
        "source_class": "SYNTHETIC_ADVERSARIAL_STRESS",
        "source_trust_level": "UNKNOWN",
        "published_at_utc": None,
        "fetched_at_utc": "2026-01-01T00:00:00+00:00",
        "language": "en",
        "title": "Self-test normal information record",
        "bounded_excerpt": "Synthetic validator self-test.",
        "normalized_text": "synthetic validator self test",
        "canonical_url_hash": "0123456789abcdef",
        "content_hash": "abcdef0123456789",
        "evidence_snapshot_pointer": "evidence://self-test/snapshot",
        "body_available": False,
        "expected_entities": [],
        "expected_tokens": [],
        "expected_chains": [],
        "expected_contract_addresses": [],
        "expected_wallets": [],
        "ambiguous_entities": [],
        "expected_narrative_labels": [label],
        "expected_adversarial_labels": [adversarial],
        "expected_severity": severity,
        "expected_market_impact": "NEUTRAL",
        "market_impact_horizon": "UNKNOWN",
        "expected_market_direction": None,
        "expected_relevance": 0.1,
        "is_real_incident": False,
        "is_fake_announcement": False,
        "is_duplicate": False,
        "duplicate_cluster_uid": None,
        "is_stale": False,
        "is_conflicting_source": False,
        "requires_human_review": False,
        "ground_truth_sources": ["self-test-source"],
        "evidence_pointers": ["evidence://self-test/snapshot"],
        "labeling_notes": "Validator self-test only.",
        "reviewer_count": 1,
        "reviewer_agreement": 1.0,
        "dataset_split": "ADVERSARIAL_STRESS",
        "dataset_version": "news_v3_golden_dataset_v1",
        "created_at_utc": "2026-01-01T00:00:00+00:00",
    }


def run_self_test(schema: dict[str, Any]) -> None:
    valid = valid_self_test_record()
    valid_result = validate_dataset(schema, [(1, valid)])
    if not valid_result["ok"]:
        raise RuntimeError(
            "VALID_SELF_TEST_FAILED:"
            + json.dumps(valid_result, sort_keys=True)
        )

    invalid = copy.deepcopy(valid)
    invalid["record_uid"] = "self-test-record-invalid"
    invalid["expected_adversarial_labels"].append(
        {
            "label": "UNKNOWN",
            "label_confidence": 0.5,
            "evidence_pointer": "evidence://self-test/unknown",
            "reviewer_agreement": 0.5,
        }
    )
    invalid_result = validate_dataset(schema, [(1, invalid)])
    if invalid_result["ok"]:
        raise RuntimeError("INVALID_SELF_TEST_UNEXPECTEDLY_PASSED")
    if not any(
        "NONE_UNKNOWN_COEXISTENCE" in item
        for item in invalid_result["errors"]
    ):
        raise RuntimeError(
            "INVALID_SELF_TEST_EXPECTED_ERROR_NOT_FOUND"
        )

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "self_test.jsonl"
        path.write_text(
            json.dumps(valid, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        loaded = load_jsonl(path)
        if len(loaded) != 1:
            raise RuntimeError("JSONL_LOAD_SELF_TEST_FAILED")

    print("SEMANTIC_VALIDATOR_SELF_TEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
    )
    args = parser.parse_args()

    schema = load_json(args.schema)

    if args.self_test:
        run_self_test(schema)

    rows = load_jsonl(args.dataset)
    result = validate_dataset(schema, rows)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
