#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/root/tokenoskobi_clean_v1")
DEFAULT_SOURCE = Path("/var/lib/tokenoskobi-product-slice-04/relay_settlement_fifo_reconstruction_v1.json")
DEFAULT_ALLOWLIST = ROOT / "config/product_slice_04_factory_allowlist_v1.json"
DEFAULT_OUTPUT = Path("/var/lib/tokenoskobi-product-slice-04/relay_pool_settlement_reconciliation_v1.json")
EXPECTED_SOURCE_SHA256 = "2cdd9503385afbcf3159a92be477e907eff6f3313ca3514d4dca444450e87f19"
EXPECTED_ALLOWLIST_SHA256 = "17308d6cd17fe2eb538d3cead016b6755ccb07b41682306c24d7dbc55c8bc8af"
EXPECTED_FACTORY_EVENTS = {
    "0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865": ("PANCAKE_V3_EXTENDED_SWAP",),
    "0x8909dc15e40173ff4699343b6eb8132c65e18ec6": ("V2_SWAP",),
    "0xca143ce32fe78f1f7019d7d551a6402fc5350c73": ("V2_SWAP",),
    "0xdb1d10011ad0ff90774d0c6bb92e5c5c8b4461f7": ("V3_SWAP",),
}
TARGET_TX = "0x3d516b2c6ccee0235ec7a81303de7e04cf667972639a881b4dc6fc602cd70f5a"
ACTOR = "0x7983a402e111002259072d600c5bf7bc709193b4"
RELAY = "0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f"
POOL_MANAGER = "0x011af51cc6614fec1de0e0ff6dc315a150f3851c"
POOL_COUNTERPARTY = "0x28e2ea090877bf75740558f6bfb36a5ffee9e9df"
FEE_RECIPIENT = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"
USDC = "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"
USDT = "0x55d398326f99059ff775485246999027b3197955"
ACTOR_INPUT_RAW = 10_500_000_000_000_000_000
FEE_RAW = 16_800_000_000_000_000
POOL_INPUT_RAW = 10_483_200_000_000_000_000
POOL_OUTPUT_RAW = 10_490_666_816_297_243_269
AUTHORITY = {key: False for key in (
    "network_access", "source_evidence_write", "repository_write",
    "production_database_write", "panel_mutation", "service_mutation",
    "timer_mutation", "paper_trade", "live_trade", "wallet", "signing",
    "order_create", "broadcast",
)}


class ReconciliationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def read_object(path: Path, code: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise ReconciliationError(f"{code}_MISSING")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReconciliationError(f"{code}_INVALID_JSON") from exc
    if not isinstance(value, dict):
        raise ReconciliationError(f"{code}_NOT_OBJECT")
    return value


def integer(value: Any, field: str) -> int:
    try:
        result = int(str(value))
    except (TypeError, ValueError) as exc:
        raise ReconciliationError(f"{field}_INVALID_INTEGER") from exc
    if result < 0:
        raise ReconciliationError(f"{field}_NEGATIVE")
    return result


def transfer_tuple(row: dict[str, Any]) -> tuple[int, str, str, str, int]:
    if not isinstance(row, dict):
        raise ReconciliationError("TRANSFER_NOT_OBJECT")
    return (integer(row.get("log_index"), "TRANSFER_LOG_INDEX"),
            str(row.get("token") or "").lower(), str(row.get("from") or "").lower(),
            str(row.get("to") or "").lower(), integer(row.get("amount_raw"), "TRANSFER_AMOUNT"))


def validate_allowlist(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "tokenoskobi.product_slice_04.factory_allowlist.v1":
        raise ReconciliationError("ALLOWLIST_SCHEMA_INVALID")
    if payload.get("chain") != "BSC" or payload.get("chain_id") != 56:
        raise ReconciliationError("ALLOWLIST_CHAIN_INVALID")
    factories = payload.get("factories")
    if not isinstance(factories, dict) or set(factories) != set(EXPECTED_FACTORY_EVENTS):
        raise ReconciliationError("ALLOWLIST_FACTORY_SCOPE_INVALID")
    for address, expected_events in EXPECTED_FACTORY_EVENTS.items():
        entry = factories.get(address)
        if not isinstance(entry, dict):
            raise ReconciliationError("ALLOWLIST_ENTRY_INVALID")
        allowed = entry.get("allowed_event_types")
        if not isinstance(allowed, list) or tuple(allowed) != expected_events:
            raise ReconciliationError(f"ALLOWLIST_EVENT_TYPES_INVALID:{address}")
    policy = payload.get("policy")
    required_policy = {
        "closed_loop_requires_strict_pair_direction_and_amount_match": True,
        "official_protocol_source_required": True,
        "router_identity_inferred_from_factory": False,
        "unlisted_factory_protocol_identity": "UNVERIFIED",
    }
    if policy != required_policy:
        raise ReconciliationError("ALLOWLIST_POLICY_INVALID")


def find_target_transaction(source: dict[str, Any]) -> dict[str, Any]:
    rows = source.get("historical_transactions")
    if not isinstance(rows, list):
        raise ReconciliationError("HISTORICAL_TRANSACTIONS_INVALID")
    matches = [row for row in rows if isinstance(row, dict) and str(row.get("tx_hash") or "").lower() == TARGET_TX]
    if len(matches) != 1:
        raise ReconciliationError(f"TARGET_TRANSACTION_COUNT_INVALID:{len(matches)}")
    return matches[0]


def reconcile_transaction(transaction: dict[str, Any]) -> dict[str, Any]:
    if str(transaction.get("tx_hash") or "").lower() != TARGET_TX:
        raise ReconciliationError("TARGET_TRANSACTION_INVALID")
    if str(transaction.get("actor") or "").lower() != ACTOR:
        raise ReconciliationError("ACTOR_MISMATCH")
    if transaction.get("single_endpoint_pair") is not True:
        raise ReconciliationError("SINGLE_ENDPOINT_PAIR_NOT_PROVEN")
    if transaction.get("role_ledger_balanced") is not True:
        raise ReconciliationError("ROLE_LEDGER_NOT_BALANCED")
    expected = [
        (309, USDC, ACTOR, RELAY, ACTOR_INPUT_RAW),
        (314, USDC, RELAY, FEE_RECIPIENT, FEE_RAW),
        (317, USDC, RELAY, POOL_MANAGER, POOL_INPUT_RAW),
        (320, USDT, POOL_COUNTERPARTY, POOL_MANAGER, POOL_OUTPUT_RAW),
        (321, USDC, POOL_MANAGER, POOL_COUNTERPARTY, POOL_INPUT_RAW),
        (322, USDT, POOL_MANAGER, RELAY, POOL_OUTPUT_RAW),
        (324, USDT, RELAY, ACTOR, POOL_OUTPUT_RAW),
    ]
    rows = transaction.get("tracked_transfers")
    if not isinstance(rows, list):
        raise ReconciliationError("TRACKED_TRANSFERS_INVALID")
    actual = [transfer_tuple(row) for row in rows]
    if actual != expected:
        raise ReconciliationError("TRANSFER_LEDGER_EXACT_MATCH_FAILED")
    indexes = [row[0] for row in actual]
    if indexes != sorted(indexes) or len(set(indexes)) != len(indexes):
        raise ReconciliationError("TRANSFER_ORDER_INVALID")
    if POOL_INPUT_RAW + FEE_RAW != ACTOR_INPUT_RAW:
        raise ReconciliationError("INPUT_CONSERVATION_FAILED")
    actor_net = transaction.get("actor_net_raw")
    expected_net = {USDC: str(-ACTOR_INPUT_RAW), USDT: str(POOL_OUTPUT_RAW)}
    if not isinstance(actor_net, dict) or {str(k).lower(): str(v) for k, v in actor_net.items()} != expected_net:
        raise ReconciliationError("ACTOR_NET_EXACT_MATCH_FAILED")
    role_ledger = transaction.get("role_ledger")
    expected_roles = {
        USDC: {"ACTOR": str(-ACTOR_INPUT_RAW), "OTHER": str(FEE_RAW), "UNISWAP_V4_POOL_MANAGER": str(POOL_INPUT_RAW)},
        USDT: {"ACTOR": str(POOL_OUTPUT_RAW), "UNISWAP_V4_POOL_MANAGER": str(-POOL_OUTPUT_RAW)},
    }
    normalized_roles = ({str(token).lower(): {str(role): str(amount) for role, amount in values.items()}
                         for token, values in role_ledger.items() if isinstance(values, dict)}
                        if isinstance(role_ledger, dict) else {})
    if normalized_roles != expected_roles:
        raise ReconciliationError("ROLE_LEDGER_EXACT_MATCH_FAILED")
    route = transaction.get("v4_route")
    if not isinstance(route, dict):
        raise ReconciliationError("V4_ROUTE_INVALID")
    if transaction.get("route_verified") is not False:
        raise ReconciliationError("ROUTE_VERIFICATION_MUST_REMAIN_FALSE")
    if route.get("aggregate_route_verified") is not False:
        raise ReconciliationError("AGGREGATE_ROUTE_VERIFICATION_MUST_REMAIN_FALSE")
    if integer(route.get("event_count"), "V4_EVENT_COUNT") != 0:
        raise ReconciliationError("UNEXPECTED_V4_EVENT_SEMANTICS_PRESENT")
    if transaction.get("relay_event_semantics_complete") is not False:
        raise ReconciliationError("RELAY_EVENT_SEMANTICS_MUST_REMAIN_INCOMPLETE")
    return {
        "transaction_hash": TARGET_TX, "actor": ACTOR, "transfer_log_indexes": indexes,
        "actor_input": {"token": USDC, "raw": str(ACTOR_INPUT_RAW)},
        "relay_fee": {"token": USDC, "raw": str(FEE_RAW), "recipient": FEE_RECIPIENT},
        "pool_input": {"token": USDC, "raw": str(POOL_INPUT_RAW), "pool_manager": POOL_MANAGER},
        "pool_output": {"token": USDT, "raw": str(POOL_OUTPUT_RAW), "pool_manager": POOL_MANAGER},
        "actor_output": {"token": USDT, "raw": str(POOL_OUTPUT_RAW)},
        "checks": {key: True for key in (
            "same_actor", "single_endpoint_pair", "strict_chronological_order", "input_conservation",
            "pool_input_round_trip", "pool_output_round_trip", "actor_net_exact", "role_ledger_exact",
            "role_ledger_balanced", "settlement_transfer_ledger_reconciled")},
        "route_gate": {"factory_allowlist_bound": True, "recognized_v4_event_count": 0,
                       "relay_event_semantics_complete": False, "route_verified": False,
                       "cost_basis_permitted": False, "pnl_permitted": False,
                       "blockers": ["NO_RECOGNIZED_ALLOWLISTED_V4_SWAP_EVENT", "RELAY_ABI_SEMANTICS_INCOMPLETE", "ROUTE_NOT_VERIFIED"]},
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(temp, 0o600)
    json.loads(temp.read_text(encoding="utf-8"))
    temp.replace(path)
    os.chmod(path, 0o600)


def run(source_path: Path, allowlist_path: Path, output_path: Path) -> dict[str, Any]:
    if source_path.resolve() != DEFAULT_SOURCE.resolve():
        raise ReconciliationError("SOURCE_PATH_NOT_ALLOWLISTED")
    if allowlist_path.resolve() != DEFAULT_ALLOWLIST.resolve():
        raise ReconciliationError("ALLOWLIST_PATH_NOT_CANONICAL")
    source_hash = sha256_file(source_path)
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise ReconciliationError(f"SOURCE_HASH_INVALID:EXPECTED={EXPECTED_SOURCE_SHA256}:ACTUAL={source_hash}")
    allowlist_hash = sha256_file(allowlist_path)
    if allowlist_hash != EXPECTED_ALLOWLIST_SHA256:
        raise ReconciliationError(f"ALLOWLIST_HASH_INVALID:EXPECTED={EXPECTED_ALLOWLIST_SHA256}:ACTUAL={allowlist_hash}")
    source = read_object(source_path, "SOURCE")
    allowlist = read_object(allowlist_path, "ALLOWLIST")
    validate_allowlist(allowlist)
    transaction = find_target_transaction(source)
    reconciliation = reconcile_transaction(transaction)
    evidence = {
        "schema": "tokenoskobi.product_slice_04.relay_pool_settlement_reconciliation.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "SETTLEMENT_TRANSFER_LEDGER_RECONCILED_ROUTE_REMAINS_FAIL_CLOSED",
        "authority": dict(AUTHORITY),
        "source": {"path": str(source_path), "sha256": source_hash,
                   "transaction_evidence_hash": str(transaction.get("transaction_evidence_hash") or ""),
                   "receipt_evidence_hash": str(transaction.get("receipt_evidence_hash") or ""),
                   "block_evidence_hash": str(transaction.get("block_evidence_hash") or "")},
        "factory_allowlist": {"path": str(allowlist_path), "sha256": allowlist_hash,
                              "schema": allowlist["schema"], "chain": allowlist["chain"],
                              "chain_id": allowlist["chain_id"], "factory_count": len(allowlist["factories"])},
        "reconciliation": reconciliation,
        "canonical_claims": {"settlement_transfer_ledger_reconciled": True, "route_verified": False,
                             "cost_basis_complete": False, "pnl_complete": False,
                             "closed_loop_confirmed": False, "successful_wallet_classification_ready": False},
        "next_safe_step": "PRODUCT_SLICE_04_RELAY_ABI_AND_ALLOWLISTED_V4_ROUTE_SEMANTIC_VERIFICATION",
    }
    basis = dict(evidence); basis.pop("generated_at_utc")
    evidence["result_hash"] = canonical_hash(basis)
    atomic_write_json(output_path, evidence)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        result = run(args.source, args.allowlist, args.output)
    except ReconciliationError as exc:
        print(f"RECONCILIATION=FAIL:{exc}"); return 1
    claims = result["canonical_claims"]
    print(f"OUTPUT={args.output}")
    print(f"RESULT_HASH={result['result_hash']}")
    for key in ("settlement_transfer_ledger_reconciled", "route_verified", "cost_basis_complete", "pnl_complete", "closed_loop_confirmed"):
        print(f"{key.upper()}={str(claims[key]).lower()}")
    print(f"NEXT_SAFE_STEP={result['next_safe_step']}")
    print("RECONCILIATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
