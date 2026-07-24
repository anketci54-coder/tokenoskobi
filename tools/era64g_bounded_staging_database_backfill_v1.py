#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
ADDRESS_RE=re.compile(r'^0x[0-9a-f]{40}$')
HASH_RE=re.compile(r'^0x[0-9a-f]{64}$')
EVIDENCE_RE=re.compile(r'^[0-9a-f]{64}$')

class Era64GError(RuntimeError):
    pass

def canonical_hash(value: Any) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def file_hash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def atomic_json(path: Path, value: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    json.loads(temp.read_text(encoding='utf-8'))
    temp.replace(path)

def ensure_staging_path(path: Path) -> Path:
    resolved=path.resolve()
    allowed=(ROOT/'runtime'/'era64g').resolve()
    if allowed not in resolved.parents or resolved.suffix not in {'.sqlite3','.sqlite','.db'}:
        raise Era64GError('DATABASE_PATH_NOT_DEDICATED_ERA64G_STAGING')
    return resolved

def normalized_address(value: Any, name: str) -> str:
    text=str(value or '').strip().lower()
    if not ADDRESS_RE.fullmatch(text):
        raise Era64GError(f'{name}:INVALID_ADDRESS')
    return text

def integer_text(value: Any, name: str, allow_zero: bool=True) -> str:
    text=str(value or '').strip()
    try:
        number=int(text)
    except ValueError as exc:
        raise Era64GError(f'{name}:INVALID_INTEGER') from exc
    if number < 0 or (not allow_zero and number == 0):
        raise Era64GError(f'{name}:OUT_OF_RANGE')
    return str(number)

def normalize_event(raw: dict[str,Any]) -> dict[str,Any]:
    if not isinstance(raw,dict):
        raise Era64GError('EVENT_NOT_OBJECT')
    event_type=str(raw.get('event_type') or '').strip().upper()
    if event_type not in {'NATIVE_TRANSFER','TOKEN_TRANSFER'}:
        raise Era64GError('EVENT_TYPE_NOT_ALLOWED')
    chain=str(raw.get('chain') or '').strip().upper()
    chain_id=int(raw.get('chain_id',0))
    if chain!='BSC' or chain_id!=56:
        raise Era64GError('CHAIN_MISMATCH')
    tx_hash=str(raw.get('tx_hash') or '').strip().lower()
    block_hash=str(raw.get('block_hash') or '').strip().lower()
    if not HASH_RE.fullmatch(tx_hash) or not HASH_RE.fullmatch(block_hash):
        raise Era64GError('TRANSACTION_OR_BLOCK_HASH_INVALID')
    evidence_hash=str(raw.get('evidence_hash') or '').strip().lower()
    if not EVIDENCE_RE.fullmatch(evidence_hash):
        raise Era64GError('EVIDENCE_HASH_INVALID')
    log_index=int(raw.get('log_index'))
    if event_type=='NATIVE_TRANSFER' and log_index!=-1:
        raise Era64GError('NATIVE_TRANSFER_LOG_INDEX_MUST_BE_MINUS_ONE')
    if event_type=='TOKEN_TRANSFER' and log_index<0:
        raise Era64GError('TOKEN_TRANSFER_LOG_INDEX_INVALID')
    block_number=int(raw.get('block_number',0))
    if block_number<=0:
        raise Era64GError('BLOCK_NUMBER_INVALID')
    block_time=str(raw.get('block_time_utc') or '').strip()
    try:
        datetime.fromisoformat(block_time.replace('Z','+00:00'))
    except ValueError as exc:
        raise Era64GError('BLOCK_TIME_INVALID') from exc
    token=normalized_address(raw.get('token_address'),'token_address')
    if event_type=='NATIVE_TRANSFER' and token!='0x0000000000000000000000000000000000000000':
        raise Era64GError('NATIVE_TOKEN_SENTINEL_INVALID')
    normalized={
        'chain':'BSC','chain_id':56,'event_type':event_type,
        'from_address':normalized_address(raw.get('from_address'),'from_address'),
        'to_address':normalized_address(raw.get('to_address'),'to_address'),
        'token_address':token,
        'amount_raw':integer_text(raw.get('amount_raw'),'amount_raw',allow_zero=False),
        'tx_hash':tx_hash,'log_index':log_index,'block_number':block_number,
        'block_hash':block_hash,'block_time_utc':block_time,
        'receipt_status':int(raw.get('receipt_status',0)),
        'gas_used':integer_text(raw.get('gas_used'),'gas_used'),
        'effective_gas_price_wei':integer_text(raw.get('effective_gas_price_wei'),'effective_gas_price_wei'),
        'gas_cost_wei':integer_text(raw.get('gas_cost_wei'),'gas_cost_wei'),
        'evidence_kind':str(raw.get('evidence_kind') or '').strip(),
        'evidence_hash':evidence_hash,
        'source_provider_host':str(raw.get('source_provider_host') or '').strip().lower(),
    }
    if normalized['receipt_status'] not in {0,1}:
        raise Era64GError('RECEIPT_STATUS_INVALID')
    if not normalized['evidence_kind'] or not normalized['source_provider_host']:
        raise Era64GError('PROVENANCE_INCOMPLETE')
    normalized['event_uid']=canonical_hash({key:normalized[key] for key in (
        'chain_id','tx_hash','log_index','event_type','from_address','to_address','token_address','amount_raw'
    )})
    return normalized

def load_source(path: Path, config: dict[str,Any]) -> tuple[dict[str,Any],list[dict[str,Any]]]:
    source=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(source,dict):
        raise Era64GError('SOURCE_NOT_OBJECT')
    if source.get('status')!=config['required_source_status']:
        raise Era64GError('SOURCE_STATUS_INVALID')
    if source.get('real_data') is not True or source.get('synthetic_data') is not False:
        raise Era64GError('SOURCE_NOT_VERIFIED_REAL_DATA')
    if source.get('chain_id')!=56:
        raise Era64GError('SOURCE_CHAIN_ID_INVALID')
    events=source.get('events')
    if not isinstance(events,list) or not events:
        raise Era64GError('SOURCE_EVENTS_EMPTY')
    if len(events)>int(config['maximum_source_events']):
        raise Era64GError('SOURCE_EVENT_BUDGET_EXCEEDED')
    normalized=[normalize_event(item) for item in events]
    if len({(e['chain_id'],e['tx_hash'],e['log_index']) for e in normalized})!=len(normalized):
        raise Era64GError('SOURCE_DUPLICATE_DEDUP_KEYS')
    return source,normalized

def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS era64g_wallet_event_staging_v1 (
      event_uid TEXT PRIMARY KEY,
      chain TEXT NOT NULL CHECK(chain='BSC'),
      chain_id INTEGER NOT NULL CHECK(chain_id=56),
      event_type TEXT NOT NULL CHECK(event_type IN ('NATIVE_TRANSFER','TOKEN_TRANSFER')),
      from_address TEXT NOT NULL,
      to_address TEXT NOT NULL,
      token_address TEXT NOT NULL,
      amount_raw TEXT NOT NULL,
      tx_hash TEXT NOT NULL,
      log_index INTEGER NOT NULL,
      block_number INTEGER NOT NULL,
      block_hash TEXT NOT NULL,
      block_time_utc TEXT NOT NULL,
      receipt_status INTEGER NOT NULL,
      gas_used TEXT NOT NULL,
      effective_gas_price_wei TEXT NOT NULL,
      gas_cost_wei TEXT NOT NULL,
      evidence_kind TEXT NOT NULL,
      evidence_hash TEXT NOT NULL,
      source_provider_host TEXT NOT NULL,
      source_artifact TEXT NOT NULL,
      source_artifact_sha256 TEXT NOT NULL,
      imported_at_utc TEXT NOT NULL,
      raw_event_json TEXT NOT NULL,
      UNIQUE(chain_id,tx_hash,log_index)
    );
    CREATE INDEX IF NOT EXISTS era64g_wallet_event_block_idx
      ON era64g_wallet_event_staging_v1(block_number,tx_hash,log_index);
    CREATE INDEX IF NOT EXISTS era64g_wallet_event_from_idx
      ON era64g_wallet_event_staging_v1(from_address,block_number);
    CREATE INDEX IF NOT EXISTS era64g_wallet_event_to_idx
      ON era64g_wallet_event_staging_v1(to_address,block_number);
    CREATE TABLE IF NOT EXISTS era64g_import_batch_v1 (
      source_artifact_sha256 TEXT PRIMARY KEY,
      source_artifact TEXT NOT NULL,
      source_event_count INTEGER NOT NULL,
      inserted_event_count INTEGER NOT NULL,
      deduplicated_event_count INTEGER NOT NULL,
      total_event_count_after INTEGER NOT NULL,
      imported_at_utc TEXT NOT NULL
    );
    ''')

def import_events(config_path: Path, source_path: Path, database_path: Path) -> dict[str,Any]:
    config=json.loads(config_path.read_text(encoding='utf-8'))
    if config.get('mode')!='LOCAL_STAGING_SQLITE_WRITE_FROM_SEALED_REAL_CANARY':
        raise Era64GError('CONFIG_MODE_INVALID')
    authority=config.get('authority',{})
    if authority.get('staging_database_write') is not True or authority.get('production_database_write') is not False:
        raise Era64GError('DATABASE_AUTHORITY_INVALID')
    for key in ('paper_trade','live_trade','wallet','signing','order_create','broadcast','blockchain_network_access'):
        if authority.get(key) is not False:
            raise Era64GError(f'{key}:MUST_BE_FALSE')
    db=ensure_staging_path(database_path)
    source,events=load_source(source_path,config)
    source_sha=file_hash(source_path)
    imported_at=datetime.now(timezone.utc).isoformat()
    db.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(db)
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA journal_mode=DELETE')
        conn.execute('PRAGMA synchronous=FULL')
        conn.execute('BEGIN IMMEDIATE')
        create_schema(conn)
        before=int(conn.execute('SELECT COUNT(*) FROM era64g_wallet_event_staging_v1').fetchone()[0])
        inserted=0
        for event in events:
            raw_json=json.dumps(event,sort_keys=True,separators=(',',':'),ensure_ascii=True)
            cursor=conn.execute('''
              INSERT OR IGNORE INTO era64g_wallet_event_staging_v1 (
                event_uid,chain,chain_id,event_type,from_address,to_address,token_address,
                amount_raw,tx_hash,log_index,block_number,block_hash,block_time_utc,
                receipt_status,gas_used,effective_gas_price_wei,gas_cost_wei,evidence_kind,
                evidence_hash,source_provider_host,source_artifact,source_artifact_sha256,
                imported_at_utc,raw_event_json
              ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''',(
              event['event_uid'],event['chain'],event['chain_id'],event['event_type'],
              event['from_address'],event['to_address'],event['token_address'],event['amount_raw'],
              event['tx_hash'],event['log_index'],event['block_number'],event['block_hash'],
              event['block_time_utc'],event['receipt_status'],event['gas_used'],
              event['effective_gas_price_wei'],event['gas_cost_wei'],event['evidence_kind'],
              event['evidence_hash'],event['source_provider_host'],str(source_path),source_sha,
              imported_at,raw_json
            ))
            inserted+=max(0,int(cursor.rowcount))
        after=int(conn.execute('SELECT COUNT(*) FROM era64g_wallet_event_staging_v1').fetchone()[0])
        deduplicated=len(events)-inserted
        conn.execute('''
          INSERT OR REPLACE INTO era64g_import_batch_v1 (
            source_artifact_sha256,source_artifact,source_event_count,inserted_event_count,
            deduplicated_event_count,total_event_count_after,imported_at_utc
          ) VALUES (?,?,?,?,?,?,?)
        ''',(source_sha,str(source_path),len(events),inserted,deduplicated,after,imported_at))
        conn.commit()
        integrity=str(conn.execute('PRAGMA integrity_check').fetchone()[0])
        distinct_wallets=int(conn.execute('''
          SELECT COUNT(*) FROM (
            SELECT from_address AS wallet
              FROM era64g_wallet_event_staging_v1
             WHERE from_address != '0x0000000000000000000000000000000000000000'
            UNION
            SELECT to_address AS wallet
              FROM era64g_wallet_event_staging_v1
             WHERE to_address != '0x0000000000000000000000000000000000000000'
          )
        ''').fetchone()[0])
        native_count=int(conn.execute("SELECT COUNT(*) FROM era64g_wallet_event_staging_v1 WHERE event_type='NATIVE_TRANSFER'").fetchone()[0])
        token_count=int(conn.execute("SELECT COUNT(*) FROM era64g_wallet_event_staging_v1 WHERE event_type='TOKEN_TRANSFER'").fetchone()[0])
        if integrity.lower()!='ok':
            raise Era64GError(f'INTEGRITY_CHECK_FAILED:{integrity}')
        if after < before or after != before + inserted:
            raise Era64GError('DATABASE_COUNT_INVARIANT_FAILED')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    db_sha=file_hash(db)
    readonly=sqlite3.connect(f'file:{db}?mode=ro',uri=True)
    try:
        readonly.execute('PRAGMA query_only=ON')
        readonly_count=int(readonly.execute('SELECT COUNT(*) FROM era64g_wallet_event_staging_v1').fetchone()[0])
    finally:
        readonly.close()
    if readonly_count!=after:
        raise Era64GError('READONLY_VERIFY_COUNT_MISMATCH')
    return {
      'schema':'tokenoskobi.era64g.bounded_staging_database_backfill.result.v1',
      'status':'BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED',
      'timestamp_utc':imported_at,
      'real_data':True,'synthetic_data':False,
      'source_status':source.get('status'),'source_artifact':str(source_path),
      'source_artifact_sha256':source_sha,'source_event_count':len(events),
      'inserted_event_count':inserted,'deduplicated_event_count':deduplicated,
      'staging_event_count':after,'native_transfer_event_count':native_count,
      'token_transfer_event_count':token_count,'distinct_wallet_count':distinct_wallets,
      'staging_database':str(database_path),'staging_database_sha256':db_sha,
      'integrity_check':integrity,'production_database_write_used':False,
      'blockchain_network_access_used':False,
      'authority':authority,
    }

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=import_events(args.config,args.source,args.database)
    atomic_json(args.output,result)
    print(f"ERA64G_BACKFILL_STATUS={result['status']}")
    print(f"SOURCE_EVENT_COUNT={result['source_event_count']}")
    print(f"INSERTED_EVENT_COUNT={result['inserted_event_count']}")
    print(f"DEDUPLICATED_EVENT_COUNT={result['deduplicated_event_count']}")
    print(f"STAGING_EVENT_COUNT={result['staging_event_count']}")
    print(f"DISTINCT_WALLET_COUNT={result['distinct_wallet_count']}")
    print(f"INTEGRITY_CHECK={result['integrity_check']}")
    return 0

if __name__=='__main__':
    raise SystemExit(main())
