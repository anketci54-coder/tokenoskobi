#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import ast
import os
import subprocess
import sys
import tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
SOURCE = ROOT / 'tools/post_era54_hot_ingress_bound_runtime_first_observation_noapi_v1.py'
EXPECTED_SOURCE_BLOB = '9c3f90b1a5028e0c71ce3a52b89e7e7adf013f40'

OLD = '''    integration_service = integration_service_snapshot.get(
        SERVICE,
        {},
    )
    integration_timer = integration_service_snapshot.get(
        TIMER,
        {},
    )
    service_unit_sha_unchanged = (
        systemd_after['service'].get('FragmentSHA256')
        == integration_service.get('FragmentSHA256')
    )
    timer_unit_sha_unchanged = (
        systemd_after['timer'].get('FragmentSHA256')
        == integration_timer.get('FragmentSHA256')
    )
    if not service_unit_sha_unchanged:
        failures.append('service_unit_file_changed')
    if not timer_unit_sha_unchanged:
        failures.append('timer_unit_file_changed')
'''

NEW = '''    service_sha_before = systemd_before['service'].get('FragmentSHA256')
    service_sha_after = systemd_after['service'].get('FragmentSHA256')
    timer_sha_before = systemd_before['timer'].get('FragmentSHA256')
    timer_sha_after = systemd_after['timer'].get('FragmentSHA256')

    service_unit_sha_unchanged = bool(
        service_sha_before
        and service_sha_after
        and service_sha_before == service_sha_after
    )
    timer_unit_sha_unchanged = bool(
        timer_sha_before
        and timer_sha_after
        and timer_sha_before == timer_sha_after
    )
    if not service_unit_sha_unchanged:
        failures.append('service_unit_file_changed')
    if not timer_unit_sha_unchanged:
        failures.append('timer_unit_file_changed')
'''


def git_blob(path: Path) -> str:
    completed = subprocess.run(
        ['git', 'hash-object', str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-wait-seconds', type=int, default=0)
    args = parser.parse_args()

    if not SOURCE.is_file():
        raise RuntimeError('SOURCE_OBSERVER_MISSING')

    actual_blob = git_blob(SOURCE)
    if actual_blob != EXPECTED_SOURCE_BLOB:
        raise RuntimeError(
            'SOURCE_BLOB_MISMATCH:expected='
            + EXPECTED_SOURCE_BLOB
            + ':actual='
            + actual_blob
        )

    source = SOURCE.read_text(encoding='utf-8')
    if source.count(OLD) != 1:
        raise RuntimeError('UNIT_SHA_BUG_BLOCK_COUNT=' + str(source.count(OLD)))

    patched = source.replace(OLD, NEW, 1)
    ast.parse(patched, filename=str(SOURCE) + '.fix1')

    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding='utf-8',
        suffix='.py',
        prefix='post_era54_first_observation_fix1_',
        dir='/tmp',
        delete=False,
    ) as handle:
        handle.write(patched)
        temp_path = Path(handle.name)

    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(temp_path),
                '--max-wait-seconds',
                str(args.max_wait_seconds),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
        )
        if completed.stdout:
            print(completed.stdout, end='')
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end='')
        return completed.returncode
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == '__main__':
    raise SystemExit(main())
