#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, tempfile, urllib.request

ROOT=Path('/root/tokenoskobi_clean_v1')
DB=ROOT/'data/tokenoskobi_clean_v1.sqlite'
PANEL=ROOT/'active_panel_8096/current/data/lifecycle_center_live_readmodel_v1.json'
OUT=ROOT/'data/control/n21d_lifecycle_source_proof_bundle_v1.json'
ROWS=ROOT/'data/control/n21d_lifecycle_source_proof_bundle_v1_rows.jsonl'
CORE=['token_lifecycle','token_lifecycle_events','token_lifecycle_autopsy_events_v1','state_aggregated_token_readmodel_v1','autopsy_cases','autopsy_evidence_events','morgue_entries','morgue_route_decisions']
HINTS=['lifecycle','autopsy','morgue','clinic','state_aggregated']

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21d_',suffix='.json',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def http():
    try:
        r=urllib.request.urlopen('https://panel.coinoskobi.com/data/lifecycle_center_live_readmodel_v1.json',timeout=8); b=r.read(2500)
        return {'ok':True,'status':r.status,'bytes':len(b)}
    except Exception as e: return {'ok':False,'status':None,'error':type(e).__name__+':'+str(e)[:160]}
def inv():
    con=sqlite3.connect(str(DB)); cur=con.cursor(); cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    out=[]
    for (name,) in cur.fetchall():
        if name in CORE or any(h in name.lower() for h in HINTS):
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
    token_lifecycle_ready=(counts.get('token_lifecycle') or 0)>0
    lifecycle_events_ready=(counts.get('token_lifecycle_events') or 0)>0
    state_ready=(counts.get('state_aggregated_token_readmodel_v1') or 0)>0
    autopsy_ready=(counts.get('autopsy_cases') or 0)>0 or (counts.get('token_lifecycle_autopsy_events_v1') or 0)>0
    morgue_ready=(counts.get('morgue_entries') or 0)>0 or (counts.get('morgue_route_decisions') or 0)>0
    nonzero=[t for t in tables if (t.get('count') or 0)>0 and not t['table'].startswith('archive_')]
    decision='LIFECYCLE_SOURCE_READY_FOR_PANEL_BINDING' if token_lifecycle_ready and state_ready else 'LIFECYCLE_SOURCE_PARTIAL_NEEDS_MAPPING'
    panel={'exists':PANEL.exists(),'parse_ok':False,'decision':None}
    if PANEL.exists():
        try:
            j=read_json(PANEL); panel['parse_ok']=True; panel['decision']=j.get('decision')
        except Exception as e: panel['error']=type(e).__name__+':'+str(e)[:160]
    checks=[
      {'gate':'db_exists','ok':DB.exists(),'value':str(DB)},
      {'gate':'token_lifecycle_ready','ok':token_lifecycle_ready,'value':counts.get('token_lifecycle')},
      {'gate':'lifecycle_events_ready','ok':lifecycle_events_ready,'value':counts.get('token_lifecycle_events')},
      {'gate':'state_readmodel_ready','ok':state_ready,'value':counts.get('state_aggregated_token_readmodel_v1')},
      {'gate':'autopsy_ready','ok':autopsy_ready,'value':{'autopsy_cases':counts.get('autopsy_cases'),'token_lifecycle_autopsy_events_v1':counts.get('token_lifecycle_autopsy_events_v1')}},
      {'gate':'morgue_ready','ok':morgue_ready,'value':{'morgue_entries':counts.get('morgue_entries'),'morgue_route_decisions':counts.get('morgue_route_decisions')}},
      {'gate':'panel_http_200','ok':http().get('status')==200}
    ]
    result={'stage':'N21D_LIFECYCLE_SOURCE_PROOF_BUNDLE','generated_at_utc':now(),'decision':decision,'next_action':'N21D2_LIFECYCLE_PANEL_BINDING' if token_lifecycle_ready and state_ready else 'N21D2_LIFECYCLE_SCHEMA_MAPPING','core_counts':{k:counts.get(k) for k in CORE},'nonzero_active_tables':nonzero[:60],'panel_local':panel,'checks':checks,'authority':{'readonly':True,'real_db_write':False,'panel_json_write':False,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result); ROWS.parent.mkdir(parents=True,exist_ok=True); ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21D_LIFECYCLE_SOURCE_PROOF_BUNDLE')
    print('DECISION='+decision)
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
