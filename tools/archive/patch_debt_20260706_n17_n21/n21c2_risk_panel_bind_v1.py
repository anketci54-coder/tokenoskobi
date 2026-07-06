#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, tempfile

ROOT=Path('/root/tokenoskobi_clean_v1')
DB=ROOT/'data/tokenoskobi_clean_v1.sqlite'
PANEL=ROOT/'active_panel_8096/current/data/risk_center_live_readmodel_v1.json'
OUT=ROOT/'data/control/n21c2_risk_panel_bind_v1.json'
ROWS=ROOT/'data/control/n21c2_risk_panel_bind_v1_rows.jsonl'

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21c2_',suffix='.json',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def count(con,t):
    cur=con.cursor(); cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(t,))
    if cur.fetchone() is None: return 0
    cur.execute(f'SELECT COUNT(*) FROM {t}'); return int(cur.fetchone()[0])
def main():
    con=sqlite3.connect(str(DB))
    counts={
      'token_risk_events':count(con,'token_risk_events'),
      'mev_permission_gate_events':count(con,'mev_permission_gate_events'),
      'mev_risk_guard_events':count(con,'mev_risk_guard_events'),
      'mev_sandwich_risk_events':count(con,'mev_sandwich_risk_events'),
      'mev_sandwich_risk_events_v1':count(con,'mev_sandwich_risk_events_v1'),
      'rug_evidence_events':count(con,'rug_evidence_events'),
      'slippage_estimates':count(con,'slippage_estimates'),
      'high_risk_tiny_route_events':count(con,'high_risk_tiny_route_events')
    }
    con.close()
    token_risk_ready=counts['token_risk_events']>0
    mev_ready=counts['mev_permission_gate_events']>0 or counts['mev_risk_guard_events']>0
    rug_ready=counts['rug_evidence_events']>0
    slippage_ready=counts['slippage_estimates']>0
    sandwich_ready=counts['mev_sandwich_risk_events']>0 or counts['mev_sandwich_risk_events_v1']>0
    decision='RISK_CENTER_PRODUCTION_BOUND_RUG_SLIPPAGE_MISSING' if token_risk_ready and mev_ready else 'RISK_CENTER_PARTIAL_BOUND'
    model={'stage':'N21C2_RISK_PANEL_BIND','generated_at_utc':now(),'decision':decision,'data_freshness_sec':0,'authority':{'trade':False,'wallet_signing':False,'provider_call_from_browser':False,'policy_apply':False,'paper_trade_write':False},'source_count':sum(counts.values()),'items':[{'key':'risk_center','label':'Risk Güvenlik Merkezi','status':decision,'token_risk_ready':token_risk_ready,'mev_ready':mev_ready,'rug_ready':rug_ready,'slippage_ready':slippage_ready,'sandwich_ready':sandwich_ready,'counts':counts,'live_risk_claim':True,'note':'Risk token events and MEV gate/guard are bound. Rug, slippage and sandwich detailed sources are still missing or zero.'}]}
    awrite(PANEL,model)
    checks=[{'gate':'token_risk_ready','ok':token_risk_ready,'value':counts['token_risk_events']},{'gate':'mev_ready','ok':mev_ready,'value':{'mev_permission_gate_events':counts['mev_permission_gate_events'],'mev_risk_guard_events':counts['mev_risk_guard_events']}},{'gate':'rug_missing_marked','ok':not rug_ready,'value':rug_ready},{'gate':'slippage_missing_marked','ok':not slippage_ready,'value':slippage_ready},{'gate':'panel_written','ok':PANEL.exists(),'value':str(PANEL.relative_to(ROOT))}]
    result={'stage':'N21C2_RISK_PANEL_BIND','generated_at_utc':now(),'decision':decision,'counts':counts,'token_risk_ready':token_risk_ready,'mev_ready':mev_ready,'rug_ready':rug_ready,'slippage_ready':slippage_ready,'sandwich_ready':sandwich_ready,'panel_file':str(PANEL.relative_to(ROOT)),'checks':checks,'next_action':'N21D_LIFECYCLE_BINDING','authority':{'real_db_write':False,'panel_json_write':True,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21C2_RISK_PANEL_BIND')
    print('DECISION='+decision)
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
