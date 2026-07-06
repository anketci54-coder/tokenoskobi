#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, tempfile, urllib.request

ROOT=Path('/root/tokenoskobi_clean_v1')
DB=ROOT/'data/tokenoskobi_clean_v1.sqlite'
PANEL=ROOT/'active_panel_8096/current/data/risk_center_live_readmodel_v1.json'
OUT=ROOT/'data/control/n21c_risk_source_proof_bundle_v1.json'
ROWS=ROOT/'data/control/n21c_risk_source_proof_bundle_v1_rows.jsonl'
HINTS=['risk','rug','mev','sandwich','slippage','honeypot','guard']
CORE=['token_risk_events','mev_permission_gate_events','mev_risk_guard_events','mev_sandwich_risk_events','mev_sandwich_risk_events_v1','rug_evidence_events','slippage_estimates','high_risk_tiny_route_events']

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21c_',suffix='.json',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def http():
    try:
        r=urllib.request.urlopen('https://panel.coinoskobi.com/data/risk_center_live_readmodel_v1.json',timeout=8); b=r.read(2500)
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
    nonzero=[t for t in tables if (t.get('count') or 0)>0 and not t['table'].startswith('archive_')]
    token_risk_ready=(counts.get('token_risk_events') or 0)>0
    mev_ready=(counts.get('mev_permission_gate_events') or 0)>0 or (counts.get('mev_risk_guard_events') or 0)>0
    rug_ready=(counts.get('rug_evidence_events') or 0)>0
    slippage_ready=(counts.get('slippage_estimates') or 0)>0
    decision='RISK_SOURCE_READY_FOR_PANEL_BINDING' if token_risk_ready and mev_ready else 'RISK_SOURCE_PARTIAL_NEEDS_MAPPING'
    panel={'exists':PANEL.exists(),'parse_ok':False,'decision':None}
    if PANEL.exists():
        try:
            j=read_json(PANEL); panel['parse_ok']=True; panel['decision']=j.get('decision')
        except Exception as e: panel['error']=type(e).__name__+':'+str(e)[:160]
    checks=[
      {'gate':'db_exists','ok':DB.exists(),'value':str(DB)},
      {'gate':'token_risk_ready','ok':token_risk_ready,'value':counts.get('token_risk_events')},
      {'gate':'mev_ready','ok':mev_ready,'value':{'mev_permission_gate_events':counts.get('mev_permission_gate_events'),'mev_risk_guard_events':counts.get('mev_risk_guard_events')}},
      {'gate':'rug_ready','ok':rug_ready,'value':counts.get('rug_evidence_events')},
      {'gate':'slippage_ready','ok':slippage_ready,'value':counts.get('slippage_estimates')},
      {'gate':'panel_http_200','ok':http().get('status')==200}
    ]
    result={'stage':'N21C_RISK_SOURCE_PROOF_BUNDLE','generated_at_utc':now(),'decision':decision,'next_action':'N21C2_RISK_PANEL_BINDING' if token_risk_ready and mev_ready else 'N21C2_RISK_SCHEMA_MAPPING','core_counts':{k:counts.get(k) for k in CORE},'nonzero_active_tables':nonzero[:60],'panel_local':panel,'checks':checks,'authority':{'readonly':True,'real_db_write':False,'panel_json_write':False,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result); ROWS.parent.mkdir(parents=True,exist_ok=True); ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21C_RISK_SOURCE_PROOF_BUNDLE')
    print('DECISION='+decision)
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
