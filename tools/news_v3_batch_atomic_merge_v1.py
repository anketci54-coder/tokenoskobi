#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path("/root/tokenoskobi_clean_v1")

DEFAULT_BATCH_DIR = (
    ROOT
    / "data/benchmarks/news/batches/batch_01"
)

DEFAULT_CANONICAL_QUEUE = (
    ROOT
    / "data/benchmarks/news/"
    "news_v3_candidate_intake_queue_v1.jsonl"
)

VALIDATOR = (
    ROOT
    / "tools/news_v3_batch_staging_validator_v1.py"
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            stripped = raw.strip()

            if not stripped:
                continue

            value = json.loads(stripped)

            if not isinstance(value, dict):
                raise ValueError(
                    f"JSON object required: {path}"
                )

            rows.append(value)

    return rows


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch-dir",
        type=Path,
        default=DEFAULT_BATCH_DIR,
    )

    parser.add_argument(
        "--canonical-queue",
        type=Path,
        default=DEFAULT_CANONICAL_QUEUE,
    )

    parser.add_argument(
        "--apply",
        action="store_true",
    )

    args = parser.parse_args()

    subprocess.run(
        [
            "python3",
            str(VALIDATOR),
            "--batch-dir",
            str(args.batch_dir),
        ],
        check=True,
    )

    staging_file = args.batch_dir / "candidates.jsonl"

    staging_rows = load_jsonl(staging_file)
    canonical_rows = load_jsonl(args.canonical_queue)

    canonical_uids = {
        str(row.get("candidate_uid") or "")
        for row in canonical_rows
    }

    canonical_hashes = {
        str(row.get("content_hash") or "")
        for row in canonical_rows
    }

    for row in staging_rows:
        candidate_uid = str(
            row.get("candidate_uid") or ""
        )
        content_hash = str(
            row.get("content_hash") or ""
        )

        if candidate_uid in canonical_uids:
            raise SystemExit(
                f"DUPLICATE_CANONICAL_UID:{candidate_uid}"
            )

        if content_hash in canonical_hashes:
            raise SystemExit(
                f"DUPLICATE_CANONICAL_CONTENT_HASH:"
                f"{content_hash}"
            )

    report = {
        "mode": (
            "APPLY"
            if args.apply
            else "DRY_RUN"
        ),
        "canonical_before": len(canonical_rows),
        "batch_candidates": len(staging_rows),
        "canonical_after": (
            len(canonical_rows)
            + len(staging_rows)
        ),
        "duplicate_uid_count": 0,
        "duplicate_content_hash_count": 0,
    }

    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    if not args.apply:
        return 0

    if not staging_rows:
        raise SystemExit(
            "EMPTY_BATCH_APPLY_FORBIDDEN"
        )

    combined = canonical_rows + staging_rows

    args.canonical_queue.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=".news_v3_candidate_merge_",
        suffix=".jsonl",
        dir=str(args.canonical_queue.parent),
    )

    temporary_path = Path(temporary_name)

    try:
        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
        ) as handle:
            for row in combined:
                handle.write(
                    json.dumps(
                        row,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n"
                )

            handle.flush()
            os.fsync(handle.fileno())

        os.replace(
            temporary_path,
            args.canonical_queue,
        )

        directory_fd = os.open(
            str(args.canonical_queue.parent),
            os.O_RDONLY,
        )

        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    print("ATOMIC_MERGE=COMPLETE")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
