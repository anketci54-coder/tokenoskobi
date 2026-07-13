#!/usr/bin/env python3
from __future__ import annotations

import json, os, re, shlex, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
SERVICE='tokenoskobi-news-radar-refresh.service'
WORK='PRE_ERA57_LIVE_RAW_RUNNER_RESOLUTION_AND_RUNTIME_ENTRY_DECISION'
TAG55='ERA55_FINAL_SEAL';SEAL55='f22ce4f07788ec7fbe22a72f872467705b72db5a'
TAG56='ERA56_FINAL_SEAL';SEAL56='39dd684a71e39c4f05ce2a5113985fcf647718a0'
RUNTIME=ROOT/'PROJECT_RUNTIME.json';HISTORY=ROOT/'PROJECT_HISTORY.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md';HANDOFF=ROOT/'07_PROJECT_HANDOFF.md'
ARTIFACT=ROOT/'data/control/pre_era57_live_raw_runner_resolution_and_runtime_entry_decision_v1.json'
ORDER_DEFAULT=Path('/run/tokenoskobi/era55a23_guarded_order.log')


def run(args:list[str],check:bool=True,timeout:int=90):
    return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check,timeout=timeout)
def git(*args:str)->str:return run(['git',*args]).stdout.strip()
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(v,dict):raise RuntimeError('JSON_OBJECT_REQUIRED:'+str(p))
    return v
def dump(p:Path,v:dict[str,Any]):
    p.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=p.name+'.',dir=p.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as h:json.dump(v,h,ensure_ascii=False,indent=2,sort_keys=True);h.write('\n');h.flush();os.fsync(h.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def section(text:str,heading:str,body:str)->str:
    s=text.find(heading)
    if s<0:raise RuntimeError('HEADING_MISSING:'+heading)
    e=text.find('\n## ',s+len(heading));e=len(text) if e<0 else e
    return text[:s]+heading+'\n\n'+body.rstrip()+'\n'+text[e:]
def parse_env(raw:str)->dict[str,str]:
    out={}
    for token in shlex.split(raw):
        if '=' in token:
            k,v=token.split('=',1);out[k]=v
    return out
def default_original(wrapper:Path)->Path|None:
    if not wrapper.is_file():return None
    text=wrapper.read_text(encoding='utf-8',errors='replace')
    m=re.search(r'news_radar_refresh_runner_v1\.PRE_DERIVED_BINDING_[A-Za-z0-9_]+\.py',text)
    return (wrapper.parent/m.group(0)).resolve() if m else None
def tail_text(path:Path,max_bytes:int=512_000)->str:
    if not path.is_file():return ''
    with path.open('rb') as h:
        h.seek(0,2);size=h.tell();h.seek(max(0,size-max_bytes));return h.read().decode('utf-8','replace')


def main()->int:
    if git('status','--short'):raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected:raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list','-n1',TAG55)!=SEAL55:raise RuntimeError('ERA55_SEAL_MISMATCH')
    if git('rev-list','-n1',TAG56)!=SEAL56:raise RuntimeError('ERA56_SEAL_MISMATCH')

    rt=load(RUNTIME);p=rt['canonical_runtime_pointer']
    if p.get('era57_opened') is not False:raise RuntimeError('ERA57_MUST_REMAIN_CLOSED')
    if p.get('next_safe_step')!=WORK:raise RuntimeError('NEXT_STEP_MISMATCH')

    props=['Environment','ExecStart','ActiveState','SubState','Result','InvocationID','FragmentPath']
    show={}
    for prop in props:
        r=run(['systemctl','show',SERVICE,'-p',prop,'--value'],check=False)
        show[prop]=r.stdout.strip() if r.returncode==0 else ''
    cat=run(['systemctl','cat',SERVICE],check=False).stdout
    env=parse_env(show['Environment'])

    exec_match=re.search(r'(/root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1\.py)',show['ExecStart'])
    wrapper=Path(exec_match.group(1)).resolve() if exec_match else ROOT/'tools/news_radar_refresh_runner_v1.py'
    configured=env.get('TOKENOSKOBI_NEWS_ORIGINAL_PATH','').strip()
    default=default_original(wrapper)
    resolved=Path(configured).resolve() if configured else default
    resolved_exists=bool(resolved and resolved.is_file())
    resolved_readable=bool(resolved_exists and os.access(resolved,os.R_OK))

    order_path=Path(env.get('TOKENOSKOBI_A10_ORDER_LOG',str(ORDER_DEFAULT)))
    evidence=tail_text(order_path)
    raw_end_codes=[int(x) for x in re.findall(r'RAW_END:(\d+)',evidence)]
    last_raw_code=raw_end_codes[-1] if raw_end_codes else None
    natural_cycle_ok=last_raw_code==0
    wrapper_exists=wrapper.is_file() and os.access(wrapper,os.R_OK)
    service_known=bool(show['FragmentPath'] and Path(show['FragmentPath']).exists())

    candidates=[]
    for candidate in sorted((ROOT/'tools').glob('*news*runner*.py')):
        if candidate.resolve()!=wrapper.resolve() and candidate.is_file():
            candidates.append(str(candidate.resolve()))

    if resolved_readable and natural_cycle_ok and wrapper_exists and service_known:
        decision='AUTHORIZE_ERA57_OPENING_DECISION'
        nxt='ERA57_AUTONOMOUS_RESEARCH_LAYER_OPENING_DECISION'
        result='OK_RAW_RUNNER_RESOLVED_NATURAL_CYCLE_VERIFIED'
    elif resolved_readable and wrapper_exists and service_known:
        decision='DEFER_FOR_ONE_NATURAL_CYCLE_OBSERVATION'
        nxt='PRE_ERA57_RAW_RUNNER_NATURAL_CYCLE_OBSERVATION_DECISION'
        result='WARN_RAW_RUNNER_RESOLVED_NATURAL_CYCLE_NOT_VERIFIED'
    else:
        decision='AUTHORIZE_BOUNDED_RAW_PATH_REPAIR_REVIEW'
        nxt='PRE_ERA57_RAW_RUNNER_BOUNDED_PATH_REPAIR_DECISION'
        result='WARN_RAW_RUNNER_UNRESOLVED_REPAIR_REVIEW_REQUIRED'

    ts=datetime.now(timezone.utc).isoformat();rel=str(ARTIFACT.relative_to(ROOT))
    data={'schema':'pre_era57_live_raw_runner_resolution_and_runtime_entry_decision_v1','timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_VERIFIED','result':result,'decision':decision,'service':SERVICE,'systemd':show,'service_unit_text_sha256':__import__('hashlib').sha256(cat.encode()).hexdigest(),'environment':env,'wrapper_path':str(wrapper),'wrapper_exists':wrapper_exists,'configured_raw_path':configured or None,'default_raw_path':str(default) if default else None,'resolved_raw_path':str(resolved) if resolved else None,'raw_runner_resolved':resolved_readable,'raw_runner_exists':resolved_exists,'raw_runner_readable':resolved_readable,'order_log_path':str(order_path),'last_raw_exit_code':last_raw_code,'natural_cycle_raw_ok':natural_cycle_ok,'candidate_runner_paths':candidates,'era57_opened':False,'production_mutation':False,'next_safe_step':nxt}
    dump(ARTIFACT,data)

    p.update({'current_stage':'PRE_ERA57_RAW_RUNNER_RESOLUTION_DECIDED','last_completed':WORK,'last_result':result,'last_artifact':rel,'pre_era57_raw_runner_resolved':resolved_readable,'pre_era57_raw_runner_path':str(resolved) if resolved else None,'pre_era57_raw_natural_cycle_ok':natural_cycle_ok,'pre_era57_runtime_entry_decision':decision,'era57_opened':False,'next_safe_step':nxt,'updated_at_utc':ts})
    rt['current_problem']={'code':'NONE' if decision=='AUTHORIZE_ERA57_OPENING_DECISION' else decision,'severity':'P1','evidence':rel}
    rt['current_state']={'project_status':'ERA56_CLOSED_ERA57_NOT_OPENED','runtime_status':'PRE_ERA57_RAW_RESOLUTION_DECIDED','mode':'PRE_ERA57_RAW_RESOLUTION_DECIDED','last_action':{'task':WORK,'result':result,'artifact':rel,'timestamp':ts},'current_problem':rt['current_problem'],'next_safe_step':{'id':nxt,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts}
    rt['current_work_unit']={'id':WORK,'status':'CLOSED_VERIFIED','result':result,'artifact':rel,'production_mutation':False,'next_step':nxt};dump(RUNTIME,rt)

    history=load(HISTORY);events=history.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')==WORK for x in events):events.append({'event_id':WORK,'timestamp_utc':ts,'status':'CLOSED_VERIFIED','result':result,'decision':decision,'artifact':rel,'raw_runner_resolved':resolved_readable,'natural_cycle_raw_ok':natural_cycle_ok,'era57_opened':False,'production_mutation':False,'next_safe_step':nxt})
    history['updated_at']=ts;history['updated_at_utc']=ts;dump(HISTORY,history)

    master=MASTER.read_text(encoding='utf-8')
    master=section(master,'## 03 LAST VERIFIED WORK',f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={result}
LAST_ARTIFACT={rel}
RAW_RUNNER_RESOLVED={str(resolved_readable).lower()}
RAW_NATURAL_CYCLE_OK={str(natural_cycle_ok).lower()}
DECISION={decision}
ERA57_OPENED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={nxt}''')
    master=section(master,'## 10 NEXT SAFE STEP',f'''```text
NEXT_SAFE_STEP={nxt}
```

Follow the recorded raw-runner decision. ERA57 remains closed until explicit opening approval.''');MASTER.write_text(master,encoding='utf-8')
    hand=HANDOFF.read_text(encoding='utf-8')
    hand=section(hand,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}
LAST_RESULT={result}
LAST_ARTIFACT={rel}
DECISION={decision}
RAW_RUNNER_RESOLVED={str(resolved_readable).lower()}
RAW_NATURAL_CYCLE_OK={str(natural_cycle_ok).lower()}
ERA57_OPENED=false''')
    hand=section(hand,'## 07 ALLOWED NEXT DECISIONS',f'''- Raw runner decision: `{decision}`.
- ERA57 opened: `false`.
- Production mutation: `false`.

NEXT_SAFE_STEP={nxt}''');HANDOFF.write_text(hand,encoding='utf-8')

    for path in (RUNTIME,HISTORY,ARTIFACT):load(path)
    if git('rev-list','-n1',TAG55)!=SEAL55 or git('rev-list','-n1',TAG56)!=SEAL56:raise RuntimeError('SEAL_CHANGED')
    git('add','-A');chk=run(['git','diff','--cached','--check'],check=False)
    if chk.returncode:print(chk.stdout,end='');print(chk.stderr,end='');raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m','PRE_ERA57_RAW_RESOLUTION | '+('OK' if resolved_readable else 'WARN')+' | RUNTIME_ENTRY_DECISION')
    print('PRE_ERA57_RAW_RESOLUTION=SUCCESS');print('RAW_RUNNER_RESOLVED='+str(resolved_readable).lower());print('RAW_NATURAL_CYCLE_OK='+str(natural_cycle_ok).lower());print('DECISION='+decision);print('ERA57_OPENED=false');print('PRODUCTION_MUTATION=false');print('NEXT_SAFE_STEP='+nxt);print('LOCAL_COMMIT='+git('rev-parse','HEAD'));return 0

if __name__=='__main__':raise SystemExit(main())
