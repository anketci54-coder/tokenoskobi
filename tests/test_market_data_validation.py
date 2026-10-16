"""Offline regressions for evidence quality at the market decision boundary."""
import sqlite3
from contextlib import closing
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from services.market import tokenoskobi_product_slice_02_server as market

TOKEN = "0x" + "a" * 40
QUOTE = "0x" + "b" * 40
POOL = "0x" + "c" * 40
NOW = 1_800_000_000


def candles(timestamps):
    return {
        "meta": {"base": {"address": TOKEN}, "quote": {"address": QUOTE}},
        "data": {"attributes": {"ohlcv_list": [
            [stamp, 100, 101, 99, 100, 10] for stamp in timestamps
        ]}},
    }


def decision_inputs():
    return [
        {"code_exists": True},
        {
            "token": {"price_usd": 100, "price_source": "TOKEN_ENDPOINT"},
            "selected_pool": {
                "target_token_address": TOKEN, "orientation_verified": True,
                "price_usd": 100, "reserve_usd": 100_000,
            },
            "target_orientation_verified": True,
        },
        {key: {"status": "OK", "target_token_address": TOKEN, "last": 100}
         for key in ("1m", "5m", "15m", "1h")},
        {"fresh": True},
        {"public_rpc_ok": True, "hybrid_ready": True},
    ]


class MarketEvidenceTests(unittest.TestCase):
    def technical(self, payload):
        with patch.object(market, "request", return_value=payload), \
                patch.object(market.time, "time", return_value=NOW):
            return market.tech(POOL, TOKEN)

    def test_missing_technical_data_cannot_allow(self):
        values = decision_inputs()
        values[2] = {}
        result = market.decide(*values)
        self.assertEqual(result["data_quality"], "VERI_YETERSIZ")
        self.assertNotEqual(result["decision"], "ALLOW")
        self.assertEqual(result["authority"], "ADVISORY_ONLY")

    def test_unverified_contract_or_liquidity_cannot_allow(self):
        for missing in ("contract", "liquidity"):
            with self.subTest(missing=missing):
                values = decision_inputs()
                if missing == "contract":
                    values[0] = {}
                else:
                    del values[1]["selected_pool"]["reserve_usd"]
                self.assertNotEqual(market.decide(*values)["decision"], "ALLOW")

    def test_complete_evidence_still_allows(self):
        self.assertEqual(market.decide(*decision_inputs())["decision"], "ALLOW")

    def test_matching_negative_market_prices_cannot_allow(self):
        values = decision_inputs()
        values[1]["token"]["price_usd"] = -100
        values[1]["selected_pool"]["price_usd"] = -100
        for row in values[2].values():
            row["last"] = -100
        self.assertEqual(market.decide(*values)["decision"], "BLOCK")

    def test_recent_candles_remain_usable(self):
        result = self.technical(candles([NOW - 10, NOW - 70, NOW - 130]))
        self.assertTrue(all(row["status"] == "OK" for row in result.values()))

    def test_old_candles_are_insufficient(self):
        result = self.technical(candles([3, 2, 1]))
        self.assertTrue(all(row["status"] == "VERI_YETERSIZ" for row in result.values()))

    def test_future_candles_are_insufficient(self):
        result = self.technical(candles([NOW + 1000, NOW + 940, NOW + 880]))
        self.assertTrue(all(row["status"] == "VERI_YETERSIZ" for row in result.values()))

    def test_candle_age_is_bounded_by_timeframe(self):
        result = self.technical(candles([NOW - 600, NOW - 660, NOW - 720]))
        self.assertEqual(result["1m"]["status"], "VERI_YETERSIZ")
        self.assertEqual(result["1d"]["status"], "OK")

    def test_invalid_or_duplicate_timestamps_are_rejected(self):
        for stamps in ([None, NOW - 60, NOW - 120],
                       [NOW - 10, NOW - 10, NOW - 60],
                       [NOW - 120, NOW - 60, NOW - 10]):
            with self.subTest(stamps=stamps):
                result = self.technical(candles(stamps))
                self.assertTrue(all(row["status"] == "VERI_YETERSIZ"
                                    for row in result.values()))

    def test_nonpositive_prices_are_rejected(self):
        for price in (0, -100):
            with self.subTest(price=price):
                payload = candles([NOW - 10, NOW - 70, NOW - 130])
                for row in payload["data"]["attributes"]["ohlcv_list"]:
                    row[4] = price
                self.assertTrue(all(row["status"] == "VERI_YETERSIZ"
                                    for row in self.technical(payload).values()))


class NewsFreshnessTests(unittest.TestCase):
    def news(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "news.sqlite"
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute("CREATE TABLE news_raw_feed_events "
                                   "(title TEXT, published_at_utc TEXT, fetched_at_utc TEXT)")
                connection.executemany("INSERT INTO news_raw_feed_events VALUES (?, ?, ?)", rows)
            with patch.object(market, "ROOT", root), \
                    patch.object(market, "DBS", [database]), \
                    patch.object(market.time, "time", return_value=NOW):
                return market.news(TOKEN, {"name": "Example Token", "symbol": "EXM"})

    @staticmethod
    def stamp(age):
        return datetime.fromtimestamp(NOW - age, timezone.utc).isoformat()

    def test_recent_matching_news_is_fresh(self):
        result = self.news([(TOKEN, self.stamp(60), self.stamp(10))])
        self.assertTrue(result["fresh"])
        self.assertEqual(result["age_sec"], 60)

    def test_unrelated_recent_news_does_not_refresh_token(self):
        result = self.news([("Another coin", self.stamp(10), self.stamp(10))])
        self.assertFalse(result["fresh"])
        self.assertEqual(result["matches"], [])

    def test_symbol_substring_is_not_a_token_match(self):
        result = self.news([("EXMORE is an unrelated asset", self.stamp(10), self.stamp(10))])
        self.assertFalse(result["fresh"])
        self.assertEqual(result["matches"], [])

    def test_future_news_does_not_count_as_fresh(self):
        result = self.news([(TOKEN, self.stamp(-31_536_000), self.stamp(10))])
        self.assertFalse(result["fresh"])

    def test_refetch_does_not_refresh_old_publication(self):
        result = self.news([(TOKEN, self.stamp(100_000), self.stamp(10))])
        self.assertFalse(result["fresh"])
        self.assertEqual(result["age_sec"], 100_000)

    def test_naive_or_missing_publication_is_not_fresh(self):
        for stamp in (None, "invalid", self.stamp(60).replace("+00:00", "")):
            with self.subTest(stamp=stamp):
                self.assertFalse(self.news([(TOKEN, stamp, self.stamp(10))])["fresh"])

    def test_future_record_does_not_hide_valid_matching_record(self):
        result = self.news([(TOKEN, self.stamp(60), self.stamp(60)),
                            (TOKEN, self.stamp(-3600), self.stamp(10))])
        self.assertTrue(result["fresh"])
        self.assertEqual(result["age_sec"], 60)


if __name__ == "__main__":
    unittest.main()
