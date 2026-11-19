"""Offline tests for observed swap behavior (sell-ability and tax estimates)."""
import inspect
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


class ServerIntegrationTests(unittest.TestCase):
    def test_wrapper_returns_observed_behavior(self):
        logs, receipts = taxed_buys(12)
        chain = Chain(logs=logs, receipts=receipts)
        with patch.object(market, "rpc", lambda url, method, params: chain(method, params)):
            result = market.observed_swap_behavior(TOK, POOL, {"selected": {"url": "u"}})
        self.assertEqual((result["status"], result["sell_ability"]), ("OK", "NO_SELLS_OBSERVED"))

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

    def test_decision_logic_does_not_read_swap_behavior(self):
        self.assertNotIn("swap_behavior", inspect.getsource(market.decide))


if __name__ == "__main__":
    unittest.main()
