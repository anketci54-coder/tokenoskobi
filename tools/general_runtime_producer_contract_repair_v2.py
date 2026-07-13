#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
SELF = ROOT / 'tools/general_runtime_producer_contract_repair_v2.py'
TRANSIENT_PRODUCER = ROOT / 'tools/news_source_ingestion_runner_v1.py'
DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
RUNTIME = ROOT / 'PROJECT_RUNTIME.json'
BOOT = ROOT / 'PROJECT_BOOT.json'
HISTORY = ROOT / 'PROJECT_HISTORY.json'
README = ROOT / 'README.md'
INDEX = ROOT / '01_INDEX.md'
ROADMAP = ROOT / '03_ROADMAP.md'
ALMANAC = ROOT / '04_ALMANAC.md'
MASTER = ROOT / '06_PROJECT_MASTER_STATE.md'
HANDOFF = ROOT / '07_PROJECT_HANDOFF.md'
TK_AI = ROOT / 'reports/LATEST_TK_AI_HANDOFF.md'
CONTRACT = ROOT / 'config/news_runtime_source_contract_v1.json'
ARTIFACT = ROOT / 'data/control/general_runtime_source_contract_v1.json'

WORK = 'GENERAL_RUNTIME_SOURCE_CONTRACT'
RESULT = 'OK_POLICY_DRIVEN_SOURCE_CONTRACT_LOCKED_NO_LIVE_FETCH'
NEXT = 'GENERAL_RUNTIME_SOURCE_ACTIVATION_DECISION'
TAG55 = 'ERA55_FINAL_SEAL'
SEAL55 = 'f22ce4f07788ec7fbe22a72f872467705b72db5a'
TAG56 = 'ERA56_FINAL_SEAL'
SEAL56 = '39dd684a71e39c4f05ce2a5113985fcf647718a0'


def run(args: list[str], check: bool = True, timeout: int = 120):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check, timeout=timeout)


def git(*args: str) -> str:
    return run(['git', *args]).stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError(f'JSON_OBJECT_REQUIRED:{path}')
    return value


def dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def replace_section(text: str, heading: str, body: str) -> str:
    start = text.find(heading)
    if start < 0:
        return text.rstrip() + '\n\n' + heading + '\n\n' + body.rstrip() + '\n'
    end = text.find('\n## ', start + len(heading))
    if end < 0:
        end = len(text)
    return text[:start] + heading + '\n\n' + body.rstrip() + '\n' + text[end:]


def table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in con.execute(f'PRAGMA table_info("{table}")').fetchall()}


def read_source_truth() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    try:
        integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity != 'ok':
            raise RuntimeError('DB_INTEGRITY_NOT_OK:' + str(integrity))

        registry_required = {
            'source_uid', 'source_name', 'source_class', 'source_url',
            'source_domain', 'trust_level', 'fetch_method', 'status',
            'priority', 'source_phase',
        }
        policy_required = {
            'source_uid', 'fetch_enabled', 'fetch_method',
            'min_interval_minutes', 'max_items_per_fetch',
            'timeout_seconds', 'retry_count', 'daily_call_budget',
            'requires_approval_for_live_fetch',
        }
        missing_registry = registry_required - table_columns(con, 'news_source_registry_v1')
        missing_policy = policy_required - table_columns(con, 'news_source_fetch_policy_v1')
        if missing_registry:
            raise RuntimeError('REGISTRY_CONTRACT_MISSING:' + ','.join(sorted(missing_registry)))
        if missing_policy:
            raise RuntimeError('POLICY_CONTRACT_MISSING:' + ','.join(sorted(missing_policy)))

        registry = [dict(row) for row in con.execute('''
            SELECT source_uid, source_name, source_class, source_url,
                   source_domain, trust_level, fetch_method, status,
                   priority, source_phase
            FROM news_source_registry_v1
            ORDER BY priority DESC, source_uid
        ''').fetchall()]
        policies = [dict(row) for row in con.execute('''
            SELECT source_uid, fetch_enabled, fetch_method,
                   min_interval_minutes, max_items_per_fetch,
                   timeout_seconds, retry_count, daily_call_budget,
                   requires_approval_for_live_fetch
            FROM news_source_fetch_policy_v1
            ORDER BY source_uid
        ''').fetchall()]
    finally:
        con.close()

    if not registry:
        raise RuntimeError('SOURCE_REGISTRY_EMPTY')
    if len(registry) != len(policies):
        raise RuntimeError('REGISTRY_POLICY_COUNT_MISMATCH')

    registry_ids = {str(row['source_uid']) for row in registry}
    policy_ids = {str(row['source_uid']) for row in policies}
    if registry_ids != policy_ids:
        raise RuntimeError('REGISTRY_POLICY_UID_MISMATCH')
    if any(int(row.get('fetch_enabled') or 0) != 0 for row in policies):
        raise RuntimeError('UNEXPECTED_LIVE_SOURCE_ALREADY_ENABLED')
    if any(int(row.get('requires_approval_for_live_fetch') or 0) != 1 for row in policies):
        raise RuntimeError('LIVE_FETCH_APPROVAL_GATE_NOT_UNIVERSAL')
    if any(int(row.get('daily_call_budget') or 0) != 0 for row in policies):
        raise RuntimeError('UNEXPECTED_NONZERO_CALL_BUDGET')

    return registry, policies


def main() -> int:
    if git('status', '--short'):
        raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected = os.environ.get('TOKENOSKOBI_EXPECTED_HEAD', '').strip()
    if expected and git('rev-parse', 'HEAD') != expected:
        raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list', '-n1', TAG55) != SEAL55:
        raise RuntimeError('ERA55_SEAL_MISMATCH')
    if git('rev-list', '-n1', TAG56) != SEAL56:
        raise RuntimeError('ERA56_SEAL_MISMATCH')

    registry, policies = read_source_truth()
    timestamp = datetime.now(timezone.utc).isoformat()

    policy_by_uid = {str(row['source_uid']): row for row in policies}
    source_rows = []
    for row in registry:
        uid = str(row['source_uid'])
        source_rows.append({
            'source_uid': uid,
            'source_name': row['source_name'],
            'source_class': row['source_class'],
            'source_domain': row['source_domain'],
            'trust_level': row['trust_level'],
            'declared_fetch_method': row['fetch_method'],
            'registry_status': row['status'],
            'priority': row['priority'],
            'fetch_enabled': False,
            'requires_human_approval': True,
            'daily_call_budget': 0,
            'runtime_eligible': False,
            'runtime_block_reason': 'LIVE_FETCH_NOT_AUTHORIZED',
        })

    contract = {
        'schema': 'news_runtime_source_contract_v1',
        'contract_version': '1.0',
        'created_at_utc': timestamp,
        'authority': {
            'seed_registry': 'news_source_registry_v1',
            'fetch_policy': 'news_source_fetch_policy_v1',
            'current_state_owner': 'PROJECT_RUNTIME.json',
            'human_final_authority': True,
        },
        'layer_contract': {
            'seed_registry_role': 'DECLARATIVE_SOURCE_CANDIDATES_ONLY',
            'fetch_policy_role': 'PER_SOURCE_RUNTIME_AUTHORIZATION_AND_BUDGET',
            'runtime_selection_role': 'DERIVED_JOIN_NOT_SEPARATE_DUPLICATE_REGISTRY',
            'producer_role': 'EXECUTE_ONLY_RUNTIME_ELIGIBLE_SOURCES',
        },
        'runtime_eligibility_rule': {
            'all_required': [
                'registry status explicitly runtime-enabled',
                'fetch_enabled=1',
                'requires_approval_for_live_fetch satisfied by recorded human decision',
                'daily_call_budget>0',
                'source_url is a confirmed HTTP(S) endpoint',
                'fetch_method has a supported adapter',
            ],
            'default': 'DENY',
            'empty_selection_behavior': 'SUCCESS_NOOP_FAIL_CLOSED',
            'automatic_activation': False,
        },
        'activation_workflow': [
            'ENDPOINT_CONFIRMATION',
            'ADAPTER_CONTRACT_VALIDATION',
            'TEMP_COPY_OR_SHADOW_TEST',
            'HUMAN_AUTHORIZATION',
            'BOUNDED_BUDGET_ASSIGNMENT',
            'SINGLE_SOURCE_CANARY',
            'POST_AUDIT',
        ],
        'forbidden': [
            'hardcoded source lists in runtime code',
            'legacy raw runner restoration',
            'implicit activation from seed presence',
            'network fetch when fetch_enabled=0',
            'network fetch with daily_call_budget=0',
            'automatic promotion to live',
        ],
        'current_truth': {
            'registered_source_count': len(source_rows),
            'runtime_eligible_source_count': 0,
            'live_fetch_authorized': False,
            'all_sources_fail_closed': True,
        },
        'sources': source_rows,
    }
    dump(CONTRACT, contract)

    artifact_rel = str(ARTIFACT.relative_to(ROOT))
    contract_rel = str(CONTRACT.relative_to(ROOT))
    dump(ARTIFACT, {
        'schema': 'general_runtime_source_contract_v1',
        'timestamp_utc': timestamp,
        'work_unit': WORK,
        'status': 'CLOSED_VERIFIED',
        'result': RESULT,
        'registered_source_count': len(source_rows),
        'runtime_eligible_source_count': 0,
        'live_fetch_authorized': False,
        'network_call': False,
        'db_write': False,
        'service_timer_change': False,
        'production_mutation': False,
        'era57_opened': False,
        'contract': contract_rel,
        'next_safe_step': NEXT,
    })

    runtime = load(RUNTIME)
    pointer = runtime['canonical_runtime_pointer']
    pointer.update({
        'current_stage': 'GENERAL_RUNTIME_SOURCE_CONTRACT_LOCKED',
        'last_completed': WORK,
        'last_result': RESULT,
        'last_artifact': artifact_rel,
        'runtime_source_contract': contract_rel,
        'runtime_source_contract_locked': True,
        'registered_source_count': len(source_rows),
        'runtime_eligible_source_count': 0,
        'live_source_fetch_authorized': False,
        'source_activation_requires_human_approval': True,
        'legacy_raw_runner_restore_forbidden': True,
        'era57_opened': False,
        'next_safe_step': NEXT,
        'updated_at_utc': timestamp,
    })
    runtime['current_problem'] = {'code': 'NO_RUNTIME_SOURCE_AUTHORIZED', 'severity': 'P1', 'evidence': artifact_rel}
    runtime['current_state'] = {
        'project_status': 'ERA56_CLOSED_ERA57_NOT_OPENED',
        'runtime_status': 'SOURCE_CONTRACT_LOCKED_NO_LIVE_SOURCE',
        'mode': 'POLICY_DRIVEN_FAIL_CLOSED',
        'last_action': {'task': WORK, 'result': RESULT, 'artifact': artifact_rel, 'timestamp': timestamp},
        'current_problem': runtime['current_problem'],
        'next_safe_step': {'id': NEXT, 'status': 'READY', 'human_authorization_required': True, 'production_mutation': False},
        'updated_at': timestamp,
    }
    runtime['current_work_unit'] = {'id': WORK, 'status': 'CLOSED_VERIFIED', 'result': RESULT, 'artifact': artifact_rel, 'production_mutation': False, 'next_step': NEXT}
    dump(RUNTIME, runtime)

    boot = load(BOOT)
    boot['runtime_source_contract'] = {
        'path': contract_rel,
        'seed_registry_is_not_live_registry': True,
        'runtime_selection_is_policy_derived': True,
        'default_deny': True,
        'automatic_activation': False,
    }
    dump(BOOT, boot)

    history = load(HISTORY)
    history.setdefault('events', []).append({
        'event_id': WORK,
        'timestamp_utc': timestamp,
        'status': 'CLOSED_VERIFIED',
        'result': RESULT,
        'artifact': artifact_rel,
        'contract': contract_rel,
        'registered_source_count': len(source_rows),
        'runtime_eligible_source_count': 0,
        'live_fetch_authorized': False,
        'production_mutation': False,
        'era57_opened': False,
        'next_safe_step': NEXT,
    })
    history['updated_at'] = timestamp
    history['updated_at_utc'] = timestamp
    dump(HISTORY, history)

    readme = README.read_text(encoding='utf-8')
    readme = replace_section(readme, '## Runtime source contract', f'''- Seed registry: `news_source_registry_v1`.
- Fetch policy: `news_source_fetch_policy_v1`.
- Seed presence does not authorize network access.
- Runtime eligibility is derived from registry + policy + explicit human authorization.
- Default behavior is deny/fail-closed.
- Current runtime-eligible source count: `0`.
- Canonical contract: `{contract_rel}`.
- No legacy raw runner restoration and no hardcoded runtime source list.''')
    README.write_text(readme.rstrip() + '\n', encoding='utf-8')

    index = INDEX.read_text(encoding='utf-8')
    if contract_rel not in index:
        index = index.rstrip() + f'\n\n## Runtime source contract\n\n- `{contract_rel}` — policy-driven source activation contract; default deny.\n'
    INDEX.write_text(index.rstrip() + '\n', encoding='utf-8')

    roadmap = ROADMAP.read_text(encoding='utf-8')
    roadmap = replace_section(roadmap, '## CURRENT RUNTIME SOURCE POSITION', f'''- General source contract: `LOCKED`.
- Registered seed sources: `{len(source_rows)}`.
- Runtime-eligible sources: `0`.
- Live network fetch: `NOT_AUTHORIZED`.
- ERA57 opened: `false`.
- Next safe step: `{NEXT}`.''')
    ROADMAP.write_text(roadmap.rstrip() + '\n', encoding='utf-8')

    master = MASTER.read_text(encoding='utf-8')
    master = replace_section(master, '## 03 LAST VERIFIED WORK', f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={artifact_rel}
RUNTIME_SOURCE_CONTRACT={contract_rel}
REGISTERED_SOURCE_COUNT={len(source_rows)}
RUNTIME_ELIGIBLE_SOURCE_COUNT=0
LIVE_FETCH_AUTHORIZED=false
ERA57_OPENED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}''')
    master = replace_section(master, '## 10 NEXT SAFE STEP', f'''```text
NEXT_SAFE_STEP={NEXT}
```

Select at most one source for bounded activation review. Seed registry presence alone is never authorization.''')
    MASTER.write_text(master.rstrip() + '\n', encoding='utf-8')

    handoff = HANDOFF.read_text(encoding='utf-8')
    handoff = replace_section(handoff, '## 03 LAST VERIFIED WORK', f'''LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={artifact_rel}
RUNTIME_SOURCE_CONTRACT={contract_rel}
RUNTIME_ELIGIBLE_SOURCE_COUNT=0
LIVE_FETCH_AUTHORIZED=false
ERA57_OPENED=false''')
    handoff = replace_section(handoff, '## 07 ALLOWED NEXT DECISIONS', f'''- Review at most one source for bounded activation.
- Do not activate from seed presence alone.
- Do not restore legacy raw runner.
- Do not add a hardcoded source list.
- ERA57 remains closed.

NEXT_SAFE_STEP={NEXT}''')
    HANDOFF.write_text(handoff.rstrip() + '\n', encoding='utf-8')

    almanac = ALMANAC.read_text(encoding='utf-8')
    almanac += f'''\n\n---\n\n## GENERAL RUNTIME SOURCE CONTRACT\n\n- Status: `CLOSED_VERIFIED`\n- Contract: `{contract_rel}`\n- Registered seed sources: `{len(source_rows)}`\n- Runtime-eligible sources: `0`\n- Live fetch authorized: `false`\n- Production mutation: `false`\n- ERA57 opened: `false`\n- Next safe step: `{NEXT}`\n'''
    ALMANAC.write_text(almanac.rstrip() + '\n', encoding='utf-8')

    TK_AI.parent.mkdir(parents=True, exist_ok=True)
    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nCURRENT_STAGE=GENERAL_RUNTIME_SOURCE_CONTRACT_LOCKED\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nRUNTIME_SOURCE_CONTRACT={contract_rel}\nREGISTERED_SOURCE_COUNT={len(source_rows)}\nRUNTIME_ELIGIBLE_SOURCE_COUNT=0\nLIVE_FETCH_AUTHORIZED=false\nERA57_OPENED=false\nPRODUCTION_MUTATION=false\nNEXT_SAFE_STEP={NEXT}\n''', encoding='utf-8')

    if TRANSIENT_PRODUCER.exists():
        TRANSIENT_PRODUCER.unlink()
    if SELF.exists():
        SELF.unlink()

    for path in (CONTRACT, ARTIFACT, RUNTIME, BOOT, HISTORY):
        load(path)
    if git('rev-list', '-n1', TAG55) != SEAL55 or git('rev-list', '-n1', TAG56) != SEAL56:
        raise RuntimeError('SEAL_CHANGED')

    git('add', '-A')
    check = run(['git', 'diff', '--cached', '--check'], check=False)
    if check.returncode:
        print(check.stdout, end='')
        print(check.stderr, end='')
        raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit', '-m', 'GENERAL_RUNTIME_SOURCE_CONTRACT | OK | POLICY_DRIVEN_DEFAULT_DENY')

    print('GENERAL_RUNTIME_SOURCE_CONTRACT=SUCCESS')
    print(f'REGISTERED_SOURCE_COUNT={len(source_rows)}')
    print('RUNTIME_ELIGIBLE_SOURCE_COUNT=0')
    print('LIVE_FETCH_AUTHORIZED=false')
    print('NETWORK_CALL=false')
    print('DB_WRITE=false')
    print('SERVICE_TIMER_CHANGE=false')
    print('LEGACY_RAW_RESTORE=false')
    print('ERA57_OPENED=false')
    print('PRODUCTION_MUTATION=false')
    print('NEXT_SAFE_STEP=' + NEXT)
    print('LOCAL_COMMIT=' + git('rev-parse', 'HEAD'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
