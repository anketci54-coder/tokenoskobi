#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

ROOT=/root/tokenoskobi_clean_v1
EXPECTED_HEAD=e2c867d4fc14ed67af0ea096563a4f768e51c06e
FIX6_BRANCH=agent/product-slice-02-fix6-bounded-recovery
EXPECTED_FIX6_HEAD=4b67cd0e3f631a9fb1e3de5fde831fd882f22e9d
SERVICE=tokenoskobi-product-slice-02.service
OLD_SERVICE=tokenoskobi-active-panel-8096.service
SERVER=tools/tokenoskobi_product_slice_02_server.py
CONFIG=config/product_slice_02_v1.json
TEST=tests/test_product_slice_02.py
UNIT=systemd_drafts/tokenoskobi-product-slice-02.service
NGINX_REPO=config/nginx/panel.coinoskobi.xyz.conf
SMOKE=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c
STATUS=PRODUCT_SLICE_02_MACHINE_RECOVERED_PHONE_ACCEPTANCE_PENDING
NEXT=PHONE_AUTHENTICATED_PRODUCT_SLICE_02_ACCEPTANCE
ARTIFACT=data/control/product_slice_02_machine_recovery_seal_v1.json
BACKUP=''
COMMITTED=0

EXPECTED_SERVER_SHA256=a2bcb0a413a04fbd49244fab987d9b55396f58af76567e7b3f36bec6fd41f024
EXPECTED_CONFIG_SHA256=7d6c2fcc53e476d1f1c8633de2270480a336328649982dce5ac7bf9092bceb6a
EXPECTED_TEST_SHA256=a61ce9ada03de21208fe871e94a0ea86f436e4091c45248d2975fcc6e99bca19
EXPECTED_UNIT_SHA256=68cc97df0c789ed83b7d27fbacd7442616fce979f69dad3a4e7320f9cc373597

say(){ printf '%s\n' "$@"; }
fail(){ say "BLOCKED=$*" >&2; return 1; }
http_code(){ curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 20 "$1" 2>/dev/null || true; }
api_code(){ curl -sS -o "$1" -w '%{http_code}' --connect-timeout 5 --max-time 150 -H 'Content-Type: application/json' --data '{"token_address":"'"$SMOKE"'"}' "$2" 2>/dev/null || true; }
api_noauth_code(){ curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 30 -H 'Content-Type: application/json' --data '{"token_address":"'"$SMOKE"'"}' "$1" 2>/dev/null || true; }

rollback(){
  rc=$?
  trap - ERR INT TERM
  set +e
  if [[ "$COMMITTED" -eq 0 && -n "$BACKUP" && -f "$BACKUP/repo_before.tar.gz" ]]; then
    rm -f \
      tools/tokenoskobi_product_slice_02_fix6_bounded_recovery.sh \
      tools/tokenoskobi_product_slice_02_fix6_helper.py \
      tools/tokenoskobi_product_slice_02_fix6_resume_nginx_recovery.sh \
      tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh \
      tools/tokenoskobi_product_slice_02_machine_recovery_seal_fix1.sh \
      tools/tokenoskobi_product_slice_02_machine_recovery_seal_fix2.sh \
      data/control/product_slice_02_single_token_decision_packet_v1.json \
      data/control/product_slice_02_smoke_analysis_v1.json \
      data/control/product_slice_02_nginx_route_recovery_v1.json \
      data/control/product_slice_02_machine_recovery_seal_v1.json \
      reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md
    tar -xzf "$BACKUP/repo_before.tar.gz" -C "$ROOT"
    git reset --quiet >/dev/null 2>&1 || true
  fi
  say PRODUCT_SLICE_02_MACHINE_SEAL_RESULT=FAILED
  say FAILED_RC=$rc
  say SERVICE_RESTART=NONE
  say NGINX_RELOAD=NONE
  say LIVE_TRADE=DISABLED
  say REAL_FINANCIAL_AUTHORITY=0
  exit "$rc"
}
trap rollback ERR INT TERM

[[ "${PRODUCT_SLICE_02_MACHINE_SEAL_CONFIRM:-}" == YES ]] || fail CONFIRMATION_MISSING
[[ "$(git branch --show-current)" == main ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail HEAD_NOT_EXACT_E2C867D
[[ "$(git rev-parse origin/main)" == "$EXPECTED_HEAD" ]] || fail ORIGIN_MAIN_NOT_EXACT_E2C867D
[[ "$(git rev-parse "origin/$FIX6_BRANCH")" == "$EXPECTED_FIX6_HEAD" ]] || fail FIX6_BRANCH_HEAD_CHANGED

EXPECTED_INITIAL=$' M systemd_drafts/tokenoskobi-product-slice-02.service\n M tests/test_product_slice_02.py\n?? config/nginx/panel.coinoskobi.xyz.conf\n?? config/product_slice_02_v1.json\n?? tools/tokenoskobi_product_slice_02_server.py'
ACTUAL_INITIAL="$(git status --short --untracked-files=all)"
[[ "$ACTUAL_INITIAL" == "$EXPECTED_INITIAL" ]] || {
  say EXPECTED_INITIAL_STATUS_BEGIN
  say "$EXPECTED_INITIAL"
  say EXPECTED_INITIAL_STATUS_END
  say ACTUAL_INITIAL_STATUS_BEGIN
  say "$ACTUAL_INITIAL"
  say ACTUAL_INITIAL_STATUS_END
  fail INITIAL_WORKTREE_SCOPE_CHANGED
}

[[ "$(sha256sum "$SERVER" | awk '{print $1}')" == "$EXPECTED_SERVER_SHA256" ]] || fail SERVER_SHA_MISMATCH
[[ "$(sha256sum "$CONFIG" | awk '{print $1}')" == "$EXPECTED_CONFIG_SHA256" ]] || fail CONFIG_SHA_MISMATCH
[[ "$(sha256sum "$TEST" | awk '{print $1}')" == "$EXPECTED_TEST_SHA256" ]] || fail TEST_SHA_MISMATCH
[[ "$(sha256sum "$UNIT" | awk '{print $1}')" == "$EXPECTED_UNIT_SHA256" ]] || fail UNIT_SHA_MISMATCH
[[ -f "$NGINX_REPO" ]] || fail NGINX_REPO_FILE_MISSING

python3 -m py_compile "$SERVER" "$TEST"
python3 -m unittest -v "$TEST"

systemctl is-active --quiet "$SERVICE" || fail SERVICE_NOT_ACTIVE
systemctl is-enabled --quiet "$SERVICE" || fail SERVICE_NOT_ENABLED
[[ "$(systemctl is-active "$OLD_SERVICE" 2>/dev/null || true)" != active ]] || fail OLD_SERVICE_ACTIVE
PID="$(systemctl show "$SERVICE" -p MainPID --value)"
[[ "$PID" =~ ^[1-9][0-9]*$ && -d "/proc/$PID" ]] || fail MAINPID_INVALID
tr '\0' ' ' <"/proc/$PID/cmdline" | grep -Fq "$ROOT/$SERVER" || fail PROCESS_PATH_UNEXPECTED

LISTEN="$(ss -ltnp 2>/dev/null | awk '$4 ~ /:8096$/ {print}')"
[[ -n "$LISTEN" ]] || fail PORT_8096_NOT_LISTENING
grep -q '127.0.0.1:8096' <<<"$LISTEN" || fail PORT_8096_NOT_LOOPBACK
! grep -Eq '0\.0\.0\.0:8096|\[::\]:8096' <<<"$LISTEN" || fail PORT_8096_PUBLIC
[[ "$(http_code http://127.0.0.1:8096/)" == 200 ]] || fail LOCAL_ROOT_NOT_200
[[ "$(http_code http://127.0.0.1:8096/healthz)" == 200 ]] || fail LOCAL_HEALTH_NOT_200
[[ "$(http_code https://panel.coinoskobi.xyz/panel/panel_v2/)" == 401 ]] || fail EXTERNAL_PANEL_NOT_401
[[ "$(http_code https://panel.coinoskobi.xyz/)" == 401 ]] || fail EXTERNAL_ROOT_NOT_401
[[ "$(api_noauth_code https://panel.coinoskobi.xyz/api/v1/analyze)" == 401 ]] || fail EXTERNAL_API_NOT_401
[[ "$(http_code https://panel.coinoskobi.xyz/healthz)" == 200 ]] || fail EXTERNAL_HEALTH_NOT_200
nginx -t >/dev/null 2>&1 || fail NGINX_INVALID

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
BACKUP="/root/tokenoskobi_product_slice_02_machine_seal_${STAMP}"
mkdir -p "$BACKUP"

BACKUP_PATHS=(
  04_ALMANAC.md 05_ATLAS.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md
  PROJECT_RUNTIME.json PROJECT_HISTORY.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
  reports/LATEST_TK_AI_HANDOFF.md
)
tar -czf "$BACKUP/repo_before.tar.gz" -C "$ROOT" "${BACKUP_PATHS[@]}"

install -d -m 0755 tools data/control reports
for rel in \
  tools/tokenoskobi_product_slice_02_fix6_bounded_recovery.sh \
  tools/tokenoskobi_product_slice_02_fix6_helper.py \
  tools/tokenoskobi_product_slice_02_fix6_resume_nginx_recovery.sh \
  tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh \
  tools/tokenoskobi_product_slice_02_machine_recovery_seal_fix1.sh \
  tools/tokenoskobi_product_slice_02_machine_recovery_seal_fix2.sh
do
  if [[ "$rel" == tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh ]]; then
    cp "$PRODUCT_SLICE_02_PATCHED_SELF" "$rel"
  else
    git show "$EXPECTED_FIX6_HEAD:$rel" > "$rel"
  fi
done
chmod 0755 \
  tools/tokenoskobi_product_slice_02_fix6_bounded_recovery.sh \
  tools/tokenoskobi_product_slice_02_fix6_helper.py \
  tools/tokenoskobi_product_slice_02_fix6_resume_nginx_recovery.sh \
  tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh \
  tools/tokenoskobi_product_slice_02_machine_recovery_seal_fix1.sh \
  tools/tokenoskobi_product_slice_02_machine_recovery_seal_fix2.sh

SMOKE_JSON="$BACKUP/smoke.json"
LOCAL_API="$(api_code "$SMOKE_JSON" http://127.0.0.1:8096/api/v1/analyze)"
[[ "$LOCAL_API" == 200 ]] || fail LOCAL_API_$LOCAL_API

PID="$PID" NOW="$NOW" STATUS="$STATUS" NEXT="$NEXT" ARTIFACT="$ARTIFACT" SMOKE_JSON="$SMOKE_JSON" python3 - <<'PY'
from __future__ import annotations
import json, os
from pathlib import Path

root=Path('/root/tokenoskobi_clean_v1')
now=os.environ['NOW']
status=os.environ['STATUS']
next_step=os.environ['NEXT']
artifact=os.environ['ARTIFACT']
pid=int(os.environ['PID'])
smoke=json.loads(Path(os.environ['SMOKE_JSON']).read_text(encoding='utf-8'))

authority=smoke.get('authority',{})
assert all(authority.get(k) is False for k in ('paper','live','wallet','signing','order','broadcast'))
assert authority.get('human_action_required') is True
assert smoke.get('decision',{}).get('authority') == 'ADVISORY_ONLY'

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

write_json(root/'data/control/product_slice_02_smoke_analysis_v1.json',smoke)

packet={
  'schema':'tokenoskobi.product_slice_02.single_token_decision_packet.v1',
  'generated_at_utc':now,
  'stage':'PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET',
  'status':status,
  'phone_acceptance':'NOT_REPORTED_NOT_AUTOMATION_VERIFIED',
  'token_address':smoke.get('token_address'),
  'decision':smoke.get('decision'),
  'provider':smoke.get('provider'),
  'contract':smoke.get('contract'),
  'market':smoke.get('market'),
  'technical_timeframes':smoke.get('technical_timeframes'),
  'news':smoke.get('news'),
  'authority':authority,
  'visible_product':{
    'local_root_http':200,
    'local_health_http':200,
    'external_panel_unauth_http':401,
    'external_api_unauth_http':401,
    'external_health_http':200,
    'basic_auth_enforced':True,
    'loopback_service':True,
    'main_pid':pid,
  },
  'next_safe_step':next_step,
}
write_json(root/'data/control/product_slice_02_single_token_decision_packet_v1.json',packet)

nginx={
  'schema':'tokenoskobi.product_slice_02.nginx_route_recovery.v1',
  'generated_at_utc':now,
  'diagnosed_cause':'STATIC_ALIAS_TRY_FILES_CONCATENATED_INDEX_TO_FILE',
  'observed_error_path':'/var/www/tokenoskobi_public/panel/panel_v2/index.htmlindex.html',
  'repair':'REMOVED_STATIC_PANEL_SHADOW_LOCATIONS_AND_ENFORCED_BASIC_AUTH_ON_ROOT_PROXY',
  'active_route':'ROOT_REVERSE_PROXY_TO_127_0_0_1_8096',
  'external_panel_unauth_http':401,
  'external_api_unauth_http':401,
  'external_health_http':200,
  'nginx_syntax':True,
  'service_restart_during_nginx_resume':False,
  'authority_change':False,
}
write_json(root/'data/control/product_slice_02_nginx_route_recovery_v1.json',nginx)

closure={
  'schema':'tokenoskobi.product_slice_02.machine_recovery_seal.v1',
  'generated_at_utc':now,
  'source_head_before_commit':'e2c867d4fc14ed67af0ea096563a4f768e51c06e',
  'fix6_evidence_head':'4b67cd0e3f631a9fb1e3de5fde831fd882f22e9d',
  'stage':'PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET',
  'status':status,
  'classification':'VALID_DEPLOYMENT_MACHINE_VERIFIED_PHONE_ACCEPTANCE_PENDING',
  'source_reconstructed':True,
  'source_restart_verified':True,
  'service_active':True,
  'main_pid':pid,
  'loopback_only':True,
  'local_root_http':200,
  'local_health_http':200,
  'external_panel_unauth_http':401,
  'external_api_unauth_http':401,
  'external_health_http':200,
  'basic_auth_enforced':True,
  'phone_acceptance':'NOT_REPORTED_NOT_AUTOMATION_VERIFIED',
  'unit_tests':'5/5_PASS',
  'smoke_decision':smoke.get('decision',{}).get('decision'),
  'smoke_data_quality':smoke.get('decision',{}).get('data_quality'),
  'paper_trade':'DISABLED',
  'live_trade':'DISABLED',
  'real_wallet_signing_order_trade_authority':0,
  'risk_engine_veto':True,
  'human_action_required':True,
  'canonical_claim_limit':'MACHINE_RECOVERY_ONLY_NOT_USER_ACCEPTANCE',
  'next_safe_step':next_step,
  'artifacts':[
    'data/control/product_slice_02_single_token_decision_packet_v1.json',
    'data/control/product_slice_02_smoke_analysis_v1.json',
    'data/control/product_slice_02_nginx_route_recovery_v1.json',
    'reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md',
  ],
}
write_json(root/artifact,closure)

runtime_path=root/'PROJECT_RUNTIME.json'
runtime=json.loads(runtime_path.read_text(encoding='utf-8'))
runtime['product_slice_02_recovery']=closure
runtime['current_stage']='PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET'
runtime['current_status']=status
runtime['next_safe_step']=next_step
runtime['updated_at_utc']=now
ptr=runtime.setdefault('canonical_runtime_pointer',{})
ptr['current_stage']='PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET'
ptr['current_status']=status
ptr['next_safe_step']=next_step
ptr['product_slice_02_recovery']=closure
write_json(runtime_path,runtime)

history_path=root/'PROJECT_HISTORY.json'
history=json.loads(history_path.read_text(encoding='utf-8'))
events=history.setdefault('events',[])
events.append({
  'timestamp_utc':now,
  'event':'PRODUCT_SLICE_02_MACHINE_RECOVERY_SEAL',
  'event_id':'PRODUCT_SLICE_02_MACHINE_RECOVERY_SEAL_V1',
  'status':status,
  'artifact':artifact,
  'source_reconstructed':True,
  'service_restart_verified':True,
  'nginx_external_500_fixed':True,
  'basic_auth_enforced':True,
  'phone_acceptance':'NOT_REPORTED_NOT_AUTOMATION_VERIFIED',
  'authority_change':False,
  'next_safe_step':next_step,
})
history['updated_at_utc']=now
write_json(history_path,history)

road_path=root/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
road=json.loads(road_path.read_text(encoding='utf-8'))
direction=road.setdefault('current_direction',{})
direction['current_stage']='PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET'
direction['current_status']=status
direction['next_safe_step']=next_step
direction['updated_at_utc']=now
road['product_slice_02_recovery']=closure
write_json(road_path,road)

machine_path=root/'data/control/latest_tk_machine_state.json'
machine=json.loads(machine_path.read_text(encoding='utf-8'))
machine['product_slice_02_recovery']=closure
machine['current_stage']='PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET'
machine['current_status']=status
machine['next_safe_step']=next_step
machine['updated_at_utc']=now
write_json(machine_path,machine)

almanac_path=root/'04_ALMANAC.md'
almanac=almanac_path.read_text(encoding='utf-8')
begin='<!-- PRODUCT_SLICE_02_MACHINE_RECOVERY:BEGIN -->'
end='<!-- PRODUCT_SLICE_02_MACHINE_RECOVERY:END -->'
block=f'''{begin}
## Product Slice 02 Machine Recovery

- Timestamp UTC: `{now}`
- Status: `{status}`
- Source reconstructed and restart verified: `true`
- Service: `active`, PID `{pid}`, `127.0.0.1:8096`
- Local root/health: `200/200`
- External panel/API unauthenticated: `401/401`
- External health: `200`
- Nginx static-shadow HTTP 500: `FIXED`
- Basic Auth: `ENFORCED`
- Unit tests: `5/5 PASS`
- Phone acceptance: `NOT_REPORTED_NOT_AUTOMATION_VERIFIED`
- Paper/live/wallet/signing/order/trade authority: `DISABLED / 0`
- Artifact: `{artifact}`
- Next: `{next_step}`
{end}

'''
if begin in almanac:
    pre=almanac.split(begin,1)[0]
    post=almanac.split(end,1)[1].lstrip('\n')
    almanac=pre+block+post
else:
    title,rest=almanac.split('\n',1)
    almanac=title+'\n\n'+block+rest.lstrip('\n')
almanac_path.write_text(almanac,encoding='utf-8')

atlas_path=root/'05_ATLAS.md'
atlas=atlas_path.read_text(encoding='utf-8')
begin='<!-- PRODUCT_SLICE_02_RUNTIME_PATH:BEGIN -->'
end='<!-- PRODUCT_SLICE_02_RUNTIME_PATH:END -->'
block=f'''{begin}
## PRODUCT SLICE 02 RUNTIME PATH

```text
PHONE / BROWSER
  -> HTTPS panel.coinoskobi.xyz
  -> BASIC AUTH
  -> NGINX ROOT REVERSE PROXY
  -> 127.0.0.1:8096
  -> PRODUCT SLICE 02 READ-ONLY SERVER
  -> BSC RPC + GECKOTERMINAL + LOCAL NEWS READ
  -> ALLOW / WAIT / REVIEW / BLOCK
  -> HUMAN ACTION REQUIRED
```

- Static alias shadow routes were removed.
- The Python source is present on disk and restart verified.
- The service binds only to loopback.
- Paper/live/wallet/signing/order/broadcast authority remains disabled.
- Phone-authenticated product acceptance remains a separate gate.
{end}

'''
if begin in atlas:
    pre=atlas.split(begin,1)[0]
    post=atlas.split(end,1)[1].lstrip('\n')
    atlas=pre+block+post
else:
    title,rest=atlas.split('\n',1)
    atlas=title+'\n\n'+block+rest.lstrip('\n')
atlas_path.write_text(atlas,encoding='utf-8')

(root/'06_PROJECT_MASTER_STATE.md').write_text(f'''# 06 PROJECT MASTER STATE

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE=PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET
CURRENT_STATUS={status}
PRODUCT_COMPLETION_DEADLINE=2026-09-01
NO_NEW_ERA=true
NEXT_SAFE_STEP={next_step}

PRODUCT_SLICE_02_SOURCE_PRESENT=true
PRODUCT_SLICE_02_RESTART_VERIFIED=true
PRODUCT_SLICE_02_SERVICE_ACTIVE=true
PRODUCT_SLICE_02_MAIN_PID={pid}
PANEL_LOOPBACK_ONLY=true
PANEL_LOCAL_ROOT_HEALTH=200_200
PANEL_HTTPS=true
PANEL_BASIC_AUTH_ENFORCED=true
PANEL_EXTERNAL_UNAUTH=401
PANEL_PHONE_ACCEPTANCE=false
NGINX_EXTERNAL_500_FIXED=true
SMOKE_DECISION={smoke.get('decision',{}).get('decision')}
SMOKE_DATA_QUALITY={smoke.get('decision',{}).get('data_quality')}
PAPER_RUNTIME=DISABLED
LIVE_TRADE=DISABLED
REAL_FINANCIAL_AUTHORITY=0
ARTIFACT={artifact}
''',encoding='utf-8')

(root/'07_PROJECT_HANDOFF.md').write_text(f'''# 07 PROJECT HANDOFF

CURRENT_STAGE=PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET
STATUS={status}
NEXT_SAFE_STEP={next_step}

Read `{artifact}` and `data/control/product_slice_02_single_token_decision_packet_v1.json`.

Product Slice 02 machine recovery is verified: source exists, restart passed, service is active on loopback, the Nginx HTTP 500 shadow route is fixed, and Basic Auth returns 401 without credentials. Phone-authenticated panel login and token-analysis acceptance have not been reported and must not be claimed as complete. No new ERA. Paper/live/wallet/signing/order authority remains disabled.
''',encoding='utf-8')

(root/'reports/LATEST_TK_AI_HANDOFF.md').write_text(f'''# TOKENOSKOBI LATEST HANDOFF

CURRENT_STAGE=PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET
STATUS={status}
NEXT_SAFE_STEP={next_step}
ARTIFACT={artifact}
PHONE_ACCEPTANCE=NOT_REPORTED_NOT_AUTOMATION_VERIFIED
PAPER_RUNTIME=DISABLED
LIVE_TRADE=DISABLED
REAL_FINANCIAL_AUTHORITY=0
''',encoding='utf-8')

(root/'reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md').write_text(f'''# PRODUCT SLICE 02 SINGLE TOKEN DECISION PACKET

- Generated UTC: `{now}`
- Status: `{status}`
- Token: `{smoke.get('token_address')}`
- Decision: `{smoke.get('decision',{}).get('decision')}`
- Risk score: `{smoke.get('decision',{}).get('risk_score')}`
- Data quality: `{smoke.get('decision',{}).get('data_quality')}`
- Source present and restart verified: `true`
- Service PID: `{pid}`
- Bind: `127.0.0.1:8096`
- Local root/health: `200/200`
- External panel/API unauthenticated: `401/401`
- External health: `200`
- Basic Auth: `ENFORCED`
- Phone acceptance: `NOT_REPORTED_NOT_AUTOMATION_VERIFIED`
- Paper/live authority: `DISABLED`
- Real financial authority: `0`
- Next: `{next_step}`
''',encoding='utf-8')
PY

python3 - <<'PY'
import json
from pathlib import Path
root=Path('/root/tokenoskobi_clean_v1')
paths=[
 'PROJECT_RUNTIME.json','PROJECT_HISTORY.json',
 'data/tokenoskobi_v1_v8_master_era_roadmap.json',
 'data/control/latest_tk_machine_state.json',
 'data/control/product_slice_02_single_token_decision_packet_v1.json',
 'data/control/product_slice_02_smoke_analysis_v1.json',
 'data/control/product_slice_02_nginx_route_recovery_v1.json',
 'data/control/product_slice_02_machine_recovery_seal_v1.json',
]
for rel in paths:
    json.loads((root/rel).read_text())
a=json.loads((root/'data/control/product_slice_02_machine_recovery_seal_v1.json').read_text())
assert a['phone_acceptance']=='NOT_REPORTED_NOT_AUTOMATION_VERIFIED'
assert a['live_trade']=='DISABLED'
assert a['real_wallet_signing_order_trade_authority']==0
assert a['external_panel_unauth_http']==401
print('CANONICAL_JSON_VALIDATION=PASS')
PY

python3 - <<'PYWS'
from pathlib import Path
p=Path("config/nginx/panel.coinoskobi.xyz.conf")
s=p.read_text(encoding="utf-8")
lines=s.splitlines(keepends=True)
out=[]
changed=0
for line in lines:
    ending=""
    body=line
    if line.endswith("\r\n"):
        body=line[:-2]; ending="\r\n"
    elif line.endswith("\n"):
        body=line[:-1]; ending="\n"
    clean=body.rstrip(" \t")
    changed += int(clean != body)
    out.append(clean+ending)
p.write_text("".join(out),encoding="utf-8")
print(f"NGINX_REPO_TRAILING_WHITESPACE_LINES_CLEANED={changed}")
PYWS
if grep -nE '[[:blank:]]+$' "$NGINX_REPO"; then fail NGINX_REPO_TRAILING_WHITESPACE_REMAINS; fi

git add \
  "$CONFIG" "$SERVER" "$TEST" "$UNIT" "$NGINX_REPO" \
  tools/tokenoskobi_product_slice_02_fix6_bounded_recovery.sh \
  tools/tokenoskobi_product_slice_02_fix6_helper.py \
  tools/tokenoskobi_product_slice_02_fix6_resume_nginx_recovery.sh \
  tools/tokenoskobi_product_slice_02_machine_recovery_seal.sh \
  tools/tokenoskobi_product_slice_02_machine_recovery_seal_fix1.sh \
  tools/tokenoskobi_product_slice_02_machine_recovery_seal_fix2.sh \
  data/control/product_slice_02_single_token_decision_packet_v1.json \
  data/control/product_slice_02_smoke_analysis_v1.json \
  data/control/product_slice_02_nginx_route_recovery_v1.json \
  data/control/product_slice_02_machine_recovery_seal_v1.json \
  PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json \
  04_ALMANAC.md 05_ATLAS.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md

git add -f \
  reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md \
  reports/LATEST_TK_AI_HANDOFF.md

[[ -z "$(git status --porcelain=v1 | awk '$1=="??"{print}')" ]] || fail UNTRACKED_FILES_REMAIN
git diff --cached --check
git diff --cached --name-status

git commit -m "Product: seal Slice 02 machine recovery pending phone acceptance"
COMMITTED=1
NEW_HEAD="$(git rev-parse HEAD)"
git push origin main
git fetch origin main --quiet
[[ "$(git rev-parse origin/main)" == "$NEW_HEAD" ]] || fail REMOTE_HEAD_MISMATCH
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail WORKTREE_NOT_CLEAN_AFTER_PUSH

say PRODUCT_SLICE_02_MACHINE_SEAL_RESULT=SUCCESS
say LOCAL_HEAD=$NEW_HEAD
say ORIGIN_MAIN=$NEW_HEAD
say SERVICE_ACTIVE="$(systemctl is-active "$SERVICE")"
say MAIN_PID=$PID
say PORT_8096=LOOPBACK_ONLY
say EXTERNAL_PANEL_UNAUTH_HTTP=401
say EXTERNAL_API_UNAUTH_HTTP=401
say EXTERNAL_HEALTH_HTTP=200
say PHONE_ACCEPTANCE=NOT_REPORTED_NOT_AUTOMATION_VERIFIED
say PAPER_TRADE=DISABLED
say LIVE_TRADE=DISABLED
say REAL_FINANCIAL_AUTHORITY=0
say CANONICAL_STATUS=$STATUS
say NEXT_SAFE_STEP=$NEXT
