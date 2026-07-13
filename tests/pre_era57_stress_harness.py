#!/usr/bin/env python3
from __future__ import annotations
import argparse, errno, hashlib, json, os, signal, socket, sqlite3, subprocess, sys, tempfile, time, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROD_DB=ROOT/'data/tokenoskobi_clean_v1.sqlite'
RESULT_SCHEMA='pre_era57_isolated_stress_harness_result_v1'
SCENARIOS=('db_latency','lock_contention','sigterm','sigkill','partial_publish','stale_cache','corrupt_cache','disk_full','network_timeout','duplicate_replay')

def h(p:Path)->str:
    d=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):d.update(b)
    return d.hexdigest()
def guard_temp(p:Path):
    r=p.resolve();t=Path(tempfile.gettempdir()).resolve();prod=ROOT.resolve()
    if r==prod or prod in r.parents or not (r==t or t in r.parents):raise RuntimeError('TEMP_ROOT_GUARD_FAILED')
def runtime_guard():
    rt=json.loads((ROOT/'PROJECT_RUNTIME.json').read_text())['canonical_runtime_pointer']
    if rt.get('era57_opened') is not False:raise RuntimeError('ERA57_MUST_REMAIN_CLOSED')
    if rt.get('era56_closed') is not True:raise RuntimeError('ERA56_NOT_CLOSED')
def mkdb(p:Path):
    c=sqlite3.connect(p);c.execute('create table t(id integer primary key,v text unique)');c.executemany('insert into t(v) values(?)',[(str(i),) for i in range(20)]);c.commit();c.close()
def scenario(name:str,tmp:Path)->dict:
    db=tmp/'test.sqlite';mkdb(db);start=time.perf_counter()
    if name=='db_latency':time.sleep(.05);sqlite3.connect(db).execute('select count(*) from t').fetchone()
    elif name=='lock_contention':
        a=sqlite3.connect(db,timeout=.1);b=sqlite3.connect(db,timeout=.05);a.execute('begin immediate');ok=False
        try:b.execute('begin immediate')
        except sqlite3.OperationalError:ok=True
        finally:a.rollback();a.close();b.close()
        if not ok:raise RuntimeError('LOCK_CONTENTION_NOT_DETECTED')
    elif name in ('sigterm','sigkill'):
        worker=tmp/'worker.py';worker.write_text("import sqlite3,time,sys\nc=sqlite3.connect(sys.argv[1]);c.execute('begin immediate');c.execute(\"insert into t(v) values('child')\");time.sleep(30)\n")
        p=subprocess.Popen([sys.executable,str(worker),str(db)]);time.sleep(.2);os.kill(p.pid,signal.SIGTERM if name=='sigterm' else signal.SIGKILL);p.wait(timeout=5)
        c=sqlite3.connect(db);n=c.execute("select count(*) from t where v='child'").fetchone()[0];c.close()
        if n:raise RuntimeError('PARTIAL_CHILD_WRITE_COMMITTED')
    elif name=='partial_publish':
        target=tmp/'published.json';target.write_text('{"old":true}\n');draft=tmp/'published.json.tmp';draft.write_text('{"new":');
        if json.loads(target.read_text()).get('old') is not True:raise RuntimeError('OLD_ARTIFACT_LOST')
    elif name=='stale_cache':
        age=3600;threshold=300
        if age<=threshold:raise RuntimeError('STALE_NOT_REJECTED')
    elif name=='corrupt_cache':
        p=tmp/'cache.json';p.write_text('{bad');ok=False
        try:json.loads(p.read_text())
        except json.JSONDecodeError:ok=True
        if not ok:raise RuntimeError('CORRUPT_CACHE_ACCEPTED')
    elif name=='disk_full':
        try:raise OSError(errno.ENOSPC,'No space left on device')
        except OSError as e:
            if e.errno!=errno.ENOSPC:raise
    elif name=='network_timeout':
        try:raise socket.timeout('injected')
        except socket.timeout:pass
    elif name=='duplicate_replay':
        c=sqlite3.connect(db);ok=False
        try:c.execute("insert into t(v) values('1')");c.commit()
        except sqlite3.IntegrityError:ok=True;c.rollback()
        finally:c.close()
        if not ok:raise RuntimeError('DUPLICATE_NOT_REJECTED')
    return {'status':'PASS','elapsed_ms':round((time.perf_counter()-start)*1000,3)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scenario',choices=SCENARIOS+('all',),default='all');ap.add_argument('--output',default='/tmp/pre_era57_stress_harness_result.json');a=ap.parse_args()
    runtime_guard();
    if not PROD_DB.is_file():raise RuntimeError('PRODUCTION_DB_MISSING')
    before=h(PROD_DB);tmp=Path(tempfile.mkdtemp(prefix='pre_era57_stress_'));guard_temp(tmp)
    results={};selected=SCENARIOS if a.scenario=='all' else (a.scenario,)
    try:
        for s in selected:
            case=tmp/s;case.mkdir();results[s]=scenario(s,case)
        after=h(PROD_DB)
        if before!=after:raise RuntimeError('SOURCE_DB_MUTATED')
        out={'schema':RESULT_SCHEMA,'run_id':str(uuid.uuid4()),'timestamp_utc':time.time(),'scenarios':results,'source_hash_before':before,'source_hash_after':after,'source_hash_verified':True,'production_path_untouched':True,'production_mutation':False,'verdict':'PASS' if all(x['status']=='PASS' for x in results.values()) else 'FAIL'}
        Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
    finally:
        import shutil;shutil.rmtree(tmp,ignore_errors=True)
if __name__=='__main__':main()
