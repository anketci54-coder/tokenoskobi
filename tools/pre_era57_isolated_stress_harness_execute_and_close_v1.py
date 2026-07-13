#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,shlex,sqlite3,subprocess,tempfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
WORK='PRE_ERA57_ISOLATED_ADVERSARIAL_STRESS_HARNESS_EXECUTION'
HARNESS=ROOT/'tests/pre_era57_stress_harness.py'
TMP=Path('/tmp/pre_era57_stress_harness_result.json')
ART=ROOT/'data/control/pre_era57_isolated_stress_harness_result_v1.json'
RUNTIME=ROOT/'PROJECT_RUNTIME.json';HISTORY=ROOT/'PROJECT_HISTORY.json'
MASTER=ROOT/'06_PROJECT_MASTER_STATE.md';HANDOFF=ROOT/'07_PROJECT_HANDOFF.md';ALMANAC=ROOT/'04_ALMANAC.md'
TKAI=ROOT/'reports/LATEST_TK_AI_HANDOFF.md';MACHINE=ROOT/'data/control/latest_tk_machine_state.json'
TAG55='ERA55_FINAL_SEAL';SEAL55='f22ce4f07788ec7fbe22a72f872467705b72db5a'
TAG56='ERA56_FINAL_SEAL';SEAL56='39dd684a71e39c4f05ce2a5113985fcf647718a0'
SERVICE='tokenoskobi-news-radar-refresh.service';TIMER='tokenoskobi-news-radar-refresh.timer'

def run(a,check=True):return subprocess.run(a,cwd=ROOT,text=True,capture_output=True,check=check,timeout=180)
def git(*a):return run(['git',*a]).stdout.strip()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+'.',dir=p.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 finally:
  if os.path.exists(t):os.unlink(t)
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def text_hash(s):return hashlib.sha256(s.encode()).hexdigest()
def section(text,heading,body):
 s=text.find(heading)
 if s<0:raise RuntimeError('HEADING_MISSING:'+heading)
 e=text.find('\n## ',s+len(heading));e=len(text) if e<0 else e
 return text[:s]+heading+'\n\n'+body.rstrip()+'\n'+text[e:]
def systemctl(*a):return run(['systemctl',*a],check=False).stdout.strip()
def env_map(s):
 out={}
 for token in shlex.split(s):
  if '=' in token:
   k,v=token.split('=',1);out[k]=v
 return out

def main():
 expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','')
 if git('status','--short'):raise RuntimeError('WORKTREE_NOT_CLEAN')
 if expected and git('rev-parse','HEAD')!=expected:raise RuntimeError('HEAD_MISMATCH')
 if git('rev-list','-n1',TAG55)!=SEAL55 or git('rev-list','-n1',TAG56)!=SEAL56:raise RuntimeError('SEAL_MISMATCH')
 rt=load(RUNTIME);p=rt['canonical_runtime_pointer']
 if p.get('era57_opened') is not False or p.get('next_safe_step')!='PRE_ERA57_ISOLATED_ADVERSARIAL_STRESS_HARNESS_EXECUTION_DECISION':raise RuntimeError('STATE_GUARD_FAILED')
 if not HARNESS.is_file():raise RuntimeError('HARNESS_MISSING')
 db=ROOT/'data/tokenoskobi_clean_v1.sqlite'
 if not db.is_file():raise RuntimeError('PRODUCTION_DB_MISSING')
 db_before=sha(db)
 con=sqlite3.connect(f'file:{db}?mode=ro',uri=True,timeout=10)
 try:
  journal=con.execute('pragma journal_mode').fetchone()[0]
  integrity=con.execute('pragma integrity_check').fetchone()[0]
  tables={r[0] for r in con.execute("select name from sqlite_master where type='table'")}
  counts={}
  for n in ('news_disposition_ledger','news_disposition_batches'):
   if n in tables:counts[n]=con.execute(f'select count(*) from "{n}"').fetchone()[0]
 finally:con.close()
 env_text=systemctl('show',SERVICE,'-p','Environment','--value')
 env=env_map(env_text)
 raw=Path(env.get('TOKENOSKOBI_NEWS_ORIGINAL_PATH',ROOT/'tools/news_radar_refresh_runner_v1.PRE_DERIVED_BINDING_20260709T171244Z.py'))
 raw_ok=raw.is_file()
 service_text=systemctl('cat',SERVICE);timer_text=systemctl('cat',TIMER)
 if not service_text or not timer_text:raise RuntimeError('SYSTEMD_UNIT_EVIDENCE_MISSING')
 if TMP.exists():TMP.unlink()
 r=run(['/usr/bin/python3',str(HARNESS),'--scenario','all','--output',str(TMP)],check=False)
 if r.returncode!=0:raise RuntimeError('HARNESS_FAILED:'+r.stderr[-1000:])
 result=load(TMP)
 if result.get('verdict')!='PASS' or result.get('source_hash_verified') is not True:raise RuntimeError('HARNESS_VERDICT_FAILED')
 db_after=sha(db)
 if db_before!=db_after:raise RuntimeError('SOURCE_DB_MUTATED')
 result.update({'work_unit':WORK,'production_db_sha256_before':db_before,'production_db_sha256_after':db_after,'production_db_unchanged':True,'journal_mode':journal,'integrity_check':integrity,'ledger_counts':counts,'service_unit_sha256':text_hash(service_text),'timer_unit_sha256':text_hash(timer_text),'raw_runner_path':str(raw),'raw_runner_resolved':raw_ok,'era55_seal_preserved':True,'era56_seal_preserved':True,'era57_opened':False,'production_mutation':False})
 dump(ART,result)
 ts=datetime.now(timezone.utc).isoformat();rel=str(ART.relative_to(ROOT))
 next_step='ERA57_AUTONOMOUS_RESEARCH_LAYER_OPENING_DECISION' if raw_ok else 'PRE_ERA57_LIVE_RAW_RUNNER_RESOLUTION_AND_RUNTIME_ENTRY_DECISION'
 p.update({'current_stage':'PRE_ERA57_ISOLATED_STRESS_HARNESS_COMPLETED','last_completed':WORK,'last_result':'OK_ISOLATED_STRESS_HARNESS_PASS','last_artifact':rel,'pre_era57_stress_harness_executed':True,'pre_era57_stress_harness_passed':True,'pre_era57_raw_runner_resolved':raw_ok,'era57_opened':False,'next_safe_step':next_step,'updated_at_utc':ts})
 rt['current_problem']={'code':'NONE' if raw_ok else 'LIVE_RAW_RUNNER_PATH_UNRESOLVED','severity':'NONE' if raw_ok else 'P1','evidence':rel}
 rt['current_state']={'project_status':'ERA56_CLOSED_PRE_ERA57_STRESS_VERIFIED','runtime_status':'PRODUCTION_UNCHANGED','mode':'PRE_ERA57_STRESS_HARNESS_COMPLETED','last_action':{'task':WORK,'result':'OK_ISOLATED_STRESS_HARNESS_PASS','artifact':rel,'timestamp':ts},'current_problem':rt['current_problem'],'next_safe_step':{'id':next_step,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts}
 rt['current_work_unit']={'id':WORK,'status':'CLOSED_VERIFIED','result':'OK_ISOLATED_STRESS_HARNESS_PASS','artifact':rel,'production_mutation':False,'next_step':next_step};dump(RUNTIME,rt)
 hist=load(HISTORY);hist.setdefault('events',[]).append({'event_id':WORK,'timestamp_utc':ts,'status':'CLOSED_VERIFIED','result':'OK_ISOLATED_STRESS_HARNESS_PASS','artifact':rel,'raw_runner_resolved':raw_ok,'production_mutation':False,'next_safe_step':next_step});hist['updated_at_utc']=ts;dump(HISTORY,hist)
 master=MASTER.read_text();master=section(master,'## 03 LAST VERIFIED WORK',f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT=OK_ISOLATED_STRESS_HARNESS_PASS
LAST_ARTIFACT={rel}
ALL_SCENARIOS_PASS=true
PRODUCTION_DB_UNCHANGED=true
RAW_RUNNER_RESOLVED={str(raw_ok).lower()}
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={next_step}''');master=section(master,'## 10 NEXT SAFE STEP',f'''```text
NEXT_SAFE_STEP={next_step}
```''');MASTER.write_text(master)
 hand=HANDOFF.read_text();hand=section(hand,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}
LAST_RESULT=OK_ISOLATED_STRESS_HARNESS_PASS
LAST_ARTIFACT={rel}
ALL_SCENARIOS_PASS=true
RAW_RUNNER_RESOLVED={str(raw_ok).lower()}
CURRENT_PROBLEM={'NONE' if raw_ok else 'LIVE_RAW_RUNNER_PATH_UNRESOLVED'}''');hand=section(hand,'## 07 ALLOWED NEXT DECISIONS',f'''- Isolated stress harness: `PASS`.
- Production mutation: `BLOCKED`.
- ERA57 opened: `FALSE`.

NEXT_SAFE_STEP={next_step}''');HANDOFF.write_text(hand)
 marker='## PRE ERA57 ISOLATED ADVERSARIAL STRESS HARNESS';alm=ALMANAC.read_text()
 if marker not in alm:ALMANAC.write_text(alm.rstrip()+f'\n\n---\n\n{marker}\n\n- Result: `OK_ISOLATED_STRESS_HARNESS_PASS`\n- Artifact: `{rel}`\n- Raw runner resolved: `{str(raw_ok).lower()}`\n- Production mutation: `false`\n- Next safe step: `{next_step}`\n')
 TKAI.write_text(f'# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nSTATE_SYNC_UTC={ts}\nLAST_COMPLETED={WORK}\nLAST_RESULT=OK_ISOLATED_STRESS_HARNESS_PASS\nRAW_RUNNER_RESOLVED={str(raw_ok).lower()}\nERA57_OPENED=false\nPRODUCTION_MUTATION=false\nNEXT_SAFE_STEP={next_step}\n')
 m=load(MACHINE);m['created_at_utc']=ts;m['known_facts']={'stress_harness_passed':True,'production_db_unchanged':True,'raw_runner_resolved':raw_ok,'era57_opened':False,'production_mutation':False};m['current_state']={'authority':'PROJECT_RUNTIME.json','next_safe_step':{'name':next_step,'status':'READY'},'last_action':{'timestamp':ts,'task':WORK,'result':'OK_ISOLATED_STRESS_HARNESS_PASS','artifact':rel}};dump(MACHINE,m)
 git('add','-A');chk=run(['git','diff','--cached','--check'],check=False)
 if chk.returncode:raise RuntimeError('DIFF_CHECK_FAILED:'+chk.stdout+chk.stderr)
 git('commit','-m','PRE_ERA57_STRESS | OK | ISOLATED_HARNESS_EXECUTED')
 print('PRE_ERA57_STRESS=SUCCESS');print('ALL_SCENARIOS_PASS=true');print('PRODUCTION_DB_UNCHANGED=true');print('RAW_RUNNER_RESOLVED='+str(raw_ok).lower());print('ERA57_OPENED=false');print('PRODUCTION_MUTATION=false');print('NEXT_SAFE_STEP='+next_step);print('LOCAL_COMMIT='+git('rev-parse','HEAD'))
if __name__=='__main__':main()
