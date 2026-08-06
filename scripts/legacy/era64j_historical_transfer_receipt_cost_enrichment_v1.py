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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
HASH_LENGTH=66
ADDRESS_LENGTH=42

class Era64JError(RuntimeError):
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

def normalize_hash(value: Any) -> str | None:
    text=str(value or '').strip().lower()
    if not text.startswith('0x') or len(text)!=HASH_LENGTH:
        return None
    try:
        int(text[2:],16)
    except ValueError:
        return None
    return text

def normalize_address(value: Any) -> str | None:
    if value in (None,''):
        return None
    text=str(value).strip().lower()
    if not text.startswith('0x') or len(text)!=ADDRESS_LENGTH:
        return None
    try:
        int(text[2:],16)
    except ValueError:
        return None
    return text

def as_hex_int(value: Any,name: str) -> int:
    try:
        number=int(str(value),16)
    except (TypeError,ValueError) as exc:
        raise Era64JError(f'{name}:INVALID_HEX') from exc
    if number<0 or not math.isfinite(float(number)):
        raise Era64JError(f'{name}:INVALID_RANGE')
    return number

def bounded_int(value: Any,name: str,minimum: int,maximum: int) -> int:
    try:
        number=int(value)
    except (TypeError,ValueError) as exc:
        raise Era64JError(f'{name}:NOT_INTEGER') from exc
    if number<minimum or number>maximum:
        raise Era64JError(f'{name}:OUT_OF_BOUNDS')
    return number

def validate_config(config: dict[str,Any],provider: dict[str,Any]) -> None:
    if config.get('schema')!='tokenoskobi.era64j.historical_transfer_receipt_cost_enrichment.config.v1':
        raise Era64JError('CONFIG_SCHEMA_MISMATCH')
    if config.get('mode')!='BOUNDED_READONLY_BSC_RECEIPT_FETCH_TO_DEDICATED_STAGING_ENRICHMENT':
        raise Era64JError('CONFIG_MODE_INVALID')
    chain=config.get('chain')
    if not isinstance(chain,dict) or chain.get('name')!='BSC' or int(chain.get('chain_id',0))!=56:
        raise Era64JError('CHAIN_MUST_BE_BSC_56')
    if config.get('source_table')!='era64i_historical_wallet_transfer_staging_v1':
        raise Era64JError('SOURCE_TABLE_NOT_ALLOWLISTED')
    if config.get('enrichment_table')!='era64j_historical_receipt_cost_enrichment_v1':
        raise Era64JError('ENRICHMENT_TABLE_NOT_ALLOWLISTED')
    methods=set(config.get('rpc_method_allowlist') or [])
    if methods!={'eth_chainId','eth_getTransactionReceipt','eth_getTransactionByHash'}:
        raise Era64JError('RPC_METHOD_ALLOWLIST_INVALID')
    policy=config.get('classification_policy')
    if not isinstance(policy,dict):
        raise Era64JError('CLASSIFICATION_POLICY_NOT_OBJECT')
    if policy.get('performance_cost_enrichment_complete') is not False:
        raise Era64JError('PERFORMANCE_COST_ENRICHMENT_MUST_REMAIN_FALSE')
    for key in ('swap_direction_classification_authorized','successful_wallet_classification_authorized','cluster_inference_authorized'):
        if policy.get(key) is not False:
            raise Era64JError(f'{key}:MUST_BE_FALSE')
    authority=config.get('authority')
    if not isinstance(authority,dict):
        raise Era64JError('AUTHORITY_NOT_OBJECT')
    if authority.get('network_access') is not True or authority.get('network_mode')!='READ_ONLY_ALLOWLISTED_BSC_RPC':
        raise Era64JError('NETWORK_AUTHORITY_INVALID')
    if authority.get('staging_database_write') is not True:
        raise Era64JError('STAGING_DATABASE_WRITE_MUST_BE_TRUE')
    for key in ('production_database_write','runtime_service_mutation','panel_mutation','timer_mutation','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
        if authority.get(key) is not False:
            raise Era64JError(f'{key}:MUST_BE_FALSE')
    limits=config.get('limits')
    if not isinstance(limits,dict):
        raise Era64JError('LIMITS_NOT_OBJECT')
    bounded_int(limits.get('maximum_source_events'),'maximum_source_events',367,1000)
    bounded_int(limits.get('maximum_source_transactions'),'maximum_source_transactions',1,1000)
    bounded_int(limits.get('maximum_rpc_requests'),'maximum_rpc_requests',100,2000)
    bounded_int(limits.get('maximum_runtime_seconds'),'maximum_runtime_seconds',120,1800)
    bounded_int(limits.get('request_timeout_seconds'),'request_timeout_seconds',2,30)
    bounded_int(limits.get('retries_per_endpoint'),'retries_per_endpoint',0,2)
    if not isinstance(provider,dict) or provider.get('schema')!='tokenoskobi.era63e.always_on_market_runtime_config.v1':
        raise Era64JError('PROVIDER_CONFIG_INVALID')
    rpc=provider.get('rpc')
    if not isinstance(rpc,dict) or int(rpc.get('chain_id',0))!=56:
        raise Era64JError('PROVIDER_CHAIN_INVALID')
    endpoints=rpc.get('endpoints')
    allowed=set(rpc.get('allowed_hosts') or [])
    if not isinstance(endpoints,list) or len(endpoints)<2:
        raise Era64JError('PROVIDER_ENDPOINTS_INSUFFICIENT')
    for endpoint in endpoints:
        parsed=urllib.parse.urlparse(str(endpoint))
        if parsed.scheme!='https' or parsed.hostname not in allowed:
            raise Era64JError('PROVIDER_ENDPOINT_NOT_ALLOWLISTED_HTTPS')

def ensure_staging_path(path: Path) -> Path:
    resolved=path.resolve()
    allowed=(ROOT/'runtime'/'era64i'/'historical_wallet_transfer_staging_v1.sqlite3').resolve()
    if resolved!=allowed:
        raise Era64JError('DATABASE_PATH_NOT_DEDICATED_ERA64I_STAGING')
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
        self.maximum_runtime=float(limits['maximum_runtime_seconds'])
        self.allowed_methods=set(config['rpc_method_allowlist'])
        self.request_count=0
        self.endpoint_index=0
        self.last_endpoint_host=None
        self.errors:list[str]=[]
        self.started=time.monotonic()

    def call(self,method: str,params: list[Any]) -> Any:
        if method not in self.allowed_methods:
            raise Era64JError(f'RPC_METHOD_NOT_ALLOWLISTED:{method}')
        if self.request_count>=self.maximum_requests:
            raise Era64JError('RPC_REQUEST_BUDGET_EXCEEDED')
        if time.monotonic()-self.started>self.maximum_runtime:
            raise Era64JError('RPC_RUNTIME_BUDGET_EXCEEDED')
        last_error=''
        count=len(self.endpoints)
        for offset in range(count):
            endpoint=self.endpoints[(self.endpoint_index+offset)%count]
            parsed=urllib.parse.urlparse(endpoint)
            if parsed.scheme!='https' or parsed.hostname not in self.allowed_hosts:
                continue
            for attempt in range(self.retries+1):
                if self.request_count>=self.maximum_requests:
                    raise Era64JError('RPC_REQUEST_BUDGET_EXCEEDED')
                self.request_count+=1
                payload=json.dumps({'jsonrpc':'2.0','id':self.request_count,'method':method,'params':params}).encode('utf-8')
                request=urllib.request.Request(
                    endpoint,
                    data=payload,
                    headers={'Content-Type':'application/json','User-Agent':'Tokenoskobi-ERA64J/1.0 bounded-receipt-readonly'},
                    method='POST',
                )
                try:
                    with urllib.request.urlopen(request,timeout=self.timeout) as response:
                        result=json.loads(response.read().decode('utf-8'))
                    if not isinstance(result,dict):
                        raise Era64JError('RPC_RESPONSE_NOT_OBJECT')
                    if result.get('error'):
                        raise Era64JError(f"RPC_ERROR:{result['error']}")
                    if 'result' not in result:
                        raise Era64JError('RPC_RESULT_MISSING')
                    self.endpoint_index=(self.endpoint_index+offset+1)%count
                    self.last_endpoint_host=parsed.hostname
                    return result['result']
                except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError,OSError,json.JSONDecodeError,Era64JError) as exc:
                    last_error=f'{type(exc).__name__}:{exc}'
                    self.errors.append(f'{parsed.hostname}:{method}:{last_error}')
                    if attempt<self.retries:
                        time.sleep(min(self.backoff*(2**attempt),2.0))
        raise Era64JError(f'ALL_RPC_ENDPOINTS_FAILED:{method}:{last_error}')

def load_source_transactions(database_path: Path,source_table: str,maximum_events: int,maximum_transactions: int) -> tuple[int,list[dict[str,Any]]]:
    db=ensure_staging_path(database_path)
    conn=sqlite3.connect(f'file:{db}?mode=ro',uri=True)
    conn.row_factory=sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        integrity=str(conn.execute('PRAGMA integrity_check').fetchone()[0])
        if integrity.lower()!='ok':
            raise Era64JError(f'SOURCE_DATABASE_INTEGRITY_FAILED:{integrity}')
        source_event_count=int(conn.execute(f'SELECT COUNT(*) FROM {source_table}').fetchone()[0])
        if source_event_count<1 or source_event_count>maximum_events:
            raise Era64JError('SOURCE_EVENT_COUNT_OUT_OF_BOUNDS')
        rows=conn.execute(f'''
          SELECT tx_hash,MIN(block_number) AS min_block,MAX(block_number) AS max_block,
                 MIN(block_hash) AS min_block_hash,MAX(block_hash) AS max_block_hash,
                 COUNT(*) AS event_count
          FROM {source_table}
          GROUP BY tx_hash
          ORDER BY tx_hash
        ''').fetchall()
        if not (1<=len(rows)<=maximum_transactions):
            raise Era64JError('SOURCE_TRANSACTION_COUNT_OUT_OF_BOUNDS')
        transactions=[]
        for row in rows:
            tx_hash=normalize_hash(row['tx_hash'])
            block_hash=normalize_hash(row['min_block_hash'])
            if tx_hash is None or block_hash is None:
                raise Era64JError('SOURCE_HASH_INVALID')
            if int(row['min_block'])!=int(row['max_block']):
                raise Era64JError('SOURCE_TRANSACTION_BLOCK_NUMBER_CONFLICT')
            if str(row['min_block_hash']).lower()!=str(row['max_block_hash']).lower():
                raise Era64JError('SOURCE_TRANSACTION_BLOCK_HASH_CONFLICT')
            transactions.append({
              'tx_hash':tx_hash,
              'block_number':int(row['min_block']),
              'block_hash':block_hash,
              'event_count':int(row['event_count']),
            })
        return source_event_count,transactions
    finally:
        conn.close()

def fetch_enrichment(client: RpcClient,source: dict[str,Any]) -> dict[str,Any]:
    tx_hash=source['tx_hash']
    receipt=client.call('eth_getTransactionReceipt',[tx_hash])
    receipt_host=str(client.last_endpoint_host or '').strip().lower()
    if not isinstance(receipt,dict):
        raise Era64JError(f'RECEIPT_NOT_OBJECT:{tx_hash}')
    actual_tx=normalize_hash(receipt.get('transactionHash'))
    block_hash=normalize_hash(receipt.get('blockHash'))
    if actual_tx!=tx_hash:
        raise Era64JError(f'RECEIPT_TX_HASH_MISMATCH:{tx_hash}')
    if block_hash!=source['block_hash']:
        raise Era64JError(f'RECEIPT_BLOCK_HASH_MISMATCH:{tx_hash}')
    block_number=as_hex_int(receipt.get('blockNumber'),'receipt.blockNumber')
    if block_number!=source['block_number']:
        raise Era64JError(f'RECEIPT_BLOCK_NUMBER_MISMATCH:{tx_hash}')
    gas_used=as_hex_int(receipt.get('gasUsed'),'receipt.gasUsed')
    if gas_used<=0:
        raise Era64JError(f'RECEIPT_GAS_USED_INVALID:{tx_hash}')
    effective_value=receipt.get('effectiveGasPrice')
    raw_transaction=''
    gas_price_source='RECEIPT_EFFECTIVE_GAS_PRICE'
    receipt_effective_gas_price=0
    if effective_value not in (None,''):
        receipt_effective_gas_price=as_hex_int(effective_value,'receipt.effectiveGasPrice')
    if receipt_effective_gas_price>0:
        effective_gas_price=receipt_effective_gas_price
    else:
        transaction=client.call('eth_getTransactionByHash',[tx_hash])
        if not isinstance(transaction,dict):
            raise Era64JError(f'TRANSACTION_NOT_OBJECT:{tx_hash}')
        if normalize_hash(transaction.get('hash'))!=tx_hash:
            raise Era64JError(f'TRANSACTION_HASH_MISMATCH:{tx_hash}')
        transaction_gas_price=as_hex_int(transaction.get('gasPrice'),'transaction.gasPrice')
        effective_gas_price=transaction_gas_price
        raw_transaction=json.dumps(transaction,sort_keys=True,separators=(',',':'),ensure_ascii=True)
        gas_price_source='TRANSACTION_GAS_PRICE_FALLBACK' if transaction_gas_price>0 else 'VERIFIED_ZERO_GAS_PRICE_OBSERVATION'
    gas_cost=gas_used*effective_gas_price
    if gas_cost<0:
        raise Era64JError(f'GAS_COST_NEGATIVE:{tx_hash}')
    status=as_hex_int(receipt.get('status'),'receipt.status')
    if status not in {0,1}:
        raise Era64JError(f'RECEIPT_STATUS_INVALID:{tx_hash}')
    cumulative_gas=as_hex_int(receipt.get('cumulativeGasUsed'),'receipt.cumulativeGasUsed')
    transaction_index=as_hex_int(receipt.get('transactionIndex'),'receipt.transactionIndex')
    tx_from=normalize_address(receipt.get('from'))
    tx_to=normalize_address(receipt.get('to'))
    contract_address=normalize_address(receipt.get('contractAddress'))
    raw_receipt=json.dumps(receipt,sort_keys=True,separators=(',',':'),ensure_ascii=True)
    evidence_core={
      'chain_id':56,'tx_hash':tx_hash,'block_number':block_number,'block_hash':block_hash,
      'receipt_status':status,'gas_used':str(gas_used),
      'effective_gas_price_wei':str(effective_gas_price),'gas_cost_wei':str(gas_cost),
      'cumulative_gas_used':str(cumulative_gas),'transaction_index':transaction_index,
      'gas_price_source':gas_price_source,'raw_receipt_json':raw_receipt,
      'raw_transaction_json':raw_transaction,
    }
    evidence_hash=canonical_hash(evidence_core)
    return {
      **evidence_core,
      'receipt_uid':canonical_hash({'chain_id':56,'tx_hash':tx_hash,'evidence_hash':evidence_hash}),
      'event_count':source['event_count'],
      'tx_from_address':tx_from or '',
      'tx_to_address':tx_to or '',
      'contract_address':contract_address or '',
      'source_provider_host':receipt_host,
      'evidence_kind':'REAL_BSC_TRANSACTION_RECEIPT_AND_GAS_COST',
      'evidence_hash':evidence_hash,
    }

def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS era64j_historical_receipt_cost_enrichment_v1 (
      tx_hash TEXT PRIMARY KEY,
      receipt_uid TEXT NOT NULL UNIQUE,
      chain_id INTEGER NOT NULL CHECK(chain_id=56),
      block_number INTEGER NOT NULL,
      block_hash TEXT NOT NULL,
      receipt_status INTEGER NOT NULL CHECK(receipt_status IN (0,1)),
      gas_used TEXT NOT NULL,
      effective_gas_price_wei TEXT NOT NULL,
      gas_cost_wei TEXT NOT NULL,
      cumulative_gas_used TEXT NOT NULL,
      transaction_index INTEGER NOT NULL,
      gas_price_source TEXT NOT NULL,
      event_count INTEGER NOT NULL,
      tx_from_address TEXT NOT NULL,
      tx_to_address TEXT NOT NULL,
      contract_address TEXT NOT NULL,
      source_provider_host TEXT NOT NULL,
      evidence_kind TEXT NOT NULL,
      evidence_hash TEXT NOT NULL UNIQUE,
      raw_receipt_json TEXT NOT NULL,
      raw_transaction_json TEXT NOT NULL,
      enriched_at_utc TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS era64j_receipt_block_idx
      ON era64j_historical_receipt_cost_enrichment_v1(block_number,transaction_index);
    CREATE TABLE IF NOT EXISTS era64j_receipt_cost_enrichment_batch_v1 (
      batch_uid TEXT PRIMARY KEY,
      source_event_count INTEGER NOT NULL,
      source_transaction_count INTEGER NOT NULL,
      inserted_receipt_count INTEGER NOT NULL,
      deduplicated_receipt_count INTEGER NOT NULL,
      receipt_count_after INTEGER NOT NULL,
      receipt_set_hash TEXT NOT NULL,
      enriched_at_utc TEXT NOT NULL
    );
    ''')

def write_enrichments(database_path: Path,source_event_count: int,enrichments: list[dict[str,Any]]) -> dict[str,Any]:
    db=ensure_staging_path(database_path)
    enriched_at=iso_now()
    conn=sqlite3.connect(db)
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        create_schema(conn)
        conn.execute('BEGIN IMMEDIATE')
        before=int(conn.execute('SELECT COUNT(*) FROM era64j_historical_receipt_cost_enrichment_v1').fetchone()[0])
        inserted=0
        for item in enrichments:
            existing=conn.execute('SELECT evidence_hash FROM era64j_historical_receipt_cost_enrichment_v1 WHERE tx_hash=?',(item['tx_hash'],)).fetchone()
            if existing is not None:
                if str(existing[0])!=item['evidence_hash']:
                    raise Era64JError(f'EXISTING_RECEIPT_EVIDENCE_CONFLICT:{item["tx_hash"]}')
                continue
            cursor=conn.execute('''
              INSERT INTO era64j_historical_receipt_cost_enrichment_v1 (
                tx_hash,receipt_uid,chain_id,block_number,block_hash,receipt_status,
                gas_used,effective_gas_price_wei,gas_cost_wei,cumulative_gas_used,
                transaction_index,gas_price_source,event_count,tx_from_address,
                tx_to_address,contract_address,source_provider_host,evidence_kind,
                evidence_hash,raw_receipt_json,raw_transaction_json,enriched_at_utc
              ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''',(
              item['tx_hash'],item['receipt_uid'],56,item['block_number'],item['block_hash'],
              item['receipt_status'],item['gas_used'],item['effective_gas_price_wei'],
              item['gas_cost_wei'],item['cumulative_gas_used'],item['transaction_index'],
              item['gas_price_source'],item['event_count'],item['tx_from_address'],
              item['tx_to_address'],item['contract_address'],item['source_provider_host'],
              item['evidence_kind'],item['evidence_hash'],item['raw_receipt_json'],
              item['raw_transaction_json'],enriched_at,
            ))
            inserted+=max(0,int(cursor.rowcount))
        after=int(conn.execute('SELECT COUNT(*) FROM era64j_historical_receipt_cost_enrichment_v1').fetchone()[0])
        deduplicated=len(enrichments)-inserted
        receipt_set_hash=canonical_hash(sorted(item['evidence_hash'] for item in enrichments))
        batch_uid=canonical_hash({'source_event_count':source_event_count,'receipt_set_hash':receipt_set_hash})
        conn.execute('''
          INSERT OR REPLACE INTO era64j_receipt_cost_enrichment_batch_v1 (
            batch_uid,source_event_count,source_transaction_count,inserted_receipt_count,
            deduplicated_receipt_count,receipt_count_after,receipt_set_hash,enriched_at_utc
          ) VALUES (?,?,?,?,?,?,?,?)
        ''',(batch_uid,source_event_count,len(enrichments),inserted,deduplicated,after,receipt_set_hash,enriched_at))
        covered_events=int(conn.execute('''
          SELECT COUNT(*)
          FROM era64i_historical_wallet_transfer_staging_v1 s
          JOIN era64j_historical_receipt_cost_enrichment_v1 e ON e.tx_hash=s.tx_hash
        ''').fetchone()[0])
        source_flags_nonzero=int(conn.execute('''
          SELECT COUNT(*) FROM era64i_historical_wallet_transfer_staging_v1
          WHERE cost_enriched!=0 OR receipt_enriched!=0
        ''').fetchone()[0])
        unique_receipts=int(conn.execute('SELECT COUNT(DISTINCT tx_hash) FROM era64j_historical_receipt_cost_enrichment_v1').fetchone()[0])
        integrity=str(conn.execute('PRAGMA integrity_check').fetchone()[0])
        if integrity.lower()!='ok':
            raise Era64JError(f'DATABASE_INTEGRITY_FAILED:{integrity}')
        if after!=before+inserted or unique_receipts!=after:
            raise Era64JError('DATABASE_COUNT_OR_UNIQUENESS_INVARIANT_FAILED')
        if covered_events!=source_event_count:
            raise Era64JError('SOURCE_EVENT_RECEIPT_COVERAGE_INCOMPLETE')
        if source_flags_nonzero!=0:
            raise Era64JError('IMMUTABLE_SOURCE_FLAGS_CHANGED')
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    readonly=sqlite3.connect(f'file:{db}?mode=ro',uri=True)
    try:
        readonly.execute('PRAGMA query_only=ON')
        readonly_count=int(readonly.execute('SELECT COUNT(*) FROM era64j_historical_receipt_cost_enrichment_v1').fetchone()[0])
    finally:
        readonly.close()
    if readonly_count!=after:
        raise Era64JError('READONLY_VERIFY_COUNT_MISMATCH')
    return {
      'database_path':str(database_path),'database_sha256':file_hash(db),
      'database_integrity_check':integrity,'receipt_count_after':after,
      'inserted_receipt_count':inserted,'deduplicated_receipt_count':deduplicated,
      'receipt_set_hash':receipt_set_hash,'batch_uid':batch_uid,
      'covered_source_event_count':covered_events,'source_flags_nonzero_count':source_flags_nonzero,
      'enriched_at_utc':enriched_at,
    }

def run(config_path: Path,database_path: Path) -> tuple[dict[str,Any],dict[str,Any]]:
    started=time.monotonic()
    config=json.loads(config_path.read_text(encoding='utf-8'))
    provider=json.loads((ROOT/str(config['provider_config'])).read_text(encoding='utf-8'))
    source_control=json.loads((ROOT/str(config['source_control'])).read_text(encoding='utf-8'))
    validate_config(config,provider)
    if source_control.get('status')!='BOUNDED_HISTORICAL_WALLET_TRANSFER_BACKFILL_VERIFIED':
        raise Era64JError('SOURCE_CONTROL_STATUS_INVALID')
    source_event_count,transactions=load_source_transactions(
      database_path,str(config['source_table']),
      int(config['limits']['maximum_source_events']),
      int(config['limits']['maximum_source_transactions']),
    )
    if source_event_count!=int(source_control.get('staging_event_count',-1)):
        raise Era64JError('SOURCE_EVENT_COUNT_CONTROL_MISMATCH')
    if source_event_count<int(config['acceptance']['minimum_source_events']):
        raise Era64JError('SOURCE_EVENT_MINIMUM_NOT_MET')
    client=RpcClient(config,provider)
    chain_id=as_hex_int(client.call('eth_chainId',[]),'eth_chainId')
    if chain_id!=56:
        raise Era64JError(f'CHAIN_ID_MISMATCH:{chain_id}')
    enrichments=[]
    for source in transactions:
        enrichments.append(fetch_enrichment(client,source))
    if len(enrichments)!=len(transactions):
        raise Era64JError('RECEIPT_TRANSACTION_COVERAGE_INCOMPLETE')
    invalid_cost=sum(1 for item in enrichments if int(item['gas_cost_wei'])!=int(item['gas_used'])*int(item['effective_gas_price_wei']))
    block_mismatches=sum(1 for item,source in zip(enrichments,transactions) if item['block_number']!=source['block_number'] or item['block_hash']!=source['block_hash'])
    missing_receipts=len(transactions)-len(enrichments)
    receipt_coverage=len(enrichments)/len(transactions)
    event_coverage=sum(item['event_count'] for item in enrichments)/source_event_count
    acceptance=config['acceptance']
    if receipt_coverage<float(acceptance['minimum_receipt_coverage_ratio']):
        raise Era64JError('RECEIPT_COVERAGE_RATIO_FAILED')
    if event_coverage<float(acceptance['minimum_gas_cost_coverage_ratio']):
        raise Era64JError('EVENT_GAS_COST_COVERAGE_RATIO_FAILED')
    if missing_receipts>int(acceptance['maximum_missing_receipts']):
        raise Era64JError('MISSING_RECEIPT_LIMIT_FAILED')
    if block_mismatches>int(acceptance['maximum_block_mismatches']):
        raise Era64JError('BLOCK_MISMATCH_LIMIT_FAILED')
    if invalid_cost>int(acceptance['maximum_invalid_cost_records']):
        raise Era64JError('INVALID_COST_LIMIT_FAILED')
    database=write_enrichments(database_path,source_event_count,enrichments)
    success_count=sum(1 for item in enrichments if item['receipt_status']==1)
    failed_count=len(enrichments)-success_count
    fallback_count=sum(1 for item in enrichments if item['gas_price_source']=='TRANSACTION_GAS_PRICE_FALLBACK')
    zero_gas_price_count=sum(1 for item in enrichments if item['gas_price_source']=='VERIFIED_ZERO_GAS_PRICE_OBSERVATION')
    total_gas_cost=sum(int(item['gas_cost_wei']) for item in enrichments)
    event_cost_coverage=sum(item['event_count'] for item in enrichments)
    authority=dict(config['authority'])
    generated=iso_now()
    detail={
      'schema':'tokenoskobi.era64j.historical_transfer_receipt_cost_enrichment.detail.v1',
      'status':'HISTORICAL_TRANSFER_RECEIPT_GAS_COST_ENRICHMENT_VERIFIED',
      'generated_at_utc':generated,'real_data':True,'synthetic_data':False,
      'chain':'BSC','chain_id':56,'network_access_used':True,
      'network_mode':'READ_ONLY_ALLOWLISTED_BSC_RPC','staging_database_write_used':True,
      'production_database_write_used':False,'database':database,
      'source_event_count':source_event_count,'source_transaction_count':len(transactions),
      'receipt_enriched_transaction_count':len(enrichments),
      'receipt_enriched_event_count':event_cost_coverage,
      'gas_cost_enriched_event_count':event_cost_coverage,
      'successful_receipt_count':success_count,'failed_receipt_count':failed_count,
      'gas_price_fallback_count':fallback_count,'zero_gas_price_observation_count':zero_gas_price_count,
      'total_gas_cost_wei':str(total_gas_cost),
      'receipt_coverage_ratio':receipt_coverage,'event_gas_cost_coverage_ratio':event_coverage,
      'missing_receipt_count':missing_receipts,'block_mismatch_count':block_mismatches,
      'invalid_cost_record_count':invalid_cost,'rpc_request_count':client.request_count,
      'provider_host':client.last_endpoint_host,'provider_error_tail':client.errors[-30:],
      'receipt_gas_cost_enrichment_complete':True,
      'performance_cost_enrichment_complete':False,
      'swap_direction_classification_ready':False,
      'closed_cycle_count':0,'successful_wallet_classification_ready':False,
      'successful_wallet_classification_status':'BLOCKED_PENDING_SWAP_DIRECTION_TOKEN_METADATA_PRICE_AND_CLOSED_CYCLE_EVIDENCE',
      'cluster_inference_performed':False,'identity_cluster_count':0,
      'source_flags_immutable_zero':database['source_flags_nonzero_count']==0,
      'sample_receipt_head':[{key:item[key] for key in ('tx_hash','block_number','receipt_status','gas_used','effective_gas_price_wei','gas_cost_wei','event_count','evidence_hash')} for item in enrichments[:20]],
      'sample_receipt_tail':[{key:item[key] for key in ('tx_hash','block_number','receipt_status','gas_used','effective_gas_price_wei','gas_cost_wei','event_count','evidence_hash')} for item in enrichments[-20:]],
      'authority':authority,
      'strongest_alternative_hypotheses':[
        'TRANSACTION_GAS_COST_IS_NOT_TOKEN_TRADING_FEE',
        'BASE_QUOTE_TRANSFER_LOGS_DO_NOT_BY_THEMSELVES_PROVE_SWAP_DIRECTION',
        'TOKEN_DECIMALS_AND_PRICE_CONTEXT_ARE_REQUIRED_FOR_COMPARABLE_PNL',
        'RECEIPT_SUCCESS_DOES_NOT_PROVE_PROFITABLE_WALLET_BEHAVIOR'
      ],
      'elapsed_seconds':round(time.monotonic()-started,6),
    }
    detail['detail_hash']=canonical_hash({key:value for key,value in detail.items() if key not in {'generated_at_utc','detail_hash'}})
    control={
      'schema':'tokenoskobi.era64j.historical_transfer_receipt_cost_enrichment.control.v1',
      'status':detail['status'],'real_data':True,'synthetic_data':False,'chain_id':56,
      'source_event_count':source_event_count,'source_transaction_count':len(transactions),
      'receipt_enriched_transaction_count':len(enrichments),
      'receipt_enriched_event_count':event_cost_coverage,
      'gas_cost_enriched_event_count':event_cost_coverage,
      'inserted_receipt_count':database['inserted_receipt_count'],
      'deduplicated_receipt_count':database['deduplicated_receipt_count'],
      'staging_receipt_count':database['receipt_count_after'],
      'successful_receipt_count':success_count,'failed_receipt_count':failed_count,
      'gas_price_fallback_count':fallback_count,'zero_gas_price_observation_count':zero_gas_price_count,
      'total_gas_cost_wei':str(total_gas_cost),
      'receipt_coverage_ratio':receipt_coverage,'event_gas_cost_coverage_ratio':event_coverage,
      'missing_receipt_count':missing_receipts,'block_mismatch_count':block_mismatches,
      'invalid_cost_record_count':invalid_cost,'rpc_request_count':client.request_count,
      'network_access_used':True,'staging_database_write_used':True,
      'production_database_write_used':False,
      'database_integrity_check':database['database_integrity_check'],
      'database_sha256':database['database_sha256'],'receipt_set_hash':database['receipt_set_hash'],
      'receipt_gas_cost_enrichment_complete':True,
      'performance_cost_enrichment_complete':False,
      'swap_direction_classification_ready':False,'closed_cycle_count':0,
      'successful_wallet_classification_ready':False,
      'cluster_inference_performed':False,'identity_cluster_count':0,
      'source_flags_immutable_zero':database['source_flags_nonzero_count']==0,
      'detail_artifact':'data/replay/era64j_historical_transfer_receipt_cost_enrichment_v1.json',
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
    print(f"ERA64J_ENRICHMENT_STATUS={control['status']}")
    print(f"SOURCE_EVENT_COUNT={control['source_event_count']}")
    print(f"SOURCE_TRANSACTION_COUNT={control['source_transaction_count']}")
    print(f"RECEIPT_ENRICHED_TRANSACTION_COUNT={control['receipt_enriched_transaction_count']}")
    print(f"RECEIPT_ENRICHED_EVENT_COUNT={control['receipt_enriched_event_count']}")
    print(f"GAS_COST_ENRICHED_EVENT_COUNT={control['gas_cost_enriched_event_count']}")
    print(f"SUCCESSFUL_RECEIPT_COUNT={control['successful_receipt_count']}")
    print(f"FAILED_RECEIPT_COUNT={control['failed_receipt_count']}")
    print(f"ZERO_GAS_PRICE_OBSERVATION_COUNT={control['zero_gas_price_observation_count']}")
    print(f"RPC_REQUEST_COUNT={control['rpc_request_count']}")
    print('RECEIPT_GAS_COST_ENRICHMENT_COMPLETE=true')
    print('PERFORMANCE_COST_ENRICHMENT_COMPLETE=false')
    print('SUCCESSFUL_WALLET_CLASSIFICATION_READY=false')
    print('NETWORK_ACCESS_USED=true')
    print('STAGING_DATABASE_WRITE_USED=true')
    print('PRODUCTION_DATABASE_WRITE_USED=false')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
