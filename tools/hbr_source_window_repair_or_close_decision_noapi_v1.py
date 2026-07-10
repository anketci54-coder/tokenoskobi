#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import re
import subprocess

ROOT = Path('/root/tokenoskobi_clean_v1')
WORK_UNIT = 'HBR_SOURCE_WINDOW_REPAIR_OR_CLOSE_DECISION_NOAPI'
DECISION = 'OK_HBR_SOURCE_WINDOW_CLOSE_DECISION_NOAPI'
CLOSE_CHOICE = 'CLOSE_CURRENT_HBR_ATTEMPT_NO_WINDOW_REPAIR'
NEXT_STEP = 'POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_NOAPI'

HBR_C_PATH = ROOT / 'data/control/hbr_c_policy_gate_and_collision_dryrun_noapi_v1.json'
HBR_A_PATH = ROOT / 'data/control/hbr_a_input_only_source_plan_noapi_v1.json'
ERA54_PATH = ROOT / 'data/control/era54f_final_closure_noapi_v1.json'
CONTROL_REL = 'data/control/hbr_source_window_repair_or_close_decision_noapi_v1.json'
DOC_REL = 'docs/canonical/HBR_SOURCE_WINDOW_REPAIR_OR_CLOSE_DECISION_NOAPI_V1.md'
TOOL_REL = 'tools/hbr_source_window_repair_or_close_decision_noapi_v1.py'


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ['git', *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError(f'JSON_OBJECT_REQUIRED:{path}')
    return value


def atomic_write_text(relative_path: str, text: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp_hbr_close')
    temporary.write_text(text, encoding='utf-8')
    os.replace(temporary, path)


def atomic_write_json(relative_path: str, value: dict[str, Any]) -> None:
    atomic_write_text(
        relative_path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + '\n',
    )


def replace_current_block(original: str, new_block: str) -> str:
    marker_pairs = [
        (
            '<!-- HBR_C_POLICY_GATE_CURRENT_START -->',
            '<!-- HBR_C_POLICY_GATE_CURRENT_END -->',
        ),
        (
            '<!-- HBR_CURRENT_ATTEMPT_CLOSE_START -->',
            '<!-- HBR_CURRENT_ATTEMPT_CLOSE_END -->',
        ),
    ]
    replacement = new_block.rstrip() + '\n\n'
    for start, end in marker_pairs:
        pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end) + r'\n*', re.S)
        if pattern.search(original):
            return pattern.sub(replacement, original, count=1)
    return replacement + original.lstrip('\ufeff')


def update_markdown(relative_path: str, block: str, append_entry: str | None = None) -> None:
    path = ROOT / relative_path
    updated = replace_current_block(path.read_text(encoding='utf-8'), block)
    if append_entry and append_entry.strip() not in updated:
        updated = updated.rstrip() + '\n\n' + append_entry.rstrip() + '\n'
    atomic_write_text(relative_path, updated)


def main() -> int:
    generated_at = now_utc()
    current_head = git_output('rev-parse', 'HEAD')
    current_branch = git_output('branch', '--show-current')
    expected_head = os.environ.get('HBR_EXPECTED_HEAD', '').strip()

    if current_branch != 'main':
        raise RuntimeError(f'BRANCH_MISMATCH:{current_branch}')
    if not expected_head:
        raise RuntimeError('HBR_EXPECTED_HEAD_REQUIRED')
    if current_head != expected_head:
        raise RuntimeError(f'HEAD_MISMATCH:expected={expected_head}:actual={current_head}')

    for required_path in (HBR_C_PATH, HBR_A_PATH, ERA54_PATH):
        if not required_path.exists():
            raise RuntimeError('MISSING_REQUIRED_ARTIFACT:' + str(required_path.relative_to(ROOT)))

    hbr_c = load_json(HBR_C_PATH)
    hbr_a = load_json(HBR_A_PATH)
    era54 = load_json(ERA54_PATH)

    failures: list[str] = []
    if hbr_c.get('decision') != 'OK_HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI':
        failures.append('hbr_c_not_ok')
    if hbr_c.get('next') != WORK_UNIT:
        failures.append('hbr_c_next_mismatch')

    result = hbr_c.get('result', {})
    collision_result = result.get('collision_result')
    eligible_count = result.get('locked_window_eligible_count')
    db_before = result.get('db_before')
    db_after = result.get('db_after')
    total_changes_before = result.get('sqlite_total_changes_before')
    total_changes_after = result.get('sqlite_total_changes_after')

    if collision_result != 'NO_PRODUCTION_COLLISION':
        failures.append('production_collision_not_clean')
    if eligible_count != 0:
        failures.append('eligible_count_not_zero')
    if db_before != db_after:
        failures.append('hbr_c_db_before_after_mismatch')
    if total_changes_before != 0 or total_changes_after != 0:
        failures.append('hbr_c_total_changes_not_zero')
    if result.get('production_insert') is not False:
        failures.append('hbr_c_production_insert_not_false')

    source_plan = hbr_a.get('result', {}).get('source_plan', {})
    sources = source_plan.get('sources', [])
    time_windows = source_plan.get('time_windows', [])
    source_types = sorted({str(source.get('source_type')) for source in sources})
    window_ids = [str(window.get('window_id')) for window in time_windows]
    june_window_locked = (
        len(time_windows) == 2
        and time_windows[0].get('start_utc') == '2026-06-01T00:00:00+00:00'
        and time_windows[1].get('end_utc') == '2026-06-30T23:59:59+00:00'
    )
    rss_only = bool(sources) and source_types == ['rss']
    if not june_window_locked:
        failures.append('historical_june_window_not_confirmed')
    if not rss_only:
        failures.append('rss_source_plan_not_confirmed')

    if era54.get('decision') != 'OK_ERA54_FINAL_CLOSED_VERIFIED_NOAPI':
        failures.append('era54_not_closed_verified')
    era54_guarantees = era54.get('summary', {}).get('guarantees', {})
    if era54_guarantees.get('runtime_change') is not False:
        failures.append('era54_runtime_boundary_unexpected')
    if era54_guarantees.get('external_source_adapter') is not False:
        failures.append('era54_external_adapter_boundary_unexpected')

    if failures:
        raise RuntimeError('HBR_CLOSE_DECISION_PREFLIGHT_FAILURE:' + '|'.join(failures))

    rationale = [
        'HBR-C proved zero production collision across news_uid, url_hash, raw_hash and derived news_uid.',
        'The sealed input contains 55 rows but zero rows inside the locked June 2026 historical windows.',
        'The selected sources are rolling RSS feeds and did not provide archive-capable June input.',
        'Moving the locked window to July would change the settled historical objective and require a new HBR-A/HBR-B seal.',
        'Continuing to HBR-D without eligible historical input would create meaningless predictions.',
        'Therefore the current HBR attempt closes as evidence-complete but replay-inconclusive.',
    ]

    decision_id = 'HBR__SOURCE_WINDOW_CLOSE_DECISION__' + current_head[:12] + '__' + generated_at
    authority = {
        'api_call': False,
        'network_call': False,
        'db_read': False,
        'db_write': False,
        'db_schema_change': False,
        'index_creation': False,
        'outcome_fetch': False,
        'prediction_run': False,
        'service_change': False,
        'timer_change': False,
        'nginx_change': False,
        'tk_machine_run': False,
        'shadow_cleanup': False,
        'paper_trade': False,
        'live_trade': False,
        'trade_authority': False,
        'new_era_opened': False,
    }

    artifact: dict[str, Any] = {
        'stage': WORK_UNIT,
        'generated_at_utc': generated_at,
        'decision': DECISION,
        'decision_id': decision_id,
        'previous_head_before_closure_commit': current_head,
        'authority': authority,
        'failures': [],
        'warnings': [],
        'next': NEXT_STEP,
        'result': {
            'choice': CLOSE_CHOICE,
            'current_hbr_attempt_status': 'CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT',
            'hbr_a_status': 'CLOSED',
            'hbr_b_status': 'CLOSED_SEALED',
            'hbr_c_status': 'CLOSED_NO_PRODUCTION_COLLISION',
            'hbr_d_status': 'NOT_RUN_ZERO_ELIGIBLE_INPUT',
            'hbr_e_status': 'NOT_RUN_NO_PREDICTION_SEAL',
            'hbr_f_status': 'NOT_RUN_NO_OUTCOME_COMPARISON',
            'collision_result': collision_result,
            'sealed_input_count': result.get('input_count'),
            'locked_window_eligible_count': eligible_count,
            'source_types': source_types,
            'window_ids': window_ids,
            'source_window_repair_now': False,
            'hbr_b_reseal_now': False,
            'prediction_now': False,
            'outcome_fetch_now': False,
            'future_hbr_retry_condition': 'ARCHIVE_CAPABLE_INPUT_SOURCE_WITH_NEW_INPUT_SEAL',
            'future_hbr_retry_priority': 'BACKLOG_NOT_IMMEDIATE',
            'return_line': 'EXISTING_NEWS_HOT_INGRESS_CONTINUATION',
            'next_safe_step': NEXT_STEP,
            'rationale': rationale,
            'era54_existing_scaffold': {
                'status': era54.get('summary', {}).get('status'),
                'tool': 'tools/hot_ingress_minimal_readonly_scaffold_v1.py',
                'runtime_change_in_era54': era54_guarantees.get('runtime_change'),
                'external_source_adapter_in_era54': era54_guarantees.get('external_source_adapter'),
            },
        },
    }
    atomic_write_json(CONTROL_REL, artifact)

    current_problem = None
    last_action = {
        'timestamp': generated_at,
        'task': WORK_UNIT,
        'result': DECISION,
        'artifact': CONTROL_REL,
    }
    active_work_unit = {
        'id': WORK_UNIT,
        'type': 'HBR_SOURCE_WINDOW_CLOSE_DECISION',
        'artifact': CONTROL_REL,
        'module': TOOL_REL,
        'status': 'CLOSED',
        'next_step': NEXT_STEP,
    }
    next_safe_step = {'name': NEXT_STEP, 'status': 'READY'}
    runtime_pointer = {
        'authority': 'PROJECT_RUNTIME.json',
        'previous_head_before_closure_commit': current_head,
        'last_completed': WORK_UNIT,
        'decision': DECISION,
        'hbr_attempt_status': 'CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT',
        'collision_result': collision_result,
        'locked_window_eligible_count': eligible_count,
        'next_safe_step': NEXT_STEP,
        'updated_at_utc': generated_at,
    }

    runtime = load_json(ROOT / 'PROJECT_RUNTIME.json')
    runtime.setdefault('current_state', {})
    runtime['current_state'].update(
        {
            'mode': 'HBR_CURRENT_ATTEMPT_CLOSED_ZERO_ELIGIBLE_INPUT',
            'runtime_status': 'WORK_UNIT_CLOSED',
            'project_status': 'ACTIVE',
            'updated_at': generated_at,
            'last_action': last_action,
            'active_work_unit': active_work_unit,
            'next_safe_step': next_safe_step,
            'current_problem': current_problem,
        }
    )
    runtime['current_work_unit'] = active_work_unit
    runtime['last_completed'] = WORK_UNIT
    runtime['mode'] = 'HBR_CURRENT_ATTEMPT_CLOSED_ZERO_ELIGIBLE_INPUT'
    runtime['next_safe_step'] = next_safe_step
    runtime['current_problem'] = current_problem
    runtime['updated_at_utc'] = generated_at
    runtime['canonical_runtime_pointer'] = runtime_pointer
    runtime['current_checkpoint'] = {
        'git_branch': 'main',
        'previous_head_before_closure_commit': current_head,
        'head_semantics': 'PREVIOUS_HEAD_BEFORE_ATOMIC_CLOSURE_COMMIT',
        'source': 'local_git',
    }
    atomic_write_json('PROJECT_RUNTIME.json', runtime)

    boot = load_json(ROOT / 'PROJECT_BOOT.json')
    boot['current_work_unit'] = active_work_unit
    boot['last_completed'] = WORK_UNIT
    boot['last_action'] = last_action
    boot['next_safe_step'] = next_safe_step
    boot['current_problem'] = current_problem
    boot['canonical_runtime_pointer'] = runtime_pointer
    boot['current_checkpoint'] = runtime['current_checkpoint']
    boot['new_chat_instruction'] = (
        'Read PROJECT_RUNTIME.json first. The current HBR attempt is closed with zero eligible historical input and no production collision. '
        f'Proceed only to {NEXT_STEP}. Do not reopen HBR-A/B, move the historical window, fetch outcomes, run predictions, or mutate DB/schema without explicit scope.'
    )
    if isinstance(boot.get('new_window_startup_instruction'), dict):
        boot['new_window_startup_instruction']['instruction'] = boot['new_chat_instruction']
    boot.setdefault('project', {})
    boot['project']['mode'] = 'HBR_CURRENT_ATTEMPT_CLOSED_ZERO_ELIGIBLE_INPUT'
    boot['project']['status'] = 'ACTIVE'
    atomic_write_json('PROJECT_BOOT.json', boot)

    tk = load_json(ROOT / 'data/control/latest_tk_machine_state.json')
    tk['collect_mode'] = 'canonical_sync_snapshot_no_tk_machine'
    tk['created_at_utc'] = generated_at
    tk['generated_by'] = WORK_UNIT
    tk['tk_machine_executed'] = False
    tk['current_state'] = {
        'active_work_unit': active_work_unit,
        'next_safe_step': next_safe_step,
        'runtime_status': 'WORK_UNIT_CLOSED',
        'updated_at': generated_at,
        'last_action': last_action,
        'authority': 'PROJECT_RUNTIME.json',
    }
    tk['canonical_runtime_pointer'] = runtime_pointer
    tk['graphs_stale_non_authoritative'] = True
    atomic_write_json('data/control/latest_tk_machine_state.json', tk)

    roadmap = load_json(ROOT / 'data/tokenoskobi_v1_v8_master_era_roadmap.json')
    roadmap['updated_at'] = generated_at
    roadmap['git_head'] = current_head
    roadmap['git_head_semantics'] = 'PREVIOUS_HEAD_BEFORE_ATOMIC_CLOSURE_COMMIT'
    roadmap['work_unit'] = WORK_UNIT
    roadmap['current_state_authority'] = 'PROJECT_RUNTIME.json'
    roadmap['runtime_alignment'] = runtime_pointer
    roadmap['hbr_chain'] = {
        'HBR_A': 'CLOSED',
        'HBR_B': 'CLOSED_SEALED',
        'HBR_C': 'CLOSED_NO_PRODUCTION_COLLISION',
        'HBR_CURRENT_ATTEMPT': 'CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT',
        'HBR_D': 'NOT_RUN_ZERO_ELIGIBLE_INPUT',
        'HBR_E': 'NOT_RUN_NO_PREDICTION_SEAL',
        'HBR_F': 'NOT_RUN_NO_OUTCOME_COMPARISON',
        'FUTURE_RETRY': 'BACKLOG_ARCHIVE_CAPABLE_SOURCE_NEW_SEAL_REQUIRED',
        'next_safe_step': NEXT_STEP,
    }
    atomic_write_json('data/tokenoskobi_v1_v8_master_era_roadmap.json', roadmap)

    block = f'''<!-- HBR_CURRENT_ATTEMPT_CLOSE_START -->
## CANONICAL CURRENT STATE — HBR ATTEMPT CLOSED

STATE_SYNC_UTC={generated_at}
PREVIOUS_HEAD_BEFORE_CLOSURE_COMMIT={current_head}
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
LAST_COMPLETED={WORK_UNIT}
LAST_DECISION={DECISION}
HBR_CLOSE_CHOICE={CLOSE_CHOICE}
HBR_CURRENT_ATTEMPT_STATUS=CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT
HBR_C_COLLISION_RESULT={collision_result}
SEALED_INPUT_COUNT={result.get('input_count')}
LOCKED_WINDOW_ELIGIBLE_COUNT={eligible_count}
SOURCE_WINDOW_REPAIR_NOW=false
HBR_B_RESEAL_NOW=false
HBR_D_PREDICTION_RUN=false
HBR_E_OUTCOME_FETCH=false
HBR_F_SCORE_COMPARISON=false
FUTURE_HBR_RETRY=BACKLOG_ARCHIVE_CAPABLE_SOURCE_NEW_SEAL_REQUIRED
NEXT_SAFE_STEP={NEXT_STEP}
TK_MACHINE_EXECUTED=false
DB_OR_SCHEMA_MUTATION=false
<!-- HBR_CURRENT_ATTEMPT_CLOSE_END -->'''

    update_markdown('03_ROADMAP.md', block)
    update_markdown(
        '04_ALMANAC.md',
        block,
        f'''## {WORK_UNIT} — {generated_at}

- Decision: `{DECISION}`
- Choice: `{CLOSE_CHOICE}`
- Current HBR attempt: `CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT`
- HBR-C collision result: `{collision_result}`
- Sealed input count: `{result.get('input_count')}`
- Locked-window eligible count: `{eligible_count}`
- Window repair now: `false`
- HBR-D/E/F executed: `false`
- Future retry: `archive-capable source + new input seal`
- Next safe step: `{NEXT_STEP}`
- Previous HEAD: `{current_head}`''',
    )
    update_markdown('06_PROJECT_MASTER_STATE.md', block)
    update_markdown('07_PROJECT_HANDOFF.md', block)

    atomic_write_text(
        'reports/LATEST_TK_AI_HANDOFF.md',
        f'''# LATEST TK AI HANDOFF

{block}

`PROJECT_RUNTIME.json` is current-state authority.

The current HBR attempt is closed. It must not be restarted by shifting the window or resealing the same rolling RSS input. A future HBR retry requires an archive-capable historical input source and a completely new input seal.

Proceed only to `{NEXT_STEP}`. This continues the already-built ERA54 hot-ingress scaffold; it does not rebuild NEWS from zero.
''',
    )

    atomic_write_text(
        DOC_REL,
        f'''# HBR_SOURCE_WINDOW_REPAIR_OR_CLOSE_DECISION_NOAPI_V1

- Decision: `{DECISION}`
- Choice: `{CLOSE_CHOICE}`
- Generated: `{generated_at}`
- Previous HEAD: `{current_head}`
- Current HBR attempt: `CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT`
- HBR-C collision result: `{collision_result}`
- Sealed input count: `{result.get('input_count')}`
- Locked-window eligible count: `{eligible_count}`
- Source types: `{', '.join(source_types)}`
- Window IDs: `{', '.join(window_ids)}`
- Window repair now: `false`
- HBR-B reseal now: `false`
- HBR-D/E/F: `not run`
- Future retry condition: `archive-capable input source with new input seal`
- Next safe step: `{NEXT_STEP}`

## Reason

The rolling RSS sources returned current July 2026 items, while the locked settled historical windows cover June 1-30, 2026. Moving the window would change the experiment and invalidate continuation from the existing HBR-B seal. The current attempt therefore closes without prediction or outcome access.

## Boundaries

No network call, DB read/write, schema/index mutation, prediction, outcome fetch, service/timer/nginx change, TK machine execution, shadow cleanup, paper trade, live trade, trade authority change, or new ERA occurred.
''',
    )

    print(
        json.dumps(
            {
                'decision': DECISION,
                'decision_id': decision_id,
                'choice': CLOSE_CHOICE,
                'hbr_current_attempt_status': 'CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT',
                'collision_result': collision_result,
                'locked_window_eligible_count': eligible_count,
                'future_hbr_retry': 'BACKLOG_ARCHIVE_CAPABLE_SOURCE_NEW_SEAL_REQUIRED',
                'next_safe_step': NEXT_STEP,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
