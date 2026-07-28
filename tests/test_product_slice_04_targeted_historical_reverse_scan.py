from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

MODULE_PATH = Path(
    os.environ.get(
        'PRODUCT_SLICE_04_HISTORICAL_REVERSE_SCAN_MODULE_PATH',
        'tools/tokenoskobi_product_slice_04_targeted_historical_reverse_scan.py',
    )
)
spec = importlib.util.spec_from_file_location('product_slice_04_historical_reverse_scan', MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def address(char: str) -> str:
    return '0x' + char * 40


def tx_hash(char: str) -> str:
    return '0x' + char * 64


class TargetedHistoricalReverseScanTests(unittest.TestCase):
    def test_topic_address_padding(self) -> None:
        actor = address('a')
        self.assertEqual(module.topic_address(actor), '0x' + '0' * 24 + 'a' * 40)

    def test_build_log_filter_out(self) -> None:
        anchor = {'actor': address('a'), 'token': address('b'), 'missing_direction': 'OUT'}
        result = module.build_log_filter(anchor, 100, 200)
        self.assertEqual(result['address'], address('b'))
        self.assertEqual(result['fromBlock'], '0x64')
        self.assertEqual(result['toBlock'], '0xc8')
        self.assertEqual(result['topics'], [module.TRANSFER_TOPIC, module.topic_address(address('a'))])

    def test_build_log_filter_in(self) -> None:
        anchor = {'actor': address('a'), 'token': address('b'), 'missing_direction': 'IN'}
        result = module.build_log_filter(anchor, 1, 2)
        self.assertEqual(
            result['topics'],
            [module.TRANSFER_TOPIC, None, module.topic_address(address('a'))],
        )

    def test_compute_actor_net(self) -> None:
        actor = address('a')
        token1 = address('1')
        token2 = address('2')
        events = [
            {'token_address': token1, 'from_address': actor, 'to_address': address('b'), 'amount_raw': '10'},
            {'token_address': token2, 'from_address': address('c'), 'to_address': actor, 'amount_raw': '7'},
            {'token_address': token2, 'from_address': actor, 'to_address': address('d'), 'amount_raw': '2'},
        ]
        self.assertEqual(module.compute_actor_net(events, actor), {token1: -10, token2: 5})

    def test_select_anchors_only_two_sided_single_endpoint(self) -> None:
        actor = address('a')
        record = {
            'tx_hash': tx_hash('1'),
            'actor': actor,
            'tx_to': address('b'),
            'block_number': 1000,
            'transaction_index': 1,
            'net_by_token': {address('1'): '-10', address('2'): '7'},
            'out_tokens': [address('1')],
            'in_tokens': [address('2')],
            'two_sided_actor_flow': True,
            'single_endpoint_pair': True,
            'raw_transaction_available': True,
            'source_event_count': 2,
        }
        ignored = {
            **record,
            'tx_hash': tx_hash('2'),
            'actor': address('c'),
            'net_by_token': {address('1'): '10'},
            'out_tokens': [],
            'in_tokens': [address('1')],
            'two_sided_actor_flow': False,
            'single_endpoint_pair': False,
        }
        anchors = module.select_anchors([record, ignored])
        self.assertEqual(len(anchors), 2)
        self.assertEqual({item['missing_direction'] for item in anchors}, {'IN', 'OUT'})
        self.assertTrue(all(item['actor'] == actor for item in anchors))

    def test_build_pair_exact_reverse_and_amount(self) -> None:
        actor = address('a')
        token_in = address('1')
        token_out = address('2')
        anchor = {
            'actor': actor,
            'token': token_out,
            'missing_direction': 'OUT',
            'observed_direction': 'IN',
            'anchor_tx_hash': tx_hash('1'),
            'anchor_tx_to': address('b'),
            'anchor_block_number': 200,
            'anchor_input_token': token_in,
            'anchor_output_token': token_out,
            'anchor_input_raw': '10',
            'anchor_output_raw': '7',
        }
        discovered = {
            'tx_hash': tx_hash('2'),
            'tx_to': address('b'),
            'block_number': 100,
            'single_endpoint_pair': True,
            'two_sided_actor_flow': True,
            'out_tokens': [token_out],
            'in_tokens': [token_in],
            'net_by_token': {token_in: '12', token_out: '-7'},
            'selector': '0x12345678',
        }
        pair = module.build_pair(anchor, discovered)
        self.assertTrue(pair['direction_opposite_exact'])
        self.assertTrue(pair['endpoint_reverse_exact'])
        self.assertTrue(pair['position_amount_exact'])
        self.assertFalse(pair['closed_loop_confirmed'])

    def test_build_pair_fails_closed_on_endpoint_mismatch(self) -> None:
        anchor = {
            'actor': address('a'),
            'token': address('2'),
            'missing_direction': 'OUT',
            'observed_direction': 'IN',
            'anchor_tx_hash': tx_hash('1'),
            'anchor_tx_to': address('b'),
            'anchor_block_number': 200,
            'anchor_input_token': address('1'),
            'anchor_output_token': address('2'),
            'anchor_input_raw': '10',
            'anchor_output_raw': '7',
        }
        discovered = {
            'tx_hash': tx_hash('2'),
            'tx_to': address('c'),
            'block_number': 100,
            'single_endpoint_pair': True,
            'two_sided_actor_flow': True,
            'out_tokens': [address('2')],
            'in_tokens': [address('3')],
            'net_by_token': {address('2'): '-7', address('3'): '5'},
            'selector': '0x12345678',
        }
        pair = module.build_pair(anchor, discovered)
        self.assertTrue(pair['direction_opposite_exact'])
        self.assertFalse(pair['endpoint_reverse_exact'])
        self.assertFalse(pair['position_amount_exact'])

    def test_decode_transfer_log(self) -> None:
        actor = address('a')
        recipient = address('b')
        token = address('c')
        log = {
            'address': token,
            'topics': [
                module.TRANSFER_TOPIC,
                module.topic_address(actor),
                module.topic_address(recipient),
            ],
            'data': hex(123),
            'transactionHash': tx_hash('1'),
            'blockNumber': hex(100),
            'logIndex': hex(2),
            'removed': False,
        }
        decoded = module.decode_transfer_log(log)
        self.assertEqual(decoded['from_address'], actor)
        self.assertEqual(decoded['to_address'], recipient)
        self.assertEqual(decoded['amount_raw'], 123)

    def test_rpc_method_allowlist_rejects_write_method(self) -> None:
        client = module.RpcClient(
            {
                'endpoints': ['https://bsc-dataseed.bnbchain.org'],
                'allowed_hosts': ['bsc-dataseed.bnbchain.org'],
                'timeout': 2,
                'retries': 0,
            }
        )
        with self.assertRaisesRegex(module.Slice04HistoricalReverseScanError, 'RPC_METHOD_NOT_ALLOWLISTED'):
            client.call('eth_sendRawTransaction', ['0x'])

    def test_authority_has_no_financial_or_mutation_power(self) -> None:
        self.assertTrue(module.AUTHORITY['network_access'])
        self.assertTrue(module.AUTHORITY['staging_file_write'])
        for key in (
            'source_database_write',
            'production_database_write',
            'repository_write',
            'panel_mutation',
            'service_mutation',
            'timer_mutation',
            'paper_trade',
            'live_trade',
            'wallet',
            'signing',
            'order_create',
            'broadcast',
        ):
            self.assertFalse(module.AUTHORITY[key], key)


if __name__ == '__main__':
    unittest.main()
