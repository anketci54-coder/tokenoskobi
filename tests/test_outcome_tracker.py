"""Offline tests for the outcome tracker (fake reserves, temp SQLite)."""
import tempfile
import unittest
from pathlib import Path

from services.market import candidate_analyzer as ca
from services.market import outcome_tracker as ot
from services.market import pair_watcher as pw
from tests.test_candidate_analyzer import answer
from tests.test_pair_watcher import TOK, TOK2, WBNB, reserves

E18 = 10**18


class Chain:
    """Fake chain: current (quote, token) reserves per pair; quote is WBNB = token0."""
    def __init__(self, quote=10 * E18, token=1000 * E18, fail=False):
        self.quote, self.token, self.fail = quote, token, fail
        self.calls = 0

    def __call__(self, method, params):
        self.calls += 1
        if self.fail:
            raise RuntimeError("down")
        return reserves(self.quote, self.token)


class Base(unittest.TestCase):
    T0 = 100_000.0

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = pw.Store(Path(tmp.name) / "p.sqlite")
        self.addCleanup(self.store.close)
        ca.ensure_table(self.store)
        ot.ensure_tables(self.store)

    def analysed(self, token, pair, decision="ALLOW", at=None):
        target, quote, _ = pw.classify_new_pair(WBNB, token)
        self.store.add({"now": 0.0, "items": [{
            "pair": pair, "target": target, "quote": quote, "token0": WBNB, "token1": token,
            "block": 1, "status": "NEW", "reason": None, "detail": None, "due_at": 0.0}]}, 1)
        self.store.decide(pair, "KEPT", "LIQUIDITY_OK", "10.0 WBNB", 1.0, None, 10.0)
        ca.analyze_one(self.store, token, lambda t: answer(decision, 30, blockers=()), at or self.T0)

    def points(self):
        return self.store.db.execute("SELECT * FROM outcome_points ORDER BY horizon").fetchall()


class RegisterTests(Base):
    def test_fresh_analysis_gets_a_baseline_and_three_due_points(self):
        self.analysed(TOK, "0x" + "1" * 40)
        self.assertEqual(ot.register(self.store, Chain(), self.T0 + 60), 1)
        row = self.store.db.execute("SELECT * FROM outcomes").fetchone()
        self.assertEqual((row["status"], row["t0_quote"], row["t0_ratio"]), ("TRACKING", 10.0 * E18, 0.01))
        self.assertEqual([p["horizon"] for p in self.points()], [60, 360, 1440])
        self.assertEqual(self.points()[0]["due_at"], self.T0 + 60 + 3600)
        self.assertEqual(ot.register(self.store, Chain(), self.T0 + 120), 0)  # never twice

    def test_late_unknown_pair_and_empty_pool_are_marked_not_guessed(self):
        self.analysed(TOK, "0x" + "1" * 40)
        ot.register(self.store, Chain(), self.T0 + ot.FRESH_SEC + 1)
        self.assertEqual(self.store.db.execute("SELECT status FROM outcomes").fetchone()[0], "SKIPPED_LATE")
        self.assertEqual(self.points(), [])
        self.store.db.execute("DELETE FROM outcomes")
        self.store.db.execute("DELETE FROM pairs")
        self.store.db.commit()
        ot.register(self.store, Chain(), self.T0 + 60)
        self.assertEqual(self.store.db.execute("SELECT status FROM outcomes").fetchone()[0], "NO_PAIR")
        self.store.db.execute("DELETE FROM outcomes")
        self.store.db.commit()
        self.analysed(TOK2, "0x" + "2" * 40)
        ot.register(self.store, Chain(quote=0), self.T0 + 60)
        self.assertIn("NO_BASELINE", [r["status"] for r in self.store.db.execute("SELECT status FROM outcomes")])

    def test_unreadable_baseline_is_retried_until_the_window_closes(self):
        self.analysed(TOK, "0x" + "1" * 40)
        self.assertEqual(ot.register(self.store, Chain(fail=True), self.T0 + 60), 0)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0], 0)
        self.assertEqual(ot.register(self.store, Chain(), self.T0 + 120), 1)


class MeasureTests(Base):
    def track(self, decision="ALLOW", token=TOK, pair="0x" + "1" * 40):
        self.analysed(token, pair, decision)
        ot.register(self.store, Chain(), self.T0 + 60)

    def test_price_and_liquidity_change_are_computed_from_reserves(self):
        self.track()
        due = self.T0 + 60 + 3600
        self.assertEqual(ot.measure(self.store, Chain(quote=5 * E18, token=2000 * E18), due)["MEASURED"], 1)
        point = self.points()[0]
        self.assertAlmostEqual(point["liq_change_pct"], -50.0)
        self.assertAlmostEqual(point["price_change_pct"], -75.0)  # ratio 0.0025 vs 0.01
        self.assertEqual(self.points()[1]["status"], "PENDING")

    def test_drained_pool_is_a_total_loss_not_an_error(self):
        self.track()
        ot.measure(self.store, Chain(quote=0, token=1000 * E18), self.T0 + 60 + 3600)
        self.assertEqual((self.points()[0]["status"], self.points()[0]["price_change_pct"]), ("MEASURED", -100.0))

    def test_errors_retry_then_fail_and_are_never_filled_in(self):
        self.track()
        now = self.T0 + 60 + 3600
        for _ in range(ot.MAX_ERRORS):
            ot.measure(self.store, Chain(fail=True), now)
            now += ot.RETRY_SEC + 1
        point = self.points()[0]
        self.assertEqual(point["status"], "FAILED")
        self.assertIsNone(point["price_change_pct"])

    def test_not_due_points_are_not_read(self):
        self.track()
        chain = Chain()
        ot.measure(self.store, chain, self.T0 + 120)
        self.assertEqual(chain.calls, 0)


class ReportTests(Base):
    def test_groups_by_decision_and_flags_small_samples(self):
        self.track_all = []
        for i, (decision, quote, token) in enumerate((("ALLOW", 10, 1000), ("REVIEW", 1, 1000), ("REVIEW", 10, 1000))):
            tok = "0x" + format(0xA0 + i, "02x") * 20
            self.analysed(tok, "0x" + format(i + 1, "x") * 40, decision)
            ot.register(self.store, Chain(), self.T0 + 60)
            ot.measure(self.store, Chain(quote=quote * E18, token=token * E18), self.T0 + 60 + 3600)
        text = ot.report(self.store)
        allow = text.split("ALLOW:")[1].split("REVIEW:")[0]
        review = text.split("REVIEW:")[1].split("WAIT:")[0]
        self.assertIn("1 örnek · likidite çekilen %0", allow)
        self.assertIn("2 örnek · likidite çekilen %50", review)
        self.assertIn("örnek az", review)
        self.assertIn("WAIT:\n  henüz ölçüm yok", text)

    def test_late_measurements_are_left_out(self):
        self.analysed(TOK, "0x" + "1" * 40)
        ot.register(self.store, Chain(), self.T0 + 60)
        ot.measure(self.store, Chain(quote=1 * E18), self.T0 + 60 + 3600 + ot.MAX_DELAY_SEC + 10)
        self.assertIn("ALLOW:\n  henüz ölçüm yok", ot.report(self.store))

    def test_empty_report(self):
        self.assertIn("kayıtlar: henüz yok", ot.report(self.store))


if __name__ == "__main__":
    unittest.main()
