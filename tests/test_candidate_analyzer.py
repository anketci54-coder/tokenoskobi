"""Offline tests for the candidate analyzer (fake panel, temp SQLite)."""
import tempfile
import unittest
from pathlib import Path

from services.market import candidate_analyzer as ca
from services.market import pair_watcher as pw
from tests.test_pair_watcher import TOK, TOK2, WBNB


def answer(decision="BLOCK", risk=100, blockers=("X",), packet="pkt1"):
    return {"decision": {"decision": decision, "risk_score": risk, "data_quality": "VERI_YETERSIZ",
                         "blockers": list(blockers), "warnings": []},
            "history": {"packet_id": packet}}


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = pw.Store(Path(tmp.name) / "p.sqlite")
        self.addCleanup(self.store.close)
        ca.ensure_table(self.store)

    def keep(self, pair, token, kept_at=1000.0, liq=10.0):
        target, quote, _ = pw.classify_new_pair(WBNB, token)
        self.store.add({"now": 0.0, "items": [{
            "pair": pair, "target": target, "quote": quote, "token0": WBNB, "token1": token,
            "block": 1, "status": "NEW", "reason": None, "detail": None, "due_at": 0.0}]}, 1)
        self.store.decide(pair, "KEPT", "LIQUIDITY_OK", f"{liq} WBNB", kept_at, None, liq)

    NOW = 1000.0 + 3 * 3600


class PickTests(Base):
    def test_only_old_enough_candidates_are_picked_newest_first(self):
        self.keep("0x" + "1" * 40, TOK, kept_at=1000.0)
        self.keep("0x" + "2" * 40, TOK2, kept_at=2000.0)
        self.keep("0x" + "3" * 40, "0x" + "f3" * 20, kept_at=self.NOW - 60)  # too young
        self.assertEqual(ca.pick(self.store, self.NOW, 60, 0.9), TOK2)

    def test_nothing_to_do_is_idle(self):
        calls = []
        self.assertEqual(ca.step(self.store, lambda t: calls.append(t), self.NOW), "IDLE")
        self.assertEqual(calls, [])

    def test_shrunk_liquidity_is_not_a_candidate(self):
        pair = "0x" + "1" * 40
        self.keep(pair, TOK)
        self.store.watch_update(pair, peak=10.0, liq=5.0, due=None)
        self.assertIsNone(ca.pick(self.store, self.NOW, 60, 0.9))


class AnalyzeTests(Base):
    def test_result_is_recorded_once(self):
        self.keep("0x" + "1" * 40, TOK)
        calls = []
        def post(token):
            calls.append(token)
            return answer()
        self.assertEqual(ca.step(self.store, post, self.NOW), "OK")
        self.assertEqual(ca.step(self.store, post, self.NOW), "IDLE")  # never re-analysed
        self.assertEqual(calls, [TOK])
        row = self.store.db.execute("SELECT * FROM analyses WHERE token=?", (TOK,)).fetchone()
        self.assertEqual((row["decision"], row["risk"], row["packet_id"]), ("BLOCK", 100, "pkt1"))
        text = ca.report(self.store)
        self.assertIn("BLOCK", text)
        self.assertIn(TOK, text)
    def test_report_counts_warnings_and_why_layers_did_not_measure(self):
        for i, (pair, token) in enumerate((("0x" + "1" * 40, TOK), ("0x" + "2" * 40, TOK2))):
            self.keep(pair, token)
        def post(token):
            reply = answer("REVIEW", 50, blockers=())
            reply["decision"]["warnings"] = ["SELL_BEHAVIOR_UNVERIFIED", "LP_NOT_BURNED"]
            reply["swap_behavior"] = {"status": "UNKNOWN", "reason": "POOL_NOT_V2_PAIR"}
            reply["lp_status"] = {"status": "UNKNOWN", "reason": "POOL_NOT_V2_PAIR"}
            return reply
        ca.step(self.store, post, self.NOW)
        ca.step(self.store, post, self.NOW)
        text = ca.report(self.store)
        self.assertIn("SELL_BEHAVIOR_UNVERIFIED: 2 (%100)", text)
        self.assertIn("UNKNOWN:POOL_NOT_V2_PAIR: 2", text)

    def test_old_table_is_migrated_and_old_rows_are_labelled(self):
        self.store.db.executescript("DROP TABLE analyses; CREATE TABLE analyses(token TEXT PRIMARY KEY,"
                                    " analyzed_at REAL, status TEXT, decision TEXT, risk INTEGER, quality TEXT,"
                                    " packet_id TEXT, blockers TEXT, warnings TEXT, error TEXT,"
                                    " attempts INTEGER DEFAULT 0, next_try REAL);")
        self.store.db.execute("INSERT INTO analyses(token, status, decision, warnings) VALUES('0xa','OK','REVIEW','[]')")
        self.store.db.commit()
        ca.ensure_table(self.store)
        self.assertIn("eski kayıt (bilinmiyor): 1", ca.report(self.store))

    def test_report_lists_warnings(self):
        self.keep("0x" + "1" * 40, TOK)
        reply = answer("REVIEW", 30, blockers=())
        reply["decision"]["warnings"] = ["NEWS_DB_MISSING", "OWNER_UNVERIFIED"]
        ca.step(self.store, lambda t: reply, self.NOW)
        self.assertIn("uyarılar: NEWS_DB_MISSING, OWNER_UNVERIFIED", ca.report(self.store))

    def test_errors_back_off_and_stop_after_max_attempts(self):
        self.keep("0x" + "1" * 40, TOK)
        def post(token):
            raise RuntimeError("HTTP_500")
        now = self.NOW
        for attempt in range(ca.MAX_ATTEMPTS):
            self.assertEqual(ca.step(self.store, post, now), "ERROR")
            self.assertEqual(ca.step(self.store, post, now), "IDLE")  # backing off
            now += ca.RETRY_BASE_SEC * (attempt + 1) + 1
        self.assertEqual(ca.step(self.store, post, now + 10**6), "IDLE")  # gave up
        row = self.store.db.execute("SELECT * FROM analyses").fetchone()
        self.assertEqual((row["status"], row["attempts"]), ("ERROR", ca.MAX_ATTEMPTS))

    def test_panel_down_records_nothing_and_does_not_burn_attempts(self):
        self.keep("0x" + "1" * 40, TOK)
        def down(token):
            raise ca.PanelUnreachable("URLError")
        self.assertEqual(ca.step(self.store, down, self.NOW), "PANEL_DOWN")
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM analyses").fetchone()[0], 0)
        self.assertEqual(ca.step(self.store, lambda t: answer(), self.NOW + 5), "OK")

    def test_unmeasured_swap_layer_is_retried_later_but_only_a_bounded_number_of_times(self):
        self.keep("0x" + "1" * 40, TOK)
        def post(token):
            reply = answer("REVIEW", 50, blockers=())
            reply["swap_behavior"] = {"status": "UNKNOWN", "reason": "LOGS_UNAVAILABLE"}
            return reply
        now = self.NOW
        runs = 0
        for _ in range(6):
            if ca.step(self.store, post, now) == "OK":
                runs += 1
            self.assertEqual(ca.step(self.store, post, now), "IDLE")  # not again right away
            now += ca.REMEASURE_AFTER_SEC + 1
        self.assertEqual(runs, ca.MAX_ANALYSES_PER_TOKEN)

    def test_measured_swap_layer_is_not_repeated_and_old_rows_are_retried(self):
        self.keep("0x" + "1" * 40, TOK)
        self.keep("0x" + "2" * 40, TOK2)
        def post(token):
            reply = answer("REVIEW", 50, blockers=())
            reply["swap_behavior"] = {"status": "OK", "sell_ability": "SELLS_OBSERVED"}
            return reply
        self.assertEqual(ca.step(self.store, post, self.NOW), "OK")
        self.assertEqual(ca.step(self.store, post, self.NOW), "OK")
        later = self.NOW + 10 * ca.REMEASURE_AFTER_SEC
        self.assertEqual(ca.step(self.store, post, later), "IDLE")
        self.store.db.execute("UPDATE analyses SET sell_state=NULL WHERE token=?", (TOK,))  # an old row
        self.store.db.commit()
        self.assertEqual(ca.step(self.store, post, later), "OK")
        self.assertEqual(ca.step(self.store, post, later), "IDLE")

    def test_malformed_response_is_an_error_not_a_verdict(self):
        self.keep("0x" + "1" * 40, TOK)
        self.assertEqual(ca.step(self.store, lambda t: {"decision": {}}, self.NOW), "ERROR")
        row = self.store.db.execute("SELECT * FROM analyses").fetchone()
        self.assertIsNone(row["decision"])
        self.assertIn("RESPONSE_MISSING_DECISION", row["error"])


if __name__ == "__main__":
    unittest.main()
