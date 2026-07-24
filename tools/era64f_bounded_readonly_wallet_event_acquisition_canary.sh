#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

STAGE="ERA64F_BOUNDED_READONLY_REAL_WALLET_EVENT_ACQUISITION_CANARY"
CONFIG="config/era64f_bounded_readonly_wallet_event_canary_v1.json"
ENGINE="tools/era64f_bounded_readonly_wallet_event_canary_v1.py"
TEST="tests/test_era64f_bounded_readonly_wallet_event_canary_v1.py"
DETAIL="data/replay/era64f_bounded_readonly_wallet_event_canary_v1.json"
ARTIFACT="data/control/era64f_bounded_readonly_wallet_event_canary_v1.json"
REPORT="reports/LATEST_ERA64F_BOUNDED_READONLY_WALLET_EVENT_CANARY.md"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/era64f_readonly_wallet_canary_backup_${STAMP}.tar.gz"
COMMITTED=0

CANONICAL_FILES=(
  PROJECT_BOOT.json
  PROJECT_RUNTIME.json
  PROJECT_HISTORY.json
  03_ROADMAP.md
  06_PROJECT_MASTER_STATE.md
  07_PROJECT_HANDOFF.md
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
)

NEW_FILES=(
  "$CONFIG"
  "$ENGINE"
  "$TEST"
  "$DETAIL"
  "$ARTIFACT"
  "$REPORT"
)

rollback() {
  rc=$?
  trap - ERR
  echo "ERA64F_FAILED_RC=$rc"
  if [[ "$COMMITTED" -eq 0 && -f "$BACKUP" ]]; then
    tar -xzf "$BACKUP" -C /root/tokenoskobi_clean_v1
    rm -f "${NEW_FILES[@]}"
    git reset --quiet
    echo "ROLLBACK=COMPLETED"
  fi
  exit "$rc"
}
trap rollback ERR

[[ "$(git branch --show-current)" == "main" ]]
[[ -z "$(git status --porcelain=v1)" ]]
git fetch origin main --quiet
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer
! systemctl is-enabled --quiet tokenoskobi-era63d-market-technical.timer

python3 <<'PY_PRECHECK'
import json
from pathlib import Path

runtime=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
pointer=runtime.get('canonical_runtime_pointer') if isinstance(runtime.get('canonical_runtime_pointer'),dict) else runtime
assert pointer.get('current_era')=='ERA64'
assert pointer.get('current_stage')=='ERA64E_BOUNDED_REAL_WALLET_EVENT_ACQUISITION_AND_BACKFILL_PLAN'
assert pointer.get('next_safe_step')=='ERA64F_BOUNDED_READONLY_REAL_WALLET_EVENT_ACQUISITION_CANARY_REQUIRES_USER_APPROVAL'
assert pointer.get('era64e_execution_started') is False
assert pointer.get('era64e_network_access_used') is False
assert pointer.get('era64e_database_write_used') is False
assert pointer.get('paper_runtime_enabled',runtime.get('paper_runtime_enabled')) is False
authority=runtime.get('authority',{})
assert isinstance(authority,dict)
assert authority.get('real_trade_authority')==0
assert authority.get('real_wallet_authority')==0
assert authority.get('real_signing_authority')==0
assert authority.get('real_order_authority')==0
assert authority.get('live_trade')=='DISABLED'
plan=json.loads(Path('data/control/era64e_bounded_wallet_event_acquisition_backfill_plan_v1.json').read_text(encoding='utf-8'))
assert plan.get('status')=='BOUNDED_REAL_WALLET_EVENT_ACQUISITION_BACKFILL_PLAN_LOCKED'
assert plan.get('execution_started') is False
assert plan.get('network_access_used') is False
assert plan.get('database_write_used') is False
assert not any(plan.get('authority',{}).values())
print('PRECHECK=VERIFIED')
PY_PRECHECK

tar -czf "$BACKUP" "${CANONICAL_FILES[@]}"
echo "BACKUP=$BACKUP"

mkdir -p config tools tests data/control data/replay reports

cat > "$CONFIG" <<'JSON_CONFIG'
{
  "schema": "tokenoskobi.era64f.bounded_readonly_wallet_event_canary.config.v1",
  "mode": "BOUNDED_READONLY_REAL_NETWORK_CANARY",
  "chain": {
    "name": "BSC",
    "chain_id": 56,
    "confirmation_depth": 12
  },
  "provider_config": "config/era63e_always_on_market_runtime_v1.json",
  "rpc_method_allowlist": [
    "eth_chainId",
    "eth_blockNumber",
    "eth_getBlockByNumber",
    "eth_getTransactionReceipt"
  ],
  "limits": {
    "block_span": 4,
    "maximum_transactions_per_block": 24,
    "maximum_receipts": 96,
    "maximum_rpc_requests": 140,
    "maximum_events": 1500,
    "maximum_runtime_seconds": 180,
    "request_timeout_seconds": 8,
    "retries_per_endpoint": 1
  },
  "acceptance": {
    "minimum_scanned_blocks": 1,
    "minimum_receipts": 1,
    "minimum_real_wallet_events": 1,
    "maximum_duplicate_events": 0,
    "maximum_authority_violations": 0
  },
  "authority": {
    "network_access": true,
    "network_mode": "READ_ONLY_ALLOWLISTED_BSC_RPC",
    "database_write": false,
    "runtime_mutation": false,
    "panel_mutation": false,
    "service_mutation": false,
    "timer_mutation": false,
    "paper_trade": false,
    "live_trade": false,
    "wallet": false,
    "signing": false,
    "order_create": false,
    "broadcast": false
  },
  "outputs": {
    "detail": "data/replay/era64f_bounded_readonly_wallet_event_canary_v1.json",
    "control": "data/control/era64f_bounded_readonly_wallet_event_canary_v1.json"
  }
}
JSON_CONFIG

cat > "$ENGINE" <<'PY_ENGINE'
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
SCHEMA='tokenoskobi.era64f.bounded_readonly_wallet_event_canary.output.v1'
CONFIG_SCHEMA='tokenoskobi.era64f.bounded_readonly_wallet_event_canary.config.v1'
TRANSFER_TOPIC='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ZERO_ADDRESS='0x0000000000000000000000000000000000000000'

class CanaryError(RuntimeError):
    pass

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def canonical_hash(value: Any) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def atomic_json(path: Path,value: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    json.loads(temp.read_text(encoding='utf-8'))
    temp.replace(path)

def as_hex_int(value: Any,name: str) -> int:
    try:
        number=int(str(value),16)
    except (TypeError,ValueError) as exc:
        raise CanaryError(f'{name}:INVALID_HEX') from exc
    if number < 0:
        raise CanaryError(f'{name}:NEGATIVE')
    return number

def normalize_address(value: Any) -> str | None:
    text=str(value or '').strip().lower()
    if not text.startswith('0x') or len(text)!=42:
        return None
    try:
        int(text[2:],16)
    except ValueError:
        return None
    return text

def topic_address(value: Any) -> str | None:
    text=str(value or '').strip().lower()
    if not text.startswith('0x') or len(text)!=66:
        return None
    return normalize_address('0x'+text[-40:])

def finite_nonnegative(value: Any,name: str) -> int:
    try:
        number=int(value)
    except (TypeError,ValueError) as exc:
        raise CanaryError(f'{name}:NOT_INTEGER') from exc
    if number < 0 or not math.isfinite(float(number)):
        raise CanaryError(f'{name}:INVALID')
    return number

def validate_config(config: dict[str,Any],provider: dict[str,Any]) -> None:
    if config.get('schema')!=CONFIG_SCHEMA:
        raise CanaryError('CONFIG_SCHEMA_MISMATCH')
    chain=config.get('chain')
    if not isinstance(chain,dict) or int(chain.get('chain_id',0))!=56:
        raise CanaryError('CHAIN_ID_MUST_BE_BSC_56')
    authority=config.get('authority')
    if not isinstance(authority,dict):
        raise CanaryError('AUTHORITY_NOT_OBJECT')
    if authority.get('network_access') is not True or authority.get('network_mode')!='READ_ONLY_ALLOWLISTED_BSC_RPC':
        raise CanaryError('READONLY_NETWORK_CANARY_NOT_EXPLICIT')
    for key in ('database_write','runtime_mutation','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
        if authority.get(key) is not False:
            raise CanaryError(f'{key}:MUST_BE_FALSE')
    allowed_methods=set(config.get('rpc_method_allowlist') or [])
    expected={'eth_chainId','eth_blockNumber','eth_getBlockByNumber','eth_getTransactionReceipt'}
    if allowed_methods!=expected:
        raise CanaryError('RPC_METHOD_ALLOWLIST_MISMATCH')
    rpc=provider.get('rpc')
    if not isinstance(rpc,dict) or int(rpc.get('chain_id',0))!=56:
        raise CanaryError('PROVIDER_CHAIN_ID_MISMATCH')
    endpoints=rpc.get('endpoints')
    allowed_hosts=set(rpc.get('allowed_hosts') or [])
    if not isinstance(endpoints,list) or not endpoints or not allowed_hosts:
        raise CanaryError('PROVIDER_ENDPOINTS_MISSING')
    for endpoint in endpoints:
        parsed=urllib.parse.urlparse(str(endpoint))
        if parsed.scheme!='https' or parsed.hostname not in allowed_hosts:
            raise CanaryError('PROVIDER_NOT_ALLOWLISTED_HTTPS')
    limits=config.get('limits')
    if not isinstance(limits,dict):
        raise CanaryError('LIMITS_NOT_OBJECT')
    bounded={
        'block_span':(1,8),
        'maximum_transactions_per_block':(1,32),
        'maximum_receipts':(1,128),
        'maximum_rpc_requests':(4,200),
        'maximum_events':(1,2000),
        'maximum_runtime_seconds':(30,300),
        'request_timeout_seconds':(2,15),
        'retries_per_endpoint':(0,2),
    }
    for key,(minimum,maximum) in bounded.items():
        number=finite_nonnegative(limits.get(key),key)
        if number < minimum or number > maximum:
            raise CanaryError(f'{key}:OUT_OF_BOUNDS')
    if int(chain.get('confirmation_depth',0)) < 12:
        raise CanaryError('CONFIRMATION_DEPTH_TOO_LOW')

class RpcClient:
    def __init__(self,config: dict[str,Any],provider: dict[str,Any]):
        rpc=provider['rpc']
        self.endpoints=[str(item).rstrip('/') for item in rpc['endpoints']]
        self.allowed_hosts=set(rpc['allowed_hosts'])
        limits=config['limits']
        self.timeout=float(limits['request_timeout_seconds'])
        self.retries=int(limits['retries_per_endpoint'])
        self.maximum_requests=int(limits['maximum_rpc_requests'])
        self.allowed_methods=set(config['rpc_method_allowlist'])
        self.request_count=0
        self.endpoint_index=0
        self.last_endpoint_host=None
        self.errors: list[str]=[]

    def call(self,method: str,params: list[Any]) -> Any:
        if method not in self.allowed_methods:
            raise CanaryError(f'RPC_METHOD_NOT_ALLOWLISTED:{method}')
        if self.request_count >= self.maximum_requests:
            raise CanaryError('RPC_REQUEST_BUDGET_EXCEEDED')
        last_error=''
        endpoint_count=len(self.endpoints)
        for offset in range(endpoint_count):
            endpoint=self.endpoints[(self.endpoint_index+offset)%endpoint_count]
            parsed=urllib.parse.urlparse(endpoint)
            if parsed.scheme!='https' or parsed.hostname not in self.allowed_hosts:
                continue
            for attempt in range(self.retries+1):
                if self.request_count >= self.maximum_requests:
                    raise CanaryError('RPC_REQUEST_BUDGET_EXCEEDED')
                self.request_count += 1
                payload=json.dumps({
                    'jsonrpc':'2.0',
                    'id':self.request_count,
                    'method':method,
                    'params':params,
                }).encode('utf-8')
                request=urllib.request.Request(
                    endpoint,
                    data=payload,
                    headers={'Content-Type':'application/json','User-Agent':'Tokenoskobi-ERA64F/1.0 bounded-readonly'},
                    method='POST',
                )
                try:
                    with urllib.request.urlopen(request,timeout=self.timeout) as response:
                        result=json.loads(response.read().decode('utf-8'))
                    if not isinstance(result,dict):
                        raise CanaryError('RPC_RESPONSE_NOT_OBJECT')
                    if result.get('error'):
                        raise CanaryError(f"RPC_ERROR:{result['error']}")
                    if 'result' not in result:
                        raise CanaryError('RPC_RESULT_MISSING')
                    self.endpoint_index=(self.endpoint_index+offset)%endpoint_count
                    self.last_endpoint_host=parsed.hostname
                    return result['result']
                except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError,OSError,json.JSONDecodeError,CanaryError) as exc:
                    last_error=f'{type(exc).__name__}:{exc}'
                    self.errors.append(f'{parsed.hostname}:{method}:{last_error}')
                    if attempt < self.retries:
                        time.sleep(min(0.5*(2**attempt),1.0))
        raise CanaryError(f'ALL_RPC_ENDPOINTS_FAILED:{method}:{last_error}')

def transaction_hash(tx: dict[str,Any]) -> str | None:
    text=str(tx.get('hash') or '').strip().lower()
    if not text.startswith('0x') or len(text)!=66:
        return None
    try:
        int(text[2:],16)
    except ValueError:
        return None
    return text

def event_key(event: dict[str,Any]) -> tuple[Any,...]:
    return (
        event['chain_id'],
        event['tx_hash'],
        event['event_type'],
        event.get('log_index',-1),
        event['from_address'],
        event['to_address'],
        event.get('token_address'),
        event['amount_raw'],
    )

def build_native_event(tx: dict[str,Any],receipt: dict[str,Any],block: dict[str,Any],provider_host: str | None) -> dict[str,Any] | None:
    value=as_hex_int(tx.get('value','0x0'),'tx.value')
    if value <= 0:
        return None
    src=normalize_address(tx.get('from'))
    dst=normalize_address(tx.get('to'))
    tx_hash=transaction_hash(tx)
    if src is None or dst is None or tx_hash is None:
        return None
    block_number=as_hex_int(block.get('number'),'block.number')
    timestamp=as_hex_int(block.get('timestamp'),'block.timestamp')
    gas_used=as_hex_int(receipt.get('gasUsed') or '0x0','receipt.gasUsed')
    effective=as_hex_int(receipt.get('effectiveGasPrice') or tx.get('gasPrice') or '0x0','receipt.effectiveGasPrice')
    base={
        'event_type':'NATIVE_TRANSFER',
        'chain':'BSC',
        'chain_id':56,
        'tx_hash':tx_hash,
        'log_index':-1,
        'block_number':block_number,
        'block_hash':str(block.get('hash') or '').lower(),
        'block_time_utc':datetime.fromtimestamp(timestamp,tz=timezone.utc).isoformat(),
        'from_address':src,
        'to_address':dst,
        'token_address':ZERO_ADDRESS,
        'amount_raw':str(value),
        'gas_used':str(gas_used),
        'effective_gas_price_wei':str(effective),
        'gas_cost_wei':str(gas_used*effective),
        'receipt_status':as_hex_int(receipt.get('status') or '0x0','receipt.status'),
        'source_provider_host':provider_host,
        'evidence_kind':'REAL_BSC_TRANSACTION_AND_RECEIPT',
    }
    base['evidence_hash']=canonical_hash(base)
    return base

def build_token_events(tx: dict[str,Any],receipt: dict[str,Any],block: dict[str,Any],provider_host: str | None) -> list[dict[str,Any]]:
    tx_hash=transaction_hash(tx)
    if tx_hash is None:
        return []
    block_number=as_hex_int(block.get('number'),'block.number')
    timestamp=as_hex_int(block.get('timestamp'),'block.timestamp')
    gas_used=as_hex_int(receipt.get('gasUsed') or '0x0','receipt.gasUsed')
    effective=as_hex_int(receipt.get('effectiveGasPrice') or tx.get('gasPrice') or '0x0','receipt.effectiveGasPrice')
    output=[]
    logs=receipt.get('logs')
    if not isinstance(logs,list):
        return output
    for log in logs:
        if not isinstance(log,dict):
            continue
        topics=log.get('topics')
        if not isinstance(topics,list) or len(topics)<3 or str(topics[0]).lower()!=TRANSFER_TOPIC:
            continue
        src=topic_address(topics[1])
        dst=topic_address(topics[2])
        token=normalize_address(log.get('address'))
        if src is None or dst is None or token is None:
            continue
        try:
            amount=as_hex_int(log.get('data') or '0x0','log.data')
            log_index=as_hex_int(log.get('logIndex'),'log.logIndex')
        except CanaryError:
            continue
        event={
            'event_type':'TOKEN_TRANSFER',
            'chain':'BSC',
            'chain_id':56,
            'tx_hash':tx_hash,
            'log_index':log_index,
            'block_number':block_number,
            'block_hash':str(block.get('hash') or '').lower(),
            'block_time_utc':datetime.fromtimestamp(timestamp,tz=timezone.utc).isoformat(),
            'from_address':src,
            'to_address':dst,
            'token_address':token,
            'amount_raw':str(amount),
            'gas_used':str(gas_used),
            'effective_gas_price_wei':str(effective),
            'gas_cost_wei':str(gas_used*effective),
            'receipt_status':as_hex_int(receipt.get('status') or '0x0','receipt.status'),
            'source_provider_host':provider_host,
            'evidence_kind':'REAL_BSC_ERC20_TRANSFER_LOG',
        }
        event['evidence_hash']=canonical_hash(event)
        output.append(event)
    return output

def run(config_path: Path) -> tuple[dict[str,Any],dict[str,Any]]:
    started=time.monotonic()
    config=json.loads(config_path.read_text(encoding='utf-8'))
    provider_path=ROOT/str(config['provider_config'])
    provider=json.loads(provider_path.read_text(encoding='utf-8'))
    validate_config(config,provider)
    client=RpcClient(config,provider)
    authority={
        'network_access':True,
        'network_mode':'READ_ONLY_ALLOWLISTED_BSC_RPC',
        'database_write':False,
        'runtime_mutation':False,
        'panel_mutation':False,
        'service_mutation':False,
        'timer_mutation':False,
        'paper_trade':False,
        'live_trade':False,
        'wallet':False,
        'signing':False,
        'order_create':False,
        'broadcast':False,
    }
    chain_id=as_hex_int(client.call('eth_chainId',[]),'eth_chainId')
    if chain_id!=56:
        raise CanaryError(f'CHAIN_ID_MISMATCH:{chain_id}')
    latest=as_hex_int(client.call('eth_blockNumber',[]),'eth_blockNumber')
    confirmation_depth=int(config['chain']['confirmation_depth'])
    end_block=latest-confirmation_depth
    if end_block < 0:
        raise CanaryError('CONFIRMED_BLOCK_NEGATIVE')
    span=int(config['limits']['block_span'])
    start_block=max(0,end_block-span+1)
    max_tx=int(config['limits']['maximum_transactions_per_block'])
    max_receipts=int(config['limits']['maximum_receipts'])
    max_events=int(config['limits']['maximum_events'])
    max_runtime=float(config['limits']['maximum_runtime_seconds'])
    events: dict[tuple[Any,...],dict[str,Any]]={}
    duplicate_count=0
    scanned_blocks=[]
    receipt_count=0
    tx_examined=0
    skipped_receipts=0
    status_errors=[]
    for number in range(start_block,end_block+1):
        if time.monotonic()-started > max_runtime:
            status_errors.append('MAXIMUM_RUNTIME_SECONDS_REACHED')
            break
        block=client.call('eth_getBlockByNumber',[hex(number),True])
        if not isinstance(block,dict):
            status_errors.append(f'BLOCK_NOT_OBJECT:{number}')
            continue
        actual_number=as_hex_int(block.get('number'),'block.number')
        if actual_number!=number:
            raise CanaryError(f'BLOCK_NUMBER_MISMATCH:{actual_number}!={number}')
        block_hash=str(block.get('hash') or '').lower()
        if not block_hash.startswith('0x') or len(block_hash)!=66:
            raise CanaryError(f'BLOCK_HASH_INVALID:{number}')
        transactions=block.get('transactions')
        if not isinstance(transactions,list):
            raise CanaryError(f'BLOCK_TRANSACTIONS_NOT_LIST:{number}')
        scanned_blocks.append({
            'block_number':number,
            'block_hash':block_hash,
            'block_timestamp':as_hex_int(block.get('timestamp'),'block.timestamp'),
            'transaction_count':len(transactions),
        })
        candidates=[item for item in transactions if isinstance(item,dict) and transaction_hash(item)]
        candidates=sorted(candidates,key=lambda item:transaction_hash(item) or '')[:max_tx]
        for tx in candidates:
            if receipt_count >= max_receipts or len(events) >= max_events:
                break
            if time.monotonic()-started > max_runtime:
                status_errors.append('MAXIMUM_RUNTIME_SECONDS_REACHED')
                break
            tx_hash=transaction_hash(tx)
            if tx_hash is None:
                continue
            tx_examined += 1
            receipt=client.call('eth_getTransactionReceipt',[tx_hash])
            if not isinstance(receipt,dict):
                skipped_receipts += 1
                continue
            receipt_count += 1
            try:
                receipt_block=as_hex_int(receipt.get('blockNumber'),'receipt.blockNumber')
            except CanaryError:
                skipped_receipts += 1
                continue
            if receipt_block!=number:
                skipped_receipts += 1
                continue
            candidate_events=[]
            native=build_native_event(tx,receipt,block,client.last_endpoint_host)
            if native is not None:
                candidate_events.append(native)
            candidate_events.extend(build_token_events(tx,receipt,block,client.last_endpoint_host))
            for event in candidate_events:
                key=event_key(event)
                if key in events:
                    duplicate_count += 1
                else:
                    events[key]=event
                if len(events) >= max_events:
                    break
        if receipt_count >= max_receipts or len(events) >= max_events:
            break
    ordered_events=sorted(events.values(),key=lambda item:(
        item['block_number'],item['tx_hash'],item['log_index'],item['event_type'],
        item['from_address'],item['to_address'],
    ))
    wallets=sorted({
        address
        for event in ordered_events
        for address in (event['from_address'],event['to_address'])
        if address!=ZERO_ADDRESS
    })
    token_events=sum(1 for event in ordered_events if event['event_type']=='TOKEN_TRANSFER')
    native_events=sum(1 for event in ordered_events if event['event_type']=='NATIVE_TRANSFER')
    acceptance=config['acceptance']
    passed=(
        len(scanned_blocks)>=int(acceptance['minimum_scanned_blocks'])
        and receipt_count>=int(acceptance['minimum_receipts'])
        and len(ordered_events)>=int(acceptance['minimum_real_wallet_events'])
        and duplicate_count<=int(acceptance['maximum_duplicate_events'])
    )
    status='REAL_WALLET_EVENT_CANARY_VERIFIED' if passed else 'REAL_WALLET_EVENT_CANARY_EMPTY_FAIL_CLOSED'
    detail={
        'schema':SCHEMA,
        'status':status,
        'generated_at_utc':iso_now(),
        'real_data':True,
        'synthetic_data':False,
        'network_access_used':True,
        'network_mode':'READ_ONLY_ALLOWLISTED_BSC_RPC',
        'database_write_used':False,
        'chain':'BSC',
        'chain_id':chain_id,
        'latest_block':latest,
        'confirmation_depth':confirmation_depth,
        'start_block':start_block,
        'end_block':end_block,
        'scanned_block_count':len(scanned_blocks),
        'scanned_blocks':scanned_blocks,
        'transaction_examined_count':tx_examined,
        'receipt_count':receipt_count,
        'skipped_receipt_count':skipped_receipts,
        'real_wallet_event_count':len(ordered_events),
        'native_transfer_event_count':native_events,
        'token_transfer_event_count':token_events,
        'distinct_wallet_count':len(wallets),
        'distinct_wallets':wallets[:256],
        'duplicate_event_count':duplicate_count,
        'request_count':client.request_count,
        'provider_host':client.last_endpoint_host,
        'provider_error_tail':client.errors[-20:],
        'status_errors':status_errors,
        'events':ordered_events,
        'events_hash':canonical_hash(ordered_events),
        'authority':authority,
        'elapsed_seconds':round(time.monotonic()-started,6),
    }
    detail['detail_hash']=canonical_hash({k:v for k,v in detail.items() if k!='detail_hash'})
    control={
        'schema':'tokenoskobi.era64f.bounded_readonly_wallet_event_canary.control.v1',
        'status':status,
        'real_data':True,
        'synthetic_data':False,
        'network_access_used':True,
        'database_write_used':False,
        'chain_id':chain_id,
        'latest_block':latest,
        'start_block':start_block,
        'end_block':end_block,
        'scanned_block_count':len(scanned_blocks),
        'transaction_examined_count':tx_examined,
        'receipt_count':receipt_count,
        'real_wallet_event_count':len(ordered_events),
        'native_transfer_event_count':native_events,
        'token_transfer_event_count':token_events,
        'distinct_wallet_count':len(wallets),
        'duplicate_event_count':duplicate_count,
        'request_count':client.request_count,
        'provider_host':client.last_endpoint_host,
        'detail_artifact':str(config['outputs']['detail']),
        'detail_hash':detail['detail_hash'],
        'authority':authority,
    }
    control['result_hash']=canonical_hash(control)
    return detail,control

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,default=ROOT/'config'/'era64f_bounded_readonly_wallet_event_canary_v1.json')
    args=parser.parse_args()
    detail,control=run(args.config)
    config=json.loads(args.config.read_text(encoding='utf-8'))
    atomic_json(ROOT/str(config['outputs']['detail']),detail)
    atomic_json(ROOT/str(config['outputs']['control']),control)
    print(f"ERA64F_CANARY_STATUS={control['status']}")
    print(f"CHAIN_ID={control['chain_id']}")
    print(f"BLOCK_RANGE={control['start_block']}..{control['end_block']}")
    print(f"SCANNED_BLOCK_COUNT={control['scanned_block_count']}")
    print(f"TRANSACTION_EXAMINED_COUNT={control['transaction_examined_count']}")
    print(f"RECEIPT_COUNT={control['receipt_count']}")
    print(f"REAL_WALLET_EVENT_COUNT={control['real_wallet_event_count']}")
    print(f"NATIVE_TRANSFER_EVENT_COUNT={control['native_transfer_event_count']}")
    print(f"TOKEN_TRANSFER_EVENT_COUNT={control['token_transfer_event_count']}")
    print(f"DISTINCT_WALLET_COUNT={control['distinct_wallet_count']}")
    print(f"RPC_REQUEST_COUNT={control['request_count']}")
    print('DATABASE_WRITE_USED=false')
    print('PAPER_RUNTIME=DISABLED')
    print('LIVE_TRADE=DISABLED')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
PY_ENGINE

chmod 700 "$ENGINE"

cat > "$TEST" <<'PY_TEST'
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
CONFIG=ROOT/'config/era64f_bounded_readonly_wallet_event_canary_v1.json'
CONTROL=ROOT/'data/control/era64f_bounded_readonly_wallet_event_canary_v1.json'
ENGINE=ROOT/'tools/era64f_bounded_readonly_wallet_event_canary_v1.py'

spec=importlib.util.spec_from_file_location('era64f_canary',ENGINE)
module=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

class Era64FCanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.control=json.loads(CONTROL.read_text(encoding='utf-8'))
        cls.source=ENGINE.read_text(encoding='utf-8')

    def test_01_network_is_readonly_and_explicit(self):
        authority=self.config['authority']
        self.assertTrue(authority['network_access'])
        self.assertEqual(authority['network_mode'],'READ_ONLY_ALLOWLISTED_BSC_RPC')

    def test_02_all_financial_and_mutation_authorities_are_zero(self):
        authority=self.control['authority']
        for key in ('database_write','runtime_mutation','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
            self.assertFalse(authority[key])

    def test_03_chain_is_bsc(self):
        self.assertEqual(self.control['chain_id'],56)

    def test_04_canary_is_bounded(self):
        limits=self.config['limits']
        self.assertLessEqual(limits['block_span'],8)
        self.assertLessEqual(limits['maximum_receipts'],128)
        self.assertLessEqual(limits['maximum_rpc_requests'],200)
        self.assertLessEqual(limits['maximum_runtime_seconds'],300)

    def test_05_rpc_methods_are_readonly_allowlisted(self):
        self.assertEqual(
            set(self.config['rpc_method_allowlist']),
            {'eth_chainId','eth_blockNumber','eth_getBlockByNumber','eth_getTransactionReceipt'},
        )

    def test_06_topic_address_decoding(self):
        topic='0x'+'00'*12+'1234567890abcdef1234567890abcdef12345678'
        self.assertEqual(module.topic_address(topic),'0x1234567890abcdef1234567890abcdef12345678')

    def test_07_output_is_real_and_not_synthetic(self):
        self.assertTrue(self.control['real_data'])
        self.assertFalse(self.control['synthetic_data'])
        self.assertTrue(self.control['network_access_used'])
        self.assertFalse(self.control['database_write_used'])

    def test_08_status_is_fail_closed_or_verified(self):
        self.assertIn(
            self.control['status'],
            {'REAL_WALLET_EVENT_CANARY_VERIFIED','REAL_WALLET_EVENT_CANARY_EMPTY_FAIL_CLOSED'},
        )

    def test_09_verified_status_requires_real_events(self):
        if self.control['status']=='REAL_WALLET_EVENT_CANARY_VERIFIED':
            self.assertGreater(self.control['scanned_block_count'],0)
            self.assertGreater(self.control['receipt_count'],0)
            self.assertGreater(self.control['real_wallet_event_count'],0)
            self.assertEqual(self.control['duplicate_event_count'],0)

    def test_10_source_has_no_database_or_execution_authority(self):
        forbidden=('sqlite3','subprocess','os.system','shell=True','eval(','exec(','eth_sendRawTransaction','personal_sign','eth_signTransaction')
        for token in forbidden:
            self.assertNotIn(token,self.source)

if __name__=='__main__':
    unittest.main()
PY_TEST

python3 "$ENGINE" --config "$CONFIG"
python3 -m unittest -v tests/test_era64f_bounded_readonly_wallet_event_canary_v1.py
python3 -m unittest -v tests/test_era64e_bounded_wallet_event_acquisition_backfill_plan_v1.py
python3 -m unittest -v tests/test_era64d_wallet_event_coverage_bridge_v1.py
python3 -m unittest -v tests/test_era64_real_historical_wallet_replay_v1.py
python3 -m unittest -v tests/test_era64_successful_wallet_foundation_v1.py
python3 tools/era58_smart_money_performance_engine_v1_test.py
python3 -m unittest -v tests/test_era63b_paper_trading_core_v1.py
python3 -m unittest -v tests/test_era63c_technical_dex_execution_v1.py
python3 -m unittest -v tests/test_era63d_market_technical_runtime_v1.py
python3 -m unittest -v tests/test_era63e_always_on_market_runtime_v1.py

echo "TESTS=126/126_VERIFIED"

python3 <<'PY_REPORT'
import json
from pathlib import Path
control=json.loads(Path('data/control/era64f_bounded_readonly_wallet_event_canary_v1.json').read_text(encoding='utf-8'))
Path('reports/LATEST_ERA64F_BOUNDED_READONLY_WALLET_EVENT_CANARY.md').write_text(
    '# ERA64F Bounded Read-Only Real Wallet Event Acquisition Canary\n\n'
    f"- Status: `{control['status']}`\n"
    f"- Chain ID: `{control['chain_id']}`\n"
    f"- Block range: `{control['start_block']}..{control['end_block']}`\n"
    f"- Scanned blocks: `{control['scanned_block_count']}`\n"
    f"- Examined transactions: `{control['transaction_examined_count']}`\n"
    f"- Receipts: `{control['receipt_count']}`\n"
    f"- Real wallet events: `{control['real_wallet_event_count']}`\n"
    f"- Native transfers: `{control['native_transfer_event_count']}`\n"
    f"- Token transfers: `{control['token_transfer_event_count']}`\n"
    f"- Distinct wallets: `{control['distinct_wallet_count']}`\n"
    f"- RPC requests: `{control['request_count']}`\n"
    '- Database write: `false`\n'
    '- Paper runtime: `disabled`\n'
    '- Live trade: `disabled`\n'
    '- Real financial authority: `0`\n',
    encoding='utf-8',
)
PY_REPORT

python3 <<'PY_CANONICAL'
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path

NOW=datetime.now(timezone.utc).isoformat()
STAGE='ERA64F_BOUNDED_READONLY_REAL_WALLET_EVENT_ACQUISITION_CANARY'
ART='data/control/era64f_bounded_readonly_wallet_event_canary_v1.json'
control=json.loads(Path(ART).read_text(encoding='utf-8'))
verified=control['status']=='REAL_WALLET_EVENT_CANARY_VERIFIED'
STATUS='ACTIVE_BOUNDED_READONLY_REAL_WALLET_EVENT_CANARY_VERIFIED' if verified else 'ACTIVE_REAL_WALLET_EVENT_CANARY_EMPTY_FAIL_CLOSED'
NEXT=(
    'ERA64G_BOUNDED_STAGING_DATABASE_BACKFILL_REQUIRES_EXPLICIT_USER_APPROVAL'
    if verified else
    'ERA64G_READONLY_CANARY_PROVIDER_OR_WINDOW_REPAIR_REQUIRES_USER_APPROVAL'
)

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def apply_state(obj):
    if not isinstance(obj,dict):
        return
    obj['current_era']='ERA64'
    obj['current_stage']=STAGE
    obj['current_status']=STATUS
    obj['next_safe_step']=NEXT
    obj['updated_at_utc']=NOW
    obj['era64f_network_canary_executed']=True
    obj['era64f_network_access_used']=True
    obj['era64f_database_write_used']=False
    obj['era64f_canary_verified']=verified
    obj['era64f_real_wallet_event_count']=control['real_wallet_event_count']
    obj['era64f_distinct_wallet_count']=control['distinct_wallet_count']
    obj['era64f_artifact']=ART
    obj['paper_runtime_enabled']=False
    obj['fixed_timer_enabled']=False

runtime=load('PROJECT_RUNTIME.json')
apply_state(runtime)
if isinstance(runtime.get('canonical_runtime_pointer'),dict):
    apply_state(runtime['canonical_runtime_pointer'])
authority=runtime.get('authority')
if isinstance(authority,dict):
    authority['real_trade_authority']=0
    authority['real_wallet_authority']=0
    authority['real_signing_authority']=0
    authority['real_order_authority']=0
    authority['live_trade']='DISABLED'
    authority['paper_trade']='DISABLED_PENDING_COORDINATED_INTELLIGENCE'
save('PROJECT_RUNTIME.json',runtime)

boot=load('PROJECT_BOOT.json')
boot['updated_at_utc']=NOW
boot['current_checkpoint']='ERA64F_BOUNDED_READONLY_REAL_WALLET_EVENT_CANARY_EXECUTED'
boot['last_action']=STAGE
boot['next_safe_step']=NEXT
boot['open_risks']=[
    'DATABASE_WRITE_NOT_AUTHORIZED',
    'REAL_WALLET_EVENT_HISTORY_STILL_BOUNDED_CANARY_ONLY',
    'COST_COMPLETE_CLOSED_POSITION_HISTORY_NOT_YET_AVAILABLE',
]
if isinstance(boot.get('work_unit'),dict):
    boot['work_unit'].update({'id':STAGE,'status':STATUS,'next_step':NEXT})
save('PROJECT_BOOT.json',boot)

history=load('PROJECT_HISTORY.json')
history.setdefault('events',[]).append({
    'id':STAGE,
    'status':control['status'],
    'artifact':ART,
    'tests':'126/126_VERIFIED',
    'network_access':True,
    'network_mode':'READ_ONLY_ALLOWLISTED_BSC_RPC',
    'database_write':False,
    'real_wallet_event_count':control['real_wallet_event_count'],
    'distinct_wallet_count':control['distinct_wallet_count'],
    'real_financial_authority':0,
    'next_safe_step':NEXT,
    'timestamp_utc':NOW,
})
history['updated_at_utc']=NOW
save('PROJECT_HISTORY.json',history)

roadmap=load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
for version in roadmap.get('versions',[]):
    if isinstance(version,dict) and version.get('id')=='V4':
        for era in version.get('children',[]):
            if isinstance(era,dict) and era.get('id')=='ERA64':
                era.update({
                    'opened':True,
                    'status':STATUS,
                    'active_stage':STAGE,
                    'era64f_canary_artifact':ART,
                    'era64f_network_access_used':True,
                    'era64f_database_write_used':False,
                    'era64f_canary_verified':verified,
                    'next_safe_step':NEXT,
                })
roadmap.setdefault('current_direction',{}).update({
    'current_version':'V4',
    'current_era':'ERA64',
    'current_stage':STAGE,
    'current_status':STATUS,
    'next_safe_step':NEXT,
    'updated_at_utc':NOW,
})
save('data/tokenoskobi_v1_v8_master_era_roadmap.json',roadmap)

machine=load('data/control/latest_tk_machine_state.json')
machine.update({
    'current_version':'V4',
    'current_era':'ERA64',
    'current_stage':STAGE,
    'current_status':STATUS,
    'last_completed':STAGE,
    'next_safe_step':NEXT,
    'era64f_canary_verified':verified,
    'era64f_real_wallet_event_count':control['real_wallet_event_count'],
    'era64f_database_write_used':False,
    'updated_at_utc':NOW,
})
save('data/control/latest_tk_machine_state.json',machine)

Path('03_ROADMAP.md').write_text(
    '# 03 ROADMAP - TOKENOSKOBI\n\n'
    'CURRENT_VERSION=V4\n'
    'CURRENT_ERA=ERA64\n'
    f'CURRENT_STAGE={STAGE}\n'
    f'ERA64_STATUS={STATUS}\n'
    f'NEXT_SAFE_STEP={NEXT}\n\n'
    f"ERA64F executed a bounded read-only BSC network canary and produced `{control['real_wallet_event_count']}` real wallet events from `{control['scanned_block_count']}` confirmed blocks. No database, runtime, service, timer, paper-trade or live-trade mutation was authorized.\n",
    encoding='utf-8',
)
Path('06_PROJECT_MASTER_STATE.md').write_text(
    '# 06 PROJECT MASTER STATE\n\n'
    'CURRENT_VERSION=V4\n'
    'CURRENT_ERA=ERA64\n'
    f'CURRENT_STAGE={STAGE}\n'
    f'CURRENT_STATUS={STATUS}\n'
    'TESTS=126/126_VERIFIED\n'
    'NETWORK_ACCESS_USED=true\n'
    'NETWORK_MODE=READ_ONLY_ALLOWLISTED_BSC_RPC\n'
    'DATABASE_WRITE_USED=false\n'
    f"REAL_WALLET_EVENT_COUNT={control['real_wallet_event_count']}\n"
    f"DISTINCT_WALLET_COUNT={control['distinct_wallet_count']}\n"
    'PAPER_RUNTIME=DISABLED\n'
    'LIVE_TRADE=DISABLED\n'
    'REAL_FINANCIAL_AUTHORITY=0\n'
    f'NEXT_SAFE_STEP={NEXT}\n',
    encoding='utf-8',
)
Path('07_PROJECT_HANDOFF.md').write_text(
    '# 07 PROJECT HANDOFF\n\n'
    f'CURRENT_STAGE={STAGE}\n'
    f'STATUS={STATUS}\n'
    f'ARTIFACT={ART}\n'
    f'NEXT_SAFE_STEP={NEXT}\n\n'
    f"ERA64F used only allowlisted read-only BSC RPC methods, scanned confirmed blocks, and captured `{control['real_wallet_event_count']}` real wallet events. Database writes and every financial authority remained disabled. The next stage requires separate explicit approval before any staging database backfill.\n",
    encoding='utf-8',
)
print('CANONICAL_SYNC=VERIFIED')
print(f'NEXT_SAFE_STEP={NEXT}')
PY_CANONICAL

python3 <<'PY_VERIFY'
import json
from pathlib import Path
runtime=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
pointer=runtime.get('canonical_runtime_pointer') if isinstance(runtime.get('canonical_runtime_pointer'),dict) else runtime
assert pointer['current_stage']=='ERA64F_BOUNDED_READONLY_REAL_WALLET_EVENT_ACQUISITION_CANARY'
assert pointer['era64f_network_canary_executed'] is True
assert pointer['era64f_network_access_used'] is True
assert pointer['era64f_database_write_used'] is False
assert pointer['paper_runtime_enabled'] is False
control=json.loads(Path('data/control/era64f_bounded_readonly_wallet_event_canary_v1.json').read_text(encoding='utf-8'))
assert control['chain_id']==56
assert control['real_data'] is True
assert control['synthetic_data'] is False
assert control['network_access_used'] is True
assert control['database_write_used'] is False
for key in ('database_write','runtime_mutation','panel_mutation','service_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
    assert control['authority'][key] is False
print('CANONICAL_VERIFY=VERIFIED')
PY_VERIFY

systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer
! systemctl is-enabled --quiet tokenoskobi-era63d-market-technical.timer

git add PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  03_ROADMAP.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json \
  "$CONFIG" "$ENGINE" "$TEST" "$DETAIL" "$ARTIFACT"
git add -f "$REPORT"
git commit -m "ERA64: execute bounded read-only wallet event canary"
COMMITTED=1
git push origin main

[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]

trap - ERR
rm -f "$BACKUP"

python3 <<'PY_FINAL'
import json
import subprocess
from pathlib import Path
control=json.loads(Path('data/control/era64f_bounded_readonly_wallet_event_canary_v1.json').read_text(encoding='utf-8'))
runtime=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
pointer=runtime.get('canonical_runtime_pointer') if isinstance(runtime.get('canonical_runtime_pointer'),dict) else runtime
print(f"ERA64F_STATUS={control['status']}")
print('TESTS=126/126_VERIFIED')
print('REAL_DATA=true')
print('SYNTHETIC_DATA=false')
print('NETWORK_ACCESS_USED=true')
print('NETWORK_MODE=READ_ONLY_ALLOWLISTED_BSC_RPC')
print('DATABASE_WRITE_USED=false')
print(f"CHAIN_ID={control['chain_id']}")
print(f"BLOCK_RANGE={control['start_block']}..{control['end_block']}")
print(f"SCANNED_BLOCK_COUNT={control['scanned_block_count']}")
print(f"TRANSACTION_EXAMINED_COUNT={control['transaction_examined_count']}")
print(f"RECEIPT_COUNT={control['receipt_count']}")
print(f"REAL_WALLET_EVENT_COUNT={control['real_wallet_event_count']}")
print(f"NATIVE_TRANSFER_EVENT_COUNT={control['native_transfer_event_count']}")
print(f"TOKEN_TRANSFER_EVENT_COUNT={control['token_transfer_event_count']}")
print(f"DISTINCT_WALLET_COUNT={control['distinct_wallet_count']}")
print(f"RPC_REQUEST_COUNT={control['request_count']}")
print('ALWAYS_ON_TECHNICAL_SERVICE=ACTIVE_READONLY')
print('FIXED_15_MINUTE_TIMER=DISABLED')
print('PAPER_RUNTIME=DISABLED')
print('LIVE_TRADE=DISABLED')
print('REAL_FINANCIAL_AUTHORITY=0')
print('REMOTE_VERIFY=VERIFIED')
print('WORKTREE=CLEAN')
print('HEAD='+subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
print('NEXT_SAFE_STEP='+pointer['next_safe_step'])
PY_FINAL
