#!/usr/bin/env python3
from __future__ import annotations

import json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
RUNTIME=ROOT/'PROJECT_RUNTIME.json'
ROADMAP=ROOT/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
ROADMAP_MD=ROOT/'03_ROADMAP.md'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md'
HANDOFF=ROOT/'07_PROJECT_HANDOFF.md'
HISTORY=ROOT/'PROJECT_HISTORY.json'
ALMANAC=ROOT/'04_ALMANAC.md'
ARTIFACT=ROOT/'data/control/era55_final_closure_and_github_seal_v1.json'
WORK='ERA55_FINAL_CLOSURE_AND_GITHUB_SEAL'
RESULT='OK_ERA55_CLOSED_VERIFIED_READY_FOR_SEAL'
NEXT='ERA56_GLOBAL_INTELLIGENCE_CACHE_OPENING_DECISION'
SUBJECT='ERA55_FINAL_CLOSURE | OK | CLOSED_VERIFIED_READY_FOR_SEAL'


def run(args):
    return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=True,timeout=60)

def git(*args): return run(['git',*args]).stdout.strip()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=p.name+'.',dir=p.parent)
    with os.fdopen(fd,'w',encoding='utf-8') as h:
        json.dump(d,h,ensure_ascii=False,indent=2,sort_keys=True); h.write('\n'); h.flush(); os.fsync(h.fileno())
    os.replace(tmp,p)

def sec(text,heading,body):
    s=text.find(heading)
    if s<0: raise RuntimeError('HEADING_MISSING:'+heading)
    e=text.find('\n## ',s+len(heading)); e=len(text) if e<0 else e
    return text[:s]+heading+'\n\n'+body.rstrip()+'\n'+text[e:]

def era55(roadmap):
    for v in roadmap.get('versions',[]):
        if v.get('id')=='V3':
            for e in v.get('children',[]):
                if e.get('id')=='ERA55': return e
    raise RuntimeError('ERA55_NOT_FOUND')


def main():
    if git('status','--short'): raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected: raise RuntimeError('HEAD_MISMATCH')

    runtime=load(RUNTIME); roadmap=load(ROADMAP); e55=era55(roadmap)
    p=runtime['canonical_runtime_pointer']
    checks={
      'a28_last_completed':p.get('last_completed')=='ERA55A_28_ERA55_FINAL_CLOSURE_READINESS_AND_CANONICAL_ALIGNMENT_DECISION',
      'a28_result':p.get('last_result')=='OK_ERA55_FINAL_CLOSURE_READINESS_CONFIRMED_NOT_YET_CLOSED',
      'next_is_final_closure':p.get('next_safe_step')==WORK,
      'era55_open':runtime.get('current_era')=='ERA55' and runtime.get('current_era_status')=='OPEN' and e55.get('status')=='OPEN',
      'closure_ready':e55.get('final_closure_ready') is True,
      'writer_active':p.get('production_ledger_writer_active') is True and e55.get('production_ledger_writer_active') is True,
      'p0_closed':p.get('p0_f1_closed') is True and e55.get('p0_f1_closed') is True,
      'option_b_blocked':p.get('option_b_authorized') is False and p.get('wal_apply_authorized') is False,
      'era56_not_open':e55.get('era56_open_authorized') is False,
    }
    if not all(checks.values()): raise RuntimeError('CLOSURE_CHECK_FAILED:'+','.join(k for k,v in checks.items() if not v))

    ts=datetime.now(timezone.utc).isoformat(); rel=str(ARTIFACT.relative_to(ROOT))
    dump(ARTIFACT,{'schema':'era55_final_closure_and_github_seal_v1','timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_VERIFIED_READY_FOR_SEAL','result':RESULT,'checks':checks,'era55_closed':True,'era56_opened':False,'production_mutation':False,'next_safe_step':NEXT})

    runtime['current_era']='ERA55'; runtime['current_era_status']='CLOSED'
    runtime['current_problem']={'code':'ERA56_OPENING_DECISION_PENDING','severity':'P1','evidence':rel}
    p.update({'project_status':'ERA55_CLOSED_VERIFIED_ERA56_OPENING_DECISION_PENDING','current_stage':'ERA55_CLOSED_VERIFIED','last_completed':WORK,'last_result':RESULT,'last_artifact':rel,'era55_closed':True,'era56_opened':False,'next_safe_step':NEXT,'updated_at_utc':ts})
    runtime['current_state']={'project_status':'ACTIVE','runtime_status':'ERA_CLOSED','mode':'ERA55_CLOSED_VERIFIED','last_action':{'task':WORK,'result':RESULT,'artifact':rel,'timestamp':ts},'current_problem':runtime['current_problem'],'next_safe_step':{'id':NEXT,'status':'READY','human_authorization_required':True,'era56_open_authorized':False},'updated_at':ts}
    runtime['current_work_unit']={'id':WORK,'status':'CLOSED_VERIFIED_READY_FOR_SEAL','result':RESULT,'artifact':rel,'production_mutation':False,'next_step':NEXT}
    dump(RUNTIME,runtime)

    e55.update({'status':'CLOSED','active_stage':'ERA55_CLOSED_VERIFIED','last_completed_substep':WORK,'last_result':RESULT,'next_safe_step':NEXT,'final_closure_ready':True,'final_closure_authorized':True,'closure_status':'CLOSED_VERIFIED','closure_artifact':rel,'era56_open_authorized':False})
    dump(ROADMAP,roadmap)

    md=ROADMAP_MD.read_text(encoding='utf-8')
    md=md.replace('- Status: `OPEN`','- Status: `CLOSED`',1)
    md=md.replace('- Last completed substep: `ERA55A_28_ERA55_FINAL_CLOSURE_READINESS_AND_CANONICAL_ALIGNMENT_DECISION`',f'- Last completed substep: `{WORK}`',1)
    md=md.replace('- Next safe step: `ERA55_FINAL_CLOSURE_AND_GITHUB_SEAL_DECISION`',f'- Next safe step: `{NEXT}`',1)
    ROADMAP_MD.write_text(md,encoding='utf-8')

    master=MASTER.read_text(encoding='utf-8')
    master=sec(master,'## 02 CURRENT MAJOR-LINE POSITION',f'''```text
CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION
ERA55_STATUS=CLOSED_VERIFIED
CURRENT_STAGE=ERA55_CLOSED_VERIFIED
LAST_COMPLETED_SUBSTEP={WORK}
PRODUCTION_LEDGER_WRITER_ACTIVE=true
P0_F1_CLOSED=true
OPTION_B_DECISION=DEFER_OPTION_B
WAL_APPLY_AUTHORIZED=false
ERA56_OPENED=false
PRODUCTION_MUTATION=false
```''')
    master=sec(master,'## 03 LAST VERIFIED WORK',f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_VERIFIED_READY_FOR_SEAL
ERA55_CLOSED=true
ERA56_OPENED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}''')
    master=sec(master,'## 10 NEXT SAFE STEP',f'''```text
NEXT_SAFE_STEP={NEXT}
```

Decide whether to open ERA56 Global Intelligence Cache. ERA56 is not opened by ERA55 closure.''')
    MASTER.write_text(master,encoding='utf-8')

    hand=HANDOFF.read_text(encoding='utf-8')
    hand=hand.replace('NEXT_SAFE_STEP=ERA55_FINAL_CLOSURE_AND_GITHUB_SEAL_DECISION','NEXT_SAFE_STEP='+NEXT)
    hand=hand.replace('CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION','CURRENT_ERA=ERA55_RUNTIME_OPTIMIZATION\nERA55_STATUS=CLOSED_VERIFIED',1)
    HANDOFF.write_text(hand,encoding='utf-8')

    hist=load(HISTORY); events=hist.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')=='ERA55_FINAL_CLOSURE' for x in events):
        events.append({'event_id':'ERA55_FINAL_CLOSURE','timestamp_utc':ts,'era':'ERA55','work_unit':WORK,'status':'CLOSED_VERIFIED_READY_FOR_SEAL','result':RESULT,'artifact':rel,'era55_closed':True,'era56_opened':False,'production_mutation':False,'next_safe_step':NEXT})
    hist['updated_at']=ts; hist['updated_at_utc']=ts; dump(HISTORY,hist)

    marker='## ERA55 FINAL CLOSURE AND GITHUB SEAL'
    alm=ALMANAC.read_text(encoding='utf-8')
    if marker not in alm:
        ALMANAC.write_text(alm.rstrip()+f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_VERIFIED_READY_FOR_SEAL`\n- Result: `{RESULT}`\n- ERA55 closed: `true`\n- ERA56 opened: `false`\n- Option B: `DEFERRED`\n- Production mutation: `false`\n- Next safe step: `{NEXT}`\n''',encoding='utf-8')

    git('add',str(ARTIFACT.relative_to(ROOT)),str(RUNTIME.relative_to(ROOT)),str(ROADMAP.relative_to(ROOT)),str(ROADMAP_MD.relative_to(ROOT)),str(MASTER.relative_to(ROOT)),str(HANDOFF.relative_to(ROOT)),str(HISTORY.relative_to(ROOT)),str(ALMANAC.relative_to(ROOT)))
    git('diff','--cached','--check')
    git('commit','-m',SUBJECT)
    print('ERA55_FINAL_CLOSURE=SUCCESS')
    print('ERA55_CLOSED=true')
    print('ERA56_OPENED=false')
    print('NEXT_SAFE_STEP='+NEXT)
    print('LOCAL_COMMIT='+git('rev-parse','HEAD'))

if __name__=='__main__': main()
