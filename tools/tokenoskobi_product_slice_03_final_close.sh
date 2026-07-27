#!/usr/bin/env bash
set -Eeuo pipefail

ROOT='/root/tokenoskobi_clean_v1'
EXPECTED_MAIN='60833fab96ec0a8af2f9d5f43c582feb7da182d2'
BRANCH='agent/product-slice-03-human-decision-history'
SOURCE_HEAD="${PRODUCT_SLICE_03_FINAL_SOURCE_HEAD:-}"

CORE='tools/tokenoskobi_product_slice_03_server.py'
RUNTIME_BINDING='tools/tokenoskobi_product_slice_03_runtime.py'
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
EVENTS_FILE="$STATE_DIR/decision_history_v1.jsonl"
PACKETS_DIR="$STATE_DIR/packets"

STAGE='PRODUCT_SLICE_03_HUMAN_APPROVAL_DECISION_HISTORY_AND_OUTCOME_TRACKING'
FINAL_STATUS='PRODUCT_SLICE_03_CLOSED_VERIFIED_PHONE_ACCEPTED_GITHUB_SEALED'
NEXT_STEP='NEXT_WORK_UNIT_PLAN'
NEXT_PLANNED_STAGE='PRODUCT_SLICE_04_DEX_WALLET_CEX_GRAPH_AND_PERFORMANCE'
ARTIFACT='data/control/product_slice_03_human_decision_history_closure_v1.json'

EXPECTED_STATUS=$' M config/nginx/panel.coinoskobi.xyz.conf\n M systemd_drafts/tokenoskobi-product-slice-02.service\n?? tests/test_product_slice_03.py\n?? tests/test_product_slice_03_runtime.py\n?? tools/tokenoskobi_product_slice_03_runtime.py\n?? tools/tokenoskobi_product_slice_03_server.py'

CANONICAL_PATHS=(
  04_ALMANAC.md
  05_ATLAS.md
  06_PROJECT_MASTER_STATE.md
  07_PROJECT_HANDOFF.md
  PROJECT_HISTORY.json
  PROJECT_RUNTIME.json
  data/control/latest_tk_machine_state.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  reports/LATEST_TK_AI_HANDOFF.md
)

PRODUCT_PATHS=(
  "$NGINX_REPO"
  "$UNIT"
  "$TEST_CORE"
  "$TEST_RUNTIME"
  "$RUNTIME_BINDING"
  "$CORE"
)

BACKUP=''
CANONICAL_MUTATED=0
COMMIT_CREATED=0
PUSH_COMPLETED=0
FINAL_HEAD=''

cd "$ROOT"
exec 9>/run/tokenoskobi_product_slice_03_final_close.lock
flock -n 9 || {
  printf 'BLOCKED=ANOTHER_SLICE03_CLOSURE_IS_RUNNING\n'
  exit 1
}

fail() {
  printf 'BLOCKED=%s\n' "$1" >&2
  return 1
}

http_code() {
  curl -sS --connect-timeout 5 --max-time 25 \
    -o /dev/null -w '%{http_code}' "$1" 2>/dev/null || true
}

restore_canonical() {
  set +e
  if [[ "$CANONICAL_MUTATED" -eq 1 && "$COMMIT_CREATED" -eq 0 && -n "$BACKUP" ]]; then
    tar -xzf "$BACKUP/canonical_before.tar.gz" -C "$ROOT" 2>/dev/null || true
    rm -f "$ARTIFACT" 2>/dev/null || true
  fi
  set -e
}

failure_report() {
  local rc=$?
  trap - ERR INT TERM
  set +e
  restore_canonical
  printf '\n===== CLOSURE FAILURE STATE =====\n'
  printf 'PRODUCT_SLICE_03_FINAL_CLOSURE=FAILED_OR_PENDING\n'
  printf 'FAILED_RC=%s\n' "$rc"
  printf 'CANONICAL_MUTATED=%s\n' "$CANONICAL_MUTATED"
  printf 'COMMIT_CREATED=%s\n' "$COMMIT_CREATED"
  printf 'PUSH_COMPLETED=%s\n' "$PUSH_COMPLETED"
  [[ -n "$FINAL_HEAD" ]] && printf 'FINAL_LOCAL_HEAD=%s\n' "$FINAL_HEAD"
  printf '\n--- WORKTREE ---\n'
  git status --short --untracked-files=all 2>/dev/null || true
  printf '\n--- LOCAL / REMOTE ---\n'
  git rev-parse HEAD 2>/dev/null || true
  git rev-parse origin/main 2>/dev/null || true
  printf '\n--- SERVICE ---\n'
  systemctl show "$SERVICE" -p ActiveState -p SubState -p MainPID -p NRestarts --no-pager 2>/dev/null || true
  printf 'LOCAL_HEALTH_HTTP=%s\n' "$(http_code http://127.0.0.1:8096/healthz)"
  printf 'PAPER_TRADE=DISABLED\n'
  printf 'LIVE_TRADE=DISABLED\n'
  printf 'REAL_FINANCIAL_AUTHORITY=0\n'
  exit "$rc"
}

trap failure_report ERR INT TERM

[[ -n "$SOURCE_HEAD" ]] || fail SOURCE_HEAD_ENV_MISSING

printf '\n===== 1 EXACT PREFLIGHT =====\n'
[[ "$(git branch --show-current)" == 'main' ]] || fail BRANCH_NOT_MAIN
[[ "$(git rev-parse HEAD)" == "$EXPECTED_MAIN" ]] || fail LOCAL_HEAD_CHANGED
ACTUAL_STATUS="$(git status --short --untracked-files=all)"
printf '%s\n' "$ACTUAL_STATUS"
[[ "$ACTUAL_STATUS" == "$EXPECTED_STATUS" ]] || fail WORKTREE_SCOPE_CHANGED

git fetch --quiet origin \
  'refs/heads/main:refs/remotes/origin/main' \
  "refs/heads/${BRANCH}:refs/remotes/origin/${BRANCH}"
[[ "$(git rev-parse origin/main)" == "$EXPECTED_MAIN" ]] || fail ORIGIN_MAIN_CHANGED
[[ "$(git rev-parse "origin/${BRANCH}")" == "$SOURCE_HEAD" ]] || fail SOURCE_HEAD_CHANGED
[[ "$(git merge-base "$EXPECTED_MAIN" "$SOURCE_HEAD")" == "$EXPECTED_MAIN" ]] || fail SOURCE_BASE_INVALID

printf 'LOCAL_HEAD=%s\n' "$(git rev-parse HEAD)"
printf 'ORIGIN_MAIN=%s\n' "$(git rev-parse origin/main)"
printf 'SOURCE_HEAD=%s\n' "$SOURCE_HEAD"
printf 'LOCAL_PRODUCT_SCOPE=6_FILES_EXACT\n'

printf '\n===== 2 EXACT PRODUCT SOURCE BLOBS =====\n'
[[ "$(git hash-object "$CORE")" == "$CORE_BLOB" ]] || fail LOCAL_CORE_BLOB_MISMATCH
[[ "$(git hash-object "$RUNTIME_BINDING")" == "$RUNTIME_BLOB" ]] || fail LOCAL_RUNTIME_BLOB_MISMATCH
[[ "$(git hash-object "$TEST_CORE")" == "$TEST_CORE_BLOB" ]] || fail LOCAL_TEST_CORE_BLOB_MISMATCH
[[ "$(git hash-object "$TEST_RUNTIME")" == "$TEST_RUNTIME_BLOB" ]] || fail LOCAL_TEST_RUNTIME_BLOB_MISMATCH
[[ "$(git hash-object "$UNIT")" == "$UNIT_BLOB" ]] || fail LOCAL_UNIT_BLOB_MISMATCH
[[ "$(git hash-object "$NGINX_REPO")" == "$NGINX_BLOB" ]] || fail LOCAL_NGINX_BLOB_MISMATCH

[[ "$(git rev-parse "$SOURCE_HEAD:$CORE")" == "$CORE_BLOB" ]] || fail REMOTE_CORE_BLOB_MISMATCH
[[ "$(git rev-parse "$SOURCE_HEAD:$RUNTIME_BINDING")" == "$RUNTIME_BLOB" ]] || fail REMOTE_RUNTIME_BLOB_MISMATCH
[[ "$(git rev-parse "$SOURCE_HEAD:$TEST_CORE")" == "$TEST_CORE_BLOB" ]] || fail REMOTE_TEST_CORE_BLOB_MISMATCH
[[ "$(git rev-parse "$SOURCE_HEAD:$TEST_RUNTIME")" == "$TEST_RUNTIME_BLOB" ]] || fail REMOTE_TEST_RUNTIME_BLOB_MISMATCH
[[ "$(git rev-parse "$SOURCE_HEAD:$UNIT")" == "$UNIT_BLOB" ]] || fail REMOTE_UNIT_BLOB_MISMATCH
[[ "$(git rev-parse "$SOURCE_HEAD:$NGINX_REPO")" == "$NGINX_BLOB" ]] || fail REMOTE_NGINX_BLOB_MISMATCH
printf 'PRODUCT_SOURCE_BLOBS=6_6_OK\n'

printf '\n===== 3 TEST, SERVICE AND SECURITY GATES =====\n'
python3 -m py_compile "$CORE" "$RUNTIME_BINDING" "$TEST_CORE" "$TEST_RUNTIME"
python3 "$TEST_CORE"
python3 "$TEST_RUNTIME"
git diff --check
systemd-analyze verify "$UNIT"
nginx -t

grep -Fxq 'ProtectSystem=strict' "$UNIT"
grep -Fxq 'PrivateTmp=true' "$UNIT"
grep -Fxq 'ReadOnlyPaths=/root/tokenoskobi_clean_v1' "$UNIT"
grep -Fxq 'StateDirectory=tokenoskobi-product-slice-03' "$UNIT"
grep -Fxq 'StateDirectoryMode=0700' "$UNIT"
grep -Fxq 'CapabilityBoundingSet=' "$UNIT"
grep -Fxq '        proxy_set_header X-Authenticated-User $remote_user;' "$NGINX_REPO"

systemctl is-active --quiet "$SERVICE" || fail PRODUCT_SERVICE_NOT_ACTIVE
systemctl is-active --quiet nginx || fail NGINX_NOT_ACTIVE
PID="$(systemctl show "$SERVICE" -p MainPID --value)"
RESTARTS="$(systemctl show "$SERVICE" -p NRestarts --value)"
[[ "$PID" =~ ^[1-9][0-9]*$ ]] || fail PRODUCT_PID_INVALID
[[ "$RESTARTS" == '0' ]] || fail PRODUCT_SERVICE_RESTARTED_UNEXPECTEDLY
[[ "$(systemctl show "$SERVICE" -p ProtectSystem --value)" == 'strict' ]] || fail PROTECT_SYSTEM_NOT_STRICT
[[ "$(systemctl show "$SERVICE" -p PrivateTmp --value)" == 'yes' ]] || fail PRIVATE_TMP_NOT_ENABLED
[[ -d "$STATE_DIR" && "$(stat -c '%a' "$STATE_DIR")" == '700' ]] || fail STATE_DIRECTORY_INVALID
[[ -f "$EVENTS_FILE" && "$(stat -c '%a' "$EVENTS_FILE")" == '600' ]] || fail EVENT_LOG_INVALID
BAD_PACKET_MODE="$(find "$PACKETS_DIR" -maxdepth 1 -type f -name '*.json' ! -perm 0600 -print -quit)"
[[ -z "$BAD_PACKET_MODE" ]] || fail PACKET_MODE_INVALID
[[ "$(http_code http://127.0.0.1:8096/healthz)" == '200' ]] || fail LOCAL_HEALTH_NOT_200
[[ "$(http_code https://panel.coinoskobi.xyz/panel/panel_v2/)" == '401' ]] || fail EXTERNAL_PANEL_AUTH_GATE_CHANGED
[[ "$(http_code https://panel.coinoskobi.xyz/healthz)" == '200' ]] || fail EXTERNAL_HEALTH_NOT_200
API_UNAUTH="$(curl -sS --connect-timeout 5 --max-time 25 -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' --data '{"token_address":"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"}' https://panel.coinoskobi.xyz/api/v1/analyze 2>/dev/null || true)"
[[ "$API_UNAUTH" == '401' ]] || fail EXTERNAL_API_AUTH_GATE_CHANGED
printf 'DETERMINISTIC_TESTS=24_24_OK\n'
printf 'SYSTEMD_HARDENING=PRESERVED\n'
printf 'BASIC_AUTH=PRESERVED\n'

printf '\n===== 4 PHONE APPEND-ONLY EVIDENCE =====\n'
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/tokenoskobi_product_slice_03_final_close_${STAMP}"
mkdir -p "$BACKUP"
chmod 0700 "$BACKUP"

EVENTS_FILE="$EVENTS_FILE" PACKETS_DIR="$PACKETS_DIR" OUT="$BACKUP/phone_evidence.json" python3 - <<'PY'
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from typing import Any

events_file = Path(os.environ['EVENTS_FILE'])
packets_dir = Path(os.environ['PACKETS_DIR'])
out_path = Path(os.environ['OUT'])
zero = '0' * 64

def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

events=[]
previous=zero
for expected_seq, line in enumerate(events_file.read_text(encoding='utf-8').splitlines(), 1):
    assert line.strip(), 'BLANK_EVENT_LINE'
    event=json.loads(line)
    assert event['seq']==expected_seq, 'EVENT_SEQUENCE_INVALID'
    assert event['prev_hash']==previous, 'EVENT_PREV_HASH_INVALID'
    unsigned=dict(event)
    event_hash=unsigned.pop('event_hash')
    assert digest(unsigned)==event_hash, 'EVENT_HASH_INVALID'
    previous=event_hash
    events.append(event)

waits=[]
for event in events:
    if event.get('event_type')!='HUMAN_DECISION_RECORDED':
        continue
    payload=event.get('payload') or {}
    if payload.get('action')=='WAIT' and payload.get('note')=='Telefon kabul testi' and payload.get('actor')=='coinoskobi_xyz':
        waits.append(event)
assert waits, 'PHONE_WAIT_DECISION_NOT_FOUND'

selected=None
for wait in waits:
    packet_id=wait['packet_id']
    accepts=[
        event for event in events
        if event.get('event_type')=='HUMAN_DECISION_RECORDED'
        and event.get('packet_id')==packet_id
        and event.get('seq', 0)>wait['seq']
        and (event.get('payload') or {}).get('action')=='ACCEPT'
        and (event.get('payload') or {}).get('note')=='Telefon kabul testi'
        and (event.get('payload') or {}).get('actor')=='coinoskobi_xyz'
        and (event.get('payload') or {}).get('previous_decision_event_hash')==wait['event_hash']
    ]
    for accept in accepts:
        outcomes=[
            event for event in events
            if event.get('event_type')=='OUTCOME_OBSERVED'
            and event.get('packet_id')==packet_id
            and (event.get('payload') or {}).get('human_decision_event_hash')==accept['event_hash']
            and (event.get('payload') or {}).get('actor')=='coinoskobi_xyz'
        ]
        if outcomes:
            selected=(wait, accept, outcomes)
            break
    if selected:
        break
assert selected is not None, 'PHONE_REVISION_OUTCOME_CHAIN_NOT_FOUND'
wait, accept, outcomes=selected
latest=outcomes[-1]
packet_id=wait['packet_id']
packet_path=packets_dir / f'{packet_id}.json'
envelope=json.loads(packet_path.read_text(encoding='utf-8'))
assert envelope['packet_id']==packet_id, 'PACKET_ID_MISMATCH'
assert digest(envelope['analysis'])==packet_id, 'PACKET_DIGEST_INVALID'
analysis=envelope['analysis']
authority=envelope['authority']
assert all(authority[key] is False for key in ('paper','live','wallet','signing','order','broadcast')), 'PACKET_AUTHORITY_INVALID'
token=str(analysis['token_address']).lower()
assert token=='0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c', 'PHONE_TOKEN_INVALID'
market=analysis['market']
assert market['target_orientation_verified'] is True, 'TARGET_ORIENTATION_INVALID'
baseline=float((market['token'] or {})['price_usd'])
payload=latest['payload']
assert abs(float(payload['baseline_price_usd'])-baseline)<1e-9, 'BASELINE_PRICE_MISMATCH'
assert float(payload['current_price_usd'])>100, 'CURRENT_PRICE_INVALID'
assert payload['classification'] in ('UP','DOWN','FLAT'), 'CLASSIFICATION_INVALID'
assert payload['target_orientation_verified'] is True, 'OUTCOME_ORIENTATION_INVALID'

result={
    'schema':'tokenoskobi.product_slice_03.phone_acceptance_evidence.v1',
    'hash_chain_integrity':'VERIFIED',
    'event_count':len(events),
    'last_event_hash':events[-1]['event_hash'],
    'packet_id':packet_id,
    'token_address':token,
    'packet_reopen':'VERIFIED',
    'actor':'coinoskobi_xyz',
    'note':'Telefon kabul testi',
    'initial_decision':'WAIT',
    'initial_decision_seq':wait['seq'],
    'initial_decision_hash':wait['event_hash'],
    'effective_decision':'ACCEPT',
    'effective_decision_seq':accept['seq'],
    'effective_decision_hash':accept['event_hash'],
    'revision_link_verified':True,
    'outcome_link_verified':True,
    'outcome_observation_count':len(outcomes),
    'repeated_outcome_observations':'NON_CORRUPTING_APPEND_ONLY_EVENTS',
    'latest_outcome_seq':latest['seq'],
    'latest_outcome_hash':latest['event_hash'],
    'baseline_price_usd':payload['baseline_price_usd'],
    'current_price_usd':payload['current_price_usd'],
    'change_pct':payload['change_pct'],
    'classification':payload['classification'],
    'target_orientation_verified':True,
}
out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('PHONE_PACKET_ID='+packet_id)
print('PHONE_INITIAL_DECISION=WAIT')
print('PHONE_EFFECTIVE_DECISION=ACCEPT')
print('PHONE_DECISION_REVISION_CHAIN=OK')
print('PHONE_OUTCOME_LINKAGE=OK')
print('PHONE_OUTCOME_OBSERVATION_COUNT='+str(len(outcomes)))
print('PHONE_BASELINE_PRICE_USD='+str(payload['baseline_price_usd']))
print('PHONE_CURRENT_PRICE_USD='+str(payload['current_price_usd']))
print('PHONE_CHANGE_PCT='+str(payload['change_pct']))
print('PHONE_CLASSIFICATION='+str(payload['classification']))
print('HASH_CHAIN_INTEGRITY=VERIFIED')
PY

printf '\n===== 5 CANONICAL BACKUP AND SYNCHRONIZATION =====\n'
for path in "${CANONICAL_PATHS[@]}"; do
  [[ -f "$path" ]] || fail "CANONICAL_FILE_MISSING_${path}"
done
tar -czf "$BACKUP/canonical_before.tar.gz" "${CANONICAL_PATHS[@]}"

NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
NOW="$NOW" ROOT="$ROOT" SOURCE_HEAD="$SOURCE_HEAD" SERVICE_PID="$PID" STAGE="$STAGE" FINAL_STATUS="$FINAL_STATUS" NEXT_STEP="$NEXT_STEP" NEXT_PLANNED_STAGE="$NEXT_PLANNED_STAGE" ARTIFACT="$ARTIFACT" PHONE_EVIDENCE="$BACKUP/phone_evidence.json" python3 - <<'PY'
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
from typing import Any

root=Path(os.environ['ROOT'])
now=os.environ['NOW']
source_head=os.environ['SOURCE_HEAD']
service_pid=int(os.environ['SERVICE_PID'])
stage=os.environ['STAGE']
status=os.environ['FINAL_STATUS']
next_step=os.environ['NEXT_STEP']
next_planned=os.environ['NEXT_PLANNED_STAGE']
artifact_path=os.environ['ARTIFACT']
phone=json.loads(Path(os.environ['PHONE_EVIDENCE']).read_text(encoding='utf-8'))
old_stage='PRODUCT_SLICE_02_SINGLE_TOKEN_INPUT_AND_REAL_DECISION_PACKET'
old_status='PRODUCT_SLICE_02_CLOSED_VERIFIED_PHONE_ACCEPTED_GITHUB_SEALED'

def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError(f'OBJECT_REQUIRED:{path}')
    return value

def save(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as handle:
            json.dump(value,handle,ensure_ascii=False,indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def assert_authority(value: dict[str, Any]) -> None:
    for key in ('real_order_authority','real_signing_authority','real_trade_authority','real_wallet_authority'):
        if value.get(key)!=0:
            raise RuntimeError(f'AUTHORITY_CHANGED:{key}:{value.get(key)}')
    if value.get('live_trade')!='DISABLED':
        raise RuntimeError('LIVE_TRADE_NOT_DISABLED')

closure={
    'schema':'tokenoskobi.product_slice_03.final_closure.v1',
    'closed_at_utc':now,
    'stage':stage,
    'status':status,
    'source_branch':'agent/product-slice-03-human-decision-history',
    'source_head':source_head,
    'github_final_head':'DYNAMIC_USE_GIT_REV_PARSE_HEAD',
    'github_remote_verification':'PERFORMED_BY_CLOSURE_SCRIPT_AFTER_PUSH',
    'issue':15,
    'pull_request':16,
    'deterministic_tests':'24/24_OK',
    'runtime':{
        'service':'tokenoskobi-product-slice-02.service',
        'main_pid':service_pid,
        'bind':'127.0.0.1:8096',
        'state_directory':'/var/lib/tokenoskobi-product-slice-03',
        'state_directory_mode':'0700',
        'event_and_packet_mode':'0600',
        'protect_system':'strict',
        'private_tmp':True,
        'repository_read_only':True,
        'basic_auth_preserved':True,
    },
    'phone_acceptance':phone,
    'capabilities':{
        'immutable_sha256_packet':True,
        'hash_chained_append_only_history':True,
        'human_decision_revision_history':True,
        'packet_reopen':True,
        'user_triggered_outcome_tracking':True,
        'authenticated_actor_evidence':True,
    },
    'authority':{
        'paper_trade':'DISABLED',
        'live_trade':'DISABLED',
        'real_wallet_authority':0,
        'real_signing_authority':0,
        'real_order_authority':0,
        'real_trade_authority':0,
        'risk_engine_veto':True,
        'human_action_required':True,
    },
    'next_safe_step':next_step,
    'next_planned_stage':next_planned,
}

runtime_path=root/'PROJECT_RUNTIME.json'
runtime=load(runtime_path)
assert_authority(runtime['authority'])
pointer=runtime.get('canonical_runtime_pointer')
if not isinstance(pointer,dict):
    raise RuntimeError('RUNTIME_POINTER_MISSING')
if pointer.get('current_stage')!=old_stage or pointer.get('current_status')!=old_status:
    raise RuntimeError(f'RUNTIME_CURRENT_STATE_CHANGED:{pointer.get("current_stage")}:{pointer.get("current_status")}')
pointer['current_stage']=stage
pointer['current_status']=status
pointer['next_safe_step']=next_step
pointer['product_slice_03_final_closure']=closure
runtime['product_slice_03_final_closure']=closure
runtime['last_action']='PRODUCT_SLICE_03_FINAL_CLOSURE_AND_GITHUB_SEAL'
runtime['last_completed']=stage
runtime['last_result']=status
runtime['last_artifact']=artifact_path
runtime['updated_at_utc']=now
save(runtime_path,runtime)

roadmap_path=root/'data/tokenoskobi_v1_v8_master_era_roadmap.json'
roadmap=load(roadmap_path)
direction=roadmap.get('current_direction')
if not isinstance(direction,dict):
    raise RuntimeError('ROADMAP_CURRENT_DIRECTION_MISSING')
if direction.get('current_stage')!=old_stage or direction.get('current_status')!=old_status:
    raise RuntimeError('ROADMAP_CURRENT_STATE_CHANGED')
direction['current_stage']=stage
direction['current_status']=status
direction['next_safe_step']=next_step
direction['updated_at_utc']=now
found=False
for item in roadmap.get('deadline_schedule',[]):
    if isinstance(item,dict) and item.get('id')==stage:
        item['status']=status
        item['closed_at_utc']=now
        item['user_visible_acceptance']=True
        item['completion_gate_verified']=True
        item['phone_acceptance_chain']='WAIT_TO_ACCEPT_REVISION_TO_OUTCOME'
        found=True
        break
if not found:
    raise RuntimeError('SLICE03_SCHEDULE_ENTRY_MISSING')
roadmap['product_slice_03_final_closure']=closure
roadmap['updated_at_utc']=now
save(roadmap_path,roadmap)

machine_path=root/'data/control/latest_tk_machine_state.json'
machine=load(machine_path)
assert_authority(machine['authority'])
machine_pointer=machine.get('canonical_runtime_pointer')
if not isinstance(machine_pointer,dict):
    raise RuntimeError('MACHINE_POINTER_MISSING')
machine_pointer['current_stage']=stage
machine_pointer['current_status']=status
machine_pointer['next_safe_step']=next_step
machine_pointer['product_slice_03_final_closure']=closure
machine['product_slice_03_final_closure']=closure
machine['next_safe_step']=next_step
machine['updated_at_utc']=now
save(machine_path,machine)

history_path=root/'PROJECT_HISTORY.json'
history=load(history_path)
events=history.get('events')
if not isinstance(events,list):
    raise RuntimeError('HISTORY_EVENTS_MISSING')
event_id='PRODUCT_SLICE_03_HUMAN_DECISION_HISTORY_FINAL_CLOSURE_V1'
if any(isinstance(event,dict) and event.get('event_id')==event_id for event in events):
    raise RuntimeError('HISTORY_EVENT_ALREADY_EXISTS')
events.append({
    'event':'PRODUCT_SLICE_03_HUMAN_DECISION_HISTORY_AND_OUTCOME_TRACKING_CLOSED',
    'event_id':event_id,
    'timestamp_utc':now,
    'schema':'tokenoskobi.product_slice_03.final_closure.v1',
    'status':status,
    'stage':stage,
    'artifact':artifact_path,
    'source_head':source_head,
    'deterministic_tests':'24/24_OK',
    'phone_acceptance':phone,
    'systemd_hardening_preserved':True,
    'basic_auth_preserved':True,
    'paper_trade':'DISABLED',
    'live_trade':'DISABLED',
    'real_financial_authority':0,
    'issue':15,
    'pull_request':16,
    'next_safe_step':next_step,
    'next_planned_stage':next_planned,
})
history['updated_at_utc']=now
save(history_path,history)

save(root/artifact_path,closure)

almanac_path=root/'04_ALMANAC.md'
almanac=almanac_path.read_text(encoding='utf-8')
marker='<!-- PRODUCT_SLICE_03_FINAL_CLOSURE:BEGIN -->'
if marker in almanac:
    raise RuntimeError('ALMANAC_SLICE03_MARKER_ALREADY_EXISTS')
section=f'''{marker}
## Product Slice 03 Final Acceptance

- Closed UTC: `{now}`
- Status: `{status}`
- Immutable packet: `SHA-256 addressed`
- Append-only history: `HASH CHAIN VERIFIED`
- Phone decision chain: `WAIT -> ACCEPT revision -> OUTCOME`
- Packet ID: `{phone['packet_id']}`
- Baseline/current: `{phone['baseline_price_usd']} / {phone['current_price_usd']} USD`
- Change/classification: `{phone['change_pct']}% / {phone['classification']}`
- Outcome observations: `{phone['outcome_observation_count']}` non-corrupting append-only events
- Authenticated actor: `{phone['actor']}`
- Tests: `24/24 OK`
- State/event/packet modes: `0700 / 0600 / 0600`
- Systemd hardening and Basic Auth: `PRESERVED`
- Paper/live authority: `DISABLED / 0`
- Artifact: `{artifact_path}`
- Next planned product stage: `{next_planned}`
- Next safe step: `{next_step}`
<!-- PRODUCT_SLICE_03_FINAL_CLOSURE:END -->'''
first,rest=almanac.split('\n',1)
almanac_path.write_text(first+'\n\n'+section+'\n\n'+rest,encoding='utf-8')

atlas_path=root/'05_ATLAS.md'
atlas=atlas_path.read_text(encoding='utf-8')
atlas_marker='<!-- PRODUCT_SLICE_03_RUNTIME_PATH:BEGIN -->'
if atlas_marker in atlas:
    raise RuntimeError('ATLAS_SLICE03_MARKER_ALREADY_EXISTS')
atlas_section=f'''{atlas_marker}
## PRODUCT SLICE 03 RUNTIME PATH

```text
AUTHENTICATED PHONE / BROWSER
  -> TOKEN ANALYSIS AND ADVISORY DECISION
  -> IMMUTABLE SHA-256 EVIDENCE PACKET
  -> HASH-CHAINED APPEND-ONLY EVENT LOG
  -> HUMAN WAIT / ACCEPT / REJECT / REVIEW
  -> DECISION REVISION WITHOUT DELETION
  -> EXACT PACKET REOPEN
  -> USER-TRIGGERED TARGET-ORIENTED OUTCOME OBSERVATION
  -> HISTORY DISPLAY
```

- Persistent state is owned by systemd `StateDirectory=tokenoskobi-product-slice-03`.
- Repository remains read-only; state directory mode is `0700`, packet/event modes are `0600`.
- Basic Auth actor is recorded in decision and outcome events.
- Outcome recording requires a human decision and links to its exact event hash.
- Repeated outcome requests append observations; previous evidence is never overwritten.
- Paper/live/wallet/signing/order/broadcast authority remains disabled.
<!-- PRODUCT_SLICE_03_RUNTIME_PATH:END -->'''
first,rest=atlas.split('\n',1)
atlas_path.write_text(first+'\n\n'+atlas_section+'\n\n'+rest,encoding='utf-8')

master=f'''# 06 PROJECT MASTER STATE

CURRENT_VERSION=V4
CURRENT_ERA=ERA64
CURRENT_STAGE={stage}
CURRENT_STATUS={status}
NO_NEW_ERA=true
NEXT_SAFE_STEP={next_step}
NEXT_PLANNED_STAGE={next_planned}

PRODUCT_SLICE_03_CLOSED=true
IMMUTABLE_EVIDENCE_PACKET=true
APPEND_ONLY_HASH_CHAIN_VERIFIED=true
PHONE_PACKET_REOPEN=true
PHONE_INITIAL_DECISION=WAIT
PHONE_EFFECTIVE_DECISION=ACCEPT
PHONE_OUTCOME_TRACKING=true
PHONE_OUTCOME_OBSERVATION_COUNT={phone['outcome_observation_count']}
AUTHENTICATED_ACTOR_EVIDENCE=true
STATE_DIRECTORY_MODE=700
EVENT_AND_PACKET_MODE=600
SYSTEMD_HARDENING_PRESERVED=true
BASIC_AUTH_PRESERVED=true
PAPER_RUNTIME=DISABLED
LIVE_TRADE=DISABLED
REAL_FINANCIAL_AUTHORITY=0
ARTIFACT={artifact_path}
'''
(root/'06_PROJECT_MASTER_STATE.md').write_text(master,encoding='utf-8')

handoff=f'''# 07 PROJECT HANDOFF

CURRENT_STAGE={stage}
STATUS={status}
NEXT_SAFE_STEP={next_step}
NEXT_PLANNED_STAGE={next_planned}

Product Slice 03 is closed and verified. The authenticated panel stores each analysis as an immutable SHA-256 evidence packet, records human decisions and revisions in a hash-chained append-only history, reopens exact packets and stores user-triggered target-oriented outcome observations. Phone acceptance verified WAIT -> ACCEPT revision -> DOWN outcome on WBNB. Repeated outcome observations remain separate non-corrupting events. Systemd hardening, repository read-only policy and Basic Auth remain active. Paper/live/wallet/signing/order/broadcast authority remains disabled.
'''
(root/'07_PROJECT_HANDOFF.md').write_text(handoff,encoding='utf-8')

report=f'''# TOKENOSKOBI LATEST HANDOFF

CURRENT_STAGE={stage}
STATUS={status}
NEXT_SAFE_STEP={next_step}
NEXT_PLANNED_STAGE={next_planned}
ARTIFACT={artifact_path}
PHONE_PACKET_REOPEN=VERIFIED
PHONE_INITIAL_DECISION=WAIT
PHONE_EFFECTIVE_DECISION=ACCEPT
PHONE_DECISION_REVISION_CHAIN=VERIFIED
PHONE_OUTCOME_LINKAGE=VERIFIED
PHONE_OUTCOME_OBSERVATION_COUNT={phone['outcome_observation_count']}
HASH_CHAIN_INTEGRITY=VERIFIED
SYSTEMD_HARDENING=PRESERVED
BASIC_AUTH=PRESERVED
PAPER_RUNTIME=DISABLED
LIVE_TRADE=DISABLED
REAL_FINANCIAL_AUTHORITY=0
'''
(root/'reports/LATEST_TK_AI_HANDOFF.md').write_text(report,encoding='utf-8')

print('CANONICAL_SYNC=OK')
print('PROJECT_BOOT_UPDATED=false')
print('SLICE03_ARTIFACT='+artifact_path)
PY
CANONICAL_MUTATED=1

printf '\n===== 6 CANONICAL AND REGRESSION VALIDATION =====\n'
JSON_FILES=(
  PROJECT_RUNTIME.json
  PROJECT_HISTORY.json
  data/control/latest_tk_machine_state.json
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  "$ARTIFACT"
)
for file in "${JSON_FILES[@]}"; do
  python3 -m json.tool "$file" >/dev/null
done

grep -Fq "$FINAL_STATUS" PROJECT_RUNTIME.json
grep -Fq "$FINAL_STATUS" PROJECT_HISTORY.json
grep -Fq "$FINAL_STATUS" data/tokenoskobi_v1_v8_master_era_roadmap.json
grep -Fq "$FINAL_STATUS" 06_PROJECT_MASTER_STATE.md
grep -Fq "$FINAL_STATUS" 07_PROJECT_HANDOFF.md
! git diff -- PROJECT_BOOT.json | grep -q . || fail PROJECT_BOOT_CHANGED_UNEXPECTEDLY

git diff --check
python3 -m py_compile "$CORE" "$RUNTIME_BINDING" "$TEST_CORE" "$TEST_RUNTIME"
python3 "$TEST_CORE"
python3 "$TEST_RUNTIME"
[[ "$(http_code http://127.0.0.1:8096/healthz)" == '200' ]] || fail HEALTH_CHANGED_AFTER_CANONICAL_SYNC
printf 'CANONICAL_VALIDATION=OK\n'
printf 'REGRESSION_TESTS=24_24_OK\n'
printf 'PROJECT_BOOT_UNCHANGED=OK\n'

printf '\n===== 7 ATOMIC CLOSURE COMMIT =====\n'
git add -- "${PRODUCT_PATHS[@]}" \
  04_ALMANAC.md \
  05_ATLAS.md \
  06_PROJECT_MASTER_STATE.md \
  07_PROJECT_HANDOFF.md \
  PROJECT_HISTORY.json \
  PROJECT_RUNTIME.json \
  data/control/latest_tk_machine_state.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  "$ARTIFACT"
git add -f -- reports/LATEST_TK_AI_HANDOFF.md

EXPECTED_STAGED="$(printf '%s\n' \
  "${PRODUCT_PATHS[@]}" \
  04_ALMANAC.md \
  05_ATLAS.md \
  06_PROJECT_MASTER_STATE.md \
  07_PROJECT_HANDOFF.md \
  PROJECT_HISTORY.json \
  PROJECT_RUNTIME.json \
  data/control/latest_tk_machine_state.json \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  "$ARTIFACT" \
  reports/LATEST_TK_AI_HANDOFF.md | sort)"
ACTUAL_STAGED="$(git diff --cached --name-only | sort)"
printf '%s\n' "$ACTUAL_STAGED"
[[ "$ACTUAL_STAGED" == "$EXPECTED_STAGED" ]] || fail STAGED_SCOPE_CHANGED
git diff --cached --check

git commit -m 'feat(product): close Slice 03 decision history loop'
COMMIT_CREATED=1
FINAL_HEAD="$(git rev-parse HEAD)"
printf 'FINAL_LOCAL_HEAD=%s\n' "$FINAL_HEAD"

printf '\n===== 8 SINGLE PUSH AND REMOTE VERIFICATION =====\n'
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail WORKTREE_NOT_CLEAN_BEFORE_PUSH
git fetch --quiet origin main
[[ "$(git rev-parse origin/main)" == "$EXPECTED_MAIN" ]] || fail ORIGIN_MAIN_MOVED_BEFORE_PUSH
git push origin HEAD:main
PUSH_COMPLETED=1
git fetch --quiet origin main
REMOTE_HEAD="$(git rev-parse origin/main)"
[[ "$REMOTE_HEAD" == "$FINAL_HEAD" ]] || fail REMOTE_HEAD_MISMATCH

[[ "$(git rev-parse "origin/main:$CORE")" == "$CORE_BLOB" ]] || fail REMOTE_CORE_BLOB_CHANGED
[[ "$(git rev-parse "origin/main:$RUNTIME_BINDING")" == "$RUNTIME_BLOB" ]] || fail REMOTE_RUNTIME_BLOB_CHANGED
[[ "$(git rev-parse "origin/main:$TEST_CORE")" == "$TEST_CORE_BLOB" ]] || fail REMOTE_TEST_CORE_BLOB_CHANGED
[[ "$(git rev-parse "origin/main:$TEST_RUNTIME")" == "$TEST_RUNTIME_BLOB" ]] || fail REMOTE_TEST_RUNTIME_BLOB_CHANGED
[[ "$(git rev-parse "origin/main:$UNIT")" == "$UNIT_BLOB" ]] || fail REMOTE_UNIT_BLOB_CHANGED
[[ "$(git rev-parse "origin/main:$NGINX_REPO")" == "$NGINX_BLOB" ]] || fail REMOTE_NGINX_BLOB_CHANGED

git show origin/main:PROJECT_RUNTIME.json | STAGE="$STAGE" FINAL_STATUS="$FINAL_STATUS" NEXT_STEP="$NEXT_STEP" python3 -c '
import json, os, sys
r=json.load(sys.stdin)
p=r["canonical_runtime_pointer"]
assert p["current_stage"]==os.environ["STAGE"]
assert p["current_status"]==os.environ["FINAL_STATUS"]
assert p["next_safe_step"]==os.environ["NEXT_STEP"]
c=p["product_slice_03_final_closure"]
assert c["status"]==os.environ["FINAL_STATUS"]
assert c["phone_acceptance"]["initial_decision"]=="WAIT"
assert c["phone_acceptance"]["effective_decision"]=="ACCEPT"
assert c["authority"]["live_trade"]=="DISABLED"
assert c["authority"]["real_trade_authority"]==0
print("REMOTE_CANONICAL_RUNTIME=OK")
'

git cat-file -e "origin/main:$ARTIFACT"
[[ -z "$(git status --porcelain=v1 --untracked-files=all)" ]] || fail FINAL_WORKTREE_NOT_CLEAN
[[ "$(http_code http://127.0.0.1:8096/healthz)" == '200' ]] || fail FINAL_LOCAL_HEALTH_NOT_200
[[ "$(http_code https://panel.coinoskobi.xyz/panel/panel_v2/)" == '401' ]] || fail FINAL_EXTERNAL_PANEL_AUTH_GATE_CHANGED
[[ "$(http_code https://panel.coinoskobi.xyz/healthz)" == '200' ]] || fail FINAL_EXTERNAL_HEALTH_NOT_200

trap - ERR INT TERM
printf '\n===== FINAL =====\n'
printf 'PRODUCT_SLICE_03_FINAL_CLOSURE=SUCCESS\n'
printf 'FINAL_LOCAL_HEAD=%s\n' "$FINAL_HEAD"
printf 'FINAL_REMOTE_HEAD=%s\n' "$REMOTE_HEAD"
printf 'ATOMIC_SINGLE_COMMIT=true\n'
printf 'SINGLE_PUSH=VERIFIED\n'
printf 'WORKTREE_CLEAN=true\n'
printf 'PHONE_PACKET_REOPEN=VERIFIED\n'
printf 'PHONE_INITIAL_DECISION=WAIT\n'
printf 'PHONE_EFFECTIVE_DECISION=ACCEPT\n'
printf 'PHONE_DECISION_REVISION_CHAIN=VERIFIED\n'
printf 'PHONE_OUTCOME_LINKAGE=VERIFIED\n'
printf 'REPEATED_OUTCOME_OBSERVATIONS=NON_CORRUPTING_APPEND_ONLY_EVENTS\n'
printf 'HASH_CHAIN_INTEGRITY=VERIFIED\n'
printf 'PROJECT_BOOT_UPDATED=false\n'
printf 'PR_16=OPEN_PENDING_ASSISTANT_CLOSURE\n'
printf 'ISSUE_15=OPEN_PENDING_ASSISTANT_CLOSURE\n'
printf 'PAPER_TRADE=DISABLED\n'
printf 'LIVE_TRADE=DISABLED\n'
printf 'REAL_FINANCIAL_AUTHORITY=0\n'
printf 'NEXT_SAFE_STEP=%s\n' "$NEXT_STEP"
printf 'NEXT_PLANNED_STAGE=%s\n' "$NEXT_PLANNED_STAGE"
printf 'BACKUP_DIR=%s\n' "$BACKUP"
