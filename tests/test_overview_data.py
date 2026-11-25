import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from services.market import candidate_analyzer as ca
from services.market import outcome_tracker as ot
from services.market import overview_data as ov
from services.market import pair_watcher as pw
from tests.test_pair_watcher import TOK, WBNB

NOW = 1_000_000.0


class OverviewTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.store = pw.Store(self.dir / "pairs.sqlite")
        ca.ensure_table(self.store)
        ot.ensure_tables(self.store)
        self.addCleanup(self.store.close)

    def keep(self, pair="0x" + "9" * 40, token=TOK, kept_at=NOW - 3 * 3600):
        target, quote, _ = pw.classify_new_pair(WBNB, token)
        self.store.add({"now": kept_at, "items": [{
            "pair": pair, "target": target, "quote": quote, "token0": WBNB, "token1": token,
            "block": 1, "status": "NEW", "reason": None, "detail": None, "due_at": 0.0}]}, 1)
        self.store.decide(pair, "KEPT", "LIQUIDITY_OK", "10.0 WBNB", kept_at, None, 10.0)

    def analysis(self, decision="REVIEW", at=NOW - 600, warnings=("LP_NOT_BURNED",), token=TOK):
        self.store.db.execute(
            "INSERT INTO analyses(token, analyzed_at, status, decision, risk, warnings, attempts) VALUES(?,?,?,?,?,?,1)",
            (token, at, "OK", decision, 40, json.dumps(list(warnings))))
        self.store.db.commit()

    def test_missing_state_dir_is_unavailable_not_an_error(self):
        out = ov.snapshot(self.dir / "yok", now=NOW)
        self.assertEqual(out["available"], False)

    def test_counts_activity_and_recent(self):
        self.keep()
        self.analysis("REVIEW", at=NOW - 600)
        out = ov.snapshot(self.dir, None, now=NOW)
        self.assertTrue(out["available"])
        self.assertEqual(out["decisions"], {"ALLOW": 0, "REVIEW": 1, "WAIT": 0, "BLOCK": 0})
        states = {a["key"]: a["state"] for a in out["activity"]}
        self.assertEqual(states["analyzer"], "taze")
        self.assertEqual(states["watcher"], "eski")      # çift 3 saat önce görüldü
        self.assertEqual(states["series"], "yok")        # hiç kayıt yok
        self.assertEqual(states["news"], "yok")          # haber veritabanı verilmedi
        self.assertEqual(out["recent"][0]["warnings"], ["LP_NOT_BURNED"])

    def test_survival_and_small_samples_are_flagged(self):
        self.keep()
        out = ov.snapshot(self.dir, None, now=NOW)
        horizon60 = next(r for r in out["survival"] if r["horizon"] == 60)
        self.assertEqual((horizon60["n"], horizon60["events"], horizon60["enough"]), (1, 0, False))

    def test_empty_outcomes_have_no_measurements(self):
        out = ov.snapshot(self.dir, None, now=NOW)
        self.assertTrue(all(r["pulled"]["n"] == 0 for r in out["outcomes"]))

    def test_bad_warnings_json_does_not_break_the_page(self):
        self.store.db.execute(
            "INSERT INTO analyses(token, analyzed_at, status, decision, risk, warnings, attempts) VALUES(?,?,?,?,?,?,1)",
            (TOK, NOW - 5, "OK", "BLOCK", 100, "{bozuk", ))
        self.store.db.commit()
        self.assertEqual(ov.snapshot(self.dir, None, now=NOW)["recent"][0]["warnings"], [])

    def test_read_only_never_writes(self):
        before = (self.dir / "pairs.sqlite").stat().st_mtime_ns
        ov.snapshot(self.dir, None, now=NOW)
        db = sqlite3.connect(self.dir / "pairs.sqlite")
        self.assertEqual(db.execute("SELECT COUNT(*) FROM analyses").fetchone()[0], 0)
        db.close()
        self.assertEqual((self.dir / "pairs.sqlite").stat().st_mtime_ns, before)


if __name__ == "__main__":
    unittest.main()
