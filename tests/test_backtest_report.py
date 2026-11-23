import sqlite3
import unittest

from services.market import backtest_report as bt

H = 3600.0


def db_with(rows):
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE analyses(token TEXT, analyzed_at REAL, status TEXT, decision TEXT, warnings TEXT)")
    db.execute("CREATE TABLE pairs(target TEXT, status TEXT, decided_at REAL, watch_until REAL)")
    for i, (decision, analyzed_at, status, decided_at, watch_until, *w) in enumerate(rows):
        warn = w[0] if w else "[]"
        db.execute("INSERT INTO analyses VALUES(?,?,?,?,?)", (f"t{i}", analyzed_at, "OK", decision, warn))
        db.execute("INSERT INTO pairs VALUES(?,?,?,?)", (f"t{i}", status, decided_at, watch_until))
    return db


class BacktestTests(unittest.TestCase):
    def row(self, status, decided_at, watch_until, analyzed_at=0.0):
        db = db_with([("ALLOW", analyzed_at, status, decided_at, watch_until)])
        db.row_factory = sqlite3.Row
        return db.execute("SELECT a.analyzed_at, p.status, p.decided_at, p.watch_until FROM analyses a "
                          "JOIN pairs p ON p.target=a.token").fetchone()

    def test_pull_inside_window_is_pulled(self):
        r = self.row("PULLED", 0.5 * H, 24 * H)
        self.assertTrue(bt.outcome_at(r, 60, now=2 * H))

    def test_pull_outside_watch_window_is_unknown_not_counted(self):
        # izleme ufku kapsamıyorsa çekilmiş olsa bile sayılmaz: yoksa yalnızca çekilenler görünür (yanlılık)
        r = self.row("PULLED", 0.5 * H, 0.9 * H)
        self.assertIsNone(bt.outcome_at(r, 60, now=30 * H))

    def test_pull_after_window_is_not_pulled_for_that_window(self):
        r = self.row("PULLED", 3 * H, 24 * H)
        self.assertFalse(bt.outcome_at(r, 60, now=5 * H))

    def test_window_not_over_yet_is_unknown(self):
        self.assertIsNone(bt.outcome_at(self.row("KEPT", None, 24 * H), 360, now=2 * H))

    def test_watch_ended_before_window_is_unknown_not_survived(self):
        self.assertIsNone(bt.outcome_at(self.row("KEPT", None, 2 * H), 360, now=30 * H))
        self.assertIsNone(bt.outcome_at(self.row("PULLED", 1 * H, 2 * H), 360, now=30 * H))

    def test_survived_full_window(self):
        self.assertFalse(bt.outcome_at(self.row("KEPT", None, 24 * H), 360, now=30 * H))

    def test_report_groups_and_flags_small_sample(self):
        db = db_with([("ALLOW", 0.0, "KEPT", None, 24 * H), ("REVIEW", 0.0, "PULLED", 0.2 * H, 24 * H),
                      ("REVIEW", 0.0, "KEPT", None, 24 * H)])
        text = bt.report(db, now=30 * H)
        self.assertIn("eşleşen analiz: 3", text)
        review = text.split("REVIEW:")[1].split("WAIT:")[0]
        self.assertIn("2 örnek · likidite çekilen %50", review)
        self.assertIn("örnek az", review)
        self.assertIn("WAIT:\n  analiz yok", text)

    def test_factor_split_and_overlap_rule(self):
        pulled = [("REVIEW", 0.0, "PULLED", 0.2 * H, 24 * H, '["LP_NOT_BURNED"]')] * 12
        kept = [("REVIEW", 0.0, "KEPT", None, 24 * H, "[]")] * 12
        text = bt.report(db_with(pulled + kept), now=30 * H)
        self.assertIn("LP_NOT_BURNED: var %100 (12) ↔ yok %0 (12) · uyarı VARKEN daha çok çekilmiş", text)
        mixed = [("REVIEW", 0.0, "PULLED" if i % 2 else "KEPT", 0.2 * H if i % 2 else None, 24 * H,
                  '["X"]' if i < 12 else "[]") for i in range(24)]
        self.assertIn("fark gösterilemedi", bt.report(db_with(mixed), now=30 * H))

    def test_small_groups_are_not_shown(self):
        rows = [("REVIEW", 0.0, "KEPT", None, 24 * H, '["Z"]')] * 3 + [("REVIEW", 0.0, "KEPT", None, 24 * H, "[]")] * 20
        self.assertIn("en az 10 örneği olan uyarı yok", bt.report(db_with(rows), now=30 * H))

    def test_missing_table_is_reported_not_crashed(self):
        self.assertIn("bulunamadı", bt.report(sqlite3.connect(":memory:")))


if __name__ == "__main__":
    unittest.main()
