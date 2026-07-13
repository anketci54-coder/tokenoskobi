#!/usr/bin/env python3
from __future__ import annotations

import json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
WORK='ERA56A_GLOBAL_CACHE_OWNERSHIP_OVERLAP_AND_REBUILD_CONTRACT'
RESULT='OK_ERA56A_OWNERSHIP_OVERLAP_REBUILD_CONTRACT_LOCKED'
NEXT='ERA56B_GLOBAL_CACHE_READONLY_SCHEMA_AND_TEMP_COPY_BUILD'
SUBJECT='ERA56A | OK | OWNERSHIP_OVERLAP_REBUILD_CONTRACT'
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
ARTIFACT=ROOT/'data/control/era56a_global_cache_ownership_overlap_and_rebuild_contract_v1.json'

REQUIRED_EXISTING=[
 'tools/news_radar_refresh_runner_v1.py',
 'tools/era55a23_p0_guarded_general_production_writer_runtime_integration_apply_and_post_audit_v1.py',
 'tools/news_coverage_readmodel_consumer_v1.py',
 'tools/news_active_panel_data_bridge_v1.py',
 'tools/hot_intelligence_ingress_gateway_v1.py',
]


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


def main()->int:
    if git('status','--short'):raise RuntimeError('WORKTREE_NOT_CLEAN')
    expected=os.environ.get('TOKENOSKOBI_EXPECTED_HEAD','').strip()
    if expected and git('rev-parse','HEAD')!=expected:raise RuntimeError('HEAD_MISMATCH')
    if git('rev-list','-n1',SEAL_TAG)!=SEAL_COMMIT:raise RuntimeError('ERA55_SEAL_MISMATCH')

    runtime=load(RUNTIME);roadmap=load(ROADMAP);p=runtime['canonical_runtime_pointer'];e56=find_era(roadmap,'ERA56')
    checks={
      'era56_open':p.get('era56_opened') is True and e56.get('status')=='OPEN',
      'era56_design_only':p.get('era56_production_apply_authorized') is False,
      'next_step_matches':p.get('next_safe_step')==WORK,
      'writer_active':p.get('production_ledger_writer_active') is True,
      'runner_lock_enabled':p.get('runner_lock_enabled') is True,
      'option_b_blocked':p.get('option_b_authorized') is False and p.get('wal_apply_authorized') is False,
      'required_files_present':all((ROOT/x).is_file() for x in REQUIRED_EXISTING),
    }
    if not all(checks.values()):raise RuntimeError('CONTRACT_CHECK_FAILED:'+','.join(k for k,v in checks.items() if not v))

    ts=datetime.now(timezone.utc).isoformat();rel=str(ARTIFACT.relative_to(ROOT))
    contract={
      'single_owner':{
        'authoritative_sources':['existing runtime DB tables','existing ledgers','producer artifacts','canonical readmodel owners'],
        'era56_owner':'derived global immutable snapshot publication only',
        'second_source_of_truth_forbidden':True,
      },
      'overlap_boundaries':{
        'ledger':'ERA56 must not write, replace or reinterpret ledger authority.',
        'hot_ingress':'ERA56 may consume published outputs only; it may not become ingress authority.',
        'readmodel':'ERA56 aggregates readmodels but does not replace owner-specific readmodels.',
        'panel_bridge':'ERA56 publishes no panel-specific state directly; panel bridges consume approved snapshots.',
        'backpressure':'ERA56 records backpressure metadata but does not own queue control.',
      },
      'snapshot_identity':{
        'immutable':True,
        'content_hash_required':True,
        'source_version_vector_required':True,
        'created_at_utc_required':True,
        'schema_version_required':True,
        'atomic_publish_required':True,
      },
      'staleness':{
        'source_version_mismatch_fails_closed':True,
        'expired_snapshot_not_served_as_fresh':True,
        'unknown_freshness_status':'STALE_UNKNOWN',
        'panel_must_receive_staleness_state':True,
      },
      'rebuild':{
        'fully_rebuildable_from_authoritative_sources':True,
        'cache_loss_must_not_cause_source_loss':True,
        'delete_and_rebuild_supported':True,
        'deterministic_uid_order_required':True,
        'logical_parity_required':True,
      },
      'authority_limits':{
        'production_db_write_authority':0,
        'ledger_write_authority':0,
        'panel_write_authority':0,
        'service_timer_authority':0,
        'trade_authority':0,
        'wallet_authority':0,
        'human_final_authority':True,
      },
      'next_build_limits':{
        'temp_copy_or_new_isolated_file_only':True,
        'production_binding_authorized':False,
        'service_timer_binding_authorized':False,
        'panel_binding_authorized':False,
      },
    }
    dump(ARTIFACT,{'schema':'era56a_global_cache_ownership_overlap_and_rebuild_contract_v1','timestamp_utc':ts,'work_unit':WORK,'status':'CLOSED_CONTRACT_LOCKED','result':RESULT,'checks':checks,'contract':contract,'production_mutation':False,'era56_production_apply_authorized':False,'next_safe_step':NEXT})

    runtime['current_problem']={'code':'ERA56B_READONLY_SCHEMA_AND_TEMP_COPY_BUILD_PENDING','severity':'P1','evidence':rel}
    p.update({'current_stage':'ERA56A_CONTRACT_LOCKED','last_completed':WORK,'last_result':RESULT,'last_artifact':rel,'era56_contract_locked':True,'era56_production_apply_authorized':False,'next_safe_step':NEXT,'updated_at_utc':ts})
    runtime['current_state']={'project_status':'ACTIVE','runtime_status':'ERA56_OPEN_DESIGN_ONLY','mode':'ERA56A_CONTRACT_LOCKED','last_action':{'task':WORK,'result':RESULT,'artifact':rel,'timestamp':ts},'current_problem':runtime['current_problem'],'next_safe_step':{'id':NEXT,'status':'READY','human_authorization_required':True,'production_mutation':False},'updated_at':ts}
    runtime['current_work_unit']={'id':WORK,'status':'CLOSED_CONTRACT_LOCKED','result':RESULT,'artifact':rel,'production_mutation':False,'next_step':NEXT}
    dump(RUNTIME,runtime)

    e56.update({'active_stage':'ERA56A_CONTRACT_LOCKED','last_completed_substep':WORK,'last_result':RESULT,'next_safe_step':NEXT,'ownership_contract_locked':True,'overlap_contract_locked':True,'rebuild_contract_locked':True,'production_apply_authorized':False})
    dump(ROADMAP,roadmap)

    master=MASTER.read_text(encoding='utf-8')
    master=sec(master,'## 02 CURRENT MAJOR-LINE POSITION',f'''```text
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=OPEN_BOUNDED_DESIGN_ONLY
CURRENT_STAGE=ERA56A_CONTRACT_LOCKED
LAST_COMPLETED_SUBSTEP={WORK}
ERA56_PRODUCTION_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
```''')
    master=sec(master,'## 03 LAST VERIFIED WORK',f'''```text
LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_CONTRACT_LOCKED
PRODUCTION_MUTATION=false
```

NEXT_SAFE_STEP={NEXT}''')
    master=sec(master,'## 10 NEXT SAFE STEP',f'''```text
NEXT_SAFE_STEP={NEXT}
```

Build only an isolated read-only schema and temp-copy snapshot path. No production DB, service, timer or panel binding.''')
    MASTER.write_text(master,encoding='utf-8')

    hand=HANDOFF.read_text(encoding='utf-8')
    hand=sec(hand,'## 02 CURRENT CONTINUATION CHECKPOINT',f'''PROJECT_STATUS=ACTIVE_ERA56_GLOBAL_INTELLIGENCE_CACHE
CURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE
ERA56_STATUS=OPEN_BOUNDED_DESIGN_ONLY
CURRENT_STAGE=ERA56A_CONTRACT_LOCKED
LAST_COMPLETED_SUBSTEP={WORK}
ERA56_PRODUCTION_APPLY_AUTHORIZED=false
PRODUCTION_MUTATION=false
CURRENT_HEAD=DYNAMIC_USE_GIT_REV_PARSE_HEAD''')
    hand=sec(hand,'## 03 LAST VERIFIED WORK',f'''LAST_COMPLETED={WORK}
LAST_RESULT={RESULT}
LAST_ARTIFACT={rel}
WORK_UNIT_STATUS=CLOSED_CONTRACT_LOCKED
CURRENT_PROBLEM=ERA56B_READONLY_SCHEMA_AND_TEMP_COPY_BUILD_PENDING''')
    hand=sec(hand,'## 07 ALLOWED NEXT DECISIONS',f'''- ERA56 ownership contract: `LOCKED`.
- ERA56 overlap contract: `LOCKED`.
- ERA56 rebuild contract: `LOCKED`.
- Production apply: `BLOCKED`.
- Next build may use only isolated temp-copy or new cache file.

NEXT_SAFE_STEP={NEXT}''')
    HANDOFF.write_text(hand,encoding='utf-8')

    hist=load(HISTORY);events=hist.setdefault('events',[])
    if not any(isinstance(x,dict) and x.get('event_id')==WORK for x in events):
        events.append({'event_id':WORK,'timestamp_utc':ts,'era':'ERA56','status':'CLOSED_CONTRACT_LOCKED','result':RESULT,'artifact':rel,'production_mutation':False,'next_safe_step':NEXT})
    hist['updated_at']=ts;hist['updated_at_utc']=ts;dump(HISTORY,hist)

    marker='## ERA56A GLOBAL CACHE OWNERSHIP OVERLAP AND REBUILD CONTRACT'
    alm=ALMANAC.read_text(encoding='utf-8')
    if marker not in alm:
        ALMANAC.write_text(alm.rstrip()+f'''\n\n---\n\n{marker}\n\n- Status: `CLOSED_CONTRACT_LOCKED`\n- Result: `{RESULT}`\n- Production mutation: `false`\n- Production apply authorized: `false`\n- Next safe step: `{NEXT}`\n''',encoding='utf-8')

    TK_AI.write_text(f'''# LATEST TK AI HANDOFF\n\nCURRENT_STATE_AUTHORITY=PROJECT_RUNTIME.json\nSTATE_SYNC_UTC={ts}\nCURRENT_ERA=ERA56_GLOBAL_INTELLIGENCE_CACHE\nCURRENT_STAGE=ERA56A_CONTRACT_LOCKED\nLAST_COMPLETED={WORK}\nLAST_RESULT={RESULT}\nERA56_PRODUCTION_APPLY_AUTHORIZED=false\nPRODUCTION_MUTATION=false\nNEXT_SAFE_STEP={NEXT}\n\nERA56 owns only immutable, derived and fully rebuildable global snapshots. Existing ledgers, runtime DB tables, ingress layers and owner-specific readmodels remain authoritative.\n''',encoding='utf-8')

    machine=load(MACHINE);machine['created_at_utc']=ts;machine['collect_mode']='canonical_sync_snapshot_no_tk_machine';machine['current_state']={'authority':'PROJECT_RUNTIME.json','runtime_status':'ERA56_OPEN_DESIGN_ONLY','active_work_unit':{'id':WORK,'status':'CLOSED_CONTRACT_LOCKED','artifact':rel},'next_safe_step':{'name':NEXT,'status':'READY'},'last_action':{'timestamp':ts,'task':WORK,'result':RESULT,'artifact':rel}};machine['known_facts']={'era56_opened':True,'era56_stage':'ERA56A_CONTRACT_LOCKED','ownership_contract_locked':True,'overlap_contract_locked':True,'rebuild_contract_locked':True,'era56_production_apply_authorized':False,'production_mutation':False};dump(MACHINE,machine)

    for path in (RUNTIME,ROADMAP,HISTORY,MACHINE,ARTIFACT):load(path)
    if git('rev-list','-n1',SEAL_TAG)!=SEAL_COMMIT:raise RuntimeError('ERA55_SEAL_CHANGED')
    git('add','-A');check=run(['git','diff','--cached','--check'],check=False)
    if check.returncode!=0:
        print(check.stdout,end='');print(check.stderr,end='');raise RuntimeError('DIFF_CHECK_FAILED')
    git('commit','-m',SUBJECT)
    print('ERA56A_CONTRACT=SUCCESS');print('OWNERSHIP_CONTRACT_LOCKED=true');print('OVERLAP_CONTRACT_LOCKED=true');print('REBUILD_CONTRACT_LOCKED=true');print('ERA56_PRODUCTION_APPLY_AUTHORIZED=false');print('PRODUCTION_MUTATION=false');print('NEXT_SAFE_STEP='+NEXT);print('LOCAL_COMMIT='+git('rev-parse','HEAD'))
    return 0

if __name__=='__main__':raise SystemExit(main())
