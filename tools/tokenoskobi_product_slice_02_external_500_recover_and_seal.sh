#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

ROOT=/root/tokenoskobi_clean_v1
SELF=tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh
SERVICE=tokenoskobi-product-slice-02.service
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_02_recovery_${STAMP}"
NGINX_LINK=/etc/nginx/sites-enabled/panel.coinoskobi.xyz.conf
NGINX_SITE="$(readlink -f "$NGINX_LINK" 2>/dev/null || true)"
REPO_NGINX=config/nginx/panel.coinoskobi.xyz.conf
COMMITTED=0

REPO_PATHS=(
  config/product_slice_02_v1.json
  config/nginx/panel.coinoskobi.xyz.conf
  tools/tokenoskobi_product_slice_02_server.py
  tests/test_product_slice_02.py
  systemd_drafts/tokenoskobi-product-slice-02.service
  data/control/product_slice_02_single_token_decision_packet_v1.json
  data/control/product_slice_02_smoke_analysis_v1.json
  data/control/product_slice_02_nginx_route_recovery_v1.json
  reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md
  reports/LATEST_TK_AI_HANDOFF.md
  03_ROADMAP.md 04_ALMANAC.md 05_ATLAS.md
  06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md
  PROJECT_RUNTIME.json PROJECT_HISTORY.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
  tools/tokenoskobi_product_slice_02_single_token_deploy.sh
  tools/tokenoskobi_product_slice_02_single_token_deploy_fix1.sh
  tools/tokenoskobi_product_slice_02_external_500_diagnose.sh
  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh
)

rollback() {
  rc=$?
  trap - ERR
  if [[ "$COMMITTED" -eq 0 ]]; then
    if [[ -f "$BACKUP_DIR/nginx_site.conf" && -n "$NGINX_SITE" ]]; then
      cp -a "$BACKUP_DIR/nginx_site.conf" "$NGINX_SITE" || true
      nginx -t >/dev/null 2>&1 && systemctl reload nginx >/dev/null 2>&1 || true
    fi
    for p in "${REPO_PATHS[@]}"; do rm -rf -- "$ROOT/$p"; done
    [[ -f "$BACKUP_DIR/repo_paths.tar.gz" ]] && tar -xzf "$BACKUP_DIR/repo_paths.tar.gz" -C "$ROOT" || true
    git reset --quiet >/dev/null 2>&1 || true
    echo ROLLBACK=COMPLETED_TO_PRE_RECOVERY_PARTIAL_STATE
  else
    echo ROLLBACK=NOT_APPLIED_AFTER_COMMIT
  fi
  exit "$rc"
}
trap rollback ERR

[[ "$(git branch --show-current)" == main ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -n "$NGINX_SITE" && -f "$NGINX_SITE" ]]
[[ -f "$REPO_NGINX" ]]
[[ -f config/product_slice_02_v1.json ]]
[[ -f tools/tokenoskobi_product_slice_02_server.py ]]
[[ -f data/control/product_slice_02_smoke_analysis_v1.json ]]
systemctl is-active --quiet "$SERVICE"

python3 - <<'PY'
import subprocess
allowed={
 'config/product_slice_02_v1.json',
 'data/control/product_slice_02_smoke_analysis_v1.json',
 'systemd_drafts/tokenoskobi-product-slice-02.service',
 'tests/test_product_slice_02.py',
 'tools/tokenoskobi_product_slice_02_server.py',
}
rows=subprocess.check_output(['git','status','--porcelain=v1'],text=True).splitlines()
seen=set()
for row in rows:
    path=row[3:]
    if ' -> ' in path:path=path.split(' -> ',1)[1]
    seen.add(path)
unexpected=sorted(seen-allowed)
missing=sorted(allowed-seen)
if unexpected:raise SystemExit('BLOCKED=UNEXPECTED_DIRTY_PATHS:'+','.join(unexpected))
if missing:raise SystemExit('BLOCKED=EXPECTED_PARTIAL_PATHS_MISSING:'+','.join(missing))
print('PRODUCT_SLICE_02_PARTIAL_STATE=VERIFIED')
PY

mkdir -p "$BACKUP_DIR"
existing=()
for p in "${REPO_PATHS[@]}"; do [[ -e "$ROOT/$p" ]] && existing+=("$p"); done
if [[ ${#existing[@]} -gt 0 ]]; then
  tar -czf "$BACKUP_DIR/repo_paths.tar.gz" -C "$ROOT" "${existing[@]}"
else
  tar -czf "$BACKUP_DIR/repo_paths.tar.gz" --files-from /dev/null
fi
cp -a "$NGINX_SITE" "$BACKUP_DIR/nginx_site.conf"
echo BACKUP="$BACKUP_DIR"

python3 - "$NGINX_SITE" "$REPO_NGINX" <<'PY'
from pathlib import Path
import sys
headers=('location = /panel/panel_v2/ {','location ^~ /panel/panel_v2/ {')
def remove_blocks(text,header):
    count=0
    while True:
        start=text.find(header)
        if start<0:break
        brace=text.find('{',start)
        if brace<0:raise SystemExit('BLOCKED=NGINX_OPEN_BRACE_MISSING')
        depth=0;end=None
        for i in range(brace,len(text)):
            if text[i]=='{':depth+=1
            elif text[i]=='}':
                depth-=1
                if depth==0:end=i+1;break
        if end is None:raise SystemExit('BLOCKED=NGINX_CLOSE_BRACE_MISSING')
        line_start=text.rfind('\n',0,start)+1
        line_end=text.find('\n',end)
        line_end=len(text) if line_end<0 else line_end+1
        indent=text[line_start:start]
        text=text[:line_start]+indent+'# TOKENOSKOBI_PRODUCT_SLICE_02_ROUTE_USES_ROOT_REVERSE_PROXY\n'+text[line_end:]
        count+=1
    return text,count
for raw in sys.argv[1:]:
    p=Path(raw);text=p.read_text(encoding='utf-8');total=0
    for header in headers:
        text,n=remove_blocks(text,header);total+=n
    if total<2:raise SystemExit(f'BLOCKED=EXPECTED_BROKEN_PANEL_LOCATIONS_NOT_FOUND:{p}:{total}')
    if any(h in text for h in headers):raise SystemExit(f'BLOCKED=BROKEN_PANEL_LOCATION_REMAINS:{p}')
    if 'proxy_pass http://127.0.0.1:8096/;' not in text:raise SystemExit(f'BLOCKED=ROOT_REVERSE_PROXY_MISSING:{p}')
    p.write_text(text,encoding='utf-8')
    print(f'NGINX_PANEL_STATIC_SHADOW_ROUTES_REMOVED={p}:{total}')
PY

nginx -t
systemctl reload nginx
sleep 2

curl -fsS --max-time 8 http://127.0.0.1:8096/healthz >/tmp/s02_recovery_health.json
curl -fsS --max-time 8 http://127.0.0.1:8096/panel/panel_v2/ >/tmp/s02_recovery_local_panel.html
grep -q 'Tek Token Karar Paketi' /tmp/s02_recovery_local_panel.html
LISTEN="$(ss -ltnp 'sport = :8096' | tail -n +2 | head -n1)"
echo "$LISTEN" | grep -q '127.0.0.1:8096'
! echo "$LISTEN" | grep -Eq '0\.0\.0\.0:8096|\[::\]:8096'

SMOKE=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c
LOCAL_CODE="$(curl -sS --max-time 120 -o /tmp/s02_recovery_smoke.json -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"'"$SMOKE"'"}' http://127.0.0.1:8096/api/v1/analyze || true)"
[[ "$LOCAL_CODE" == 200 ]]
cp /tmp/s02_recovery_smoke.json data/control/product_slice_02_smoke_analysis_v1.json
EXT="$(curl -k -sS --max-time 20 -o /tmp/s02_recovery_external_panel.html -w '%{http_code}' https://panel.coinoskobi.xyz/panel/panel_v2/ || true)"
[[ "$EXT" == 200 ]]
grep -q 'Tek Token Karar Paketi' /tmp/s02_recovery_external_panel.html
EXT_API="$(curl -k -sS --max-time 120 -o /tmp/s02_recovery_external_api.json -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"'"$SMOKE"'"}' https://panel.coinoskobi.xyz/api/v1/analyze || true)"
[[ "$EXT_API" == 200 ]]

python3 - <<'PY'
import json
from pathlib import Path
for raw in ('/tmp/s02_recovery_smoke.json','/tmp/s02_recovery_external_api.json'):
    x=json.loads(Path(raw).read_text())
    assert x['schema']=='tokenoskobi.product_slice_02.packet.v1'
    assert all(x['authority'][k] is False for k in ('paper','live','wallet','signing','order','broadcast'))
print('PRODUCT_SLICE_02_LOCAL_AND_EXTERNAL_API=VERIFIED')
PY

python3 - "$EXT" "$EXT_API" "$LISTEN" "$NGINX_SITE" <<'PY'
import json,re,sys
from datetime import datetime,timezone
from pathlib import Path
root=Path('/root/tokenoskobi_clean_v1')
ext,ext_api,listen,nginx_site=sys.argv[1:5]
now=datetime.now(timezone.utc).isoformat()
sm=json.loads((root/'data/control/product_slice_02_smoke_analysis_v1.json').read_text())
p=sm['provider'];d=sm['decision'];n=sm['news']
remaining=['PANEL_AUTH_NOT_PROVEN']
if not p['alchemy_http_ok']:remaining.append('ALCHEMY_HTTP_NOT_WORKING')
if not p['hybrid_ready']:remaining.append('HYBRID_RPC_NOT_READY')
if not n['fresh']:remaining.append('NEWS_NOT_FRESH_WITHIN_6H')
remaining+=['UFW_FAIL2BAN_SSH_HARDENING_PENDING_ACCESS_SAFE_APPLY','NGINX_RATE_LIMIT_NOT_PROVEN']
recovery={
 'schema':'tokenoskobi.product_slice_02.nginx_route_recovery.v1',
 'generated_at_utc':now,
 'diagnosed_cause':'STATIC_ALIAS_TRY_FILES_CONCATENATED_INDEX_TO_FILE',
 'observed_error_path':'/var/www/tokenoskobi_public/panel/panel_v2/index.htmlindex.html',
 'repair':'REMOVED_STATIC_PANEL_INDEX_AND_PREFIX_SHADOW_LOCATIONS',
 'active_route':'ROOT_REVERSE_PROXY_TO_127_0_0_1_8096',
 'nginx_site':nginx_site,
 'nginx_syntax':True,
 'external_panel_http_code':ext,
 'external_api_http_code':ext_api,
 'authority_change':False,
}
(root/'data/control/product_slice_02_nginx_route_recovery_v1.json').write_text(json.dumps(recovery,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
a={
 'schema':'tokenoskobi.product_slice_02.deployment.v1',
 'stage':'PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET',
 'status':'DEPLOYED_VERIFIED_WITH_REMAINING_BLOCKERS',
 'generated_at_utc':now,
 'visible_product':{
   'external_url':'https://panel.coinoskobi.xyz/panel/panel_v2/',
   'external_http_code':ext,
   'external_api_http_code':ext_api,
   'single_token_input':True,
   'real_decision_packet':True,
   'timeframes':['1m','5m','15m','1h','4h','1d'],
   'explicit_insufficient_data':True,
 },
 'security':{
   'listen':listen,
   'loopback_only':True,
   'external_8096_binding_fixed':True,
   'nginx_external_500_fixed':True,
   'remaining_blockers':remaining,
 },
 'smoke':{
   'token_address':sm['token_address'],
   'decision':d['decision'],
   'data_quality':d['data_quality'],
   'risk_score':d['risk_score'],
   'public_rpc_ok':p['public_rpc_ok'],
   'alchemy_http_ok':p['alchemy_http_ok'],
   'hybrid_ready':p['hybrid_ready'],
   'news_fresh':n['fresh'],
 },
 'authority':{
   'paper_runtime':'DISABLED','live_trade':'DISABLED','wallet_authority':0,
   'signing_authority':0,'order_create_authority':0,'real_financial_authority':0,
 },
 'next_safe_step':'PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING',
}
(root/'data/control/product_slice_02_single_token_decision_packet_v1.json').write_text(json.dumps(a,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
(root/'reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md').write_text(
 f"# PRODUCT SLICE 02\n\n- Status: `{a['status']}`\n- URL: `{a['visible_product']['external_url']}`\n"
 f"- External panel/API: `{ext}` / `{ext_api}`\n- Nginx external 500 fixed: `true`\n"
 f"- 8096 loopback-only: `true`\n- Smoke: `{d['decision']}` / `{d['data_quality']}`\n"
 f"- Public RPC / Alchemy / Hybrid: `{p['public_rpc_ok']}` / `{p['alchemy_http_ok']}` / `{p['hybrid_ready']}`\n"
 f"- NEWS fresh: `{n['fresh']}`\n- Authority: `DISABLED / 0`\n- Next: `{a['next_safe_step']}`\n"
)
def load(path):return json.loads(path.read_text())
def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
rp=root/'PROJECT_RUNTIME.json';r=load(rp);r['current_stage']=a['stage'];r['current_status']=a['status'];r['next_safe_step']=a['next_safe_step'];r['last_result']=a['status'];r['product_slice_02']=a;r['updated_at_utc']=now;dump(rp,r)
hp=root/'PROJECT_HISTORY.json';h=load(hp);h.setdefault('events',[]).append({'event':'PRODUCT_SLICE_02_DEPLOYED','event_id':'PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET_V1','timestamp_utc':now,'status':a['status'],'artifact':'data/control/product_slice_02_single_token_decision_packet_v1.json','nginx_recovery_artifact':'data/control/product_slice_02_nginx_route_recovery_v1.json','authority_change':False,'next_safe_step':a['next_safe_step']});dump(hp,h)
mp=root/'data/tokenoskobi_v1_v8_master_era_roadmap.json';m=load(mp);m['current_stage']=a['stage'];m['current_status']=a['status'];m['next_safe_step']=a['next_safe_step'];m['product_slice_02']=a;m['updated_at_utc']=now;dump(mp,m)
sp=root/'data/control/latest_tk_machine_state.json';s=load(sp);c=s.setdefault('canonical_runtime_pointer',{});c['current_stage']=a['stage'];c['current_status']=a['status'];c['next_safe_step']=a['next_safe_step'];c['product_slice_02']=a;s['updated_at_utc']=now;dump(sp,s)
section=f'''<!-- PRODUCT_SLICE_02:BEGIN -->
## Product Slice 02 — Tek Token Karar Paketi

- Status: `{a['status']}`
- URL: `{a['visible_product']['external_url']}`
- External panel/API: `{ext}` / `{ext_api}`
- Tek token gerçek karar paketi: `true`
- Nginx external 500: `FIXED`
- 8096: `LOOPBACK_ONLY`
- Smoke: `{d['decision']}` / `{d['data_quality']}`
- Public RPC / Alchemy / Hybrid: `{p['public_rpc_ok']}` / `{p['alchemy_http_ok']}` / `{p['hybrid_ready']}`
- NEWS fresh: `{n['fresh']}`
- Authority: `PAPER_DISABLED; LIVE_DISABLED; REAL_FINANCIAL_AUTHORITY_0`
- Next: `{a['next_safe_step']}`
<!-- PRODUCT_SLICE_02:END -->'''
for name in ('03_ROADMAP.md','04_ALMANAC.md','05_ATLAS.md','06_PROJECT_MASTER_STATE.md','07_PROJECT_HANDOFF.md','reports/LATEST_TK_AI_HANDOFF.md'):
    path=root/name;old=path.read_text();pat=re.compile(r'<!-- PRODUCT_SLICE_02:BEGIN -->.*?<!-- PRODUCT_SLICE_02:END -->',re.S)
    new=pat.sub(section,old) if pat.search(old) else old.splitlines()[0]+'\n\n'+section+'\n\n'+'\n'.join(old.splitlines()[1:])+'\n'
    path.write_text(new)
print('PRODUCT_SLICE_02_CANONICAL_UPDATE=VERIFIED')
PY

python3 - <<'PY'
import json
from pathlib import Path
root=Path('/root/tokenoskobi_clean_v1')
r=json.loads((root/'PROJECT_RUNTIME.json').read_text())
a=json.loads((root/'data/control/product_slice_02_single_token_decision_packet_v1.json').read_text())
x=json.loads((root/'data/control/product_slice_02_nginx_route_recovery_v1.json').read_text())
s=json.loads((root/'data/control/product_slice_02_smoke_analysis_v1.json').read_text())
assert r['next_safe_step']=='PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING'
assert a['security']['loopback_only'] is True and a['security']['nginx_external_500_fixed'] is True
assert a['visible_product']['external_http_code']=='200' and a['visible_product']['external_api_http_code']=='200'
assert x['authority_change'] is False
assert all(s['authority'][k] is False for k in ('paper','live','wallet','signing','order','broadcast'))
assert all(v in (0,'DISABLED') for v in a['authority'].values())
print('PRODUCT_SLICE_02_RECOVERY_VALIDATION=VERIFIED')
PY

rm -f \
  tools/tokenoskobi_product_slice_02_single_token_deploy.sh \
  tools/tokenoskobi_product_slice_02_single_token_deploy_fix1.sh \
  tools/tokenoskobi_product_slice_02_external_500_diagnose.sh \
  "$SELF"

git add \
  config/product_slice_02_v1.json \
  config/nginx/panel.coinoskobi.xyz.conf \
  tools/tokenoskobi_product_slice_02_server.py \
  tests/test_product_slice_02.py \
  systemd_drafts/tokenoskobi-product-slice-02.service \
  data/control/product_slice_02_single_token_decision_packet_v1.json \
  data/control/product_slice_02_smoke_analysis_v1.json \
  data/control/product_slice_02_nginx_route_recovery_v1.json \
  03_ROADMAP.md 04_ALMANAC.md 05_ATLAS.md \
  06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json
git add -f reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md reports/LATEST_TK_AI_HANDOFF.md
git add -u -- \
  tools/tokenoskobi_product_slice_02_single_token_deploy.sh \
  tools/tokenoskobi_product_slice_02_single_token_deploy_fix1.sh \
  tools/tokenoskobi_product_slice_02_external_500_diagnose.sh \
  "$SELF"

git diff --cached --check
git commit -m "Product: recover panel route and seal Slice 02"
COMMITTED=1
git push origin main
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]

python3 - <<'PY'
import json
from pathlib import Path
a=json.loads(Path('data/control/product_slice_02_single_token_decision_packet_v1.json').read_text())
print('PRODUCT_SLICE_02=DEPLOYED_VERIFIED_GITHUB_SEALED')
print('EXTERNAL_URL='+a['visible_product']['external_url'])
print('EXTERNAL_HTTP_CODE='+a['visible_product']['external_http_code'])
print('EXTERNAL_API_HTTP_CODE='+a['visible_product']['external_api_http_code'])
print('NGINX_EXTERNAL_500_FIXED=true')
print('PANEL_8096_LOOPBACK_ONLY=true')
print('SINGLE_TOKEN_INPUT=true')
print('REAL_DECISION_PACKET=true')
print('SMOKE_DECISION='+a['smoke']['decision'])
print('SMOKE_DATA_QUALITY='+a['smoke']['data_quality'])
print('PUBLIC_RPC_OK='+str(a['smoke']['public_rpc_ok']))
print('ALCHEMY_HTTP_OK='+str(a['smoke']['alchemy_http_ok']).lower())
print('HYBRID_READY='+str(a['smoke']['hybrid_ready']).lower())
print('NEWS_FRESH='+str(a['smoke']['news_fresh']).lower())
print('PAPER_RUNTIME=DISABLED')
print('LIVE_TRADE=DISABLED')
print('REAL_FINANCIAL_AUTHORITY=0')
print('NEXT_SAFE_STEP='+a['next_safe_step'])
PY
echo REMOTE_VERIFY=VERIFIED
echo WORKTREE=CLEAN
echo HEAD="$(git rev-parse HEAD)"
