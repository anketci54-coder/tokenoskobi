#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
TRANSFER_TOPIC='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ZERO_ADDRESS='0x0000000000000000000000000000000000000000'
ADDRESS_LENGTH=42
HASH_LENGTH=66

class Era64IError(RuntimeError):
    pass

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def canonical_hash(value: Any) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def file_hash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def atomic_json(path: Path,value: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    json.loads(temp.read_text(encoding='utf-8'))
    temp.replace(path)

def as_hex_int(value: Any,name: str) -> int:
    try:
        number=int(str(value),16)
    except (TypeError,ValueError) as exc:
        raise Era64IError(f'{name}:INVALID_HEX') from exc
    if number<0:
        raise Era64IError(f'{name}:NEGATIVE')
    return number

def normalize_address(value: Any) -> str | None:
    text=str(value or '').strip().lower()
    if not text.startswith('0x') or len(text)!=ADDRESS_LENGTH:
        return None
    try:
        int(text[2:],16)
    except ValueError:
        return None
    return text

def normalize_hash(value: Any) -> str | None:
    text=str(value or '').strip().lower()
    if not text.startswith('0x') or len(text)!=HASH_LENGTH:
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

def bounded_int(value: Any,name: str,minimum: int,maximum: int) -> int:
    try:
        number=int(value)
    except (TypeError,ValueError) as exc:
        raise Era64IError(f'{name}:NOT_INTEGER') from exc
    if number<minimum or number>maximum or not math.isfinite(float(number)):
        raise Era64IError(f'{name}:OUT_OF_BOUNDS')
    return number

def validate_config(config: dict[str,Any],provider: dict[str,Any]) -> None:
    if config.get('schema')!='tokenoskobi.era64i.bounded_historical_wallet_event_backfill.config.v1':
        raise Era64IError('CONFIG_SCHEMA_MISMATCH')
    if config.get('mode')!='BOUNDED_HISTORICAL_BSC_TRANSFER_LOG_BACKFILL_TO_DEDICATED_STAGING':
        raise Era64IError('CONFIG_MODE_INVALID')
    chain=config.get('chain')
    if not isinstance(chain,dict) or int(chain.get('chain_id',0))!=56 or chain.get('name')!='BSC':
        raise Era64IError('CHAIN_MUST_BE_BSC_56')
    if int(chain.get('confirmation_depth',0))<12:
        raise Era64IError('CONFIRMATION_DEPTH_TOO_LOW')
    if int(chain.get('historical_safety_lag_blocks',0))<128:
        raise Era64IError('HISTORICAL_SAFETY_LAG_TOO_LOW')
    if config.get('synthetic_data_allowed') is not False:
        raise Era64IError('SYNTHETIC_DATA_MUST_BE_FALSE')
    if config.get('successful_wallet_classification_authorized') is not False:
        raise Era64IError('SUCCESSFUL_WALLET_CLASSIFICATION_MUST_BE_FALSE')
    if config.get('cluster_inference_authorized') is not False:
        raise Era64IError('CLUSTER_INFERENCE_MUST_BE_FALSE')
    authority=config.get('authority')
    if not isinstance(authority,dict):
        raise Era64IError('AUTHORITY_NOT_OBJECT')
    if authority.get('network_access') is not True:
        raise Era64IError('NETWORK_ACCESS_MUST_BE_EXPLICIT_TRUE')
    if authority.get('network_mode')!='READ_ONLY_ALLOWLISTED_BSC_RPC':
        raise Era64IError('NETWORK_MODE_INVALID')
    if authority.get('staging_database_write') is not True:
        raise Era64IError('STAGING_DATABASE_WRITE_MUST_BE_TRUE')
    for key in ('production_database_write','runtime_service_mutation','panel_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
        if authority.get(key) is not False:
            raise Era64IError(f'{key}:MUST_BE_FALSE')
    methods=config.get('rpc_method_allowlist')
    if set(methods or [])!={'eth_chainId','eth_blockNumber','eth_getTransactionReceipt','eth_getBlockByNumber'}:
        raise Era64IError('RPC_METHOD_ALLOWLIST_INVALID')
    tokens=config.get('scope_tokens')
    if not isinstance(tokens,list) or not (1<=len(tokens)<=4):
        raise Era64IError('SCOPE_TOKEN_COUNT_INVALID')
    normalized=[normalize_address(item) for item in tokens]
    if any(item is None for item in normalized) or len(set(normalized))!=len(normalized):
        raise Era64IError('SCOPE_TOKENS_INVALID')
    limits=config.get('limits')
    if not isinstance(limits,dict):
        raise Era64IError('LIMITS_NOT_OBJECT')
    span=bounded_int(limits.get('historical_block_span'),'historical_block_span',256,4096)
    chunk=bounded_int(limits.get('log_chunk_size'),'log_chunk_size',1,64)
    if span%chunk!=0:
        raise Era64IError('BLOCK_SPAN_MUST_DIVIDE_BY_CHUNK')
    bounded_int(limits.get('maximum_sampled_blocks_per_chunk'),'maximum_sampled_blocks_per_chunk',1,4)
    bounded_int(limits.get('maximum_wallet_scope'),'maximum_wallet_scope',1,32)
    bounded_int(limits.get('maximum_receipts_per_sampled_block'),'maximum_receipts_per_sampled_block',1,24)
    bounded_int(limits.get('maximum_logs_per_sampled_block'),'maximum_logs_per_sampled_block',1,16)
    bounded_int(limits.get('maximum_events'),'maximum_events',100,2000)
    bounded_int(limits.get('maximum_distinct_blocks'),'maximum_distinct_blocks',16,256)
    bounded_int(limits.get('maximum_rpc_requests'),'maximum_rpc_requests',100,1200)
    bounded_int(limits.get('maximum_runtime_seconds'),'maximum_runtime_seconds',120,1800)
    bounded_int(limits.get('request_timeout_seconds'),'request_timeout_seconds',2,30)
    bounded_int(limits.get('retries_per_endpoint'),'retries_per_endpoint',0,2)
    if not isinstance(provider,dict) or provider.get('schema')!='tokenoskobi.era63e.always_on_market_runtime_config.v1':
        raise Era64IError('PROVIDER_CONFIG_INVALID')
    rpc=provider.get('rpc')
    if not isinstance(rpc,dict) or int(rpc.get('chain_id',0))!=56:
        raise Era64IError('PROVIDER_CHAIN_INVALID')
    endpoints=rpc.get('endpoints')
    allowed=set(rpc.get('allowed_hosts') or [])
    if not isinstance(endpoints,list) or len(endpoints)<2:
        raise Era64IError('PROVIDER_ENDPOINTS_INSUFFICIENT')
    for endpoint in endpoints:
        parsed=urllib.parse.urlparse(str(endpoint))
        if parsed.scheme!='https' or parsed.hostname not in allowed:
            raise Era64IError('PROVIDER_ENDPOINT_NOT_ALLOWLISTED_HTTPS')

def ensure_staging_path(path: Path) -> Path:
    resolved=path.resolve()
    allowed=(ROOT/'runtime'/'era64i'/'historical_wallet_transfer_staging_v1.sqlite3').resolve()
    if resolved!=allowed:
        raise Era64IError('DATABASE_PATH_NOT_DEDICATED_ERA64I_STAGING')
    return resolved

class RpcClient:
    def __init__(self,config: dict[str,Any],provider: dict[str,Any]):
        rpc=provider['rpc']
        self.endpoints=[str(item).rstrip('/') for item in rpc['endpoints']]
        self.allowed_hosts=set(rpc['allowed_hosts'])
        limits=config['limits']
        self.timeout=float(limits['request_timeout_seconds'])
        self.retries=int(limits['retries_per_endpoint'])
        self.backoff=float(limits['retry_backoff_seconds'])
        self.maximum_requests=int(limits['maximum_rpc_requests'])
        self.allowed_methods=set(config['rpc_method_allowlist'])
        self.request_count=0
        self.endpoint_index=0
        self.last_endpoint_host=None
        self.errors:list[str]=[]

    def call(self,method: str,params: list[Any]) -> Any:
        if method not in self.allowed_methods:
            raise Era64IError(f'RPC_METHOD_NOT_ALLOWLISTED:{method}')
        if self.request_count>=self.maximum_requests:
            raise Era64IError('RPC_REQUEST_BUDGET_EXCEEDED')
        last_error=''
        count=len(self.endpoints)
        for offset in range(count):
            endpoint=self.endpoints[(self.endpoint_index+offset)%count]
            parsed=urllib.parse.urlparse(endpoint)
            if parsed.scheme!='https' or parsed.hostname not in self.allowed_hosts:
                continue
            for attempt in range(self.retries+1):
                if self.request_count>=self.maximum_requests:
                    raise Era64IError('RPC_REQUEST_BUDGET_EXCEEDED')
                self.request_count+=1
                payload=json.dumps({'jsonrpc':'2.0','id':self.request_count,'method':method,'params':params}).encode('utf-8')
                request=urllib.request.Request(
                    endpoint,
                    data=payload,
                    headers={'Content-Type':'application/json','User-Agent':'Tokenoskobi-ERA64I/1.0 bounded-historical-readonly'},
                    method='POST',
                )
                try:
                    with urllib.request.urlopen(request,timeout=self.timeout) as response:
                        result=json.loads(response.read().decode('utf-8'))
                    if not isinstance(result,dict):
                        raise Era64IError('RPC_RESPONSE_NOT_OBJECT')
                    if result.get('error'):
                        raise Era64IError(f"RPC_ERROR:{result['error']}")
                    if 'result' not in result:
                        raise Era64IError('RPC_RESULT_MISSING')
                    self.endpoint_index=(self.endpoint_index+offset+1)%count
                    self.last_endpoint_host=parsed.hostname
                    return result['result']
                except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError,OSError,json.JSONDecodeError,Era64IError) as exc:
                    last_error=f'{type(exc).__name__}:{exc}'
                    self.errors.append(f'{parsed.hostname}:{method}:{last_error}')
                    if attempt<self.retries:
                        time.sleep(min(self.backoff*(2**attempt),2.0))
        raise Era64IError(f'ALL_RPC_ENDPOINTS_FAILED:{method}:{last_error}')

def evenly_select(items: list[Any],limit: int) -> list[Any]:
    if limit<=0 or not items:
        return []
    if len(items)<=limit:
        return list(items)
    if limit==1:
        return [items[len(items)//2]]
    indices=[]
    for index in range(limit):
        position=round(index*(len(items)-1)/(limit-1))
        if position not in indices:
            indices.append(position)
    return [items[index] for index in indices]

def transaction_hash(item: Any) -> str | None:
    if isinstance(item,dict):
        return normalize_hash(item.get('hash'))
    return normalize_hash(item)

def transaction_wallet_priority(item: Any,wallets: set[str]) -> tuple[int,str]:
    tx_hash=transaction_hash(item) or '0x'+'f'*64
    if not isinstance(item,dict):
        return (1,tx_hash)
    src=normalize_address(item.get('from'))
    dst=normalize_address(item.get('to'))
    return (0 if src in wallets or dst in wallets else 1,tx_hash)

def fetch_logs_for_chunk(
    client: RpcClient,
    tokens: list[str],
    wallets: list[str],
    start: int,
    end: int,
    maximum_receipts: int,
) -> tuple[list[dict[str,Any]],str|None,str]:
    if not wallets:
        raise Era64IError('WALLET_SCOPE_EMPTY')
    sampled_block=start+(end-start)//2
    block=client.call('eth_getBlockByNumber',[hex(sampled_block),True])
    if not isinstance(block,dict):
        raise Era64IError('SAMPLED_BLOCK_NOT_OBJECT')
    if as_hex_int(block.get('number'),'sampled_block.number')!=sampled_block:
        raise Era64IError('SAMPLED_BLOCK_NUMBER_MISMATCH')
    transactions=block.get('transactions')
    if not isinstance(transactions,list):
        raise Era64IError('SAMPLED_BLOCK_TRANSACTIONS_NOT_LIST')
    wallet_set={item for item in wallets if normalize_address(item) is not None}
    ordered=sorted(transactions,key=lambda item:transaction_wallet_priority(item,wallet_set))
    prioritized=[item for item in ordered if transaction_wallet_priority(item,wallet_set)[0]==0]
    remainder=[item for item in ordered if transaction_wallet_priority(item,wallet_set)[0]!=0]
    chosen=prioritized[:maximum_receipts]
    remaining=maximum_receipts-len(chosen)
    if remaining>0:
        chosen.extend(evenly_select(remainder,remaining))
    token_set=set(tokens)
    merged=[]
    for transaction in chosen:
        tx_hash=transaction_hash(transaction)
        if tx_hash is None:
            continue
        receipt=client.call('eth_getTransactionReceipt',[tx_hash])
        if not isinstance(receipt,dict):
            raise Era64IError('TRANSACTION_RECEIPT_NOT_OBJECT')
        logs=receipt.get('logs')
        if not isinstance(logs,list):
            raise Era64IError('TRANSACTION_RECEIPT_LOGS_NOT_LIST')
        for item in logs:
            if not isinstance(item,dict):
                continue
            token=normalize_address(item.get('address'))
            topics=item.get('topics')
            if token not in token_set:
                continue
            if not isinstance(topics,list) or len(topics)<3 or str(topics[0]).lower()!=TRANSFER_TOPIC:
                continue
            merged.append(item)
    unique={}
    for item in merged:
        key=(
          str(item.get('blockHash') or '').lower(),
          str(item.get('transactionHash') or '').lower(),
          str(item.get('logIndex') or '').lower(),
          str(item.get('address') or '').lower(),
        )
        unique.setdefault(key,item)
    return sorted(unique.values(),key=log_sort_key),client.last_endpoint_host,'FULL_BLOCK_TRANSACTION_RECEIPT_SAMPLING'

def log_sort_key(item: dict[str,Any]) -> tuple[Any,...]:
    try:
        block=as_hex_int(item.get('blockNumber'),'log.blockNumber')
        index=as_hex_int(item.get('logIndex'),'log.logIndex')
    except Era64IError:
        block=2**63-1
        index=2**63-1
    return (block,str(item.get('transactionHash') or '').lower(),index,str(item.get('address') or '').lower())

def sample_chunk_logs(logs: list[dict[str,Any]],max_blocks: int,max_logs_per_block: int) -> list[dict[str,Any]]:
    grouped:dict[int,list[dict[str,Any]]]=defaultdict(list)
    for item in sorted(logs,key=log_sort_key):
        try:
            block=as_hex_int(item.get('blockNumber'),'log.blockNumber')
        except Era64IError:
            continue
        grouped[block].append(item)
    selected_blocks=evenly_select(sorted(grouped),max_blocks)
    output=[]
    for block in selected_blocks:
        output.extend(evenly_select(grouped[block],max_logs_per_block))
    return sorted(output,key=log_sort_key)

def build_event(log: dict[str,Any],block: dict[str,Any],provider_host: str|None) -> dict[str,Any] | None:
    topics=log.get('topics')
    if not isinstance(topics,list) or len(topics)<3 or str(topics[0]).lower()!=TRANSFER_TOPIC:
        return None
    token=normalize_address(log.get('address'))
    src=topic_address(topics[1])
    dst=topic_address(topics[2])
    tx_hash=normalize_hash(log.get('transactionHash'))
    block_hash=normalize_hash(log.get('blockHash'))
    if token is None or src is None or dst is None or tx_hash is None or block_hash is None:
        return None
    block_number=as_hex_int(log.get('blockNumber'),'log.blockNumber')
    if block_number!=as_hex_int(block.get('number'),'block.number'):
        raise Era64IError('LOG_BLOCK_NUMBER_MISMATCH')
    header_hash=normalize_hash(block.get('hash'))
    if header_hash is None or header_hash!=block_hash:
        raise Era64IError('LOG_BLOCK_HASH_MISMATCH')
    log_index=as_hex_int(log.get('logIndex'),'log.logIndex')
    amount=as_hex_int(log.get('data') or '0x0','log.data')
    if amount<=0:
        return None
    timestamp=as_hex_int(block.get('timestamp'),'block.timestamp')
    base={
      'chain':'BSC','chain_id':56,'event_type':'TOKEN_TRANSFER',
      'token_address':token,'from_address':src,'to_address':dst,
      'amount_raw':str(amount),'tx_hash':tx_hash,'log_index':log_index,
      'block_number':block_number,'block_hash':block_hash,
      'block_time_utc':datetime.fromtimestamp(timestamp,tz=timezone.utc).isoformat(),
      'source_provider_host':str(provider_host or '').strip().lower(),
      'evidence_kind':'REAL_BSC_ERC20_TRANSFER_LOG_HISTORICAL',
      'cost_enriched':False,'receipt_enriched':False,
    }
    if not base['source_provider_host']:
        raise Era64IError('SOURCE_PROVIDER_HOST_MISSING')
    base['evidence_hash']=canonical_hash(base)
    base['event_uid']=canonical_hash({key:base[key] for key in ('chain_id','tx_hash','log_index','token_address','from_address','to_address','amount_raw')})
    base['raw_log_json']=json.dumps(log,sort_keys=True,separators=(',',':'),ensure_ascii=True)
    return base

def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS era64i_historical_wallet_transfer_staging_v1 (
      event_uid TEXT PRIMARY KEY,
      chain TEXT NOT NULL CHECK(chain='BSC'),
      chain_id INTEGER NOT NULL CHECK(chain_id=56),
      event_type TEXT NOT NULL CHECK(event_type='TOKEN_TRANSFER'),
      token_address TEXT NOT NULL,
      from_address TEXT NOT NULL,
      to_address TEXT NOT NULL,
      amount_raw TEXT NOT NULL,
      tx_hash TEXT NOT NULL,
      log_index INTEGER NOT NULL,
      block_number INTEGER NOT NULL,
      block_hash TEXT NOT NULL,
      block_time_utc TEXT NOT NULL,
      source_provider_host TEXT NOT NULL,
      evidence_kind TEXT NOT NULL,
      evidence_hash TEXT NOT NULL,
      cost_enriched INTEGER NOT NULL CHECK(cost_enriched=0),
      receipt_enriched INTEGER NOT NULL CHECK(receipt_enriched=0),
      imported_at_utc TEXT NOT NULL,
      raw_log_json TEXT NOT NULL,
      UNIQUE(chain_id,tx_hash,log_index)
    );
    CREATE INDEX IF NOT EXISTS era64i_transfer_block_idx
      ON era64i_historical_wallet_transfer_staging_v1(block_number,tx_hash,log_index);
    CREATE INDEX IF NOT EXISTS era64i_transfer_from_idx
      ON era64i_historical_wallet_transfer_staging_v1(from_address,block_number);
    CREATE INDEX IF NOT EXISTS era64i_transfer_to_idx
      ON era64i_historical_wallet_transfer_staging_v1(to_address,block_number);
    CREATE INDEX IF NOT EXISTS era64i_transfer_token_idx
      ON era64i_historical_wallet_transfer_staging_v1(token_address,block_number);
    CREATE TABLE IF NOT EXISTS era64i_historical_import_batch_v1 (
      batch_uid TEXT PRIMARY KEY,
      start_block INTEGER NOT NULL,
      end_block INTEGER NOT NULL,
      scanned_chunk_count INTEGER NOT NULL,
      sampled_block_count INTEGER NOT NULL,
      selected_event_count INTEGER NOT NULL,
      inserted_event_count INTEGER NOT NULL,
      deduplicated_event_count INTEGER NOT NULL,
      total_event_count_after INTEGER NOT NULL,
      event_set_hash TEXT NOT NULL,
      imported_at_utc TEXT NOT NULL
    );
    ''')

def write_events(database_path: Path,events: list[dict[str,Any]],scan: dict[str,Any]) -> dict[str,Any]:
    db=ensure_staging_path(database_path)
    db.parent.mkdir(parents=True,exist_ok=True)
    imported_at=iso_now()
    conn=sqlite3.connect(db)
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA journal_mode=DELETE')
        conn.execute('PRAGMA synchronous=FULL')
        conn.execute('BEGIN IMMEDIATE')
        create_schema(conn)
        before=int(conn.execute('SELECT COUNT(*) FROM era64i_historical_wallet_transfer_staging_v1').fetchone()[0])
        inserted=0
        for event in events:
            cursor=conn.execute('''
              INSERT OR IGNORE INTO era64i_historical_wallet_transfer_staging_v1 (
                event_uid,chain,chain_id,event_type,token_address,from_address,to_address,
                amount_raw,tx_hash,log_index,block_number,block_hash,block_time_utc,
                source_provider_host,evidence_kind,evidence_hash,cost_enriched,receipt_enriched,
                imported_at_utc,raw_log_json
              ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''',(
              event['event_uid'],event['chain'],event['chain_id'],event['event_type'],
              event['token_address'],event['from_address'],event['to_address'],event['amount_raw'],
              event['tx_hash'],event['log_index'],event['block_number'],event['block_hash'],
              event['block_time_utc'],event['source_provider_host'],event['evidence_kind'],
              event['evidence_hash'],0,0,imported_at,event['raw_log_json']
            ))
            inserted+=max(0,int(cursor.rowcount))
        after=int(conn.execute('SELECT COUNT(*) FROM era64i_historical_wallet_transfer_staging_v1').fetchone()[0])
        deduplicated=len(events)-inserted
        event_set_hash=canonical_hash([event['evidence_hash'] for event in events])
        batch_uid=canonical_hash({'start_block':scan['start_block'],'end_block':scan['end_block'],'event_set_hash':event_set_hash})
        conn.execute('''
          INSERT OR REPLACE INTO era64i_historical_import_batch_v1 (
            batch_uid,start_block,end_block,scanned_chunk_count,sampled_block_count,
            selected_event_count,inserted_event_count,deduplicated_event_count,
            total_event_count_after,event_set_hash,imported_at_utc
          ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ''',(
          batch_uid,scan['start_block'],scan['end_block'],scan['scanned_chunk_count'],
          scan['sampled_block_count'],len(events),inserted,deduplicated,after,event_set_hash,imported_at
        ))
        conn.commit()
        integrity=str(conn.execute('PRAGMA integrity_check').fetchone()[0])
        unique_count=int(conn.execute('''SELECT COUNT(*) FROM (
          SELECT chain_id,tx_hash,log_index FROM era64i_historical_wallet_transfer_staging_v1
          GROUP BY chain_id,tx_hash,log_index
        )''').fetchone()[0])
        if integrity.lower()!='ok':
            raise Era64IError(f'INTEGRITY_CHECK_FAILED:{integrity}')
        if after!=before+inserted or unique_count!=after:
            raise Era64IError('DATABASE_COUNT_OR_UNIQUENESS_INVARIANT_FAILED')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    readonly=sqlite3.connect(f'file:{db}?mode=ro',uri=True)
    try:
        readonly.execute('PRAGMA query_only=ON')
        readonly_count=int(readonly.execute('SELECT COUNT(*) FROM era64i_historical_wallet_transfer_staging_v1').fetchone()[0])
    finally:
        readonly.close()
    if readonly_count!=after:
        raise Era64IError('READONLY_VERIFY_COUNT_MISMATCH')
    return {
      'database_path':str(database_path),'database_sha256':file_hash(db),
      'database_integrity_check':integrity,'database_event_count':after,
      'inserted_event_count':inserted,'deduplicated_event_count':deduplicated,
      'event_set_hash':event_set_hash,'batch_uid':batch_uid,'imported_at_utc':imported_at,
    }

def run(config_path: Path,database_path: Path) -> tuple[dict[str,Any],dict[str,Any]]:
    started=time.monotonic()
    config=json.loads(config_path.read_text(encoding='utf-8'))
    provider=json.loads((ROOT/str(config['provider_config'])).read_text(encoding='utf-8'))
    validate_config(config,provider)
    client=RpcClient(config,provider)
    chain_id=as_hex_int(client.call('eth_chainId',[]),'eth_chainId')
    if chain_id!=56:
        raise Era64IError(f'CHAIN_ID_MISMATCH:{chain_id}')
    latest=as_hex_int(client.call('eth_blockNumber',[]),'eth_blockNumber')
    chain=config['chain']
    confirmed=latest-int(chain['confirmation_depth'])
    end_block=confirmed-int(chain['historical_safety_lag_blocks'])
    span=int(config['limits']['historical_block_span'])
    if end_block<=0 or end_block-span+1<0:
        raise Era64IError('HISTORICAL_RANGE_INVALID')
    start_block=end_block-span+1
    chunk_size=int(config['limits']['log_chunk_size'])
    max_blocks_per_chunk=int(config['limits']['maximum_sampled_blocks_per_chunk'])
    max_receipts_per_block=int(config['limits']['maximum_receipts_per_sampled_block'])
    max_logs_per_block=int(config['limits']['maximum_logs_per_sampled_block'])
    max_events=int(config['limits']['maximum_events'])
    max_blocks=int(config['limits']['maximum_distinct_blocks'])
    max_runtime=float(config['limits']['maximum_runtime_seconds'])
    tokens=[str(item).lower() for item in config['scope_tokens']]
    wallet_scope_path=ROOT/str(config['wallet_scope_artifact'])
    wallet_scope_source=json.loads(wallet_scope_path.read_text(encoding='utf-8'))
    graph=wallet_scope_source.get('relationship_graph')
    nodes=graph.get('nodes') if isinstance(graph,dict) else None
    if not isinstance(nodes,list) or not nodes:
        raise Era64IError('WALLET_SCOPE_GRAPH_NODES_EMPTY')
    ranked=sorted(
      (item for item in nodes if isinstance(item,dict) and normalize_address(item.get('address')) not in {None,ZERO_ADDRESS}),
      key=lambda item:(-int(item.get('transfer_event_count',0)),-int(item.get('counterparty_count',0)),str(item.get('address')).lower()),
    )
    maximum_wallet_scope=int(config['limits']['maximum_wallet_scope'])
    wallet_scope=[str(item['address']).lower() for item in ranked[:maximum_wallet_scope]]
    if len(wallet_scope)<1 or len(set(wallet_scope))!=len(wallet_scope):
        raise Era64IError('WALLET_SCOPE_INVALID')
    selected:dict[tuple[int,str,int],dict[str,Any]]={}
    selected_block_hosts:dict[int,str]={}
    scanned_chunks=[]
    duplicate_count=0
    filter_modes=Counter()
    raw_log_count=0
    for chunk_start in range(start_block,end_block+1,chunk_size):
        if len(selected)>=max_events:
            break
        if time.monotonic()-started>max_runtime:
            raise Era64IError('MAXIMUM_RUNTIME_SECONDS_EXCEEDED_DURING_LOG_SCAN')
        chunk_end=min(end_block,chunk_start+chunk_size-1)
        logs,host,filter_mode=fetch_logs_for_chunk(client,tokens,wallet_scope,chunk_start,chunk_end,max_receipts_per_block)
        raw_log_count+=len(logs)
        sampled=sample_chunk_logs(logs,max_blocks_per_chunk,max_logs_per_block)
        accepted_in_chunk=0
        for log in sampled:
            if len(selected)>=max_events:
                break
            try:
                block_number=as_hex_int(log.get('blockNumber'),'log.blockNumber')
                tx_hash=normalize_hash(log.get('transactionHash'))
                log_index=as_hex_int(log.get('logIndex'),'log.logIndex')
            except Era64IError:
                continue
            if tx_hash is None:
                continue
            if block_number not in selected_block_hosts and len(selected_block_hosts)>=max_blocks:
                continue
            key=(56,tx_hash,log_index)
            if key in selected:
                duplicate_count+=1
                continue
            selected[key]=log
            selected_block_hosts.setdefault(block_number,str(host or ''))
            accepted_in_chunk+=1
        filter_modes[filter_mode]+=1
        scanned_chunks.append({
          'start_block':chunk_start,'end_block':chunk_end,'raw_log_count':len(logs),
          'sampled_log_count':len(sampled),'accepted_log_count':accepted_in_chunk,
          'provider_host':host,'filter_mode':filter_mode,
        })
    block_headers={}
    for block_number in sorted(selected_block_hosts):
        if time.monotonic()-started>max_runtime:
            raise Era64IError('MAXIMUM_RUNTIME_SECONDS_EXCEEDED_DURING_BLOCK_HEADER_ENRICHMENT')
        block=client.call('eth_getBlockByNumber',[hex(block_number),False])
        if not isinstance(block,dict):
            raise Era64IError(f'BLOCK_HEADER_NOT_OBJECT:{block_number}')
        actual=as_hex_int(block.get('number'),'block.number')
        if actual!=block_number:
            raise Era64IError(f'BLOCK_HEADER_NUMBER_MISMATCH:{actual}!={block_number}')
        block_headers[block_number]=block
        selected_block_hosts[block_number]=str(client.last_endpoint_host or selected_block_hosts[block_number])
    events=[]
    rejected_event_count=0
    for key in sorted(selected):
        log=selected[key]
        block_number=key[0] and as_hex_int(log.get('blockNumber'),'log.blockNumber')
        event=build_event(log,block_headers[block_number],selected_block_hosts[block_number])
        if event is None:
            rejected_event_count+=1
        else:
            events.append(event)
    events.sort(key=lambda item:(item['block_number'],item['tx_hash'],item['log_index'],item['token_address']))
    if len({(event['chain_id'],event['tx_hash'],event['log_index']) for event in events})!=len(events):
        raise Era64IError('FINAL_EVENT_DUPLICATE_KEYS')
    wallets=sorted({
      address for event in events for address in (event['from_address'],event['to_address'])
      if address!=ZERO_ADDRESS
    })
    missing_timestamp=sum(1 for event in events if not event['block_time_utc'])
    missing_provenance=sum(1 for event in events if not event['source_provider_host'] or not event['evidence_hash'])
    acceptance=config['acceptance']
    passed=(
      len(scanned_chunks)>=int(acceptance['minimum_scanned_chunks'])
      and len(block_headers)>=int(acceptance['minimum_sampled_blocks'])
      and len(events)>=int(acceptance['minimum_real_transfer_events'])
      and len(wallets)>=int(acceptance['minimum_distinct_wallets'])
      and duplicate_count<=int(acceptance['maximum_duplicate_events'])
      and missing_timestamp<=int(acceptance['maximum_missing_timestamp_events'])
      and missing_provenance<=int(acceptance['maximum_missing_provenance_events'])
    )
    if not passed:
        raise Era64IError('HISTORICAL_BACKFILL_ACCEPTANCE_FAILED')
    scan={
      'latest_block':latest,'confirmed_block':confirmed,'start_block':start_block,'end_block':end_block,
      'historical_block_span':span,'scanned_chunk_count':len(scanned_chunks),
      'sampled_block_count':len(block_headers),'raw_log_count':raw_log_count,
      'selected_log_count':len(selected),'accepted_event_count':len(events),
      'rejected_event_count':rejected_event_count,'duplicate_event_count':duplicate_count,
      'missing_timestamp_event_count':missing_timestamp,'missing_provenance_event_count':missing_provenance,
    }
    database=write_events(database_path,events,scan)
    token_counts=Counter(event['token_address'] for event in events)
    block_counts=Counter(event['block_number'] for event in events)
    event_manifest=[{
      'block_number':event['block_number'],'block_time_utc':event['block_time_utc'],
      'tx_hash':event['tx_hash'],'log_index':event['log_index'],
      'token_address':event['token_address'],'from_address':event['from_address'],
      'to_address':event['to_address'],'amount_raw':event['amount_raw'],
      'evidence_hash':event['evidence_hash']
    } for event in events]
    authority=dict(config['authority'])
    generated=iso_now()
    detail={
      'schema':'tokenoskobi.era64i.bounded_historical_wallet_event_backfill.detail.v1',
      'status':'BOUNDED_HISTORICAL_WALLET_TRANSFER_BACKFILL_VERIFIED',
      'generated_at_utc':generated,'real_data':True,'synthetic_data':False,
      'chain':'BSC','chain_id':56,'network_access_used':True,
      'network_mode':'READ_ONLY_ALLOWLISTED_BSC_RPC','staging_database_write_used':True,
      'production_database_write_used':False,'database':database,'scan':scan,
      'distinct_wallet_count':len(wallets),'distinct_token_count':len(token_counts),
      'scope_tokens':tokens,'wallet_scope_artifact':str(config['wallet_scope_artifact']),
      'wallet_scope_count':len(wallet_scope),'wallet_scope':wallet_scope,
      'token_event_counts':dict(sorted(token_counts.items())),
      'sampled_block_event_counts':{str(key):block_counts[key] for key in sorted(block_counts)},
      'rpc_request_count':client.request_count,'provider_host':client.last_endpoint_host,
      'provider_error_tail':client.errors[-30:],'filter_mode_counts':dict(sorted(filter_modes.items())),
      'cost_enriched_event_count':0,'receipt_enriched_event_count':0,
      'cost_enrichment_complete':False,'closed_cycle_count':0,
      'successful_wallet_classification_ready':False,
      'successful_wallet_classification_status':'BLOCKED_PENDING_RECEIPT_COST_AND_SWAP_ENRICHMENT',
      'cluster_inference_performed':False,'identity_cluster_count':0,
      'event_set_hash':canonical_hash([event['evidence_hash'] for event in events]),
      'sample_event_head':event_manifest[:20],'sample_event_tail':event_manifest[-20:],
      'chunk_summaries':scanned_chunks,'authority':authority,
      'elapsed_seconds':round(time.monotonic()-started,6),
      'strongest_alternative_hypotheses':[
        'BASE_QUOTE_TOKEN_TRANSFER_DOES_NOT_BY_ITSELF_PROVE_A_SWAP',
        'TRANSFER_COUNTERPARTY_DOES_NOT_PROVE_COMMON_WALLET_OWNERSHIP',
        'RAW_TOKEN_AMOUNT_IS_NOT_COMPARABLE_ACROSS_DECIMALS',
        'SUCCESSFUL_WALLET_CLASSIFICATION_REQUIRES_RECEIPT_COST_PRICE_AND_CLOSED_CYCLE_EVIDENCE'
      ]
    }
    detail['detail_hash']=canonical_hash({key:value for key,value in detail.items() if key not in {'generated_at_utc','detail_hash'}})
    control={
      'schema':'tokenoskobi.era64i.bounded_historical_wallet_event_backfill.control.v1',
      'status':detail['status'],'real_data':True,'synthetic_data':False,
      'chain_id':56,'start_block':start_block,'end_block':end_block,
      'historical_block_span':span,'scanned_chunk_count':len(scanned_chunks),
      'sampled_block_count':len(block_headers),'raw_log_count':raw_log_count,
      'selected_event_count':len(events),'inserted_event_count':database['inserted_event_count'],
      'deduplicated_event_count':database['deduplicated_event_count'],
      'staging_event_count':database['database_event_count'],'distinct_wallet_count':len(wallets),
      'distinct_token_count':len(token_counts),'wallet_scope_count':len(wallet_scope),
      'rpc_request_count':client.request_count,
      'network_access_used':True,'staging_database_write_used':True,
      'production_database_write_used':False,'database_integrity_check':database['database_integrity_check'],
      'database_sha256':database['database_sha256'],'event_set_hash':detail['event_set_hash'],
      'cost_enriched_event_count':0,'receipt_enriched_event_count':0,
      'cost_enrichment_complete':False,'closed_cycle_count':0,
      'successful_wallet_classification_ready':False,
      'cluster_inference_performed':False,'identity_cluster_count':0,
      'detail_artifact':'data/replay/era64i_bounded_historical_wallet_event_backfill_v1.json',
      'detail_hash':detail['detail_hash'],'authority':authority,
    }
    control['result_hash']=canonical_hash(control)
    return detail,control

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--detail',type=Path,required=True)
    parser.add_argument('--control',type=Path,required=True)
    args=parser.parse_args()
    detail,control=run(args.config,args.database)
    atomic_json(args.detail,detail)
    atomic_json(args.control,control)
    print(f"ERA64I_BACKFILL_STATUS={control['status']}")
    print(f"BLOCK_RANGE={control['start_block']}..{control['end_block']}")
    print(f"HISTORICAL_BLOCK_SPAN={control['historical_block_span']}")
    print(f"SCANNED_CHUNK_COUNT={control['scanned_chunk_count']}")
    print(f"SAMPLED_BLOCK_COUNT={control['sampled_block_count']}")
    print(f"RAW_LOG_COUNT={control['raw_log_count']}")
    print(f"SELECTED_EVENT_COUNT={control['selected_event_count']}")
    print(f"INSERTED_EVENT_COUNT={control['inserted_event_count']}")
    print(f"STAGING_EVENT_COUNT={control['staging_event_count']}")
    print(f"DISTINCT_WALLET_COUNT={control['distinct_wallet_count']}")
    print(f"DISTINCT_TOKEN_COUNT={control['distinct_token_count']}")
    print(f"WALLET_SCOPE_COUNT={control['wallet_scope_count']}")
    print(f"RPC_REQUEST_COUNT={control['rpc_request_count']}")
    print('NETWORK_ACCESS_USED=true')
    print('STAGING_DATABASE_WRITE_USED=true')
    print('PRODUCTION_DATABASE_WRITE_USED=false')
    print('COST_ENRICHMENT_COMPLETE=false')
    print('SUCCESSFUL_WALLET_CLASSIFICATION_READY=false')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
