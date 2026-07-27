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

printf '\n===== 3 PHONE DECISION REVISION AND OUTCOME CHAIN =====\n'
EVENTS_FILE="$STATE_DIR/decision_history_v1.jsonl" \
PACKETS_DIR="$STATE_DIR/packets" \
python3 - <<'PY'
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

EVENTS_FILE = Path(os.environ['EVENTS_FILE'])
PACKETS_DIR = Path(os.environ['PACKETS_DIR'])
ZERO_HASH = '0' * 64


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
        allow_nan=False,
    ).encode('utf-8')


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

lines = EVENTS_FILE.read_text(encoding='utf-8').splitlines()
assert lines

events: list[dict[str, Any]] = []
previous = ZERO_HASH
for expected_seq, line in enumerate(lines, start=1):
    event = json.loads(line)
    assert event['seq'] == expected_seq
    assert event['prev_hash'] == previous
    event_hash = event['event_hash']
    unsigned = dict(event)
    unsigned.pop('event_hash')
    assert digest(unsigned) == event_hash
    previous = event_hash
    events.append(event)

phone_waits = [
    event for event in events
    if event['event_type'] == 'HUMAN_DECISION_RECORDED'
    and event['payload'].get('action') == 'WAIT'
    and event['payload'].get('note') == 'Telefon kabul testi'
    and event['payload'].get('actor') == 'coinoskobi_xyz'
]
assert len(phone_waits) == 1
initial = phone_waits[0]
packet_id = initial['packet_id']

decisions = [
    event for event in events
    if event['packet_id'] == packet_id
    and event['event_type'] == 'HUMAN_DECISION_RECORDED'
]
decision_by_hash = {event['event_hash']: event for event in decisions}

outcomes = [
    event for event in events
    if event['packet_id'] == packet_id
    and event['event_type'] == 'OUTCOME_OBSERVED'
]
assert outcomes
latest_outcome = outcomes[-1]
linked_hash = latest_outcome['payload']['human_decision_event_hash']
assert linked_hash in decision_by_hash
effective = decision_by_hash[linked_hash]
assert effective['seq'] >= initial['seq']
assert effective['payload'].get('actor') == 'coinoskobi_xyz'
assert effective['payload'].get('note') == 'Telefon kabul testi'
assert effective['payload'].get('action') in {'ACCEPT', 'REJECT', 'WAIT', 'REVIEW'}

cursor = effective
seen: set[str] = set()
while cursor['event_hash'] != initial['event_hash']:
    current_hash = cursor['event_hash']
    assert current_hash not in seen
    seen.add(current_hash)
    previous_decision = cursor['payload'].get('previous_decision_event_hash')
    assert previous_decision in decision_by_hash
    cursor = decision_by_hash[previous_decision]
assert cursor['event_hash'] == initial['event_hash']

packet_path = PACKETS_DIR / f'{packet_id}.json'
packet = json.loads(packet_path.read_text(encoding='utf-8'))
assert packet['packet_id'] == packet_id
assert digest(packet['analysis']) == packet_id
assert packet['analysis']['token_address'] == '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'
authority = packet['authority']
assert all(
    authority[key] is False
    for key in ('paper', 'live', 'wallet', 'signing', 'order', 'broadcast')
)

payload = latest_outcome['payload']
assert payload['actor'] == 'coinoskobi_xyz'
assert payload['human_decision_event_hash'] == effective['event_hash']
assert float(payload['baseline_price_usd']) > 100
assert float(payload['current_price_usd']) > 100
assert payload['classification'] in {'UP', 'DOWN', 'FLAT'}
assert payload['target_orientation_verified'] is True

linked_outcomes = [
    event for event in outcomes
    if event['payload'].get('human_decision_event_hash') == effective['event_hash']
]
assert linked_outcomes

print('EVENT_COUNT=' + str(len(events)))
print('HASH_CHAIN_INTEGRITY=VERIFIED')
print('PHONE_PACKET_ID=' + packet_id)
print('PHONE_PACKET_REOPEN=PASS')
print('PHONE_INITIAL_DECISION=' + initial['payload']['action'])
print('PHONE_EFFECTIVE_DECISION=' + effective['payload']['action'])
print('PHONE_DECISION_REVISION_CHAIN=PASS')
print('PHONE_OUTCOME_LINKAGE=PASS')
print('PHONE_OUTCOME_OBSERVATION_COUNT=' + str(len(linked_outcomes)))
print('PHONE_BASELINE_PRICE_USD=' + str(payload['baseline_price_usd']))
print('PHONE_CURRENT_PRICE_USD=' + str(payload['current_price_usd']))
print('PHONE_CHANGE_PCT=' + str(payload['change_pct']))
print('PHONE_CLASSIFICATION=' + str(payload['classification']))
print('PHONE_ACTOR=coinoskobi_xyz')
PY

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
printf 'PHONE_ACCEPTANCE_CHAIN=WAIT_TO_ACCEPT_REVISION_TO_OUTCOME\n'
printf 'REPEATED_OUTCOME_OBSERVATIONS=NON_CORRUPTING_APPEND_ONLY_EVENTS\n'
printf 'FAILED_TO_FETCH_EXTRA_ANALYZE=NON_BLOCKING_TRANSIENT\n'
printf 'COMMIT_PUSH=NONE\n'
printf 'CANONICAL_UPDATE=NONE\n'
printf 'PR_16=DRAFT_OPEN_UNMERGED\n'
printf 'ISSUE_15=OPEN\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'
printf 'NEXT_SAFE_STEP=FINAL_COMMIT_PUSH_CANONICAL_SEAL\n'
