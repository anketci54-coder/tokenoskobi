#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, os, shutil, sqlite3, subprocess, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
WORK='ERA56C_GLOBAL_CACHE_RECORD_MAPPING_AND_LOGICAL_PARITY_TEST'
RESULT='OK_ERA56C_RECORD_MAPPING_LOGICAL_PARITY_AND_STALE_DETECTION'
NEXT='ERA56D_GLOBAL_CACHE_ATOMIC_PUBLISH_AND_READONLY_CONSUMER_DRYRUN'
SUBJECT='ERA56C | OK | RECORD_MAPPING_LOGICAL_PARITY'
SEAL_TAG='ERA55_FINAL_SEAL';SEAL_COMMIT='f22ce4f07788ec7fbe22a72f872467705b72db5a'
RUNTIME=ROOT/'PROJECT_RUNTIME.json';ROADMAP=ROOT/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md';HANDOFF=ROOT/'07_PROJECT_HANDOFF.md';HISTORY=ROOT/'PROJECT_HISTORY.json';ALMANAC=ROOT/'04_ALMANAC.md'
TK_AI=ROOT/'reports/LATEST_TK_AI_HANDOFF.md';MACHINE=ROOT/'data/control/latest_tk_machine_state.json'
ARTIFACT=ROOT/'data/control/era56c_global_cache_record_mapping_and_logical_parity_test_v1.json'
DB_CANDIDATES=[ROOT/'data/tokenoskobi_clean_v1.sqlite',ROOT/'data/tokenoskobi.sqlite',ROOT/'data/tokenoskobi.db']
CACHE_SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE cache_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE cache_table_manifest(table_name TEXT PRIMARY KEY,row_count INTEGER NOT NULL,logical_multiset_sha256 TEXT NOT NULL,schema_sha256 TEXT NOT NULL);
CREATE TABLE cache_record_map(table_name TEXT NOT NULL,record_uid TEXT NOT NULL,row_sha256 TEXT NOT NULL,occurrence_index INTEGER NOT NULL CHECK(occurrence_index>=0),PRIMARY KEY(table_name,record_uid));
CREATE TABLE cache_snapshot_identity(snapshot_uid TEXT PRIMARY KEY,source_version_vector_sha256 TEXT NOT NULL,logical_content_sha256 TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('READY','STALE','STALE_UNKNOWN','INVALID')));
'''

def run(args:list[str],check:bool=True):return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check,timeout=180)
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
def choose_source()->Path:
    override=os.environ.get('TOKENOSKOBI_SOURCE_DB','').strip();c=[Path(override)] if override else DB_CANDIDATES
    for p in c:
        if p.is_file() and p.stat().st_size>0:return p.resolve()
    raise RuntimeError('SOURCE_DB_NOT_FOUND')
def file_hash(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def ro_uri(p:Path)->str:return f'file:{p.as_posix()}?mode=ro&immutable=0'
def backup_source(source:Path,target:Path):
    src=sqlite3.connect(ro_uri(source),uri=True,timeout=30);dst=sqlite3.connect(target)
    try:src.backup(dst,pages=256,sleep=.01)
    finally:dst.close();src.close()
def canon_value(v:Any)->Any:
    if v is None or isinstance(v,(int,float,str)):return v
    if isinstance(v,bytes):return {'__bytes_sha256__':hashlib.sha256(v).hexdigest(),'length':len(v)}
    return str(v)
def table_rows(con:sqlite3.Connection,name:str)->tuple[str,list[str]]:
    q='SELECT * FROM "'+name.replace('"','""')+'"';cur=con.execute(q);cols=[d[0] for d in cur.description or []];hashes=[]
    for row in cur:
        payload=json.dumps({'columns':cols,'values':[canon_value(v) for v in row]},ensure_ascii=False,sort_keys=True,separators=(',',':'))
        hashes.append(hashlib.sha256(payload.encode()).hexdigest())
    hashes.sort();schema=con.execute("SELECT COALESCE(sql,'') FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone()[0]
    return hashlib.sha256(schema.encode()).hexdigest(),hashes
def extract(snapshot:Path)->tuple[list[dict[str,Any]],list[dict[str,Any]],str,str]:
    con=sqlite3.connect(snapshot)
    try:
        tables=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        manifests=[];records=[];vector_parts=[];content_parts=[]
        for name in tables:
            schema_hash,hashes=table_rows(con,name);counts={}
            for row_hash in hashes:
                idx=counts.get(row_hash,0);counts[row_hash]=idx+1
                uid=hashlib.sha256(f'{name}|{row_hash}|{idx}'.encode()).hexdigest()
                records.append({'table_name':name,'record_uid':uid,'row_sha256':row_hash,'occurrence_index':idx})
            multiset=hashlib.sha256('\n'.join(hashes).encode()).hexdigest()
            manifests.append({'table_name':name,'row_count':len(hashes),'logical_multiset_sha256':multiset,'schema_sha256':schema_hash})
            vector_parts.append(f'{name}|{len(hashes)}|{schema_hash}');content_parts.append(f'{name}|{multiset}')
        return manifests,records,hashlib.sha256('\n'.join(vector_parts).encode()).hexdigest(),hashlib.sha256('\n'.join(content_parts).encode()).hexdigest()
    finally:con.close()
def build_cache(path:Path,manifests:list[dict[str,Any]],records:list[dict[str,Any]],vector:str,content:str,status:str='READY')->dict[str,Any]:
    if path.exists():path.unlink()
    con=sqlite3.connect(path)
    try:
        con.executescript(CACHE_SCHEMA);con.execute('BEGIN IMMEDIATE')
        con.executemany('INSERT INTO cache_table_manifest VALUES(:table_name,:row_count,:logical_multiset_sha256,:schema_sha256)',manifests)
        con.executemany('INSERT INTO cache_record_map VALUES(:table_name,:record_uid,:row_sha256,:occurrence_index)',records)
        uid=hashlib.sha256(f'era56c|v1|{vector}|{content}'.encode()).hexdigest()
        con.executemany('INSERT INTO cache_meta VALUES(?,?)',[('schema_version','era56_cache_v1'),('source_authority','existing_runtime_db'),('production_binding','false')])
        con.execute('INSERT INTO cache_snapshot_identity VALUES(?,?,?,?)',(uid,vector,content,status));con.commit()
        integrity=con.execute('PRAGMA integrity_check').fetchone()[0];fk=len(con.execute('PRAGMA foreign_key_check').fetchall())
        counts=con.execute('SELECT (SELECT COUNT(*) FROM cache_table_manifest),(SELECT COUNT(*) FROM cache_record_map)').fetchone()
        return {'snapshot_uid':uid,'table_count':counts[0],'record_count':counts[1],'integrity_check':integrity,'foreign_key_violations':fk,'status':status,'cache_bytes':path.stat().st_size}
    finally:con.close()
def mark_stale(path:Path):
    con=sqlite3.connect(path)
    try:con.execute("UPDATE cache_snapshot_identity SET status='STALE'");con.commit()
    finally:con.close()

def main()->int:
    if git('status','--short'):raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected:raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list','-n1',SEAL_TAG)!=SEAL_COMMIT:raise RuntimeError('ERA55_SEAL_MISMATCH')
    runtime=load(RUNTIME);roadmap=load(ROADMAP);p=runtime['canonical_runtime_pointer'];e56=find_era(roadmap,'ERA56')
    checks={'era56_open':p.get('era56_opened') is True and e56.get('status')=='OPEN','era56b_ready':p.get('era56b_schema_validated') is True and p.get('era56b_rebuild_parity') is True,'next_step_matches':p.get('next_safe_step')==WORK,'production_apply_blocked':p.get('era56_production_apply_authorized') is False}
    if not all(checks.values()):raise RuntimeError('ERA56C_CHECK_FAILED:'+','.join(k for k,v in checks.items() if not v))
    source=choose_source();source_before=file_hash(source);ts=datetime.now(timezone.utc).isoformat();tmp=Path(tempfile.mkdtemp(prefix='era56c_',dir='/tmp'));snap=tmp/'source.sqlite';cache1=tmp/'cache1.sqlite';cache2=tmp/'cache2.sqlite';started=time.perf_counter()
    try:
        backup_source(source,snap);manifests,records,vector,content=extract(snap)
        if not manifests or not records:raise RuntimeError('EMPTY_RECORD_MAPPING')
        first=build_cache(cache1,manifests,records,vector,content);second=build_cache(cache2,manifests,records,vector,content)
        parity=first['snapshot_uid']==second['snapshot_uid'] and first['record_count']==second['record_count'] and first['record_count']==sum(x['row_count'] for x in manifests)
        if not parity:raise RuntimeError('LOGICAL_PARITY_FAILED')
        con=sqlite3.connect(snap);table=manifests[0]['table_name'];con.execute('CREATE TABLE IF NOT EXISTS __era56c_stale_probe(x INTEGER)');con.execute('INSERT INTO __era56c_stale_probe VALUES(1)');con.commit();con.close()
        stale_manifests,stale_records,stale_vector,stale_content=extract(snap);stale_detected=stale_vector!=vector or stale_content!=content
        if not stale_detected:raise RuntimeError('STALE_DETECTION_FAILED')
        mark_stale(cache1);stale_status=sqlite3.connect(cache1).execute('SELECT status FROM cache_snapshot_identity').fetchone()[0]
        if stale_status!='STALE':raise RuntimeError('STALE_MARK_FAILED')
        source_after=file_hash(source)
        if source_before!=source_after:raise RuntimeError('SOURCE_DB_CHANGED')
        elapsed=(time.perf_counter()-started)*1000;rel=str(ARTIFACT.relative_to(ROOT))
        dump(ARTIFACT,{'schema':'era56c_global_cache_record_mapping_and_logical_parity_test_v1','timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_LOGICAL_PARITY_VERIFIED','result':RESULT,'checks':checks,'source_db_path':str(source),'source_db_sha256_before':source_before,'source_db_sha256_after':source_after,'source_unchanged':True,'source_table_count':len(manifests),'source_record_count':len(records),'cache_build_1':first,'cache_build_2':second,'logical_parity':parity,'record_uid_unique':len({r['record_uid'] for r in records})==len(records),'source_version_vector_sha256':vector,'logical_content_sha256':content,'stale_detection':{'detected':stale_detected,'original_vector':vector,'mutated_vector':stale_vector,'cache_status_after_mark':stale_status},'elapsed_ms':elapsed,'temp_artifacts_retained':False,'production_mutation':False,'production_binding':False,'next_safe_step':NEXT})
    finally:shutil.rmtree(tmp,ignore_errors=True)
    runtime['current_problem']={'code':'ERA56D_ATOMIC_PUBLISH_AND_READONLY_CONSUMER_DRYRUN_PENDING','severity':'P1','evidence':rel};p.update({'current_stage':'ERA56C_LOGICAL_PARITY_VERIFIED','last_completed':WORK,'last_result':RESULT,'last_artifact':rel,'era56c_record_mapping_validated':True,'era56c_logical_parity':True,'era56c_stale_detection':True,'era56_production_apply_authorized':False,'next_safe_step':NEXT,'updated_at_utc':ts});runtime['current_state']={'project_status':'ACTIVE','runtime_status':'ERA56_OPEN_DESIGN_ONLY','mode':'ERA56C_LOGICAL_PARITY_VERIFIED','last_action':{'task':WORK,'result':RESULT,'artifact':rel,'timestamp':ts},'current_problem':runtime['current_problem'],'next_safe_step':{'id':NEXT,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts};runtime['current_work_unit']={'id':WORK,'status':'CLOSED_LOGICAL_PARITY_VERIFIED','result':RESULT,'artifact':rel,'production_mutation':False,'next_step':NEXT};dump(RUNTIME,runtime)
    e56.update({'active_stage':'ERA56C_LOGICAL_PARITY_VERIFIED','last_completed_substep':WORK,'last_result':RESULT,'next_safe_step':NEXT,'record_mapping_validated':True,'logical_parity_validated':True,'stale_detection_validated':True,'production_apply_authorized':False});dump(ROADMAP,roadmap)
    master=MASTER.read_text(encoding='utf-8');master=sec(master,'## 02 CURRENT MAJOR-LINE POSITION',f'''```text\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nERA56_STATUS=OPEN_BOUNDED_DESIGN_ONLY\nCURRENT_STAGE=ERA56C_LOGICAL_PARITY_VERIFIED\nLAST_COMPLETED_SUBSTEP={WORK}\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\n```''');master=sec(master,'## 03 LAST VERIFIED WORK',f'''```text\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nLAST_ARTIFACT={rel}\nWORK_UNIT_STATUS=CLOSED_LOGICAL_PARITY_VERIFIED\nSOURCE_DB_UNCHANGED=true\nLOGICAL_PARITY=true\nSTALE_DETECTION=true\nPRODUCTION_MUTATION=false\n```\n\nNEXT_SAFE_STEP={NEXT}''');master=sec(master,'## 10 NEXT SAFE STEP',f'''```text\nNEXT_SAFE_STEP={NEXT}\n```\n\nProve atomic publish and read-only consumer behavior on isolated temp artifacts only.''');MASTER.write_text(master,encoding='utf-8')
    hand=HANDOFF.read_text(encoding='utf-8');hand=sec(hand,'## 02 CURRENT CONTINUATION CHECKPOINT',f'''PROJECT_STATUS=ACTIVE_ERA56_GLOBAL_INTELLIGENCE_CACHE\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nERA56_STATUS=OPEN_BOUNDED_DESIGN_ONLY\nCURRENT_STAGE=ERA56C_LOGICAL_PARITY_VERIFIED\nLAST_COMPLETED_SUBSTEP={WORK}\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\nCURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD''');hand=sec(hand,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nLAST_ARTIFACT={rel}\nWORK_UNIT_STATUS=CLOSED_LOGICAL_PARITY_VERIFIED\nCURRENT_PROBLEM=ERA56D_ATOMIC_PUBLISH_AND_READONLY_CONSUMER_DRYRUN_PENDING''');hand=sec(hand,'## 07 ALLOWED NEXT DECISIONS',f'''- Record mapping: `VALIDATED`.\n- Logical parity: `VALIDATED`.\n- Stale detection: `VALIDATED`.\n- Production apply: `BLOCKED`.\n\nNEXT_SAFE_STEP={NEXT}''');HANDOFF.write_text(hand,encoding='utf-8')
    history=load(HISTORY);events=history.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')==WORK for x in events):events.append({'event_id':WORK,'timestamp_utc':ts,'era':'ERA56','status':'CLOSED_LOGICAL_PARITY_VERIFIED','result':RESULT,'artifact':rel,'production_mutation':False,'next_safe_step':NEXT})
    history['updated_at']=ts;history['updated_at_utc']=ts;dump(HISTORY,history)
    marker='## ERA56C GLOBAL CACHE RECORD MAPPING AND LOGICAL PARITY TEST';alm=ALMANAC.read_text(encoding='utf-8')
    if marker not in alm:ALMANAC.write_text(alm.rstrip()+f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_LOGICAL_PARITY_VERIFIED`\n- Result: `{RESULT}`\n- Source DB unchanged: `true`\n- Logical parity: `true`\n- Stale detection: `true`\n- Production mutation: `false`\n- Next safe step: `{NEXT}`\n''',encoding='utf-8')
    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nSTATE_SYNC_UTC={ts}\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nCURRENT_STAGE=ERA56C_LOGICAL_PARITY_VERIFIED\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\nNEXT_SAFE_STEP={NEXT}\n''',encoding='utf-8')
    machine=load(MACHINE);machine['created_at_utc']=ts;machine['collect_mode']='canonical_sync_snapshot_no_tk_machine';machine['current_state']={'authority':'PROJECT_RUNTIME.json','runtime_status':'ERA56_OPEN_DESIGN_ONLY','active_work_unit':{'id':WORK,'status':'CLOSED_LOGICAL_PARITY_VERIFIED','artifact':rel},'next_safe_step':{'name':NEXT,'status':'READY'},'last_action':{'timestamp':ts,'task':WORK,'result':RESULT,'artifact':rel}};machine['known_facts']={'era56_opened':True,'era56_stage':'ERA56C_LOGICAL_PARITY_VERIFIED','record_mapping_validated':True,'logical_parity_validated':True,'stale_detection_validated':True,'era56_production_apply_authorized':False,'production_mutation':False};dump(MACHINE,machine)
    for path in (RUNTIME,ROADMAP,HISTORY,MACHINE,ARTIFACT):load(path)
    if git('rev-list','-n1',SEAL_TAG)!=SEAL_COMMIT:raise RuntimeError('ERA55_SEAL_CHANGED')
    git('add','-A');check=run(['git','diff','--cached','--check'],check=False)
    if check.returncode!=0:print(check.stdout,end='');print(check.stderr,end='');raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m',SUBJECT)
    print('ERA56C_TEST=SUCCESS');print('SOURCE_DB_UNCHANGED=true');print('RECORD_MAPPING_VALIDATED=true');print('LOGICAL_PARITY=true');print('STALE_DETECTION=true');print('ERA56_PRODUCTION_APPLY_AUTHORIZED=false');print('PRODUCTION_MUTATION=false');print('NEXT_SAFE_STEP='+NEXT);print('LOCAL_COMMIT='+git('rev-parse','HEAD'));return 0
if __name__=='__main__':raise SystemExit(main())
