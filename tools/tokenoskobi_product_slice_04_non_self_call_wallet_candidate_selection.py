#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/tokenoskobi_clean_v1')
DEFAULT_DB = ROOT / 'runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3'
DEFAULT_EXECUTOR = Path('/var/lib/tokenoskobi-product-slice-04/executor_route_blocker_classification_v1.json')
DEFAULT_OUTPUT = Path('/var/lib/tokenoskobi-product-slice-04/non_self_call_wallet_candidate_selection_v1.json')
SOURCE_TABLE = 'era64i_historical_wallet_transfer_staging_v1'
RECEIPT_TABLE = 'era64j_historical_receipt_cost_enrichment_v1'
EXPECTED_DB_HASH = '99b990df8ebb50096d8ae46c1ab772f7187851ef877ccb8e5d5a0edb9ab0bd6b'
EXPECTED_EXECUTOR_HASH = '7148a81cd6e869a32d501a02a50741c17aa37883108e36401f4183ade616d19f'
EXCLUDED_EXECUTOR = '0x9999b0cdd35d7f3b281ba02efc0d228486940515'
HASH_RE = re.compile(r'^0x[0-9a-f]{64}$')
ADDRESS_RE = re.compile(r'^0x[0-9a-f]{40}$')
MAX_ALL_PAIRS = 5000
MAX_OUTPUT_PAIRS = 20
MAX_OUTPUT_ACTORS = 10
MAX_OUTPUT_TRANSACTIONS = 40

AUTHORITY = {
    'network_access': False,
    'staging_file_write': True,
    'source_database_write': False,
    'production_database_write': False,
    'repository_write': False,
    'panel_mutation': False,
    'service_mutation': False,
    'timer_mutation': False,
    'paper_trade': False,
    'live_trade': False,
    'wallet': False,
    'signing': False,
    'order_create': False,
    'broadcast': False,
}


class Slice04NonSelfCallSelectionError(RuntimeError):
    pass


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_hash(value: Any) -> str:
    text = str(value or '').strip().lower()
    if HASH_RE.fullmatch(text) is None:
        raise Slice04NonSelfCallSelectionError('INVALID_TRANSACTION_HASH')
    return text


def normalize_address(value: Any, *, allow_empty: bool = False) -> str:
    text = str(value or '').strip().lower()
    if allow_empty and text == '':
        return ''
    if ADDRESS_RE.fullmatch(text) is None:
        raise Slice04NonSelfCallSelectionError('INVALID_EVM_ADDRESS')
    return text


def read_json(path: Path, code: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise Slice04NonSelfCallSelectionError(f'{code}_MISSING')
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise Slice04NonSelfCallSelectionError(f'{code}_INVALID_JSON') from exc
    if not isinstance(payload, dict):
        raise Slice04NonSelfCallSelectionError(f'{code}_NOT_OBJECT')
    return payload


def validate_executor(path: Path) -> dict[str, Any]:
    payload = read_json(path, 'EXECUTOR_CLASSIFICATION')
    if payload.get('schema') != 'tokenoskobi.product_slice_04.executor_route_blocker_classification.v1':
        raise Slice04NonSelfCallSelectionError('EXECUTOR_SCHEMA_INVALID')
    if payload.get('status') != 'EXECUTOR_ROUTE_BLOCKERS_CLASSIFIED':
        raise Slice04NonSelfCallSelectionError('EXECUTOR_STATUS_INVALID')
    if payload.get('result_hash') != EXPECTED_EXECUTOR_HASH:
        raise Slice04NonSelfCallSelectionError('EXECUTOR_HASH_INVALID')
    if normalize_address(payload.get('actor')) != EXCLUDED_EXECUTOR:
        raise Slice04NonSelfCallSelectionError('EXECUTOR_ACTOR_INVALID')
    summary = payload.get('summary')
    if not isinstance(summary, dict):
        raise Slice04NonSelfCallSelectionError('EXECUTOR_SUMMARY_INVALID')
    if summary.get('closed_loop_confirmed') is not False:
        raise Slice04NonSelfCallSelectionError('EXECUTOR_CLOSED_LOOP_STATE_INVALID')
    if summary.get('next_safe_step') != 'EXCLUDE_SELF_CALL_EXECUTOR_AND_SELECT_NON_SELF_CALL_WALLET_CANDIDATES':
        raise Slice04NonSelfCallSelectionError('EXECUTOR_NEXT_STEP_INVALID')
    return payload


def load_database(database_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    resolved = database_path.resolve()
    if resolved != DEFAULT_DB.resolve() or not resolved.is_file() or file_sha256(resolved) != EXPECTED_DB_HASH:
        raise Slice04NonSelfCallSelectionError('SOURCE_DATABASE_INVALID')
    uri = f'file:{resolved}?mode=ro&immutable=1'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA query_only=ON')
        if str(conn.execute('PRAGMA integrity_check').fetchone()[0]).lower() != 'ok':
            raise Slice04NonSelfCallSelectionError('SOURCE_DATABASE_INTEGRITY_FAILED')
        tables = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if SOURCE_TABLE not in tables or RECEIPT_TABLE not in tables:
            raise Slice04NonSelfCallSelectionError('SOURCE_TABLES_MISSING')
        source_rows = [dict(row) for row in conn.execute(
            f'''SELECT event_uid,token_address,from_address,to_address,amount_raw,tx_hash,log_index,
                       block_number,block_time_utc,evidence_hash
                FROM {SOURCE_TABLE}
                ORDER BY block_number,tx_hash,log_index'''
        )]
        receipt_rows = [dict(row) for row in conn.execute(
            f'''SELECT tx_hash,block_number,transaction_index,receipt_status,gas_cost_wei,
                       tx_from_address,tx_to_address,evidence_hash,raw_receipt_json,raw_transaction_json
                FROM {RECEIPT_TABLE}
                ORDER BY block_number,transaction_index,tx_hash'''
        )]
    finally:
        conn.close()
    if len(source_rows) != 367 or len(receipt_rows) != 277:
        raise Slice04NonSelfCallSelectionError('SOURCE_COUNTS_CHANGED')
    return source_rows, receipt_rows


def compute_actor_net(events: list[dict[str, Any]], actor: str) -> dict[str, int]:
    net: dict[str, int] = defaultdict(int)
    for event in events:
        token = normalize_address(event.get('token_address'))
        amount = int(str(event.get('amount_raw')))
        if amount <= 0:
            raise Slice04NonSelfCallSelectionError('SOURCE_AMOUNT_INVALID')
        if normalize_address(event.get('from_address')) == actor:
            net[token] -= amount
        if normalize_address(event.get('to_address')) == actor:
            net[token] += amount
    return {token: amount for token, amount in net.items() if amount != 0}


def raw_transaction_available(value: Any) -> bool:
    text = str(value or '').strip()
    if not text:
        return False
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return False
    return isinstance(payload, dict) and bool(payload)


def endpoint_tokens(net: dict[str, int]) -> tuple[list[str], list[str]]:
    outs = sorted(token for token, amount in net.items() if amount < 0)
    ins = sorted(token for token, amount in net.items() if amount > 0)
    return outs, ins


def select_non_self_call_candidates(
    source_rows: list[dict[str, Any]],
    receipt_rows: list[dict[str, Any]],
    excluded_actor: str = EXCLUDED_EXECUTOR,
) -> dict[str, Any]:
    excluded_actor = normalize_address(excluded_actor)
    events_by_tx: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        events_by_tx[normalize_hash(row.get('tx_hash'))].append(row)

    records: list[dict[str, Any]] = []
    actor_token_series: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    excluded_self_call_count = 0
    excluded_executor_transaction_count = 0
    excluded_failed_receipt_count = 0
    non_self_call_source_transaction_count = 0

    seen_receipts: set[str] = set()
    for receipt in receipt_rows:
        tx_hash = normalize_hash(receipt.get('tx_hash'))
        if tx_hash in seen_receipts:
            raise Slice04NonSelfCallSelectionError('RECEIPT_DUPLICATE_TRANSACTION')
        seen_receipts.add(tx_hash)
        actor = normalize_address(receipt.get('tx_from_address'))
        tx_to = normalize_address(receipt.get('tx_to_address'), allow_empty=True)
        if int(receipt.get('receipt_status')) != 1:
            excluded_failed_receipt_count += 1
            continue
        if actor == excluded_actor:
            excluded_executor_transaction_count += 1
            continue
        if not tx_to or actor == tx_to:
            excluded_self_call_count += 1
            continue
        events = events_by_tx.get(tx_hash)
        if not events:
            continue
        net = compute_actor_net(events, actor)
        if not net:
            continue
        non_self_call_source_transaction_count += 1
        outs, ins = endpoint_tokens(net)
        record = {
            'tx_hash': tx_hash,
            'actor': actor,
            'tx_to': tx_to,
            'block_number': int(receipt.get('block_number')),
            'transaction_index': int(receipt.get('transaction_index')),
            'gas_cost_wei': str(receipt.get('gas_cost_wei')),
            'receipt_evidence_hash': str(receipt.get('evidence_hash')),
            'source_event_count': len(events),
            'net_by_token': {token: str(amount) for token, amount in sorted(net.items())},
            'out_tokens': outs,
            'in_tokens': ins,
            'two_sided_actor_flow': bool(outs and ins),
            'single_endpoint_pair': len(outs) == 1 and len(ins) == 1,
            'raw_transaction_available': raw_transaction_available(receipt.get('raw_transaction_json')),
        }
        records.append(record)
        for token, amount in net.items():
            actor_token_series[(actor, token)].append({**record, 'selected_token_net_raw': amount})

    all_pairs: list[dict[str, Any]] = []
    for (actor, token), rows in sorted(actor_token_series.items()):
        ordered = sorted(rows, key=lambda item: (item['block_number'], item['transaction_index'], item['tx_hash']))
        for index, first in enumerate(ordered):
            for second in ordered[index + 1:]:
                first_amount = int(first['selected_token_net_raw'])
                second_amount = int(second['selected_token_net_raw'])
                if not ((first_amount > 0 > second_amount) or (first_amount < 0 < second_amount)):
                    continue
                endpoint_reverse_exact = (
                    first['single_endpoint_pair']
                    and second['single_endpoint_pair']
                    and first['out_tokens'][0] == second['in_tokens'][0]
                    and first['in_tokens'][0] == second['out_tokens'][0]
                )
                selected_token_amount_exact = abs(first_amount) == abs(second_amount)
                both_two_sided = bool(first['two_sided_actor_flow'] and second['two_sided_actor_flow'])
                raw_coverage = bool(first['raw_transaction_available'] and second['raw_transaction_available'])
                same_target = first['tx_to'] == second['tx_to']
                pair = {
                    'actor': actor,
                    'selected_token': token,
                    'first_tx_hash': first['tx_hash'],
                    'first_block_number': first['block_number'],
                    'first_transaction_index': first['transaction_index'],
                    'first_direction': 'IN' if first_amount > 0 else 'OUT',
                    'first_net_raw': str(first_amount),
                    'second_tx_hash': second['tx_hash'],
                    'second_block_number': second['block_number'],
                    'second_transaction_index': second['transaction_index'],
                    'second_direction': 'IN' if second_amount > 0 else 'OUT',
                    'second_net_raw': str(second_amount),
                    'block_distance': second['block_number'] - first['block_number'],
                    'endpoint_reverse_exact': endpoint_reverse_exact,
                    'selected_token_amount_exact': selected_token_amount_exact,
                    'both_transactions_two_sided': both_two_sided,
                    'raw_transaction_coverage_complete': raw_coverage,
                    'same_transaction_target': same_target,
                    'first_tx_to': first['tx_to'],
                    'second_tx_to': second['tx_to'],
                    'first_net_by_token': first['net_by_token'],
                    'second_net_by_token': second['net_by_token'],
                }
                pair['ranking_score'] = (
                    16 * int(endpoint_reverse_exact)
                    + 8 * int(selected_token_amount_exact)
                    + 4 * int(both_two_sided)
                    + 2 * int(raw_coverage)
                    + int(same_target)
                )
                pair['candidate_hash'] = canonical_hash(pair)
                all_pairs.append(pair)
                if len(all_pairs) > MAX_ALL_PAIRS:
                    raise Slice04NonSelfCallSelectionError('ALL_PAIR_SCOPE_EXCEEDED')

    all_pairs.sort(
        key=lambda item: (
            -int(item['ranking_score']),
            int(item['block_distance']),
            item['actor'],
            item['first_tx_hash'],
            item['second_tx_hash'],
            item['selected_token'],
        )
    )
    selected_pairs: list[dict[str, Any]] = []
    selected_actors: set[str] = set()
    selected_hashes: set[str] = set()
    for pair in all_pairs:
        prospective_actors = selected_actors | {pair['actor']}
        prospective_hashes = selected_hashes | {pair['first_tx_hash'], pair['second_tx_hash']}
        if len(prospective_actors) > MAX_OUTPUT_ACTORS or len(prospective_hashes) > MAX_OUTPUT_TRANSACTIONS:
            continue
        selected_pairs.append(pair)
        selected_actors = prospective_actors
        selected_hashes = prospective_hashes
        if len(selected_pairs) >= MAX_OUTPUT_PAIRS:
            break

    record_by_hash = {item['tx_hash']: item for item in records}
    selected_transactions = [record_by_hash[tx_hash] for tx_hash in selected_hashes]
    selected_transactions.sort(key=lambda item: (item['block_number'], item['transaction_index'], item['tx_hash']))
    strong_count = sum(int(item['endpoint_reverse_exact']) for item in selected_pairs)
    exact_amount_count = sum(int(item['endpoint_reverse_exact'] and item['selected_token_amount_exact']) for item in selected_pairs)
    if strong_count:
        next_step = 'BOUNDED_NON_SELF_CALL_TRANSACTION_ENRICHMENT_AND_ROUTE_DECODE'
    elif selected_pairs:
        next_step = 'ENRICH_TOP_NON_SELF_CALL_CANDIDATES_AND_FAIL_CLOSED_ROUTE_DECODE'
    else:
        next_step = 'CURRENT_DATASET_HAS_NO_NON_SELF_CALL_ROUND_TRIP_CANDIDATE_EXTEND_HISTORICAL_SCAN'
    return {
        'records': records,
        'all_pair_count': len(all_pairs),
        'selected_pairs': selected_pairs,
        'selected_actors': sorted(selected_actors),
        'selected_transactions': selected_transactions,
        'excluded_self_call_count': excluded_self_call_count,
        'excluded_executor_transaction_count': excluded_executor_transaction_count,
        'excluded_failed_receipt_count': excluded_failed_receipt_count,
        'non_self_call_source_transaction_count': non_self_call_source_transaction_count,
        'strong_candidate_count': strong_count,
        'exact_amount_strong_candidate_count': exact_amount_count,
        'next_safe_step': next_step,
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    os.chmod(temp, 0o600)
    json.loads(temp.read_text(encoding='utf-8'))
    temp.replace(path)
    os.chmod(path, 0o600)


def run(database_path: Path, executor_path: Path, output_path: Path) -> dict[str, Any]:
    executor = validate_executor(executor_path)
    source_rows, receipt_rows = load_database(database_path)
    selection = select_non_self_call_candidates(source_rows, receipt_rows)
    payload: dict[str, Any] = {
        'schema': 'tokenoskobi.product_slice_04.non_self_call_wallet_candidate_selection.v1',
        'generated_at_utc': iso_now(),
        'status': 'NON_SELF_CALL_WALLET_CANDIDATE_SELECTION_COMPLETED',
        'chain': 'BSC',
        'chain_id': 56,
        'authority': dict(AUTHORITY),
        'source': {
            'database_path': str(database_path.resolve()),
            'database_sha256': file_sha256(database_path),
            'source_event_count': len(source_rows),
            'source_transaction_count': len(receipt_rows),
            'executor_classification_path': str(executor_path),
            'executor_classification_result_hash': executor['result_hash'],
        },
        'policy': {
            'excluded_executor_actor': EXCLUDED_EXECUTOR,
            'exclude_all_self_call_transactions': True,
            'receipt_status_must_equal_one': True,
            'same_actor_same_tracked_token_opposite_direction_required': True,
            'selection_is_candidate_only_not_closed_loop_proof': True,
            'identity_or_ownership_inference_allowed': False,
            'maximum_output_pairs': MAX_OUTPUT_PAIRS,
            'maximum_output_actors': MAX_OUTPUT_ACTORS,
            'maximum_output_transactions': MAX_OUTPUT_TRANSACTIONS,
        },
        'selected_actors': selection['selected_actors'],
        'selected_transactions': selection['selected_transactions'],
        'candidate_pairs': selection['selected_pairs'],
        'top_candidate': selection['selected_pairs'][0] if selection['selected_pairs'] else None,
        'summary': {
            'excluded_executor_transaction_count': selection['excluded_executor_transaction_count'],
            'excluded_self_call_transaction_count': selection['excluded_self_call_count'],
            'excluded_failed_receipt_count': selection['excluded_failed_receipt_count'],
            'non_self_call_source_transaction_count': selection['non_self_call_source_transaction_count'],
            'all_round_trip_pair_count': selection['all_pair_count'],
            'selected_candidate_pair_count': len(selection['selected_pairs']),
            'selected_actor_count': len(selection['selected_actors']),
            'selected_transaction_count': len(selection['selected_transactions']),
            'endpoint_reverse_exact_candidate_count': selection['strong_candidate_count'],
            'endpoint_reverse_and_amount_exact_candidate_count': selection['exact_amount_strong_candidate_count'],
            'closed_loop_confirmed': False,
            'next_safe_step': selection['next_safe_step'],
        },
    }
    payload['result_hash'] = canonical_hash(payload)
    atomic_write_json(output_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=DEFAULT_DB)
    parser.add_argument('--executor', type=Path, default=DEFAULT_EXECUTOR)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.database, args.executor, args.output)
    summary = result['summary']
    print(f'OUTPUT={args.output}')
    for key in (
        'excluded_executor_transaction_count',
        'excluded_self_call_transaction_count',
        'excluded_failed_receipt_count',
        'non_self_call_source_transaction_count',
        'all_round_trip_pair_count',
        'selected_candidate_pair_count',
        'selected_actor_count',
        'selected_transaction_count',
        'endpoint_reverse_exact_candidate_count',
        'endpoint_reverse_and_amount_exact_candidate_count',
    ):
        print(f'{key.upper()}={summary[key]}')
    print('SELECTED_ACTORS=' + json.dumps(result['selected_actors'], separators=(',', ':')))
    for index, pair in enumerate(result['candidate_pairs'], start=1):
        print(
            f'CANDIDATE_PAIR_{index}=actor:{pair["actor"]},token:{pair["selected_token"]},'
            f'first_tx:{pair["first_tx_hash"]},first:{pair["first_direction"]},'
            f'second_tx:{pair["second_tx_hash"]},second:{pair["second_direction"]},'
            f'block_distance:{pair["block_distance"]},endpoint_reverse:{str(pair["endpoint_reverse_exact"]).lower()},'
            f'amount_exact:{str(pair["selected_token_amount_exact"]).lower()},'
            f'two_sided:{str(pair["both_transactions_two_sided"]).lower()},'
            f'raw_coverage:{str(pair["raw_transaction_coverage_complete"]).lower()},'
            f'same_target:{str(pair["same_transaction_target"]).lower()},score:{pair["ranking_score"]}'
        )
    for index, tx in enumerate(result['selected_transactions'], start=1):
        print(
            f'SELECTED_TX_{index}=tx:{tx["tx_hash"]},block:{tx["block_number"]},actor:{tx["actor"]},'
            f'tx_to:{tx["tx_to"]},two_sided:{str(tx["two_sided_actor_flow"]).lower()},'
            f'single_endpoint:{str(tx["single_endpoint_pair"]).lower()},'
            f'raw_available:{str(tx["raw_transaction_available"]).lower()},events:{tx["source_event_count"]}'
        )
    top = result.get('top_candidate')
    if top:
        print(
            f'TOP_CANDIDATE=actor:{top["actor"]},first_tx:{top["first_tx_hash"]},'
            f'second_tx:{top["second_tx_hash"]},token:{top["selected_token"]},'
            f'endpoint_reverse:{str(top["endpoint_reverse_exact"]).lower()},'
            f'amount_exact:{str(top["selected_token_amount_exact"]).lower()},score:{top["ranking_score"]}'
        )
    else:
        print('TOP_CANDIDATE=NONE')
    print(f'RESULT_HASH={result["result_hash"]}')
    print('CLOSED_LOOP_CONFIRMED=false')
    print(f'NEXT_SAFE_STEP={summary["next_safe_step"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
