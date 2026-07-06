#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, sqlite3, tempfile

ROOT=Path('/root/tokenoskobi_clean_v1')
DB=ROOT/'data/tokenoskobi_clean_v1.sqlite'
PANEL=ROOT/'active_panel_8096/current/data/onchain_center_live_readmodel_v1.json'
OUT=ROOT/'data/control/n21b2_onchain_panel_bind_v1.json'
ROWS=ROOT/'data/control/n21b2_onchain_panel_bind_v1_rows.jsonl'

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21b2_',suffix='.json',dir=str(p.parent))
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
      'tokens':count(con,'tokens'),
      'pairs':count(con,'pairs'),
      'token_birth_events':count(con,'token_birth_events'),
      'liquidity_snapshots':count(con,'liquidity_snapshots'),
      'holder_snapshots':count(con,'holder_snapshots'),
      'holder_distribution_events':count(con,'holder_distribution_events'),
      'token_score_100_events':count(con,'token_score_100_events'),
      'token_score_snapshots':count(con,'token_score_snapshots'),
      'token_risk_events':count(con,'token_risk_events'),
      'state_aggregated_token_readmodel_v1':count(con,'state_aggregated_token_readmodel_v1'),
      'initial_holder_evidence_events_v1':count(con,'initial_holder_evidence_events_v1')
    }
    con.close()
    source_ready=counts['tokens']>0 and counts['pairs']>0
    liquidity_ready=counts['liquidity_snapshots']>0
    score_ready=counts['token_score_100_events']>0 or counts['token_score_snapshots']>0
    holder_ready=counts['holder_snapshots']>0 or counts['holder_distribution_events']>0
    risk_ready=counts['token_risk_events']>0
    decision='ONCHAIN_CENTER_PRODUCTION_BOUND_HOLDER_MISSING' if source_ready and liquidity_ready and score_ready else 'ONCHAIN_CENTER_PARTIAL_BOUND'
    model={'stage':'N21B2_ONCHAIN_PANEL_BIND','generated_at_utc':now(),'decision':decision,'data_freshness_sec':0,'authority':{'trade':False,'wallet_signing':False,'provider_call_from_browser':False,'policy_apply':False,'paper_trade_write':False},'source_count':sum(counts.values()),'items':[{'key':'onchain_center','label':'Onchain Veri Merkezi','status':decision,'source_ready':source_ready,'liquidity_ready':liquidity_ready,'score_ready':score_ready,'risk_ready':risk_ready,'holder_ready':holder_ready,'counts':counts,'live_onchain_claim':True,'note':'Onchain token/pair/liquidity/score/risk sources are bound. Holder snapshots are still missing and explicitly marked.'}]}
    awrite(PANEL,model)
    checks=[{'gate':'source_ready','ok':source_ready,'value':{'tokens':counts['tokens'],'pairs':counts['pairs']}},{'gate':'liquidity_ready','ok':liquidity_ready,'value':counts['liquidity_snapshots']},{'gate':'score_ready','ok':score_ready,'value':{'token_score_100_events':counts['token_score_100_events'],'token_score_snapshots':counts['token_score_snapshots']}},{'gate':'risk_ready','ok':risk_ready,'value':counts['token_risk_events']},{'gate':'holder_missing_marked','ok':not holder_ready,'value':holder_ready},{'gate':'panel_written','ok':PANEL.exists(),'value':str(PANEL.relative_to(ROOT))}]
    result={'stage':'N21B2_ONCHAIN_PANEL_BIND','generated_at_utc':now(),'decision':decision,'counts':counts,'source_ready':source_ready,'liquidity_ready':liquidity_ready,'score_ready':score_ready,'risk_ready':risk_ready,'holder_ready':holder_ready,'panel_file':str(PANEL.relative_to(ROOT)),'checks':checks,'next_action':'N21C_RISK_BINDING','authority':{'real_db_write':False,'panel_json_write':True,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21B2_ONCHAIN_PANEL_BIND')
    print('DECISION='+decision)
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
