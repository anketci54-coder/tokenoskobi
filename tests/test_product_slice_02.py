import importlib.util
import pathlib
import unittest

PATH = pathlib.Path('/root/tokenoskobi_clean_v1/tools/tokenoskobi_product_slice_02_api.py')
SPEC = importlib.util.spec_from_file_location('slice02', PATH)
M = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(M)


class ProductSlice02Tests(unittest.TestCase):
    def test_address_regex(self):
        self.assertTrue(M.ADDRESS_RE.match('0x' + 'a' * 40))
        self.assertFalse(M.ADDRESS_RE.match('0x1234'))

    def test_bytes32_decode(self):
        value = '0x' + b'TEST'.ljust(32, b'\x00').hex()
        self.assertEqual(M.decode_abi_string(value), 'TEST')

    def test_dynamic_string_decode(self):
        raw = (32).to_bytes(32, 'big') + (4).to_bytes(32, 'big') + b'TEST'.ljust(32, b'\x00')
        self.assertEqual(M.decode_abi_string('0x' + raw.hex()), 'TEST')

    def test_uint_decode(self):
        self.assertEqual(M.decode_uint('0x12'), 18)
        self.assertIsNone(M.decode_uint('bad'))

    def test_hard_block_no_code(self):
        decision = M.make_decision(
            {'code_present': False, 'name': 'X', 'symbol': 'X', 'decimals': 18, 'total_supply': 1},
            {'available': True, 'primary_pool': {'reserve_usd': 100000, 'token_price_usd': 1, 'volume_usd': {'h24': 20000}}},
            {'timeframes': {x: {'status': 'OK'} for x in ('1m','5m','15m','1h')}},
            {'available': True, 'freshness': 'GUNCEL'},
        )
        self.assertEqual(decision['verdict'], 'BLOCK')

    def test_review_low_liquidity(self):
        decision = M.make_decision(
            {'code_present': True, 'name': 'X', 'symbol': 'X', 'decimals': 18, 'total_supply': 1},
            {'available': True, 'primary_pool': {'reserve_usd': 20000, 'token_price_usd': 1, 'volume_usd': {'h24': 20000}}},
            {'timeframes': {x: {'status': 'OK'} for x in ('1m','5m','15m','1h')}},
            {'available': True, 'freshness': 'GUNCEL'},
        )
        self.assertEqual(decision['verdict'], 'REVIEW')

    def test_allow_complete_packet(self):
        decision = M.make_decision(
            {'code_present': True, 'name': 'X', 'symbol': 'X', 'decimals': 18, 'total_supply': 1},
            {'available': True, 'primary_pool': {'reserve_usd': 100000, 'token_price_usd': 1, 'volume_usd': {'h24': 20000}}},
            {'timeframes': {x: {'status': 'OK'} for x in ('1m','5m','15m','1h')}},
            {'available': True, 'freshness': 'GUNCEL'},
        )
        self.assertEqual(decision['verdict'], 'ALLOW')

    def test_fixed_cap_removed(self):
        decision = M.make_decision(
            {'code_present': True, 'name': 'X', 'symbol': 'X', 'decimals': 18, 'total_supply': 1},
            {'available': False, 'primary_pool': None},
            {'timeframes': {}},
            {'available': False},
        )
        self.assertFalse(decision['position_sizing']['fixed_1_to_2_usd_cap'])

    def test_authority_zero(self):
        for key in ('ai_authority','trade_authority','wallet_authority','signing_authority','order_create_authority','real_financial_authority'):
            self.assertEqual(M.AUTHORITY[key], 0)
        self.assertEqual(M.AUTHORITY['paper_trade'], 'DISABLED')
        self.assertEqual(M.AUTHORITY['live_trade'], 'DISABLED')

    def test_sql_identifier_rejects_injection(self):
        with self.assertRaises(M.ProductError):
            M.sql_identifier('x;drop table y')


if __name__ == '__main__':
    unittest.main()
