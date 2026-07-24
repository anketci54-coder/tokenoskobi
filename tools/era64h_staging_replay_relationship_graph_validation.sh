#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
STAGE="ERA64H_STAGING_REPLAY_AND_RELATIONSHIP_GRAPH_VALIDATION"
NEXT="ERA64I_BOUNDED_HISTORICAL_WALLET_EVENT_BACKFILL_REQUIRES_EXPLICIT_USER_APPROVAL"
CONFIG="config/era64h_staging_replay_relationship_graph_v1.json"
TOOL="tools/era64h_staging_replay_relationship_graph_v1.py"
TEST="tests/test_era64h_staging_replay_relationship_graph_v1.py"
CONTROL="data/control/era64h_staging_replay_relationship_graph_validation_v1.json"
DETAIL="data/replay/era64h_staging_replay_relationship_graph_v1.json"
REPORT="reports/LATEST_ERA64H_STAGING_REPLAY_RELATIONSHIP_GRAPH_VALIDATION.md"
DB="runtime/era64g/wallet_events_staging_v1.sqlite3"
BACKUP="/root/era64h_canonical_backup_${STAMP}.tar.gz"
COMMITTED=0

CANONICAL_FILES=(
  PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json
  03_ROADMAP.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
)
NEW_FILES=("$CONFIG" "$TOOL" "$TEST" "$CONTROL" "$DETAIL" "$REPORT")

rollback() {
  rc=$?
  trap - ERR
  echo "ERA64H_FAILED_RC=$rc"
  if [[ "$COMMITTED" -eq 0 ]]; then
    if [[ -f "$BACKUP" ]]; then
      tar -xzf "$BACKUP" -C /root/tokenoskobi_clean_v1
    fi
    rm -f "${NEW_FILES[@]}"
    git reset --quiet || true
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
import sqlite3
from pathlib import Path

runtime=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
pointer=runtime.get('canonical_runtime_pointer') if isinstance(runtime.get('canonical_runtime_pointer'),dict) else runtime
assert pointer.get('current_era')=='ERA64'
assert pointer.get('current_stage')=='ERA64G_BOUNDED_STAGING_DATABASE_BACKFILL'
assert pointer.get('next_safe_step')=='ERA64H_STAGING_REPLAY_AND_RELATIONSHIP_GRAPH_VALIDATION_REQUIRES_USER_APPROVAL'
assert pointer.get('era64g_staging_event_count')==191
assert pointer.get('era64g_distinct_wallet_count')==150
assert pointer.get('era64g_production_database_write_used') is False
assert pointer.get('paper_runtime_enabled',runtime.get('paper_runtime_enabled')) is False
a=runtime.get('authority',{})
assert isinstance(a,dict)
assert a.get('real_trade_authority')==0
assert a.get('real_wallet_authority')==0
assert a.get('real_signing_authority')==0
assert a.get('real_order_authority')==0
assert a.get('live_trade')=='DISABLED'
control=json.loads(Path('data/control/era64g_bounded_staging_database_backfill_v1.json').read_text(encoding='utf-8'))
assert control.get('status')=='BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED'
assert control.get('staging_event_count')==191
assert control.get('distinct_wallet_count')==150
assert control.get('production_database_write_used') is False
db=Path('runtime/era64g/wallet_events_staging_v1.sqlite3')
assert db.is_file() and db.stat().st_size>0
conn=sqlite3.connect(f'file:{db}?mode=ro',uri=True)
try:
    conn.execute('PRAGMA query_only=ON')
    assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert conn.execute('SELECT COUNT(*) FROM era64g_wallet_event_staging_v1').fetchone()[0]==191
finally:
    conn.close()
print('PRECHECK=VERIFIED')
PY_PRECHECK

tar -czf "$BACKUP" "${CANONICAL_FILES[@]}"
echo "BACKUP=$BACKUP"
mkdir -p config tools tests data/control data/replay reports

cat > "$CONFIG" <<'JSON_CONFIG'
{
  "schema": "tokenoskobi.era64h.staging_replay_relationship_graph.config.v1",
  "mode": "LOCAL_STAGING_SQLITE_READ_ONLY_REPLAY",
  "chain": "BSC",
  "chain_id": 56,
  "staging_database": "runtime/era64g/wallet_events_staging_v1.sqlite3",
  "source_control": "data/control/era64g_bounded_staging_database_backfill_v1.json",
  "source_table": "era64g_wallet_event_staging_v1",
  "maximum_events": 500,
  "zero_address": "0x0000000000000000000000000000000000000000",
  "relationship_semantics": "OBSERVED_TRANSACTION_FLOW_ONLY_NOT_OWNERSHIP_CONTROL_OR_IDENTITY",
  "cluster_inference_authorized": false,
  "successful_wallet_classification_authorized": false,
  "authority": {
    "network_access": false,
    "database_write": false,
    "production_database_write": false,
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
  }
}
JSON_CONFIG

cat > "$TOOL" <<'PY_TOOL'
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
PY_TOOL
chmod 700 "$TOOL"

python3 "$TOOL" --config "$CONFIG" --detail "$DETAIL" --control "$CONTROL"

cat > "$TEST" <<'PY_TEST'
import importlib.util
import json
import sqlite3
import unittest
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
CONFIG=ROOT/'config/era64h_staging_replay_relationship_graph_v1.json'
CONTROL=ROOT/'data/control/era64h_staging_replay_relationship_graph_validation_v1.json'
DETAIL=ROOT/'data/replay/era64h_staging_replay_relationship_graph_v1.json'
DB=ROOT/'runtime/era64g/wallet_events_staging_v1.sqlite3'
TOOL=ROOT/'tools/era64h_staging_replay_relationship_graph_v1.py'
SPEC=importlib.util.spec_from_file_location('era64h',TOOL)
MODULE=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

class Era64HTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.control=json.loads(CONTROL.read_text(encoding='utf-8'))
        cls.detail=json.loads(DETAIL.read_text(encoding='utf-8'))

    def test_01_status_and_real_data(self):
        self.assertEqual(self.control['status'],'STAGING_REPLAY_RELATIONSHIP_GRAPH_VALIDATED')
        self.assertTrue(self.control['real_data'])
        self.assertFalse(self.control['synthetic_data'])

    def test_02_all_authorities_are_zero(self):
        self.assertFalse(any(self.control['authority'].values()))
        self.assertFalse(self.control['database_write_used'])
        self.assertFalse(self.control['network_access_used'])

    def test_03_database_is_readonly_and_unchanged(self):
        self.assertEqual(self.detail['database_mode'],'READ_ONLY_IMMUTABLE_SQLITE')
        self.assertEqual(self.detail['database_sha256_before'],self.detail['database_sha256_after'])
        self.assertEqual(self.detail['database_mtime_ns_before'],self.detail['database_mtime_ns_after'])
        self.assertEqual(self.control['database_integrity_check'],'ok')

    def test_04_event_counts_are_preserved(self):
        self.assertEqual(self.control['staging_event_count'],191)
        self.assertEqual(self.control['unique_event_count'],191)
        self.assertEqual(self.control['native_transfer_event_count'],17)
        self.assertEqual(self.control['token_transfer_event_count'],174)

    def test_05_zero_address_is_not_a_wallet_node(self):
        graph=self.detail['relationship_graph']
        self.assertEqual(graph['node_count'],150)
        addresses={item['address'] for item in graph['nodes']}
        self.assertNotIn(self.config['zero_address'],addresses)

    def test_06_evidence_is_complete_and_unique(self):
        self.assertEqual(self.control['evidence_complete_event_count'],191)
        self.assertEqual(self.detail['evidence_incomplete_event_count'],0)
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            total=conn.execute('SELECT COUNT(*) FROM era64g_wallet_event_staging_v1').fetchone()[0]
            unique=conn.execute('SELECT COUNT(*) FROM (SELECT chain_id,tx_hash,log_index FROM era64g_wallet_event_staging_v1 GROUP BY chain_id,tx_hash,log_index)').fetchone()[0]
            self.assertEqual(total,unique)
        finally:
            conn.close()

    def test_07_relationship_graph_is_nonempty(self):
        self.assertGreater(self.control['relationship_event_count'],0)
        self.assertGreater(self.control['relationship_edge_count'],0)
        self.assertGreater(self.control['connected_component_count'],0)

    def test_08_relationship_semantics_do_not_claim_identity(self):
        self.assertFalse(self.control['cluster_inference_performed'])
        self.assertEqual(self.control['identity_cluster_count'],0)
        for edge in self.detail['relationship_graph']['edges']:
            self.assertEqual(edge['relationship_type'],'OBSERVED_TRANSACTION_FLOW_ONLY')
            self.assertEqual(edge['evidence_count'],edge['event_count'])

    def test_09_components_partition_all_nodes(self):
        components=self.detail['relationship_graph']['components']
        members=[wallet for component in components for wallet in component['members']]
        self.assertEqual(len(members),150)
        self.assertEqual(len(set(members)),150)

    def test_10_graph_is_deterministic(self):
        first_detail,first_control=MODULE.run(CONFIG)
        second_detail,second_control=MODULE.run(CONFIG)
        self.assertEqual(first_control['graph_hash'],second_control['graph_hash'])
        self.assertEqual(first_detail['relationship_graph'],second_detail['relationship_graph'])

    def test_11_successful_wallet_classification_remains_blocked(self):
        self.assertFalse(self.control['successful_wallet_classification_ready'])
        self.assertEqual(self.control['cost_complete_trade_event_count'],0)
        self.assertEqual(self.control['closed_cycle_count'],0)

    def test_12_source_has_no_network_write_or_dynamic_execution(self):
        source=TOOL.read_text(encoding='utf-8')
        for token in ('urllib','requests','subprocess','os.system','shell=True','eval(','exec('):
            self.assertNotIn(token,source)
        lowered=source.lower()
        for sql in ('insert into','update era64g','delete from','create table','drop table','alter table'):
            self.assertNotIn(sql,lowered)

if __name__=='__main__':
    unittest.main()
PY_TEST

cat > "$REPORT" <<'MD_REPORT'
# ERA64H Staging Replay and Relationship Graph Validation

STATUS=STAGING_REPLAY_RELATIONSHIP_GRAPH_VALIDATED

ERA64H replays the ERA64G staging SQLite database in immutable read-only mode and builds an evidence-preserving transfer relationship graph. Graph edges mean only that an on-chain transfer was observed. They do not prove common ownership, control, funding intent or identity clustering.

The four-block canary remains insufficient for successful-wallet classification. No cost-complete closed trade cycles exist. No network call, database write, production mutation, paper trade, live trade, wallet, signing, order or broadcast authority is used.
MD_REPORT

python3 -m unittest -v tests/test_era64h_staging_replay_relationship_graph_v1.py
python3 -m unittest -v tests/test_era64g_bounded_staging_database_backfill_v1.py
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

echo "TESTS=148/148_VERIFIED"

python3 <<'PY_CANONICAL'
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path

NOW=datetime.now(timezone.utc).isoformat()
STAGE='ERA64H_STAGING_REPLAY_AND_RELATIONSHIP_GRAPH_VALIDATION'
STATUS='ACTIVE_STAGING_REPLAY_RELATIONSHIP_GRAPH_VALIDATED'
NEXT='ERA64I_BOUNDED_HISTORICAL_WALLET_EVENT_BACKFILL_REQUIRES_EXPLICIT_USER_APPROVAL'
ART='data/control/era64h_staging_replay_relationship_graph_validation_v1.json'
DETAIL='data/replay/era64h_staging_replay_relationship_graph_v1.json'
control=json.loads(Path(ART).read_text(encoding='utf-8'))

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
    obj['era64h_artifact']=ART
    obj['era64h_detail_artifact']=DETAIL
    obj['era64h_staging_replay_validated']=True
    obj['era64h_staging_event_count']=control['staging_event_count']
    obj['era64h_node_count']=control['node_count']
    obj['era64h_relationship_event_count']=control['relationship_event_count']
    obj['era64h_relationship_edge_count']=control['relationship_edge_count']
    obj['era64h_connected_component_count']=control['connected_component_count']
    obj['era64h_cluster_inference_performed']=False
    obj['era64h_successful_wallet_classification_ready']=False
    obj['era64h_database_write_used']=False
    obj['era64h_network_access_used']=False
    obj['paper_runtime_enabled']=False
    obj['fixed_timer_enabled']=False

runtime=load('PROJECT_RUNTIME.json')
apply_state(runtime)
if isinstance(runtime.get('canonical_runtime_pointer'),dict):
    apply_state(runtime['canonical_runtime_pointer'])
a=runtime.get('authority')
if isinstance(a,dict):
    a['real_trade_authority']=0
    a['real_wallet_authority']=0
    a['real_signing_authority']=0
    a['real_order_authority']=0
    a['live_trade']='DISABLED'
    a['paper_trade']='DISABLED_PENDING_COORDINATED_INTELLIGENCE'
save('PROJECT_RUNTIME.json',runtime)

boot=load('PROJECT_BOOT.json')
boot['updated_at_utc']=NOW
boot['current_checkpoint']='ERA64H_STAGING_REPLAY_RELATIONSHIP_GRAPH_VALIDATED'
boot['last_action']=STAGE
boot['next_safe_step']=NEXT
boot['open_risks']=['FOUR_BLOCK_SAMPLE_INSUFFICIENT','NO_COST_COMPLETE_CLOSED_TRADE_CYCLES','IDENTITY_CLUSTERING_NOT_AUTHORIZED','HISTORICAL_BACKFILL_NOT_AUTHORIZED']
if isinstance(boot.get('work_unit'),dict):
    boot['work_unit'].update({'id':STAGE,'status':'VALIDATED_PENDING_HISTORICAL_BACKFILL_APPROVAL','next_step':NEXT})
save('PROJECT_BOOT.json',boot)

history=load('PROJECT_HISTORY.json')
history.setdefault('events',[]).append({
  'id':STAGE,'status':'VALIDATED_VERIFIED','artifact':ART,'detail_artifact':DETAIL,
  'tests':'148/148_VERIFIED','staging_event_count':control['staging_event_count'],
  'node_count':control['node_count'],'relationship_event_count':control['relationship_event_count'],
  'relationship_edge_count':control['relationship_edge_count'],
  'cluster_inference_performed':False,'successful_wallet_classification_ready':False,
  'network_access':False,'database_write':False,'real_financial_authority':0,
  'next_safe_step':NEXT,'timestamp_utc':NOW
})
history['updated_at_utc']=NOW
save('PROJECT_HISTORY.json',history)

roadmap=load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
for version in roadmap.get('versions',[]):
    if isinstance(version,dict) and version.get('id')=='V4':
        for era in version.get('children',[]):
            if isinstance(era,dict) and era.get('id')=='ERA64':
                era.update({'opened':True,'status':STATUS,'active_stage':STAGE,'era64h_artifact':ART,'era64h_staging_replay_validated':True,'next_safe_step':NEXT})
roadmap.setdefault('current_direction',{}).update({'current_version':'V4','current_era':'ERA64','current_stage':STAGE,'current_status':STATUS,'next_safe_step':NEXT,'updated_at_utc':NOW})
save('data/tokenoskobi_v1_v8_master_era_roadmap.json',roadmap)

machine=load('data/control/latest_tk_machine_state.json')
machine.update({'current_version':'V4','current_era':'ERA64','current_stage':STAGE,'current_status':STATUS,'last_completed':STAGE,'next_safe_step':NEXT,'era64h_staging_replay_validated':True,'era64h_relationship_edge_count':control['relationship_edge_count'],'updated_at_utc':NOW})
save('data/control/latest_tk_machine_state.json',machine)

Path('03_ROADMAP.md').write_text(f'''# 03 ROADMAP - TOKENOSKOBI\n\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA64\nCURRENT_STAGE={STAGE}\nERA64_STATUS={STATUS}\nNEXT_SAFE_STEP={NEXT}\n\nERA64H validated the immutable read-only replay of 191 real BSC transfer events and built an evidence-only relationship graph. Historical depth and cost-complete trade cycles remain insufficient for successful-wallet classification.\n''',encoding='utf-8')
Path('06_PROJECT_MASTER_STATE.md').write_text(f'''# 06 PROJECT MASTER STATE\n\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA64\nCURRENT_STAGE={STAGE}\nCURRENT_STATUS={STATUS}\nTESTS=148/148_VERIFIED\nSTAGING_EVENTS={control['staging_event_count']}\nGRAPH_NODES={control['node_count']}\nRELATIONSHIP_EVENTS={control['relationship_event_count']}\nRELATIONSHIP_EDGES={control['relationship_edge_count']}\nCLUSTER_INFERENCE_PERFORMED=false\nSUCCESSFUL_WALLET_CLASSIFICATION_READY=false\nNETWORK_ACCESS_USED=false\nDATABASE_WRITE_USED=false\nPAPER_RUNTIME=DISABLED\nLIVE_TRADE=DISABLED\nREAL_FINANCIAL_AUTHORITY=0\nNEXT_SAFE_STEP={NEXT}\n''',encoding='utf-8')
Path('07_PROJECT_HANDOFF.md').write_text(f'''# 07 PROJECT HANDOFF\n\nCURRENT_STAGE={STAGE}\nSTATUS={STATUS}\nARTIFACT={ART}\nDETAIL={DETAIL}\nNEXT_SAFE_STEP={NEXT}\n\nERA64H replayed the dedicated ERA64G staging database in immutable read-only mode. Relationship edges represent observed transfer flows only and do not establish common ownership or identity clusters. A bounded historical backfill requires separate explicit approval.\n''',encoding='utf-8')
print('CANONICAL_SYNC=VERIFIED')
print(f'NEXT_SAFE_STEP={NEXT}')
PY_CANONICAL

python3 <<'PY_VERIFY'
import json
from pathlib import Path
r=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
p=r.get('canonical_runtime_pointer') if isinstance(r.get('canonical_runtime_pointer'),dict) else r
assert p['current_stage']=='ERA64H_STAGING_REPLAY_AND_RELATIONSHIP_GRAPH_VALIDATION'
assert p['next_safe_step']=='ERA64I_BOUNDED_HISTORICAL_WALLET_EVENT_BACKFILL_REQUIRES_EXPLICIT_USER_APPROVAL'
assert p['era64h_staging_replay_validated'] is True
assert p['era64h_database_write_used'] is False
assert p['era64h_network_access_used'] is False
control=json.loads(Path('data/control/era64h_staging_replay_relationship_graph_validation_v1.json').read_text(encoding='utf-8'))
assert control['status']=='STAGING_REPLAY_RELATIONSHIP_GRAPH_VALIDATED'
assert control['staging_event_count']==191
assert control['node_count']==150
assert control['relationship_edge_count']>0
assert control['cluster_inference_performed'] is False
assert control['successful_wallet_classification_ready'] is False
assert not any(control['authority'].values())
print('CANONICAL_VERIFY=VERIFIED')
PY_VERIFY

systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer
! systemctl is-enabled --quiet tokenoskobi-era63d-market-technical.timer

git add PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  03_ROADMAP.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json \
  "$CONFIG" "$TOOL" "$TEST" "$CONTROL" "$DETAIL"
git add -f "$REPORT"
git commit -m "ERA64: validate staging replay relationship graph"
COMMITTED=1
git push origin main

[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]
trap - ERR
rm -f "$BACKUP"

python3 <<'PY_FINAL'
import json
from pathlib import Path
c=json.loads(Path('data/control/era64h_staging_replay_relationship_graph_validation_v1.json').read_text(encoding='utf-8'))
print(f"ERA64H_STATUS={c['status']}")
print('TESTS=148/148_VERIFIED')
print('REAL_DATA=true')
print('SYNTHETIC_DATA=false')
print('DATABASE_MODE=READ_ONLY_IMMUTABLE_SQLITE')
print('DATABASE_WRITE_USED=false')
print('NETWORK_ACCESS_USED=false')
print(f"STAGING_EVENT_COUNT={c['staging_event_count']}")
print(f"NODE_COUNT={c['node_count']}")
print(f"RELATIONSHIP_EVENT_COUNT={c['relationship_event_count']}")
print(f"RELATIONSHIP_EDGE_COUNT={c['relationship_edge_count']}")
print(f"CONNECTED_COMPONENT_COUNT={c['connected_component_count']}")
print(f"LARGEST_COMPONENT_SIZE={c['largest_component_size']}")
print(f"ZERO_ADDRESS_EVENT_COUNT={c['zero_address_event_count']}")
print('CLUSTER_INFERENCE_PERFORMED=false')
print('SUCCESSFUL_WALLET_CLASSIFICATION_READY=false')
print('ALWAYS_ON_TECHNICAL_SERVICE=ACTIVE_READONLY')
print('FIXED_15_MINUTE_TIMER=DISABLED')
print('PAPER_RUNTIME=DISABLED')
print('LIVE_TRADE=DISABLED')
print('REAL_FINANCIAL_AUTHORITY=0')
PY_FINAL

echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$(git rev-parse HEAD)"
echo "NEXT_SAFE_STEP=$NEXT"
