#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
RUNTIME = ROOT / 'PROJECT_RUNTIME.json'
ROADMAP = ROOT / 'data/tokenoskobi_v1_v8_master_era_roadmap.json'
MASTER = ROOT / '06_PROJECT_MASTER_STATE.md'
HANDOFF = ROOT / '07_PROJECT_HANDOFF.md'
HISTORY = ROOT / 'PROJECT_HISTORY.json'
ALMANAC = ROOT / '04_ALMANAC.md'
ARTIFACT = ROOT / 'data/control/era55a28_final_closure_readiness_decision_v1.json'
WORK_UNIT = 'ERA55A_28_ERA55_FINAL_CLOSURE_READINESS_AND_CANONICAL_ALIGNMENT_DECISION'
NEXT = 'ERA55_FINAL_CLOSURE_AND_GITHUB_SEAL_DECISION'
RESULT = 'OK_ERA55_FINAL_CLOSURE_READINESS_CONFIRMED_NOT_YET_CLOSED'
SUBJECT = 'ERA55A28_DECISION | OK | FINAL_CLOSURE_READINESS_CONFIRMED'


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check, timeout=60)


def git(*args: str) -> str:
    return run(['git', *args]).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError(f'JSON_OBJECT_REQUIRED:{path}')
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def replace_section(text: str, heading: str, body: str) -> str:
    start = text.find(heading)
    if start < 0:
        raise RuntimeError(f'HEADING_MISSING:{heading}')
    end = text.find('\n## ', start + len(heading))
    if end < 0:
        end = len(text)
    return text[:start] + heading + '\n\n' + body.rstrip() + '\n' + text[end:]


def find_era55(roadmap: dict[str, Any]) -> dict[str, Any]:
    for version in roadmap.get('versions', []):
        if version.get('id') == 'V3':
            for era in version.get('children', []):
                if era.get('id') == 'ERA55':
                    return era
    raise RuntimeError('ERA55_NOT_FOUND')


def readiness() -> tuple[dict[str, bool], dict[str, Any], dict[str, Any]]:
    runtime = load(RUNTIME)
    roadmap = load(ROADMAP)
    pointer = runtime['canonical_runtime_pointer']
    era55 = find_era55(roadmap)
    checks = {
        'era55_open': era55.get('status') == 'OPEN',
        'runtime_era55_open': runtime.get('current_era') == 'ERA55' and runtime.get('current_era_status') == 'OPEN',
        'p0_f1_closed': pointer.get('p0_f1_closed') is True and era55.get('p0_f1_closed') is True,
        'writer_active': pointer.get('production_ledger_writer_active') is True and era55.get('production_ledger_writer_active') is True,
        'option_b_deferred': pointer.get('option_b_authorized') is False and era55.get('option_b_authorized') is False,
        'wal_apply_blocked': pointer.get('wal_apply_authorized') is False and era55.get('wal_apply_authorized') is False,
        'era24f_below_baseline': float(pointer.get('era24f_net_utility', 999)) < 95.0,
        'a27_is_last_completed': pointer.get('last_completed') == 'ERA55A_27_P1_WAL_BOUNDED_APPLY_READINESS_ROLLBACK_AND_AUTHORIZATION_DECISION',
        'a28_is_next': pointer.get('next_safe_step') == WORK_UNIT and era55.get('next_safe_step') == WORK_UNIT,
        'era56_not_open': era55.get('era56_open_authorized') is False,
        'closure_not_yet_authorized': era55.get('final_closure_authorized') is False,
    }
    return checks, runtime, roadmap


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    if git('status', '--short'):
        raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected = os.environ.get('TOKENOSKOBI_EXPECTED_HEAD', '').strip()
    if expected and git('rev-parse', 'HEAD') != expected:
        raise RuntimeError('HEAD_MISMATCH')

    checks, runtime, roadmap = readiness()
    ready = all(checks.values())
    print('A28_DRY_RUN=' + str(not args.apply).lower())
    print('ERA55_FINAL_CLOSURE_READY=' + str(ready).lower())
    print('ERA55_CLOSED=false')
    print('ERA56_OPENED=false')
    print('PRODUCTION_MUTATION=false')
    if not ready:
        print('FAILED_CHECKS=' + ','.join(k for k, v in checks.items() if not v))
        return 1
    if not args.apply:
        return 0

    timestamp = datetime.now(timezone.utc).isoformat()
    artifact_rel = str(ARTIFACT.relative_to(ROOT))
    artifact = {
        'schema': 'era55a28_final_closure_readiness_decision_v1',
        'timestamp_utc': timestamp,
        'work_unit': WORK_UNIT,
        'status': 'CLOSED_READY_FOR_FINAL_ERA55_CLOSURE_DECISION',
        'result': RESULT,
        'checks': checks,
        'era55_final_closure_ready': True,
        'era55_closed': False,
        'era56_opened': False,
        'production_mutation': False,
        'next_safe_step': NEXT,
    }
    atomic_json(ARTIFACT, artifact)

    pointer = runtime['canonical_runtime_pointer']
    runtime['current_problem'] = {'code': 'ERA55_FINAL_CLOSURE_AND_GITHUB_SEAL_DECISION_PENDING', 'severity': 'P1', 'evidence': artifact_rel}
    pointer.update({'project_status': 'ACTIVE_ERA55_FINAL_CLOSURE_DECISION_PENDING', 'current_stage': 'ERA55_FINAL_CLOSURE_DECISION_PENDING', 'last_completed': WORK_UNIT, 'last_result': RESULT, 'last_artifact': artifact_rel, 'next_safe_step': NEXT, 'updated_at_utc': timestamp})
    runtime['current_state']['current_problem'] = runtime['current_problem']
    runtime['current_state']['next_safe_step'] = {'id': NEXT, 'status': 'READY', 'human_authorization_required': True, 'era55_close_authorized': False, 'era56_open_authorized': False, 'production_mutation': False}
    runtime['current_state']['updated_at'] = timestamp
    runtime['current_work_unit'] = {'id': WORK_UNIT, 'status': 'CLOSED_READY_FOR_FINAL_ERA55_CLOSURE_DECISION', 'result': RESULT, 'artifact': artifact_rel, 'production_mutation': False, 'next_step': NEXT}
    atomic_json(RUNTIME, runtime)

    era55 = find_era55(roadmap)
    era55.update({'status': 'OPEN', 'active_stage': 'ERA55_FINAL_CLOSURE_DECISION_PENDING', 'last_completed_substep': WORK_UNIT, 'last_result': RESULT, 'next_safe_step': NEXT, 'final_closure_ready': True, 'final_closure_authorized': False, 'era56_open_authorized': False})
    atomic_json(ROADMAP, roadmap)

    master = MASTER.read_text(encoding='utf-8')
    master = replace_section(master, '## 03 LAST VERIFIED WORK', f'''```text
LAST_COMPLETED={WORK_UNIT}
LAST_RESULT={RESULT}
LAST_ARTIFACT={artifact_rel}
WORK_UNIT_STATUS=CLOSED_READY_FOR_FINAL_ERA55_CLOSURE_DECISION
PRODUCTION_MUTATION=false
ERA55_CLOSED=false
ERA56_OPENED=false
```

NEXT_SAFE_STEP={NEXT}''')
    master = replace_section(master, '## 10 NEXT SAFE STEP', f'''```text
NEXT_SAFE_STEP={NEXT}
```

Decide whether to close ERA55 and seal it on GitHub. Do not open ERA56 in the same decision step.''')
    MASTER.write_text(master, encoding='utf-8')

    handoff = HANDOFF.read_text(encoding='utf-8')
    handoff = handoff.replace('NEXT_SAFE_STEP=' + WORK_UNIT, 'NEXT_SAFE_STEP=' + NEXT)
    HANDOFF.write_text(handoff, encoding='utf-8')

    history = load(HISTORY)
    events = history.setdefault('events', [])
    if not any(isinstance(e, dict) and e.get('event_id') == 'ERA55A28_FINAL_CLOSURE_READINESS' for e in events):
        events.append({'event_id': 'ERA55A28_FINAL_CLOSURE_READINESS', 'timestamp_utc': timestamp, 'era': 'ERA55', 'work_unit': WORK_UNIT, 'status': 'CLOSED_READY_FOR_FINAL_ERA55_CLOSURE_DECISION', 'result': RESULT, 'artifact': artifact_rel, 'production_mutation': False, 'era55_closed': False, 'era56_opened': False, 'next_safe_step': NEXT})
    history['updated_at'] = timestamp
    history['updated_at_utc'] = timestamp
    atomic_json(HISTORY, history)

    marker = '## ERA55A_28 FINAL CLOSURE READINESS DECISION'
    almanac = ALMANAC.read_text(encoding='utf-8')
    if marker not in almanac:
        ALMANAC.write_text(almanac.rstrip() + f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_READY_FOR_FINAL_ERA55_CLOSURE_DECISION`\n- Result: `{RESULT}`\n- ERA55 final closure ready: `true`\n- ERA55 closed: `false`\n- ERA56 opened: `false`\n- Production mutation: `false`\n- Next safe step: `{NEXT}`\n''', encoding='utf-8')

    git('add', artifact_rel, str(RUNTIME.relative_to(ROOT)), str(ROADMAP.relative_to(ROOT)), str(MASTER.relative_to(ROOT)), str(HANDOFF.relative_to(ROOT)), str(HISTORY.relative_to(ROOT)), str(ALMANAC.relative_to(ROOT)))
    git('diff', '--cached', '--check')
    git('commit', '-m', SUBJECT)

    print('A28_APPLY=SUCCESS')
    print('ERA55_FINAL_CLOSURE_READY=true')
    print('ERA55_CLOSED=false')
    print('ERA56_OPENED=false')
    print('NEXT_SAFE_STEP=' + NEXT)
    print('LOCAL_COMMIT=' + git('rev-parse', 'HEAD'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
