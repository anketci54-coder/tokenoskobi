#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')
TARGET = ROOT / 'tools/era56e_global_cache_bounded_runtime_binding_readiness_decision_v1.py'
OLD = "      'era56d_atomic_readonly_failclosed':p.get('era56d_atomic_publish') is True and p.get('era56d_readonly_consumer') is True and p.get('era56d_stale_rejected') is True and p.get('era56d_hash_mismatch_rejected') is True,"
NEW = "      'era56d_atomic_readonly_failclosed':p.get('era56d_atomic_publish') is True and p.get('era56d_readonly_consumer') is True and p.get('era56d_fail_closed') is True,"


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check, timeout=90)


def main() -> int:
    expected = os.environ.get('TOKENOSKOBI_EXPECTED_HEAD', '').strip()
    if run(['git', 'status', '--short']).stdout.strip():
        raise RuntimeError('WORKTREE_NOT_CLEAN')
    if expected and run(['git', 'rev-parse', 'HEAD']).stdout.strip() != expected:
        raise RuntimeError('HEAD_MISMATCH')
    text = TARGET.read_text(encoding='utf-8')
    if OLD not in text:
        raise RuntimeError('PATCH_TARGET_NOT_FOUND')
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding='utf-8')
    compile_result = run(['python3', '-m', 'py_compile', str(TARGET.relative_to(ROOT))], check=False)
    if compile_result.returncode != 0:
        print(compile_result.stdout, end='')
        print(compile_result.stderr, end='')
        raise RuntimeError('TARGET_COMPILE_FAILED')
    run(['git', 'add', str(TARGET.relative_to(ROOT))])
    diff = run(['git', 'diff', '--cached', '--check'], check=False)
    if diff.returncode != 0:
        print(diff.stdout, end='')
        print(diff.stderr, end='')
        raise RuntimeError('DIFF_CHECK_FAILED')
    run(['git', 'commit', '-m', 'ERA56E_FIX_1 | OK | ALIGN_FAIL_CLOSED_GUARD_WITH_RUNTIME'])
    print('ERA56E_GUARD_FIX=SUCCESS')
    print('ERA56D_FAIL_CLOSED_FIELD=era56d_fail_closed')
    print('LOCAL_COMMIT=' + run(['git', 'rev-parse', 'HEAD']).stdout.strip())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
