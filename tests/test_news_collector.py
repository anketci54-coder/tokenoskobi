"""Offline tests for the news collector and for "scanned, no match" in the panel's news check."""
import copy
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from services.market import news_collector as nc
from services.market import tokenoskobi_product_slice_02_server as market
from tests.test_market_data_validation import TOKEN, decision_inputs

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Alpha listed</title><guid>g1</guid><link>https://x/1</link>
<description>about ALPHA</description><pubDate>Fri, 20 Nov 2026 10:00:00 +0000</pubDate></item>
<item><title>No zone</title><guid>g2</guid><pubDate>Fri, 20 Nov 2026 10:00:00</pubDate></item>
</channel></rss>"""
ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Beta hack</title><id>b1</id><link href="https://x/b"/>
<updated>2026-11-20T09:00:00Z</updated></entry></feed>"""
EVIL = b"""<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "aaaa">]><rss><channel>
<item><title>&a;</title><guid>e</guid></item></channel></rss>"""


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.db = nc.connect(self.dir / "n.sqlite")
        self.addCleanup(self.db.close)


class ParseTests(unittest.TestCase):
    def test_rss_and_atom(self):
        items = nc.parse_feed(RSS)
        self.assertEqual(items[0]["published"], "2026-11-20T10:00:00+00:00")
        self.assertIsNone(items[1]["published"])  # a date without a zone is not trusted
        atom = nc.parse_feed(ATOM)
        self.assertEqual((atom[0]["title"], atom[0]["link"]), ("Beta hack", "https://x/b"))

    def test_bad_feeds_are_rejected(self):
        for data, why in ((EVIL, "DTD_OR_ENTITY_REJECTED"), (b"not xml", "FEED_NOT_XML"),
                          (b"<html/>", "FEED_FORMAT_UNKNOWN"),
                          (b"<rss><channel></channel></rss>", "FEED_EMPTY")):
            with self.subTest(why=why), self.assertRaisesRegex(ValueError, why):
                nc.parse_feed(data)


class RunTests(Base):
    CONFIG = {"min_sources_ok": 2, "feeds": [{"source_id": "a", "url": "u1"},
                                              {"source_id": "b", "url": "u2"},
                                              {"source_id": "c", "url": "u3"}]}

    def test_partial_failure_is_recorded_and_items_are_deduplicated(self):
        data = {"u1": RSS, "u2": ATOM}
        def get(url):
            if url not in data:
                raise OSError("down")
            return data[url]
        first = nc.run_once(self.db, self.CONFIG, get, 1000.0)
        self.assertEqual((first["sources_ok"], first["sources_total"], first["items_new"]), (2, 3, 3))
        self.assertTrue(first["status"]["c"].startswith("FAIL"))
        second = nc.run_once(self.db, self.CONFIG, get, 1100.0)
        self.assertEqual(second["items_new"], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM news_raw_feed_events").fetchone()[0], 3)
        self.assertIn("2/3 açıldı", nc.report(self.db))

    def test_report_before_first_run(self):
        self.assertIn("henüz çalışmadı", nc.report(self.db))


class ScanStateTests(Base):
    def beat(self, ok, min_ok=2, age=60.0):
        self.db.execute("INSERT INTO news_collector_runs(run_at, sources_total, sources_ok, min_ok,"
                        " items_new, detail) VALUES(?,?,?,?,?,?)", (time.time() - age, 3, ok, min_ok, 0, "{}"))
        self.db.commit()

    def test_clean_only_with_fresh_enough_scan(self):
        self.assertFalse(market._scan_state(self.db)["clean"])           # no run yet
        self.beat(2)
        self.assertTrue(market._scan_state(self.db)["clean"])
        self.beat(1)                                                      # newest run: too few sources
        self.assertEqual(market._scan_state(self.db)["why"], "TOO_FEW_SOURCES")
        self.beat(3, age=7200)                                            # older runs do not count
        self.assertEqual(market._scan_state(self.db)["why"], "TOO_FEW_SOURCES")

    def test_stale_scan_is_not_clean(self):
        self.beat(3, age=7200)
        self.assertEqual(market._scan_state(self.db)["why"], "SCAN_STALE")

    def test_zero_min_ok_is_never_clean(self):
        self.beat(0, min_ok=0)
        self.assertFalse(market._scan_state(self.db)["clean"])


class NewsFunctionTests(Base):
    def news(self):
        self.db.commit()
        with patch.object(market, "ROOT", self.dir), patch.object(market, "DBS", [self.dir / "n.sqlite"]):
            return market.news(TOKEN, {"name": "Alpha", "symbol": "ALP"})

    def beat(self, ok=3):
        self.db.execute("INSERT INTO news_collector_runs(run_at, sources_total, sources_ok, min_ok,"
                        " items_new, detail) VALUES(?,?,?,?,?,?)", (time.time(), 3, ok, 2, 0, "{}"))

    def test_no_match_after_fresh_scan_is_measured_nothing(self):
        self.beat()
        result = self.news()
        self.assertIs(result["scanned_clean"], True)
        self.assertEqual(result["reason"], "NEWS_SCANNED_NO_MATCH")
        self.assertIsNot(result["fresh"], True)  # still not "fresh evidence"

    def test_no_scan_heartbeat_keeps_old_behaviour(self):
        result = self.news()
        self.assertIs(result["scanned_clean"], False)
        self.assertEqual(result["reason"], "NEWS_NO_MATCH")

    def test_too_few_sources_keeps_old_behaviour(self):
        self.beat(ok=1)
        self.assertEqual(self.news()["reason"], "NEWS_NO_MATCH")

    def test_a_matching_article_is_never_treated_as_clean(self):
        self.beat()
        self.db.execute("INSERT INTO news_raw_feed_events(source_id, guid, title, summary, link,"
                        " published_at_utc, fetched_at_utc) VALUES('a','g','Alpha rugged','','',"
                        " '2020-01-01T00:00:00+00:00', 'x')")
        result = self.news()
        self.assertFalse(result.get("scanned_clean"))
        self.assertTrue(result["matches"])


class DecideTests(unittest.TestCase):
    def decide(self, news_state):
        values = copy.deepcopy(decision_inputs())
        values[3] = news_state
        return market.decide(*values)

    def test_scanned_clean_news_unlocks_sufficient_quality_but_not_extra_safety(self):
        base = self.decide({"fresh": True})
        scanned = self.decide({"fresh": False, "scanned_clean": True, "reason": "NEWS_SCANNED_NO_MATCH"})
        self.assertEqual((scanned["decision"], scanned["data_quality"]), ("ALLOW", "SUFFICIENT"))
        self.assertIn("NEWS_SCANNED_NO_MATCH", scanned["evidence"])
        self.assertEqual(scanned["risk_score"], base["risk_score"])
        self.assertEqual(scanned["warnings"], base["warnings"])

    def test_unscanned_or_garbage_flags_stay_unverified(self):
        for state in ({"fresh": False, "reason": "NEWS_NO_MATCH"},
                      {"fresh": False, "scanned_clean": "yes", "reason": "NEWS_NO_MATCH"},
                      {"fresh": False, "scanned_clean": 1}, {}, None):
            with self.subTest(state=state):
                result = self.decide(state if state is not None else {})
                self.assertEqual(result["data_quality"], "VERI_YETERSIZ")
                self.assertNotEqual(result["decision"], "ALLOW")

    def test_scanned_clean_never_hides_a_blocker(self):
        values = copy.deepcopy(decision_inputs())
        values[3] = {"fresh": False, "scanned_clean": True}
        values[5] = {**values[5], "sell_ability": "NO_SELLS_OBSERVED"}
        self.assertEqual(market.decide(*values)["decision"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
