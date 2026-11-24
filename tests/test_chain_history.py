import tempfile
import unittest
from pathlib import Path

from services.market import chain_history as ch
from services.market import pair_watcher as pw
from tests.test_pair_watcher import TOK, WBNB

PAIR = "0x" + "9" * 40
E18 = 10**18


def sync_log(block, r0, r1):
    return {"blockNumber": hex(block), "data": "0x" + format(r0, "064x") + format(r1, "064x")}


class FakeChain:
    def __init__(self, logs=None, head=1_000_000):
        self.logs, self.head, self.requests = logs or [], head, []

    def __call__(self, method, params):
        if method == "eth_blockNumber":
            return hex(self.head)
        self.requests.append((int(params[0]["fromBlock"], 16), int(params[0]["toBlock"], 16)))
        lo, hi = self.requests[-1]
        return [entry for entry in self.logs if lo <= int(entry["blockNumber"], 16) <= hi]


class ParseTests(unittest.TestCase):
    def test_parse_and_bad_data(self):
        self.assertEqual(ch.parse_sync(sync_log(7, 5, 9)), (7, 5, 9))
        with self.assertRaises(ValueError):
            ch.parse_sync({"blockNumber": "0x1", "data": "0x12"})

    def test_curve_picks_the_quote_side(self):
        events = [(1, 10 * E18, 5), (2, 4 * E18, 6)]
        self.assertEqual(ch.curve(events, True), [(1, 10.0), (2, 4.0)])
        self.assertEqual(ch.curve([(1, 5, 10 * E18)], False), [(1, 10.0)])

    def test_fetch_is_chunked_and_complete(self):
        chain = FakeChain([sync_log(b, 1, 1) for b in (100, 5200, 10500)])
        events = ch.fetch_sync(chain, PAIR, 100, 12000, span=5000)
        self.assertEqual([e[0] for e in events], [100, 5200, 10500])
        self.assertEqual(chain.requests, [(100, 5099), (5100, 10099), (10100, 12000)])

    def test_unreadable_logs_raise(self):
        with self.assertRaises(RuntimeError):
            ch.fetch_sync(lambda m, p: "boom", PAIR, 1, 10)


class CheckTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = pw.Store(Path(tmp.name) / "p.sqlite")
        self.addCleanup(self.store.close)
        target, quote, _ = pw.classify_new_pair(WBNB, TOK)
        self.store.add({"now": 0.0, "items": [{
            "pair": PAIR, "target": target, "quote": quote, "token0": WBNB, "token1": TOK,
            "block": 999_000, "status": "NEW", "reason": None, "detail": None, "due_at": 0.0}]}, 1)
        self.store.decide(PAIR, "KEPT", "LIQUIDITY_OK", "10.0 WBNB", 1.0, None, 10.0)

    def test_matching_history_is_reported_as_matching(self):
        text = ch.check(self.store, FakeChain([sync_log(999_010, 10 * E18, 1), sync_log(999_500, 12 * E18, 1)]))
        self.assertIn("TUTUYOR", text)
        self.assertIn("tutan 1 · tutmayan 0 · veri yok 0 · okunamadı 0", text)

    def test_chain_lower_than_watcher_is_a_mismatch(self):
        text = ch.check(self.store, FakeChain([sync_log(999_010, 2 * E18, 1)]))
        self.assertIn("TUTMUYOR", text)

    def test_no_events_is_no_data_not_safe(self):
        text = ch.check(self.store, FakeChain([]))
        self.assertIn("veri yok", text)
        self.assertIn("DEĞİL", text)

    def test_never_asks_beyond_head_minus_margin_and_unreadable_is_counted_apart(self):
        chain = FakeChain([sync_log(999_010, 10 * E18, 1)], head=999_100)
        ch.check(self.store, chain)
        self.assertLessEqual(max(hi for _, hi in chain.requests), 999_100 - ch.HEAD_MARGIN)
        text = ch.check(self.store, lambda m, p: hex(999_100) if m == "eth_blockNumber" else (_ for _ in ()).throw(RuntimeError("boom")))
        self.assertIn("okunamadı 1", text)
        self.assertIn("veri yok 0", text)

    def test_too_old_pairs_are_skipped(self):
        text = ch.check(self.store, FakeChain([], head=999_000 + ch.MAX_AGE_BLOCKS + 10))
        self.assertIn("bakılan havuz: 0", text)


if __name__ == "__main__":
    unittest.main()
