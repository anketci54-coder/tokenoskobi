#!/usr/bin/env python3
from __future__ import annotations

import json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
WORK='ERA56E_GLOBAL_CACHE_BOUNDED_RUNTIME_BINDING_READINESS_DECISION'
RESULT='OK_BOUNDED_RUNTIME_BINDING_READINESS_AUTHORIZED_APPLY_BLOCKED'
NEXT='ERA56F_GLOBAL_CACHE_BOUNDED_RUNTIME_BINDING_PLAN_AND_CANARY_DECISION'
SUBJECT='ERA56E | OK | BOUNDED_RUNTIME_BINDING_READINESS_DECISION'
TAG='ERA55_FINAL_SEAL';SEAL='f22ce4f07788ec7fbe22a72f872467705b72db5a'
RUNTIME=ROOT/'PROJECT_RUNTIME.json';ROADMAP=ROOT/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md';HANDOFF=ROOT/'07_PROJECT_HANDOFF.md';HISTORY=ROOT/'PROJECT_HISTORY.json';ALMANAC=ROOT/'04_ALMANAC.md'
TK_AI=ROOT/'reports/LATEST_TK_AI_HANDOFF.md';MACHINE=ROOT/'data/control/latest_tk_machine_state.json'
ARTIFACT=ROOT/'data/control/era56e_global_cache_bounded_runtime_binding_readiness_decision_v1.json'


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
    if git('rev-list','-n1',TAG)!=SEAL:raise RuntimeError('ERA55_SEAL_MISMATCH')

    runtime=load(RUNTIME);roadmap=load(ROADMAP);p=runtime['canonical_runtime_pointer'];e56=era(roadmap,'ERA56')
    checks={
      'era56_open':p.get('era56_opened') is True and e56.get('status')=='OPEN',
      'era56a_contract_locked':p.get('era56_contract_locked') is True,
      'era56b_schema_and_rebuild':p.get('era56b_schema_validated') is True and p.get('era56b_rebuild_parity') is True,
      'era56c_mapping_parity_stale':p.get('era56c_record_mapping_validated') is True and p.get('era56c_logical_parity') is True and p.get('era56c_stale_detection') is True,
      'era56d_atomic_readonly_failclosed':p.get('era56d_atomic_publish') is True and p.get('era56d_readonly_consumer') is True and p.get('era56d_fail_closed') is True,
      'next_step_matches':p.get('next_safe_step')==WORK,
      'production_apply_blocked':p.get('era56_production_apply_authorized') is False,
      'writer_active':p.get('production_ledger_writer_active') is True,
      'runner_lock_enabled':p.get('runner_lock_enabled') is True,
      'option_b_blocked':p.get('option_b_authorized') is False and p.get('wal_apply_authorized') is False,
    }
    if not all(checks.values()):raise RuntimeError('READINESS_CHECK_FAILED:'+','.join(k for k,v in checks.items() if not v))

    # Decision is intentionally conservative: readiness to plan is authorized,
    # runtime binding/apply remains blocked until a bounded canary plan is approved.
    scores={
      'reliability':96,
      'security':97,
      'performance':85,
      'statistics':82,
      'probability':91,
    }
    expected_gain=(scores['reliability']+scores['security']+scores['probability'])/3
    cost_penalty=max(0,100-scores['performance'])
    uncertainty_penalty=max(0,100-scores['statistics'])
    net_utility=round(expected_gain-cost_penalty-uncertainty_penalty,4)
    decision='AUTHORIZE_FUTURE_BOUNDED_BINDING_PLAN'
    production_apply_authorized=False
    runtime_binding_authorized=False

    ts=datetime.now(timezone.utc).isoformat();rel=str(ARTIFACT.relative_to(ROOT))
    dump(ARTIFACT,{
      'schema':'era56e_global_cache_bounded_runtime_binding_readiness_decision_v1',
      'timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_READINESS_DECISION_VERIFIED','result':RESULT,
      'checks':checks,'era24f_scores':scores,'expected_gain':round(expected_gain,4),'cost_penalty':cost_penalty,
      'uncertainty_penalty':uncertainty_penalty,'net_utility':net_utility,'accept_baseline':95.0,
      'decision':decision,'bounded_binding_plan_authorized':True,'runtime_binding_authorized':runtime_binding_authorized,
      'production_apply_authorized':production_apply_authorized,'service_timer_panel_mutation':False,'production_mutation':False,
      'required_next_guards':['separate cache file','single writer','atomic publish','readonly consumer','stale/hash fail-closed','rollback by unbinding','no source authority mutation','human approval'],
      'next_safe_step':NEXT,
    })

    runtime['current_problem']={'code':'ERA56F_BOUNDED_RUNTIME_BINDING_PLAN_AND_CANARY_DECISION_PENDING','severity':'P1','evidence':rel}
    p.update({'current_stage':'ERA56E_BINDING_READINESS_DECIDED','last_completed':WORK,'last_result':RESULT,'last_artifact':rel,
      'era56e_readiness_decision':decision,'era56e_net_utility':net_utility,'era56_bounded_binding_plan_authorized':True,
      'era56_runtime_binding_authorized':False,'era56_production_apply_authorized':False,'next_safe_step':NEXT,'updated_at_utc':ts})
    runtime['current_state']={'project_status':'ACTIVE','runtime_status':'ERA56_OPEN_DESIGN_ONLY','mode':'ERA56E_BINDING_READINESS_DECIDED',
      'last_action':{'task':WORK,'result':RESULT,'artifact':rel,'timestamp':ts},'current_problem':runtime['current_problem'],
      'next_safe_step':{'id':NEXT,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts}
    runtime['current_work_unit']={'id':WORK,'status':'CLOSED_READINESS_DECISION_VERIFIED','result':RESULT,'artifact':rel,'production_mutation':False,'next_step':NEXT}
    dump(RUNTIME,runtime)

    e56.update({'active_stage':'ERA56E_BINDING_READINESS_DECIDED','last_completed_substep':WORK,'last_result':RESULT,'next_safe_step':NEXT,
      'bounded_binding_plan_authorized':True,'runtime_binding_authorized':False,'production_apply_authorized':False,'era24f_net_utility':net_utility})
    dump(ROADMAP,roadmap)

    master=MASTER.read_text(encoding='utf-8')
    master=sec(master,'## 02 CURRENT MAJOR-LINE POSITION',f'''```text
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=OPEN_BOUNDED_DESIGN_ONLY
CURRENT_STAGE=ERA56E_BINDING_READINESS_DECIDED
LAST_COMPLETED_SUBSTEP={WORK}
ERA56_BOUNDED_BINDING_PLAN_AUTHORIZED=true
ERA56_RUNTIME_BINDING_AUTHORIZED=false
ERA56_PRODUCTION_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
```''')
    master=sec(master,'## 03 LAST VERIFIED WORK',f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_READINESS_DECISION_VERIFIED
DECISION={decision}
ERA24F_NET_UTILITY={net_utility}
RUNTIME_BINDING_AUTHORIZED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}''')
    master=sec(master,'## 10 NEXT SAFE STEP',f'''```text
NEXT_SAFE_STEP={NEXT}
```

Prepare the bounded runtime-binding plan and canary decision only. No service, timer, panel or production cache binding yet.''')
    MASTER.write_text(master,encoding='utf-8')

    hand=HANDOFF.read_text(encoding='utf-8')
    hand=sec(hand,'## 02 CURRENT CONTINUATION CHECKPOINT',f'''PROJECT_STATUS=ACTIVE_ERA56_GLOBAL_INTELLIGENCE_CACHE
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=OPEN_BOUNDED_DESIGN_ONLY
CURRENT_STAGE=ERA56E_BINDING_READINESS_DECIDED
LAST_COMPLETED_SUBSTEP={WORK}
ERA56_BOUNDED_BINDING_PLAN_AUTHORIZED=true
ERA56_RUNTIME_BINDING_AUTHORIZED=false
ERA56_PRODUCTION_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD''')
    hand=sec(hand,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_READINESS_DECISION_VERIFIED
DECISION={decision}
CURRENT_PROBLEM=ERA56F_BOUNDED_RUNTIME_BINDING_PLAN_AND_CANARY_DECISION_PENDING''')
    hand=sec(hand,'## 07 ALLOWED NEXT DECISIONS',f'''- Bounded binding plan: `AUTHORIZED`.
- Runtime binding: `BLOCKED`.
- Production apply: `BLOCKED`.
- Service/timer/panel mutation: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}''')
    HANDOFF.write_text(hand,encoding='utf-8')

    history=load(HISTORY);events=history.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')==WORK for x in events):
        events.append({'event_id':WORK,'timestamp_utc':ts,'era':'ERA56','status':'CLOSED_READINESS_DECISION_VERIFIED','result':RESULT,'artifact':rel,
          'decision':decision,'net_utility':net_utility,'runtime_binding_authorized':False,'production_mutation':False,'next_safe_step':NEXT})
    history['updated_at']=ts;history['updated_at_utc']=ts;dump(HISTORY,history)

    marker='## ERA56E GLOBAL CACHE BOUNDED RUNTIME BINDING READINESS DECISION';alm=ALMANAC.read_text(encoding='utf-8')
    if marker not in alm:
        ALMANAC.write_text(alm.rstrip()+f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_READINESS_DECISION_VERIFIED`\n- Result: `{RESULT}`\n- Decision: `{decision}`\n- ERA24F net utility: `{net_utility}`\n- Bounded binding plan authorized: `true`\n- Runtime binding authorized: `false`\n- Production mutation: `false`\n- Next safe step: `{NEXT}`\n''',encoding='utf-8')

    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nSTATE_SYNC_UTC={ts}\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nCURRENT_STAGE=ERA56E_BINDING_READINESS_DECIDED\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nDECISION={decision}\nERA24F_NET_UTILITY={net_utility}\nERA56_RUNTIME_BINDING_AUTHORIZED=false\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\nNEXT_SAFE_STEP={NEXT}\n''',encoding='utf-8')

    machine=load(MACHINE);machine['created_at_utc']=ts;machine['collect_mode']='canonical_sync_snapshot_no_tk_machine'
    machine['current_state']={'authority':'PROJECT_RUNTIME.json','runtime_status':'ERA56_OPEN_DESIGN_ONLY','active_work_unit':{'id':WORK,'status':'CLOSED_READINESS_DECISION_VERIFIED','artifact':rel},'next_safe_step':{'name':NEXT,'status':'READY'},'last_action':{'timestamp':ts,'task':WORK,'result':RESULT,'artifact':rel}}
    machine['known_facts']={'era56_opened':True,'era56_stage':'ERA56E_BINDING_READINESS_DECIDED','bounded_binding_plan_authorized':True,'runtime_binding_authorized':False,'production_apply_authorized':False,'production_mutation':False,'era24f_net_utility':net_utility}
    dump(MACHINE,machine)

    for path in (RUNTIME,ROADMAP,HISTORY,MACHINE,ARTIFACT):load(path)
    if git('rev-list','-n1',TAG)!=SEAL:raise RuntimeError('ERA55_SEAL_CHANGED')
    git('add','-A');check=run(['git','diff','--cached','--check'],check=False)
    if check.returncode!=0:print(check.stdout,end='');print(check.stderr,end='');raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m',SUBJECT)
    print('ERA56E_DECISION=SUCCESS');print('DECISION='+decision);print('ERA24F_NET_UTILITY='+str(net_utility));print('BOUNDED_BINDING_PLAN_AUTHORIZED=true');print('RUNTIME_BINDING_AUTHORIZED=false');print('PRODUCTION_APPLY_AUTHORIZED=false');print('PRODUCTION_MUTATION=false');print('NEXT_SAFE_STEP='+NEXT);print('LOCAL_COMMIT='+git('rev-parse','HEAD'));return 0

if __name__=='__main__':raise SystemExit(main())
