"""LP burn measurement: pure logic on a fake eth_call, plus how decide() uses it."""
import copy
import unittest

from services.market import lp_status as lp
from services.market import tokenoskobi_product_slice_02_server as market
from tests.test_market_data_validation import POOL, decision_inputs, healthy_lp_state


def word(value):
    return "0x" + format(value, "064x")


def fake(total=1_000_000, zero=1000, dead=0, v2=True, fail=None):
    def call(to, data):
        if fail and data.startswith(fail):
            raise RuntimeError("down")
        if data == lp.RESERVES_CALL:
            return "0x" + format(1, "064x") * 3 if v2 else "0x"
        if data == lp.TOTAL_SUPPLY_CALL:
            return word(total)
        if data.startswith(lp.BALANCE_OF_SELECTOR):
            holder = data[-40:]
            return word(dead if holder == lp.DEAD_ADDRESS[2:] else zero if holder == "0" * 40 else 7)
        raise AssertionError(data)
    return call


class CollectTests(unittest.TestCase):
    def test_burn_share_adds_zero_and_dead(self):
        result = lp.collect_lp(POOL, fake(total=1_000_000, zero=1000, dead=949_000))
        self.assertEqual((result["status"], result["burned_pct"]), ("OK", 95.0))
        self.assertEqual((result["zero_pct"], result["dead_pct"]), (0.1, 94.9))
        self.assertEqual(result["total_supply"], "1000000")

    def test_nothing_burned_is_ok_but_low(self):
        result = lp.collect_lp(POOL, fake(total=10**18, zero=1000, dead=0))
        self.assertEqual(result["status"], "OK")
        self.assertLess(result["burned_pct"], 0.001)

    def test_unreadable_is_unknown_never_burned(self):
        cases = {"not v2": fake(v2=False), "supply fails": fake(fail=lp.TOTAL_SUPPLY_CALL),
                 "balance fails": fake(fail=lp.BALANCE_OF_SELECTOR), "empty supply": fake(total=0),
                 "inconsistent": fake(total=10, zero=8, dead=8)}
        for name, call in cases.items():
            with self.subTest(name=name):
                result = lp.collect_lp(POOL, call)
                self.assertEqual(result["status"], "UNKNOWN")
                self.assertIsNone(result["burned_pct"])

    def test_garbage_words_are_unknown(self):
        def call(to, data):
            return "0x" + format(1, "064x") * 3 if data == lp.RESERVES_CALL else "0xzz"
        self.assertEqual(lp.collect_lp(POOL, call)["status"], "UNKNOWN")


class DecideTests(unittest.TestCase):
    def decide(self, lp_state="default"):
        values = copy.deepcopy(decision_inputs())
        if lp_state != "default":
            values[6] = lp_state
        return market.decide(*values)

    def test_burned_lp_is_evidence_and_allows(self):
        result = self.decide(healthy_lp_state(95.0))
        self.assertEqual((result["decision"], result["data_quality"]), ("ALLOW", "SUFFICIENT"))
        self.assertIn("LP_BURNED", result["evidence"])

    def test_threshold_is_inclusive_at_90(self):
        self.assertIn("LP_BURNED", self.decide(healthy_lp_state(90.0))["evidence"])
        self.assertIn("LP_NOT_BURNED", self.decide(healthy_lp_state(89.99))["warnings"])

    def test_not_burned_tightens_and_blocks_allow(self):
        base = self.decide()
        result = self.decide(healthy_lp_state(0.1))
        self.assertIn("LP_NOT_BURNED", result["warnings"])
        self.assertEqual(result["data_quality"], "VERI_YETERSIZ")
        self.assertNotEqual(result["decision"], "ALLOW")
        self.assertGreater(result["risk_score"], base["risk_score"])

    def test_missing_or_garbage_lp_is_unverified_never_safe(self):
        for value in (None, {}, "x", 5, [], {"status": "UNKNOWN", "burned_pct": None},
                      {"status": "OK", "burned_pct": "100"}, {"status": "OK"},
                      {"status": "UNKNOWN", "burned_pct": 100}):
            with self.subTest(value=value):
                result = self.decide(value)
                self.assertIn("LP_STATUS_UNVERIFIED", result["warnings"])
                self.assertNotEqual(result["decision"], "ALLOW")

    def test_lp_never_hides_a_blocker(self):
        values = copy.deepcopy(decision_inputs())
        values[5] = {**values[5], "sell_ability": "NO_SELLS_OBSERVED"}
        self.assertEqual(market.decide(*values)["decision"], "BLOCK")

    def test_omitted_lp_argument_is_unverified(self):
        result = market.decide(*decision_inputs()[:6])
        self.assertIn("LP_STATUS_UNVERIFIED", result["warnings"])
        self.assertNotEqual(result["decision"], "ALLOW")


if __name__ == "__main__":
    unittest.main()
