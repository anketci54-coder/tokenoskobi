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


class PublicRpcTests(unittest.TestCase):
    def test_first_answering_bsc_endpoint_wins_and_alchemy_is_never_asked(self):
        asked = []
        def call(url, method, params):
            asked.append(url)
            if url == "https://down":
                raise OSError("down")
            return "0x1" if url == "https://eth" else "0x38"
        urls = ["https://down", "https://eth", "https://bsc", "https://other"]
        self.assertEqual(pw.pick_public_rpc(urls, call), "https://bsc")
        self.assertEqual(asked, ["https://down", "https://eth", "https://bsc"])

    def test_no_public_endpoint_is_an_error(self):
        with self.assertRaisesRegex(RuntimeError, "NO_PUBLIC_RPC"):
            pw.pick_public_rpc(["https://a"], lambda *a: (_ for _ in ()).throw(OSError("x")))


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


class WatchTests(Base):
    def keep(self, liq_wbnb=10, now=1000.0):
        target, quote, _ = pw.classify_new_pair(WBNB, TOK)
        self.store.add({"now": 0.0, "items": [{
            "pair": PAIR, "target": target, "quote": quote, "token0": WBNB, "token1": TOK,
            "block": 1, "status": "NEW", "reason": None, "detail": None, "due_at": 0.0}]}, 1)
        self.store.decide(PAIR, "KEPT", "LIQUIDITY_OK", "x", now, None, float(liq_wbnb))

    def test_kept_pair_gets_a_watch_schedule(self):
        self.keep()
        row = self.row()
        self.assertEqual((row["peak"], row["last_liq"]), (10.0, 10.0))
        self.assertEqual(row["watch_due"], 1000.0 + pw.WATCH_INTERVAL_SEC)

    def test_not_due_is_not_read(self):
        self.keep()
        rpc = FakeRpc(res=reserves(0, 0))
        self.assertEqual(pw.check_watch(self.store, rpc, 1001.0)["PULLED"], 0)
        self.assertEqual(rpc.calls, [])

    def test_big_drop_marks_pulled(self):
        self.keep(10)
        now = 1000.0 + pw.WATCH_INTERVAL_SEC + 1
        out = pw.check_watch(self.store, FakeRpc(res=reserves(2 * 10**18, 10**30)), now)
        self.assertEqual(out["PULLED"], 1)
        row = self.row()
        self.assertEqual((row["status"], row["reason"]), ("PULLED", "LIQUIDITY_PULLED"))
        self.assertIn("10.0000 -> 2.0000", row["detail"])
        self.assertIn(TOK, pw.report(self.store))

    def test_small_dip_is_not_pulled_and_peak_follows_growth(self):
        self.keep(10)
        now = 1000.0 + pw.WATCH_INTERVAL_SEC + 1
        pw.check_watch(self.store, FakeRpc(res=reserves(8 * 10**18, 1)), now)
        self.assertEqual(self.row()["status"], "KEPT")
        now += pw.WATCH_INTERVAL_SEC + 1
        pw.check_watch(self.store, FakeRpc(res=reserves(30 * 10**18, 1)), now)
        self.assertEqual(self.row()["peak"], 30.0)
        now += pw.WATCH_INTERVAL_SEC + 1
        pw.check_watch(self.store, FakeRpc(res=reserves(14 * 10**18, 1)), now)
        self.assertEqual(self.row()["status"], "PULLED")

    def test_unreadable_reserves_neither_pull_nor_clear(self):
        self.keep()
        now = 1000.0 + pw.WATCH_INTERVAL_SEC + 1
        for rpc in (FakeRpc(res="0x"), FakeRpc(fail="eth_call")):
            out = pw.check_watch(self.store, rpc, now)
            self.assertEqual(out["WATCH_ERRORS"], 1)
            self.assertEqual(self.row()["status"], "KEPT")
            now += pw.ERROR_RETRY_SEC + 1

    def test_watch_ends_after_window(self):
        self.keep()
        now = 1000.0 + pw.WATCH_HOURS * 3600 + 1
        pw.check_watch(self.store, FakeRpc(res=reserves(10 * 10**18, 1)), now)
        row = self.row()
        self.assertEqual(row["status"], "KEPT")
        self.assertIsNone(row["watch_due"])

    def test_kept_rows_from_before_the_watch_are_backfilled(self):
        target, quote, _ = pw.classify_new_pair(WBNB, TOK)
        self.store.add({"now": 0.0, "items": [{
            "pair": PAIR, "target": target, "quote": quote, "token0": WBNB, "token1": TOK,
            "block": 1, "status": "NEW", "reason": None, "detail": None, "due_at": 0.0}]}, 1)
        with self.store.db:  # old-style KEPT row: no watch columns filled
            self.store.db.execute("UPDATE pairs SET status='KEPT', detail='8.7437 WBNB',"
                                  " decided_at=1000 WHERE pair=?", (PAIR,))
        self.assertEqual(self.store.backfill_watch(5000.0), 1)
        row = self.row()
        self.assertEqual((row["peak"], row["watch_due"]), (8.7437, 5000.0))
        self.assertEqual(row["watch_until"], 1000 + pw.WATCH_HOURS * 3600)
        self.assertEqual(self.store.backfill_watch(6000.0), 0)  # idempotent
        out = pw.check_watch(self.store, FakeRpc(res=reserves(10**18, 1)), 5001.0)
        self.assertEqual(out["PULLED"], 1)

    def test_report_summarises_outcome_and_time_to_pull(self):
        self.keep(10, now=1000.0)
        pw.check_watch(self.store, FakeRpc(res=reserves(10**18, 1)), 1000.0 + 600)
        text = pw.report(self.store)
        self.assertIn("eleği geçen: 1 · likiditesi çekilen: 1 (%100.0) · hâlâ ayakta: 0", text)
        self.assertIn("ortanca 10", text)

    def test_backfilled_pull_is_not_given_a_time(self):
        self.keep(10, now=1000.0)
        with self.store.db:
            self.store.db.execute("UPDATE pairs SET watch_due=NULL, watch_until=NULL, peak=NULL,"
                                  " kept_at=NULL, detail='10.0000 WBNB' WHERE pair=?", (PAIR,))
        self.store.backfill_watch(5000.0)
        pw.check_watch(self.store, FakeRpc(res=reserves(10**18, 1)), 5001.0)
        text = pw.report(self.store)
        self.assertNotIn("çekilme süresi", text)
        self.assertIn("1 kaydın çekilme zamanı bilinmiyor", text)

    def add_kept(self, pair, kept_at, liq=10.0, token=TOK):
        target, quote, _ = pw.classify_new_pair(WBNB, token)
        self.store.add({"now": 0.0, "items": [{
            "pair": pair, "target": target, "quote": quote, "token0": WBNB, "token1": token,
            "block": 1, "status": "NEW", "reason": None, "detail": None, "due_at": 0.0}]}, 1)
        self.store.decide(pair, "KEPT", "LIQUIDITY_OK", f"{liq} WBNB", kept_at, None, liq)

    def test_wilson_interval_basics(self):
        low, high = pw.wilson(50, 100)
        self.assertAlmostEqual(low, 0.4038, places=3)
        self.assertAlmostEqual(high, 0.5962, places=3)
        low, high = pw.wilson(0, 10)
        self.assertEqual(low, 0.0)
        self.assertGreater(high, 0.25)

    def test_survival_cohort_is_everyone_watched_for_the_full_horizon(self):
        pairs = ["0x" + f"{i:040x}" for i in range(1, 5)]
        for pair in pairs:
            self.add_kept(pair, 1000.0)
        # A pulled after 5 min, B pulled after 90 min; C and D still alive.
        self.store.mark_pulled(pairs[0], "x", 1000.0 + 300, 10.0, 0.0)
        self.store.mark_pulled(pairs[1], "x", 1000.0 + 5400, 10.0, 0.0)
        table = {r["horizon"]: r for r in pw.survival_table(self.store, 1000.0 + 7200)}
        self.assertEqual((table[10]["pulled"], table[10]["n"]), (1, 4))
        self.assertEqual((table[60]["pulled"], table[60]["n"]), (1, 4))
        self.assertEqual((table[180]["pulled"], table[180]["n"]), (0, 0))  # nobody watched 3 h yet

    def test_early_pulls_do_not_inflate_the_rate_while_survivors_are_still_young(self):
        # Regression: 3 pulls at 5 min, 7 survivors kept 20 min ago. Horizon 30 must not read 100%.
        pairs = ["0x" + f"{i:040x}" for i in range(20, 30)]
        for pair in pairs:
            self.add_kept(pair, 1000.0)
        for pair in pairs[:3]:
            self.store.mark_pulled(pair, "x", 1000.0 + 300, 10.0, 0.0)
        table = {r["horizon"]: r for r in pw.survival_table(self.store, 1000.0 + 1200)}
        self.assertEqual((table[30]["pulled"], table[30]["n"]), (0, 0))  # no one watched 30 min yet
        self.assertEqual((table[10]["pulled"], table[10]["n"]), (3, 10))

    def test_watch_window_end_counts_as_full_observation(self):
        pair = "0x" + "9" * 40
        self.add_kept(pair, 1000.0)
        table = {r["horizon"]: r for r in pw.survival_table(self.store, 1000.0 + pw.WATCH_HOURS * 3600 + 99999)}
        self.assertEqual((table[180]["pulled"], table[180]["n"]), (0, 1))

    def test_empty_table_says_no_sample(self):
        text = pw.report(self.store, now=5000.0)
        self.assertIn("10 dk içinde: henüz örnek yok", text)
        self.assertIn("toplam 0 aday", text)

    def test_candidates_need_age_and_kept_liquidity(self):
        old, young, shrunk = ("0x" + f"{i:040x}" for i in (11, 12, 13))
        toks = {old: "0x" + "e1" * 20, young: "0x" + "e2" * 20, shrunk: "0x" + "e3" * 20}
        self.add_kept(old, 1000.0, token=toks[old])
        self.add_kept(young, 1000.0 + 3000, token=toks[young])
        self.add_kept(shrunk, 1000.0, token=toks[shrunk])
        self.store.watch_update(shrunk, peak=10.0, liq=8.0, due=None)
        text = pw.report(self.store, now=1000.0 + 3700, min_age_min=60, keep_fraction=0.9)
        section = text.split("Adaylar")[1].split("Likiditesi")[0]
        self.assertIn("toplam 1 aday", section)
        self.assertIn(toks[old], section)
        self.assertNotIn(toks[young], section)
        self.assertNotIn(toks[shrunk], section)

    def test_old_database_is_migrated(self):
        import sqlite3
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "old.sqlite"
        db = sqlite3.connect(path)
        db.execute("CREATE TABLE pairs(pair TEXT PRIMARY KEY, target TEXT, quote TEXT, token0 TEXT,"
                   " token1 TEXT, block INTEGER, seen_at REAL, status TEXT, reason TEXT, detail TEXT,"
                   " attempts INTEGER DEFAULT 0, errors INTEGER DEFAULT 0, due_at REAL,"
                   " decided_at REAL, controls TEXT)")
        db.commit()
        db.close()
        store = pw.Store(path)
        self.addCleanup(store.close)
        cols = {r["name"] for r in store.db.execute("PRAGMA table_info(pairs)")}
        self.assertTrue({"peak", "last_liq", "watch_due", "watch_until", "kept_at", "backfilled"} <= cols)


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
