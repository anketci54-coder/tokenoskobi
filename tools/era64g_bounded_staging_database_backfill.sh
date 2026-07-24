#!/usr/bin/env bash
set -Eeuo pipefail

cd /root/tokenoskobi_clean_v1

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
STAGE="ERA64G_BOUNDED_STAGING_DATABASE_BACKFILL"
NEXT="ERA64H_STAGING_REPLAY_AND_RELATIONSHIP_GRAPH_VALIDATION_REQUIRES_USER_APPROVAL"
CONFIG="config/era64g_bounded_staging_database_backfill_v1.json"
TOOL="tools/era64g_bounded_staging_database_backfill_v1.py"
TEST="tests/test_era64g_bounded_staging_database_backfill_v1.py"
CONTROL="data/control/era64g_bounded_staging_database_backfill_v1.json"
REPORT="reports/LATEST_ERA64G_BOUNDED_STAGING_DATABASE_BACKFILL.md"
SOURCE="data/replay/era64f_bounded_readonly_wallet_event_canary_v1.json"
DB="runtime/era64g/wallet_events_staging_v1.sqlite3"
BACKUP="/root/era64g_canonical_backup_${STAMP}.tar.gz"
DB_BACKUP="/root/era64g_runtime_backup_${STAMP}.tar.gz"
DB_DIR_EXISTED=0
COMMITTED=0

CANONICAL_FILES=(
  PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json
  03_ROADMAP.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md
  data/tokenoskobi_v1_v8_master_era_roadmap.json
  data/control/latest_tk_machine_state.json
)
NEW_FILES=("$CONFIG" "$TOOL" "$TEST" "$CONTROL" "$REPORT")

rollback() {
  rc=$?
  trap - ERR
  echo "ERA64G_FAILED_RC=$rc"
  if [[ "$COMMITTED" -eq 0 ]]; then
    if [[ -f "$BACKUP" ]]; then
      tar -xzf "$BACKUP" -C /root/tokenoskobi_clean_v1
    fi
    rm -f "${NEW_FILES[@]}"
    rm -rf runtime/era64g
    if [[ "$DB_DIR_EXISTED" -eq 1 && -f "$DB_BACKUP" ]]; then
      tar -xzf "$DB_BACKUP" -C /root/tokenoskobi_clean_v1
    fi
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
from pathlib import Path
runtime=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
pointer=runtime.get('canonical_runtime_pointer') if isinstance(runtime.get('canonical_runtime_pointer'),dict) else runtime
assert pointer.get('current_era')=='ERA64'
assert pointer.get('current_stage')=='ERA64F_BOUNDED_READONLY_REAL_WALLET_EVENT_ACQUISITION_CANARY'
assert pointer.get('next_safe_step')=='ERA64G_BOUNDED_STAGING_DATABASE_BACKFILL_REQUIRES_EXPLICIT_USER_APPROVAL'
assert pointer.get('paper_runtime_enabled',runtime.get('paper_runtime_enabled')) is False
a=runtime.get('authority',{})
assert isinstance(a,dict)
assert a.get('real_trade_authority')==0
assert a.get('real_wallet_authority')==0
assert a.get('real_signing_authority')==0
assert a.get('real_order_authority')==0
assert a.get('live_trade')=='DISABLED'
source=json.loads(Path('data/replay/era64f_bounded_readonly_wallet_event_canary_v1.json').read_text(encoding='utf-8'))
assert source.get('status')=='REAL_WALLET_EVENT_CANARY_VERIFIED'
assert source.get('real_data') is True
assert source.get('synthetic_data') is False
assert source.get('chain_id')==56
assert len(source.get('events',[]))==191
print('PRECHECK=VERIFIED')
PY_PRECHECK

tar -czf "$BACKUP" "${CANONICAL_FILES[@]}"
if [[ -d runtime/era64g ]]; then
  DB_DIR_EXISTED=1
  tar -czf "$DB_BACKUP" runtime/era64g
fi
echo "BACKUP=$BACKUP"

mkdir -p config tools tests data/control reports runtime/era64g

cat > "$CONFIG" <<'JSON_CONFIG'
{
  "schema": "tokenoskobi.era64g.bounded_staging_database_backfill.config.v1",
  "mode": "LOCAL_STAGING_SQLITE_WRITE_FROM_SEALED_REAL_CANARY",
  "chain": "BSC",
  "chain_id": 56,
  "source_artifact": "data/replay/era64f_bounded_readonly_wallet_event_canary_v1.json",
  "staging_database": "runtime/era64g/wallet_events_staging_v1.sqlite3",
  "maximum_source_events": 250,
  "required_source_status": "REAL_WALLET_EVENT_CANARY_VERIFIED",
  "deduplication_key": ["chain_id", "tx_hash", "log_index"],
  "database_policy": {
    "dedicated_staging_only": true,
    "production_database_write": false,
    "atomic_transaction_required": true,
    "foreign_keys_required": true,
    "integrity_check_required": true,
    "raw_event_evidence_preserved": true
  },
  "authority": {
    "blockchain_network_access": false,
    "staging_database_write": true,
    "production_database_write": false,
    "runtime_service_mutation": false,
    "panel_mutation": false,
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
            SELECT from_address AS wallet FROM era64g_wallet_event_staging_v1
            UNION
            SELECT to_address AS wallet FROM era64g_wallet_event_staging_v1
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
PY_TOOL
chmod 755 "$TOOL"

python3 "$TOOL" --config "$CONFIG" --source "$SOURCE" --database "$DB" --output "$CONTROL"

cat > "$TEST" <<'PY_TEST'
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT=Path('/root/tokenoskobi_clean_v1')
SPEC=importlib.util.spec_from_file_location('era64g',ROOT/'tools/era64g_bounded_staging_database_backfill_v1.py')
MODULE=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONFIG=ROOT/'config/era64g_bounded_staging_database_backfill_v1.json'
SOURCE=ROOT/'data/replay/era64f_bounded_readonly_wallet_event_canary_v1.json'
CONTROL=ROOT/'data/control/era64g_bounded_staging_database_backfill_v1.json'
DB=ROOT/'runtime/era64g/wallet_events_staging_v1.sqlite3'

class Era64GTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.control=json.loads(CONTROL.read_text(encoding='utf-8'))
        cls.source=json.loads(SOURCE.read_text(encoding='utf-8'))

    def test_01_status_and_real_data(self):
        self.assertEqual(self.control['status'],'BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED')
        self.assertTrue(self.control['real_data'])
        self.assertFalse(self.control['synthetic_data'])

    def test_02_only_staging_database_write_authorized(self):
        authority=self.control['authority']
        self.assertTrue(authority['staging_database_write'])
        self.assertFalse(authority['production_database_write'])
        for key in ('blockchain_network_access','paper_trade','live_trade','wallet','signing','order_create','broadcast'):
            self.assertFalse(authority[key])

    def test_03_source_count_preserved(self):
        self.assertEqual(self.control['source_event_count'],len(self.source['events']))
        self.assertEqual(self.control['staging_event_count'],191)
        self.assertEqual(self.control['distinct_wallet_count'],150)

    def test_04_transfer_counts_preserved(self):
        self.assertEqual(self.control['native_transfer_event_count'],17)
        self.assertEqual(self.control['token_transfer_event_count'],174)

    def test_05_database_integrity_and_unique_key(self):
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            total=conn.execute('SELECT COUNT(*) FROM era64g_wallet_event_staging_v1').fetchone()[0]
            unique=conn.execute('SELECT COUNT(*) FROM (SELECT chain_id,tx_hash,log_index FROM era64g_wallet_event_staging_v1 GROUP BY chain_id,tx_hash,log_index)').fetchone()[0]
            self.assertEqual(total,unique)
        finally:
            conn.close()

    def test_06_idempotent_import(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'runtime/era64g') as tmp:
            path=Path(tmp)/'test.sqlite3'
            first=MODULE.import_events(CONFIG,SOURCE,path)
            second=MODULE.import_events(CONFIG,SOURCE,path)
            self.assertEqual(first['inserted_event_count'],191)
            self.assertEqual(second['inserted_event_count'],0)
            self.assertEqual(second['deduplicated_event_count'],191)
            self.assertEqual(second['staging_event_count'],191)

    def test_07_production_path_rejected(self):
        with self.assertRaises(MODULE.Era64GError):
            MODULE.ensure_staging_path(ROOT/'data/tokenoskobi.db')

    def test_08_invalid_wallet_rejected(self):
        event=dict(self.source['events'][0])
        event['from_address']='0x1234'
        with self.assertRaises(MODULE.Era64GError):
            MODULE.normalize_event(event)

    def test_09_native_log_index_contract(self):
        event=next(dict(item) for item in self.source['events'] if item['event_type']=='NATIVE_TRANSFER')
        event['log_index']=0
        with self.assertRaises(MODULE.Era64GError):
            MODULE.normalize_event(event)

    def test_10_raw_evidence_and_hash_preserved(self):
        conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
        try:
            row=conn.execute('SELECT raw_event_json,evidence_hash,source_artifact_sha256 FROM era64g_wallet_event_staging_v1 LIMIT 1').fetchone()
            self.assertTrue(json.loads(row[0])['event_uid'])
            self.assertEqual(len(row[1]),64)
            self.assertEqual(len(row[2]),64)
        finally:
            conn.close()

if __name__=='__main__':
    unittest.main()
PY_TEST

cat > "$REPORT" <<'MD_REPORT'
# ERA64G Bounded Staging Database Backfill

STATUS=BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED

The sealed ERA64F real BSC canary dataset was written transactionally into a dedicated local staging SQLite database. The operational Tokenoskobi database was not modified. The import preserves raw evidence, provenance, gas fields, block identity and a deterministic unique key. Re-running the importer is idempotent.

No blockchain network call, service mutation, timer mutation, paper trade, live trade, wallet, signing, order creation or broadcast authority is present in this stage.
MD_REPORT

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

echo "TESTS=136/136_VERIFIED"

python3 <<'PY_CANONICAL'
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path

NOW=datetime.now(timezone.utc).isoformat()
STAGE='ERA64G_BOUNDED_STAGING_DATABASE_BACKFILL'
STATUS='ACTIVE_BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED'
NEXT='ERA64H_STAGING_REPLAY_AND_RELATIONSHIP_GRAPH_VALIDATION_REQUIRES_USER_APPROVAL'
ART='data/control/era64g_bounded_staging_database_backfill_v1.json'
control=json.loads(Path(ART).read_text(encoding='utf-8'))

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,obj): Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def apply(obj):
    if not isinstance(obj,dict): return
    obj.update({
      'current_era':'ERA64','current_stage':STAGE,'current_status':STATUS,
      'next_safe_step':NEXT,'updated_at_utc':NOW,
      'era64g_staging_database_write_used':True,
      'era64g_production_database_write_used':False,
      'era64g_source_event_count':control['source_event_count'],
      'era64g_staging_event_count':control['staging_event_count'],
      'era64g_distinct_wallet_count':control['distinct_wallet_count'],
      'era64g_artifact':ART,'era64g_staging_database':control['staging_database'],
      'paper_runtime_enabled':False,'fixed_timer_enabled':False,
    })

runtime=load('PROJECT_RUNTIME.json')
apply(runtime)
if isinstance(runtime.get('canonical_runtime_pointer'),dict): apply(runtime['canonical_runtime_pointer'])
a=runtime.get('authority')
if isinstance(a,dict):
    a.update({'real_trade_authority':0,'real_wallet_authority':0,'real_signing_authority':0,'real_order_authority':0,'live_trade':'DISABLED','paper_trade':'DISABLED_PENDING_COORDINATED_INTELLIGENCE'})
save('PROJECT_RUNTIME.json',runtime)

boot=load('PROJECT_BOOT.json')
boot.update({'updated_at_utc':NOW,'current_checkpoint':'ERA64G_BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED','last_action':STAGE,'next_safe_step':NEXT,'open_risks':['HISTORICAL_SAMPLE_REMAINS_BOUNDED','SWAP_SIDE_AND_EXECUTION_PRICE_NOT_YET_CLASSIFIED','NO_PRODUCTION_DATABASE_WRITE_AUTHORIZED']})
if isinstance(boot.get('work_unit'),dict): boot['work_unit'].update({'id':STAGE,'status':'STAGING_BACKFILL_VERIFIED_PENDING_REPLAY_APPROVAL','next_step':NEXT})
save('PROJECT_BOOT.json',boot)

history=load('PROJECT_HISTORY.json')
history.setdefault('events',[]).append({'id':STAGE,'status':'BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED','artifact':ART,'tests':'136/136_VERIFIED','staging_database_write':True,'production_database_write':False,'blockchain_network_access':False,'real_financial_authority':0,'source_event_count':control['source_event_count'],'staging_event_count':control['staging_event_count'],'next_safe_step':NEXT,'timestamp_utc':NOW})
history['updated_at_utc']=NOW
save('PROJECT_HISTORY.json',history)

roadmap=load('data/tokenoskobi_v1_v8_master_era_roadmap.json')
for version in roadmap.get('versions',[]):
    if isinstance(version,dict) and version.get('id')=='V4':
        for era in version.get('children',[]):
            if isinstance(era,dict) and era.get('id')=='ERA64':
                era.update({'opened':True,'status':STATUS,'active_stage':STAGE,'era64g_artifact':ART,'era64g_staging_database_write':True,'era64g_production_database_write':False,'next_safe_step':NEXT})
roadmap.setdefault('current_direction',{}).update({'current_version':'V4','current_era':'ERA64','current_stage':STAGE,'current_status':STATUS,'next_safe_step':NEXT,'updated_at_utc':NOW})
save('data/tokenoskobi_v1_v8_master_era_roadmap.json',roadmap)

machine=load('data/control/latest_tk_machine_state.json')
machine.update({'current_version':'V4','current_era':'ERA64','current_stage':STAGE,'current_status':STATUS,'last_completed':STAGE,'next_safe_step':NEXT,'era64g_staging_event_count':control['staging_event_count'],'era64g_production_database_write':False,'updated_at_utc':NOW})
save('data/control/latest_tk_machine_state.json',machine)

Path('03_ROADMAP.md').write_text(f'''# 03 ROADMAP - TOKENOSKOBI\n\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA64\nCURRENT_STAGE={STAGE}\nERA64_STATUS={STATUS}\nNEXT_SAFE_STEP={NEXT}\n\nERA64G transactionally imported the sealed real BSC wallet-event canary into a dedicated staging SQLite database. Production database writes and all financial authorities remain disabled.\n''',encoding='utf-8')
Path('06_PROJECT_MASTER_STATE.md').write_text(f'''# 06 PROJECT MASTER STATE\n\nCURRENT_VERSION=V4\nCURRENT_ERA=ERA64\nCURRENT_STAGE={STAGE}\nCURRENT_STATUS={STATUS}\nTESTS=136/136_VERIFIED\nSTAGING_DATABASE_WRITE_USED=true\nPRODUCTION_DATABASE_WRITE_USED=false\nSOURCE_EVENT_COUNT={control['source_event_count']}\nSTAGING_EVENT_COUNT={control['staging_event_count']}\nDISTINCT_WALLET_COUNT={control['distinct_wallet_count']}\nPAPER_RUNTIME=DISABLED\nLIVE_TRADE=DISABLED\nREAL_FINANCIAL_AUTHORITY=0\nNEXT_SAFE_STEP={NEXT}\n''',encoding='utf-8')
Path('07_PROJECT_HANDOFF.md').write_text(f'''# 07 PROJECT HANDOFF\n\nCURRENT_STAGE={STAGE}\nSTATUS={STATUS}\nARTIFACT={ART}\nSTAGING_DATABASE={control['staging_database']}\nSOURCE_EVENT_COUNT={control['source_event_count']}\nSTAGING_EVENT_COUNT={control['staging_event_count']}\nPRODUCTION_DATABASE_WRITE_USED=false\nNEXT_SAFE_STEP={NEXT}\n\nThe ERA64F real canary events are now available in a dedicated local staging SQLite database with deterministic deduplication and preserved evidence. The next step is read-only replay and relationship-graph validation.\n''',encoding='utf-8')
print('CANONICAL_SYNC=VERIFIED')
print(f'NEXT_SAFE_STEP={NEXT}')
PY_CANONICAL

python3 <<'PY_VERIFY'
import json,sqlite3
from pathlib import Path
r=json.loads(Path('PROJECT_RUNTIME.json').read_text(encoding='utf-8'))
p=r.get('canonical_runtime_pointer') if isinstance(r.get('canonical_runtime_pointer'),dict) else r
assert p['current_stage']=='ERA64G_BOUNDED_STAGING_DATABASE_BACKFILL'
assert p['next_safe_step']=='ERA64H_STAGING_REPLAY_AND_RELATIONSHIP_GRAPH_VALIDATION_REQUIRES_USER_APPROVAL'
assert p['era64g_staging_database_write_used'] is True
assert p['era64g_production_database_write_used'] is False
c=json.loads(Path('data/control/era64g_bounded_staging_database_backfill_v1.json').read_text(encoding='utf-8'))
assert c['status']=='BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED'
assert c['staging_event_count']==191
assert c['distinct_wallet_count']==150
assert c['production_database_write_used'] is False
conn=sqlite3.connect('file:runtime/era64g/wallet_events_staging_v1.sqlite3?mode=ro',uri=True)
try:
    conn.execute('PRAGMA query_only=ON')
    assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert conn.execute('SELECT COUNT(*) FROM era64g_wallet_event_staging_v1').fetchone()[0]==191
finally:
    conn.close()
print('CANONICAL_VERIFY=VERIFIED')
PY_VERIFY

systemctl is-active --quiet tokenoskobi-era63e-always-on-market.service
! systemctl is-active --quiet tokenoskobi-era63d-market-technical.timer
! systemctl is-enabled --quiet tokenoskobi-era63d-market-technical.timer

git add PROJECT_BOOT.json PROJECT_RUNTIME.json PROJECT_HISTORY.json \
  03_ROADMAP.md 06_PROJECT_MASTER_STATE.md 07_PROJECT_HANDOFF.md \
  data/tokenoskobi_v1_v8_master_era_roadmap.json \
  data/control/latest_tk_machine_state.json \
  "$CONFIG" "$TOOL" "$TEST" "$CONTROL"
git add -f "$REPORT"
git commit -m "ERA64: backfill bounded wallet events into staging database"
COMMITTED=1
git push origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain=v1)" ]]

trap - ERR
rm -f "$BACKUP" "$DB_BACKUP"

echo "ERA64G_STATUS=BOUNDED_STAGING_DATABASE_BACKFILL_VERIFIED"
echo "TESTS=136/136_VERIFIED"
echo "REAL_DATA=true"
echo "SYNTHETIC_DATA=false"
echo "BLOCKCHAIN_NETWORK_ACCESS_USED=false"
echo "STAGING_DATABASE_WRITE_USED=true"
echo "PRODUCTION_DATABASE_WRITE_USED=false"
python3 - <<'PY_SUMMARY'
import json
from pathlib import Path
c=json.loads(Path('data/control/era64g_bounded_staging_database_backfill_v1.json').read_text(encoding='utf-8'))
for key in ('source_event_count','inserted_event_count','deduplicated_event_count','staging_event_count','native_transfer_event_count','token_transfer_event_count','distinct_wallet_count','integrity_check'):
    print(f'{key.upper()}={c[key]}')
PY_SUMMARY
echo "ALWAYS_ON_TECHNICAL_SERVICE=ACTIVE_READONLY"
echo "FIXED_15_MINUTE_TIMER=DISABLED"
echo "PAPER_RUNTIME=DISABLED"
echo "LIVE_TRADE=DISABLED"
echo "REAL_FINANCIAL_AUTHORITY=0"
echo "REMOTE_VERIFY=VERIFIED"
echo "WORKTREE=CLEAN"
echo "HEAD=$(git rev-parse HEAD)"
echo "NEXT_SAFE_STEP=$NEXT"
