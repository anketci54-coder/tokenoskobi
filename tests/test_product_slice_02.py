import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ.setdefault("TOKENOSKOBI_ROOT", str(REPO))
os.environ.setdefault(
    "TOKENOSKOBI_GT_RATE_DIR", tempfile.mkdtemp(prefix="tokenoskobi_gt_test_")
)
SERVER = Path(
    os.getenv(
        "TOKENOSKOBI_SLICE02_SERVER_PATH",
        REPO / "tools/tokenoskobi_product_slice_02_server.py",
    )
)
SPEC = importlib.util.spec_from_file_location("product_slice_02", SERVER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BASE = "0x" + "a" * 40
QUOTE = "0x" + "b" * 40
POOL = "0x" + "c" * 40
OTHER = "0x" + "d" * 40


def pool_item(base=BASE, quote=QUOTE):
    return {
        "id": "bsc_" + POOL,
        "attributes": {
            "address": POOL,
            "name": "BASE / QUOTE",
            "reserve_in_usd": "1000000",
            "base_token_price_usd": "571.05",
            "quote_token_price_usd": "1.001",
            "volume_usd": {"h24": "1000"},
            "price_change_percentage": {"h24": "1.2"},
        },
        "relationships": {
            "base_token": {"data": {"id": "bsc_" + base}},
            "quote_token": {"data": {"id": "bsc_" + quote}},
        },
    }


def ohlcv_payload(base=BASE, quote=QUOTE, close=571.0):
    return {
        "data": {
            "attributes": {
                "ohlcv_list": [
                    [3, close, close, close, close + 2, 100],
                    [2, close, close, close, close + 1, 90],
                    [1, close, close, close, close, 80],
                ]
            }
        },
        "meta": {
            "base": {"address": base},
            "quote": {"address": quote},
        },
    }


def valid_market():
    selected = MODULE.oriented_pool(pool_item(), BASE)
    return {
        "token": {"price_usd": 571.05, "price_source": "TOKEN_ENDPOINT"},
        "selected_pool": selected,
        "target_orientation_verified": True,
    }


class ProductSlice02Tests(unittest.TestCase):
    def test_address(self):
        self.assertTrue(MODULE.ADDR.fullmatch(BASE))
        self.assertFalse(MODULE.ADDR.fullmatch("0x12"))

    def test_uint(self):
        self.assertEqual(MODULE.uint("0x12"), 18)

    def test_text(self):
        self.assertEqual(
            MODULE.text("0x" + b"TKN".ljust(32, b"\0").hex()), "TKN"
        )

    def test_gecko_url_detection(self):
        self.assertTrue(
            MODULE.is_geckoterminal("https://api.geckoterminal.com/api/v2/x")
        )
        self.assertFalse(
            MODULE.is_geckoterminal("https://bsc-dataseed.bnbchain.org")
        )

    def test_pool_base_orientation(self):
        row = MODULE.oriented_pool(pool_item(), BASE)
        self.assertEqual(row["target_side"], "base")
        self.assertEqual(row["price_usd"], 571.05)
        self.assertTrue(row["orientation_verified"])

    def test_pool_quote_orientation(self):
        row = MODULE.oriented_pool(pool_item(), QUOTE)
        self.assertEqual(row["target_side"], "quote")
        self.assertEqual(row["price_usd"], 1.001)
        self.assertTrue(row["orientation_verified"])
        self.assertAlmostEqual(
            row["change_24h_pct"], (1 / 1.012 - 1) * 100, places=8
        )

    def test_pool_unknown_orientation(self):
        row = MODULE.oriented_pool(pool_item(), OTHER)
        self.assertIsNone(row["target_side"])
        self.assertIsNone(row["price_usd"])
        self.assertFalse(row["orientation_verified"])

    def test_market_token_endpoint_price_source(self):
        original = MODULE.request

        def fake(url, body=None):
            if "/pools?" in url:
                return {"data": [pool_item()]}
            if url.endswith("/" + BASE):
                return {
                    "data": {
                        "attributes": {
                            "name": "Base",
                            "symbol": "BASE",
                            "price_usd": "571.05",
                            "market_cap_usd": "1",
                            "fdv_usd": "1",
                        }
                    }
                }
            raise AssertionError(url)

        MODULE.request = fake
        try:
            result = MODULE.market(BASE)
        finally:
            MODULE.request = original

        self.assertEqual(result["token"]["price_usd"], 571.05)
        self.assertEqual(result["token"]["price_source"], "TOKEN_ENDPOINT")

    def test_market_price_fallback_from_oriented_pool(self):
        original = MODULE.request

        def fake(url, body=None):
            if "/pools?" in url:
                return {"data": [pool_item()]}
            if url.endswith("/" + BASE):
                raise RuntimeError("TOKEN_ENDPOINT_DOWN")
            raise AssertionError(url)

        MODULE.request = fake
        try:
            result = MODULE.market(BASE)
        finally:
            MODULE.request = original

        self.assertEqual(result["token"]["price_usd"], 571.05)
        self.assertEqual(
            result["token"]["price_source"],
            "SELECTED_POOL_ORIENTED_FALLBACK",
        )
        self.assertTrue(result["target_orientation_verified"])

    def test_market_null_token_price_uses_oriented_fallback(self):
        original = MODULE.request

        def fake(url, body=None):
            if "/pools?" in url:
                return {"data": [pool_item()]}
            if url.endswith("/" + BASE):
                return {
                    "data": {
                        "attributes": {
                            "name": "Base",
                            "symbol": "BASE",
                            "price_usd": None,
                        }
                    }
                }
            raise AssertionError(url)

        MODULE.request = fake
        try:
            result = MODULE.market(BASE)
        finally:
            MODULE.request = original

        self.assertEqual(result["token"]["price_usd"], 571.05)
        self.assertEqual(
            result["token"]["price_source"],
            "SELECTED_POOL_ORIENTED_FALLBACK",
        )

    def test_market_does_not_fallback_from_unoriented_pool(self):
        original = MODULE.request

        def fake(url, body=None):
            if "/pools?" in url:
                return {"data": [pool_item(QUOTE, OTHER)]}
            if url.endswith("/" + BASE):
                raise RuntimeError("TOKEN_ENDPOINT_DOWN")
            raise AssertionError(url)

        MODULE.request = fake
        try:
            result = MODULE.market(BASE)
        finally:
            MODULE.request = original

        self.assertIsNone(result["selected_pool"])
        self.assertNotIn("price_usd", result["token"])
        self.assertFalse(result["target_orientation_verified"])

    def test_tech_uses_target_selector(self):
        seen = []
        original = MODULE.request

        def fake(url, body=None):
            seen.append(url)
            return ohlcv_payload()

        MODULE.request = fake
        try:
            result = MODULE.tech(POOL, BASE)
        finally:
            MODULE.request = original

        self.assertEqual(len(seen), 6)
        self.assertTrue(all("token=" + BASE in url for url in seen))
        self.assertTrue(
            all(
                row["status"] == "OK"
                and row["target_token_address"] == BASE
                for row in result.values()
            )
        )

    def test_tech_rejects_metadata_without_target(self):
        original = MODULE.request

        def fake(url, body=None):
            return ohlcv_payload(base=QUOTE, quote=OTHER, close=1.0)

        MODULE.request = fake
        try:
            result = MODULE.tech(POOL, BASE)
        finally:
            MODULE.request = original

        self.assertTrue(
            all(
                row["status"] == "VERI_YETERSIZ"
                and "TARGET_TOKEN_NOT_IN_OHLCV_META" in row["error"]
                for row in result.values()
            )
        )

    def test_decide_accepts_consistent_target(self):
        technical = {
            key: {"status": "OK", "target_token_address": BASE, "last": 571.0}
            for key in ("1m", "5m", "15m", "1h")
        }
        decision = MODULE.decide(
            {"code_exists": True},
            valid_market(),
            technical,
            {"fresh": True},
            {"public_rpc_ok": 1, "hybrid_ready": True},
        )
        self.assertEqual(decision["decision"], "ALLOW")
        self.assertEqual(decision["data_quality"], "SUFFICIENT")
        self.assertIn("TARGET_ASSET_ORIENTATION_VERIFIED", decision["evidence"])

    def test_decide_blocks_wrong_target(self):
        technical = {
            "1m": {
                "status": "OK",
                "target_token_address": QUOTE,
                "last": 571,
            }
        }
        decision = MODULE.decide(
            {"code_exists": True},
            valid_market(),
            technical,
            {"fresh": True},
            {"public_rpc_ok": 1, "hybrid_ready": True},
        )
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertIn("TECHNICAL_TARGET_MISMATCH", decision["blockers"])

    def test_decide_blocks_wrong_price_side(self):
        technical = {
            "1m": {"status": "OK", "target_token_address": BASE, "last": 1.0},
            "5m": {"status": "OK", "target_token_address": BASE, "last": 1.0},
        }
        decision = MODULE.decide(
            {"code_exists": True},
            valid_market(),
            technical,
            {"fresh": True},
            {"public_rpc_ok": 1, "hybrid_ready": True},
        )
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertIn(
            "TECHNICAL_TARGET_PRICE_MISMATCH", decision["blockers"]
        )

    def test_decide_blocks_unverified_orientation(self):
        decision = MODULE.decide(
            {"code_exists": True},
            {
                "token": {},
                "selected_pool": None,
                "target_orientation_verified": False,
            },
            {},
            {"fresh": False},
            {"public_rpc_ok": 1, "hybrid_ready": False},
        )
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertIn(
            "TARGET_ASSET_ORIENTATION_UNVERIFIED", decision["blockers"]
        )

    def test_authority_is_zero(self):
        self.assertTrue(
            all(value is False for value in MODULE.CFG["authority"].values())
        )


if __name__ == "__main__":
    unittest.main()
