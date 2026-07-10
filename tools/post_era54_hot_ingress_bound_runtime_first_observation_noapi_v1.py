#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import time

ROOT = Path('/root/tokenoskobi_clean_v1')
WORK_UNIT = 'POST_ERA54_HOT_INGRESS_BOUND_RUNTIME_FIRST_OBSERVATION_NOAPI'
DECISION = 'OK_POST_ERA54_HOT_INGRESS_BOUND_RUNTIME_FIRST_OBSERVATION_NOAPI'
NEXT_STEP = 'NEXT_MAJOR_PROJECT_LINE_SELECTION_AFTER_NEWS_OPERATIONAL_BASELINE_CLOSURE'

INTEGRATION = ROOT / 'data/control/post_era54_hot_ingress_bounded_runtime_integration_noapi_v1.json'
DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
SERVICE = 'tokenoskobi-news-radar-refresh.service'
TIMER = 'tokenoskobi-news-radar-refresh.timer'

HOT_REFRESH_STATE = ROOT / 'runtime/state/news_hot_ingress_bounded_runtime_refresh_v1.json'
SUMMARY = ROOT / 'runtime/state/news_coverage_readmodel_consumer_summary_v1.json'
DISPLAY = ROOT / 'runtime/state/news_coverage_panel_display_v1.json'
HOT = ROOT / 'runtime/state/hot_intelligence_ingress_gateway_v1.json'
BRIDGE = ROOT / 'runtime/state/news_active_panel_data_bridge_v1.json'
TRACKER = ROOT / 'runtime/state/news_processed_tracker_v1.json'
MARKET_JSONL = ROOT / 'runtime/state/news_market_indicator_events_v1.jsonl'
ADVERSARIAL_JSONL = ROOT / 'runtime/state/news_adversarial_events_v1.jsonl'

CONTROL_REL = 'data/control/post_era54_hot_ingress_bound_runtime_first_observation_noapi_v1.json'
DOC_REL = 'docs/canonical/POST_ERA54_HOT_INGRESS_BOUND_RUNTIME_FIRST_OBSERVATION_NOAPI_V1.md'
TOOL_REL = 'tools/post_era54_hot_ingress_bound_runtime_first_observation_noapi_v1.py'

TABLES = [
    'news_raw_feed_events',
    'news_token_match_events',
    'news_signal_events',
    'news_score_events_v1',
    'news_runtime_freshness_v1',
]

DYNAMIC_PATHS = [
    'runtime/state/news_market_indicator_events_v1.jsonl',
    'runtime/state/news_adversarial_events_v1.jsonl',
    'runtime/state/news_coverage_readmodel_consumer_summary_v1.json',
    'runtime/state/news_market_indicator_latest_v1.json',
    'runtime/state/news_adversarial_latest_v1.json',
    'runtime/state/news_coverage_panel_display_v1.json',
    'runtime/state/news_coverage_panel_display_v1.html',
    'runtime/state/hot_intelligence_ingress_gateway_v1.json',
    'runtime/state/news_active_panel_data_bridge_v1.json',
    'active_panel_8096/current/data/news_coverage_readmodel_consumer_summary_v1.json',
    'active_panel_8096/current/data/news_market_indicator_latest_v1.json',
    'active_panel_8096/current/data/news_adversarial_latest_v1.json',
    'active_panel_8096/current/data/news_coverage_panel_display_v1.json',
    'active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json',
    'active_panel_8096/current/data/news_runtime_stabilization_review_v1.json',
    'active_panel_8096/current/data/news_producer_health_watch_and_hot_gateway_review_v1.json',
    'active_panel_8096/current/data/news_active_panel_data_bridge_manifest_v1.json',
]

ACTIVE_COPY_PAIRS = {
    'news_coverage_readmodel_consumer_summary_v1.json': SUMMARY,
    'news_market_indicator_latest_v1.json': ROOT / 'runtime/state/news_market_indicator_latest_v1.json',
    'news_adversarial_latest_v1.json': ROOT / 'runtime/state/news_adversarial_latest_v1.json',
    'news_coverage_panel_display_v1.json': DISPLAY,
    'hot_intelligence_ingress_gateway_v1.json': HOT,
    'news_runtime_stabilization_review_v1.json': ROOT / 'runtime/state/news_runtime_stabilization_review_v1.json',
    'news_producer_health_watch_and_hot_gateway_review_v1.json': ROOT / 'runtime/state/news_producer_health_watch_and_hot_gateway_review_v1.json',
}

REQUIRED_HOT_STEPS = {
    'consumer',
    'display_adapter',
    'hot_gateway',
    'active_panel_bridge',
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value: str) -> datetime:
    text = str(value or '').strip().replace('Z', '+00:00')
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_systemd_timestamp(value: str) -> datetime | None:
    text = str(value or '').strip()
    if not text or text == 'n/a':
        return None
    completed = subprocess.run(
        ['date', '-u', '-d', text, '+%Y-%m-%dT%H:%M:%S.%N+00:00'],
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return None
    try:
        return parse_dt(completed.stdout.strip())
    except Exception:
        return None


def run(args: list[str], timeout: int = 60, check: bool = False) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            'COMMAND_FAILED:' + ' '.join(args)
            + ':rc=' + str(completed.returncode)
            + ':stderr=' + completed.stderr.strip()
        )
    return completed


def git_output(*args: str) -> str:
    return run(['git', *args], check=True).stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError('JSON_OBJECT_REQUIRED:' + str(path))
    return value


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def jsonl_stats(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            'exists': False,
            'line_count': 0,
            'parse_errors': 0,
            'duplicate_event_uid_count': 0,
            'unsafe_events': 0,
            'sha256': None,
        }
    line_count = 0
    parse_errors = 0
    duplicate_event_uids = 0
    unsafe_events = 0
    seen: set[str] = set()
    with path.open('r', encoding='utf-8') as handle:
        for line in handle:
            if not line.strip():
                continue
            line_count += 1
            try:
                obj = json.loads(line)
            except Exception:
                parse_errors += 1
                continue
            if not isinstance(obj, dict):
                parse_errors += 1
                continue
            uid = str(obj.get('event_uid') or '').strip()
            if uid:
                if uid in seen:
                    duplicate_event_uids += 1
                seen.add(uid)
            if (
                obj.get('hunter_authorized') is not False
                or obj.get('db_match_write') is not False
                or obj.get('trade_signal') is not False
                or obj.get('paper_signal') is not False
            ):
                unsafe_events += 1
    return {
        'exists': True,
        'line_count': line_count,
        'parse_errors': parse_errors,
        'duplicate_event_uid_count': duplicate_event_uids,
        'unsafe_events': unsafe_events,
        'sha256': sha256_file(path),
    }


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def db_snapshot() -> dict[str, Any]:
    connection = sqlite3.connect(
        'file:' + str(DB) + '?mode=ro',
        uri=True,
        timeout=10,
    )
    try:
        connection.execute('PRAGMA query_only=ON')
        existing = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        missing = [table for table in TABLES if table not in existing]
        counts = {
            table: int(
                connection.execute(
                    'SELECT COUNT(*) FROM ' + quote_identifier(table)
                ).fetchone()[0]
            )
            for table in TABLES
            if table in existing
        }
        return {
            'query_only': bool(
                connection.execute('PRAGMA query_only').fetchone()[0]
            ),
            'total_changes': connection.total_changes,
            'integrity': str(
                connection.execute('PRAGMA integrity_check').fetchone()[0]
            ),
            'missing_tables': missing,
            'counts': counts,
        }
    finally:
        connection.close()


def systemd_show(unit: str, properties: list[str]) -> dict[str, str]:
    args = ['systemctl', 'show', unit]
    for prop in properties:
        args.extend(['-p', prop])
    completed = run(args)
    result: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            result[key] = value
    result['_rc'] = str(completed.returncode)
    return result


def systemd_snapshot() -> dict[str, Any]:
    service = systemd_show(
        SERVICE,
        [
            'ActiveState',
            'SubState',
            'Result',
            'ExecMainStatus',
            'ExecMainStartTimestamp',
            'ExecMainExitTimestamp',
            'FragmentPath',
        ],
    )
    timer = systemd_show(
        TIMER,
        [
            'ActiveState',
            'SubState',
            'Result',
            'LastTriggerUSec',
            'NextElapseUSecRealtime',
            'FragmentPath',
        ],
    )
    service_enabled = run(['systemctl', 'is-enabled', SERVICE])
    timer_enabled = run(['systemctl', 'is-enabled', TIMER])
    service['EnabledState'] = service_enabled.stdout.strip()
    service['EnabledRC'] = str(service_enabled.returncode)
    timer['EnabledState'] = timer_enabled.stdout.strip()
    timer['EnabledRC'] = str(timer_enabled.returncode)
    for item in [service, timer]:
        fragment = Path(item.get('FragmentPath') or '')
        item['FragmentSHA256'] = (
            sha256_file(fragment) if fragment.is_file() else None
        )
    return {'service': service, 'timer': timer}


def journal_since(value: str) -> str:
    since = parse_dt(value).strftime('%Y-%m-%d %H:%M:%S UTC')
    completed = run(
        [
            'journalctl',
            '-u', SERVICE,
            '--since', since,
            '--no-pager',
            '--output=short-iso-precise',
        ],
        timeout=90,
    )
    return (
        (completed.stdout or '')
        + ('\n' + completed.stderr if completed.stderr else '')
    )


def natural_cycle_evidence(
    integration_time: datetime,
    journal_text: str,
    systemd: dict[str, Any],
) -> dict[str, Any]:
    service = systemd['service']
    start_time = parse_systemd_timestamp(
        service.get('ExecMainStartTimestamp', '')
    )
    exit_time = parse_systemd_timestamp(
        service.get('ExecMainExitTimestamp', '')
    )

    journal_hot_marker = (
        'OK_NEWS_HOT_INGRESS_BOUNDED_RUNTIME_REFRESH_V1'
        in journal_text
    )
    journal_wrapper_marker = (
        'NEWS_SYSTEMD_TIMER_DERIVED_REFRESH' in journal_text
        or 'TOKENOSKOBI_WRAPPER_TRACE_V1' in journal_text
        or 'final_return_after_downstream_hook' in journal_text
    )

    runtime_state_exists = HOT_REFRESH_STATE.exists()
    runtime_state: dict[str, Any] = {}
    runtime_state_error: str | None = None
    hot_generated: datetime | None = None
    hot_finished: datetime | None = None
    hot_decision_ok = False
    hot_steps_ok = False
    hot_runtime_after_binding = False
    hot_runtime_correlated = False

    if runtime_state_exists:
        try:
            runtime_state = load_json(HOT_REFRESH_STATE)
            hot_decision_ok = (
                runtime_state.get('decision')
                == 'OK_NEWS_HOT_INGRESS_BOUNDED_RUNTIME_REFRESH_V1'
            )
            hot_generated = parse_dt(
                str(runtime_state.get('generated_at_utc') or '')
            )
            hot_finished = parse_dt(
                str(runtime_state.get('finished_at_utc') or '')
            )
            steps = runtime_state.get('steps')
            if isinstance(steps, list):
                step_by_name = {
                    str(step.get('name')): step
                    for step in steps
                    if isinstance(step, dict)
                }
                hot_steps_ok = (
                    REQUIRED_HOT_STEPS.issubset(set(step_by_name))
                    and all(
                        int(step_by_name[name].get('rc', -1)) == 0
                        for name in REQUIRED_HOT_STEPS
                    )
                )
            hot_runtime_after_binding = hot_generated > integration_time
            if start_time and exit_time:
                hot_runtime_correlated = bool(
                    (hot_generated - start_time).total_seconds() >= -5
                    and (hot_finished - start_time).total_seconds() >= -5
                    and (hot_finished - exit_time).total_seconds() <= 10
                    and hot_finished >= hot_generated
                )
        except Exception as exc:
            runtime_state_error = repr(exc)

    runtime_hot_marker = bool(
        hot_decision_ok
        and hot_runtime_after_binding
        and hot_runtime_correlated
    )
    runtime_wrapper_marker = bool(
        hot_steps_ok
        and hot_runtime_after_binding
        and hot_runtime_correlated
    )
    marker_hot = bool(journal_hot_marker or runtime_hot_marker)
    marker_wrapper = bool(
        journal_wrapper_marker or runtime_wrapper_marker
    )
    exit_after_binding = bool(
        exit_time and exit_time > integration_time
    )
    successful_exit = (
        service.get('Result') == 'success'
        and service.get('ExecMainStatus') == '0'
        and service.get('ActiveState') == 'inactive'
    )
    observed = bool(
        marker_hot
        and marker_wrapper
        and exit_after_binding
        and successful_exit
    )

    if runtime_hot_marker and runtime_wrapper_marker:
        evidence_source = (
            'RUNTIME_STATE_CORRELATED_TO_SYSTEMD_SERVICE_CYCLE'
        )
    elif journal_hot_marker and journal_wrapper_marker:
        evidence_source = 'JOURNAL_MARKERS'
    else:
        evidence_source = 'INSUFFICIENT'

    return {
        'observed': observed,
        'evidence_source': evidence_source,
        'hot_refresh_marker': marker_hot,
        'wrapper_or_derived_marker': marker_wrapper,
        'journal_hot_marker': journal_hot_marker,
        'journal_wrapper_or_derived_marker': journal_wrapper_marker,
        'runtime_state_exists': runtime_state_exists,
        'runtime_state_error': runtime_state_error,
        'runtime_state_decision': runtime_state.get('decision'),
        'runtime_state_generated_at_utc': (
            hot_generated.isoformat() if hot_generated else None
        ),
        'runtime_state_finished_at_utc': (
            hot_finished.isoformat() if hot_finished else None
        ),
        'runtime_state_steps_ok': hot_steps_ok,
        'runtime_state_after_binding': hot_runtime_after_binding,
        'runtime_state_correlated_to_service_cycle': (
            hot_runtime_correlated
        ),
        'service_start_time_utc': (
            start_time.isoformat() if start_time else None
        ),
        'service_exit_after_binding': exit_after_binding,
        'service_success': successful_exit,
        'service_exit_time_utc': (
            exit_time.isoformat() if exit_time else None
        ),
    }


def wait_for_natural_cycle(
    integration_time_text: str,
    max_wait_seconds: int,
) -> dict[str, Any]:
    integration_time = parse_dt(integration_time_text)
    started_monotonic = time.monotonic()
    attempts = 0
    last: dict[str, Any] = {}
    while True:
        attempts += 1
        systemd = systemd_snapshot()
        journal = journal_since(integration_time_text)
        evidence = natural_cycle_evidence(
            integration_time,
            journal,
            systemd,
        )
        last = {
            'attempts': attempts,
            'elapsed_seconds': int(
                time.monotonic() - started_monotonic
            ),
            'systemd': systemd,
            'evidence': evidence,
            'journal_line_count': len(
                [line for line in journal.splitlines() if line.strip()]
            ),
            'journal_tail': '\n'.join(
                journal.splitlines()[-120:]
            ),
        }
        if evidence['observed']:
            return last
        elapsed = time.monotonic() - started_monotonic
        if elapsed >= max_wait_seconds:
            raise RuntimeError(
                'NATURAL_TIMER_CYCLE_NOT_OBSERVED_WITHIN_BOUND:'
                + json.dumps(last, ensure_ascii=False, sort_keys=True)
            )
        if attempts == 1 or attempts % 6 == 0:
            print(
                'OBSERVATION_PENDING elapsed_seconds='
                + str(int(elapsed))
                + ' timer_last_trigger='
                + str(systemd['timer'].get('LastTriggerUSec')),
                flush=True,
            )
        time.sleep(10)


def validate_authority(
    authority: Any,
    prefix: str,
    failures: list[str],
) -> None:
    if not isinstance(authority, dict):
        failures.append(prefix + ':authority_missing')
        return
    for key in [
        'db_write',
        'db_schema_change',
        'hunter_authorized',
        'trade_signal',
        'paper_signal',
        'live_trade',
        'execution_authority',
        'service_change',
        'timer_change',
        'network_call',
        'external_api_call',
    ]:
        if key in authority and authority.get(key) is not False:
            failures.append(prefix + ':' + key + '_not_false')


def atomic_write_text(path: Path, text: str) -> None:
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


def atomic_write_json(
    relative: str,
    value: dict[str, Any],
) -> None:
    atomic_write_text(
        ROOT / relative,
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
        ) + '\n',
    )


def replace_current_block(original: str, block: str) -> str:
    marker_sets = [
        (
            '<!-- POST_ERA54_HOT_INGRESS_BOUND_CURRENT_START -->',
            '<!-- POST_ERA54_HOT_INGRESS_BOUND_CURRENT_END -->',
        ),
        (
            '<!-- POST_ERA54_HOT_FIRST_OBSERVATION_CURRENT_START -->',
            '<!-- POST_ERA54_HOT_FIRST_OBSERVATION_CURRENT_END -->',
        ),
    ]
    replacement = block.rstrip() + '\n\n'
    for start, end in marker_sets:
        pattern = re.compile(
            re.escape(start) + r'.*?' + re.escape(end) + r'\n*',
            re.S,
        )
        if pattern.search(original):
            return pattern.sub(replacement, original, count=1)
    return replacement + original.lstrip('\ufeff')


def update_markdown(
    relative: str,
    block: str,
    append: str | None = None,
) -> None:
    path = ROOT / relative
    updated = replace_current_block(
        path.read_text(encoding='utf-8'),
        block,
    )
    if append and append.strip() not in updated:
        updated = (
            updated.rstrip()
            + '\n\n'
            + append.rstrip()
            + '\n'
        )
    atomic_write_text(path, updated)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--max-wait-seconds',
        type=int,
        default=0,
    )
    args = parser.parse_args()

    expected_head = os.environ.get(
        'POST_ERA54_OBSERVATION_EXPECTED_HEAD',
        '',
    ).strip()
    if not expected_head:
        raise RuntimeError(
            'POST_ERA54_OBSERVATION_EXPECTED_HEAD_REQUIRED'
        )
    if args.max_wait_seconds < 0 or args.max_wait_seconds > 3600:
        raise RuntimeError('MAX_WAIT_SECONDS_OUT_OF_RANGE')

    current_head = git_output('rev-parse', 'HEAD')
    branch = git_output('branch', '--show-current')
    if current_head != expected_head:
        raise RuntimeError(
            'HEAD_MISMATCH:expected=' + expected_head
            + ':actual=' + current_head
        )
    if branch != 'main':
        raise RuntimeError('BRANCH_NOT_MAIN:' + branch)
    if git_output('status', '--porcelain=v1'):
        raise RuntimeError(
            'WORKTREE_NOT_CLEAN_AT_OBSERVATION_START'
        )

    integration = load_json(INTEGRATION)
    if (
        integration.get('decision')
        != 'OK_POST_ERA54_HOT_INGRESS_BOUNDED_RUNTIME_INTEGRATION_NOAPI'
    ):
        raise RuntimeError('INTEGRATION_DECISION_NOT_OK')
    if integration.get('next') != WORK_UNIT:
        raise RuntimeError('INTEGRATION_NEXT_MISMATCH')

    integration_time_text = str(
        integration.get('generated_at_utc') or ''
    )
    integration_time = parse_dt(integration_time_text)
    integration_result = integration.get('result', {})
    integration_counts = (
        integration_result.get('db_after', {}).get('counts', {})
    )
    integration_service_snapshot = (
        integration_result.get('service_snapshot', {})
    )

    tracked_dynamic = [
        line
        for line in git_output(
            'ls-files',
            '--',
            *DYNAMIC_PATHS,
        ).splitlines()
        if line.strip()
    ]
    if tracked_dynamic:
        raise RuntimeError(
            'DYNAMIC_OUTPUTS_STILL_TRACKED:'
            + ','.join(tracked_dynamic)
        )
    missing_dynamic = [
        path
        for path in DYNAMIC_PATHS
        if not (ROOT / path).exists()
    ]
    if missing_dynamic:
        raise RuntimeError(
            'DYNAMIC_LOCAL_FILES_MISSING:'
            + ','.join(missing_dynamic)
        )
    not_ignored = [
        path
        for path in DYNAMIC_PATHS
        if run(['git', 'check-ignore', '-q', path]).returncode != 0
    ]
    if not_ignored:
        raise RuntimeError(
            'DYNAMIC_OUTPUTS_NOT_IGNORED:'
            + ','.join(not_ignored)
        )

    systemd_before = systemd_snapshot()
    db_before = db_snapshot()
    market_before = jsonl_stats(MARKET_JSONL)
    adversarial_before = jsonl_stats(ADVERSARIAL_JSONL)

    observation = wait_for_natural_cycle(
        integration_time_text,
        args.max_wait_seconds,
    )

    systemd_after = systemd_snapshot()
    db_after = db_snapshot()
    market_after = jsonl_stats(MARKET_JSONL)
    adversarial_after = jsonl_stats(ADVERSARIAL_JSONL)

    failures: list[str] = []
    warnings: list[str] = []

    evidence = observation['evidence']
    if not evidence.get('observed'):
        failures.append('natural_cycle_not_observed')
    if systemd_after['timer'].get('ActiveState') != 'active':
        failures.append('timer_not_active')
    if systemd_after['timer'].get('EnabledState') != 'enabled':
        failures.append('timer_not_enabled')
    if systemd_after['service'].get('Result') != 'success':
        failures.append('service_result_not_success')
    if systemd_after['service'].get('ExecMainStatus') != '0':
        failures.append('service_exec_main_status_not_zero')

    integration_service = integration_service_snapshot.get(
        SERVICE,
        {},
    )
    integration_timer = integration_service_snapshot.get(
        TIMER,
        {},
    )
    service_unit_sha_unchanged = (
        systemd_after['service'].get('FragmentSHA256')
        == integration_service.get('FragmentSHA256')
    )
    timer_unit_sha_unchanged = (
        systemd_after['timer'].get('FragmentSHA256')
        == integration_timer.get('FragmentSHA256')
    )
    if not service_unit_sha_unchanged:
        failures.append('service_unit_file_changed')
    if not timer_unit_sha_unchanged:
        failures.append('timer_unit_file_changed')

    if db_after.get('integrity') != 'ok':
        failures.append('db_integrity_not_ok')
    if db_after.get('missing_tables'):
        failures.append('db_missing_tables')
    if (
        db_after.get('query_only') is not True
        or db_after.get('total_changes') != 0
    ):
        failures.append('observer_db_snapshot_not_readonly')

    counts_after = db_after.get('counts', {})
    for table in TABLES:
        baseline = integration_counts.get(table)
        current = counts_after.get(table)
        if not isinstance(baseline, int) or not isinstance(current, int):
            failures.append('db_count_missing:' + table)
        elif current < baseline:
            failures.append('db_count_regressed:' + table)

    match_count = counts_after.get('news_token_match_events')
    signal_count = counts_after.get('news_signal_events')
    score_count = counts_after.get('news_score_events_v1')
    derived_counts_equal = (
        match_count == signal_count == score_count
    )
    if not derived_counts_equal:
        failures.append('derived_counts_not_equal')

    for lane_name, stats in [
        ('market', market_after),
        ('adversarial', adversarial_after),
    ]:
        if stats.get('exists') is not True:
            failures.append(lane_name + '_jsonl_missing')
        if stats.get('parse_errors') != 0:
            failures.append(lane_name + '_jsonl_parse_errors')
        if stats.get('duplicate_event_uid_count') != 0:
            failures.append(
                lane_name + '_jsonl_duplicate_event_uid'
            )
        if stats.get('unsafe_events') != 0:
            failures.append(lane_name + '_jsonl_unsafe_events')

    required_json = [
        HOT_REFRESH_STATE,
        SUMMARY,
        DISPLAY,
        HOT,
        BRIDGE,
    ]
    missing_json = [
        str(path.relative_to(ROOT))
        for path in required_json
        if not path.exists()
    ]
    if missing_json:
        failures.append(
            'required_runtime_json_missing:'
            + ','.join(missing_json)
        )

    hot_refresh: dict[str, Any] = {}
    summary: dict[str, Any] = {}
    display: dict[str, Any] = {}
    hot: dict[str, Any] = {}
    bridge: dict[str, Any] = {}
    tracker: dict[str, Any] = {}

    if not missing_json:
        hot_refresh = load_json(HOT_REFRESH_STATE)
        summary = load_json(SUMMARY)
        display = load_json(DISPLAY)
        hot = load_json(HOT)
        bridge = load_json(BRIDGE)
        tracker = load_json(TRACKER) if TRACKER.exists() else {}

        if (
            hot_refresh.get('decision')
            != 'OK_NEWS_HOT_INGRESS_BOUNDED_RUNTIME_REFRESH_V1'
        ):
            failures.append('hot_refresh_decision_not_ok')
        try:
            hot_generated = parse_dt(
                str(hot_refresh.get('generated_at_utc') or '')
            )
            if hot_generated <= integration_time:
                failures.append('hot_refresh_not_after_integration')
        except Exception:
            failures.append('hot_refresh_generated_at_invalid')

        for prefix, obj in [
            ('hot_refresh', hot_refresh),
            ('summary', summary),
            ('display', display),
            ('hot', hot),
            ('bridge', bridge),
        ]:
            validate_authority(
                obj.get('authority'),
                prefix,
                failures,
            )

        for key in [
            'parse_errors',
            'duplicate_event_uids',
            'unsafe_events',
        ]:
            if int(summary.get(key, -1)) != 0:
                failures.append('summary_' + key + '_nonzero')

        health = display.get('health') or {}
        if health.get('source_authority_ok') is not True:
            failures.append('display_source_authority_not_ok')
        for key in [
            'parse_errors',
            'duplicate_event_uids',
            'unsafe_events',
        ]:
            if int(health.get(key, -1)) != 0:
                failures.append('display_' + key + '_nonzero')

        queue = hot.get('hot_queue')
        queue_count = hot.get('hot_queue_count')
        if not isinstance(queue, list) or not isinstance(queue_count, int):
            failures.append('hot_queue_contract_invalid')
        else:
            if queue_count != len(queue):
                failures.append('hot_queue_count_mismatch')
            if queue_count < 0 or queue_count > 50:
                failures.append('hot_queue_out_of_bound')
            for item in queue:
                if not isinstance(item, dict):
                    failures.append('hot_queue_item_not_object')
                    continue
                if item.get('gateway_decision') != 'REVIEW_ONLY':
                    failures.append(
                        'hot_queue_item_not_review_only'
                    )
                validate_authority(
                    item.get('authority'),
                    'hot_item',
                    failures,
                )

        if (
            bridge.get('decision')
            != 'OK_NEWS_ACTIVE_PANEL_DATA_BRIDGE_APPLIED'
        ):
            failures.append('panel_bridge_decision_not_ok')
        hash_match = bridge.get('hash_match')
        if (
            not isinstance(hash_match, dict)
            or not hash_match
            or not all(value is True for value in hash_match.values())
        ):
            failures.append(
                'panel_bridge_hash_match_not_all_true'
            )

    active_data = ROOT / 'active_panel_8096/current/data'
    active_hashes: dict[str, Any] = {}
    for name, source in ACTIVE_COPY_PAIRS.items():
        target = active_data / name
        source_sha = sha256_file(source)
        target_sha = sha256_file(target)
        active_hashes[name] = {
            'source_sha256': source_sha,
            'target_sha256': target_sha,
            'match': bool(
                source_sha and source_sha == target_sha
            ),
        }
        if not active_hashes[name]['match']:
            failures.append(
                'active_panel_hash_mismatch:' + name
            )

    tracker_alignment: dict[str, Any] = {
        'exists': TRACKER.exists(),
    }
    if tracker:
        tracker_alignment.update({
            'last_raw_count_seen': tracker.get(
                'last_raw_count_seen'
            ),
            'last_match_count_seen': tracker.get(
                'last_match_count_seen'
            ),
            'last_signal_count_seen': tracker.get(
                'last_signal_count_seen'
            ),
            'last_score_count_seen': tracker.get(
                'last_score_count_seen'
            ),
            'processed_news_uid_count': len(
                tracker.get('processed_news_uids') or []
            ),
            'last_success_batch': tracker.get(
                'last_success_batch'
            ),
        })
    else:
        warnings.append('processed_tracker_missing_or_empty')

    if failures:
        raise RuntimeError(
            'OBSERVATION_VALIDATION_FAILURE:'
            + '|'.join(failures)
        )

    generated = utc_now()
    decision_id = (
        'POST_ERA54__HOT_INGRESS_FIRST_OBSERVATION__'
        + current_head[:12]
        + '__'
        + generated
    )
    db_delta_from_integration = {
        table: counts_after[table] - integration_counts[table]
        for table in TABLES
    }
    db_delta_during_observer = {
        table: (
            db_after['counts'][table]
            - db_before['counts'][table]
        )
        for table in TABLES
    }

    artifact: dict[str, Any] = {
        'stage': WORK_UNIT,
        'generated_at_utc': generated,
        'decision': DECISION,
        'decision_id': decision_id,
        'previous_head_before_closure_commit': current_head,
        'authority': {
            'api_call_by_observer': False,
            'network_call_by_observer': False,
            'db_read': True,
            'db_read_mode': 'SQLITE_MODE_RO_QUERY_ONLY',
            'db_write_by_observer': False,
            'db_schema_change': False,
            'service_configuration_change': False,
            'timer_configuration_change': False,
            'natural_timer_cycle_observed': True,
            'panel_data_write_by_existing_runtime': True,
            'hunter_authorized': False,
            'trade_signal': False,
            'paper_signal': False,
            'live_trade': False,
            'execution_authority': False,
            'new_era_opened': False,
        },
        'failures': [],
        'warnings': warnings,
        'next': NEXT_STEP,
        'result': {
            'integration_decision': integration.get('decision'),
            'integration_generated_at_utc': integration_time_text,
            'observation_status': (
                'NATURAL_TIMER_FULL_CYCLE_OBSERVED_AND_VERIFIED'
            ),
            'news_operational_baseline_status': (
                'CLOSED_VERIFIED_BOUNDED_RUNTIME'
            ),
            'news_module_status': (
                'OPERATIONAL_BASELINE_CLOSED_FUTURE_EVOLUTION_BACKLOG'
            ),
            'current_era': 'ERA54_CLOSED',
            'new_era_opened': False,
            'natural_cycle': observation,
            'systemd_before': systemd_before,
            'systemd_after': systemd_after,
            'service_unit_sha_unchanged': (
                service_unit_sha_unchanged
            ),
            'timer_unit_sha_unchanged': (
                timer_unit_sha_unchanged
            ),
            'db_before_observer': db_before,
            'db_after_observer': db_after,
            'db_delta_during_observer': (
                db_delta_during_observer
            ),
            'db_delta_from_integration_baseline': (
                db_delta_from_integration
            ),
            'derived_counts_equal': derived_counts_equal,
            'market_jsonl_before': market_before,
            'market_jsonl_after': market_after,
            'adversarial_jsonl_before': adversarial_before,
            'adversarial_jsonl_after': adversarial_after,
            'hot_refresh_state': {
                'decision': hot_refresh.get('decision'),
                'generated_at_utc': hot_refresh.get(
                    'generated_at_utc'
                ),
                'finished_at_utc': hot_refresh.get(
                    'finished_at_utc'
                ),
                'steps': hot_refresh.get('steps'),
            },
            'coverage_summary': {
                'market_indicator_count': summary.get(
                    'market_indicator_count'
                ),
                'adversarial_count': summary.get(
                    'adversarial_count'
                ),
                'parse_errors': summary.get('parse_errors'),
                'duplicate_event_uids': summary.get(
                    'duplicate_event_uids'
                ),
                'unsafe_events': summary.get('unsafe_events'),
            },
            'hot_queue_count': hot.get('hot_queue_count'),
            'hot_queue_bound': 50,
            'panel_bridge_decision': bridge.get('decision'),
            'active_panel_hashes': active_hashes,
            'tracker_alignment': tracker_alignment,
            'next_safe_step': NEXT_STEP,
        },
    }
    atomic_write_json(CONTROL_REL, artifact)

    last_action = {
        'timestamp': generated,
        'task': WORK_UNIT,
        'result': DECISION,
        'artifact': CONTROL_REL,
    }
    active_work_unit = {
        'id': WORK_UNIT,
        'type': 'NEWS_OPERATIONAL_BASELINE_FIRST_NATURAL_CYCLE_OBSERVATION',
        'artifact': CONTROL_REL,
        'module': TOOL_REL,
        'status': 'CLOSED',
        'next_step': NEXT_STEP,
    }
    next_safe_step = {
        'name': NEXT_STEP,
        'status': 'READY',
    }
    runtime_pointer = {
        'authority': 'PROJECT_RUNTIME.json',
        'previous_head_before_closure_commit': current_head,
        'last_completed': WORK_UNIT,
        'decision': DECISION,
        'news_operational_baseline_status': (
            'CLOSED_VERIFIED_BOUNDED_RUNTIME'
        ),
        'natural_cycle_evidence_source': evidence.get(
            'evidence_source'
        ),
        'next_safe_step': NEXT_STEP,
        'updated_at_utc': generated,
    }

    runtime = load_json(ROOT / 'PROJECT_RUNTIME.json')
    runtime.setdefault('current_state', {})
    runtime['current_state'].update({
        'mode': 'NEWS_OPERATIONAL_BASELINE_CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'runtime_status': 'WORK_UNIT_CLOSED',
        'project_status': 'ACTIVE',
        'updated_at': generated,
        'last_action': last_action,
        'active_work_unit': active_work_unit,
        'next_safe_step': next_safe_step,
        'current_problem': None,
    })
    runtime['current_work_unit'] = active_work_unit
    runtime['last_completed'] = WORK_UNIT
    runtime['mode'] = (
        'NEWS_OPERATIONAL_BASELINE_CLOSED_VERIFIED_BOUNDED_RUNTIME'
    )
    runtime['next_safe_step'] = next_safe_step
    runtime['current_problem'] = None
    runtime['updated_at_utc'] = generated
    runtime['canonical_runtime_pointer'] = runtime_pointer
    runtime['current_checkpoint'] = {
        'git_branch': 'main',
        'previous_head_before_closure_commit': current_head,
        'head_semantics': (
            'PREVIOUS_HEAD_BEFORE_ATOMIC_CLOSURE_COMMIT'
        ),
        'source': 'local_git',
    }
    runtime['news_operational_baseline'] = {
        'status': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'natural_timer_cycle_observed': True,
        'evidence_source': evidence.get('evidence_source'),
        'service_success': evidence.get('service_success'),
        'hot_refresh_marker': evidence.get(
            'hot_refresh_marker'
        ),
        'derived_counts_equal': derived_counts_equal,
        'hot_queue_count': hot.get('hot_queue_count'),
        'panel_bridge_decision': bridge.get('decision'),
        'closed_at_utc': generated,
        'artifact': CONTROL_REL,
    }
    atomic_write_json('PROJECT_RUNTIME.json', runtime)

    boot = load_json(ROOT / 'PROJECT_BOOT.json')
    boot['current_work_unit'] = active_work_unit
    boot['last_completed'] = WORK_UNIT
    boot['last_action'] = last_action
    boot['next_safe_step'] = next_safe_step
    boot['current_problem'] = None
    boot['canonical_runtime_pointer'] = runtime_pointer
    boot['current_checkpoint'] = runtime['current_checkpoint']
    boot.setdefault('project', {})
    boot['project']['mode'] = (
        'NEWS_OPERATIONAL_BASELINE_CLOSED_VERIFIED_BOUNDED_RUNTIME'
    )
    boot['project']['status'] = 'ACTIVE'
    boot['new_chat_instruction'] = (
        'Read PROJECT_RUNTIME.json first. NEWS operational baseline '
        'is closed and verified with a natural timer cycle. '
        'Proceed only to ' + NEXT_STEP + '. '
        'Do not reopen HBR or rebuild NEWS from zero.'
    )
    if isinstance(
        boot.get('new_window_startup_instruction'),
        dict,
    ):
        boot['new_window_startup_instruction']['instruction'] = (
            boot['new_chat_instruction']
        )
    atomic_write_json('PROJECT_BOOT.json', boot)

    tk = load_json(
        ROOT / 'data/control/latest_tk_machine_state.json'
    )
    tk['collect_mode'] = 'canonical_sync_snapshot_no_tk_machine'
    tk['created_at_utc'] = generated
    tk['generated_by'] = WORK_UNIT
    tk['tk_machine_executed'] = False
    tk['current_state'] = {
        'active_work_unit': active_work_unit,
        'next_safe_step': next_safe_step,
        'runtime_status': 'WORK_UNIT_CLOSED',
        'updated_at': generated,
        'last_action': last_action,
        'authority': 'PROJECT_RUNTIME.json',
    }
    tk['canonical_runtime_pointer'] = runtime_pointer
    tk['graphs_stale_non_authoritative'] = True
    atomic_write_json(
        'data/control/latest_tk_machine_state.json',
        tk,
    )

    roadmap = load_json(
        ROOT / 'data/tokenoskobi_v1_v8_master_era_roadmap.json'
    )
    roadmap['updated_at'] = generated
    roadmap['git_head'] = current_head
    roadmap['git_head_semantics'] = (
        'PREVIOUS_HEAD_BEFORE_ATOMIC_CLOSURE_COMMIT'
    )
    roadmap['work_unit'] = WORK_UNIT
    roadmap['current_state_authority'] = 'PROJECT_RUNTIME.json'
    roadmap['runtime_alignment'] = runtime_pointer
    roadmap['news_operational_baseline'] = {
        'status': 'CLOSED_VERIFIED_BOUNDED_RUNTIME',
        'hbr_status': 'CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT',
        'hot_ingress_integration': 'BOUND',
        'natural_timer_cycle': 'OBSERVED_VERIFIED',
        'evidence_source': evidence.get('evidence_source'),
        'next_safe_step': NEXT_STEP,
    }
    atomic_write_json(
        'data/tokenoskobi_v1_v8_master_era_roadmap.json',
        roadmap,
    )

    block = f'''<!-- POST_ERA54_HOT_FIRST_OBSERVATION_CURRENT_START -->
## CANONICAL CURRENT STATE — NEWS OPERATIONAL BASELINE CLOSED

STATE_SYNC_UTC={generated}
PREVIOUS_HEAD_BEFORE_CLOSURE_COMMIT={current_head}
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
LAST_COMPLETED={WORK_UNIT}
LAST_DECISION={DECISION}
CURRENT_ERA=ERA54_CLOSED
NEWS_OPERATIONAL_BASELINE=CLOSED_VERIFIED_BOUNDED_RUNTIME
NATURAL_TIMER_FULL_CYCLE=OBSERVED_VERIFIED
EVIDENCE_SOURCE={evidence.get('evidence_source')}
SERVICE_SUCCESS=true
DERIVED_COUNTS_EQUAL=true
HOT_QUEUE_COUNT={hot.get('hot_queue_count')}
HOT_QUEUE_BOUND=50
PANEL_BRIDGE_DECISION={bridge.get('decision')}
HBR_STATUS=CLOSED_INCONCLUSIVE_ZERO_ELIGIBLE_INPUT
NEXT_SAFE_STEP={NEXT_STEP}
NEW_ERA_OPENED=false
<!-- POST_ERA54_HOT_FIRST_OBSERVATION_CURRENT_END -->'''

    update_markdown('03_ROADMAP.md', block)
    update_markdown(
        '04_ALMANAC.md',
        block,
        f'''## {WORK_UNIT} — {generated}

- Decision: `{DECISION}`
- Natural timer cycle: `OBSERVED_VERIFIED`
- Evidence source: `{evidence.get('evidence_source')}`
- Service success: `true`
- Derived counts equal: `true`
- Hot queue: `{hot.get('hot_queue_count')}/50`
- Panel bridge: `{bridge.get('decision')}`
- NEWS operational baseline: `CLOSED_VERIFIED_BOUNDED_RUNTIME`
- Next safe step: `{NEXT_STEP}`
- Previous HEAD: `{current_head}`''',
    )
    update_markdown('06_PROJECT_MASTER_STATE.md', block)
    update_markdown('07_PROJECT_HANDOFF.md', block)

    atomic_write_text(
        ROOT / 'reports/LATEST_TK_AI_HANDOFF.md',
        f'''# LATEST TK AI HANDOFF

{block}

`PROJECT_RUNTIME.json` is current-state authority.

NEWS was not rebuilt. The existing cold producer, derived chain, bounded hot ingress gateway, and active panel data bridge completed a natural timer-driven full cycle successfully.

Proceed only to `{NEXT_STEP}`.
''',
    )

    atomic_write_text(
        ROOT / DOC_REL,
        f'''# POST_ERA54_HOT_INGRESS_BOUND_RUNTIME_FIRST_OBSERVATION_NOAPI_V1

- Decision: `{DECISION}`
- Generated: `{generated}`
- Previous HEAD: `{current_head}`
- Natural cycle: `OBSERVED_VERIFIED`
- Evidence source: `{evidence.get('evidence_source')}`
- Service success: `{str(evidence.get('service_success')).lower()}`
- Hot refresh marker: `{str(evidence.get('hot_refresh_marker')).lower()}`
- Wrapper/derived marker: `{str(evidence.get('wrapper_or_derived_marker')).lower()}`
- DB integrity: `{db_after.get('integrity')}`
- Derived counts equal: `{str(derived_counts_equal).lower()}`
- Market indicators: `{summary.get('market_indicator_count')}`
- Adversarial events: `{summary.get('adversarial_count')}`
- Hot queue: `{hot.get('hot_queue_count')}/50`
- Panel bridge: `{bridge.get('decision')}`
- NEWS operational baseline: `CLOSED_VERIFIED_BOUNDED_RUNTIME`
- Next safe step: `{NEXT_STEP}`

No observer DB write, schema mutation, service/timer configuration change, trade authority, paper trade, live trade, or new ERA occurred.
''',
    )

    print(json.dumps({
        'decision': DECISION,
        'decision_id': decision_id,
        'evidence_source': evidence.get('evidence_source'),
        'service_success': evidence.get('service_success'),
        'hot_refresh_marker': evidence.get('hot_refresh_marker'),
        'wrapper_or_derived_marker': evidence.get(
            'wrapper_or_derived_marker'
        ),
        'db_counts': counts_after,
        'market_indicator_count': summary.get(
            'market_indicator_count'
        ),
        'adversarial_count': summary.get('adversarial_count'),
        'hot_queue_count': hot.get('hot_queue_count'),
        'panel_bridge_decision': bridge.get('decision'),
        'next_safe_step': NEXT_STEP,
    }, ensure_ascii=False, indent=2, sort_keys=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
