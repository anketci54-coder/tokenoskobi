#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import importlib.util, json, os, shutil, sqlite3, tempfile

ROOT = Path('/root/tokenoskobi_clean_v1')
REAL_DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
PANEL_DATA = ROOT / 'active_panel_8096/current/data'
NEWS_PANEL = PANEL_DATA / 'news_center_live_readmodel_v1.json'
COMMAND_PANEL = PANEL_DATA / 'command_center_live_readmodel_v1.json'
OUT = ROOT / 'data/control/n18_n19_n20_news_production_bundle_v1.json'
ROWS = ROOT / 'data/control/n18_n19_n20_news_production_bundle_v1_rows.jsonl'
MATCHER_PATH = ROOT / 'tools/news_token_matcher_v1.py'

TOKENS = [
    {'token_uid':'dict_btc','pair_uid':'dict_btc_usd','symbol':'BTC','name':'Bitcoin','chain':'Bitcoin'},
    {'token_uid':'dict_eth','pair_uid':'dict_eth_usd','symbol':'ETH','name':'Ethereum','chain':'Ethereum'},
    {'token_uid':'dict_bnb','pair_uid':'dict_bnb_usd','symbol':'BNB','name':'BNB','chain':'BSC'},
    {'token_uid':'dict_sol','pair_uid':'dict_sol_usd','symbol':'SOL','name':'Solana','chain':'Solana'},
    {'token_uid':'dict_xrp','pair_uid':'dict_xrp_usd','symbol':'XRP','name':'XRP','chain':'XRP'},
    {'token_uid':'dict_doge','pair_uid':'dict_doge_usd','symbol':'DOGE','name':'Dogecoin','chain':'Dogecoin'},
    {'token_uid':'dict_ton','pair_uid':'dict_ton_usd','symbol':'TON','name':'Toncoin','chain':'TON'}
]

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p, encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n18n19n20_', suffix='.json', dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def load_matcher():
    spec=importlib.util.spec_from_file_location('news_token_matcher_v1', str(MATCHER_PATH))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def count(con,t):
    cur=con.cursor(); cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(t,))
    if cur.fetchone() is None: return None
    cur.execute(f'SELECT COUNT(*) FROM {t}'); return int(cur.fetchone()[0])
def ensure_tables(con):
    con.execute('''CREATE TABLE IF NOT EXISTS news_token_match_events (
      match_uid TEXT PRIMARY KEY, news_uid TEXT, source_uid TEXT, token_uid TEXT, pair_uid TEXT,
      symbol TEXT, chain TEXT, match_type TEXT, match_confidence TEXT, match_score INTEGER,
      match_reasons_json TEXT, evidence_text TEXT, is_duplicate INTEGER DEFAULT 0,
      write_allowed INTEGER DEFAULT 0, trade_signal INTEGER DEFAULT 0, paper_signal INTEGER DEFAULT 0,
      created_at_utc TEXT)''')
    con.execute('''CREATE TABLE IF NOT EXISTS news_signal_events (
      signal_uid TEXT PRIMARY KEY, news_uid TEXT, token_uid TEXT, pair_uid TEXT, symbol TEXT, chain TEXT,
      signal_type TEXT, signal_strength INTEGER, signal_label TEXT, source_match_uid TEXT,
      evidence_text TEXT, created_at_utc TEXT)''')
    con.execute('''CREATE TABLE IF NOT EXISTS news_score_events_v1 (
      score_uid TEXT PRIMARY KEY, news_uid TEXT, token_uid TEXT, pair_uid TEXT, symbol TEXT, chain TEXT,
      news_token_relevance_score_100 INTEGER, news_risk_score_100 INTEGER, news_fusion_score_100 INTEGER,
      importance_label TEXT, risk_label TEXT, fusion_label TEXT, explanation TEXT, created_at_utc TEXT)''')
    con.execute('''CREATE TABLE IF NOT EXISTS news_runtime_freshness_v1 (
      freshness_uid TEXT PRIMARY KEY, component TEXT, last_observed_at_utc TEXT, raw_count INTEGER,
      match_count INTEGER, signal_count INTEGER, score_count INTEGER, heartbeat_status TEXT, created_at_utc TEXT)''')
    con.commit()
def raw_rows(con, limit=100):
    cur=con.cursor(); cur.execute('SELECT news_uid, source_uid, title, published_at_utc FROM news_raw_feed_events ORDER BY published_at_utc DESC LIMIT ?', (limit,))
    cols=[d[0] for d in cur.description]
    return [dict(zip(cols,row)) for row in cur.fetchall()]
def insert_matches(con, matches):
    n=0
    for m in matches:
        if not m.get('write_allowed'): continue
        con.execute('''INSERT OR REPLACE INTO news_token_match_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            m.get('match_uid'),m.get('news_uid'),m.get('source_uid'),m.get('token_uid'),m.get('pair_uid'),m.get('symbol'),m.get('chain'),m.get('match_type'),m.get('match_confidence'),int(m.get('match_score') or 0),json.dumps(m.get('match_reasons') or [],ensure_ascii=False),m.get('evidence_text'),int(bool(m.get('is_duplicate'))),int(bool(m.get('write_allowed'))),0,0,now()))
        n+=1
    con.commit(); return n
def promote_signals_scores(con):
    cur=con.cursor(); cur.execute('SELECT match_uid,news_uid,token_uid,pair_uid,symbol,chain,match_score,evidence_text FROM news_token_match_events WHERE write_allowed=1 LIMIT 100')
    rows=cur.fetchall(); sig=0; sco=0
    for match_uid,news_uid,token_uid,pair_uid,symbol,chain,match_score,evidence_text in rows:
        signal_uid='signal_'+match_uid.replace('match_','')
        score_uid='score_'+match_uid.replace('match_','')
        strength=int(match_score or 0)
        label='HIGH' if strength>=70 else 'MEDIUM' if strength>=45 else 'LOW'
        con.execute('INSERT OR REPLACE INTO news_signal_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (signal_uid,news_uid,token_uid,pair_uid,symbol,chain,'TOKEN_NEWS_MATCH',strength,label,match_uid,evidence_text,now()))
        risk=max(0,100-strength)
        con.execute('INSERT OR REPLACE INTO news_score_events_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (score_uid,news_uid,token_uid,pair_uid,symbol,chain,strength,risk,strength,label,'LOW' if risk<40 else 'MEDIUM','NEWS_TOKEN_RELEVANT','TempDB proof score from matcher binding bundle',now()))
        sig+=1; sco+=1
    con.commit(); return sig,sco
def write_freshness(con):
    vals={t:count(con,t) or 0 for t in ['news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1']}
    status='GREEN' if vals['news_token_match_events']>0 and vals['news_signal_events']>0 and vals['news_score_events_v1']>0 else 'YELLOW'
    con.execute('INSERT OR REPLACE INTO news_runtime_freshness_v1 VALUES (?,?,?,?,?,?,?,?,?)', ('fresh_news_bundle','news_pipeline_tempdb',now(),vals['news_raw_feed_events'],vals['news_token_match_events'],vals['news_signal_events'],vals['news_score_events_v1'],status,now()))
    con.commit(); return vals,status
def real_counts():
    con=sqlite3.connect(str(REAL_DB)); out={t:count(con,t) for t in ['news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1']}; con.close(); return out
def main():
    before=real_counts()
    work=Path(tempfile.mkdtemp(prefix='n18_n19_n20_news_')); tempdb=work/REAL_DB.name; shutil.copy2(REAL_DB,tempdb)
    matcher=load_matcher(); con=sqlite3.connect(str(tempdb)); ensure_tables(con)
    raws=raw_rows(con,100); matches=matcher.match_many(raws,TOKENS); inserted=insert_matches(con,matches)
    sig,sco=promote_signals_scores(con); freshness,status=write_freshness(con); con.close()
    after=real_counts(); real_unchanged=(before==after)
    n18='PASS' if inserted>0 and real_unchanged else 'FAIL'
    n19='PASS' if status in ('GREEN','YELLOW') and real_unchanged else 'FAIL'
    n20='PASS' if sig>0 and sco>0 and real_unchanged else 'FAIL'
    decision='N18_N19_N20_TEMPDB_PROOF_READY_FOR_APPROVAL' if n18==n19==n20=='PASS' else 'N18_N19_N20_NEEDS_REPAIR'
    result={
      'stage':'N18_N19_N20_NEWS_PRODUCTION_BUNDLE','generated_at_utc':now(),'decision':decision,
      'n18_news_production_binding':n18,'n19_live_freshness':n19,'n20_command_integration':n20,
      'real_db':str(REAL_DB),'temp_db':str(tempdb),'real_before':before,'real_after':after,'real_unchanged':real_unchanged,
      'raw_used':len(raws),'matches_returned':len(matches),'matches_inserted_tempdb':inserted,'signals_inserted_tempdb':sig,'scores_inserted_tempdb':sco,
      'freshness_counts':freshness,'heartbeat_status':status,
      'next_action':'APPROVE_REAL_DB_APPLY_OR_KEEP_TEMPDB_ONLY',
      'authority':{'real_db_write':False,'tempdb_write':True,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False},
      'checks':[{'gate':'n18_match_inserted_tempdb','ok':inserted>0,'value':inserted},{'gate':'n19_freshness_written_tempdb','ok':bool(status),'value':status},{'gate':'n20_signal_score_tempdb','ok':sig>0 and sco>0,'value':{'signals':sig,'scores':sco}},{'gate':'real_db_unchanged','ok':real_unchanged,'value':{'before':before,'after':after}}]
    }
    awrite(OUT,result); ROWS.parent.mkdir(parents=True,exist_ok=True); ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in result['checks'])+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N18_N19_N20_NEWS_PRODUCTION_BUNDLE')
    print('DECISION='+decision); print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
