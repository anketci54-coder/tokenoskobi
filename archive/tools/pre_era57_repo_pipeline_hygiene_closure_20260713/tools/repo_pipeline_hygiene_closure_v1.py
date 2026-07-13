#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
WORK = 'PRE_ERA57_REPO_AND_PIPELINE_HYGIENE_CLOSURE'
RESULT = 'OK_PRE_ERA57_REPO_AND_PIPELINE_HYGIENE_CLOSED'
NEXT = 'ERA57_AUTONOMOUS_RESEARCH_LAYER_OPENING_DECISION'
TAG = 'PRE_ERA57_REPO_PIPELINE_HYGIENE_FINAL_SEAL'
ARTIFACT_REL = 'data/control/pre_era57_repo_pipeline_hygiene_closure_v1.json'
ARTIFACT = ROOT / ARTIFACT_REL
DEPENDENCY_RESULT = Path('/tmp/pre_era57_phase9_timer_dependency_check_v1.json')
POST_STRESS = Path('/tmp/pre_era57_post_hygiene_stress_v1.json')
CLASSIFIER_ARTIFACT = ROOT / 'data/control/general_runtime_hardening_b_active_surface_classification_v1.json'
PHASE9_TIMER = 'tokenoskobi-phase9-observation-runtime.timer'
PHASE9_SERVICE = 'tokenoskobi-phase9-observation-runtime.service'
TRANSIENT_UNIT = 'tokenoskobi-era55a24-observation-20260712T134302Z.service'
NEWS_TIMER = 'tokenoskobi-news-radar-refresh.timer'
PRODUCTION_DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
ARCHIVE_ROOT = ROOT / 'archive/tools/pre_era57_repo_pipeline_hygiene_closure_20260713'

ONE_OFF_FILES = (
    'tools/general_runtime_emergency_patch_cleanup_and_canonical_realign_v1.py',
    'tools/general_runtime_producer_contract_repair_v2.py',
    'tools/general_runtime_runner_contract_validator_v1.py',
    'tools/general_runtime_policy_authority_validator_v1.py',
    'tools/general_runtime_hardening_e_final_stress_gate_v1.py',
    'tools/pre_era57_canonical_continuation_and_stress_harness_prep_v1.py',
    'tools/pre_era57_isolated_stress_harness_execute_and_close_v1.py',
    'tools/pre_era57_live_raw_runner_resolution_and_runtime_entry_decision_v1.py',
    'tools/pre_era57_raw_runner_bounded_path_repair_decision_v1.py',
    'tools/phase9_dependency_check_fast_v1.py',
    'tools/run_phase9_dependency_check_v1.sh',
    'tests/pre_era57_stress_harness.py',
)


def say(text: str) -> None:
    print(text, flush=True)


def run(
    argv: list[str],
    *,
    check: bool = True,
    timeout: int = 180,
    capture: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        timeout=timeout,
        check=False,
        env=env,
    )
    if check and result.returncode != 0:
        detail = ''
        if capture:
            detail = f'\nSTDOUT:\n{result.stdout[-4000:]}\nSTDERR:\n{result.stderr[-4000:]}'
        raise RuntimeError(f'COMMAND_FAILED:{argv}:RC={result.returncode}{detail}')
    return result


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError(f'JSON_OBJECT_REQUIRED:{path}')
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    return run(['git', *args]).stdout.strip()


def systemctl_props(unit: str, props: tuple[str, ...]) -> dict[str, str]:
    argv = ['systemctl', 'show', unit, '--no-pager']
    for prop in props:
        argv.extend(['-p', prop])
    result = run(argv, check=False)
    return {
        line.split('=', 1)[0]: line.split('=', 1)[1]
        for line in result.stdout.splitlines()
        if '=' in line
    }


def unit_state(unit: str) -> dict[str, str]:
    return systemctl_props(
        unit,
        ('LoadState', 'ActiveState', 'SubState', 'UnitFileState', 'Result', 'FragmentPath'),
    )


def fragment_hash(state: dict[str, str]) -> str | None:
    raw = state.get('FragmentPath') or ''
    path = Path(raw) if raw else None
    return sha256(path) if path and path.is_file() else None


def replace_section(text: str, heading: str, body: str) -> str:
    start = text.find(heading)
    if start < 0:
        return text.rstrip() + '\n\n' + heading + '\n\n' + body.rstrip() + '\n'
    end = text.find('\n## ', start + len(heading))
    if end < 0:
        end = len(text)
    return text[:start] + heading + '\n\n' + body.rstrip() + '\n' + text[end:]


def require_clean_and_synced() -> tuple[str, str]:
    run(['git', 'fetch', 'origin', 'main'])
    status = git_value('status', '--porcelain')
    if status:
        raise RuntimeError('WORKTREE_NOT_CLEAN:\n' + status)
    head = git_value('rev-parse', 'HEAD')
    remote = git_value('rev-parse', 'origin/main')
    if head != remote:
        raise RuntimeError(f'HEAD_REMOTE_MISMATCH:{head}:{remote}')
    return head, remote


def maybe_finish_existing_push() -> bool:
    runtime = load(ROOT / 'PROJECT_RUNTIME.json')
    pointer = runtime.get('canonical_runtime_pointer', {})
    hygiene = pointer.get('pre_era57_repo_pipeline_hygiene', {})
    if not isinstance(hygiene, dict) or hygiene.get('status') != 'CLOSED_VERIFIED':
        return False
    run(['git', 'fetch', 'origin', 'main'])
    head = git_value('rev-parse', 'HEAD')
    remote = git_value('rev-parse', 'origin/main')
    if head != remote:
        say('STEP=RESUME_PENDING_PUSH')
        run(['git', 'push', 'origin', 'main', TAG], capture=False, timeout=600)
        run(['git', 'fetch', 'origin', 'main', '--tags'])
        if git_value('rev-parse', 'origin/main') != head:
            raise RuntimeError('REMOTE_VERIFY_FAILED_AFTER_RESUME')
    say('PRE_ERA57_REPO_PIPELINE_HYGIENE=CLOSED_VERIFIED')
    say('REMOTE_VERIFY=OK')
    return True


def validate_dependency_result() -> dict[str, Any]:
    if not DEPENDENCY_RESULT.is_file():
        raise RuntimeError('PHASE9_DEPENDENCY_RESULT_MISSING')
    data = load(DEPENDENCY_RESULT)
    checks = data.get('checks', {})
    required = {
        'systemd_binding_proven': True,
        'script_declares_inert': True,
        'config_inert': True,
        'active_repo_consumer_count': 0,
        'external_systemd_consumer_count': 0,
        'external_filesystem_consumer_count': 0,
        'timer_enabled': True,
        'timer_active': True,
        'production_mutation': False,
        'systemd_mutation': False,
        'era57_opened': False,
    }
    if data.get('decision') != 'SAFE_TO_DISABLE_AND_STOP':
        raise RuntimeError('PHASE9_NOT_SAFE_TO_DISABLE:' + str(data.get('decision')))
    for key, expected in required.items():
        if checks.get(key) != expected:
            raise RuntimeError(f'PHASE9_DEPENDENCY_CHECK_MISMATCH:{key}:{checks.get(key)}')
    return data


def protected_inventory() -> tuple[list[str], list[str], dict[str, str]]:
    artifact = load(CLASSIFIER_ARTIFACT)
    classification = artifact['classification']
    active_runtime = list(classification['ACTIVE_RUNTIME'])
    active_data = list(classification['ACTIVE_RUNTIME_DATA'])
    if len(active_runtime) != 14 or len(active_data) != 12:
        raise RuntimeError(
            f'PROTECTED_INVENTORY_COUNT_MISMATCH:{len(active_runtime)}:{len(active_data)}'
        )
    protected = active_runtime + active_data
    hashes: dict[str, str] = {}
    for rel in protected:
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError('PROTECTED_FILE_MISSING:' + rel)
        hashes[rel] = sha256(path)
    return active_runtime, active_data, hashes


def remove_disposable_files() -> list[str]:
    removed: list[str] = []
    roots = ('tools', 'tests', 'runtime', 'data', 'reports')
    disposable_suffixes = {'.pyc', '.pyo', '.tmp', '.swp', '.bak', '.orig'}
    for root_name in roots:
        base = ROOT / root_name
        if not base.exists():
            continue
        for directory in sorted(base.rglob('__pycache__'), reverse=True):
            if not directory.is_dir():
                continue
            for file in directory.rglob('*'):
                if file.is_file():
                    removed.append(str(file.relative_to(ROOT)))
            shutil.rmtree(directory, ignore_errors=False)
        for file in sorted(base.rglob('*')):
            if file.is_file() and file.suffix.lower() in disposable_suffixes:
                removed.append(str(file.relative_to(ROOT)))
                file.unlink()
    return sorted(set(removed))


def archive_one_off_files() -> tuple[list[dict[str, str]], list[str]]:
    moved: list[dict[str, str]] = []
    absent: list[str] = []
    for rel in ONE_OFF_FILES:
        source = ROOT / rel
        if not source.is_file():
            absent.append(rel)
            continue
        destination = ARCHIVE_ROOT / rel
        if destination.exists():
            raise RuntimeError('ARCHIVE_DESTINATION_EXISTS:' + str(destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        mode = source.stat().st_mode
        shutil.copy2(source, destination)
        os.chmod(destination, mode)
        run(['git', 'add', '-f', str(destination.relative_to(ROOT))])
        run(['git', 'rm', '--', rel])
        moved.append({
            'source': rel,
            'destination': str(destination.relative_to(ROOT)),
            'sha256': sha256(destination),
        })
    if len(moved) < 8:
        raise RuntimeError(f'INSUFFICIENT_ONE_OFF_ARCHIVE_COUNT:{len(moved)}')
    return moved, absent


def load_classifier_module():
    path = ROOT / 'tools/general_runtime_surface_classifier_v1.py'
    spec = importlib.util.spec_from_file_location('general_runtime_surface_classifier_v1', path)
    if spec is None or spec.loader is None:
        raise RuntimeError('CLASSIFIER_IMPORT_FAILED')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reclassify(expected_runtime: list[str], expected_data: list[str]) -> dict[str, Any]:
    module = load_classifier_module()
    files = module.tracked(ROOT)
    file_set = set(files)
    unit_rows, seeds = module.units(ROOT)
    edges, parse_errors = module.graph(ROOT, files)
    reachable = module.walk(seeds, edges)
    active_runtime = sorted(
        item for item in reachable
        if item in file_set and item.endswith('.py')
        and item.startswith(('tools/', 'active_panel_8096/'))
    )
    active_data = sorted(
        item for item in reachable
        if item in file_set and not item.endswith('.py')
    )
    missing = []
    for source in sorted(reachable):
        if not source.endswith('.py') or not (ROOT / source).is_file():
            continue
        text = (ROOT / source).read_text(encoding='utf-8', errors='replace')
        for target in sorted(module.paths(ROOT, text)):
            if not (ROOT / target).exists():
                missing.append({'source': source, 'target': target})
    disposable = []
    for base_name in ('tools', 'tests', 'runtime', 'data', 'reports'):
        base = ROOT / base_name
        if not base.exists():
            continue
        for full in base.rglob('*'):
            if full.is_file() and (
                '__pycache__' in full.parts
                or full.suffix.lower() in {'.pyc', '.pyo', '.tmp', '.swp', '.bak', '.orig'}
            ):
                disposable.append(str(full.relative_to(ROOT)))
    if active_runtime != sorted(expected_runtime):
        raise RuntimeError('ACTIVE_RUNTIME_SET_CHANGED')
    if active_data != sorted(expected_data):
        raise RuntimeError('ACTIVE_RUNTIME_DATA_SET_CHANGED')
    if parse_errors:
        raise RuntimeError('POST_HYGIENE_PARSE_ERRORS:' + json.dumps(parse_errors))
    if missing:
        raise RuntimeError('POST_HYGIENE_MISSING_REFERENCES:' + json.dumps(missing))
    if disposable:
        raise RuntimeError('POST_HYGIENE_DISPOSABLE_REMAINS:' + json.dumps(disposable))
    return {
        'active_runtime_count': len(active_runtime),
        'active_runtime_data_count': len(active_data),
        'active_runtime_unchanged': True,
        'active_runtime_data_unchanged': True,
        'parse_error_count': 0,
        'missing_active_reference_count': 0,
        'disposable_remaining_count': 0,
        'systemd_unit_count': len(unit_rows),
    }


def run_stress() -> dict[str, Any]:
    POST_STRESS.unlink(missing_ok=True)
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    result = run(
        [
            sys.executable,
            'tests/general_runtime_stress_harness_v1.py',
            '--scenario',
            'all',
            '--output',
            str(POST_STRESS),
        ],
        timeout=180,
        env=env,
    )
    if result.stdout.strip():
        say(result.stdout.strip())
    data = load(POST_STRESS)
    scenarios = data.get('scenarios', {})
    if data.get('verdict') != 'OK' or len(scenarios) != 10:
        raise RuntimeError('POST_HYGIENE_STRESS_FAILED')
    if data.get('source_hash_verified') is not True:
        raise RuntimeError('POST_HYGIENE_STRESS_SOURCE_HASH_NOT_VERIFIED')
    return {
        'verdict': 'OK',
        'scenario_count': 10,
        'scenario_names': sorted(scenarios),
        'production_path_untouched': data.get('production_path_untouched'),
        'production_mutation': data.get('production_mutation'),
        'source_hash_verified': data.get('source_hash_verified'),
    }


def update_canonical(artifact: dict[str, Any], now: str) -> None:
    runtime_path = ROOT / 'PROJECT_RUNTIME.json'
    runtime = load(runtime_path)
    pointer = runtime['canonical_runtime_pointer']
    pointer.update({
        'current_stage': 'PRE_ERA57_REPO_AND_PIPELINE_HYGIENE_CLOSED_VERIFIED',
        'last_completed': WORK,
        'last_result': RESULT,
        'last_artifact': ARTIFACT_REL,
        'pre_era57_repo_pipeline_hygiene': {
            'status': 'CLOSED_VERIFIED',
            'repo_hygiene_ready_for_era57': True,
            'pipeline_hygiene_ready_for_era57': True,
            'phase9_timer_retired': True,
            'transient_failed_unit_cleared': True,
            'active_runtime_unchanged': True,
            'active_runtime_data_unchanged': True,
            'unclassified_blind_delete': False,
            'artifact': ARTIFACT_REL,
            'closed_at_utc': now,
        },
        'repo_hygiene_ready_for_era57': True,
        'pipeline_hygiene_ready_for_era57': True,
        'phase9_observation_timer_enabled': False,
        'phase9_observation_timer_active': False,
        'era57_opening_decision_ready': True,
        'era57_opened': False,
        'live_source_fetch_authorized': False,
        'production_mutation': False,
        'next_safe_step': NEXT,
        'project_status': 'ERA56_CLOSED_ERA57_OPENING_DECISION_READY',
        'updated_at_utc': now,
    })
    runtime.update({
        'last_completed': WORK,
        'last_result': RESULT,
        'last_artifact': ARTIFACT_REL,
        'next_safe_step': NEXT,
        'updated_at': now,
        'updated_at_utc': now,
        'current_problem': {'code': 'NONE', 'severity': 'NONE', 'evidence': ARTIFACT_REL},
        'current_work_unit': {
            'id': WORK,
            'status': 'CLOSED_VERIFIED',
            'result': RESULT,
            'artifact': ARTIFACT_REL,
            'production_database_mutation': False,
            'systemd_reduction_only': True,
            'next_step': NEXT,
        },
        'current_state': {
            'project_status': 'ERA56_CLOSED_ERA57_OPENING_DECISION_READY',
            'runtime_status': 'PRE_ERA57_REPO_PIPELINE_HYGIENE_CLOSED_VERIFIED',
            'mode': 'ERA57_OPENING_DECISION_READY',
            'last_action': {
                'task': WORK,
                'result': RESULT,
                'artifact': ARTIFACT_REL,
                'timestamp': now,
            },
            'current_problem': {'code': 'NONE', 'severity': 'NONE', 'evidence': ARTIFACT_REL},
            'next_safe_step': {
                'id': NEXT,
                'status': 'READY',
                'human_authorization_required': True,
                'production_mutation': False,
            },
            'updated_at': now,
        },
    })
    save(runtime_path, runtime)

    history_path = ROOT / 'PROJECT_HISTORY.json'
    history = load(history_path)
    events = history.setdefault('events', [])
    if not any(isinstance(item, dict) and item.get('event_id') == WORK for item in events):
        events.append({
            'event_id': WORK,
            'timestamp_utc': now,
            'status': 'CLOSED_VERIFIED',
            'result': RESULT,
            'artifact': ARTIFACT_REL,
            'phase9_timer_disabled': True,
            'transient_failed_unit_cleared': True,
            'disposable_removed_count': artifact['disposable_cleanup']['removed_count'],
            'one_off_archived_count': artifact['one_off_archive']['moved_count'],
            'active_runtime_unchanged': True,
            'active_runtime_data_unchanged': True,
            'production_database_mutation': False,
            'era57_opened': False,
            'next_safe_step': NEXT,
        })
    history['updated_at'] = now
    history['updated_at_utc'] = now
    save(history_path, history)

    master_path = ROOT / '06_PROJECT_MASTER_STATE.md'
    master = master_path.read_text(encoding='utf-8')
    master = replace_section(master, '## 02 CURRENT MAJOR-LINE POSITION', '''```text
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
ERA55_STATUS=CLOSED_SEALED
ERA56_STATUS=CLOSED_SEALED
GENERAL_RUNTIME_HARDENING_STATUS=CLOSED_VERIFIED
PRE_ERA57_REPO_PIPELINE_HYGIENE=CLOSED_VERIFIED
PHASE9_OBSERVATION_TIMER=DISABLED_INACTIVE
ERA57_OPENING_DECISION_READY=true
ERA57_OPENED=false
LIVE_FETCH_AUTHORIZED=false
PRODUCTION_MUTATION=false
```''')
    master = replace_section(master, '## 03 LAST VERIFIED WORK', f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
ACTIVE_RUNTIME=14_UNCHANGED
ACTIVE_RUNTIME_DATA=12_UNCHANGED
DISPOSABLE_REMAINING=0
PHASE9_TIMER=DISABLED_INACTIVE
TRANSIENT_FAILED_UNIT=CLEARED
POST_HYGIENE_STRESS=10/10
PRODUCTION_DATABASE_MUTATION=false
ERA57_OPENED=false
```

NEXT_SAFE_STEP={NEXT}''')
    master_path.write_text(master.rstrip() + '\n', encoding='utf-8')

    handoff_path = ROOT / '07_PROJECT_HANDOFF.md'
    handoff = handoff_path.read_text(encoding='utf-8')
    handoff = replace_section(handoff, '## 02 CURRENT CONTINUATION CHECKPOINT', f'''PROJECT_STATUS=ERA56_CLOSED_ERA57_OPENING_DECISION_READY
CURRENT_VERSION=V3_RUNTIME_INTELLIGENCE_OS
CURRENT_MAIN_LINE=PRE_ERA57_REPO_AND_PIPELINE_HYGIENE
CURRENT_STAGE=PRE_ERA57_REPO_AND_PIPELINE_HYGIENE_CLOSED_VERIFIED
LAST_COMPLETED={WORK}
PRE_ERA57_REPO_PIPELINE_HYGIENE=CLOSED_VERIFIED
PHASE9_TIMER=DISABLED_INACTIVE
ERA57_OPENING_DECISION_READY=true
ERA57_OPENED=false
LIVE_FETCH_AUTHORIZED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD''')
    handoff = replace_section(handoff, '## 03 LAST VERIFIED WORK', f'''LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={ARTIFACT_REL}
ACTIVE_RUNTIME=14_UNCHANGED
ACTIVE_RUNTIME_DATA=12_UNCHANGED
DISPOSABLE_REMAINING=0
ONE_OFF_TOOLS_ARCHIVED={artifact['one_off_archive']['moved_count']}
POST_HYGIENE_STRESS=10/10
ERA57_OPENED=false
PRODUCTION_MUTATION=false''')
    handoff_path.write_text(handoff.rstrip() + '\n', encoding='utf-8')

    almanac_path = ROOT / '04_ALMANAC.md'
    almanac = almanac_path.read_text(encoding='utf-8')
    marker = '## PRE ERA57 REPO AND PIPELINE HYGIENE CLOSURE'
    if marker not in almanac:
        almanac = almanac.rstrip() + f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_VERIFIED`\n- Result: `{RESULT}`\n- Phase9 timer: `DISABLED_INACTIVE`\n- Transient failed unit: `CLEARED`\n- Active runtime: `14_UNCHANGED`\n- Active runtime data: `12_UNCHANGED`\n- Disposable remaining: `0`\n- One-off tools archived: `{artifact['one_off_archive']['moved_count']}`\n- Post-hygiene stress: `10/10`\n- Production database mutation: `false`\n- ERA57 opened: `false`\n- Artifact: `{ARTIFACT_REL}`\n- Next safe step: `{NEXT}`\n'''
        almanac_path.write_text(almanac, encoding='utf-8')


def rollback(base_head: str, destinations: list[Path], restore_timer: bool) -> None:
    say('ROLLBACK=BEGIN')
    run(['git', 'reset', '--hard', base_head], check=False)
    ARTIFACT.unlink(missing_ok=True)
    for destination in destinations:
        if destination.is_file():
            destination.unlink()
    for parent in sorted({path.parent for path in destinations}, key=lambda p: len(p.parts), reverse=True):
        try:
            parent.rmdir()
        except OSError:
            pass
    if restore_timer:
        run(['systemctl', 'enable', '--now', PHASE9_TIMER], check=False, timeout=60)
    say('ROLLBACK=COMPLETE')


def main() -> int:
    if maybe_finish_existing_push():
        return 0

    base_head, _ = require_clean_and_synced()
    runtime = load(ROOT / 'PROJECT_RUNTIME.json')
    pointer = runtime['canonical_runtime_pointer']
    if pointer.get('next_safe_step') != NEXT:
        raise RuntimeError('UNEXPECTED_NEXT_SAFE_STEP:' + str(pointer.get('next_safe_step')))
    if pointer.get('era57_opened') is not False:
        raise RuntimeError('ERA57_MUST_REMAIN_CLOSED')
    if pointer.get('pre_era57_hardening_closed') is not True:
        raise RuntimeError('GENERAL_RUNTIME_HARDENING_MUST_BE_CLOSED')

    say('STEP=VALIDATE_PHASE9_DEPENDENCY_PROOF')
    dependency = validate_dependency_result()

    say('STEP=FREEZE_ACTIVE_RUNTIME_HASHES')
    active_runtime, active_data, protected_before = protected_inventory()
    db_hash_before = sha256(PRODUCTION_DB)
    phase9_timer_before = unit_state(PHASE9_TIMER)
    phase9_service_before = unit_state(PHASE9_SERVICE)
    news_timer_before = unit_state(NEWS_TIMER)
    transient_before = unit_state(TRANSIENT_UNIT)
    timer_fragment_before = fragment_hash(phase9_timer_before)
    service_fragment_before = fragment_hash(phase9_service_before)
    if phase9_timer_before.get('ActiveState') != 'active' or phase9_timer_before.get('UnitFileState') != 'enabled':
        raise RuntimeError('PHASE9_TIMER_NOT_ACTIVE_ENABLED_AT_APPLY')
    if news_timer_before.get('ActiveState') != 'active' or news_timer_before.get('UnitFileState') != 'enabled':
        raise RuntimeError('NEWS_TIMER_BASELINE_NOT_ACTIVE_ENABLED')

    timer_mutated = False
    committed = False
    archive_destinations: list[Path] = []
    try:
        say('STEP=DISABLE_INERT_PHASE9_TIMER')
        result = run(['systemctl', 'disable', '--now', PHASE9_TIMER], timeout=60)
        if result.stdout.strip():
            say(result.stdout.strip())
        timer_mutated = True
        phase9_timer_after = unit_state(PHASE9_TIMER)
        if phase9_timer_after.get('ActiveState') != 'inactive':
            raise RuntimeError('PHASE9_TIMER_NOT_INACTIVE')
        if phase9_timer_after.get('UnitFileState') != 'disabled':
            raise RuntimeError('PHASE9_TIMER_NOT_DISABLED')

        say('STEP=CLEAR_FAILED_TRANSIENT_UNIT')
        run(['systemctl', 'stop', TRANSIENT_UNIT], check=False, timeout=30)
        run(['systemctl', 'reset-failed', TRANSIENT_UNIT], check=False, timeout=30)
        run(['systemctl', 'daemon-reload'], timeout=30)
        transient_after = unit_state(TRANSIENT_UNIT)
        if transient_after.get('ActiveState') == 'failed':
            raise RuntimeError('TRANSIENT_UNIT_STILL_FAILED')

        say('STEP=REMOVE_DISPOSABLE_FILES')
        removed = remove_disposable_files()

        say('STEP=ARCHIVE_ONE_OFF_TOOLS')
        moved, absent = archive_one_off_files()
        archive_destinations = [ROOT / item['destination'] for item in moved]

        say('STEP=RECLASSIFY_ACTIVE_SURFACE')
        classification = reclassify(active_runtime, active_data)

        say('STEP=RUN_POST_HYGIENE_STRESS')
        stress = run_stress()

        say('STEP=VERIFY_PROTECTED_HASHES')
        protected_after = {
            rel: sha256(ROOT / rel)
            for rel in active_runtime + active_data
        }
        if protected_before != protected_after:
            raise RuntimeError('PROTECTED_ACTIVE_SURFACE_HASH_CHANGED')
        db_hash_after = sha256(PRODUCTION_DB)
        if db_hash_before != db_hash_after:
            raise RuntimeError('PRODUCTION_DB_HASH_CHANGED')

        phase9_service_after = unit_state(PHASE9_SERVICE)
        news_timer_after = unit_state(NEWS_TIMER)
        if fragment_hash(phase9_timer_after) != timer_fragment_before:
            raise RuntimeError('PHASE9_TIMER_FRAGMENT_CHANGED')
        if fragment_hash(phase9_service_after) != service_fragment_before:
            raise RuntimeError('PHASE9_SERVICE_FRAGMENT_CHANGED')
        if news_timer_after.get('ActiveState') != 'active' or news_timer_after.get('UnitFileState') != 'enabled':
            raise RuntimeError('NEWS_TIMER_STATE_CHANGED')

        now = datetime.now(timezone.utc).isoformat()
        artifact = {
            'schema': 'pre_era57_repo_pipeline_hygiene_closure_v1',
            'timestamp_utc': now,
            'work_unit': WORK,
            'status': 'CLOSED_VERIFIED',
            'result': RESULT,
            'phase9_dependency_proof': {
                'decision': dependency['decision'],
                'blocking_reasons': dependency.get('blocking_reasons', []),
                'checks': dependency['checks'],
            },
            'phase9_timer': {
                'before': phase9_timer_before,
                'after': phase9_timer_after,
                'disabled': True,
                'inactive': True,
                'fragment_hash_unchanged': True,
            },
            'phase9_service': {
                'before': phase9_service_before,
                'after': phase9_service_after,
                'fragment_hash_unchanged': True,
                'script_preserved': True,
            },
            'transient_unit': {
                'unit': TRANSIENT_UNIT,
                'before': transient_before,
                'after': transient_after,
                'failed_state_cleared': transient_after.get('ActiveState') != 'failed',
            },
            'disposable_cleanup': {
                'classified_expected_count': 25,
                'removed_count': len(removed),
                'removed': removed,
                'remaining_count': 0,
            },
            'one_off_archive': {
                'moved_count': len(moved),
                'moved': moved,
                'already_absent': absent,
                'reusable_tools_preserved': [
                    'tools/general_runtime_surface_classifier_v1.py',
                    'tools/general_systemd_dependency_check_v1.py',
                    'tests/general_runtime_stress_harness_v1.py',
                ],
            },
            'active_surface_post_hygiene': classification,
            'post_hygiene_stress': stress,
            'protected_active_runtime_count': len(active_runtime),
            'protected_active_runtime_data_count': len(active_data),
            'protected_hashes_before': protected_before,
            'protected_hashes_after': protected_after,
            'protected_hashes_unchanged': True,
            'production_db_hash_before': db_hash_before,
            'production_db_hash_after': db_hash_after,
            'production_database_mutation': False,
            'news_timer_unchanged_active_enabled': True,
            'unclassified_blind_delete': False,
            'broad_authority_expansion': False,
            'live_source_fetch_authorized': False,
            'era57_opened': False,
            'era57_opening_decision_ready': True,
            'next_safe_step': NEXT,
        }

        say('STEP=UPDATE_CANONICAL_STATE')
        save(ARTIFACT, artifact)
        update_canonical(artifact, now)

        protected_final = {
            rel: sha256(ROOT / rel)
            for rel in active_runtime + active_data
        }
        if protected_final != protected_before:
            raise RuntimeError('CANONICAL_UPDATE_TOUCHED_PROTECTED_RUNTIME_DATA')

        say('STEP=POST_AUDIT')
        run(['git', 'diff', '--check'])
        runtime_after = load(ROOT / 'PROJECT_RUNTIME.json')
        pointer_after = runtime_after['canonical_runtime_pointer']
        if pointer_after.get('next_safe_step') != NEXT:
            raise RuntimeError('NEXT_SAFE_STEP_DRIFT')
        if pointer_after.get('era57_opened') is not False:
            raise RuntimeError('ERA57_OPENED_UNEXPECTEDLY')
        if pointer_after.get('repo_hygiene_ready_for_era57') is not True:
            raise RuntimeError('REPO_HYGIENE_NOT_CLOSED')
        if pointer_after.get('pipeline_hygiene_ready_for_era57') is not True:
            raise RuntimeError('PIPELINE_HYGIENE_NOT_CLOSED')

        say('STEP=GIT_COMMIT_AND_SEAL')
        run([
            'git', 'add',
            'PROJECT_RUNTIME.json',
            'PROJECT_HISTORY.json',
            '04_ALMANAC.md',
            '06_PROJECT_MASTER_STATE.md',
            '07_PROJECT_HANDOFF.md',
            ARTIFACT_REL,
        ])
        run(['git', 'diff', '--cached', '--check'])
        run(['git', 'commit', '-m', 'PRE_ERA57_HYGIENE | REPO AND PIPELINE HYGIENE CLOSED'])
        committed = True
        final_head = git_value('rev-parse', 'HEAD')
        if run(['git', 'rev-parse', '-q', '--verify', f'refs/tags/{TAG}'], check=False).returncode == 0:
            raise RuntimeError('FINAL_TAG_ALREADY_EXISTS')
        run(['git', 'tag', '-a', TAG, '-m', 'Pre-ERA57 repository and pipeline hygiene closed and verified'])

        say('STEP=PUSH_AND_REMOTE_VERIFY')
        run(['git', 'push', 'origin', 'main', TAG], capture=False, timeout=600)
        run(['git', 'fetch', 'origin', 'main', '--tags'])
        if git_value('rev-parse', 'origin/main') != final_head:
            raise RuntimeError('REMOTE_HEAD_VERIFY_FAILED')
        if git_value('rev-parse', f'{TAG}^{{}}') != final_head:
            raise RuntimeError('REMOTE_TAG_VERIFY_FAILED')
        if git_value('status', '--porcelain'):
            raise RuntimeError('WORKTREE_NOT_CLEAN_AFTER_PUSH')

        say('PRE_ERA57_REPO_PIPELINE_HYGIENE=CLOSED_VERIFIED')
        say('PHASE9_TIMER=DISABLED_INACTIVE')
        say('TRANSIENT_FAILED_UNIT=CLEARED')
        say(f'DISPOSABLE_REMOVED={len(removed)}')
        say('DISPOSABLE_REMAINING=0')
        say(f'ONE_OFF_TOOLS_ARCHIVED={len(moved)}')
        say('ACTIVE_RUNTIME=14_UNCHANGED')
        say('ACTIVE_RUNTIME_DATA=12_UNCHANGED')
        say('POST_HYGIENE_STRESS=10/10')
        say('PRODUCTION_DATABASE_MUTATION=false')
        say('LIVE_FETCH_AUTHORIZED=false')
        say('ERA57_OPENED=false')
        say('ERA57_OPENING_DECISION_READY=true')
        say(f'NEXT_SAFE_STEP={NEXT}')
        say(f'FINAL_HEAD={final_head}')
        say(f'FINAL_SEAL={TAG}')
        say('REMOTE_VERIFY=OK')
        return 0
    except Exception:
        if not committed:
            rollback(base_head, archive_destinations, timer_mutated)
        else:
            say('LOCAL_COMMIT_CREATED_PUSH_OR_VERIFY_FAILED=true')
            say('RETRY_SAME_COMMAND_TO_RESUME_PUSH=true')
        raise


if __name__ == '__main__':
    raise SystemExit(main())
