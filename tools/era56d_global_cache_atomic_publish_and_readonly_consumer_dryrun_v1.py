#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, os, shutil, sqlite3, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
WORK='ERA56D_GLOBAL_CACHE_ATOMIC_PUBLISH_AND_READONLY_CONSUMER_DRYRUN'
RESULT='OK_ERA56D_ATOMIC_PUBLISH_READONLY_CONSUMER_FAIL_CLOSED'
NEXT='ERA56E_GLOBAL_CACHE_BOUNDED_RUNTIME_BINDING_READINESS_DECISION'
SUBJECT='ERA56D | OK | ATOMIC_PUBLISH_READONLY_CONSUMER'
SEAL_TAG='ERA55_FINAL_SEAL';SEAL_COMMIT='f22ce4f07788ec7fbe22a72f872467705b72db5a'
RUNTIME=ROOT/'PROJECT_RUNTIME.json';ROADMAP=ROOT/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md';HANDOFF=ROOT/'07_PROJECT_HANDOFF.md';HISTORY=ROOT/'PROJECT_HISTORY.json';ALMANAC=ROOT/'04_ALMANAC.md'
TK_AI=ROOT/'reports/LATEST_TK_AI_HANDOFF.md';MACHINE=ROOT/'data/control/latest_tk_machine_state.json'
ARTIFACT=ROOT/'data/control/era56d_global_cache_atomic_publish_and_readonly_consumer_dryrun_v1.json'

SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE cache_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE cache_records(record_uid TEXT PRIMARY KEY,payload_sha256 TEXT NOT NULL,payload_json TEXT NOT NULL);
CREATE TABLE cache_snapshot_identity(snapshot_uid TEXT PRIMARY KEY,logical_content_sha256 TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('READY','STALE','STALE_UNKNOWN','INVALID')));
'''

def run(args:list[str],check:bool=True):return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check,timeout=120)
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
def find_era(roadmap:dict[str,Any],era_id:str)->dict[str,Any]:
    for v in roadmap.get('versions',[]):
        if v.get('id')=='V3':
            for e in v.get('children',[]):
                if e.get('id')==era_id:return e
    raise RuntimeError('ERA_NOT_FOUND:'+era_id)
def logical_hash(records:list[dict[str,str]])->str:
    return hashlib.sha256('\n'.join(f"{r['record_uid']}|{r['payload_sha256']}" for r in sorted(records,key=lambda x:x['record_uid'])).encode()).hexdigest()
def build_candidate(path:Path,records:list[dict[str,str]],status:str='READY')->dict[str,str]:
    con=sqlite3.connect(path)
    try:
        con.executescript(SCHEMA);content=logical_hash(records);uid=hashlib.sha256(f'era56d|v1|{content}'.encode()).hexdigest()
        con.execute('BEGIN IMMEDIATE');con.executemany('INSERT INTO cache_records VALUES(:record_uid,:payload_sha256,:payload_json)',records)
        con.executemany('INSERT INTO cache_meta VALUES(?,?)',[('schema_version','era56_cache_v1'),('production_binding','false'),('atomic_publish','true')])
        con.execute('INSERT INTO cache_snapshot_identity VALUES(?,?,?)',(uid,content,status));con.commit()
        if con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('CANDIDATE_INTEGRITY_FAILED')
        return {'snapshot_uid':uid,'logical_content_sha256':content}
    finally:con.close()
def publish(candidate:Path,published:Path):
    with candidate.open('rb') as src:
        os.fsync(src.fileno())
    os.replace(candidate,published)
    fd=os.open(str(published.parent),os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
def consume(path:Path,expected_uid:str,expected_hash:str)->dict[str,Any]:
    con=sqlite3.connect(f'file:{path.as_posix()}?mode=ro',uri=True,timeout=5)
    try:
        uid,content,status=con.execute('SELECT snapshot_uid,logical_content_sha256,status FROM cache_snapshot_identity').fetchone()
        rows=con.execute('SELECT record_uid,payload_sha256,payload_json FROM cache_records ORDER BY record_uid').fetchall()
        calc=hashlib.sha256('\n'.join(f'{r[0]}|{r[1]}' for r in rows).encode()).hexdigest()
        if status!='READY':raise RuntimeError('CONSUMER_REJECTED_'+status)
        if uid!=expected_uid or content!=expected_hash or calc!=expected_hash:raise RuntimeError('CONSUMER_HASH_MISMATCH')
        return {'accepted':True,'record_count':len(rows),'snapshot_uid':uid,'logical_content_sha256':content,'status':status}
    finally:con.close()
def expect_reject(path:Path,uid:str,content:str,reason:str)->bool:
    try:consume(path,uid,content)
    except RuntimeError as exc:return reason in str(exc)
    return False


def main()->int:
    if git('status','--short'):raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected:raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list','-n1',SEAL_TAG)!=SEAL_COMMIT:raise RuntimeError('ERA55_SEAL_MISMATCH')
    runtime=load(RUNTIME);roadmap=load(ROADMAP);p=runtime['canonical_runtime_pointer'];e56=find_era(roadmap,'ERA56')
    checks={'era56_open':p.get('era56_opened') is True and e56.get('status')=='OPEN','era56c_ready':p.get('era56c_record_mapping_validated') is True and p.get('era56c_logical_parity') is True and p.get('era56c_stale_detection') is True,'next_step_matches':p.get('next_safe_step')==WORK,'production_apply_blocked':p.get('era56_production_apply_authorized') is False}
    if not all(checks.values()):raise RuntimeError('ERA56D_CHECK_FAILED:'+','.join(k for k,v in checks.items() if not v))
    ts=datetime.now(timezone.utc).isoformat();tmp=Path(tempfile.mkdtemp(prefix='era56d_',dir='/tmp'));candidate=tmp/'candidate.sqlite';published=tmp/'published.sqlite'
    records=[]
    for i,payload in enumerate(({'kind':'news','value':'alpha'},{'kind':'whale','value':'beta'},{'kind':'risk','value':'gamma'})):
        text=json.dumps(payload,sort_keys=True,separators=(',',':'));ph=hashlib.sha256(text.encode()).hexdigest();records.append({'record_uid':hashlib.sha256(f'{i}|{ph}'.encode()).hexdigest(),'payload_sha256':ph,'payload_json':text})
    try:
        identity=build_candidate(candidate,records);publish(candidate,published)
        accepted=consume(published,identity['snapshot_uid'],identity['logical_content_sha256'])
        con=sqlite3.connect(published);con.execute("UPDATE cache_snapshot_identity SET status='STALE'");con.commit();con.close()
        stale_rejected=expect_reject(published,identity['snapshot_uid'],identity['logical_content_sha256'],'CONSUMER_REJECTED_STALE')
        if not stale_rejected:raise RuntimeError('STALE_FAIL_CLOSED_FAILED')
        published.unlink();identity=build_candidate(candidate,records);publish(candidate,published)
        hash_rejected=expect_reject(published,identity['snapshot_uid'],'0'*64,'CONSUMER_HASH_MISMATCH')
        if not hash_rejected:raise RuntimeError('HASH_FAIL_CLOSED_FAILED')
        rel=str(ARTIFACT.relative_to(ROOT))
        dump(ARTIFACT,{'schema':'era56d_global_cache_atomic_publish_and_readonly_consumer_dryrun_v1','timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_DRYRUN_VERIFIED','result':RESULT,'checks':checks,'atomic_publish_verified':True,'readonly_consumer_verified':True,'consumer_accept_result':accepted,'stale_snapshot_rejected':stale_rejected,'hash_mismatch_rejected':hash_rejected,'temp_artifacts_retained':False,'production_mutation':False,'production_binding':False,'service_timer_binding':False,'panel_binding':False,'next_safe_step':NEXT})
    finally:shutil.rmtree(tmp,ignore_errors=True)
    runtime['current_problem']={'code':'ERA56E_BOUNDED_RUNTIME_BINDING_READINESS_DECISION_PENDING','severity':'P1','evidence':rel};p.update({'current_stage':'ERA56D_ATOMIC_PUBLISH_CONSUMER_VERIFIED','last_completed':WORK,'last_result':RESULT,'last_artifact':rel,'era56d_atomic_publish':True,'era56d_readonly_consumer':True,'era56d_fail_closed':True,'era56_production_apply_authorized':False,'next_safe_step':NEXT,'updated_at_utc':ts});runtime['current_state']={'project_status':'ACTIVE','runtime_status':'ERA56_OPEN_DESIGN_ONLY','mode':'ERA56D_ATOMIC_PUBLISH_CONSUMER_VERIFIED','last_action':{'task':WORK,'result':RESULT,'artifact':rel,'timestamp':ts},'current_problem':runtime['current_problem'],'next_safe_step':{'id':NEXT,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts};runtime['current_work_unit']={'id':WORK,'status':'CLOSED_DRYRUN_VERIFIED','result':RESULT,'artifact':rel,'production_mutation':False,'next_step':NEXT};dump(RUNTIME,runtime)
    e56.update({'active_stage':'ERA56D_ATOMIC_PUBLISH_CONSUMER_VERIFIED','last_completed_substep':WORK,'last_result':RESULT,'next_safe_step':NEXT,'atomic_publish_validated':True,'readonly_consumer_validated':True,'fail_closed_validated':True,'production_apply_authorized':False});dump(ROADMAP,roadmap)
    master=MASTER.read_text(encoding='utf-8');master=sec(master,'## 02 CURRENT MAJOR-LINE POSITION',f'''```text\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nERA56_STATUS=OPEN_BOUNDED_DESIGN_ONLY\nCURRENT_STAGE=ERA56D_ATOMIC_PUBLISH_CONSUMER_VERIFIED\nLAST_COMPLETED_SUBSTEP={WORK}\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\n```''');master=sec(master,'## 03 LAST VERIFIED WORK',f'''```text\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nLAST_ARTIFACT={rel}\nWORK_UNIT_STATUS=CLOSED_DRYRUN_VERIFIED\nATOMIC_PUBLISH=true\nREADONLY_CONSUMER=true\nFAIL_CLOSED=true\nPRODUCTION_MUTATION=false\n```\n\nNEXT_SAFE_STEP={NEXT}''');master=sec(master,'## 10 NEXT SAFE STEP',f'''```text\nNEXT_SAFE_STEP={NEXT}\n```\n\nDecide whether a bounded runtime binding test is justified. No production binding is authorized by ERA56D.''');MASTER.write_text(master,encoding='utf-8')
    hand=HANDOFF.read_text(encoding='utf-8');hand=sec(hand,'## 02 CURRENT CONTINUATION CHECKPOINT',f'''PROJECT_STATUS=ACTIVE_ERA56_GLOBAL_INTELLIGENCE_CACHE\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nERA56_STATUS=OPEN_BOUNDED_DESIGN_ONLY\nCURRENT_STAGE=ERA56D_ATOMIC_PUBLISH_CONSUMER_VERIFIED\nLAST_COMPLETED_SUBSTEP={WORK}\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\nCURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD''');hand=sec(hand,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nLAST_ARTIFACT={rel}\nWORK_UNIT_STATUS=CLOSED_DRYRUN_VERIFIED\nCURRENT_PROBLEM=ERA56E_BOUNDED_RUNTIME_BINDING_READINESS_DECISION_PENDING''');hand=sec(hand,'## 07 ALLOWED NEXT DECISIONS',f'''- Atomic publish: `VALIDATED`.\n- Read-only consumer: `VALIDATED`.\n- Stale/hash mismatch fail-closed: `VALIDATED`.\n- Production binding: `BLOCKED`.\n\nNEXT_SAFE_STEP={NEXT}''');HANDOFF.write_text(hand,encoding='utf-8')
    history=load(HISTORY);events=history.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')==WORK for x in events):events.append({'event_id':WORK,'timestamp_utc':ts,'era':'ERA56','status':'CLOSED_DRYRUN_VERIFIED','result':RESULT,'artifact':rel,'production_mutation':False,'next_safe_step':NEXT})
    history['updated_at']=ts;history['updated_at_utc']=ts;dump(HISTORY,history)
    marker='## ERA56D GLOBAL CACHE ATOMIC PUBLISH AND READONLY CONSUMER DRYRUN';alm=ALMANAC.read_text(encoding='utf-8')
    if marker not in alm:ALMANAC.write_text(alm.rstrip()+f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_DRYRUN_VERIFIED`\n- Result: `{RESULT}`\n- Atomic publish: `true`\n- Read-only consumer: `true`\n- Fail-closed: `true`\n- Production mutation: `false`\n- Next safe step: `{NEXT}`\n''',encoding='utf-8')
    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nSTATE_SYNC_UTC={ts}\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nCURRENT_STAGE=ERA56D_ATOMIC_PUBLISH_CONSUMER_VERIFIED\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\nNEXT_SAFE_STEP={NEXT}\n''',encoding='utf-8')
    machine=load(MACHINE);machine['created_at_utc']=ts;machine['collect_mode']='canonical_sync_snapshot_no_tk_machine';machine['current_state']={'authority':'PROJECT_RUNTIME.json','runtime_status':'ERA56_OPEN_DESIGN_ONLY','active_work_unit':{'id':WORK,'status':'CLOSED_DRYRUN_VERIFIED','artifact':rel},'next_safe_step':{'name':NEXT,'status':'READY'},'last_action':{'timestamp':ts,'task':WORK,'result':RESULT,'artifact':rel}};machine['known_facts']={'era56_opened':True,'era56_stage':'ERA56D_ATOMIC_PUBLISH_CONSUMER_VERIFIED','atomic_publish_validated':True,'readonly_consumer_validated':True,'fail_closed_validated':True,'era56_production_apply_authorized':False,'production_mutation':False};dump(MACHINE,machine)
    for path in (RUNTIME,ROADMAP,HISTORY,MACHINE,ARTIFACT):load(path)
    if git('rev-list','-n1',SEAL_TAG)!=SEAL_COMMIT:raise RuntimeError('ERA55_SEAL_CHANGED')
    git('add','-A');check=run(['git','diff','--cached','--check'],check=False)
    if check.returncode!=0:print(check.stdout,end='');print(check.stderr,end='');raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m',SUBJECT)
    print('ERA56D_DRYRUN=SUCCESS');print('ATOMIC_PUBLISH=true');print('READONLY_CONSUMER=true');print('STALE_REJECTED=true');print('HASH_MISMATCH_REJECTED=true');print('ERA56_PRODUCTION_APPLY_AUTHORIZED=false');print('PRODUCTION_MUTATION=false');print('NEXT_SAFE_STEP='+NEXT);print('LOCAL_COMMIT='+git('rev-parse','HEAD'));return 0
if __name__=='__main__':raise SystemExit(main())
