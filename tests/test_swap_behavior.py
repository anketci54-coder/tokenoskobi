"""Offline tests for observed swap behavior (sell-ability and tax estimates)."""
import unittest
from unittest.mock import patch

from services.market import swap_behavior as sb
from services.market import token_controls as tc
from services.market import tokenoskobi_product_slice_02_server as market

TOK = "0x" + "11" * 20
POOL = "0x" + "22" * 20
WBNB = "0x" + "33" * 20
FEE = "0x" + "55" * 20
SELL_SIG = "swapExactTokensForETHSupportingFeeOnTransferTokens(uint256,uint256,address[],address,uint256)"


def pad(address):
    return "0x" + "0" * 24 + address[2:]


def word(value):
    return format(value, "064x")


def buyer(i):
    return "0x" + format(0x400000 + i, "040x")


def swap_log(tx, sender, to, in0, in1, out0, out1):
    return {"topics": [sb.SWAP_TOPIC, pad(sender), pad(to)],
            "data": "0x" + word(in0) + word(in1) + word(out0) + word(out1),
            "transactionHash": tx}


def transfer_log(frm, to, value, address=TOK):
    return {"address": address, "topics": [sb.TRANSFER_TOPIC, pad(frm), pad(to)],
            "data": "0x" + word(value)}


def sell_input(amount_in, path, signature=SELL_SIG):
    words = [amount_in, 0, 0xA0, int(WBNB, 16), 9999999999, len(path)] + [int(p, 16) for p in path]
    return "0x" + tc.selector(signature) + "".join(word(w) for w in words)


class Chain:
    def __init__(self, token0=TOK, token1=WBNB, logs=(), fail_spans=(), receipts=None, txs=None, v2=True):
        self.token0, self.token1, self.v2 = token0, token1, v2
        self.logs, self.fail_spans = list(logs), set(fail_spans)
        self.receipts, self.txs = receipts or {}, txs or {}
        self.spans = []

    def __call__(self, method, params):
        if method == "eth_call":
            data = params[0]["data"]
            if data == sb.TOKEN0_CALL:
                if self.token0 is None:
                    raise RuntimeError("execution reverted")
                return pad(self.token0)
            if data == sb.TOKEN1_CALL:
                return pad(self.token1)
            if data == sb.RESERVES_CALL:
                if not self.v2:
                    raise RuntimeError("execution reverted")
                return "0x" + word(1) * 3
        if method == "eth_blockNumber":
            return "0x10000"
        if method == "eth_getLogs":
            span = int(params[0]["toBlock"], 16) - int(params[0]["fromBlock"], 16)
            self.spans.append(span)
            if span in self.fail_spans:
                raise RuntimeError("query returned more than 10000 results")
            return self.logs
        if method == "eth_getTransactionReceipt":
            return self.receipts[params[0]]
        if method == "eth_getTransactionByHash":
            return self.txs[params[0]]
        raise AssertionError(method)


def taxed_buys(count, tax_pct=10, start=0):
    logs, receipts = [], {}
    for i in range(start, start + count):
        tx, out = f"0xb{i:03d}", 1000
        net = out * (100 - tax_pct) // 100
        logs.append(swap_log(tx, sb.ROUTER_V2, buyer(i), 0, 5, out, 0))
        receipts[tx] = {"logs": [transfer_log(POOL, buyer(i), net)]
                        + ([transfer_log(POOL, FEE, out - net)] if net < out else [])}
    return logs, receipts


def taxed_sells(count, tax_pct=5, start=0):
    logs, txs = [], {}
    for i in range(start, start + count):
        tx, gross = f"0xs{i:03d}", 1000
        net = gross * (100 - tax_pct) // 100
        logs.append(swap_log(tx, sb.ROUTER_V2, sb.ROUTER_V2, net, 0, 0, 4))
        txs[tx] = {"to": sb.ROUTER_V2, "input": sell_input(gross, [TOK, WBNB])}
    return logs, txs


class ConstantTests(unittest.TestCase):
    def test_event_topics_match_known_values(self):
        self.assertEqual(sb.TRANSFER_TOPIC,
                         "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef")
        self.assertEqual(sb.SWAP_TOPIC,
                         "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822")

    def test_token_getters(self):
        self.assertEqual(sb.TOKEN0_CALL, "0x0dfe1681")
        self.assertEqual(sb.TOKEN1_CALL, "0xd21220a7")


class ParseTests(unittest.TestCase):
    def test_buy_and_sell_orientation(self):
        buy = sb.parse_swap(swap_log("0xa", WBNB, FEE, 0, 5, 1000, 0), True)
        self.assertEqual((buy["kind"], buy["target_out"]), ("buy", 1000))
        sell = sb.parse_swap(swap_log("0xb", WBNB, FEE, 700, 0, 0, 3), True)
        self.assertEqual((sell["kind"], sell["target_in"]), ("sell", 700))
        flipped = sb.parse_swap(swap_log("0xc", WBNB, FEE, 5, 0, 0, 900), False)
        self.assertEqual((flipped["kind"], flipped["target_out"]), ("buy", 900))

    def test_unusable_logs_are_dropped(self):
        for bad in (None, {}, swap_log("0xa", WBNB, FEE, 1, 0, 1, 0),
                    {"topics": [sb.SWAP_TOPIC], "data": "0x"},
                    {**swap_log("0xa", WBNB, FEE, 0, 5, 1000, 0), "data": "0x12"}):
            with self.subTest(bad=bad):
                self.assertIsNone(sb.parse_swap(bad, True))


class TaxSampleTests(unittest.TestCase):
    def swap(self, **extra):
        return {"kind": "buy", "sender": sb.ROUTER_V2, "to": buyer(1), "target_in": 0,
                "target_out": 1000, "tx": "0xa", **extra}

    def test_buy_tax_from_buyer_transfer(self):
        receipt = {"logs": [transfer_log(POOL, buyer(1), 900), transfer_log(POOL, FEE, 100)]}
        self.assertAlmostEqual(sb.buy_tax_sample(self.swap(), receipt, TOK, POOL), 0.10)

    def test_buy_tax_unmeasurable_cases_are_none_not_zero(self):
        for receipt in (None, {}, {"logs": []},
                        {"logs": [transfer_log(POOL, FEE, 900)]},
                        {"logs": [transfer_log(POOL, buyer(1), 1500)]},
                        {"logs": [transfer_log(POOL, buyer(1), 900, address=FEE)]}):
            with self.subTest(receipt=receipt):
                self.assertIsNone(sb.buy_tax_sample(self.swap(), receipt, TOK, POOL))

    def sell(self, **extra):
        return {"kind": "sell", "sender": sb.ROUTER_V2, "to": sb.ROUTER_V2, "target_in": 950,
                "target_out": 0, "tx": "0xs", **extra}

    def test_sell_tax_from_router_calldata(self):
        tx = {"to": sb.ROUTER_V2, "input": sell_input(1000, [TOK, WBNB])}
        self.assertAlmostEqual(sb.sell_tax_sample(self.sell(), tx, TOK), 0.05)

    def test_sell_tax_unmeasurable_cases_are_none(self):
        good = {"to": sb.ROUTER_V2, "input": sell_input(1000, [TOK, WBNB])}
        cases = {
            "other_router": ({**good, "to": FEE}, self.sell()),
            "swap_not_from_router": (good, self.sell(sender=FEE)),
            "three_hop_path": ({**good, "input": sell_input(1000, [TOK, WBNB, FEE])}, self.sell()),
            "other_first_token": ({**good, "input": sell_input(1000, [FEE, WBNB])}, self.sell()),
            "unknown_function": ({**good, "input": sell_input(1000, [TOK, WBNB], "foo(uint256)")}, self.sell()),
            "net_above_gross": (good, self.sell(target_in=2000)),
            "empty_input": ({**good, "input": "0x"}, self.sell()),
            "none_tx": (None, self.sell()),
        }
        for name, (tx, swap) in cases.items():
            with self.subTest(name=name):
                self.assertIsNone(sb.sell_tax_sample(swap, tx, TOK))

    def test_summary_needs_enough_samples(self):
        self.assertEqual(sb.summarize_tax([0.1, 0.1])["status"], "UNKNOWN")
        result = sb.summarize_tax([0.0, 0.1, 0.2])
        self.assertEqual((result["status"], result["median_pct"], result["max_pct"], result["samples"]),
                         ("ESTIMATED", 10.0, 20.0, 3))


class CollectTests(unittest.TestCase):
    def test_many_buys_no_sells_is_flagged_and_range_falls_back(self):
        logs, receipts = taxed_buys(12, tax_pct=10)
        chain = Chain(logs=logs, receipts=receipts, fail_spans={3000})
        result = sb.collect_swap_behavior(TOK, POOL, chain)
        self.assertEqual(chain.spans, [3000, 1000])
        self.assertEqual((result["status"], result["window_blocks"]), ("OK", 1000))
        self.assertEqual((result["buys"], result["sells"], result["unique_buyers"]), (12, 0, 12))
        self.assertEqual(result["sell_ability"], "NO_SELLS_OBSERVED")
        self.assertEqual((result["buy_tax"]["status"], result["buy_tax"]["median_pct"]), ("ESTIMATED", 10.0))
        self.assertEqual(result["buy_tax"]["samples"], sb.MAX_SAMPLES)
        self.assertEqual(result["sell_tax"]["status"], "UNKNOWN")

    def test_sells_observed_with_taxes(self):
        buy_logs, receipts = taxed_buys(4, tax_pct=0)
        sell_logs, txs = taxed_sells(4, tax_pct=5)
        result = sb.collect_swap_behavior(TOK, POOL, Chain(logs=buy_logs + sell_logs, receipts=receipts, txs=txs))
        self.assertEqual(result["sell_ability"], "SELLS_OBSERVED")
        self.assertEqual((result["buy_tax"]["status"], result["buy_tax"]["median_pct"]), ("ESTIMATED", 0.0))
        self.assertEqual((result["sell_tax"]["status"], result["sell_tax"]["median_pct"]), ("ESTIMATED", 5.0))

    def test_few_swaps_is_sample_too_small_not_a_verdict(self):
        logs, receipts = taxed_buys(3)
        result = sb.collect_swap_behavior(TOK, POOL, Chain(logs=logs, receipts=receipts))
        self.assertEqual(result["sell_ability"], "SAMPLE_TOO_SMALL")
        empty = sb.collect_swap_behavior(TOK, POOL, Chain(logs=[]))
        self.assertEqual((empty["status"], empty["sell_ability"]), ("OK", "SAMPLE_TOO_SMALL"))

    def test_target_as_token1(self):
        logs = [swap_log(f"0xb{i}", sb.ROUTER_V2, buyer(i), 5, 0, 0, 1000) for i in range(11)]
        result = sb.collect_swap_behavior(TOK, POOL, Chain(token0=WBNB, token1=TOK, logs=logs))
        self.assertEqual((result["buys"], result["sell_ability"]), (11, "NO_SELLS_OBSERVED"))

    def test_unknown_reasons(self):
        self.assertEqual(sb.collect_swap_behavior(TOK, POOL, Chain(token0=None))["reason"], "POOL_NOT_V2_PAIR")
        self.assertEqual(sb.collect_swap_behavior(TOK, POOL, Chain(token0=WBNB, token1=FEE))["reason"], "TOKEN_NOT_IN_POOL")
        self.assertEqual(sb.collect_swap_behavior(TOK, POOL, Chain(v2=False))["reason"], "POOL_NOT_V2_PAIR")
        every_span = Chain(fail_spans=set(sb.LOOKBACK_STEPS))
        self.assertEqual(sb.collect_swap_behavior(TOK, POOL, every_span)["reason"], "LOGS_UNAVAILABLE")
        for result in (sb.collect_swap_behavior(TOK, POOL, Chain(token0=None)),):
            self.assertEqual(result["status"], "UNKNOWN")
            self.assertNotIn("sell_ability", result)

    def test_time_budget_stops_sampling(self):
        logs, receipts = taxed_buys(12)
        ticks = iter(range(0, 10_000, 100))
        result = sb.collect_swap_behavior(TOK, POOL, Chain(logs=logs, receipts=receipts),
                                          budget_sec=1, clock=lambda: next(ticks))
        self.assertEqual(result["buy_tax"]["samples"], 0)
        self.assertEqual(result["buy_tax"]["status"], "UNKNOWN")


AGG = "0x" + "66" * 20
SELLER = "0x" + "77" * 20


def sell_receipt(net, fee, extra_logs=()):
    pool_swap = {"address": POOL, "topics": [sb.SWAP_TOPIC, pad(AGG), pad(AGG)],
                 "data": "0x" + word(net) + word(0) + word(0) + word(4)}
    logs = [pool_swap, transfer_log(SELLER, POOL, net)]
    if fee:
        logs.append(transfer_log(SELLER, FEE, fee))
    return {"logs": logs + list(extra_logs)}


def sell_swap(net, sender=AGG):
    return {"kind": "sell", "sender": sender, "to": sender, "target_in": net, "target_out": 0, "tx": "0xs"}


class SellDiagnosticsTests(unittest.TestCase):
    def test_outcome_reasons_are_specific(self):
        good_tx = {"to": sb.ROUTER_V2, "input": sell_input(1000, [TOK, WBNB])}
        base = sell_swap(950, sender=sb.ROUTER_V2)
        cases = {
            "SENDER_NOT_V2_ROUTER": (sell_swap(950), good_tx),
            "TX_NOT_TO_V2_ROUTER": (base, {**good_tx, "to": FEE}),
            "UNKNOWN_FUNCTION": (base, {**good_tx, "input": sell_input(1000, [TOK, WBNB], "foo(uint256)")}),
            "MULTI_HOP": (base, {**good_tx, "input": sell_input(1000, [TOK, WBNB, FEE])}),
            "FIRST_TOKEN_MISMATCH": (base, {**good_tx, "input": sell_input(1000, [FEE, WBNB])}),
            "AMOUNT_INCONSISTENT": (sell_swap(2000, sender=sb.ROUTER_V2), good_tx),
            "BAD_CALLDATA": (base, None),
        }
        for reason, (swap, tx) in cases.items():
            with self.subTest(reason=reason):
                self.assertEqual(sb.sell_tax_outcome(swap, tx, TOK), (None, reason))
        value, reason = sb.sell_tax_outcome(base, good_tx, TOK)
        self.assertEqual(reason, "OK")
        self.assertAlmostEqual(value, 0.05)

    def test_fee_transfer_is_detected_without_a_router(self):
        kind, value = sb.sell_fee_event_outcome(sell_swap(920), sell_receipt(920, 80), TOK, POOL)
        self.assertEqual(kind, "FEE")
        self.assertAlmostEqual(value, 0.08)

    def test_clear_layout_without_fee_is_not_called_zero_tax(self):
        self.assertEqual(sb.sell_fee_event_outcome(sell_swap(1000), sell_receipt(1000, 0), TOK, POOL),
                         ("NO_FEE_TRANSFER", 0.0))

    def test_ambiguous_layouts_are_inconclusive(self):
        base = sell_receipt(920, 80)
        two_swaps = {"logs": base["logs"] + [base["logs"][0]]}
        two_into_pool = {"logs": base["logs"] + [transfer_log(SELLER, POOL, 5)]}
        pool_like_recipient = sell_receipt(920, 80, extra_logs=[
            {"address": FEE, "topics": ["0x" + "ab" * 32], "data": "0x"}])
        cases = {
            "two_swaps": (sell_swap(920), two_swaps),
            "two_transfers_into_pool": (sell_swap(920), two_into_pool),
            "net_differs_from_swap": (sell_swap(900), base),
            "pool_like_recipient": (sell_swap(920), pool_like_recipient),
            "no_receipt": (sell_swap(920), None),
            "empty_receipt": (sell_swap(920), {}),
        }
        for name, (swap, receipt) in cases.items():
            with self.subTest(name=name):
                self.assertEqual(sb.sell_fee_event_outcome(swap, receipt, TOK, POOL), ("INCONCLUSIVE", None))

    def test_fee_summary_thresholds(self):
        detected = sb.summarize_fee_events([("FEE", 0.08), ("FEE", 0.10), ("INCONCLUSIVE", None)])
        self.assertEqual((detected["status"], detected["median_pct"], detected["max_pct"],
                          detected["detected"], detected["inconclusive"]), ("DETECTED", 9.0, 10.0, 2, 1))
        clear = ("NO_FEE_TRANSFER", 0.0)
        self.assertEqual(sb.summarize_fee_events([clear] * 3)["status"], "NOT_DETECTED")
        self.assertEqual(sb.summarize_fee_events([clear] * 2)["status"], "UNKNOWN")
        self.assertEqual(sb.summarize_fee_events([("FEE", 0.1)] + [clear] * 5)["status"], "UNKNOWN")
        self.assertEqual(sb.summarize_fee_events([])["status"], "UNKNOWN")

    def test_top_senders_label_only_known_routers(self):
        swaps = [sell_swap(1, sender=sb.ROUTER_V2)] * 3 + [sell_swap(1)] * 2
        self.assertEqual(sb.top_senders(swaps), [
            {"address": sb.ROUTER_V2, "label": "PANCAKE_V2_ROUTER", "count": 3},
            {"address": AGG, "label": None, "count": 2}])

    def test_aggregator_sells_report_why_and_still_find_the_fee(self):
        buy_logs, receipts = taxed_buys(4, tax_pct=0)
        sell_logs = [swap_log(f"0xs{i}", AGG, AGG, 920, 0, 0, 4) for i in range(4)]
        receipts = {**receipts, **{f"0xs{i}": sell_receipt(920, 80) for i in range(4)}}
        result = sb.collect_swap_behavior(TOK, POOL, Chain(logs=buy_logs + sell_logs, receipts=receipts))
        self.assertEqual((result["sell_tax"]["status"], result["sell_tax"]["samples"]), ("UNKNOWN", 0))
        self.assertEqual(result["sell_tax_skips"], {"SENDER_NOT_V2_ROUTER": 4})
        fee = result["sell_fee_events"]
        self.assertEqual((fee["status"], fee["median_pct"], fee["detected"]), ("DETECTED", 8.0, 4))
        self.assertEqual(result["sell_senders"], [{"address": AGG, "label": None, "count": 4}])

    def test_unreadable_transactions_are_inconclusive_with_a_reason(self):
        sell_logs, _ = taxed_sells(4, tax_pct=5)
        result = sb.collect_swap_behavior(TOK, POOL, Chain(logs=sell_logs))
        self.assertEqual(result["sell_tax_skips"], {"TX_UNAVAILABLE": 4})
        self.assertEqual(result["sell_fee_events"]["status"], "UNKNOWN")
        self.assertEqual(result["sell_fee_events"]["inconclusive"], 4)


class ServerIntegrationTests(unittest.TestCase):
    def test_wrapper_returns_observed_behavior_over_a_public_endpoint_only(self):
        logs, receipts = taxed_buys(12)
        chain = Chain(logs=logs, receipts=receipts)
        urls = []
        def fake(url, method, params):
            urls.append(url)
            if url == "https://metered-key":
                raise AssertionError("the metered endpoint must not be used for swap analysis")
            return "0x38" if method == "eth_chainId" else chain(method, params)
        with patch.object(market, "rpc", fake):
            result = market.observed_swap_behavior(TOK, POOL, {"selected": {"url": "https://metered-key"}})
        self.assertEqual((result["status"], result["sell_ability"]), ("OK", "NO_SELLS_OBSERVED"))
        self.assertNotIn("https://metered-key", urls)
        self.assertTrue(set(urls) <= set(market.CFG["rpc"]))

    def test_wrapper_with_no_public_endpoint_is_unknown_not_a_fallback_to_the_key(self):
        urls = []
        def fake(url, method, params):
            urls.append(url)
            return "0x1"  # wrong chain everywhere
        with patch.object(market, "rpc", fake):
            result = market.observed_swap_behavior(TOK, POOL, {"selected": {"url": "https://metered-key"}})
        self.assertEqual((result["status"], result["reason"]), ("UNKNOWN", "COLLECT_ERROR"))
        self.assertIn("NO_PUBLIC_RPC", result["error"])
        self.assertNotIn("https://metered-key", urls)

    def test_wrapper_without_rpc_or_pool_is_unknown(self):
        for state, pool in (({}, POOL), ({"selected": None}, POOL), ({"selected": {"url": "u"}}, None),
                            ({"selected": {"url": "u"}}, "not-an-address")):
            with self.subTest(state=state, pool=pool):
                self.assertEqual(market.observed_swap_behavior(TOK, pool, state)["reason"], "NO_RPC_OR_POOL")

    def test_wrapper_survives_rpc_failure(self):
        def boom(*_):
            raise RuntimeError("rpc down")
        with patch.object(market, "rpc", boom):
            result = market.observed_swap_behavior(TOK, POOL, {"selected": {"url": "u"}})
        self.assertEqual(result["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
