#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path('/root/tokenoskobi_clean_v1')
TARGET = ROOT / 'tools/repo_pipeline_hygiene_closure_v2.py'

spec = importlib.util.spec_from_file_location('repo_pipeline_hygiene_closure_v2', TARGET)
if spec is None or spec.loader is None:
    raise SystemExit('HYGIENE_V2_IMPORT_FAILED')

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


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


module.archive_one_off_files = archive_one_off_files_exact
raise SystemExit(module.main())
