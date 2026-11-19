"""Offline tests for the new-pair watcher (fake RPC, temp SQLite)."""
import tempfile
import unittest
from pathlib import Path

from services.market import pair_watcher as pw

WBNB, USDT = pw.WBNB, pw.USDT
TOK = "0x" + "a1" * 20
TOK2 = "0x" + "b2" * 20
PAIR = "0x" + "c3" * 20
PAIR2 = "0x" + "d4" * 20


def word(addr):
    return "0x" + "0" * 24 + addr[2:]


def log(t0, t1, pair, block):
    return {"topics": [pw.PAIR_CREATED_TOPIC, word(t0), word(t1)],
            "data": "0x" + "0" * 24 + pair[2:] + "0" * 63 + "1",
            "blockNumber": hex(block)}


def reserves(r0, r1):
    return "0x" + f"{r0:064x}{r1:064x}{0:064x}"


class FakeRpc:
    def __init__(self, logs=(), latest=1000, code="0x6080", res=None, fail=None):
        self.logs, self.latest, self.code, self.res, self.fail = list(logs), latest, code, res, fail
        self.calls = []

    def __call__(self, method, params):
        self.calls.append((method, params))
        if self.fail and method == self.fail:
            raise RuntimeError("down")
        if method == "eth_blockNumber":
            return hex(self.latest)
        if method == "eth_getLogs":
            return self.logs
        if method == "eth_getCode":
            return self.code
        if method == "eth_getStorageAt":
            return "0x" + "0" * 64
        if method == "eth_call":
            if params[0]["data"] == pw.RESERVES_CALL:
                return self.res
            return "0x"
        raise AssertionError(method)


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = pw.Store(Path(tmp.name) / "p.sqlite")
        self.addCleanup(self.store.close)

    def row(self, pair=PAIR):
        return self.store.db.execute("SELECT * FROM pairs WHERE pair=?", (pair,)).fetchone()


class ParseTests(unittest.TestCase):
    def test_topic_literal(self):
        self.assertEqual(pw.PAIR_CREATED_TOPIC,
                         "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9")

    def test_parse_and_garbage(self):
        got = pw.parse_pair_created(log(WBNB, TOK, PAIR, 7))
        self.assertEqual(got, {"token0": WBNB, "token1": TOK, "pair": PAIR, "block": 7})
        for bad in (None, {}, {"topics": [], "data": "0x"},
                    {**log(WBNB, TOK, PAIR, 7), "data": "0x12"},
                    {**log(WBNB, TOK, PAIR, 7), "topics": ["0x1", "0x2", "0x3"]}):
            self.assertIsNone(pw.parse_pair_created(bad))

    def test_classify(self):
        self.assertEqual(pw.classify_new_pair(WBNB, TOK), (TOK, WBNB, None))
        self.assertEqual(pw.classify_new_pair(TOK, USDT), (TOK, USDT, None))
        self.assertEqual(pw.classify_new_pair(WBNB, USDT)[2], "BOTH_QUOTE_TOKENS")
        self.assertEqual(pw.classify_new_pair(TOK, TOK2)[2], "NO_ALLOWED_QUOTE")


class ScanTests(Base):
    def test_first_scan_uses_short_lookback_and_filters(self):
        rpc = FakeRpc([log(WBNB, TOK, PAIR, 990), log(TOK, TOK2, PAIR2, 991)])
        self.assertEqual(pw.scan(self.store, rpc, 100.0), 2)
        query = [c for c in rpc.calls if c[0] == "eth_getLogs"][0][1][0]
        self.assertEqual(query["fromBlock"], hex(1000 - pw.LOOKBACK_BLOCKS + 1))
        self.assertEqual(self.row()["status"], "NEW")
        self.assertEqual(self.row(PAIR2)["reason"], "NO_ALLOWED_QUOTE")
        self.assertEqual(self.store.cursor(), 1000)

    def test_cursor_advances_in_bounded_chunks_and_no_duplicates(self):
        self.store.add({"items": [], "now": 0}, 100)
        rpc = FakeRpc([log(WBNB, TOK, PAIR, 150)], latest=10000)
        pw.scan(self.store, rpc, 1.0)
        self.assertEqual(self.store.cursor(), 100 + pw.MAX_SPAN)
        pw.scan(self.store, rpc, 2.0)  # same log again must not duplicate
        count = self.store.db.execute("SELECT COUNT(*) FROM pairs").fetchone()[0]
        self.assertEqual(count, 1)

    def test_rpc_failure_keeps_cursor(self):
        self.store.add({"items": [], "now": 0}, 100)
        with self.assertRaises(RuntimeError):
            pw.scan(self.store, FakeRpc(fail="eth_getLogs", latest=500), 1.0)
        self.assertEqual(self.store.cursor(), 100)


class CheckTests(Base):
    def add(self, now=0.0, token0=WBNB, token1=TOK):
        target, quote, _ = pw.classify_new_pair(token0, token1)
        self.store.add({"now": now, "items": [{
            "pair": PAIR, "target": target, "quote": quote, "token0": token0, "token1": token1,
            "block": 1, "status": "NEW", "reason": None, "detail": None,
            "due_at": now + pw.CHECK_DELAY_SEC}]}, 1)

    def test_not_due_yet(self):
        self.add()
        self.assertEqual(pw.check_due(self.store, FakeRpc(res=reserves(0, 0)), 10.0)["KEPT"], 0)
        self.assertEqual(self.row()["status"], "NEW")

    def test_kept_with_enough_liquidity(self):
        self.add()
        out = pw.check_due(self.store, FakeRpc(res=reserves(10 * 10**18, 5)), 1000.0)
        self.assertEqual(out["KEPT"], 1)
        self.assertEqual(self.row()["status"], "KEPT")

    def test_quote_on_token1_side_is_read_correctly(self):
        self.add(token0=TOK, token1=WBNB)
        out = pw.check_due(self.store, FakeRpc(res=reserves(10**30, 10 * 10**18)), 1000.0)
        self.assertEqual(out["KEPT"], 1)

    def test_low_liquidity_dropped_with_reason(self):
        self.add()
        pw.check_due(self.store, FakeRpc(res=reserves(10**18, 10**30)), 1000.0)
        self.assertEqual((self.row()["status"], self.row()["reason"]), ("DROPPED", "LIQUIDITY_TOO_LOW"))

    def test_no_code_dropped(self):
        self.add()
        pw.check_due(self.store, FakeRpc(code="0x", res=reserves(1, 1)), 1000.0)
        self.assertEqual(self.row()["reason"], "NO_CODE")

    def test_empty_liquidity_waits_then_drops(self):
        self.add()
        now = 1000.0
        for _ in range(pw.MAX_LIQUIDITY_ATTEMPTS):
            pw.check_due(self.store, FakeRpc(res=reserves(0, 0)), now)
            now += pw.RETRY_SEC + 1
        self.assertEqual(self.row()["reason"], "NO_LIQUIDITY_ADDED")

    def test_errors_retry_then_check_failed_never_kept(self):
        self.add()
        now = 1000.0
        for _ in range(pw.MAX_ERRORS):
            self.assertEqual(self.row()["status"], "NEW")
            pw.check_due(self.store, FakeRpc(fail="eth_getCode"), now)
            now += pw.ERROR_RETRY_SEC + 1
        self.assertEqual((self.row()["status"], self.row()["reason"]), ("DROPPED", "CHECK_FAILED"))

    def test_unreadable_reserves_is_an_error_not_kept(self):
        self.add()
        pw.check_due(self.store, FakeRpc(res="0x"), 1000.0)
        self.assertEqual(self.row()["status"], "NEW")
        self.assertEqual(self.row()["errors"], 1)


class PruneAndReportTests(Base):
    def test_prune_folds_old_drops_into_stats(self):
        old = 1_000_000.0
        self.store.add({"now": old, "items": [
            {"pair": PAIR, "target": TOK, "quote": WBNB, "token0": WBNB, "token1": TOK, "block": 1,
             "status": "DROPPED", "reason": "NO_CODE", "detail": None, "due_at": None}]}, 1)
        now = old + (pw.RETAIN_DROPPED_DAYS + 1) * 86400
        self.assertEqual(self.store.prune(now), 1)
        self.assertIsNone(self.row())
        self.assertIn("NO_CODE: 1", pw.report(self.store))

    def test_run_once_end_to_end(self):
        rpc = FakeRpc([log(WBNB, TOK, PAIR, 999)], res=reserves(10 * 10**18, 1))
        first = pw.run_once(self.store, rpc, 100.0)
        self.assertEqual(first["found"], 1)
        second = pw.run_once(self.store, rpc, 100.0 + pw.CHECK_DELAY_SEC + 1)
        self.assertEqual(second["KEPT"], 1)
        self.assertIn(TOK, pw.report(self.store))


if __name__ == "__main__":
    unittest.main()
