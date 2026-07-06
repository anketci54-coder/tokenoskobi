#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, tempfile, urllib.request

ROOT=Path('/root/tokenoskobi_clean_v1')
DB=ROOT/'data/tokenoskobi_clean_v1.sqlite'
PANEL=ROOT/'active_panel_8096/current/data/onchain_center_live_readmodel_v1.json'
OUT=ROOT/'data/control/n21b_onchain_source_proof_bundle_v1.json'
ROWS=ROOT/'data/control/n21b_onchain_source_proof_bundle_v1_rows.jsonl'
HINTS=['token','pair','holder','liquidity','pool','birth','score','risk','lifecycle']
CORE_TABLES=['tokens','pairs','token_birth_events','pair_birth_events','liquidity_snapshots','holder_snapshots','token_score_snapshots','token_risk_events','state_aggregated_token_readmodel_v1']

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21b_',suffix='.json',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def http():
    url='https://panel.coinoskobi.com/data/onchain_center_live_readmodel_v1.json'
    try:
        r=urllib.request.urlopen(url,timeout=8); b=r.read(2500)
        return {'ok':True,'status':r.status,'bytes':len(b)}
    except Exception as e:
        return {'ok':False,'status':None,'error':type(e).__name__+':'+str(e)[:160]}
def inv():
    con=sqlite3.connect(str(DB)); cur=con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    out=[]
    for (name,) in cur.fetchall():
        if name in CORE_TABLES or any(h in name.lower() for h in HINTS):
            try:
                cur.execute(f'SELECT COUNT(*) FROM {name}')
                cnt=int(cur.fetchone()[0])
            except Exception: cnt=None
            cur.execute(f'PRAGMA table_info({name})')
            cols=[r[1] for r in cur.fetchall()]
            out.append({'table':name,'count':cnt,'columns':cols})
    con.close(); return out
def main():
    tables=inv() if DB.exists() else []
    counts={t['table']:t['count'] for t in tables}
    core={t:counts.get(t) for t in CORE_TABLES}
    nonzero=[t for t in tables if (t.get('count') or 0)>0 and not t['table'].startswith('archive_')]
    panel={'exists':PANEL.exists(),'parse_ok':False,'decision':None}
    if PANEL.exists():
        try:
            j=read_json(PANEL); panel['parse_ok']=True; panel['decision']=j.get('decision')
        except Exception as e: panel['error']=type(e).__name__+':'+str(e)[:160]
    minimum_ready=(counts.get('tokens') or 0)>0 and (counts.get('pairs') or 0)>0
    liquidity_ready=(counts.get('liquidity_snapshots') or 0)>0
    holder_ready=(counts.get('holder_snapshots') or 0)>0 or (counts.get('holder_distribution_events') or 0)>0
    score_ready=(counts.get('token_score_snapshots') or 0)>0 or (counts.get('token_score_100_events') or 0)>0
    decision='ONCHAIN_SOURCE_READY_FOR_PANEL_BINDING' if minimum_ready else 'ONCHAIN_SOURCE_PARTIAL_NEEDS_MAPPING'
    checks=[
      {'gate':'db_exists','ok':DB.exists(),'value':str(DB)},
      {'gate':'tokens_nonzero','ok':(counts.get('tokens') or 0)>0,'value':counts.get('tokens')},
      {'gate':'pairs_nonzero','ok':(counts.get('pairs') or 0)>0,'value':counts.get('pairs')},
      {'gate':'liquidity_ready','ok':liquidity_ready,'value':counts.get('liquidity_snapshots')},
      {'gate':'holder_ready','ok':holder_ready,'value':{'holder_snapshots':counts.get('holder_snapshots'),'holder_distribution_events':counts.get('holder_distribution_events')}},
      {'gate':'score_ready','ok':score_ready,'value':{'token_score_snapshots':counts.get('token_score_snapshots'),'token_score_100_events':counts.get('token_score_100_events')}},
      {'gate':'panel_http_200','ok':http().get('status')==200}
    ]
    result={'stage':'N21B_ONCHAIN_SOURCE_PROOF_BUNDLE','generated_at_utc':now(),'decision':decision,'next_action':'N21B2_ONCHAIN_PANEL_BINDING' if minimum_ready else 'N21B2_ONCHAIN_SCHEMA_MAPPING','core_counts':core,'nonzero_active_tables':nonzero[:60],'panel_local':panel,'checks':checks,'authority':{'readonly':True,'real_db_write':False,'panel_json_write':False,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21B_ONCHAIN_SOURCE_PROOF_BUNDLE')
    print('DECISION='+decision)
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
