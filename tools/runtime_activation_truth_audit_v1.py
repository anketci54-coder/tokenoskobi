#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, subprocess, tempfile, urllib.request

ROOT=Path('/root/tokenoskobi_clean_v1')
DB=ROOT/'data/tokenoskobi_clean_v1.sqlite'
PANEL=ROOT/'active_panel_8096/current/data'
OUT=ROOT/'data/control/runtime_activation_truth_audit_v1.json'
ROWS=ROOT/'data/control/runtime_activation_truth_audit_v1_rows.jsonl'
PANEL_FILES={
 'news':'news_center_live_readmodel_v1.json',
 'whale':'whale_center_live_readmodel_v1.json',
 'onchain':'onchain_center_live_readmodel_v1.json',
 'risk':'risk_center_live_readmodel_v1.json',
 'lifecycle':'lifecycle_center_live_readmodel_v1.json',
 'technical':'technical_center_live_readmodel_v1.json',
 'system':'system_center_live_readmodel_v1.json',
 'command':'command_center_live_readmodel_v1.json'
}
DB_TABLES=['news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1','news_runtime_freshness_v1','known_wallet_source_registry_v1','known_wallet_seed_queue_v1','known_wallet_cex_classification_events_v1','tokens','pairs','liquidity_snapshots','token_score_100_events','token_risk_events','mev_permission_gate_events','mev_risk_guard_events','token_lifecycle','token_lifecycle_events','state_aggregated_token_readmodel_v1']
SYSTEMD_UNITS=['tokenoskobi-news-radar-refresh.service','tokenoskobi-news-radar-refresh.timer','tokenoskobi-panel-status-refresh.service','tokenoskobi-panel-status-refresh.timer']

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.runtime_truth_',suffix='.json',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def sh(cmd):
    p=subprocess.run(cmd,shell=True,text=True,capture_output=True,timeout=12)
    return {'rc':p.returncode,'stdout':p.stdout.strip()[:4000],'stderr':p.stderr.strip()[:1200]}
def table_counts():
    if not DB.exists(): return {}
    con=sqlite3.connect(str(DB)); cur=con.cursor(); out={}
    for t in DB_TABLES:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(t,))
        if cur.fetchone() is None: out[t]=None
        else:
            cur.execute(f'SELECT COUNT(*) FROM {t}'); out[t]=int(cur.fetchone()[0])
    con.close(); return out
def panel_state(name,fn):
    p=PANEL/fn
    out={'exists':p.exists(),'parse_ok':False,'decision':None,'local_file':str(p.relative_to(ROOT))}
    if p.exists():
        try:
            j=read_json(p); out['parse_ok']=True; out['decision']=j.get('decision'); out['generated_at_utc']=j.get('generated_at_utc')
        except Exception as e: out['error']=type(e).__name__+':'+str(e)[:160]
    try:
        r=urllib.request.urlopen('https://panel.coinoskobi.com/data/'+fn,timeout=8); b=r.read(5000)
        out['https']={'ok':True,'status':r.status,'bytes':len(b)}
    except Exception as e: out['https']={'ok':False,'status':None,'error':type(e).__name__+':'+str(e)[:160]}
    return out
def systemd_state():
    out={}
    for u in SYSTEMD_UNITS:
        out[u]={
          'is_active':sh('systemctl is-active '+u+' || true'),
          'is_enabled':sh('systemctl is-enabled '+u+' || true'),
          'show':sh('systemctl show '+u+' -p ActiveState -p SubState -p Result -p ExecMainStatus -p NRestarts -p FragmentPath -p UnitFileState || true')
        }
    return out
def news_latest():
    if not DB.exists(): return {}
    con=sqlite3.connect(str(DB)); cur=con.cursor(); out={}
    for t in ['news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1','news_runtime_freshness_v1']:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(t,))
        if cur.fetchone() is None:
            out[t]=None; continue
        cur.execute(f'PRAGMA table_info({t})')
        cols=[r[1] for r in cur.fetchall()]
        ts=[c for c in cols if c in ['created_at_utc','event_time_utc','generated_at_utc','last_updated_utc','last_seen_at_utc']]
        if ts:
            col=ts[0]
            try:
                cur.execute(f'SELECT MAX({col}) FROM {t}')
                out[t]={'timestamp_col':col,'max_ts':cur.fetchone()[0]}
            except Exception as e: out[t]={'error':type(e).__name__+':'+str(e)[:120]}
        else: out[t]={'timestamp_col':None,'max_ts':None}
    con.close(); return out

def main():
    counts=table_counts()
    panels={k:panel_state(k,v) for k,v in PANEL_FILES.items()}
    systemd=systemd_state()
    latest=news_latest()
    checks=[]
    checks.append({'gate':'news_db_chain_nonzero','ok':all((counts.get(t) or 0)>0 for t in ['news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1']),'value':{t:counts.get(t) for t in ['news_raw_feed_events','news_token_match_events','news_signal_events','news_score_events_v1']}})
    checks.append({'gate':'news_timer_active','ok':systemd['tokenoskobi-news-radar-refresh.timer']['is_active']['stdout']=='active','value':systemd['tokenoskobi-news-radar-refresh.timer']['is_active']['stdout']})
    checks.append({'gate':'panel_all_https_200','ok':all(p['https'].get('status')==200 for p in panels.values()),'value':{k:v['https'].get('status') for k,v in panels.items()}})
    checks.append({'gate':'command_display_only','ok':'DISPLAY_ONLY' in str(panels['command'].get('decision')),'value':panels['command'].get('decision')})
    checks.append({'gate':'non_news_runtime_declared_readmodel_bound','ok':True,'value':'whale/onchain/risk/lifecycle currently DB-readmodel/panel-bound; continuous producer runtime not proven by systemd in this audit'})
    fail=[c for c in checks if not c.get('ok')]
    decision='RUNTIME_ACTIVATION_TRUTH_AUDIT_PASS' if not fail else 'RUNTIME_ACTIVATION_TRUTH_AUDIT_REVIEW'
    result={'stage':'RUNTIME_ACTIVATION_TRUTH_AUDIT_V1','generated_at_utc':now(),'decision':decision,'fail_count':len(fail),'db_counts':counts,'news_latest':latest,'panels':panels,'systemd':systemd,'checks':checks,'next_action':'REVIEW_RUNTIME_GAPS_AND_DECIDE_CONTINUOUS_PRODUCERS','authority':{'readonly':True,'real_db_write':False,'panel_json_write':False,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_RUNTIME_ACTIVATION_TRUTH_AUDIT_V1')
    print('DECISION='+decision)
    print('FAIL_COUNT='+str(len(fail)))
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
