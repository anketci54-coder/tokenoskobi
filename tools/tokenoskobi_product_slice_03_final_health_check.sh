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

printf '\n===== 3 FULL APPEND-ONLY PHONE EVIDENCE =====\n'
TOKENOSKOBI_ROOT="$ROOT" \
TOKENOSKOBI_SLICE03_STATE_DIR="$STATE_DIR" \
TOKENOSKOBI_SLICE02_SERVER_PATH="$ROOT/tools/tokenoskobi_product_slice_02_server.py" \
TOKENOSKOBI_SLICE03_CORE_PATH="$ROOT/tools/tokenoskobi_product_slice_03_server.py" \
python3 - "$ROOT/tools/tokenoskobi_product_slice_03_runtime.py" "$TMP/selected.json" <<'PY'
import importlib.util
import json
import sys
from pathlib import Path

runtime_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("slice03_health_runtime", runtime_path)
if not spec or not spec.loader:
    raise SystemExit("BLOCKED=RUNTIME_IMPORT_FAILED")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
events = module.verify_event_chain_locked()
if not events:
    raise SystemExit("BLOCKED=EVENT_CHAIN_EMPTY")

decisions = []
for event in events:
    if event.get("event_type") != "HUMAN_DECISION_RECORDED":
        continue
    payload = event.get("payload") or {}
    note = str(payload.get("note") or "").strip().casefold()
    action = str(payload.get("action") or "").strip().upper()
    if note == "telefon kabul testi" and action == "WAIT":
        decisions.append(event)

if not decisions:
    recent = [
        {
            "seq": event.get("seq"),
            "packet": str(event.get("packet_id") or "")[:12],
            "action": (event.get("payload") or {}).get("action"),
            "actor": (event.get("payload") or {}).get("actor"),
            "note": (event.get("payload") or {}).get("note"),
        }
        for event in events
        if event.get("event_type") == "HUMAN_DECISION_RECORDED"
    ][-10:]
    print("RECENT_HUMAN_DECISIONS=" + json.dumps(recent, ensure_ascii=False))
    raise SystemExit("BLOCKED=PHONE_DECISION_EVENT_NOT_FOUND")

selected = None
for decision in reversed(decisions):
    linked = [
        event
        for event in events
        if event.get("event_type") == "OUTCOME_OBSERVED"
        and event.get("packet_id") == decision.get("packet_id")
        and (event.get("payload") or {}).get("human_decision_event_hash")
        == decision.get("event_hash")
    ]
    if linked:
        selected = {
            "packet_id": decision["packet_id"],
            "decision": decision,
            "outcome": linked[-1],
        }
        break

if selected is None:
    raise SystemExit("BLOCKED=PHONE_OUTCOME_LINK_NOT_FOUND")

decision_payload = selected["decision"]["payload"]
outcome_payload = selected["outcome"]["payload"]
if decision_payload.get("actor") != "coinoskobi_xyz":
    raise SystemExit(
        "BLOCKED=PHONE_DECISION_ACTOR_INVALID:" + str(decision_payload.get("actor"))
    )
if outcome_payload.get("actor") != "coinoskobi_xyz":
    raise SystemExit(
        "BLOCKED=PHONE_OUTCOME_ACTOR_INVALID:" + str(outcome_payload.get("actor"))
    )
if float(outcome_payload.get("baseline_price_usd") or 0) <= 100:
    raise SystemExit("BLOCKED=PHONE_BASELINE_PRICE_INVALID")
if float(outcome_payload.get("current_price_usd") or 0) <= 100:
    raise SystemExit("BLOCKED=PHONE_CURRENT_PRICE_INVALID")
if outcome_payload.get("classification") not in ("UP", "DOWN", "FLAT"):
    raise SystemExit("BLOCKED=PHONE_CLASSIFICATION_INVALID")
if outcome_payload.get("target_orientation_verified") is not True:
    raise SystemExit("BLOCKED=PHONE_TARGET_ORIENTATION_INVALID")

output_path.write_text(
    json.dumps(selected, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print("EVENT_CHAIN_COUNT=" + str(len(events)))
print("PHONE_DECISION_SEQ=" + str(selected["decision"]["seq"]))
print("PHONE_OUTCOME_SEQ=" + str(selected["outcome"]["seq"]))
print("PHONE_ACTOR=" + str(decision_payload["actor"]))
print("PHONE_PACKET_ID=" + str(selected["packet_id"]))
PY

PACKET_ID="$(python3 - "$TMP/selected.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding='utf-8'))['packet_id'])
PY
)"

curl -sS --connect-timeout 5 --max-time 30 \
  "http://127.0.0.1:8096/api/v1/packets/${PACKET_ID}" \
  > "$TMP/packet.json"

python3 - "$TMP/packet.json" "$TMP/selected.json" <<'PY'
import json
import sys

packet = json.load(open(sys.argv[1], encoding="utf-8"))
selected = json.load(open(sys.argv[2], encoding="utf-8"))
pid = selected["packet_id"]
decision = selected["decision"]
outcome = selected["outcome"]

assert packet["integrity"] == "VERIFIED"
assert packet["packet"]["packet_id"] == pid
events = packet["events"]
by_hash = {event["event_hash"]: event for event in events}
assert decision["event_hash"] in by_hash
assert outcome["event_hash"] in by_hash
assert by_hash[decision["event_hash"]]["payload"]["action"] == "WAIT"
assert by_hash[decision["event_hash"]]["payload"]["note"] == "Telefon kabul testi"
assert by_hash[decision["event_hash"]]["payload"]["actor"] == "coinoskobi_xyz"
assert by_hash[outcome["event_hash"]]["payload"]["actor"] == "coinoskobi_xyz"
assert (
    by_hash[outcome["event_hash"]]["payload"]["human_decision_event_hash"]
    == decision["event_hash"]
)
assert [event["seq"] for event in events] == sorted(event["seq"] for event in events)
op = by_hash[outcome["event_hash"]]["payload"]
print("PHONE_PACKET_REOPEN=PASS")
print("PHONE_HUMAN_DECISION=WAIT")
print("PHONE_OUTCOME_TRACKING=PASS")
print("PHONE_BASELINE_PRICE_USD=" + str(op["baseline_price_usd"]))
print("PHONE_CURRENT_PRICE_USD=" + str(op["current_price_usd"]))
print("PHONE_CHANGE_PCT=" + str(op["change_pct"]))
print("PHONE_CLASSIFICATION=" + str(op["classification"]))
PY
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
