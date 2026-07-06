#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, tempfile, urllib.request

ROOT = Path('/root/tokenoskobi_clean_v1')
DB = ROOT / 'data/tokenoskobi_clean_v1.sqlite'
PANEL = ROOT / 'active_panel_8096/current/data'
WHALE_PANEL = PANEL / 'whale_center_live_readmodel_v1.json'
OUT = ROOT / 'data/control/n21a_whale_source_proof_bundle_v1.json'
ROWS = ROOT / 'data/control/n21a_whale_source_proof_bundle_v1_rows.jsonl'
WHALE_HINTS = ['whale','wallet','entity','transfer','cex','flow','known_wallet','balance','cluster','reputation']

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p, encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21a_', suffix='.json', dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def http(path):
    url='https://panel.coinoskobi.com/data/'+path
    try:
        r=urllib.request.urlopen(url,timeout=8); b=r.read(2500)
        return {'url':url,'ok':True,'status':r.status,'bytes':len(b)}
    except Exception as e:
        return {'url':url,'ok':False,'status':None,'error':type(e).__name__+':'+str(e)[:180]}
def table_inventory():
    con=sqlite3.connect(str(DB)); cur=con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    rows=[]
    for (name,) in cur.fetchall():
        if not any(h in name.lower() for h in WHALE_HINTS):
            continue
        try:
            cur.execute(f'SELECT COUNT(*) FROM {name}')
            cnt=int(cur.fetchone()[0])
        except Exception:
            cnt=None
        cur.execute(f'PRAGMA table_info({name})')
        cols=[r[1] for r in cur.fetchall()]
        sample=[]
        if cnt and cnt>0:
            try:
                sel=','.join(cols[:6])
                cur.execute(f'SELECT {sel} FROM {name} LIMIT 5')
                sample=[{cols[i]:row[i] for i in range(len(cols[:6]))} for row in cur.fetchall()]
            except Exception as e:
                sample=[{'sample_error':type(e).__name__+':'+str(e)[:120]}]
        rows.append({'table':name,'count':cnt,'columns':cols,'sample':sample})
    con.close(); return rows
def classify_tables(tables):
    nonzero=[t for t in tables if (t.get('count') or 0)>0]
    active=[t for t in nonzero if not t['table'].startswith('archive_')]
    registry=[t for t in active if 'registry' in t['table'] or 'known_wallet' in t['table'] or 'entity' in t['table']]
    flow=[t for t in active if 'flow' in t['table'] or 'transfer' in t['table'] or 'balance' in t['table']]
    quality=[t for t in active if 'quality' in t['table'] or 'classification' in t['table'] or 'reputation' in t['table']]
    return {'nonzero':nonzero,'active':active,'registry':registry,'flow':flow,'quality':quality}
def main():
    tables=table_inventory() if DB.exists() else []
    cls=classify_tables(tables)
    panel_local={'exists':WHALE_PANEL.exists(),'parse_ok':False,'decision':None,'items_status':[]}
    if WHALE_PANEL.exists():
        try:
            j=read_json(WHALE_PANEL); panel_local['parse_ok']=True; panel_local['decision']=j.get('decision'); panel_local['items_status']=[x.get('status') for x in j.get('items',[]) if isinstance(x,dict)]
        except Exception as e:
            panel_local['error']=type(e).__name__+':'+str(e)[:160]
    checks=[
        {'gate':'db_exists','ok':DB.exists(),'value':str(DB)},
        {'gate':'whale_tables_found','ok':len(tables)>0,'value':len(tables)},
        {'gate':'active_nonzero_whale_tables','ok':len(cls['active'])>0,'value':[t['table'] for t in cls['active']]},
        {'gate':'registry_source_nonzero','ok':len(cls['registry'])>0,'value':[t['table'] for t in cls['registry']]},
        {'gate':'flow_source_nonzero','ok':len(cls['flow'])>0,'value':[t['table'] for t in cls['flow']]},
        {'gate':'panel_whale_json_200','ok':http('whale_center_live_readmodel_v1.json').get('status')==200},
    ]
    if len(cls['registry'])>0 and len(cls['flow'])>0:
        decision='WHALE_SOURCE_READY_FOR_PRODUCTION_BINDING'
        next_action='N21A2_BUILD_WHALE_PANEL_READMODEL_FROM_ACTIVE_SOURCES'
    elif len(cls['registry'])>0:
        decision='WHALE_REGISTRY_READY_FLOW_SOURCE_MISSING'
        next_action='N21A2_BIND_REGISTRY_ONLY_AND_MARK_FLOW_MISSING'
    elif len(cls['active'])>0:
        decision='WHALE_ACTIVE_SOURCE_PARTIAL_REQUIRES_SCHEMA_MAPPING'
        next_action='N21A2_SCHEMA_MAP_ACTIVE_WHALE_TABLES'
    else:
        decision='WHALE_SOURCE_NOT_READY'
        next_action='KEEP_WHALE_DATA_MISSING'
    result={'stage':'N21A_WHALE_SOURCE_PROOF_BUNDLE','generated_at_utc':now(),'decision':decision,'next_action':next_action,'tables_found':len(tables),'active_nonzero_count':len(cls['active']),'registry_count':len(cls['registry']),'flow_count':len(cls['flow']),'quality_count':len(cls['quality']),'active_tables':cls['active'],'registry_tables':cls['registry'],'flow_tables':cls['flow'],'quality_tables':cls['quality'],'panel_local':panel_local,'checks':checks,'authority':{'readonly':True,'real_db_write':False,'tempdb_write':False,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21A_WHALE_SOURCE_PROOF_BUNDLE')
    print('DECISION='+decision)
    print('NEXT_ACTION='+next_action)
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
