from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/tokenoskobi_product_slice_04_relay_v4_route_semantic_verification.py"
SPEC = importlib.util.spec_from_file_location("slice04_v4_semantics", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def address_word(value: str) -> bytes:
    return bytes.fromhex("00" * 12 + value[2:])


def uint_word(value: int) -> bytes:
    return value.to_bytes(32, "big")


def int_word(value: int, bits: int = 256) -> bytes:
    if value < 0:
        value = (1 << bits) + value
        value |= ((1 << (256 - bits)) - 1) << bits
    return value.to_bytes(32, "big")


def dynamic_event(static: list[bytes], payload: bytes) -> str:
    offset = 32 * (len(static) + 1)
    padding = b"\x00" * ((32 - len(payload) % 32) % 32)
    return "0x" + b"".join(static + [uint_word(offset), uint_word(len(payload)), payload, padding]).hex()


def topic_address(value: str) -> str:
    return "0x" + address_word(value).hex()


def log(index: int, address: str, topic0: str, data: str, extra_topics=None):
    return {"logIndex": hex(index), "address": address,
            "topics": [topic0] + list(extra_topics or []), "data": data}


def solver_call(index=323, target=None):
    target = target or module.SETTLEMENT_CALLER
    payload = b"\x12\x34"
    padding = b"\x00" * 30
    data = "0x" + b"".join([
        address_word(target), uint_word(96), uint_word(0),
        uint_word(len(payload)), payload, padding,
    ]).hex()
    return log(index, module.RELAY_V3_ROUTER, module.SOLVER_CALL_EXECUTED_TOPIC,
               data)


def movement(index, source, target, token, amount):
    return log(index, module.RELAY_V3_ROUTER, module.FUNDS_MOVEMENT_TOPIC,
               dynamic_event([address_word(source), address_word(target), address_word(token), uint_word(amount)], b"evidence"))


def swap(index=320, amount0=None, amount1=None, pool_id=None, sender=None):
    amount0 = -module.POOL_OUTPUT_RAW if amount0 is None else amount0
    amount1 = module.POOL_INPUT_RAW if amount1 is None else amount1
    data = "0x" + b"".join([int_word(amount0, 128), int_word(amount1, 128), uint_word(100),
                              uint_word(200), int_word(3, 24), uint_word(500)]).hex()
    return log(index, module.UNISWAP_V4_POOL_MANAGER, module.UNISWAP_V4_SWAP_TOPIC, data,
               [pool_id or module.POOL_ID, topic_address(sender or module.SETTLEMENT_CALLER)])


def receipt():
    return {"transactionHash": module.TARGET_TX, "status": "0x1", "logs": [
        solver_call(),
        movement(314, module.RELAY_V3_ROUTER, module.SETTLEMENT_CALLER, module.USDC, module.POOL_INPUT_RAW),
        swap(),
        movement(322, module.SETTLEMENT_CALLER, module.RELAY_V3_ROUTER, module.USDT, module.POOL_OUTPUT_RAW),
    ]}


class RelayV4SemanticVerificationTests(unittest.TestCase):
    def test_exact_receipt_verifies_route_but_not_pnl(self):
        result = module.validate_receipt(receipt())
        self.assertEqual(result["v4_swap"]["pool_id"], module.POOL_ID)
        self.assertEqual(result["solver_call"]["to"], module.SETTLEMENT_CALLER)

    def test_wrong_pool_id_fails_closed(self):
        value = receipt(); value["logs"][2] = swap(pool_id="0x" + "1" * 64)
        with self.assertRaisesRegex(module.SemanticVerificationError, "TARGET_V4_SWAP_COUNT_INVALID"):
            module.validate_receipt(value)

    def test_wrong_pool_manager_fails_closed(self):
        value = receipt(); value["logs"][2]["address"] = "0x" + "1" * 40
        with self.assertRaisesRegex(module.SemanticVerificationError, "TARGET_V4_SWAP_COUNT_INVALID"):
            module.validate_receipt(value)

    def test_wrong_swap_sender_fails_closed(self):
        value = receipt(); value["logs"][2] = swap(sender="0x" + "1" * 40)
        with self.assertRaisesRegex(module.SemanticVerificationError, "V4_SWAP_SENDER_MISMATCH"):
            module.validate_receipt(value)

    def test_amount_mismatch_fails_closed(self):
        value = receipt(); value["logs"][2] = swap(amount1=module.POOL_INPUT_RAW - 1)
        with self.assertRaisesRegex(module.SemanticVerificationError, "V4_SWAP_AMOUNTS_MISMATCH"):
            module.validate_receipt(value)

    def test_missing_relay_movement_fails_closed(self):
        value = receipt(); value["logs"].pop()
        with self.assertRaisesRegex(module.SemanticVerificationError, "RELAY_FUNDS_MOVEMENT_LINK_MISSING"):
            module.validate_receipt(value)

    def test_wrong_relay_emitter_fails_closed(self):
        value = receipt(); value["logs"][0]["address"] = "0x" + "2" * 40
        with self.assertRaisesRegex(module.SemanticVerificationError, "SETTLEMENT_CALL_EVENT_COUNT_INVALID"):
            module.validate_receipt(value)

    def test_wrong_chronology_fails_closed(self):
        value = receipt(); value["logs"][0] = solver_call(index=310)
        with self.assertRaisesRegex(module.SemanticVerificationError, "SOLVER_CALL_SWAP_CHRONOLOGY_INVALID"):
            module.validate_receipt(value)

    def test_duplicate_log_index_fails_closed(self):
        value = receipt(); value["logs"][1]["logIndex"] = value["logs"][0]["logIndex"]
        with self.assertRaisesRegex(module.SemanticVerificationError, "DUPLICATE_LOG_INDEX"):
            module.validate_receipt(value)

    def test_failed_receipt_fails_closed(self):
        value = receipt(); value["status"] = "0x0"
        with self.assertRaisesRegex(module.SemanticVerificationError, "RECEIPT_NOT_SUCCESSFUL"):
            module.validate_receipt(value)

    def test_sign_extension_is_strict(self):
        value = receipt()
        raw = bytearray.fromhex(value["logs"][2]["data"][2:]); raw[0] = 0
        value["logs"][2]["data"] = "0x" + raw.hex()
        with self.assertRaisesRegex(module.SemanticVerificationError, "SIGN_EXTENSION_INVALID"):
            module.validate_receipt(value)

    def test_rpc_method_allowlist(self):
        with self.assertRaisesRegex(module.SemanticVerificationError, "RPC_METHOD_NOT_ALLOWLISTED"):
            module.rpc_call({"endpoints": [], "allowed_hosts": set(), "timeout": 2}, "eth_sendRawTransaction", [])

    def test_authority_has_no_financial_power(self):
        for key in ("live_trade", "wallet", "signing", "order_create", "broadcast"):
            self.assertFalse(module.AUTHORITY[key])


if __name__ == "__main__":
    unittest.main()
