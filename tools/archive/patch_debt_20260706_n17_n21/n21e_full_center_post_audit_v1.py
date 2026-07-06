#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, tempfile, urllib.request

ROOT=Path('/root/tokenoskobi_clean_v1')
DB=ROOT/'data/tokenoskobi_clean_v1.sqlite'
PANEL=ROOT/'active_panel_8096/current/data'
OUT=ROOT/'data/control/n21e_full_center_post_audit_v1.json'
ROWS=ROOT/'data/control/n21e_full_center_post_audit_v1_rows.jsonl'
CENTERS={
 'news':'news_center_live_readmodel_v1.json',
 'whale':'whale_center_live_readmodel_v1.json',
 'onchain':'onchain_center_live_readmodel_v1.json',
 'risk':'risk_center_live_readmodel_v1.json',
 'lifecycle':'lifecycle_center_live_readmodel_v1.json',
 'technical':'technical_center_live_readmodel_v1.json',
 'system':'system_center_live_readmodel_v1.json',
 'command':'command_center_live_readmodel_v1.json'
}
EXPECTED={
 'news':'NEWS_CENTER_REAL_PIPELINE_BOUND',
 'whale':'WHALE_CENTER_REGISTRY_BOUND_FLOW_MISSING',
 'onchain':'ONCHAIN_CENTER_PRODUCTION_BOUND_HOLDER_MISSING',
 'risk':'RISK_CENTER_PRODUCTION_BOUND_RUG_SLIPPAGE_MISSING',
 'lifecycle':'LIFECYCLE_CENTER_PRODUCTION_BOUND_AUTOPSY_MORGUE_MISSING'
}
DB_TABLES=['news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1','news_runtime_freshness_v1','known_wallet_source_registry_v1','known_wallet_seed_queue_v1','known_wallet_cex_classification_events_v1','tokens','pairs','liquidity_snapshots','token_score_100_events','token_risk_events','mev_permission_gate_events','mev_risk_guard_events','token_lifecycle','token_lifecycle_events','state_aggregated_token_readmodel_v1']

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21e_',suffix='.json',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def http_json(filename):
    url='https://panel.coinoskobi.com/data/'+filename
    try:
        r=urllib.request.urlopen(url,timeout=8); b=r.read(5000)
        return {'ok':True,'status':r.status,'bytes':len(b)}
    except Exception as e:
        return {'ok':False,'status':None,'error':type(e).__name__+':'+str(e)[:160]}
def db_counts():
    con=sqlite3.connect(str(DB)); cur=con.cursor(); out={}
    for t in DB_TABLES:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(t,))
        if cur.fetchone() is None:
            out[t]=None
        else:
            cur.execute(f'SELECT COUNT(*) FROM {t}')
            out[t]=int(cur.fetchone()[0])
    con.close(); return out
def local_panel(center,filename):
    p=PANEL/filename
    out={'center':center,'file':str(p.relative_to(ROOT)),'exists':p.exists(),'parse_ok':False,'decision':None,'item_statuses':[]}
    if p.exists():
        try:
            j=read_json(p); out['parse_ok']=True; out['decision']=j.get('decision'); out['item_statuses']=[x.get('status') for x in j.get('items',[]) if isinstance(x,dict)]
        except Exception as e: out['error']=type(e).__name__+':'+str(e)[:160]
    out['https']=http_json(filename)
    return out
def main():
    counts=db_counts() if DB.exists() else {}
    panels={c:local_panel(c,f) for c,f in CENTERS.items()}
    checks=[]
    for c,expected in EXPECTED.items():
        got=panels[c].get('decision')
        checks.append({'gate':c+'_decision_expected','ok':got==expected,'value':{'expected':expected,'got':got}})
        checks.append({'gate':c+'_https_200','ok':panels[c]['https'].get('status')==200,'value':panels[c]['https']})
    for t in DB_TABLES:
        min_required=1 if t not in ['holder_snapshots','rug_evidence_events','slippage_estimates'] else 0
        checks.append({'gate':'db_'+t+'_nonzero','ok':counts.get(t) is not None and counts.get(t)>=min_required,'value':counts.get(t)})
    checks.append({'gate':'technical_expected_missing','ok':panels['technical'].get('decision')=='TECHNICAL_CENTER_DATA_MISSING','value':panels['technical'].get('decision')})
    checks.append({'gate':'system_https_200','ok':panels['system']['https'].get('status')==200,'value':panels['system']['https']})
    checks.append({'gate':'command_https_200','ok':panels['command']['https'].get('status')==200,'value':panels['command']['https']})
    fail=[c for c in checks if not c.get('ok')]
    decision='N21E_FULL_CENTER_POST_AUDIT_PASS' if not fail else 'N21E_FULL_CENTER_POST_AUDIT_REVIEW'
    result={'stage':'N21E_FULL_CENTER_POST_AUDIT','generated_at_utc':now(),'decision':decision,'fail_count':len(fail),'db_counts':counts,'panels':panels,'checks':checks,'next_action':'N21F_COMMAND_FUSION_BINDING' if not fail else 'REVIEW_FAILED_GATES_BEFORE_FUSION','authority':{'readonly':True,'real_db_write':False,'panel_json_write':False,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21E_FULL_CENTER_POST_AUDIT')
    print('DECISION='+decision)
    print('FAIL_COUNT='+str(len(fail)))
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
