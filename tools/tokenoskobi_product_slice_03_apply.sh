#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='60833fab96ec0a8af2f9d5f43c582feb7da182d2'
BRANCH='agent/product-slice-03-human-decision-history'
SOURCE_HEAD="${PRODUCT_SLICE_03_SOURCE_HEAD:-}"

CORE='tools/tokenoskobi_product_slice_03_server.py'
RUNTIME='tools/tokenoskobi_product_slice_03_runtime.py'
TEST_CORE='tests/test_product_slice_03.py'
TEST_RUNTIME='tests/test_product_slice_03_runtime.py'
UNIT='systemd_drafts/tokenoskobi-product-slice-02.service'
NGINX_REPO='config/nginx/panel.coinoskobi.xyz.conf'

CORE_BLOB='138e8f1b3562cecb930cfe211c8f2017ecc19da9'
RUNTIME_BLOB='119e608e995317adbfe542f6ca93480bd87ab47e'
TEST_CORE_BLOB='b2cf06d082a8b1bd165de47b38115529420a1a51'
TEST_RUNTIME_BLOB='cad64d73b6a7d410b389db36e62a6f20e5d81fd5'
UNIT_BLOB='bf1c428da08390f6756a8fb75c75293b3aec3ab6'
NGINX_BLOB='6354dd881694f0d21259def230ead02888f28509'

SERVICE='tokenoskobi-product-slice-02.service'
STATE_DIR='/var/lib/tokenoskobi-product-slice-03'
RUNTIME_DIR='/run/tokenoskobi-product-slice-02'
SHADOW_PORT='18097'
WBNB='0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'

BACKUP=''
ACTIVE_UNIT=''
ACTIVE_NGINX=''
SHADOW_PID=''
REPO_CHANGED=0
UNIT_CHANGED=0
NGINX_CHANGED=0
STATE_EXISTED=0

cd "$ROOT"

exec 9>/run/tokenoskobi_product_slice_03_apply.lock
flock -n 9 || {
  printf 'BLOCKED=ANOTHER_SLICE03_APPLY_IS_RUNNING\n'
  exit 1
}

fail() {
  printf 'BLOCKED=%s\n' "$1" >&2
  return 1
}

http_code() {
  curl -sS \
    --connect-timeout 5 \
    --max-time 25 \
    -o /dev/null \
    -w '%{http_code}' \
    "$1" 2>/dev/null || true
}

wait_http() {
  local url="$1"
  local expected="$2"
  local attempt code
  for attempt in $(seq 1 60); do
    code="$(http_code "$url")"
    [[ "$code" == "$expected" ]] && return 0
    sleep 1
  done
  return 1
}

cleanup_shadow() {
  set +e
  if [[ -n "$SHADOW_PID" ]] && kill -0 "$SHADOW_PID" 2>/dev/null; then
    kill "$SHADOW_PID" 2>/dev/null || true
    wait "$SHADOW_PID" 2>/dev/null || true
  fi
  SHADOW_PID=''
  set -e
}

rollback() {
  local rc=$?
  trap - ERR INT TERM
  set +e
  cleanup_shadow

  if [[ "$REPO_CHANGED" -eq 1 && -n "$BACKUP" ]]; then
    rm -f "$CORE" "$RUNTIME" "$TEST_CORE" "$TEST_RUNTIME"
    cp "$BACKUP/unit.repo.original" "$UNIT" 2>/dev/null || true
    cp "$BACKUP/nginx.repo.original" "$NGINX_REPO" 2>/dev/null || true
    chmod 0644 "$UNIT" "$NGINX_REPO" 2>/dev/null || true
  fi

  if [[ "$UNIT_CHANGED" -eq 1 && -f "$BACKUP/unit.active.original" ]]; then
    cp "$BACKUP/unit.active.original" "$ACTIVE_UNIT" 2>/dev/null || true
    chmod 0644 "$ACTIVE_UNIT" 2>/dev/null || true
  fi

  if [[ "$NGINX_CHANGED" -eq 1 && -f "$BACKUP/nginx.active.original" ]]; then
    cp "$BACKUP/nginx.active.original" "$ACTIVE_NGINX" 2>/dev/null || true
    chmod 0644 "$ACTIVE_NGINX" 2>/dev/null || true
  fi

  if [[ "$STATE_EXISTED" -eq 0 ]]; then
    rm -rf "$STATE_DIR" 2>/dev/null || true
  elif [[ -f "$BACKUP/state_before.tar.gz" ]]; then
    rm -rf "$STATE_DIR" 2>/dev/null || true
    tar -xzf "$BACKUP/state_before.tar.gz" -C / 2>/dev/null || true
  fi

  systemctl daemon-reload >/dev/null 2>&1 || true
  nginx -t >/dev/null 2>&1 && systemctl reload nginx >/dev/null 2>&1 || true
  systemctl restart "$SERVICE" >/dev/null 2>&1 || true
  wait_http 'http://127.0.0.1:8096/healthz' '200' >/dev/null 2>&1 || true

  printf '\n===== ROLLBACK =====\n'
  printf 'PRODUCT_SLICE_03_APPLY=FAILED_ROLLED_BACK\n'
  printf 'FAILED_RC=%s\n' "$rc"
  printf 'REPO_ROLLBACK=%s\n' "$REPO_CHANGED"
  printf 'UNIT_ROLLBACK=%s\n' "$UNIT_CHANGED"
  printf 'NGINX_ROLLBACK=%s\n' "$NGINX_CHANGED"
  printf 'PAPER_TRADE=DISABLED\n'
  printf 'LIVE_TRADE=DISABLED\n'
  printf 'REAL_FINANCIAL_AUTHORITY=0\n'
  exit "$rc"
}

trap rollback ERR INT TERM

[[ -n "$SOURCE_HEAD" ]] || fail SOURCE_HEAD_ENV_MISSING

printf '\n===== 1 EXACT PREFLIGHT =====\n'
[[ "$(git branch --show-current)" == 'main' ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$EXPECTED_MAIN" ]] || fail LOCAL_HEAD_CHANGED
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail WORKTREE_NOT_CLEAN

git fetch --quiet origin \
  'refs/heads/main:refs/remotes/origin/main' \
  "refs/heads/${BRANCH}:refs/remotes/origin/${BRANCH}"

[[ "$(git rev-parse origin/main)" == "$EXPECTED_MAIN" ]] || fail ORIGIN_MAIN_CHANGED
[[ "$(git rev-parse "origin/${BRANCH}")" == "$SOURCE_HEAD" ]] || fail SOURCE_HEAD_CHANGED
[[ "$(git merge-base "$EXPECTED_MAIN" "$SOURCE_HEAD")" == "$EXPECTED_MAIN" ]] || fail SOURCE_BASE_INVALID

systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE
systemctl is-active --quiet nginx || fail NGINX_NOT_ACTIVE
[[ "$(http_code http://127.0.0.1:8096/healthz)" == '200' ]] || fail LOCAL_HEALTH_NOT_200

ACTIVE_UNIT="$(systemctl show "$SERVICE" -p FragmentPath --value)"
[[ -n "$ACTIVE_UNIT" && -f "$ACTIVE_UNIT" ]] || fail ACTIVE_UNIT_NOT_FOUND

mapfile -t NGINX_CANDIDATES < <(
  grep -RIl 'server_name panel.coinoskobi.xyz;' \
    /etc/nginx/sites-enabled /etc/nginx/conf.d 2>/dev/null | sort -u
)
[[ "${#NGINX_CANDIDATES[@]}" -eq 1 ]] || fail ACTIVE_NGINX_CONFIG_COUNT_NOT_ONE
ACTIVE_NGINX="$(readlink -f "${NGINX_CANDIDATES[0]}")"
[[ -f "$ACTIVE_NGINX" ]] || fail ACTIVE_NGINX_NOT_FOUND

printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_HEAD=%s\n' "$SOURCE_HEAD"
printf 'ACTIVE_UNIT=%s\n' "$ACTIVE_UNIT"
printf 'ACTIVE_NGINX=%s\n' "$ACTIVE_NGINX"

printf '\n===== 2 MATERIALIZE EXACT BRANCH FILES =====\n'
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/tokenoskobi_product_slice_03_apply_${STAMP}"
mkdir -p "$BACKUP/new" "$BACKUP/test_rate" "$BACKUP/test_state" "$BACKUP/shadow_rate" "$BACKUP/shadow_state"
chmod 0700 "$BACKUP" "$BACKUP/test_rate" "$BACKUP/test_state" "$BACKUP/shadow_rate" "$BACKUP/shadow_state"

cp "$UNIT" "$BACKUP/unit.repo.original"
cp "$NGINX_REPO" "$BACKUP/nginx.repo.original"
cp "$ACTIVE_UNIT" "$BACKUP/unit.active.original"
cp "$ACTIVE_NGINX" "$BACKUP/nginx.active.original"

if [[ -d "$STATE_DIR" ]]; then
  STATE_EXISTED=1
  tar -czf "$BACKUP/state_before.tar.gz" -C / "${STATE_DIR#/}"
fi

for path in "$CORE" "$RUNTIME" "$TEST_CORE" "$TEST_RUNTIME" "$UNIT" "$NGINX_REPO"; do
  mkdir -p "$BACKUP/new/$(dirname "$path")"
  git show "$SOURCE_HEAD:$path" > "$BACKUP/new/$path"
done

[[ "$(git hash-object "$BACKUP/new/$CORE")" == "$CORE_BLOB" ]] || fail CORE_BLOB_MISMATCH
[[ "$(git hash-object "$BACKUP/new/$RUNTIME")" == "$RUNTIME_BLOB" ]] || fail RUNTIME_BLOB_MISMATCH
[[ "$(git hash-object "$BACKUP/new/$TEST_CORE")" == "$TEST_CORE_BLOB" ]] || fail TEST_CORE_BLOB_MISMATCH
[[ "$(git hash-object "$BACKUP/new/$TEST_RUNTIME")" == "$TEST_RUNTIME_BLOB" ]] || fail TEST_RUNTIME_BLOB_MISMATCH
[[ "$(git hash-object "$BACKUP/new/$UNIT")" == "$UNIT_BLOB" ]] || fail UNIT_BLOB_MISMATCH
[[ "$(git hash-object "$BACKUP/new/$NGINX_REPO")" == "$NGINX_BLOB" ]] || fail NGINX_BLOB_MISMATCH
printf 'EXACT_SOURCE_FILES=6_6_PASS\n'

printf '\n===== 3 STATIC AND DETERMINISTIC TESTS =====\n'
python3 -m py_compile \
  "$BACKUP/new/$CORE" \
  "$BACKUP/new/$RUNTIME" \
  "$BACKUP/new/$TEST_CORE" \
  "$BACKUP/new/$TEST_RUNTIME"

TOKENOSKOBI_ROOT="$ROOT" \
TOKENOSKOBI_GT_RATE_DIR="$BACKUP/test_rate" \
TOKENOSKOBI_SLICE03_STATE_DIR="$BACKUP/test_state" \
TOKENOSKOBI_SLICE02_SERVER_PATH="$ROOT/tools/tokenoskobi_product_slice_02_server.py" \
TOKENOSKOBI_SLICE03_SERVER_PATH="$BACKUP/new/$CORE" \
  python3 "$BACKUP/new/$TEST_CORE"

rm -rf "$BACKUP/test_state" && mkdir -m 0700 "$BACKUP/test_state"

TOKENOSKOBI_ROOT="$ROOT" \
TOKENOSKOBI_GT_RATE_DIR="$BACKUP/test_rate" \
TOKENOSKOBI_SLICE03_STATE_DIR="$BACKUP/test_state" \
TOKENOSKOBI_SLICE02_SERVER_PATH="$ROOT/tools/tokenoskobi_product_slice_02_server.py" \
TOKENOSKOBI_SLICE03_CORE_PATH="$BACKUP/new/$CORE" \
TOKENOSKOBI_SLICE03_RUNTIME_PATH="$BACKUP/new/$RUNTIME" \
  python3 "$BACKUP/new/$TEST_RUNTIME"

systemd-analyze verify "$BACKUP/new/$UNIT"
grep -Fxq 'ProtectSystem=strict' "$BACKUP/new/$UNIT"
grep -Fxq 'PrivateTmp=true' "$BACKUP/new/$UNIT"
grep -Fxq 'ReadOnlyPaths=/root/tokenoskobi_clean_v1' "$BACKUP/new/$UNIT"
grep -Fxq 'StateDirectory=tokenoskobi-product-slice-03' "$BACKUP/new/$UNIT"
grep -Fxq 'StateDirectoryMode=0700' "$BACKUP/new/$UNIT"
grep -Fxq 'CapabilityBoundingSet=' "$BACKUP/new/$UNIT"
grep -Fxq '        proxy_set_header X-Authenticated-User $remote_user;' "$BACKUP/new/$NGINX_REPO"
printf 'DETERMINISTIC_TESTS=24_24_PASS\n'
printf 'SYSTEMD_SECURITY_CONTRACT=PASS\n'
printf 'AUTHENTICATED_ACTOR_HEADER=PASS\n'

printf '\n===== 4 SHADOW END-TO-END ACCEPTANCE =====\n'
printf 'GECKOTERMINAL_PRE_SHADOW_COOLDOWN_SEC=70\n'
sleep 70

TOKENOSKOBI_ROOT="$ROOT" \
TOKENOSKOBI_PRODUCT_SLICE_02_PORT="$SHADOW_PORT" \
TOKENOSKOBI_GT_RATE_DIR="$BACKUP/shadow_rate" \
TOKENOSKOBI_SLICE03_STATE_DIR="$BACKUP/shadow_state" \
TOKENOSKOBI_SLICE02_SERVER_PATH="$ROOT/tools/tokenoskobi_product_slice_02_server.py" \
TOKENOSKOBI_SLICE03_CORE_PATH="$BACKUP/new/$CORE" \
  python3 "$BACKUP/new/$RUNTIME" > "$BACKUP/shadow.log" 2>&1 &
SHADOW_PID=$!

wait_http "http://127.0.0.1:${SHADOW_PORT}/healthz" '200' || fail SHADOW_NOT_READY

curl -sS --connect-timeout 5 --max-time 600 \
  -H 'Content-Type: application/json' \
  --data '{"token_address":"'"$WBNB"'"}' \
  "http://127.0.0.1:${SHADOW_PORT}/api/v1/analyze" > "$BACKUP/shadow_analyze.json"

SHADOW_PACKET_ID="$(
  python3 - "$BACKUP/shadow_analyze.json" <<'PY'
import json, sys
p=json.load(open(sys.argv[1], encoding='utf-8'))
assert p['authority']['paper'] is False
assert p['authority']['live'] is False
assert p['decision']['data_quality']=='SUFFICIENT'
assert p['market']['target_orientation_verified'] is True
assert float(p['market']['token']['price_usd']) > 100
assert p['history']['immutable'] is True
print(p['history']['packet_id'])
PY
)"

curl -sS --connect-timeout 5 --max-time 30 \
  -H 'Content-Type: application/json' \
  -H 'X-Authenticated-User: SHADOW_TEST_USER' \
  --data '{"packet_id":"'"$SHADOW_PACKET_ID"'","action":"WAIT","note":"shadow acceptance"}' \
  "http://127.0.0.1:${SHADOW_PORT}/api/v1/decisions" > "$BACKUP/shadow_decision.json"

curl -sS --connect-timeout 5 --max-time 30 \
  "http://127.0.0.1:${SHADOW_PORT}/api/v1/history?limit=20" > "$BACKUP/shadow_history.json"

curl -sS --connect-timeout 5 --max-time 30 \
  "http://127.0.0.1:${SHADOW_PORT}/api/v1/packets/${SHADOW_PACKET_ID}" > "$BACKUP/shadow_packet.json"

python3 - "$BACKUP/shadow_decision.json" "$BACKUP/shadow_history.json" "$BACKUP/shadow_packet.json" "$SHADOW_PACKET_ID" <<'PY'
import json, sys
d=json.load(open(sys.argv[1], encoding='utf-8'))
h=json.load(open(sys.argv[2], encoding='utf-8'))
p=json.load(open(sys.argv[3], encoding='utf-8'))
pid=sys.argv[4]
assert d['event']['payload']['actor']=='SHADOW_TEST_USER'
assert d['event']['payload']['action']=='WAIT'
assert h['integrity']=='VERIFIED'
r=next(x for x in h['records'] if x['packet_id']==pid)
assert r['latest_human_decision']['payload']['actor']=='SHADOW_TEST_USER'
assert p['integrity']=='VERIFIED'
assert p['packet']['packet_id']==pid
assert [e['event_type'] for e in p['events']]==['ANALYSIS_CREATED','HUMAN_DECISION_RECORDED']
print('SHADOW_HISTORY_AND_REOPEN=PASS')
PY
cleanup_shadow

printf '\n===== 5 ATOMIC REPOSITORY APPLY =====\n'
install -m 0755 "$BACKUP/new/$CORE" "${CORE}.tmp.$$"
install -m 0755 "$BACKUP/new/$RUNTIME" "${RUNTIME}.tmp.$$"
install -m 0644 "$BACKUP/new/$TEST_CORE" "${TEST_CORE}.tmp.$$"
install -m 0644 "$BACKUP/new/$TEST_RUNTIME" "${TEST_RUNTIME}.tmp.$$"
install -m 0644 "$BACKUP/new/$UNIT" "${UNIT}.tmp.$$"
install -m 0644 "$BACKUP/new/$NGINX_REPO" "${NGINX_REPO}.tmp.$$"
mv -f "${CORE}.tmp.$$" "$CORE"
mv -f "${RUNTIME}.tmp.$$" "$RUNTIME"
mv -f "${TEST_CORE}.tmp.$$" "$TEST_CORE"
mv -f "${TEST_RUNTIME}.tmp.$$" "$TEST_RUNTIME"
mv -f "${UNIT}.tmp.$$" "$UNIT"
mv -f "${NGINX_REPO}.tmp.$$" "$NGINX_REPO"
REPO_CHANGED=1

git diff --check
EXPECTED_STATUS=$' M config/nginx/panel.coinoskobi.xyz.conf\n M systemd_drafts/tokenoskobi-product-slice-02.service\n?? tests/test_product_slice_03.py\n?? tests/test_product_slice_03_runtime.py\n?? tools/tokenoskobi_product_slice_03_runtime.py\n?? tools/tokenoskobi_product_slice_03_server.py'
ACTUAL_STATUS="$(git status --short --untracked-files=all)"
printf '%s\n' "$ACTUAL_STATUS"
[[ "$ACTUAL_STATUS" == "$EXPECTED_STATUS" ]] || fail APPLIED_SCOPE_CHANGED

printf '\n===== 6 DEPLOY UNIT AND NGINX =====\n'
install -m 0644 "$UNIT" "${ACTIVE_UNIT}.tmp.$$"
mv -f "${ACTIVE_UNIT}.tmp.$$" "$ACTIVE_UNIT"
UNIT_CHANGED=1

install -m 0644 "$NGINX_REPO" "${ACTIVE_NGINX}.tmp.$$"
mv -f "${ACTIVE_NGINX}.tmp.$$" "$ACTIVE_NGINX"
NGINX_CHANGED=1

nginx -t
systemctl daemon-reload
OLD_PID="$(systemctl show "$SERVICE" -p MainPID --value)"
systemctl restart "$SERVICE"
wait_http 'http://127.0.0.1:8096/healthz' '200' || fail PRODUCTION_NOT_READY
systemctl reload nginx
sleep 3
NEW_PID="$(systemctl show "$SERVICE" -p MainPID --value)"
[[ "$NEW_PID" =~ ^[1-9][0-9]*$ && "$NEW_PID" != "$OLD_PID" ]] || fail PRODUCT_PID_INVALID
[[ -d "$STATE_DIR" && "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_INVALID
[[ "$(systemctl show "$SERVICE" -p ProtectSystem --value)" == 'strict' ]] || fail PROTECT_SYSTEM_NOT_STRICT
[[ "$(systemctl show "$SERVICE" -p PrivateTmp --value)" == 'yes' ]] || fail PRIVATE_TMP_NOT_ENABLED
printf 'OLD_PID=%s\n' "$OLD_PID"
printf 'NEW_PID=%s\n' "$NEW_PID"
printf 'STATE_DIRECTORY=%s\n' "$STATE_DIR"
printf 'STATE_DIRECTORY_MODE=700\n'
printf 'REPOSITORY_READ_ONLY=PRESERVED\n'

printf '\n===== 7 PRODUCTION END-TO-END ACCEPTANCE =====\n'
printf 'GECKOTERMINAL_PRE_PRODUCTION_COOLDOWN_SEC=70\n'
sleep 70

curl -sS --connect-timeout 5 --max-time 600 \
  -H 'Content-Type: application/json' \
  --data '{"token_address":"'"$WBNB"'"}' \
  http://127.0.0.1:8096/api/v1/analyze > "$BACKUP/production_analyze.json"

PACKET_ID="$(
  python3 - "$BACKUP/production_analyze.json" <<'PY'
import json, sys
p=json.load(open(sys.argv[1], encoding='utf-8'))
assert p['decision']['data_quality']=='SUFFICIENT'
assert p['market']['target_orientation_verified'] is True
assert float(p['market']['token']['price_usd']) > 100
assert p['history']['immutable'] is True
assert all(p['authority'][k] is False for k in ('paper','live','wallet','signing','order','broadcast'))
print(p['history']['packet_id'])
PY
)"

curl -sS --connect-timeout 5 --max-time 30 \
  -H 'Content-Type: application/json' \
  -H 'X-Authenticated-User: LOCAL_ACCEPTANCE' \
  --data '{"packet_id":"'"$PACKET_ID"'","action":"WAIT","note":"production machine acceptance"}' \
  http://127.0.0.1:8096/api/v1/decisions > "$BACKUP/production_decision.json"

printf 'GECKOTERMINAL_PRE_OUTCOME_COOLDOWN_SEC=70\n'
sleep 70

curl -sS --connect-timeout 5 --max-time 300 \
  -H 'Content-Type: application/json' \
  -H 'X-Authenticated-User: LOCAL_ACCEPTANCE' \
  --data '{"packet_id":"'"$PACKET_ID"'"}' \
  http://127.0.0.1:8096/api/v1/outcomes/observe > "$BACKUP/production_outcome.json"

curl -sS --connect-timeout 5 --max-time 30 \
  http://127.0.0.1:8096/api/v1/history?limit=20 > "$BACKUP/production_history.json"
curl -sS --connect-timeout 5 --max-time 30 \
  "http://127.0.0.1:8096/api/v1/packets/${PACKET_ID}" > "$BACKUP/production_packet.json"

python3 - "$BACKUP/production_decision.json" "$BACKUP/production_outcome.json" "$BACKUP/production_history.json" "$BACKUP/production_packet.json" "$PACKET_ID" <<'PY'
import json, sys
d=json.load(open(sys.argv[1], encoding='utf-8'))
o=json.load(open(sys.argv[2], encoding='utf-8'))
h=json.load(open(sys.argv[3], encoding='utf-8'))
p=json.load(open(sys.argv[4], encoding='utf-8'))
pid=sys.argv[5]
assert d['event']['payload']['actor']=='LOCAL_ACCEPTANCE'
assert d['event']['payload']['action']=='WAIT'
assert o['event']['payload']['actor']=='LOCAL_ACCEPTANCE'
assert o['event']['payload']['human_decision_event_hash']==d['event']['event_hash']
assert o['event']['payload']['target_orientation_verified'] is True
assert float(o['event']['payload']['current_price_usd']) > 100
assert h['integrity']=='VERIFIED'
r=next(x for x in h['records'] if x['packet_id']==pid)
assert r['latest_human_decision']['event_hash']==d['event']['event_hash']
assert r['latest_outcome']['event_hash']==o['event']['event_hash']
assert p['integrity']=='VERIFIED'
assert [e['event_type'] for e in p['events']]==['ANALYSIS_CREATED','HUMAN_DECISION_RECORDED','OUTCOME_OBSERVED']
assert [e['seq'] for e in p['events']]==sorted(e['seq'] for e in p['events'])
print('PRODUCTION_APPEND_ONLY_HISTORY=PASS')
print('PRODUCTION_PACKET_REOPEN=PASS')
print('PRODUCTION_OUTCOME_TRACKING=PASS')
PY

[[ "$(stat -c '%a' "$STATE_DIR/decision_history_v1.jsonl")" == '600' ]] || fail EVENT_LOG_MODE_INVALID
[[ "$(find "$STATE_DIR/packets" -maxdepth 1 -type f -name '*.json' -printf '%m\n' | sort -u)" == '600' ]] || fail PACKET_MODE_INVALID

printf '\n===== 8 EXTERNAL AND FINAL GATES =====\n'
[[ "$(http_code http://127.0.0.1:8096/healthz)" == '200' ]] || fail FINAL_LOCAL_HEALTH_NOT_200
[[ "$(http_code https://panel.coinoskobi.xyz/panel/panel_v2/)" == '401' ]] || fail EXTERNAL_PANEL_AUTH_GATE_CHANGED
[[ "$(http_code https://panel.coinoskobi.xyz/healthz)" == '200' ]] || fail EXTERNAL_HEALTH_NOT_200
API_UNAUTH="$(curl -sS --connect-timeout 5 --max-time 25 -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"'"$WBNB"'"}' https://panel.coinoskobi.xyz/api/v1/analyze 2>/dev/null || true)"
[[ "$API_UNAUTH" == '401' ]] || fail EXTERNAL_API_AUTH_GATE_CHANGED

git diff --check
ACTUAL_STATUS="$(git status --short --untracked-files=all)"
[[ "$ACTUAL_STATUS" == "$EXPECTED_STATUS" ]] || fail FINAL_SCOPE_CHANGED

trap - ERR INT TERM
printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_03_LOCAL_APPLY=SUCCESS\n'
printf 'DETERMINISTIC_TESTS=24_24_PASS\n'
printf 'SHADOW_HISTORY_AND_REOPEN=PASS\n'
printf 'PRODUCTION_APPEND_ONLY_HISTORY=PASS\n'
printf 'PRODUCTION_PACKET_REOPEN=PASS\n'
printf 'PRODUCTION_OUTCOME_TRACKING=PASS\n'
printf 'AUTHENTICATED_ACTOR_EVIDENCE=PASS\n'
printf 'STATE_DIRECTORY_MODE=700\n'
printf 'EVENT_AND_PACKET_MODE=600\n'
printf 'SYSTEMD_HARDENING=PRESERVED\n'
printf 'BASIC_AUTH=PRESERVED\n'
printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_HEAD=%s\n' "$SOURCE_HEAD"
printf 'BACKUP_DIR=%s\n' "$BACKUP"
printf 'PR_16=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_15=OPEN\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'
printf 'PHONE_ACCEPTANCE=REQUIRED\n'
printf 'NEXT_SAFE_STEP=PHONE_ANALYZE_RECORD_DECISION_REOPEN_AND_OBSERVE_OUTCOME\n'
