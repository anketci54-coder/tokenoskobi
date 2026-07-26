#!/usr/bin/env bash
set -Eeuo pipefail
cd /root/tokenoskobi_clean_v1

ROOT=/root/tokenoskobi_clean_v1
EXPECTED_HEAD=e2c867d4fc14ed67af0ea096563a4f768e51c06e
SERVICE=tokenoskobi-product-slice-02.service
OLD_SERVICE=tokenoskobi-active-panel-8096.service
HELPER=${FIX6_HELPER:-/root/tokenoskobi_fix6_review/tokenoskobi_product_slice_02_fix6_helper.py}
SERVER=tools/tokenoskobi_product_slice_02_server.py
CONFIG=config/product_slice_02_v1.json
TEST=tests/test_product_slice_02.py
UNIT=systemd_drafts/tokenoskobi-product-slice-02.service
NGINX_LINK=/etc/nginx/sites-enabled/panel.coinoskobi.xyz.conf
SMOKE=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c

EXPECTED_SERVER_SHA256=a2bcb0a413a04fbd49244fab987d9b55396f58af76567e7b3f36bec6fd41f024
EXPECTED_CONFIG_SHA256=7d6c2fcc53e476d1f1c8633de2270480a336328649982dce5ac7bf9092bceb6a
EXPECTED_TEST_SHA256=a61ce9ada03de21208fe871e94a0ea86f436e4091c45248d2975fcc6e99bca19
EXPECTED_UNIT_SHA256=68cc97df0c789ed83b7d27fbacd7442616fce979f69dad3a4e7320f9cc373597

BACKUP='' NGINX_SITE='' NGINX_TOUCHED=0

say(){ printf '%s\n' "$@"; }
fail(){ say "BLOCKED=$*" >&2; return 1; }
http_code(){
  curl -sS -o /dev/null -w '%{http_code}' \
    --connect-timeout 5 --max-time 20 "$1" 2>/dev/null || true
}
api_code(){
  curl -sS -o /dev/null -w '%{http_code}' \
    --connect-timeout 5 --max-time 30 \
    -H 'Content-Type: application/json' \
    --data '{"token_address":"'"$SMOKE"'"}' "$1" 2>/dev/null || true
}
rollback(){
  rc=$?
  trap - ERR INT TERM
  set +e
  if ((NGINX_TOUCHED)) && [[ -f "$BACKUP/nginx.before" ]]; then
    cp -a "$BACKUP/nginx.before" "$NGINX_SITE"
    nginx -t >/dev/null 2>&1 && systemctl reload nginx >/dev/null 2>&1
  fi
  say FIX6_RESUME_RESULT=FAILED FIX6_RESUME_FAILED_RC=$rc
  say SERVICE_RESTART=NONE CANONICAL_UPDATE=NONE COMMIT_PUSH=NONE
  exit "$rc"
}
trap rollback ERR INT TERM

[[ "${FIX6_RESUME_CONFIRM:-}" == YES ]] || fail RESUME_CONFIRMATION_MISSING
[[ -f "$HELPER" ]] || fail FIX6_HELPER_MISSING
[[ "$(git branch --show-current)" == main ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail HEAD_NOT_EXACT_E2C867D

python3 "$HELPER" dirty-check "$ROOT"

[[ "$(sha256sum "$SERVER" | awk '{print $1}')" == "$EXPECTED_SERVER_SHA256" ]] || fail SERVER_SHA_MISMATCH
[[ "$(sha256sum "$CONFIG" | awk '{print $1}')" == "$EXPECTED_CONFIG_SHA256" ]] || fail CONFIG_SHA_MISMATCH
[[ "$(sha256sum "$TEST" | awk '{print $1}')" == "$EXPECTED_TEST_SHA256" ]] || fail TEST_SHA_MISMATCH
[[ "$(sha256sum "$UNIT" | awk '{print $1}')" == "$EXPECTED_UNIT_SHA256" ]] || fail UNIT_SHA_MISMATCH

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

BEFORE="$(http_code https://panel.coinoskobi.xyz/panel/panel_v2/)"
[[ "$BEFORE" == 500 ]] || fail EXTERNAL_PANEL_NOT_EXPECTED_500

NGINX_SITE="$(readlink -f "$NGINX_LINK" 2>/dev/null || true)"
[[ -n "$NGINX_SITE" && -f "$NGINX_SITE" ]] || fail NGINX_SITE_MISSING
grep -q 'server_name panel.coinoskobi.xyz' "$NGINX_SITE" || fail NGINX_SERVER_NAME_MISMATCH
nginx -t >/dev/null 2>&1 || fail NGINX_BASELINE_INVALID

AUTH_FILE="${FIX6_AUTH_FILE:-}"
[[ -n "$AUTH_FILE" ]] || AUTH_FILE="$(python3 "$HELPER" discover-auth)"
[[ "$AUTH_FILE" =~ ^/[A-Za-z0-9._/-]+$ && -f "$AUTH_FILE" ]] || fail AUTH_FILE_INVALID

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/tokenoskobi_product_slice_02_fix6_resume_${STAMP}"
mkdir -p "$BACKUP"
cp -a "$NGINX_SITE" "$BACKUP/nginx.before"
find /etc/nginx -type f ! -path "$NGINX_SITE" -print0 2>/dev/null |
  sort -z | xargs -0 -r sha256sum >"$BACKUP/nginx_other.before"

NGINX_TOUCHED=1
python3 "$HELPER" patch-nginx "$NGINX_SITE" "$AUTH_FILE"
nginx -t
systemctl reload nginx

PANEL='' API='' ROOT_CODE='' HEALTH=''
for _ in {1..60}; do
  PANEL="$(http_code https://panel.coinoskobi.xyz/panel/panel_v2/)"
  API="$(api_code https://panel.coinoskobi.xyz/api/v1/analyze)"
  ROOT_CODE="$(http_code https://panel.coinoskobi.xyz/)"
  HEALTH="$(http_code https://panel.coinoskobi.xyz/healthz)"
  if [[ "$PANEL" == 401 && "$API" == 401 && "$ROOT_CODE" == 401 && "$HEALTH" == 200 ]]; then
    break
  fi
  sleep .5
done

[[ "$PANEL" == 401 ]] || fail EXTERNAL_PANEL_AUTH_GATE_$PANEL
[[ "$API" == 401 ]] || fail EXTERNAL_API_AUTH_GATE_$API
[[ "$ROOT_CODE" == 401 ]] || fail EXTERNAL_ROOT_AUTH_GATE_$ROOT_CODE
[[ "$HEALTH" == 200 ]] || fail EXTERNAL_HEALTH_$HEALTH

install -d -m 0755 config/nginx
cp -a "$NGINX_SITE" config/nginx/panel.coinoskobi.xyz.conf

find /etc/nginx -type f ! -path "$NGINX_SITE" -print0 2>/dev/null |
  sort -z | xargs -0 -r sha256sum >"$BACKUP/nginx_other.after"
cmp -s "$BACKUP/nginx_other.before" "$BACKUP/nginx_other.after" || fail OTHER_NGINX_CHANGED

python3 "$HELPER" dirty-check "$ROOT"

NGINX_TOUCHED=0
trap - ERR INT TERM

say FIX6_RESUME_RESULT=NGINX_RECOVERED_PENDING_PHONE_ACCEPTANCE_AND_SEPARATE_SEAL
say LOCAL_HEAD=$EXPECTED_HEAD MAIN_PID=$PID PORT_8096=LOOPBACK_ONLY
say EXTERNAL_PANEL_UNAUTH_HTTP=$PANEL EXTERNAL_API_UNAUTH_HTTP=$API
say EXTERNAL_ROOT_UNAUTH_HTTP=$ROOT_CODE EXTERNAL_HEALTH_HTTP=$HEALTH
say PAPER_TRADE=DISABLED LIVE_TRADE=DISABLED WALLET_SIGNING_ORDER_AUTHORITY=0
say SERVICE_RESTART=NONE CANONICAL_UPDATE=NONE COMMIT_PUSH=NONE
say BACKUP_DIR=$BACKUP
say NEXT_SAFE_STEP=PHONE_AUTHENTICATED_PANEL_ACCEPTANCE_THEN_SEPARATE_SEAL
