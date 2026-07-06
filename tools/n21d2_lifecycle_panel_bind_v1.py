#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, tempfile

ROOT=Path('/root/tokenoskobi_clean_v1')
DB=ROOT/'data/tokenoskobi_clean_v1.sqlite'
PANEL=ROOT/'active_panel_8096/current/data/lifecycle_center_live_readmodel_v1.json'
OUT=ROOT/'data/control/n21d2_lifecycle_panel_bind_v1.json'
ROWS=ROOT/'data/control/n21d2_lifecycle_panel_bind_v1_rows.jsonl'

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21d2_',suffix='.json',dir=str(p.parent))
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
      'token_lifecycle':count(con,'token_lifecycle'),
      'token_lifecycle_events':count(con,'token_lifecycle_events'),
      'state_aggregated_token_readmodel_v1':count(con,'state_aggregated_token_readmodel_v1'),
      'token_lifecycle_autopsy_events_v1':count(con,'token_lifecycle_autopsy_events_v1'),
      'autopsy_cases':count(con,'autopsy_cases'),
      'autopsy_evidence_events':count(con,'autopsy_evidence_events'),
      'morgue_entries':count(con,'morgue_entries'),
      'morgue_route_decisions':count(con,'morgue_route_decisions')
    }
    con.close()
    lifecycle_ready=counts['token_lifecycle']>0 and counts['state_aggregated_token_readmodel_v1']>0
    events_ready=counts['token_lifecycle_events']>0
    autopsy_ready=counts['token_lifecycle_autopsy_events_v1']>0 or counts['autopsy_cases']>0
    morgue_ready=counts['morgue_entries']>0 or counts['morgue_route_decisions']>0
    decision='LIFECYCLE_CENTER_PRODUCTION_BOUND_AUTOPSY_MORGUE_MISSING' if lifecycle_ready else 'LIFECYCLE_CENTER_PARTIAL_BOUND'
    model={'stage':'N21D2_LIFECYCLE_PANEL_BIND','generated_at_utc':now(),'decision':decision,'data_freshness_sec':0,'authority':{'trade':False,'wallet_signing':False,'provider_call_from_browser':False,'policy_apply':False,'paper_trade_write':False},'source_count':sum(counts.values()),'items':[{'key':'lifecycle_center','label':'Token Yaşam Merkezi','status':decision,'lifecycle_ready':lifecycle_ready,'events_ready':events_ready,'autopsy_ready':autopsy_ready,'morgue_ready':morgue_ready,'counts':counts,'live_lifecycle_claim':True,'note':'Lifecycle and state readmodel are bound. Autopsy and morgue runtime sources are still missing or zero.'}]}
    awrite(PANEL,model)
    checks=[{'gate':'lifecycle_ready','ok':lifecycle_ready,'value':{'token_lifecycle':counts['token_lifecycle'],'state_aggregated_token_readmodel_v1':counts['state_aggregated_token_readmodel_v1']}},{'gate':'events_ready','ok':events_ready,'value':counts['token_lifecycle_events']},{'gate':'autopsy_missing_marked','ok':not autopsy_ready,'value':autopsy_ready},{'gate':'morgue_missing_marked','ok':not morgue_ready,'value':morgue_ready},{'gate':'panel_written','ok':PANEL.exists(),'value':str(PANEL.relative_to(ROOT))}]
    result={'stage':'N21D2_LIFECYCLE_PANEL_BIND','generated_at_utc':now(),'decision':decision,'counts':counts,'lifecycle_ready':lifecycle_ready,'events_ready':events_ready,'autopsy_ready':autopsy_ready,'morgue_ready':morgue_ready,'panel_file':str(PANEL.relative_to(ROOT)),'checks':checks,'next_action':'N21E_FULL_CENTER_POST_AUDIT','authority':{'real_db_write':False,'panel_json_write':True,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21D2_LIFECYCLE_PANEL_BIND')
    print('DECISION='+decision)
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
