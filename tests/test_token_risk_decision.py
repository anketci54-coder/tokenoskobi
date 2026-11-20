"""decide() with token-level evidence: rules only tighten, unknown is never safe."""
import copy
import unittest

from services.market import tokenoskobi_product_slice_02_server as market
from tests.test_market_data_validation import decision_inputs

RANK = {"ALLOW": 0, "WAIT": 1, "REVIEW": 2, "BLOCK": 3}


def decide(mutate=None):
    values = copy.deepcopy(decision_inputs())
    if mutate:
        mutate(values)
    return market.decide(*values)


def controls(**parts):
    def apply(values):
        values[0]["controls"] = {**values[0]["controls"], **parts}
    return apply


def swap(**parts):
    def apply(values):
        values[5] = {**values[5], **parts}
    return apply


def tax(status, median=None):
    return {"status": status, "median_pct": median, "max_pct": median, "samples": 5}


class HealthyAndBlockingTests(unittest.TestCase):
    def test_complete_healthy_evidence_allows_with_token_evidence(self):
        result = decide()
        self.assertEqual((result["decision"], result["data_quality"]), ("ALLOW", "SUFFICIENT"))
        for item in ("OWNER_RENOUNCED", "EIP1967_PROXY_NOT_DETECTED", "SELLS_OBSERVED",
                     "BUY_TAX_MEASURED_LOW", "SELL_TAX_MEASURED_LOW"):
            self.assertIn(item, result["evidence"])

    def test_many_buys_without_sells_is_a_suspected_honeypot_block(self):
        result = decide(swap(sell_ability="NO_SELLS_OBSERVED"))
        self.assertEqual((result["decision"], result["risk_score"]), ("BLOCK", 100))
        self.assertIn("HONEYPOT_SUSPECTED_NO_SELLS", result["blockers"])

    def test_tax_thresholds(self):
        cases = (("buy_tax", 9.99, None, None), ("buy_tax", 10.0, "BUY_TAX_HIGH", None),
                 ("buy_tax", 30.0, None, "BUY_TAX_VERY_HIGH"),
                 ("sell_tax", 10.0, "SELL_TAX_HIGH", None),
                 ("sell_tax", 55.0, None, "SELL_TAX_VERY_HIGH"))
        for key, pct, warning, blocker in cases:
            with self.subTest(key=key, pct=pct):
                result = decide(swap(**{key: tax("ESTIMATED", pct)}))
                self.assertEqual(warning in result["warnings"], warning is not None)
                self.assertEqual(blocker in result["blockers"], blocker is not None)
                if blocker:
                    self.assertEqual(result["decision"], "BLOCK")

    def test_fee_transfer_detection_counts_as_a_measured_sell_tax(self):
        events = {"status": "DETECTED", "median_pct": 35.0, "max_pct": 40.0,
                  "detected": 4, "not_detected": 0, "inconclusive": 1}
        result = decide(swap(sell_tax=tax("UNKNOWN"), sell_fee_events=events))
        self.assertIn("SELL_TAX_VERY_HIGH", result["blockers"])

    def test_the_higher_of_two_sell_tax_measurements_wins(self):
        events = {"status": "DETECTED", "median_pct": 12.0, "detected": 3}
        result = decide(swap(sell_tax=tax("ESTIMATED", 2.0), sell_fee_events=events))
        self.assertIn("SELL_TAX_HIGH", result["warnings"])


class UnknownIsNotSafeTests(unittest.TestCase):
    def assert_not_sufficient(self, result):
        self.assertEqual(result["data_quality"], "VERI_YETERSIZ")
        self.assertNotEqual(result["decision"], "ALLOW")

    def test_missing_or_garbage_controls(self):
        for value in (None, {}, "x", 7, []):
            with self.subTest(value=value):
                result = decide(lambda v, value=value: v[0].__setitem__("controls", value))
                self.assertIn("TOKEN_CONTROLS_UNVERIFIED", result["warnings"])
                self.assert_not_sufficient(result)

    def test_missing_failed_or_small_swap_evidence(self):
        for value in (None, {}, "x", {"status": "UNKNOWN", "reason": "LOGS_UNAVAILABLE"},
                      {**decision_inputs()[5], "sell_ability": "SAMPLE_TOO_SMALL"}):
            with self.subTest(value=value):
                result = decide(lambda v, value=value: v.__setitem__(5, value))
                self.assertIn("SELL_BEHAVIOR_UNVERIFIED", result["warnings"])
                self.assert_not_sufficient(result)

    def test_unlisted_swap_argument_is_treated_as_unverified(self):
        values = decision_inputs()[:5]
        result = market.decide(*values)
        self.assertIn("SELL_BEHAVIOR_UNVERIFIED", result["warnings"])
        self.assert_not_sufficient(result)

    def test_unmeasured_taxes_are_not_zero(self):
        not_detected = {"status": "NOT_DETECTED", "median_pct": None, "detected": 0,
                        "not_detected": 5, "inconclusive": 0}
        for name, parts in {
            "sell_unknown": {"sell_tax": tax("UNKNOWN"), "sell_fee_events": not_detected},
            "buy_unknown": {"buy_tax": tax("UNKNOWN")},
            "garbage_tax": {"sell_tax": "x", "buy_tax": 5},
        }.items():
            with self.subTest(name=name):
                result = decide(swap(**parts))
                self.assert_not_sufficient(result)
        self.assertIn("SELL_TAX_UNMEASURED",
                      decide(swap(sell_tax=tax("UNKNOWN"), sell_fee_events=not_detected))["warnings"])

    def test_owner_and_proxy_states(self):
        eoa = decide(controls(owner={"status": "OWNER_ACTIVE_EOA"}))
        self.assertIn("OWNER_ACTIVE_EOA", eoa["warnings"])
        contract_owner = decide(controls(owner={"status": "OWNER_ACTIVE_CONTRACT"}))
        self.assertIn("OWNER_ACTIVE_CONTRACT", contract_owner["evidence"])
        self.assertEqual(contract_owner["decision"], "ALLOW")
        for status in ("OWNER_UNKNOWN", "OWNER_ACTIVE_UNVERIFIED_TYPE", None):
            self.assertIn("OWNER_UNVERIFIED", decide(controls(owner={"status": status}))["warnings"])
        self.assertIn("PROXY_UPGRADEABLE",
                      decide(controls(proxy={"status": "EIP1967_PROXY_DETECTED"}))["warnings"])
        for status in ("PROXY_CHECK_UNKNOWN", None):
            self.assertIn("PROXY_UNVERIFIED", decide(controls(proxy={"status": status}))["warnings"])

    def test_mint_hint_matters_only_without_a_known_safe_owner(self):
        hints = {"selector_hints": ["MINT_SELECTOR_PRESENT"]}
        safe = decide(controls(owner={"status": "OWNER_ACTIVE_CONTRACT"}, **hints))
        self.assertIn("MINT_HINT_PRESENT", safe["evidence"])
        self.assertNotIn("MINT_HINT_WITH_UNVERIFIED_OWNER", safe["warnings"])
        for status in ("OWNER_ACTIVE_EOA", "OWNER_UNKNOWN"):
            risky = decide(controls(owner={"status": status}, **hints))
            self.assertIn("MINT_HINT_WITH_UNVERIFIED_OWNER", risky["warnings"])


class OnlyTightenTests(unittest.TestCase):
    def test_no_worse_evidence_ever_loosens_decision_or_lowers_score(self):
        baseline = decide()
        worse = [
            controls(owner={"status": "OWNER_ACTIVE_EOA"}),
            controls(owner={"status": "OWNER_UNKNOWN"}),
            controls(proxy={"status": "EIP1967_PROXY_DETECTED"}),
            controls(proxy={"status": "PROXY_CHECK_UNKNOWN"}),
            controls(selector_hints=["MINT_SELECTOR_PRESENT"], owner={"status": "OWNER_ACTIVE_EOA"}),
            swap(sell_ability="NO_SELLS_OBSERVED"),
            swap(sell_ability="SAMPLE_TOO_SMALL"),
            swap(buy_tax=tax("ESTIMATED", 12.0)),
            swap(sell_tax=tax("ESTIMATED", 40.0)),
            swap(sell_tax=tax("UNKNOWN")),
            lambda v: v.__setitem__(6, {"status": "OK", "burned_pct": 5.0}),
            lambda v: v.__setitem__(6, None),
            lambda v: v.__setitem__(5, None),
            lambda v: v[0].pop("controls"),
        ]
        for index, mutate in enumerate(worse):
            with self.subTest(index=index):
                result = decide(mutate)
                self.assertGreaterEqual(RANK[result["decision"]], RANK[baseline["decision"]])
                self.assertGreaterEqual(result["risk_score"], baseline["risk_score"])


class RealWorldShapeTests(unittest.TestCase):
    def test_cake_like_result_stays_in_review_without_a_honeypot_flag(self):
        # Seen live: contract owner, no EIP-1967 proxy, mint hint, sells present,
        # buy tax measured 0%, sell tax unmeasurable, news database missing.
        def mutate(values):
            values[0]["controls"] = {
                "owner": {"status": "OWNER_ACTIVE_CONTRACT"},
                "proxy": {"status": "EIP1967_PROXY_NOT_DETECTED"},
                "selector_hints": ["MINT_SELECTOR_PRESENT"], "selector_scan": "OK"}
            values[3] = {"fresh": False, "reason": "NEWS_DB_MISSING"}
            values[5] = {**values[5], "sell_tax": tax("UNKNOWN"),
                         "sell_fee_events": {"status": "UNKNOWN", "inconclusive": 10}}
        result = decide(mutate)
        self.assertEqual((result["decision"], result["data_quality"]), ("REVIEW", "VERI_YETERSIZ"))
        self.assertEqual(result["blockers"], [])
        for item in ("SELL_TAX_UNMEASURED", "NEWS_DB_MISSING"):
            self.assertIn(item, result["warnings"])
        self.assertIn("SELLS_OBSERVED", result["evidence"])


if __name__ == "__main__":
    unittest.main()
