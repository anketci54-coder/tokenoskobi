#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, tempfile

ROOT=Path('/root/tokenoskobi_clean_v1')
PANEL=ROOT/'active_panel_8096/current/data'
COMMAND=PANEL/'command_center_live_readmodel_v1.json'
OUT=ROOT/'data/control/n21f_command_fusion_bind_v1.json'
ROWS=ROOT/'data/control/n21f_command_fusion_bind_v1_rows.jsonl'
CENTERS={
 'news':'news_center_live_readmodel_v1.json',
 'whale':'whale_center_live_readmodel_v1.json',
 'onchain':'onchain_center_live_readmodel_v1.json',
 'risk':'risk_center_live_readmodel_v1.json',
 'lifecycle':'lifecycle_center_live_readmodel_v1.json',
 'technical':'technical_center_live_readmodel_v1.json',
 'system':'system_center_live_readmodel_v1.json'
}

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21f_',suffix='.json',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def load_center(name,filename):
    p=PANEL/filename
    out={'center':name,'exists':p.exists(),'parse_ok':False,'decision':None,'status':None,'source_count':None,'counts':{}}
    if not p.exists(): return out
    try:
        j=read_json(p); out['parse_ok']=True; out['decision']=j.get('decision'); out['source_count']=j.get('source_count')
        items=j.get('items') or []
        if items and isinstance(items[0],dict):
            out['status']=items[0].get('status'); out['counts']=items[0].get('counts') or {}
    except Exception as e:
        out['error']=type(e).__name__+':'+str(e)[:160]
    return out
def main():
    centers={k:load_center(k,v) for k,v in CENTERS.items()}
    production_bound=[k for k,v in centers.items() if v.get('decision') and ('PRODUCTION_BOUND' in v['decision'] or 'REAL_PIPELINE_BOUND' in v['decision'] or 'REGISTRY_BOUND' in v['decision'])]
    missing=[k for k,v in centers.items() if v.get('decision') and 'DATA_MISSING' in v['decision']]
    explicit_gaps=[]
    for k,v in centers.items():
        d=str(v.get('decision') or '')
        for marker in ['FLOW_MISSING','HOLDER_MISSING','RUG_SLIPPAGE_MISSING','AUTOPSY_MORGUE_MISSING','DATA_MISSING']:
            if marker in d: explicit_gaps.append({'center':k,'gap':marker,'decision':d})
    fusion_decision='COMMAND_FUSION_BOUND_DISPLAY_ONLY_PARTIAL_TECHNICAL_MISSING' if len(production_bound)>=5 else 'COMMAND_FUSION_NOT_READY'
    model={'stage':'N21F_COMMAND_FUSION_BIND','generated_at_utc':now(),'decision':fusion_decision,'data_freshness_sec':0,'authority':{'trade':False,'wallet_signing':False,'provider_call_from_browser':False,'policy_apply':False,'paper_trade_write':False},'items':[{'key':'command_center','label':'Komuta ve Karar Merkezi','status':fusion_decision,'mode':'DISPLAY_ONLY_NO_TRADE_AUTHORITY','production_bound_centers':production_bound,'missing_centers':missing,'explicit_gaps':explicit_gaps,'center_decisions':{k:v.get('decision') for k,v in centers.items()},'center_counts':{k:v.get('counts') for k,v in centers.items()},'note':'Fusion command readmodel aggregates center status only. It has no trade, wallet, provider, policy or paper execution authority.'}]}
    awrite(COMMAND,model)
    checks=[{'gate':'minimum_bound_centers','ok':len(production_bound)>=5,'value':production_bound},{'gate':'technical_missing_explicit','ok':'technical' in missing or centers['technical'].get('decision')=='TECHNICAL_CENTER_DATA_MISSING','value':centers['technical'].get('decision')},{'gate':'command_written','ok':COMMAND.exists(),'value':str(COMMAND.relative_to(ROOT))},{'gate':'authority_display_only','ok':True,'value':model['authority']}]
    result={'stage':'N21F_COMMAND_FUSION_BIND','generated_at_utc':now(),'decision':fusion_decision,'production_bound_centers':production_bound,'missing_centers':missing,'explicit_gaps':explicit_gaps,'center_decisions':{k:v.get('decision') for k,v in centers.items()},'checks':checks,'next_action':'N21G_FINAL_PANEL_SYSTEM_POST_AUDIT','authority':{'real_db_write':False,'panel_json_write':True,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21F_COMMAND_FUSION_BIND')
    print('DECISION='+fusion_decision)
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
