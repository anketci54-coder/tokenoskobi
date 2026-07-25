#!/usr/bin/env bash
set -Eeuo pipefail
SELF_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd /root/tokenoskobi_clean_v1

ROOT=/root/tokenoskobi_clean_v1
EXPECTED_HEAD=e2c867d4fc14ed67af0ea096563a4f768e51c06e
EXPECTED_DEPLOY_SHA256=7e3087b672d897b58b08146f9017a9931585beccec0a668880e154c20ef7ce5b
SERVICE=tokenoskobi-product-slice-02.service
OLD_SERVICE=tokenoskobi-active-panel-8096.service
DEPLOY=tools/tokenoskobi_product_slice_02_single_token_deploy.sh
HELPER="$SELF_DIR/tokenoskobi_product_slice_02_fix6_helper.py"
SERVER=tools/tokenoskobi_product_slice_02_server.py
CONFIG=config/product_slice_02_v1.json
TEST=tests/test_product_slice_02.py
UNIT=systemd_drafts/tokenoskobi-product-slice-02.service
NGINX_LINK=/etc/nginx/sites-enabled/panel.coinoskobi.xyz.conf
SMOKE=0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c
MODE=${1:---audit}
BACKUP='' NGINX_SITE='' OLD_PID='' NEW_PID='' SHADOW_PID='' SERVICE_TOUCHED=0 NGINX_TOUCHED=0

say(){ printf '%s\n' "$@"; }
fail(){ say "BLOCKED=$*" >&2; return 1; }
code(){ curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 20 "$1" 2>/dev/null || true; }
extcode(){ code https://panel.coinoskobi.xyz/panel/panel_v2/; }
stop_shadow(){ [[ -n "$SHADOW_PID" ]] && kill "$SHADOW_PID" 2>/dev/null || true; SHADOW_PID=''; }
rollback(){ rc=$?; trap - ERR INT TERM; set +e; stop_shadow; if ((NGINX_TOUCHED)); then cp -a "$BACKUP/nginx.before" "$NGINX_SITE"; nginx -t >/dev/null 2>&1 && systemctl reload nginx; fi; if ((SERVICE_TOUCHED)); then cp -a "$BACKUP/unit.before" "/etc/systemd/system/$SERVICE"; systemctl daemon-reload; systemctl restart "$SERVICE" || true; fi; say FIX6_RESULT=FAILED FIX6_FAILED_RC=$rc RECONSTRUCTED_SOURCE_RETAINED=true COMMIT_PUSH=NONE; exit "$rc"; }
trap rollback ERR INT TERM

port_gate(){ lines="$(ss -ltnp 2>/dev/null|awk '$4~/:8096$/{print}')"; [[ -n "$lines" ]]||fail PORT_8096_NOT_LISTENING; grep -q '127.0.0.1:8096'<<<"$lines"||fail PORT_8096_NOT_LOOPBACK; ! grep -Eq '0\.0\.0\.0:8096|\[::\]:8096'<<<"$lines"||fail PORT_8096_PUBLIC; say "$lines"; }

preflight(){
  [[ -d .git ]]||fail REPOSITORY_NOT_FOUND
  [[ "$(git branch --show-current)" == main ]]||fail BRANCH_NOT_MAIN
  [[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]]||fail HEAD_NOT_EXACT_E2C867D
  python3 "$HELPER" dirty-check "$ROOT"
  [[ "$(sha256sum "$DEPLOY"|awk '{print $1}')" == "$EXPECTED_DEPLOY_SHA256" ]]||fail DEPLOY_SHA_MISMATCH
  systemctl is-active --quiet "$SERVICE"||fail SERVICE_NOT_ACTIVE
  systemctl is-enabled --quiet "$SERVICE"||fail SERVICE_NOT_ENABLED
  [[ "$(systemctl is-active "$OLD_SERVICE" 2>/dev/null||true)" != active ]]||fail OLD_SERVICE_ACTIVE
  OLD_PID="$(systemctl show "$SERVICE" -p MainPID --value)"; [[ -d /proc/$OLD_PID ]]||fail MAINPID_INVALID
  tr '\0' ' '</proc/$OLD_PID/cmdline|grep -Fq "$ROOT/$SERVER"||fail PROCESS_PATH_UNEXPECTED
  port_gate
  [[ "$(code http://127.0.0.1:8096/)" == 200 ]]||fail LOCAL_ROOT_NOT_200
  [[ "$(code http://127.0.0.1:8096/healthz)" == 200 ]]||fail LOCAL_HEALTH_NOT_200
  NGINX_SITE="$(readlink -f "$NGINX_LINK")"; [[ -f "$NGINX_SITE" ]]||fail NGINX_SITE_MISSING
  grep -q 'server_name panel.coinoskobi.xyz' "$NGINX_SITE"||fail NGINX_SERVER_NAME_MISMATCH
  nginx -t >/dev/null 2>&1||fail NGINX_BASELINE_INVALID
  ext="$(extcode)"; [[ "$ext" == 500 || "$ext" == 401 ]]||fail EXTERNAL_HTTP_$ext
  say LOCAL_HEAD=$EXPECTED_HEAD OLD_MAIN_PID=$OLD_PID PROCESS_SOURCE_DISK_STATE=$([[ -f $SERVER ]]&&echo PRESENT||echo MISSING) PORT_8096=LOOPBACK_ONLY LOCAL_HTTP=200 EXTERNAL_PANEL_HTTP_BEFORE=$ext PREFLIGHT=PASS
}

shadow(){
  python3 - "$ROOT/$SERVER" >"$BACKUP/shadow.log" 2>&1 <<'PY' &
import importlib.util,sys
s=importlib.util.spec_from_file_location('m',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
assert all(m.CFG['authority'][k] is False for k in ('paper','live','wallet','signing','order','broadcast'))
m.ThreadingHTTPServer(('127.0.0.1',18096),m.H).serve_forever()
PY
  SHADOW_PID=$!
  for _ in {1..30}; do [[ "$(code http://127.0.0.1:18096/healthz)" == 200 ]]&&break; sleep .5; done
  [[ "$(code http://127.0.0.1:18096/)" == 200 ]]||fail SHADOW_ROOT_NOT_200
  c="$(curl -sS --max-time 150 -o "$BACKUP/shadow.json" -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"'"$SMOKE"'"}' http://127.0.0.1:18096/api/v1/analyze 2>/dev/null||true)"; [[ "$c" == 200 ]]||fail SHADOW_API_$c
  python3 "$HELPER" verify-packet "$BACKUP/shadow.json"; stop_shadow; say SHADOW_TEST=PASS
}

repair_nginx(){
  auth="${FIX6_AUTH_FILE:-}"; [[ -n "$auth" ]]||auth="$(python3 "$HELPER" discover-auth)"; [[ "$auth" =~ ^/[A-Za-z0-9._/-]+$ && -f "$auth" ]]||fail AUTH_FILE_INVALID
  cp -a "$NGINX_SITE" "$BACKUP/nginx.before"; NGINX_TOUCHED=1
  python3 "$HELPER" patch-nginx "$NGINX_SITE" "$auth"
  nginx -t||fail NGINX_PATCH_INVALID; systemctl reload nginx; sleep 2
  p="$(extcode)"; a="$(curl -sS -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"'"$SMOKE"'"}' https://panel.coinoskobi.xyz/api/v1/analyze 2>/dev/null||true)"
  [[ "$p" == 401 && "$a" == 401 && "$(code https://panel.coinoskobi.xyz/)" == 401 && "$(code https://panel.coinoskobi.xyz/healthz)" == 200 ]]||fail EXTERNAL_AUTH_GATE_FAILED
  install -d -m 0755 config/nginx; cp -a "$NGINX_SITE" config/nginx/panel.coinoskobi.xyz.conf
  say EXTERNAL_PANEL_UNAUTH_HTTP=401 EXTERNAL_API_UNAUTH_HTTP=401 NGINX_ROUTE_REPAIR=PASS
}

apply(){
  [[ "${FIX6_APPLY_CONFIRM:-}" == YES ]]||fail APPLY_CONFIRMATION_MISSING
  preflight
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"; BACKUP="/root/tokenoskobi_product_slice_02_fix6_$stamp"; stage="$BACKUP/stage"; mkdir -p "$stage"
  cp -a "/etc/systemd/system/$SERVICE" "$BACKUP/unit.before"; cp -a "$NGINX_SITE" "$BACKUP/nginx.initial"
  find /etc/nginx -type f ! -path "$NGINX_SITE" -print0|sort -z|xargs -0 -r sha256sum >"$BACKUP/nginx_other.before"
  python3 "$HELPER" extract "$DEPLOY" "$stage"
  install -d -m 0755 config tools tests systemd_drafts
  install -m0644 "$stage/$CONFIG" "$CONFIG"; install -m0755 "$stage/$SERVER" "$SERVER"; install -m0644 "$stage/$TEST" "$TEST"; install -m0644 "$stage/$UNIT" "$UNIT"
  python3 -m py_compile "$SERVER" "$TEST"; python3 -m unittest -v "$TEST"; shadow
  install -m0644 "$UNIT" "/etc/systemd/system/$SERVICE"; SERVICE_TOUCHED=1; systemctl daemon-reload; systemctl restart "$SERVICE"
  for _ in {1..30}; do NEW_PID="$(systemctl show "$SERVICE" -p MainPID --value 2>/dev/null||true)"; [[ -d /proc/$NEW_PID && "$NEW_PID" != "$OLD_PID" ]]&&break; sleep .5; done
  systemctl is-active --quiet "$SERVICE"||fail SERVICE_RESTART_FAILED; [[ "$NEW_PID" != "$OLD_PID" ]]||fail PID_NOT_CHANGED
  tr '\0' ' '</proc/$NEW_PID/cmdline|grep -Fq "$ROOT/$SERVER"||fail NEW_PROCESS_PATH_BAD; port_gate
  [[ "$(code http://127.0.0.1:8096/healthz)" == 200 ]]||fail NEW_HEALTH_BAD
  c="$(curl -sS --max-time 150 -o "$BACKUP/local.json" -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"'"$SMOKE"'"}' http://127.0.0.1:8096/api/v1/analyze 2>/dev/null||true)"; [[ "$c" == 200 ]]||fail LOCAL_API_$c; python3 "$HELPER" verify-packet "$BACKUP/local.json"
  [[ "$(extcode)" == 500 ]]&&repair_nginx||[[ "$(extcode)" == 401 ]]||fail EXTERNAL_STATE_CHANGED
  find /etc/nginx -type f ! -path "$NGINX_SITE" -print0|sort -z|xargs -0 -r sha256sum >"$BACKUP/nginx_other.after"; cmp -s "$BACKUP/nginx_other.before" "$BACKUP/nginx_other.after"||fail OTHER_NGINX_CHANGED
  python3 "$HELPER" dirty-check "$ROOT"
  say FIX6_RESULT=RECOVERED_PENDING_USER_ACCEPTANCE_AND_SEPARATE_SEAL LOCAL_HEAD=$EXPECTED_HEAD OLD_MAIN_PID=$OLD_PID NEW_MAIN_PID=$NEW_PID PROCESS_SOURCE_PATH=$ROOT/$SERVER PROCESS_SOURCE_SHA256=$(sha256sum "$SERVER"|awk '{print $1}') PORT_8096=LOOPBACK_ONLY EXTERNAL_PANEL_UNAUTH_HTTP=$(extcode) PAPER_TRADE=DISABLED LIVE_TRADE=DISABLED WALLET_SIGNING_ORDER_AUTHORITY=0 CANONICAL_UPDATE=NONE COMMIT_PUSH=NONE BACKUP_DIR=$BACKUP NEXT_SAFE_STEP=PHONE_AUTHENTICATED_PANEL_ACCEPTANCE_THEN_SEPARATE_SEAL
  trap - ERR INT TERM
}

case "$MODE" in
  --audit) preflight; say FIX6_MODE=AUDIT_ONLY MUTATION_PERFORMED=NONE NEXT_SAFE_STEP=EXPLICIT_FIX6_APPLY_APPROVAL;;
  --apply) apply;;
  *) fail USAGE_AUDIT_OR_APPLY;;
esac
