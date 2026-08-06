#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, subprocess, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
OUT = ROOT / 'data/control/n17a_news_runtime_probe_readonly_result_v1.json'
ROWS = ROOT / 'data/control/n17a_news_runtime_probe_readonly_result_v1_rows.jsonl'
DB_CANDIDATES = [
    ROOT / 'data/tokenoskobi_v1.sqlite',
    ROOT / 'data/tokenoskobi.sqlite',
    ROOT / 'tokenoskobi.sqlite',
    ROOT / 'data/tokenoskobi_clean_v1.sqlite'
]
TABLES = ['news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1']
RUNNERS = [
    ROOT / 'tools/news_radar_refresh_runner_v1.py',
    ROOT / 'tools/news_token_matcher_v1.py',
    ROOT / 'tools/news_radar_refresh_runner_v1.ORIGINAL_NEWS27A11_20260510_211813.py'
]
SYSTEMD_UNITS = [
    'tokenoskobi-news-radar-refresh.service',
    'tokenoskobi-news-radar-refresh.timer'
]

def now():
    return datetime.now(timezone.utc).isoformat()

def run(cmd):
    p = subprocess.run(cmd, shell=True, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'cmd': cmd, 'rc': p.returncode, 'stdout': p.stdout[-4000:], 'stderr': p.stderr[-2000:]}

def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def atomic_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.n17a_news_probe_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write('\n')
        read_json(Path(tmp))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def table_count(db, table):
    try:
        con = sqlite3.connect(str(db))
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        exists = cur.fetchone() is not None
        count = None
        if exists:
            cur.execute(f'SELECT COUNT(*) FROM {table}')
            count = cur.fetchone()[0]
        con.close()
        return {'table': table, 'exists': exists, 'count': count, 'error': None}
    except Exception as e:
        return {'table': table, 'exists': False, 'count': None, 'error': type(e).__name__ + ':' + str(e)[:200]}

def main():
    units = {u: run('systemctl is-active ' + u + ' || true') for u in SYSTEMD_UNITS}
    unit_status = {u: units[u]['stdout'].strip() for u in SYSTEMD_UNITS}
    unit_files = {u: run('systemctl cat ' + u + ' 2>/dev/null || true') for u in SYSTEMD_UNITS}
    runners = [{'path': str(p), 'exists': p.exists(), 'is_file': p.is_file() if p.exists() else False} for p in RUNNERS]
    dbs = [{'path': str(p), 'exists': p.exists(), 'is_file': p.is_file() if p.exists() else False} for p in DB_CANDIDATES]
    selected_db = next((p for p in DB_CANDIDATES if p.exists() and p.is_file()), None)
    table_counts = [table_count(selected_db, t) for t in TABLES] if selected_db else []
    log_files = []
    for p in [ROOT/'logs/news_radar/news_radar_refresh.log', ROOT/'logs/news_radar/news_radar_refresh.err.log']:
        log_files.append({'path': str(p), 'exists': p.exists(), 'size': p.stat().st_size if p.exists() else None, 'mtime_utc': datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat() if p.exists() else None})

    checks = [
        {'name': 'service_unit_exists', 'ok': bool(unit_files[SYSTEMD_UNITS[0]]['stdout'].strip())},
        {'name': 'timer_unit_exists', 'ok': bool(unit_files[SYSTEMD_UNITS[1]]['stdout'].strip())},
        {'name': 'timer_active', 'ok': unit_status.get(SYSTEMD_UNITS[1]) == 'active'},
        {'name': 'runner_exists', 'ok': any(r['exists'] for r in runners)},
        {'name': 'db_selected', 'ok': selected_db is not None},
        {'name': 'raw_feed_table_nonzero', 'ok': any(t['table']=='news_raw_feed_events' and (t['count'] or 0) > 0 for t in table_counts)},
        {'name': 'token_match_table_nonzero', 'ok': any(t['table']=='news_token_match_events' and (t['count'] or 0) > 0 for t in table_counts)},
        {'name': 'signal_table_nonzero', 'ok': any(t['table']=='news_signal_events' and (t['count'] or 0) > 0 for t in table_counts)},
        {'name': 'score_table_nonzero', 'ok': any(t['table']=='news_score_events_v1' and (t['count'] or 0) > 0 for t in table_counts)}
    ]
    if unit_status.get(SYSTEMD_UNITS[1]) == 'active' and all(c['ok'] for c in checks[:6]):
        decision = 'NEWS_RUNTIME_PARTIAL_PROVEN_NEEDS_MATCH_SIGNAL_SCORE_REPAIR'
    elif any(t.get('count') for t in table_counts):
        decision = 'NEWS_RUNTIME_HISTORICAL_DATA_PRESENT_BUT_NOT_LIVE_PROVEN'
    else:
        decision = 'NEWS_RUNTIME_NOT_LIVE_PROVEN'

    result = {
        'stage': 'N17A_NEWS_RUNTIME_PROBE_READONLY',
        'generated_at_utc': now(),
        'producer': 'tools/news_runtime_probe_readonly_v1.py',
        'decision': decision,
        'unit_status': unit_status,
        'runners': runners,
        'db_candidates': dbs,
        'selected_db': str(selected_db) if selected_db else None,
        'table_counts': table_counts,
        'log_files': log_files,
        'checks': checks,
        'authority': {'readonly': True, 'systemd_start': False, 'systemd_stop': False, 'api_calls': 0, 'provider_call': False, 'wallet': False, 'signing': False, 'live_trade': False, 'db_write': False, 'core_change': False},
        'next_step': 'N17A_DECIDE_NEWS_REPAIR_OR_KEEP_SEALED_INACTIVE'
    }
    atomic_write(OUT, result)
    ROWS.parent.mkdir(parents=True, exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in checks) + '\n', encoding='utf-8')
    print('FINAL_GATE=PASS_N17A_NEWS_RUNTIME_PROBE_READONLY')
    print('DECISION=' + decision)
    print('JSON=' + str(OUT.relative_to(ROOT)))
    print('ROWS=' + str(ROWS.relative_to(ROOT)))

if __name__ == '__main__':
    main()
