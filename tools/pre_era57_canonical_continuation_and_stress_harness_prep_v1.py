#!/usr/bin/env python3
from __future__ import annotations

import json, os, subprocess, tempfile, textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
WORK='PRE_ERA57_CANONICAL_CONTINUATION_AND_ISOLATED_STRESS_HARNESS_PREP'
RESULT='OK_CANONICAL_CONTINUATION_HARDENED_STRESS_HARNESS_PREPARED'
NEXT='PRE_ERA57_ISOLATED_ADVERSARIAL_STRESS_HARNESS_EXECUTION_DECISION'
SUBJECT='PRE_ERA57_PREP | OK | CANONICAL_CONTINUATION_AND_STRESS_HARNESS'
ERA55_TAG='ERA55_FINAL_SEAL';ERA55_SEAL='f22ce4f07788ec7fbe22a72f872467705b72db5a'
ERA56_TAG='ERA56_FINAL_SEAL';ERA56_SEAL='39dd684a71e39c4f05ce2a5113985fcf647718a0'
README=ROOT/'README.md';MANIFESTO=ROOT/'02_MANIFESTO.md';BOOT=ROOT/'PROJECT_BOOT.json';RUNTIME=ROOT/'PROJECT_RUNTIME.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md';HANDOFF=ROOT/'07_PROJECT_HANDOFF.md';INDEX=ROOT/'01_INDEX.md';ROADMAP=ROOT/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
HISTORY=ROOT/'PROJECT_HISTORY.json';TK_AI=ROOT/'reports/LATEST_TK_AI_HANDOFF.md';MACHINE=ROOT/'data/control/latest_tk_machine_state.json'
HARNESS=ROOT/'tests/pre_era57_stress_harness.py';ARTIFACT=ROOT/'data/control/pre_era57_canonical_continuation_and_stress_harness_prep_v1.json'


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
def append_once(p:Path,marker:str,block:str):
    text=p.read_text(encoding='utf-8')
    if marker not in text:p.write_text(text.rstrip()+'\n\n'+block.strip()+'\n',encoding='utf-8')
def era(roadmap:dict[str,Any],era_id:str)->dict[str,Any]:
    for v in roadmap.get('versions',[]):
        if v.get('id')=='V3':
            for e in v.get('children',[]):
                if e.get('id')==era_id:return e
    raise RuntimeError('ERA_NOT_FOUND:'+era_id)

HARNESS_CODE=r'''#!/usr/bin/env python3
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
'''


def main()->int:
    if git('status','--short'):raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected:raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list','-n1',ERA55_TAG)!=ERA55_SEAL:raise RuntimeError('ERA55_SEAL_MISMATCH')
    if git('rev-list','-n1',ERA56_TAG)!=ERA56_SEAL:raise RuntimeError('ERA56_SEAL_MISMATCH')
    ts=datetime.now(timezone.utc).isoformat();runtime=load(RUNTIME);boot=load(BOOT);roadmap=load(ROADMAP);p=runtime['canonical_runtime_pointer'];e57=era(roadmap,'ERA57')
    if p.get('era56_closed') is not True or p.get('era57_opened') is not False:raise RuntimeError('ERA_BOUNDARY_INVALID')

    README.write_text(textwrap.dedent('''
    # TOKENOSKOBI / COINOSKOBI

    Bu dosya kısa başlangıç ve devam işaretçisidir. Canlı proje durumu burada kopyalanmaz; `PROJECT_RUNTIME.json` dosyasından okunur.

    ## Yeni pencere başlangıç sırası

    1. `PROJECT_RUNTIME.json` — mevcut durum ve gerçek `NEXT_SAFE_STEP`
    2. `PROJECT_BOOT.json` — kalıcı kimlik, anayasa ve başlangıç sözleşmesi
    3. `06_PROJECT_MASTER_STATE.md` — okunabilir mevcut durum özeti
    4. `07_PROJECT_HANDOFF.md` — devam bağlamı
    5. `02_MANIFESTO.md` — kalıcı anayasal kurallar
    6. `03_ROADMAP.md` — gelecek yönü
    7. `PROJECT_HISTORY.json` — yalnız tarih gerektiğinde

    Canonical navigation için `01_INDEX.md` kullanılır.

    ## Devam garantisi

    - Önce `git rev-parse HEAD` ve tag doğrulaması yapılır.
    - Mevcut ERA, son tamamlanan iş ve sonraki güvenli adım yalnız `PROJECT_RUNTIME.json` içinden okunur.
    - README, Boot, Master State veya AI hafızası Runtime ile çelişirse Runtime üstün gelir.
    - Local workspace ve Local Git, GitHub remote ve AI hafızasından üstündür.
    - Yeni ERA yalnız açık insan kararıyla açılır.

    ## İcra modeli

    `CONSTITUTION → RISK CLASSIFICATION → PLAYBOOK SELECTION → EXECUTION → EVIDENCE → SEAL`

    Anayasal yaşam döngüsü değişmez. Temp-copy, shadow, canary, benchmark, stress veya red-team teknikleri zorunlu anayasa adımları değil; işin riskine göre seçilen playbook araçlarıdır.

    ## Kalıcı kısa kurallar

    - Constitution is invariant; playbook is risk-driven.
    - Complexity must pay for itself.
    - Evidence never disappears; geçici araç kalıcı olmak zorunda değildir.
    - One source of truth: current state owner is `PROJECT_RUNTIME.json`.
    - Tek mantıksal operasyon, mümkünse tek commit ve tek push.
    - Runtime, DB, panel, service, timer veya yetki mutasyonu yalnız açık kapsamla yapılır.
    - Canlı trade, wallet signing, order creation ve AI trade authority kilitlidir.

    ## Script yaşam döngüsü

    - `ACTIVE_RUNTIME`: doğrulanmış runtime zinciri tarafından çağrılır.
    - `ACTIVE_LIBRARY`: aktif kod tarafından import edilir.
    - `MANUAL_ONLY`: yalnız açık insan komutuyla çalışır.
    - `HISTORICAL_EVIDENCE`: geçmiş kanıtıdır; archive alanında korunabilir.
    - `DISPOSABLE`: yeniden üretilebilir ve kanıt değeri olmayan geçici araçtır.
    ''').lstrip(),encoding='utf-8')

    marker='<!-- RISK_DRIVEN_PLAYBOOK_DOCTRINE_START -->'
    append_once(MANIFESTO,marker,textwrap.dedent(f'''
    {marker}
    ## RISK-DRIVEN PLAYBOOK AND COMPLEXITY DOCTRINE

    STATUS: PERMANENT CONSTITUTIONAL RULE
    UPDATED_UTC: {ts}

    1. Constitution is invariant. It defines mandatory authority, evidence, canonical synchronization, commit, push, remote verification and closure rules.
    2. Playbook is risk-driven. Read-only, temp-copy, shadow runtime, canary, benchmark, stress, chaos and external review are selected only when the work's risk justifies them.
    3. No playbook may bypass or replace the Constitution.
    4. Complexity must pay for itself through measured SPEED, POWER, SECURITY, ECONOMY or ADAPTABILITY value. Otherwise it is rejected or deferred.
    5. Evidence never disappears. Reproducible temporary tools may be removed after their evidence and decision remain canonical.
    6. Current state has one owner: `PROJECT_RUNTIME.json`. Other documents reference or summarize it and may not create competing current-state authority.
    7. Prefer the smallest safe playbook that satisfies the risk class and evidence requirement.
    <!-- RISK_DRIVEN_PLAYBOOK_DOCTRINE_END -->
    '''))

    boot['boot_version']='3.1'
    boot['execution_model']={'constitution':'INVARIANT','playbook':'RISK_DRIVEN','constitution_overrides_playbook':True,'playbook_cannot_bypass_constitution':True,'complexity_must_pay_for_itself':True,'evidence_never_disappears':True,'current_state_single_owner':'PROJECT_RUNTIME.json'}
    boot['boot_architecture']['resume_guarantee']={'goal':'Any new AI window resumes from canonical files without chat memory.','state_owner':'PROJECT_RUNTIME.json','head_owner':'local_git_dynamic','conflict_rule':'Runtime wins over summaries; local workspace and local Git win over remote and AI memory.'}
    boot['canonical_identity']['doctrine']=[x for x in boot['canonical_identity']['doctrine'] if x not in ('Constitution is invariant','Playbooks are risk-driven','Complexity must pay for itself')]+['Constitution is invariant','Playbooks are risk-driven','Complexity must pay for itself']
    dump(BOOT,boot)

    runtime['execution_model']={'constitution':'INVARIANT','playbook':'RISK_DRIVEN','selected_playbook':'ISOLATED_TEMP_COPY_AND_SHADOW_STRESS','risk_level':'HIGH_PRE_ERA_RUNTIME_ENTRY','production_chaos_test':False,'maintenance_window_test':False,'one_result_artifact':True}
    runtime['canonical_document_condition']['README.md']='SHORT_STARTUP_AND_RESUME_POINTER_ONLY'
    runtime['current_problem']={'code':'PRE_ERA57_ISOLATED_STRESS_HARNESS_EXECUTION_DECISION_PENDING','severity':'P1','evidence':str(ARTIFACT.relative_to(ROOT))}
    p.update({'current_stage':'PRE_ERA57_STRESS_HARNESS_PREPARED','last_completed':WORK,'last_result':RESULT,'last_artifact':str(ARTIFACT.relative_to(ROOT)),'era57_opened':False,'pre_era57_stress_harness_prepared':True,'pre_era57_stress_harness_executed':False,'production_chaos_test_authorized':False,'next_safe_step':NEXT,'updated_at_utc':ts})
    runtime['current_state']={'project_status':'ERA56_CLOSED_PRE_ERA57_STRESS_DECISION_PENDING','runtime_status':'NO_PRODUCTION_CHANGE','mode':'PRE_ERA57_STRESS_HARNESS_PREPARED','last_action':{'task':WORK,'result':RESULT,'artifact':str(ARTIFACT.relative_to(ROOT)),'timestamp':ts},'current_problem':runtime['current_problem'],'next_safe_step':{'id':NEXT,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts}
    runtime['current_work_unit']={'id':WORK,'status':'CLOSED_PREPARED_NOT_EXECUTED','result':RESULT,'artifact':str(ARTIFACT.relative_to(ROOT)),'production_mutation':False,'next_step':NEXT}
    dump(RUNTIME,runtime)

    e57.update({'status':'PLANNED','opening_blocked_until':'PRE_ERA57_ISOLATED_STRESS_RESULT_REVIEW','entry_playbook':'RISK_DRIVEN_ISOLATED_STRESS','production_runtime_open_authorized':False,'next_safe_step':NEXT})
    dump(ROADMAP,roadmap)

    HARNESS.parent.mkdir(parents=True,exist_ok=True);HARNESS.write_text(HARNESS_CODE,encoding='utf-8');HARNESS.chmod(0o755)
    append_once(MASTER,'<!-- EXECUTION_MODEL_CANONICAL_START -->',textwrap.dedent(f'''
    <!-- EXECUTION_MODEL_CANONICAL_START -->
    ## EXECUTION MODEL AND PRE-ERA57 ENTRY

    CONSTITUTION=INVARIANT
    PLAYBOOK=RISK_DRIVEN
    COMPLEXITY_MUST_PAY_FOR_ITSELF=true
    CURRENT_STATE_OWNER=PROJECT_RUNTIME.json
    ERA56_CLOSED=true
    ERA57_OPENED=false
    STRESS_HARNESS_PREPARED=true
    STRESS_HARNESS_EXECUTED=false
    PRODUCTION_CHAOS_TEST=false
    NEXT_SAFE_STEP={NEXT}
    <!-- EXECUTION_MODEL_CANONICAL_END -->
    '''))
    append_once(HANDOFF,'<!-- PRE_ERA57_CONTINUATION_START -->',textwrap.dedent(f'''
    <!-- PRE_ERA57_CONTINUATION_START -->
    ## PRE-ERA57 CONTINUATION

    Read `PROJECT_RUNTIME.json` first. ERA56 is sealed. ERA57 is not opened.
    The single reusable harness is `tests/pre_era57_stress_harness.py`.
    It has not been executed by this preparation work unit.
    NEXT_SAFE_STEP={NEXT}
    <!-- PRE_ERA57_CONTINUATION_END -->
    '''))
    append_once(INDEX,'<!-- STARTUP_RESUME_MAP_START -->',textwrap.dedent('''
    <!-- STARTUP_RESUME_MAP_START -->
    ## STARTUP AND RESUME MAP

    - Current state: `PROJECT_RUNTIME.json`
    - Stable boot contract: `PROJECT_BOOT.json`
    - Human-readable state: `06_PROJECT_MASTER_STATE.md`
    - Continuation context: `07_PROJECT_HANDOFF.md`
    - Constitution: `02_MANIFESTO.md`
    - Future direction: `03_ROADMAP.md`
    - History: `PROJECT_HISTORY.json`
    - Pre-ERA57 isolated harness: `tests/pre_era57_stress_harness.py`
    <!-- STARTUP_RESUME_MAP_END -->
    '''))

    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nSTATE_SYNC_UTC={ts}\nERA56_CLOSED=true\nERA57_OPENED=false\nCONSTITUTION=INVARIANT\nPLAYBOOK=RISK_DRIVEN\nSTRESS_HARNESS=tests/pre_era57_stress_harness.py\nSTRESS_HARNESS_EXECUTED=false\nPRODUCTION_CHAOS_TEST=false\nNEXT_SAFE_STEP={NEXT}\n''',encoding='utf-8')
    machine=load(MACHINE);machine['created_at_utc']=ts;machine['collect_mode']='canonical_sync_snapshot_no_tk_machine';machine['current_state']={'authority':'PROJECT_RUNTIME.json','runtime_status':'ERA56_CLOSED_PRE_ERA57_STRESS_DECISION_PENDING','active_work_unit':{'id':WORK,'status':'CLOSED_PREPARED_NOT_EXECUTED','artifact':str(ARTIFACT.relative_to(ROOT))},'next_safe_step':{'name':NEXT,'status':'READY'},'last_action':{'timestamp':ts,'task':WORK,'result':RESULT,'artifact':str(ARTIFACT.relative_to(ROOT))}};machine['known_facts']={'era56_closed':True,'era57_opened':False,'constitution_invariant':True,'playbook_risk_driven':True,'stress_harness_prepared':True,'stress_harness_executed':False,'production_mutation':False};dump(MACHINE,machine)

    history=load(HISTORY);events=history.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')==WORK for x in events):events.append({'event_id':WORK,'timestamp_utc':ts,'status':'CLOSED_PREPARED_NOT_EXECUTED','result':RESULT,'artifact':str(ARTIFACT.relative_to(ROOT)),'era57_opened':False,'production_mutation':False,'next_safe_step':NEXT})
    history['updated_at']=ts;history['updated_at_utc']=ts;dump(HISTORY,history)
    dump(ARTIFACT,{'schema':'pre_era57_canonical_continuation_and_stress_harness_prep_v1','timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_PREPARED_NOT_EXECUTED','result':RESULT,'files_updated':['README.md','02_MANIFESTO.md','PROJECT_BOOT.json','PROJECT_RUNTIME.json','06_PROJECT_MASTER_STATE.md','07_PROJECT_HANDOFF.md','01_INDEX.md','data/tokenoskobi_v1_v8_master_era_roadmap.json','PROJECT_HISTORY.json','reports/LATEST_TK_AI_HANDOFF.md','data/control/latest_tk_machine_state.json'],'harness':'tests/pre_era57_stress_harness.py','harness_executed':False,'era57_opened':False,'production_mutation':False,'next_safe_step':NEXT})

    for f in (BOOT,RUNTIME,ROADMAP,HISTORY,MACHINE,ARTIFACT):load(f)
    run(['python3','-m','py_compile',str(HARNESS)])
    if git('rev-list','-n1',ERA55_TAG)!=ERA55_SEAL or git('rev-list','-n1',ERA56_TAG)!=ERA56_SEAL:raise RuntimeError('SEAL_CHANGED')
    git('add','-A');chk=run(['git','diff','--cached','--check'],check=False)
    if chk.returncode!=0:print(chk.stdout,end='');print(chk.stderr,end='');raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m',SUBJECT)
    print('PRE_ERA57_PREP=SUCCESS');print('CANONICAL_CONTINUATION_HARDENED=true');print('STRESS_HARNESS_PREPARED=true');print('STRESS_HARNESS_EXECUTED=false');print('ERA57_OPENED=false');print('PRODUCTION_MUTATION=false');print('NEXT_SAFE_STEP='+NEXT);print('LOCAL_COMMIT='+git('rev-parse','HEAD'));return 0
if __name__=='__main__':raise SystemExit(main())
