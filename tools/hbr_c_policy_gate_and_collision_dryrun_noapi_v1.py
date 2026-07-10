#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import os
import re
import sqlite3
import subprocess

ROOT = Path('/root/tokenoskobi_clean_v1')
DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
EXPECTED_HEAD = 'd9b6c8bc95217b7161694a73903fe4e8e676be93'
WORK_UNIT = 'HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI'
DECISION = 'OK_HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI'

SYNC_ARTIFACT = ROOT / 'data/control/hbr_canonical_state_sync_noapi_v1.json'
HBR_B_ARTIFACT = ROOT / 'data/control/hbr_b_input_only_fetch_and_seal_with_network_tempfiles_v1.json'
HBR_A_ARTIFACT = ROOT / 'data/control/hbr_a_input_only_source_plan_noapi_v1.json'
POLICY_PATH = ROOT / 'runtime/policies/news_runtime_policy_lock_v1.json'
MANIFEST_PATH = ROOT / 'runtime/hbr_blind_replay/hbr_b_input_manifest_v1.json'
ITEMS_PATH = ROOT / 'runtime/hbr_blind_replay/hbr_b_input_only_items_v1.jsonl'
SKIPPED_PATH = ROOT / 'runtime/hbr_blind_replay/hbr_b_input_only_skipped_v1.jsonl'

CONTROL_REL = 'data/control/hbr_c_policy_gate_and_collision_dryrun_noapi_v1.json'
DOC_REL = 'docs/canonical/HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI_V1.md'
TOOL_REL = 'tools/hbr_c_policy_gate_and_collision_dryrun_noapi_v1.py'

TABLES = [
    'news_raw_feed_events',
    'news_token_match_events',
    'news_signal_events',
    'news_score_events_v1',
]
DERIVED_TABLES = TABLES[1:]
EXPECTED_MANIFEST_SHA = '98ac79dc325d5f433ca7921978537dce5774484669976a78e9331dcd352e431c'
EXPECTED_ITEMS_SHA = '132e5a2a80debe3f0eb625570639b5a84b8bc4e129934596195a1e3d110bdc5c'
EXPECTED_SKIPPED_SHA = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_output(*args: str) -> str:
    cp = subprocess.run(
        ['git', *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return cp.stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError(f'JSON_OBJECT_REQUIRED:{path}')
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError(f'JSONL_OBJECT_REQUIRED:{path}:{line_number}')
        rows.append(value)
    return rows


def atomic_write_text(relative_path: str, text: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp_hbr_c')
    temp.write_text(text, encoding='utf-8')
    os.replace(temp, path)


def atomic_write_json(relative_path: str, value: dict[str, Any]) -> None:
    atomic_write_text(
        relative_path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + '\n',
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_canonical_json(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')
    return sha256_bytes(payload)


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def placeholders(count: int) -> str:
    return ','.join('?' for _ in range(count))


def table_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [
        str(row[1])
        for row in connection.execute(
            'PRAGMA table_info(' + quote_identifier(table) + ')'
        ).fetchall()
    ]


def table_count(connection: sqlite3.Connection, table: str) -> int:
    return int(
        connection.execute(
            'SELECT COUNT(*) FROM ' + quote_identifier(table)
        ).fetchone()[0]
    )


def query_rows(
    connection: sqlite3.Connection,
    sql: str,
    parameters: list[Any],
) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(sql, parameters).fetchall()]


def replace_current_block(original: str, new_block: str) -> str:
    marker_pairs = [
        (
            '<!-- HBR_CANONICAL_STATE_SYNC_CURRENT_START -->',
            '<!-- HBR_CANONICAL_STATE_SYNC_CURRENT_END -->',
        ),
        (
            '<!-- HBR_C_POLICY_GATE_CURRENT_START -->',
            '<!-- HBR_C_POLICY_GATE_CURRENT_END -->',
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
    failures: list[str] = []
    warnings: list[str] = []

    current_head = git_output('rev-parse', 'HEAD')
    current_branch = git_output('branch', '--show-current')
    if current_head != EXPECTED_HEAD:
        raise RuntimeError(f'HEAD_MISMATCH:expected={EXPECTED_HEAD}:actual={current_head}')
    if current_branch != 'main':
        raise RuntimeError(f'BRANCH_MISMATCH:{current_branch}')

    required_paths = [
        DB,
        SYNC_ARTIFACT,
        HBR_B_ARTIFACT,
        HBR_A_ARTIFACT,
        POLICY_PATH,
        MANIFEST_PATH,
        ITEMS_PATH,
        SKIPPED_PATH,
    ]
    missing_paths = [str(path.relative_to(ROOT)) for path in required_paths if not path.exists()]
    if missing_paths:
        raise RuntimeError('MISSING_REQUIRED_PATHS:' + ','.join(missing_paths))

    sync = load_json(SYNC_ARTIFACT)
    hbr_b = load_json(HBR_B_ARTIFACT)
    hbr_a = load_json(HBR_A_ARTIFACT)
    policy = load_json(POLICY_PATH)
    manifest = load_json(MANIFEST_PATH)
    items_bytes = ITEMS_PATH.read_bytes()
    skipped_bytes = SKIPPED_PATH.read_bytes()
    items = load_jsonl(ITEMS_PATH)
    skipped = load_jsonl(SKIPPED_PATH)

    if sync.get('decision') != 'OK_HBR_CANONICAL_STATE_SYNC_NOAPI':
        failures.append('canonical_sync_not_ok')
    if sync.get('next') != WORK_UNIT:
        failures.append('canonical_sync_next_mismatch')
    if hbr_b.get('decision') != 'OK_HBR_B_INPUT_ONLY_FETCH_AND_SEAL_WITH_NETWORK_TEMPFILES':
        failures.append('hbr_b_not_ok')
    if hbr_b.get('next') != WORK_UNIT:
        failures.append('hbr_b_next_mismatch')
    if hbr_a.get('decision') != 'OK_HBR_A_INPUT_ONLY_SOURCE_PLAN_NOAPI':
        failures.append('hbr_a_not_ok')

    manifest_core = dict(manifest)
    claimed_manifest_sha = manifest_core.pop('input_manifest_sha256', None)
    actual_manifest_sha = sha256_canonical_json(manifest_core)
    actual_items_sha = sha256_bytes(items_bytes)
    actual_skipped_sha = sha256_bytes(skipped_bytes)

    if claimed_manifest_sha != actual_manifest_sha:
        failures.append('manifest_internal_sha_mismatch')
    if claimed_manifest_sha != EXPECTED_MANIFEST_SHA:
        failures.append('manifest_expected_sha_mismatch')
    if actual_items_sha != EXPECTED_ITEMS_SHA:
        failures.append('items_sha_mismatch')
    if actual_skipped_sha != EXPECTED_SKIPPED_SHA:
        failures.append('skipped_sha_mismatch')
    if manifest.get('items_jsonl_sha256') != actual_items_sha:
        failures.append('manifest_items_sha_pointer_mismatch')
    if manifest.get('skipped_jsonl_sha256') != actual_skipped_sha:
        failures.append('manifest_skipped_sha_pointer_mismatch')
    if manifest.get('input_count') != len(items):
        failures.append('manifest_input_count_mismatch')
    if manifest.get('skipped_count') != len(skipped):
        failures.append('manifest_skipped_count_mismatch')
    if len(items) != 55:
        failures.append(f'input_count_not_55:{len(items)}')
    if skipped:
        failures.append(f'skipped_count_not_zero:{len(skipped)}')

    source_plan = hbr_a.get('result', {}).get('source_plan', {})
    forbidden_fields = set(source_plan.get('forbidden_fields_before_prediction_seal', []))
    if not forbidden_fields:
        forbidden_fields = {'outcome', 'result', 'prediction', 'price_after', 'return_after'}

    forbidden_hits: list[dict[str, str]] = []
    for index, item in enumerate(items):
        for key in item:
            key_lower = key.lower()
            if key in forbidden_fields or any(fragment in key_lower for fragment in ('outcome', 'result', 'prediction')):
                forbidden_hits.append({'row': str(index), 'field': key})

    if forbidden_hits:
        failures.append('forbidden_outcome_or_prediction_fields_present')
    if not all(item.get('input_only') is True for item in items):
        failures.append('input_only_flag_invalid')
    if not all(str(item.get('candidate_news_uid', '')).startswith('hbr_input_') for item in items):
        failures.append('temp_uid_namespace_invalid')

    candidate_uids = [str(item.get('candidate_news_uid', '')) for item in items]
    url_hashes = [str(item.get('url_hash', '')) for item in items]
    raw_hashes = [str(item.get('raw_hash', '')) for item in items]

    internal_duplicate_uids = duplicate_values(candidate_uids)
    internal_duplicate_url_hashes = duplicate_values(url_hashes)
    internal_duplicate_raw_hashes = duplicate_values(raw_hashes)
    if internal_duplicate_uids:
        failures.append('internal_duplicate_candidate_uid')
    if internal_duplicate_url_hashes:
        failures.append('internal_duplicate_url_hash')
    if internal_duplicate_raw_hashes:
        failures.append('internal_duplicate_raw_hash')

    eligible_count = sum(item.get('within_locked_window') is True for item in items)
    if manifest.get('in_locked_window_count') != eligible_count:
        failures.append('locked_window_count_mismatch')

    policy_authority = policy.get('authority', {})
    required_false_authority = [
        'api_call',
        'network_call',
        'db_write',
        'db_schema_change',
        'index_creation',
        'service_change',
        'timer_change',
        'nginx_change',
        'paper_trade',
        'live_trade',
        'trade_authority',
    ]
    for key in required_false_authority:
        if policy_authority.get(key) is not False:
            failures.append('policy_authority_not_false:' + key)

    allowed_prefixes = policy.get('uid_policy', {}).get('allowed_prefixes', [])
    temp_namespace_isolated = 'hbr_input_' not in allowed_prefixes
    if not temp_namespace_isolated:
        failures.append('temp_namespace_unexpectedly_production_allowed')
    if policy.get('uid_policy', {}).get('collision_allowed') is not False:
        failures.append('policy_collision_allowed_not_false')
    failure_routing = policy.get('failure_routing_policy', {})
    if failure_routing.get('uid_namespace_collision') != 'HOLD':
        failures.append('uid_namespace_collision_route_not_hold')
    if failure_routing.get('duplicate_uid') != 'HOLD':
        failures.append('duplicate_uid_route_not_hold')

    db_before: dict[str, Any] = {}
    db_after: dict[str, Any] = {}
    schema: dict[str, list[str]] = {}
    uid_collision_rows: list[dict[str, Any]] = []
    url_hash_collision_rows: list[dict[str, Any]] = []
    raw_hash_collision_rows: list[dict[str, Any]] = []
    derived_collision_rows: dict[str, list[dict[str, Any]]] = {}
    query_only = False
    total_changes_before = 0
    total_changes_after = 0

    if not failures:
        connection = sqlite3.connect('file:' + str(DB) + '?mode=ro', uri=True)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute('PRAGMA query_only=ON')
            connection.execute('PRAGMA busy_timeout=5000')
            query_only = bool(connection.execute('PRAGMA query_only').fetchone()[0])
            total_changes_before = connection.total_changes
            connection.execute('BEGIN')

            existing_tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            missing_tables = [table for table in TABLES if table not in existing_tables]
            if missing_tables:
                failures.append('missing_tables:' + ','.join(missing_tables))
            else:
                schema = {table: table_columns(connection, table) for table in TABLES}
                required_raw_columns = {'news_uid', 'url_hash', 'raw_hash'}
                if not required_raw_columns.issubset(set(schema['news_raw_feed_events'])):
                    failures.append('raw_collision_columns_missing')
                for table in DERIVED_TABLES:
                    if 'news_uid' not in schema[table]:
                        failures.append('derived_news_uid_missing:' + table)

            if not failures:
                db_before = {
                    'counts': {table: table_count(connection, table) for table in TABLES},
                    'integrity': str(connection.execute('PRAGMA integrity_check').fetchone()[0]),
                }
                if db_before['integrity'] != 'ok':
                    failures.append('sqlite_integrity_not_ok')

            if not failures:
                uid_marks = placeholders(len(candidate_uids))
                url_marks = placeholders(len(url_hashes))
                raw_marks = placeholders(len(raw_hashes))
                uid_collision_rows = query_rows(
                    connection,
                    'SELECT news_uid,url_hash,raw_hash FROM news_raw_feed_events '
                    f'WHERE news_uid IN ({uid_marks}) ORDER BY news_uid',
                    candidate_uids,
                )
                url_hash_collision_rows = query_rows(
                    connection,
                    'SELECT news_uid,url_hash,raw_hash FROM news_raw_feed_events '
                    f'WHERE url_hash IN ({url_marks}) ORDER BY url_hash,news_uid',
                    url_hashes,
                )
                raw_hash_collision_rows = query_rows(
                    connection,
                    'SELECT news_uid,url_hash,raw_hash FROM news_raw_feed_events '
                    f'WHERE raw_hash IN ({raw_marks}) ORDER BY raw_hash,news_uid',
                    raw_hashes,
                )
                for table in DERIVED_TABLES:
                    derived_collision_rows[table] = query_rows(
                        connection,
                        'SELECT news_uid,COUNT(*) AS row_count FROM '
                        + quote_identifier(table)
                        + f' WHERE news_uid IN ({uid_marks}) GROUP BY news_uid ORDER BY news_uid',
                        candidate_uids,
                    )

                db_after = {
                    'counts': {table: table_count(connection, table) for table in TABLES},
                    'integrity': str(connection.execute('PRAGMA integrity_check').fetchone()[0]),
                }
                total_changes_after = connection.total_changes
                if db_before != db_after:
                    failures.append('readonly_snapshot_changed_inside_transaction')
                if total_changes_before != 0 or total_changes_after != 0:
                    failures.append('sqlite_total_changes_nonzero')
                if not query_only:
                    failures.append('sqlite_query_only_not_enabled')
            connection.rollback()
        finally:
            connection.close()

    if failures:
        raise RuntimeError('HBR_C_PREFLIGHT_OR_READONLY_FAILURE:' + '|'.join(failures))

    uid_collision_values = sorted({str(row['news_uid']) for row in uid_collision_rows})
    url_collision_values = sorted({str(row['url_hash']) for row in url_hash_collision_rows})
    raw_collision_values = sorted({str(row['raw_hash']) for row in raw_hash_collision_rows})
    derived_collision_uids = sorted(
        {
            str(row['news_uid'])
            for rows in derived_collision_rows.values()
            for row in rows
        }
    )

    namespace_collision_found = bool(uid_collision_values or derived_collision_uids)
    content_duplicate_found = bool(url_collision_values or raw_collision_values)
    if namespace_collision_found and content_duplicate_found:
        collision_result = 'UID_AND_CONTENT_COLLISION_FOUND'
    elif namespace_collision_found:
        collision_result = 'UID_NAMESPACE_COLLISION_FOUND'
    elif content_duplicate_found:
        collision_result = 'CONTENT_DUPLICATE_FOUND'
    else:
        collision_result = 'NO_PRODUCTION_COLLISION'

    uid_collision_set = set(uid_collision_values)
    url_collision_set = set(url_collision_values)
    raw_collision_set = set(raw_collision_values)
    derived_collision_set = set(derived_collision_uids)
    simulated_routes: list[dict[str, Any]] = []
    for item in items:
        uid = str(item['candidate_news_uid'])
        url_hash = str(item['url_hash'])
        raw_hash = str(item['raw_hash'])
        collision_types: list[str] = []
        if uid in uid_collision_set:
            collision_types.append('NEWS_UID')
        if url_hash in url_collision_set:
            collision_types.append('URL_HASH')
        if raw_hash in raw_collision_set:
            collision_types.append('RAW_HASH')
        if uid in derived_collision_set:
            collision_types.append('DERIVED_NEWS_UID')
        if 'NEWS_UID' in collision_types or 'DERIVED_NEWS_UID' in collision_types:
            route = 'HOLD_UID_COLLISION'
        elif collision_types:
            route = 'SKIP_DUPLICATE_AND_REPORT'
        else:
            route = 'HOLD_TEMP_NAMESPACE_NOT_PRODUCTION_ADMISSIBLE'
        simulated_routes.append(
            {
                'candidate_news_uid': uid,
                'url_hash': url_hash,
                'raw_hash': raw_hash,
                'within_locked_window': item.get('within_locked_window') is True,
                'collision_types': collision_types,
                'simulated_route': route,
                'production_insert': False,
            }
        )

    if namespace_collision_found:
        operational_route = 'ERA60_NAMESPACE_AND_COLLISION_EVIDENCE_REVIEW_NOAPI'
        policy_gate = 'HOLD_UID_NAMESPACE_COLLISION_EVIDENCE'
    elif eligible_count == 0:
        operational_route = 'HBR_SOURCE_WINDOW_REPAIR_OR_CLOSE_DECISION_NOAPI'
        policy_gate = (
            'HOLD_ZERO_ELIGIBLE_INPUT_AFTER_CONTENT_DEDUPE'
            if content_duplicate_found
            else 'HOLD_ZERO_ELIGIBLE_INPUT'
        )
    else:
        operational_route = 'HBR_D_PREDICTION_RUN_WITHOUT_RESULTS_NOAPI'
        policy_gate = (
            'READY_FOR_HBR_D_AFTER_CONTENT_DEDUPE'
            if content_duplicate_found
            else 'READY_FOR_HBR_D_TEMPFILE_ONLY'
        )

    tests = [
        {'test_id': 'T01_CANONICAL_SYNC_OK', 'ok': True},
        {'test_id': 'T02_HBR_B_SEAL_SHA_OK', 'ok': True},
        {'test_id': 'T03_INPUT_COUNT_55', 'ok': len(items) == 55, 'value': len(items)},
        {'test_id': 'T04_SKIPPED_COUNT_ZERO', 'ok': len(skipped) == 0, 'value': len(skipped)},
        {'test_id': 'T05_INPUT_ONLY_AND_NO_RESULT_LEAK', 'ok': not forbidden_hits},
        {'test_id': 'T06_INTERNAL_DUPLICATES_ZERO', 'ok': not internal_duplicate_uids and not internal_duplicate_url_hashes and not internal_duplicate_raw_hashes},
        {'test_id': 'T07_POLICY_AUTHORITY_LOCKED', 'ok': True},
        {'test_id': 'T08_TEMP_NAMESPACE_ISOLATED', 'ok': temp_namespace_isolated},
        {'test_id': 'T09_SQLITE_MODE_RO_QUERY_ONLY', 'ok': query_only},
        {'test_id': 'T10_REQUIRED_TABLES_AND_COLUMNS', 'ok': True},
        {'test_id': 'T11_COLLISION_DRYRUN_COMPLETED', 'ok': True, 'collision_result': collision_result},
        {'test_id': 'T12_DERIVED_COLLISION_CHECK_COMPLETED', 'ok': True},
        {'test_id': 'T13_DB_BEFORE_AFTER_EQUAL', 'ok': db_before == db_after},
        {'test_id': 'T14_SQLITE_TOTAL_CHANGES_ZERO', 'ok': total_changes_before == total_changes_after == 0},
        {'test_id': 'T15_NO_PRODUCTION_INSERT', 'ok': True},
    ]

    decision_id = 'HBR__C_POLICY_GATE_COLLISION_DRYRUN__' + current_head[:12] + '__' + generated_at
    authority = {
        'api_call': False,
        'network_call': False,
        'db_read': True,
        'db_read_mode': 'SQLITE_MODE_RO_QUERY_ONLY',
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
    }

    artifact: dict[str, Any] = {
        'stage': WORK_UNIT,
        'generated_at_utc': generated_at,
        'decision': DECISION,
        'decision_id': decision_id,
        'previous_head_before_closure_commit': current_head,
        'authority': authority,
        'failures': [],
        'warnings': warnings,
        'next': operational_route,
        'result': {
            'source_of_truth': 'PROJECT_RUNTIME.json',
            'hbr_b_manifest_sha256': claimed_manifest_sha,
            'hbr_b_items_sha256': actual_items_sha,
            'hbr_b_skipped_sha256': actual_skipped_sha,
            'input_count': len(items),
            'skipped_count': len(skipped),
            'locked_window_eligible_count': eligible_count,
            'internal_duplicates': {
                'candidate_news_uid': internal_duplicate_uids,
                'url_hash': internal_duplicate_url_hashes,
                'raw_hash': internal_duplicate_raw_hashes,
            },
            'policy': {
                'policy_id': policy.get('policy_id'),
                'allowed_production_prefixes': allowed_prefixes,
                'temp_namespace': 'hbr_input_',
                'temp_namespace_isolated': temp_namespace_isolated,
                'production_admission': 'HOLD_UID_NAMESPACE_POLICY',
                'policy_gate': policy_gate,
            },
            'collision_result': collision_result,
            'collision_summary': {
                'news_uid_collision_count': len(uid_collision_values),
                'url_hash_collision_count': len(url_collision_values),
                'raw_hash_collision_count': len(raw_collision_values),
                'derived_news_uid_collision_count': len(derived_collision_uids),
                'news_uid_collision_values': uid_collision_values,
                'url_hash_collision_values': url_collision_values,
                'raw_hash_collision_values': raw_collision_values,
                'derived_news_uid_collision_values': derived_collision_uids,
            },
            'collision_evidence': {
                'news_raw_feed_events_by_news_uid': uid_collision_rows,
                'news_raw_feed_events_by_url_hash': url_hash_collision_rows,
                'news_raw_feed_events_by_raw_hash': raw_hash_collision_rows,
                'derived_tables_by_candidate_news_uid': derived_collision_rows,
            },
            'simulated_item_routes': simulated_routes,
            'db_schema': schema,
            'db_before': db_before,
            'db_after': db_after,
            'db_delta': {
                table: db_after['counts'][table] - db_before['counts'][table]
                for table in TABLES
            },
            'sqlite_query_only': query_only,
            'sqlite_total_changes_before': total_changes_before,
            'sqlite_total_changes_after': total_changes_after,
            'production_insert': False,
            'window_gate': 'HOLD' if eligible_count == 0 else 'OPEN_FOR_TEMPFILE_REPLAY_ONLY',
            'historical_replay_eligibility': (
                'HOLD_ZERO_ELIGIBLE_INPUT'
                if eligible_count == 0
                else 'READY_FOR_HBR_D_TEMPFILE_ONLY'
            ),
            'operational_route': operational_route,
        },
        'tests': tests,
        'test_count': len(tests),
        'ok_count': sum(test.get('ok') is True for test in tests),
        'fail_count': sum(test.get('ok') is not True for test in tests),
    }
    if artifact['fail_count'] != 0:
        raise RuntimeError('HBR_C_TEST_FAILURE')
    atomic_write_json(CONTROL_REL, artifact)

    if namespace_collision_found:
        current_problem: dict[str, Any] | None = {
            'type': 'HBR_UID_NAMESPACE_COLLISION_EVIDENCE',
            'description': 'HBR-C measured production UID namespace collision evidence; no write occurred.',
            'immediate_priority': operational_route,
        }
    elif eligible_count == 0:
        current_problem = {
            'type': 'HBR_ZERO_ELIGIBLE_INPUT',
            'description': 'HBR-C completed collision measurement, but sealed input has zero locked-window-eligible rows.',
            'immediate_priority': operational_route,
        }
    else:
        current_problem = None

    runtime = load_json(ROOT / 'PROJECT_RUNTIME.json')
    last_action = {
        'timestamp': generated_at,
        'task': WORK_UNIT,
        'result': DECISION,
        'artifact': CONTROL_REL,
    }
    active_work_unit = {
        'id': WORK_UNIT,
        'type': 'HISTORICAL_BLIND_REPLAY_POLICY_AND_COLLISION_DRYRUN',
        'artifact': CONTROL_REL,
        'module': TOOL_REL,
        'status': 'CLOSED',
        'next_step': operational_route,
    }
    next_safe_step = {'name': operational_route, 'status': 'READY'}
    runtime_pointer = {
        'authority': 'PROJECT_RUNTIME.json',
        'previous_head_before_closure_commit': current_head,
        'last_completed': WORK_UNIT,
        'decision': DECISION,
        'collision_result': collision_result,
        'policy_gate': policy_gate,
        'locked_window_eligible_count': eligible_count,
        'historical_replay_eligibility': artifact['result']['historical_replay_eligibility'],
        'next_safe_step': operational_route,
        'updated_at_utc': generated_at,
    }

    runtime.setdefault('current_state', {})
    runtime['current_state'].update(
        {
            'mode': 'HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_CLOSED',
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
    runtime['mode'] = 'HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_CLOSED'
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
        'Read PROJECT_RUNTIME.json first. HBR-C is closed. '
        f'collision_result={collision_result}. '
        f'Proceed only to {operational_route}. '
        'Do not run tk machine or mutate DB/schema/UID/services/timers/nginx.'
    )
    if isinstance(boot.get('new_window_startup_instruction'), dict):
        boot['new_window_startup_instruction']['instruction'] = boot['new_chat_instruction']
    boot.setdefault('project', {})
    boot['project']['mode'] = 'HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_CLOSED'
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
        'HBR_CANONICAL_STATE_SYNC': 'CLOSED',
        'HBR_C': 'CLOSED',
        'HBR_C_COLLISION_RESULT': collision_result,
        'HBR_D': (
            'READY'
            if operational_route == 'HBR_D_PREDICTION_RUN_WITHOUT_RESULTS_NOAPI'
            else 'BLOCKED_BY_HBR_C_ROUTE'
        ),
        'next_safe_step': operational_route,
    }
    atomic_write_json('data/tokenoskobi_v1_v8_master_era_roadmap.json', roadmap)

    block = f'''<!-- HBR_C_POLICY_GATE_CURRENT_START -->
## CANONICAL CURRENT STATE — HBR-C CLOSED

STATE_SYNC_UTC={generated_at}
PREVIOUS_HEAD_BEFORE_CLOSURE_COMMIT={current_head}
CURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json
LAST_COMPLETED={WORK_UNIT}
LAST_DECISION={DECISION}
HBR_B_SEAL=INTACT
HBR_C_STATUS=CLOSED
COLLISION_RESULT={collision_result}
POLICY_GATE={policy_gate}
INPUT_COUNT={len(items)}
LOCKED_WINDOW_ELIGIBLE_COUNT={eligible_count}
HISTORICAL_REPLAY_ELIGIBILITY={artifact['result']['historical_replay_eligibility']}
DB_MODE=SQLITE_MODE_RO_QUERY_ONLY
DB_TOTAL_CHANGES=0
PRODUCTION_INSERT=false
NEXT_SAFE_STEP={operational_route}
TK_MACHINE_EXECUTED=false
SCHEMA_OR_UID_MUTATION=false
<!-- HBR_C_POLICY_GATE_CURRENT_END -->'''

    update_markdown('03_ROADMAP.md', block)
    update_markdown(
        '04_ALMANAC.md',
        block,
        f'''## {WORK_UNIT} — {generated_at}

- Decision: `{DECISION}`
- Collision result: `{collision_result}`
- Policy gate: `{policy_gate}`
- Input count: `{len(items)}`
- Locked-window eligible count: `{eligible_count}`
- DB mode: `SQLITE_MODE_RO_QUERY_ONLY`
- DB total changes: `0`
- Production insert: `false`
- Next safe step: `{operational_route}`
- Previous HEAD: `{current_head}`''',
    )
    update_markdown('06_PROJECT_MASTER_STATE.md', block)
    update_markdown('07_PROJECT_HANDOFF.md', block)

    atomic_write_text(
        'reports/LATEST_TK_AI_HANDOFF.md',
        f'''# LATEST TK AI HANDOFF

{block}

`PROJECT_RUNTIME.json` is current-state authority.

Proceed only to `{operational_route}`.

HBR-C performed a read-only production collision measurement. It did not write to production DB, change schema, run prediction, fetch outcomes, change services/timers/nginx, run TK machine, or change trade authority.
''',
    )

    atomic_write_text(
        DOC_REL,
        f'''# HBR_C_POLICY_GATE_AND_COLLISION_DRYRUN_NOAPI_V1

- Decision: `{DECISION}`
- Generated: `{generated_at}`
- Previous HEAD: `{current_head}`
- HBR-B manifest SHA: `{claimed_manifest_sha}`
- HBR-B items SHA: `{actual_items_sha}`
- Input count: `{len(items)}`
- Locked-window eligible count: `{eligible_count}`
- Collision result: `{collision_result}`
- Policy gate: `{policy_gate}`
- SQLite mode: `mode=ro + query_only`
- SQLite total changes: `0`
- Production insert: `false`
- Next safe step: `{operational_route}`

## Collision summary

- news_uid: `{len(uid_collision_values)}`
- url_hash: `{len(url_collision_values)}`
- raw_hash: `{len(raw_collision_values)}`
- derived news_uid: `{len(derived_collision_uids)}`

## Boundaries

No production DB write, schema/index mutation, UID algorithm change, prediction, outcome fetch, service/timer/nginx change, TK machine execution, shadow cleanup, paper trade, live trade, or trade authority change occurred.
''',
    )

    print(
        json.dumps(
            {
                'decision': DECISION,
                'decision_id': decision_id,
                'collision_result': collision_result,
                'policy_gate': policy_gate,
                'locked_window_eligible_count': eligible_count,
                'next_safe_step': operational_route,
                'db_before': db_before,
                'db_after': db_after,
                'sqlite_total_changes': total_changes_after,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
        )
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
