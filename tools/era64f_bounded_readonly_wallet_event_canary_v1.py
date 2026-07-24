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
