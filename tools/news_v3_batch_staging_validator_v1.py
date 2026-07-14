#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import jsonschema


ROOT = Path("/root/tokenoskobi_clean_v1")

CANDIDATE_SCHEMA = (
    ROOT
    / "data/benchmarks/news/"
    "news_v3_candidate_intake_schema_v1.json"
)

EVIDENCE_SCHEMA = (
    ROOT
    / "data/benchmarks/news/"
    "news_v3_evidence_snapshot_schema_v1.json"
)

MANIFEST_SCHEMA = (
    ROOT
    / "data/benchmarks/news/"
    "news_v3_batch_manifest_schema_v1.json"
)

COLLECTION_QUEUE = (
    ROOT
    / "data/benchmarks/news/"
    "news_v3_collection_queue_v1.jsonl"
)

SOURCE_REGISTRY = (
    ROOT
    / "data/benchmarks/news/"
    "news_v3_source_class_registry_v1.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def evidence_payload_checksum(
    evidence: dict[str, Any],
) -> str:
    payload = dict(evidence)
    payload.pop("snapshot_checksum", None)

    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return sha256_text(canonical)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(value, dict):
        raise ValueError(
            f"JSON object required: {path}"
        )

    return value


def load_jsonl(
    path: Path,
) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(
            handle,
            start=1,
        ):
            stripped = raw.strip()

            if not stripped:
                continue

            value = json.loads(stripped)

            if not isinstance(value, dict):
                raise ValueError(
                    f"JSON object required: "
                    f"{path}:{line_number}"
                )

            rows.append((line_number, value))

    return rows


def schema_errors(
    schema: dict[str, Any],
    value: dict[str, Any],
) -> list[str]:
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )

    errors = sorted(
        validator.iter_errors(value),
        key=lambda item: list(item.absolute_path),
    )

    return [
        error.message
        for error in errors
    ]


def validate_batch(
    batch_dir: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    candidate_file = batch_dir / "candidates.jsonl"
    manifest_file = batch_dir / "batch_manifest.json"
    evidence_dir = batch_dir / "evidence"

    candidate_schema = load_json(CANDIDATE_SCHEMA)
    evidence_schema = load_json(EVIDENCE_SCHEMA)
    manifest_schema = load_json(MANIFEST_SCHEMA)
    manifest = load_json(manifest_file)

    for error in schema_errors(
        manifest_schema,
        manifest,
    ):
        errors.append(
            f"MANIFEST_SCHEMA:{error}"
        )

    candidates = load_jsonl(candidate_file)

    collection_tasks = {
        row["task_uid"]: row
        for _, row in load_jsonl(COLLECTION_QUEUE)
    }

    source_registry = load_json(SOURCE_REGISTRY)

    known_source_classes = {
        item["source_class"]
        for item in source_registry["classes"]
    }

    candidate_uids: set[str] = set()
    candidate_hashes: set[str] = set()

    evidence_uids: set[str] = set()
    evidence_by_candidate: dict[
        str,
        list[tuple[Path, dict[str, Any]]],
    ] = {}

    evidence_files = sorted(
        path
        for path in evidence_dir.glob("*.json")
        if path.is_file()
    )

    for evidence_file in evidence_files:
        evidence = load_json(evidence_file)

        for error in schema_errors(
            evidence_schema,
            evidence,
        ):
            errors.append(
                f"EVIDENCE_SCHEMA:"
                f"{evidence_file.name}:{error}"
            )

        evidence_uid = str(
            evidence.get("evidence_uid") or ""
        )

        if evidence_uid in evidence_uids:
            errors.append(
                f"DUPLICATE_EVIDENCE_UID:"
                f"{evidence_uid}"
            )

        evidence_uids.add(evidence_uid)

        expected_payload_checksum = (
            evidence_payload_checksum(evidence)
        )

        if (
            evidence.get("snapshot_checksum")
            != expected_payload_checksum
        ):
            errors.append(
                f"EVIDENCE_PAYLOAD_CHECKSUM_MISMATCH:"
                f"{evidence_file.name}"
            )

        source_class = str(
            evidence.get("source_class") or ""
        )

        if source_class not in known_source_classes:
            errors.append(
                f"EVIDENCE_UNKNOWN_SOURCE_CLASS:"
                f"{evidence_file.name}:"
                f"{source_class}"
            )

        locator = str(
            evidence.get(
                "canonical_source_locator"
            )
            or ""
        )

        if evidence.get(
            "canonical_source_locator_hash"
        ) != sha256_text(locator):
            errors.append(
                f"EVIDENCE_LOCATOR_HASH_MISMATCH:"
                f"{evidence_file.name}"
            )

        candidate_uid = str(
            evidence.get("candidate_uid") or ""
        )

        evidence_by_candidate.setdefault(
            candidate_uid,
            [],
        ).append(
            (evidence_file, evidence)
        )

    for line_number, candidate in candidates:
        for error in schema_errors(
            candidate_schema,
            candidate,
        ):
            errors.append(
                f"CANDIDATE_SCHEMA:"
                f"line={line_number}:{error}"
            )

        candidate_uid = str(
            candidate.get("candidate_uid") or ""
        )

        if candidate_uid in candidate_uids:
            errors.append(
                f"DUPLICATE_CANDIDATE_UID:"
                f"{candidate_uid}"
            )

        candidate_uids.add(candidate_uid)

        content_hash = str(
            candidate.get("content_hash") or ""
        )

        if content_hash in candidate_hashes:
            errors.append(
                f"DUPLICATE_CONTENT_HASH:"
                f"{content_hash}"
            )

        candidate_hashes.add(content_hash)

        task_uid = str(
            candidate.get(
                "collection_task_uid"
            )
            or ""
        )

        task = collection_tasks.get(task_uid)

        if task is None:
            errors.append(
                f"UNKNOWN_COLLECTION_TASK:"
                f"{task_uid}"
            )

        source_class = str(
            candidate.get("source_class") or ""
        )

        if source_class not in known_source_classes:
            errors.append(
                f"UNKNOWN_SOURCE_CLASS:"
                f"{source_class}"
            )

        if (
            task is not None
            and source_class
            not in task.get(
                "source_class_requirements",
                [],
            )
        ):
            errors.append(
                f"SOURCE_CLASS_NOT_ALLOWED_FOR_TASK:"
                f"{candidate_uid}:"
                f"{source_class}"
            )

        labels = set(
            candidate.get(
                "proposed_adversarial_labels"
            )
            or []
        )

        if {"NONE", "UNKNOWN"}.issubset(labels):
            errors.append(
                f"NONE_UNKNOWN_COEXISTENCE:"
                f"{candidate_uid}"
            )

        if candidate.get("is_synthetic") is True:
            if (
                task is None
                or task.get(
                    "synthetic_records_allowed"
                )
                is not True
            ):
                errors.append(
                    f"SYNTHETIC_NOT_ALLOWED:"
                    f"{candidate_uid}"
                )

        evidence_records = evidence_by_candidate.get(
            candidate_uid,
            [],
        )

        status = str(
            candidate.get("candidate_status") or ""
        )

        pointer = str(
            candidate.get(
                "evidence_snapshot_pointer"
            )
            or ""
        )

        primary_evidence = None

        if status != "QUEUED" and not pointer:
            errors.append(
                f"EVIDENCE_POINTER_REQUIRED:"
                f"{candidate_uid}"
            )

        if pointer:
            prefix = (
                f"batch://{batch_dir.name}/evidence/"
            )

            if not pointer.startswith(prefix):
                errors.append(
                    f"INVALID_BATCH_POINTER_SCHEME:"
                    f"{candidate_uid}"
                )
            else:
                filename = pointer[len(prefix):]

                if (
                    not filename
                    or "/" in filename
                    or "\\" in filename
                    or filename in {".", ".."}
                ):
                    errors.append(
                        f"INVALID_EVIDENCE_FILENAME:"
                        f"{candidate_uid}"
                    )
                else:
                    evidence_root = evidence_dir.resolve()
                    pointer_path = (
                        evidence_root / filename
                    ).resolve()

                    try:
                        pointer_path.relative_to(
                            evidence_root
                        )
                    except ValueError:
                        errors.append(
                            f"EVIDENCE_POINTER_OUTSIDE_BATCH:"
                            f"{candidate_uid}"
                        )
                    else:
                        if not pointer_path.is_file():
                            errors.append(
                                f"EVIDENCE_POINTER_NOT_FOUND:"
                                f"{candidate_uid}:"
                                f"{pointer}"
                            )
                        else:
                            referenced = [
                                evidence
                                for evidence_path, evidence
                                in evidence_records
                                if evidence_path.resolve()
                                == pointer_path
                            ]

                            if len(referenced) != 1:
                                errors.append(
                                    f"EVIDENCE_POINTER_CANDIDATE_"
                                    f"MISMATCH:{candidate_uid}"
                                )
                            else:
                                primary_evidence = referenced[0]

        if primary_evidence is not None:
            primary_checks = {
                "source_uid": candidate.get(
                    "source_uid"
                ),
                "source_family_uid": candidate.get(
                    "source_family_uid"
                ),
                "source_class": candidate.get(
                    "source_class"
                ),
                "content_hash": candidate.get(
                    "content_hash"
                ),
                "canonical_source_locator_hash": (
                    candidate.get(
                        "source_locator_hash"
                    )
                ),
            }

            for field, expected in primary_checks.items():
                if primary_evidence.get(field) != expected:
                    errors.append(
                        f"PRIMARY_EVIDENCE_CANDIDATE_"
                        f"FIELD_MISMATCH:"
                        f"{candidate_uid}:"
                        f"{field}"
                    )

        severity = str(
            candidate.get("proposed_severity") or ""
        )

        if severity in {"HIGH", "CRITICAL"}:
            if len(evidence_records) < 2:
                errors.append(
                    f"HIGH_CRITICAL_EVIDENCE_LT_2:"
                    f"{candidate_uid}"
                )

            verification_states = {
                evidence.get("verification_status")
                for _, evidence in evidence_records
            }

            if (
                "VERIFIED_PRIMARY"
                not in verification_states
            ):
                errors.append(
                    f"HIGH_CRITICAL_PRIMARY_MISSING:"
                    f"{candidate_uid}"
                )

            if (
                "VERIFIED_CORROBORATING"
                not in verification_states
            ):
                errors.append(
                    f"HIGH_CRITICAL_CORROBORATION_MISSING:"
                    f"{candidate_uid}"
                )

            source_uids = {
                str(evidence.get("source_uid") or "")
                for _, evidence in evidence_records
            }

            source_families = {
                str(
                    evidence.get(
                        "source_family_uid"
                    )
                    or ""
                )
                for _, evidence in evidence_records
            }

            if len(source_uids) < 2:
                errors.append(
                    f"HIGH_CRITICAL_DISTINCT_SOURCE_LT_2:"
                    f"{candidate_uid}"
                )

            if len(source_families) < 2:
                errors.append(
                    f"HIGH_CRITICAL_DISTINCT_FAMILY_LT_2:"
                    f"{candidate_uid}"
                )

    for evidence_candidate_uid in evidence_by_candidate:
        if evidence_candidate_uid not in candidate_uids:
            errors.append(
                f"ORPHAN_EVIDENCE:"
                f"{evidence_candidate_uid}"
            )

    if (
        manifest.get("candidate_file_checksum")
        != sha256_file(candidate_file)
    ):
        errors.append(
            "MANIFEST_CANDIDATE_CHECKSUM_MISMATCH"
        )

    if manifest.get("candidate_count") != len(candidates):
        errors.append(
            "MANIFEST_CANDIDATE_COUNT_MISMATCH"
        )

    if manifest.get("evidence_count") != len(
        evidence_files
    ):
        errors.append(
            "MANIFEST_EVIDENCE_COUNT_MISMATCH"
        )

    actual_evidence_checksums = {
        path.name: sha256_file(path)
        for path in evidence_files
    }

    if (
        manifest.get("evidence_file_checksums")
        != actual_evidence_checksums
    ):
        errors.append(
            "MANIFEST_EVIDENCE_CHECKSUM_MAP_MISMATCH"
        )

    if not candidates:
        warnings.append(
            "BATCH_CANDIDATE_FILE_EMPTY"
        )

    return {
        "ok": not errors,
        "batch_uid": manifest.get("batch_uid"),
        "candidate_count": len(candidates),
        "evidence_count": len(evidence_files),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def create_self_test_batch(
    batch_dir: Path,
) -> None:
    evidence_dir = batch_dir / "evidence"
    evidence_dir.mkdir(parents=True)

    locator = "local://news-v3/self-test"
    content_hash = sha256_text(
        "synthetic validator self test"
    )

    evidence = {
        "evidence_uid": "evidence-self-test-1",
        "candidate_uid": "candidate-self-test-1",
        "source_uid": "source-self-test",
        "source_family_uid": "family-self-test",
        "source_name": "Synthetic Self Test",
        "source_class": (
            "SYNTHETIC_ADVERSARIAL_STRESS"
        ),
        "canonical_source_locator": locator,
        "canonical_source_locator_hash": (
            sha256_text(locator)
        ),
        "title": "Synthetic validator self-test",
        "bounded_excerpt": (
            "Local validator self-test only."
        ),
        "published_at_utc": None,
        "captured_at_utc": (
            "2026-01-01T00:00:00+00:00"
        ),
        "capture_method": (
            "ARCHIVED_LOCAL_SOURCE"
        ),
        "content_hash": content_hash,
        "snapshot_checksum": "",
        "verification_status": (
            "PARTIALLY_VERIFIED"
        ),
        "source_availability_status": (
            "ARCHIVED_COPY_ONLY"
        ),
        "reviewer_notes": (
            "Validator self-test only."
        ),
    }

    evidence["snapshot_checksum"] = (
        evidence_payload_checksum(evidence)
    )

    evidence_path = (
        evidence_dir / "evidence-self-test-1.json"
    )

    evidence_path.write_text(
        json.dumps(
            evidence,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    candidate = {
        "candidate_uid": "candidate-self-test-1",
        "collection_task_uid": "Q019",
        "candidate_status": "EVIDENCE_CAPTURED",
        "source_uid": "source-self-test",
        "source_family_uid": "family-self-test",
        "source_name": "Synthetic Self Test",
        "source_class": (
            "SYNTHETIC_ADVERSARIAL_STRESS"
        ),
        "source_locator_hash": sha256_text(locator),
        "content_hash": content_hash,
        "title": "Synthetic validator self-test",
        "bounded_excerpt": (
            "Local validator self-test only."
        ),
        "normalized_text": (
            "synthetic validator self test"
        ),
        "language": "en",
        "published_at_utc": None,
        "captured_at_utc": (
            "2026-01-01T00:00:00+00:00"
        ),
        "proposed_narrative_labels": [
            "UNKNOWN"
        ],
        "proposed_adversarial_labels": [
            "UNKNOWN"
        ],
        "proposed_severity": "UNKNOWN",
        "is_synthetic": True,
        "evidence_snapshot_pointer": (
            "batch://batch_01/evidence/evidence-self-test-1.json"
        ),
        "incident_uid_hint": None,
        "event_group_uid_hint": None,
        "content_cluster_uid_hint": None,
        "duplicate_candidate_uid": None,
        "collector_notes": (
            "Validator self-test only."
        ),
        "created_at_utc": (
            "2026-01-01T00:00:00+00:00"
        ),
    }

    candidate_path = batch_dir / "candidates.jsonl"

    candidate_path.write_text(
        json.dumps(
            candidate,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = {
        "schema": "news_v3_batch_manifest_v1",
        "batch_uid": "batch_01",
        "batch_status": "STAGED",
        "batch_role": "SMOKE_TEST_ONLY",
        "candidate_file": (
            "data/benchmarks/news/batches/"
            "batch_01/candidates.jsonl"
        ),
        "evidence_directory": (
            "data/benchmarks/news/batches/"
            "batch_01/evidence"
        ),
        "candidate_count": 1,
        "evidence_count": 1,
        "candidate_file_checksum": (
            sha256_file(candidate_path)
        ),
        "evidence_file_checksums": {
            evidence_path.name: (
                sha256_file(evidence_path)
            )
        },
        "created_at_utc": (
            "2026-01-01T00:00:00+00:00"
        ),
        "updated_at_utc": (
            "2026-01-01T00:00:00+00:00"
        ),
        "automated_live_fetch": False,
        "runtime_network_access": False,
        "manual_historical_source_research": True,
        "runtime_mutation": False,
        "database_mutation": False,
        "validation_state": "NOT_RUN",
        "merge_state": "NOT_MERGED",
    }

    (batch_dir / "batch_manifest.json").write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as directory:
        batch_dir = Path(directory) / "batch_01"

        create_self_test_batch(batch_dir)

        valid = validate_batch(batch_dir)

        if not valid["ok"]:
            raise RuntimeError(
                "VALID_SELF_TEST_FAILED:"
                + json.dumps(valid, sort_keys=True)
            )

        evidence_path = (
            batch_dir
            / "evidence/evidence-self-test-1.json"
        )

        evidence = load_json(evidence_path)
        evidence["snapshot_checksum"] = "0" * 64

        evidence_path.write_text(
            json.dumps(
                evidence,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        invalid = validate_batch(batch_dir)

        if invalid["ok"]:
            raise RuntimeError(
                "INVALID_SELF_TEST_UNEXPECTEDLY_PASSED"
            )

        if not any(
            "EVIDENCE_PAYLOAD_CHECKSUM_MISMATCH"
            in error
            for error in invalid["errors"]
        ):
            raise RuntimeError(
                "EXPECTED_CHECKSUM_ERROR_NOT_FOUND"
            )

    print(
        "BATCH_STAGING_VALIDATOR_SELF_TEST=PASS"
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch-dir",
        type=Path,
        default=(
            ROOT
            / "data/benchmarks/news/"
            "batches/batch_01"
        ),
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
    )

    args = parser.parse_args()

    if args.self_test:
        run_self_test()

    result = validate_batch(args.batch_dir)

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
