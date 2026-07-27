#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

BASE_HEAD='d1d5078a7fb9bab7108755bf63806cb27f697007'
SERVICE='tokenoskobi-product-slice-02.service'
STATUS='PRODUCT_SLICE_02_CLOSED_VERIFIED_PHONE_ACCEPTED_GITHUB_SEALED'
NEXT='NEXT_WORK_UNIT_PLAN'
WBNB='0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'
USDT='0x55d398326f99059ff775485246999027b3197955'
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
BACKUP="/root/tokenoskobi_ps02_final_close_${STAMP}"
mkdir -p "$BACKUP"

fail(){ printf 'BLOCKED=%s\n' "$1" >&2; exit 1; }
code(){ curl -sS --connect-timeout 5 --max-time 25 -o /dev/null -w '%{http_code}' "$1" 2>/dev/null || true; }

[[ "${PRODUCT_SLICE_02_FINAL_CLOSE_CONFIRM:-}" == 'YES' ]] || fail CONFIRMATION_MISSING
[[ "$(git branch --show-current)" == 'main' ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$BASE_HEAD" ]] || fail LOCAL_HEAD_CHANGED
[[ "$(git rev-parse origin/main)" == "$BASE_HEAD" ]] || fail ORIGIN_MAIN_CHANGED

EXPECTED=$' M config/nginx/panel.coinoskobi.xyz.conf\n M systemd_drafts/tokenoskobi-product-slice-02.service\n M tests/test_product_slice_02.py\n M tools/tokenoskobi_product_slice_02_server.py'
[[ "$(git status --short --untracked-files=all)" == "$EXPECTED" ]] || fail WORKTREE_SCOPE_CHANGED

python3 -m py_compile tools/tokenoskobi_product_slice_02_server.py tests/test_product_slice_02.py
python3 tests/test_product_slice_02.py
nginx -t
systemctl is-active --quiet "$SERVICE" || fail SERVICE_NOT_ACTIVE
[[ "$(code http://127.0.0.1:8096/healthz)" == '200' ]] || fail LOCAL_HEALTH_NOT_200
[[ "$(code https://panel.coinoskobi.xyz/panel/panel_v2/)" == '401' ]] || fail PANEL_AUTH_GATE_CHANGED
[[ "$(code https://panel.coinoskobi.xyz/healthz)" == '200' ]] || fail EXTERNAL_HEALTH_NOT_200

printf 'GECKOTERMINAL_COOLDOWN_SEC=70\n'
sleep 70
curl -sS --connect-timeout 5 --max-time 600 -H 'Content-Type: application/json' \
  --data '{"token_address":"'"$WBNB"'"}' http://127.0.0.1:8096/api/v1/analyze > "$BACKUP/wbnb.json"
printf 'GECKOTERMINAL_SECOND_TOKEN_COOLDOWN_SEC=70\n'
sleep 70
curl -sS --connect-timeout 5 --max-time 600 -H 'Content-Type: application/json' \
  --data '{"token_address":"'"$USDT"'"}' http://127.0.0.1:8096/api/v1/analyze > "$BACKUP/usdt.json"

NOW="$NOW" STATUS="$STATUS" NEXT="$NEXT" BACKUP="$BACKUP" python3 - <<'PY'
import json, os
from pathlib import Path

root=Path('/root/tokenoskobi_clean_v1')
now=os.environ['NOW']; status=os.environ['STATUS']; nxt=os.environ['NEXT']; backup=Path(os.environ['BACKUP'])
wbnb=json.loads((backup/'wbnb.json').read_text())
usdt=json.loads((backup/'usdt.json').read_text())

def validate(p, addr, lo, hi, min_tf):
    assert p['token_address']==addr
    m=p['market']; pool=m['selected_pool']; d=p['decision']; a=p['authority']
    assert m['target_orientation_verified'] is True and pool['orientation_verified'] is True
    tp=float(m['token']['price_usd']); pp=float(pool['price_usd'])
    assert lo <= tp <= hi and lo <= pp <= hi and 0.75 <= tp/pp <= 1.25
    ok=[x for x in p['technical_timeframes'].values() if x.get('status')=='OK']
    assert len(ok)>=min_tf
    assert d['decision'] in ('ALLOW','WAIT','REVIEW') and d['data_quality']=='SUFFICIENT' and not d['blockers']
    assert all(a[k] is False for k in ('paper','live','wallet','signing','order','broadcast'))
    assert a['human_action_required'] is True
    return {'token_price_usd':tp,'pool_price_usd':pp,'technical_ok':len(ok),'decision':d['decision'],'risk_score':d['risk_score'],'data_quality':d['data_quality']}

ws=validate(wbnb,'0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',100,10000,4)
us=validate(usdt,'0x55d398326f99059ff775485246999027b3197955',0.5,2,2)

closure={
 'schema':'tokenoskobi.product_slice_02.phone_acceptance_closure.v1',
 'closed_at_utc':now,'status':status,'next_safe_step':nxt,
 'machine_acceptance':{'wbnb':ws,'usdt':us},
 'phone_acceptance':{
   'wbnb':{'visible_price_usd':574.1,'decision':'ALLOW','risk_score':30,'data_quality':'SUFFICIENT'},
   'usdt':{'visible_price_usd':0.9958780199,'decision':'ALLOW','risk_score':35,'data_quality':'SUFFICIENT'}},
 'systemd_hardening_preserved':True,'nginx_timeout_seconds':600,
 'paper_trade':'DISABLED','live_trade':'DISABLED','real_financial_authority':0,
 'issue':12,'pull_request':14}

def load(p): return json.loads(p.read_text())
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def replace(v,old,new):
    n=0
    if isinstance(v,dict):
      for k,x in list(v.items()):
        if x==old: v[k]=new; n+=1
        else: n+=replace(x,old,new)
    elif isinstance(v,list):
      for i,x in enumerate(v):
        if x==old: v[i]=new; n+=1
        else: n+=replace(x,old,new)
    return n

old_status='PRODUCT_SLICE_02_MACHINE_RECOVERED_PHONE_ACCEPTANCE_PENDING'
old_next='PHONE_AUTHENTICATED_PRODUCT_SLICE_02_ACCEPTANCE'
for rel in ('PROJECT_RUNTIME.json','data/tokenoskobi_v1_v8_master_era_roadmap.json','data/control/latest_tk_machine_state.json'):
    p=root/rel; obj=load(p)
    assert replace(obj,old_status,status)>=1
    assert replace(obj,old_next,nxt)>=1
    if rel=='PROJECT_RUNTIME.json': obj['canonical_runtime_pointer']['product_slice_02_phone_acceptance_closure']=closure
    if rel.endswith('latest_tk_machine_state.json'): obj['product_slice_02_phone_acceptance_closure']=closure
    save(p,obj)

hp=root/'PROJECT_HISTORY.json'; h=load(hp)
h['events'].append({'event':'PRODUCT_SLICE_02_PHONE_ACCEPTANCE_CLOSED','event_id':'PRODUCT_SLICE_02_PHONE_ACCEPTANCE_FINAL_CLOSURE_V1','timestamp_utc':now,**closure})
save(hp,h)

seal=root/'data/control/product_slice_02_machine_recovery_seal_v1.json'; s=load(seal)
s.update({'generated_at_utc':now,'status':status,'phone_acceptance':'AUTHENTICATED_USER_ACCEPTED_WBNB_AND_USDT','phone_acceptance_closure':closure,'unit_tests':'18/18_OK','next_safe_step':nxt})
save(seal,s)
save(root/'data/control/product_slice_02_smoke_analysis_v1.json',wbnb)
save(root/'data/control/product_slice_02_single_token_decision_packet_v1.json',{'schema':'tokenoskobi.product_slice_02.accepted_samples.v1','generated_at_utc':now,'status':status,'accepted_samples':{'wbnb':wbnb,'usdt':usdt},'authority':wbnb['authority'],'next_safe_step':nxt})

(root/'06_PROJECT_MASTER_STATE.md').write_text(f'''# 06 PROJECT MASTER STATE\n\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA64\nCURRENT_STAGE=PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET\nCURRENT_STATUS={status}\nNO_NEW_ERA=true\nNEXT_SAFE_STEP={nxt}\n\nPRODUCT_SLICE_02_CLOSED=true\nPHONE_WBNB_ACCEPTANCE=true\nPHONE_USDT_ACCEPTANCE=true\nTARGET_TOKEN_ORIENTATION_VERIFIED=true\nSYSTEMD_HARDENING_PRESERVED=true\nNGINX_TIMEOUT_SECONDS=600\nPAPER_RUNTIME=DISABLED\nLIVE_TRADE=DISABLED\nREAL_FINANCIAL_AUTHORITY=0\n''')
(root/'07_PROJECT_HANDOFF.md').write_text(f'''# 07 PROJECT HANDOFF\n\nCURRENT_STAGE=PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET\nSTATUS={status}\nNEXT_SAFE_STEP={nxt}\n\nProduct Slice 02 WBNB and BSC-USDT machine and authenticated-phone acceptance are verified. Target-token orientation, bounded GeckoTerminal pacing, service-specific runtime directory, Nginx timeout and Basic Auth are active. Paper/live/wallet/signing/order authority remains disabled.\n''')
(root/'reports/LATEST_TK_AI_HANDOFF.md').write_text(f'''# TOKENOSKOBI LATEST HANDOFF\n\nSTATUS={status}\nNEXT_SAFE_STEP={nxt}\nPHONE_WBNB_ACCEPTANCE=VERIFIED\nPHONE_USDT_ACCEPTANCE=VERIFIED\nLIVE_TRADE=DISABLED\nREAL_FINANCIAL_AUTHORITY=0\n''')

ap=root/'04_ALMANAC.md'; text=ap.read_text(); b='<!-- PRODUCT_SLICE_02_MACHINE_RECOVERY:BEGIN -->'; e='<!-- PRODUCT_SLICE_02_MACHINE_RECOVERY:END -->'; i=text.index(b); j=text.index(e)+len(e)
section=f'''{b}\n## Product Slice 02 Final Acceptance\n\n- Closed UTC: `{now}`\n- Status: `{status}`\n- WBNB phone: `574.1 USD / ALLOW / 30 / SUFFICIENT`\n- USDT phone: `0.9958780199 USD / ALLOW / 35 / SUFFICIENT`\n- Target-token orientation: `VERIFIED`\n- Unit tests: `18/18 OK`\n- Systemd hardening: `PRESERVED`\n- Nginx timeout: `600s`\n- Paper/live authority: `DISABLED / 0`\n- Next: `{nxt}`\n{e}'''
ap.write_text(text[:i]+section+text[j:])
print('CANONICAL_SYNC=OK')
PY

for f in PROJECT_RUNTIME.json PROJECT_HISTORY.json data/tokenoskobi_v1_v8_master_era_roadmap.json data/control/latest_tk_machine_state.json data/control/product_slice_02_machine_recovery_seal_v1.json data/control/product_slice_02_single_token_decision_packet_v1.json; do python3 -m json.tool "$f" >/dev/null; done

git add -- config/nginx/panel.coinoskobi.xyz.conf systemd_drafts/tokenoskobi-product-slice-02.service tests/test_product_slice_02.py tools/tokenoskobi_product_slice_02_server.py
git commit -m 'fix(product): correct target-token orientation and bounded transport'

git add -- 04_ALMANAC.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md PROJECT_RUNTIME.json PROJECT_HISTORY.json data/tokenoskobi_v1_v8_master_era_roadmap.json data/control/latest_tk_machine_state.json data/control/product_slice_02_machine_recovery_seal_v1.json data/control/product_slice_02_single_token_decision_packet_v1.json data/control/product_slice_02_smoke_analysis_v1.json reports/LATEST_TK_AI_HANDOFF.md
git commit -m 'chore(canonical): close Product Slice 02 phone acceptance'

[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail WORKTREE_NOT_CLEAN
git fetch --quiet origin main
[[ "$(git rev-parse origin/main)" == "$BASE_HEAD" ]] || fail ORIGIN_MAIN_MOVED
git push origin HEAD:main
git fetch --quiet origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || fail REMOTE_VERIFY_FAILED

printf 'PRODUCT_SLICE_02_FINAL_CLOSURE=SUCCESS\n'
printf 'FINAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'WORKTREE_CLEAN=true\n'
printf 'PHONE_WBNB_ACCEPTANCE=VERIFIED\n'
printf 'PHONE_USDT_ACCEPTANCE=VERIFIED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'
printf 'NEXT_SAFE_STEP=%s\n' "$NEXT"
