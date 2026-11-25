import tempfile
import unittest
from pathlib import Path

from services.market import history_lab as hl
from services.market import pair_watcher as pw
from tests.test_pair_watcher import TOK, WBNB

E18 = 10**18
BPM = 10.0  # blok/dakika (test için)


def log(block, idx, r0, r1):
    return {"blockNumber": hex(block), "logIndex": hex(idx), "data": "0x" + format(r0, "064x") + format(r1, "064x")}


class Chain:
    def __init__(self, logs, head=2_000_000, fail=False):
        self.logs, self.head, self.fail, self.calls = logs, head, fail, 0

    def __call__(self, method, params):
        if method == "eth_blockNumber":
            return hex(self.head)
        if method == "eth_getBlockByNumber":
            return {"timestamp": hex(1000 + int(params[0], 16))}   # 1 sn/blok
        self.calls += 1
        if self.fail:
            raise RuntimeError("rate limited")
        lo, hi = int(params[0]["fromBlock"], 16), int(params[0]["toBlock"], 16)
        return [entry for entry in self.logs if lo <= int(entry["blockNumber"], 16) <= hi]


class CurveTests(unittest.TestCase):
    def test_last_event_per_block_wins_and_quote_side_is_used(self):
        chain = Chain([log(100, 2, 4 * E18, 9), log(100, 1, 10 * E18, 9), log(200, 0, 6 * E18, 9)])
        self.assertEqual(hl.fetch_curve(chain, "p", 50, 300, True), [(100, 4.0), (200, 6.0)])
        self.assertEqual(hl.fetch_curve(Chain([log(1, 0, 5, 7 * E18)]), "p", 0, 10, False), [(1, 7.0)])

    def test_seconds_per_block(self):
        self.assertEqual(hl.seconds_per_block(Chain([]), 1_000_000), 1.0)

    def test_unreadable_logs_raise(self):
        with self.assertRaises(RuntimeError):
            hl.fetch_curve(lambda m, p: "x", "p", 0, 10, True)


class SimulateTests(unittest.TestCase):
    def sim(self, curve, age=60, keep=0.9):
        return hl.simulate(curve, 0, BPM, age, keep, horizon_min=360)

    def test_steady_pool_is_candidate_and_survives(self):
        res = self.sim([(5, 10.0), (700, 10.0), (3000, 9.5)])
        self.assertEqual(res, {"candidate": True, "survived": True, "pulled": False})

    def test_pull_after_age_makes_a_pulled_candidate(self):
        res = self.sim([(5, 10.0), (1000, 2.0)])   # çekilme 100. dk, aday yaşı 60 dk
        self.assertEqual(res, {"candidate": True, "survived": False, "pulled": True})

    def test_pull_before_age_is_not_a_candidate(self):
        res = self.sim([(5, 10.0), (100, 2.0)])
        self.assertFalse(res["candidate"])
        self.assertFalse(res["pulled"])

    def test_below_keep_fraction_is_not_a_candidate(self):
        self.assertFalse(self.sim([(5, 10.0), (100, 8.5)], keep=0.9)["candidate"])
        self.assertTrue(self.sim([(5, 10.0), (100, 8.5)], keep=0.8)["candidate"])

    def test_no_event_by_age_is_not_a_candidate(self):
        self.assertFalse(self.sim([(2000, 10.0)])["candidate"])


class FetchAndReportTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = pw.Store(Path(tmp.name) / "p.sqlite")
        self.addCleanup(self.store.close)
        target, quote, _ = pw.classify_new_pair(WBNB, TOK)
        self.store.add({"now": 0.0, "items": [{
            "pair": "0x" + "9" * 40, "target": target, "quote": quote, "token0": WBNB, "token1": TOK,
            "block": 1_900_000, "status": "NEW", "reason": None, "detail": None, "due_at": 0.0}]}, 1)
        self.store.decide("0x" + "9" * 40, "KEPT", "LIQUIDITY_OK", "10.0 WBNB", 1.0, None, 10.0)

    def test_fetch_report_roundtrip_and_resume(self):
        chain = Chain([log(1_900_005, 0, 10 * E18, 1), log(1_900_900, 0, 95 * E18 // 10, 1)])
        self.assertEqual(hl.fetch(self.store, chain, 10, pause=0), {"OK": 1, "NO_DATA": 0, "ERROR": 0})
        calls = chain.calls
        self.assertEqual(hl.fetch(self.store, chain, 10, pause=0), {"OK": 0, "NO_DATA": 0, "ERROR": 0})
        self.assertEqual(chain.calls, calls)   # bir daha çekilmez
        text = hl.report(self.store, 60.0)
        self.assertIn("evren: 1 havuz", text)
        self.assertIn("1 / 1 havuz 6 saat sonunda hâlâ ayakta", text)
        self.assertIn("1/1 (%100)", text)
        self.assertIn("örnek az", text)

    def test_errors_retry_then_stop_and_are_not_in_the_universe(self):
        chain = Chain([], fail=True)
        for _ in range(hl.MAX_ATTEMPTS + 1):
            hl.fetch(self.store, chain, 10, pause=0)
        row = self.store.db.execute("SELECT status, attempts FROM hist_fetch").fetchone()
        self.assertEqual((row["status"], row["attempts"]), ("ERROR", hl.MAX_ATTEMPTS))
        self.assertIn("ERROR 1", hl.report(self.store, 60.0))
        self.assertNotIn("evren:", hl.report(self.store, 60.0))

    def test_no_events_is_no_data_not_pulled(self):
        self.assertEqual(hl.fetch(self.store, Chain([]), 10, pause=0)["NO_DATA"], 1)

    def test_too_young_pair_is_not_fetched(self):
        self.assertEqual(hl.fetch(self.store, Chain([], head=1_900_000 + 100), 10, pause=0),
                         {"OK": 0, "NO_DATA": 0, "ERROR": 0})


if __name__ == "__main__":
    unittest.main()
