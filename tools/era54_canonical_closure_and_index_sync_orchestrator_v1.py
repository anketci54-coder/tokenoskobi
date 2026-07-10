#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import ast
import json
import os
import subprocess
import sys

ROOT = Path('/root/tokenoskobi_clean_v1')
SOURCE = ROOT / 'tools/era54_canonical_closure_and_index_sync_noapi_v1.py'
LAUNCHER = ROOT / 'tools/era54_canonical_closure_and_index_sync_fix1_launcher_v1.py'
CONTROL = ROOT / 'data/control/era54_canonical_closure_and_index_sync_noapi_v1.json'
SOURCE_BLOB = 'f62a3f10cc76f497950be328d928b8fd1b5814e4'
LAUNCHER_BLOB = '210671c18634563f44479cc01f05814584e9a438'
DECISION = 'OK_ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI'
NEXT_STEP = 'NEXT_MAJOR_PROJECT_LINE_SELECTION_AFTER_NEWS_OPERATIONAL_BASELINE_CLOSURE'

TRACKED_TARGETS = [
    'README.md',
    '01_INDEX.md',
    'PROJECT_BOOT.json',
    'PROJECT_RUNTIME.json',
    'PROJECT_HISTORY.json',
    '03_ROADMAP.md',
    '04_ALMANAC.md',
    '05_ATLAS.md',
    '06_PROJECT_MASTER_STATE.md',
    '07_PROJECT_HANDOFF.md',
    'data/tokenoskobi_v1_v8_master_era_roadmap.json',
    'docs/canonical/CANONICAL_DOCUMENTATION_V1_LOCK.md',
    'reports/LATEST_TK_AI_HANDOFF.md',
    'data/control/latest_tk_machine_state.json',
    'tools/era54_canonical_closure_and_index_sync_noapi_v1.py',
]
NEW_TARGETS = [
    'data/control/era54_canonical_closure_and_index_sync_noapi_v1.json',
]
ALL_TARGETS = TRACKED_TARGETS + NEW_TARGETS


def run(
    args: list[str],
    *,
    capture: bool = True,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=capture,
        env=env,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            'COMMAND_FAILED:' + ' '.join(args)
            + ':rc=' + str(completed.returncode)
            + ':stdout=' + (completed.stdout or '').strip()
            + ':stderr=' + (completed.stderr or '').strip()
        )
    return completed


def git_output(*args: str) -> str:
    return run(['git', *args]).stdout.strip()


def git_blob(relative: str) -> str:
    return git_output('hash-object', relative)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError('JSON_OBJECT_REQUIRED:' + str(path))
    return value


def rollback() -> None:
    run(
        ['git', 'restore', '--staged', '--worktree', '--', *TRACKED_TARGETS],
        check=False,
    )
    CONTROL.unlink(missing_ok=True)


def validate_source() -> None:
    if git_blob(str(SOURCE.relative_to(ROOT))) != SOURCE_BLOB:
        raise RuntimeError('SOURCE_BLOB_MISMATCH')
    if git_blob(str(LAUNCHER.relative_to(ROOT))) != LAUNCHER_BLOB:
        raise RuntimeError('LAUNCHER_BLOB_MISMATCH')
    ast.parse(SOURCE.read_text(encoding='utf-8'), filename=str(SOURCE))
    launcher_text = LAUNCHER.read_text(encoding='utf-8')
    ast.parse(launcher_text, filename=str(LAUNCHER))
    required = [
        'BOOT_REQUIRED_FIELDS_PATCH_COUNT',
        'ATOMIC_CLOSURE_PROTOCOL_PATCH_COUNT',
        'DOCUMENTATION_LOCK_SEQUENCE_PATCH_COUNT',
        'HISTORY_STATUS_PATCH_COUNT',
    ]
    missing = [marker for marker in required if marker not in launcher_text]
    if missing:
        raise RuntimeError('LAUNCHER_MARKERS_MISSING:' + ','.join(missing))


def validate_staged() -> dict[str, Any]:
    expected = set(ALL_TARGETS)
    staged = set(git_output('diff', '--cached', '--name-only').splitlines())
    if staged != expected:
        raise RuntimeError(
            'STAGED_SET_MISMATCH:'
            + json.dumps({
                'expected': sorted(expected),
                'actual': sorted(staged),
                'missing': sorted(expected - staged),
                'unexpected': sorted(staged - expected),
            }, sort_keys=True)
        )
    unstaged = set(git_output('diff', '--name-only').splitlines())
    if unstaged:
        raise RuntimeError('UNSTAGED_TRACKED_FILES:' + ','.join(sorted(unstaged)))
    untracked = set(
        git_output('ls-files', '--others', '--exclude-standard').splitlines()
    )
    if untracked:
        raise RuntimeError('UNTRACKED_UNIGNORED_FILES:' + ','.join(sorted(untracked)))

    artifact = load_json(CONTROL)
    result = artifact.get('result', {})
    checks = {
        'decision': artifact.get('decision') == DECISION,
        'failures_empty': artifact.get('failures') == [],
        'fail_count_zero': artifact.get('fail_count') == 0,
        'era_closed': result.get('era_status') == 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'news_closed': result.get('news_operational_baseline') == 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'natural_cycle': result.get('natural_timer_cycle') == 'OBSERVED_VERIFIED',
        'index_valid': result.get('index_navigation_valid') is True,
        'readme_valid': result.get('readme_startup_pointers_valid') is True,
        'history_appended': result.get('project_history_appended') is True,
        'atlas_updated': result.get('atlas_updated') is True,
        'roadmap_corrected': result.get('master_roadmap_era54_corrected') is True,
        'era55_closed': result.get('era55_opened') is False,
        'next_step': artifact.get('next') == NEXT_STEP,
        'mandatory_count': len(result.get('mandatory_closure_files') or []) == 9,
        'all_changed_count': len(result.get('all_changed_files') or []) == 15,
    }
    failed = [name for name, ok in checks.items() if ok is not True]
    if failed:
        raise RuntimeError('ARTIFACT_GATE_FAILED:' + ','.join(failed))

    runtime = load_json(ROOT / 'PROJECT_RUNTIME.json')
    boot = load_json(ROOT / 'PROJECT_BOOT.json')
    history = load_json(ROOT / 'PROJECT_HISTORY.json')
    roadmap = load_json(ROOT / 'data/tokenoskobi_v1_v8_master_era_roadmap.json')

    if runtime.get('last_completed') != 'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI':
        raise RuntimeError('RUNTIME_LAST_COMPLETED_MISMATCH')
    if runtime.get('current_era_status') != 'CLOSED_VERIFIED_BOUNDED_RUNTIME':
        raise RuntimeError('RUNTIME_ERA54_STATUS_MISMATCH')
    if runtime.get('next_safe_step', {}).get('name') != NEXT_STEP:
        raise RuntimeError('RUNTIME_NEXT_STEP_MISMATCH')
    if runtime.get('news_operational_state', {}).get('known_warnings') != []:
        raise RuntimeError('RUNTIME_CURRENT_WARNINGS_NOT_CLEARED')
    if runtime.get('news_operational_state', {}).get('hot_gateway_deferred') is not False:
        raise RuntimeError('RUNTIME_HOT_GATEWAY_STILL_DEFERRED')

    if boot.get('work_unit') != 'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI':
        raise RuntimeError('BOOT_WORK_UNIT_MISSING')
    if not isinstance(boot.get('open_risks'), list) or len(boot['open_risks']) != 3:
        raise RuntimeError('BOOT_OPEN_RISKS_INVALID')
    protocol = boot.get('work_unit_protocol', {})
    if protocol.get('boot_update_position') != 'FINAL_CONTENT_MUTATION_BEFORE_ATOMIC_CLOSURE_COMMIT':
        raise RuntimeError('BOOT_ATOMIC_CLOSURE_PROTOCOL_MISSING')
    sequence = protocol.get('mandatory_sequence') or []
    for marker in ['BOOT_RUNTIME_UPDATE', 'COMMIT', 'PUSH', 'REMOTE_VERIFY', 'GITHUB_SEAL', 'WORK_UNIT_CLOSED']:
        if marker not in sequence:
            raise RuntimeError('BOOT_SEQUENCE_MARKER_MISSING:' + marker)

    events = history.get('events') or []
    matching = [
        event for event in events
        if isinstance(event, dict)
        and event.get('event_id') == 'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI_V1'
    ]
    if len(matching) != 1:
        raise RuntimeError('PROJECT_HISTORY_EVENT_COUNT=' + str(len(matching)))
    if matching[0].get('status') != 'CLOSED_VERIFIED_GITHUB_SEALED_BY_ATOMIC_CLOSURE_COMMIT':
        raise RuntimeError('PROJECT_HISTORY_STATUS_MISMATCH')

    era54 = None
    era55 = None
    for version in roadmap.get('versions', []):
        if isinstance(version, dict) and version.get('id') == 'V3':
            for child in version.get('children', []):
                if isinstance(child, dict) and child.get('id') == 'ERA54':
                    era54 = child
                elif isinstance(child, dict) and child.get('id') == 'ERA55':
                    era55 = child
    if not era54 or era54.get('title') != 'Hot Intelligence Ingress Bounded Runtime':
        raise RuntimeError('ROADMAP_ERA54_TITLE_NOT_CORRECTED')
    if era54.get('status') != 'CLOSED':
        raise RuntimeError('ROADMAP_ERA54_NOT_CLOSED')
    if not era55 or era55.get('status') != 'PLANNED_CANDIDATE_NOT_OPENED':
        raise RuntimeError('ROADMAP_ERA55_STATE_INVALID')

    index_text = (ROOT / '01_INDEX.md').read_text(encoding='utf-8')
    readme_text = (ROOT / 'README.md').read_text(encoding='utf-8')
    lock_text = (
        ROOT / 'docs/canonical/CANONICAL_DOCUMENTATION_V1_LOCK.md'
    ).read_text(encoding='utf-8')
    atlas_text = (ROOT / '05_ATLAS.md').read_text(encoding='utf-8')
    roadmap_text = (ROOT / '03_ROADMAP.md').read_text(encoding='utf-8')
    almanac_text = (ROOT / '04_ALMANAC.md').read_text(encoding='utf-8')

    for required in [
        'PROJECT_RUNTIME.json',
        'PROJECT_BOOT.json',
        'PROJECT_HISTORY.json',
        'data/tokenoskobi_v1_v8_master_era_roadmap.json',
    ]:
        if required not in index_text:
            raise RuntimeError('INDEX_POINTER_MISSING:' + required)
    for forbidden in [
        'NEXT_CHAT_HANDOFF.md',
        'TOKENOSKOBI_OS_REGISTRY.json',
        'tk ai',
        'tk sync',
    ]:
        if forbidden in readme_text:
            raise RuntimeError('README_STALE_POINTER:' + forbidden)
    if 'MANDATORY_ERA_AND_V_CLOSURE_UPDATE_SET' not in lock_text:
        raise RuntimeError('DOCUMENTATION_LOCK_CLOSURE_SET_MISSING')
    if 'atomic closure commit' not in lock_text:
        raise RuntimeError('DOCUMENTATION_LOCK_ATOMIC_SEQUENCE_MISSING')
    if 'ERA54_FINAL_BOUNDED_NEWS_RUNTIME_ATLAS_START' not in atlas_text:
        raise RuntimeError('ATLAS_CURRENT_FLOW_MISSING')
    if 'ERA54_FINAL_CANONICAL_CLOSURE_ENTRY_V1' not in roadmap_text:
        raise RuntimeError('ROADMAP_CLOSURE_ENTRY_MISSING')
    if 'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_ENTRY_V1' not in almanac_text:
        raise RuntimeError('ALMANAC_CLOSURE_ENTRY_MISSING')

    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-head', required=True)
    args = parser.parse_args()

    current_head = git_output('rev-parse', 'HEAD')
    branch = git_output('branch', '--show-current')
    if current_head != args.expected_head:
        raise RuntimeError(
            'HEAD_MISMATCH:expected=' + args.expected_head + ':actual=' + current_head
        )
    if branch != 'main':
        raise RuntimeError('BRANCH_NOT_MAIN:' + branch)
    if git_output('status', '--porcelain=v1'):
        raise RuntimeError('WORKTREE_NOT_CLEAN_AT_START')

    validate_source()
    committed = False
    try:
        completed = run(
            [sys.executable, str(LAUNCHER), '--expected-head', current_head],
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
        )
        if completed.stdout:
            print(completed.stdout, end='')
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end='')

        run(['git', 'add', '-f', '--', *ALL_TARGETS])
        run(['git', 'diff', '--cached', '--check'])
        artifact = validate_staged()
        decision_id = str(artifact.get('decision_id') or '')
        if not decision_id:
            raise RuntimeError('DECISION_ID_MISSING')

        run([
            'git',
            'commit',
            '-m',
            'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI | OK | ' + decision_id,
        ], capture=False)
        committed = True
        new_head = git_output('rev-parse', 'HEAD')

        run(['git', 'push', 'origin', 'main'], capture=False)
        remote = git_output('ls-remote', 'origin', 'refs/heads/main').split()[0]
        if remote != new_head:
            raise RuntimeError(
                'REMOTE_SEAL_MISMATCH:local=' + new_head + ':remote=' + remote
            )
        if git_output('status', '--porcelain=v1'):
            raise RuntimeError('POST_SEAL_WORKTREE_NOT_CLEAN')

        result = artifact['result']
        print('ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI=SUCCESS')
        print('ERA54_STATUS=' + result['era_status'])
        print('NEWS_OPERATIONAL_BASELINE=' + result['news_operational_baseline'])
        print('INDEX_NAVIGATION=' + str(result['index_navigation_valid']).lower())
        print('README_POINTERS=' + str(result['readme_startup_pointers_valid']).lower())
        print('MANDATORY_CLOSURE_FILES=' + str(len(result['mandatory_closure_files'])))
        print('TOTAL_UPDATED_FILES=' + str(len(result['all_changed_files']) + 1))
        print('PROJECT_HISTORY=APPENDED')
        print('ATLAS=CURRENT_RUNTIME_FLOW_BOUND')
        print('MASTER_ROADMAP_ERA54=CORRECTED_CLOSED')
        print('ERA55_OPENED=false')
        print('NEXT_SAFE_STEP=' + artifact['next'])
        print('NEW_HEAD=' + new_head)
        print('REMOTE_HEAD=' + remote)
        print('GIT_WORKTREE=CLEAN')
        return 0
    except Exception:
        if not committed:
            rollback()
            print('ERA54_CLOSURE_SYNC_ROLLBACK=RESTORED_TO_RUNNER_HEAD')
        raise


if __name__ == '__main__':
    raise SystemExit(main())
