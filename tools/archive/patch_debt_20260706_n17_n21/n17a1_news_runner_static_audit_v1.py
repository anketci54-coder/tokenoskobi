#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os, re, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
RUNNER = ROOT / 'tools/news_radar_refresh_runner_v1.py'
ORIGINAL = ROOT / 'tools/news_radar_refresh_runner_v1.ORIGINAL_NEWS27A11_20260510_211813.py'
MATCHER = ROOT / 'tools/news_token_matcher_v1.py'
OUT = ROOT / 'data/control/n17a1_news_runner_static_audit_v1.json'
ROWS = ROOT / 'data/control/n17a1_news_runner_static_audit_v1_rows.jsonl'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read_text(path):
    return path.read_text(encoding='utf-8', errors='replace')


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def atomic_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.n17a1_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        read_json(Path(tmp))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def ast_info(path):
    info = {'parse_ok': False, 'functions': [], 'calls_postprocess': False, 'return_before_postprocess': False, 'errors': []}
    if not path.exists():
        info['errors'].append('missing')
        return info
    src = read_text(path)
    try:
        tree = ast.parse(src)
        info['parse_ok'] = True
    except Exception as e:
        info['errors'].append(type(e).__name__ + ':' + str(e)[:200])
        return info
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            info['functions'].append(node.name)
        if isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, 'id', None) or getattr(fn, 'attr', None)
            if name == '_postprocess':
                info['calls_postprocess'] = True
    lines = src.splitlines()
    post_line = None
    returns = []
    for i, line in enumerate(lines, 1):
        if '_postprocess(' in line:
            post_line = i if post_line is None else post_line
        if re.match(r'\s*return\b', line):
            returns.append(i)
    if post_line and any(r < post_line for r in returns[-3:]):
        info['return_before_postprocess'] = True
    return info


def file_record(path):
    exists = path.exists() and path.is_file()
    return {
        'path': str(path.relative_to(ROOT)) if path.exists() else str(path),
        'exists': exists,
        'size': path.stat().st_size if exists else None,
        'sha256': sha256(path) if exists else None,
        'ast': ast_info(path) if exists and path.suffix == '.py' else None
    }


def grep_flags(path):
    if not path.exists():
        return {}
    src = read_text(path)
    return {
        'contains_ORIGINAL_RUNNER': 'ORIGINAL_RUNNER' in src,
        'contains_PREVIEW_DATA': 'PREVIEW_DATA' in src,
        'contains_PREVIEW_HTML': 'PREVIEW_HTML' in src,
        'contains_news_token_matcher': 'news_token_matcher' in src,
        'contains_news_raw_feed_events': 'news_raw_feed_events' in src,
        'contains_news_token_match_events': 'news_token_match_events' in src,
        'contains_news_signal_events': 'news_signal_events' in src,
        'contains_news_score_events_v1': 'news_score_events_v1' in src,
        'contains_subprocess_run': 'subprocess.run' in src,
        'contains_sys_exit': 'sys.exit' in src,
        'postprocess_line_numbers': [i for i, line in enumerate(src.splitlines(), 1) if '_postprocess' in line],
        'return_line_numbers_tail': [i for i, line in enumerate(src.splitlines(), 1) if re.match(r'\s*return\b', line)][-10:]
    }


def main():
    records = [file_record(p) for p in [RUNNER, ORIGINAL, MATCHER]]
    runner_flags = grep_flags(RUNNER)
    original_flags = grep_flags(ORIGINAL)
    matcher_flags = grep_flags(MATCHER)
    checks = [
        {'name': 'runner_exists_parse_ok', 'ok': records[0]['exists'] and records[0]['ast']['parse_ok']},
        {'name': 'original_runner_exists_parse_ok', 'ok': records[1]['exists'] and records[1]['ast']['parse_ok']},
        {'name': 'matcher_exists_parse_ok', 'ok': records[2]['exists'] and records[2]['ast']['parse_ok']},
        {'name': 'runner_references_original', 'ok': runner_flags.get('contains_ORIGINAL_RUNNER') is True},
        {'name': 'runner_calls_postprocess', 'ok': records[0]['ast']['calls_postprocess'] is True},
        {'name': 'runner_no_unreachable_postprocess_hint', 'ok': records[0]['ast']['return_before_postprocess'] is False},
        {'name': 'matcher_mentions_token_match_table', 'ok': matcher_flags.get('contains_news_token_match_events') is True},
        {'name': 'runner_mentions_downstream_tables', 'ok': any(runner_flags.get(k) for k in ['contains_news_token_match_events','contains_news_signal_events','contains_news_score_events_v1'])}
    ]
    failed = [c['name'] for c in checks if not c['ok']]
    if 'runner_no_unreachable_postprocess_hint' in failed:
        decision = 'RUNNER_STATIC_AUDIT_POSTPROCESS_REACHABILITY_SUSPECT'
        next_action = 'PATCH_RUNNER_RETURN_ORDER_OR_POSTPROCESS_CALL_PATH'
    elif 'matcher_mentions_token_match_table' in failed:
        decision = 'MATCHER_STATIC_BINDING_MISSING_OR_NOT_VISIBLE'
        next_action = 'AUDIT_MATCHER_TO_DB_TABLE_BINDING'
    elif failed:
        decision = 'NEWS_STATIC_AUDIT_HAS_FAILED_GATES'
        next_action = 'REPAIR_FAILED_STATIC_GATES'
    else:
        decision = 'NEWS_STATIC_AUDIT_PASS_READY_FOR_DRYRUN_PROBE'
        next_action = 'RUN_TEMPDB_OR_DRYRUN_MATCHER_PROBE'
    result = {
        'stage': 'N17A1_NEWS_RUNNER_STATIC_AUDIT',
        'generated_at_utc': now(),
        'producer': 'tools/n17a1_news_runner_static_audit_v1.py',
        'decision': decision,
        'next_action': next_action,
        'files': records,
        'flags': {'runner': runner_flags, 'original_runner': original_flags, 'matcher': matcher_flags},
        'checks': checks,
        'failed_checks': failed,
        'authority': {'readonly': True, 'systemd_start': False, 'systemd_stop': False, 'api_calls': 0, 'provider_call': False, 'wallet': False, 'signing': False, 'live_trade': False, 'db_write': False, 'core_change': False}
    }
    atomic_write(OUT, result)
    ROWS.parent.mkdir(parents=True, exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c, ensure_ascii=False, sort_keys=True) for c in checks) + '\n', encoding='utf-8')
    print('FINAL_GATE=PASS_N17A1_NEWS_RUNNER_STATIC_AUDIT')
    print('DECISION=' + decision)
    print('NEXT_ACTION=' + next_action)
    print('JSON=' + str(OUT.relative_to(ROOT)))


if __name__ == '__main__':
    main()
