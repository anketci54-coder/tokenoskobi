#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

ROOT=/root/tokenoskobi_clean_v1
SELF=tools/tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix4.sh
SOURCE=tools/tokenoskobi_product_slice_02_single_token_deploy.sh
TEMP=/tmp/tokenoskobi_product_slice_02_fix4_inner.sh
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/root/tokenoskobi_product_slice_02_fix4_${STAMP}"
BASE_HEAD="$(git rev-parse HEAD)"
NGINX_LINK=/etc/nginx/sites-enabled/panel.coinoskobi.xyz.conf
NGINX_SITE="$(readlink -f "$NGINX_LINK" 2>/dev/null || true)"
SERVICE=tokenoskobi-product-slice-02.service
OLD_SERVICE=tokenoskobi-active-panel-8096.service

KNOWN_PATHS=(
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
  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix2.sh
  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix3.sh
  tools/tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix4.sh
)

mkdir -p "$BACKUP_DIR"

git fetch origin main --quiet
[[ "$(git branch --show-current)" == main ]]
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -n "$NGINX_SITE" && -f "$NGINX_SITE" ]]
grep -q 'server_name panel.coinoskobi.xyz' "$NGINX_SITE"

python3 - <<'PY'
import subprocess
allowed={
 'config/product_slice_02_v1.json',
 'config/nginx/panel.coinoskobi.xyz.conf',
 'tools/tokenoskobi_product_slice_02_server.py',
 'tests/test_product_slice_02.py',
 'systemd_drafts/tokenoskobi-product-slice-02.service',
 'data/control/product_slice_02_single_token_decision_packet_v1.json',
 'data/control/product_slice_02_smoke_analysis_v1.json',
 'data/control/product_slice_02_nginx_route_recovery_v1.json',
 'reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md',
 'reports/LATEST_TK_AI_HANDOFF.md',
 '03_ROADMAP.md','04_ALMANAC.md','05_ATLAS.md','06_PROJECT_MASTER_STATE.md','07_PROJECT_HANDOFF.md',
 'PROJECT_RUNTIME.json','PROJECT_HISTORY.json',
 'data/tokenoskobi_v1_v8_master_era_roadmap.json','data/control/latest_tk_machine_state.json',
 'tools/tokenoskobi_product_slice_02_single_token_deploy.sh',
 'tools/tokenoskobi_product_slice_02_single_token_deploy_fix1.sh',
 'tools/tokenoskobi_product_slice_02_external_500_diagnose.sh',
 'tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh',
 'tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix2.sh',
 'tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix3.sh',
 'tools/tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix4.sh',
}
rows=subprocess.check_output(['git','status','--porcelain=v1'],text=True).splitlines()
seen=set()
for row in rows:
    path=row[3:]
    if ' -> ' in path:path=path.split(' -> ',1)[1]
    seen.add(path)
unexpected=sorted(seen-allowed)
if unexpected:raise SystemExit('BLOCKED=UNEXPECTED_DIRTY_PATHS:'+','.join(unexpected))
print('FIX4_DIRTY_STATE_SCOPE=VERIFIED')
PY

existing=()
for p in "${KNOWN_PATHS[@]}"; do [[ -e "$p" ]] && existing+=("$p"); done
if [[ ${#existing[@]} -gt 0 ]]; then
  tar -czf "$BACKUP_DIR/repo_pre_fix4.tar.gz" -C "$ROOT" "${existing[@]}"
else
  tar -czf "$BACKUP_DIR/repo_pre_fix4.tar.gz" --files-from /dev/null
fi
cp -a "$NGINX_SITE" "$BACKUP_DIR/nginx_site.conf"
[[ -f "/etc/systemd/system/$SERVICE" ]] && cp -a "/etc/systemd/system/$SERVICE" "$BACKUP_DIR/product_service.unit" || true
NEW_WAS_ACTIVE=0; NEW_WAS_ENABLED=0; OLD_WAS_ACTIVE=0; OLD_WAS_ENABLED=0
systemctl is-active --quiet "$SERVICE" 2>/dev/null && NEW_WAS_ACTIVE=1 || true
systemctl is-enabled --quiet "$SERVICE" 2>/dev/null && NEW_WAS_ENABLED=1 || true
systemctl is-active --quiet "$OLD_SERVICE" 2>/dev/null && OLD_WAS_ACTIVE=1 || true
systemctl is-enabled --quiet "$OLD_SERVICE" 2>/dev/null && OLD_WAS_ENABLED=1 || true
find /etc/nginx -type f \( -iname '*tokenoskobi.com*' -o -iname '*coinoskobi.com*' \) -print0 2>/dev/null | sort -z | xargs -0 -r sha256sum > "$BACKUP_DIR/main_website_nginx.before"
echo BACKUP="$BACKUP_DIR"
echo TOKENOSKOBI_COM_POLICY=PRIVATE_NOT_PUBLIC_UNTIL_EXPLICIT_USER_APPROVAL

restore_pre_fix4() {
  set +e
  git fetch origin main --quiet
  remote_now="$(git rev-parse origin/main 2>/dev/null)"
  if [[ "$remote_now" != "$BASE_HEAD" ]]; then
    echo BLOCKED=REMOTE_ADVANCED_DURING_FAILED_FIX4
    echo ORIGIN_MAIN="$remote_now"
    return 1
  fi
  cp -a "$BACKUP_DIR/nginx_site.conf" "$NGINX_SITE"
  nginx -t >/dev/null 2>&1 && systemctl reload nginx >/dev/null 2>&1
  for p in "${KNOWN_PATHS[@]}"; do rm -rf -- "$ROOT/$p"; done
  git reset --hard "$BASE_HEAD" >/dev/null 2>&1
  tar -xzf "$BACKUP_DIR/repo_pre_fix4.tar.gz" -C "$ROOT"
  git reset --quiet >/dev/null 2>&1
  if [[ -f "$BACKUP_DIR/product_service.unit" ]]; then cp -a "$BACKUP_DIR/product_service.unit" "/etc/systemd/system/$SERVICE"; fi
  systemctl daemon-reload >/dev/null 2>&1
  if [[ "$NEW_WAS_ENABLED" -eq 1 ]]; then systemctl enable "$SERVICE" >/dev/null 2>&1; else systemctl disable "$SERVICE" >/dev/null 2>&1; fi
  if [[ "$NEW_WAS_ACTIVE" -eq 1 ]]; then systemctl restart "$SERVICE" >/dev/null 2>&1; else systemctl stop "$SERVICE" >/dev/null 2>&1; fi
  if [[ "$OLD_WAS_ENABLED" -eq 1 ]]; then systemctl enable "$OLD_SERVICE" >/dev/null 2>&1; else systemctl disable "$OLD_SERVICE" >/dev/null 2>&1; fi
  if [[ "$OLD_WAS_ACTIVE" -eq 1 ]]; then systemctl start "$OLD_SERVICE" >/dev/null 2>&1; else systemctl stop "$OLD_SERVICE" >/dev/null 2>&1; fi
  echo ROLLBACK=RESTORED_EXACT_PRE_FIX4_STATE
}

tracked=()
for p in "${KNOWN_PATHS[@]}"; do git ls-files --error-unmatch "$p" >/dev/null 2>&1 && tracked+=("$p"); done
[[ ${#tracked[@]} -gt 0 ]] && git restore --source=origin/main --staged --worktree -- "${tracked[@]}"
for p in \
  config/product_slice_02_v1.json \
  config/nginx/panel.coinoskobi.xyz.conf \
  tools/tokenoskobi_product_slice_02_server.py \
  data/control/product_slice_02_single_token_decision_packet_v1.json \
  data/control/product_slice_02_smoke_analysis_v1.json \
  data/control/product_slice_02_nginx_route_recovery_v1.json \
  reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md; do
  git ls-files --error-unmatch "$p" >/dev/null 2>&1 || rm -rf -- "$p"
done
[[ -z "$(git status --porcelain=v1)" ]]
[[ -f "$SOURCE" ]]
echo FIX4_REPOSITORY_BASELINE=CLEAN_ORIGIN_MAIN

python3 - <<'PY'
from pathlib import Path
source=Path('/root/tokenoskobi_clean_v1/tools/tokenoskobi_product_slice_02_single_token_deploy.sh')
target=Path('/tmp/tokenoskobi_product_slice_02_fix4_inner.sh')
text=source.read_text(encoding='utf-8')

def rep(old,new,label,count=1):
    n=text.count(old)
    if n < count:
        raise SystemExit(f'BLOCKED={label}_COUNT:{n}')
    return text.replace(old,new,count)

text=rep(
 'RUNNER="tools/tokenoskobi_product_slice_02_single_token_deploy.sh"',
 'RUNNER="tools/tokenoskobi_product_slice_02_rebuild_recover_and_seal_fix4.sh"',
 'FIX4_RUNNER_PATCH',
)
text=rep(
 '  config/product_slice_02_v1.json\n',
 '  config/product_slice_02_v1.json\n  config/nginx/panel.coinoskobi.xyz.conf\n  data/control/product_slice_02_nginx_route_recovery_v1.json\n',
 'FIX4_FILES_PATCH',
)
text=rep('trap rollback ERR','trap - ERR\n# Full rollback is owned by the outer fix4 runner.','FIX4_TRAP_PATCH')

anchor='''! echo "$LISTEN" | grep -Eq '0\\.0\\.0\\.0:8096|\\[::\\]:8096'

SMOKE=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c
'''
insert='''! echo "$LISTEN" | grep -Eq '0\\.0\\.0\\.0:8096|\\[::\\]:8096'

NGINX_LINK=/etc/nginx/sites-enabled/panel.coinoskobi.xyz.conf
NGINX_SITE="$(readlink -f "$NGINX_LINK" 2>/dev/null || true)"
[[ -n "$NGINX_SITE" && -f "$NGINX_SITE" ]]
grep -q 'server_name panel.coinoskobi.xyz' "$NGINX_SITE"
mkdir -p config/nginx
cp -a "$NGINX_SITE" config/nginx/panel.coinoskobi.xyz.conf
python3 - "$NGINX_SITE" config/nginx/panel.coinoskobi.xyz.conf <<'PYNGINX'
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
        line_start=text.rfind('\\n',0,start)+1
        line_end=text.find('\\n',end)
        line_end=len(text) if line_end<0 else line_end+1
        indent=text[line_start:start]
        text=text[:line_start]+indent+'# TOKENOSKOBI_PRODUCT_SLICE_02_ROUTE_USES_ROOT_REVERSE_PROXY\\n'+text[line_end:]
        count+=1
    return text,count
for raw in sys.argv[1:]:
    p=Path(raw);body=p.read_text(encoding='utf-8');total=0
    for header in headers:
        body,n=remove_blocks(body,header);total+=n
    if total<2:raise SystemExit(f'BLOCKED=EXPECTED_BROKEN_PANEL_LOCATIONS_NOT_FOUND:{p}:{total}')
    if any(h in body for h in headers):raise SystemExit(f'BLOCKED=BROKEN_PANEL_LOCATION_REMAINS:{p}')
    if 'proxy_pass http://127.0.0.1:8096/;' not in body:raise SystemExit(f'BLOCKED=ROOT_REVERSE_PROXY_MISSING:{p}')
    p.write_text(body,encoding='utf-8')
    print(f'NGINX_PANEL_STATIC_SHADOW_ROUTES_REMOVED={p}:{total}')
PYNGINX
nginx -t
systemctl reload nginx
sleep 2

SMOKE=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c
'''
text=rep(anchor,insert,'FIX4_NGINX_INSERT')

old='''EXT="$(curl -k -sS --max-time 12 -o /tmp/s02_ext.html -w '%{http_code}' https://panel.coinoskobi.xyz/panel/panel_v2/ || true)"
case "$EXT" in 200|401|403);;*) echo "BLOCKED=EXTERNAL_HTTP_$EXT";exit 1;;esac
'''
new='''EXT="$(curl -k -sS --max-time 20 -o /tmp/s02_ext.html -w '%{http_code}' https://panel.coinoskobi.xyz/panel/panel_v2/ || true)"
[[ "$EXT" == 200 ]] || { echo "BLOCKED=EXTERNAL_PANEL_HTTP_$EXT"; exit 1; }
grep -q 'Tek Token Karar Paketi' /tmp/s02_ext.html
EXT_API="$(curl -k -sS --max-time 120 -o /tmp/s02_ext_api.json -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"'"$SMOKE"'"}' https://panel.coinoskobi.xyz/api/v1/analyze || true)"
[[ "$EXT_API" == 200 ]] || { echo "BLOCKED=EXTERNAL_API_HTTP_$EXT_API"; exit 1; }
'''
text=rep(old,new,'FIX4_EXTERNAL_GATE')
text=rep('python3 - "$EXT" "$LISTEN" <<\'PY\'','python3 - "$EXT" "$EXT_API" "$LISTEN" "$NGINX_SITE" <<\'PY\'','FIX4_CANONICAL_ARGS')
text=rep(
 "root=Path('/root/tokenoskobi_clean_v1');ext,listen=sys.argv[1:3];now=datetime.now(timezone.utc).isoformat();sm=json.loads((root/'data/control/product_slice_02_smoke_analysis_v1.json').read_text());p=sm['provider'];d=sm['decision'];n=sm['news'];remaining=[]",
 "root=Path('/root/tokenoskobi_clean_v1');ext,ext_api,listen,nginx_site=sys.argv[1:5];now=datetime.now(timezone.utc).isoformat();sm=json.loads((root/'data/control/product_slice_02_smoke_analysis_v1.json').read_text());p=sm['provider'];d=sm['decision'];n=sm['news'];remaining=[]",
 'FIX4_CANONICAL_PARSE',
)
text=rep(
 "a={'schema':'tokenoskobi.product_slice_02.deployment.v1'",
 "recovery={'schema':'tokenoskobi.product_slice_02.nginx_route_recovery.v1','generated_at_utc':now,'diagnosed_cause':'STATIC_ALIAS_TRY_FILES_CONCATENATED_INDEX_TO_FILE','observed_error_path':'/var/www/tokenoskobi_public/panel/panel_v2/index.htmlindex.html','repair':'REMOVED_STATIC_PANEL_INDEX_AND_PREFIX_SHADOW_LOCATIONS','active_route':'ROOT_REVERSE_PROXY_TO_127_0_0_1_8096','nginx_site':nginx_site,'nginx_syntax':True,'external_panel_http_code':ext,'external_api_http_code':ext_api,'authority_change':False};(root/'data/control/product_slice_02_nginx_route_recovery_v1.json').write_text(json.dumps(recovery,ensure_ascii=False,indent=2,sort_keys=True)+'\\n');a={'schema':'tokenoskobi.product_slice_02.deployment.v1'",
 'FIX4_RECOVERY_ARTIFACT',
)
text=rep("'external_http_code':ext,'single_token_input'","'external_http_code':ext,'external_api_http_code':ext_api,'single_token_input'",'FIX4_API_CODE')
text=rep("'external_8096_binding_fixed':True,'remaining_blockers'","'external_8096_binding_fixed':True,'nginx_external_500_fixed':True,'remaining_blockers'",'FIX4_SECURITY_FLAG')
text=rep(
 "'next_safe_step':'PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING'}",
 "'next_safe_step':'PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING','exposure_policy':{'tokenoskobi.com':'PRIVATE_NOT_PUBLIC_UNTIL_EXPLICIT_USER_APPROVAL','main_website_mutation':False,'staging_panel_domain':'panel.coinoskobi.xyz','staging_panel_scope':'CONTROLLED_TEST_PANEL_ONLY'}}",
 'FIX4_EXPOSURE_POLICY',
)
text=rep(
 "f\"- NEWS fresh: `{n['fresh']}`\\n- Authority: `DISABLED / 0`\\n- Next: `{a['next_safe_step']}`\\n\"",
 "f\"- NEWS fresh: `{n['fresh']}`\\n- Tokenoskobi.com: `PRIVATE_NOT_PUBLIC`\\n- Main website mutation: `NONE`\\n- Authority: `DISABLED / 0`\\n- Next: `{a['next_safe_step']}`\\n\"",
 'FIX4_REPORT_POLICY',
)
text=rep(
 "- NEWS fresh: `{n['fresh']}`\n- Authority: `PAPER_DISABLED; LIVE_DISABLED; REAL_FINANCIAL_AUTHORITY_0`",
 "- NEWS fresh: `{n['fresh']}`\n- Tokenoskobi.com: `PRIVATE_NOT_PUBLIC`\n- Main website mutation: `NONE`\n- Authority: `PAPER_DISABLED; LIVE_DISABLED; REAL_FINANCIAL_AUTHORITY_0`",
 'FIX4_CANONICAL_POLICY',
)
text=rep(
 "r=json.loads(Path('PROJECT_RUNTIME.json').read_text());a=json.loads(Path('data/control/product_slice_02_single_token_decision_packet_v1.json').read_text());s=json.loads(Path('data/control/product_slice_02_smoke_analysis_v1.json').read_text())",
 "r=json.loads(Path('PROJECT_RUNTIME.json').read_text());a=json.loads(Path('data/control/product_slice_02_single_token_decision_packet_v1.json').read_text());x=json.loads(Path('data/control/product_slice_02_nginx_route_recovery_v1.json').read_text());s=json.loads(Path('data/control/product_slice_02_smoke_analysis_v1.json').read_text())",
 'FIX4_VALIDATION_LOAD',
)
text=rep(
 "assert a['security']['loopback_only'] is True",
 "assert a['security']['loopback_only'] is True and a['security']['nginx_external_500_fixed'] is True\nassert a['visible_product']['external_http_code']=='200' and a['visible_product']['external_api_http_code']=='200'\nassert a['exposure_policy']['tokenoskobi.com']=='PRIVATE_NOT_PUBLIC_UNTIL_EXPLICIT_USER_APPROVAL'\nassert a['exposure_policy']['main_website_mutation'] is False\nassert x['authority_change'] is False",
 'FIX4_VALIDATION_POLICY',
)

old='''rm -f tools/.tokenoskobi_product_slice_02_deploy_payload.zlib "$RUNNER"
git add config/product_slice_02_v1.json tools/tokenoskobi_product_slice_02_server.py tests/test_product_slice_02.py systemd_drafts/tokenoskobi-product-slice-02.service data/control/product_slice_02_single_token_decision_packet_v1.json data/control/product_slice_02_smoke_analysis_v1.json 03_ROADMAP.md 04_ALMANAC.md 05_ATLAS.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md PROJECT_RUNTIME.json PROJECT_HISTORY.json data/tokenoskobi_v1_v8_master_era_roadmap.json data/control/latest_tk_machine_state.json
git add -f reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md reports/LATEST_TK_AI_HANDOFF.md
git add -A tools/.tokenoskobi_product_slice_02_deploy_payload.zlib "$RUNNER"
'''
new='''rm -f \\
  tools/.tokenoskobi_product_slice_02_deploy_payload.zlib \\
  tools/tokenoskobi_product_slice_02_single_token_deploy.sh \\
  tools/tokenoskobi_product_slice_02_single_token_deploy_fix1.sh \\
  tools/tokenoskobi_product_slice_02_external_500_diagnose.sh \\
  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh \\
  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix2.sh \\
  tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix3.sh \\
  "$RUNNER"
git add config/product_slice_02_v1.json config/nginx/panel.coinoskobi.xyz.conf tools/tokenoskobi_product_slice_02_server.py tests/test_product_slice_02.py systemd_drafts/tokenoskobi-product-slice-02.service data/control/product_slice_02_single_token_decision_packet_v1.json data/control/product_slice_02_smoke_analysis_v1.json data/control/product_slice_02_nginx_route_recovery_v1.json 03_ROADMAP.md 04_ALMANAC.md 05_ATLAS.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md PROJECT_RUNTIME.json PROJECT_HISTORY.json data/tokenoskobi_v1_v8_master_era_roadmap.json data/control/latest_tk_machine_state.json
git add -f reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md reports/LATEST_TK_AI_HANDOFF.md
git add -u -- tools/tokenoskobi_product_slice_02_single_token_deploy.sh tools/tokenoskobi_product_slice_02_single_token_deploy_fix1.sh tools/tokenoskobi_product_slice_02_external_500_diagnose.sh tools/tokenoskobi_product_slice_02_external_500_recover_and_seal.sh tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix2.sh tools/tokenoskobi_product_slice_02_external_500_recover_and_seal_fix3.sh "$RUNNER"
if git ls-files --error-unmatch tools/.tokenoskobi_product_slice_02_deploy_payload.zlib >/dev/null 2>&1; then git add -u -- tools/.tokenoskobi_product_slice_02_deploy_payload.zlib; fi
'''
text=rep(old,new,'FIX4_CLEANUP_STAGE')
text=rep(
 "print('EXTERNAL_HTTP_CODE='+a['visible_product']['external_http_code'])",
 "print('EXTERNAL_HTTP_CODE='+a['visible_product']['external_http_code'])\nprint('EXTERNAL_API_HTTP_CODE='+a['visible_product']['external_api_http_code'])\nprint('NGINX_EXTERNAL_500_FIXED=true')",
 'FIX4_FINAL_HTTP',
)
text=rep(
 "print('REAL_FINANCIAL_AUTHORITY=0')\nprint('NEXT_SAFE_STEP='+a['next_safe_step'])",
 "print('REAL_FINANCIAL_AUTHORITY=0')\nprint('TOKENOSKOBI_COM=PRIVATE_NOT_PUBLIC')\nprint('MAIN_WEBSITE_MUTATION=NONE')\nprint('NEXT_SAFE_STEP='+a['next_safe_step'])",
 'FIX4_FINAL_POLICY',
)

target.write_text(text,encoding='utf-8')
target.chmod(0o700)
print('PRODUCT_SLICE_02_FIX4_INNER=PREPARED')
PY

bash -n "$TEMP"
if ! bash "$TEMP"; then
  restore_pre_fix4
  exit 1
fi
rm -f "$TEMP"

find /etc/nginx -type f \( -iname '*tokenoskobi.com*' -o -iname '*coinoskobi.com*' \) -print0 2>/dev/null | sort -z | xargs -0 -r sha256sum > "$BACKUP_DIR/main_website_nginx.after"
cmp -s "$BACKUP_DIR/main_website_nginx.before" "$BACKUP_DIR/main_website_nginx.after"
echo TOKENOSKOBI_COM=PRIVATE_NOT_PUBLIC
echo MAIN_WEBSITE_NGINX_MUTATION=NONE
echo STAGING_PANEL_SCOPE=ONLY_PANEL_COINOSKOBI_XYZ
