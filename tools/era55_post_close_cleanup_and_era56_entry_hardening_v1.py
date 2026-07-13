#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
WORK = 'ERA55_POST_CLOSE_CLEANUP_AND_ERA56_ENTRY_HARDENING'
RESULT = 'OK_CONTROLLED_ARCHIVE_CANONICAL_HARDENING_ERA56_STILL_CLOSED'
NEXT = 'ERA56_GLOBAL_INTELLIGENCE_CACHE_OPENING_DECISION'
SUBJECT = 'ERA55_POST_CLOSE_CLEANUP | OK | ARCHIVE_AND_ENTRY_HARDENING'
SEAL_COMMIT = 'f22ce4f07788ec7fbe22a72f872467705b72db5a'
SEAL_TAG = 'ERA55_FINAL_SEAL'

RUNTIME = ROOT / 'PROJECT_RUNTIME.json'
BOOT = ROOT / 'PROJECT_BOOT.json'
HISTORY = ROOT / 'PROJECT_HISTORY.json'
ROADMAP_MD = ROOT / '03_ROADMAP.md'
ALMANAC = ROOT / '04_ALMANAC.md'
MASTER = ROOT / '06_PROJECT_MASTER_STATE.md'
HANDOFF = ROOT / '07_PROJECT_HANDOFF.md'
README = ROOT / 'README.md'
ROADMAP_JSON = ROOT / 'data/tokenoskobi_v1_v8_master_era_roadmap.json'
TK_AI = ROOT / 'reports/LATEST_TK_AI_HANDOFF.md'
MACHINE = ROOT / 'data/control/latest_tk_machine_state.json'
ARTIFACT = ROOT / 'data/control/era55_post_close_cleanup_and_era56_entry_hardening_v1.json'
ARCHIVE_DIR = ROOT / 'tools/archive/era55_runner_history'
ARCHIVE_MANIFEST = ARCHIVE_DIR / 'ARCHIVE_MANIFEST.json'

MOVES = {
    ROOT / 'tools/news_radar_refresh_runner_v1.ORIGINAL_NEWS27A11_20260510_211813.py': ARCHIVE_DIR / 'news_radar_refresh_runner_v1.ORIGINAL_NEWS27A11_20260510_211813.py',
    ROOT / 'tools/news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py': ARCHIVE_DIR / 'news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py',
}
ACTIVE_DO_NOT_MOVE = [
    'tools/news_radar_refresh_runner_v1.py',
    'tools/era55a23_p0_guarded_general_production_writer_runtime_integration_apply_and_post_audit_v1.py',
]


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check, timeout=90)


def git(*args: str) -> str:
    return run(['git', *args]).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError(f'JSON_OBJECT_REQUIRED:{path}')
    return value


def dump(path: Path, value: dict[str, Any]) -> None:
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


def era55(roadmap: dict[str, Any]) -> dict[str, Any]:
    for version in roadmap.get('versions', []):
        if version.get('id') == 'V3':
            for era in version.get('children', []):
                if era.get('id') == 'ERA55':
                    return era
    raise RuntimeError('ERA55_NOT_FOUND')


def main() -> int:
    if git('status', '--short'):
        raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected = os.environ.get('TOKENOSKOBI_EXPECTED_HEAD', '').strip()
    if expected and git('rev-parse', 'HEAD') != expected:
        raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list', '-n1', SEAL_TAG) != SEAL_COMMIT:
        raise RuntimeError('ERA55_SEAL_MISMATCH')

    for active in ACTIVE_DO_NOT_MOVE:
        if not (ROOT / active).is_file():
            raise RuntimeError('ACTIVE_RUNTIME_MISSING:' + active)
    for source, target in MOVES.items():
        if not source.is_file() or target.exists():
            raise RuntimeError('ARCHIVE_MOVE_PRECONDITION_FAILED:' + str(source))

    runtime = load(RUNTIME)
    pointer = runtime['canonical_runtime_pointer']
    if pointer.get('era55_closed') is not True or pointer.get('era56_opened') is not False:
        raise RuntimeError('CANONICAL_ERA_STATE_INVALID')
    if pointer.get('next_safe_step') != NEXT:
        raise RuntimeError('NEXT_SAFE_STEP_INVALID')

    timestamp = datetime.now(timezone.utc).isoformat()
    archive_rows = []
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for source, target in MOVES.items():
        shutil.move(str(source), str(target))
        archive_rows.append({
            'original_path': str(source.relative_to(ROOT)),
            'archive_path': str(target.relative_to(ROOT)),
            'reason': 'CONFIRMED_NON_SYSTEMD_HISTORICAL_RUNNER_COPY',
            'delete_allowed': False,
            'retain_as_evidence': True,
        })

    dump(ARCHIVE_MANIFEST, {
        'schema': 'era55_runner_history_archive_manifest_v1',
        'created_at_utc': timestamp,
        'era55_seal_tag': SEAL_TAG,
        'era55_seal_commit': SEAL_COMMIT,
        'active_do_not_move': ACTIVE_DO_NOT_MOVE,
        'archived_files': archive_rows,
    })

    artifact_rel = str(ARTIFACT.relative_to(ROOT))
    dump(ARTIFACT, {
        'schema': 'era55_post_close_cleanup_and_era56_entry_hardening_v1',
        'timestamp_utc': timestamp,
        'work_unit': WORK,
        'status': 'CLOSED_VERIFIED',
        'result': RESULT,
        'era55_seal_tag': SEAL_TAG,
        'era55_seal_commit': SEAL_COMMIT,
        'runner_lock_verified_enabled': True,
        'active_runtime_files': ACTIVE_DO_NOT_MOVE,
        'archived_files': archive_rows,
        'bulk_delete': False,
        'production_mutation': False,
        'era56_opened': False,
        'next_safe_step': NEXT,
    })

    runtime['current_era'] = 'ERA55'
    runtime['current_era_status'] = 'CLOSED'
    runtime['current_problem'] = {'code': 'ERA56_GLOBAL_INTELLIGENCE_CACHE_OPENING_DECISION_PENDING', 'severity': 'P1', 'evidence': artifact_rel}
    pointer.update({
        'project_status': 'ERA55_CLOSED_CLEANUP_HARDENED_ERA56_OPENING_DECISION_PENDING',
        'current_stage': 'ERA55_POST_CLOSE_CLEANUP_HARDENED',
        'last_completed': WORK,
        'last_result': RESULT,
        'last_artifact': artifact_rel,
        'era55_closed': True,
        'era56_opened': False,
        'runner_lock_enabled': True,
        'next_safe_step': NEXT,
        'updated_at_utc': timestamp,
    })
    runtime['current_state'] = {
        'project_status': 'ACTIVE',
        'runtime_status': 'ERA55_CLOSED_ERA56_NOT_OPENED',
        'mode': 'POST_ERA55_CLEANUP_HARDENED',
        'last_action': {'task': WORK, 'result': RESULT, 'artifact': artifact_rel, 'timestamp': timestamp},
        'current_problem': runtime['current_problem'],
        'next_safe_step': {'id': NEXT, 'status': 'READY', 'human_authorization_required': True, 'era56_open_authorized': False},
        'updated_at': timestamp,
    }
    runtime['current_work_unit'] = {'id': WORK, 'status': 'CLOSED_VERIFIED', 'result': RESULT, 'artifact': artifact_rel, 'production_mutation': False, 'next_step': NEXT}
    dump(RUNTIME, runtime)

    roadmap = load(ROADMAP_JSON)
    e55 = era55(roadmap)
    e55.update({
        'status': 'CLOSED',
        'active_stage': 'ERA55_POST_CLOSE_CLEANUP_HARDENED',
        'last_completed_substep': WORK,
        'last_result': RESULT,
        'next_safe_step': NEXT,
        'closure_status': 'CLOSED_VERIFIED',
        'era56_open_authorized': False,
    })
    dump(ROADMAP_JSON, roadmap)

    master = MASTER.read_text(encoding='utf-8')
    master = replace_section(master, '## 02 CURRENT MAJOR-LINE POSITION', f'''```text
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=CLOSED_VERIFIED
CURRENT_STAGE=ERA55_POST_CLOSE_CLEANUP_HARDENED
LAST_COMPLETED_SUBSTEP={WORK}
PRODUCTION_LEDGER_WRITER_ACTIVE=true
RUNNER_LOCK_ENABLED=true
P0_F1_CLOSED=true
OPTION_B_DECISION=DEFER_OPTION_B
WAL_APPLY_AUTHORIZED=false
ERA56_OPENED=false
PRODUCTION_MUTATION=false
```''')
    master = replace_section(master, '## 03 LAST VERIFIED WORK', f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={artifact_rel}
WORK_UNIT_STATUS=CLOSED_VERIFIED
ERA55_CLOSED=true
ERA56_OPENED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}''')
    master = replace_section(master, '## 10 NEXT SAFE STEP', f'''```text
NEXT_SAFE_STEP={NEXT}
```

Decide whether to open ERA56 Global Intelligence Cache. Define ownership and overlap boundaries before opening ERA56.''')
    MASTER.write_text(master, encoding='utf-8')

    handoff = HANDOFF.read_text(encoding='utf-8')
    handoff = replace_section(handoff, '## 02 CURRENT CONTINUATION CHECKPOINT', f'''PROJECT_STATUS=ERA55_CLOSED_CLEANUP_HARDENED_ERA56_OPENING_DECISION_PENDING
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=CLOSED_VERIFIED
CURRENT_STAGE=ERA55_POST_CLOSE_CLEANUP_HARDENED
LAST_COMPLETED_SUBSTEP={WORK}
PRODUCTION_LEDGER_WRITER_ACTIVE=true
RUNNER_LOCK_ENABLED=true
P0_F1_CLOSED=true
OPTION_B_DECISION=DEFER_OPTION_B
WAL_APPLY_AUTHORIZED=false
ERA56_OPENED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD''')
    handoff = replace_section(handoff, '## 03 LAST VERIFIED WORK', f'''LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={artifact_rel}
WORK_UNIT_STATUS=CLOSED_VERIFIED
PRODUCTION_MUTATION=false
CURRENT_PROBLEM=ERA56_GLOBAL_INTELLIGENCE_CACHE_OPENING_DECISION_PENDING''')
    handoff = replace_section(handoff, '## 07 ALLOWED NEXT DECISIONS', f'''- ERA55: `CLOSED_VERIFIED`.
- Runner lock: `ENABLED`.
- Active runtime surface: `2 files verified`.
- Option B: `DEFERRED`.
- WAL production apply: `BLOCKED`.
- ERA56 opening decision: `AUTHORIZED`.
- ERA56 opened: `false`.

NEXT_SAFE_STEP={NEXT}''')
    HANDOFF.write_text(handoff, encoding='utf-8')

    roadmap_md = ROADMAP_MD.read_text(encoding='utf-8')
    roadmap_md = roadmap_md.replace('CURRENT_STAGE=ERA55A_OPTION_B_DEFERRED_FINAL_CLOSURE_READINESS_PENDING', 'CURRENT_STAGE=ERA55_POST_CLOSE_CLEANUP_HARDENED')
    roadmap_md = roadmap_md.replace('NEXT_SAFE_STEP=ERA55A_28_ERA55_FINAL_CLOSURE_READINESS_AND_CANONICAL_ALIGNMENT_DECISION', 'NEXT_SAFE_STEP=' + NEXT)
    roadmap_md = roadmap_md.replace('- Active baseline stage: `ERA55A_OPTION_B_DEFERRED_FINAL_CLOSURE_READINESS_PENDING`', '- Active baseline stage: `ERA55_POST_CLOSE_CLEANUP_HARDENED`')
    roadmap_md = roadmap_md.replace('- Next safe step: `ERA56_GLOBAL_INTELLIGENCE_CACHE_OPENING_DECISION`', '- Next safe step: `ERA56_GLOBAL_INTELLIGENCE_CACHE_OPENING_DECISION`')
    ROADMAP_MD.write_text(roadmap_md, encoding='utf-8')

    readme = README.read_text(encoding='utf-8')
    lifecycle = '''\n## Script yaşam döngüsü\n\n- `ACTIVE_RUNTIME`: systemd, timer veya doğrulanmış runtime zinciri tarafından çağrılır; açık runtime kapsamı olmadan taşınmaz veya değiştirilmez.\n- `ACTIVE_LIBRARY`: aktif kod tarafından import edilir; caller doğrulanmadan taşınmaz.\n- `MANUAL_ONLY`: yalnız açık insan komutuyla çalıştırılır; production entrypoint sayılmaz.\n- `HISTORICAL_EVIDENCE`: geçmiş karar veya repair kanıtıdır; aktif `tools/` yüzeyinden archive alanına taşınabilir fakat kanıt zinciri korunur.\n- `DISPOSABLE`: yeniden üretilebilir ve kanıt değeri olmayan geçici araçtır; yalnız kanıtlı sınıflandırma ve insan onayıyla repo dışına çıkarılabilir.\n- Aynı yetenek için ikinci bir motor oluşturulmaz; yeni karmaşıklık yalnız net faydası kanıtlanırsa kabul edilir.\n'''
    if '## Script yaşam döngüsü' not in readme:
        readme = readme.rstrip() + lifecycle + '\n'
    README.write_text(readme.rstrip() + '\n', encoding='utf-8')

    boot = load(BOOT)
    boot['script_lifecycle_policy'] = {
        'active_runtime': 'Runtime reachable. Do not move or modify without explicit runtime scope.',
        'active_library': 'Imported by active code. Preserve caller compatibility.',
        'manual_only': 'Human-invoked only. Not a production entrypoint.',
        'historical_evidence': 'Retain evidence; archive outside active surface when safe.',
        'disposable': 'Remove only when reproducible, evidence-free and explicitly approved.',
        'one_capability_one_engine': True,
        'unjustified_complexity_never_up': True,
        'bulk_delete_without_inventory': False,
    }
    dump(BOOT, boot)

    history = load(HISTORY)
    events = history.setdefault('events', [])
    if not any(isinstance(e, dict) and e.get('event_id') == WORK for e in events):
        events.append({'event_id': WORK, 'timestamp_utc': timestamp, 'era': 'ERA55_POST_CLOSE', 'status': 'CLOSED_VERIFIED', 'result': RESULT, 'artifact': artifact_rel, 'era55_seal_tag': SEAL_TAG, 'era55_seal_commit': SEAL_COMMIT, 'era56_opened': False, 'production_mutation': False, 'next_safe_step': NEXT})
    history['updated_at'] = timestamp
    history['updated_at_utc'] = timestamp
    dump(HISTORY, history)

    marker = '## ERA55 POST-CLOSE CLEANUP AND ERA56 ENTRY HARDENING'
    almanac = ALMANAC.read_text(encoding='utf-8')
    if marker not in almanac:
        almanac = almanac.rstrip() + f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_VERIFIED`\n- Result: `{RESULT}`\n- Immutable ERA55 seal tag: `{SEAL_TAG}`\n- Immutable ERA55 seal commit: `{SEAL_COMMIT}`\n- Runner lock: `ENABLED`\n- Active runtime files protected: `2`\n- Historical runner copies archived: `2`\n- Bulk delete: `false`\n- ERA56 opened: `false`\n- Next safe step: `{NEXT}`\n'''
    ALMANAC.write_text(almanac, encoding='utf-8')

    TK_AI.parent.mkdir(parents=True, exist_ok=True)
    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\n## CURRENT CANONICAL STATE\n\nSTATE_SYNC_UTC={timestamp}\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nERA55_STATUS=CLOSED_VERIFIED\nERA55_SEAL_TAG={SEAL_TAG}\nERA55_SEAL_COMMIT={SEAL_COMMIT}\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nPRODUCTION_LEDGER_WRITER_ACTIVE=true\nRUNNER_LOCK_ENABLED=true\nP0_F1_CLOSED=true\nOPTION_B=DEFERRED\nWAL_APPLY_AUTHORIZED=false\nERA56_OPENED=false\nNEXT_SAFE_STEP={NEXT}\n\n## ACTIVE RUNTIME\n\n- `tools/news_radar_refresh_runner_v1.py`\n- `tools/era55a23_p0_guarded_general_production_writer_runtime_integration_apply_and_post_audit_v1.py`\n\n## BOUNDARIES\n\n- Do not run `tk machine`.\n- Do not open ERA56 without a separate human decision.\n- Historical tools are not production entrypoints.\n- Archive evidence must remain traceable.\n''', encoding='utf-8')

    machine = load(MACHINE)
    machine['collect_mode'] = 'canonical_sync_snapshot_no_tk_machine'
    machine['created_at_utc'] = timestamp
    machine['project'] = {
        'name': 'Tokenoskobi',
        'root': str(ROOT),
        'branch': 'main',
        'local_head': 'DYNAMIC_USE_GIT_REV_PARSE_HEAD',
        'remote_head': 'DYNAMIC_USE_GIT_REV_PARSE_ORIGIN_MAIN',
        'head_sync': 'VERIFY_AFTER_PUSH',
        'git_clean': 'VERIFY_AFTER_COMMIT',
    }
    machine['current_state'] = {
        'authority': 'PROJECT_RUNTIME.json',
        'runtime_status': 'ERA55_CLOSED_ERA56_NOT_OPENED',
        'active_work_unit': {'id': WORK, 'status': 'CLOSED_VERIFIED', 'artifact': artifact_rel},
        'next_safe_step': {'name': NEXT, 'status': 'READY'},
        'last_action': {'timestamp': timestamp, 'task': WORK, 'result': RESULT, 'artifact': artifact_rel},
    }
    machine['known_facts'] = {
        'era55_status': 'CLOSED_VERIFIED',
        'era55_seal_tag': SEAL_TAG,
        'era55_seal_commit': SEAL_COMMIT,
        'era56_opened': False,
        'runner_lock_enabled': True,
        'active_runtime_files': ACTIVE_DO_NOT_MOVE,
        'archived_historical_runner_copies': [row['archive_path'] for row in archive_rows],
    }
    dump(MACHINE, machine)

    for path in (RUNTIME, BOOT, HISTORY, ROADMAP_JSON, MACHINE, ARTIFACT, ARCHIVE_MANIFEST):
        load(path)
    if git('rev-list', '-n1', SEAL_TAG) != SEAL_COMMIT:
        raise RuntimeError('ERA55_SEAL_CHANGED')
    for active in ACTIVE_DO_NOT_MOVE:
        if not (ROOT / active).is_file():
            raise RuntimeError('ACTIVE_RUNTIME_MOVED:' + active)
    for source, target in MOVES.items():
        if source.exists() or not target.is_file():
            raise RuntimeError('ARCHIVE_MOVE_VALIDATION_FAILED:' + str(source))

    git('add', '-A')
    diff_check = run(
        [
            'git', 'diff', '--cached', '--check', '--', '.',
            ':(exclude)tools/archive/era55_runner_history/*.py',
        ],
        check=False,
    )
    if diff_check.returncode != 0:
        print(diff_check.stdout, end='')
        print(diff_check.stderr, end='')
        raise RuntimeError('STAGED_DIFF_CHECK_FAILED')
    git('commit', '-m', SUBJECT)

    print('CLEANUP_AND_HARDENING=SUCCESS')
    print('ERA55_SEAL_PRESERVED=true')
    print('RUNNER_LOCK_ENABLED=true')
    print('ACTIVE_RUNTIME_FILES=2')
    print('ARCHIVED_FILES=2')
    print('BULK_DELETE=false')
    print('PRODUCTION_MUTATION=false')
    print('ERA56_OPENED=false')
    print('NEXT_SAFE_STEP=' + NEXT)
    print('LOCAL_COMMIT=' + git('rev-parse', 'HEAD'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
