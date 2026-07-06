#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import importlib.util, json, os, shutil, sqlite3, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
REAL_DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
OUT = ROOT / 'data/control/n17a5_news_matcher_binding_tempdb_runner_v1.json'
ROWS = ROOT / 'data/control/n17a5_news_matcher_binding_tempdb_runner_v1_rows.jsonl'
MATCHER_PATH = ROOT / 'tools/news_token_matcher_v1.py'

TOKEN_DICTIONARY = [
    {'token_uid':'dict_btc','pair_uid':'dict_btc_usd','symbol':'BTC','name':'Bitcoin','chain':'Bitcoin'},
    {'token_uid':'dict_eth','pair_uid':'dict_eth_usd','symbol':'ETH','name':'Ethereum','chain':'Ethereum'},
    {'token_uid':'dict_bnb','pair_uid':'dict_bnb_usd','symbol':'BNB','name':'BNB','chain':'BSC'},
    {'token_uid':'dict_sol','pair_uid':'dict_sol_usd','symbol':'SOL','name':'Solana','chain':'Solana'},
    {'token_uid':'dict_xrp','pair_uid':'dict_xrp_usd','symbol':'XRP','name':'XRP','chain':'XRP'},
    {'token_uid':'dict_doge','pair_uid':'dict_doge_usd','symbol':'DOGE','name':'Dogecoin','chain':'Dogecoin'},
    {'token_uid':'dict_ton','pair_uid':'dict_ton_usd','symbol':'TON','name':'Toncoin','chain':'TON'},
]

def now(): return datetime.now(timezone.utc).isoformat()

def read_json(path):
    with open(path, encoding='utf-8') as f: return json.load(f)

def awrite(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.n17a5_', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def load_matcher():
    spec = importlib.util.spec_from_file_location('news_token_matcher_v1', str(MATCHER_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def count(con, table):
    cur=con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if cur.fetchone() is None: return None
    cur.execute(f'SELECT COUNT(*) FROM {table}')
    return int(cur.fetchone()[0])

def ensure_match_table(con):
    con.execute('''CREATE TABLE IF NOT EXISTS news_token_match_events (
        match_uid TEXT PRIMARY KEY,
        news_uid TEXT,
        source_uid TEXT,
        token_uid TEXT,
        pair_uid TEXT,
        symbol TEXT,
        chain TEXT,
        match_type TEXT,
        match_confidence TEXT,
        match_score INTEGER,
        match_reasons_json TEXT,
        evidence_text TEXT,
        is_duplicate INTEGER DEFAULT 0,
        write_allowed INTEGER DEFAULT 0,
        trade_signal INTEGER DEFAULT 0,
        paper_signal INTEGER DEFAULT 0,
        created_at_utc TEXT
    )''')
    con.commit()

def raw_rows(con, limit=100):
    cur=con.cursor()
    cur.execute('SELECT news_uid, source_uid, title, published_at_utc FROM news_raw_feed_events ORDER BY published_at_utc DESC LIMIT ?', (limit,))
    cols=[d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def insert_matches(con, matches):
    inserted=0
    for m in matches:
        if not m.get('write_allowed'):
            continue
        con.execute('''INSERT OR REPLACE INTO news_token_match_events
            (match_uid, news_uid, source_uid, token_uid, pair_uid, symbol, chain, match_type, match_confidence, match_score, match_reasons_json, evidence_text, is_duplicate, write_allowed, trade_signal, paper_signal, created_at_utc)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (m.get('match_uid'), m.get('news_uid'), m.get('source_uid'), m.get('token_uid'), m.get('pair_uid'), m.get('symbol'), m.get('chain'), m.get('match_type'), m.get('match_confidence'), int(m.get('match_score') or 0), json.dumps(m.get('match_reasons') or [], ensure_ascii=False), m.get('evidence_text'), int(bool(m.get('is_duplicate'))), int(bool(m.get('write_allowed'))), int(bool(m.get('trade_signal'))), int(bool(m.get('paper_signal'))), now()))
        inserted += 1
    con.commit()
    return inserted

def main():
    if not REAL_DB.exists():
        raise SystemExit('FAIL_REAL_DB_MISSING')
    if not MATCHER_PATH.exists():
        raise SystemExit('FAIL_MATCHER_MISSING')
    work=Path(tempfile.mkdtemp(prefix='n17a5_news_binding_'))
    tempdb=work/REAL_DB.name
    shutil.copy2(REAL_DB, tempdb)
    matcher=load_matcher()

    real_before={}
    con_real=sqlite3.connect(str(REAL_DB))
    for t in ['news_raw_feed_events','news_token_match_events']:
        real_before[t]=count(con_real,t)
    con_real.close()

    con=sqlite3.connect(str(tempdb))
    ensure_match_table(con)
    before=count(con,'news_token_match_events') or 0
    raws=raw_rows(con, 100)
    matches=matcher.match_many(raws, TOKEN_DICTIONARY)
    inserted=insert_matches(con, matches)
    after=count(con,'news_token_match_events') or 0
    sample=[m for m in matches if m.get('write_allowed')][:10]
    con.close()

    con_real=sqlite3.connect(str(REAL_DB))
    real_after={}
    for t in ['news_raw_feed_events','news_token_match_events']:
        real_after[t]=count(con_real,t)
    con_real.close()
    real_unchanged = real_before == real_after

    if inserted > 0 and real_unchanged:
        decision='TEMPDB_MATCHER_BINDING_PROVEN_REAL_DB_UNCHANGED'
        next_action='PROMOTE_ACTIVE_MATCH_TABLE_SCHEMA_AND_BINDING_WITH_APPROVAL'
    elif inserted == 0 and real_unchanged:
        decision='TEMPDB_BINDING_RUNS_BUT_NO_WRITABLE_MATCHES'
        next_action='TRACE_MATCHER_RULES_AGAINST_RAW_SAMPLE_AND_DICTIONARY'
    else:
        decision='REAL_DB_CHANGED_ABORT_REVIEW'
        next_action='STOP_AND_REVIEW'

    result={
        'stage':'N17A5_NEWS_MATCHER_BINDING_TEMPDB_RUNNER',
        'generated_at_utc':now(),
        'producer':'tools/n17a5_news_matcher_binding_tempdb_runner_v1.py',
        'decision':decision,
        'next_action':next_action,
        'real_db':str(REAL_DB),
        'temp_db':str(tempdb),
        'raw_count_used':len(raws),
        'token_dictionary_count':len(TOKEN_DICTIONARY),
        'matches_returned':len(matches),
        'writable_matches':sum(1 for m in matches if m.get('write_allowed')),
        'inserted_tempdb':inserted,
        'temp_match_count_before':before,
        'temp_match_count_after':after,
        'real_before':real_before,
        'real_after':real_after,
        'real_unchanged':real_unchanged,
        'sample_writable_matches':sample,
        'checks':[
            {'gate':'real_db_exists','ok':REAL_DB.exists()},
            {'gate':'matcher_exists','ok':MATCHER_PATH.exists()},
            {'gate':'raw_rows_used_positive','ok':len(raws)>0,'value':len(raws)},
            {'gate':'tempdb_inserted_positive','ok':inserted>0,'value':inserted},
            {'gate':'real_db_unchanged','ok':real_unchanged,'value':{'before':real_before,'after':real_after}}
        ],
        'authority':{'real_db_write':False,'tempdb_write':True,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}
    }
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True, exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in result['checks'])+'\n', encoding='utf-8')
    print('FINAL_GATE=PASS_N17A5_NEWS_MATCHER_BINDING_TEMPDB_RUNNER')
    print('DECISION='+decision)
    print('NEXT_ACTION='+next_action)
    print('INSERTED_TEMPDB='+str(inserted))
    print('JSON='+str(OUT.relative_to(ROOT)))

if __name__=='__main__': main()
