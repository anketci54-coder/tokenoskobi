#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
WORK='ERA56B_GLOBAL_CACHE_READONLY_SCHEMA_AND_TEMP_COPY_BUILD'
RESULT='OK_ERA56B_ISOLATED_SCHEMA_TEMP_COPY_REBUILD_PARITY'
NEXT='ERA56C_GLOBAL_CACHE_RECORD_MAPPING_AND_LOGICAL_PARITY_TEST'
SUBJECT='ERA56B | OK | READONLY_SCHEMA_TEMP_COPY_BUILD'
SEAL_TAG='ERA55_FINAL_SEAL'
SEAL_COMMIT='f22ce4f07788ec7fbe22a72f872467705b72db5a'

RUNTIME=ROOT/'PROJECT_RUNTIME.json'
ROADMAP=ROOT/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md'
HANDOFF=ROOT/'07_PROJECT_HANDOFF.md'
HISTORY=ROOT/'PROJECT_HISTORY.json'
ALMANAC=ROOT/'04_ALMANAC.md'
TK_AI=ROOT/'reports/LATEST_TK_AI_HANDOFF.md'
MACHINE=ROOT/'data/control/latest_tk_machine_state.json'
ARTIFACT=ROOT/'data/control/era56b_global_cache_readonly_schema_and_temp_copy_build_v1.json'

DB_CANDIDATES=[
 ROOT/'data/tokenoskobi_clean_v1.sqlite',
 ROOT/'data/tokenoskobi.sqlite',
 ROOT/'data/tokenoskobi.db',
]

CACHE_SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE cache_meta(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE source_table_manifest(
  table_name TEXT PRIMARY KEY,
  row_count INTEGER NOT NULL CHECK(row_count>=0),
  schema_sha256 TEXT NOT NULL,
  source_db_sha256 TEXT NOT NULL,
  captured_at_utc TEXT NOT NULL
);
CREATE TABLE cache_snapshot_identity(
  snapshot_uid TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL,
  source_db_sha256 TEXT NOT NULL,
  source_version_vector_sha256 TEXT NOT NULL,
  logical_content_sha256 TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('READY','STALE','STALE_UNKNOWN','INVALID'))
);
'''


def run(args:list[str],check:bool=True):
    return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check,timeout=90)

def git(*args:str)->str:return run(['git',*args]).stdout.strip()
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(v,dict):raise RuntimeError('JSON_OBJECT_REQUIRED:'+str(p))
    return v

def dump(p:Path,v:dict[str,Any]):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=p.name+'.',dir=p.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as h:
            json.dump(v,h,ensure_ascii=False,indent=2,sort_keys=True);h.write('\n');h.flush();os.fsync(h.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

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

def choose_source()->Path:
    override=os.environ.get('TOKENOSKOBI_SOURCE_DB','').strip()
    candidates=[Path(override)] if override else DB_CANDIDATES
    for p in candidates:
        if p.is_file() and p.stat().st_size>0:return p.resolve()
    raise RuntimeError('SOURCE_DB_NOT_FOUND')

def readonly_uri(p:Path)->str:return f'file:{p.as_posix()}?mode=ro&immutable=0'

def backup_source(source:Path,target:Path)->None:
    src=sqlite3.connect(readonly_uri(source),uri=True,timeout=30)
    dst=sqlite3.connect(target)
    try:
        src.backup(dst,pages=256,sleep=0.01)
        if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('TEMP_BACKUP_INTEGRITY_FAILED')
    finally:
        dst.close();src.close()

def source_manifest(snapshot:Path,source_hash:str,captured:str)->list[dict[str,Any]]:
    con=sqlite3.connect(snapshot)
    try:
        tables=con.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        rows=[]
        for name,sql in tables:
            q='SELECT COUNT(*) FROM "'+name.replace('"','""')+'"'
            count=int(con.execute(q).fetchone()[0])
            rows.append({'table_name':name,'row_count':count,'schema_sha256':hashlib.sha256((sql or '').encode()).hexdigest(),'source_db_sha256':source_hash,'captured_at_utc':captured})
        return rows
    finally:con.close()

def logical_hash(rows:list[dict[str,Any]])->str:
    payload='\n'.join(f"{r['table_name']}|{r['row_count']}|{r['schema_sha256']}|{r['source_db_sha256']}" for r in rows)
    return hashlib.sha256(payload.encode()).hexdigest()

def build_cache(path:Path,rows:list[dict[str,Any]],source_hash:str,captured:str)->dict[str,Any]:
    if path.exists():path.unlink()
    con=sqlite3.connect(path)
    try:
        con.executescript(CACHE_SCHEMA)
        con.execute('BEGIN IMMEDIATE')
        con.executemany('INSERT INTO source_table_manifest(table_name,row_count,schema_sha256,source_db_sha256,captured_at_utc) VALUES(:table_name,:row_count,:schema_sha256,:source_db_sha256,:captured_at_utc)',rows)
        version_vector=hashlib.sha256('\n'.join(f"{r['table_name']}:{r['row_count']}:{r['schema_sha256']}" for r in rows).encode()).hexdigest()
        content=logical_hash(rows)
        uid=hashlib.sha256(f'era56b|v1|{source_hash}|{version_vector}|{content}'.encode()).hexdigest()
        con.executemany('INSERT INTO cache_meta(key,value) VALUES(?,?)',[
          ('schema_version','era56_cache_v1'),('source_authority','existing_runtime_db'),('production_binding','false'),('rebuildable','true')])
        con.execute('INSERT INTO cache_snapshot_identity VALUES(?,?,?,?,?,?,?)',(uid,'era56_cache_v1',source_hash,version_vector,content,captured,'READY'))
        con.commit()
        integrity=con.execute('PRAGMA integrity_check').fetchone()[0]
        fk=con.execute('PRAGMA foreign_key_check').fetchall()
        count=con.execute('SELECT COUNT(*) FROM source_table_manifest').fetchone()[0]
        identity=con.execute('SELECT snapshot_uid,source_version_vector_sha256,logical_content_sha256,status FROM cache_snapshot_identity').fetchone()
        return {'snapshot_uid':identity[0],'source_version_vector_sha256':identity[1],'logical_content_sha256':identity[2],'status':identity[3],'manifest_rows':count,'integrity_check':integrity,'foreign_key_violations':len(fk),'cache_bytes':path.stat().st_size}
    finally:con.close()


def main()->int:
    if git('status','--short'):raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected:raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list','-n1',SEAL_TAG)!=SEAL_COMMIT:raise RuntimeError('ERA55_SEAL_MISMATCH')

    runtime=load(RUNTIME);roadmap=load(ROADMAP);p=runtime['canonical_runtime_pointer'];e56=find_era(roadmap,'ERA56')
    checks={
      'era56_open':p.get('era56_opened') is True and e56.get('status')=='OPEN',
      'era56a_contract_locked':p.get('era56_contract_locked') is True and e56.get('ownership_contract_locked') is True and e56.get('overlap_contract_locked') is True and e56.get('rebuild_contract_locked') is True,
      'next_step_matches':p.get('next_safe_step')==WORK,
      'production_apply_blocked':p.get('era56_production_apply_authorized') is False,
      'writer_active':p.get('production_ledger_writer_active') is True,
      'runner_lock_enabled':p.get('runner_lock_enabled') is True,
    }
    if not all(checks.values()):raise RuntimeError('BUILD_CHECK_FAILED:'+','.join(k for k,v in checks.items() if not v))

    source=choose_source();source_hash_before=sha256_file(source);captured=datetime.now(timezone.utc).isoformat()
    tmpdir=Path(tempfile.mkdtemp(prefix='era56b_',dir='/tmp'))
    snapshot=tmpdir/'source_snapshot.sqlite';cache1=tmpdir/'global_cache_1.sqlite';cache2=tmpdir/'global_cache_2.sqlite'
    started=time.perf_counter()
    try:
        backup_source(source,snapshot)
        rows=source_manifest(snapshot,source_hash_before,captured)
        if not rows:raise RuntimeError('SOURCE_MANIFEST_EMPTY')
        first=build_cache(cache1,rows,source_hash_before,captured)
        second=build_cache(cache2,rows,source_hash_before,captured)
        source_hash_after=sha256_file(source)
        parity=first['snapshot_uid']==second['snapshot_uid'] and first['logical_content_sha256']==second['logical_content_sha256']
        if source_hash_before!=source_hash_after:raise RuntimeError('SOURCE_DB_CHANGED_DURING_BUILD')
        if not parity:raise RuntimeError('REBUILD_PARITY_FAILED')
        if first['integrity_check']!='ok' or first['foreign_key_violations']!=0:raise RuntimeError('CACHE_INTEGRITY_FAILED')
        elapsed=(time.perf_counter()-started)*1000
        rel=str(ARTIFACT.relative_to(ROOT))
        dump(ARTIFACT,{'schema':'era56b_global_cache_readonly_schema_and_temp_copy_build_v1','timestamp_utc':captured,'work_unit':WORK,'status':'CLOSED_TEMP_COPY_BUILD_VERIFIED','result':RESULT,'checks':checks,'source_db_path':str(source),'source_db_sha256_before':source_hash_before,'source_db_sha256_after':source_hash_after,'source_unchanged':True,'source_snapshot_bytes':snapshot.stat().st_size,'source_table_count':len(rows),'source_total_rows':sum(r['row_count'] for r in rows),'cache_build_1':first,'cache_build_2':second,'rebuild_parity':parity,'elapsed_ms':elapsed,'temp_root':str(tmpdir),'temp_artifacts_retained':False,'production_mutation':False,'production_binding':False,'service_timer_binding':False,'panel_binding':False,'next_safe_step':NEXT})
    finally:
        for x in (cache1,cache2,snapshot):
            if x.exists():x.unlink()
        tmpdir.rmdir()

    runtime['current_problem']={'code':'ERA56C_RECORD_MAPPING_AND_LOGICAL_PARITY_TEST_PENDING','severity':'P1','evidence':rel}
    p.update({'current_stage':'ERA56B_TEMP_COPY_BUILD_VERIFIED','last_completed':WORK,'last_result':RESULT,'last_artifact':rel,'era56b_schema_validated':True,'era56b_rebuild_parity':True,'era56_production_apply_authorized':False,'next_safe_step':NEXT,'updated_at_utc':captured})
    runtime['current_state']={'project_status':'ACTIVE','runtime_status':'ERA56_OPEN_DESIGN_ONLY','mode':'ERA56B_TEMP_COPY_BUILD_VERIFIED','last_action':{'task':WORK,'result':RESULT,'artifact':rel,'timestamp':captured},'current_problem':runtime['current_problem'],'next_safe_step':{'id':NEXT,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':captured}
    runtime['current_work_unit']={'id':WORK,'status':'CLOSED_TEMP_COPY_BUILD_VERIFIED','result':RESULT,'artifact':rel,'production_mutation':False,'next_step':NEXT}
    dump(RUNTIME,runtime)

    e56.update({'active_stage':'ERA56B_TEMP_COPY_BUILD_VERIFIED','last_completed_substep':WORK,'last_result':RESULT,'next_safe_step':NEXT,'readonly_schema_validated':True,'temp_copy_build_validated':True,'rebuild_parity_validated':True,'production_apply_authorized':False})
    dump(ROADMAP,roadmap)

    master=MASTER.read_text(encoding='utf-8');master=sec(master,'## 02 CURRENT MAJOR-LINE POSITION',f'''```text
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=OPEN_BOUNDED_DESIGN_ONLY
CURRENT_STAGE=ERA56B_TEMP_COPY_BUILD_VERIFIED
LAST_COMPLETED_SUBSTEP={WORK}
ERA56_PRODUCTION_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
```''');master=sec(master,'## 03 LAST VERIFIED WORK',f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_TEMP_COPY_BUILD_VERIFIED
SOURCE_DB_UNCHANGED=true
REBUILD_PARITY=true
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}''');master=sec(master,'## 10 NEXT SAFE STEP',f'''```text
NEXT_SAFE_STEP={NEXT}
```

Define actual record mapping into the isolated cache and prove logical parity without production binding.''');MASTER.write_text(master,encoding='utf-8')

    hand=HANDOFF.read_text(encoding='utf-8');hand=sec(hand,'## 02 CURRENT CONTINUATION CHECKPOINT',f'''PROJECT_STATUS=ACTIVE_ERA56_GLOBAL_INTELLIGENCE_CACHE
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=OPEN_BOUNDED_DESIGN_ONLY
CURRENT_STAGE=ERA56B_TEMP_COPY_BUILD_VERIFIED
LAST_COMPLETED_SUBSTEP={WORK}
ERA56_PRODUCTION_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD''');hand=sec(hand,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_TEMP_COPY_BUILD_VERIFIED
CURRENT_PROBLEM=ERA56C_RECORD_MAPPING_AND_LOGICAL_PARITY_TEST_PENDING''');hand=sec(hand,'## 07 ALLOWED NEXT DECISIONS',f'''- Isolated cache schema: `VALIDATED`.
- Temp-copy source snapshot: `VALIDATED`.
- Deterministic rebuild parity: `VALIDATED`.
- Production binding: `BLOCKED`.
- Next work: record mapping and logical parity in isolation.

NEXT_SAFE_STEP={NEXT}''');HANDOFF.write_text(hand,encoding='utf-8')

    hist=load(HISTORY);events=hist.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')==WORK for x in events):events.append({'event_id':WORK,'timestamp_utc':captured,'era':'ERA56','status':'CLOSED_TEMP_COPY_BUILD_VERIFIED','result':RESULT,'artifact':rel,'production_mutation':False,'next_safe_step':NEXT})
    hist['updated_at']=captured;hist['updated_at_utc']=captured;dump(HISTORY,hist)

    marker='## ERA56B GLOBAL CACHE READONLY SCHEMA AND TEMP COPY BUILD';alm=ALMANAC.read_text(encoding='utf-8')
    if marker not in alm:ALMANAC.write_text(alm.rstrip()+f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_TEMP_COPY_BUILD_VERIFIED`\n- Result: `{RESULT}`\n- Source DB unchanged: `true`\n- Rebuild parity: `true`\n- Production binding: `false`\n- Production mutation: `false`\n- Next safe step: `{NEXT}`\n''',encoding='utf-8')

    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nSTATE_SYNC_UTC={captured}\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nCURRENT_STAGE=ERA56B_TEMP_COPY_BUILD_VERIFIED\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nSOURCE_DB_UNCHANGED=true\nREBUILD_PARITY=true\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\nNEXT_SAFE_STEP={NEXT}\n''',encoding='utf-8')

    machine=load(MACHINE);machine['created_at_utc']=captured;machine['collect_mode']='canonical_sync_snapshot_no_tk_machine';machine['current_state']={'authority':'PROJECT_RUNTIME.json','runtime_status':'ERA56_OPEN_DESIGN_ONLY','active_work_unit':{'id':WORK,'status':'CLOSED_TEMP_COPY_BUILD_VERIFIED','artifact':rel},'next_safe_step':{'name':NEXT,'status':'READY'},'last_action':{'timestamp':captured,'task':WORK,'result':RESULT,'artifact':rel}};machine['known_facts']={'era56_stage':'ERA56B_TEMP_COPY_BUILD_VERIFIED','source_db_unchanged':True,'rebuild_parity':True,'era56_production_apply_authorized':False,'production_mutation':False};dump(MACHINE,machine)

    for path in (RUNTIME,ROADMAP,HISTORY,MACHINE,ARTIFACT):load(path)
    if git('rev-list','-n1',SEAL_TAG)!=SEAL_COMMIT:raise RuntimeError('ERA55_SEAL_CHANGED')
    git('add','-A');check=run(['git','diff','--cached','--check'],check=False)
    if check.returncode!=0:
        print(check.stdout,end='');print(check.stderr,end='');raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m',SUBJECT)
    print('ERA56B_BUILD=SUCCESS');print('SOURCE_DB_UNCHANGED=true');print('REBUILD_PARITY=true');print('ERA56_PRODUCTION_APPLY_AUTHORIZED=false');print('PRODUCTION_MUTATION=false');print('NEXT_SAFE_STEP='+NEXT);print('LOCAL_COMMIT='+git('rev-parse','HEAD'))
    return 0

if __name__=='__main__':raise SystemExit(main())
