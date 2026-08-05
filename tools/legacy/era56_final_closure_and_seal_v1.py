#!/usr/bin/env python3
from __future__ import annotations

import json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
WORK='ERA56_FINAL_CLOSURE_AND_GITHUB_SEAL'
RESULT='OK_ERA56_CLOSED_VERIFIED_READY_FOR_SEAL'
NEXT='ERA57_AUTONOMOUS_RESEARCH_LAYER_OPENING_DECISION'
SUBJECT='ERA56_FINAL_CLOSURE | OK | CLOSED_VERIFIED_READY_FOR_SEAL'
ERA55_TAG='ERA55_FINAL_SEAL';ERA55_SEAL='f22ce4f07788ec7fbe22a72f872467705b72db5a'
RUNTIME=ROOT/'PROJECT_RUNTIME.json';ROADMAP=ROOT/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md';HANDOFF=ROOT/'07_PROJECT_HANDOFF.md';HISTORY=ROOT/'PROJECT_HISTORY.json';ALMANAC=ROOT/'04_ALMANAC.md'
TK_AI=ROOT/'reports/LATEST_TK_AI_HANDOFF.md';MACHINE=ROOT/'data/control/latest_tk_machine_state.json'
ARTIFACT=ROOT/'data/control/era56_final_closure_and_seal_v1.json'


def run(args:list[str],check:bool=True):return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check,timeout=90)
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
def sec(text:str,heading:str,body:str)->str:
    s=text.find(heading)
    if s<0:raise RuntimeError('HEADING_MISSING:'+heading)
    e=text.find('\n## ',s+len(heading));e=len(text) if e<0 else e
    return text[:s]+heading+'\n\n'+body.rstrip()+'\n'+text[e:]
def era(roadmap:dict[str,Any],era_id:str)->dict[str,Any]:
    for v in roadmap.get('versions',[]):
        if v.get('id')=='V3':
            for e in v.get('children',[]):
                if e.get('id')==era_id:return e
    raise RuntimeError('ERA_NOT_FOUND:'+era_id)


def main()->int:
    if git('status','--short'):raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected:raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list','-n1',ERA55_TAG)!=ERA55_SEAL:raise RuntimeError('ERA55_SEAL_MISMATCH')
    if run(['git','tag','-l','ERA56_FINAL_SEAL']).stdout.strip():raise RuntimeError('ERA56_SEAL_ALREADY_EXISTS')

    runtime=load(RUNTIME);roadmap=load(ROADMAP);p=runtime['canonical_runtime_pointer'];e56=era(roadmap,'ERA56');e57=era(roadmap,'ERA57')
    checks={
      'era56_open':p.get('era56_opened') is True and e56.get('status')=='OPEN',
      'final_closure_ready':p.get('era56_final_closure_ready') is True and e56.get('final_closure_ready') is True,
      'next_step_matches':p.get('next_safe_step')=='ERA56_FINAL_CLOSURE_AND_GITHUB_SEAL_DECISION',
      'runtime_binding_blocked':p.get('era56_runtime_binding_authorized') is False,
      'production_apply_blocked':p.get('era56_production_apply_authorized') is False,
      'additional_canary_blocked':p.get('era56_additional_canary_authorized') is False,
      'canary_passed_unbound':p.get('era56h_canary_passed') is True and p.get('era56h_canary_unbound') is True,
      'runner_lock_enabled':p.get('runner_lock_enabled') is True,
      'writer_active':p.get('production_ledger_writer_active') is True,
      'era57_not_open':e57.get('status')=='PLANNED',
    }
    if not all(checks.values()):raise RuntimeError('CLOSURE_CHECK_FAILED:'+','.join(k for k,v in checks.items() if not v))

    ts=datetime.now(timezone.utc).isoformat();rel=str(ARTIFACT.relative_to(ROOT))
    dump(ARTIFACT,{'schema':'era56_final_closure_and_seal_v1','timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_VERIFIED_READY_FOR_SEAL','result':RESULT,'checks':checks,'era56_closed':True,'era57_opened':False,'runtime_binding_authorized':False,'production_apply_authorized':False,'production_mutation':False,'seal_tag':'ERA56_FINAL_SEAL','next_safe_step':NEXT})

    runtime['current_era']='ERA56';runtime['current_era_status']='CLOSED'
    runtime['current_problem']={'code':'ERA57_AUTONOMOUS_RESEARCH_LAYER_OPENING_DECISION_PENDING','severity':'P1','evidence':rel}
    p.update({'current_stage':'ERA56_CLOSED_VERIFIED_READY_FOR_SEAL','last_completed':WORK,'last_result':RESULT,'last_artifact':rel,'era56_opened':False,'era56_closed':True,'era56_final_closure_ready':True,'era57_opened':False,'era56_runtime_binding_authorized':False,'era56_production_apply_authorized':False,'next_safe_step':NEXT,'updated_at_utc':ts})
    runtime['current_state']={'project_status':'ACTIVE','runtime_status':'ERA56_CLOSED_ERA57_NOT_OPENED','mode':'ERA56_CLOSED_VERIFIED_READY_FOR_SEAL','last_action':{'task':WORK,'result':RESULT,'artifact':rel,'timestamp':ts},'current_problem':runtime['current_problem'],'next_safe_step':{'id':NEXT,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts}
    runtime['current_work_unit']={'id':WORK,'status':'CLOSED_VERIFIED_READY_FOR_SEAL','result':RESULT,'artifact':rel,'production_mutation':False,'next_step':NEXT};dump(RUNTIME,runtime)

    e56.update({'status':'CLOSED','closed':True,'closed_at_utc':ts,'active_stage':'ERA56_CLOSED_VERIFIED_READY_FOR_SEAL','last_completed_substep':WORK,'last_result':RESULT,'next_safe_step':NEXT,'closure_status':'CLOSED_VERIFIED_READY_FOR_SEAL','runtime_binding_authorized':False,'production_apply_authorized':False})
    e57['status']='PLANNED';dump(ROADMAP,roadmap)

    master=MASTER.read_text(encoding='utf-8');master=sec(master,'## 02 CURRENT MAJOR-LINE POSITION',f'''```text
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=CLOSED_VERIFIED_READY_FOR_SEAL
CURRENT_STAGE=ERA56_CLOSED_VERIFIED_READY_FOR_SEAL
LAST_COMPLETED_SUBSTEP={WORK}
ERA56_CLOSED=true
ERA57_OPENED=false
ERA56_RUNTIME_BINDING_AUTHORIZED=false
ERA56_PRODUCTION_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
```''');master=sec(master,'## 03 LAST VERIFIED WORK',f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_VERIFIED_READY_FOR_SEAL
ERA56_CLOSED=true
ERA57_OPENED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}''');master=sec(master,'## 10 NEXT SAFE STEP',f'''```text
NEXT_SAFE_STEP={NEXT}
```

Decide whether to open ERA57 Autonomous Research Layer. ERA57 is not opened by ERA56 closure.''');MASTER.write_text(master,encoding='utf-8')

    hand=HANDOFF.read_text(encoding='utf-8');hand=sec(hand,'## 02 CURRENT CONTINUATION CHECKPOINT',f'''PROJECT_STATUS=ERA56_CLOSED_ERA57_OPENING_DECISION_PENDING
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=CLOSED_VERIFIED_READY_FOR_SEAL
CURRENT_STAGE=ERA56_CLOSED_VERIFIED_READY_FOR_SEAL
LAST_COMPLETED_SUBSTEP={WORK}
ERA56_CLOSED=true
ERA57_OPENED=false
ERA56_RUNTIME_BINDING_AUTHORIZED=false
ERA56_PRODUCTION_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD''');hand=sec(hand,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_VERIFIED_READY_FOR_SEAL
CURRENT_PROBLEM=ERA57_AUTONOMOUS_RESEARCH_LAYER_OPENING_DECISION_PENDING''');hand=sec(hand,'## 07 ALLOWED NEXT DECISIONS',f'''- ERA56: `CLOSED_VERIFIED_READY_FOR_SEAL`.
- ERA57: `NOT_OPENED`.
- Runtime binding: `DEFERRED`.
- Production apply: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}''');HANDOFF.write_text(hand,encoding='utf-8')

    history=load(HISTORY);events=history.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')==WORK for x in events):events.append({'event_id':WORK,'timestamp_utc':ts,'era':'ERA56','status':'CLOSED_VERIFIED_READY_FOR_SEAL','result':RESULT,'artifact':rel,'era56_closed':True,'era57_opened':False,'production_mutation':False,'seal_tag':'ERA56_FINAL_SEAL','next_safe_step':NEXT})
    history['updated_at']=ts;history['updated_at_utc']=ts;dump(HISTORY,history)

    marker='## ERA56 FINAL CLOSURE AND GITHUB SEAL';alm=ALMANAC.read_text(encoding='utf-8')
    if marker not in alm:ALMANAC.write_text(alm.rstrip()+f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_VERIFIED_READY_FOR_SEAL`\n- Result: `{RESULT}`\n- ERA56 closed: `true`\n- ERA57 opened: `false`\n- Runtime binding authorized: `false`\n- Production mutation: `false`\n- Seal tag: `ERA56_FINAL_SEAL`\n- Next safe step: `{NEXT}`\n''',encoding='utf-8')

    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nSTATE_SYNC_UTC={ts}\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nCURRENT_STAGE=ERA56_CLOSED_VERIFIED_READY_FOR_SEAL\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nERA56_CLOSED=true\nERA57_OPENED=false\nERA56_RUNTIME_BINDING_AUTHORIZED=false\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\nNEXT_SAFE_STEP={NEXT}\n''',encoding='utf-8')

    machine=load(MACHINE);machine['created_at_utc']=ts;machine['collect_mode']='canonical_sync_snapshot_no_tk_machine';machine['current_state']={'authority':'PROJECT_RUNTIME.json','runtime_status':'ERA56_CLOSED_ERA57_NOT_OPENED','active_work_unit':{'id':WORK,'status':'CLOSED_VERIFIED_READY_FOR_SEAL','artifact':rel},'next_safe_step':{'name':NEXT,'status':'READY'},'last_action':{'timestamp':ts,'task':WORK,'result':RESULT,'artifact':rel}};machine['known_facts']={'era56_closed':True,'era57_opened':False,'runtime_binding_authorized':False,'production_apply_authorized':False,'production_mutation':False,'seal_tag':'ERA56_FINAL_SEAL'};dump(MACHINE,machine)

    for path in (RUNTIME,ROADMAP,HISTORY,MACHINE,ARTIFACT):load(path)
    if git('rev-list','-n1',ERA55_TAG)!=ERA55_SEAL:raise RuntimeError('ERA55_SEAL_CHANGED')
    git('add','-A');check=run(['git','diff','--cached','--check'],check=False)
    if check.returncode!=0:print(check.stdout,end='');print(check.stderr,end='');raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m',SUBJECT)
    print('ERA56_FINAL_CLOSURE=SUCCESS');print('ERA56_CLOSED=true');print('ERA57_OPENED=false');print('RUNTIME_BINDING_AUTHORIZED=false');print('PRODUCTION_APPLY_AUTHORIZED=false');print('PRODUCTION_MUTATION=false');print('NEXT_SAFE_STEP='+NEXT);print('LOCAL_COMMIT='+git('rev-parse','HEAD'));return 0

if __name__=='__main__':raise SystemExit(main())
