"""Offline tests for advisory token-level control hints (owner, proxy, selectors)."""
import hashlib
import unittest
from unittest.mock import patch

from services.market import token_controls as tc
from services.market import tokenoskobi_product_slice_02_server as market
from tests.test_market_data_validation import TOKEN, decision_inputs

ZERO = "0x" + "0" * 64
OWNER = "0x" + "0" * 24 + "ab" * 20
OWNER_ADDR = "0x" + "ab" * 20


class KeccakTests(unittest.TestCase):
    def test_known_keccak256_vectors(self):
        self.assertEqual(tc.keccak256(b"").hex(),
                         "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
        self.assertEqual(tc.keccak256(b"abc").hex(),
                         "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45")

    def test_permutation_and_multiblock_padding_match_nist_sha3(self):
        # Same sponge with NIST's suffix must equal hashlib across block boundaries.
        for size in (0, 1, 135, 136, 137, 271, 272, 273, 1000):
            data = bytes((i * 7 + 3) % 256 for i in range(size))
            with self.subTest(size=size):
                self.assertEqual(tc._sponge(data, 0x06), hashlib.sha3_256(data).digest())

    def test_function_selectors(self):
        for signature, expected in (
            ("transfer(address,uint256)", "a9059cbb"), ("balanceOf(address)", "70a08231"),
            ("owner()", "8da5cb5b"), ("getOwner()", "893d20e8"),
            ("renounceOwnership()", "715018a6"), ("mint(address,uint256)", "40c10f19"),
            ("pause()", "8456cb59"),
        ):
            with self.subTest(signature=signature):
                self.assertEqual(tc.selector(signature), expected)

    def test_eip1967_slot_constant(self):
        self.assertEqual(
            tc.EIP1967_IMPLEMENTATION_SLOT,
            "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc",
        )


class SelectorScanTests(unittest.TestCase):
    def test_push4_selector_is_found(self):
        code = "0x" + "6080" + "63" + "40c10f19" + "5b"
        self.assertEqual(tc.scan_selector_hints(code), ["MINT_SELECTOR_PRESENT"])

    def test_push_data_is_not_misread_as_push4(self):
        # PUSH5 whose data contains 0x63 followed by the mint selector: not a PUSH4.
        code = "0x" + "64" + "63" + "40c10f19" + "00"
        self.assertEqual(tc.scan_selector_hints(code), [])

    def test_several_hints_and_clean_code(self):
        code = "0x" + "63" + "8456cb59" + "63" + tc.selector("blacklist(address)")
        self.assertEqual(tc.scan_selector_hints(code),
                         ["BLACKLIST_SELECTOR_PRESENT", "PAUSE_SELECTOR_PRESENT"])
        self.assertEqual(tc.scan_selector_hints("0x6080604052"), [])

    def test_unscannable_code_is_unavailable_not_clean(self):
        for value in (None, "", "0x", "0xzz", 5):
            with self.subTest(value=value):
                self.assertIsNone(tc.scan_selector_hints(value))


class OwnerAndProxyTests(unittest.TestCase):
    def test_owner_states_are_distinct(self):
        self.assertEqual(tc.classify_owner(ZERO, None)["status"], "OWNER_RENOUNCED")
        dead = "0x" + "0" * 60 + "dead"
        self.assertEqual(tc.classify_owner(dead, None)["status"], "OWNER_RENOUNCED")
        self.assertEqual(tc.classify_owner(OWNER, False)["status"], "OWNER_ACTIVE_EOA")
        self.assertEqual(tc.classify_owner(OWNER, True)["status"], "OWNER_ACTIVE_CONTRACT")
        self.assertEqual(tc.classify_owner(OWNER, None)["status"], "OWNER_ACTIVE_UNVERIFIED_TYPE")
        for raw in (None, "0x", "", "0x12", "0x" + "z" * 64, "0x" + "f" * 64, 7):
            with self.subTest(raw=raw):
                result = tc.classify_owner(raw, None)
                self.assertEqual(result["status"], "OWNER_UNKNOWN")
                self.assertIsNone(result["address"])

    def test_proxy_states(self):
        self.assertEqual(tc.classify_proxy(ZERO)["status"], "EIP1967_PROXY_NOT_DETECTED")
        found = tc.classify_proxy(OWNER)
        self.assertEqual(found["status"], "EIP1967_PROXY_DETECTED")
        self.assertEqual(found["implementation"], OWNER_ADDR)
        for raw in (None, "0x", "0x12", 3):
            self.assertEqual(tc.classify_proxy(raw)["status"], "PROXY_CHECK_UNKNOWN")


class CollectTests(unittest.TestCase):
    def test_collect_with_active_eoa_owner_proxy_and_mint(self):
        code = "0x63" + "40c10f19"
        result = tc.collect_controls(
            code, OWNER, lambda data: None, lambda addr: "0x", lambda slot: OWNER)
        self.assertEqual(result["owner"]["status"], "OWNER_ACTIVE_EOA")
        self.assertEqual(result["owner"]["source"], "owner()")
        self.assertEqual(result["proxy"]["status"], "EIP1967_PROXY_DETECTED")
        self.assertEqual(result["selector_hints"], ["MINT_SELECTOR_PRESENT"])
        self.assertEqual(result["selector_scan"], "OK")
        self.assertTrue(result["limits"])

    def test_getowner_fallback_when_owner_is_unanswered(self):
        calls = []
        def call(data):
            calls.append(data)
            return OWNER
        result = tc.collect_controls("0x6080", None, call, lambda addr: "0x6080", lambda s: ZERO)
        self.assertEqual(calls, [tc.OWNER_SELECTORS["getOwner()"]])
        self.assertEqual(result["owner"]["status"], "OWNER_ACTIVE_CONTRACT")
        self.assertEqual(result["owner"]["source"], "getOwner()")

    def test_every_failure_becomes_unknown_never_safe(self):
        def boom(*_):
            raise RuntimeError("rpc down")
        result = tc.collect_controls(None, None, boom, boom, boom)
        self.assertEqual(result["owner"]["status"], "OWNER_UNKNOWN")
        self.assertEqual(result["proxy"]["status"], "PROXY_CHECK_UNKNOWN")
        self.assertEqual(result["selector_scan"], "UNAVAILABLE")
        self.assertEqual(result["selector_hints"], [])

    def test_owner_code_lookup_failure_keeps_owner_type_unverified(self):
        def boom(*_):
            raise RuntimeError("rpc down")
        result = tc.collect_controls("0x6080", OWNER, boom, boom, lambda s: ZERO)
        self.assertEqual(result["owner"]["status"], "OWNER_ACTIVE_UNVERIFIED_TYPE")


class ContractIntegrationTests(unittest.TestCase):
    def fake_rpc(self, code="0x6340c10f19", fail_storage=False):
        def fake(url, method, params):
            if method == "eth_getCode":
                return code if params[0] == TOKEN else "0x"
            if method == "eth_getStorageAt":
                if fail_storage:
                    raise RuntimeError("no storage")
                return ZERO
            if method == "eth_call":
                return OWNER if params[0]["data"] == market.SEL["owner"] else "0x"
            raise AssertionError(method)
        return fake

    def test_contract_exposes_controls_and_keeps_metadata(self):
        with patch.object(market, "rpc", self.fake_rpc()):
            state = market.contract(TOKEN, {"selected": {"url": "u"}})
        self.assertIs(state["code_exists"], True)
        self.assertEqual(state["controls"]["owner"]["status"], "OWNER_ACTIVE_EOA")
        self.assertEqual(state["controls"]["proxy"]["status"], "EIP1967_PROXY_NOT_DETECTED")
        self.assertEqual(state["metadata"]["owner"], OWNER_ADDR)

    def test_storage_failure_is_unknown_and_does_not_break_contract(self):
        with patch.object(market, "rpc", self.fake_rpc(fail_storage=True)):
            state = market.contract(TOKEN, {"selected": {"url": "u"}})
        self.assertEqual(state["controls"]["proxy"]["status"], "PROXY_CHECK_UNKNOWN")
        self.assertEqual(state["errors"], [])

    def test_no_code_means_no_controls(self):
        with patch.object(market, "rpc", self.fake_rpc(code="0x")):
            state = market.contract(TOKEN, {"selected": {"url": "u"}})
        self.assertIs(state["code_exists"], False)
        self.assertIsNone(state["controls"])

    def test_risky_controls_only_tighten_the_decision(self):
        baseline = market.decide(*decision_inputs())
        self.assertEqual(baseline["decision"], "ALLOW")
        values = decision_inputs()
        values[0] = {**values[0], "controls": {
            "owner": {"status": "OWNER_ACTIVE_EOA", "address": OWNER_ADDR},
            "proxy": {"status": "EIP1967_PROXY_DETECTED", "implementation": OWNER_ADDR},
            "selector_hints": ["MINT_SELECTOR_PRESENT"], "selector_scan": "OK", "limits": "x"}}
        risky = market.decide(*values)
        self.assertEqual(risky["decision"], "REVIEW")
        self.assertGreater(risky["risk_score"], baseline["risk_score"])


if __name__ == "__main__":
    unittest.main()
