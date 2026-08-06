#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path('/root/tokenoskobi_clean_v1')
ADDRESS_RE=re.compile(r'^0x[0-9a-f]{40}$')
HASH_RE=re.compile(r'^0x[0-9a-f]{64}$')
EVIDENCE_RE=re.compile(r'^[0-9a-f]{64}$')

class Era64HError(RuntimeError):
    pass

def canonical_hash(value: Any) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def file_hash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def atomic_json(path: Path,value: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    json.loads(temp.read_text(encoding='utf-8'))
    temp.replace(path)

def validate_address(value: Any,name: str) -> str:
    text=str(value or '').strip().lower()
    if not ADDRESS_RE.fullmatch(text):
        raise Era64HError(f'{name}:INVALID_ADDRESS')
    return text

def validate_hash(value: Any,name: str) -> str:
    text=str(value or '').strip().lower()
    if not HASH_RE.fullmatch(text):
        raise Era64HError(f'{name}:INVALID_HASH')
    return text

def validate_config(config: dict[str,Any]) -> None:
    if config.get('mode')!='LOCAL_STAGING_SQLITE_READ_ONLY_REPLAY':
        raise Era64HError('CONFIG_MODE_INVALID')
    if config.get('chain')!='BSC' or config.get('chain_id')!=56:
        raise Era64HError('CHAIN_MISMATCH')
    if config.get('cluster_inference_authorized') is not False:
        raise Era64HError('CLUSTER_INFERENCE_MUST_BE_FALSE')
    if config.get('successful_wallet_classification_authorized') is not False:
        raise Era64HError('SUCCESSFUL_WALLET_CLASSIFICATION_MUST_BE_FALSE')
    authority=config.get('authority')
    if not isinstance(authority,dict) or any(authority.values()):
        raise Era64HError('AUTHORITY_MUST_BE_ZERO')

def read_rows(conn: sqlite3.Connection,table: str,limit: int) -> list[dict[str,Any]]:
    if table!='era64g_wallet_event_staging_v1':
        raise Era64HError('SOURCE_TABLE_NOT_ALLOWLISTED')
    rows=conn.execute(f'''
      SELECT event_uid,chain,chain_id,event_type,from_address,to_address,token_address,
             amount_raw,tx_hash,log_index,block_number,block_hash,block_time_utc,
             receipt_status,gas_used,effective_gas_price_wei,gas_cost_wei,evidence_kind,
             evidence_hash,source_provider_host,source_artifact,source_artifact_sha256,
             imported_at_utc,raw_event_json
      FROM {table}
      ORDER BY block_number,tx_hash,log_index,event_type,event_uid
      LIMIT ?
    ''',(limit,)).fetchall()
    return [dict(row) for row in rows]

def validate_row(row: dict[str,Any]) -> dict[str,Any]:
    if row.get('chain')!='BSC' or int(row.get('chain_id',0))!=56:
        raise Era64HError('ROW_CHAIN_MISMATCH')
    event_type=str(row.get('event_type') or '').upper()
    if event_type not in {'NATIVE_TRANSFER','TOKEN_TRANSFER'}:
        raise Era64HError('ROW_EVENT_TYPE_INVALID')
    src=validate_address(row.get('from_address'),'from_address')
    dst=validate_address(row.get('to_address'),'to_address')
    token=validate_address(row.get('token_address'),'token_address')
    tx_hash=validate_hash(row.get('tx_hash'),'tx_hash')
    block_hash=validate_hash(row.get('block_hash'),'block_hash')
    evidence_hash=str(row.get('evidence_hash') or '').strip().lower()
    if not EVIDENCE_RE.fullmatch(evidence_hash):
        raise Era64HError('EVIDENCE_HASH_INVALID')
    event_uid=str(row.get('event_uid') or '').strip().lower()
    if not EVIDENCE_RE.fullmatch(event_uid):
        raise Era64HError('EVENT_UID_INVALID')
    block_number=int(row.get('block_number',0))
    if block_number<=0:
        raise Era64HError('BLOCK_NUMBER_INVALID')
    log_index=int(row.get('log_index'))
    if event_type=='NATIVE_TRANSFER' and log_index!=-1:
        raise Era64HError('NATIVE_LOG_INDEX_INVALID')
    if event_type=='TOKEN_TRANSFER' and log_index<0:
        raise Era64HError('TOKEN_LOG_INDEX_INVALID')
    try:
        amount=int(str(row.get('amount_raw')))
        gas_used=int(str(row.get('gas_used')))
        gas_price=int(str(row.get('effective_gas_price_wei')))
        gas_cost=int(str(row.get('gas_cost_wei')))
    except ValueError as exc:
        raise Era64HError('INTEGER_FIELD_INVALID') from exc
    if amount<=0 or gas_used<0 or gas_price<0 or gas_cost<0:
        raise Era64HError('INTEGER_FIELD_OUT_OF_RANGE')
    if gas_cost!=gas_used*gas_price:
        raise Era64HError('GAS_COST_INVARIANT_FAILED')
    block_time=str(row.get('block_time_utc') or '').strip()
    try:
        datetime.fromisoformat(block_time.replace('Z','+00:00'))
    except ValueError as exc:
        raise Era64HError('BLOCK_TIME_INVALID') from exc
    if int(row.get('receipt_status',-1)) not in {0,1}:
        raise Era64HError('RECEIPT_STATUS_INVALID')
    if not str(row.get('evidence_kind') or '').strip():
        raise Era64HError('EVIDENCE_KIND_MISSING')
    if not str(row.get('source_provider_host') or '').strip():
        raise Era64HError('SOURCE_PROVIDER_MISSING')
    raw=json.loads(str(row.get('raw_event_json') or '{}'))
    for key,expected in {
        'chain':'BSC','chain_id':56,'event_type':event_type,'from_address':src,
        'to_address':dst,'token_address':token,'tx_hash':tx_hash,
        'log_index':log_index,'block_number':block_number,'block_hash':block_hash,
        'evidence_hash':evidence_hash
    }.items():
        actual=raw.get(key)
        if isinstance(expected,str):
            actual=str(actual or '').lower() if key not in {'chain','event_type'} else str(actual or '').upper()
            expected=expected.lower() if key not in {'chain','event_type'} else expected.upper()
        if actual!=expected:
            raise Era64HError(f'RAW_EVIDENCE_MISMATCH:{key}')
    return {
      **row,
      'event_type':event_type,'from_address':src,'to_address':dst,'token_address':token,
      'tx_hash':tx_hash,'block_hash':block_hash,'evidence_hash':evidence_hash,
      'event_uid':event_uid,'block_number':block_number,'log_index':log_index,
      'amount_raw':str(amount),'gas_used':str(gas_used),
      'effective_gas_price_wei':str(gas_price),'gas_cost_wei':str(gas_cost),
      'block_time_utc':block_time,
    }

def build_graph(events: list[dict[str,Any]],zero: str) -> dict[str,Any]:
    wallets:set[str]=set()
    node_stats:dict[str,dict[str,Any]]={}
    adjacency:dict[str,set[str]]=defaultdict(set)
    edges:dict[tuple[str,str],dict[str,Any]]={}
    zero_address_event_count=0
    self_transfer_event_count=0
    relationship_event_count=0

    def node(address: str) -> dict[str,Any]:
        if address not in node_stats:
            node_stats[address]={
              'address':address,'in_event_count':0,'out_event_count':0,
              'native_event_count':0,'token_event_count':0,
              'in_counterparties':set(),'out_counterparties':set(),
              'first_block':None,'last_block':None,
            }
        return node_stats[address]

    for event in events:
        src=event['from_address']; dst=event['to_address']
        for address in (src,dst):
            if address!=zero:
                wallets.add(address)
                item=node(address)
                block=event['block_number']
                item['first_block']=block if item['first_block'] is None else min(item['first_block'],block)
                item['last_block']=block if item['last_block'] is None else max(item['last_block'],block)
                item['native_event_count']+=1 if event['event_type']=='NATIVE_TRANSFER' else 0
                item['token_event_count']+=1 if event['event_type']=='TOKEN_TRANSFER' else 0
        if src!=zero:
            node(src)['out_event_count']+=1
            if dst!=zero and dst!=src:
                node(src)['out_counterparties'].add(dst)
        if dst!=zero:
            node(dst)['in_event_count']+=1
            if src!=zero and src!=dst:
                node(dst)['in_counterparties'].add(src)
        if src==zero or dst==zero:
            zero_address_event_count+=1
            continue
        if src==dst:
            self_transfer_event_count+=1
            continue
        relationship_event_count+=1
        adjacency[src].add(dst)
        adjacency[dst].add(src)
        key=(src,dst)
        if key not in edges:
            edges[key]={
              'from_address':src,'to_address':dst,
              'relationship_type':'OBSERVED_TRANSACTION_FLOW_ONLY',
              'event_count':0,'native_event_count':0,'token_event_count':0,
              'tx_hashes':set(),'token_addresses':set(),'evidence_hashes':set(),
              'first_block':event['block_number'],'last_block':event['block_number'],
              'first_time_utc':event['block_time_utc'],'last_time_utc':event['block_time_utc'],
            }
        edge=edges[key]
        edge['event_count']+=1
        edge['native_event_count']+=1 if event['event_type']=='NATIVE_TRANSFER' else 0
        edge['token_event_count']+=1 if event['event_type']=='TOKEN_TRANSFER' else 0
        edge['tx_hashes'].add(event['tx_hash'])
        edge['token_addresses'].add(event['token_address'])
        edge['evidence_hashes'].add(event['evidence_hash'])
        if event['block_number']<edge['first_block']:
            edge['first_block']=event['block_number']; edge['first_time_utc']=event['block_time_utc']
        if event['block_number']>edge['last_block']:
            edge['last_block']=event['block_number']; edge['last_time_utc']=event['block_time_utc']

    for wallet in wallets:
        adjacency.setdefault(wallet,set())

    components=[]
    unseen=set(wallets)
    while unseen:
        start=min(unseen)
        queue=deque([start])
        members=[]
        unseen.remove(start)
        while queue:
            current=queue.popleft()
            members.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(members))
    components.sort(key=lambda members:(-len(members),members[0]))
    component_by_wallet={wallet:f'component_{index:04d}' for index,members in enumerate(components,1) for wallet in members}

    node_output=[]
    for address in sorted(wallets):
        item=node_stats[address]
        counterparties=item['in_counterparties']|item['out_counterparties']
        node_output.append({
          'address':address,
          'component_id':component_by_wallet[address],
          'in_event_count':item['in_event_count'],
          'out_event_count':item['out_event_count'],
          'transfer_event_count':item['in_event_count']+item['out_event_count'],
          'native_event_count':item['native_event_count'],
          'token_event_count':item['token_event_count'],
          'in_counterparty_count':len(item['in_counterparties']),
          'out_counterparty_count':len(item['out_counterparties']),
          'counterparty_count':len(counterparties),
          'first_block':item['first_block'],'last_block':item['last_block'],
        })

    edge_output=[]
    for key in sorted(edges):
        item=edges[key]
        edge_output.append({
          'from_address':item['from_address'],'to_address':item['to_address'],
          'relationship_type':item['relationship_type'],
          'event_count':item['event_count'],
          'native_event_count':item['native_event_count'],
          'token_event_count':item['token_event_count'],
          'distinct_transaction_count':len(item['tx_hashes']),
          'distinct_token_count':len(item['token_addresses']),
          'evidence_count':len(item['evidence_hashes']),
          'first_block':item['first_block'],'last_block':item['last_block'],
          'first_time_utc':item['first_time_utc'],'last_time_utc':item['last_time_utc'],
          'bidirectional_observed':(item['to_address'],item['from_address']) in edges,
          'tx_hashes':sorted(item['tx_hashes']),
          'token_addresses':sorted(item['token_addresses']),
          'evidence_hashes':sorted(item['evidence_hashes']),
        })

    component_output=[
      {'component_id':f'component_{index:04d}','member_count':len(members),'members':members}
      for index,members in enumerate(components,1)
    ]
    graph_core={'nodes':node_output,'edges':edge_output,'components':component_output}
    return {
      'node_count':len(node_output),
      'relationship_event_count':relationship_event_count,
      'relationship_edge_count':len(edge_output),
      'connected_component_count':len(component_output),
      'largest_component_size':max((len(item) for item in components),default=0),
      'singleton_component_count':sum(1 for item in components if len(item)==1),
      'zero_address_event_count':zero_address_event_count,
      'self_transfer_event_count':self_transfer_event_count,
      'excluded_from_relationship_graph_count':zero_address_event_count+self_transfer_event_count,
      'nodes':node_output,'edges':edge_output,'components':component_output,
      'graph_hash':canonical_hash(graph_core),
    }

def run(config_path: Path) -> tuple[dict[str,Any],dict[str,Any]]:
    config=json.loads(config_path.read_text(encoding='utf-8'))
    validate_config(config)
    db=(ROOT/str(config['staging_database'])).resolve()
    allowed=(ROOT/'runtime'/'era64g'/'wallet_events_staging_v1.sqlite3').resolve()
    if db!=allowed or not db.is_file():
        raise Era64HError('STAGING_DATABASE_PATH_INVALID')
    source_control=json.loads((ROOT/str(config['source_control'])).read_text(encoding='utf-8'))
    if source_control.get('status')!='BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED':
        raise Era64HError('SOURCE_CONTROL_STATUS_INVALID')
    before_hash=file_hash(db)
    before_mtime=db.stat().st_mtime_ns
    uri=f'file:{db}?mode=ro&immutable=1'
    conn=sqlite3.connect(uri,uri=True)
    conn.row_factory=sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        integrity=str(conn.execute('PRAGMA integrity_check').fetchone()[0])
        if integrity.lower()!='ok':
            raise Era64HError(f'INTEGRITY_CHECK_FAILED:{integrity}')
        table=str(config['source_table'])
        total=int(conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0])
        unique_count=int(conn.execute(f'''SELECT COUNT(*) FROM (
          SELECT chain_id,tx_hash,log_index FROM {table}
          GROUP BY chain_id,tx_hash,log_index
        )''').fetchone()[0])
        if total>int(config['maximum_events']):
            raise Era64HError('EVENT_BUDGET_EXCEEDED')
        rows=[validate_row(row) for row in read_rows(conn,table,int(config['maximum_events']))]
    finally:
        conn.close()
    after_hash=file_hash(db)
    after_mtime=db.stat().st_mtime_ns
    if before_hash!=after_hash or before_mtime!=after_mtime:
        raise Era64HError('READ_ONLY_DATABASE_INVARIANT_FAILED')
    if len(rows)!=total or unique_count!=total:
        raise Era64HError('EVENT_COUNT_OR_UNIQUENESS_INVARIANT_FAILED')
    if total!=int(source_control.get('staging_event_count',-1)):
        raise Era64HError('SOURCE_CONTROL_EVENT_COUNT_MISMATCH')
    graph=build_graph(rows,str(config['zero_address']))
    if graph['node_count']!=int(source_control.get('distinct_wallet_count',-1)):
        raise Era64HError('DISTINCT_WALLET_COUNT_MISMATCH')
    if graph['relationship_event_count']<=0 or graph['relationship_edge_count']<=0:
        raise Era64HError('RELATIONSHIP_GRAPH_EMPTY')
    evidence_complete=sum(1 for row in rows if row['evidence_hash'] and row['source_provider_host'] and row['source_artifact_sha256'])
    authority=dict(config['authority'])
    generated=datetime.now(timezone.utc).isoformat()
    detail={
      'schema':'tokenoskobi.era64h.staging_replay_relationship_graph.detail.v1',
      'status':'STAGING_REPLAY_RELATIONSHIP_GRAPH_VALIDATED',
      'generated_at_utc':generated,
      'real_data':True,'synthetic_data':False,
      'database_mode':'READ_ONLY_IMMUTABLE_SQLITE',
      'database_write_used':False,'network_access_used':False,
      'database_integrity_check':integrity,
      'database_sha256_before':before_hash,'database_sha256_after':after_hash,
      'database_mtime_ns_before':before_mtime,'database_mtime_ns_after':after_mtime,
      'staging_event_count':total,'unique_event_count':unique_count,
      'evidence_complete_event_count':evidence_complete,
      'evidence_incomplete_event_count':total-evidence_complete,
      'native_transfer_event_count':sum(1 for row in rows if row['event_type']=='NATIVE_TRANSFER'),
      'token_transfer_event_count':sum(1 for row in rows if row['event_type']=='TOKEN_TRANSFER'),
      'relationship_semantics':config['relationship_semantics'],
      'cluster_inference_performed':False,'identity_cluster_count':0,
      'funding_relationship_inference_performed':False,
      'cost_complete_trade_event_count':0,'closed_cycle_count':0,
      'successful_wallet_classification_ready':False,
      'successful_wallet_classification_status':'BLOCKED_INSUFFICIENT_HISTORICAL_COST_COMPLETE_TRADE_DATA',
      'relationship_graph':graph,
      'authority':authority,
      'strongest_alternative_hypotheses':[
        'TRANSFER_COUNTERPARTY_DOES_NOT_PROVE_COMMON_OWNERSHIP',
        'CONTRACT_ROUTER_INTERACTIONS_CAN_CREATE_FALSE_SOCIAL_PROXIMITY',
        'FOUR_BLOCK_CANARY_IS_INSUFFICIENT_FOR_SUCCESSFUL_WALLET_CLASSIFICATION',
        'RAW_TOKEN_AMOUNTS_ARE_NOT_COMPARABLE_WITHOUT_DECIMALS_AND_PRICE_CONTEXT'
      ]
    }
    detail['detail_hash']=canonical_hash({k:v for k,v in detail.items() if k not in {'generated_at_utc','detail_hash'}})
    control={
      'schema':'tokenoskobi.era64h.staging_replay_relationship_graph.control.v1',
      'status':detail['status'],'real_data':True,'synthetic_data':False,
      'staging_event_count':total,'unique_event_count':unique_count,
      'evidence_complete_event_count':evidence_complete,
      'native_transfer_event_count':detail['native_transfer_event_count'],
      'token_transfer_event_count':detail['token_transfer_event_count'],
      'node_count':graph['node_count'],
      'relationship_event_count':graph['relationship_event_count'],
      'relationship_edge_count':graph['relationship_edge_count'],
      'connected_component_count':graph['connected_component_count'],
      'largest_component_size':graph['largest_component_size'],
      'singleton_component_count':graph['singleton_component_count'],
      'zero_address_event_count':graph['zero_address_event_count'],
      'self_transfer_event_count':graph['self_transfer_event_count'],
      'cluster_inference_performed':False,'identity_cluster_count':0,
      'cost_complete_trade_event_count':0,'closed_cycle_count':0,
      'successful_wallet_classification_ready':False,
      'database_write_used':False,'network_access_used':False,
      'database_integrity_check':integrity,
      'database_sha256':after_hash,'graph_hash':graph['graph_hash'],
      'detail_artifact':'data/replay/era64h_staging_replay_relationship_graph_v1.json',
      'detail_hash':detail['detail_hash'],'authority':authority,
    }
    control['result_hash']=canonical_hash(control)
    return detail,control

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--detail',type=Path,required=True)
    parser.add_argument('--control',type=Path,required=True)
    args=parser.parse_args()
    detail,control=run(args.config)
    atomic_json(args.detail,detail)
    atomic_json(args.control,control)
    print(f"ERA64H_REPLAY_STATUS={control['status']}")
    print(f"STAGING_EVENT_COUNT={control['staging_event_count']}")
    print(f"UNIQUE_EVENT_COUNT={control['unique_event_count']}")
    print(f"NODE_COUNT={control['node_count']}")
    print(f"RELATIONSHIP_EVENT_COUNT={control['relationship_event_count']}")
    print(f"RELATIONSHIP_EDGE_COUNT={control['relationship_edge_count']}")
    print(f"CONNECTED_COMPONENT_COUNT={control['connected_component_count']}")
    print(f"LARGEST_COMPONENT_SIZE={control['largest_component_size']}")
    print(f"ZERO_ADDRESS_EVENT_COUNT={control['zero_address_event_count']}")
    print('DATABASE_WRITE_USED=false')
    print('NETWORK_ACCESS_USED=false')
    print('CLUSTER_INFERENCE_PERFORMED=false')
    print('SUCCESSFUL_WALLET_CLASSIFICATION_READY=false')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
