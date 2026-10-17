"""Policy regressions: provider claims cannot substitute for BSC provenance."""
import unittest
from copy import deepcopy
from unittest.mock import patch

from services.market import tokenoskobi_product_slice_02_server as market
from services.market import dex_policy as policy
from engineering.tests.pancakeswap_fixture import BscPoolFixture, FACTORIES, ROUTERS, word, verified_pool
from tests.test_market_data_validation import TOKEN, QUOTE, POOL, decision_inputs

USDT = "0x55d398326f99059ff775485246999027b3197955"


class EligibilityRegressionTests(unittest.TestCase):
    def test_oriented_liquid_pool_without_chain_provenance_cannot_allow(self):
        values = decision_inputs()
        values[1]["selected_pool"].pop("provenance", None)
        result = market.decide(*values)
        self.assertNotEqual(result["decision"], "ALLOW")
        self.assertEqual(result["data_quality"], "VERI_YETERSIZ")
        self.assertIn("POOL_PROVENANCE_UNVERIFIED", result["blockers"])

    def test_verified_stable_target_is_excluded_in_either_orientation(self):
        for side in ("base", "quote"):
            values = decision_inputs()
            values[1]["target_token_address"] = USDT
            values[1]["selected_pool"].update(target_token_address=USDT, target_side=side)
            for row in values[2].values():
                row["target_token_address"] = USDT
            with self.subTest(side=side):
                result = market.decide(*values)
                self.assertEqual(result["decision"], "BLOCK")
                self.assertIn("STABLECOIN_TARGET_EXCLUDED", result["blockers"])

    def test_unverified_pool_is_never_selected_by_liquidity(self):
        item = {
            "attributes": {"address": "0x" + "c" * 40, "reserve_in_usd": "999999999",
                           "base_token_price_usd": "100"},
            "relationships": {"base_token": {"data": {"id": "bsc_" + TOKEN}},
                              "quote_token": {"data": {"id": "bsc_" + USDT}},
                              "dex": {"data": {"id": "unverified-provider-claim"}}},
        }
        def provider(url, body=None):
            if body is not None:
                raise RuntimeError("RPC unavailable")
            return {"data": [item]} if "/pools?" in url else {"data": {"attributes": {}}}
        with patch.object(market, "request", side_effect=provider):
            result = market.market(TOKEN)
        self.assertIsNone(result["selected_pool"])

    def test_stable_quotes_and_a_cex_listed_target_remain_eligible(self):
        # CAKE identity is in the official PancakeSwap list. No CEX data is read.
        cake = "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82"
        for quote in policy.STABLE_TARGETS:
            values = decision_inputs()
            values[0]["metadata"] = {"symbol": "USDT", "name": "spoofed name"}
            values[1]["target_token_address"] = cake
            values[1]["selected_pool"].update(verified_pool(cake, quote, POOL))
            values[1]["token"]["cex_listed"] = True
            for row in values[2].values():
                row["target_token_address"] = cake
            with self.subTest(quote=quote):
                self.assertEqual(market.decide(*values)["decision"], "ALLOW")

    def test_all_registered_stable_targets_block_even_with_valid_pool_evidence(self):
        for stable in policy.STABLE_TARGETS:
            values = decision_inputs()
            values[1]["target_token_address"] = stable
            values[1]["selected_pool"].update(verified_pool(stable, TOKEN, POOL))
            for row in values[2].values():
                row["target_token_address"] = stable
            with self.subTest(stable=stable):
                self.assertIn("STABLECOIN_TARGET_EXCLUDED", market.decide(*values)["blockers"])

    def test_missing_nonboolean_and_misbound_provenance_cannot_allow(self):
        for key, value in (("verified", "true"), ("verified", 1), ("chain_id", 1),
                           ("pool_address", "0x" + "d" * 40), ("block_number", None),
                           ("factory", FACTORIES["v3"]), ("router", ROUTERS["v3"]),
                           ("token0", "0x" + "e" * 40), ("policy_id", "unknown")):
            values = decision_inputs()
            values[1]["selected_pool"]["provenance"][key] = value
            with self.subTest(key=key, value=value):
                self.assertNotEqual(market.decide(*values)["decision"], "ALLOW")


class PoolProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.row = verified_pool(TOKEN, QUOTE, POOL)
        self.row.pop("provenance")
        self.provider = {"selected": {"url": "fixture://bsc", "name": "fixture"}}

    def verifier(self, version="v2", rpc=None, **pool):
        self.transport = BscPoolFixture({POOL: {"version": version, "tokens": (TOKEN, QUOTE), **pool}})
        return policy.PoolVerifier(rpc or self.transport, self.provider["selected"])

    def test_v2_and_v3_require_registration_and_pin_all_reads_to_one_block(self):
        for version in ("v2", "v3"):
            verifier = self.verifier(version)
            row = deepcopy(self.row)
            row["provenance"] = verifier.verify(row)
            with self.subTest(version=version):
                self.assertTrue(policy.pool_is_verified(row, TOKEN), row)
                self.assertEqual(row["provenance"]["version"], version)
                self.assertEqual(row["provenance"]["factory"], FACTORIES[version])
                self.assertTrue(all(params[-1] == "0x100000" for method, params in self.transport.calls
                                    if method in ("eth_call", "eth_getCode")))
                self.assertNotIn("fixture://", str(row["provenance"]))

    def test_name_and_label_cannot_attest_a_foreign_factory(self):
        verifier = self.verifier(factory="0x" + "d" * 40)
        self.row.update(name="PancakeSwap V2", provider_dex_id="pancakeswap-v2")
        result = verifier.verify(self.row)
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "UNSUPPORTED_FACTORY")

    def test_forged_factory_claim_is_insufficient_without_reverse_registration(self):
        for version in ("v2", "v3"):
            with self.subTest(version=version):
                self.assertFalse(self.verifier(version, registered=False).verify(self.row)["verified"])

    def test_rpc_absence_errors_wrong_chain_and_empty_code_fail_closed(self):
        self.assertFalse(policy.PoolVerifier(None, None).verify(self.row)["verified"])
        for failure in ("unavailable", "value-error", "wrong-chain", "empty-code", "malformed-abi", "wrong-router"):
            self.verifier()
            def rpc(url, method, params):
                if failure == "unavailable":
                    raise RuntimeError("private-endpoint")
                if failure == "value-error" and method == "eth_call":
                    raise ValueError("private-endpoint")
                if failure == "wrong-chain" and method == "eth_chainId":
                    return "0x1"
                if failure == "empty-code" and method == "eth_getCode":
                    return "0x"
                if method == "eth_call":
                    if failure == "malformed-abi":
                        return "0x" + "f" * 64
                    if failure == "wrong-router" and params[0]["to"] == ROUTERS["v2"]:
                        return word(FACTORIES["v3"])
                return self.transport(url, method, params)
            with self.subTest(failure=failure):
                result = policy.PoolVerifier(rpc, self.provider["selected"]).verify(self.row)
                self.assertFalse(result["verified"], result)
                self.assertNotIn("private-endpoint", str(result))

    def test_factory_router_and_pool_each_require_deployed_code(self):
        for missing in (POOL, FACTORIES["v2"], ROUTERS["v2"]):
            self.verifier()
            def rpc(url, method, params):
                return "0x" if method == "eth_getCode" and params[0] == missing else self.transport(url, method, params)
            with self.subTest(missing=missing):
                self.assertFalse(policy.PoolVerifier(rpc, self.provider["selected"]).verify(self.row)["verified"])

    def test_target_token_metadata_must_match_pool_tokens(self):
        verifier = self.verifier(tokens=(TOKEN, USDT))
        self.assertEqual(verifier.verify(self.row)["reason"], "POOL_TOKEN_MISMATCH")

    def test_v3_fee_is_a_strict_positive_uint24(self):
        for fee in (0, 2**24):
            with self.subTest(fee=fee):
                result = self.verifier("v3", fee=fee).verify(self.row)
                self.assertFalse(result["verified"])
                self.assertEqual(result["reason"], "POOL_FEE_UNVERIFIED")

    def test_malformed_addresses_and_foreign_networks_never_verify(self):
        for key, value in (("address", "0x" + "0" * 40), ("address", "0x123"),
                           ("network", "eth"), ("orientation_verified", "true")):
            row = {**self.row, key: value}
            with self.subTest(key=key, value=value):
                self.assertFalse(self.verifier().verify(row)["verified"])
        item = {"relationships": {"base_token": {"data": {"id": "eth_" + TOKEN}}}}
        self.assertIsNone(market.relationship_address(item, "base_token"))

    def test_deployment_reads_are_reused_only_within_one_snapshot(self):
        verifier = self.verifier()
        self.assertTrue(verifier.verify(self.row)["verified"])
        self.assertTrue(verifier.verify(self.row)["verified"])
        self.assertEqual(sum(method == "eth_chainId" for method, _ in self.transport.calls), 1)
        router_reads = [p for m, p in self.transport.calls if m == "eth_call" and p[0]["to"] == ROUTERS["v2"]]
        self.assertEqual(len(router_reads), 1)

    def test_filter_precedes_liquidity_and_aggregate_price_cannot_override(self):
        foreign, genuine = "0x" + "d" * 40, POOL
        pools = {genuine: {"version": "v2", "tokens": (TOKEN, USDT)},
                 foreign: {"version": "v2", "tokens": (TOKEN, USDT), "factory": "0x" + "e" * 40}}
        rpc = BscPoolFixture(pools)
        def item(pool, liquidity):
            return {"id": "bsc_" + pool,
                    "attributes": {"address": pool, "reserve_in_usd": liquidity,
                                   "base_token_price_usd": "100", "quote_token_price_usd": "1"},
                    "relationships": {"base_token": {"data": {"id": "bsc_" + TOKEN}},
                                      "quote_token": {"data": {"id": "bsc_" + USDT}}}}
        def provider(url, body=None):
            return {"data": [item(foreign, "999999999"), item(genuine, "100000")]} if "/pools?" in url else {
                "data": {"attributes": {"price_usd": "999999"}}}
        with patch.object(market, "request", side_effect=provider), patch.object(market, "rpc", side_effect=rpc):
            result = market.market(TOKEN, self.provider)
        self.assertEqual(result["selected_pool"]["address"], genuine)
        self.assertEqual([row["address"] for row in result["pools"]], [genuine])
        self.assertEqual(result["rejected_pools"][0]["address"], foreign)
        self.assertEqual(result["token"]["price_usd"], 100)
        self.assertEqual(result["token"]["price_source"], "VERIFIED_PANCAKESWAP_POOL")

    def test_no_verified_pool_means_no_aggregate_price_fallback(self):
        def provider(url, body=None):
            return {"data": []} if "/pools?" in url else {"data": {"attributes": {"price_usd": "100"}}}
        with patch.object(market, "request", side_effect=provider):
            result = market.market(TOKEN, {"selected": None})
        self.assertIsNone(result["selected_pool"])
        self.assertNotIn("price_usd", result["token"])


if __name__ == "__main__":
    unittest.main()
