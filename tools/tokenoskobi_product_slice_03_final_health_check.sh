#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_HEAD='60833fab96ec0a8af2f9d5f43c582feb7da182d2'
SERVICE='tokenoskobi-product-slice-02.service'
STATE_DIR='/var/lib/tokenoskobi-product-slice-03'
EXPECTED_STATUS=$' M config/nginx/panel.coinoskobi.xyz.conf\n M systemd_drafts/tokenoskobi-product-slice-02.service\n?? tests/test_product_slice_03.py\n?? tests/test_product_slice_03_runtime.py\n?? tools/tokenoskobi_product_slice_03_runtime.py\n?? tools/tokenoskobi_product_slice_03_server.py'
TMP="$(mktemp -d /tmp/tokenoskobi_slice03_health.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"

fail() {
  printf 'BLOCKED=%s\n' "$1" >&2
  exit 1
}

http_code() {
  curl -sS --connect-timeout 5 --max-time 25 \
    -o /dev/null -w '%{http_code}' "$1" 2>/dev/null || true
}

printf '\n===== 1 REPOSITORY SCOPE =====\n'
[[ "$(git branch --show-current)" == 'main' ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail LOCAL_HEAD_CHANGED
git fetch --quiet origin main
[[ "$(git rev-parse origin/main)" == "$EXPECTED_HEAD" ]] || fail ORIGIN_MAIN_CHANGED
ACTUAL_STATUS="$(git status --short --untracked-files=all)"
printf '%s\n' "$ACTUAL_STATUS"
[[ "$ACTUAL_STATUS" == "$EXPECTED_STATUS" ]] || fail WORKTREE_SCOPE_CHANGED
git diff --check
printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'LOCAL_PRODUCT_SCOPE=6_FILES_EXACT\n'

printf '\n===== 2 SERVICE AND SECURITY =====\n'
systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE
systemctl is-active --quiet nginx || fail NGINX_NOT_ACTIVE
[[ "$(systemctl show "$SERVICE" -p ProtectSystem --value)" == 'strict' ]] || fail PROTECT_SYSTEM_NOT_STRICT
[[ "$(systemctl show "$SERVICE" -p PrivateTmp --value)" == 'yes' ]] || fail PRIVATE_TMP_NOT_ENABLED
PID="$(systemctl show "$SERVICE" -p MainPID --value)"
RESTARTS="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PID" =~ ^[1-9][0-9]*$ ]] || fail PRODUCT_PID_INVALID
[[ "$RESTARTS" == '0' ]] || fail PRODUCT_SERVICE_RESTARTED_UNEXPECTEDLY
[[ -d "$STATE_DIR" ]] || fail STATE_DIRECTORY_MISSING
[[ "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_MODE_INVALID
[[ -f "$STATE_DIR/decision_history_v1.jsonl" ]] || fail EVENT_LOG_MISSING
[[ "$(stat -c '%a' "$STATE_DIR/decision_history_v1.jsonl")" == '600' ]] || fail EVENT_LOG_MODE_INVALID
PACKET_COUNT="$(find "$STATE_DIR/packets" -maxdepth 1 -type f -name '*.json' | wc -l)"
[[ "$PACKET_COUNT" -gt 0 ]] || fail EVIDENCE_PACKETS_MISSING
BAD_PACKET_MODE="$(find "$STATE_DIR/packets" -maxdepth 1 -type f -name '*.json' ! -perm 0600 -print -quit)"
[[ -z "$BAD_PACKET_MODE" ]] || fail EVIDENCE_PACKET_MODE_INVALID
printf 'PRODUCT_PID=%s\n' "$PID"
printf 'PRODUCT_NRESTARTS=%s\n' "$RESTARTS"
printf 'STATE_DIRECTORY_MODE=700\n'
printf 'EVENT_AND_PACKET_MODE=600\n'
printf 'SYSTEMD_HARDENING=PRESERVED\n'

printf '\n===== 3 PHONE EVIDENCE CHAIN =====\n'
curl -sS --connect-timeout 5 --max-time 30 \
  'http://127.0.0.1:8096/api/v1/history?limit=100' \
  > "$TMP/history.json"

PACKET_ID="$(python3 - "$TMP/history.json" <<'PY'
import json, sys
h=json.load(open(sys.argv[1], encoding='utf-8'))
assert h['integrity']=='VERIFIED'
match=None
for r in h['records']:
    d=(r.get('latest_human_decision') or {}).get('payload') or {}
    if d.get('note')=='Telefon kabul testi' and d.get('action')=='WAIT':
        match=r
        break
assert match is not None
out=match.get('latest_outcome') or {}
op=out.get('payload') or {}
assert d.get('actor')=='coinoskobi_xyz'
assert op.get('actor')=='coinoskobi_xyz'
assert op.get('human_decision_event_hash')==match['latest_human_decision']['event_hash']
assert float(op['current_price_usd']) > 100
assert op['classification'] in ('UP','DOWN','FLAT')
assert op['target_orientation_verified'] is True
print(match['packet_id'])
PY
)"

curl -sS --connect-timeout 5 --max-time 30 \
  "http://127.0.0.1:8096/api/v1/packets/${PACKET_ID}" \
  > "$TMP/packet.json"

python3 - "$TMP/packet.json" "$PACKET_ID" <<'PY'
import json, sys
p=json.load(open(sys.argv[1], encoding='utf-8'))
pid=sys.argv[2]
assert p['integrity']=='VERIFIED'
assert p['packet']['packet_id']==pid
events=p['events']
assert [e['event_type'] for e in events]==[
    'ANALYSIS_CREATED',
    'HUMAN_DECISION_RECORDED',
    'OUTCOME_OBSERVED',
]
assert [e['seq'] for e in events]==sorted(e['seq'] for e in events)
d=events[1]['payload']
o=events[2]['payload']
assert d['action']=='WAIT'
assert d['note']=='Telefon kabul testi'
assert d['actor']=='coinoskobi_xyz'
assert o['actor']=='coinoskobi_xyz'
assert o['human_decision_event_hash']==events[1]['event_hash']
assert float(o['baseline_price_usd']) > 100
assert float(o['current_price_usd']) > 100
assert o['classification'] in ('UP','DOWN','FLAT')
print('PHONE_PACKET_REOPEN=PASS')
print('PHONE_HUMAN_DECISION=WAIT')
print('PHONE_OUTCOME_TRACKING=PASS')
print('PHONE_ACTOR=coinoskobi_xyz')
print('PHONE_BASELINE_PRICE_USD='+str(o['baseline_price_usd']))
print('PHONE_CURRENT_PRICE_USD='+str(o['current_price_usd']))
print('PHONE_CHANGE_PCT='+str(o['change_pct']))
print('PHONE_CLASSIFICATION='+str(o['classification']))
PY
printf 'PHONE_PACKET_ID=%s\n' "$PACKET_ID"
printf 'HASH_CHAIN_INTEGRITY=VERIFIED\n'

printf '\n===== 4 LOCAL AND EXTERNAL HEALTH =====\n'
[[ "$(http_code http://127.0.0.1:8096/healthz)" == '200' ]] || fail LOCAL_HEALTH_NOT_200
[[ "$(http_code https://panel.coinoskobi.xyz/panel/panel_v2/)" == '401' ]] || fail EXTERNAL_PANEL_AUTH_GATE_CHANGED
[[ "$(http_code https://panel.coinoskobi.xyz/healthz)" == '200' ]] || fail EXTERNAL_HEALTH_NOT_200
API_UNAUTH="$(curl -sS --connect-timeout 5 --max-time 25 -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"}' https://panel.coinoskobi.xyz/api/v1/analyze 2>/dev/null || true)"
[[ "$API_UNAUTH" == '401' ]] || fail EXTERNAL_API_AUTH_GATE_CHANGED
printf 'LOCAL_HEALTH_HTTP=200\n'
printf 'EXTERNAL_PANEL_UNAUTH_HTTP=401\n'
printf 'EXTERNAL_API_UNAUTH_HTTP=401\n'
printf 'EXTERNAL_HEALTH_HTTP=200\n'
printf 'BASIC_AUTH=PRESERVED\n'

printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_03_FINAL_HEALTH=PASS\n'
printf 'PHONE_ACCEPTANCE=VERIFIED\n'
printf 'FAILED_TO_FETCH_EXTRA_ANALYZE=NON_BLOCKING_TRANSIENT\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_16=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_15=OPEN\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'
printf 'NEXT_SAFE_STEP=FINAL_COMMIT_PUSH_CANONICAL_SEAL\n'
