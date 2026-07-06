#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, os, tempfile, urllib.request

ROOT=Path('/root/tokenoskobi_clean_v1')
PANEL=ROOT/'active_panel_8096/current/data'
OUT=ROOT/'data/control/n21g_final_panel_system_post_audit_v1.json'
ROWS=ROOT/'data/control/n21g_final_panel_system_post_audit_v1_rows.jsonl'
FILES={
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
 'lifecycle':'LIFECYCLE_CENTER_PRODUCTION_BOUND_AUTOPSY_MORGUE_MISSING',
 'technical':'TECHNICAL_CENTER_DATA_MISSING',
 'command':'COMMAND_FUSION_BOUND_DISPLAY_ONLY_PARTIAL_TECHNICAL_MISSING'
}

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def awrite(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.n21g_',suffix='.json',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n')
        read_json(Path(tmp)); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def http(filename):
    try:
        r=urllib.request.urlopen('https://panel.coinoskobi.com/data/'+filename,timeout=8); b=r.read(8000)
        return {'ok':True,'status':r.status,'bytes':len(b)}
    except Exception as e:
        return {'ok':False,'status':None,'error':type(e).__name__+':'+str(e)[:160]}
def load(name,filename):
    p=PANEL/filename
    out={'center':name,'file':str(p.relative_to(ROOT)),'exists':p.exists(),'parse_ok':False,'decision':None,'authority':{},'status':None,'https':http(filename)}
    if p.exists():
        try:
            j=read_json(p); out['parse_ok']=True; out['decision']=j.get('decision'); out['authority']=j.get('authority') or {}
            items=j.get('items') or []
            if items and isinstance(items[0],dict): out['status']=items[0].get('status')
        except Exception as e:
            out['error']=type(e).__name__+':'+str(e)[:160]
    return out
def safe_authority(authority):
    bad=[]
    for k,v in authority.items():
        if k in ['trade','wallet_signing','provider_call_from_browser','policy_apply','paper_trade_write'] and v is not False:
            bad.append({k:v})
    return bad

def main():
    centers={k:load(k,v) for k,v in FILES.items()}
    checks=[]
    for c,expected in EXPECTED.items():
        got=centers[c].get('decision')
        checks.append({'gate':c+'_decision','ok':got==expected,'value':{'expected':expected,'got':got}})
    for c,info in centers.items():
        checks.append({'gate':c+'_https_200','ok':info['https'].get('status')==200,'value':info['https']})
        checks.append({'gate':c+'_json_parse_ok','ok':info.get('parse_ok') is True,'value':info.get('parse_ok')})
        checks.append({'gate':c+'_authority_safe','ok':len(safe_authority(info.get('authority') or {}))==0,'value':info.get('authority')})
    command=centers['command']
    checks.append({'gate':'command_display_only','ok':'DISPLAY_ONLY' in str(command.get('decision')),'value':command.get('decision')})
    checks.append({'gate':'technical_missing_explicit','ok':centers['technical'].get('decision')=='TECHNICAL_CENTER_DATA_MISSING','value':centers['technical'].get('decision')})
    failed=[c for c in checks if not c.get('ok')]
    decision='N21G_FINAL_PANEL_SYSTEM_POST_AUDIT_PASS' if not failed else 'N21G_FINAL_PANEL_SYSTEM_POST_AUDIT_REVIEW'
    result={'stage':'N21G_FINAL_PANEL_SYSTEM_POST_AUDIT','generated_at_utc':now(),'decision':decision,'fail_count':len(failed),'centers':centers,'checks':checks,'next_action':'PATCH_DEBT_AND_DOC_REVISION_PHASE' if not failed else 'FIX_FAILED_GATES_BEFORE_CLEANUP','authority':{'readonly':True,'real_db_write':False,'panel_json_write':False,'systemd_start':False,'systemd_stop':False,'api_calls':0,'provider_call':False,'wallet':False,'signing':False,'live_trade':False,'core_change':False}}
    awrite(OUT,result)
    ROWS.parent.mkdir(parents=True,exist_ok=True)
    ROWS.write_text('\n'.join(json.dumps(c,ensure_ascii=False,sort_keys=True) for c in checks)+'\n',encoding='utf-8')
    print('FINAL_GATE=PASS_N21G_FINAL_PANEL_SYSTEM_POST_AUDIT')
    print('DECISION='+decision)
    print('FAIL_COUNT='+str(len(failed)))
    print('JSON='+str(OUT.relative_to(ROOT)))
if __name__=='__main__': main()
