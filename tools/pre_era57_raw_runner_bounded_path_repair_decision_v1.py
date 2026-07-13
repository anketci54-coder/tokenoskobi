#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
WORK='PRE_ERA57_RAW_RUNNER_BOUNDED_PATH_REPAIR_DECISION'
TARGET='tools/news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py'
CLEANUP_COMMIT='71c2a083508011a51c6071a3678063b0a21c876c'
SOURCE_REF=CLEANUP_COMMIT+'^:'+TARGET
TAG55='ERA55_FINAL_SEAL';SEAL55='f22ce4f07788ec7fbe22a72f872467705b72db5a'
TAG56='ERA56_FINAL_SEAL';SEAL56='39dd684a71e39c4f05ce2a5113985fcf647718a0'
RUNTIME=ROOT/'PROJECT_RUNTIME.json';HISTORY=ROOT/'PROJECT_HISTORY.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md';HANDOFF=ROOT/'07_PROJECT_HANDOFF.md'
ARTIFACT=ROOT/'data/control/pre_era57_raw_runner_bounded_path_repair_decision_v1.json'


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


def main()->int:
    if git('status','--short'):raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected:raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list','-n1',TAG55)!=SEAL55 or git('rev-list','-n1',TAG56)!=SEAL56:raise RuntimeError('SEAL_MISMATCH')
    rt=load(RUNTIME);p=rt['canonical_runtime_pointer']
    if p.get('era57_opened') is not False:raise RuntimeError('ERA57_MUST_REMAIN_CLOSED')
    if p.get('next_safe_step')!=WORK:raise RuntimeError('NEXT_STEP_MISMATCH')

    show=run(['git','show',SOURCE_REF],check=False)
    blob=show.stdout if show.returncode==0 else ''
    blob_found=bool(blob)
    syntax_ok=False
    marker_ok=False
    sha=None
    if blob_found:
        sha=hashlib.sha256(blob.encode()).hexdigest()
        marker_ok=('sqlite3' in blob or 'news_' in blob) and ('__main__' in blob or 'main(' in blob)
        with tempfile.TemporaryDirectory(prefix='pre_era57_raw_review_') as td:
            f=Path(td)/'candidate.py';f.write_text(blob,encoding='utf-8')
            syntax_ok=run(['/usr/bin/python3','-m','py_compile',str(f)],check=False).returncode==0

    if blob_found and syntax_ok and marker_ok:
        decision='AUTHORIZE_EXACT_GIT_HISTORY_RESTORE_REVIEW'
        nxt='PRE_ERA57_RAW_RUNNER_EXACT_RESTORE_AND_NATURAL_CYCLE_VERIFY'
        result='OK_EXACT_HISTORY_BLOB_VALIDATED'
    else:
        decision='DEFER_ERA57_RAW_RUNNER_TARGET_UNPROVEN'
        nxt='PRE_ERA57_RAW_RUNNER_TARGET_DISCOVERY_REVIEW'
        result='WARN_HISTORY_BLOB_NOT_PROVEN'

    ts=datetime.now(timezone.utc).isoformat();rel=str(ARTIFACT.relative_to(ROOT))
    dump(ARTIFACT,{'schema':'pre_era57_raw_runner_bounded_path_repair_decision_v1','timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_VERIFIED','result':result,'decision':decision,'cleanup_commit':CLEANUP_COMMIT,'source_ref':SOURCE_REF,'target_path':TARGET,'history_blob_found':blob_found,'candidate_sha256':sha,'candidate_syntax_ok':syntax_ok,'candidate_contract_markers_ok':marker_ok,'restore_performed':False,'systemd_mutation':False,'production_mutation':False,'era57_opened':False,'next_safe_step':nxt})

    p.update({'current_stage':'PRE_ERA57_RAW_REPAIR_DECIDED','last_completed':WORK,'last_result':result,'last_artifact':rel,'pre_era57_raw_repair_decision':decision,'pre_era57_raw_history_blob_sha256':sha,'era57_opened':False,'next_safe_step':nxt,'updated_at_utc':ts})
    rt['current_problem']={'code':'NONE' if decision.startswith('AUTHORIZE_') else decision,'severity':'P1','evidence':rel}
    rt['current_state']={'project_status':'ERA56_CLOSED_ERA57_NOT_OPENED','runtime_status':'PRE_ERA57_RAW_REPAIR_DECIDED','mode':'PRE_ERA57_RAW_REPAIR_DECIDED','last_action':{'task':WORK,'result':result,'artifact':rel,'timestamp':ts},'current_problem':rt['current_problem'],'next_safe_step':{'id':nxt,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts}
    rt['current_work_unit']={'id':WORK,'status':'CLOSED_VERIFIED','result':result,'artifact':rel,'production_mutation':False,'next_step':nxt};dump(RUNTIME,rt)

    hist=load(HISTORY);events=hist.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')==WORK for x in events):events.append({'event_id':WORK,'timestamp_utc':ts,'status':'CLOSED_VERIFIED','result':result,'decision':decision,'artifact':rel,'history_blob_found':blob_found,'candidate_sha256':sha,'restore_performed':False,'era57_opened':False,'production_mutation':False,'next_safe_step':nxt})
    hist['updated_at']=ts;hist['updated_at_utc']=ts;dump(HISTORY,hist)

    m=MASTER.read_text(encoding='utf-8');m=sec(m,'## 03 LAST VERIFIED WORK',f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={result}
LAST_ARTIFACT={rel}
DECISION={decision}
HISTORY_BLOB_FOUND={str(blob_found).lower()}
CANDIDATE_SYNTAX_OK={str(syntax_ok).lower()}
RESTORE_PERFORMED=false
ERA57_OPENED=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={nxt}''');m=sec(m,'## 10 NEXT SAFE STEP',f'''```text
NEXT_SAFE_STEP={nxt}
```

Follow the bounded raw-runner decision. No unrelated runtime changes.''');MASTER.write_text(m,encoding='utf-8')
    h=HANDOFF.read_text(encoding='utf-8');h=sec(h,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}
LAST_RESULT={result}
LAST_ARTIFACT={rel}
DECISION={decision}
RESTORE_PERFORMED=false
ERA57_OPENED=false''');h=sec(h,'## 07 ALLOWED NEXT DECISIONS',f'''- Raw repair decision: `{decision}`.
- Restore performed: `false`.
- ERA57 opened: `false`.
- Production mutation: `false`.

NEXT_SAFE_STEP={nxt}''');HANDOFF.write_text(h,encoding='utf-8')

    for x in (RUNTIME,HISTORY,ARTIFACT):load(x)
    git('add','-A');chk=run(['git','diff','--cached','--check'],check=False)
    if chk.returncode:print(chk.stdout,end='');print(chk.stderr,end='');raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m','PRE_ERA57_RAW_REPAIR_DECISION | '+('OK' if decision.startswith('AUTHORIZE_') else 'WARN')+' | BOUNDED_HISTORY_REVIEW')
    print('PRE_ERA57_RAW_REPAIR_DECISION=SUCCESS');print('HISTORY_BLOB_FOUND='+str(blob_found).lower());print('CANDIDATE_SYNTAX_OK='+str(syntax_ok).lower());print('DECISION='+decision);print('RESTORE_PERFORMED=false');print('ERA57_OPENED=false');print('PRODUCTION_MUTATION=false');print('NEXT_SAFE_STEP='+nxt);print('LOCAL_COMMIT='+git('rev-parse','HEAD'));return 0

if __name__=='__main__':raise SystemExit(main())
