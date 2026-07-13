#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path('/root/tokenoskobi_clean_v1')
TIMER = 'tokenoskobi-phase9-observation-runtime.timer'
SERVICE = 'tokenoskobi-phase9-observation-runtime.service'
SCRIPT_REL = 'tools/phase9_commercial_observation_runtime.py'
SCRIPT = ROOT / SCRIPT_REL
CONFIG = ROOT / 'data/phase9_commercial_observation_config.json'
DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
OUT = Path('/tmp/pre_era57_phase9_timer_dependency_check_v1.json')
ACTIVE_PREFIXES = ('tools/', 'core/', 'runtime/', 'config/', 'active_panel_8096/', 'systemd/', 'systemd_drafts/', '.github/workflows/')
SELF = {SCRIPT_REL, 'tools/phase9_dependency_check_fast_v1.py', 'tools/run_phase9_dependency_check_v1.sh', 'tools/general_systemd_dependency_check_v1.py'}


def say(text: str) -> None:
    print(text, flush=True)


def run(argv: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def show(unit: str, props: list[str]) -> dict[str, str]:
    argv = ['systemctl', 'show', unit, '--no-pager']
    for prop in props:
        argv += ['-p', prop]
    result = run(argv)
    if result.returncode != 0:
        raise RuntimeError(f'SYSTEMCTL_SHOW_FAILED:{unit}:{result.stderr.strip()}')
    return {line.split('=', 1)[0]: line.split('=', 1)[1] for line in result.stdout.splitlines() if '=' in line}


def active_repo_consumers(patterns: tuple[str, ...]) -> list[str]:
    result = run(['git', 'ls-files'], timeout=20)
    if result.returncode != 0:
        raise RuntimeError('GIT_LS_FILES_FAILED')
    found = set()
    for rel in result.stdout.splitlines():
        if rel in SELF or not rel.startswith(ACTIVE_PREFIXES):
            continue
        path = ROOT / rel
        try:
            if not path.is_file() or path.stat().st_size > 2_000_000:
                continue
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        if any(pattern in text for pattern in patterns):
            found.add(rel)
    return sorted(found)


def external_systemd_consumers() -> list[str]:
    names = set()
    for unit in (TIMER, SERVICE):
        result = run(['systemctl', 'list-dependencies', '--reverse', '--all', '--plain', '--no-pager', unit])
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            text = line.strip().lstrip('●○*+- ')
            if not text or text in {TIMER, SERVICE} or text.endswith('.target'):
                continue
            if text.endswith(('.service', '.timer', '.socket', '.path')):
                names.add(text)
    return sorted(names)


def external_filesystem_consumers(patterns: tuple[str, ...], fragments: set[str]) -> list[str]:
    found = set()
    roots = [Path('/etc/systemd/system'), Path('/etc/cron.d'), Path('/etc/cron.hourly'), Path('/etc/cron.daily')]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob('*'):
            try:
                if str(path) in fragments:
                    continue
                if path.is_symlink():
                    target = os.readlink(path)
                    if path.name in {TIMER, SERVICE} or target.endswith('/' + TIMER) or target.endswith('/' + SERVICE):
                        continue
                    if any(pattern in target or pattern in str(path) for pattern in patterns):
                        found.add(str(path))
                    continue
                if not path.is_file() or path.stat().st_size > 1_000_000:
                    continue
                text = path.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            if any(pattern in text for pattern in patterns):
                found.add(str(path))
    return sorted(found)


def main() -> int:
    say('STEP=LOAD_INPUTS')
    script_text = SCRIPT.read_text(encoding='utf-8', errors='replace')
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    script_inert = all(token in script_text for token in ('"runtime_enabled": False', '"api_calls": 0', '"rpc_calls": 0', '"fetch_calls": 0', '"paper_allowed": False', '"live_allowed": False', 'INERT_INSTALL_ONLY_NO_RUNTIME_LOOP'))
    config_flags = {k: config.get(k) for k in ('runtime_enabled', 'api_rpc_fetch_enabled', 'live_allowed', 'paper_allowed', 'panel_apply_allowed')}
    config_inert = all(v is False for v in config_flags.values())

    say('STEP=READ_SYSTEMD')
    timer = show(TIMER, ['ActiveState', 'SubState', 'UnitFileState', 'Triggers', 'FragmentPath'])
    service = show(SERVICE, ['ActiveState', 'SubState', 'UnitFileState', 'TriggeredBy', 'ExecStart', 'FragmentPath'])
    binding_ok = str(SCRIPT) in service.get('ExecStart', '') and SERVICE in timer.get('Triggers', '') and TIMER in service.get('TriggeredBy', '')

    patterns = (TIMER, SERVICE, SCRIPT_REL, str(SCRIPT))
    say('STEP=SCAN_ACTIVE_REPO')
    repo_consumers = active_repo_consumers(patterns)
    say('STEP=SCAN_SYSTEMD_DEPENDENCIES')
    systemd_consumers = external_systemd_consumers()
    say('STEP=SCAN_EXTERNAL_REFERENCES')
    fragments = {timer.get('FragmentPath', ''), service.get('FragmentPath', '')}
    filesystem_consumers = external_filesystem_consumers(patterns, fragments)

    db_before = sha256(DB)
    db_after = sha256(DB)
    blocking = []
    if not binding_ok:
        blocking.append('SYSTEMD_BINDING_NOT_PROVEN')
    if not script_inert:
        blocking.append('SCRIPT_NOT_PROVEN_INERT')
    if not config_inert:
        blocking.append('CONFIG_NOT_PROVEN_INERT')
    if repo_consumers:
        blocking.append('ACTIVE_REPO_CONSUMERS_PRESENT')
    if systemd_consumers:
        blocking.append('EXTERNAL_SYSTEMD_CONSUMERS_PRESENT')
    if filesystem_consumers:
        blocking.append('EXTERNAL_FILESYSTEM_CONSUMERS_PRESENT')

    timer_enabled = timer.get('UnitFileState') == 'enabled'
    timer_active = timer.get('ActiveState') == 'active'
    decision = 'REVIEW_REQUIRED' if blocking else ('SAFE_TO_DISABLE_AND_STOP' if timer_enabled or timer_active else 'ALREADY_INACTIVE_NO_ACTION')

    result = {
        'schema': 'phase9_dependency_check_fast_v1',
        'mode': 'READ_ONLY',
        'decision': decision,
        'blocking_reasons': blocking,
        'checks': {
            'systemd_binding_proven': binding_ok,
            'script_declares_inert': script_inert,
            'config_inert': config_inert,
            'config_flags': config_flags,
            'timer_enabled': timer_enabled,
            'timer_active': timer_active,
            'active_repo_consumer_count': len(repo_consumers),
            'external_systemd_consumer_count': len(systemd_consumers),
            'external_filesystem_consumer_count': len(filesystem_consumers),
            'production_db_hash_unchanged': db_before == db_after,
            'production_mutation': False,
            'systemd_mutation': False,
            'era57_opened': False,
        },
        'active_repo_consumers': repo_consumers,
        'external_systemd_consumers': systemd_consumers,
        'external_filesystem_consumers': filesystem_consumers,
        'timer': timer,
        'service': service,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    say('STEP=DONE')
    print('DECISION=' + decision)
    print('BLOCKING_REASONS=' + ','.join(blocking))
    print('SYSTEMD_BINDING_PROVEN=' + str(binding_ok).lower())
    print('SCRIPT_DECLARES_INERT=' + str(script_inert).lower())
    print('CONFIG_INERT=' + str(config_inert).lower())
    print('ACTIVE_REPO_CONSUMERS=' + str(len(repo_consumers)))
    print('EXTERNAL_SYSTEMD_CONSUMERS=' + str(len(systemd_consumers)))
    print('EXTERNAL_FILESYSTEM_CONSUMERS=' + str(len(filesystem_consumers)))
    print('TIMER_ENABLED=' + str(timer_enabled).lower())
    print('TIMER_ACTIVE=' + str(timer_active).lower())
    print('PRODUCTION_MUTATION=false')
    print('SYSTEMD_MUTATION=false')
    print('ERA57_OPENED=false')
    return 0 if decision != 'REVIEW_REQUIRED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
