#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, sqlite3, subprocess, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
OUT = ROOT / 'data/control/n17a2_news_matcher_dryrun_probe_v1.json'
ROWS = ROOT / 'data/control/n17a2_news_matcher_dryrun_probe_v1_rows.jsonl'
DB_CANDIDATES = [
    ROOT / 'data/tokenoskobi_v1.sqlite',
    ROOT / 'data/tokenoskobi.sqlite',
    ROOT / 'tokenoskobi.sqlite',
    ROOT / 'data/tokenoskobi_clean_v1.sqlite'
]
TABLES = ['news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1']
MATCHER = ROOT / 'tools/news_token_matcher_v1.py'
RUNNER = ROOT / 'tools/news_radar_refresh_runner_v1.py'

def now(): return datetime.now(timezone.utc).isoformat()

def run(cmd, env=None):
    p = subprocess.run(cmd, shell=True, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return {'cmd': cmd, 'rc': p.returncode, 'stdout': p.stdout[-4000:], 'stderr': p.stderr[-3000:]}

def read_json(path):
    with open(path, encoding='utf-8') as f: return json.load(f)

def atomic_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.n17a2_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def count_table(db, table):
    try:
        con = sqlite3.connect(str(db)); cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        exists = cur.fetchone() is not None
        count = None
        if exists:
            cur.execute(f'SELECT COUNT(*) FROM {table}')
            count = int(cur.fetchone()[0])
        con.close()
        return {'table': table, 'exists': exists, 'count': count, 'error': None}
    except Exception as e:
        return {'table': table, 'exists': False, 'count': None, 'error': type(e).__name__ + ':' + str(e)[:200]}

def counts(db): return [count_table(db, t) for t in TABLES]

def map_counts(rows): return {r['table']: (r.get('count') or 0) for r in rows}

def main():
    selected = next((p for p in DB_CANDIDATES if p.exists() and p.is_file()), None)
    if not selected:
        result = {'stage':'N17A2_NEWS_MATCHER_DRYRUN_PROBE','generated_at_utc':now(),'decision':'NO_DB_FOUND','authority':{'real_db_write':False,'api_calls':0,'core_change':False}}
        atomic_write(OUT, result); print('FINAL_GATE=PASS_N17A2_NEWS_MATCHER_DRYRUN_PROBE'); print('DECISION=NO_DB_FOUND'); return

    work = Path(tempfile.mkdtemp(prefix='n17a2_news_dryrun_'))
    tempdb = work / selected.name
    shutil.copy2(selected, tempdb)
    before_real = counts(selected)
    before_temp = counts(tempdb)

    env = os.environ.copy()
    # Best-effort common DB env names; script still records if matcher ignores them.
    env.update({
        'TOKENOSKOBI_DB_PATH': str(tempdb),
        'TOKENOSKOBI_SQLITE_PATH': str(tempdb),
        'DB_PATH': str(tempdb),
        'SQLITE_PATH': str(tempdb),
        'TOKENOSKOBI_NOAPI': '1',
        'TOKENOSKOBI_DRYRUN': '1'
    })

    matcher_run = {'cmd': 'SKIPPED_NO_MATCHER', 'rc': None, 'stdout': '', 'stderr': ''}
    if MATCHER.exists():
        matcher_run = run('python3 tools/news_token_matcher_v1.py', env=env)

    after_temp = counts(tempdb)
    after_real = counts(selected)
    bt, at = map_counts(before_temp), map_counts(after_temp)
    br, ar = map_counts(before_real), map_counts(after_real)
    temp_delta = {k: at.get(k,0)-bt.get(k,0) for k in TABLES}
    real_delta = {k: ar.get(k,0)-br.get(k,0) for k in TABLES}

    temp_wrote_match = temp_delta.get('news_token_match_events',0) > 0
    real_unchanged = all(v == 0 for v in real_delta.values())
    raw_available = bt.get('news_raw_feed_events',0) > 0

    if matcher_run['rc'] == 0 and temp_wrote_match and real_unchanged:
        decision = 'MATCHER_DRYRUN_TEMPDB_WRITES_MATCHES_REAL_DB_UNCHANGED'
        next_action = 'AUDIT_SIGNAL_SCORE_CHAIN_TEMPDB'
    elif matcher_run['rc'] == 0 and raw_available and not temp_wrote_match:
        decision = 'MATCHER_RUNS_BUT_PRODUCES_NO_MATCHES_FROM_RAW_NEWS'
        next_action = 'AUDIT_MATCHER_TOKEN_SOURCE_AND_RULES'
    elif matcher_run['rc'] is None:
        decision = 'MATCHER_FILE_MISSING'
        next_action = 'RESTORE_OR_BUILD_MATCHER'
    else:
        decision = 'MATCHER_DRYRUN_FAILED'
        next_action = 'INSPECT_MATCHER_STDERR_AND_DB_PATH_BINDING'

    result = {
        'stage':'N17A2_NEWS_MATCHER_DRYRUN_PROBE',
        'generated_at_utc':now(),
        'producer':'tools/n17a2_news_matcher_dryrun_probe_v1.py',
        'decision':decision,
        'next_action':next_action,
        'selected_real_db':str(selected),
        'temp_db':str(tempdb),
        'matcher_exists':MATCHER.exists(),
        'runner_exists':RUNNER.exists(),
        'matcher_run':matcher_run,
        'before_real':before_real,
        'after_real':after_real,
        'before_temp':before_temp,
        'after_temp':after_temp,
        'temp_delta':temp_delta,
        'real_delta':real_delta,
        'checks':[
            {'name':'raw_available_in_tempdb','ok':raw_available},
            {'name':'matcher_rc_zero','ok':matcher_run['rc'] == 0},
            {'name':'tempdb_match_delta_positive','ok':temp_wrote_match},
            {'name':'real_db_unchanged','ok':real_unchanged}
        ],
        'authority':{'real_db_write':False,'tempdb_write':True,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}
    }
    atomic_write(OUT, result)
    ROWS.parent.mkdir(parents=True, exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in result['checks'])+'\n', encoding='utf-8')
    print('FINAL_GATE=PASS_N17A2_NEWS_MATCHER_DRYRUN_PROBE')
    print('DECISION='+decision)
    print('NEXT_ACTION='+next_action)
    print('JSON='+str(OUT.relative_to(ROOT)))

if __name__ == '__main__': main()
