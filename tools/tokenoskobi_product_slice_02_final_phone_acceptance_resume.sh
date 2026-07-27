#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

ROOT='/root/tokenoskobi_clean_v1'
BASE_HEAD='d1d5078a7fb9bab7108755bf63806cb27f697007'
IMPLEMENTATION_SHORT='b82b734'
IMPLEMENTATION_MESSAGE='fix(product): correct target-token orientation and bounded transport'
FINAL_STATUS='PRODUCT_SLICE_02_CLOSED_VERIFIED_PHONE_ACCEPTED_GITHUB_SEALED'
NEXT_STEP='NEXT_WORK_UNIT_PLAN'
SERVICE='tokenoskobi-product-slice-02.service'

SERVER='tools/tokenoskobi_product_slice_02_server.py'
TEST='tests/test_product_slice_02.py'
UNIT='systemd_drafts/tokenoskobi-product-slice-02.service'
NGINX_REPO='config/nginx/panel.coinoskobi.xyz.conf'

SERVER_BLOB='fc5fbb485f54990959ba97b123bdd9da8db3ec09'
TEST_BLOB='73b185e0b83f0f9a18bd97803fd5515f6499dc7e'
UNIT_BLOB='c12f5c84b9b7d3b09c1c4a264993703869ee4c28'
NGINX_BLOB='141ddc4a4c5c2a526c5411a80a0d21ec51a70c7d'

CANONICAL_PATHS=(
  04_ALMANAC.md
  05_ATLAS.md
  06_PROJECT_MASTER_STATE.md
  07_PROJECT_HANDOFF.md
  PROJECT_HISTORY.json
  PROJECT_RUNTIME.json
  data/control/latest_tk_machine_state.json
  data/control/product_slice_02_machine_recovery_seal_v1.json
  data/control/product_slice_02_nginx_route_recovery_v1.json
  data/control/product_slice_02_single_token_decision_packet_v1.json
  data/control/product_slice_02_smoke_analysis_v1.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md
  reports/LATEST_TK_AI_HANDOFF.md
)

REPORT_PATHS=(
  reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md
  reports/LATEST_TK_AI_HANDOFF.md
)

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

report_failure() {
  local rc=$?

  trap - ERR INT TERM
  set +e

  printf '\n===== RESUME FAILURE STATE =====\n'
  printf 'FINAL_CLOSURE_RESUME=FAILED_OR_PENDING\n'
  printf 'FAILED_RC=%s\n' "$rc"
  printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD 2>/dev/null || true)"
  printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main 2>/dev/null || true)"

  printf '\n--- WORKTREE ---\n'
  git status --short --untracked-files=all 2>/dev/null || true

  printf '\n--- SERVICE ---\n'
  systemctl show "$SERVICE" \
    -p ActiveState \
    -p SubState \
    -p MainPID \
    -p NRestarts \
    --no-pager 2>/dev/null || true

  printf 'LOCAL_HEALTH_HTTP=%s\n' "$(
    http_code http://127.0.0.1:8096/healthz
  )"
  printf 'IMPLEMENTATION_COMMIT_PRESERVED=true\n'
  printf 'PAPER_TRADE=DISABLED\n'
  printf 'LIVE_TRADE=DISABLED\n'
  printf 'REAL_FINANCIAL_AUTHORITY=0\n'

  exit "$rc"
}

trap report_failure ERR INT TERM

[[ "${PRODUCT_SLICE_02_FINAL_RESUME_CONFIRM:-}" == 'YES' ]] ||
  fail CONFIRMATION_MISSING

exec 9>/run/tokenoskobi_product_slice_02_final_resume.lock
flock -n 9 || fail ANOTHER_FINAL_RESUME_IS_RUNNING

printf '\n===== 1 PARTIAL-CLOSURE PREFLIGHT =====\n'

[[ "$(git branch --show-current)" == 'main' ]] ||
  fail BRANCH_NOT_MAIN

[[ "$(git rev-parse --short=7 HEAD)" == "$IMPLEMENTATION_SHORT" ]] ||
  fail IMPLEMENTATION_HEAD_NOT_EXPECTED

[[ "$(git rev-parse HEAD^)" == "$BASE_HEAD" ]] ||
  fail IMPLEMENTATION_PARENT_NOT_BASE_HEAD

[[ "$(git log -1 --pretty=%s)" == "$IMPLEMENTATION_MESSAGE" ]] ||
  fail IMPLEMENTATION_COMMIT_MESSAGE_CHANGED

IMPLEMENTATION_HEAD="$(git rev-parse HEAD)"

[[ "$(git rev-parse "HEAD:$SERVER")" == "$SERVER_BLOB" ]] ||
  fail IMPLEMENTATION_SERVER_BLOB_CHANGED

[[ "$(git rev-parse "HEAD:$TEST")" == "$TEST_BLOB" ]] ||
  fail IMPLEMENTATION_TEST_BLOB_CHANGED

[[ "$(git rev-parse "HEAD:$UNIT")" == "$UNIT_BLOB" ]] ||
  fail IMPLEMENTATION_UNIT_BLOB_CHANGED

[[ "$(git rev-parse "HEAD:$NGINX_REPO")" == "$NGINX_BLOB" ]] ||
  fail IMPLEMENTATION_NGINX_BLOB_CHANGED

git fetch --quiet origin main

[[ "$(git rev-parse origin/main)" == "$BASE_HEAD" ]] ||
  fail ORIGIN_MAIN_MOVED_AFTER_IMPLEMENTATION_COMMIT

printf 'IMPLEMENTATION_HEAD=%s\n' "$IMPLEMENTATION_HEAD"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"

printf '\n===== 2 NORMALIZE PARTIAL INDEX =====\n'

git reset --quiet

ALLOWED_FILE="$(mktemp)"
ACTUAL_FILE="$(mktemp)"
trap 'rm -f "$ALLOWED_FILE" "$ACTUAL_FILE"' EXIT

printf '%s\n' "${CANONICAL_PATHS[@]}" | sort -u > "$ALLOWED_FILE"

{
  git diff --name-only HEAD
  git ls-files --others --exclude-standard
} | sort -u > "$ACTUAL_FILE"

EXTRA="$({ comm -13 "$ALLOWED_FILE" "$ACTUAL_FILE" || true; })"

if [[ -n "$EXTRA" ]]; then
  printf 'UNEXPECTED_CHANGED_PATHS_BEGIN\n%s\nUNEXPECTED_CHANGED_PATHS_END\n' "$EXTRA"
  fail PARTIAL_CLOSURE_SCOPE_CHANGED
fi

for path in "${CANONICAL_PATHS[@]}"; do
  [[ -f "$path" ]] || fail "CANONICAL_FILE_MISSING_${path}"
done

printf 'PARTIAL_CANONICAL_SCOPE=OK\n'

printf '\n===== 3 CANONICAL CONTENT VALIDATION =====\n'

JSON_FILES=(
  PROJECT_RUNTIME.json
  PROJECT_HISTORY.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
  data/control/product_slice_02_machine_recovery_seal_v1.json
  data/control/product_slice_02_nginx_route_recovery_v1.json
  data/control/product_slice_02_single_token_decision_packet_v1.json
  data/control/product_slice_02_smoke_analysis_v1.json
)

for file in "${JSON_FILES[@]}"; do
  python3 -m json.tool "$file" >/dev/null
done

FINAL_STATUS="$FINAL_STATUS" \
NEXT_STEP="$NEXT_STEP" \
python3 - <<'PY'
import json
import os
from pathlib import Path

final_status = os.environ["FINAL_STATUS"]
next_step = os.environ["NEXT_STEP"]

runtime = json.loads(Path("PROJECT_RUNTIME.json").read_text(encoding="utf-8"))
pointer = runtime["canonical_runtime_pointer"]

assert pointer["current_status"] == final_status
assert pointer["next_safe_step"] == next_step
closure = pointer["product_slice_02_phone_acceptance_closure"]
assert closure["status"] == final_status
assert closure["next_safe_step"] == next_step
assert closure["phone_acceptance"]["status"] == "AUTHENTICATED_USER_ACCEPTED_WBNB_AND_USDT"
assert closure["authority"]["paper_trade"] == "DISABLED"
assert closure["authority"]["live_trade"] == "DISABLED"
assert closure["authority"]["real_wallet_authority"] == 0
assert closure["authority"]["real_signing_authority"] == 0
assert closure["authority"]["real_order_authority"] == 0
assert closure["authority"]["real_trade_authority"] == 0

runtime_authority = runtime["authority"]
assert runtime_authority["live_trade"] == "DISABLED"
assert runtime_authority["real_wallet_authority"] == 0
assert runtime_authority["real_signing_authority"] == 0
assert runtime_authority["real_order_authority"] == 0
assert runtime_authority["real_trade_authority"] == 0

history = json.loads(Path("PROJECT_HISTORY.json").read_text(encoding="utf-8"))
event_id = "PRODUCT_SLICE_02_TARGET_ORIENTATION_PHONE_ACCEPTANCE_FINAL_CLOSURE_V1"
assert any(
    isinstance(event, dict) and event.get("event_id") == event_id
    for event in history["events"]
)

roadmap_text = Path("data/tokenoskobi_v1_v8_master_era_roadmap.json").read_text(encoding="utf-8")
assert final_status in roadmap_text
assert next_step in roadmap_text

machine = json.loads(Path("data/control/latest_tk_machine_state.json").read_text(encoding="utf-8"))
assert machine["product_slice_02_phone_acceptance_closure"]["status"] == final_status

seal = json.loads(Path("data/control/product_slice_02_machine_recovery_seal_v1.json").read_text(encoding="utf-8"))
assert seal["status"] == final_status
assert seal["phone_acceptance"] == "AUTHENTICATED_USER_ACCEPTED_WBNB_AND_USDT"
assert seal["unit_tests"] == "18/18_OK"
assert seal["next_safe_step"] == next_step

packet = json.loads(Path("data/control/product_slice_02_single_token_decision_packet_v1.json").read_text(encoding="utf-8"))
assert packet["status"] == final_status
assert set(packet["accepted_samples"]) == {"wbnb", "usdt"}
assert packet["authority"]["paper"] is False
assert packet["authority"]["live"] is False
assert packet["authority"]["wallet"] is False
assert packet["authority"]["signing"] is False
assert packet["authority"]["order"] is False
assert packet["authority"]["broadcast"] is False

print("CANONICAL_SEMANTIC_VALIDATION=OK")
PY

grep -Fq "$FINAL_STATUS" 04_ALMANAC.md
grep -Fq "$FINAL_STATUS" 06_PROJECT_MASTER_STATE.md
grep -Fq "$FINAL_STATUS" 07_PROJECT_HANDOFF.md
grep -Fq "$FINAL_STATUS" reports/LATEST_TK_AI_HANDOFF.md
grep -Fq "$FINAL_STATUS" reports/LATEST_PRODUCT_SLICE_02_SINGLE_TOKEN_DECISION_PACKET.md

! git diff -- PROJECT_BOOT.json | grep -q . ||
  fail PROJECT_BOOT_CHANGED_UNEXPECTEDLY

git diff --check
python3 -m py_compile "$SERVER" "$TEST"
python3 "$TEST"

printf 'CANONICAL_JSON_AND_SEMANTIC_VALIDATION=OK\n'
printf 'PROJECT_BOOT_UNCHANGED=OK\n'

printf '\n===== 4 RUNTIME AND SECURITY GATES =====\n'

systemctl is-active --quiet "$SERVICE" ||
  fail PRODUCT_SERVICE_NOT_ACTIVE

systemctl is-active --quiet nginx ||
  fail NGINX_NOT_ACTIVE

[[ "$(http_code http://127.0.0.1:8096/healthz)" == '200' ]] ||
  fail LOCAL_HEALTH_NOT_200

[[ "$(http_code https://panel.coinoskobi.xyz/panel/panel_v2/)" == '401' ]] ||
  fail EXTERNAL_PANEL_AUTH_GATE_CHANGED

[[ "$(http_code https://panel.coinoskobi.xyz/healthz)" == '200' ]] ||
  fail EXTERNAL_HEALTH_NOT_200

[[ "$(systemctl show "$SERVICE" -p ProtectSystem --value)" == 'strict' ]] ||
  fail PROTECT_SYSTEM_NOT_STRICT

[[ "$(systemctl show "$SERVICE" -p PrivateTmp --value)" == 'yes' ]] ||
  fail PRIVATE_TMP_NOT_ENABLED

printf 'RUNTIME_AND_SECURITY_GATES=OK\n'

printf '\n===== 5 FORCE-STAGE CANONICAL CLOSURE =====\n'

NON_REPORT_PATHS=()
for path in "${CANONICAL_PATHS[@]}"; do
  case "$path" in
    reports/*) ;;
    *) NON_REPORT_PATHS+=("$path") ;;
  esac
done

git add -- "${NON_REPORT_PATHS[@]}"
git add -f -- "${REPORT_PATHS[@]}"

EXPECTED_STAGED="$(printf '%s\n' "${CANONICAL_PATHS[@]}" | sort -u)"
ACTUAL_STAGED="$(git diff --cached --name-only | sort -u)"

printf '%s\n' "$ACTUAL_STAGED"

[[ "$ACTUAL_STAGED" == "$EXPECTED_STAGED" ]] ||
  fail CANONICAL_STAGED_SCOPE_CHANGED

git diff --cached --check

printf 'CANONICAL_STAGED_SCOPE=OK\n'

printf '\n===== 6 CANONICAL COMMIT =====\n'

git commit -m 'chore(canonical): close Product Slice 02 phone acceptance'
FINAL_HEAD="$(git rev-parse HEAD)"

[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] ||
  fail WORKTREE_NOT_CLEAN_AFTER_CANONICAL_COMMIT

printf 'FINAL_LOCAL_HEAD=%s\n' "$FINAL_HEAD"
git log --oneline -2

printf '\n===== 7 SINGLE PUSH =====\n'

git fetch --quiet origin main

[[ "$(git rev-parse origin/main)" == "$BASE_HEAD" ]] ||
  fail ORIGIN_MAIN_MOVED_BEFORE_PUSH

git push origin HEAD:main

printf '\n===== 8 REMOTE VERIFICATION =====\n'

git fetch --quiet origin main
REMOTE_HEAD="$(git rev-parse origin/main)"

[[ "$REMOTE_HEAD" == "$FINAL_HEAD" ]] ||
  fail REMOTE_HEAD_MISMATCH

[[ "$(git rev-parse "origin/main:$SERVER")" == "$SERVER_BLOB" ]] ||
  fail REMOTE_SERVER_BLOB_CHANGED

[[ "$(git rev-parse "origin/main:$TEST")" == "$TEST_BLOB" ]] ||
  fail REMOTE_TEST_BLOB_CHANGED

[[ "$(git rev-parse "origin/main:$UNIT")" == "$UNIT_BLOB" ]] ||
  fail REMOTE_UNIT_BLOB_CHANGED

[[ "$(git rev-parse "origin/main:$NGINX_REPO")" == "$NGINX_BLOB" ]] ||
  fail REMOTE_NGINX_BLOB_CHANGED

git show origin/main:PROJECT_RUNTIME.json |
  FINAL_STATUS="$FINAL_STATUS" \
  NEXT_STEP="$NEXT_STEP" \
  python3 -c '
import json
import os
import sys

runtime = json.load(sys.stdin)
pointer = runtime["canonical_runtime_pointer"]
assert pointer["current_status"] == os.environ["FINAL_STATUS"]
assert pointer["next_safe_step"] == os.environ["NEXT_STEP"]
closure = pointer["product_slice_02_phone_acceptance_closure"]
assert closure["status"] == os.environ["FINAL_STATUS"]
assert closure["authority"]["live_trade"] == "DISABLED"
assert closure["authority"]["real_trade_authority"] == 0
print("REMOTE_CANONICAL_RUNTIME=OK")
'

[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] ||
  fail FINAL_WORKTREE_NOT_CLEAN

[[ "$(http_code http://127.0.0.1:8096/healthz)" == '200' ]] ||
  fail FINAL_LOCAL_HEALTH_NOT_200

trap - ERR INT TERM
rm -f "$ALLOWED_FILE" "$ACTUAL_FILE"
trap - EXIT

printf '\n===== FINAL CLOSURE =====\n'
printf 'PRODUCT_SLICE_02_FINAL_CLOSURE=SUCCESS\n'
printf 'IMPLEMENTATION_HEAD=%s\n' "$IMPLEMENTATION_HEAD"
printf 'FINAL_LOCAL_HEAD=%s\n' "$FINAL_HEAD"
printf 'FINAL_REMOTE_HEAD=%s\n' "$REMOTE_HEAD"
printf 'SINGLE_PUSH=VERIFIED\n'
printf 'WORKTREE_CLEAN=true\n'
printf 'PHONE_WBNB_ACCEPTANCE=VERIFIED\n'
printf 'PHONE_USDT_ACCEPTANCE=VERIFIED\n'
printf 'TARGET_TOKEN_ORIENTATION=VERIFIED\n'
printf 'PR_14=OPEN_PENDING_ASSISTANT_CLOSURE\n'
printf 'ISSUE_12=OPEN_PENDING_ASSISTANT_CLOSURE\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'
printf 'NEXT_SAFE_STEP=%s\n' "$NEXT_STEP"
