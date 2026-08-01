from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/tokenoskobi_product_slice_04_relay_pool_settlement_reconciliation.py"
SPEC = importlib.util.spec_from_file_location("slice04_reconciliation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def allowlist_fixture():
    factories = {
        address: {"allowed_event_types": list(events)}
        for address, events in module.EXPECTED_FACTORY_EVENTS.items()
    }
    return {
        "schema": "tokenoskobi.product_slice_04.factory_allowlist.v1",
        "chain": "BSC", "chain_id": 56, "factories": factories,
        "policy": {
            "closed_loop_requires_strict_pair_direction_and_amount_match": True,
            "official_protocol_source_required": True,
            "router_identity_inferred_from_factory": False,
            "unlisted_factory_protocol_identity": "UNVERIFIED",
        },
    }


def transaction_fixture():
    transfer = lambda index, token, source, target, amount: {
        "log_index": index, "token": token, "from": source, "to": target, "amount_raw": str(amount)
    }
    return {
        "tx_hash": module.TARGET_TX, "actor": module.ACTOR,
        "single_endpoint_pair": True, "role_ledger_balanced": True,
        "route_verified": False, "relay_event_semantics_complete": False,
        "v4_route": {"aggregate_route_verified": False, "event_count": 0},
        "actor_net_raw": {module.USDC: str(-module.ACTOR_INPUT_RAW), module.USDT: str(module.POOL_OUTPUT_RAW)},
        "role_ledger": {
            module.USDC: {"ACTOR": str(-module.ACTOR_INPUT_RAW), "OTHER": str(module.FEE_RAW),
                          "UNISWAP_V4_POOL_MANAGER": str(module.POOL_INPUT_RAW)},
            module.USDT: {"ACTOR": str(module.POOL_OUTPUT_RAW),
                          "UNISWAP_V4_POOL_MANAGER": str(-module.POOL_OUTPUT_RAW)},
        },
        "tracked_transfers": [
            transfer(309, module.USDC, module.ACTOR, module.RELAY, module.ACTOR_INPUT_RAW),
            transfer(314, module.USDC, module.RELAY, module.FEE_RECIPIENT, module.FEE_RAW),
            transfer(317, module.USDC, module.RELAY, module.POOL_MANAGER, module.POOL_INPUT_RAW),
            transfer(320, module.USDT, module.POOL_COUNTERPARTY, module.POOL_MANAGER, module.POOL_OUTPUT_RAW),
            transfer(321, module.USDC, module.POOL_MANAGER, module.POOL_COUNTERPARTY, module.POOL_INPUT_RAW),
            transfer(322, module.USDT, module.POOL_MANAGER, module.RELAY, module.POOL_OUTPUT_RAW),
            transfer(324, module.USDT, module.RELAY, module.ACTOR, module.POOL_OUTPUT_RAW),
        ],
    }


class RelayPoolSettlementReconciliationTests(unittest.TestCase):
    def assert_ledger_rejected(self, value):
        with self.assertRaisesRegex(module.ReconciliationError, "TRANSFER_LEDGER_EXACT_MATCH_FAILED"):
            module.reconcile_transaction(value)

    def test_exact_transfer_ledger_reconciles_but_route_stays_closed(self):
        result = module.reconcile_transaction(transaction_fixture())
        self.assertTrue(result["checks"]["settlement_transfer_ledger_reconciled"])
        self.assertFalse(result["route_gate"]["route_verified"])
        self.assertFalse(result["route_gate"]["cost_basis_permitted"])
        self.assertFalse(result["route_gate"]["pnl_permitted"])

    def test_wrong_actor_fails_closed(self):
        value = transaction_fixture(); value["actor"] = "0x" + "0" * 39 + "1"
        with self.assertRaisesRegex(module.ReconciliationError, "ACTOR_MISMATCH"):
            module.reconcile_transaction(value)

    def test_raw_amount_mismatch_fails_closed(self):
        value = transaction_fixture(); value["tracked_transfers"][2]["amount_raw"] = str(module.POOL_INPUT_RAW - 1)
        self.assert_ledger_rejected(value)

    def test_wrong_direction_fails_closed(self):
        value = transaction_fixture(); row = value["tracked_transfers"][5]
        row["from"], row["to"] = row["to"], row["from"]
        self.assert_ledger_rejected(value)

    def test_wrong_chronology_fails_closed(self):
        value = transaction_fixture(); value["tracked_transfers"][4:6] = reversed(value["tracked_transfers"][4:6])
        self.assert_ledger_rejected(value)

    def test_extra_transfer_fails_closed(self):
        value = transaction_fixture(); value["tracked_transfers"].append(copy.deepcopy(value["tracked_transfers"][-1]))
        self.assert_ledger_rejected(value)

    def test_missing_transfer_fails_closed(self):
        value = transaction_fixture(); value["tracked_transfers"].pop()
        self.assert_ledger_rejected(value)

    def test_duplicate_transfer_fails_closed(self):
        value = transaction_fixture(); value["tracked_transfers"][5] = copy.deepcopy(value["tracked_transfers"][4])
        self.assert_ledger_rejected(value)

    def test_route_cannot_be_promoted_without_events(self):
        value = transaction_fixture(); value["route_verified"] = True
        with self.assertRaisesRegex(module.ReconciliationError, "ROUTE_VERIFICATION_MUST_REMAIN_FALSE"):
            module.reconcile_transaction(value)

    def test_canonical_factory_allowlist_is_accepted(self):
        module.validate_allowlist(allowlist_fixture())

    def test_missing_or_extra_factory_fails_closed(self):
        for mutate in (lambda d: d["factories"].pop(next(iter(d["factories"]))),
                       lambda d: d["factories"].update({"0x" + "1" * 40: {"allowed_event_types": ["V2_SWAP"]}})):
            value = allowlist_fixture(); mutate(value)
            with self.assertRaisesRegex(module.ReconciliationError, "ALLOWLIST_FACTORY_SCOPE_INVALID"):
                module.validate_allowlist(value)

    def test_changed_or_duplicate_event_type_fails_closed(self):
        address = next(iter(module.EXPECTED_FACTORY_EVENTS))
        for events in (["V2_SWAP"], [module.EXPECTED_FACTORY_EVENTS[address][0]] * 2):
            value = allowlist_fixture(); value["factories"][address]["allowed_event_types"] = events
            with self.assertRaisesRegex(module.ReconciliationError, "ALLOWLIST_EVENT_TYPES_INVALID"):
                module.validate_allowlist(value)

    def test_allowlist_policy_must_match_exactly(self):
        value = allowlist_fixture(); value["policy"]["official_protocol_source_required"] = False
        with self.assertRaisesRegex(module.ReconciliationError, "ALLOWLIST_POLICY_INVALID"):
            module.validate_allowlist(value)

    def test_alternative_allowlist_path_fails_before_file_read(self):
        with tempfile.TemporaryDirectory() as directory:
            alternative = Path(directory) / "allowlist.json"
            alternative.write_text(json.dumps(allowlist_fixture()), encoding="utf-8")
            with self.assertRaisesRegex(module.ReconciliationError, "ALLOWLIST_PATH_NOT_CANONICAL"):
                module.run(module.DEFAULT_SOURCE, alternative, Path(directory) / "out.json")

    def test_allowlist_hash_mismatch_fails_closed(self):
        with mock.patch.object(module, "sha256_file", side_effect=[module.EXPECTED_SOURCE_SHA256, "0" * 64]):
            with self.assertRaisesRegex(module.ReconciliationError, "ALLOWLIST_HASH_INVALID"):
                module.run(module.DEFAULT_SOURCE, module.DEFAULT_ALLOWLIST, Path("/tmp/unused.json"))

    def test_authority_has_no_financial_or_mutation_power(self):
        self.assertTrue(module.AUTHORITY)
        self.assertTrue(all(value is False for value in module.AUTHORITY.values()))


if __name__ == "__main__":
    unittest.main()
