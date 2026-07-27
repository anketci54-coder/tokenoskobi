from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_TARGETED_HISTORY_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_targeted_actor_history_enrichment.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_targeted_actor_history', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def address(char: str) -> str:
    return '0x' + char * 40


def tx_hash(number: int) -> str:
    return '0x' + f'{number:064x}'


def source_event(tx: str, token: str, src: str, dst: str, amount: int, block: int, log_index: int = 0) -> dict:
    return {
        'event_uid': f'{tx}:{log_index}',
        'token_address': token,
        'from_address': src,
        'to_address': dst,
        'amount_raw': str(amount),
        'tx_hash': tx,
        'log_index': log_index,
        'block_number': block,
        'block_time_utc': f'2026-01-01T00:00:{block % 60:02d}+00:00',
        'evidence_hash': f'evidence-{tx}-{log_index}',
    }


def receipt(tx: str, actor: str, target: str, block: int, index: int = 0) -> dict:
    return {
        'tx_hash': tx,
        'block_number': block,
        'transaction_index': index,
        'receipt_status': 1,
        'gas_used': '21000',
        'effective_gas_price_wei': '1000000000',
        'gas_cost_wei': '21000000000000',
        'tx_from_address': actor,
        'tx_to_address': target,
        'evidence_hash': f'receipt-{tx}',
        'raw_receipt_json': '{"logs":[]}',
        'raw_transaction_json': '',
    }


class ProductSlice04TargetedActorHistoryTests(unittest.TestCase):
    def test_compute_actor_net(self):
        actor = address('1')
        token = address('a')
        events = [
            source_event(tx_hash(1), token, address('2'), actor, 100, 1),
            source_event(tx_hash(1), token, actor, address('3'), 40, 1, 1),
        ]
        self.assertEqual(module.compute_actor_net(events, actor), {token: 60})

    def test_select_target_scope_finds_opposite_history(self):
        actor = address('1')
        token = address('a')
        other = address('2')
        target = address('3')
        first, second = tx_hash(1), tx_hash(2)
        source_rows = [
            source_event(first, token, other, actor, 100, 10),
            source_event(second, token, actor, other, 60, 20),
        ]
        receipts = [receipt(first, actor, target, 10), receipt(second, actor, target, 20)]
        result = module.select_target_scope(source_rows, receipts)
        self.assertEqual(result['target_actors'], [actor])
        self.assertEqual(len(result['round_trip_pairs']), 1)
        self.assertEqual(len(result['transactions']), 2)
        self.assertEqual(result['round_trip_pairs'][0]['first_direction'], 'IN')
        self.assertEqual(result['round_trip_pairs'][0]['second_direction'], 'OUT')

    def test_select_target_scope_rejects_one_direction_only(self):
        actor = address('1')
        token = address('a')
        first = tx_hash(1)
        source_rows = [source_event(first, token, address('2'), actor, 100, 10)]
        receipts = [receipt(first, actor, address('3'), 10)]
        with self.assertRaises(module.Slice04TargetedHistoryError):
            module.select_target_scope(source_rows, receipts)

    def test_raw_transaction_from_database(self):
        self.assertIsNone(module.raw_transaction_from_database(''))
        self.assertIsNone(module.raw_transaction_from_database('not-json'))
        self.assertEqual(module.raw_transaction_from_database('{"hash":"x"}'), {'hash': 'x'})

    def test_validate_transaction(self):
        actor = address('1')
        target = address('2')
        tx = tx_hash(1)
        raw = {
            'hash': tx,
            'blockNumber': '0xa',
            'transactionIndex': '0x1',
            'from': actor,
            'to': target,
            'value': '0x0',
            'gas': '0x5208',
            'gasPrice': '0x3b9aca00',
            'nonce': '0x2',
            'input': '0x12345678',
        }
        result = module.validate_transaction(raw, tx, receipt(tx, actor, target, 10, 1))
        self.assertEqual(result['selector'], '0x12345678')
        self.assertEqual(result['actor'], actor)

    def test_validate_transaction_rejects_actor_mismatch(self):
        actor = address('1')
        target = address('2')
        tx = tx_hash(1)
        raw = {
            'hash': tx,
            'blockNumber': '0xa',
            'transactionIndex': '0x0',
            'from': address('4'),
            'to': target,
            'value': '0x0',
            'gas': '0x5208',
            'gasPrice': '0x1',
            'nonce': '0x0',
            'input': '0x',
        }
        with self.assertRaises(module.Slice04TargetedHistoryError):
            module.validate_transaction(raw, tx, receipt(tx, actor, target, 10))

    def test_build_actor_flow(self):
        actor = address('1')
        token_in = address('a')
        token_out = address('b')
        tx = tx_hash(1)
        events = [
            source_event(tx, token_in, address('2'), actor, 50, 1),
            source_event(tx, token_out, actor, address('3'), 20, 1, 1),
        ]
        metadata = {
            token_in: {'symbol': 'A', 'decimals': 1},
            token_out: {'symbol': 'B', 'decimals': 1},
        }
        result = module.build_actor_flow(actor, events, metadata)
        self.assertTrue(result['two_sided_actor_flow'])
        self.assertEqual({item['direction'] for item in result['token_flows']}, {'IN', 'OUT'})

    def test_normalize_amount(self):
        self.assertEqual(module.normalize_amount(1234500, 4), '123.45')
        self.assertEqual(module.normalize_amount(-50, 1), '-5')

    def test_rpc_method_allowlist(self):
        self.assertEqual(module.RpcClient.ALLOWED_METHODS, {'eth_chainId', 'eth_getTransactionByHash'})

    def test_authority_boundary(self):
        self.assertTrue(module.AUTHORITY['network_access'])
        self.assertTrue(module.AUTHORITY['staging_file_write'])
        for key in (
            'source_database_write', 'production_database_write', 'repository_write',
            'panel_mutation', 'service_mutation', 'timer_mutation', 'paper_trade',
            'live_trade', 'wallet', 'signing', 'order_create', 'broadcast',
        ):
            self.assertFalse(module.AUTHORITY[key], key)


if __name__ == '__main__':
    unittest.main()
