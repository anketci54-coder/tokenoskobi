#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

BASE_HEAD='d1d5078a7fb9bab7108755bf63806cb27f697007'
IMPLEMENTATION_HEAD='b82b734aab6f385db3b6551d6ef5ce5c6435ef7c'
IMPLEMENTATION_MESSAGE='fix(product): correct target-token orientation and bounded transport'
FINAL_STATUS='PRODUCT_SLICE_02_CLOSED_VERIFIED_PHONE_ACCEPTED_GITHUB_SEALED'
NEXT_STEP='NEXT_WORK_UNIT_PLAN'
SERVICE='tokenoskobi-product-slice-02.service'

CANONICAL_PATHS=(
  04_ALMANAC.md
  06_PROJECT_MASTER_STATE.md
  07_PROJECT_HANDOFF.md
  PROJECT_HISTORY.json
  PROJECT_RUNTIME.json
  data/control/latest_tk_machine_state.json
  data/control/product_slice_02_machine_recovery_seal_v1.json
  data/control/product_slice_02_single_token_decision_packet_v1.json
  data/control/product_slice_02_smoke_analysis_v1.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  reports/LATEST_TK_AI_HANDOFF.md
)

EXPECTED_STATUS=$' M 04_ALMANAC.md\n M 06_PROJECT_MASTER_STATE.md\n M 07_PROJECT_HANDOFF.md\n M PROJECT_HISTORY.json\n M PROJECT_RUNTIME.json\n M data/control/latest_tk_machine_state.json\n M data/control/product_slice_02_machine_recovery_seal_v1.json\n M data/control/product_slice_02_single_token_decision_packet_v1.json\n M data/control/product_slice_02_smoke_analysis_v1.json\n M data/tokenoskobi_v1_v8_master_era_roadmap.json\n M reports/LATEST_TK_AI_HANDOFF.md'

fail(){ printf 'BLOCKED=%s\n' "$1" >&2; return 1; }
http_code(){ curl -sS --connect-timeout 5 --max-time 25 -o /dev/null -w '%{http_code}' "$1" 2>/dev/null || true; }

report_failure(){
  rc=$?
  trap - ERR INT TERM
  set +e
  printf '\n===== RESUME2 FAILURE STATE =====\n'
  printf 'FINAL_CLOSURE_RESUME2=FAILED_OR_PENDING\n'
  printf 'FAILED_RC=%s\n' "$rc"
  printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD 2>/dev/null || true)"
  printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main 2>/dev/null || true)"
  printf '\n--- WORKTREE ---\n'
  git status --short --untracked-files=all 2>/dev/null || true
  printf '\n--- SERVICE ---\n'
  systemctl show "$SERVICE" -p ActiveState -p SubState -p MainPID -p NRestarts --no-pager 2>/dev/null || true
  printf 'LOCAL_HEALTH_HTTP=%s\n' "$(http_code http://127.0.0.1:8096/healthz)"
  printf 'IMPLEMENTATION_COMMIT_PRESERVED=true\n'
  printf 'PAPER_TRADE=DISABLED\n'
  printf 'LIVE_TRADE=DISABLED\n'
  printf 'REAL_FINANCIAL_AUTHORITY=0\n'
  exit "$rc"
}
trap report_failure ERR INT TERM

[[ "${PRODUCT_SLICE_02_FINAL_RESUME2_CONFIRM:-}" == 'YES' ]] || fail CONFIRMATION_MISSING

exec 9>/run/tokenoskobi_product_slice_02_final_resume2.lock
flock -n 9 || fail ANOTHER_FINAL_RESUME_IS_RUNNING

printf '\n===== 1 EXACT PARTIAL-CLOSURE PREFLIGHT =====\n'
[[ "$(git branch --show-current)" == 'main' ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$IMPLEMENTATION_HEAD" ]] || fail IMPLEMENTATION_HEAD_NOT_EXPECTED
[[ "$(git rev-parse HEAD^)" == "$BASE_HEAD" ]] || fail IMPLEMENTATION_PARENT_NOT_BASE
[[ "$(git log -1 --pretty=%s)" == "$IMPLEMENTATION_MESSAGE" ]] || fail IMPLEMENTATION_MESSAGE_CHANGED

git fetch --quiet origin main
[[ "$(git rev-parse origin/main)" == "$BASE_HEAD" ]] || fail ORIGIN_MAIN_MOVED

git reset --quiet
ACTUAL_STATUS="$(git status --short --untracked-files=all)"
printf '%s\n' "$ACTUAL_STATUS"
[[ "$ACTUAL_STATUS" == "$EXPECTED_STATUS" ]] || fail PARTIAL_CANONICAL_SCOPE_CHANGED

for path in "${CANONICAL_PATHS[@]}"; do
  [[ -f "$path" ]] || fail "CANONICAL_FILE_MISSING_${path}"
done

printf 'IMPLEMENTATION_HEAD=%s\n' "$IMPLEMENTATION_HEAD"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'PARTIAL_CANONICAL_SCOPE=OK\n'

printf '\n===== 2 JSON AND SEMANTIC VALIDATION =====\n'
JSON_FILES=(
  PROJECT_RUNTIME.json
  PROJECT_HISTORY.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
  data/control/product_slice_02_machine_recovery_seal_v1.json
  data/control/product_slice_02_single_token_decision_packet_v1.json
  data/control/product_slice_02_smoke_analysis_v1.json
)
for file in "${JSON_FILES[@]}"; do python3 -m json.tool "$file" >/dev/null; done

FINAL_STATUS="$FINAL_STATUS" NEXT_STEP="$NEXT_STEP" python3 - <<'PY'
import json, os
from pathlib import Path

status=os.environ['FINAL_STATUS']; nxt=os.environ['NEXT_STEP']
def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))

runtime=load('PROJECT_RUNTIME.json')
pointer=runtime['canonical_runtime_pointer']
assert pointer['current_status']==status
assert pointer['next_safe_step']==nxt
closure=pointer['product_slice_02_phone_acceptance_closure']
assert closure['status']==status and closure['next_safe_step']==nxt
phone=closure['phone_acceptance']
assert set(phone)=={'wbnb','usdt'}
assert phone['wbnb']['decision']=='ALLOW' and phone['wbnb']['data_quality']=='SUFFICIENT'
assert phone['usdt']['decision']=='ALLOW' and phone['usdt']['data_quality']=='SUFFICIENT'
assert closure['paper_trade']=='DISABLED'
assert closure['live_trade']=='DISABLED'
assert closure['real_financial_authority']==0

auth=runtime['authority']
assert auth['live_trade']=='DISABLED'
for key in ('real_wallet_authority','real_signing_authority','real_order_authority','real_trade_authority'):
    assert auth[key]==0

history=load('PROJECT_HISTORY.json')
assert any(isinstance(e,dict) and e.get('event_id')=='PRODUCT_SLICE_02_PHONE_ACCEPTANCE_FINAL_CLOSURE_V1' for e in history['events'])

roadmap=Path('data/tokenoskobi_v1_v8_master_era_roadmap.json').read_text(encoding='utf-8')
assert status in roadmap and nxt in roadmap

machine=load('data/control/latest_tk_machine_state.json')
mc=machine['product_slice_02_phone_acceptance_closure']
assert mc['status']==status and mc['next_safe_step']==nxt
assert set(mc['phone_acceptance'])=={'wbnb','usdt'}

seal=load('data/control/product_slice_02_machine_recovery_seal_v1.json')
assert seal['status']==status
assert seal['phone_acceptance']=='AUTHENTICATED_USER_ACCEPTED_WBNB_AND_USDT'
assert seal['unit_tests']=='18/18_OK'
assert seal['next_safe_step']==nxt

packet=load('data/control/product_slice_02_single_token_decision_packet_v1.json')
assert packet['status']==status
assert set(packet['accepted_samples'])=={'wbnb','usdt'}
for key in ('paper','live','wallet','signing','order','broadcast'):
    assert packet['authority'][key] is False
assert packet['authority']['human_action_required'] is True

smoke=load('data/control/product_slice_02_smoke_analysis_v1.json')
assert smoke['token_address']=='0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'
assert smoke['market']['target_orientation_verified'] is True
assert smoke['decision']['data_quality']=='SUFFICIENT'
print('CANONICAL_SEMANTIC_VALIDATION=OK')
PY

grep -Fq "$FINAL_STATUS" 04_ALMANAC.md
grep -Fq "$FINAL_STATUS" 06_PROJECT_MASTER_STATE.md
grep -Fq "$FINAL_STATUS" 07_PROJECT_HANDOFF.md
grep -Fq "$FINAL_STATUS" reports/LATEST_TK_AI_HANDOFF.md
! git diff -- PROJECT_BOOT.json | grep -q . || fail PROJECT_BOOT_CHANGED_UNEXPECTEDLY

git diff --check
python3 -m py_compile tools/tokenoskobi_product_slice_02_server.py tests/test_product_slice_02.py
python3 tests/test_product_slice_02.py
systemctl is-active --quiet "$SERVICE" || fail SERVICE_NOT_ACTIVE
[[ "$(http_code http://127.0.0.1:8096/healthz)" == '200' ]] || fail LOCAL_HEALTH_NOT_200
[[ "$(http_code https://panel.coinoskobi.xyz/panel/panel_v2/)" == '401' ]] || fail PANEL_AUTH_GATE_CHANGED
[[ "$(http_code https://panel.coinoskobi.xyz/healthz)" == '200' ]] || fail EXTERNAL_HEALTH_CHANGED
printf 'RUNTIME_AND_SERVICE_VALIDATION=OK\n'

printf '\n===== 3 STAGE EXACT CANONICAL SCOPE =====\n'
git add -- \
  04_ALMANAC.md \
  06_PROJECT_MASTER_STATE.md \
  07_PROJECT_HANDOFF.md \
  PROJECT_HISTORY.json \
  PROJECT_RUNTIME.json \
  data/control/latest_tk_machine_state.json \
  data/control/product_slice_02_machine_recovery_seal_v1.json \
  data/control/product_slice_02_single_token_decision_packet_v1.json \
  data/control/product_slice_02_smoke_analysis_v1.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json

git add -f -- reports/LATEST_TK_AI_HANDOFF.md

EXPECTED_STAGED="$(printf '%s\n' "${CANONICAL_PATHS[@]}" | sort)"
ACTUAL_STAGED="$(git diff --cached --name-only | sort)"
printf '%s\n' "$ACTUAL_STAGED"
[[ "$ACTUAL_STAGED" == "$EXPECTED_STAGED" ]] || fail CANONICAL_STAGED_SCOPE_CHANGED
git diff --cached --check

printf '\n===== 4 CANONICAL COMMIT =====\n'
git commit -m 'chore(canonical): close Product Slice 02 phone acceptance'
FINAL_HEAD="$(git rev-parse HEAD)"
printf 'FINAL_LOCAL_HEAD=%s\n' "$FINAL_HEAD"
[[ "$(git rev-parse HEAD^)" == "$IMPLEMENTATION_HEAD" ]] || fail CANONICAL_PARENT_CHANGED
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail WORKTREE_NOT_CLEAN_BEFORE_PUSH

printf '\n===== 5 SINGLE PUSH AND REMOTE VERIFY =====\n'
git fetch --quiet origin main
[[ "$(git rev-parse origin/main)" == "$BASE_HEAD" ]] || fail ORIGIN_MAIN_MOVED_BEFORE_PUSH
git push origin HEAD:main
git fetch --quiet origin main
REMOTE_HEAD="$(git rev-parse origin/main)"
[[ "$REMOTE_HEAD" == "$FINAL_HEAD" ]] || fail REMOTE_HEAD_MISMATCH

git show origin/main:PROJECT_RUNTIME.json | FINAL_STATUS="$FINAL_STATUS" NEXT_STEP="$NEXT_STEP" python3 -c '
import json,os,sys
r=json.load(sys.stdin); p=r["canonical_runtime_pointer"]
assert p["current_status"]==os.environ["FINAL_STATUS"]
assert p["next_safe_step"]==os.environ["NEXT_STEP"]
c=p["product_slice_02_phone_acceptance_closure"]
assert c["status"]==os.environ["FINAL_STATUS"]
assert set(c["phone_acceptance"])=={"wbnb","usdt"}
assert c["live_trade"]=="DISABLED" and c["real_financial_authority"]==0
print("REMOTE_CANONICAL_RUNTIME=OK")
'

[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail FINAL_WORKTREE_NOT_CLEAN
[[ "$(http_code http://127.0.0.1:8096/healthz)" == '200' ]] || fail FINAL_LOCAL_HEALTH_NOT_200

trap - ERR INT TERM
printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_02_FINAL_CLOSURE=SUCCESS\n'
printf 'IMPLEMENTATION_HEAD=%s\n' "$IMPLEMENTATION_HEAD"
printf 'FINAL_LOCAL_HEAD=%s\n' "$FINAL_HEAD"
printf 'FINAL_REMOTE_HEAD=%s\n' "$REMOTE_HEAD"
printf 'SINGLE_PUSH=VERIFIED\n'
printf 'WORKTREE_CLEAN=true\n'
printf 'PHONE_WBNB_ACCEPTANCE=VERIFIED\n'
printf 'PHONE_USDT_ACCEPTANCE=VERIFIED\n'
printf 'PROJECT_BOOT_UPDATED=false\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'
printf 'NEXT_SAFE_STEP=%s\n' "$NEXT_STEP"
