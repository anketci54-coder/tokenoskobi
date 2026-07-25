#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TMP="/tmp/tokenoskobi_slice02_ext500_${STAMP}"
mkdir -p "$TMP"

printf 'PRODUCT_SLICE_02_EXTERNAL_500_DIAGNOSIS=STARTED\n'
printf 'TIMESTAMP_UTC=%s\n' "$STAMP"
printf 'HEAD=%s\n' "$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main 2>/dev/null || echo UNKNOWN)"
printf 'BRANCH=%s\n' "$(git branch --show-current 2>/dev/null || echo UNKNOWN)"
printf '%s\n' '--- GIT_STATUS_BEGIN ---'
git status --porcelain=v1 || true
printf '%s\n' '--- GIT_STATUS_END ---'

for svc in tokenoskobi-product-slice-02.service tokenoskobi-active-panel-8096.service nginx.service; do
  active="$(systemctl is-active "$svc" 2>/dev/null || true)"
  enabled="$(systemctl is-enabled "$svc" 2>/dev/null || true)"
  printf 'SERVICE=%s ACTIVE=%s ENABLED=%s\n' "$svc" "$active" "$enabled"
done

printf '%s\n' '--- LISTEN_8096_BEGIN ---'
ss -ltnp 'sport = :8096' || true
printf '%s\n' '--- LISTEN_8096_END ---'

probe() {
  local name="$1"
  local url="$2"
  shift 2
  local code
  code="$(curl -k -sS --max-time 20 -D "$TMP/${name}.headers" -o "$TMP/${name}.body" -w '%{http_code}' "$@" "$url" 2>"$TMP/${name}.err" || true)"
  printf 'PROBE=%s CODE=%s BYTES=%s\n' "$name" "$code" "$(wc -c < "$TMP/${name}.body" 2>/dev/null || echo 0)"
  if [[ -s "$TMP/${name}.err" ]]; then
    printf 'PROBE_ERROR_%s=%s\n' "$name" "$(tr '\n' ' ' < "$TMP/${name}.err" | cut -c1-500)"
  fi
  printf '%s\n' "--- ${name}_HEADERS_BEGIN ---"
  sed -n '1,40p' "$TMP/${name}.headers" 2>/dev/null || true
  printf '%s\n' "--- ${name}_HEADERS_END ---"
  printf '%s\n' "--- ${name}_BODY_BEGIN ---"
  head -c 600 "$TMP/${name}.body" 2>/dev/null || true
  printf '\n%s\n' "--- ${name}_BODY_END ---"
}

probe LOCAL_HEALTH http://127.0.0.1:8096/healthz
probe LOCAL_PANEL http://127.0.0.1:8096/panel/panel_v2/
probe PUBLIC_PANEL https://panel.coinoskobi.xyz/panel/panel_v2/
probe DIRECT_LOCAL_TLS https://panel.coinoskobi.xyz/panel/panel_v2/ --resolve panel.coinoskobi.xyz:443:127.0.0.1

printf '%s\n' '--- NGINX_TEST_BEGIN ---'
nginx -t 2>&1 || true
printf '%s\n' '--- NGINX_TEST_END ---'

nginx -T >"$TMP/nginx_T.txt" 2>"$TMP/nginx_T.err" || true
printf '%s\n' '--- PANEL_NGINX_FILES_BEGIN ---'
grep -RIl --include='*.conf' --include='*panel*' 'server_name[[:space:]].*panel\.coinoskobi\.xyz' /etc/nginx/sites-enabled /etc/nginx/sites-available /etc/nginx/conf.d 2>/dev/null | sort -u || true
printf '%s\n' '--- PANEL_NGINX_FILES_END ---'

python3 - "$TMP/nginx_T.txt" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1])
text=p.read_text(errors='replace') if p.exists() else ''
print('--- NGINX_RELEVANT_LINES_BEGIN ---')
current='UNKNOWN'
for raw in text.splitlines():
    m=re.match(r'# configuration file (.*):$',raw)
    if m:
        current=m.group(1)
        continue
    line=raw.strip()
    if any(k in line for k in (
        'panel.coinoskobi.xyz','location = /panel/panel_v2/','location ^~ /panel/panel_v2/',
        'location /panel/panel_v2/','location = /api/v1/analyze','location /api/v1/',
        'proxy_pass','try_files','alias ','auth_basic','auth_basic_user_file','listen 443'
    )):
        safe=re.sub(r'(?i)(authorization\s+)(.+)',r'\1[REDACTED]',line)
        print(f'{current}: {safe}')
print('--- NGINX_RELEVANT_LINES_END ---')
PY

printf '%s\n' '--- STATIC_PATH_STATE_BEGIN ---'
for p in /var/www/tokenoskobi_public /var/www/tokenoskobi_public/panel /var/www/tokenoskobi_public/panel/panel_v2 /var/www/tokenoskobi_public/panel/panel_v2/index.html /root/tokenoskobi_clean_v1/active_panel_8096/current/panel/panel_v2/index.html; do
  if [[ -e "$p" ]]; then
    stat -c 'PATH=%n TYPE=%F MODE=%a OWNER=%U GROUP=%G SIZE=%s' "$p" 2>/dev/null || true
  else
    printf 'PATH=%s STATE=MISSING\n' "$p"
  fi
done
printf '%s\n' '--- STATIC_PATH_STATE_END ---'

printf '%s\n' '--- AUTH_FILE_STATE_BEGIN ---'
python3 - "$TMP/nginx_T.txt" <<'PY'
from pathlib import Path
import os,re,stat,sys
text=Path(sys.argv[1]).read_text(errors='replace') if Path(sys.argv[1]).exists() else ''
paths=[]
for m in re.finditer(r'auth_basic_user_file\s+([^;]+);',text):
    p=m.group(1).strip().strip('"\'')
    if '$' not in p and p not in paths: paths.append(p)
if not paths:
    print('AUTH_FILE=NONE_DECLARED')
for p in paths:
    try:
        s=os.stat(p)
        print(f'AUTH_FILE={p} EXISTS=true MODE={stat.S_IMODE(s.st_mode):04o} OWNER_UID={s.st_uid} GROUP_GID={s.st_gid} SIZE={s.st_size}')
    except FileNotFoundError:
        print(f'AUTH_FILE={p} EXISTS=false')
    except Exception as e:
        print(f'AUTH_FILE={p} ERROR={type(e).__name__}')
PY
printf '%s\n' '--- AUTH_FILE_STATE_END ---'

ERROR_LOG=/var/log/nginx/error.log
before=0
if [[ -f "$ERROR_LOG" ]]; then before="$(wc -l < "$ERROR_LOG")"; fi
curl -k -sS --max-time 12 --resolve panel.coinoskobi.xyz:443:127.0.0.1 -o /dev/null https://panel.coinoskobi.xyz/panel/panel_v2/ || true
sleep 1
if [[ -f "$ERROR_LOG" ]]; then
  after="$(wc -l < "$ERROR_LOG")"
  start=$((before + 1))
  printf '%s\n' '--- NGINX_NEW_ERROR_LINES_BEGIN ---'
  if (( after >= start )); then sed -n "${start},${after}p" "$ERROR_LOG" | tail -n 80; fi
  printf '%s\n' '--- NGINX_NEW_ERROR_LINES_END ---'
  sed -n "${start},${after}p" "$ERROR_LOG" > "$TMP/new_errors.txt" || true
else
  : > "$TMP/new_errors.txt"
fi

printf '%s\n' '--- PRODUCT_SERVICE_LOG_BEGIN ---'
journalctl -u tokenoskobi-product-slice-02.service -n 80 --no-pager 2>/dev/null || true
printf '%s\n' '--- PRODUCT_SERVICE_LOG_END ---'

python3 - "$TMP/new_errors.txt" "$TMP/PUBLIC_PANEL.body" "$TMP/DIRECT_LOCAL_TLS.body" <<'PY'
from pathlib import Path
import sys
blob='\n'.join(Path(x).read_text(errors='replace') if Path(x).exists() else '' for x in sys.argv[1:]).lower()
labels=[]
checks=[
 ('NGINX_INTERNAL_REDIRECT_CYCLE','rewrite or internal redirection cycle'),
 ('NGINX_AUTH_FILE_FAILURE','auth_basic_user_file'),
 ('NGINX_PASSWORD_FILE_FAILURE','password file'),
 ('NGINX_PERMISSION_FAILURE','permission denied'),
 ('NGINX_UPSTREAM_REFUSED','connect() failed'),
 ('NGINX_UPSTREAM_PREMATURE_CLOSE','upstream prematurely closed'),
 ('NGINX_NO_LIVE_UPSTREAM','no live upstreams'),
 ('NGINX_FILE_NOT_FOUND','no such file or directory'),
]
for label,needle in checks:
    if needle in blob: labels.append(label)
if not labels: labels=['UNCLASSIFIED_FROM_AVAILABLE_LOGS']
print('DIAGNOSIS='+'|'.join(labels))
PY

printf 'PRODUCT_SLICE_02_EXTERNAL_500_DIAGNOSIS=COMPLETED_READ_ONLY\n'
printf 'REPO_MUTATION=NONE\n'
printf 'SERVICE_MUTATION=NONE\n'
printf 'AUTHORITY_CHANGE=NONE\n'
printf 'OUTPUT_DIR=%s\n' "$TMP"
