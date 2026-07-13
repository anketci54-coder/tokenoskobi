#!/usr/bin/env python3
from __future__ import annotations

import json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
RUNTIME=ROOT/'PROJECT_RUNTIME.json'
ROADMAP=ROOT/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md'
HANDOFF=ROOT/'07_PROJECT_HANDOFF.md'
HISTORY=ROOT/'PROJECT_HISTORY.json'
ALMANAC=ROOT/'04_ALMANAC.md'
ARTIFACT=ROOT/'data/control/era56_opening_and_ownership_decision_v1.json'
WORK='ERA56_GLOBAL_INTELLIGENCE_CACHE_OPENING_DECISION'
RESULT='OK_ERA56_OPENED_OWNERSHIP_AND_OVERLAP_DESIGN_REQUIRED'
NEXT='ERA56A_GLOBAL_CACHE_OWNERSHIP_OVERLAP_AND_REBUILD_CONTRACT'
SUBJECT='ERA56_OPENING | OK | OWNERSHIP_AND_OVERLAP_DECISION'
SEAL='ERA55_FINAL_SEAL'
SEAL_COMMIT='f22ce4f07788ec7fbe22a72f872467705b72db5a'


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
def sec(text,h,b):
    s=text.find(h)
    if s<0: raise RuntimeError('HEADING_MISSING:'+h)
    e=text.find('\n## ',s+len(h)); e=len(text) if e<0 else e
    return text[:s]+h+'\n\n'+b.rstrip()+'\n'+text[e:]
def era(roadmap,era_id):
    for v in roadmap.get('versions',[]):
        if v.get('id')=='V3':
            for e in v.get('children',[]):
                if e.get('id')==era_id:return e
    raise RuntimeError('ERA_NOT_FOUND:'+era_id)


def main():
    if git('status','--short'): raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected: raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list','-n1',SEAL)!=SEAL_COMMIT: raise RuntimeError('ERA55_SEAL_MISMATCH')

    runtime=load(RUNTIME); roadmap=load(ROADMAP); p=runtime['canonical_runtime_pointer']; e55=era(roadmap,'ERA55'); e56=era(roadmap,'ERA56')
    checks={
      'era55_closed':p.get('era55_closed') is True and e55.get('status')=='CLOSED',
      'era56_not_open':p.get('era56_opened') is False and e56.get('status')=='PLANNED',
      'cleanup_closed':p.get('last_completed')=='ERA55_POST_CLOSE_CLEANUP_AND_ERA56_ENTRY_HARDENING',
      'next_is_opening_decision':p.get('next_safe_step')==WORK,
      'runner_lock_enabled':p.get('runner_lock_enabled') is True,
      'writer_active':p.get('production_ledger_writer_active') is True,
      'p0_closed':p.get('p0_f1_closed') is True,
      'option_b_blocked':p.get('option_b_authorized') is False and p.get('wal_apply_authorized') is False,
      'era55_dependency':e56.get('depends_on')=='ERA55',
      'immutable_cache_purpose':e56.get('purpose')=='Global immutable snapshot/cache/readmodel katmanı.',
    }
    if not all(checks.values()): raise RuntimeError('OPENING_CHECK_FAILED:'+','.join(k for k,v in checks.items() if not v))

    ts=datetime.now(timezone.utc).isoformat(); rel=str(ARTIFACT.relative_to(ROOT))
    ownership={
      'source_of_truth':'Existing canonical DB/ledger/readmodel owners remain authoritative; ERA56 cache is derived only.',
      'write_authority':'ERA56 has zero authority to mutate source DB, ledger, service, timer, panel, trade or wallet state.',
      'cache_role':'Immutable derived snapshot and read acceleration layer only.',
      'overlap_rule':'No duplicate ownership with backpressure readmodel, panel bridge, hot ingress or ledger.',
      'invalidation_rule':'Staleness and source-version mismatch must fail closed.',
      'rebuild_rule':'Cache must be fully rebuildable from authoritative sources.',
      'human_authority':True,
    }
    dump(ARTIFACT,{'schema':'era56_opening_and_ownership_decision_v1','timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_ERA56_OPENED_DESIGN_ONLY','result':RESULT,'checks':checks,'era56_opened':True,'implementation_started':False,'production_mutation':False,'ownership_contract_seed':ownership,'next_safe_step':NEXT})

    runtime['current_era']='ERA56'; runtime['current_era_status']='OPEN'
    runtime['current_problem']={'code':'ERA56_CACHE_OWNERSHIP_OVERLAP_REBUILD_CONTRACT_PENDING','severity':'P1','evidence':rel}
    p.update({'current_era':'ERA56_GLOBAL_INTELLIGENCE_CACHE','current_stage':'ERA56_OPENED_DESIGN_ONLY','project_status':'ACTIVE_ERA56_OPENED_OWNERSHIP_CONTRACT_PENDING','last_completed':WORK,'last_result':RESULT,'last_artifact':rel,'era56_opened':True,'era56_implementation_started':False,'next_safe_step':NEXT,'updated_at_utc':ts})
    runtime['current_state']={'project_status':'ACTIVE','runtime_status':'ERA56_OPEN_DESIGN_ONLY','mode':'ERA56_OWNERSHIP_CONTRACT_PENDING','last_action':{'task':WORK,'result':RESULT,'artifact':rel,'timestamp':ts},'current_problem':runtime['current_problem'],'next_safe_step':{'id':NEXT,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts}
    runtime['current_work_unit']={'id':WORK,'status':'CLOSED_ERA56_OPENED_DESIGN_ONLY','result':RESULT,'artifact':rel,'production_mutation':False,'next_step':NEXT}
    dump(RUNTIME,runtime)

    e56.update({'status':'OPEN','opened_at_utc':ts,'opening_artifact':rel,'active_stage':'ERA56_OPENED_DESIGN_ONLY','implementation_started':False,'ownership_contract_required':True,'overlap_analysis_required':True,'rebuild_contract_required':True,'production_mutation_authorized':False,'next_safe_step':NEXT})
    e55['era56_open_authorized']=True
    dump(ROADMAP,roadmap)

    master=MASTER.read_text(encoding='utf-8')
    master=sec(master,'## 02 CURRENT MAJOR-LINE POSITION',f'''```text
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=OPEN_DESIGN_ONLY
CURRENT_STAGE=ERA56_OPENED_DESIGN_ONLY
LAST_COMPLETED_SUBSTEP={WORK}
ERA55_STATUS=CLOSED_VERIFIED
ERA56_IMPLEMENTATION_STARTED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=true
RUNNER_LOCK_ENABLED=true
P0_F1_CLOSED=true
OPTION_B_DECISION=DEFER_OPTION_B
WAL_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
```''')
    master=sec(master,'## 03 LAST VERIFIED WORK',f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_ERA56_OPENED_DESIGN_ONLY
ERA56_OPENED=true
ERA56_IMPLEMENTATION_STARTED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}''')
    master=sec(master,'## 10 NEXT SAFE STEP',f'''```text
NEXT_SAFE_STEP={NEXT}
```

Define source ownership, overlap boundaries, invalidation, staleness detection and full rebuild contract before any ERA56 implementation.''')
    MASTER.write_text(master,encoding='utf-8')

    hand=HANDOFF.read_text(encoding='utf-8')
    hand=sec(hand,'## 02 CURRENT CONTINUATION CHECKPOINT',f'''PROJECT_STATUS=ACTIVE_ERA56_OPENED_OWNERSHIP_CONTRACT_PENDING
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=OPEN_DESIGN_ONLY
CURRENT_STAGE=ERA56_OPENED_DESIGN_ONLY
LAST_COMPLETED_SUBSTEP={WORK}
ERA55_STATUS=CLOSED_VERIFIED
ERA56_IMPLEMENTATION_STARTED=false
PRODUCTION_LEDGER_WRITER_ACTIVE=true
RUNNER_LOCK_ENABLED=true
P0_F1_CLOSED=true
OPTION_B_DECISION=DEFER_OPTION_B
WAL_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD''')
    hand=sec(hand,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_ERA56_OPENED_DESIGN_ONLY
PRODUCTION_MUTATION=false
CURRENT_PROBLEM=ERA56_CACHE_OWNERSHIP_OVERLAP_REBUILD_CONTRACT_PENDING''')
    hand=sec(hand,'## 07 ALLOWED NEXT DECISIONS',f'''- ERA55: `CLOSED_VERIFIED`.
- ERA56: `OPEN_DESIGN_ONLY`.
- ERA56 implementation: `NOT_STARTED`.
- Cache source ownership contract: `REQUIRED`.
- Overlap and rebuild contract: `REQUIRED`.
- Production mutation: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}''')
    HANDOFF.write_text(hand,encoding='utf-8')

    hist=load(HISTORY); events=hist.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')=='ERA56_OPENING_DECISION' for x in events):
        events.append({'event_id':'ERA56_OPENING_DECISION','timestamp_utc':ts,'era':'ERA56','work_unit':WORK,'status':'CLOSED_ERA56_OPENED_DESIGN_ONLY','result':RESULT,'artifact':rel,'era56_opened':True,'implementation_started':False,'production_mutation':False,'next_safe_step':NEXT})
    hist['updated_at']=ts;hist['updated_at_utc']=ts;dump(HISTORY,hist)

    marker='## ERA56 GLOBAL INTELLIGENCE CACHE OPENING DECISION'
    alm=ALMANAC.read_text(encoding='utf-8')
    if marker not in alm:
        ALMANAC.write_text(alm.rstrip()+f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_ERA56_OPENED_DESIGN_ONLY`\n- Result: `{RESULT}`\n- ERA56 opened: `true`\n- Implementation started: `false`\n- Production mutation: `false`\n- Next safe step: `{NEXT}`\n''',encoding='utf-8')

    git('add',str(ARTIFACT.relative_to(ROOT)),str(RUNTIME.relative_to(ROOT)),str(ROADMAP.relative_to(ROOT)),str(MASTER.relative_to(ROOT)),str(HANDOFF.relative_to(ROOT)),str(HISTORY.relative_to(ROOT)),str(ALMANAC.relative_to(ROOT)))
    check=run(['git','diff','--cached','--check'],check=False)
    if check.returncode!=0:
        print(check.stdout,end='');print(check.stderr,end='');raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m',SUBJECT)
    print('ERA56_OPENING=SUCCESS')
    print('ERA56_OPENED=true')
    print('ERA56_IMPLEMENTATION_STARTED=false')
    print('PRODUCTION_MUTATION=false')
    print('NEXT_SAFE_STEP='+NEXT)
    print('LOCAL_COMMIT='+git('rev-parse','HEAD'))

if __name__=='__main__':main()
