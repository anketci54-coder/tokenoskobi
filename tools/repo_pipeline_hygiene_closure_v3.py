#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path('/root/tokenoskobi_clean_v1')
TARGET = ROOT / 'tools/repo_pipeline_hygiene_closure_v2.py'
SELF_REL = 'tools/repo_pipeline_hygiene_closure_v3.py'

spec = importlib.util.spec_from_file_location('repo_pipeline_hygiene_closure_v2', TARGET)
if spec is None or spec.loader is None:
    raise SystemExit('HYGIENE_V2_IMPORT_FAILED')

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.ONE_OFF_FILES = tuple(module.ONE_OFF_FILES) + (SELF_REL,)


def archive_one_off_files_exact():
    available_before = [
        rel
        for rel in module.ONE_OFF_FILES
        if (module.ROOT / rel).is_file()
    ]
    if not available_before:
        raise RuntimeError('NO_ONE_OFF_ARCHIVE_CANDIDATE_FOUND')

    moved = []
    absent = []
    destinations = []

    for rel in module.ONE_OFF_FILES:
        source = module.ROOT / rel
        if not source.is_file():
            absent.append(rel)
            continue

        destination = module.ARCHIVE_ROOT / rel
        if destination.exists():
            raise RuntimeError('ARCHIVE_DESTINATION_EXISTS:' + str(destination))

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        os.chmod(destination, source.stat().st_mode)
        module.run(['git', 'add', '-f', str(destination.relative_to(module.ROOT))])
        module.run(['git', 'rm', '--', rel])
        destinations.append(destination)
        moved.append({
            'source': rel,
            'destination': str(destination.relative_to(module.ROOT)),
            'sha256': module.sha256(destination),
        })

    if len(moved) != len(available_before):
        raise RuntimeError(
            'ONE_OFF_ARCHIVE_COUNT_MISMATCH:'
            + str(len(moved))
            + ':'
            + str(len(available_before))
        )

    print('ONE_OFF_AVAILABLE=' + str(len(available_before)), flush=True)
    print('ONE_OFF_ARCHIVED=' + str(len(moved)), flush=True)
    print('ONE_OFF_ABSENT=' + str(len(absent)), flush=True)
    return moved, absent, destinations


def purge_untracked_bytecode() -> list[str]:
    tracked_result = subprocess.run(
        ['git', 'ls-files', '-z'],
        cwd=module.ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tracked_result.returncode != 0:
        raise RuntimeError('GIT_LS_FILES_FAILED_DURING_BYTECODE_PURGE')

    tracked = {
        item.decode('utf-8')
        for item in tracked_result.stdout.split(b'\0')
        if item
    }
    removed: list[str] = []

    for base_name in ('tools', 'tests', 'runtime', 'data', 'reports'):
        base = module.ROOT / base_name
        if not base.exists():
            continue

        for path in sorted(base.rglob('*')):
            if not path.is_file():
                continue
            rel = str(path.relative_to(module.ROOT))
            if rel in tracked:
                continue
            if '__pycache__' in path.parts or path.suffix.lower() in {'.pyc', '.pyo'}:
                path.unlink()
                removed.append(rel)

        for directory in sorted(base.rglob('__pycache__'), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass

    return removed


original_post_classification = module.post_classification


def post_classification_with_bytecode_purge(expected_runtime, expected_data):
    removed_before = purge_untracked_bytecode()
    print('EPHEMERAL_BYTECODE_PURGED=' + str(len(removed_before)), flush=True)

    try:
        return original_post_classification(expected_runtime, expected_data)
    except RuntimeError as exc:
        if not str(exc).startswith('POST_HYGIENE_DISPOSABLE_REMAINS:'):
            raise

        removed_retry = purge_untracked_bytecode()
        print('EPHEMERAL_BYTECODE_PURGED_RETRY=' + str(len(removed_retry)), flush=True)
        return original_post_classification(expected_runtime, expected_data)


module.archive_one_off_files = archive_one_off_files_exact
module.post_classification = post_classification_with_bytecode_purge
raise SystemExit(module.main())
