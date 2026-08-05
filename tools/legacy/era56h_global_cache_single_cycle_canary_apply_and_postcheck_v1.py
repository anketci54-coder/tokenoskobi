#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, os, shutil, sqlite3, subprocess, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
WORK='ERA56H_GLOBAL_CACHE_SINGLE_CYCLE_CANARY_APPLY_AND_POSTCHECK'
RESULT='OK_SINGLE_CYCLE_CANARY_APPLIED_POSTCHECK_PASSED_UNBOUND'
NEXT='ERA56I_GLOBAL_CACHE_POST_CANARY_REVIEW_AND_RUNTIME_BINDING_DECISION'
SUBJECT='ERA56H | OK | SINGLE_CYCLE_CANARY_APPLY_AND_POSTCHECK'
TAG='ERA55_FINAL_SEAL';SEAL='f22ce4f07788ec7fbe22a72f872467705b72db5a'
RUNTIME=ROOT/'PROJECT_RUNTIME.json';ROADMAP=ROOT/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md';HANDOFF=ROOT/'07_PROJECT_HANDOFF.md';HISTORY=ROOT/'PROJECT_HISTORY.json';ALMANAC=ROOT/'04_ALMANAC.md'
TK_AI=ROOT/'reports/LATEST_TK_AI_HANDOFF.md';MACHINE=ROOT/'data/control/latest_tk_machine_state.json'
ARTIFACT=ROOT/'data/control/era56h_global_cache_single_cycle_canary_apply_and_postcheck_v1.json'
DB_CANDIDATES=[ROOT/'data/tokenoskobi_clean_v1.sqlite',ROOT/'data/tokenoskobi.sqlite',ROOT/'data/tokenoskobi.db']
CANARY_ROOT=Path('/run/tokenoskobi/era56h_canary')
CANARY_DB=CANARY_ROOT/'global_cache_canary.sqlite'
CANARY_TMP=CANARY_ROOT/'global_cache_canary.sqlite.tmp'

SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE cache_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE cache_table_manifest(table_name TEXT PRIMARY KEY,row_count INTEGER NOT NULL,logical_sha256 TEXT NOT NULL);
CREATE TABLE cache_snapshot(snapshot_uid TEXT PRIMARY KEY,source_sha256 TEXT NOT NULL,logical_sha256 TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('READY','STALE','INVALID')));
'''

def run(args:list[str],check:bool=True): return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check,timeout=120)
def git(*args:str)->str: return run(['git',*args]).stdout.strip()
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(v,dict): raise RuntimeError('JSON_OBJECT_REQUIRED:'+str(p))
    return v
def dump(p:Path,v:dict[str,Any]):
    p.parent.mkdir(parents=True,exist_ok=True); fd,tmp=tempfile.mkstemp(prefix=p.name+'.',dir=p.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as h:
            json.dump(v,h,ensure_ascii=False,indent=2,sort_keys=True); h.write('\n'); h.flush(); os.fsync(h.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def sec(text:str,heading:str,body:str)->str:
    s=text.find(heading)
    if s<0: raise RuntimeError('HEADING_MISSING:'+heading)
    e=text.find('\n## ',s+len(heading)); e=len(text) if e<0 else e
    return text[:s]+heading+'\n\n'+body.rstrip()+'\n'+text[e:]
def era(roadmap:dict[str,Any],era_id:str)->dict[str,Any]:
    for v in roadmap.get('versions',[]):
        if v.get('id')=='V3':
            for e in v.get('children',[]):
                if e.get('id')==era_id:return e
    raise RuntimeError('ERA_NOT_FOUND:'+era_id)
def choose_source()->Path:
    override=os.environ.get('TOKENOSKOBI_SOURCE_DB','').strip(); choices=[Path(override)] if override else DB_CANDIDATES
    for p in choices:
        if p.is_file() and p.stat().st_size>0:return p.resolve()
    raise RuntimeError('SOURCE_DB_NOT_FOUND')
def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def q(name:str)->str:return '"'+name.replace('"','""')+'"'
def snapshot_manifest(source:Path)->tuple[list[tuple[str,int,str]],str]:
    uri=f'file:{source.as_posix()}?mode=ro'
    con=sqlite3.connect(uri,uri=True,timeout=30)
    try:
        tables=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        out=[]; total=[]
        for name in tables:
            cur=con.execute('SELECT * FROM '+q(name)); cols=[d[0] for d in cur.description or []]; rows=[]
            for row in cur:
                vals=[]
                for v in row:
                    if isinstance(v,bytes): vals.append({'bytes_sha256':hashlib.sha256(v).hexdigest(),'len':len(v)})
                    else: vals.append(v)
                payload=json.dumps({'columns':cols,'values':vals},ensure_ascii=False,sort_keys=True,separators=(',',':'))
                rows.append(hashlib.sha256(payload.encode()).hexdigest())
            rows.sort(); logical=hashlib.sha256('\n'.join(rows).encode()).hexdigest(); out.append((name,len(rows),logical)); total.append(f'{name}|{len(rows)}|{logical}')
        if not out: raise RuntimeError('EMPTY_SOURCE_MANIFEST')
        return out,hashlib.sha256('\n'.join(total).encode()).hexdigest()
    finally: con.close()
def build_atomic(source:Path,source_sha:str,manifest:list[tuple[str,int,str]],logical:str)->dict[str,Any]:
    CANARY_ROOT.mkdir(parents=True,exist_ok=True)
    for p in (CANARY_TMP,CANARY_DB):
        if p.exists(): p.unlink()
    con=sqlite3.connect(CANARY_TMP)
    try:
        con.executescript(SCHEMA); con.execute('BEGIN IMMEDIATE')
        con.executemany('INSERT INTO cache_table_manifest VALUES(?,?,?)',manifest)
        uid=hashlib.sha256(f'era56h|{source_sha}|{logical}'.encode()).hexdigest()
        con.executemany('INSERT INTO cache_meta VALUES(?,?)',[('schema_version','era56_cache_v1'),('source_authority','existing_runtime_db'),('runtime_binding','false'),('cycle_scope','single')])
        con.execute('INSERT INTO cache_snapshot VALUES(?,?,?,?)',(uid,source_sha,logical,'READY')); con.commit()
        if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok': raise RuntimeError('CACHE_INTEGRITY_FAILED')
    finally: con.close()
    os.replace(CANARY_TMP,CANARY_DB)
    return {'snapshot_uid':uid,'cache_sha256':sha256_file(CANARY_DB),'cache_bytes':CANARY_DB.stat().st_size}
def readonly_postcheck(expected_source_sha:str,expected_logical:str)->dict[str,Any]:
    uri=f'file:{CANARY_DB.as_posix()}?mode=ro'
    con=sqlite3.connect(uri,uri=True,timeout=10)
    try:
        row=con.execute('SELECT snapshot_uid,source_sha256,logical_sha256,status FROM cache_snapshot').fetchone()
        if not row: raise RuntimeError('CACHE_SNAPSHOT_MISSING')
        uid,source_sha,logical,status=row
        if status!='READY': raise RuntimeError('CACHE_NOT_READY')
        if source_sha!=expected_source_sha or logical!=expected_logical: raise RuntimeError('CACHE_PARITY_MISMATCH')
        tables=con.execute('SELECT COUNT(*),COALESCE(SUM(row_count),0) FROM cache_table_manifest').fetchone()
        return {'snapshot_uid':uid,'table_count':tables[0],'source_row_count':tables[1],'status':status,'readonly_consumer':True}
    finally: con.close()
def unbind_cleanup():
    for p in (CANARY_TMP,CANARY_DB):
        if p.exists(): p.unlink()
    try: CANARY_ROOT.rmdir()
    except OSError: pass

def main()->int:
    if git('status','--short'): raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected: raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list','-n1',TAG)!=SEAL: raise RuntimeError('ERA55_SEAL_MISMATCH')
    runtime=load(RUNTIME); roadmap=load(ROADMAP); p=runtime['canonical_runtime_pointer']; e56=era(roadmap,'ERA56')
    checks={
      'era56_open':p.get('era56_opened') is True and e56.get('status')=='OPEN',
      'era56g_authorized':p.get('era56_single_cycle_canary_apply_authorized') is True,
      'next_step_matches':p.get('next_safe_step')==WORK,
      'runtime_binding_blocked':p.get('era56_runtime_binding_authorized') is False,
      'production_apply_blocked':p.get('era56_production_apply_authorized') is False,
      'runner_lock_enabled':p.get('runner_lock_enabled') is True,
      'writer_active':p.get('production_ledger_writer_active') is True,
      'fail_closed_verified':p.get('era56d_fail_closed') is True,
    }
    if not all(checks.values()): raise RuntimeError('CANARY_CHECK_FAILED:'+','.join(k for k,v in checks.items() if not v))

    source=choose_source(); source_before=sha256_file(source); started=time.perf_counter(); unbind_cleanup()
    try:
        manifest,logical=snapshot_manifest(source)
        publish=build_atomic(source,source_before,manifest,logical)
        consumer=readonly_postcheck(source_before,logical)
        source_after=sha256_file(source)
        if source_before!=source_after: raise RuntimeError('SOURCE_DB_CHANGED')
        ghost_rows=0
        con=sqlite3.connect(f'file:{CANARY_DB.as_posix()}?mode=ro',uri=True)
        try: ghost_rows=con.execute("SELECT COUNT(*) FROM cache_snapshot WHERE status!='READY'").fetchone()[0]
        finally: con.close()
        if ghost_rows!=0: raise RuntimeError('GHOST_OR_STALE_ROWS_FOUND')
        elapsed=round((time.perf_counter()-started)*1000,3)
        ts=datetime.now(timezone.utc).isoformat(); rel=str(ARTIFACT.relative_to(ROOT))
        evidence={'schema':'era56h_global_cache_single_cycle_canary_apply_and_postcheck_v1','timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_CANARY_PASSED_UNBOUND','result':RESULT,'checks':checks,'source_db_path':str(source),'source_sha256_before':source_before,'source_sha256_after':source_after,'source_db_unchanged':True,'publish':publish,'consumer_postcheck':consumer,'ghost_or_stale_rows':ghost_rows,'elapsed_ms':elapsed,'single_cycle_only':True,'canary_unbound_after_postcheck':True,'runtime_binding_authorized':False,'production_apply_authorized':False,'automatic_promotion':False,'production_mutation':False,'next_safe_step':NEXT}
    finally:
        unbind_cleanup()
    if CANARY_DB.exists() or CANARY_TMP.exists(): raise RuntimeError('CANARY_UNBIND_FAILED')
    dump(ARTIFACT,evidence)

    runtime['current_problem']={'code':'ERA56I_POST_CANARY_REVIEW_AND_RUNTIME_BINDING_DECISION_PENDING','severity':'P1','evidence':rel}
    p.update({'current_stage':'ERA56H_SINGLE_CYCLE_CANARY_PASSED_UNBOUND','last_completed':WORK,'last_result':RESULT,'last_artifact':rel,'era56h_canary_passed':True,'era56h_canary_unbound':True,'era56_single_cycle_canary_apply_authorized':False,'era56_runtime_binding_authorized':False,'era56_production_apply_authorized':False,'next_safe_step':NEXT,'updated_at_utc':ts})
    runtime['current_state']={'project_status':'ACTIVE','runtime_status':'ERA56_OPEN_CANARY_VERIFIED_UNBOUND','mode':'ERA56H_SINGLE_CYCLE_CANARY_PASSED_UNBOUND','last_action':{'task':WORK,'result':RESULT,'artifact':rel,'timestamp':ts},'current_problem':runtime['current_problem'],'next_safe_step':{'id':NEXT,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts}
    runtime['current_work_unit']={'id':WORK,'status':'CLOSED_CANARY_PASSED_UNBOUND','result':RESULT,'artifact':rel,'production_mutation':False,'next_step':NEXT}; dump(RUNTIME,runtime)
    e56.update({'active_stage':'ERA56H_SINGLE_CYCLE_CANARY_PASSED_UNBOUND','last_completed_substep':WORK,'last_result':RESULT,'next_safe_step':NEXT,'single_cycle_canary_passed':True,'canary_unbound':True,'runtime_binding_authorized':False,'production_apply_authorized':False}); dump(ROADMAP,roadmap)

    master=MASTER.read_text(encoding='utf-8'); master=sec(master,'## 02 CURRENT MAJOR-LINE POSITION',f'''```text
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=OPEN_CANARY_VERIFIED_UNBOUND
CURRENT_STAGE=ERA56H_SINGLE_CYCLE_CANARY_PASSED_UNBOUND
LAST_COMPLETED_SUBSTEP={WORK}
ERA56_SINGLE_CYCLE_CANARY_PASSED=true
ERA56_CANARY_UNBOUND=true
ERA56_RUNTIME_BINDING_AUTHORIZED=false
ERA56_PRODUCTION_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
```'''); master=sec(master,'## 03 LAST VERIFIED WORK',f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_CANARY_PASSED_UNBOUND
SOURCE_DB_UNCHANGED=true
GHOST_OR_STALE_ROWS=0
AUTOMATIC_PROMOTION=false
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}'''); master=sec(master,'## 10 NEXT SAFE STEP',f'''```text
NEXT_SAFE_STEP={NEXT}
```

Review canary evidence and decide whether any future runtime binding is justified. No automatic promotion.'''); MASTER.write_text(master,encoding='utf-8')
    hand=HANDOFF.read_text(encoding='utf-8'); hand=sec(hand,'## 02 CURRENT CONTINUATION CHECKPOINT',f'''PROJECT_STATUS=ACTIVE_ERA56_GLOBAL_INTELLIGENCE_CACHE
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=OPEN_CANARY_VERIFIED_UNBOUND
CURRENT_STAGE=ERA56H_SINGLE_CYCLE_CANARY_PASSED_UNBOUND
LAST_COMPLETED_SUBSTEP={WORK}
ERA56_RUNTIME_BINDING_AUTHORIZED=false
ERA56_PRODUCTION_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD'''); hand=sec(hand,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_CANARY_PASSED_UNBOUND
CURRENT_PROBLEM=ERA56I_POST_CANARY_REVIEW_AND_RUNTIME_BINDING_DECISION_PENDING'''); hand=sec(hand,'## 07 ALLOWED NEXT DECISIONS',f'''- Single-cycle canary: `PASSED`.
- Canary binding: `REMOVED`.
- Runtime binding: `BLOCKED`.
- Production apply: `BLOCKED`.
- Automatic promotion: `BLOCKED`.

NEXT_SAFE_STEP={NEXT}'''); HANDOFF.write_text(hand,encoding='utf-8')
    history=load(HISTORY); events=history.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')==WORK for x in events): events.append({'event_id':WORK,'timestamp_utc':ts,'era':'ERA56','status':'CLOSED_CANARY_PASSED_UNBOUND','result':RESULT,'artifact':rel,'source_db_unchanged':True,'ghost_or_stale_rows':0,'runtime_binding_authorized':False,'production_mutation':False,'next_safe_step':NEXT})
    history['updated_at']=ts; history['updated_at_utc']=ts; dump(HISTORY,history)
    marker='## ERA56H GLOBAL CACHE SINGLE CYCLE CANARY APPLY AND POSTCHECK'; alm=ALMANAC.read_text(encoding='utf-8')
    if marker not in alm: ALMANAC.write_text(alm.rstrip()+f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_CANARY_PASSED_UNBOUND`\n- Result: `{RESULT}`\n- Source DB unchanged: `true`\n- Ghost or stale rows: `0`\n- Canary unbound: `true`\n- Runtime binding authorized: `false`\n- Production mutation: `false`\n- Next safe step: `{NEXT}`\n''',encoding='utf-8')
    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nSTATE_SYNC_UTC={ts}\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nCURRENT_STAGE=ERA56H_SINGLE_CYCLE_CANARY_PASSED_UNBOUND\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nSOURCE_DB_UNCHANGED=true\nGHOST_OR_STALE_ROWS=0\nCANARY_UNBOUND=true\nERA56_RUNTIME_BINDING_AUTHORIZED=false\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\nNEXT_SAFE_STEP={NEXT}\n''',encoding='utf-8')
    machine=load(MACHINE); machine['created_at_utc']=ts; machine['collect_mode']='canonical_sync_snapshot_no_tk_machine'; machine['current_state']={'authority':'PROJECT_RUNTIME.json','runtime_status':'ERA56_OPEN_CANARY_VERIFIED_UNBOUND','active_work_unit':{'id':WORK,'status':'CLOSED_CANARY_PASSED_UNBOUND','artifact':rel},'next_safe_step':{'name':NEXT,'status':'READY'},'last_action':{'timestamp':ts,'task':WORK,'result':RESULT,'artifact':rel}}; machine['known_facts']={'era56_opened':True,'era56_stage':'ERA56H_SINGLE_CYCLE_CANARY_PASSED_UNBOUND','single_cycle_canary_passed':True,'canary_unbound':True,'source_db_unchanged':True,'ghost_or_stale_rows':0,'runtime_binding_authorized':False,'production_apply_authorized':False,'production_mutation':False}; dump(MACHINE,machine)

    for path in (RUNTIME,ROADMAP,HISTORY,MACHINE,ARTIFACT): load(path)
    if git('rev-list','-n1',TAG)!=SEAL: raise RuntimeError('ERA55_SEAL_CHANGED')
    git('add','-A'); check=run(['git','diff','--cached','--check'],check=False)
    if check.returncode!=0: print(check.stdout,end=''); print(check.stderr,end=''); raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m',SUBJECT)
    print('ERA56H_CANARY=SUCCESS'); print('SOURCE_DB_UNCHANGED=true'); print('GHOST_OR_STALE_ROWS=0'); print('CANARY_UNBOUND=true'); print('RUNTIME_BINDING_AUTHORIZED=false'); print('PRODUCTION_APPLY_AUTHORIZED=false'); print('AUTOMATIC_PROMOTION=false'); print('PRODUCTION_MUTATION=false'); print('NEXT_SAFE_STEP='+NEXT); print('LOCAL_COMMIT='+git('rev-parse','HEAD')); return 0

if __name__=='__main__': raise SystemExit(main())
