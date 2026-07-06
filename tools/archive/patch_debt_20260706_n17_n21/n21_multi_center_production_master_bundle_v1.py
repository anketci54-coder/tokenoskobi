#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, tempfile, urllib.request

ROOT = Path('/root/tokenoskobi_clean_v1')
DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
PANEL = ROOT / 'active_panel_8096/current/data'
OUT = ROOT / 'data/control/n21_multi_center_production_master_bundle_v1.json'
ROWS = ROOT / 'data/control/n21_multi_center_production_master_bundle_v1_rows.jsonl'
CENTERS = {
    'news': 'news_center_live_readmodel_v1.json',
    'whale': 'whale_center_live_readmodel_v1.json',
    'onchain': 'onchain_center_live_readmodel_v1.json',
    'risk': 'risk_center_live_readmodel_v1.json',
    'technical': 'technical_center_live_readmodel_v1.json',
    'lifecycle': 'lifecycle_center_live_readmodel_v1.json',
    'system': 'system_center_live_readmodel_v1.json',
    'command': 'command_center_live_readmodel_v1.json'
}
EXPECTED_TABLE_HINTS = {
    'news': ['news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1','news_runtime_freshness_v1'],
    'whale': ['whale','wallet','entity','transfer'],
    'onchain': ['onchain','token','pair','pool','holder','liquidity'],
    'risk': ['risk','honeypot','rug','slippage','mev'],
    'technical': ['technical','ohlcv','candle','indicator','rsi','trend'],
    'lifecycle': ['lifecycle','state','morg','clinic','autopsy']
}

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p, encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21_', suffix='.json', dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def http_json(path):
    url='https://panel.coinoskobi.com/data/'+path
    try:
        r=urllib.request.urlopen(url, timeout=8); b=r.read(4096)
        return {'url':url,'ok':True,'status':r.status,'head_bytes':len(b)}
    except Exception as e:
        return {'url':url,'ok':False,'status':None,'error':type(e).__name__+':'+str(e)[:180]}
def table_inventory():
    if not DB.exists(): return []
    con=sqlite3.connect(str(DB)); cur=con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables=[]
    for (name,) in cur.fetchall():
        try:
            cur.execute(f'SELECT COUNT(*) FROM {name}')
            cnt=int(cur.fetchone()[0])
        except Exception:
            cnt=None
        tables.append({'table':name,'count':cnt})
    con.close(); return tables
def center_panel_state(center, filename):
    p=PANEL/filename
    local={'file':str(p.relative_to(ROOT)),'exists':p.exists(),'parse_ok':False,'decision':None,'items_status':[]}
    if p.exists():
        try:
            j=read_json(p); local['parse_ok']=True; local['decision']=j.get('decision')
            local['items_status']=[i.get('status') for i in j.get('items',[]) if isinstance(i,dict)]
        except Exception as e:
            local['error']=type(e).__name__+':'+str(e)[:160]
    return {'center':center,'local':local,'https':http_json(filename)}
def readiness(center, tables, panel_state):
    names=[t['table'] for t in tables]
    counts={t['table']:t.get('count') for t in tables}
    if center=='news':
        ok=all((counts.get(t) or 0)>0 for t in EXPECTED_TABLE_HINTS['news']) and panel_state['local'].get('decision')=='NEWS_CENTER_REAL_PIPELINE_BOUND'
        return {'center':center,'status':'PRODUCTION_BOUND' if ok else 'NEEDS_REPAIR','proof':{t:counts.get(t) for t in EXPECTED_TABLE_HINTS['news']}}
    hints=EXPECTED_TABLE_HINTS.get(center,[])
    matched=[t for t in names if any(h.lower() in t.lower() for h in hints)]
    nonzero=[t for t in matched if (counts.get(t) or 0)>0]
    decision=panel_state['local'].get('decision')
    if nonzero:
        status='SOURCE_TABLE_NONZERO_NEEDS_BINDING'
    elif matched:
        status='SOURCE_TABLE_EXISTS_ZERO_OR_ARCHIVE'
    elif decision and 'DATA_MISSING' not in str(decision) and 'SEALED' not in str(decision):
        status='PANEL_READY_SOURCE_UNPROVEN'
    else:
        status='DATA_MISSING_NEEDS_PRODUCER'
    return {'center':center,'status':status,'matched_tables':matched[:30],'nonzero_tables':nonzero[:30],'panel_decision':decision}
def main():
    tables=table_inventory()
    panels={c:center_panel_state(c,f) for c,f in CENTERS.items()}
    ready={c:readiness(c,tables,panels[c]) for c in ['news','whale','onchain','risk','technical','lifecycle']}
    fusion_inputs={c:ready[c]['status'] for c in ready}
    fusion_status='FUSION_READY_PARTIAL_NEWS_ONLY' if ready['news']['status']=='PRODUCTION_BOUND' else 'FUSION_NOT_READY'
    blockers=[{'center':c,'status':r['status']} for c,r in ready.items() if r['status']!='PRODUCTION_BOUND']
    result={'stage':'N21_MULTI_CENTER_PRODUCTION_MASTER_BUNDLE','generated_at_utc':now(),'decision':fusion_status,'db_exists':DB.exists(),'table_count':len(tables),'center_panels':panels,'center_readiness':ready,'fusion_inputs':fusion_inputs,'blockers':blockers,'next_sequence':['N21A whale producer/source proof','N21B onchain producer/source proof','N21C risk producer/source proof','N21D technical producer/source proof','N21E lifecycle producer/source proof','N21F fusion command readmodel after at least two non-news centers are production-bound'],'authority':{'readonly':True,'real_db_write':False,'tempdb_write':False,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    checks=[]
    for c,r in ready.items(): checks.append({'gate':c+'_readiness','ok':r['status']=='PRODUCTION_BOUND','value':r['status']})
    result['checks']=checks
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21_MULTI_CENTER_PRODUCTION_MASTER_BUNDLE')
    print('DECISION='+fusion_status)
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
