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
SOURCE = ROOT / 'tools/era54_canonical_closure_and_index_sync_noapi_v1.py'
EXPECTED_SOURCE_BLOB = 'f62a3f10cc76f497950be328d928b8fd1b5814e4'

OLD_BOOT = '''    boot['current_checkpoint'] = checkpoint
    boot['current_problem'] = None
    boot['current_work_unit'] = work_unit
    boot['last_completed'] = WORK_UNIT
'''

NEW_BOOT = '''    boot['current_checkpoint'] = checkpoint
    boot['current_problem'] = None
    boot['current_work_unit'] = work_unit
    boot['work_unit'] = WORK_UNIT
    boot['open_risks'] = [
        'Next major project line is not selected yet.',
        'ERA55 is not opened and requires explicit human selection.',
        'Risk is minimized, never zero.',
    ]
    boot['last_completed'] = WORK_UNIT
'''

OLD_PROTOCOL = '''    boot.setdefault('project', {})
    boot['project']['status'] = 'ACTIVE'
'''

NEW_PROTOCOL = '''    boot.setdefault('work_unit_protocol', {})
    boot['work_unit_protocol'].update({
        'boot_update_position': 'FINAL_CONTENT_MUTATION_BEFORE_ATOMIC_CLOSURE_COMMIT',
        'closure_rule': (
            'BOOT and RUNTIME are included in the atomic closure commit. '
            'The work unit is declared closed only after push, remote verify, and GitHub seal.'
        ),
        'mandatory_sequence': [
            'PLAN',
            'APPROVAL',
            'APPLY',
            'TEST',
            'AUDIT',
            'POST_AUDIT',
            'CLOSURE_DOCUMENT_SYNC',
            'BOOT_RUNTIME_UPDATE',
            'COMMIT',
            'PUSH',
            'REMOTE_VERIFY',
            'GITHUB_SEAL',
            'WORK_UNIT_CLOSED',
        ],
        'forbidden': [
            'Do not mark work unit closed before remote verification.',
            'Do not start next work unit before GitHub seal.',
            'Do not rely on chat memory as closure evidence.',
            'Do not create a second state-only commit when one atomic closure commit is sufficient.',
        ],
    })
    boot.setdefault('project', {})
    boot['project']['status'] = 'ACTIVE'
'''

OLD_LOCK_RULE = '''- PROJECT_HISTORY.json is append-only.
- `tk machine` is not used by the current canonical flow.
'''

NEW_LOCK_RULE = '''- PROJECT_HISTORY.json is append-only.
- BOOT and RUNTIME are included in the atomic closure commit; closure is declared only after push and remote verification.
- `tk machine` is not used by the current canonical flow.
'''

OLD_HISTORY_STATUS = "            'status': 'CLOSED_READY_FOR_GITHUB_SEAL',\n"
NEW_HISTORY_STATUS = "            'status': 'CLOSED_VERIFIED_GITHUB_SEALED_BY_ATOMIC_CLOSURE_COMMIT',\n"


def git_blob(path: Path) -> str:
    completed = subprocess.run(
        ['git', 'hash-object', str(path.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def atomic_write(path: Path, text: str) -> None:
    fd, temp_name = tempfile.mkstemp(
        prefix='.' + path.name + '.',
        suffix='.tmp',
        dir=str(path.parent),
    )
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(text)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-head', required=True)
    args = parser.parse_args()

    if not SOURCE.is_file():
        raise RuntimeError('SOURCE_SYNC_RUNNER_MISSING')
    actual_blob = git_blob(SOURCE)
    if actual_blob != EXPECTED_SOURCE_BLOB:
        raise RuntimeError(
            'SOURCE_BLOB_MISMATCH:expected=' + EXPECTED_SOURCE_BLOB
            + ':actual=' + actual_blob
        )

    source = SOURCE.read_text(encoding='utf-8')
    replacements = [
        ('BOOT_REQUIRED_FIELDS_PATCH_COUNT', OLD_BOOT, NEW_BOOT),
        ('ATOMIC_CLOSURE_PROTOCOL_PATCH_COUNT', OLD_PROTOCOL, NEW_PROTOCOL),
        ('DOCUMENTATION_LOCK_SEQUENCE_PATCH_COUNT', OLD_LOCK_RULE, NEW_LOCK_RULE),
        ('HISTORY_STATUS_PATCH_COUNT', OLD_HISTORY_STATUS, NEW_HISTORY_STATUS),
    ]
    patched = source
    for label, old, new in replacements:
        count = patched.count(old)
        if count != 1:
            raise RuntimeError(label + '=' + str(count))
        patched = patched.replace(old, new, 1)

    ast.parse(patched, filename=str(SOURCE) + '.fix1')

    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding='utf-8',
        suffix='.py',
        prefix='era54_closure_sync_fix1_',
        dir='/tmp',
        delete=False,
    ) as handle:
        handle.write(patched)
        temporary = Path(handle.name)

    try:
        completed = subprocess.run(
            [sys.executable, str(temporary)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env={
                **os.environ,
                'PYTHONDONTWRITEBYTECODE': '1',
                'ERA54_CLOSURE_SYNC_EXPECTED_HEAD': args.expected_head,
            },
        )
        if completed.stdout:
            print(completed.stdout, end='')
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end='')
        if completed.returncode != 0:
            return completed.returncode
        atomic_write(SOURCE, patched)
        print('ERA54_CLOSURE_SYNC_SOURCE_FIX1_APPLIED=OK')
        return 0
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    raise SystemExit(main())
