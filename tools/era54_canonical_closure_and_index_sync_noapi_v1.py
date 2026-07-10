#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import re
import subprocess
import tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
WORK_UNIT = 'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI'
DECISION = 'OK_ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI'
NEXT_STEP = 'NEXT_MAJOR_PROJECT_LINE_SELECTION_AFTER_NEWS_OPERATIONAL_BASELINE_CLOSURE'
TECHNICAL_CLOSURE_HEAD = 'c72995c352a76fe8557de369228f86e6f7d2846e'
OBSERVATION = ROOT / 'data/control/post_era54_hot_ingress_bound_runtime_first_observation_noapi_v1.json'
CONTROL_REL = 'data/control/era54_canonical_closure_and_index_sync_noapi_v1.json'

MANDATORY_ERA_CLOSURE_FILES = [
    'PROJECT_RUNTIME.json',
    'PROJECT_BOOT.json',
    'PROJECT_HISTORY.json',
    'data/tokenoskobi_v1_v8_master_era_roadmap.json',
    '03_ROADMAP.md',
    '04_ALMANAC.md',
    '05_ATLAS.md',
    '06_PROJECT_MASTER_STATE.md',
    '07_PROJECT_HANDOFF.md',
]

CONDITIONAL_NAVIGATION_FILES = [
    'README.md',
    '01_INDEX.md',
    'docs/canonical/CANONICAL_DOCUMENTATION_V1_LOCK.md',
]

OPERATIONAL_COMPANION_FILES = [
    'reports/LATEST_TK_AI_HANDOFF.md',
    'data/control/latest_tk_machine_state.json',
]

ALL_CHANGED_FILES = (
    MANDATORY_ERA_CLOSURE_FILES
    + CONDITIONAL_NAVIGATION_FILES
    + OPERATIONAL_COMPANION_FILES
    + [CONTROL_REL]
)

INDEX_TEXT = '''# 01_INDEX.md - TOKENOSKOBI / COINOSKOBI CANONICAL INDEX

## 1. BOOT POINTER

- `README.md` — kısa başlangıç ve güvenlik işaretçisi

## 2. HUMAN-READABLE CANONICAL DOCUMENTS

- `02_MANIFESTO.md` — anayasa, doktrin, yasaklar ve yetki sınırları
- `03_ROADMAP.md` — ileri yön, ana hatlar ve açılmamış işler
- `04_ALMANAC.md` — tamamlanan işler ve kapanış kayıtları
- `05_ATLAS.md` — mimari bağ ve veri akış haritası
- `06_PROJECT_MASTER_STATE.md` — güncel insan-okur proje özeti
- `07_PROJECT_HANDOFF.md` — yeni oturum devam bilgisi

## 3. MACHINE-READABLE CANONICAL AUTHORITIES

- `PROJECT_RUNTIME.json` — güncel durumun birincil kaynağı
- `PROJECT_BOOT.json` — sabit kimlik, doktrin ve başlangıç sözleşmesi
- `PROJECT_HISTORY.json` — eklemeli tarihsel kayıt; yalnız gerektiğinde okunur
- `data/tokenoskobi_v1_v8_master_era_roadmap.json` — V/ERA ana yol haritası

## 4. DOCUMENTATION LOCK

- `docs/canonical/CANONICAL_DOCUMENTATION_V1_LOCK.md` — canonical doküman sahipliği ve kapanış güncelleme sözleşmesi

## STARTUP READ ORDER

1. `PROJECT_RUNTIME.json`
2. `PROJECT_BOOT.json`
3. `06_PROJECT_MASTER_STATE.md`
4. `07_PROJECT_HANDOFF.md`
5. `02_MANIFESTO.md`
6. `03_ROADMAP.md`
7. `PROJECT_HISTORY.json` yalnız tarihsel bağlam gerektiğinde

## INDEX CONSTITUTION

`01_INDEX.md` yalnız navigation içindir.

Bu dosya şunları içermez:

- canlı runtime durumu
- GitHub HEAD veya zaman damgası
- proje tarihi veya kapanış ayrıntıları
- mimari teknik ayrıntı
- faz/ERA sonuçları
- root dizin envanteri
- geçici veya arşiv dosyaları

Navigation değişmedikçe bu dosya değiştirilmez.
'''

README_TEXT = '''# TOKENOSKOBI / COINOSKOBI

Bu README yalnız başlangıç işaretçisidir. Canlı proje durumu burada tutulmaz.

## Yetkili başlangıç sırası

1. `PROJECT_RUNTIME.json`
2. `PROJECT_BOOT.json`
3. `06_PROJECT_MASTER_STATE.md`
4. `07_PROJECT_HANDOFF.md`
5. `02_MANIFESTO.md`
6. `03_ROADMAP.md`
7. `PROJECT_HISTORY.json` yalnız tarihsel bağlam gerektiğinde

Canonical navigation için `01_INDEX.md` kullanılır.

## Kaynak önceliği

1. Local workspace
2. Local Git
3. GitHub remote
4. AI memory

## Çalışma kuralları

- Yeni ERA yalnız açık insan kararıyla açılır.
- Kapanmış audit veya hat, kanıtlı drift yoksa yeniden açılmaz.
- Tek mantıksal operasyon, tek doğrulama seti, mümkünse tek commit ve tek push kullanılır.
- Runtime, DB, panel, service, timer veya yetki değişikliği yalnız açık kapsamla yapılır.
- Canlı trade, wallet signing, order creation ve AI trade authority kilitlidir.
- GitHub incelemesi önce; server yalnız local/runtime kanıtı gerektiğinde kullanılır.
- `tk machine` güncel canonical akışta çalıştırılmaz.
'''


def utc_now() -> str:
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
        raise RuntimeError('JSON_OBJECT_REQUIRED:' + str(path))
    return value


def atomic_write_text(relative: str, text: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
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


def atomic_write_json(relative: str, value: dict[str, Any]) -> None:
    atomic_write_text(
        relative,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + '\n',
    )


def replace_marker_block(
    original: str,
    start_markers: list[tuple[str, str]],
    replacement: str,
) -> str:
    block = replacement.rstrip() + '\n\n'
    for start, end in start_markers:
        pattern = re.compile(
            re.escape(start) + r'.*?' + re.escape(end) + r'\n*',
            re.S,
        )
        if pattern.search(original):
            return pattern.sub(block, original, count=1)
    return block + original.lstrip('\ufeff')


def append_once(original: str, marker: str, text: str) -> str:
    if marker in original:
        return original
    return original.rstrip() + '\n\n' + text.rstrip() + '\n'


def update_current_markdown(relative: str, current_block: str) -> None:
    path = ROOT / relative
    original = path.read_text(encoding='utf-8')
    updated = replace_marker_block(
        original,
        [
            (
                '<!-- POST_ERA54_HOT_FIRST_OBSERVATION_CURRENT_START -->',
                '<!-- POST_ERA54_HOT_FIRST_OBSERVATION_CURRENT_END -->',
            ),
            (
                '<!-- ERA54_FINAL_CLOSURE_INDEX_SYNC_CURRENT_START -->',
                '<!-- ERA54_FINAL_CLOSURE_INDEX_SYNC_CURRENT_END -->',
            ),
        ],
        current_block,
    )
    atomic_write_text(relative, updated)


def update_documentation_lock(generated: str) -> None:
    path = ROOT / 'docs/canonical/CANONICAL_DOCUMENTATION_V1_LOCK.md'
    original = path.read_text(encoding='utf-8')
    separator = '\n---\n'
    if separator not in original:
        raise RuntimeError('DOCUMENTATION_LOCK_SEPARATOR_MISSING')
    _, tail = original.split(separator, 1)
    header = f'''# CANONICAL DOCUMENTATION V1 LOCK

STATUS=LOCKED_CURRENT
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
UPDATED_AT_UTC={generated}

ROOT_NAVIGATION_AND_HUMAN_DOCS:
- README.md
- 01_INDEX.md
- 02_MANIFESTO.md
- 03_ROADMAP.md
- 04_ALMANAC.md
- 05_ATLAS.md
- 06_PROJECT_MASTER_STATE.md
- 07_PROJECT_HANDOFF.md

MACHINE_CANONICAL_AUTHORITIES:
- PROJECT_RUNTIME.json
- PROJECT_BOOT.json
- PROJECT_HISTORY.json
- data/tokenoskobi_v1_v8_master_era_roadmap.json

STARTUP_READ_ORDER:
1. PROJECT_RUNTIME.json
2. PROJECT_BOOT.json
3. 06_PROJECT_MASTER_STATE.md
4. 07_PROJECT_HANDOFF.md
5. 02_MANIFESTO.md
6. 03_ROADMAP.md
7. PROJECT_HISTORY.json only when historical context is required

MANDATORY_ERA_AND_V_CLOSURE_UPDATE_SET:
- PROJECT_RUNTIME.json
- PROJECT_BOOT.json
- PROJECT_HISTORY.json
- data/tokenoskobi_v1_v8_master_era_roadmap.json
- 03_ROADMAP.md
- 04_ALMANAC.md
- 05_ATLAS.md
- 06_PROJECT_MASTER_STATE.md
- 07_PROJECT_HANDOFF.md

OPERATIONAL_CLOSURE_COMPANIONS:
- reports/LATEST_TK_AI_HANDOFF.md
- data/control/latest_tk_machine_state.json

CONDITIONAL_NAVIGATION_UPDATE_SET:
- README.md when startup pointers change
- 01_INDEX.md when navigation changes
- docs/canonical/CANONICAL_DOCUMENTATION_V1_LOCK.md when ownership or closure rules change

RULES:
- 02_MANIFESTO.md changes only when doctrine changes.
- Index contains navigation only; no runtime state, heads, timestamps, or history.
- One purpose equals one canonical file.
- No new canonical document is created when an existing owner file can be updated.
- PROJECT_RUNTIME.json is the current-state authority.
- PROJECT_HISTORY.json is append-only.
- `tk machine` is not used by the current canonical flow.

CURRENT_ALIGNMENT:
- ERA54 actual scope: Hot Intelligence Ingress Bounded Runtime
- ERA54 status: CLOSED_VERIFIED_BOUNDED_RUNTIME
- NEWS operational baseline: CLOSED_VERIFIED_BOUNDED_RUNTIME
- Next safe step: {NEXT_STEP}
'''
    atomic_write_text(
        'docs/canonical/CANONICAL_DOCUMENTATION_V1_LOCK.md',
        header.rstrip() + separator + tail,
    )


def main() -> int:
    expected_head = os.environ.get('ERA54_CLOSURE_SYNC_EXPECTED_HEAD', '').strip()
    if not expected_head:
        raise RuntimeError('ERA54_CLOSURE_SYNC_EXPECTED_HEAD_REQUIRED')

    current_head = git_output('rev-parse', 'HEAD')
    branch = git_output('branch', '--show-current')
    status = git_output('status', '--porcelain=v1')
    if current_head != expected_head:
        raise RuntimeError(
            'HEAD_MISMATCH:expected=' + expected_head + ':actual=' + current_head
        )
    if branch != 'main':
        raise RuntimeError('BRANCH_NOT_MAIN:' + branch)
    if status:
        raise RuntimeError('WORKTREE_NOT_CLEAN_AT_START:' + status.replace('\n', '|'))

    generated = utc_now()
    observation = load_json(OBSERVATION)
    if observation.get('decision') != 'OK_POST_ERA54_HOT_INGRESS_BOUND_RUNTIME_FIRST_OBSERVATION_NOAPI':
        raise RuntimeError('OBSERVATION_DECISION_NOT_OK')
    result = observation.get('result', {})
    if result.get('news_operational_baseline_status') != 'CLOSED_VERIFIED_BOUNDED_RUNTIME':
        raise RuntimeError('NEWS_BASELINE_NOT_CLOSED')
    if result.get('observation_status') != 'NATURAL_TIMER_FULL_CYCLE_OBSERVED_AND_VERIFIED':
        raise RuntimeError('NATURAL_TIMER_CYCLE_NOT_VERIFIED')
    if observation.get('failures'):
        raise RuntimeError('OBSERVATION_FAILURES_NOT_EMPTY')

    counts = result.get('db_after_observer', {}).get('counts', {})
    required_counts = {
        'news_raw_feed_events': 372,
        'news_token_match_events': 184,
        'news_signal_events': 184,
        'news_score_events_v1': 184,
        'news_runtime_freshness_v1': 3,
    }
    if counts != required_counts:
        raise RuntimeError(
            'OBSERVATION_COUNTS_MISMATCH:'
            + json.dumps(counts, sort_keys=True)
        )

    summary = result.get('coverage_summary', {})
    market_count = int(summary.get('market_indicator_count', -1))
    adversarial_count = int(summary.get('adversarial_count', -1))
    hot_queue_count = int(result.get('hot_queue_count', -1))
    if (market_count, adversarial_count, hot_queue_count) != (39, 59, 50):
        raise RuntimeError('COVERAGE_OR_QUEUE_COUNT_MISMATCH')

    last_action = {
        'timestamp': generated,
        'task': WORK_UNIT,
        'result': DECISION,
        'artifact': CONTROL_REL,
    }
    work_unit = {
        'id': WORK_UNIT,
        'type': 'ERA54_CLOSURE_DOCUMENTATION_AND_INDEX_SYNC',
        'artifact': CONTROL_REL,
        'module': 'tools/era54_canonical_closure_and_index_sync_noapi_v1.py',
        'status': 'CLOSED',
        'next_step': NEXT_STEP,
    }
    next_safe_step = {'name': NEXT_STEP, 'status': 'READY'}
    checkpoint = {
        'git_branch': 'main',
        'previous_head_before_closure_commit': current_head,
        'technical_closure_head': TECHNICAL_CLOSURE_HEAD,
        'head_semantics': 'PREVIOUS_HEAD_BEFORE_ATOMIC_CLOSURE_COMMIT',
        'source': 'local_git',
    }
    pointer = {
        'authority': 'PROJECT_RUNTIME.json',
        'previous_head_before_closure_commit': current_head,
        'technical_closure_head': TECHNICAL_CLOSURE_HEAD,
        'last_completed': WORK_UNIT,
        'decision': DECISION,
        'era': 'ERA54',
        'era_status': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'news_operational_baseline': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'next_safe_step': NEXT_STEP,
        'updated_at_utc': generated,
    }

    runtime = load_json(ROOT / 'PROJECT_RUNTIME.json')
    runtime['current_era'] = 'ERA54'
    runtime['current_era_status'] = 'CLOSED_VERIFIED_BOUNDED_RUNTIME'
    runtime['current_head'] = 'DYNAMIC_USE_GIT_REV_PARSE_HEAD'
    runtime['current_checkpoint'] = checkpoint
    runtime['current_problem'] = None
    runtime['current_work_unit'] = work_unit
    runtime['last_completed'] = WORK_UNIT
    runtime['last_action'] = last_action
    runtime['mode'] = 'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_CLOSED'
    runtime['next_safe_step'] = next_safe_step
    runtime['project_status'] = 'ACTIVE_NEWS_OPERATIONAL_BASELINE_CLOSED'
    runtime['recent_event'] = last_action
    runtime['source'] = 'era54_canonical_closure_and_index_sync_noapi_v1'
    runtime['status'] = 'WORK_UNIT_CLOSED'
    runtime['updated_at'] = generated
    runtime['updated_at_utc'] = generated
    runtime['canonical_runtime_pointer'] = pointer
    runtime.setdefault('current_state', {})
    runtime['current_state'].update({
        'mode': 'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_CLOSED',
        'runtime_status': 'WORK_UNIT_CLOSED',
        'project_status': 'ACTIVE',
        'updated_at': generated,
        'last_action': last_action,
        'active_work_unit': work_unit,
        'next_safe_step': next_safe_step,
        'current_problem': None,
    })

    era54_status = runtime.setdefault('era54_status', {})
    era54_status.update({
        'era': 'ERA54',
        'title': 'Hot Intelligence Ingress Bounded Runtime',
        'status': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'technical_closure_head': TECHNICAL_CLOSURE_HEAD,
        'final_observation_artifact': str(OBSERVATION.relative_to(ROOT)),
        'final_observation_decision': observation.get('decision'),
        'final_closed_at_utc': observation.get('generated_at_utc'),
        'closure_sync_at_utc': generated,
        'natural_timer_cycle': 'OBSERVED_VERIFIED',
        'news_operational_baseline': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'next_safe_step': NEXT_STEP,
        'new_era_opened': False,
    })

    news_state = runtime.setdefault('news_operational_state', {})
    historical_warnings = news_state.get('historical_known_warnings')
    if not isinstance(historical_warnings, list):
        historical_warnings = []
    old_warnings = news_state.get('known_warnings')
    if isinstance(old_warnings, list):
        for warning in old_warnings:
            if warning not in historical_warnings:
                historical_warnings.append(warning)
    news_state.update({
        'status': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'module_status': 'OPERATIONAL_BASELINE_CLOSED_FUTURE_EVOLUTION_BACKLOG',
        'raw_count': counts['news_raw_feed_events'],
        'match_count': counts['news_token_match_events'],
        'signal_count': counts['news_signal_events'],
        'score_count': counts['news_score_events_v1'],
        'freshness_count': counts['news_runtime_freshness_v1'],
        'market_indicator_count': market_count,
        'adversarial_count': adversarial_count,
        'hot_queue_count': hot_queue_count,
        'hot_queue_bound': 50,
        'timer_active': 'active',
        'timer_enabled': 'enabled',
        'service_result': 'success',
        'hot_gateway_deferred': False,
        'hot_gateway_next': None,
        'panel_bridge_decision': result.get('panel_bridge_decision'),
        'known_warnings': [],
        'historical_known_warnings': historical_warnings,
        'warnings_status': 'OLDER_WARNINGS_SUPERSEDED_BY_VERIFIED_NATURAL_TIMER_CYCLE',
        'final_observation_artifact': str(OBSERVATION.relative_to(ROOT)),
        'technical_closure_head': TECHNICAL_CLOSURE_HEAD,
    })

    runtime['open_risks'] = [
        'Next major project line is not selected yet.',
        'ERA55 is not opened and requires explicit human selection.',
        'Risk is minimized, never zero.',
    ]

    if isinstance(runtime.get('news_coverage_panel_display_state'), dict):
        runtime['news_coverage_panel_display_state'].update({
            'status': 'CLOSED_VERIFIED_CURRENT',
            'market_jsonl_events': market_count,
            'adversarial_jsonl_events': adversarial_count,
            'summary_market_indicator_count': market_count,
            'summary_adversarial_count': adversarial_count,
            'display_market_count': market_count,
            'display_adversarial_count': adversarial_count,
            'current_evidence_artifact': str(OBSERVATION.relative_to(ROOT)),
        })
    if isinstance(runtime.get('hot_intelligence_ingress_gateway_state'), dict):
        runtime['hot_intelligence_ingress_gateway_state'].update({
            'status': 'CLOSED_VERIFIED_BOUND_RUNTIME',
            'hot_queue_count': hot_queue_count,
            'next': NEXT_STEP,
            'current_evidence_artifact': str(OBSERVATION.relative_to(ROOT)),
        })
    if isinstance(runtime.get('news_runtime_stabilization_state'), dict):
        runtime['news_runtime_stabilization_state'].update({
            'status': 'CLOSED_VERIFIED_NATURAL_TIMER_CYCLE',
            'market_jsonl_events': market_count,
            'adversarial_jsonl_events': adversarial_count,
            'summary_market': market_count,
            'summary_adversarial': adversarial_count,
            'hot_queue_count': hot_queue_count,
            'db_counts': counts,
            'warnings': [],
            'current_evidence_artifact': str(OBSERVATION.relative_to(ROOT)),
            'next': NEXT_STEP,
        })
    atomic_write_json('PROJECT_RUNTIME.json', runtime)

    boot = load_json(ROOT / 'PROJECT_BOOT.json')
    boot.setdefault('boot_architecture', {})
    boot['boot_architecture']['new_window_read_order'] = [
        'PROJECT_RUNTIME.json',
        'PROJECT_BOOT.json',
        '06_PROJECT_MASTER_STATE.md',
        '07_PROJECT_HANDOFF.md',
        '02_MANIFESTO.md',
        '03_ROADMAP.md',
        'PROJECT_HISTORY.json only if historical context is required',
    ]
    boot['boot_architecture']['rule'] = (
        'RUNTIME is current-state authority. BOOT is stable doctrine. '
        'HISTORY is append-only and read only when historical context is required.'
    )
    boot['current_checkpoint'] = checkpoint
    boot['current_problem'] = None
    boot['current_work_unit'] = work_unit
    boot['last_completed'] = WORK_UNIT
    boot['last_action'] = last_action
    boot['next_safe_step'] = next_safe_step
    boot['canonical_runtime_pointer'] = pointer
    boot['updated_at'] = generated
    boot['updated_at_utc'] = generated
    boot['new_chat_instruction'] = (
        'Read PROJECT_RUNTIME.json first. ERA54 and the NEWS operational baseline '
        'are closed and verified. Proceed only to ' + NEXT_STEP + '. '
        'Do not reopen HBR, rebuild NEWS from zero, run tk machine, or open ERA55 '
        'without explicit human selection.'
    )
    if isinstance(boot.get('new_window_startup_instruction'), dict):
        boot['new_window_startup_instruction']['instruction'] = boot['new_chat_instruction']
    boot.setdefault('project', {})
    boot['project']['status'] = 'ACTIVE'
    boot['project']['mode'] = 'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_CLOSED'
    boot.setdefault('documentation_status', {})
    boot['documentation_status']['root_canonical_files_expected'] = [
        'README.md',
        '01_INDEX.md',
        '02_MANIFESTO.md',
        '03_ROADMAP.md',
        '04_ALMANAC.md',
        '05_ATLAS.md',
        '06_PROJECT_MASTER_STATE.md',
        '07_PROJECT_HANDOFF.md',
        'PROJECT_BOOT.json',
        'PROJECT_RUNTIME.json',
        'PROJECT_HISTORY.json',
    ]
    boot['documentation_status']['rule_now'] = (
        'Do not create new canonical documentation when an existing owner file can be updated.'
    )
    atomic_write_json('PROJECT_BOOT.json', boot)

    history = load_json(ROOT / 'PROJECT_HISTORY.json')
    events = history.setdefault('events', [])
    if not isinstance(events, list):
        raise RuntimeError('PROJECT_HISTORY_EVENTS_NOT_LIST')
    event_id = 'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_NOAPI_V1'
    if not any(isinstance(item, dict) and item.get('event_id') == event_id for item in events):
        events.append({
            'event_id': event_id,
            'timestamp_utc': generated,
            'era': 'ERA54',
            'work_unit': WORK_UNIT,
            'event': 'FINAL_CANONICAL_CLOSURE_AND_INDEX_SYNC',
            'status': 'CLOSED_READY_FOR_GITHUB_SEAL',
            'technical_closure_head': TECHNICAL_CLOSURE_HEAD,
            'head_before_closure_commit': current_head,
            'news_operational_baseline': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
            'natural_timer_cycle': 'OBSERVED_VERIFIED',
            'counts': counts,
            'market_indicator_count': market_count,
            'adversarial_count': adversarial_count,
            'hot_queue_count': hot_queue_count,
            'updated_files': ALL_CHANGED_FILES,
            'next_safe_step': NEXT_STEP,
        })
    history['updated_at'] = generated
    history['updated_at_utc'] = generated
    atomic_write_json('PROJECT_HISTORY.json', history)

    roadmap = load_json(ROOT / 'data/tokenoskobi_v1_v8_master_era_roadmap.json')
    roadmap['updated_at'] = generated
    roadmap['git_head'] = current_head
    roadmap['git_head_semantics'] = 'PREVIOUS_HEAD_BEFORE_ATOMIC_CLOSURE_COMMIT'
    roadmap['work_unit'] = WORK_UNIT
    roadmap['current_state_authority'] = 'PROJECT_RUNTIME.json'
    closure_rule = roadmap.setdefault('closure_update_rule', {})
    closure_rule['every_era_closure_updates'] = MANDATORY_ERA_CLOSURE_FILES
    closure_rule['every_v_closure_updates'] = MANDATORY_ERA_CLOSURE_FILES
    closure_rule['operational_companion_updates'] = OPERATIONAL_COMPANION_FILES
    closure_rule['conditional_navigation_updates'] = CONDITIONAL_NAVIGATION_FILES
    closure_rule['rule'] = (
        'Every ERA/V closure updates the complete mandatory set. Navigation files '
        'change only when startup/navigation ownership changes.'
    )

    era54_found = False
    era55_found = False
    for version in roadmap.get('versions', []):
        if not isinstance(version, dict) or version.get('id') != 'V3':
            continue
        for child in version.get('children', []):
            if not isinstance(child, dict):
                continue
            if child.get('id') == 'ERA54':
                era54_found = True
                previous_title = child.get('title')
                previous_purpose = child.get('purpose')
                child.update({
                    'title': 'Hot Intelligence Ingress Bounded Runtime',
                    'status': 'CLOSED',
                    'purpose': (
                        'NEWS cold producer, derived refresh, bounded hot ingress queue '
                        'and active panel bridge verified by a natural timer cycle.'
                    ),
                    'depends_on': 'ERA53',
                    'connects_to': 'ERA55_SELECTION_GATE',
                    'actual_scope_override': True,
                    'historical_planned_title': previous_title,
                    'historical_planned_purpose': previous_purpose,
                    'technical_closure_head': TECHNICAL_CLOSURE_HEAD,
                    'closure_artifact': str(OBSERVATION.relative_to(ROOT)),
                    'closure_status': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
                })
            elif child.get('id') == 'ERA55':
                era55_found = True
                child['status'] = 'PLANNED_CANDIDATE_NOT_OPENED'
                child['selection_required'] = True
                child['human_authorization_required'] = True
                child['provisional_only'] = True
                child['depends_on'] = 'ERA54_CLOSED_AND_NEXT_MAJOR_LINE_SELECTION'
    if not era54_found or not era55_found:
        raise RuntimeError('ERA54_OR_ERA55_ROADMAP_NODE_MISSING')

    roadmap['era54_final_closure'] = {
        'status': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'actual_title': 'Hot Intelligence Ingress Bounded Runtime',
        'technical_closure_head': TECHNICAL_CLOSURE_HEAD,
        'observation_artifact': str(OBSERVATION.relative_to(ROOT)),
        'natural_timer_cycle': 'OBSERVED_VERIFIED',
        'news_operational_baseline': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'counts': counts,
        'market_indicator_count': market_count,
        'adversarial_count': adversarial_count,
        'hot_queue_count': hot_queue_count,
        'next_safe_step': NEXT_STEP,
        'era55_opened': False,
    }
    roadmap['post_era54_selection_gate'] = {
        'status': 'READY',
        'next_safe_step': NEXT_STEP,
        'era55_opened': False,
        'rule': 'Do not open ERA55 until the next major line is explicitly selected by the user.',
    }
    atomic_write_json('data/tokenoskobi_v1_v8_master_era_roadmap.json', roadmap)

    current_block = f'''<!-- ERA54_FINAL_CLOSURE_INDEX_SYNC_CURRENT_START -->
## CANONICAL CURRENT STATE — ERA54 FINAL CLOSURE SYNCED

STATE_SYNC_UTC={generated}
PREVIOUS_HEAD_BEFORE_CLOSURE_COMMIT={current_head}
TECHNICAL_CLOSURE_HEAD={TECHNICAL_CLOSURE_HEAD}
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
LAST_COMPLETED={WORK_UNIT}
LAST_DECISION={DECISION}
CURRENT_ERA=ERA54
ERA54_STATUS=CLOSED_VERIFIED_BOUNDED_RUNTIME
NEWS_OPERATIONAL_BASELINE=CLOSED_VERIFIED_BOUNDED_RUNTIME
NATURAL_TIMER_FULL_CYCLE=OBSERVED_VERIFIED
RAW_COUNT={counts['news_raw_feed_events']}
MATCH_COUNT={counts['news_token_match_events']}
SIGNAL_COUNT={counts['news_signal_events']}
SCORE_COUNT={counts['news_score_events_v1']}
MARKET_INDICATOR_COUNT={market_count}
ADVERSARIAL_COUNT={adversarial_count}
HOT_QUEUE_COUNT={hot_queue_count}
HOT_QUEUE_BOUND=50
PANEL_BRIDGE_DECISION={result.get('panel_bridge_decision')}
INDEX_STATUS=CANONICAL_NAVIGATION_CORRECTED
ERA_CLOSURE_DOCUMENT_SET=COMPLETE
ERA55_OPENED=false
NEXT_SAFE_STEP={NEXT_STEP}
<!-- ERA54_FINAL_CLOSURE_INDEX_SYNC_CURRENT_END -->'''

    update_current_markdown('03_ROADMAP.md', current_block)
    roadmap_path = ROOT / '03_ROADMAP.md'
    roadmap_text = roadmap_path.read_text(encoding='utf-8')
    roadmap_text = append_once(
        roadmap_text,
        'ERA54_FINAL_CANONICAL_CLOSURE_ENTRY_V1',
        f'''<!-- ERA54_FINAL_CANONICAL_CLOSURE_ENTRY_V1 -->
## ERA54 FINAL CANONICAL CLOSURE

- Actual scope: `Hot Intelligence Ingress Bounded Runtime`
- Status: `CLOSED_VERIFIED_BOUNDED_RUNTIME`
- Technical closure HEAD: `{TECHNICAL_CLOSURE_HEAD}`
- Natural timer cycle: `OBSERVED_VERIFIED`
- NEWS operational baseline: `CLOSED_VERIFIED_BOUNDED_RUNTIME`
- Master-roadmap old ERA54 title `Massive Scale Processing` is preserved only as historical planning metadata.
- ERA55 is not opened.
- Next: `{NEXT_STEP}`''',
    )
    atomic_write_text('03_ROADMAP.md', roadmap_text)

    update_current_markdown('04_ALMANAC.md', current_block)
    almanac_path = ROOT / '04_ALMANAC.md'
    almanac_text = almanac_path.read_text(encoding='utf-8')
    almanac_text = append_once(
        almanac_text,
        'ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_ENTRY_V1',
        f'''<!-- ERA54_CANONICAL_CLOSURE_AND_INDEX_SYNC_ENTRY_V1 -->
## {WORK_UNIT} — {generated}

- Decision: `{DECISION}`
- ERA54: `CLOSED_VERIFIED_BOUNDED_RUNTIME`
- NEWS baseline: `CLOSED_VERIFIED_BOUNDED_RUNTIME`
- Natural timer cycle: `OBSERVED_VERIFIED`
- DB counts: raw `{counts['news_raw_feed_events']}`, match `{counts['news_token_match_events']}`, signal `{counts['news_signal_events']}`, score `{counts['news_score_events_v1']}`
- Coverage: market `{market_count}`, adversarial `{adversarial_count}`
- Hot queue: `{hot_queue_count}/50`
- Index and README startup pointers corrected.
- Mandatory ERA closure document set completed, including `PROJECT_HISTORY.json` and `05_ATLAS.md`.
- ERA55 opened: `false`
- Next: `{NEXT_STEP}`
- Technical closure HEAD: `{TECHNICAL_CLOSURE_HEAD}`''',
    )
    atomic_write_text('04_ALMANAC.md', almanac_text)

    atlas_path = ROOT / '05_ATLAS.md'
    atlas_original = atlas_path.read_text(encoding='utf-8')
    atlas_block = f'''<!-- ERA54_FINAL_BOUNDED_NEWS_RUNTIME_ATLAS_START -->
## ERA54 FINAL BOUNDED NEWS RUNTIME MAP

UPDATED_UTC: {generated}
STATUS: CLOSED_VERIFIED_BOUNDED_RUNTIME

FLOW:

systemd timer
  -> tokenoskobi-news-radar-refresh.service
  -> tools/news_radar_refresh_runner_v1.py
  -> cold raw producer
  -> derived matcher / signal / score refresh
  -> news coverage readmodel consumer
  -> panel display adapter
  -> hot intelligence ingress gateway
  -> bounded review-only queue (max 50)
  -> active panel data bridge
  -> human review

VERIFIED COUNTS:
- raw: {counts['news_raw_feed_events']}
- match: {counts['news_token_match_events']}
- signal: {counts['news_signal_events']}
- score: {counts['news_score_events_v1']}
- market indicator: {market_count}
- adversarial: {adversarial_count}
- hot queue: {hot_queue_count}/50

AUTHORITY BOUNDARY:
- news context only
- review only
- DB schema change: false
- service/timer configuration change: false
- trade signal: false
- paper trade: false
- live trade: false
- wallet/signing/order authority: false
- AI execution authority: false

EVIDENCE:
- technical closure HEAD: {TECHNICAL_CLOSURE_HEAD}
- natural timer cycle: OBSERVED_VERIFIED
- panel bridge: {result.get('panel_bridge_decision')}
- observation artifact: {OBSERVATION.relative_to(ROOT)}
<!-- ERA54_FINAL_BOUNDED_NEWS_RUNTIME_ATLAS_END -->'''
    atlas_updated = replace_marker_block(
        atlas_original,
        [
            (
                '<!-- ERA54_FINAL_BOUNDED_NEWS_RUNTIME_ATLAS_START -->',
                '<!-- ERA54_FINAL_BOUNDED_NEWS_RUNTIME_ATLAS_END -->',
            )
        ],
        atlas_block,
    )
    atomic_write_text('05_ATLAS.md', atlas_updated)

    update_current_markdown('06_PROJECT_MASTER_STATE.md', current_block)
    update_current_markdown('07_PROJECT_HANDOFF.md', current_block)

    handoff = f'''# LATEST TK AI HANDOFF

{current_block}

## STARTUP ORDER

1. `PROJECT_RUNTIME.json`
2. `PROJECT_BOOT.json`
3. `06_PROJECT_MASTER_STATE.md`
4. `07_PROJECT_HANDOFF.md`
5. `02_MANIFESTO.md`
6. `03_ROADMAP.md`
7. `PROJECT_HISTORY.json` only if history is needed

## BOUNDARIES

- HBR is closed and must not be reopened without an archive-capable input source.
- NEWS must not be rebuilt from zero.
- ERA55 is not open.
- No DB/schema/service/timer/trade-authority change occurred in this closure sync.
- Do not run `tk machine`.
- Proceed only to `{NEXT_STEP}`.
'''
    atomic_write_text('reports/LATEST_TK_AI_HANDOFF.md', handoff)

    tk = load_json(ROOT / 'data/control/latest_tk_machine_state.json')
    tk['collect_mode'] = 'canonical_sync_snapshot_no_tk_machine'
    tk['created_at_utc'] = generated
    tk['generated_by'] = WORK_UNIT
    tk['tk_machine_executed'] = False
    tk['current_state'] = {
        'authority': 'PROJECT_RUNTIME.json',
        'runtime_status': 'WORK_UNIT_CLOSED',
        'active_work_unit': work_unit,
        'next_safe_step': next_safe_step,
        'last_action': last_action,
        'updated_at': generated,
    }
    tk['canonical_runtime_pointer'] = pointer
    tk['graphs_stale_non_authoritative'] = True
    atomic_write_json('data/control/latest_tk_machine_state.json', tk)

    atomic_write_text('01_INDEX.md', INDEX_TEXT)
    atomic_write_text('README.md', README_TEXT)
    update_documentation_lock(generated)

    index_value = (ROOT / '01_INDEX.md').read_text(encoding='utf-8')
    readme_value = (ROOT / 'README.md').read_text(encoding='utf-8')
    index_required = [
        'PROJECT_RUNTIME.json',
        'PROJECT_BOOT.json',
        'PROJECT_HISTORY.json',
        'data/tokenoskobi_v1_v8_master_era_roadmap.json',
        '06_PROJECT_MASTER_STATE.md',
        '07_PROJECT_HANDOFF.md',
    ]
    index_missing = [item for item in index_required if item not in index_value]
    index_forbidden = [
        item for item in [TECHNICAL_CLOSURE_HEAD, generated, 'raw=372']
        if item in index_value
    ]
    readme_forbidden = [
        item for item in ['NEXT_CHAT_HANDOFF.md', 'TOKENOSKOBI_OS_REGISTRY.json', 'tk ai', 'tk sync']
        if item in readme_value
    ]
    if index_missing or index_forbidden or readme_forbidden:
        raise RuntimeError(
            'NAVIGATION_VALIDATION_FAILURE:'
            + json.dumps({
                'index_missing': index_missing,
                'index_forbidden': index_forbidden,
                'readme_forbidden': readme_forbidden,
            }, sort_keys=True)
        )

    artifact = {
        'stage': WORK_UNIT,
        'generated_at_utc': generated,
        'decision': DECISION,
        'decision_id': 'ERA54__CANONICAL_CLOSURE_INDEX_SYNC__' + current_head[:12] + '__' + generated,
        'previous_head_before_closure_commit': current_head,
        'technical_closure_head': TECHNICAL_CLOSURE_HEAD,
        'authority': {
            'github_document_sync': True,
            'db_read': False,
            'db_write': False,
            'db_schema_change': False,
            'network_call': False,
            'api_call': False,
            'service_change': False,
            'timer_change': False,
            'panel_runtime_change': False,
            'tk_machine_run': False,
            'trade_signal': False,
            'paper_trade': False,
            'live_trade': False,
            'wallet_signing': False,
            'new_era_opened': False,
        },
        'failures': [],
        'warnings': [],
        'next': NEXT_STEP,
        'result': {
            'era': 'ERA54',
            'era_status': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
            'actual_era54_title': 'Hot Intelligence Ingress Bounded Runtime',
            'historical_planned_era54_title': 'Massive Scale Processing',
            'news_operational_baseline': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
            'natural_timer_cycle': 'OBSERVED_VERIFIED',
            'counts': counts,
            'market_indicator_count': market_count,
            'adversarial_count': adversarial_count,
            'hot_queue_count': hot_queue_count,
            'hot_queue_bound': 50,
            'panel_bridge_decision': result.get('panel_bridge_decision'),
            'mandatory_closure_files': MANDATORY_ERA_CLOSURE_FILES,
            'conditional_navigation_files': CONDITIONAL_NAVIGATION_FILES,
            'operational_companion_files': OPERATIONAL_COMPANION_FILES,
            'all_changed_files': ALL_CHANGED_FILES,
            'index_navigation_valid': True,
            'readme_startup_pointers_valid': True,
            'project_history_appended': True,
            'atlas_updated': True,
            'master_roadmap_era54_corrected': True,
            'era55_opened': False,
            'next_safe_step': NEXT_STEP,
        },
        'tests': [
            {'id': 'T01_OBSERVATION_DECISION_OK', 'ok': True},
            {'id': 'T02_NATURAL_TIMER_CYCLE_VERIFIED', 'ok': True},
            {'id': 'T03_INDEX_NAVIGATION_ONLY', 'ok': True},
            {'id': 'T04_README_POINTERS_CURRENT', 'ok': True},
            {'id': 'T05_PROJECT_HISTORY_APPENDED', 'ok': True},
            {'id': 'T06_ATLAS_CURRENT_FLOW_UPDATED', 'ok': True},
            {'id': 'T07_MASTER_ROADMAP_ERA54_CORRECTED', 'ok': True},
            {'id': 'T08_ERA55_NOT_OPENED', 'ok': True},
            {'id': 'T09_COMPLETE_CLOSURE_DOCUMENT_SET', 'ok': True},
            {'id': 'T10_NO_RUNTIME_OR_AUTHORITY_MUTATION', 'ok': True},
        ],
    }
    artifact['test_count'] = len(artifact['tests'])
    artifact['ok_count'] = sum(test['ok'] is True for test in artifact['tests'])
    artifact['fail_count'] = artifact['test_count'] - artifact['ok_count']
    atomic_write_json(CONTROL_REL, artifact)

    changed = set(git_output('diff', '--name-only').splitlines())
    expected_changed = set(ALL_CHANGED_FILES)
    if changed != expected_changed:
        raise RuntimeError(
            'CHANGED_FILE_SET_MISMATCH:'
            + json.dumps({
                'expected': sorted(expected_changed),
                'actual': sorted(changed),
                'missing': sorted(expected_changed - changed),
                'unexpected': sorted(changed - expected_changed),
            }, sort_keys=True)
        )

    print(json.dumps({
        'decision': DECISION,
        'era_status': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'news_operational_baseline': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'index_navigation_valid': True,
        'mandatory_closure_file_count': len(MANDATORY_ERA_CLOSURE_FILES),
        'total_changed_file_count': len(ALL_CHANGED_FILES),
        'era55_opened': False,
        'next_safe_step': NEXT_STEP,
        'artifact': CONTROL_REL,
    }, ensure_ascii=False, indent=2, sort_keys=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
